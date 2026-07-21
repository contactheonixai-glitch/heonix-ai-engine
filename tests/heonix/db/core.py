"""HEONIX GEN-5 · module `heonix.db.core`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 1667-2610, 5864-5983).
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
from heonix.concurrency import (submit_bg)
from heonix.config import (cfg)
from heonix.logsetup import (log)
from heonix.security.crypto import (_crm_phone_hash, pii_vault)
from heonix.utils import (_now)
from heonix import _latebind  # GEN-5 SPLIT


class PostgreSQLPool:
    """
    Production PostgreSQL pool via psycopg2.
    v8 adds optional read-replica pool for SELECT queries.
    """

    def __init__(self, dsn: str, min_conn: int = 2, max_conn: int = 20,
                 replica_dsn: str = ""):
        if not POSTGRES_AVAILABLE:
            raise RuntimeError("psycopg2 not installed. pip install psycopg2-binary")
        # v16g4 FIX HF3 (hotfix, 20-Jul): managed Postgres (Render/Neon)
        # closes idle TLS connections; a stale pooled handle then dies on
        # next use with "SSL SYSCALL error: EOF" / "bad record mac" — the H5
        # self-heal already discards them, but keepalives stop most handles
        # from going stale in the first place.
        _ka = dict(keepalives=1, keepalives_idle=30,
                   keepalives_interval=10, keepalives_count=3)
        self._write = psycopg2.pool.ThreadedConnectionPool(
            minconn=min_conn, maxconn=max_conn, dsn=dsn, **_ka)
        self._read  = None
        if replica_dsn:
            try:
                self._read = psycopg2.pool.ThreadedConnectionPool(
                    minconn=2, maxconn=max_conn, dsn=replica_dsn, **_ka)
                log.info("🐘 PostgreSQL read-replica pool ready.")
            except Exception as exc:
                log.warning(f"⚠️  Read replica unavailable ({exc}) — reads use primary.")
        log.info(f"🐘 PostgreSQL write pool ready — min={min_conn} max={max_conn}")

    @contextmanager
    def get(self, read_only: bool = False) -> Generator:
        pool = (self._read or self._write) if read_only else self._write
        conn = pool.getconn()
        # v14g5 FIX 41: read paths use autocommit so pure SELECTs don't churn an
        # empty COMMIT every call; write paths keep explicit transaction control.
        conn.autocommit = bool(read_only)
        # v16g4 FIX H5: the v15g3 FIX 4 poisoned-connection self-heal was
        # SQLite-only. Here: if commit raised and rollback ALSO raised, the
        # broken handle was still putconn()'d back into the pool for the next
        # caller — and psycopg2's own putconn() runs a rollback that can raise
        # *from the finally*, masking the original error. Now: rollback is
        # best-effort; a connection whose rollback failed (or that reports
        # closed) is marked poisoned and returned with close=True so the pool
        # discards it and opens a fresh one; putconn itself is wrapped so a
        # putconn failure can never shadow the real exception.
        poisoned = False
        try:
            yield conn
            if not read_only:
                conn.commit()
        except Exception:
            if not read_only:
                try:
                    conn.rollback()
                except Exception as rb_exc:
                    poisoned = True
                    log.error(f"🛑 PG rollback failed on poisoned connection "
                              f"— discarding handle: {rb_exc}")
            raise
        finally:
            try:
                if getattr(conn, "closed", 0):
                    poisoned = True
                pool.putconn(conn, close=poisoned)
            except Exception as put_exc:
                # Never let pool bookkeeping mask the caller's exception.
                log.error(f"🛑 PG putconn failed (handle dropped): {put_exc}")
                try:
                    conn.close()
                except Exception:
                    pass

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
    def get(self, read_only: bool = False) -> Generator:
        try:
            conn = self._pool.get(timeout=self._timeout)
        except queue.Empty:
            raise RuntimeError("SQLite pool exhausted")
        # v15g3 FIX 4 (MED): if commit/rollback themselves raised (disk I/O error,
        # interrupted WAL, closed handle) the OLD finally put the now-POISONED
        # connection straight back into the pool — every future borrower of that
        # slot then failed forever. On the SQLite path (what production runs on
        # Render TODAY) one bad write could brick 1/10th of all DB traffic until
        # restart. Now a connection that fails commit AND rollback is closed and
        # replaced with a fresh one, so the pool self-heals.
        broken = False
        try:
            yield conn
            # v16g5 FIX R5-L6: read_only was accepted and IGNORED, so every
            # SELECT ended in a COMMIT — pointless WAL churn and a write-lock
            # acquisition for a pure read on the path production runs today.
            if read_only:
                conn.rollback()
            else:
                conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                broken = True
            raise
        finally:
            if broken:
                try:
                    conn.close()
                except Exception:
                    pass
                try:
                    self._pool.put(self._new_conn())
                    log.warning("♻️  SQLite pool: poisoned connection replaced.")
                except Exception:
                    # v16g2 FIX N11: the old last-resort put the just-CLOSED
                    # handle back — that slot then failed forever ("Cannot
                    # operate on a closed database"), resurrecting the exact
                    # poisoned-slot bug this block exists to fix. Replenish in
                    # the background instead; a briefly smaller pool beats a
                    # permanently broken slot. (Correlated failure is the real
                    # case here: disk-full breaks rollback AND _new_conn.)
                    log.critical("🛑 SQLite pool: could not create a replacement "
                                 "connection — replenishing in background.")
                    def _replenish(_p=self._pool, _new=self._new_conn):
                        for _ in range(30):
                            time.sleep(2)
                            try:
                                _p.put(_new())
                                log.warning("♻️  SQLite pool: slot replenished.")
                                return
                            except Exception:
                                continue
                        log.critical("🛑 SQLite pool: replenish failed — pool "
                                     "is one slot smaller until restart.")
                    threading.Thread(target=_replenish, daemon=True,
                                     name="sqlite-replenish").start()
            else:
                self._pool.put(conn)

    def close_all(self) -> None:
        # v16g3 FIX R3-L11: empty() could lie between checks, and one failing
        # .close() aborted the whole drain. Pull-until-Empty; close best-effort.
        while True:
            try:
                conn = self._pool.get_nowait()
            except queue.Empty:
                break
            try:
                conn.close()
            except Exception:
                pass


_db_pool: Any = None
# v14g3 BUG 17: removed the dead db(read_only=...) helper. It was never called
# (every call site uses `_db_pool.get(...)` directly) and its read_only argument
# was silently ignored — a latent footgun if anyone had ever used it.


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
    channel       TEXT DEFAULT 'api',
    subject_hash  TEXT DEFAULT ''
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
    is_active     BOOLEAN DEFAULT TRUE,
    tenant_id     TEXT NOT NULL DEFAULT ''  -- v16g4 FIX M10: '' = fleet-wide
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
    attempts     INTEGER DEFAULT 0,
    next_attempt_at TEXT NOT NULL DEFAULT ''
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
    subject_hash  TEXT DEFAULT '',
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
    is_active  INTEGER DEFAULT 1,
    tenant_id  TEXT NOT NULL DEFAULT ''  -- v16g4 FIX M10: '' = fleet-wide
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
    attempts     INTEGER DEFAULT 0,
    next_attempt_at TEXT NOT NULL DEFAULT ''
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
            # v16g5 FIX R5-L4: the cursor was created inline and never closed
            # (it lived until GC), the one place in the file that skipped the
            # FIX L15 discipline. Multi-statement DDL still can't go through
            # _execute (it would ?→%s-translate the schema text), so close it
            # explicitly instead.
            _cur = conn.cursor()
            try:
                _cur.execute(schema)
            finally:
                try:
                    _cur.close()
                except Exception:
                    pass
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
    swallowed and the schema is still correct. On Postgres the DDL and the
    backfill SCAN each take their own try-advisory-xact lock — v16g6 FIX
    R6-H7: xact locks die with their transaction, and the backfill ran on a
    NEW connection, so the single lock above never actually covered it and
    every booting worker ran the full 5,000-row scan concurrently."""
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    if is_pg:
        # v16g5 FIX R5-C3 (LAUNCH-CRITICAL): this used a SESSION-scoped
        # pg_advisory_lock. Three compounding failures:
        #   1. a failing ALTER aborts the Postgres transaction, so the
        #      `finally` unlock ALSO fails ("current transaction is aborted");
        #   2. a session advisory lock SURVIVES ROLLBACK, so the pool handed
        #      that connection back with the lock still held;
        #   3. pg_advisory_lock BLOCKS WITH NO TIMEOUT, so the next worker to
        #      boot waited on it forever.
        # One bad migration could therefore wedge every subsequent boot until
        # the connection was killed by hand — and Render recycles workers
        # routinely. pg_advisory_xact_lock is transaction-scoped: Postgres
        # releases it on COMMIT *or* ROLLBACK, unconditionally. The try-variant
        # never blocks, so a losing worker skips instead of hanging.
        try:
            with _db_pool.get() as conn:
                _cur = _execute(conn, "SELECT pg_try_advisory_xact_lock(427011) AS got")
                _row = _cur.fetchone()
                _got = bool(_row["got"] if isinstance(_row, dict) else _row[0])
                if _got:
                    _execute(conn, "ALTER TABLE crm_contacts "
                                   "ADD COLUMN IF NOT EXISTS phone_hash TEXT DEFAULT ''")
                    _execute(conn, "CREATE INDEX IF NOT EXISTS idx_crm_dedupe "
                                   "ON crm_contacts(customer_id, phone_hash)")
                else:
                    log.info("🗄️  v11 migration: another worker holds the "
                             "migration lock — skipping (no blocking wait).")
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
            # v16g5 FIX R5-L1: bounded, but now RESUMABLE. The old query had
            # no cursor, so with >5,000 legacy rows the same first page was
            # re-read on every boot forever and the rows past it were never
            # reached. ORDER BY id + a persisted high-water mark walks the
            # whole table across successive boots.
            _mark = brain_cache.get("migrate:v11:backfill_after") or 0
            try:
                _mark = int(_mark)
            except (TypeError, ValueError):
                _mark = 0
            # v16g6 FIX R6-H7: serialise the scan itself. This is a fresh
            # transaction, so the DDL lock above is long gone.
            _bf_lock_ok = True
            if isinstance(_db_pool, PostgreSQLPool):
                _c2 = _execute(conn,
                    "SELECT pg_try_advisory_xact_lock(427012) AS got")
                _r2 = _c2.fetchone()
                _bf_lock_ok = bool(_r2["got"] if not isinstance(_r2, tuple)
                                   else _r2[0])
            if _bf_lock_ok:
                cur = _execute(conn,
                    "SELECT id, customer_id, enc_phone FROM crm_contacts "
                    "WHERE (phone_hash='' OR phone_hash IS NULL) AND id > ? "
                    "ORDER BY id LIMIT 5000", (_mark,))
                rows = cur.fetchall()
            else:
                rows = []
                log.info("🗄️  v11 backfill: another worker holds the scan "
                         "lock — skipping this boot (v16g6 FIX R6-H7).")
        # v16g4 FIX P4: the backfill borrowed a pooled connection PER ROW —
        # up to 5,000 getconn/commit/putconn cycles every boot. Decrypt and
        # hash first (per-row fault-isolated), then apply every update on ONE
        # connection in ONE transaction.
        updates = []
        # v16g6 FIX R6-H6: classify every skip. A TRANSIENT skip (key missing
        # or wrong → "[ENCRYPTED]" / disabled-vault ciphertext passthrough)
        # must NOT advance the mark — one boot with a lost ENCRYPTION_KEY
        # used to move it past a whole page, stranding those rows behind it
        # FOREVER once the key came back: phone_hash='' → invisible to
        # dedupe, follow-ups and erasure. Only written rows and permanent
        # junk (too few digits under a HEALTHY decrypt) may advance it.
        _safe_ids = set()
        for r in rows:
            try:
                phone = pii_vault.decrypt(r["enc_phone"])
                # v16g2 FIX L13: with the vault disabled, decrypt() passes
                # CIPHERTEXT through unchanged — hashing that poisons dedupe.
                if (phone == "[ENCRYPTED]"
                        or (not pii_vault.enabled and len(phone or "") > 20)):
                    continue                      # transient — retry next boot
                if len(re.sub(r"\D", "", phone or "")) < 7:
                    _safe_ids.add(r["id"])        # permanent junk — skip forever
                    continue
                updates.append((_crm_phone_hash(r["customer_id"], phone), r["id"]))
                _safe_ids.add(r["id"])
            except Exception:
                continue                          # unknown — treat as transient
        if updates:
            with _db_pool.get() as conn:
                for row_hash, row_id in updates:
                    _execute(conn, "UPDATE crm_contacts SET phone_hash=? WHERE id=?",
                             (row_hash, row_id))
        if rows:
            # v16g5 FIX R5-L1: report what was actually WRITTEN, not what was
            # scanned — the old line claimed a backfill even when every row
            # was skipped by the L13 guard. Advance the high-water mark so the
            # next boot resumes past this page instead of re-reading it.
            # v16g6 FIX R6-H6: advance only across the longest PREFIX of this
            # page whose rows were written or are permanently unfixable — the
            # first transient row is a barrier the next boot resumes from.
            # (Without Redis the mark is per-process; re-scanning is now
            # merely redundant work, never data loss.)
            try:
                _last = _mark
                for r in rows:
                    if r["id"] in _safe_ids:
                        _last = r["id"]
                    else:
                        break
                if _last != _mark:
                    brain_cache.set("migrate:v11:backfill_after", int(_last),
                                    ttl=30 * 86400)
            except Exception:
                pass
            log.info(f"🗄️  v11 migration: scanned {len(rows)} contacts, "
                     f"backfilled phone_hash for {len(updates)}")
    except Exception as exc:
        log.warning(f"⚠️  v11 backfill skipped: {exc}")


