"""HEONIX GEN-5 · module `heonix.crm`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 6647-7118).
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
from heonix.config import (cfg)
from heonix.db.core import (PostgreSQLPool, _column_exists, _db_true, _execute, audit)
from heonix.logsetup import (log)
from heonix.security.auth import (_ROLE_RANK)
from heonix.security.crypto import (_crm_phone_hash, _is_bsuid, _normalize_msisdn, pii_vault)
from heonix.utils import (_now)
from heonix import _latebind  # GEN-5 SPLIT
_db_pool: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.db.core at startup
_latebind.register('_db_pool', __name__)


def crm_add_contact(customer_id: str, name: str, phone: str,
                     email: str = "", notes: str = "",
                     stage: str = "lead", is_consented: bool = False,
                     wa_user_id: str = "") -> int:   # v16 U1
    now         = _now()
    phash       = _crm_phone_hash(customer_id, phone)
    is_pg       = isinstance(_db_pool, PostgreSQLPool)
    wa_user_id  = (wa_user_id or "").strip()

    # v11 #3: was a blind INSERT on EVERY message → 10 messages = 10 duplicate
    # rows. Now: same lead → just bump updated_at and return the existing id.
    with _db_pool.get() as conn:
        _has_uid_col = _column_exists(conn, "crm_contacts", "wa_user_id")
        cur = _execute(conn,
            ("SELECT id, updated_at, wa_user_id, enc_name FROM crm_contacts "
             if _has_uid_col else
             "SELECT id, updated_at, enc_name FROM crm_contacts ")
            + "WHERE customer_id=? AND phone_hash=?",
            (customer_id, phash))
        row = cur.fetchone()
        if row:
            # v16 U1: BACKFILL — existing patients (rows created before V16, or
            # matched by phone) get their BSUID attached the next time they
            # message, so the Meta Contact-Book mapping is mirrored locally.
            _uid_changed = bool(_has_uid_col and wa_user_id and (
                    (row["wa_user_id"] or "") != wa_user_id))
            # v16g4 port (audit item 221): a patient's WhatsApp/IG display name
            # can change (marriage, typo fix, new phone) but the CRM kept the
            # FIRST name forever. Refresh enc_name when the caller passed a
            # REAL captured name (not the "WA/IG <masked>" placeholder callers
            # use when no profile name is available) and it actually differs.
            _new_name = (name or "").strip()
            _is_placeholder = bool(re.match(r"^(WA|IG)\s", _new_name))
            _name_changed = False
            if _new_name and not _is_placeholder:
                try:
                    _cur_name = pii_vault.decrypt(row["enc_name"] or "")
                except Exception:
                    _cur_name = ""
                if _cur_name in ("", "[ENCRYPTED]") or _cur_name != _new_name:
                    _name_changed = True
            if _uid_changed or _name_changed:
                # v16g2 FIX L8 (BSUID self-heal) + name refresh, one UPDATE.
                sets, vals2 = ["updated_at=?"], [now]
                if _uid_changed:
                    sets.append("wa_user_id=?"); vals2.append(wa_user_id)
                if _name_changed:
                    sets.append("enc_name=?"); vals2.append(pii_vault.encrypt(_new_name))
                vals2.append(row["id"])
                _execute(conn,
                    f"UPDATE crm_contacts SET {', '.join(sets)} WHERE id=?",
                    tuple(vals2))
                if _uid_changed:
                    analytics.inc("crm.contact.bsuid_backfilled")
                if _name_changed:
                    analytics.inc("crm.contact.name_refreshed")
                return row["id"]
            # v15g4 FIX D3: the touch itself was a write on EVERY message —
            # needless SQLite write-lock pressure. Throttle to one bump per
            # 10 min per contact; any parse hiccup falls back to bumping.
            fresh = False
            try:
                ua = row["updated_at"]
                ua_dt = ua if isinstance(ua, datetime) else \
                        datetime.fromisoformat(str(ua).replace(" ", "T"))
                if ua_dt.tzinfo is None:
                    ua_dt = ua_dt.replace(tzinfo=timezone.utc)
                fresh = (datetime.now(timezone.utc) - ua_dt) < timedelta(seconds=600)
            except Exception:
                fresh = False
            if not fresh:
                _execute(conn,
                    "UPDATE crm_contacts SET updated_at=? WHERE id=?",
                    (now, row["id"]))
                analytics.inc("crm.contact.touched")
            return row["id"]

        enc_name    = pii_vault.encrypt(name)
        enc_phone   = pii_vault.encrypt(phone)
        enc_email   = pii_vault.encrypt(email) if email else ""
        enc_notes   = pii_vault.encrypt(notes) if notes else ""
        consent_val = is_consented if is_pg else int(is_consented)
        if _has_uid_col:                                   # v16 U1
            cols = ("INSERT INTO crm_contacts "
                    "(customer_id, phone_hash, enc_name, enc_phone, enc_email, enc_notes, "
                    "contact_stage, created_at, updated_at, is_consented, wa_user_id) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)")
            vals = (customer_id, phash, enc_name, enc_phone, enc_email, enc_notes,
                    stage, now, now, consent_val, wa_user_id)
        else:
            cols = ("INSERT INTO crm_contacts "
                    "(customer_id, phone_hash, enc_name, enc_phone, enc_email, enc_notes, "
                    "contact_stage, created_at, updated_at, is_consented) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)")
            vals = (customer_id, phash, enc_name, enc_phone, enc_email, enc_notes,
                    stage, now, now, consent_val)
        if is_pg:
            # v13 BUGFIX: psycopg2 cursor.lastrowid is 0 for normal tables, so the
            # API previously returned contact_id=0 for every new Postgres contact.
            # RETURNING id gives the real primary key.
            insert_sql = cols + " RETURNING id"
        else:
            insert_sql = cols
        _race_lost = False
        try:
            cur = _execute(conn, insert_sql, vals)
            if is_pg:
                picked = cur.fetchone()
                new_id = (picked["id"] if picked else None)
            else:
                new_id = cur.lastrowid if hasattr(cur, "lastrowid") else None
        except Exception:
            # v14g3 BUG 10: lost the insert race against the unique dedupe index
            # (uq_crm_dedupe — another worker just created this same lead).
            # v16g6 FIX R6-M4: the recovery lookup used to open a SECOND
            # pooled connection while STILL HOLDING the first — the only
            # nested _db_pool.get() in the file. Ten concurrent threads in
            # this branch deadlocked a pool_size=10 SQLite pool into
            # "SQLite pool exhausted" after the 5s timeout. Release the
            # insert connection first; recover on a fresh one below.
            new_id = None
            _race_lost = True

    if _race_lost:
        try:
            with _db_pool.get(read_only=True) as conn2:
                c2 = _execute(conn2,
                    "SELECT id FROM crm_contacts WHERE customer_id=? AND phone_hash=?",
                    (customer_id, phash))
                r2 = c2.fetchone()
                new_id = r2["id"] if r2 else None
        except Exception:
            new_id = None
        analytics.inc("crm.contact.race_merged")
        return new_id or 0

    analytics.inc("crm.contact.added")
    log.info(f"📋 CRM contact → customer={customer_id} phone={pii_vault.mask(phone)}")
    return new_id or 0


# ─────────────────────────────────────────────────────────────────────────────
# 🆔  v16 — USERNAMES / BSUID HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def crm_attach_phone(customer_id: str, chat_id: str, real_phone: str) -> bool:
    """v16 U3: a username patient (BSUID identity) shared their real number —
    store it in enc_phone on THEIR EXISTING row. Identity continuity is the
    whole point: phone_hash stays keyed on the BSUID (sessions, bookings, and
    dedupe all keep working), the real number rides alongside for reminders
    and clinic records."""
    # v16g2 FIX N2: canonicalise EXACTLY like the Tally intake does — a patient
    # typing "98765 43210" the natural way (nobody types +91) gets
    # DEFAULT_COUNTRY_CODE prepended, so the number the scheduler later hands
    # to Meta's `to` is actually deliverable instead of dead-lettering after
    # we PROMISED "reminders to ****3210". Floor raised 7→10: a 7-digit
    # landline was never a valid WhatsApp recipient.
    digits = _normalize_msisdn(real_phone or "")
    if len(digits) < 10:
        return False
    phash = _crm_phone_hash(customer_id, chat_id)
    try:
        with _db_pool.get() as conn:
            cur = _execute(conn,
                "UPDATE crm_contacts SET enc_phone=?, updated_at=? "
                "WHERE customer_id=? AND phone_hash=?",
                (pii_vault.encrypt(digits), _now(), customer_id, phash))
            ok = getattr(cur, "rowcount", 0) > 0
            # v16g3 FIX R3-M6: a patient who messaged from this NUMBER in the
            # pre-username era already has a phone-keyed row; capturing the
            # same number onto the BSUID row left TWO live rows for one
            # person (double follow-ups — the unique dedupe index can't fire
            # across different hashes). Merge, N3-style: carry consent over,
            # retire the old row, and re-key its bookings + sessions onto the
            # BSUID identity so history unifies.
            old_hash = _crm_phone_hash(customer_id, digits)
            if ok and old_hash != phash:
                cur = _execute(conn,
                    "SELECT id, is_consented, enc_notes, enc_email, "
                    "contact_stage, created_at FROM crm_contacts "
                    "WHERE customer_id=? AND phone_hash=?",
                    (customer_id, old_hash))
                _dup = cur.fetchone()
                if _dup:
                    # v16g6 FIX R6-M3: the merge kept ONLY is_consented — the
                    # retired row's notes, email, stage and original
                    # created_at were destroyed with it. Fold them into the
                    # survivor (fill-if-empty; notes concatenate; earliest
                    # created_at wins) BEFORE the delete, same transaction.
                    _sv = _execute(conn,
                        "SELECT id, enc_notes, enc_email, contact_stage, "
                        "created_at FROM crm_contacts "
                        "WHERE customer_id=? AND phone_hash=?",
                        (customer_id, phash)).fetchone()
                    if _sv:
                        def _dec(v):
                            _x = pii_vault.decrypt(v or "")
                            return "" if _x == "[ENCRYPTED]" else _x
                        _sets, _vals = [], []
                        _dn, _sn = _dec(_dup["enc_notes"]), _dec(_sv["enc_notes"])
                        if _dn and _dn not in _sn:
                            _sets.append("enc_notes=?")
                            _vals.append(pii_vault.encrypt(
                                (_sn + "\n" + _dn).strip() if _sn else _dn))
                        if _dec(_dup["enc_email"]) and not _dec(_sv["enc_email"]):
                            _sets.append("enc_email=?")
                            _vals.append(_dup["enc_email"])
                        if ((_dup["contact_stage"] or "") not in ("", "lead")
                                and (_sv["contact_stage"] or "lead") == "lead"):
                            _sets.append("contact_stage=?")
                            _vals.append(_dup["contact_stage"])
                        if ((_dup["created_at"] or "") and
                                str(_dup["created_at"]) < str(_sv["created_at"] or "9999")):
                            _sets.append("created_at=?")
                            _vals.append(_dup["created_at"])
                        if _sets:
                            _vals.append(_sv["id"])
                            _execute(conn,
                                f"UPDATE crm_contacts SET {', '.join(_sets)} "
                                f"WHERE id=?", tuple(_vals))
                    if _dup["is_consented"]:
                        _execute(conn,
                            "UPDATE crm_contacts SET is_consented=? "
                            "WHERE customer_id=? AND phone_hash=?",
                            (_db_true(), customer_id, phash))
                    _execute(conn, "DELETE FROM crm_contacts WHERE id=?",
                             (_dup["id"],))
                    # v16g6 FIX R6-M3: re-key EVERY booking — the old
                    # status='booked' filter orphaned cancelled/completed
                    # history from the surviving identity (and from erasure).
                    _execute(conn,
                        "UPDATE bookings SET phone_hash=? "
                        "WHERE customer_id=? AND phone_hash=?",
                        (phash, customer_id, old_hash))
                    _execute(conn,
                        "UPDATE chat_sessions SET subject_hash=? "
                        "WHERE customer_id=? AND subject_hash=?",
                        (phash, customer_id, old_hash))
                    analytics.inc("crm.identity_merged")
                    log.info(f"🆔 U3 capture: merged pre-username row for "
                             f"{pii_vault.mask(digits)} into the BSUID row.")
        if ok:
            brain_cache.delete(f"wa_session:{customer_id}:{digits}")  # old-spelling map
            brain_cache.set(f"realphone:{customer_id}:{chat_id}", digits,
                            ttl=86400 * 30)
            analytics.inc("crm.phone_captured")
            audit("system", "crm.phone_captured", customer_id,
                  {"chat_id_tail": chat_id[-8:], "phone": pii_vault.mask(digits)}, "")
        return ok
    except Exception as exc:
        log.warning(f"⚠️  crm_attach_phone failed: {exc}")
        return False


def crm_get_real_phone(customer_id: str, chat_id: str) -> str:
    """v16 U3: the captured real number for a BSUID conversation, '' if none.
    Cache-first (30d), DB fallback via the BSUID-keyed row's enc_phone."""
    cached = brain_cache.get(f"realphone:{customer_id}:{chat_id}")
    if cached:
        return str(cached)
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT enc_phone FROM crm_contacts "
                "WHERE customer_id=? AND phone_hash=? LIMIT 1",
                (customer_id, _crm_phone_hash(customer_id, chat_id)))
            row = cur.fetchone()
        if not row:
            return ""
        dec = pii_vault.decrypt(row["enc_phone"] or "")
        if dec and dec != "[ENCRYPTED]" and not _is_bsuid(dec) \
                and len(re.sub(r"\D", "", dec)) >= 7:
            brain_cache.set(f"realphone:{customer_id}:{chat_id}", dec, ttl=86400 * 30)
            return dec
    except Exception as exc:
        log.warning(f"⚠️  crm_get_real_phone failed: {exc}")
    return ""


