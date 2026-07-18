"""Text front-end for Mnemos. Run from the repo root:

python -m runner.cli "scan the status of a project" --note vault/02-projects/EXAMPLE.md
python -m runner.cli --list
"""

from __future__ import annotations

import argparse

from security.limits import Guard

from .orchestrator import run
from .registry import persona_of, risk_of
from .router import load_specialists


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mnemos", description="Mnemos text concierge")
    ap.add_argument("request", nargs="*", help="what you want Mnemos to do")
    ap.add_argument("--note", help="target project note, e.g. vault/02-projects/EXAMPLE.md")
    ap.add_argument("--backend", default=None, help="stub | http")
    ap.add_argument("--yes", action="store_true", help="approve risk 3-5 actions")
    ap.add_argument("--signoff", action="store_true", help="professional sign-off for risk 5")
    ap.add_argument("--list", action="store_true", help="list specialists and exit")
    ap.add_argument("--list-adapters", action="store_true", help="list channel adapters and exit")
    ap.add_argument("--send", metavar="ADAPTER", help="deliver the text via a channel adapter")
    args = ap.parse_args(argv)

    if args.list:
        for s in load_specialists():
            persona, voice = persona_of(s)
            print(
                f"- {s['name']} (risk {risk_of(s)}, {persona}/{voice}): {s.get('description', '')}"
            )
        return 0

    if args.list_adapters:
        from runner import adapters

        for name in adapters.names():
            a = adapters.get(name)
            tag = "  [third-party: discloses + needs approval]" if a.third_party else ""
            print(f"- {name} (risk {a.risk}){tag}")
        return 0

    request = " ".join(args.request).strip()
    if not request:
        ap.error("no request given")

    if args.send:
        from runner import adapters

        r = adapters.send(args.send, request, approve=args.yes, signoff=args.signoff)
        if r.delivered:
            print(f"delivered via {r.adapter}: {', '.join(r.written)}")
            return 0
        print(f"[not delivered] {r.note}")
        return 3

    from .model import get_backend

    backend = get_backend(args.backend) if args.backend else None
    guard = Guard.from_env()

    res = run(
        request,
        target_note=args.note,
        approve=args.yes,
        signoff=args.signoff,
        backend=backend,
        guard=guard,
    )

    if (
        res.specialist
        and res.approved is False
        and not res.ran
        and not res.escalated
        and not args.yes
    ):
        ans = (
            input(f"'{res.specialist}' is a risk {res.risk} action. Proceed? [y/N] ")
            .strip()
            .lower()
        )
        if ans == "y":
            res = run(
                request,
                target_note=args.note,
                approve=True,
                signoff=args.signoff,
                backend=backend,
                guard=guard,
            )
        else:
            print("Aborted. (recorded in audit)")
            return 1

    if res.escalated and not res.ran:
        print(f"[escalated] {res.note}")
        return 3

    if not res.specialist:
        print(res.note)
        return 2

    print(res.output)
    if res.sources:
        print("\nEvidence:")
        for s in res.sources:
            print(f"  - {s}")
    if res.note:
        print(f"\n[{res.note}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
