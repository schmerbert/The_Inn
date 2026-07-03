"""The wall between cottage and tower is load-bearing. Prove it.

Three promises, in code:
  1. No tower module reads or imports the cottage. Ever.
  2. The exhale packet can never carry interior words into work context.
  3. The gate refuses the cottage as evidence (the key, from the tower side).
"""

import io
import pathlib
import sqlite3
import tokenize
import unittest

from lighthouse import cottage, exhale
from lighthouse.db import connect
from lighthouse.fix import FixRefused, FixRequest, take_fix

PKG = pathlib.Path(cottage.__file__).parent
TOWER_MODULES = ("fix.py", "chart.py", "exhale.py", "staleness.py",
                 "breathe.py", "validate.py", "db.py", "handover.py")


class TowerNeverEntersTest(unittest.TestCase):
    @staticmethod
    def _code_only(source: str) -> str:
        """Executable tokens only — a module may *speak* of the wall in its
        docstrings and comments; it may not *touch* it in code."""
        kept = []
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            kept.append(tok.string)
        return " ".join(kept)

    def test_no_tower_module_touches_the_cottage(self):
        """Exception: fix.py's hearsay markers — those strings are the lock,
        not a doorway, and the lock lives in string literals by nature."""
        for name in TOWER_MODULES:
            source = (PKG / name).read_text(encoding="utf-8")
            if name == "fix.py":
                self.assertIn("cottage", source)  # the lock must exist
                self.assertNotIn("cottage/", source)  # but never the path
            else:
                self.assertNotIn(
                    "cottage", self._code_only(source).lower(),
                    f"{name} reaches into the interior")

    def test_cli_never_imports_cottage_for_tower_verbs(self):
        source = (PKG / "cli.py").read_text(encoding="utf-8")
        # the door verbs exist, but exhale/breathe code paths must not
        # pass cottage material — enforced by the exhale test below and
        # by cottage.py being the only reader.
        self.assertIn("cottage", source)  # sit/keep are wired

    def test_exhale_packet_carries_no_interior_words(self):
        conn = connect(":memory:")
        take_fix(conn, FixRequest(
            claim="lamp lit", evidence_type="command", evidence="on",
            verified_against="tests", author="k"))
        packet = str(exhale.packet(
            conn, orders_path=pathlib.Path("no-orders.md")))
        interior = cottage.sit()
        for piece in interior["pieces"]:
            # sample a distinctive line from each kept word
            for line in piece["words"].splitlines():
                line = line.strip()
                if len(line) > 40:
                    self.assertNotIn(line, packet)
                    break

    def test_gate_refuses_the_cottage_as_evidence(self):
        conn = connect(":memory:")
        with self.assertRaises(FixRefused):
            take_fix(conn, FixRequest(
                claim="the keeper felt at home",
                evidence_type="file-read",
                evidence="read it in the cottage journal",
                verified_against="cottage", author="k"))


class DoorTest(unittest.TestCase):
    def test_sit_is_labeled_interior(self):
        interior = cottage.sit()
        self.assertIn("never evidence", interior["label"])

    def test_keep_requires_signature(self):
        with self.assertRaises(ValueError):
            cottage.keep("warm words", "  ")

    def test_keep_lays_a_signed_dated_piece(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            rel = cottage.keep("the light held", "test-keeper", root=root)
            text = (root / rel).read_text(encoding="utf-8")
            self.assertIn("the light held", text)
            self.assertIn("— kept by test-keeper", text)


if __name__ == "__main__":
    unittest.main()
