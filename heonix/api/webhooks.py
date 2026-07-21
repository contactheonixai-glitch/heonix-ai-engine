"""HEONIX GEN-5 · module `heonix.api.webhooks`
Verbatim slice of heonix_ultra_engine_v16_gen6.py (lines 9035-10223).
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

from heonix.ai.pipeline import (ai_reply_pipeline, govern_message)
from heonix.analytics import (analytics)
from heonix.api.app import (app, elapsed_ms, limiter)
from heonix.api.helpers import (
    extract_by_label,
    find_legacy_brain_id_by_phone,
    make_customer_id,
)
from heonix.api.validators import (ChatRequestValidator, WebhookPayloadValidator)
from heonix.booking.engine import (_OPT_OUT_KEYWORDS, handle_booking)
from heonix.cache import (brain_cache, customer_limiter)
from heonix.channels.instagram import (send_instagram_sync)
from heonix.channels.whatsapp import (send_owner_alert_async, send_whatsapp_sync)
from heonix.classify import (_brain_is_health, build_system_prompt, ghost_is_muted, ghost_mute)
from heonix.concurrency import (submit_bg, submit_ordered)
from heonix.config import (cfg)
from heonix.crm import (
    _extract_phone_like,
    crm_add_contact,
    crm_attach_phone,
    crm_remap_user_id,
)
from heonix.db.core import (PostgreSQLPool, _column_exists, _db_true, _execute, audit)
from heonix.db.store import (
    _find_session_by_subject,
    _wa_touch_window,
    brain_ig_creds,
    brain_wa_creds,
    check_idempotency,
    create_session,
    get_brain_by_ig_id,
    get_brain_by_wa_phone_id,
    get_customer_brain,
    get_session_history,
    increment_chat_count,
    log_webhook,
    opt_out_subject,
    outbox_publish,
    save_customer_brain,
    save_messages_batch,
    session_exists,
    store_idempotency,
)
from heonix.i18n import (_norm_text, _t, _user_lang)
from heonix.logsetup import (log)
from heonix.media import (transcribe_audio_url, transcribe_voice_note, understand_image_media)
from heonix.privacy import (_find_subject_rows)
from heonix.security.auth import (_safe_ct_eq, verify_meta_signature, verify_tally_signature)
from heonix.security.crypto import (_crm_phone_hash, _is_bsuid, _normalize_msisdn, pii_vault)
from heonix import _latebind  # GEN-5 SPLIT
_db_pool: Any = None   # GEN-5 SPLIT: late-bound; published by heonix.db.core at startup
_latebind.register('_db_pool', __name__)



# ── Tally Webhook ──────────────────────────────────────────────────────────────
@app.route("/tally-webhook", methods=["POST", "GET"])
@limiter.limit(cfg.WEBHOOK_RATE_LIMIT)
def tally_webhook():
    if request.method == "GET":
        return jsonify({
            "status":  "live",
            "engine":  "HEONIX",   # v16g4 FIX L7: no version recon for scanners
            "message": "POST Tally form payload here to deploy a customer brain.",
        }), 200

    source_ip    = request.remote_addr
    raw_body     = request.get_data()
    payload_hash = hashlib.sha256(raw_body).hexdigest()[:24]

    # Tally signature verification (FIX #14)
    # v16g5 FIX R5-C2 (LAUNCH-CRITICAL): this used to pass
    # `dict(request.headers)`, which THROWS AWAY Werkzeug's case-insensitive
    # lookup and preserves whatever casing arrived on the wire. Only two exact
    # spellings were probed, so a header delivered as "Tally-signature" or
    # "TALLY-SIGNATURE" matched neither → compare_digest("", sig) → 401 on
    # every legitimate onboarding. That is v15 FIX 3 resurrected through a
    # different door: the day TALLY_WEBHOOK_SECRET is set, signups die
    # silently. Pass the header object itself.
    if not verify_tally_signature(raw_body, request.headers):
        analytics.inc("webhook.tally.sig_fail")
        return jsonify({"error": "Invalid webhook signature"}), 401

    cached = check_idempotency(payload_hash)
    if cached:
        log.info(f"♻️  Duplicate webhook → {payload_hash}")
        return jsonify(cached), 200

    # v15 FIX 16 (MEDIUM): SELECT-then-INSERT idempotency is racy — two
    # simultaneous identical deliveries both passed the check above and both
    # ran the full flow (double welcome message via the outbox). Claim the
    # payload atomically; the loser answers 200 so Tally never retries it.
    if not brain_cache.setnx(f"tallylock:{payload_hash}", ttl=120):
        analytics.inc("webhook.tally.dup_inflight")
        return jsonify({"status": "duplicate_in_flight",
                        "payload_hash": payload_hash}), 200

    tally_data = request.get_json(silent=True)
    if not tally_data:
        # v15g2 FIX H1: release the claim on failure (v14g3 BUG 13 discipline).
        brain_cache.delete(f"tallylock:{payload_hash}")
        log_webhook(source_ip, payload_hash, None, "REJECTED", error="Empty JSON")
        return jsonify({"error": "Invalid JSON payload"}), 400

    try:
        fields = tally_data.get("data", {}).get("fields", [])
        # v15g4 FIX B6: candidates are MORE-SPECIFIC-FIRST — the generic kw
        # "name" matched an "Owner Name" field before "Business Name" (form
        # order decided the winner), onboarding the clinic under the owner's
        # personal name. Phone slots additionally demand ≥7 digits so a
        # checkbox like "Do you use WhatsApp?" ("Yes") can't become a number.
        raw    = WebhookPayloadValidator(
            customer_name  = extract_by_label(
                fields, ("business name", "clinic name", "company name",
                         "clinic", "business", "name"), 0, "Anonymous Client"),
            business_type  = extract_by_label(
                fields, ("business type", "type", "industry", "category",
                         "vertical"), 1, "General Business"),
            extra_notes    = extract_by_label(
                fields, ("note", "detail", "message", "anything else"), 2, ""),
            whatsapp_phone = extract_by_label(
                fields, ("whatsapp number", "wa number", "business number",
                         "business phone", "whatsapp"), 3, "",
                require_digits=7),                              # v15g4 FIX B6
            owner_phone    = extract_by_label(
                fields, ("owner number", "owner phone", "your phone",
                         "contact number", "personal", "owner"), 4, "",
                require_digits=7),                              # v15g4 FIX B6
            instagram_id   = extract_by_label(
                fields, ("instagram", "insta", "ig handle", "ig id"), 5, ""),
        )
        # v15g4 FIX B5: canonicalise the phones ONCE at intake. The raw form
        # value ("+91 98765 43210", with spaces) was used verbatim as the
        # welcome-message send target AND the identity seed — Meta rejects
        # malformed 'to' values and the id seed drifted per formatting.
        # Garbage that survives the digit guard is dropped LOUDLY here.
        wa_phone  = _normalize_msisdn(raw.whatsapp_phone)
        own_phone = _normalize_msisdn(raw.owner_phone)
        if raw.whatsapp_phone and not wa_phone:
            log.warning(f"⚠️  Tally: whatsapp_phone {raw.whatsapp_phone!r} is not "
                        "a usable number — onboarding WITHOUT a welcome target.")
        if raw.owner_phone and not own_phone:
            log.warning(f"⚠️  Tally: owner_phone {raw.owner_phone!r} is not a "
                        "usable number — owner alerts will fall back.")
        # v14 BUG 41: stable, phone-derived id (no more orphaning on name edits).
        # First honour any pre-v14 brain that already owns this number, so an old
        # name-based clinic keeps its id; otherwise mint the stable phone-based id.
        customer_id = (find_legacy_brain_id_by_phone(wa_phone or raw.whatsapp_phone)
                       or make_customer_id(raw.customer_name,
                                           wa_phone, own_phone))

        # v16g4 FIX L19: a Tally RE-SUBMIT for a soft-deleted clinic used to
        # flip is_active back to TRUE via the upsert — but its routing keys and
        # tokens were deliberately blanked at delete time, so the clinic looked
        # alive while actually dark, and no log said why. A deliberate delete
        # now requires a deliberate re-activation (delete the row or use the
        # admin API); the form re-submit is acknowledged (200 so Tally never
        # retries) but does NOT resurrect.
        try:
            with _db_pool.get(read_only=True) as conn:
                _cur = _execute(conn, "SELECT is_active FROM customer_brains "
                                      "WHERE customer_id=?", (customer_id,))
                _row = _cur.fetchone()
            _was_deleted = (_row is not None and not (
                _row[0] if isinstance(_row, tuple) else _row["is_active"]))
        except Exception:
            _was_deleted = False
        if _was_deleted:
            brain_cache.delete(f"tallylock:{payload_hash}")
            log.warning(f"⚠️  Tally re-submit for SOFT-DELETED clinic "
                        f"{customer_id} — reactivation blocked (v16g4 FIX L19). "
                        f"Re-activate via the admin API if intended.")
            log_webhook(source_ip, payload_hash, customer_id,
                        "REACTIVATION_BLOCKED")
            analytics.inc("webhook.tally.reactivation_blocked")
            return jsonify({"status": "reactivation_blocked",
                            "customer_id": customer_id,
                            "detail": "This clinic was deactivated; re-submit "
                                      "does not reactivate it."}), 200
        bot_name, sys_prompt = build_system_prompt(raw.customer_name, raw.business_type)
        if raw.extra_notes:
            sys_prompt += f"\n\nAdditional context: {raw.extra_notes}"

        # v16g5 FIX R5-C1 (LAUNCH-CRITICAL): owner_phone used to fall back to
        # `wa_phone` — the clinic's own WABA line. FIX H1 already established
        # that a WABA line CANNOT message itself (that is why the welcome
        # refuses that target), but the same number was still persisted as the
        # owner's, and owner_phone is the destination for every EMERGENCY
        # escalation (send_owner_alert_async). Result: every "chest pain",
        # "bleeding", "I need a doctor now" alert was addressed to the line
        # that generated it and silently rejected by Meta. An UNSET owner
        # phone that screams at boot beats a set one that black-holes.
        _owner_for_brain = own_phone
        if _owner_for_brain and _owner_for_brain == wa_phone:
            log.critical(f"🛑 Tally: owner phone == WABA line for {customer_id} "
                         f"— storing NO owner phone. EMERGENCY OWNER ALERTS "
                         f"ARE DISABLED for this clinic until a distinct "
                         f"owner number is attached (v16g5 FIX R5-C1).")
            analytics.inc("onboard.owner_phone_is_waba")
            _owner_for_brain = ""
        elif not _owner_for_brain:
            log.critical(f"🛑 Tally: NO owner phone for {customer_id} — "
                         f"emergency owner alerts are DISABLED until one is "
                         f"attached via /admin/customer/<id>/channel.")
            analytics.inc("onboard.owner_phone_missing")
        save_customer_brain(customer_id, raw.customer_name,
                            raw.business_type, sys_prompt, wa_phone,   # v15g4 FIX B5
                            owner_phone=_owner_for_brain,
                            instagram_id=raw.instagram_id,
                            bot_name=bot_name)

        # Publish welcome message via transactional outbox (FIX #3).
        # v14g3 BUG 9: carry customer_id so the sender can use this clinic's creds.
        # v16g4 FIX H1: this welcome is BUSINESS-INITIATED to a number that has
        # never messaged us — free text with no open 24h session is rejected by
        # Meta 100% of the time (131047-class), so every new clinic's first
        # experience was 5 burned attempts → dead-letter. It now goes via the
        # approved WELCOME_TEMPLATE, and to the OWNER's phone — the old target
        # was wa_phone, often the WABA line itself, which can't receive from
        # itself. No template configured / no distinct owner number → the send
        # is SKIPPED with a loud log instead of burned.
        # v16g6 FIX R6-L4: the equality re-check that used to sit here was
        # unreachable — R5-C1 already blanks _owner_for_brain for exactly
        # that condition a few lines up. Dead code removed.
        _welcome_to = _owner_for_brain
        if _welcome_to and cfg.WELCOME_TEMPLATE:
            outbox_publish("whatsapp.template", {
                "to":          _welcome_to,
                "customer_id": customer_id,
                "template":    cfg.WELCOME_TEMPLATE,
                "lang":        cfg.WELCOME_TEMPLATE_LANG,
                "body_param":  (f"Your AI assistant {bot_name} is live for "
                                f"{raw.customer_name}. Customer ID: "
                                f"{customer_id}"),
            })
        elif _welcome_to:
            log.warning(f"⚠️  Welcome for {customer_id} SKIPPED — "
                        f"WELCOME_TEMPLATE is not set and a business-initiated "
                        f"free text cannot be delivered (v16g4 FIX H1). "
                        f"Approve a welcome template in Meta Business Manager "
                        f"and set WELCOME_TEMPLATE.")
        else:
            # v16g5 FIX R5-M12: the no-owner-number case fell off the end of
            # this if/elif with ZERO output — onboarding completed, no welcome
            # was ever sent, and nothing said why.
            log.warning(f"⚠️  Welcome for {customer_id} SKIPPED — no usable "
                        f"owner number on the form (a WABA line cannot message "
                        f"itself). Collect a distinct owner mobile.")
            analytics.inc("onboard.welcome_skipped_no_target")

        log_webhook(source_ip, payload_hash, customer_id, "SUCCESS")
        actor = g.jwt_user["sub"] if hasattr(g, "jwt_user") else "webhook"
        audit(actor, "customer.deploy", customer_id,
              {"bot": bot_name, "type": raw.business_type}, source_ip)

        response_body = {
            "status":        "success",
            "message":       f"Brain deployed for {raw.customer_name}",
            "customer_id":   customer_id,
            "bot_name":      bot_name,
            "business_type": raw.business_type,
            "region":        cfg.REGION,
            "request_id":    g.get("request_id"),
            "elapsed_ms":    elapsed_ms(),
        }
        if not store_idempotency(payload_hash, response_body):  # v15g4 FIX C7
            log.critical(f"🛑 idempotency NOT stored for Tally {payload_hash[:12]} — "
                         "a retry after the 120s claim lock will REPLAY this "
                         "onboarding (duplicate welcome message).")
        analytics.inc("webhook.tally.success")
        log.info(f"🚀 Brain deployed → {customer_id} bot={bot_name}")
        return jsonify(response_body), 200

    except ValidationError as exc:
        # v15g2 FIX H1 (HIGH): the atomic tallylock claim (FIX 16) was never
        # released on failure. Sequence of the bug: attempt 1 errors → 500 →
        # Tally retries within the 120s lock TTL → setnx loses → we answered
        # 200 "duplicate_in_flight" → Tally marks it DELIVERED and never
        # retries again → the clinic that just signed up is silently lost
        # forever. Release the claim on every non-success path so the retry
        # actually re-runs the flow (same discipline as v14g3 BUG 13).
        brain_cache.delete(f"tallylock:{payload_hash}")
        log_webhook(source_ip, payload_hash, None, "VALIDATION_ERROR", error=str(exc))
        return jsonify({"error": "Validation failed", "detail": exc.errors()}), 422
    except Exception as exc:
        brain_cache.delete(f"tallylock:{payload_hash}")   # v15g2 FIX H1
        log.error(f"❌ Webhook error: {exc}", exc_info=True)
        analytics.inc("webhook.tally.error")
        log_webhook(source_ip, payload_hash, None, "ERROR", error=str(exc))
        return jsonify({"error": "Processing failed", "request_id": g.get("request_id")}), 500


# ── WhatsApp Cloud API Webhook ─────────────────────────────────────────────────
# v11 fix #1: the route now ONLY validates + dedups + queues, then 200s Meta
# instantly. All heavy work (DB, AI, voice, sends) runs in the bounded worker
# pool. Previously everything was synchronous → a slow AI/voice call (20-40s)
# blocked the worker, Meta timed out at ~10s and re-sent, and 8 gunicorn slots
# could starve under light load.
# v11 fix #7: loops over EVERY entry / change / message (Meta can batch them);
# v10 processed only entry[0]/changes[0]/messages[0] and silently dropped rest.
def _resolve_inbound_brain(phone_number_id: str, from_phone: str) -> Optional[str]:
    """
    v12 #13/#16: figure out WHICH clinic an inbound WhatsApp message belongs to.

    v11 matched `whatsapp_phone == from_phone` — i.e. it compared the brain's
    stored number against the *patient's* number, so real patient messages never
    matched and silently dropped. The correct key is Meta's phone_number_id (the
    business line the patient texted), which Meta puts in value.metadata.

    Resolution order (backward compatible, single-tenant friendly):
      1. brain whose wa_phone_number_id == the webhook's phone_number_id
         (v15g2 FIX L12: docstring previously still described the dead
         whatsapp_phone == phone_number_id mapping that v14g3 BUG 4 removed)
      2. if exactly ONE active brain exists, use it      (the common 1-clinic case)
      3. otherwise None  (ambiguous — cannot safely route)

    Full multi-tenant routing (per-clinic creds, many lines) is deferred to
    tenant #2; this just makes sure replies actually reach the patient today.
    """
    # 1) explicit routing: the Meta phone_number_id → the owning brain.
    # v14g3 BUG 4: the old query compared whatsapp_phone (a phone NUMBER) against
    # phone_number_id (a Meta numeric ID) — they can NEVER be equal, so this path
    # was dead code and every inbound fell straight through to the single-brain
    # guess below. The correct routing column is wa_phone_number_id (attached via
    # POST /admin/customer/<id>/channel), so this resolver is now correct on its
    # own even when get_brain_by_wa_phone_id wasn't consulted first.
    if phone_number_id:
        ckey = f"wa_route:{phone_number_id}"
        cached = brain_cache.get(ckey)
        if cached:
            return cached if cached != "__none__" else None
        try:
            with _db_pool.get(read_only=True) as conn:
                if _column_exists(conn, "customer_brains", "wa_phone_number_id"):
                    cur = _execute(conn,
                        "SELECT customer_id FROM customer_brains "
                        "WHERE wa_phone_number_id=? AND is_active=?",
                        (phone_number_id, _db_true()))
                    row = cur.fetchone()
                    if row:
                        cid = row["customer_id"]
                        brain_cache.set(ckey, cid, ttl=600)
                        return cid
                    # v16g5 FIX R5-L2: only HITS were cached here, so the
                    # "__none__" branch read above was dead code for this path
                    # and every unroutable inbound cost a fresh DB round-trip
                    # on a PUBLIC webhook — a free amplifier for anyone
                    # spraying unknown phone_number_ids. Cache the miss too
                    # (short TTL so attaching a number still goes live fast).
                    brain_cache.set(ckey, "__none__", ttl=60)
        except Exception as exc:
            log.warning(f"⚠️  inbound route lookup failed: {exc}")

    # 2) single-tenant fallback — exactly one active brain (cached briefly).
    # v14g5 FIX 10: gated behind SINGLE_TENANT_FALLBACK. This is a convenience for a
    # pre-v13 single-clinic setup; in a real multi-tenant deployment it can mis-route
    # an unknown number to the only clinic, so it can be turned off.
    if not cfg.SINGLE_TENANT_FALLBACK:
        return None
    try:
        single = brain_cache.get("wa_route:__single__")
        if single:
            return single if single != "__none__" else None
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT customer_id FROM customer_brains WHERE is_active=? LIMIT 2",
                (_db_true(),))
            rows = cur.fetchall()
        if len(rows) == 1:
            cid = rows[0]["customer_id"]
            brain_cache.set("wa_route:__single__", cid, ttl=120)
            # If a business number actually arrived but didn't match a brain above,
            # routing fell through to the single-tenant guess — surface that loudly.
            if phone_number_id:
                log.warning(f"⚠️  WA single-tenant fallback used for pnid={phone_number_id} "
                            f"→ {cid}. Attach this number via /admin to enable true routing.")
            return cid
        # 0 or >1 active brains → ambiguous, cache the miss briefly
        brain_cache.set("wa_route:__single__", "__none__", ttl=60)
    except Exception as exc:
        log.warning(f"⚠️  single-brain fallback failed: {exc}")
    return None


def _handle_wa_user_id_update(phone_number_id: str, from_id: str,
                              sys_payload: dict) -> None:
    """v16 U5: background worker for the user_id_update system event. Field
    names are read tolerantly (Meta's classic user_changed_number used
    system.new_wa_id; the BSUID-era event documents old→new user IDs)."""
    try:
        old_id = (sys_payload.get("old_user_id") or from_id or "").strip()
        new_id = (sys_payload.get("new_user_id") or sys_payload.get("user_id")
                  or sys_payload.get("new_wa_id") or sys_payload.get("wa_id")
                  or "").strip()
        if not (old_id and new_id) or old_id == new_id:
            return
        brain = get_brain_by_wa_phone_id(phone_number_id)
        if not brain:
            _cid  = _resolve_inbound_brain(phone_number_id, old_id)
            brain = get_customer_brain(_cid) if _cid else None
        if not brain:
            log.info(f"🆔 user_id_update unroutable (pnid={phone_number_id or 'none'})")
            return
        crm_remap_user_id(brain["customer_id"], old_id, new_id)
    except Exception as exc:
        log.warning(f"⚠️  user_id_update handler failed: {exc}")


def _ensure_wa_session(customer_id: str, from_phone: str) -> str:
    """v16g2 FIX N8: session resolve/create shared by the main flow AND the U3
    capture paths, so captured-number turns can be persisted like every other
    exchange (persist-then-send discipline, v14g5 FIX 50)."""
    skey  = f"wa_session:{customer_id}:{from_phone}"
    shash = _crm_phone_hash(customer_id, from_phone)
    session_id = brain_cache.get(skey)
    if not session_id:
        # v15g2 FIX M3: resume from the DB before minting a fresh session.
        session_id = (_find_session_by_subject(customer_id, shash)
                      or create_session(customer_id, channel="whatsapp",
                                        subject_hash=shash))
    # v15g2 FIX M3: SLIDING TTL — refreshed on every message. It was set only
    # at creation, so an ACTIVE chat lost all AI context at exactly 60 min.
    brain_cache.set(skey, session_id, ttl=3600)
    return session_id


def _release_wamid(msg: dict) -> None:
    """v16g4 FIX H6: the wamid dedupe claim is taken in the WEBHOOK, but only
    the backlog-full path released it on failure. When the WORKER then bailed
    (unroutable, rate-limited, crash), the claim stood for DEDUPE_TTL and
    Meta's automatic redelivery was deduped away — permanent message loss on
    what were transient conditions. Release wherever the message was NOT
    actually handled. Deliberately NOT released where the turn WAS consumed
    (ghost-mute takeover, empty text, transcription failure that already sent
    the patient a reply) — a redelivery there would double-message."""
    _id = (msg or {}).get("id", "")
    if _id:
        try:
            brain_cache.delete(f"wamid:{_id}")
        except Exception:
            pass


def _process_wa_message(from_phone: str, msg: dict, phone_number_id: str = "",
                        profile_name: str = "", wa_user_id: str = "") -> None:
    """Heavy per-message handler — runs in the background pool, fully outside
    any Flask request context.
    v13: routes by the BUSINESS number that received the message
    (phone_number_id) → the owning clinic, and replies from THAT clinic's own
    number+token. Falls back to the v12 single-tenant resolver for pre-v13 setups
    so your first clinic keeps working with zero config.
    v16 U1/U2: from_phone is an OPAQUE chat identifier — a phone number for
    classic contacts, a BSUID (CC.alphanum) for username patients. Nothing in
    this handler may assume it is E.164. wa_user_id carries the BSUID that
    Meta now includes on every message webhook."""
    try:
        msg_type = msg.get("type", "text")

        # ── v13 routing: which clinic owns the number the patient texted? ──
        brain = get_brain_by_wa_phone_id(phone_number_id)
        if not brain:
            # backward-compat: v12 resolver (explicit phone map OR single active brain)
            _cid  = _resolve_inbound_brain(phone_number_id, from_phone)
            brain = get_customer_brain(_cid) if _cid else None
        if not brain:
            log.info(f"📲 Unroutable WA msg (pnid={phone_number_id or 'none'}, "
                     f"from={pii_vault.mask(from_phone)}) — no matching active brain")
            analytics.inc("whatsapp.unroutable")
            _release_wamid(msg)   # v16g4 FIX H6: retry works once routing is fixed
            return

        customer_id      = brain["customer_id"]
        out_pid, out_tok = brain_wa_creds(brain)   # ← this clinic's own creds

        # v15 FIX 11 (MEDIUM): scope the webhook limiter per CONVERSATION
        # (clinic + patient). The old clinic-wide bucket meant ALL patients of
        # one busy clinic shared 60/min — morning rush = legit messages
        # silently vanishing. Per-conversation still stops the actual abuse
        # case (one number flooding), and drops are now LOGGED, not invisible.
        if not customer_limiter.check(f"{customer_id}:{from_phone}"):
            analytics.inc("ratelimit.customer.hit")
            log.warning(f"🚦 rate-limited WA msg dropped cust={customer_id} "
                        f"from={pii_vault.mask(from_phone)}")
            _release_wamid(msg)   # v16g4 FIX H6: dropped ≠ handled
            return

        # #13: scope ghost-mute + session per (customer, patient) so one patient
        # texting two clinics is two independent conversations.
        guid = f"{customer_id}:{from_phone}"
        # v16g5 FIX R5-H1: an inbound message is what opens WhatsApp's 24-hour
        # customer-service window — record it so the reminder path can tell
        # whether free text is deliverable at all.
        _wa_touch_window(customer_id, from_phone)
        if ghost_is_muted(guid):                 # human owner has taken over
            analytics.inc("ghost.skipped")
            return

        if msg_type == "text":
            user_text = msg.get("text", {}).get("body", "").strip()
            if not user_text:
                return
            # #40: bound text before any regex / classification work
            if len(user_text) > cfg.MAX_MESSAGE_LEN:
                user_text = user_text[:cfg.MAX_MESSAGE_LEN]
        elif msg_type == "audio":
            user_text = transcribe_voice_note(msg.get("audio", {}).get("id", ""), out_tok)
            if not user_text:
                send_whatsapp_sync(from_phone,                    # v16g5 R5-M2
                    _t("audio_unclear", _user_lang(customer_id, from_phone)),
                    out_pid, out_tok, customer_id)  # v14: ordered reply
                return
            analytics.inc("voice.transcribed")
        elif msg_type == "image" and cfg.ENABLE_IMAGE_UNDERSTANDING:
            # v14g4: actually LOOK at the image with Gemini, then fall through to
            # the normal pipeline so the bot answers in the clinic's own persona.
            caption = (msg.get("image", {}).get("caption") or "").strip()
            desc    = understand_image_media(msg.get("image", {}).get("id", ""), out_tok)
            if not desc:
                send_whatsapp_sync(from_phone,                    # v16g5 R5-M2
                    _t("image_unreadable", _user_lang(customer_id, from_phone)),
                    out_pid, out_tok, customer_id)
                analytics.inc("whatsapp.image_unreadable")
                return
            analytics.inc("image.understood")
            user_text = ((caption + "\n\n") if caption else "") + \
                        f"[The customer sent an image. It appears to show: {desc}]"
            if len(user_text) > cfg.MAX_MESSAGE_LEN:
                user_text = user_text[:cfg.MAX_MESSAGE_LEN]
        elif msg_type == "interactive":
            # v14g4: a tapped reply-button / list-row arrives here.
            # v16g3 FIX R3-L7: history used to persist the bare machine id
            # ('slot:1753…'), polluting the AI's context. Persist
            # 'Title [id]' — the booking matchers key off the id by
            # substring, the AI reads the title.
            inter = msg.get("interactive", {})
            br    = inter.get("button_reply") or inter.get("list_reply") or {}
            _tid  = (br.get("id") or "").strip()
            _ttl  = (br.get("title") or "").strip()
            user_text = (f"{_ttl} [{_tid}]"
                         if (_tid and _ttl and _tid != _ttl)
                         else (_tid or _ttl))
            if not user_text:
                return
        elif msg_type == "button":
            # v15g2 FIX L11: TEMPLATE quick-reply taps arrive as type 'button'
            # (msg.button.text / .payload) — a different shape from 'interactive'
            # — and were silently dropped by the final else. A future template
            # like "Reply YES to confirm" would have gone nowhere.
            _btn = msg.get("button", {}) or {}
            user_text = ((_btn.get("text") or _btn.get("payload") or "")).strip()
            if not user_text:
                return
        elif msg_type == "contacts":
            # v16 U3: this is how the shared number ARRIVES — a tap on the
            # phone-number-request button (or a shared contact card) delivers
            # a `contacts`-type message carrying the phone.
            # v16g2 FIX H1: the branch is GATED — it runs only for a BSUID
            # patient we actually ASKED (`numreq_asked` live). A classic
            # phone-identified patient forwarding "here's my friend's dentist,
            # try him" no longer overwrites their OWN CRM number with a third
            # party's (cold-lead follow-ups to a non-consenting stranger is a
            # DPDP problem, not just a data one); it falls through to the
            # generic media acknowledgement instead.
            if not (_is_bsuid(from_phone) and brain_cache.get(
                    f"numreq_asked:{customer_id}:{from_phone}")):
                send_whatsapp_sync(from_phone,                    # v16g5 R5-M2
                    _t("contact_ack", _user_lang(customer_id, from_phone)),
                    out_pid, out_tok, customer_id)
                analytics.inc("whatsapp.media_ack")
                return
            _shared = ""
            try:
                for c in (msg.get("contacts") or []):
                    for p in (c.get("phones") or []):
                        _shared = (p.get("phone") or p.get("wa_id") or "").strip()
                        if _shared:
                            break
                    if _shared:
                        break
            except Exception:
                _shared = ""
            digits = _normalize_msisdn(_shared)              # v16g2 FIX N2
            session_id = _ensure_wa_session(customer_id, from_phone)  # FIX N8
            _in_window = bool(brain_cache.get(
                f"numreq_window:{customer_id}:{from_phone}"))
            if not _in_window:
                # v16g3 FIX R3-M3: FIX H1 gated classic patients, but a BSUID
                # patient forwarding a FRIEND's card anywhere inside the 7-day
                # numreq_asked window still had the friend's number written as
                # THEIR phone — and cold-lead nudges could then message a
                # non-consenting stranger. Outside the 15-min ask window a
                # card is as likely a referral as a self-share: never
                # auto-attach; ask them to TYPE their own number, which
                # re-opens the typed-capture window.
                # v16g4 FIX M9: the re-opened window is marked "strict" — it
                # was opened by a FORWARDED CARD, not by our own ask, so the
                # very next typed message is as likely "call my brother
                # 98765…" as a self-share. Strict mode accepts only a bare
                # number (see typed-capture below).
                brain_cache.set(f"numreq_window:{customer_id}:{from_phone}",
                                "strict", ttl=900)
                _confirm = _t("card_deferred",
                              _user_lang(customer_id, from_phone))   # v16g4 FIX M8
                analytics.inc("whatsapp.contact_card_deferred")
            elif digits and len(digits) >= 10 and crm_attach_phone(
                    customer_id, from_phone, digits):
                brain_cache.delete(f"numreq_window:{customer_id}:{from_phone}")
                brain_cache.delete(f"numreq_asked:{customer_id}:{from_phone}")
                _lgc = _user_lang(customer_id, from_phone)   # v16g4 FIX M8
                _confirm = _t("phone_saved_reminders" if cfg.ENABLE_SCHEDULER
                              else "phone_saved_records",     # v16g2 FIX C8
                              _lgc, masked=pii_vault.mask(digits))
                analytics.inc("whatsapp.phone_shared")
            else:
                _confirm = _t("card_unreadable",
                              _user_lang(customer_id, from_phone))   # v16g4 FIX M8
            save_messages_batch(session_id, [                # v16g2 FIX N8
                ("user",  "[shared a contact card]", "whatsapp", 0),
                ("model", _confirm,                  "local",    0)])
            increment_chat_count(customer_id)
            send_whatsapp_sync(from_phone, _confirm, out_pid, out_tok, customer_id)
            return
        elif msg_type == "location":
            # v16g4 port (audit item 101): fell through to the generic 'else'
            # and was silently dropped — a patient sharing their location
            # (home-visit address, "come find me here") got no reply at all.
            loc  = msg.get("location", {}) or {}
            lat, lng = loc.get("latitude"), loc.get("longitude")
            log.info(f"📍 WA location from {pii_vault.mask(from_phone)}: "
                     f"({lat}, {lng})")
            send_whatsapp_sync(from_phone,
                _t("location_ack", _user_lang(customer_id, from_phone)),
                out_pid, out_tok, customer_id)
            analytics.inc("whatsapp.location_ack")
            return
        elif msg_type in ("image", "document", "video", "sticker"):
            # #16: acknowledge media instead of silently black-holing it
            send_whatsapp_sync(from_phone,                        # v16g5 R5-M2
                _t("media_ack", _user_lang(customer_id, from_phone)),
                out_pid, out_tok, customer_id)  # v14: ordered reply
            analytics.inc("whatsapp.media_ack")
            return
        else:
            return

        session_id = _ensure_wa_session(customer_id, from_phone)  # v16g2 FIX N8

        # (v16g2 FIX H2: the typed-number capture block that lived here — BEFORE
        # govern_message — moved BELOW the routing gate. "Accident! please call
        # my son 9876543210" was being consumed as a phone share: cheery ✅,
        # no emergency route, no owner alert, question never answered — the
        # exact priority-inversion class A3/A4 existed to kill.)

        # v15g4 FIX A2/A5: HELIO clinics get the strict emergency list and no
        # VIP-₹ alert spam. Healthcare is detected from the assigned persona
        # (HELIO) with the business-type template as fallback.
        _is_health = _brain_is_health(brain)   # v16g4 FIX P3: cached per brain version
        # v15g4 FIX A3: while a slot offer or a cancel-confirmation is pending,
        # v16g4 port (audit item 201): global marketing opt-out. Only fires
        # for plain text, an exact opt-out keyword (not merely containing
        # "stop"), and when NO booking flow is mid-conversation — inside a
        # booking offer/cancel-confirm, "stop" already means "abort this
        # flow" (see handle_booking) and must keep that narrower meaning.
        # v16g6 FIX R6-H8: (1) strip().lower() can never match Tamil/Hindi —
        # compare via _norm_text like every other matcher in this file;
        # (2) template quick-replies ("Stop promotions") arrive as msg_type
        # 'button' or 'interactive', and a tap on the unsubscribe button did
        # NOTHING — user_text already carries the tapped text by this point.
        if (msg_type in ("text", "button", "interactive")
                and _norm_text(user_text) in _OPT_OUT_KEYWORDS
                and not (brain_cache.get(f"bk_cancel:{customer_id}:{from_phone}")
                         or brain_cache.get(f"bk_offer:{customer_id}:{from_phone}"))):
            # v16g5 FIX R5-H4: the durable suppression FIRST — this is what
            # actually stops reminders and follow-ups. The CRM consent flip
            # stays as a secondary signal for the ops views.
            _opt_ok = opt_out_subject(customer_id, from_phone)
            for _r in _find_subject_rows(customer_id, from_phone):
                try:
                    with _db_pool.get() as _c:
                        _execute(_c,
                            "UPDATE crm_contacts SET is_consented=? WHERE id=?",
                            (False if isinstance(_db_pool, PostgreSQLPool) else 0,
                             _r["id"]))
                except Exception as exc:
                    log.warning(f"⚠️  opt-out update failed (id={_r.get('id')}): {exc}")
            if not _opt_ok:
                # Never claim "you've been unsubscribed" when nothing was
                # written — that was the old behaviour for every BSUID patient
                # with no matching CRM row.
                log.critical(f"🛑 opt-out NOT persisted for cust={customer_id} "
                             f"— telling the patient to retry rather than "
                             f"lying about it (v16g5 FIX R5-H4).")
                _confirm = _t("optout_failed", _user_lang(customer_id,
                                                          from_phone, user_text))
                save_messages_batch(session_id, [
                    ("user",  user_text, "whatsapp", 0),
                    ("model", _confirm,  "local",    0)])
                send_whatsapp_sync(from_phone, _confirm, out_pid, out_tok, customer_id)
                analytics.inc("whatsapp.optout_failed")
                return
            _confirm = _t("opted_out", _user_lang(customer_id, from_phone,
                                                  user_text))
            save_messages_batch(session_id, [
                ("user",  user_text, "whatsapp", 0),
                ("model", _confirm,  "local",    0)])
            increment_chat_count(customer_id)
            send_whatsapp_sync(from_phone, _confirm, out_pid, out_tok, customer_id)
            analytics.inc("whatsapp.opted_out")
            return

        # canned one-worders ("ok"/"சரி"/"ठीक है") must reach the booking state
        # machine — the canned layer was answering them with a generic 👍 and
        # the cancellation silently never happened.
        _bk_pending = bool(cfg.ENABLE_BOOKING and (
            brain_cache.get(f"bk_cancel:{customer_id}:{from_phone}")
            or brain_cache.get(f"bk_offer:{customer_id}:{from_phone}")))
        gov = govern_message(user_text, guid,
                             bot_name=(brain.get("bot_name") or ""),
                             owner_phone=(brain.get("owner_phone") or ""),
                             healthcare=_is_health,
                             skip_canned=_bk_pending)
        for to, alert in gov["alerts"]:
            # v13: owner alerts go FROM this clinic's own number
            send_owner_alert_async(to, alert, out_pid, out_tok, customer_id)
        if gov["muted"]:
            return
        if gov["reply"]:
            # v14g5 FIX 50: persist the turn BEFORE the network send so a record
            # always backs a delivered message (and a mid-send crash can't lose it).
            save_messages_batch(session_id, [
                ("user",  user_text,    "whatsapp", 0),
                ("model", gov["reply"], "local",    0),
            ])
            increment_chat_count(customer_id)
            # v14g5 FIX 26: a first contact that only triggers a local/templated
            # reply is still a lead — capture it here too, not just on the AI path.
            crm_add_contact(customer_id,
                            (profile_name.strip() or f"WA {pii_vault.mask(from_phone)}"),
                            from_phone, notes=f"First msg: {user_text[:200]}",
                            wa_user_id=wa_user_id)   # v16 U1
            send_whatsapp_sync(from_phone, gov["reply"], out_pid, out_tok, customer_id)  # v14: ordered
            analytics.inc("whatsapp.local_reply")
            return

        # v16g2 FIX H2+H3: typed-number capture runs HERE — after emergency /
        # human / VIP routing and only when nothing routed (gov reply is None,
        # not muted, no alerts fired). The 7-day ask key no longer doubles as
        # the capture trigger: capture listens ONLY to the 15-minute
        # `numreq_window`, and ONLY when the message is mostly the number
        # (≤6 words) — an Aadhaar number, an order id, or a lab's number the
        # patient is asking about days later is no longer "their phone" that
        # swallows the actual question with a cheery "✅ Got it!".
        _numwin = brain_cache.get(f"numreq_window:{customer_id}:{from_phone}")
        if (cfg.ENABLE_PHONE_CAPTURE and _is_bsuid(from_phone)
                and msg_type == "text" and not gov["alerts"]
                and len(user_text.split()) <= 6
                and _numwin):
            _typed = _extract_phone_like(user_text)
            # v16g4 FIX M9: window re-opened by a forwarded CONTACT CARD
            # (value "strict") accepts only a message that IS the number —
            # ≤2 tokens and almost nothing but digits/punctuation left over.
            # "call my brother 98765 43210" no longer becomes their phone.
            if _typed and _numwin == "strict":
                _residue = re.sub(r"[\d\s+\-().]", "", user_text)
                if len(user_text.split()) > 2 or len(_residue) > 2:
                    _typed = ""
            if _typed and crm_attach_phone(customer_id, from_phone, _typed):
                brain_cache.delete(f"numreq_window:{customer_id}:{from_phone}")
                _shown = _normalize_msisdn(_typed) or _typed   # v16g2 FIX N2
                _confirm = _t("phone_saved_reminders" if cfg.ENABLE_SCHEDULER
                              else "phone_saved_records",      # v16g2 FIX C8
                              _user_lang(customer_id, from_phone, user_text),
                              masked=pii_vault.mask(_shown))   # v16g4 FIX M8
                save_messages_batch(session_id, [              # v16g2 FIX N8
                    ("user",  user_text, "whatsapp", 0),
                    ("model", _confirm,  "local",    0)])
                increment_chat_count(customer_id)
                send_whatsapp_sync(from_phone, _confirm, out_pid, out_tok,
                                   customer_id)
                analytics.inc("whatsapp.phone_typed")
                return

        # v14g4: appointment booking (flag-gated, default OFF). If this message is
        # part of a booking flow, handle it deterministically and stop — the AI
        # only runs for non-booking messages, so booking can never be derailed by
        # a hallucinated time or double-booked slot.
        if cfg.ENABLE_BOOKING and handle_booking(
                brain, from_phone, user_text, out_pid, out_tok, customer_id,
                session_id, subject_name=profile_name):
            return

        history = get_session_history(session_id)
        t0 = time.monotonic()
        try:
            reply, provider, escalated = ai_reply_pipeline(
                brain, history, user_text,
                user_uid=guid, channel="whatsapp")
        except RuntimeError:
            reply     = _t("ai_unavailable",                       # v16g5 R5-M2
                           _user_lang(customer_id, from_phone, user_text))
            provider  = "fallback"
            escalated = False
        latency_ms = int((time.monotonic() - t0) * 1000)

        if escalated:
            ghost_mute(guid)

        save_messages_batch(session_id, [
            ("user",  user_text, "whatsapp", 0),
            ("model", reply,     provider,   latency_ms),
        ])
        increment_chat_count(customer_id)
        crm_add_contact(customer_id,
                         (profile_name.strip() or f"WA {pii_vault.mask(from_phone)}"),
                         from_phone, notes=f"First msg: {user_text[:200]}",
                         wa_user_id=wa_user_id)   # v16 U1
        send_whatsapp_sync(from_phone, reply, out_pid, out_tok, customer_id)  # v14: ordered

        analytics.inc("whatsapp.chat.handled")
        log.info(f"📱 WA chat → {customer_id} | {pii_vault.mask(from_phone)} | {provider}")
    except Exception as exc:
        log.error(f"❌ WA worker error: {exc}", exc_info=True)
        analytics.inc("whatsapp.error")
        _release_wamid(msg)   # v16g4 FIX H6: crashed mid-turn → let Meta retry


@app.route("/whatsapp-webhook", methods=["GET", "POST"])
@limiter.exempt   # v14g5 FIX 5: Meta posts every clinic's traffic from shared IPs;
                  # an IP limit here throttles ALL clinics at once. The HMAC
                  # signature check (verify_meta_signature) is the real gatekeeper.
def whatsapp_webhook():
    if request.method == "GET":
        mode      = request.args.get("hub.mode")
        token     = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and _safe_ct_eq(
                token, cfg.WHATSAPP_VERIFY_TOKEN):   # v15g2 FIX L8 / v16g3 R3-M1
            log.info("✅ WhatsApp webhook verified by Meta.")
            return challenge or "", 200
        return "Forbidden", 403

    raw_body  = request.get_data()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_meta_signature(raw_body, signature, cfg.WHATSAPP_APP_SECRET):
        analytics.inc("whatsapp.sig_fail")
        log.warning(f"🚫 Invalid WA signature from {request.remote_addr}")
        return jsonify({"error": "Invalid signature"}), 401

    data    = request.get_json(silent=True) or {}
    queued  = 0
    for entry in data.get("entry", []):                 # #7: all entries
        for change in entry.get("changes", []):          # #7: all changes
            value           = change.get("value", {})
            # #13: the business line the patient texted (Meta's routing key)
            phone_number_id = value.get("metadata", {}).get("phone_number_id", "")
            # v14g5 FIX 15: WhatsApp delivers the sender's display name once per
            # webhook under value.contacts[].profile.name — capture it so CRM leads
            # and bookings carry a real name instead of just a masked number.
            # v16g2 FIX N10: key BOTH maps by wa_id AND user_id — for username
            # patients `from` is the BSUID, and a wa_id-only map missed every
            # lookup, naming every username patient "WA IN***…" forever.
            name_map: Dict[str, str] = {}
            uid_map:  Dict[str, str] = {}
            for c in value.get("contacts", []):
                _nm = (c.get("profile", {}) or {}).get("name", "")
                _cu = (c.get("user_id") or "")
                for _k in (c.get("wa_id", ""), _cu):
                    if _k:
                        name_map[_k] = _nm
                        uid_map[_k]  = _cu
            # v16g6 FIX R6-M6: delivery/read/FAILED callbacks arrive as
            # value.statuses and were dropped on the floor — a send the API
            # accepted (200) but never delivered (131047 outside the 24h
            # window, 131026 undeliverable, blocked recipient) was invisible.
            # On a build whose whole point was template-window correctness,
            # that meant no feedback loop at all. Count every status; log
            # failures loudly with Meta's exact code + title.
            for _st in value.get("statuses", []):
                _s = (_st.get("status") or "").lower()
                if _s:
                    analytics.inc(f"whatsapp.status.{_s}")
                if _s == "failed":
                    _errs = _st.get("errors") or []
                    _e0   = (_errs[0] if _errs else {}) or {}
                    log.error(f"❌ WA delivery FAILED "
                              f"wamid={str(_st.get('id',''))[:28]} "
                              f"to={pii_vault.mask(str(_st.get('recipient_id','')))} "
                              f"code={_e0.get('code')} "
                              f"{str(_e0.get('title') or _e0.get('message') or '')[:160]}")
            for msg in value.get("messages", []):        # #7: all msgs
                from_phone = msg.get("from", "")
                wamid      = msg.get("id", "")
                # #11/#38/#44: atomic claim — only the FIRST arrival of a wamid
                # wins; Meta retries / multi-worker races fast-fail here. The old
                # get()+set() had a TOCTOU gap that double-replied to patients.
                # v16g2 FIX L2: the claim now happens FIRST — system events
                # included — so a Meta redelivery can't reprocess a
                # user_id_update (duplicate remap audit/log lines).
                if wamid and not brain_cache.setnx(f"wamid:{wamid}",
                        ttl=cfg.DEDUPE_TTL_SECONDS):   # v15g4 FIX B9: was 600s
                    continue
                # v16 U5: a patient changing their phone number regenerates
                # their BSUID; Meta announces it via a system event carrying
                # the old and new IDs. Remap identity or their history orphans.
                if msg.get("type") == "system":
                    _sys = msg.get("system", {}) or {}
                    # v16g2 FIX M2: classic user_changed_number events carry
                    # ONLY system.new_wa_id (type "user_changed_number") — the
                    # old gate never let the exact shape the handler parses
                    # reach it, so real phone-change events silently dropped.
                    if ("user_id" in str(_sys.get("type", ""))
                            or "changed_number" in str(_sys.get("type", ""))
                            or _sys.get("new_user_id") or _sys.get("user_id")
                            or _sys.get("new_wa_id")):
                        submit_bg(_handle_wa_user_id_update,
                                  phone_number_id, from_phone, dict(_sys))
                    continue
                if not from_phone:
                    # v16 U2: for username patients `from` can be the BSUID —
                    # and per Meta docs it may even be OMITTED while user_id is
                    # present. Fall back to the BSUID as the chat identifier.
                    from_phone = (msg.get("user_id") or "").strip()
                    if not from_phone:
                        if wamid:
                            # v16g2 FIX L16: unprocessable → release the claim
                            # (BUG-13 release-on-drop discipline).
                            brain_cache.delete(f"wamid:{wamid}")
                        continue
                wa_user_id = (msg.get("user_id")
                              or uid_map.get(from_phone, "") or "").strip()  # v16 U1
                # v14 Bug 43: serialize per conversation (same patient + same
                # business line) so rapid messages are processed in arrival order;
                # different conversations still run in parallel.
                conv_key = f"wa:{phone_number_id}:{from_phone}"
                if submit_ordered(conv_key, _process_wa_message,
                                  from_phone, msg, phone_number_id,
                                  name_map.get(from_phone, ""),
                                  wa_user_id):  # #1: async, ordered / v16 U1
                    queued += 1        # v16g2 FIX M1: was duplicated — the
                    #                    webhook's `accepted` count read 2×
                elif wamid:
                    # v14g3 BUG 13: backlog full → this message was NOT processed.
                    # Release the dedupe claim so Meta's automatic retry can try
                    # again later, instead of being deduped away (= permanent loss).
                    brain_cache.delete(f"wamid:{wamid}")

    # #1: ALWAYS 200 immediately — Meta must never time out or retry-storm.
    return jsonify({"status": "queued", "accepted": queued}), 200


# ── Instagram Messaging Webhook (v11 — async, same brain / CRM / memory) ─────
# Same #1 + #7 fixes as WhatsApp: validate + dedupe + queue, then 200 instantly;
# process every messaging event (not just events[0]) in the worker pool.
def _process_ig_message(sender: str, recipient: str, message: dict) -> None:
    """Heavy per-DM handler — runs in the background pool. Owner alerts still go
    out over WhatsApp; the customer reply goes back over Instagram.
    v13: routes by the IG business account that received the DM (recipient) →
    owning clinic, and replies from THAT clinic's own IG token (global fallback)."""
    try:
        user_text  = (message.get("text") or "").strip()
        media_only = False   # v15 FIX 22: image/video/file DM → ack after routing
        if not user_text:
            atts = message.get("attachments") or []
            aud  = next((a for a in atts if a.get("type") == "audio"), None)
            if aud:
                user_text = transcribe_audio_url((aud.get("payload") or {}).get("url", ""))
                if user_text:
                    analytics.inc("voice.transcribed")
            if not user_text:
                if atts:
                    # v15 FIX 22: was a bare `return` — an IG follower sending a
                    # property photo or a report got NOTHING (WhatsApp has acked
                    # media since v12 #16). Route first, then acknowledge below.
                    media_only = True
                else:
                    return

        # #40: bound text before any regex / classification work
        if len(user_text) > cfg.MAX_MESSAGE_LEN:
            user_text = user_text[:cfg.MAX_MESSAGE_LEN]

        # ── v13 routing: which clinic owns the IG account that got this DM? ──
        brain = get_brain_by_ig_id(recipient)
        if not brain:
            log.info(f"📸 Unknown IG account: {pii_vault.mask(recipient)}")
            analytics.inc("instagram.unroutable")
            return
        customer_id    = brain["customer_id"]
        ig_own, ig_tok = brain_ig_creds(brain)     # this clinic's own IG creds
        wa_pid, wa_tok = brain_wa_creds(brain)     # owner alerts go via WhatsApp

        # v15 FIX 11 (MEDIUM): per-conversation scope + logged drop (see WA path).
        if not customer_limiter.check(f"{customer_id}:{sender}"):
            analytics.inc("ratelimit.customer.hit")
            log.warning(f"🚦 rate-limited IG msg dropped cust={customer_id} "
                        f"from={pii_vault.mask(sender)}")
            return

        uid = f"ig:{customer_id}:{sender}"
        if ghost_is_muted(uid):
            analytics.inc("ghost.skipped")
            return

        if media_only:   # v15 FIX 22: acknowledge, mirroring the WA media ack
            send_instagram_sync(sender,
                "📎 Thanks! We've received your file. Our team will review it "
                "shortly — meanwhile, feel free to type any question and I'll "
                "help right away.", ig_own, ig_tok, customer_id)
            analytics.inc("instagram.media_ack")
            return

        # #13: scope session key by customer_id so two businesses sharing an IG
        # follower never bleed conversation history across tenants.
        skey  = f"ig_session:{customer_id}:{sender}"
        shash = _crm_phone_hash(customer_id, f"ig_{sender}")
        session_id = brain_cache.get(skey)
        if not session_id:
            # v15g2 FIX M3: resume from the DB before minting a fresh session.
            session_id = (_find_session_by_subject(customer_id, shash)
                          or create_session(customer_id, channel="instagram",
                                            subject_hash=shash))
        brain_cache.set(skey, session_id, ttl=3600)   # v15g2 FIX M3: sliding TTL

        _is_health = _brain_is_health(brain)   # v16g4 FIX P3: cached per brain version

        # v16g6 FIX R6-H8 (IG): WhatsApp has had a global marketing opt-out
        # since v16g4; Instagram had NONE — an IG lead could never
        # unsubscribe from cold-lead follow-ups. Same exact-match gate, same
        # durable suppression, keyed exactly the way IG subjects are stored
        # everywhere else in this file ("ig_<sender>").
        if _norm_text(user_text) in _OPT_OUT_KEYWORDS:
            _ig_subj = f"ig_{sender}"
            _opt_ok = opt_out_subject(customer_id, _ig_subj)
            for _r in _find_subject_rows(customer_id, _ig_subj):
                try:
                    with _db_pool.get() as _c:
                        _execute(_c,
                            "UPDATE crm_contacts SET is_consented=? WHERE id=?",
                            (False if isinstance(_db_pool, PostgreSQLPool) else 0,
                             _r["id"]))
                except Exception as exc:
                    log.warning(f"⚠️  IG opt-out update failed "
                                f"(id={_r.get('id')}): {exc}")
            if _opt_ok:
                _ack = ("You will no longer receive promotional messages "
                        "from us. / இனி எங்களிடமிருந்து விளம்பரச் "
                        "செய்திகள் அனுப்பப்படாது.")
                analytics.inc("optout.instagram")
            else:
                _ack = ("Sorry — we couldn't record that just now. "
                        "Please send STOP once more.")
            send_instagram_sync(sender, _ack, ig_own, ig_tok, customer_id)
            return

        gov = govern_message(user_text, uid,
                             bot_name=(brain.get("bot_name") or ""),
                             owner_phone=(brain.get("owner_phone") or ""),
                             healthcare=_is_health)   # v15g4 FIX A2/A5
        for to, alert in gov["alerts"]:
            send_owner_alert_async(to, alert, wa_pid, wa_tok, customer_id)
        if gov["muted"]:
            return
        if gov["reply"]:
            # v14g5 FIX 50: persist before the network send (see WA path).
            save_messages_batch(session_id, [
                ("user",  user_text,    "instagram", 0),
                ("model", gov["reply"], "local",     0),
            ])
            increment_chat_count(customer_id)
            # v14g5 FIX 26: capture the IG lead on the local-reply path too.
            crm_add_contact(customer_id, f"IG {pii_vault.mask(sender)}",
                            f"ig_{sender}", notes=f"First msg: {user_text[:200]}")
            send_instagram_sync(sender, gov["reply"], ig_own, ig_tok, customer_id)  # v14: ordered
            analytics.inc("instagram.local_reply")
            return

        history = get_session_history(session_id)
        t0 = time.monotonic()
        try:
            reply, provider, escalated = ai_reply_pipeline(
                brain, history, user_text, user_uid=uid, channel="instagram")
        except RuntimeError:
            reply     = _t("ai_unavailable",                       # v16g5 R5-M2
                           _user_lang(customer_id, f"ig_{sender}", user_text))
            provider  = "fallback"
            escalated = False
        latency_ms = int((time.monotonic() - t0) * 1000)

        if escalated:
            ghost_mute(uid)

        save_messages_batch(session_id, [
            ("user",  user_text, "instagram", 0),
            ("model", reply,     provider,    latency_ms),
        ])
        increment_chat_count(customer_id)
        crm_add_contact(customer_id, f"IG {pii_vault.mask(sender)}",
                         f"ig_{sender}", notes=f"First msg: {user_text[:200]}")
        send_instagram_sync(sender, reply, ig_own, ig_tok, customer_id)  # v14: ordered

        analytics.inc("instagram.chat.handled")
        log.info(f"📸 IG chat → {customer_id} | {pii_vault.mask(sender)} | {provider}")
    except Exception as exc:
        log.error(f"❌ IG worker error: {exc}", exc_info=True)
        analytics.inc("instagram.error")


