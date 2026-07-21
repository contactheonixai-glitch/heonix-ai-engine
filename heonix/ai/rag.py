"""HEONIX GEN-5 · module `heonix.ai.rag`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 5314-5482).
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
from heonix.concurrency import (_call_with_timeout, submit_bg)
from heonix.config import (cfg)
from heonix.logsetup import (log)
from heonix.resilience import (_qdrant_breaker)
from heonix.security.crypto import (pii_vault)
from heonix.utils import (_now)
from heonix import _latebind  # GEN-5 SPLIT


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
            try:
                client.create_collection(
                    collection_name=cfg.QDRANT_COLLECTION,
                    vectors_config=qmodels.VectorParams(
                        size=cfg.EMBED_DIMS, distance=qmodels.Distance.COSINE))
                log.info(f"🧬 Qdrant collection created: {cfg.QDRANT_COLLECTION}")
            except Exception as _ce:
                # v16g2 FIX M13: two workers boot, both miss get_collection,
                # the loser's "already exists" used to bubble to the OUTER
                # except — that worker then logged "Qdrant unreachable" and ran
                # MEMORY-FREE for its whole lifetime. Tolerate the boot race.
                if "exist" in str(_ce).lower():
                    log.info("🧬 Qdrant collection already exists (boot race) — OK.")
                else:
                    raise
        _qdrant_client = client
        _rag_ready     = True
        _latebind.publish("_rag_ready", True)  # GEN-5 SPLIT: health/ready/startup read this
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
    vec = list(res["embedding"])
    # v14g5 FIX 18: PAD (not just truncate) so a short embedding can't produce a
    # wrong-size vector that silently fails the Qdrant upsert / corrupts search.
    if len(vec) < cfg.EMBED_DIMS:
        vec = vec + [0.0] * (cfg.EMBED_DIMS - len(vec))
    return vec[:cfg.EMBED_DIMS]


# v12 #1: replies we must NEVER write into long-term memory (they'd poison it).
_FALLBACK_MARKERS = (
    "temporarily unavailable", "couldn't hear that", "could you please type",
    "try again", "something went wrong",
)


def _is_low_quality_reply(reply: str) -> bool:
    if not reply or len(reply.strip()) < 2:
        return True
    low = reply.lower()
    return any(m in low for m in _FALLBACK_MARKERS)


def rag_store(customer_id: str, uid: str, user_text: str, reply: str) -> None:
    """Fire-and-forget — memory writes never slow down or break a reply.
    v12 #1: refuses to memorise a fallback/error reply, so a transient AI
    outage can't poison this user's long-term memory with apology text."""
    if not _rag_ready or len(user_text.split()) < 4:
        return
    if _is_low_quality_reply(reply):
        analytics.inc("rag.store.skipped_lowquality")
        return

    def _w():
        def _impl():
            vec = _embed(user_text, is_query=False)
            enc = pii_vault.encrypt(
                f"User said: {user_text[:500]} | Assistant replied: {reply[:300]}")
            _qdrant_client.upsert(
                collection_name=cfg.QDRANT_COLLECTION,
                points=[qmodels.PointStruct(
                    id=str(uuid.uuid4()), vector=vec,
                    payload={"customer_id": customer_id, "uid": uid,
                             "enc": enc, "ts": _now()})])
        try:
            # v12 #9/#23: bounded by the Qdrant breaker + hard timeout so a hung
            # embedder or vector DB degrades the write silently instead of
            # pinning a worker thread.
            _qdrant_breaker.call(_call_with_timeout, _impl, cfg.RAG_TIMEOUT_SECS)
            analytics.inc("rag.stored")
        except Exception as exc:
            log.warning(f"⚠️  RAG store degraded: {exc}")

    submit_bg(_w)   # v11 #11: bounded pool instead of a raw daemon thread


def _rag_retrieve_impl(customer_id: str, uid: str, query: str) -> str:
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
    return "\n".join(lines)


def rag_retrieve(customer_id: str, uid: str, query: str) -> str:
    """Returns a memory block ('' if none). Failures degrade silently.
    v12 #9/#23: embedding + vector search run inside the Qdrant breaker with a
    hard timeout — if the vector DB hangs, the reply still ships memory-free."""
    if not _rag_ready or len(query.split()) < 3:
        return ""
    try:
        result = _qdrant_breaker.call(
            _call_with_timeout, _rag_retrieve_impl, cfg.RAG_TIMEOUT_SECS,
            customer_id, uid, query)
        if result:
            analytics.inc("rag.hit")
        return result or ""
    except Exception as exc:
        log.warning(f"⚠️  RAG retrieve degraded: {exc}")
        return ""


def rag_forget(customer_id: str, uid: str) -> bool:
    """v14g4 (DPDP): delete every RAG memory point for ONE data subject (uid =
    'customer_id:phone'). Best-effort; never raises. Returns True if the delete
    call succeeded. Vectors store only AES-256-GCM-encrypted text, but erasure
    means erasure — so we remove the points entirely."""
    if not _rag_ready:
        return False
    try:
        flt = qmodels.Filter(must=[
            qmodels.FieldCondition(key="customer_id",
                                   match=qmodels.MatchValue(value=customer_id)),
            qmodels.FieldCondition(key="uid", match=qmodels.MatchValue(value=uid)),
        ])
        _qdrant_breaker.call(
            _call_with_timeout,
            lambda: _qdrant_client.delete(
                collection_name=cfg.QDRANT_COLLECTION,
                points_selector=qmodels.FilterSelector(filter=flt)),
            cfg.RAG_TIMEOUT_SECS)
        analytics.inc("rag.forgotten")
        return True
    except Exception as exc:
        log.warning(f"⚠️  rag_forget failed: {exc}")
        return False


_latebind.register("_rag_ready", __name__)  # GEN-5 SPLIT
