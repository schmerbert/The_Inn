"""Positive paths — the right thing must have somewhere good to go.

A marble that only refuses things becomes brittle.
"""

import pathlib
import unittest

from lighthouse import chart, exhale
from lighthouse.db import connect
from lighthouse.fix import FixRequest, take_fix


class PositiveTests(unittest.TestCase):
    def setUp(self):
        self.conn = connect(":memory:")

    def tearDown(self):
        self.conn.close()

    def test_valid_fix_lands_as_ground(self):
        fix_id = take_fix(self.conn, FixRequest(
            claim="47 tests pass in EXAMPLEmarbles/fall",
            evidence_type="command",
            evidence="python -m unittest discover -s tests -q -> Ran 47 tests, OK",
            verified_against="EXAMPLEmarbles/fall @ 2026-07-01",
            author="fable-5/session-1",
        ))
        row = self.conn.execute("SELECT * FROM fix WHERE id = ?", (fix_id,)).fetchone()
        self.assertEqual(row["status"], "active")
        self.assertEqual(row["author"], "fable-5/session-1")
        outcome = self.conn.execute(
            "SELECT outcome FROM fix_audit ORDER BY seq DESC LIMIT 1"
        ).fetchone()[0]
        self.assertEqual(outcome, "fixed")

    def test_user_words_can_be_fixed(self):
        fix_id = take_fix(self.conn, FixRequest(
            claim="user approved the lighthouse prebuild",
            evidence_type="user-said",
            evidence='"yes. A lighthouse is important." — user, this conversation',
            verified_against="conversation 2026-07-01",
            author="fable-5/session-1",
        ))
        self.assertTrue(fix_id.startswith("fix-"))

    def test_dr_is_cheap_and_labeled(self):
        dr_id = chart.plot(
            self.conn,
            "the cabin panel probably still has the seam-stomp bug",
            author="fable-5/session-1",
            basis="cabin HANDOFF listed it as open; not re-verified",
        )
        packet = exhale.packet(self.conn, orders_path=pathlib.Path("no-orders-in-tests.md"))
        pressure = [p for p in packet["pressure"] if p["id"] == dr_id]
        self.assertEqual(len(pressure), 1)
        self.assertIn("DR", pressure[0]["label"])
        self.assertEqual(packet["ground"], [], "DR must never appear as ground")

    def test_exhale_orders_warnings_first_and_names_empty_ground(self):
        packet = exhale.packet(self.conn, orders_path=pathlib.Path("no-orders-in-tests.md"))
        self.assertIsNotNone(packet["silence_note"])
        self.assertIn("position unknown", packet["silence_note"])
        self.assertEqual(list(packet.keys())[0], "warnings")


if __name__ == "__main__":
    unittest.main()
