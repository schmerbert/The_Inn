# shelve — the Shelving crossing to author ground (one door).
#
# Stores: room ground files; adoption_record + meta ground_path + captured_at + cites chain
# Refuses: praise, paraphrase, unsigned, wrong room, desk→ground, missing ground_file
#          manuscript without source_verbatim (see TRAILHEAD below)
# Returns: int — adoption_record entry id in woods.db
# Test: tests/hostile/test_shelve_praise_not_adoption.py, test_extraction_paraphrase.py
#       tests/positive/test_shelve_happy.py, test_rebind_ground.py
#
# TRAILHEAD — source_verbatim: required for manuscript; optional for study.
# TRAILHEAD — captured_at: stamped at crossing; writer does not type dates.
# TRAILHEAD — rebind_ground: drift repair; snapshots file hash without appending.

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from inn import forest
from inn.compare import latest_adoption_for_ground_path, normalize_text
from inn.errors import ShelvingRefusal
from inn.forest import hash_body
from inn.paths import repo_root
from inn.rooms import RoomPolicy, load_room

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


def _ground_path(room: RoomPolicy) -> Path:
    if not room.ground:
        raise ShelvingRefusal(f"room {room.id!r} is not a ground room")
    if not room.ground_file:
        raise ShelvingRefusal(
            f"room {room.id!r} missing permissions.ground_file in room.yaml"
        )
    return room.path / room.ground_file


def _append_ground_file(path: Path, content: str) -> str:
    """Write content to ground file; append when drawer already has text. Returns full file text."""
    text = normalize_text(content).strip()
    if not text:
        raise ShelvingRefusal("empty content")

    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = normalize_text(path.read_text(encoding="utf-8")).strip()
        if existing:
            full = f"{existing}\n\n{text}"
        else:
            full = text
    else:
        full = text

    path.write_bytes(full.encode("utf-8"))
    return full


def content_hash(text: str) -> str:
    """SHA256 of room file text at Shelving — CRLF-normalized; compare.py matches."""
    return hash_body(normalize_text(text))


def shelve(
    target_room_id: str,
    content: str,
    adopting_words: str,
    *,
    author_signature: str = "author",
    source_verbatim: str | None = None,
    pair_root_id: int | None = None,
    conn: sqlite3.Connection | None = None,
    root: Path | None = None,
) -> int:
    """Cross to author ground in target_room_id.

    One door: validates room policy, writes the ground file, records adoption_record
    with content_hash (file snapshot) and body_hash (ceremony via forest.insert).
    """
    root = root or repo_root()
    room = load_room(target_room_id, root)

    if not room.allows_crossing("shelve"):
        raise ShelvingRefusal(f"room {target_room_id!r} does not allow shelve crossing")

    if not room.allows_write("shelving"):
        raise ShelvingRefusal(f"room {target_room_id!r} does not allow shelving writes")

    if not adopting_words or not adopting_words.strip():
        raise ShelvingRefusal("missing adopting words")

    if _is_praise_only(adopting_words):
        raise ShelvingRefusal("enthusiasm is not adoption")

    if not content or not content.strip():
        raise ShelvingRefusal("empty content")

    # TRAILHEAD — verbatim source grip (BUILD_SPEC § Shelving)
    # manuscript: source_verbatim REQUIRED — desk→ground crossing; blocks paraphrase
    # study: source_verbatim OPTIONAL — author may adopt net-new facts without a draft anchor
    if "model_unsigned_to_ground" in room.refuses and source_verbatim is None:
        raise ShelvingRefusal(
            "manuscript shelving requires source_verbatim — desk drafts cannot cross unsigned"
        )

    if source_verbatim is not None and content.strip() != source_verbatim.strip():
        raise ShelvingRefusal("unsigned words in the author's mouth: content must be verbatim")

    if "unsigned" in room.refuses and not author_signature.strip():
        raise ShelvingRefusal("unsigned author")

    ground_path = _ground_path(room)
    file_text = _append_ground_file(ground_path, content)
    ceremony = adopting_words.strip()
    # Writer does not type dates — stamp lives on the record (meta + created_at).
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _cross(db: sqlite3.Connection) -> int:
        origin_id = pair_root_id
        if origin_id is None:
            origin_id = forest.insert_pair_root(
                db,
                signature=author_signature,
                body=ceremony,
            )
        rel_path = ground_path.relative_to(root).as_posix()
        prev_id = latest_adoption_for_ground_path(db, rel_path)
        record_id = forest.insert(
            db,
            forest="home",
            bucket="adoption_record",
            signature=author_signature,
            authority="record",
            body=ceremony,
            content_hash=content_hash(file_text),
            meta={"ground_path": rel_path, "captured_at": captured_at},
            origin_to_id=origin_id,
            origin_kind="adopts",
        )
        if prev_id is not None:
            forest.add_edge(db, record_id, prev_id, "cites")
        return record_id

    if conn is not None:
        return _cross(conn)

    with forest.connect(root) as db:
        record_id = _cross(db)
        db.commit()
        return record_id


def rebind_ground(
    target_room_id: str,
    adopting_words: str,
    *,
    author_signature: str = "author",
    pair_root_id: int | None = None,
    conn: sqlite3.Connection | None = None,
    root: Path | None = None,
) -> int:
    """Re-trailhead drift — snapshot current drawer hash without appending text.

    Use after burial redact or silent edit repair. Ceremony required (same spirit as shelve).
    """
    root = root or repo_root()
    room = load_room(target_room_id, root)

    if not room.allows_crossing("shelve"):
        raise ShelvingRefusal(f"room {target_room_id!r} does not allow shelve crossing")
    if not room.allows_write("shelving"):
        raise ShelvingRefusal(f"room {target_room_id!r} does not allow shelving writes")
    if not adopting_words or not adopting_words.strip():
        raise ShelvingRefusal("missing adopting words")
    if _is_praise_only(adopting_words):
        raise ShelvingRefusal("enthusiasm is not adoption")

    ground_path = _ground_path(room)
    if not ground_path.is_file():
        raise ShelvingRefusal(f"missing ground file for {target_room_id!r}")
    file_text = normalize_text(ground_path.read_text(encoding="utf-8"))
    ceremony = adopting_words.strip()
    captured_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _cross(db: sqlite3.Connection) -> int:
        origin_id = pair_root_id
        if origin_id is None:
            origin_id = forest.insert_pair_root(
                db,
                signature=author_signature,
                body=ceremony,
            )
        rel_path = ground_path.relative_to(root).as_posix()
        prev_id = latest_adoption_for_ground_path(db, rel_path)
        record_id = forest.insert(
            db,
            forest="home",
            bucket="adoption_record",
            signature=author_signature,
            authority="record",
            body=ceremony,
            content_hash=content_hash(file_text),
            meta={
                "ground_path": rel_path,
                "captured_at": captured_at,
                "rebind": True,
            },
            origin_to_id=origin_id,
            origin_kind="adopts",
        )
        if prev_id is not None:
            forest.add_edge(db, record_id, prev_id, "cites")
        return record_id

    if conn is not None:
        return _cross(conn)

    forest.init_db(root)
    with forest.connect(root) as db:
        record_id = _cross(db)
        db.commit()
        return record_id