def _resolve_send_addr(customer_id: str, addr: str) -> str:
    """v16 U3: outbound resolver for scheduler paths. If the stored recipient
    is a BSUID and the patient has since shared a real number, prefer the
    number (keeps working even if the BSUID lapses, and matches what the
    clinic has on record). Otherwise send to the BSUID — Meta's 'Send to
    BSUID' delivers to username patients directly. Plain phones pass through."""
    if not _is_bsuid(addr):
        return addr
    return crm_get_real_phone(customer_id, addr) or addr


def crm_remap_user_id(customer_id: str, old_id: str, new_id: str) -> int:
    """v16 U5: Meta regenerates a patient's BSUID when they change their phone
    number and announces it via a `user_id_update` system webhook. Without
    this remap the patient's next message arrives under an unknown identity —
    history, bookings, and captured phone all orphan. Re-key the CRM row, any
    upcoming bookings, AND the chat sessions from the old hash to the new one.
    v16g2 FIX N3: Meta guarantees NO cross-type ordering — if the patient's
    first post-change message beat the system event, crm_add_contact already
    created a stub row under the NEW hash, and the old UPDATE then hit
    uq_crm_dedupe and rolled the WHOLE remap back (identity split forever,
    bookings stranded). The stub is now merged (deleted) first.
    v16g2 FIX N4: for a classic user_changed_number (new id is a PHONE), the
    remap now also refreshes enc_phone — reminders stop dialling the dead
    SIM — and no longer writes a phone number into the BSUID column.
    v16g2 FIX M3: chat_sessions.subject_hash is re-keyed in the same
    transaction, and the old wa_session / numreq cache keys are dropped, so
    the patient's next message resumes the SAME session with full AI context —
    the header's "history never orphans" promise is finally true."""
    if not (old_id and new_id) or old_id == new_id:
        return 0
    old_hash = _crm_phone_hash(customer_id, old_id)
    new_hash = _crm_phone_hash(customer_id, new_id)
    changed  = 0
    try:
        with _db_pool.get() as conn:
            has_uid = _column_exists(conn, "crm_contacts", "wa_user_id")
            # v16g2 FIX N3: merge a pre-existing stub under the new identity so
            # the re-key below can never violate uq_crm_dedupe.
            cur = _execute(conn,
                "SELECT id FROM crm_contacts WHERE customer_id=? AND phone_hash=?",
                (customer_id, new_hash))
            _stub = cur.fetchone()
            if _stub:
                _execute(conn, "DELETE FROM crm_contacts WHERE id=?", (_stub["id"],))
                log.info(f"🆔 user_id_update: merged stub row id={_stub['id']} "
                         f"created under the new identity before the event.")
            if _is_bsuid(new_id):
                if has_uid:
                    cur = _execute(conn,
                        "UPDATE crm_contacts SET wa_user_id=?, phone_hash=?, updated_at=? "
                        "WHERE customer_id=? AND phone_hash=?",
                        (new_id, new_hash, _now(), customer_id, old_hash))
                else:
                    cur = _execute(conn,
                        "UPDATE crm_contacts SET phone_hash=?, updated_at=? "
                        "WHERE customer_id=? AND phone_hash=?",
                        (new_hash, _now(), customer_id, old_hash))
            else:
                # v16g2 FIX N4: classic number change — refresh the number the
                # scheduler will actually dial; leave wa_user_id untouched.
                _nd = _normalize_msisdn(new_id) or re.sub(r"\D", "", new_id)
                cur = _execute(conn,
                    "UPDATE crm_contacts SET phone_hash=?, enc_phone=?, updated_at=? "
                    "WHERE customer_id=? AND phone_hash=?",
                    (new_hash, pii_vault.encrypt(_nd), _now(),
                     customer_id, old_hash))
            changed += getattr(cur, "rowcount", 0) or 0
            cur = _execute(conn,
                "UPDATE bookings SET phone_hash=? "
                "WHERE customer_id=? AND phone_hash=? AND status='booked'",
                (new_hash, customer_id, old_hash))
            changed += getattr(cur, "rowcount", 0) or 0
            cur = _execute(conn,                              # v16g2 FIX M3
                "UPDATE chat_sessions SET subject_hash=? "
                "WHERE customer_id=? AND subject_hash=?",
                (new_hash, customer_id, old_hash))
            changed += getattr(cur, "rowcount", 0) or 0
        brain_cache.delete(f"realphone:{customer_id}:{old_id}")
        brain_cache.delete(f"wa_session:{customer_id}:{old_id}")   # v16g2 FIX M3
        for _k in ("numreq", "numreq_asked", "numreq_window", "numreq_inflight"):
            brain_cache.delete(f"{_k}:{customer_id}:{old_id}")     # v16g2 FIX M3
        audit("system", "crm.user_id_remap", customer_id,
              {"old_tail": old_id[-8:], "new_tail": new_id[-8:],
               "rows": changed}, "")
        analytics.inc("crm.user_id_remapped")
        log.info(f"🆔 user_id_update: remapped …{old_id[-8:]} → …{new_id[-8:]} "
                 f"({changed} rows) for {customer_id}")
    except Exception as exc:
        log.warning(f"⚠️  crm_remap_user_id failed: {exc}")
    return changed


