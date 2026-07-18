"""Governed Notion read: pull a page's text into Mnemos (risk 1, audited).

Reads are low risk (information only) and never write. The token comes from
MNEMOS_NOTION_TOKEN. Block rendering is a pure function so it is testable without a network.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from . import audit

API = "https://api.notion.com/v1"
VERSION = "2022-06-28"


def blocks_to_text(blocks: list) -> str:
    lines = []
    for b in blocks:
        t = b.get("type", "")
        node = b.get(t)
        rich = node.get("rich_text", []) if isinstance(node, dict) else []
        text = "".join(x.get("plain_text", "") for x in rich)
        if text:
            lines.append(text)
    return "\n".join(lines)


def read_page(page_id: str, *, audit_dir=None) -> dict:  # pragma: no cover - network
    token = os.environ.get("MNEMOS_NOTION_TOKEN")
    if not token:
        raise RuntimeError("MNEMOS_NOTION_TOKEN not set")
    headers = {"Authorization": f"Bearer {token}", "Notion-Version": VERSION}
    req = urllib.request.Request(
        f"{API}/blocks/{page_id}/children?page_size=100", headers=headers, method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.load(r)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"notion API {exc.code}: {exc.read().decode()[:200]}") from exc
    text = blocks_to_text(data.get("results", []))
    audit.record("notion-read", "notion", [f"notion:page:{page_id}"], risk=1, audit_dir=audit_dir)
    return {"id": page_id, "text": text}
