"""HEONIX GEN-5 · module `heonix.api.routes_public`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 8843-9033).
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

from heonix.ai.providers import (AI_PROVIDERS_ACTIVE)
from heonix.analytics import (analytics)
from heonix.api.app import (app)
from heonix.cache import (brain_cache)
from heonix.config import (ENGINE_BANNER, ENGINE_GEN, ENGINE_VERSION, cfg)
from heonix.db.core import (PostgreSQLPool, _execute)
from heonix.resilience import (
    _claude_breaker,
    _gemini_breaker,
    _openai_breaker,
    _whatsapp_breaker,
)
from heonix.security.auth import (_safe_ct_eq)
from heonix.security.crypto import (pii_vault)
from heonix.utils import (_now)
from heonix import _latebind  # GEN-5 SPLIT
_db_pool: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.db.core at startup
_latebind.register('_db_pool', __name__)
_rag_ready: Any = False   # GEN-5 SPLIT: late-bound; published by heonix.ai.rag at startup
_latebind.register('_rag_ready', __name__)


# ─────────────────────────────────────────────────────────────────────────────

# ── Health Check (Kubernetes liveness probe) ──────────────────────────────────
@app.route("/", methods=["GET"])
def root():
    """Friendly landing — visiting the bare Render URL previously 404'd.
    v16g4 FIX L7: the banner advertised the exact build + patch count to any
    anonymous scanner — free recon that maps this deployment to every bug
    fixed AFTER it. Version detail now needs the same token /health uses (or
    DEBUG); the public face is just "online"."""
    body = {
        "engine":  "HEONIX",
        "status":  "online",
        "health":  "/health",
        "ready":   "/ready",
        "metrics": "/metrics",
    }
    if cfg.DEBUG or (cfg.METRICS_TOKEN and _safe_ct_eq(
            request.headers.get("X-Metrics-Token", ""), cfg.METRICS_TOKEN)):
        body["engine"] = ENGINE_BANNER
    return jsonify(body), 200


@app.route("/health", methods=["GET"])
def health():
    db_ok = True
    try:
        with _db_pool.get(read_only=True) as conn:
            _execute(conn, "SELECT 1", ())
    except Exception:
        db_ok = False

    # v16g3 FIX R3-L10: with METRICS_TOKEN set, the full body (replica
    # layout, PII-encryption on/off, circuit states) needs the token — public
    # probes get status-only, so /health still works as a plain liveness
    # check for Render/K8s without leaking deployment recon.
    if cfg.METRICS_TOKEN and not _safe_ct_eq(
            request.headers.get("X-Metrics-Token", ""), cfg.METRICS_TOKEN):
        return (jsonify({"status": "UP" if db_ok else "DEGRADED",
                         "timestamp": _now()}),
                200 if db_ok else 503)

    ai_active = [k for k, v in AI_PROVIDERS_ACTIVE.items() if v]
    return jsonify({
        "status":           "UP" if db_ok else "DEGRADED",
        "engine":           f"HEONIX Ultra {ENGINE_VERSION} {ENGINE_GEN}",
        "region":           cfg.REGION,
        "timestamp":        _now(),
        "db_mode":          cfg.DATABASE_MODE,
        "db_healthy":       db_ok,
        "replica_pool":     bool(
            isinstance(_db_pool, PostgreSQLPool) and _db_pool._read),
        "redis_connected":  brain_cache.ping(),   # v14g5 FIX 48: real round-trip
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
    # v16g3 FIX R3-M7: a pod with the database down passed readiness and kept
    # receiving traffic it could only 500. Same one-liner /health uses.
    try:
        with _db_pool.get(read_only=True) as conn:
            _execute(conn, "SELECT 1", ())
    except Exception:
        return jsonify({"ready": False, "reason": "Database unavailable"}), 503
    return jsonify({
        "ready":    True,
        "region":   cfg.REGION,
        "ai_chain": [k for k, v in AI_PROVIDERS_ACTIVE.items() if v],
    }), 200


# ── Prometheus Metrics (FIX #15: histograms + P99 latency) ──────────────────
@app.route("/metrics", methods=["GET"])
def metrics():
    # v14g5 FIX 23: if METRICS_TOKEN is set, require it (constant-time) so the
    # endpoint that exposes customer/session/message counts isn't world-readable.
    # Unset = open (dev / private network), preserving prior behaviour.
    if cfg.METRICS_TOKEN and not _safe_ct_eq(
            request.headers.get("X-Metrics-Token", ""), cfg.METRICS_TOKEN):  # v16g3 R3-M1
        return jsonify({"error": "Unauthorized"}), 401
    snap = analytics.snapshot()
    c    = snap["counters"]
    p99  = snap["latency_p99"]

    # v12 #10: COUNT(*) over chat_messages gets very expensive at scale, and a
    # Prometheus scrape storm (or a curious dashboard on refresh) would hammer
    # the DB. Cache the three counts for METRICS_CACHE_TTL seconds.
    cached_counts = brain_cache.get("metrics:counts")
    if isinstance(cached_counts, dict):
        customers = cached_counts.get("customers", -1)
        sessions  = cached_counts.get("sessions", -1)
        messages  = cached_counts.get("messages", -1)
    else:
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
            brain_cache.set("metrics:counts",
                            {"customers": customers, "sessions": sessions,
                             "messages": messages}, ttl=cfg.METRICS_CACHE_TTL)
        except Exception:
            customers = sessions = messages = -1

    # v16g2 FIX C3: every series now carries a TYPE line; sessions/messages
    # are COUNT(*) snapshots that DECREASE after the retention purge — calling
    # them `counter` broke Prometheus rate(); they are gauges. The pointless
    # f-string on the uptime HELP line is gone.
    lines = [
        "# HELP heonix_customers_total Active customer brains",
        "# TYPE heonix_customers_total gauge",
        f"heonix_customers_total {customers}",
        "# HELP heonix_sessions_total Chat sessions",
        "# TYPE heonix_sessions_total gauge",
        f"heonix_sessions_total {sessions}",
        "# HELP heonix_messages_total Chat messages",
        "# TYPE heonix_messages_total gauge",
        f"heonix_messages_total {messages}",
        "# HELP heonix_requests_total HTTP requests processed",
        "# TYPE heonix_requests_total counter",
        f"heonix_requests_total {c.get('request.total', 0)}",
        "# HELP heonix_cache_hit_total Cache hits",
        "# TYPE heonix_cache_hit_total counter",
        f"heonix_cache_hit_total {c.get('cache.hit', 0)}",
        "# HELP heonix_cache_miss_total Cache misses",
        "# TYPE heonix_cache_miss_total counter",
        f"heonix_cache_miss_total {c.get('cache.miss', 0)}",
        "# HELP heonix_ai_gemini_success Gemini success count",
        "# TYPE heonix_ai_gemini_success counter",
        f"heonix_ai_gemini_success {c.get('ai.gemini.success', 0)}",
        "# HELP heonix_ai_openai_success OpenAI success count",
        "# TYPE heonix_ai_openai_success counter",
        f"heonix_ai_openai_success {c.get('ai.openai.success', 0)}",
        "# HELP heonix_ai_claude_success Claude success count",
        "# TYPE heonix_ai_claude_success counter",
        f"heonix_ai_claude_success {c.get('ai.claude.success', 0)}",
        "# HELP heonix_ai_gemini_latency_p99_ms Gemini P99 latency ms",
        "# TYPE heonix_ai_gemini_latency_p99_ms gauge",
        f"heonix_ai_gemini_latency_p99_ms {p99.get('ai.gemini.latency_ms', 0)}",
        "# HELP heonix_ai_openai_latency_p99_ms OpenAI P99 latency ms",
        "# TYPE heonix_ai_openai_latency_p99_ms gauge",
        f"heonix_ai_openai_latency_p99_ms {p99.get('ai.openai.latency_ms', 0)}",
        "# HELP heonix_ai_claude_latency_p99_ms Claude P99 latency ms",
        "# TYPE heonix_ai_claude_latency_p99_ms gauge",
        f"heonix_ai_claude_latency_p99_ms {p99.get('ai.claude.latency_ms', 0)}",
        "# HELP heonix_ai_gemini_circuit Gemini circuit (0=CLOSED,1=OPEN)",
        "# TYPE heonix_ai_gemini_circuit gauge",
        f"heonix_ai_gemini_circuit {1 if _gemini_breaker.state == 'OPEN' else 0}",
        "# HELP heonix_ai_openai_circuit OpenAI circuit",
        "# TYPE heonix_ai_openai_circuit gauge",
        f"heonix_ai_openai_circuit {1 if _openai_breaker.state == 'OPEN' else 0}",
        "# HELP heonix_ai_claude_circuit Claude circuit",
        "# TYPE heonix_ai_claude_circuit gauge",
        f"heonix_ai_claude_circuit {1 if _claude_breaker.state == 'OPEN' else 0}",
        "# HELP heonix_whatsapp_sent WhatsApp messages sent",
        "# TYPE heonix_whatsapp_sent counter",
        f"heonix_whatsapp_sent {c.get('whatsapp.sent', 0)}",
        "# HELP heonix_uptime_seconds Uptime seconds",
        "# TYPE heonix_uptime_seconds gauge",
        f"heonix_uptime_seconds {snap['uptime_secs']}",
    ]
    return "\n".join(lines) + "\n", 200, {"Content-Type": "text/plain; charset=utf-8"}
