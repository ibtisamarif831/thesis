-- Expand trial indices for 3 practice + 100 controlled trials. Preserve all v1 records.
CREATE TABLE recognition_attempts_v2 (
  attempt_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES recognition_sessions(session_id),
  trial_index INTEGER NOT NULL CHECK(trial_index BETWEEN 0 AND 102),
  phase TEXT NOT NULL CHECK(phase IN ('practice','recorded')),
  target_id TEXT NOT NULL,
  grid_json TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'active' CHECK(state IN ('active','interrupted','answered')),
  repeated_exposure INTEGER NOT NULL DEFAULT 0,
  started_at TEXT NOT NULL,
  received_at TEXT,
  response_json TEXT,
  correct INTEGER,
  interruption_json TEXT
);
INSERT INTO recognition_attempts_v2 SELECT * FROM recognition_attempts;
DROP TABLE recognition_attempts;
ALTER TABLE recognition_attempts_v2 RENAME TO recognition_attempts;
CREATE UNIQUE INDEX IF NOT EXISTS recognition_one_active ON recognition_attempts(session_id) WHERE state='active';
CREATE UNIQUE INDEX IF NOT EXISTS recognition_one_answer ON recognition_attempts(session_id,trial_index) WHERE state='answered';
CREATE INDEX IF NOT EXISTS recognition_attempts_session ON recognition_attempts(session_id,trial_index);
