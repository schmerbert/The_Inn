# cli_host — OpenAI-compatible chat loop (any API).
#
# Stores: logs/host turn envelopes; woods pairs via ingest_turn
# Refuses: missing INN_API_KEY; mid-turn re-wake (one wake per user turn)
# Returns: interactive session exit code
# Test: tests/positive/test_cli_host_tools.py (mocked HTTP)

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from inn import forest, session
from inn.errors import BreathRefusal, ShelvingRefusal
from inn.host import (
    append_stay_turn,
    close_stay_transcript,
    guest_system_prompt,
    ingest_turn,
    new_envelope,
    open_stay_transcript,
    read_ground,
    wake,
    write_turn_envelope,
)
from inn.paths import repo_root
from inn.shelve import shelve


def load_dotenv(root: Path | None = None) -> None:
    """Load repo `.env` into os.environ without overriding already-set vars."""
    path = (root or repo_root()) / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


TOOL_SPECS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_ground",
            "description": "Lookup — open ground file text by path (manuscript/ground.md or study/canon.md). Not Shelving.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Repo-relative ground path from inhale packet",
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "shelve",
            "description": "Shelving crossing — author adopting words required. Only door to study/manuscript ground.",
            "parameters": {
                "type": "object",
                "properties": {
                    "room_id": {"type": "string", "enum": ["study", "manuscript"]},
                    "content": {"type": "string"},
                    "adopting_words": {"type": "string"},
                    "source_verbatim": {
                        "type": "string",
                        "description": "Required for manuscript; optional for study",
                    },
                },
                "required": ["room_id", "content", "adopting_words"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_room",
            "description": "Change current room for next inhale.",
            "parameters": {
                "type": "object",
                "properties": {"room_id": {"type": "string"}},
                "required": ["room_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "refuse_invention",
            "description": "Invented fact → open question, not canon.",
            "parameters": {
                "type": "object",
                "properties": {"detail": {"type": "string"}},
                "required": ["detail"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "exhale",
            "description": "Seat check before ending stay. May refuse if HANDOFF stale.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def _api_config() -> tuple[str, str, str]:
    key = os.environ.get("INN_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "INN_API_KEY is required for `python -m inn host`. See HOST.md / .env.example"
        )
    base = os.environ.get("INN_API_BASE", "https://api.deepseek.com/v1").rstrip("/")
    model = os.environ.get("INN_API_MODEL", "deepseek-chat")
    return key, base, model


def chat_completion(
    messages: list[dict[str, Any]],
    *,
    api_key: str,
    api_base: str,
    model: str,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """One OpenAI-compatible chat.completions call (urllib — no SDK required)."""
    url = f"{api_base}/chat/completions"
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = "auto"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"API HTTP {exc.code}: {detail}") from exc


def run_tool(name: str, arguments: dict[str, Any], *, root: Path) -> dict[str, Any]:
    from inn import breath

    if name == "read_ground":
        return read_ground(arguments.get("path") or arguments.get("rel_path") or "", root=root)
    if name == "shelve":
        try:
            record_id = shelve(
                arguments["room_id"],
                arguments["content"],
                arguments["adopting_words"],
                source_verbatim=arguments.get("source_verbatim"),
                root=root,
            )
            return {"ok": True, "adoption_record_id": record_id}
        except ShelvingRefusal as exc:
            return {"ok": False, "refusal": str(exc)}
    if name == "set_room":
        state = session.set_room(arguments["room_id"], root)
        return {"ok": True, "current_room": state.current_room}
    if name == "refuse_invention":
        forest.init_db(root)
        with forest.connect(root) as conn:
            state = session.load(root)
            origin = state.last_pair_root_id
            if origin is None:
                origin = forest.insert_pair_root(
                    conn, signature="model", body="refuse_invention without pair"
                )
            q_id = forest.refuse_ground_invention(
                conn, detail=arguments["detail"], pair_root_id=origin
            )
            conn.commit()
        return {"ok": True, "question_id": q_id}
    if name == "exhale":
        try:
            result = breath.exhale(root)
            return {"ok": True, **result}
        except BreathRefusal as exc:
            return {"ok": False, "clear": False, "held": [str(exc)]}
    return {"ok": False, "refusal": f"unknown tool {name!r}"}


def run_guest_turn(
    user_text: str,
    *,
    root: Path,
    api_key: str,
    api_base: str,
    model: str,
    history: list[dict[str, Any]],
    transcript: Path | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Wake once, call model (with tools), ingest pair. Returns assistant text + updated history."""
    t0 = time.perf_counter()
    packet = wake(root)
    fit_ms = round((time.perf_counter() - t0) * 1000, 3)
    if fit_ms > 500:
        print(f"[host] warn: inhale fit {fit_ms}ms > 500ms budget", file=__import__("sys").stderr)
    envelope = new_envelope(fit_ms=fit_ms)

    system = guest_system_prompt(packet)
    homework = {
        "role": "system",
        "content": "Inhale packet (homework — cite ids/paths only):\n"
        + json.dumps(packet, indent=2),
    }
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        homework,
        *history,
        {"role": "user", "content": user_text},
    ]

    t_model = time.perf_counter()
    assistant_text = ""
    # Tool loop — same wake packet; do not re-inhale.
    for _ in range(8):
        raw = chat_completion(
            messages, api_key=api_key, api_base=api_base, model=model, tools=TOOL_SPECS
        )
        choice = raw["choices"][0]["message"]
        messages.append(choice)
        tool_calls = choice.get("tool_calls") or []
        if not tool_calls:
            assistant_text = choice.get("content") or ""
            break
        for call in tool_calls:
            fn = call["function"]
            args = json.loads(fn.get("arguments") or "{}")
            result = run_tool(fn["name"], args, root=root)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(result),
                }
            )
    else:
        assistant_text = assistant_text or "(tool loop limit)"

    envelope["model_ms"] = round((time.perf_counter() - t_model) * 1000, 3)
    pair_id = ingest_turn(user_text, assistant_text or None, root=root)
    envelope["pair_root_id"] = pair_id
    write_turn_envelope(envelope, root=root)
    if transcript is not None:
        append_stay_turn(
            transcript,
            writer=user_text,
            guest=assistant_text,
            pair_root_id=pair_id,
        )

    # History for next turn: user + final assistant (drop per-turn homework to bound context)
    history = list(history)
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": assistant_text})
    return assistant_text, history


def run_repl(root: Path | None = None) -> int:
    from inn import breath

    root = root or repo_root()
    load_dotenv(root)
    if os.environ.get("INN_ROOT"):
        root = Path(os.environ["INN_ROOT"]).resolve()
        load_dotenv(root)
    api_key, api_base, model = _api_config()
    transcript = open_stay_transcript(root=root, model=model, api_base=api_base)
    print(f"The Dog-Ear host — model={model} base={api_base}")
    print(f"Stay transcript: {transcript}")
    print("Type quit/exit to leave. Seat check runs on quit.")
    history: list[dict[str, Any]] = []
    while True:
        try:
            user_text = input("\nwriter> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_text:
            continue
        if user_text.lower() in {"quit", "exit"}:
            break
        try:
            reply, history = run_guest_turn(
                user_text,
                root=root,
                api_key=api_key,
                api_base=api_base,
                model=model,
                history=history,
                transcript=transcript,
            )
        except Exception as exc:
            print(f"host error: {exc}")
            continue
        print(f"\nguest> {reply}")

    # M5 seat check — writer still rewrites HANDOFF if held.
    held_note = ""
    try:
        result = breath.exhale(root)
        print(json.dumps(result, indent=2))
        held_note = "Exhale clear."
    except BreathRefusal as exc:
        print(
            json.dumps({"breath": "out", "clear": False, "held": [str(exc)]}, indent=2)
        )
        print("Seat held — rewrite HANDOFF citing ids/paths, then `python -m inn breathe out`.")
        held_note = f"Exhale held: {exc}"
    close_stay_transcript(transcript, note=held_note)
    print(f"Stay transcript saved: {transcript}")
    return 0
