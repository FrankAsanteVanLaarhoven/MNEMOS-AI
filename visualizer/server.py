"""Localhost-only visualizer server for Mnemos.

Binds 127.0.0.1 exclusively -- the visualizer is never exposed on a public interface. It
serves one self-contained page plus an SSE stream of the current Mnemos state, which the
voice loop updates via set_state().
"""

from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

_HTML = (Path(__file__).parent / "index.html").read_bytes()
_state = {"value": "idle"}


def set_state(state: str) -> None:
    _state["value"] = state


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silence default request logging
        pass

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(_HTML)))
            self.end_headers()
            self.wfile.write(_HTML)
        elif self.path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                while True:
                    payload = json.dumps({"state": _state["value"]})
                    self.wfile.write(f"data: {payload}\n\n".encode())
                    self.wfile.flush()
                    time.sleep(0.2)
            except (BrokenPipeError, ConnectionResetError):
                return
        else:
            self.send_response(404)
            self.end_headers()


def make_server(port: int = 8765) -> HTTPServer:
    return HTTPServer(("127.0.0.1", port), _Handler)


def serve_in_thread(port: int = 8765) -> HTTPServer:
    srv = make_server(port)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
