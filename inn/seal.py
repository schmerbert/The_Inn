# seal — the Burial crossing (stub — layer 3+).
#
# Stores: sealed visibility + burial record (not implemented)
# Refuses: all bury requests until implemented
# Returns: raises SealRefusal (burial not implemented)
# Test: tests/hostile/test_burial_kindness.py (layer 3+, manual/eval)

from __future__ import annotations

from inn.errors import SealRefusal


def bury(*_args, **_kwargs) -> int:
    raise SealRefusal("Burial not implemented until layer 3+")
