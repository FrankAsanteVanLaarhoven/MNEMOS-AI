"""Append-only JSONL audit log for Mnemos.

One line per action, each carrying the evidence sources it used. High-stakes actions
also record the approval decision. Logs live under audit/ and are gitignored -- the
audit trail is local, never published.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from security.secrets import redact

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUDIT_DIR = ROOT / "audit"


def record(
    action: str,
    specialist: str,
    sources: list[str],
    *,
    risk: int = 0,
    high_stakes: bool = False,
    approved: bool | None = None,
    output_preview: str = "",
    audit_dir: Path | str | None = None,
) -> dict:
    audit_dir = Path(audit_dir) if audit_dir else DEFAULT_AUDIT_DIR
    audit_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    entry = {
        "ts": now.isoformat(),
        "action": action,
        "specialist": specialist,
        "sources": sources,
        "risk": risk,
        "high_stakes": high_stakes,
        "approved": approved,
        "output_preview": redact(output_preview)[:200],
    }
    path = audit_dir / (now.strftime("%Y-%m-%d") + ".jsonl")
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry
