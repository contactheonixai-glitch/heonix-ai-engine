"""HEONIX GEN-5 · module `heonix.booking.engine`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 7131-7828).
Behaviour is unchanged; the only additions are import wiring and lines
tagged  # GEN-5 SPLIT  (late-binding sync for module-level globals).
"""
from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# 📦  STANDARD LIBRARY
# ─────────────────────────────────────────────────────────────────────────────
import atexit
import base64
import functools
import hashlib
import hmac
import io
import json
import logging
import math                                        # v16g4 FIX L2
import os
import queue
import random
import re
import signal
import sqlite3
import sys
import threading
import time
import unicodedata
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor   # v11 #1/#11: bounded async workers
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple
from urllib.parse import urlparse                  # v16g3 FIX R3-L4

import requests
from requests.adapters import HTTPAdapter          # v15g3 FIX 2: pooled WA session
from urllib3.util.retry import Retry               # v15g3 FIX 2: connect-only retries
from flask import Flask, g, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pydantic import BaseModel, Field, field_validator, ValidationError


# ─────────────────────────────────────────────────────────────────────────────
# 🔌  OPTIONAL DEPENDENCIES  (graceful fallbacks if not installed)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    import jwt as pyjwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    import bcrypt as bcrypt_lib
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

try:
    import psycopg2
    import psycopg2.pool
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

try:
    import redis as redis_lib
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import openai as openai_lib
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic as anthropic_lib
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────

from heonix.analytics import (analytics)
from heonix.cache import (brain_cache)
from heonix.channels.whatsapp import (
    _maybe_request_phone,
    send_whatsapp_sync,
    wa_send_buttons_now,
    wa_send_list_now,
)
from heonix.classify import (_kw_hit)
from heonix.config import (cfg)
from heonix.db.core import (_execute, _is_unique_violation)
from heonix.db.store import (increment_chat_count, save_messages_batch)
from heonix.i18n import (_norm_text, _t, _user_lang)
from heonix.logsetup import (log)
from heonix.security.crypto import (_crm_phone_hash, pii_vault)
from heonix.utils import (_now)
from heonix import _latebind  # GEN-5 SPLIT
_db_pool: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.db.core at startup
_latebind.register('_db_pool', __name__)


def _parse_dt(s: str) -> datetime:
    """Parse an ISO timestamp to an aware UTC datetime (tolerates a trailing Z)."""
    s = (s or "").strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_local(dt_or_iso) -> datetime:
    # v14g5 FIX 25: return a NAIVE local wall-clock datetime (was tagged UTC while
    # carrying local numbers — misleading if ever reused in tz-aware math).
    dt = dt_or_iso if isinstance(dt_or_iso, datetime) else _parse_dt(dt_or_iso)
    return (dt + timedelta(minutes=cfg.BOOKING_TZ_OFFSET_MIN)).replace(tzinfo=None)


def _fmt_local_dt(s) -> str:
    return _to_local(s).strftime("%a %d %b, %I:%M %p")


def _fmt_local_time_range(s, e) -> str:
    return _to_local(s).strftime("%I:%M %p") + "–" + _to_local(e).strftime("%I:%M %p")


