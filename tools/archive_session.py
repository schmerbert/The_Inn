"""Archive a session transcript as a clean 1:1 conversation log.

Supports:
  - Claude Code / Fable .jsonl (type + message.role)
  - Cursor agent .jsonl (top-level role + message.content)

Extraction-only: the source .jsonl is never modified. Output is markdown
with alternating user / assistant messages. Tool calls, tool results,
thinking blocks, system reminders, sidechains, and meta lines are dropped.

Usage:
    python archive_session.py <session.jsonl> [output.md] [--note "…"]

If output is omitted, writes to ../logs/<jsonl-stem>.md.
Archives the source jsonl to ../logs/.source/ (gitignored).
Runs sanitize_logs on the published copy.

Optional --note becomes a subtitle line under the source header (e.g. pass 2).
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
SOURCE = LOGS / ".source"

REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)
CAVEAT = re.compile(r"<local-command-caveat>.*?</local-command-caveat>", re.DOTALL)
COMMAND_TAGS = re.compile(
    r"<command-(?:name|message|args)>.*?</command-(?:name|message|args)>", re.DOTALL
)
STDOUT_TAG = re.compile(r"<local-command-stdout>.*?</local-command-stdout>", re.DOTALL)
TIMESTAMP = re.compile(r"<timestamp>.*?</timestamp>\s*", re.DOTALL)
USER_QUERY = re.compile(r"<user_query>\s*(.*?)\s*</user_query>", re.DOTALL)
THINKING = re.compile(r"<think(?:ing)?>.*?</think(?:ing)?>", re.DOTALL)
REDACTED_TRAIL = re.compile(r"\n*\[REDACTED\]\s*$")


def clean(text: str) -> str:
    text = REMINDER.sub("", text)
    text = CAVEAT.sub("", text)
    text = COMMAND_TAGS.sub("", text)
    text = STDOUT_TAG.sub("", text)
    text = THINKING.sub("", text)
    text = TIMESTAMP.sub("", text)
    m = USER_QUERY.search(text)
    if m:
        text = m.group(1)
    text = REDACTED_TRAIL.sub("", text)
    return text.strip()


def text_of_claude(message: dict) -> str:
    content = message.get("content", "")
    if isinstance(content, str):
        return clean(content)
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return clean("\n\n".join(parts))


def text_of_cursor(message: dict) -> str:
    content = message.get("content", "")
    if isinstance(content, str):
        return clean(content)
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return clean("\n\n".join(parts))


def drop_redacted_only(text: str) -> str:
    """Remove paragraphs that are only harness redaction markers."""
    if not text:
        return ""
    parts = [p.strip() for p in text.split("\n\n")]
    kept = [p for p in parts if p and p != "[REDACTED]"]
    out = "\n\n".join(kept)
    return REDACTED_TRAIL.sub("", out).strip()


def detect_format(sample: dict) -> str:
    if sample.get("role") in ("user", "assistant") and "message" in sample:
        return "cursor"
    if sample.get("type") in ("user", "assistant"):
        return "claude"
    return "unknown"


def load_records(jsonl_path: Path) -> list[dict]:
    records = []
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def extract_claude(records: list[dict]):
    for rec in records:
        if rec.get("isSidechain") or rec.get("isMeta"):
            continue
        if rec.get("type") not in ("user", "assistant"):
            continue
        msg = rec.get("message") or {}
        role = msg.get("role")
        if role not in ("user", "assistant"):
            continue
        content = msg.get("content")
        if isinstance(content, list) and content and all(
            isinstance(b, dict) and b.get("type") in ("tool_result", "tool_use")
            for b in content
        ):
            continue
        text = drop_redacted_only(text_of_claude(msg))
        if not text:
            continue
        yield role, text, rec.get("timestamp", "")


def extract_cursor(records: list[dict]):
    for rec in records:
        if rec.get("type") == "turn_ended":
            continue
        role = rec.get("role")
        if role not in ("user", "assistant"):
            continue
        msg = rec.get("message") or {}
        content = msg.get("content")
        if isinstance(content, list) and content and all(
            isinstance(b, dict) and b.get("type") == "tool_use"
            for b in content
        ):
            continue
        text = drop_redacted_only(text_of_cursor(msg))
        if not text:
            continue
        yield role, text, rec.get("timestamp", "")


def merge_runs(turns):
    merged = []
    for role, text, ts in turns:
        if merged and merged[-1][0] == role:
            prev = merged[-1][1]
            merged[-1] = (role, f"{prev}\n\n{text}".strip(), merged[-1][2] or ts)
        else:
            merged.append((role, text, ts))
    return merged


def date_from_turns(turns, records, fmt: str) -> str:
    for _, _, ts in turns:
        if ts and len(ts) >= 10:
            return ts[:10]
    if fmt == "cursor":
        for rec in records:
            if rec.get("role") != "user":
                continue
            msg = rec.get("message") or {}
            text = text_of_cursor(msg)
            m = re.search(
                r"<timestamp>\w+,\s+(\w+\s+\d{1,2},\s+\d{4})",
                msg.get("content", "")
                if isinstance(msg.get("content"), str)
                else json.dumps(msg.get("content", "")),
            )
            if m:
                from datetime import datetime

                raw_date = m.group(1)
                for fmt in ("%B %d, %Y", "%b %d, %Y"):
                    try:
                        return datetime.strptime(raw_date, fmt).strftime("%Y-%m-%d")
                    except ValueError:
                        continue
    return "unknown-date"


def archive_source(jsonl_path: Path) -> Path:
    SOURCE.mkdir(parents=True, exist_ok=True)
    dest = SOURCE / jsonl_path.name
    if not dest.exists():
        shutil.copy2(jsonl_path, dest)
    return dest


def sanitize_file(md_path: Path) -> None:
    from sanitize_logs import sanitize

    original = md_path.read_text(encoding="utf-8")
    clean_text = sanitize(original)
    if clean_text != original:
        backup = SOURCE / md_path.relative_to(LOGS)
        backup.parent.mkdir(parents=True, exist_ok=True)
        if not backup.exists():
            shutil.copy2(md_path, backup)
        md_path.write_text(clean_text, encoding="utf-8")


def main() -> int:
    raw = sys.argv[1:]
    note = ""
    if "--note" in raw:
        i = raw.index("--note")
        if i + 1 < len(raw):
            note = raw[i + 1].strip()
        raw = raw[:i] + raw[i + 2 :]

    if not raw:
        sys.exit(__doc__)

    src = Path(raw[0])
    if len(raw) > 1:
        out = Path(raw[1])
    else:
        out = LOGS / f"{src.stem}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    records = load_records(src)
    if not records:
        sys.exit(f"No records in {src}")

    fmt = "unknown"
    for rec in records:
        fmt = detect_format(rec)
        if fmt != "unknown":
            break

    if fmt == "cursor":
        turns = merge_runs(list(extract_cursor(records)))
        source_label = "Cursor transcript; verbatim extraction"
    elif fmt == "claude":
        turns = merge_runs(list(extract_claude(records)))
        source_label = "Claude Code transcript; verbatim extraction"
    else:
        sys.exit(f"Unrecognized jsonl format in {src}")

    if not turns:
        sys.exit(f"No conversation turns found in {src}")

    archive_source(src)
    session_date = date_from_turns(turns, records, fmt)

    lines = [
        f"# Session log — {session_date}",
        "",
        f"Source: `{src.name}` ({source_label}; tool calls and system",
        "plumbing omitted; user and assistant words untouched).",
    ]
    if note:
        lines.append("")
        lines.append(note)
    lines.extend(["", "---", ""])

    for role, text, _ in turns:
        label = "**User:**" if role == "user" else "**Assistant:**"
        lines.extend([label, "", text, "", "---", ""])

    out.write_text("\n".join(lines), encoding="utf-8")
    sanitize_file(out)
    print(f"{fmt}: {len(turns)} turns -> {out.relative_to(ROOT)}")
    print(f"source archived -> {SOURCE / src.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
