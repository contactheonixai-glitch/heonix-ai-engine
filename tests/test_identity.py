"""v14g3 BUG 11/12 + v16 U2: phone canonicalisation and BSUID identity."""
from heonix.api.helpers import _normalize_msisdn
from heonix.security.crypto import _crm_phone_hash, _is_bsuid


def test_normalize_msisdn_india_defaults():
    assert _normalize_msisdn("098765 43210") == "919876543210"
    assert _normalize_msisdn("+91 98765-43210") == "919876543210"
    assert _normalize_msisdn("0091 9876543210") == "919876543210"
    assert _normalize_msisdn("091 98765 43210") == "919876543210"   # v16g3 R3-L12
    assert _normalize_msisdn("9876543210") == "919876543210"


def test_normalize_msisdn_foreign_and_garbage():
    assert _normalize_msisdn("+1 415 555 2671") == "14155552671"    # keeps CC
    assert _normalize_msisdn("12345") == ""                          # too short
    assert _normalize_msisdn("") == ""


def test_bsuid_detection_and_exact_hashing():
    assert _is_bsuid("IN.1A2B3C4D5E")
    assert not _is_bsuid("919876543210")
    assert not _is_bsuid("")
    # v16 U2: BSUID hashed as FULL string — and scoped per clinic
    a = _crm_phone_hash("HX_CLINIC_A", "IN.1A2B3C4D5E")
    b = _crm_phone_hash("HX_CLINIC_B", "IN.1A2B3C4D5E")
    assert a != b and len(a) == 40
    # format-insensitive: same digits, different punctuation → same row
    assert (_crm_phone_hash("HX_A", "+91 98765 43210")
            == _crm_phone_hash("HX_A", "91 98765-43210"))
    # v16g6 R6-H4: the hash canonicalises through _normalize_msisdn, so a
    # trunk-0 / bare-national spelling CONVERGES onto the E.164 identity —
    # same patient typed three ways is one CRM row now (was a GEN-5 gap).
    assert (_crm_phone_hash("HX_A", "+91 98765 43210")
            == _crm_phone_hash("HX_A", "09876543210")
            == _crm_phone_hash("HX_A", "9876543210"))