def booking_available_slots(customer_id: str, limit: int) -> List[Tuple[datetime, datetime]]:
    """Return the next `limit` open slots (as aware-UTC (start,end) tuples),
    computed from business-hours config minus slots already booked. At least
    60 minutes in the future so nobody books a slot that's basically now."""
    step    = max(5, cfg.BOOKING_SLOT_MINUTES)
    open_m  = cfg.BOOKING_OPEN_HOUR * 60
    close_m = cfg.BOOKING_CLOSE_HOUR * 60
    wkdays  = {int(x) for x in cfg.BOOKING_WEEKDAYS.split(",")
               if x.strip().isdigit() and 0 <= int(x.strip()) <= 6}
    # v16g5 FIX R5-M5: a typo'd BOOKING_WEEKDAYS ("Mon,Tue") produced an EMPTY
    # weekday set and this function returned [] forever — the patient just saw
    # "no slots available", with nothing anywhere saying why. Same for an
    # inverted OPEN/CLOSE hour. Fail LOUD (hourly-throttled) instead of dark.
    # v16g6 FIX R6-L5: BOOKING_CLOSE_HOUR=25 sailed past this guard and blew
    # up later at d_loc.replace(hour=…) — an uncaught ValueError out of the
    # offer builder, straight into handle_booking. Clamp to the calendar
    # first; the loud guard below still catches a nonsensical clamped range.
    open_m  = min(max(open_m, 0), 24 * 60)
    close_m = min(max(close_m, 0), 24 * 60)
    if not wkdays or open_m + step > close_m:
        if brain_cache.setnx("warn:booking_cfg", ttl=3600):
            log.critical(
                f"🛑 BOOKING MISCONFIGURED — no slot can ever be offered. "
                f"BOOKING_WEEKDAYS={cfg.BOOKING_WEEKDAYS!r} parsed to {sorted(wkdays)} "
                f"(expects digits 0-6, Mon=0), OPEN_HOUR={cfg.BOOKING_OPEN_HOUR} "
                f"CLOSE_HOUR={cfg.BOOKING_CLOSE_HOUR} SLOT_MINUTES={step}.")
        analytics.inc("booking.misconfigured")
        return []
    # v16g6 R6-L13 (documented limitation): a FIXED minute offset is correct
    # for IST (+330, no DST — the launch market) and WRONG for any DST
    # region: this naive wall-clock drifts ±60min across transitions.
    # Before selling outside fixed-offset zones, replace
    # BOOKING_TZ_OFFSET_MIN with a per-clinic IANA zone via zoneinfo.
    off     = timedelta(minutes=cfg.BOOKING_TZ_OFFSET_MIN)
    now_utc = datetime.now(timezone.utc)
    now_loc = (now_utc + off).replace(tzinfo=None)        # naive local wall-clock

    booked: set = set()
    try:
        with _db_pool.get(read_only=True) as conn:
            # v16g4 FIX P5: also bound ABOVE — the offer builder only looks
            # BOOKING_DAYS_AHEAD out, but the scan fetched every future booked
            # row to the end of time (a clinic with months of forward bookings
            # paid for all of them on every offer).
            _horizon = (now_utc + timedelta(days=cfg.BOOKING_DAYS_AHEAD + 1)).isoformat()
            # v16g5 FIX R5-H3: widen the lower bound by one slot length so a
            # booking that STARTED before `now` but still RUNS INTO the
            # offerable window is seen by the overlap test.
            _floor = (now_utc - timedelta(minutes=step * 4)).isoformat()
            cur = _execute(conn,
                "SELECT slot_start, slot_end FROM bookings WHERE customer_id=? "
                "AND status='booked' AND slot_start >= ? AND slot_start < ?",
                (customer_id, _floor, _horizon))
            # v14g5 FIX 38: key booked slots by canonical epoch-second, not raw ISO
            # string, so dedupe survives any future formatting drift (Z vs +00:00).
            # v16g5 FIX R5-H3: carry the END of each booking too. Exact-start
            # equality alone meant a booking that did not sit on the CURRENT
            # grid blocked nothing: change BOOKING_SLOT_MINUTES 30→20 and the
            # engine happily offered 14:00–14:20 while 14:00–14:30 was taken,
            # and the unique index (on slot_start) could not catch the 14:20
            # collision either. Two patients, one chair.
            for r in cur.fetchall():
                _bs = int(_parse_dt(r["slot_start"]).timestamp())
                try:
                    _be = int(_parse_dt(r["slot_end"]).timestamp())
                except Exception:
                    _be = _bs + step * 60
                booked.add((_bs, max(_be, _bs + 1)))
    except Exception as exc:
        log.warning(f"⚠️  booking slot scan failed: {exc}")

    out: List[Tuple[datetime, datetime]] = []
    for day in range(0, cfg.BOOKING_DAYS_AHEAD + 1):
        d_loc = now_loc + timedelta(days=day)
        if d_loc.weekday() not in wkdays:
            continue
        m = open_m
        while m + step <= close_m:
            hh, mm = divmod(m, 60)
            m += step
            local_naive = d_loc.replace(hour=hh, minute=mm, second=0, microsecond=0)
            start_utc   = (local_naive - off).replace(tzinfo=timezone.utc)
            if start_utc <= now_utc + timedelta(minutes=60):
                continue
            # v16g5 FIX R5-H3: true half-open interval overlap
            # (a.start < b.end AND a.end > b.start), not start equality.
            _cs = int(start_utc.timestamp())
            _ce = _cs + step * 60
            if any(_cs < _be and _ce > _bs for _bs, _be in booked):
                continue
            out.append((start_utc, start_utc + timedelta(minutes=step)))
            if len(out) >= limit:
                return out
    return out


