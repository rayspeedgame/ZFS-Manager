import { computed } from "vue";

import JsonDebugPanel from "../components/common/JsonDebugPanel.js";
import { formatBytes, formatPercent } from "../lib/formatters.js";

export default {
  components: {
    JsonDebugPanel,
  },
  props: {
    state: { type: Object, required: true },
  },
  setup(props) {
    const snapshot = computed(() => props.state.snapshot.value);
    const pools = computed(() => snapshot.value?.zpool_overview?.pools || []);
    const disks = computed(() => snapshot.value?.disk_overview?.lsblk?.blockdevices || []);
    const datasets = computed(() => snapshot.value?.dataset_overview?.datasets || []);

    const summaryCards = computed(() => {
      const unhealthyPools = pools.value.filter((pool) => pool.health !== "ONLINE").length;
      const used = pools.value.reduce((total, pool) => total + Number(pool.allocated || 0), 0);
      const free = pools.value.reduce((total, pool) => total + Number(pool.free || 0), 0);
      return [
        {
          label: "Connection",
          value: snapshot.value?.status || "unknown",
          meta: props.state.connectionState.value,
        },
        {
          label: "Pools",
          value: String(pools.value.length),
          meta: unhealthyPools ? `${unhealthyPools} unhealthy` : "All healthy",
        },
        {
          label: "Capacity",
          value: formatBytes(used),
          meta: `${formatBytes(free)} free`,
        },
        {
          label: "Datasets",
          value: String(datasets.value.length),
          meta: `${disks.value.length} disks discovered`,
        },
      ];
    });

    return {
      disks,
      pools,
      snapshot,
      summaryCards,
      datasets,
      formatBytes,
      formatPercent,
    };
  },
  template: `
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
                  <p>{{ pool.health }} · {{ formatBytes(pool.allocated) }} used</p>
                </div>
                <span class="inline-status" :data-health="pool.health">{{ formatPercent(pool.capacity) }}</span>
              </div>
              <div class="usage-bar">
                <span class="usage-bar-fill" :style="{ width: (pool.capacity || 0) + '%' }"></span>
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

      <JsonDebugPanel :payload="snapshot" />
    </section>
  `,
};
