const API_BASE_URL = "http://127.0.0.1:5000/api";
const taskList = document.querySelector("#task-list");
const taskDialog = document.querySelector("#task-dialog");
const taskForm = document.querySelector("#task-form");
const messageBox = document.querySelector("#message");
const statusFilter = document.querySelector("#status-filter");

let tasks = [];
let messageTimeout;

const statusLabels = {
  todo: "To do",
  in_progress: "In progress",
  done: "Completed",
};

document.querySelector("#today-label").textContent = new Intl.DateTimeFormat(
  undefined,
  { weekday: "short", month: "short", day: "numeric" },
).format(new Date());

document.querySelector("#new-task-button").addEventListener("click", () => {
  taskForm.reset();
  taskDialog.showModal();
  document.querySelector("#task-title").focus();
});
document.querySelector("#close-dialog").addEventListener("click", closeDialog);
document.querySelector("#cancel-dialog").addEventListener("click", closeDialog);
taskDialog.addEventListener("click", (event) => {
  if (event.target === taskDialog) closeDialog();
});
taskForm.addEventListener("submit", createTask);
statusFilter.addEventListener("change", renderTasks);
taskList.addEventListener("change", updateTaskStatus);
taskList.addEventListener("click", deleteTask);

function closeDialog() {
  taskDialog.close();
}

function showMessage(text, type = "success") {
  window.clearTimeout(messageTimeout);
  messageBox.textContent = text;
  messageBox.className = `message ${type}`;
  messageBox.hidden = false;
  messageTimeout = window.setTimeout(() => {
    messageBox.hidden = true;
  }, 4500);
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
  } catch (error) {
    throw new Error("Cannot connect to the API. Make sure the backend is running.");
  }

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || `Request failed (${response.status}).`);
  }
  return payload;
}

async function loadTasks() {
  taskList.innerHTML = '<div class="loading-state"><span class="spinner" aria-hidden="true"></span>Loading your tasks…</div>';
  try {
    const payload = await request("/tasks");
    tasks = payload.tasks;
    renderTasks();
  } catch (error) {
    taskList.innerHTML = `<div class="error-state">${escapeHtml(error.message)}<button class="button button-secondary" type="button" id="retry-load">Try again</button></div>`;
    taskList.querySelector("#retry-load").addEventListener("click", loadTasks);
    showMessage(error.message, "error");
  }
}

function renderTasks() {
  const inProgress = tasks.filter((task) => task.status === "in_progress").length;
  const completed = tasks.filter((task) => task.status === "done").length;
  document.querySelector("#task-count").textContent = tasks.length;
  document.querySelector("#total-count").textContent = tasks.length;
  document.querySelector("#in-progress-count").textContent = inProgress;
  document.querySelector("#completed-count").textContent = completed;

  const selectedStatus = statusFilter.value;
  const visibleTasks = tasks.filter(
    (task) => selectedStatus === "all" || task.status === selectedStatus,
  );
  if (!visibleTasks.length) {
    const isFiltered = selectedStatus !== "all";
    taskList.innerHTML = `
      <div class="empty-state">
        <span class="empty-icon" aria-hidden="true">${isFiltered ? "⌕" : "✦"}</span>
        <strong>${isFiltered ? "No tasks in this view" : "Nothing on your list yet"}</strong>
        <p>${isFiltered ? "Try another status filter." : "Create your first task and start making progress."}</p>
        ${isFiltered ? "" : '<button class="button button-primary" type="button" id="empty-new-task"><span aria-hidden="true">+</span> Create your first task</button>'}
      </div>`;
    taskList.querySelector("#empty-new-task")?.addEventListener("click", () => {
      taskDialog.showModal();
      document.querySelector("#task-title").focus();
    });
    return;
  }

  const rows = visibleTasks.map((task) => `
    <div class="task-row" data-task-id="${task.id}">
      <span class="task-title" title="${escapeHtml(task.title)}">${escapeHtml(task.title)}</span>
      <span class="task-description" title="${escapeHtml(task.description || "")}">${escapeHtml(task.description || "No description")}</span>
      <select class="status-select ${task.status}" aria-label="Status for ${escapeHtml(task.title)}" data-action="status" data-id="${task.id}">
        ${Object.entries(statusLabels).map(([value, label]) => `<option value="${value}" ${task.status === value ? "selected" : ""}>${label}</option>`).join("")}
      </select>
      <time class="task-date" datetime="${escapeHtml(task.created_at)}">${formatDate(task.created_at)}</time>
      <button class="delete-button" type="button" aria-label="Delete ${escapeHtml(task.title)}" title="Delete task" data-action="delete" data-id="${task.id}">×</button>
    </div>`).join("");
  taskList.innerHTML = `
    <div class="task-row table-head" aria-hidden="true">
      <span>Task</span><span>Description</span><span>Status</span><span>Created</span><span></span>
    </div>${rows}`;
}

async function createTask(event) {
  event.preventDefault();
  const submitButton = document.querySelector("#submit-task");
  const title = taskForm.elements.title.value.trim();
  const description = taskForm.elements.description.value.trim();
  if (!title) {
    taskForm.elements.title.focus();
    showMessage("Please enter a task title.", "error");
    return;
  }
  submitButton.disabled = true;
  submitButton.textContent = "Creating…";
  try {
    const payload = await request("/tasks", {
      method: "POST",
      body: JSON.stringify({ title, description }),
    });
    tasks.unshift(payload.task);
    closeDialog();
    taskForm.reset();
    statusFilter.value = "all";
    renderTasks();
    showMessage("Task created successfully.");
  } catch (error) {
    showMessage(error.message, "error");
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Create task";
  }
}

async function updateTaskStatus(event) {
  const select = event.target.closest('[data-action="status"]');
  if (!select) return;
  const task = tasks.find((item) => item.id === Number(select.dataset.id));
  if (!task) return;
  const previousStatus = task.status;
  select.disabled = true;
  try {
    const payload = await request(`/tasks/${task.id}`, {
      method: "PUT",
      body: JSON.stringify({ status: select.value }),
    });
    tasks = tasks.map((item) => item.id === payload.task.id ? payload.task : item);
    renderTasks();
    showMessage("Task status updated.");
  } catch (error) {
    select.value = previousStatus;
    showMessage(error.message, "error");
  } finally {
    select.disabled = false;
  }
}

async function deleteTask(event) {
  const button = event.target.closest('[data-action="delete"]');
  if (!button) return;
  const taskId = Number(button.dataset.id);
  const task = tasks.find((item) => item.id === taskId);
  if (!task || !window.confirm(`Delete "${task.title}"? This cannot be undone.`)) return;
  button.disabled = true;
  try {
    await request(`/tasks/${taskId}`, { method: "DELETE" });
    tasks = tasks.filter((item) => item.id !== taskId);
    renderTasks();
    showMessage("Task deleted.");
  } catch (error) {
    button.disabled = false;
    showMessage(error.message, "error");
  }
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(date);
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

loadTasks();
