# breath_ledger — append-only inhale receipt trailhead (layer 4).
#
# Stores: logs/breath/*.json receipts
# Refuses: invalid packet receipt shape
# Returns: Path to written receipt
# Test: tests/positive/test_breath_ledger.py

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _logs_dir(root: Path) -> Path:
    return root / "logs" / "breath"


def _stamp() -> str:
    return datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")


def _ids_only(values: list[dict[str, Any]], key: str = "id") -> list[int]:
    ids: list[int] = []
    for row in values:
        value = row.get(key)
        if isinstance(value, int):
            ids.append(value)
    return ids


def receipt_from_packet(
    packet: dict[str, Any],
    timings_ms: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Build a minimal, cite-only inhale receipt from packet slots."""
    ground = packet.get("ground", [])
    if not isinstance(ground, list):
        raise ValueError("packet.ground must be a list")

    return {
        "kind": "inhale_receipt",
        "stamp_utc": _stamp(),
        "slot_ids": {
            "pressure": _ids_only(packet.get("pressure", [])),
            "ground_adoption_records": [
                int(row["adoption_record_id"])
                for row in ground
                if isinstance(row, dict) and isinstance(row.get("adoption_record_id"), int)
            ],
        },
        "slot_counts": {
            "warnings": len(packet.get("warnings", [])) if isinstance(packet.get("warnings", []), list) else 0,
            "ground": len(ground),
            "pressure": len(packet.get("pressure", [])) if isinstance(packet.get("pressure", []), list) else 0,
        },
        "timings_ms": timings_ms or {},
    }


def write_receipt(
    packet: dict[str, Any],
    root: Path,
    timings_ms: dict[str, float] | None = None,
) -> Path:
    """Write one append-only inhale receipt JSON file."""
    logs_dir = _logs_dir(root)
    logs_dir.mkdir(parents=True, exist_ok=True)
    path = logs_dir / f"{_stamp()}-inhale.json"
    path.write_text(json.dumps(receipt_from_packet(packet, timings_ms), indent=2), encoding="utf-8")
    return path
