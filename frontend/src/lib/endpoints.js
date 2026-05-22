import { buildBackendOrigin } from "../services/api.js";

export function buildWebSocketUrl(path = "/ws/state") {
  const backendOrigin = new URL(buildBackendOrigin());
  backendOrigin.protocol = backendOrigin.protocol === "https:" ? "wss:" : "ws:";
  backendOrigin.pathname = path;
  backendOrigin.search = "";
  backendOrigin.hash = "";
  return backendOrigin.toString();
}