def booking_create(customer_id: str, phone: str, name: str,
                   start_iso: str, end_iso: str, source: str = "whatsapp") -> str:
    """Insert a booking. Returns 'ok' | 'conflict' | 'error'.
    v15g2 FIX L5: EVERY exception used to be reported as a slot conflict, so a
    DB outage told the patient 'sorry, that slot was just taken'. A unique-index
    violation (uq_book_slot, the race-safe guard) is 'conflict'; anything else
    is an infrastructure 'error' and is logged loudly. ('ok' stays truthy, so
    any legacy truthiness check keeps working.)"""
    phash = _crm_phone_hash(customer_id, phone)
    now   = _now()
    try:
        with _db_pool.get() as conn:
            # v16g6 FIX R6-C4: R5-H3 fixed interval overlap in the OFFER
            # builder only. uq_book_slot indexes slot_start EQUALITY, so after
            # a BOOKING_SLOT_MINUTES change a 14:00–14:30 row cannot block a
            # 14:20 insert — the exact scenario the R5-H3 comment names is
            # still committable from a stale offer. Re-verify half-open
            # overlap INSIDE the insert transaction (ISO-8601 UTC strings
            # compare lexicographically = chronologically). The durable DB
            # guarantee — tstzrange EXCLUDE USING gist — belongs to the next
            # migration slot; this closes the stale-offer window portably on
            # both engines today.
            _c = _execute(conn,
                "SELECT 1 FROM bookings WHERE customer_id=? AND "
                "status='booked' AND slot_start < ? AND slot_end > ? LIMIT 1",
                (customer_id, end_iso, start_iso))
            if _c.fetchone():
                analytics.inc("booking.slot_conflict")
                log.info(f"📅 booking overlap conflict (cust={customer_id})")
                return "conflict"
            _execute(conn,
                "INSERT INTO bookings (customer_id, phone_hash, enc_phone, enc_name, "
                "slot_start, slot_end, status, reminders_sent, source, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (customer_id, phash, pii_vault.encrypt(phone), pii_vault.encrypt(name or ""),
                 start_iso, end_iso, "booked", "", source, now, now))
        analytics.inc("booking.created")
        return "ok"
    except Exception as exc:
        if _is_unique_violation(exc):             # v16g4 FIX M11
            analytics.inc("booking.slot_conflict")
            log.info(f"📅 booking slot conflict (cust={customer_id})")
            return "conflict"
        analytics.inc("booking.error")
        log.error(f"❌ booking insert failed (cust={customer_id}): {exc}")
        return "error"


def booking_upcoming_for_phone(customer_id: str, phone: str) -> Optional[Dict]:
    phash   = _crm_phone_hash(customer_id, phone)
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT id, slot_start, slot_end FROM bookings WHERE customer_id=? "
                "AND phone_hash=? AND status='booked' AND slot_start >= ? "
                "ORDER BY slot_start ASC LIMIT 1", (customer_id, phash, now_iso))
            r = cur.fetchone()
            return dict(r) if r else None
    except Exception:
        return None


# v15g2: booking_cancel_upcoming() removed — orphaned by the FIX C2b
# confirmation flow (lookup via booking_upcoming_for_phone, destruction only
# via booking_cancel_by_id after an explicit YES). No other callers existed.


def booking_cancel_by_id(booking_id) -> bool:
    """v14g5 FIX 12: cancel one specific booking by id — used by reschedule, but
    only AFTER the replacement slot has been secured.
    v16g4 FIX M5: swallowed failure used to return NOTHING and every caller
    printed "✅ Cancelled" unconditionally — a DB blip mid-cancel told the
    patient it was cancelled while the row stayed booked (and on reschedule
    they could end up holding two slots). Now returns True only when a row
    actually transitioned booked→cancelled."""
    try:
        with _db_pool.get() as conn:
            cur = _execute(conn, "UPDATE bookings SET status='cancelled', updated_at=? "
                                 "WHERE id=? AND status='booked'", (_now(), booking_id))
            changed = (getattr(cur, "rowcount", -1) or 0) > 0
        if changed:
            analytics.inc("booking.cancelled")
        return changed
    except Exception as exc:
        log.warning(f"⚠️  booking cancel-by-id failed: {exc}")
        analytics.inc("booking.cancel_failed")
        return False


# v16g3 FIX R3-H2: two-tier intent vocabulary. STRONG words alone mean the
# patient wants a slot. The old flat list let WEAK time/consult vocabulary
# hijack informational questions — "what is the vaccination schedule for my
# baby", "fees for consult", "what are your timings" all got a slot list
# instead of an answer. WEAK words now fire only beside a booking-context cue
# ("is the doctor available", "checkup tomorrow" still book); everything else
# falls through to the AI, which actually answers the question.
_BOOK_WORDS_STRONG = ("book", "appointment", "appointments", "appoint",
                      "booking", "bookings", "slot", "slots", "reserve",
                      "appointment venum", "varalama")
_BOOK_WORDS_WEAK   = ("schedule", "available", "availability", "timing",
                      "timings", "consult", "checkup", "check-up", "neram",
                      "milna", "samay", "dikhana")
_BOOK_CONTEXT      = ("appointment", "book", "slot", "visit", "doctor", "dr",
                      "clinic", "tomorrow", "today", "when", "free", "time")
_BOOK_WORDS = _BOOK_WORDS_STRONG + _BOOK_WORDS_WEAK   # back-compat alias
_CANCEL_WORDS = ("cancel", "cancel appointment", "cancel booking", "cancel pannu",
                 "venda", "radd")
_RESCHED_WORDS = ("reschedule", "change appointment", "change time", "postpone",
                  "vera time", "time maathu", "time change")
_STATUS_WORDS = ("my appointment", "my booking", "when is my", "appointment status",
                 "booking status")

