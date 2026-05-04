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
