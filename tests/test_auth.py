"""Signature verification + tenant-scoped JWT — the webhook front door."""
import hashlib
import hmac

from heonix.config import cfg
from heonix.security.auth import (_safe_ct_eq, decode_jwt, generate_jwt,
                                  verify_meta_signature)

SECRET = "wa-app-secret"
BODY = b'{"entry":[{"id":"123"}]}'


def _sig(body: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_safe_ct_eq_never_raises_on_non_ascii():
    assert _safe_ct_eq("token", "token")
    assert not _safe_ct_eq("token", "other")
    assert not _safe_ct_eq("héllo👍", "x")     # v16g3 R3-M1: must not 500
    assert not _safe_ct_eq(None, "x")


def test_meta_signature_valid_and_tampered():
    assert verify_meta_signature(BODY, _sig(BODY, SECRET), SECRET)
    assert not verify_meta_signature(BODY + b".", _sig(BODY, SECRET), SECRET)
    assert not verify_meta_signature(BODY, _sig(BODY, "other"), SECRET)
    assert not verify_meta_signature(BODY, "no-prefix", SECRET)


def test_meta_signature_fail_closed_under_strict_prod(monkeypatch):
    monkeypatch.setattr(cfg, "STRICT_PROD", True)
    assert not verify_meta_signature(BODY, "", "")        # v14g3 BUG 7
    monkeypatch.setattr(cfg, "STRICT_PROD", False)
    monkeypatch.setattr(cfg, "REQUIRE_WEBHOOK_SIGNATURE", False)
    assert verify_meta_signature(BODY, "", "")            # dev mode: open + loud


def test_jwt_roundtrip_tenant_scope_and_tamper():
    tok = generate_jwt("admin-1", role="owner", tenant="HX_CLINIC_42")
    claims = decode_jwt(tok)
    assert claims and claims["sub"] == "admin-1"
    assert claims["role"] == "owner" and claims["tnt"] == "HX_CLINIC_42"
    assert decode_jwt(tok[:-2] + "xx") is None
    assert "tnt" not in (decode_jwt(generate_jwt("a")) or {})
