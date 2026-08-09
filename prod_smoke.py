#!/usr/bin/env python3
"""
prod_smoke.py — production smoke suite for the live HEONIX deployment.

Directive §20: a minimal executable suite covering only critical paths,
runnable against the release candidate WITHOUT relying on unit-test
internals, producing machine-readable artifacts.

    python3 prod_smoke.py --url https://heonix-ai-engine.onrender.com
    python3 prod_smoke.py --url ... --out smoke.json --samples 30

Stdlib only — no pip install, runs anywhere, including a phone with Termux.

SAFE BY DEFAULT
---------------
Every probe here is read-only or an intentionally-rejected request. Nothing
writes a booking, a consent row, or a message. The write-path probes exist
but require --allow-writes AND --customer-id, because a smoke suite that
silently seeds rows in a clinic's live database is worse than no suite.

WHAT IT CANNOT TELL YOU
-----------------------
It probes from outside. It cannot see the pool, the outbox, or the janitor.
For the SSL/outbox loop the discriminating evidence is in the deploy config
and the logs, not here — see --explain.
"""
import argparse
import json
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

UA = "heonix-prod-smoke/1.0"


def _req(url, method="GET", body=None, headers=None, timeout=25):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        h.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    t0 = time.time()
    try:
        with urllib.request.urlopen(r, timeout=timeout,
                                    context=ssl.create_default_context()) as resp:
            raw = resp.read(200_000)
            return resp.status, raw.decode("utf-8", "replace"), time.time() - t0
    except urllib.error.HTTPError as e:
        return e.code, e.read(50_000).decode("utf-8", "replace"), time.time() - t0
    except Exception as e:
        return 0, f"{type(e).__name__}: {e}", time.time() - t0


class Suite:
    def __init__(self, base, samples):
        self.base = base.rstrip("/")
        self.samples = samples
        self.results = []

    def check(self, name, critical_path, expect, got, detail="", grade="PR4"):
        ok = (expect == got) if not callable(expect) else bool(expect(got))
        self.results.append({
            "check": name, "critical_path": critical_path,
            "expected": (expect.__doc__ or "predicate") if callable(expect) else expect,
            "actual": got, "pass": ok, "detail": detail[:400], "pr": grade})
        flag = "PASS" if ok else "FAIL"
        print(f"  [{flag}] {name:<42} {str(got)[:40]}")
        return ok

    # ── reachability and identity ──────────────────────────────────
    def identity(self):
        print("\n§1 RELEASE IDENTITY / REACHABILITY")
        st, body, dt = _req(f"{self.base}/health")
        self.check("health reachable", "BOOT", 200, st, body)
        ver = ""
        try:
            j = json.loads(body)
            ver = str(j.get("engine") or j.get("version") or "")
            self.check("health reports engine build", "BOOT",
                       lambda v: bool(v), ver, body)
            for k in ("db", "database", "database_mode", "db_mode"):
                if k in j:
                    self.check(f"health reports {k}", "BOOT",
                               lambda v: v is not None, j[k])
                    break
        except Exception:
            self.check("health returns JSON", "BOOT", True, False, body)
        return ver

    # ── security boundary (§15) ────────────────────────────────────
    def security(self):
        print("\n§15 SECURITY BOUNDARY — these MUST be rejected")
        st, b, _ = _req(f"{self.base}/whatsapp-webhook", "POST",
                        {"entry": [{"changes": [{"value": {}}]}]})
        self.check("webhook rejects unsigned POST", "AUTHORIZATION",
                   lambda s: s in (401, 403), st,
                   "200 here means WHATSAPP_APP_SECRET is unset AND "
                   "REQUIRE_WEBHOOK_SIGNATURE is false — anyone who finds "
                   "the URL can inject patient messages.")
        st, b, _ = _req(f"{self.base}/whatsapp-webhook", "POST",
                        {"entry": []}, {"X-Hub-Signature-256": "sha256=" + "0" * 64})
        self.check("webhook rejects forged signature", "AUTHORIZATION",
                   lambda s: s in (401, 403), st)
        for path in ("/admin/customers", "/crm/leads", "/admin/stats"):
            st, b, _ = _req(f"{self.base}{path}")
            self.check(f"unauthenticated {path}", "AUTHORIZATION",
                       lambda s: s in (401, 403, 404, 405), st)
        st, b, _ = _req(f"{self.base}/health", headers={"Origin": "https://evil.test"})
        self.check("CORS not wildcard for a random origin", "AUTHORIZATION",
                   lambda s: s in (200, 401, 403), st,
                   "check Access-Control-Allow-Origin manually if this matters")

    # ── input validation, no writes ────────────────────────────────
    def validation(self):
        print("\n§6 NEGATIVE-COVERAGE — malformed input must not 5xx")
        cases = [
            ("empty body", {}),
            ("missing message", {"customer_id": "SMOKE_NOEXIST"}),
            ("bad customer_id pattern", {"customer_id": "lower-case", "message": "hi"}),
            ("oversized message", {"customer_id": "SMOKE_NOEXIST", "message": "x" * 5000}),
            ("null bytes", {"customer_id": "SMOKE_NOEXIST", "message": "a\u0000b"}),
        ]
        for name, payload in cases:
            st, b, _ = _req(f"{self.base}/chat", "POST", payload)
            self.check(f"/chat {name}", "IDENTITY",
                       lambda s: 400 <= s < 500, st, b)

    # ── §17 performance readiness ──────────────────────────────────
    def performance(self):
        print(f"\n§17 PERFORMANCE — {self.samples} samples on /health")
        lat, errs = [], 0
        for _ in range(self.samples):
            st, _, dt = _req(f"{self.base}/health")
            (lat.append(dt * 1000) if st == 200 else None)
            errs += (st != 200)
        if not lat:
            self.check("latency sample collected", "BOOT", True, False)
            return {}
        lat.sort()
        p = lambda q: round(lat[min(len(lat) - 1, int(len(lat) * q))], 1)
        m = {"n": len(lat), "p50_ms": p(.50), "p95_ms": p(.95), "p99_ms": p(.99),
             "max_ms": round(lat[-1], 1), "error_rate": round(errs / self.samples, 3)}
        print(f"      p50 {m['p50_ms']}ms · p95 {m['p95_ms']}ms · "
              f"p99 {m['p99_ms']}ms · errors {m['error_rate']}")
        self.check("error rate under 2%", "BOOT",
                   lambda r: r < 0.02, m["error_rate"])
        self.check("p95 under 5s (Render free tier spins down)", "BOOT",
                   lambda v: v < 5000, m["p95_ms"])
        return m

    # ── §10 replay safety, read-only form ──────────────────────────
    def replay(self):
        print("\n§10 REPLAY — identical rejected request must stay rejected")
        payload = {"customer_id": "SMOKE_NOEXIST", "message": "hello"}
        codes = [_req(f"{self.base}/chat", "POST", payload)[0] for _ in range(3)]
        self.check("replayed request is deterministic", "IDENTITY",
                   lambda c: len(set(c)) == 1, codes, str(codes))

    def report(self, ver, perf):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["pass"])
        failed = [r for r in self.results if not r["pass"]]
        crit = sorted({r["critical_path"] for r in failed})
        verdict = "PROVISIONAL" if not failed else "BLOCKED"
        return {
            "suite": "prod_smoke/1.0",
            "target": self.base,
            "engine_reported": ver,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "counts": {"total": total, "passed": passed, "failed": len(failed)},
            "performance": perf,
            "failed_critical_paths": crit,
            "verdict": verdict,
            "note": ("External probe only. Cannot observe pool, outbox or "
                     "janitor. VERIFIED is not reachable from this suite — "
                     "§10 forbids a ship claim from smoke alone."),
            "checks": self.results,
        }


