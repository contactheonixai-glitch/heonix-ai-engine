"""Round-5 close-out surface (v16.0 GEN-5). These guard the fixes that landed
on top of post-HF3 GEN-4 — without them the package suite would silently
under-cover the newest and least-exercised code in the engine."""
import uuid

import pytest

from heonix.db.store import (_wa_in_service_window, _wa_touch_window,
                             is_opted_out, opt_out_subject)
from heonix.i18n import _t
from heonix.security.auth import decode_jwt, generate_jwt, revoke_jwt
from heonix.security.crypto import PIIVault

KEY_A = "ab" * 32
KEY_B = "cd" * 32


# ── R5-C4 · versioned ciphertext, legacy rows must survive ──────────────────
def test_ciphertext_is_version_tagged_and_roundtrips():
    v = PIIVault(KEY_A)
    blob = v.encrypt("919876543210")
    assert blob.startswith("v1:")            # tagged by this build
    assert v.decrypt(blob) == "919876543210"


def test_legacy_plaintext_row_is_not_bricked():
    # The row was written before ENCRYPTION_KEY existed. Enabling the key
    # must hand the plaintext back, not destroy it.
    v = PIIVault(KEY_A)
    assert v.decrypt("Dr Keerthiga") == "Dr Keerthiga"
    assert v.decrypt("919876543210") == "919876543210"


def test_wrong_key_yields_sentinel_never_a_raw_blob():
    # Every scheduler guard tests `!= "[ENCRYPTED]"`, so a key mismatch must
    # land on the sentinel — tagged or untagged (legacy ciphertext).
    a, b = PIIVault(KEY_A), PIIVault(KEY_B)
    tagged = a.encrypt("919876543210")
    assert b.decrypt(tagged) == "[ENCRYPTED]"
    assert b.decrypt(tagged[len("v1:"):]) == "[ENCRYPTED]"


# ── R5-L3 · JWT issuer/audience binding + revocation denylist ───────────────
def test_jwt_carries_issuer_and_audience():
    claims = decode_jwt(generate_jwt("admin-1", tenant="HX_CLINIC_42"))
    assert claims["iss"] == "heonix-engine"
    assert claims["aud"] == "heonix-admin"
    assert claims["jti"]


def test_revoked_jwt_stops_decoding():
    tok = generate_jwt("admin-1")
    claims = decode_jwt(tok)
    assert claims is not None                    # valid before revocation
    revoke_jwt(claims["jti"])
    assert decode_jwt(tok) is None               # /admin/logout is now real


# ── R5-H4 · durable opt-out, fails CLOSED ──────────────────────────────────
def test_optout_roundtrip_is_durable(client):     # client → engine booted
    subject = f"9199{uuid.uuid4().int % 10**8:08d}"
    assert is_opted_out("HX_TEST", subject) is False
    assert opt_out_subject("HX_TEST", subject) is True
    assert is_opted_out("HX_TEST", subject) is True


def test_optout_lookup_fails_closed(monkeypatch, client):
    """DB down + cache miss ⇒ assume opted out. Silence is the safe direction
    for consent: better a missed reminder than a message to someone who said
    STOP."""
    class _DeadPool:
        def get(self, *a, **kw):
            raise RuntimeError("pool down")

    monkeypatch.setattr("heonix.db.store._db_pool", _DeadPool())
    assert is_opted_out("HX_TEST", f"9199{uuid.uuid4().int % 10**8:08d}") is True


def test_optout_ignores_empty_subject():
    assert is_opted_out("HX_TEST", "") is False


# ── R5-H1 · 24h customer-service window tracking ───────────────────────────
def test_service_window_opens_on_inbound_only():
    subject = f"9199{uuid.uuid4().int % 10**8:08d}"
    assert _wa_in_service_window("HX_TEST", subject) is False
    _wa_touch_window("HX_TEST", subject)
    assert _wa_in_service_window("HX_TEST", subject) is True


# ── R5-M2 · the six new strings exist in all three languages ───────────────
@pytest.mark.parametrize("key", ["audio_unclear", "image_unreadable", "media_ack",
                                 "contact_ack", "optout_failed", "ai_unavailable"])
def test_new_l10n_keys_present_in_en_ta_hi(key):
    for lang in ("en", "ta", "hi"):
        assert _t(key, lang), f"{key} missing for {lang}"
