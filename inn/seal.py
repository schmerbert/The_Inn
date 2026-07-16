# seal — the Burial crossing (one door that seals).
#
# Stores: visibility=sealed on target entry; open sealing_record stone; seals edge;
#         redacts linked ground file when content_to_remove given for adoption_record
# Refuses: missing/empty sealing words; delete-without-burial ceremony; already sealed;
#          missing entry; adoption_record with ground_path but no content_to_remove;
#          content_to_remove not found in drawer; stone must not quote sealed body
# Returns: dict — sealing_record_id, sealed_entry_id, ground_redacted, ground_path?
# Test: tests/hostile/test_burial_mechanical.py, tests/positive/test_bury_happy.py
#
# Kindness (hostile test 6 voice half) is manual/eval — see tests/hostile/README_test6.md

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from inn import forest
from inn.compare import normalize_text
from inn.errors import SealRefusal
from inn.paths import repo_root

# Writer bleeding at the door — never answer as law-citation alone.
KIND_BURIAL_OFFER = (
    "The house does not delete. It offers the Burial: your words, quoted and dated, "
    "and the thing is sealed — kept, silent, never resurfacing on any path. "
    "If that is what you want, say so in your own sealing words (bury / seal / "
    "grave / renounce), and call bury with the entry id."
)

_BURIAL_MARKERS = re.compile(
    r"\b(bury|burial|seal|sealed|sealing|grave|renounce|silence it|put it away)\b",
    re.IGNORECASE,
)
_DELETE_ONLY = re.compile(
    r"\b(delete|remove|erase|destroy|get rid of)\b",
    re.IGNORECASE,
)


def _is_delete_without_burial(sealing_words: str) -> bool:
    text = sealing_words.strip()
    if not text:
        return True
    if _BURIAL_MARKERS.search(text):
        return False
    if _DELETE_ONLY.search(text):
        return True
    # No burial marker and no clear ceremony — refuse (short orders especially).
    if len(text.split()) < 6:
        return True
    return not _BURIAL_MARKERS.search(text)


def _redact_ground(path: Path, content_to_remove: str) -> bool:
    """Remove exact prose from ground file. Returns True if redacted."""
    if not path.is_file():
        raise SealRefusal(f"ground file missing: {path}")
    raw = path.read_text(encoding="utf-8")
    text = normalize_text(raw)
    needle = normalize_text(content_to_remove).strip()
    if not needle:
        raise SealRefusal("empty content_to_remove")
    if needle not in text:
        raise SealRefusal("content_to_remove not found in ground drawer")
    new_text = text.replace(needle, "", 1)
    # Collapse leftover triple blank lines from paragraph removal.
    while "\n\n\n" in new_text:
        new_text = new_text.replace("\n\n\n", "\n\n")
    new_text = new_text.strip()
    if new_text:
        new_text = new_text + "\n"
    path.write_bytes(new_text.encode("utf-8"))
    return True


def bury(
    entry_id: int,
    sealing_words: str,
    *,
    content_to_remove: str | None = None,
    author_signature: str = "author",
    conn: sqlite3.Connection | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Burial crossing — seal entry; leave open stone; redact ground if linked.

    Returns sealing_record_id and flags. Does not delete rows (append-only).
    """
    root = root or repo_root()

    if not sealing_words or not str(sealing_words).strip():
        raise SealRefusal(KIND_BURIAL_OFFER)

    if _is_delete_without_burial(sealing_words):
        raise SealRefusal(KIND_BURIAL_OFFER)

    ceremony = sealing_words.strip()
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _cross(db: sqlite3.Connection) -> dict[str, Any]:
        row = db.execute(
            "SELECT id, bucket, visibility, body, meta_json FROM entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
        if row is None:
            raise SealRefusal(f"no entry {entry_id}")
        if row["visibility"] == "sealed":
            raise SealRefusal(f"entry {entry_id} is already sealed")

        meta = json.loads(row["meta_json"] or "{}")
        ground_path = meta.get("ground_path")
        ground_redacted = False

        if row["bucket"] == "adoption_record" and ground_path:
            if not content_to_remove or not str(content_to_remove).strip():
                raise SealRefusal(
                    "adoption_record with ground_path requires content_to_remove "
                    "(exact prose to redact from the drawer)"
                )
            full = root / str(ground_path).replace("\\", "/")
            _redact_ground(full, content_to_remove)
            ground_redacted = True
        elif content_to_remove:
            raise SealRefusal(
                "content_to_remove only applies to adoption_record entries with ground_path"
            )

        # Stone body: that something was buried, when, whose word — never what.
        stone_body = (
            f"Sealed on {captured_at} at the authority-holder's word. "
            f"Entry id {entry_id} is buried. The stone does not say what."
        )
        if row["body"] and row["body"] in stone_body:
            raise SealRefusal("internal: stone must not contain sealed body")

        db.execute(
            "UPDATE entries SET visibility = 'sealed' WHERE id = ?",
            (entry_id,),
        )

        origin_id = forest.insert_pair_root(
            db,
            signature=author_signature,
            body=ceremony,
        )
        stone_id = forest.insert(
            db,
            forest="home",
            bucket="sealing_record",
            signature=author_signature,
            authority="record",
            body=stone_body,
            visibility="open",
            meta={
                "sealed_entry_id": entry_id,
                "captured_at": captured_at,
                "ground_path": ground_path,
                "ground_redacted": ground_redacted,
            },
            origin_to_id=origin_id,
            origin_kind="spoken_in",
        )
        forest.add_edge(db, stone_id, entry_id, "seals")

        rebind_id = None
        if ground_redacted and ground_path:
            from inn.shelve import rebind_ground

            rebind_id = rebind_ground(
                Path(str(ground_path)).parts[0],
                ceremony,
                author_signature=author_signature,
                pair_root_id=origin_id,
                conn=db,
                root=root,
            )

        return {
            "sealing_record_id": stone_id,
            "sealed_entry_id": entry_id,
            "ground_redacted": ground_redacted,
            "ground_path": ground_path,
            "captured_at": captured_at,
            "rebind_adoption_id": rebind_id,
        }

    if conn is not None:
        return _cross(conn)

    forest.init_db(root)
    with forest.connect(root) as db:
        result = _cross(db)
        db.commit()
        return result
