"""HEONIX GEN-5 · module `heonix.api.validators`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 5701-5753).
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
from heonix.security.crypto import (_normalize_msisdn)


class WebhookPayloadValidator(BaseModel):
    customer_name:  str = Field(default="Anonymous Client", min_length=1, max_length=200)
    business_type:  str = Field(default="General Business", max_length=300)
    extra_notes:    str = Field(default="", max_length=1000)
    whatsapp_phone: str = Field(default="", max_length=20)
    owner_phone:    str = Field(default="", max_length=20)   # v10: alerts target
    instagram_id:   str = Field(default="", max_length=60)   # v10: IG business id

    @field_validator("customer_name", "business_type", mode="before")
    @classmethod
    def strip_strings(cls, v: Any) -> str:
        return str(v).strip() if v else ""


class ChatRequestValidator(BaseModel):
    customer_id: str = Field(..., min_length=3, max_length=100, pattern=r"^[A-Z0-9_]+$")
    # v15g2 FIX L6: was hardcoded 2000 — silently ignored a raised MAX_MESSAGE_LEN
    message:     str = Field(..., min_length=1, max_length=cfg.MAX_MESSAGE_LEN)
    session_id:  str = Field(default="", max_length=100)

    @field_validator("message", "session_id", mode="before")
    @classmethod
    def strip_str(cls, v: Any) -> str:
        return str(v).strip() if v else ""


class CRMContactValidator(BaseModel):
    customer_id:   str  = Field(..., min_length=3, max_length=100)
    name:          str  = Field(..., min_length=1, max_length=200)
    phone:         str  = Field(..., min_length=7, max_length=20)
    email:         str  = Field(default="", max_length=200)
    notes:         str  = Field(default="", max_length=2000)
    contact_stage: str  = Field(default="lead", max_length=50)
    is_consented:  bool = Field(default=False)

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, v: Any) -> str:
        phone = re.sub(r"[^\d+]", "", str(v))
        if len(phone) < 7:
            raise ValueError("Phone number too short")
        # v16g6 FIX R6-H4: Meta always delivers E.164; this API kept whatever
        # the admin typed. A bare 10-digit entry minted a DIFFERENT phone_hash
        # than the same patient's webhook row — two CRM rows, split booking
        # history, double follow-ups, and erasure reaching only one of them.
        # Canonicalise through the SAME function the webhook path uses.
        norm = _normalize_msisdn(phone)
        return norm or phone


class AdminLoginValidator(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=200)
