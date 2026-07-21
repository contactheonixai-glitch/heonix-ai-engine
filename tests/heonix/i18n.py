"""HEONIX GEN-5 · module `heonix.i18n`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 4367-4893).
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
from heonix.config import (cfg)


_SCRIPT_RANGES = [
    ("ta", 0x0B80, 0x0BFF),   # Tamil
    ("te", 0x0C00, 0x0C7F),   # Telugu
    ("kn", 0x0C80, 0x0CFF),   # Kannada
    ("ml", 0x0D00, 0x0D7F),   # Malayalam
    ("hi", 0x0900, 0x097F),   # Devanagari (Hindi/Marathi/Nepali)
    ("bn", 0x0980, 0x09FF),   # Bengali
    ("gu", 0x0A80, 0x0AFF),   # Gujarati
    ("pa", 0x0A00, 0x0A7F),   # Gurmukhi (Punjabi)
    ("or", 0x0B00, 0x0B7F),   # Odia
    ("si", 0x0D80, 0x0DFF),   # Sinhala
    ("ar", 0x0600, 0x06FF),   # Arabic / Urdu script
    ("ru", 0x0400, 0x04FF),   # Cyrillic
    ("th", 0x0E00, 0x0E7F),   # Thai
    ("zh", 0x4E00, 0x9FFF),   # CJK
    ("ja", 0x3040, 0x30FF),   # Kana
    ("ko", 0xAC00, 0xD7AF),   # Hangul
]


def detect_language(text):
    """Script-based detection, with a romanised-text fallback (v11 #10).
    The AI always replies in the user's language via _LANGUAGE_RULE; this
    function only decides which *local* canned/emergency line to use."""
    counts = {}
    for ch in text:
        cp = ord(ch)
        for code, lo, hi in _SCRIPT_RANGES:
            if lo <= cp <= hi:
                counts[code] = counts.get(code, 0) + 1
                break
    if counts:
        # v16g3 FIX R3-L5: Japanese text is usually MAJORITY kanji, so the
        # CJK bucket outvoted Kana and mostly-kanji Japanese classified as
        # zh. Any kana at all proves Japanese; fold the kanji votes in.
        if "ja" in counts and "zh" in counts:
            counts["ja"] += counts.pop("zh")
        return max(counts, key=counts.get)
    # v11 #10: pure-Latin input → could be romanised Tamil/Hindi ("vanakkam",
    # "enakku romba vali"). Without this, a Tamil speaker typing in English
    # letters got the English emergency line. AI reply path was already fine.
    return _romanized_lang(text) or "en"


# Strong romanised markers — chosen to NOT collide with common English words.
_ROMAN_TA = {
    "vanakkam", "nandri", "enakku", "enaku", "romba", "rumba", "vali",
    "poitu", "poidu", "varen", "eppadi", "epadi", "irukku", "iruku",
    "venum", "vendum", "seekiram", "seekkiram", "kandippa", "udane",
    "moochu", "moochi", "thangala", "thangamudiyala", "ratham", "vibathu",   # v16g4 FIX L1: was "rathum" — never matched real romanised bleeding msgs
    "thatkolai", "saavu", "mayakkam", "sapida", "sappida", "udanadiyaa",  # v16g2 FIX C6
}
_ROMAN_HI = {
    "namaste", "namaskar", "dhanyavad", "dhanyawad", "shukriya", "kaise",
    "kyun", "nahi", "nahin", "madad", "chahiye", "kripya", "theek",
    "bahut", "dard", "jaldi", "turant", "khoon", "saans", "behosh",
    "aatmahatya", "bachao",
}


def _romanized_lang(text):
    """Returns 'ta' / 'hi' if the Latin text carries strong romanised markers,
    else None. Conservative: needs at least one high-confidence token."""
    toks = set(_norm_text(text).split())
    ta = len(toks & _ROMAN_TA)
    hi = len(toks & _ROMAN_HI)
    if ta == 0 and hi == 0:
        return None
    return "ta" if ta >= hi else "hi"


# ═════════════════════════════════════════════════════════════════════════════
# 🌐  v16g4 FIX M8 — LOCALIZED SYSTEM STRINGS  (en / ta / hi)
#   Reminder copy, follow-up copy, phone request, booking prompts and confirm
#   buttons were all English-only in a Tamil-first product — while the
#   language stack sat right there. Every system-authored patient-facing
#   string now routes through _t(); the AI reply path was already fine
#   (_LANGUAGE_RULE). Detection is per-message; a confident detection is
#   remembered for 7 days so a button tap (always Latin) keeps the patient's
#   language instead of resetting to English.
# ═════════════════════════════════════════════════════════════════════════════
_L10N_SUPPORTED = ("en", "ta", "hi")

_L10N: Dict[str, Dict[str, str]] = {
    "phone_request": {
        "en": ("To send you appointment reminders, could you share your "
               "mobile number? Tap below — or just type it. It's optional "
               "and stays with the clinic only. 🙏"),
        "ta": ("உங்கள் அப்பாய்ண்ட்மென்ட் நினைவூட்டல்களை அனுப்ப, உங்கள் "
               "மொபைல் எண்ணை பகிர முடியுமா? கீழே தட்டவும் — அல்லது டைப் "
               "செய்யவும். இது விருப்பம் மட்டுமே; கிளினிக்கிடம் மட்டுமே "
               "இருக்கும். 🙏"),
        "hi": ("आपको अपॉइंटमेंट रिमाइंडर भेजने के लिए, क्या आप अपना मोबाइल "
               "नंबर साझा कर सकते हैं? नीचे टैप करें — या बस टाइप करें। यह "
               "वैकल्पिक है और सिर्फ़ क्लिनिक के पास रहेगा। 🙏"),
    },
    "offer_header": {
        "en": "Here are the next available times — tap one or reply with its number:",
        "ta": "அடுத்த கிடைக்கும் நேரங்கள் இதோ — ஒன்றை தட்டவும் அல்லது அதன் எண்ணை அனுப்பவும்:",
        "hi": "अगले उपलब्ध समय ये हैं — किसी एक को टैप करें या उसका नंबर भेजें:",
    },
    "no_slots": {
        "en": ("Sorry, there are no open slots in the next few days. "
               "Please try again later, or leave a message for our team."),
        "ta": ("மன்னிக்கவும், அடுத்த சில நாட்களில் காலி நேரம் இல்லை. சிறிது "
               "நேரம் கழித்து முயற்சிக்கவும், அல்லது எங்கள் குழுவிற்கு "
               "செய்தி விடவும்."),
        "hi": ("क्षमा करें, अगले कुछ दिनों में कोई स्लॉट खाली नहीं है। कृपया "
               "बाद में फिर कोशिश करें, या हमारी टीम के लिए संदेश छोड़ें।"),
    },
    "booked_confirmed": {
        "en": ("✅ Booked! Your appointment is confirmed for *{when}*. "
               "We'll remind you beforehand. Reply 'cancel appointment' "
               "anytime to cancel."),
        "ta": ("✅ முடிந்தது! உங்கள் அப்பாய்ண்ட்மென்ட் *{when}* அன்று உறுதி "
               "செய்யப்பட்டது. முன்கூட்டியே நினைவூட்டுவோம். ரத்து செய்ய "
               "எப்போது வேண்டுமானாலும் 'cancel appointment' என அனுப்பவும்."),
        "hi": ("✅ हो गया! आपका अपॉइंटमेंट *{when}* के लिए पक्का हो गया है। "
               "हम पहले से याद दिला देंगे। रद्द करने के लिए कभी भी "
               "'cancel appointment' भेजें।"),
    },
    "booked_rescheduled": {
        "en": ("✅ Booked! Your appointment is rescheduled to *{when}*. "
               "We'll remind you beforehand. Reply 'cancel appointment' "
               "anytime to cancel."),
        "ta": ("✅ முடிந்தது! உங்கள் அப்பாய்ண்ட்மென்ட் *{when}*-க்கு "
               "மாற்றப்பட்டது. முன்கூட்டியே நினைவூட்டுவோம். ரத்து செய்ய "
               "எப்போது வேண்டுமானாலும் 'cancel appointment' என அனுப்பவும்."),
        "hi": ("✅ हो गया! आपका अपॉइंटमेंट *{when}* पर बदल दिया गया है। हम "
               "पहले से याद दिला देंगे। रद्द करने के लिए कभी भी "
               "'cancel appointment' भेजें।"),
    },
    "own_slot_kept": {
        "en": ("That's your current appointment — you're already booked for "
               "*{when}*, so it's kept. ✅"),
        "ta": ("அது உங்களின் தற்போதைய அப்பாய்ண்ட்மென்ட் தான் — *{when}* "
               "அன்று ஏற்கனவே பதிவாகி உள்ளது, அப்படியே வைத்துள்ளோம். ✅"),
        "hi": ("यही आपका मौजूदा अपॉइंटमेंट है — *{when}* के लिए आप पहले से "
               "बुक हैं, वैसा ही रखा है। ✅"),
    },
    "slot_taken": {
        "en": "Sorry, that slot was just taken — here are fresh times:",
        "ta": "மன்னிக்கவும், அந்த நேரம் இப்போதுதான் நிரம்பியது — புதிய நேரங்கள் இதோ:",
        "hi": "क्षमा करें, वह स्लॉट अभी-अभी भर गया — नए समय ये हैं:",
    },
    "pick_number": {
        "en": "Please reply with the *number* of a time from the list:",
        "ta": "பட்டியலில் உள்ள நேரத்தின் *எண்ணை* அனுப்பவும்:",
        "hi": "सूची में से समय का *नंबर* भेजें:",
    },
    "offer_expired": {
        "en": "That list had expired — here are fresh times:",
        "ta": "அந்த பட்டியல் காலாவதியாகிவிட்டது — புதிய நேரங்கள் இதோ:",
        "hi": "वह सूची पुरानी हो गई थी — नए समय ये हैं:",
    },
    "save_error": {
        "en": ("Sorry — something went wrong saving your booking. "
               "Please reply with the number once more. 🙏"),
        "ta": ("மன்னிக்கவும் — பதிவை சேமிப்பதில் சிக்கல் ஏற்பட்டது. எண்ணை "
               "மீண்டும் ஒருமுறை அனுப்பவும். 🙏"),
        "hi": ("क्षमा करें — बुकिंग सेव करने में दिक्कत आई। कृपया नंबर एक "
               "बार फिर भेजें। 🙏"),
    },
    "stop_booking": {
        "en": "No problem — I've stopped the booking.{kept} Ask anytime to book again. 🙂",
        "ta": ("பரவாயில்லை — பதிவு நிறுத்தப்பட்டது.{kept} மீண்டும் பதிவு "
               "செய்ய எப்போது வேண்டுமானாலும் கேளுங்கள். 🙂"),
        "hi": ("कोई बात नहीं — बुकिंग रोक दी है।{kept} दोबारा बुक करने के "
               "लिए कभी भी कहें। 🙂"),
    },
    "kept_note": {
        "en": " Your existing appointment is unchanged.",
        "ta": " உங்கள் தற்போதைய அப்பாய்ண்ட்மென்ட் அப்படியே உள்ளது.",
        "hi": " आपका मौजूदा अपॉइंटमेंट वैसा ही है।",
    },
    "cancel_confirm": {
        "en": "You have an appointment on *{when}*.\n\nAre you sure you want to cancel it?",
        "ta": "உங்களுக்கு *{when}* அன்று அப்பாய்ண்ட்மென்ட் உள்ளது.\n\nநிச்சயமாக ரத்து செய்யவா?",
        "hi": "आपका अपॉइंटमेंट *{when}* को है।\n\nक्या आप वाकई इसे रद्द करना चाहते हैं?",
    },
    "btn_yes_cancel": {"en": "Yes, cancel", "ta": "ஆம், ரத்து செய்", "hi": "हाँ, रद्द करें"},
    "btn_no_keep":    {"en": "No, keep it", "ta": "வேண்டாம், வைத்திரு", "hi": "नहीं, रहने दें"},
    "btn_pick_time":  {"en": "Pick a time", "ta": "நேரம் தேர்வு", "hi": "समय चुनें"},
    "hdr_book":       {"en": "Book appointment", "ta": "அப்பாய்ண்ட்மென்ட்", "hi": "अपॉइंटमेंट बुक करें"},
    "cancelled_ok": {
        "en": ("✅ Cancelled your appointment ({when}). Reply 'book' anytime "
               "to pick a new time."),
        "ta": ("✅ உங்கள் அப்பாய்ண்ட்மென்ட் ரத்து செய்யப்பட்டது ({when}). "
               "புதிய நேரம் தேர்வு செய்ய 'book' என அனுப்பவும்."),
        "hi": ("✅ आपका अपॉइंटमेंट रद्द कर दिया गया ({when})। नया समय चुनने "
               "के लिए 'book' भेजें।"),
    },
    "cancel_failed": {
        "en": ("Sorry — I couldn't cancel that just now. Please try again in "
               "a moment, or call the clinic. 🙏"),
        "ta": ("மன்னிக்கவும் — இப்போது ரத்து செய்ய முடியவில்லை. சிறிது நேரம் "
               "கழித்து முயற்சிக்கவும், அல்லது கிளினிக்கை அழைக்கவும். 🙏"),
        "hi": ("क्षमा करें — अभी रद्द नहीं हो पाया। कृपया थोड़ी देर में फिर "
               "कोशिश करें, या क्लिनिक को कॉल करें। 🙏"),
    },
    "already_changed": {
        "en": ("That appointment was already changed — reply 'my appointment' "
               "to check the latest."),
        "ta": ("அந்த அப்பாய்ண்ட்மென்ட் ஏற்கனவே மாற்றப்பட்டுவிட்டது — "
               "சமீபத்தியதை பார்க்க 'my appointment' என அனுப்பவும்."),
        "hi": ("वह अपॉइंटमेंट पहले ही बदल चुका है — नवीनतम देखने के लिए "
               "'my appointment' भेजें।"),
    },
    "keep_unchanged": {
        "en": "👍 No problem — your appointment is unchanged.",
        "ta": "👍 பரவாயில்லை — உங்கள் அப்பாய்ண்ட்மென்ட் அப்படியே உள்ளது.",
        "hi": "👍 कोई बात नहीं — आपका अपॉइंटमेंट वैसा ही है।",
    },
    "reconfirm_cancel": {
        "en": ("Just to confirm — reply *YES* to cancel your appointment, "
               "or *NO* to keep it."),
        "ta": ("உறுதிப்படுத்த — ரத்து செய்ய *YES* என்றும், வைத்திருக்க *NO* "
               "என்றும் அனுப்பவும்."),
        "hi": "पुष्टि के लिए — रद्द करने के लिए *YES* भेजें, रखने के लिए *NO*।",
    },
    "no_upcoming_cancel": {
        "en": ("I couldn't find an upcoming appointment to cancel. "
               "Reply 'book' to make one. 🙂"),
        "ta": ("ரத்து செய்ய வரவிருக்கும் அப்பாய்ண்ட்மென்ட் எதுவும் இல்லை. "
               "புதிதாக பதிவு செய்ய 'book' என அனுப்பவும். 🙂"),
        "hi": ("रद्द करने के लिए कोई आगामी अपॉइंटमेंट नहीं मिला। नया बुक "
               "करने के लिए 'book' भेजें। 🙂"),
    },
    "status_upcoming": {
        "en": ("📅 Your upcoming appointment: *{when}*. Reply 'cancel "
               "appointment' to cancel or 'reschedule' to change."),
        "ta": ("📅 உங்கள் வரவிருக்கும் அப்பாய்ண்ட்மென்ட்: *{when}*. ரத்து "
               "செய்ய 'cancel appointment', மாற்ற 'reschedule' என அனுப்பவும்."),
        "hi": ("📅 आपका आगामी अपॉइंटमेंट: *{when}*। रद्द करने के लिए "
               "'cancel appointment', बदलने के लिए 'reschedule' भेजें।"),
    },
    "status_none": {
        "en": ("You don't have an upcoming appointment yet. Reply 'book "
               "appointment' and I'll show you available times. 🙂"),
        "ta": ("உங்களுக்கு இன்னும் வரவிருக்கும் அப்பாய்ண்ட்மென்ட் இல்லை. "
               "'book appointment' என அனுப்பினால் கிடைக்கும் நேரங்களை "
               "காட்டுகிறேன். 🙂"),
        "hi": ("आपका अभी कोई आगामी अपॉइंटमेंट नहीं है। 'book appointment' "
               "भेजें, मैं उपलब्ध समय दिखा दूँगा। 🙂"),
    },
    "typed_yes_no": {
        "en": "Reply *YES* to cancel or *NO* to keep it.",
        "ta": "ரத்து செய்ய *YES*, வைத்திருக்க *NO* என அனுப்பவும்.",
        "hi": "रद्द करने के लिए *YES*, रखने के लिए *NO* भेजें।",
    },
    "reminder": {
        "en": ("⏰ Reminder: you have an appointment {hrs} — *{when}*. "
               "Reply 'cancel appointment' if you can't make it."),
        "ta": ("⏰ நினைவூட்டல்: உங்களுக்கு {hrs} அப்பாய்ண்ட்மென்ட் உள்ளது — "
               "*{when}*. வர முடியாவிட்டால் 'cancel appointment' என "
               "அனுப்பவும்."),
        "hi": ("⏰ रिमाइंडर: आपका अपॉइंटमेंट {hrs} है — *{when}*। न आ पाएँ "
               "तो 'cancel appointment' भेजें।"),
    },
    "t_today":    {"en": "today",    "ta": "இன்று", "hi": "आज"},
    "t_tomorrow": {"en": "tomorrow", "ta": "நாளை",  "hi": "कल"},
    "t_in_hour":  {"en": "in about an hour", "ta": "சுமார் ஒரு மணி நேரத்தில்",
                   "hi": "लगभग एक घंटे में"},
    "t_in_hours": {"en": "in ~{n} hour(s)", "ta": "சுமார் {n} மணி நேரத்தில்",
                   "hi": "लगभग {n} घंटे में"},
    "followup": {
        "en": ("Hi! 👋 Just checking in from {bot} — do you still have any "
               "questions we can help with? We're happy to assist anytime."),
        "ta": ("வணக்கம்! 👋 {bot} சார்பாக ஒரு சிறிய நினைவூட்டல் — உங்களுக்கு "
               "இன்னும் ஏதேனும் கேள்விகள் உள்ளதா? எப்போது வேண்டுமானாலும் "
               "உதவ தயாராக இருக்கிறோம்."),
        "hi": ("नमस्ते! 👋 {bot} की ओर से बस हालचाल — क्या अब भी कोई सवाल है "
               "जिसमें हम मदद कर सकें? हम कभी भी मदद के लिए तैयार हैं।"),
    },
    "phone_saved_reminders": {
        "en": "✅ Thank you! We'll send your appointment reminders to {masked}.",
        "ta": ("✅ நன்றி! உங்கள் அப்பாய்ண்ட்மென்ட் நினைவூட்டல்களை "
               "{masked}-க்கு அனுப்புவோம்."),
        "hi": "✅ धन्यवाद! आपके अपॉइंटमेंट रिमाइंडर {masked} पर भेजेंगे।",
    },
    "phone_saved_records": {
        "en": "✅ Thank you! We've noted {masked} for the clinic's records.",
        "ta": "✅ நன்றி! கிளினிக் பதிவுகளுக்காக {masked} குறித்துக்கொண்டோம்.",
        "hi": "✅ धन्यवाद! क्लिनिक रिकॉर्ड के लिए {masked} नोट कर लिया है।",
    },
    "card_deferred": {
        "en": ("📇 Thanks! Just to be sure I save YOUR number (and not "
               "someone else's), could you type your own 10-digit mobile "
               "number?"),
        "ta": ("📇 நன்றி! உங்களுடைய எண்ணைத்தான் சேமிக்கிறேன் என்பதை உறுதி "
               "செய்ய, உங்கள் சொந்த 10-இலக்க மொபைல் எண்ணை டைப் செய்யவும்?"),
        "hi": ("📇 धन्यवाद! यह पक्का करने के लिए कि मैं आपका ही नंबर सेव "
               "करूँ (किसी और का नहीं), कृपया अपना 10 अंकों का मोबाइल नंबर "
               "टाइप करें?"),
    },
    "location_ack": {
        "en": ("📍 Thanks, we've received your location! Our team will take "
               "it from here — meanwhile, feel free to type any question."),
        "ta": ("📍 நன்றி, உங்கள் இருப்பிடம் கிடைத்தது! எங்கள் குழு "
               "தொடர்ந்து கவனிக்கும் — இதற்கிடையில் எந்த கேள்வியும் "
               "தட்டச்சு செய்யலாம்."),
        "hi": ("📍 धन्यवाद, आपकी लोकेशन मिल गई! हमारी टीम आगे संभाल लेगी — "
               "इस बीच कोई भी सवाल टाइप कर सकते हैं।"),
    },
    "opted_out": {
        "en": ("You've been unsubscribed from follow-up messages. You can "
               "still message us anytime for help. 🙏"),
        "ta": ("பின்தொடர் செய்திகளிலிருந்து நீங்கள் விலக்கப்பட்டீர்கள். "
               "உதவிக்கு எப்போது வேண்டுமானாலும் எங்களுக்கு செய்தி "
               "அனுப்பலாம். 🙏"),
        "hi": ("आपको फ़ॉलो-अप संदेशों से हटा दिया गया है। मदद के लिए आप कभी "
               "भी हमें संदेश भेज सकते हैं। 🙏"),
    },
    "card_unreadable": {
        "en": ("📇 Thanks for sharing! I couldn't read a usable number from "
               "that — could you type your 10-digit mobile number?"),
        "ta": ("📇 பகிர்ந்ததற்கு நன்றி! அதிலிருந்து பயன்படுத்தக்கூடிய எண்ணை "
               "படிக்க முடியவில்லை — உங்கள் 10-இலக்க மொபைல் எண்ணை டைப் "
               "செய்யவும்?"),
        "hi": ("📇 साझा करने के लिए धन्यवाद! उसमें से नंबर पढ़ नहीं पाया — "
               "कृपया अपना 10 अंकों का मोबाइल नंबर टाइप करें?"),
    },
    # ── v16g5 FIX R5-M2: four patient-facing strings still bypassed _t() and
    # went out in English regardless of the conversation language, despite M8
    # claiming full ta/hi/en coverage of every system string. ──────────────
    "audio_unclear": {
        "en": ("🎤 Sorry, I couldn't hear that clearly — could you please "
               "type your message?"),
        "ta": ("🎤 மன்னிக்கவும், அதைத் தெளிவாகக் கேட்க முடியவில்லை — உங்கள் "
               "செய்தியை டைப் செய்ய முடியுமா?"),
        "hi": ("🎤 माफ़ कीजिए, वह स्पष्ट सुनाई नहीं दिया — क्या आप अपना "
               "संदेश टाइप कर सकते हैं?"),
    },
    "image_unreadable": {
        "en": ("📎 Thanks for the image! I couldn't read it clearly — could "
               "you briefly type what you'd like help with?"),
        "ta": ("📎 படத்திற்கு நன்றி! அதைத் தெளிவாகப் படிக்க முடியவில்லை — "
               "எதற்கு உதவி வேண்டும் என்று சுருக்கமாக டைப் செய்யவும்?"),
        "hi": ("📎 इमेज के लिए धन्यवाद! मैं उसे साफ़ नहीं पढ़ पाया — कृपया "
               "संक्षेप में टाइप करें कि आपको किसमें मदद चाहिए?"),
    },
    "media_ack": {
        "en": ("📎 Thanks! I've received your file. Our team will review it "
               "shortly. Meanwhile, feel free to type any question and I'll "
               "help right away."),
        "ta": ("📎 நன்றி! உங்கள் கோப்பு கிடைத்தது. எங்கள் குழு விரைவில் "
               "பார்க்கும். இதற்கிடையில் எந்தக் கேள்வியையும் டைப் செய்யுங்கள், "
               "உடனே உதவுகிறேன்."),
        "hi": ("📎 धन्यवाद! आपकी फ़ाइल मिल गई। हमारी टीम जल्द ही देखेगी। इस "
               "बीच कोई भी सवाल टाइप करें, मैं तुरंत मदद करूँगा।"),
    },
    "contact_ack": {
        "en": ("📎 Thanks! I've received the contact. Our team will review it "
               "shortly — meanwhile, feel free to type any question and I'll "
               "help right away."),
        "ta": ("📎 நன்றி! தொடர்பு விவரம் கிடைத்தது. எங்கள் குழு விரைவில் "
               "பார்க்கும் — இதற்கிடையில் எந்தக் கேள்வியையும் டைப் "
               "செய்யுங்கள், உடனே உதவுகிறேன்."),
        "hi": ("📎 धन्यवाद! संपर्क मिल गया। हमारी टीम जल्द ही देखेगी — इस "
               "बीच कोई भी सवाल टाइप करें, मैं तुरंत मदद करूँगा।"),
    },
    "optout_failed": {
        "en": ("Sorry — I couldn't record that just now. Please send STOP "
               "once more, or reply and our team will handle it."),
        "ta": ("மன்னிக்கவும் — அதைப் பதிவு செய்ய முடியவில்லை. STOP என்று "
               "மீண்டும் ஒருமுறை அனுப்பவும், அல்லது பதிலளியுங்கள், எங்கள் "
               "குழு கவனிக்கும்."),
        "hi": ("क्षमा करें — यह अभी दर्ज नहीं हो सका। कृपया एक बार फिर STOP "
               "भेजें, या जवाब दें, हमारी टीम संभाल लेगी।"),
    },
    "ai_unavailable": {
        "en": ("Sorry, our AI is temporarily unavailable. We'll get back to "
               "you shortly!"),
        "ta": ("மன்னிக்கவும், எங்கள் AI தற்காலிகமாக கிடைக்கவில்லை. விரைவில் "
               "உங்களைத் தொடர்பு கொள்கிறோம்!"),
        "hi": ("क्षमा करें, हमारा AI अभी उपलब्ध नहीं है। हम जल्द ही आपसे "
               "संपर्क करेंगे!"),
    },
}


def _t(key: str, lang: str = "en", **kw) -> str:
    """v16g4 FIX M8: localized system string. Unknown key → ''; unknown or
    unsupported lang → English; a bad format placeholder can never raise into
    a webhook (returns the raw template instead)."""
    entry = _L10N.get(key) or {}
    s = entry.get(lang) or entry.get("en") or ""
    if not kw:
        return s
    try:
        return s.format(**kw)
    except Exception:
        return s


def _user_lang(customer_id: str, uid: str, text: str = "") -> str:
    """v16g4 FIX M8: pick the language for system-authored strings. A
    confident per-message detection wins and is remembered for 7 days (keyed
    on the chat uid, so BSUID patients keep theirs too); a button tap or bare
    number (always Latin, <3 words) falls back to the remembered language;
    final fallback is cfg.DEFAULT_LANG. Never raises."""
    try:
        det = detect_language(text) if (text or "").strip() else ""
        if det in ("ta", "hi") or (det == "en" and len((text or "").split()) >= 3):
            try:
                brain_cache.set(f"lang:{customer_id}:{uid}", det, ttl=7 * 86400)
            except Exception:
                pass
            return det if det in _L10N_SUPPORTED else "en"
        cached = brain_cache.get(f"lang:{customer_id}:{uid}")
        if cached in _L10N_SUPPORTED:
            return cached
    except Exception:
        pass
    return cfg.DEFAULT_LANG if cfg.DEFAULT_LANG in _L10N_SUPPORTED else "en"


def _norm_text(text):
    """Lowercase + strip punctuation → stable matching.
    v15g4 FIX A1 (CRITICAL, root-cause): Indic matras and virama are Unicode
    COMBINING MARKS (category M*), which are NOT `isalnum()` — the old filter
    replaced them with spaces, collapsing every Tamil/Hindi word to its bare
    consonant skeleton. Proven live: खाना (food) and खून (blood) both became
    'ख न', so "मुझे खाना चाहिए" (I need food) fired the medical-EMERGENCY
    route + owner alert; சரி became 'சர', etc. EVERY Indic keyword in the
    engine (emergency / human / VIP / booking / canned / cancel-YES) was
    matching skeletons instead of words. Marks are now kept."""
    text = unicodedata.normalize("NFKC", str(text)).lower()
    text = "".join(ch if (ch.isalnum() or ch.isspace()
                          or unicodedata.category(ch).startswith("M"))  # v15g4 FIX A1
                   else " " for ch in text)
    return re.sub(r"\s+", " ", text).strip()


# Canned replies — 10 languages. Any other language → None → goes to the AI,
# which answers natively in whatever language the user wrote.
_CANNED = {
    "greet": {
        "en": "Hello! 👋 I'm {bot}. How can I help you today?",
        "ta": "வணக்கம்! 👋 நான் {bot}. இன்று எப்படி உதவலாம்?",
        "hi": "नमस्ते! 👋 मैं {bot} हूँ। आज मैं कैसे मदद कर सकता हूँ?",
        "te": "నమస్తే! 👋 నేను {bot}. ఈ రోజు మీకు ఎలా సహాయం చేయగలను?",
        "kn": "ನಮಸ್ಕಾರ! 👋 ನಾನು {bot}. ಇಂದು ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?",
        "ml": "നമസ്കാരം! 👋 ഞാൻ {bot}. ഇന്ന് എങ്ങനെ സഹായിക്കാം?",
        "bn": "নমস্কার! 👋 আমি {bot}। আজ কীভাবে সাহায্য করতে পারি?",
        "gu": "નમસ્તે! 👋 હું {bot} છું. આજે કેવી રીતે મદદ કરી શકું?",
        "pa": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! 👋 ਮੈਂ {bot} ਹਾਂ। ਅੱਜ ਕਿਵੇਂ ਮਦਦ ਕਰਾਂ?",
        "ar": "مرحباً! 👋 أنا {bot}. كيف أستطيع مساعدتك اليوم؟",
    },
    "thanks": {
        "en": "You're welcome! 🙏 Anything else I can help with?",
        "ta": "மகிழ்ச்சி! 🙏 வேறு ஏதாவது உதவி வேண்டுமா?",
        "hi": "आपका स्वागत है! 🙏 और कुछ मदद चाहिए?",
        "te": "సంతోషం! 🙏 ఇంకేమైనా సహాయం కావాలా?",
        "kn": "ಸಂತೋಷ! 🙏 ಇನ್ನೇನಾದರೂ ಸಹಾಯ ಬೇಕೇ?",
        "ml": "സന്തോഷം! 🙏 വേറെ എന്തെങ്കിലും സഹായം വേണോ?",
        "bn": "স্বাগতম! 🙏 আর কিছু সাহায্য লাগবে?",
        "gu": "સ્વાગત છે! 🙏 બીજી કોઈ મદદ જોઈએ?",
        "pa": "ਜੀ ਆਇਆਂ ਨੂੰ! 🙏 ਹੋਰ ਕੋਈ ਮਦਦ ਚਾਹੀਦੀ ਹੈ?",
        "ar": "على الرحب والسعة! 🙏 هل تحتاج مساعدة أخرى؟",
    },
    "ack": {
        "en": "👍 Let me know if you need anything else.",
        "ta": "👍 வேறு ஏதாவது தேவைப்பட்டால் சொல்லுங்கள்.",
        "hi": "👍 कुछ और चाहिए तो बताइए।",
        "te": "👍 ఇంకేమైనా కావాలంటే చెప్పండి.",
        "kn": "👍 ಇನ್ನೇನಾದರೂ ಬೇಕಿದ್ದರೆ ತಿಳಿಸಿ.",
        "ml": "👍 വേറെ എന്തെങ്കിലും വേണമെങ്കിൽ പറയൂ.",
        "bn": "👍 আর কিছু লাগলে জানাবেন।",
        "gu": "👍 બીજું કંઈ જોઈએ તો જણાવજો.",
        "pa": "👍 ਹੋਰ ਕੁਝ ਚਾਹੀਦਾ ਹੋਵੇ ਤਾਂ ਦੱਸੋ।",
        "ar": "👍 أخبرني إذا احتجت أي شيء آخر.",
    },
    "bye": {
        "en": "Thank you for reaching out — take care! 👋",
        "ta": "தொடர்பு கொண்டதற்கு நன்றி — பத்திரம்! 👋",
        "hi": "संपर्क करने के लिए धन्यवाद — ध्यान रखें! 👋",
        "te": "సంప్రదించినందుకు ధన్యవాదాలు — జాగ్రత్త! 👋",
        "kn": "ಸಂಪರ್ಕಿಸಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದಗಳು — ಜೋಪಾನ! 👋",
        "ml": "ബന്ധപ്പെട്ടതിന് നന്ദി — ശ്രദ്ധിക്കണേ! 👋",
        "bn": "যোগাযোগের জন্য ধন্যবাদ — ভালো থাকবেন! 👋",
        "gu": "સંપર્ક કરવા બદલ આભાર — સંભાળજો! 👋",
        "pa": "ਸੰਪਰਕ ਕਰਨ ਲਈ ਧੰਨਵਾਦ — ਖ਼ਿਆਲ ਰੱਖਣਾ! 👋",
        "ar": "شكراً لتواصلك — اعتنِ بنفسك! 👋",
    },
}

# v16g2 FIX N6: "menu" removed — the restaurant vertical's single most common
# query was answered with "Hello! 👋 I'm ELITE…" forever instead of the menu.
_GREET_RAW = ["hi", "hii", "hiii", "hey", "hello", "helo", "hlo", "start",
              "vanakkam", "வணக்கம்", "ஹாய்", "ஹலோ", "namaste", "namaskar",
              "नमस्ते", "नमस्कार", "నమస్తే", "నమస్కారం", "ನಮಸ್ಕಾರ", "നമസ്കാരം",
              "নমস্কার", "નમસ્તે", "ਸਤ ਸ੍ਰੀ ਅਕਾਲ", "مرحبا", "السلام عليكم", "اهلا"]
_THANKS_RAW = ["thanks", "thank you", "thank u", "thx", "ty", "tnx",
               # v15g4 FIX C12: "रोम्बा नन्द्री" was Tamil spelled in Devanagari —
               # a dead entry nobody types. Real romanised forms instead.
               "nandri", "romba nandri", "நன்றி", "ரொம்ப நன்றி",
               "dhanyavad", "dhanyawad",
               "धन्यवाद", "शुक्रिया", "ధన్యవాదాలు", "ಧನ್ಯವಾದ", "നന്ദി",
               "ধন্যবাদ", "આભાર", "ਧੰਨਵਾਦ", "شكرا", "شكرًا"]
_ACK_RAW = ["ok", "okay", "okk", "k", "fine", "good", "great", "got it", "done",
            "sari", "சரி", "ஓகே", "thik", "theek", "ठीक", "ठीक है", "ओके",
            "సరే", "ಸರಿ", "ശരി", "ঠিক আছে", "ઠીક છે", "ਠੀਕ ਹੈ", "تمام", "حسنا"]
_BYE_RAW = ["bye", "goodbye", "good bye", "tata", "ta ta", "poitu varen",
            "போயிட்டு வரேன்", "alvida", "अलविदा", "விடை", "మళ్ళీ కలుద్దాం",  # v16g2 FIX N13: விடை (was dead "வீடி")
            "ਅਲਵਿਦਾ", "مع السلامة", "وداعا"]

_GREET  = {_norm_text(x) for x in _GREET_RAW}
_THANKS = {_norm_text(x) for x in _THANKS_RAW}
_ACK    = {_norm_text(x) for x in _ACK_RAW}
_BYE    = {_norm_text(x) for x in _BYE_RAW}


def canned_reply(text, bot_name=""):
    """Local zero-cost reply for trivial messages; None → send to the AI."""
    norm = _norm_text(text)
    if not norm or len(norm.split()) > 4:
        return None
    lang = detect_language(text)
    bot  = bot_name or "your AI assistant"
    if norm in _GREET:
        tpl = _CANNED["greet"].get(lang)
        return tpl.format(bot=bot) if tpl else None
    for key, vocab in (("thanks", _THANKS), ("ack", _ACK), ("bye", _BYE)):
        if norm in vocab:
            return _CANNED[key].get(lang)   # unknown lang → None → AI handles
    return None
