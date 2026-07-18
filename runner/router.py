"""Transparent, deterministic routing for Mnemos.

Routing is keyword-based and inspectable -- no model call is needed to choose a
specialist. Each specialist config declares trigger words; the request is scored by how
many whole-word triggers it hits, highest score wins. A tie or zero hits returns None so
the caller can ask which specialist to use.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

SPEC_DIR = Path(__file__).resolve().parent / "specialists"


def load_specialists(spec_dir: Path | str | None = None) -> list[dict]:
    spec_dir = Path(spec_dir) if spec_dir else SPEC_DIR
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(spec_dir.glob("*.json"))]


def score(request: str, spec: dict) -> int:
    r = request.lower()
    n = 0
    for t in spec.get("triggers", []):
        if re.search(r"\b" + re.escape(t.lower()) + r"\b", r):
            n += 1
    return n


def route(request: str, specialists: list[dict] | None = None) -> dict | None:
    specialists = specialists if specialists is not None else load_specialists()
    scored = sorted(
        ((score(request, s), s) for s in specialists), key=lambda x: x[0], reverse=True
    )
    if not scored or scored[0][0] == 0:
        return None
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None  # ambiguous -- let the caller disambiguate
    return scored[0][1]
