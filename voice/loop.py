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
    guard=None,
    viz=None,
    action_root=None,
) -> TextToSpeech:
    stt = stt or TextSTT()
    tts = tts or TextTTS()

    def state(s):
        if viz is not None:
            viz(s)

    turns = 0
    state("idle")
    while max_turns is None or turns < max_turns:
        state("listening")
        text = stt.listen()
        if text is None:
            break
        text = text.strip()
        if not text:
            continue
        if text.lower() in _STOP:
            state("speaking")
            tts.say("Ending the session.")
            break
        turns += 1
        state("thinking")
        res = run(text, backend=backend, audit_dir=audit_dir, guard=guard, action_root=action_root)
        if res.specialist is None:
            state("speaking")
            tts.say(res.note)
            state("idle")
            continue
        if res.escalated or res.risk >= 5:
            state("speaking")
            tts.say(res.note)
            state("idle")
            continue
        if res.approved is False and not res.ran:
            state("speaking")
            tts.say(f"{res.specialist} is a risk {res.risk} action. Say yes to proceed.")
            state("listening")
            reply = (stt.listen() or "").strip().lower()
            if reply in _YES:
                state("thinking")
                res = run(
                    text,
                    approve=True,
                    backend=backend,
                    audit_dir=audit_dir,
                    guard=guard,
                    action_root=action_root,
                )
            else:
                state("speaking")
                tts.say(f"Skipped {res.specialist}.")
                state("idle")
                continue
        state("speaking")
        tts.say(res.output)
        if res.sources:
            tts.say("Sources: " + ", ".join(res.sources))
        if res.note:
            tts.say(res.note)
        state("idle")
    state("idle")
    return tts
