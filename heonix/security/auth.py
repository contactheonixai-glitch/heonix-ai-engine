"""HEONIX GEN-5 · module `heonix.security.auth`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 1434-1587, 3370-3404, 8810-8838).
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
from heonix.logsetup import (log)


ROLES = {"superadmin", "admin", "viewer"}
_ROLE_RANK = {"viewer": 0, "admin": 1, "superadmin": 2}
# v16g5 FIX R5-L3: issuer/audience binding for admin JWTs.
_JWT_ISS = "heonix-engine"
_JWT_AUD = "heonix-admin"


def _tenant_forbidden(customer_id: str) -> bool:
    """v16g4 FIX M10: True when the current JWT is tenant-scoped and the
    requested customer_id is not its tenant. For endpoints that carry
    customer_id in the body or query string (the path-param case is enforced
    centrally in require_jwt)."""
    u = getattr(g, "jwt_user", None) or {}
    tnt = u.get("tnt", "")
    return bool(tnt and u.get("role") != "superadmin"
                and customer_id and customer_id != tnt)


def generate_jwt(user_id: str, role: str = "admin", tenant: str = "") -> str:
    if not JWT_AVAILABLE:
        return ""
    payload = {
        "sub":  user_id,
        "role": role,
        "iat":  datetime.now(timezone.utc),
        "exp":  datetime.now(timezone.utc) + timedelta(hours=cfg.JWT_EXPIRY_HOURS),
        "jti":  uuid.uuid4().hex,
        "rgn":  cfg.REGION,
        # v16g5 FIX R5-L3: bind the token to this issuer/audience so a token
        # minted by another HEONIX deployment sharing an ENCRYPTION_KEY-derived
        # secret cannot be replayed here.
        "iss":  _JWT_ISS,
        "aud":  _JWT_AUD,
    }
    if tenant:                       # v16g4 FIX M10: tenant-scoped admin token
        payload["tnt"] = tenant
    return pyjwt.encode(payload, cfg.JWT_SECRET_KEY, algorithm="HS256")


def revoke_jwt(jti: str, ttl: int = 0) -> None:
    """v16g5 FIX R5-L3: add a token id to the denylist until its natural
    expiry. Backed by the shared cache, so a revoke lands fleet-wide on Redis
    (and process-locally in dev). This is what makes /admin/logout real —
    before this a leaked admin token stayed valid for the full expiry window
    with no way to kill it."""
    if not jti:
        return
    try:
        brain_cache.set(f"jwtban:{jti}", "1",
                        ttl=ttl or (cfg.JWT_EXPIRY_HOURS * 3600))
    except Exception as exc:
        log.warning(f"\u26a0\ufe0f  JWT revoke failed for {jti[:8]}: {exc}")


def decode_jwt(token: str) -> Optional[Dict]:
    if not JWT_AVAILABLE:
        return None
    try:
        # v16g6 FIX R6-M9: passing issuer= makes PyJWT raise
        # MissingRequiredClaimError when `iss` is ABSENT — the exact legacy
        # token the R5-L3 comment promised to tolerate — and the broad
        # InvalidTokenError catch below turned that into None, logging every
        # pre-R5 admin out after all. iss/aud are verified MANUALLY just
        # below: strict when present, tolerated when absent, exactly as
        # documented.
        payload = pyjwt.decode(
            token, cfg.JWT_SECRET_KEY, algorithms=["HS256"],
            options={"require": ["exp"], "verify_aud": False})
        _iss = payload.get("iss")
        _aud = payload.get("aud")
        if (_iss and _iss != _JWT_ISS) or (_aud and _aud != _JWT_AUD):
            return None
        # Denylist check (revoked / logged out).
        _jti = payload.get("jti", "")
        if _jti:
            try:
                if brain_cache.get(f"jwtban:{_jti}"):
                    return None
            except Exception as _rex:
                # v16g6 FIX R6-M10: still fail OPEN (401ing every request on
                # a Redis blip is worse than honouring a token for one gap) —
                # but LOUDLY. With /admin/logout live (R6-C5), silence here
                # means a banned token quietly works again. Counter + a
                # once-per-5-min alarm make the gap visible; in no-Redis mode
                # a revoke is per-worker by construction (ops constraint,
                # STRICT_PROD requires Redis anyway).
                try:
                    analytics.inc("jwt.revocation_check_failed")
                    if brain_cache.setnx("warn:jwtban_check", ttl=300):
                        log.error(f"❌ JWT revocation check UNAVAILABLE — "
                                  f"revoked tokens may be honoured: {_rex}")
                except Exception:
                    pass
        return payload
    except pyjwt.InvalidTokenError:   # v14g3 BUG 19: ExpiredSignatureError \u2282 InvalidTokenError
        return None


def require_jwt(min_role: str = "admin"):
    """Decorator: validates Bearer JWT and enforces minimum role hierarchy."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Legacy X-Admin-Key backward compat.
            # v16g4 FIX M13: this header is a permanent, unrotatable env
            # superadmin. In STRICT_PROD it is refused unless explicitly
            # acknowledged via ADMIN_API_KEY_LEGACY_OK=1 (JWT login is the
            # supported path), and the audit actor now carries a fingerprint
            # of the key so a rotation is visible in the audit trail instead
            # of every row reading the same anonymous 'legacy_admin'.
            if cfg.ADMIN_API_KEY and (not cfg.STRICT_PROD
                                      or cfg.ADMIN_API_KEY_LEGACY_OK):
                try:
                    # v16g2 FIX L6: a non-ASCII header value made compare_digest
                    # raise TypeError → 500. Garbage input is just a 401.
                    _hdr_ok = hmac.compare_digest(
                        request.headers.get("X-Admin-Key", ""),
                        cfg.ADMIN_API_KEY)   # v14g5 FIX 19: constant-time
                except (TypeError, UnicodeError):
                    _hdr_ok = False
                if _hdr_ok:
                    _fp = hashlib.sha256(cfg.ADMIN_API_KEY.encode()).hexdigest()[:8]
                    g.jwt_user = {"sub": f"legacy_admin:{_fp}",
                                  "role": "superadmin"}
                    return func(*args, **kwargs)

            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "Missing Authorization header"}), 401

            payload = decode_jwt(auth.split(" ", 1)[1])
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401

            user_role = payload.get("role", "viewer")
            if _ROLE_RANK.get(user_role, -1) < _ROLE_RANK.get(min_role, 99):
                return jsonify({"error": f"Insufficient permissions. Required: {min_role}"}), 403

            # v16g4 FIX M10: central tenant fence. A token minted with a "tnt"
            # claim (non-superadmin) can only act on ITS clinic — enforced here
            # for every route with a customer_id path param, so no endpoint can
            # forget the check. Endpoints that take customer_id in body/query
            # call _tenant_forbidden() explicitly.
            _tnt = payload.get("tnt", "")
            if (_tnt and user_role != "superadmin"
                    and "customer_id" in kwargs
                    and kwargs["customer_id"] != _tnt):
                return jsonify({"error": "Token is scoped to a different "
                                         "tenant"}), 403

            g.jwt_user = payload
            return func(*args, **kwargs)
        return wrapper
    return decorator


