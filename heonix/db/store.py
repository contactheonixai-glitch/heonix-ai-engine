"""HEONIX GEN-5 · module `heonix.db.store`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 5783-5861, 5989-6600).
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

from heonix.ai.providers import (_gemini_model)
from heonix.analytics import (analytics)
from heonix.cache import (brain_cache)
from heonix.channels.whatsapp import (
    WhatsAppAuthError,
    _flag_channel_reauth,
    _meta_send_retry,
    _to_whatsapp_markdown,
    _wa_send_template,
    _wa_send_text,
)
from heonix.concurrency import (submit_bg)
from heonix.config import (cfg)
from heonix.db.core import (
    PostgreSQLPool,
    _column_exists,
    _db_true,
    _execute,
    _is_unique_violation,
)
from heonix.logsetup import (log)
from heonix.resilience import (_whatsapp_breaker)
from heonix.security.crypto import (_crm_phone_hash, pii_vault)
from heonix.utils import (_iso_in, _now)
from heonix import _latebind  # GEN-5 SPLIT
_db_pool: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.db.core at startup
_latebind.register('_db_pool', __name__)


# ─────────────────────────────────────────────────────────────────────────────
# 🔕  v16g5 FIX R5-H4 — DURABLE OPT-OUT SUPPRESSION
#   Before this, a "STOP" flipped is_consented on whatever crm_contacts rows
#   _find_subject_rows happened to match — and nothing else. It did NOT mute
#   the AI, it did NOT stop appointment reminders (the reminder scanner reads
#   `bookings` and never looks at consent at all), and when the subject had no
#   matching CRM row — the common case for a BSUID patient whose row is keyed
#   on a hash of the BSUID — it wrote NOTHING while still replying "you've
#   been unsubscribed". Under DPDP that is telling a person you stopped and
#   then continuing to message them.
#   The suppression is stored in its own table, keyed by the same subject hash
#   the rest of the engine uses, and is consulted by every outbound initiator.
# ─────────────────────────────────────────────────────────────────────────────
def opt_out_subject(customer_id: str, subject: str) -> bool:
    """Record a durable opt-out. Returns True only when the row landed."""
    try:
        with _db_pool.get() as conn:
            _execute(conn,
                "INSERT INTO opt_outs (customer_id, subject_hash, created_at) "
                "VALUES (?,?,?)",
                (customer_id, _crm_phone_hash(customer_id, subject), _now()))
        brain_cache.set(f"optout:{customer_id}:{subject}", "1", ttl=86400)
        return True
    except Exception as exc:
        if _is_unique_violation(exc):        # already opted out — still success
            brain_cache.set(f"optout:{customer_id}:{subject}", "1", ttl=86400)
            return True
        log.error(f"❌ opt-out NOT recorded (cust={customer_id}): {exc}")
        analytics.inc("optout.write_failed")
        return False


def is_opted_out_checked(customer_id: str, subject: str) -> Tuple[bool, bool]:
    """v16g6 FIX R6-H9: returns (suppressed, known). Failing CLOSED is right
    for the SEND decision and catastrophic for a CONSUME decision — a caller
    that marks one-shot work done on the strength of a DB blip loses that
    work forever. Callers that consume leads must see the difference between
    'this subject is suppressed' and 'I could not find out'."""
    if not subject:
        return False, True
    ck = f"optout:{customer_id}:{subject}"
    cached = brain_cache.get(ck)
    if cached is not None:
        return (bool(cached) and cached != "0"), True
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT 1 FROM opt_outs WHERE customer_id=? AND subject_hash=? LIMIT 1",
                (customer_id, _crm_phone_hash(customer_id, subject)))
            hit = cur.fetchone() is not None
        brain_cache.set(ck, "1" if hit else "0", ttl=3600)
        return hit, True
    except Exception as exc:
        log.warning(f"⚠️  opt-out lookup failed (cust={customer_id}): {exc}")
        return True, False               # fail closed, and SAY it's a guess


def is_opted_out(customer_id: str, subject: str) -> bool:
    """True = never initiate an outbound to this subject again. Fails CLOSED
    on a cache miss + DB error: silence is the safe direction for consent.
    v16g6 FIX R6-H9: now a thin wrapper — consuming callers use
    is_opted_out_checked to tell suppression from lookup failure."""
    return is_opted_out_checked(customer_id, subject)[0]


def _wa_touch_window(customer_id: str, subject: str) -> None:
    """v16g5 FIX R5-H1 support: remember that this subject messaged US, which
    is what opens WhatsApp's 24-hour customer-service window for free text."""
    try:
        brain_cache.set(f"wawin:{customer_id}:{subject}", "1", ttl=24 * 3600)
    except Exception:
        pass


