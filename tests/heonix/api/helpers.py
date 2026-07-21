"""HEONIX GEN-5 · module `heonix.api.helpers`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 8657-8711, 8739-8807).
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

from heonix.classify import (_kw_hit)
from heonix.db.core import (_db_true, _execute)
from heonix.i18n import (_norm_text)
from heonix.logsetup import (log)
from heonix.security.crypto import (_normalize_msisdn)
from heonix import _latebind  # GEN-5 SPLIT
_db_pool: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.db.core at startup
_latebind.register('_db_pool', __name__)


def _int_arg(name: str, default: int, lo: int, hi: int) -> int:
    """v15g4 FIX C3: ?page=abc used to raise ValueError → 500. Garbage or
    out-of-range values now safely resolve to a clamped default."""
    try:
        v = int(request.args.get(name, default))
    except (TypeError, ValueError):
        v = default
    return max(lo, min(hi, v))


def extract_field(fields: List, index: int, default: str = "") -> str:
    try:
        val = fields[index].get("value", default)
        return str(val).strip() if val else default
    except (IndexError, AttributeError):
        return default


def extract_by_label(fields: List, labels: Tuple[str, ...], idx_fallback: int,
                     default: str = "", require_digits: int = 0) -> str:
    """v14g5 FIX 17: Tally's field ORDER is not stable — reordering questions or
    inserting one silently shifts every positional index, so (e.g.) a phone number
    lands in the name column and a clinic onboards with garbage data. Prefer
    matching the field's own label (case-insensitive substring of any candidate);
    fall back to the positional index only when no label matches.
    v15g4 FIX B6: require_digits=N → a label-matched value must contain at
    least N digits to be accepted. A checkbox labelled 'Do you use WhatsApp?'
    matched the 'whatsapp' candidate and its value — 'Yes' — became the
    business phone (then the welcome-send target AND the identity seed).
    Non-phone-shaped values are now skipped and scanning continues."""
    try:
        # v15g2 FIX M5: (1) whole-word/phrase label matching via _kw_hit — the
        # old substring test let a field labelled 'Instagram userNAME' steal the
        # customer_name slot, onboarding a clinic as '@handle'; (2) candidates
        # are tried in PRIORITY order (outer loop), so 'whatsapp' beats a vaguer
        # later candidate no matter where the fields sit in the form.
        for kw in labels:
            # v16g2 FIX L10: whole-word matching missed simple plurals — the
            # candidate "note" never hit a field labelled "Notes", silently
            # falling back to the fragile positional index (breaks the moment
            # the form is reordered). Try the naive plural too.
            _kws = (kw, kw + "s") if not kw.endswith("s") else (kw,)
            for f in fields:
                lbl = _norm_text(str(f.get("label", "")))
                if lbl and any(_kw_hit(lbl, _k) for _k in _kws):
                    val = str(f.get("value", "") or "").strip()
                    if not val:
                        continue
                    if require_digits and \
                       len(re.sub(r"\D", "", val)) < require_digits:   # v15g4 FIX B6
                        continue
                    return val
    except Exception:
        pass
    return extract_field(fields, idx_fallback, default)




def make_customer_id(name: str, whatsapp_phone: str = "",
                     owner_phone: str = "") -> str:
    """v14 BUG 41 / v14g3 BUG 11 — stable, collision-safe identity.

    The id is derived from the WhatsApp number (which does NOT change when the
    display name is edited), normalised country-aware via _normalize_msisdn so:
      • '+91 98765 43210', '9876543210', '+91-98765-43210' → ONE id, and
      • a +1 number and a +91 number that share the last 10 digits → TWO ids.
    The old 'last-10-digits only' rule could collide those two and let one
    clinic's Tally re-submit silently OVERWRITE another clinic's brain via the
    UPSERT. Name is only a last-resort fallback when no usable phone is given."""
    msisdn = _normalize_msisdn(whatsapp_phone or owner_phone or "")
    if msisdn:
        return "HX_WA_" + msisdn                # stable + country-safe
    # Fallback: no phone given → legacy name-based id (best effort, unavoidable).
    # v14g5 FIX 14: restrict to ASCII [A-Z0-9_] so the id always satisfies the
    # /chat id validator (Unicode letters pass .isalnum() and used to leak in). If
    # nothing usable survives, hash the name so two names can't collide on "HX_".
    safe = "".join(c if (c.isascii() and c.isalnum()) else "_" for c in (name or "").upper())
    safe = safe.strip("_")
    if safe:
        return f"HX_{safe[:60]}"
    if name:
        return "HX_" + hashlib.sha256(name.encode("utf-8")).hexdigest()[:16].upper()
    return "HX_" + uuid.uuid4().hex[:16].upper()


def find_legacy_brain_id_by_phone(whatsapp_phone: str) -> Optional[str]:
    """v14 BUG 41 transition helper / v14g3 BUG 12 fix.

    If a business was created on a PRE-v14 (name-based) id and now re-submits
    with the same WhatsApp number, find that existing brain so we keep its id
    instead of minting a parallel phone-based row.

    v14g3: the old version did an EXACT string match on whatsapp_phone only, so
    the same number stored as '+91 98765 43210' but re-submitted as '9876543210'
    would NOT match → a new id was minted → the very orphaning BUG 41 was meant
    to kill. We now (1) try the fast exact match (indexed), then (2) fall back to
    a bounded scan that compares the COUNTRY-AWARE NORMALISED form."""
    wp = (whatsapp_phone or "").strip()
    if not wp:
        return None
    target = _normalize_msisdn(wp)
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT customer_id FROM customer_brains "
                "WHERE whatsapp_phone=? AND is_active=? LIMIT 1",
                (wp, _db_true()))
            row = cur.fetchone()
            if row:
                return row["customer_id"]
            if not target:
                return None
            # (2) normalised scan — bounded; runs only on onboarding, never on the
            # hot message path, and tenant counts are small.
            cur = _execute(conn,
                "SELECT customer_id, whatsapp_phone FROM customer_brains "
                "WHERE whatsapp_phone <> '' AND is_active=? LIMIT 5000",
                (_db_true(),))
            for r in cur.fetchall():
                if _normalize_msisdn(r["whatsapp_phone"]) == target:
                    return r["customer_id"]
        return None
    except Exception as exc:
        log.warning(f"⚠️  legacy-id lookup failed: {exc}")
        return None
