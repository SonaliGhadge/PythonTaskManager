"""Application data models."""

from dataclasses import dataclass
from sqlite3 import Row


@dataclass(frozen=True)
class Task:
    """A task stored in the task manager."""

    id: int
    title: str
    description: str
    status: str
    created_at: str

    @classmethod
    def from_row(cls, row: Row) -> "Task":
        """Build a model from a SQLite result row."""
        return cls(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            created_at=row["created_at"],
        )

    def to_dict(self) -> dict[str, int | str]:
        """Serialize the task for the JSON API."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
        }
