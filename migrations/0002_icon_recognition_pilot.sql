-- Additive: does not modify reviewer nominations or the catalog.
CREATE TABLE IF NOT EXISTS recognition_pilots (
  pilot_id TEXT PRIMARY KEY,
  invitation TEXT NOT NULL UNIQUE,
  title TEXT NOT NULL,
  config_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  closed_at TEXT
);
CREATE TABLE IF NOT EXISTS recognition_sessions (
  session_id TEXT PRIMARY KEY,
  pilot_id TEXT NOT NULL REFERENCES recognition_pilots(pilot_id),
  credential_hash TEXT NOT NULL,
  schedule_json TEXT NOT NULL,
  viewport_json TEXT NOT NULL,
  started_at TEXT NOT NULL,
  last_activity_at TEXT NOT NULL,
  completed_at TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','completed','ended')),
  debrief_json TEXT
);
CREATE INDEX IF NOT EXISTS recognition_sessions_pilot ON recognition_sessions(pilot_id);
CREATE TABLE IF NOT EXISTS recognition_attempts (
  attempt_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES recognition_sessions(session_id),
  trial_index INTEGER NOT NULL CHECK(trial_index BETWEEN 0 AND 22),
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
CREATE UNIQUE INDEX IF NOT EXISTS recognition_one_active ON recognition_attempts(session_id) WHERE state='active';
CREATE UNIQUE INDEX IF NOT EXISTS recognition_one_answer ON recognition_attempts(session_id,trial_index) WHERE state='answered';
CREATE INDEX IF NOT EXISTS recognition_attempts_session ON recognition_attempts(session_id,trial_index);
