"""Tests for the Mnemos voice loop, using text STT/TTS (no audio) and the stub model.

Run:  python -m pytest voice/tests -q    (or)    python voice/tests/test_voice.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner.model import StubBackend  # noqa: E402
from voice.loop import converse  # noqa: E402
from voice.stt import TextSTT  # noqa: E402
from voice.tts import TextTTS  # noqa: E402


def test_low_stakes_spoken_with_evidence(tmp_path):
    stt = TextSTT(script=["scan the status", "exit"])
    tts = converse(
        stt, TextTTS(echo=False), backend=StubBackend(), audit_dir=tmp_path, action_root=tmp_path
    )
    joined = "\n".join(tts.spoken)
    assert "[stub]" in joined
    assert "Sources:" in joined and "vault/03-jobs/governance-scan.md" in joined
    assert "Ending the session." in tts.spoken


def test_high_stakes_requires_spoken_yes(tmp_path):
    stt = TextSTT(script=["write a checkpoint", "yes", "exit"])
    tts = converse(
        stt, TextTTS(echo=False), backend=StubBackend(), audit_dir=tmp_path, action_root=tmp_path
    )
    joined = "\n".join(tts.spoken)
    assert "high-stakes action" in joined
    assert "[stub]" in joined  # ran after spoken approval


def test_high_stakes_declined_when_not_yes(tmp_path):
    stt = TextSTT(script=["write a checkpoint", "no", "exit"])
    tts = converse(
        stt, TextTTS(echo=False), backend=StubBackend(), audit_dir=tmp_path, action_root=tmp_path
    )
    joined = "\n".join(tts.spoken)
    assert "Skipped write-checkpoint." in joined
    assert "[stub]" not in joined  # never ran


def test_unmatched_speaks_choices(tmp_path):
    stt = TextSTT(script=["tell me a joke", "exit"])
    tts = converse(
        stt, TextTTS(echo=False), backend=StubBackend(), audit_dir=tmp_path, action_root=tmp_path
    )
    joined = "\n".join(tts.spoken)
    assert "no specialist matched" in joined


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