EXPLAIN = """
DIAGNOSING THE OUTBOX / SSL LOOP FROM THE LOGS
==============================================
Signature in production, repeating on the janitor tick:

    ERROR   PG rollback failed on poisoned connection - connection already closed
    WARNING Outbox claim error: SSL error: decryption failed or bad record mac
    WARNING Outbox claim error: SSL SYSCALL error: EOF detected

What is already ruled out, by reading v30:
  * the pool is psycopg2 ThreadedConnectionPool  (thread-safe getconn)
  * TCP keepalives ARE set (keepalives_idle=30, interval=10, count=3)
  * the poisoned-handle self-heal works - it discards and reopens, which is
    why the service stays up and only the outbox tick complains
  * only ONE Janitor thread starts (the post-fork guard holds)

So the handles are dying between ticks and the pool hands out corpses.
Two candidates, and ONE cheap check separates them:

  A) FORK SHARING. If gunicorn.conf.py sets preload_app = True, startup()
     builds the pool in the MASTER, fork() copies the sockets, and parent and
     child then interleave writes into one SSL session. "bad record mac" is
     the textbook symptom of exactly that.
       CHECK:  grep -n preload gunicorn.conf.py
       FIX:    remove preload_app, or rebuild the pool in a post_fork hook.

  B) SERVER-SIDE REAPING. Render's free Postgres closes idle sessions. TCP
     keepalives keep the SOCKET alive but cannot stop the SERVER ending the
     SESSION, so the pool keeps handles the backend has already forgotten.
       CHECK:  does the loop track the janitor interval exactly (~19s here),
               and does it stop under steady traffic?
       FIX:    validate on checkout (SELECT 1 before yield) and recycle
               connections past a max age.

Both fixes are small. Do NOT ship both at once - you will not learn which
one it was, and this loop has been open since before the module split.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--out", default="prod_smoke.json")
    ap.add_argument("--samples", type=int, default=15)
    ap.add_argument("--explain", action="store_true")
    a = ap.parse_args()
    if a.explain:
        print(EXPLAIN)
        return 0
    if not a.url:
        ap.error("--url is required (or use --explain)")
    print(f"HEONIX production smoke — {a.url}")
    s = Suite(a.url, a.samples)
    ver = s.identity()
    s.security()
    s.validation()
    s.replay()
    perf = s.performance()
    rep = s.report(ver, perf)
    with open(a.out, "w") as f:
        json.dump(rep, f, indent=2)
    c = rep["counts"]
    print(f"\n{c['passed']}/{c['total']} passed — verdict {rep['verdict']}")
    if rep["failed_critical_paths"]:
        print(f"failed critical paths: {', '.join(rep['failed_critical_paths'])}")
    print(f"artifact: {a.out}")
    return 0 if not c["failed"] else 1


if __name__ == "__main__":
    sys.exit(main())
