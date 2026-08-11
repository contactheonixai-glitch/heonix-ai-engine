"""
═══════════════════════════════════════════════════════════════════════════════
  HEONIX ULTRA ENGINE  v16.0   ·   WHATSAPP USERNAMES / BSUID COMPAT 🦅
═══════════════════════════════════════════════════════════════════════════════
  Meta is changing WhatsApp's identity layer: users can adopt a USERNAME and
  hide their phone number. Since 31-Mar-2026 every message webhook carries a
  business-scoped user ID (user_id / BSUID, format CC.alphanum e.g.
  IN.1A2B3C4D…); from June 2026 a username patient's first message may arrive
  with a BSUID INSTEAD of a phone number. v16 makes the engine identity-
  agnostic end-to-end. Tags: "v16 U<n>".

  ── v16 GEN-4 · ROUND-4 CLOSE-OUT (50 fixes · tags "v16g4 FIX *" · +3 ports) ──
   LAUNCH-CRITICAL — H1 Tally welcome: template-only, to the OWNER's phone
   (was free text to the WABA line itself = never delivered) · H2 follow-ups
   template-only + boot warning (a cold lead is BY DEFINITION outside the 24h
   window; the free-text fallback burned 5 retries per lead per tick) · H3
   IG leads (ig_*) skipped by the WhatsApp follow-up sender, visibly · H4
   Tally signature fails CLOSED under STRICT_PROD (the brain-minting endpoint
   was open when the secret was unset) · H5 PG pool self-heals poisoned
   connections (rollback-fail → close, not recycle) · H6 wamid claim released
   on unroutable / rate-limit / crash exits (Meta's retry was being deduped
   into permanent message loss) · H7 WhatsApp creds fall back AS A PAIR
   (clinic pid + global token = guaranteed 401 + false needs_reauth).
   BEHAVIOUR — M2 keyword emergencies ghost-mute like AI escalations · M3
   "ok/சரி/ठीक है" re-confirms instead of cancelling · M4 unrecognized reply
   in the cancel window falls through to the AI (question answered, booking
   kept) · M5 cancel/retire report REAL success; retire-failure = CRITICAL
   log + honest "confirmed" wording · M8 FULL ta/hi/en localization of every
   system string (booking, reminders, follow-ups, phone capture; per-user
   7-day language memory) · M9 card-reopened capture window accepts only a
   bare number · M15 stale slot-pick after offer TTL → fresh list.
   PLATFORM — M1 one boolean env parser (12 flags) · M6 smoke test uses a
   template / says the free-text delivery caveat · M7 4096-char chunked sends
   · M10 tenant-scoped admin JWTs ("tnt" claim, central fence in require_jwt,
   admin_users.tenant_id migration) · M11 real unique-violation detection
   (pgcode 23505 / IntegrityError, 4 sites) · M12 reminder idempotency claim
   (DB blip ≠ reminder every minute) · M13 legacy ADMIN_API_KEY refused under
   STRICT_PROD unless acknowledged; audit actor fingerprinted · M14 limiter
   reads both window terms from ONE backend · L1-L20 ratham typo/percentile
   ceiling/true dark-count/boot ready-event/calendar-correct "tomorrow"/
   ap-south-1 default/banner recon gating/cfg-read Tally secret/₹-negation/
   shutdown fallback off-caller-thread/paid reply survives persist failure/
   erasure flushes resp:* cache/one mask policy/reauth tuple rows/PG cursor
   close/viewer-tier CRM masking/canonical _iso_utc writer/IG id digits
   guard/soft-delete resurrect blocked/script-aware token estimate ·
   P1-P6 column-check memo/Gemini client LRU/health-flag cache/one-txn
   migration backfill/bounded slot scan/shared lease scanner + lock backoff ·
   O1 leader-gated outbox drain · O2 WEB_CONCURRENCY-under-gunicorn warning.
   HOTFIX 20-Jul (first live Postgres run): HF1 _execute escapes literal %
   (%%-then-?→%s — a '%' inside a SQL COMMENT was parsed as a placeholder →
   IndexError → Tally webhook 500) · HF2 that comment moved out of the SQL
   string · HF3 TCP keepalives on both PG pools (idle-drop SSL EOF noise).
   PORTS (re-verified from a stale 223-item report — 3 real): #101 location
   messages acknowledged · #201 exact-match STOP/UNSUBSCRIBE opt-out ·
   #221 CRM refreshes a changed display name.

  ── v16 GEN-3 · ROUND-3 CLOSE-OUT (24 fixes · tags "v16g3 FIX R3-*") ──
   H1 VIP ₹-regex word boundary ("3 floors 2" no longer pings 💎) · H2 two-
   tier booking vocabulary (informational schedule/consult/timings answered
   by the AI, not the slot list) · H3 negation windows (pre≤3 on the human
   list, clause-final post≤3 ta/hi everywhere; emergencies pinned pre=1) ·
   M1 _safe_ct_eq on every header/param compare_digest (garbage 401s, not
   500s) · M2 typed-capture plausibility (an Aadhaar is not a phone) · M3
   contact-card provenance (auto-attach only inside the 15-min ask window) ·
   M4 tiered mask() (8-11 chars no longer 75% visible) · M5 stale "keep it"
   tap keeps · M6 U3-capture merges the pre-username row (consent carried,
   bookings + sessions re-keyed) · M7 /ready checks the DB · M8 admin-create
   409 only on real duplicates · M9 sliding-window limiter (boundary 2×
   burst gone) · L1-L12 dead-var/lint/safe-env/SSRF-allowlist/ja-detect/
   prompt-time-bucket/readable tap history/limit-before-auth/idempotency
   parse guard/health recon gating/pool drain/msisdn leading zeros.

   U1  BSUID CAPTURE + STORAGE — msg.user_id (fallback contacts[].user_id)
       is read on every inbound message; new crm_contacts.wa_user_id column
       (idempotent _migrate_v16, indexed per clinic). Existing patients are
       BACKFILLED the next time they message, mirroring Meta's Contact Book
       locally.
   U2  IDENTIFIER FLEXIBILITY — the chat id (`from`) is treated as OPAQUE
       everywhere: phone for classic contacts, BSUID for username patients.
       _is_bsuid() detects the documented format; _crm_phone_hash hashes a
       BSUID as the FULL exact string (the old digits-only normalisation
       would have silently MERGED username patients into one CRM row).
       Sends, sessions, bookings, dedupe, DPDP erasure and owner-alert
       masking all handle both. `from` may even be OMITTED per Meta docs —
       the engine falls back to user_id as the chat identifier.
   U3  PHONE-NUMBER CAPTURE FLOW — when a username-only patient completes a
       booking, HELIO asks ONCE (7-day guard) for their real number via
       Meta's request button, falling back to a plain-text ask if the
       interactive type is rejected (type/action strings env-tunable:
       WA_PHONE_REQUEST_TYPE / WA_PHONE_REQUEST_ACTION — VERIFY against
       current Cloud API docs at GA). The reply arrives as a `contacts`
       webhook (previously silently dropped!) or as typed text — both are
       parsed, stored encrypted in enc_phone on the SAME row (identity
       continuity: phone_hash stays BSUID-keyed), confirmed to the patient,
       and preferred automatically by reminder/follow-up sends
       (_resolve_send_addr). Declining is fine — 'Send to BSUID' delivers.
       ENABLE_PHONE_CAPTURE=0 disables the ask.
   U4  CONTACT BOOK — Meta-hosted, ON by default, zero integration work per
       docs. Boot summary now reminds you to VERIFY it once in Business
       Suite; if a known patient later adopts a username, their number keeps
       appearing in webhooks because of this mapping.
   U5  user_id_update HANDLER — a patient changing their phone number gets a
       REGENERATED BSUID, announced via a system webhook. v16 remaps the CRM
       row + upcoming bookings old→new (audited), so their history and
       appointments never orphan. Field names parsed tolerantly across the
       documented shapes.

  NOTES · DPDP erasure for a username patient: pass their BSUID as "phone".
        · Authentication templates still REQUIRE a real phone (Meta rule) —
          another reason the U3 capture exists. Utility/marketing templates
          and free-form sends work to BSUIDs.
        · Instagram unchanged — IG PSIDs were always opaque IDs (the same
          design this update forces onto WhatsApp).
        · Test before rollout: Meta's dummy BSUID API + existing webhook
          endpoint; U1/U2/U5 are pure webhook-side and safe from day one.
  NEW ENV (all optional): ENABLE_PHONE_CAPTURE=1,
        WA_PHONE_REQUEST_TYPE=phone_number_request_message,
        WA_PHONE_REQUEST_ACTION=send_phone_number
═══════════════════════════════════════════════════════════════════════════════
  HEONIX ULTRA ENGINE  v15.0 — GEN-4   ·   ROUND-4 AUDIT CLEAN (50 findings) 🦅
═══════════════════════════════════════════════════════════════════════════════
  v15 GEN-4 closes the ROUND-4 (launch-readiness) audit — 38 code fixes across
  7 launch-critical · 13 medium · 12 low · 6 perf findings. Same discipline:
  surgical patches, no rewrite, compile-verified. Tags: "v15g4 FIX <id>"
  (ids match HEONIX_v15_GEN3_Round4_Audit_50_Findings.md).

  🔴 LAUNCH-CRITICAL
   A1  _norm_text stripped Indic COMBINING MARKS (matras/virama are not
       "alnum"), collapsing every Tamil/Hindi word to bare consonants —
       खाना (food) == खून (blood), so "मुझे खाना चाहिए" fired the EMERGENCY
       route + owner alert. One-line root fix: marks are kept. Every Indic
       keyword in the engine (emergency/human/VIP/booking/canned/cancel-YES)
       now matches the actual word, not its skeleton.
   A2  Emergency keywords are now VERTICAL-AWARE. "bleeding", "unbearable",
       "severe pain", "ரொம்ப வலி" are routine DENTAL vocabulary — at a clinic
       they hijacked normal complaints into the emergency script + alert spam.
       Healthcare uses a strict life-threat list (heart attack / can't breathe
       / collapsed / suicide / accident ...); ambiguous pain-words stay active
       for other verticals. Genuine nuanced emergencies remain covered by the
       AI escalation token (all languages) — the same documented pattern that
       already removed lone "urgent".
   A3  Canned-reply layer no longer swallows booking-flow answers: "ok"/"okay"/
       "சரி"/"ठीक है" typed to a cancel-confirmation got a generic 👍 while the
       cancellation silently did NOT happen. When a booking state (offer or
       cancel-confirm) is pending, canned replies are skipped; emergency/human
       routing still runs first (correct priority).
   A4  "speak to the doctor" muted the bot for a full 15 minutes. Keyword-based
       human requests now use HUMAN_REQUEST_MUTE_SECONDS (default 300); the AI
       escalation path keeps the full GHOST_MUTE_SECONDS.
   A5  VIP/₹ owner alerts are DISABLED for healthcare — every "cleaning ₹500
       ah?" was pinging the doctor (alert fatigue kills real alerts). ELITE /
       real-estate keeps full VIP detection.
  🟠 MEDIUM
   B1  SQLite outbox claim is now rowcount-confirmed (UPDATE ... WHERE
       status='pending') — the janitor tick and the publish-time drain could
       both claim the same rows and DOUBLE-SEND welcomes/reminders.
   B2  /channel now busts the OLD wa_phone_number_id / instagram_id routing
       caches (wapid:*, wa_route:*, igid:*) — moving a number no longer leaves
       stale routing+creds live for up to 10 minutes.
   B3  Interactive slot ids now carry the slot EPOCH (slot:<epoch>) and are
       validated against the CURRENT offer — a tap on a stale list can no
       longer book a different time than the button displayed; stale taps get
       a fresh list.
   B4  DPDP erasure normalises the phone to digits for RAG uids + session
       cache keys — "+91 98765..." now actually erases the vectors stored
       under Meta's digit format. (IG erasure: pass the bare PSID as "phone".)
   B5  Tally intake normalises whatsapp/owner phones via _normalize_msisdn;
       garbage ("Yes", spaced numbers) can no longer become the welcome-send
       target or the identity seed — it's dropped with a loud log instead.
   B6  extract_by_label: candidates are more-specific-first AND phone slots
       require a ≥7-digit value — "Owner Name" can't steal the clinic-name
       slot, "Do you use WhatsApp?" can't become the business number.
   B7  AI retry policy: permanent errors (401/403/404/invalid key/bad model)
       are no longer retried; MAX_RETRIES default 3 → 1 (env-restorable) so a
       worst-case turn is seconds, not minutes. Docstring finally true.
   B8  Response cache buckets by HALF-hour aligned to :00/:30 — open/closed
       answers flip at the boundaries clinics actually use.
   B9  Webhook dedupe TTL 600s → DEDUPE_TTL_SECONDS (default 21600) — a Meta
       redelivery >10 min later no longer double-replies.
   B10 Rescheduling onto the slot you ALREADY hold is recognised ("kept ✅")
       instead of looping "that slot was just taken" forever.
   B11 A booking intent typed inside the cancel-confirm window (book /
       reschedule / status) is now SERVED, not discarded with "unchanged".
   B12 Follow-up scheduler logs + counts decrypt-skips instead of silently
       marking those leads followed.
   B13 Soft-deleting a clinic blanks wa_token_enc / ig_token_enc — no live
       secrets parked on dead rows.
  🟡 LOW
   C1  /admin/login returns 503 when pyjwt is missing (was 200 + empty token).
   C2  Unknown-username logins verify against a dummy hash — no more ~250ms
       timing oracle for username enumeration.
   C3  ?page=abc style params are safe-parsed + clamped (was a 500).
   C4  _execute logs LOUDLY if a future SQL string ever contains a literal
       '%' on Postgres (the blind ?→%s landmine, fenced).
   C5  multi_ai_reply distinguishes breaker-open from other RuntimeErrors in
       errors/metrics (was mislabelled).
   C6  /channel rejects a non-numeric wa_phone_number_id (400).
   C7  store_idempotency returns success; the Tally path logs CRITICAL when
       the idempotency record could not be written (duplicate-welcome risk
       is now visible).
   C8  GRAPH_API_VERSION default bumped v21.0 → v23.0 (verify current in env).
   C9  An over-long ENCRYPTION_KEY now warns that only the first 64 hex chars
       are used (was silent truncation).
   C11 Emergency lines name India's real numbers (108 / 112) in en/ta/hi.
   C12 Dead "रोम्बा नन्द्री" entry replaced with real romanised thanks tokens.
       (C10 re-assessed: for 12-digit Indian numbers, first-2 == country code,
        so mask() effectively reveals only last-4 — no change needed.)
  🔵 PERF
   D2  Conversation-lock wait is env-tunable (CONV_LOCK_WAIT_SECS, default 5).
   D3  CRM "touch" UPDATE is throttled to once per 10 min per contact — 1 less
       write on nearly every message (SQLite write-lock relief).
   D4  New indexes for the hourly purges: chat_messages(timestamp),
       webhook_log(processed_at) — no more full-table cleanup scans.
   D5  idx_wh_customer now also created on SQLite.
   D6  Qdrant client version is logged at init (pin it in requirements).
       (D1 stays an env knob: WORKER_THREADS is the concurrency ceiling.)
  ⚫ OPS ASSISTS (the 12 env/console items cannot be "fixed in code" — but:)
   E9a Boot now warns when ENABLE_SCHEDULER is on without REMINDER_TEMPLATE
       (most 24h reminders would die outside Meta's window).
   E11a Boot logs the (legacy) google.generativeai SDK version + configured
       model so the deprecated-SDK risk is visible on every deploy.

  NEW ENV (all optional, safe defaults):
    HUMAN_REQUEST_MUTE_SECONDS=300   DEDUPE_TTL_SECONDS=21600
    CONV_LOCK_WAIT_SECS=5            MAX_RETRIES=1  (set 3 to restore old)
  Still ONE file. Still surgical. A1–A5 were the last code between you and
  Vaakai — everything left is a SIM, Postgres, billing, and Meta templates. 🦅
═══════════════════════════════════════════════════════════════════════════════
  HEONIX ULTRA ENGINE  v15.0 — GEN-3   ·   ROUND-3 AUDIT CLEAN (5 findings) 🦅
═══════════════════════════════════════════════════════════════════════════════
  v15 GEN-3 closes the ROUND-3 adversarial audit. Same discipline as GEN-1→2:
  surgical patches, no rewrite, compile-verified. Tags: "v15g3 FIX <id>".
  Theme: production latency + retry resilience — the two things that decide
  whether a clinic's patient actually receives their reminder.

  HIGH
   1  Outbox retries had ZERO backoff: a transient failure retried on the very
      next 20s janitor tick (and instantly on every submit_bg drain), burning
      all 5 attempts in ~80 seconds — a routine 3-5 minute Meta hiccup
      DEAD-LETTERED real patient reminders and welcome messages. Now each
      failure schedules the row exponentially (30s→60s→120s→240s + jitter)
      via a new idempotent next_attempt_at column, stretching the same
      attempt budget across ~7.5 minutes. Breaker-open deferrals also get one
      tick of spacing so publish storms stop hot-looping the claim cycle.
   2  _wa_session was a BARE Session(): urllib3 defaults = pool_maxsize 10,
      zero retries. Worker pool + outbox + scheduler exceed 10 concurrent
      sends; every connection past #10 was discarded, so the next send paid a
      fresh TCP+TLS handshake to graph.facebook.com (~200-400ms from India).
      Now: HTTPAdapter pool_maxsize=64 + CONNECT-only retries (double-send
      safe — the request was never transmitted; read/status retries stay 0).
  MEDIUM
   3  Managed Redis drops idle connections; the first command after an idle
      gap failed silently and fell to the per-process dict — the same stale-
      brain split FIX H2 fought, triggered by idleness. health_check_interval
      =30 pings stale sockets before reuse; + connect timeout, retry_on_
      timeout, TCP keepalive.
   4  SQLite pool could return a POISONED connection: if commit AND rollback
      both raised (disk I/O error, interrupted WAL) the finally put the dead
      handle back — bricking 1/10th of all DB traffic until restart, on the
      exact SQLite path production runs TODAY. Broken connections are now
      closed and replaced; the pool self-heals.
   5  _kw_hit re-ran _norm_text (unicodedata NFKD + casefold) on the SAME
      constant keywords for EVERY message — hundreds of redundant Unicode
      normalisations per inbound in the hottest path. Keyword token tuples
      are now lru_cache'd; per-message cost drops to dict hits.

  ── GEN-2 history below ──────────────────────────────────────────────────────
  v15 GEN-2 closed the ROUND-2 adversarial audit: 22 findings (2 Critical ·
  2 High · 6 Medium · 12 Low) — 10 of them REPRODUCED LIVE against a running
  engine before fixing, then re-run green after. Same discipline as always:
  surgical patches, no rewrite, compile-verified. Tags: "v15g2 FIX <id>".

  CRITICAL
   C1  Postgres outbox was 100% DEAD — psycopg2 auto-decodes JSONB to a dict,
       json.loads(dict) threw TypeError, so EVERY welcome message, reminder and
       follow-up failed 5× and dead-lettered the moment the engine ran on
       Postgres. SQLite (TEXT column) hid it. Fixed with an isinstance guard.
   C2  detect_booking_intent was raw substring + ZERO confirmation:
       "what is your canCELLATION policy?" — and even "I do NOT want to
       cancel" — instantly CANCELLED a patient's real appointment;
       "UNavailable" / "consultation fee" hijacked normal questions into the
       booking flow. Now: whole-word + negation matching via _kw_hit (the same
       matcher v15 FIX 4 gave business detection) AND a mandatory YES/NO
       confirmation via wa_send_buttons_now — the function whose own docstring
       said "used for yes/no confirmations (cancel)" yet was never called.
  HIGH
   H1  A transient error during Tally onboarding LOST THE SIGNUP FOREVER: the
       FIX-16 lock was never released on failure → Tally's retry hit setnx,
       got 200 "duplicate_in_flight", marked it delivered, never retried.
       The claim is now released on every non-success path (BUG 13 discipline).
   H2  On Postgres, brain/route rows (datetime columns) silently NEVER reached
       Redis — json.dumps raised, the blanket except swallowed it, the value
       fell into the per-process dict. Token re-attach / channel-edit /
       soft-delete cache busts didn't propagate across workers (stale dead
       tokens served up to full TTL). json.dumps(..., default=str).
  MEDIUM
   M1  Dead-token outbox sends were marked 'done' — an undelivered welcome
       looked delivered forever and never resent after re-auth. Now 'failed'.
   M2  A booking inside two reminder windows fired BOTH reminders in one tick
       (two near-identical messages back-to-back). Only the closest due lead
       fires; larger ones are consumed.
   M3  ACTIVE chats lost all AI context at exactly 60 minutes: the session
       cache TTL was set only at creation. Now a sliding TTL + DB resume of
       the latest session by subject_hash (uses the FIX-3 index).
   M4  Worst-case AI turn (retries × 3 providers ≈ minutes) outlived the 60s
       conversation lease → cross-worker exclusivity silently expired exactly
       when the AI was slow. A heartbeat (new cache.renew()) keeps the lease
       alive while the task runs.
   M5  Tally label matcher was substring — "Instagram userNAME" stole the
       clinic-name slot ('@handle' onboarded as the clinic). Whole-word
       matching + priority-ordered candidates.
   M6  Breaker-OPEN fast-fails burned outbox attempts — a short WhatsApp
       outage could dead-letter perfectly good messages without one real send
       attempt. Deferred to 'pending' with the attempt budget preserved.
  LOW
   L1  plan_tier='premium' → GEMINI_MODEL_PREMIUM finally WIRED (a Config
       promise since v11; plan_tier was only ever SELECTed for a list).
   L3  Booking hours honestly documented as GLOBAL env (per-tenant = roadmap).
   L4  _booking_dispatch now persist-then-send (v14g5 FIX 50 standard).
   L5  booking_create returns ok/conflict/error — a DB outage is no longer
       reported to the patient as "that slot was just taken".
   L6  /chat validator honours MAX_MESSAGE_LEN (was hardcoded 2000).
   L7  First-admin bootstrap: ADMIN_BOOTSTRAP_USER/PASSWORD seed a superadmin
       when the table is empty — no more JWT chicken-and-egg.
   L8  Webhook verify-token compares constant-time (WA + IG) + a loud warning
       when the public default 'heonix_verify' is still in use.
   L9  Unset JWT/Flask secrets now derive DETERMINISTICALLY from
       ENCRYPTION_KEY — identical in every gunicorn worker (was per-worker
       random; the old guard missed `gunicorn -w 4` without WEB_CONCURRENCY).
   L10 /chat no longer creates an orphan empty session on the 503 path.
   L11 Template quick-reply taps (type 'button') handled, not black-holed.
   L12 _resolve_inbound_brain docstring un-staled (BUG-4-era mapping).

  NEW ENV (all optional):  ADMIN_BOOTSTRAP_USER / ADMIN_BOOTSTRAP_PASSWORD
  Still ONE file. Still surgical. Round-2 audit closed — what this engine
  needs next is STILL a paying clinic's live token, not more code. Ship it. 🦅
═══════════════════════════════════════════════════════════════════════════════
  HEONIX ULTRA ENGINE  v15.0   ·   AUDIT-CLEAN (independent 26-finding audit) 🦅
═══════════════════════════════════════════════════════════════════════════════
  v15 closes EVERY finding of the independent line-by-line audit of GEN-5
  (3 critical · 4 high · 9 medium · 10 low). Same discipline as always: surgical
  patches, no rewrite, compile-verified, backward compatible. Tags: "v15 FIX N"
  (numbers match HEONIX_v14_GEN5_Bug_Audit.md).

  CRITICAL
    1  _shutdown_event was referenced but NEVER DEFINED → the janitor thread
       died with a NameError milliseconds after every boot. Outbox timer drain,
       stuck-row recovery, cache pruning (RAM leak without Redis), the ENTIRE
       Gen-4 scheduler and retention purge silently never ran. Now defined.
    2  GET /crm/contacts crashed on SQLite (sqlite3.Row has no .get()).
    3  Tally signature: computed HEX, Tally sends BASE64 → setting
       TALLY_WEBHOOK_SECRET killed onboarding with 401s. Now base64 per docs.
  HIGH
    4  Business-type detection is word-boundary + priority ordered. "Hair salon
       in Chennai" no longer onboards as SaaS (the "ai"-substring bug); a
       "medical shop" is healthcare, not ecommerce.
    5  POST /chat gets an optional CHAT_API_KEY gate (X-Api-Key, constant-time).
       customer_id is derivable from a clinic's PUBLIC number — an open /chat
       let anyone burn Gemini quota. Unset = open + loud warning; STRICT_PROD
       fail-closes.
    6  A safety-blocked/empty AI reply (AIEmptyResponse) no longer counts as a
       circuit-breaker failure — 5 weird messages can't dark Gemini fleet-wide.
    7  Outbox 'processing' rows are stamped at CLAIM time and re-queued on that
       stamp (was created_at) → no more double-sends of slow in-flight events.
  MEDIUM
    8  OpenAI fallback: None content no longer crashes; raises AIEmptyResponse.
    9  Slot pick accepts ONLY a bare number ('3', 'no 3', '#3') — "can I come
       at 5?" no longer books slot #5.
   10  "cancel appointment" typed mid-offer now aborts the flow (was an
       infinite re-offer loop).
   11  Webhook rate limiter is scoped per CONVERSATION (clinic+patient) and
       drops are LOGGED — one flooder can't ghost a whole clinic silently.
   12  SMOKE_TEST_ENABLED now truly defaults OFF (code matches its own comment).
       ⚠️ Haroon: set SMOKE_TEST_ENABLED=1 in Render env — you use this tool.
   13  Postgres pool-overcommit clamp actually clamps (_write, not the
       nonexistent _pool attribute).
   14  Signals: handlers install ONLY under `python engine.py` (gunicorn keeps
       its own graceful SIGTERM), the handler now actually exits, and an atexit
       hook stops the janitor + closes the DB pool on the gunicorn path.
   15  Idempotency-store failures log at WARNING (duplicate-key stays DEBUG).
   16  Tally payloads are claimed atomically (setnx) → simultaneous identical
       deliveries can't double-process/double-welcome.
  LOW
   17  Dead verify_whatsapp_signature removed. ghost_resume() finally WIRED:
       new POST /admin/customer/<id>/ghost-resume {phone|ig_sender} un-mutes
       the AI instantly when the owner is done (was: wait out full mute TTL).
   18  AnalyticsEngine.percentile() no longer auto-creates probed keys (twin of
       v14g5 FIX 29, on the latency dict).
   19  Voice transcription uses _safe_response_text (Gemini .text can raise on
       safety blocks — same fix image understanding already had).
   20  pii_vault.mask() no longer reproduces every character of 5–6 char values.
   21  CustomerRateLimiter.check() docstring matches reality (returns bool).
   22  Instagram image/document DMs get an acknowledgement (were black-holed;
       WhatsApp has acked media since v12 #16).
   23  increment_chat_count no longer busts the brain cache on EVERY message
       (total_chats may lag ≤ CACHE_TTL in stats — the cache works again).
   24  _column_exists (PG) filters table_schema = current_schema().
   25  A malformed (non-hex) ENCRYPTION_KEY disables the vault with a LOUD
       error instead of an unhandled ValueError stack trace at import.
   26  (noted, unchanged by design) CORS default *, /health verbosity — tighten
       via env when multi-tenant goes live.

  NEW ENV (all optional):  CHAT_API_KEY=<unset = open>   SMOKE_TEST_ENABLED=0
  NEW ENDPOINT:            POST /admin/customer/<id>/ghost-resume
  Still ONE file. Still surgical. The engine is now audit-clean — the next
  upgrade it needs is a paying clinic's live token, not more code. Ship it. 🦅
═══════════════════════════════════════════════════════════════════════════════
  HEONIX ULTRA ENGINE  v14.0 — GEN-5   ·   AUDIT-HARDENED (50 findings closed) 🦅
═══════════════════════════════════════════════════════════════════════════════
  GEN-5 is a pure CORRECTNESS + SECURITY pass over GEN-4 driven by the 50-item
  audit. It is additive and backward compatible — with every Gen-4 flag still OFF
  it boots and behaves like Gen-4. Each fix is tagged inline "v14g5 FIX N".

  CODE-FIXED (real change in this file):
    1  /channel partial update no longer wipes the other channel (dynamic SET).
    2  WhatsApp media (voice/image) fetched with the OWNING clinic's token.
    3  DPDP erasure resolves sessions from the DB via chat_sessions.subject_hash
       (was a 1-hour cache key) + erases WA- and IG-shaped RAG uids.
    4  crm_get_contact_full is tenant-scoped (?customer_id=) → no id-enumeration IDOR.
    5  WhatsApp/Instagram webhooks exempt from the IP limiter (Meta = one source IP).
    6  Cross-worker per-conversation mutex (Redis) so two workers can't interleave
       one conversation. (Strict arrival order across workers still wants WEB_CONCURRENCY=1.)
    7  Scheduler runs under a single-leader Redis lock → no duplicate reminders/follow-ups.
    8  Token-death self-heal busts the ROUTING caches too (not just the brain cache).
    9  Voice-transcription Gemini + Whisper calls now carry hard timeouts.
   10  Single-tenant routing fallback is gated (SINGLE_TENANT_FALLBACK) + logs on use.
   11  Missing JWT/SECRET with >1 worker now REFUSES to boot (was warn-only).
   12  Reschedule keeps the old appointment until the NEW slot is actually booked.
   14  make_customer_id name-fallback is ASCII-safe (always matches the id pattern).
   15  Real WhatsApp profile name captured into CRM + bookings (was "WA 91***").
   16  Cold-lead follow-ups skip soft-deleted clinics.
   17  Tally fields mapped by LABEL first (robust to form reordering), index fallback.
   18  RAG embeddings padded (not just truncated) to EMBED_DIMS.
   19  Legacy X-Admin-Key compared in constant time.
   21  Password fallback is salted PBKDF2 (was unsalted SHA-256); constant-time verify.
   22  bookings table gets a FK→customer_brains ON DELETE CASCADE (fresh installs).
   23  /metrics optional token gate (METRICS_TOKEN).
   24  Reminder copy uses the ACTUAL remaining time, not the lead bucket.
   25  _to_local returns a true naive local datetime (no misleading UTC tag).
   26  Leads captured on the local/canned path too (not only the AI path).
   29  Analytics get_counter no longer auto-creates probed keys.
   33  store_idempotency logs instead of silently swallowing every error.
   35  Separate INSTAGRAM_VERIFY_TOKEN (falls back to the WhatsApp verify token).
   38  Booking slot dedupe keyed by canonical epoch (survives ISO formatting drift).
   40  Soft-deleting a clinic releases its routing number + busts caches.
   41  Read-only DB paths use autocommit (no empty COMMIT churn).
   44  Outbox fails permanent errors (missing creds/template) immediately, not after 5 tries.
   46  Owner alerts mask the subject (no internal id / full number leak).
   48  /health reports a LIVE Redis ping, not just "configured".
   50  Local/booking reply paths standardised to persist-then-send.

  BY DESIGN / OPS (documented, not a code defect — see the audit file):
    13 (offer state needs Redis — already required by STRICT_PROD)
    20 (Gemini model names are env-config — verify against the live model list)
    27/28/30/31/32/34/36/37/39/42/45/47 (accepted trade-offs / require env or sticky LB)

  NEW ENV (all optional, safe defaults):
    INSTAGRAM_VERIFY_TOKEN=<falls back to WHATSAPP_VERIFY_TOKEN>
    METRICS_TOKEN=<unset = open>   SINGLE_TENANT_FALLBACK=true
    CONV_LOCK_TTL=60   SCHED_LOCK_TTL=290
  Still ONE file. Still backward compatible. What stands between you and revenue
  is the first paying clinic + a live token — not another rewrite. Ship it. 🦅
═══════════════════════════════════════════════════════════════════════════════
  HEONIX ULTRA ENGINE  v14.0 — GEN-4   ·   ADVANCED FEATURES (additive) 🦅
═══════════════════════════════════════════════════════════════════════════════
  Gen-4 ADDS real, working features on top of the gen-3 hardened core. It is
  PURELY ADDITIVE and every feature is behind a flag that defaults OFF — so with
  no env changes, Gen-4 boots and behaves EXACTLY like Gen-3. Turn features on
  one at a time, after testing each live. New code is tagged inline "v14g4".

  WHAT'S NEW (all flag-gated, default OFF):
   • Appointment booking engine (ENABLE_BOOKING) — per-tenant slots computed
     from business-hours config; deterministic book / reschedule / cancel /
     status state machine (no fragile LLM tool-loop); race-safe via a unique
     slot index. Offered as a tappable WhatsApp list with a numbered-text
     fallback.
   • Background scheduler (ENABLE_SCHEDULER) — runs in the existing janitor
     thread: appointment reminders (REMINDER_LEAD_HOURS, e.g. "24,2"), one-time
     cold-lead follow-ups for CONSENTED contacts (FOLLOWUP_ENABLED), and DPDP
     retention purge of chat logs + dead bookings (DATA_RETENTION_DAYS).
   • Image understanding (ENABLE_IMAGE_UNDERSTANDING) — a patient/customer photo
     is read by Gemini (your existing multimodal key) and answered in the bot's
     own persona. Voice notes were already supported in gen-3.
   • Interactive WhatsApp messages — reply buttons + list pickers.
   • DPDP endpoints — POST /admin/customer/<id>/erase-subject (right-to-erasure:
     CRM + bookings + RAG memory + cache-mapped chat session), POST
     /admin/customer/<id>/consent, GET /admin/customer/<id>/bookings.
   • Outbox gains a whatsapp.template event so scheduled sends can use an
     approved template.

  HONEST CONSTRAINTS (read before enabling the scheduler):
   • WhatsApp delivers FREE TEXT only inside the 24-hour customer-service window.
     Reminders/follow-ups sent OUTSIDE 24h REQUIRE a pre-approved template —
     set REMINDER_TEMPLATE / FOLLOWUP_TEMPLATE to an approved template name and
     the scheduler routes via template automatically. Without a template, a
     scheduled send outside 24h will be rejected by Meta (by design).
   • The scheduler needs a long-lived process — fine on a Render *web service*,
     not on serverless/scale-to-zero.
   • None of this is a substitute for testing live against Meta + Gemini + your
     DB. All flags default OFF precisely so you can enable + verify one at a time.

═══════════════════════════════════════════════════════════════════════════════
  HEONIX ULTRA ENGINE  v14.0 — GEN-3   ·   PREMIUM HARDENING (20 bugs killed) 🦅
═══════════════════════════════════════════════════════════════════════════════
  Gen-3 is a CORRECTNESS + RESILIENCE pass over gen-2 — no new surface area, no
  rewrite. Every change below kills a real bug found in the gen-2 audit. The
  fixes are tagged inline in the code as "v14g3 BUG N":

   1  Analytics deadlock (CRITICAL) — snapshot() re-acquired a non-reentrant
      lock, so every /metrics scrape & /admin/analytics hit permanently hung a
      worker. Fixed with a no-lock inner percentile.
   2  Gemini & Claude had NO request timeout (only OpenAI did) — a frozen socket
      pinned a worker thread forever. Native SDK timeouts added.
   3  JWT_SECRET_KEY / SECRET_KEY defaulted to a per-process random value →
      tokens & Flask sessions broke across gunicorn workers. Startup now fails
      loud and refuses to boot under STRICT_PROD.
   4  Inbound routing compared whatsapp_phone == phone_number_id (a number vs a
      Meta ID — never equal) → dead path. Now routes on wa_phone_number_id.
   5  Conversation drains and fire-and-forget I/O shared ONE 8-thread pool
      (head-of-line blocking). Sends/alerts/audit/RAG get their own _IO_POOL.
   6  Timeout pool could leak threads on overrun — enlarged + breaker-guarded,
      and the AI path no longer needs it (native timeouts). Limitation documented.
   7  An empty WHATSAPP_APP_SECRET meant "accept ALL webhooks" → forgeable.
      Now fail-closed under STRICT_PROD / REQUIRE_WEBHOOK_SIGNATURE.
   8  Per-customer rate limit was per-process without Redis (effective limit ×
      worker count). Divides by worker count in the local fallback.
   9  Outbox welcome message always used GLOBAL creds → wrong number for tenant
      #2. Now uses the clinic's own creds + token self-heal.
  10  CRM dedupe was SELECT-then-INSERT over a NON-unique index (dup rows under
      races). Unique index + race-recovery that returns the existing id.
  11  customer_id used the last 10 digits only → a +1 and a +91 number could
      COLLIDE and overwrite each other's brain. Country-aware normalisation.
  12  Legacy phone lookup was exact-string → a reformatted number re-orphaned
      the clinic. Now also matches the normalised form.
  13  Backlog-full dropped a message AND its dedupe claim → Meta's retry was
      swallowed (permanent loss). The claim is now released on drop.
  14  Audit log rode on ENABLE_ANALYTICS → muting metrics silently killed the
      SOC2/GDPR trail. It now has its own ENABLE_AUDIT switch.
  15  Response cache wasn't language-keyed → a wrong-language reply was possible.
      Detected language is folded into the cache key.
  16  idx_brain_phone existed on Postgres only → table scan on SQLite. Added.
  17  Dead db() helper (ignored its read_only arg) removed — latent footgun.
  18  Gemini .text raised on safety blocks → spurious circuit-breaker trips.
      Safe extraction; an empty reply is "no answer" and falls through cleanly.
  19  Redundant JWT except clause (ExpiredSignatureError ⊂ InvalidTokenError).
  20  DATABASE_FILE default no longer mismatches its own documentation.

  NEW ENV (all optional, safe defaults):
    REQUIRE_WEBHOOK_SIGNATURE=0   ENABLE_AUDIT=true   DEFAULT_COUNTRY_CODE=91
    IO_THREADS=16   (TIMEOUT_THREADS default bumped 4 → 8)
  Still ONE file. Still backward compatible. What stands between you and revenue
  is deploying it + a live token + the first paying clinic — not another rewrite.
═══════════════════════════════════════════════════════════════════════════════

╔══════════════════════════════════════════════════════════════════════════════╗
║   HEONIX ULTRA ENGINE  v14.0 — STABLE-IDENTITY + ORDERED (2 real bugs killed) ║
║                                                                              ║
║  v14 FIXES TWO GENUINE CORRECTNESS BUGS ON TOP OF v13's MULTI-TENANT:         ║
║  ✅ BUG 41 — Identity Fragmentation: customer_id was derived from the mutable ║
║     display NAME, so a tiny Tally spelling edit minted a NEW id and orphaned  ║
║     all old patients/CRM. v14 derives a STABLE id from the WhatsApp number    ║
║     (HX_WA_<digits>) → same business = same id, name edits are harmless. A    ║
║     legacy-lookup keeps any pre-v14 name-based clinic on its existing id.     ║
║  ✅ BUG 43 — Asynchronous Anarchy: inbound messages were thrown onto an       ║
║     8-thread pool with NO ordering, so a patient's 3 fast messages could be   ║
║     processed out of order → scrambled AI history → wrong reply. v14 adds a   ║
║     per-conversation ordered runner: same patient+line = strict FIFO on one   ║
║     drainer; different conversations still run fully in parallel. Patient     ║
║     replies are now sent synchronously inside that slot, so even the OUTBOUND ║
║     replies arrive in order — not just the history.                          ║
║  ➕ Bonus: boot-time duplicate-number detector names exactly which clinics    ║
║     share a WhatsApp number (drawback #4 → self-diagnosing, 30-sec cleanup).  ║
║                                                                              ║
║  STRAIGHT TALK (read this): the long "10 drawbacks" list is mostly NOT bugs.  ║
║  Several are LAWS, not defects — you cannot auto-mint a Meta token (OAuth     ║
║  needs human consent), Meta rate limits are real, a DB has finite capacity,   ║
║  and infra costs money. Others (monolith / multi-tenant complexity) are the   ║
║  direct PRICE of choices you asked for: ONE single file, and true multi-      ║
║  clinic. No "v15 / v99" deletes physics or economics. This engine is already  ║
║  strong; what stands between you and revenue is DEPLOYING it + a live token + ║
║  the first paying clinic — not another rewrite. Ship it. 🦅                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║   HEONIX ULTRA ENGINE  v13.0 — TRUE MULTI-TENANT (per-clinic creds + self-heal)║
║                                                                              ║
║  v13 TURNS THE SINGLE-CLINIC ENGINE INTO AN INFINITE-CLINIC PLATFORM:        ║
║  ✅ Inbound routed by phone_number_id → the OWNING clinic (not the sender)   ║
║  ✅ Each clinic replies from its OWN WhatsApp number + token (global fallback)║
║  ✅ Per-clinic Instagram account + token, same routing model                 ║
║  ✅ Per-clinic tokens AES-256-GCM encrypted at rest (wa_token_enc/ig_token_enc)║
║  ✅ UNIQUE index on wa_phone_number_id — two clinics can NEVER share a number ║
║  ✅ Token-death self-heal: dead clinic token → flag needs_reauth + alert YOU ║
║  ✅ Secure JWT creds endpoint  POST /admin/customer/<id>/channel  (409 on dup)║
║  ✅ Onboarding smoke-test  POST /admin/customer/<id>/smoke-test (token alive?)║
║  ✅ Fleet health dashboard  GET /admin/tenants/health (which clinics are dark)║
║  ✅ Postgres-safe migration (check-before-ALTER → no poisoned transactions)  ║
║  ✅ BUGFIX: CRM contact id no longer returns 0 on Postgres (RETURNING id)    ║
║  ✅ 100% backward compatible — your FIRST clinic keeps working, zero config   ║
║                                                                              ║
║  HONEST SCALE NOTE: "infinite clinics / 100-crore users" is an INFRASTRUCTURE║
║  property, not a single-file property. This code is now architecturally      ║
║  correct to scale HORIZONTALLY (stateless workers + Postgres + Redis + outbox)║
║  so the ceiling becomes your DB size / dyno count / Meta limits — money you   ║
║  add, not bugs you hit. No software is "zero-bug"; this is hardened to fail   ║
║  loud, degrade safe, and self-heal. Scale it with read-replicas, a managed   ║
║  Postgres (or pgBouncer), more workers, and partitioning as volume grows.    ║
╚══════════════════════════════════════════════════════════════════════════════╝

╔══════════════════════════════════════════════════════════════════════════════╗
║     HEONIX ULTRA ENGINE  v12.0 — HYPER-SCALE HARDENED (concurrency-safe)    ║
║                                                                              ║
║  v12 CLOSES THE REAL CONCURRENCY / SCALE GAPS ON TOP OF v11:                 ║
║  ✅ Inbound routing by phone_number_id — replies now reach the real patient  ║
║  ✅ Image/PDF/video msgs get a friendly ack — no more silent black-holing    ║
║  ✅ Atomic webhook dedupe (Redis SET NX) — no double replies under N workers ║
║  ✅ Outbox claimed with FOR UPDATE SKIP LOCKED — one worker per event        ║
║  ✅ Outbox + webhook_log auto-cleanup in janitor — no table/disk bloat       ║
║  ✅ Circuit breaker HALF_OPEN now single-probe — no thundering-herd on AI    ║
║  ✅ Qdrant RAG wrapped in its own breaker + soft timeout — can't hang engine ║
║  ✅ ProxyFix behind Render LB — rate limit sees the real client IP, not Meta ║
║  ✅ MAX_CONTENT_LENGTH — oversized JSON payloads rejected before they hit RAM ║
║  ✅ Media download size-capped + connect/read timeouts — no OOM, no hang     ║
║  ✅ Local rate-limit keys now expire + get pruned — no zombie bans, no leak  ║
║  ✅ WhatsApp markdown normaliser — Gemini's **bold** rendered as WA *bold*    ║
║  ✅ Session cache key scoped per customer_id — no cross-tenant session mixup  ║
║  ✅ Gemini history trimmed to start on a user turn — no "must start with     ║
║     user" API crash when the window slices off the first turn                ║
║  ✅ Meta sends retried on transient/5xx/429 only — fewer silently dropped     ║
║  ✅ RAG never stores fallback/error replies — memory can't be poisoned       ║
║  ✅ /metrics COUNT(*) cached ~30s — a scrape storm can't lock the DB         ║
║  ✅ DB pool sizing guard — warns/clamps if workers×pool exceeds DB max conns ║
║  ✅ Per-worker janitor self-heal — survives gunicorn --preload fork          ║
║                                                                              ║
║  NOTE (honest): a handful of the audited items are ENV/OPS, not code —        ║
║  JWT_SECRET_KEY, ENCRYPTION_KEY, DATABASE_URL(+postgres), REDIS_URL,         ║
║  WEB_CONCURRENCY sizing. The engine now logs LOUD if they're wrong, but you  ║
║  still have to set them in Render. Full multi-tenant routing by              ║
║  phone_number_id is deliberately deferred to tenant #2 (see V12 doc).        ║
║                                                                              ║
║  ── inherited from v11.0 — PRODUCTION-HARDENED (all 15 v10 gaps) ──          ║
║  v7 DRAWBACKS RESOLVED IN v8:                                                ║
║  ✅ FIX #1  → Modular layer architecture (no more single-file chaos)        ║
║  ✅ FIX #2  → Multi-region geo-aware routing + health failover               ║
║  ✅ FIX #3  → Distributed transaction Saga + outbox pattern                  ║
║  ✅ FIX #4  → Horizontal DB: read replicas + table partitioning              ║
║  ✅ FIX #5  → Real-time analytics engine (event streaming + counters)        ║
║  ✅ FIX #6  → SOC 2 / GDPR audit trail + consent ledger                     ║
║  ✅ FIX #7  → bcrypt password hashing (was plaintext in v7 admin table)     ║
║  ✅ FIX #8  → Token-bucket rate limiter per customer_id (not just IP)       ║
║  ✅ FIX #9  → Retry with exponential back-off + jitter (AI calls)           ║
║  ✅ FIX #10 → OpenAI client singleton (was instantiated per request)        ║
║  ✅ FIX #11 → Anthropic client singleton (same)                              ║
║  ✅ FIX #12 → Graceful connection-pool drain on SIGTERM (K8s safe)          ║
║  ✅ FIX #13 → Health/readiness probes separate + structured for k8s          ║
║  ✅ FIX #14 → Webhook signature validation covers WhatsApp & Tally           ║
║  ✅ FIX #15 → Prometheus histograms for latency (was counters only)         ║
║                                                                              ║
║  RETAINED FROM v7 (all working):                                             ║
║  ◆ PostgreSQL + Redis + SQLite fallback                                     ║
║  ◆ AES-256-GCM PII encryption at rest                                      ║
║  ◆ JWT + RBAC (superadmin / admin / viewer)                                 ║
║  ◆ Multi-AI fallback: Gemini → OpenAI → Claude                             ║
║  ◆ Official Meta WhatsApp Cloud API                                          ║
║  ◆ Idempotency keys                                                          ║
║  ◆ Circuit breakers per AI provider                                          ║
║                                                                              ║
║  v10 GOD-LOGIC ADDITIONS (god_logic_v9 merged + drawbacks fixed):            ║
║  ◆ Instagram Messaging channel — same brain, CRM, memory as WhatsApp        ║
║  ◆ Voice-note decoder: WA/IG audio → Gemini → Whisper fallback              ║
║  ◆ Qdrant RAG long-term memory per end-user (AES-256 encrypted payloads)    ║
║  ◆ Cost optimizer: trivial msgs answered locally in 10 languages, ₹0 API    ║
║  ◆ Redis-backed response cache + ghost mode (multi-worker safe)             ║
║  ◆ Webhook de-duplication (Meta retries no longer cause double replies)     ║
║  ◆ Emergency / human-handoff / VIP routing: keywords + AI escalation token  ║
║  ◆ Languages: script auto-detect; AI replies in ANY language user writes    ║
║  ◆ Meta Graph v21.0 + Gemini 2.5 (v8 defaults were shut down by vendors)    ║
╚══════════════════════════════════════════════════════════════════════════════╝

ENVIRONMENT VARIABLES:

  ── DATABASE ──────────────────────────────────────────────────────────────────
  DATABASE_MODE         = "postgres" | "sqlite"     (default: postgres)
  DATABASE_URL          = postgresql://user:pass@primary-host:5432/heonix_db
  DATABASE_REPLICA_URL  = postgresql://user:pass@replica-host:5432/heonix_db
                          (optional read-replica — improves read throughput)
  DATABASE_FILE         = heonix_ultra.db            (sqlite fallback only)
  MAX_POOL_SIZE         = 20

  ── AI ENGINE ─────────────────────────────────────────────────────────────────
  GENAI_API_KEY         = Google Gemini API key
  OPENAI_API_KEY        = OpenAI GPT-4 API key
  ANTHROPIC_API_KEY     = Anthropic Claude API key
  GEMINI_MODEL          = gemini-3.1-flash-lite
  OPENAI_MODEL          = gpt-4o-mini
  ANTHROPIC_MODEL       = claude-haiku-4-5-20251001
  AI_MAX_TOKENS         = 1000
  AI_TIMEOUT_SECS       = 30

  ── WHATSAPP ──────────────────────────────────────────────────────────────────
  WHATSAPP_TOKEN        = Meta WhatsApp Cloud API token
  WHATSAPP_PHONE_ID     = WhatsApp Business Phone Number ID
  WHATSAPP_VERIFY_TOKEN = Webhook verify token
  WHATSAPP_APP_SECRET   = App secret (HMAC signature verification)

  ── REDIS ─────────────────────────────────────────────────────────────────────
  REDIS_URL             = redis://localhost:6379/0
                          (Upstash / Redis Cloud for managed deployments)

  ── SECURITY ──────────────────────────────────────────────────────────────────
  SECRET_KEY            = Flask session secret (auto-generated if omitted)
  ADMIN_API_KEY         = Legacy X-Admin-Key (backward compat only)
  ENCRYPTION_KEY        = 32-byte hex for AES-256-GCM PII encryption
                          python -c "import secrets; print(secrets.token_hex(32))"
  JWT_SECRET_KEY        = JWT signing secret (rotate regularly)
  JWT_EXPIRY_HOURS      = 24

  ── MULTI-REGION ──────────────────────────────────────────────────────────────
  REGION                = "us-east-1" | "eu-west-1" | "ap-south-1"  (optional)
  ENABLE_ANALYTICS      = true | false   (default: true)

  ── OBSERVABILITY ─────────────────────────────────────────────────────────────
  PORT                  = 5000
  DEBUG                 = false
  LOG_FORMAT            = "json" | "text"
  RATE_LIMIT_DEFAULT    = 200 per minute
  CACHE_TTL             = 600
  CHAT_HISTORY_LIMIT    = 20

  ── v10 ADDITIONS ─────────────────────────────────────────────────────────────
  GRAPH_API_VERSION     = v23.0   (Meta deprecates old versions — keep current)
  INSTAGRAM_TOKEN       = Page/IG access token with instagram_manage_messages
  INSTAGRAM_ID          = IG business account id (the recipient.id in webhooks)
  INSTAGRAM_APP_SECRET  = optional; falls back to WHATSAPP_APP_SECRET
  QDRANT_URL            = https://xxxx.cloud.qdrant.io  (Qdrant Cloud free tier OK)
  QDRANT_API_KEY        = Qdrant Cloud API key
  EMBED_MODEL           = models/gemini-embedding-001
  EMBED_DIMS            = 768
  RAG_TOP_K             = 3        RAG_MIN_SCORE = 0.55
  GHOST_MUTE_SECONDS    = 900   (AI silence after human takeover)
  RESPONSE_CACHE_TTL    = 900   (identical-question reuse; Redis-backed)
  OPENAI_TRANSCRIBE_MODEL = whisper-1  (voice fallback if Gemini audio fails)
"""

# ═════════════════════════════════════════════════════════════════════════════
# 🦅  v16 GEN-2 — ROUND-1 + ROUND-2 AUDIT CLOSE-OUT  (16 July 2026)
#     57 findings patched in place; every patch is tagged `v16g2 FIX <id>`
#     inline at the exact line it lands.
#       Round-1 (44): H1–H4 · M1–M15 · L1–L16 · C1–C9
#       Round-2 (13): N1–N13
#     Headliners:
#       • U3 capture: gated (H1) · post-routing (H2) · 15-min window + mostly-
#         number rule (H3) · country-coded (N2) · persisted (N8) · honest
#         wording when the scheduler is off (C8) · ask-guard burned only on
#         delivered ask (M14, on L1's real bool)
#       • "recorded-delivered-while-actually-dead" family closed: H4, M6, M7,
#         M8, M11 — plus N7 (past bookings finally complete → purge works)
#       • U5 remap: gate reaches classic events (M2) · stub-merge beats the
#         uq_crm_dedupe collision (N3) · enc_phone refreshed on classic number
#         change (N4) · sessions re-keyed + caches dropped (M3) · changed
#         BSUIDs self-heal on next message (L8)
#       • DPDP: erasure + consent resolve BSUID subjects by the number the
#         clinic actually holds and clear every Redis key (M4, M5, N9)
#       • Language: post-positioned Tamil/Hindi negation understood (N1) ·
#         dizziness out of the universal emergency list (M15) · "menu" freed
#         for restaurants (N6)
#       • Demo isolation: /chat can't page the owner or share RAG (M9, M10)
#     NO new features in this round — audit-fix rounds never mix with feature
#     rounds; that is how regressions are born. Feature work resumes GEN-3.
# ═════════════════════════════════════════════════════════════════════════════
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
import secrets                      # v16.9 R15-H2
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
# ⚙️  CONFIGURATION  (v8: adds replica URL, region tag, analytics toggle)
# ─────────────────────────────────────────────────────────────────────────────
def _env_int(name: str, default) -> int:
    """v16g3 FIX R3-L3: a typo'd numeric env (MAX_POOL_SIZE=abc) killed the
    boot with a bare ValueError mid-import — v15 FIX 25 gave only the hex key
    a friendly failure. Warn + default instead. (The logger isn't built yet at
    Config time, so this writes straight to stderr.)"""
    raw = os.getenv(name, "")
    try:
        return int(str(raw).strip()) if str(raw).strip() else int(default)
    except (TypeError, ValueError):
        sys.stderr.write(f"⚠️  HEONIX: env {name}={raw!r} is not a valid "
                         f"integer — using default {default}.\n")
        return int(default)


def _env_float(name: str, default) -> float:
    """v16g3 FIX R3-L3 (float twin of _env_int)."""
    raw = os.getenv(name, "")
    try:
        return float(str(raw).strip()) if str(raw).strip() else float(default)
    except (TypeError, ValueError):
        sys.stderr.write(f"⚠️  HEONIX: env {name}={raw!r} is not a valid "
                         f"number — using default {default}.\n")
        return float(default)


_ENV_BOOL_TRUE  = frozenset({"1", "true", "yes", "on"})
_ENV_BOOL_FALSE = frozenset({"0", "false", "no", "off"})


def _env_bool(name: str, default: bool) -> bool:
    """v16g4 FIX M1: env booleans previously split into TWO dialects —
    STRICT_PROD/SMOKE_TEST_ENABLED/REQUIRE_WEBHOOK_SIGNATURE/ENABLE_PHONE_CAPTURE
    accepted only "1" while ENABLE_BOOKING/ENABLE_SCHEDULER/FOLLOWUP_ENABLED/
    DEBUG/… accepted only "true". STRICT_PROD=true was silently OFF and
    ENABLE_BOOKING=1 silently OFF, with no warning either way. One parser now
    accepts both dialects (1/0, true/false, yes/no, on/off, case-insensitive),
    warns loudly on garbage, and treats empty/unset as the default — matching
    _env_int semantics."""
    raw = os.getenv(name)
    if raw is None or not str(raw).strip():
        return bool(default)
    val = str(raw).strip().lower()
    if val in _ENV_BOOL_TRUE:
        return True
    if val in _ENV_BOOL_FALSE:
        return False
    sys.stderr.write(f"⚠️  HEONIX: env {name}={raw!r} is not a valid boolean "
                     f"(use 1/0 or true/false) — using default {default}.\n")
    return bool(default)


# v16.9 FIX R15-H2: resolved once, before Config exists, because BOTH the
# WhatsApp and Instagram verify-token fields live inside the class body and
# neither can reference `cfg` yet. Unset ⇒ one random per-boot token, so a
# misconfigured webhook fails the handshake loudly instead of trusting the
# constant that used to be published in this file.
_WA_VERIFY_DEFAULT = os.getenv("WHATSAPP_VERIFY_TOKEN") or secrets.token_urlsafe(24)


class Config:
    # ── Database ──
    DATABASE_MODE: str          = os.getenv("DATABASE_MODE", "postgres")
    DATABASE_URL: str           = os.getenv("DATABASE_URL", "")
    DATABASE_REPLICA_URL: str   = os.getenv("DATABASE_REPLICA_URL", "")   # NEW v8
    DATABASE_FILE: str          = os.getenv("DATABASE_FILE", "heonix_ultra.db")  # v14g3 BUG 20: matches the docstring
    MAX_POOL_SIZE: int          = _env_int("MAX_POOL_SIZE", "20")

    # ── AI Keys ──
    GENAI_API_KEY: str          = os.getenv("GENAI_API_KEY", "")
    OPENAI_API_KEY: str         = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str      = os.getenv("ANTHROPIC_API_KEY", "")

    # ── AI Models ──
    GEMINI_MODEL: str           = os.getenv("GEMINI_MODEL",    "gemini-3.1-flash-lite")  # v11 #5: 2.5-flash retiring 2026; lite = 6x cheaper, chatbot-tuned
    # Per-customer premium model: pass plan_tier="premium" → uses GEMINI_MODEL_PREMIUM.
    GEMINI_MODEL_PREMIUM: str   = os.getenv("GEMINI_MODEL_PREMIUM", "gemini-3.5-flash")   # only worth it for tool-heavy/agentic clients
    OPENAI_MODEL: str           = os.getenv("OPENAI_MODEL",    "gpt-4o-mini")
    ANTHROPIC_MODEL: str        = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    AI_MAX_TOKENS: int          = _env_int("AI_MAX_TOKENS", "1000")
    # v16.3 FIX R9-C2 (ROOT CAUSE). gunicorn's DEFAULT worker timeout is 30s
    # and the start command sets no --timeout, so the old 30s AI budget raced
    # the worker reaper dead even. When Gemini ran slow — and it was already
    # visibly degrading at 5.6s and 9.5s per reply — gunicorn killed the worker
    # mid-request. A killed worker drops the socket with no HTTP status at all,
    # which is precisely the browser-side "Can't reach the engine" seen in the
    # red-team session, and why it looked like a crash from the payload rather
    # than a timeout. Budget now sits well under the worker timeout set in
    # gunicorn.conf.py, so the engine always wins the race and can return its
    # own graceful degraded reply instead of vanishing.
    AI_TIMEOUT_SECS: float      = _env_float("AI_TIMEOUT_SECS", "20")

    # ── WhatsApp Cloud API ──
    WHATSAPP_TOKEN: str         = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_ID: str      = os.getenv("WHATSAPP_PHONE_ID", "")
    # v16.9 FIX R15-H2: this defaulted to the literal "heonix_verify" — a
    # "secret" sitting in a file that lives in a public repo, so anyone who
    # read it could complete Meta's webhook handshake against this engine.
    # Unset now means a random per-boot value: webhook verification fails
    # loudly until the real token is configured, which is the safe direction.
    WHATSAPP_VERIFY_TOKEN: str  = _WA_VERIFY_DEFAULT      # v16.9 R15-H2
    WHATSAPP_APP_SECRET: str    = os.getenv("WHATSAPP_APP_SECRET", "")
    # v15g4 FIX C8: v21.0 (Oct-2024) is inside Meta's ~2-year deprecation
    # window. v23.0 keeps a fresh default; ALWAYS verify the live version in
    # the Meta changelog and pin it via env before launch.
    GRAPH_API_VERSION: str      = os.getenv("GRAPH_API_VERSION", "v23.0")   # v10 / v15g4 FIX C8
    # v19.0 R19-C1: booking on the /chat (api) channel. Default ON — the whole
    # point of the fix is that the demo runs the real state machine. Set to
    # false ONLY if you expose /chat publicly against a LIVE clinic brain, in
    # which case visitors can consume real slots (see the note on /chat).
    BOOKING_ON_API: bool        = _env_bool("BOOKING_ON_API", True)

    # ── Instagram Messaging API (v10) ──
    INSTAGRAM_TOKEN: str        = os.getenv("INSTAGRAM_TOKEN", "")
    INSTAGRAM_ID: str           = os.getenv("INSTAGRAM_ID", "")            # IG business account id
    INSTAGRAM_APP_SECRET: str   = os.getenv("INSTAGRAM_APP_SECRET", "")    # fallback: WHATSAPP_APP_SECRET

    # ── Redis ──
    REDIS_URL: str              = os.getenv("REDIS_URL", "")

    # ── Security ──
    ADMIN_API_KEY: str          = os.getenv("ADMIN_API_KEY", "")
    ENCRYPTION_KEY: str         = os.getenv("ENCRYPTION_KEY", "")
    # v15g2 FIX L9: unset JWT/Flask secrets used to default to a fresh uuid PER
    # PROCESS — under gunicorn -w N each worker minted its own, so admin JWTs and
    # Flask sessions broke non-deterministically across workers, and the v14g5
    # FIX 11 boot guard only fired when the WEB_CONCURRENCY env happened to be
    # set (gunicorn -w 4 without it sailed straight past). Now: if ENCRYPTION_KEY
    # exists (it must, for PII), derive a DETERMINISTIC secret from it — identical
    # in every worker — and fall back to per-process random only when there is
    # truly nothing shared to derive from. Explicit env values always win.
    SECRET_KEY: str             = (os.getenv("SECRET_KEY", "")
        or (hashlib.sha256(("heonix|flask|" + os.getenv("ENCRYPTION_KEY", ""))
                           .encode()).hexdigest()
            if os.getenv("ENCRYPTION_KEY") else uuid.uuid4().hex))
    JWT_SECRET_KEY: str         = (os.getenv("JWT_SECRET_KEY", "")
        or (hashlib.sha256((# v16.9 FIX R15-H1: JWT_SECRET_KEY was derived from ENCRYPTION_KEY, so one
        # leaked value gave an attacker PII decryption AND admin-token forgery
        # AND Flask session forgery from the same string. Domain separation
        # means a leak of one no longer implies the others; setting an explicit
        # JWT_SECRET_KEY env var (recommended) severs the link entirely.
        "heonix|jwt|v2|domain-separated|" + os.getenv("ENCRYPTION_KEY", ""))
                           .encode()).hexdigest()
            if os.getenv("ENCRYPTION_KEY") else uuid.uuid4().hex))
    JWT_EXPIRY_HOURS: int       = _env_int("JWT_EXPIRY_HOURS", "24")

    # ── Chat ──
    CHAT_HISTORY_LIMIT: int     = _env_int("CHAT_HISTORY_LIMIT", "20")
    MAX_MESSAGE_LEN: int        = _env_int("MAX_MESSAGE_LEN", "2000")

    # ── Rate Limits ──
    RATE_LIMIT_DEFAULT: str     = os.getenv("RATE_LIMIT_DEFAULT", "200 per minute")
    WEBHOOK_RATE_LIMIT: str     = os.getenv("WEBHOOK_RATE_LIMIT", "60 per minute")
    CHAT_RATE_LIMIT: str        = os.getenv("CHAT_RATE_LIMIT",    "120 per minute")
    ADMIN_RATE_LIMIT: str       = os.getenv("ADMIN_RATE_LIMIT",   "30 per minute")

    # ── Cache ──
    CACHE_TTL: int              = _env_int("CACHE_TTL", "600")

    # ── Retry ──
    # v15g4 FIX B7: default 3 → 1. Worst case was MAX_RETRIES × AI_TIMEOUT ×
    # 3 providers ≈ minutes of a patient staring at "typing…". One retry per
    # provider + the Gemini→OpenAI→Claude fallback chain is plenty of
    # resilience. Set MAX_RETRIES=3 in env to restore the old behaviour.
    MAX_RETRIES: int            = _env_int("MAX_RETRIES", "1")
    RETRY_BASE_DELAY: float     = _env_float("RETRY_BASE_DELAY", "1.0")

    # ── Observability ──
    LOG_FORMAT: str             = os.getenv("LOG_FORMAT", "json")
    REGION: str                 = os.getenv("REGION", "ap-south-1")         # NEW v8 / v16g4 FIX L6: India default
    ENABLE_ANALYTICS: bool      = _env_bool("ENABLE_ANALYTICS", True)   # v16g4 FIX M1

    # ── Server ──
    PORT: int                   = _env_int("PORT", "5000")
    DEBUG: bool                 = _env_bool("DEBUG", False)             # v16g4 FIX M1

    # ── v10: God-Logic / RAG / Voice ──
    GHOST_MUTE_SECONDS: int     = _env_int("GHOST_MUTE_SECONDS", "900")
    RESPONSE_CACHE_TTL: int     = _env_int("RESPONSE_CACHE_TTL", "900")
    QDRANT_URL: str             = os.getenv("QDRANT_URL", "")
    QDRANT_API_KEY: str         = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION: str      = os.getenv("QDRANT_COLLECTION", "heonix_memory")
    EMBED_MODEL: str            = os.getenv("EMBED_MODEL", "models/gemini-embedding-001")
    EMBED_DIMS: int             = _env_int("EMBED_DIMS", "768")
    RAG_TOP_K: int              = _env_int("RAG_TOP_K", "3")
    RAG_MIN_SCORE: float        = _env_float("RAG_MIN_SCORE", "0.55")
    OPENAI_TRANSCRIBE_MODEL: str = os.getenv("OPENAI_TRANSCRIBE_MODEL", "whisper-1")

    # ══ v14 Gen-4 — ADVANCED FEATURES (every flag defaults OFF) ════════════════
    # Gen-4 is purely ADDITIVE: with all flags off, the engine behaves EXACTLY
    # like Gen-3. Turn features on one at a time, after testing each live.
    #  Appointment booking + reminders
    ENABLE_BOOKING: bool        = _env_bool("ENABLE_BOOKING", False)    # v16g4 FIX M1
    # v32.0 R32-C1: the demo door, separate from every production door.
    # OFF by default — a public brain-minting path must be opted into, never
    # inherited. See /demo/provision for why this exists at all.
    ENABLE_DEMO_PROVISION: bool = _env_bool("ENABLE_DEMO_PROVISION", False)
    DEMO_RATE_LIMIT: str        = os.getenv("DEMO_RATE_LIMIT", "6 per hour")
    DEMO_TTL_HOURS: int         = _env_int("DEMO_TTL_HOURS", 48)
    BOOKING_SLOT_MINUTES: int   = _env_int("BOOKING_SLOT_MINUTES", "30")
    BOOKING_OPEN_HOUR: int      = _env_int("BOOKING_OPEN_HOUR", "9")    # local clinic hour
    BOOKING_CLOSE_HOUR: int     = _env_int("BOOKING_CLOSE_HOUR", "18")  # local clinic hour
    BOOKING_DAYS_AHEAD: int     = _env_int("BOOKING_DAYS_AHEAD", "5")
    BOOKING_SLOTS_SHOWN: int    = _env_int("BOOKING_SLOTS_SHOWN", "6")
    BOOKING_TZ_OFFSET_MIN: int  = _env_int("BOOKING_TZ_OFFSET_MIN", "330")  # IST +5:30
    BOOKING_WEEKDAYS: str       = os.getenv("BOOKING_WEEKDAYS", "0,1,2,3,4,5")     # Mon=0..Sun=6
    #  Background scheduler (reminders / follow-ups / retention) — needs a
    #  long-lived process (true on Render web service; NOT on serverless).
    ENABLE_SCHEDULER: bool      = _env_bool("ENABLE_SCHEDULER", False)  # v16g4 FIX M1
    REMINDER_LEAD_HOURS: str    = os.getenv("REMINDER_LEAD_HOURS", "24,2")         # csv hours-before
    FOLLOWUP_ENABLED: bool      = _env_bool("FOLLOWUP_ENABLED", False)  # v16g4 FIX M1
    FOLLOWUP_AFTER_HOURS: int   = _env_int("FOLLOWUP_AFTER_HOURS", "24")
    FOLLOWUP_MAX_AGE_HOURS: int = _env_int("FOLLOWUP_MAX_AGE_HOURS", "168")  # don't chase >7d-old
    DATA_RETENTION_DAYS: int    = _env_int("DATA_RETENTION_DAYS", "0")       # 0 = keep forever
    #  Image understanding (uses your existing Gemini key — already multimodal)
    ENABLE_IMAGE_UNDERSTANDING: bool = _env_bool("ENABLE_IMAGE_UNDERSTANDING", False)  # v16g4 FIX M1
    #  Scheduled sends (reminders/follow-ups) outside WhatsApp's 24-hour customer
    #  service window REQUIRE a pre-approved template. If you set these to an
    #  approved template name, the scheduler sends via template (reliable). If
    #  left blank, it sends free text — which Meta only delivers INSIDE 24h.
    REMINDER_TEMPLATE: str      = os.getenv("REMINDER_TEMPLATE", "")
    REMINDER_TEMPLATE_LANG: str = os.getenv("REMINDER_TEMPLATE_LANG", "en")
    FOLLOWUP_TEMPLATE: str      = os.getenv("FOLLOWUP_TEMPLATE", "")
    FOLLOWUP_TEMPLATE_LANG: str = os.getenv("FOLLOWUP_TEMPLATE_LANG", "en")

    # ── v11 ──
    # #4: free-form WhatsApp texts to the OWNER are blocked by Meta outside
    # the 24-hour window (error 131047) — an emergency alert could silently
    # die. Create ONE approved utility template with a single {{1}} body
    # parameter (e.g. name it "heonix_owner_alert", body: "{{1}}") and set:
    # v16.5 R11-H1: booking alerts mask the patient number by default, matching
    # every other owner alert in this file. A clinic running the AI on a SEPARATE
    # line has no patient chat to look the number up in, so they can flip this —
    # deliberately opt-in, because it puts patient PII into a WhatsApp thread.
    # v16.6 R12-H1: a CAP, deliberately not a hard "one booking per number".
    # One number legitimately books for a family — a mother holding slots for
    # two children, a follow-up booked alongside a checkup. Blocking the second
    # booking would break real patients to stop a rare prankster. Three lets
    # families through and still stops anyone hoarding a clinic's day.
    MAX_ACTIVE_BOOKINGS_PER_PHONE: int = min(50, max(1,
        _env_int("MAX_ACTIVE_BOOKINGS_PER_PHONE", 3)))
    OWNER_ALERT_FULL_PHONE: bool   = _env_bool("OWNER_ALERT_FULL_PHONE", False)
    OWNER_ALERT_TEMPLATE: str      = os.getenv("OWNER_ALERT_TEMPLATE", "")
    OWNER_ALERT_TEMPLATE_LANG: str = os.getenv("OWNER_ALERT_TEMPLATE_LANG", "en")
    # #2: set STRICT_PROD=1 to REFUSE booting without Postgres + Redis
    # (recommended once live — prevents the silent SQLite/in-process fallback
    # that breaks dedupe + ghost-mute across gunicorn workers).
    STRICT_PROD: bool              = _env_bool("STRICT_PROD", False)       # v16g4 FIX M1
    # v16g5 FIX R5-M11: promoted out of a raw per-import os.getenv into cfg,
    # like every other setting. Comma-separated origins; empty = dev wildcard
    # (refused under STRICT_PROD).
    CORS_ORIGINS: str              = os.getenv("CORS_ORIGINS", "").strip()

    # ── v12 ── (hyper-scale / concurrency hardening)
    # JSON-bomb guard (#37): reject oversized request bodies before they hit RAM.
    MAX_CONTENT_BYTES: int         = _env_int("MAX_CONTENT_BYTES", 1 * 1024 * 1024)  # 1 MB
    # RAM-nuke guard (#7/#16): never pull a media file bigger than this into memory.
    MEDIA_MAX_BYTES: int           = _env_int("MEDIA_MAX_BYTES", 16 * 1024 * 1024)  # 16 MB
    # Network timeouts as (connect, read) tuples (#39): a frozen socket can no
    # longer pin a background thread forever.
    HTTP_CONNECT_TIMEOUT: float    = _env_float("HTTP_CONNECT_TIMEOUT", "5")
    MEDIA_READ_TIMEOUT: float      = _env_float("MEDIA_READ_TIMEOUT", "30")
    # RAG soft timeout (#9/#23): embedding + vector search are bounded so Qdrant
    # or the embedding endpoint hanging can't wedge the whole reply path.
    RAG_TIMEOUT_SECS: float        = _env_float("RAG_TIMEOUT_SECS", "6")
    # Pool-explosion guard (#34): workers × MAX_POOL_SIZE must stay under the
    # database's own connection ceiling. Render free Postgres ~= 97; leave headroom.
    DB_MAX_CONNECTIONS: int        = _env_int("DB_MAX_CONNECTIONS", "90")
    WEB_CONCURRENCY: int           = _env_int("WEB_CONCURRENCY", "1")
    # Meta send retries (#36): only transient/5xx/429 are retried (see _meta_send_retry).
    META_SEND_RETRIES: int         = _env_int("META_SEND_RETRIES", "2")
    # /metrics COUNT(*) cache (#10): a Prometheus scrape storm can't hammer the DB.
    METRICS_CACHE_TTL: int         = _env_int("METRICS_CACHE_TTL", "30")

    # ── v13 ── (TRUE MULTI-TENANT — per-clinic creds, token-death self-heal)
    # When a clinic's own WhatsApp/Instagram token dies (Meta code 190/401), the
    # engine flags that clinic needs_reauth and pings THIS number so you re-attach
    # before the clinic notices. Uses the GLOBAL token to send the alert.
    ADMIN_ALERT_PHONE: str         = os.getenv("ADMIN_ALERT_PHONE", "")
    # Routing cache TTL for phone_number_id → brain (seconds). 10 min is plenty;
    # channel edits bust the key immediately, so staleness is bounded.
    ROUTE_CACHE_TTL: int           = _env_int("ROUTE_CACHE_TTL", "600")
    # Allow the onboarding smoke-test endpoint to send ONE real test WhatsApp to a
    # number you pass in. Off by default so it can never be abused to fan out spam.
    # v15 FIX 12: this comment always said "off by default" — the code said ON.
    # Now they agree. ⚠️ Set SMOKE_TEST_ENABLED=1 in Render env — you USE this.
    SMOKE_TEST_ENABLED: bool       = _env_bool("SMOKE_TEST_ENABLED", False)  # v16g4 FIX M1

    # ── v14 Gen-3 ── (hardening pass — see the CHANGELOG header at top of file)
    # BUG 7: force webhook signature verification even when STRICT_PROD is off.
    REQUIRE_WEBHOOK_SIGNATURE: bool = _env_bool("REQUIRE_WEBHOOK_SIGNATURE", False)  # v16g4 FIX M1
    # BUG 14: the audit trail no longer rides on ENABLE_ANALYTICS — its own switch
    # so you can mute metrics without silently losing the SOC2/GDPR audit log.
    ENABLE_AUDIT: bool             = _env_bool("ENABLE_AUDIT", True)     # v16g4 FIX M1
    # BUG 11: country code assumed for a bare 10-digit national number (India=91)
    # when minting the stable customer_id, so +1 / +44 / … can't collide on the
    # last 10 digits and overwrite each other's brain.
    DEFAULT_COUNTRY_CODE: str      = os.getenv("DEFAULT_COUNTRY_CODE", "91")

    # ── v14 Gen-5 ── (audit fixes — 50 findings closed; see header)
    # FIX 35: a separate Instagram webhook verify token (falls back to the WA one).
    INSTAGRAM_VERIFY_TOKEN: str    = (os.getenv("INSTAGRAM_VERIFY_TOKEN", "")
                                      or _WA_VERIFY_DEFAULT)   # R15-H2
    # FIX 23: optional token to gate /metrics so counts aren't public recon.
    METRICS_TOKEN: str             = os.getenv("METRICS_TOKEN", "")
    # FIX 10: gate the "route any unknown number to the only clinic" guess.
    SINGLE_TENANT_FALLBACK: bool   = _env_bool("SINGLE_TENANT_FALLBACK", True)  # v16g4 FIX M1
    # FIX 6: cross-worker per-conversation mutex TTL (must exceed a slow AI turn).
    CONV_LOCK_TTL: int             = _env_int("CONV_LOCK_TTL", "60")
    # FIX 7: single-leader scheduler lock TTL (~ the 5-min cadence, just under it).
    SCHED_LOCK_TTL: int            = _env_int("SCHED_LOCK_TTL", "290")

    # ── v15 ── (26-finding independent audit close-out; see header changelog)
    # FIX 5: optional API key for POST /chat. customer_id is derivable from a
    # clinic's PUBLIC WhatsApp number ("HX_WA_" + digits), so an open /chat
    # lets anyone burn your Gemini quota and probe the persona. Unset = open
    # (dev) with a loud startup warning; STRICT_PROD fail-closes the endpoint.
    CHAT_API_KEY: str              = os.getenv("CHAT_API_KEY", "")

    # ── v15 Gen-4 ── (round-4 launch-readiness audit; see header changelog)
    # FIX A4: a keyword "talk to doctor/manager" request muted the AI for the
    # full GHOST_MUTE_SECONDS (15 min) — at a clinic that phrase is routine,
    # so the bot went dark constantly. Keyword-based handoffs now use this
    # shorter lease; the AI-escalation path keeps the full ghost mute.
    HUMAN_REQUEST_MUTE_SECONDS: int = _env_int("HUMAN_REQUEST_MUTE_SECONDS", "300")
    # FIX B9: wamid/igmid dedupe claims lived only 600s — a Meta redelivery
    # later than that was reprocessed and DOUBLE-replied. 6h default.
    DEDUPE_TTL_SECONDS: int         = _env_int("DEDUPE_TTL_SECONDS", "21600")
    # FIX D2: how long a drain waits for the cross-worker conversation lease
    # before proceeding without it (documented interleave tradeoff).
    CONV_LOCK_WAIT_SECS: float      = _env_float("CONV_LOCK_WAIT_SECS", "5")

    # ── v16 ── WhatsApp Usernames / BSUID (see header changelog)
    # U3: when a username-only patient books, ask once for their real number
    # (reminders + clinic records). Set 0 to disable the ask entirely —
    # BSUID-addressed sends still work either way.
    ENABLE_PHONE_CAPTURE: bool      = _env_bool("ENABLE_PHONE_CAPTURE", True)  # v16g4 FIX M1
    # U3: the interactive request-button type/action strings. Defaults follow
    # Meta's location_request_message naming pattern; VERIFY against the
    # current Cloud API docs when the button GAs in your region — a mismatch
    # is harmless (the send 400s and the engine falls back to a plain-text
    # ask; typed-number capture handles the reply either way).
    WA_PHONE_REQUEST_TYPE: str      = os.getenv("WA_PHONE_REQUEST_TYPE",
                                                "phone_number_request_message")
    WA_PHONE_REQUEST_ACTION: str    = os.getenv("WA_PHONE_REQUEST_ACTION",
                                                "send_phone_number")

    # ── v16 Gen-4 ── (round-4 audit close-out — 50 findings; see header)
    # FIX L8: TALLY_WEBHOOK_SECRET was the one config value read via a raw
    # os.getenv per request inside verify_tally_signature — now it lives in
    # cfg like every other secret (and the boot summary can see it: FIX H4).
    TALLY_WEBHOOK_SECRET: str       = os.getenv("TALLY_WEBHOOK_SECRET", "")
    # FIX H1: the onboarding welcome is BUSINESS-INITIATED — the clinic owner
    # has never messaged the WABA line, so free text is rejected by Meta 100%
    # of the time (131047-class: no open 24h session). The welcome MUST go via
    # a pre-approved template. Create one utility template with a single {{1}}
    # body parameter (suggested name "heonix_welcome", body: "{{1}}"), get it
    # approved in Meta Business Manager, then set:
    WELCOME_TEMPLATE: str           = os.getenv("WELCOME_TEMPLATE", "")
    WELCOME_TEMPLATE_LANG: str      = os.getenv("WELCOME_TEMPLATE_LANG", "en")
    # FIX M13: ADMIN_API_KEY is a permanent, unrotatable env superadmin. In
    # STRICT_PROD it is now refused unless you explicitly acknowledge the risk
    # with ADMIN_API_KEY_LEGACY_OK=1 (JWT admin login is the supported path).
    ADMIN_API_KEY_LEGACY_OK: bool   = _env_bool("ADMIN_API_KEY_LEGACY_OK", False)
    # FIX M8: default language for system-authored strings (booking prompts,
    # phone request, cancel confirms) when the patient's own script can't be
    # detected. Per-message detection still wins; this is only the fallback.
    DEFAULT_LANG: str               = os.getenv("DEFAULT_LANG", "en")


cfg = Config()

# v16g4 FIX L7: the detailed build banner — shown only to DEBUG or a caller
# holding METRICS_TOKEN; the anonymous landing page says just "HEONIX".
# v16g6 FIX R6-L1: FOUR version identities lived in one build (this banner
# said GEN-4, /health said GEN-3, the shutdown log said GEN-3, the startup
# banner said GEN-5). After a hotfix night, /health is the one thing that
# must be trusted to say which build is live. One constant; all derive.
ENGINE_VERSION = "v34.0"   # R34
ENGINE_GEN     = "GEN-6"
ENGINE_BANNER  = (f"HEONIX ULTRA ENGINE {ENGINE_VERSION} {ENGINE_GEN} "
                  f"(Usernames/BSUID · 182 audit fixes)")


# ─────────────────────────────────────────────────────────────────────────────
# 🪵  STRUCTURED LOGGING  (JSON by default — Datadog/CloudWatch/Loki friendly)
# ─────────────────────────────────────────────────────────────────────────────
class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts":     datetime.now(timezone.utc).isoformat(),
            "level":  record.levelname,
            "logger": record.name,
            "region": cfg.REGION,
            "msg":    record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if cfg.DEBUG else logging.INFO)
    # v27.0 · FIX R27-C1. The comment below said "stdout ONLY" and the block
    # under it says Render captures stdout "so that is the single source of
    # truth" — but logging.StreamHandler() with no argument defaults to
    # STDERR. Measured on a plain boot of v26: stdout 0 lines, stderr 2.
    # Render captures both, so nothing was lost there; anywhere that ships
    # stdout only — a `gunicorn … | logshipper` pipe, a container runtime
    # that splits the streams, a structured-log ingest configured for stdout —
    # received NOTHING. That is the entire 🛑 detection surface: R18-H1's
    # database-mode warning, R20-C1's missing constraint, R26-C1's zombie
    # booking. Detectors built over nine rounds, all writing to a stream the
    # code says it does not use. Same class as R18-H1 itself: a stated intent
    # that was never implemented, believed for sixteen versions because the
    # comment read true.
    handler = logging.StreamHandler(sys.stdout)   # v11 fix #12 · v27 R27-C1
    fmt = _JSONFormatter() if cfg.LOG_FORMAT == "json" else logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(fmt)
    # v11 fix #12: dropped FileHandler. On Render the disk is ephemeral, two
    # workers fought over the same file, and it grew unbounded. Render/Railway/
    # Fly all capture stdout, so that is the single source of truth.
    logger.addHandler(handler)
    logger.propagate = False
    return logger


log = _build_logger("HEONIX")   # v11 fix #15: was "HEONIX_V8"


# ─────────────────────────────────────────────────────────────────────────────
# 🔐  AES-256-GCM PII VAULT  (DPDP + HIPAA + GDPR)
# ─────────────────────────────────────────────────────────────────────────────
class PIIVault:
    """
    AES-256-GCM authenticated encryption for PII fields.
    Each field gets a unique 96-bit nonce so identical values encrypt differently.
    Designed with DPDP-style controls (encryption at rest, opt-out,
    right-to-erasure endpoints). v33 R33-C1: this is a description of
    implemented CONTROLS, not a claim of certification under any law.
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


# ─────────────────────────────────────────────────────────────────────────────
# 🔑  JWT AUTH + RBAC
# ─────────────────────────────────────────────────────────────────────────────
ROLES = {"superadmin", "admin", "viewer"}
_ROLE_RANK = {"viewer": 0, "admin": 1, "superadmin": 2}
# v16g5 FIX R5-L3: issuer/audience binding for admin JWTs.
_JWT_ISS = "heonix-engine"
_JWT_AUD = "heonix-admin"


def _tenant_forbidden(customer_id: str) -> bool:
    """v16g4 FIX M10: True when the current JWT is tenant-scoped and the
    requested customer_id is not its tenant. For endpoints that carry
    customer_id in the body or query string (the path-param case is enforced
    centrally in require_jwt)."""
    u = getattr(g, "jwt_user", None) or {}
    tnt = u.get("tnt", "")
    return bool(tnt and u.get("role") != "superadmin"
                and customer_id and customer_id != tnt)


def generate_jwt(user_id: str, role: str = "admin", tenant: str = "") -> str:
    if not JWT_AVAILABLE:
        return ""
    payload = {
        "sub":  user_id,
        "role": role,
        "iat":  datetime.now(timezone.utc),
        "exp":  datetime.now(timezone.utc) + timedelta(hours=cfg.JWT_EXPIRY_HOURS),
        "jti":  uuid.uuid4().hex,
        "rgn":  cfg.REGION,
        # v16g5 FIX R5-L3: bind the token to this issuer/audience so a token
        # minted by another HEONIX deployment sharing an ENCRYPTION_KEY-derived
        # secret cannot be replayed here.
        "iss":  _JWT_ISS,
        "aud":  _JWT_AUD,
    }
    if tenant:                       # v16g4 FIX M10: tenant-scoped admin token
        payload["tnt"] = tenant
    return pyjwt.encode(payload, cfg.JWT_SECRET_KEY, algorithm="HS256")


def revoke_jwt(jti: str, ttl: int = 0) -> None:
    """v16g5 FIX R5-L3: add a token id to the denylist until its natural
    expiry. Backed by the shared cache, so a revoke lands fleet-wide on Redis
    (and process-locally in dev). This is what makes /admin/logout real —
    before this a leaked admin token stayed valid for the full expiry window
    with no way to kill it."""
    if not jti:
        return
    try:
        brain_cache.set(f"jwtban:{jti}", "1",
                        ttl=ttl or (cfg.JWT_EXPIRY_HOURS * 3600))
    except Exception as exc:
        log.warning(f"\u26a0\ufe0f  JWT revoke failed for {jti[:8]}: {exc}")


def decode_jwt(token: str) -> Optional[Dict]:
    if not JWT_AVAILABLE:
        return None
    try:
        # v16g6 FIX R6-M9: passing issuer= makes PyJWT raise
        # MissingRequiredClaimError when `iss` is ABSENT — the exact legacy
        # token the R5-L3 comment promised to tolerate — and the broad
        # InvalidTokenError catch below turned that into None, logging every
        # pre-R5 admin out after all. iss/aud are verified MANUALLY just
        # below: strict when present, tolerated when absent, exactly as
        # documented.
        payload = pyjwt.decode(
            token, cfg.JWT_SECRET_KEY, algorithms=["HS256"],
            options={"require": ["exp"], "verify_aud": False})
        _iss = payload.get("iss")
        _aud = payload.get("aud")
        if (_iss and _iss != _JWT_ISS) or (_aud and _aud != _JWT_AUD):
            return None
        # Denylist check (revoked / logged out).
        _jti = payload.get("jti", "")
        if _jti:
            try:
                if brain_cache.get(f"jwtban:{_jti}"):
                    return None
            except Exception as _rex:
                # v16g6 FIX R6-M10: still fail OPEN (401ing every request on
                # a Redis blip is worse than honouring a token for one gap) —
                # but LOUDLY. With /admin/logout live (R6-C5), silence here
                # means a banned token quietly works again. Counter + a
                # once-per-5-min alarm make the gap visible; in no-Redis mode
                # a revoke is per-worker by construction (ops constraint,
                # STRICT_PROD requires Redis anyway).
                try:
                    analytics.inc("jwt.revocation_check_failed")
                    if brain_cache.setnx("warn:jwtban_check", ttl=300):
                        log.error(f"❌ JWT revocation check UNAVAILABLE — "
                                  f"revoked tokens may be honoured: {_rex}")
                except Exception:
                    pass
        return payload
    except pyjwt.InvalidTokenError:   # v14g3 BUG 19: ExpiredSignatureError \u2282 InvalidTokenError
        return None


def require_jwt(min_role: str = "admin"):
    """Decorator: validates Bearer JWT and enforces minimum role hierarchy."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Legacy X-Admin-Key backward compat.
            # v16g4 FIX M13: this header is a permanent, unrotatable env
            # superadmin. In STRICT_PROD it is refused unless explicitly
            # acknowledged via ADMIN_API_KEY_LEGACY_OK=1 (JWT login is the
            # supported path), and the audit actor now carries a fingerprint
            # of the key so a rotation is visible in the audit trail instead
            # of every row reading the same anonymous 'legacy_admin'.
            if cfg.ADMIN_API_KEY and (not cfg.STRICT_PROD
                                      or cfg.ADMIN_API_KEY_LEGACY_OK):
                try:
                    # v16g2 FIX L6: a non-ASCII header value made compare_digest
                    # raise TypeError → 500. Garbage input is just a 401.
                    _hdr_ok = hmac.compare_digest(
                        request.headers.get("X-Admin-Key", ""),
                        cfg.ADMIN_API_KEY)   # v14g5 FIX 19: constant-time
                except (TypeError, UnicodeError):
                    _hdr_ok = False
                if _hdr_ok:
                    _fp = hashlib.sha256(cfg.ADMIN_API_KEY.encode()).hexdigest()[:8]
                    g.jwt_user = {"sub": f"legacy_admin:{_fp}",
                                  "role": "superadmin"}
                    return func(*args, **kwargs)

            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "Missing Authorization header"}), 401

            payload = decode_jwt(auth.split(" ", 1)[1])
            if not payload:
                return jsonify({"error": "Invalid or expired token"}), 401

            user_role = payload.get("role", "viewer")
            if _ROLE_RANK.get(user_role, -1) < _ROLE_RANK.get(min_role, 99):
                return jsonify({"error": f"Insufficient permissions. Required: {min_role}"}), 403

            # v16g4 FIX M10: central tenant fence. A token minted with a "tnt"
            # claim (non-superadmin) can only act on ITS clinic — enforced here
            # for every route with a customer_id path param, so no endpoint can
            # forget the check. Endpoints that take customer_id in body/query
            # call _tenant_forbidden() explicitly.
            _tnt = payload.get("tnt", "")
            if (_tnt and user_role != "superadmin"
                    and "customer_id" in kwargs
                    and kwargs["customer_id"] != _tnt):
                return jsonify({"error": "Token is scoped to a different "
                                         "tenant"}), 403

            g.jwt_user = payload
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# 📊  REAL-TIME ANALYTICS ENGINE  (v8 FIX #5 — event counters + latency P99)
# ─────────────────────────────────────────────────────────────────────────────
class AnalyticsEngine:
    """
    Lock-guarded IN-PROCESS analytics — per gunicorn worker, with NO cross-worker
    Redis sync. v16g2 FIX M12: the old docstring promised "Redis sync every 60 s"
    (and "Lock-free" while using a Lock) — no such code exists anywhere in this
    file. Under -w N, /metrics and /admin/analytics reflect whichever worker
    served the scrape; ops must not treat the split numbers as fleet totals.
    Tracks: requests, errors, AI provider usage, latency histograms.
    Exported on GET /metrics (Prometheus-compatible).
    """

    def __init__(self):
        self._lock     = threading.Lock()
        self._counters: Dict[str, int]         = defaultdict(int)
        self._latencies: Dict[str, deque]      = defaultdict(lambda: deque(maxlen=1000))
        self._started  = time.monotonic()

    def inc(self, key: str, n: int = 1) -> None:
        with self._lock:
            self._counters[key] += n

    def record_latency(self, key: str, ms: float) -> None:
        with self._lock:
            self._latencies[key].append(ms)

    def get_counter(self, key: str) -> int:
        with self._lock:
            return self._counters.get(key, 0)   # v14g5 FIX 29: don't auto-create probed keys

    def _percentile_nolock(self, key: str, pct: float = 0.99) -> float:
        # v14g3 BUG 1: the caller already holds self._lock. threading.Lock is
        # NOT reentrant, so any method invoked while the lock is held must not
        # try to re-acquire it. This no-lock variant is the safe inner core.
        data = sorted(self._latencies[key])
        if not data:
            return 0.0
        # v16g4 FIX L2: int(n*pct)-1 under-reported on small n — p99 of 10
        # samples returned the 9th value, not the max. Ceiling-based nearest-
        # rank: p99 of 10 → ceil(9.9)=10 → index 9 → the true max.
        idx = min(len(data) - 1, max(0, math.ceil(len(data) * pct) - 1))
        return round(data[idx], 2)

    def percentile(self, key: str, pct: float = 0.99) -> float:
        with self._lock:
            if key not in self._latencies:   # v15 FIX 18: twin of v14g5 FIX 29 —
                return 0.0                   # bracket access on a defaultdict
            return self._percentile_nolock(key, pct)

    def snapshot(self) -> Dict:
        # v14g3 BUG 1 FIX (CRITICAL): the old body did
        #     latency_p99 = {k: self.percentile(k) for k in self._latencies}
        # INSIDE `with self._lock`, and percentile() then re-acquired the SAME
        # non-reentrant lock → the thread blocked forever waiting on a lock it
        # already held. Every Prometheus scrape of /metrics (and every hit to
        # /admin/analytics) permanently hung a gunicorn worker. Now we compute
        # percentiles with the no-lock variant while holding the lock once.
        with self._lock:
            counters    = dict(self._counters)
            latency_p99 = {k: self._percentile_nolock(k) for k in self._latencies}
        uptime_s = time.monotonic() - self._started
        return {
            "counters":    counters,
            "latency_p99": latency_p99,
            "uptime_secs": round(uptime_s, 1),
        }


analytics = AnalyticsEngine()


# ─────────────────────────────────────────────────────────────────────────────
# 🏊  DATABASE LAYER  — Primary write pool + optional read-replica pool
#     v8 FIX #4: read replicas for horizontal read scaling
# ─────────────────────────────────────────────────────────────────────────────
def _pg_conn_alive(conn) -> bool:
    """v31.0 R31-C1: cheap liveness probe for a pooled Postgres handle.

    Deliberately catches EVERYTHING. A handle that cannot answer SELECT 1 for
    ANY reason is unusable, and the whole point is to fail here — cheaply,
    before the caller's real work — rather than in the middle of it."""
    if getattr(conn, "closed", 0):
        return False
    try:
        _prev = conn.autocommit
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.autocommit = _prev
        return True
    except Exception:
        return False


class PostgreSQLPool:
    """
    Production PostgreSQL pool via psycopg2.
    v8 adds optional read-replica pool for SELECT queries.
    """

    def __init__(self, dsn: str, min_conn: int = 2, max_conn: int = 20,
                 replica_dsn: str = ""):
        if not POSTGRES_AVAILABLE:
            raise RuntimeError("psycopg2 not installed. pip install psycopg2-binary")
        # v16g4 FIX HF3 (hotfix, 20-Jul): managed Postgres (Render/Neon)
        # closes idle TLS connections; a stale pooled handle then dies on
        # next use with "SSL SYSCALL error: EOF" / "bad record mac" — the H5
        # self-heal already discards them, but keepalives stop most handles
        # from going stale in the first place.
        _ka = dict(keepalives=1, keepalives_idle=30,
                   keepalives_interval=10, keepalives_count=3)
        self._write = psycopg2.pool.ThreadedConnectionPool(
            minconn=min_conn, maxconn=max_conn, dsn=dsn, **_ka)
        self._read  = None
        if replica_dsn:
            try:
                self._read = psycopg2.pool.ThreadedConnectionPool(
                    minconn=2, maxconn=max_conn, dsn=replica_dsn, **_ka)
                log.info("🐘 PostgreSQL read-replica pool ready.")
            except Exception as exc:
                log.warning(f"⚠️  Read replica unavailable ({exc}) — reads use primary.")
        log.info(f"🐘 PostgreSQL write pool ready — min={min_conn} max={max_conn}")

    @contextmanager
    def get(self, read_only: bool = False) -> Generator:
        pool = (self._read or self._write) if read_only else self._write
        # ── v31.0 · FIX R31-C1 — VALIDATE ON CHECKOUT ────────────────────
        # The v16g4 FIX H5 self-heal below discards a poisoned handle AFTER
        # the caller has already failed on it. That is one round too late for
        # anything that does not retry, and _process_outbox does not retry —
        # it logs "Outbox claim error" and returns, so a single dead handle
        # costs the whole tick and the outbox never drains.
        #
        # Managed Postgres (Render free tier) ends idle SESSIONS server-side.
        # TCP keepalives, which this pool already sets, keep the SOCKET alive
        # and cannot prevent that; the pool then hands out handles the backend
        # has forgotten. Reproduced deterministically with
        # pg_terminate_backend: with min_conn=2, the first TWO checkouts raise
        # and the third succeeds — which is exactly the production signature,
        # two failures ~1s apart inside one janitor tick, then silence until
        # the next tick 19-20s later.
        #
        # So: ping before yielding, and replace anything that does not answer.
        # One extra round-trip per checkout, ~1ms on the same host. Bounded to
        # three attempts so a genuinely unreachable database still surfaces its
        # real error to the caller instead of spinning here.
        conn = None
        for _ping_try in range(3):
            _cand = pool.getconn()
            if _pg_conn_alive(_cand):
                conn = _cand
                break
            log.info("\u267b\ufe0f  PG pool: dead handle replaced on checkout "
                     "(server-side session ended).")
            try:
                pool.putconn(_cand, close=True)
            except Exception:
                try:
                    _cand.close()
                except Exception:
                    pass
        if conn is None:
            # Every candidate failed the ping. Do not swallow it — hand the
            # caller a real connection attempt so the true error is raised.
            conn = pool.getconn()
        # v14g5 FIX 41: read paths use autocommit so pure SELECTs don't churn an
        # empty COMMIT every call; write paths keep explicit transaction control.
        conn.autocommit = bool(read_only)
        # v16g4 FIX H5: the v15g3 FIX 4 poisoned-connection self-heal was
        # SQLite-only. Here: if commit raised and rollback ALSO raised, the
        # broken handle was still putconn()'d back into the pool for the next
        # caller — and psycopg2's own putconn() runs a rollback that can raise
        # *from the finally*, masking the original error. Now: rollback is
        # best-effort; a connection whose rollback failed (or that reports
        # closed) is marked poisoned and returned with close=True so the pool
        # discards it and opens a fresh one; putconn itself is wrapped so a
        # putconn failure can never shadow the real exception.
        poisoned = False
        try:
            yield conn
            if not read_only:
                conn.commit()
        except Exception:
            if not read_only:
                try:
                    conn.rollback()
                except Exception as rb_exc:
                    poisoned = True
                    log.error(f"🛑 PG rollback failed on poisoned connection "
                              f"— discarding handle: {rb_exc}")
            raise
        finally:
            try:
                if getattr(conn, "closed", 0):
                    poisoned = True
                pool.putconn(conn, close=poisoned)
            except Exception as put_exc:
                # Never let pool bookkeeping mask the caller's exception.
                log.error(f"🛑 PG putconn failed (handle dropped): {put_exc}")
                try:
                    conn.close()
                except Exception:
                    pass

    def close_all(self) -> None:
        self._write.closeall()
        if self._read:
            self._read.closeall()
        log.info("🐘 PostgreSQL pools closed.")


class SQLitePool:
    """SQLite pool — dev/demo. WAL mode for better concurrency."""

    def __init__(self, db_path: str, pool_size: int = 10, timeout: float = 5.0):
        self._path    = db_path
        self._timeout = timeout
        self._pool: queue.Queue[sqlite3.Connection] = queue.Queue(maxsize=pool_size)
        for _ in range(pool_size):
            self._pool.put(self._new_conn())
        log.warning("⚠️  SQLite mode — single-server only. Set DATABASE_URL for PostgreSQL.")

    def _new_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA cache_size=-32000;")
        conn.execute("PRAGMA busy_timeout=5000;")
        return conn

    @contextmanager
    def get(self, read_only: bool = False) -> Generator:
        try:
            conn = self._pool.get(timeout=self._timeout)
        except queue.Empty:
            raise RuntimeError("SQLite pool exhausted")
        # v15g3 FIX 4 (MED): if commit/rollback themselves raised (disk I/O error,
        # interrupted WAL, closed handle) the OLD finally put the now-POISONED
        # connection straight back into the pool — every future borrower of that
        # slot then failed forever. On the SQLite path (what production runs on
        # Render TODAY) one bad write could brick 1/10th of all DB traffic until
        # restart. Now a connection that fails commit AND rollback is closed and
        # replaced with a fresh one, so the pool self-heals.
        broken = False
        try:
            yield conn
            # v16g5 FIX R5-L6: read_only was accepted and IGNORED, so every
            # SELECT ended in a COMMIT — pointless WAL churn and a write-lock
            # acquisition for a pure read on the path production runs today.
            if read_only:
                conn.rollback()
            else:
                conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                broken = True
            raise
        finally:
            if broken:
                try:
                    conn.close()
                except Exception:
                    pass
                try:
                    self._pool.put(self._new_conn())
                    log.warning("♻️  SQLite pool: poisoned connection replaced.")
                except Exception:
                    # v16g2 FIX N11: the old last-resort put the just-CLOSED
                    # handle back — that slot then failed forever ("Cannot
                    # operate on a closed database"), resurrecting the exact
                    # poisoned-slot bug this block exists to fix. Replenish in
                    # the background instead; a briefly smaller pool beats a
                    # permanently broken slot. (Correlated failure is the real
                    # case here: disk-full breaks rollback AND _new_conn.)
                    log.critical("🛑 SQLite pool: could not create a replacement "
                                 "connection — replenishing in background.")
                    def _replenish(_p=self._pool, _new=self._new_conn):
                        for _ in range(30):
                            time.sleep(2)
                            try:
                                _p.put(_new())
                                log.warning("♻️  SQLite pool: slot replenished.")
                                return
                            except Exception:
                                continue
                        log.critical("🛑 SQLite pool: replenish failed — pool "
                                     "is one slot smaller until restart.")
                    threading.Thread(target=_replenish, daemon=True,
                                     name="sqlite-replenish").start()
            else:
                self._pool.put(conn)

    def close_all(self) -> None:
        # v16g3 FIX R3-L11: empty() could lie between checks, and one failing
        # .close() aborted the whole drain. Pull-until-Empty; close best-effort.
        while True:
            try:
                conn = self._pool.get_nowait()
            except queue.Empty:
                break
            try:
                conn.close()
            except Exception:
                pass


_db_pool: Any = None
# v14g3 BUG 17: removed the dead db(read_only=...) helper. It was never called
# (every call site uses `_db_pool.get(...)` directly) and its read_only argument
# was silently ignored — a latent footgun if anyone had ever used it.


# ─────────────────────────────────────────────────────────────────────────────
# 🗄️  SCHEMA  — PostgreSQL + SQLite compatible (v8 adds audit_log + partitioned)
# ─────────────────────────────────────────────────────────────────────────────
_PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS customer_brains (
    customer_id      TEXT PRIMARY KEY,
    customer_name    TEXT NOT NULL,
    business_type    TEXT DEFAULT 'General',
    system_prompt    TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_chats      BIGINT DEFAULT 0,
    is_active        BOOLEAN DEFAULT TRUE,
    plan_tier        TEXT DEFAULT 'starter',
    whatsapp_phone   TEXT DEFAULT '',
    region           TEXT DEFAULT 'us-east-1'
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id    TEXT PRIMARY KEY,
    customer_id   TEXT NOT NULL REFERENCES customer_brains(customer_id) ON DELETE CASCADE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,
    channel       TEXT DEFAULT 'api',
    subject_hash  TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id             BIGSERIAL PRIMARY KEY,
    session_id     TEXT NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    role           TEXT NOT NULL CHECK(role IN ('user','model')),
    content        TEXT NOT NULL,
    timestamp      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    token_estimate INTEGER DEFAULT 0,
    ai_provider    TEXT DEFAULT 'gemini',
    latency_ms     INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS crm_contacts (
    id             BIGSERIAL PRIMARY KEY,
    customer_id    TEXT NOT NULL REFERENCES customer_brains(customer_id) ON DELETE CASCADE,
    phone_hash     TEXT DEFAULT '',
    enc_name       TEXT NOT NULL,
    enc_phone      TEXT NOT NULL,
    enc_email      TEXT DEFAULT '',
    enc_notes      TEXT DEFAULT '',
    contact_stage  TEXT DEFAULT 'lead',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_consented   BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS webhook_log (
    id           BIGSERIAL PRIMARY KEY,
    source_ip    TEXT,
    payload_hash TEXT NOT NULL,
    customer_id  TEXT,
    channel      TEXT DEFAULT 'tally',
    status       TEXT NOT NULL,
    error_detail TEXT,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS idempotency_keys (
    key           TEXT PRIMARY KEY,
    response_body TEXT NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS admin_users (
    user_id       TEXT PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    hashed_pw     TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'admin',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active     BOOLEAN DEFAULT TRUE,
    tenant_id     TEXT NOT NULL DEFAULT ''  -- v16g4 FIX M10: '' = fleet-wide
);

-- v8: SOC 2 / GDPR audit trail (FIX #6)
CREATE TABLE IF NOT EXISTS audit_log (
    id          BIGSERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_id    TEXT NOT NULL,
    action      TEXT NOT NULL,
    resource    TEXT NOT NULL,
    detail      JSONB DEFAULT '{}',
    ip          TEXT,
    region      TEXT DEFAULT 'us-east-1'
);

-- v8: outbox for distributed saga pattern (FIX #3)
CREATE TABLE IF NOT EXISTS outbox (
    id           BIGSERIAL PRIMARY KEY,
    event_type   TEXT NOT NULL,
    payload      JSONB NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    attempts     INTEGER DEFAULT 0,
    next_attempt_at TEXT NOT NULL DEFAULT ''
);

-- Indexes (optimised for 100B-scale read patterns)
CREATE INDEX IF NOT EXISTS idx_msg_session    ON chat_messages(session_id, id);
CREATE INDEX IF NOT EXISTS idx_sess_customer  ON chat_sessions(customer_id);
CREATE INDEX IF NOT EXISTS idx_crm_customer   ON crm_contacts(customer_id, contact_stage);
CREATE INDEX IF NOT EXISTS idx_idem_created   ON idempotency_keys(created_at);
CREATE INDEX IF NOT EXISTS idx_wh_customer    ON webhook_log(customer_id, processed_at);
CREATE INDEX IF NOT EXISTS idx_audit_actor    ON audit_log(actor_id, ts);
CREATE INDEX IF NOT EXISTS idx_outbox_status  ON outbox(status, created_at);
CREATE INDEX IF NOT EXISTS idx_brain_phone    ON customer_brains(whatsapp_phone) WHERE whatsapp_phone <> '';
"""

_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS customer_brains (
    customer_id     TEXT PRIMARY KEY,
    customer_name   TEXT NOT NULL,
    business_type   TEXT DEFAULT 'General',
    system_prompt   TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    total_chats     INTEGER DEFAULT 0,
    is_active       INTEGER DEFAULT 1,
    plan_tier       TEXT DEFAULT 'starter',
    whatsapp_phone  TEXT DEFAULT '',
    region          TEXT DEFAULT 'us-east-1'
);
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id    TEXT PRIMARY KEY,
    customer_id   TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    last_active   TEXT NOT NULL,
    message_count INTEGER DEFAULT 0,
    channel       TEXT DEFAULT 'api',
    subject_hash  TEXT DEFAULT '',
    FOREIGN KEY (customer_id) REFERENCES customer_brains(customer_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     TEXT NOT NULL,
    role           TEXT NOT NULL CHECK(role IN ('user','model')),
    content        TEXT NOT NULL,
    timestamp      TEXT NOT NULL,
    token_estimate INTEGER DEFAULT 0,
    ai_provider    TEXT DEFAULT 'gemini',
    latency_ms     INTEGER DEFAULT 0,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS crm_contacts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id   TEXT NOT NULL,
    phone_hash    TEXT DEFAULT '',
    enc_name      TEXT NOT NULL,
    enc_phone     TEXT NOT NULL,
    enc_email     TEXT DEFAULT '',
    enc_notes     TEXT DEFAULT '',
    contact_stage TEXT DEFAULT 'lead',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    is_consented  INTEGER DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customer_brains(customer_id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS webhook_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    source_ip    TEXT,
    payload_hash TEXT NOT NULL,
    customer_id  TEXT,
    channel      TEXT DEFAULT 'tally',
    status       TEXT NOT NULL,
    error_detail TEXT,
    processed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS idempotency_keys (
    key           TEXT PRIMARY KEY,
    response_body TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS admin_users (
    user_id    TEXT PRIMARY KEY,
    username   TEXT UNIQUE NOT NULL,
    hashed_pw  TEXT NOT NULL,
    role       TEXT NOT NULL DEFAULT 'admin',
    created_at TEXT NOT NULL,
    is_active  INTEGER DEFAULT 1,
    tenant_id  TEXT NOT NULL DEFAULT ''  -- v16g4 FIX M10: '' = fleet-wide
);
CREATE TABLE IF NOT EXISTS audit_log (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ts       TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    action   TEXT NOT NULL,
    resource TEXT NOT NULL,
    detail   TEXT DEFAULT '{}',
    ip       TEXT,
    region   TEXT DEFAULT 'us-east-1'
);
CREATE TABLE IF NOT EXISTS outbox (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type   TEXT NOT NULL,
    payload      TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'pending',
    created_at   TEXT NOT NULL,
    processed_at TEXT,
    attempts     INTEGER DEFAULT 0,
    next_attempt_at TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_msg_session   ON chat_messages(session_id, id);
CREATE INDEX IF NOT EXISTS idx_sess_customer ON chat_sessions(customer_id);
CREATE INDEX IF NOT EXISTS idx_crm_customer  ON crm_contacts(customer_id, contact_stage);
CREATE INDEX IF NOT EXISTS idx_idem_created  ON idempotency_keys(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_actor   ON audit_log(actor_id, ts);
CREATE INDEX IF NOT EXISTS idx_outbox_status ON outbox(status, created_at);
"""


def init_db() -> None:
    is_pg  = isinstance(_db_pool, PostgreSQLPool)
    schema = _PG_SCHEMA if is_pg else _SQLITE_SCHEMA
    with _db_pool.get() as conn:
        if is_pg:
            # v16g5 FIX R5-L4: the cursor was created inline and never closed
            # (it lived until GC), the one place in the file that skipped the
            # FIX L15 discipline. Multi-statement DDL still can't go through
            # _execute (it would ?→%s-translate the schema text), so close it
            # explicitly instead.
            _cur = conn.cursor()
            try:
                _cur.execute(schema)
            finally:
                try:
                    _cur.close()
                except Exception:
                    pass
        else:
            conn.executescript(schema)
    log.info("🗄️  Database schema initialised.")


def _migrate_v10() -> None:
    """v10: add new customer_brains columns. Safe to run on every boot."""
    for col in ("owner_phone TEXT DEFAULT ''",
                "instagram_id TEXT DEFAULT ''",
                "bot_name TEXT DEFAULT ''"):
        try:
            with _db_pool.get() as conn:
                _execute(conn, f"ALTER TABLE customer_brains ADD COLUMN {col}")
            log.info(f"🗄️  v10 migration: added {col.split()[0]}")
        except Exception:
            pass  # column already exists
    try:
        with _db_pool.get() as conn:
            _execute(conn,
                "CREATE INDEX IF NOT EXISTS idx_brain_ig "
                "ON customer_brains(instagram_id)")
    except Exception:
        pass


def _migrate_v11() -> None:
    """v11: CRM phone_hash dedupe column + index. Idempotent on every boot.
    #13: each statement runs in its own connection, so when two gunicorn
    workers boot simultaneously, the loser's 'duplicate column' error is
    swallowed and the schema is still correct. On Postgres the DDL and the
    backfill SCAN each take their own try-advisory-xact lock — v16g6 FIX
    R6-H7: xact locks die with their transaction, and the backfill ran on a
    NEW connection, so the single lock above never actually covered it and
    every booting worker ran the full 5,000-row scan concurrently."""
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    if is_pg:
        # v16g5 FIX R5-C3 (LAUNCH-CRITICAL): this used a SESSION-scoped
        # pg_advisory_lock. Three compounding failures:
        #   1. a failing ALTER aborts the Postgres transaction, so the
        #      `finally` unlock ALSO fails ("current transaction is aborted");
        #   2. a session advisory lock SURVIVES ROLLBACK, so the pool handed
        #      that connection back with the lock still held;
        #   3. pg_advisory_lock BLOCKS WITH NO TIMEOUT, so the next worker to
        #      boot waited on it forever.
        # One bad migration could therefore wedge every subsequent boot until
        # the connection was killed by hand — and Render recycles workers
        # routinely. pg_advisory_xact_lock is transaction-scoped: Postgres
        # releases it on COMMIT *or* ROLLBACK, unconditionally. The try-variant
        # never blocks, so a losing worker skips instead of hanging.
        try:
            with _db_pool.get() as conn:
                _cur = _execute(conn, "SELECT pg_try_advisory_xact_lock(427011) AS got")
                _row = _cur.fetchone()
                _got = bool(_row["got"] if isinstance(_row, dict) else _row[0])
                if _got:
                    _execute(conn, "ALTER TABLE crm_contacts "
                                   "ADD COLUMN IF NOT EXISTS phone_hash TEXT DEFAULT ''")
                    _execute(conn, "CREATE INDEX IF NOT EXISTS idx_crm_dedupe "
                                   "ON crm_contacts(customer_id, phone_hash)")
                else:
                    log.info("🗄️  v11 migration: another worker holds the "
                             "migration lock — skipping (no blocking wait).")
        except Exception as exc:
            log.warning(f"⚠️  v11 migration (pg) issue: {exc}")
    else:
        try:
            with _db_pool.get() as conn:
                _execute(conn, "ALTER TABLE crm_contacts ADD COLUMN phone_hash TEXT DEFAULT ''")
            log.info("🗄️  v11 migration: added crm_contacts.phone_hash")
        except Exception:
            pass  # column already exists
        try:
            with _db_pool.get() as conn:
                _execute(conn, "CREATE INDEX IF NOT EXISTS idx_crm_dedupe "
                               "ON crm_contacts(customer_id, phone_hash)")
        except Exception:
            pass

    # Best-effort backfill so pre-v11 rows participate in dedupe. Bounded,
    # per-row fault-isolated, and skipped instantly when nothing needs it.
    try:
        with _db_pool.get() as conn:
            # v16g5 FIX R5-L1: bounded, but now RESUMABLE. The old query had
            # no cursor, so with >5,000 legacy rows the same first page was
            # re-read on every boot forever and the rows past it were never
            # reached. ORDER BY id + a persisted high-water mark walks the
            # whole table across successive boots.
            _mark = brain_cache.get("migrate:v11:backfill_after") or 0
            try:
                _mark = int(_mark)
            except (TypeError, ValueError):
                _mark = 0
            # v16g6 FIX R6-H7: serialise the scan itself. This is a fresh
            # transaction, so the DDL lock above is long gone.
            _bf_lock_ok = True
            if isinstance(_db_pool, PostgreSQLPool):
                _c2 = _execute(conn,
                    "SELECT pg_try_advisory_xact_lock(427012) AS got")
                _r2 = _c2.fetchone()
                _bf_lock_ok = bool(_r2["got"] if not isinstance(_r2, tuple)
                                   else _r2[0])
            if _bf_lock_ok:
                cur = _execute(conn,
                    "SELECT id, customer_id, enc_phone FROM crm_contacts "
                    "WHERE (phone_hash='' OR phone_hash IS NULL) AND id > ? "
                    "ORDER BY id LIMIT 5000", (_mark,))
                rows = cur.fetchall()
            else:
                rows = []
                log.info("🗄️  v11 backfill: another worker holds the scan "
                         "lock — skipping this boot (v16g6 FIX R6-H7).")
        # v16g4 FIX P4: the backfill borrowed a pooled connection PER ROW —
        # up to 5,000 getconn/commit/putconn cycles every boot. Decrypt and
        # hash first (per-row fault-isolated), then apply every update on ONE
        # connection in ONE transaction.
        updates = []
        # v16g6 FIX R6-H6: classify every skip. A TRANSIENT skip (key missing
        # or wrong → "[ENCRYPTED]" / disabled-vault ciphertext passthrough)
        # must NOT advance the mark — one boot with a lost ENCRYPTION_KEY
        # used to move it past a whole page, stranding those rows behind it
        # FOREVER once the key came back: phone_hash='' → invisible to
        # dedupe, follow-ups and erasure. Only written rows and permanent
        # junk (too few digits under a HEALTHY decrypt) may advance it.
        _safe_ids = set()
        for r in rows:
            try:
                phone = pii_vault.decrypt(r["enc_phone"])
                # v16g2 FIX L13: with the vault disabled, decrypt() passes
                # CIPHERTEXT through unchanged — hashing that poisons dedupe.
                if (phone == "[ENCRYPTED]"
                        or (not pii_vault.enabled and len(phone or "") > 20)):
                    continue                      # transient — retry next boot
                if len(re.sub(r"\D", "", phone or "")) < 7:
                    _safe_ids.add(r["id"])        # permanent junk — skip forever
                    continue
                updates.append((_crm_phone_hash(r["customer_id"], phone), r["id"]))
                _safe_ids.add(r["id"])
            except Exception:
                continue                          # unknown — treat as transient
        if updates:
            with _db_pool.get() as conn:
                for row_hash, row_id in updates:
                    _execute(conn, "UPDATE crm_contacts SET phone_hash=? WHERE id=?",
                             (row_hash, row_id))
        if rows:
            # v16g5 FIX R5-L1: report what was actually WRITTEN, not what was
            # scanned — the old line claimed a backfill even when every row
            # was skipped by the L13 guard. Advance the high-water mark so the
            # next boot resumes past this page instead of re-reading it.
            # v16g6 FIX R6-H6: advance only across the longest PREFIX of this
            # page whose rows were written or are permanently unfixable — the
            # first transient row is a barrier the next boot resumes from.
            # (Without Redis the mark is per-process; re-scanning is now
            # merely redundant work, never data loss.)
            try:
                _last = _mark
                for r in rows:
                    if r["id"] in _safe_ids:
                        _last = r["id"]
                    else:
                        break
                if _last != _mark:
                    brain_cache.set("migrate:v11:backfill_after", int(_last),
                                    ttl=30 * 86400)
            except Exception:
                pass
            log.info(f"🗄️  v11 migration: scanned {len(rows)} contacts, "
                     f"backfilled phone_hash for {len(updates)}")
    except Exception as exc:
        log.warning(f"⚠️  v11 backfill skipped: {exc}")


_COL_MEMO: Dict[Tuple[str, str], bool] = {}   # v16g4 FIX P1


def _column_exists(conn, table: str, column: str) -> bool:
    """v13: check a column BEFORE ALTER so Postgres never poisons the transaction.
    On Postgres a failed ALTER inside a txn aborts it (`current transaction is
    aborted`) and every following statement fails too — the old `try/except pass`
    does NOT save you there. SQLite path uses PRAGMA table_info.
    v16g4 FIX P1: POSITIVE results are memoized — crm_add_contact ran this
    catalog query on EVERY inbound message for a column that has existed since
    the v16 migration. A column, once present, never un-exists at runtime;
    negative results are NOT cached so boot-time check-before-alter still sees
    its own ALTER land."""
    _k = (table, column)
    if _COL_MEMO.get(_k):
        return True
    if isinstance(_db_pool, PostgreSQLPool):
        cur = _execute(conn,
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name=? AND column_name=? "
            "AND table_schema = current_schema()", (table, column))  # v15 FIX 24
        _found = cur.fetchone() is not None
    else:
        # v16g5 FIX R5-M8: PRAGMA cannot take a bound parameter, so the table
        # name is interpolated — but it is now whitelisted against the
        # identifier grammar first. Every current call site passes a literal;
        # this makes sure the day one doesn't, it raises instead of executing
        # attacker-shaped SQL in the one place this file interpolates.
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", table or ""):
            raise ValueError(f"unsafe table identifier: {table!r}")
        cur = _execute(conn, f"PRAGMA table_info({table})")
        _found = any((r[1] if not isinstance(r, dict) else r.get("name")) == column
                     for r in cur.fetchall())
    if _found:
        _COL_MEMO[_k] = True   # v16g4 FIX P1
    return _found


def _migrate_v12() -> None:
    """v13 TRUE MULTI-TENANT — per-clinic WhatsApp/Instagram credentials.
    Postgres-safe (check-before-alter), idempotent on every boot.

    New columns on customer_brains:
      wa_phone_number_id  → the Meta business line THIS clinic owns (routing key)
      wa_token_enc        → AES-256-GCM encrypted per-clinic WhatsApp token
      ig_token_enc        → AES-256-GCM encrypted per-clinic Instagram token
      channel_status      → 'ok' | 'needs_reauth'  (token-death self-heal flag)

    Plus a UNIQUE index on wa_phone_number_id so two clinics can NEVER share a
    business number — the DB itself blocks the ambiguous-routing footgun.
    """
    cols = {
        "wa_phone_number_id": "TEXT DEFAULT ''",
        "wa_token_enc":       "TEXT DEFAULT ''",
        "ig_token_enc":       "TEXT DEFAULT ''",
        "channel_status":     "TEXT DEFAULT 'ok'",
    }
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    if is_pg:
        # advisory lock → exactly one worker runs the DDL when many boot at once
        try:
            with _db_pool.get() as conn:
                _execute(conn, "SELECT pg_advisory_lock(427012)")
                try:
                    for col, typ in cols.items():
                        if not _column_exists(conn, "customer_brains", col):
                            _execute(conn,
                                f"ALTER TABLE customer_brains ADD COLUMN {col} {typ}")
                            log.info(f"🗄️  v13 migration: added {col}")
                finally:
                    _execute(conn, "SELECT pg_advisory_unlock(427012)")
        except Exception as exc:
            log.warning(f"⚠️  v13 migration (pg cols) issue: {exc}")
    else:
        for col, typ in cols.items():
            try:
                with _db_pool.get() as conn:
                    if not _column_exists(conn, "customer_brains", col):
                        _execute(conn,
                            f"ALTER TABLE customer_brains ADD COLUMN {col} {typ}")
                        log.info(f"🗄️  v13 migration: added {col}")
            except Exception:
                pass  # column already exists

    # Routing indexes + 🔴 UNIQUENESS. Each in its own connection so one failure
    # (e.g. a pre-existing duplicate blocking the unique index) can't abort the
    # others. If the unique index can't be built because real duplicates exist,
    # we log LOUD instead of silently shipping ambiguous routing.
    stmts = [
        ("idx_brain_wa_pid",
         "CREATE INDEX IF NOT EXISTS idx_brain_wa_pid "
         "ON customer_brains(wa_phone_number_id)"),
        ("idx_brain_ig_id2",
         "CREATE INDEX IF NOT EXISTS idx_brain_ig_id2 "
         "ON customer_brains(instagram_id)"),
        ("uq_brain_wa_pid",
         "CREATE UNIQUE INDEX IF NOT EXISTS uq_brain_wa_pid "
         "ON customer_brains(wa_phone_number_id) "
         "WHERE wa_phone_number_id <> ''"),
    ]
    for name, stmt in stmts:
        try:
            with _db_pool.get() as conn:
                _execute(conn, stmt)
        except Exception as exc:
            if name == "uq_brain_wa_pid":
                log.critical(
                    "🛑 v13: could NOT create the unique phone_number_id index "
                    f"({exc}). Two active clinics likely share a wa_phone_number_id "
                    "— inbound routing is ambiguous until you fix the duplicate. "
                    "Run: SELECT wa_phone_number_id, COUNT(*) FROM customer_brains "
                    "WHERE wa_phone_number_id<>'' GROUP BY 1 HAVING COUNT(*)>1;")
            else:
                log.warning(f"⚠️  v13 index skip [{name}]: {exc}")


def _migrate_v14g3() -> None:
    """v14 Gen-3 migrations — idempotent, safe on every boot.

    BUG 10: a UNIQUE index on (customer_id, phone_hash) makes CRM dedupe
    race-proof — a concurrent second insert of the same lead fails at the DB and
    crm_add_contact returns the existing row instead of creating a duplicate.
    Best-effort: if pre-existing duplicate phone_hash rows block the unique index,
    we log and keep the non-unique idx_crm_dedupe (lookups still work, the SELECT
    -first dedupe still applies, and the messaging path is already serialised).

    BUG 16: the whatsapp_phone index ships in the Postgres schema but was missing
    on SQLite — add it so the legacy-id lookup isn't a table scan there."""
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    uq = ("CREATE UNIQUE INDEX IF NOT EXISTS uq_crm_dedupe "
          "ON crm_contacts(customer_id, phone_hash) WHERE phone_hash <> ''")
    try:
        with _db_pool.get() as conn:
            if is_pg:
                _execute(conn, "SELECT pg_advisory_lock(427014)")
                try:
                    _execute(conn, uq)
                finally:
                    _execute(conn, "SELECT pg_advisory_unlock(427014)")
            else:
                _execute(conn, uq)
        log.info("🗄️  v14g3 migration: unique CRM dedupe index ensured.")
    except Exception as exc:
        log.warning("⚠️  v14g3: unique CRM index not built (likely existing "
                    f"duplicate phone_hash rows) — dedupe stays best-effort: {exc}")

    if not is_pg:
        try:
            with _db_pool.get() as conn:
                _execute(conn, "CREATE INDEX IF NOT EXISTS idx_brain_phone "
                               "ON customer_brains(whatsapp_phone)")
        except Exception:
            pass


def _migrate_v14g4() -> None:
    """v14 Gen-4 migrations — idempotent, safe on every boot, fully additive.

    Creates the `bookings` table (appointment engine) and adds
    crm_contacts.followed_up_at (cold-lead follow-up marker). Nothing here
    touches existing rows or behaviour — and every Gen-4 feature is flag-gated
    OFF by default, so a fresh boot of Gen-4 behaves EXACTLY like Gen-3 until you
    explicitly enable a feature."""
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    pk = "BIGSERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    create_bookings = f"""
        CREATE TABLE IF NOT EXISTS bookings (
            id             {pk},
            customer_id    TEXT NOT NULL,
            phone_hash     TEXT NOT NULL,
            enc_phone      TEXT DEFAULT '',
            enc_name       TEXT DEFAULT '',
            slot_start     TEXT NOT NULL,
            slot_end       TEXT NOT NULL,
            status         TEXT DEFAULT 'booked',
            reminders_sent TEXT DEFAULT '',
            source         TEXT DEFAULT 'whatsapp',
            created_at     TEXT NOT NULL,
            updated_at     TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customer_brains(customer_id) ON DELETE CASCADE
        )"""
    try:
        with _db_pool.get() as conn:
            _execute(conn, create_bookings)
            _execute(conn, "CREATE INDEX IF NOT EXISTS idx_book_slot "
                           "ON bookings(customer_id, status, slot_start)")
            _execute(conn, "CREATE INDEX IF NOT EXISTS idx_book_phone "
                           "ON bookings(customer_id, phone_hash, status)")
            # a slot can be held by at most one active booking per clinic
            _execute(conn, "CREATE UNIQUE INDEX IF NOT EXISTS uq_book_slot "
                           "ON bookings(customer_id, slot_start) WHERE status='booked'")
        log.info("🗄️  v14g4 migration: bookings table + indexes ensured.")
    except Exception as exc:
        log.warning(f"⚠️  v14g4: bookings migration issue: {exc}")

    _migrate_booking_overlap_constraint()   # v20.0 R20-C1

    try:
        with _db_pool.get() as conn:
            if not _column_exists(conn, "crm_contacts", "followed_up_at"):
                _execute(conn, "ALTER TABLE crm_contacts "
                               "ADD COLUMN followed_up_at TEXT DEFAULT ''")
        log.info("🗄️  v14g4 migration: crm_contacts.followed_up_at ensured.")
    except Exception as exc:
        log.warning(f"⚠️  v14g4: followed_up_at migration issue: {exc}")



# ── v20.0 · FIX R20-C1 (REVENUE-CRITICAL, Postgres only) ─────────────────────
# booking_create guards overlap with SELECT-then-INSERT inside one transaction.
# That is check-then-act: under READ COMMITTED two workers both run the SELECT,
# both see nothing, and both INSERT. uq_book_slot cannot catch it because it
# indexes slot_start EQUALITY — 14:00-14:30 and 14:20-14:50 have different
# starts. SQLite was BELIEVED to be hiding this by serialising writes. v30
# R30-M1 measured that and it is only half true. Six independent processes
# racing mutually-overlapping slots through booking_create give exactly one
# row on BOTH backends — but that is the guard above winning, not the
# database. With the guard bypassed by a direct INSERT (an admin tool, a
# migration, a future code path that forgets it) PostgreSQL raises 23P01 and
# holds at one row, while SQLite writes BOTH overlapping rows. SQLite has no
# backstop at all; it only ever had the guard.
#
# Reproduced on PostgreSQL 16.14 with two real connections interleaved exactly
# as two gunicorn workers would be:
#   without this constraint : A committed | B committed  -> 2 rows, double-booked
#   with this constraint    : A committed | B rejected 23P01 -> 1 row
#
# Why the constraint is built this way. slot_start/slot_end are TEXT (ISO-8601),
# and the obvious DDL is rejected by Postgres:
#     tstzrange(slot_start::timestamptz, ...) -> ERROR: functions in index
#     expression must be marked IMMUTABLE
# because text->timestamptz depends on the TimeZone setting. It only depends on
# it when the string carries NO offset. The engine always writes an explicit
# +00:00 (datetime.now(timezone.utc).isoformat()), so the parse really is
# timezone-independent for this data — but "really is" has to be enforced, not
# assumed. The CHECK lands FIRST and rejects any row without a UTC offset;
# only then is the wrapper honestly marked IMMUTABLE. Do not reorder these.
#
# Deliberately NOT touching the column types. ALTER ... TYPE timestamptz would
# make psycopg2 hand back datetime objects where every caller
# (_fmt_local_dt(b["slot_start"]), the reminder sweep, the ICS export) expects
# an ISO string, and would diverge the two engines' schemas. The application
# guard in booking_create stays as the first line of defence and still returns
# the friendly "that time just went" — this is the durable backstop underneath
# it, for the case where two requests land in the same millisecond.
# NOTE the {0,1} instead of the obvious `?`. _execute translates ? -> %s with a
# blind string replace, so a literal '?' anywhere in the SQL corrupts it — and
# v16g5 FIX R5-M7's placeholder guard caught exactly that when this migration
# was first run, refusing the DDL instead of sending nonsense to Postgres. The
# guard worked; the regex is what had to change.
_BK_ISO_UTC_RE = (r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+){0,1}"
                  r"(\+00:00|Z)$")


def _pg_has_constraint(conn, table: str, name: str) -> bool:
    cur = _execute(conn,
        "SELECT 1 FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid "
        "WHERE t.relname = ? AND c.conname = ? LIMIT 1", (table, name))
    return cur.fetchone() is not None


def _migrate_booking_overlap_constraint() -> None:
    """Idempotent, Postgres-only, and non-fatal. SQLite has no EXCLUDE and does
    not need one — it serialises writers. If the constraint cannot be added
    because live data already contains an overlap, say so LOUDLY and carry on:
    refusing to boot would take a working clinic offline over a historical row."""
    if not isinstance(_db_pool, PostgreSQLPool):
        # v30.0 · FIX R30-M1. This early-return was SILENT, and silence is the
        # failure mode this engine is worst at detecting. On SQLite there is no
        # bk_no_overlap and no bk_slot_iso_utc — the only thing preventing a
        # double-booked chair is booking_create's in-transaction check-then-
        # insert, which a direct write does not go through. Postgres is the
        # production backend, so this is normally dev-only; it stops being
        # dev-only the moment a Postgres URL is wrong or the free tier is
        # reclaimed and the pool falls back — the R18-H1 scenario that made the
        # banner report the pool actually built rather than the mode requested.
        log.warning(
            "\u26a0\ufe0f  SQLite mode: booking overlap has NO durable "
            "constraint. bk_no_overlap (EXCLUDE ... WITH &&) and "
            "bk_slot_iso_utc are PostgreSQL-only, so partial overlaps are "
            "prevented solely by booking_create's in-transaction guard, and "
            "any write that bypasses it can double-book. Measured on v29 with "
            "the guard bypassed: Postgres 23P01 (1 row), SQLite 2 overlapping "
            "rows. Use Postgres in production (v20 R20-C1).")
        return
    try:
        with _db_pool.get() as conn:
            _execute(conn, "CREATE EXTENSION IF NOT EXISTS btree_gist")
            if not _pg_has_constraint(conn, "bookings", "bk_slot_iso_utc"):
                _execute(conn,
                    "ALTER TABLE bookings ADD CONSTRAINT bk_slot_iso_utc CHECK ("
                    f"slot_start ~ '{_BK_ISO_UTC_RE}' AND "
                    f"slot_end   ~ '{_BK_ISO_UTC_RE}')")
            _execute(conn,
                "CREATE OR REPLACE FUNCTION heonix_iso_utc(txt text) "
                "RETURNS timestamptz LANGUAGE sql IMMUTABLE STRICT "
                "PARALLEL SAFE AS $fn$ SELECT txt::timestamptz $fn$")
            if not _pg_has_constraint(conn, "bookings", "bk_no_overlap"):
                _execute(conn,
                    "ALTER TABLE bookings ADD CONSTRAINT bk_no_overlap "
                    "EXCLUDE USING gist (customer_id WITH =, "
                    "tstzrange(heonix_iso_utc(slot_start), "
                    "heonix_iso_utc(slot_end)) WITH &&) "
                    "WHERE (status = 'booked')")
        log.info("🗄️  v20 R20-C1: booking overlap EXCLUDE constraint ensured.")
    except Exception as exc:
        log.critical(
            "🛑 R20-C1: could not install the booking overlap constraint — "
            "double-booking is possible under concurrency until this is fixed. "
            f"Cause: {exc}")


def _migrate_v14g5() -> None:
    """v14 Gen-5 migrations — idempotent, additive. Adds chat_sessions.subject_hash
    (FIX 3 — lets DPDP erasure resolve a subject's sessions from the DB instead of a
    1-hour cache key) plus its lookup index. Safe on every boot."""
    try:
        with _db_pool.get() as conn:
            if not _column_exists(conn, "chat_sessions", "subject_hash"):
                _execute(conn, "ALTER TABLE chat_sessions ADD COLUMN subject_hash TEXT DEFAULT ''")
                log.info("🗄️  v14g5 migration: chat_sessions.subject_hash added.")
    except Exception as exc:
        log.warning(f"⚠️  v14g5: subject_hash migration issue: {exc}")
    try:
        with _db_pool.get() as conn:
            _execute(conn, "CREATE INDEX IF NOT EXISTS idx_sess_subject "
                           "ON chat_sessions(customer_id, subject_hash)")
    except Exception:
        pass


def _migrate_v15g3() -> None:
    """v15 Gen-3 migration — idempotent, additive. Adds outbox.next_attempt_at
    (FIX 1) so failed rows retry on an EXPONENTIAL schedule instead of burning
    all 5 attempts in ~80 seconds of janitor ticks. TEXT ISO-8601 UTC, same
    lexicographically-sortable format every timestamp in this engine uses.
    Empty string = eligible immediately (all pre-existing rows keep working)."""
    try:
        with _db_pool.get() as conn:
            if not _column_exists(conn, "outbox", "next_attempt_at"):
                _execute(conn, "ALTER TABLE outbox "
                               "ADD COLUMN next_attempt_at TEXT DEFAULT ''")
                log.info("🗄️  v15g3 migration: outbox.next_attempt_at added.")
    except Exception as exc:
        log.warning(f"⚠️  v15g3: next_attempt_at migration issue: {exc}")


def _migrate_v15g4() -> None:
    """v15 Gen-4 migration — idempotent, additive (indexes only, no schema
    change). v15g4 FIX D4: the hourly retention purges filter on
    chat_messages.timestamp and webhook_log.processed_at, neither of which had
    a usable index — full-table scans every hour at scale. v15g4 FIX D5:
    idx_wh_customer existed only in the Postgres fresh-install schema, never
    on SQLite. All CREATE INDEX IF NOT EXISTS → safe on every boot, both DBs."""
    stmts = (
        "CREATE INDEX IF NOT EXISTS idx_msg_ts        ON chat_messages(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_wh_processed  ON webhook_log(processed_at)",
        "CREATE INDEX IF NOT EXISTS idx_wh_customer   ON webhook_log(customer_id, processed_at)",
    )
    try:
        with _db_pool.get() as conn:
            for s in stmts:
                try:
                    _execute(conn, s)
                except Exception as exc:
                    log.warning(f"⚠️  v15g4 index skipped ({s.split()[5]}): {exc}")
        log.info("🗄️  v15g4 migration: purge-path indexes ensured.")
    except Exception as exc:
        log.warning(f"⚠️  v15g4 migration issue: {exc}")


def _migrate_v16() -> None:
    """v16 U1 migration — idempotent, additive. WhatsApp usernames/BSUID:
    crm_contacts.wa_user_id stores Meta's business-scoped user ID alongside
    the phone identity, mirroring the Contact-Book mapping locally. Indexed
    per clinic for the remap/lookup paths."""
    try:
        with _db_pool.get() as conn:
            if not _column_exists(conn, "crm_contacts", "wa_user_id"):
                _execute(conn, "ALTER TABLE crm_contacts "
                               "ADD COLUMN wa_user_id TEXT DEFAULT ''")
                log.info("🗄️  v16 migration: crm_contacts.wa_user_id added.")
            try:
                _execute(conn, "CREATE INDEX IF NOT EXISTS idx_crm_userid "
                               "ON crm_contacts(customer_id, wa_user_id)")
            except Exception as exc:
                log.warning(f"⚠️  v16 idx_crm_userid skipped: {exc}")
    except Exception as exc:
        log.warning(f"⚠️  v16 migration issue: {exc}")


def _migrate_v16g5() -> None:
    """v16g5 FIX R5-H4: durable opt-out suppression table."""
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    ddl = ("CREATE TABLE IF NOT EXISTS opt_outs ("
           "id BIGSERIAL PRIMARY KEY, customer_id TEXT NOT NULL, "
           "subject_hash TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"
           if is_pg else
           "CREATE TABLE IF NOT EXISTS opt_outs ("
           "id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id TEXT NOT NULL, "
           "subject_hash TEXT NOT NULL, created_at TEXT NOT NULL)")
    for stmt in (ddl,
                 "CREATE UNIQUE INDEX IF NOT EXISTS uq_optout "
                 "ON opt_outs(customer_id, subject_hash)"):
        try:
            with _db_pool.get() as conn:
                _execute(conn, stmt)
        except Exception as exc:
            log.warning(f"⚠️  v16g5 opt_outs migration issue: {exc}")


def _migrate_v16g4() -> None:
    """v16g4 FIX M10: admin_users.tenant_id — admin JWTs carried role but no
    tenant claim, so every 'admin' token was fleet-wide; the v16 IDOR fix only
    forced them to NAME a customer_id, not to name their OWN. '' keeps legacy
    rows fleet-wide (existing behaviour); a tenant-scoped admin can only touch
    their tenant. Check-before-alter (Postgres txn-poison safe)."""
    try:
        with _db_pool.get() as conn:
            if not _column_exists(conn, "admin_users", "tenant_id"):
                _execute(conn, "ALTER TABLE admin_users "
                               "ADD COLUMN tenant_id TEXT NOT NULL DEFAULT ''")
                log.info("🗄️  v16g4 migration: added admin_users.tenant_id")
    except Exception as exc:
        log.warning(f"⚠️  v16g4 migration issue: {exc}")


def _report_wa_pid_duplicates() -> None:
    """v14 (drawback #4): make duplicate-tenant routing self-diagnosing. If two
    active clinics share a wa_phone_number_id, inbound routing is ambiguous and
    the unique index can't build. Instead of leaving you to guess, log EXACTLY
    which number is shared by which clinics so cleanup is a 30-second fix."""
    try:
        with _db_pool.get(read_only=True) as conn:
            if not _column_exists(conn, "customer_brains", "wa_phone_number_id"):
                return
            cur = _execute(conn,
                "SELECT wa_phone_number_id AS pid, COUNT(*) AS c "
                "FROM customer_brains WHERE wa_phone_number_id <> '' "
                "AND is_active=? GROUP BY wa_phone_number_id "
                "HAVING COUNT(*) > 1", (_db_true(),))
            dups = cur.fetchall()
            for d in dups:
                pid = d["pid"]
                cur2 = _execute(conn,
                    "SELECT customer_id FROM customer_brains "
                    "WHERE wa_phone_number_id=? AND is_active=?",
                    (pid, _db_true()))
                owners = [r["customer_id"] for r in cur2.fetchall()]
                log.critical(f"🛑 DUPLICATE wa_phone_number_id={pid} shared by "
                             f"clinics {owners}. Routing is ambiguous — keep ONE, "
                             f"clear it on the others via "
                             f"POST /admin/customer/<id>/channel.")
        if not dups:
            log.info("✅ Tenant routing check: no duplicate WhatsApp numbers.")
    except Exception as exc:
        log.warning(f"⚠️  duplicate-tenant check skipped: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 🧠  DISTRIBUTED CACHE  — Redis primary + in-process fallback
# ─────────────────────────────────────────────────────────────────────────────
class DistributedCache:
    def __init__(self, redis_url: str, default_ttl: int = 600):
        self._ttl   = default_ttl
        self._redis = None
        self._local: Dict[str, Tuple[Any, float]] = {}
        self._lock  = threading.Lock()
        if redis_url and REDIS_AVAILABLE:
            try:
                # v15g3 FIX 3 (MED): managed Redis (Render/Upstash) silently drops
                # idle connections. Without health_check_interval the FIRST command
                # after an idle gap failed, the blanket except ate it, and that call
                # silently fell to the per-process dict — the exact stale-brain
                # split FIX H2 fought, just triggered by idleness instead of JSON.
                # health_check_interval PINGs a stale socket before reuse;
                # retry_on_timeout absorbs one transient stall; keepalive stops
                # NAT/proxy idle reaping; connect timeout bounds boot-time hangs.
                r = redis_lib.from_url(redis_url, decode_responses=True,
                                       socket_timeout=2,
                                       socket_connect_timeout=2,
                                       retry_on_timeout=True,
                                       health_check_interval=30,
                                       socket_keepalive=True)
                r.ping()
                self._redis = r
                log.info("🧠 Redis distributed cache connected.")
            except Exception as exc:
                log.warning(f"⚠️  Redis unavailable ({exc}) — in-process cache only.")
        else:
            log.warning("⚠️  REDIS_URL not set — in-process cache (single-server).")

    def get(self, key: str) -> Optional[Any]:
        if self._redis:
            try:
                val = self._redis.get(f"heonix:{key}")
                return json.loads(val) if val else None
            except Exception:
                pass
        with self._lock:
            entry = self._local.get(key)
            if entry and time.monotonic() < entry[1]:
                return entry[0]
            self._local.pop(key, None)
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if self._redis:
            try:
                # v15g2 FIX H2 (HIGH): Postgres brain/route rows carry datetime
                # objects (TIMESTAMPTZ) — plain json.dumps raised TypeError, the
                # blanket except swallowed it, and the value silently fell into
                # the PER-PROCESS dict below. Result on PG + multi-worker: every
                # cache-bust (token re-attach, /channel edit, soft-delete, FIX 8
                # self-heal) cleared Redis + ONE worker; the other workers kept
                # serving the stale brain (dead token included) for up to the
                # full TTL. default=str makes the row Redis-safe; consumers
                # already str() the timestamp fields, so nothing else changes.
                self._redis.setex(f"heonix:{key}", ttl or self._ttl,
                                  json.dumps(value, default=str))
                return
            except Exception:
                pass
        with self._lock:
            self._local[key] = (value, time.monotonic() + (ttl or self._ttl))

    def delete(self, key: str) -> None:
        if self._redis:
            try:
                self._redis.delete(f"heonix:{key}")
            except Exception:
                pass
        with self._lock:
            self._local.pop(key, None)

    def incr_checked(self, key: str, ttl: int = 60) -> Tuple[int, bool]:
        """Atomic increment. v16g2 FIX L11: returns (count, distributed) — the
        second element tells the caller whether the increment actually landed
        in Redis (fleet-wide) or fell back to this process's dict, so the rate
        limiter can shrink its budget during a live-Redis blip instead of
        silently letting the fleet allow rpm × workers again."""
        if self._redis:
            try:
                pipe = self._redis.pipeline()
                pipe.incr(f"heonix:{key}")
                pipe.expire(f"heonix:{key}", ttl)
                result = pipe.execute()
                return result[0], True
            except Exception:
                pass
        with self._lock:
            # v12 #42/#35: the old code reused an EXPIRED window's count and
            # never dropped stale keys → a user who once hit the limit stayed
            # banned forever and the dict grew unbounded. Now an elapsed window
            # resets to 1 and expired keys are eligible for prune_local().
            now   = time.monotonic()
            entry = self._local.get(key)
            if entry is None or now >= entry[1]:
                self._local[key] = (1, now + ttl)
                return 1, False
            new_val = entry[0] + 1
            self._local[key] = (new_val, entry[1])
            return new_val, False

    def incr(self, key: str, ttl: int = 60) -> int:
        """Back-compat shim over incr_checked (v16g2 FIX L11)."""
        return self.incr_checked(key, ttl)[0]

    def get_pinned(self, key: str, distributed: bool) -> Optional[Any]:
        """v16g4 FIX M14: read from the SAME backend a paired incr_checked
        landed in. The sliding-window limiter's two reads (current-minute INCR,
        previous-minute GET) could split across Redis and the local dict during
        a blip — the weighted window then quietly degraded to a per-process
        fixed window. Pinning the read keeps the two terms coherent; if the
        pinned backend can't answer, the caller gets None and knowingly falls
        back to a fixed window on ONE consistent backend."""
        if distributed:
            if not self._redis:
                return None
            try:
                val = self._redis.get(f"heonix:{key}")
                return json.loads(val) if val else None
            except Exception:
                return None
        with self._lock:
            entry = self._local.get(key)
            if entry and time.monotonic() < entry[1]:
                return entry[0]
        return None

    def setnx(self, key: str, ttl: int) -> bool:
        """v12: atomic 'claim this key exactly once'. Returns True only for the
        single caller that won the claim. On Redis this is SET key 1 NX EX ttl
        (atomic across ALL gunicorn workers) — this is what makes webhook dedupe
        race-proof (#11/#38/#44). Local fallback is lock-guarded."""
        if self._redis:
            try:
                return bool(self._redis.set(f"heonix:{key}", "1", nx=True, ex=ttl))
            except Exception:
                pass
        with self._lock:
            now   = time.monotonic()
            entry = self._local.get(key)
            if entry is not None and now < entry[1]:
                return False
            self._local[key] = (1, now + ttl)
            return True

    def delete_prefix(self, prefix: str) -> int:
        """v16g4 FIX L12: bulk-delete every key under a prefix (Redis SCAN +
        local dict sweep). Used by DPDP erasure to flush the `resp:` reply
        cache — those entries are keyed on message CONTENT, so a message that
        contained the subject's own details can sit cached (and replayable to
        the next patient who types the same text) for the full TTL. There is
        no per-subject index into a content-hash cache, so erasure flushes
        the whole prefix; it is a perf cache and rebuilds on demand."""
        removed = 0
        if self._redis:
            try:
                # v16g6 FIX R6-L9: one DELETE per key made erasure's resp:*
                # flush a few thousand sequential round-trips inside a
                # request. Pipeline in batches of 500.
                _batch = []

                def _flush(_b):
                    _pipe = self._redis.pipeline(transaction=False)
                    for _bk in _b:
                        _pipe.delete(_bk)
                    return sum(1 for _r in _pipe.execute() if _r)

                for k in self._redis.scan_iter(match=f"heonix:{prefix}*",
                                               count=500):
                    _batch.append(k)
                    if len(_batch) >= 500:
                        removed += _flush(_batch)
                        _batch = []
                if _batch:
                    removed += _flush(_batch)
            except Exception:
                pass
        with self._lock:
            stale = [k for k in self._local if k.startswith(prefix)]
            for k in stale:
                self._local.pop(k, None)
                removed += 1
        return removed

    def prune_local(self) -> int:
        """v12 #35: drop expired in-process entries so the local fallback can't
        leak RAM. Cheap no-op when Redis is the backend (local dict stays tiny)."""
        removed = 0
        with self._lock:
            now    = time.monotonic()
            stale  = [k for k, v in self._local.items()
                      if isinstance(v, tuple) and len(v) == 2 and now >= v[1]]
            for k in stale:
                self._local.pop(k, None)
                removed += 1
        return removed

    # v14g5 FIX 6/7: cross-worker mutex (per-conversation) + single-leader lock
    # (scheduler). On Redis these are atomic across ALL gunicorn workers: SET NX EX
    # with a random token, released only by the holder via a check-and-del (Lua).
    # Local fallback is lock-guarded — single-process dev only, so in prod you MUST
    # set REDIS_URL (STRICT_PROD already enforces this) for these to be real.
    def lock(self, name: str, ttl: int) -> Optional[str]:
        token = uuid.uuid4().hex
        if self._redis:
            try:
                if self._redis.set(f"heonix:lock:{name}", token, nx=True, ex=ttl):
                    return token
                return None
            except Exception:
                pass
        with self._lock:
            now   = time.monotonic()
            entry = self._local.get(f"__lock__{name}")
            if entry is not None and now < entry[1]:
                return None
            self._local[f"__lock__{name}"] = (token, now + ttl)
            return token

    def unlock(self, name: str, token: str) -> None:
        if not token:
            return
        if self._redis:
            try:
                lua = ("if redis.call('get', KEYS[1]) == ARGV[1] then "
                       "return redis.call('del', KEYS[1]) else return 0 end")
                self._redis.eval(lua, 1, f"heonix:lock:{name}", token)
                return
            except Exception:
                pass
        with self._lock:
            entry = self._local.get(f"__lock__{name}")
            if entry and entry[0] == token:
                self._local.pop(f"__lock__{name}", None)

    def renew(self, name: str, token: str, ttl: int) -> bool:
        """v15g2 FIX M4: extend a held lock's TTL (only if we still hold it).
        Lets a drain heartbeat keep the per-conversation lease alive through a
        slow AI turn instead of silently losing exclusivity at CONV_LOCK_TTL."""
        if not token:
            return False
        if self._redis:
            try:
                lua = ("if redis.call('get', KEYS[1]) == ARGV[1] then "
                       "return redis.call('expire', KEYS[1], ARGV[2]) else return 0 end")
                return bool(self._redis.eval(lua, 1, f"heonix:lock:{name}",
                                             token, int(ttl)))
            except Exception:
                return False
        with self._lock:
            entry = self._local.get(f"__lock__{name}")
            if entry and entry[0] == token:
                self._local[f"__lock__{name}"] = (token, time.monotonic() + ttl)
                return True
        return False

    def ping(self) -> bool:
        """v14g5 FIX 48: live Redis health, not just 'a client object exists'."""
        if not self._redis:
            return False
        try:
            return bool(self._redis.ping())
        except Exception:
            return False


brain_cache = DistributedCache(cfg.REDIS_URL, default_ttl=cfg.CACHE_TTL)


# ─────────────────────────────────────────────────────────────────────────────
# 🪙  PER-CUSTOMER FIXED-WINDOW RATE LIMITER  (v8 FIX #8 · v16g2 FIX C9)
#     Limits per customer_id, not just IP — prevents one customer starving others
# ─────────────────────────────────────────────────────────────────────────────
class CustomerRateLimiter:
    """
    SLIDING-WINDOW-approximation rate limiter keyed on customer_id.
    v16g2 FIX C9 corrected the docstring to fixed-window; v16g3 FIX R3-M9
    upgrades the algorithm: current-minute count + previous-minute count
    weighted by window overlap (the standard CDN approximation), so the old
    2× burst at every :00 boundary (60 msgs at :59 + 60 at :00 in ~2s per
    conversation — the exact flood this limiter exists for) is gone. Redis
    for distributed accuracy; falls back to in-process.
    """
    def __init__(self, requests_per_minute: int = 60):
        self._rpm = requests_per_minute

    def _effective_rpm(self, distributed: bool) -> int:
        # v14g3 BUG 8: with Redis, INCR is shared across all workers, so the
        # limit is global and exact. WITHOUT Redis the counter is per-process,
        # so N gunicorn workers would EACH allow the full rpm (aggregate =
        # rpm × N). Divide by the worker count in that fallback so the whole
        # fleet stays close to the intended limit.
        # v16g2 FIX L11: the divisor now keys off whether THIS increment
        # actually landed in Redis — not off "a client object exists". During a
        # live-Redis error, incr falls back to the per-process dict; the old
        # object-existence check kept returning the full rpm for the blip.
        if distributed:
            return self._rpm
        workers = max(1, cfg.WEB_CONCURRENCY)
        return max(1, self._rpm // workers)

    # v16g5 FIX R5-L5: the window math below ran on time.time() — a WALL
    # clock. An NTP step BACKWARDS re-opens a window a caller already spent
    # (limit silently doubles); a step FORWARDS skips one (legitimate patients
    # dropped). Every other timer in this file already uses time.monotonic().
    # v16g6 FIX R6-L11: pinning time.time()-time.monotonic() AT IMPORT made
    # the anchor itself per-process — workers booted either side of an NTP
    # step (or drifted apart over a long uptime) computed different `win`
    # ids for the same instant, and the fleet limiter silently degraded to
    # per-worker: the exact failure R5-L5 existed to fix. Fleet-comparable
    # ids need the fleet's shared clock: time.time() directly. An NTP step
    # now glitches at most ONE window and self-heals; permanent cross-worker
    # skew is gone.
    @classmethod
    def _wall(cls) -> float:
        return time.time()

    def is_allowed(self, customer_id: str) -> bool:
        # v16g3 FIX R3-M9: sliding-window approximation. ttl 120 keeps the
        # previous minute's counter readable for the weighted term.
        now  = self._wall()                       # v16g5 FIX R5-L5
        win  = int(now // 60)
        count, distributed = brain_cache.incr_checked(
            f"rl:{customer_id}:{win}", ttl=120)     # v16g2 FIX L11 signal kept
        # v16g4 FIX M14: previous-minute read pinned to the backend the
        # increment landed in — never mix Redis-current with local-previous.
        prev = brain_cache.get_pinned(f"rl:{customer_id}:{win - 1}", distributed)
        try:
            prev_n = int(prev) if prev is not None else 0
        except (TypeError, ValueError):
            prev_n = 0
        weight = 1.0 - ((now % 60) / 60.0)
        return (count + prev_n * weight) <= self._effective_rpm(distributed)

    def check(self, customer_id: str):
        """Call this in route handlers. Returns True if the request is allowed.
        v15 FIX 21: the old docstring promised (allowed, count) — anyone
        unpacking it would have crashed."""
        return self.is_allowed(customer_id)


customer_limiter = CustomerRateLimiter(requests_per_minute=60)


# ─────────────────────────────────────────────────────────────────────────────
# ⚡  CIRCUIT BREAKER
# ─────────────────────────────────────────────────────────────────────────────
class CircuitBreaker:
    CLOSED = "CLOSED"; OPEN = "OPEN"; HALF_OPEN = "HALF_OPEN"

    def __init__(self, name: str, failure_threshold: int = 5, reset_timeout: float = 60.0):
        self.name           = name
        self._threshold     = failure_threshold
        self._reset_timeout = reset_timeout
        self._failures      = 0
        self._state         = self.CLOSED
        self._opened_at     = 0.0
        self._probe_inflight = False     # v12 #22: single-probe gate for HALF_OPEN
        self._probe_started_at = 0.0     # v16g5 FIX R5-H2
        self._lock          = threading.Lock()

    @property
    def state(self) -> str:
        with self._lock:
            return self._state

    def call(self, func: Callable, *args, **kwargs):
        is_probe = False
        with self._lock:
            if self._state == self.OPEN:
                if time.monotonic() - self._opened_at >= self._reset_timeout:
                    self._state = self.HALF_OPEN
                    self._probe_inflight = False
                    log.info(f"⚡ CircuitBreaker [{self.name}] → HALF_OPEN")
                else:
                    raise RuntimeError(f"CircuitBreaker [{self.name}] OPEN")
            if self._state == self.HALF_OPEN:
                # v12 #22: let exactly ONE request probe recovery. Every other
                # concurrent caller fast-fails instead of stampeding a provider
                # that just came back from the dead (which would re-trip it and
                # could DDoS Gemini/OpenAI ourselves).
                # v16g5 FIX R5-H2: belt-and-braces for the finally above — a
                # probe still "in flight" past the reset window is treated as
                # abandoned and reclaimed, so the breaker can never wedge.
                if (self._probe_inflight
                        and time.monotonic() - self._probe_started_at
                            < max(self._reset_timeout, 30.0)):
                    raise RuntimeError(f"CircuitBreaker [{self.name}] HALF_OPEN (probing)")
                if self._probe_inflight:
                    log.warning(f"⚡ CircuitBreaker [{self.name}] reclaiming an "
                                f"abandoned probe slot")
                self._probe_inflight   = True
                self._probe_started_at = time.monotonic()
                is_probe = True
        # v16g5 FIX R5-H2: _probe_inflight used to be cleared only on the three
        # `except Exception` / success paths. A BaseException out of the probe
        # — SystemExit, KeyboardInterrupt, a gevent/eventlet Timeout, a
        # GeneratorExit from a killed worker thread — left it True FOREVER, and
        # nothing else ever resets it: every later call raised
        # "HALF_OPEN (probing)" and that provider was dead for the life of the
        # process. The flag is now released in a finally, and an abandoned
        # probe additionally ages out via _probe_started_at.
        try:
            result = func(*args, **kwargs)
            with self._lock:
                self._failures = 0
                if self._state == self.HALF_OPEN:
                    self._state = self.CLOSED
                    log.info(f"⚡ CircuitBreaker [{self.name}] → CLOSED (recovered)")
            return result
        except AIEmptyResponse:
            # v15 FIX 6 (HIGH): an empty/safety-blocked reply means the provider
            # is UP — it answered, it just had nothing usable to say. Counting it
            # as a failure meant 5 borderline patient messages in a row opened
            # the Gemini breaker for 60s FOR EVERY TENANT. Treat as liveness:
            # don't increment failures; a successful probe closes the circuit.
            with self._lock:
                if self._state == self.HALF_OPEN:
                    self._state    = self.CLOSED
                    # v16g2 FIX N12: match the success path — a breaker
                    # "recovered" via an empty-reply probe otherwise kept
                    # failures at 4 and re-opened on the next single blip.
                    self._failures = 0
                    log.info(f"⚡ CircuitBreaker [{self.name}] → CLOSED "
                             f"(probe answered, empty reply)")
            raise
        except Exception:
            with self._lock:
                self._failures += 1
                if is_probe or self._state == self.HALF_OPEN:
                    # probe failed → straight back to OPEN, restart the timer.
                    self._state          = self.OPEN
                    self._opened_at      = time.monotonic()
                    log.error(f"⚡ CircuitBreaker [{self.name}] → OPEN (probe failed)")
                elif self._failures >= self._threshold:
                    self._state     = self.OPEN
                    self._opened_at = time.monotonic()
                    log.error(f"⚡ CircuitBreaker [{self.name}] → OPEN (failures={self._failures})")
            raise
        finally:
            # v16g5 FIX R5-H2: the ONLY place the probe gate is released.
            if is_probe:
                with self._lock:
                    self._probe_inflight = False


_gemini_breaker   = CircuitBreaker("Gemini",   failure_threshold=5, reset_timeout=60.0)
_openai_breaker   = CircuitBreaker("OpenAI",   failure_threshold=5, reset_timeout=60.0)
_claude_breaker   = CircuitBreaker("Claude",   failure_threshold=5, reset_timeout=60.0)
_whatsapp_breaker  = CircuitBreaker("WhatsApp",  failure_threshold=3, reset_timeout=30.0)
_instagram_breaker = CircuitBreaker("Instagram", failure_threshold=3, reset_timeout=30.0)  # v10
_qdrant_breaker    = CircuitBreaker("Qdrant",    failure_threshold=3, reset_timeout=30.0)  # v12 #23


# ─────────────────────────────────────────────────────────────────────────────
# 🤖  MULTI-AI FALLBACK ENGINE  (v8 FIX #9, #10, #11)
#     Gemini → OpenAI → Claude with exponential back-off + jitter
#     Client singletons — NOT recreated per request (major v7 bug fixed)
# ─────────────────────────────────────────────────────────────────────────────
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

    active = [k for k, v in AI_PROVIDERS_ACTIVE.items() if v]
    if not active:
        log.error("❌ No AI providers configured! Set at least one API key.")
    else:
        log.info(f"🤖 AI Fallback Chain: {' → '.join(active)}")


class AIEmptyResponse(Exception):
    """v14g3 BUG 18: raised when a provider returns no usable text (e.g. a safety
    block). Treated as 'this provider had no answer' → fall through to the next
    one WITHOUT retry-spamming and without slamming the circuit breaker."""


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


# ─────────────────────────────────────────────────────────────────────────────
# 📱  WHATSAPP CLOUD API  (Official Meta Business API)
# ─────────────────────────────────────────────────────────────────────────────
WHATSAPP_API_BASE = f"https://graph.facebook.com/{cfg.GRAPH_API_VERSION}"  # v10: v19 → env (v21.0)
# v15g3 FIX 2 (HIGH-PERF): a bare Session() keeps urllib3 defaults — pool_maxsize
# =10 and ZERO retries. The worker pool + outbox drain + scheduler easily exceed
# 10 concurrent sends; every connection past #10 was DISCARDED after use, so the
# next send paid a fresh TCP+TLS handshake to graph.facebook.com (~200-400ms from
# India). Under a burst this throttled the whole fleet's reply latency.
# Fix: mount an HTTPAdapter with a real pool, plus CONNECT-only retries.
# connect-retries are double-send safe — the request was never transmitted —
# while read/status retries stay at 0 so a slow Meta 200 can never be re-sent.
_wa_session = requests.Session()
_wa_session.mount("https://", HTTPAdapter(
    pool_connections=8,
    pool_maxsize=64,
    max_retries=Retry(total=None, connect=2, read=0, redirect=0, status=0,
                      backoff_factor=0.3),
))


# ── v13 TRUE MULTI-TENANT: token-death detection ─────────────────────────────
# When a CLINIC's own token expires/revokes, Meta returns 401/403 or one of these
# error codes. We surface it as a typed exception so the send layer can flag that
# specific clinic 'needs_reauth' and alert YOU — instead of silently logging while
# that clinic's bot goes dark and the owner calls angry days later.
class WhatsAppAuthError(Exception):
    def __init__(self, code, message=""):
        self.code = code
        super().__init__(f"WA auth error code={code}: {message}")


# Meta auth/permission codes: 190 expired, 102 session, 10 permission,
# 200 perm, 803 invalid object, 0/3 sometimes wrap OAuth failures.
_WA_AUTH_FAIL_CODES = {190, 102, 10, 200, 803, 463, 467}


def _safe_ct_eq(a: str, b: str) -> bool:
    """v16g3 FIX R3-M1: hmac.compare_digest raises TypeError on non-ASCII str
    input — a probe with a garbage hub.verify_token / X-Api-Key /
    X-Metrics-Token 500'd instead of 401/403-ing. v16g2 FIX L6 guarded only
    the admin header; this is the shared guard for every header/param path."""
    try:
        return hmac.compare_digest(a or "", b or "")
    except (TypeError, UnicodeError):
        return False


def verify_meta_signature(raw_body: bytes, signature_header: str,
                          app_secret: str) -> bool:
    """v10: shared by WhatsApp + Instagram webhooks (same X-Hub-Signature-256).

    v14g3 BUG 7: an empty app secret used to mean 'accept everything', so a
    deployment that forgot to set WHATSAPP_APP_SECRET silently accepted FORGED
    webhooks from anyone who found the URL. Now an empty secret skips the check
    ONLY in dev; under STRICT_PROD (or REQUIRE_WEBHOOK_SIGNATURE) a missing
    secret is fail-CLOSED — in production an unsigned webhook is an attack, not
    a convenience."""
    if not app_secret:
        if cfg.STRICT_PROD or cfg.REQUIRE_WEBHOOK_SIGNATURE:
            log.error("🛑 Webhook rejected: signature required but no app secret "
                      "set (configure WHATSAPP_APP_SECRET / INSTAGRAM_APP_SECRET).")
            return False
        return True  # dev mode only — explicitly insecure
    if not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


# v15 FIX 17: removed the dead verify_whatsapp_signature wrapper — it was never
# called; both webhooks invoke verify_meta_signature directly.


def _split_wa_chunks(message: str, limit: int = 4096) -> List[str]:
    """v16g4 FIX M7: Meta's text body cap is 4,096 CHARS — 1,000 tokens of
    Tamil comfortably exceeds it, and message[:4096] truncated silently,
    mid-word. Split on whitespace (falling back to a hard cut only for a
    single unbroken 4k+ run) so long replies arrive complete as sequenced
    messages instead of ending mid-sentence."""
    message = message or ""
    if len(message) <= limit:
        return [message]
    chunks, rest = [], message
    while len(rest) > limit:
        cut = rest.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = rest.rfind(" ", 0, limit)
        if cut < limit // 2:          # one unbroken ≥4k run: hard cut
            cut = limit
        chunks.append(rest[:cut].rstrip())
        rest = rest[cut:].lstrip()
    if rest:
        chunks.append(rest)
    return chunks


def _wa_send_text(to_phone: str, message: str,
                  phone_id: str = "", token: str = "") -> Dict:
    """v13: per-tenant aware. phone_id/token default to the GLOBAL env creds, so
    your FIRST clinic and every old call site keep working untouched. Multi-tenant
    callers pass the clinic's OWN number+token. On an auth failure (dead clinic
    token) this raises WhatsAppAuthError so the caller can self-heal.
    v16g4 FIX M7: messages >4,096 chars are chunk-sent in order; the LAST
    chunk's API response is returned so callers keep their existing shape."""
    phone_id = phone_id or cfg.WHATSAPP_PHONE_ID
    token    = token    or cfg.WHATSAPP_TOKEN
    if not token or not phone_id:
        return {"error": "not_configured"}
    url = f"{WHATSAPP_API_BASE}/{phone_id}/messages"
    last: Dict = {}
    # v16g5 FIX R5-M3: a 4xx/5xx on chunk 2 raised AFTER chunk 1 had already
    # been delivered; _meta_send_retry then restarted the whole loop and the
    # patient received the first 4,096 characters TWICE — and a long clinical
    # answer is exactly the message that chunks. Record per-chunk progress
    # under a short-lived content-derived key so a retry RESUMES. Best-effort:
    # a cache miss degrades to the old behaviour, never to a dropped message.
    _chunks = _split_wa_chunks(message)
    _ck = _done = None
    if len(_chunks) > 1:
        _ck = "wachunk:" + hashlib.sha256(
            f"{to_phone}|{phone_id}|{message}".encode("utf-8")).hexdigest()[:24]
        try:
            _done = int(brain_cache.get(_ck) or 0)
        except (TypeError, ValueError):
            _done = 0
        if _done >= len(_chunks):
            # v16g6 FIX R6-M7: a STALE completion marker (the final delete
            # below failed and was swallowed) made an identical repeat
            # message within the TTL skip EVERY chunk and return {} — a
            # silent non-send the caller records as delivered. A marker that
            # claims "all chunks done" can only be stale on a NEW call: this
            # call exists because the caller wants a send. Start fresh.
            _done = 0
        if _done:
            log.info(f"📤 resuming chunked send at part {_done + 1}/{len(_chunks)} "
                     f"(v16g5 FIX R5-M3)")
    for _idx, chunk in enumerate(_chunks):
        if _done and _idx < _done:
            continue
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type":    "individual",
            "to":                to_phone,
            "type":              "text",
            "text":              {"body": chunk},
        }
        resp = _wa_session.post(
            url,
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json"},
            json=payload,
            timeout=(cfg.HTTP_CONNECT_TIMEOUT, 15),
        )
        if resp.status_code >= 400:
            # v10: Meta says EXACTLY what is wrong. error.code 190 = expired token.
            err  = {}
            try:
                if "json" in resp.headers.get("content-type", ""):
                    err = (resp.json() or {}).get("error", {}) or {}
            except Exception:
                err = {}
            code = err.get("code")
            log.error(f"❌ WhatsApp send {resp.status_code} code={code} → {resp.text[:500]}")
            if resp.status_code in (401, 403) or code in _WA_AUTH_FAIL_CODES:
                raise WhatsAppAuthError(code, err.get("message", "auth failed"))
        resp.raise_for_status()
        if _ck:                                          # v16g5 FIX R5-M3
            try:
                # v16g6 FIX R6-L10: progress is recorded BEFORE parsing the
                # body — a Meta 200 with a non-JSON body used to raise first,
                # so the retry re-sent this chunk: the exact duplicate R5-M3
                # exists to prevent. Delivered is delivered.
                brain_cache.set(_ck, _idx + 1, ttl=600)
            except Exception:
                pass
        try:
            last = resp.json()
        except Exception:
            last = {"note": "non-json 2xx body"}         # v16g6 FIX R6-L10
    if _ck:
        try:
            brain_cache.delete(_ck)
        except Exception:
            try:
                # v16g6 FIX R6-M7: second, independent chance to clear the
                # marker; the resume guard above self-heals the rest.
                brain_cache.set(_ck, 0, ttl=1)
            except Exception:
                pass
    return last


# ─────────────────────────────────────────────────────────────────────────────
# 🧵  BOUNDED BACKGROUND WORKER POOL  (v11 fix #1 + #11)
#   Webhooks return 200 instantly; heavy work (AI call, voice transcription,
#   outbound sends, RAG store) runs here. Bounded so a traffic burst can never
#   spawn unlimited threads and OOM a 512 MB Render dyno. Was: a fresh
#   threading.Thread per send/store (unbounded → thread explosion under load).
# ─────────────────────────────────────────────────────────────────────────────
_WORKER_POOL = ThreadPoolExecutor(
    max_workers=_env_int("WORKER_THREADS", "8"),
    thread_name_prefix="heonix-bg",
)

# v14g3 BUG 5: the ordered per-conversation drains run on _WORKER_POOL and hold
# a thread for the ENTIRE duration of an AI call. Previously fire-and-forget
# work (owner alerts, audit writes, RAG stores, outbox sends) was submitted to
# the SAME pool, so it queued behind slow AI calls and, under load, the 8 drain
# threads and competing bg tasks throttled each other (head-of-line blocking).
# Side-effect I/O now gets its OWN pool, fully decoupled from the drains.
_IO_POOL = ThreadPoolExecutor(
    max_workers=_env_int("IO_THREADS", "16"),
    thread_name_prefix="heonix-io",
)

# v15 FIX 1 (CRITICAL): this Event was referenced by the janitor loop (its very
# first statement) and by the shutdown handler — but it was NEVER DEFINED. The
# janitor thread therefore died with a NameError milliseconds after every boot,
# silently killing: the periodic outbox drain, stuck-'processing' row recovery,
# idempotency/webhook_log cleanup, in-process cache pruning (a slow RAM leak in
# no-Redis mode), the ENTIRE Gen-4 scheduler (reminders + follow-ups), and the
# DPDP retention purge. One line. This one line is v15's biggest upgrade.
_shutdown_event = threading.Event()


_IO_QUEUE_MAX = _env_int("IO_QUEUE_MAX", "2000")     # v16g5 FIX R5-L7


def submit_bg(fn: Callable, *args, **kwargs) -> None:
    """Fire-and-forget onto the dedicated I/O pool (v14g3 BUG 5 — kept separate
    from the conversation-drain pool so alerts/audit/RAG never queue behind a
    slow AI call). Never raises into the caller. If the pool is shutting down
    (SIGTERM in flight), runs inline so in-progress work is never lost."""
    # v16g5 FIX R5-L7: the pool is bounded in THREADS, not in QUEUED WORK.
    # ThreadPoolExecutor's work queue is unbounded, so .submit() never raises
    # under load — it just grows RAM until the dyno is OOM-killed, and the
    # RuntimeError fallback below only fires AFTER shutdown. Shed load at an
    # explicit depth instead: audit/analytics writes are the right thing to
    # drop when the box is already drowning, and a dropped one is now COUNTED
    # rather than silently swallowing memory.
    try:
        _q = getattr(_IO_POOL, "_work_queue", None)
        if _q is not None and _q.qsize() > _IO_QUEUE_MAX:
            analytics.inc("bg.shed")
            if brain_cache.setnx("warn:bg_queue", ttl=300):
                log.error(f"🛑 background I/O queue over {_IO_QUEUE_MAX} deep — "
                          f"shedding fire-and-forget work (v16g5 FIX R5-L7). "
                          f"The box is saturated; scale workers or check for a "
                          f"stalled outbound provider.")
            return
    except Exception:
        pass
    try:
        _IO_POOL.submit(fn, *args, **kwargs)
    except RuntimeError:
        # v16g4 FIX L10: the old inline fallback ran the task ON THE CALLER'S
        # thread during shutdown — a webhook 200 could block behind a live
        # Meta call. A plain daemon thread is unbounded but shutdown-scoped:
        # only reachable after _IO_POOL rejects, i.e. for the final seconds
        # of a SIGTERM drain, so it cannot become the pre-v11 thread
        # explosion. In-progress work is still never lost and the caller
        # returns immediately.
        try:
            threading.Thread(target=fn, args=args, kwargs=kwargs,
                             daemon=True,
                             name="heonix-bg-shutdown").start()
        except Exception as exc:
            log.error(f"❌ shutdown bg fallback failed: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 🔢  v14 BUG 43 FIX — PER-CONVERSATION ORDERED EXECUTION
#   Problem: webhook handlers pushed every inbound message onto an 8-thread pool.
#   A ThreadPoolExecutor gives NO ordering guarantee, so a patient firing 3 quick
#   messages could have msg #3 processed before msg #1 → the history handed to the
#   AI is scrambled → wrong/contradictory reply, and replies arrive out of order.
#
#   Fix: tasks that share a key (one conversation = one patient on one business
#   line) run STRICTLY in submission order, one at a time, on a single drainer.
#   Different keys still run fully in parallel across the pool — so global
#   throughput is unchanged, only per-conversation order is enforced.
# ─────────────────────────────────────────────────────────────────────────────
# v16g4 FIX P6: one shared renewer for every in-flight conversation lease —
# the old design spawned a fresh heartbeat THREAD per message (thread churn on
# every single webhook) just to renew one lock. Registry + single daemon
# scanner; drains register on acquire and deregister in finally.
_LEASE_REG: Dict[str, str] = {}
_LEASE_REG_LOCK = threading.Lock()
_LEASE_SCANNER_ON = False


def _lease_scanner() -> None:
    while not _shutdown_event.wait(max(5, cfg.CONV_LOCK_TTL // 3)):
        with _LEASE_REG_LOCK:
            items = list(_LEASE_REG.items())
        for _k, _lease in items:
            try:
                brain_cache.renew(f"conv:{_k}", _lease, cfg.CONV_LOCK_TTL)
            except Exception:
                pass


def _ensure_lease_scanner() -> None:
    global _LEASE_SCANNER_ON
    with _LEASE_REG_LOCK:
        if _LEASE_SCANNER_ON:
            return
        _LEASE_SCANNER_ON = True
    threading.Thread(target=_lease_scanner, daemon=True,
                     name="conv-lease-scan").start()


class OrderedKeyedRunner:
    """Serializes tasks per key (FIFO), parallel across keys. Exactly one drainer
    is live per active key at any moment (enforced under a single lock), which is
    what makes the ordering race-proof even while many messages arrive at once."""

    def __init__(self, pool: ThreadPoolExecutor, max_pending_per_key: int = 50):
        self._pool      = pool
        self._max_q     = max_pending_per_key
        self._queues: Dict[str, deque] = {}
        self._active: set               = set()
        self._lock      = threading.Lock()

    def submit(self, key: str, fn: Callable, *args, **kwargs) -> bool:
        """Queue a task for `key`. Returns False if this key's backlog is full
        (flood guard — a single conversation can't OOM the dyno) — the caller
        treats that exactly like a dropped/duplicate inbound message."""
        start = False
        with self._lock:
            q = self._queues.get(key)
            if q is None:
                q = deque()
                self._queues[key] = q
            if len(q) >= self._max_q:
                analytics.inc("ordered.queue_full")
                return False
            q.append((fn, args, kwargs))
            if key not in self._active:
                self._active.add(key)
                start = True
        if start:
            try:
                self._pool.submit(self._drain, key)
            except RuntimeError:
                # pool shutting down (SIGTERM) → drain inline so nothing is lost
                self._drain(key)
        return True

    def _drain(self, key: str) -> None:
        while True:
            with self._lock:
                q = self._queues.get(key)
                if not q:
                    # confirmed empty under lock → release the key. A submit that
                    # races in right after will see key not-active and start a
                    # fresh drainer, so no item is ever stranded.
                    self._active.discard(key)
                    self._queues.pop(key, None)
                    return
                fn, args, kwargs = q.popleft()
            # v14g5 FIX 6: take a CROSS-WORKER per-conversation mutex so the same
            # conversation can't be processed concurrently on two gunicorn workers
            # (which would interleave and scramble history). Bounded wait — if we
            # can't acquire it we proceed rather than stall forever. NOTE: this stops
            # concurrent corruption, but strict ARRIVAL order across separate POSTs
            # landing on different workers still needs WEB_CONCURRENCY=1 (use threads).
            lease  = None
            waited = 0.0
            _nap   = 0.05
            while waited < cfg.CONV_LOCK_WAIT_SECS:   # v15g4 FIX D2: env-tunable
                lease = brain_cache.lock(f"conv:{key}", ttl=cfg.CONV_LOCK_TTL)
                if lease:
                    break
                time.sleep(_nap)                      # v16g4 FIX P6: growing nap
                waited += _nap
                _nap = min(0.4, _nap * 2)             # 20 Hz spin → gentle backoff
            # v15g2 FIX M4: worst-case AI path (MAX_RETRIES×AI_TIMEOUT + backoff,
            # × up to 3 fallback providers) can run for minutes — far past
            # CONV_LOCK_TTL (60s). The lease then expired MID-TURN, another
            # worker could grab the same conversation, and the exact
            # interleaving FIX 6 exists to prevent came back precisely when the
            # AI was slow. A tiny heartbeat renews the lease while fn runs; it
            # stops the instant fn returns (bounded: one sleeping thread per
            # in-flight drain, ≤ pool size).
            if lease:
                # v16g4 FIX P6: register with the shared scanner (replaces the
                # per-task heartbeat thread — same mid-turn renewal guarantee
                # from v15g2 FIX M4, minus one thread spawn per message).
                _ensure_lease_scanner()
                with _LEASE_REG_LOCK:
                    _LEASE_REG[key] = lease
            try:
                fn(*args, **kwargs)
            except Exception as exc:
                log.error(f"❌ ordered task error [{key}]: {exc}", exc_info=True)
            finally:
                if lease:
                    with _LEASE_REG_LOCK:
                        _LEASE_REG.pop(key, None)
                    brain_cache.unlock(f"conv:{key}", lease)


_ORDERED = OrderedKeyedRunner(
    _WORKER_POOL,
    max_pending_per_key=_env_int("ORDERED_MAX_PENDING", "50"),
)


def submit_ordered(key: str, fn: Callable, *args, **kwargs) -> bool:
    """Public entry: run fn in-order for `key`. False = backlog full (drop)."""
    return _ORDERED.submit(key, fn, *args, **kwargs)


# ── v12: a tiny separate executor used ONLY to put a hard wall-clock ceiling on
#    a blocking call (RAG embed / vector search). Kept distinct from _WORKER_POOL
#    so a timeout wrapper can never end up waiting on the same pool it runs in.
_TIMEOUT_POOL = ThreadPoolExecutor(
    max_workers=_env_int("TIMEOUT_THREADS", "8"),   # v14g3 BUG 6: was 4
    thread_name_prefix="heonix-to",
)


def _call_with_timeout(fn: Callable, timeout: float, *args, **kwargs):
    """Run fn with a hard wall-clock ceiling; raises TimeoutError on overrun so
    the surrounding circuit breaker counts it as a failure (v12 #9/#23).

    v14g3 BUG 6 — HONEST LIMITATION: Python cannot cancel a running thread, so on
    timeout the underlying call keeps executing until it returns on its own. The
    REAL guard is the breaker: a few RAG timeouts open the Qdrant breaker, which
    then short-circuits further submits for reset_timeout seconds — so leaked
    threads drain instead of piling up. We also doubled this pool (4 → 8) for
    headroom, and RAG is now the ONLY caller: the primary AI calls use native SDK
    timeouts (BUG 2), which need no extra thread at all."""
    fut = _TIMEOUT_POOL.submit(fn, *args, **kwargs)
    return fut.result(timeout=timeout)


# ── v12 #24: WhatsApp bold is a *single* asterisk and it has no headings.
#    Gemini emits standard Markdown (**bold**, ## Heading, [text](url)) which
#    renders as literal junk on WhatsApp. Normalise outbound text first.
_MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
# v16g2 FIX C5: require whitespace after the hashes (CommonMark headings do) —
# "#1 clinic in Coimbatore" no longer loses its "#".
_MD_HEAD_RE = re.compile(r"^\s{0,3}#{1,6}\s+", re.MULTILINE)
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")


def _to_whatsapp_markdown(text: str) -> str:
    if not text:
        return text
    text = _MD_LINK_RE.sub(r"\1 (\2)", text)   # [label](url) → label (url)
    text = _MD_BOLD_RE.sub(r"*\1*", text)        # **bold** → *bold*
    text = _MD_HEAD_RE.sub("", text)             # drop leading # heading markers
    return text


def _is_retryable_meta_error(exc: Exception) -> bool:
    """v12 #36: retry ONLY transient failures. A 4xx like 190 (expired token) or
    131047 (outside 24h window) is permanent — retrying it just burns calls."""
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True
    resp = getattr(exc, "response", None)
    code = getattr(resp, "status_code", None)
    return code in (429, 500, 502, 503, 504)


def _meta_send_retry(fn: Callable, *args):
    """Bounded retry wrapper for Meta sends. Sits INSIDE the circuit breaker, so
    the breaker only sees a failure after transient retries are exhausted."""
    last = None
    for attempt in range(cfg.META_SEND_RETRIES + 1):
        try:
            return fn(*args)
        except Exception as exc:
            last = exc
            if attempt >= cfg.META_SEND_RETRIES or not _is_retryable_meta_error(exc):
                raise
            time.sleep(min((2 ** attempt) * 0.5 + random.uniform(0, 0.3), 4.0))
    if last:
        raise last


def _flag_channel_reauth(customer_id: str, detail: str) -> None:
    """v13: a clinic's token is dead → mark that clinic 'needs_reauth' and ping
    ADMIN_ALERT_PHONE (over the GLOBAL line) so YOU re-attach it before the clinic
    notices. customer_id='' (a global-creds send) is a no-op — we never flag the
    whole fleet, and the admin-alert send below passes customer_id='' so it can
    never recurse into flagging itself."""
    if not customer_id:
        return
    try:
        _pid = _igid = ""          # v16g3 FIX R3-L1: dead is_pg removed
        with _db_pool.get() as conn:
            # column may not exist on a very old DB that skipped _migrate_v12 — guard
            if _column_exists(conn, "customer_brains", "channel_status"):
                _execute(conn,
                    "UPDATE customer_brains SET channel_status=?, updated_at=? "
                    "WHERE customer_id=?",
                    ("needs_reauth", _now(), customer_id))
            # v14g5 FIX 8: read the routing keys so we can bust their caches below.
            try:
                if _column_exists(conn, "customer_brains", "wa_phone_number_id"):
                    cur = _execute(conn, "SELECT wa_phone_number_id, instagram_id "
                                         "FROM customer_brains WHERE customer_id=?", (customer_id,))
                    _r = cur.fetchone()
                    if _r:
                        # v16g4 FIX L14: the old isinstance-tuple guard silently
                        # SKIPPED the routing-cache bust for tuple rows — a
                        # guard that hid the case instead of handling it. Tuple
                        # rows are positional in SELECT order.
                        if isinstance(_r, tuple):
                            _pid  = (_r[0] or "") if len(_r) > 0 else ""
                            _igid = (_r[1] or "") if len(_r) > 1 else ""
                        else:
                            _pid  = _r["wa_phone_number_id"] or ""
                            _igid = _r["instagram_id"] or ""
            except Exception:
                pass
        # v14g5 FIX 8: bust the ROUTING caches too, not just the brain cache, so the
        # send path stops using the stale brain (with the dead token) immediately.
        brain_cache.delete(f"brain:{customer_id}")     # v16g6 FIX R6-L6
        if _pid:
            brain_cache.delete(f"wapid:{_pid}")
            brain_cache.delete(f"wa_route:{_pid}")
        if _igid:
            brain_cache.delete(f"igid:{_igid}")
        brain_cache.delete("wa_route:__single__")
        analytics.inc("channel.reauth_flagged")
        log.error(f"🔑 Clinic {customer_id} token DEAD → needs_reauth ({detail})")
        if cfg.ADMIN_ALERT_PHONE and cfg.WHATSAPP_PHONE_ID and cfg.WHATSAPP_TOKEN:
            send_whatsapp_async(
                cfg.ADMIN_ALERT_PHONE,
                f"⚠️ HEONIX: clinic {customer_id} WhatsApp token failed ({detail}). "
                f"Re-attach via POST /admin/customer/{customer_id}/channel",
                phone_id=cfg.WHATSAPP_PHONE_ID, token=cfg.WHATSAPP_TOKEN,
                customer_id="")   # ← '' so this alert never re-flags anything
    except Exception as exc:
        log.error(f"❌ reauth flag failed for {customer_id}: {exc}")


def _wa_send_now(to_phone: str, message: str, phone_id: str = "",
                 token: str = "", customer_id: str = "") -> bool:
    """v14: the actual WhatsApp send body, shared by the async and sync wrappers.
    Runs the breaker + transient-retry path and self-heals on token death. Never
    raises into the caller (so a failed send can't break a serialized drain).
    v16g2 FIX L1: returns True only when Meta accepted the message — the docstring
    of the phone-request path promised a bool that never existed, so the M14 fix
    (set the 7-day ask-guard only on delivery) finally has a signal to trust."""
    msg = _to_whatsapp_markdown(message)        # v12 #24
    try:
        res = _whatsapp_breaker.call(_meta_send_retry, _wa_send_text,
                                     to_phone, msg, phone_id, token)  # v12 #36 / v13
        if isinstance(res, dict) and res.get("error"):        # v16g2 FIX L1
            log.warning(f"⚠️  WhatsApp send skipped ({res.get('error')}) → "
                        f"{pii_vault.mask(to_phone)}")
            return False
        analytics.inc("whatsapp.sent")
        return True
    except WhatsAppAuthError as exc:            # v13: token death → self-heal
        analytics.inc("whatsapp.auth_fail")
        _flag_channel_reauth(customer_id, f"code={exc.code}")
        return False
    except Exception as exc:
        analytics.inc("whatsapp.error")
        log.error(f"❌ WhatsApp send failed → {pii_vault.mask(to_phone)}: {exc}")
        return False


def _wa_send_interactive(to_phone: str, payload_interactive: Dict,
                         phone_id: str = "", token: str = "") -> Dict:
    """v14g4: send a WhatsApp INTERACTIVE message (reply-buttons or a list).
    Same per-tenant creds + auth-death semantics as _wa_send_text. Buttons/lists
    let a patient TAP a slot instead of typing — far fewer mis-bookings."""
    phone_id = phone_id or cfg.WHATSAPP_PHONE_ID
    token    = token    or cfg.WHATSAPP_TOKEN
    if not token or not phone_id:
        return {"error": "not_configured"}
    url  = f"{WHATSAPP_API_BASE}/{phone_id}/messages"
    body = {"messaging_product": "whatsapp", "recipient_type": "individual",
            "to": to_phone, "type": "interactive", "interactive": payload_interactive}
    resp = _wa_session.post(
        url, headers={"Authorization": f"Bearer {token}",
                      "Content-Type": "application/json"},
        json=body, timeout=(cfg.HTTP_CONNECT_TIMEOUT, 15))
    if resp.status_code >= 400:
        err  = {}
        try:
            if "json" in resp.headers.get("content-type", ""):
                err = (resp.json() or {}).get("error", {}) or {}
        except Exception:
            err = {}
        code = err.get("code")
        log.error(f"❌ WA interactive {resp.status_code} code={code} → {resp.text[:400]}")
        if resp.status_code in (401, 403) or code in _WA_AUTH_FAIL_CODES:
            raise WhatsAppAuthError(code, err.get("message", "auth failed"))
    resp.raise_for_status()
    return resp.json()


def wa_send_list_now(to_phone: str, body_text: str, button_label: str,
                     rows: List[Dict], phone_id: str = "", token: str = "",
                     customer_id: str = "", header: str = "") -> bool:
    """v14g4: send a single-section list message. `rows` = [{id,title,description?}]
    (max 10 per WhatsApp). Returns True on success. Never raises (self-heals on
    token death) so it is safe inside a serialized drain. Falls back to plain text
    by returning False so the caller can degrade gracefully."""
    section = {"title": button_label[:24] or "Options",
               "rows": [{"id": str(r["id"])[:200],
                         "title": str(r["title"])[:24],
                         "description": str(r.get("description", ""))[:72]}
                        for r in rows[:10]]}
    inter = {"type": "list",
             "body": {"text": body_text[:1024]},
             "action": {"button": (button_label[:20] or "Choose"),
                        "sections": [section]}}
    if header:
        inter["header"] = {"type": "text", "text": header[:60]}
    try:
        _whatsapp_breaker.call(_meta_send_retry, _wa_send_interactive,
                               to_phone, inter, phone_id, token)
        analytics.inc("whatsapp.list_sent")
        return True
    except WhatsAppAuthError as exc:
        analytics.inc("whatsapp.auth_fail")
        _flag_channel_reauth(customer_id, f"code={exc.code}")
    except Exception as exc:
        analytics.inc("whatsapp.interactive_error")
        log.warning(f"⚠️  list send failed → {pii_vault.mask(to_phone)}: {exc}")
    return False


def wa_send_buttons_now(to_phone: str, body_text: str, buttons: List[Dict],
                        phone_id: str = "", token: str = "",
                        customer_id: str = "") -> bool:
    """v14g4: send up to 3 reply buttons. `buttons` = [{id,title}]. Returns True
    on success, never raises. Used for yes/no confirmations (cancel, reschedule)."""
    inter = {"type": "button",
             "body": {"text": body_text[:1024]},
             "action": {"buttons": [
                 {"type": "reply",
                  "reply": {"id": str(b["id"])[:256], "title": str(b["title"])[:20]}}
                 for b in buttons[:3]]}}
    try:
        _whatsapp_breaker.call(_meta_send_retry, _wa_send_interactive,
                               to_phone, inter, phone_id, token)
        analytics.inc("whatsapp.buttons_sent")
        return True
    except WhatsAppAuthError as exc:
        analytics.inc("whatsapp.auth_fail")
        _flag_channel_reauth(customer_id, f"code={exc.code}")
    except Exception as exc:
        analytics.inc("whatsapp.interactive_error")
        log.warning(f"⚠️  buttons send failed → {pii_vault.mask(to_phone)}: {exc}")
    return False


_PHONE_REQUEST_BODY = ("To send you appointment reminders, could you share "
                       "your mobile number? Tap below — or just type it. "
                       "It's optional and stays with the clinic only. 🙏")


def _wa_send_phone_request(to_id: str, phone_id: str = "", token: str = "",
                           customer_id: str = "", lang: str = "en") -> bool:
    """v16 U3: send Meta's phone-number-request CTA to a username patient.
    Per BSP docs, tapping it delivers a `contacts` webhook carrying the shared
    number (handled in _process_wa_message). If the interactive type string is
    rejected (not yet GA in this region / naming differs — see cfg notes), we
    fall back to a plain-text ask; the typed-number capture path covers the
    reply either way. Never raises."""
    inter = {"type": cfg.WA_PHONE_REQUEST_TYPE,
             "body": {"text": _t("phone_request", lang)[:1024]},   # v16g4 FIX M8
             "action": {"name": cfg.WA_PHONE_REQUEST_ACTION}}
    try:
        _whatsapp_breaker.call(_meta_send_retry, _wa_send_interactive,
                               to_id, inter, phone_id, token)
        analytics.inc("whatsapp.phone_request_sent")
        return True
    except WhatsAppAuthError as exc:
        analytics.inc("whatsapp.auth_fail")
        _flag_channel_reauth(customer_id, f"code={exc.code}")
        return False
    except Exception as exc:
        log.info(f"ℹ️  phone-request interactive rejected "
                 f"({str(exc)[:120]}) — falling back to text ask.")
        analytics.inc("whatsapp.phone_request_fallback")
        return send_whatsapp_sync(to_id, _t("phone_request", lang),   # v16g4 FIX M8
                                  phone_id, token, customer_id)


def _maybe_request_phone(customer_id: str, chat_id: str,
                         phone_id: str = "", token: str = "",
                         lang: str = "en") -> None:
    """v16 U3: ask a BSUID-only patient for their number ONCE per 7 days —
    right after a booking succeeds, which is the moment the number actually
    matters (reminders).
    v16g2 FIX H3: ONE key used to be both the 7-day nag guard AND the capture
    window — for a full week, any digits the patient typed (an Aadhaar, an
    order id, a lab's number they were asking about) became "their phone" and
    swallowed the actual question. Split: `numreq_asked` (7d) only guards
    re-asking; `numreq_window` (15 min) is the ONLY thing typed-capture
    listens to.
    v16g2 FIX M14: the once-per-7-days guard is no longer burned before the
    ask is even delivered — a short `numreq_inflight` claim serialises
    concurrent turns, and the 7-day key is set ONLY after
    _wa_send_phone_request reports success (a real bool since FIX L1)."""
    if not cfg.ENABLE_PHONE_CAPTURE or not _is_bsuid(chat_id):
        return
    if crm_get_real_phone(customer_id, chat_id):
        return
    if brain_cache.get(f"numreq_asked:{customer_id}:{chat_id}"):
        return    # already asked recently (7-day nag guard)
    if not brain_cache.setnx(f"numreq_inflight:{customer_id}:{chat_id}", ttl=120):
        return    # an ask is already in flight (v16g2 FIX M14)

    def _ask():
        try:
            ok = _wa_send_phone_request(chat_id, phone_id, token, customer_id,
                                        lang=lang)   # v16g4 FIX M8
            if ok:                                            # v16g2 FIX M14
                brain_cache.set(f"numreq_asked:{customer_id}:{chat_id}", 1,
                                ttl=86400 * 7)
                brain_cache.set(f"numreq_window:{customer_id}:{chat_id}", 1,
                                ttl=900)                       # v16g2 FIX H3
        finally:
            brain_cache.delete(f"numreq_inflight:{customer_id}:{chat_id}")

    submit_bg(_ask)


def send_whatsapp_async(to_phone: str, message: str,
                        phone_id: str = "", token: str = "",
                        customer_id: str = "") -> None:
    """v13: per-tenant aware + self-healing. phone_id/token default to global env
    (backward compatible — old 2-arg calls still work). On a dead clinic token,
    flags that clinic needs_reauth and alerts you instead of failing silently."""
    submit_bg(_wa_send_now, to_phone, message, phone_id, token, customer_id)


def send_whatsapp_sync(to_phone: str, message: str, phone_id: str = "",
                       token: str = "", customer_id: str = "") -> bool:
    """v14 Bug 43: blocking patient reply, used ONLY inside the per-conversation
    serialized runner. Because processing for one patient is already one-at-a-time,
    sending in-thread guarantees reply N is on the wire before reply N+1 is even
    generated — so the patient never sees answers arrive out of order.
    v16g2 FIX L1: now returns the real send outcome."""
    return _wa_send_now(to_phone, message, phone_id, token, customer_id)


def _wa_send_template(to_phone: str, template: str, lang: str,
                      body_param: str, phone_id: str = "", token: str = "") -> Dict:
    """v11 #4: template messages work OUTSIDE the 24-hour window — the only
    reliable channel for owner alerts. Template must be pre-approved in the
    Meta console with one {{1}} body parameter.
    v13: per-tenant creds with global fallback + token-death detection."""
    phone_id = phone_id or cfg.WHATSAPP_PHONE_ID
    token    = token    or cfg.WHATSAPP_TOKEN
    if not token or not phone_id:
        return {"error": "not_configured"}
    # Meta rejects params containing newlines/tabs/4+ consecutive spaces.
    clean = re.sub(r"\s+", " ", body_param).strip()[:900]
    url = f"{WHATSAPP_API_BASE}/{phone_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {
            "name": template,
            "language": {"code": lang},
            "components": [{"type": "body",
                            "parameters": [{"type": "text", "text": clean}]}],
        },
    }
    resp = _wa_session.post(
        url,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json=payload, timeout=(cfg.HTTP_CONNECT_TIMEOUT, 15))
    if resp.status_code >= 400:
        err = {}
        try:
            if "json" in resp.headers.get("content-type", ""):
                err = (resp.json() or {}).get("error", {}) or {}
        except Exception:
            err = {}
        code = err.get("code")
        log.error(f"❌ WA template send {resp.status_code} code={code} → {resp.text[:500]}")
        if resp.status_code in (401, 403) or code in _WA_AUTH_FAIL_CODES:
            raise WhatsAppAuthError(code, err.get("message", "auth failed"))
    resp.raise_for_status()
    return resp.json()


def send_owner_alert_async(owner_phone: str, message: str,
                           phone_id: str = "", token: str = "",
                           customer_id: str = "") -> None:
    """v11 #4: ALL owner alerts (emergency / handoff / VIP / escalation) route
    here. With OWNER_ALERT_TEMPLATE set → template (works any time). Without it
    → free-form text, and if Meta rejects with 131047 (outside 24h window) we
    log exactly what to fix instead of failing silently.
    v13: alerts go from the CLINIC'S OWN number (per-tenant creds) so the owner
    recognises the sender; dead token → flag needs_reauth + alert you."""
    def _send():
        try:
            # v16g2 FIX L9: owner alerts were the ONE send class without the
            # transient-retry wrapper — a single 502 dropped an emergency alert
            # that every other path would have retried.
            if cfg.OWNER_ALERT_TEMPLATE:
                _whatsapp_breaker.call(_meta_send_retry, _wa_send_template,
                                       owner_phone, cfg.OWNER_ALERT_TEMPLATE,
                                       cfg.OWNER_ALERT_TEMPLATE_LANG, message,
                                       phone_id, token)
            else:
                _whatsapp_breaker.call(_meta_send_retry, _wa_send_text,
                                       owner_phone, message, phone_id, token)
            analytics.inc("owner_alert.sent")
        except WhatsAppAuthError as exc:        # v13: clinic token dead
            analytics.inc("owner_alert.auth_fail")
            _flag_channel_reauth(customer_id, f"owner-alert code={exc.code}")
        except Exception as exc:
            analytics.inc("owner_alert.error")
            extra = ""
            if "131047" in str(exc):
                extra = (" ← Meta 24h-window block. Fix: approve a template "
                         "with one {{1}} param and set OWNER_ALERT_TEMPLATE.")
            log.error(f"🚨 OWNER ALERT FAILED → {pii_vault.mask(owner_phone)}: "
                      f"{exc}{extra}")
    submit_bg(_send)


# ─────────────────────────────────────────────────────────────────────────────
# 📸  INSTAGRAM MESSAGING API  (v10 — official Meta Graph, same app family)
# ─────────────────────────────────────────────────────────────────────────────
def _ig_send_text(psid: str, message: str,
                  ig_id: str = "", token: str = "") -> Dict:
    """Send an Instagram DM reply. psid = the sender id from the webhook.
    v13: per-tenant IG creds with global fallback + token-death detection."""
    token = token or cfg.INSTAGRAM_TOKEN
    if not token:
        log.error("❌ Instagram NOT configured: set INSTAGRAM_TOKEN")
        return {"error": "not_configured"}
    target = ig_id or cfg.INSTAGRAM_ID or "me"
    url = f"https://graph.facebook.com/{cfg.GRAPH_API_VERSION}/{target}/messages"
    payload = {
        "recipient": {"id": psid},
        "message":   {"text": message[:1000]},   # IG text limit = 1000 chars
    }
    resp = _wa_session.post(
        url,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json"},
        json=payload,
        timeout=(cfg.HTTP_CONNECT_TIMEOUT, 15),
    )
    if resp.status_code >= 400:
        err = {}
        try:
            if "json" in resp.headers.get("content-type", ""):
                err = (resp.json() or {}).get("error", {}) or {}
        except Exception:
            err = {}
        code = err.get("code")
        log.error(f"❌ Instagram send {resp.status_code} code={code} → {resp.text[:500]}")
        if resp.status_code in (401, 403) or code in _WA_AUTH_FAIL_CODES:
            raise WhatsAppAuthError(code, err.get("message", "ig auth failed"))
    resp.raise_for_status()
    return resp.json()


def _ig_send_now(psid: str, message: str, ig_id: str = "",
                 token: str = "", customer_id: str = "") -> None:
    """v14: shared Instagram send body for the async + sync wrappers. Never raises."""
    # v12 #24: Instagram DMs have no markdown — strip bold/heading/link syntax
    # so the user never sees literal ** or ## characters.
    msg = _MD_LINK_RE.sub(r"\1 (\2)", message or "")
    msg = _MD_BOLD_RE.sub(r"\1", msg)
    msg = _MD_HEAD_RE.sub("", msg).replace("**", "")
    try:
        _instagram_breaker.call(_meta_send_retry, _ig_send_text,
                                psid, msg, ig_id, token)  # v12 #36 / v13
        analytics.inc("instagram.sent")
    except WhatsAppAuthError as exc:            # v13: IG token dead
        analytics.inc("instagram.auth_fail")
        _flag_channel_reauth(customer_id, f"ig code={exc.code}")
    except Exception as exc:
        analytics.inc("instagram.error")
        log.error(f"❌ Instagram send failed → {pii_vault.mask(psid)}: {exc}")


def send_instagram_async(psid: str, message: str,
                         ig_id: str = "", token: str = "",
                         customer_id: str = "") -> None:
    submit_bg(_ig_send_now, psid, message, ig_id, token, customer_id)


def send_instagram_sync(psid: str, message: str, ig_id: str = "",
                        token: str = "", customer_id: str = "") -> None:
    """v14 Bug 43: blocking IG reply inside the serialized runner — guarantees DM
    replies to the same follower go out in order."""
    _ig_send_now(psid, message, ig_id, token, customer_id)


# ─────────────────────────────────────────────────────────────────────────────
# 🏢  BUSINESS TEMPLATES  (auto-detect industry, assign AI persona)
# ─────────────────────────────────────────────────────────────────────────────
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
        "keywords": [
            # v16.4 FIX R10-C1 (SAFETY). The original nine words missed seven
            # of twenty real clinic types tested on 26-Jul: physiotherapy,
            # IVF/fertility, diagnostic lab, dialysis, homeopathy, maternity
            # nursing home and oncology all fell through to ELITE — whose
            # prompt carries NO diagnosis/prescription refusal and NO
            # anti-fabrication rule. For a healthcare business that is a
            # safety gap, not a branding one. Deliberately excluded: bare
            # "lab"/"labs" (AI Lab, design lab) and "care" (car care, pet
            # care, customer care) — healthcare is checked FIRST, so a
            # false positive there hijacks every other vertical.
            "clinic", "clinics", "health", "healthcare", "doctor", "doctors",
            "medical", "medicine", "medicines", "hospital", "hospitals",
            "dental", "dentist", "dentistry", "pharmacy", "pharmacies",
            "wellness", "patient", "patients",
            # specialities that carry no generic healthcare word
            "physiotherapy", "physio", "rehab", "rehabilitation",
            "ivf", "fertility", "maternity", "obstetrics", "gynaecology",
            "gynecology", "paediatric", "pediatric", "dermatology",
            "cardiology", "neurology", "psychiatry", "orthopaedic",
            "orthopedic", "oncology", "cancer", "chemotherapy", "dialysis",
            "nephrology", "urology", "gastroenterology", "pulmonology",
            "endocrinology", "rheumatology",
            # diagnostics and procedures
            "diagnostic", "diagnostics", "pathology", "radiology", "imaging",
            "ultrasound", "sonography", "endoscopy", "biopsy", "vaccination",
            "immunisation", "immunization",
            # traditional and allied systems
            "homeopathy", "homeopathic", "ayurveda", "ayurvedic", "siddha",
            "unani", "naturopathy", "physician", "surgeon", "surgery",
            "surgical", "nursing", "nurse", "therapist", "therapy",
            "optical", "optometry", "optician", "ophthalmology",
            "veterinary", "orthodontic", "endodontic", "periodontal",
        ],
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
            # v16.8 FIX R14-C1. Observed twice: asked \"I am 5 months pregnant,
            # is a dental X-ray safe?\" and \"I have a pacemaker, is an
            # ultrasonic scaler safe?\", HELIO answered with clinical safety
            # verdicts — lead aprons, which scalers interfere, whether
            # antibiotic prophylaxis is needed. None of that is a diagnosis or
            # a prescription, so the rule above did not reach it. Naming the
            # category explicitly is what closes the vocabulary gap.
            "NEVER judge whether any procedure, X-ray, anaesthetic, medicine or "
            "device is safe, unsafe, required or not required for a patient who "
            "has told you about a medical condition, pregnancy, implant, "
            "pacemaker, allergy or ongoing medication. That judgement belongs to "
            "the treating doctor who can see the full history. Say clearly that "
            "you cannot advise on it, tell them to raise it with the doctor "
            "(and their specialist where relevant), and offer to book. "
            "Always recommend a licensed professional for serious concerns. "
            # v33.0 FIX R33-C1. This line used to read "All data is handled
            # per DPDP Act / HIPAA compliance." and every healthcare tenant
            # said it to patients, in writing, at scale. HIPAA is a US statute
            # binding US covered entities and their business associates; an
            # Indian clinic is not one, so the claim was simply false. DPDP was
            # asserted just as flatly — a factual claim about how this SYSTEM
            # operates, which is not a chatbot's to make on the clinic's behalf.
            # The whole engine exists to stop the model asserting things it
            # cannot back; here the prompt was ORDERING it to. So the order is
            # removed rather than guarded, and replaced with what is true and
            # checkable, plus an explicit prohibition. R33-S1 is the code
            # control behind this request, because a prompt rule is a request.
            "On privacy: you may say that messages are handled privately for "
            "this clinic only and that the patient can ask to stop messages at "
            "any time. NEVER claim compliance with, or certification under, any "
            "law, standard, regulation or framework, named or unnamed. You cannot "
            "verify it and it is not yours to promise. For "
            "any question about policy, consent, data handling or legal "
            "obligations, say plainly that the clinic answers that directly and "
            "offer to pass the question on. "
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
    # v16.4 FIX R10-M1: ecommerce sat before saas, and its keyword list holds
    # the very generic "product" and "order" — so "our software product" was
    # claimed by PULSE before APEX was ever consulted. saas keywords
    # (software, saas, platform, api, dashboard) are far more specific, so it
    # goes first. restaurant still precedes both, keeping "food delivery app"
    # on NOVA where it belongs.
    order = ("healthcare", "legal", "education", "restaurant", "saas", "ecommerce")
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
    # v16.1 GEN-6 FIX R7-H1: business_desc was read ONLY to pick a template
    # and then thrown away — the one piece of clinic-specific text collected
    # at onboarding never reached the model. With nothing to ground on, a
    # question like "what is your address?" has no honest answer available,
    # and the model fills the gap itself (see R7-C1). Carry it through.
    desc = (business_desc or "").strip()
    if desc:
        prompt += ("\n\nWhat the owner told us about this business — treat "
                   "these as the ONLY authoritative facts you hold: " + desc)
    return template["bot_name"], prompt


# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# 👑  GOD-LOGIC v10  (god_logic_v9 merged in — every v9 drawback addressed)
#     Drawback fixes vs v9 module:
#       1. Cache lost on restart      → brain_cache (Redis when REDIS_URL set)
#       2. Only ta/hi/en              → 16-script detect, 10-language canned,
#                                       AI itself replies in ANY language
#       3. Keyword-only emergencies   → hybrid: keywords (instant, free) + AI
#                                       escalation token (understands meaning,
#                                       works in every language)
#       4. Voice = Gemini only        → Gemini → OpenAI Whisper fallback chain
#       5. "Mostly routing"           → Qdrant RAG long-term memory per user
#       6. No vector memory           → see #5 (AES-256-encrypted payloads)
# ─────────────────────────────────────────────────────────────────────────────

# ⟦PURE-LOGIC-BEGIN⟧  (no I/O — unit-testable in isolation)

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
    "booking_limit": {
        "en": ("You already have {n} upcoming appointments on this number. "
               "Reply 'my appointment' to see or change them, or call the "
               "clinic if you need another one."),
        "ta": ("\u0b87\u0ba8\u0bcd\u0ba4 \u0ba8\u0bae\u0bcd\u0baa\u0bb0\u0bbf\u0bb2\u0bcd \u0b8f\u0bb1\u0bcd\u0b95\u0ba9\u0bb5\u0bc7 {n} \u0b85\u0baa\u0bcd\u0baa\u0bbe\u0baf\u0bcd\u0ba3\u0bcd\u0b9f\u0bcd\u0bae\u0bc6\u0ba9\u0bcd\u0b9f\u0bcd "
               "\u0b89\u0bb3\u0bcd\u0bb3\u0ba9. \u0b85\u0bb5\u0bb1\u0bcd\u0bb1\u0bc8\u0baa\u0bcd \u0baa\u0bbe\u0bb0\u0bcd\u0b95\u0bcd\u0b95 \u0b85\u0bb2\u0bcd\u0bb2\u0ba4\u0bc1 \u0bae\u0bbe\u0bb1\u0bcd\u0bb1 'my appointment' \u0b8e\u0ba9 "
               "\u0b85\u0ba9\u0bc1\u0baa\u0bcd\u0baa\u0bb5\u0bc1\u0bae\u0bcd. \u0bae\u0bc7\u0bb2\u0bc1\u0bae\u0bcd \u0ba4\u0bc7\u0bb5\u0bc8\u0baf\u0bc6\u0ba9\u0bbf\u0ba9\u0bcd clinic-\u0b90 \u0ba4\u0bca\u0b9f\u0bb0\u0bcd\u0baa\u0bc1 \u0b95\u0bca\u0bb3\u0bcd\u0bb3\u0bb5\u0bc1\u0bae\u0bcd."),
        "hi": ("\u0907\u0938 \u0928\u0902\u092c\u0930 \u092a\u0930 \u092a\u0939\u0932\u0947 \u0938\u0947 {n} \u0905\u092a\u0949\u0907\u0902\u091f\u092e\u0947\u0902\u091f \u0939\u0948\u0902\u0964 "
               "\u0926\u0947\u0916\u0928\u0947 \u092f\u093e \u092c\u0926\u0932\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f 'my appointment' \u092d\u0947\u091c\u0947\u0902\u0964"),
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


# ── v16.3 · FIX R9-C1 (INGRESS HARDENING) ────────────────────────────────────
# Context, because this one is easy to get wrong in a way that looks right.
# A red-team message ("John'; DROP TABLE patients;--") appeared to take the
# engine down, and the obvious reading is SQL injection. It is not: every
# query here is parameterised, and the payload was replayed against this build
# — 200 OK, all 12 tables intact, the string stored as literal text. Stripping
# quotes and semicolons would therefore buy no safety at all while corrupting
# every legitimate O'Brien, D'Souza and Naik-Patil that ever books a slot.
#
# What DOES need removing is the class of bytes that breaks storage and logs
# rather than SQL:
#   • NUL (0x00) — psycopg2 refuses to adapt a string containing it, so the
#     insert raises before it ever reaches Postgres. SQLite accepts it happily,
#     which is exactly why local testing cannot see this. Same shape as the
#     HF1 bug that only surfaced on the live database.
#   • other C0/C1 control characters — corrupt JSON log lines and terminal
#     output, and serve no purpose in a patient message.
#   • bidi/zero-width overrides (U+202A-E, U+2066-9, U+200B-F) — invisible
#     characters that let a message render one way to a human reviewer and
#     another way to the model.
# Newlines and tabs stay: patients format addresses with them.
_CTRL_CHARS_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u200b-\u200f\u202a-\u202e\u2066-\u2069]")


def scrub_inbound(text: Any) -> str:
    """Make inbound text safe to STORE and LOG. Not a SQL defence — that is
    what parameterised queries are for, and they already work."""
    if not text:
        return ""
    out = _CTRL_CHARS_RE.sub("", str(text))
    # NFC keeps Indic matras composed (see v15g4 FIX A1) and collapses the
    # look-alike codepoints used to smuggle homoglyph clinic names.
    return unicodedata.normalize("NFC", out).strip()


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


# Intent keywords — fast free layer for en/ta/hi (the launch markets).
# Every OTHER language is covered by the AI escalation token further below.
# v15g4 FIX A2: emergency detection is now VERTICAL-AWARE.
#
# UNIVERSAL = unambiguous life-threats — these fire for EVERY business type.
# BROAD_EXTRA = pain/blood vocabulary that is a real emergency signal at a
# restaurant or a real-estate office, but is ROUTINE COMPLAINT LANGUAGE at a
# clinic: "gum bleeding while brushing", "severe tooth pain", "ரொம்ப வலி",
# "cleaning cost is unbearable" all hijacked normal dental messages into the
# emergency script + a 🚨 owner alert (proven in the round-4 audit). For
# healthcare, those words go to the AI, which understands context — genuine
# nuanced emergencies are still caught by the AI escalation token in every
# language (the same documented pattern that already removed lone "urgent").
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
    # ── v16.9 FIX R15-C4 (PATIENT SAFETY) ────────────────────────────────
    # Found while verifying R15-C1: with the AI down, "vaayil ratham nikkave
    # illa, mayakkam varudhu" produced NOTHING from the deterministic layer.
    # Bare "bleeding" and "mayakkam" live in BROAD_EXTRA and are deliberately
    # excluded for healthcare (v16g2 M15 — "konjam mayakkam-a irukku" is
    # routine clinic talk), and that call is right. The gap is that no
    # COMPOUND form was covered, and a compound is unambiguous: nobody says
    # "bleeding won't stop" about something routine. These are the dental
    # presentations that are genuinely time-critical — uncontrolled bleeding,
    # and airway compromise from facial swelling (Ludwig's angina).
    # v17.0 FIX R16-C3a: "not responding" was here and matched "doctor is not
    # responding to my calls" — the single most common complaint a clinic gets
    # — paging the owner and muting the bot for 15 minutes. "unconscious" and
    # "unresponsive" carry the real meaning without the collision.
    "bleeding won't stop", "bleeding wont stop", "bleeding will not stop",
    "bleeding is not stopping", "bleeding not stopping", "non stop bleeding",
    "continuous bleeding", "heavy bleeding", "blood won't stop",
    "blood wont stop", "unconscious", "unresponsive",
    "can't swallow", "cant swallow", "cannot swallow", "trouble swallowing",
    # v17.0 FIX R16-C3b: plain facial swelling is the most common post-
    # extraction message a dental clinic receives and is usually expected
    # recovery — every one of those was becoming an emergency plus a 15-minute
    # mute. Airway compromise is the actual emergency, so only the swallowing
    # and throat/tongue forms remain.
    # v17.0 R17-C4. Two lessons. (a) "swollen and can't breathe" was a DEAD
    # entry — the real sentence "my face is swollen and I can't breathe" has
    # words in between, so it could never be the reason anything fired.
    # (b) Every entry needs its morphological twin: "throat swelling" fired
    # while "swollen throat" did not. Airway compromise is the emergency, so
    # both word orders are listed, and facial swelling counts only when
    # breathing or swallowing trouble is mentioned too.
    "difficulty swallowing", "throat swelling", "swollen throat",
    "tongue swelling", "swollen tongue", "tongue is swollen",
    "neck swelling", "swollen neck", "swelling under jaw",
    "face fully swollen", "whole face swollen",
    "hard to breathe", "breathing difficult", "difficulty breathing",
    "breathless", "cannot talk", "can't talk",
    # romanised Tamil
    "ratham nikkala", "ratham nikkave illa", "ratham niykkave illa",
    "ratham nikkuthu illa", "ratham niruthala", "rathum nikkala",
    "vizhungave mudiyala", "vizhunga mudiyala",
    # R17-C4b: R16-C3b removed the Tamil facial-swelling terms and put nothing
    # back, so Tamil coverage of this presentation fell to zero. Restored in
    # the qualified form only — swelling WITH breathing or swallowing trouble.
    "veengi moochu", "moochu vaangala", "moochu vaanga kastam",
    "mugam veengi", "kazhuthu veengi",
    "mayakkam varudhu ratham", "nikkave illa ratham",
    "ரத்தம் நிற்கல்",
    # Tamil script. Colloquial spelling drops or keeps the final pulli
    # freely, and patients type both — so both are covered (R15-C4b).
    "ரத்தம் நிக்கல்",
    "ரத்தம் நிற்கல", "ரத்தம் நிற்கவில்லை", "ரத்தம் நிக்கல",
    "ரத்தம் நிற்கவே இல்லை", "விழுங்க முடியல",
    # R17-C4c: Tamil airway-compromise forms, absent since R16-C3b.
    "மூச்சு வாங்க", "முகம் வீங்கி மூச்சு", "கழுத்து வீங்கி", "நாக்கு வீங்கி",
    # Hindi
    "खून नहीं रुक", "खून बंद नहीं", "निगल नहीं",
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
# ── v18.0 · FIX R18-C2 (PATIENT SAFETY — coverage parity) ────────────────────
# Measured gaps on R17, every one reproduced by execution before being added:
#
#  1. AIRWAY, Tamil. "மூச்சு விட முடியல" / "முடியவில்லை" — the most literal
#     Tamil for "can't breathe" — was absent in BOTH scripts and in roman.
#     English carried "can't breathe" AND "cannot breathe"; Tamil carried only
#     "மூச்சு வாங்க" (panting) and "மூச்சு முட்ட". R18-C1 fixes the inflection
#     problem; it cannot invent a stem that was never listed.
#  2. CARDIAC, Tamil + Hindi. "chest pain" fired in English and had no
#     equivalent in either other language. In a dental chair, chest pain is a
#     cardiac event until proven otherwise.
#  3. ANAPHYLAXIS. Nothing in any language. Local anaesthetic and post-op
#     antibiotics are the two commonest triggers in a dental clinic.
#     DELIBERATELY NOT ADDED: bare "allergic reaction" and bare "allergic".
#     "I'm allergic to penicillin, is that ok?" is a routine pre-op
#     DISCLOSURE, and firing on it would page the doctor and mute the bot for
#     15 minutes — the exact harm R16-C3 was raised to remove. Only forms
#     carrying acuity or a severity marker are listed.
#  4. BLEEDING, word order. "heavy bleeding" was listed, "bleeding heavily"
#     was not — the same one-directional listing R17-C5a fixed for BP terms
#     and left everywhere else. Ditto "niruthave illa", where the twin form
#     "nikkave illa" HAD been added.
_EMERGENCY_KW_R18 = [
    # 1 — airway, Tamil script + roman
    "மூச்சு விட முடிய", "மூச்சு விடமுடிய", "மூச்சு திணற", "மூச்சு கஷ்ட",
    # Latin keeps EXACT token matching by design (see R18-C1), so romanized
    # Tamil cannot rely on the prefix rule — its surface forms are listed.
    "moochu vida mudiyala", "moochu vida mudiyalai", "moochu vida mudiyale",
    "mucchu vida mudiyala", "moochu vidamudiyala", "moochu thinaral",
    "moochu thinarudhu", "mucchu thinaral",
    # 2 — cardiac, Tamil + Hindi
    "நெஞ்சு வலி", "நெஞ்சு வலிக்க", "மார்பு வலி", "seene mein dard",
    "nenju vali", "सीने में दर्द",
    # 3 — anaphylaxis (acuity-bearing forms only — see note above)
    "anaphylaxis", "anaphylactic", "severe allergic", "severe allergy",
    "throat closing",
    "throat is closing", "lips swelling", "wheezing badly",
    "ஒவ்வாமை ரொம்ப", "गंभीर एलर्जी",
    # 4 — bleeding, the missing word orders
    "bleeding heavily", "bleeding a lot", "blood is not stopping",
    "blood not stopping", "ratham niruthave illa", "niruthave illa ratham",
    "ரத்தம் நிறுத்தவே இல்லை",
]
_EMERGENCY_KW_UNIVERSAL = _EMERGENCY_KW_UNIVERSAL + _EMERGENCY_KW_R18

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
# ── v25.0 · FIX R25-C1 (PATIENT SAFETY — human handoff, romanised Tamil) ─────
# MEASURED on R24, driven through govern_message with healthcare=True, one
# A.uid() per case (never a slice of the message — R21's harness trap):
#
#     register            reached a human
#     English                 10/10
#     Tamil script             5/5
#     Hindi                    4/4
#     romanised Tamil          0/15
#
# _HUMAN_KW was the ONLY patient-inbound trigger list in the engine with ZERO
# Thanglish entries. Every other one carries it: _EMERGENCY_KW 68, _BOOK_WORDS
# 11, _OPT_OUT_KEYWORDS 10, _RESCHED_WORDS 9, _CANCEL_WORDS 4, _VIP_KW 2.
# The Tamil-script entry above is literally "டாக்டர் கிட்ட பேசணும்" — the same
# sentence, in the other script. The twin was written and the romanisation was
# forgotten: the R18/R21/R22/R23/R24 asymmetry, in a sixth list.
#
# Rule 2 — isolated before believing it. The matcher is fine:
#     _kw_hit(_norm_text("doctor kitta pesanum"), "kitta pesanum") -> True
# The keyword simply was not in the list. The list, not the matcher.
#
# What the patient experiences on R24: "doctor kitta pesanum" produces
# alerts=0, muted=False, reply=None. No 🙋 TAKE OVER alert to the owner, no
# ghost-mute, no canned handoff line. The patient keeps talking to a bot and
# the clinic is never told anyone asked for a person. It fails CLOSED, so
# nothing logs and no detector fires — invisible to Rule 6.
#
# It matters most where it is least visible: govern_message is the PRE-AI
# gate, so when Gemini is down — the live condition on this deployment, where
# the free-tier cap 503s the demo — this list is the ONLY route to a human.
# The measurement above ran with zero AI providers configured, and English,
# Tamil and Hindi patients still reached one. Thanglish patients did not.
#
# SHAPE OF EVERY ENTRY: a human TARGET plus a SPEAK verb, never a bare verb.
# "pesanum" alone would fire on "naan tamil la pesanum" (I want to speak IN
# TAMIL) and page a doctor for a language preference. The discriminating token
# is the connector "kitta/kitte/kooda" (to/with a PERSON), which is not
# grammatical without a person on its left. Latin is EXACT by design (R18-C1),
# so every romanised variant is spelled out; there is no stemming to fall
# back on, and A.dead_indic_stems does not apply to a Latin list.
#
# MEASURED AFTER: tg 15/15, one proving sentence PER ENTRY (Rule 9 — zero dead
# entries), and 0 false fires across 37 controls built as the harm shape:
# ordinary clinic Thanglish that mentions doctor / pesa / kitta ("doctor kitta
# appointment venum", "english la pesa mudiyuma", "bus stand kitta clinic
# irukka" — for a PLACE, kitta means "near"), the R23/R24 booking intents, and
# four spellings of refusal.
#
# DELIBERATELY NOT ADDED:
#  - bare "kitta pesa". It covers "kitta pesa mudiyuma" for free, and it was
#    measured firing on "enakku doctor kitta pesa venam" (I do NOT want to
#    speak to the doctor) — because _NEGATORS_POST carries "vendam"/"venda"
#    and not the "venam" spelling. Spelling out the positive modal instead
#    removes the dependency on a negator list this round is not touching.
#    The _NEGATORS_POST gap is real and is reported, not patched.
#  - bare "pesanum" / "pesa" / "kitta" / "manushan". Each is ordinary Tamil.
#  - bare "doctor". Half of all clinic traffic names the doctor.
_HUMAN_KW_R25 = (
    # connector + speak-verb — needs a person noun on its left to be
    # grammatical at all, which is what keeps it off language-preference
    # sentences, where there is no connector.
    "kitta pesanum", "kitte pesanum", "kita pesanum", "kitta pesanam",
    "kitta pesa mudiyuma", "kitte pesa mudiyuma", "kitta pesa mudiyum",
    "kooda pesanum", "kuda pesanum", "kitta konjam pesanum",
    "kitta pesa vendum", "kitta line kudunga",
    "kitta connect pannunga", "kitta connect panunga",
    # explicit human target + connector (the verb is implied by the noun)
    "manushan kitta", "manusha kitta", "manidhan kitta", "aal kitta",
    "aalu kitta", "yaaravathu kitta", "yaarayavathu kitta", "yaarachum kitta",
    "staff kitta", "reception kitta",
    # "speak to me directly" idioms — no connector, so listed in full
    "direct a pesanum", "directa pesanum", "neradiya pesanum",
    "nerdiya pesanum",
    # "put the doctor on / call the doctor". _norm_text turns the hyphen in
    # "doctor-a" into a space, hence the two-token forms.
    "doctor a kupdunga", "doctor kupdunga", "doctor a koopidunga",
)
_HUMAN_KW = _HUMAN_KW + list(_HUMAN_KW_R25)
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


# ── v18.0 · FIX R18-C1 (PATIENT SAFETY — agglutinative languages) ────────────
# _kw_hit compared WHOLE TOKENS for exact equality. That is right for English
# and wrong for Tamil and Hindi, which glue their suffixes straight onto the
# stem. Measured on R17: "மூச்சு வாங்குது" did NOT match the keyword
# "மூச்சு வாங்க" that was sitting in the emergency list, and "ரத்தம் நிக்கலை"
# did not match "ரத்தம் நிக்கல்" — while the uninflected dictionary forms both
# fired. Every Tamil emergency term in the list therefore only worked for the
# one spelling somebody happened to type into the constant, and the launch
# market writes Tamil.
#
# The fix is scoped as narrowly as it can be and still be useful:
#   • Latin script keeps EXACT equality. English is not agglutinative, and
#     prefix matching there would make "can" match "cannot" — the negation
#     inversion this matcher exists to prevent.
#   • An Indic keyword token may match a text token that STARTS WITH it, but
#     only when the stem is >= _AGGLU_MIN_STEM codepoints and the text token
#     grows it by at most _AGGLU_MAX_SUFFIX. Both bounds matter: the first
#     stops short words ("வலி", pain) matching unrelated longer ones
#     ("வலிமை", strength); the second stops a stem matching an arbitrarily
#     long compound.
#   • Negation handling is untouched — it runs on the matched span exactly as
#     before, so a negated Tamil hit is still skipped.
_AGGLU_MIN_STEM   = 4     # codepoints, excluding combining marks
_AGGLU_MAX_SUFFIX = 8     # how far a suffix may extend the stem
# R18-C1b: 5 was measured too tight — Tamil negative-verb endings alone run
# to 6-7 codepoints (முடிய -> முடியவில்லை). Raised to 8 and re-verified
# against the full silence suite, which stayed at zero false pages.


def _is_indic_tok(t: str) -> bool:
    return any("\u0900" <= c <= "\u0d7f" for c in t)


def _toks_match(text_toks, kw_toks) -> bool:
    """True when this window of text tokens satisfies the keyword tokens.
    Latin: exact. Indic: exact, or a bounded agglutinative prefix."""
    if tuple(text_toks) == kw_toks:
        return True
    if len(text_toks) != len(kw_toks):
        return False
    for tt, kt in zip(text_toks, kw_toks):
        if tt == kt:
            continue
        if not (_is_indic_tok(kt) and _is_indic_tok(tt)):
            return False
        if len(kt) < _AGGLU_MIN_STEM:
            return False
        if not tt.startswith(kt):
            return False
        if len(tt) - len(kt) > _AGGLU_MAX_SUFFIX:
            return False
    return True


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
        if _toks_match(toks[i:i + n], kw_toks):   # v18 R18-C1
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


# v33.0 · FIX R33-C2 — asking ABOUT emergencies is not an emergency.
# Measured on v32: "do you handle emergency cases?", "what is your emergency
# number?", "is there an emergency contact after 9pm" and "neenga emergency
# case paapingala?" ALL paged the doctor. Every one is an ordinary question a
# patient asks BEFORE booking. Same class as R16-C3, where "not responding"
# matched "doctor is not responding to my calls" — fixed once, back under a
# different word.
#
# Why this matters more than it looks: owner alerts already die silently after
# 24h without an approved Meta template (error 131047). A doctor paged for
# "do you handle emergencies?" learns to ignore the alerts, and then the real
# chest-pain page is ignored too. Alert fatigue is how an emergency layer dies.
#
# THE SCOPE IS ONE WORD. The census showed every genuine phrase fires on its
# OWN entry — "chest pain", "bleeding wont stop", "மூச்சு வாங்க". Only the bare
# category noun "emergency" was doing meta duty. So suppression is allowed ONLY
# when every emergency hit is a bare category noun; if any symptom term hit,
# nothing is suppressed and the guard is structurally incapable of silencing a
# real emergency. That is a proof, not a measurement.
_EMERGENCY_GENERIC = frozenset({
    "emergency", "emergencies", "emergency case", "emergency cases",
    "\u0b85\u0bb5\u0b9a\u0bb0\u0bae\u0bcd", "\u0b85\u0bb5\u0b9a\u0bb0",
    "\u0906\u092a\u093e\u0924\u0915\u093e\u0932", "\u0907\u092e\u0930\u091c\u0947\u0902\u0938\u0940",
})
# Asking about the SERVICE: interrogative + second person + no first-person
# distress. All three required, because the cost of a wrong suppression is a
# patient in trouble being ignored and the cost of a wrong page is one buzz.
_META_QUESTION  = ("do you", "does your", "do u", "is there", "are there",
                   "what is your", "whats your", "what's your", "how do i",
                   "can i get", "you have any", "neenga", "ungaluku",
                   "ungalukku", "irukka", "paapingala", "pakuringala",
                   "kya aap", "\u0915\u094d\u092f\u093e \u0906\u092a", "\u0928\u0940\u0902\u0917",
                   "\u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd", "\u0b87\u0bb0\u0bc1\u0b95\u0bcd\u0b95\u0bbe")
_SELF_DISTRESS  = ("i have", "i am", "im ", "i'm ", "my ", "me ", "help",
                   "urgent", "now", "please", "enaku", "enakku", "\u0b8e\u0ba9\u0b95\u0bcd\u0b95\u0bc1",
                   "\u0b8e\u0ba9\u0bcd", "mujhe", "\u092e\u0941\u091d\u0947", "\u092e\u0947\u0930\u0947", "mera", "meri")


def _emergency_hit(norm: str, ekw) -> bool:
    """True if this is a real emergency. See R33-C2 above for the scope proof."""
    hits = [k for k in ekw if _kw_hit(norm, k, pre_w=1)]
    if not hits:
        return False
    if any(h.lower() not in _EMERGENCY_GENERIC for h in hits):
        return True                      # a symptom fired — never suppress
    if any(d in norm for d in _SELF_DISTRESS):
        return True                      # first-person distress wins
    if any(q in norm for q in _META_QUESTION):
        return False                     # asking about the service
    return True                          # ambiguous -> fire. Fail LOUD.


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
        "emergency": _emergency_hit(norm, ekw),   # v33 R33-C2
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


# ── 🎙️ Voice-note decoder — Gemini (multimodal) → OpenAI Whisper fallback.
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


# ── 🧬 RAG LONG-TERM MEMORY — Qdrant + Gemini embeddings (v9 drawbacks #5,#6)
#    Per end-user memory across sessions. Payload text is AES-256-GCM encrypted
#    so the vector DB never stores readable PII (DPDP-friendly).
_qdrant_client: Any = None
_rag_ready: bool    = False


def init_rag() -> None:
    global _qdrant_client, _rag_ready
    if not QDRANT_AVAILABLE:
        log.warning("⚠️  qdrant-client not installed — RAG memory OFF.")
        return
    if not cfg.QDRANT_URL:
        log.warning("⚠️  QDRANT_URL not set — RAG memory OFF.")
        return
    if not AI_PROVIDERS_ACTIVE.get("gemini"):
        log.warning("⚠️  Gemini key required for embeddings — RAG memory OFF.")
        return
    try:
        client = QdrantClient(url=cfg.QDRANT_URL,
                              api_key=cfg.QDRANT_API_KEY or None, timeout=10)
        try:
            client.get_collection(cfg.QDRANT_COLLECTION)
        except Exception:
            try:
                client.create_collection(
                    collection_name=cfg.QDRANT_COLLECTION,
                    vectors_config=qmodels.VectorParams(
                        size=cfg.EMBED_DIMS, distance=qmodels.Distance.COSINE))
                log.info(f"🧬 Qdrant collection created: {cfg.QDRANT_COLLECTION}")
            except Exception as _ce:
                # v16g2 FIX M13: two workers boot, both miss get_collection,
                # the loser's "already exists" used to bubble to the OUTER
                # except — that worker then logged "Qdrant unreachable" and ran
                # MEMORY-FREE for its whole lifetime. Tolerate the boot race.
                if "exist" in str(_ce).lower():
                    log.info("🧬 Qdrant collection already exists (boot race) — OK.")
                else:
                    raise
        _qdrant_client = client
        _rag_ready     = True
        log.info("🧬 RAG long-term memory ONLINE (Qdrant).")
    except Exception as exc:
        log.warning(f"⚠️  Qdrant unreachable ({exc}) — RAG memory OFF, engine OK.")


def _embed(text: str, is_query: bool = False) -> List[float]:
    task = "retrieval_query" if is_query else "retrieval_document"
    try:
        res = genai.embed_content(model=cfg.EMBED_MODEL, content=text[:2000],
                                  task_type=task,
                                  output_dimensionality=cfg.EMBED_DIMS)
    except TypeError:   # older SDK without output_dimensionality
        res = genai.embed_content(model=cfg.EMBED_MODEL, content=text[:2000],
                                  task_type=task)
    vec = list(res["embedding"])
    # v14g5 FIX 18: PAD (not just truncate) so a short embedding can't produce a
    # wrong-size vector that silently fails the Qdrant upsert / corrupts search.
    if len(vec) < cfg.EMBED_DIMS:
        vec = vec + [0.0] * (cfg.EMBED_DIMS - len(vec))
    return vec[:cfg.EMBED_DIMS]


# v12 #1: replies we must NEVER write into long-term memory (they'd poison it).
_FALLBACK_MARKERS = (
    "temporarily unavailable", "couldn't hear that", "could you please type",
    "try again", "something went wrong",
)


def _is_low_quality_reply(reply: str) -> bool:
    if not reply or len(reply.strip()) < 2:
        return True
    low = reply.lower()
    return any(m in low for m in _FALLBACK_MARKERS)


def rag_store(customer_id: str, uid: str, user_text: str, reply: str) -> None:
    """Fire-and-forget — memory writes never slow down or break a reply.
    v12 #1: refuses to memorise a fallback/error reply, so a transient AI
    outage can't poison this user's long-term memory with apology text."""
    if not _rag_ready or len(user_text.split()) < 4:
        return
    if _is_low_quality_reply(reply):
        analytics.inc("rag.store.skipped_lowquality")
        return

    def _w():
        def _impl():
            vec = _embed(user_text, is_query=False)
            enc = pii_vault.encrypt(
                f"User said: {user_text[:500]} | Assistant replied: {reply[:300]}")
            _qdrant_client.upsert(
                collection_name=cfg.QDRANT_COLLECTION,
                points=[qmodels.PointStruct(
                    id=str(uuid.uuid4()), vector=vec,
                    payload={"customer_id": customer_id, "uid": uid,
                             "enc": enc, "ts": _now()})])
        try:
            # v12 #9/#23: bounded by the Qdrant breaker + hard timeout so a hung
            # embedder or vector DB degrades the write silently instead of
            # pinning a worker thread.
            _qdrant_breaker.call(_call_with_timeout, _impl, cfg.RAG_TIMEOUT_SECS)
            analytics.inc("rag.stored")
        except Exception as exc:
            log.warning(f"⚠️  RAG store degraded: {exc}")

    submit_bg(_w)   # v11 #11: bounded pool instead of a raw daemon thread


def _rag_retrieve_impl(customer_id: str, uid: str, query: str) -> str:
    vec = _embed(query, is_query=True)
    flt = qmodels.Filter(must=[
        qmodels.FieldCondition(key="customer_id",
                               match=qmodels.MatchValue(value=customer_id)),
        qmodels.FieldCondition(key="uid",
                               match=qmodels.MatchValue(value=uid)),
    ])
    hits = _qdrant_client.search(
        collection_name=cfg.QDRANT_COLLECTION, query_vector=vec,
        query_filter=flt, limit=cfg.RAG_TOP_K,
        score_threshold=cfg.RAG_MIN_SCORE)
    lines = []
    for h in hits:
        dec = pii_vault.decrypt((h.payload or {}).get("enc", ""))
        if dec and dec != "[ENCRYPTED]":
            lines.append("- " + dec)
    return "\n".join(lines)


def rag_retrieve(customer_id: str, uid: str, query: str) -> str:
    """Returns a memory block ('' if none). Failures degrade silently.
    v12 #9/#23: embedding + vector search run inside the Qdrant breaker with a
    hard timeout — if the vector DB hangs, the reply still ships memory-free."""
    if not _rag_ready or len(query.split()) < 3:
        return ""
    try:
        result = _qdrant_breaker.call(
            _call_with_timeout, _rag_retrieve_impl, cfg.RAG_TIMEOUT_SECS,
            customer_id, uid, query)
        if result:
            analytics.inc("rag.hit")
        return result or ""
    except Exception as exc:
        log.warning(f"⚠️  RAG retrieve degraded: {exc}")
        return ""


def rag_forget(customer_id: str, uid: str) -> bool:
    """v14g4 (DPDP): delete every RAG memory point for ONE data subject (uid =
    'customer_id:phone'). Best-effort; never raises. Returns True if the delete
    call succeeded. Vectors store only AES-256-GCM-encrypted text, but erasure
    means erasure — so we remove the points entirely."""
    if not _rag_ready:
        return False
    try:
        flt = qmodels.Filter(must=[
            qmodels.FieldCondition(key="customer_id",
                                   match=qmodels.MatchValue(value=customer_id)),
            qmodels.FieldCondition(key="uid", match=qmodels.MatchValue(value=uid)),
        ])
        _qdrant_breaker.call(
            _call_with_timeout,
            lambda: _qdrant_client.delete(
                collection_name=cfg.QDRANT_COLLECTION,
                points_selector=qmodels.FilterSelector(filter=flt)),
            cfg.RAG_TIMEOUT_SECS)
        analytics.inc("rag.forgotten")
        return True
    except Exception as exc:
        log.warning(f"⚠️  rag_forget failed: {exc}")
        return False


# ── 🚨 AI ESCALATION TOKEN — the "AI understanding" layer (every language).
# v11 fix #8: the token is randomised per process boot, so a user can NEVER
# induce a false escalation by typing it — they can't know it. The AI receives
# it in the (hidden) system prompt and emits it only on a genuine escalation.
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
# v16.2 FIX R8-L1: asked "what company built this AI", the assistant honestly
# said it did not know — because nothing in the prompt ever told it. HEONIX
# appears 29 times in this file and not once in anything the model receives.
# Two reasons that matters: a prospect testing the demo has no way to learn
# who to call, and the underlying model is Gemini, so an unanswered identity
# question invites "I am built by Google" — which is worse than silence in
# front of a doctor. Configurable, because a clinic may prefer white-label.
VENDOR_NAME = os.getenv("VENDOR_NAME", "HEONIX AI").strip()
_VENDOR_RULE = (
    ("\n\nWHO BUILT YOU: if\u2014and only if\u2014the user asks who made, built, "
     "powers or is behind this assistant, say briefly that the assistant is "
     "built by " + VENDOR_NAME + ", then return to helping with the business. "
     "Never say you were built by Google, OpenAI, Anthropic or any AI vendor, "
     "and never name the underlying model. Never raise this unprompted.")
    if VENDOR_NAME else "")

# ── v16.4 · FIX R10-C2 (CRITICAL, CROSS-VERTICAL) ───────────────────────────
# Measured 26-Jul: the healthcare prompt is 793 chars and carries "never
# invent the clinic name, address, doctor name, fees or timings" plus the
# diagnosis/prescription refusal. The default (ELITE) prompt is 258 chars and
# carries NEITHER — and NOVA, PULSE, SAGE, APEX and LEX are no better. So the
# exact defect class that produced "Smile Care Dental at RS Puram" was fixed
# for clinics only, while every other vertical shipped wide open.
#
# Rather than paste the rule into seven templates and let them drift apart,
# it becomes universal — one rule, appended to every prompt, phrased in
# business-neutral language. The healthcare template keeps its own stricter
# medical wording on top; this is the floor, not the ceiling.
_INTEGRITY_RULE = (
    "\n\nFACTUAL INTEGRITY: the ONLY facts you have about this business are "
    "the ones stated in this prompt. Never invent or guess a business name, "
    "address, branch, phone number, price, package, staff or owner name, "
    "qualification, timing, or availability. If you are asked for something "
    "not stated above, say plainly that you don't have that detail confirmed "
    "and offer to have the business confirm it. A wrong detail sends a "
    "customer to the wrong place \u2014 saying 'I'll check' is always better.")

_LANGUAGE_RULE = ("\n\nLANGUAGE: Always reply in the same language and script "
                  "the user used, no matter which language it is.")
# v16.1 GEN-6 FIX R7-M1b: asked about news / world events, the model invented
# answers (it has no internet). Fabricated current affairs from a clinic
# assistant is the same defect class as R7-C1 — confident fiction. Scope it.
_SCOPE_RULE = ("\n\nSCOPE: You have NO internet access and NO knowledge of "
               "current news, events, prices, or the outside world beyond what "
               "this prompt states. If asked about such things, say briefly, in "
               "the user's own language, that you can only help with this "
               "business's services and bookings, then steer back. Never "
               "fabricate news, scores, or world facts. (The current date/time "
               "given below IS known to you — answer those directly.)")


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

def _mentions_current_time(reply: str) -> bool:
    """v16.1 GEN-6 FIX R7-M2: with minute-exact time back in the prompt, a
    cached reply that STATES the current clock time would go stale inside its
    half-hour cache bucket — the exact regression v16g3 R3-L6 fixed by
    rounding. Instead of rounding (observed live 22-Jul: '12:30 AM' shown at
    12:50, reading as simply wrong), keep the time exact and refuse to CACHE
    any reply that contains the current minute. Static times in replies
    (working hours like '9:00 AM') still cache; only now-o'clock answers
    stay fresh."""
    hm = _now_ist().strftime("%I:%M")
    return bool(reply) and (hm in reply or hm.lstrip("0") in reply)


def _time_context() -> str:
    n = _now_ist()
    # v16g3 FIX R3-L6 rounded this to the half-hour cache bucket; superseded
    # by R7-M2 above — exact minute here, cache-side guard over there.
    return ("\n\n[REAL-TIME — India / IST] It is currently exactly "
            + n.strftime("%A, %d %B %Y, %I:%M %p")
            + ". You DO know the current date, day and time — it is stated right "
              "here. If the user asks the time, date, or day, answer directly "
              "from this line; never claim you lack real-time access. Use it to "
              "decide whether the business is open or closed right now (compare "
              "against the working hours stated above). Never guess, assume, or "
              "invent the time.")   # v16.1 GEN-6 FIX R7-M1a

def _cache_hour_seed(base: str) -> str:
    # Bucket the response cache by IST time so time-sensitive answers
    # (e.g. "are you open now?") cannot be served stale within the cache TTL.
    # v15g4 FIX B8: hour buckets let a 9:05 "we're closed, we open at 9:30"
    # answer be served at 9:55. HALF-hour buckets align with the :00/:30
    # boundaries clinics actually open and close on, so open/closed answers
    # flip exactly when the clinic does.
    n = _now_ist()
    return base + "\n#h=" + n.strftime("%Y%m%d%H") + ("0" if n.minute < 30 else "1")


# ── v16.1 GEN-6 · FIX R7-C1 (LAUNCH-CRITICAL) ────────────────────────────────
# Observed live on 21-Jul-2026: the greeting correctly said "Vakkai Care Dental"
# (interpolated from customer_name) and the very next reply said "Smile Care
# Dental is located at RS Puram, Coimbatore" — a clinic name AND an address that
# appear nowhere in this codebase or in the brain. The healthcare template
# already carries an explicit rule ("this is the ONLY clinic name you may ever
# use", "Never invent, guess, or make up any clinic name, address, location,
# doctor name, fees, or timings") and gemini-3.1-flash-lite ignored it.
#
# A prompt rule is a request, not a control. So the check moves into code: if
# the model names a business whose distinctive word is not this clinic's, the
# turn is refused instead of sent. The failure this exists to prevent is a
# patient walking to another clinic's address.
# v16.4 FIX R10-C3b: every word in _BIZ_TAIL below MUST also appear here.
# A tail word is a business-TYPE word, never a brand word — but the guard
# only knew the healthcare ones, so when "Physiotherapy" was added to the
# tail list it was still being scored as distinctive. Result: own="Haroon
# Physiotherapy" vs impostor="Prime Rehab Physiotherapy" shared the token
# {physiotherapy}, the sets intersected, and the impostor passed. Caught by
# the cross-vertical guard matrix on 26-Jul. Keep the two lists in sync.
_GENERIC_BIZ_WORDS = {
    # healthcare
    "dental", "dentistry", "clinic", "clinics", "hospital", "hospitals",
    # v19.0 R19-P1: R18-C4b added Dentist / Dentists / Orthodontics /
    # Endodontics / Periodontics / "Smile Studio" as recognised tails in
    # _BIZ_NAME_RE but never mirrored them here, so the sync test between the
    # two lists no longer told the truth and "Sabka Dentist" kept "dentist" as
    # a DISTINCTIVE token. Deliberately NOT adding "smile": the tail is the
    # two-word phrase "Smile Studio", and making "smile" generic would empty
    # the token set of "Smile Care Dental" and reopen the 21-Jul fabrication.
    "dentist", "dentists", "orthodontics", "orthodontic",
    "endodontics", "periodontics", "studio",
    "polyclinic", "medical", "medicals", "centre", "center", "care",
    "health", "healthcare", "diagnostics", "nursing", "home", "speciality",
    "specialty", "multispeciality", "multispecialty",
    "physiotherapy", "ayurveda", "homeopathy", "labs", "scans", "fertility",
    # restaurant / hospitality
    "restaurant", "restaurants", "cafe", "café", "caf", "bakery", "bakes",
    # "caf" because _distinctive_tokens matches [A-Za-z] only, so it
    # tokenises "Café" as "caf" — without this, two different cafés
    # share a token and the impostor slips through (R10-C3c).
    "kitchen", "kitchens", "hotel", "hotels", "resort", "resorts", "dhaba",
    "mess", "biryani", "tiffin",
    # education
    "school", "schools", "academy", "college", "institute", "institution",
    "tuition", "tuitions", "coaching", "learning",
    # legal
    "associates", "advocates", "law", "firm", "legal", "chambers",
    # retail
    "store", "stores", "mart", "supermarket", "boutique", "showroom",
    "emporium", "traders",
    # tech
    "technologies", "software", "softwares", "solutions", "systems",
    "digital",
    # ELITE service businesses
    "gym", "fitness", "salon", "spa", "studio", "studios", "motors",
    "garage", "builders", "construction", "constructions", "properties",
    "realtors", "realty", "travels", "tours", "packers", "movers",
    "interiors", "enterprises", "agencies", "services",
    # connectives, possessives and deixis. v16.9 FIX R15-C2a: without these,
    # "Our Dental Clinic is open 9 AM to 6 PM" was REFUSED — "Our" scored as a
    # brand token, so the guard blocked the clinic describing itself.
    "the", "and", "for", "our", "ours", "we", "us", "my", "mine", "your",
    "yours", "their", "theirs", "his", "her", "its", "this", "that", "these",
    "those", "at", "in", "on", "to", "of", "a", "an",
    # Service words. These describe what a business DOES, so they can never be
    # the distinctive part of a name. R15-C2b: "please call Emergency Services
    # immediately" was refused and replaced with "I don't have that detail
    # confirmed" — the guard silencing an emergency instruction is the worst
    # failure it has, and "emergency" belongs here to stop that.
    "emergency", "emergencies", "cleaning", "customer", "professional",
    "quality", "treatment", "treatments", "consultation", "appointment",
    # Tamil / Hindi equivalents of the same function words (R15-C2c)
    "\u0b8e\u0b99\u0bcd\u0b95\u0bb3\u0bcd", "\u0ba8\u0bae\u0ba4\u0bc1", "\u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd", "\u0b87\u0ba8\u0bcd\u0ba4", "\u0b85\u0ba8\u0bcd\u0ba4",
    "\u0939\u092e\u093e\u0930\u093e", "\u0906\u092a\u0915\u093e", "\u092f\u0939", "\u0935\u0939",
}

# v16.9 FIX R15-C2c: the guard exists because of "Smile Care Dental" — and it
# could not see that name written in Tamil script, which is how most patients
# here actually write. _BIZ_NAME_RE requires [A-Z] and _distinctive_tokens
# matches [A-Za-z] only, so "ஸ்மைல் கேர் டென்டல்" sailed through untouched.
_TA_HI_BIZ_TAIL = (
    "\u0b9f\u0bc6\u0ba9\u0bcd\u0b9f\u0bb2\u0bcd", "\u0b95\u0bbf\u0bb3\u0bbf\u0ba9\u0bbf\u0b95\u0bcd", "\u0bae\u0bb0\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1\u0bb5\u0bae\u0ba9\u0bc8", "\u0b86\u0bb8\u0bcd\u0baa\u0ba4\u0bcd\u0ba4\u0bbf\u0bb0\u0bbf",
    "\u0bb9\u0bbe\u0bb8\u0bcd\u0baa\u0bbf\u0b9f\u0bcd\u0b9f\u0bb2\u0bcd", "\u0b95\u0bcd\u0bb3\u0bbf\u0ba9\u0bbf\u0b95\u0bcd",
    "\u0921\u0947\u0902\u091f\u0932", "\u0915\u094d\u0932\u093f\u0928\u093f\u0915", "\u0905\u0938\u094d\u092a\u0924\u093e\u0932",
)
# v16.4 FIX R10-C3: this list decided WHICH business names the guard can even
# see, and it only knew healthcare words — live-tested 26-Jul, a restaurant
# persona naming a rival restaurant passed straight through while the
# identical clinic case blocked. Every vertical the engine sells to now has
# vocabulary here, or its guard is decoration.
_BIZ_TAIL = (
    # healthcare
    r"Dental|Dentistry|Dentists|Dentist|Orthodontics|Orthodontic|"
    # v18.0 FIX R18-C4b: "Dentist" was not a recognised tail, so
    # "Greetings from Sabka Dentist" produced NO candidate and the guard
    # had nothing to compare — an impostor name in the single commonest
    # Indian dental-chain naming style walked straight through.
    r"Endodontics|Periodontics|Smile Studio|Clinic|Clinics|Hospital|"
    r"Hospitals|Polyclinic|"
    r"Diagnostics|Labs|Scans|Physiotherapy|Ayurveda|Homeopathy|"
    r"Nursing\s+Home|Medical\s+Cent(?:re|er)|Health\s+Cent(?:re|er)|"
    r"Care\s+Cent(?:re|er)|Fertility\s+Cent(?:re|er)|"
    # restaurant / hospitality  (NOVA)
    r"Restaurant|Restaurants|Cafe|Café|Bakery|Bakes|Kitchen|Kitchens|"   # noqa: RUF001 — literal é, not an escape (R10-C3c)
    r"Hotel|Hotels|Resort|Resorts|Dhaba|Mess|Biryani|Tiffin\s+Cent(?:re|er)|"
    # education  (SAGE)
    r"School|Schools|Academy|College|Institute|Institution|Tuitions?|"
    r"Coaching\s+Cent(?:re|er)|Learning\s+Cent(?:re|er)|"
    # legal  (LEX)
    r"Associates|Advocates|Law\s+Firm|Legal\s+Services|Chambers|"
    # retail / ecommerce  (PULSE)
    r"Stores?|Mart|Supermarket|Boutique|Showroom|Emporium|Traders|"
    # saas / tech  (APEX)
    r"Technologies|Softwares?|Solutions|Systems|Labs\.|Digital|"
    # ELITE catch-all: the service businesses that actually land on default
    r"Gym|Fitness\s+Cent(?:re|er)|Salon|Spa|Studio|Studios|Motors|Garage|"
    r"Builders|Constructions?|Properties|Realtors|Realty|Travels|Tours|"
    r"Packers|Movers|Interiors|Enterprises|Agencies|Services")
# At least one Capitalised word must precede the tail, so a generic mention
# ("please contact the clinic", "go to a hospital") never trips the guard.
_BIZ_NAME_RE = re.compile(r"\b((?:[A-Z][\w&'\u2019.-]*\s+){1,3}(?:" + _BIZ_TAIL + r"))\b")
# v17.0 R17-C3: the case-INSENSITIVE companion added in R16 is gone. It was
# the direct cause of 8/8 ordinary sentences being refused, and R16's own
# comment claimed the case-sensitive pattern 'runs first' when in fact it
# had no callers at all. Dead code with a confident comment is how R15-C3
# survived a whole round — one pattern, one caller, no narration.

_UNVERIFIED_LINES = {
    "en": ("I don't have that detail confirmed on my side — let me check with "
           "the clinic and come back to you. You can also call the clinic directly."),
    "ta": ("\u0b85\u0ba8\u0bcd\u0ba4 \u0bb5\u0bbf\u0bb5\u0bb0\u0bae\u0bcd \u0b8e\u0ba9\u0bcd\u0ba9\u0bbf\u0b9f\u0bae\u0bcd \u0b89\u0bb1\u0bc1\u0ba4\u0bbf\u0baf\u0bbe \u0b87\u0bb2\u0bcd\u0bb2 \u2014 clinic-\u0b95\u0bbf\u0b9f\u0bcd\u0b9f \u0b95\u0bc7\u0b9f\u0bcd\u0b9f\u0bc1 \u0b9a\u0bca\u0bb2\u0bcd\u0bb1\u0bc7\u0ba9\u0bcd. "
           "\u0ba8\u0bc7\u0bb0\u0b9f\u0bbf\u0baf\u0bbe\u0bb5\u0bc1\u0bae\u0bcd \u0ba4\u0bca\u0b9f\u0bb0\u0bcd\u0baa\u0bc1 \u0b95\u0bca\u0bb3\u0bcd\u0bb3\u0bb2\u0bbe\u0bae\u0bcd."),
    "hi": ("\u092e\u0947\u0930\u0947 \u092a\u093e\u0938 \u092f\u0939 \u091c\u093e\u0928\u0915\u093e\u0930\u0940 \u092a\u0941\u0937\u094d\u091f \u0928\u0939\u0940\u0902 \u0939\u0948 \u2014 \u092e\u0948\u0902 \u0915\u094d\u0932\u093f\u0928\u093f\u0915 \u0938\u0947 \u092a\u0942\u091b\u0915\u0930 \u092c\u0924\u093e\u0924\u093e \u0939\u0942\u0901\u0964 "
           "\u0906\u092a \u0938\u0940\u0927\u0947 \u0915\u094d\u0932\u093f\u0928\u093f\u0915 \u0938\u0947 \u092d\u0940 \u0938\u0902\u092a\u0930\u094d\u0915 \u0915\u0930 \u0938\u0915\u0924\u0947 \u0939\u0948\u0902\u0964"),
}


# v17.0 FIX R16-C4: R15 dumped grammar words and service words into ONE set,
# and that conflation cut both ways. Words like "general", "specialist", "new"
# and "best" ARE legitimately part of business names ("General Hospital"), so
# treating them as never-a-brand let a fabricated referral through — verified:
# "Specialist Dental Clinic la poi paarunga" passed clean. Grammar is a
# different thing from vocabulary: these are stripped from a CANDIDATE because
# they are syntax, but they never make the candidate harmless on their own.
_FUNCTION_WORDS = {
    "our", "ours", "we", "us", "my", "mine", "your", "yours", "their",
    "theirs", "his", "her", "its", "this", "that", "these", "those",
    "the", "a", "an", "and", "or", "for", "at", "in", "on", "to", "of",
    "from", "with", "by", "is", "are", "was", "were", "be", "been",
    "please", "contact", "call", "visit", "book", "booking", "go", "goto",
    "you", "can", "may", "will", "would", "should", "offer", "offers",
    "offering", "provide", "provides", "available", "welcome", "here",
    "near", "nearby", "above", "below", "also", "just", "only",
    "\u0b8e\u0b99\u0bcd\u0b95\u0bb3\u0bcd", "\u0ba8\u0bae\u0ba4\u0bc1", "\u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd", "\u0b87\u0ba8\u0bcd\u0ba4", "\u0b85\u0ba8\u0bcd\u0ba4",
    "\u0939\u092e\u093e\u0930\u093e", "\u0906\u092a\u0915\u093e", "\u092f\u0939", "\u0935\u0939",
}

# v17.0 FIX R16-C5. R15-C2c gave the guard Tamil eyes and immediately blinded
# it to the clinic's own name: `own` is built from the Latin customer_name, so
# for "Vakkai Dental Clinic" the script token set is EMPTY and a perfectly
# correct Tamil reply — "வாக்கை கேர் டென்டல் இன்று திறந்திருக்கும்" — was refused. Every
# Tamil patient asking "clinic open-a?" got "I don't have that detail
# confirmed". Comparing CONSONANT SKELETONS bridges the scripts: Tamil vowel
# spelling varies wildly between writers, consonants barely do, so
# வாக்கை -> "vkk" and "Vakkai" -> "vkk" match, while ஸ்மைல் -> "sml" does not.
_TA_CONSONANT = {
    "\u0b95": "k", "\u0b99": "n", "\u0b9a": "s", "\u0b9e": "n", "\u0b9f": "t", "\u0ba3": "n",
    "\u0ba4": "t", "\u0ba8": "n", "\u0baa": "p", "\u0bae": "m", "\u0baf": "y", "\u0bb0": "r",
    "\u0bb2": "l", "\u0bb5": "v", "\u0bb4": "l", "\u0bb3": "l", "\u0bb1": "r", "\u0ba9": "n",
    "\u0bb8": "s", "\u0bb7": "s", "\u0b9c": "j", "\u0bb9": "h",
    # v17.0 R17-C2b: "\u0b95\u0bcd\u0bb7" was unreachable — the loop iterates single
    # characters, so a three-codepoint key could never match. Dropped.
    # Devanagari, absent in R16: the Tamil bridge was built and Hindi was left
    # blind, so "\u0935\u0915\u094d\u0915\u093e\u0908 \u0921\u0947\u0902\u091f\u0932 \u0915\u094d\u0932\u093f\u0928\u093f\u0915" was refused for clinic "Vakkai".
    "\u0915": "k", "\u0916": "k", "\u0917": "g", "\u0918": "g", "\u091a": "c", "\u091b": "c",
    "\u091c": "j", "\u091d": "j", "\u091f": "t", "\u0920": "t", "\u0921": "d", "\u0922": "d",
    "\u0923": "n", "\u0924": "t", "\u0925": "t", "\u0926": "d", "\u0927": "d", "\u0928": "n",
    "\u092a": "p", "\u092b": "p", "\u092c": "b", "\u092d": "b", "\u092e": "m", "\u092f": "y",
    "\u0930": "r", "\u0932": "l", "\u0935": "v", "\u0936": "s", "\u0937": "s", "\u0938": "s",
    "\u0939": "h",
}


def _consonant_skeleton(text: str) -> str:
    """Consonants only, script-folded. Vowels are where transliteration
    disagrees; consonants are where identity lives."""
    out = []
    for ch in (text or "").lower():
        if ch in _TA_CONSONANT:
            out.append(_TA_CONSONANT[ch])
        elif "a" <= ch <= "z" and ch not in "aeiou":
            out.append(ch)
    # collapse doubles so "vakkai"/"வாக்கை" agree on "vk"
    sk = "".join(out)
    return re.sub(r"(.)\1+", r"\1", sk)


# ── v21.0 · FIX R21-C1 (IDENTITY GUARD — cross-script bridge, own short name) ─
# R17-C2 set _MIN_SKELETON = 3 because two consonants collide at ~75% on real
# Indian brand words, and R16 had let "Try Vikki Dental Clinic" pass for clinic
# "Vakkai" (both reduce to "vk"). That measurement was taken from the
# IMPOSTOR's side only. Nobody measured what the same threshold does when the
# CLINIC'S OWN name reduces to two consonants — and the guard computes
#   my_sk = {sk for sk in ... if len(sk) >= _MIN_SKELETON}
# then gates the whole cross-script branch on `if my_sk and ...`. For a clinic
# whose every brand token is short, my_sk is EMPTY, the branch is skipped, and
# the guard refuses the clinic's own name written in Tamil or Devanagari —
# every single time. Not a narrower match: a total bypass of the bridge, which
# is the failure mode R18-C4 named for marker sets and which lives here too.
#
# Measured on R20 over 22 real Indian dental brand names: the bridge is dead
# for 12 of them (55%) — Vaakai, Vakkai, Sara, Nova, Sri, Deva, Apollo, Anu,
# Ravi, Mano, Jeeva, Aruna. Reproduction, clinic "Vaakai Dental Clinic":
#   _guard_clinic_identity("வாக்கை டென்டல் கிளினிக்கிற்கு வரவேற்கிறோம்.", brain, "hi")
#   → ("இந்த தகவலை என்னால் உறுதிப்படுத்த முடியவில்லை…", True)
# The assistant refuses to greet a patient using its own clinic's name, in the
# script most of this launch market actually writes. R15-C2c and R16-C5 were
# both raised for exactly this harm; R17 reintroduced it through a threshold
# instead of a wordlist, which is why two rounds of tests did not catch it.
#
# Widening the measurement from 22 names to 40 showed the damage is not
# confined to short names. The skeleton also breaks on every romanisation that
# spells a single Indic letter as a Latin digraph or a different voicing:
# "Roshni" → rshn but ரோஷ்னி → rsn (sh is one letter, ஷ); "Prathima" → prthm
# but ப்ரதிமா → prtm; "Ganga" → gng but கங்கா → knk (Tamil has no g). Over 40
# real brand words matched against their own honest Indic rendering, R20's
# bridge succeeds 8 times. It is not a coarse signal; it is a broken one.
#
# The fix is NOT to lower _MIN_SKELETON — that hands "Vikki" back its pass.
# A two-consonant skeleton is untrustworthy because it throws away the vowels,
# and for short Indic names the vowels are precisely where the identity sits
# (vaakai/vikki, sara/sooria, deva/diva). So add a SECOND route that keeps a
# coarse vowel class alongside the consonants and folds the voicing/aspiration
# distinctions Tamil script does not make. R17's comparison is untouched and
# still runs first; a candidate clears by matching on either. Coverage over
# the same 40 names goes 8 → 36, and over all 1560 cross-brand pairs the only
# two acceptances the new route adds are Vaakai↔Vakkai, which are one clinic
# spelling its own name two ways.
#
# Vowel classes are deliberately coarse — length is folded (aa/a, ii/ee/i,
# uu/oo/u) because transliteration disagrees about it, while quality is kept
# because transliteration agrees about it. Diphthongs get non-letter marks so
# they can never collide with the Latin consonants y and w. Voiced/voiceless
# pairs are folded (g→k, d→t, b→p, j→c, s→c) because Tamil script does not
# distinguish them at all — தேவா is written the same whether the clinic
# romanises itself "Deva" or "Theva" — and the retained vowels pay for the
# extra folding.
_XS_VOWEL_SIGN = {          # dependent vowel signs (matras)
    "\u0bbe": "a", "\u0bbf": "i", "\u0bc0": "i", "\u0bc1": "u", "\u0bc2": "u",
    "\u0bc6": "e", "\u0bc7": "e", "\u0bc8": "2", "\u0bca": "o", "\u0bcb": "o",
    "\u0bcc": "3",
    "\u093e": "a", "\u093f": "i", "\u0940": "i", "\u0941": "u", "\u0942": "u",
    "\u0943": "i", "\u0947": "e", "\u0948": "2", "\u094b": "o", "\u094c": "3",
}
_XS_VOWEL_IND = {           # independent vowel letters
    "\u0b85": "a", "\u0b86": "a", "\u0b87": "i", "\u0b88": "i", "\u0b89": "u",
    "\u0b8a": "u", "\u0b8e": "e", "\u0b8f": "e", "\u0b90": "2", "\u0b92": "o",
    "\u0b93": "o", "\u0b94": "3",
    "\u0905": "a", "\u0906": "a", "\u0907": "i", "\u0908": "i", "\u0909": "u",
    "\u090a": "u", "\u090f": "e", "\u0910": "2", "\u0913": "o", "\u0914": "3",
}
_XS_VIRAMA = {"\u0bcd", "\u094d"}      # pulli / halant — kills the inherent vowel
_XS_FOLD   = {"g": "k", "d": "t", "b": "p", "j": "c", "z": "c", "s": "c",
              "f": "p", "w": "v", "q": "k"}
_MIN_VKEY  = 3              # same "carries identity" bar as _MIN_SKELETON


def _xs_latin_vowel(run: str) -> str:
    """Coarse class for a run of Latin vowels. Diphthongs first — 'ai' is what
    separates Vaakai from Vikki and must not be folded into 'a'."""
    if "ai" in run or "ay" in run:
        return "2"
    if "au" in run or "aw" in run:
        return "3"
    if run[:2] in ("ee", "ii"):
        return "i"
    if run[:2] in ("oo", "uu"):
        return "u"
    return run[0]


def _xscript_vkey(text: str) -> str:
    """Consonants AND coarse vowels, script-folded — the higher-precision
    sibling of _consonant_skeleton, used only where the skeleton is too short
    to be trusted (R21-C1). Indic input is read as an abugida: a consonant
    letter carries an inherent 'a' unless a virama kills it or a matra
    overrides it."""
    out: List[str] = []
    s = (text or "").lower()
    i, n = 0, len(s)
    while i < n:
        ch = s[i]
        if ch in _TA_CONSONANT:
            out.append(_XS_FOLD.get(_TA_CONSONANT[ch], _TA_CONSONANT[ch]))
            j = i + 1
            if j < n and s[j] in _XS_VIRAMA:
                i = j + 1                     # dead consonant — no vowel at all
                continue
            if j < n and s[j] in _XS_VOWEL_SIGN:
                out.append(_XS_VOWEL_SIGN[s[j]])
                i = j + 1
                continue
            out.append("a")                   # inherent vowel
            i += 1
            continue
        if ch in _XS_VOWEL_IND:
            out.append(_XS_VOWEL_IND[ch])
            i += 1
            continue
        if "a" <= ch <= "z":
            if ch in "aeiou":
                run = ""
                while i < n and s[i] in "aeiou":
                    run += s[i]
                    i += 1
                out.append(_xs_latin_vowel(run))
                continue
            # aspirate digraphs: Tamil has no separate kh/th/ph letters, so a
            # romanisation that spells them out must fold to the same key.
            if ch == "h" and out and out[-1] in "kctp":
                i += 1
                continue
            out.append(_XS_FOLD.get(ch, ch))
            i += 1
            continue
        i += 1                                 # punctuation, ZWNJ, digits
    return re.sub(r"(.)\1+", r"\1", "".join(out))


def _script_tokens(name: str) -> set:
    """Brand words in Tamil or Devanagari. Same idea as _distinctive_tokens but
    for scripts that have no case, so the [A-Z] anchor cannot be used."""
    toks = re.findall(r"[\u0b80-\u0bff\u0900-\u097f]+", name or "")
    return {t for t in toks
            if t not in _GENERIC_BIZ_WORDS and t not in _TA_HI_BIZ_TAIL
            and len(t) > 2}


def _distinctive_tokens(name: str) -> set:
    """The brand word(s) only. "Vakkai Care Dental" and "Smile Care Dental"
    both reduce to a single token — {vakkai} vs {smile} — so the shared
    generic words ("care", "dental") can't mask an impostor name."""
    toks = re.findall(r"[A-Za-z][A-Za-z'\u2019-]*", (name or "").lower())
    return {t for t in toks if t not in _GENERIC_BIZ_WORDS and len(t) > 2}


# v17.0 R17-C1. A name only matters when the sentence is making a claim about
# who this assistant is, or where this business is. Everything else — service
# lists, treatment names, branch mentions, referrals — is ordinary talk.
_SELF_ID_MARKERS = (
    # v18.0 FIX R18-C4: the marker set decides whether the guard looks at the
    # reply AT ALL, so a missing marker is a silent bypass of the entire
    # guard — not a narrower match. Verified on R17: "You have reached Bright
    # Smile Dental Care", "Thanks for calling Apollo White Dental" and
    # "Greetings from Sabka Dentist" were all waved through, while the same
    # impostor name behind "I am" / "Welcome to" was refused. These are the
    # standard opening lines of every business auto-reply, which makes them
    # the phrasings a model is MOST likely to reach for.
    "you have reached", "you've reached", "youve reached",
    "thanks for calling", "thank you for calling", "thanks for contacting",
    "thank you for contacting", "you are chatting with", "you're chatting with",
    "you are speaking with", "you're speaking with", "speaking with",
    "on behalf of", "greetings from", "reached out to",
    "நீங்கள் தொடர்பு", "தொடர்பு கொண்டது", "சார்பாக",
    "आपने संपर्क", "की ओर से",
    "i am ", "i'm ", "this is ", "we are ", "we're ", "my name is",
    "assistant for", "assistant of", "assistant at", "welcome to",
    "is located", "are located", "located at", "located in",
    "our address", "the address is", "address is",
    " is at ", " is in ", " are at ",
    "naan ", "engal ", "namadhu ", "oda assistant", "-oda ", "amaindh",
    "irukku", "irukk", "-la iru", "-il iru", "kitta iru",
    "\u0ba8\u0bbe\u0ba9\u0bcd ", "\u0b8e\u0b99\u0bcd\u0b95\u0bb3\u0bcd ", "\u0ba8\u0bae\u0ba4\u0bc1 ", "\u0b89\u0ba4\u0bb5\u0bbf\u0baf\u0bbe\u0bb3", "\u0bae\u0bc1\u0b95\u0bb5\u0bb0\u0bbf",
    "\u0b87\u0bb0\u0bc1\u0b95\u0bcd\u0b95", "\u0bb5\u0bb0\u0bb5\u0bc7\u0bb1\u0bcd",
    "\u092e\u0948\u0902 ", "\u0939\u092e\u093e\u0930\u093e ", "\u0938\u094d\u0925\u093f\u0924 ", "\u092a\u0924\u093e ",
)

# v17.0 R17-C2. Measured collision rate on real Indian clinic brand words was
# ~75% at 2 consonants (Sri/Sree/Saru -> "sr"; Vakkai/Vikki -> "vk"), which is
# why R16 let "Try Vikki Dental Clinic" pass for clinic "Vakkai". Three
# consonants is the shortest length that carries identity.
_MIN_SKELETON = 3


def _is_cross_script(a: str, b: str) -> bool:
    """True when the two strings are written in different alphabets — the only
    situation where a consonant skeleton is the right tool."""
    ind = lambda t: any("\u0900" <= c <= "\u0d7f" for c in (t or ""))
    lat = lambda t: any("a" <= c.lower() <= "z" for c in (t or ""))
    return (ind(a) and lat(b) and not ind(b)) or (ind(b) and lat(a) and not ind(a))


def _guard_clinic_identity(reply: str, brain: Dict, user_text: str) -> Tuple[str, bool]:
    """Refuse a reply that claims THIS assistant belongs to a different business.

    v17.0 REWRITE (R17-C1). This guard has been patched six times — R7, R8-M2,
    R10-C3, R15-C2, R16-C4/5/6 — and every round traded false positives for
    false negatives, because it was scanning the WHOLE reply for anything that
    looked like a business name and then arguing about stopword lists. R16
    reached the point of refusing 8 of 8 ordinary clinic sentences: "We offer
    teeth cleaning services", "You can visit our Kalapatti branch clinic". A
    guard that blocks half of normal traffic does more damage than the
    hallucination it prevents.

    The fix is scope, not vocabulary. What actually went wrong on 21-Jul was a
    SELF-IDENTIFICATION claim — "Smile Care Dental is located at RS Puram" from
    an assistant that belongs to a different clinic. So a candidate name is
    only examined when it sits next to a marker that makes it a claim about
    who WE are or where WE are. Describing services, listing treatments and
    naming a branch are none of those things and are now out of scope.

    This deliberately catches LESS than R16 did. It catches the failure it was
    built for, and it does not break ordinary conversation — which, on the
    evidence of six rounds, is the harder half.
    """
    if not reply:
        return reply, False

    low = reply.lower()
    if not any(mk in low for mk in _SELF_ID_MARKERS):
        return reply, False                      # not an identity claim at all

    own = _distinctive_tokens(brain.get("customer_name") or "")
    own_script = _script_tokens(brain.get("customer_name") or "")
    mine = own | own_script
    # Precomputed once, not per candidate (R16-M4 was O(candidates x own)).
    my_sk = {sk for sk in (_consonant_skeleton(t) for t in mine)
             if len(sk) >= _MIN_SKELETON}
    # v21.0 FIX R21-C1: the vowel-aware key, precomputed the same way.
    my_vk = {vk for vk in (_xscript_vkey(t) for t in mine)
             if len(vk) >= _MIN_VKEY}

    cands = [mm.group(1) for mm in _BIZ_NAME_RE.finditer(reply)]
    # A model that drops capitalisation has not stopped fabricating, so an
    # all-lowercase reply is title-cased and rescanned. Ordinary sentences
    # carry capitals, so this cannot reintroduce the R16 false positives.
    # R17-C1b: title-cased rescan runs unconditionally. R15/R16 gated it on the
    # whole reply being lowercase, which a single "Hi!" defeated — but that gate
    # only existed to stop ordinary sentences becoming candidates, and the
    # marker check above already does that far better.
    cands += [mm.group(1) for mm in _BIZ_NAME_RE.finditer(reply.title())]
    for tail in _TA_HI_BIZ_TAIL:
        cands += [mm.group(1) for mm in re.finditer(
            r"((?:[\u0b80-\u0bff\u0900-\u097f]+[\s\u200c-]+){1,3}" + re.escape(tail) + r")",
            reply)]

    for cand in cands:
        cand_tok = {t for t in (_distinctive_tokens(cand) | _script_tokens(cand))
                    if t not in _FUNCTION_WORDS}
        if not cand_tok:
            continue                              # generic phrase, no claim
        if mine and (cand_tok & mine):
            continue                              # it is us, spelled the same
        # Cross-script only: a consonant skeleton is a coarse signal ("Vakkai"
        # and "Vikki" both reduce to "vk"), so it may confirm a match across
        # alphabets but must never be trusted to clear a same-script name.
        if _is_cross_script(cand, brain.get("customer_name") or ""):
            if my_sk:
                cand_sk = {sk for sk in (_consonant_skeleton(t) for t in cand_tok)
                           if len(sk) >= _MIN_SKELETON}
                if cand_sk & my_sk:
                    continue
            # v21.0 FIX R21-C1: everything above is R17, unchanged and tried
            # first. This is a SECOND route, not a replacement — a candidate
            # clears only by matching the clinic on one of them, so the change
            # is monotone: it can turn a refusal into a pass, never the
            # reverse (asserted over the whole corpus in the R21 suite).
            #
            # Measured on R20 over 40 real Indian clinic brand words, each
            # against its own honest Tamil/Devanagari rendering:
            #   consonant skeleton alone  ..  8/40 self-match   (bridge dead
            #                                 for 80% of clinics)
            #   vowel-aware key alone     .. 33/40
            #   either                    .. 36/40
            # and over all 1560 cross-brand pairs (clinic X vs impostor Y):
            #   skeleton false-accepts .. 0/1560
            #   either   false-accepts .. 2/1560, both of them Vaakai↔Vakkai
            #                             — the SAME name spelled two ways,
            #                             which is the answer we want anyway.
            # So the union is ~4.5x the coverage at no measured cost in
            # impostor acceptance. The four still missed (Bright, Clove,
            # Meenakshi, Chandra) fail on Latin orthography, not on script —
            # silent-e, gh, kṣ, and the epenthetic vowel Tamil inserts into
            # "ndr". Deliberately not chased: each needs English pronunciation
            # rules, and chasing them is how a contained round stops being one.
            if my_vk:
                cand_vk = {vk for vk in (_xscript_vkey(t) for t in cand_tok)
                           if len(vk) >= _MIN_VKEY}
                if cand_vk & my_vk:
                    continue
        log.error(f"\U0001f6d1 R7-C1 identity guard: reply claimed identity "
                  f"{cand!r} for business {brain.get('customer_name')!r} "
                  f"\u2014 refused, not cached, not stored.")
        analytics.inc("guard.identity_block")
        lang = detect_language(user_text)
        return _UNVERIFIED_LINES.get(lang, _UNVERIFIED_LINES["en"]), True
    return reply, False


# ── v16.2 · FIX R8-C2 (CRITICAL) ─────────────────────────────────────────────
# Observed 22-Jul across two adversarial rounds. The model is well guarded
# against inventing FACTS ("I don't have the doctor's registration number",
# "I can't confirm an all-inclusive total") — the prompt forbids that. Nothing
# forbade claiming an ACTION, so it happily said "all your appointments have
# been cancelled" and "I won't send you messages anymore" while no booking
# row moved and no opt-out was recorded. A patient believes both.
#
# This function can only run when handle_booking and the opt-out handler have
# ALREADY declined to act — by construction, any completed-action claim
# reaching here is false. So the claim is refused rather than sent.
_ACTION_CLAIM_PATTERNS = (
    # English
    "has been cancel", "have been cancel", "i have cancel", "i've cancel",
    "is cancelled", "are cancelled", "is canceled", "are canceled",
    "has been booked", "have been booked", "i have booked", "i've booked",
    "is confirmed", "has been confirmed", "i have removed you",
    "you have been unsubscribed", "i won't send", "i will not send",
    "i won t send", "i have unsubscribed",
    # Tamil
    "\u0bb0\u0ba4\u0bcd\u0ba4\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f",
    "\u0bb0\u0ba4\u0bcd\u0ba4\u0bc1\u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f",
    "\u0bb0\u0ba4\u0bcd\u0ba4\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0ba4\u0bc1\u0bb5\u0bbf\u0b9f\u0bcd\u0b9f",
    "\u0baa\u0ba4\u0bbf\u0bb5\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f",
    "\u0baa\u0bc1\u0b95\u0bcd \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f",
    "\u0b85\u0ba9\u0bc1\u0baa\u0bcd\u0baa \u0bae\u0bbe\u0b9f\u0bcd\u0b9f\u0bc7\u0ba9\u0bcd",
    # Hindi
    "\u0930\u0926\u094d\u0926 \u0915\u0930 \u0926\u093f\u092f", "\u0930\u0926\u094d\u0926 \u0915\u0930 \u0926\u0940",
    "\u092c\u0941\u0915 \u0915\u0930 \u0926\u093f\u092f", "\u0928\u0939\u0940\u0902 \u092d\u0947\u091c\u0942\u0902\u0917",
    # Romanised Tamil
    "cancel pannitten", "cancel panniten", "cancel aagiduchu", "cancel aiduchu",
    "book pannitten", "book panniten", "anuppa matten", "anuppa maaten",
)
_OPTOUT_CLAIM_HINTS = ("send", "unsubscrib", "\u0b85\u0ba9\u0bc1\u0baa\u0bcd\u0baa",
                       "\u092d\u0947\u091c", "anuppa", "removed you")
_NO_ACTION_LINES = {
    "en": ("I'm not able to book or cancel anything myself — I can only pass "
           "this on. Please contact the clinic directly to confirm, and they "
           "will take care of it."),
    "ta": ("\u0b8e\u0ba9\u0bcd\u0ba9\u0bbe\u0bb2\u0bcd \u0ba8\u0bc7\u0bb0\u0b9f\u0bbf\u0baf\u0bbe\u0b95 book \u0b85\u0bb2\u0bcd\u0bb2\u0ba4\u0bc1 cancel \u0b9a\u0bc6\u0baf\u0bcd\u0baf \u0bae\u0bc1\u0b9f\u0bbf\u0baf\u0bbe\u0ba4\u0bc1. "
           "\u0ba4\u0baf\u0bb5\u0bc1\u0b9a\u0bc6\u0baf\u0bcd\u0ba4\u0bc1 clinic-\u0b90 \u0ba8\u0bc7\u0bb0\u0b9f\u0bbf\u0baf\u0bbe\u0b95\u0ba4\u0bcd \u0ba4\u0bca\u0b9f\u0bb0\u0bcd\u0baa\u0bc1 \u0b95\u0bca\u0ba3\u0bcd\u0b9f\u0bc1 \u0b89\u0bb1\u0bc1\u0ba4\u0bbf\u0baa\u0bcd\u0baa\u0b9f\u0bc1\u0ba4\u0bcd\u0ba4\u0bbf\u0b95\u0bcd\u0b95\u0bca\u0bb3\u0bcd\u0bb3\u0bb5\u0bc1\u0bae\u0bcd."),
    "hi": ("\u092e\u0948\u0902 \u0916\u0941\u0926 \u092c\u0941\u0915\u093f\u0902\u0917 \u092f\u093e \u0930\u0926\u094d\u0926 \u0928\u0939\u0940\u0902 \u0915\u0930 \u0938\u0915\u0924\u093e\u0964 "
           "\u0915\u0943\u092a\u092f\u093e \u0938\u0940\u0927\u0947 \u0915\u094d\u0932\u093f\u0928\u093f\u0915 \u0938\u0947 \u0938\u0902\u092a\u0930\u094d\u0915 \u0915\u0930\u0947\u0902\u0964"),
}
_OPTOUT_HOWTO_LINES = {
    "en": ("To stop messages I need it recorded properly \u2014 please send just "
           "the word STOP and it takes effect immediately."),
    "ta": ("\u0b9a\u0bc6\u0baf\u0ba4\u0bbf\u0b95\u0bb3\u0bcd \u0ba8\u0bbf\u0bb1\u0bc1\u0ba4\u0bcd\u0ba4 \u0b85\u0ba4\u0bc1 \u0b9a\u0bb0\u0bbf\u0baf\u0bbe\u0b95\u0baa\u0bcd \u0baa\u0ba4\u0bbf\u0bb5\u0bbe\u0b95 \u0bb5\u0bc7\u0ba3\u0bcd\u0b9f\u0bc1\u0bae\u0bcd \u2014 "
           "'STOP' \u0b8e\u0ba9\u0bcd\u0bb1\u0bc1 \u0bae\u0b9f\u0bcd\u0b9f\u0bc1\u0bae\u0bcd \u0ba4\u0ba9\u0bbf\u0baf\u0bbe\u0b95 \u0b85\u0ba9\u0bc1\u0baa\u0bcd\u0baa\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd, \u0b89\u0b9f\u0ba9\u0bc7 \u0ba8\u0bbf\u0ba9\u0bcd\u0bb1\u0bc1\u0bb5\u0bbf\u0b9f\u0bc1\u0bae\u0bcd."),
    "hi": ("\u0938\u0902\u0926\u0947\u0936 \u092c\u0902\u0926 \u0915\u0930\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f \u0915\u0943\u092a\u092f\u093e \u0915\u0947\u0935\u0932 STOP \u092d\u0947\u091c\u0947\u0902\u0964"),
}


# ── v18.0 · FIX R18-C3 (unbacked action claims) ──────────────────────────────
# RESCHEDULE was absent from _ACTION_CLAIM_PATTERNS entirely — in every
# language — even though reschedule is a first-class action in the booking
# state machine (handle_booking, intent "reschedule", owner event
# "rescheduled", template "booked_rescheduled"). So the one guard whose whole
# job is "the model must not claim an action that did not run" was blind to a
# third of the actions that exist. Verified on R17: "I have rescheduled your
# appointment to 4 PM" passed straight through.
# Also closed here, all reproduced: "i've unsubscribed"/"i've removed you"
# (the contracted twins of forms that WERE listed), Tamil and Hindi CONFIRM
# (both had cancel and book but not confirm, while English had confirm), and
# romanized "confirm pannitten" (cancel/book pannitten were listed).
_ACTION_CLAIM_PATTERNS_R18 = (
    # reschedule / move — en
    "has been reschedul", "have been reschedul", "i have reschedul",
    "i've reschedul", "is reschedul", "are reschedul",
    "i have moved your", "i've moved your", "i have changed your appointment",
    "i've changed your appointment", "has been moved to",
    # reschedule — ta / hi / roman
    "மாற்றப்பட்ட", "மாற்றி விட்ட", "மாற்றிவிட்ட",
    "बदल दिय", "बदल दी", "reschedule pannitten", "reschedule panniten",
    "time maathitten", "maathitten",
    # contracted twins of forms already listed
    "i've unsubscribed", "i've removed you", "i have removed your name",
    # confirm — ta / hi / roman (en already had "is confirmed")
    "உறுதி செய்யப்பட்ட", "உறுதிசெய்யப்பட்ட", "confirm செய்யப்பட்ட",
    "कन्फर्म हो गय", "कन्फर्म कर दिय", "पुष्टि हो गय",
    "confirm pannitten", "confirm panniten", "confirm aagiduchu",
)
_ACTION_CLAIM_PATTERNS = tuple(_ACTION_CLAIM_PATTERNS) + _ACTION_CLAIM_PATTERNS_R18


def _guard_unbacked_action_claim(reply: str, user_text: str) -> Tuple[str, bool]:
    """Refuse any reply that claims a booking/cancellation/opt-out was done."""
    if not reply:
        return reply, False
    low = reply.lower()
    hit = next((p for p in _ACTION_CLAIM_PATTERNS if p in low), None)
    if not hit:
        return reply, False
    lang = detect_language(user_text)
    optout = any(h in low for h in _OPTOUT_CLAIM_HINTS) and (
        "cancel" not in hit and "book" not in hit)
    log.error(f"\U0001f6d1 R8-C2 action-claim guard: model claimed {hit!r} "
              f"but no action ran \u2014 reply refused, not cached, not stored.")
    analytics.inc("guard.action_claim_block")
    table = _OPTOUT_HOWTO_LINES if optout else _NO_ACTION_LINES
    return table.get(lang, table["en"]), True


# ── v16.8 · FIX R14-C2 (PATIENT SAFETY) ──────────────────────────────────────
# Prompt rules are requests; the R14-C1 wording above is a request too, and the
# previous version of it was ignored twice on exactly this topic — once giving
# a pregnant patient X-ray guidance, once telling a pacemaker patient which
# drills are safe. Worse, the pacemaker question was asked twice nine minutes
# apart and answered correctly once and unsafely once: prompt compliance is
# probabilistic, so a doctor testing the demo cannot be shown a stable answer.
#
# Detection needs THREE signals together, because any one alone is harmless:
#   1. the PATIENT disclosed a condition/state (pregnancy, pacemaker, blood
#      thinner, diabetes, implant, chemo...),
#   2. the REPLY reaches a safety verdict ("is safe", "not required",
#      "avoid", "romba safe"...), and
#   3. the REPLY names a procedure, drug or device the verdict is about.
# All three means a clinical judgement about THIS patient. Any fewer means
# ordinary conversation — "it is safe to come during working hours" must pass.
#
# Both directions are refused. "Unsafe / avoid it" is not the cautious side:
# talking a patient out of needed treatment is its own harm.
# How far back a disclosed condition stays relevant. Generous on purpose: the
# cost of remembering too long is a referral the patient did not need; the cost
# of forgetting is a safety verdict for a pregnant or anticoagulated patient.
# v17.0 FIX R16-M1: this was named "TURNS" but history holds MESSAGES, so 20
# meant roughly 10 exchanges — and the slice was a no-op whenever history was
# already capped below it. Named for what it counts, and set above the history
# cap so the whole retained conversation is always scanned.
# v17.0 R17-M1a: 60 sat above CHAT_HISTORY_LIMIT (20), so the slice was inert
# and the real window was whatever the caller loaded. Matched to the actual
# limit so the number states the truth rather than an aspiration.
_SAFETY_HISTORY_MESSAGES = 20
_PATIENT_CONDITION_TERMS = (
    "pregnan", "\u0b95\u0bb0\u0bcd\u0baa\u0bcd\u0baa", "garbh", "conceive", "trimester", "breastfeed",
    "pacemaker", "stent", "bypass", "heart condition", "cardiac", "cardiolog",
    "blood thinner", "warfarin", "aspirin", "anticoagul",
    "diabet", "sugar level", "\u0b9a\u0bb0\u0bcd\u0b95\u0bcd\u0b95\u0bb0\u0bc8",
    # v17.0 FIX R16-M2: bare "bp " matched "my bp is fine" and turned a
    # reassurance into a disclosed condition. Qualified forms only.
    # v17.0 R17-C5a: R16-M2 fixed the "my bp is fine" false positive by listing
    # adjective-FIRST forms only, so it missed "my bp is high", "enakku bp
    # irukku", "bp 160" — the phrasings people here actually use. Both orders
    # now, still without the bare "bp " that started this.
    "high bp", "low bp", "bp problem", "bp tablet", "bp medicine",
    "bp is high", "bp high", "bp irukku", "bp iruku", "bp patient",
    "bp 1", "bp 2", "sugar and bp", "bp and sugar", "bp check",
    "blood pressure", "hypertens", "thyroid",
    "asthma", "epilep", "seizure", "kidney", "dialysis", "liver", "hepatit",
    "cancer", "chemo", "radiation therapy", "tumour", "tumor",
    # v17.0 R17-C5b: "prosthe" matched "prosthesis/prosthetic", ordinary DENTAL
    # vocabulary (dentures, crowns) — the same collision as "implant", one word
    # over. Qualified forms only.
    "hiv", "immune", "transplant", "joint prosthesis", "prosthetic joint",
    "prosthetic valve",
    # v17.0 FIX R16-C2: bare "implant" sat in BOTH this list and
    # _PROCEDURE_TERMS. Once R16-C1 made history actually readable, one
    # "how much for a dental implant?" would mark the whole conversation as a
    # disclosed medical condition, and every later routine answer would be
    # refused — breaking the highest-value dental enquiry there is. A MEDICAL
    # implant is qualified; a dental implant is a procedure and stays there.
    "cochlear implant", "knee implant", "hip implant", "metal implant",
    "joint replacement", "artificial valve", "heart implant",
    "allerg", "penicillin", "anaesthes", "anesthes",
    "on medication", "medicine eduthu", "tablet eduthu", "maruthu",
)
# ── v22.0 · FIX R22-C1 (PATIENT SAFETY — the guard's three gates are AND-ed,
#    and two of the three had no Indic vocabulary at all) ──────────────────────
# _guard_clinical_safety_verdict refuses a reply only when THREE lists all hit:
# the patient disclosed a condition, the reply reaches a safety verdict, and the
# reply names a procedure. Three ANDs mean three independent chances at a TOTAL
# bypass — the R21 defect class, one layer up. Nobody had measured this guard
# from the non-English side.
#
# Measured on R21 over 672 realistic cases (7 conditions x 6 procedures x 4
# verdict phrasings x 4 languages), each an R14-shaped failure — a disclosed
# condition, a named procedure, a safety verdict:
#
#     language        refused      gate that opened
#     English         168/168      —
#     Thanglish       108/168      verdict 42, condition 24
#     Tamil script      0/168      procedure 168, condition 120, verdict 42
#     Hindi             0/168      condition 168, verdict 168, procedure 168
#
# _PROCEDURE_TERMS was 100% Latin, so every reply written in Tamil or Devanagari
# failed gate 3 whatever else it said. _SAFETY_VERDICT_TERMS carried three Tamil
# entries and NO Devanagari. _PATIENT_CONDITION_TERMS carried two Tamil words and
# no Devanagari beyond the romanised "garbh".
#
# This matters more than the raw numbers because of R8-M1: the system prompt PINS
# the reply to the patient's own language ("THIS TURN: the user's message is in
# Tamil. Reply in that same language."). So the guard was structurally at its
# weakest in exactly the conversations it exists for. End to end on /chat, model
# stubbed to the reply a real patient would receive:
#     EN "A dental x-ray is safe for you"          -> refused, referral line sent
#     TA "பல் எக்ஸ்-ரே உங்களுக்கு பாதுகாப்பானது"        -> DELIVERED VERBATIM
#     HI "डेंटल एक्स-रे आपके लिए सुरक्षित है"            -> DELIVERED VERBATIM
# R14 exists because HELIO twice gave a clinical verdict — lead-apron guidance to
# a pregnant patient, "drills are safe / antibiotics usually not required" to a
# pacemaker patient. In Tamil and Hindi that control was never switched on.
#
# NOT MONOTONE, and said out loud (R21 could prove direction; this cannot).
# Adding terms can only turn passes into refusals, so the entire risk is false
# positives — and a false positive here mutes a useful answer and pushes a
# patient toward a consultation they did not need. The burden of proof is
# therefore on the control side, measured below at the fix.
#
# What is deliberately NOT here:
#  - No bare "safe" equivalent. English lists "is safe"/"safe to", never "safe",
#    so "there is safe parking behind the building" survives. The Tamil and Hindi
#    entries are the inflected predicate forms only, for the same reason.
#  - No bare "வலி"/"दर्द" (pain) or "பிரச்சனை"/"समस्या" (problem) in the condition
#    list. Every dental patient has pain and a problem; that is the presenting
#    complaint, not a disclosed medical condition, and it would mark every
#    conversation for the rest of its life (the R16-C2 harm).
#  - No bare "ஒவ்வாமை"/"एलर्जी" without qualification beyond what English already
#    carries — "allerg" is already listed and already accepts the pre-op
#    disclosure trade-off that R18-C2 documented for the emergency list.
_PATIENT_CONDITION_TERMS_R22 = (
    # ── pregnancy / feeding — Devanagari, plus the Tamil forms beyond கர்ப்ப
    "\u0917\u0930\u094d\u092d", "\u092a\u094d\u0930\u0947\u0917\u094d\u0928\u0947\u0902\u091f", "\u0917\u0930\u094d\u092d\u0935\u0924\u0940",
    "\u0938\u094d\u0924\u0928\u092a\u093e\u0928", "\u0918\u094d\u0930\u0928\u0940",
    "\u0b95\u0bb0\u0bc1\u0bb5\u0bc1\u0bb1\u0bcd", "\u0baa\u0bbe\u0bb2\u0bcd \u0b95\u0bca\u0b9f\u0bc1",
    # ── cardiac / implanted device
    "\u092a\u0947\u0938\u092e\u0947\u0915\u0930", "\u0938\u094d\u091f\u0947\u0902\u091f", "\u0926\u093f\u0932 \u0915\u0940 \u092c\u0940\u092e\u093e\u0930",
    "\u0939\u0943\u0926\u092f \u0930\u094b\u0917", "\u092c\u093e\u092f\u092a\u093e\u0938",
    "\u0baa\u0bc7\u0bb8\u0bcd\u0bae\u0bc7\u0b95\u0bcd\u0b95\u0bb0\u0bcd", "\u0b9a\u0bcd\u0b9f\u0bc6\u0ba3\u0bcd\u0b9f\u0bcd", "\u0b87\u0ba4\u0baf \u0ba8\u0bcb\u0baf\u0bcd",
    "\u0b87\u0ba4\u0baf\u0bae\u0bcd \u0b85\u0bb1\u0bc1\u0bb5\u0bc8",
    # ── anticoagulants
    "\u0916\u0942\u0928 \u092a\u0924\u0932\u093e", "\u0935\u093e\u0930\u092b\u093c\u093e\u0930\u093f\u0928",
    "\u0bb0\u0ba4\u0bcd\u0ba4\u0bae\u0bcd \u0b89\u0bb1\u0bc8\u0baf\u0bbe\u0bae\u0bb2\u0bcd",
    # ── diabetes — note "\u0b9a\u0bc1\u0b95\u0bb0\u0bcd"/"\u0936\u0941\u0917\u0930" are what patients actually type;
    #    the dictionary words \u0b9a\u0bb0\u0bcd\u0b95\u0bcd\u0b95\u0bb0\u0bc8/\u092e\u0927\u0941\u092e\u0947\u0939 are what only textbooks use.
    "\u0936\u0941\u0917\u0930", "\u092e\u0927\u0941\u092e\u0947\u0939", "\u0921\u093e\u092f\u092c\u093f\u091f\u0940\u091c",
    "\u0b9a\u0bc1\u0b95\u0bb0\u0bcd", "\u0ba8\u0bc0\u0bb0\u0bbf\u0bb4\u0bbf\u0bb5\u0bc1",
    # ── blood pressure — qualified both orders, mirroring R17-C5a, never bare
    "\u0939\u093e\u0908 \u092c\u0940\u092a\u0940", "\u092c\u0940\u092a\u0940 \u0939\u093e\u0908", "\u092c\u0940\u092a\u0940 \u0915\u0940 \u0926\u0935\u093e",
    "\u092c\u0940\u092a\u0940 \u0939\u0948", "\u0930\u0915\u094d\u0924\u091a\u093e\u092a", "\u092c\u094d\u0932\u0921 \u092a\u094d\u0930\u0947\u0936\u0930",
    "\u0b89\u0baf\u0bb0\u0bcd \u0bb0\u0ba4\u0bcd\u0ba4", "\u0bb0\u0ba4\u0bcd\u0ba4 \u0b85\u0bb4\u0bc1\u0ba4\u0bcd\u0ba4", "\u0baa\u0bbf\u0baa\u0bbf \u0b87\u0bb0\u0bc1",
    # ── endocrine / respiratory / neuro
    "\u0925\u093e\u092f\u0930\u093e\u0907\u0921", "\u0926\u092e\u093e", "\u0905\u0938\u094d\u0925\u092e\u093e", "\u092e\u093f\u0930\u094d\u0917\u0940", "\u0926\u094c\u0930\u093e \u092a\u0921\u093c",
    "\u0ba4\u0bc8\u0bb0\u0bbe\u0baf\u0bcd\u0b9f\u0bc1", "\u0b86\u0bb8\u0bcd\u0ba4\u0bc1\u0bae\u0bbe", "\u0bb5\u0bb2\u0bbf\u0baa\u0bcd\u0baa\u0bc1 \u0ba8\u0bcb\u0baf\u0bcd",
    # ── organ / oncology / immune
    "\u0915\u093f\u0921\u0928\u0940", "\u0921\u093e\u092f\u0932\u093f\u0938\u093f\u0938", "\u0932\u093f\u0935\u0930", "\u0915\u0948\u0902\u0938\u0930", "\u0915\u0940\u092e\u094b",
    "\u0b9a\u0bbf\u0bb1\u0bc1\u0ba8\u0bc0\u0bb0\u0b95", "\u0b95\u0bc0\u0bae\u0bcb", "\u0baa\u0bc1\u0bb1\u0bcd\u0bb1\u0bc1\u0ba8\u0bcb\u0baf\u0bcd", "\u0b95\u0bb2\u0bcd\u0bb2\u0bc0\u0bb0\u0bb2\u0bcd",
    # ── allergy / anaesthetic history (the twins of "allerg"/"anaesthes")
    "\u090f\u0932\u0930\u094d\u091c\u0940", "\u0910\u0932\u0930\u094d\u091c\u0940", "\u092a\u0947\u0928\u093f\u0938\u093f\u0932\u093f\u0928",
    "\u0b92\u0bb5\u0bcd\u0bb5\u0bbe\u0bae\u0bc8", "\u0baa\u0bc6\u0ba9\u0bbf\u0b9a\u0bbf\u0bb2\u0bbf\u0ba9\u0bcd",
    # Romanised Tamil, same R18-C1 reason. "sugar level" was listed; "sugar
    # irukku" — how a patient here actually discloses diabetes — was not, and it
    # was the only Thanglish condition of seven that failed the gate. Qualified
    # with the verb, never bare "sugar", which would catch "sugar free".
    "sugar irukku", "sugar iruku", "sugar patient", "sugar problem",
)
_PATIENT_CONDITION_TERMS = _PATIENT_CONDITION_TERMS + _PATIENT_CONDITION_TERMS_R22
_SAFETY_VERDICT_TERMS = (
    "is safe", "are safe", "safe to", "safe-ah", "safe-dhan", "safe dhan",
    "generally safe", "completely safe", "perfectly safe", "romba safe",
    "not safe", "unsafe", "should avoid", "must avoid", "avoid taking",
    "do not require", "does not require", "not required", "no need for",
    "is required", "you will need", "recommended for you", "contraindicat",
    "\u0baa\u0bbe\u0ba4\u0bc1\u0b95\u0bbe\u0baa\u0bcd", "\u0b86\u0baa\u0ba4\u0bcd\u0ba4\u0bc1", "\u0ba4\u0bb5\u0bbf\u0bb0\u0bcd\u0b95\u0bcd\u0b95",
)
# v22.0 FIX R22-C1 — gate 2 carried three Tamil stems and ZERO Devanagari, so a
# Hindi reply could not reach a verdict this guard was able to see. The Tamil
# side also missed the two commonest ways a verdict is actually phrased here:
# "\u0ba4\u0bc7\u0bb5\u0bc8\u0baf\u0bbf\u0bb2\u0bcd\u0bb2\u0bc8" (not required — the pacemaker/antibiotic sentence R14 was
# raised for, verbatim) and "\u0baa\u0bbf\u0bb0\u0b9a\u0bcd\u0b9a\u0ba9\u0bc8 \u0b87\u0bb2\u0bcd\u0bb2\u0bc8" (no problem).
# Following the English list's discipline exactly: no bare "\u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924"/"\u0baa\u0bbe\u0ba4\u0bc1\u0b95\u0bbe\u0baa\u0bcd"
# as a standalone word would be added that did not already exist — the entries
# below are predicate forms ("... \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u0939\u0948" = "is safe"), so "\u092a\u093e\u0930\u094d\u0915\u093f\u0902\u0917
# \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u0939\u0948" is the one case knowingly accepted, and it needs a disclosed
# condition AND a procedure term in the same reply to matter.
_SAFETY_VERDICT_TERMS_R22 = (
    # Tamil — the missing phrasings
    "\u0ba4\u0bc7\u0bb5\u0bc8\u0baf\u0bbf\u0bb2\u0bcd\u0bb2", "\u0ba4\u0bc7\u0bb5\u0bc8 \u0b87\u0bb2\u0bcd\u0bb2", "\u0baa\u0bbf\u0bb0\u0b9a\u0bcd\u0b9a\u0ba9\u0bc8 \u0b87\u0bb2\u0bcd\u0bb2",
    "\u0baa\u0bbf\u0bb0\u0b9a\u0bcd\u0b9a\u0ba9\u0bc8 \u0b95\u0bbf\u0b9f\u0bc8\u0baf\u0bbe", "\u0baa\u0bb0\u0bb5\u0bbe\u0baf\u0bbf\u0bb2\u0bcd\u0bb2", "\u0b86\u0baa\u0ba4\u0bcd\u0ba4\u0bc1 \u0b87\u0bb2\u0bcd\u0bb2",
    "\u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0bb2\u0bbe\u0bae\u0bcd", "\u0b9a\u0bc6\u0baf\u0bcd\u0baf \u0b95\u0bc2\u0b9f\u0bbe\u0ba4\u0bc1", "\u0ba4\u0bc7\u0bb5\u0bc8\u0baa\u0bcd\u0baa\u0b9f",
    # Hindi — none of this existed
    "\u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u0939\u0948", "\u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u0930\u0939\u0947\u0917", "\u092a\u0942\u0930\u0940 \u0924\u0930\u0939 \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924",
    "\u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u0928\u0939\u0940\u0902", "\u0916\u0924\u0930\u093e \u0928\u0939\u0940\u0902", "\u0915\u094b\u0908 \u0926\u093f\u0915\u094d\u0915\u0924 \u0928\u0939\u0940\u0902",
    "\u091c\u093c\u0930\u0942\u0930\u0924 \u0928\u0939\u0940\u0902", "\u091c\u0930\u0942\u0930\u0924 \u0928\u0939\u0940\u0902", "\u0906\u0935\u0936\u094d\u092f\u0915\u0924\u093e \u0928\u0939\u0940\u0902",
    "\u092c\u091a\u0928\u093e \u091a\u093e\u0939\u093f\u090f", "\u0928\u0939\u0940\u0902 \u0915\u0930\u0935\u093e\u0928\u093e \u091a\u093e\u0939\u093f\u090f", "\u0915\u0930\u0935\u093e \u0938\u0915\u0924\u0947 \u0939\u0948\u0902",
    "\u0932\u0947\u0928\u093e \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924", "\u0906\u092a\u0915\u0947 \u0932\u093f\u090f \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924", "\u0915\u094b\u0908 \u0916\u0924\u0930\u093e \u0928\u0939\u0940\u0902",
    # Romanised Tamil. R18-C1 keeps Latin on EXACT token matching by design, so
    # every surface form has to be spelled out — and the measurement showed the
    # imperative "avoid pannunga" (the way an actual Thanglish reply tells you to
    # skip something) had no listed twin, while "should avoid"/"must avoid" did.
    # 42 of the 60 Thanglish misses were this single unlisted phrasing.
    "avoid pannunga", "avoid pannunum", "vena nu solren", "vendam",
)
_SAFETY_VERDICT_TERMS = _SAFETY_VERDICT_TERMS + _SAFETY_VERDICT_TERMS_R22
_PROCEDURE_TERMS = (
    "x-ray", "xray", "scan", "ct ", "mri", "radiograph",
    "anaesthe", "anesthe", "sedation", "injection",
    "antibiotic", "prophylax", "painkiller", "tablet", "medicine", "dose",
    "drill", "scaler", "scaling", "cleaning", "extraction", "surgery",
    "root canal", "implant", "crown", "filling", "whitening", "braces",
    "treatment", "procedure",
)
# v22.0 FIX R22-C1 — gate 3 was 100% Latin, so it failed on 168 of 168 Tamil
# cases and 168 of 168 Hindi ones no matter what the other two gates said. Most
# dental procedure names in both languages are transliterations of the English,
# which is why the Latin list looked like it might carry them and does not:
# "\u0b8e\u0b95\u0bcd\u0bb8\u0bcd-\u0bb0\u0bc7" and "x-ray" share no characters. Native words are listed
# alongside the transliterations because patients and models use both.
# "\u0bae\u0bb0\u0bc1\u0ba8\u0bcd\u0ba4\u0bc1"/"\u0926\u0935\u093e" (medicine) and "\u0b9a\u0bbf\u0b95\u0bbf\u0b9a\u0bcd\u0b9a\u0bc8"/"\u0907\u0932\u093e\u091c" (treatment) are broad,
# and are included only because English already carries their exact twins
# ("medicine", "treatment"); the AND with the other two gates is what keeps them
# safe, and the control measurement at the fix is what proves it.
_PROCEDURE_TERMS_R22 = (
    # Tamil — transliterated
    "\u0b8e\u0b95\u0bcd\u0bb8\u0bcd-\u0bb0\u0bc7", "\u0b8e\u0b95\u0bcd\u0bb8\u0bcd \u0bb0\u0bc7", "\u0bb8\u0bcd\u0b95\u0bc7\u0bb2\u0bbf\u0b99\u0bcd", "\u0bb0\u0bc2\u0b9f\u0bcd \u0b95\u0bbe\u0bb2\u0bcd",
    "\u0b86\u0ba3\u0bcd\u0b9f\u0bbf\u0baa\u0baf\u0bbe\u0b9f\u0bbf\u0b95\u0bcd", "\u0b85\u0ba9\u0bb8\u0bcd\u0ba4\u0bc0\u0bb7\u0bbf\u0baf\u0bbe", "\u0b87\u0bae\u0bcd\u0baa\u0bcd\u0bb3\u0bbe\u0ba3\u0bcd\u0b9f\u0bcd",
    "\u0b95\u0bbf\u0bb0\u0bb5\u0bc1\u0ba9\u0bcd", "\u0baa\u0bcd\u0bb3\u0bc2\u0bb0\u0bc8\u0b9f\u0bcd", "\u0b9a\u0bcd\u0b95\u0bc7\u0ba9\u0bcd",
    # Tamil — native
    "\u0baa\u0bb2\u0bcd \u0baa\u0bbf\u0b9f\u0bc1\u0b99\u0bcd", "\u0baa\u0bbf\u0b9f\u0bc1\u0b99\u0bcd\u0b95", "\u0b9a\u0bbf\u0b95\u0bbf\u0b9a\u0bcd\u0b9a\u0bc8", "\u0b85\u0bb1\u0bc1\u0bb5\u0bc8 \u0b9a\u0bbf\u0b95\u0bbf",
    "\u0bae\u0baf\u0b95\u0bcd\u0b95 \u0bae\u0bb0\u0bc1\u0ba8\u0bcd\u0ba4\u0bc1", "\u0bae\u0bb0\u0bc1\u0ba8\u0bcd\u0ba4\u0bc1", "\u0b8a\u0b9a\u0bbf", "\u0bae\u0bbe\u0ba4\u0bcd\u0ba4\u0bbf\u0bb0\u0bc8",
    "\u0baa\u0bb2\u0bcd \u0b9a\u0bc1\u0ba4\u0bcd\u0ba4", "\u0bb5\u0bc6\u0bb3\u0bcd\u0bb3\u0bc8\u0baf\u0bbe\u0b95\u0bcd\u0b95",
    # Hindi — transliterated
    "\u090f\u0915\u094d\u0938-\u0930\u0947", "\u090f\u0915\u094d\u0938 \u0930\u0947", "\u0938\u094d\u0915\u0947\u0932\u093f\u0902\u0917", "\u0930\u0942\u091f \u0915\u0948\u0928\u093e\u0932",
    "\u090f\u0902\u091f\u0940\u092c\u093e\u092f\u094b\u091f\u093f\u0915", "\u090f\u0928\u0947\u0938\u094d\u0925\u0940\u0938\u093f\u092f\u093e", "\u0907\u092e\u094d\u092a\u094d\u0932\u093e\u0902\u091f",
    "\u0915\u094d\u0930\u093e\u0909\u0928", "\u092b\u093f\u0932\u093f\u0902\u0917", "\u0938\u094d\u0915\u0948\u0928", "\u0907\u0902\u091c\u0947\u0915\u094d\u0936\u0928",
    # Hindi — native
    "\u0926\u093e\u0901\u0924 \u0928\u093f\u0915\u093e\u0932", "\u0926\u093e\u0902\u0924 \u0928\u093f\u0915\u093e\u0932", "\u0938\u092b\u093e\u0908", "\u0907\u0932\u093e\u091c", "\u0938\u0930\u094d\u091c\u0930\u0940",
    "\u0926\u0935\u093e", "\u0917\u094b\u0932\u0940", "\u0938\u0941\u0908 \u0932\u0917",
)
_PROCEDURE_TERMS = _PROCEDURE_TERMS + _PROCEDURE_TERMS_R22
_CLINICAL_REFERRAL_LINES = {
    "en": ("I'm not able to advise whether that is safe in your situation — "
           "that depends on your full medical history and only the doctor can "
           "judge it. Please raise it with the doctor (and your specialist if "
           "you have one). I can book you a consultation so it's checked "
           "properly before anything is done."),
    "ta": ("\u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0ba8\u0bbf\u0bb2\u0bc8\u0bae\u0bc8\u0baf\u0bbf\u0bb2\u0bcd \u0b85\u0ba4\u0bc1 \u0baa\u0bbe\u0ba4\u0bc1\u0b95\u0bbe\u0baa\u0bbe\u0ba9\u0ba4\u0bbe \u0b8e\u0ba9\u0bcd\u0bb1\u0bc1 \u0b9a\u0bca\u0bb2\u0bcd\u0bb2 "
           "\u0b8e\u0ba9\u0b95\u0bcd\u0b95\u0bc1 \u0b85\u0ba4\u0bbf\u0b95\u0bbe\u0bb0\u0bae\u0bcd \u0b87\u0bb2\u0bcd\u0bb2\u0bc8 \u2014 \u0b85\u0ba4\u0bc1 \u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0bae\u0bc1\u0bb4\u0bc1 \u0bae\u0bb0\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1\u0bb5 \u0bb5\u0bb0\u0bb2\u0bbe\u0bb1\u0bcd\u0bb1\u0bc8\u0baa\u0bcd "
           "\u0baa\u0bca\u0bb1\u0bc1\u0ba4\u0bcd\u0ba4\u0ba4\u0bc1, \u0ba9\u0bbf\u0baa\u0bc1\u0ba3\u0bb0\u0bcd \u0bae\u0bb0\u0bc1\u0ba4\u0bcd\u0ba4\u0bb0\u0bcd \u0bae\u0b9f\u0bcd\u0b9f\u0bc1\u0bae\u0bc7 \u0bae\u0bc1\u0b9f\u0bbf\u0bb5\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0baf \u0bae\u0bc1\u0b9f\u0bbf\u0baf\u0bc1\u0bae\u0bcd. "
           "\u0ba4\u0baf\u0bb5\u0bc1\u0b9a\u0bc6\u0baf\u0bcd\u0ba4\u0bc1 \u0b87\u0ba4\u0bc8 \u0bae\u0bb0\u0bc1\u0ba4\u0bcd\u0ba4\u0bb0\u0bbf\u0b9f\u0bae\u0bcd \u0b95\u0bc7\u0b9f\u0bcd\u0b9f\u0bc1\u0b9a\u0bcd \u0b9a\u0bcb\u0bb2\u0bcd\u0bb2\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd. \u0bb5\u0bc7\u0ba3\u0bcd\u0b9f\u0bc1\u0bae\u0bc6\u0ba9\u0bcd\u0bb1\u0bbe\u0bb2\u0bcd "
           "consultation appointment book \u0baa\u0ba3\u0bcd\u0ba3\u0bbf\u0ba4\u0bcd \u0ba4\u0bb0\u0bc1\u0b95\u0bbf\u0bb1\u0bc7\u0ba9\u0bcd."),
    "hi": ("\u092e\u0948\u0902 \u092f\u0939 \u0928\u0939\u0940\u0902 \u092c\u0924\u093e \u0938\u0915\u0924\u093e \u0915\u093f \u0906\u092a\u0915\u0940 \u0938\u094d\u0925\u093f\u0924\u093f \u092e\u0947\u0902 \u092f\u0939 \u0938\u0941\u0930\u0915\u094d\u0937\u093f\u0924 \u0939\u0948 \u092f\u093e \u0928\u0939\u0940\u0902 \u2014 "
           "\u092f\u0939 \u0921\u0949\u0915\u094d\u091f\u0930 \u0939\u0940 \u0924\u092f \u0915\u0930 \u0938\u0915\u0924\u0947 \u0939\u0948\u0902\u0964 \u0915\u0943\u092a\u092f\u093e \u0921\u0949\u0915\u094d\u091f\u0930 \u0938\u0947 \u092a\u0942\u091b\u0947\u0902\u0964"),
}


# v33.0 · FIX R33-S1 — REGULATORY-CLAIM GUARD
# Fourth appearance of one class: the reply asserts a fact the system cannot
# back. R7/R15/R17 was WHO the clinic is, R8-C2 was an action that never
# happened, R14-C2 was a clinical verdict, and now R33-C1 is a legal one. The
# escalation law says stop patching instances at three; this is the control.
#
# Scope is deliberately narrow. It fires on DATA-PROTECTION frameworks — claims
# about how this SYSTEM handles data — and not on clinical accreditation, so a
# clinic that really is NABH accredited can still say so. And it stands down
# entirely when the clinic's OWN saved details contain the term: if the clinic
# put it there, the claim is the clinic's to make and the bot is only relaying
# it. Guarding the clinic's own words would be the R15/R16 mistake all over
# again — refusing ordinary, truthful sentences.
_REG_FRAMEWORKS = (
    "hipaa", "gdpr", "dpdp", "ccpa", "iso 27001", "iso27001", "soc 2", "soc2",
    "pci dss", "pci-dss", "hitech",
)
_REG_CLAIM_VERBS = (
    "compliant", "compliance", "complies", "certified", "certification",
    "accredited", "as per", "per the", "in accordance", "adheres", "adhering",
    "meets", "conforms", "regulated under", "\u0b9a\u0b9f\u0bcd\u0b9f\u0ba4\u0bcd\u0ba4\u0bbf\u0ba9\u0bcd\u0baa\u0b9f\u0bbf",
    "\u0bb5\u0bbf\u0ba4\u0bbf\u0bae\u0bc1\u0bb1\u0bc8", "\u0915\u0947 \u0905\u0928\u0941\u0938\u093e\u0930", "\u0905\u0928\u0941\u092a\u093e\u0932\u0928",
)
_REG_REFUSAL = {
    "en": "I can't speak for the clinic on legal or data-protection matters. "
          "Please ask the clinic directly and they'll answer it properly.",
    "ta": "\u0b9a\u0b9f\u0bcd\u0b9f \u0bb0\u0bc0\u0ba4\u0bbf\u0baf\u0bbe\u0ba9 \u0b85\u0bb2\u0bcd\u0bb2\u0ba4\u0bc1 \u0ba4\u0bb0\u0bb5\u0bc1 \u0baa\u0bbe\u0ba4\u0bc1\u0b95\u0bbe\u0baa\u0bcd\u0baa\u0bc1 \u0b95\u0bc7\u0bb3\u0bcd\u0bb5\u0bbf\u0b95\u0bb3\u0bc1\u0b95\u0bcd\u0b95\u0bc1 \u0ba8\u0bbe\u0ba9\u0bcd "
          "\u0baa\u0ba4\u0bbf\u0bb2\u0bb3\u0bbf\u0b95\u0bcd\u0b95 \u0bae\u0bc1\u0b9f\u0bbf\u0baf\u0bbe\u0ba4\u0bc1. \u0b95\u0bbf\u0bb3\u0bbf\u0ba9\u0bbf\u0b95\u0bcd\u0b95\u0bbf\u0b9f\u0bcd\u0b9f \u0ba8\u0bc7\u0bb0\u0b9f\u0bbf\u0baf\u0bbe\u0b95\u0bcd \u0b95\u0bc7\u0b9f\u0bcd\u0b9f\u0bbe\u0bb2\u0bcd "
          "\u0b9a\u0bb0\u0bbf\u0baf\u0bbe\u0ba9 \u0baa\u0ba4\u0bbf\u0bb2\u0bcd \u0b95\u0bbf\u0b9f\u0bc8\u0b95\u0bcd\u0b95\u0bc1\u0bae\u0bcd.",
    "hi": "\u092e\u0948\u0902 \u0915\u093e\u0928\u0942\u0928\u0940 \u092f\u093e \u0921\u0947\u091f\u093e-\u0938\u0941\u0930\u0915\u094d\u0937\u093e \u0938\u0902\u092c\u0902\u0927\u0940 \u092c\u093e\u0924\u094b\u0902 \u092a\u0930 \u0915\u094d\u0932\u093f\u0928\u093f\u0915 "
          "\u0915\u0940 \u0913\u0930 \u0938\u0947 \u0928\u0939\u0940\u0902 \u092c\u094b\u0932 \u0938\u0915\u0924\u093e\u0964 \u0915\u0943\u092a\u092f\u093e \u0938\u0940\u0927\u0947 \u0915\u094d\u0932\u093f\u0928\u093f\u0915 \u0938\u0947 \u092a\u0942\u091b\u0947\u0902\u0964",
}


def _guard_regulatory_claim(reply: str, brain: Dict) -> Tuple[str, bool]:
    """Refuse a reply that claims compliance with a data-protection framework.

    Returns (reply, blocked). Like every other guard here it REPLACES the reply
    rather than editing it — a half-corrected legal claim is still a legal
    claim."""
    low = (reply or "").lower()
    fw = next((f for f in _REG_FRAMEWORKS if f in low), None)
    if not fw:
        return reply, False
    if not any(v in low for v in _REG_CLAIM_VERBS):
        return reply, False
    # Stand down if the CLINIC itself put the term in its own details.
    #
    # v34.0 FIX R34-C1: this used to scan the whole system_prompt, which is
    # BUSINESS_TEMPLATES boilerplate plus the clinic's text. R33-C1 wrote the
    # new prohibition as "...not HIPAA, GDPR, DPDP, ISO or any other", so every
    # healthcare tenant's prompt contained all four names and this check stood
    # the guard down for ALL of them. The control was dead in exactly the
    # configuration it was built for, and the R33 tests missed it because they
    # used a stub brain ("You are a clinic receptionist.") instead of the real
    # template — a fixture that was not the production fixture, which is the
    # R29-H1 lesson repeating.
    #
    # R34 fixes it twice: the prohibition no longer names frameworks, AND the
    # boilerplate is subtracted here so a future prompt edit cannot re-disarm
    # the control. Only text the CLINIC supplied is consulted.
    _sp = str(brain.get("system_prompt", "") or "")
    for _tpl in BUSINESS_TEMPLATES.values():
        _base = _tpl.get("prompt", "")
        if _base and _base in _sp:
            _sp = _sp.replace(_base, " ")
    own = " ".join([_sp, str(brain.get("business_type", "") or ""),
                    str(brain.get("customer_name", "") or "")]).lower()
    if fw in own:
        return reply, False
    lang = "en"
    if any("\u0b80" <= c <= "\u0bff" for c in reply):
        lang = "ta"
    elif any("\u0900" <= c <= "\u097f" for c in reply):
        lang = "hi"
    log.warning(f"\U0001f6e1\ufe0f  R33-S1: regulatory claim refused ({fw!r}) \u2014 "
                f"the bot cannot certify the clinic under any law.")
    try:
        analytics.inc("guard.regulatory_claim")
    except Exception:
        pass
    return _REG_REFUSAL[lang], True


def _guard_clinical_safety_verdict(reply: str, brain: Dict, user_text: str,
                                   history: Optional[List[Dict]] = None
                                   ) -> Tuple[str, bool]:
    """Refuse a safety verdict about a procedure for a patient who disclosed a
    medical condition. Healthcare tenants only — a gym saying 'this workout is
    safe' is not practising medicine."""
    if not reply or not _brain_is_health(brain):
        return reply, False
    # v16.9 FIX R15-C3: the guard read ONLY the current message, so the most
    # natural way to ask defeated it — disclose the pregnancy in turn 2, ask
    # "x-ray ok va?" in turn 4, and by then no condition word is in user_text.
    # That is the exact R14 failure, still reachable, just one turn later. A
    # condition a patient disclosed does not stop being true because they moved
    # on, so the whole conversation is scanned.
    u = (user_text or "").lower()
    if history:
        # v17.0 FIX R16-C1: R15-C3 read _h["content"] — but get_session_history
        # emits the Gemini shape {"role":..., "parts":[text]}. Every lookup
        # returned None, so the "cross-turn" guard scanned an empty string and
        # the R14 hole stayed exactly as open as before. The code ran; it never
        # matched. Both shapes are read now, because the WhatsApp path and the
        # API path do not agree on one.
        for _h in history[-_SAFETY_HISTORY_MESSAGES:]:
            # R17-M1b: "human" was never written by anything here — handling a
            # shape that does not exist is what hid R15-C3 for a whole round.
            if (_h.get("role") or "") != "user":
                continue
            _txt = _h.get("content")
            if _txt is None:
                # R17-M1c: join every part, not just [0] — multi-part content
                # was silently truncated to its first fragment.
                _txt = " ".join(str(x) for x in (_h.get("parts") or []))
            u += " " + str(_txt or "").lower()
    r = reply.lower()
    if not any(t in u for t in _PATIENT_CONDITION_TERMS):
        return reply, False
    if not any(t in r for t in _SAFETY_VERDICT_TERMS):
        return reply, False
    if not any(t in r for t in _PROCEDURE_TERMS):
        return reply, False
    log.error("\U0001f6d1 R14-C2 clinical-safety guard: reply judged a procedure "
              "safe/unsafe for a disclosed condition \u2014 refused, not cached, "
              "not stored.")
    analytics.inc("guard.clinical_safety_block")
    lang = detect_language(user_text)
    return _CLINICAL_REFERRAL_LINES.get(lang, _CLINICAL_REFERRAL_LINES["en"]), True


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
    sys_prompt += (_LANGUAGE_RULE + _ESCALATION_RULE + _SCOPE_RULE
                   + _VENDOR_RULE + _INTEGRITY_RULE)    # R7-M1b / R8-L1 / R10-C2
    # v16.2 FIX R8-M1: observed 22-Jul \u2014 a pure-English "What is your root
    # canal fee?" got a Tamil reply because the standing rule competes with
    # the Tamil conversation history. Naming THIS turn's language explicitly
    # beats a general instruction the model has to infer against.
    _turn_lang = detect_language(user_text)
    sys_prompt += ("\n\nTHIS TURN: the user's message is in "
                   + {"ta": "Tamil", "hi": "Hindi"}.get(_turn_lang, "English")
                   + ". Reply in that same language, whatever earlier turns used.")
    sys_prompt += _time_context()

    reply, provider = multi_ai_reply(sys_prompt, history, user_text,
                                     plan_tier=str(brain.get("plan_tier") or ""))  # v15g2 FIX L1

    # v16.1 GEN-6 FIX R7-C1: check the model's output before anyone sees it.
    # v16.8 FIX R14-M1: every guard REPLACES the reply, and ESCALATE_TOKEN is
    # only looked for further down — so a model reply that both escalated AND
    # tripped a guard lost its escalation silently, and no human was ever
    # paged. The most dangerous replies are exactly the ones most likely to do
    # both. Remember the token first and restore it after.
    _wanted_escalation = ESCALATE_TOKEN in reply
    reply, _identity_blocked = _guard_clinic_identity(reply, brain, user_text)
    reply, _action_blocked = _guard_unbacked_action_claim(reply, user_text)  # R8-C2
    reply, _safety_blocked = _guard_clinical_safety_verdict(
        reply, brain, user_text, history)                 # R14-C2 / R15-C3
    reply, _reg_blocked = _guard_regulatory_claim(reply, brain)   # v33 R33-S1
    _identity_blocked = (_identity_blocked or _action_blocked
                         or _safety_blocked or _reg_blocked)
    if _identity_blocked and _wanted_escalation and ESCALATE_TOKEN not in reply:
        reply = ESCALATE_TOKEN + " " + reply

    escalated = ESCALATE_TOKEN in reply
    if escalated:
        reply = reply.replace(ESCALATE_TOKEN, "").strip() or \
                _HUMAN_LINES.get(detect_language(user_text), _HUMAN_LINES["en"])
        # v16.2 FIX R8-C1 (PATIENT SAFETY). Observed 22-Jul: "bleeding won't
        # stop, feeling faint" and "blood sugar 320" both escalated correctly
        # — and both replied with only the model's own calm sentence. The
        # KEYWORD emergency branch has carried 108/112 since v15g4 C11; this
        # branch never did, so the cases the keywords MISS (exactly the
        # nuanced ones the AI token exists to catch) got the weakest reply.
        # The line is conditional ("if this is a medical emergency"), so
        # appending it to a plain "let me talk to the doctor" is harmless
        # while a real crisis now always sees the number.
        _elang = detect_language(user_text)
        _eline = _EMERGENCY_LINES.get(_elang, _EMERGENCY_LINES["en"])
        _etail = _eline.split(". ", 1)[-1].strip()
        if _etail and _etail.lower() not in reply.lower():
            reply = reply.rstrip() + "\n\n" + _etail
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
        if (cacheable and provider != "cache" and not _identity_blocked
                and not _mentions_current_time(reply)):     # R7-M2
            resp_cache_put(_cache_hour_seed(base), cache_msg, reply)
        if channel != "api" and not _identity_blocked:        # v16g2 FIX M10 / R7-C1
            rag_store(brain.get("customer_id", ""), user_uid, user_text, reply)

    return reply, provider, escalated


# ─────────────────────────────────────────────────────────────────────────────
# 📐  PYDANTIC VALIDATION MODELS
# ─────────────────────────────────────────────────────────────────────────────
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
        return scrub_inbound(v)          # v16.3 FIX R9-C1


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


# ─────────────────────────────────────────────────────────────────────────────
# 💾  SQL HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _iso_utc(dt: datetime) -> str:
    """v16g4 FIX L17: THE canonical timestamp writer. Every stored timestamp
    funnels through here so the format can never drift between writers —
    string comparisons in SQL (outbox backoff, reminder scans, retention
    purge) silently mis-order the moment two formats coexist. Naive input is
    treated as UTC; output is always +00:00-suffixed ISO-8601. Readers use
    _parse_dt, which additionally tolerates a trailing Z."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def _now() -> str:
    return _iso_utc(datetime.now(timezone.utc))   # v16g4 FIX L17


def _iso_in(seconds: float) -> str:
    """v15g3 FIX 1: ISO-8601 UTC timestamp `seconds` from now — the outbox
    backoff schedule. Same format as _now(), so string comparison in SQL
    stays correct on both Postgres and SQLite."""
    return _iso_utc(datetime.now(timezone.utc)
                    + timedelta(seconds=seconds))   # v16g4 FIX L17


# ─────────────────────────────────────────────────────────────────────────────
# 🔕  v16g5 FIX R5-H4 — DURABLE OPT-OUT SUPPRESSION
#   Before this, a "STOP" flipped is_consented on whatever crm_contacts rows
#   _find_subject_rows happened to match — and nothing else. It did NOT mute
#   the AI, it did NOT stop appointment reminders (the reminder scanner reads
#   `bookings` and never looks at consent at all), and when the subject had no
#   matching CRM row — the common case for a BSUID patient whose row is keyed
#   on a hash of the BSUID — it wrote NOTHING while still replying "you've
#   been unsubscribed". Under DPDP that is telling a person you stopped and
#   then continuing to message them.
#   The suppression is stored in its own table, keyed by the same subject hash
#   the rest of the engine uses, and is consulted by every outbound initiator.
# ─────────────────────────────────────────────────────────────────────────────
def opt_out_subject(customer_id: str, subject: str) -> bool:
    """Record a durable opt-out. Returns True only when the row landed."""
    try:
        with _db_pool.get() as conn:
            _execute(conn,
                "INSERT INTO opt_outs (customer_id, subject_hash, created_at) "
                "VALUES (?,?,?)",
                (customer_id, _crm_phone_hash(customer_id, subject), _now()))
        brain_cache.set(f"optout:{customer_id}:{subject}", "1", ttl=86400)
        return True
    except Exception as exc:
        if _is_unique_violation(exc):        # already opted out — still success
            brain_cache.set(f"optout:{customer_id}:{subject}", "1", ttl=86400)
            return True
        log.error(f"❌ opt-out NOT recorded (cust={customer_id}): {exc}")
        analytics.inc("optout.write_failed")
        return False


def is_opted_out_checked(customer_id: str, subject: str) -> Tuple[bool, bool]:
    """v16g6 FIX R6-H9: returns (suppressed, known). Failing CLOSED is right
    for the SEND decision and catastrophic for a CONSUME decision — a caller
    that marks one-shot work done on the strength of a DB blip loses that
    work forever. Callers that consume leads must see the difference between
    'this subject is suppressed' and 'I could not find out'."""
    if not subject:
        return False, True
    ck = f"optout:{customer_id}:{subject}"
    cached = brain_cache.get(ck)
    if cached is not None:
        return (bool(cached) and cached != "0"), True
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT 1 FROM opt_outs WHERE customer_id=? AND subject_hash=? LIMIT 1",
                (customer_id, _crm_phone_hash(customer_id, subject)))
            hit = cur.fetchone() is not None
        brain_cache.set(ck, "1" if hit else "0", ttl=3600)
        return hit, True
    except Exception as exc:
        log.warning(f"⚠️  opt-out lookup failed (cust={customer_id}): {exc}")
        return True, False               # fail closed, and SAY it's a guess


# v17.0 R17-N1: DEAD as of R6 — the reminder scheduler was changed to a batch
# pre-filter and stopped calling this, and nothing replaced it. Left in place
# rather than deleted: it is correct, it is the obvious helper for a future
# per-subject check, and deleting working untested code mid-audit is how you
# introduce the next bug. Flagged so it is a decision, not an oversight.
def is_opted_out(customer_id: str, subject: str) -> bool:
    """True = never initiate an outbound to this subject again. Fails CLOSED
    on a cache miss + DB error: silence is the safe direction for consent.
    v16g6 FIX R6-H9: now a thin wrapper — consuming callers use
    is_opted_out_checked to tell suppression from lookup failure."""
    return is_opted_out_checked(customer_id, subject)[0]


def _wa_touch_window(customer_id: str, subject: str) -> None:
    """v16g5 FIX R5-H1 support: remember that this subject messaged US, which
    is what opens WhatsApp's 24-hour customer-service window for free text."""
    try:
        brain_cache.set(f"wawin:{customer_id}:{subject}", "1", ttl=24 * 3600)
    except Exception:
        pass


def _wa_in_service_window(customer_id: str, subject: str) -> bool:
    try:
        return bool(brain_cache.get(f"wawin:{customer_id}:{subject}"))
    except Exception:
        return False


def _is_unique_violation(exc: Exception) -> bool:
    """v16g4 FIX M11: four sites classified 'duplicate row' by sniffing the
    exception STRING for "unique"/"constraint"/"duplicate" — so a CHECK or
    FK/NOT NULL violation on Postgres ("violates check constraint …") was
    mis-read as a duplicate: booking_create answered 'slot just taken' to a
    data bug, create_admin_user answered 409 'Username already exists' to a
    schema problem. Use the drivers' real signals: pgcode 23505 (psycopg2)
    and sqlite3.IntegrityError whose message names UNIQUE."""
    if POSTGRES_AVAILABLE:
        try:
            if isinstance(exc, psycopg2.Error):
                # v20.0 R20-C2: 23P01 is exclusion_violation — what the new
                # bk_no_overlap constraint raises. Without it here, the
                # durable guard added in R20-C1 would surface as
                # booking.error and the patient would be told something went
                # wrong instead of "that time just went, here are the others".
                # A correct backstop that produces a wrong message is a
                # regression, not a fix.
                return getattr(exc, "pgcode", None) in ("23505", "23P01")
        except Exception:
            pass
    if isinstance(exc, sqlite3.IntegrityError):
        return "unique" in str(exc).lower()
    return False


def _execute(conn, sql: str, params: tuple = ()) -> Any:
    """Execute SQL — translates ? → %s for psycopg2 automatically.
    v15g4 FIX C4: the translation is a blind string replace — a future query
    containing a literal '%' (LIKE) or '?' inside a string would silently
    corrupt on Postgres. No current query does (audited); this guard makes
    sure the day one appears, it screams instead of corrupting."""
    is_pg = POSTGRES_AVAILABLE and isinstance(conn, psycopg2.extensions.connection)
    if is_pg:
        # v16g4 FIX HF1 (hotfix, 20-Jul): a literal '%' anywhere in the SQL
        # TEXT — including inside a SQL comment — was passed straight to
        # psycopg2's paramstyle parser after ?→%s translation, which then
        # expected MORE parameters than given: "IndexError: tuple index out
        # of range", a 500 on the live Tally webhook. The v15g4 C4 guard saw
        # it and LOGGED, but still executed the doomed statement. Now literal
        # % is escaped to %% FIRST (psycopg2 renders %% as a literal %), THEN
        # ? becomes %s — the whole bug class is gone, so the guard scream is
        # retired. House rule stands: parameters use ?, never raw %s.
        # v16g5 FIX R5-M7: HF1 fixed the `%` half of the C4 landmine and
        # RETIRED the guard — but `?`→`%s` is still a blind whole-string
        # replace, so a `?` inside a string literal or an identifier now
        # corrupts silently with nothing watching. Re-arm the scream for the
        # half that is still blind: count the `?` we are about to translate
        # and refuse to execute when it doesn't match the parameter count.
        # Count on the ORIGINAL sql: after %-escaping, a pattern like
        # LIKE '%stat%' would alias into a false "%s" hit.
        _holes = sql.count("?")
        _translated = sql.replace("%", "%%").replace("?", "%s")
        if _holes != len(params or ()):
            raise ValueError(
                f"SQL placeholder mismatch: {_holes} '?' translated but "
                f"{len(params or ())} parameter(s) supplied. A literal '?' "
                f"inside a string/identifier corrupts the ?→%s translation "
                f"(v16g5 FIX R5-M7). Offending SQL: {sql[:200]}")
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(_translated, params)
        if cur.description is None:
            # v16g4 FIX L15: INSERT/UPDATE/DDL produce no result set, yet the
            # cursor was returned open and lived until GC — loop-heavy paths
            # (erasure hash loop, outbox claim, migration backfill) piled up
            # dozens per connection. No caller can fetch from a result-less
            # cursor, and .rowcount stays readable after close (psycopg2), so
            # closing here is free. SELECT cursors must stay open for the
            # caller's fetch and are released with the connection.
            cur.close()
        return cur
    return conn.execute(sql, params)


def _db_true():
    """
    v12: portable truthy literal for WHERE clauses.
    PostgreSQL stores booleans natively (True); SQLite uses integer 1.
    Checks the live pool instance (not just driver availability) so it stays
    correct when psycopg2 is installed but DATABASE_URL is unset (SQLite mode).
    """
    return True if isinstance(_db_pool, PostgreSQLPool) else 1


# ─────────────────────────────────────────────────────────────────────────────
# 📋  SOC 2 AUDIT TRAIL  (v8 FIX #6)
# ─────────────────────────────────────────────────────────────────────────────
_AUDIT_DETAIL_MAX = 4000     # v16g5 FIX R5-L8


def audit(actor_id: str, action: str, resource: str,
          detail: Optional[Dict] = None, ip: Optional[str] = None) -> None:
    """Write an immutable audit record — async so it never blocks the request path.
    v14g3 BUG 14: was gated on ENABLE_ANALYTICS, so disabling metrics to cut DB
    load ALSO silently killed the SOC2/GDPR audit log. Now it has its own switch."""
    if not cfg.ENABLE_AUDIT:
        return

    def _write():
        try:
            # v16g5 FIX R5-L8: detail was json.dumps'd with NO size cap, so a
            # caller passing a large dict wrote an unbounded row into the one
            # table that must stay cheap to query.
            detail_str = json.dumps(detail or {})
            if len(detail_str) > _AUDIT_DETAIL_MAX:
                detail_str = json.dumps({
                    "_truncated": True,
                    "_original_bytes": len(detail_str),
                    "_head": detail_str[:_AUDIT_DETAIL_MAX]})
            with _db_pool.get() as conn:
                _execute(conn,
                    "INSERT INTO audit_log (ts, actor_id, action, resource, detail, ip, region) "
                    "VALUES (?,?,?,?,?,?,?)",
                    (_now(), actor_id, action, resource, detail_str, ip, cfg.REGION))
        except Exception as exc:
            log.warning(f"⚠️  Audit write failed: {exc}")

    # v16g6 FIX R6-M11: compliance writes went through the SAME
    # shed-on-saturation queue as analytics — under load the audit trail was
    # preferentially the first thing dropped (counted in bg.shed,
    # indistinguishable from a dropped metric). Admin actions are rare:
    # write synchronously; the bounded pool remains only as the fallback so
    # a slow DB cannot stall a webhook path that audits.
    try:
        _write()
    except Exception:
        submit_bg(_write)   # v11 #11: bounded pool


# ─────────────────────────────────────────────────────────────────────────────
# 📬  OUTBOX / SAGA PATTERN  (v8 FIX #3 — distributed transaction safety)
# ─────────────────────────────────────────────────────────────────────────────
def outbox_publish(event_type: str, payload: Dict) -> bool:
    """
    Transactional outbox pattern: events are persisted BEFORE external side-effects.
    A background worker processes pending events, guaranteeing at-least-once delivery.
    v12 #18: also kicks an immediate background drain so the welcome message and
    owner alerts go out in ~1s instead of waiting up to a full janitor cycle.
    v16g2 FIX M8: returns True only when the INSERT landed — the schedulers used
    to mark reminders_sent / followed_up_at on the ASSUMPTION the publish worked,
    so one DB hiccup during a tick lost messages forever AND recorded them sent.
    """
    try:
        # v16g6 FIX R6-C3: the outbox was the ONE store keeping patient
        # numbers in cleartext (crm_contacts and bookings both AES-GCM their
        # PII). Seal `to` at rest; the drain unseals just-in-time. encrypt()
        # is a no-op when the vault is disabled, so dev behaviour is
        # unchanged and no schema migration is needed.
        if payload.get("to"):
            payload = dict(payload, to=pii_vault.encrypt(str(payload["to"])))
        payload_str = json.dumps(payload)
        with _db_pool.get() as conn:
            _execute(conn,
                "INSERT INTO outbox (event_type, payload, status, created_at) VALUES (?,?,?,?)",
                (event_type, payload_str, "pending", _now()))
        # v16g6 FIX R6-L7: EVERY publish kicked its own drain — a burst of N
        # publishes produced N overlapping claim sweeps fighting over the
        # same rows (row-atomic, so pure wasted DB churn). One kick per 1s
        # window; the drain claims in batches of 20 and the janitor tick is
        # the backstop for anything landing inside the window.
        if brain_cache.setnx("outbox:kick", ttl=1):
            submit_bg(_process_outbox)   # v12 #18: drain now, not next tick
        return True
    except Exception as exc:
        log.error(f"❌ Outbox publish failed: {exc}")
        return False


def _claim_outbox_batch(limit: int = 20) -> List[Tuple]:
    """v12 #2/#44: atomically claim a batch of pending events. On Postgres,
    SELECT ... FOR UPDATE SKIP LOCKED guarantees two gunicorn workers can never
    grab the same row — so the welcome/alert message is sent exactly once, not
    once per worker. Rows are flipped to 'processing' inside the same locking
    transaction; slow sends then happen OUTSIDE the lock."""
    is_pg   = isinstance(_db_pool, PostgreSQLPool)
    claimed: List[Tuple] = []
    with _db_pool.get() as conn:
        if is_pg:
            # v15g3 FIX 1: only claim rows whose backoff window has elapsed.
            # COALESCE guards NULL (rows inserted before the column's DEFAULT
            # applied on some PG versions); '' compares less-than any ISO
            # timestamp, so legacy rows stay immediately eligible.
            cur = _execute(conn,
                "SELECT id, event_type, payload, attempts FROM outbox "
                "WHERE status='pending' AND attempts < 5 "
                "AND COALESCE(next_attempt_at,'') <= ? "
                "ORDER BY id LIMIT ? FOR UPDATE SKIP LOCKED", (_now(), limit))
            rows = cur.fetchall()
            ids  = [r["id"] for r in rows]
            if ids:
                # v15 FIX 7: stamp the CLAIM time so the janitor's stuck-row
                # requeue measures from when work started, not row creation.
                _execute(conn,
                    "UPDATE outbox SET status='processing', processed_at=? "
                    "WHERE id = ANY(?)", (_now(), ids))
        else:
            cur = _execute(conn,
                "SELECT id, event_type, payload, attempts FROM outbox "
                "WHERE status='pending' AND attempts < 5 "
                "AND COALESCE(next_attempt_at,'') <= ? "        # v15g3 FIX 1
                "ORDER BY id LIMIT ?", (_now(), limit))
            candidates = cur.fetchall()
            # v15g4 FIX B1: the old SELECT-then-UPDATE was not a claim — the
            # 20s janitor tick and the publish-time drain could BOTH read the
            # same pending rows before either flipped them, and each would
            # send (duplicate welcome/reminder messages). The UPDATE below is
            # conditional on status still being 'pending'; SQLite serialises
            # writes, so exactly ONE caller sees rowcount==1 per row. Postgres
            # already had this guarantee via FOR UPDATE SKIP LOCKED.
            rows = []
            for r in candidates:
                u = _execute(conn, "UPDATE outbox SET status='processing', "
                                   "processed_at=? WHERE id=? AND status='pending'",
                             (_now(), r["id"]))                 # v15 FIX 7 / v15g4 FIX B1
                if getattr(u, "rowcount", 1) == 1:
                    rows.append(r)
        claimed = [(r["id"], r["event_type"], r["payload"], r["attempts"]) for r in rows]
    return claimed


def _process_outbox() -> None:
    """Process a claimed batch. Claiming is atomic (see _claim_outbox_batch); the
    actual sends reuse the breaker + transient-retry path."""
    try:
        batch = _claim_outbox_batch(20)
    except Exception as exc:
        log.warning(f"⚠️  Outbox claim error: {exc}")
        return

    for evt_id, event_type, payload_raw, attempts in batch:
        try:
            # v15g2 FIX C1 (CRITICAL): on Postgres the payload column is JSONB and
            # psycopg2 auto-decodes it to a Python dict (default since 2.5.4) —
            # json.loads(dict) raised TypeError, so EVERY outbox event (welcome
            # messages, reminders, follow-ups) failed 5× and dead-lettered the
            # moment the engine ran on Postgres. SQLite (TEXT column) hid this.
            payload = payload_raw if isinstance(payload_raw, dict) \
                      else json.loads(payload_raw)
            # v16g6 FIX R6-C3: unseal the recipient written by outbox_publish.
            # Rows from pre-GEN-6 builds are untagged cleartext and pass
            # through decrypt() unchanged (the R5-C4 tag contract).
            _to0 = payload.get("to")
            if isinstance(_to0, str) and _to0.startswith("v1:"):
                payload["to"] = pii_vault.decrypt(_to0)
            if event_type == "whatsapp.send":
                # v14g3 BUG 9: route outbox sends through THIS clinic's OWN creds
                # (was always the GLOBAL number, so a multi-tenant welcome went
                # out from the wrong line or failed when global creds were unset).
                # A dead per-clinic token now flags needs_reauth and stops being
                # retried; transient errors still bubble up for outbox retry.
                cust = payload.get("customer_id", "")
                pid = tok = ""
                if cust:
                    _b = get_customer_brain(cust)
                    if _b:
                        pid, tok = brain_wa_creds(_b)
                try:
                    res = _whatsapp_breaker.call(
                        _meta_send_retry, _wa_send_text,
                        payload["to"], _to_whatsapp_markdown(payload["message"]),
                        pid, tok)
                    # v16g2 FIX H4: mirror the template branch's guard — a
                    # not_configured return is a SILENT non-send; without this
                    # it fell straight through to status='done', recording a
                    # never-sent welcome/reminder as delivered forever.
                    if isinstance(res, dict) and res.get("error"):
                        raise RuntimeError(
                            f"permanent: send not sent: {res.get('error')}")
                except WhatsAppAuthError as _ae:
                    _flag_channel_reauth(cust, f"outbox code={_ae.code}")
                    # v15g2 FIX M1: the message was NOT delivered — falling through
                    # to status='done' recorded a dead-token send as delivered
                    # forever (invisible in failed-row queries, never resent after
                    # the token is re-attached). Surface it as a permanent failure.
                    raise RuntimeError(
                        f"permanent: auth_dead: wa token code={_ae.code}")
            elif event_type == "whatsapp.template":
                # v14g4: scheduled sends (reminders / follow-ups) use an approved
                # template so they deliver OUTSIDE the 24-hour window. Same per-
                # tenant creds + token-death self-heal as whatsapp.send.
                cust = payload.get("customer_id", "")
                pid = tok = ""
                if cust:
                    _b = get_customer_brain(cust)
                    if _b:
                        pid, tok = brain_wa_creds(_b)
                try:
                    res = _whatsapp_breaker.call(
                        _meta_send_retry, _wa_send_template,
                        payload["to"], payload["template"],
                        payload.get("lang", "en"), payload.get("body_param", ""),
                        pid, tok)
                    if isinstance(res, dict) and res.get("error"):
                        raise RuntimeError(
                            f"permanent: template not sent: {res.get('error')}")
                except WhatsAppAuthError as _ae:
                    _flag_channel_reauth(cust, f"outbox tmpl code={_ae.code}")
                    raise RuntimeError(                            # v15g2 FIX M1
                        f"permanent: auth_dead: wa token code={_ae.code}")
            # Add more event types here as the system grows.
            with _db_pool.get() as conn:
                _execute(conn,
                    "UPDATE outbox SET status='done', processed_at=? WHERE id=?",
                    (_now(), evt_id))
        except Exception as exc:
            # v14g5 FIX 44: separate PERMANENT failures (misconfiguration, unknown
            # template, undeliverable recipient) from transient ones. Retrying a
            # permanent error five times only delays the dead-letter and spams the
            # logs — mark it failed on the first hit.
            _emsg = str(exc).lower()
            # v15g2 FIX M6: while the WhatsApp breaker is OPEN every drain pass
            # fast-fails without a single real send attempt — burning attempts
            # meant a ~5-tick outage could dead-letter perfectly good messages.
            # Put the row back to 'pending' with attempts UNCHANGED and move on.
            if "circuitbreaker" in _emsg and "open" in _emsg:
                # v15g3 FIX 1: attempts stay UNCHANGED (M6 discipline), but give
                # the row one tick of spacing — during breaker-open a burst of
                # publishes fired submit_bg drains that claimed + unclaimed the
                # same rows in a hot loop, hammering the DB for nothing.
                with _db_pool.get() as conn:
                    _execute(conn,
                        "UPDATE outbox SET status='pending', next_attempt_at=? "
                        "WHERE id=?", (_iso_in(20), evt_id))
                log.info(f"⏸️  Outbox event {evt_id} deferred — WhatsApp breaker open "
                         f"(attempt budget preserved).")
                continue
            # v16g6 FIX R6-M5: failures WE originate are tagged explicitly at
            # the raise site ("permanent: …") — a transient Meta 5xx whose
            # body happened to contain "not sent:" was dead-lettered on
            # attempt 1 by pure substring luck. Meta-body markers stay ONLY
            # as a fallback for errors we don't originate. (Same driver-
            # signals-over-sniffing discipline M11 applied to unique
            # violations.)
            _permanent = _emsg.startswith("permanent:") or any(m in _emsg for m in (
                "not_configured", "not configured", "does not exist",
                "unknown template", "invalid template", "template not found",
                "recipient not", "132001", "131026"))
            new_status = "failed" if (_permanent or attempts >= 4) else "pending"
            # v15g3 FIX 1 (HIGH): the old path retried a transient failure on the
            # very NEXT janitor tick (20s default — and instantly on every
            # submit_bg drain), burning all 5 attempts in ~80s. A routine 3-5min
            # Meta hiccup dead-lettered real patient reminders. Now each failure
            # pushes the row out on an exponential schedule — 30s → 60s → 120s →
            # 240s (+0-5s jitter so a batch doesn't retry as one thundering
            # herd) — stretching the attempt budget across ~7.5 minutes.
            _backoff = min(600.0, 30.0 * (2 ** attempts)) + random.uniform(0, 5)
            with _db_pool.get() as conn:
                _execute(conn,
                    "UPDATE outbox SET attempts=attempts+1, status=?, "
                    "next_attempt_at=? WHERE id=?",
                    (new_status, _iso_in(_backoff), evt_id))
            (log.error if _permanent else log.warning)(
                f"⚠️  Outbox event {evt_id} ({event_type}) "
                f"{'PERMANENT — not retrying' if _permanent else 'failed'}: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 💾  DATABASE OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────
def save_customer_brain(customer_id: str, customer_name: str,
                         business_type: str, system_prompt: str,
                         whatsapp_phone: str = "", owner_phone: str = "",
                         instagram_id: str = "", bot_name: str = "") -> None:
    now   = _now()
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    # v16g2 FIX N5: ? placeholders (_execute translates). v16g4 FIX HF2: the
    # N5 note used to live INSIDE the SQL string as a `--` comment — and the
    # note's own "%s"/"%-guard" text was the literal '%' that blew up the
    # first real Postgres run of this INSERT (see FIX HF1). Commentary lives
    # in Python now; SQL strings carry SQL only.
    if is_pg:
        sql = """
            INSERT INTO customer_brains
                (customer_id, customer_name, business_type, system_prompt,
                 created_at, updated_at, whatsapp_phone, region,
                 owner_phone, instagram_id, bot_name)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT (customer_id) DO UPDATE SET
                customer_name  = EXCLUDED.customer_name,
                business_type  = EXCLUDED.business_type,
                system_prompt  = EXCLUDED.system_prompt,
                updated_at     = EXCLUDED.updated_at,
                is_active      = TRUE,
                whatsapp_phone = EXCLUDED.whatsapp_phone,
                owner_phone    = EXCLUDED.owner_phone,
                instagram_id   = EXCLUDED.instagram_id,
                bot_name       = EXCLUDED.bot_name
        """
    else:
        sql = """
            INSERT INTO customer_brains
                (customer_id, customer_name, business_type, system_prompt,
                 created_at, updated_at, whatsapp_phone, region,
                 owner_phone, instagram_id, bot_name)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(customer_id) DO UPDATE SET
                customer_name  = excluded.customer_name,
                business_type  = excluded.business_type,
                system_prompt  = excluded.system_prompt,
                updated_at     = excluded.updated_at,
                is_active      = 1,
                whatsapp_phone = excluded.whatsapp_phone,
                owner_phone    = excluded.owner_phone,
                instagram_id   = excluded.instagram_id,
                bot_name       = excluded.bot_name
        """
    # v16g6 FIX R6-M2: every PATIENT number is AES-GCM'd; the clinic owner's
    # personal mobile — the emergency-escalation target — sat plaintext in
    # Postgres AND in the Redis brain cache. Seal it at rest; callers get it
    # back through _brain_unseal in the fetchers. Legacy plaintext rows pass
    # through decrypt() unchanged (tag contract) — no migration required.
    with _db_pool.get() as conn:
        _execute(conn, sql, (customer_id, customer_name, business_type,
                             system_prompt, now, now, whatsapp_phone, cfg.REGION,
                             pii_vault.encrypt(owner_phone or ""),
                             instagram_id, bot_name))
    brain_cache.delete(f"brain:{customer_id}")    # v16g6 FIX R6-L6
    try:
        # v16g6 FIX R6-L15: a clinic that edits its prompt kept the OLD
        # per-prompt Gemini client cached until LRU aging evicted it — 64
        # full system prompts held strongly on a 512MB dyno. Brain updates
        # are rare; clearing the factory outright is cheap and exact.
        _gemini_model.cache_clear()
    except Exception:
        pass
    analytics.inc("customer.saved")
    log.info(f"💾 Brain saved → {customer_id}")


def _brain_unseal(b: Dict) -> Dict:
    """v16g6 FIX R6-M2: caller-facing COPY with owner_phone decrypted. The
    cache keeps the sealed form (Redis included); legacy plaintext passes
    through decrypt() unchanged; unreadable ciphertext degrades to '' (no
    alert target) rather than leaking garbage into a send."""
    if not b:
        return b
    out = dict(b)
    out["owner_phone"] = pii_vault.decrypt(out.get("owner_phone") or "")
    if out["owner_phone"] == "[ENCRYPTED]":
        out["owner_phone"] = ""
    return out


def get_customer_brain(customer_id: str) -> Optional[Dict]:
    cached = brain_cache.get(f"brain:{customer_id}")   # v16g6 FIX R6-L6:
    # every other key in the file is namespaced (wapid:, igid:, ghost:,
    # resp:, optout:, wawin:) — the bare id meant delete_prefix could never
    # target brains, and any same-string key would collide.
    if cached:
        analytics.inc("cache.hit")
        return _brain_unseal(cached)              # v16g6 FIX R6-M2
    analytics.inc("cache.miss")
    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn,
            "SELECT * FROM customer_brains WHERE customer_id=? AND is_active=?",
            (customer_id, True if isinstance(_db_pool, PostgreSQLPool) else 1))
        row = cur.fetchone()
    if row:
        data = dict(row)
        brain_cache.set(f"brain:{customer_id}", data)   # sealed form · R6-L6
        return _brain_unseal(data)                # v16g6 FIX R6-M2
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 🧭  v13 TRUE MULTI-TENANT ROUTING  — which clinic owns the business number?
# ─────────────────────────────────────────────────────────────────────────────
def get_brain_by_wa_phone_id(phone_number_id: str) -> Optional[Dict]:
    """v13: find the clinic that OWNS the WhatsApp business line that received a
    message. This is the correct routing key (Meta's value.metadata.phone_number_id),
    not the sender's number. Cached per phone_number_id; channel edits bust it."""
    if not phone_number_id:
        return None
    ckey   = f"wapid:{phone_number_id}"
    cached = brain_cache.get(ckey)
    if cached:
        return _brain_unseal(cached) if cached != "__none__" else None   # R6-M2
    try:
        with _db_pool.get(read_only=True) as conn:
            if not _column_exists(conn, "customer_brains", "wa_phone_number_id"):
                return None  # pre-v13 DB — caller falls back to single-tenant route
            cur = _execute(conn,
                "SELECT * FROM customer_brains "
                "WHERE wa_phone_number_id=? AND is_active=?",
                (phone_number_id, _db_true()))
            row = cur.fetchone()
        if row:
            data = dict(row)
            brain_cache.set(ckey, data, ttl=cfg.ROUTE_CACHE_TTL)
            return _brain_unseal(data)               # v16g6 FIX R6-M2
        brain_cache.set(ckey, "__none__", ttl=60)   # cache the miss briefly
    except Exception as exc:
        log.warning(f"⚠️  wa_phone_id route lookup failed: {exc}")
    return None


def get_brain_by_ig_id(ig_account_id: str) -> Optional[Dict]:
    """v13: route an Instagram DM to the clinic that owns the IG business account
    that received it (the webhook recipient.id). Cached, miss-cached briefly."""
    if not ig_account_id:
        return None
    ckey   = f"igid:{ig_account_id}"
    cached = brain_cache.get(ckey)
    if cached:
        return _brain_unseal(cached) if cached != "__none__" else None   # R6-M2
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT * FROM customer_brains "
                "WHERE instagram_id=? AND is_active=?",
                (ig_account_id, _db_true()))
            row = cur.fetchone()
        if row:
            data = dict(row)
            brain_cache.set(ckey, data, ttl=cfg.ROUTE_CACHE_TTL)
            return _brain_unseal(data)               # v16g6 FIX R6-M2
        brain_cache.set(ckey, "__none__", ttl=60)
    except Exception as exc:
        log.warning(f"⚠️  ig_id route lookup failed: {exc}")
    return None


def brain_wa_creds(brain: Dict) -> Tuple[str, str]:
    """v13: THIS clinic's own (phone_id, token). Falls back to the GLOBAL env
    creds so your FIRST clinic and any pre-v13 setup keep working with zero extra
    config. v16g6 FIX R6-C6: a clinic that OWNS a phone_id but has no usable
    token gets ('','') — send disabled, reauth flagged — never the global
    pair. The global fallback is reserved for brains with no
    wa_phone_number_id at all."""
    pid_own = (brain.get("wa_phone_number_id") or "").strip()
    enc = (brain.get("wa_token_enc") or "").strip()
    tok_own = (pii_vault.decrypt(enc) if enc else "")
    if tok_own == "[ENCRYPTED]":
        # v16g2 FIX M6: decrypt failure returned the truthy sentinel, so the
        # global fallback never fired — one ENCRYPTION_KEY typo dark-flagged
        # the ENTIRE fleet with 401s instead of falling back to global creds.
        tok_own = ""
    if pid_own and tok_own:
        return pid_own, tok_own
    # v16g4 FIX H7: creds fall back AS A PAIR. The old per-field fallback
    # could return (clinic's phone_id, GLOBAL token) — or the reverse — a
    # cross-WABA pair that Meta always 401/403s, which then false-flagged
    # needs_reauth on what was a CONFIG problem, not a dead token.
    if pid_own and not tok_own:
        # v16g6 FIX R6-C6: routing REACHED this brain via its own
        # wa_phone_number_id — the clinic provably owns the line the patient
        # wrote to. H7's global-pair fallback here replied from a DIFFERENT
        # WhatsApp business identity, so the answer never appears in the
        # thread the patient used (your number, or Clinic A's, answers
        # Clinic B's patient). The safe failure is NO send + a loud reauth
        # flag — never someone else's number.
        log.error(f"❌ clinic {brain.get('customer_id','?')} owns phone_id "
                  f"{pid_own} but has NO usable token — sends DISABLED for "
                  f"this clinic until the token is re-attached via "
                  f"/admin/customer/<id>/channel (v16g6 FIX R6-C6).")
        try:
            _flag_channel_reauth(brain.get("customer_id", ""),
                                 "wa token unreadable/missing")
        except Exception:
            pass
        return "", ""
    elif tok_own and not pid_own:
        log.warning(f"⚠️  clinic {brain.get('customer_id','?')} has a token "
                    f"but NO phone_id — falling back to the GLOBAL pair "
                    f"(v16g4 FIX H7).")
    return cfg.WHATSAPP_PHONE_ID, cfg.WHATSAPP_TOKEN


def brain_ig_creds(brain: Dict) -> Tuple[str, str]:
    """v13: THIS clinic's own (ig_account_id, ig_token), global env fallback."""
    igid = (brain.get("instagram_id") or "").strip() or cfg.INSTAGRAM_ID
    enc  = (brain.get("ig_token_enc") or "").strip()
    tok  = (pii_vault.decrypt(enc) if enc else "")
    if tok == "[ENCRYPTED]":
        tok = ""                                    # v16g2 FIX M6 (IG twin)
    tok  = tok or cfg.INSTAGRAM_TOKEN
    return igid, tok


def create_session(customer_id: str, channel: str = "api", subject_hash: str = "") -> str:
    session_id = f"sess_{uuid.uuid4().hex[:20]}"
    now = _now()
    with _db_pool.get() as conn:
        _execute(conn,
            "INSERT INTO chat_sessions (session_id, customer_id, created_at, last_active, channel, subject_hash) "
            "VALUES (?,?,?,?,?,?)",
            (session_id, customer_id, now, now, channel, subject_hash))
    analytics.inc("session.created")
    return session_id


def session_exists(session_id: str, customer_id: str) -> bool:
    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn,
            "SELECT 1 FROM chat_sessions WHERE session_id=? AND customer_id=?",
            (session_id, customer_id))
        return cur.fetchone() is not None


def _find_session_by_subject(customer_id: str, subject_hash: str) -> Optional[str]:
    """v15g2 FIX M3: resume the subject's most recent session from the DB when
    the 1-hour cache mapping has expired — an ACTIVE conversation no longer gets
    total amnesia at the 60-minute mark. Cheap: hits idx_sess_subject (FIX 3)."""
    if not subject_hash:
        return None
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT session_id FROM chat_sessions "
                "WHERE customer_id=? AND subject_hash=? "
                "ORDER BY last_active DESC LIMIT 1",
                (customer_id, subject_hash))
            r = cur.fetchone()
            return r["session_id"] if r else None
    except Exception:
        return None


def save_messages_batch(session_id: str, turns: List[Tuple[str, str, str, int]]) -> None:
    """Save (role, content, ai_provider, latency_ms) tuples in one transaction."""
    now   = _now()
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    sql = (
        "INSERT INTO chat_messages "
        "(session_id, role, content, timestamp, token_estimate, ai_provider, latency_ms) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s)" if is_pg else
        "INSERT INTO chat_messages "
        "(session_id, role, content, timestamp, token_estimate, ai_provider, latency_ms) "
        "VALUES (?,?,?,?,?,?,?)"
    )
    # v16g4 FIX L20: len(split()) undercounts Indic scripts ~2× (Tamil words
    # are long, agglutinative, and sub-word tokenized) — any future context
    # budgeting on this column would over-stuff history for Tamil chats.
    # Heuristic: ~4 chars/token for ASCII, ~2 chars/token for non-ASCII.
    def _token_estimate(_c: str) -> int:
        _a = sum(1 for ch in _c if ord(ch) < 128)
        return max(len(_c.split()), (_a + 3) // 4 + (len(_c) - _a + 1) // 2)
    rows = [(session_id, role, content, now, _token_estimate(content), provider, latency)
            for role, content, provider, latency in turns]
    with _db_pool.get() as conn:
        if is_pg:
            # v16g6 FIX R6-M12: the inline cursor was never closed — one
            # leaked cursor per saved chat turn, the exact pattern R5-L4
            # hunted down in init_db; it survived because executemany
            # bypasses _execute, where the closing lives. R6-M13: the
            # hand-built %s SQL above bypasses the placeholder guard for the
            # same reason — it stays (executemany has no _execute path) but
            # is now confined to this one audited, commented site.
            _mcur = conn.cursor()
            try:
                _mcur.executemany(sql, rows)
            finally:
                _mcur.close()
        else:
            conn.executemany(sql, rows)
        # v16g2 FIX N5: one dialect-neutral UPDATE through _execute — the old
        # Postgres branch carried literal %s, tripping the v15g4-C4 %-guard
        # into a spurious 🛑 ERROR log on EVERY saved chat turn (the hottest
        # write path), drowning real errors the day the Postgres migration
        # lands.
        _execute(conn,
            "UPDATE chat_sessions SET last_active=?, message_count=message_count+? "
            "WHERE session_id=?",
            (now, len(turns), session_id))
    analytics.inc("message.saved", len(turns))


def get_session_history(session_id: str) -> List[Dict]:
    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn,
            "SELECT role, content FROM chat_messages "
            "WHERE session_id=? ORDER BY id DESC LIMIT ?",
            (session_id, cfg.CHAT_HISTORY_LIMIT))
        rows = cur.fetchall()
    hist = [{"role": r["role"], "parts": [r["content"]]} for r in reversed(rows)]
    # v12 #21: the LIMIT window can slice off the first user turn and leave the
    # history starting with a 'model' turn. Gemini's start_chat REQUIRES the
    # history to begin with a user turn (and to alternate) or it raises. Drop any
    # leading model turns so the window always starts clean.
    while hist and hist[0]["role"] == "model":
        hist.pop(0)
    return hist


def log_webhook(source_ip: str, payload_hash: str, customer_id: Optional[str],
                status: str, channel: str = "tally", error: Optional[str] = None) -> None:
    with _db_pool.get() as conn:
        _execute(conn,
            "INSERT INTO webhook_log "
            "(source_ip, payload_hash, customer_id, channel, status, error_detail, processed_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (source_ip, payload_hash, customer_id, channel, status, error, _now()))


def increment_chat_count(customer_id: str) -> None:
    with _db_pool.get() as conn:
        # v16g2 FIX L15: updated_at is no longer bumped per message — it made
        # tenants_health's needs_reauth "since" show the last patient message
        # instead of when the token actually died.
        _execute(conn,
            "UPDATE customer_brains SET total_chats=total_chats+1 "
            "WHERE customer_id=?",
            (customer_id,))
    # v15 FIX 23: this used to brain_cache.delete(customer_id) on EVERY message,
    # forcing a fresh DB read of the brain per turn — the cache never lived
    # longer than one message. total_chats in cached stats may now lag up to
    # CACHE_TTL (≤10 min); the live COUNT(*) queries in /stats are unaffected.
    analytics.inc("chat.total")


def check_idempotency(key: str) -> Optional[Dict]:
    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn, "SELECT response_body FROM idempotency_keys WHERE key=?", (key,))
        row = cur.fetchone()
    if not row:
        return None
    try:
        return json.loads(row["response_body"])
    except Exception:
        # v16g3 FIX R3-L9: one corrupt stored body used to 500 the DUPLICATE
        # path of the Tally webhook. Unreadable body = cache miss.
        log.warning(f"⚠️  idempotency body unreadable for {key[:12]} — miss.")
        return None


def store_idempotency(key: str, response: Dict) -> bool:
    """v15g4 FIX C7: now returns True on a durable write (or the harmless
    duplicate-race). False means the idempotency record was NOT stored — a
    Tally retry arriving after the 120s claim lock expires would replay the
    whole flow (duplicate welcome message). The caller logs that loudly."""
    with _db_pool.get() as conn:
        try:
            _execute(conn,
                "INSERT INTO idempotency_keys (key, response_body, created_at) VALUES (?,?,?)",
                (key, json.dumps(response), _now()))
            return True
        except Exception as exc:
            # v14g5 FIX 33 + v15 FIX 15: a duplicate-key race is the expected,
            # harmless case → DEBUG. Everything else (serialization failure,
            # full disk) was invisible at the default INFO level — now WARNING.
            _is_dup = _is_unique_violation(exc)   # v16g4 FIX M11
            (log.debug if _is_dup else log.warning)(
                f"idempotency store skipped for {key}: {exc}")
            return _is_dup


# ─────────────────────────────────────────────────────────────────────────────
# 📋  ENCRYPTED CRM
# ─────────────────────────────────────────────────────────────────────────────
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


def crm_add_contact(customer_id: str, name: str, phone: str,
                     email: str = "", notes: str = "",
                     stage: str = "lead", is_consented: bool = False,
                     wa_user_id: str = "") -> int:   # v16 U1
    now         = _now()
    phash       = _crm_phone_hash(customer_id, phone)
    is_pg       = isinstance(_db_pool, PostgreSQLPool)
    wa_user_id  = (wa_user_id or "").strip()

    # v11 #3: was a blind INSERT on EVERY message → 10 messages = 10 duplicate
    # rows. Now: same lead → just bump updated_at and return the existing id.
    with _db_pool.get() as conn:
        _has_uid_col = _column_exists(conn, "crm_contacts", "wa_user_id")
        cur = _execute(conn,
            ("SELECT id, updated_at, wa_user_id, enc_name FROM crm_contacts "
             if _has_uid_col else
             "SELECT id, updated_at, enc_name FROM crm_contacts ")
            + "WHERE customer_id=? AND phone_hash=?",
            (customer_id, phash))
        row = cur.fetchone()
        if row:
            # v16 U1: BACKFILL — existing patients (rows created before V16, or
            # matched by phone) get their BSUID attached the next time they
            # message, so the Meta Contact-Book mapping is mirrored locally.
            _uid_changed = bool(_has_uid_col and wa_user_id and (
                    (row["wa_user_id"] or "") != wa_user_id))
            # v16g4 port (audit item 221): a patient's WhatsApp/IG display name
            # can change (marriage, typo fix, new phone) but the CRM kept the
            # FIRST name forever. Refresh enc_name when the caller passed a
            # REAL captured name (not the "WA/IG <masked>" placeholder callers
            # use when no profile name is available) and it actually differs.
            _new_name = (name or "").strip()
            _is_placeholder = bool(re.match(r"^(WA|IG)\s", _new_name))
            _name_changed = False
            if _new_name and not _is_placeholder:
                try:
                    _cur_name = pii_vault.decrypt(row["enc_name"] or "")
                except Exception:
                    _cur_name = ""
                if _cur_name in ("", "[ENCRYPTED]") or _cur_name != _new_name:
                    _name_changed = True
            if _uid_changed or _name_changed:
                # v16g2 FIX L8 (BSUID self-heal) + name refresh, one UPDATE.
                sets, vals2 = ["updated_at=?"], [now]
                if _uid_changed:
                    sets.append("wa_user_id=?"); vals2.append(wa_user_id)
                if _name_changed:
                    sets.append("enc_name=?"); vals2.append(pii_vault.encrypt(_new_name))
                vals2.append(row["id"])
                _execute(conn,
                    f"UPDATE crm_contacts SET {', '.join(sets)} WHERE id=?",
                    tuple(vals2))
                if _uid_changed:
                    analytics.inc("crm.contact.bsuid_backfilled")
                if _name_changed:
                    analytics.inc("crm.contact.name_refreshed")
                return row["id"]
            # v15g4 FIX D3: the touch itself was a write on EVERY message —
            # needless SQLite write-lock pressure. Throttle to one bump per
            # 10 min per contact; any parse hiccup falls back to bumping.
            fresh = False
            try:
                ua = row["updated_at"]
                ua_dt = ua if isinstance(ua, datetime) else \
                        datetime.fromisoformat(str(ua).replace(" ", "T"))
                if ua_dt.tzinfo is None:
                    ua_dt = ua_dt.replace(tzinfo=timezone.utc)
                fresh = (datetime.now(timezone.utc) - ua_dt) < timedelta(seconds=600)
            except Exception:
                fresh = False
            if not fresh:
                _execute(conn,
                    "UPDATE crm_contacts SET updated_at=? WHERE id=?",
                    (now, row["id"]))
                analytics.inc("crm.contact.touched")
            return row["id"]

        enc_name    = pii_vault.encrypt(name)
        enc_phone   = pii_vault.encrypt(phone)
        enc_email   = pii_vault.encrypt(email) if email else ""
        enc_notes   = pii_vault.encrypt(notes) if notes else ""
        consent_val = is_consented if is_pg else int(is_consented)
        if _has_uid_col:                                   # v16 U1
            cols = ("INSERT INTO crm_contacts "
                    "(customer_id, phone_hash, enc_name, enc_phone, enc_email, enc_notes, "
                    "contact_stage, created_at, updated_at, is_consented, wa_user_id) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)")
            vals = (customer_id, phash, enc_name, enc_phone, enc_email, enc_notes,
                    stage, now, now, consent_val, wa_user_id)
        else:
            cols = ("INSERT INTO crm_contacts "
                    "(customer_id, phone_hash, enc_name, enc_phone, enc_email, enc_notes, "
                    "contact_stage, created_at, updated_at, is_consented) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)")
            vals = (customer_id, phash, enc_name, enc_phone, enc_email, enc_notes,
                    stage, now, now, consent_val)
        if is_pg:
            # v13 BUGFIX: psycopg2 cursor.lastrowid is 0 for normal tables, so the
            # API previously returned contact_id=0 for every new Postgres contact.
            # RETURNING id gives the real primary key.
            insert_sql = cols + " RETURNING id"
        else:
            insert_sql = cols
        _race_lost = False
        try:
            cur = _execute(conn, insert_sql, vals)
            if is_pg:
                picked = cur.fetchone()
                new_id = (picked["id"] if picked else None)
            else:
                new_id = cur.lastrowid if hasattr(cur, "lastrowid") else None
        except Exception:
            # v14g3 BUG 10: lost the insert race against the unique dedupe index
            # (uq_crm_dedupe — another worker just created this same lead).
            # v16g6 FIX R6-M4: the recovery lookup used to open a SECOND
            # pooled connection while STILL HOLDING the first — the only
            # nested _db_pool.get() in the file. Ten concurrent threads in
            # this branch deadlocked a pool_size=10 SQLite pool into
            # "SQLite pool exhausted" after the 5s timeout. Release the
            # insert connection first; recover on a fresh one below.
            new_id = None
            _race_lost = True

    if _race_lost:
        try:
            with _db_pool.get(read_only=True) as conn2:
                c2 = _execute(conn2,
                    "SELECT id FROM crm_contacts WHERE customer_id=? AND phone_hash=?",
                    (customer_id, phash))
                r2 = c2.fetchone()
                new_id = r2["id"] if r2 else None
        except Exception:
            new_id = None
        analytics.inc("crm.contact.race_merged")
        return new_id or 0

    analytics.inc("crm.contact.added")
    log.info(f"📋 CRM contact → customer={customer_id} phone={pii_vault.mask(phone)}")
    return new_id or 0


# ─────────────────────────────────────────────────────────────────────────────
# 🆔  v16 — USERNAMES / BSUID HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def crm_attach_phone(customer_id: str, chat_id: str, real_phone: str) -> bool:
    """v16 U3: a username patient (BSUID identity) shared their real number —
    store it in enc_phone on THEIR EXISTING row. Identity continuity is the
    whole point: phone_hash stays keyed on the BSUID (sessions, bookings, and
    dedupe all keep working), the real number rides alongside for reminders
    and clinic records."""
    # v16g2 FIX N2: canonicalise EXACTLY like the Tally intake does — a patient
    # typing "98765 43210" the natural way (nobody types +91) gets
    # DEFAULT_COUNTRY_CODE prepended, so the number the scheduler later hands
    # to Meta's `to` is actually deliverable instead of dead-lettering after
    # we PROMISED "reminders to ****3210". Floor raised 7→10: a 7-digit
    # landline was never a valid WhatsApp recipient.
    digits = _normalize_msisdn(real_phone or "")
    if len(digits) < 10:
        return False
    phash = _crm_phone_hash(customer_id, chat_id)
    try:
        with _db_pool.get() as conn:
            cur = _execute(conn,
                "UPDATE crm_contacts SET enc_phone=?, updated_at=? "
                "WHERE customer_id=? AND phone_hash=?",
                (pii_vault.encrypt(digits), _now(), customer_id, phash))
            ok = getattr(cur, "rowcount", 0) > 0
            # v16g3 FIX R3-M6: a patient who messaged from this NUMBER in the
            # pre-username era already has a phone-keyed row; capturing the
            # same number onto the BSUID row left TWO live rows for one
            # person (double follow-ups — the unique dedupe index can't fire
            # across different hashes). Merge, N3-style: carry consent over,
            # retire the old row, and re-key its bookings + sessions onto the
            # BSUID identity so history unifies.
            old_hash = _crm_phone_hash(customer_id, digits)
            if ok and old_hash != phash:
                cur = _execute(conn,
                    "SELECT id, is_consented, enc_notes, enc_email, "
                    "contact_stage, created_at FROM crm_contacts "
                    "WHERE customer_id=? AND phone_hash=?",
                    (customer_id, old_hash))
                _dup = cur.fetchone()
                if _dup:
                    # v16g6 FIX R6-M3: the merge kept ONLY is_consented — the
                    # retired row's notes, email, stage and original
                    # created_at were destroyed with it. Fold them into the
                    # survivor (fill-if-empty; notes concatenate; earliest
                    # created_at wins) BEFORE the delete, same transaction.
                    _sv = _execute(conn,
                        "SELECT id, enc_notes, enc_email, contact_stage, "
                        "created_at FROM crm_contacts "
                        "WHERE customer_id=? AND phone_hash=?",
                        (customer_id, phash)).fetchone()
                    if _sv:
                        def _dec(v):
                            _x = pii_vault.decrypt(v or "")
                            return "" if _x == "[ENCRYPTED]" else _x
                        _sets, _vals = [], []
                        _dn, _sn = _dec(_dup["enc_notes"]), _dec(_sv["enc_notes"])
                        if _dn and _dn not in _sn:
                            _sets.append("enc_notes=?")
                            _vals.append(pii_vault.encrypt(
                                (_sn + "\n" + _dn).strip() if _sn else _dn))
                        if _dec(_dup["enc_email"]) and not _dec(_sv["enc_email"]):
                            _sets.append("enc_email=?")
                            _vals.append(_dup["enc_email"])
                        if ((_dup["contact_stage"] or "") not in ("", "lead")
                                and (_sv["contact_stage"] or "lead") == "lead"):
                            _sets.append("contact_stage=?")
                            _vals.append(_dup["contact_stage"])
                        if ((_dup["created_at"] or "") and
                                str(_dup["created_at"]) < str(_sv["created_at"] or "9999")):
                            _sets.append("created_at=?")
                            _vals.append(_dup["created_at"])
                        if _sets:
                            _vals.append(_sv["id"])
                            _execute(conn,
                                f"UPDATE crm_contacts SET {', '.join(_sets)} "
                                f"WHERE id=?", tuple(_vals))
                    if _dup["is_consented"]:
                        _execute(conn,
                            "UPDATE crm_contacts SET is_consented=? "
                            "WHERE customer_id=? AND phone_hash=?",
                            (_db_true(), customer_id, phash))
                    _execute(conn, "DELETE FROM crm_contacts WHERE id=?",
                             (_dup["id"],))
                    # v16g6 FIX R6-M3: re-key EVERY booking — the old
                    # status='booked' filter orphaned cancelled/completed
                    # history from the surviving identity (and from erasure).
                    _execute(conn,
                        "UPDATE bookings SET phone_hash=? "
                        "WHERE customer_id=? AND phone_hash=?",
                        (phash, customer_id, old_hash))
                    _execute(conn,
                        "UPDATE chat_sessions SET subject_hash=? "
                        "WHERE customer_id=? AND subject_hash=?",
                        (phash, customer_id, old_hash))
                    analytics.inc("crm.identity_merged")
                    log.info(f"🆔 U3 capture: merged pre-username row for "
                             f"{pii_vault.mask(digits)} into the BSUID row.")
        if ok:
            brain_cache.delete(f"wa_session:{customer_id}:{digits}")  # old-spelling map
            brain_cache.set(f"realphone:{customer_id}:{chat_id}", digits,
                            ttl=86400 * 30)
            analytics.inc("crm.phone_captured")
            audit("system", "crm.phone_captured", customer_id,
                  {"chat_id_tail": chat_id[-8:], "phone": pii_vault.mask(digits)}, "")
        return ok
    except Exception as exc:
        log.warning(f"⚠️  crm_attach_phone failed: {exc}")
        return False


def crm_get_real_phone(customer_id: str, chat_id: str) -> str:
    """v16 U3: the captured real number for a BSUID conversation, '' if none.
    Cache-first (30d), DB fallback via the BSUID-keyed row's enc_phone."""
    cached = brain_cache.get(f"realphone:{customer_id}:{chat_id}")
    if cached:
        return str(cached)
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT enc_phone FROM crm_contacts "
                "WHERE customer_id=? AND phone_hash=? LIMIT 1",
                (customer_id, _crm_phone_hash(customer_id, chat_id)))
            row = cur.fetchone()
        if not row:
            return ""
        dec = pii_vault.decrypt(row["enc_phone"] or "")
        if dec and dec != "[ENCRYPTED]" and not _is_bsuid(dec) \
                and len(re.sub(r"\D", "", dec)) >= 7:
            brain_cache.set(f"realphone:{customer_id}:{chat_id}", dec, ttl=86400 * 30)
            return dec
    except Exception as exc:
        log.warning(f"⚠️  crm_get_real_phone failed: {exc}")
    return ""


def _resolve_send_addr(customer_id: str, addr: str) -> str:
    """v16 U3: outbound resolver for scheduler paths. If the stored recipient
    is a BSUID and the patient has since shared a real number, prefer the
    number (keeps working even if the BSUID lapses, and matches what the
    clinic has on record). Otherwise send to the BSUID — Meta's 'Send to
    BSUID' delivers to username patients directly. Plain phones pass through."""
    if not _is_bsuid(addr):
        return addr
    return crm_get_real_phone(customer_id, addr) or addr


def crm_remap_user_id(customer_id: str, old_id: str, new_id: str) -> int:
    """v16 U5: Meta regenerates a patient's BSUID when they change their phone
    number and announces it via a `user_id_update` system webhook. Without
    this remap the patient's next message arrives under an unknown identity —
    history, bookings, and captured phone all orphan. Re-key the CRM row, any
    upcoming bookings, AND the chat sessions from the old hash to the new one.
    v16g2 FIX N3: Meta guarantees NO cross-type ordering — if the patient's
    first post-change message beat the system event, crm_add_contact already
    created a stub row under the NEW hash, and the old UPDATE then hit
    uq_crm_dedupe and rolled the WHOLE remap back (identity split forever,
    bookings stranded). The stub is now merged (deleted) first.
    v16g2 FIX N4: for a classic user_changed_number (new id is a PHONE), the
    remap now also refreshes enc_phone — reminders stop dialling the dead
    SIM — and no longer writes a phone number into the BSUID column.
    v16g2 FIX M3: chat_sessions.subject_hash is re-keyed in the same
    transaction, and the old wa_session / numreq cache keys are dropped, so
    the patient's next message resumes the SAME session with full AI context —
    the header's "history never orphans" promise is finally true."""
    if not (old_id and new_id) or old_id == new_id:
        return 0
    old_hash = _crm_phone_hash(customer_id, old_id)
    new_hash = _crm_phone_hash(customer_id, new_id)
    changed  = 0
    try:
        with _db_pool.get() as conn:
            has_uid = _column_exists(conn, "crm_contacts", "wa_user_id")
            # v16g2 FIX N3: merge a pre-existing stub under the new identity so
            # the re-key below can never violate uq_crm_dedupe.
            cur = _execute(conn,
                "SELECT id FROM crm_contacts WHERE customer_id=? AND phone_hash=?",
                (customer_id, new_hash))
            _stub = cur.fetchone()
            if _stub:
                _execute(conn, "DELETE FROM crm_contacts WHERE id=?", (_stub["id"],))
                log.info(f"🆔 user_id_update: merged stub row id={_stub['id']} "
                         f"created under the new identity before the event.")
            if _is_bsuid(new_id):
                if has_uid:
                    cur = _execute(conn,
                        "UPDATE crm_contacts SET wa_user_id=?, phone_hash=?, updated_at=? "
                        "WHERE customer_id=? AND phone_hash=?",
                        (new_id, new_hash, _now(), customer_id, old_hash))
                else:
                    cur = _execute(conn,
                        "UPDATE crm_contacts SET phone_hash=?, updated_at=? "
                        "WHERE customer_id=? AND phone_hash=?",
                        (new_hash, _now(), customer_id, old_hash))
            else:
                # v16g2 FIX N4: classic number change — refresh the number the
                # scheduler will actually dial; leave wa_user_id untouched.
                _nd = _normalize_msisdn(new_id) or re.sub(r"\D", "", new_id)
                cur = _execute(conn,
                    "UPDATE crm_contacts SET phone_hash=?, enc_phone=?, updated_at=? "
                    "WHERE customer_id=? AND phone_hash=?",
                    (new_hash, pii_vault.encrypt(_nd), _now(),
                     customer_id, old_hash))
            changed += getattr(cur, "rowcount", 0) or 0
            cur = _execute(conn,
                "UPDATE bookings SET phone_hash=? "
                "WHERE customer_id=? AND phone_hash=? AND status='booked'",
                (new_hash, customer_id, old_hash))
            changed += getattr(cur, "rowcount", 0) or 0
            cur = _execute(conn,                              # v16g2 FIX M3
                "UPDATE chat_sessions SET subject_hash=? "
                "WHERE customer_id=? AND subject_hash=?",
                (new_hash, customer_id, old_hash))
            changed += getattr(cur, "rowcount", 0) or 0
        brain_cache.delete(f"realphone:{customer_id}:{old_id}")
        brain_cache.delete(f"wa_session:{customer_id}:{old_id}")   # v16g2 FIX M3
        for _k in ("numreq", "numreq_asked", "numreq_window", "numreq_inflight"):
            brain_cache.delete(f"{_k}:{customer_id}:{old_id}")     # v16g2 FIX M3
        audit("system", "crm.user_id_remap", customer_id,
              {"old_tail": old_id[-8:], "new_tail": new_id[-8:],
               "rows": changed}, "")
        analytics.inc("crm.user_id_remapped")
        log.info(f"🆔 user_id_update: remapped …{old_id[-8:]} → …{new_id[-8:]} "
                 f"({changed} rows) for {customer_id}")
    except Exception as exc:
        log.warning(f"⚠️  crm_remap_user_id failed: {exc}")
    return changed


_PHONE_LIKE_RE = re.compile(r"(?:\+?\d[\d\s\-().]{6,18}\d)")


def _extract_phone_like(text: str) -> str:
    """v16 U3: pull a typed phone number out of a chat message ('my number is
    98765 43210'). Returns normalised digits or ''. ≥10 digits required for a
    confident capture (Indian mobiles), ≤15 per E.164."""
    m = _PHONE_LIKE_RE.search(text or "")
    if not m:
        return ""
    digits = re.sub(r"\D", "", m.group(0))
    if not (10 <= len(digits) <= 15):
        return ""
    # v16g3 FIX R3-M2: inside the 15-min ask window a typed 12-digit AADHAAR
    # sailed through the length gate and became "their phone" — reminders
    # promised to a government ID. Plausibility: a bare 10-digit Indian mobile
    # starts 6-9; longer strings must start with the country code (and then a
    # 6-9 mobile digit) or be written in explicit +intl form, which we trust.
    if len(digits) == 10:
        return digits if digits[0] in "6789" else ""
    _cc = cfg.DEFAULT_COUNTRY_CODE
    if (digits.startswith(_cc) and len(digits) > len(_cc)
            and digits[len(_cc)] in "6789"):
        return digits
    if m.group(0).strip().startswith("+"):
        return digits
    return ""


def crm_list_contacts(customer_id: str, stage: Optional[str] = None,
                       page: int = 1, per_page: int = 50) -> Tuple[List[Dict], int]:
    offset       = (page - 1) * per_page
    stage_filter = "AND contact_stage=?" if stage else ""
    params_count = (customer_id,) + ((stage,) if stage else ())
    params_data  = params_count + (per_page, offset)

    with _db_pool.get(read_only=True) as conn:
        cur_total = _execute(conn,
            f"SELECT COUNT(*) as cnt FROM crm_contacts WHERE customer_id=? {stage_filter}",
            params_count)
        _trow = cur_total.fetchone()
        # v15 FIX 2 (CRITICAL): sqlite3.Row has NO .get() method — the old
        # `(fetchone() or {}).get("cnt", 0)` raised AttributeError on SQLite,
        # 500-ing GET /crm/contacts on the current deployment. Index access
        # works on both sqlite3.Row and psycopg2's RealDictRow.
        total = (_trow["cnt"] if _trow else 0) or 0
        cur_data = _execute(conn,
            f"SELECT id, enc_name, enc_phone, enc_email, enc_notes, "
            f"contact_stage, created_at, is_consented "
            f"FROM crm_contacts WHERE customer_id=? {stage_filter} "
            f"ORDER BY id DESC LIMIT ? OFFSET ?",
            params_data)
        rows = cur_data.fetchall()

    # v16g4 FIX L16: role-tiered PII. Only the phone was masked for viewers —
    # names, emails and free-text notes (which regularly hold health context:
    # "asked about root canal pricing") went out in clear to the lowest role.
    _u = getattr(g, "jwt_user", None) or {}
    _viewer_only = (_ROLE_RANK.get(_u.get("role", "viewer"), 0)
                    < _ROLE_RANK.get("admin", 1))
    def _p(v):   # viewer → masked
        return pii_vault.mask(v) if _viewer_only else v
    contacts = [{
        "id":            r["id"],
        "name":          _p(pii_vault.decrypt(r["enc_name"])),
        "phone":         pii_vault.mask(pii_vault.decrypt(r["enc_phone"])),
        "email":         _p(pii_vault.decrypt(r["enc_email"]) if r["enc_email"] else ""),
        "notes":         ("[restricted]" if (_viewer_only and r["enc_notes"]) else
                          (pii_vault.decrypt(r["enc_notes"]) if r["enc_notes"] else "")),
        "contact_stage": r["contact_stage"],
        "created_at":    str(r["created_at"]),
        "is_consented":  bool(r["is_consented"]),
    } for r in rows]
    return contacts, total


def crm_get_contact_full(contact_id: int, customer_id: str = "") -> Optional[Dict]:
    """v14g5 FIX 4 (IDOR): when customer_id is supplied the lookup is scoped to that
    tenant, so a clinic enumerating /crm/contact/<id> can never read another
    clinic's PII. An empty customer_id (superadmin) keeps the unscoped lookup."""
    with _db_pool.get(read_only=True) as conn:
        if customer_id:
            cur = _execute(conn,
                "SELECT * FROM crm_contacts WHERE id=? AND customer_id=?",
                (contact_id, customer_id))
        else:
            cur = _execute(conn, "SELECT * FROM crm_contacts WHERE id=?", (contact_id,))
        row = cur.fetchone()
    if not row:
        return None
    return {
        "id":            row["id"],
        "customer_id":   row["customer_id"],
        "name":          pii_vault.decrypt(row["enc_name"]),
        "phone":         pii_vault.decrypt(row["enc_phone"]),
        "email":         pii_vault.decrypt(row["enc_email"]) if row["enc_email"] else "",
        "notes":         pii_vault.decrypt(row["enc_notes"]) if row["enc_notes"] else "",
        "contact_stage": row["contact_stage"],
        "created_at":    str(row["created_at"]),
        "is_consented":  bool(row["is_consented"]),
    }


# ═════════════════════════════════════════════════════════════════════════════
# 📅  v14 GEN-4 — APPOINTMENT BOOKING ENGINE  (flag: ENABLE_BOOKING, default OFF)
#   v15g2 FIX L3 (honesty): business hours are GLOBAL env config
#   (BOOKING_OPEN_HOUR / BOOKING_CLOSE_HOUR / BOOKING_WEEKDAYS) — every clinic
#   shares one set. True per-tenant hours need a schema column and belong to the
#   multi-clinic milestone, not this file. Only BOOKINGS are stored (slot
#   availability is computed, so there's no slot table to seed).
#   A deterministic per-conversation state machine drives book / reschedule /
#   cancel / status — no fragile LLM tool-loop, so behaviour is predictable.
# ═════════════════════════════════════════════════════════════════════════════
def _parse_dt(s: str) -> datetime:
    """Parse an ISO timestamp to an aware UTC datetime (tolerates a trailing Z)."""
    s = (s or "").strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_local(dt_or_iso) -> datetime:
    # v14g5 FIX 25: return a NAIVE local wall-clock datetime (was tagged UTC while
    # carrying local numbers — misleading if ever reused in tz-aware math).
    dt = dt_or_iso if isinstance(dt_or_iso, datetime) else _parse_dt(dt_or_iso)
    return (dt + timedelta(minutes=cfg.BOOKING_TZ_OFFSET_MIN)).replace(tzinfo=None)


def _fmt_local_dt(s) -> str:
    return _to_local(s).strftime("%a %d %b, %I:%M %p")


def _fmt_local_time_range(s, e) -> str:
    return _to_local(s).strftime("%I:%M %p") + "–" + _to_local(e).strftime("%I:%M %p")


def booking_available_slots(customer_id: str, limit: int) -> List[Tuple[datetime, datetime]]:
    """Return the next `limit` open slots (as aware-UTC (start,end) tuples),
    computed from business-hours config minus slots already booked. At least
    60 minutes in the future so nobody books a slot that's basically now."""
    step    = max(5, cfg.BOOKING_SLOT_MINUTES)
    open_m  = cfg.BOOKING_OPEN_HOUR * 60
    close_m = cfg.BOOKING_CLOSE_HOUR * 60
    wkdays  = {int(x) for x in cfg.BOOKING_WEEKDAYS.split(",")
               if x.strip().isdigit() and 0 <= int(x.strip()) <= 6}
    # v16g5 FIX R5-M5: a typo'd BOOKING_WEEKDAYS ("Mon,Tue") produced an EMPTY
    # weekday set and this function returned [] forever — the patient just saw
    # "no slots available", with nothing anywhere saying why. Same for an
    # inverted OPEN/CLOSE hour. Fail LOUD (hourly-throttled) instead of dark.
    # v16g6 FIX R6-L5: BOOKING_CLOSE_HOUR=25 sailed past this guard and blew
    # up later at d_loc.replace(hour=…) — an uncaught ValueError out of the
    # offer builder, straight into handle_booking. Clamp to the calendar
    # first; the loud guard below still catches a nonsensical clamped range.
    open_m  = min(max(open_m, 0), 24 * 60)
    close_m = min(max(close_m, 0), 24 * 60)
    if not wkdays or open_m + step > close_m:
        if brain_cache.setnx("warn:booking_cfg", ttl=3600):
            log.critical(
                f"🛑 BOOKING MISCONFIGURED — no slot can ever be offered. "
                f"BOOKING_WEEKDAYS={cfg.BOOKING_WEEKDAYS!r} parsed to {sorted(wkdays)} "
                f"(expects digits 0-6, Mon=0), OPEN_HOUR={cfg.BOOKING_OPEN_HOUR} "
                f"CLOSE_HOUR={cfg.BOOKING_CLOSE_HOUR} SLOT_MINUTES={step}.")
        analytics.inc("booking.misconfigured")
        return []
    # v16g6 R6-L13 (documented limitation): a FIXED minute offset is correct
    # for IST (+330, no DST — the launch market) and WRONG for any DST
    # region: this naive wall-clock drifts ±60min across transitions.
    # Before selling outside fixed-offset zones, replace
    # BOOKING_TZ_OFFSET_MIN with a per-clinic IANA zone via zoneinfo.
    off     = timedelta(minutes=cfg.BOOKING_TZ_OFFSET_MIN)
    now_utc = datetime.now(timezone.utc)
    now_loc = (now_utc + off).replace(tzinfo=None)        # naive local wall-clock

    booked: set = set()
    try:
        with _db_pool.get(read_only=True) as conn:
            # v16g4 FIX P5: also bound ABOVE — the offer builder only looks
            # BOOKING_DAYS_AHEAD out, but the scan fetched every future booked
            # row to the end of time (a clinic with months of forward bookings
            # paid for all of them on every offer).
            _horizon = (now_utc + timedelta(days=cfg.BOOKING_DAYS_AHEAD + 1)).isoformat()
            # v16g5 FIX R5-H3: widen the lower bound by one slot length so a
            # booking that STARTED before `now` but still RUNS INTO the
            # offerable window is seen by the overlap test.
            _floor = (now_utc - timedelta(minutes=step * 4)).isoformat()
            cur = _execute(conn,
                "SELECT slot_start, slot_end FROM bookings WHERE customer_id=? "
                "AND status='booked' AND slot_start >= ? AND slot_start < ?",
                (customer_id, _floor, _horizon))
            # v14g5 FIX 38: key booked slots by canonical epoch-second, not raw ISO
            # string, so dedupe survives any future formatting drift (Z vs +00:00).
            # v16g5 FIX R5-H3: carry the END of each booking too. Exact-start
            # equality alone meant a booking that did not sit on the CURRENT
            # grid blocked nothing: change BOOKING_SLOT_MINUTES 30→20 and the
            # engine happily offered 14:00–14:20 while 14:00–14:30 was taken,
            # and the unique index (on slot_start) could not catch the 14:20
            # collision either. Two patients, one chair.
            for r in cur.fetchall():
                _bs = int(_parse_dt(r["slot_start"]).timestamp())
                try:
                    _be = int(_parse_dt(r["slot_end"]).timestamp())
                except Exception:
                    _be = _bs + step * 60
                booked.add((_bs, max(_be, _bs + 1)))
    except Exception as exc:
        log.warning(f"⚠️  booking slot scan failed: {exc}")

    out: List[Tuple[datetime, datetime]] = []
    for day in range(0, cfg.BOOKING_DAYS_AHEAD + 1):
        d_loc = now_loc + timedelta(days=day)
        if d_loc.weekday() not in wkdays:
            continue
        m = open_m
        while m + step <= close_m:
            hh, mm = divmod(m, 60)
            m += step
            local_naive = d_loc.replace(hour=hh, minute=mm, second=0, microsecond=0)
            start_utc   = (local_naive - off).replace(tzinfo=timezone.utc)
            if start_utc <= now_utc + timedelta(minutes=60):
                continue
            # v16g5 FIX R5-H3: true half-open interval overlap
            # (a.start < b.end AND a.end > b.start), not start equality.
            _cs = int(start_utc.timestamp())
            _ce = _cs + step * 60
            if any(_cs < _be and _ce > _bs for _bs, _be in booked):
                continue
            out.append((start_utc, start_utc + timedelta(minutes=step)))
            if len(out) >= limit:
                return out
    return out


def booking_active_count_for_phone(customer_id: str, phone: str,
                                   exclude_id=None) -> int:
    """How many upcoming slots this number already holds at this clinic.
    exclude_id lets a RESCHEDULE ignore the slot it is about to replace —
    without it, a patient at the cap could never move their appointment."""
    phash   = _crm_phone_hash(customer_id, phone)
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with _db_pool.get(read_only=True) as conn:
            if exclude_id:
                cur = _execute(conn,
                    "SELECT COUNT(*) FROM bookings WHERE customer_id=? AND "
                    "phone_hash=? AND status='booked' AND slot_start >= ? AND id != ?",
                    (customer_id, phash, now_iso, exclude_id))
            else:
                cur = _execute(conn,
                    "SELECT COUNT(*) FROM bookings WHERE customer_id=? AND "
                    "phone_hash=? AND status='booked' AND slot_start >= ?",
                    (customer_id, phash, now_iso))
            row = cur.fetchone()
            return int(row[0]) if row else 0
    except Exception as exc:
        # v16.6 R12-H1: fail OPEN. A counting outage must not stop a real
        # patient from booking — the cap exists to blunt a nuisance, not to
        # gate care. The overlap guard below still prevents double-booked slots.
        log.warning(f"\u26a0\ufe0f  active-booking count failed (cust={customer_id}): {exc}")
        return 0


def booking_create(customer_id: str, phone: str, name: str,
                   start_iso: str, end_iso: str, source: str = "whatsapp",
                   replacing_id=None) -> str:
    """Insert a booking. Returns 'ok' | 'conflict' | 'limit' | 'error'.
    v15g2 FIX L5: EVERY exception used to be reported as a slot conflict, so a
    DB outage told the patient 'sorry, that slot was just taken'. A unique-index
    violation (uq_book_slot, the race-safe guard) is 'conflict'; anything else
    is an infrastructure 'error' and is logged loudly. ('ok' stays truthy, so
    any legacy truthiness check keeps working.)"""
    # v16.6 FIX R12-H1: audited 26-Jul — ONE number could hold unlimited
    # slots. booking_create never counted, and handle_booking only looked for
    # an existing appointment on a RESCHEDULE, so repeating "book pannunga"
    # just handed out another slot every time. A single number could take a
    # clinic's whole day. The cap lives here, at the DB chokepoint every path
    # funnels through, so no future caller can bypass it by accident.
    _held = booking_active_count_for_phone(customer_id, phone,
                                           exclude_id=replacing_id)
    if _held >= cfg.MAX_ACTIVE_BOOKINGS_PER_PHONE:
        analytics.inc("booking.limit_blocked")
        log.info(f"\U0001f6d1 booking cap hit (cust={customer_id}, "
                 f"holds={_held}, cap={cfg.MAX_ACTIVE_BOOKINGS_PER_PHONE})")
        return "limit"
    phash = _crm_phone_hash(customer_id, phone)
    now   = _now()
    try:
        with _db_pool.get() as conn:
            # v16g6 FIX R6-C4: R5-H3 fixed interval overlap in the OFFER
            # builder only. uq_book_slot indexes slot_start EQUALITY, so after
            # a BOOKING_SLOT_MINUTES change a 14:00–14:30 row cannot block a
            # 14:20 insert — the exact scenario the R5-H3 comment names is
            # still committable from a stale offer. Re-verify half-open
            # overlap INSIDE the insert transaction (ISO-8601 UTC strings
            # compare lexicographically = chronologically). The durable DB
            # guarantee — tstzrange EXCLUDE USING gist — belongs to the next
            # migration slot; this closes the stale-offer window portably on
            # both engines today.
            _c = _execute(conn,
                "SELECT 1 FROM bookings WHERE customer_id=? AND "
                "status='booked' AND slot_start < ? AND slot_end > ? LIMIT 1",
                (customer_id, end_iso, start_iso))
            if _c.fetchone():
                analytics.inc("booking.slot_conflict")
                log.info(f"📅 booking overlap conflict (cust={customer_id})")
                return "conflict"
            _execute(conn,
                "INSERT INTO bookings (customer_id, phone_hash, enc_phone, enc_name, "
                "slot_start, slot_end, status, reminders_sent, source, created_at, updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (customer_id, phash, pii_vault.encrypt(phone), pii_vault.encrypt(name or ""),
                 start_iso, end_iso, "booked", "", source, now, now))
        analytics.inc("booking.created")
        return "ok"
    except Exception as exc:
        if _is_unique_violation(exc):             # v16g4 FIX M11
            analytics.inc("booking.slot_conflict")
            log.info(f"📅 booking slot conflict (cust={customer_id})")
            return "conflict"
        analytics.inc("booking.error")
        log.error(f"❌ booking insert failed (cust={customer_id}): {exc}")
        return "error"


def booking_upcoming_for_phone(customer_id: str, phone: str) -> Optional[Dict]:
    phash   = _crm_phone_hash(customer_id, phone)
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT id, slot_start, slot_end FROM bookings WHERE customer_id=? "
                "AND phone_hash=? AND status='booked' AND slot_start >= ? "
                "ORDER BY slot_start ASC LIMIT 1", (customer_id, phash, now_iso))
            r = cur.fetchone()
            return dict(r) if r else None
    except Exception:
        return None


# v15g2: booking_cancel_upcoming() removed — orphaned by the FIX C2b
# confirmation flow (lookup via booking_upcoming_for_phone, destruction only
# via booking_cancel_by_id after an explicit YES). No other callers existed.


def booking_cancel_by_id(booking_id) -> bool:
    """v14g5 FIX 12: cancel one specific booking by id — used by reschedule, but
    only AFTER the replacement slot has been secured.
    v16g4 FIX M5: swallowed failure used to return NOTHING and every caller
    printed "✅ Cancelled" unconditionally — a DB blip mid-cancel told the
    patient it was cancelled while the row stayed booked (and on reschedule
    they could end up holding two slots). Now returns True only when a row
    actually transitioned booked→cancelled."""
    try:
        with _db_pool.get() as conn:
            cur = _execute(conn, "UPDATE bookings SET status='cancelled', updated_at=? "
                                 "WHERE id=? AND status='booked'", (_now(), booking_id))
            changed = (getattr(cur, "rowcount", -1) or 0) > 0
        if changed:
            analytics.inc("booking.cancelled")
        return changed
    except Exception as exc:
        log.warning(f"⚠️  booking cancel-by-id failed: {exc}")
        analytics.inc("booking.cancel_failed")
        return False


# v16g3 FIX R3-H2: two-tier intent vocabulary. STRONG words alone mean the
# patient wants a slot. The old flat list let WEAK time/consult vocabulary
# hijack informational questions — "what is the vaccination schedule for my
# baby", "fees for consult", "what are your timings" all got a slot list
# instead of an answer. WEAK words now fire only beside a booking-context cue
# ("is the doctor available", "checkup tomorrow" still book); everything else
# falls through to the AI, which actually answers the question.
_BOOK_WORDS_STRONG = ("book", "appointment", "appointments", "appoint",
                      "booking", "bookings", "slot", "slots", "reserve",
                      "appointment venum", "varalama")
_BOOK_WORDS_WEAK   = ("schedule", "available", "availability", "timing",
                      "timings", "consult", "checkup", "check-up", "neram",
                      "milna", "samay", "dikhana")
_BOOK_CONTEXT      = ("appointment", "book", "slot", "visit", "doctor", "dr",
                      "clinic", "tomorrow", "today", "when", "free", "time")

# ── v24.0 · FIX R24-C1 (BOOKING — a Tamil or Hindi patient could not BOOK) ────
# R23 restored cancel, reschedule and status for Indic patients and never asked
# the prior question. The Rule 8 runtime census asked it: _BOOK_WORDS is 23
# entries, 22 English and 1 Thanglish — zero Tamil, zero Devanagari. So the
# product's PRIMARY function was unavailable in both of its launch market's
# scripts, and had been through twenty-three audit rounds.
#
# Measured by execution over 28 realistic booking requests, 7 per language:
#
#     en  6/7        tg  5/7        ta  0/7        hi  0/7      overall 11/28 (39%)
#
# Driven to the outcome (Rule 10), not to the gate:
#     [EN] provider='booking'  slots offered: True
#     [TA] provider=None       slots offered: False   -> "AI unavailable"
#     [HI] provider=None       slots offered: False   -> "AI unavailable"
# The message falls through to an AI that has no booking tools, so a patient
# asking for an appointment in Tamil receives a conversational reply and no slot
# list, forever. Fails CLOSED (Rule 9): nothing logs, no detector fires, and the
# clinic simply never hears from that patient again.
#
# Rule 2 — isolated before believing it. _kw_hit works correctly on Indic input
# (verified against a Tamil cancel keyword on the same text), and
# _BOOK_WORDS contains no Indic entry at all. The list, not the matcher.
#
# Two structural notes that shaped the fix:
#  - detect_booking_intent tests reschedule -> cancel -> status -> book, so book
#    is LAST and these entries cannot hijack the three intents R23 repaired.
#    Asserted as a fence.
#  - the WEAK path is a conjunctive guard (Rule 5): _BOOK_WORDS_WEAK AND
#    _BOOK_CONTEXT. Both were 100% Latin, so it was doubly dead in Indic —
#    two ANDs, two bypasses. Both halves are extended here or the weak path
#    stays dead no matter what is added to one of them.
#
# DELIBERATELY NOT ADDED:
#  - bare "நேரம்" / "समय" (time) to the STRONG list. "உங்கள் நேரம் என்ன?" and
#    "आपका समय क्या है?" are "what are your opening hours" — a question every
#    clinic gets daily — and booking them would answer an FAQ with a slot list.
#    They appear in _BOOK_CONTEXT only, where a WEAK word must also hit.
#  - bare "அப்பாயின்ட்மென்ட்" / "अपॉइंटमेंट" to STRONG. English carries bare
#    "appointment" and gets away with it because status and cancel are tested
#    first and both now have Indic entries — but relying on branch order for a
#    bare noun is how R15's C2a hijacks happened. Compounds only.
#  - bare "பார்க்க" / "मिलना" (to see / to meet). They are ordinary verbs;
#    "உங்க கிளினிக்கை பார்க்க வேண்டும்" is someone asking for directions. They
#    are WEAK entries, requiring a _BOOK_CONTEXT hit alongside.
_BOOK_WORDS_STRONG_R24 = (
    # English / Thanglish surface forms the measurement exposed
    "need to see the doctor", "see the doctor", "appointment kidaikuma",
    "time venum", "slot venuma", "appointment venuma",
    # Tamil script — compounds only
    "அப்பாயின்ட்மென்ட் வேண்டும்", "அப்பாயின்ட்மென்ட் வேணும்",
    "அப்பாயின்ட்மென்ட் புக்", "அப்பாயின்ட்மென்ட் கிடைக்கும்",
    "புக் பண்ணணும்", "புக் பண்ண", "நேரம் ஒதுக்க", "நேரம் புக்",
    # Devanagari — compounds only. R18-C1 gives Indic prefix matching only from
    # a 4-codepoint stem, so short verb stems are spelled out as surface forms
    # (the R23 lesson: "बदल" is three and can never reach "बदलना").
    "अपॉइंटमेंट चाहिए", "अपॉइंटमेंट बुक", "अपॉइंटमेंट लेना", "अपॉइंटमेंट दे",
    "अपॉइंटमेंट मिलेगा", "समय दे दीजिए", "स्लॉट है", "बुक करना है",
)
_BOOK_WORDS_STRONG = _BOOK_WORDS_STRONG + _BOOK_WORDS_STRONG_R24

_BOOK_WORDS_WEAK_R24 = (
    "paakanum", "paaka", "time irukka", "irukka", "kidaikuma",
    "பார்க்க", "பார்க்கணும்", "இருக்கா", "ஒதுக்க", "வேணும்",
    "मिलना", "मिलेगा", "दिखाना", "लेना है", "मिल सकता",
)
_BOOK_WORDS_WEAK = _BOOK_WORDS_WEAK + _BOOK_WORDS_WEAK_R24

_BOOK_CONTEXT_R24 = (
    "டாக்டர்", "டாக்டரை", "மருத்துவர்", "மருத்துவரை", "அப்பாயின்ட்மென்ட்",
    "கிளினிக்", "நாளை", "நாளைக்கு", "இன்று", "இன்னைக்கு", "நேரம்", "பல்",
    "डॉक्टर", "अपॉइंटमेंट", "क्लिनिक", "कल", "आज", "समय", "दाँत", "दांत",
)
_BOOK_CONTEXT = _BOOK_CONTEXT + _BOOK_CONTEXT_R24

_BOOK_WORDS = _BOOK_WORDS_STRONG + _BOOK_WORDS_WEAK   # back-compat alias
_CANCEL_WORDS = ("cancel", "cancel appointment", "cancel booking", "cancel pannu",
                 "venda", "radd")
_RESCHED_WORDS = ("reschedule", "change appointment", "change time", "postpone",
                  "vera time", "time maathu", "time change")
_STATUS_WORDS = ("my appointment", "my booking", "when is my", "appointment status",
                 "booking status")

# ── v23.0 · FIX R23-C1 (BOOKING STATE MACHINE — a Tamil or Hindi patient could
#    not cancel, reschedule, or check an appointment) ──────────────────────────
# The Rule 3 census made this visible in about a minute: of 24 safety lists,
# _CANCEL_WORDS was 100% Latin (6 entries), and _RESCHED_WORDS and _STATUS_WORDS
# were too. These are the triggers detect_booking_intent dispatches on, so a
# patient writing the script most of this launch market writes fell straight
# through to the AI, which has no booking tools and cannot release a slot.
#
# Measured on R22 by execution over a realistic population, not by counting:
#
#     intent        en      tg      ta      hi      overall
#     cancel       5/5     5/5     0/5     0/5     10/20  (50%)
#     reschedule   2/3     2/3     0/3     0/3      4/12  (33%)
#     status       2/2     1/2     0/2     0/2      3/8   (38%)
#
# This is the same defect class as R18 (emergency keywords), R21 (the identity
# guard's cross-script bridge) and R22 (the clinical-safety control) — the fourth
# consecutive round — but it is the first time it has landed in the BOOKING state
# machine rather than in a guard, and that changes the harm. A dead guard fails
# open and something unsafe reaches the patient. A dead trigger fails CLOSED and
# leaves zombie state: the patient asks to cancel, the engine does not
# understand, the row stays 'booked', and the clinic's chair is held by someone
# who tried to give it back. Nobody is told. Nothing logs. The slot is simply
# gone until _migrate/cleanup marks it 'completed' after slot_end has passed.
#
# The English and Thanglish misses came out of the same measurement and are the
# ordinary asymmetry trap: "change time" was listed but "change the time" was
# not, and "time maathu" was listed but "time maathunga" — the polite imperative,
# which is how anyone actually says it — was not.
#
# Order matters and is preserved: detect_booking_intent tests reschedule BEFORE
# cancel, so "நேரம் மாற்ற" must not also read as a cancel. Verified by execution.
#
# DELIBERATELY NOT ADDED:
#  - bare "வேண்டாம்" / "नहीं चाहिए". They are the ordinary words for "no thanks"
#    and they are how a patient answers NO inside the cancel-confirmation window
#    (_CANCEL_NO_RAW). Listing them as a cancel TRIGGER would let a patient
#    declining a slot cancel a different appointment. Only the compound
#    "அப்பாயின்ட்மென்ட் வேண்டாம்" form is listed.
#  - bare "அப்பாயின்ட்மென்ட்" / "अपॉइंटमेंट" in the status list. _STATUS_WORDS is
#    matched with post_w=0 and would then swallow "எனக்கு அப்பாயின்ட்மென்ட்
#    வேண்டும்" — which is a BOOKING request, the opposite intent. Compounds only.
#  - bare "ரத்த". "ரத்து" (cancel) and "ரத்தம்" (blood) share four codepoints, and
#    R18-C1 gives Indic tokens bounded prefix matching. Checked by execution:
#    0 collisions between every candidate cancel keyword and five Tamil/Hindi
#    bleeding-emergency phrases, and those phrases still fire the emergency layer.
_CANCEL_WORDS_R23 = (
    # English / Thanglish mirrors the measurement exposed
    "cancel it", "cancel my appointment", "want to cancel", "cancel panniduven",
    "appointment venda", "booking venda",
    # Tamil script
    "ரத்து செய்",          # ரத்து செய் — annul
    "ரத்து பண்ண",          # ரத்து பண்ண
    "கேன்சல்",                        # கேன்சல்
    "புக்கிங் ரத்து",   # புக்கிங் ரத்து
    "அப்பாயின்ட்மென்ட் ரத்து",
    "அப்பாயின்ட்மென்ட் வேண்டாம்",
    # Devanagari
    "कैंसिल",                              # कैंसिल
    "केंसिल", "रद्द", "निरस्त",
    "अपॉइंटमेंट नहीं चाहिए",
    "बुकिंग कैंसिल",
)
_CANCEL_WORDS = _CANCEL_WORDS + _CANCEL_WORDS_R23

_RESCHED_WORDS_R23 = (
    "change the time", "change my appointment", "move my appointment",
    "another time", "different time", "time maathunga", "time maathanum",
    "vera time venum", "reschedule pannunga",
    # Tamil script
    "நேரம் மாற்ற",     # நேரம் மாற்ற
    "மாற்றணும்",            # மாற்றணும்
    "வேறு நேரம்",           # வேறு நேரம்
    "ரீ-ஷெட்யூல்",
    "நேரம் மாற்றணும்",
    # Devanagari
    "समय बदल",                             # समय बदल
    # R18-C1 gives Indic tokens prefix matching only from a 4-codepoint stem,
    # and "बदल" is three — so it can never reach "बदलना", which is the form
    # anyone actually writes. Caught by the measurement, not by reading. The
    # surface forms are spelled out, exactly as R18-C1 requires for Latin.
    "समय बदलना", "टाइम बदलना", "समय बदलें", "समय बदलवा", "अपॉइंटमेंट बदलना",
    "टाइम बदल", "री-शेड्यूल",
    "दूसरा टाइम", "दूसरा समय",
)
_RESCHED_WORDS = _RESCHED_WORDS + _RESCHED_WORDS_R23

_STATUS_WORDS_R23 = (
    "en appointment eppo", "booking status enna", "appointment eppo",
    # Tamil script — compounds only, never the bare noun (see note above)
    "அப்பாயின்ட்மென்ட் எப்போது",
    "புக்கிங் நிலை",
    "எனது அப்பாயின்ட்மென்ட்",
    "என் புக்கிங்",
    # Devanagari — compounds only
    "अपॉइंटमेंट कब",
    "बुकिंग की स्थिति",
    "मेरा अपॉइंटमेंट",
    "मेरी बुकिंग",
)
_STATUS_WORDS = _STATUS_WORDS + _STATUS_WORDS_R23

# v15g2 FIX C2b: explicit YES vocabulary for the cancel-confirmation step
# (en / ta / hi + the tapped button id). Anything NOT in this set keeps the
# appointment — the only safe default for a destructive action.
# v16g4 FIX M3: "ok"/"okay"/"சரி"/"ठीक है" — the most common "understood"
# tokens in the launch market — were in the YES set and destroyed the
# appointment, while the fallback prompt promised "Reply *YES*… or *NO*".
# They are now AMBIGUOUS-ACK tokens that trigger a re-confirm instead.
_CANCEL_YES_RAW = ("yes", "y", "yeah", "yep", "yes cancel", "confirm", "sure",
                   "aama", "ama", "aamaa", "haan", "ha", "ji haan",
                   "ஆமாம்", "ஆமா", "ஆம்", "हाँ", "हां", "जी हाँ")
_CANCEL_YES = {_norm_text(x) for x in _CANCEL_YES_RAW}
_CANCEL_ACK_RAW = ("ok", "okay", "k", "kk", "hmm", "hm", "sari", "seri",
                   "சரி", "ठीक है", "theek hai", "thik hai", "acha", "accha")
_CANCEL_ACK = {_norm_text(x) for x in _CANCEL_ACK_RAW}   # v16g4 FIX M3
_CANCEL_NO_RAW = ("no", "n", "nope", "no keep it", "keep", "keep it", "dont",
                  "dont cancel", "vendam", "venda", "illa", "illai",
                  "வேண்டாம்", "இல்லை", "नहीं", "nahi", "nahin", "mat karo")
_CANCEL_NO = {_norm_text(x) for x in _CANCEL_NO_RAW}     # v16g4 FIX M4

# v16g4 port (audit item 201): exact-match global marketing opt-out keywords.
# Deliberately an EXACT-message match (not a substring check) so an ordinary
# sentence containing the word "stop" is never mistaken for an unsubscribe.
# v16g6 FIX R6-H8: English-only consent in a Tamil-first product is not a
# defensible posture under DPDP — a patient typing நிறுத்து could not
# unsubscribe while every other system string was localised in v16g4.
# ta/hi + romanised forms, normalised through _norm_text (the same
# discipline _CANCEL_NO_RAW already uses), plus the standard template
# quick-reply payloads, which arrive as button taps.
_OPT_OUT_RAW = (
    "stop", "unsubscribe", "stop all", "opt out", "optout",
    "stop promotions", "stop promotion",
    "நிறுத்து", "நிறுத்துங்க", "நிறுத்துங்கள்",
    "niruthu", "niruthunga", "stop pannu", "stop pannunga",
    "message vendam", "msg vendam", "sms vendam",
    "बंद करो", "रोको", "band karo", "bandh karo", "message band karo",
    # v16.2 FIX R8-H1: matching stays EXACT (#201) so "don't stop the
    # treatment" can never opt someone out — but the list was keyword-shaped
    # while real people write whole sentences. The 22-Jul test message could
    # not match anything here, so it fell through to the model, which promised
    # to stop sending messages while nothing at all was recorded.
    "\u0b85\u0ba9\u0bc1\u0baa\u0bcd\u0baa\u0bbe\u0ba4\u0bc0\u0b99\u0bcd\u0b95",
    "message \u0b85\u0ba9\u0bc1\u0baa\u0bcd\u0baa\u0bbe\u0ba4\u0bc0\u0b99\u0bcd\u0b95",
    "\u0b87\u0ba9\u0bbf\u0bae\u0bc7 message \u0b85\u0ba9\u0bc1\u0baa\u0bcd\u0baa\u0bbe\u0ba4\u0bc0\u0b99\u0bcd\u0b95",
    "\u0bb5\u0bc7\u0ba3\u0bcd\u0b9f\u0bbe\u0bae\u0bcd \u0b87\u0ba9\u0bbf\u0bae\u0bc7 message \u0b85\u0ba9\u0bc1\u0baa\u0bcd\u0baa\u0bbe\u0ba4\u0bc0\u0b99\u0bcd\u0b95",
    "\u0b9a\u0bc6\u0baf\u0ba4\u0bbf \u0b85\u0ba9\u0bc1\u0baa\u0bcd\u0baa\u0bbe\u0ba4\u0bc0\u0b99\u0bcd\u0b95",
    "\u0b9a\u0bc6\u0baf\u0ba4\u0bbf \u0bb5\u0bc7\u0ba3\u0bcd\u0b9f\u0bbe\u0bae\u0bcd",
    # v28.0 · FIX R28-C1. R8-H1 above rewrote this list from keyword-shaped to
    # sentence-shaped because "real people write whole sentences" — and did it
    # for English, Tamil script and romanised Tamil only. Devanagari kept the
    # bare keyword forms it had before ("बंद करो", "रोको"), and matching is
    # EXACT whole-message by design (#201), so a bare keyword can never be
    # reached by a sentence. Measured on v27 over 7 real Hindi opt-out
    # sentences: en 5/7, ta 7/7, tg 7/7, **hi 0/7**. Driven end-to-end on
    # /chat: the English sentence returns 200 with provider="system" and one
    # opt_outs row; the identical Hindi sentence records NOTHING and falls
    # through to the model — exactly the 22-Jul failure R8-H1 was written to
    # stop, still live for one register. Sentence forms only; no bare "बंद"
    # (a patient asking "बंद क्यों है" is asking whether the clinic is shut)
    # and no bare "नहीं चाहिए" (that is how a patient declines a slot).
    "message anuppadheenga", "message anupadhinga", "msg anuppadheenga",
    "innime message anuppadheenga", "message anupathinga",
    "stop sending messages", "stop messaging me", "do not message me",
    "dont message me", "no more messages", "remove me from list",
    "remove my number",
)

_OPT_OUT_RAW_R28 = (
    "\u092e\u0941\u091d\u0947 \u092e\u0948\u0938\u0947\u091c \u092e\u0924 \u092d\u0947\u091c\u094b",
    "\u092e\u0941\u091d\u0947 \u092e\u0948\u0938\u0947\u091c \u092e\u0924 \u092d\u0947\u091c\u093f\u090f",
    "\u092e\u0948\u0938\u0947\u091c \u092e\u0924 \u092d\u0947\u091c\u094b",
    "\u092e\u0948\u0938\u0947\u091c \u092d\u0947\u091c\u0928\u093e \u092c\u0902\u0926 \u0915\u0930\u094b",
    "\u092e\u0948\u0938\u0947\u091c \u092d\u0947\u091c\u0928\u093e \u092c\u0902\u0926 \u0915\u0930\u0947\u0902",
    "\u092e\u0941\u091d\u0947 \u0914\u0930 \u092e\u0948\u0938\u0947\u091c \u0928\u0939\u0940\u0902 \u091a\u093e\u0939\u093f\u090f",
    "\u092e\u0941\u091d\u0947 \u092e\u0948\u0938\u0947\u091c \u0928\u0939\u0940\u0902 \u091a\u093e\u0939\u093f\u090f",
    "\u0905\u092c \u092e\u0948\u0938\u0947\u091c \u092e\u0924 \u092d\u0947\u091c\u093f\u090f",
    "\u0905\u092c \u092e\u0948\u0938\u0947\u091c \u092e\u0924 \u092d\u0947\u091c\u094b",
    "\u092e\u0947\u0930\u093e \u0928\u0902\u092c\u0930 \u0939\u091f\u093e \u0926\u094b",
    "\u092e\u0947\u0930\u093e \u0928\u0902\u092c\u0930 \u0939\u091f\u093e\u0907\u090f",
    "\u092e\u0941\u091d\u0947 \u0932\u093f\u0938\u094d\u091f \u0938\u0947 \u0939\u091f\u093e \u0926\u094b",
    "\u0938\u0902\u0926\u0947\u0936 \u092c\u0902\u0926 \u0915\u0930\u094b",
    "\u0938\u0902\u0926\u0947\u0936 \u092e\u0924 \u092d\u0947\u091c\u094b",
    "\u092e\u0948\u0938\u0947\u091c \u092c\u0902\u0926 \u0915\u0930\u094b",
    "\u0915\u094b\u0908 \u092e\u0948\u0938\u0947\u091c \u092e\u0924 \u092d\u0947\u091c\u094b",
)
_OPT_OUT_KEYWORDS = {_norm_text(x) for x in _OPT_OUT_RAW + _OPT_OUT_RAW_R28}

# v29.0 · FIX R29-C1. The WhatsApp handler suppresses the ENTIRE opt-out list
# while a slot offer (900s) or a cancel confirmation is open. /chat and the
# Instagram webhook suppress nothing — three implementations of one consent
# operation, and the strictest one is on the only channel real patients use.
# Measured: WA with no window records a row; WA with bk_offer open records
# NOTHING, for "stop sending messages" AND for a bare "unsubscribe"; /chat
# records a row for the same text. Suppression is defensible only for forms
# that could plausibly mean "stop THIS flow" — a bare stop-word answering a
# slot list. It is not defensible for "unsubscribe", "opt out", "remove my
# number" or any sentence form: those cannot mean anything except consent
# withdrawal, and DPDP does not pause for a booking window.
_OPT_OUT_AMBIGUOUS_IN_WINDOW = {_norm_text(x) for x in (
    "stop", "\u0ba8\u0bbf\u0bb1\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1",
    "\u0ba8\u0bbf\u0bb1\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1\u0b99\u0bcd\u0b95",
    "\u0ba8\u0bbf\u0bb1\u0bc1\u0ba4\u0bcd\u0ba4\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd",
    "niruthu", "niruthunga", "stop pannu", "stop pannunga",
    "\u0930\u094b\u0915\u094b", "\u092c\u0902\u0926 \u0915\u0930\u094b",
    "band karo", "bandh karo",
)}


def detect_booking_intent(text: str) -> Optional[str]:
    """v15g2 FIX C2a (CRITICAL): was raw substring matching — 'cancel' matched
    inside 'canCELLATION policy', 'available' inside 'UNavailable', 'consult'
    inside 'consultation fee' — so ordinary questions were hijacked by the
    booking engine and (before FIX C2b) a policy QUESTION instantly cancelled a
    patient's real appointment. Now whole-word + negation-aware via _kw_hit,
    the exact matcher v15 FIX 4 already gave business-type detection."""
    norm = _norm_text(text)
    if not norm:
        return None
    if any(_kw_hit(norm, w) for w in _RESCHED_WORDS): return "reschedule"
    # v16g3 FIX R3-H3: pre_w=2 catches "please don't ever cancel"; a wrongly
    # skipped genuine cancel is safe — the read-only status branch (post_w=0,
    # so "cancel my appointment illa" resolves to STATUS, not a slot list)
    # or the AI picks it up, and destruction always re-confirms anyway.
    if any(_kw_hit(norm, w, pre_w=2) for w in _CANCEL_WORDS):  return "cancel"
    if any(_kw_hit(norm, w, post_w=0) for w in _STATUS_WORDS): return "status"
    if any(_kw_hit(norm, w) for w in _BOOK_WORDS_STRONG):      return "book"
    if (any(_kw_hit(norm, w) for w in _BOOK_WORDS_WEAK)        # v16g3 FIX R3-H2
            and any(_kw_hit(norm, c) for c in _BOOK_CONTEXT)):
        return "book"
    return None


def _parse_slot_pick(text: str) -> Optional[int]:
    t = (text or "").strip().lower()
    # v15g4 FIX B3: the 'slot:N' interactive-id branch moved to handle_booking,
    # where taps are matched by EPOCH against the current offer — this parser
    # now handles TYPED picks only.
    # v15 FIX 9 (MEDIUM): only a BARE pick counts — '3', 'no 3', '#3',
    # 'option 3.', '3.'. The old \D*(\d{1,2})\D* matched a number ANYWHERE in a
    # sentence, so "can I come at 5?" booked slot #5 (a totally different time)
    # and "I prefer 2pm" booked slot #2. Anything else → re-offer with guidance.
    m = re.fullmatch(r"(?:no\.?\s*|option\s*|#\s*)?(\d{1,2})\s*\.?", t)
    if m:
        return int(m.group(1))
    return None


def _booking_owner_of_slot(customer_id: str, start_iso: str) -> Optional[Dict]:
    """v15g4 FIX B10: who holds this exact slot, if anyone? Used to recognise
    a patient rescheduling onto the appointment they ALREADY have (the unique
    index reports it as a 'conflict', which used to loop 'just taken' forever)."""
    try:
        with _db_pool.get(read_only=True) as conn:
            # v16g6 FIX R6-L12: exact-string equality on slot_start breaks
            # the moment two writers format the same instant differently
            # (+00:00 vs Z, microseconds present or not) — B10's
            # self-conflict detection then misses and the patient loops on
            # "just taken". Match the parsed INSTANT over the enclosing
            # minute window instead.
            _t0 = _parse_dt(start_iso)
            cur = _execute(conn,
                "SELECT id, phone_hash, slot_start FROM bookings "
                "WHERE customer_id=? AND status='booked' "
                "AND slot_start >= ? AND slot_start < ? LIMIT 8",
                (customer_id,
                 (_t0 - timedelta(minutes=1)).isoformat(),
                 (_t0 + timedelta(minutes=1)).isoformat()))
            for _r in cur.fetchall():
                try:
                    if _parse_dt(_r["slot_start"]) == _t0:
                        return {"id": _r["id"], "phone_hash": _r["phone_hash"]}
                except Exception:
                    continue
            row = None
        return dict(row) if row else None
    except Exception as exc:
        log.warning(f"⚠️  _booking_owner_of_slot failed: {exc}")
        return None


def _booking_status_text(b: Optional[Dict], lang: str = "en") -> str:
    """v14g5 FIX 49: one canonical 'your appointment' message so the wording can
    never drift between the status branch and any future caller.
    v16g4 FIX M8: localized."""
    if b:
        return _t("status_upcoming", lang, when=_fmt_local_dt(b['slot_start']))
    return _t("status_none", lang)


def handle_booking(brain: Dict, from_phone: str, user_text: str,
                   out_pid: str, out_tok: str, customer_id: str,
                   session_id: str, subject_name: str = "",
                   channel: str = "whatsapp",
                   sink: Optional[List[str]] = None) -> bool:   # v19.0 R19-C1
    """Deterministic booking state machine. Returns True if it handled the
    message (caller should then stop). Returns False to let the normal AI run.
    v14g5 FIX 12: a RESCHEDULE no longer cancels the existing appointment up-front;
    the old slot is carried as prev_id and retired ONLY after a new slot is secured,
    so abandoning the flow can never leave the patient with no appointment."""
    if not cfg.ENABLE_BOOKING:
        return False

    offer_key  = f"bk_offer:{customer_id}:{from_phone}"
    cancel_key = f"bk_cancel:{customer_id}:{from_phone}"   # v15g2 FIX C2b
    booked_ok  = False                                     # v16 U3
    _owner_event = ""      # v16.5 R11-H1: "new" | "rescheduled" | "cancelled"
    _owner_slot  = ""      # set together with _owner_event, never alone
    text      = (user_text or "").strip()
    low       = text.lower()
    lang      = _user_lang(customer_id, from_phone, text)  # v16g4 FIX M8
    # ('text',msg) | ('list',body,rows,payload) | ('confirm',body,buttons)
    action: Optional[Tuple] = None

    # v15g2 FIX C2b (CRITICAL): a pending cancel-confirmation is answered FIRST.
    # Cancelling is destructive — it now requires an explicit YES (button tap or
    # typed). Any other reply keeps the appointment: the safe default.
    pending_cancel = brain_cache.get(cancel_key)
    if pending_cancel:
        # v16g6 FIX R6-M14: the window was consumed at the TOP, so an
        # unrelated reply ("fine", "done", a question) silently destroyed
        # the pending confirmation — the patient's later YES did nothing,
        # and the AI answered with no idea a cancellation was pending.
        # Consume the window only on the branches that RESOLVE it; the
        # unmatched fall-through keeps it armed for its remaining TTL.
        # v16g3 FIX R3-L7: taps arrive as 'Title [id]' now — match button
        # ids by substring so readable history and the state machine coexist.
        if "cancel:yes" in low or _norm_text(text) in _CANCEL_YES:
            brain_cache.delete(cancel_key)
            try:
                _pending_id = int(pending_cancel)
            except (TypeError, ValueError):
                _pending_id = None
            b = booking_upcoming_for_phone(customer_id, from_phone)
            if b and (_pending_id is None or b["id"] == _pending_id):
                # v16g4 FIX M5: only claim "Cancelled" when the row actually
                # transitioned — a DB blip no longer lies to the patient.
                if booking_cancel_by_id(b["id"]):
                    _owner_event = "cancelled"                # v16.5 R11-H1
                    _owner_slot  = b["slot_start"]
                    action = ("text", _t("cancelled_ok", lang,
                                         when=_fmt_local_dt(b['slot_start'])))
                else:
                    action = ("text", _t("cancel_failed", lang))
            else:
                action = ("text", _t("already_changed", lang))
        elif "cancel:no" in low or _norm_text(text) in _CANCEL_NO:
            # v16g3 FIX R3-M5: the explicit keep-tap is never re-read as a
            # fresh cancel intent. v16g4 FIX M4: typed "no"/"vendam"/"नहीं"
            # count as the explicit keep too.
            brain_cache.delete(cancel_key)               # v16g6 FIX R6-M14
            action = ("text", _t("keep_unchanged", lang))
        elif _norm_text(text) in _CANCEL_ACK:
            # v16g4 FIX M3: "ok"/"சரி"/"ठीक है" is an acknowledgement, not a
            # confirmed destruction. Re-arm the window and ask plainly.
            brain_cache.set(cancel_key, pending_cancel, ttl=300)
            action = ("text", _t("reconfirm_cancel", lang))
        elif detect_booking_intent(text) in ("book", "reschedule", "status"):
            # v15g4 FIX B11: a booking intent typed inside the confirm window
            # was discarded with "your appointment is unchanged" and the
            # patient had to repeat themselves. The appointment still stays
            # (safe default) — but the intent now falls through to the normal
            # flow below and gets SERVED.
            brain_cache.delete(cancel_key)               # v16g6 FIX R6-M14
            action = None
        else:
            # v16g4 FIX M4 (last residue of the A3/B11 class): "wait, what
            # time was it?" inside the confirm window was swallowed and the
            # question never reached the AI. v16g6 FIX R6-M14: the window now
            # stays ARMED for its remaining TTL — the question gets answered
            # below, and a follow-up YES/NO still lands on the pending
            # cancellation instead of doing nothing.
            return False
        if action is not None:
            # v16g5 FIX R5-M1: this was the only _booking_dispatch call site
            # in the file that omitted lang=, so a Tamil/Hindi patient
            # confirming a cancellation got the English "Reply *YES* / *NO*"
            # fallback wording — an M8 gap hiding in the most destructive
            # branch of the state machine.
            _booking_dispatch(action, from_phone, out_pid, out_tok, customer_id,
                              session_id, user_text, lang=lang)
            # v16.7 FIX R13-H1: the confirm-window has its OWN dispatch and
            # returns here, so it never reached the notifier in the shared tail
            # below — the R11 cancellation alert set its flag and was then
            # thrown away. The doctor's slot silently freed up with no message.
            # Missed by the R11 tests because they asserted "handle_booking
            # CALLS notify_owner_booking" via AST, which was true of the other
            # path; only driving a real cancel end-to-end exposed it.
            if _owner_event:
                notify_owner_booking(brain, _owner_event, subject_name,
                                     from_phone, _owner_slot, channel=channel)
            return True

    # v16g3 FIX R3-M5: a "No, keep it" tap landing AFTER the 5-min confirm
    # TTL used to be re-read as a fresh CANCEL intent — the bot answered
    # "keep it" by asking "are you sure you want to cancel?" again. A stale
    # keep-tap now just keeps. (A stale cancel:yes still re-confirms — the
    # safe direction for a destructive action.)
    if "cancel:no" in low:
        _booking_dispatch(("text", _t("keep_unchanged", lang)),
                          from_phone, out_pid, out_tok, customer_id,
                          session_id, user_text, lang=lang)   # v16g4 FIX M8
        return True

    raw_offer = brain_cache.get(offer_key)
    if raw_offer:
        # An offer is active — interpret this message as a slot pick / abort.
        try:
            payload = json.loads(raw_offer)
            if isinstance(payload, dict):
                offers  = payload.get("slots", [])
                prev_id = payload.get("prev_id")
            else:                       # tolerate pre-FIX bare-list payloads in cache
                offers, prev_id = payload, None
        except Exception:
            offers, prev_id = [], None

        # v15 FIX 10 (MEDIUM): the abort list was exact-match only, so a patient
        # typing "cancel appointment" or "cancel pannu" MID-OFFER fell through
        # to slot parsing and got "Please reply with the number…" forever. Any
        # cancel intent now aborts the flow (the existing appointment, if any,
        # stays untouched — same safe semantics as before).
        if (low in ("stop", "no", "exit")
                or detect_booking_intent(text) == "cancel"):
            brain_cache.delete(offer_key)
            # FIX 12: abandoning a reschedule must NOT lose the original booking —
            # we never cancelled it, so it simply stands.
            kept = _t("kept_note", lang) if prev_id else ""
            # v16g6 FIX R6-M15: inside a booking flow "stop" deliberately
            # means "abort this flow", NOT the global unsubscribe (the R6-H8
            # gate excludes active flows for exactly that reason). The
            # narrower meaning is defensible; saying nothing about it is not
            # — the patient hears "okay, stopped" and reasonably believes
            # they unsubscribed. Say so, and say how to actually do it.
            _note = {"ta": "நீங்கள் unsubscribe ஆகவில்லை — செய்திகளை "
                           "நிறுத்த 'STOP' என்று மட்டும் தனியாக அனுப்புங்கள்.",
                     "hi": "आप अनसब्सक्राइब नहीं हुए हैं — संदेश बंद करने "
                           "के लिए केवल 'STOP' भेजें।",
                     }.get(lang, "You are still subscribed — to stop "
                                 "receiving messages, send just 'STOP'.")
            action = ("text", _t("stop_booking", lang, kept=kept)   # v16g4 FIX M8
                              + "\n" + _note)
        else:
            pick, stale_tap = None, False
            m_tap = re.search(r"slot:(\d+)", low)
            if m_tap:
                # v15g4 FIX B3: a tap is matched by EPOCH to the exact time the
                # button displayed. No match = the tap came from a superseded
                # (or pre-GEN4) list → offer fresh times, never a wrong slot.
                want = m_tap.group(1)
                for i, pair in enumerate(offers):
                    try:
                        if str(int(datetime.fromisoformat(pair[0]).timestamp())) == want:
                            pick = i + 1
                            break
                    except Exception:
                        continue
                stale_tap = pick is None
            else:
                pick = _parse_slot_pick(text)
            if stale_tap:
                action = _booking_offer_action(customer_id,
                    note=_t("offer_expired", lang),
                    prev_id=prev_id, lang=lang)   # v16g4 FIX M8
            elif pick is not None and 1 <= pick <= len(offers):
                start_iso, end_iso = offers[pick - 1]
                res = booking_create(customer_id, from_phone, subject_name,
                                     start_iso, end_iso,
                                     replacing_id=prev_id)   # v16.6 R12-H1
                if res == "ok":
                    brain_cache.delete(offer_key)
                    # only NOW retire the old slot — the reschedule has succeeded
                    _retired = booking_cancel_by_id(prev_id) if prev_id else True
                    if prev_id and not _retired:
                        # v16g4 FIX M5: the new slot IS booked but the old row
                        # refused to die — the patient now holds two slots.
                        # Say "confirmed" (true), and scream so you reconcile.
                        log.critical(f"🛑 reschedule retire FAILED — patient "
                                     f"holds TWO slots (old id={prev_id}, "
                                     f"cust={customer_id}). Reconcile manually.")
                        analytics.inc("booking.retire_failed")
                    _msg_key = ("booked_rescheduled" if (prev_id and _retired)
                                else "booked_confirmed")
                    booked_ok = True                       # v16 U3
                    # v16.5 R11-H1: reuse the SAME condition the patient's
                    # confirmation rides on, so the owner is told exactly when
                    # (and only when) a row really moved.
                    _owner_event = ("rescheduled" if (prev_id and _retired)
                                    else "new")
                    _owner_slot  = start_iso
                    action = ("text", _t(_msg_key, lang,
                                         when=_fmt_local_dt(start_iso)))
                elif res == "limit":
                    # v16.6 R12-H1: reached only from a stale offer — the
                    # pre-check below normally stops this before slots are
                    # ever shown. Clear the offer so they are not stuck.
                    brain_cache.delete(offer_key)
                    _held = booking_active_count_for_phone(customer_id, from_phone)
                    action = ("text", _t("booking_limit", lang, n=_held))
                    notify_owner_booking(brain, "limit_hit", subject_name,
                                         from_phone, "", channel=channel)
                elif res == "conflict":
                    # v15g4 FIX B10: if the "taken" slot is the patient's OWN
                    # current appointment (rescheduling onto the time they
                    # already hold), the old branch looped "just taken — fresh
                    # times" forever. Recognise self-conflict and keep it.
                    own = _booking_owner_of_slot(customer_id, start_iso)
                    if own and own.get("phone_hash") == _crm_phone_hash(customer_id, from_phone):
                        brain_cache.delete(offer_key)
                        action = ("text", _t("own_slot_kept", lang,
                                             when=_fmt_local_dt(start_iso)))
                    else:
                        # genuinely taken by someone else — re-offer, PRESERVING
                        # prev_id so the next pick still reschedules.
                        action = _booking_offer_action(customer_id,
                            note=_t("slot_taken", lang),
                            prev_id=prev_id, lang=lang)
                else:
                    # v15g2 FIX L5: infrastructure error ≠ taken slot. Keep the
                    # existing offer in cache (never deleted) so their retry works.
                    action = ("text", _t("save_error", lang))
            else:
                action = _booking_offer_action(customer_id,
                    note=_t("pick_number", lang),
                    prev_id=prev_id, lang=lang)
    else:
        # v16g4 FIX M15: no ACTIVE offer, but the patient just typed a bare
        # slot number ("2") shortly after the offer TTL lapsed. Without this,
        # the number fell through to the AI as arbitrary text. If a recent
        # tombstone is present, treat it as a stale pick and re-offer fresh
        # times (never book blindly — the old list's times may be gone).
        if (cfg.ENABLE_BOOKING and _parse_slot_pick(text) is not None
                and not re.search(r"slot:\d+", low)
                and brain_cache.get(f"bk_offer_recent:{customer_id}:{from_phone}")):
            brain_cache.delete(f"bk_offer_recent:{customer_id}:{from_phone}")
            _booking_dispatch(
                _booking_offer_action(customer_id,
                                      note=_t("offer_expired", lang),
                                      lang=lang),
                from_phone, out_pid, out_tok, customer_id,
                session_id, user_text, lang=lang)
            return True
        intent = detect_booking_intent(text)
        if not intent:
            return False
        if intent == "status":
            b = booking_upcoming_for_phone(customer_id, from_phone)
            action = ("text", _booking_status_text(b, lang))   # v16g4 FIX M8
        elif intent == "cancel":
            # v15g2 FIX C2b (CRITICAL): NEVER cancel on intent alone — the old
            # branch destroyed the appointment instantly, so "what is your
            # cancellation policy?" and "I do NOT want to cancel" both deleted a
            # patient's real booking. Now: stash the booking id (5-min window)
            # and ask an explicit yes/no via wa_send_buttons_now — the function
            # whose own docstring said it was "used for yes/no confirmations
            # (cancel, reschedule)" yet was never called anywhere until now.
            b = booking_upcoming_for_phone(customer_id, from_phone)
            if not b:
                action = ("text", _t("no_upcoming_cancel", lang))   # v16g4 FIX M8
            else:
                brain_cache.set(cancel_key, str(b["id"]), ttl=300)
                action = ("confirm",
                    _t("cancel_confirm", lang,
                       when=_fmt_local_dt(b['slot_start'])),
                    [{"id": "cancel:yes", "title": _t("btn_yes_cancel", lang)},
                     {"id": "cancel:no",  "title": _t("btn_no_keep", lang)}])
        else:  # book or reschedule
            prev_id = None
            if intent == "reschedule":
                # FIX 12: capture (do NOT cancel) the current appointment.
                existing = booking_upcoming_for_phone(customer_id, from_phone)
                prev_id  = existing["id"] if existing else None
            # v16.6 R12-H1: check BEFORE showing times. Offering a slot list
            # and then refusing the pick is a bad way to tell someone they are
            # at the limit. A reschedule replaces rather than adds, so it is
            # never pre-checked.
            _held = (0 if intent == "reschedule"
                     else booking_active_count_for_phone(customer_id, from_phone))
            if _held >= cfg.MAX_ACTIVE_BOOKINGS_PER_PHONE:
                analytics.inc("booking.limit_prechecked")
                action = ("text", _t("booking_limit", lang, n=_held))
                notify_owner_booking(brain, "limit_hit", subject_name,
                                     from_phone, "", channel=channel)
            else:
                action = _booking_offer_action(customer_id, prev_id=prev_id,
                                               lang=lang)   # v16g4 FIX M8

    if action is None:
        return False
    _booking_dispatch(action, from_phone, out_pid, out_tok, customer_id,
                      session_id, user_text, lang=lang,
                      channel=channel, sink=sink)   # v19.0 R19-C1
    # v16.5 R11-H1: patient first, owner second — the confirmation the patient
    # is waiting on never queues behind a notification.
    if _owner_event:
        notify_owner_booking(brain, _owner_event, subject_name, from_phone,
                             _owner_slot, channel=channel)
    if booked_ok and channel != "api":
        # v16 U3: booking secured → if this patient is username-only (BSUID)
        # and we hold no real number, ask exactly once. Reminders need it;
        # the ask rides AFTER the ✅ confirmation so the flow feels natural.
        # v19.0 R19-C1c: never on the api channel — _maybe_request_phone sends
        # a WhatsApp interactive message to a chat id that does not exist, and
        # would burn the 7-day nag guard for an identity that will never be
        # seen again.
        _maybe_request_phone(customer_id, from_phone, out_pid, out_tok,
                             lang=lang)   # v16g4 FIX M8
    return True


def _booking_offer_action(customer_id: str, note: str = "", prev_id=None,
                          lang: str = "en") -> Tuple:
    """Build the slot-offer action AND stash the offered slots (plus any prev_id
    being rescheduled) in cache so the next inbound message can be matched to a
    slot by index and complete the reschedule atomically.
    v16g4 FIX M8: localized note + no-slots line."""
    slots = booking_available_slots(customer_id, cfg.BOOKING_SLOTS_SHOWN)
    if not slots:
        return ("text", _t("no_slots", lang))
    offers = [[s.isoformat(), e.isoformat()] for s, e in slots]
    # v15g4 FIX B3: the row id used to be a bare index (slot:3). A tap on a
    # STALE list — after a newer offer replaced the cache — booked index 3 of
    # the NEW list: a different datetime than the button displayed. The id now
    # carries the slot's epoch, so a tap is matched to the exact time it
    # showed, and a mismatch triggers a fresh list instead of a wrong booking.
    rows = [{"id": f"slot:{int(s.timestamp())}", "title": _fmt_local_dt(s)[:24],
             "description": _fmt_local_time_range(s, e)}
            for s, e in slots]                        # v16g2 FIX C4: unused `i`
    body = ((note + "\n\n") if note else "") + _t("offer_header", lang)
    return ("list", body, rows, {"slots": offers, "prev_id": prev_id})


# ── v16.5 · FIX R11-H1 (REVENUE-CRITICAL) ────────────────────────────────────
# Audited 26-Jul: owner alerts fired for emergencies, human-handoff requests,
# VIP leads and AI escalations — but NEVER for an actual booking. handle_booking
# does not call send_owner_alert_async at all. So the assistant could fill a
# doctor's whole day and the doctor would learn about it only by calling a JSON
# admin endpoint with a JWT, which no clinic owner will ever do.
#
# That is the first question every prospect asks — "fine, but how do I see the
# appointments?" — and "check the API" is not an answer. The alert goes to the
# place they already live: their own WhatsApp.
#
# Failure here must never cost the booking: the send is fire-and-forget and the
# whole call is wrapped, because a notification problem is not a booking problem.
_BOOKING_EVENT_LINES = {
    "new":         "\U0001f4c5 NEW BOOKING",
    "rescheduled": "\U0001f501 RESCHEDULED",
    "cancelled":   "\u274c CANCELLED",
    # v16.6 R12-H1: not a diary change — a heads-up that one number is trying
    # to take a fourth slot. This is the signal a doctor actually wants when
    # they ask "what if someone prank-books me?".
    "limit_hit":   "\u26a0\ufe0f BOOKING LIMIT HIT \u2014 this number tried to book again",
}


def notify_owner_booking(brain: Dict, event: str, subject_name: str,
                         patient_phone: str, slot_iso: str,
                         channel: str = "whatsapp") -> None:
    """Tell the clinic owner, on WhatsApp, that their diary just changed."""
    try:
        # v16g2 FIX M9 precedent: a public demo must never page a real owner.
        # handle_booking is currently reachable only from the WhatsApp webhook,
        # so this is belt-and-braces for whoever wires it up next.
        if channel == "api":
            return
        owner = (brain.get("owner_phone") or "").strip()
        if not owner:
            return
        head = _BOOKING_EVENT_LINES.get(event, _BOOKING_EVENT_LINES["new"])
        who  = (subject_name or "").strip() or "Patient"
        num  = (patient_phone if cfg.OWNER_ALERT_FULL_PHONE
                else pii_vault.mask(patient_phone))
        when = _fmt_local_dt(slot_iso) if slot_iso else ""
        when = ("was " + when) if (event == "cancelled" and when) else when
        body = f"{head}\n{who} \u00b7 {num}" + (f"\n{when}" if when else "")
        _opid, _otok = brain_wa_creds(brain)
        send_owner_alert_async(owner, body, _opid, _otok,
                               brain.get("customer_id", ""))
        analytics.inc(f"owner_alert.booking_{event}")
    except Exception as exc:                       # never break a booking
        log.warning(f"\u26a0\ufe0f  booking owner-alert failed ({event}): {exc}")


def _booking_dispatch(action: Tuple, from_phone: str, out_pid: str, out_tok: str,
                      customer_id: str, session_id: str, user_text: str,
                      lang: str = "en", channel: str = "whatsapp",
                      sink: Optional[List[str]] = None) -> None:   # v19.0 R19-C1
    """Record the turn, THEN send — v15g2 FIX L4: this path was send-then-persist,
    contradicting the v14g5 FIX 50 persist-then-send standard, so a crash between
    the network send and the save dropped the turn from history. Handles three
    kinds: plain text, interactive slot list (numbered-text fallback), and yes/no
    confirmation buttons (typed YES/NO fallback — v15g2 FIX C2b)."""
    if action[0] == "list":
        _, body, rows, payload = action
        brain_cache.set(f"bk_offer:{customer_id}:{from_phone}",
                        json.dumps(payload), ttl=900)
        # v16g4 FIX M15: leave a short tombstone so a bare slot-number typed
        # just after the 15-min offer TTL lapsed is recognised as a stale
        # pick (→ re-offer) instead of being handed to the AI as if it were
        # arbitrary text ("please reply with a number" loop / nonsense reply).
        brain_cache.set(f"bk_offer_recent:{customer_id}:{from_phone}", "1",
                        ttl=3600)
        # offer and cancel-confirmation states must never coexist
        brain_cache.delete(f"bk_cancel:{customer_id}:{from_phone}")
        numbered = "\n".join(f"{i+1}. {r['title']} ({r['description']})"
                             for i, r in enumerate(rows))
        log_text = body + "\n\n" + numbered
    elif action[0] == "confirm":                      # v15g2 FIX C2b
        _, body, _buttons = action
        log_text = body + "\n\n" + _t("typed_yes_no", lang)   # v16g4 FIX M8
    else:
        _, msg = action
        log_text = msg
    try:
        # v19.0 R19-C1b: this hard-coded "whatsapp" as the inbound channel.
        # Once /chat reaches this path, every demo turn would have been filed
        # as a WhatsApp message — corrupting the one table the clinic reads to
        # see where its patients actually come from.
        save_messages_batch(session_id, [
            ("user",  user_text, ("api" if channel == "api" else "whatsapp"), 0),
            ("model", log_text,  "booking",  0)])
        increment_chat_count(customer_id)
        analytics.inc("booking.handled")
    except Exception as _pe:
        # v16g2 FIX L12: the whole point of persist-then-send is the audit
        # trail existing — a swallowed save must at least be visible.
        analytics.inc("booking.persist_failed")
        log.warning(f"⚠️  booking turn persist failed (session={session_id}): {_pe}")
    # ── v19.0 · FIX R19-C1 (REVENUE-CRITICAL) ───────────────────────────────
    # The api channel has no WhatsApp session to send into, so the reply is
    # CAPTURED and handed back to the caller instead. log_text is exactly what
    # a WhatsApp user whose interactive send failed would have received — the
    # numbered slot list, or the confirmation body plus the typed YES/NO line
    # — so the demo shows the real flow, not a re-implementation of it that
    # can drift. Everything above this point (persist, cache, offer/cancel
    # state) has already run identically for both channels; only the transport
    # differs.
    if channel == "api":
        if sink is not None:
            sink.append(log_text)
        analytics.inc("booking.api_captured")
        return
    # ── v26.0 · FIX R26-C1 (ZOMBIE BOOKING — persist committed, patient never told)
    # Rule 12, eight rounds on the ledger, driven for the first time here.
    #
    # The house convention is persist-first-send-second, which is right. But the
    # send below was UNGUARDED, and everything above it has already committed.
    # Measured on the WhatsApp path with the transport raising ConnectionError
    # immediately after the commit:
    #
    #   booking row committed ........ yes
    #   slot removed from availability yes
    #   patient told .................. NO
    #   handle_booking returned ....... None (the exception escaped)
    #   outbox entry .................. none
    #   retry ......................... none
    #
    # And there is no retry to be had. The webhook returns 200 to Meta the
    # instant it queues (`ALWAYS 200 immediately — Meta must never time out or
    # retry-storm`), so Meta never redelivers; the wamid dedupe claim is only
    # released when the BACKLOG is full, not when the worker throws; and the
    # worker's own handler logs a generic `❌ ordered task error` with a stack
    # trace, which tells nobody that a chair is now held by a patient who does
    # not know they booked it. The clinic loses the slot AND the patient.
    #
    # The cure was already in the building. `outbox_publish("whatsapp.send", …)`
    # is the transactional outbox — persisted first, drained by a background
    # worker, at-least-once — and reminders and owner alerts have used it since
    # v14. Booking confirmations, the one message a patient is actually waiting
    # for, went out on a bare synchronous call. The patient messaged us this
    # turn, so they are inside WhatsApp's 24-hour service window by definition
    # and free text delivers.
    #
    # Swallowing is deliberate and narrow: the booking DID happen, so
    # handle_booking must still return True or the AI answers on top of a real
    # confirmation. The exception is converted into a durable retry plus a
    # SPECIFIC log line — the failure this guards is silence, so the cure is
    # noise that names what is actually wrong.
    def _send_or_queue(fn, *args, **kwargs) -> None:
        try:
            if fn(*args, **kwargs):
                return
            send_whatsapp_sync(from_phone, log_text, out_pid, out_tok, customer_id)
            return
        except Exception as exc:
            queued = outbox_publish("whatsapp.send", {
                "to": from_phone, "customer_id": customer_id,
                "message": log_text})
            analytics.inc("booking.send_failed_queued" if queued
                          else "booking.send_failed_lost")
            log.critical(
                f"🛑 R26-C1 ZOMBIE BOOKING: the row is COMMITTED and the slot is "
                f"consumed, but the confirmation did not reach the patient "
                f"(cust={customer_id}, action={action[0]}). "
                + ("Re-queued on the outbox for retry. " if queued else
                   "OUTBOX PUBLISH ALSO FAILED — this patient will not be told "
                   "by any automatic path. ")
                + f"Cause: {type(exc).__name__}: {exc}")

    if action[0] == "list":
        _, body, rows, _payload = action
        _send_or_queue(wa_send_list_now, from_phone, body,
                       _t("btn_pick_time", lang), rows, out_pid, out_tok,
                       customer_id, header=_t("hdr_book", lang))   # v16g4 FIX M8
    elif action[0] == "confirm":
        _, body, buttons = action
        _send_or_queue(wa_send_buttons_now, from_phone, body, buttons,
                       out_pid, out_tok, customer_id)
    else:
        _send_or_queue(lambda *a, **k: send_whatsapp_sync(*a, **k) or True,
                       from_phone, log_text, out_pid, out_tok, customer_id)


# ═════════════════════════════════════════════════════════════════════════════
# ⏰  v14 GEN-4 — SCHEDULER  (flag: ENABLE_SCHEDULER, default OFF)
#   Runs inside the existing janitor thread. Reminders + cold-lead follow-ups
#   are published to the transactional OUTBOX, so they reuse the per-tenant
#   creds + token self-heal path (gen-3 BUG 9). HONEST NOTE: WhatsApp only
#   delivers FREE TEXT inside the 24-hour customer-service window; outside it
#   you MUST use an approved template (set *_TEMPLATE env). The scheduler routes
#   via template automatically when one is configured.
# ═════════════════════════════════════════════════════════════════════════════
def _publish_reminder(customer_id: str, phone: str, when_text: str, full_msg: str) -> bool:
    """v16g5 FIX R5-H1: FIX H2's own reasoning — "a cold lead is BY DEFINITION
    outside the 24h customer-service window, so the free-text fallback burned
    5 outbox retries per lead per tick" — applies VERBATIM to a 24-hour
    appointment reminder: a patient who booked yesterday and hasn't messaged
    since is outside the window too. H2 guarded _publish_followup and left
    this twin free-texting. With REMINDER_TEMPLATE unset (the default ""),
    every 24h reminder burned its attempt budget and dead-lettered while
    `scheduler.reminders_scanned` read perfectly healthy.

    Free text is still permitted for a reminder falling INSIDE the window
    (the 2-hour lead for a patient who chatted this morning) — that one
    genuinely delivers — but only when we can see an open session."""
    # v16g5: BSUID-aware, matching _publish_followup (was missing here).
    phone = _resolve_send_addr(customer_id, phone)
    if cfg.REMINDER_TEMPLATE:
        return outbox_publish("whatsapp.template", {
            "to": phone, "customer_id": customer_id,
            "template": cfg.REMINDER_TEMPLATE, "lang": cfg.REMINDER_TEMPLATE_LANG,
            "body_param": when_text})
    # No template. Free text can only land if this patient messaged us inside
    # the last 24h — _wa_touch_window records that on every inbound.
    if _wa_in_service_window(customer_id, phone):
        return outbox_publish("whatsapp.send",
                              {"to": phone, "customer_id": customer_id,
                               "message": full_msg})
    if brain_cache.setnx("warn:reminder_no_template", ttl=3600):
        log.warning("⚠️  reminder skipped — REMINDER_TEMPLATE is unset and the "
                    "patient is outside WhatsApp's 24h service window, so a "
                    "business-initiated free text CANNOT be delivered "
                    "(v16g5 FIX R5-H1). Approve a reminder template in Meta "
                    "Business Manager and set REMINDER_TEMPLATE.")
    analytics.inc("scheduler.reminder_no_template")
    return False


def _publish_followup(customer_id: str, phone: str, full_msg: str) -> bool:
    """v16g4 FIX H2: a cold-lead nudge is BY DEFINITION outside the 24-hour
    customer-service window — that is what makes the lead cold. The free-text
    fallback therefore could not deliver: every nudge burned 5 outbox retries
    and dead-lettered, at ~3 API calls per lead per tick, while the counter
    happily read 'followup_sent'. Template or nothing."""
    phone = _resolve_send_addr(customer_id, phone)   # v16 U3: BSUID-aware
    if not cfg.FOLLOWUP_TEMPLATE:
        log.warning("⚠️  follow-up skipped — FOLLOWUP_TEMPLATE unset; a "
                    "business-initiated free text outside the 24h window "
                    "cannot be delivered (v16g4 FIX H2).")
        analytics.inc("scheduler.followup_no_template")
        return False
    # v16g2 FIX M8: propagate the publish outcome (see _publish_reminder).
    # v16g6 FIX R6-C1: `full_msg` — the per-lead LOCALISED body the caller
    # builds via _t("followup", …) — was discarded, so every cold-lead nudge
    # sent the literal English string "follow-up" as {{1}}. All the ta/hi
    # localisation on this path was dead code. Pass it through, capped to
    # Meta's template-parameter budget. Compare _publish_reminder, which
    # passes when_text — same shape, one branch was wired and one was not.
    return outbox_publish("whatsapp.template", {
        "to": phone, "customer_id": customer_id,
        "template": cfg.FOLLOWUP_TEMPLATE, "lang": cfg.FOLLOWUP_TEMPLATE_LANG,
        "body_param": (full_msg or "follow-up")[:640]})


def _scheduler_send_reminders() -> None:
    """Fire each configured lead-time reminder exactly once per booking."""
    leads = sorted({int(x) for x in cfg.REMINDER_LEAD_HOURS.split(",")
                    if x.strip().lstrip("-").isdigit() and int(x) > 0}, reverse=True)
    if not leads:
        return
    now_utc = datetime.now(timezone.utc)
    horizon = (now_utc + timedelta(hours=leads[0])).isoformat()
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT id, customer_id, enc_phone, slot_start, slot_end, reminders_sent "
                "FROM bookings WHERE status='booked' AND slot_start > ? AND slot_start <= ?",
                (now_utc.isoformat(), horizon))
            rows = [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        log.warning(f"⚠️  reminder scan failed: {exc}")
        return
    # v16g6 FIX R6-M17: memoise consent lookups for the tick — the loop
    # consulted is_opted_out up to twice per due booking, each cold lookup a
    # synchronous DB round-trip inside the single-leader tick; with a few
    # hundred bookings in the horizon that is a query storm, and the storm
    # is what made R6-H9 reachable in the first place.
    _oo_memo: Dict[Tuple[str, str], Tuple[bool, bool]] = {}

    def _oo(cust: str, addr: str) -> Tuple[bool, bool]:
        _k = (cust, addr)
        if _k not in _oo_memo:
            _oo_memo[_k] = is_opted_out_checked(cust, addr)
        return _oo_memo[_k]

    for b in rows:
        try:
            start = _parse_dt(b["slot_start"])
            sent  = {x for x in (b.get("reminders_sent") or "").split(",") if x}
            changed = False
            # v15g2 FIX M2: a booking created INSIDE several lead windows (e.g.
            # 90 min out with REMINDER_LEAD_HOURS="24,2") fired EVERY due lead in
            # the same tick — the patient got two near-identical reminders
            # back-to-back. Fire only the CLOSEST due lead; consume the larger
            # ones silently so they can never fire later either.
            due = [h for h in leads
                   if str(h) not in sent and now_utc >= start - timedelta(hours=h)]
            if due:
                phone = pii_vault.decrypt(b["enc_phone"])
                if not phone or phone == "[ENCRYPTED]":
                    # v16g2 FIX M7: mirror B12 — a decrypt failure is now
                    # VISIBLE (counter + warning) and the leads are NOT
                    # consumed, so a repaired ENCRYPTION_KEY resumes these
                    # reminders instead of them being silently marked handled.
                    analytics.inc("scheduler.reminder_skipped_decrypt")
                    log.warning(f"⚠️  reminder skipped — phone undecryptable "
                                f"(booking id={b.get('id')}, "
                                f"cust={b.get('customer_id')})")
                    continue
                # v16 U3: bookings made by username patients store the
                # BSUID here. Prefer the real number if it was captured
                # since; otherwise the BSUID itself is a valid recipient
                # ('Send to BSUID').
                # v16g5 FIX R5-H4: reminders read `bookings` and never
                # consulted consent at ALL — a patient who texted STOP kept
                # getting appointment reminders. Check the suppression under
                # every spelling the booking may have been keyed on.
                # v16g6 FIX R6-H9: fail-closed is right for the SEND, wrong
                # for the CONSUME. A transient lookup blip returned True here
                # and the block below then marked every due lead handled
                # FOREVER — the patient misses the visit while the dashboard
                # says the reminder went out. Suppressed (known) → consume;
                # unknown → skip THIS tick, keep the leads, retry next tick.
                _checks = [_oo(b["customer_id"], _p) for _p in          # R6-M17
                           dict.fromkeys([phone, _resolve_send_addr(b["customer_id"], phone)])
                           if _p]
                if any(_sup and _known for _sup, _known in _checks):
                    analytics.inc("scheduler.reminder_skipped_optout")
                    for h in due:
                        sent.add(str(h))
                    with _db_pool.get() as conn:
                        _execute(conn, "UPDATE bookings SET reminders_sent=?, "
                                       "updated_at=? WHERE id=?",
                                 (",".join(sorted(sent)), _now(), b["id"]))
                    continue
                if any(not _known for _sup, _known in _checks):
                    analytics.inc("scheduler.reminder_optout_unknown")
                    log.warning(f"⚠️  opt-out state UNKNOWN (lookup failing) "
                                f"— holding reminder for booking "
                                f"id={b.get('id')} until it can be verified "
                                f"(v16g6 FIX R6-H9)")
                    continue
                phone   = _resolve_send_addr(b["customer_id"], phone)
                when    = _fmt_local_dt(b["slot_start"])
                # v14g5 FIX 24: word the lead from the ACTUAL remaining time, not
                # the configured lead bucket (a slot 1h away no longer says "~2h").
                rem_h   = max(0, int(round((start - now_utc).total_seconds() / 3600)))
                # v16g4 FIX L5: "tomorrow" was a raw >=20h test, so a 10 p.m.
                # scan for a 9 a.m. slot the NEXT MORNING (11h) said "in ~11
                # hour(s)" while a Friday-2 p.m. scan for a Saturday-11 a.m.
                # slot (21h) could say "tomorrow" — and a 21h gap that lands
                # the day after tomorrow said "tomorrow" too. Word it from the
                # LOCAL CALENDAR DAY difference, which is what a patient reads.
                _lg = _user_lang(b["customer_id"], phone)     # v16g4 FIX M8
                day_diff = (_to_local(start).date()
                            - _to_local(now_utc).date()).days
                if rem_h <= 1:
                    hrs_txt = _t("t_in_hour", _lg)
                elif day_diff == 0:
                    hrs_txt = _t("t_today", _lg)
                elif day_diff == 1:
                    hrs_txt = _t("t_tomorrow", _lg)
                else:
                    hrs_txt = _t("t_in_hours", _lg, n=rem_h)
                # v16g4 FIX M12: claim this exact (booking, lead) BEFORE
                # publishing. The old order was publish → UPDATE; if the
                # UPDATE failed (DB blip, pool exhaustion) the swallowed
                # exception left reminders_sent unchanged and the NEXT tick
                # re-published the same reminder — a patient could be pinged
                # every minute. The claim is the idempotency fence; losing it
                # still sets changed=True so the missed UPDATE self-heals.
                _claim = f"rem:{b['id']}:{max(due)}"
                if not brain_cache.setnx(_claim, ttl=6 * 3600):
                    log.info(f"♻️  reminder already claimed this window "
                             f"(booking id={b.get('id')}) — repairing row only")
                    for h in due:
                        sent.add(str(h))
                    changed = True
                    published = None                  # skip the publish
                else:
                    published = _publish_reminder(b["customer_id"], phone, when,
                        _t("reminder", _lg, hrs=hrs_txt, when=when))
                if published:                         # v16g2 FIX M8
                    for h in due:      # consume ALL due leads, not only the fired one
                        sent.add(str(h))
                    changed = True
                elif published is False:
                    brain_cache.delete(_claim)        # v16g4 FIX M12: allow retry
                    log.warning(f"⚠️  reminder publish failed — leads kept for "
                                f"retry (booking id={b.get('id')})")
            if changed:
                # v16g5 FIX R5-M6: `sorted(sent, key=lambda x: -int(x))`
                # raised on ANY non-numeric token that ever reached
                # reminders_sent (a partial write, a manual edit, a future
                # lead format). The outer except swallowed it, so that
                # booking's row NEVER updated again and re-entered the due set
                # on every tick — only the 6h setnx claim contained it. Sort
                # defensively and drop junk instead of exploding.
                def _lead_key(x):
                    try:
                        return -int(x)
                    except (TypeError, ValueError):
                        return 0
                _clean = sorted({x for x in sent if str(x).strip()}, key=_lead_key)
                with _db_pool.get() as conn:
                    _execute(conn, "UPDATE bookings SET reminders_sent=?, updated_at=? WHERE id=?",
                             (",".join(_clean), _now(), b["id"]))
        except Exception as exc:
            log.warning(f"⚠️  reminder send failed (id={b.get('id')}): {exc}")
    if rows:
        analytics.inc("scheduler.reminders_scanned")


def _scheduler_followups() -> None:
    """One-time cold-lead nudge for CONSENTED contacts that went quiet."""
    if not cfg.FOLLOWUP_ENABLED:
        return
    if not cfg.FOLLOWUP_TEMPLATE:
        # v16g4 FIX H2: without an approved template nothing here can be
        # delivered — skip the scan entirely (it used to run every tick,
        # publishing undeliverable rows). Warn at most once an hour so the
        # reason is visible without flooding the log.
        if brain_cache.setnx("warn:followup_no_template", ttl=3600):
            log.warning("⚠️  FOLLOWUP_ENABLED=1 but FOLLOWUP_TEMPLATE is unset "
                        "— cold-lead nudges are DISABLED (they cannot be "
                        "delivered outside the 24h window). Approve a template "
                        "in Meta Business Manager and set FOLLOWUP_TEMPLATE.")
        return
    now_utc    = datetime.now(timezone.utc)
    older_than = (now_utc - timedelta(hours=cfg.FOLLOWUP_AFTER_HOURS)).isoformat()
    too_old    = (now_utc - timedelta(hours=cfg.FOLLOWUP_MAX_AGE_HOURS)).isoformat()
    try:
        with _db_pool.get(read_only=True) as conn:
            # v14g5 FIX 16: only chase leads belonging to ACTIVE clinics (was also
            # messaging cold leads of soft-deleted clinics).
            # v16g5 FIX R5-H5: the ONLY time signal was contact CREATION, so a
            # patient who first messaged 25 hours ago and has been in
            # conversation since this morning still matched — and got
            # "just following up, anything I can help with?" mid-chat. Join
            # the session's last_active and require THAT to be stale too.
            # LEFT JOIN + COALESCE so a lead with no session row (an imported
            # contact) still qualifies on created_at alone, as before.
            cur = _execute(conn,
                "SELECT c.id, c.customer_id, c.enc_phone FROM crm_contacts c "
                "JOIN customer_brains b ON b.customer_id=c.customer_id "
                "WHERE (c.followed_up_at IS NULL OR c.followed_up_at='') "
                "AND c.created_at <= ? AND c.created_at >= ? AND c.is_consented=? "
                "AND b.is_active=? "
                # NOT EXISTS, not a LEFT JOIN + GROUP BY: with two sessions
                # (one stale, one live) a join would keep the stale row and
                # nudge an active patient anyway. This asks the right
                # question — "has this subject been active AT ALL recently?"
                "AND NOT EXISTS (SELECT 1 FROM chat_sessions s "
                "                WHERE s.customer_id = c.customer_id "
                "                  AND s.subject_hash = c.phone_hash "
                "                  AND s.last_active > ?) "
                "ORDER BY c.id "
                "LIMIT 200",
                (older_than, too_old, _db_true(), _db_true(), older_than))
            rows = [dict(r) for r in cur.fetchall()]
    except Exception as exc:
        log.warning(f"⚠️  followup scan failed: {exc}")
        return
    for c in rows:
        try:
            phone = pii_vault.decrypt(c["enc_phone"])
            if phone and phone.startswith("ig_"):
                # v16g4 FIX H3: Instagram leads are stored as ig_<sender-id>
                # (crm_add_contact on the IG path). The follow-up scan is
                # channel-blind, so it handed that pseudo-number to the
                # WhatsApp sender — guaranteed Meta rejection, 5 retries,
                # dead-letter, per IG lead. Marked followed (this row is not
                # WhatsApp-deliverable and never will be) but VISIBLE, in the
                # same discipline as the B12 undecryptable branch. IG nudges
                # need their own sender — a separate feature, not a silent
                # failure mode.
                analytics.inc("scheduler.followup_skipped_ig")
                log.warning(f"⚠️  followup skipped — Instagram lead has no "
                            f"WhatsApp address (contact id={c.get('id')}, "
                            f"cust={c.get('customer_id')})")
            elif phone and phone != "[ENCRYPTED]" \
                    and not (_fo := is_opted_out_checked(c["customer_id"], phone))[1]:
                # v16g6 FIX R6-M16 (R6-H9's twin in the followup scanner):
                # the opt-out lookup FAILED — unknown is neither consent nor
                # suppression. The old code fell through to _mark_followed
                # and consumed the lead FOREVER on a DB blip. Hold it (no
                # mark); the next tick retries.
                analytics.inc("scheduler.followup_optout_unknown")
                log.warning(f"⚠️  followup held — opt-out state unknown "
                            f"(contact id={c.get('id')})")
                continue
            elif phone and phone != "[ENCRYPTED]" and _fo[0]:
                # v16g5 FIX R5-H4 · v16g6 R6-M16: a suppressed lead is still
                # marked below (nothing can opt back in today — the day that
                # flow exists it must clear followed_up_at) — but only a
                # KNOWN verdict may consume it.
                analytics.inc("scheduler.followup_skipped_optout")
            elif phone and phone != "[ENCRYPTED]":
                brain = get_customer_brain(c["customer_id"])
                bot   = (brain.get("bot_name") if brain else "") or "our team"
                # v16g4 FIX M8: use the language this lead actually wrote in.
                _lg = _user_lang(c["customer_id"], phone)
                if _publish_followup(c["customer_id"], phone,
                                     _t("followup", _lg, bot=bot)):
                    analytics.inc("scheduler.followup_sent")
                else:                                        # v16g2 FIX M8
                    log.warning(f"⚠️  followup publish failed — lead kept for "
                                f"rescan (contact id={c.get('id')})")
                    continue     # do NOT mark followed; next tick retries
            else:
                # v15g4 FIX B12: these leads were marked followed and vanished
                # with ZERO signal — a key-rotation mistake could silently kill
                # every nudge. Still marked (a decrypt failure is permanent for
                # this row), but now counted and visible.
                analytics.inc("scheduler.followup_skipped_decrypt")
                log.warning(f"⚠️  followup skipped — phone undecryptable "
                            f"(contact id={c.get('id')}, cust={c.get('customer_id')})")
            _mark_followed(c["id"])     # mark regardless, so we never rescan it
        except Exception as exc:
            log.warning(f"⚠️  followup failed (id={c.get('id')}): {exc}")


def _mark_followed(contact_id) -> None:
    try:
        with _db_pool.get() as conn:
            _execute(conn, "UPDATE crm_contacts SET followed_up_at=? WHERE id=?",
                     (_now(), contact_id))
    except Exception:
        pass


def _scheduler_retention_purge() -> None:
    """DPDP retention: drop chat logs + dead bookings older than DATA_RETENTION_DAYS
    (0 = keep forever). Lead/CRM data is NOT auto-purged — use the erasure endpoint
    for that, so a business never loses its book of contacts by surprise."""
    days = cfg.DATA_RETENTION_DAYS
    if days <= 0:
        return
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    try:
        with _db_pool.get() as conn:
            _execute(conn, "DELETE FROM chat_messages WHERE timestamp < ?", (cutoff,))
            _execute(conn, "DELETE FROM chat_sessions WHERE last_active < ?", (cutoff,))
            _execute(conn, "DELETE FROM bookings WHERE status IN ('cancelled','completed') "
                           "AND updated_at < ?", (cutoff,))
        analytics.inc("scheduler.retention_purged")
        log.info(f"🧹 Retention purge: removed chat/booking data older than {days}d.")
    except Exception as exc:
        log.warning(f"⚠️  retention purge failed: {exc}")


def _find_subject_rows(customer_id: str, phone: str,
                       limit: int = 2000) -> List[Dict]:
    """v16g2 FIX M5/N9: resolve a data subject's CRM rows from whatever
    spelling the admin actually holds. U3's whole point is that the clinic
    ends up holding the patient's REAL number while the CRM row is keyed on
    the BSUID hash — a direct hash lookup then matches nothing. Strategy:
      1. direct phone_hash match on typed / digit / country-normalised
         spellings (fast path);
      2. bounded decrypt-compare of enc_phone across the tenant (last-10-digit
         match, ≥10 digits required) — this is what finds the BSUID-keyed row.
    Returns [{id, phone_hash, wa_user_id}] — wa_user_id is the chat-id alias
    the caller must also act under (erasure, consent)."""
    digits = re.sub(r"\D", "", phone or "")
    hashes = {_crm_phone_hash(customer_id, p)
              for p in dict.fromkeys(
                  [phone, digits, _normalize_msisdn(phone or "")]) if p}
    rows:  List[Dict] = []
    exact: List[Dict] = []      # v16g5 FIX R5-M4
    fuzzy: List[Dict] = []
    want_full = _normalize_msisdn(phone or "")
    try:
        with _db_pool.get(read_only=True) as conn:
            has_uid = _column_exists(conn, "crm_contacts", "wa_user_id")
            cur = _execute(conn,
                ("SELECT id, phone_hash, enc_phone, wa_user_id "
                 if has_uid else
                 "SELECT id, phone_hash, enc_phone ")
                + "FROM crm_contacts WHERE customer_id=? LIMIT ?",
                (customer_id, limit))
            for r in cur.fetchall():
                d = dict(r)
                d.setdefault("wa_user_id", "")
                if d["phone_hash"] in hashes:
                    rows.append(d)
                    continue
                if len(digits) >= 10:
                    dec = pii_vault.decrypt(d.get("enc_phone") or "")
                    if (dec and dec != "[ENCRYPTED]"
                            and re.sub(r"\D", "", dec)[-10:] == digits[-10:]):
                        # v16g5 FIX R5-M4: a last-10 match is a COLLISION, not
                        # an identity: +91 98765 43210 and +1 998765 43210
                        # share a tail. Tolerable for a read; this helper also
                        # backs erase_data_subject() (irreversible) and
                        # set_consent_api(). Separate EXACT country-aware
                        # matches from mere tail matches and prefer the exact
                        # set when one exists.
                        if (want_full
                                and _normalize_msisdn(dec) == want_full):
                            exact.append(d)
                        else:
                            fuzzy.append(d)
        # Exact wins outright. A tail-only match is trusted ONLY when it is
        # unambiguous (exactly one) — two candidates means we cannot tell the
        # subjects apart, and guessing would erase a stranger's records.
        if exact:
            rows.extend(exact)
        elif len(fuzzy) == 1:
            rows.extend(fuzzy)
        elif fuzzy:
            log.error(f"🛑 _find_subject_rows: {len(fuzzy)} contacts share the "
                      f"last 10 digits of {pii_vault.mask(phone)} under "
                      f"{customer_id} and none matched exactly — REFUSING to "
                      f"guess (v16g5 FIX R5-M4). Pass the full E.164 number.")
            analytics.inc("dpdp.ambiguous_subject")
    except Exception as exc:
        log.warning(f"⚠️  _find_subject_rows failed: {exc}")
    return rows


def erase_data_subject(customer_id: str, phone: str) -> Dict:
    """v14g4 (DPDP right-to-erasure): delete ALL data for ONE person (by phone)
    under ONE clinic — CRM contact, bookings, RAG memory, chat sessions +
    messages, and every Redis-state key. Returns a small report. Best-effort.
    v15g4 FIX B4: try both the typed and digit spellings.
    v16g2 FIX M5: the subject is ALSO resolved via _find_subject_rows
    (wa_user_id alias + bounded enc_phone decrypt-compare), so erasing a
    USERNAME patient by the real number the clinic actually holds reaches the
    BSUID-keyed CRM row, its bookings, its sessions and its RAG memory too.
    v16g2 FIX M4: the captured real phone (`realphone:` — PLAINTEXT digits,
    30-day TTL), the numreq ask-state, booking-flow state and ghost mutes are
    deleted for every candidate spelling — erasure means erasure, Redis
    included; crm_get_real_phone can no longer answer post-erasure."""
    digits = re.sub(r"\D", "", phone or "")
    cands  = [p for p in dict.fromkeys([phone, digits]) if p]   # unique, ordered
    # v16g2 FIX M5: fold in every alias the CRM can prove belongs to this subject.
    subject_rows = _find_subject_rows(customer_id, phone)
    for _r in subject_rows:
        if _r.get("wa_user_id"):
            cands.append(_r["wa_user_id"])
    cands  = [p for p in dict.fromkeys(cands) if p]
    hashes = list(dict.fromkeys(
        [_crm_phone_hash(customer_id, p) for p in cands]
        + [r["phone_hash"] for r in subject_rows if r.get("phone_hash")]))
    report = {"crm": 0, "bookings": 0, "sessions": 0, "messages": 0, "rag": False}
    # v16g4 FIX L12: flush cached AI replies — see delete_prefix docstring.
    try:
        report["resp_cache_flushed"] = brain_cache.delete_prefix("resp:")
    except Exception:
        pass
    # 1) CRM + bookings — under EVERY resolved hash (v16g2 FIX M5)
    try:
        with _db_pool.get() as conn:
            for h in hashes:
                cur = _execute(conn, "DELETE FROM crm_contacts WHERE customer_id=? AND phone_hash=?",
                               (customer_id, h))
                report["crm"] += getattr(cur, "rowcount", 0) or 0
                cur = _execute(conn, "DELETE FROM bookings WHERE customer_id=? AND phone_hash=?",
                               (customer_id, h))
                report["bookings"] += getattr(cur, "rowcount", 0) or 0
    except Exception as exc:
        log.warning(f"⚠️  erase (crm/bookings) failed: {exc}")
    # 2) Chat sessions + messages. v14g5 FIX 3: resolve sessions from the DB by
    # subject_hash — for EVERY resolved hash (v16g2 FIX M5) — plus any
    # cache-mapped session ids (pre-FIX rows whose subject_hash is empty).
    try:
        with _db_pool.get() as conn:
            sids: List[str] = []
            for h in hashes:
                cur = _execute(conn,
                    "SELECT session_id FROM chat_sessions WHERE customer_id=? AND subject_hash=?",
                    (customer_id, h))
                for r in cur.fetchall():
                    _sid = r["session_id"] if not isinstance(r, tuple) else r[0]
                    if _sid and _sid not in sids:
                        sids.append(_sid)
            for p in cands:                                     # v15g4 FIX B4
                for k in (f"wa_session:{customer_id}:{p}",
                          f"ig_session:{customer_id}:{p}"):
                    _sid = brain_cache.get(k)
                    if _sid and _sid not in sids:
                        sids.append(_sid)
                    brain_cache.delete(k)
            for sid in sids:
                cur = _execute(conn, "DELETE FROM chat_messages WHERE session_id=?", (sid,))
                report["messages"] += getattr(cur, "rowcount", 0) or 0
                cur = _execute(conn, "DELETE FROM chat_sessions WHERE session_id=?", (sid,))
                report["sessions"] += getattr(cur, "rowcount", 0) or 0
    except Exception as exc:
        log.warning(f"⚠️  erase (sessions) failed: {exc}")
    # 3) RAG memory — BOTH channel-shaped uids, under EVERY candidate spelling
    # (v15g4 FIX B4 + v16g2 FIX M5: BSUID aliases included).
    rag_ok = False
    for p in cands:
        rag_ok = rag_forget(customer_id, f"{customer_id}:{p}") or rag_ok
        rag_ok = rag_forget(customer_id, f"ig:{customer_id}:{p}") or rag_ok
    report["rag"] = rag_ok
    # 4) v16g2 FIX M4: Redis state — captured real phone, ask-state, booking
    # flow, ghost mutes — for every candidate spelling. Erasure means erasure.
    for p in cands:
        for k in (f"realphone:{customer_id}:{p}",
                  f"numreq:{customer_id}:{p}",
                  f"numreq_asked:{customer_id}:{p}",
                  f"numreq_window:{customer_id}:{p}",
                  f"numreq_inflight:{customer_id}:{p}",
                  f"bk_offer:{customer_id}:{p}",
                  # v16g6 FIX R6-M1: two keys added since this list was last
                  # touched. wawin is the flag that AUTHORISES free-text
                  # sends — erasure must revoke it with everything else.
                  f"bk_offer_recent:{customer_id}:{p}",
                  f"wawin:{customer_id}:{p}",
                  f"bk_cancel:{customer_id}:{p}",
                  f"ghost:{customer_id}:{p}",
                  f"ghost:ig:{customer_id}:{p}"):
            brain_cache.delete(k)
    # 5) v16g6 FIX R6-C3: the OUTBOX. Queued reminders/follow-ups for this
    # subject held their number in the payload and were still DELIVERED
    # AFTER erasure — the one table this function never touched. Cancel
    # every not-yet-sent row whose `to` matches any candidate spelling
    # (payloads written before this build are cleartext; new ones are
    # sealed — compare via decrypt so both generations match).
    try:
        _digs = {re.sub(r"\D", "", c)[-12:] for c in cands
                 if re.sub(r"\D", "", c)}
        with _db_pool.get() as conn:
            cur = _execute(conn,
                "SELECT id, payload FROM outbox "
                "WHERE status IN ('pending','processing','failed')")
            _kill = []
            for r in cur.fetchall():
                _pid = r["id"] if not isinstance(r, tuple) else r[0]
                _raw = r["payload"] if not isinstance(r, tuple) else r[1]
                try:
                    _p = _raw if isinstance(_raw, dict) else json.loads(_raw)
                except Exception:
                    continue
                if _p.get("customer_id") != customer_id:
                    continue
                _to = pii_vault.decrypt(str(_p.get("to", "")))
                if (_to in cands
                        or re.sub(r"\D", "", _to)[-12:] in _digs):
                    _kill.append(_pid)
            for _i in _kill:
                _execute(conn, "DELETE FROM outbox WHERE id=?", (_i,))
            report["outbox"] = len(_kill)
    except Exception as exc:
        log.warning(f"⚠️  erase (outbox) failed: {exc}")
    analytics.inc("dpdp.subject_erased")
    log.info(f"🗑️  DPDP erase → cust={customer_id} phone={pii_vault.mask(phone)} {report}")
    return report





def _janitor_loop() -> None:
    """v12: tighter cadence + real housekeeping.
    Every OUTBOX_TICK seconds → drain the outbox and prune expired in-process
    cache keys (#35). Roughly hourly → delete stale idempotency keys, finished
    outbox rows (#25), and old webhook_log rows (#32); re-queue any outbox row
    left 'processing' by a crashed worker."""
    tick        = max(5, _env_int("OUTBOX_TICK", "20"))
    med_every   = max(1, int(300 / tick))      # v14g4: ~ every 5 minutes
    n = 0
    # v16g5 FIX R5-H6b: the heavy block used to fire on `n % heavy_every`,
    # where `n` is a PER-PROCESS tick counter reset on every restart. A worker
    # recycled more often than hourly — the norm on Render's free tier — never
    # reached the heavy block AT ALL: bookings never flipped to 'completed',
    # idempotency/webhook_log/done-outbox never pruned, stuck rows never
    # requeued. v16g6 FIX R6-H3: anchor to a SHARED expiring lease — the
    # only clock that survives restarts AND elects one leader fleet-wide.
    while not _shutdown_event.wait(timeout=tick):
        n += 1
        # v16g4 FIX O1: every gunicorn worker ran the drain each tick — N
        # workers = N near-simultaneous claim sweeps hammering the same rows
        # (claims are row-atomic, so no double-send — this is pure wasted DB
        # churn). Same single-leader lease the scheduler uses; a short TTL so
        # a crashed leader is replaced within one tick.
        _ob_lease = brain_cache.lock("outbox:drain", ttl=max(5, tick - 1))
        if _ob_lease:
            try:
                _process_outbox()
            except Exception as exc:
                log.warning(f"⚠️  Janitor (outbox) error: {exc}")
            finally:
                # v16g5 FIX R5-M10: the lease was ACQUIRED every tick and never
                # RELEASED, so it expired on its own ~1s before the next tick.
                # Janitors across workers aren't tick-synchronised, so a worker
                # waking inside that window found it held and skipped — some
                # ticks NOBODY drained, doubling worst-case welcome/reminder
                # latency for no reason. Release it the moment we're done.
                try:
                    # v16g6 FIX R6-H2: delete("lock:outbox:drain") only ever
                    # worked on Redis, where prefix concatenation lined up by
                    # coincidence. The local store writes "__lock__outbox:drain",
                    # so in no-Redis mode the R5-M10 release was a NO-OP and
                    # the skipped-tick behaviour it removed came straight back
                    # — and a raw delete bypasses the holder-token check, so
                    # any worker could free any holder's lease. Use the real
                    # check-and-del release.
                    brain_cache.unlock("outbox:drain", _ob_lease)
                except Exception:
                    pass
        try:
            brain_cache.prune_local()          # v12 #35
        except Exception:
            pass

        # v14g4: scheduler (reminders + cold-lead follow-ups) on a 5-min cadence.
        # Flag-gated OFF by default; needs a long-lived process (true on Render).
        if cfg.ENABLE_SCHEDULER and (n % med_every == 0):
            # v14g5 FIX 7: single-leader lock so reminders/follow-ups run on exactly
            # ONE worker per tick. Every gunicorn worker runs a janitor → without
            # this the same reminder went out once PER worker. Lease is intentionally
            # NOT released early; its TTL (~the cadence) blocks a second run.
            _lease = brain_cache.lock("sched:cycle", ttl=cfg.SCHED_LOCK_TTL)
            if _lease:
                try:
                    _scheduler_send_reminders()
                except Exception as exc:
                    log.warning(f"⚠️  scheduler (reminders) error: {exc}")
                try:
                    _scheduler_followups()
                except Exception as exc:
                    log.warning(f"⚠️  scheduler (followups) error: {exc}")

        # v16g6 FIX R6-H3: R5-H6b swapped a per-process TICK counter for a
        # per-process MONOTONIC timer — `_last_heavy` re-armed on every boot,
        # so a worker recycled faster than hourly (the Render free-tier norm)
        # STILL never reached this block: bookings never flipped to
        # 'completed', idempotency/webhook_log/done-outbox never pruned,
        # stuck rows never requeued — the named failure was unchanged, only
        # the mechanism moved. The gate must live OUTSIDE the process: one
        # shared expiring setnx = hourly cadence AND single-leader election
        # in a single atomic call (no-Redis dev degrades to per-process,
        # the documented single-worker case).
        if not brain_cache.setnx("janitor:heavy:ran", ttl=3600):
            continue

        now_     = datetime.now(timezone.utc)
        day_ago  = (now_ - timedelta(days=1)).isoformat()
        week_ago = (now_ - timedelta(days=7)).isoformat()
        stuck    = (now_ - timedelta(minutes=15)).isoformat()
        # v16g5 FIX R5-H6 (HIGH): all seven statements below shared ONE
        # transaction and ONE `except`. Any single failure — a missing column
        # on a partly-migrated DB, a lock timeout, one bad row — rolled back
        # ALL of them, permanently, once an hour, forever. Bookings never
        # flipped to 'completed' (so the retention purge's completed-branch
        # stayed dead code, defeating FIX N7), and nothing ever pruned. Each
        # statement now runs in its OWN transaction and is fault-isolated, the
        # discipline the migration code has used since v11.
        _chores = [
            # v16g2 FIX N7: past appointments become 'completed' so their
            # enc_phone/enc_name PII stops being immortal.
            ("bookings→completed",
             "UPDATE bookings SET status='completed', updated_at=? "
             "WHERE status='booked' AND slot_end < ?", (_now(), now_.isoformat())),
            ("idempotency prune",
             "DELETE FROM idempotency_keys WHERE created_at < ?", (day_ago,)),
            ("outbox done prune",
             "DELETE FROM outbox WHERE status='done' AND created_at < ?", (day_ago,)),
            # v16g2 FIX M11: a stuck row that has burned its attempt budget
            # becomes 'failed' (visible, cleanable) instead of a zombie the
            # claimer's attempts<5 filter can never pick up again.
            # v15 FIX 7: measure from the CLAIM time, not row creation.
            ("stuck-row requeue",
             "UPDATE outbox SET attempts=attempts+1, next_attempt_at=?, "
             "status = CASE WHEN attempts >= 4 THEN 'failed' ELSE 'pending' END "
             "WHERE status='processing' AND COALESCE(processed_at, created_at) < ?",
             (_iso_in(30), stuck)),
            # v16g2 FIX M11: dead-letters stay visible for a week, then out.
            ("dead-letter prune",
             "DELETE FROM outbox WHERE status='failed' AND created_at < ?", (week_ago,)),
            ("webhook_log prune",
             "DELETE FROM webhook_log WHERE processed_at < ?", (week_ago,)),
            # v16g5 FIX R5-L9 companion: opt-outs are permanent by design and
            # are deliberately NOT pruned here.
            # v16g6 FIX R6-C3: a pending row that no claimer ever picked up
            # (attempts stuck, next_attempt_at pathologies) was retained
            # FOREVER with its payload — nothing pruned status='pending'.
            # A week-old undelivered welcome/reminder is dead either way.
            ("outbox pending age-out",
             "DELETE FROM outbox WHERE status='pending' AND created_at < ?",
             (week_ago,)),
        ]
        _ok = _fail = 0
        for _label, _sql, _prm in _chores:
            try:
                with _db_pool.get() as conn:
                    _execute(conn, _sql, _prm)
                _ok += 1
            except Exception as exc:
                _fail += 1
                log.warning(f"⚠️  Janitor chore '{_label}' failed "
                            f"(others continue): {exc}")
        log.info(f"🧹 Janitor: housekeeping {_ok} ok, {_fail} failed.")
        # v14g4: DPDP retention purge (chat logs + dead bookings) — no-op unless
        # DATA_RETENTION_DAYS > 0. Never touches live CRM/lead data.
        if cfg.ENABLE_SCHEDULER:
            _rlease = brain_cache.lock("sched:retention", ttl=cfg.SCHED_LOCK_TTL)  # FIX 7
            if _rlease:
                try:
                    _scheduler_retention_purge()
                except Exception as exc:
                    log.warning(f"⚠️  Janitor (retention) error: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 🌐  FLASK APP
# ─────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = cfg.SECRET_KEY
# v12 #37: cap request bodies so an attacker can't POST a giant JSON blob and
# blow up RAM — Flask 413s anything larger before it is read into memory.
app.config["MAX_CONTENT_LENGTH"] = cfg.MAX_CONTENT_BYTES

# v12 #14/#30: Render (and every PaaS) sits behind a load balancer, so the
# socket peer is the LB, not the user. Without ProxyFix, get_remote_address()
# returns the LB/Meta IP and the IP rate limiter throttles ALL clinics as one.
# Honour X-Forwarded-For/Proto from exactly one trusted proxy hop.
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
except Exception as _pf_exc:   # pragma: no cover
    log.warning(f"⚠️  ProxyFix unavailable ({_pf_exc}) — client IPs may be the LB's.")

# v16g5 FIX R5-M11: this was a wildcard by default across EVERY route —
# /admin/*, /crm/*, the DPDP erasure endpoint — and read through a raw
# os.getenv instead of cfg (the pattern FIX L8 cleaned up for the Tally
# secret). Webhooks stay open (Meta posts server-side, so CORS is irrelevant
# there); the admin/CRM surface is same-origin unless CORS_ORIGINS names the
# dashboard explicitly. STRICT_PROD refuses the wildcard outright.
_cors_origins = [o.strip() for o in (cfg.CORS_ORIGINS or "").split(",") if o.strip()]
if not _cors_origins:
    if cfg.STRICT_PROD:
        raise SystemExit("STRICT_PROD=1: set CORS_ORIGINS to your dashboard "
                         "origin(s). A wildcard would let any website call "
                         "/admin/* and /crm/* from a logged-in browser.")
    _cors_origins = ["*"]
    log.warning("⚠️  CORS_ORIGINS unset → '*' (dev default). Set it to your "
                "dashboard origin before launch (v16g5 FIX R5-M11).")
CORS(app, resources={
    r"/whatsapp-webhook":  {"origins": "*"},
    r"/instagram-webhook": {"origins": "*"},
    r"/tally-webhook":     {"origins": "*"},
    r"/health":            {"origins": "*"},
    r"/ready":             {"origins": "*"},
    r"/*":                 {"origins": _cors_origins},
})

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[cfg.RATE_LIMIT_DEFAULT],
    storage_uri=cfg.REDIS_URL if cfg.REDIS_URL else "memory://",
)


# v12 #29: under gunicorn --preload, startup() runs in the master BEFORE fork,
# so the janitor thread lives only in the master and dies in the workers. This
# guard lets each worker lazily start its own janitor on first request — the
# flag is per-process, so it's exactly-once per worker.
_worker_janitor_started = False
_worker_janitor_lock    = threading.Lock()


def _ensure_worker_janitor() -> None:
    global _worker_janitor_started
    if _worker_janitor_started:
        return
    with _worker_janitor_lock:
        if _worker_janitor_started:
            return
        alive = any(t.name == "Janitor" and t.is_alive()
                    for t in threading.enumerate())
        if not alive:
            threading.Thread(target=_janitor_loop, name="Janitor", daemon=True).start()
            log.info("🧹 Per-worker janitor started (post-fork self-heal).")
        _worker_janitor_started = True


@app.after_request
def _security_headers(response):
    """OWASP-recommended security headers on every response."""
    response.headers["X-Content-Type-Options"]    = "nosniff"
    response.headers["X-Frame-Options"]           = "DENY"
    # v16g2 FIX C7: X-XSS-Protection removed — deprecated; modern browsers
    # ignore it, and it could re-enable a buggy legacy auditor.
    response.headers["Referrer-Policy"]           = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Cache-Control"]             = "no-store, max-age=0"
    response.headers["Permissions-Policy"]        = "geolocation=(), microphone=()"
    response.headers["X-Request-ID"]              = g.get("request_id", "")
    response.headers["Content-Security-Policy"]   = "default-src 'self'"
    return response


@app.before_request
def _tag_request():
    g.request_id = uuid.uuid4().hex[:12]
    g.start_time = time.monotonic()
    analytics.inc("request.total")
    _ensure_worker_janitor()   # v12 #29


def elapsed_ms() -> int:
    return int((time.monotonic() - g.get("start_time", time.monotonic())) * 1000)


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


def verify_tally_signature(raw_body: bytes, headers: dict) -> bool:
    """Verify Tally webhook signature if secret is configured.
    v15 FIX 3 (CRITICAL): Tally signs HMAC-SHA256 over the raw body and encodes
    it BASE64 in the tally-signature header (per Tally's own docs). The old code
    compared a HEXDIGEST — so the moment TALLY_WEBHOOK_SECRET was set, every
    legitimate onboarding webhook was rejected with 401 and signups silently
    died. Unset secret skips the check in DEV only.
    v16g4 FIX H4: verify_meta_signature refuses unsigned webhooks under
    STRICT_PROD / REQUIRE_WEBHOOK_SIGNATURE — but this twin returned True
    whenever the secret was unset, even in strict prod. That left the
    brain-minting endpoint (which also chose the outbound welcome target)
    open to anyone who found the URL. Now the same fail-closed rule applies.
    v16g4 FIX L8: the secret is read from cfg like every other secret, not a
    per-request os.getenv."""
    tally_secret = cfg.TALLY_WEBHOOK_SECRET
    if not tally_secret:
        if cfg.STRICT_PROD or cfg.REQUIRE_WEBHOOK_SIGNATURE:
            log.error("🛑 Tally webhook REJECTED: TALLY_WEBHOOK_SECRET unset "
                      "under STRICT_PROD/REQUIRE_WEBHOOK_SIGNATURE (v16g4 FIX H4)")
            return False
        return True
    # v16g5 FIX R5-C2: `headers` is now the case-insensitive Werkzeug object
    # (a plain dict still works — the explicit spellings below cover it).
    sig = (headers.get("Tally-Signature", "")
           or headers.get("tally-signature", "")
           or headers.get("TALLY-SIGNATURE", "") or "")
    digest   = hmac.new(tally_secret.encode(), raw_body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(expected, sig)


# ─────────────────────────────────────────────────────────────────────────────
# 🚪  ROUTES
# ─────────────────────────────────────────────────────────────────────────────

# ── Health Check (Kubernetes liveness probe) ──────────────────────────────────
@app.route("/", methods=["GET"])
def root():
    """Friendly landing — visiting the bare Render URL previously 404'd.
    v16g4 FIX L7: the banner advertised the exact build + patch count to any
    anonymous scanner — free recon that maps this deployment to every bug
    fixed AFTER it. Version detail now needs the same token /health uses (or
    DEBUG); the public face is just "online"."""
    body = {
        "engine":  "HEONIX",
        "status":  "online",
        "health":  "/health",
        "ready":   "/ready",
        "metrics": "/metrics",
    }
    if cfg.DEBUG or (cfg.METRICS_TOKEN and _safe_ct_eq(
            request.headers.get("X-Metrics-Token", ""), cfg.METRICS_TOKEN)):
        body["engine"] = ENGINE_BANNER
    return jsonify(body), 200


# ── v32.0 · FIX R32-C1 — the demo provisioning door ──────────────────────────
@app.route("/demo/provision", methods=["POST"])
@limiter.limit(lambda: cfg.DEMO_RATE_LIMIT)
def demo_provision():
    """Mint a SANDBOXED brain for the browser demo.

    WHY THIS EXISTS
    ---------------
    The demo used to mint brains through /tally-webhook. That endpoint is a
    WEBHOOK — Tally to server, HMAC-signed — and v16g4 FIX H4 deliberately
    made it fail closed under REQUIRE_WEBHOOK_SIGNATURE, because it also
    chooses the outbound welcome target and was "open to anyone who found the
    URL". Correct decision. But it means the moment WhatsApp signature
    enforcement is switched on, the demo dies with a 401.

    The wrong fixes, and why:
      * turn REQUIRE_WEBHOOK_SIGNATURE off — trades a real control on the
        WhatsApp door for a demo convenience. The whole product is the claim
        that code checks beat prompt rules; reopening a door to demo that
        claim is self-defeating.
      * put TALLY_WEBHOOK_SECRET in the demo page — the demo is public HTML.
        A secret in a browser is a published secret.

    So: a different door, with different properties.

    WHAT MAKES IT SAFE — structurally, not by promise
    -------------------------------------------------
    1. OFF unless ENABLE_DEMO_PROVISION is set. Fails closed like everything
       else in this file.
    2. Rate limited per IP (DEMO_RATE_LIMIT), unlike the Meta webhooks which
       are limiter-exempt because a signature is their gatekeeper.
    3. customer_id is FORCED into the DEMO_ namespace. It cannot collide with
       a real tenant id and it is greppable in every log and table forever.
    4. It NEVER writes wa_phone_number_id or instagram_id. This is the load-
       bearing property: routing keys are what let a brain RECEIVE and SEND
       real messages, so a demo brain is structurally incapable of reaching a
       real patient — even if the endpoint is abused. The worst case is a junk
       row, not a message to a stranger's phone.
    5. No owner phone, so it can never fire an owner alert (v16g5 FIX R5-C1
       territory).
    6. No welcome message, no outbox write. /tally-webhook sends one; this
       must not.
    7. It refuses to touch a soft-deleted brain (v16g4 FIX L19 rule), and it
       refuses any id that is not DEMO_-prefixed, so it can never overwrite a
       live clinic.
    8. expires_at is stamped in the prompt tail so demo rows are identifiable
       for collection; DEMO_TTL_HOURS controls it.
    """
    if not cfg.ENABLE_DEMO_PROVISION:
        return jsonify({"error": "demo provisioning disabled",
                        "detail": "Set ENABLE_DEMO_PROVISION=true to enable "
                                  "the sandboxed demo door."}), 403
    body = request.get_json(silent=True) or {}
    name = str(body.get("clinic") or body.get("customer_name") or "").strip()
    btype = str(body.get("business_type") or "General Business").strip()
    notes = str(body.get("details") or body.get("extra_notes") or "").strip()
    if not name or len(name) > 120:
        return jsonify({"error": "clinic name required (1-120 chars)"}), 400
    notes = notes[:2000]

    # DEMO_ + short stable hash of the name, so the same clinic name in the
    # same demo session lands on the same brain instead of littering rows.
    _slug = hashlib.sha256(f"demo::{name.lower()}::{btype.lower()}"
                           .encode()).hexdigest()[:10].upper()
    customer_id = f"DEMO_{_slug}"
    if not customer_id.startswith("DEMO_"):          # belt and braces
        return jsonify({"error": "namespace violation"}), 500

    try:
        with _db_pool.get(read_only=True) as conn:
            _cur = _execute(conn, "SELECT is_active FROM customer_brains "
                                  "WHERE customer_id=?", (customer_id,))
            _row = _cur.fetchone()
        if _row is not None and not (_row[0] if isinstance(_row, tuple)
                                     else _row["is_active"]):
            return jsonify({"status": "reactivation_blocked",
                            "customer_id": customer_id}), 200
    except Exception:
        pass

    bot_name, sys_prompt = build_system_prompt(name, btype)
    if notes:
        sys_prompt += f"\n\nAdditional context: {notes}"
    _exp = (datetime.now(timezone.utc)
            + timedelta(hours=cfg.DEMO_TTL_HOURS)).isoformat()
    sys_prompt += (f"\n\n[SANDBOX DEMO BRAIN — no WhatsApp routing, "
                   f"no owner alerts, expires {_exp}]")
    try:
        save_customer_brain(customer_id, name, btype, sys_prompt,
                            bot_name=bot_name)      # NO routing keys. Ever.
    except Exception as e:
        log.error(f"🛑 demo provision failed for {customer_id}: {e}")
        return jsonify({"error": "provisioning failed"}), 500

    log.info(f"🧪 Demo brain provisioned {customer_id} ({name}) — sandboxed, "
             f"no routing keys, expires {_exp}")
    analytics.inc("demo.provision")
    return jsonify({"status": "ok", "customer_id": customer_id,
                    "bot_name": bot_name, "sandbox": True,
                    "expires_at": _exp}), 200


@app.route("/health", methods=["GET"])
def health():
    db_ok = True
    try:
        with _db_pool.get(read_only=True) as conn:
            _execute(conn, "SELECT 1", ())
    except Exception:
        db_ok = False

    # v16g3 FIX R3-L10: with METRICS_TOKEN set, the full body (replica
    # layout, PII-encryption on/off, circuit states) needs the token — public
    # probes get status-only, so /health still works as a plain liveness
    # check for Render/K8s without leaking deployment recon.
    if cfg.METRICS_TOKEN and not _safe_ct_eq(
            request.headers.get("X-Metrics-Token", ""), cfg.METRICS_TOKEN):
        return (jsonify({"status": "UP" if db_ok else "DEGRADED",
                         "timestamp": _now()}),
                200 if db_ok else 503)

    ai_active = [k for k, v in AI_PROVIDERS_ACTIVE.items() if v]
    return jsonify({
        "status":           "UP" if db_ok else "DEGRADED",
        "engine":           f"HEONIX Ultra {ENGINE_VERSION} {ENGINE_GEN}",
        "region":           cfg.REGION,
        "timestamp":        _now(),
        "db_mode":          cfg.DATABASE_MODE,
        "db_healthy":       db_ok,
        "replica_pool":     bool(
            isinstance(_db_pool, PostgreSQLPool) and _db_pool._read),
        "redis_connected":  brain_cache.ping(),   # v14g5 FIX 48: real round-trip
        "ai_providers":     AI_PROVIDERS_ACTIVE,
        "active_ai_chain":  ai_active,
        "pii_encryption":   pii_vault.enabled,
        "whatsapp_ready":   bool(cfg.WHATSAPP_TOKEN and cfg.WHATSAPP_PHONE_ID),
        "instagram_ready":  bool(cfg.INSTAGRAM_TOKEN),
        "graph_api":        cfg.GRAPH_API_VERSION,
        "rag_memory":       _rag_ready,
        "voice_decoder":    bool(AI_PROVIDERS_ACTIVE.get("gemini") or AI_PROVIDERS_ACTIVE.get("openai")),
        "gemini_circuit":   _gemini_breaker.state,
        "openai_circuit":   _openai_breaker.state,
        "claude_circuit":   _claude_breaker.state,
        "whatsapp_circuit": _whatsapp_breaker.state,
        "request_id":       g.get("request_id"),
    }), 200 if db_ok else 503


# ── Readiness Probe (Kubernetes — separate from liveness per k8s best practice) ─
@app.route("/ready", methods=["GET"])
def ready():
    """
    FIX #13: Separate readiness check.
    K8s uses /ready to decide if traffic can be sent — not the same as /health.
    Pod may be alive but not ready (e.g., AI providers still configuring).
    """
    ai_ok = any(AI_PROVIDERS_ACTIVE.values())
    if not ai_ok:
        return jsonify({"ready": False, "reason": "No AI providers configured"}), 503
    # v16g3 FIX R3-M7: a pod with the database down passed readiness and kept
    # receiving traffic it could only 500. Same one-liner /health uses.
    try:
        with _db_pool.get(read_only=True) as conn:
            _execute(conn, "SELECT 1", ())
    except Exception:
        return jsonify({"ready": False, "reason": "Database unavailable"}), 503
    return jsonify({
        "ready":    True,
        "region":   cfg.REGION,
        "ai_chain": [k for k, v in AI_PROVIDERS_ACTIVE.items() if v],
    }), 200


# ── Prometheus Metrics (FIX #15: histograms + P99 latency) ──────────────────
@app.route("/metrics", methods=["GET"])
def metrics():
    # v14g5 FIX 23: if METRICS_TOKEN is set, require it (constant-time) so the
    # endpoint that exposes customer/session/message counts isn't world-readable.
    # Unset = open (dev / private network), preserving prior behaviour.
    if cfg.METRICS_TOKEN and not _safe_ct_eq(
            request.headers.get("X-Metrics-Token", ""), cfg.METRICS_TOKEN):  # v16g3 R3-M1
        return jsonify({"error": "Unauthorized"}), 401
    snap = analytics.snapshot()
    c    = snap["counters"]
    p99  = snap["latency_p99"]

    # v12 #10: COUNT(*) over chat_messages gets very expensive at scale, and a
    # Prometheus scrape storm (or a curious dashboard on refresh) would hammer
    # the DB. Cache the three counts for METRICS_CACHE_TTL seconds.
    cached_counts = brain_cache.get("metrics:counts")
    if isinstance(cached_counts, dict):
        customers = cached_counts.get("customers", -1)
        sessions  = cached_counts.get("sessions", -1)
        messages  = cached_counts.get("messages", -1)
    else:
        try:
            with _db_pool.get(read_only=True) as conn:
                is_pg   = isinstance(_db_pool, PostgreSQLPool)
                active  = True if is_pg else 1
                cur     = _execute(conn,
                    "SELECT COUNT(*) as c FROM customer_brains WHERE is_active=?", (active,))
                customers = cur.fetchone()["c"]
                cur     = _execute(conn, "SELECT COUNT(*) as c FROM chat_sessions", ())
                sessions  = cur.fetchone()["c"]
                cur     = _execute(conn, "SELECT COUNT(*) as c FROM chat_messages", ())
                messages  = cur.fetchone()["c"]
            brain_cache.set("metrics:counts",
                            {"customers": customers, "sessions": sessions,
                             "messages": messages}, ttl=cfg.METRICS_CACHE_TTL)
        except Exception:
            customers = sessions = messages = -1

    # v16g2 FIX C3: every series now carries a TYPE line; sessions/messages
    # are COUNT(*) snapshots that DECREASE after the retention purge — calling
    # them `counter` broke Prometheus rate(); they are gauges. The pointless
    # f-string on the uptime HELP line is gone.
    lines = [
        "# HELP heonix_customers_total Active customer brains",
        "# TYPE heonix_customers_total gauge",
        f"heonix_customers_total {customers}",
        "# HELP heonix_sessions_total Chat sessions",
        "# TYPE heonix_sessions_total gauge",
        f"heonix_sessions_total {sessions}",
        "# HELP heonix_messages_total Chat messages",
        "# TYPE heonix_messages_total gauge",
        f"heonix_messages_total {messages}",
        "# HELP heonix_requests_total HTTP requests processed",
        "# TYPE heonix_requests_total counter",
        f"heonix_requests_total {c.get('request.total', 0)}",
        "# HELP heonix_cache_hit_total Cache hits",
        "# TYPE heonix_cache_hit_total counter",
        f"heonix_cache_hit_total {c.get('cache.hit', 0)}",
        "# HELP heonix_cache_miss_total Cache misses",
        "# TYPE heonix_cache_miss_total counter",
        f"heonix_cache_miss_total {c.get('cache.miss', 0)}",
        "# HELP heonix_ai_gemini_success Gemini success count",
        "# TYPE heonix_ai_gemini_success counter",
        f"heonix_ai_gemini_success {c.get('ai.gemini.success', 0)}",
        "# HELP heonix_ai_openai_success OpenAI success count",
        "# TYPE heonix_ai_openai_success counter",
        f"heonix_ai_openai_success {c.get('ai.openai.success', 0)}",
        "# HELP heonix_ai_claude_success Claude success count",
        "# TYPE heonix_ai_claude_success counter",
        f"heonix_ai_claude_success {c.get('ai.claude.success', 0)}",
        "# HELP heonix_ai_gemini_latency_p99_ms Gemini P99 latency ms",
        "# TYPE heonix_ai_gemini_latency_p99_ms gauge",
        f"heonix_ai_gemini_latency_p99_ms {p99.get('ai.gemini.latency_ms', 0)}",
        "# HELP heonix_ai_openai_latency_p99_ms OpenAI P99 latency ms",
        "# TYPE heonix_ai_openai_latency_p99_ms gauge",
        f"heonix_ai_openai_latency_p99_ms {p99.get('ai.openai.latency_ms', 0)}",
        "# HELP heonix_ai_claude_latency_p99_ms Claude P99 latency ms",
        "# TYPE heonix_ai_claude_latency_p99_ms gauge",
        f"heonix_ai_claude_latency_p99_ms {p99.get('ai.claude.latency_ms', 0)}",
        "# HELP heonix_ai_gemini_circuit Gemini circuit (0=CLOSED,1=OPEN)",
        "# TYPE heonix_ai_gemini_circuit gauge",
        f"heonix_ai_gemini_circuit {1 if _gemini_breaker.state == 'OPEN' else 0}",
        "# HELP heonix_ai_openai_circuit OpenAI circuit",
        "# TYPE heonix_ai_openai_circuit gauge",
        f"heonix_ai_openai_circuit {1 if _openai_breaker.state == 'OPEN' else 0}",
        "# HELP heonix_ai_claude_circuit Claude circuit",
        "# TYPE heonix_ai_claude_circuit gauge",
        f"heonix_ai_claude_circuit {1 if _claude_breaker.state == 'OPEN' else 0}",
        "# HELP heonix_whatsapp_sent WhatsApp messages sent",
        "# TYPE heonix_whatsapp_sent counter",
        f"heonix_whatsapp_sent {c.get('whatsapp.sent', 0)}",
        "# HELP heonix_uptime_seconds Uptime seconds",
        "# TYPE heonix_uptime_seconds gauge",
        f"heonix_uptime_seconds {snap['uptime_secs']}",
    ]
    return "\n".join(lines) + "\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


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
            user_text = scrub_inbound(msg.get("text", {}).get("body", ""))  # R9-C1
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
        _oo_norm = _norm_text(user_text)
        # v29.0 FIX R29-C1: the window now suppresses only the AMBIGUOUS forms,
        # and only when booking is actually enabled — the sibling _bk_pending
        # 45 lines below already gates on cfg.ENABLE_BOOKING, so a stale cache
        # key on a booking-disabled tenant was silently eating opt-outs here
        # while meaning nothing there. Strictly MONOTONE: this can only ever
        # record more opt-outs than v28, never fewer.
        _bk_window = bool(cfg.ENABLE_BOOKING and (
            brain_cache.get(f"bk_cancel:{customer_id}:{from_phone}")
            or brain_cache.get(f"bk_offer:{customer_id}:{from_phone}")))
        if (msg_type in ("text", "button", "interactive")
                and _oo_norm in _OPT_OUT_KEYWORDS
                and not (_bk_window and _oo_norm in _OPT_OUT_AMBIGUOUS_IN_WINDOW)):
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
                session_id, subject_name=profile_name,
                channel="whatsapp"):                     # v16.5 R11-H1
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

    # v16.2 FIX R8-H1: the opt-out handler lived ONLY in the WhatsApp and
    # Instagram webhooks. On /chat a "stop messaging me" fell through to the
    # model, which politely promised to stop while nothing was recorded —
    # demoing a consent feature that does not exist. Same keywords, same
    # l10n keys, same durable write as the real line.
    if _norm_text(req.message) in _OPT_OUT_KEYWORDS:
        # v17.0 R17-C8: this suppressed the demo for EVERY visitor at the
        # clinic — one person typing STOP silenced it for all of them, sitting
        # directly below a per-visitor _gov_uid that got this right.
        _ok   = opt_out_subject(req.customer_id,
                                f"api:{req.customer_id}:"
                                + (session_id or get_remote_address() or "anon"))
        _lang = detect_language(req.message)
        analytics.inc("chat.optout" if _ok else "chat.optout_failed")
        if not _ok:
            log.critical(f"🛑 opt-out NOT persisted on /chat for "
                         f"cust={req.customer_id} — telling the user to retry.")
        return jsonify({
            "reply":      _t("opted_out" if _ok else "optout_failed", _lang),
            "provider":   "system",
            "escalated":  False,
            "session_id": session_id,
            "persisted":  _ok,
            "request_id": g.get("request_id"),
        }), 200

    # ── v16.9 FIX R15-C1 (PATIENT SAFETY) ───────────────────────────────────
    # Audited 31-Jul: govern_message ran on the WhatsApp and Instagram webhooks
    # and NOWHERE else. /chat — the endpoint every demo and every prospect
    # actually touches — skipped the entire pre-AI gate: no emergency 108/112
    # layer, no canned replies, no human-handoff mute. Two consequences, both
    # bad. A patient in crisis on this path got whatever the model felt like
    # saying, or a bare 503 when Gemini was down; and the safety layer that is
    # the product's whole differentiator was invisible in the one place it gets
    # judged. It is pure Python and runs before any model call, so it also
    # answers when the AI is unavailable.
    # The ghost-mute and dedupe state inside govern_message are keyed on this
    # uid. On WhatsApp that is one patient; here it must be one CONVERSATION,
    # not one clinic — keying it on customer_id alone would let a single demo
    # visitor's emergency silence the demo for every other visitor for 15
    # minutes. Falls back to the request id so a brand-new session still gets
    # its own bucket.
    # v17.0 FIX R16-C7: R15 fell back to the REQUEST id when session_id was
    # empty — and it is empty until the AI succeeds and the client echoes it
    # back. A key that changes every message is not a key: the emergency mute
    # and the human-handoff mute were both dead on the demo path, exactly
    # where R15-C1 had just put them. The caller's stable identity is the
    # session when there is one, else the remote address.
    _gov_uid = ("api:" + req.customer_id + ":"
                + (session_id or get_remote_address() or "anon"))
    _gov = govern_message(
        req.message, _gov_uid,
        bot_name=(brain.get("bot_name") or ""),
        owner_phone=(brain.get("owner_phone") or ""),
        healthcare=_brain_is_health(brain))
    # Alerts are deliberately NOT dispatched here: /chat is the public demo and
    # v16g2 FIX M9 established that a demo must never page a real clinic owner.
    # The emergency REPLY still reaches the patient — that is the part that
    # matters to whoever is typing.
    if _gov["alerts"]:
        analytics.inc("chat.gov_alert_suppressed")
    # v17.0 FIX R16-C8: R15 set the mute AND suppressed the alert, so a demo
    # patient who asked for a human got one canned line and then permanent
    # silence with nobody notified — strictly worse than R14, which at least
    # kept talking. On the demo there is no owner to page, so the mute must
    # not be honoured either: say the line, then carry on answering.
    if _gov["muted"] and not _gov["reply"]:
        analytics.inc("chat.gov_mute_ignored_demo")
    # v17.0 R17-C6: R16 had an `elif _gov["muted"]` arm here that could never
    # run — govern_message only sets muted=True in the branch that returns
    # reply=None, so the first condition always won. It also left R16-C7's
    # carefully-scoped uid with no consumer at all: C7 built a stable key and
    # C8 then ignored the mute unconditionally, so the two cancelled out.
    # Resolution: on the demo the mute is genuinely the wrong behaviour (there
    # is no owner to page and nobody is coming), so it is ignored on purpose —
    # once, explicitly, with the counter above — and the uid still earns its
    # keep because govern_message's per-caller dedupe reads it.
    if _gov["reply"]:
        analytics.inc("chat.gov_reply")
        # v17.0 FIX R16-C9: R15 returned the governed reply and wrote nothing.
        # An emergency message left ZERO record it ever arrived — no transcript
        # for the clinic, nothing to review, nothing to prove. The crisis turn
        # is the one turn you most need on disk.
        try:
            session_id = session_id or create_session(req.customer_id,
                                                      channel="api")
            save_messages_batch(session_id, [
                ("user",  req.message,    "api",    0),
                ("model", _gov["reply"],  "system", 0),
            ])
            increment_chat_count(req.customer_id)
            _gov_persisted = True
        except Exception as exc:
            # R17-C7: if create_session succeeded but the batch threw, the new
            # session id was still returned alongside persisted:false — the
            # client then kept writing into a session with no first turn.
            _gov_persisted = False
            log.warning(f"\u26a0\ufe0f  /chat governed turn not persisted: {exc}")
        return jsonify({
            "reply":      _gov["reply"],
            "provider":   "system",
            # R16-M3: R15 reported escalated=true while suppressing the alert.
            # On the demo nobody is paged, so the field said something untrue.
            "escalated":  False,
            "session_id": session_id,
            "persisted":  _gov_persisted,
            "request_id": g.get("request_id"),
        }), 200

    # ── v19.0 · FIX R19-C1 (REVENUE-CRITICAL) ───────────────────────────────
    # Audited 4-Aug: handle_booking was reachable ONLY from the WhatsApp
    # webhook. /chat — the endpoint every demo and every prospect actually
    # touches — sent "appointment venum" straight to the model, which answered
    # with a friendly sentence and booked nothing. So the deterministic slot
    # machine that is the entire reason a clinic would pay for this was
    # invisible in the one place it gets judged, and the demo showed a
    # chatbot rather than a receptionist. Same position in the pipeline as the
    # webhook: after opt-out, after govern_message, before the AI.
    #
    # Identity: bookings key on from_phone, and there is no phone here. The
    # engine has been identity-neutral since v16 (BSUID patients), so an
    # "api:" identity flows through unchanged. It must be STABLE per visitor
    # and UNIQUE across visitors — the same requirement R16-C7 established
    # for _gov_uid, and for the same reason: keyed on customer_id alone, one
    # visitor's slot offer would be handed to the next visitor, and
    # MAX_ACTIVE_BOOKINGS_PER_PHONE would be a shared clinic-wide cap instead
    # of a per-visitor one. Reuse the governance identity verbatim.
    #
    # The session must exist BEFORE this runs: _booking_dispatch persists
    # first and sends second (the v14g5 FIX 50 standard), and a None
    # session_id would throw inside the try and silently lose the audit trail
    # of a real booking.
    if cfg.ENABLE_BOOKING and cfg.BOOKING_ON_API:
        _bk_sink: List[str] = []
        _bk_session = session_id
        try:
            if not _bk_session:
                _bk_session = create_session(req.customer_id, channel="api")
            # v19.0 R19-C1d: this first used _gov_uid, and a live run caught
            # it inside one turn. _gov_uid falls back to the REMOTE ADDRESS
            # when session_id is empty — which it is on the very first
            # message — and switches to the session id from turn two onward.
            # The slot offer was therefore cached under one identity and
            # looked up under another: the patient got a slot list, typed
            # "1", and the pick fell through to the AI. Exactly the R16-C7
            # failure, one layer down. The session is created immediately
            # above and echoed back to the client, so it is stable from the
            # first turn — key on that and nothing else.
            _bk_identity = f"api:{req.customer_id}:{_bk_session}"
            _bk_handled = handle_booking(
                brain, _bk_identity, req.message, "", "", req.customer_id,
                _bk_session, subject_name="", channel="api", sink=_bk_sink)
        except Exception as _bke:
            # A booking failure must never take down the turn — fall through
            # to the AI, which at least keeps the conversation alive.
            analytics.inc("chat.booking_error")
            log.error(f"❌ /chat booking failed (cust={req.customer_id}): {_bke}")
            _bk_handled = False
        if _bk_handled and _bk_sink:
            analytics.inc("chat.booking_handled")
            return jsonify({
                "reply":      "\n\n".join(_bk_sink),
                "provider":   "booking",
                "escalated":  False,
                "session_id": _bk_session,
                "persisted":  True,
                "request_id": g.get("request_id"),
            }), 200
        if _bk_handled and not _bk_sink:
            # Handled but produced no text: impossible today (handle_booking
            # returns True only after dispatching an action) — but if a future
            # branch ever does, returning an empty reply is worse than letting
            # the AI answer. Say so loudly rather than shipping silence.
            analytics.inc("chat.booking_empty")
            log.error("❌ R19-C1: handle_booking returned True with no captured "
                      "reply on /chat — falling through to the AI.")
        session_id = _bk_session
        _new_session = False

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


# ── Admin: Login (JWT issue) ──────────────────────────────────────────────────
@app.route("/admin/login", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
def admin_login():
    # v15g4 FIX C1: without pyjwt the login "succeeded" with an EMPTY token
    # (generate_jwt returns ""), which then failed every authenticated call.
    if not JWT_AVAILABLE:
        return jsonify({"error": "Auth unavailable — pyjwt is not installed "
                        "on this deployment"}), 503
    try:
        _body = request.get_json(silent=True)
        # v16g6 FIX R6-M8: non-dict JSON gave a cheap unauthenticated 500.
        req = AdminLoginValidator(**(_body if isinstance(_body, dict) else {}))
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "detail": exc.errors()}), 422

    with _db_pool.get(read_only=True) as conn:
        cur = _execute(conn,
            "SELECT user_id, hashed_pw, role, tenant_id FROM admin_users "
            "WHERE username=? AND is_active=?",   # v16g4 FIX M10
            (req.username, True if isinstance(_db_pool, PostgreSQLPool) else 1))
        row = cur.fetchone()

    if not row:
        # v15g4 FIX C2: an unknown username returned in ~1ms while a known one
        # cost a ~250ms bcrypt check — a clean timing oracle for enumerating
        # valid admin usernames. Burn the same work on the miss path.
        global _TIMING_PAD
        if _TIMING_PAD is None:
            _TIMING_PAD = hash_password("heonix-timing-pad-not-a-secret")
        verify_password(req.password, _TIMING_PAD)
        analytics.inc("admin.login.fail")
        return jsonify({"error": "Invalid credentials"}), 401
    if not verify_password(req.password, row["hashed_pw"]):
        analytics.inc("admin.login.fail")
        return jsonify({"error": "Invalid credentials"}), 401

    _tenant = (row["tenant_id"] or "") if "tenant_id" in row.keys() else ""
    token = generate_jwt(row["user_id"], row["role"], tenant=_tenant)  # v16g4 FIX M10
    audit(row["user_id"], "admin.login", "admin_users", ip=request.remote_addr)
    analytics.inc("admin.login.success")
    resp = {
        "token":      token,
        "user_id":    row["user_id"],
        "role":       row["role"],
        "expires_in": f"{cfg.JWT_EXPIRY_HOURS}h",
    }
    if _tenant:
        resp["tenant_id"] = _tenant
    return jsonify(resp), 200


# ── Admin: Logout (JWT revocation) ────────────────────────────────────────────
@app.route("/admin/logout", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)
@require_jwt(min_role="viewer")
def admin_logout():
    """v16g6 FIX R6-C5: revoke_jwt shipped in R5 with ZERO call sites — the
    denylist was checked on every request and nothing could ever write to it,
    so a leaked admin token stayed valid for the full JWT_EXPIRY_HOURS with no
    kill switch (revoke_jwt's own docstring promised this route existed).
    This is the missing write half: ban this token's jti until its natural
    expiry — fleet-wide when Redis backs the cache."""
    _jti = g.jwt_user.get("jti", "")
    _exp = int(g.jwt_user.get("exp", 0) or 0)
    _ttl = max(60, _exp - int(time.time())) if _exp else 0
    revoke_jwt(_jti, ttl=_ttl)
    audit(g.jwt_user.get("sub", "unknown"), "admin.logout", "admin_users",
          ip=request.remote_addr)
    analytics.inc("admin.logout")
    return jsonify({"status": "logged_out"}), 200


# ── Admin: Create Admin User ───────────────────────────────────────────────────
@app.route("/admin/user", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="superadmin")
def create_admin_user():
    data  = request.get_json(silent=True) or {}
    uname = data.get("username", "").strip()
    pw    = data.get("password", "")
    role  = data.get("role", "admin")
    tenant_id = str(data.get("tenant_id", "") or "").strip()  # v16g4 FIX M10
    if not uname or not pw or role not in ROLES:
        return jsonify({"error": "username, password, and valid role required"}), 400
    if len(pw) < 8:                                          # v16g2 FIX L4
        return jsonify({"error": "password must be at least 8 characters"}), 400
    if tenant_id and role == "superadmin":                    # v16g4 FIX M10
        return jsonify({"error": "superadmin cannot be tenant-scoped"}), 400

    user_id   = f"adm_{uuid.uuid4().hex[:12]}"
    hashed_pw = hash_password(pw)
    try:
        with _db_pool.get() as conn:
            _execute(conn,
                "INSERT INTO admin_users (user_id, username, hashed_pw, role, "
                "created_at, tenant_id) VALUES (?,?,?,?,?,?)",   # v16g4 FIX M10
                (user_id, uname, hashed_pw, role, _now(), tenant_id))
    except Exception as exc:
        # v16g3 FIX R3-M8 + v16g4 FIX M11: only a REAL unique-violation is
        # "already exists" — string-sniffing "constraint" also matched CHECK/
        # NOT-NULL failures, turning schema bugs into a misleading 409.
        if _is_unique_violation(exc):
            return jsonify({"error": "Username already exists"}), 409
        log.error(f"❌ create_admin_user failed: {exc}")
        return jsonify({"error": "Database error creating user"}), 500

    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "admin.create_user", user_id, {"role": role}, request.remote_addr)
    return jsonify({"status": "created", "user_id": user_id, "role": role}), 201


# ── Admin: Customer Stats ─────────────────────────────────────────────────────
@app.route("/admin/customer/<customer_id>/stats", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="viewer")
def customer_stats(customer_id: str):
    brain = get_customer_brain(customer_id)
    if not brain:
        return jsonify({"error": "Not found"}), 404
    with _db_pool.get(read_only=True) as conn:
        sessions = _execute(conn,
            "SELECT COUNT(*) as c FROM chat_sessions WHERE customer_id=?",
            (customer_id,)).fetchone()["c"]
        messages = _execute(conn,
            "SELECT COUNT(*) as c FROM chat_messages cm "
            "JOIN chat_sessions cs ON cm.session_id=cs.session_id "
            "WHERE cs.customer_id=?",
            (customer_id,)).fetchone()["c"]
        leads = _execute(conn,
            "SELECT COUNT(*) as c FROM crm_contacts WHERE customer_id=?",
            (customer_id,)).fetchone()["c"]
    return jsonify({
        "customer_id":    customer_id,
        "name":           brain["customer_name"],
        "business_type":  brain["business_type"],
        "region":         brain.get("region", cfg.REGION),
        "is_active":      bool(brain["is_active"]),
        "total_sessions": sessions,
        "total_messages": messages,
        "total_chats":    brain["total_chats"],
        "crm_leads":      leads,
        "last_updated":   str(brain["updated_at"]),
    }), 200


# ── Admin: Soft Delete Customer ───────────────────────────────────────────────
@app.route("/admin/customer/<customer_id>", methods=["DELETE"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="superadmin")
def delete_customer(customer_id: str):
    brain = get_customer_brain(customer_id)
    if not brain:
        return jsonify({"error": "Not found"}), 404
    old_wa_pid = (brain.get("wa_phone_number_id") or "")
    old_ig_id  = (brain.get("instagram_id") or "")
    is_pg = isinstance(_db_pool, PostgreSQLPool)
    with _db_pool.get() as conn:
        # v14g5 FIX 40: also release the routing identifiers. The unique index on
        # wa_phone_number_id otherwise keeps a DELETED clinic's number reserved
        # forever, so it could never be re-attached to a new clinic.
        clear_route = (_column_exists(conn, "customer_brains", "wa_phone_number_id")
                       and _column_exists(conn, "customer_brains", "instagram_id"))
        # v15g4 FIX B13: also blank the ENCRYPTED TOKENS — a soft-deleted
        # clinic's live Meta secrets were parked on the dead row forever.
        clear_toks = (_column_exists(conn, "customer_brains", "wa_token_enc")
                      and _column_exists(conn, "customer_brains", "ig_token_enc"))
        if clear_route and clear_toks:
            _execute(conn,
                "UPDATE customer_brains SET is_active=?, wa_phone_number_id=?, "
                "instagram_id=?, wa_token_enc=?, ig_token_enc=?, updated_at=? "
                "WHERE customer_id=?",
                (False if is_pg else 0, "", "", "", "", _now(), customer_id))
        elif clear_route:
            _execute(conn,
                "UPDATE customer_brains SET is_active=?, wa_phone_number_id=?, "
                "instagram_id=?, updated_at=? WHERE customer_id=?",
                (False if is_pg else 0, "", "", _now(), customer_id))
        else:
            _execute(conn,
                "UPDATE customer_brains SET is_active=?, updated_at=? WHERE customer_id=?",
                (False if is_pg else 0, _now(), customer_id))
    brain_cache.delete(f"brain:{customer_id}")         # v16g6 FIX R6-L6
    # bust every routing cache that could still point at this (now freed) number
    if old_wa_pid:
        brain_cache.delete(f"wapid:{old_wa_pid}")
        brain_cache.delete(f"wa_route:{old_wa_pid}")   # v15g4 FIX B2 (same class)
    if old_ig_id:
        brain_cache.delete(f"igid:{old_ig_id}")
    brain_cache.delete("wa_route:__single__")
    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "customer.delete", customer_id, ip=request.remote_addr)
    analytics.inc("customer.deleted")
    log.info(f"🗑️  Soft-deleted → {customer_id} (released wa_pid={old_wa_pid or '(none)'})")
    return jsonify({"status": "deleted", "customer_id": customer_id}), 200


# ── v13 Admin: Attach a clinic's OWN WhatsApp / Instagram credentials ─────────
@app.route("/admin/customer/<customer_id>/channel", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="superadmin")
def set_customer_channel(customer_id: str):
    """v13 TRUE MULTI-TENANT: securely attach a clinic's OWN WhatsApp business
    number + token (and/or Instagram account + token). Tokens are AES-256-GCM
    encrypted at rest. Rejects (409) if the WhatsApp number already belongs to a
    DIFFERENT clinic — both here (friendly error) and at the DB unique index
    (hard safety net). NEVER expose this on a public Tally form — JWT only.
    Body: {wa_phone_number_id, wa_token, instagram_id, ig_token}"""
    brain = get_customer_brain(customer_id)
    if not brain:
        return jsonify({"error": "Not found"}), 404
    # v15g4 FIX B2: remember the CURRENT routing ids — after the update we must
    # bust their cache entries too, or inbound traffic on the OLD number keeps
    # routing to this clinic (stale brain + creds) for up to ROUTE_CACHE_TTL.
    old_wa_pid = (brain.get("wa_phone_number_id") or "")
    old_ig_id  = (brain.get("instagram_id") or "")
    body   = request.get_json(silent=True) or {}
    wa_pid = (body.get("wa_phone_number_id") or "").strip()
    wa_tok = (body.get("wa_token") or "").strip()
    ig_id  = (body.get("instagram_id") or "").strip()
    ig_tok = (body.get("ig_token") or "").strip()

    # v15g4 FIX C6: Meta phone-number ids are numeric — a pasted typo silently
    # routed nothing (webhooks simply never matched). Reject it up-front.
    if wa_pid and not wa_pid.isdigit():
        return jsonify({"error": "wa_phone_number_id must be the numeric id "
                        "from Meta (WhatsApp → API Setup), not a phone number "
                        "or a name"}), 400
    # v16g4 FIX L18: twin of FIX C6 — IG account ids are numeric too; a pasted
    # @handle attached fine and then simply never matched an inbound webhook.
    if ig_id and not ig_id.isdigit():
        return jsonify({"error": "instagram_id must be the numeric IG account "
                        "id from Meta, not an @handle"}), 400

    # 🔴 friendly pre-check: this number already attached to another clinic?
    if wa_pid:
        existing = get_brain_by_wa_phone_id(wa_pid)
        if existing and existing.get("customer_id") != customer_id:
            return jsonify({"error": "wa_phone_number_id already attached to "
                            f"{existing['customer_id']}"}), 409

    # v14g5 FIX 1: build the UPDATE from ONLY the channel keys actually present in
    # the request body. Attaching just Instagram must never blank out an existing
    # WhatsApp number/token (and vice-versa). A bare key with empty value is an
    # explicit "clear this field".
    sets: list[str] = []
    vals: list[Any] = []
    if "wa_phone_number_id" in body:
        sets.append("wa_phone_number_id=?"); vals.append(wa_pid)
    if "wa_token" in body:
        sets.append("wa_token_enc=?");       vals.append(pii_vault.encrypt(wa_tok) if wa_tok else "")
    if "instagram_id" in body:
        sets.append("instagram_id=?");       vals.append(ig_id)
    if "ig_token" in body:
        sets.append("ig_token_enc=?");       vals.append(pii_vault.encrypt(ig_tok) if ig_tok else "")
    if not sets:
        return jsonify({"error": "No channel fields provided "
                        "(wa_phone_number_id, wa_token, instagram_id, ig_token)"}), 400
    sets.append("channel_status=?"); vals.append("ok")
    sets.append("updated_at=?");     vals.append(_now())
    vals.append(customer_id)

    try:
        with _db_pool.get() as conn:
            _execute(conn,
                "UPDATE customer_brains SET " + ", ".join(sets) +
                " WHERE customer_id=?", tuple(vals))
    except Exception as exc:
        # DB-level unique-index violation → 409 (the real safety net)
        if "uq_brain_wa_pid" in str(exc) or "unique" in str(exc).lower():
            return jsonify({"error": "wa_phone_number_id already in use"}), 409
        log.error(f"❌ set channel failed for {customer_id}: {exc}")
        return jsonify({"error": "Update failed"}), 500

    # bust every cache key that could hold the old routing/creds
    # v15g4 FIX B2: OLD ids and the wa_route:* cid entries included — the old
    # code busted only the NEW wapid, leaving the previous number's routing
    # (and this clinic's stale creds) served from cache for up to 10 minutes.
    brain_cache.delete(f"brain:{customer_id}")         # v16g6 FIX R6-L6
    for pid in {wa_pid, old_wa_pid}:
        if pid:
            brain_cache.delete(f"wapid:{pid}")
            brain_cache.delete(f"wa_route:{pid}")
    for iid in {ig_id, old_ig_id}:
        if iid:
            brain_cache.delete(f"igid:{iid}")
    brain_cache.delete("wa_route:__single__")
    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "customer.channel", customer_id,
          {"wa_pid": wa_pid, "ig": bool(ig_id)}, request.remote_addr)
    analytics.inc("customer.channel_set")
    log.info(f"🔗 Channel attached → {customer_id} wa_pid={wa_pid or '(none)'}")
    return jsonify({"status": "ok", "customer_id": customer_id,
                    "wa_phone_number_id": wa_pid,
                    "instagram_id": ig_id,
                    "channel_status": "ok"}), 200


# ── v13 Admin: Onboarding smoke-test — is this clinic's token actually alive? ──
@app.route("/admin/customer/<customer_id>/smoke-test", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="superadmin")
def smoke_test_channel(customer_id: str):
    """v13 god-mode weapon: in ~2 seconds, KNOW whether a freshly-attached clinic
    token works — before the clinic's first patient finds out the hard way. Sends
    ONE real WhatsApp to the number you pass (the clinic owner's phone), using the
    clinic's OWN creds, and reports alive / dead-token / misconfigured.
    Body: {to: '<owner phone in intl format>'}"""
    if not cfg.SMOKE_TEST_ENABLED:
        return jsonify({"error": "Smoke test disabled (set SMOKE_TEST_ENABLED=1)"}), 403
    brain = get_customer_brain(customer_id)
    if not brain:
        return jsonify({"error": "Not found"}), 404
    to = ((request.get_json(silent=True) or {}).get("to") or "").strip()
    if not _is_bsuid(to):                          # v16 U2: BSUIDs pass as-is
        to = re.sub(r"[^\d+]", "", to)
    if len(to) < 7:
        return jsonify({"error": "Provide 'to' = a valid phone in international format"}), 400

    pid, tok = brain_wa_creds(brain)
    if not pid or not tok:
        return jsonify({"channel": "whatsapp", "ok": False,
                        "reason": "no_credentials",
                        "hint": "Attach creds via POST /admin/customer/"
                                f"{customer_id}/channel first."}), 200

    # synchronous send so we can report the actual result (not fire-and-forget)
    # v16g4 FIX M6: the owner's number is usually COLD (never messaged this
    # line) — a free text passes the API (proving the token) but is silently
    # dropped by the 24h-window rule, so "ALIVE" + no phone buzz sent you
    # chasing a phantom bug. Use an approved template when one exists (always
    # delivers); otherwise still run the free-text token check but SAY the
    # delivery caveat out loud in the response.
    _smoke_body = (f"✅ HEONIX smoke-test: {brain.get('bot_name') or 'your AI'} "
                   f"is live for {brain.get('customer_name', customer_id)}.")
    _tmpl = cfg.WELCOME_TEMPLATE or cfg.REMINDER_TEMPLATE
    _delivery_note = None
    try:
        if _tmpl:
            _wa_send_template(to, _tmpl,
                              cfg.WELCOME_TEMPLATE_LANG if cfg.WELCOME_TEMPLATE
                              else cfg.REMINDER_TEMPLATE_LANG,
                              _smoke_body, pid, tok)
        else:
            _wa_send_text(to, _smoke_body, pid, tok)
            _delivery_note = ("Token is valid, but this was FREE TEXT — it "
                              "only DELIVERS if that phone messaged this line "
                              "in the last 24h. For a guaranteed test buzz, "
                              "approve a template and set WELCOME_TEMPLATE.")
        with _db_pool.get() as conn:
            if _column_exists(conn, "customer_brains", "channel_status"):
                _execute(conn,
                    "UPDATE customer_brains SET channel_status=?, updated_at=? "
                    "WHERE customer_id=?", ("ok", _now(), customer_id))
        brain_cache.delete(f"brain:{customer_id}")     # v16g6 FIX R6-L6
        analytics.inc("smoke_test.pass")
        _resp = {"channel": "whatsapp", "ok": True,
                 "wa_phone_number_id": pid,
                 "message": "Test message sent — token is ALIVE."}
        if _delivery_note:
            _resp["delivery_note"] = _delivery_note   # v16g4 FIX M6
        return jsonify(_resp), 200
    except WhatsAppAuthError as exc:
        _flag_channel_reauth(customer_id, f"smoke-test code={exc.code}")
        analytics.inc("smoke_test.auth_fail")
        return jsonify({"channel": "whatsapp", "ok": False,
                        "reason": "dead_token", "code": exc.code,
                        "hint": "Token expired/revoked. Re-attach a fresh token via "
                                f"POST /admin/customer/{customer_id}/channel."}), 200
    except Exception as exc:
        analytics.inc("smoke_test.error")
        return jsonify({"channel": "whatsapp", "ok": False,
                        "reason": "send_failed", "detail": str(exc)[:300]}), 200


# ── v13 Admin: Tenant-health dashboard — which clinics are dark right now? ─────
@app.route("/admin/tenants/health", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="viewer")
def tenants_health():
    """v13: fleet view. How many clinics are healthy vs need a token re-attach,
    and exactly which ones — so you fix dark clinics proactively, not reactively."""
    is_pg  = isinstance(_db_pool, PostgreSQLPool)
    active = True if is_pg else 1
    healthy = needs_reauth = total = 0
    dark: List[Dict] = []
    try:
        with _db_pool.get(read_only=True) as conn:
            has_status = _column_exists(conn, "customer_brains", "channel_status")
            cur = _execute(conn,
                "SELECT COUNT(*) AS c FROM customer_brains WHERE is_active=?", (active,))
            total = cur.fetchone()["c"]
            if has_status:
                # v16g4 FIX L3: needs_reauth came from len(dark) — capped at
                # the LIMIT 200 detail list, so a fleet with 250 dark clinics
                # reported 200 dark / 50 "healthy". Count separately; the
                # list stays a 200-row sample for the response body.
                cur = _execute(conn,
                    "SELECT COUNT(*) AS c FROM customer_brains "
                    "WHERE is_active=? AND channel_status=?",
                    (active, "needs_reauth"))
                needs_reauth = cur.fetchone()["c"]
                cur = _execute(conn,
                    "SELECT customer_id, customer_name, channel_status, updated_at "
                    "FROM customer_brains WHERE is_active=? AND channel_status=? "
                    "ORDER BY updated_at DESC LIMIT 200",
                    (active, "needs_reauth"))
                for r in cur.fetchall():
                    dark.append({"customer_id": r["customer_id"],
                                 "name": r["customer_name"],
                                 "since": str(r["updated_at"])})
                healthy = max(0, total - needs_reauth)
            else:
                healthy = total
    except Exception as exc:
        log.warning(f"⚠️  tenants/health query failed: {exc}")
        return jsonify({"error": "query_failed"}), 500

    return jsonify({
        "engine":             "HEONIX Ultra v16.0 GEN-3",
        "region":             cfg.REGION,
        "active_tenants":     total,
        "healthy":            healthy,
        "needs_reauth":       needs_reauth,
        "needs_reauth_list":  dark,
        "whatsapp_circuit":   _whatsapp_breaker.state,
        "instagram_circuit":  _instagram_breaker.state,
    }), 200


# ── Admin: List All Customers ─────────────────────────────────────────────────
@app.route("/admin/customers", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="viewer")
def list_customers():
    page     = _int_arg("page", 1, 1, 10**6)          # v15g4 FIX C3
    per_page = _int_arg("per_page", 50, 1, 100)        # v15g4 FIX C3
    offset   = (page - 1) * per_page
    is_pg    = isinstance(_db_pool, PostgreSQLPool)
    active   = True if is_pg else 1
    with _db_pool.get(read_only=True) as conn:
        total_row = _execute(conn,
            "SELECT COUNT(*) as c FROM customer_brains WHERE is_active=?", (active,)).fetchone()
        total     = total_row["c"] if total_row else 0
        rows      = _execute(conn,
            "SELECT customer_id, customer_name, business_type, plan_tier, "
            "total_chats, region, created_at FROM customer_brains "
            "WHERE is_active=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (active, per_page, offset)).fetchall()
    return jsonify({
        "customers": [dict(r) for r in rows],
        "total":     total,
        "page":      page,
        "per_page":  per_page,
    }), 200


# ── CRM: Add Contact ──────────────────────────────────────────────────────────
@app.route("/crm/contact", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="admin")
def crm_add_contact_api():
    data = request.get_json(silent=True) or {}
    try:
        contact = CRMContactValidator(**data)
    except ValidationError as exc:
        return jsonify({"error": "Validation failed", "detail": exc.errors()}), 422

    if _tenant_forbidden(contact.customer_id):        # v16g4 FIX M10
        return jsonify({"error": "Token is scoped to a different tenant"}), 403
    brain = get_customer_brain(contact.customer_id)
    if not brain:
        return jsonify({"error": "Customer not found"}), 404

    contact_id = crm_add_contact(
        contact.customer_id, contact.name, contact.phone,
        contact.email, contact.notes, contact.contact_stage, contact.is_consented,
    )
    if not contact_id:
        # v16g6 FIX R6-L8: 201 with contact_id 0 — the insert lost the race
        # AND the recovery re-lookup failed. Nothing verifiably exists;
        # saying "created" with a fake id poisons the caller's records.
        return jsonify({"error": "Contact could not be verified as created — "
                                 "please retry"}), 503
    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "crm.add_contact", contact.customer_id,
          {"stage": contact.contact_stage, "consented": contact.is_consented},
          request.remote_addr)
    return jsonify({
        "status":        "success",
        "contact_id":    contact_id,
        "pii_encrypted": pii_vault.enabled,
        "request_id":    g.get("request_id"),
    }), 201


# ── CRM: List Contacts ────────────────────────────────────────────────────────
@app.route("/crm/contacts/<customer_id>", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="viewer")
def crm_list_contacts_api(customer_id: str):
    stage    = request.args.get("stage")
    page     = _int_arg("page", 1, 1, 10**6)          # v15g4 FIX C3
    per_page = _int_arg("per_page", 50, 1, 100)        # v15g4 FIX C3
    contacts, total = crm_list_contacts(customer_id, stage, page, per_page)
    return jsonify({
        "contacts": contacts,
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "note":     "Phones masked in list view. Use /crm/contact/{id} for full details.",
    }), 200


# ── CRM: Full Contact ─────────────────────────────────────────────────────────
@app.route("/crm/contact/<int:contact_id>", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="admin")
def crm_get_contact_api(contact_id: int):
    # v14g5 FIX 4 (IDOR): require the caller to name the tenant they're reading, so
    # a non-superadmin token can't enumerate contact ids across clinics. Superadmin
    # may omit it for cross-tenant support.
    customer_id = (request.args.get("customer_id") or "").strip()
    role        = g.jwt_user.get("role", "viewer")
    if not customer_id and role != "superadmin":
        return jsonify({"error": "customer_id query param required"}), 400
    if _tenant_forbidden(customer_id):                 # v16g4 FIX M10
        return jsonify({"error": "Token is scoped to a different tenant"}), 403
    contact = crm_get_contact_full(contact_id, customer_id)
    if not contact:
        return jsonify({"error": "Contact not found"}), 404
    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "crm.view_full", f"{customer_id or '*'}:{contact_id}", ip=request.remote_addr)
    return jsonify(contact), 200


# ── v14g4 DPDP: right-to-erasure for ONE data subject (by phone) ──────────────
@app.route("/admin/customer/<customer_id>/erase-subject", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="admin")
def erase_subject_api(customer_id: str):
    """DPDP Act 2023 right-to-erasure. Body: {"phone": "+91..."}. Deletes this
    person's CRM contact, bookings, RAG memory, and cache-mapped chat session."""
    data  = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    if not phone:
        return jsonify({"error": "phone is required"}), 400
    report = erase_data_subject(customer_id, phone)
    actor  = g.jwt_user.get("sub", "unknown")
    audit(actor, "dpdp.erase_subject", f"{customer_id}:{pii_vault.mask(phone)}",
          ip=request.remote_addr)
    return jsonify({"status": "erased", "customer_id": customer_id, "deleted": report}), 200


# ── v14g4: record/clear a contact's marketing consent (DPDP) ──────────────────
@app.route("/admin/customer/<customer_id>/consent", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="admin")
def set_consent_api(customer_id: str):
    """Body: {"phone": "+91...", "consented": true}. Only CONSENTED contacts are
    ever sent cold-lead follow-ups by the scheduler."""
    data  = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    if not phone:
        return jsonify({"error": "phone is required"}), 400
    consented = bool(data.get("consented", True))
    # v16g2 FIX N9: resolve the subject the same way erasure does (M5) — a
    # USERNAME patient's row is keyed on the BSUID hash, so hashing the real
    # number the clinic holds matched nothing and this endpoint answered
    # 200 "ok, rows_updated: 0" while consent silently never landed for
    # exactly the patients U3 exists for. Zero matches is now a 404.
    rows = _find_subject_rows(customer_id, phone)
    if not rows:
        return jsonify({"error": "subject not found for that number"}), 404
    val = _db_true() if consented else (False if isinstance(_db_pool, PostgreSQLPool) else 0)
    updated = 0
    try:
        with _db_pool.get() as conn:
            for r in rows:
                cur = _execute(conn,
                    "UPDATE crm_contacts SET is_consented=? WHERE id=? AND customer_id=?",
                    (val, r["id"], customer_id))
                updated += getattr(cur, "rowcount", 0) or 0
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    actor = g.jwt_user.get("sub", "unknown")
    audit(actor, "dpdp.set_consent", f"{customer_id}:{pii_vault.mask(phone)}={consented}",
          ip=request.remote_addr)
    return jsonify({"status": "ok", "consented": consented, "rows_updated": updated}), 200


# ── v15: instantly un-mute the AI for one conversation (owner is done) ────────
@app.route("/admin/customer/<customer_id>/ghost-resume", methods=["POST"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="admin")
def ghost_resume_api(customer_id: str):
    """v15 FIX 17: ghost_resume() existed since v10 but NOTHING ever called it —
    once a human took over a chat, the AI stayed muted for the full
    GHOST_MUTE_SECONDS with no way back. Now the owner (or you) can hand the
    conversation back to the bot the second they're done.
    Body: {"phone": "9198..."} (WhatsApp) and/or {"ig_sender": "<psid>"}."""
    data  = request.get_json(silent=True) or {}
    phone = (data.get("phone") or "").strip()
    ig    = (data.get("ig_sender") or "").strip()
    if not phone and not ig:
        return jsonify({"error": "phone or ig_sender required"}), 400
    resumed: List[str] = []
    if phone:
        # v16g2 FIX L3: the mute key was stored under Meta's bare-digit
        # spelling — an owner typing "+91 98…" got 200 "resumed" while nothing
        # unmuted. Resume under every candidate spelling (erasure's B4 trick).
        _digits = re.sub(r"\D", "", phone)
        for _p in dict.fromkeys([phone, _digits, _normalize_msisdn(phone)]):
            if _p:
                ghost_resume(f"{customer_id}:{_p}")
        resumed.append("whatsapp")
    if ig:
        ghost_resume(f"ig:{customer_id}:{ig}")
        resumed.append("instagram")
    audit(g.jwt_user.get("sub", "unknown"), "ghost.resume",
          f"{customer_id}:{pii_vault.mask(phone or ig)}", ip=request.remote_addr)
    analytics.inc("ghost.resumed")
    return jsonify({"status": "resumed", "customer_id": customer_id,
                    "channels": resumed}), 200


# ── v14g4: list a clinic's upcoming bookings (ops view) ───────────────────────
@app.route("/admin/customer/<customer_id>/bookings", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="viewer")
def list_bookings_api(customer_id: str):
    """Upcoming booked appointments for a clinic. Phones are masked."""
    now_iso = datetime.now(timezone.utc).isoformat()
    limit   = _int_arg("limit", 50, 1, 200)            # v15g4 FIX C3
    out: List[Dict] = []
    try:
        with _db_pool.get(read_only=True) as conn:
            cur = _execute(conn,
                "SELECT id, enc_phone, slot_start, slot_end, status, reminders_sent "
                "FROM bookings WHERE customer_id=? AND status='booked' AND slot_start >= ? "
                "ORDER BY slot_start ASC LIMIT ?", (customer_id, now_iso, limit))
            for r in cur.fetchall():
                d = dict(r)
                out.append({
                    "id":            d["id"],
                    "phone":         pii_vault.mask(pii_vault.decrypt(d["enc_phone"])),
                    "slot_start":    d["slot_start"],
                    "slot_end":      d["slot_end"],
                    "local_time":    _fmt_local_dt(d["slot_start"]),
                    "status":        d["status"],
                    "reminders_sent": d.get("reminders_sent", ""),
                })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    return jsonify({"customer_id": customer_id, "count": len(out), "bookings": out}), 200


# ── Analytics Snapshot ────────────────────────────────────────────────────────
@app.route("/admin/analytics", methods=["GET"])
@limiter.limit(cfg.ADMIN_RATE_LIMIT)   # v16g3 FIX R3-L8: throttle runs BEFORE auth — 401 spray now hits ADMIN_RATE_LIMIT
@require_jwt(min_role="viewer")
def analytics_snapshot():
    """Real-time analytics dashboard endpoint (FIX #5)."""
    snap = analytics.snapshot()
    return jsonify({
        "region":      cfg.REGION,
        "engine":      "HEONIX Ultra v16.0 GEN-3",
        "counters":    snap["counters"],
        "latency_p99": snap["latency_p99"],
        "uptime_secs": snap["uptime_secs"],
    }), 200


# ── Error Handlers ────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found", "hint": "GET /health for status"}), 404


@app.errorhandler(429)
def rate_limited(e):
    analytics.inc("ratelimit.ip.hit")
    return jsonify({"error": "Rate limit exceeded", "retry_after": "60s"}), 429


@app.errorhandler(413)
def payload_too_large(e):
    # #37: MAX_CONTENT_LENGTH tripped — reject before the body is buffered into RAM.
    analytics.inc("error.413")
    return jsonify({"error": "Payload too large",
                    "limit_bytes": cfg.MAX_CONTENT_BYTES}), 413


@app.errorhandler(500)
def server_error(e):
    log.error(f"500: {e}", exc_info=True)
    analytics.inc("error.500")
    return jsonify({"error": "Internal server error",
                    "request_id": g.get("request_id", "")}), 500


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405


# ─────────────────────────────────────────────────────────────────────────────
# 🚦  GRACEFUL SHUTDOWN  (v11 #14 — no blocking sleep inside the handler)
# ─────────────────────────────────────────────────────────────────────────────
def _shutdown_handler(signum, frame):
    log.info(f"📴 Signal {signum} — graceful shutdown starting...")
    _shutdown_event.set()
    # v11 #14: was time.sleep(10) INSIDE the handler (blocks all signal
    # delivery). Now: stop accepting new bg work, let queued sends finish
    # with a hard ceiling enforced by a watchdog, then close the DB pool.
    def _drain():
        # v14g3 BUG 5: drain ALL bounded pools on shutdown, not just the worker
        # pool — the I/O pool (alerts/audit/sends) and timeout pool must finish
        # or be released cleanly too.
        for _pool in (_WORKER_POOL, _IO_POOL, _TIMEOUT_POOL):
            try:
                _pool.shutdown(wait=True)
            except Exception:
                pass
        if _db_pool:
            try:
                _db_pool.close_all()
            except Exception:
                pass
        log.info(f"✅ HEONIX Ultra {ENGINE_VERSION} {ENGINE_GEN} "
                 f"shut down cleanly.")                              # v16g2 FIX C1
    t = threading.Thread(target=_drain, name="drain", daemon=True)
    t.start()
    t.join(timeout=10)        # bounded — gunicorn's graceful-timeout is the boss
    # v15 FIX 14: the old handler drained and then simply RETURNED — under the
    # dev server Ctrl+C was swallowed (the app kept serving), and a worker that
    # inherited this handler never exited on SIGTERM until SIGKILL. Exit for real.
    sys.exit(0)


def _install_signal_handlers() -> None:
    """v15 FIX 14: only claim SIGTERM/SIGINT when THIS process owns them
    (direct `python engine.py`). The old module-import-time takeover REPLACED
    gunicorn's own worker SIGTERM handler with one that never exited — graceful
    stops degraded to SIGKILL after the timeout. Under gunicorn we now leave
    its signal handling alone and clean up via atexit instead."""
    signal.signal(signal.SIGTERM, _shutdown_handler)
    signal.signal(signal.SIGINT,  _shutdown_handler)


def _atexit_cleanup() -> None:
    """v15 FIX 14: gunicorn path — stop the janitor loop and release the DB
    pool when the interpreter exits normally (the bounded thread pools already
    join themselves via concurrent.futures' own atexit hook)."""
    _shutdown_event.set()
    try:
        if _db_pool:
            _db_pool.close_all()
    except Exception:
        pass


atexit.register(_atexit_cleanup)


def _bootstrap_first_admin() -> None:
    """v15g2 FIX L7: creating the first admin required a superadmin JWT — which
    required an existing admin. The only escape hatch (legacy ADMIN_API_KEY) was
    undocumented as the bootstrap path. Now: if admin_users is EMPTY and
    ADMIN_BOOTSTRAP_USER / ADMIN_BOOTSTRAP_PASSWORD (≥8 chars) are set, seed one
    superadmin on boot; otherwise say exactly how to get in."""
    try:
        with _db_pool.get(read_only=True) as conn:
            _r = _execute(conn, "SELECT COUNT(*) AS c FROM admin_users", ()).fetchone()
            n  = (_r["c"] if _r else 0) or 0
        if n:
            return
        bu = os.getenv("ADMIN_BOOTSTRAP_USER", "").strip()
        bp = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "")
        if bu and len(bp) >= 8:
            with _db_pool.get() as conn:
                _execute(conn,
                    "INSERT INTO admin_users (user_id, username, hashed_pw, role, created_at) "
                    "VALUES (?,?,?,?,?)",
                    (f"adm_{uuid.uuid4().hex[:12]}", bu, hash_password(bp),
                     "superadmin", _now()))
            log.info(f"🔑 Bootstrap superadmin '{bu}' created via ADMIN_BOOTSTRAP_*. "
                     f"Unset those env vars after your first login.")
        elif not cfg.ADMIN_API_KEY:
            log.warning("🔑 No admin users exist and no ADMIN_API_KEY set — admin "
                        "login is impossible. Set ADMIN_BOOTSTRAP_USER + "
                        "ADMIN_BOOTSTRAP_PASSWORD (≥8 chars) once, or set "
                        "ADMIN_API_KEY for the legacy X-Admin-Key path.")
    except Exception as exc:
        log.warning(f"⚠️  admin bootstrap check skipped: {exc}")


# ─────────────────────────────────────────────────────────────────────────────
# 🚀  STARTUP SEQUENCE
# ─────────────────────────────────────────────────────────────────────────────
_startup_done = False
_startup_lock = threading.Lock()


_startup_ready = threading.Event()   # v16g4 FIX L4


# ─────────────────────────────────────────────────────────────────────────────
# 🛑 v25.0 · FIX R25-S1 — THE INBOUND-COVERAGE INVARIANT
#    (fix the CLASS, not the sixth instance)
# ─────────────────────────────────────────────────────────────────────────────
# Six consecutive rounds found ONE defect: an inbound keyword list written by
# somebody thinking in English, so a whole register of patients cannot reach a
# feature AT ALL.
#   R18 emergency keywords · R21 identity bridge · R22 clinical control ·
#   R23 cancel/reschedule/status · R24 BOOK — the primary function, dead in
#   ta/hi through 23 rounds · R25 human handoff, dead in romanised Tamil.
# Six instances means the CLASS is the defect, and patching a seventh buys
# exactly one more round. This assertion runs at every boot, on every deploy,
# and NAMES the feature and the register — the same move R18-H1 made when it
# stopped trusting the configured value and printed the one actually built.
#
# THREE DESIGN CHOICES, each from something that measurably went wrong:
#
# 1. The check is BEHAVIOURAL, not a word count. It drives a real patient
#    sentence through the real production matcher. A script-counting census
#    has to GUESS which register a Latin string belongs to, and it guesses
#    badly: the audit toolkit's own heuristic misfiles 15 of R25-C1's 31
#    genuine romanised-Tamil entries as English. A list can also read healthy
#    and be dead — an entry shadowed by an earlier branch, killed by a
#    negator, or with a stem too short to ever match (R23: Hindi "बदल" is
#    three codepoints and can never reach "बदलना"). Only driving the matcher
#    answers the question the patient cares about.
#
# 2. The registry is EXPLICIT, not a name prefix. The toolkit's
#    INBOUND_PREFIXES is itself a hand-maintained list — the same defect one
#    level up — and measured against this file it matched 26 of 49 string
#    collections. A new list with an unanticipated name is invisible to a
#    prefix scan and visible here only if somebody adds a probe, which is a
#    line of code in a diff rather than a silence.
#
# 3. Required registers are declared PER FEATURE. A global required=("ta","hi")
#    is precisely what hid R25-C1 for twenty-four rounds: _HUMAN_KW had Tamil
#    AND Hindi and zero romanised Tamil, so it passed every check while a
#    Thanglish patient could not reach a human at all. Note this covers
#    INBOUND lists only — reply-side guard lists are deliberately out of
#    scope, because the model writes Tamil script or English and R8-M1 pins
#    it to the patient's language, so demanding "tg" there would be noise.
_INBOUND_PROBES = (
    # (feature, what this patient loses, {register: one real patient sentence})
    ("emergency", "report a medical emergency", {
        "en": "i have severe chest pain",
        "ta": "எனக்கு நெஞ்சு வலி ரொம்ப அதிகமா இருக்கு",
        "hi": "मुझे सीने में दर्द हो रहा है",
        "tg": "enakku romba nenju vali irukku",
    }),
    ("human", "reach a human being", {
        "en": "i want to talk to a human",
        "ta": "டாக்டர் கிட்ட பேசணும்",
        "hi": "मुझे डॉक्टर से बात करनी है",
        "tg": "doctor kitta pesanum",
    }),
    ("book", "book an appointment", {
        "en": "i want to book an appointment",
        "ta": "எனக்கு அப்பாயின்ட்மென்ட் புக் பண்ணணும்",
        "hi": "मुझे अपॉइंटमेंट बुक करना है",
        "tg": "enakku appointment book pannanum",
    }),
    ("cancel", "cancel an appointment", {
        "en": "please cancel my appointment",
        "ta": "என் அப்பாயின்ட்மென்ட் ரத்து செய்யுங்க",
        "hi": "मेरा अपॉइंटमेंट रद्द कर दीजिए",
        "tg": "en appointment cancel pannunga",
    }),
    ("reschedule", "move an appointment", {
        "en": "can i reschedule my appointment",
        "ta": "என் அப்பாயின்ட்மென்ட் நேரம் மாற்றணும்",
        "hi": "मेरा अपॉइंटमेंट का समय बदलना है",
        "tg": "en appointment time maathanum",
    }),
    # v28.0 · FIX R28-S1. THE CONTROL ITSELF WAS THE GAP. R25-S1 probes six
    # features; opt-out is a seventh patient-inbound route and had no probe,
    # so R28-C1 (hi 0/7) sat under a boot line reading "all 6 features
    # reachable in en/ta/hi/tg" for two rounds. Mutation-tested the R25
    # control first: emptying each of the six features' own lists makes every
    # one of its 24 (feature, register) probes go dead — zero survivors, so
    # the control is sound ON ITS REGISTRY. Its weakness is the registry's
    # EDGE, which is the failure mode any explicit registry has and the price
    # design choice 2 knowingly pays. Adding the seventh route is the fix;
    # the general lesson is that a new inbound feature must arrive with its
    # probe in the same diff.
    ("optout", "stop receiving messages", {
        "en": "stop sending messages",
        "ta": "\u0b9a\u0bc6\u0baf\u0ba4\u0bbf \u0bb5\u0bc7\u0ba3\u0bcd\u0b9f\u0bbe\u0bae\u0bcd",
        "hi": "\u092e\u0948\u0938\u0947\u091c \u092d\u0947\u091c\u0928\u093e \u092c\u0902\u0926 \u0915\u0930\u094b",
        "tg": "message anuppadheenga",
    }),
    ("status", "check an appointment", {
        "en": "when is my appointment",
        "ta": "என் அப்பாயின்ட்மென்ட் எப்போது",
        "hi": "मेरा अपॉइंटमेंट कब है",
        "tg": "en appointment eppo",
    }),
)


def _probe_fires(feature: str, text: str) -> bool:
    """Drive ONE probe through the REAL production matcher — no parallel
    implementation, because a parallel implementation is a thing that can
    agree with itself while the engine disagrees with both. healthcare=True:
    that is the launch market and the strictest emergency list."""
    if feature in ("emergency", "human"):
        return bool(classify_message(text, healthcare=True).get(feature))
    if feature == "optout":
        # v28.0 R28-S1: opt-out does NOT go through detect_booking_intent. It
        # is exact whole-message membership (#201) — the real consumer at
        # /chat, the WhatsApp webhook and the Instagram webhook is this same
        # expression, so the probe drives production, not a copy of it.
        return _norm_text(text) in _OPT_OUT_KEYWORDS
    return detect_booking_intent(text) == feature


def _assert_inbound_coverage() -> List[str]:
    """One line per (feature, register) a patient cannot reach at all.

    DELIBERATELY NON-FATAL. A clinic mid-consultation must not lose its
    receptionist because a keyword list is thin — and the failure this guards
    against is SILENCE, so the cure is noise, not a crash. It is also wrapped
    by the caller: a bug in this check must never be what stops a boot.
    """
    violations: List[str] = []
    for feature, loses, probes in _INBOUND_PROBES:
        dead = sorted(reg for reg, text in probes.items()
                      if not _probe_fires(feature, text))
        if dead:
            violations.append(
                f"{feature}: no route from {'/'.join(dead)} — "
                f"those patients cannot {loses}")
    return violations


def startup() -> None:
    global _db_pool, _startup_done
    with _startup_lock:
        if _startup_done:          # idempotent — safe under gunicorn + __main__
            # v16g4 FIX L4: _startup_done was flipped BEFORE any work ran, so
            # a second caller returned instantly and could serve a request
            # against a _db_pool that didn't exist yet. Late callers now WAIT
            # for the first boot to actually finish (bounded, then proceed —
            # a hung boot shouldn't deadlock the health probe).
            _startup_ready.wait(timeout=120)
            return
        _startup_done = True

    log.info("=" * 76)
    log.info(f"  👑  HEONIX ULTRA ENGINE  {ENGINE_VERSION} {ENGINE_GEN}"
             f"  ·  ROUND-6 CLOSE-OUT (47 FIXES)")
    log.info(f"  🌍  Region: {cfg.REGION}")
    log.info("=" * 76)

    # ── Database ──
    if cfg.DATABASE_MODE == "postgres" and cfg.DATABASE_URL and POSTGRES_AVAILABLE:
        _db_pool = PostgreSQLPool(
            cfg.DATABASE_URL,
            min_conn=2,
            max_conn=cfg.MAX_POOL_SIZE,
            replica_dsn=cfg.DATABASE_REPLICA_URL,
        )
    else:
        _db_pool = SQLitePool(cfg.DATABASE_FILE, pool_size=cfg.MAX_POOL_SIZE)

    # ── v11 #2: never *silently* run a multi-worker deployment on fallbacks ──
    on_paas    = bool(os.getenv("RENDER") or os.getenv("DYNO") or os.getenv("FLY_APP_NAME"))
    sqlite_db  = isinstance(_db_pool, SQLitePool)
    no_redis   = not (cfg.REDIS_URL and REDIS_AVAILABLE)
    if sqlite_db and on_paas:
        log.critical("🛑 SQLite on a PaaS dyno: disk is EPHEMERAL (all customer "
                     "data lost on every deploy) and 'database locked' errors "
                     "appear under 2+ workers. Set DATABASE_URL + DATABASE_MODE=postgres.")
    if no_redis and on_paas:
        log.critical("🛑 No REDIS_URL: dedupe / ghost-mute / response-cache are "
                     "per-process → with 2 gunicorn workers users can get DOUBLE "
                     "replies and human-takeover mute won't stick. Set REDIS_URL "
                     "(Upstash free tier works).")
    if cfg.STRICT_PROD and (sqlite_db or no_redis):
        raise SystemExit("STRICT_PROD=1: refusing to boot without Postgres + Redis. "
                         "Set DATABASE_URL, DATABASE_MODE=postgres, REDIS_URL "
                         "— or unset STRICT_PROD for dev.")

    # ── v14g3 BUG 3: JWT / Flask secrets MUST be set explicitly for multi-worker.
    # If unset, each gunicorn worker generated its OWN random secret at import →
    # a JWT minted by worker A failed validation on worker B (admin login broke
    # intermittently) and Flask sessions broke the same way. We cannot invent a
    # shared secret across processes, so fail LOUD (and refuse under STRICT_PROD).
    # v15g2 FIX L9: secrets derived from ENCRYPTION_KEY are identical in every
    # worker, so they no longer count as 'missing' — the refuse-to-boot guard
    # now only fires when there is genuinely nothing shared to derive from.
    _missing_secrets = ([] if os.getenv("ENCRYPTION_KEY") else
                        [n for n in ("JWT_SECRET_KEY", "SECRET_KEY")
                         if not os.getenv(n)])
    if _missing_secrets:
        _smsg = ("🛑 " + " & ".join(_missing_secrets) + " not set — each worker "
                 "will use a DIFFERENT random secret, so JWT auth and Flask "
                 "sessions break across gunicorn workers. Generate one with: "
                 "python -c \"import secrets; print(secrets.token_hex(32))\"")
        # v14g5 FIX 11: a missing shared secret under >1 worker is not a warning —
        # admin JWTs minted on one worker are REJECTED on another, so login breaks
        # nondeterministically. Refuse to boot (matches STRICT_PROD behaviour).
        if cfg.STRICT_PROD or cfg.WEB_CONCURRENCY > 1:
            raise SystemExit(_smsg + ("  (STRICT_PROD=1 refuses to boot.)"
                                      if cfg.STRICT_PROD else
                                      f"  (WEB_CONCURRENCY={cfg.WEB_CONCURRENCY} "
                                      "> 1 refuses to boot — set a shared secret.)"))
        log.warning(_smsg)

    # ── #34: pool-explosion guard ──
    # Each gunicorn worker opens its OWN pool of up to MAX_POOL_SIZE connections.
    # workers × MAX_POOL_SIZE must stay under the Postgres connection ceiling, or
    # the Nth worker gets "FATAL: remaining connection slots are reserved" / "too
    # many connections" at peak — which looks like random 500s under load. Warn
    # loudly, and if Postgres, clamp this worker's pool so the fleet stays legal.
    if not sqlite_db:
        projected = cfg.WEB_CONCURRENCY * cfg.MAX_POOL_SIZE
        if projected > cfg.DB_MAX_CONNECTIONS:
            safe = max(2, cfg.DB_MAX_CONNECTIONS // max(1, cfg.WEB_CONCURRENCY))
            log.critical(
                f"🛑 DB pool overcommit: WEB_CONCURRENCY({cfg.WEB_CONCURRENCY}) × "
                f"MAX_POOL_SIZE({cfg.MAX_POOL_SIZE}) = {projected} > "
                f"DB_MAX_CONNECTIONS({cfg.DB_MAX_CONNECTIONS}). Under load the last "
                f"workers will hit 'too many connections'. Clamping this worker's "
                f"pool to {safe}. Fix properly: lower MAX_POOL_SIZE or raise the "
                f"Postgres max_connections / use a pgBouncer.")
            try:
                # v15 FIX 13: the clamp checked `_db_pool._pool` — an attribute
                # PostgreSQLPool never had (its pools are _write/_read), so the
                # "best-effort runtime clamp" was dead code and overcommit was
                # only ever logged, never contained.
                if hasattr(_db_pool, "_write") and hasattr(_db_pool._write, "maxconn"):
                    _db_pool._write.maxconn = safe
                if getattr(_db_pool, "_read", None) is not None \
                        and hasattr(_db_pool._read, "maxconn"):
                    _db_pool._read.maxconn = safe
            except Exception:
                pass

    init_db()
    _migrate_v10()   # v10: new columns, safe every boot
    _migrate_v11()   # v11: CRM dedupe column + index, safe every boot
    _migrate_v12()   # v13: per-tenant WA/IG creds + unique routing index, safe every boot
    _migrate_v14g3() # v14g3: unique CRM dedupe index + SQLite phone index
    _migrate_v14g4() # v14g4: bookings table + cold-lead follow-up marker (additive)
    _migrate_v14g5() # v14g5: chat_sessions.subject_hash for DB-based DPDP erasure
    _migrate_v15g3() # v15g3: outbox.next_attempt_at for exponential retry backoff
    _migrate_v15g4() # v15g4: purge-path indexes (D4) + SQLite idx_wh_customer (D5)
    _migrate_v16()   # v16: crm_contacts.wa_user_id (WhatsApp usernames/BSUID)
    _migrate_v16g4() # v16g4 FIX M10: admin_users.tenant_id
    _migrate_v16g5() # v16g5 FIX R5-H4: durable opt_outs suppression table
    _report_wa_pid_duplicates()   # v14: self-diagnose ambiguous-routing duplicates
    _bootstrap_first_admin()      # v15g2 FIX L7: no more admin chicken-and-egg

    # ── AI Providers ──
    _init_ai_providers()

    # ── v10: RAG long-term memory ──
    init_rag()

    # ── Background Janitor ──
    threading.Thread(target=_janitor_loop, name="Janitor", daemon=True).start()
    log.info("🧹 Background janitor started.")

    # ── Startup Summary ──
    log.info("=" * 76)
    log.info(f"  🌐  Port:            {cfg.PORT}")
    # v18.0 FIX R18-H1: this printed cfg.DATABASE_MODE, which is the INTENT
    # ("postgres" by default), not the pool that actually got built. With
    # DATABASE_URL unset or psycopg2 missing, the engine silently fell back to
    # SQLite and still announced "postgres" at boot. On Render that is the
    # difference between durable data and a database wiped on every redeploy,
    # reported as success. Print what was actually constructed, and say so
    # loudly when it disagrees with what was asked for.
    _actual = "postgres" if type(_db_pool).__name__ == "PostgreSQLPool" else "sqlite"
    log.info(f"  🗄️   DB Mode:         {_actual}"
             + ("" if _actual == cfg.DATABASE_MODE
                else f"  ⚠️  (DATABASE_MODE={cfg.DATABASE_MODE} requested)"))
    if _actual != cfg.DATABASE_MODE:
        log.critical(
            f"🛑 R18-H1: DATABASE_MODE={cfg.DATABASE_MODE} was requested but the "
            f"engine is running on {_actual}. "
            + ("DATABASE_URL is empty. " if not cfg.DATABASE_URL else "")
            + ("psycopg2 is not installed. " if not POSTGRES_AVAILABLE else "")
            + "On an ephemeral host, SQLite data is LOST on every redeploy.")
    log.info(f"  📚  Read Replica:    "
             f"{'YES ✅' if isinstance(_db_pool, PostgreSQLPool) and _db_pool._read else 'NO'}")
    log.info(f"  🧠  Redis Cache:     "
             f"{'distributed ✅' if brain_cache._redis else 'in-process only'}")
    log.info(f"  🔐  PII Encryption: "
             f"{'AES-256-GCM ✅' if pii_vault.enabled else 'DISABLED ⚠️'}")
    log.info(f"  🔑  bcrypt Hashing: "
             f"{'ACTIVE ✅' if BCRYPT_AVAILABLE else 'SHA-256 fallback ⚠️'}")
    log.info(f"  📱  WhatsApp API:   "
             f"{'CONFIGURED ✅' if cfg.WHATSAPP_TOKEN else 'NOT SET ⚠️'}")
    if not cfg.WHATSAPP_APP_SECRET:
        log.warning("  🚨  WHATSAPP_APP_SECRET not set → webhook signature "
                    "verification is OFF. Anyone who finds the URL can POST "
                    "fake messages. Set it before going live!")
    if cfg.WHATSAPP_VERIFY_TOKEN == "heonix_verify":
        # v15g2 FIX L8: the default is public (it ships in this source file).
        log.warning("  🚨  WHATSAPP_VERIFY_TOKEN is the public default "
                    "('heonix_verify'). Set your own random value before live.")
    if not cfg.CHAT_API_KEY:
        log.warning("  🚨  CHAT_API_KEY not set → POST /chat is OPEN. customer_id "
                    "is derivable from a clinic's public WhatsApp number, so "
                    "anyone can burn your Gemini quota. Set it before going live!")
    if not cfg.SMOKE_TEST_ENABLED:
        log.info("  🔬  Smoke Test:      disabled — set SMOKE_TEST_ENABLED=1 "
                 "(v15 FIX 12: default now matches the docs; you use this tool!)")
    log.info(f"  📸  Instagram API:  "
             f"{'CONFIGURED ✅' if cfg.INSTAGRAM_TOKEN else 'NOT SET (optional)'}")
    log.info(f"  🧬  RAG Memory:     "
             f"{'Qdrant ONLINE ✅' if _rag_ready else 'OFF (set QDRANT_URL + QDRANT_API_KEY)'}")
    log.info(f"  🎙️   Voice Decoder:  "
             f"{'Gemini→Whisper ✅' if (AI_PROVIDERS_ACTIVE.get('gemini') or AI_PROVIDERS_ACTIVE.get('openai')) else 'OFF'}")
    log.info(f"  🤖  AI Chain:       {[k for k, v in AI_PROVIDERS_ACTIVE.items() if v]}")
    log.info(f"  🔒  JWT Auth:       {'ACTIVE ✅' if JWT_AVAILABLE else 'pyjwt not installed ⚠️'}")
    log.info(f"  📊  Analytics:      {'ENABLED ✅' if cfg.ENABLE_ANALYTICS else 'DISABLED'}")
    log.info("  📬  Outbox/Saga:    ACTIVE ✅")   # v16g3 R3-L2: stray f
    log.info("  🪙  Customer RL:    60 req/min per conversation (webhooks) / per customer_id (API) ✅")
    log.info(f"  🧵  BG Workers:     {_WORKER_POOL._max_workers} bounded threads ✅")
    log.info(f"  📨  Owner Alerts:   "
             f"{'template (24h-proof) ✅' if cfg.OWNER_ALERT_TEMPLATE else 'free-form (set OWNER_ALERT_TEMPLATE!) ⚠️'}")
    log.info("  🏥  Multi-Tenant:   per-clinic creds + phone_id routing ✅")
    # v16 U4: Contact Book is Meta-hosted and ON by default — zero integration
    # work, but verify it ONCE per WABA so known patients who adopt usernames
    # keep surfacing their number in webhooks.
    log.info("  🆔  Usernames:      BSUID compat ACTIVE ✅ (v16) — verify Contact "
             "Book is ON once: Business Suite → WhatsApp Manager → Settings")
    log.info(f"  🔑  Token Self-Heal:"
             f"{' ON (ADMIN_ALERT_PHONE set) ✅' if cfg.ADMIN_ALERT_PHONE else ' flag-only (set ADMIN_ALERT_PHONE for WA alerts) ⚠️'}")
    log.info(f"  📝  Log Format:     {cfg.LOG_FORMAT}")
    # v15g4 FIX E9a: WhatsApp rejects free-form messages outside the 24h
    # window (131047). Most appointments are booked >24h ahead, so WITHOUT an
    # approved template, most 24h reminders dead-letter after 5 retries.
    if cfg.DATA_RETENTION_DAYS <= 0:
        # v16g5 FIX R5-L9: the default (0 = keep forever) is the one DPDP knob
        # that ships non-compliant. Defensible as a default — silently is not.
        log.warning("  🚨  DATA_RETENTION_DAYS=0 → chat transcripts (patient "
                    "symptoms, names, numbers) are kept FOREVER. DPDP expects a "
                    "stated retention limit. Set it (e.g. 365) before launch.")
    if cfg.ENABLE_SCHEDULER and not cfg.REMINDER_TEMPLATE:
        log.warning("  🚨  ENABLE_SCHEDULER is ON but REMINDER_TEMPLATE is not "
                    "set → reminders for bookings made >24h ahead WILL fail "
                    "outside Meta's window. Create + approve a template in the "
                    "Meta console and set REMINDER_TEMPLATE before launch.")
    # v15g4 FIX E11a: google.generativeai is the DEPRECATED legacy SDK. Make
    # the risk visible on every deploy: verify this SDK version still serves
    # the configured models, and plan the google-genai migration.
    if AI_PROVIDERS_ACTIVE.get("gemini"):
        try:
            _gv = getattr(genai, "__version__", "?")
            log.info(f"  🧬  Gemini SDK:     google.generativeai {_gv} "
                     f"(LEGACY — verify it serves {cfg.GEMINI_MODEL}; "
                     f"plan google-genai migration)")
        except Exception:
            pass
    # v15g4 FIX D6: .search() is the pre-query_points Qdrant API — pin the
    # client version in requirements so an upgrade can't surprise-break RAG.
    if _rag_ready:
        try:
            import qdrant_client as _qc
            log.info(f"  🧷  Qdrant client:  {getattr(_qc, '__version__', '?')} "
                     f"(pin this in requirements — engine uses the legacy "
                     f".search() API)")
        except Exception:
            pass
    # ── v16g4 boot warnings: every silent-death config gap gets a voice ──
    if cfg.FOLLOWUP_ENABLED and not cfg.FOLLOWUP_TEMPLATE:
        # v16g4 FIX H2: twin of E9a — cold-lead nudges are BY DEFINITION
        # outside the 24h window; without a template none can deliver.
        log.warning("  🚨  FOLLOWUP_ENABLED is ON but FOLLOWUP_TEMPLATE is not "
                    "set → cold-lead nudges are DISABLED (nothing outside the "
                    "24h window can deliver as free text). Approve a template "
                    "and set FOLLOWUP_TEMPLATE.")
    if not cfg.WELCOME_TEMPLATE:
        # v16g4 FIX H1 companion warning.
        log.warning("  🚨  WELCOME_TEMPLATE not set → the Tally onboarding "
                    "welcome to new clinic owners is SKIPPED (a cold number "
                    "can't receive free text). Approve a welcome template and "
                    "set WELCOME_TEMPLATE.")
    if (cfg.STRICT_PROD or cfg.REQUIRE_WEBHOOK_SIGNATURE) and not cfg.TALLY_WEBHOOK_SECRET:
        # v16g4 FIX H4 companion warning: the endpoint fails CLOSED now.
        log.warning("  🚨  TALLY_WEBHOOK_SECRET not set under strict mode → "
                    "the /tally-webhook endpoint REJECTS all onboarding posts "
                    "(fail-closed). Set the secret from your Tally form's "
                    "webhook settings.")
    if cfg.ADMIN_API_KEY:
        # v16g4 FIX M13 companion warning.
        if cfg.STRICT_PROD and not cfg.ADMIN_API_KEY_LEGACY_OK:
            log.warning("  🔐  ADMIN_API_KEY is set but REFUSED under "
                        "STRICT_PROD (v16g4 FIX M13). Use JWT login, or set "
                        "ADMIN_API_KEY_LEGACY_OK=1 to acknowledge the risk.")
        else:
            log.warning("  🔐  Legacy ADMIN_API_KEY auth is ACTIVE — a "
                        "permanent env superadmin. Prefer JWT logins; rotate "
                        "the key if it has ever been shared.")
    if cfg.WEB_CONCURRENCY <= 1 and (os.getenv("GUNICORN_CMD_ARGS")
                                     or os.getenv("SERVER_SOFTWARE", "").startswith("gunicorn")):
        # v16g4 FIX O2: the limiter's no-Redis divisor and the pool-overcommit
        # math both read WEB_CONCURRENCY; if gunicorn runs >1 workers while it
        # is unset (default 1), those calculations silently under-divide.
        log.warning("  🚨  Running under gunicorn but WEB_CONCURRENCY is unset/1 "
                    "— if you run more than 1 worker, set WEB_CONCURRENCY to "
                    "the same number so rate-limit and DB-pool math stay true.")
    # ── v25.0 · FIX R25-S1: the inbound-coverage invariant, at every boot ───
    try:
        _cov = _assert_inbound_coverage()
    except Exception as _cov_exc:          # never let the check break a boot
        _cov = []
        log.error(f"❌ R25-S1 inbound-coverage check failed to run: {_cov_exc}")
    if _cov:
        log.critical("  🛑  R25-S1 INBOUND COVERAGE — %d feature/register "
                     "pair(s) a patient CANNOT REACH. This fails SILENTLY: "
                     "nothing logs when a patient is not understood.",
                     len(_cov))
        for _v in _cov:
            log.critical("      🛑  %s", _v)
    else:
        log.info("  ✅  R25-S1 INBOUND COVERAGE — all %d features reachable "
                 "in en/ta/hi/tg.", len(_INBOUND_PROBES))
    log.info("=" * 76)
    log.info(f"  🦅  {ENGINE_VERSION} {ENGINE_GEN} — R27 · every defensive log "
             f"line now reaches STDOUT as _build_logger always claimed "
             f"(measured v26: stdout 0, stderr 2) · 8 suites / 243 tests / "
             f"373 assertions green on one build for the first time")
    log.info("=" * 76)
    _startup_ready.set()   # v16g4 FIX L4: boot genuinely complete


# ─────────────────────────────────────────────────────────────────────────────
# ▶️   ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
# v10 FIX: run startup at import time too. The documented production command is
#   gunicorn heonix_ultra_engine_v12:app
# which imports this module but never executes __main__ — in v8 that left
# _db_pool = None and every request crashed with "pool not initialised".
# startup() is idempotent, so both paths are safe.
startup()

if __name__ == "__main__":
    _install_signal_handlers()   # v15 FIX 14: direct-run only — gunicorn keeps its own
    # v16g2 FIX L14: DEBUG=true under `python engine.py` serves the Werkzeug
    # interactive debugger — a remote Python console. Refuse it on a PaaS.
    _debug = cfg.DEBUG
    if _debug and (os.getenv("RENDER") or os.getenv("DYNO") or os.getenv("FLY_APP_NAME")):
        log.critical("🛑 DEBUG=true on a PaaS — the Werkzeug debugger is a "
                     "remote console. Forcing DEBUG off; unset DEBUG in env.")
        _debug = False
    app.run(
        host         = "0.0.0.0",
        port         = cfg.PORT,
        debug        = _debug,
        threaded     = True,
        use_reloader = False,
    )
