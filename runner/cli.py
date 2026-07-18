"""Text front-end for Mnemos. Run from the repo root:

    python -m runner.cli "scan the status of a project" --note vault/02-projects/EXAMPLE.md
    python -m runner.cli --list
"""
from __future__ import annotations

import argparse

from .orchestrator import run
from .router import load_specialists


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mnemos", description="Mnemos text concierge")
    ap.add_argument("request", nargs="*", help="what you want Mnemos to do")
    ap.add_argument("--note", help="target project note, e.g. vault/02-projects/EXAMPLE.md")
    ap.add_argument("--backend", default=None, help="stub | http")
    ap.add_argument("--yes", action="store_true", help="pre-approve high-stakes actions")
    ap.add_argument("--list", action="store_true", help="list specialists and exit")
    args = ap.parse_args(argv)

    if args.list:
        for s in load_specialists():
            flag = "  [high-stakes]" if s.get("high_stakes") else ""
            print(f"- {s['name']}: {s.get('description', '')}{flag}")
        return 0

    request = " ".join(args.request).strip()
    if not request:
        ap.error("no request given")

    from .model import get_backend

    backend = get_backend(args.backend) if args.backend else None

    res = run(request, target_note=args.note, approve=args.yes, backend=backend)

    if res.specialist and res.approved is False and not res.ran and not args.yes:
        ans = input(f"'{res.specialist}' is a high-stakes action. Proceed? [y/N] ").strip().lower()
        if ans == "y":
            res = run(request, target_note=args.note, approve=True, backend=backend)
        else:
            print("Aborted. (recorded in audit)")
            return 1

    if not res.specialist:
        print(res.note)
        return 2

    print(res.output)
    if res.sources:
        print("\nEvidence:")
        for s in res.sources:
            print(f"  - {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
