"""HEONIX GEN-5 · module `heonix.media`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 5138-5308).
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

from heonix.ai.providers import (AI_PROVIDERS_ACTIVE, _gemini_model, _safe_response_text)
from heonix.analytics import (analytics)
from heonix.channels.whatsapp import (_wa_session)
from heonix.config import (cfg)
from heonix.logsetup import (log)
from heonix import _latebind  # GEN-5 SPLIT
_openai_client: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.ai.providers at startup
_latebind.register('_openai_client', __name__)


_TRANSCRIBE_PROMPT = ("Transcribe this voice message to plain text. Keep the "
                      "original language exactly as spoken. Return ONLY the "
                      "transcript, nothing else.")


def _download_capped(url: str, headers: Optional[Dict] = None) -> Tuple[bytes, str]:
    """v12 #7/#39: stream a media file with a HARD byte cap + (connect, read)
    timeouts. Returns (bytes, content_type). Raises if the file exceeds
    MEDIA_MAX_BYTES — so a 100 MB upload can never be slurped whole into a
    512 MB dyno, and a stalled CDN socket can't pin a worker forever."""
    timeout = (cfg.HTTP_CONNECT_TIMEOUT, cfg.MEDIA_READ_TIMEOUT)
    with _wa_session.get(url, headers=headers or {}, timeout=timeout,
                         stream=True) as r:
        r.raise_for_status()
        clen = r.headers.get("Content-Length")
        if clen and clen.isdigit() and int(clen) > cfg.MEDIA_MAX_BYTES:
            raise ValueError(f"media too large: {clen} B > cap {cfg.MEDIA_MAX_BYTES}")
        mime = r.headers.get("Content-Type", "")
        buf  = bytearray()
        for chunk in r.iter_content(chunk_size=65536):
            if not chunk:
                continue
            buf.extend(chunk)
            if len(buf) > cfg.MEDIA_MAX_BYTES:
                raise ValueError(f"media exceeded cap {cfg.MEDIA_MAX_BYTES} B mid-stream")
        return bytes(buf), mime


def transcribe_audio_bytes(audio_bytes: bytes, mime: str = "audio/ogg") -> str:
    """Never raises — returns '' on failure so one bad audio can't 500 a webhook."""
    if not audio_bytes:
        return ""
    mime = (mime or "audio/ogg").split(";")[0].strip()

    # 1) Gemini (primary — already configured by _init_ai_providers)
    if AI_PROVIDERS_ACTIVE.get("gemini"):
        try:
            gmodel = _gemini_model(cfg.GEMINI_MODEL)   # v16g4 FIX P2
            resp   = gmodel.generate_content(
                [_TRANSCRIBE_PROMPT, {"mime_type": mime, "data": audio_bytes}],
                request_options={"timeout": cfg.AI_TIMEOUT_SECS})   # v14g5 FIX 9
            text = _safe_response_text(resp)   # v15 FIX 19: .text RAISES on
            #                                    safety blocks — same guard the
            #                                    image path already had
            if text:
                analytics.inc("voice.gemini.success")
                return text
        except Exception as exc:
            log.warning(f"⚠️  Gemini transcription failed: {exc}")
            analytics.inc("voice.gemini.error")

    # 2) OpenAI Whisper fallback (fixes v9 drawback #4)
    if AI_PROVIDERS_ACTIVE.get("openai") and _openai_client is not None:
        try:
            buf = io.BytesIO(audio_bytes)
            buf.name = "voice." + ("ogg" if "ogg" in mime else
                                   (mime.split("/")[-1] or "mp3"))
            tr = _openai_client.audio.transcriptions.create(
                model=cfg.OPENAI_TRANSCRIBE_MODEL, file=buf,
                timeout=cfg.AI_TIMEOUT_SECS)   # v14g5 FIX 9
            text = (getattr(tr, "text", "") or "").strip()
            if text:
                analytics.inc("voice.whisper.success")
                log.info("🔄 Voice fallback used: whisper")
                return text
        except Exception as exc:
            log.warning(f"⚠️  Whisper transcription failed: {exc}")
            analytics.inc("voice.whisper.error")

    return ""