def _wa_in_service_window(customer_id: str, subject: str) -> bool:
    try:
        return bool(brain_cache.get(f"wawin:{customer_id}:{subject}"))
    except Exception:
        return False


def outbox_publish(event_type: str, payload: Dict) -> bool:
    """
    Transactional outbox pattern: events are persisted BEFORE external side-effects.
    A background worker processes pending events, guaranteeing at-least-once delivery.
    v12 #18: also kicks an immediate background drain so the welcome message and
    owner alerts go out in ~1s instead of waiting up to a full janitor cycle.
    v16g2 FIX M8: returns True only when the INSERT landed — the schedulers used
    to mark reminders_sent / followed_up_at on the ASSUMPTION the publish worked,
    so one DB hiccup during a tick lost messages forever AND recorded them sent.
    """
    try:
        # v16g6 FIX R6-C3: the outbox was the ONE store keeping patient
        # numbers in cleartext (crm_contacts and bookings both AES-GCM their
        # PII). Seal `to` at rest; the drain unseals just-in-time. encrypt()
        # is a no-op when the vault is disabled, so dev behaviour is
        # unchanged and no schema migration is needed.
        if payload.get("to"):
            payload = dict(payload, to=pii_vault.encrypt(str(payload["to"])))
        payload_str = json.dumps(payload)
        with _db_pool.get() as conn:
            _execute(conn,
                "INSERT INTO outbox (event_type, payload, status, created_at) VALUES (?,?,?,?)",
                (event_type, payload_str, "pending", _now()))
        # v16g6 FIX R6-L7: EVERY publish kicked its own drain — a burst of N
        # publishes produced N overlapping claim sweeps fighting over the
        # same rows (row-atomic, so pure wasted DB churn). One kick per 1s
        # window; the drain claims in batches of 20 and the janitor tick is
        # the backstop for anything landing inside the window.
        if brain_cache.setnx("outbox:kick", ttl=1):
            submit_bg(_process_outbox)   # v12 #18: drain now, not next tick
        return True
    except Exception as exc:
        log.error(f"❌ Outbox publish failed: {exc}")
        return False


def _claim_outbox_batch(limit: int = 20) -> List[Tuple]:
    """v12 #2/#44: atomically claim a batch of pending events. On Postgres,
    SELECT ... FOR UPDATE SKIP LOCKED guarantees two gunicorn workers can never
    grab the same row — so the welcome/alert message is sent exactly once, not
    once per worker. Rows are flipped to 'processing' inside the same locking
    transaction; slow sends then happen OUTSIDE the lock."""
    is_pg   = isinstance(_db_pool, PostgreSQLPool)
    claimed: List[Tuple] = []
    with _db_pool.get() as conn:
        if is_pg:
            # v15g3 FIX 1: only claim rows whose backoff window has elapsed.
            # COALESCE guards NULL (rows inserted before the column's DEFAULT
            # applied on some PG versions); '' compares less-than any ISO
            # timestamp, so legacy rows stay immediately eligible.
            cur = _execute(conn,
                "SELECT id, event_type, payload, attempts FROM outbox "
                "WHERE status='pending' AND attempts < 5 "
                "AND COALESCE(next_attempt_at,'') <= ? "
                "ORDER BY id LIMIT ? FOR UPDATE SKIP LOCKED", (_now(), limit))
            rows = cur.fetchall()
            ids  = [r["id"] for r in rows]
            if ids:
                # v15 FIX 7: stamp the CLAIM time so the janitor's stuck-row
                # requeue measures from when work started, not row creation.
                _execute(conn,
                    "UPDATE outbox SET status='processing', processed_at=? "
                    "WHERE id = ANY(?)", (_now(), ids))
        else:
            cur = _execute(conn,
                "SELECT id, event_type, payload, attempts FROM outbox "
                "WHERE status='pending' AND attempts < 5 "
                "AND COALESCE(next_attempt_at,'') <= ? "        # v15g3 FIX 1
                "ORDER BY id LIMIT ?", (_now(), limit))
            candidates = cur.fetchall()
            # v15g4 FIX B1: the old SELECT-then-UPDATE was not a claim — the
            # 20s janitor tick and the publish-time drain could BOTH read the
            # same pending rows before either flipped them, and each would
            # send (duplicate welcome/reminder messages). The UPDATE below is
            # conditional on status still being 'pending'; SQLite serialises
            # writes, so exactly ONE caller sees rowcount==1 per row. Postgres
            # already had this guarantee via FOR UPDATE SKIP LOCKED.
            rows = []
            for r in candidates:
                u = _execute(conn, "UPDATE outbox SET status='processing', "
                                   "processed_at=? WHERE id=? AND status='pending'",
                             (_now(), r["id"]))                 # v15 FIX 7 / v15g4 FIX B1
                if getattr(u, "rowcount", 1) == 1:
                    rows.append(r)
        claimed = [(r["id"], r["event_type"], r["payload"], r["attempts"]) for r in rows]
    return claimed


