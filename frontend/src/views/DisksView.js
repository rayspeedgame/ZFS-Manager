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
    const expandedRows = ref({});

    const rows = computed(() => props.state.snapshot.value?.data?.disks || []);

    function openDisk(row) {
      selectedDisk.value = row;
      drawerOpen.value = true;
    }

    function toggleRow(row) {
      const key = row.path || row.name;
      expandedRows.value = {
        ...expandedRows.value,
        [key]: !expandedRows.value[key],
      };
    }

    function isExpanded(row) {
      return Boolean(expandedRows.value[row.path || row.name]);
    }

    return {
      drawerOpen,
      expandedRows,
      isExpanded,
      openDisk,
      rows,
      selectedDisk,
      toggleRow,
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
                <th></th>
              </tr>
            </thead>
            <tbody>
              <template v-for="row in rows" :key="row.path || row.name">
                <tr>
                  <td>
                    <div class="disk-cell">
                      <button
                        v-if="row.partitions?.length"
                        type="button"
                        class="row-toggle"
                        :data-expanded="isExpanded(row)"
                        @click="toggleRow(row)"
                      >
                        ▸
                      </button>
                      <span v-else class="row-toggle-placeholder"></span>
                      <div>
                        <strong>{{ row.name }}</strong>
                        <div class="subtle-text">{{ row.path }}</div>
                      </div>
                    </div>
                  </td>
                  <td>{{ row.model || "-" }}</td>
                  <td>{{ formatBytes(row.size) }}</td>
                  <td>{{ row.filesystem }}</td>
                  <td>{{ row.poolName }}</td>
                  <td class="action-cell">
                    <button type="button" class="ghost-button" @click="openDisk(row)">View</button>
                  </td>
                </tr>
                <tr v-if="isExpanded(row)" class="partition-row">
                  <td colspan="6">
                    <div class="partition-shell">
                      <div class="partition-header">
                        <span>Name</span>
                        <span>Path</span>
                        <span>Type</span>
                        <span>Size</span>
                        <span>Filesystem</span>
                        <span>Pool</span>
                      </div>
                      <div
                        v-for="partition in row.partitions"
                        :key="partition.path || partition.name"
                        class="partition-item"
                      >
                        <strong>{{ partition.name }}</strong>
                        <span>{{ partition.path }}</span>
                        <span>{{ partition.type }}</span>
                        <span>{{ formatBytes(partition.size) }}</span>
                        <span>{{ partition.filesystem }}</span>
                        <span>{{ partition.poolName }}</span>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
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
              <div><dt>Partition</dt><dd>{{ selectedDisk.partitionPath || '-' }}</dd></div>
            </dl>
          </section>
        </div>
      </DetailDrawer>
    </section>
  `,
};
