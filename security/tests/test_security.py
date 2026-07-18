"""Tests for the Mnemos security controls (validation, redaction, budget guard).

Run:  python -m pytest security/tests -q    (or)    python security/tests/test_security.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner.model import StubBackend  # noqa: E402
from runner.orchestrator import run  # noqa: E402
from security.limits import BudgetExceeded, Guard, RateExceeded, estimate_tokens  # noqa: E402
from security.secrets import redact  # noqa: E402
from security.validate import InvalidInput, clean_request  # noqa: E402


def test_clean_request_strips_and_trims():
    assert clean_request("  hi\x00 there \n") == "hi there"


def test_clean_request_rejects_empty():
    for bad in ["", "   ", "\x00"]:
        try:
            clean_request(bad)
            raised = False
        except InvalidInput:
            raised = True
        assert raised, bad


def test_clean_request_rejects_too_long():
    try:
        clean_request("a" * 5000)
        raised = False
    except InvalidInput:
        raised = True
    assert raised


def test_redact_removes_env_secret():
    os.environ["MNEMOS_TEST_API_KEY"] = "supersecretvalue123"
    try:
        out = redact("the token is supersecretvalue123 ok")
        assert "supersecretvalue123" not in out and "[REDACTED]" in out
    finally:
        del os.environ["MNEMOS_TEST_API_KEY"]


def test_redact_bearer_token():
    out = redact("Authorization: Bearer abcdef1234567890")
    assert "abcdef1234567890" not in out and "[REDACTED]" in out


def test_estimate_tokens():
    assert estimate_tokens("abcd" * 10) == 10
    assert estimate_tokens("") == 1


def test_rate_limit_window():
    g = Guard(max_per_minute=2)
    g.check_rate(1000.0)
    g.check_rate(1000.5)
    try:
        g.check_rate(1001.0)
        raised = False
    except RateExceeded:
        raised = True
    assert raised
    g.check_rate(1100.0)  # window has rolled; allowed again


def test_token_budget_warn_then_stop():
    g = Guard(token_budget=100, warn_at=0.8)
    g.add_tokens(50)
    assert g.check_budget() is None
    g.add_tokens(35)  # 85 -> warn once
    assert "warning" in (g.check_budget() or "")
    assert g.check_budget() is None
    g.add_tokens(20)  # 105 -> stop
    try:
        g.check_budget()
        raised = False
    except BudgetExceeded:
        raised = True
    assert raised


def test_run_rejects_bad_input(tmp_path):
    res = run("", backend=StubBackend(), audit_dir=tmp_path)
    assert res.specialist is None and "rejected input" in res.note


def test_run_rate_limited(tmp_path):
    g = Guard(max_per_minute=1)
    r1 = run("scan status", backend=StubBackend(), audit_dir=tmp_path, guard=g)
    r2 = run("scan status", backend=StubBackend(), audit_dir=tmp_path, guard=g)
    assert r1.ran
    assert r2.specialist is None and "rate limited" in r2.note


def _run_all():
    import inspect
    import tempfile
    import traceback

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            if "tmp_path" in inspect.signature(fn).parameters:
                with tempfile.TemporaryDirectory() as d:
                    fn(Path(d))
            else:
                fn()
            passed += 1
            print(f"PASS {fn.__name__}")
        except Exception:
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{passed}/{len(fns)} passed")
    return passed == len(fns)


if __name__ == "__main__":
    raise SystemExit(0 if _run_all() else 1)
