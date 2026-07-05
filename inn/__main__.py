# __main__ — CLI entry: python -m inn breathe
#
# Stores: nothing
# Refuses: exhale until layer 5 (prints held JSON, exit 1)
# Returns: exit code; inhale prints JSON packet to stdout
# Test: tests/positive/test_cold_wake.py

"""CLI — python -m inn breathe"""

from __future__ import annotations

import argparse
import json
import sys

from inn import breath
from inn.errors import BreathRefusal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="inn", description="The Dog-Ear")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_breathe = sub.add_parser("breathe", help="inhale packet (M0.5 ground fitting)")
    p_breathe.add_argument(
        "direction",
        nargs="?",
        choices=("in", "out"),
        default="in",
        help="in: arrival (default); out: departure (not implemented)",
    )

    args = parser.parse_args(argv)

    if args.cmd == "breathe":
        if args.direction == "out":
            try:
                breath.exhale()
            except BreathRefusal as exc:
                print(json.dumps({"breath": "out", "clear": False, "held": [str(exc)]}, indent=2))
                return 1
        else:
            print(breath.inhale_json())
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
