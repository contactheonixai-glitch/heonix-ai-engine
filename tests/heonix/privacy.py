"""HEONIX GEN-5 · module `heonix.privacy`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 8199-8397).
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

from heonix.ai.rag import (rag_forget)
from heonix.analytics import (analytics)
from heonix.cache import (brain_cache)
from heonix.db.core import (_column_exists, _execute)
from heonix.logsetup import (log)
from heonix.security.crypto import (_crm_phone_hash, _normalize_msisdn, pii_vault)
from heonix import _latebind  # GEN-5 SPLIT
_db_pool: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.db.core at startup
_latebind.register('_db_pool', __name__)


def _find_subject_rows(customer_id: str, phone: str,
                       limit: int = 2000) -> List[Dict]:
    """v16g2 FIX M5/N9: resolve a data subject's CRM rows from whatever
    spelling the admin actually holds. U3's whole point is that the clinic
    ends up holding the patient's REAL number while the CRM row is keyed on
    the BSUID hash — a direct hash lookup then matches nothing. Strategy:
      1. direct phone_hash match on typed / digit / country-normalised
         spellings (fast path);
      2. bounded decrypt-compare of enc_phone across the tenant (last-10-digit
         match, ≥10 digits required) — this is what finds the BSUID-keyed row.
    Returns [{id, phone_hash, wa_user_id}] — wa_user_id is the chat-id alias
    the caller must also act under (erasure, consent)."""
    digits = re.sub(r"\D", "", phone or "")
    hashes = {_crm_phone_hash(customer_id, p)
              for p in dict.fromkeys(
                  [phone, digits, _normalize_msisdn(phone or "")]) if p}
    rows:  List[Dict] = []
    exact: List[Dict] = []      # v16g5 FIX R5-M4
    fuzzy: List[Dict] = []
    want_full = _normalize_msisdn(phone or "")
    try:
        with _db_pool.get(read_only=True) as conn:
            has_uid = _column_exists(conn, "crm_contacts", "wa_user_id")
            cur = _execute(conn,
                ("SELECT id, phone_hash, enc_phone, wa_user_id "
                 if has_uid else
                 "SELECT id, phone_hash, enc_phone ")
                + "FROM crm_contacts WHERE customer_id=? LIMIT ?",
                (customer_id, limit))
            for r in cur.fetchall():
                d = dict(r)
                d.setdefault("wa_user_id", "")
                if d["phone_hash"] in hashes:
                    rows.append(d)
                    continue
                if len(digits) >= 10:
                    dec = pii_vault.decrypt(d.get("enc_phone") or "")
                    if (dec and dec != "[ENCRYPTED]"
                            and re.sub(r"\D", "", dec)[-10:] == digits[-10:]):
                        # v16g5 FIX R5-M4: a last-10 match is a COLLISION, not
                        # an identity: +91 98765 43210 and +1 998765 43210
                        # share a tail. Tolerable for a read; this helper also
                        # backs erase_data_subject() (irreversible) and
                        # set_consent_api(). Separate EXACT country-aware
                        # matches from mere tail matches and prefer the exact
                        # set when one exists.
                        if (want_full
                                and _normalize_msisdn(dec) == want_full):
                            exact.append(d)
                        else:
                            fuzzy.append(d)
        # Exact wins outright. A tail-only match is trusted ONLY when it is
        # unambiguous (exactly one) — two candidates means we cannot tell the
        # subjects apart, and guessing would erase a stranger's records.
        if exact:
            rows.extend(exact)
        elif len(fuzzy) == 1:
            rows.extend(fuzzy)
        elif fuzzy:
            log.error(f"🛑 _find_subject_rows: {len(fuzzy)} contacts share the "
                      f"last 10 digits of {pii_vault.mask(phone)} under "
                      f"{customer_id} and none matched exactly — REFUSING to "
                      f"guess (v16g5 FIX R5-M4). Pass the full E.164 number.")
            analytics.inc("dpdp.ambiguous_subject")
    except Exception as exc:
        log.warning(f"⚠️  _find_subject_rows failed: {exc}")
    return rows


def erase_data_subject(customer_id: str, phone: str) -> Dict:
    """v14g4 (DPDP right-to-erasure): delete ALL data for ONE person (by phone)
    under ONE clinic — CRM contact, bookings, RAG memory, chat sessions +
    messages, and every Redis-state key. Returns a small report. Best-effort.
    v15g4 FIX B4: try both the typed and digit spellings.
    v16g2 FIX M5: the subject is ALSO resolved via _find_subject_rows
    (wa_user_id alias + bounded enc_phone decrypt-compare), so erasing a
    USERNAME patient by the real number the clinic actually holds reaches the
    BSUID-keyed CRM row, its bookings, its sessions and its RAG memory too.
    v16g2 FIX M4: the captured real phone (`realphone:` — PLAINTEXT digits,
    30-day TTL), the numreq ask-state, booking-flow state and ghost mutes are
    deleted for every candidate spelling — erasure means erasure, Redis
    included; crm_get_real_phone can no longer answer post-erasure."""
    digits = re.sub(r"\D", "", phone or "")
    cands  = [p for p in dict.fromkeys([phone, digits]) if p]   # unique, ordered
    # v16g2 FIX M5: fold in every alias the CRM can prove belongs to this subject.
    subject_rows = _find_subject_rows(customer_id, phone)
    for _r in subject_rows:
        if _r.get("wa_user_id"):
            cands.append(_r["wa_user_id"])
    cands  = [p for p in dict.fromkeys(cands) if p]
    hashes = list(dict.fromkeys(
        [_crm_phone_hash(customer_id, p) for p in cands]
        + [r["phone_hash"] for r in subject_rows if r.get("phone_hash")]))
    report = {"crm": 0, "bookings": 0, "sessions": 0, "messages": 0, "rag": False}
    # v16g4 FIX L12: flush cached AI replies — see delete_prefix docstring.
    try:
        report["resp_cache_flushed"] = brain_cache.delete_prefix("resp:")
    except Exception:
        pass
    # 1) CRM + bookings — under EVERY resolved hash (v16g2 FIX M5)
    try:
        with _db_pool.get() as conn:
            for h in hashes:
                cur = _execute(conn, "DELETE FROM crm_contacts WHERE customer_id=? AND phone_hash=?",
                               (customer_id, h))
                report["crm"] += getattr(cur, "rowcount", 0) or 0
                cur = _execute(conn, "DELETE FROM bookings WHERE customer_id=? AND phone_hash=?",
                               (customer_id, h))
                report["bookings"] += getattr(cur, "rowcount", 0) or 0
    except Exception as exc:
        log.warning(f"⚠️  erase (crm/bookings) failed: {exc}")
    # 2) Chat sessions + messages. v14g5 FIX 3: resolve sessions from the DB by
    # subject_hash — for EVERY resolved hash (v16g2 FIX M5) — plus any
    # cache-mapped session ids (pre-FIX rows whose subject_hash is empty).
    try:
        with _db_pool.get() as conn:
            sids: List[str] = []
            for h in hashes:
                cur = _execute(conn,
                    "SELECT session_id FROM chat_sessions WHERE customer_id=? AND subject_hash=?",
                    (customer_id, h))
                for r in cur.fetchall():
                    _sid = r["session_id"] if not isinstance(r, tuple) else r[0]
                    if _sid and _sid not in sids:
                        sids.append(_sid)
            for p in cands:                                     # v15g4 FIX B4
                for k in (f"wa_session:{customer_id}:{p}",
                          f"ig_session:{customer_id}:{p}"):
                    _sid = brain_cache.get(k)
                    if _sid and _sid not in sids:
                        sids.append(_sid)
                    brain_cache.delete(k)
            for sid in sids:
                cur = _execute(conn, "DELETE FROM chat_messages WHERE session_id=?", (sid,))
                report["messages"] += getattr(cur, "rowcount", 0) or 0
                cur = _execute(conn, "DELETE FROM chat_sessions WHERE session_id=?", (sid,))
                report["sessions"] += getattr(cur, "rowcount", 0) or 0
    except Exception as exc:
        log.warning(f"⚠️  erase (sessions) failed: {exc}")
    # 3) RAG memory — BOTH channel-shaped uids, under EVERY candidate spelling
    # (v15g4 FIX B4 + v16g2 FIX M5: BSUID aliases included).
    rag_ok = False
    for p in cands:
        rag_ok = rag_forget(customer_id, f"{customer_id}:{p}") or rag_ok
        rag_ok = rag_forget(customer_id, f"ig:{customer_id}:{p}") or rag_ok
    report["rag"] = rag_ok
    # 4) v16g2 FIX M4: Redis state — captured real phone, ask-state, booking
    # flow, ghost mutes — for every candidate spelling. Erasure means erasure.
    for p in cands:
        for k in (f"realphone:{customer_id}:{p}",
                  f"numreq:{customer_id}:{p}",
                  f"numreq_asked:{customer_id}:{p}",
                  f"numreq_window:{customer_id}:{p}",
                  f"numreq_inflight:{customer_id}:{p}",
                  f"bk_offer:{customer_id}:{p}",
                  # v16g6 FIX R6-M1: two keys added since this list was last
                  # touched. wawin is the flag that AUTHORISES free-text
                  # sends — erasure must revoke it with everything else.
                  f"bk_offer_recent:{customer_id}:{p}",
                  f"wawin:{customer_id}:{p}",
                  f"bk_cancel:{customer_id}:{p}",
                  f"ghost:{customer_id}:{p}",
                  f"ghost:ig:{customer_id}:{p}"):
            brain_cache.delete(k)
    # 5) v16g6 FIX R6-C3: the OUTBOX. Queued reminders/follow-ups for this
    # subject held their number in the payload and were still DELIVERED
    # AFTER erasure — the one table this function never touched. Cancel
    # every not-yet-sent row whose `to` matches any candidate spelling
    # (payloads written before this build are cleartext; new ones are
    # sealed — compare via decrypt so both generations match).
    try:
        _digs = {re.sub(r"\D", "", c)[-12:] for c in cands
                 if re.sub(r"\D", "", c)}
        with _db_pool.get() as conn:
            cur = _execute(conn,
                "SELECT id, payload FROM outbox "
                "WHERE status IN ('pending','processing','failed')")
            _kill = []
            for r in cur.fetchall():
                _pid = r["id"] if not isinstance(r, tuple) else r[0]
                _raw = r["payload"] if not isinstance(r, tuple) else r[1]
                try:
                    _p = _raw if isinstance(_raw, dict) else json.loads(_raw)
                except Exception:
                    continue
                if _p.get("customer_id") != customer_id:
                    continue
                _to = pii_vault.decrypt(str(_p.get("to", "")))
                if (_to in cands
                        or re.sub(r"\D", "", _to)[-12:] in _digs):
                    _kill.append(_pid)
            for _i in _kill:
                _execute(conn, "DELETE FROM outbox WHERE id=?", (_i,))
            report["outbox"] = len(_kill)
    except Exception as exc:
        log.warning(f"⚠️  erase (outbox) failed: {exc}")
    analytics.inc("dpdp.subject_erased")
    log.info(f"🗑️  DPDP erase → cust={customer_id} phone={pii_vault.mask(phone)} {report}")
    return report
