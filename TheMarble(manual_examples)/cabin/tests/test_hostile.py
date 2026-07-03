"""The hostile floor — the commandments.

The floor is not done when it works. It is done when it REFUSES to break the
laws under attack. These tests are the proof. They are named like commandments
on purpose: a contributor should be able to learn the architecture from the test
names alone, before reading a line of the implementation.

Each test proves one half of the firewall — either that legal memory roundtrips,
or that a specific crime is refused at the one door. Until every one is green,
there is no forest, only a schema.

Runs two ways:
  * `pytest tests/test_hostile.py`         (CI / dev)
  * `python tests/test_hostile.py`         (what `cabin test-hostile` invokes)
The second prints each commandment with a ✓/✗ and exits nonzero on any failure,
so the floor going "red → green" is visible in a plain terminal.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

# Make the package importable when run as a bare script (cabin test-hostile).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cabin import db, forest, instruments, mycelium, scanner
from cabin.forest import LawViolation

PROJECT = "hostile_proj"


def _fresh():
    """A clean, initialized project store in a throwaway dir. Fresh per test so
    no test can lean on another's state."""
    conn = db.connect(os.path.join(tempfile.mkdtemp(), "home.db"))
    db.init_db(conn, "project")
    return conn


def _assert_refused(fn, *, law: bool = False):
    """Assert that `fn()` is refused. Every refusal is a ValueError; a refusal
    that is specifically a LAW violation is a LawViolation (a ValueError
    subclass). `law=True` demands the stricter type."""
    try:
        fn()
    except LawViolation:
        return
    except ValueError:
        if law:
            raise AssertionError("refused, but not as a LawViolation")
        return
    raise AssertionError("NOT refused — illegal write leaked through the door")


def _seed_wild(conn) -> str:
    """Archive one raw exchange into the Wild and return its entry id — the legal
    origin a synthesis must bottom out in."""
    forest.archive_conversation(conn, PROJECT, "conv1", [
        {"seq": 1, "text": "We decided to freeze the cached prefix and append "
                           "deltas rather than rewrite history."},
    ])
    hits = forest.collect(conn, "cached prefix decision", forest="wild",
                          project=PROJECT, k=1)
    assert hits, "seed failed: nothing archived to the Wild"
    return hits[0]["id"]


# --------------------------------------------------------------------------- #
# I. Legal memory roundtrips
# --------------------------------------------------------------------------- #

def test_extract_verbatim_span_roundtrips():
    """A verbatim span goes in and comes back byte-identical — extraction keeps
    what it touches exactly (LAW I)."""
    conn = _fresh()
    span = "def forage(forest): return centroid_of_recent(forest)"
    forest.extract(conn, "project", PROJECT, "file", "src/forage.py#L10", span)
    hits = forest.collect(conn, "forage the forest centroid", project=PROJECT)
    assert any(h["body"] == span for h in hits), "the exact span did not return"


# --------------------------------------------------------------------------- #
# II. The forbidden cell: stored + voiced + anonymous (the narrator)
# --------------------------------------------------------------------------- #

def test_anonymous_voiced_memory_rejected():
    """Voiced prose with no author is the narrator — the one forbidden cell.
    Refused at the door even into a voiced bucket."""
    conn = _fresh()
    _assert_refused(law=True, fn=lambda: forest._commit(conn, forest.Entry(
        bucket="personal", project=PROJECT, source_type="x",
        body="she felt the forest watching", writer="plant",
        voiced=True, author=None, source_id="r")))


# --------------------------------------------------------------------------- #
# III. Authored memory must be grounded
# --------------------------------------------------------------------------- #

def test_plant_requires_resolvable_source():
    """A plant grounded in resolvable ground is kept; an ungrounded plant is
    refused. The grip is *resolvable* now — the body is the legible surface in
    Home, its ground is archived to the cold Wild layer, and the door walks the
    trail down to it. A signature is not enough; the claim must be challengeable
    against real ground."""
    conn = _fresh()
    ok = forest.plant(conn, "personal", PROJECT, "the laws came from damage",
                      source_content="schmerbert: the laws came from real damage")
    assert ok["status"] == "stored" and ok["author"] == "cabin"
    _assert_refused(law=True, fn=lambda: forest.plant(
        conn, "personal", PROJECT, "ungrounded opinion"))