_PHONE_LIKE_RE = re.compile(r"(?:\+?\d[\d\s\-().]{6,18}\d)")


def _extract_phone_like(text: str) -> str:
    """v16 U3: pull a typed phone number out of a chat message ('my number is
    98765 43210'). Returns normalised digits or ''. ≥10 digits required for a
    confident capture (Indian mobiles), ≤15 per E.164."""
    m = _PHONE_LIKE_RE.search(text or "")
    if not m:
        return ""
    digits = re.sub(r"\D", "", m.group(0))
    if not (10 <= len(digits) <= 15):
        return ""
    # v16g3 FIX R3-M2: inside the 15-min ask window a typed 12-digit AADHAAR
    # sailed through the length gate and became "their phone" — reminders
    # promised to a government ID. Plausibility: a bare 10-digit Indian mobile
    # starts 6-9; longer strings must start with the country code (and then a
    # 6-9 mobile digit) or be written in explicit +intl form, which we trust.
    if len(digits) == 10:
        return digits if digits[0] in "6789" else ""
    _cc = cfg.DEFAULT_COUNTRY_CODE
    if (digits.startswith(_cc) and len(digits) > len(_cc)
            and digits[len(_cc)] in "6789"):
        return digits
    if m.group(0).strip().startswith("+"):
        return digits
    return ""


