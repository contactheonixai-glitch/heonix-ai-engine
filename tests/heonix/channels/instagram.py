"""HEONIX GEN-5 · module `heonix.channels.instagram`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 4171-4237).
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
from heonix.channels.whatsapp import (
    WhatsAppAuthError,
    _MD_BOLD_RE,
    _MD_HEAD_RE,
    _MD_LINK_RE,
    _WA_AUTH_FAIL_CODES,
    _flag_channel_reauth,
    _meta_send_retry,
    _wa_session,
)
from heonix.concurrency import (submit_bg)
from heonix.config import (cfg)
from heonix.logsetup import (log)
from heonix.resilience import (_instagram_breaker)
from heonix.security.crypto import (pii_vault)


def _ig_send_text(psid: str, message: str,
                  ig_id: str = "", token: str = "") -> Dict:
    """Send an Instagram DM reply. psid = the sender id from the webhook.
    v13: per-tenant IG creds with global fallback + token-death detection."""
    token = token or cfg.INSTAGRAM_TOKEN
    if not token:
        log.error("❌ Instagram NOT configured: set INSTAGRAM_TOKEN")
        return {"error": "not_configured"}
    target = ig_id or cfg.INSTAGRAM_ID or "me"
    url = f"https://graph.facebook.com/{cfg.GRAPH_API_VERSION}/{target}/messages"
    payload = {
        "recipient": {"id": psid},
        "message":   {"text": message[:1000]},   # IG text limit = 1000 chars
    }
    resp = _wa_session.post(
        url,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json=payload,
        timeout=(cfg.HTTP_CONNECT_TIMEOUT, 15),
    )
    if resp.status_code >= 400:
        err = {}
        try:
            if "json" in resp.headers.get("content-type", ""):
                err = (resp.json() or {}).get("error", {}) or {}
        except Exception:
            err = {}
        code = err.get("code")
        log.error(f"❌ Instagram send {resp.status_code} code={code} → {resp.text[:500]}")
        if resp.status_code in (401, 403) or code in _WA_AUTH_FAIL_CODES:
            raise WhatsAppAuthError(code, err.get("message", "ig auth failed"))
    resp.raise_for_status()
    return resp.json()


def _ig_send_now(psid: str, message: str, ig_id: str = "",
                 token: str = "", customer_id: str = "") -> None:
    """v14: shared Instagram send body for the async + sync wrappers. Never raises."""
    # v12 #24: Instagram DMs have no markdown — strip bold/heading/link syntax
    # so the user never sees literal ** or ## characters.
    msg = _MD_LINK_RE.sub(r"\1 (\2)", message or "")
    msg = _MD_BOLD_RE.sub(r"\1", msg)
    msg = _MD_HEAD_RE.sub("", msg).replace("**", "")
    try:
        _instagram_breaker.call(_meta_send_retry, _ig_send_text,
                                psid, msg, ig_id, token)  # v12 #36 / v13
        analytics.inc("instagram.sent")
    except WhatsAppAuthError as exc:            # v13: IG token dead
        analytics.inc("instagram.auth_fail")
        _flag_channel_reauth(customer_id, f"ig code={exc.code}")
    except Exception as exc:
        analytics.inc("instagram.error")
        log.error(f"❌ Instagram send failed → {pii_vault.mask(psid)}: {exc}")


def send_instagram_async(psid: str, message: str,
                         ig_id: str = "", token: str = "",
                         customer_id: str = "") -> None:
    submit_bg(_ig_send_now, psid, message, ig_id, token, customer_id)


def send_instagram_sync(psid: str, message: str, ig_id: str = "",
                        token: str = "", customer_id: str = "") -> None:
    """v14 Bug 43: blocking IG reply inside the serialized runner — guarantees DM
    replies to the same follower go out in order."""
    _ig_send_now(psid, message, ig_id, token, customer_id)
