# Taskflow — Task Management Web Application

A lightweight task management dashboard built with Flask, SQLite, HTML, CSS, and vanilla JavaScript. Tasks persist in a local SQLite database. The dashboard lets you create tasks, change their status, filter the list, and delete tasks.

## Architecture

```text
python-task-manager/
├── backend/
│   ├── app.py             # Flask routes, validation, and error responses
│   ├── database.py        # SQLite schema and persistence operations
│   ├── models.py          # Task model and JSON serialization
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── index.html         # Dashboard markup
│   ├── style.css          # Responsive dashboard styles
│   └── app.js             # UI behavior and REST API client
├── tests/
│   └── test_api.py        # API tests using isolated SQLite databases
├── README.md
└── .gitignore
```

The browser app calls the Flask API at `http://127.0.0.1:5000/api`. The API creates `backend/tasks.db` on first launch by default. Set `TASK_MANAGER_DATABASE` to use another database file. The API permits browser requests from `http://127.0.0.1:8000` and `http://localhost:8000`, the origins used by the local frontend server below.

## Requirements

- Python 3.10 or newer
- pip

## Installation

Open a terminal in the project root and create/activate a virtual environment:

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r backend\requirements.txt
```

**macOS/Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

## Start the backend

From the project root, with the virtual environment active:

```powershell
py -m backend.app
```

On macOS/Linux, use `python -m backend.app`. The API is available at `http://127.0.0.1:5000`. Keep this terminal running.

## Launch the frontend

Open a second terminal in the project root and serve the static frontend on port 8000:

```powershell
py -m http.server 8000 --directory frontend
```

On macOS/Linux, use `python3 -m http.server 8000 --directory frontend`. Then open `http://127.0.0.1:8000` in your browser. The frontend server and backend must both be running.

## API

All request and response bodies use JSON unless noted otherwise. A task has `id`, `title`, `description`, `status`, and `created_at`. Valid statuses are `todo`, `in_progress`, and `done`. Titles are required (1–200 characters); descriptions are optional (up to 2,000 characters).

| Method | Endpoint | Description | Success response |
|---|---|---|---|
| `GET` | `/api/tasks` | List tasks, newest first | `200 {"tasks": [...]}` |
| `POST` | `/api/tasks` | Create a task; requires `title`, optional `description` and `status` | `201 {"task": {...}}` |
| `PUT` | `/api/tasks/<id>` | Update one or more of `title`, `description`, or `status` | `200 {"task": {...}}` |
| `DELETE` | `/api/tasks/<id>` | Delete a task | `204` with no body |

Invalid input returns `400`, unsupported content type returns `415`, a missing task returns `404`, and oversized request bodies return `413`. Unexpected SQLite errors return `500` with a generic error message.

Example:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/tasks `
  -ContentType application/json -Body '{"title":"Plan the week","description":"Review priorities"}'
```

## Tests

Run the API test suite from the project root:

```powershell
py -m pytest
```

On macOS/Linux, use `python -m pytest`. Tests use a temporary SQLite database and do not modify the development database.
