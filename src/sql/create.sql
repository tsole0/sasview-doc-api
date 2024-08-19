-- Create the table if it doesn't exist
CREATE TABLE IF NOT EXISTS processed_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    lookup_hash TEXT,
    branch_name TEXT,
    successful BOOLEAN NOT NULL DEFAULT FALSE
);