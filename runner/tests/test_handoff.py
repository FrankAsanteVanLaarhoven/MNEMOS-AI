"""Tests for multi-skill handoff (run_plan) and route_all.

Run:  python -m pytest runner/tests/test_handoff.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner.model import StubBackend  # noqa: E402
from runner.orchestrator import run_plan  # noqa: E402
from runner.router import route_all  # noqa: E402

A = {
    "name": "a",
    "job": "vault/03-jobs/governance-scan.md",
    "triggers": ["alpha"],
    "risk": 0,
    "handoff": ["b"],
}
B = {"name": "b", "job": "vault/03-jobs/governance-scan.md", "triggers": ["beta"], "risk": 0}
C = {"name": "c", "job": "vault/03-jobs/governance-scan.md", "triggers": ["gamma"], "risk": 0}
POOL = [A, B, C]


def test_route_all_returns_all_matches():
    assert {s["name"] for s in route_all("alpha beta", POOL)} == {"a", "b"}
    assert route_all("nothing here", POOL) == []


def test_plan_chains_primary_then_allowed_handoff(tmp_path):
    results = run_plan(
        "alpha beta gamma", specialists=POOL, backend=StubBackend(), audit_dir=tmp_path
    )
    # a is primary; b is in a's handoff allow-list; c matches but is NOT allowed -> skipped
    assert [r.specialist for r in results] == ["a", "b"]


def test_plan_runs_primary_only_when_no_allowed_handoff(tmp_path):
    results = run_plan("alpha gamma", specialists=POOL, backend=StubBackend(), audit_dir=tmp_path)
    assert [r.specialist for r in results] == ["a"]


def test_plan_no_match(tmp_path):
    results = run_plan("zzz", specialists=POOL, backend=StubBackend(), audit_dir=tmp_path)
    assert len(results) == 1 and results[0].specialist is None


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
