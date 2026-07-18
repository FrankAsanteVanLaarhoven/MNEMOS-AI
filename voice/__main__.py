"""Run the Mnemos voice loop as push-to-talk-by-typing (text backends) by default:

    python -m voice

For real audio, wire CommandSTT / CommandTTS via MNEMOS_STT_CMD / MNEMOS_TTS_CMD. The
model backend follows MNEMOS_MODEL_* (default: offline stub).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runner.model import get_backend  # noqa: E402
from voice.loop import converse  # noqa: E402


def main() -> int:
    print("Mnemos voice loop (type to talk; 'exit' to end).")
    converse(backend=get_backend())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
