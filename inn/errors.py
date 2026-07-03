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