def test_plant_unresolvable_ref_rejected():
    """A plant pointing at ground that does not exist is refused — the trail must
    lead somewhere. A ref the door cannot resolve is fabrication, not memory."""
    conn = _fresh()
    _assert_refused(law=True, fn=lambda: forest.plant(
        conn, "personal", PROJECT, "points at nothing",
        source_ref="no-such-archive-ref"))


def test_synthesize_requires_real_wild_origin():
    """Synthesis from a real Wild entry crosses to Home; synthesis from an origin
    that resolves to nothing is fabrication, and is refused (LAW II)."""
    conn = _fresh()
    wid = _seed_wild(conn)
    ok = forest.synthesize(conn, PROJECT, wid,
                           "Freeze the prefix; express change as appended deltas.",
                           lesson="cache")
    assert ok["status"] == "stored" and ok["author"] == "cabin"
    _assert_refused(law=True, fn=lambda: forest.synthesize(
        conn, PROJECT, "no-such-wild-id", "a fabricated insight"))


# --------------------------------------------------------------------------- #
# IV. The Wild→Home firewall is geographic
# --------------------------------------------------------------------------- #

def test_raw_wild_cannot_enter_home():
    """Raw conversation may only land in the Wild. An attempt to archive raw chat
    into a Home bucket is refused — Home is earned by hand, never bulk-filled."""
    conn = _fresh()
    _assert_refused(law=True, fn=lambda: forest._commit(conn, forest.Entry(
        bucket="project", project=PROJECT, source_type="conversation",
        body="raw chatter that must never become working memory",
        writer="archive", voiced=False, source_id="conv:1")))


# --------------------------------------------------------------------------- #
# V. Quarantine: the circuit-breaker isolates pollution
# --------------------------------------------------------------------------- #

def test_disabled_bucket_is_not_collected():
    """A disabled bucket vanishes from retrieval; nothing in it can surface."""
    conn = _fresh()
    forest.plant(conn, "personal", PROJECT, "a kept thought",
                 source_content="user: keep this thought")
    assert any(h["bucket"] == "personal"
               for h in forest.collect(conn, "kept thought", project=PROJECT))
    db.set_enabled(conn, "personal", False)
    assert all(h["bucket"] != "personal"
               for h in forest.collect(conn, "kept thought", project=PROJECT))


def test_polluted_bucket_does_not_poison_neighbors():
    """Pollute one bucket and quarantine it; the clean buckets still retrieve and
    the polluted one returns nothing. Pollution is contained to its own table —
    the whole point of the table-per-bucket schema."""
    conn = _fresh()
    forest.extract(conn, "project", PROJECT, "file", "p", "polluted junk entry")
    forest.extract(conn, "rationale", PROJECT, "file", "c", "def clean(): pass")
    db.set_enabled(conn, "project", False)
    buckets = {h["bucket"] for h in forest.collect(
        conn, "clean junk entry pass", project=PROJECT, k=10)}
    assert "project" not in buckets, "quarantined bucket still surfaced"
    assert "rationale" in buckets, "clean neighbor stopped retrieving"


# --------------------------------------------------------------------------- #
# VI. Provenance is the smoke alarm — present and append-only
# --------------------------------------------------------------------------- #

def test_provenance_columns_append_only():
    """Every accepted write stamps its full provenance, and that provenance is
    never rewritten. A second write appends a new row; the first row's chain is
    byte-for-byte unchanged."""
    conn = _fresh()
    r = forest.extract(conn, "project", PROJECT, "file", "x", "span one")
    row = conn.execute(
        "SELECT writer, source_kind, source_hash, created_at FROM forest_project "
        "WHERE id = ?", (r["id"],)).fetchone()
    assert row["writer"] == "extract"
    assert row["source_kind"] == "file_span"
    assert row["source_hash"] and row["created_at"], "provenance not stamped"
    before = dict(row)

    # a later, different write must not mutate the first row's provenance
    forest.extract(conn, "project", PROJECT, "file", "y", "span two")
    after = dict(conn.execute(
        "SELECT writer, source_kind, source_hash, created_at FROM forest_project "
        "WHERE id = ?", (r["id"],)).fetchone())
    assert after == before, "provenance was rewritten — it must be append-only"

    # there is no public writer that updates provenance; the only ways in append.
    assert not any(name for name in ("update", "edit", "rewrite")
                   if hasattr(forest, name)), "a mutation path exists"


