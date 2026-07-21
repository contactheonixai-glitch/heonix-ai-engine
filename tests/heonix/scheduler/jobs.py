"""HEONIX GEN-5 · module `heonix.scheduler.jobs`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 7840-8196).
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
from heonix.booking.engine import (_fmt_local_dt, _parse_dt, _to_local)
from heonix.cache import (brain_cache)
from heonix.config import (cfg)
from heonix.crm import (_resolve_send_addr)
from heonix.db.core import (_db_true, _execute)
from heonix.db.store import (
    _wa_in_service_window,
    get_customer_brain,
    is_opted_out_checked,
    outbox_publish,
)
from heonix.i18n import (_t, _user_lang)
from heonix.logsetup import (log)
from heonix.security.crypto import (pii_vault)
from heonix.utils import (_now)
from heonix import _latebind  # GEN-5 SPLIT
_db_pool: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.db.core at startup
_latebind.register('_db_pool', __name__)


def _publish_reminder(customer_id: str, phone: str, when_text: str, full_msg: str) -> bool:
    """v16g5 FIX R5-H1: FIX H2's own reasoning — "a cold lead is BY DEFINITION
    outside the 24h customer-service window, so the free-text fallback burned
    5 outbox retries per lead per tick" — applies VERBATIM to a 24-hour
    appointment reminder: a patient who booked yesterday and hasn't messaged
    since is outside the window too. H2 guarded _publish_followup and left
    this twin free-texting. With REMINDER_TEMPLATE unset (the default ""),
    every 24h reminder burned its attempt budget and dead-lettered while
    `scheduler.reminders_scanned` read perfectly healthy.

    Free text is still permitted for a reminder falling INSIDE the window
    (the 2-hour lead for a patient who chatted this morning) — that one
    genuinely delivers — but only when we can see an open session."""
    # v16g5: BSUID-aware, matching _publish_followup (was missing here).
    phone = _resolve_send_addr(customer_id, phone)
    if cfg.REMINDER_TEMPLATE:
        return outbox_publish("whatsapp.template", {
            "to": phone, "customer_id": customer_id,
            "template": cfg.REMINDER_TEMPLATE, "lang": cfg.REMINDER_TEMPLATE_LANG,
            "body_param": when_text})
    # No template. Free text can only land if this patient messaged us inside
    # the last 24h — _wa_touch_window records that on every inbound.
    if _wa_in_service_window(customer_id, phone):
        return outbox_publish("whatsapp.send",
                              {"to": phone, "customer_id": customer_id,
                               "message": full_msg})
    if brain_cache.setnx("warn:reminder_no_template", ttl=3600):
        log.warning("⚠️  reminder skipped — REMINDER_TEMPLATE is unset and the "
                    "patient is outside WhatsApp's 24h service window, so a "
                    "business-initiated free text CANNOT be delivered "
                    "(v16g5 FIX R5-H1). Approve a reminder template in Meta "
                    "Business Manager and set REMINDER_TEMPLATE.")
    analytics.inc("scheduler.reminder_no_template")
    return False


def _publish_followup(customer_id: str, phone: str, full_msg: str) -> bool:
    """v16g4 FIX H2: a cold-lead nudge is BY DEFINITION outside the 24-hour
    customer-service window — that is what makes the lead cold. The free-text
    fallback therefore could not deliver: every nudge burned 5 outbox retries
    and dead-lettered, at ~3 API calls per lead per tick, while the counter
    happily read 'followup_sent'. Template or nothing."""
    phone = _resolve_send_addr(customer_id, phone)   # v16 U3: BSUID-aware
    if not cfg.FOLLOWUP_TEMPLATE:
        log.warning("⚠️  follow-up skipped — FOLLOWUP_TEMPLATE unset; a "
                    "business-initiated free text outside the 24h window "
                    "cannot be delivered (v16g4 FIX H2).")
        analytics.inc("scheduler.followup_no_template")
        return False
    # v16g2 FIX M8: propagate the publish outcome (see _publish_reminder).
    # v16g6 FIX R6-C1: `full_msg` — the per-lead LOCALISED body the caller
    # builds via _t("followup", …) — was discarded, so every cold-lead nudge
    # sent the literal English string "follow-up" as {{1}}. All the ta/hi
    # localisation on this path was dead code. Pass it through, capped to
    # Meta's template-parameter budget. Compare _publish_reminder, which
    # passes when_text — same shape, one branch was wired and one was not.
    return outbox_publish("whatsapp.template", {
        "to": phone, "customer_id": customer_id,
        "template": cfg.FOLLOWUP_TEMPLATE, "lang": cfg.FOLLOWUP_TEMPLATE_LANG,
        "body_param": (full_msg or "follow-up")[:640]})


def _scheduler_send_reminders() -> None:
    """Fire each configured lead-time reminder exactly once per booking."""
    leads = sorted({int(x) for x in cfg.REMINDER_LEAD_HOURS.split(",")
                    if x.strip().lstrip("-").isdigit() and int(x) > 0}, reverse=True)
    if not leads:
        return
    now_utc = datetime.now(timezone.utc)
    horizon = (now_utc + timedelta(hours=leads[0])).isoformat()
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT id, customer_id, enc_phone, slot_start, slot_end, reminders_sent "
                "FROM bookings WHERE status='booked' AND slot_start > ? AND slot_start <= ?",
                (now_utc.isoformat(), horizon))
            rows = [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        log.warning(f"⚠️  reminder scan failed: {exc}")
        return
    # v16g6 FIX R6-M17: memoise consent lookups for the tick — the loop
    # consulted is_opted_out up to twice per due booking, each cold lookup a
    # synchronous DB round-trip inside the single-leader tick; with a few
    # hundred bookings in the horizon that is a query storm, and the storm
    # is what made R6-H9 reachable in the first place.
    _oo_memo: Dict[Tuple[str, str], Tuple[bool, bool]] = {}

    def _oo(cust: str, addr: str) -> Tuple[bool, bool]:
        _k = (cust, addr)
        if _k not in _oo_memo:
            _oo_memo[_k] = is_opted_out_checked(cust, addr)
        return _oo_memo[_k]

    for b in rows:
        try:
            start = _parse_dt(b["slot_start"])
            sent  = {x for x in (b.get("reminders_sent") or "").split(",") if x}
            changed = False
            # v15g2 FIX M2: a booking created INSIDE several lead windows (e.g.
            # 90 min out with REMINDER_LEAD_HOURS="24,2") fired EVERY due lead in
            # the same tick — the patient got two near-identical reminders
            # back-to-back. Fire only the CLOSEST due lead; consume the larger
            # ones silently so they can never fire later either.
            due = [h for h in leads
                   if str(h) not in sent and now_utc >= start - timedelta(hours=h)]
            if due:
                phone = pii_vault.decrypt(b["enc_phone"])
                if not phone or phone == "[ENCRYPTED]":
                    # v16g2 FIX M7: mirror B12 — a decrypt failure is now
                    # VISIBLE (counter + warning) and the leads are NOT
                    # consumed, so a repaired ENCRYPTION_KEY resumes these
                    # reminders instead of them being silently marked handled.
                    analytics.inc("scheduler.reminder_skipped_decrypt")
                    log.warning(f"⚠️  reminder skipped — phone undecryptable "
                                f"(booking id={b.get('id')}, "
                                f"cust={b.get('customer_id')})")
                    continue
                # v16 U3: bookings made by username patients store the
                # BSUID here. Prefer the real number if it was captured
                # since; otherwise the BSUID itself is a valid recipient
                # ('Send to BSUID').
                # v16g5 FIX R5-H4: reminders read `bookings` and never
                # consulted consent at ALL — a patient who texted STOP kept
                # getting appointment reminders. Check the suppression under
                # every spelling the booking may have been keyed on.
                # v16g6 FIX R6-H9: fail-closed is right for the SEND, wrong
                # for the CONSUME. A transient lookup blip returned True here
                # and the block below then marked every due lead handled
                # FOREVER — the patient misses the visit while the dashboard
                # says the reminder went out. Suppressed (known) → consume;
                # unknown → skip THIS tick, keep the leads, retry next tick.
                _checks = [_oo(b["customer_id"], _p) for _p in          # R6-M17
                           dict.fromkeys([phone, _resolve_send_addr(b["customer_id"], phone)])
                           if _p]
                if any(_sup and _known for _sup, _known in _checks):
                    analytics.inc("scheduler.reminder_skipped_optout")
                    for h in due:
                        sent.add(str(h))
                    with _db_pool.get() as conn:
                        _execute(conn, "UPDATE bookings SET reminders_sent=?, "
                                       "updated_at=? WHERE id=?",
                                 (",".join(sorted(sent)), _now(), b["id"]))
                    continue
                if any(not _known for _sup, _known in _checks):
                    analytics.inc("scheduler.reminder_optout_unknown")
                    log.warning(f"⚠️  opt-out state UNKNOWN (lookup failing) "
                                f"— holding reminder for booking "
                                f"id={b.get('id')} until it can be verified "
                                f"(v16g6 FIX R6-H9)")
                    continue
                phone   = _resolve_send_addr(b["customer_id"], phone)
                when    = _fmt_local_dt(b["slot_start"])
                # v14g5 FIX 24: word the lead from the ACTUAL remaining time, not
                # the configured lead bucket (a slot 1h away no longer says "~2h").
                rem_h   = max(0, int(round((start - now_utc).total_seconds() / 3600)))
                # v16g4 FIX L5: "tomorrow" was a raw >=20h test, so a 10 p.m.
                # scan for a 9 a.m. slot the NEXT MORNING (11h) said "in ~11
                # hour(s)" while a Friday-2 p.m. scan for a Saturday-11 a.m.
                # slot (21h) could say "tomorrow" — and a 21h gap that lands
                # the day after tomorrow said "tomorrow" too. Word it from the
                # LOCAL CALENDAR DAY difference, which is what a patient reads.
                _lg = _user_lang(b["customer_id"], phone)     # v16g4 FIX M8
                day_diff = (_to_local(start).date()
                            - _to_local(now_utc).date()).days
                if rem_h <= 1:
                    hrs_txt = _t("t_in_hour", _lg)
                elif day_diff == 0:
                    hrs_txt = _t("t_today", _lg)
                elif day_diff == 1:
                    hrs_txt = _t("t_tomorrow", _lg)
                else:
                    hrs_txt = _t("t_in_hours", _lg, n=rem_h)
                # v16g4 FIX M12: claim this exact (booking, lead) BEFORE
                # publishing. The old order was publish → UPDATE; if the
                # UPDATE failed (DB blip, pool exhaustion) the swallowed
                # exception left reminders_sent unchanged and the NEXT tick
                # re-published the same reminder — a patient could be pinged
                # every minute. The claim is the idempotency fence; losing it
                # still sets changed=True so the missed UPDATE self-heals.
                _claim = f"rem:{b['id']}:{max(due)}"
                if not brain_cache.setnx(_claim, ttl=6 * 3600):
                    log.info(f"♻️  reminder already claimed this window "
                             f"(booking id={b.get('id')}) — repairing row only")
                    for h in due:
                        sent.add(str(h))
                    changed = True
                    published = None                  # skip the publish
                else:
                    published = _publish_reminder(b["customer_id"], phone, when,
                        _t("reminder", _lg, hrs=hrs_txt, when=when))
                if published:                         # v16g2 FIX M8
                    for h in due:      # consume ALL due leads, not only the fired one
                        sent.add(str(h))
                    changed = True
                elif published is False:
                    brain_cache.delete(_claim)        # v16g4 FIX M12: allow retry
                    log.warning(f"⚠️  reminder publish failed — leads kept for "
                                f"retry (booking id={b.get('id')})")
            if changed:
                # v16g5 FIX R5-M6: `sorted(sent, key=lambda x: -int(x))`
                # raised on ANY non-numeric token that ever reached
                # reminders_sent (a partial write, a manual edit, a future
                # lead format). The outer except swallowed it, so that
                # booking's row NEVER updated again and re-entered the due set
                # on every tick — only the 6h setnx claim contained it. Sort
                # defensively and drop junk instead of exploding.
                def _lead_key(x):
                    try:
                        return -int(x)
                    except (TypeError, ValueError):
                        return 0
                _clean = sorted({x for x in sent if str(x).strip()}, key=_lead_key)
                with _db_pool.get() as conn:
                    _execute(conn, "UPDATE bookings SET reminders_sent=?, updated_at=? WHERE id=?",
                             (",".join(_clean), _now(), b["id"]))
        except Exception as exc:
            log.warning(f"⚠️  reminder send failed (id={b.get('id')}): {exc}")
    if rows:
        analytics.inc("scheduler.reminders_scanned")


def _scheduler_followups() -> None:
    """One-time cold-lead nudge for CONSENTED contacts that went quiet."""
    if not cfg.FOLLOWUP_ENABLED:
        return
    if not cfg.FOLLOWUP_TEMPLATE:
        # v16g4 FIX H2: without an approved template nothing here can be
        # delivered — skip the scan entirely (it used to run every tick,
        # publishing undeliverable rows). Warn at most once an hour so the
        # reason is visible without flooding the log.
        if brain_cache.setnx("warn:followup_no_template", ttl=3600):
            log.warning("⚠️  FOLLOWUP_ENABLED=1 but FOLLOWUP_TEMPLATE is unset "
                        "— cold-lead nudges are DISABLED (they cannot be "
                        "delivered outside the 24h window). Approve a template "
                        "in Meta Business Manager and set FOLLOWUP_TEMPLATE.")
        return
    now_utc    = datetime.now(timezone.utc)
    older_than = (now_utc - timedelta(hours=cfg.FOLLOWUP_AFTER_HOURS)).isoformat()
    too_old    = (now_utc - timedelta(hours=cfg.FOLLOWUP_MAX_AGE_HOURS)).isoformat()
    try:
        with _db_pool.get(read_only=True) as conn:
            # v14g5 FIX 16: only chase leads belonging to ACTIVE clinics (was also
            # messaging cold leads of soft-deleted clinics).
            # v16g5 FIX R5-H5: the ONLY time signal was contact CREATION, so a
            # patient who first messaged 25 hours ago and has been in
            # conversation since this morning still matched — and got
            # "just following up, anything I can help with?" mid-chat. Join
            # the session's last_active and require THAT to be stale too.
            # LEFT JOIN + COALESCE so a lead with no session row (an imported
            # contact) still qualifies on created_at alone, as before.
            cur = _execute(conn,
                "SELECT c.id, c.customer_id, c.enc_phone FROM crm_contacts c "
                "JOIN customer_brains b ON b.customer_id=c.customer_id "
                "WHERE (c.followed_up_at IS NULL OR c.followed_up_at='') "
                "AND c.created_at <= ? AND c.created_at >= ? AND c.is_consented=? "
                "AND b.is_active=? "
                # NOT EXISTS, not a LEFT JOIN + GROUP BY: with two sessions
                # (one stale, one live) a join would keep the stale row and
                # nudge an active patient anyway. This asks the right
                # question — "has this subject been active AT ALL recently?"
                "AND NOT EXISTS (SELECT 1 FROM chat_sessions s "
                "                WHERE s.customer_id = c.customer_id "
                "                  AND s.subject_hash = c.phone_hash "
                "                  AND s.last_active > ?) "
                "ORDER BY c.id "
                "LIMIT 200",
                (older_than, too_old, _db_true(), _db_true(), older_than))
            rows = [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        log.warning(f"⚠️  followup scan failed: {exc}")
        return
    for c in rows:
        try:
            phone = pii_vault.decrypt(c["enc_phone"])
            if phone and phone.startswith("ig_"):
                # v16g4 FIX H3: Instagram leads are stored as ig_<sender-id>
                # (crm_add_contact on the IG path). The follow-up scan is
                # channel-blind, so it handed that pseudo-number to the
                # WhatsApp sender — guaranteed Meta rejection, 5 retries,
                # dead-letter, per IG lead. Marked followed (this row is not
                # WhatsApp-deliverable and never will be) but VISIBLE, in the
                # same discipline as the B12 undecryptable branch. IG nudges
                # need their own sender — a separate feature, not a silent
                # failure mode.
                analytics.inc("scheduler.followup_skipped_ig")
                log.warning(f"⚠️  followup skipped — Instagram lead has no "
                            f"WhatsApp address (contact id={c.get('id')}, "
                            f"cust={c.get('customer_id')})")
            elif phone and phone != "[ENCRYPTED]" \
                    and not (_fo := is_opted_out_checked(c["customer_id"], phone))[1]:
                # v16g6 FIX R6-M16 (R6-H9's twin in the followup scanner):
                # the opt-out lookup FAILED — unknown is neither consent nor
                # suppression. The old code fell through to _mark_followed
                # and consumed the lead FOREVER on a DB blip. Hold it (no
                # mark); the next tick retries.
                analytics.inc("scheduler.followup_optout_unknown")
                log.warning(f"⚠️  followup held — opt-out state unknown "
                            f"(contact id={c.get('id')})")
                continue
            elif phone and phone != "[ENCRYPTED]" and _fo[0]:
                # v16g5 FIX R5-H4 · v16g6 R6-M16: a suppressed lead is still
                # marked below (nothing can opt back in today — the day that
                # flow exists it must clear followed_up_at) — but only a
                # KNOWN verdict may consume it.
                analytics.inc("scheduler.followup_skipped_optout")
            elif phone and phone != "[ENCRYPTED]":
                brain = get_customer_brain(c["customer_id"])
                bot   = (brain.get("bot_name") if brain else "") or "our team"
                # v16g4 FIX M8: use the language this lead actually wrote in.
                _lg = _user_lang(c["customer_id"], phone)
                if _publish_followup(c["customer_id"], phone,
                                     _t("followup", _lg, bot=bot)):
                    analytics.inc("scheduler.followup_sent")
                else:                                        # v16g2 FIX M8
                    log.warning(f"⚠️  followup publish failed — lead kept for "
                                f"rescan (contact id={c.get('id')})")
                    continue     # do NOT mark followed; next tick retries
            else:
                # v15g4 FIX B12: these leads were marked followed and vanished
                # with ZERO signal — a key-rotation mistake could silently kill
                # every nudge. Still marked (a decrypt failure is permanent for
                # this row), but now counted and visible.
                analytics.inc("scheduler.followup_skipped_decrypt")
                log.warning(f"⚠️  followup skipped — phone undecryptable "
                            f"(contact id={c.get('id')}, cust={c.get('customer_id')})")
            _mark_followed(c["id"])     # mark regardless, so we never rescan it
        except Exception as exc:
            log.warning(f"⚠️  followup failed (id={c.get('id')}): {exc}")


def _mark_followed(contact_id) -> None:
    try:
        with _db_pool.get() as conn:
            _execute(conn, "UPDATE crm_contacts SET followed_up_at=? WHERE id=?",
                     (_now(), contact_id))
    except Exception:
        pass


def _scheduler_retention_purge() -> None:
    """DPDP retention: drop chat logs + dead bookings older than DATA_RETENTION_DAYS
    (0 = keep forever). Lead/CRM data is NOT auto-purged — use the erasure endpoint
    for that, so a business never loses its book of contacts by surprise."""
    days = cfg.DATA_RETENTION_DAYS
    if days <= 0:
        return
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        with _db_pool.get() as conn:
            _execute(conn, "DELETE FROM chat_messages WHERE timestamp < ?", (cutoff,))
            _execute(conn, "DELETE FROM chat_sessions WHERE last_active < ?", (cutoff,))
            _execute(conn, "DELETE FROM bookings WHERE status IN ('cancelled','completed') "
                           "AND updated_at < ?", (cutoff,))
        analytics.inc("scheduler.retention_purged")
        log.info(f"🧹 Retention purge: removed chat/booking data older than {days}d.")
    except Exception as exc:
        log.warning(f"⚠️  retention purge failed: {exc}")