def crm_list_contacts(customer_id: str, stage: Optional[str] = None,
                       page: int = 1, per_page: int = 50) -> Tuple[List[Dict], int]:
    offset       = (page - 1) * per_page
    stage_filter = "AND contact_stage=?" if stage else ""
    params_count = (customer_id,) + ((stage,) if stage else ())
    params_data  = params_count + (per_page, offset)

    with _db_pool.get(read_only=True) as conn:
        cur_total = _execute(conn,
            f"SELECT COUNT(*) as cnt FROM crm_contacts WHERE customer_id=? {stage_filter}",
            params_count)
        _trow = cur_total.fetchone()
        # v15 FIX 2 (CRITICAL): sqlite3.Row has NO .get() method — the old
        # `(fetchone() or {}).get("cnt", 0)` raised AttributeError on SQLite,
        # 500-ing GET /crm/contacts on the current deployment. Index access
        # works on both sqlite3.Row and psycopg2's RealDictRow.
        total = (_trow["cnt"] if _trow else 0) or 0
        cur_data = _execute(conn,
            f"SELECT id, enc_name, enc_phone, enc_email, enc_notes, "
            f"contact_stage, created_at, is_consented "
            f"FROM crm_contacts WHERE customer_id=? {stage_filter} "
            f"ORDER BY id DESC LIMIT ? OFFSET ?",
            params_data)
        rows = cur_data.fetchall()

    # v16g4 FIX L16: role-tiered PII. Only the phone was masked for viewers —
    # names, emails and free-text notes (which regularly hold health context:
    # "asked about root canal pricing") went out in clear to the lowest role.
    _u = getattr(g, "jwt_user", None) or {}
    _viewer_only = (_ROLE_RANK.get(_u.get("role", "viewer"), 0)
                    < _ROLE_RANK.get("admin", 1))
    def _p(v):   # viewer → masked
        return pii_vault.mask(v) if _viewer_only else v
    contacts = [{
        "id":            r["id"],
        "name":          _p(pii_vault.decrypt(r["enc_name"])),
        "phone":         pii_vault.mask(pii_vault.decrypt(r["enc_phone"])),
        "email":         _p(pii_vault.decrypt(r["enc_email"]) if r["enc_email"] else ""),
        "notes":         ("[restricted]" if (_viewer_only and r["enc_notes"]) else
                          (pii_vault.decrypt(r["enc_notes"]) if r["enc_notes"] else "")),
        "contact_stage": r["contact_stage"],
        "created_at":    str(r["created_at"]),
        "is_consented":  bool(r["is_consented"]),
    } for r in rows]
    return contacts, total


