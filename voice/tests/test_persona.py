"""Persona + voice plumbing (no audio; text backend)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner.model import StubBackend  # noqa: E402
from runner.registry import persona_of  # noqa: E402
from voice.loop import converse  # noqa: E402
from voice.stt import TextSTT  # noqa: E402
from voice.tts import TextTTS  # noqa: E402


def test_persona_of_defaults_and_lookup():
    assert persona_of({}) == ("Mnemos", "neutral")
    assert persona_of({"persona": {"name": "Ada", "voice": "female"}}) == ("Ada", "female")


def test_texttts_say_accepts_voice():
    t = TextTTS(echo=False)
    t.say("hello", voice="male")
    assert t.spoken == ["hello"]


def test_voice_announces_acting_persona(tmp_path):
    stt = TextSTT(script=["scan the status", "exit"])
    tts = converse(
        stt, TextTTS(echo=False), backend=StubBackend(), audit_dir=tmp_path, action_root=tmp_path
    )
    joined = "\n".join(tts.spoken)
    assert "This is Vera." in joined  # governance-scan's persona is announced


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
