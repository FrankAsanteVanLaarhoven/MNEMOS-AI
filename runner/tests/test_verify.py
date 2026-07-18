"""Tests for the independent challenge/verify pass (evidence before execution).

Run:  python -m pytest runner/tests/test_verify.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner.model import StubBackend  # noqa: E402
from runner.orchestrator import run  # noqa: E402
from runner.verify import challenge  # noqa: E402


class FakeVerifier:
    """Returns a controllable verdict, independent of the primary output."""

    def __init__(self, ok: bool):
        self._ok = ok

    def complete(self, system: str, prompt: str) -> str:
        return "VERDICT: SUPPORTED" if self._ok else "VERDICT: UNSUPPORTED: claim X not in sources"


VER = {
    "name": "ver-demo",
    "job": "vault/03-jobs/governance-scan.md",
    "triggers": ["verifyme"],
    "risk": 0,
    "verify": True,
    "action": "write-checkpoint",
}


def test_challenge_supported():
    assert challenge("out", "src", FakeVerifier(True)).ok


def test_challenge_unsupported():
    assert not challenge("out", "src", FakeVerifier(False)).ok


def test_verify_unsupported_skips_action(tmp_path):
    res = run(
        "verifyme now",
        backend=StubBackend(),
        verifier_backend=FakeVerifier(False),
        specialists=[VER],
        audit_dir=tmp_path,
        action_root=tmp_path,
    )
    assert res.escalated and "unsupported" in res.note.lower()
    daily = tmp_path / "vault" / "01-daily"
    assert not daily.exists() or not list(daily.glob("*.md"))  # action was skipped


def test_verify_supported_runs_action(tmp_path):
    res = run(
        "verifyme now",
        backend=StubBackend(),
        verifier_backend=FakeVerifier(True),
        specialists=[VER],
        audit_dir=tmp_path,
        action_root=tmp_path,
    )
    assert res.ran and not res.escalated
    assert list((tmp_path / "vault" / "01-daily").glob("*.md"))  # action ran


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
