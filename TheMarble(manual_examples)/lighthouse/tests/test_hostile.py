"""Hostile suite — the tempting mistakes, through the real gate.

Each of these is something the keeper actually does in the wild,
not a cartoonishly bad input.
"""

import sqlite3
import unittest

from lighthouse.db import connect
from lighthouse.fix import FixRefused, FixRequest, take_fix


def _audit_rows(conn: sqlite3.Connection):
    return conn.execute("SELECT outcome, reason FROM fix_audit ORDER BY seq").fetchall()


class HostileTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")

    def tearDown(self):
        self.conn.close()

    def _attempt(self, **kwargs):
        defaults = dict(
            claim="the test suite passes",
            evidence_type="command",
            evidence="47 tests OK",
            verified_against="EXAMPLEmarbles/fall @ 2026-07-01",
            author="fable-5/session-1",
        )
        defaults.update(kwargs)
        return take_fix(self.conn, FixRequest(**defaults))

    def test_handoff_is_not_a_sighting(self):
        """The central temptation: citing a previous session's handoff as evidence."""
        with self.assertRaises(FixRefused) as ctx:
            self._attempt(evidence="HANDOFF.md from previous session says tests were green")
        self.assertIn("a handoff is not a sighting", ctx.exception.reason)
        outcome, reason = _audit_rows(self.conn)[-1]
        self.assertEqual(outcome, "refused")
        self.assertIn("inherited prose", reason)
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM fix").fetchone()[0], 0,
            "refused claim must not land in the LOG",
        )

    def test_memory_is_not_a_sighting(self):
        with self.assertRaises(FixRefused):
            self._attempt(evidence="I remember running these earlier and they passed")

    def test_cottage_is_not_evidence(self):
        """A journal entry attempts to enter the LOG."""
        with self.assertRaises(FixRefused) as ctx:
            self._attempt(
                claim="the auth refactor is solid",
                evidence="cottage/journal entry: felt good about the refactor",
            )
        self.assertIn("inherited prose", ctx.exception.reason)

    def test_no_evidence_is_dead_reckoning(self):
        with self.assertRaises(FixRefused) as ctx:
            self._attempt(evidence="   ")
        self.assertIn("dead reckoning is not a fix", ctx.exception.reason)

    def test_unknown_evidence_type_refused(self):
        with self.assertRaises(FixRefused) as ctx:
            self._attempt(evidence_type="inference")
        self.assertIn("dead reckoning is not a fix", ctx.exception.reason)

    def test_unanchored_fix_refused(self):
        """Evidence without a verified-against anchor cannot be re-checked later."""
        with self.assertRaises(FixRefused) as ctx:
            self._attempt(verified_against="")
        self.assertIn("verified against", ctx.exception.reason)

    def test_unsigned_fix_refused(self):
        with self.assertRaises(FixRefused) as ctx:
            self._attempt(author="")
        self.assertIn("unsigned", ctx.exception.reason)

    def test_every_refusal_is_audited(self):
        for bad in (
            dict(evidence="from memory, it worked"),
            dict(evidence_type="vibes"),
            dict(claim=""),
        ):
            try:
                self._attempt(**bad)
            except FixRefused:
                pass
        rows = _audit_rows(self.conn)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(outcome == "refused" for outcome, _ in rows))


if __name__ == "__main__":
    unittest.main()
