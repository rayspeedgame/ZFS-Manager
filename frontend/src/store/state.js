import { computed, reactive } from "vue";

const state = reactive({
  connectionState: "connecting",
  statusMessage: "Opening WebSocket connection...",
  snapshot: null,
  websocketUrl: "",
  apiBaseUrl: "",
});

let socket = null;
let reconnectTimer = null;

function buildWebSocketUrl() {
  const backendPort = import.meta.env.VITE_BACKEND_PORT || "8000";
  const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${wsProtocol}://${window.location.hostname}:${backendPort}/ws/state`;
}

function buildApiBaseUrl() {
  const backendPort = import.meta.env.VITE_BACKEND_PORT || "8000";
  return `${window.location.protocol}//${window.location.hostname}:${backendPort}/api`;
}

function connect() {
  if (socket && socket.readyState === WebSocket.OPEN) {
    return;
  }

  if (reconnectTimer) {
    window.clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }

  state.websocketUrl = buildWebSocketUrl();
  state.apiBaseUrl = buildApiBaseUrl();
  state.connectionState = "connecting";
  state.statusMessage = `Connecting to ${state.websocketUrl}`;

  socket = new WebSocket(state.websocketUrl);

  socket.onopen = () => {
    state.connectionState = "open";
    state.statusMessage = "WebSocket connected. Waiting for live updates...";
  };

  socket.onmessage = (event) => {
    state.snapshot = JSON.parse(event.data);
    state.statusMessage = state.snapshot.message || "Received state update";
  };

  socket.onerror = () => {
    state.connectionState = "error";
    state.statusMessage = "WebSocket reported an error.";
  };

  socket.onclose = () => {
    state.connectionState = "closed";
    state.statusMessage = "WebSocket closed. Reconnecting in 2 seconds...";
    reconnectTimer = window.setTimeout(connect, 2000);
  };
}

function disconnect() {
  if (reconnectTimer) {
    window.clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (socket) {
    socket.close();
    socket = null;
  }
}

async function refreshStateOnce() {
  // Use REST as an explicit resync path after writes or transient WS issues.
  const response = await fetch(`${buildApiBaseUrl()}/state`);
  if (!response.ok) {
    throw new Error(`Failed to refresh state: ${response.status}`);
  }
  const snapshot = await response.json();
  state.snapshot = snapshot;
  state.statusMessage = snapshot.message || "Fetched latest state snapshot.";
  return snapshot;
}

async function forceRefreshState() {
  const response = await fetch(`${buildApiBaseUrl()}/state/refresh`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Failed to force refresh state: ${response.status}`);
  }
  const snapshot = await response.json();
  state.snapshot = snapshot;
  state.statusMessage = snapshot.message || "Forced a full backend refresh.";
  return snapshot;
}

async function updatePoolProperties(poolName, changes) {
  const response = await fetch(`${buildApiBaseUrl()}/pools/${encodeURIComponent(poolName)}/properties`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ changes }),
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(payload?.detail || `Failed to update pool properties: ${response.status}`);
  }
  return payload;
}

async function updatePoolTopology(poolName, additions, force = false) {
  const response = await fetch(`${buildApiBaseUrl()}/pools/${encodeURIComponent(poolName)}/topology`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ additions, force }),
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(payload?.detail || `Failed to update pool topology: ${response.status}`);
  }
  return payload;
}

async function updateDatasetProperties(datasetName, changes) {
  const response = await fetch(`${buildApiBaseUrl()}/datasets/${encodeURIComponent(datasetName)}/properties`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ changes }),
  });

  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(payload?.detail || `Failed to update dataset properties: ${response.status}`);
  }
  return payload;
}

async function createDataset(payload) {
  const response = await fetch(`${buildApiBaseUrl()}/datasets`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const result = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(result?.detail || `Failed to create dataset: ${response.status}`);
  }
  return result;
}

async function destroyDataset(datasetName) {
  const response = await fetch(`${buildApiBaseUrl()}/datasets/${encodeURIComponent(datasetName)}/destroy`, {
    method: "POST",
  });

  const result = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(result?.detail || `Failed to destroy dataset: ${response.status}`);
  }
  return result;
}

async function createPool(payload) {
  const response = await fetch(`${buildApiBaseUrl()}/pools`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const result = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(result?.detail || `Failed to create pool: ${response.status}`);
  }
  return result;
}

async function destroyPool(poolName) {
  const response = await fetch(`${buildApiBaseUrl()}/pools/${encodeURIComponent(poolName)}/destroy`, {
    method: "POST",
  });

  const result = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(result?.detail || `Failed to destroy pool: ${response.status}`);
  }
  return result;
}

async function removePoolTarget(poolName, commandTarget) {
  const response = await fetch(`${buildApiBaseUrl()}/pools/${encodeURIComponent(poolName)}/remove`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ command_target: commandTarget }),
  });

  const result = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(result?.detail || `Failed to remove pool target: ${response.status}`);
  }
  return result;
}

export function useAppState() {
  return {
    state: {
      connectionState: computed(() => state.connectionState),
      statusMessage: computed(() => state.statusMessage),
      snapshot: computed(() => state.snapshot),
      websocketUrl: computed(() => state.websocketUrl),
      apiBaseUrl: computed(() => state.apiBaseUrl),
    },
    connect,
    createDataset,
    destroyDataset,
    disconnect,
    forceRefreshState,
    createPool,
    destroyPool,
    removePoolTarget,
    refreshStateOnce,
    updateDatasetProperties,
    updatePoolProperties,
    updatePoolTopology,
  };
}
