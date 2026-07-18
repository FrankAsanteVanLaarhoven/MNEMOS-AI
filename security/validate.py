"""Input validation for Mnemos requests.

Mnemos is a single-user local tool that does not listen on a public network, so this is
not a hostile-internet firewall. It guards against malformed or oversized input and stops
control characters from being injected into the audit trail.
"""

from __future__ import annotations

MAX_REQUEST_CHARS = 4000


class InvalidInput(ValueError):
    pass


def clean_request(text: str, *, max_chars: int = MAX_REQUEST_CHARS) -> str:
    if not isinstance(text, str):
        raise InvalidInput("request must be text")
    t = text.replace("\x00", "").strip()
    t = "".join(c for c in t if c in "\n\t" or ord(c) >= 32)
    if not t:
        raise InvalidInput("empty request")
    if len(t) > max_chars:
        raise InvalidInput(f"request too long ({len(t)} > {max_chars} chars)")
    return t
