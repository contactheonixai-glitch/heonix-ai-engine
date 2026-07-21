"""HEONIX GEN-5 · module `heonix.resilience`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 2961-3065, 3111-3114).
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

from heonix.logsetup import (log)


class CircuitBreaker:
    CLOSED = "CLOSED"; OPEN = "OPEN"; HALF_OPEN = "HALF_OPEN"

    def __init__(self, name: str, failure_threshold: int = 5, reset_timeout: float = 60.0):
        self.name           = name
        self._threshold     = failure_threshold
        self._reset_timeout = reset_timeout
        self._failures      = 0
        self._state         = self.CLOSED
        self._opened_at     = 0.0
        self._probe_inflight = False     # v12 #22: single-probe gate for HALF_OPEN
        self._probe_started_at = 0.0     # v16g5 FIX R5-H2
        self._lock          = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    def call(self, func: Callable, *args, **kwargs):
        is_probe = False
        with self._lock:
            if self._state == self.OPEN:
                if time.monotonic() - self._opened_at >= self._reset_timeout:
                    self._state = self.HALF_OPEN
                    self._probe_inflight = False
                    log.info(f"⚡ CircuitBreaker [{self.name}] → HALF_OPEN")
                else:
                    raise RuntimeError(f"CircuitBreaker [{self.name}] OPEN")
            if self._state == self.HALF_OPEN:
                # v12 #22: let exactly ONE request probe recovery. Every other
                # concurrent caller fast-fails instead of stampeding a provider
                # that just came back from the dead (which would re-trip it and
                # could DDoS Gemini/OpenAI ourselves).
                # v16g5 FIX R5-H2: belt-and-braces for the finally above — a
                # probe still "in flight" past the reset window is treated as
                # abandoned and reclaimed, so the breaker can never wedge.
                if (self._probe_inflight
                        and time.monotonic() - self._probe_started_at
                            < max(self._reset_timeout, 30.0)):
                    raise RuntimeError(f"CircuitBreaker [{self.name}] HALF_OPEN (probing)")
                if self._probe_inflight:
                    log.warning(f"⚡ CircuitBreaker [{self.name}] reclaiming an "
                                f"abandoned probe slot")
                self._probe_inflight   = True
                self._probe_started_at = time.monotonic()
                is_probe = True
        # v16g5 FIX R5-H2: _probe_inflight used to be cleared only on the three
        # `except Exception` / success paths. A BaseException out of the probe
        # — SystemExit, KeyboardInterrupt, a gevent/eventlet Timeout, a
        # GeneratorExit from a killed worker thread — left it True FOREVER, and
        # nothing else ever resets it: every later call raised
        # "HALF_OPEN (probing)" and that provider was dead for the life of the
        # process. The flag is now released in a finally, and an abandoned
        # probe additionally ages out via _probe_started_at.
        try:
            result = func(*args, **kwargs)
            with self._lock:
                self._failures = 0
                if self._state == self.HALF_OPEN:
                    self._state = self.CLOSED
                    log.info(f"⚡ CircuitBreaker [{self.name}] → CLOSED (recovered)")
            return result
        except AIEmptyResponse:
            # v15 FIX 6 (HIGH): an empty/safety-blocked reply means the provider
            # is UP — it answered, it just had nothing usable to say. Counting it
            # as a failure meant 5 borderline patient messages in a row opened
            # the Gemini breaker for 60s FOR EVERY TENANT. Treat as liveness:
            # don't increment failures; a successful probe closes the circuit.
            with self._lock:
                if self._state == self.HALF_OPEN:
                    self._state    = self.CLOSED
                    # v16g2 FIX N12: match the success path — a breaker
                    # "recovered" via an empty-reply probe otherwise kept
                    # failures at 4 and re-opened on the next single blip.
                    self._failures = 0
                    log.info(f"⚡ CircuitBreaker [{self.name}] → CLOSED "
                             f"(probe answered, empty reply)")
            raise
        except Exception:
            with self._lock:
                self._failures += 1
                if is_probe or self._state == self.HALF_OPEN:
                    # probe failed → straight back to OPEN, restart the timer.
                    self._state          = self.OPEN
                    self._opened_at      = time.monotonic()
                    log.error(f"⚡ CircuitBreaker [{self.name}] → OPEN (probe failed)")
                elif self._failures >= self._threshold:
                    self._state     = self.OPEN
                    self._opened_at = time.monotonic()
                    log.error(f"⚡ CircuitBreaker [{self.name}] → OPEN (failures={self._failures})")
            raise
        finally:
            # v16g5 FIX R5-H2: the ONLY place the probe gate is released.
            if is_probe:
                with self._lock:
                    self._probe_inflight = False


_gemini_breaker   = CircuitBreaker("Gemini",   failure_threshold=5, reset_timeout=60.0)
_openai_breaker   = CircuitBreaker("OpenAI",   failure_threshold=5, reset_timeout=60.0)
_claude_breaker   = CircuitBreaker("Claude",   failure_threshold=5, reset_timeout=60.0)
_whatsapp_breaker  = CircuitBreaker("WhatsApp",  failure_threshold=3, reset_timeout=30.0)
_instagram_breaker = CircuitBreaker("Instagram", failure_threshold=3, reset_timeout=30.0)  # v10
_qdrant_breaker    = CircuitBreaker("Qdrant",    failure_threshold=3, reset_timeout=30.0)  # v12 #23


class AIEmptyResponse(Exception):
    """v14g3 BUG 18: raised when a provider returns no usable text (e.g. a safety
    block). Treated as 'this provider had no answer' → fall through to the next
    one WITHOUT retry-spamming and without slamming the circuit breaker."""
