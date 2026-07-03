"""panel_server.py — Channel B: the human's direct window into the cabin.

Lightweight Starlette HTTP server, separate port from the MCP server. The VS
Code extension starts this process; the panel webview calls it directly.
Zero tokens — Claude never knows the human is browsing the forest.

Start:  python -m cabin.panel_server [--port 7771] [--root .]

Two doors into the same DB. The MCP server is Claude's door (pull — the model
reaches). This is the human's door (push — the cabin surfaces to you).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

DEFAULT_PORT = 7771


def _root() -> str:
    return os.environ.get("CABIN_ROOT", os.getcwd())


def _open(root: str):
    from . import db
    import hashlib
    db_path = Path(root) / ".cabin" / "home.db"
    conn = db.connect(db_path)
    db.init_db(conn, "project")

    # Use the project_id already stored in the DB — recomputing from the path
    # is unreliable on Windows (case differences in typed vs canonical paths
    # produce different SHA1 hashes). The stored ID is whatever the MCP server
    # used when it wrote the entries; we must match it exactly.
    row = conn.execute(
        "SELECT project FROM forest_personal WHERE project IS NOT NULL LIMIT 1"
    ).fetchone()
    if row:
        project_id = row["project"]
    else:
        project_id = hashlib.sha1(os.path.abspath(root).encode()).hexdigest()[:12]

    return conn, project_id


# --------------------------------------------------------------------------- #
# /state — hearth card: gauge + pulse + seam
# --------------------------------------------------------------------------- #

async def state(request: Request) -> JSONResponse:
    root = _root()
    from . import instruments

    gauge_data: dict = {}
    session_file = Path(root) / ".cabin" / "current_session.json"
    if session_file.exists():
        try:
            session = json.loads(session_file.read_text(encoding="utf-8"))
            tp = session.get("transcript_path", "")
            if tp:
                gauge_data = instruments.gauge(tp)
                gauge_data["session_id"] = session.get("session_id", "")
                gauge_data["model"] = session.get("model", "")
        except Exception as exc:
            gauge_data = {"error": str(exc)}

    # Prefer structured hearth_card.json (written by hook after hound runs).
    # Falls back to latest raw pulse file for sessions before the card wiring.
    hearth_card_path = Path(root) / ".cabin" / "hearth_card.json"
    pulse: dict | None = None
    if hearth_card_path.exists():
        try:
            pulse = json.loads(hearth_card_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    if pulse is None:
        pulse = instruments.latest_pulse(Path(root) / ".cabin" / "pulses")

    seam_entry = None
    seam_dir = Path(root) / ".cabin" / "seam"
    if seam_dir.exists():
        files = sorted(seam_dir.glob("*.json"))
        if files:
            try:
                raw = json.loads(files[-1].read_text(encoding="utf-8"))
                seam_entry = {
                    "ts": raw.get("ts"),
                    "files": [e.get("file", e.get("id", "")) for e in raw.get("entries", [])],
                    "path": str(files[-1]),
                }
            except Exception:
                pass

    return JSONResponse({
        "project": {"name": Path(root).name, "root": root},
        "gauge": gauge_data,
        "pulse": pulse,
        "seam": seam_entry,
    })


# --------------------------------------------------------------------------- #
# /forage — zero-token forest browse
# --------------------------------------------------------------------------- #

async def forage(request: Request) -> JSONResponse:
    body = await request.json()
    query = body.get("query", "").strip()
    k = int(body.get("k", 10))
    buckets_filter = body.get("buckets") or None
    voiced_only = bool(body.get("voiced_only", False))
    include_dismissed = bool(body.get("include_dismissed", False))
    forest_type = body.get("forest", "home")

    if not query:
        return JSONResponse({"hits": [], "error": "empty query"})

    root = _root()
    conn, project = _open(root)

    from . import embed as _embed, db as _db

    # Wild browse — read-only, zero influence, no traversal_count or pressure effects
    if forest_type == "wild":
        from . import forest as _forest
        hits = _forest.collect(conn, query, forest="wild", project=project, k=k)
        return JSONResponse({
            "hits": [
                {
                    "id": h["id"],
                    "bucket": h["bucket"],
                    "forest": "wild",
                    "voiced": False,
                    "distance": round(float(h["distance"]), 4),
                    "body": h["body"],
                    "source_type": h["source_type"],
                    "source_kind": None,
                    "writer": None,
                    "author": h["author"],
                    "model": h.get("model"),
                    "created_at": h["created_at"],
                    "traversed_at": None,
                    "traversal_count": 0,
                    "surface_pressure": 0,
                    "neighbor_pressure": 0,
                    "effective_pressure": 0,
                    "dismissed": False,
                    "lesson": None,
                }
                for h in hits
            ],
            "query": query,
            "errors": {},
        })

    qvec = _embed.embed(query)
    qblob = _embed.serialize(qvec)

    available = _db.enabled_buckets(conn, "home")
    if buckets_filter:
        available = [b for b in available if b in buckets_filter]

    all_hits: list[dict] = []
    bucket_errors: dict[str, str] = {}

    for bucket in available:
        try:
            reg = conn.execute(
                "SELECT voiced FROM forest_registry WHERE bucket = ?", (bucket,)
            ).fetchone()
            is_voiced = bool(reg["voiced"]) if reg else False
            if voiced_only and not is_voiced:
                continue

            content_t = f"forest_{bucket}"
            vec_t = f"vec_{bucket}"
            per_k = k * 4  # overfetch: project + dismissed filter will trim

            rows = conn.execute(
                f"SELECT v.entry_id, v.distance, "
                f"       c.project, c.body, c.source_type, c.source_kind, "
                f"       c.writer, c.author, c.model, c.created_at, c.traversed_at, "
                f"       c.traversal_count, c.surface_pressure, c.neighbor_pressure, "
                f"       c.dismissed, c.lesson "
                f"FROM {vec_t} v JOIN {content_t} c ON c.id = v.entry_id "
                f"WHERE v.embedding MATCH ? AND k = ? "
                f"ORDER BY v.distance",
                (qblob, per_k),
            ).fetchall()

            for row in rows:
                if row["dismissed"] and not include_dismissed:
                    continue
                if row["project"] is not None and row["project"] != project:
                    continue
                eff_pressure = (row["neighbor_pressure"] or 0) + 2 * (row["surface_pressure"] or 0)
                all_hits.append({
                    "id": row["entry_id"],
                    "bucket": bucket,
                    "forest": "home",
                    "voiced": is_voiced,
                    "distance": round(float(row["distance"]), 4),
                    "body": row["body"],
                    "source_type": row["source_type"],
                    "source_kind": row["source_kind"],
                    "writer": row["writer"],
                    "author": row["author"],
                    "model": row["model"],
                    "created_at": row["created_at"],
                    "traversed_at": row["traversed_at"],
                    "traversal_count": row["traversal_count"] or 0,
                    "surface_pressure": row["surface_pressure"] or 0,
                    "neighbor_pressure": row["neighbor_pressure"] or 0,
                    "effective_pressure": eff_pressure,
                    "dismissed": bool(row["dismissed"]),
                    "lesson": row["lesson"],
                })
        except Exception as exc:
            bucket_errors[bucket] = str(exc)

    all_hits.sort(key=lambda h: h.get("distance", 999.0))
    return JSONResponse({"hits": all_hits[:k], "query": query, "errors": bucket_errors})


# --------------------------------------------------------------------------- #
# /buckets — bucket list with entry counts and high-pressure entries
# --------------------------------------------------------------------------- #

async def buckets_view(request: Request) -> JSONResponse:
    root = _root()
    conn, project = _open(root)

    from . import db as _db
    from .mycelium import PRESSURE_THRESHOLD

    result = []
    for row in _db.list_buckets(conn):
        bucket = row["bucket"]
        entry_count = 0
        high_pressure: list[dict] = []
        try:
            ct = f"forest_{bucket}"
            n = conn.execute(
                f"SELECT COUNT(*) AS n FROM {ct} WHERE project = ? OR project IS NULL",
                (project,)
            ).fetchone()
            entry_count = n["n"] if n else 0

            hp = conn.execute(
                f"SELECT id, body, neighbor_pressure, surface_pressure, "
                f"       source_kind, writer, author, model, created_at "
                f"FROM {ct} "
                f"WHERE (neighbor_pressure + 2 * surface_pressure) >= ? "
                f"  AND dismissed = 0 "
                f"  AND (project = ? OR project IS NULL) "
                f"ORDER BY (neighbor_pressure + 2 * surface_pressure) DESC "
                f"LIMIT 5",
                (PRESSURE_THRESHOLD, project),
            ).fetchall()
            high_pressure = [dict(r) for r in hp]
        except Exception:
            pass

        result.append({
            "bucket": bucket,
            "forest": row["forest"],
            "enabled": bool(row["enabled"]),
            "voiced": bool(row["voiced"]),
            "note": row["note"],
            "created_at": row["created_at"],
            "entry_count": entry_count,
            "high_pressure": high_pressure,
        })

    return JSONResponse({"buckets": result})


# --------------------------------------------------------------------------- #
# /notifications — live: pressure neighbors + seam losses
# --------------------------------------------------------------------------- #

async def notifications(request: Request) -> JSONResponse:
    root = _root()
    conn, project = _open(root)

    from . import db as _db, instruments
    from .mycelium import PRESSURE_THRESHOLD

    items: list[dict] = []

    # 1. Pressure neighbors near or at threshold
    for bucket in _db.enabled_buckets(conn, "home"):
        try:
            ct = f"forest_{bucket}"
            rows = conn.execute(
                f"SELECT id, body, neighbor_pressure, surface_pressure, "
                f"       source_kind, writer, author, model, created_at "
                f"FROM {ct} "
                f"WHERE (neighbor_pressure + 2 * surface_pressure) >= ? "
                f"  AND dismissed = 0 "
                f"  AND (project = ? OR project IS NULL) "
                f"ORDER BY (neighbor_pressure + 2 * surface_pressure) DESC "
                f"LIMIT 3",
                (PRESSURE_THRESHOLD, project),
            ).fetchall()
            for row in rows:
                items.append({
                    "type": "pressure",
                    "bucket": bucket,
                    "id": row["id"],
                    "body": row["body"],
                    "effective_pressure": (row["neighbor_pressure"] or 0) + 2 * (row["surface_pressure"] or 0),
                    "neighbor_pressure": row["neighbor_pressure"] or 0,
                    "surface_pressure": row["surface_pressure"] or 0,
                    "source_kind": row["source_kind"],
                    "writer": row["writer"],
                    "author": row["author"],
                    "model": row["model"],
                    "created_at": row["created_at"],
                })
        except Exception:
            pass

    # 2. Seam losses — files that dropped between the two most recent snapshots
    seam_dir = Path(root) / ".cabin" / "seam"
    if seam_dir.exists():
        files = sorted(seam_dir.glob("*.json"))
        if len(files) >= 2:
            try:
                diff = instruments.seam_diff(files[-2], files[-1])
                if diff["removed"]["count"] > 0:
                    items.append({
                        "type": "seam_loss",
                        "removed": diff["removed"]["ids"],
                        "count": diff["removed"]["count"],
                        "before_ts": json.loads(files[-2].read_text())["ts"],
                        "after_ts": json.loads(files[-1].read_text())["ts"],
                    })
            except Exception:
                pass

    return JSONResponse({"notifications": items})


# --------------------------------------------------------------------------- #
# /seam — list + diff
# --------------------------------------------------------------------------- #

async def seam_list(request: Request) -> JSONResponse:
    root = _root()
    seam_dir = Path(root) / ".cabin" / "seam"
    snapshots: list[dict] = []
    if seam_dir.exists():
        for f in sorted(seam_dir.glob("*.json"), reverse=True)[:30]:
            try:
                raw = json.loads(f.read_text(encoding="utf-8"))
                files = [e.get("file", e.get("id", "")) for e in raw.get("entries", [])]
                snapshots.append({
                    "ts": raw.get("ts"),
                    "file_count": len(files),
                    "files": files,
                    "path": str(f),
                })
            except Exception:
                pass
    return JSONResponse({"snapshots": snapshots})


async def seam_diff_view(request: Request) -> JSONResponse:
    root = _root()
    seam_dir = Path(root) / ".cabin" / "seam"
    before = request.query_params.get("before")
    after = request.query_params.get("after")

    if not (before and after):
        files = sorted(seam_dir.glob("*.json")) if seam_dir.exists() else []
        if len(files) < 2:
            return JSONResponse({"error": "need at least two seam snapshots"})
        before, after = str(files[-2]), str(files[-1])

    from . import instruments
    try:
        diff = instruments.seam_diff(before, after)
        return JSONResponse({"diff": diff, "before": before, "after": after})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


# --------------------------------------------------------------------------- #
# /dismiss/:id — set dismissed=1 on an entry
# --------------------------------------------------------------------------- #

async def dismiss(request: Request) -> JSONResponse:
    entry_id = request.path_params["id"]
    bucket = request.query_params.get("bucket", "")
    if not bucket:
        return JSONResponse({"error": "bucket query param required"}, status_code=400)

    root = _root()
    conn, _ = _open(root)

    from . import db as _db
    try:
        _db.validate_slug(bucket)
        ct = f"forest_{bucket}"
        conn.execute(f"UPDATE {ct} SET dismissed = 1 WHERE id = ?", (entry_id,))
        conn.commit()
        return JSONResponse({"ok": True, "id": entry_id, "bucket": bucket})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


# --------------------------------------------------------------------------- #
# /undismiss/:id — set dismissed=0
# --------------------------------------------------------------------------- #

async def undismiss(request: Request) -> JSONResponse:
    entry_id = request.path_params["id"]
    bucket = request.query_params.get("bucket", "")
    if not bucket:
        return JSONResponse({"error": "bucket query param required"}, status_code=400)

    root = _root()
    conn, _ = _open(root)

    from . import db as _db
    try:
        _db.validate_slug(bucket)
        ct = f"forest_{bucket}"
        conn.execute(f"UPDATE {ct} SET dismissed = 0 WHERE id = ?", (entry_id,))
        conn.commit()
        return JSONResponse({"ok": True, "id": entry_id, "bucket": bucket})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


# --------------------------------------------------------------------------- #
# /quarantine/:bucket — set enabled=0
# --------------------------------------------------------------------------- #

async def quarantine(request: Request) -> JSONResponse:
    bucket = request.path_params["bucket"]
    root = _root()
    conn, _ = _open(root)

    from . import db as _db
    try:
        _db.set_enabled(conn, bucket, False)
        return JSONResponse({"ok": True, "bucket": bucket, "enabled": False})
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


# --------------------------------------------------------------------------- #
# /hound — dispatch mid-session fetch
# --------------------------------------------------------------------------- #

async def hound_dispatch(request: Request) -> JSONResponse:
    body = await request.json()
    reason = body.get("reason", "panel dispatch")
    root = _root()

    session_file = Path(root) / ".cabin" / "current_session.json"
    session: dict = {}
    if session_file.exists():
        try:
            session = json.loads(session_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    from .hook import (_spawn_hound, _read_transcript, _build_seam_entries,
                       _assemble_hound_fetch_prompt)
    import hashlib
    conn, project = _open(root)
    session_id = session.get("session_id", "panel")
    tp = session.get("transcript_path", "")
    pairs = _read_transcript(tp) if tp else []
    entries = _build_seam_entries(root, session_id)

    import asyncio, functools
    loop = asyncio.get_event_loop()
    output = await loop.run_in_executor(
        None,
        functools.partial(_spawn_hound, root, project, session_id, pairs, entries),
    )

    if output:
        from . import instruments
        from .hook import _write_hearth_card
        path = instruments.save_pulse(output, session_id, Path(root) / ".cabin" / "pulses")
        _write_hearth_card(root, output, session_id)
        return JSONResponse({"ok": True, "path": str(path), "preview": output[:400]})
    return JSONResponse({"ok": False, "error": "hound produced no output"})


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #

async def switch_root(request: Request) -> JSONResponse:
    body = await request.json()
    new_root = body.get("root", "").strip()
    if not new_root:
        return JSONResponse({"error": "root required"}, status_code=400)
    p = Path(new_root)
    if not p.exists():
        return JSONResponse({"error": f"path does not exist: {new_root}"}, status_code=400)
    os.environ["CABIN_ROOT"] = str(p.resolve())
    return JSONResponse({"ok": True, "root": os.environ["CABIN_ROOT"]})


async def traverse_view(request: Request) -> JSONResponse:
    body = await request.json()
    entry_id = body.get("entry_id", "").strip()
    if not entry_id:
        return JSONResponse({"error": "entry_id required"}, status_code=400)
    root = _root()
    conn, project = _open(root)
    from . import forest as _forest
    result = _forest.traverse(conn, entry_id, project, human=True)
    return JSONResponse(result)


routes = [
    Route("/state",              state),
    Route("/root",               switch_root, methods=["POST"]),
    Route("/forage",             forage,         methods=["POST"]),
    Route("/traverse",           traverse_view,  methods=["POST"]),
    Route("/buckets",            buckets_view),
    Route("/notifications",      notifications),
    Route("/seam",               seam_list),
    Route("/seam/diff",          seam_diff_view),
    Route("/dismiss/{id}",       dismiss,        methods=["POST"]),
    Route("/undismiss/{id}",     undismiss,      methods=["POST"]),
    Route("/quarantine/{bucket}", quarantine,    methods=["POST"]),
    Route("/hound",              hound_dispatch, methods=["POST"]),
]

app = Starlette(routes=routes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def main() -> None:
    parser = argparse.ArgumentParser(description="cabin panel server")
    parser.add_argument("--port", type=int,
                        default=int(os.environ.get("CABIN_PANEL_PORT", DEFAULT_PORT)))
    parser.add_argument("--root", default=os.getcwd())
    args = parser.parse_args()
    os.environ["CABIN_ROOT"] = os.path.abspath(args.root)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
