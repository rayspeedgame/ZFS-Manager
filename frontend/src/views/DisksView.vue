<script setup>
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

import DetailDrawer from "../components/common/DetailDrawer.vue";
import EmptyState from "../components/common/EmptyState.vue";
import { formatBytes } from "../lib/formatters.js";
import { useAppState } from "../store/state.js";

const props = defineProps({
  state: { type: Object, required: true },
});

const { t } = useI18n();
const { refreshStateOnce, updateDiskLabel } = useAppState();
const selectedDisk = ref(null);
const drawerOpen = ref(false);
const expandedRows = ref({});
const labelDraft = ref("");
const labelSubmitting = ref(false);
const labelSummary = ref("");
const labelError = ref("");

const rows = computed(() => props.state.snapshot.value?.data?.disks || []);

watch(
  () => props.state.snapshot.value?.meta?.last_updated,
  () => {
    if (!selectedDisk.value?.diskKey) {
      return;
    }
    const updated = rows.value.find((row) => row.diskKey === selectedDisk.value.diskKey);
    if (updated) {
      selectedDisk.value = updated;
      labelDraft.value = updated.customName || "";
    }
  }
);

function openDisk(row) {
  selectedDisk.value = row;
  labelDraft.value = row.customName || "";
  labelSummary.value = "";
  labelError.value = "";
  drawerOpen.value = true;
}

function toggleRow(row) {
  const key = row.diskKey || row.path || row.name;
  expandedRows.value = {
    ...expandedRows.value,
    [key]: !expandedRows.value[key],
  };
}

function isExpanded(row) {
  return Boolean(expandedRows.value[row.diskKey || row.path || row.name]);
}

async function saveLabel() {
  if (!selectedDisk.value?.diskKey || labelSubmitting.value) {
    return;
  }

  labelSubmitting.value = true;
  labelSummary.value = "";
  labelError.value = "";

  try {
    const response = await updateDiskLabel(selectedDisk.value.diskKey, labelDraft.value);
    labelSummary.value = response.message || "";
    await refreshStateOnce();
    const updated = rows.value.find((row) => row.diskKey === selectedDisk.value.diskKey);
    if (updated) {
      selectedDisk.value = updated;
      labelDraft.value = updated.customName || "";
    }
  } catch (error) {
    labelError.value = error instanceof Error ? error.message : String(error);
  } finally {
    labelSubmitting.value = false;
  }
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
            <template v-for="row in rows" :key="row.diskKey || row.path || row.name">
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
                      <strong>{{ row.displayName || row.name }}</strong>
                      <div class="subtle-text">{{ row.kernelPath || row.path }}</div>
                      <div v-if="row.byIdPath" class="subtle-text">{{ row.byIdPath }}</div>
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
      :description="selectedDisk?.displayName || selectedDisk?.kernelPath || ''"
    >
      <div v-if="selectedDisk" class="drawer-section-list">
        <section class="drawer-section">
          <div class="drawer-section-header">
            <div>
              <h4>{{ t("disks.identity") }}</h4>
              <p class="subtle-text">{{ t("disks.labelDescription") }}</p>
            </div>
            <button type="button" class="primary-button" :disabled="labelSubmitting" @click="saveLabel">
              {{ labelSubmitting ? t("common.saving") : t("common.save") }}
            </button>
          </div>
          <label class="form-field">
            <span>{{ t("disks.customName") }}</span>
            <input v-model="labelDraft" type="text" class="property-field" :placeholder="selectedDisk.kernelPath || selectedDisk.path" />
          </label>
          <p v-if="labelSummary" class="notice-text">{{ labelSummary }}</p>
          <p v-if="labelError" class="error-text">{{ labelError }}</p>
          <dl class="detail-grid">
            <div><dt>{{ t("disks.columns.name") }}</dt><dd>{{ selectedDisk.displayName || selectedDisk.name }}</dd></div>
            <div><dt>{{ t("disks.columns.path") }}</dt><dd>{{ selectedDisk.kernelPath || selectedDisk.path }}</dd></div>
            <div><dt>{{ t("disks.byIdPath") }}</dt><dd>{{ selectedDisk.byIdPath || "-" }}</dd></div>
            <div><dt>{{ t("disks.columns.model") }}</dt><dd>{{ selectedDisk.model || "-" }}</dd></div>
            <div><dt>{{ t("disks.columns.size") }}</dt><dd>{{ formatBytes(selectedDisk.size) }}</dd></div>
            <div><dt>{{ t("disks.diskId") }}</dt><dd>{{ selectedDisk.diskId }}</dd></div>
          </dl>
        </section>

        <section class="drawer-section">
          <h4>{{ t("disks.filesystemRelation") }}</h4>
          <dl class="detail-grid">
            <div><dt>{{ t("disks.columns.filesystem") }}</dt><dd>{{ selectedDisk.filesystemDisplay || selectedDisk.filesystem }}</dd></div>
            <div><dt>{{ t("disks.columns.pool") }}</dt><dd>{{ selectedDisk.poolName }}</dd></div>
            <div><dt>{{ t("disks.columns.partition") }}</dt><dd>{{ selectedDisk.partitionPath || "-" }}</dd></div>
            <div><dt>{{ t("disks.commandPath") }}</dt><dd>{{ selectedDisk.commandPath || selectedDisk.kernelPath || "-" }}</dd></div>
          </dl>
        </section>
      </div>
    </DetailDrawer>
  </section>
</template>
