"""Staleness — absence of a fresh fix reads as position unknown."""

import pathlib
import unittest
from datetime import datetime, timedelta, timezone

from lighthouse import exhale, staleness
from lighthouse.db import connect
from lighthouse.fix import FixRequest, take_fix


class StalenessTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")

    def tearDown(self):
        self.conn.close()

    def _fix(self, claim="build is green", verified_against="repo @ head"):
        return take_fix(self.conn, FixRequest(
            claim=claim, evidence_type="command", evidence="exit 0",
            verified_against=verified_against, author="fable-5/session-1",
        ))

    def test_old_fix_demotes_to_dr_authority(self):
        fix_id = self._fix()
        demoted = staleness.check(
            self.conn, max_age_days=14,
            now=datetime.now(timezone.utc) + timedelta(days=15),
        )
        self.assertEqual(demoted[0]["id"], fix_id)
        row = self.conn.execute("SELECT status, stale_reason FROM fix WHERE id = ?", (fix_id,)).fetchone()
        self.assertEqual(row["status"], "stale")
        self.assertIn("re-verify", row["stale_reason"])

    def test_stale_fix_exhales_as_warning_not_ground(self):
        self._fix(claim="deps install cleanly")
        staleness.check(self.conn, max_age_days=14,
                        now=datetime.now(timezone.utc) + timedelta(days=30))
        packet = exhale.packet(self.conn, orders_path=pathlib.Path("no-orders-in-tests.md"))
        self.assertEqual(packet["ground"], [])
        self.assertEqual(len(packet["warnings"]), 1)
        self.assertIn("STALE", packet["warnings"][0]["text"])
        self.assertIn("position unknown", packet["silence_note"])

    def test_vanished_anchor_demotes(self):
        fix_id = self._fix(claim="config file present",
                           verified_against="./no-such-anchor-path.txt")
        demoted = staleness.check(self.conn)
        self.assertEqual(demoted[0]["id"], fix_id)
        self.assertIn("no longer exists", demoted[0]["reason"])

    def test_fresh_fix_survives_check(self):
        self._fix(verified_against="repo @ head")
        self.assertEqual(staleness.check(self.conn), [])
        self.assertEqual(
            self.conn.execute("SELECT COUNT(*) FROM fix WHERE status='active'").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
