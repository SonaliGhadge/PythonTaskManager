"""SQLite persistence helpers for tasks."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from backend.models import Task


@contextmanager
def get_connection(database_path: str | Path) -> Iterator[sqlite3.Connection]:
    """Open a SQLite connection and ensure it is committed and closed."""
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(database_path: str | Path) -> None:
    """Create the database directory and tasks table if needed."""
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 200),
                description TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'todo'
                    CHECK(status IN ('todo', 'in_progress', 'done')),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            )
            """
        )


def get_tasks(database_path: str | Path) -> list[Task]:
    """Return all tasks, newest first."""
    with get_connection(database_path) as connection:
        rows = connection.execute(
            "SELECT id, title, description, status, created_at FROM tasks ORDER BY id DESC"
        ).fetchall()
    return [Task.from_row(row) for row in rows]


def get_task(database_path: str | Path, task_id: int) -> Task | None:
    """Return one task, or None if it does not exist."""
    with get_connection(database_path) as connection:
        row = connection.execute(
            "SELECT id, title, description, status, created_at FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    return Task.from_row(row) if row else None


def create_task(
    database_path: str | Path, title: str, description: str, status: str
) -> Task:
    """Insert a task and return the persisted record."""
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            "INSERT INTO tasks (title, description, status) VALUES (?, ?, ?)",
            (title, description, status),
        )
        row = connection.execute(
            "SELECT id, title, description, status, created_at FROM tasks WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return Task.from_row(row)


def update_task(
    database_path: str | Path,
    task_id: int,
    fields: dict[str, str],
) -> Task | None:
    """Update provided task fields and return the row, if present."""
    if not fields:
        return get_task(database_path, task_id)
    assignments = ", ".join(f"{field} = ?" for field in fields)
    values = [*fields.values(), task_id]
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            f"UPDATE tasks SET {assignments} WHERE id = ?", values
        )
        if cursor.rowcount == 0:
            return None
        row = connection.execute(
            "SELECT id, title, description, status, created_at FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
    return Task.from_row(row)


def delete_task(database_path: str | Path, task_id: int) -> bool:
    """Delete a task and return whether a row was removed."""
    with get_connection(database_path) as connection:
        cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    return cursor.rowcount > 0
