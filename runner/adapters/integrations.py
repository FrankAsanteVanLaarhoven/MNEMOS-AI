"""Draft-only integration adapters for your own accounts (Notion, Slack, Gmail).

Each prepares content as a LOCAL draft in outbox/, targeting the account named in an
environment variable (never hardcoded). It does NOT send or post: live delivery needs a
per-channel API credential that is intentionally not built until there is a real token to
build and verify against. Everything still runs through the risk gate; the third-party
channels (Slack, Gmail) also carry the disclosure line and need approval.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

from .base import Adapter, register


class DraftAdapter(Adapter):
    def __init__(self, name, risk, *, third_party=False, disclosure="", account_env=""):
        super().__init__(name, risk, third_party=third_party, disclosure=disclosure)
        self._account_env = account_env

    def deliver(self, payload: str, *, root: Path) -> list[str]:
        account = os.environ.get(self._account_env, "(account not configured)")
        outbox = root / "outbox"
        outbox.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
        rel = f"outbox/{self.name}-{stamp}.md"
        header = (
            f"# DRAFT for {self.name} -> {account}\n"
            f"# NOT sent/posted -- live delivery needs a {self.name} token (not configured)\n\n"
        )
        (root / rel).write_text(header + payload, encoding="utf-8")
        return [rel]


def register_integrations() -> None:
    register(DraftAdapter("notion", 2, account_env="MNEMOS_NOTION_ACCOUNT"))
    register(
        DraftAdapter(
            "slack",
            3,
            third_party=True,
            disclosure="Posted via Mnemos, an automated assistant.",
            account_env="MNEMOS_SLACK_ACCOUNT",
        )
    )
    register(
        DraftAdapter(
            "gmail",
            3,
            third_party=True,
            disclosure="Prepared by Mnemos, an automated assistant, on Frank's behalf.",
            account_env="MNEMOS_GMAIL_ACCOUNT",
        )
    )
