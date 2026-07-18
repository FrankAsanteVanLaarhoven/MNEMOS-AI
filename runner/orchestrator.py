"""Mnemos master orchestrator: prime -> route -> run specialist -> audit.

Follows the boot contract: read core/boot.md + vault/INDEX.md + the specialist's job
note (+ any target project note) before acting, cite those sources, and record the
action. High-stakes specialists require explicit approval before they run.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from security.limits import BudgetExceeded, Guard, RateExceeded, estimate_tokens
from security.validate import InvalidInput, clean_request

from . import audit
from .actions import ActionContext, has_action, run_action
from .model import ModelBackend, get_backend
from .registry import gate_for, load_registry, risk_of
from .router import route
from .verify import challenge

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
    risk: int = 0
    escalated: bool = False
    verdict: str = ""
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
    guard: Guard | None = None,
    action_root=None,
    signoff: bool = False,
    verifier_backend: ModelBackend | None = None,
) -> Result:
    try:
        request = clean_request(request)
    except InvalidInput as exc:
        return Result(specialist=None, output="", note=f"rejected input: {exc}")

    if guard is not None:
        try:
            guard.check_rate(time.monotonic())
        except RateExceeded as exc:
            return Result(specialist=None, output="", note=f"rate limited: {exc}")

    specialists = specialists if specialists is not None else load_registry()
    spec = route(request, specialists)
    if spec is None:
        names = ", ".join(s["name"] for s in specialists)
        return Result(
            specialist=None,
            output="",
            note=f"no specialist matched; choose one of: {names}",
        )

    risk = risk_of(spec)
    gate = gate_for(risk)
    boundary = spec.get("boundary") or "a qualified professional"
    needs_approval = gate in ("approval", "professional")
    approved_flag = True if needs_approval else None

    if gate == "prohibited":
        audit.record(
            "prohibited",
            spec["name"],
            [spec["job"]],
            risk=risk,
            high_stakes=True,
            approved=False,
            audit_dir=audit_dir,
        )
        return Result(
            specialist=spec["name"],
            output="",
            approved=False,
            ran=False,
            risk=risk,
            escalated=True,
            note=f"prohibited (risk {risk}); requires multi-party authorisation via {boundary}",
        )

    if needs_approval and not approve:
        audit.record(
            "blocked-awaiting-approval",
            spec["name"],
            [spec["job"]],
            risk=risk,
            high_stakes=True,
            approved=False,
            audit_dir=audit_dir,
        )
        return Result(
            specialist=spec["name"],
            output="",
            approved=False,
            ran=False,
            risk=risk,
            note=f"risk {risk} requires approval (pass --yes / approve=True)",
        )

    if gate == "professional" and not signoff:
        audit.record(
            "blocked-awaiting-signoff",
            spec["name"],
            [spec["job"]],
            risk=risk,
            high_stakes=True,
            approved=True,
            audit_dir=audit_dir,
        )
        return Result(
            specialist=spec["name"],
            output="",
            approved=True,
            ran=False,
            risk=risk,
            escalated=True,
            note=f"risk {risk}: requires professional sign-off by {boundary} (pass --signoff)",
        )

    system, sources = prime(spec, target_note)

    warn = None
    if guard is not None:
        guard.add_tokens(estimate_tokens(system) + estimate_tokens(request))
        try:
            warn = guard.check_budget()
        except BudgetExceeded as exc:
            return Result(
                specialist=spec["name"],
                output="",
                approved=approved_flag,
                risk=risk,
                note=f"budget stop: {exc}",
            )

    backend = backend or get_backend()
    output = backend.complete(system, request)
    if guard is not None:
        guard.add_tokens(estimate_tokens(output))

    verdict = ""
    if spec.get("verify"):
        checked = challenge(output, system, verifier_backend or backend)
        verdict = checked.detail
        audit.record(
            "verify",
            spec["name"],
            sources,
            risk=risk,
            approved=approved_flag,
            output_preview=checked.detail,
            audit_dir=audit_dir,
        )
        if not checked.ok:
            return Result(
                specialist=spec["name"],
                output=output,
                sources=sources,
                approved=approved_flag,
                ran=True,
                risk=risk,
                escalated=True,
                verdict=verdict,
                note="verifier: unsupported claims — action skipped",
            )

    action_name = spec.get("action")
    if has_action(action_name):
        result = run_action(
            action_name,
            ActionContext(
                root=Path(action_root) if action_root else ROOT,
                request=request,
                output=output,
                target_note=target_note,
            ),
        )
        sources = sources + result.written
        output = f"{output}\n\n({result.message})"

    if gate == "professional":
        output = f"[ESCALATED — draft for review by {boundary}; not final advice]\n{output}"

    audit.record(
        "ran",
        spec["name"],
        sources,
        risk=risk,
        high_stakes=(risk >= 3),
        approved=approved_flag,
        output_preview=output,
        audit_dir=audit_dir,
    )
    return Result(
        specialist=spec["name"],
        output=output,
        sources=sources,
        approved=approved_flag,
        ran=True,
        risk=risk,
        escalated=(gate == "professional"),
        verdict=verdict,
        note=warn or "",
    )