_COL_MEMO: Dict[Tuple[str, str], bool] = {}   # v16g4 FIX P1


def _column_exists(conn, table: str, column: str) -> bool:
    """v13: check a column BEFORE ALTER so Postgres never poisons the transaction.
    On Postgres a failed ALTER inside a txn aborts it (`current transaction is
    aborted`) and every following statement fails too — the old `try/except pass`
    does NOT save you there. SQLite path uses PRAGMA table_info.
    v16g4 FIX P1: POSITIVE results are memoized — crm_add_contact ran this
    catalog query on EVERY inbound message for a column that has existed since
    the v16 migration. A column, once present, never un-exists at runtime;
    negative results are NOT cached so boot-time check-before-alter still sees
    its own ALTER land."""
    _k = (table, column)
    if _COL_MEMO.get(_k):
        return True
    if isinstance(_db_pool, PostgreSQLPool):
        cur = _execute(conn,
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name=? AND column_name=? "
            "AND table_schema = current_schema()", (table, column))  # v15 FIX 24
        _found = cur.fetchone() is not None
    else:
        # v16g5 FIX R5-M8: PRAGMA cannot take a bound parameter, so the table
        # name is interpolated — but it is now whitelisted against the
        # identifier grammar first. Every current call site passes a literal;
        # this makes sure the day one doesn't, it raises instead of executing
        # attacker-shaped SQL in the one place this file interpolates.
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", table or ""):
            raise ValueError(f"unsafe table identifier: {table!r}")
        cur = _execute(conn, f"PRAGMA table_info({table})")
        _found = any((r[1] if not isinstance(r, dict) else r.get("name")) == column
                     for r in cur.fetchall())
    if _found:
        _COL_MEMO[_k] = True   # v16g4 FIX P1
    return _found


