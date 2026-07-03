"""Shared path resolution."""

from __future__ import annotations

from pathlib import Path

_PKG = Path(__file__).resolve().parent
ROOT = _PKG.parent


def repo_root() -> Path:
    return ROOT
