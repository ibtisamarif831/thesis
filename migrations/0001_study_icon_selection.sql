CREATE TABLE IF NOT EXISTS study_icons (
  icon_id TEXT PRIMARY KEY,
  set_id TEXT NOT NULL,
  label TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS study_icons_set_id_idx ON study_icons(set_id);

CREATE TABLE IF NOT EXISTS study_submissions (
  submission_id TEXT PRIMARY KEY,
  reviewer_code TEXT NOT NULL UNIQUE COLLATE NOCASE,
  selection_version TEXT NOT NULL,
  rationale TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS study_selections (
  submission_id TEXT NOT NULL REFERENCES study_submissions(submission_id) ON DELETE CASCADE,
  set_id TEXT NOT NULL,
  icon_id TEXT NOT NULL REFERENCES study_icons(icon_id),
  selection_order INTEGER NOT NULL CHECK(selection_order BETWEEN 1 AND 20),
  PRIMARY KEY (submission_id, set_id, icon_id),
  UNIQUE (submission_id, set_id, selection_order)
);

CREATE INDEX IF NOT EXISTS study_selections_icon_id_idx ON study_selections(icon_id);
