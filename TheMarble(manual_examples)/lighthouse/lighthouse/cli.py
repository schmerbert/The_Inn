"""Keeper's console.

  python -m lighthouse fix     --claim ... --evidence-type ... --evidence ... --verified-against ... --author ...
  python -m lighthouse dr      --note ... [--basis ...] [--author ...]
  python -m lighthouse exhale
  python -m lighthouse check   [--days N]
  python -m lighthouse status
  python -m lighthouse audit
  python -m lighthouse validate
"""

from __future__ import annotations

import argparse
import json
import sys

from lighthouse import (breathe, chart, cottage, exhale, handover, staleness,
                        validate)
from lighthouse.db import connect
from lighthouse.fix import FixRefused, FixRequest, take_fix


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lighthouse")
    parser.add_argument("--db", default=None, help="substrate path (default: data/light.db)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fix = sub.add_parser("fix", help="attempt the Fix crossing into the LOG")
    p_fix.add_argument("--claim", required=True)
    p_fix.add_argument("--evidence-type", required=True)
    p_fix.add_argument("--evidence", required=True)
    p_fix.add_argument("--verified-against", required=True)
    p_fix.add_argument("--author", required=True)

    p_dr = sub.add_parser("dr", help="plot dead reckoning on the chart (no gate; labeled DR)")
    p_dr.add_argument("--note", required=True)
    p_dr.add_argument("--basis", default=None)
    p_dr.add_argument("--author", default="keeper")

    p_sup = sub.add_parser("supersede", help="close a DR plot that work has resolved")
    p_sup.add_argument("dr_id")

    sub.add_parser("exhale", help="arrival packet: warnings, ground, DR pressure")
    p_check = sub.add_parser("check", help="demote stale fixes to DR authority")
    p_check.add_argument("--days", type=int, default=staleness.DEFAULT_MAX_AGE_DAYS)
    sub.add_parser("status", help="counts across LOG, chart, audit")
    sub.add_parser("audit", help="every Fix attempt, passed or refused")
    sub.add_parser("validate", help="arrival docs must point at real files")
    p_breathe = sub.add_parser(
        "breathe", help="in: full arrival breath; out: departure seat check")
    p_breathe.add_argument("direction", nargs="?", choices=("in", "out"),
                           default="in")
    sub.add_parser("sit", help="the keeper's own door: hearth and house, "
                               "labeled interior — never evidence")
    p_keep = sub.add_parser("keep", help="lay something by the fire, signed")
    p_keep.add_argument("--words", required=True)
    p_keep.add_argument("--author", required=True)
    sub.add_parser("handover", help="regrow the seat's gauges from the LOG "
                                    "(run after the narrative, before breathe out)")

    assert set(sub.choices) == set(validate.COMMANDS), (
        "console verbs and validate.COMMANDS have drifted apart"
    )

    args = parser.parse_args(argv)

    if args.cmd == "sit":
        print(json.dumps(cottage.sit(), indent=2))
        return 0

    if args.cmd == "keep":
        try:
            rel = cottage.keep(args.words, args.author)
        except ValueError as err:
            print(json.dumps({"declined": str(err)}))
            return 1
        print(json.dumps({"kept": rel, "label": "interior — signed"}))
        return 0

    if args.cmd == "validate":
        problems = validate.check()
        if problems:
            print(json.dumps({"ok": False, "problems": problems}, indent=2))
            return 1
        print(json.dumps({"ok": True, "problems": []}))
        return 0

    conn = connect(args.db)
    try:
        if args.cmd == "fix":
            req = FixRequest(
                claim=args.claim, evidence_type=args.evidence_type,
                evidence=args.evidence, verified_against=args.verified_against,
                author=args.author,
            )
            try:
                fix_id = take_fix(conn, req)
                print(json.dumps({"fixed": fix_id, "claim": args.claim}))
            except FixRefused as refusal:
                print(json.dumps({"refused": refusal.reason, "claim": args.claim}))
                return 1

        elif args.cmd == "dr":
            dr_id = chart.plot(conn, args.note, args.author, args.basis)
            print(json.dumps({"plotted": dr_id, "label": "DR — pressure, not ground"}))

        elif args.cmd == "supersede":
            chart.supersede(conn, args.dr_id)
            print(json.dumps({"superseded": args.dr_id}))

        elif args.cmd == "exhale":
            print(json.dumps(exhale.packet(conn), indent=2))

        elif args.cmd == "check":
            demoted = staleness.check(conn, max_age_days=args.days)
            print(json.dumps({"demoted": demoted}, indent=2))

        elif args.cmd == "status":
            counts = {}
            for label, query in (
                ("fixes_active", "SELECT COUNT(*) FROM fix WHERE status='active'"),
                ("fixes_stale", "SELECT COUNT(*) FROM fix WHERE status='stale'"),
                ("chart_open", "SELECT COUNT(*) FROM chart WHERE status='open'"),
                ("audit_entries", "SELECT COUNT(*) FROM fix_audit"),
            ):
                counts[label] = conn.execute(query).fetchone()[0]
            print(json.dumps(counts, indent=2))

        elif args.cmd == "handover":
            stamped = handover.stamp(conn)
            print(json.dumps({"stamped": stamped,
                              "note": "gauges regrown from the LOG"
                              if stamped else "no HANDOFF.md to stamp"}))
            if not stamped:
                return 1

        elif args.cmd == "breathe":
            if args.direction == "in":
                result = breathe.inhale(conn)
                print(json.dumps(result, indent=2))
                if not result["door"]["ok"]:
                    return 1
            else:
                result = breathe.out(conn)
                print(json.dumps(result, indent=2))
                if not result["clear"]:
                    return 1

        elif args.cmd == "audit":
            rows = [dict(r) for r in conn.execute(
                "SELECT attempted_at, claim, outcome, reason FROM fix_audit ORDER BY seq"
            ).fetchall()]
            print(json.dumps(rows, indent=2))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