def _process_outbox() -> None:
    """Process a claimed batch. Claiming is atomic (see _claim_outbox_batch); the
    actual sends reuse the breaker + transient-retry path."""
    try:
        batch = _claim_outbox_batch(20)
    except Exception as exc:
        log.warning(f"⚠️  Outbox claim error: {exc}")
        return

    for evt_id, event_type, payload_raw, attempts in batch:
        try:
            # v15g2 FIX C1 (CRITICAL): on Postgres the payload column is JSONB and
            # psycopg2 auto-decodes it to a Python dict (default since 2.5.4) —
            # json.loads(dict) raised TypeError, so EVERY outbox event (welcome
            # messages, reminders, follow-ups) failed 5× and dead-lettered the
            # moment the engine ran on Postgres. SQLite (TEXT column) hid this.
            payload = payload_raw if isinstance(payload_raw, dict) \
                      else json.loads(payload_raw)
            # v16g6 FIX R6-C3: unseal the recipient written by outbox_publish.
            # Rows from pre-GEN-6 builds are untagged cleartext and pass
            # through decrypt() unchanged (the R5-C4 tag contract).
            _to0 = payload.get("to")
            if isinstance(_to0, str) and _to0.startswith("v1:"):
                payload["to"] = pii_vault.decrypt(_to0)
            if event_type == "whatsapp.send":
                # v14g3 BUG 9: route outbox sends through THIS clinic's OWN creds
                # (was always the GLOBAL number, so a multi-tenant welcome went
                # out from the wrong line or failed when global creds were unset).
                # A dead per-clinic token now flags needs_reauth and stops being
                # retried; transient errors still bubble up for outbox retry.
                cust = payload.get("customer_id", "")
                pid = tok = ""
                if cust:
                    _b = get_customer_brain(cust)
                    if _b:
                        pid, tok = brain_wa_creds(_b)
                try:
                    res = _whatsapp_breaker.call(
                        _meta_send_retry, _wa_send_text,
                        payload["to"], _to_whatsapp_markdown(payload["message"]),
                        pid, tok)
                    # v16g2 FIX H4: mirror the template branch's guard — a
                    # not_configured return is a SILENT non-send; without this
                    # it fell straight through to status='done', recording a
                    # never-sent welcome/reminder as delivered forever.
                    if isinstance(res, dict) and res.get("error"):
                        raise RuntimeError(
                            f"permanent: send not sent: {res.get('error')}")
                except WhatsAppAuthError as _ae:
                    _flag_channel_reauth(cust, f"outbox code={_ae.code}")
                    # v15g2 FIX M1: the message was NOT delivered — falling through
                    # to status='done' recorded a dead-token send as delivered
                    # forever (invisible in failed-row queries, never resent after
                    # the token is re-attached). Surface it as a permanent failure.
                    raise RuntimeError(
                        f"permanent: auth_dead: wa token code={_ae.code}")
            elif event_type == "whatsapp.template":
                # v14g4: scheduled sends (reminders / follow-ups) use an approved
                # template so they deliver OUTSIDE the 24-hour window. Same per-
                # tenant creds + token-death self-heal as whatsapp.send.
                cust = payload.get("customer_id", "")
                pid = tok = ""
                if cust:
                    _b = get_customer_brain(cust)
                    if _b:
                        pid, tok = brain_wa_creds(_b)
                try:
                    res = _whatsapp_breaker.call(
                        _meta_send_retry, _wa_send_template,
                        payload["to"], payload["template"],
                        payload.get("lang", "en"), payload.get("body_param", ""),
                        pid, tok)
                    if isinstance(res, dict) and res.get("error"):
                        raise RuntimeError(
                            f"permanent: template not sent: {res.get('error')}")
                except WhatsAppAuthError as _ae:
                    _flag_channel_reauth(cust, f"outbox tmpl code={_ae.code}")
                    raise RuntimeError(                            # v15g2 FIX M1
                        f"permanent: auth_dead: wa token code={_ae.code}")
            # Add more event types here as the system grows.
            with _db_pool.get() as conn:
                _execute(conn,
                    "UPDATE outbox SET status='done', processed_at=? WHERE id=?",
                    (_now(), evt_id))
        except Exception as exc:
            # v14g5 FIX 44: separate PERMANENT failures (misconfiguration, unknown
            # template, undeliverable recipient) from transient ones. Retrying a
            # permanent error five times only delays the dead-letter and spams the
            # logs — mark it failed on the first hit.
            _emsg = str(exc).lower()
            # v15g2 FIX M6: while the WhatsApp breaker is OPEN every drain pass
            # fast-fails without a single real send attempt — burning attempts
            # meant a ~5-tick outage could dead-letter perfectly good messages.
            # Put the row back to 'pending' with attempts UNCHANGED and move on.
            if "circuitbreaker" in _emsg and "open" in _emsg:
                # v15g3 FIX 1: attempts stay UNCHANGED (M6 discipline), but give
                # the row one tick of spacing — during breaker-open a burst of
                # publishes fired submit_bg drains that claimed + unclaimed the
                # same rows in a hot loop, hammering the DB for nothing.
                with _db_pool.get() as conn:
                    _execute(conn,
                        "UPDATE outbox SET status='pending', next_attempt_at=? "
                        "WHERE id=?", (_iso_in(20), evt_id))
                log.info(f"⏸️  Outbox event {evt_id} deferred — WhatsApp breaker open "
                         f"(attempt budget preserved).")
                continue
            # v16g6 FIX R6-M5: failures WE originate are tagged explicitly at
            # the raise site ("permanent: …") — a transient Meta 5xx whose
            # body happened to contain "not sent:" was dead-lettered on
            # attempt 1 by pure substring luck. Meta-body markers stay ONLY
            # as a fallback for errors we don't originate. (Same driver-
            # signals-over-sniffing discipline M11 applied to unique
            # violations.)
            _permanent = _emsg.startswith("permanent:") or any(m in _emsg for m in (
                "not_configured", "not configured", "does not exist",
                "unknown template", "invalid template", "template not found",
                "recipient not", "132001", "131026"))
            new_status = "failed" if (_permanent or attempts >= 4) else "pending"
            # v15g3 FIX 1 (HIGH): the old path retried a transient failure on the
            # very NEXT janitor tick (20s default — and instantly on every
            # submit_bg drain), burning all 5 attempts in ~80s. A routine 3-5min
            # Meta hiccup dead-lettered real patient reminders. Now each failure
            # pushes the row out on an exponential schedule — 30s → 60s → 120s →
            # 240s (+0-5s jitter so a batch doesn't retry as one thundering
            # herd) — stretching the attempt budget across ~7.5 minutes.
            _backoff = min(600.0, 30.0 * (2 ** attempts)) + random.uniform(0, 5)
            with _db_pool.get() as conn:
                _execute(conn,
                    "UPDATE outbox SET attempts=attempts+1, status=?, "
                    "next_attempt_at=? WHERE id=?",
                    (new_status, _iso_in(_backoff), evt_id))
            (log.error if _permanent else log.warning)(
                f"⚠️  Outbox event {evt_id} ({event_type}) "
                f"{'PERMANENT — not retrying' if _permanent else 'failed'}: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 💾  DATABASE OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────
def save_customer_brain(customer_id: str, customer_name: str,
                         business_type: str, system_prompt: str,
                         whatsapp_phone: str = "", owner_phone: str = "",
                         instagram_id: str = "", bot_name: str = "") -> None:
    now   = _now()
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    # v16g2 FIX N5: ? placeholders (_execute translates). v16g4 FIX HF2: the
    # N5 note used to live INSIDE the SQL string as a `--` comment — and the
    # note's own "%s"/"%-guard" text was the literal '%' that blew up the
    # first real Postgres run of this INSERT (see FIX HF1). Commentary lives
    # in Python now; SQL strings carry SQL only.
    if is_pg:
        sql = """
            INSERT INTO customer_brains
                (customer_id, customer_name, business_type, system_prompt,
                 created_at, updated_at, whatsapp_phone, region,
                 owner_phone, instagram_id, bot_name)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT (customer_id) DO UPDATE SET
                customer_name  = EXCLUDED.customer_name,
                business_type  = EXCLUDED.business_type,
                system_prompt  = EXCLUDED.system_prompt,
                updated_at     = EXCLUDED.updated_at,
                is_active      = TRUE,
                whatsapp_phone = EXCLUDED.whatsapp_phone,
                owner_phone    = EXCLUDED.owner_phone,
                instagram_id   = EXCLUDED.instagram_id,
                bot_name       = EXCLUDED.bot_name
        """
    else:
        sql = """
            INSERT INTO customer_brains
                (customer_id, customer_name, business_type, system_prompt,
                 created_at, updated_at, whatsapp_phone, region,
                 owner_phone, instagram_id, bot_name)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(customer_id) DO UPDATE SET
                customer_name  = excluded.customer_name,
                business_type  = excluded.business_type,
                system_prompt  = excluded.system_prompt,
                updated_at     = excluded.updated_at,
                is_active      = 1,
                whatsapp_phone = excluded.whatsapp_phone,
                owner_phone    = excluded.owner_phone,
                instagram_id   = excluded.instagram_id,
                bot_name       = excluded.bot_name
        """
    # v16g6 FIX R6-M2: every PATIENT number is AES-GCM'd; the clinic owner's
    # personal mobile — the emergency-escalation target — sat plaintext in
    # Postgres AND in the Redis brain cache. Seal it at rest; callers get it
    # back through _brain_unseal in the fetchers. Legacy plaintext rows pass
    # through decrypt() unchanged (tag contract) — no migration required.
    with _db_pool.get() as conn:
        _execute(conn, sql, (customer_id, customer_name, business_type,
                             system_prompt, now, now, whatsapp_phone, cfg.REGION,
                             pii_vault.encrypt(owner_phone or ""),
                             instagram_id, bot_name))
    brain_cache.delete(f"brain:{customer_id}")    # v16g6 FIX R6-L6
    try:
        # v16g6 FIX R6-L15: a clinic that edits its prompt kept the OLD
        # per-prompt Gemini client cached until LRU aging evicted it — 64
        # full system prompts held strongly on a 512MB dyno. Brain updates
        # are rare; clearing the factory outright is cheap and exact.
        _gemini_model.cache_clear()
    except Exception:
        pass
    analytics.inc("customer.saved")
    log.info(f"💾 Brain saved → {customer_id}")


def _brain_unseal(b: Dict) -> Dict:
    """v16g6 FIX R6-M2: caller-facing COPY with owner_phone decrypted. The
    cache keeps the sealed form (Redis included); legacy plaintext passes
    through decrypt() unchanged; unreadable ciphertext degrades to '' (no
    alert target) rather than leaking garbage into a send."""
    if not b:
        return b
    out = dict(b)
    out["owner_phone"] = pii_vault.decrypt(out.get("owner_phone") or "")
    if out["owner_phone"] == "[ENCRYPTED]":
        out["owner_phone"] = ""
    return out


def get_customer_brain(customer_id: str) -> Optional[Dict]:
    cached = brain_cache.get(f"brain:{customer_id}")   # v16g6 FIX R6-L6:
    # every other key in the file is namespaced (wapid:, igid:, ghost:,
    # resp:, optout:, wawin:) — the bare id meant delete_prefix could never
    # target brains, and any same-string key would collide.
    if cached:
        analytics.inc("cache.hit")
        return _brain_unseal(cached)              # v16g6 FIX R6-M2
    analytics.inc("cache.miss")
    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn,
            "SELECT * FROM customer_brains WHERE customer_id=? AND is_active=?",
            (customer_id, True if isinstance(_db_pool, PostgreSQLPool) else 1))
        row = cur.fetchone()
    if row:
        data = dict(row)
        brain_cache.set(f"brain:{customer_id}", data)   # sealed form · R6-L6
        return _brain_unseal(data)                # v16g6 FIX R6-M2
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 🧭  v13 TRUE MULTI-TENANT ROUTING  — which clinic owns the business number?
# ─────────────────────────────────────────────────────────────────────────────
def get_brain_by_wa_phone_id(phone_number_id: str) -> Optional[Dict]:
    """v13: find the clinic that OWNS the WhatsApp business line that received a
    message. This is the correct routing key (Meta's value.metadata.phone_number_id),
    not the sender's number. Cached per phone_number_id; channel edits bust it."""
    if not phone_number_id:
        return None
    ckey   = f"wapid:{phone_number_id}"
    cached = brain_cache.get(ckey)
    if cached:
        return _brain_unseal(cached) if cached != "__none__" else None   # R6-M2
    try:
        with _db_pool.get(read_only=True) as conn:
            if not _column_exists(conn, "customer_brains", "wa_phone_number_id"):
                return None  # pre-v13 DB — caller falls back to single-tenant route
            cur = _execute(conn,
                "SELECT * FROM customer_brains "
                "WHERE wa_phone_number_id=? AND is_active=?",
                (phone_number_id, _db_true()))
            row = cur.fetchone()
        if row:
            data = dict(row)
            brain_cache.set(ckey, data, ttl=cfg.ROUTE_CACHE_TTL)
            return _brain_unseal(data)               # v16g6 FIX R6-M2
        brain_cache.set(ckey, "__none__", ttl=60)   # cache the miss briefly
    except Exception as exc:
        log.warning(f"⚠️  wa_phone_id route lookup failed: {exc}")
    return None


