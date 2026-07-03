"""hound_server.py — Lightweight MCP server for the hound (bounded Haiku observer).

Two tools only: read_file and grep. No vector layer, no heavy imports.
Cold-start: ~0.1s vs 7-9s for the full .cabin server.

Used exclusively by _spawn_hound / forage_hound via:
  --mcp-config .cabin/hound_mcp.json --strict-mcp-config
The hound never sees the main server and its sentence_transformers weight.

Both tools are confined to CABIN_ROOT (set by the MCP config env). Paths
outside the project root are rejected before any filesystem access.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import fastmcp

mcp = fastmcp.FastMCP("hound")

_ROOT = Path(os.environ.get("CABIN_ROOT", ".")).resolve()


def _safe(path: str) -> Path | None:
    """Resolve path and return it only if it lives under _ROOT."""
    try:
        resolved = Path(path).resolve()
        resolved.relative_to(_ROOT)
        return resolved
    except (ValueError, OSError):
        return None


@mcp.tool(description="Read a file within the project root.")
def read_file(path: str) -> str:
    p = _safe(path)
    if p is None:
        return f"access denied: {path!r} is outside project root"
    if not p.exists():
        return f"file not found: {path}"
    try:
        return p.read_text(encoding="utf-8")
    except Exception as exc:
        return f"error reading {path}: {exc}"


@mcp.tool(description=(
    "Search file contents for a regex pattern within the project root. "
    "path may be a file or directory (searches *.py recursively). "
    "Returns matching lines with file:lineno prefix."
))
def grep(pattern: str, path: str = ".", max_results: int = 50) -> list[str]:
    try:
        rx = re.compile(pattern)
    except re.error as exc:
        return [f"invalid pattern: {exc}"]
    p = _safe(path)
    if p is None:
        return [f"access denied: {path!r} is outside project root"]
    files = [p] if p.is_file() else list(p.rglob("*.py"))
    matches: list[str] = []
    for f in files:
        try:
            for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                if rx.search(line):
                    matches.append(f"{f}:{i}: {line}")
                    if len(matches) >= max_results:
                        return matches
        except Exception:
            continue
    return matches


if __name__ == "__main__":
    mcp.run()