def transcribe_voice_note(media_id: str, token: str = "") -> str:
    """WhatsApp: media_id → signed URL → bytes → transcript. '' on any failure.
    v14g5 FIX 2: fetch media with the OWNING clinic's token (passed in) so a tenant
    on its own token is actually retrievable; falls back to the global token."""
    token = token or cfg.WHATSAPP_TOKEN
    if not media_id or not token:
        return ""
    try:
        hdr  = {"Authorization": f"Bearer {token}"}
        meta = _wa_session.get(
            f"https://graph.facebook.com/{cfg.GRAPH_API_VERSION}/{media_id}",
            headers=hdr, timeout=(cfg.HTTP_CONNECT_TIMEOUT, 15))
        meta.raise_for_status()
        info         = meta.json()
        audio, ctype = _download_capped(info["url"], headers=hdr)   # v12 #7/#39
        return transcribe_audio_bytes(
            audio, info.get("mime_type") or ctype or "audio/ogg")
    except Exception as exc:
        log.error(f"❌ Voice download failed: {exc}")
        return ""


_IG_MEDIA_HOST_SUFFIXES = (".fbcdn.net", ".cdninstagram.com", ".fbsbx.com",
                           ".facebook.com", ".instagram.com")


def transcribe_audio_url(url: str) -> str:
    """Instagram: attachments carry a public CDN URL — no auth header needed.
    v16g3 FIX R3-L4: host allow-listed to Meta's CDNs. The webhook signature
    is the primary gate, but with the app secret unset (the dev default) a
    forged webhook could point this fetch at arbitrary/internal URLs (SSRF —
    bounded at 16 MB, but still a free proxy)."""
    if not url:
        return ""
    try:
        _p = urlparse(url)
        _h = (_p.hostname or "").lower()
        if _p.scheme != "https" or not any(
                _h == s.lstrip(".") or _h.endswith(s)
                for s in _IG_MEDIA_HOST_SUFFIXES):
            log.warning(f"🚫 IG audio URL host rejected: {_h or '(none)'}")
            analytics.inc("instagram.media_host_rejected")
            return ""
        audio, ctype = _download_capped(url)                       # v12 #7/#39
        return transcribe_audio_bytes(audio, ctype or "audio/mp4")
    except Exception as exc:
        log.error(f"❌ IG audio download failed: {exc}")
        return ""


_IMAGE_PROMPT = (
    "You are assisting a business (e.g. a clinic or real-estate office) on "
    "WhatsApp. A customer sent this image. In 1-2 short, factual sentences, "
    "describe what is shown so a staff member can act on it. If it shows a "
    "document, prescription, report, ID, or property, say so and read the key "
    "visible details. Do NOT give a medical diagnosis or legal/financial advice "
    "— only describe. If the image is unclear, say that plainly."
)


def understand_image_bytes(img_bytes: bytes, mime: str = "image/jpeg") -> str:
    """v14g4: describe an image with Gemini (your existing multimodal key).
    Never raises — returns '' on failure so one bad image can't 500 a webhook."""
    if not img_bytes or not AI_PROVIDERS_ACTIVE.get("gemini"):
        return ""
    mime = (mime or "image/jpeg").split(";")[0].strip()
    try:
        gmodel = _gemini_model(cfg.GEMINI_MODEL)   # v16g4 FIX P2
        resp   = gmodel.generate_content(
            [_IMAGE_PROMPT, {"mime_type": mime, "data": img_bytes}],
            request_options={"timeout": cfg.AI_TIMEOUT_SECS})   # v14g3 BUG 2 discipline
        text = _safe_response_text(resp)                        # v14g3 BUG 18 helper
        if text:
            analytics.inc("image.gemini.success")
            return text
    except Exception as exc:
        log.warning(f"⚠️  Gemini image understanding failed: {exc}")
        analytics.inc("image.gemini.error")
    return ""


def understand_image_media(media_id: str, token: str = "") -> str:
    """WhatsApp: media_id → signed URL → bytes → Gemini description. '' on failure.
    v14g5 FIX 2: fetch with the owning clinic's token (global fallback)."""
    token = token or cfg.WHATSAPP_TOKEN
    if not media_id or not token:
        return ""
    try:
        hdr  = {"Authorization": f"Bearer {token}"}
        meta = _wa_session.get(
            f"https://graph.facebook.com/{cfg.GRAPH_API_VERSION}/{media_id}",
            headers=hdr, timeout=(cfg.HTTP_CONNECT_TIMEOUT, 15))
        meta.raise_for_status()
        info       = meta.json()
        img, ctype = _download_capped(info["url"], headers=hdr)   # hard byte cap
        return understand_image_bytes(img, info.get("mime_type") or ctype or "image/jpeg")
    except Exception as exc:
        log.error(f"❌ Image download failed: {exc}")
        return ""
