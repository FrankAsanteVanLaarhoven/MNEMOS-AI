"""Tests for the governed channel-adapter framework.

Run:  python -m pytest runner/tests/test_adapters.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner import adapters  # noqa: E402


def test_note_adapter_auto_local(tmp_path):
    r = adapters.send("note", "a local reminder", root=tmp_path, audit_dir=tmp_path)
    assert r.delivered
    notes = tmp_path / "outbox" / "notes.md"
    assert notes.exists() and "a local reminder" in notes.read_text()


def test_email_third_party_blocked_without_approval(tmp_path):
    r = adapters.send("email", "Hello client", root=tmp_path, audit_dir=tmp_path)
    assert not r.delivered and "approval" in r.note
    assert (
        not list((tmp_path / "outbox").glob("email-*.md"))
        if (tmp_path / "outbox").exists()
        else True
    )


def test_email_delivers_with_approval_and_discloses(tmp_path):
    r = adapters.send("email", "Hello client", approve=True, root=tmp_path, audit_dir=tmp_path)
    assert r.delivered and r.written
    body = (tmp_path / r.written[0]).read_text()
    assert "automated assistant" in body  # disclosure prepended
    assert "Hello client" in body


def test_unknown_adapter_refused(tmp_path):
    r = adapters.send("telephony", "call someone", root=tmp_path, audit_dir=tmp_path)
    assert not r.delivered and "unknown adapter" in r.note


def test_third_party_requires_disclosure():
    from runner.adapters import base

    class Bad(base.Adapter):
        def __init__(self):
            super().__init__("bad-nodisc", risk=3, third_party=True, disclosure="")

        def deliver(self, payload, *, root):
            return []

    base.register(Bad())
    try:
        r = base.send("bad-nodisc", "hi", approve=True)
        assert not r.delivered and "no AI-disclosure" in r.note
    finally:
        base._ADAPTERS.pop("bad-nodisc", None)


def test_delivery_failure_is_caught(tmp_path):
    from runner.adapters import base

    class Boom(base.Adapter):
        def __init__(self):
            super().__init__("boom", risk=0)

        def deliver(self, payload, *, root):
            raise RuntimeError("kaboom")

    base.register(Boom())
    try:
        r = base.send("boom", "hi", root=tmp_path, audit_dir=tmp_path)
        assert not r.delivered and "delivery failed" in r.note and "kaboom" in r.note
    finally:
        base._ADAPTERS.pop("boom", None)


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