def _migrate_v12() -> None:
    """v13 TRUE MULTI-TENANT — per-clinic WhatsApp/Instagram credentials.
    Postgres-safe (check-before-alter), idempotent on every boot.

    New columns on customer_brains:
      wa_phone_number_id  → the Meta business line THIS clinic owns (routing key)
      wa_token_enc        → AES-256-GCM encrypted per-clinic WhatsApp token
      ig_token_enc        → AES-256-GCM encrypted per-clinic Instagram token
      channel_status      → 'ok' | 'needs_reauth'  (token-death self-heal flag)

    Plus a UNIQUE index on wa_phone_number_id so two clinics can NEVER share a
    business number — the DB itself blocks the ambiguous-routing footgun.
    """
    cols = {
        "wa_phone_number_id": "TEXT DEFAULT ''",
        "wa_token_enc":       "TEXT DEFAULT ''",
        "ig_token_enc":       "TEXT DEFAULT ''",
        "channel_status":     "TEXT DEFAULT 'ok'",
    }
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    if is_pg:
        # advisory lock → exactly one worker runs the DDL when many boot at once
        try:
            with _db_pool.get() as conn:
                _execute(conn, "SELECT pg_advisory_lock(427012)")
                try:
                    for col, typ in cols.items():
                        if not _column_exists(conn, "customer_brains", col):
                            _execute(conn,
                                f"ALTER TABLE customer_brains ADD COLUMN {col} {typ}")
                            log.info(f"🗄️  v13 migration: added {col}")
                finally:
                    _execute(conn, "SELECT pg_advisory_unlock(427012)")
        except Exception as exc:
            log.warning(f"⚠️  v13 migration (pg cols) issue: {exc}")
    else:
        for col, typ in cols.items():
            try:
                with _db_pool.get() as conn:
                    if not _column_exists(conn, "customer_brains", col):
                        _execute(conn,
                            f"ALTER TABLE customer_brains ADD COLUMN {col} {typ}")
                        log.info(f"🗄️  v13 migration: added {col}")
            except Exception:
                pass  # column already exists

    # Routing indexes + 🔴 UNIQUENESS. Each in its own connection so one failure
    # (e.g. a pre-existing duplicate blocking the unique index) can't abort the
    # others. If the unique index can't be built because real duplicates exist,
    # we log LOUD instead of silently shipping ambiguous routing.
    stmts = [
        ("idx_brain_wa_pid",
         "CREATE INDEX IF NOT EXISTS idx_brain_wa_pid "
         "ON customer_brains(wa_phone_number_id)"),
        ("idx_brain_ig_id2",
         "CREATE INDEX IF NOT EXISTS idx_brain_ig_id2 "
         "ON customer_brains(instagram_id)"),
        ("uq_brain_wa_pid",
         "CREATE UNIQUE INDEX IF NOT EXISTS uq_brain_wa_pid "
         "ON customer_brains(wa_phone_number_id) "
         "WHERE wa_phone_number_id <> ''"),
    ]
    for name, stmt in stmts:
        try:
            with _db_pool.get() as conn:
                _execute(conn, stmt)
        except Exception as exc:
            if name == "uq_brain_wa_pid":
                log.critical(
                    "🛑 v13: could NOT create the unique phone_number_id index "
                    f"({exc}). Two active clinics likely share a wa_phone_number_id "
                    "— inbound routing is ambiguous until you fix the duplicate. "
                    "Run: SELECT wa_phone_number_id, COUNT(*) FROM customer_brains "
                    "WHERE wa_phone_number_id<>'' GROUP BY 1 HAVING COUNT(*)>1;")
            else:
                log.warning(f"⚠️  v13 index skip [{name}]: {exc}")


