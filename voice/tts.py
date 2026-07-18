"""Text-to-speech backends for Mnemos voice.

Default prints the text (no speakers needed) and captures spoken lines so the loop is
testable. A command backend speaks via any external TTS CLI named in env MNEMOS_TTS_CMD,
with the text piped on stdin -- brand-free, point it at any local engine. The command
backend is not exercised by the tests.
"""

from __future__ import annotations

import os
import shlex
import subprocess


class TextToSpeech:
    def say(self, text: str, voice: str | None = None) -> None:
        raise NotImplementedError


class TextTTS(TextToSpeech):
    """Prints instead of speaking; records spoken lines for inspection/tests."""

    def __init__(self, echo: bool = True):
        self.spoken: list[str] = []
        self._echo = echo

    def say(self, text: str, voice: str | None = None) -> None:
        self.spoken.append(text)
        if self._echo:
            tag = f"({voice}) " if voice and voice != "neutral" else ""
            print(f"mnemos> {tag}{text}")


class CommandTTS(TextToSpeech):
    """Speak via an external command (env MNEMOS_TTS_CMD), text piped on stdin."""

    def __init__(self):
        self._cmd = os.environ.get("MNEMOS_TTS_CMD")
        if not self._cmd:
            raise RuntimeError("CommandTTS needs env MNEMOS_TTS_CMD (a local TTS CLI)")

    def say(self, text: str, voice: str | None = None) -> None:  # pragma: no cover
        env = dict(os.environ)
        if voice:
            env["MNEMOS_TTS_VOICE"] = voice
        subprocess.run(shlex.split(self._cmd), input=text, text=True, timeout=120, env=env)
