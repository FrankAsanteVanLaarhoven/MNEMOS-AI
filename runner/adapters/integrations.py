"""Integration adapters for your own accounts (Notion + Gmail live; Slack draft-only).

- Notion is LIVE when MNEMOS_NOTION_TOKEN + MNEMOS_NOTION_PARENT_PAGE are set (creates a
  page via the API); else a local draft.
- Gmail is LIVE when MNEMOS_GMAIL_ACCOUNT + MNEMOS_GMAIL_APP_PASSWORD are set (sends via
  Google SMTP; works for gmail.com and Google Workspace domains); else a local draft. A
  payload may start with `To:` / `Subject:` lines; without a `To:` it emails the account
  itself.
- Slack stays draft-only until its token is built and verified.

Everything runs through the risk gate; Slack/Gmail also carry the disclosure. Account
identifiers and tokens live only in the gitignored .env, never in the repo.
"""

from __future__ import annotations

import json
import os
import smtplib
import urllib.error
import urllib.request
from datetime import UTC, datetime
from email.message import EmailMessage
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


def parse_email(text: str, default_to: str) -> tuple[str, str, str]:
    """Pull optional `To:` / `Subject:` lines out of the payload; the rest is the body
    (the disclosure line, if any, stays in the body). Missing `To:` -> the account itself."""
    to, subject = default_to, "Mnemos message"
    body = []
    for ln in text.splitlines():
        s = ln.strip()
        low = s.lower()
        if low.startswith("to:") and "@" in s:
            to = s.split(":", 1)[1].strip()
        elif low.startswith("subject:"):
            subject = s.split(":", 1)[1].strip()
        else:
            body.append(ln)
    return to, subject, "\n".join(body).strip()


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


class GmailAdapter(Adapter):
    """Live email via Google SMTP when MNEMOS_GMAIL_ACCOUNT + MNEMOS_GMAIL_APP_PASSWORD are
    set (gmail.com or a Google Workspace domain); otherwise a local draft. Risk 3,
    third-party, disclosed."""

    def __init__(self):
        super().__init__(
            "gmail",
            3,
            third_party=True,
            disclosure="Prepared by Mnemos, an automated assistant, on Frank's behalf.",
        )

    def deliver(self, payload: str, *, root: Path) -> list[str]:
        account = os.environ.get("MNEMOS_GMAIL_ACCOUNT")
        pw = os.environ.get("MNEMOS_GMAIL_APP_PASSWORD")
        if not (account and pw):
            return _draft(self.name, payload, root, account)
        to, subject, body = parse_email(payload, account)
        return [self._send(account, pw, to, subject, body)]

    def _send(self, account, pw, to, subject, body) -> str:  # pragma: no cover - network
        host = os.environ.get("MNEMOS_SMTP_HOST", "smtp.gmail.com")
        port = int(os.environ.get("MNEMOS_SMTP_PORT", "587"))
        msg = EmailMessage()
        msg["From"] = account
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(host, port, timeout=20) as s:
            s.ehlo()
            s.starttls()
            s.ehlo()
            s.login(account, pw)
            s.send_message(msg)
        return f"email:sent:{to}"


def register_integrations() -> None:
    register(NotionAdapter())
    register(GmailAdapter())
    register(
        DraftAdapter(
            "slack",
            3,
            third_party=True,
            disclosure="Posted via Mnemos, an automated assistant.",
            account_env="MNEMOS_SLACK_ACCOUNT",
        )
    )
