"""HEONIX GEN-5 · module `heonix.channels.whatsapp`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 3336-3367, 3411-3527, 3779-4165).
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
from heonix.concurrency import (submit_bg)
from heonix.config import (cfg)
from heonix.crm import (crm_get_real_phone)
from heonix.db.core import (_column_exists, _execute)
from heonix.i18n import (_t)
from heonix.logsetup import (log)
from heonix.resilience import (_whatsapp_breaker)
from heonix.security.crypto import (_is_bsuid, pii_vault)
from heonix.utils import (_now)
from heonix import _latebind  # GEN-5 SPLIT
_db_pool: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.db.core at startup
_latebind.register('_db_pool', __name__)


WHATSAPP_API_BASE = f"https://graph.facebook.com/{cfg.GRAPH_API_VERSION}"  # v10: v19 → env (v21.0)
# v15g3 FIX 2 (HIGH-PERF): a bare Session() keeps urllib3 defaults — pool_maxsize
# =10 and ZERO retries. The worker pool + outbox drain + scheduler easily exceed
# 10 concurrent sends; every connection past #10 was DISCARDED after use, so the
# next send paid a fresh TCP+TLS handshake to graph.facebook.com (~200-400ms from
# India). Under a burst this throttled the whole fleet's reply latency.
# Fix: mount an HTTPAdapter with a real pool, plus CONNECT-only retries.
# connect-retries are double-send safe — the request was never transmitted —
# while read/status retries stay at 0 so a slow Meta 200 can never be re-sent.
_wa_session = requests.Session()
_wa_session.mount("https://", HTTPAdapter(
    pool_connections=8,
    pool_maxsize=64,
    max_retries=Retry(total=None, connect=2, read=0, redirect=0, status=0,
                      backoff_factor=0.3),
))


# ── v13 TRUE MULTI-TENANT: token-death detection ─────────────────────────────
# When a CLINIC's own token expires/revokes, Meta returns 401/403 or one of these
# error codes. We surface it as a typed exception so the send layer can flag that
# specific clinic 'needs_reauth' and alert YOU — instead of silently logging while
# that clinic's bot goes dark and the owner calls angry days later.
class WhatsAppAuthError(Exception):
    def __init__(self, code, message=""):
        self.code = code
        super().__init__(f"WA auth error code={code}: {message}")


# Meta auth/permission codes: 190 expired, 102 session, 10 permission,
# 200 perm, 803 invalid object, 0/3 sometimes wrap OAuth failures.
_WA_AUTH_FAIL_CODES = {190, 102, 10, 200, 803, 463, 467}


def _split_wa_chunks(message: str, limit: int = 4096) -> List[str]:
    """v16g4 FIX M7: Meta's text body cap is 4,096 CHARS — 1,000 tokens of
    Tamil comfortably exceeds it, and message[:4096] truncated silently,
    mid-word. Split on whitespace (falling back to a hard cut only for a
    single unbroken 4k+ run) so long replies arrive complete as sequenced
    messages instead of ending mid-sentence."""
    message = message or ""
    if len(message) <= limit:
        return [message]
    chunks, rest = [], message
    while len(rest) > limit:
        cut = rest.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = rest.rfind(" ", 0, limit)
        if cut < limit // 2:          # one unbroken ≥4k run: hard cut
            cut = limit
        chunks.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    if rest:
        chunks.append(rest)
    return chunks


def _wa_send_text(to_phone: str, message: str,
                  phone_id: str = "", token: str = "") -> Dict:
    """v13: per-tenant aware. phone_id/token default to the GLOBAL env creds, so
    your FIRST clinic and every old call site keep working untouched. Multi-tenant
    callers pass the clinic's OWN number+token. On an auth failure (dead clinic
    token) this raises WhatsAppAuthError so the caller can self-heal.
    v16g4 FIX M7: messages >4,096 chars are chunk-sent in order; the LAST
    chunk's API response is returned so callers keep their existing shape."""
    phone_id = phone_id or cfg.WHATSAPP_PHONE_ID
    token    = token    or cfg.WHATSAPP_TOKEN
    if not token or not phone_id:
        return {"error": "not_configured"}
    url = f"{WHATSAPP_API_BASE}/{phone_id}/messages"
    last: Dict = {}
    # v16g5 FIX R5-M3: a 4xx/5xx on chunk 2 raised AFTER chunk 1 had already
    # been delivered; _meta_send_retry then restarted the whole loop and the
    # patient received the first 4,096 characters TWICE — and a long clinical
    # answer is exactly the message that chunks. Record per-chunk progress
    # under a short-lived content-derived key so a retry RESUMES. Best-effort:
    # a cache miss degrades to the old behaviour, never to a dropped message.
    _chunks = _split_wa_chunks(message)
    _ck = _done = None
    if len(_chunks) > 1:
        _ck = "wachunk:" + hashlib.sha256(
            f"{to_phone}|{phone_id}|{message}".encode("utf-8")).hexdigest()[:24]
        try:
            _done = int(brain_cache.get(_ck) or 0)
        except (TypeError, ValueError):
            _done = 0
        if _done >= len(_chunks):
            # v16g6 FIX R6-M7: a STALE completion marker (the final delete
            # below failed and was swallowed) made an identical repeat
            # message within the TTL skip EVERY chunk and return {} — a
            # silent non-send the caller records as delivered. A marker that
            # claims "all chunks done" can only be stale on a NEW call: this
            # call exists because the caller wants a send. Start fresh.
            _done = 0
        if _done:
            log.info(f"📤 resuming chunked send at part {_done + 1}/{len(_chunks)} "
                     f"(v16g5 FIX R5-M3)")
    for _idx, chunk in enumerate(_chunks):
        if _done and _idx < _done:
            continue
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type":    "individual",
            "to":                to_phone,
            "type":              "text",
            "text":              {"body": chunk},
        }
        resp = _wa_session.post(
            url,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            json=payload,
            timeout=(cfg.HTTP_CONNECT_TIMEOUT, 15),
        )
        if resp.status_code >= 400:
            # v10: Meta says EXACTLY what is wrong. error.code 190 = expired token.
            err  = {}
            try:
                if "json" in resp.headers.get("content-type", ""):
                    err = (resp.json() or {}).get("error", {}) or {}
            except Exception:
                err = {}
            code = err.get("code")
            log.error(f"❌ WhatsApp send {resp.status_code} code={code} → {resp.text[:500]}")
            if resp.status_code in (401, 403) or code in _WA_AUTH_FAIL_CODES:
                raise WhatsAppAuthError(code, err.get("message", "auth failed"))
        resp.raise_for_status()
        if _ck:                                          # v16g5 FIX R5-M3
            try:
                # v16g6 FIX R6-L10: progress is recorded BEFORE parsing the
                # body — a Meta 200 with a non-JSON body used to raise first,
                # so the retry re-sent this chunk: the exact duplicate R5-M3
                # exists to prevent. Delivered is delivered.
                brain_cache.set(_ck, _idx + 1, ttl=600)
            except Exception:
                pass
        try:
            last = resp.json()
        except Exception:
            last = {"note": "non-json 2xx body"}         # v16g6 FIX R6-L10
    if _ck:
        try:
            brain_cache.delete(_ck)
        except Exception:
            try:
                # v16g6 FIX R6-M7: second, independent chance to clear the
                # marker; the resume guard above self-heals the rest.
                brain_cache.set(_ck, 0, ttl=1)
            except Exception:
                pass
    return last


_MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
# v16g2 FIX C5: require whitespace after the hashes (CommonMark headings do) —
# "#1 clinic in Coimbatore" no longer loses its "#".
_MD_HEAD_RE = re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE)
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")


def _to_whatsapp_markdown(text: str) -> str:
    if not text:
        return text
    text = _MD_LINK_RE.sub(r"\1 (\2)", text)   # [label](url) → label (url)
    text = _MD_BOLD_RE.sub(r"*\1*", text)        # **bold** → *bold*
    text = _MD_HEAD_RE.sub("", text)             # drop leading # heading markers
    return text


def _is_retryable_meta_error(exc: Exception) -> bool:
    """v12 #36: retry ONLY transient failures. A 4xx like 190 (expired token) or
    131047 (outside 24h window) is permanent — retrying it just burns calls."""
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True
    resp = getattr(exc, "response", None)
    code = getattr(resp, "status_code", None)
    return code in (429, 500, 502, 503, 504)


def _meta_send_retry(fn: Callable, *args):
    """Bounded retry wrapper for Meta sends. Sits INSIDE the circuit breaker, so
    the breaker only sees a failure after transient retries are exhausted."""
    last = None
    for attempt in range(cfg.META_SEND_RETRIES + 1):
        try:
            return fn(*args)
        except Exception as exc:
            last = exc
            if attempt >= cfg.META_SEND_RETRIES or not _is_retryable_meta_error(exc):
                raise
            time.sleep(min((2 ** attempt) * 0.5 + random.uniform(0, 0.3), 4.0))
    if last:
        raise last


