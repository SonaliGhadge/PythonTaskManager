"""Tests for the task management API."""

import pytest

from backend.app import create_app


@pytest.fixture
def client(tmp_path):
    """Provide an isolated Flask test client and SQLite database."""
    app = create_app(
        {
            "TESTING": True,
            "DATABASE_PATH": str(tmp_path / "test_tasks.db"),
        }
    )
    with app.test_client() as test_client:
        yield test_client


def test_get_tasks_returns_empty_list(client):
    response = client.get("/api/tasks")

    assert response.status_code == 200
    assert response.get_json() == {"tasks": []}


def test_create_and_retrieve_task(client):
    created = client.post(
        "/api/tasks",
        json={"title": "Write tests", "description": "Cover the API"},
    )

    assert created.status_code == 201
    task = created.get_json()["task"]
    assert task["title"] == "Write tests"
    assert task["description"] == "Cover the API"
    assert task["status"] == "todo"
    assert task["id"] > 0
    assert task["created_at"]

    retrieved = client.get("/api/tasks")
    assert retrieved.status_code == 200
    assert retrieved.get_json()["tasks"] == [task]


def test_create_task_rejects_invalid_input(client):
    missing_title = client.post("/api/tasks", json={"description": "No title"})
    blank_title = client.post("/api/tasks", json={"title": "  "})
    invalid_status = client.post(
        "/api/tasks", json={"title": "Task", "status": "blocked"}
    )
    non_object = client.post("/api/tasks", json=["not", "an", "object"])

    assert missing_title.status_code == 400
    assert "Title is required" in missing_title.get_json()["error"]
    assert blank_title.status_code == 400
    assert invalid_status.status_code == 400
    assert non_object.status_code == 400


def test_create_task_requires_json_content_type(client):
    response = client.post("/api/tasks", data="title=Task")

    assert response.status_code == 415
    assert "application/json" in response.get_json()["error"]


def test_update_task(client):
    task_id = client.post("/api/tasks", json={"title": "Original"}).get_json()["task"]["id"]

    response = client.put(
        f"/api/tasks/{task_id}",
        json={"title": "Updated", "status": "in_progress"},
    )

    assert response.status_code == 200
    assert response.get_json()["task"]["title"] == "Updated"
    assert response.get_json()["task"]["status"] == "in_progress"


def test_update_task_rejects_invalid_input(client):
    task_id = client.post("/api/tasks", json={"title": "Task"}).get_json()["task"]["id"]

    invalid_status = client.put(
        f"/api/tasks/{task_id}", json={"status": "unknown"}
    )
    empty_update = client.put(f"/api/tasks/{task_id}", json={})

    assert invalid_status.status_code == 400
    assert empty_update.status_code == 400


def test_update_missing_task_returns_404(client):
    response = client.put("/api/tasks/999", json={"title": "Missing"})

    assert response.status_code == 404
    assert response.get_json()["error"] == "Task not found."


def test_delete_task(client):
    task_id = client.post("/api/tasks", json={"title": "Remove me"}).get_json()["task"]["id"]

    deleted = client.delete(f"/api/tasks/{task_id}")

    assert deleted.status_code == 204
    assert client.get("/api/tasks").get_json()["tasks"] == []


def test_delete_missing_task_returns_404(client):
    response = client.delete("/api/tasks/999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Task not found."