# v15g2 FIX C2b: explicit YES vocabulary for the cancel-confirmation step
# (en / ta / hi + the tapped button id). Anything NOT in this set keeps the
# appointment — the only safe default for a destructive action.
# v16g4 FIX M3: "ok"/"okay"/"சரி"/"ठीक है" — the most common "understood"
# tokens in the launch market — were in the YES set and destroyed the
# appointment, while the fallback prompt promised "Reply *YES*… or *NO*".
# They are now AMBIGUOUS-ACK tokens that trigger a re-confirm instead.
_CANCEL_YES_RAW = ("yes", "y", "yeah", "yep", "yes cancel", "confirm", "sure",
                   "aama", "ama", "aamaa", "haan", "ha", "ji haan",
                   "ஆமாம்", "ஆமா", "ஆம்", "हाँ", "हां", "जी हाँ")
_CANCEL_YES = {_norm_text(x) for x in _CANCEL_YES_RAW}
_CANCEL_ACK_RAW = ("ok", "okay", "k", "kk", "hmm", "hm", "sari", "seri",
                   "சரி", "ठीक है", "theek hai", "thik hai", "acha", "accha")
_CANCEL_ACK = {_norm_text(x) for x in _CANCEL_ACK_RAW}   # v16g4 FIX M3
_CANCEL_NO_RAW = ("no", "n", "nope", "no keep it", "keep", "keep it", "dont",
                  "dont cancel", "vendam", "venda", "illa", "illai",
                  "வேண்டாம்", "இல்லை", "नहीं", "nahi", "nahin", "mat karo")
_CANCEL_NO = {_norm_text(x) for x in _CANCEL_NO_RAW}     # v16g4 FIX M4

# v16g4 port (audit item 201): exact-match global marketing opt-out keywords.
# Deliberately an EXACT-message match (not a substring check) so an ordinary
# sentence containing the word "stop" is never mistaken for an unsubscribe.
# v16g6 FIX R6-H8: English-only consent in a Tamil-first product is not a
# defensible posture under DPDP — a patient typing நிறுத்து could not
# unsubscribe while every other system string was localised in v16g4.
# ta/hi + romanised forms, normalised through _norm_text (the same
# discipline _CANCEL_NO_RAW already uses), plus the standard template
# quick-reply payloads, which arrive as button taps.
_OPT_OUT_RAW = (
    "stop", "unsubscribe", "stop all", "opt out", "optout",
    "stop promotions", "stop promotion",
    "நிறுத்து", "நிறுத்துங்க", "நிறுத்துங்கள்",
    "niruthu", "niruthunga", "stop pannu", "stop pannunga",
    "message vendam", "msg vendam", "sms vendam",
    "बंद करो", "रोको", "band karo", "bandh karo", "message band karo",
)
_OPT_OUT_KEYWORDS = {_norm_text(x) for x in _OPT_OUT_RAW}


def detect_booking_intent(text: str) -> Optional[str]:
    """v15g2 FIX C2a (CRITICAL): was raw substring matching — 'cancel' matched
    inside 'canCELLATION policy', 'available' inside 'UNavailable', 'consult'
    inside 'consultation fee' — so ordinary questions were hijacked by the
    booking engine and (before FIX C2b) a policy QUESTION instantly cancelled a
    patient's real appointment. Now whole-word + negation-aware via _kw_hit,
    the exact matcher v15 FIX 4 already gave business-type detection."""
    norm = _norm_text(text)
    if not norm:
        return None
    if any(_kw_hit(norm, w) for w in _RESCHED_WORDS): return "reschedule"
    # v16g3 FIX R3-H3: pre_w=2 catches "please don't ever cancel"; a wrongly
    # skipped genuine cancel is safe — the read-only status branch (post_w=0,
    # so "cancel my appointment illa" resolves to STATUS, not a slot list)
    # or the AI picks it up, and destruction always re-confirms anyway.
    if any(_kw_hit(norm, w, pre_w=2) for w in _CANCEL_WORDS):  return "cancel"
    if any(_kw_hit(norm, w, post_w=0) for w in _STATUS_WORDS): return "status"
    if any(_kw_hit(norm, w) for w in _BOOK_WORDS_STRONG):      return "book"
    if (any(_kw_hit(norm, w) for w in _BOOK_WORDS_WEAK)        # v16g3 FIX R3-H2
            and any(_kw_hit(norm, c) for c in _BOOK_CONTEXT)):
        return "book"
    return None


def _parse_slot_pick(text: str) -> Optional[int]:
    t = (text or "").strip().lower()
    # v15g4 FIX B3: the 'slot:N' interactive-id branch moved to handle_booking,
    # where taps are matched by EPOCH against the current offer — this parser
    # now handles TYPED picks only.
    # v15 FIX 9 (MEDIUM): only a BARE pick counts — '3', 'no 3', '#3',
    # 'option 3.', '3.'. The old \D*(\d{1,2})\D* matched a number ANYWHERE in a
    # sentence, so "can I come at 5?" booked slot #5 (a totally different time)
    # and "I prefer 2pm" booked slot #2. Anything else → re-offer with guidance.
    m = re.fullmatch(r"(?:no\.?\s*|option\s*|#\s*)?(\d{1,2})\s*\.?", t)
    if m:
        return int(m.group(1))
    return None