def _flag_channel_reauth(customer_id: str, detail: str) -> None:
    """v13: a clinic's token is dead → mark that clinic 'needs_reauth' and ping
    ADMIN_ALERT_PHONE (over the GLOBAL line) so YOU re-attach it before the clinic
    notices. customer_id='' (a global-creds send) is a no-op — we never flag the
    whole fleet, and the admin-alert send below passes customer_id='' so it can
    never recurse into flagging itself."""
    if not customer_id:
        return
    try:
        _pid = _igid = ""          # v16g3 FIX R3-L1: dead is_pg removed
        with _db_pool.get() as conn:
            # column may not exist on a very old DB that skipped _migrate_v12 — guard
            if _column_exists(conn, "customer_brains", "channel_status"):
                _execute(conn,
                    "UPDATE customer_brains SET channel_status=?, updated_at=? "
                    "WHERE customer_id=?",
                    ("needs_reauth", _now(), customer_id))
            # v14g5 FIX 8: read the routing keys so we can bust their caches below.
            try:
                if _column_exists(conn, "customer_brains", "wa_phone_number_id"):
                    cur = _execute(conn, "SELECT wa_phone_number_id, instagram_id "
                                         "FROM customer_brains WHERE customer_id=?", (customer_id,))
                    _r = cur.fetchone()
                    if _r:
                        # v16g4 FIX L14: the old isinstance-tuple guard silently
                        # SKIPPED the routing-cache bust for tuple rows — a
                        # guard that hid the case instead of handling it. Tuple
                        # rows are positional in SELECT order.
                        if isinstance(_r, tuple):
                            _pid  = (_r[0] or "") if len(_r) > 0 else ""
                            _igid = (_r[1] or "") if len(_r) > 1 else ""
                        else:
                            _pid  = _r["wa_phone_number_id"] or ""
                            _igid = _r["instagram_id"] or ""
            except Exception:
                pass
        # v14g5 FIX 8: bust the ROUTING caches too, not just the brain cache, so the
        # send path stops using the stale brain (with the dead token) immediately.
        brain_cache.delete(f"brain:{customer_id}")     # v16g6 FIX R6-L6
        if _pid:
            brain_cache.delete(f"wapid:{_pid}")
            brain_cache.delete(f"wa_route:{_pid}")
        if _igid:
            brain_cache.delete(f"igid:{_igid}")
        brain_cache.delete("wa_route:__single__")
        analytics.inc("channel.reauth_flagged")
        log.error(f"🔑 Clinic {customer_id} token DEAD → needs_reauth ({detail})")
        if cfg.ADMIN_ALERT_PHONE and cfg.WHATSAPP_PHONE_ID and cfg.WHATSAPP_TOKEN:
            send_whatsapp_async(
                cfg.ADMIN_ALERT_PHONE,
                f"⚠️ HEONIX: clinic {customer_id} WhatsApp token failed ({detail}). "
                f"Re-attach via POST /admin/customer/{customer_id}/channel",
                phone_id=cfg.WHATSAPP_PHONE_ID, token=cfg.WHATSAPP_TOKEN,
                customer_id="")   # ← '' so this alert never re-flags anything
    except Exception as exc:
        log.error(f"❌ reauth flag failed for {customer_id}: {exc}")


def _wa_send_now(to_phone: str, message: str, phone_id: str = "",
                 token: str = "", customer_id: str = "") -> bool:
    """v14: the actual WhatsApp send body, shared by the async and sync wrappers.
    Runs the breaker + transient-retry path and self-heals on token death. Never
    raises into the caller (so a failed send can't break a serialized drain).
    v16g2 FIX L1: returns True only when Meta accepted the message — the docstring
    of the phone-request path promised a bool that never existed, so the M14 fix
    (set the 7-day ask-guard only on delivery) finally has a signal to trust."""
    msg = _to_whatsapp_markdown(message)        # v12 #24
    try:
        res = _whatsapp_breaker.call(_meta_send_retry, _wa_send_text,
                                     to_phone, msg, phone_id, token)  # v12 #36 / v13
        if isinstance(res, dict) and res.get("error"):        # v16g2 FIX L1
            log.warning(f"⚠️  WhatsApp send skipped ({res.get('error')}) → "
                        f"{pii_vault.mask(to_phone)}")
            return False
        analytics.inc("whatsapp.sent")
        return True
    except WhatsAppAuthError as exc:            # v13: token death → self-heal
        analytics.inc("whatsapp.auth_fail")
        _flag_channel_reauth(customer_id, f"code={exc.code}")
        return False
    except Exception as exc:
        analytics.inc("whatsapp.error")
        log.error(f"❌ WhatsApp send failed → {pii_vault.mask(to_phone)}: {exc}")
        return False


