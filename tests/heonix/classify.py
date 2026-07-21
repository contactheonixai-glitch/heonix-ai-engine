"""HEONIX GEN-5 · module `heonix.classify`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 4243-4347, 4909-5134).
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
from heonix.cache import (brain_cache)
from heonix.config import (cfg)
from heonix.i18n import (_norm_text)


BUSINESS_TEMPLATES: Dict[str, Dict] = {
    "restaurant": {
        "keywords": ["restaurant", "cafe", "food", "dining", "catering", "bistro", "bakery", "hotel"],
        "bot_name": "NOVA",
        "prompt": (
            "You are NOVA, a warm and knowledgeable AI dining assistant for {name}. "
            "Help guests explore the menu, make reservations, clarify dietary needs, "
            "and create a memorable hospitality experience. "
            "Always respond in the same language the user writes in."
        ),
    },
    "ecommerce": {
        "keywords": ["shop", "store", "ecommerce", "product", "order", "shipping", "fashion", "retail"],
        "bot_name": "PULSE",
        "prompt": (
            "You are PULSE, a fast and friendly AI shopping assistant for {name}. "
            "Help customers find products, track orders, handle returns, and provide "
            "personalised recommendations. Be concise and solutions-focused. "
            "Always respond in the same language the user writes in."
        ),
    },
    "healthcare": {
        "keywords": ["clinic", "health", "doctor", "medical", "hospital", "dental", "pharmacy", "wellness", "patient"],
        "bot_name": "HELIO",
        "prompt": (
            "You are HELIO, a compassionate AI health assistant for \"{name}\". "
            "The clinic you represent is \"{name}\" — this is the ONLY clinic name you may ever use. "
            "When asked the clinic name, you MUST answer exactly \"{name}\" and nothing else. "
            "CRITICAL: Never invent, guess, or make up any clinic name, address, location, "
            "doctor name, fees, or timings. If a detail was not given to you, do NOT fabricate it — "
            "instead say you will check and confirm, or ask the patient to contact the clinic directly. "
            "Answer general health queries and help schedule appointments with empathy and clarity. "
            "NEVER provide diagnoses or prescribe treatments. "
            "Always recommend a licensed professional for serious concerns. "
            "All data is handled per DPDP Act / HIPAA compliance. "
            "Always respond in the same language the user writes in."
        ),
    },
    "education": {
        "keywords": ["school", "education", "tutoring", "course", "learning", "academy", "university", "coaching"],
        "bot_name": "SAGE",
        "prompt": (
            "You are SAGE, a knowledgeable AI learning assistant for {name}. "
            "Help students and parents understand offerings, guide enrolment, "
            "and answer academic queries with patience and clarity. "
            "Always respond in the same language the user writes in."
        ),
    },
    "saas": {
        "keywords": ["software", "saas", "platform", "app", "tool", "startup", "tech", "ai", "api", "dashboard"],
        "bot_name": "APEX",
        "prompt": (
            "You are APEX, a razor-sharp AI product specialist for {name}. "
            "Help users understand features, navigate onboarding, handle billing queries, "
            "and escalate technical issues. Be precise and solution-focused. "
            "Always respond in the same language the user writes in."
        ),
    },
    "legal": {
        "keywords": ["law", "legal", "lawyer", "attorney", "advocate", "court", "litigation"],
        "bot_name": "LEX",
        "prompt": (
            "You are LEX, a professional AI legal intake assistant for {name}. "
            "Help prospects understand services, qualify case types, and book consultations. "
            "NEVER provide specific legal advice. Always recommend a licensed attorney. "
            "Be formal, precise, and trustworthy. "
            "Always respond in the same language the user writes in."
        ),
    },
    "default": {
        "keywords": [],
        "bot_name": "ELITE",
        "prompt": (
            "You are ELITE, a professional AI business assistant for {name}. "
            "Understand customer needs, provide excellent support, and create a memorable "
            "brand experience. Be sharp, efficient, and solutions-focused. "
            "Always respond in the same language the user writes in."
        ),
    },
}


def detect_business_type(description: str) -> str:
    """v15 FIX 4 (HIGH): the old `kw in lower` was a SUBSTRING test, so the
    saas keyword "ai" matched Chenn-AI, Mumb-AI, h-AI-r and rep-AI-r — a hair
    salon in Chennai onboarded as APEX the SaaS bot. And dict order let "shop"
    (ecommerce) claim a "medical shop" before healthcare was even checked.
    Now: whole-word matching via _kw_hit (the same negation-aware matcher the
    emergency classifier uses) + an explicit priority order with healthcare
    first — for a clinics-first product, ties break toward HELIO."""
    norm  = _norm_text(description)
    order = ("healthcare", "legal", "education", "restaurant", "ecommerce", "saas")
    extra = tuple(k for k in BUSINESS_TEMPLATES
                  if k not in order and k != "default")
    for btype in order + extra:
        if any(_kw_hit(norm, kw) for kw in BUSINESS_TEMPLATES[btype]["keywords"]):
            return btype
    return "default"


def build_system_prompt(customer_name: str, business_desc: str) -> Tuple[str, str]:
    btype    = detect_business_type(business_desc)
    template = BUSINESS_TEMPLATES[btype]
    prompt   = template["prompt"].format(name=customer_name)
    return template["bot_name"], prompt


_EMERGENCY_KW_UNIVERSAL = [
    # NOTE: lone "urgent" removed on purpose — sales leads say "urgent" too.
    "emergency", "medical emergency",
    "accident", "heart attack", "chest pain", "can't breathe", "cant breathe",
    "fainted", "collapsed", "suicide", "kill myself", "sos",
    # v11 #10: romanised Tamil/Hindi markers (launch markets)
    "moochu vanga", "moochi vanga", "saans nahi", "aatmahatya",
    "thatkolai", "vibathu",
    "விபத்து", "தற்கொலை", "மூச்சு வாங்க", "மூச்சு முட்ட",
    "इमरजेंसी", "साँस नहीं", "आत्महत्या", "दुर्घटना",
]
_EMERGENCY_KW_BROAD_EXTRA = [
    # pain/blood/urgency words — active for NON-healthcare verticals only
    "severe pain", "unbearable", "bleeding",
    "romba vali", "thanga mudiyala", "rathum", "bahut dard", "khoon",
    # v16g2 FIX M15: dizziness vocabulary moved OUT of the universal list —
    # "konjam mayakkam-a irukku" is routine clinic talk (fasting, medication
    # side-effects); genuine collapse is still caught by "fainted"/"collapsed"
    # (universal) and by the AI escalation token in every language.
    "mayakkam", "behosh", "மயக்கம்",
    "அவசரம்", "ரொம்ப வலி", "தாங்க முடியல", "ரத்தம்", "बहुत दर्द", "खून",
]
# backward-compat alias (full list) for any external import/tests
_EMERGENCY_KW = _EMERGENCY_KW_UNIVERSAL + _EMERGENCY_KW_BROAD_EXTRA
_HUMAN_KW = [
    "talk to a human", "talk to human", "talk to a person", "real person",
    "human agent", "live agent", "customer care", "speak to the doctor",
    "talk to the doctor", "talk to doctor", "speak to manager", "talk to manager",
    "talk to owner", "speak to owner", "connect me to", "transfer me",
    "i want to talk to", "want to speak to",
    "டாக்டர் கிட்ட பேசணும்", "மேனேஜர் கிட்ட", "ஆள் கிட்ட பேசணும்",
    "எம்.டி கிட்ட", "நேரடியா பேசணும்",
    "डॉक्टर से बात", "मैनेजर से बात", "किसी इंसान से बात", "इंसान से बात",
]
_VIP_KW = [
    "crore", "crores", "lakh", "lakhs", "budget", "premium", "luxury",
    "penthouse", "villa", "bulk order", "wholesale", "enterprise plan",
    "கோடி", "லட்சம்", "பட்ஜெட்", "வில்லா", "करोड़", "लाख", "बजट",
]
# v16g3 FIX R3-H1: no left word-boundary meant "3 floors 2", "visiting
# hours 9", "2 doors 4", "offers 50" all matched the rs/inr branch and
# fired 💎 VIP owner alerts — the "Chenn-AI" substring bug's twin, alive
# inside a regex. \b keeps "rs 500" / "Rs.2000" / "inr 99" firing.
_MONEY_RE  = re.compile(r"(₹|\brs\.?\s?\d|\binr\s?\d)", re.IGNORECASE)
_BIGNUM_RE = re.compile(r"\d+\s*(crore|crores|cr|lakh|lakhs)\b", re.IGNORECASE)


def _money_hit(text: str) -> bool:
    """v16g4 FIX L9: the ₹/lakh VIP trigger was a raw regex — the negation
    window every KEYWORD respects (v11 #9) never applied, so "my budget is
    NOT 50 lakhs" and "illa, 2 crore mudiyadhu" still pinged the owner as a
    VIP lead. Check the up-to-3 normalized tokens before the match for a
    negator, same window _kw_hit uses."""
    for rx in (_MONEY_RE, _BIGNUM_RE):
        m = rx.search(text or "")
        if not m:
            continue
        pre = _norm_text(text[:m.start()]).split()[-3:]
        if not any(t in _NEGATORS for t in pre):
            return True
    return False

# v11 #9: words that, immediately before a keyword, flip its meaning.
_NEGATORS = {
    "no", "not", "non", "without", "never", "dont", "doesnt", "isnt", "wont",
    "cant", "neither", "nor", "illa", "illai", "kidaiyaadhu", "nahi", "nahin",
    "mat", "bina", "bila",
}
# v16g2 FIX N1: Tamil and Hindi negate AFTER the word ("வலி இல்ல", "dard nahi")
# — the pre-token check alone made illa/nahi dead weight in their own
# languages: "மயக்கம் இல்ல" (no dizziness) fired the emergency route. Checked
# against the token immediately FOLLOWING a keyword match.
_NEGATORS_POST = {
    "illa", "illai", "illaye", "kidaiyaadhu", "nahi", "nahin",
    "maatten", "matten", "mudiyadhu", "mudiyathu", "vendam", "venda",
    "இல்ல", "இல்லை", "மாட்டேன்", "முடியாது", "வேண்டாம்", "नहीं", "नही",
}


@functools.lru_cache(maxsize=1024)
def _kw_toks(keyword: str) -> tuple:
    """v15g3 FIX 5 (MED-PERF): _kw_hit re-ran _norm_text (unicodedata NFKD +
    casefold + regex strip) on the SAME constant keyword strings for EVERY
    inbound message — classify_message alone fires it across the emergency/
    human/VIP lists, then business detection re-fires it across every
    template's keyword list. That is hundreds of redundant Unicode
    normalisations per message in the single hottest path in the engine.
    The keyword vocabulary is a small fixed set → memoise its token tuples
    once; per-message cost drops to a dict hit."""
    return tuple(_norm_text(keyword).split())


def _kw_hit(norm_text: str, keyword: str,
            pre_w: int = 1, post_w: int = 3) -> bool:
    """v11 #9: whole-word match for `keyword` inside already-normalised text,
    skipping negated occurrences ('no budget' → VIP, 'no chest pain' →
    emergency stay silent while real 'severe chest pain' fires).
    v15g3 FIX 5: keyword tokenisation memoised via _kw_toks.
    v16g3 FIX R3-H3: the negation check was ONE token wide on each side.
    "i don't want to talk to the doctor, just book" fired a TAKE-OVER alert
    ('dont' sits 3 back), and "cancel my appointment illa" (ta/hi negation is
    CLAUSE-FINAL, past the object) started the cancel-confirm flow. Windows:
      pre_w  — tokens scanned BEFORE the match for _NEGATORS (default 1;
               emergencies keep 1 so a 'not' clauses earlier can never mute a
               real 'chest pain'; the human list passes 3).
      post_w — tokens scanned AFTER the match for the clause-final
               _NEGATORS_POST set (default 3; pass 0 to disable).
    Every widened skip fails SAFE: skipped destructive/handoff intents fall
    through to the AI escalation token or the read-only status branch."""
    kw_toks = _kw_toks(keyword)
    if not kw_toks:
        return False
    toks    = norm_text.split()
    n       = len(kw_toks)
    for i in range(len(toks) - n + 1):
        if tuple(toks[i:i + n]) == kw_toks:   # tuple() — kw_toks is a cached tuple
            if any(t in _NEGATORS
                   for t in toks[max(0, i - max(1, pre_w)):i]):
                continue           # pre-negated occurrence → keep scanning
            if post_w and any(t in _NEGATORS_POST
                              for t in toks[i + n:i + n + post_w]):
                continue           # clause-final negation → keep scanning
            return True
    return False


_HEALTH_FLAG_CACHE: Dict[str, Tuple[str, bool]] = {}   # v16g4 FIX P3


def _brain_is_health(brain: Dict) -> bool:
    """v16g4 FIX P3: detect_business_type walks the full keyword template map
    — and ran PER MESSAGE for every non-HELIO brain. The verdict only changes
    when the brain row changes, so cache it keyed on the row's updated_at."""
    cid = brain.get("customer_id") or ""
    ver = str(brain.get("updated_at") or "")
    hit = _HEALTH_FLAG_CACHE.get(cid)
    if hit and hit[0] == ver:
        return hit[1]
    flag = ((brain.get("bot_name") or "").upper() == "HELIO"
            or detect_business_type(brain.get("business_type") or "") == "healthcare")
    if len(_HEALTH_FLAG_CACHE) > 4096:      # unbounded-growth guard
        _HEALTH_FLAG_CACHE.clear()
    _HEALTH_FLAG_CACHE[cid] = (ver, flag)
    return flag


def classify_message(text, healthcare: bool = False):
    """Returns {'emergency','human','vip'} booleans. Pure, instant, free.
    v11 #9: word-boundary + negation aware (was naive substring matching).
    v15g4 FIX A2/A5: healthcare=True → strict life-threat emergency list
    (pain/blood words are routine clinic vocabulary; the AI escalation token
    covers nuance) and VIP is always False (every ₹/fee question at a clinic
    was pinging the doctor — alert fatigue buries real alerts)."""
    norm = _norm_text(text)
    ekw  = (_EMERGENCY_KW_UNIVERSAL if healthcare
            else _EMERGENCY_KW_UNIVERSAL + _EMERGENCY_KW_BROAD_EXTRA)
    return {
        # v16g3 FIX R3-H3: emergency PINS pre_w=1 — a stray 'not' earlier in
        # the sentence must never suppress a genuine life-threat keyword. The
        # human list gets pre_w=3 so "i don't want to talk to the doctor" no
        # longer pages the owner + mutes the bot for 5 minutes.
        "emergency": any(_kw_hit(norm, k, pre_w=1) for k in ekw),
        "human":     any(_kw_hit(norm, k, pre_w=3) for k in _HUMAN_KW),
        "vip":       (False if healthcare else                     # v15g4 FIX A5
                      (any(_kw_hit(norm, k) for k in _VIP_KW)
                       or _money_hit(text))),   # v16g4 FIX L9: negation-aware
    }

# ⟦PURE-LOGIC-END⟧


_EMERGENCY_LINES = {
    # v15g4 FIX C11: name India's real numbers (108 ambulance / 112 all-in-one)
    # instead of the vague "your local emergency number".
    "ta": ("உங்கள் செய்தி எங்கள் குழுவிற்கு உடனடியாக அனுப்பப்பட்டது. "
           "மருத்துவ அவசரநிலை எனில் உடனே 108 அல்லது 112-ஐ அழைக்கவும்."),
    "hi": ("आपका संदेश हमारी टीम को तुरंत भेज दिया गया है। "
           "मेडिकल इमरजेंसी होने पर कृपया तुरंत 108 या 112 पर कॉल करें।"),
    "en": ("Your message has been sent to our team right away. If this is a "
           "medical emergency, please call 108 or 112 immediately."),
}
_HUMAN_LINES = {
    "ta": "ஒரு நிமிடம் 🙏 உங்களை எங்கள் குழுவுடன் இணைக்கிறேன்.",
    "hi": "एक मिनट 🙏 मैं आपको हमारी टीम से जोड़ रहा हूँ।",
    "en": "One moment 🙏 connecting you with our team now.",
}


# ── 👻 Ghost mode — Redis-backed via brain_cache → works across ALL gunicorn
#    workers (the in-memory v9 version silently broke with --workers 4).
def ghost_mute(uid: str, ttl: int = 0) -> None:
    # v15g4 FIX A4: keyword handoffs pass HUMAN_REQUEST_MUTE_SECONDS (short);
    # AI-escalation and manual takeover keep the full GHOST_MUTE_SECONDS.
    brain_cache.set(f"ghost:{uid}", 1, ttl=(ttl or cfg.GHOST_MUTE_SECONDS))
    analytics.inc("ghost.muted")


def ghost_is_muted(uid: str) -> bool:
    return brain_cache.get(f"ghost:{uid}") is not None


def ghost_resume(uid: str) -> None:
    brain_cache.delete(f"ghost:{uid}")


# ── 🗄️ Response cache — brain_cache backend = survives restarts + shared
#    across workers when REDIS_URL is set (fixes v9 drawback #1).
def _resp_key(system_prompt: str, message: str) -> str:
    # v11 fix #6: hash the WHOLE prompt, not [:200]. Two customers whose prompts
    # share the first 200 chars (very common — same template header) would
    # otherwise collide and get each other's cached answers. The prompt already
    # carries the customer identity, so a full-prompt hash is the cache boundary.
    raw = (hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()
           + "|" + _norm_text(message)).encode("utf-8")
    return "resp:" + hashlib.sha256(raw).hexdigest()[:32]


def resp_cache_get(system_prompt: str, message: str) -> Optional[str]:
    val = brain_cache.get(_resp_key(system_prompt, message))
    return val if isinstance(val, str) and val else None


def resp_cache_put(system_prompt: str, message: str, reply: str) -> None:
    if reply:
        brain_cache.set(_resp_key(system_prompt, message), reply,
                        ttl=cfg.RESPONSE_CACHE_TTL)
