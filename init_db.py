"""Create and seed tasks.db for the Week 7 task-db-server MCP server.

The Flask app keeps its data in memory; this database exists only so the
MCP server has a SQLite table to query and update.

Run: python3 init_db.py  (recreates tasks.db from scratch each time)
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "tasks.db"

SEED_TASKS: list[tuple[str, str, str, str]] = [
    ("Buy groceries", "Alice", "2026-11-02", "open"),
    ("Write report", "Alice", "2026-11-05", "open"),
    ("Fix login bug", "Bob", "2026-11-03", "open"),
    ("Write unit tests", "Alice", "2026-11-10", "in_progress"),
    ("Review pull request", "Bob", "2026-11-04", "in_progress"),
    ("Call dentist", "Bob", "2026-10-20", "completed"),
    ("Set up CI pipeline", "Alice", "2026-10-15", "completed"),
]


def init_db(db_path: Path = DB_PATH) -> int:
    """Recreate the tasks table and insert the seed rows.

    Args:
        db_path: Path of the SQLite database file to create.

    Returns:
        The number of tasks inserted.

    Raises:
        sqlite3.Error: If the database cannot be created or written.
    """
    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TABLE IF EXISTS tasks")
        conn.execute(
            """
            CREATE TABLE tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                assigned_to TEXT NOT NULL,
                due_date    TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'open'
                            CHECK (status IN ('open', 'in_progress', 'completed'))
            )
            """
        )
        conn.executemany(
            "INSERT INTO tasks (title, assigned_to, due_date, status) VALUES (?, ?, ?, ?)",
            SEED_TASKS,
        )
    return len(SEED_TASKS)


if __name__ == "__main__":
    count = init_db()
    print(f"Created {DB_PATH} with {count} tasks")
