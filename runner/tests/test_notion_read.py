"""Tests for Notion read block rendering (pure function; no network).

Run:  python -m pytest runner/tests/test_notion_read.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runner.notion_read import blocks_to_text  # noqa: E402


def test_blocks_to_text_renders_paragraphs_and_headings():
    blocks = [
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "hello"}]}},
        {"type": "heading_1", "heading_1": {"rich_text": [{"plain_text": "Title"}]}},
        {"type": "divider", "divider": {}},  # no rich_text -> skipped
        {"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "world"}]}},
    ]
    assert blocks_to_text(blocks) == "hello\nTitle\nworld"


def test_blocks_to_text_empty():
    assert blocks_to_text([]) == ""


def _run_all():
    import traceback

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        try:
            fn()
            passed += 1
            print(f"PASS {fn.__name__}")
        except Exception:
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{passed}/{len(fns)} passed")
    return passed == len(fns)


if __name__ == "__main__":
    raise SystemExit(0 if _run_all() else 1)
