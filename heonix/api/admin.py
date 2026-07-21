"""HEONIX GEN-5 · module `heonix.api.admin`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 10225-10896).
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
from heonix.api.app import (app, limiter)
from heonix.api.helpers import (_int_arg)
from heonix.api.validators import (AdminLoginValidator, CRMContactValidator)
from heonix.booking.engine import (_fmt_local_dt)
from heonix.cache import (brain_cache)
from heonix.channels.whatsapp import (
    WhatsAppAuthError,
    _flag_channel_reauth,
    _wa_send_template,
    _wa_send_text,
)
from heonix.classify import (ghost_resume)
from heonix.config import (cfg)
from heonix.crm import (crm_add_contact, crm_get_contact_full, crm_list_contacts)
from heonix.db.core import (
    PostgreSQLPool,
    _column_exists,
    _db_true,
    _execute,
    _is_unique_violation,
    audit,
)
from heonix.db.store import (brain_wa_creds, get_brain_by_wa_phone_id, get_customer_brain)
from heonix.logsetup import (log)
from heonix.privacy import (_find_subject_rows, erase_data_subject)
from heonix.resilience import (_instagram_breaker, _whatsapp_breaker)
from heonix.security.auth import (
    ROLES,
    _tenant_forbidden,
    generate_jwt,
    require_jwt,
    revoke_jwt,
)
from heonix.security.crypto import (
    _is_bsuid,
    _normalize_msisdn,
    hash_password,
    pii_vault,
    verify_password,
)
from heonix.utils import (_now)
from heonix.security import crypto as _crypto_mod  # GEN-5 SPLIT: _TIMING_PAD lives there
from heonix import _latebind  # GEN-5 SPLIT
_db_pool: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.db.core at startup
_latebind.register('_db_pool', __name__)



# ── Admin: Login (JWT issue) ──────────────────────────────────────────────────
@app.route("/admin/login", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
def admin_login():
    # v15g4 FIX C1: without pyjwt the login "succeeded" with an EMPTY token
    # (generate_jwt returns ""), which then failed every authenticated call.
    if not JWT_AVAILABLE:
        return jsonify({"error": "Auth unavailable — pyjwt is not installed "
                        "on this deployment"}), 503
    try:
        _body = request.get_json(silent=True)
        # v16g6 FIX R6-M8: non-dict JSON gave a cheap unauthenticated 500.
        req = AdminLoginValidator(**(_body if isinstance(_body, dict) else {}))
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "detail": exc.errors()}), 422

    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn,
            "SELECT user_id, hashed_pw, role, tenant_id FROM admin_users "
            "WHERE username=? AND is_active=?",   # v16g4 FIX M10
            (req.username, True if isinstance(_db_pool, PostgreSQLPool) else 1))
        row = cur.fetchone()

    if not row:
        # v15g4 FIX C2: an unknown username returned in ~1ms while a known one
        # cost a ~250ms bcrypt check — a clean timing oracle for enumerating
        # valid admin usernames. Burn the same work on the miss path.
        # GEN-5 SPLIT: _TIMING_PAD is owned by heonix.security.crypto now —
        # rebind through the module attribute so all readers share one pad.
        if _crypto_mod._TIMING_PAD is None:
            _crypto_mod._TIMING_PAD = hash_password("heonix-timing-pad-not-a-secret")
        verify_password(req.password, _crypto_mod._TIMING_PAD)
        analytics.inc("admin.login.fail")
        return jsonify({"error": "Invalid credentials"}), 401
    if not verify_password(req.password, row["hashed_pw"]):
        analytics.inc("admin.login.fail")
        return jsonify({"error": "Invalid credentials"}), 401

    _tenant = (row["tenant_id"] or "") if "tenant_id" in row.keys() else ""
    token = generate_jwt(row["user_id"], row["role"], tenant=_tenant)  # v16g4 FIX M10
    audit(row["user_id"], "admin.login", "admin_users", ip=request.remote_addr)
    analytics.inc("admin.login.success")
    resp = {
        "token":      token,
        "user_id":    row["user_id"],
        "role":       row["role"],
        "expires_in": f"{cfg.JWT_EXPIRY_HOURS}h",
    }
    if _tenant:
        resp["tenant_id"] = _tenant
    return jsonify(resp), 200


# ── Admin: Logout (JWT revocation) ────────────────────────────────────────────
@app.route("/admin/logout", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
@require_jwt(min_role="viewer")
def admin_logout():
    """v16g6 FIX R6-C5: revoke_jwt shipped in R5 with ZERO call sites — the
    denylist was checked on every request and nothing could ever write to it,
    so a leaked admin token stayed valid for the full JWT_EXPIRY_HOURS with no
    kill switch (revoke_jwt's own docstring promised this route existed).
    This is the missing write half: ban this token's jti until its natural
    expiry — fleet-wide when Redis backs the cache."""
    _jti = g.jwt_user.get("jti", "")
    _exp = int(g.jwt_user.get("exp", 0) or 0)
    _ttl = max(60, _exp - int(time.time())) if _exp else 0
    revoke_jwt(_jti, ttl=_ttl)
    audit(g.jwt_user.get("sub", "unknown"), "admin.logout", "admin_users",
          ip=request.remote_addr)
    analytics.inc("admin.logout")
    return jsonify({"status": "logged_out"}), 200


# ── Admin: Create Admin User ───────────────────────────────────────────────────
@app.route("/admin/user", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="superadmin")
def create_admin_user():
    data  = request.get_json(silent=True) or {}
    uname = data.get("username", "").strip()
    pw    = data.get("password", "")
    role  = data.get("role", "admin")
    tenant_id = str(data.get("tenant_id", "") or "").strip()  # v16g4 FIX M10
    if not uname or not pw or role not in ROLES:
        return jsonify({"error": "username, password, and valid role required"}), 400
    if len(pw) < 8:                                          # v16g2 FIX L4
        return jsonify({"error": "password must be at least 8 characters"}), 400
    if tenant_id and role == "superadmin":                    # v16g4 FIX M10
        return jsonify({"error": "superadmin cannot be tenant-scoped"}), 400

    user_id   = f"adm_{uuid.uuid4().hex[:12]}"
    hashed_pw = hash_password(pw)
    try:
        with _db_pool.get() as conn:
            _execute(conn,
                "INSERT INTO admin_users (user_id, username, hashed_pw, role, "
                "created_at, tenant_id) VALUES (?,?,?,?,?,?)",   # v16g4 FIX M10
                (user_id, uname, hashed_pw, role, _now(), tenant_id))
    except Exception as exc:
        # v16g3 FIX R3-M8 + v16g4 FIX M11: only a REAL unique-violation is
        # "already exists" — string-sniffing "constraint" also matched CHECK/
        # NOT-NULL failures, turning schema bugs into a misleading 409.
        if _is_unique_violation(exc):
            return jsonify({"error": "Username already exists"}), 409
        log.error(f"❌ create_admin_user failed: {exc}")
        return jsonify({"error": "Database error creating user"}), 500

    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "admin.create_user", user_id, {"role": role}, request.remote_addr)
    return jsonify({"status": "created", "user_id": user_id, "role": role}), 201


# ── Admin: Customer Stats ─────────────────────────────────────────────────────
@app.route("/admin/customer/<customer_id>/stats", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="viewer")
def customer_stats(customer_id: str):
    brain = get_customer_brain(customer_id)
    if not brain:
        return jsonify({"error": "Not found"}), 404
    with _db_pool.get(read_only=True) as conn:
        sessions = _execute(conn,
            "SELECT COUNT(*) as c FROM chat_sessions WHERE customer_id=?",
            (customer_id,)).fetchone()["c"]
        messages = _execute(conn,
            "SELECT COUNT(*) as c FROM chat_messages cm "
            "JOIN chat_sessions cs ON cm.session_id=cs.session_id "
            "WHERE cs.customer_id=?",
            (customer_id,)).fetchone()["c"]
        leads = _execute(conn,
            "SELECT COUNT(*) as c FROM crm_contacts WHERE customer_id=?",
            (customer_id,)).fetchone()["c"]
    return jsonify({
        "customer_id":    customer_id,
        "name":           brain["customer_name"],
        "business_type":  brain["business_type"],
        "region":         brain.get("region", cfg.REGION),
        "is_active":      bool(brain["is_active"]),
        "total_sessions": sessions,
        "total_messages": messages,
        "total_chats":    brain["total_chats"],
        "crm_leads":      leads,
        "last_updated":   str(brain["updated_at"]),
    }), 200


# ── Admin: Soft Delete Customer ───────────────────────────────────────────────
@app.route("/admin/customer/<customer_id>", methods=["DELETE"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="superadmin")
def delete_customer(customer_id: str):
    brain = get_customer_brain(customer_id)
    if not brain:
        return jsonify({"error": "Not found"}), 404
    old_wa_pid = (brain.get("wa_phone_number_id") or "")
    old_ig_id  = (brain.get("instagram_id") or "")
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    with _db_pool.get() as conn:
        # v14g5 FIX 40: also release the routing identifiers. The unique index on
        # wa_phone_number_id otherwise keeps a DELETED clinic's number reserved
        # forever, so it could never be re-attached to a new clinic.
        clear_route = (_column_exists(conn, "customer_brains", "wa_phone_number_id")
                       and _column_exists(conn, "customer_brains", "instagram_id"))
        # v15g4 FIX B13: also blank the ENCRYPTED TOKENS — a soft-deleted
        # clinic's live Meta secrets were parked on the dead row forever.
        clear_toks = (_column_exists(conn, "customer_brains", "wa_token_enc")
                      and _column_exists(conn, "customer_brains", "ig_token_enc"))
        if clear_route and clear_toks:
            _execute(conn,
                "UPDATE customer_brains SET is_active=?, wa_phone_number_id=?, "
                "instagram_id=?, wa_token_enc=?, ig_token_enc=?, updated_at=? "
                "WHERE customer_id=?",
                (False if is_pg else 0, "", "", "", "", _now(), customer_id))
        elif clear_route:
            _execute(conn,
                "UPDATE customer_brains SET is_active=?, wa_phone_number_id=?, "
                "instagram_id=?, updated_at=? WHERE customer_id=?",
                (False if is_pg else 0, "", "", _now(), customer_id))
        else:
            _execute(conn,
                "UPDATE customer_brains SET is_active=?, updated_at=? WHERE customer_id=?",
                (False if is_pg else 0, _now(), customer_id))
    brain_cache.delete(f"brain:{customer_id}")         # v16g6 FIX R6-L6
    # bust every routing cache that could still point at this (now freed) number
    if old_wa_pid:
        brain_cache.delete(f"wapid:{old_wa_pid}")
        brain_cache.delete(f"wa_route:{old_wa_pid}")   # v15g4 FIX B2 (same class)
    if old_ig_id:
        brain_cache.delete(f"igid:{old_ig_id}")
    brain_cache.delete("wa_route:__single__")
    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "customer.delete", customer_id, ip=request.remote_addr)
    analytics.inc("customer.deleted")
    log.info(f"🗑️  Soft-deleted → {customer_id} (released wa_pid={old_wa_pid or '(none)'})")
    return jsonify({"status": "deleted", "customer_id": customer_id}), 200


# ── v13 Admin: Attach a clinic's OWN WhatsApp / Instagram credentials ─────────
@app.route("/admin/customer/<customer_id>/channel", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="superadmin")
def set_customer_channel(customer_id: str):
    """v13 TRUE MULTI-TENANT: securely attach a clinic's OWN WhatsApp business
    number + token (and/or Instagram account + token). Tokens are AES-256-GCM
    encrypted at rest. Rejects (409) if the WhatsApp number already belongs to a
    DIFFERENT clinic — both here (friendly error) and at the DB unique index
    (hard safety net). NEVER expose this on a public Tally form — JWT only.
    Body: {wa_phone_number_id, wa_token, instagram_id, ig_token}"""
    brain = get_customer_brain(customer_id)
    if not brain:
        return jsonify({"error": "Not found"}), 404
    # v15g4 FIX B2: remember the CURRENT routing ids — after the update we must
    # bust their cache entries too, or inbound traffic on the OLD number keeps
    # routing to this clinic (stale brain + creds) for up to ROUTE_CACHE_TTL.
    old_wa_pid = (brain.get("wa_phone_number_id") or "")
    old_ig_id  = (brain.get("instagram_id") or "")
    body   = request.get_json(silent=True) or {}
    wa_pid = (body.get("wa_phone_number_id") or "").strip()
    wa_tok = (body.get("wa_token") or "").strip()
    ig_id  = (body.get("instagram_id") or "").strip()
    ig_tok = (body.get("ig_token") or "").strip()

    # v15g4 FIX C6: Meta phone-number ids are numeric — a pasted typo silently
    # routed nothing (webhooks simply never matched). Reject it up-front.
    if wa_pid and not wa_pid.isdigit():
        return jsonify({"error": "wa_phone_number_id must be the numeric id "
                        "from Meta (WhatsApp → API Setup), not a phone number "
                        "or a name"}), 400
    # v16g4 FIX L18: twin of FIX C6 — IG account ids are numeric too; a pasted
    # @handle attached fine and then simply never matched an inbound webhook.
    if ig_id and not ig_id.isdigit():
        return jsonify({"error": "instagram_id must be the numeric IG account "
                        "id from Meta, not an @handle"}), 400

    # 🔴 friendly pre-check: this number already attached to another clinic?
    if wa_pid:
        existing = get_brain_by_wa_phone_id(wa_pid)
        if existing and existing.get("customer_id") != customer_id:
            return jsonify({"error": "wa_phone_number_id already attached to "
                            f"{existing['customer_id']}"}), 409

    # v14g5 FIX 1: build the UPDATE from ONLY the channel keys actually present in
    # the request body. Attaching just Instagram must never blank out an existing
    # WhatsApp number/token (and vice-versa). A bare key with empty value is an
    # explicit "clear this field".
    sets: list[str] = []
    vals: list[Any] = []
    if "wa_phone_number_id" in body:
        sets.append("wa_phone_number_id=?"); vals.append(wa_pid)
    if "wa_token" in body:
        sets.append("wa_token_enc=?");       vals.append(pii_vault.encrypt(wa_tok) if wa_tok else "")
    if "instagram_id" in body:
        sets.append("instagram_id=?");       vals.append(ig_id)
    if "ig_token" in body:
        sets.append("ig_token_enc=?");       vals.append(pii_vault.encrypt(ig_tok) if ig_tok else "")
    if not sets:
        return jsonify({"error": "No channel fields provided "
                        "(wa_phone_number_id, wa_token, instagram_id, ig_token)"}), 400
    sets.append("channel_status=?"); vals.append("ok")
    sets.append("updated_at=?");     vals.append(_now())
    vals.append(customer_id)

    try:
        with _db_pool.get() as conn:
            _execute(conn,
                "UPDATE customer_brains SET " + ", ".join(sets) +
                " WHERE customer_id=?", tuple(vals))
    except Exception as exc:
        # DB-level unique-index violation → 409 (the real safety net)
        if "uq_brain_wa_pid" in str(exc) or "unique" in str(exc).lower():
            return jsonify({"error": "wa_phone_number_id already in use"}), 409
        log.error(f"❌ set channel failed for {customer_id}: {exc}")
        return jsonify({"error": "Update failed"}), 500

    # bust every cache key that could hold the old routing/creds
    # v15g4 FIX B2: OLD ids and the wa_route:* cid entries included — the old
    # code busted only the NEW wapid, leaving the previous number's routing
    # (and this clinic's stale creds) served from cache for up to 10 minutes.
    brain_cache.delete(f"brain:{customer_id}")         # v16g6 FIX R6-L6
    for pid in {wa_pid, old_wa_pid}:
        if pid:
            brain_cache.delete(f"wapid:{pid}")
            brain_cache.delete(f"wa_route:{pid}")
    for iid in {ig_id, old_ig_id}:
        if iid:
            brain_cache.delete(f"igid:{iid}")
    brain_cache.delete("wa_route:__single__")
    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "customer.channel", customer_id,
          {"wa_pid": wa_pid, "ig": bool(ig_id)}, request.remote_addr)
    analytics.inc("customer.channel_set")
    log.info(f"🔗 Channel attached → {customer_id} wa_pid={wa_pid or '(none)'}")
    return jsonify({"status": "ok", "customer_id": customer_id,
                    "wa_phone_number_id": wa_pid,
                    "instagram_id": ig_id,
                    "channel_status": "ok"}), 200


# ── v13 Admin: Onboarding smoke-test — is this clinic's token actually alive? ──
@app.route("/admin/customer/<customer_id>/smoke-test", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="superadmin")
def smoke_test_channel(customer_id: str):
    """v13 god-mode weapon: in ~2 seconds, KNOW whether a freshly-attached clinic
    token works — before the clinic's first patient finds out the hard way. Sends
    ONE real WhatsApp to the number you pass (the clinic owner's phone), using the
    clinic's OWN creds, and reports alive / dead-token / misconfigured.
    Body: {to: '<owner phone in intl format>'}"""
    if not cfg.SMOKE_TEST_ENABLED:
        return jsonify({"error": "Smoke test disabled (set SMOKE_TEST_ENABLED=1)"}), 403
    brain = get_customer_brain(customer_id)
    if not brain:
        return jsonify({"error": "Not found"}), 404
    to = ((request.get_json(silent=True) or {}).get("to") or "").strip()
    if not _is_bsuid(to):                          # v16 U2: BSUIDs pass as-is
        to = re.sub(r"[^\d+]", "", to)
    if len(to) < 7:
        return jsonify({"error": "Provide 'to' = a valid phone in international format"}), 400

    pid, tok = brain_wa_creds(brain)
    if not pid or not tok:
        return jsonify({"channel": "whatsapp", "ok": False,
                        "reason": "no_credentials",
                        "hint": "Attach creds via POST /admin/customer/"
                                f"{customer_id}/channel first."}), 200

    # synchronous send so we can report the actual result (not fire-and-forget)
    # v16g4 FIX M6: the owner's number is usually COLD (never messaged this
    # line) — a free text passes the API (proving the token) but is silently
    # dropped by the 24h-window rule, so "ALIVE" + no phone buzz sent you
    # chasing a phantom bug. Use an approved template when one exists (always
    # delivers); otherwise still run the free-text token check but SAY the
    # delivery caveat out loud in the response.
    _smoke_body = (f"✅ HEONIX smoke-test: {brain.get('bot_name') or 'your AI'} "
                   f"is live for {brain.get('customer_name', customer_id)}.")
    _tmpl = cfg.WELCOME_TEMPLATE or cfg.REMINDER_TEMPLATE
    _delivery_note = None
    try:
        if _tmpl:
            _wa_send_template(to, _tmpl,
                              cfg.WELCOME_TEMPLATE_LANG if cfg.WELCOME_TEMPLATE
                              else cfg.REMINDER_TEMPLATE_LANG,
                              _smoke_body, pid, tok)
        else:
            _wa_send_text(to, _smoke_body, pid, tok)
            _delivery_note = ("Token is valid, but this was FREE TEXT — it "
                              "only DELIVERS if that phone messaged this line "
                              "in the last 24h. For a guaranteed test buzz, "
                              "approve a template and set WELCOME_TEMPLATE.")
        with _db_pool.get() as conn:
            if _column_exists(conn, "customer_brains", "channel_status"):
                _execute(conn,
                    "UPDATE customer_brains SET channel_status=?, updated_at=? "
                    "WHERE customer_id=?", ("ok", _now(), customer_id))
        brain_cache.delete(f"brain:{customer_id}")     # v16g6 FIX R6-L6
        analytics.inc("smoke_test.pass")
        _resp = {"channel": "whatsapp", "ok": True,
                 "wa_phone_number_id": pid,
                 "message": "Test message sent — token is ALIVE."}
        if _delivery_note:
            _resp["delivery_note"] = _delivery_note   # v16g4 FIX M6
        return jsonify(_resp), 200
    except WhatsAppAuthError as exc:
        _flag_channel_reauth(customer_id, f"smoke-test code={exc.code}")
        analytics.inc("smoke_test.auth_fail")
        return jsonify({"channel": "whatsapp", "ok": False,
                        "reason": "dead_token", "code": exc.code,
                        "hint": "Token expired/revoked. Re-attach a fresh token via "
                                f"POST /admin/customer/{customer_id}/channel."}), 200
    except Exception as exc:
        analytics.inc("smoke_test.error")
        return jsonify({"channel": "whatsapp", "ok": False,
                        "reason": "send_failed", "detail": str(exc)[:300]}), 200


# ── v13 Admin: Tenant-health dashboard — which clinics are dark right now? ─────
@app.route("/admin/tenants/health", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="viewer")
def tenants_health():
    """v13: fleet view. How many clinics are healthy vs need a token re-attach,
    and exactly which ones — so you fix dark clinics proactively, not reactively."""
    is_pg  = isinstance(_db_pool, PostgreSQLPool)
    active = True if is_pg else 1
    healthy = needs_reauth = total = 0
    dark: List[Dict] = []
    try:
        with _db_pool.get(read_only=True) as conn:
            has_status = _column_exists(conn, "customer_brains", "channel_status")
            cur = _execute(conn,
                "SELECT COUNT(*) AS c FROM customer_brains WHERE is_active=?", (active,))
            total = cur.fetchone()["c"]
            if has_status:
                # v16g4 FIX L3: needs_reauth came from len(dark) — capped at
                # the LIMIT 200 detail list, so a fleet with 250 dark clinics
                # reported 200 dark / 50 "healthy". Count separately; the
                # list stays a 200-row sample for the response body.
                cur = _execute(conn,
                    "SELECT COUNT(*) AS c FROM customer_brains "
                    "WHERE is_active=? AND channel_status=?",
                    (active, "needs_reauth"))
                needs_reauth = cur.fetchone()["c"]
                cur = _execute(conn,
                    "SELECT customer_id, customer_name, channel_status, updated_at "
                    "FROM customer_brains WHERE is_active=? AND channel_status=? "
                    "ORDER BY updated_at DESC LIMIT 200",
                    (active, "needs_reauth"))
                for r in cur.fetchall():
                    dark.append({"customer_id": r["customer_id"],
                                 "name": r["customer_name"],
                                 "since": str(r["updated_at"])})
                healthy = max(0, total - needs_reauth)
            else:
                healthy = total
    except Exception as exc:
        log.warning(f"⚠️  tenants/health query failed: {exc}")
        return jsonify({"error": "query_failed"}), 500

    return jsonify({
        "engine":             "HEONIX Ultra v16.0 GEN-3",
        "region":             cfg.REGION,
        "active_tenants":     total,
        "healthy":            healthy,
        "needs_reauth":       needs_reauth,
        "needs_reauth_list":  dark,
        "whatsapp_circuit":   _whatsapp_breaker.state,
        "instagram_circuit":  _instagram_breaker.state,
    }), 200


# ── Admin: List All Customers ─────────────────────────────────────────────────
@app.route("/admin/customers", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="viewer")
def list_customers():
    page     = _int_arg("page", 1, 1, 10**6)          # v15g4 FIX C3
    per_page = _int_arg("per_page", 50, 1, 100)        # v15g4 FIX C3
    offset   = (page - 1) * per_page
    is_pg    = isinstance(_db_pool, PostgreSQLPool)
    active   = True if is_pg else 1
    with _db_pool.get(read_only=True) as conn:
        total_row = _execute(conn,
            "SELECT COUNT(*) as c FROM customer_brains WHERE is_active=?", (active,)).fetchone()
        total     = total_row["c"] if total_row else 0
        rows      = _execute(conn,
            "SELECT customer_id, customer_name, business_type, plan_tier, "
            "total_chats, region, created_at FROM customer_brains "
            "WHERE is_active=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (active, per_page, offset)).fetchall()
    return jsonify({
        "customers": [dict(r) for r in rows],
        "total":     total,
        "page":      page,
        "per_page":  per_page,
    }), 200


# ── CRM: Add Contact ──────────────────────────────────────────────────────────
@app.route("/crm/contact", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="admin")
def crm_add_contact_api():
    data = request.get_json(silent=True) or {}
    try:
        contact = CRMContactValidator(**data)
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "detail": exc.errors()}), 422

    if _tenant_forbidden(contact.customer_id):        # v16g4 FIX M10
        return jsonify({"error": "Token is scoped to a different tenant"}), 403
    brain = get_customer_brain(contact.customer_id)
    if not brain:
        return jsonify({"error": "Customer not found"}), 404

    contact_id = crm_add_contact(
        contact.customer_id, contact.name, contact.phone,
        contact.email, contact.notes, contact.contact_stage, contact.is_consented,
    )
    if not contact_id:
        # v16g6 FIX R6-L8: 201 with contact_id 0 — the insert lost the race
        # AND the recovery re-lookup failed. Nothing verifiably exists;
        # saying "created" with a fake id poisons the caller's records.
        return jsonify({"error": "Contact could not be verified as created — "
                                 "please retry"}), 503
    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "crm.add_contact", contact.customer_id,
          {"stage": contact.contact_stage, "consented": contact.is_consented},
          request.remote_addr)
    return jsonify({
        "status":        "success",
        "contact_id":    contact_id,
        "pii_encrypted": pii_vault.enabled,
        "request_id":    g.get("request_id"),
    }), 201


# ── CRM: List Contacts ────────────────────────────────────────────────────────
@app.route("/crm/contacts/<customer_id>", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="viewer")
def crm_list_contacts_api(customer_id: str):
    stage    = request.args.get("stage")
    page     = _int_arg("page", 1, 1, 10**6)          # v15g4 FIX C3
    per_page = _int_arg("per_page", 50, 1, 100)        # v15g4 FIX C3
    contacts, total = crm_list_contacts(customer_id, stage, page, per_page)
    return jsonify({
        "contacts": contacts,
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "note":     "Phones masked in list view. Use /crm/contact/{id} for full details.",
    }), 200


# ── CRM: Full Contact ─────────────────────────────────────────────────────────
@app.route("/crm/contact/<int:contact_id>", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="admin")
def crm_get_contact_api(contact_id: int):
    # v14g5 FIX 4 (IDOR): require the caller to name the tenant they're reading, so
    # a non-superadmin token can't enumerate contact ids across clinics. Superadmin
    # may omit it for cross-tenant support.
    customer_id = (request.args.get("customer_id") or "").strip()
    role        = g.jwt_user.get("role", "viewer")
    if not customer_id and role != "superadmin":
        return jsonify({"error": "customer_id query param required"}), 400
    if _tenant_forbidden(customer_id):                 # v16g4 FIX M10
        return jsonify({"error": "Token is scoped to a different tenant"}), 403
    contact = crm_get_contact_full(contact_id, customer_id)
    if not contact:
        return jsonify({"error": "Contact not found"}), 404
    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "crm.view_full", f"{customer_id or '*'}:{contact_id}", ip=request.remote_addr)
    return jsonify(contact), 200


# ── v14g4 DPDP: right-to-erasure for ONE data subject (by phone) ──────────────
@app.route("/admin/customer/<customer_id>/erase-subject", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="admin")
def erase_subject_api(customer_id: str):
    """DPDP Act 2023 right-to-erasure. Body: {"phone": "+91..."}. Deletes this
    person's CRM contact, bookings, RAG memory, and cache-mapped chat session."""
    data  = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    if not phone:
        return jsonify({"error": "phone is required"}), 400
    report = erase_data_subject(customer_id, phone)
    actor  = g.jwt_user.get("sub", "unknown")
    audit(actor, "dpdp.erase_subject", f"{customer_id}:{pii_vault.mask(phone)}",
          ip=request.remote_addr)
    return jsonify({"status": "erased", "customer_id": customer_id, "deleted": report}), 200


# ── v14g4: record/clear a contact's marketing consent (DPDP) ──────────────────
@app.route("/admin/customer/<customer_id>/consent", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="admin")
def set_consent_api(customer_id: str):
    """Body: {"phone": "+91...", "consented": true}. Only CONSENTED contacts are
    ever sent cold-lead follow-ups by the scheduler."""
    data  = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    if not phone:
        return jsonify({"error": "phone is required"}), 400
    consented = bool(data.get("consented", True))
    # v16g2 FIX N9: resolve the subject the same way erasure does (M5) — a
    # USERNAME patient's row is keyed on the BSUID hash, so hashing the real
    # number the clinic holds matched nothing and this endpoint answered
    # 200 "ok, rows_updated: 0" while consent silently never landed for
    # exactly the patients U3 exists for. Zero matches is now a 404.
    rows = _find_subject_rows(customer_id, phone)
    if not rows:
        return jsonify({"error": "subject not found for that number"}), 404
    val = _db_true() if consented else (False if isinstance(_db_pool, PostgreSQLPool) else 0)
    updated = 0
    try:
        with _db_pool.get() as conn:
            for r in rows:
                cur = _execute(conn,
                    "UPDATE crm_contacts SET is_consented=? WHERE id=? AND customer_id=?",
                    (val, r["id"], customer_id))
                updated += getattr(cur, "rowcount", 0) or 0
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "dpdp.set_consent", f"{customer_id}:{pii_vault.mask(phone)}={consented}",
          ip=request.remote_addr)
    return jsonify({"status": "ok", "consented": consented, "rows_updated": updated}), 200


# ── v15: instantly un-mute the AI for one conversation (owner is done) ────────
@app.route("/admin/customer/<customer_id>/ghost-resume", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="admin")
def ghost_resume_api(customer_id: str):
    """v15 FIX 17: ghost_resume() existed since v10 but NOTHING ever called it —
    once a human took over a chat, the AI stayed muted for the full
    GHOST_MUTE_SECONDS with no way back. Now the owner (or you) can hand the
    conversation back to the bot the second they're done.
    Body: {"phone": "9198..."} (WhatsApp) and/or {"ig_sender": "<psid>"}."""
    data  = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    ig    = (data.get("ig_sender") or "").strip()
    if not phone and not ig:
        return jsonify({"error": "phone or ig_sender required"}), 400
    resumed: List[str] = []
    if phone:
        # v16g2 FIX L3: the mute key was stored under Meta's bare-digit
        # spelling — an owner typing "+91 98…" got 200 "resumed" while nothing
        # unmuted. Resume under every candidate spelling (erasure's B4 trick).
        _digits = re.sub(r"\D", "", phone)
        for _p in dict.fromkeys([phone, _digits, _normalize_msisdn(phone)]):
            if _p:
                ghost_resume(f"{customer_id}:{_p}")
        resumed.append("whatsapp")
    if ig:
        ghost_resume(f"ig:{customer_id}:{ig}")
        resumed.append("instagram")
    audit(g.jwt_user.get("sub", "unknown"), "ghost.resume",
          f"{customer_id}:{pii_vault.mask(phone or ig)}", ip=request.remote_addr)
    analytics.inc("ghost.resumed")
    return jsonify({"status": "resumed", "customer_id": customer_id,
                    "channels": resumed}), 200


# ── v14g4: list a clinic's upcoming bookings (ops view) ───────────────────────
@app.route("/admin/customer/<customer_id>/bookings", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="viewer")
def list_bookings_api(customer_id: str):
    """Upcoming booked appointments for a clinic. Phones are masked."""
    now_iso = datetime.now(timezone.utc).isoformat()
    limit   = _int_arg("limit", 50, 1, 200)            # v15g4 FIX C3
    out: List[Dict] = []
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT id, enc_phone, slot_start, slot_end, status, reminders_sent "
                "FROM bookings WHERE customer_id=? AND status='booked' AND slot_start >= ? "
                "ORDER BY slot_start ASC LIMIT ?", (customer_id, now_iso, limit))
            for r in cur.fetchall():
                d = dict(r)
                out.append({
                    "id":            d["id"],
                    "phone":         pii_vault.mask(pii_vault.decrypt(d["enc_phone"])),
                    "slot_start":    d["slot_start"],
                    "slot_end":      d["slot_end"],
                    "local_time":    _fmt_local_dt(d["slot_start"]),
                    "status":        d["status"],
                    "reminders_sent": d.get("reminders_sent", ""),
                })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    return jsonify({"customer_id": customer_id, "count": len(out), "bookings": out}), 200


# ── Analytics Snapshot ────────────────────────────────────────────────────────
@app.route("/admin/analytics", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="viewer")
def analytics_snapshot():
    """Real-time analytics dashboard endpoint (FIX #5)."""
    snap = analytics.snapshot()
    return jsonify({
        "region":      cfg.REGION,
        "engine":      "HEONIX Ultra v16.0 GEN-3",
        "counters":    snap["counters"],
        "latency_p99": snap["latency_p99"],
        "uptime_secs": snap["uptime_secs"],
    }), 200
