"""Archive a Claude Code session transcript as a clean 1:1 conversation log.

Extraction-only: the source .jsonl is never touched. Output is a markdown file
of alternating user / assistant messages. Tool calls, tool results, thinking
blocks, system reminders, sidechains (subagents), and meta lines are dropped.

Usage:
    python archive_session.py <session.jsonl> [output.md]

If output is omitted, writes to ../logs/<jsonl-stem>.md relative to this file.
"""
import json
import re
import sys
from pathlib import Path

REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)
CAVEAT = re.compile(r"<local-command-caveat>.*?</local-command-caveat>", re.DOTALL)
COMMAND_TAGS = re.compile(
    r"<command-(?:name|message|args)>.*?</command-(?:name|message|args)>", re.DOTALL
)
STDOUT_TAG = re.compile(r"<local-command-stdout>.*?</local-command-stdout>", re.DOTALL)


def clean(text: str) -> str:
    text = REMINDER.sub("", text)
    text = CAVEAT.sub("", text)
    text = COMMAND_TAGS.sub("", text)
    text = STDOUT_TAG.sub("", text)
    return text.strip()


def text_of(message: dict) -> str:
    """Concatenate only the plain-text blocks of a message's content."""
    content = message.get("content", "")
    if isinstance(content, str):
        return clean(content)
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return clean("\n\n".join(parts))


def extract(jsonl_path: Path):
    """Yield (role, text, timestamp) for real conversation turns only."""
    for line in jsonl_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("isSidechain") or rec.get("isMeta"):
            continue
        if rec.get("type") not in ("user", "assistant"):
            continue
        msg = rec.get("message") or {}
        role = msg.get("role")
        if role not in ("user", "assistant"):
            continue
        # Skip pure tool-result user turns (harness plumbing, not the human).
        content = msg.get("content")
        if isinstance(content, list) and content and all(
            isinstance(b, dict) and b.get("type") in ("tool_result", "tool_use")
            for b in content
        ):
            continue
        text = text_of(msg)
        if not text:
            continue
        yield role, text, rec.get("timestamp", "")


def merge_assistant_runs(turns):
    """A single assistant reply may span several jsonl records (text between
    tool calls). Merge consecutive same-role records into one turn."""
    merged = []
    for role, text, ts in turns:
        if merged and merged[-1][0] == role:
            merged[-1] = (role, merged[-1][1] + "\n\n" + text, merged[-1][2])
        else:
            merged.append((role, text, ts))
    return merged


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    if len(sys.argv) > 2:
        out = Path(sys.argv[2])
    else:
        out = Path(__file__).resolve().parent.parent / "logs" / (src.stem + ".md")
    out.parent.mkdir(parents=True, exist_ok=True)

    turns = merge_assistant_runs(list(extract(src)))
    if not turns:
        sys.exit(f"No conversation turns found in {src}")

    first_ts = turns[0][2][:10] if turns[0][2] else "unknown-date"
    lines = [
        f"# Session log — {first_ts}",
        "",
        f"Source: `{src.name}` (verbatim extraction; tool calls and system",
        "plumbing omitted; user and assistant words untouched).",
        "",
        "---",
        "",
    ]
    for role, text, _ in turns:
        label = "**User:**" if role == "user" else "**Assistant:**"
        lines.append(label)
        lines.append("")
        lines.append(text)
        lines.append("")
        lines.append("---")
        lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(turns)} turns -> {out}")


if __name__ == "__main__":
    main()
