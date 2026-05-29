"""
╔══════════════════════════════════════════════════════════════════╗
║          HEONIX ULTRA ENGINE v5.0 — GOD-MASTER LEVEL            ║
║    Zero-Bug • Crash-Proof • Async • Cached • Production-Grade    ║
╚══════════════════════════════════════════════════════════════════╝
"""

# ============================================================
# 📦 IMPORTS — ALL POWER TOOLS
# ============================================================
import os
import json
import time
import uuid
import logging
import hashlib
import sqlite3
import threading
import functools
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Optional, Dict, Any, Tuple

import requests
from flask import Flask, request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

# ============================================================
# 🪵 LOGGING SYSTEM — FULL VISIBILITY
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("heonix_engine.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("HEONIX")

# ============================================================
# ⚙️ CONFIGURATION — ENVIRONMENT-BASED (SECURE)
# ============================================================
class Config:
    MAKE_WEBHOOK_URL: str = os.getenv(
        "MAKE_WEBHOOK_URL",
        "https://hook.eu1.make.com/zo9a0e8yk8n95tkr9dog5hx7men5z9dx",
    )
    GENAI_API_KEY: str = os.getenv("GENAI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
    DATABASE_FILE: str = os.getenv("DATABASE_FILE", "heonix_ultra.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", uuid.uuid4().hex)
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.5          # seconds between retries
    CHAT_HISTORY_LIMIT: int = 20      # max turns kept in memory per session
    RATE_LIMIT_DEFAULT: str = "100 per minute"
    WEBHOOK_RATE_LIMIT: str = "30 per minute"
    CHAT_RATE_LIMIT: str = "60 per minute"
    PORT: int = int(os.getenv("PORT", 5000))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    GEMINI_MODEL: str = "gemini-1.5-flash"

cfg = Config()

# ============================================================
# 🛡️ GEMINI AI SETUP
# ============================================================
if cfg.GENAI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
    log.warning("⚠️  Gemini API key not set! Set GENAI_API_KEY env variable.")
else:
    genai.configure(api_key=cfg.GENAI_API_KEY)
    log.info("✅ Gemini AI configured successfully.")

# ============================================================
# 🗄️ SQLITE DATABASE ENGINE — PERSISTENT + THREAD-SAFE
# ============================================================
_db_lock = threading.Lock()

@contextmanager
def get_db():
    """Thread-safe SQLite connection context manager."""
    conn = sqlite3.connect(cfg.DATABASE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")   # Write-Ahead Logging — faster
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Create all tables if they don't exist — runs once on startup."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS customer_brains (
                customer_id     TEXT PRIMARY KEY,
                customer_name   TEXT NOT NULL,
                business_type   TEXT DEFAULT 'General',
                system_prompt   TEXT NOT NULL,
                created_at      TEXT NOT NULL,
                updated_at      TEXT NOT NULL,
                total_chats     INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id      TEXT PRIMARY KEY,
                customer_id     TEXT NOT NULL,
                created_at      TEXT NOT NULL,
                last_active     TEXT NOT NULL,
                message_count   INTEGER DEFAULT 0,
                FOREIGN KEY (customer_id) REFERENCES customer_brains(customer_id)
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id      TEXT NOT NULL,
                role            TEXT NOT NULL,
                content         TEXT NOT NULL,
                timestamp       TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
            );

            CREATE TABLE IF NOT EXISTS webhook_log (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                source_ip       TEXT,
                payload_hash    TEXT,
                customer_id     TEXT,
                status          TEXT,
                error_detail    TEXT,
                processed_at    TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_chat_messages_session
                ON chat_messages(session_id);
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_customer
                ON chat_sessions(customer_id);
        """)
    log.info("🗄️  Database initialized and ready.")

# ============================================================
# 🧠 IN-MEMORY CACHE — BLAZING FAST (TTL-BASED)
# ============================================================
class TTLCache:
    """Thread-safe in-memory cache with Time-To-Live expiration."""

    def __init__(self, default_ttl: int = 300):
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._ttl = default_ttl
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry and time.time() < entry[1]:
                return entry[0]
            if entry:
                del self._store[key]   # expired — evict
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self._lock:
            self._store[key] = (value, time.time() + (ttl or self._ttl))

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

brain_cache = TTLCache(default_ttl=600)       # 10-min cache for prompts
session_cache: Dict[str, Any] = {}            # active Gemini sessions

# ============================================================
# 💡 SMART PROMPT ENGINE — AUTO-DETECTS BUSINESS TYPE
# ============================================================
BUSINESS_TEMPLATES: Dict[str, Dict[str, str]] = {
    "real_estate": {
        "keywords": ["real estate", "property", "realty", "homes", "realtor"],
        "bot_name": "ARIA",
        "prompt": (
            "You are ARIA, an elite AI real estate closer for {name}. "
            "Your mission: qualify leads fast, build genuine rapport, and "
            "collect phone numbers by offering a FREE property valuation. "
            "Be concise, confident, and empathetic. Never be pushy. "
            "Always respond in the language the user writes in."
        ),
    },
    "fitness": {
        "keywords": ["gym", "fitness", "workout", "yoga", "crossfit", "sport"],
        "bot_name": "ROCKY",
        "prompt": (
            "You are ROCKY, a high-energy AI fitness coach for {name}. "
            "Your mission: inspire, motivate, and offer a 10% discount on the "
            "first month membership in exchange for the user's phone number. "
            "Keep energy HIGH. Use emojis sparingly for impact. "
            "Always respond in the language the user writes in."
        ),
    },
    "restaurant": {
        "keywords": ["restaurant", "food", "cafe", "dining", "cuisine", "eatery"],
        "bot_name": "CHEF",
        "prompt": (
            "You are CHEF, a charming AI host for {name}. "
            "Your mission: help customers explore the menu, make reservations, "
            "and collect phone numbers for exclusive deals and birthday offers. "
            "Be warm, welcoming, and mouth-wateringly descriptive. "
            "Always respond in the language the user writes in."
        ),
    },
    "ecommerce": {
        "keywords": ["shop", "store", "ecommerce", "products", "brand", "retail"],
        "bot_name": "NOVA",
        "prompt": (
            "You are NOVA, a sharp AI shopping assistant for {name}. "
            "Your mission: guide customers to the right products, handle objections, "
            "and collect contact info for exclusive early-access drops. "
            "Be trendy, knowledgeable, and customer-obsessed. "
            "Always respond in the language the user writes in."
        ),
    },
    "healthcare": {
        "keywords": ["clinic", "health", "doctor", "medical", "hospital", "dental"],
        "bot_name": "HELIO",
        "prompt": (
            "You are HELIO, a compassionate AI health assistant for {name}. "
            "Your mission: answer general health queries, help book appointments, "
            "and reassure patients with empathy. NEVER give medical diagnoses. "
            "Always recommend consulting a licensed doctor for serious concerns. "
            "Always respond in the language the user writes in."
        ),
    },
    "default": {
        "keywords": [],
        "bot_name": "ELITE",
        "prompt": (
            "You are ELITE, a professional AI business assistant for {name}. "
            "Your mission: understand the customer's needs, provide excellent support, "
            "and create a memorable experience that reflects the brand's quality. "
            "Be sharp, efficient, and solutions-focused. "
            "Always respond in the language the user writes in."
        ),
    },
}

def detect_business_type(business_type_str: str) -> str:
    """Detect the best template based on business description keywords."""
    lower = business_type_str.lower()
    for btype, data in BUSINESS_TEMPLATES.items():
        if btype == "default":
            continue
        if any(kw in lower for kw in data["keywords"]):
            return btype
    return "default"

def build_system_prompt(customer_name: str, business_type_str: str) -> Tuple[str, str]:
    """Returns (bot_name, full_system_prompt) for a given customer."""
    btype = detect_business_type(business_type_str)
    template = BUSINESS_TEMPLATES[btype]
    prompt = template["prompt"].format(name=customer_name)
    return template["bot_name"], prompt

# ============================================================
# 💾 DATABASE OPERATIONS — CLEAN CRUD LAYER
# ============================================================
def save_customer_brain(
    customer_id: str,
    customer_name: str,
    business_type: str,
    system_prompt: str,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _db_lock, get_db() as conn:
        conn.execute(
            """
            INSERT INTO customer_brains
                (customer_id, customer_name, business_type, system_prompt, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(customer_id) DO UPDATE SET
                customer_name  = excluded.customer_name,
                business_type  = excluded.business_type,
                system_prompt  = excluded.system_prompt,
                updated_at     = excluded.updated_at
            """,
            (customer_id, customer_name, business_type, system_prompt, now, now),
        )
    brain_cache.delete(customer_id)   # invalidate stale cache
    log.info(f"💾 Brain saved → {customer_id}")

def get_customer_brain(customer_id: str) -> Optional[Dict]:
    """Fetch brain from cache first, then DB (cache-aside pattern)."""
    cached = brain_cache.get(customer_id)
    if cached:
        return cached
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM customer_brains WHERE customer_id = ?", (customer_id,)
        ).fetchone()
    if row:
        data = dict(row)
        brain_cache.set(customer_id, data)
        return data
    return None

def create_session(customer_id: str) -> str:
    session_id = f"sess_{uuid.uuid4().hex[:16]}"
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chat_sessions (session_id, customer_id, created_at, last_active) VALUES (?,?,?,?)",
            (session_id, customer_id, now, now),
        )
    return session_id

def save_message(session_id: str, role: str, content: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chat_messages (session_id, role, content, timestamp) VALUES (?,?,?,?)",
            (session_id, role, content, now),
        )
        conn.execute(
            "UPDATE chat_sessions SET last_active=?, message_count=message_count+1 WHERE session_id=?",
            (now, session_id),
        )

def get_session_history(session_id: str) -> list:
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM chat_messages
            WHERE session_id=?
            ORDER BY id DESC LIMIT ?
            """,
            (session_id, cfg.CHAT_HISTORY_LIMIT),
        ).fetchall()
    return [{"role": r["role"], "parts": [r["content"]]} for r in reversed(rows)]

def log_webhook(source_ip, payload_hash, customer_id, status, error=None):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        conn.execute(
            "INSERT INTO webhook_log (source_ip, payload_hash, customer_id, status, error_detail, processed_at) VALUES (?,?,?,?,?,?)",
            (source_ip, payload_hash, customer_id, status, error, now),
        )

# ============================================================
# 🔁 RETRY DECORATOR — NEVER FAIL ON TRANSIENT ERRORS
# ============================================================
def with_retry(max_retries: int = 3, delay: float = 1.5, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    log.warning(f"⚠️  Attempt {attempt}/{max_retries} failed for {func.__name__}: {exc}")
                    if attempt < max_retries:
                        time.sleep(delay * attempt)   # exponential-ish back-off
            raise last_exc
        return wrapper
    return decorator

# ============================================================
# 🤖 GEMINI CHAT ENGINE — STATEFUL + RETRY
# ============================================================
@with_retry(max_retries=cfg.MAX_RETRIES, delay=cfg.RETRY_DELAY, exceptions=(GoogleAPIError, Exception))
def gemini_reply(system_prompt: str, history: list, user_message: str) -> str:
    """Send a message to Gemini with full history context. Returns reply text."""
    model = genai.GenerativeModel(
        model_name=cfg.GEMINI_MODEL,
        system_instruction=system_prompt,
    )
    chat = model.start_chat(history=history)
    response = chat.send_message(user_message)
    return response.text.strip()

# ============================================================
# 📡 MAKE.COM BACKUP — ASYNC-STYLE (NON-BLOCKING)
# ============================================================
def send_to_make_async(payload: dict) -> None:
    """Fire-and-forget backup to Make.com webhook in a background thread."""
    def _send():
        try:
            res = requests.post(cfg.MAKE_WEBHOOK_URL, json=payload, timeout=10)
            log.info(f"📤 Make.com backup: HTTP {res.status_code}")
        except Exception as exc:
            log.warning(f"⚠️  Make.com backup failed (non-critical): {exc}")
    threading.Thread(target=_send, daemon=True).start()

# ============================================================
# 🌐 FLASK APP + RATE LIMITER
# ============================================================
app = Flask(__name__)
app.config["SECRET_KEY"] = cfg.SECRET_KEY

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[cfg.RATE_LIMIT_DEFAULT],
    storage_uri="memory://",
)

# ============================================================
# 🛠️ HELPER — INPUT VALIDATOR
# ============================================================
def extract_field(fields: list, index: int, default: str = "") -> str:
    try:
        val = fields[index].get("value", default)
        return str(val).strip() if val else default
    except (IndexError, AttributeError):
        return default

def make_customer_id(name: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in name.upper())
    return f"HEONIX_{safe}"

# ============================================================
# 🚪 ROUTES
# ============================================================

# ── Health Check ──────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "UP",
        "engine": "HEONIX Ultra v5.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "db": cfg.DATABASE_FILE,
    }), 200


# ── Tally Webhook ─────────────────────────────────────────────
@app.route("/tally-webhook", methods=["POST", "GET"])
@limiter.limit(cfg.WEBHOOK_RATE_LIMIT)
def tally_webhook():
    if request.method == "GET":
        return "👑 HEONIX ULTRA ENGINE v5.0 IS LIVE AND RUNNING!", 200

    source_ip = request.remote_addr
    raw_body = request.get_data()
    payload_hash = hashlib.sha256(raw_body).hexdigest()[:16]

    tally_data = request.get_json(silent=True)
    if not tally_data:
        log_webhook(source_ip, payload_hash, None, "REJECTED", "Empty or invalid JSON")
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        # ── Step 1: Non-blocking backup ──────────────────────
        send_to_make_async(tally_data)

        # ── Step 2: Extract fields ───────────────────────────
        fields = tally_data.get("data", {}).get("fields", [])
        customer_name = extract_field(fields, 0, "Anonymous Client")
        business_type = extract_field(fields, 1, "General Business")
        extra_notes   = extract_field(fields, 2, "")

        customer_id = make_customer_id(customer_name)

        # ── Step 3: Build smart prompt ───────────────────────
        bot_name, system_prompt = build_system_prompt(customer_name, business_type)
        if extra_notes:
            system_prompt += f"\n\nAdditional context: {extra_notes}"

        # ── Step 4: Persist to DB ────────────────────────────
        save_customer_brain(customer_id, customer_name, business_type, system_prompt)

        # ── Step 5: Log success ──────────────────────────────
        log_webhook(source_ip, payload_hash, customer_id, "SUCCESS")
        log.info(f"🚀 Brain factory complete → {customer_id} | Bot: {bot_name}")

        return jsonify({
            "status": "success",
            "message": f"Brain deployed for {customer_name}",
            "customer_id": customer_id,
            "bot_name": bot_name,
            "business_type": business_type,
        }), 200

    except Exception as exc:
        log.error(f"❌ Webhook error: {exc}", exc_info=True)
        log_webhook(source_ip, payload_hash, None, "ERROR", str(exc))
        return jsonify({"error": "Processing failed", "detail": str(exc)}), 500


# ── Chat Endpoint ─────────────────────────────────────────────
@app.route("/chat", methods=["POST"])
@limiter.limit(cfg.CHAT_RATE_LIMIT)
def chat():
    """
    POST /chat
    Body: {
        "customer_id": "HEONIX_ACME_CORP",
        "session_id":  "sess_abc123",          ← optional; omit to start new session
        "message":     "Hello, I'm interested"
    }
    """
    data = request.get_json(silent=True) or {}

    customer_id = data.get("customer_id", "").strip()
    user_message = data.get("message", "").strip()
    session_id   = data.get("session_id", "").strip()

    # ── Validate ─────────────────────────────────────────────
    if not customer_id or not user_message:
        return jsonify({"error": "customer_id and message are required"}), 400
    if len(user_message) > 2000:
        return jsonify({"error": "Message too long (max 2000 chars)"}), 400

    # ── Load brain ───────────────────────────────────────────
    brain = get_customer_brain(customer_id)
    if not brain:
        return jsonify({"error": f"No brain found for customer_id: {customer_id}"}), 404

    # ── Session management ───────────────────────────────────
    if not session_id:
        session_id = create_session(customer_id)
        history = []
    else:
        history = get_session_history(session_id)

    # ── AI reply ─────────────────────────────────────────────
    try:
        reply = gemini_reply(
            system_prompt=brain["system_prompt"],
            history=history,
            user_message=user_message,
        )
    except Exception as exc:
        log.error(f"❌ Gemini error for {customer_id}: {exc}", exc_info=True)
        return jsonify({"error": "AI engine temporarily unavailable", "detail": str(exc)}), 503

    # ── Persist messages ─────────────────────────────────────
    save_message(session_id, "user", user_message)
    save_message(session_id, "model", reply)

    # ── Update chat counter ──────────────────────────────────
    with get_db() as conn:
        conn.execute(
            "UPDATE customer_brains SET total_chats=total_chats+1 WHERE customer_id=?",
            (customer_id,),
        )

    log.info(f"💬 Chat → {customer_id} | session: {session_id} | {len(reply)} chars reply")

    return jsonify({
        "status": "success",
        "session_id": session_id,
        "customer_id": customer_id,
        "reply": reply,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }), 200


# ── Admin: List all customers ─────────────────────────────────
@app.route("/admin/customers", methods=["GET"])
def list_customers():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT customer_id, customer_name, business_type, total_chats, updated_at FROM customer_brains ORDER BY updated_at DESC"
        ).fetchall()
    return jsonify({"customers": [dict(r) for r in rows], "count": len(rows)}), 200


