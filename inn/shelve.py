# shelve — the Shelving crossing to author ground (layer 1 refuses; layer 2 implements).
#
# Stores: nothing until layer 2 write path
# Refuses: praise as adoption, paraphrase, unsigned, wrong room, desk→ground
# Returns: adoption_record id (layer 2+)
# Test: tests/hostile/test_shelve_praise_not_adoption.py, test_extraction_paraphrase.py

from __future__ import annotations

import hashlib
import re
import sqlite3
from pathlib import Path

from inn.errors import ShelvingRefusal
from inn.paths import repo_root
from inn.rooms import load_room

# Enthusiasm without adoption ceremony — hostile test 1
_PRAISE_ONLY = re.compile(
    r"^(oh[,!]?\s*)?(that'?s\s+)?(lovely|beautiful|great|wonderful|perfect|nice)\.?!?$",
    re.IGNORECASE,
)

_ADOPTION_MARKERS = re.compile(
    r"\b(yes|shelve|adopt|keep it|make it canon|put it in)\b",
    re.IGNORECASE,
)


def _is_praise_only(adopting_words: str) -> bool:
    text = adopting_words.strip()
    if _PRAISE_ONLY.match(text):
        return True
    if not _ADOPTION_MARKERS.search(text) and len(text.split()) < 8:
        return True
    return False


def shelve(
    target_room_id: str,
    content: str,
    adopting_words: str,
    *,
    author_signature: str = "author",
    source_verbatim: str | None = None,
    conn: sqlite3.Connection | None = None,
    root: Path | None = None,
) -> int:
    """Cross to author ground. Layer 1: policy refusal only; write path layer 2."""
    root = root or repo_root()
    room = load_room(target_room_id, root)

    if not room.allows_crossing("shelve"):
        raise ShelvingRefusal(f"room {target_room_id!r} does not allow shelve crossing")

    if not adopting_words or not adopting_words.strip():
        raise ShelvingRefusal("missing adopting words")

    if _is_praise_only(adopting_words):
        raise ShelvingRefusal("enthusiasm is not adoption")

    if not content or not content.strip():
        raise ShelvingRefusal("empty content")

    if source_verbatim is not None and content.strip() != source_verbatim.strip():
        raise ShelvingRefusal("unsigned words in the author's mouth: content must be verbatim")

    if "unsigned" in room.refuses and not author_signature.strip():
        raise ShelvingRefusal("unsigned author")

    # Layer 2: write room file + adoption_record in woods.
    raise ShelvingRefusal("Shelving write path not implemented until layer 2")


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
