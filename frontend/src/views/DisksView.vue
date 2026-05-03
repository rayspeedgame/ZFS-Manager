<script setup>
import { computed, ref } from "vue";
import { useI18n } from "vue-i18n";

import DetailDrawer from "../components/common/DetailDrawer.vue";
import EmptyState from "../components/common/EmptyState.vue";
import { formatBytes } from "../lib/formatters.js";

const props = defineProps({
  state: { type: Object, required: true },
});

const { t } = useI18n();
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
</script>

<template>
  <section class="view-grid">
    <article class="surface-panel">
      <div class="section-header">
        <div>
          <h3>{{ t("disks.inventory") }}</h3>
          <p>{{ t("disks.inventoryDescription") }}</p>
        </div>
      </div>

      <EmptyState
        v-if="!rows.length"
        :title="t('disks.emptyTitle')"
        :description="t('disks.emptyDescription')"
      />

      <div v-else class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t("disks.columns.device") }}</th>
              <th>{{ t("disks.columns.model") }}</th>
              <th>{{ t("disks.columns.size") }}</th>
              <th>{{ t("disks.columns.filesystem") }}</th>
              <th>{{ t("disks.columns.pool") }}</th>
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
                      >
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
                <td>{{ row.filesystemDisplay || row.filesystem }}</td>
                <td>{{ row.poolName }}</td>
                <td class="action-cell">
                  <button type="button" class="ghost-button" @click="openDisk(row)">{{ t("common.view") }}</button>
                </td>
              </tr>
              <tr v-if="isExpanded(row)" class="partition-row">
                <td colspan="6">
                  <div class="partition-shell">
                    <div class="partition-header">
                      <span>{{ t("disks.columns.name") }}</span>
                      <span>{{ t("disks.columns.path") }}</span>
                      <span>{{ t("disks.columns.type") }}</span>
                      <span>{{ t("disks.columns.size") }}</span>
                      <span>{{ t("disks.columns.filesystem") }}</span>
                      <span>{{ t("disks.columns.pool") }}</span>
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
                      <span>{{ partition.filesystemDisplay || partition.filesystem }}</span>
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
      :title="t('disks.detailTitle')"
      :description="selectedDisk?.path || ''"
    >
      <div v-if="selectedDisk" class="drawer-section-list">
        <section class="drawer-section">
          <h4>{{ t("disks.identity") }}</h4>
          <dl class="detail-grid">
            <div><dt>{{ t("disks.columns.name") }}</dt><dd>{{ selectedDisk.name }}</dd></div>
            <div><dt>{{ t("disks.columns.path") }}</dt><dd>{{ selectedDisk.path }}</dd></div>
            <div><dt>{{ t("disks.columns.model") }}</dt><dd>{{ selectedDisk.model || "-" }}</dd></div>
            <div><dt>{{ t("disks.columns.size") }}</dt><dd>{{ formatBytes(selectedDisk.size) }}</dd></div>
          </dl>
        </section>

        <section class="drawer-section">
          <h4>{{ t("disks.filesystemRelation") }}</h4>
          <dl class="detail-grid">
            <div><dt>{{ t("disks.columns.filesystem") }}</dt><dd>{{ selectedDisk.filesystemDisplay || selectedDisk.filesystem }}</dd></div>
            <div><dt>{{ t("disks.columns.pool") }}</dt><dd>{{ selectedDisk.poolName }}</dd></div>
            <div><dt>{{ t("disks.columns.partition") }}</dt><dd>{{ selectedDisk.partitionPath || "-" }}</dd></div>
          </dl>
        </section>
      </div>
    </DetailDrawer>
  </section>
</template>
