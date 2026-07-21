"""HEONIX GEN-5 · module `heonix.api.app`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 8558-8654, 10935-10988, 10991-11292).
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

from heonix.ai.providers import (AI_PROVIDERS_ACTIVE, _init_ai_providers)
from heonix.ai.rag import (init_rag)
from heonix.analytics import (analytics)
from heonix.cache import (brain_cache)
from heonix.concurrency import (_IO_POOL, _TIMEOUT_POOL, _WORKER_POOL, _shutdown_event)
from heonix.config import (ENGINE_GEN, ENGINE_VERSION, cfg)
from heonix.db.core import (
    PostgreSQLPool,
    SQLitePool,
    _execute,
    _migrate_v10,
    _migrate_v11,
    _migrate_v12,
    _migrate_v14g3,
    _migrate_v14g4,
    _migrate_v14g5,
    _migrate_v15g3,
    _migrate_v15g4,
    _migrate_v16,
    _migrate_v16g4,
    _migrate_v16g5,
    _report_wa_pid_duplicates,
    init_db,
)
from heonix.logsetup import (log)
from heonix.scheduler.janitor import (_janitor_loop)
from heonix.security.crypto import (hash_password, pii_vault)
from heonix.utils import (_now)
from heonix.db.core import _publish_db_pool  # GEN-5 SPLIT
from heonix import _latebind  # GEN-5 SPLIT
_db_pool: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.db.core at startup
_latebind.register('_db_pool', __name__)
_rag_ready: Any = False   # GEN-5 SPLIT: late-bound; published by heonix.ai.rag at startup
_latebind.register('_rag_ready', __name__)


app = Flask(__name__)
app.config["SECRET_KEY"] = cfg.SECRET_KEY
# v12 #37: cap request bodies so an attacker can't POST a giant JSON blob and
# blow up RAM — Flask 413s anything larger before it is read into memory.
app.config["MAX_CONTENT_LENGTH"] = cfg.MAX_CONTENT_BYTES

# v12 #14/#30: Render (and every PaaS) sits behind a load balancer, so the
# socket peer is the LB, not the user. Without ProxyFix, get_remote_address()
# returns the LB/Meta IP and the IP rate limiter throttles ALL clinics as one.
# Honour X-Forwarded-For/Proto from exactly one trusted proxy hop.
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
except Exception as _pf_exc:   # pragma: no cover
    log.warning(f"⚠️  ProxyFix unavailable ({_pf_exc}) — client IPs may be the LB's.")

# v16g5 FIX R5-M11: this was a wildcard by default across EVERY route —
# /admin/*, /crm/*, the DPDP erasure endpoint — and read through a raw
# os.getenv instead of cfg (the pattern FIX L8 cleaned up for the Tally
# secret). Webhooks stay open (Meta posts server-side, so CORS is irrelevant
# there); the admin/CRM surface is same-origin unless CORS_ORIGINS names the
# dashboard explicitly. STRICT_PROD refuses the wildcard outright.
_cors_origins = [o.strip() for o in (cfg.CORS_ORIGINS or "").split(",") if o.strip()]
if not _cors_origins:
    if cfg.STRICT_PROD:
        raise SystemExit("STRICT_PROD=1: set CORS_ORIGINS to your dashboard "
                         "origin(s). A wildcard would let any website call "
                         "/admin/* and /crm/* from a logged-in browser.")
    _cors_origins = ["*"]
    log.warning("⚠️  CORS_ORIGINS unset → '*' (dev default). Set it to your "
                "dashboard origin before launch (v16g5 FIX R5-M11).")
CORS(app, resources={
    r"/whatsapp-webhook":  {"origins": "*"},
    r"/instagram-webhook": {"origins": "*"},
    r"/tally-webhook":     {"origins": "*"},
    r"/health":            {"origins": "*"},
    r"/ready":             {"origins": "*"},
    r"/*":                 {"origins": _cors_origins},
})

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[cfg.RATE_LIMIT_DEFAULT],
    storage_uri=cfg.REDIS_URL if cfg.REDIS_URL else "memory://",
)


# v12 #29: under gunicorn --preload, startup() runs in the master BEFORE fork,
# so the janitor thread lives only in the master and dies in the workers. This
# guard lets each worker lazily start its own janitor on first request — the
# flag is per-process, so it's exactly-once per worker.
_worker_janitor_started = False
_worker_janitor_lock    = threading.Lock()


def _ensure_worker_janitor() -> None:
    global _worker_janitor_started
    if _worker_janitor_started:
        return
    with _worker_janitor_lock:
        if _worker_janitor_started:
            return
        alive = any(t.name == "Janitor" and t.is_alive()
                    for t in threading.enumerate())
        if not alive:
            threading.Thread(target=_janitor_loop, name="Janitor", daemon=True).start()
            log.info("🧹 Per-worker janitor started (post-fork self-heal).")
        _worker_janitor_started = True


@app.after_request
def _security_headers(response):
    """OWASP-recommended security headers on every response."""
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    # v16g2 FIX C7: X-XSS-Protection removed — deprecated; modern browsers
    # ignore it, and it could re-enable a buggy legacy auditor.
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
    _ensure_worker_janitor()   # v12 #29


def elapsed_ms() -> int:
    return int((time.monotonic() - g.get("start_time", time.monotonic())) * 1000)


def _shutdown_handler(signum, frame):
    log.info(f"📴 Signal {signum} — graceful shutdown starting...")
    _shutdown_event.set()
    # v11 #14: was time.sleep(10) INSIDE the handler (blocks all signal
    # delivery). Now: stop accepting new bg work, let queued sends finish
    # with a hard ceiling enforced by a watchdog, then close the DB pool.
    def _drain():
        # v14g3 BUG 5: drain ALL bounded pools on shutdown, not just the worker
        # pool — the I/O pool (alerts/audit/sends) and timeout pool must finish
        # or be released cleanly too.
        for _pool in (_WORKER_POOL, _IO_POOL, _TIMEOUT_POOL):
            try:
                _pool.shutdown(wait=True)
            except Exception:
                pass
        if _db_pool:
            try:
                _db_pool.close_all()
            except Exception:
                pass
        log.info(f"✅ HEONIX Ultra {ENGINE_VERSION} {ENGINE_GEN} "
                 f"shut down cleanly.")                              # v16g2 FIX C1
    t = threading.Thread(target=_drain, name="drain", daemon=True)
    t.start()
    t.join(timeout=10)        # bounded — gunicorn's graceful-timeout is the boss
    # v15 FIX 14: the old handler drained and then simply RETURNED — under the
    # dev server Ctrl+C was swallowed (the app kept serving), and a worker that
    # inherited this handler never exited on SIGTERM until SIGKILL. Exit for real.
    sys.exit(0)


def _install_signal_handlers() -> None:
    """v15 FIX 14: only claim SIGTERM/SIGINT when THIS process owns them
    (direct `python engine.py`). The old module-import-time takeover REPLACED
    gunicorn's own worker SIGTERM handler with one that never exited — graceful
    stops degraded to SIGKILL after the timeout. Under gunicorn we now leave
    its signal handling alone and clean up via atexit instead."""
    signal.signal(signal.SIGTERM, _shutdown_handler)
    signal.signal(signal.SIGINT,  _shutdown_handler)


def _atexit_cleanup() -> None:
    """v15 FIX 14: gunicorn path — stop the janitor loop and release the DB
    pool when the interpreter exits normally (the bounded thread pools already
    join themselves via concurrent.futures' own atexit hook)."""
    _shutdown_event.set()
    try:
        if _db_pool:
            _db_pool.close_all()
    except Exception:
        pass


atexit.register(_atexit_cleanup)


def _bootstrap_first_admin() -> None:
    """v15g2 FIX L7: creating the first admin required a superadmin JWT — which
    required an existing admin. The only escape hatch (legacy ADMIN_API_KEY) was
    undocumented as the bootstrap path. Now: if admin_users is EMPTY and
    ADMIN_BOOTSTRAP_USER / ADMIN_BOOTSTRAP_PASSWORD (≥8 chars) are set, seed one
    superadmin on boot; otherwise say exactly how to get in."""
    try:
        with _db_pool.get(read_only=True) as conn:
            _r = _execute(conn, "SELECT COUNT(*) AS c FROM admin_users", ()).fetchone()
            n  = (_r["c"] if _r else 0) or 0
        if n:
            return
        bu = os.getenv("ADMIN_BOOTSTRAP_USER", "").strip()
        bp = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "")
        if bu and len(bp) >= 8:
            with _db_pool.get() as conn:
                _execute(conn,
                    "INSERT INTO admin_users (user_id, username, hashed_pw, role, created_at) "
                    "VALUES (?,?,?,?,?)",
                    (f"adm_{uuid.uuid4().hex[:12]}", bu, hash_password(bp),
                     "superadmin", _now()))
            log.info(f"🔑 Bootstrap superadmin '{bu}' created via ADMIN_BOOTSTRAP_*. "
                     f"Unset those env vars after your first login.")
        elif not cfg.ADMIN_API_KEY:
            log.warning("🔑 No admin users exist and no ADMIN_API_KEY set — admin "
                        "login is impossible. Set ADMIN_BOOTSTRAP_USER + "
                        "ADMIN_BOOTSTRAP_PASSWORD (≥8 chars) once, or set "
                        "ADMIN_API_KEY for the legacy X-Admin-Key path.")
    except Exception as exc:
        log.warning(f"⚠️  admin bootstrap check skipped: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 🚀  STARTUP SEQUENCE
# ─────────────────────────────────────────────────────────────────────────────
_startup_done = False
_startup_lock = threading.Lock()


_startup_ready = threading.Event()   # v16g4 FIX L4


def startup() -> None:
    global _db_pool, _startup_done
    with _startup_lock:
        if _startup_done:          # idempotent — safe under gunicorn + __main__
            # v16g4 FIX L4: _startup_done was flipped BEFORE any work ran, so
            # a second caller returned instantly and could serve a request
            # against a _db_pool that didn't exist yet. Late callers now WAIT
            # for the first boot to actually finish (bounded, then proceed —
            # a hung boot shouldn't deadlock the health probe).
            _startup_ready.wait(timeout=120)
            return
        _startup_done = True

    log.info("=" * 76)
    log.info(f"  👑  HEONIX ULTRA ENGINE  {ENGINE_VERSION} {ENGINE_GEN}"
             f"  ·  ROUND-6 CLOSE-OUT (47 FIXES)")
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
    _publish_db_pool(_db_pool)  # GEN-5 SPLIT: sync pool into every module that uses it

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

    # ── v14g3 BUG 3: JWT / Flask secrets MUST be set explicitly for multi-worker.
    # If unset, each gunicorn worker generated its OWN random secret at import →
    # a JWT minted by worker A failed validation on worker B (admin login broke
    # intermittently) and Flask sessions broke the same way. We cannot invent a
    # shared secret across processes, so fail LOUD (and refuse under STRICT_PROD).
    # v15g2 FIX L9: secrets derived from ENCRYPTION_KEY are identical in every
    # worker, so they no longer count as 'missing' — the refuse-to-boot guard
    # now only fires when there is genuinely nothing shared to derive from.
    _missing_secrets = ([] if os.getenv("ENCRYPTION_KEY") else
                        [n for n in ("JWT_SECRET_KEY", "SECRET_KEY")
                         if not os.getenv(n)])
    if _missing_secrets:
        _smsg = ("🛑 " + " & ".join(_missing_secrets) + " not set — each worker "
                 "will use a DIFFERENT random secret, so JWT auth and Flask "
                 "sessions break across gunicorn workers. Generate one with: "
                 "python -c \"import secrets; print(secrets.token_hex(32))\"")
        # v14g5 FIX 11: a missing shared secret under >1 worker is not a warning —
        # admin JWTs minted on one worker are REJECTED on another, so login breaks
        # nondeterministically. Refuse to boot (matches STRICT_PROD behaviour).
        if cfg.STRICT_PROD or cfg.WEB_CONCURRENCY > 1:
            raise SystemExit(_smsg + ("  (STRICT_PROD=1 refuses to boot.)"
                                      if cfg.STRICT_PROD else
                                      f"  (WEB_CONCURRENCY={cfg.WEB_CONCURRENCY} "
                                      "> 1 refuses to boot — set a shared secret.)"))
        log.warning(_smsg)

    # ── #34: pool-explosion guard ──
    # Each gunicorn worker opens its OWN pool of up to MAX_POOL_SIZE connections.
    # workers × MAX_POOL_SIZE must stay under the Postgres connection ceiling, or
    # the Nth worker gets "FATAL: remaining connection slots are reserved" / "too
    # many connections" at peak — which looks like random 500s under load. Warn
    # loudly, and if Postgres, clamp this worker's pool so the fleet stays legal.
    if not sqlite_db:
        projected = cfg.WEB_CONCURRENCY * cfg.MAX_POOL_SIZE
        if projected > cfg.DB_MAX_CONNECTIONS:
            safe = max(2, cfg.DB_MAX_CONNECTIONS // max(1, cfg.WEB_CONCURRENCY))
            log.critical(
                f"🛑 DB pool overcommit: WEB_CONCURRENCY({cfg.WEB_CONCURRENCY}) × "
                f"MAX_POOL_SIZE({cfg.MAX_POOL_SIZE}) = {projected} > "
                f"DB_MAX_CONNECTIONS({cfg.DB_MAX_CONNECTIONS}). Under load the last "
                f"workers will hit 'too many connections'. Clamping this worker's "
                f"pool to {safe}. Fix properly: lower MAX_POOL_SIZE or raise the "
                f"Postgres max_connections / use a pgBouncer.")
            try:
                # v15 FIX 13: the clamp checked `_db_pool._pool` — an attribute
                # PostgreSQLPool never had (its pools are _write/_read), so the
                # "best-effort runtime clamp" was dead code and overcommit was
                # only ever logged, never contained.
                if hasattr(_db_pool, "_write") and hasattr(_db_pool._write, "maxconn"):
                    _db_pool._write.maxconn = safe
                if getattr(_db_pool, "_read", None) is not None \
                        and hasattr(_db_pool._read, "maxconn"):
                    _db_pool._read.maxconn = safe
            except Exception:
                pass

    init_db()
    _migrate_v10()   # v10: new columns, safe every boot
    _migrate_v11()   # v11: CRM dedupe column + index, safe every boot
    _migrate_v12()   # v13: per-tenant WA/IG creds + unique routing index, safe every boot
    _migrate_v14g3() # v14g3: unique CRM dedupe index + SQLite phone index
    _migrate_v14g4() # v14g4: bookings table + cold-lead follow-up marker (additive)
    _migrate_v14g5() # v14g5: chat_sessions.subject_hash for DB-based DPDP erasure
    _migrate_v15g3() # v15g3: outbox.next_attempt_at for exponential retry backoff
    _migrate_v15g4() # v15g4: purge-path indexes (D4) + SQLite idx_wh_customer (D5)
    _migrate_v16()   # v16: crm_contacts.wa_user_id (WhatsApp usernames/BSUID)
    _migrate_v16g4() # v16g4 FIX M10: admin_users.tenant_id
    _migrate_v16g5() # v16g5 FIX R5-H4: durable opt_outs suppression table
    _report_wa_pid_duplicates()   # v14: self-diagnose ambiguous-routing duplicates
    _bootstrap_first_admin()      # v15g2 FIX L7: no more admin chicken-and-egg

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
    if cfg.WHATSAPP_VERIFY_TOKEN == "heonix_verify":
        # v15g2 FIX L8: the default is public (it ships in this source file).
        log.warning("  🚨  WHATSAPP_VERIFY_TOKEN is the public default "
                    "('heonix_verify'). Set your own random value before live.")
    if not cfg.CHAT_API_KEY:
        log.warning("  🚨  CHAT_API_KEY not set → POST /chat is OPEN. customer_id "
                    "is derivable from a clinic's public WhatsApp number, so "
                    "anyone can burn your Gemini quota. Set it before going live!")
    if not cfg.SMOKE_TEST_ENABLED:
        log.info("  🔬  Smoke Test:      disabled — set SMOKE_TEST_ENABLED=1 "
                 "(v15 FIX 12: default now matches the docs; you use this tool!)")
    log.info(f"  📸  Instagram API:  "
             f"{'CONFIGURED ✅' if cfg.INSTAGRAM_TOKEN else 'NOT SET (optional)'}")
    log.info(f"  🧬  RAG Memory:     "
             f"{'Qdrant ONLINE ✅' if _rag_ready else 'OFF (set QDRANT_URL + QDRANT_API_KEY)'}")
    log.info(f"  🎙️   Voice Decoder:  "
             f"{'Gemini→Whisper ✅' if (AI_PROVIDERS_ACTIVE.get('gemini') or AI_PROVIDERS_ACTIVE.get('openai')) else 'OFF'}")
    log.info(f"  🤖  AI Chain:       {[k for k, v in AI_PROVIDERS_ACTIVE.items() if v]}")
    log.info(f"  🔒  JWT Auth:       {'ACTIVE ✅' if JWT_AVAILABLE else 'pyjwt not installed ⚠️'}")
    log.info(f"  📊  Analytics:      {'ENABLED ✅' if cfg.ENABLE_ANALYTICS else 'DISABLED'}")
    log.info("  📬  Outbox/Saga:    ACTIVE ✅")   # v16g3 R3-L2: stray f
    log.info("  🪙  Customer RL:    60 req/min per conversation (webhooks) / per customer_id (API) ✅")
    log.info(f"  🧵  BG Workers:     {_WORKER_POOL._max_workers} bounded threads ✅")
    log.info(f"  📨  Owner Alerts:   "
             f"{'template (24h-proof) ✅' if cfg.OWNER_ALERT_TEMPLATE else 'free-form (set OWNER_ALERT_TEMPLATE!) ⚠️'}")
    log.info("  🏥  Multi-Tenant:   per-clinic creds + phone_id routing ✅")
    # v16 U4: Contact Book is Meta-hosted and ON by default — zero integration
    # work, but verify it ONCE per WABA so known patients who adopt usernames
    # keep surfacing their number in webhooks.
    log.info("  🆔  Usernames:      BSUID compat ACTIVE ✅ (v16) — verify Contact "
             "Book is ON once: Business Suite → WhatsApp Manager → Settings")
    log.info(f"  🔑  Token Self-Heal:"
             f"{' ON (ADMIN_ALERT_PHONE set) ✅' if cfg.ADMIN_ALERT_PHONE else ' flag-only (set ADMIN_ALERT_PHONE for WA alerts) ⚠️'}")
    log.info(f"  📝  Log Format:     {cfg.LOG_FORMAT}")
    # v15g4 FIX E9a: WhatsApp rejects free-form messages outside the 24h
    # window (131047). Most appointments are booked >24h ahead, so WITHOUT an
    # approved template, most 24h reminders dead-letter after 5 retries.
    if cfg.DATA_RETENTION_DAYS <= 0:
        # v16g5 FIX R5-L9: the default (0 = keep forever) is the one DPDP knob
        # that ships non-compliant. Defensible as a default — silently is not.
        log.warning("  🚨  DATA_RETENTION_DAYS=0 → chat transcripts (patient "
                    "symptoms, names, numbers) are kept FOREVER. DPDP expects a "
                    "stated retention limit. Set it (e.g. 365) before launch.")
    if cfg.ENABLE_SCHEDULER and not cfg.REMINDER_TEMPLATE:
        log.warning("  🚨  ENABLE_SCHEDULER is ON but REMINDER_TEMPLATE is not "
                    "set → reminders for bookings made >24h ahead WILL fail "
                    "outside Meta's window. Create + approve a template in the "
                    "Meta console and set REMINDER_TEMPLATE before launch.")
    # v15g4 FIX E11a: google.generativeai is the DEPRECATED legacy SDK. Make
    # the risk visible on every deploy: verify this SDK version still serves
    # the configured models, and plan the google-genai migration.
    if AI_PROVIDERS_ACTIVE.get("gemini"):
        try:
            _gv = getattr(genai, "__version__", "?")
            log.info(f"  🧬  Gemini SDK:     google.generativeai {_gv} "
                     f"(LEGACY — verify it serves {cfg.GEMINI_MODEL}; "
                     f"plan google-genai migration)")
        except Exception:
            pass
    # v15g4 FIX D6: .search() is the pre-query_points Qdrant API — pin the
    # client version in requirements so an upgrade can't surprise-break RAG.
    if _rag_ready:
        try:
            import qdrant_client as _qc
            log.info(f"  🧷  Qdrant client:  {getattr(_qc, '__version__', '?')} "
                     f"(pin this in requirements — engine uses the legacy "
                     f".search() API)")
        except Exception:
            pass
    # ── v16g4 boot warnings: every silent-death config gap gets a voice ──
    if cfg.FOLLOWUP_ENABLED and not cfg.FOLLOWUP_TEMPLATE:
        # v16g4 FIX H2: twin of E9a — cold-lead nudges are BY DEFINITION
        # outside the 24h window; without a template none can deliver.
        log.warning("  🚨  FOLLOWUP_ENABLED is ON but FOLLOWUP_TEMPLATE is not "
                    "set → cold-lead nudges are DISABLED (nothing outside the "
                    "24h window can deliver as free text). Approve a template "
                    "and set FOLLOWUP_TEMPLATE.")
    if not cfg.WELCOME_TEMPLATE:
        # v16g4 FIX H1 companion warning.
        log.warning("  🚨  WELCOME_TEMPLATE not set → the Tally onboarding "
                    "welcome to new clinic owners is SKIPPED (a cold number "
                    "can't receive free text). Approve a welcome template and "
                    "set WELCOME_TEMPLATE.")
    if (cfg.STRICT_PROD or cfg.REQUIRE_WEBHOOK_SIGNATURE) and not cfg.TALLY_WEBHOOK_SECRET:
        # v16g4 FIX H4 companion warning: the endpoint fails CLOSED now.
        log.warning("  🚨  TALLY_WEBHOOK_SECRET not set under strict mode → "
                    "the /tally-webhook endpoint REJECTS all onboarding posts "
                    "(fail-closed). Set the secret from your Tally form's "
                    "webhook settings.")
    if cfg.ADMIN_API_KEY:
        # v16g4 FIX M13 companion warning.
        if cfg.STRICT_PROD and not cfg.ADMIN_API_KEY_LEGACY_OK:
            log.warning("  🔐  ADMIN_API_KEY is set but REFUSED under "
                        "STRICT_PROD (v16g4 FIX M13). Use JWT login, or set "
                        "ADMIN_API_KEY_LEGACY_OK=1 to acknowledge the risk.")
        else:
            log.warning("  🔐  Legacy ADMIN_API_KEY auth is ACTIVE — a "
                        "permanent env superadmin. Prefer JWT logins; rotate "
                        "the key if it has ever been shared.")
    if cfg.WEB_CONCURRENCY <= 1 and (os.getenv("GUNICORN_CMD_ARGS")
                                     or os.getenv("SERVER_SOFTWARE", "").startswith("gunicorn")):
        # v16g4 FIX O2: the limiter's no-Redis divisor and the pool-overcommit
        # math both read WEB_CONCURRENCY; if gunicorn runs >1 workers while it
        # is unset (default 1), those calculations silently under-divide.
        log.warning("  🚨  Running under gunicorn but WEB_CONCURRENCY is unset/1 "
                    "— if you run more than 1 worker, set WEB_CONCURRENCY to "
                    "the same number so rate-limit and DB-pool math stay true.")
    log.info("=" * 76)
    log.info(f"  🦅  {ENGINE_VERSION} {ENGINE_GEN} — 47/47 round-6 findings "
             f"closed · sealed owner PII · delivery-status feedback · "
             f"commit-path overlap guard")
    log.info("=" * 76)
    _startup_ready.set()   # v16g4 FIX L4: boot genuinely complete
