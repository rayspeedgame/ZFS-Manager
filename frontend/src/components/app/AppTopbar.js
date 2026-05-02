import { computed } from "vue";

import StatusBadge from "./StatusBadge.js";
import { formatDateTime } from "../../lib/formatters.js";

export default {
  components: {
    StatusBadge,
  },
  props: {
    title: { type: String, required: true },
    description: { type: String, required: true },
    state: { type: Object, required: true },
  },
  setup(props) {
    const snapshot = computed(() => props.state.snapshot.value);
    const meta = computed(() => snapshot.value?.meta || {});
    const connectionState = computed(() => props.state.connectionState.value);
    const appStatus = computed(() => meta.value?.app_status || "unknown");
    const sourceStatus = computed(() => meta.value?.source_status || "unknown");
    const lastUpdated = computed(() => formatDateTime(meta.value?.last_success_at));
    const staleText = computed(() => {
      const staleSeconds = meta.value?.stale_seconds;
      if (staleSeconds === null || staleSeconds === undefined) {
        return "Fresh";
      }
      return staleSeconds === 0 ? "Fresh" : `${staleSeconds}s old`;
    });

    return {
      appStatus,
      connectionState,
      lastUpdated,
      meta,
      snapshot,
      sourceStatus,
      staleText,
    };
  },
  template: `
    <header class="topbar-shell">
      <div>
        <p class="eyebrow">Realtime Storage Console</p>
        <h1>{{ title }}</h1>
        <p class="topbar-description">{{ description }}</p>
      </div>

      <div class="topbar-meta">
        <div class="meta-pill" :data-status="appStatus">
          <span class="meta-label">SSH Source</span>
          <strong>{{ sourceStatus }}</strong>
        </div>
        <div class="meta-pill">
          <span class="meta-label">Last Success</span>
          <strong>{{ lastUpdated }}</strong>
        </div>
        <div class="meta-pill">
          <span class="meta-label">Data Age</span>
          <strong>{{ staleText }}</strong>
        </div>
        <div class="meta-pill">
          <span class="meta-label">WebSocket</span>
          <strong>{{ connectionState }}</strong>
        </div>
        <StatusBadge :state="appStatus" />
      </div>
    </header>
  `,
};
