<script setup>
import EmptyState from "../common/EmptyState.vue";
import { formatBytes } from "../../lib/formatters.js";

defineProps({
  rows: { type: Array, required: true },
  treeRows: { type: Array, required: true },
  showSnapshots: { type: Boolean, default: false },
});

const emit = defineEmits([
  "update:showSnapshots",
  "toggle-row",
  "open-create",
  "open-dataset",
]);
</script>

<template>
  <article class="surface-panel">
    <div class="section-header">
      <div>
        <h3>Dataset Inventory</h3>
        <p>Filesystem and volume inventory with manage and create workflows.</p>
      </div>
      <label class="inline-checkbox">
        <input
          :checked="showSnapshots"
          type="checkbox"
          @change="emit('update:showSnapshots', $event.target.checked)"
        />
        <span>Show snapshots</span>
      </label>
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
            <th></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="row in treeRows" :key="row.key">
            <tr v-if="row.entryType === 'group'" class="dataset-group-row">
              <td colspan="7">
                <div class="dataset-group-header">
                  <strong>{{ row.label }}</strong>
                  <span class="subtle-text">{{ row.meta }}</span>
                </div>
              </td>
            </tr>
            <tr v-else>
              <td>
                <div class="dataset-name-cell" :style="{ paddingLeft: row.depth * 18 + 'px' }">
                  <button
                    v-if="row.hasChildren"
                    type="button"
                    class="dataset-name-toggle"
                    :data-expanded="row.expanded ? 'true' : 'false'"
                    :aria-label="row.expanded ? 'Collapse dataset' : 'Expand dataset'"
                    @click="emit('toggle-row', row.name)"
                  >
                    >
                  </button>
                  <span v-else class="dataset-name-toggle-placeholder"></span>
                  <span class="dataset-type-pill" :data-type="row.type">{{ row.typeLabel }}</span>
                  <div class="dataset-name-stack">
                    <div class="dataset-name-main">
                      <strong>{{ row.shortName }}</strong>
                      <span v-if="row.depth === 0" class="dataset-root-badge">root</span>
                    </div>
                    <span class="subtle-text">{{ row.name }}</span>
                  </div>
                </div>
              </td>
              <td>{{ row.type }}</td>
              <td>{{ row.mountpoint || "-" }}</td>
              <td>{{ formatBytes(row.used) }}</td>
              <td>{{ formatBytes(row.avail) }}</td>
              <td>{{ row.compressionDisplay }}</td>
              <td class="action-cell">
                <div class="inline-button-row">
                  <button
                    v-if="row.type === 'filesystem'"
                    type="button"
                    class="ghost-button"
                    @click="emit('open-create', row)"
                  >
                    New
                  </button>
                  <button type="button" class="ghost-button" @click="emit('open-dataset', row)">Manage</button>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </article>
</template>
