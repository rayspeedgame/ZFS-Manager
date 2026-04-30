import { computed, reactive } from "vue";

const state = reactive({
  connectionState: "connecting",
  statusMessage: "Opening WebSocket connection...",
  snapshot: null,
  websocketUrl: "",
});

let socket = null;
let reconnectTimer = null;

function buildWebSocketUrl() {
  const backendPort = import.meta.env.VITE_BACKEND_PORT || "8000";
  const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${wsProtocol}://${window.location.hostname}:${backendPort}/ws/state`;
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

export function useAppState() {
  return {
    state: {
      connectionState: computed(() => state.connectionState),
      statusMessage: computed(() => state.statusMessage),
      snapshot: computed(() => state.snapshot),
      websocketUrl: computed(() => state.websocketUrl),
    },
    connect,
    disconnect,
  };
}
