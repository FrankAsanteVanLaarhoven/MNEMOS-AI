"""Speech-to-text backends for Mnemos voice.

Default is a text backend (type instead of speak), so the push-to-talk loop runs and is
testable with no microphone or model. A command backend shells out to any external ASR
CLI named in env MNEMOS_STT_CMD -- Mnemos stays free of a specific engine dependency. The
command backend is not exercised by the tests.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from collections import deque


class SpeechToText:
    def listen(self) -> str | None:
        """Return the next transcript, or None to end the session."""
        raise NotImplementedError


class TextSTT(SpeechToText):
    """Reads lines instead of audio. With a script, pops from it (tests); otherwise reads
    a line from stdin (interactive push-to-talk-by-typing)."""

    def __init__(self, script: list[str] | None = None, prompt: str = "you> "):
        self._script = deque(script) if script is not None else None
        self._prompt = prompt

    def listen(self) -> str | None:
        if self._script is not None:
            return self._script.popleft() if self._script else None
        try:
            return input(self._prompt)
        except EOFError:
            return None


class CommandSTT(SpeechToText):
    """Transcribe a wav file via an external command (env MNEMOS_STT_CMD). The command
    receives the wav path as its final argument and prints the transcript to stdout."""

    def __init__(self, wav_path: str | None = None):
        self._cmd = os.environ.get("MNEMOS_STT_CMD")
        self._wav = wav_path
        if not self._cmd:
            raise RuntimeError("CommandSTT needs env MNEMOS_STT_CMD (a local ASR CLI)")

    def listen(self) -> str | None:  # pragma: no cover
        if not self._wav:
            return None
        out = subprocess.run(
            shlex.split(self._cmd) + [self._wav],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return out.stdout.strip() or None
