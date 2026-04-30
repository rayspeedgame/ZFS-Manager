import { computed } from "vue";

import StatusBadge from "./StatusBadge.js";
import { formatDateTime, formatSourceLabel } from "../../lib/formatters.js";

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
    const connectionState = computed(() => props.state.connectionState.value);
    const sourceLabel = computed(() =>
      formatSourceLabel(snapshot.value?.message, snapshot.value?.status)
    );
    const lastUpdated = computed(() => formatDateTime(snapshot.value?.last_updated));

    return {
      connectionState,
      lastUpdated,
      snapshot,
      sourceLabel,
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
        <div class="meta-pill">
          <span class="meta-label">Source</span>
          <strong>{{ sourceLabel }}</strong>
        </div>
        <div class="meta-pill">
          <span class="meta-label">Updated</span>
          <strong>{{ lastUpdated }}</strong>
        </div>
        <div class="meta-pill">
          <span class="meta-label">Interval</span>
          <strong>{{ snapshot?.refresh_interval_seconds || "-" }}s</strong>
        </div>
        <StatusBadge :state="connectionState" />
      </div>
    </header>
  `,
};
