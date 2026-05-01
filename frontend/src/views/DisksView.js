import { computed, ref } from "vue";

import DetailDrawer from "../components/common/DetailDrawer.js";
import EmptyState from "../components/common/EmptyState.js";
import { formatBytes } from "../lib/formatters.js";

export default {
  components: {
    DetailDrawer,
    EmptyState,
  },
  props: {
    state: { type: Object, required: true },
  },
  setup(props) {
    const selectedDisk = ref(null);
    const drawerOpen = ref(false);

    const rows = computed(() => props.state.snapshot.value?.data?.disks || []);

    function openDisk(row) {
      selectedDisk.value = row;
      drawerOpen.value = true;
    }

    return {
      drawerOpen,
      openDisk,
      rows,
      selectedDisk,
      formatBytes,
    };
  },
  template: `
    <section class="view-grid">
      <article class="surface-panel">
        <div class="section-header">
          <div>
            <h3>Disk Inventory</h3>
            <p>Physical devices, partitions, and detected ZFS membership.</p>
          </div>
        </div>

        <EmptyState
          v-if="!rows.length"
          title="No disks discovered"
          description="The current snapshot did not report any block devices."
        />

        <div v-else class="table-shell">
          <table class="data-table">
            <thead>
              <tr>
                <th>Device</th>
                <th>Model</th>
                <th>Size</th>
                <th>Filesystem</th>
                <th>Pool</th>
                <th>Mount</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.path || row.name">
                <td>
                  <strong>{{ row.name }}</strong>
                  <div class="subtle-text">{{ row.path }}</div>
                </td>
                <td>{{ row.model || "-" }}</td>
                <td>{{ formatBytes(row.size) }}</td>
                <td>{{ row.filesystem }}</td>
                <td>{{ row.poolName }}</td>
                <td>{{ row.mountpoint }}</td>
                <td class="action-cell">
                  <button type="button" class="ghost-button" @click="openDisk(row)">View</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <DetailDrawer
        v-model="drawerOpen"
        title="Disk Details"
        :description="selectedDisk?.path || ''"
      >
        <div v-if="selectedDisk" class="drawer-section-list">
          <section class="drawer-section">
            <h4>Identity</h4>
            <dl class="detail-grid">
              <div><dt>Name</dt><dd>{{ selectedDisk.name }}</dd></div>
              <div><dt>Path</dt><dd>{{ selectedDisk.path }}</dd></div>
              <div><dt>Model</dt><dd>{{ selectedDisk.model || '-' }}</dd></div>
              <div><dt>Size</dt><dd>{{ formatBytes(selectedDisk.size) }}</dd></div>
            </dl>
          </section>

          <section class="drawer-section">
            <h4>Filesystem Relation</h4>
            <dl class="detail-grid">
              <div><dt>Filesystem</dt><dd>{{ selectedDisk.filesystem }}</dd></div>
              <div><dt>Pool</dt><dd>{{ selectedDisk.poolName }}</dd></div>
              <div><dt>Mount</dt><dd>{{ selectedDisk.mountpoint }}</dd></div>
              <div><dt>Partition</dt><dd>{{ selectedDisk.partitionPath || '-' }}</dd></div>
            </dl>
          </section>
        </div>
      </DetailDrawer>
    </section>
  `,
};
