"""HEONIX GEN-5 · module `heonix.security.crypto`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 1249-1428, 6606-6644, 8714-8738).
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


class PIIVault:
    """
    AES-256-GCM authenticated encryption for PII fields.
    Each field gets a unique 96-bit nonce so identical values encrypt differently.
    Compliant: DPDP Act (India), HIPAA (USA), GDPR (EU).
    """

    def __init__(self, hex_key: str):
        if not CRYPTO_AVAILABLE:
            log.warning("⚠️  cryptography not installed — PII encryption disabled.")
            self._enabled = False
            return
        if not hex_key or len(hex_key) < 64:
            log.warning("⚠️  ENCRYPTION_KEY missing/short — PII encryption disabled. "
                        "Generate: python -c \"import secrets; print(secrets.token_hex(32))\"")
            self._enabled = False
            return
        if len(hex_key) > 64:
            # v15g4 FIX C9: a longer pasted key silently "worked" while only
            # its first 32 bytes were ever used — say so out loud.
            log.warning(f"⚠️  ENCRYPTION_KEY is {len(hex_key)} hex chars — only "
                        "the first 64 (32 bytes) are used for AES-256-GCM.")
        try:
            self._aesgcm = AESGCM(bytes.fromhex(hex_key[:64]))
        except ValueError:
            # v15 FIX 25: a non-hex character in ENCRYPTION_KEY used to raise an
            # unhandled ValueError DURING MODULE IMPORT — a confusing stack
            # trace instead of a clear message. Fail soft + loud, matching the
            # short-key path above.
            log.error("❌ ENCRYPTION_KEY is not valid hex — PII encryption "
                      "DISABLED. Regenerate: python -c \"import secrets; "
                      "print(secrets.token_hex(32))\"")
            self._enabled = False
            return
        self._enabled = True
        log.info("🔐 AES-256-GCM PII Vault ready.")

    @property
    def enabled(self) -> bool:
        return self._enabled

    # v16g5 FIX R5-C4: ciphertext is now VERSION-TAGGED. Before this, a value
    # written while the vault was disabled sat in enc_phone as raw plaintext
    # ("919876543210"); the day ENCRYPTION_KEY was set, decrypt() ran
    # b64decode on it — which SUCCEEDS (bare digits are valid base64
    # alphabet), produced garbage, failed the AESGCM tag, and returned
    # "[ENCRYPTED]". Those rows were unreadable forever, and they are exactly
    # the rows the reminder scanner, the follow-up scanner and DPDP erasure
    # need. A "v1:" prefix makes ciphertext self-identifying, so an untagged
    # value is recognised as legacy plaintext and returned as-is instead of
    # being destroyed. Legacy UNTAGGED ciphertext (written by a pre-R5 build
    # with the vault enabled) still decrypts via the fallback branch.
    _CT_PREFIX = "v1:"

    def encrypt(self, plaintext: str) -> str:
        if not self._enabled or not plaintext:
            return plaintext
        nonce = os.urandom(12)
        ct    = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return self._CT_PREFIX + base64.b64encode(nonce + ct).decode("ascii")

    def _open(self, blob: str) -> Optional[str]:
        """Attempt one AESGCM open. None = not our ciphertext."""
        try:
            raw = base64.b64decode(blob, validate=True)
        except Exception:
            return None
        if len(raw) < 29:            # 12-byte nonce + 16-byte tag + ≥1 byte
            return None
        try:
            return self._aesgcm.decrypt(raw[:12], raw[12:], None).decode("utf-8")
        except Exception:
            return None

    def decrypt(self, token: str) -> str:
        if not token:
            return token
        if not self._enabled:
            # v16g6 FIX R6-C2: with the vault OFF (lost/typo'd ENCRYPTION_KEY —
            # note _load fails SOFT), tagged ciphertext was returned VERBATIM.
            # "v1:AAAA…" is truthy and != "[ENCRYPTED]", so it sailed past
            # every downstream guard: brain_wa_creds sent it to Meta as a
            # Bearer token (401 → the whole fleet false-flagged needs_reauth,
            # blamed on token death instead of the real one-env-var cause) and
            # the reminder scanner handed it to Meta as a phone number. Never
            # give ciphertext to a caller as a value.
            if token.startswith(self._CT_PREFIX):
                log.error("❌ PII vault is DISABLED but tagged ciphertext was "
                          "read — ENCRYPTION_KEY is missing/invalid on this "
                          "deployment. Returning sentinel (v16g6 FIX R6-C2).")
                return "[ENCRYPTED]"
            return token
        # Fast path: tagged ciphertext written by this build.
        if token.startswith(self._CT_PREFIX):
            out = self._open(token[len(self._CT_PREFIX):])
            if out is not None:
                return out
            log.error("❌ PII decryption failed — key mismatch or corrupt data.")
            return "[ENCRYPTED]"
        # Untagged: could be legacy ciphertext OR legacy plaintext. Try to
        # open it; if it isn't ours, it was written before encryption was
        # enabled — hand back the plaintext rather than bricking the row.
        out = self._open(token)
        if out is not None:
            return out
        # Ciphertext-SHAPED but unopenable = a real key mismatch on a legacy
        # row. Keep the old sentinel so every `!= "[ENCRYPTED]"` guard in the
        # schedulers still fires (never leak a raw blob as a phone number).
        try:
            if len(base64.b64decode(token, validate=True)) >= 29:
                log.error("❌ PII decryption failed — key mismatch or corrupt data.")
                return "[ENCRYPTED]"
        except Exception:
            pass
        return token

    def mask(self, value: str) -> str:
        # v15 FIX 20 / v16g2 FIX L7 / v16g3 FIX R3-M4: tiered. L7 only moved
        # the cliff — an 8-char value still showed 6 of its 8 chars
        # ("AB***EFGH", 75%). ≤7 → full mask; 8-11 → first-1 + last-2 (≤37%
        # shown); ≥12 (E.164 phones) → the classic first-2 + last-4.
        if not value or len(value) <= 7:
            return "****"
        if len(value) <= 11:
            return value[:1] + "***" + value[-2:]
        return value[:2] + "***" + value[-4:]


pii_vault = PIIVault(cfg.ENCRYPTION_KEY)


# ─────────────────────────────────────────────────────────────────────────────
# 🔑  PASSWORD HASHING  (v8 fix: bcrypt replaces plaintext in admin table)
# ─────────────────────────────────────────────────────────────────────────────
_PBKDF2_ITERS = 240_000


def hash_password(plaintext: str) -> str:
    """bcrypt-hash a password. v14g5 FIX 21: if bcrypt is unavailable, fall back to
    SALTED PBKDF2-HMAC-SHA256 (was unsalted SHA-256 → instantly rainbow-tableable).
    v16g2 FIX L5 (documented limitation): bcrypt hashes only the FIRST 72 BYTES —
    characters beyond that never affect the hash. We log instead of pre-hashing,
    because pre-hashing now would invalidate any existing >72-byte password.
    Bytes, not chars: one Tamil character is 3 UTF-8 bytes."""
    if BCRYPT_AVAILABLE and len(plaintext.encode("utf-8")) > 72:   # v16g2 FIX L5
        log.warning("⚠️  password exceeds bcrypt's 72-byte limit — only the "
                    "first 72 bytes are significant.")
    if BCRYPT_AVAILABLE:
        return bcrypt_lib.hashpw(plaintext.encode("utf-8"), bcrypt_lib.gensalt(rounds=12)).decode("utf-8")
    salt = os.urandom(16)
    dk   = hashlib.pbkdf2_hmac("sha256", plaintext.encode("utf-8"), salt, _PBKDF2_ITERS)
    return f"pbkdf2${_PBKDF2_ITERS}${salt.hex()}${dk.hex()}"


# v15g4 FIX C2: dummy hash lazily built on the first unknown-username login so
# the miss path costs the same bcrypt work as a real check (no timing oracle).
_TIMING_PAD: Optional[str] = None


def verify_password(plaintext: str, stored_hash: str) -> bool:
    """v14g5 FIX 21: constant-time across bcrypt / salted-PBKDF2 / legacy sha256."""
    if not stored_hash:
        return False
    if stored_hash.startswith("$2"):
        if not BCRYPT_AVAILABLE:
            return False
        try:
            return bcrypt_lib.checkpw(plaintext.encode("utf-8"), stored_hash.encode("utf-8"))
        except Exception:
            return False
    if stored_hash.startswith("pbkdf2$"):
        try:
            _, iters, salt_hex, hash_hex = stored_hash.split("$", 3)
            dk = hashlib.pbkdf2_hmac("sha256", plaintext.encode("utf-8"),
                                     bytes.fromhex(salt_hex), int(iters))
            return hmac.compare_digest(dk.hex(), hash_hex)
        except Exception:
            return False
    # legacy unsalted sha256 hex (pre-v14g5) — still compared in constant time
    return hmac.compare_digest(hashlib.sha256(plaintext.encode("utf-8")).hexdigest(), stored_hash)


_BSUID_RE = re.compile(r"^[A-Za-z]{2}\.[A-Za-z0-9]{1,128}$")


def _is_bsuid(s: str) -> bool:
    """v16 U2: Meta's Business-Scoped User ID — the new identity layer that
    arrives when a WhatsApp user adopts a username and hides their number.
    Documented format: ISO-3166 alpha-2 country code + '.' + up to 128
    alphanumeric chars (e.g. IN.1A2B3C4D5E6F7G8H9I0J). Detection rule per
    Meta/BSP docs: two letters followed by a period."""
    return bool(_BSUID_RE.match((s or "").strip()))


def _crm_phone_hash(customer_id: str, phone: str) -> str:
    """v11 #3: deterministic dedupe handle. AES-GCM ciphertext changes every
    encryption (random nonce), so enc_phone can't be compared — this hash can.
    Scoped per customer so the same lead at two businesses stays two rows.
    v16 U2: a BSUID is hashed as the FULL exact string. The old digits-only
    normalisation would have stripped 'IN.' and truncated to the last 12
    digits — every username patient whose BSUID shared a digit-tail (or had
    few digits at all) would silently MERGE into one CRM row: wrong history,
    wrong bookings, wrong erasure. Meta's docs are explicit that a BSUID must
    be used exactly as-is."""
    p = (phone or "").strip()
    if _is_bsuid(p) or p.startswith("ig_"):
        # v16 U2 + v16g6 FIX R6-H5: an Instagram pseudo-address ("ig_<id>")
        # must hash as the FULL exact string, exactly like a BSUID. The
        # digits-only branch stripped the channel prefix, so the identity key
        # lost the channel disambiguator — and an IG scoped-ID whose last-12
        # digit tail matched a patient's phone number silently MERGED with
        # that patient's CRM row.
        norm = p
    else:
        # v16g6 FIX R6-H4: canonicalise HERE so no caller can bypass it —
        # the last-12 rule then always sees the same country-coded spelling
        # the webhook writes. (Legacy rows hashed from a bare national
        # number converge onto the E.164 identity — the dedupe direction
        # this fix exists to force.)
        norm = re.sub(r"\D", "", _normalize_msisdn(p) or p)[-12:]
    return hashlib.sha256(f"{customer_id}|{norm}".encode()).hexdigest()[:40]


def _normalize_msisdn(raw: str) -> str:
    """v14g3 BUG 11/12: canonicalise a phone number to digits in a COUNTRY-AWARE
    way, so the same line always yields the same key while two different lines
    that merely share the last 10 digits (different country codes) stay distinct.
      • strip every non-digit
      • drop a leading '00' international prefix, then a single leading '0' trunk
      • if exactly 10 digits remain (a bare national number), prepend the default
        country code (DEFAULT_COUNTRY_CODE — India '91' by default)
      • otherwise keep the digits as-is (they already carry a country code)
    Returns '' when there aren't enough digits to be a real number."""
    d = re.sub(r"\D", "", raw or "")
    if d.startswith("00"):
        d = d[2:]
    # v16g3 FIX R3-L12: strip EVERY leading trunk-'0' while more than a bare
    # 10-digit national number remains — "091 98765 43210" (13 digits) used
    # to pass through 0-prefixed, minting HX_WA_0919… beside HX_WA_919… for
    # the SAME clinic typed two ways. Subsumes the old single-'0' 11-digit
    # rule.
    while d.startswith("0") and len(d) > 10:
        d = d[1:]
    if len(d) < 7:
        return ""
    if len(d) == 10:
        d = cfg.DEFAULT_COUNTRY_CODE + d
    return d
