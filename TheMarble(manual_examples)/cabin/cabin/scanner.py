"""scanner.py — the concept-index builder (§20.4).

Answers the question the audit step always needs: "where does this project
already do X?" It does this by indexing the project's own vocabulary —
function names, signatures, docstrings — so a semantic query like "where does
this project handle dedup?" finds `_nearest_cosine` without the worker needing
to remember it existed.

The scanner is the ONE PLACE raw code is auto-ingested into memory. That
permission is narrow and deliberate. Auto-ingestion is safe here because
`repo_map`:

  - is voiceless (no authored prose may live there; extracted spans only)
  - is per-project and disposable (blanks on project change; auto-rebuilt)
  - carries no authored claims (verbatim name + signature + docstring only)
  - is quarantinable like every other bucket (the circuit-breaker holds)

These four together are what make auto-ingestion legal here and illegal
everywhere else. Relax any one and you have reintroduced the narrator at
scale — auto-ingested model-generated summaries living anonymously in memory.

THE ONE THING NOT TO DO HERE: do not embed raw file contents. Only the
symbol surface (name + signature + docstring) is indexed. Embedding full file
text would bloat the bucket, flood retrieval, and turn the concept-index into
a copy of the repo instead of a navigable map of its vocabulary.

The scanner does NOT write to the forest. It produces the text bodies that
`index_repo()` (server.py) passes to `forest.extract()` — through the one
door, as always.

Public API:
  scan_repo(root)        — walk root's Python files; return [{symbol}, ...]
  diff_scans(prev, curr) — compare two symbol lists by source_hash
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

# Directories that are never part of the project's own vocabulary. Hidden dirs,
# virtual environments, and caches are excluded because scanning them would fill
# the concept-index with stdlib internals and vendored code, making the
# "where does this project do X?" query unanswerable under noise.
_SKIP_DIRS = frozenset({
    ".git", ".cabin", "__pycache__", ".venv", "venv", "env",
    "node_modules", ".tox", "dist", "build", "site-packages",
})


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _fn_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Reconstruct the signature from AST: (args) -> return_type.

    ast.unparse matches what a reader sees in source. The prefix 'async '
    is included so async functions are identifiable at a glance.
    """
    args = ast.unparse(node.args)
    ret = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    return f"{prefix}({args}){ret}"


def _class_signature(node: ast.ClassDef) -> str:
    bases = ", ".join(ast.unparse(b) for b in node.bases)
    return f"({bases})" if bases else "()"


def _docstring(node: ast.AST) -> str:
    """First string literal in the body. ast.get_docstring handles the
    triple-quote forms; returns '' if none."""
    return ast.get_docstring(node) or ""


def _make_body(name: str, signature: str, docstring: str) -> str:
    """The embeddable surface: 'name: signature — first line of docstring'.

    Only the first line of the docstring is used: it is the summary sentence
    that the author wrote for the outside world. Multi-paragraph docstrings
    carry implementation detail that would distort the embedding toward the
    specifics rather than the concept. The name + signature + summary is the
    vocabulary; the rest is the implementation.
    """
    if docstring:
        first_line = docstring.splitlines()[0].strip()
        return f"{name}: {signature} — {first_line}"
    return f"{name}: {signature}"


def _symbols_from_file(path: Path, root: Path) -> list[dict]:
    """Extract module-level functions + classes and their methods from one file.

    Only module-level and class-level nodes are extracted — not nested
    functions. A nested function is an implementation detail; it is not part
    of the project's findable vocabulary (the audit question "where does this
    project do X?" is never answered by a closure buried inside another
    function).

    Returns one dict per symbol:
      name        — "ClassName.method" for methods; bare name otherwise
      path        — relative to root, forward-slash separated
      lineno      — source line (for the cold reference to the code)
      signature   — reconstructed from AST
      docstring   — first string literal in body, or ""
      body        — the embeddable surface (name + signature + docstring)
      source_hash — sha256 of body; the drift detector (mismatch = code moved)
    """
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []  # unparseable file — skip silently, log nothing

    rel = path.relative_to(root).as_posix()
    symbols: list[dict] = []

    def _record(name: str, node: ast.AST, sig: str, doc: str) -> None:
        b = _make_body(name, sig, doc)
        symbols.append({
            "name": name,
            "path": rel,
            "lineno": getattr(node, "lineno", 0),
            "signature": sig,
            "docstring": doc,
            "body": b,
            "source_hash": _sha256(b),
        })

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            _record(node.name, node, _fn_signature(node), _docstring(node))
        elif isinstance(node, ast.ClassDef):
            _record(node.name, node, _class_signature(node), _docstring(node))
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    _record(
                        f"{node.name}.{child.name}", child,
                        _fn_signature(child), _docstring(child),
                    )

    return symbols


def scan_repo(root: Path | str) -> list[dict]:
    """Walk root for Python symbols. Returns one dict per symbol (see
    `_symbols_from_file` for the shape). Skips hidden dirs, caches, and
    dependency stores so only the project's own vocabulary is indexed.

    The result is stable: same file tree → same output → same source_hashes.
    diff_scans uses this stability to detect what changed between sessions.
    """
    root = Path(root).resolve()
    symbols: list[dict] = []
    for py_file in sorted(root.rglob("*.py")):
        rel_parts = py_file.relative_to(root).parts
        if any(part in _SKIP_DIRS for part in rel_parts):
            continue
        symbols.extend(_symbols_from_file(py_file, root))
    return symbols


def diff_scans(prev: list[dict], curr: list[dict]) -> dict:
    """Diff two symbol lists by source_hash.

    The key is 'path:name'; a hash mismatch means the symbol's embeddable
    surface (name, signature, or docstring summary) changed. source_hash is
    the same drift-detection primitive the rest of the floor uses — sha256
    of what was stored, immutable after write, compared at audit time.

    Returns:
      added    — symbols in curr but not in prev (new functions/classes)
      removed  — symbols in prev but not in curr (deleted or renamed)
      changed  — symbols in both but with different source_hash; each entry
                 is {'before': sym, 'after': sym} for the full before→after
      unchanged_count — symbols identical between scans (not listed; just counted)
    """
    prev_by_key = {f"{s['path']}:{s['name']}": s for s in prev}
    curr_by_key = {f"{s['path']}:{s['name']}": s for s in curr}

    added: list[dict] = []
    removed: list[dict] = []
    changed: list[dict] = []
    unchanged = 0

    for key, sym in curr_by_key.items():
        if key not in prev_by_key:
            added.append(sym)
        elif sym["source_hash"] != prev_by_key[key]["source_hash"]:
            changed.append({"before": prev_by_key[key], "after": sym})
        else:
            unchanged += 1

    for key, sym in prev_by_key.items():
        if key not in curr_by_key:
            removed.append(sym)

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "unchanged_count": unchanged,
    }
