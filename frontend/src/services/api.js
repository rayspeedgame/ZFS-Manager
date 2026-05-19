function buildApiBaseUrl() {
  const backendPort = import.meta.env.VITE_BACKEND_PORT || "8000";
  return `${window.location.protocol}//${window.location.hostname}:${backendPort}/api`;
}

async function parsePayload(response) {
  return response.json().catch(() => null);
}

async function request(path, init = {}, errorLabel = "Request failed") {
  const response = await fetch(`${buildApiBaseUrl()}${path}`, {
    // Settings save, login, and state refresh all rely on the backend cookie.
    credentials: "include",
    ...init,
  });
  const payload = await parsePayload(response);

  if (!response.ok) {
    throw new Error(payload?.detail || `${errorLabel}: ${response.status}`);
  }

  return payload;
}

export async function getAuthStatus() {
  return request("/auth/status", {}, "Failed to load auth status");
}

export async function login(payload) {
  return request(
    "/auth/login",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "Failed to log in"
  );
}

export async function logout() {
  return request(
    "/auth/logout",
    {
      method: "POST",
    },
    "Failed to log out"
  );
}

export async function getTasks({ page = 1, pageSize = 20, statusFilter = "" } = {}) {
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (statusFilter) {
    query.set("status_filter", String(statusFilter));
  }
  return request(`/tasks?${query.toString()}`, {}, "Failed to load tasks");
}

export async function getTask(taskId) {
  return request(`/tasks/${encodeURIComponent(taskId)}`, {}, "Failed to load task");
}

export async function getTaskSchedules() {
  return request("/task-schedules", {}, "Failed to load task schedules");
}

export async function getSnapshots({
  page = 1,
  pageSize = 25,
  search = "",
  pool = "",
  dataset = "",
  snapshotType = "",
  sortBy = "created_at",
  sortOrder = "desc",
} = {}) {
  const query = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    sort_by: String(sortBy),
    sort_order: String(sortOrder),
  });
  if (search) {
    query.set("search", String(search));
  }
  if (pool) {
    query.set("pool", String(pool));
  }
  if (dataset) {
    query.set("dataset", String(dataset));
  }
  if (snapshotType) {
    query.set("snapshot_type", String(snapshotType));
  }
  return request(`/snapshots?${query.toString()}`, {}, "Failed to load snapshots");
}

export async function getSnapshot(snapshotName) {
  return request(`/snapshots/${encodeURIComponent(snapshotName)}`, {}, "Failed to load snapshot");
}

export async function getSnapshotFilters() {
  return request("/snapshots/filters", {}, "Failed to load snapshot filters");
}

export async function getDatasetSnapshots(datasetName, limit = 5) {
  const query = new URLSearchParams({ limit: String(limit) });
  return request(
    `/datasets/${encodeURIComponent(datasetName)}/snapshots?${query.toString()}`,
    {},
    "Failed to load dataset snapshots"
  );
}

export async function createSnapshot(datasetName, payload) {
  return request(
    `/datasets/${encodeURIComponent(datasetName)}/snapshots`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "Failed to create snapshot"
  );
}

export async function destroySnapshot(snapshotName) {
  return request(
    `/snapshots/${encodeURIComponent(snapshotName)}`,
    {
      method: "DELETE",
    },
    "Failed to delete snapshot"
  );
}

export async function rollbackSnapshot(snapshotName, payload = { mode: "safe" }) {
  return request(
    `/snapshots/${encodeURIComponent(snapshotName)}/rollback`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "Failed to roll back snapshot"
  );
}

export async function createTaskSchedule(payload) {
  return request(
    "/task-schedules",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "Failed to create task schedule"
  );
}

export async function updateTaskSchedule(scheduleId, payload) {
  return request(
    `/task-schedules/${encodeURIComponent(scheduleId)}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "Failed to update task schedule"
  );
}

export async function deleteTaskSchedule(scheduleId) {
  return request(
    `/task-schedules/${encodeURIComponent(scheduleId)}`,
    {
      method: "DELETE",
    },
    "Failed to delete task schedule"
  );
}

export async function updatePoolProperties(poolName, changes) {
  return request(
    `/pools/${encodeURIComponent(poolName)}/properties`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ changes }),
    },
    "Failed to update pool properties"
  );
}

export async function startPoolScrub(poolName) {
  return request(
    `/pools/${encodeURIComponent(poolName)}/scrub/start`,
    {
      method: "POST",
    },
    "Failed to start pool scrub"
  );
}

export async function stopPoolScrub(poolName) {
  return request(
    `/pools/${encodeURIComponent(poolName)}/scrub/stop`,
    {
      method: "POST",
    },
    "Failed to stop pool scrub"
  );
}

export async function getSettings() {
  return request("/settings", {}, "Failed to load settings");
}

export async function saveSettings(payload) {
  return request(
    "/settings",
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "Failed to save settings"
  );
}

export async function testSshConnection(payload) {
  return request(
    "/settings/test-ssh",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "Failed to test SSH connection"
  );
}

export async function updatePoolTopology(poolName, additions, force = false) {
  return request(
    `/pools/${encodeURIComponent(poolName)}/topology`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ additions, force }),
    },
    "Failed to update pool topology"
  );
}

export async function updateDatasetProperties(datasetName, changes) {
  return request(
    `/datasets/${encodeURIComponent(datasetName)}/properties`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ changes }),
    },
    "Failed to update dataset properties"
  );
}

export async function createDataset(payload) {
  return request(
    "/datasets",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "Failed to create dataset"
  );
}

export async function destroyDataset(datasetName) {
  return request(
    `/datasets/${encodeURIComponent(datasetName)}/destroy`,
    {
      method: "POST",
    },
    "Failed to destroy dataset"
  );
}

export async function createPool(payload) {
  return request(
    "/pools",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
    "Failed to create pool"
  );
}

export async function destroyPool(poolName) {
  return request(
    `/pools/${encodeURIComponent(poolName)}/destroy`,
    {
      method: "POST",
    },
    "Failed to destroy pool"
  );
}

export async function removePoolTarget(poolName, commandTarget) {
  return request(
    `/pools/${encodeURIComponent(poolName)}/remove`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ command_target: commandTarget }),
    },
    "Failed to remove pool target"
  );
}

export { buildApiBaseUrl };
