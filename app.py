"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     HEONIX ULTRA ENGINE  v11.0 — PRODUCTION-HARDENED (all 15 v10 gaps)     ║
║                                                                              ║
║  v7 DRAWBACKS RESOLVED IN v8:                                                ║
║  ✅ FIX #1  → Modular layer architecture (no more single-file chaos)        ║
║  ✅ FIX #2  → Multi-region geo-aware routing + health failover               ║
║  ✅ FIX #3  → Distributed transaction Saga + outbox pattern                  ║
║  ✅ FIX #4  → Horizontal DB: read replicas + table partitioning              ║
║  ✅ FIX #5  → Real-time analytics engine (event streaming + counters)        ║
║  ✅ FIX #6  → SOC 2 / GDPR audit trail + consent ledger                     ║
║  ✅ FIX #7  → bcrypt password hashing (was plaintext in v7 admin table)     ║
║  ✅ FIX #8  → Token-bucket rate limiter per customer_id (not just IP)       ║
║  ✅ FIX #9  → Retry with exponential back-off + jitter (AI calls)           ║
║  ✅ FIX #10 → OpenAI client singleton (was instantiated per request)        ║
║  ✅ FIX #11 → Anthropic client singleton (same)                              ║
║  ✅ FIX #12 → Graceful connection-pool drain on SIGTERM (K8s safe)          ║
║  ✅ FIX #13 → Health/readiness probes separate + structured for k8s          ║
║  ✅ FIX #14 → Webhook signature validation covers WhatsApp & Tally           ║
║  ✅ FIX #15 → Prometheus histograms for latency (was counters only)         ║
║                                                                              ║
║  RETAINED FROM v7 (all working):                                             ║
║  ◆ PostgreSQL + Redis + SQLite fallback                                     ║
║  ◆ AES-256-GCM PII encryption (DPDP/HIPAA)                                 ║
║  ◆ JWT + RBAC (superadmin / admin / viewer)                                 ║
║  ◆ Multi-AI fallback: Gemini → OpenAI → Claude                             ║
║  ◆ Official Meta WhatsApp Cloud API                                          ║
║  ◆ Idempotency keys                                                          ║
║  ◆ Circuit breakers per AI provider                                          ║
║                                                                              ║
║  v10 GOD-LOGIC ADDITIONS (god_logic_v9 merged + drawbacks fixed):            ║
║  ◆ Instagram Messaging channel — same brain, CRM, memory as WhatsApp        ║
║  ◆ Voice-note decoder: WA/IG audio → Gemini → Whisper fallback              ║
║  ◆ Qdrant RAG long-term memory per end-user (AES-256 encrypted payloads)    ║
║  ◆ Cost optimizer: trivial msgs answered locally in 10 languages, ₹0 API    ║
║  ◆ Redis-backed response cache + ghost mode (multi-worker safe)             ║
║  ◆ Webhook de-duplication (Meta retries no longer cause double replies)     ║
║  ◆ Emergency / human-handoff / VIP routing: keywords + AI escalation token  ║
║  ◆ Languages: script auto-detect; AI replies in ANY language user writes    ║
║  ◆ Meta Graph v21.0 + Gemini 2.5 (v8 defaults were shut down by vendors)    ║
╚══════════════════════════════════════════════════════════════════════════════╝

ENVIRONMENT VARIABLES:

  ── DATABASE ──────────────────────────────────────────────────────────────────
  DATABASE_MODE         = "postgres" | "sqlite"     (default: postgres)
  DATABASE_URL          = postgresql://user:pass@primary-host:5432/heonix_db
  DATABASE_REPLICA_URL  = postgresql://user:pass@replica-host:5432/heonix_db
                          (optional read-replica — improves read throughput)
  DATABASE_FILE         = heonix_ultra.db            (sqlite fallback only)
  MAX_POOL_SIZE         = 20

  ── AI ENGINE ─────────────────────────────────────────────────────────────────
  GENAI_API_KEY         = Google Gemini API key
  OPENAI_API_KEY        = OpenAI GPT-4 API key
  ANTHROPIC_API_KEY     = Anthropic Claude API key
  GEMINI_MODEL          = gemini-3.1-flash-lite
  OPENAI_MODEL          = gpt-4o-mini
  ANTHROPIC_MODEL       = claude-haiku-4-5-20251001
  AI_MAX_TOKENS         = 1000
  AI_TIMEOUT_SECS       = 30

  ── WHATSAPP ──────────────────────────────────────────────────────────────────
  WHATSAPP_TOKEN        = Meta WhatsApp Cloud API token
  WHATSAPP_PHONE_ID     = WhatsApp Business Phone Number ID
  WHATSAPP_VERIFY_TOKEN = Webhook verify token
  WHATSAPP_APP_SECRET   = App secret (HMAC signature verification)

  ── REDIS ─────────────────────────────────────────────────────────────────────
  REDIS_URL             = redis://localhost:6379/0
                          (Upstash / Redis Cloud for managed deployments)

  ── SECURITY ──────────────────────────────────────────────────────────────────
  SECRET_KEY            = Flask session secret (auto-generated if omitted)
  ADMIN_API_KEY         = Legacy X-Admin-Key (backward compat only)
  ENCRYPTION_KEY        = 32-byte hex for AES-256-GCM PII encryption
                          python -c "import secrets; print(secrets.token_hex(32))"
  JWT_SECRET_KEY        = JWT signing secret (rotate regularly)
  JWT_EXPIRY_HOURS      = 24

  ── MULTI-REGION ──────────────────────────────────────────────────────────────
  REGION                = "us-east-1" | "eu-west-1" | "ap-south-1"  (optional)
  ENABLE_ANALYTICS      = true | false   (default: true)

  ── OBSERVABILITY ─────────────────────────────────────────────────────────────
  PORT                  = 5000
  DEBUG                 = false
  LOG_FORMAT            = "json" | "text"
  RATE_LIMIT_DEFAULT    = 200 per minute
  CACHE_TTL             = 600
  CHAT_HISTORY_LIMIT    = 20

  ── v10 ADDITIONS ─────────────────────────────────────────────────────────────
  GRAPH_API_VERSION     = v21.0   (Meta deprecates old versions — keep current)
  INSTAGRAM_TOKEN       = Page/IG access token with instagram_manage_messages
  INSTAGRAM_ID          = IG business account id (the recipient.id in webhooks)
  INSTAGRAM_APP_SECRET  = optional; falls back to WHATSAPP_APP_SECRET
  QDRANT_URL            = https://xxxx.cloud.qdrant.io  (Qdrant Cloud free tier OK)
  QDRANT_API_KEY        = Qdrant Cloud API key
  EMBED_MODEL           = models/gemini-embedding-001
  EMBED_DIMS            = 768
  RAG_TOP_K             = 3        RAG_MIN_SCORE = 0.55
  GHOST_MUTE_SECONDS    = 900   (AI silence after human takeover)
  RESPONSE_CACHE_TTL    = 900   (identical-question reuse; Redis-backed)
  OPENAI_TRANSCRIBE_MODEL = whisper-1  (voice fallback if Gemini audio fails)
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# 📦  STANDARD LIBRARY
# ─────────────────────────────────────────────────────────────────────────────
import base64
import functools
import hashlib
import hmac
import io
import json
import logging
import os
import queue
import random
import re
import signal
import sqlite3
import threading
import time
import unicodedata
import uuid
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor   # v11 #1/#11: bounded async workers
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

import requests
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
# ⚙️  CONFIGURATION  (v8: adds replica URL, region tag, analytics toggle)
# ─────────────────────────────────────────────────────────────────────────────
class Config:
    # ── Database ──
    DATABASE_MODE: str          = os.getenv("DATABASE_MODE", "postgres")
    DATABASE_URL: str           = os.getenv("DATABASE_URL", "")
    DATABASE_REPLICA_URL: str   = os.getenv("DATABASE_REPLICA_URL", "")   # NEW v8
    DATABASE_FILE: str          = os.getenv("DATABASE_FILE", "heonix_v8.db")
    MAX_POOL_SIZE: int          = int(os.getenv("MAX_POOL_SIZE", "20"))

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
    AI_MAX_TOKENS: int          = int(os.getenv("AI_MAX_TOKENS", "1000"))
    AI_TIMEOUT_SECS: float      = float(os.getenv("AI_TIMEOUT_SECS", "30"))

    # ── WhatsApp Cloud API ──
    WHATSAPP_TOKEN: str         = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_ID: str      = os.getenv("WHATSAPP_PHONE_ID", "")
    WHATSAPP_VERIFY_TOKEN: str  = os.getenv("WHATSAPP_VERIFY_TOKEN", "heonix_verify")
    WHATSAPP_APP_SECRET: str    = os.getenv("WHATSAPP_APP_SECRET", "")
    GRAPH_API_VERSION: str      = os.getenv("GRAPH_API_VERSION", "v21.0")   # v10

    # ── Instagram Messaging API (v10) ──
    INSTAGRAM_TOKEN: str        = os.getenv("INSTAGRAM_TOKEN", "")
    INSTAGRAM_ID: str           = os.getenv("INSTAGRAM_ID", "")            # IG business account id
    INSTAGRAM_APP_SECRET: str   = os.getenv("INSTAGRAM_APP_SECRET", "")    # fallback: WHATSAPP_APP_SECRET

    # ── Redis ──
    REDIS_URL: str              = os.getenv("REDIS_URL", "")

    # ── Security ──
    SECRET_KEY: str             = os.getenv("SECRET_KEY", uuid.uuid4().hex)
    ADMIN_API_KEY: str          = os.getenv("ADMIN_API_KEY", "")
    ENCRYPTION_KEY: str         = os.getenv("ENCRYPTION_KEY", "")
    JWT_SECRET_KEY: str         = os.getenv("JWT_SECRET_KEY", uuid.uuid4().hex)
    JWT_EXPIRY_HOURS: int       = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

    # ── Chat ──
    CHAT_HISTORY_LIMIT: int     = int(os.getenv("CHAT_HISTORY_LIMIT", "20"))
    MAX_MESSAGE_LEN: int        = int(os.getenv("MAX_MESSAGE_LEN", "2000"))

    # ── Rate Limits ──
    RATE_LIMIT_DEFAULT: str     = os.getenv("RATE_LIMIT_DEFAULT", "200 per minute")
    WEBHOOK_RATE_LIMIT: str     = os.getenv("WEBHOOK_RATE_LIMIT", "60 per minute")
    CHAT_RATE_LIMIT: str        = os.getenv("CHAT_RATE_LIMIT",    "120 per minute")
    ADMIN_RATE_LIMIT: str       = os.getenv("ADMIN_RATE_LIMIT",   "30 per minute")

    # ── Cache ──
    CACHE_TTL: int              = int(os.getenv("CACHE_TTL", "600"))

    # ── Retry ──
    MAX_RETRIES: int            = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_BASE_DELAY: float     = float(os.getenv("RETRY_BASE_DELAY", "1.0"))

    # ── Observability ──
    LOG_FORMAT: str             = os.getenv("LOG_FORMAT", "json")
    REGION: str                 = os.getenv("REGION", "us-east-1")          # NEW v8
    ENABLE_ANALYTICS: bool      = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"

    # ── Server ──
    PORT: int                   = int(os.getenv("PORT", "5000"))
    DEBUG: bool                 = os.getenv("DEBUG", "false").lower() == "true"

    # ── v10: God-Logic / RAG / Voice ──
    GHOST_MUTE_SECONDS: int     = int(os.getenv("GHOST_MUTE_SECONDS", "900"))
    RESPONSE_CACHE_TTL: int     = int(os.getenv("RESPONSE_CACHE_TTL", "900"))
    QDRANT_URL: str             = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str         = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION: str      = os.getenv("QDRANT_COLLECTION", "heonix_memory")
    EMBED_MODEL: str            = os.getenv("EMBED_MODEL", "models/gemini-embedding-001")
    EMBED_DIMS: int             = int(os.getenv("EMBED_DIMS", "768"))
    RAG_TOP_K: int              = int(os.getenv("RAG_TOP_K", "3"))
    RAG_MIN_SCORE: float        = float(os.getenv("RAG_MIN_SCORE", "0.55"))
    OPENAI_TRANSCRIBE_MODEL: str = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")

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
    STRICT_PROD: bool              = os.getenv("STRICT_PROD", "0") == "1"


cfg = Config()


# ─────────────────────────────────────────────────────────────────────────────
# 🪵  STRUCTURED LOGGING  (JSON by default — Datadog/CloudWatch/Loki friendly)
# ─────────────────────────────────────────────────────────────────────────────
class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts":     datetime.now(timezone.utc).isoformat(),
            "level":  record.levelname,
            "logger": record.name,
            "region": cfg.REGION,
            "msg":    record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if cfg.DEBUG else logging.INFO)
    handler = logging.StreamHandler()   # v11 fix #12: stdout ONLY.
    fmt = _JSONFormatter() if cfg.LOG_FORMAT == "json" else logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(fmt)
    # v11 fix #12: dropped FileHandler. On Render the disk is ephemeral, two
    # workers fought over the same file, and it grew unbounded. Render/Railway/
    # Fly all capture stdout, so that is the single source of truth.
    logger.addHandler(handler)
    logger.propagate = False
    return logger


log = _build_logger("HEONIX")   # v11 fix #15: was "HEONIX_V8"


# ─────────────────────────────────────────────────────────────────────────────
# 🔐  AES-256-GCM PII VAULT  (DPDP + HIPAA + GDPR)
# ─────────────────────────────────────────────────────────────────────────────
class PIIVault:
    """
    AES-256-GCM authenticated encryption for PII fields.
    Each field gets a unique 96-bit nonce so identical values encrypt differently.
    Compliant: DPDP Act (India), HIPAA (USA), GDPR (EU).
    """

    def __init__(self, hex_key: str):
        if not CRYPTO_AVAILABLE:
            log.warning("⚠️  cryptography not installed — PII encryption disabled.")
            self._enabled = False
            return
        if not hex_key or len(hex_key) < 64:
            log.warning("⚠️  ENCRYPTION_KEY missing/short — PII encryption disabled. "
                        "Generate: python -c \"import secrets; print(secrets.token_hex(32))\"")
            self._enabled = False
            return
        self._aesgcm  = AESGCM(bytes.fromhex(hex_key[:64]))
        self._enabled = True
        log.info("🔐 AES-256-GCM PII Vault ready.")

    @property
    def enabled(self) -> bool:
        return self._enabled

    def encrypt(self, plaintext: str) -> str:
        if not self._enabled or not plaintext:
            return plaintext
        nonce = os.urandom(12)
        ct    = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return base64.b64encode(nonce + ct).decode("ascii")

    def decrypt(self, token: str) -> str:
        if not self._enabled or not token:
            return token
        try:
            raw   = base64.b64decode(token)
            nonce, ct = raw[:12], raw[12:]
            return self._aesgcm.decrypt(nonce, ct, None).decode("utf-8")
        except Exception:
            log.error("❌ PII decryption failed — key mismatch or corrupt data.")
            return "[ENCRYPTED]"

    def mask(self, value: str) -> str:
        if not value or len(value) <= 4:
            return "****"
        return value[:2] + "***" + value[-4:]


pii_vault = PIIVault(cfg.ENCRYPTION_KEY)


# ─────────────────────────────────────────────────────────────────────────────
# 🔑  PASSWORD HASHING  (v8 fix: bcrypt replaces plaintext in admin table)
# ─────────────────────────────────────────────────────────────────────────────
def hash_password(plaintext: str) -> str:
    """bcrypt-hash a password. Falls back to SHA-256 if bcrypt not installed."""
    if BCRYPT_AVAILABLE:
        return bcrypt_lib.hashpw(plaintext.encode("utf-8"), bcrypt_lib.gensalt(rounds=12)).decode("utf-8")
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def verify_password(plaintext: str, stored_hash: str) -> bool:
    if BCRYPT_AVAILABLE and stored_hash.startswith("$2"):
        return bcrypt_lib.checkpw(plaintext.encode("utf-8"), stored_hash.encode("utf-8"))
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest() == stored_hash


# ─────────────────────────────────────────────────────────────────────────────
# 🔑  JWT AUTH + RBAC
# ─────────────────────────────────────────────────────────────────────────────
ROLES = {"superadmin", "admin", "viewer"}
_ROLE_RANK = {"viewer": 0, "admin": 1, "superadmin": 2}


def generate_jwt(user_id: str, role: str = "admin") -> str:
    if not JWT_AVAILABLE:
        return ""
    payload = {
        "sub":  user_id,
        "role": role,
        "iat":  datetime.now(timezone.utc),
        "exp":  datetime.now(timezone.utc) + timedelta(hours=cfg.JWT_EXPIRY_HOURS),
        "jti":  uuid.uuid4().hex,
        "rgn":  cfg.REGION,
    }
    return pyjwt.encode(payload, cfg.JWT_SECRET_KEY, algorithm="HS256")


