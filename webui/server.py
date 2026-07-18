"""Localhost-only browser voice UI server for Mnemos.

Binds 127.0.0.1. Serves one page and a POST /ask endpoint: JSON {text, approve?} in, JSON
{specialist, persona, voice, risk, output, note, escalated, approved, ran, sources} out.
The browser does speech-to-text and text-to-speech with native Web APIs; the server only
runs the governed Mnemos runner over text -- so no audio ever leaves the machine, no third
party is contacted, and the server stays testable.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from runner.model import get_backend
from runner.orchestrator import run
from runner.registry import load_registry, persona_of
from security.limits import Guard

_DIR = Path(__file__).parent
_HTML = (_DIR / "index.html").read_bytes()
_STATIC = {
    "/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json"),
    "/sw.js": ("sw.js", "application/javascript"),
    "/icon-192.png": ("icon-192.png", "image/png"),
    "/icon-512.png": ("icon-512.png", "image/png"),
}


def answer(text: str, *, approve: bool = False, backend=None, guard=None) -> dict:
    res = run(text, approve=approve, backend=backend, guard=guard)
    persona, voice = "Mnemos", "neutral"
    if res.specialist:
        specs = {s["name"]: s for s in load_registry()}
        persona, voice = persona_of(specs.get(res.specialist, {}))
    return {
        "specialist": res.specialist,
        "persona": persona,
        "voice": voice,
        "risk": res.risk,
        "output": res.output,
        "note": res.note,
        "escalated": res.escalated,
        "approved": res.approved,
        "ran": res.ran,
        "sources": res.sources,
    }


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silence
        pass

    def _send(self, code: int, ctype: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", _HTML)
        elif self.path in _STATIC:
            fname, ctype = _STATIC[self.path]
            self._send(200, ctype, (_DIR / fname).read_bytes())
        else:
            self._send(404, "text/plain", b"not found")

    def do_POST(self):
        if self.path != "/ask":
            self._send(404, "text/plain", b"not found")
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._send(400, "application/json", b'{"error":"bad json"}')
            return
        text = (payload.get("text") or "").strip()
        if not text:
            self._send(400, "application/json", b'{"error":"empty"}')
            return
        result = answer(
            text,
            approve=bool(payload.get("approve")),
            backend=get_backend(),
            guard=Guard.from_env(),
        )
        self._send(200, "application/json", json.dumps(result).encode())


def make_server(port: int = 8766) -> HTTPServer:
    return HTTPServer(("127.0.0.1", port), _Handler)


def serve(port: int = 8766) -> None:  # pragma: no cover
    srv = make_server(port)
    print(f"Mnemos voice UI at http://127.0.0.1:{port}  (Ctrl-C to stop)")
    srv.serve_forever()
