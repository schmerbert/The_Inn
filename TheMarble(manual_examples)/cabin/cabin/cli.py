"""CLI — the terminal front door to the floor.

This module is the thin wrapper between user intent and the library. It owns
argument parsing, calling the library functions exactly as specified, and
formatting output. All law logic lives in the library (db.py, forest.py);
the CLI must never validate or reject a write itself — it calls the library
and reports what the library decided.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from . import db, forest


def open_project() -> tuple[sqlite3.Connection, str]:
    """Open or create the local project database.

    Returns (conn, project_id) where project_id is a stable hash of the
    absolute path to the current working directory.
    """
    db_path = Path("./.cabin/home.db")
    project_id = hashlib.sha1(
        os.path.abspath(".").encode("utf-8")
    ).hexdigest()[:12]
    conn = db.connect(db_path)
    db.init_db(conn, "project")
    return conn, project_id


def format_bucket_table(buckets: list[sqlite3.Row]) -> str:
    """Format bucket list as an aligned table."""
    if not buckets:
        return ""

    # Collect all values and compute column widths
    rows_data = []
    for b in buckets:
        enabled_str = "●" if b["enabled"] else "○"
        voiced_str = "●" if b["voiced"] else "○"
        rows_data.append({
            "bucket": b["bucket"],
            "forest": b["forest"],
            "enabled": enabled_str,
            "voiced": voiced_str,
            "note": b["note"] or "",
        })

    # Compute column widths
    headers = ["bucket", "forest", "enabled", "voiced", "note"]
    widths = {h: len(h) for h in headers}
    for row in rows_data:
        for h in headers:
            widths[h] = max(widths[h], len(str(row[h])))

    # Format header
    header_line = "  ".join(
        h.ljust(widths[h]) for h in headers
    )
    lines = [header_line]

    # Format rows
    for row in rows_data:
        line = "  ".join(
            str(row[h]).ljust(widths[h]) for h in headers
        )
        lines.append(line)

    return "\n".join(lines)


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize the project database."""
    conn, project_id = open_project()
    db_path = Path("./.cabin/home.db").resolve()
    print(f"initialized: {db_path} (project: {project_id})")

    buckets = db.list_buckets(conn)
    table = format_bucket_table(buckets)
    if table:
        print(table)
    conn.close()
    return 0


def cmd_bucket_list(args: argparse.Namespace) -> int:
    """List all buckets."""
    conn, _ = open_project()
    buckets = db.list_buckets(conn)
    table = format_bucket_table(buckets)
    if table:
        print(table)
    conn.close()
    return 0


def cmd_bucket_disable(args: argparse.Namespace) -> int:
    """Disable a bucket."""
    conn, _ = open_project()
    try:
        db.set_enabled(conn, args.bucket, False)
        print(f"disabled: {args.bucket}")
        return 0
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()


def cmd_bucket_enable(args: argparse.Namespace) -> int:
    """Enable a bucket."""
    conn, _ = open_project()
    try:
        db.set_enabled(conn, args.bucket, True)
        print(f"enabled: {args.bucket}")
        return 0
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()


def cmd_extract(args: argparse.Namespace) -> int:
    """Extract a span into a bucket."""
    conn, project_id = open_project()
    try:
        result = forest.extract(
            conn,
            args.bucket,
            project_id,
            args.source_type,
            args.source_id,
            args.span,
        )
        status = result.get("status", "unknown")
        entry_id = result.get("id", "")
        if entry_id:
            print(f"{status}: {entry_id}")
        else:
            print(f"{status}")
        return 0
    except (forest.LawViolation, ValueError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()


def cmd_collect(args: argparse.Namespace) -> int:
    """Collect hits for a query."""
    conn, project_id = open_project()
    try:
        hits = forest.collect(
            conn,
            args.query,
            forest=args.forest,
            project=project_id,
            buckets=args.bucket if args.bucket else None,
            k=args.k,
        )

        if not hits:
            print("no matches")
            return 0

        for hit in hits:
            distance = hit["distance"]
            bucket = hit["bucket"]
            source_id = hit["source_id"] or ""
            body = hit["body"][:80] if hit["body"] else ""
            print(f"[{distance}]  {bucket}  {source_id}  {body}")

        return 0
    except (forest.LawViolation, ValueError) as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()


def cmd_test_hostile(args: argparse.Namespace) -> int:
    """Run the hostile test suite."""
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests",
        "test_hostile.py",
    )
    result = subprocess.run([sys.executable, test_file])
    return result.returncode


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point."""
    # The bucket table uses ●/○ glyphs; Windows consoles default to cp1252.
    # Reconfigure to UTF-8 so the floor reads correctly on every platform.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

    parser = argparse.ArgumentParser(
        prog="cabin",
        description=".cabin: the floor of contamination-safe memory.",
    )
    subparsers = parser.add_subparsers(dest="command", help="subcommand")

    # cabin init
    init_parser = subparsers.add_parser("init", help="Initialize the project database")
    init_parser.set_defaults(func=cmd_init)

    # cabin bucket
    bucket_parser = subparsers.add_parser("bucket", help="Manage buckets")
    bucket_subparsers = bucket_parser.add_subparsers(dest="bucket_command")

    # cabin bucket list
    bucket_list_parser = bucket_subparsers.add_parser("list", help="List all buckets")
    bucket_list_parser.set_defaults(func=cmd_bucket_list)

    # cabin bucket disable <bucket>
    bucket_disable_parser = bucket_subparsers.add_parser("disable", help="Disable a bucket")
    bucket_disable_parser.add_argument("bucket", help="bucket name")
    bucket_disable_parser.set_defaults(func=cmd_bucket_disable)

    # cabin bucket enable <bucket>
    bucket_enable_parser = bucket_subparsers.add_parser("enable", help="Enable a bucket")
    bucket_enable_parser.add_argument("bucket", help="bucket name")
    bucket_enable_parser.set_defaults(func=cmd_bucket_enable)

    # cabin extract
    extract_parser = subparsers.add_parser("extract", help="Extract a span into a bucket")
    extract_parser.add_argument("bucket", help="target bucket")
    extract_parser.add_argument("source_type", help="source type label")
    extract_parser.add_argument("source_id", help="source identifier")
    extract_parser.add_argument("span", help="verbatim span to extract")
    extract_parser.set_defaults(func=cmd_extract)

    # cabin collect
    collect_parser = subparsers.add_parser("collect", help="Collect hits for a query")
    collect_parser.add_argument("query", help="search query")
    collect_parser.add_argument(
        "--forest",
        choices=["home", "wild"],
        default="home",
        help="forest to search (default: home)",
    )
    collect_parser.add_argument(
        "--k",
        type=int,
        default=10,
        help="number of results (default: 10)",
    )
    collect_parser.add_argument(
        "--bucket",
        action="append",
        help="restrict to bucket (repeatable)",
    )
    collect_parser.set_defaults(func=cmd_collect)

    # cabin test-hostile
    test_hostile_parser = subparsers.add_parser(
        "test-hostile",
        help="Run the hostile test suite",
    )
    test_hostile_parser.set_defaults(func=cmd_test_hostile)

    args = parser.parse_args(argv)

    # Route to the appropriate subcommand
    if hasattr(args, "func"):
        return args.func(args)

    # If no subcommand, print help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