def _safe_ct_eq(a: str, b: str) -> bool:
    """v16g3 FIX R3-M1: hmac.compare_digest raises TypeError on non-ASCII str
    input — a probe with a garbage hub.verify_token / X-Api-Key /
    X-Metrics-Token 500'd instead of 401/403-ing. v16g2 FIX L6 guarded only
    the admin header; this is the shared guard for every header/param path."""
    try:
        return hmac.compare_digest(a or "", b or "")
    except (TypeError, UnicodeError):
        return False


def verify_meta_signature(raw_body: bytes, signature_header: str,
                          app_secret: str) -> bool:
    """v10: shared by WhatsApp + Instagram webhooks (same X-Hub-Signature-256).

    v14g3 BUG 7: an empty app secret used to mean 'accept everything', so a
    deployment that forgot to set WHATSAPP_APP_SECRET silently accepted FORGED
    webhooks from anyone who found the URL. Now an empty secret skips the check
    ONLY in dev; under STRICT_PROD (or REQUIRE_WEBHOOK_SIGNATURE) a missing
    secret is fail-CLOSED — in production an unsigned webhook is an attack, not
    a convenience."""
    if not app_secret:
        if cfg.STRICT_PROD or cfg.REQUIRE_WEBHOOK_SIGNATURE:
            log.error("🛑 Webhook rejected: signature required but no app secret "
                      "set (configure WHATSAPP_APP_SECRET / INSTAGRAM_APP_SECRET).")
            return False
        return True  # dev mode only — explicitly insecure
    if not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def verify_tally_signature(raw_body: bytes, headers: dict) -> bool:
    """Verify Tally webhook signature if secret is configured.
    v15 FIX 3 (CRITICAL): Tally signs HMAC-SHA256 over the raw body and encodes
    it BASE64 in the tally-signature header (per Tally's own docs). The old code
    compared a HEXDIGEST — so the moment TALLY_WEBHOOK_SECRET was set, every
    legitimate onboarding webhook was rejected with 401 and signups silently
    died. Unset secret skips the check in DEV only.
    v16g4 FIX H4: verify_meta_signature refuses unsigned webhooks under
    STRICT_PROD / REQUIRE_WEBHOOK_SIGNATURE — but this twin returned True
    whenever the secret was unset, even in strict prod. That left the
    brain-minting endpoint (which also chose the outbound welcome target)
    open to anyone who found the URL. Now the same fail-closed rule applies.
    v16g4 FIX L8: the secret is read from cfg like every other secret, not a
    per-request os.getenv."""
    tally_secret = cfg.TALLY_WEBHOOK_SECRET
    if not tally_secret:
        if cfg.STRICT_PROD or cfg.REQUIRE_WEBHOOK_SIGNATURE:
            log.error("🛑 Tally webhook REJECTED: TALLY_WEBHOOK_SECRET unset "
                      "under STRICT_PROD/REQUIRE_WEBHOOK_SIGNATURE (v16g4 FIX H4)")
            return False
        return True
    # v16g5 FIX R5-C2: `headers` is now the case-insensitive Werkzeug object
    # (a plain dict still works — the explicit spellings below cover it).
    sig = (headers.get("Tally-Signature", "")
           or headers.get("tally-signature", "")
           or headers.get("TALLY-SIGNATURE", "") or "")
    digest   = hmac.new(tally_secret.encode(), raw_body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(expected, sig)
