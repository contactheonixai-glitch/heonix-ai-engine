"""HEONIX GEN-5 · module `heonix.ai.providers`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 3073-3108, 3117-3330).
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
from heonix.config import (cfg)
from heonix.logsetup import (log)
from heonix.resilience import (
    AIEmptyResponse,
    _claude_breaker,
    _gemini_breaker,
    _openai_breaker,
)
from heonix import _latebind  # GEN-5 SPLIT


AI_PROVIDERS_ACTIVE: Dict[str, bool] = {}

# Singletons — instantiated once at startup
_openai_client: Any  = None
_claude_client: Any  = None


def _init_ai_providers() -> None:
    global _openai_client, _claude_client
    if cfg.GENAI_API_KEY and GEMINI_AVAILABLE:
        genai.configure(api_key=cfg.GENAI_API_KEY)
        AI_PROVIDERS_ACTIVE["gemini"] = True
        log.info("✅ Gemini AI ready (Primary)")
    else:
        AI_PROVIDERS_ACTIVE["gemini"] = False
        log.warning("⚠️  Gemini not configured.")

    if cfg.OPENAI_API_KEY and OPENAI_AVAILABLE:
        _openai_client = openai_lib.OpenAI(api_key=cfg.OPENAI_API_KEY)
        AI_PROVIDERS_ACTIVE["openai"] = True
        log.info("✅ OpenAI GPT ready (Fallback #1)")
    else:
        AI_PROVIDERS_ACTIVE["openai"] = False

    if cfg.ANTHROPIC_API_KEY and CLAUDE_AVAILABLE:
        _claude_client = anthropic_lib.Anthropic(api_key=cfg.ANTHROPIC_API_KEY)
        AI_PROVIDERS_ACTIVE["claude"] = True
        log.info("✅ Anthropic Claude ready (Fallback #2)")
    else:
        AI_PROVIDERS_ACTIVE["claude"] = False

    _latebind.publish("_openai_client", _openai_client)  # GEN-5 SPLIT: heonix.media reads this
    active = [k for k, v in AI_PROVIDERS_ACTIVE.items() if v]
    if not active:
        log.error("❌ No AI providers configured! Set at least one API key.")
    else:
        log.info(f"🤖 AI Fallback Chain: {' → '.join(active)}")


def _safe_response_text(resp: Any) -> str:
    """v14g3 BUG 18: Gemini's `.text` *raises* (ValueError) when the model emits
    no usable candidate. The old `.text.strip()` therefore threw a raw exception
    that got retried 3× and counted as hard breaker failures — a safety block
    could trip the Gemini circuit. Extract text defensively; '' when none."""
    try:
        t = getattr(resp, "text", None)
        if t:
            return t.strip()
    except Exception:
        pass
    try:
        for cand in (getattr(resp, "candidates", None) or []):
            parts = getattr(getattr(cand, "content", None), "parts", None) or []
            buf = "".join((getattr(p, "text", "") or "") for p in parts).strip()
            if buf:
                return buf
    except Exception:
        pass
    return ""


@functools.lru_cache(maxsize=64)
def _gemini_model(model_name: str, system_instruction: str = ""):
    """v16g4 FIX P2: genai.GenerativeModel was constructed PER CALL in chat,
    transcription and image understanding — the same per-request-client
    pattern v11 FIX #10/#11 killed for OpenAI/Anthropic. Bounded LRU keyed on
    (model, system_instruction) so per-clinic prompts each keep one client."""
    if system_instruction:
        return genai.GenerativeModel(model_name=model_name,
                                     system_instruction=system_instruction)
    return genai.GenerativeModel(model_name=model_name)


def _call_gemini(system_prompt: str, history: List[Dict], user_message: str,
                 model_name: str = "") -> str:
    model = _gemini_model(
        model_name or cfg.GEMINI_MODEL,   # v15g2 FIX L1: premium tier
        system_prompt,                    # v16g4 FIX P2: cached client
    )
    chat = model.start_chat(history=history)
    # v14g3 BUG 2: a HARD request timeout — a frozen Gemini socket can no longer
    # pin a worker thread forever (previously only OpenAI passed a timeout).
    resp = chat.send_message(
        user_message,
        request_options={"timeout": cfg.AI_TIMEOUT_SECS},
    )
    text = _safe_response_text(resp)          # v14g3 BUG 18: safe extraction
    if not text:
        raise AIEmptyResponse("gemini returned no text")
    return text


def _call_openai(system_prompt: str, history: List[Dict], user_message: str) -> str:
    messages = [{"role": "system", "content": system_prompt}]
    for turn in history:
        role    = "assistant" if turn["role"] == "model" else "user"
        content = turn["parts"][0] if turn.get("parts") else ""
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})
    resp = _openai_client.chat.completions.create(
        model=cfg.OPENAI_MODEL,
        messages=messages,
        max_tokens=cfg.AI_MAX_TOKENS,
        timeout=cfg.AI_TIMEOUT_SECS,
    )
    # v15 FIX 8: content is None on refusals/filters — `.strip()` on None threw
    # AttributeError, burned 3 retries, and hit the breaker. Gemini and Claude
    # both got safe extraction in v14g3 BUG 18; OpenAI was skipped. Now aligned.
    choice = resp.choices[0] if getattr(resp, "choices", None) else None
    text   = ((getattr(getattr(choice, "message", None), "content", "") or "")
              .strip()) if choice else ""
    if not text:
        raise AIEmptyResponse("openai returned no text")
    return text


def _call_claude(system_prompt: str, history: List[Dict], user_message: str) -> str:
    messages = []
    for turn in history:
        role    = "assistant" if turn["role"] == "model" else "user"
        content = turn["parts"][0] if turn.get("parts") else ""
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})
    resp = _claude_client.messages.create(
        model=cfg.ANTHROPIC_MODEL,
        max_tokens=cfg.AI_MAX_TOKENS,
        system=system_prompt,
        messages=messages,
        timeout=cfg.AI_TIMEOUT_SECS,   # v14g3 BUG 2: hard timeout (was unbounded)
    )
    # v14g3 BUG 18: tolerate an empty content list instead of raising IndexError.
    blocks = getattr(resp, "content", None) or []
    text = "".join((getattr(b, "text", "") or "") for b in blocks).strip()
    if not text:
        raise AIEmptyResponse("claude returned no text")
    return text


_PERMANENT_AI_ERR_NAMES = {
    # openai / anthropic SDK exception class names
    "AuthenticationError", "PermissionDeniedError", "NotFoundError",
    "BadRequestError", "UnprocessableEntityError",
    # google.api_core / grpc class names
    "InvalidArgument", "PermissionDenied", "NotFound", "Unauthenticated",
    "FailedPrecondition",
}


def _is_permanent_ai_error(exc: Exception) -> bool:
    """v15g4 FIX B7: a bad API key, revoked permission, or an invalid model
    name will NOT heal on a retry — the old loop burned every attempt (plus
    ~7-8s of backoff) per provider and hammered the breaker with the same
    deterministic failure. Classify by SDK exception class name first, then by
    HTTP status where the SDK exposes one. Unknown → treated as transient."""
    if type(exc).__name__ in _PERMANENT_AI_ERR_NAMES:
        return True
    status = (getattr(exc, "status_code", None)
              or getattr(getattr(exc, "response", None), "status_code", None)
              or getattr(exc, "code", None))
    try:
        return int(status) in (400, 401, 403, 404, 422)
    except (TypeError, ValueError):
        return False


def _retry_with_backoff(fn: Callable, *args, max_retries: int = 3,
                         base_delay: float = 1.0) -> Any:
    """
    Exponential back-off with full jitter (FIX #9).
    Retries on transient errors only; re-raises on final attempt.
    v15g4 FIX B7: the docstring above is finally TRUE — permanent 4xx-class
    errors are re-raised immediately instead of being retried.
    """
    # v16g6 FIX R6-L3: MAX_RETRIES=-1 (accepted silently by _env_int) made
    # range() empty — the loop never ran, the function fell off the end, and
    # None propagated outward as the AI reply.
    for attempt in range(max(0, max_retries) + 1):
        try:
            return fn(*args)
        except AIEmptyResponse:
            # v14g3 BUG 18: an empty/safety-blocked reply will not change on a
            # retry — re-raise immediately so we fall straight through to the
            # next provider instead of burning the retry budget and counting
            # multiple spurious failures against the circuit breaker.
            raise
        except Exception as exc:
            if attempt == max_retries or _is_permanent_ai_error(exc):  # v15g4 FIX B7
                raise
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1.0)
            log.warning(f"⚠️  Attempt {attempt+1}/{max_retries} failed ({exc}) — retry in {delay:.1f}s")
            time.sleep(delay)


def multi_ai_reply(
    system_prompt: str,
    history: List[Dict],
    user_message: str,
    plan_tier: str = "",
) -> Tuple[str, str]:
    """
    Try providers in order: Gemini → OpenAI → Claude.
    Each provider uses circuit breaker + exponential back-off retry.
    Returns (reply_text, provider_used). Raises RuntimeError only if ALL fail.
    v15g2 FIX L1: plan_tier='premium' now genuinely routes Gemini calls to
    GEMINI_MODEL_PREMIUM — the Config comment promised this since v11 while
    plan_tier was only ever SELECTed for the customer list. Dead promise, wired.
    """
    # v16g6 FIX R6-L2: this local used to be named `_gemini_model`, shadowing
    # the module-level lru_cache'd factory of the same name — one future
    # `_gemini_model(...)` call in this scope away from "'str' object is not
    # callable".
    _gemini_model_name = (cfg.GEMINI_MODEL_PREMIUM
                          if (plan_tier or "").strip().lower() == "premium"
                          else cfg.GEMINI_MODEL)
    providers = [
        ("gemini", _gemini_breaker,
         lambda s, h, u, _m=_gemini_model_name: _call_gemini(s, h, u, _m)),
        ("openai", _openai_breaker, _call_openai),
        ("claude", _claude_breaker, _call_claude),
    ]
    errors = []
    for name, breaker, fn in providers:
        if not AI_PROVIDERS_ACTIVE.get(name):
            continue
        try:
            t0    = time.monotonic()
            reply = breaker.call(_retry_with_backoff, fn, system_prompt,
                                 history, user_message,
                                 max_retries=cfg.MAX_RETRIES,
                                 base_delay=cfg.RETRY_BASE_DELAY)
            latency_ms = (time.monotonic() - t0) * 1000
            analytics.inc(f"ai.{name}.success")
            analytics.record_latency(f"ai.{name}.latency_ms", latency_ms)
            if name != "gemini":
                log.info(f"🔄 AI fallback used: {name}")
            return reply, name
        except RuntimeError as exc:
            # v15g4 FIX C5: only the breaker's own RuntimeError is a
            # circuit-open; any other RuntimeError from the provider path was
            # being mislabelled in errors + analytics.
            if str(exc).startswith("CircuitBreaker"):
                errors.append(f"{name}:circuit_open")
                analytics.inc(f"ai.{name}.circuit_open")
            else:
                errors.append(f"{name}:{exc}")
                analytics.inc(f"ai.{name}.error")
                log.warning(f"⚠️  {name} failed — next provider. Error: {exc}")
        except Exception as exc:
            errors.append(f"{name}:{exc}")
            analytics.inc(f"ai.{name}.error")
            log.warning(f"⚠️  {name} failed — next provider. Error: {exc}")

    raise RuntimeError(f"All AI providers failed: {'; '.join(errors)}")


_latebind.register("_openai_client", __name__)  # GEN-5 SPLIT