def _booking_owner_of_slot(customer_id: str, start_iso: str) -> Optional[Dict]:
    """v15g4 FIX B10: who holds this exact slot, if anyone? Used to recognise
    a patient rescheduling onto the appointment they ALREADY have (the unique
    index reports it as a 'conflict', which used to loop 'just taken' forever)."""
    try:
        with _db_pool.get(read_only=True) as conn:
            # v16g6 FIX R6-L12: exact-string equality on slot_start breaks
            # the moment two writers format the same instant differently
            # (+00:00 vs Z, microseconds present or not) — B10's
            # self-conflict detection then misses and the patient loops on
            # "just taken". Match the parsed INSTANT over the enclosing
            # minute window instead.
            _t0 = _parse_dt(start_iso)
            cur = _execute(conn,
                "SELECT id, phone_hash, slot_start FROM bookings "
                "WHERE customer_id=? AND status='booked' "
                "AND slot_start >= ? AND slot_start < ? LIMIT 8",
                (customer_id,
                 (_t0 - timedelta(minutes=1)).isoformat(),
                 (_t0 + timedelta(minutes=1)).isoformat()))
            for _r in cur.fetchall():
                try:
                    if _parse_dt(_r["slot_start"]) == _t0:
                        return {"id": _r["id"], "phone_hash": _r["phone_hash"]}
                except Exception:
                    continue
            row = None
        return dict(row) if row else None
    except Exception as exc:
        log.warning(f"⚠️  _booking_owner_of_slot failed: {exc}")
        return None


def _booking_status_text(b: Optional[Dict], lang: str = "en") -> str:
    """v14g5 FIX 49: one canonical 'your appointment' message so the wording can
    never drift between the status branch and any future caller.
    v16g4 FIX M8: localized."""
    if b:
        return _t("status_upcoming", lang, when=_fmt_local_dt(b['slot_start']))
    return _t("status_none", lang)


