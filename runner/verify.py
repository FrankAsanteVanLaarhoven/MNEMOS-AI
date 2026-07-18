"""Independent challenge / verify pass: evidence before execution.

A specialist marked `verify` has its output checked by a second, independent model pass
that judges whether every claim is grounded in the primed sources. An unsupported verdict
flags the output and skips any side-effecting action -- unverified output never persists or
is delivered.

The verifier is deliberately a separate call (optionally a separate backend) so it does
not simply agree with the primary model.
"""

from __future__ import annotations

from dataclasses import dataclass

_VERIFIER_SYSTEM = (
    "You are an independent verifier. Judge only whether the OUTPUT is grounded in the "
    "SOURCES. Do not add new information or opinions."
)


@dataclass
class Verdict:
    ok: bool
    detail: str


def challenge(output: str, source_text: str, backend) -> Verdict:
    prompt = (
        "SOURCES:\n"
        + source_text
        + "\n\nOUTPUT:\n"
        + output
        + "\n\nIf every factual claim in OUTPUT is supported by SOURCES, reply exactly "
        "'VERDICT: SUPPORTED'. Otherwise reply 'VERDICT: UNSUPPORTED' followed by the "
        "unsupported claims."
    )
    resp = backend.complete(_VERIFIER_SYSTEM, prompt)
    ok = "UNSUPPORTED" not in resp.upper()
    return Verdict(ok=ok, detail=resp.strip()[:300])
