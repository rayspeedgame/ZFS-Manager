import { computed, ref } from "vue";

import DetailDrawer from "../components/common/DetailDrawer.js";
import EmptyState from "../components/common/EmptyState.js";
import { formatBytes, formatDateTime } from "../lib/formatters.js";

export default {
  components: {
    DetailDrawer,
    EmptyState,
  },
  props: {
    state: { type: Object, required: true },
  },
  setup(props) {
    const selectedDataset = ref(null);
    const drawerOpen = ref(false);

    const rows = computed(() => props.state.snapshot.value?.data?.datasets || []);

    function openDataset(row) {
      selectedDataset.value = row;
      drawerOpen.value = true;
    }

    return {
      drawerOpen,
      openDataset,
      rows,
      selectedDataset,
      formatBytes,
      formatDateTime,
    };
  },
  template: `
    <section class="view-grid">
      <article class="surface-panel">
        <div class="section-header">
          <div>
            <h3>Dataset Inventory</h3>
            <p>Filesystem and volume inventory with inheritance-aware summaries.</p>
          </div>
        </div>

        <EmptyState
          v-if="!rows.length"
          title="No datasets discovered"
          description="The current snapshot did not report any datasets."
        />

        <div v-else class="table-shell">
          <table class="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Mountpoint</th>
                <th>Used</th>
                <th>Available</th>
                <th>Compression</th>
                <th>Source</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in rows" :key="row.name">
                <td>
                  <div class="tree-cell" :style="{ paddingLeft: (row.depth * 20) + 'px' }">
                    <strong>{{ row.name.split('/').slice(-1)[0] }}</strong>
                    <span class="subtle-text">{{ row.name }}</span>
                  </div>
                </td>
                <td>{{ row.type }}</td>
                <td>{{ row.mountpoint || '-' }}</td>
                <td>{{ formatBytes(row.used) }}</td>
                <td>{{ formatBytes(row.avail) }}</td>
                <td>{{ row.compression || '-' }}</td>
                <td>{{ row.sourceSummary }}</td>
                <td class="action-cell">
                  <button type="button" class="ghost-button" @click="openDataset(row)">View</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <DetailDrawer
        v-model="drawerOpen"
        title="Dataset Details"
        :description="selectedDataset?.name || ''"
      >
        <div v-if="selectedDataset" class="drawer-section-list">
          <section class="drawer-section">
            <h4>Overview</h4>
            <dl class="detail-grid">
              <div><dt>Type</dt><dd>{{ selectedDataset.type }}</dd></div>
              <div><dt>Mountpoint</dt><dd>{{ selectedDataset.mountpoint || '-' }}</dd></div>
              <div><dt>Used</dt><dd>{{ formatBytes(selectedDataset.used) }}</dd></div>
              <div><dt>Available</dt><dd>{{ formatBytes(selectedDataset.avail) }}</dd></div>
              <div><dt>Created</dt><dd>{{ formatDateTime(selectedDataset.creation * 1000) }}</dd></div>
              <div><dt>Readonly</dt><dd>{{ selectedDataset.readonly }}</dd></div>
            </dl>
          </section>

          <section class="drawer-section">
            <h4>Property Sources</h4>
            <dl class="detail-grid">
              <div v-for="(property, name) in selectedDataset.properties" :key="name">
                <dt>{{ name }}</dt>
                <dd>{{ property.value }} <span class="subtle-text">({{ property.source }})</span></dd>
              </div>
            </dl>
          </section>
        </div>
      </DetailDrawer>
    </section>
  `,
};
