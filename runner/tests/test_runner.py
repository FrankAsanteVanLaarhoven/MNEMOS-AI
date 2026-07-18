"""Tests for the Mnemos runner. Uses the offline stub backend; writes audit to a tmp dir.

Run:  python -m pytest runner/tests -q    (or)    python runner/tests/test_runner.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner.model import StubBackend  # noqa: E402
from runner.orchestrator import prime, run  # noqa: E402
from runner.router import load_specialists, route  # noqa: E402

SPECS = load_specialists()


def test_routes_governance_scan():
    spec = route("please scan the governance status", SPECS)
    assert spec is not None and spec["name"] == "governance-scan"


def test_routes_write_checkpoint():
    spec = route("write a checkpoint so I can resume later", SPECS)
    assert spec is not None and spec["name"] == "write-checkpoint"


def test_unmatched_returns_none():
    assert route("tell me a joke about penguins", SPECS) is None


def test_prime_includes_core_job_and_note():
    spec = route("scan status", SPECS)
    system, sources = prime(spec, target_note="vault/02-projects/EXAMPLE.md")
    assert "core/boot.md" in sources and "vault/INDEX.md" in sources
    assert spec["job"] in sources and "vault/02-projects/EXAMPLE.md" in sources
    assert "Locked rules" in system  # boot content was actually read


def test_low_stakes_runs_and_audits(tmp_path):
    res = run(
        "scan governance status",
        target_note="vault/02-projects/EXAMPLE.md",
        backend=StubBackend(),
        specialists=SPECS,
        audit_dir=tmp_path,
    )
    assert res.ran and res.specialist == "governance-scan"
    assert res.output.startswith("[stub]")
    assert "vault/02-projects/EXAMPLE.md" in res.sources
    logs = list(Path(tmp_path).glob("*.jsonl"))
    assert logs, "audit line written"
    entry = json.loads(logs[0].read_text().splitlines()[-1])
    assert entry["specialist"] == "governance-scan"
    assert "vault/02-projects/EXAMPLE.md" in entry["sources"]


def test_high_stakes_blocked_without_approval(tmp_path):
    res = run("write a checkpoint", backend=StubBackend(), specialists=SPECS, audit_dir=tmp_path)
    assert res.specialist == "write-checkpoint"
    assert res.ran is False and res.approved is False
    entry = json.loads(list(Path(tmp_path).glob("*.jsonl"))[0].read_text().splitlines()[-1])
    assert entry["approved"] is False and entry["high_stakes"] is True


def test_high_stakes_runs_with_approval(tmp_path):
    res = run(
        "write a checkpoint",
        approve=True,
        backend=StubBackend(),
        specialists=SPECS,
        audit_dir=tmp_path,
    )
    assert res.ran and res.approved is True


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