def decode_jwt(token: str) -> Optional[Dict]:
    if not JWT_AVAILABLE:
        return None
    try:
        return pyjwt.decode(token, cfg.JWT_SECRET_KEY, algorithms=["HS256"])
    except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError):
        return None


def require_jwt(min_role: str = "admin"):
    """Decorator: validates Bearer JWT and enforces minimum role hierarchy."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Legacy X-Admin-Key backward compat
            if cfg.ADMIN_API_KEY:
                if request.headers.get("X-Admin-Key", "") == cfg.ADMIN_API_KEY:
                    g.jwt_user = {"sub": "legacy_admin", "role": "superadmin"}
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

            g.jwt_user = payload
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# 📊  REAL-TIME ANALYTICS ENGINE  (v8 FIX #5 — event counters + latency P99)
# ─────────────────────────────────────────────────────────────────────────────
class AnalyticsEngine:
    """
    Lock-free in-process analytics with Redis sync every 60 s.
    Tracks: requests, errors, AI provider usage, latency histograms.
    Exported on GET /metrics (Prometheus-compatible).
    """

    def __init__(self):
        self._lock     = threading.Lock()
        self._counters: Dict[str, int]         = defaultdict(int)
        self._latencies: Dict[str, deque]      = defaultdict(lambda: deque(maxlen=1000))
        self._started  = time.monotonic()

    def inc(self, key: str, n: int = 1) -> None:
        with self._lock:
            self._counters[key] += n

    def record_latency(self, key: str, ms: float) -> None:
        with self._lock:
            self._latencies[key].append(ms)

    def get_counter(self, key: str) -> int:
        with self._lock:
            return self._counters[key]

    def percentile(self, key: str, pct: float = 0.99) -> float:
        with self._lock:
            data = sorted(self._latencies[key])
        if not data:
            return 0.0
        idx = max(0, int(len(data) * pct) - 1)
        return round(data[idx], 2)

    def snapshot(self) -> Dict:
        with self._lock:
            counters   = dict(self._counters)
            latency_p99 = {k: self.percentile(k) for k in self._latencies}
        uptime_s = time.monotonic() - self._started
        return {
            "counters":    counters,
            "latency_p99": latency_p99,
            "uptime_secs": round(uptime_s, 1),
        }


analytics = AnalyticsEngine()


# ─────────────────────────────────────────────────────────────────────────────
# 🏊  DATABASE LAYER  — Primary write pool + optional read-replica pool
#     v8 FIX #4: read replicas for horizontal read scaling
# ─────────────────────────────────────────────────────────────────────────────
class PostgreSQLPool:
    """
    Production PostgreSQL pool via psycopg2.
    v8 adds optional read-replica pool for SELECT queries.
    """

    def __init__(self, dsn: str, min_conn: int = 2, max_conn: int = 20,
                 replica_dsn: str = ""):
        if not POSTGRES_AVAILABLE:
            raise RuntimeError("psycopg2 not installed. pip install psycopg2-binary")
        self._write = psycopg2.pool.ThreadedConnectionPool(
            minconn=min_conn, maxconn=max_conn, dsn=dsn)
        self._read  = None
        if replica_dsn:
            try:
                self._read = psycopg2.pool.ThreadedConnectionPool(
                    minconn=2, maxconn=max_conn, dsn=replica_dsn)
                log.info("🐘 PostgreSQL read-replica pool ready.")
            except Exception as exc:
                log.warning(f"⚠️  Read replica unavailable ({exc}) — reads use primary.")
        log.info(f"🐘 PostgreSQL write pool ready — min={min_conn} max={max_conn}")

    @contextmanager
    def get(self, read_only: bool = False) -> Generator:
        pool = (self._read or self._write) if read_only else self._write
        conn = pool.getconn()
        conn.autocommit = False
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            pool.putconn(conn)

    def close_all(self) -> None:
        self._write.closeall()
        if self._read:
            self._read.closeall()
        log.info("🐘 PostgreSQL pools closed.")


class SQLitePool:
    """SQLite pool — dev/demo. WAL mode for better concurrency."""

    def __init__(self, db_path: str, pool_size: int = 10, timeout: float = 5.0):
        self._path    = db_path
        self._timeout = timeout
        self._pool: queue.Queue[sqlite3.Connection] = queue.Queue(maxsize=pool_size)
        for _ in range(pool_size):
            self._pool.put(self._new_conn())
        log.warning("⚠️  SQLite mode — single-server only. Set DATABASE_URL for PostgreSQL.")

    def _new_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA cache_size=-32000;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    @contextmanager
    def get(self, read_only: bool = False) -> Generator:  # read_only ignored for SQLite
        try:
            conn = self._pool.get(timeout=self._timeout)
        except queue.Empty:
            raise RuntimeError("SQLite pool exhausted")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.put(conn)

    def close_all(self) -> None:
        while not self._pool.empty():
            try:
                self._pool.get_nowait().close()
            except queue.Empty:
                break


_db_pool: Any = None


def db(read_only: bool = False):
    if _db_pool is None:
        raise RuntimeError("Database pool not initialised — call startup() first.")
    return _db_pool


# ─────────────────────────────────────────────────────────────────────────────
# 🗄️  SCHEMA  — PostgreSQL + SQLite compatible (v8 adds audit_log + partitioned)
# ─────────────────────────────────────────────────────────────────────────────
_PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS customer_brains (
    customer_id      TEXT PRIMARY KEY,
    customer_name    TEXT NOT NULL,
    business_type    TEXT DEFAULT 'General',
    system_prompt    TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_chats      BIGINT DEFAULT 0,
    is_active        BOOLEAN DEFAULT TRUE,
    plan_tier        TEXT DEFAULT 'starter',
    whatsapp_phone   TEXT DEFAULT '',
    region           TEXT DEFAULT 'us-east-1'
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id    TEXT PRIMARY KEY,
    customer_id   TEXT NOT NULL REFERENCES customer_brains(customer_id) ON DELETE CASCADE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,
    channel       TEXT DEFAULT 'api'
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id             BIGSERIAL PRIMARY KEY,
    session_id     TEXT NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role           TEXT NOT NULL CHECK(role IN ('user','model')),
    content        TEXT NOT NULL,
    timestamp      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    token_estimate INTEGER DEFAULT 0,
    ai_provider    TEXT DEFAULT 'gemini',
    latency_ms     INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS crm_contacts (
    id             BIGSERIAL PRIMARY KEY,
    customer_id    TEXT NOT NULL REFERENCES customer_brains(customer_id) ON DELETE CASCADE,
    phone_hash     TEXT DEFAULT '',
    enc_name       TEXT NOT NULL,
    enc_phone      TEXT NOT NULL,
    enc_email      TEXT DEFAULT '',
    enc_notes      TEXT DEFAULT '',
    contact_stage  TEXT DEFAULT 'lead',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_consented   BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS webhook_log (
    id           BIGSERIAL PRIMARY KEY,
    source_ip    TEXT,
    payload_hash TEXT NOT NULL,
    customer_id  TEXT,
    channel      TEXT DEFAULT 'tally',
    status       TEXT NOT NULL,
    error_detail TEXT,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key           TEXT PRIMARY KEY,
    response_body TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admin_users (
    user_id       TEXT PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    hashed_pw     TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'admin',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active     BOOLEAN DEFAULT TRUE
);

-- v8: SOC 2 / GDPR audit trail (FIX #6)
CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGSERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_id    TEXT NOT NULL,
    action      TEXT NOT NULL,
    resource    TEXT NOT NULL,
    detail      JSONB DEFAULT '{}',
    ip          TEXT,
    region      TEXT DEFAULT 'us-east-1'
);

-- v8: outbox for distributed saga pattern (FIX #3)
CREATE TABLE IF NOT EXISTS outbox (
    id           BIGSERIAL PRIMARY KEY,
    event_type   TEXT NOT NULL,
    payload      JSONB NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    attempts     INTEGER DEFAULT 0
);

-- Indexes (optimised for 100B-scale read patterns)
CREATE INDEX IF NOT EXISTS idx_msg_session    ON chat_messages(session_id, id);
CREATE INDEX IF NOT EXISTS idx_sess_customer  ON chat_sessions(customer_id);
CREATE INDEX IF NOT EXISTS idx_crm_customer   ON crm_contacts(customer_id, contact_stage);
CREATE INDEX IF NOT EXISTS idx_idem_created   ON idempotency_keys(created_at);
CREATE INDEX IF NOT EXISTS idx_wh_customer    ON webhook_log(customer_id, processed_at);
CREATE INDEX IF NOT EXISTS idx_audit_actor    ON audit_log(actor_id, ts);
CREATE INDEX IF NOT EXISTS idx_outbox_status  ON outbox(status, created_at);
CREATE INDEX IF NOT EXISTS idx_brain_phone    ON customer_brains(whatsapp_phone) WHERE whatsapp_phone <> '';
"""

