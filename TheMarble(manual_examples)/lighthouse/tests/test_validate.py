"""The door check — earned twice on day one.

Once by cabin's stale map (file pointers), once by this marble's own
handoff naming a console verb that didn't exist yet (the missing pen).
"""

import tempfile
import unittest
from pathlib import Path

from lighthouse import validate


def _write_docs(root: Path, arrival: str):
    (root / "ARRIVAL.md").write_text(arrival, encoding="utf-8")
    (root / "MANIFEST.md").write_text("# manifest\n", encoding="utf-8")
    (root / "HANDOFF.md").write_text("# handoff\n", encoding="utf-8")
    (root / "CLAUDE.md").write_text("# claude\n", encoding="utf-8")


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_missing_file_pointer_flagged(self):
        _write_docs(self.root, "read `no/such/file.md` first\n")
        problems = validate.check(self.root)
        self.assertTrue(any("no/such/file.md" in p for p in problems))

    def test_missing_pen_flagged(self):
        """A doc naming a verb the console doesn't have must fail the door check."""
        _write_docs(self.root, "then run python -m lighthouse levitate\n")
        problems = validate.check(self.root)
        self.assertTrue(any("levitate" in p and "not on the wall" in p for p in problems))

    def test_real_verbs_pass(self):
        _write_docs(
            self.root,
            "run python -m lighthouse exhale then python -m lighthouse supersede as needed\n",
        )
        self.assertEqual(validate.check(self.root), [])

    def test_live_arrival_docs_are_clean(self):
        """The marble's own docs must pass their own law."""
        self.assertEqual(validate.check(), [])


if __name__ == "__main__":
    unittest.main()
