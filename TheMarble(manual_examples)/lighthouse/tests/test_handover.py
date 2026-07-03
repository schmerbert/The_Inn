"""The gauges must grow from the LOG — and regrow without scarring."""

import pathlib
import tempfile
import unittest

from lighthouse import handover
from lighthouse.db import connect
from lighthouse.fix import FixRequest, take_fix


class HandoverTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.conn = connect(":memory:")

    def tearDown(self):
        self.tmp.cleanup()

    def _seat(self, text):
        (self.root / "HANDOFF.md").write_text(text, encoding="utf-8")

    def test_first_stamp_inserts_gauges_under_title(self):
        take_fix(self.conn, FixRequest(
            claim="lamp lit", evidence_type="command", evidence="on",
            verified_against="tests", author="k"))
        self._seat("# HANDOFF\n\nnarrative stays human\n")
        self.assertTrue(handover.stamp(self.conn, root=self.root))
        text = (self.root / "HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("active fixes: 1", text)
        self.assertIn("newest ground: lamp lit", text)
        self.assertIn("narrative stays human", text)

    def test_restamp_replaces_block_not_narrative(self):
        self._seat("# HANDOFF\n\nnarrative stays human\n")
        handover.stamp(self.conn, root=self.root)
        take_fix(self.conn, FixRequest(
            claim="second ground", evidence_type="command", evidence="x",
            verified_against="tests", author="k"))
        handover.stamp(self.conn, root=self.root)
        text = (self.root / "HANDOFF.md").read_text(encoding="utf-8")
        self.assertEqual(text.count(handover.BEGIN), 1)
        self.assertIn("active fixes: 1", text)
        self.assertIn("second ground", text)
        self.assertIn("narrative stays human", text)

    def test_open_dr_appears_in_gauges(self):
        self.conn.execute(
            "INSERT INTO chart (id, note, plotted_at, author) VALUES "
            "('dr-x', 'a labeled guess', '2026-01-01T00:00:00+00:00', 'k')")
        self._seat("# HANDOFF\n")
        handover.stamp(self.conn, root=self.root)
        text = (self.root / "HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("open DR dr-x: a labeled guess", text)

    def test_no_seat_no_stamp(self):
        self.assertFalse(handover.stamp(self.conn, root=self.root))


if __name__ == "__main__":
    unittest.main()
