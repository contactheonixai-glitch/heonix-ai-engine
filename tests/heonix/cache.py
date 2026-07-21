"""HEONIX GEN-5 · module `heonix.cache`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 2613-2955).
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

from heonix.config import (cfg)
from heonix.logsetup import (log)


class DistributedCache:
    def __init__(self, redis_url: str, default_ttl: int = 600):
        self._ttl   = default_ttl
        self._redis = None
        self._local: Dict[str, Tuple[Any, float]] = {}
        self._lock  = threading.Lock()
        if redis_url and REDIS_AVAILABLE:
            try:
                # v15g3 FIX 3 (MED): managed Redis (Render/Upstash) silently drops
                # idle connections. Without health_check_interval the FIRST command
                # after an idle gap failed, the blanket except ate it, and that call
                # silently fell to the per-process dict — the exact stale-brain
                # split FIX H2 fought, just triggered by idleness instead of JSON.
                # health_check_interval PINGs a stale socket before reuse;
                # retry_on_timeout absorbs one transient stall; keepalive stops
                # NAT/proxy idle reaping; connect timeout bounds boot-time hangs.
                r = redis_lib.from_url(redis_url, decode_responses=True,
                                       socket_timeout=2,
                                       socket_connect_timeout=2,
                                       retry_on_timeout=True,
                                       health_check_interval=30,
                                       socket_keepalive=True)
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
                # v15g2 FIX H2 (HIGH): Postgres brain/route rows carry datetime
                # objects (TIMESTAMPTZ) — plain json.dumps raised TypeError, the
                # blanket except swallowed it, and the value silently fell into
                # the PER-PROCESS dict below. Result on PG + multi-worker: every
                # cache-bust (token re-attach, /channel edit, soft-delete, FIX 8
                # self-heal) cleared Redis + ONE worker; the other workers kept
                # serving the stale brain (dead token included) for up to the
                # full TTL. default=str makes the row Redis-safe; consumers
                # already str() the timestamp fields, so nothing else changes.
                self._redis.setex(f"heonix:{key}", ttl or self._ttl,
                                  json.dumps(value, default=str))
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

    def incr_checked(self, key: str, ttl: int = 60) -> Tuple[int, bool]:
        """Atomic increment. v16g2 FIX L11: returns (count, distributed) — the
        second element tells the caller whether the increment actually landed
        in Redis (fleet-wide) or fell back to this process's dict, so the rate
        limiter can shrink its budget during a live-Redis blip instead of
        silently letting the fleet allow rpm × workers again."""
        if self._redis:
            try:
                pipe = self._redis.pipeline()
                pipe.incr(f"heonix:{key}")
                pipe.expire(f"heonix:{key}", ttl)
                result = pipe.execute()
                return result[0], True
            except Exception:
                pass
        with self._lock:
            # v12 #42/#35: the old code reused an EXPIRED window's count and
            # never dropped stale keys → a user who once hit the limit stayed
            # banned forever and the dict grew unbounded. Now an elapsed window
            # resets to 1 and expired keys are eligible for prune_local().
            now   = time.monotonic()
            entry = self._local.get(key)
            if entry is None or now >= entry[1]:
                self._local[key] = (1, now + ttl)
                return 1, False
            new_val = entry[0] + 1
            self._local[key] = (new_val, entry[1])
            return new_val, False

    def incr(self, key: str, ttl: int = 60) -> int:
        """Back-compat shim over incr_checked (v16g2 FIX L11)."""
        return self.incr_checked(key, ttl)[0]

    def get_pinned(self, key: str, distributed: bool) -> Optional[Any]:
        """v16g4 FIX M14: read from the SAME backend a paired incr_checked
        landed in. The sliding-window limiter's two reads (current-minute INCR,
        previous-minute GET) could split across Redis and the local dict during
        a blip — the weighted window then quietly degraded to a per-process
        fixed window. Pinning the read keeps the two terms coherent; if the
        pinned backend can't answer, the caller gets None and knowingly falls
        back to a fixed window on ONE consistent backend."""
        if distributed:
            if not self._redis:
                return None
            try:
                val = self._redis.get(f"heonix:{key}")
                return json.loads(val) if val else None
            except Exception:
                return None
        with self._lock:
            entry = self._local.get(key)
            if entry and time.monotonic() < entry[1]:
                return entry[0]
        return None

    def setnx(self, key: str, ttl: int) -> bool:
        """v12: atomic 'claim this key exactly once'. Returns True only for the
        single caller that won the claim. On Redis this is SET key 1 NX EX ttl
        (atomic across ALL gunicorn workers) — this is what makes webhook dedupe
        race-proof (#11/#38/#44). Local fallback is lock-guarded."""
        if self._redis:
            try:
                return bool(self._redis.set(f"heonix:{key}", "1", nx=True, ex=ttl))
            except Exception:
                pass
        with self._lock:
            now   = time.monotonic()
            entry = self._local.get(key)
            if entry is not None and now < entry[1]:
                return False
            self._local[key] = (1, now + ttl)
            return True

    def delete_prefix(self, prefix: str) -> int:
        """v16g4 FIX L12: bulk-delete every key under a prefix (Redis SCAN +
        local dict sweep). Used by DPDP erasure to flush the `resp:` reply
        cache — those entries are keyed on message CONTENT, so a message that
        contained the subject's own details can sit cached (and replayable to
        the next patient who types the same text) for the full TTL. There is
        no per-subject index into a content-hash cache, so erasure flushes
        the whole prefix; it is a perf cache and rebuilds on demand."""
        removed = 0
        if self._redis:
            try:
                # v16g6 FIX R6-L9: one DELETE per key made erasure's resp:*
                # flush a few thousand sequential round-trips inside a
                # request. Pipeline in batches of 500.
                _batch = []

                def _flush(_b):
                    _pipe = self._redis.pipeline(transaction=False)
                    for _bk in _b:
                        _pipe.delete(_bk)
                    return sum(1 for _r in _pipe.execute() if _r)

                for k in self._redis.scan_iter(match=f"heonix:{prefix}*",
                                               count=500):
                    _batch.append(k)
                    if len(_batch) >= 500:
                        removed += _flush(_batch)
                        _batch = []
                if _batch:
                    removed += _flush(_batch)
            except Exception:
                pass
        with self._lock:
            stale = [k for k in self._local if k.startswith(prefix)]
            for k in stale:
                self._local.pop(k, None)
                removed += 1
        return removed

    def prune_local(self) -> int:
        """v12 #35: drop expired in-process entries so the local fallback can't
        leak RAM. Cheap no-op when Redis is the backend (local dict stays tiny)."""
        removed = 0
        with self._lock:
            now    = time.monotonic()
            stale  = [k for k, v in self._local.items()
                      if isinstance(v, tuple) and len(v) == 2 and now >= v[1]]
            for k in stale:
                self._local.pop(k, None)
                removed += 1
        return removed

    # v14g5 FIX 6/7: cross-worker mutex (per-conversation) + single-leader lock
    # (scheduler). On Redis these are atomic across ALL gunicorn workers: SET NX EX
    # with a random token, released only by the holder via a check-and-del (Lua).
    # Local fallback is lock-guarded — single-process dev only, so in prod you MUST
    # set REDIS_URL (STRICT_PROD already enforces this) for these to be real.
    def lock(self, name: str, ttl: int) -> Optional[str]:
        token = uuid.uuid4().hex
        if self._redis:
            try:
                if self._redis.set(f"heonix:lock:{name}", token, nx=True, ex=ttl):
                    return token
                return None
            except Exception:
                pass
        with self._lock:
            now   = time.monotonic()
            entry = self._local.get(f"__lock__{name}")
            if entry is not None and now < entry[1]:
                return None
            self._local[f"__lock__{name}"] = (token, now + ttl)
            return token

    def unlock(self, name: str, token: str) -> None:
        if not token:
            return
        if self._redis:
            try:
                lua = ("if redis.call('get', KEYS[1]) == ARGV[1] then "
                       "return redis.call('del', KEYS[1]) else return 0 end")
                self._redis.eval(lua, 1, f"heonix:lock:{name}", token)
                return
            except Exception:
                pass
        with self._lock:
            entry = self._local.get(f"__lock__{name}")
            if entry and entry[0] == token:
                self._local.pop(f"__lock__{name}", None)

    def renew(self, name: str, token: str, ttl: int) -> bool:
        """v15g2 FIX M4: extend a held lock's TTL (only if we still hold it).
        Lets a drain heartbeat keep the per-conversation lease alive through a
        slow AI turn instead of silently losing exclusivity at CONV_LOCK_TTL."""
        if not token:
            return False
        if self._redis:
            try:
                lua = ("if redis.call('get', KEYS[1]) == ARGV[1] then "
                       "return redis.call('expire', KEYS[1], ARGV[2]) else return 0 end")
                return bool(self._redis.eval(lua, 1, f"heonix:lock:{name}",
                                             token, int(ttl)))
            except Exception:
                return False
        with self._lock:
            entry = self._local.get(f"__lock__{name}")
            if entry and entry[0] == token:
                self._local[f"__lock__{name}"] = (token, time.monotonic() + ttl)
                return True
        return False

    def ping(self) -> bool:
        """v14g5 FIX 48: live Redis health, not just 'a client object exists'."""
        if not self._redis:
            return False
        try:
            return bool(self._redis.ping())
        except Exception:
            return False


brain_cache = DistributedCache(cfg.REDIS_URL, default_ttl=cfg.CACHE_TTL)


# ─────────────────────────────────────────────────────────────────────────────
# 🪙  PER-CUSTOMER FIXED-WINDOW RATE LIMITER  (v8 FIX #8 · v16g2 FIX C9)
#     Limits per customer_id, not just IP — prevents one customer starving others
# ─────────────────────────────────────────────────────────────────────────────
class CustomerRateLimiter:
    """
    SLIDING-WINDOW-approximation rate limiter keyed on customer_id.
    v16g2 FIX C9 corrected the docstring to fixed-window; v16g3 FIX R3-M9
    upgrades the algorithm: current-minute count + previous-minute count
    weighted by window overlap (the standard CDN approximation), so the old
    2× burst at every :00 boundary (60 msgs at :59 + 60 at :00 in ~2s per
    conversation — the exact flood this limiter exists for) is gone. Redis
    for distributed accuracy; falls back to in-process.
    """
    def __init__(self, requests_per_minute: int = 60):
        self._rpm = requests_per_minute

    def _effective_rpm(self, distributed: bool) -> int:
        # v14g3 BUG 8: with Redis, INCR is shared across all workers, so the
        # limit is global and exact. WITHOUT Redis the counter is per-process,
        # so N gunicorn workers would EACH allow the full rpm (aggregate =
        # rpm × N). Divide by the worker count in that fallback so the whole
        # fleet stays close to the intended limit.
        # v16g2 FIX L11: the divisor now keys off whether THIS increment
        # actually landed in Redis — not off "a client object exists". During a
        # live-Redis error, incr falls back to the per-process dict; the old
        # object-existence check kept returning the full rpm for the blip.
        if distributed:
            return self._rpm
        workers = max(1, cfg.WEB_CONCURRENCY)
        return max(1, self._rpm // workers)

    # v16g5 FIX R5-L5: the window math below ran on time.time() — a WALL
    # clock. An NTP step BACKWARDS re-opens a window a caller already spent
    # (limit silently doubles); a step FORWARDS skips one (legitimate patients
    # dropped). Every other timer in this file already uses time.monotonic().
    # v16g6 FIX R6-L11: pinning time.time()-time.monotonic() AT IMPORT made
    # the anchor itself per-process — workers booted either side of an NTP
    # step (or drifted apart over a long uptime) computed different `win`
    # ids for the same instant, and the fleet limiter silently degraded to
    # per-worker: the exact failure R5-L5 existed to fix. Fleet-comparable
    # ids need the fleet's shared clock: time.time() directly. An NTP step
    # now glitches at most ONE window and self-heals; permanent cross-worker
    # skew is gone.
    @classmethod
    def _wall(cls) -> float:
        return time.time()

    def is_allowed(self, customer_id: str) -> bool:
        # v16g3 FIX R3-M9: sliding-window approximation. ttl 120 keeps the
        # previous minute's counter readable for the weighted term.
        now  = self._wall()                       # v16g5 FIX R5-L5
        win  = int(now // 60)
        count, distributed = brain_cache.incr_checked(
            f"rl:{customer_id}:{win}", ttl=120)     # v16g2 FIX L11 signal kept
        # v16g4 FIX M14: previous-minute read pinned to the backend the
        # increment landed in — never mix Redis-current with local-previous.
        prev = brain_cache.get_pinned(f"rl:{customer_id}:{win - 1}", distributed)
        try:
            prev_n = int(prev) if prev is not None else 0
        except (TypeError, ValueError):
            prev_n = 0
        weight = 1.0 - ((now % 60) / 60.0)
        return (count + prev_n * weight) <= self._effective_rpm(distributed)

    def check(self, customer_id: str):
        """Call this in route handlers. Returns True if the request is allowed.
        v15 FIX 21: the old docstring promised (allowed, count) — anyone
        unpacking it would have crashed."""
        return self.is_allowed(customer_id)


customer_limiter = CustomerRateLimiter(requests_per_minute=60)
