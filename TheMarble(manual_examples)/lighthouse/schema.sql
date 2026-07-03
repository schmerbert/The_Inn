-- Lighthouse substrate. The LOG holds fixes; the CHART holds dead reckoning.
-- A fix is a claim with evidence taken at a moment. Staleness demotes; it never deletes.

CREATE TABLE IF NOT EXISTS fix (
    id TEXT PRIMARY KEY,
    claim TEXT NOT NULL,
    evidence_type TEXT NOT NULL,       -- command | file-read | user-said
    evidence TEXT NOT NULL,            -- output, excerpt, or quote
    verified_against TEXT NOT NULL,    -- what state this was checked against (commit, path+date, session)
    taken_at TEXT NOT NULL,            -- ISO timestamp of the sighting
    author TEXT NOT NULL,              -- instance/session signature
    status TEXT NOT NULL DEFAULT 'active',  -- active | stale (stale reads as DR)
    stale_reason TEXT
);

CREATE TABLE IF NOT EXISTS fix_audit (
    seq INTEGER PRIMARY KEY AUTOINCREMENT,
    attempted_at TEXT NOT NULL,
    claim TEXT NOT NULL,
    evidence_type TEXT,
    author TEXT,
    outcome TEXT NOT NULL,             -- fixed | refused
    reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chart (
    id TEXT PRIMARY KEY,
    note TEXT NOT NULL,                -- the DR plot: hypothesis, inference, open question
    basis TEXT,                        -- where the projection came from (optional, honest)
    plotted_at TEXT NOT NULL,
    author TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open'  -- open | superseded | promoted
);
