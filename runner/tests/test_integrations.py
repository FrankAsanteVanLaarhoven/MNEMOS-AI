"""Tests for the integration adapters (draft path + email parsing; no network, no creds).

The live Notion (`_create_page`) and Gmail (`_send`) paths run against real credentials,
not here. Run:  python -m pytest runner/tests/test_integrations.py -q
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner import adapters  # noqa: E402
from runner.adapters.integrations import parse_email  # noqa: E402


def test_notion_drafts_without_token(tmp_path):
    saved = {
        k: os.environ.pop(k, None) for k in ("MNEMOS_NOTION_TOKEN", "MNEMOS_NOTION_PARENT_PAGE")
    }
    os.environ["MNEMOS_NOTION_ACCOUNT"] = "me@example.com"
    try:
        r = adapters.send("notion", "a page body", approve=True, root=tmp_path, audit_dir=tmp_path)
        assert r.delivered
        body = (tmp_path / r.written[0]).read_text()
        assert "DRAFT for notion" in body and "me@example.com" in body and "NOT sent/posted" in body
    finally:
        os.environ.pop("MNEMOS_NOTION_ACCOUNT", None)
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v


def test_notion_needs_approval(tmp_path):
    r = adapters.send("notion", "a page body", root=tmp_path, audit_dir=tmp_path)
    assert not r.delivered and "approval" in r.note  # risk 3 -> gated


def test_slack_third_party_blocked_without_approval(tmp_path):
    r = adapters.send("slack", "hello team", root=tmp_path, audit_dir=tmp_path)
    assert not r.delivered and "approval" in r.note


def test_gmail_drafts_without_credentials(tmp_path):
    saved = os.environ.pop("MNEMOS_GMAIL_APP_PASSWORD", None)
    os.environ["MNEMOS_GMAIL_ACCOUNT"] = "me@example.com"
    try:
        r = adapters.send("gmail", "Dear client", approve=True, root=tmp_path, audit_dir=tmp_path)
        assert r.delivered
        body = (tmp_path / r.written[0]).read_text()
        assert "automated assistant" in body  # disclosure prepended
        assert "NOT sent/posted" in body  # never actually sent
    finally:
        os.environ.pop("MNEMOS_GMAIL_ACCOUNT", None)
        if saved is not None:
            os.environ["MNEMOS_GMAIL_APP_PASSWORD"] = saved


def test_parse_email_defaults_to_self():
    to, subject, body = parse_email("just a body line", "me@x.com")
    assert to == "me@x.com" and subject == "Mnemos message" and body == "just a body line"


def test_parse_email_extracts_to_and_subject():
    payload = "Disclosure line\n\nTo: bob@x.com\nSubject: Hi Bob\n\nBody here"
    to, subject, body = parse_email(payload, "me@x.com")
    assert to == "bob@x.com" and subject == "Hi Bob"
    assert "Body here" in body and "Disclosure line" in body and "To:" not in body


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
