"""Round-6 close-out surface (v16.1 GEN-6) — offline-testable fixes only.
Every assertion here was pinned against the GEN-6 monolith before the split."""
import uuid

from heonix.config import ENGINE_GEN, ENGINE_VERSION
from heonix.db.store import is_opted_out_checked, opt_out_subject
from heonix.security.crypto import PIIVault, _crm_phone_hash

KEY = "ab" * 32


# ── R6-C2 · disabled-vault decrypt of tagged ciphertext must not leak blob ──
def test_disabled_vault_returns_sentinel_for_tagged_ciphertext():
    blob = PIIVault(KEY).encrypt("919876543210")
    assert blob.startswith("v1:")
    # Vault off (no ENCRYPTION_KEY): the row is unreadable — say so loudly
    # with the sentinel every scheduler guard already checks, never hand the
    # raw ciphertext onward as if it were a phone number.
    assert PIIVault("").decrypt(blob) == "[ENCRYPTED]"
    assert PIIVault("").decrypt("plain text") == "plain text"   # passthrough intact


# ── R6-H5 · Instagram pseudo-identities are their own namespace ─────────────
def test_ig_identity_never_merges_with_phone_digit_tail():
    assert (_crm_phone_hash("HX_A", "ig_9876543210")
            != _crm_phone_hash("HX_A", "9876543210"))
    assert (_crm_phone_hash("HX_A", "ig_17841400000000001")
            != _crm_phone_hash("HX_A", "17841400000000001"))


# ── R6-H9 · three-state opt-out verdict: unknown must hold, not consume ─────
def test_optout_checked_known_states(client):
    subject = f"9199{uuid.uuid4().int % 10**8:08d}"
    assert is_opted_out_checked("HX_T", subject) == (False, True)
    assert opt_out_subject("HX_T", subject) is True
    assert is_opted_out_checked("HX_T", subject) == (True, True)
    assert is_opted_out_checked("HX_T", "") == (False, True)


def test_optout_checked_unknown_on_db_error(monkeypatch, client):
    class _DeadPool:
        def get(self, *a, **kw):
            raise RuntimeError("pool down")
    monkeypatch.setattr("heonix.db.store._db_pool", _DeadPool())
    suppressed, known = is_opted_out_checked("HX_T", f"9199{uuid.uuid4().int % 10**8:08d}")
    assert suppressed is True and known is False   # hold the reminder, don't consume it


# ── R6-M8 · non-dict JSON on public POST is a 4xx, not a 500 ────────────────
def test_chat_rejects_non_dict_json(client):
    r = client.post("/chat", json=[1, 2, 3])
    assert 400 <= r.status_code < 500


# ── R6-L1 · one constant drives the version string everywhere ───────────────
def test_engine_version_constant_reaches_health(client):
    body = client.get("/health").get_json()
    assert ENGINE_VERSION in body["engine"] and ENGINE_GEN in body["engine"]
