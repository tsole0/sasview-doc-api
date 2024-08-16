SELECT branch_name
FROM processed_queries
WHERE hash = ?
LIMIT 1;