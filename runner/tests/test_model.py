"""Tests for model-backend selection (no network)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner.model import StubBackend, get_backend  # noqa: E402


def test_stub_is_default():
    old = os.environ.pop("MNEMOS_MODEL_BACKEND", None)
    try:
        assert isinstance(get_backend(), StubBackend)
    finally:
        if old is not None:
            os.environ["MNEMOS_MODEL_BACKEND"] = old


def test_http_backend_honours_model_override():
    b = get_backend("http", model="llama3.2:3b")
    assert b.name == "http" and b.model == "llama3.2:3b"


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