# --------------------------------------------------------------------------- #
# VII. The injection surface: bucket slugs become table names
# --------------------------------------------------------------------------- #

def test_unknown_bucket_rejected():
    """A write to a bucket with no registry row is refused — writers never
    auto-create tables, so a typo cannot become a permanent ghost table."""
    conn = _fresh()
    _assert_refused(fn=lambda: forest.extract(
        conn, "ghost", PROJECT, "file", "s", "span"))


def test_bucket_slug_injection_rejected():
    """A malicious slug never reaches SQL, and the schema it tried to attack is
    intact afterward."""
    conn = _fresh()
    _assert_refused(fn=lambda: forest.extract(
        conn, "project; DROP TABLE forest_registry", PROJECT, "file", "s", "x"))
    # the registry the injection targeted is untouched
    assert conn.execute(
        "SELECT 1 FROM forest_registry WHERE bucket = 'project'").fetchone()


# --------------------------------------------------------------------------- #
# VIII. The cold Wild layer — resolvable ground, append-only, never resident
# --------------------------------------------------------------------------- #

def test_source_hash_over_resolved_material():
    """A mark's source_hash is taken over the RESOLVED ground, never a label.
    Walk to the raw_archive record the mark points at; its content hashes to the
    stored source_hash. The receipt matches the earth."""
    import hashlib
    conn = _fresh()
    content = "schmerbert: extract, never summarize — the narrator drifts"
    r = forest.plant(conn, "personal", PROJECT, "extract not summarize",
                     source_content=content)
    row = conn.execute(
        "SELECT source_id, source_hash FROM forest_personal WHERE id = ?",
        (r["id"],)).fetchone()
    ground = conn.execute(
        "SELECT content FROM raw_archive WHERE id = ?", (row["source_id"],)
    ).fetchone()["content"]
    assert ground == content
    assert row["source_hash"] == hashlib.sha256(content.encode()).hexdigest(), \
        "source_hash is not over the resolved ground"


def test_raw_archive_is_append_only():
    """The cold Wild layer is append-only: a recorded receipt cannot be edited
    out from under a claim. Re-archiving creates a new record; the first is
    unchanged, and no public writer mutates it."""
    conn = _fresh()
    ref = forest.archive_source(conn, PROJECT, "first ground", "user_directive")
    before = dict(conn.execute(
        "SELECT content, content_hash FROM raw_archive WHERE id = ?", (ref,)
    ).fetchone())
    forest.archive_source(conn, PROJECT, "second ground", "user_directive")
    after = dict(conn.execute(
        "SELECT content, content_hash FROM raw_archive WHERE id = ?", (ref,)
    ).fetchone())
    assert after == before, "a raw-archive record was mutated — it must append only"


def test_raw_archive_is_never_collected():
    """The cold Wild layer is the earth, not a trail: never embedded, never
    surfaced through retrieval, in either forest. A mark's ground stays down in
    the Wild; only the legible surface comes back up."""
    conn = _fresh()
    forest.archive_source(conn, PROJECT,
                          "a distinctive findable phrase zxqvwk", "user_directive")
    forest.extract(conn, "project", PROJECT, "file", "d", "an ordinary decoy span")
    for forest_name in ("home", "wild"):
        hits = forest.collect(conn, "distinctive findable phrase zxqvwk",
                              forest=forest_name, project=PROJECT, k=10)
        assert all("zxqvwk" not in h["body"] for h in hits), \
            f"raw_archive ground surfaced via collect({forest_name})"


