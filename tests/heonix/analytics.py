"""HEONIX GEN-5 · module `heonix.analytics`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 1593-1660).
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



class AnalyticsEngine:
    """
    Lock-guarded IN-PROCESS analytics — per gunicorn worker, with NO cross-worker
    Redis sync. v16g2 FIX M12: the old docstring promised "Redis sync every 60 s"
    (and "Lock-free" while using a Lock) — no such code exists anywhere in this
    file. Under -w N, /metrics and /admin/analytics reflect whichever worker
    served the scrape; ops must not treat the split numbers as fleet totals.
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
            return self._counters.get(key, 0)   # v14g5 FIX 29: don't auto-create probed keys

    def _percentile_nolock(self, key: str, pct: float = 0.99) -> float:
        # v14g3 BUG 1: the caller already holds self._lock. threading.Lock is
        # NOT reentrant, so any method invoked while the lock is held must not
        # try to re-acquire it. This no-lock variant is the safe inner core.
        data = sorted(self._latencies[key])
        if not data:
            return 0.0
        # v16g4 FIX L2: int(n*pct)-1 under-reported on small n — p99 of 10
        # samples returned the 9th value, not the max. Ceiling-based nearest-
        # rank: p99 of 10 → ceil(9.9)=10 → index 9 → the true max.
        idx = min(len(data) - 1, max(0, math.ceil(len(data) * pct) - 1))
        return round(data[idx], 2)

    def percentile(self, key: str, pct: float = 0.99) -> float:
        with self._lock:
            if key not in self._latencies:   # v15 FIX 18: twin of v14g5 FIX 29 —
                return 0.0                   # bracket access on a defaultdict
            return self._percentile_nolock(key, pct)

    def snapshot(self) -> Dict:
        # v14g3 BUG 1 FIX (CRITICAL): the old body did
        #     latency_p99 = {k: self.percentile(k) for k in self._latencies}
        # INSIDE `with self._lock`, and percentile() then re-acquired the SAME
        # non-reentrant lock → the thread blocked forever waiting on a lock it
        # already held. Every Prometheus scrape of /metrics (and every hit to
        # /admin/analytics) permanently hung a gunicorn worker. Now we compute
        # percentiles with the no-lock variant while holding the lock once.
        with self._lock:
            counters    = dict(self._counters)
            latency_p99 = {k: self._percentile_nolock(k) for k in self._latencies}
        uptime_s = time.monotonic() - self._started
        return {
            "counters":    counters,
            "latency_p99": latency_p99,
            "uptime_secs": round(uptime_s, 1),
        }


analytics = AnalyticsEngine()
