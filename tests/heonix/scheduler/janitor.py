"""HEONIX GEN-5 · module `heonix.scheduler.janitor`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 8403-8552).
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

from heonix.cache import (brain_cache)
from heonix.concurrency import (_shutdown_event)
from heonix.config import (_env_int, cfg)
from heonix.db.core import (_execute)
from heonix.db.store import (_process_outbox)
from heonix.logsetup import (log)
from heonix.scheduler.jobs import (
    _scheduler_followups,
    _scheduler_retention_purge,
    _scheduler_send_reminders,
)
from heonix.utils import (_iso_in, _now)
from heonix import _latebind  # GEN-5 SPLIT
_db_pool: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.db.core at startup
_latebind.register('_db_pool', __name__)


def _janitor_loop() -> None:
    """v12: tighter cadence + real housekeeping.
    Every OUTBOX_TICK seconds → drain the outbox and prune expired in-process
    cache keys (#35). Roughly hourly → delete stale idempotency keys, finished
    outbox rows (#25), and old webhook_log rows (#32); re-queue any outbox row
    left 'processing' by a crashed worker."""
    tick        = max(5, _env_int("OUTBOX_TICK", "20"))
    med_every   = max(1, int(300 / tick))      # v14g4: ~ every 5 minutes
    n = 0
    # v16g5 FIX R5-H6b: the heavy block used to fire on `n % heavy_every`,
    # where `n` is a PER-PROCESS tick counter reset on every restart. A worker
    # recycled more often than hourly — the norm on Render's free tier — never
    # reached the heavy block AT ALL: bookings never flipped to 'completed',
    # idempotency/webhook_log/done-outbox never pruned, stuck rows never
    # requeued. v16g6 FIX R6-H3: anchor to a SHARED expiring lease — the
    # only clock that survives restarts AND elects one leader fleet-wide.
    while not _shutdown_event.wait(timeout=tick):
        n += 1
        # v16g4 FIX O1: every gunicorn worker ran the drain each tick — N
        # workers = N near-simultaneous claim sweeps hammering the same rows
        # (claims are row-atomic, so no double-send — this is pure wasted DB
        # churn). Same single-leader lease the scheduler uses; a short TTL so
        # a crashed leader is replaced within one tick.
        _ob_lease = brain_cache.lock("outbox:drain", ttl=max(5, tick - 1))
        if _ob_lease:
            try:
                _process_outbox()
            except Exception as exc:
                log.warning(f"⚠️  Janitor (outbox) error: {exc}")
            finally:
                # v16g5 FIX R5-M10: the lease was ACQUIRED every tick and never
                # RELEASED, so it expired on its own ~1s before the next tick.
                # Janitors across workers aren't tick-synchronised, so a worker
                # waking inside that window found it held and skipped — some
                # ticks NOBODY drained, doubling worst-case welcome/reminder
                # latency for no reason. Release it the moment we're done.
                try:
                    # v16g6 FIX R6-H2: delete("lock:outbox:drain") only ever
                    # worked on Redis, where prefix concatenation lined up by
                    # coincidence. The local store writes "__lock__outbox:drain",
                    # so in no-Redis mode the R5-M10 release was a NO-OP and
                    # the skipped-tick behaviour it removed came straight back
                    # — and a raw delete bypasses the holder-token check, so
                    # any worker could free any holder's lease. Use the real
                    # check-and-del release.
                    brain_cache.unlock("outbox:drain", _ob_lease)
                except Exception:
                    pass
        try:
            brain_cache.prune_local()          # v12 #35
        except Exception:
            pass

        # v14g4: scheduler (reminders + cold-lead follow-ups) on a 5-min cadence.
        # Flag-gated OFF by default; needs a long-lived process (true on Render).
        if cfg.ENABLE_SCHEDULER and (n % med_every == 0):
            # v14g5 FIX 7: single-leader lock so reminders/follow-ups run on exactly
            # ONE worker per tick. Every gunicorn worker runs a janitor → without
            # this the same reminder went out once PER worker. Lease is intentionally
            # NOT released early; its TTL (~the cadence) blocks a second run.
            _lease = brain_cache.lock("sched:cycle", ttl=cfg.SCHED_LOCK_TTL)
            if _lease:
                try:
                    _scheduler_send_reminders()
                except Exception as exc:
                    log.warning(f"⚠️  scheduler (reminders) error: {exc}")
                try:
                    _scheduler_followups()
                except Exception as exc:
                    log.warning(f"⚠️  scheduler (followups) error: {exc}")

        # v16g6 FIX R6-H3: R5-H6b swapped a per-process TICK counter for a
        # per-process MONOTONIC timer — `_last_heavy` re-armed on every boot,
        # so a worker recycled faster than hourly (the Render free-tier norm)
        # STILL never reached this block: bookings never flipped to
        # 'completed', idempotency/webhook_log/done-outbox never pruned,
        # stuck rows never requeued — the named failure was unchanged, only
        # the mechanism moved. The gate must live OUTSIDE the process: one
        # shared expiring setnx = hourly cadence AND single-leader election
        # in a single atomic call (no-Redis dev degrades to per-process,
        # the documented single-worker case).
        if not brain_cache.setnx("janitor:heavy:ran", ttl=3600):
            continue

        now_     = datetime.now(timezone.utc)
        day_ago  = (now_ - timedelta(days=1)).isoformat()
        week_ago = (now_ - timedelta(days=7)).isoformat()
        stuck    = (now_ - timedelta(minutes=15)).isoformat()
        # v16g5 FIX R5-H6 (HIGH): all seven statements below shared ONE
        # transaction and ONE `except`. Any single failure — a missing column
        # on a partly-migrated DB, a lock timeout, one bad row — rolled back
        # ALL of them, permanently, once an hour, forever. Bookings never
        # flipped to 'completed' (so the retention purge's completed-branch
        # stayed dead code, defeating FIX N7), and nothing ever pruned. Each
        # statement now runs in its OWN transaction and is fault-isolated, the
        # discipline the migration code has used since v11.
        _chores = [
            # v16g2 FIX N7: past appointments become 'completed' so their
            # enc_phone/enc_name PII stops being immortal.
            ("bookings→completed",
             "UPDATE bookings SET status='completed', updated_at=? "
             "WHERE status='booked' AND slot_end < ?", (_now(), now_.isoformat())),
            ("idempotency prune",
             "DELETE FROM idempotency_keys WHERE created_at < ?", (day_ago,)),
            ("outbox done prune",
             "DELETE FROM outbox WHERE status='done' AND created_at < ?", (day_ago,)),
            # v16g2 FIX M11: a stuck row that has burned its attempt budget
            # becomes 'failed' (visible, cleanable) instead of a zombie the
            # claimer's attempts<5 filter can never pick up again.
            # v15 FIX 7: measure from the CLAIM time, not row creation.
            ("stuck-row requeue",
             "UPDATE outbox SET attempts=attempts+1, next_attempt_at=?, "
             "status = CASE WHEN attempts >= 4 THEN 'failed' ELSE 'pending' END "
             "WHERE status='processing' AND COALESCE(processed_at, created_at) < ?",
             (_iso_in(30), stuck)),
            # v16g2 FIX M11: dead-letters stay visible for a week, then out.
            ("dead-letter prune",
             "DELETE FROM outbox WHERE status='failed' AND created_at < ?", (week_ago,)),
            ("webhook_log prune",
             "DELETE FROM webhook_log WHERE processed_at < ?", (week_ago,)),
            # v16g5 FIX R5-L9 companion: opt-outs are permanent by design and
            # are deliberately NOT pruned here.
            # v16g6 FIX R6-C3: a pending row that no claimer ever picked up
            # (attempts stuck, next_attempt_at pathologies) was retained
            # FOREVER with its payload — nothing pruned status='pending'.
            # A week-old undelivered welcome/reminder is dead either way.
            ("outbox pending age-out",
             "DELETE FROM outbox WHERE status='pending' AND created_at < ?",
             (week_ago,)),
        ]
        _ok = _fail = 0
        for _label, _sql, _prm in _chores:
            try:
                with _db_pool.get() as conn:
                    _execute(conn, _sql, _prm)
                _ok += 1
            except Exception as exc:
                _fail += 1
                log.warning(f"⚠️  Janitor chore '{_label}' failed "
                            f"(others continue): {exc}")
        log.info(f"🧹 Janitor: housekeeping {_ok} ok, {_fail} failed.")
        # v14g4: DPDP retention purge (chat logs + dead bookings) — no-op unless
        # DATA_RETENTION_DAYS > 0. Never touches live CRM/lead data.
        if cfg.ENABLE_SCHEDULER:
            _rlease = brain_cache.lock("sched:retention", ttl=cfg.SCHED_LOCK_TTL)  # FIX 7
            if _rlease:
                try:
                    _scheduler_retention_purge()
                except Exception as exc:
                    log.warning(f"⚠️  Janitor (retention) error: {exc}")
