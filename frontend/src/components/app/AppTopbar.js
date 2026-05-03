import { computed, ref } from "vue";

import { formatDateTime } from "../../lib/formatters.js";
import { useAppState } from "../../store/state.js";

export default {
  props: {
    title: { type: String, required: true },
    description: { type: String, required: true },
    state: { type: Object, required: true },
  },
  setup(props) {
    const { forceRefreshState } = useAppState();
    const snapshot = computed(() => props.state.snapshot.value);
    const meta = computed(() => snapshot.value?.meta || {});
    const connectionState = computed(() => props.state.connectionState.value);
    const appStatus = computed(() => meta.value?.app_status || "unknown");
    const sourceStatus = computed(() => meta.value?.source_status || "unknown");
    const refreshing = ref(false);
    const refreshError = ref("");
    const lastUpdated = computed(() => formatDateTime(meta.value?.last_success_at));
    const staleText = computed(() => {
      const staleSeconds = meta.value?.stale_seconds;
      if (staleSeconds === null || staleSeconds === undefined) {
        return "Fresh";
      }
      return staleSeconds === 0 ? "Fresh" : `${staleSeconds}s old`;
    });

    async function forceRefresh() {
      refreshError.value = "";
      refreshing.value = true;
      try {
        await forceRefreshState();
      } catch (error) {
        refreshError.value = error instanceof Error ? error.message : String(error);
      } finally {
        refreshing.value = false;
      }
    }

    return {
      connectionState,
      forceRefresh,
      lastUpdated,
      refreshError,
      refreshing,
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

      <section class="topbar-status-panel">
        <div class="topbar-status-header">
          <div>
            <p class="topbar-status-kicker">Live Status</p>
            <strong class="topbar-status-title">Connection and refresh state</strong>
          </div>
          <button type="button" class="ghost-button topbar-refresh-mini" :disabled="refreshing" @click="forceRefresh">
            {{ refreshing ? "Refreshing..." : "Refresh" }}
          </button>
        </div>

        <div class="topbar-meta">
          <div class="topbar-meta-item" :data-status="sourceStatus">
            <span class="meta-label">SSH Source</span>
            <strong>{{ sourceStatus }}</strong>
          </div>
          <div class="topbar-meta-item" :data-status="connectionState">
            <span class="meta-label">WebSocket</span>
            <strong>{{ connectionState }}</strong>
          </div>
          <div class="topbar-meta-item">
            <span class="meta-label">Last Success</span>
            <strong>{{ lastUpdated }}</strong>
          </div>
          <div class="topbar-meta-item">
            <span class="meta-label">Data Age</span>
            <strong>{{ staleText }}</strong>
          </div>
        </div>

        <p v-if="refreshError" class="topbar-refresh-error">{{ refreshError }}</p>
      </section>
    </header>
  `,
};
