<script setup>
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

import ConfirmDialog from "../components/common/ConfirmDialog.vue";
import DetailDrawer from "../components/common/DetailDrawer.vue";
import EmptyState from "../components/common/EmptyState.vue";
import { formatBytes } from "../lib/formatters.js";
import { useAppState } from "../store/state.js";

const props = defineProps({
  state: { type: Object, required: true },
});

const { t } = useI18n();
const { refreshStateOnce, updateDiskLabel, getDiskSmartData, refreshDiskSmartData } = useAppState();
const selectedDisk = ref(null);
const drawerOpen = ref(false);
const smartDialogOpen = ref(false);
const expandedRows = ref({});
const labelDraft = ref("");
const labelSubmitting = ref(false);
const labelSummary = ref("");
const labelError = ref("");

// SMART reactive state
const smartData = ref(null);
const smartLoading = ref(false);
const smartRefreshing = ref(false);
const smartError = ref("");

const rows = computed(() => props.state.snapshot.value?.data?.disks || []);

const smartOverview = computed(() => props.state.snapshot.value?.data?.smart_overview || null);

function getDiskSmartHealth(row) {
  if (!smartOverview.value?.devices) return null;
  // Try kernelPath first, then path, then byIdPath
  const key = row.kernelPath || row.path || row.diskPath || null;
  if (!key) return null;
  return smartOverview.value.devices[key] || null;
}

function smartStatusLabel(health) {
  if (!health) return "";
  if (!health.raw_data_available) return "N/A";
  if (health.smart_status_passed === true) return "✓ PASS";
  if (health.smart_status_passed === false) return "✗ FAIL";
  return "?";
}

function smartStatusClass(health) {
  if (!health?.raw_data_available) return "";
  if (health.smart_status_passed === true) return "health-online";
  if (health.smart_status_passed === false) return "health-warning";
  return "";
}

function formatSmartTemp(health) {
  if (!health?.raw_data_available || health.temperature == null) return null;
  return `${health.temperature}°C`;
}

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
  loadSmartData(row);
}

async function loadSmartData(disk) {
  if (!disk?.diskKey && !disk?.kernelPath && !disk?.path) {
    return;
  }
  const key = disk.diskKey || disk.kernelPath || disk.path;
  smartLoading.value = true;
  smartData.value = null;
  smartError.value = "";
  try {
    const data = await getDiskSmartData(key);
    smartData.value = data;
  } catch (error) {
    smartError.value = error instanceof Error ? error.message : String(error);
  } finally {
    smartLoading.value = false;
  }
}

async function refreshSmart() {
  if (!selectedDisk.value?.diskKey && !selectedDisk.value?.kernelPath) {
    return;
  }
  const key = selectedDisk.value.diskKey || selectedDisk.value.kernelPath || selectedDisk.value.path;
  smartRefreshing.value = true;
  smartError.value = "";
  try {
    await refreshDiskSmartData(key);
    const data = await getDiskSmartData(key);
    smartData.value = data;
  } catch (error) {
    smartError.value = error instanceof Error ? error.message : String(error);
  } finally {
    smartRefreshing.value = false;
  }
}

const smartHealthClass = computed(() => {
  if (!smartData.value?.raw_data_available) return "health-unknown";
  if (smartData.value.smart_status_passed === true) return "health-online";
  if (smartData.value.smart_status_passed === false) return "health-warning";
  return "health-unknown";
});

const smartHealthLabel = computed(() => {
  if (!smartData.value?.raw_data_available) return t("disks.smart.unknown");
  if (smartData.value.smart_status_passed === true) return t("disks.smart.passed");
  if (smartData.value.smart_status_passed === false) return t("disks.smart.failed");
  return t("disks.smart.unsupported");
});