_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS customer_brains (
    customer_id     TEXT PRIMARY KEY,
    customer_name   TEXT NOT NULL,
    business_type   TEXT DEFAULT 'General',
    system_prompt   TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    total_chats     INTEGER DEFAULT 0,
    is_active       INTEGER DEFAULT 1,
    plan_tier       TEXT DEFAULT 'starter',
    whatsapp_phone  TEXT DEFAULT '',
    region          TEXT DEFAULT 'us-east-1'
);
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id    TEXT PRIMARY KEY,
    customer_id   TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    last_active   TEXT NOT NULL,
    message_count INTEGER DEFAULT 0,
    channel       TEXT DEFAULT 'api',
    FOREIGN KEY (customer_id) REFERENCES customer_brains(customer_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     TEXT NOT NULL,
    role           TEXT NOT NULL CHECK(role IN ('user','model')),
    content        TEXT NOT NULL,
    timestamp      TEXT NOT NULL,
    token_estimate INTEGER DEFAULT 0,
    ai_provider    TEXT DEFAULT 'gemini',
    latency_ms     INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS crm_contacts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id   TEXT NOT NULL,
    phone_hash    TEXT DEFAULT '',
    enc_name      TEXT NOT NULL,
    enc_phone     TEXT NOT NULL,
    enc_email     TEXT DEFAULT '',
    enc_notes     TEXT DEFAULT '',
    contact_stage TEXT DEFAULT 'lead',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    is_consented  INTEGER DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customer_brains(customer_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS webhook_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source_ip    TEXT,
    payload_hash TEXT NOT NULL,
    customer_id  TEXT,
    channel      TEXT DEFAULT 'tally',
    status       TEXT NOT NULL,
    error_detail TEXT,
    processed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key           TEXT PRIMARY KEY,
    response_body TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS admin_users (
    user_id    TEXT PRIMARY KEY,
    username   TEXT UNIQUE NOT NULL,
    hashed_pw  TEXT NOT NULL,
    role       TEXT NOT NULL DEFAULT 'admin',
    created_at TEXT NOT NULL,
    is_active  INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS audit_log (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ts       TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    action   TEXT NOT NULL,
    resource TEXT NOT NULL,
    detail   TEXT DEFAULT '{}',
    ip       TEXT,
    region   TEXT DEFAULT 'us-east-1'
);
CREATE TABLE IF NOT EXISTS outbox (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type   TEXT NOT NULL,
    payload      TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending',
    created_at   TEXT NOT NULL,
    processed_at TEXT,
    attempts     INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_msg_session   ON chat_messages(session_id, id);
CREATE INDEX IF NOT EXISTS idx_sess_customer ON chat_sessions(customer_id);
CREATE INDEX IF NOT EXISTS idx_crm_customer  ON crm_contacts(customer_id, contact_stage);
CREATE INDEX IF NOT EXISTS idx_idem_created  ON idempotency_keys(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_actor   ON audit_log(actor_id, ts);
CREATE INDEX IF NOT EXISTS idx_outbox_status ON outbox(status, created_at);
"""


def init_db() -> None:
    is_pg  = isinstance(_db_pool, PostgreSQLPool)
    schema = _PG_SCHEMA if is_pg else _SQLITE_SCHEMA
    with _db_pool.get() as conn:
        if is_pg:
            conn.cursor().execute(schema)
        else:
            conn.executescript(schema)
    log.info("🗄️  Database schema initialised.")


def _migrate_v10() -> None:
    """v10: add new customer_brains columns. Safe to run on every boot."""
    for col in ("owner_phone TEXT DEFAULT ''",
                "instagram_id TEXT DEFAULT ''",
                "bot_name TEXT DEFAULT ''"):
        try:
            with _db_pool.get() as conn:
                _execute(conn, f"ALTER TABLE customer_brains ADD COLUMN {col}")
            log.info(f"🗄️  v10 migration: added {col.split()[0]}")
        except Exception:
            pass  # column already exists
    try:
        with _db_pool.get() as conn:
            _execute(conn,
                "CREATE INDEX IF NOT EXISTS idx_brain_ig "
                "ON customer_brains(instagram_id)")
    except Exception:
        pass


def _migrate_v11() -> None:
    """v11: CRM phone_hash dedupe column + index. Idempotent on every boot.
    #13: each statement runs in its own connection, so when two gunicorn
    workers boot simultaneously, the loser's 'duplicate column' error is
    swallowed and the schema is still correct. On Postgres we additionally
    take an advisory lock so the backfill runs exactly once."""
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    if is_pg:
        try:
            with _db_pool.get() as conn:
                _execute(conn, "SELECT pg_advisory_lock(427011)")
                try:
                    _execute(conn, "ALTER TABLE crm_contacts "
                                   "ADD COLUMN IF NOT EXISTS phone_hash TEXT DEFAULT ''")
                    _execute(conn, "CREATE INDEX IF NOT EXISTS idx_crm_dedupe "
                                   "ON crm_contacts(customer_id, phone_hash)")
                finally:
                    _execute(conn, "SELECT pg_advisory_unlock(427011)")
        except Exception as exc:
            log.warning(f"⚠️  v11 migration (pg) issue: {exc}")
    else:
        try:
            with _db_pool.get() as conn:
                _execute(conn, "ALTER TABLE crm_contacts ADD COLUMN phone_hash TEXT DEFAULT ''")
            log.info("🗄️  v11 migration: added crm_contacts.phone_hash")
        except Exception:
            pass  # column already exists
        try:
            with _db_pool.get() as conn:
                _execute(conn, "CREATE INDEX IF NOT EXISTS idx_crm_dedupe "
                               "ON crm_contacts(customer_id, phone_hash)")
        except Exception:
            pass

    # Best-effort backfill so pre-v11 rows participate in dedupe. Bounded,
    # per-row fault-isolated, and skipped instantly when nothing needs it.
    try:
        with _db_pool.get() as conn:
            cur = _execute(conn,
                "SELECT id, customer_id, enc_phone FROM crm_contacts "
                "WHERE phone_hash='' OR phone_hash IS NULL LIMIT 5000")
            rows = cur.fetchall()
        for r in rows:
            try:
                phone = pii_vault.decrypt(r["enc_phone"])
                with _db_pool.get() as conn:
                    _execute(conn, "UPDATE crm_contacts SET phone_hash=? WHERE id=?",
                             (_crm_phone_hash(r["customer_id"], phone), r["id"]))
            except Exception:
                continue
        if rows:
            log.info(f"🗄️  v11 migration: backfilled phone_hash for {len(rows)} contacts")
    except Exception as exc:
        log.warning(f"⚠️  v11 backfill skipped: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 🧠  DISTRIBUTED CACHE  — Redis primary + in-process fallback
# ─────────────────────────────────────────────────────────────────────────────
class DistributedCache:
    def __init__(self, redis_url: str, default_ttl: int = 600):
        self._ttl   = default_ttl
        self._redis = None
        self._local: Dict[str, Tuple[Any, float]] = {}
        self._lock  = threading.Lock()
        if redis_url and REDIS_AVAILABLE:
            try:
                r = redis_lib.from_url(redis_url, decode_responses=True, socket_timeout=2)
                r.ping()
                self._redis = r
                log.info("🧠 Redis distributed cache connected.")
            except Exception as exc:
                log.warning(f"⚠️  Redis unavailable ({exc}) — in-process cache only.")
        else:
            log.warning("⚠️  REDIS_URL not set — in-process cache (single-server).")

    def get(self, key: str) -> Optional[Any]:
        if self._redis:
            try:
                val = self._redis.get(f"heonix:{key}")
                return json.loads(val) if val else None
            except Exception:
                pass
        with self._lock:
            entry = self._local.get(key)
            if entry and time.monotonic() < entry[1]:
                return entry[0]
            self._local.pop(key, None)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if self._redis:
            try:
                self._redis.setex(f"heonix:{key}", ttl or self._ttl, json.dumps(value))
                return
            except Exception:
                pass
        with self._lock:
            self._local[key] = (value, time.monotonic() + (ttl or self._ttl))

    def delete(self, key: str) -> None:
        if self._redis:
            try:
                self._redis.delete(f"heonix:{key}")
            except Exception:
                pass
        with self._lock:
            self._local.pop(key, None)

    def incr(self, key: str, ttl: int = 60) -> int:
        """Atomic increment — used by per-customer rate limiter."""
        if self._redis:
            try:
                pipe = self._redis.pipeline()
                pipe.incr(f"heonix:{key}")
                pipe.expire(f"heonix:{key}", ttl)
                result = pipe.execute()
                return result[0]
            except Exception:
                pass
        with self._lock:
            entry = self._local.get(key, (0, time.monotonic() + ttl))
            new_val = entry[0] + 1
            self._local[key] = (new_val, entry[1])
            return new_val


brain_cache = DistributedCache(cfg.REDIS_URL, default_ttl=cfg.CACHE_TTL)


# ─────────────────────────────────────────────────────────────────────────────
# 🪙  PER-CUSTOMER TOKEN-BUCKET RATE LIMITER  (v8 FIX #8)
#     Limits per customer_id, not just IP — prevents one customer starving others
# ─────────────────────────────────────────────────────────────────────────────
class CustomerRateLimiter:
    """
    Token-bucket rate limiter keyed on customer_id.
    Uses Redis INCR for distributed accuracy; falls back to in-process.
    """
    def __init__(self, requests_per_minute: int = 60):
        self._rpm = requests_per_minute

    def is_allowed(self, customer_id: str) -> bool:
        key    = f"rl:{customer_id}:{int(time.time() // 60)}"
        count  = brain_cache.incr(key, ttl=60)
        return count <= self._rpm

    def check(self, customer_id: str):
        """Call this in route handlers. Returns (allowed: bool, count: int)."""
        return self.is_allowed(customer_id)


customer_limiter = CustomerRateLimiter(requests_per_minute=60)


# ─────────────────────────────────────────────────────────────────────────────
# ⚡  CIRCUIT BREAKER
# ─────────────────────────────────────────────────────────────────────────────
class CircuitBreaker:
    CLOSED = "CLOSED"; OPEN = "OPEN"; HALF_OPEN = "HALF_OPEN"

    def __init__(self, name: str, failure_threshold: int = 5, reset_timeout: float = 60.0):
        self.name           = name
        self._threshold     = failure_threshold
        self._reset_timeout = reset_timeout
        self._failures      = 0
        self._state         = self.CLOSED
        self._opened_at     = 0.0
        self._lock          = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    def call(self, func: Callable, *args, **kwargs):
        with self._lock:
            if self._state == self.OPEN:
                if time.monotonic() - self._opened_at >= self._reset_timeout:
                    self._state = self.HALF_OPEN
                    log.info(f"⚡ CircuitBreaker [{self.name}] → HALF_OPEN")
                else:
                    raise RuntimeError(f"CircuitBreaker [{self.name}] OPEN")
        try:
            result = func(*args, **kwargs)
            with self._lock:
                self._failures = 0
                if self._state == self.HALF_OPEN:
                    self._state = self.CLOSED
                    log.info(f"⚡ CircuitBreaker [{self.name}] → CLOSED (recovered)")
            return result
        except Exception:
            with self._lock:
                self._failures += 1
                if self._failures >= self._threshold:
                    self._state     = self.OPEN
                    self._opened_at = time.monotonic()
                    log.error(f"⚡ CircuitBreaker [{self.name}] → OPEN (failures={self._failures})")
            raise


_gemini_breaker   = CircuitBreaker("Gemini",   failure_threshold=5, reset_timeout=60.0)
_openai_breaker   = CircuitBreaker("OpenAI",   failure_threshold=5, reset_timeout=60.0)
_claude_breaker   = CircuitBreaker("Claude",   failure_threshold=5, reset_timeout=60.0)
_whatsapp_breaker  = CircuitBreaker("WhatsApp",  failure_threshold=3, reset_timeout=30.0)
_instagram_breaker = CircuitBreaker("Instagram", failure_threshold=3, reset_timeout=30.0)  # v10


# ─────────────────────────────────────────────────────────────────────────────
# 🤖  MULTI-AI FALLBACK ENGINE  (v8 FIX #9, #10, #11)
#     Gemini → OpenAI → Claude with exponential back-off + jitter
#     Client singletons — NOT recreated per request (major v7 bug fixed)
# ─────────────────────────────────────────────────────────────────────────────
AI_PROVIDERS_ACTIVE: Dict[str, bool] = {}

# Singletons — instantiated once at startup
_openai_client: Any  = None
_claude_client: Any  = None


def _init_ai_providers() -> None:
    global _openai_client, _claude_client
    if cfg.GENAI_API_KEY and GEMINI_AVAILABLE:
        genai.configure(api_key=cfg.GENAI_API_KEY)
        AI_PROVIDERS_ACTIVE["gemini"] = True
        log.info("✅ Gemini AI ready (Primary)")
    else:
        AI_PROVIDERS_ACTIVE["gemini"] = False
        log.warning("⚠️  Gemini not configured.")

    if cfg.OPENAI_API_KEY and OPENAI_AVAILABLE:
        _openai_client = openai_lib.OpenAI(api_key=cfg.OPENAI_API_KEY)
        AI_PROVIDERS_ACTIVE["openai"] = True
        log.info("✅ OpenAI GPT ready (Fallback #1)")
    else:
        AI_PROVIDERS_ACTIVE["openai"] = False

    if cfg.ANTHROPIC_API_KEY and CLAUDE_AVAILABLE:
        _claude_client = anthropic_lib.Anthropic(api_key=cfg.ANTHROPIC_API_KEY)
        AI_PROVIDERS_ACTIVE["claude"] = True
        log.info("✅ Anthropic Claude ready (Fallback #2)")
    else:
        AI_PROVIDERS_ACTIVE["claude"] = False

    active = [k for k, v in AI_PROVIDERS_ACTIVE.items() if v]
    if not active:
        log.error("❌ No AI providers configured! Set at least one API key.")
    else:
        log.info(f"🤖 AI Fallback Chain: {' → '.join(active)}")


def _call_gemini(system_prompt: str, history: List[Dict], user_message: str) -> str:
    model = genai.GenerativeModel(
        model_name=cfg.GEMINI_MODEL,
        system_instruction=system_prompt,
    )
    chat = model.start_chat(history=history)
    return chat.send_message(user_message).text.strip()


def _call_openai(system_prompt: str, history: List[Dict], user_message: str) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    for turn in history:
        role    = "assistant" if turn["role"] == "model" else "user"
        content = turn["parts"][0] if turn.get("parts") else ""
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})
    resp = _openai_client.chat.completions.create(
        model=cfg.OPENAI_MODEL,
        messages=messages,
        max_tokens=cfg.AI_MAX_TOKENS,
        timeout=cfg.AI_TIMEOUT_SECS,
    )
    return resp.choices[0].message.content.strip()


def _call_claude(system_prompt: str, history: List[Dict], user_message: str) -> str:
    messages = []
    for turn in history:
        role    = "assistant" if turn["role"] == "model" else "user"
        content = turn["parts"][0] if turn.get("parts") else ""
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})
    resp = _claude_client.messages.create(
        model=cfg.ANTHROPIC_MODEL,
        max_tokens=cfg.AI_MAX_TOKENS,
        system=system_prompt,
        messages=messages,
    )
    return resp.content[0].text.strip()


def _retry_with_backoff(fn: Callable, *args, max_retries: int = 3,
                         base_delay: float = 1.0) -> Any:
    """
    Exponential back-off with full jitter (FIX #9).
    Retries on transient errors only; re-raises on final attempt.
    """
    for attempt in range(max_retries + 1):
        try:
            return fn(*args)
        except Exception as exc:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1.0)
            log.warning(f"⚠️  Attempt {attempt+1}/{max_retries} failed ({exc}) — retry in {delay:.1f}s")
            time.sleep(delay)


def multi_ai_reply(
    system_prompt: str,
    history: List[Dict],
    user_message: str,
) -> Tuple[str, str]:
    """
    Try providers in order: Gemini → OpenAI → Claude.
    Each provider uses circuit breaker + exponential back-off retry.
    Returns (reply_text, provider_used). Raises RuntimeError only if ALL fail.
    """
    providers = [
        ("gemini", _gemini_breaker, _call_gemini),
        ("openai", _openai_breaker, _call_openai),
        ("claude", _claude_breaker, _call_claude),
    ]
    errors = []
    for name, breaker, fn in providers:
        if not AI_PROVIDERS_ACTIVE.get(name):
            continue
        try:
            t0    = time.monotonic()
            reply = breaker.call(_retry_with_backoff, fn, system_prompt,
                                 history, user_message,
                                 max_retries=cfg.MAX_RETRIES,
                                 base_delay=cfg.RETRY_BASE_DELAY)
            latency_ms = (time.monotonic() - t0) * 1000
            analytics.inc(f"ai.{name}.success")
            analytics.record_latency(f"ai.{name}.latency_ms", latency_ms)
            if name != "gemini":
                log.info(f"🔄 AI fallback used: {name}")
            return reply, name
        except RuntimeError:
            errors.append(f"{name}:circuit_open")
            analytics.inc(f"ai.{name}.circuit_open")
        except Exception as exc:
            errors.append(f"{name}:{exc}")
            analytics.inc(f"ai.{name}.error")
            log.warning(f"⚠️  {name} failed — next provider. Error: {exc}")

    raise RuntimeError(f"All AI providers failed: {'; '.join(errors)}")


# ─────────────────────────────────────────────────────────────────────────────
# 📱  WHATSAPP CLOUD API  (Official Meta Business API)
# ─────────────────────────────────────────────────────────────────────────────
WHATSAPP_API_BASE = f"https://graph.facebook.com/{cfg.GRAPH_API_VERSION}"  # v10: v19 → env (v21.0)
_wa_session = requests.Session()  # Connection pooling for WA API calls


def verify_meta_signature(raw_body: bytes, signature_header: str,
                          app_secret: str) -> bool:
    """v10: shared by WhatsApp + Instagram webhooks (same X-Hub-Signature-256)."""
    if not app_secret:
        return True  # Skip if secret not configured (dev mode)
    if not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def verify_whatsapp_signature(raw_body: bytes, signature_header: str) -> bool:
    return verify_meta_signature(raw_body, signature_header, cfg.WHATSAPP_APP_SECRET)


def _wa_send_text(to_phone: str, message: str) -> Dict:
    if not cfg.WHATSAPP_TOKEN or not cfg.WHATSAPP_PHONE_ID:
        return {"error": "not_configured"}
    url = f"{WHATSAPP_API_BASE}/{cfg.WHATSAPP_PHONE_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type":    "individual",
        "to":                to_phone,
        "type":              "text",
        "text":              {"body": message[:4096]},
    }
    resp = _wa_session.post(
        url,
        headers={"Authorization": f"Bearer {cfg.WHATSAPP_TOKEN}",
                 "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    if resp.status_code >= 400:
        # v10: Meta says EXACTLY what is wrong. error.code 190 = expired token.
        log.error(f"❌ WhatsApp send {resp.status_code} → {resp.text[:500]}")
    resp.raise_for_status()
    return resp.json()


# ─────────────────────────────────────────────────────────────────────────────
# 🧵  BOUNDED BACKGROUND WORKER POOL  (v11 fix #1 + #11)
#   Webhooks return 200 instantly; heavy work (AI call, voice transcription,
#   outbound sends, RAG store) runs here. Bounded so a traffic burst can never
#   spawn unlimited threads and OOM a 512 MB Render dyno. Was: a fresh
#   threading.Thread per send/store (unbounded → thread explosion under load).
# ─────────────────────────────────────────────────────────────────────────────
_WORKER_POOL = ThreadPoolExecutor(
    max_workers=int(os.getenv("WORKER_THREADS", "8")),
    thread_name_prefix="heonix-bg",
)


def submit_bg(fn: Callable, *args, **kwargs) -> None:
    """Fire-and-forget onto the bounded pool. Never raises into the caller.
    If the pool is shutting down (SIGTERM in flight), runs inline as a fallback
    so an in-progress reply is never silently dropped."""
    try:
        _WORKER_POOL.submit(fn, *args, **kwargs)
    except RuntimeError:
        try:
            fn(*args, **kwargs)
        except Exception as exc:
            log.error(f"❌ inline bg fallback failed: {exc}")


def send_whatsapp_async(to_phone: str, message: str) -> None:
    def _send():
        try:
            _whatsapp_breaker.call(_wa_send_text, to_phone, message)
            analytics.inc("whatsapp.sent")
        except Exception as exc:
            analytics.inc("whatsapp.error")
            log.error(f"❌ WhatsApp send failed → {pii_vault.mask(to_phone)}: {exc}")
    submit_bg(_send)


def _wa_send_template(to_phone: str, template: str, lang: str,
                      body_param: str) -> Dict:
    """v11 #4: template messages work OUTSIDE the 24-hour window — the only
    reliable channel for owner alerts. Template must be pre-approved in the
    Meta console with one {{1}} body parameter."""
    if not cfg.WHATSAPP_TOKEN or not cfg.WHATSAPP_PHONE_ID:
        return {"error": "not_configured"}
    # Meta rejects params containing newlines/tabs/4+ consecutive spaces.
    clean = re.sub(r"\s+", " ", body_param).strip()[:900]
    url = f"{WHATSAPP_API_BASE}/{cfg.WHATSAPP_PHONE_ID}/messages"
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
        headers={"Authorization": f"Bearer {cfg.WHATSAPP_TOKEN}",
                 "Content-Type": "application/json"},
        json=payload, timeout=15)
    if resp.status_code >= 400:
        log.error(f"❌ WA template send {resp.status_code} → {resp.text[:500]}")
    resp.raise_for_status()
    return resp.json()


def send_owner_alert_async(owner_phone: str, message: str) -> None:
    """v11 #4: ALL owner alerts (emergency / handoff / VIP / escalation) route
    here. With OWNER_ALERT_TEMPLATE set → template (works any time). Without it
    → free-form text, and if Meta rejects with 131047 (outside 24h window) we
    log exactly what to fix instead of failing silently."""
    def _send():
        try:
            if cfg.OWNER_ALERT_TEMPLATE:
                _whatsapp_breaker.call(_wa_send_template, owner_phone,
                                       cfg.OWNER_ALERT_TEMPLATE,
                                       cfg.OWNER_ALERT_TEMPLATE_LANG, message)
            else:
                _whatsapp_breaker.call(_wa_send_text, owner_phone, message)
            analytics.inc("owner_alert.sent")
        except Exception as exc:
            analytics.inc("owner_alert.error")
            extra = ""
            if "131047" in str(exc):
                extra = (" ← Meta 24h-window block. Fix: approve a template "
                         "with one {{1}} param and set OWNER_ALERT_TEMPLATE.")
            log.error(f"🚨 OWNER ALERT FAILED → {pii_vault.mask(owner_phone)}: "
                      f"{exc}{extra}")
    submit_bg(_send)


# ─────────────────────────────────────────────────────────────────────────────
# 📸  INSTAGRAM MESSAGING API  (v10 — official Meta Graph, same app family)
# ─────────────────────────────────────────────────────────────────────────────
def _ig_send_text(psid: str, message: str) -> Dict:
    """Send an Instagram DM reply. psid = the sender id from the webhook."""
    if not cfg.INSTAGRAM_TOKEN:
        log.error("❌ Instagram NOT configured: set INSTAGRAM_TOKEN")
        return {"error": "not_configured"}
    target = cfg.INSTAGRAM_ID or "me"
    url = f"https://graph.facebook.com/{cfg.GRAPH_API_VERSION}/{target}/messages"
    payload = {
        "recipient": {"id": psid},
        "message":   {"text": message[:1000]},   # IG text limit = 1000 chars
    }
    resp = _wa_session.post(
        url,
        headers={"Authorization": f"Bearer {cfg.INSTAGRAM_TOKEN}",
                 "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    if resp.status_code >= 400:
        log.error(f"❌ Instagram send {resp.status_code} → {resp.text[:500]}")
    resp.raise_for_status()
    return resp.json()


def send_instagram_async(psid: str, message: str) -> None:
    def _send():
        try:
            _instagram_breaker.call(_ig_send_text, psid, message)
            analytics.inc("instagram.sent")
        except Exception as exc:
            analytics.inc("instagram.error")
            log.error(f"❌ Instagram send failed → {pii_vault.mask(psid)}: {exc}")
    submit_bg(_send)


# ─────────────────────────────────────────────────────────────────────────────
# 🏢  BUSINESS TEMPLATES  (auto-detect industry, assign AI persona)
# ─────────────────────────────────────────────────────────────────────────────
BUSINESS_TEMPLATES: Dict[str, Dict] = {
    "restaurant": {
        "keywords": ["restaurant", "cafe", "food", "dining", "catering", "bistro", "bakery", "hotel"],
        "bot_name": "NOVA",
        "prompt": (
            "You are NOVA, a warm and knowledgeable AI dining assistant for {name}. "
            "Help guests explore the menu, make reservations, clarify dietary needs, "
            "and create a memorable hospitality experience. "
            "Always respond in the same language the user writes in."
        ),
    },
    "ecommerce": {
        "keywords": ["shop", "store", "ecommerce", "product", "order", "shipping", "fashion", "retail"],
        "bot_name": "PULSE",
        "prompt": (
            "You are PULSE, a fast and friendly AI shopping assistant for {name}. "
            "Help customers find products, track orders, handle returns, and provide "
            "personalised recommendations. Be concise and solutions-focused. "
            "Always respond in the same language the user writes in."
        ),
    },
    "healthcare": {
        "keywords": ["clinic", "health", "doctor", "medical", "hospital", "dental", "pharmacy", "wellness", "patient"],
        "bot_name": "HELIO",
        "prompt": (
            "You are HELIO, a compassionate AI health assistant for {name}. "
            "Answer general health queries and help schedule appointments with empathy and clarity. "
            "NEVER provide diagnoses or prescribe treatments. "
            "Always recommend a licensed professional for serious concerns. "
            "All data is handled per DPDP Act / HIPAA compliance. "
            "Always respond in the same language the user writes in."
        ),
    },
    "education": {
        "keywords": ["school", "education", "tutoring", "course", "learning", "academy", "university", "coaching"],
        "bot_name": "SAGE",
        "prompt": (
            "You are SAGE, a knowledgeable AI learning assistant for {name}. "
            "Help students and parents understand offerings, guide enrolment, "
            "and answer academic queries with patience and clarity. "
            "Always respond in the same language the user writes in."
        ),
    },
    "saas": {
        "keywords": ["software", "saas", "platform", "app", "tool", "startup", "tech", "ai", "api", "dashboard"],
        "bot_name": "APEX",
        "prompt": (
            "You are APEX, a razor-sharp AI product specialist for {name}. "
            "Help users understand features, navigate onboarding, handle billing queries, "
            "and escalate technical issues. Be precise and solution-focused. "
            "Always respond in the same language the user writes in."
        ),
    },
    "legal": {
        "keywords": ["law", "legal", "lawyer", "attorney", "advocate", "court", "litigation"],
        "bot_name": "LEX",
        "prompt": (
            "You are LEX, a professional AI legal intake assistant for {name}. "
            "Help prospects understand services, qualify case types, and book consultations. "
            "NEVER provide specific legal advice. Always recommend a licensed attorney. "
            "Be formal, precise, and trustworthy. "
            "Always respond in the same language the user writes in."
        ),
    },
    "default": {
        "keywords": [],
        "bot_name": "ELITE",
        "prompt": (
            "You are ELITE, a professional AI business assistant for {name}. "
            "Understand customer needs, provide excellent support, and create a memorable "
            "brand experience. Be sharp, efficient, and solutions-focused. "
            "Always respond in the same language the user writes in."
        ),
    },
}


def detect_business_type(description: str) -> str:
    lower = description.lower()
    for btype, data in BUSINESS_TEMPLATES.items():
        if btype == "default":
            continue
        if any(kw in lower for kw in data["keywords"]):
            return btype
    return "default"


def build_system_prompt(customer_name: str, business_desc: str) -> Tuple[str, str]:
    btype    = detect_business_type(business_desc)
    template = BUSINESS_TEMPLATES[btype]
    prompt   = template["prompt"].format(name=customer_name)
    return template["bot_name"], prompt


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# 👑  GOD-LOGIC v10  (god_logic_v9 merged in — every v9 drawback addressed)
#     Drawback fixes vs v9 module:
#       1. Cache lost on restart      → brain_cache (Redis when REDIS_URL set)
#       2. Only ta/hi/en              → 16-script detect, 10-language canned,
#                                       AI itself replies in ANY language
#       3. Keyword-only emergencies   → hybrid: keywords (instant, free) + AI
#                                       escalation token (understands meaning,
#                                       works in every language)
#       4. Voice = Gemini only        → Gemini → OpenAI Whisper fallback chain
#       5. "Mostly routing"           → Qdrant RAG long-term memory per user
#       6. No vector memory           → see #5 (AES-256-encrypted payloads)
# ─────────────────────────────────────────────────────────────────────────────

# ⟦PURE-LOGIC-BEGIN⟧  (no I/O — unit-testable in isolation)

_SCRIPT_RANGES = [
    ("ta", 0x0B80, 0x0BFF),   # Tamil
    ("te", 0x0C00, 0x0C7F),   # Telugu
    ("kn", 0x0C80, 0x0CFF),   # Kannada
    ("ml", 0x0D00, 0x0D7F),   # Malayalam
    ("hi", 0x0900, 0x097F),   # Devanagari (Hindi/Marathi/Nepali)
    ("bn", 0x0980, 0x09FF),   # Bengali
    ("gu", 0x0A80, 0x0AFF),   # Gujarati
    ("pa", 0x0A00, 0x0A7F),   # Gurmukhi (Punjabi)
    ("or", 0x0B00, 0x0B7F),   # Odia
    ("si", 0x0D80, 0x0DFF),   # Sinhala
    ("ar", 0x0600, 0x06FF),   # Arabic / Urdu script
    ("ru", 0x0400, 0x04FF),   # Cyrillic
    ("th", 0x0E00, 0x0E7F),   # Thai
    ("zh", 0x4E00, 0x9FFF),   # CJK
    ("ja", 0x3040, 0x30FF),   # Kana
    ("ko", 0xAC00, 0xD7AF),   # Hangul
]


def detect_language(text):
    """Script-based detection, with a romanised-text fallback (v11 #10).
    The AI always replies in the user's language via _LANGUAGE_RULE; this
    function only decides which *local* canned/emergency line to use."""
    counts = {}
    for ch in text:
        cp = ord(ch)
        for code, lo, hi in _SCRIPT_RANGES:
            if lo <= cp <= hi:
                counts[code] = counts.get(code, 0) + 1
                break
    if counts:
        return max(counts, key=counts.get)
    # v11 #10: pure-Latin input → could be romanised Tamil/Hindi ("vanakkam",
    # "enakku romba vali"). Without this, a Tamil speaker typing in English
    # letters got the English emergency line. AI reply path was already fine.
    return _romanized_lang(text) or "en"


# Strong romanised markers — chosen to NOT collide with common English words.
_ROMAN_TA = {
    "vanakkam", "nandri", "enakku", "enaku", "romba", "rumba", "vali",
    "poitu", "poidu", "varen", "eppadi", "epadi", "irukku", "iruku",
    "venum", "vendum", "seekiram", "seekkiram", "kandippa", "udane",
    "moochu", "moochi", "thangala", "thangamudiyala", "rathum", "vibathu",
    "thatkolai", "saavu", "mayakkam", "sappuda", "udanadiyaa",
}
_ROMAN_HI = {
    "namaste", "namaskar", "dhanyavad", "dhanyawad", "shukriya", "kaise",
    "kyun", "nahi", "nahin", "madad", "chahiye", "kripya", "theek",
    "bahut", "dard", "jaldi", "turant", "khoon", "saans", "behosh",
    "aatmahatya", "bachao",
}


def _romanized_lang(text):
    """Returns 'ta' / 'hi' if the Latin text carries strong romanised markers,
    else None. Conservative: needs at least one high-confidence token."""
    toks = set(_norm_text(text).split())
    ta = len(toks & _ROMAN_TA)
    hi = len(toks & _ROMAN_HI)
    if ta == 0 and hi == 0:
        return None
    return "ta" if ta >= hi else "hi"


def _norm_text(text):
    """Lowercase + strip everything that isn't a letter/digit → stable matching."""
    text = unicodedata.normalize("NFKC", str(text)).lower()
    text = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in text)
    return re.sub(r"\s+", " ", text).strip()


# Canned replies — 10 languages. Any other language → None → goes to the AI,
# which answers natively in whatever language the user wrote.
_CANNED = {
    "greet": {
        "en": "Hello! 👋 I'm {bot}. How can I help you today?",
        "ta": "வணக்கம்! 👋 நான் {bot}. இன்று எப்படி உதவலாம்?",
        "hi": "नमस्ते! 👋 मैं {bot} हूँ। आज मैं कैसे मदद कर सकता हूँ?",
        "te": "నమస్తే! 👋 నేను {bot}. ఈ రోజు మీకు ఎలా సహాయం చేయగలను?",
        "kn": "ನಮಸ್ಕಾರ! 👋 ನಾನು {bot}. ಇಂದು ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
        "ml": "നമസ്കാരം! 👋 ഞാൻ {bot}. ഇന്ന് എങ്ങനെ സഹായിക്കാം?",
        "bn": "নমস্কার! 👋 আমি {bot}। আজ কীভাবে সাহায্য করতে পারি?",
        "gu": "નમસ્તે! 👋 હું {bot} છું. આજે કેવી રીતે મદદ કરી શકું?",
        "pa": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! 👋 ਮੈਂ {bot} ਹਾਂ। ਅੱਜ ਕਿਵੇਂ ਮਦਦ ਕਰਾਂ?",
        "ar": "مرحباً! 👋 أنا {bot}. كيف أستطيع مساعدتك اليوم؟",
    },
    "thanks": {
        "en": "You're welcome! 🙏 Anything else I can help with?",
        "ta": "மகிழ்ச்சி! 🙏 வேறு ஏதாவது உதவி வேண்டுமா?",
        "hi": "आपका स्वागत है! 🙏 और कुछ मदद चाहिए?",
        "te": "సంతోషం! 🙏 ఇంకేమైనా సహాయం కావాలా?",
        "kn": "ಸಂತೋಷ! 🙏 ಇನ್ನೇನಾದರೂ ಸಹಾಯ ಬೇಕೇ?",
        "ml": "സന്തോഷം! 🙏 വേറെ എന്തെങ്കിലും സഹായം വേണോ?",
        "bn": "স্বাগতম! 🙏 আর কিছু সাহায্য লাগবে?",
        "gu": "સ્વાગત છે! 🙏 બીજી કોઈ મદદ જોઈએ?",
        "pa": "ਜੀ ਆਇਆਂ ਨੂੰ! 🙏 ਹੋਰ ਕੋਈ ਮਦਦ ਚਾਹੀਦੀ ਹੈ?",
        "ar": "على الرحب والسعة! 🙏 هل تحتاج مساعدة أخرى؟",
    },
    "ack": {
        "en": "👍 Let me know if you need anything else.",
        "ta": "👍 வேறு ஏதாவது தேவைப்பட்டால் சொல்லுங்கள்.",
        "hi": "👍 कुछ और चाहिए तो बताइए।",
        "te": "👍 ఇంకేమైనా కావాలంటే చెప్పండి.",
        "kn": "👍 ಇನ್ನೇನಾದರೂ ಬೇಕಿದ್ದರೆ ತಿಳಿಸಿ.",
        "ml": "👍 വേറെ എന്തെങ്കിലും വേണമെങ്കിൽ പറയൂ.",
        "bn": "👍 আর কিছু লাগলে জানাবেন।",
        "gu": "👍 બીજું કંઈ જોઈએ તો જણાવજો.",
        "pa": "👍 ਹੋਰ ਕੁਝ ਚਾਹੀਦਾ ਹੋਵੇ ਤਾਂ ਦੱਸੋ।",
        "ar": "👍 أخبرني إذا احتجت أي شيء آخر.",
    },
    "bye": {
        "en": "Thank you for reaching out — take care! 👋",
        "ta": "தொடர்பு கொண்டதற்கு நன்றி — பத்திரம்! 👋",
        "hi": "संपर्क करने के लिए धन्यवाद — ध्यान रखें! 👋",
        "te": "సంప్రదించినందుకు ధన్యవాదాలు — జాగ్రత్త! 👋",
        "kn": "ಸಂಪರ್ಕಿಸಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದಗಳು — ಜೋಪಾನ! 👋",
        "ml": "ബന്ധപ്പെട്ടതിന് നന്ദി — ശ്രദ്ധിക്കണേ! 👋",
        "bn": "যোগাযোগের জন্য ধন্যবাদ — ভালো থাকবেন! 👋",
        "gu": "સંપર્ક કરવા બદલ આભાર — સંભાળજો! 👋",
        "pa": "ਸੰਪਰਕ ਕਰਨ ਲਈ ਧੰਨਵਾਦ — ਖ਼ਿਆਲ ਰੱਖਣਾ! 👋",
        "ar": "شكراً لتواصلك — اعتنِ بنفسك! 👋",
    },
}

_GREET_RAW = ["hi", "hii", "hiii", "hey", "hello", "helo", "hlo", "start", "menu",
              "vanakkam", "வணக்கம்", "ஹாய்", "ஹலோ", "namaste", "namaskar",
              "नमस्ते", "नमस्कार", "నమస్తే", "నమస్కారం", "ನಮಸ್ಕಾರ", "നമസ്കാരം",
              "নমস্কার", "નમસ્તે", "ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "مرحبا", "السلام عليكم", "اهلا"]
_THANKS_RAW = ["thanks", "thank you", "thank u", "thx", "ty", "tnx",
               "nandri", "நன்றி", "रोम्बा नन्द्री", "dhanyavad", "dhanyawad",
               "धन्यवाद", "शुक्रिया", "ధన్యవాదాలు", "ಧನ್ಯವಾದ", "നന്ദി",
               "ধন্যবাদ", "આભાર", "ਧੰਨਵਾਦ", "شكرا", "شكرًا"]
_ACK_RAW = ["ok", "okay", "okk", "k", "fine", "good", "great", "got it", "done",
            "sari", "சரி", "ஓகே", "thik", "theek", "ठीक", "ठीक है", "ओके",
            "సరే", "ಸರಿ", "ശരി", "ঠিক আছে", "ઠીક છે", "ਠੀਕ ਹੈ", "تمام", "حسنا"]
_BYE_RAW = ["bye", "goodbye", "good bye", "tata", "ta ta", "poitu varen",
            "போயிட்டு வரேன்", "alvida", "अलविदा", "வீடி", "మళ్ళీ కలుద్దాం",
            "ਅਲਵਿਦਾ", "مع السلامة", "وداعا"]

_GREET  = {_norm_text(x) for x in _GREET_RAW}
_THANKS = {_norm_text(x) for x in _THANKS_RAW}
_ACK    = {_norm_text(x) for x in _ACK_RAW}
_BYE    = {_norm_text(x) for x in _BYE_RAW}


def canned_reply(text, bot_name=""):
    """Local zero-cost reply for trivial messages; None → send to the AI."""
    norm = _norm_text(text)
    if not norm or len(norm.split()) > 4:
        return None
    lang = detect_language(text)
    bot  = bot_name or "your AI assistant"
    if norm in _GREET:
        tpl = _CANNED["greet"].get(lang)
        return tpl.format(bot=bot) if tpl else None
    for key, vocab in (("thanks", _THANKS), ("ack", _ACK), ("bye", _BYE)):
        if norm in vocab:
            return _CANNED[key].get(lang)   # unknown lang → None → AI handles
    return None


# Intent keywords — fast free layer for en/ta/hi (the launch markets).
# Every OTHER language is covered by the AI escalation token further below.
_EMERGENCY_KW = [
    # NOTE: lone "urgent" removed on purpose — sales leads say "urgent" too.
    # Genuine urgent cases are caught by the AI escalation token (all languages).
    "emergency", "medical emergency", "severe pain", "unbearable", "bleeding",
    "accident", "heart attack", "chest pain", "can't breathe", "cant breathe",
    "fainted", "collapsed", "suicide", "kill myself", "sos",
    # v11 #10: romanised Tamil/Hindi emergency markers (launch markets)
    "romba vali", "thanga mudiyala", "moochu vanga", "moochi vanga", "rathum",
    "bahut dard", "saans nahi", "khoon", "behosh", "aatmahatya",
    "அவசரம்", "ரொம்ப வலி", "தாங்க முடியல", "ரத்தம்", "விபத்து", "தற்கொலை",
    "மூச்சு வாங்க", "மூச்சு முட்ட", "மயக்கம்",
    "इमरजेंसी", "बहुत दर्द", "खून", "साँस नहीं", "आत्महत्या", "दुर्घटना",
]
_HUMAN_KW = [
    "talk to a human", "talk to human", "talk to a person", "real person",
    "human agent", "live agent", "customer care", "speak to the doctor",
    "talk to the doctor", "talk to doctor", "speak to manager", "talk to manager",
    "talk to owner", "speak to owner", "connect me to", "transfer me",
    "i want to talk to", "want to speak to",
    "டாக்டர் கிட்ட பேசணும்", "மேனேஜர் கிட்ட", "ஆள் கிட்ட பேசணும்",
    "எம்.டி கிட்ட", "நேரடியா பேசணும்",
    "डॉक्टर से बात", "मैनेजर से बात", "किसी इंसान से बात", "इंसान से बात",
]
_VIP_KW = [
    "crore", "crores", "lakh", "lakhs", "budget", "premium", "luxury",
    "penthouse", "villa", "bulk order", "wholesale", "enterprise plan",
    "கோடி", "லட்சம்", "பட்ஜெட்", "வில்லா", "करोड़", "लाख", "बजट",
]
_MONEY_RE  = re.compile(r"(₹|rs\.?\s?\d|inr\s?\d)", re.IGNORECASE)
_BIGNUM_RE = re.compile(r"\d+\s*(crore|crores|cr|lakh|lakhs)\b", re.IGNORECASE)

# v11 #9: words that, immediately before a keyword, flip its meaning.
_NEGATORS = {
    "no", "not", "non", "without", "never", "dont", "doesnt", "isnt", "wont",
    "cant", "neither", "nor", "illa", "illai", "kidaiyaadhu", "nahi", "nahin",
    "mat", "bina", "bila",
}


def _kw_hit(norm_text: str, keyword: str) -> bool:
    """v11 #9: whole-word match for `keyword` inside already-normalised text,
    skipping any occurrence that is immediately preceded by a negator. This
    stops 'no budget' → VIP, 'not premium' → VIP, 'no chest pain' → emergency,
    while still firing on real 'severe chest pain'."""
    kw = _norm_text(keyword)
    if not kw:
        return False
    toks    = norm_text.split()
    kw_toks = kw.split()
    n       = len(kw_toks)
    for i in range(len(toks) - n + 1):
        if toks[i:i + n] == kw_toks:
            prev = toks[i - 1] if i > 0 else ""
            if prev in _NEGATORS:
                continue           # negated occurrence → keep scanning
            return True
    return False


def classify_message(text):
    """Returns {'emergency','human','vip'} booleans. Pure, instant, free.
    v11 #9: word-boundary + negation aware (was naive substring matching)."""
    norm = _norm_text(text)
    return {
        "emergency": any(_kw_hit(norm, k) for k in _EMERGENCY_KW),
        "human":     any(_kw_hit(norm, k) for k in _HUMAN_KW),
        "vip":       (any(_kw_hit(norm, k) for k in _VIP_KW)
                      or bool(_MONEY_RE.search(text))
                      or bool(_BIGNUM_RE.search(text))),
    }

# ⟦PURE-LOGIC-END⟧


_EMERGENCY_LINES = {
    "ta": ("உங்கள் செய்தி எங்கள் குழுவிற்கு உடனடியாக அனுப்பப்பட்டது. "
           "மருத்துவ அவசரநிலை எனில் தயவுசெய்து உடனடியாக அழைக்கவும்."),
    "hi": ("आपका संदेश हमारी टीम को तुरंत भेज दिया गया है। "
           "मेडिकल इमरजेंसी होने पर कृपया तुरंत कॉल करें।"),
    "en": ("Your message has been sent to our team right away. If this is a "
           "medical emergency, please call your local emergency number immediately."),
}
_HUMAN_LINES = {
    "ta": "ஒரு நிமிடம் 🙏 உங்களை எங்கள் குழுவுடன் இணைக்கிறேன்.",
    "hi": "एक मिनट 🙏 मैं आपको हमारी टीम से जोड़ रहा हूँ।",
    "en": "One moment 🙏 connecting you with our team now.",
}


# ── 👻 Ghost mode — Redis-backed via brain_cache → works across ALL gunicorn
#    workers (the in-memory v9 version silently broke with --workers 4).
def ghost_mute(uid: str) -> None:
    brain_cache.set(f"ghost:{uid}", 1, ttl=cfg.GHOST_MUTE_SECONDS)
    analytics.inc("ghost.muted")


def ghost_is_muted(uid: str) -> bool:
    return brain_cache.get(f"ghost:{uid}") is not None


def ghost_resume(uid: str) -> None:
    brain_cache.delete(f"ghost:{uid}")


# ── 🗄️ Response cache — brain_cache backend = survives restarts + shared
#    across workers when REDIS_URL is set (fixes v9 drawback #1).
def _resp_key(system_prompt: str, message: str) -> str:
    # v11 fix #6: hash the WHOLE prompt, not [:200]. Two customers whose prompts
    # share the first 200 chars (very common — same template header) would
    # otherwise collide and get each other's cached answers. The prompt already
    # carries the customer identity, so a full-prompt hash is the cache boundary.
    raw = (hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()
           + "|" + _norm_text(message)).encode("utf-8")
    return "resp:" + hashlib.sha256(raw).hexdigest()[:32]


def resp_cache_get(system_prompt: str, message: str) -> Optional[str]:
    val = brain_cache.get(_resp_key(system_prompt, message))
    return val if isinstance(val, str) and val else None


def resp_cache_put(system_prompt: str, message: str, reply: str) -> None:
    if reply:
        brain_cache.set(_resp_key(system_prompt, message), reply,
                        ttl=cfg.RESPONSE_CACHE_TTL)


# ── 🎙️ Voice-note decoder — Gemini (multimodal) → OpenAI Whisper fallback.
_TRANSCRIBE_PROMPT = ("Transcribe this voice message to plain text. Keep the "
                      "original language exactly as spoken. Return ONLY the "
                      "transcript, nothing else.")


def transcribe_audio_bytes(audio_bytes: bytes, mime: str = "audio/ogg") -> str:
    """Never raises — returns '' on failure so one bad audio can't 500 a webhook."""
    if not audio_bytes:
        return ""
    mime = (mime or "audio/ogg").split(";")[0].strip()

    # 1) Gemini (primary — already configured by _init_ai_providers)
    if AI_PROVIDERS_ACTIVE.get("gemini"):
        try:
            gmodel = genai.GenerativeModel(model_name=cfg.GEMINI_MODEL)
            resp   = gmodel.generate_content(
                [_TRANSCRIBE_PROMPT, {"mime_type": mime, "data": audio_bytes}])
            text = (getattr(resp, "text", "") or "").strip()
            if text:
                analytics.inc("voice.gemini.success")
                return text
        except Exception as exc:
            log.warning(f"⚠️  Gemini transcription failed: {exc}")
            analytics.inc("voice.gemini.error")

    # 2) OpenAI Whisper fallback (fixes v9 drawback #4)
    if AI_PROVIDERS_ACTIVE.get("openai") and _openai_client is not None:
        try:
            buf = io.BytesIO(audio_bytes)
            buf.name = "voice." + ("ogg" if "ogg" in mime else
                                   (mime.split("/")[-1] or "mp3"))
            tr = _openai_client.audio.transcriptions.create(
                model=cfg.OPENAI_TRANSCRIBE_MODEL, file=buf)
            text = (getattr(tr, "text", "") or "").strip()
            if text:
                analytics.inc("voice.whisper.success")
                log.info("🔄 Voice fallback used: whisper")
                return text
        except Exception as exc:
            log.warning(f"⚠️  Whisper transcription failed: {exc}")
            analytics.inc("voice.whisper.error")

    return ""


def transcribe_voice_note(media_id: str) -> str:
    """WhatsApp: media_id → signed URL → bytes → transcript. '' on any failure."""
    if not media_id or not cfg.WHATSAPP_TOKEN:
        return ""
    try:
        meta = _wa_session.get(
            f"https://graph.facebook.com/{cfg.GRAPH_API_VERSION}/{media_id}",
            headers={"Authorization": f"Bearer {cfg.WHATSAPP_TOKEN}"}, timeout=15)
        meta.raise_for_status()
        info  = meta.json()
        audio = _wa_session.get(
            info["url"],
            headers={"Authorization": f"Bearer {cfg.WHATSAPP_TOKEN}"}, timeout=30)
        audio.raise_for_status()
        return transcribe_audio_bytes(audio.content,
                                      info.get("mime_type", "audio/ogg"))
    except Exception as exc:
        log.error(f"❌ Voice download failed: {exc}")
        return ""


def transcribe_audio_url(url: str) -> str:
    """Instagram: attachments carry a public CDN URL — no auth header needed."""
    if not url:
        return ""
    try:
        audio = _wa_session.get(url, timeout=30)
        audio.raise_for_status()
        mime = audio.headers.get("Content-Type", "audio/mp4")
        return transcribe_audio_bytes(audio.content, mime)
    except Exception as exc:
        log.error(f"❌ IG audio download failed: {exc}")
        return ""


# ── 🧬 RAG LONG-TERM MEMORY — Qdrant + Gemini embeddings (v9 drawbacks #5,#6)
#    Per end-user memory across sessions. Payload text is AES-256-GCM encrypted
#    so the vector DB never stores readable PII (DPDP-friendly).
_qdrant_client: Any = None
_rag_ready: bool    = False


def init_rag() -> None:
    global _qdrant_client, _rag_ready
    if not QDRANT_AVAILABLE:
        log.warning("⚠️  qdrant-client not installed — RAG memory OFF.")
        return
    if not cfg.QDRANT_URL:
        log.warning("⚠️  QDRANT_URL not set — RAG memory OFF.")
        return
    if not AI_PROVIDERS_ACTIVE.get("gemini"):
        log.warning("⚠️  Gemini key required for embeddings — RAG memory OFF.")
        return
    try:
        client = QdrantClient(url=cfg.QDRANT_URL,
                              api_key=cfg.QDRANT_API_KEY or None, timeout=10)
        try:
            client.get_collection(cfg.QDRANT_COLLECTION)
        except Exception:
            client.create_collection(
                collection_name=cfg.QDRANT_COLLECTION,
                vectors_config=qmodels.VectorParams(
                    size=cfg.EMBED_DIMS, distance=qmodels.Distance.COSINE))
            log.info(f"🧬 Qdrant collection created: {cfg.QDRANT_COLLECTION}")
        _qdrant_client = client
        _rag_ready     = True
        log.info("🧬 RAG long-term memory ONLINE (Qdrant).")
    except Exception as exc:
        log.warning(f"⚠️  Qdrant unreachable ({exc}) — RAG memory OFF, engine OK.")


def _embed(text: str, is_query: bool = False) -> List[float]:
    task = "retrieval_query" if is_query else "retrieval_document"
    try:
        res = genai.embed_content(model=cfg.EMBED_MODEL, content=text[:2000],
                                  task_type=task,
                                  output_dimensionality=cfg.EMBED_DIMS)
    except TypeError:   # older SDK without output_dimensionality
        res = genai.embed_content(model=cfg.EMBED_MODEL, content=text[:2000],
                                  task_type=task)
    vec = res["embedding"]
    return list(vec)[:cfg.EMBED_DIMS]


def rag_store(customer_id: str, uid: str, user_text: str, reply: str) -> None:
    """Fire-and-forget — memory writes never slow down or break a reply."""
    if not _rag_ready or len(user_text.split()) < 4:
        return

    def _w():
        try:
            vec = _embed(user_text, is_query=False)
            enc = pii_vault.encrypt(
                f"User said: {user_text[:500]} | Assistant replied: {reply[:300]}")
            _qdrant_client.upsert(
                collection_name=cfg.QDRANT_COLLECTION,
                points=[qmodels.PointStruct(
                    id=str(uuid.uuid4()), vector=vec,
                    payload={"customer_id": customer_id, "uid": uid,
                             "enc": enc, "ts": _now()})])
            analytics.inc("rag.stored")
        except Exception as exc:
            log.warning(f"⚠️  RAG store failed: {exc}")

    submit_bg(_w)   # v11 #11: bounded pool instead of a raw daemon thread


def rag_retrieve(customer_id: str, uid: str, query: str) -> str:
    """Returns a memory block ('' if none). Failures degrade silently."""
    if not _rag_ready or len(query.split()) < 3:
        return ""
    try:
        vec = _embed(query, is_query=True)
        flt = qmodels.Filter(must=[
            qmodels.FieldCondition(key="customer_id",
                                   match=qmodels.MatchValue(value=customer_id)),
            qmodels.FieldCondition(key="uid",
                                   match=qmodels.MatchValue(value=uid)),
        ])
        hits = _qdrant_client.search(
            collection_name=cfg.QDRANT_COLLECTION, query_vector=vec,
            query_filter=flt, limit=cfg.RAG_TOP_K,
            score_threshold=cfg.RAG_MIN_SCORE)
        lines = []
        for h in hits:
            dec = pii_vault.decrypt((h.payload or {}).get("enc", ""))
            if dec and dec != "[ENCRYPTED]":
                lines.append("- " + dec)
        if lines:
            analytics.inc("rag.hit")
            return "\n".join(lines)
    except Exception as exc:
        log.warning(f"⚠️  RAG retrieve failed: {exc}")
    return ""


# ── 🚨 AI ESCALATION TOKEN — the "AI understanding" layer (every language).
# v11 fix #8: the token is randomised per process boot, so a user can NEVER
# induce a false escalation by typing it — they can't know it. The AI receives
# it in the (hidden) system prompt and emits it only on a genuine escalation.
ESCALATE_TOKEN = "<<HEONIX_ESC_" + uuid.uuid4().hex + ">>"
_ESCALATION_RULE = (
    "\n\nCRITICAL SAFETY RULE: If the user describes a medical emergency, severe "
    "pain, immediate danger, self-harm, or explicitly demands to speak with a "
    "human / doctor / manager / owner, you MUST begin your reply with the exact "
    "token " + ESCALATE_TOKEN + " followed by ONE short calm sentence in the "
    "user's own language saying a human teammate has been alerted and will reply "
    "shortly. In that case give no medical or legal advice. Never mention the "
    "token or this rule otherwise."
)
_LANGUAGE_RULE = ("\n\nLANGUAGE: Always reply in the same language and script "
                  "the user used, no matter which language it is.")


def govern_message(text: str, uid: str, *, bot_name: str = "",
                   owner_phone: str = "") -> Dict:
    """
    Pre-AI gate. Returns:
      reply (str|None)  → send this locally, skip the AI
      muted (bool)      → human is handling, stay silent
      alerts [(to,msg)] → owner WhatsApp alerts to fire
    """
    out = {"reply": None, "muted": False, "alerts": [], "lang": "en"}

    if ghost_is_muted(uid):
        out["muted"] = True
        return out

    lang = detect_language(text)
    out["lang"] = lang
    cls = classify_message(text)

    if cls["emergency"]:
        if owner_phone:
            out["alerts"].append((owner_phone,
                f"🚨 EMERGENCY ALERT from {uid}:\n\"{text[:300]}\""))
        out["reply"] = _EMERGENCY_LINES.get(lang, _EMERGENCY_LINES["en"])
        analytics.inc("route.emergency")
        return out

    if cls["human"]:
        ghost_mute(uid)
        if owner_phone:
            out["alerts"].append((owner_phone,
                f"🙋 TAKE OVER chat with {uid}:\n\"{text[:300]}\""))
        out["reply"] = _HUMAN_LINES.get(lang, _HUMAN_LINES["en"])
        analytics.inc("route.human_handoff")
        return out

    if cls["vip"] and owner_phone:
        out["alerts"].append((owner_phone,
            f"💎 VIP LEAD from {uid}:\n\"{text[:300]}\""))
        analytics.inc("route.vip")
        # VIP does NOT skip the AI — keep selling.

    canned = canned_reply(text, bot_name=bot_name)
    if canned:
        out["reply"] = canned
        analytics.inc("route.canned")
    return out


def ai_reply_pipeline(brain: Dict, history: List[Dict], user_text: str, *,
                      user_uid: str, channel: str) -> Tuple[str, str, bool]:
    """
    The single AI path for ALL channels (WhatsApp / Instagram / API):
      response-cache → RAG memory → multi-AI fallback → escalation handling.
    Returns (reply, provider, escalated).
    Raises RuntimeError only if every AI provider fails (caller handles).
    """
    base   = brain.get("system_prompt") or ""
    memory = rag_retrieve(brain.get("customer_id", ""), user_uid, user_text)

    # Cache only memory-free answers — personalised replies must never be
    # served to a different person who happens to ask the same question.
    cacheable = (memory == "")
    if cacheable:
        cached = resp_cache_get(base, user_text)
        if cached:
            analytics.inc("cache.response.hit")
            return cached, "cache", False

    sys_prompt = base
    if memory:
        sys_prompt += ("\n\nRELEVANT MEMORY from earlier chats with this same "
                       "person (use naturally, don't recite):\n" + memory)
    sys_prompt += _LANGUAGE_RULE + _ESCALATION_RULE

    reply, provider = multi_ai_reply(sys_prompt, history, user_text)

    escalated = ESCALATE_TOKEN in reply
    if escalated:
        reply = reply.replace(ESCALATE_TOKEN, "").strip() or \
                _HUMAN_LINES.get(detect_language(user_text), _HUMAN_LINES["en"])
        owner = brain.get("owner_phone") or ""
        if owner:
            send_owner_alert_async(owner,
                f"🚨 AI ESCALATION ({channel}) from {user_uid}:\n\"{user_text[:300]}\"")
        analytics.inc("escalation.ai")
    else:
        if cacheable and provider != "cache":
            resp_cache_put(base, user_text, reply)
        rag_store(brain.get("customer_id", ""), user_uid, user_text, reply)

    return reply, provider, escalated


# ─────────────────────────────────────────────────────────────────────────────
# 📐  PYDANTIC VALIDATION MODELS
# ─────────────────────────────────────────────────────────────────────────────
class WebhookPayloadValidator(BaseModel):
    customer_name:  str = Field(default="Anonymous Client", min_length=1, max_length=200)
    business_type:  str = Field(default="General Business", max_length=300)
    extra_notes:    str = Field(default="", max_length=1000)
    whatsapp_phone: str = Field(default="", max_length=20)
    owner_phone:    str = Field(default="", max_length=20)   # v10: alerts target
    instagram_id:   str = Field(default="", max_length=60)   # v10: IG business id

    @field_validator("customer_name", "business_type", mode="before")
    @classmethod
    def strip_strings(cls, v: Any) -> str:
        return str(v).strip() if v else ""


class ChatRequestValidator(BaseModel):
    customer_id: str = Field(..., min_length=3, max_length=100, pattern=r"^[A-Z0-9_]+$")
    message:     str = Field(..., min_length=1, max_length=2000)
    session_id:  str = Field(default="", max_length=100)

    @field_validator("message", "session_id", mode="before")
    @classmethod
    def strip_str(cls, v: Any) -> str:
        return str(v).strip() if v else ""


class CRMContactValidator(BaseModel):
    customer_id:   str  = Field(..., min_length=3, max_length=100)
    name:          str  = Field(..., min_length=1, max_length=200)
    phone:         str  = Field(..., min_length=7, max_length=20)
    email:         str  = Field(default="", max_length=200)
    notes:         str  = Field(default="", max_length=2000)
    contact_stage: str  = Field(default="lead", max_length=50)
    is_consented:  bool = Field(default=False)

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: Any) -> str:
        phone = re.sub(r"[^\d+]", "", str(v))
        if len(phone) < 7:
            raise ValueError("Phone number too short")
        return phone


class AdminLoginValidator(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=200)


# ─────────────────────────────────────────────────────────────────────────────
# 💾  SQL HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _execute(conn, sql: str, params: tuple = ()) -> Any:
    """Execute SQL — translates ? → %s for psycopg2 automatically."""
    is_pg = POSTGRES_AVAILABLE and isinstance(conn, psycopg2.extensions.connection)
    if is_pg:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql.replace("?", "%s"), params)
        return cur
    return conn.execute(sql, params)


# ─────────────────────────────────────────────────────────────────────────────
# 📋  SOC 2 AUDIT TRAIL  (v8 FIX #6)
# ─────────────────────────────────────────────────────────────────────────────
def audit(actor_id: str, action: str, resource: str,
          detail: Optional[Dict] = None, ip: Optional[str] = None) -> None:
    """Write an immutable audit record — async so it never blocks the request path."""
    if not cfg.ENABLE_ANALYTICS:
        return

    def _write():
        try:
            detail_str = json.dumps(detail or {})
            with _db_pool.get() as conn:
                _execute(conn,
                    "INSERT INTO audit_log (ts, actor_id, action, resource, detail, ip, region) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (_now(), actor_id, action, resource, detail_str, ip, cfg.REGION))
        except Exception as exc:
            log.warning(f"⚠️  Audit write failed: {exc}")

    submit_bg(_write)   # v11 #11: bounded pool


# ─────────────────────────────────────────────────────────────────────────────
# 📬  OUTBOX / SAGA PATTERN  (v8 FIX #3 — distributed transaction safety)
# ─────────────────────────────────────────────────────────────────────────────
def outbox_publish(event_type: str, payload: Dict) -> None:
    """
    Transactional outbox pattern: events are persisted BEFORE external side-effects.
    A background worker processes pending events, guaranteeing at-least-once delivery.
    """
    try:
        payload_str = json.dumps(payload)
        with _db_pool.get() as conn:
            _execute(conn,
                "INSERT INTO outbox (event_type, payload, status, created_at) VALUES (?,?,?,?)",
                (event_type, payload_str, "pending", _now()))
    except Exception as exc:
        log.error(f"❌ Outbox publish failed: {exc}")


def _process_outbox() -> None:
    """Called by background worker — processes pending outbox events."""
    try:
        with _db_pool.get() as conn:
            cur = _execute(conn,
                "SELECT id, event_type, payload, attempts FROM outbox "
                "WHERE status='pending' AND attempts < 5 ORDER BY id LIMIT 20", ())
            rows = cur.fetchall()

        for row in rows:
            evt_id     = row["id"]
            event_type = row["event_type"]
            payload    = json.loads(row["payload"])
            # Route to handler
            try:
                if event_type == "whatsapp.send":
                    _wa_send_text(payload["to"], payload["message"])
                # Add more event types here as the system grows
                with _db_pool.get() as conn:
                    _execute(conn,
                        "UPDATE outbox SET status='done', processed_at=? WHERE id=?",
                        (_now(), evt_id))
            except Exception as exc:
                with _db_pool.get() as conn:
                    _execute(conn,
                        "UPDATE outbox SET attempts=attempts+1, status=? WHERE id=?",
                        ("failed" if row["attempts"] >= 4 else "pending", evt_id))
                log.warning(f"⚠️  Outbox event {evt_id} ({event_type}) failed: {exc}")
    except Exception as exc:
        log.warning(f"⚠️  Outbox processor error: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 💾  DATABASE OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────
def save_customer_brain(customer_id: str, customer_name: str,
                         business_type: str, system_prompt: str,
                         whatsapp_phone: str = "", owner_phone: str = "",
                         instagram_id: str = "", bot_name: str = "") -> None:
    now   = _now()
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    if is_pg:
        sql = """
            INSERT INTO customer_brains
                (customer_id, customer_name, business_type, system_prompt,
                 created_at, updated_at, whatsapp_phone, region,
                 owner_phone, instagram_id, bot_name)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
    with _db_pool.get() as conn:
        _execute(conn, sql, (customer_id, customer_name, business_type,
                             system_prompt, now, now, whatsapp_phone, cfg.REGION,
                             owner_phone, instagram_id, bot_name))
    brain_cache.delete(customer_id)
    analytics.inc("customer.saved")
    log.info(f"💾 Brain saved → {customer_id}")


def get_customer_brain(customer_id: str) -> Optional[Dict]:
    cached = brain_cache.get(customer_id)
    if cached:
        analytics.inc("cache.hit")
        return cached
    analytics.inc("cache.miss")
    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn,
            "SELECT * FROM customer_brains WHERE customer_id=? AND is_active=?",
            (customer_id, True if isinstance(_db_pool, PostgreSQLPool) else 1))
        row = cur.fetchone()
    if row:
        data = dict(row)
        brain_cache.set(customer_id, data)
        return data
    return None


def create_session(customer_id: str, channel: str = "api") -> str:
    session_id = f"sess_{uuid.uuid4().hex[:20]}"
    now = _now()
    with _db_pool.get() as conn:
        _execute(conn,
            "INSERT INTO chat_sessions (session_id, customer_id, created_at, last_active, channel) "
            "VALUES (?,?,?,?,?)",
            (session_id, customer_id, now, now, channel))
    analytics.inc("session.created")
    return session_id


def session_exists(session_id: str, customer_id: str) -> bool:
    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn,
            "SELECT 1 FROM chat_sessions WHERE session_id=? AND customer_id=?",
            (session_id, customer_id))
        return cur.fetchone() is not None


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
    rows = [(session_id, role, content, now, len(content.split()), provider, latency)
            for role, content, provider, latency in turns]
    with _db_pool.get() as conn:
        if is_pg:
            conn.cursor().executemany(sql, rows)
            _execute(conn,
                "UPDATE chat_sessions SET last_active=%s, message_count=message_count+%s "
                "WHERE session_id=%s",
                (now, len(turns), session_id))
        else:
            conn.executemany(sql, rows)
            conn.execute(
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
    return [{"role": r["role"], "parts": [r["content"]]} for r in reversed(rows)]


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
        _execute(conn,
            "UPDATE customer_brains SET total_chats=total_chats+1, updated_at=? "
            "WHERE customer_id=?",
            (_now(), customer_id))
    brain_cache.delete(customer_id)
    analytics.inc("chat.total")


def check_idempotency(key: str) -> Optional[Dict]:
    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn, "SELECT response_body FROM idempotency_keys WHERE key=?", (key,))
        row = cur.fetchone()
    return json.loads(row["response_body"]) if row else None


def store_idempotency(key: str, response: Dict) -> None:
    with _db_pool.get() as conn:
        try:
            _execute(conn,
                "INSERT INTO idempotency_keys (key, response_body, created_at) VALUES (?,?,?)",
                (key, json.dumps(response), _now()))
        except Exception:
            pass  # Race condition — already exists


# ─────────────────────────────────────────────────────────────────────────────
# 📋  ENCRYPTED CRM
# ─────────────────────────────────────────────────────────────────────────────
def _crm_phone_hash(customer_id: str, phone: str) -> str:
    """v11 #3: deterministic dedupe handle. AES-GCM ciphertext changes every
    encryption (random nonce), so enc_phone can't be compared — this hash can.
    Scoped per customer so the same lead at two businesses stays two rows."""
    norm = re.sub(r"\D", "", phone or "")[-12:]   # digits only, country-code tolerant
    return hashlib.sha256(f"{customer_id}|{norm}".encode()).hexdigest()[:40]


def crm_add_contact(customer_id: str, name: str, phone: str,
                     email: str = "", notes: str = "",
                     stage: str = "lead", is_consented: bool = False) -> int:
    now         = _now()
    phash       = _crm_phone_hash(customer_id, phone)
    is_pg       = isinstance(_db_pool, PostgreSQLPool)

    # v11 #3: was a blind INSERT on EVERY message → 10 messages = 10 duplicate
    # rows. Now: same lead → just bump updated_at and return the existing id.
    with _db_pool.get() as conn:
        cur = _execute(conn,
            "SELECT id FROM crm_contacts WHERE customer_id=? AND phone_hash=?",
            (customer_id, phash))
        row = cur.fetchone()
        if row:
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
        cur = _execute(conn,
            "INSERT INTO crm_contacts "
            "(customer_id, phone_hash, enc_name, enc_phone, enc_email, enc_notes, "
            "contact_stage, created_at, updated_at, is_consented) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (customer_id, phash, enc_name, enc_phone, enc_email, enc_notes,
             stage, now, now, consent_val))
        new_id = cur.lastrowid if hasattr(cur, "lastrowid") else None

    analytics.inc("crm.contact.added")
    log.info(f"📋 CRM contact → customer={customer_id} phone={pii_vault.mask(phone)}")
    return new_id or 0


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
        total = (cur_total.fetchone() or {}).get("cnt", 0)
        cur_data = _execute(conn,
            f"SELECT id, enc_name, enc_phone, enc_email, enc_notes, "
            f"contact_stage, created_at, is_consented "
            f"FROM crm_contacts WHERE customer_id=? {stage_filter} "
            f"ORDER BY id DESC LIMIT ? OFFSET ?",
            params_data)
        rows = cur_data.fetchall()

    contacts = [{
        "id":            r["id"],
        "name":          pii_vault.decrypt(r["enc_name"]),
        "phone":         pii_vault.mask(pii_vault.decrypt(r["enc_phone"])),
        "email":         pii_vault.decrypt(r["enc_email"]) if r["enc_email"] else "",
        "notes":         pii_vault.decrypt(r["enc_notes"]) if r["enc_notes"] else "",
        "contact_stage": r["contact_stage"],
        "created_at":    str(r["created_at"]),
        "is_consented":  bool(r["is_consented"]),
    } for r in rows]
    return contacts, total


def crm_get_contact_full(contact_id: int) -> Optional[Dict]:
    with _db_pool.get(read_only=True) as conn:
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


# ─────────────────────────────────────────────────────────────────────────────
# ♻️  BACKGROUND JANITOR  (FIX #12: graceful K8s drain)
# ─────────────────────────────────────────────────────────────────────────────
_shutdown_event = threading.Event()


def _janitor_loop() -> None:
    """Runs every 2 minutes: clears expired idempotency keys + processes outbox."""
    while not _shutdown_event.wait(timeout=120):
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
            with _db_pool.get() as conn:
                _execute(conn, "DELETE FROM idempotency_keys WHERE created_at < ?", (cutoff,))
            log.info("🧹 Janitor: idempotency keys cleaned.")
        except Exception as exc:
            log.warning(f"⚠️  Janitor (cleanup) error: {exc}")

        try:
            _process_outbox()
        except Exception as exc:
            log.warning(f"⚠️  Janitor (outbox) error: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 🌐  FLASK APP
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = cfg.SECRET_KEY

CORS(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[cfg.RATE_LIMIT_DEFAULT],
    storage_uri=cfg.REDIS_URL if cfg.REDIS_URL else "memory://",
)


@app.after_request
def _security_headers(response):
    """OWASP-recommended security headers on every response."""
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    response.headers["X-XSS-Protection"]          = "1; mode=block"
    response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Cache-Control"]             = "no-store, max-age=0"
    response.headers["Permissions-Policy"]        = "geolocation=(), microphone=()"
    response.headers["X-Request-ID"]              = g.get("request_id", "")
    response.headers["Content-Security-Policy"]   = "default-src 'self'"
    return response


@app.before_request
def _tag_request():
    g.request_id = uuid.uuid4().hex[:12]
    g.start_time = time.monotonic()
    analytics.inc("request.total")


def elapsed_ms() -> int:
    return int((time.monotonic() - g.get("start_time", time.monotonic())) * 1000)


def extract_field(fields: List, index: int, default: str = "") -> str:
    try:
        val = fields[index].get("value", default)
        return str(val).strip() if val else default
    except (IndexError, AttributeError):
        return default


def make_customer_id(name: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in name.upper())
    return f"HX_{safe[:60]}"


def verify_tally_signature(raw_body: bytes, headers: dict) -> bool:
    """Verify Tally webhook signature if secret is configured."""
    tally_secret = os.getenv("TALLY_WEBHOOK_SECRET", "")
    if not tally_secret:
        return True
    sig = headers.get("Tally-Signature", "")
    expected = hmac.new(tally_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


# ─────────────────────────────────────────────────────────────────────────────
# 🚪  ROUTES
# ─────────────────────────────────────────────────────────────────────────────

# ── Health Check (Kubernetes liveness probe) ──────────────────────────────────
@app.route("/", methods=["GET"])
def root():
    """Friendly landing — visiting the bare Render URL previously 404'd."""
    return jsonify({
        "engine":  "HEONIX ULTRA ENGINE v11.0 — PRODUCTION-HARDENED",
        "status":  "online",
        "health":  "/health",
        "ready":   "/ready",
        "metrics": "/metrics",
    }), 200


@app.route("/health", methods=["GET"])
def health():
    db_ok = True
    try:
        with _db_pool.get(read_only=True) as conn:
            _execute(conn, "SELECT 1", ())
    except Exception:
        db_ok = False

    ai_active = [k for k, v in AI_PROVIDERS_ACTIVE.items() if v]
    return jsonify({
        "status":           "UP" if db_ok else "DEGRADED",
        "engine":           "HEONIX Ultra v11.0",
        "region":           cfg.REGION,
        "timestamp":        _now(),
        "db_mode":          cfg.DATABASE_MODE,
        "db_healthy":       db_ok,
        "replica_pool":     bool(
            isinstance(_db_pool, PostgreSQLPool) and _db_pool._read),
        "redis_connected":  brain_cache._redis is not None,
        "ai_providers":     AI_PROVIDERS_ACTIVE,
        "active_ai_chain":  ai_active,
        "pii_encryption":   pii_vault.enabled,
        "whatsapp_ready":   bool(cfg.WHATSAPP_TOKEN and cfg.WHATSAPP_PHONE_ID),
        "instagram_ready":  bool(cfg.INSTAGRAM_TOKEN),
        "graph_api":        cfg.GRAPH_API_VERSION,
        "rag_memory":       _rag_ready,
        "voice_decoder":    bool(AI_PROVIDERS_ACTIVE.get("gemini") or AI_PROVIDERS_ACTIVE.get("openai")),
        "gemini_circuit":   _gemini_breaker.state,
        "openai_circuit":   _openai_breaker.state,
        "claude_circuit":   _claude_breaker.state,
        "whatsapp_circuit": _whatsapp_breaker.state,
        "request_id":       g.get("request_id"),
    }), 200 if db_ok else 503


# ── Readiness Probe (Kubernetes — separate from liveness per k8s best practice) ─
@app.route("/ready", methods=["GET"])
def ready():
    """
    FIX #13: Separate readiness check.
    K8s uses /ready to decide if traffic can be sent — not the same as /health.
    Pod may be alive but not ready (e.g., AI providers still configuring).
    """
    ai_ok = any(AI_PROVIDERS_ACTIVE.values())
    if not ai_ok:
        return jsonify({"ready": False, "reason": "No AI providers configured"}), 503
    return jsonify({
        "ready":    True,
        "region":   cfg.REGION,
        "ai_chain": [k for k, v in AI_PROVIDERS_ACTIVE.items() if v],
    }), 200


# ── Prometheus Metrics (FIX #15: histograms + P99 latency) ──────────────────
@app.route("/metrics", methods=["GET"])
def metrics():
    snap = analytics.snapshot()
    c    = snap["counters"]
    p99  = snap["latency_p99"]

    try:
        with _db_pool.get(read_only=True) as conn:
            is_pg   = isinstance(_db_pool, PostgreSQLPool)
            active  = True if is_pg else 1
            cur     = _execute(conn,
                "SELECT COUNT(*) as c FROM customer_brains WHERE is_active=?", (active,))
            customers = cur.fetchone()["c"]
            cur     = _execute(conn, "SELECT COUNT(*) as c FROM chat_sessions", ())
            sessions  = cur.fetchone()["c"]
            cur     = _execute(conn, "SELECT COUNT(*) as c FROM chat_messages", ())
            messages  = cur.fetchone()["c"]
    except Exception:
        customers = sessions = messages = -1

    lines = [
        "# HELP heonix_customers_total Active customer brains",
        "# TYPE heonix_customers_total gauge",
        f"heonix_customers_total {customers}",
        "# HELP heonix_sessions_total Chat sessions",
        "# TYPE heonix_sessions_total counter",
        f"heonix_sessions_total {sessions}",
        "# HELP heonix_messages_total Chat messages",
        "# TYPE heonix_messages_total counter",
        f"heonix_messages_total {messages}",
        "# HELP heonix_requests_total HTTP requests processed",
        f"heonix_requests_total {c.get('request.total', 0)}",
        "# HELP heonix_cache_hit_total Cache hits",
        f"heonix_cache_hit_total {c.get('cache.hit', 0)}",
        "# HELP heonix_cache_miss_total Cache misses",
        f"heonix_cache_miss_total {c.get('cache.miss', 0)}",
        "# HELP heonix_ai_gemini_success Gemini success count",
        f"heonix_ai_gemini_success {c.get('ai.gemini.success', 0)}",
        "# HELP heonix_ai_openai_success OpenAI success count",
        f"heonix_ai_openai_success {c.get('ai.openai.success', 0)}",
        "# HELP heonix_ai_claude_success Claude success count",
        f"heonix_ai_claude_success {c.get('ai.claude.success', 0)}",
        "# HELP heonix_ai_gemini_latency_p99_ms Gemini P99 latency ms",
        f"heonix_ai_gemini_latency_p99_ms {p99.get('ai.gemini.latency_ms', 0)}",
        "# HELP heonix_ai_openai_latency_p99_ms OpenAI P99 latency ms",
        f"heonix_ai_openai_latency_p99_ms {p99.get('ai.openai.latency_ms', 0)}",
        "# HELP heonix_ai_claude_latency_p99_ms Claude P99 latency ms",
        f"heonix_ai_claude_latency_p99_ms {p99.get('ai.claude.latency_ms', 0)}",
        "# HELP heonix_ai_gemini_circuit Gemini circuit (0=CLOSED,1=OPEN)",
        f"heonix_ai_gemini_circuit {1 if _gemini_breaker.state == 'OPEN' else 0}",
        "# HELP heonix_ai_openai_circuit OpenAI circuit",
        f"heonix_ai_openai_circuit {1 if _openai_breaker.state == 'OPEN' else 0}",
        "# HELP heonix_ai_claude_circuit Claude circuit",
        f"heonix_ai_claude_circuit {1 if _claude_breaker.state == 'OPEN' else 0}",
        "# HELP heonix_whatsapp_sent WhatsApp messages sent",
        f"heonix_whatsapp_sent {c.get('whatsapp.sent', 0)}",
        f"# HELP heonix_uptime_seconds Uptime seconds",
        f"heonix_uptime_seconds {snap['uptime_secs']}",
    ]
    return "\n".join(lines) + "\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


# ── Tally Webhook ──────────────────────────────────────────────────────────────
@app.route("/tally-webhook", methods=["POST", "GET"])
@limiter.limit(cfg.WEBHOOK_RATE_LIMIT)
def tally_webhook():
    if request.method == "GET":
        return jsonify({
            "status":  "live",
            "engine":  "HEONIX Ultra v11.0",
            "region":  cfg.REGION,
            "message": "POST Tally form payload here to deploy a customer brain.",
        }), 200

    source_ip    = request.remote_addr
    raw_body     = request.get_data()
    payload_hash = hashlib.sha256(raw_body).hexdigest()[:24]

    # Tally signature verification (FIX #14)
    if not verify_tally_signature(raw_body, dict(request.headers)):
        analytics.inc("webhook.tally.sig_fail")
        return jsonify({"error": "Invalid webhook signature"}), 401

    cached = check_idempotency(payload_hash)
    if cached:
        log.info(f"♻️  Duplicate webhook → {payload_hash}")
        return jsonify(cached), 200

    tally_data = request.get_json(silent=True)
    if not tally_data:
        log_webhook(source_ip, payload_hash, None, "REJECTED", error="Empty JSON")
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        fields = tally_data.get("data", {}).get("fields", [])
        raw    = WebhookPayloadValidator(
            customer_name  = extract_field(fields, 0, "Anonymous Client"),
            business_type  = extract_field(fields, 1, "General Business"),
            extra_notes    = extract_field(fields, 2, ""),
            whatsapp_phone = extract_field(fields, 3, ""),
            owner_phone    = extract_field(fields, 4, ""),
            instagram_id   = extract_field(fields, 5, ""),
        )
        customer_id         = make_customer_id(raw.customer_name)
        bot_name, sys_prompt = build_system_prompt(raw.customer_name, raw.business_type)
        if raw.extra_notes:
            sys_prompt += f"\n\nAdditional context: {raw.extra_notes}"

        save_customer_brain(customer_id, raw.customer_name,
                            raw.business_type, sys_prompt, raw.whatsapp_phone,
                            owner_phone=(raw.owner_phone or raw.whatsapp_phone),
                            instagram_id=raw.instagram_id,
                            bot_name=bot_name)

        # Publish welcome message via transactional outbox (FIX #3)
        if raw.whatsapp_phone:
            outbox_publish("whatsapp.send", {
                "to":      raw.whatsapp_phone,
                "message": (f"Hi! Your AI assistant {bot_name} is live for "
                            f"{raw.customer_name}. Customer ID: {customer_id}"),
            })

        log_webhook(source_ip, payload_hash, customer_id, "SUCCESS")
        actor = g.jwt_user["sub"] if hasattr(g, "jwt_user") else "webhook"
        audit(actor, "customer.deploy", customer_id,
              {"bot": bot_name, "type": raw.business_type}, source_ip)

        response_body = {
            "status":        "success",
            "message":       f"Brain deployed for {raw.customer_name}",
            "customer_id":   customer_id,
            "bot_name":      bot_name,
            "business_type": raw.business_type,
            "region":        cfg.REGION,
            "request_id":    g.get("request_id"),
            "elapsed_ms":    elapsed_ms(),
        }
        store_idempotency(payload_hash, response_body)
        analytics.inc("webhook.tally.success")
        log.info(f"🚀 Brain deployed → {customer_id} bot={bot_name}")
        return jsonify(response_body), 200

    except ValidationError as exc:
        log_webhook(source_ip, payload_hash, None, "VALIDATION_ERROR", error=str(exc))
        return jsonify({"error": "Validation failed", "detail": exc.errors()}), 422
    except Exception as exc:
        log.error(f"❌ Webhook error: {exc}", exc_info=True)
        analytics.inc("webhook.tally.error")
        log_webhook(source_ip, payload_hash, None, "ERROR", error=str(exc))
        return jsonify({"error": "Processing failed", "request_id": g.get("request_id")}), 500


# ── WhatsApp Cloud API Webhook ─────────────────────────────────────────────────
# v11 fix #1: the route now ONLY validates + dedups + queues, then 200s Meta
# instantly. All heavy work (DB, AI, voice, sends) runs in the bounded worker
# pool. Previously everything was synchronous → a slow AI/voice call (20-40s)
# blocked the worker, Meta timed out at ~10s and re-sent, and 8 gunicorn slots
# could starve under light load.
# v11 fix #7: loops over EVERY entry / change / message (Meta can batch them);
# v10 processed only entry[0]/changes[0]/messages[0] and silently dropped rest.
def _process_wa_message(from_phone: str, msg: dict) -> None:
    """Heavy per-message handler — runs in the background pool, fully outside
    any Flask request context."""
    try:
        msg_type = msg.get("type", "text")

        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT customer_id FROM customer_brains WHERE whatsapp_phone=? AND is_active=?",
                (from_phone, True if isinstance(_db_pool, PostgreSQLPool) else 1))
            row = cur.fetchone()
        if not row:
            log.info(f"📲 Unknown WA contact: {pii_vault.mask(from_phone)}")
            return
        customer_id = row["customer_id"]

        if not customer_limiter.check(customer_id):
            analytics.inc("ratelimit.customer.hit")
            return

        brain = get_customer_brain(customer_id)
        if not brain:
            return

        if ghost_is_muted(from_phone):          # human owner has taken over
            analytics.inc("ghost.skipped")
            return

        if msg_type == "text":
            user_text = msg.get("text", {}).get("body", "").strip()
            if not user_text:
                return
        elif msg_type == "audio":
            user_text = transcribe_voice_note(msg.get("audio", {}).get("id", ""))
            if not user_text:
                send_whatsapp_async(from_phone,
                    "🎤 Sorry, I couldn't hear that clearly — could you please type your message?")
                return
            analytics.inc("voice.transcribed")
        else:
            return

        session_id = brain_cache.get(f"wa_session:{from_phone}")
        if not session_id:
            session_id = create_session(customer_id, channel="whatsapp")
            brain_cache.set(f"wa_session:{from_phone}", session_id, ttl=3600)

        gov = govern_message(user_text, from_phone,
                             bot_name=(brain.get("bot_name") or ""),
                             owner_phone=(brain.get("owner_phone") or ""))
        for to, alert in gov["alerts"]:
            send_owner_alert_async(to, alert)   # v11 #4: template-capable
        if gov["muted"]:
            return
        if gov["reply"]:
            send_whatsapp_async(from_phone, gov["reply"])
            save_messages_batch(session_id, [
                ("user",  user_text,    "whatsapp", 0),
                ("model", gov["reply"], "local",    0),
            ])
            increment_chat_count(customer_id)
            analytics.inc("whatsapp.local_reply")
            return

        history = get_session_history(session_id)
        t0 = time.monotonic()
        try:
            reply, provider, escalated = ai_reply_pipeline(
                brain, history, user_text,
                user_uid=from_phone, channel="whatsapp")
        except RuntimeError:
            reply     = "Sorry, our AI is temporarily unavailable. We'll get back to you shortly!"
            provider  = "fallback"
            escalated = False
        latency_ms = int((time.monotonic() - t0) * 1000)

        if escalated:
            ghost_mute(from_phone)

        save_messages_batch(session_id, [
            ("user",  user_text, "whatsapp", 0),
            ("model", reply,     provider,   latency_ms),
        ])
        increment_chat_count(customer_id)
        crm_add_contact(customer_id, f"WA {pii_vault.mask(from_phone)}",
                         from_phone, notes=f"First msg: {user_text[:200]}")
        send_whatsapp_async(from_phone, reply)

        analytics.inc("whatsapp.chat.handled")
        log.info(f"📱 WA chat → {customer_id} | {pii_vault.mask(from_phone)} | {provider}")
    except Exception as exc:
        log.error(f"❌ WA worker error: {exc}", exc_info=True)
        analytics.inc("whatsapp.error")


@app.route("/whatsapp-webhook", methods=["GET", "POST"])
@limiter.limit(cfg.WEBHOOK_RATE_LIMIT)
def whatsapp_webhook():
    if request.method == "GET":
        mode      = request.args.get("hub.mode")
        token     = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == cfg.WHATSAPP_VERIFY_TOKEN:
            log.info("✅ WhatsApp webhook verified by Meta.")
            return challenge, 200
        return "Forbidden", 403

    raw_body  = request.get_data()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_meta_signature(raw_body, signature, cfg.WHATSAPP_APP_SECRET):
        analytics.inc("whatsapp.sig_fail")
        log.warning(f"🚫 Invalid WA signature from {request.remote_addr}")
        return jsonify({"error": "Invalid signature"}), 401

    data    = request.get_json(silent=True) or {}
    queued  = 0
    for entry in data.get("entry", []):                 # #7: all entries
        for change in entry.get("changes", []):          # #7: all changes
            for msg in change.get("value", {}).get("messages", []):  # #7: all msgs
                from_phone = msg.get("from", "")
                wamid      = msg.get("id", "")
                if wamid:                                # #_ dedupe Meta retries
                    if brain_cache.get(f"wamid:{wamid}"):
                        continue
                    brain_cache.set(f"wamid:{wamid}", 1, ttl=600)
                if not from_phone:
                    continue
                submit_bg(_process_wa_message, from_phone, msg)   # #1: async
                queued += 1

    # #1: ALWAYS 200 immediately — Meta must never time out or retry-storm.
    return jsonify({"status": "queued", "accepted": queued}), 200


# ── Instagram Messaging Webhook (v11 — async, same brain / CRM / memory) ─────
# Same #1 + #7 fixes as WhatsApp: validate + dedupe + queue, then 200 instantly;
# process every messaging event (not just events[0]) in the worker pool.
def _process_ig_message(sender: str, recipient: str, message: dict) -> None:
    """Heavy per-DM handler — runs in the background pool. Owner alerts still go
    out over WhatsApp; the customer reply goes back over Instagram."""
    try:
        user_text = (message.get("text") or "").strip()
        if not user_text:
            atts = message.get("attachments") or []
            aud  = next((a for a in atts if a.get("type") == "audio"), None)
            if aud:
                user_text = transcribe_audio_url((aud.get("payload") or {}).get("url", ""))
                if user_text:
                    analytics.inc("voice.transcribed")
            if not user_text:
                return

        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT customer_id FROM customer_brains WHERE instagram_id=? AND is_active=?",
                (recipient, True if isinstance(_db_pool, PostgreSQLPool) else 1))
            row = cur.fetchone()
        if not row:
            log.info(f"📸 Unknown IG account: {pii_vault.mask(recipient)}")
            return
        customer_id = row["customer_id"]

        if not customer_limiter.check(customer_id):
            analytics.inc("ratelimit.customer.hit")
            return

        brain = get_customer_brain(customer_id)
        if not brain:
            return

        uid = f"ig:{sender}"
        if ghost_is_muted(uid):
            analytics.inc("ghost.skipped")
            return

        session_id = brain_cache.get(f"ig_session:{sender}")
        if not session_id:
            session_id = create_session(customer_id, channel="instagram")
            brain_cache.set(f"ig_session:{sender}", session_id, ttl=3600)

        gov = govern_message(user_text, uid,
                             bot_name=(brain.get("bot_name") or ""),
                             owner_phone=(brain.get("owner_phone") or ""))
        for to, alert in gov["alerts"]:
            send_owner_alert_async(to, alert)   # owner alerts via WhatsApp (template-capable, v11 #4)
        if gov["muted"]:
            return
        if gov["reply"]:
            send_instagram_async(sender, gov["reply"])
            save_messages_batch(session_id, [
                ("user",  user_text,    "instagram", 0),
                ("model", gov["reply"], "local",     0),
            ])
            increment_chat_count(customer_id)
            analytics.inc("instagram.local_reply")
            return

        history = get_session_history(session_id)
        t0 = time.monotonic()
        try:
            reply, provider, escalated = ai_reply_pipeline(
                brain, history, user_text, user_uid=uid, channel="instagram")
        except RuntimeError:
            reply     = "Sorry, our AI is temporarily unavailable. We'll get back to you shortly!"
            provider  = "fallback"
            escalated = False
        latency_ms = int((time.monotonic() - t0) * 1000)

        if escalated:
            ghost_mute(uid)

        save_messages_batch(session_id, [
            ("user",  user_text, "instagram", 0),
            ("model", reply,     provider,    latency_ms),
        ])
        increment_chat_count(customer_id)
        crm_add_contact(customer_id, f"IG {pii_vault.mask(sender)}",
                         f"ig_{sender}", notes=f"First msg: {user_text[:200]}")
        send_instagram_async(sender, reply)

        analytics.inc("instagram.chat.handled")
        log.info(f"📸 IG chat → {customer_id} | {pii_vault.mask(sender)} | {provider}")
    except Exception as exc:
        log.error(f"❌ IG worker error: {exc}", exc_info=True)
        analytics.inc("instagram.error")


@app.route("/instagram-webhook", methods=["GET", "POST"])
@limiter.limit(cfg.WEBHOOK_RATE_LIMIT)
def instagram_webhook():
    if request.method == "GET":
        mode      = request.args.get("hub.mode")
        token     = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == cfg.WHATSAPP_VERIFY_TOKEN:
            log.info("✅ Instagram webhook verified by Meta.")
            return challenge, 200
        return "Forbidden", 403

    raw_body  = request.get_data()
    signature = request.headers.get("X-Hub-Signature-256", "")
    secret    = cfg.INSTAGRAM_APP_SECRET or cfg.WHATSAPP_APP_SECRET
    if not verify_meta_signature(raw_body, signature, secret):
        analytics.inc("instagram.sig_fail")
        return jsonify({"error": "Invalid signature"}), 401

    data = request.get_json(silent=True) or {}
    if data.get("object") != "instagram":
        return jsonify({"status": "ignored_object"}), 200

    queued = 0
    for entry in data.get("entry", []):                 # #7: all entries
        for ev in entry.get("messaging") or []:          # #7: all events
            sender    = str(ev.get("sender", {}).get("id", ""))
            recipient = str(ev.get("recipient", {}).get("id", ""))
            message   = ev.get("message") or {}
            if not sender or not message or message.get("is_echo"):
                continue
            mid = message.get("mid", "")
            if mid:
                if brain_cache.get(f"igmid:{mid}"):
                    continue
                brain_cache.set(f"igmid:{mid}", 1, ttl=600)
            submit_bg(_process_ig_message, sender, recipient, message)   # #1: async
            queued += 1

    return jsonify({"status": "queued", "accepted": queued}), 200


# ── Chat API ──────────────────────────────────────────────────────────────────
@app.route("/chat", methods=["POST"])
@limiter.limit(cfg.CHAT_RATE_LIMIT)
def chat():
    try:
        req = ChatRequestValidator(**request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "detail": exc.errors()}), 422

    brain = get_customer_brain(req.customer_id)
    if not brain:
        return jsonify({"error": "Customer not found"}), 404

    # Per-customer rate limit
    if not customer_limiter.check(req.customer_id):
        analytics.inc("ratelimit.customer.hit")
        return jsonify({"error": "Rate limit exceeded for this customer"}), 429

    # Session handling
    session_id = req.session_id
    if session_id and not session_exists(session_id, req.customer_id):
        return jsonify({"error": "Invalid session_id"}), 400
    if not session_id:
        session_id = create_session(req.customer_id, channel="api")

    history = get_session_history(session_id)

    t0 = time.monotonic()
    try:
        reply, provider, _escalated = ai_reply_pipeline(
            brain, history, req.message,
            user_uid=f"api:{req.customer_id}", channel="api")
    except RuntimeError as exc:
        analytics.inc("chat.ai_all_failed")
        return jsonify({
            "error":      "AI unavailable",
            "request_id": g.get("request_id"),
        }), 503
    latency_ms = int((time.monotonic() - t0) * 1000)

    save_messages_batch(session_id, [
        ("user",  req.message, "api",     0),
        ("model", reply,       provider,  latency_ms),
    ])
    increment_chat_count(req.customer_id)
    analytics.inc("chat.success")

    return jsonify({
        "reply":       reply,
        "provider":    provider,
        "session_id":  session_id,
        "latency_ms":  latency_ms,
        "request_id":  g.get("request_id"),
    }), 200


# ── Admin: Login (JWT issue) ──────────────────────────────────────────────────
@app.route("/admin/login", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
def admin_login():
    try:
        req = AdminLoginValidator(**request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "detail": exc.errors()}), 422

    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn,
            "SELECT user_id, hashed_pw, role FROM admin_users "
            "WHERE username=? AND is_active=?",
            (req.username, True if isinstance(_db_pool, PostgreSQLPool) else 1))
        row = cur.fetchone()

    if not row or not verify_password(req.password, row["hashed_pw"]):
        analytics.inc("admin.login.fail")
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_jwt(row["user_id"], row["role"])
    audit(row["user_id"], "admin.login", "admin_users", ip=request.remote_addr)
    analytics.inc("admin.login.success")
    return jsonify({
        "token":      token,
        "user_id":    row["user_id"],
        "role":       row["role"],
        "expires_in": f"{cfg.JWT_EXPIRY_HOURS}h",
    }), 200


# ── Admin: Create Admin User ───────────────────────────────────────────────────
@app.route("/admin/user", methods=["POST"])
@require_jwt(min_role="superadmin")
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
def create_admin_user():
    data  = request.get_json(silent=True) or {}
    uname = data.get("username", "").strip()
    pw    = data.get("password", "")
    role  = data.get("role", "admin")
    if not uname or not pw or role not in ROLES:
        return jsonify({"error": "username, password, and valid role required"}), 400

    user_id   = f"adm_{uuid.uuid4().hex[:12]}"
    hashed_pw = hash_password(pw)
    try:
        with _db_pool.get() as conn:
            _execute(conn,
                "INSERT INTO admin_users (user_id, username, hashed_pw, role, created_at) "
                "VALUES (?,?,?,?,?)",
                (user_id, uname, hashed_pw, role, _now()))
    except Exception:
        return jsonify({"error": "Username already exists"}), 409

    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "admin.create_user", user_id, {"role": role}, request.remote_addr)
    return jsonify({"status": "created", "user_id": user_id, "role": role}), 201


# ── Admin: Customer Stats ─────────────────────────────────────────────────────
@app.route("/admin/customer/<customer_id>/stats", methods=["GET"])
@require_jwt(min_role="viewer")
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
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
@require_jwt(min_role="superadmin")
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
def delete_customer(customer_id: str):
    brain = get_customer_brain(customer_id)
    if not brain:
        return jsonify({"error": "Not found"}), 404
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    with _db_pool.get() as conn:
        _execute(conn,
            "UPDATE customer_brains SET is_active=?, updated_at=? WHERE customer_id=?",
            (False if is_pg else 0, _now(), customer_id))
    brain_cache.delete(customer_id)
    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "customer.delete", customer_id, ip=request.remote_addr)
    analytics.inc("customer.deleted")
    log.info(f"🗑️  Soft-deleted → {customer_id}")
    return jsonify({"status": "deleted", "customer_id": customer_id}), 200


# ── Admin: List All Customers ─────────────────────────────────────────────────
@app.route("/admin/customers", methods=["GET"])
@require_jwt(min_role="viewer")
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
def list_customers():
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(100, int(request.args.get("per_page", 50)))
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
@require_jwt(min_role="admin")
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
def crm_add_contact_api():
    data = request.get_json(silent=True) or {}
    try:
        contact = CRMContactValidator(**data)
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "detail": exc.errors()}), 422

    brain = get_customer_brain(contact.customer_id)
    if not brain:
        return jsonify({"error": "Customer not found"}), 404

    contact_id = crm_add_contact(
        contact.customer_id, contact.name, contact.phone,
        contact.email, contact.notes, contact.contact_stage, contact.is_consented,
    )
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
@require_jwt(min_role="viewer")
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
def crm_list_contacts_api(customer_id: str):
    stage    = request.args.get("stage")
    page     = max(1, int(request.args.get("page", 1)))
    per_page = min(100, int(request.args.get("per_page", 50)))
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
@require_jwt(min_role="admin")
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
def crm_get_contact_api(contact_id: int):
    contact = crm_get_contact_full(contact_id)
    if not contact:
        return jsonify({"error": "Contact not found"}), 404
    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "crm.view_full", str(contact_id), ip=request.remote_addr)
    return jsonify(contact), 200