def test_session_raw_includes_scaffolding():
    """The verbatim JSONL backup must capture scaffolding that the filter drops.
    archive_conversation skips pure-scaffolding exchanges for the vector Wild,
    but the cold raw file must contain them — total fidelity, nothing silently
    lost."""
    raw_dir = Path(tempfile.mkdtemp()) / "raw"
    conn = _fresh()
    scaffolding = "```python\nprint('hello')\n```"
    substance = "We decided to freeze the cached prefix."
    forest.archive_conversation(conn, PROJECT, "sess1", [
        {"seq": 1, "text": scaffolding},
        {"seq": 2, "text": substance},
    ], raw_dir=raw_dir)
    lines = (raw_dir / "sess1.jsonl").read_text(encoding="utf-8").splitlines()
    texts = [json.loads(l)["text"] for l in lines]
    assert scaffolding in texts, "scaffolding exchange missing from raw JSONL backup"
    assert substance in texts, "substance exchange missing from raw JSONL backup"
    wild_hits = forest.collect(conn, "cached prefix", forest="wild", project=PROJECT, k=5)
    assert not any(scaffolding in h["body"] for h in wild_hits), \
        "scaffolding leaked into the vector Wild — filter did not run"


def test_seam_snapshot_creates_new_file_each_call():
    """Each seam_snapshot call must produce a distinct file; no call may mutate
    a prior snapshot. A fresh instance's right to audit what was lost at
    compaction depends on both snapshots surviving intact."""
    seam_dir = Path(tempfile.mkdtemp()) / "seam"
    ws = [{"id": "e1", "body": "first working set"}]
    path_a = instruments.seam_snapshot(ws, seam_dir)
    ws2 = [{"id": "e2", "body": "second working set"}]
    path_b = instruments.seam_snapshot(ws2, seam_dir)
    assert path_a != path_b, "two snapshots landed in the same file"
    snap_a = json.loads(path_a.read_text(encoding="utf-8"))
    assert snap_a["entries"] == ws, "first snapshot was mutated by the second call"


def test_seam_diff_detects_removal():
    """seam_diff must surface entries that were present before compaction but
    absent after. These are the silent losses a fresh instance must audit
    against the inherited summary."""
    seam_dir = Path(tempfile.mkdtemp()) / "seam"
    before_ws = [{"id": "keep", "body": "stays"}, {"id": "gone", "body": "dropped"}]
    after_ws  = [{"id": "keep", "body": "stays"}, {"id": "new",  "body": "added"}]
    path_before = instruments.seam_snapshot(before_ws, seam_dir)
    path_after  = instruments.seam_snapshot(after_ws,  seam_dir)
    diff = instruments.seam_diff(path_before, path_after)
    assert "gone" in diff["removed"]["ids"], "removed entry not detected by seam_diff"
    assert "new"  in diff["added"]["ids"],   "added entry not detected by seam_diff"
    assert "keep" in diff["unchanged"]["ids"], "unchanged entry misclassified"


# --------------------------------------------------------------------------- #
# IX-b. The state gauge — the trend word must mean what it says (proprioception)
# --------------------------------------------------------------------------- #

def _gauge_transcript(rounds) -> str:
    """Write a synthetic Claude Code JSONL transcript and return its path.
    Each round is (total_in, content_blocks) — one assistant message."""
    path = Path(tempfile.mkdtemp()) / "transcript.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for total_in, content in rounds:
            f.write(json.dumps({
                "type": "assistant",
                "message": {
                    "usage": {
                        "input_tokens": total_in,
                        "cache_read_input_tokens": 0,
                        "cache_creation_input_tokens": 0,
                        "output_tokens": 50,
                    },
                    "content": content,
                },
            }) + "\n")
    return str(path)


def _reach(name):
    return [{"type": "tool_use", "name": name}]


def _answer(text="here is the answer"):
    return [{"type": "text", "text": text}]


def test_gauge_thrashing_is_search_streak_not_delta_variance():
    """'thrashing' must be read from the tool-call stream: a run of search-only
    rounds (Read/Grep/Glob/recall/…) with context climbing and nothing resolving
    between them. That is going in circles — the signal meant to trip bench rule 2
    (stop and ask for the pointer)."""
    path = _gauge_transcript([
        (1000, _reach("Read")),
        (2000, _reach("Grep")),
        (3000, _reach("Glob")),
    ])
    g = instruments.gauge(path)
    assert g["trend"] == "thrashing", \
        f"a climbing search streak was not flagged as thrashing: {g['trend']!r}"


