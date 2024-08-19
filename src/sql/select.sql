SELECT branch_name
FROM processed_queries
WHERE lookup_hash = ?
LIMIT 1;