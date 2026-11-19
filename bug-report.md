# Task Management Application Bug Report

Review scope: frontend, backend, tests, dependencies, and project documentation.

Five defects were identified. No application source code was modified during this review.

| Bug ID | File Path | Error Type | Description | Priority |
|---|---|---|---|---|
| B-01 | `backend/app.py` | Runtime / validation | The title validator calls `.strip()` before checking that the title is a string. | High |
| B-02 | `backend/database.py` | Logical / database | The task query sorts oldest-first, contrary to its stated newest-first behavior. | Medium |
| B-03 | `backend/models.py` | API / integration | The serialized timestamp uses a different key from the key expected by the frontend and tests. | High |
| B-04 | `frontend/app.js` | Logical | The “Total tasks” summary excludes completed tasks. | Low |
| B-05 | `tests/test_api.py` | Syntax / testing | An assertion ends with an incomplete `and`, preventing the test module from being parsed. | High |

## Findings

### B-01 — Title validation can raise a runtime exception

- **Location:** `backend/app.py`, `_validate_fields`, approximately line 56
- **Category:** Runtime / validation
- **Issue:** The validator calls `title.strip()` before checking `isinstance(title, str)`.
- **Expected:** A non-string title should produce a `400` response explaining that the title must be a non-empty string.
- **Actual:** A JSON value such as a number can raise `AttributeError`, resulting in an unhandled server error.
- **Recommended correction:** Verify that the value is a string before calling string methods.

### B-02 — Task list ordering is reversed

- **Location:** `backend/database.py`, `get_tasks`, approximately line 50
- **Category:** Logical / database
- **Issue:** The query sorts task IDs in ascending order even though the function describes the result as newest-first.
- **Expected:** Newly created tasks appear before older tasks.
- **Actual:** Older tasks appear first.
- **Recommended correction:** Sort IDs in descending order to match the documented behavior.

### B-03 — Timestamp field name does not match the API contract

- **Location:** `backend/models.py`, `Task.to_dict`, approximately line 35
- **Category:** API / integration
- **Issue:** The serialized timestamp key is `created_on`, while the frontend and tests expect `created_at`.
- **Expected:** API responses contain the timestamp under `created_at`.
- **Actual:** The expected key is absent; the frontend cannot format the task date, and the create/retrieve test fails.
- **Recommended correction:** Use a consistent timestamp field name across the model, API response, frontend, and tests.

### B-04 — Total task count excludes completed tasks

- **Location:** `frontend/app.js`, `renderTasks`, approximately line 89
- **Category:** Logical
- **Issue:** The total count is calculated by subtracting completed tasks from all tasks.
- **Expected:** The total includes tasks in every status.
- **Actual:** The displayed total decreases when a task is completed.
- **Recommended correction:** Display the full task count in the total summary.

### B-05 — Test module contains invalid Python syntax

- **Location:** `tests/test_api.py`, `test_create_task_rejects_invalid_input`, approximately line 55
- **Category:** Syntax / testing
- **Issue:** An assertion ends with an incomplete `and` operator.
- **Expected:** Pytest imports the test module and runs its tests.
- **Actual:** Python raises a syntax error during test collection, preventing the suite from running.
- **Recommended correction:** Complete the boolean expression or remove the dangling operator.

