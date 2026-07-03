# seal — the Burial crossing (layer 3+ stub).
#
# Stores: sealed visibility + burial record
# Refuses: all requests until layer 3
# Returns: burial record id
# Test: tests/hostile/test_burial_kindness.py (layer 3+, manual)

from __future__ import annotations

from inn.errors import SealRefusal


def bury(*_args, **_kwargs) -> int:
    raise SealRefusal("Burial not implemented until layer 3")
