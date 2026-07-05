# errors — refusal exceptions; one family per crossing.
#
# Stores: nothing
# Refuses: n/a (these ARE the refusals)
# Returns: n/a
# Test: raised by tests/hostile/* and tests/positive/*
#
#   InnRefusal       — base; compare.py wrong-bucket adoption lookup
#   RoomRefusal      — rooms.py
#   ShelvingRefusal  — shelve.py
#   ForestRefusal    — forest.py
#   SealRefusal      — seal.py
#   BreathRefusal    — breath.py

"""Refusal exceptions — one type per crossing family."""

from __future__ import annotations


class InnRefusal(Exception):
    """Base for all enforced refusals."""


class RoomRefusal(InnRefusal):
    pass


class ShelvingRefusal(InnRefusal):
    pass


class ForestRefusal(InnRefusal):
    pass


class SealRefusal(InnRefusal):
    pass


class BreathRefusal(InnRefusal):
    pass
