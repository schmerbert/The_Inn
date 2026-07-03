"""
cabin/filter.py — contamination guard for .cabin's memory pipeline.

Job: strip system-injected scaffolding out of any text before it enters a
memory table or is forwarded to a model.  Nothing enters memory except
verbatim spans or authored, attributed prose (LAW I — Extract, never
summarize).  If scaffolding recirculates through retrieval, the system orients
toward the wrapper instead of the substance.  This file is what prevents that.

THE ONE THING NOT TO DO: split this into two diverging cleaners — one for
memory, one for the API.  A proven prior implementation learned that the hard
way: when shared patterns live in two places they drift, and scaffolding that
the API path strips correctly silently survives into memory (or vice versa).
The fix is ONE module, TWO modes, ONE shared pattern set.  Preserve that.

Public surface:
    FILTER_VERSION   str — stamped into provenance columns
    strip_scaffolding(text, mode="forest") -> str
    is_pure_scaffolding(text) -> bool
"""

import re

# ── Version ───────────────────────────────────────────────────────────────────

FILTER_VERSION: str = "1.0"

# ── Scaffolding patterns (coding context: Claude Code / VSCode) ───────────────
#
# All patterns are compiled once at import time so every call is fast.
# Grouped by category; each group explains WHY these are scaffolding, not
# substance, so a future reader (human or model) can audit the set.

# --- Harness injection tags ---------------------------------------------------
# Claude Code and IDE harnesses inject XML-like blocks that are operational
# metadata.  They are never part of the human's or the assistant's authored
# prose and must never enter memory.

_TAG_SYSTEM_REMINDER = re.compile(
    r'<system-reminder>.*?</system-reminder>',
    re.DOTALL | re.IGNORECASE,
)
_TAG_THINKING = re.compile(
    r'<thinking>.*?</thinking>',
    re.DOTALL | re.IGNORECASE,
)
_TAG_IDE_SELECTION = re.compile(
    r'<ide_selection>.*?</ide_selection>',
    re.DOTALL | re.IGNORECASE,
)
# Generic harness tags: <context>, <document>, <source>, <result>, <output>
# used as injection wrappers.  Unwrap (keep content) in api mode; strip fully
# in forest mode (the content itself is usually scaffolding too — a file dump
# or retrieval result, not authored prose).
_TAG_CONTEXT_WRAP = re.compile(
    r'<(?:context|document|source|output|result)>.*?</(?:context|document|source|output|result)>',
    re.DOTALL | re.IGNORECASE,
)

# Claude Code lifecycle tags — operational metadata injected into the
# conversation context. Each tag type gets its own paired pattern so nested
# tags of different names don't confuse the non-greedy match. A combined
# alternation like <a|b>.*?</a|b> matches <a> against </b> — wrong.
# Each alternative here requires its own matching close tag.
_TAG_CLAUDE_CODE_LIFECYCLE = re.compile(
    r'<local-command-stdout>.*?</local-command-stdout>'
    r'|<local-command-caveat>.*?</local-command-caveat>'
    r'|<local-command-stdin>.*?</local-command-stdin>'
    r'|<command-name>.*?</command-name>'
    r'|<command-message>.*?</command-message>'
    r'|<command-args>.*?</command-args>'
    r'|<task-notification>.*?</task-notification>',
    re.DOTALL | re.IGNORECASE,
)

# --- Tool-use XML/JSON envelopes ----------------------------------------------
# Anthropic tool-use format: <tool_use> / <tool_result> blocks and their JSON
# payloads.  These are protocol, not prose.

_TAG_TOOL_USE = re.compile(
    r'<tool_use>.*?</tool_use>',
    re.DOTALL | re.IGNORECASE,
)
_TAG_TOOL_RESULT = re.compile(
    r'<tool_result>.*?</tool_result>',
    re.DOTALL | re.IGNORECASE,
)
_TAG_FUNCTION_CALLS = re.compile(
    r'<function_calls>.*?</function_calls>',
    re.DOTALL | re.IGNORECASE,
)
_TAG_FUNCTION_RESULTS = re.compile(
    r'<function_results>.*?</function_results>',
    re.DOTALL | re.IGNORECASE,
)
# Single-line JSON tool-result blobs — forest mode: only known result-shape
# keys; api mode: any long single-line JSON (same heuristic as the proven prior
# implementation: tool results are always long, real JSON examples are short or
# multi-line formatted).
_JSON_RESULT_FOREST = re.compile(
    r'^[ \t]*\{"(?:result|output|error|status|ok|saved|content|stdout|stderr|'
    r'exitCode|exit_code|returncode|files|matches|text|data|tool_use_id)[^\n]*$',
    re.MULTILINE,
)
_JSON_RESULT_API = re.compile(
    r'^[ \t]*\{".{50,}$',
    re.MULTILINE,
)

