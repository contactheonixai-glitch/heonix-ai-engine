"""Boots the full engine once (SQLite mode) and probes the public surface."""


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.get_json()["engine"] == "HEONIX"


def test_health(client):
    r = client.get("/health")
    body = r.get_json()
    assert r.status_code == 200
    assert body["engine"].startswith("HEONIX Ultra")
    assert body["db_healthy"] is True and body["db_mode"] == "sqlite"
    assert body["pii_encryption"] is True
    assert set(body["ai_providers"]) == {"gemini", "openai", "claude"}


def test_ready_fail_closed_without_ai_keys(client):
    # No AI keys in the test env → the engine must report NOT ready (503),
    # exactly as GEN-4 does. With any provider key set this flips to 200.
    r = client.get("/ready")
    assert r.status_code == 503
    assert r.get_json() == {"ready": False, "reason": "No AI providers configured"}


def test_security_headers_present(client):
    r = client.get("/")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Request-ID")
