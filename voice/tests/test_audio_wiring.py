"""Engine-neutral audio wiring tests (no real audio hardware).

The mic->transcribe pipeline is driven by fake shell commands so the plumbing is verified
without a microphone or ASR model.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from voice.stt import MicCommandSTT  # noqa: E402


def test_mic_command_stt_pipeline():
    os.environ["MNEMOS_MIC_CMD"] = "true"  # "records" (no-op, exit 0)
    os.environ["MNEMOS_STT_CMD"] = "python3 -c \"print('hello mnemos')\""
    try:
        assert MicCommandSTT().listen() == "hello mnemos"
    finally:
        os.environ.pop("MNEMOS_MIC_CMD", None)
        os.environ.pop("MNEMOS_STT_CMD", None)


def test_mic_command_stt_requires_env():
    os.environ.pop("MNEMOS_MIC_CMD", None)
    os.environ.pop("MNEMOS_STT_CMD", None)
    try:
        MicCommandSTT()
        raised = False
    except RuntimeError:
        raised = True
    assert raised


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
