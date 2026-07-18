"""Run the Mnemos voice loop as push-to-talk-by-typing (text backends) by default:

    python -m voice
    python -m voice --visualizer     # also serve http://127.0.0.1:8765

For real audio, wire CommandSTT / CommandTTS via MNEMOS_STT_CMD / MNEMOS_TTS_CMD. The
model backend follows MNEMOS_MODEL_* (default: offline stub).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runner.model import get_backend  # noqa: E402
from security.limits import Guard  # noqa: E402
from voice.loop import converse  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(prog="mnemos-voice")
    ap.add_argument("--visualizer", action="store_true", help="serve the localhost visualizer")
    ap.add_argument(
        "--audio", action="store_true", help="microphone + speaker (needs MNEMOS_*_CMD)"
    )
    args = ap.parse_args()

    viz = None
    if args.visualizer:
        from visualizer.server import serve_in_thread, set_state

        serve_in_thread(8765)
        viz = set_state
        print("Visualizer at http://127.0.0.1:8765")

    stt = tts = None
    if args.audio:
        from voice.stt import MicCommandSTT
        from voice.tts import CommandTTS

        stt, tts = MicCommandSTT(), CommandTTS()
        print("Mnemos voice loop (audio mode; say 'exit' to end).")
    else:
        print("Mnemos voice loop (type to talk; 'exit' to end).")

    converse(stt, tts, backend=get_backend(), guard=Guard.from_env(), viz=viz)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
