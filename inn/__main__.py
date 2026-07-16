# __main__ — CLI entry: breathe | host
#
# Stores: nothing
# Refuses: stale exhale seat (via breath.exhale)
# Returns: exit code; inhale JSON / host REPL
# Test: tests/positive/test_cold_wake.py, test_cli_host_tools.py

"""CLI — python -m inn breathe | python -m inn host"""

from __future__ import annotations

import argparse
import json
import sys

from inn import breath
from inn.errors import BreathRefusal


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="inn", description="The Dog-Ear")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_breathe = sub.add_parser("breathe", help="inhale packet or exhale seat check")
    p_breathe.add_argument(
        "direction",
        nargs="?",
        choices=("in", "out"),
        default="in",
        help="in: arrival (default); out: departure seat check",
    )

    sub.add_parser("host", help="OpenAI-compatible guest REPL (see HOST.md)")
    sub.add_parser("pulse", help="Plant a dusk faun gesture for the next wake")

    args = parser.parse_args(argv)

    if args.cmd == "breathe":
        if args.direction == "out":
            try:
                result = breath.exhale()
                print(json.dumps(result, indent=2))
                return 0
            except BreathRefusal as exc:
                print(
                    json.dumps(
                        {"breath": "out", "clear": False, "held": [str(exc)]},
                        indent=2,
                    )
                )
                return 1
        print(breath.inhale_json())
        return 0

    if args.cmd == "host":
        from inn.cli_host import run_repl

        return run_repl()

    if args.cmd == "pulse":
        from inn import forest, pulse, session
        from inn.compare import scan_ground_warnings
        from inn.paths import repo_root

        root = repo_root()
        state = session.load(root)
        forest.init_db(root)
        with forest.connect(root) as conn:
            warns = scan_ground_warnings(root, conn)
        paths = [
            p
            for p in ("manuscript/ground.md", "study/canon.md")
            if (root / p).exists()
        ]
        eid = pulse.plant_stay_gesture(
            root=root,
            current_room=state.current_room,
            warning_count=len(warns),
            ground_paths=paths,
        )
        print(json.dumps({"ok": True, "pulse_id": eid}, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