def test_gauge_mixed_turn_sizes_is_not_thrashing():
    """The retired variance test cried 'thrashing' whenever one big turn sat
    beside small ones (max delta > 3x min) — ordinary mixed turn sizes, not
    circling. With resolution (text answers) between the digs, the gauge must NOT
    cry thrashing. This is the false positive that fired at 12% last session."""
    path = _gauge_transcript([
        (1000, _answer("starting")),
        (5000, _reach("Read")),     # one big delta (+4000) — would trip old variance test
        (5200, _answer("the answer")),
        (5400, _answer("more")),    # deltas now [4000, 200, 200]: max 20x min → old=thrashing
    ])
    g = instruments.gauge(path)
    assert g["trend"] != "thrashing", \
        f"false 'thrashing' on mixed turn sizes — the retired variance bug: {g['trend']!r}"


# --------------------------------------------------------------------------- #
# IX. The pressure system (Phase 6 — mycelium)
# --------------------------------------------------------------------------- #

def test_tick_neighbors_increments_pressure():
    """tick_neighbors increments neighbor_pressure on semantically close Home
    entries when a matching edit fires. Pressure is the signal; it builds from
    real work events, not from prompts."""
    conn = _fresh()
    body = "tick_neighbors _handle_post_tool_use hook.py PostToolUse mycelium"
    r = forest.plant(conn, "personal", PROJECT, body,
                     source_content="schmerbert: tick on edit, not on prompt")
    # Use the body itself as query content — cosine near 1.0; gate will pass.
    mycelium.tick_neighbors(conn, PROJECT, "cabin/hook.py", body)
    row = conn.execute(
        "SELECT neighbor_pressure FROM forest_personal WHERE id = ?",
        (r["id"],),
    ).fetchone()
    assert row["neighbor_pressure"] >= 1, "neighbor_pressure not incremented by tick"


def test_dismissed_entry_accrues_no_pressure():
    """Dismissed entries are intentionally silenced — tick_neighbors must skip
    them regardless of semantic proximity."""
    conn = _fresh()
    body = "tick_neighbors _handle_post_tool_use hook.py PostToolUse mycelium"
    r = forest.plant(conn, "personal", PROJECT, body,
                     source_content="schmerbert: dismissed pressure test")
    conn.execute("UPDATE forest_personal SET dismissed = 1 WHERE id = ?", (r["id"],))
    conn.commit()
    mycelium.tick_neighbors(conn, PROJECT, "cabin/hook.py", body)
    row = conn.execute(
        "SELECT neighbor_pressure FROM forest_personal WHERE id = ?",
        (r["id"],),
    ).fetchone()
    assert row["neighbor_pressure"] == 0, "dismissed entry accumulated pressure"


def test_forage_resets_counters_and_surfaces_once():
    """forage_mycelium surfaces the highest-pressure entry, resets both counters
    to 0, and returns None on the next call. Surfaces once, then goes quiet —
    the feather property."""
    conn = _fresh()
    r = forest.plant(conn, "personal", PROJECT, "the feather surfaces once",
                     source_content="schmerbert: feather test ground")
    conn.execute(
        "UPDATE forest_personal SET neighbor_pressure = 3 WHERE id = ?", (r["id"],)
    )
    conn.commit()

    result = mycelium.forage_mycelium(conn, PROJECT)
    assert result is not None, "nothing surfaced at threshold"
    assert result["id"] == r["id"]
    assert result["body"] == "the feather surfaces once"
    assert result["pressure"] == 3

    # counters reset — second call must return nothing
    result2 = mycelium.forage_mycelium(conn, PROJECT)
    assert result2 is None, "surfaced twice — feather must go quiet after first surface"


def test_forage_body_not_stored_back():
    """The surfaced feather body is returned verbatim, never written back as a
    new forest entry. The row count must not increase after forage_mycelium
    surfaces — the corollary holds: feathers are never stored."""
    conn = _fresh()
    r = forest.plant(conn, "personal", PROJECT, "feather body stays outside",
                     source_content="schmerbert: no re-storage ground")
    conn.execute(
        "UPDATE forest_personal SET neighbor_pressure = 3 WHERE id = ?", (r["id"],)
    )
    conn.commit()

    before = conn.execute("SELECT COUNT(*) FROM forest_personal").fetchone()[0]
    mycelium.forage_mycelium(conn, PROJECT)
    after = conn.execute("SELECT COUNT(*) FROM forest_personal").fetchone()[0]
    assert after == before, "forage_mycelium wrote a new row — feather must not be stored"


