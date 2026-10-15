CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    employee_id   TEXT UNIQUE,
    active        INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS fobs (
    fob_uid       TEXT PRIMARY KEY,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    assigned_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    revoked_at    TEXT
);

CREATE TABLE IF NOT EXISTS scans (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    fob_uid       TEXT,
    user_id       INTEGER,
    scanned_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    direction     TEXT NOT NULL,
    entry_source  TEXT NOT NULL DEFAULT 'fob',
    note          TEXT,
    created_by    TEXT
);

CREATE INDEX IF NOT EXISTS scans_user_time ON scans(user_id, scanned_at);
CREATE INDEX IF NOT EXISTS scans_time ON scans(scanned_at);

CREATE TABLE IF NOT EXISTS api_keys (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    label         TEXT NOT NULL,
    key_hash      TEXT NOT NULL UNIQUE,
    created_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    last_used_at  TEXT,
    revoked_at    TEXT
);
