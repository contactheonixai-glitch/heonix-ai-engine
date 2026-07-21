"""HEONIX GEN-5 — entry point.  Deploy command: gunicorn heonix.main:app
(unchanged single-artifact deploy; the package ships as one repo/build).
Route modules register themselves on `app` at import time — same flat
Flask pattern as the original file, split across files.
"""
from __future__ import annotations

import os

from heonix.config import cfg
from heonix.logsetup import log
from heonix.api.app import app, startup, _install_signal_handlers

# Route registration (order preserved from the original file):
import heonix.api.routes_public   # noqa: F401,E402
import heonix.api.webhooks        # noqa: F401,E402
import heonix.api.admin           # noqa: F401,E402
import heonix.api.errors          # noqa: F401,E402

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