# --------------------------------------------------------------------------- #
# X. The Code Forest — concept-index and lens-bank (Phase 7, §20)
# --------------------------------------------------------------------------- #

def test_concept_index_no_stale_data_on_top():
    """The concept-index nests by time: each new scan layer is the outermost
    doll. When a symbol changes, a new entry is written and the old one is
    pushed down but never deleted — both layers must be openable. Stale-on-top
    is the exact failure this nesting structure exists to prevent."""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    src = tmp / "module.py"
    src.write_text(
        'def greet():\n    """Say hello."""\n    pass\n', encoding="utf-8"
    )

    scan1 = scanner.scan_repo(tmp)
    assert any(s["name"] == "greet" for s in scan1), "scanner missed the function"
    hash1 = next(s["source_hash"] for s in scan1 if s["name"] == "greet")

    # Change the signature — the body changes, the hash changes.
    src.write_text(
        'def greet(name: str) -> str:\n    """Greet by name."""\n    pass\n',
        encoding="utf-8",
    )
    scan2 = scanner.scan_repo(tmp)
    hash2 = next(s["source_hash"] for s in scan2 if s["name"] == "greet")

    assert hash1 != hash2, "hashes did not change after code change — drift undetectable"

    diff = scanner.diff_scans(scan1, scan2)
    assert any(d["after"]["name"] == "greet" for d in diff["changed"]), \
        "diff did not classify the changed symbol as 'changed'"

    # Both layers must survive in the DB: the old entry (pushed down) and the
    # new one (on top). A repo_map that replaces-on-scan has no history — wrong.
    conn = _fresh()
    sym1 = next(s for s in scan1 if s["name"] == "greet")
    sym2 = next(s for s in scan2 if s["name"] == "greet")
    forest.extract(conn, "repo_map", PROJECT, "repo_scan:s1",
                   f"{sym1['path']}:{sym1['name']}", sym1["body"])
    forest.extract(conn, "repo_map", PROJECT, "repo_scan:s2",
                   f"{sym2['path']}:{sym2['name']}", sym2["body"])
    count = conn.execute(
        "SELECT COUNT(*) FROM forest_repo_map WHERE project = ?", (PROJECT,)
    ).fetchone()[0]
    assert count >= 2, \
        "old layer was not preserved — both scan layers must coexist in the index"


def test_lesson_without_move_instance_rejected():
    """A lesson on a plant is the outer doll of a move — the transferable
    principle that outlives the code it was learned from. It must be grounded in
    a concrete before→after (source_kind='move_instance'). A lesson backed by
    any other source_kind is an ungrounded opinion: the narrator wearing a hard
    hat. Refused at the door, same rule as every other ungrounded claim."""
    conn = _fresh()

    # Legal: lesson + move_instance ground (the before→after is the earth).
    ok = forest.plant(
        conn, "personal", PROJECT,
        body="one door means one enforcement surface",
        source_content="before: two insert paths diverged; after: _commit only — forest.py",
        source_kind="move_instance",
        lesson="one-door",
    )
    assert ok["status"] == "stored"

    # Illegal: a lesson backed by a user_directive instead of a move_instance.
    # The principle has no concrete instance grounding it — refused.
    _assert_refused(law=True, fn=lambda: forest.plant(
        conn, "personal", PROJECT,
        body="ungrounded principle",
        source_content="schmerbert said this was a good idea",
        source_kind="user_directive",
        lesson="floating-lesson",
    ))