@app.route("/instagram-webhook", methods=["GET", "POST"])
@limiter.exempt   # v14g5 FIX 5: see WhatsApp webhook — signature is the real gate.
def instagram_webhook():
    if request.method == "GET":
        mode      = request.args.get("hub.mode")
        token     = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and _safe_ct_eq(
                token, cfg.INSTAGRAM_VERIFY_TOKEN):  # v14g5 FIX 35 / v16g3 R3-M1
            log.info("✅ Instagram webhook verified by Meta.")
            return challenge or "", 200
        return "Forbidden", 403

    raw_body  = request.get_data()
    signature = request.headers.get("X-Hub-Signature-256", "")
    secret    = cfg.INSTAGRAM_APP_SECRET or cfg.WHATSAPP_APP_SECRET
    if not verify_meta_signature(raw_body, signature, secret):
        analytics.inc("instagram.sig_fail")
        return jsonify({"error": "Invalid signature"}), 401

    data = request.get_json(silent=True) or {}
    if data.get("object") != "instagram":
        return jsonify({"status": "ignored_object"}), 200

    queued = 0
    for entry in data.get("entry", []):                 # #7: all entries
        for ev in entry.get("messaging") or []:          # #7: all events
            sender    = str(ev.get("sender", {}).get("id", ""))
            recipient = str(ev.get("recipient", {}).get("id", ""))
            message   = ev.get("message") or {}
            if not sender or not message or message.get("is_echo"):
                continue
            mid = message.get("mid", "")
            # #11/#38/#44: atomic claim — first arrival of an mid wins; retries
            # and multi-worker races fast-fail instead of double-replying.
            if mid and not brain_cache.setnx(f"igmid:{mid}",
                    ttl=cfg.DEDUPE_TTL_SECONDS):       # v15g4 FIX B9: was 600s
                continue
            # v14 Bug 43: serialize per IG conversation (same follower → same
            # business account) so rapid DMs process in order; parallel across convos.
            conv_key = f"ig:{recipient}:{sender}"
            if submit_ordered(conv_key, _process_ig_message,
                              sender, recipient, message):   # #1: async, ordered
                queued += 1
            elif mid:
                # v14g3 BUG 13: backlog full → release the dedupe claim so a Meta
                # retry can re-deliver instead of being silently deduped away.
                brain_cache.delete(f"igmid:{mid}")

    return jsonify({"status": "queued", "accepted": queued}), 200