# ── Admin: Customer stats ─────────────────────────────────────
@app.route("/admin/customer/<customer_id>", methods=["GET"])
def customer_stats(customer_id):
    brain = get_customer_brain(customer_id)
    if not brain:
        return jsonify({"error": "Not found"}), 404
    with get_db() as conn:
        sessions = conn.execute(
            "SELECT COUNT(*) as cnt FROM chat_sessions WHERE customer_id=?",
            (customer_id,),
        ).fetchone()["cnt"]
        messages = conn.execute(
            """SELECT COUNT(*) as cnt FROM chat_messages cm
               JOIN chat_sessions cs ON cm.session_id=cs.session_id
               WHERE cs.customer_id=?""",
            (customer_id,),
        ).fetchone()["cnt"]
    return jsonify({
        "customer_id": customer_id,
        "name": brain["customer_name"],
        "business_type": brain["business_type"],
        "total_sessions": sessions,
        "total_messages": messages,
        "total_chats": brain["total_chats"],
        "last_updated": brain["updated_at"],
    }), 200


# ── Admin: Delete customer ────────────────────────────────────
@app.route("/admin/customer/<customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    brain = get_customer_brain(customer_id)
    if not brain:
        return jsonify({"error": "Not found"}), 404
    with get_db() as conn:
        conn.execute("DELETE FROM customer_brains WHERE customer_id=?", (customer_id,))
    brain_cache.delete(customer_id)
    log.info(f"🗑️  Deleted brain → {customer_id}")
    return jsonify({"status": "deleted", "customer_id": customer_id}), 200


# ── Error Handlers ────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found", "hint": "Check /health for status"}), 404

@app.errorhandler(429)
def rate_limited(e):
    return jsonify({"error": "Too many requests. Please slow down."}), 429

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ============================================================
# 🚀 STARTUP
# ============================================================
def startup():
    log.info("=" * 64)
    log.info("  👑  HEONIX ULTRA ENGINE v5.0 — STARTING UP")
    log.info("=" * 64)
    init_db()
    log.info(f"🌐 Server will run on port {cfg.PORT}")
    log.info(f"📦 Gemini model: {cfg.GEMINI_MODEL}")
    log.info(f"🗄️  Database: {cfg.DATABASE_FILE}")
    log.info(f"🛡️  Rate limit (webhook): {cfg.WEBHOOK_RATE_LIMIT}")
    log.info(f"💬 Rate limit (chat):    {cfg.CHAT_RATE_LIMIT}")
    log.info("=" * 64)

if __name__ == "__main__":
    startup()
    app.run(
        host="0.0.0.0",
        port=cfg.PORT,
        debug=cfg.DEBUG,
        threaded=True,        # handle concurrent requests properly
        use_reloader=False,   # avoid double-startup in debug mode
    )
