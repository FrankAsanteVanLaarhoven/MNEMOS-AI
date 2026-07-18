"""Run the Mnemos visualizer standalone (localhost demo cycling all states):

python -m visualizer      # then open http://127.0.0.1:8765
"""

from __future__ import annotations

import itertools
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from visualizer.server import serve_in_thread, set_state  # noqa: E402


def main() -> int:
    serve_in_thread(8765)
    print("Mnemos visualizer at http://127.0.0.1:8765  (Ctrl-C to stop)")
    cycle = itertools.cycle(["idle", "listening", "thinking", "speaking"])
    try:
        while True:
            set_state(next(cycle))
            time.sleep(2.0)
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
