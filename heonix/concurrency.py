"""HEONIX GEN-5 · module `heonix.concurrency`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 3537-3773).
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
from heonix.config import (_env_int, cfg)
from heonix.logsetup import (log)


_WORKER_POOL = ThreadPoolExecutor(
    max_workers=_env_int("WORKER_THREADS", "8"),
    thread_name_prefix="heonix-bg",
)

# v14g3 BUG 5: the ordered per-conversation drains run on _WORKER_POOL and hold
# a thread for the ENTIRE duration of an AI call. Previously fire-and-forget
# work (owner alerts, audit writes, RAG stores, outbox sends) was submitted to
# the SAME pool, so it queued behind slow AI calls and, under load, the 8 drain
# threads and competing bg tasks throttled each other (head-of-line blocking).
# Side-effect I/O now gets its OWN pool, fully decoupled from the drains.
_IO_POOL = ThreadPoolExecutor(
    max_workers=_env_int("IO_THREADS", "16"),
    thread_name_prefix="heonix-io",
)

# v15 FIX 1 (CRITICAL): this Event was referenced by the janitor loop (its very
# first statement) and by the shutdown handler — but it was NEVER DEFINED. The
# janitor thread therefore died with a NameError milliseconds after every boot,
# silently killing: the periodic outbox drain, stuck-'processing' row recovery,
# idempotency/webhook_log cleanup, in-process cache pruning (a slow RAM leak in
# no-Redis mode), the ENTIRE Gen-4 scheduler (reminders + follow-ups), and the
# DPDP retention purge. One line. This one line is v15's biggest upgrade.
_shutdown_event = threading.Event()


_IO_QUEUE_MAX = _env_int("IO_QUEUE_MAX", "2000")     # v16g5 FIX R5-L7


def submit_bg(fn: Callable, *args, **kwargs) -> None:
    """Fire-and-forget onto the dedicated I/O pool (v14g3 BUG 5 — kept separate
    from the conversation-drain pool so alerts/audit/RAG never queue behind a
    slow AI call). Never raises into the caller. If the pool is shutting down
    (SIGTERM in flight), runs inline so in-progress work is never lost."""
    # v16g5 FIX R5-L7: the pool is bounded in THREADS, not in QUEUED WORK.
    # ThreadPoolExecutor's work queue is unbounded, so .submit() never raises
    # under load — it just grows RAM until the dyno is OOM-killed, and the
    # RuntimeError fallback below only fires AFTER shutdown. Shed load at an
    # explicit depth instead: audit/analytics writes are the right thing to
    # drop when the box is already drowning, and a dropped one is now COUNTED
    # rather than silently swallowing memory.
    try:
        _q = getattr(_IO_POOL, "_work_queue", None)
        if _q is not None and _q.qsize() > _IO_QUEUE_MAX:
            analytics.inc("bg.shed")
            if brain_cache.setnx("warn:bg_queue", ttl=300):
                log.error(f"🛑 background I/O queue over {_IO_QUEUE_MAX} deep — "
                          f"shedding fire-and-forget work (v16g5 FIX R5-L7). "
                          f"The box is saturated; scale workers or check for a "
                          f"stalled outbound provider.")
            return
    except Exception:
        pass
    try:
        _IO_POOL.submit(fn, *args, **kwargs)
    except RuntimeError:
        # v16g4 FIX L10: the old inline fallback ran the task ON THE CALLER'S
        # thread during shutdown — a webhook 200 could block behind a live
        # Meta call. A plain daemon thread is unbounded but shutdown-scoped:
        # only reachable after _IO_POOL rejects, i.e. for the final seconds
        # of a SIGTERM drain, so it cannot become the pre-v11 thread
        # explosion. In-progress work is still never lost and the caller
        # returns immediately.
        try:
            threading.Thread(target=fn, args=args, kwargs=kwargs,
                             daemon=True,
                             name="heonix-bg-shutdown").start()
        except Exception as exc:
            log.error(f"❌ shutdown bg fallback failed: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 🔢  v14 BUG 43 FIX — PER-CONVERSATION ORDERED EXECUTION
#   Problem: webhook handlers pushed every inbound message onto an 8-thread pool.
#   A ThreadPoolExecutor gives NO ordering guarantee, so a patient firing 3 quick
#   messages could have msg #3 processed before msg #1 → the history handed to the
#   AI is scrambled → wrong/contradictory reply, and replies arrive out of order.
#
#   Fix: tasks that share a key (one conversation = one patient on one business
#   line) run STRICTLY in submission order, one at a time, on a single drainer.
#   Different keys still run fully in parallel across the pool — so global
#   throughput is unchanged, only per-conversation order is enforced.
# ─────────────────────────────────────────────────────────────────────────────
# v16g4 FIX P6: one shared renewer for every in-flight conversation lease —
# the old design spawned a fresh heartbeat THREAD per message (thread churn on
# every single webhook) just to renew one lock. Registry + single daemon
# scanner; drains register on acquire and deregister in finally.
_LEASE_REG: Dict[str, str] = {}
_LEASE_REG_LOCK = threading.Lock()
_LEASE_SCANNER_ON = False


def _lease_scanner() -> None:
    while not _shutdown_event.wait(max(5, cfg.CONV_LOCK_TTL // 3)):
        with _LEASE_REG_LOCK:
            items = list(_LEASE_REG.items())
        for _k, _lease in items:
            try:
                brain_cache.renew(f"conv:{_k}", _lease, cfg.CONV_LOCK_TTL)
            except Exception:
                pass


def _ensure_lease_scanner() -> None:
    global _LEASE_SCANNER_ON
    with _LEASE_REG_LOCK:
        if _LEASE_SCANNER_ON:
            return
        _LEASE_SCANNER_ON = True
    threading.Thread(target=_lease_scanner, daemon=True,
                     name="conv-lease-scan").start()


class OrderedKeyedRunner:
    """Serializes tasks per key (FIFO), parallel across keys. Exactly one drainer
    is live per active key at any moment (enforced under a single lock), which is
    what makes the ordering race-proof even while many messages arrive at once."""

    def __init__(self, pool: ThreadPoolExecutor, max_pending_per_key: int = 50):
        self._pool      = pool
        self._max_q     = max_pending_per_key
        self._queues: Dict[str, deque] = {}
        self._active: set               = set()
        self._lock      = threading.Lock()

    def submit(self, key: str, fn: Callable, *args, **kwargs) -> bool:
        """Queue a task for `key`. Returns False if this key's backlog is full
        (flood guard — a single conversation can't OOM the dyno) — the caller
        treats that exactly like a dropped/duplicate inbound message."""
        start = False
        with self._lock:
            q = self._queues.get(key)
            if q is None:
                q = deque()
                self._queues[key] = q
            if len(q) >= self._max_q:
                analytics.inc("ordered.queue_full")
                return False
            q.append((fn, args, kwargs))
            if key not in self._active:
                self._active.add(key)
                start = True
        if start:
            try:
                self._pool.submit(self._drain, key)
            except RuntimeError:
                # pool shutting down (SIGTERM) → drain inline so nothing is lost
                self._drain(key)
        return True

    def _drain(self, key: str) -> None:
        while True:
            with self._lock:
                q = self._queues.get(key)
                if not q:
                    # confirmed empty under lock → release the key. A submit that
                    # races in right after will see key not-active and start a
                    # fresh drainer, so no item is ever stranded.
                    self._active.discard(key)
                    self._queues.pop(key, None)
                    return
                fn, args, kwargs = q.popleft()
            # v14g5 FIX 6: take a CROSS-WORKER per-conversation mutex so the same
            # conversation can't be processed concurrently on two gunicorn workers
            # (which would interleave and scramble history). Bounded wait — if we
            # can't acquire it we proceed rather than stall forever. NOTE: this stops
            # concurrent corruption, but strict ARRIVAL order across separate POSTs
            # landing on different workers still needs WEB_CONCURRENCY=1 (use threads).
            lease  = None
            waited = 0.0
            _nap   = 0.05
            while waited < cfg.CONV_LOCK_WAIT_SECS:   # v15g4 FIX D2: env-tunable
                lease = brain_cache.lock(f"conv:{key}", ttl=cfg.CONV_LOCK_TTL)
                if lease:
                    break
                time.sleep(_nap)                      # v16g4 FIX P6: growing nap
                waited += _nap
                _nap = min(0.4, _nap * 2)             # 20 Hz spin → gentle backoff
            # v15g2 FIX M4: worst-case AI path (MAX_RETRIES×AI_TIMEOUT + backoff,
            # × up to 3 fallback providers) can run for minutes — far past
            # CONV_LOCK_TTL (60s). The lease then expired MID-TURN, another
            # worker could grab the same conversation, and the exact
            # interleaving FIX 6 exists to prevent came back precisely when the
            # AI was slow. A tiny heartbeat renews the lease while fn runs; it
            # stops the instant fn returns (bounded: one sleeping thread per
            # in-flight drain, ≤ pool size).
            if lease:
                # v16g4 FIX P6: register with the shared scanner (replaces the
                # per-task heartbeat thread — same mid-turn renewal guarantee
                # from v15g2 FIX M4, minus one thread spawn per message).
                _ensure_lease_scanner()
                with _LEASE_REG_LOCK:
                    _LEASE_REG[key] = lease
            try:
                fn(*args, **kwargs)
            except Exception as exc:
                log.error(f"❌ ordered task error [{key}]: {exc}", exc_info=True)
            finally:
                if lease:
                    with _LEASE_REG_LOCK:
                        _LEASE_REG.pop(key, None)
                    brain_cache.unlock(f"conv:{key}", lease)


_ORDERED = OrderedKeyedRunner(
    _WORKER_POOL,
    max_pending_per_key=_env_int("ORDERED_MAX_PENDING", "50"),
)


def submit_ordered(key: str, fn: Callable, *args, **kwargs) -> bool:
    """Public entry: run fn in-order for `key`. False = backlog full (drop)."""
    return _ORDERED.submit(key, fn, *args, **kwargs)


# ── v12: a tiny separate executor used ONLY to put a hard wall-clock ceiling on
#    a blocking call (RAG embed / vector search). Kept distinct from _WORKER_POOL
#    so a timeout wrapper can never end up waiting on the same pool it runs in.
_TIMEOUT_POOL = ThreadPoolExecutor(
    max_workers=_env_int("TIMEOUT_THREADS", "8"),   # v14g3 BUG 6: was 4
    thread_name_prefix="heonix-to",
)


def _call_with_timeout(fn: Callable, timeout: float, *args, **kwargs):
    """Run fn with a hard wall-clock ceiling; raises TimeoutError on overrun so
    the surrounding circuit breaker counts it as a failure (v12 #9/#23).

    v14g3 BUG 6 — HONEST LIMITATION: Python cannot cancel a running thread, so on
    timeout the underlying call keeps executing until it returns on its own. The
    REAL guard is the breaker: a few RAG timeouts open the Qdrant breaker, which
    then short-circuits further submits for reset_timeout seconds — so leaked
    threads drain instead of piling up. We also doubled this pool (4 → 8) for
    headroom, and RAG is now the ONLY caller: the primary AI calls use native SDK
    timeouts (BUG 2), which need no extra thread at all."""
    fut = _TIMEOUT_POOL.submit(fn, *args, **kwargs)
    return fut.result(timeout=timeout)