def _wa_send_interactive(to_phone: str, payload_interactive: Dict,
                         phone_id: str = "", token: str = "") -> Dict:
    """v14g4: send a WhatsApp INTERACTIVE message (reply-buttons or a list).
    Same per-tenant creds + auth-death semantics as _wa_send_text. Buttons/lists
    let a patient TAP a slot instead of typing — far fewer mis-bookings."""
    phone_id = phone_id or cfg.WHATSAPP_PHONE_ID
    token    = token    or cfg.WHATSAPP_TOKEN
    if not token or not phone_id:
        return {"error": "not_configured"}
    url  = f"{WHATSAPP_API_BASE}/{phone_id}/messages"
    body = {"messaging_product": "whatsapp", "recipient_type": "individual",
            "to": to_phone, "type": "interactive", "interactive": payload_interactive}
    resp = _wa_session.post(
        url, headers={"Authorization": f"Bearer {token}",
                      "Content-Type": "application/json"},
        json=body, timeout=(cfg.HTTP_CONNECT_TIMEOUT, 15))
    if resp.status_code >= 400:
        err  = {}
        try:
            if "json" in resp.headers.get("content-type", ""):
                err = (resp.json() or {}).get("error", {}) or {}
        except Exception:
            err = {}
        code = err.get("code")
        log.error(f"❌ WA interactive {resp.status_code} code={code} → {resp.text[:400]}")
        if resp.status_code in (401, 403) or code in _WA_AUTH_FAIL_CODES:
            raise WhatsAppAuthError(code, err.get("message", "auth failed"))
    resp.raise_for_status()
    return resp.json()


def wa_send_list_now(to_phone: str, body_text: str, button_label: str,
                     rows: List[Dict], phone_id: str = "", token: str = "",
                     customer_id: str = "", header: str = "") -> bool:
    """v14g4: send a single-section list message. `rows` = [{id,title,description?}]
    (max 10 per WhatsApp). Returns True on success. Never raises (self-heals on
    token death) so it is safe inside a serialized drain. Falls back to plain text
    by returning False so the caller can degrade gracefully."""
    section = {"title": button_label[:24] or "Options",
               "rows": [{"id": str(r["id"])[:200],
                         "title": str(r["title"])[:24],
                         "description": str(r.get("description", ""))[:72]}
                        for r in rows[:10]]}
    inter = {"type": "list",
             "body": {"text": body_text[:1024]},
             "action": {"button": (button_label[:20] or "Choose"),
                        "sections": [section]}}
    if header:
        inter["header"] = {"type": "text", "text": header[:60]}
    try:
        _whatsapp_breaker.call(_meta_send_retry, _wa_send_interactive,
                               to_phone, inter, phone_id, token)
        analytics.inc("whatsapp.list_sent")
        return True
    except WhatsAppAuthError as exc:
        analytics.inc("whatsapp.auth_fail")
        _flag_channel_reauth(customer_id, f"code={exc.code}")
    except Exception as exc:
        analytics.inc("whatsapp.interactive_error")
        log.warning(f"⚠️  list send failed → {pii_vault.mask(to_phone)}: {exc}")
    return False


def wa_send_buttons_now(to_phone: str, body_text: str, buttons: List[Dict],
                        phone_id: str = "", token: str = "",
                        customer_id: str = "") -> bool:
    """v14g4: send up to 3 reply buttons. `buttons` = [{id,title}]. Returns True
    on success, never raises. Used for yes/no confirmations (cancel, reschedule)."""
    inter = {"type": "button",
             "body": {"text": body_text[:1024]},
             "action": {"buttons": [
                 {"type": "reply",
                  "reply": {"id": str(b["id"])[:256], "title": str(b["title"])[:20]}}
                 for b in buttons[:3]]}}
    try:
        _whatsapp_breaker.call(_meta_send_retry, _wa_send_interactive,
                               to_phone, inter, phone_id, token)
        analytics.inc("whatsapp.buttons_sent")
        return True
    except WhatsAppAuthError as exc:
        analytics.inc("whatsapp.auth_fail")
        _flag_channel_reauth(customer_id, f"code={exc.code}")
    except Exception as exc:
        analytics.inc("whatsapp.interactive_error")
        log.warning(f"⚠️  buttons send failed → {pii_vault.mask(to_phone)}: {exc}")
    return False