# --- Role headers -------------------------------------------------------------
# Conversation transcripts often include "Human:", "Assistant:", "User:",
# "System:" prefixes.  These are formatting scaffolding, not the words
# themselves.  Strip the prefix; keep any prose that follows on the same line.
# (The prose on the same line is kept by removing only the prefix token.)
_ROLE_HEADER = re.compile(
    r'^[ \t]*(?:Human|Assistant|User|System|AI)\s*:\s*',
    re.MULTILINE | re.IGNORECASE,
)

# --- Injected context blocks --------------------------------------------------
# Harnesses inject "relevant context", file contents, and similar retrieval
# payloads as labeled blocks.  The label patterns below cover the common forms
# used by Claude Code and VSCode extensions.
_INJECTED_CONTEXT_BLOCK = re.compile(
    r'^[ \t]*(?:Relevant context|Related context|Injected context|Context from '
    r'codebase|Retrieved context|Background context)\s*[:\-–—].*?(?=\n\n|\Z)',
    re.IGNORECASE | re.DOTALL,
)
_CONTEXT_BRACKET_LINE = re.compile(
    r'^[ \t]*\[(?:Context|Relevant context|File context|Codebase context|'
    r'Session context|Project context|System context|Memory context|'
    r'Tool result|Tool output)[^\n]*$',
    re.IGNORECASE | re.MULTILINE,
)

# --- File dumps ---------------------------------------------------------------
# Lines that are purely a file path header (e.g. "--- path/to/file.py ---" or
# "# File: src/foo.py") followed by a fenced code block.  The whole dump is
# scaffolding.  We strip the header line; the code fence pattern below strips
# the body in forest mode.
_FILE_DUMP_HEADER = re.compile(
    r'^[ \t]*(?:#+\s*)?(?:File|Path|Source file)\s*[:\-–—]\s*\S[^\n]*$',
    re.MULTILINE | re.IGNORECASE,
)
# Fenced code blocks — stripped in forest mode because they are almost always
# file dumps, terminal pastes, or diff fragments injected by the harness, not
# the human's authored prose.  In api mode they are kept (the model needs to
# see code the user is referencing).
_CODE_FENCE = re.compile(
    r'^[ \t]*```[^\n]*\n.*?^[ \t]*```[ \t]*$',
    re.MULTILINE | re.DOTALL,
)

# --- Code diffs ---------------------------------------------------------------
# Unified-diff format lines: headers and +/-/@ lines that are structural, not
# prose.  Stripped in forest mode; kept in api mode.
_DIFF_HEADER = re.compile(
    r'^(?:---|\+\+\+|diff --git|index [0-9a-f]+\.\.[0-9a-f]+)[^\n]*$',
    re.MULTILINE,
)
_DIFF_HUNK = re.compile(
    r'^@@[^@]*@@[^\n]*$',
    re.MULTILINE,
)

# --- Terminal / command output ------------------------------------------------
# Shell prompt lines and common terminal-output markers.  In forest mode these
# are scaffolding; in api mode they may be relevant context.
_TERMINAL_PROMPT = re.compile(
    r'^[ \t]*(?:\$|>|>>|#|PS [A-Z]:\\[^\n]*>)\s',
    re.MULTILINE,
)
_COMMAND_ECHO = re.compile(
    r'^[ \t]*(?:Running|Executing|Command|Output|Stdout|Stderr|Exit code|'
    r'Return code|Error)\s*[:\-–—][^\n]*$',
    re.MULTILINE | re.IGNORECASE,
)

# --- Whitespace normalisation -------------------------------------------------
# Applied last in every mode.  Trailing whitespace on a line is always
# scaffolding; excess blank lines are always scaffolding.
_TRAILING_SPACE = re.compile(r'[ \t]+\n')
_EXCESS_BLANK   = re.compile(r'\n{3,}')


# ── Shared core: patterns that run in every mode ──────────────────────────────

def _apply_common(text: str) -> str:
    """
    Strip patterns that are unambiguously scaffolding in ALL modes.

    These run before either mode applies its own rules, so there is no risk of
    the same pattern being maintained in two separate lists.  Any pattern that
    belongs here AND in a mode-specific block is a drift waiting to happen —
    put it here instead.
    """
    t = text
    # Harness injection tags — always scaffolding regardless of mode
    t = _TAG_SYSTEM_REMINDER.sub('', t)
    t = _TAG_THINKING.sub('', t)
    t = _TAG_IDE_SELECTION.sub('', t)
    t = _TAG_CLAUDE_CODE_LIFECYCLE.sub('', t)
    # Tool-use protocol envelopes
    t = _TAG_TOOL_USE.sub('', t)
    t = _TAG_TOOL_RESULT.sub('', t)
    t = _TAG_FUNCTION_CALLS.sub('', t)
    t = _TAG_FUNCTION_RESULTS.sub('', t)
    # Role prefixes (strip prefix, keep the prose on the same line)
    t = _ROLE_HEADER.sub('', t)
    # Bracket-form injected-context labels
    t = _CONTEXT_BRACKET_LINE.sub('', t)
    return t