# ── Chat API ──────────────────────────────────────────────────────────────────
@app.route("/chat", methods=["POST"])
@limiter.limit(cfg.CHAT_RATE_LIMIT)
def chat():
    # v15 FIX 5 (HIGH): auth gate. Customer IDs are minted as HX_WA_<digits> —
    # derivable from any clinic's public WhatsApp number — so an open /chat is
    # a free ticket to burn this deployment's Gemini quota. Constant-time key
    # compare; unset key = open (dev) unless STRICT_PROD, which fail-closes.
    if cfg.CHAT_API_KEY:
        if not _safe_ct_eq(request.headers.get("X-Api-Key", ""),
                           cfg.CHAT_API_KEY):        # v16g3 R3-M1
            analytics.inc("chat.auth_fail")
            return jsonify({"error": "Invalid or missing X-Api-Key"}), 401
    elif cfg.STRICT_PROD:
        return jsonify({"error": "/chat requires CHAT_API_KEY under STRICT_PROD"}), 401
    try:
        _body = request.get_json(silent=True)
        # v16g6 FIX R6-M8: a non-dict JSON body ([1,2], "hello") is truthy,
        # so ** raised TypeError OUTSIDE the ValidationError catch → 500.
        req = ChatRequestValidator(**(_body if isinstance(_body, dict) else {}))
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "detail": exc.errors()}), 422

    brain = get_customer_brain(req.customer_id)
    if not brain:
        return jsonify({"error": "Customer not found"}), 404

    # Per-customer rate limit
    if not customer_limiter.check(req.customer_id):
        analytics.inc("ratelimit.customer.hit")
        return jsonify({"error": "Rate limit exceeded for this customer"}), 429

    # Session handling
    session_id = req.session_id
    if session_id and not session_exists(session_id, req.customer_id):
        return jsonify({"error": "Invalid session_id"}), 400
    # v15g2 FIX L10: session creation is DEFERRED until the AI succeeds — the
    # 503 path used to leave one orphan empty session per failed call.
    _new_session = not session_id
    history = [] if _new_session else get_session_history(session_id)

    t0 = time.monotonic()
    try:
        reply, provider, _escalated = ai_reply_pipeline(
            brain, history, req.message,
            user_uid=f"api:{req.customer_id}", channel="api")
    except RuntimeError:                            # v16g2 FIX C4: unused `exc`
        analytics.inc("chat.ai_all_failed")
        return jsonify({
            "error":      "AI unavailable",
            "request_id": g.get("request_id"),
        }), 503
    latency_ms = int((time.monotonic() - t0) * 1000)

    _persisted = True
    try:
        # v16g4 FIX L11: the Gemini call above is PAID and already succeeded —
        # a create_session/save hiccup used to 500 the whole request and throw
        # the reply away. Persistence is best-effort here; the reply always
        # reaches the caller, with persisted=false so the client knows the
        # turn isn't in history.
        if _new_session:
            session_id = create_session(req.customer_id, channel="api")   # v15g2 FIX L10
        save_messages_batch(session_id, [
            ("user",  req.message, "api",     0),
            ("model", reply,       provider,  latency_ms),
        ])
        increment_chat_count(req.customer_id)
    except Exception as _pe:
        _persisted = False
        analytics.inc("chat.persist_failed")
        log.error(f"❌ /chat persist failed (cust={req.customer_id}): {_pe}")
    analytics.inc("chat.success")

    _body = {
        "reply":       reply,
        "provider":    provider,
        "session_id":  session_id,
        "latency_ms":  latency_ms,
        "request_id":  g.get("request_id"),
    }
    if not _persisted:
        _body["persisted"] = False   # v16g4 FIX L11
    return jsonify(_body), 200
