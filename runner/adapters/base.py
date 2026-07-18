"""Adapter framework: governed delivery to output channels.

Every delivery runs through the same risk/authority gate as a specialist, plus two hard
rules for channels that reach other people (see the package docstring).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from runner import audit
from runner.registry import gate_for

REPO_ROOT = Path(__file__).resolve().parents[2]


class Adapter:
    """A governed output channel. Subclasses implement `deliver`."""

    def __init__(self, name: str, risk: int, *, third_party: bool = False, disclosure: str = ""):
        self.name = name
        self.risk = risk
        self.third_party = third_party
        self.disclosure = disclosure

    def deliver(self, payload: str, *, root: Path) -> list[str]:
        raise NotImplementedError


@dataclass
class DeliveryResult:
    adapter: str
    delivered: bool
    written: list[str] = field(default_factory=list)
    note: str = ""


_ADAPTERS: dict[str, Adapter] = {}


def register(adapter: Adapter) -> None:
    _ADAPTERS[adapter.name] = adapter


def get(name: str) -> Adapter | None:
    return _ADAPTERS.get(name)


def names() -> list[str]:
    return sorted(_ADAPTERS)


def send(
    name: str,
    payload: str,
    *,
    approve: bool = False,
    signoff: bool = False,
    root: Path | str | None = None,
    audit_dir=None,
) -> DeliveryResult:
    adapter = _ADAPTERS.get(name)
    if adapter is None:
        return DeliveryResult(name, False, note=f"unknown adapter: {name}")

    # Rule 1: a third-party channel must disclose it is automated.
    if adapter.third_party and not adapter.disclosure:
        return DeliveryResult(
            name, False, note="third-party channel refused: no AI-disclosure configured"
        )

    # Rule 2: the risk gate (never autonomous for approval/professional/prohibited).
    gate = gate_for(adapter.risk)
    if gate == "prohibited":
        audit.record(
            "adapter-prohibited", name, [], risk=adapter.risk, approved=False, audit_dir=audit_dir
        )
        return DeliveryResult(name, False, note=f"prohibited (risk {adapter.risk})")
    if gate in ("approval", "professional") and not approve:
        audit.record(
            "adapter-blocked", name, [], risk=adapter.risk, approved=False, audit_dir=audit_dir
        )
        return DeliveryResult(name, False, note=f"risk {adapter.risk} needs approval (--yes)")
    if gate == "professional" and not signoff:
        audit.record(
            "adapter-blocked-signoff",
            name,
            [],
            risk=adapter.risk,
            approved=True,
            audit_dir=audit_dir,
        )
        return DeliveryResult(
            name, False, note=f"risk {adapter.risk} needs professional sign-off (--signoff)"
        )

    body = f"{adapter.disclosure}\n\n{payload}" if adapter.third_party else payload
    written = adapter.deliver(body, root=Path(root) if root else REPO_ROOT)
    audit.record(
        "adapter-delivered",
        name,
        written,
        risk=adapter.risk,
        high_stakes=(adapter.risk >= 3),
        approved=(True if gate != "auto" else None),
        output_preview=body,
        audit_dir=audit_dir,
    )
    return DeliveryResult(name, True, written=written)