def _migrate_v14g3() -> None:
    """v14 Gen-3 migrations — idempotent, safe on every boot.

    BUG 10: a UNIQUE index on (customer_id, phone_hash) makes CRM dedupe
    race-proof — a concurrent second insert of the same lead fails at the DB and
    crm_add_contact returns the existing row instead of creating a duplicate.
    Best-effort: if pre-existing duplicate phone_hash rows block the unique index,
    we log and keep the non-unique idx_crm_dedupe (lookups still work, the SELECT
    -first dedupe still applies, and the messaging path is already serialised).

    BUG 16: the whatsapp_phone index ships in the Postgres schema but was missing
    on SQLite — add it so the legacy-id lookup isn't a table scan there."""
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    uq = ("CREATE UNIQUE INDEX IF NOT EXISTS uq_crm_dedupe "
          "ON crm_contacts(customer_id, phone_hash) WHERE phone_hash <> ''")
    try:
        with _db_pool.get() as conn:
            if is_pg:
                _execute(conn, "SELECT pg_advisory_lock(427014)")
                try:
                    _execute(conn, uq)
                finally:
                    _execute(conn, "SELECT pg_advisory_unlock(427014)")
            else:
                _execute(conn, uq)
        log.info("🗄️  v14g3 migration: unique CRM dedupe index ensured.")
    except Exception as exc:
        log.warning("⚠️  v14g3: unique CRM index not built (likely existing "
                    f"duplicate phone_hash rows) — dedupe stays best-effort: {exc}")

    if not is_pg:
        try:
            with _db_pool.get() as conn:
                _execute(conn, "CREATE INDEX IF NOT EXISTS idx_brain_phone "
                               "ON customer_brains(whatsapp_phone)")
        except Exception:
            pass