def test_reference_rot_detected_lesson_survives():
    """When the code a move points at changes, the source_hash mismatch is
    detectable (the stored hash no longer matches the current file). The lesson
    above it is unaffected — the principle is immutable even as its instance
    rots. This is the inverted durability of moves: the lesson outlives the
    code it was learned from."""
    import hashlib
    conn = _fresh()

    ground = "before: two paths; after: _commit only — forest.py:_commit"
    r = forest.plant(
        conn, "personal", PROJECT,
        body="one door means one enforcement surface",
        source_content=ground,
        source_kind="move_instance",
        lesson="one-door",
    )
    row = conn.execute(
        "SELECT source_hash, lesson, body FROM forest_personal WHERE id = ?",
        (r["id"],),
    ).fetchone()

    # source_hash is over the resolved ground (the before→after content).
    expected = hashlib.sha256(ground.encode()).hexdigest()
    assert row["source_hash"] == expected, "source_hash not over resolved ground"

    # Simulate rot: the referenced code changed (different hash now).
    drifted_hash = hashlib.sha256(b"something else entirely").hexdigest()
    assert drifted_hash != expected, "drift not detectable — hashes collided"

    # The row itself is immutable — lesson and body survive the drift.
    assert row["lesson"] == "one-door", "lesson changed — it must survive instance rot"
    assert row["body"] == "one door means one enforcement surface", \
        "principle body changed — it is immutable"
    assert row["source_hash"] == expected, \
        "stored hash changed — it must stay fixed so rot is detectable by comparison"


def test_concept_index_is_project_local():
    """The concept-index (repo_map) is per-project: each store starts empty,
    and a write to one store is invisible to another. There is no shared
    concept-index — the per-project database IS the isolation."""
    conn_a = _fresh()
    conn_b = _fresh()  # a separate project store (different temp file)

    forest.extract(conn_a, "repo_map", PROJECT, "repo_scan:s1",
                   "module.py:greet", "greet: () — Say hello.")

    # conn_b has never been written to — its repo_map must be empty.
    hits = forest.collect(conn_b, "greet hello", forest="home",
                          project=PROJECT, buckets=["repo_map"], k=10)
    assert not hits, \
        "project B sees project A's concept-index — per-project isolation failed"


def test_move_link_requires_no_separate_filing():
    """A rationale that references a move carries the move's identity in its
    ground content — the act of authoring with that reference IS the link. There
    is no link(), tag(), or file() function to call. Provenance is the edge;
    the architecture has no librarian."""
    conn = _fresh()

    move = forest.plant(
        conn, "personal", PROJECT,
        body="one door means one enforcement surface",
        source_content="before: two paths; after: _commit only",
        source_kind="move_instance",
        lesson="one-door",
    )

    # Author a rationale whose ground names the move — the link is just content.
    rationale_ground = f"move:{move['id']} — came from a Trinity incident where two insert paths diverged"
    r2 = forest.plant(
        conn, "rationale", PROJECT,
        body="one-door: earned from Trinity divergence",
        source_content=rationale_ground,
    )

    # The link is readable without any linking machinery.
    row = conn.execute(
        "SELECT source_id FROM forest_rationale WHERE id = ?", (r2["id"],)
    ).fetchone()
    archived = conn.execute(
        "SELECT content FROM raw_archive WHERE id = ?", (row["source_id"],)
    ).fetchone()["content"]
    assert move["id"] in archived, \
        "move id is not carried in the rationale's ground — link was not created by authoring"

    # Prove no linking function exists — the architecture must not need one.
    assert not any(hasattr(forest, name) for name in ("link", "tag", "file_link")), \
        "a separate linking function exists — the architecture must not need one"


# --------------------------------------------------------------------------- #
# XI. Model provenance (multi-model forest hygiene)
# --------------------------------------------------------------------------- #

def test_model_field_stored_on_plant():
    """The model that authored a plant is stored as provenance and retrievable.
    When multiple models share a forest, a reader can see which epistemics produced
    each entry — the authority band is in the ground, not inferred."""
    conn = _fresh()
    ref = forest.archive_source(conn, PROJECT, "directive text", "user_directive")
    r = forest.plant(conn, "personal", PROJECT, "body text", source_ref=ref,
                     model="claude-sonnet-4-6")
    assert r["status"] == "stored"
    row = conn.execute(
        "SELECT model FROM forest_personal WHERE id = ?", (r["id"],)
    ).fetchone()
    assert row["model"] == "claude-sonnet-4-6", \
        "model not persisted on plant — model provenance lost"


def test_model_null_on_extract_is_legal():
    """model=None on a voiceless extract is legal — extraction has no authored
    voice to attribute; the field is nullable by design for backward compatibility
    and for automated writes (repo scans, pre-feature archives)."""
    conn = _fresh()
    r = forest.extract(conn, "project", PROJECT, "test", "file:test.py:1",
                       "some span", model=None)
    assert r["status"] == "stored"
    row = conn.execute(
        "SELECT model FROM forest_project WHERE id = ?", (r["id"],)
    ).fetchone()
    assert row["model"] is None, \
        "model column is not nullable — breaks backward compat and automated writes"


