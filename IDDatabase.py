import sqlite3

from pathlib import Path
from threading import Lock

lock = Lock()

def read_query(file_path):
    """Reads SQL from a file."""
    with open(file_path, 'r') as file:
        return file.read()

def execute_script(file_path):
    """Executes SQL commands from a file."""
    connection = sqlite3.connect(Path('sql/data.db'))
    cursor = connection.cursor()
    with open(file_path, 'r') as file:
        sql_script = file.read()
    # Execute the script
    cursor.executescript(sql_script)
    connection.commit()
    connection.close()

def access_database(filename):
    """Generate new row in database and return unique ID."""
    with lock:
        # Create table if it doesn't exist
        execute_script(Path('sql/create.sql'))

        # Insert new row using the SQL from insert.sql and get the ID
        connection = sqlite3.connect(Path('sql/data.db'))
        cursor = connection.cursor()

        # Read and execute the insert command
        insert_query = read_query(Path('sql/insert.sql'))
        cursor.execute(insert_query, (filename,))
        row_id = cursor.lastrowid

        connection.commit()
        connection.close()

        return row_id