_PHONE_REQUEST_BODY = ("To send you appointment reminders, could you share "
                       "your mobile number? Tap below — or just type it. "
                       "It's optional and stays with the clinic only. 🙏")


def _wa_send_phone_request(to_id: str, phone_id: str = "", token: str = "",
                           customer_id: str = "", lang: str = "en") -> bool:
    """v16 U3: send Meta's phone-number-request CTA to a username patient.
    Per BSP docs, tapping it delivers a `contacts` webhook carrying the shared
    number (handled in _process_wa_message). If the interactive type string is
    rejected (not yet GA in this region / naming differs — see cfg notes), we
    fall back to a plain-text ask; the typed-number capture path covers the
    reply either way. Never raises."""
    inter = {"type": cfg.WA_PHONE_REQUEST_TYPE,
             "body": {"text": _t("phone_request", lang)[:1024]},   # v16g4 FIX M8
             "action": {"name": cfg.WA_PHONE_REQUEST_ACTION}}
    try:
        _whatsapp_breaker.call(_meta_send_retry, _wa_send_interactive,
                               to_id, inter, phone_id, token)
        analytics.inc("whatsapp.phone_request_sent")
        return True
    except WhatsAppAuthError as exc:
        analytics.inc("whatsapp.auth_fail")
        _flag_channel_reauth(customer_id, f"code={exc.code}")
        return False
    except Exception as exc:
        log.info(f"ℹ️  phone-request interactive rejected "
                 f"({str(exc)[:120]}) — falling back to text ask.")
        analytics.inc("whatsapp.phone_request_fallback")
        return send_whatsapp_sync(to_id, _t("phone_request", lang),   # v16g4 FIX M8
                                  phone_id, token, customer_id)


def _maybe_request_phone(customer_id: str, chat_id: str,
                         phone_id: str = "", token: str = "",
                         lang: str = "en") -> None:
    """v16 U3: ask a BSUID-only patient for their number ONCE per 7 days —
    right after a booking succeeds, which is the moment the number actually
    matters (reminders).
    v16g2 FIX H3: ONE key used to be both the 7-day nag guard AND the capture
    window — for a full week, any digits the patient typed (an Aadhaar, an
    order id, a lab's number they were asking about) became "their phone" and
    swallowed the actual question. Split: `numreq_asked` (7d) only guards
    re-asking; `numreq_window` (15 min) is the ONLY thing typed-capture
    listens to.
    v16g2 FIX M14: the once-per-7-days guard is no longer burned before the
    ask is even delivered — a short `numreq_inflight` claim serialises
    concurrent turns, and the 7-day key is set ONLY after
    _wa_send_phone_request reports success (a real bool since FIX L1)."""
    if not cfg.ENABLE_PHONE_CAPTURE or not _is_bsuid(chat_id):
        return
    if crm_get_real_phone(customer_id, chat_id):
        return
    if brain_cache.get(f"numreq_asked:{customer_id}:{chat_id}"):
        return    # already asked recently (7-day nag guard)
    if not brain_cache.setnx(f"numreq_inflight:{customer_id}:{chat_id}", ttl=120):
        return    # an ask is already in flight (v16g2 FIX M14)

    def _ask():
        try:
            ok = _wa_send_phone_request(chat_id, phone_id, token, customer_id,
                                        lang=lang)   # v16g4 FIX M8
            if ok:                                            # v16g2 FIX M14
                brain_cache.set(f"numreq_asked:{customer_id}:{chat_id}", 1,
                                ttl=86400 * 7)
                brain_cache.set(f"numreq_window:{customer_id}:{chat_id}", 1,
                                ttl=900)                       # v16g2 FIX H3
        finally:
            brain_cache.delete(f"numreq_inflight:{customer_id}:{chat_id}")

    submit_bg(_ask)