def handle_booking(brain: Dict, from_phone: str, user_text: str,
                   out_pid: str, out_tok: str, customer_id: str,
                   session_id: str, subject_name: str = "") -> bool:
    """Deterministic booking state machine. Returns True if it handled the
    message (caller should then stop). Returns False to let the normal AI run.
    v14g5 FIX 12: a RESCHEDULE no longer cancels the existing appointment up-front;
    the old slot is carried as prev_id and retired ONLY after a new slot is secured,
    so abandoning the flow can never leave the patient with no appointment."""
    if not cfg.ENABLE_BOOKING:
        return False

    offer_key  = f"bk_offer:{customer_id}:{from_phone}"
    cancel_key = f"bk_cancel:{customer_id}:{from_phone}"   # v15g2 FIX C2b
    booked_ok  = False                                     # v16 U3
    text      = (user_text or "").strip()
    low       = text.lower()
    lang      = _user_lang(customer_id, from_phone, text)  # v16g4 FIX M8
    # ('text',msg) | ('list',body,rows,payload) | ('confirm',body,buttons)
    action: Optional[Tuple] = None

    # v15g2 FIX C2b (CRITICAL): a pending cancel-confirmation is answered FIRST.
    # Cancelling is destructive — it now requires an explicit YES (button tap or
    # typed). Any other reply keeps the appointment: the safe default.
    pending_cancel = brain_cache.get(cancel_key)
    if pending_cancel:
        # v16g6 FIX R6-M14: the window was consumed at the TOP, so an
        # unrelated reply ("fine", "done", a question) silently destroyed
        # the pending confirmation — the patient's later YES did nothing,
        # and the AI answered with no idea a cancellation was pending.
        # Consume the window only on the branches that RESOLVE it; the
        # unmatched fall-through keeps it armed for its remaining TTL.
        # v16g3 FIX R3-L7: taps arrive as 'Title [id]' now — match button
        # ids by substring so readable history and the state machine coexist.
        if "cancel:yes" in low or _norm_text(text) in _CANCEL_YES:
            brain_cache.delete(cancel_key)
            try:
                _pending_id = int(pending_cancel)
            except (TypeError, ValueError):
                _pending_id = None
            b = booking_upcoming_for_phone(customer_id, from_phone)
            if b and (_pending_id is None or b["id"] == _pending_id):
                # v16g4 FIX M5: only claim "Cancelled" when the row actually
                # transitioned — a DB blip no longer lies to the patient.
                if booking_cancel_by_id(b["id"]):
                    action = ("text", _t("cancelled_ok", lang,
                                         when=_fmt_local_dt(b['slot_start'])))
                else:
                    action = ("text", _t("cancel_failed", lang))
            else:
                action = ("text", _t("already_changed", lang))
        elif "cancel:no" in low or _norm_text(text) in _CANCEL_NO:
            # v16g3 FIX R3-M5: the explicit keep-tap is never re-read as a
            # fresh cancel intent. v16g4 FIX M4: typed "no"/"vendam"/"नहीं"
            # count as the explicit keep too.
            brain_cache.delete(cancel_key)               # v16g6 FIX R6-M14
            action = ("text", _t("keep_unchanged", lang))
        elif _norm_text(text) in _CANCEL_ACK:
            # v16g4 FIX M3: "ok"/"சரி"/"ठीक है" is an acknowledgement, not a
            # confirmed destruction. Re-arm the window and ask plainly.
            brain_cache.set(cancel_key, pending_cancel, ttl=300)
            action = ("text", _t("reconfirm_cancel", lang))
        elif detect_booking_intent(text) in ("book", "reschedule", "status"):
            # v15g4 FIX B11: a booking intent typed inside the confirm window
            # was discarded with "your appointment is unchanged" and the
            # patient had to repeat themselves. The appointment still stays
            # (safe default) — but the intent now falls through to the normal
            # flow below and gets SERVED.
            brain_cache.delete(cancel_key)               # v16g6 FIX R6-M14
            action = None
        else:
            # v16g4 FIX M4 (last residue of the A3/B11 class): "wait, what
            # time was it?" inside the confirm window was swallowed and the
            # question never reached the AI. v16g6 FIX R6-M14: the window now
            # stays ARMED for its remaining TTL — the question gets answered
            # below, and a follow-up YES/NO still lands on the pending
            # cancellation instead of doing nothing.
            return False
        if action is not None:
            # v16g5 FIX R5-M1: this was the only _booking_dispatch call site
            # in the file that omitted lang=, so a Tamil/Hindi patient
            # confirming a cancellation got the English "Reply *YES* / *NO*"
            # fallback wording — an M8 gap hiding in the most destructive
            # branch of the state machine.
            _booking_dispatch(action, from_phone, out_pid, out_tok, customer_id,
                              session_id, user_text, lang=lang)
            return True

    # v16g3 FIX R3-M5: a "No, keep it" tap landing AFTER the 5-min confirm
    # TTL used to be re-read as a fresh CANCEL intent — the bot answered
    # "keep it" by asking "are you sure you want to cancel?" again. A stale
    # keep-tap now just keeps. (A stale cancel:yes still re-confirms — the
    # safe direction for a destructive action.)
    if "cancel:no" in low:
        _booking_dispatch(("text", _t("keep_unchanged", lang)),
                          from_phone, out_pid, out_tok, customer_id,
                          session_id, user_text, lang=lang)   # v16g4 FIX M8
        return True

    raw_offer = brain_cache.get(offer_key)
    if raw_offer:
        # An offer is active — interpret this message as a slot pick / abort.
        try:
            payload = json.loads(raw_offer)
            if isinstance(payload, dict):
                offers  = payload.get("slots", [])
                prev_id = payload.get("prev_id")
            else:                       # tolerate pre-FIX bare-list payloads in cache
                offers, prev_id = payload, None
        except Exception:
            offers, prev_id = [], None

        # v15 FIX 10 (MEDIUM): the abort list was exact-match only, so a patient
        # typing "cancel appointment" or "cancel pannu" MID-OFFER fell through
        # to slot parsing and got "Please reply with the number…" forever. Any
        # cancel intent now aborts the flow (the existing appointment, if any,
        # stays untouched — same safe semantics as before).
        if (low in ("stop", "no", "exit")
                or detect_booking_intent(text) == "cancel"):
            brain_cache.delete(offer_key)
            # FIX 12: abandoning a reschedule must NOT lose the original booking —
            # we never cancelled it, so it simply stands.
            kept = _t("kept_note", lang) if prev_id else ""
            # v16g6 FIX R6-M15: inside a booking flow "stop" deliberately
            # means "abort this flow", NOT the global unsubscribe (the R6-H8
            # gate excludes active flows for exactly that reason). The
            # narrower meaning is defensible; saying nothing about it is not
            # — the patient hears "okay, stopped" and reasonably believes
            # they unsubscribed. Say so, and say how to actually do it.
            _note = {"ta": "நீங்கள் unsubscribe ஆகவில்லை — செய்திகளை "
                           "நிறுத்த 'STOP' என்று மட்டும் தனியாக அனுப்புங்கள்.",
                     "hi": "आप अनसब्सक्राइब नहीं हुए हैं — संदेश बंद करने "
                           "के लिए केवल 'STOP' भेजें।",
                     }.get(lang, "You are still subscribed — to stop "
                                 "receiving messages, send just 'STOP'.")
            action = ("text", _t("stop_booking", lang, kept=kept)   # v16g4 FIX M8
                              + "\n" + _note)
        else:
            pick, stale_tap = None, False
            m_tap = re.search(r"slot:(\d+)", low)
            if m_tap:
                # v15g4 FIX B3: a tap is matched by EPOCH to the exact time the
                # button displayed. No match = the tap came from a superseded
                # (or pre-GEN4) list → offer fresh times, never a wrong slot.
                want = m_tap.group(1)
                for i, pair in enumerate(offers):
                    try:
                        if str(int(datetime.fromisoformat(pair[0]).timestamp())) == want:
                            pick = i + 1
                            break
                    except Exception:
                        continue
                stale_tap = pick is None
            else:
                pick = _parse_slot_pick(text)
            if stale_tap:
                action = _booking_offer_action(customer_id,
                    note=_t("offer_expired", lang),
                    prev_id=prev_id, lang=lang)   # v16g4 FIX M8
            elif pick is not None and 1 <= pick <= len(offers):
                start_iso, end_iso = offers[pick - 1]
                res = booking_create(customer_id, from_phone, subject_name,
                                     start_iso, end_iso)
                if res == "ok":
                    brain_cache.delete(offer_key)
                    # only NOW retire the old slot — the reschedule has succeeded
                    _retired = booking_cancel_by_id(prev_id) if prev_id else True
                    if prev_id and not _retired:
                        # v16g4 FIX M5: the new slot IS booked but the old row
                        # refused to die — the patient now holds two slots.
                        # Say "confirmed" (true), and scream so you reconcile.
                        log.critical(f"🛑 reschedule retire FAILED — patient "
                                     f"holds TWO slots (old id={prev_id}, "
                                     f"cust={customer_id}). Reconcile manually.")
                        analytics.inc("booking.retire_failed")
                    _msg_key = ("booked_rescheduled" if (prev_id and _retired)
                                else "booked_confirmed")
                    booked_ok = True                       # v16 U3
                    action = ("text", _t(_msg_key, lang,
                                         when=_fmt_local_dt(start_iso)))
                elif res == "conflict":
                    # v15g4 FIX B10: if the "taken" slot is the patient's OWN
                    # current appointment (rescheduling onto the time they
                    # already hold), the old branch looped "just taken — fresh
                    # times" forever. Recognise self-conflict and keep it.
                    own = _booking_owner_of_slot(customer_id, start_iso)
                    if own and own.get("phone_hash") == _crm_phone_hash(customer_id, from_phone):
                        brain_cache.delete(offer_key)
                        action = ("text", _t("own_slot_kept", lang,
                                             when=_fmt_local_dt(start_iso)))
                    else:
                        # genuinely taken by someone else — re-offer, PRESERVING
                        # prev_id so the next pick still reschedules.
                        action = _booking_offer_action(customer_id,
                            note=_t("slot_taken", lang),
                            prev_id=prev_id, lang=lang)
                else:
                    # v15g2 FIX L5: infrastructure error ≠ taken slot. Keep the
                    # existing offer in cache (never deleted) so their retry works.
                    action = ("text", _t("save_error", lang))
            else:
                action = _booking_offer_action(customer_id,
                    note=_t("pick_number", lang),
                    prev_id=prev_id, lang=lang)
    else:
        # v16g4 FIX M15: no ACTIVE offer, but the patient just typed a bare
        # slot number ("2") shortly after the offer TTL lapsed. Without this,
        # the number fell through to the AI as arbitrary text. If a recent
        # tombstone is present, treat it as a stale pick and re-offer fresh
        # times (never book blindly — the old list's times may be gone).
        if (cfg.ENABLE_BOOKING and _parse_slot_pick(text) is not None
                and not re.search(r"slot:\d+", low)
                and brain_cache.get(f"bk_offer_recent:{customer_id}:{from_phone}")):
            brain_cache.delete(f"bk_offer_recent:{customer_id}:{from_phone}")
            _booking_dispatch(
                _booking_offer_action(customer_id,
                                      note=_t("offer_expired", lang),
                                      lang=lang),
                from_phone, out_pid, out_tok, customer_id,
                session_id, user_text, lang=lang)
            return True
        intent = detect_booking_intent(text)
        if not intent:
            return False
        if intent == "status":
            b = booking_upcoming_for_phone(customer_id, from_phone)
            action = ("text", _booking_status_text(b, lang))   # v16g4 FIX M8
        elif intent == "cancel":
            # v15g2 FIX C2b (CRITICAL): NEVER cancel on intent alone — the old
            # branch destroyed the appointment instantly, so "what is your
            # cancellation policy?" and "I do NOT want to cancel" both deleted a
            # patient's real booking. Now: stash the booking id (5-min window)
            # and ask an explicit yes/no via wa_send_buttons_now — the function
            # whose own docstring said it was "used for yes/no confirmations
            # (cancel, reschedule)" yet was never called anywhere until now.
            b = booking_upcoming_for_phone(customer_id, from_phone)
            if not b:
                action = ("text", _t("no_upcoming_cancel", lang))   # v16g4 FIX M8
            else:
                brain_cache.set(cancel_key, str(b["id"]), ttl=300)
                action = ("confirm",
                    _t("cancel_confirm", lang,
                       when=_fmt_local_dt(b['slot_start'])),
                    [{"id": "cancel:yes", "title": _t("btn_yes_cancel", lang)},
                     {"id": "cancel:no",  "title": _t("btn_no_keep", lang)}])
        else:  # book or reschedule
            prev_id = None
            if intent == "reschedule":
                # FIX 12: capture (do NOT cancel) the current appointment.
                existing = booking_upcoming_for_phone(customer_id, from_phone)
                prev_id  = existing["id"] if existing else None
            action = _booking_offer_action(customer_id, prev_id=prev_id,
                                           lang=lang)   # v16g4 FIX M8

    if action is None:
        return False
    _booking_dispatch(action, from_phone, out_pid, out_tok, customer_id,
                      session_id, user_text, lang=lang)   # v16g4 FIX M8
    if booked_ok:
        # v16 U3: booking secured → if this patient is username-only (BSUID)
        # and we hold no real number, ask exactly once. Reminders need it;
        # the ask rides AFTER the ✅ confirmation so the flow feels natural.
        _maybe_request_phone(customer_id, from_phone, out_pid, out_tok,
                             lang=lang)   # v16g4 FIX M8
    return True


