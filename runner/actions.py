"""Vault side-effect handlers for Mnemos specialists.

A specialist may declare an `action`; after the model produces its text, the orchestrator
runs the action to persist that text into the vault. All writes are appends (never
overwrites), so they are safe to run behind the high-stakes approval gate and are recorded
in the audit trail. This is what makes Mnemos a memory that accumulates, not a read-only
prompt template.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class ActionContext:
    root: Path
    request: str
    output: str
    target_note: str | None = None


@dataclass
class ActionResult:
    message: str
    written: list[str] = field(default_factory=list)


def _today() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


def append_daily(ctx: ActionContext) -> ActionResult:
    """Append the model's checkpoint text to today's daily log, and (if a target note is
    given) leave a dated pointer at the end of that note. Both are appends."""
    day = _today()
    rel = f"vault/01-daily/{day}.md"
    path = ctx.root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    header = f"# {day} — Daily log\n" if not path.exists() else ""
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{header}\n## checkpoint\n{ctx.output.strip()}\n")
    written = [rel]

    if ctx.target_note:
        note = ctx.root / ctx.target_note
        if note.exists():
            with note.open("a", encoding="utf-8") as f:
                f.write(f"\n- checkpoint {day}: see {rel}\n")
            written.append(ctx.target_note)

    return ActionResult(message=f"checkpoint written to {rel}", written=written)


_ACTIONS = {"write-checkpoint": append_daily}


def has_action(name: str | None) -> bool:
    return bool(name) and name in _ACTIONS


def run_action(name: str, ctx: ActionContext) -> ActionResult:
    handler = _ACTIONS.get(name)
    if handler is None:
        raise KeyError(f"unknown action: {name}")
    return handler(ctx)
