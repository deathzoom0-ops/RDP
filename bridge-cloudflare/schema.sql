CREATE TABLE IF NOT EXISTS jobs (
  ticket TEXT PRIMARY KEY,
  preset TEXT NOT NULL,
  expires INTEGER NOT NULL,
  status TEXT NOT NULL,
  format TEXT,
  content TEXT
);
CREATE INDEX IF NOT EXISTS jobs_expires ON jobs(expires);
