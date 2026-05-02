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
    disconnect,
    refreshStateOnce,
    updatePoolProperties,
  };
}