def _booking_offer_action(customer_id: str, note: str = "", prev_id=None,
                          lang: str = "en") -> Tuple:
    """Build the slot-offer action AND stash the offered slots (plus any prev_id
    being rescheduled) in cache so the next inbound message can be matched to a
    slot by index and complete the reschedule atomically.
    v16g4 FIX M8: localized note + no-slots line."""
    slots = booking_available_slots(customer_id, cfg.BOOKING_SLOTS_SHOWN)
    if not slots:
        return ("text", _t("no_slots", lang))
    offers = [[s.isoformat(), e.isoformat()] for s, e in slots]
    # v15g4 FIX B3: the row id used to be a bare index (slot:3). A tap on a
    # STALE list — after a newer offer replaced the cache — booked index 3 of
    # the NEW list: a different datetime than the button displayed. The id now
    # carries the slot's epoch, so a tap is matched to the exact time it
    # showed, and a mismatch triggers a fresh list instead of a wrong booking.
    rows = [{"id": f"slot:{int(s.timestamp())}", "title": _fmt_local_dt(s)[:24],
             "description": _fmt_local_time_range(s, e)}
            for s, e in slots]                        # v16g2 FIX C4: unused `i`
    body = ((note + "\n\n") if note else "") + _t("offer_header", lang)
    return ("list", body, rows, {"slots": offers, "prev_id": prev_id})


