"""Safe, local-only adapters: an email draft and a note.

No network, no third-party contact. An email is written to a local outbox for you to
review and send yourself -- Mnemos does not send it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from .base import Adapter, register


class EmailDraftAdapter(Adapter):
    def __init__(self):
        super().__init__(
            "email",
            risk=3,
            third_party=True,
            disclosure=(
                "This message was prepared by Mnemos, an automated assistant, on Frank's behalf."
            ),
        )

    def deliver(self, payload: str, *, root: Path) -> list[str]:
        outbox = root / "outbox"
        outbox.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        rel = f"outbox/email-{stamp}.md"
        (root / rel).write_text(payload, encoding="utf-8")
        return [rel]


class NoteAdapter(Adapter):
    def __init__(self):
        super().__init__("note", risk=2, third_party=False)

    def deliver(self, payload: str, *, root: Path) -> list[str]:
        outbox = root / "outbox"
        outbox.mkdir(parents=True, exist_ok=True)
        rel = "outbox/notes.md"
        with (root / rel).open("a", encoding="utf-8") as f:
            f.write(payload.rstrip() + "\n")
        return [rel]


def register_default() -> None:
    register(EmailDraftAdapter())
    register(NoteAdapter())
