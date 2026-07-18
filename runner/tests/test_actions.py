"""Tests for vault-writing specialist actions (write-checkpoint).

Run:  python -m pytest runner/tests/test_actions.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner.actions import ActionContext, append_daily, has_action, run_action  # noqa: E402
from runner.model import StubBackend  # noqa: E402
from runner.orchestrator import run  # noqa: E402
from runner.router import load_specialists  # noqa: E402

SPECS = load_specialists()


def test_append_daily_writes(tmp_path):
    res = append_daily(ActionContext(root=tmp_path, request="chk", output="state is green"))
    assert res.written
    p = tmp_path / res.written[0]
    assert p.exists() and "state is green" in p.read_text()


def test_append_daily_pointers_target_note(tmp_path):
    note = tmp_path / "vault/02-projects/foo.md"
    note.parent.mkdir(parents=True)
    note.write_text("# Foo\n")
    res = append_daily(
        ActionContext(
            root=tmp_path, request="chk", output="ok", target_note="vault/02-projects/foo.md"
        )
    )
    assert "vault/02-projects/foo.md" in res.written
    assert "checkpoint" in note.read_text()


def test_write_checkpoint_specialist_declares_action():
    spec = next(s for s in SPECS if s["name"] == "write-checkpoint")
    assert has_action(spec.get("action"))


def test_run_write_checkpoint_persists(tmp_path):
    res = run(
        "write a checkpoint",
        approve=True,
        backend=StubBackend(),
        specialists=SPECS,
        audit_dir=tmp_path,
        action_root=tmp_path,
    )
    assert res.ran and res.specialist == "write-checkpoint"
    dailies = list((tmp_path / "vault/01-daily").glob("*.md"))
    assert dailies, "daily log written"
    assert "[stub]" in dailies[0].read_text()
    assert any("01-daily" in s for s in res.sources)


def test_unknown_action_raises():
    try:
        run_action("nope", ActionContext(root=Path("."), request="", output=""))
        raised = False
    except KeyError:
        raised = True
    assert raised


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
