-- The Dog-Ear woods — FOREST-aligned core + Inn cable (content_hash).
-- Append-only. Signatures and ancestry required at insert.

CREATE TABLE IF NOT EXISTS entries (
  id            INTEGER PRIMARY KEY,
  created_at    TEXT NOT NULL,
  forest        TEXT NOT NULL,
  bucket        TEXT NOT NULL,
  signature     TEXT NOT NULL,
  authority     TEXT NOT NULL,
  visibility    TEXT NOT NULL DEFAULT 'open',
  superseded_by INTEGER REFERENCES entries(id),
  content_hash  TEXT,
  body          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS edges (
  from_id INTEGER NOT NULL REFERENCES entries(id),
  to_id   INTEGER NOT NULL REFERENCES entries(id),
  kind    TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
  body,
  content='entries',
  content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
  INSERT INTO entries_fts(rowid, body) VALUES (new.id, new.body);
END;

CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
  INSERT INTO entries_fts(entries_fts, rowid, body) VALUES ('delete', old.id, old.body);
END;

CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
  INSERT INTO entries_fts(entries_fts, rowid, body) VALUES ('delete', old.id, old.body);
  INSERT INTO entries_fts(rowid, body) VALUES (new.id, new.body);
END;

CREATE INDEX IF NOT EXISTS idx_entries_bucket ON entries(bucket);
CREATE INDEX IF NOT EXISTS idx_entries_forest ON entries(forest);
CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_id);
CREATE INDEX IF NOT EXISTS idx_edges_to ON edges(to_id);
