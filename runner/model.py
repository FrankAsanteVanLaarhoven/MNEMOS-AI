"""Model backends for Mnemos.

The runner never imports a provider SDK directly. It talks to a ModelBackend, so the
model is swappable: an offline deterministic stub (default), or any chat-completions
HTTP endpoint -- a local runtime on the RTX 4080, or a hosted gateway.

Env:
  MNEMOS_MODEL_BACKEND   stub | http        (default: stub)
  MNEMOS_MODEL_BASE_URL  e.g. http://localhost:11434/v1
  MNEMOS_MODEL_NAME      model id to request
  MNEMOS_MODEL_API_KEY   optional bearer token (hosted endpoints)
  MNEMOS_MODEL_TIMEOUT   request timeout in seconds (default: 600; cold loads are slow)
"""

from __future__ import annotations

import json
import os
import urllib.request


class ModelBackend:
    name = "base"

    def complete(self, system: str, prompt: str) -> str:
        raise NotImplementedError


class StubBackend(ModelBackend):
    """Offline, deterministic. Produces a short acknowledgement so the full
    prime -> route -> run -> audit loop can run and be tested without a model."""

    name = "stub"

    def complete(self, system: str, prompt: str) -> str:
        first = prompt.strip().splitlines()[0] if prompt.strip() else ""
        return f"[stub] handled request: {first[:200]}"


class HttpChatBackend(ModelBackend):
    """Any chat-completions HTTP endpoint (local runtime or hosted gateway)."""

    name = "http"

    def __init__(self, model: str | None = None) -> None:
        self.base = os.environ.get("MNEMOS_MODEL_BASE_URL", "http://localhost:11434/v1")
        self.model = model or os.environ.get("MNEMOS_MODEL_NAME", "local")
        self.key = os.environ.get("MNEMOS_MODEL_API_KEY", "")
        self.timeout = float(os.environ.get("MNEMOS_MODEL_TIMEOUT", "600"))

    def complete(self, system: str, prompt: str) -> str:
        body = json.dumps(
            {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
            }
        ).encode()
        headers = {"Content-Type": "application/json"}
        if self.key:
            headers["Authorization"] = f"Bearer {self.key}"
        req = urllib.request.Request(
            self.base.rstrip("/") + "/chat/completions", data=body, headers=headers
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.load(resp)
        return data["choices"][0]["message"]["content"]


def get_backend(name: str | None = None, model: str | None = None) -> ModelBackend:
    name = name or os.environ.get("MNEMOS_MODEL_BACKEND", "stub")
    if name == "stub":
        return StubBackend()
    if name in ("http", "chat"):
        return HttpChatBackend(model=model)
    raise ValueError(f"unknown model backend: {name!r}")
