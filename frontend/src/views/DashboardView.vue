<script setup>
import { computed } from "vue";

import JsonDebugPanel from "../components/common/JsonDebugPanel.vue";
import { formatBytes, formatPercent } from "../lib/formatters.js";

const SHOW_DEBUG_PANEL = import.meta.env.VITE_SHOW_JSON_DEBUG === "true";

const props = defineProps({
  state: { type: Object, required: true },
});

const snapshot = computed(() => props.state.snapshot.value);
const summary = computed(() => snapshot.value?.data?.summary || {});
const pools = computed(() => snapshot.value?.zpool_overview?.pools || []);
const disks = computed(() => snapshot.value?.disk_overview?.lsblk?.blockdevices || []);
const datasets = computed(() => snapshot.value?.dataset_overview?.datasets || []);

const summaryCards = computed(() => [
  {
    label: "Disks",
    value: String(summary.value?.disk_count ?? disks.value.length),
    meta: "All healthy",
  },
  {
    label: "Pools",
    value: String(summary.value?.pool_count ?? pools.value.length),
    meta:
      (summary.value?.unhealthy_pool_count ?? 0) > 0
        ? `${summary.value.unhealthy_pool_count} unhealthy`
        : "All healthy",
  },
  {
    label: "Capacity",
    value: formatBytes(summary.value?.total_allocated ?? 0),
    meta: `${formatBytes(summary.value?.total_free ?? 0)} free`,
  },
  {
    label: "Datasets",
    value: String(summary.value?.dataset_count ?? datasets.value.length),
    meta: `${summary.value?.disk_count ?? disks.value.length} disks discovered`,
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
            <h3>Pool Capacity</h3>
            <p>Live pool usage and health overview.</p>
          </div>
        </div>

        <div class="stack-list" v-if="pools.length">
          <div v-for="pool in pools" :key="pool.name" class="stack-row">
            <div class="stack-row-head">
              <div>
                <strong>{{ pool.name }}</strong>
                <p>{{ pool.health }} | {{ formatBytes(pool.allocated) }} used</p>
              </div>
              <span class="inline-status" :data-health="pool.health">{{ formatPercent(pool.capacity) }}</span>
            </div>
            <div class="usage-bar">
              <span class="usage-bar-fill" :style="{ width: `${pool.capacity || 0}%` }"></span>
            </div>
            <div class="stack-row-meta">
              <span>Free {{ formatBytes(pool.free) }}</span>
              <span>Fragmentation {{ formatPercent(pool.fragmentation) }}</span>
              <span>Dedup {{ pool.dedupratio }}</span>
            </div>
          </div>
        </div>
      </article>

      <article class="surface-panel">
        <div class="section-header">
          <div>
            <h3>Health Overview</h3>
            <p>Current pool and disk conditions from the live snapshot.</p>
          </div>
        </div>

        <div class="split-list">
          <div>
            <span class="mini-heading">Pools</span>
            <ul class="simple-list">
              <li v-for="pool in pools" :key="pool.name">
                <strong>{{ pool.name }}</strong>
                <span>{{ pool.health }}</span>
              </li>
            </ul>
          </div>

          <div>
            <span class="mini-heading">Disks</span>
            <ul class="simple-list">
              <li v-for="disk in disks" :key="disk.path || disk.name">
                <strong>{{ disk.name }}</strong>
                <span>{{ disk.model || disk.type }}</span>
              </li>
            </ul>
          </div>
        </div>
      </article>
    </div>

    <JsonDebugPanel v-if="SHOW_DEBUG_PANEL" :payload="snapshot" />
  </section>
</template>