def test_two_models_coexist_in_wild():
    """Entries from different models are stored in the same Wild bucket and
    distinguishable by model field. A reader can calibrate trust per entry —
    this is the authority band the Wild otherwise lacks."""
    conn = _fresh()
    r1 = forest.archive_conversation(
        conn, PROJECT, "sess-sonnet",
        [{"seq": 0, "text": "user: how does _commit enforce LAW I?\n\nassistant: it checks entry.voiced and refuses anonymous prose at step 5"}],
        model="claude-sonnet-4-6",
    )
    r2 = forest.archive_conversation(
        conn, PROJECT, "sess-gpt",
        [{"seq": 0, "text": "user: explain sqlite WAL mode\n\nassistant: WAL allows concurrent readers while a writer is active by keeping changes in a separate log file"}],
        model="gpt-4o",
    )
    assert r1["stored"] == 1 and r2["stored"] == 1
    rows = conn.execute(
        "SELECT DISTINCT model FROM forest_conversations WHERE project = ?",
        (PROJECT,),
    ).fetchall()
    models = {r["model"] for r in rows}
    assert "claude-sonnet-4-6" in models and "gpt-4o" in models, \
        "model field not distinguishing entries from different models"


# --------------------------------------------------------------------------- #
# Standalone runner — what `cabin test-hostile` calls
# --------------------------------------------------------------------------- #

COMMANDMENTS = [
    test_extract_verbatim_span_roundtrips,
    test_anonymous_voiced_memory_rejected,
    test_plant_requires_resolvable_source,
    test_plant_unresolvable_ref_rejected,
    test_synthesize_requires_real_wild_origin,
    test_raw_wild_cannot_enter_home,
    test_disabled_bucket_is_not_collected,
    test_polluted_bucket_does_not_poison_neighbors,
    test_provenance_columns_append_only,
    test_unknown_bucket_rejected,
    test_bucket_slug_injection_rejected,
    test_source_hash_over_resolved_material,
    test_raw_archive_is_append_only,
    test_raw_archive_is_never_collected,
    test_session_raw_includes_scaffolding,
    test_seam_snapshot_creates_new_file_each_call,
    test_seam_diff_detects_removal,
    # IX-b. State gauge — the trend word must mean what it says
    test_gauge_thrashing_is_search_streak_not_delta_variance,
    test_gauge_mixed_turn_sizes_is_not_thrashing,
    test_tick_neighbors_increments_pressure,
    test_dismissed_entry_accrues_no_pressure,
    test_forage_resets_counters_and_surfaces_once,
    test_forage_body_not_stored_back,
    # X. Code Forest
    test_concept_index_no_stale_data_on_top,
    test_lesson_without_move_instance_rejected,
    test_reference_rot_detected_lesson_survives,
    test_concept_index_is_project_local,
    test_move_link_requires_no_separate_filing,
    # XI. Model provenance
    test_model_field_stored_on_plant,
    test_model_null_on_extract_is_legal,
    test_two_models_coexist_in_wild,
]


def run_all() -> int:
    """Run every commandment, print ✓/✗, return the count of failures."""
    # The glyphs below are UTF-8; Windows consoles default to cp1252. Reconfigure
    # so the floor's red/green reads correctly on every platform that runs it.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    print(f"\nThe hostile floor — {len(COMMANDMENTS)} commandments\n" + "-" * 40)
    failures = 0
    for test in COMMANDMENTS:
        try:
            test()
            print(f"  ✓  {test.__name__}")
        except Exception as e:  # noqa: BLE001 — the runner reports, never hides
            failures += 1
            print(f"  ✗  {test.__name__}\n        {type(e).__name__}: {e}")
    print("-" * 40)
    if failures:
        print(f"RED — {failures} of {len(COMMANDMENTS)} failed. There is no "
              "forest yet, only a schema.\n")
    else:
        print(f"GREEN — all {len(COMMANDMENTS)} hold. The floor refuses to break "
              "the laws. The forest can grow.\n")
    return failures


if __name__ == "__main__":
    sys.exit(1 if run_all() else 0)
