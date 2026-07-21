"""PIIVault (AES-256-GCM) + password hashing — the layer clinic PII rides on."""
from heonix.security.crypto import PIIVault, hash_password, verify_password


def test_pii_vault_roundtrip_and_random_nonce():
    v = PIIVault("ab" * 32)
    assert v.enabled
    pt = "+91 98765 43210 · வாக்கை டெண்டல்"
    c1, c2 = v.encrypt(pt), v.encrypt(pt)
    assert c1 != pt and c2 != pt
    assert c1 != c2                      # unique nonce per encryption
    assert v.decrypt(c1) == pt and v.decrypt(c2) == pt


def test_pii_vault_bad_key_fails_soft():
    assert not PIIVault("too-short").enabled
    assert not PIIVault("zz" * 32).enabled          # non-hex
    v = PIIVault("")                                 # disabled → passthrough
    assert v.encrypt("x") == "x"


def test_pii_vault_mask_tiers():
    v = PIIVault("ab" * 32)
    assert v.mask("1234567") == "****"                    # ≤7 → full mask
    assert v.mask("ABCDEFGH") == "A***GH"                 # 8–11
    assert v.mask("919876543210") == "91***3210"          # ≥12 (E.164)


def test_password_hash_and_verify():
    h = hash_password("s3cret-pw")
    assert h and h != "s3cret-pw"
    assert verify_password("s3cret-pw", h)
    assert not verify_password("wrong-pw", h)
    assert not verify_password("anything", "")
