"""Integration adapters for your own accounts (Notion live; Slack, Gmail draft-only).

Notion is LIVE when MNEMOS_NOTION_TOKEN and MNEMOS_NOTION_PARENT_PAGE are set: it creates a
page under that parent via the Notion API. Without them it falls back to a local draft.
Slack and Gmail stay draft-only (a local outbox file) until their own tokens are built and
verified. Everything runs through the risk gate; Slack and Gmail also carry the disclosure.
Account identifiers and tokens live only in the gitignored .env, never in the repo.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from .base import Adapter, register


def _draft(name: str, payload: str, root: Path, account: str | None) -> list[str]:
    account = account or "(account not configured)"
    outbox = root / "outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
    rel = f"outbox/{name}-{stamp}.md"
    header = (
        f"# DRAFT for {name} -> {account}\n"
        f"# NOT sent/posted -- live delivery needs a {name} token (not configured)\n\n"
    )
    (root / rel).write_text(header + payload, encoding="utf-8")
    return [rel]


class DraftAdapter(Adapter):
    def __init__(self, name, risk, *, third_party=False, disclosure="", account_env=""):
        super().__init__(name, risk, third_party=third_party, disclosure=disclosure)
        self._account_env = account_env

    def deliver(self, payload: str, *, root: Path) -> list[str]:
        return _draft(self.name, payload, root, os.environ.get(self._account_env))


class NotionAdapter(Adapter):
    """Live to your own Notion workspace when MNEMOS_NOTION_TOKEN and
    MNEMOS_NOTION_PARENT_PAGE are set (creates a child page via the API); otherwise a local
    draft. Risk 3 -> needs approval either way."""

    API = "https://api.notion.com/v1"
    VERSION = "2022-06-28"

    def __init__(self):
        super().__init__("notion", 3, third_party=False)

    def deliver(self, payload: str, *, root: Path) -> list[str]:
        token = os.environ.get("MNEMOS_NOTION_TOKEN")
        parent = os.environ.get("MNEMOS_NOTION_PARENT_PAGE")
        if not (token and parent):
            return _draft(self.name, payload, root, os.environ.get("MNEMOS_NOTION_ACCOUNT"))
        return [self._create_page(token, parent, payload)]

    def _create_page(self, token: str, parent: str, payload: str) -> str:  # pragma: no cover
        lines = [ln for ln in payload.splitlines() if ln.strip()]
        title = (lines[0] if lines else "Mnemos note")[:100]
        children = []
        for ln in lines[1:] or lines[:1]:
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": ln[:1900]}}]},
                }
            )
            if len(children) >= 90:
                break
        body = {
            "parent": {"page_id": parent},
            "properties": {"title": {"title": [{"text": {"content": title}}]}},
            "children": children,
        }
        req = urllib.request.Request(
            f"{self.API}/pages",
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": self.VERSION,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"notion API {exc.code}: {exc.read().decode()[:300]}") from exc
        return data.get("url") or f"notion:page:{data.get('id')}"


def register_integrations() -> None:
    register(NotionAdapter())
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
