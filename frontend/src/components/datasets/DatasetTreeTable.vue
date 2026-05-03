<script setup>
import { useI18n } from "vue-i18n";

import EmptyState from "../common/EmptyState.vue";
import { formatBytes } from "../../lib/formatters.js";

defineProps({
  rows: { type: Array, required: true },
  treeRows: { type: Array, required: true },
  showSnapshots: { type: Boolean, default: false },
});

const { t } = useI18n();
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
          <h3>{{ t("datasets.inventory") }}</h3>
          <p>{{ t("datasets.inventoryDescription") }}</p>
        </div>
      <label class="inline-checkbox">
        <input
          :checked="showSnapshots"
          type="checkbox"
          @change="emit('update:showSnapshots', $event.target.checked)"
        />
        <span>{{ t("datasets.showSnapshots") }}</span>
      </label>
    </div>

    <EmptyState
      v-if="!rows.length"
      :title="t('datasets.emptyTitle')"
      :description="t('datasets.emptyDescription')"
    />

    <div v-else class="table-shell">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t("datasets.columns.name") }}</th>
            <th>{{ t("datasets.columns.type") }}</th>
            <th>{{ t("datasets.columns.mountpoint") }}</th>
            <th>{{ t("datasets.columns.used") }}</th>
            <th>{{ t("datasets.columns.available") }}</th>
            <th>{{ t("datasets.columns.compression") }}</th>
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
                    :aria-label="row.expanded ? t('datasets.collapseDataset') : t('datasets.expandDataset')"
                    @click="emit('toggle-row', row.name)"
                  >
                    >
                  </button>
                  <span v-else class="dataset-name-toggle-placeholder"></span>
                  <span class="dataset-type-pill" :data-type="row.type">{{ row.typeLabel }}</span>
                  <div class="dataset-name-stack">
                    <div class="dataset-name-main">
                      <strong>{{ row.shortName }}</strong>
                      <span v-if="row.depth === 0" class="dataset-root-badge">{{ t("datasets.root") }}</span>
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
                    {{ t("common.new") }}
                  </button>
                  <button type="button" class="ghost-button" @click="emit('open-dataset', row)">{{ t("common.manage") }}</button>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </article>
</template>