function formatPowerOnHours(hours) {
  if (hours == null) return "-";
  const h = Number(hours);
  const d = Math.floor(h / 24);
  const remaining = h % 24;
  if (d > 0) return `${d}d ${remaining}h`;
  return `${h}h`;
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
              <th>{{ t("disks.smart.health") }}</th>
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
                <td>
                  <template v-if="getDiskSmartHealth(row)">
                    <div class="inline-health-badge" :class="smartStatusClass(getDiskSmartHealth(row))">
                      {{ smartStatusLabel(getDiskSmartHealth(row)) }}
                    </div>
                    <div v-if="formatSmartTemp(getDiskSmartHealth(row))" class="inline-health-temp">
                      {{ formatSmartTemp(getDiskSmartHealth(row)) }}
                    </div>
                  </template>
                  <span v-else class="subtle-text">-</span>
                </td>
                <td>{{ row.filesystemDisplay || row.filesystem }}</td>
                <td>{{ row.poolName }}</td>
                <td class="action-cell">
                  <button type="button" class="ghost-button" @click="openDisk(row)">{{ t("common.view") }}</button>
                </td>
              </tr>
              <tr v-if="isExpanded(row)" class="partition-row">
                <td colspan="7">
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

        <!-- ── SMART Health (compact) ── -->
        <section class="drawer-section">
          <div class="drawer-section-header">
            <div>
              <h4>{{ t("disks.smart.title") }}</h4>
              <p class="subtle-text">{{ t("disks.smart.refreshHint") }}</p>
            </div>
            <div class="inline-button-row">
              <button
                type="button"
                class="ghost-button"
                :disabled="smartRefreshing || !selectedDisk"
                @click="refreshSmart"
              >
                {{ smartRefreshing ? t("disks.smart.refreshing") : t("disks.smart.refresh") }}
              </button>
              <button
                type="button"
                class="primary-button"
                :disabled="!smartData?.raw_data_available"
                @click="smartDialogOpen = true"
              >
                {{ t("disks.smart.viewDetails") }}
              </button>
            </div>
          </div>

          <!-- Loading / Error / No data states -->
          <div v-if="smartLoading" class="subtle-text">{{ t("common.waitingForState") }}</div>
          <p v-else-if="smartError" class="error-text">{{ smartError }}</p>
          <p v-else-if="!smartData" class="subtle-text">{{ t("disks.smart.noData") }}</p>

          <!-- Compact health badge only -->
          <template v-else-if="smartData.raw_data_available">
            <span class="smart-health-badge" :class="smartHealthClass">{{ smartHealthLabel }}</span>
            <p v-if="smartData.attributes?.some(a => a.when_failed)" class="error-text" style="margin-top: 6px;">
              {{ t("disks.smart.failingNow") }}
            </p>
          </template>

          <!-- Unsupported -->
          <p v-else-if="smartData?.error?.includes('smartctl')" class="subtle-text">{{ t("disks.smart.notInstalled") }}</p>
          <p v-else class="subtle-text">{{ t("disks.smart.noData") }}</p>
        </section>
      </div>
    </DetailDrawer>

    <!-- ── Full SMART details dialog ── -->
    <ConfirmDialog
      v-model="smartDialogOpen"
      :title="t('disks.smart.title') + ' - ' + (selectedDisk?.displayName || selectedDisk?.kernelPath || '')"
      :description="t('disks.smart.lastCollected') + ': ' + (smartData?.collected_at ? new Date(smartData.collected_at).toLocaleString() : '-')"
      result-mode
      :close-text="t('common.close')"
    >
      <!-- Loading -->
      <div v-if="smartLoading" class="empty-state">
        <strong>{{ t("common.waitingForState") }}</strong>
      </div>

      <!-- Error state -->
      <p v-else-if="smartError" class="error-text">{{ smartError }}</p>

      <!-- No data -->
      <p v-else-if="!smartData" class="subtle-text">{{ t("disks.smart.noData") }}</p>

      <template v-else-if="smartData.raw_data_available">
        <!-- Health + metrics row -->
        <div class="smart-health-row">
          <span class="smart-health-badge" :class="smartHealthClass">{{ smartHealthLabel }}</span>
          <span v-if="smartData.temperature != null" class="smart-metric"><strong>{{ t("disks.smart.temperature") }}:</strong> {{ smartData.temperature }}°C</span>
          <span v-if="smartData.power_on_hours != null" class="smart-metric"><strong>{{ t("disks.smart.powerOnHours") }}:</strong> {{ formatPowerOnHours(smartData.power_on_hours) }}</span>
          <span v-if="smartData.protocol" class="smart-metric"><strong>{{ t("disks.smart.protocol") }}:</strong> {{ smartData.protocol.toUpperCase() }}</span>
        </div>

        <!-- Serial / FW -->
        <dl class="detail-grid" style="margin-top: 8px;">
          <div v-if="smartData.model_name"><dt>{{ t("disks.columns.model") }}</dt><dd>{{ smartData.model_name }}</dd></div>
          <div v-if="smartData.serial_number"><dt>{{ t("disks.serial") }}</dt><dd>{{ smartData.serial_number }}</dd></div>
          <div v-if="smartData.firmware_version"><dt>{{ t("disks.firmware") }}</dt><dd>{{ smartData.firmware_version }}</dd></div>
        </dl>

        <!-- Attribute table -->
        <div v-if="smartData.attributes?.length" class="smart-attr-section">
          <h5>{{ t("disks.smart.attributes") }}</h5>
          <div class="table-shell smart-table-shell-dialog">
            <table class="data-table smart-attr-table">
              <thead>
                <tr>
                  <th>{{ t("disks.smart.id") }}</th>
                  <th>{{ t("disks.smart.name") }}</th>
                  <th>{{ t("disks.smart.value") }}</th>
                  <th>{{ t("disks.smart.worst") }}</th>
                  <th>{{ t("disks.smart.threshold") }}</th>
                  <th>{{ t("disks.smart.raw") }}</th>
                  <th>{{ t("disks.smart.whenFailed") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="attr in smartData.attributes"
                  :key="attr.id ?? attr.name"
                  :class="{ 'smart-attr-warning': attr.when_failed }"
                >
                  <td>{{ attr.id ?? "-" }}</td>
                  <td><strong>{{ attr.name }}</strong></td>
                  <td>{{ attr.value ?? "-" }}</td>
                  <td>{{ attr.worst ?? "-" }}</td>
                  <td>{{ attr.threshold ?? "-" }}</td>
                  <td class="smart-raw-cell">{{ attr.raw ?? "-" }}</td>
                  <td>
                    <span v-if="attr.when_failed === 'FAILING_NOW'" class="health-badge health-badge-failing">{{ t("disks.smart.failingNow") }}</span>
                    <span v-else-if="attr.when_failed === 'In_the_past'" class="health-badge health-badge-past">{{ t("disks.smart.failedInPast") }}</span>
                    <span v-else class="subtle-text">{{ t("disks.smart.healthyAttr") }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <p v-if="smartData.error" class="notice-text" style="margin-top: 8px;">{{ smartData.error }}</p>
      </template>

      <!-- Unsupported -->
      <p v-else-if="smartData?.error?.includes('smartctl')" class="subtle-text">{{ t("disks.smart.notInstalled") }}</p>
      <p v-else class="subtle-text">{{ t("disks.smart.noData") }}</p>
    </ConfirmDialog>
  </section>
</template>
