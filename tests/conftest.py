"""Test env must exist BEFORE any heonix import — cfg is built at import time."""
import os

os.environ.setdefault("DATABASE_MODE", "sqlite")
os.environ.setdefault("DATABASE_FILE", "/tmp/heonix_pytest.db")
os.environ.setdefault("ENCRYPTION_KEY", "ab" * 32)   # valid 64-hex AES-256 key
os.environ.setdefault("LOG_FORMAT", "text")

import pytest


@pytest.fixture(scope="session")
def app():
    from heonix.main import app as flask_app   # boots engine once (SQLite mode)
    return flask_app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()
