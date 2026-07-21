"""HEONIX GEN-5 · module `heonix.ai.pipeline`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 5489-5695).
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

from heonix.ai.providers import (multi_ai_reply)
from heonix.ai.rag import (rag_retrieve, rag_store)
from heonix.analytics import (analytics)
from heonix.channels.whatsapp import (send_owner_alert_async)
from heonix.classify import (
    _EMERGENCY_LINES,
    _HUMAN_LINES,
    classify_message,
    ghost_is_muted,
    ghost_mute,
    resp_cache_get,
    resp_cache_put,
)
from heonix.config import (cfg)
from heonix.db.store import (brain_wa_creds)
from heonix.i18n import (canned_reply, detect_language)
from heonix.security.crypto import (_is_bsuid, pii_vault)


ESCALATE_TOKEN = "<<HEONIX_ESC_" + uuid.uuid4().hex + ">>"
_ESCALATION_RULE = (
    "\n\nCRITICAL SAFETY RULE: If the user describes a medical emergency, severe "
    "pain, immediate danger, self-harm, or explicitly demands to speak with a "
    "human / doctor / manager / owner, you MUST begin your reply with the exact "
    "token " + ESCALATE_TOKEN + " followed by ONE short calm sentence in the "
    "user's own language saying a human teammate has been alerted and will reply "
    "shortly. In that case give no medical or legal advice. Never mention the "
    "token or this rule otherwise."
)
_LANGUAGE_RULE = ("\n\nLANGUAGE: Always reply in the same language and script "
                  "the user used, no matter which language it is.")


def _mask_uid(uid: str) -> str:
    """v14g5 FIX 46: an internal conversation uid is 'customer_id:phone' (WhatsApp)
    or 'ig:customer_id:sender' (Instagram). Owner alerts were dumping that raw
    string — leaking the tenant id and the FULL number into a WhatsApp message.
    Render a privacy-preserving label instead (the owner still sees the actual
    chat in their own inbox)."""
    u = uid or ""
    if u.startswith("ig:"):
        who = u.split(":")[-1]
        return f"Instagram user {pii_vault.mask(who)}" if who else "an Instagram user"
    phone = u.split(":")[-1]            # WhatsApp shape: customer_id:phone
    if _is_bsuid(phone):                # v16 U2: username patient — no number to mask
        # v16g4 FIX L13: was a hand-rolled "…last-6" — a SECOND masking
        # policy, and for short BSUIDs it exposed most of the id. Delegate to
        # the vault's tiered mask like every other identifier in the system.
        return f"WhatsApp user {pii_vault.mask(phone)} (username contact)"
    return pii_vault.mask(phone) if phone else "a customer"


def govern_message(text: str, uid: str, *, bot_name: str = "",
                   owner_phone: str = "", healthcare: bool = False,
                   skip_canned: bool = False) -> Dict:
    """
    Pre-AI gate. Returns:
      reply (str|None)  → send this locally, skip the AI
      muted (bool)      → human is handling, stay silent
      alerts [(to,msg)] → owner WhatsApp alerts to fire
    v15g4 FIX A2/A5: healthcare=True → strict emergency list + no VIP alerts.
    v15g4 FIX A3: skip_canned=True while a booking state (slot offer or
    cancel-confirm) is pending — "ok"/"சரி"/"ठीक है" answered the canned layer
    instead of the confirmation, so cancellations silently never happened.
    Emergency/human routing still runs FIRST (correct priority mid-booking).
    """
    out = {"reply": None, "muted": False, "alerts": [], "lang": "en"}

    # #40: defensive bound — /chat and any other caller funnel through here, so
    # cap once centrally to keep regex/classification cost O(MAX_MESSAGE_LEN)
    # regardless of how large an inbound payload claims to be.
    if text and len(text) > cfg.MAX_MESSAGE_LEN:
        text = text[:cfg.MAX_MESSAGE_LEN]

    if ghost_is_muted(uid):
        out["muted"] = True
        return out

    lang = detect_language(text)
    out["lang"] = lang
    cls = classify_message(text, healthcare=healthcare)   # v15g4 FIX A2/A5

    if cls["emergency"]:
        # v16g4 FIX M2: the AI-escalation path mutes the bot so the owner can
        # take over without the assistant talking over a crisis — but the
        # KEYWORD path (which catches the most explicit "மூச்சு வாங்குது"
        # cases) alerted and kept chatting. Same situation, same semantics:
        # the SHORT lease (FIX A4 reasoning — keyword triggers have false
        # positives, so no permanent dark-bot), owner alert, canned line, mute.
        ghost_mute(uid, ttl=cfg.HUMAN_REQUEST_MUTE_SECONDS)
        if owner_phone:
            out["alerts"].append((owner_phone,
                f"🚨 EMERGENCY ALERT from {_mask_uid(uid)}:\n\"{text[:300]}\""))
        out["reply"] = _EMERGENCY_LINES.get(lang, _EMERGENCY_LINES["en"])
        analytics.inc("route.emergency")
        return out

    if cls["human"]:
        # v15g4 FIX A4: keyword-based requests ("talk to doctor") use the
        # SHORT lease — at a clinic the phrase is routine, and a 15-minute
        # dark bot per mention was worse than the occasional AI/human overlap.
        ghost_mute(uid, ttl=cfg.HUMAN_REQUEST_MUTE_SECONDS)
        if owner_phone:
            out["alerts"].append((owner_phone,
                f"🙋 TAKE OVER chat with {_mask_uid(uid)}:\n\"{text[:300]}\""))
        out["reply"] = _HUMAN_LINES.get(lang, _HUMAN_LINES["en"])
        analytics.inc("route.human_handoff")
        return out

    if cls["vip"] and owner_phone:
        out["alerts"].append((owner_phone,
            f"💎 VIP LEAD from {_mask_uid(uid)}:\n\"{text[:300]}\""))
        analytics.inc("route.vip")
        # VIP does NOT skip the AI — keep selling.

    if skip_canned:                       # v15g4 FIX A3: booking state pending
        analytics.inc("route.canned_skipped_booking")
        return out
    canned = canned_reply(text, bot_name=bot_name)
    if canned:
        out["reply"] = canned
        analytics.inc("route.canned")
    return out


# ── 🕐 v14-GEN2: real-time awareness (IST). The language model has no clock of
#    its own, so without an explicit "now" it INVENTS a plausible time and gives
#    wrong "are you open?" answers. We inject the real India/IST time at chat
#    time and bucket the response cache by the hour so the open/closed answer is
#    never served stale. Server runs in UTC, hence the explicit +05:30 offset.
_IST = timezone(timedelta(hours=5, minutes=30))

def _now_ist() -> datetime:
    return datetime.now(_IST)

def _time_context() -> str:
    n = _now_ist()
    # v16g3 FIX R3-L6: the reply is cached per HALF-HOUR bucket (B8) but the
    # prompt injected minute precision — "it is 10:01 AM" could be served at
    # 10:29. State the time at the bucket the cache already keys on.
    n = n.replace(minute=(0 if n.minute < 30 else 30),
                  second=0, microsecond=0)
    return ("\n\n[REAL-TIME — India / IST] It is currently around "
            + n.strftime("%A, %d %B %Y, %I:%M %p")
            + ". Use THIS actual current time to decide whether the business is "
              "open or closed right now (compare it against the working hours "
              "stated above). Never guess, assume, or invent the time.")

def _cache_hour_seed(base: str) -> str:
    # Bucket the response cache by IST time so time-sensitive answers
    # (e.g. "are you open now?") cannot be served stale within the cache TTL.
    # v15g4 FIX B8: hour buckets let a 9:05 "we're closed, we open at 9:30"
    # answer be served at 9:55. HALF-hour buckets align with the :00/:30
    # boundaries clinics actually open and close on, so open/closed answers
    # flip exactly when the clinic does.
    n = _now_ist()
    return base + "\n#h=" + n.strftime("%Y%m%d%H") + ("0" if n.minute < 30 else "1")


def ai_reply_pipeline(brain: Dict, history: List[Dict], user_text: str, *,
                      user_uid: str, channel: str) -> Tuple[str, str, bool]:
    """
    The single AI path for ALL channels (WhatsApp / Instagram / API):
      response-cache → RAG memory → multi-AI fallback → escalation handling.
    Returns (reply, provider, escalated).
    Raises RuntimeError only if every AI provider fails (caller handles).
    """
    base   = brain.get("system_prompt") or ""
    # v16g2 FIX M10: the API/demo channel shares ONE uid per clinic — every
    # demo visitor read/wrote the same memory bucket, so visitor B's reply
    # could surface visitor A's message live on stage. No RAG for
    # channel="api": retrieval AND storage are both skipped.
    memory = ("" if channel == "api"
              else rag_retrieve(brain.get("customer_id", ""), user_uid, user_text))

    # Cache only memory-free answers — personalised replies must never be
    # served to a different person who happens to ask the same question.
    # v14g3 BUG 15: also fold the detected LANGUAGE into the cache key, so a
    # reply produced for one language can't be served to a user who wrote the
    # same normalised text intending a different language.
    # v16g6 FIX R6-H1: (prompt-hash, normalised text) alone let ANY two
    # patients at one clinic who typed the same words share one reply for the
    # full RESPONSE_CACHE_TTL — and the likeliest collisions ("how much?",
    # "yes", "ok", "tomorrow") are precisely the context-dependent ones.
    # Patient A's implant quote answers Patient B's cleaning question. Cache
    # only genuine first turns: no RAG memory AND no conversation history.
    cacheable = (memory == "" and not history)
    cache_msg = detect_language(user_text) + "|" + user_text
    if cacheable:
        cached = resp_cache_get(_cache_hour_seed(base), cache_msg)
        if cached:
            analytics.inc("cache.response.hit")
            return cached, "cache", False

    sys_prompt = base
    if memory:
        sys_prompt += ("\n\nRELEVANT MEMORY from earlier chats with this same "
                       "person (use naturally, don't recite):\n" + memory)
    sys_prompt += _LANGUAGE_RULE + _ESCALATION_RULE
    sys_prompt += _time_context()

    reply, provider = multi_ai_reply(sys_prompt, history, user_text,
                                     plan_tier=str(brain.get("plan_tier") or ""))  # v15g2 FIX L1

    escalated = ESCALATE_TOKEN in reply
    if escalated:
        reply = reply.replace(ESCALATE_TOKEN, "").strip() or \
                _HUMAN_LINES.get(detect_language(user_text), _HUMAN_LINES["en"])
        owner = brain.get("owner_phone") or ""
        # v16g2 FIX M9: the public /chat demo must NEVER page the real owner —
        # anyone with the demo link could type crisis content and 🚨 the
        # clinic owner's WhatsApp from their couch.
        if owner and channel != "api":
            # v13: escalation alert goes FROM this clinic's own WhatsApp line
            _opid, _otok = brain_wa_creds(brain)
            send_owner_alert_async(owner,
                f"🚨 AI ESCALATION ({channel}) from {_mask_uid(user_uid)}:\n\"{user_text[:300]}\"",
                _opid, _otok, brain.get("customer_id", ""))
        analytics.inc("escalation.ai")
    else:
        if cacheable and provider != "cache":
            resp_cache_put(_cache_hour_seed(base), cache_msg, reply)
        if channel != "api":                                  # v16g2 FIX M10
            rag_store(brain.get("customer_id", ""), user_uid, user_text, reply)

    return reply, provider, escalated