# ── Public entry point ────────────────────────────────────────────────────────

def strip_scaffolding(text: str, mode: str = "forest") -> str:
    """
    Strip system-injected scaffolding from *text*.

    Parameters
    ----------
    text : str
        The raw text to clean.
    mode : {"forest", "api"}
        "forest"  — aggressive.  For text about to enter a memory table.
                    Strips everything that is not the human's or the cabin's
                    authored prose: code fences, diffs, terminal output, file
                    dumps, JSON result blobs, injected context blocks, and all
                    common patterns.
        "api"     — lighter.  For text about to be sent to a model.
                    Strips unambiguous scaffolding (common patterns + long JSON
                    result blobs) but keeps code fences, diffs, and terminal
                    output because the model may need them to respond correctly.

    Returns
    -------
    str
        Cleaned text.  Always deterministic and side-effect free.
    """
    if not text:
        return text

    t = _apply_common(text)

    if mode == "forest":
        # Aggressive — memory must contain only authored prose.
        # Injected context blocks (labeled prose wrappers)
        t = _INJECTED_CONTEXT_BLOCK.sub('', t)
        # Generic harness wrapper tags — strip entirely; their payloads are
        # almost always file dumps or retrieval results, not authored prose.
        t = _TAG_CONTEXT_WRAP.sub('', t)
        # File dump headers
        t = _FILE_DUMP_HEADER.sub('', t)
        # Fenced code blocks (file dumps, terminal pastes)
        t = _CODE_FENCE.sub('', t)
        # Unified diff scaffolding
        t = _DIFF_HEADER.sub('', t)
        t = _DIFF_HUNK.sub('', t)
        # Terminal / command output markers
        t = _TERMINAL_PROMPT.sub('', t)
        t = _COMMAND_ECHO.sub('', t)
        # JSON tool-result blobs (forest: known result-shape keys only, so
        # legitimate JSON in prose that happens to be long isn't caught)
        t = _JSON_RESULT_FOREST.sub('', t)

    elif mode == "api":
        # Surgical — the model needs to see code, diffs, and terminal output;
        # strip only what adds zero signal and pure token cost.
        # Injected context blocks (labeled, not the content itself)
        t = _INJECTED_CONTEXT_BLOCK.sub('', t)
        # JSON result blobs — any long single-line JSON is a tool result; real
        # conversation JSON is short or multi-line formatted.
        t = _JSON_RESULT_API.sub('', t)
        # Generic harness wrappers: unwrap to content (keep the text inside)
        # rather than stripping entirely, because some payloads are the user's
        # actual question context.
        t = _TAG_CONTEXT_WRAP.sub(
            lambda m: re.sub(r'^<[^>]+>', '', re.sub(r'<[^>]+>$', '', m.group(0), flags=re.DOTALL), flags=re.DOTALL).strip(),
            t,
        )

    else:
        raise ValueError(f"strip_scaffolding: unknown mode {mode!r}; expected 'forest' or 'api'")

    # Normalise whitespace — always last, both modes
    t = _TRAILING_SPACE.sub('\n', t)
    t = _EXCESS_BLANK.sub('\n\n', t).strip()
    return t


# ── Archiver helper ───────────────────────────────────────────────────────────

# "Essentially nothing" threshold: after forest-mode stripping, if the
# remaining text has fewer than this many non-whitespace characters the
# exchange is treated as low-signal residue (empty strings, role-header-only
# lines, stray punctuation, whitespace) and the archiver may drop it. 20 chars
# is a deliberately low bar: anything with a real clause of authored prose
# clears it, while bare scaffolding remnants do not. A short human turn is kept
# the moment it carries 20+ characters of substance.
_SUBSTANCE_THRESHOLD: int = 20


def is_pure_scaffolding(text: str) -> bool:
    """
    Return True if *text* is entirely scaffolding with no authored substance.

    Used by the conversation archiver to drop exchanges whose stripped form
    falls below the substance threshold (_SUBSTANCE_THRESHOLD non-whitespace
    characters).  Dropping them prevents low-signal turns from inflating
    retrieval noise.

    The test is run in forest mode — the most aggressive stripping — so a
    False result (substance found) is a conservative lower bound: it means
    something human-authored survived even the strictest filter.
    """
    if not text:
        return True
    stripped = strip_scaffolding(text, mode="forest")
    return len(stripped.replace(' ', '').replace('\n', '').replace('\t', '')) < _SUBSTANCE_THRESHOLD
