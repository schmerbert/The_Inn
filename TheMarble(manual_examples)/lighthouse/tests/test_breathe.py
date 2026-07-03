"""The breath must actually catch a held breath — not just decorate departure."""

import datetime as dt
import pathlib
import sqlite3
import tempfile
import time
import unittest

from lighthouse import breathe
from lighthouse.db import connect
from lighthouse.fix import FixRequest, take_fix


def _mem() -> sqlite3.Connection:
    return connect(":memory:")


def _fix(conn, claim="light checked"):
    take_fix(conn, FixRequest(
        claim=claim, evidence_type="command", evidence="lamp on",
        verified_against="tests", author="test-keeper"))


class InhaleTest(unittest.TestCase):
    def test_inhale_returns_door_packet_and_instruction(self):
        conn = _mem()
        _fix(conn)
        result = breathe.inhale(conn)
        self.assertEqual(result["breath"], "in")
        self.assertIn("packet", result)
        self.assertIn("ground", result["packet"])
        self.assertIn("STANDING_ORDERS", result["then"])


class OutTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        for doc in ("ARRIVAL.md", "MANIFEST.md", "CLAUDE.md"):
            (self.root / doc).write_text("clean\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def _seat(self, text="seat\n"):
        (self.root / "HANDOFF.md").write_text(text, encoding="utf-8")

    def test_out_holds_when_log_moved_past_the_seat(self):
        conn = _mem()
        self._seat()
        time.sleep(0.01)
        # fix taken AFTER the handoff was written — the founder's "16 tests"
        future = (dt.datetime.now(dt.timezone.utc)
                  + dt.timedelta(seconds=5)).isoformat()
        conn.execute(
            "INSERT INTO fix (id, claim, evidence_type, evidence, "
            "verified_against, taken_at, author) VALUES "
            "('fix-x', 'new ground', 'command', 'out', 'tests', ?, 'k')",
            (future,))
        result = breathe.out(conn, root=self.root)
        self.assertFalse(result["clear"])
        self.assertTrue(any("predates" in h for h in result["held"]))

    def test_out_holds_when_open_dr_unmentioned(self):
        conn = _mem()
        conn.execute(
            "INSERT INTO chart (id, note, plotted_at, author) VALUES "
            "('dr-x', 'a guess', '2026-01-01T00:00:00+00:00', 'k')")
        self._seat("a seat that never says dee-arr\n")
        result = breathe.out(conn, root=self.root)
        self.assertFalse(result["clear"])
        self.assertTrue(any("DR plot" in h for h in result["held"]))

    def test_out_clear_when_seat_is_fresh_and_honest(self):
        conn = _mem()
        _fix(conn)
        time.sleep(0.01)
        self._seat("fresh seat, no open DR\n")
        result = breathe.out(conn, root=self.root)
        self.assertTrue(result["clear"], result["held"])


if __name__ == "__main__":
    unittest.main()
