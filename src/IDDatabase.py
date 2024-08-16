import sqlite3

from pathlib import Path
from threading import Lock
from typing import Any

lock = Lock()

def read_query(file_path):
    """Reads SQL from a file."""
    with open(file_path, 'r') as file:
        return file.read()

def execute_script(file_path):
    """Executes SQL commands from a file."""
    connection = sqlite3.connect(Path('src/sql/data.db'))
    cursor = connection.cursor()
    with open(file_path, 'r') as file:
        sql_script = file.read()
    # Execute the script
    cursor.executescript(sql_script)
    connection.commit()
    connection.close()

def returnData(script_path: Path, *inputs, **kwrds) -> Any:
    """
    Convenience function for returning data\n
    :param inputs: The inputs to the SQL query.\
    Include `rowid=True` to return last row ID instead of query result.
    """
    # Create table if it doesn't exist
    execute_script(Path('src/sql/create.sql'))

    connection = sqlite3.connect(Path('src/sql/data.db'))
    cursor = connection.cursor()

    # Read and execute a command command
    select_query = read_query(script_path)
    cursor.execute(select_query, tuple(input for input in inputs))
    if kwrds.get('rowid', False):
        result = cursor.lastrowid
    else:
        result = cursor.fetchone()
    connection.commit()
    connection.close()
    return result

def newData(filename, hash, branch_name):
    """Generate new row in database and return unique ID."""
    with lock:
        row_id = returnData(Path('src/sql/insert.sql'), filename, hash, branch_name, rowid=True)
        return row_id

def findBranch(hash):
    """Return the branch name for a given hash."""
    with lock:
        result = returnData(Path('src/sql/select.sql'), hash)

        if result:
            return result[0]
        else:
            return None
