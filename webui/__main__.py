"""Run the Mnemos browser voice UI (localhost only):

    python -m webui        # then open http://127.0.0.1:8766

The model follows MNEMOS_MODEL_* (default: offline stub). Source your .env first to use the
local model on the 4080:  set -a; source .env; set +a
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from webui.server import serve  # noqa: E402

if __name__ == "__main__":
    serve(8766)
