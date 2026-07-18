"""Mnemos master orchestrator: prime -> route -> run specialist -> audit.

Follows the boot contract: read core/boot.md + vault/INDEX.md + the specialist's job
note (+ any target project note) before acting, cite those sources, and record the
action. High-stakes specialists require explicit approval before they run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import audit
from .model import ModelBackend, get_backend
from .router import load_specialists, route

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


@dataclass
class Result:
    specialist: str | None
    output: str
    sources: list[str] = field(default_factory=list)
    approved: bool | None = None
    ran: bool = False
    note: str = ""


def prime(spec: dict, target_note: str | None = None) -> tuple[str, list[str]]:
    sources = ["core/boot.md", "vault/INDEX.md", spec["job"]]
    parts = [_read("core/boot.md"), _read("vault/INDEX.md"), _read(spec["job"])]
    if target_note:
        parts.append(_read(target_note))
        sources.append(target_note)
    return "\n\n---\n\n".join(parts), sources


def run(
    request: str,
    *,
    target_note: str | None = None,
    approve: bool = False,
    backend: ModelBackend | None = None,
    specialists: list[dict] | None = None,
    audit_dir=None,
) -> Result:
    specialists = specialists if specialists is not None else load_specialists()
    spec = route(request, specialists)
    if spec is None:
        names = ", ".join(s["name"] for s in specialists)
        return Result(
            specialist=None,
            output="",
            note=f"no specialist matched; choose one of: {names}",
        )

    high = bool(spec.get("high_stakes"))
    if high and not approve:
        audit.record(
            "blocked-awaiting-approval",
            spec["name"],
            [spec["job"]],
            high_stakes=True,
            approved=False,
            audit_dir=audit_dir,
        )
        return Result(
            specialist=spec["name"],
            output="",
            approved=False,
            ran=False,
            note="high-stakes action requires approval (pass --yes / approve=True)",
        )

    system, sources = prime(spec, target_note)
    backend = backend or get_backend()
    output = backend.complete(system, request)
    audit.record(
        "ran",
        spec["name"],
        sources,
        high_stakes=high,
        approved=(True if high else None),
        output_preview=output,
        audit_dir=audit_dir,
    )
    return Result(
        specialist=spec["name"],
        output=output,
        sources=sources,
        approved=(True if high else None),
        ran=True,
    )