def get_brain_by_ig_id(ig_account_id: str) -> Optional[Dict]:
    """v13: route an Instagram DM to the clinic that owns the IG business account
    that received it (the webhook recipient.id). Cached, miss-cached briefly."""
    if not ig_account_id:
        return None
    ckey   = f"igid:{ig_account_id}"
    cached = brain_cache.get(ckey)
    if cached:
        return _brain_unseal(cached) if cached != "__none__" else None   # R6-M2
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT * FROM customer_brains "
                "WHERE instagram_id=? AND is_active=?",
                (ig_account_id, _db_true()))
            row = cur.fetchone()
        if row:
            data = dict(row)
            brain_cache.set(ckey, data, ttl=cfg.ROUTE_CACHE_TTL)
            return _brain_unseal(data)               # v16g6 FIX R6-M2
        brain_cache.set(ckey, "__none__", ttl=60)
    except Exception as exc:
        log.warning(f"⚠️  ig_id route lookup failed: {exc}")
    return None


def brain_wa_creds(brain: Dict) -> Tuple[str, str]:
    """v13: THIS clinic's own (phone_id, token). Falls back to the GLOBAL env
    creds so your FIRST clinic and any pre-v13 setup keep working with zero extra
    config. v16g6 FIX R6-C6: a clinic that OWNS a phone_id but has no usable
    token gets ('','') — send disabled, reauth flagged — never the global
    pair. The global fallback is reserved for brains with no
    wa_phone_number_id at all."""
    pid_own = (brain.get("wa_phone_number_id") or "").strip()
    enc = (brain.get("wa_token_enc") or "").strip()
    tok_own = (pii_vault.decrypt(enc) if enc else "")
    if tok_own == "[ENCRYPTED]":
        # v16g2 FIX M6: decrypt failure returned the truthy sentinel, so the
        # global fallback never fired — one ENCRYPTION_KEY typo dark-flagged
        # the ENTIRE fleet with 401s instead of falling back to global creds.
        tok_own = ""
    if pid_own and tok_own:
        return pid_own, tok_own
    # v16g4 FIX H7: creds fall back AS A PAIR. The old per-field fallback
    # could return (clinic's phone_id, GLOBAL token) — or the reverse — a
    # cross-WABA pair that Meta always 401/403s, which then false-flagged
    # needs_reauth on what was a CONFIG problem, not a dead token.
    if pid_own and not tok_own:
        # v16g6 FIX R6-C6: routing REACHED this brain via its own
        # wa_phone_number_id — the clinic provably owns the line the patient
        # wrote to. H7's global-pair fallback here replied from a DIFFERENT
        # WhatsApp business identity, so the answer never appears in the
        # thread the patient used (your number, or Clinic A's, answers
        # Clinic B's patient). The safe failure is NO send + a loud reauth
        # flag — never someone else's number.
        log.error(f"❌ clinic {brain.get('customer_id','?')} owns phone_id "
                  f"{pid_own} but has NO usable token — sends DISABLED for "
                  f"this clinic until the token is re-attached via "
                  f"/admin/customer/<id>/channel (v16g6 FIX R6-C6).")
        try:
            _flag_channel_reauth(brain.get("customer_id", ""),
                                 "wa token unreadable/missing")
        except Exception:
            pass
        return "", ""
    elif tok_own and not pid_own:
        log.warning(f"⚠️  clinic {brain.get('customer_id','?')} has a token "
                    f"but NO phone_id — falling back to the GLOBAL pair "
                    f"(v16g4 FIX H7).")
    return cfg.WHATSAPP_PHONE_ID, cfg.WHATSAPP_TOKEN


def brain_ig_creds(brain: Dict) -> Tuple[str, str]:
    """v13: THIS clinic's own (ig_account_id, ig_token), global env fallback."""
    igid = (brain.get("instagram_id") or "").strip() or cfg.INSTAGRAM_ID
    enc  = (brain.get("ig_token_enc") or "").strip()
    tok  = (pii_vault.decrypt(enc) if enc else "")
    if tok == "[ENCRYPTED]":
        tok = ""                                    # v16g2 FIX M6 (IG twin)
    tok  = tok or cfg.INSTAGRAM_TOKEN
    return igid, tok


def create_session(customer_id: str, channel: str = "api", subject_hash: str = "") -> str:
    session_id = f"sess_{uuid.uuid4().hex[:20]}"
    now = _now()
    with _db_pool.get() as conn:
        _execute(conn,
            "INSERT INTO chat_sessions (session_id, customer_id, created_at, last_active, channel, subject_hash) "
            "VALUES (?,?,?,?,?,?)",
            (session_id, customer_id, now, now, channel, subject_hash))
    analytics.inc("session.created")
    return session_id


def session_exists(session_id: str, customer_id: str) -> bool:
    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn,
            "SELECT 1 FROM chat_sessions WHERE session_id=? AND customer_id=?",
            (session_id, customer_id))
        return cur.fetchone() is not None


