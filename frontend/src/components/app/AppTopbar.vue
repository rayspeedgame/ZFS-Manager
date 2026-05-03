<script setup>
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";

import { formatDateTime } from "../../lib/formatters.js";
import { setLocale, supportedLocales } from "../../i18n/index.js";
import { useAppState } from "../../store/state.js";

const props = defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
  state: { type: Object, required: true },
});

const { locale, t } = useI18n();
const { forceRefreshState } = useAppState();
const snapshot = computed(() => props.state.snapshot.value);
const meta = computed(() => snapshot.value?.meta || {});
const connectionState = computed(() => props.state.connectionState.value);
const sourceStatus = computed(() => meta.value?.source_status || "unknown");
const refreshing = ref(false);
const refreshError = ref("");
const lastUpdated = computed(() => formatDateTime(meta.value?.last_success_at));
const staleText = computed(() => {
  const staleSeconds = meta.value?.stale_seconds;
  if (staleSeconds === null || staleSeconds === undefined) {
    return t("app.topbar.fresh");
  }
  return staleSeconds === 0
    ? t("app.topbar.fresh")
    : t("app.topbar.secondsOld", { seconds: staleSeconds });
});

const localeOptions = computed(() =>
  supportedLocales.map((value) => ({
    value,
    label: t(`app.localeNames.${value}`),
  }))
);

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

function updateLocale(nextLocale) {
  setLocale(nextLocale);
}
</script>

<template>
  <header class="topbar-shell">
    <div>
      <p class="eyebrow">{{ t("app.topbar.eyebrow") }}</p>
      <h1>{{ title }}</h1>
      <p class="topbar-description">{{ description }}</p>
    </div>

    <section class="topbar-status-panel">
      <div class="topbar-status-header">
        <div>
          <p class="topbar-status-kicker">{{ t("app.topbar.liveStatus") }}</p>
          <strong class="topbar-status-title">{{ t("app.topbar.connectionAndRefresh") }}</strong>
        </div>
        <div class="topbar-header-actions">
          <label class="topbar-locale-picker">
            <span class="topbar-locale-label">{{ t("app.topbar.language") }}</span>
            <select :value="locale" class="property-field topbar-locale-select" @change="updateLocale($event.target.value)">
              <option v-for="option in localeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>
          <button type="button" class="ghost-button topbar-refresh-mini" :disabled="refreshing" @click="forceRefresh">
            {{ refreshing ? t("app.topbar.refreshing") : t("app.topbar.refresh") }}
          </button>
        </div>
      </div>

      <div class="topbar-meta">
        <div class="topbar-meta-item" :data-status="sourceStatus">
          <span class="meta-label">{{ t("app.topbar.sshSource") }}</span>
          <strong>{{ sourceStatus }}</strong>
        </div>
        <div class="topbar-meta-item" :data-status="connectionState">
          <span class="meta-label">{{ t("app.topbar.websocket") }}</span>
          <strong>{{ connectionState }}</strong>
        </div>
        <div class="topbar-meta-item">
          <span class="meta-label">{{ t("app.topbar.lastSuccess") }}</span>
          <strong>{{ lastUpdated }}</strong>
        </div>
        <div class="topbar-meta-item">
          <span class="meta-label">{{ t("app.topbar.dataAge") }}</span>
          <strong>{{ staleText }}</strong>
        </div>
      </div>

      <p v-if="refreshError" class="topbar-refresh-error">{{ refreshError }}</p>
    </section>
  </header>
</template>
