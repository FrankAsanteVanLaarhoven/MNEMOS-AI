"""Secret handling for Mnemos.

Secrets come from the environment or the OS keyring -- never from tracked files. `redact`
scrubs secret-looking values out of anything bound for a log or the audit trail, so keys
and tokens never land on disk in the clear.
"""

from __future__ import annotations

import os
import re

# env var names whose *values* must never be logged
_SECRET_HINTS = ("KEY", "TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL")
_BEARER = re.compile(r"(?i)\b(bearer\s+)[A-Za-z0-9._\-]{8,}")


def secret_values() -> list[str]:
    """Current environment values that look like secrets (longest first, so overlapping
    values redact cleanly)."""
    vals = [v for k, v in os.environ.items() if v and any(h in k.upper() for h in _SECRET_HINTS)]
    return sorted(set(vals), key=len, reverse=True)


def redact(text: str) -> str:
    if not text:
        return text
    out = text
    for v in secret_values():
        out = out.replace(v, "[REDACTED]")
    out = _BEARER.sub(r"\1[REDACTED]", out)
    return out


def get_secret(name: str) -> str | None:
    """Env first, then the OS keyring if the optional `keyring` package is present."""
    v = os.environ.get(name)
    if v:
        return v
    try:
        import keyring
    except Exception:
        return None
    try:  # pragma: no cover - depends on a configured keyring backend
        return keyring.get_password("mnemos", name)
    except Exception:  # pragma: no cover
        return None