def _find_session_by_subject(customer_id: str, subject_hash: str) -> Optional[str]:
    """v15g2 FIX M3: resume the subject's most recent session from the DB when
    the 1-hour cache mapping has expired — an ACTIVE conversation no longer gets
    total amnesia at the 60-minute mark. Cheap: hits idx_sess_subject (FIX 3)."""
    if not subject_hash:
        return None
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT session_id FROM chat_sessions "
                "WHERE customer_id=? AND subject_hash=? "
                "ORDER BY last_active DESC LIMIT 1",
                (customer_id, subject_hash))
            r = cur.fetchone()
            return r["session_id"] if r else None
    except Exception:
        return None


def save_messages_batch(session_id: str, turns: List[Tuple[str, str, str, int]]) -> None:
    """Save (role, content, ai_provider, latency_ms) tuples in one transaction."""
    now   = _now()
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    sql = (
        "INSERT INTO chat_messages "
        "(session_id, role, content, timestamp, token_estimate, ai_provider, latency_ms) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)" if is_pg else
        "INSERT INTO chat_messages "
        "(session_id, role, content, timestamp, token_estimate, ai_provider, latency_ms) "
        "VALUES (?,?,?,?,?,?,?)"
    )
    # v16g4 FIX L20: len(split()) undercounts Indic scripts ~2× (Tamil words
    # are long, agglutinative, and sub-word tokenized) — any future context
    # budgeting on this column would over-stuff history for Tamil chats.
    # Heuristic: ~4 chars/token for ASCII, ~2 chars/token for non-ASCII.
    def _token_estimate(_c: str) -> int:
        _a = sum(1 for ch in _c if ord(ch) < 128)
        return max(len(_c.split()), (_a + 3) // 4 + (len(_c) - _a + 1) // 2)
    rows = [(session_id, role, content, now, _token_estimate(content), provider, latency)
            for role, content, provider, latency in turns]
    with _db_pool.get() as conn:
        if is_pg:
            # v16g6 FIX R6-M12: the inline cursor was never closed — one
            # leaked cursor per saved chat turn, the exact pattern R5-L4
            # hunted down in init_db; it survived because executemany
            # bypasses _execute, where the closing lives. R6-M13: the
            # hand-built %s SQL above bypasses the placeholder guard for the
            # same reason — it stays (executemany has no _execute path) but
            # is now confined to this one audited, commented site.
            _mcur = conn.cursor()
            try:
                _mcur.executemany(sql, rows)
            finally:
                _mcur.close()
        else:
            conn.executemany(sql, rows)
        # v16g2 FIX N5: one dialect-neutral UPDATE through _execute — the old
        # Postgres branch carried literal %s, tripping the v15g4-C4 %-guard
        # into a spurious 🛑 ERROR log on EVERY saved chat turn (the hottest
        # write path), drowning real errors the day the Postgres migration
        # lands.
        _execute(conn,
            "UPDATE chat_sessions SET last_active=?, message_count=message_count+? "
            "WHERE session_id=?",
            (now, len(turns), session_id))
    analytics.inc("message.saved", len(turns))


def get_session_history(session_id: str) -> List[Dict]:
    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn,
            "SELECT role, content FROM chat_messages "
            "WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, cfg.CHAT_HISTORY_LIMIT))
        rows = cur.fetchall()
    hist = [{"role": r["role"], "parts": [r["content"]]} for r in reversed(rows)]
    # v12 #21: the LIMIT window can slice off the first user turn and leave the
    # history starting with a 'model' turn. Gemini's start_chat REQUIRES the
    # history to begin with a user turn (and to alternate) or it raises. Drop any
    # leading model turns so the window always starts clean.
    while hist and hist[0]["role"] == "model":
        hist.pop(0)
    return hist


def log_webhook(source_ip: str, payload_hash: str, customer_id: Optional[str],
                status: str, channel: str = "tally", error: Optional[str] = None) -> None:
    with _db_pool.get() as conn:
        _execute(conn,
            "INSERT INTO webhook_log "
            "(source_ip, payload_hash, customer_id, channel, status, error_detail, processed_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (source_ip, payload_hash, customer_id, channel, status, error, _now()))


def increment_chat_count(customer_id: str) -> None:
    with _db_pool.get() as conn:
        # v16g2 FIX L15: updated_at is no longer bumped per message — it made
        # tenants_health's needs_reauth "since" show the last patient message
        # instead of when the token actually died.
        _execute(conn,
            "UPDATE customer_brains SET total_chats=total_chats+1 "
            "WHERE customer_id=?",
            (customer_id,))
    # v15 FIX 23: this used to brain_cache.delete(customer_id) on EVERY message,
    # forcing a fresh DB read of the brain per turn — the cache never lived
    # longer than one message. total_chats in cached stats may now lag up to
    # CACHE_TTL (≤10 min); the live COUNT(*) queries in /stats are unaffected.
    analytics.inc("chat.total")


def check_idempotency(key: str) -> Optional[Dict]:
    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn, "SELECT response_body FROM idempotency_keys WHERE key=?", (key,))
        row = cur.fetchone()
    if not row:
        return None
    try:
        return json.loads(row["response_body"])
    except Exception:
        # v16g3 FIX R3-L9: one corrupt stored body used to 500 the DUPLICATE
        # path of the Tally webhook. Unreadable body = cache miss.
        log.warning(f"⚠️  idempotency body unreadable for {key[:12]} — miss.")
        return None


def store_idempotency(key: str, response: Dict) -> bool:
    """v15g4 FIX C7: now returns True on a durable write (or the harmless
    duplicate-race). False means the idempotency record was NOT stored — a
    Tally retry arriving after the 120s claim lock expires would replay the
    whole flow (duplicate welcome message). The caller logs that loudly."""
    with _db_pool.get() as conn:
        try:
            _execute(conn,
                "INSERT INTO idempotency_keys (key, response_body, created_at) VALUES (?,?,?)",
                (key, json.dumps(response), _now()))
            return True
        except Exception as exc:
            # v14g5 FIX 33 + v15 FIX 15: a duplicate-key race is the expected,
            # harmless case → DEBUG. Everything else (serialization failure,
            # full disk) was invisible at the default INFO level — now WARNING.
            _is_dup = _is_unique_violation(exc)   # v16g4 FIX M11
            (log.debug if _is_dup else log.warning)(
                f"idempotency store skipped for {key}: {exc}")
            return _is_dup
