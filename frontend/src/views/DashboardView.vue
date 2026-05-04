<script setup>
import { computed } from "vue";
import { useI18n } from "vue-i18n";

import JsonDebugPanel from "../components/common/JsonDebugPanel.vue";
import { formatBytes, formatPercent } from "../lib/formatters.js";

const SHOW_DEBUG_PANEL = import.meta.env.VITE_SHOW_JSON_DEBUG === "true";
const { t } = useI18n();

const props = defineProps({
  state: { type: Object, required: true },
});

const snapshot = computed(() => props.state.snapshot.value);
const summary = computed(() => snapshot.value?.data?.summary || {});
const pools = computed(() => snapshot.value?.zpool_overview?.pools || []);
const disks = computed(() => snapshot.value?.disk_overview?.lsblk?.blockdevices || []);
const datasets = computed(() => snapshot.value?.dataset_overview?.datasets || []);

function getHealthClass(health) {
  const s = (health || "").toLowerCase();
  if (s === "online") return "health-online";
  if (s === "degraded" || s === "faulted" || s === "unavailable") return "health-warning";
  if (s === "offline") return "health-offline";
  return "health-unknown";
}

function getDiskStatus(disk) {
  const state = (disk.state || "").toLowerCase();
  const rota = disk.rota;
  if (state === "running") return t("dashboard.diskRunning");
  if (state === "idle") return t("dashboard.diskIdle");
  if (state === "standby") return t("dashboard.diskStandby");
  if (state === "unknown" || !state) return t("dashboard.diskUnknown");
  return disk.state;
}

function getDiskHealthClass(disk) {
  const state = (disk.state || "").toLowerCase();
  if (state === "running") return "health-online";
  if (state === "idle" || state === "standby") return "health-idle";
  if (state === "unknown" || !state) return "health-unknown";
  return "health-warning";
}

const summaryCards = computed(() => [
  {
    label: t("dashboard.summary.disks"),
    value: String(summary.value?.disk_count ?? disks.value.length),
    meta: t("dashboard.summary.allHealthy"),
  },
  {
    label: t("dashboard.summary.pools"),
    value: String(summary.value?.pool_count ?? pools.value.length),
    meta:
      (summary.value?.unhealthy_pool_count ?? 0) > 0
        ? t("dashboard.summary.unhealthyCount", { count: summary.value.unhealthy_pool_count })
        : t("dashboard.summary.allHealthy"),
  },
  {
    label: t("dashboard.summary.capacity"),
    value: formatBytes(summary.value?.total_allocated ?? 0),
    meta: t("dashboard.summary.freeValue", { value: formatBytes(summary.value?.total_free ?? 0) }),
  },
  {
    label: t("dashboard.summary.datasets"),
    value: String(summary.value?.dataset_count ?? datasets.value.length),
    meta: t("dashboard.summary.disksDiscovered", { count: summary.value?.disk_count ?? disks.value.length }),
  },
]);
</script>

<template>
  <section class="view-grid">
    <div class="summary-grid">
      <article v-for="card in summaryCards" :key="card.label" class="surface-panel summary-card">
        <span class="summary-label">{{ card.label }}</span>
        <strong class="summary-value">{{ card.value }}</strong>
        <span class="summary-meta">{{ card.meta }}</span>
      </article>
    </div>

    <div class="dashboard-grid">
      <article class="surface-panel">
        <div class="section-header">
          <div>
            <h3>{{ t("dashboard.poolOverview") }}</h3>
            <p>{{ t("dashboard.poolOverviewDescription") }}</p>
          </div>
        </div>

        <div class="stack-list" v-if="pools.length">
          <div v-for="pool in pools" :key="pool.name" class="stack-row">
            <div class="stack-row-head">
              <div>
                <strong>{{ pool.name }}</strong>
                <p>
                  <span class="health-status" :class="getHealthClass(pool.health)">{{ pool.health }}</span>
                  | {{ t("dashboard.usedValue", { value: formatBytes(pool.allocated) }) }}
                </p>
              </div>
              <span class="inline-status" :data-health="pool.health">{{ formatPercent(pool.capacity) }}</span>
            </div>
            <div class="usage-bar">
              <span class="usage-bar-fill" :style="{ width: `${pool.capacity || 0}%` }"></span>
            </div>
            <div class="stack-row-meta">
              <span>{{ t("dashboard.freeValue", { value: formatBytes(pool.free) }) }}</span>
              <span>{{ t("dashboard.fragmentationValue", { value: formatPercent(pool.fragmentation) }) }}</span>
              <span>{{ t("dashboard.dedupValue", { value: pool.dedupratio }) }}</span>
            </div>
          </div>
        </div>
      </article>

      <article class="surface-panel">
        <div class="section-header">
          <div>
            <h3>{{ t("dashboard.diskHealthOverview") }}</h3>
            <p>{{ t("dashboard.diskHealthOverviewDescription") }}</p>
          </div>
        </div>

        <div class="simple-list" v-if="disks.length">
          <div v-for="disk in disks" :key="disk.path || disk.name" class="disk-health-row">
            <span class="disk-name">{{ disk.name }}</span>
            <span class="disk-model">{{ disk.model || disk.type || "Unknown" }}</span>
            <span class="health-status" :class="getDiskHealthClass(disk)">{{ getDiskStatus(disk) }}</span>
          </div>
        </div>
        <div v-else class="empty-hint">{{ t("dashboard.noDisks") }}</div>
      </article>
    </div>

    <JsonDebugPanel v-if="SHOW_DEBUG_PANEL" :payload="snapshot" />
  </section>
</template>
