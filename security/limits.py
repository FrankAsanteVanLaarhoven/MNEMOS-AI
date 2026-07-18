"""Local rate and token-budget guard for Mnemos.

A single-user tool does not need per-IP internet rate limiting; it needs to not blow a
token budget or hammer the model in a runaway loop. This is an in-process guard: a
sliding-window request cap plus a cumulative token budget with a warn threshold and a
hard stop. Time is passed in by the caller so behaviour is deterministic and testable.
"""

from __future__ import annotations

import os
from collections import deque
from dataclasses import dataclass, field


class RateExceeded(RuntimeError):
    pass


class BudgetExceeded(RuntimeError):
    pass


def estimate_tokens(text: str) -> int:
    """Rough token estimate (~4 chars/token). Good enough for a local budget guard."""
    return max(1, len(text) // 4)


@dataclass
class Guard:
    max_per_minute: int = 60
    token_budget: int | None = None  # None = unlimited
    warn_at: float = 0.8
    _times: deque = field(default_factory=deque)
    _tokens: int = 0
    _warned: bool = False

    @classmethod
    def from_env(cls) -> Guard:
        tb = os.environ.get("MNEMOS_TOKEN_BUDGET")
        return cls(
            max_per_minute=int(os.environ.get("MNEMOS_MAX_PER_MIN", "60")),
            token_budget=int(tb) if tb else None,
        )

    def check_rate(self, now: float) -> None:
        cutoff = now - 60.0
        while self._times and self._times[0] < cutoff:
            self._times.popleft()
        if len(self._times) >= self.max_per_minute:
            raise RateExceeded(f"rate limit: {self.max_per_minute}/min")
        self._times.append(now)

    def add_tokens(self, n: int) -> None:
        self._tokens += max(0, n)

    @property
    def tokens_used(self) -> int:
        return self._tokens

    def check_budget(self) -> str | None:
        """Raise if the budget is exhausted; return a one-time warning string near it."""
        if self.token_budget is None:
            return None
        if self._tokens >= self.token_budget:
            raise BudgetExceeded(
                f"token budget {self.token_budget} exhausted (used {self._tokens})"
            )
        if not self._warned and self._tokens >= self.warn_at * self.token_budget:
            self._warned = True
            return f"warning: {self._tokens}/{self.token_budget} tokens used"
        return None