def send_whatsapp_async(to_phone: str, message: str,
                        phone_id: str = "", token: str = "",
                        customer_id: str = "") -> None:
    """v13: per-tenant aware + self-healing. phone_id/token default to global env
    (backward compatible — old 2-arg calls still work). On a dead clinic token,
    flags that clinic needs_reauth and alerts you instead of failing silently."""
    submit_bg(_wa_send_now, to_phone, message, phone_id, token, customer_id)


def send_whatsapp_sync(to_phone: str, message: str, phone_id: str = "",
                       token: str = "", customer_id: str = "") -> bool:
    """v14 Bug 43: blocking patient reply, used ONLY inside the per-conversation
    serialized runner. Because processing for one patient is already one-at-a-time,
    sending in-thread guarantees reply N is on the wire before reply N+1 is even
    generated — so the patient never sees answers arrive out of order.
    v16g2 FIX L1: now returns the real send outcome."""
    return _wa_send_now(to_phone, message, phone_id, token, customer_id)


def _wa_send_template(to_phone: str, template: str, lang: str,
                      body_param: str, phone_id: str = "", token: str = "") -> Dict:
    """v11 #4: template messages work OUTSIDE the 24-hour window — the only
    reliable channel for owner alerts. Template must be pre-approved in the
    Meta console with one {{1}} body parameter.
    v13: per-tenant creds with global fallback + token-death detection."""
    phone_id = phone_id or cfg.WHATSAPP_PHONE_ID
    token    = token    or cfg.WHATSAPP_TOKEN
    if not token or not phone_id:
        return {"error": "not_configured"}
    # Meta rejects params containing newlines/tabs/4+ consecutive spaces.
    clean = re.sub(r"\s+", " ", body_param).strip()[:900]
    url = f"{WHATSAPP_API_BASE}/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {
            "name": template,
            "language": {"code": lang},
            "components": [{"type": "body",
                            "parameters": [{"type": "text", "text": clean}]}],
        },
    }
    resp = _wa_session.post(
        url,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json=payload, timeout=(cfg.HTTP_CONNECT_TIMEOUT, 15))
    if resp.status_code >= 400:
        err = {}
        try:
            if "json" in resp.headers.get("content-type", ""):
                err = (resp.json() or {}).get("error", {}) or {}
        except Exception:
            err = {}
        code = err.get("code")
        log.error(f"❌ WA template send {resp.status_code} code={code} → {resp.text[:500]}")
        if resp.status_code in (401, 403) or code in _WA_AUTH_FAIL_CODES:
            raise WhatsAppAuthError(code, err.get("message", "auth failed"))
    resp.raise_for_status()
    return resp.json()


def send_owner_alert_async(owner_phone: str, message: str,
                           phone_id: str = "", token: str = "",
                           customer_id: str = "") -> None:
    """v11 #4: ALL owner alerts (emergency / handoff / VIP / escalation) route
    here. With OWNER_ALERT_TEMPLATE set → template (works any time). Without it
    → free-form text, and if Meta rejects with 131047 (outside 24h window) we
    log exactly what to fix instead of failing silently.
    v13: alerts go from the CLINIC'S OWN number (per-tenant creds) so the owner
    recognises the sender; dead token → flag needs_reauth + alert you."""
    def _send():
        try:
            # v16g2 FIX L9: owner alerts were the ONE send class without the
            # transient-retry wrapper — a single 502 dropped an emergency alert
            # that every other path would have retried.
            if cfg.OWNER_ALERT_TEMPLATE:
                _whatsapp_breaker.call(_meta_send_retry, _wa_send_template,
                                       owner_phone, cfg.OWNER_ALERT_TEMPLATE,
                                       cfg.OWNER_ALERT_TEMPLATE_LANG, message,
                                       phone_id, token)
            else:
                _whatsapp_breaker.call(_meta_send_retry, _wa_send_text,
                                       owner_phone, message, phone_id, token)
            analytics.inc("owner_alert.sent")
        except WhatsAppAuthError as exc:        # v13: clinic token dead
            analytics.inc("owner_alert.auth_fail")
            _flag_channel_reauth(customer_id, f"owner-alert code={exc.code}")
        except Exception as exc:
            analytics.inc("owner_alert.error")
            extra = ""
            if "131047" in str(exc):
                extra = (" ← Meta 24h-window block. Fix: approve a template "
                         "with one {{1}} param and set OWNER_ALERT_TEMPLATE.")
            log.error(f"🚨 OWNER ALERT FAILED → {pii_vault.mask(owner_phone)}: "
                      f"{exc}{extra}")
    submit_bg(_send)
