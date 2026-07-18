"""Expert registry for Mnemos: load and validate specialists, and map risk to a gate.

Every specialist must be governable: a name, a priming job note, and a risk level (0-6,
per the authority model). Optional governance fields: `boundary` (the qualified
professional a regulated task must route to), `action`, `owner`, `version`. An invalid
registry fails loudly rather than silently mis-routing.

Risk -> gate:
  0-2  auto          runs without approval (information / draft / reversible internal)
  3-4  approval      needs explicit approval (external comms / commercial commitment)
  5    professional  needs approval AND professional sign-off; output is escalated
  6    prohibited    never runs autonomously; always escalates to a human

A specialist cannot be approved through a professional boundary: risk 5 still needs a
deliberate sign-off, and risk 6 never runs. This is the point the enterprise blueprints
keep missing -- the boundary is the product, not the fake professional.
"""

from __future__ import annotations

from .router import load_specialists

REQUIRED = ("name", "job")


def risk_of(spec: dict) -> int:
    """Risk level 0-6. Falls back to the legacy `high_stakes` bool if `risk` is absent."""
    if "risk" in spec:
        return int(spec["risk"])
    return 3 if spec.get("high_stakes") else 0


def gate_for(risk: int) -> str:
    if risk <= 2:
        return "auto"
    if risk <= 4:
        return "approval"
    if risk == 5:
        return "professional"
    return "prohibited"


def validate(spec: dict) -> list[str]:
    errs = [f"missing {f}" for f in REQUIRED if not spec.get(f)]
    risk = spec.get("risk", 3 if spec.get("high_stakes") else 0)
    if isinstance(risk, bool) or not isinstance(risk, int) or not (0 <= risk <= 6):
        errs.append(f"risk must be an int 0-6, got {risk!r}")
    return errs


def load_registry(spec_dir=None) -> list[dict]:
    specs = load_specialists(spec_dir)
    seen: set[str] = set()
    for s in specs:
        errs = validate(s)
        if errs:
            raise ValueError(f"specialist {s.get('name', '?')!r}: {'; '.join(errs)}")
        if s["name"] in seen:
            raise ValueError(f"duplicate specialist name: {s['name']}")
        seen.add(s["name"])
    return specs
