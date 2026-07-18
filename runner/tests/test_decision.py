"""Tests for the governed decisioning specialist (routing + auto-run)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner.model import StubBackend  # noqa: E402
from runner.orchestrator import run  # noqa: E402
from runner.registry import load_registry  # noqa: E402
from runner.router import route  # noqa: E402

REGISTRY = load_registry()


def test_decision_is_registered_and_low_risk():
    spec = next((s for s in REGISTRY if s["name"] == "decision"), None)
    assert spec is not None and spec["risk"] == 1  # recommends only -> auto gate


def test_routes_to_decision():
    spec = route("what are my options here, help me decide", REGISTRY)
    assert spec is not None and spec["name"] == "decision"


def test_decision_runs_without_approval(tmp_path):
    res = run(
        "give me options and help me decide",
        backend=StubBackend(),
        specialists=REGISTRY,
        audit_dir=tmp_path,
    )
    assert res.ran and res.specialist == "decision" and res.risk == 1


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