def _booking_dispatch(action: Tuple, from_phone: str, out_pid: str, out_tok: str,
                      customer_id: str, session_id: str, user_text: str,
                      lang: str = "en") -> None:
    """Record the turn, THEN send — v15g2 FIX L4: this path was send-then-persist,
    contradicting the v14g5 FIX 50 persist-then-send standard, so a crash between
    the network send and the save dropped the turn from history. Handles three
    kinds: plain text, interactive slot list (numbered-text fallback), and yes/no
    confirmation buttons (typed YES/NO fallback — v15g2 FIX C2b)."""
    if action[0] == "list":
        _, body, rows, payload = action
        brain_cache.set(f"bk_offer:{customer_id}:{from_phone}",
                        json.dumps(payload), ttl=900)
        # v16g4 FIX M15: leave a short tombstone so a bare slot-number typed
        # just after the 15-min offer TTL lapsed is recognised as a stale
        # pick (→ re-offer) instead of being handed to the AI as if it were
        # arbitrary text ("please reply with a number" loop / nonsense reply).
        brain_cache.set(f"bk_offer_recent:{customer_id}:{from_phone}", "1",
                        ttl=3600)
        # offer and cancel-confirmation states must never coexist
        brain_cache.delete(f"bk_cancel:{customer_id}:{from_phone}")
        numbered = "\n".join(f"{i+1}. {r['title']} ({r['description']})"
                             for i, r in enumerate(rows))
        log_text = body + "\n\n" + numbered
    elif action[0] == "confirm":                      # v15g2 FIX C2b
        _, body, _buttons = action
        log_text = body + "\n\n" + _t("typed_yes_no", lang)   # v16g4 FIX M8
    else:
        _, msg = action
        log_text = msg
    try:
        save_messages_batch(session_id, [
            ("user",  user_text, "whatsapp", 0),
            ("model", log_text,  "booking",  0)])
        increment_chat_count(customer_id)
        analytics.inc("booking.handled")
    except Exception as _pe:
        # v16g2 FIX L12: the whole point of persist-then-send is the audit
        # trail existing — a swallowed save must at least be visible.
        analytics.inc("booking.persist_failed")
        log.warning(f"⚠️  booking turn persist failed (session={session_id}): {_pe}")
    if action[0] == "list":
        _, body, rows, _payload = action
        sent = wa_send_list_now(from_phone, body, _t("btn_pick_time", lang),
                                rows, out_pid, out_tok, customer_id,
                                header=_t("hdr_book", lang))   # v16g4 FIX M8
        if not sent:
            send_whatsapp_sync(from_phone, log_text, out_pid, out_tok, customer_id)
    elif action[0] == "confirm":
        _, body, buttons = action
        sent = wa_send_buttons_now(from_phone, body, buttons,
                                   out_pid, out_tok, customer_id)
        if not sent:
            send_whatsapp_sync(from_phone, log_text, out_pid, out_tok, customer_id)
    else:
        send_whatsapp_sync(from_phone, log_text, out_pid, out_tok, customer_id)