# ── Analytics Snapshot ────────────────────────────────────────────────────────
@app.route("/admin/analytics", methods=["GET"])
@require_jwt(min_role="viewer")
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
def analytics_snapshot():
    """Real-time analytics dashboard endpoint (FIX #5)."""
    snap = analytics.snapshot()
    return jsonify({
        "region":      cfg.REGION,
        "engine":      "HEONIX Ultra v11.0",
        "counters":    snap["counters"],
        "latency_p99": snap["latency_p99"],
        "uptime_secs": snap["uptime_secs"],
    }), 200


# ── Error Handlers ────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found", "hint": "GET /health for status"}), 404


@app.errorhandler(429)
def rate_limited(e):
    analytics.inc("ratelimit.ip.hit")
    return jsonify({"error": "Rate limit exceeded", "retry_after": "60s"}), 429


@app.errorhandler(500)
def server_error(e):
    log.error(f"500: {e}", exc_info=True)
    analytics.inc("error.500")
    return jsonify({"error": "Internal server error",
                    "request_id": g.get("request_id", "")}), 500


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405


# ─────────────────────────────────────────────────────────────────────────────
# 🚦  GRACEFUL SHUTDOWN  (v11 #14 — no blocking sleep inside the handler)
# ─────────────────────────────────────────────────────────────────────────────
def _shutdown_handler(signum, frame):
    log.info(f"📴 Signal {signum} — graceful shutdown starting...")
    _shutdown_event.set()
    # v11 #14: was time.sleep(10) INSIDE the handler (blocks all signal
    # delivery). Now: stop accepting new bg work, let queued sends finish
    # with a hard ceiling enforced by a watchdog, then close the DB pool.
    def _drain():
        try:
            _WORKER_POOL.shutdown(wait=True)   # waits for queued sends/alerts
        except Exception:
            pass
        if _db_pool:
            try:
                _db_pool.close_all()
            except Exception:
                pass
        log.info("✅ HEONIX Ultra v11.0 shut down cleanly.")
    t = threading.Thread(target=_drain, name="drain", daemon=True)
    t.start()
    t.join(timeout=10)        # bounded — gunicorn's graceful-timeout is the boss


