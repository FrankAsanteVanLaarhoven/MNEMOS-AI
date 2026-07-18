"""Tests for the browser voice UI server (text path only; browser audio is native).

Run:  python -m pytest webui/tests -q
"""

from __future__ import annotations

import json
import sys
import threading
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner.model import StubBackend  # noqa: E402
from webui.server import answer, make_server  # noqa: E402


def test_answer_returns_persona_and_voice():
    d = answer("scan the status", backend=StubBackend())
    assert d["specialist"] == "governance-scan"
    assert d["persona"] == "Vera" and d["voice"] == "female"
    assert d["output"].startswith("[stub]")


def test_server_serves_page_and_ask_binds_localhost():
    srv = make_server(0)  # ephemeral port
    assert srv.server_address[0] == "127.0.0.1"
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]
    try:
        html = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5).read().decode()
        assert "mic" in html.lower() and "speechSynthesis" in html

        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/ask",
            data=json.dumps({"text": "scan the status"}).encode(),
            headers={"Content-Type": "application/json"},
        )
        d = json.load(urllib.request.urlopen(req, timeout=10))
        assert d["specialist"] == "governance-scan" and d["persona"] == "Vera"
    finally:
        srv.shutdown()
        srv.server_close()


def _run_all():
    import traceback

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
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