def crm_get_contact_full(contact_id: int, customer_id: str = "") -> Optional[Dict]:
    """v14g5 FIX 4 (IDOR): when customer_id is supplied the lookup is scoped to that
    tenant, so a clinic enumerating /crm/contact/<id> can never read another
    clinic's PII. An empty customer_id (superadmin) keeps the unscoped lookup."""
    with _db_pool.get(read_only=True) as conn:
        if customer_id:
            cur = _execute(conn,
                "SELECT * FROM crm_contacts WHERE id=? AND customer_id=?",
                (contact_id, customer_id))
        else:
            cur = _execute(conn, "SELECT * FROM crm_contacts WHERE id=?", (contact_id,))
        row = cur.fetchone()
    if not row:
        return None
    return {
        "id":            row["id"],
        "customer_id":   row["customer_id"],
        "name":          pii_vault.decrypt(row["enc_name"]),
        "phone":         pii_vault.decrypt(row["enc_phone"]),
        "email":         pii_vault.decrypt(row["enc_email"]) if row["enc_email"] else "",
        "notes":         pii_vault.decrypt(row["enc_notes"]) if row["enc_notes"] else "",
        "contact_stage": row["contact_stage"],
        "created_at":    str(row["created_at"]),
        "is_consented":  bool(row["is_consented"]),
    }
