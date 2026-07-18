"""Tests for the expert registry and the risk/authority gate.

Run:  python -m pytest runner/tests/test_registry.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner.model import StubBackend  # noqa: E402
from runner.orchestrator import run  # noqa: E402
from runner.registry import gate_for, load_registry, risk_of, validate  # noqa: E402

GOV = next(s for s in load_registry() if s["name"] == "governance-scan")

PROF = {
    "name": "prof-demo",
    "job": "vault/03-jobs/governance-scan.md",
    "triggers": ["legaladvice"],
    "risk": 5,
    "boundary": "a qualified solicitor",
    "description": "demo professional-boundary specialist",
}
PROHIB = {
    "name": "prohib-demo",
    "job": "vault/03-jobs/governance-scan.md",
    "triggers": ["wiremoney"],
    "risk": 6,
    "description": "demo prohibited specialist",
}


def test_gate_mapping():
    assert [gate_for(r) for r in range(7)] == [
        "auto",
        "auto",
        "auto",
        "approval",
        "approval",
        "professional",
        "prohibited",
    ]


def test_shipped_registry_validates():
    names = {s["name"] for s in load_registry()}
    assert {"governance-scan", "write-checkpoint"} <= names


def test_validate_rejects_bad_risk():
    assert validate({"name": "x", "job": "j", "risk": 9})
    assert validate({"name": "x", "job": "j", "risk": True})
    assert validate({"name": "x", "job": "j", "risk": 0}) == []


def test_risk_of_legacy_high_stakes():
    assert risk_of({"high_stakes": True}) == 3
    assert risk_of({"high_stakes": False}) == 0
    assert risk_of({"risk": 5}) == 5


def test_risk0_auto_runs(tmp_path):
    res = run("scan status", backend=StubBackend(), specialists=[GOV], audit_dir=tmp_path)
    assert res.ran and res.risk == 0 and res.approved is None


def test_risk5_needs_approval_then_signoff(tmp_path):
    r1 = run("please legaladvice", backend=StubBackend(), specialists=[PROF], audit_dir=tmp_path)
    assert not r1.ran and r1.risk == 5  # blocked: no approval

    r2 = run(
        "please legaladvice",
        approve=True,
        backend=StubBackend(),
        specialists=[PROF],
        audit_dir=tmp_path,
    )
    assert not r2.ran and r2.escalated  # approved but needs professional sign-off

    r3 = run(
        "please legaladvice",
        approve=True,
        signoff=True,
        backend=StubBackend(),
        specialists=[PROF],
        audit_dir=tmp_path,
    )
    assert r3.ran and r3.escalated and "ESCALATED" in r3.output


def test_risk6_prohibited_never_runs(tmp_path):
    r = run(
        "wiremoney now",
        approve=True,
        signoff=True,
        backend=StubBackend(),
        specialists=[PROHIB],
        audit_dir=tmp_path,
    )
    assert not r.ran and r.escalated and "prohibited" in r.note


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
