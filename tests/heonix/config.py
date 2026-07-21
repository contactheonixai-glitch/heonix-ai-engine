"""HEONIX GEN-5 · module `heonix.config`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 877-1206).
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



def _env_int(name: str, default) -> int:
    """v16g3 FIX R3-L3: a typo'd numeric env (MAX_POOL_SIZE=abc) killed the
    boot with a bare ValueError mid-import — v15 FIX 25 gave only the hex key
    a friendly failure. Warn + default instead. (The logger isn't built yet at
    Config time, so this writes straight to stderr.)"""
    raw = os.getenv(name, "")
    try:
        return int(str(raw).strip()) if str(raw).strip() else int(default)
    except (TypeError, ValueError):
        sys.stderr.write(f"⚠️  HEONIX: env {name}={raw!r} is not a valid "
                         f"integer — using default {default}.\n")
        return int(default)


def _env_float(name: str, default) -> float:
    """v16g3 FIX R3-L3 (float twin of _env_int)."""
    raw = os.getenv(name, "")
    try:
        return float(str(raw).strip()) if str(raw).strip() else float(default)
    except (TypeError, ValueError):
        sys.stderr.write(f"⚠️  HEONIX: env {name}={raw!r} is not a valid "
                         f"number — using default {default}.\n")
        return float(default)


_ENV_BOOL_TRUE  = frozenset({"1", "true", "yes", "on"})
_ENV_BOOL_FALSE = frozenset({"0", "false", "no", "off"})


def _env_bool(name: str, default: bool) -> bool:
    """v16g4 FIX M1: env booleans previously split into TWO dialects —
    STRICT_PROD/SMOKE_TEST_ENABLED/REQUIRE_WEBHOOK_SIGNATURE/ENABLE_PHONE_CAPTURE
    accepted only "1" while ENABLE_BOOKING/ENABLE_SCHEDULER/FOLLOWUP_ENABLED/
    DEBUG/… accepted only "true". STRICT_PROD=true was silently OFF and
    ENABLE_BOOKING=1 silently OFF, with no warning either way. One parser now
    accepts both dialects (1/0, true/false, yes/no, on/off, case-insensitive),
    warns loudly on garbage, and treats empty/unset as the default — matching
    _env_int semantics."""
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return bool(default)
    val = str(raw).strip().lower()
    if val in _ENV_BOOL_TRUE:
        return True
    if val in _ENV_BOOL_FALSE:
        return False
    sys.stderr.write(f"⚠️  HEONIX: env {name}={raw!r} is not a valid boolean "
                     f"(use 1/0 or true/false) — using default {default}.\n")
    return bool(default)


class Config:
    # ── Database ──
    DATABASE_MODE: str          = os.getenv("DATABASE_MODE", "postgres")
    DATABASE_URL: str           = os.getenv("DATABASE_URL", "")
    DATABASE_REPLICA_URL: str   = os.getenv("DATABASE_REPLICA_URL", "")   # NEW v8
    DATABASE_FILE: str          = os.getenv("DATABASE_FILE", "heonix_ultra.db")  # v14g3 BUG 20: matches the docstring
    MAX_POOL_SIZE: int          = _env_int("MAX_POOL_SIZE", "20")

    # ── AI Keys ──
    GENAI_API_KEY: str          = os.getenv("GENAI_API_KEY", "")
    OPENAI_API_KEY: str         = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str      = os.getenv("ANTHROPIC_API_KEY", "")

    # ── AI Models ──
    GEMINI_MODEL: str           = os.getenv("GEMINI_MODEL",    "gemini-3.1-flash-lite")  # v11 #5: 2.5-flash retiring 2026; lite = 6x cheaper, chatbot-tuned
    # Per-customer premium model: pass plan_tier="premium" → uses GEMINI_MODEL_PREMIUM.
    GEMINI_MODEL_PREMIUM: str   = os.getenv("GEMINI_MODEL_PREMIUM", "gemini-3.5-flash")   # only worth it for tool-heavy/agentic clients
    OPENAI_MODEL: str           = os.getenv("OPENAI_MODEL",    "gpt-4o-mini")
    ANTHROPIC_MODEL: str        = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    AI_MAX_TOKENS: int          = _env_int("AI_MAX_TOKENS", "1000")
    AI_TIMEOUT_SECS: float      = _env_float("AI_TIMEOUT_SECS", "30")

    # ── WhatsApp Cloud API ──
    WHATSAPP_TOKEN: str         = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_ID: str      = os.getenv("WHATSAPP_PHONE_ID", "")
    WHATSAPP_VERIFY_TOKEN: str  = os.getenv("WHATSAPP_VERIFY_TOKEN", "heonix_verify")
    WHATSAPP_APP_SECRET: str    = os.getenv("WHATSAPP_APP_SECRET", "")
    # v15g4 FIX C8: v21.0 (Oct-2024) is inside Meta's ~2-year deprecation
    # window. v23.0 keeps a fresh default; ALWAYS verify the live version in
    # the Meta changelog and pin it via env before launch.
    GRAPH_API_VERSION: str      = os.getenv("GRAPH_API_VERSION", "v23.0")   # v10 / v15g4 FIX C8

    # ── Instagram Messaging API (v10) ──
    INSTAGRAM_TOKEN: str        = os.getenv("INSTAGRAM_TOKEN", "")
    INSTAGRAM_ID: str           = os.getenv("INSTAGRAM_ID", "")            # IG business account id
    INSTAGRAM_APP_SECRET: str   = os.getenv("INSTAGRAM_APP_SECRET", "")    # fallback: WHATSAPP_APP_SECRET

    # ── Redis ──
    REDIS_URL: str              = os.getenv("REDIS_URL", "")

    # ── Security ──
    ADMIN_API_KEY: str          = os.getenv("ADMIN_API_KEY", "")
    ENCRYPTION_KEY: str         = os.getenv("ENCRYPTION_KEY", "")
    # v15g2 FIX L9: unset JWT/Flask secrets used to default to a fresh uuid PER
    # PROCESS — under gunicorn -w N each worker minted its own, so admin JWTs and
    # Flask sessions broke non-deterministically across workers, and the v14g5
    # FIX 11 boot guard only fired when the WEB_CONCURRENCY env happened to be
    # set (gunicorn -w 4 without it sailed straight past). Now: if ENCRYPTION_KEY
    # exists (it must, for PII), derive a DETERMINISTIC secret from it — identical
    # in every worker — and fall back to per-process random only when there is
    # truly nothing shared to derive from. Explicit env values always win.
    SECRET_KEY: str             = (os.getenv("SECRET_KEY", "")
        or (hashlib.sha256(("heonix|flask|" + os.getenv("ENCRYPTION_KEY", ""))
                           .encode()).hexdigest()
            if os.getenv("ENCRYPTION_KEY") else uuid.uuid4().hex))
    JWT_SECRET_KEY: str         = (os.getenv("JWT_SECRET_KEY", "")
        or (hashlib.sha256(("heonix|jwt|" + os.getenv("ENCRYPTION_KEY", ""))
                           .encode()).hexdigest()
            if os.getenv("ENCRYPTION_KEY") else uuid.uuid4().hex))
    JWT_EXPIRY_HOURS: int       = _env_int("JWT_EXPIRY_HOURS", "24")

    # ── Chat ──
    CHAT_HISTORY_LIMIT: int     = _env_int("CHAT_HISTORY_LIMIT", "20")
    MAX_MESSAGE_LEN: int        = _env_int("MAX_MESSAGE_LEN", "2000")

    # ── Rate Limits ──
    RATE_LIMIT_DEFAULT: str     = os.getenv("RATE_LIMIT_DEFAULT", "200 per minute")
    WEBHOOK_RATE_LIMIT: str     = os.getenv("WEBHOOK_RATE_LIMIT", "60 per minute")
    CHAT_RATE_LIMIT: str        = os.getenv("CHAT_RATE_LIMIT",    "120 per minute")
    ADMIN_RATE_LIMIT: str       = os.getenv("ADMIN_RATE_LIMIT",   "30 per minute")

    # ── Cache ──
    CACHE_TTL: int              = _env_int("CACHE_TTL", "600")

    # ── Retry ──
    # v15g4 FIX B7: default 3 → 1. Worst case was MAX_RETRIES × AI_TIMEOUT ×
    # 3 providers ≈ minutes of a patient staring at "typing…". One retry per
    # provider + the Gemini→OpenAI→Claude fallback chain is plenty of
    # resilience. Set MAX_RETRIES=3 in env to restore the old behaviour.
    MAX_RETRIES: int            = _env_int("MAX_RETRIES", "1")
    RETRY_BASE_DELAY: float     = _env_float("RETRY_BASE_DELAY", "1.0")

    # ── Observability ──
    LOG_FORMAT: str             = os.getenv("LOG_FORMAT", "json")
    REGION: str                 = os.getenv("REGION", "ap-south-1")         # NEW v8 / v16g4 FIX L6: India default
    ENABLE_ANALYTICS: bool      = _env_bool("ENABLE_ANALYTICS", True)   # v16g4 FIX M1

    # ── Server ──
    PORT: int                   = _env_int("PORT", "5000")
    DEBUG: bool                 = _env_bool("DEBUG", False)             # v16g4 FIX M1

    # ── v10: God-Logic / RAG / Voice ──
    GHOST_MUTE_SECONDS: int     = _env_int("GHOST_MUTE_SECONDS", "900")
    RESPONSE_CACHE_TTL: int     = _env_int("RESPONSE_CACHE_TTL", "900")
    QDRANT_URL: str             = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str         = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION: str      = os.getenv("QDRANT_COLLECTION", "heonix_memory")
    EMBED_MODEL: str            = os.getenv("EMBED_MODEL", "models/gemini-embedding-001")
    EMBED_DIMS: int             = _env_int("EMBED_DIMS", "768")
    RAG_TOP_K: int              = _env_int("RAG_TOP_K", "3")
    RAG_MIN_SCORE: float        = _env_float("RAG_MIN_SCORE", "0.55")
    OPENAI_TRANSCRIBE_MODEL: str = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")

    # ══ v14 Gen-4 — ADVANCED FEATURES (every flag defaults OFF) ════════════════
    # Gen-4 is purely ADDITIVE: with all flags off, the engine behaves EXACTLY
    # like Gen-3. Turn features on one at a time, after testing each live.
    #  Appointment booking + reminders
    ENABLE_BOOKING: bool        = _env_bool("ENABLE_BOOKING", False)    # v16g4 FIX M1
    BOOKING_SLOT_MINUTES: int   = _env_int("BOOKING_SLOT_MINUTES", "30")
    BOOKING_OPEN_HOUR: int      = _env_int("BOOKING_OPEN_HOUR", "9")    # local clinic hour
    BOOKING_CLOSE_HOUR: int     = _env_int("BOOKING_CLOSE_HOUR", "18")  # local clinic hour
    BOOKING_DAYS_AHEAD: int     = _env_int("BOOKING_DAYS_AHEAD", "5")
    BOOKING_SLOTS_SHOWN: int    = _env_int("BOOKING_SLOTS_SHOWN", "6")
    BOOKING_TZ_OFFSET_MIN: int  = _env_int("BOOKING_TZ_OFFSET_MIN", "330")  # IST +5:30
    BOOKING_WEEKDAYS: str       = os.getenv("BOOKING_WEEKDAYS", "0,1,2,3,4,5")     # Mon=0..Sun=6
    #  Background scheduler (reminders / follow-ups / retention) — needs a
    #  long-lived process (true on Render web service; NOT on serverless).
    ENABLE_SCHEDULER: bool      = _env_bool("ENABLE_SCHEDULER", False)  # v16g4 FIX M1
    REMINDER_LEAD_HOURS: str    = os.getenv("REMINDER_LEAD_HOURS", "24,2")         # csv hours-before
    FOLLOWUP_ENABLED: bool      = _env_bool("FOLLOWUP_ENABLED", False)  # v16g4 FIX M1
    FOLLOWUP_AFTER_HOURS: int   = _env_int("FOLLOWUP_AFTER_HOURS", "24")
    FOLLOWUP_MAX_AGE_HOURS: int = _env_int("FOLLOWUP_MAX_AGE_HOURS", "168")  # don't chase >7d-old
    DATA_RETENTION_DAYS: int    = _env_int("DATA_RETENTION_DAYS", "0")       # 0 = keep forever
    #  Image understanding (uses your existing Gemini key — already multimodal)
    ENABLE_IMAGE_UNDERSTANDING: bool = _env_bool("ENABLE_IMAGE_UNDERSTANDING", False)  # v16g4 FIX M1
    #  Scheduled sends (reminders/follow-ups) outside WhatsApp's 24-hour customer
    #  service window REQUIRE a pre-approved template. If you set these to an
    #  approved template name, the scheduler sends via template (reliable). If
    #  left blank, it sends free text — which Meta only delivers INSIDE 24h.
    REMINDER_TEMPLATE: str      = os.getenv("REMINDER_TEMPLATE", "")
    REMINDER_TEMPLATE_LANG: str = os.getenv("REMINDER_TEMPLATE_LANG", "en")
    FOLLOWUP_TEMPLATE: str      = os.getenv("FOLLOWUP_TEMPLATE", "")
    FOLLOWUP_TEMPLATE_LANG: str = os.getenv("FOLLOWUP_TEMPLATE_LANG", "en")

    # ── v11 ──
    # #4: free-form WhatsApp texts to the OWNER are blocked by Meta outside
    # the 24-hour window (error 131047) — an emergency alert could silently
    # die. Create ONE approved utility template with a single {{1}} body
    # parameter (e.g. name it "heonix_owner_alert", body: "{{1}}") and set:
    OWNER_ALERT_TEMPLATE: str      = os.getenv("OWNER_ALERT_TEMPLATE", "")
    OWNER_ALERT_TEMPLATE_LANG: str = os.getenv("OWNER_ALERT_TEMPLATE_LANG", "en")
    # #2: set STRICT_PROD=1 to REFUSE booting without Postgres + Redis
    # (recommended once live — prevents the silent SQLite/in-process fallback
    # that breaks dedupe + ghost-mute across gunicorn workers).
    STRICT_PROD: bool              = _env_bool("STRICT_PROD", False)       # v16g4 FIX M1
    # v16g5 FIX R5-M11: promoted out of a raw per-import os.getenv into cfg,
    # like every other setting. Comma-separated origins; empty = dev wildcard
    # (refused under STRICT_PROD).
    CORS_ORIGINS: str              = os.getenv("CORS_ORIGINS", "").strip()

    # ── v12 ── (hyper-scale / concurrency hardening)
    # JSON-bomb guard (#37): reject oversized request bodies before they hit RAM.
    MAX_CONTENT_BYTES: int         = _env_int("MAX_CONTENT_BYTES", 1 * 1024 * 1024)  # 1 MB
    # RAM-nuke guard (#7/#16): never pull a media file bigger than this into memory.
    MEDIA_MAX_BYTES: int           = _env_int("MEDIA_MAX_BYTES", 16 * 1024 * 1024)  # 16 MB
    # Network timeouts as (connect, read) tuples (#39): a frozen socket can no
    # longer pin a background thread forever.
    HTTP_CONNECT_TIMEOUT: float    = _env_float("HTTP_CONNECT_TIMEOUT", "5")
    MEDIA_READ_TIMEOUT: float      = _env_float("MEDIA_READ_TIMEOUT", "30")
    # RAG soft timeout (#9/#23): embedding + vector search are bounded so Qdrant
    # or the embedding endpoint hanging can't wedge the whole reply path.
    RAG_TIMEOUT_SECS: float        = _env_float("RAG_TIMEOUT_SECS", "6")
    # Pool-explosion guard (#34): workers × MAX_POOL_SIZE must stay under the
    # database's own connection ceiling. Render free Postgres ~= 97; leave headroom.
    DB_MAX_CONNECTIONS: int        = _env_int("DB_MAX_CONNECTIONS", "90")
    WEB_CONCURRENCY: int           = _env_int("WEB_CONCURRENCY", "1")
    # Meta send retries (#36): only transient/5xx/429 are retried (see _meta_send_retry).
    META_SEND_RETRIES: int         = _env_int("META_SEND_RETRIES", "2")
    # /metrics COUNT(*) cache (#10): a Prometheus scrape storm can't hammer the DB.
    METRICS_CACHE_TTL: int         = _env_int("METRICS_CACHE_TTL", "30")

    # ── v13 ── (TRUE MULTI-TENANT — per-clinic creds, token-death self-heal)
    # When a clinic's own WhatsApp/Instagram token dies (Meta code 190/401), the
    # engine flags that clinic needs_reauth and pings THIS number so you re-attach
    # before the clinic notices. Uses the GLOBAL token to send the alert.
    ADMIN_ALERT_PHONE: str         = os.getenv("ADMIN_ALERT_PHONE", "")
    # Routing cache TTL for phone_number_id → brain (seconds). 10 min is plenty;
    # channel edits bust the key immediately, so staleness is bounded.
    ROUTE_CACHE_TTL: int           = _env_int("ROUTE_CACHE_TTL", "600")
    # Allow the onboarding smoke-test endpoint to send ONE real test WhatsApp to a
    # number you pass in. Off by default so it can never be abused to fan out spam.
    # v15 FIX 12: this comment always said "off by default" — the code said ON.
    # Now they agree. ⚠️ Set SMOKE_TEST_ENABLED=1 in Render env — you USE this.
    SMOKE_TEST_ENABLED: bool       = _env_bool("SMOKE_TEST_ENABLED", False)  # v16g4 FIX M1

    # ── v14 Gen-3 ── (hardening pass — see the CHANGELOG header at top of file)
    # BUG 7: force webhook signature verification even when STRICT_PROD is off.
    REQUIRE_WEBHOOK_SIGNATURE: bool = _env_bool("REQUIRE_WEBHOOK_SIGNATURE", False)  # v16g4 FIX M1
    # BUG 14: the audit trail no longer rides on ENABLE_ANALYTICS — its own switch
    # so you can mute metrics without silently losing the SOC2/GDPR audit log.
    ENABLE_AUDIT: bool             = _env_bool("ENABLE_AUDIT", True)     # v16g4 FIX M1
    # BUG 11: country code assumed for a bare 10-digit national number (India=91)
    # when minting the stable customer_id, so +1 / +44 / … can't collide on the
    # last 10 digits and overwrite each other's brain.
    DEFAULT_COUNTRY_CODE: str      = os.getenv("DEFAULT_COUNTRY_CODE", "91")

    # ── v14 Gen-5 ── (audit fixes — 50 findings closed; see header)
    # FIX 35: a separate Instagram webhook verify token (falls back to the WA one).
    INSTAGRAM_VERIFY_TOKEN: str    = (os.getenv("INSTAGRAM_VERIFY_TOKEN", "")
                                      or os.getenv("WHATSAPP_VERIFY_TOKEN", "heonix_verify"))
    # FIX 23: optional token to gate /metrics so counts aren't public recon.
    METRICS_TOKEN: str             = os.getenv("METRICS_TOKEN", "")
    # FIX 10: gate the "route any unknown number to the only clinic" guess.
    SINGLE_TENANT_FALLBACK: bool   = _env_bool("SINGLE_TENANT_FALLBACK", True)  # v16g4 FIX M1
    # FIX 6: cross-worker per-conversation mutex TTL (must exceed a slow AI turn).
    CONV_LOCK_TTL: int             = _env_int("CONV_LOCK_TTL", "60")
    # FIX 7: single-leader scheduler lock TTL (~ the 5-min cadence, just under it).
    SCHED_LOCK_TTL: int            = _env_int("SCHED_LOCK_TTL", "290")

    # ── v15 ── (26-finding independent audit close-out; see header changelog)
    # FIX 5: optional API key for POST /chat. customer_id is derivable from a
    # clinic's PUBLIC WhatsApp number ("HX_WA_" + digits), so an open /chat
    # lets anyone burn your Gemini quota and probe the persona. Unset = open
    # (dev) with a loud startup warning; STRICT_PROD fail-closes the endpoint.
    CHAT_API_KEY: str              = os.getenv("CHAT_API_KEY", "")

    # ── v15 Gen-4 ── (round-4 launch-readiness audit; see header changelog)
    # FIX A4: a keyword "talk to doctor/manager" request muted the AI for the
    # full GHOST_MUTE_SECONDS (15 min) — at a clinic that phrase is routine,
    # so the bot went dark constantly. Keyword-based handoffs now use this
    # shorter lease; the AI-escalation path keeps the full ghost mute.
    HUMAN_REQUEST_MUTE_SECONDS: int = _env_int("HUMAN_REQUEST_MUTE_SECONDS", "300")
    # FIX B9: wamid/igmid dedupe claims lived only 600s — a Meta redelivery
    # later than that was reprocessed and DOUBLE-replied. 6h default.
    DEDUPE_TTL_SECONDS: int         = _env_int("DEDUPE_TTL_SECONDS", "21600")
    # FIX D2: how long a drain waits for the cross-worker conversation lease
    # before proceeding without it (documented interleave tradeoff).
    CONV_LOCK_WAIT_SECS: float      = _env_float("CONV_LOCK_WAIT_SECS", "5")

    # ── v16 ── WhatsApp Usernames / BSUID (see header changelog)
    # U3: when a username-only patient books, ask once for their real number
    # (reminders + clinic records). Set 0 to disable the ask entirely —
    # BSUID-addressed sends still work either way.
    ENABLE_PHONE_CAPTURE: bool      = _env_bool("ENABLE_PHONE_CAPTURE", True)  # v16g4 FIX M1
    # U3: the interactive request-button type/action strings. Defaults follow
    # Meta's location_request_message naming pattern; VERIFY against the
    # current Cloud API docs when the button GAs in your region — a mismatch
    # is harmless (the send 400s and the engine falls back to a plain-text
    # ask; typed-number capture handles the reply either way).
    WA_PHONE_REQUEST_TYPE: str      = os.getenv("WA_PHONE_REQUEST_TYPE",
                                                "phone_number_request_message")
    WA_PHONE_REQUEST_ACTION: str    = os.getenv("WA_PHONE_REQUEST_ACTION",
                                                "send_phone_number")

    # ── v16 Gen-4 ── (round-4 audit close-out — 50 findings; see header)
    # FIX L8: TALLY_WEBHOOK_SECRET was the one config value read via a raw
    # os.getenv per request inside verify_tally_signature — now it lives in
    # cfg like every other secret (and the boot summary can see it: FIX H4).
    TALLY_WEBHOOK_SECRET: str       = os.getenv("TALLY_WEBHOOK_SECRET", "")
    # FIX H1: the onboarding welcome is BUSINESS-INITIATED — the clinic owner
    # has never messaged the WABA line, so free text is rejected by Meta 100%
    # of the time (131047-class: no open 24h session). The welcome MUST go via
    # a pre-approved template. Create one utility template with a single {{1}}
    # body parameter (suggested name "heonix_welcome", body: "{{1}}"), get it
    # approved in Meta Business Manager, then set:
    WELCOME_TEMPLATE: str           = os.getenv("WELCOME_TEMPLATE", "")
    WELCOME_TEMPLATE_LANG: str      = os.getenv("WELCOME_TEMPLATE_LANG", "en")
    # FIX M13: ADMIN_API_KEY is a permanent, unrotatable env superadmin. In
    # STRICT_PROD it is now refused unless you explicitly acknowledge the risk
    # with ADMIN_API_KEY_LEGACY_OK=1 (JWT admin login is the supported path).
    ADMIN_API_KEY_LEGACY_OK: bool   = _env_bool("ADMIN_API_KEY_LEGACY_OK", False)
    # FIX M8: default language for system-authored strings (booking prompts,
    # phone request, cancel confirms) when the patient's own script can't be
    # detected. Per-message detection still wins; this is only the fallback.
    DEFAULT_LANG: str               = os.getenv("DEFAULT_LANG", "en")


cfg = Config()

# v16g4 FIX L7: the detailed build banner — shown only to DEBUG or a caller
# holding METRICS_TOKEN; the anonymous landing page says just "HEONIX".
# v16g6 FIX R6-L1: FOUR version identities lived in one build (this banner
# said GEN-4, /health said GEN-3, the shutdown log said GEN-3, the startup
# banner said GEN-5). After a hotfix night, /health is the one thing that
# must be trusted to say which build is live. One constant; all derive.
ENGINE_VERSION = "v16.1"
ENGINE_GEN     = "GEN-6"
ENGINE_BANNER  = (f"HEONIX ULTRA ENGINE {ENGINE_VERSION} {ENGINE_GEN} "
                  f"(Usernames/BSUID · 178 audit fixes)")