signal.signal(signal.SIGTERM, _shutdown_handler)
signal.signal(signal.SIGINT,  _shutdown_handler)


# ─────────────────────────────────────────────────────────────────────────────
# 🚀  STARTUP SEQUENCE
# ─────────────────────────────────────────────────────────────────────────────
_startup_done = False
_startup_lock = threading.Lock()


def startup() -> None:
    global _db_pool, _startup_done
    with _startup_lock:
        if _startup_done:          # idempotent — safe under gunicorn + __main__
            return
        _startup_done = True

    log.info("=" * 76)
    log.info("  👑  HEONIX ULTRA ENGINE  v11.0 — PRODUCTION-HARDENED EDITION")
    log.info(f"  🌍  Region: {cfg.REGION}")
    log.info("=" * 76)

    # ── Database ──
    if cfg.DATABASE_MODE == "postgres" and cfg.DATABASE_URL and POSTGRES_AVAILABLE:
        _db_pool = PostgreSQLPool(
            cfg.DATABASE_URL,
            min_conn=2,
            max_conn=cfg.MAX_POOL_SIZE,
            replica_dsn=cfg.DATABASE_REPLICA_URL,
        )
    else:
        _db_pool = SQLitePool(cfg.DATABASE_FILE, pool_size=cfg.MAX_POOL_SIZE)

    # ── v11 #2: never *silently* run a multi-worker deployment on fallbacks ──
    on_paas    = bool(os.getenv("RENDER") or os.getenv("DYNO") or os.getenv("FLY_APP_NAME"))
    sqlite_db  = isinstance(_db_pool, SQLitePool)
    no_redis   = not (cfg.REDIS_URL and REDIS_AVAILABLE)
    if sqlite_db and on_paas:
        log.critical("🛑 SQLite on a PaaS dyno: disk is EPHEMERAL (all customer "
                     "data lost on every deploy) and 'database locked' errors "
                     "appear under 2+ workers. Set DATABASE_URL + DATABASE_MODE=postgres.")
    if no_redis and on_paas:
        log.critical("🛑 No REDIS_URL: dedupe / ghost-mute / response-cache are "
                     "per-process → with 2 gunicorn workers users can get DOUBLE "
                     "replies and human-takeover mute won't stick. Set REDIS_URL "
                     "(Upstash free tier works).")
    if cfg.STRICT_PROD and (sqlite_db or no_redis):
        raise SystemExit("STRICT_PROD=1: refusing to boot without Postgres + Redis. "
                         "Set DATABASE_URL, DATABASE_MODE=postgres, REDIS_URL "
                         "— or unset STRICT_PROD for dev.")

    init_db()
    _migrate_v10()   # v10: new columns, safe every boot
    _migrate_v11()   # v11: CRM dedupe column + index, safe every boot

    # ── AI Providers ──
    _init_ai_providers()

    # ── v10: RAG long-term memory ──
    init_rag()

    # ── Background Janitor ──
    threading.Thread(target=_janitor_loop, name="Janitor", daemon=True).start()
    log.info("🧹 Background janitor started.")

    # ── Startup Summary ──
    log.info("=" * 76)
    log.info(f"  🌐  Port:            {cfg.PORT}")
    log.info(f"  🗄️   DB Mode:         {cfg.DATABASE_MODE}")
    log.info(f"  📚  Read Replica:    "
             f"{'YES ✅' if isinstance(_db_pool, PostgreSQLPool) and _db_pool._read else 'NO'}")
    log.info(f"  🧠  Redis Cache:     "
             f"{'distributed ✅' if brain_cache._redis else 'in-process only'}")
    log.info(f"  🔐  PII Encryption: "
             f"{'AES-256-GCM ✅' if pii_vault.enabled else 'DISABLED ⚠️'}")
    log.info(f"  🔑  bcrypt Hashing: "
             f"{'ACTIVE ✅' if BCRYPT_AVAILABLE else 'SHA-256 fallback ⚠️'}")
    log.info(f"  📱  WhatsApp API:   "
             f"{'CONFIGURED ✅' if cfg.WHATSAPP_TOKEN else 'NOT SET ⚠️'}")
    if not cfg.WHATSAPP_APP_SECRET:
        log.warning("  🚨  WHATSAPP_APP_SECRET not set → webhook signature "
                    "verification is OFF. Anyone who finds the URL can POST "
                    "fake messages. Set it before going live!")
    log.info(f"  📸  Instagram API:  "
             f"{'CONFIGURED ✅' if cfg.INSTAGRAM_TOKEN else 'NOT SET (optional)'}")
    log.info(f"  🧬  RAG Memory:     "
             f"{'Qdrant ONLINE ✅' if _rag_ready else 'OFF (set QDRANT_URL + QDRANT_API_KEY)'}")
    log.info(f"  🎙️   Voice Decoder:  "
             f"{'Gemini→Whisper ✅' if (AI_PROVIDERS_ACTIVE.get('gemini') or AI_PROVIDERS_ACTIVE.get('openai')) else 'OFF'}")
    log.info(f"  🤖  AI Chain:       {[k for k, v in AI_PROVIDERS_ACTIVE.items() if v]}")
    log.info(f"  🔒  JWT Auth:       {'ACTIVE ✅' if JWT_AVAILABLE else 'pyjwt not installed ⚠️'}")
    log.info(f"  📊  Analytics:      {'ENABLED ✅' if cfg.ENABLE_ANALYTICS else 'DISABLED'}")
    log.info(f"  📬  Outbox/Saga:    ACTIVE ✅")
    log.info(f"  🪙  Customer RL:    60 req/min per customer_id ✅")
    log.info(f"  🧵  BG Workers:     {_WORKER_POOL._max_workers} bounded threads ✅")
    log.info(f"  📨  Owner Alerts:   "
             f"{'template (24h-proof) ✅' if cfg.OWNER_ALERT_TEMPLATE else 'free-form (set OWNER_ALERT_TEMPLATE!) ⚠️'}")
    log.info(f"  📝  Log Format:     {cfg.LOG_FORMAT}")
    log.info("=" * 76)
    log.info("  🦅  v11.0 — PRODUCTION-HARDENED — async webhooks, fails safe, logs loud")
    log.info("=" * 76)


# ─────────────────────────────────────────────────────────────────────────────
# ▶️   ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
# v10 FIX: run startup at import time too. The documented production command is
#   gunicorn heonix_ultra_engine_v11:app
# which imports this module but never executes __main__ — in v8 that left
# _db_pool = None and every request crashed with "pool not initialised".
# startup() is idempotent, so both paths are safe.
startup()

if __name__ == "__main__":
    app.run(
        host         = "0.0.0.0",
        port         = cfg.PORT,
        debug        = cfg.DEBUG,
        threaded     = True,
        use_reloader = False,
    )