def _migrate_v14g4() -> None:
    """v14 Gen-4 migrations — idempotent, safe on every boot, fully additive.

    Creates the `bookings` table (appointment engine) and adds
    crm_contacts.followed_up_at (cold-lead follow-up marker). Nothing here
    touches existing rows or behaviour — and every Gen-4 feature is flag-gated
    OFF by default, so a fresh boot of Gen-4 behaves EXACTLY like Gen-3 until you
    explicitly enable a feature."""
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    pk = "BIGSERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    create_bookings = f"""
        CREATE TABLE IF NOT EXISTS bookings (
            id             {pk},
            customer_id    TEXT NOT NULL,
            phone_hash     TEXT NOT NULL,
            enc_phone      TEXT DEFAULT '',
            enc_name       TEXT DEFAULT '',
            slot_start     TEXT NOT NULL,
            slot_end       TEXT NOT NULL,
            status         TEXT DEFAULT 'booked',
            reminders_sent TEXT DEFAULT '',
            source         TEXT DEFAULT 'whatsapp',
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customer_brains(customer_id) ON DELETE CASCADE
        )"""
    try:
        with _db_pool.get() as conn:
            _execute(conn, create_bookings)
            _execute(conn, "CREATE INDEX IF NOT EXISTS idx_book_slot "
                           "ON bookings(customer_id, status, slot_start)")
            _execute(conn, "CREATE INDEX IF NOT EXISTS idx_book_phone "
                           "ON bookings(customer_id, phone_hash, status)")
            # a slot can be held by at most one active booking per clinic
            _execute(conn, "CREATE UNIQUE INDEX IF NOT EXISTS uq_book_slot "
                           "ON bookings(customer_id, slot_start) WHERE status='booked'")
        log.info("🗄️  v14g4 migration: bookings table + indexes ensured.")
    except Exception as exc:
        log.warning(f"⚠️  v14g4: bookings migration issue: {exc}")

    try:
        with _db_pool.get() as conn:
            if not _column_exists(conn, "crm_contacts", "followed_up_at"):
                _execute(conn, "ALTER TABLE crm_contacts "
                               "ADD COLUMN followed_up_at TEXT DEFAULT ''")
        log.info("🗄️  v14g4 migration: crm_contacts.followed_up_at ensured.")
    except Exception as exc:
        log.warning(f"⚠️  v14g4: followed_up_at migration issue: {exc}")


def _migrate_v14g5() -> None:
    """v14 Gen-5 migrations — idempotent, additive. Adds chat_sessions.subject_hash
    (FIX 3 — lets DPDP erasure resolve a subject's sessions from the DB instead of a
    1-hour cache key) plus its lookup index. Safe on every boot."""
    try:
        with _db_pool.get() as conn:
            if not _column_exists(conn, "chat_sessions", "subject_hash"):
                _execute(conn, "ALTER TABLE chat_sessions ADD COLUMN subject_hash TEXT DEFAULT ''")
                log.info("🗄️  v14g5 migration: chat_sessions.subject_hash added.")
    except Exception as exc:
        log.warning(f"⚠️  v14g5: subject_hash migration issue: {exc}")
    try:
        with _db_pool.get() as conn:
            _execute(conn, "CREATE INDEX IF NOT EXISTS idx_sess_subject "
                           "ON chat_sessions(customer_id, subject_hash)")
    except Exception:
        pass


def _migrate_v15g3() -> None:
    """v15 Gen-3 migration — idempotent, additive. Adds outbox.next_attempt_at
    (FIX 1) so failed rows retry on an EXPONENTIAL schedule instead of burning
    all 5 attempts in ~80 seconds of janitor ticks. TEXT ISO-8601 UTC, same
    lexicographically-sortable format every timestamp in this engine uses.
    Empty string = eligible immediately (all pre-existing rows keep working)."""
    try:
        with _db_pool.get() as conn:
            if not _column_exists(conn, "outbox", "next_attempt_at"):
                _execute(conn, "ALTER TABLE outbox "
                               "ADD COLUMN next_attempt_at TEXT DEFAULT ''")
                log.info("🗄️  v15g3 migration: outbox.next_attempt_at added.")
    except Exception as exc:
        log.warning(f"⚠️  v15g3: next_attempt_at migration issue: {exc}")


def _migrate_v15g4() -> None:
    """v15 Gen-4 migration — idempotent, additive (indexes only, no schema
    change). v15g4 FIX D4: the hourly retention purges filter on
    chat_messages.timestamp and webhook_log.processed_at, neither of which had
    a usable index — full-table scans every hour at scale. v15g4 FIX D5:
    idx_wh_customer existed only in the Postgres fresh-install schema, never
    on SQLite. All CREATE INDEX IF NOT EXISTS → safe on every boot, both DBs."""
    stmts = (
        "CREATE INDEX IF NOT EXISTS idx_msg_ts        ON chat_messages(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_wh_processed  ON webhook_log(processed_at)",
        "CREATE INDEX IF NOT EXISTS idx_wh_customer   ON webhook_log(customer_id, processed_at)",
    )
    try:
        with _db_pool.get() as conn:
            for s in stmts:
                try:
                    _execute(conn, s)
                except Exception as exc:
                    log.warning(f"⚠️  v15g4 index skipped ({s.split()[5]}): {exc}")
        log.info("🗄️  v15g4 migration: purge-path indexes ensured.")
    except Exception as exc:
        log.warning(f"⚠️  v15g4 migration issue: {exc}")


def _migrate_v16() -> None:
    """v16 U1 migration — idempotent, additive. WhatsApp usernames/BSUID:
    crm_contacts.wa_user_id stores Meta's business-scoped user ID alongside
    the phone identity, mirroring the Contact-Book mapping locally. Indexed
    per clinic for the remap/lookup paths."""
    try:
        with _db_pool.get() as conn:
            if not _column_exists(conn, "crm_contacts", "wa_user_id"):
                _execute(conn, "ALTER TABLE crm_contacts "
                               "ADD COLUMN wa_user_id TEXT DEFAULT ''")
                log.info("🗄️  v16 migration: crm_contacts.wa_user_id added.")
            try:
                _execute(conn, "CREATE INDEX IF NOT EXISTS idx_crm_userid "
                               "ON crm_contacts(customer_id, wa_user_id)")
            except Exception as exc:
                log.warning(f"⚠️  v16 idx_crm_userid skipped: {exc}")
    except Exception as exc:
        log.warning(f"⚠️  v16 migration issue: {exc}")


def _migrate_v16g5() -> None:
    """v16g5 FIX R5-H4: durable opt-out suppression table."""
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    ddl = ("CREATE TABLE IF NOT EXISTS opt_outs ("
           "id BIGSERIAL PRIMARY KEY, customer_id TEXT NOT NULL, "
           "subject_hash TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
           if is_pg else
           "CREATE TABLE IF NOT EXISTS opt_outs ("
           "id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT NOT NULL, "
           "subject_hash TEXT NOT NULL, created_at TEXT NOT NULL)")
    for stmt in (ddl,
                 "CREATE UNIQUE INDEX IF NOT EXISTS uq_optout "
                 "ON opt_outs(customer_id, subject_hash)"):
        try:
            with _db_pool.get() as conn:
                _execute(conn, stmt)
        except Exception as exc:
            log.warning(f"⚠️  v16g5 opt_outs migration issue: {exc}")


def _migrate_v16g4() -> None:
    """v16g4 FIX M10: admin_users.tenant_id — admin JWTs carried role but no
    tenant claim, so every 'admin' token was fleet-wide; the v16 IDOR fix only
    forced them to NAME a customer_id, not to name their OWN. '' keeps legacy
    rows fleet-wide (existing behaviour); a tenant-scoped admin can only touch
    their tenant. Check-before-alter (Postgres txn-poison safe)."""
    try:
        with _db_pool.get() as conn:
            if not _column_exists(conn, "admin_users", "tenant_id"):
                _execute(conn, "ALTER TABLE admin_users "
                               "ADD COLUMN tenant_id TEXT NOT NULL DEFAULT ''")
                log.info("🗄️  v16g4 migration: added admin_users.tenant_id")
    except Exception as exc:
        log.warning(f"⚠️  v16g4 migration issue: {exc}")


def _report_wa_pid_duplicates() -> None:
    """v14 (drawback #4): make duplicate-tenant routing self-diagnosing. If two
    active clinics share a wa_phone_number_id, inbound routing is ambiguous and
    the unique index can't build. Instead of leaving you to guess, log EXACTLY
    which number is shared by which clinics so cleanup is a 30-second fix."""
    try:
        with _db_pool.get(read_only=True) as conn:
            if not _column_exists(conn, "customer_brains", "wa_phone_number_id"):
                return
            cur = _execute(conn,
                "SELECT wa_phone_number_id AS pid, COUNT(*) AS c "
                "FROM customer_brains WHERE wa_phone_number_id <> '' "
                "AND is_active=? GROUP BY wa_phone_number_id "
                "HAVING COUNT(*) > 1", (_db_true(),))
            dups = cur.fetchall()
            for d in dups:
                pid = d["pid"]
                cur2 = _execute(conn,
                    "SELECT customer_id FROM customer_brains "
                    "WHERE wa_phone_number_id=? AND is_active=?",
                    (pid, _db_true()))
                owners = [r["customer_id"] for r in cur2.fetchall()]
                log.critical(f"🛑 DUPLICATE wa_phone_number_id={pid} shared by "
                             f"clinics {owners}. Routing is ambiguous — keep ONE, "
                             f"clear it on the others via "
                             f"POST /admin/customer/<id>/channel.")
        if not dups:
            log.info("✅ Tenant routing check: no duplicate WhatsApp numbers.")
    except Exception as exc:
        log.warning(f"⚠️  duplicate-tenant check skipped: {exc}")


# ─────────────────────────────────────────────────────────────────────────────


def _is_unique_violation(exc: Exception) -> bool:
    """v16g4 FIX M11: four sites classified 'duplicate row' by sniffing the
    exception STRING for "unique"/"constraint"/"duplicate" — so a CHECK or
    FK/NOT NULL violation on Postgres ("violates check constraint …") was
    mis-read as a duplicate: booking_create answered 'slot just taken' to a
    data bug, create_admin_user answered 409 'Username already exists' to a
    schema problem. Use the drivers' real signals: pgcode 23505 (psycopg2)
    and sqlite3.IntegrityError whose message names UNIQUE."""
    if POSTGRES_AVAILABLE:
        try:
            if isinstance(exc, psycopg2.Error):
                return getattr(exc, "pgcode", None) == "23505"
        except Exception:
            pass
    if isinstance(exc, sqlite3.IntegrityError):
        return "unique" in str(exc).lower()
    return False


def _execute(conn, sql: str, params: tuple = ()) -> Any:
    """Execute SQL — translates ? → %s for psycopg2 automatically.
    v15g4 FIX C4: the translation is a blind string replace — a future query
    containing a literal '%' (LIKE) or '?' inside a string would silently
    corrupt on Postgres. No current query does (audited); this guard makes
    sure the day one appears, it screams instead of corrupting."""
    is_pg = POSTGRES_AVAILABLE and isinstance(conn, psycopg2.extensions.connection)
    if is_pg:
        # v16g4 FIX HF1 (hotfix, 20-Jul): a literal '%' anywhere in the SQL
        # TEXT — including inside a SQL comment — was passed straight to
        # psycopg2's paramstyle parser after ?→%s translation, which then
        # expected MORE parameters than given: "IndexError: tuple index out
        # of range", a 500 on the live Tally webhook. The v15g4 C4 guard saw
        # it and LOGGED, but still executed the doomed statement. Now literal
        # % is escaped to %% FIRST (psycopg2 renders %% as a literal %), THEN
        # ? becomes %s — the whole bug class is gone, so the guard scream is
        # retired. House rule stands: parameters use ?, never raw %s.
        # v16g5 FIX R5-M7: HF1 fixed the `%` half of the C4 landmine and
        # RETIRED the guard — but `?`→`%s` is still a blind whole-string
        # replace, so a `?` inside a string literal or an identifier now
        # corrupts silently with nothing watching. Re-arm the scream for the
        # half that is still blind: count the `?` we are about to translate
        # and refuse to execute when it doesn't match the parameter count.
        # Count on the ORIGINAL sql: after %-escaping, a pattern like
        # LIKE '%stat%' would alias into a false "%s" hit.
        _holes = sql.count("?")
        _translated = sql.replace("%", "%%").replace("?", "%s")
        if _holes != len(params or ()):
            raise ValueError(
                f"SQL placeholder mismatch: {_holes} '?' translated but "
                f"{len(params or ())} parameter(s) supplied. A literal '?' "
                f"inside a string/identifier corrupts the ?→%s translation "
                f"(v16g5 FIX R5-M7). Offending SQL: {sql[:200]}")
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(_translated, params)
        if cur.description is None:
            # v16g4 FIX L15: INSERT/UPDATE/DDL produce no result set, yet the
            # cursor was returned open and lived until GC — loop-heavy paths
            # (erasure hash loop, outbox claim, migration backfill) piled up
            # dozens per connection. No caller can fetch from a result-less
            # cursor, and .rowcount stays readable after close (psycopg2), so
            # closing here is free. SELECT cursors must stay open for the
            # caller's fetch and are released with the connection.
            cur.close()
        return cur
    return conn.execute(sql, params)


def _db_true():
    """
    v12: portable truthy literal for WHERE clauses.
    PostgreSQL stores booleans natively (True); SQLite uses integer 1.
    Checks the live pool instance (not just driver availability) so it stays
    correct when psycopg2 is installed but DATABASE_URL is unset (SQLite mode).
    """
    return True if isinstance(_db_pool, PostgreSQLPool) else 1


# ─────────────────────────────────────────────────────────────────────────────
# 📋  SOC 2 AUDIT TRAIL  (v8 FIX #6)
# ─────────────────────────────────────────────────────────────────────────────
_AUDIT_DETAIL_MAX = 4000     # v16g5 FIX R5-L8


def audit(actor_id: str, action: str, resource: str,
          detail: Optional[Dict] = None, ip: Optional[str] = None) -> None:
    """Write an immutable audit record — async so it never blocks the request path.
    v14g3 BUG 14: was gated on ENABLE_ANALYTICS, so disabling metrics to cut DB
    load ALSO silently killed the SOC2/GDPR audit log. Now it has its own switch."""
    if not cfg.ENABLE_AUDIT:
        return

    def _write():
        try:
            # v16g5 FIX R5-L8: detail was json.dumps'd with NO size cap, so a
            # caller passing a large dict wrote an unbounded row into the one
            # table that must stay cheap to query.
            detail_str = json.dumps(detail or {})
            if len(detail_str) > _AUDIT_DETAIL_MAX:
                detail_str = json.dumps({
                    "_truncated": True,
                    "_original_bytes": len(detail_str),
                    "_head": detail_str[:_AUDIT_DETAIL_MAX]})
            with _db_pool.get() as conn:
                _execute(conn,
                    "INSERT INTO audit_log (ts, actor_id, action, resource, detail, ip, region) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (_now(), actor_id, action, resource, detail_str, ip, cfg.REGION))
        except Exception as exc:
            log.warning(f"⚠️  Audit write failed: {exc}")

    # v16g6 FIX R6-M11: compliance writes went through the SAME
    # shed-on-saturation queue as analytics — under load the audit trail was
    # preferentially the first thing dropped (counted in bg.shed,
    # indistinguishable from a dropped metric). Admin actions are rare:
    # write synchronously; the bounded pool remains only as the fallback so
    # a slow DB cannot stall a webhook path that audits.
    try:
        _write()
    except Exception:
        submit_bg(_write)   # v11 #11: bounded pool


_latebind.register("_db_pool", __name__)  # GEN-5 SPLIT


def _publish_db_pool(pool) -> None:
    """GEN-5 SPLIT: push the live pool into every registered consumer module.
    Called once by startup() right after the pool is constructed."""
    _latebind.publish("_db_pool", pool)
