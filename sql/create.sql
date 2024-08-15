-- Create the table if it doesn't exist
CREATE TABLE IF NOT EXISTS processed_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    successful BOOLEAN NOT NULL DEFAULT FALSE,
    hash TEXT
);