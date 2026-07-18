"""Mnemos voice loop: listen -> run through the runner -> speak. Backend-agnostic.

Uses the same orchestrator as the text CLI, so routing, priming, evidence citation, and
the high-stakes approval gate all apply. Approval in voice is spoken: a high-stakes action
is announced and proceeds only on a spoken 'yes'.
"""

from __future__ import annotations

from runner.orchestrator import run

from .stt import SpeechToText, TextSTT
from .tts import TextToSpeech, TextTTS

_STOP = {"exit", "quit", "stop", "goodbye"}
_YES = {"yes", "y", "yeah", "approve", "confirm", "do it"}


def converse(
    stt: SpeechToText | None = None,
    tts: TextToSpeech | None = None,
    *,
    backend=None,
    max_turns: int | None = None,
    audit_dir=None,
) -> TextToSpeech:
    stt = stt or TextSTT()
    tts = tts or TextTTS()
    turns = 0
    while max_turns is None or turns < max_turns:
        text = stt.listen()
        if text is None:
            break
        text = text.strip()
        if not text:
            continue
        if text.lower() in _STOP:
            tts.say("Ending the session.")
            break
        turns += 1
        res = run(text, backend=backend, audit_dir=audit_dir)
        if res.specialist is None:
            tts.say(res.note)
            continue
        if res.approved is False and not res.ran:
            tts.say(f"{res.specialist} is a high-stakes action. Say yes to proceed.")
            reply = (stt.listen() or "").strip().lower()
            if reply in _YES:
                res = run(text, approve=True, backend=backend, audit_dir=audit_dir)
            else:
                tts.say(f"Skipped {res.specialist}.")
                continue
        tts.say(res.output)
        if res.sources:
            tts.say("Sources: " + ", ".join(res.sources))
    return tts
