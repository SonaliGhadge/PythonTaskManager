"""Flask REST API for the Taskflow application."""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request
from werkzeug.exceptions import BadRequest

from backend.database import (
    create_task as insert_task,
    delete_task as remove_task,
    get_tasks,
    initialize_database,
    update_task as save_task,
)

logger = logging.getLogger(__name__)
VALID_STATUSES = {"todo", "in_progress", "done"}
ALLOWED_UPDATE_FIELDS = {"title", "description", "status"}
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000


def _json_body() -> tuple[dict[str, Any] | None, tuple[Any, int] | None]:
    """Parse a JSON object or return a useful API error response."""
    if not request.is_json:
        return None, (jsonify(error="Content-Type must be application/json."), 415)
    try:
        payload = request.get_json()
    except BadRequest:
        return None, (jsonify(error="Request body must contain valid JSON."), 400)
    if not isinstance(payload, dict):
        return None, (jsonify(error="Request body must be a JSON object."), 400)
    return payload, None


def _validate_fields(
    payload: dict[str, Any],
    *,
    creating: bool,
) -> tuple[dict[str, str] | None, str | None]:
    """Validate request fields and return normalized fields or an error."""
    unknown_fields = set(payload) - ALLOWED_UPDATE_FIELDS
    if unknown_fields:
        return None, f"Unknown field(s): {', '.join(sorted(unknown_fields))}."

    if creating and "title" not in payload:
        return None, "Title is required."

    fields: dict[str, str] = {}
    if "title" in payload:
        title = payload["title"]
        if not isinstance(title, str) or not title.strip():
            return None, "Title must be a non-empty string."
        title = title.strip()
        if len(title) > MAX_TITLE_LENGTH:
            return None, f"Title must be {MAX_TITLE_LENGTH} characters or fewer."
        fields["title"] = title

    if "description" in payload:
        description = payload["description"]
        if not isinstance(description, str):
            return None, "Description must be a string."
        description = description.strip()
        if len(description) > MAX_DESCRIPTION_LENGTH:
            return None, (
                f"Description must be {MAX_DESCRIPTION_LENGTH} characters or fewer."
            )
        fields["description"] = description

    if "status" in payload:
        status = payload["status"]
        if not isinstance(status, str) or status not in VALID_STATUSES:
            return None, "Status must be one of: todo, in_progress, done."
        fields["status"] = status

    if creating:
        fields.setdefault("description", "")
        fields.setdefault("status", "todo")
    elif not fields:
        return None, "Provide at least one field to update."

    return fields, None


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_PATH=os.environ.get(
            "TASK_MANAGER_DATABASE",
            str(Path(__file__).resolve().parent / "tasks.db"),
        ),
        MAX_CONTENT_LENGTH=64 * 1024,
        CORS_ORIGINS={"http://127.0.0.1:8000", "http://localhost:8000"},
    )
    if test_config:
        app.config.update(test_config)
    initialize_database(app.config["DATABASE_PATH"])

    @app.after_request
    def add_cors_headers(response: Any) -> Any:
        origin = request.headers.get("Origin")
        if origin in app.config["CORS_ORIGINS"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.errorhandler(sqlite3.Error)
    def handle_database_error(error: sqlite3.Error) -> tuple[Any, int]:
        logger.exception("Database operation failed", exc_info=error)
        return jsonify(error="A database error occurred."), 500

    @app.errorhandler(413)
    def handle_too_large(_: Any) -> tuple[Any, int]:
        return jsonify(error="Request body is too large."), 413

    @app.route("/api/tasks", methods=["GET", "OPTIONS"])
    def tasks_collection() -> Any:
        if request.method == "OPTIONS":
            return "", 204
        tasks = get_tasks(app.config["DATABASE_PATH"])
        return jsonify(tasks=[task.to_dict() for task in tasks]), 200

    @app.route("/api/tasks", methods=["POST", "OPTIONS"])
    def tasks_create() -> Any:
        if request.method == "OPTIONS":
            return "", 204
        payload, error_response = _json_body()
        if error_response:
            return error_response
        fields, error = _validate_fields(payload, creating=True)
        if error:
            return jsonify(error=error), 400
        task = insert_task(
            app.config["DATABASE_PATH"],
            fields["title"],
            fields["description"],
            fields["status"],
        )
        return jsonify(task=task.to_dict()), 201

    @app.route("/api/tasks/<int:task_id>", methods=["PUT", "OPTIONS"])
    def tasks_update(task_id: int) -> Any:
        if request.method == "OPTIONS":
            return "", 204
        payload, error_response = _json_body()
        if error_response:
            return error_response
        fields, error = _validate_fields(payload, creating=False)
        if error:
            return jsonify(error=error), 400
        task = save_task(app.config["DATABASE_PATH"], task_id, fields)
        if task is None:
            return jsonify(error="Task not found."), 404
        return jsonify(task=task.to_dict()), 200

    @app.route("/api/tasks/<int:task_id>", methods=["DELETE", "OPTIONS"])
    def tasks_delete(task_id: int) -> Any:
        if request.method == "OPTIONS":
            return "", 204
        if not remove_task(app.config["DATABASE_PATH"], task_id):
            return jsonify(error="Task not found."), 404
        return "", 204

    @app.errorhandler(404)
    def handle_not_found(_: Any) -> tuple[Any, int]:
        return jsonify(error="Resource not found."), 404

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="127.0.0.1", port=5000, debug=False)
