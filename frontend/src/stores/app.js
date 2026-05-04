import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { buildApiBaseUrl, getAuthStatus, login as loginRequest, logout as logoutRequest } from "../services/api.js";

let socket = null;
let reconnectTimer = null;
let shouldReconnect = true;

function buildWebSocketUrl() {
  const backendPort = import.meta.env.VITE_BACKEND_PORT || "8000";
  const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${wsProtocol}://${window.location.hostname}:${backendPort}/ws/state`;
}

export const useAppStore = defineStore("app", () => {
  const connectionState = ref("connecting");
  const statusMessage = ref("Opening WebSocket connection...");
  const snapshot = ref(null);
  const websocketUrl = ref("");
  const apiBaseUrl = ref("");
  const authEnabled = ref(false);
  const authenticated = ref(false);
  const authChecking = ref(true);
  const authError = ref("");

  function syncEndpoints() {
    websocketUrl.value = buildWebSocketUrl();
    apiBaseUrl.value = buildApiBaseUrl();
  }

  function scheduleReconnect() {
    reconnectTimer = window.setTimeout(connect, 2000);
  }

  function clearReconnectTimer() {
    if (reconnectTimer) {
      window.clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  }

  function attachSocketHandlers() {
    socket.onopen = () => {
      connectionState.value = "open";
      statusMessage.value = "WebSocket connected. Waiting for live updates...";
    };

    socket.onmessage = (event) => {
      snapshot.value = JSON.parse(event.data);
      statusMessage.value = snapshot.value?.message || "Received state update";
    };

    socket.onerror = () => {
      connectionState.value = "error";
      statusMessage.value = "WebSocket reported an error.";
    };

    socket.onclose = () => {
      connectionState.value = "closed";
      statusMessage.value = "WebSocket closed. Reconnecting in 2 seconds...";
      socket = null;
      if (shouldReconnect && (!authEnabled.value || authenticated.value)) {
        scheduleReconnect();
      }
    };
  }

  function connect() {
    // When password login is enabled, delay the socket until the user has an
    // authenticated session; otherwise the backend will reject the handshake.
    if (authEnabled.value && !authenticated.value) {
      return;
    }
    if (socket && [WebSocket.OPEN, WebSocket.CONNECTING].includes(socket.readyState)) {
      return;
    }

    shouldReconnect = true;
    clearReconnectTimer();
    syncEndpoints();
    connectionState.value = "connecting";
    statusMessage.value = `Connecting to ${websocketUrl.value}`;
    socket = new WebSocket(websocketUrl.value);
    attachSocketHandlers();
  }

  function disconnect() {
    shouldReconnect = false;
    clearReconnectTimer();
    if (socket) {
      socket.close();
      socket = null;
    }
  }

  async function refreshAuthStatus() {
    authChecking.value = true;
    authError.value = "";
    try {
      const status = await getAuthStatus();
      authEnabled.value = Boolean(status?.enabled);
      // Treat auth as satisfied when the feature is disabled so the rest of
      // the app can boot exactly like the original no-login behavior.
      authenticated.value = Boolean(status?.authenticated) || !authEnabled.value;
      if (authenticated.value) {
        connect();
      } else {
        disconnect();
      }
      return status;
    } catch (error) {
      authError.value = error instanceof Error ? error.message : String(error);
      throw error;
    } finally {
      authChecking.value = false;
    }
  }

  async function login(password) {
    const result = await loginRequest({ password });
    authenticated.value = true;
    authError.value = "";
    connect();
    return result;
  }

  async function logout() {
    const result = await logoutRequest();
    authenticated.value = false;
    disconnect();
    return result;
  }

  async function refreshStateOnce() {
    syncEndpoints();
    const response = await fetch(`${apiBaseUrl.value}/state`, {
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`Failed to refresh state: ${response.status}`);
    }
    const nextSnapshot = await response.json();
    snapshot.value = nextSnapshot;
    statusMessage.value = nextSnapshot.message || "Fetched latest state snapshot.";
    return nextSnapshot;
  }

  async function forceRefreshState() {
    syncEndpoints();
    const response = await fetch(`${apiBaseUrl.value}/state/refresh`, {
      method: "POST",
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`Failed to force refresh state: ${response.status}`);
    }
    const nextSnapshot = await response.json();
    snapshot.value = nextSnapshot;
    statusMessage.value = nextSnapshot.message || "Forced a full backend refresh.";
    return nextSnapshot;
  }

  return {
    apiBaseUrl,
    authChecking,
    authEnabled,
    authenticated,
    authError,
    connectionState,
    connect,
    disconnect,
    forceRefreshState,
    login,
    logout,
    refreshAuthStatus,
    refreshStateOnce,
    snapshot,
    statusMessage,
    websocketUrl,
    state: computed(() => ({
      connectionState: computed(() => connectionState.value),
      authChecking: computed(() => authChecking.value),
      authEnabled: computed(() => authEnabled.value),
      authenticated: computed(() => authenticated.value),
      authError: computed(() => authError.value),
      statusMessage: computed(() => statusMessage.value),
      snapshot: computed(() => snapshot.value),
      websocketUrl: computed(() => websocketUrl.value),
      apiBaseUrl: computed(() => apiBaseUrl.value),
    })),
  };
});
