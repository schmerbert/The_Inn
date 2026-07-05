# paths — repo root resolution for inn package.
#
# Stores: nothing
# Refuses: nothing
# Returns: Path to repository root (parent of inn/)
# Test: indirect — all modules use repo_root()

"""Shared path resolution."""

from __future__ import annotations

from pathlib import Path

_PKG = Path(__file__).resolve().parent
ROOT = _PKG.parent


def repo_root() -> Path:
    return ROOT
