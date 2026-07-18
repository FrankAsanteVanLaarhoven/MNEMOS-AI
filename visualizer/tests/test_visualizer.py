"""Test that the visualizer serves its page and binds to localhost only.

Run:  python -m pytest visualizer/tests -q  (or)  python visualizer/tests/test_visualizer.py
"""

from __future__ import annotations

import sys
import threading
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from visualizer.server import make_server  # noqa: E402


def test_serves_index_and_binds_localhost():
    srv = make_server(0)  # ephemeral port
    assert srv.server_address[0] == "127.0.0.1"
    threading.Thread(target=srv.handle_request, daemon=True).start()
    port = srv.server_address[1]
    body = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5).read().decode()
    srv.server_close()
    assert "<canvas" in body and "mnemosSetState" in body


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
