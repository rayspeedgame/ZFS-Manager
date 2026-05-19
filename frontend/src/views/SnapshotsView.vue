<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

import ConfirmDialog from "../components/common/ConfirmDialog.vue";
import DetailDrawer from "../components/common/DetailDrawer.vue";
import EmptyState from "../components/common/EmptyState.vue";
import CommandResultList from "../components/common/CommandResultList.vue";
import CommandLogPanel from "../components/common/CommandLogPanel.vue";
import { formatBytes, formatDateTime } from "../lib/formatters.js";
import { useAppState } from "../store/state.js";

const { t } = useI18n();
const {
  destroySnapshot,
  getSnapshot,
  getSnapshotFilters,
  getSnapshots,
  rollbackSnapshot,
  refreshStateOnce,
} = useAppState();

const loading = ref(false);
const filtersLoading = ref(false);
const deleting = ref(false);
const rollingBack = ref(false);
const error = ref("");
const items = ref([]);
const total = ref(0);
const page = ref(1);
const pageSize = ref(25);
const totalPages = ref(1);
const selectedSnapshotName = ref("");
const selectedSnapshot = ref(null);
const drawerOpen = ref(false);
const deleteDialogOpen = ref(false);
const deleteDialogPhase = ref("confirm");
const deleteDialogSummary = ref("");
const deleteDialogError = ref("");
const deleteDialogResult = ref(null);
const rollbackDialogOpen = ref(false);
const rollbackDialogPhase = ref("confirm");
const rollbackDialogSummary = ref("");
const rollbackDialogError = ref("");
const rollbackDialogResult = ref(null);
const rollbackMode = ref("safe");
const filters = ref({
  pools: [],
  datasets: [],
  types: [],
});
const query = ref({
  search: "",
  pool: "",
  dataset: "",
  snapshotType: "",
  sortBy: "created_at",
  sortOrder: "desc",
});

let searchTimer = null;

const pageItemCount = computed(() => items.value.length);
const poolCount = computed(() => filters.value.pools.length);
const datasetCount = computed(() => filters.value.datasets.length);
const hasActiveFilters = computed(() =>
  Boolean(query.value.search || query.value.pool || query.value.dataset || query.value.snapshotType)
);

watch(items, (nextItems) => {
  if (!nextItems.length) {
    selectedSnapshotName.value = "";
    selectedSnapshot.value = null;
    drawerOpen.value = false;
    return;
  }
  if (selectedSnapshotName.value && nextItems.some((item) => item.full_name === selectedSnapshotName.value)) {
    return;
  }
  selectedSnapshotName.value = nextItems[0].full_name;
}, { immediate: true });

watch(selectedSnapshotName, async (snapshotName) => {
  if (!snapshotName) {
    selectedSnapshot.value = null;
    return;
  }
  try {
    const payload = await getSnapshot(snapshotName);
    selectedSnapshot.value = payload?.snapshot || null;
  } catch (nextError) {
    deleteDialogError.value = nextError instanceof Error ? nextError.message : String(nextError);
  }
}, { immediate: true });

watch(
  () => query.value.search,
  () => {
    if (searchTimer) {
      window.clearTimeout(searchTimer);
    }
    searchTimer = window.setTimeout(() => {
      refreshSnapshots({ page: 1 }).catch(() => {
        // Keep the last visible list when debounce refresh fails.
      });
    }, 300);
  }
);

onMounted(async () => {
  await Promise.all([loadFilters(), refreshSnapshots()]);
});

onBeforeUnmount(() => {
  if (searchTimer) {
    window.clearTimeout(searchTimer);
    searchTimer = null;
  }
});

async function loadFilters() {
  filtersLoading.value = true;
  try {
    const payload = await getSnapshotFilters();
    filters.value = {
      pools: Array.isArray(payload?.pools) ? payload.pools : [],
      datasets: Array.isArray(payload?.datasets) ? payload.datasets : [],
      types: Array.isArray(payload?.types) ? payload.types : [],
    };
  } catch (nextError) {
    error.value = nextError instanceof Error ? nextError.message : String(nextError);
  } finally {
    filtersLoading.value = false;
  }
}

async function refreshSnapshots(options = {}) {
  loading.value = true;
  error.value = "";
  try {
    if (options.page !== undefined) {
      page.value = Math.max(1, Number(options.page) || 1);
    }
    if (options.pageSize !== undefined) {
      pageSize.value = Math.max(1, Number(options.pageSize) || 25);
    }
    const payload = await getSnapshots({
      page: page.value,
      pageSize: pageSize.value,
      search: query.value.search,
      pool: query.value.pool,
      dataset: query.value.dataset,
      snapshotType: query.value.snapshotType,
      sortBy: query.value.sortBy,
      sortOrder: query.value.sortOrder,
    });
    items.value = Array.isArray(payload?.items) ? payload.items : [];
    total.value = Number(payload?.total ?? items.value.length);
    page.value = Number(payload?.page ?? page.value);
    pageSize.value = Number(payload?.page_size ?? pageSize.value);
    totalPages.value = Number(payload?.total_pages ?? 1);
    if (selectedSnapshotName.value) {
      const matched = items.value.find((item) => item.full_name === selectedSnapshotName.value);
      if (matched) {
        selectedSnapshot.value = matched;
      }
    }
  } catch (nextError) {
    error.value = nextError instanceof Error ? nextError.message : String(nextError);
  } finally {
    loading.value = false;
  }
}

function applyFilterChange() {
  refreshSnapshots({ page: 1 }).catch(() => {
    // The page already renders the error state.
  });
}

function clearFilters() {
  query.value = {
    search: "",
    pool: "",
    dataset: "",
    snapshotType: "",
    sortBy: "created_at",
    sortOrder: "desc",
  };
  refreshSnapshots({ page: 1 }).catch(() => {
    // The page already renders the error state.
  });
}

function openDetails(snapshot) {
  selectedSnapshotName.value = snapshot.full_name;
  selectedSnapshot.value = snapshot;
  drawerOpen.value = true;
}

function openDeleteDialog(snapshot) {
  selectedSnapshotName.value = snapshot.full_name;
  selectedSnapshot.value = snapshot;
  deleteDialogPhase.value = "confirm";
  deleteDialogSummary.value = "";
  deleteDialogError.value = "";
  deleteDialogResult.value = null;
  deleteDialogOpen.value = true;
}

function openRollbackDialog(snapshot) {
  selectedSnapshotName.value = snapshot.full_name;
  selectedSnapshot.value = snapshot;
  rollbackDialogPhase.value = "confirm";
  rollbackDialogSummary.value = "";
  rollbackDialogError.value = "";
  rollbackDialogResult.value = null;
  rollbackMode.value = "safe";
  rollbackDialogOpen.value = true;
}

async function confirmDeleteSnapshot() {
  if (!selectedSnapshot.value?.full_name || deleting.value) {
    return;
  }

  deleting.value = true;
  deleteDialogPhase.value = "submitting";
  deleteDialogSummary.value = "";
  deleteDialogError.value = "";
  deleteDialogResult.value = null;

  try {
    const payload = await destroySnapshot(selectedSnapshot.value.full_name);
    deleteDialogResult.value = payload || null;
    await refreshStateOnce();
    await Promise.all([loadFilters(), refreshSnapshots()]);
    deleteDialogSummary.value = payload?.refreshed
      ? t("snapshots.summary.deleteSubmittedAndRefreshed")
      : t("snapshots.summary.deleteSubmittedRefreshFailed");
    if (payload?.refresh_error) {
      deleteDialogError.value = payload.refresh_error;
    }
    deleteDialogPhase.value = "result";
    drawerOpen.value = false;
  } catch (nextError) {
    deleteDialogPhase.value = "result";
    deleteDialogError.value = nextError instanceof Error ? nextError.message : String(nextError);
  } finally {
    deleting.value = false;
  }
}

async function confirmRollbackSnapshot() {
  if (!selectedSnapshot.value?.full_name || rollingBack.value) {
    return;
  }

  rollingBack.value = true;
  rollbackDialogPhase.value = "submitting";
  rollbackDialogSummary.value = "";
  rollbackDialogError.value = "";
  rollbackDialogResult.value = null;

  try {
    const payload = await rollbackSnapshot(selectedSnapshot.value.full_name, {
      mode: rollbackMode.value,
    });
    rollbackDialogResult.value = payload || null;
    await refreshStateOnce();
    await Promise.all([loadFilters(), refreshSnapshots()]);
    rollbackDialogSummary.value = payload?.refreshed
      ? t("snapshots.summary.rollbackSubmittedAndRefreshed")
      : t("snapshots.summary.rollbackSubmittedRefreshFailed");
    if (payload?.refresh_error) {
      rollbackDialogError.value = payload.refresh_error;
    }
    rollbackDialogPhase.value = "result";
    drawerOpen.value = false;
  } catch (nextError) {
    rollbackDialogPhase.value = "result";
    rollbackDialogError.value = nextError instanceof Error ? nextError.message : String(nextError);
  } finally {
    rollingBack.value = false;
  }
}

function changePage(nextPage) {
  refreshSnapshots({ page: nextPage }).catch(() => {
    // The page already renders the error state.
  });
}

function changePageSize(event) {
  refreshSnapshots({ page: 1, pageSize: Number(event.target.value) || 25 }).catch(() => {
    // The page already renders the error state.
  });
}

function changeSortDirection() {
  query.value.sortOrder = query.value.sortOrder === "asc" ? "desc" : "asc";
  applyFilterChange();
}

function buildDeleteLogLines(result, label) {
  if (!result) {
    return [];
  }
  return [
    {
      key: `snapshot-delete:${label}`,
      label,
      success: result.success,
      lines: [
        `$ ${result.command || "N/A"}`,
        result.exit_status !== null && result.exit_status !== undefined ? `exit_status: ${result.exit_status}` : null,
        result.stdout ? `stdout: ${result.stdout}` : null,
        result.stderr ? `stderr: ${result.stderr}` : null,
        !result.stdout && !result.stderr ? result.message : null,
      ].filter(Boolean),
    },
  ];
}

function buildRollbackLogLines(result, label) {
  if (!result) {
    return [];
  }
  return [
    {
      key: `snapshot-rollback:${label}`,
      label,
      success: result.success,
      lines: [
        `$ ${result.command || "N/A"}`,
        result.exit_status !== null && result.exit_status !== undefined ? `exit_status: ${result.exit_status}` : null,
        result.stdout ? `stdout: ${result.stdout}` : null,
        result.stderr ? `stderr: ${result.stderr}` : null,
        !result.stdout && !result.stderr ? result.message : null,
      ].filter(Boolean),
    },
  ];
}

function rollbackModeLabel(mode) {
  return t(`snapshots.rollbackModes.${mode}.label`);
}

function rollbackModeDescription(mode) {
  return t(`snapshots.rollbackModes.${mode}.description`);
}

function rollbackModeWarning(mode) {
  return t(`snapshots.rollbackModes.${mode}.warning`);
}
</script>

<template>
  <section class="view-grid">
    <div class="summary-grid">
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("snapshots.summary.total") }}</span>
        <strong class="summary-value">{{ total }}</strong>
        <span class="summary-meta">{{ t("snapshots.summary.totalDescription") }}</span>
      </article>
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("snapshots.summary.currentPage") }}</span>
        <strong class="summary-value">{{ pageItemCount }}</strong>
        <span class="summary-meta">{{ t("snapshots.summary.currentPageDescription") }}</span>
      </article>
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("snapshots.summary.pools") }}</span>
        <strong class="summary-value">{{ poolCount }}</strong>
        <span class="summary-meta">{{ t("snapshots.summary.poolsDescription") }}</span>
      </article>
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("snapshots.summary.datasets") }}</span>
        <strong class="summary-value">{{ datasetCount }}</strong>
        <span class="summary-meta">{{ t("snapshots.summary.datasetsDescription") }}</span>
      </article>
    </div>

    <div v-if="error" class="surface-panel">
      <p class="error-text">{{ error }}</p>
    </div>

    <article class="surface-panel">
      <div class="section-header">
        <div>
          <h3>{{ t("snapshots.listTitle") }}</h3>
          <p>{{ t("snapshots.listDescription") }}</p>
        </div>
        <div class="inline-action-controls">
          <button type="button" class="ghost-button" :disabled="loading || filtersLoading" @click="loadFilters">
            {{ filtersLoading ? t("snapshots.refreshing") : t("snapshots.refreshFilters") }}
          </button>
          <button type="button" class="ghost-button" :disabled="loading" @click="refreshSnapshots()">
            {{ loading ? t("snapshots.refreshing") : t("snapshots.refresh") }}
          </button>
        </div>
      </div>

      <div class="schedule-form-grid">
        <label class="form-field">
          <span>{{ t("snapshots.filters.search") }}</span>
          <input v-model="query.search" class="property-field" type="text" :placeholder="t('snapshots.filters.searchPlaceholder')" />
        </label>

        <label class="form-field">
          <span>{{ t("snapshots.filters.pool") }}</span>
          <select v-model="query.pool" class="property-field" @change="applyFilterChange">
            <option value="">{{ t("snapshots.filters.allPools") }}</option>
            <option v-for="poolName in filters.pools" :key="poolName" :value="poolName">{{ poolName }}</option>
          </select>
        </label>

        <label class="form-field">
          <span>{{ t("snapshots.filters.dataset") }}</span>
          <select v-model="query.dataset" class="property-field" @change="applyFilterChange">
            <option value="">{{ t("snapshots.filters.allDatasets") }}</option>
            <option v-for="datasetName in filters.datasets" :key="datasetName" :value="datasetName">{{ datasetName }}</option>
          </select>
        </label>

        <label class="form-field">
          <span>{{ t("snapshots.filters.type") }}</span>
          <select v-model="query.snapshotType" class="property-field" @change="applyFilterChange">
            <option value="">{{ t("snapshots.filters.allTypes") }}</option>
            <option v-for="snapshotType in filters.types" :key="snapshotType" :value="snapshotType">
              {{ t(`snapshots.types.${snapshotType}`) }}
            </option>
          </select>
        </label>

        <label class="form-field">
          <span>{{ t("snapshots.filters.sortBy") }}</span>
          <select v-model="query.sortBy" class="property-field" @change="applyFilterChange">
            <option value="created_at">{{ t("snapshots.sort.createdAt") }}</option>
            <option value="name">{{ t("snapshots.sort.name") }}</option>
            <option value="dataset">{{ t("snapshots.sort.dataset") }}</option>
            <option value="used">{{ t("snapshots.sort.used") }}</option>
            <option value="referenced">{{ t("snapshots.sort.referenced") }}</option>
          </select>
        </label>

        <label class="form-field">
          <span>{{ t("snapshots.pagination.pageSize") }}</span>
          <select class="property-field" :value="pageSize" @change="changePageSize">
            <option :value="10">10</option>
            <option :value="25">25</option>
            <option :value="50">50</option>
          </select>
        </label>
      </div>

      <div class="dialog-actions">
        <button type="button" class="ghost-button" @click="changeSortDirection">
          {{ query.sortOrder === "asc" ? t("snapshots.sort.ascending") : t("snapshots.sort.descending") }}
        </button>
        <button type="button" class="ghost-button" @click="clearFilters">
          {{ t("snapshots.clearFilters") }}
        </button>
      </div>

      <EmptyState
        v-if="!items.length && !loading"
        :title="hasActiveFilters ? t('snapshots.filteredEmptyTitle') : t('snapshots.emptyTitle')"
        :description="hasActiveFilters ? t('snapshots.filteredEmptyDescription') : t('snapshots.emptyDescription')"
      />

      <div v-else class="table-shell">
        <table class="data-table">
          <thead>
            <tr>
              <th>{{ t("snapshots.columns.name") }}</th>
              <th>{{ t("snapshots.columns.dataset") }}</th>
              <th>{{ t("snapshots.columns.pool") }}</th>
              <th>{{ t("snapshots.columns.createdAt") }}</th>
              <th>{{ t("snapshots.columns.used") }}</th>
              <th>{{ t("snapshots.columns.referenced") }}</th>
              <th>{{ t("snapshots.columns.type") }}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="snapshot in items" :key="snapshot.id">
              <td>
                <div class="dataset-name-stack">
                  <strong>{{ snapshot.name }}</strong>
                  <span class="subtle-text">{{ snapshot.full_name }}</span>
                </div>
              </td>
              <td>{{ snapshot.dataset }}</td>
              <td>{{ snapshot.pool }}</td>
              <td>{{ formatDateTime(snapshot.created_at) }}</td>
              <td>{{ formatBytes(snapshot.used) }}</td>
              <td>{{ formatBytes(snapshot.referenced) }}</td>
              <td>{{ t(`snapshots.types.${snapshot.snapshot_type}`) }}</td>
              <td class="action-cell">
                <div class="inline-button-row">
                  <button type="button" class="ghost-button" @click="openDetails(snapshot)">
                    {{ t("common.view") }}
                  </button>
                  <button
                    type="button"
                    class="ghost-button"
                    :disabled="!snapshot.can_rollback"
                    :title="snapshot.rollback_reason || ''"
                    @click="openRollbackDialog(snapshot)"
                  >
                    {{ t("snapshots.rollback") }}
                  </button>
                  <button
                    type="button"
                    class="danger-button"
                    :disabled="!snapshot.can_delete"
                    :title="snapshot.delete_reason || ''"
                    @click="openDeleteDialog(snapshot)"
                  >
                    {{ t("common.delete") }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination-row">
        <p class="subtle-text">{{ t("snapshots.pagination.summary", { page, totalPages, total }) }}</p>
        <div class="inline-action-controls">
          <button type="button" class="ghost-button" :disabled="loading || page <= 1" @click="changePage(page - 1)">
            {{ t("snapshots.pagination.previous") }}
          </button>
          <button type="button" class="ghost-button" :disabled="loading || page >= totalPages" @click="changePage(page + 1)">
            {{ t("snapshots.pagination.next") }}
          </button>
        </div>
      </div>
    </article>

    <DetailDrawer
      v-model="drawerOpen"
      :title="t('snapshots.detailTitle')"
      :description="selectedSnapshot?.full_name || ''"
    >
      <div v-if="selectedSnapshot" class="drawer-section-list">
        <section class="drawer-section">
          <h4>{{ t("common.overview") }}</h4>
          <dl class="detail-grid">
            <div><dt>{{ t("snapshots.detail.name") }}</dt><dd>{{ selectedSnapshot.name }}</dd></div>
            <div><dt>{{ t("snapshots.detail.dataset") }}</dt><dd>{{ selectedSnapshot.dataset }}</dd></div>
            <div><dt>{{ t("snapshots.detail.pool") }}</dt><dd>{{ selectedSnapshot.pool }}</dd></div>
            <div><dt>{{ t("snapshots.detail.createdAt") }}</dt><dd>{{ formatDateTime(selectedSnapshot.created_at) }}</dd></div>
            <div><dt>{{ t("snapshots.detail.used") }}</dt><dd>{{ formatBytes(selectedSnapshot.used) }}</dd></div>
            <div><dt>{{ t("snapshots.detail.referenced") }}</dt><dd>{{ formatBytes(selectedSnapshot.referenced) }}</dd></div>
            <div><dt>{{ t("snapshots.detail.type") }}</dt><dd>{{ t(`snapshots.types.${selectedSnapshot.snapshot_type}`) }}</dd></div>
            <div><dt>{{ t("snapshots.detail.userrefs") }}</dt><dd>{{ selectedSnapshot.userrefs }}</dd></div>
          </dl>
        </section>

        <section class="drawer-section">
          <div class="drawer-section-header">
            <div>
              <h4>{{ t("snapshots.rollbackTitle") }}</h4>
              <p class="subtle-text">{{ selectedSnapshot.rollback_reason || t("snapshots.rollbackDescription") }}</p>
            </div>
            <button
              type="button"
              class="ghost-button"
              :disabled="!selectedSnapshot.can_rollback"
              @click="openRollbackDialog(selectedSnapshot)"
            >
              {{ t("snapshots.rollback") }}
            </button>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-section-header">
            <div>
              <h4>{{ t("common.dangerZone") }}</h4>
              <p class="subtle-text">{{ selectedSnapshot.delete_reason || t("snapshots.deleteDescription") }}</p>
            </div>
            <button
              type="button"
              class="danger-button"
              :disabled="!selectedSnapshot.can_delete"
              @click="openDeleteDialog(selectedSnapshot)"
            >
              {{ t("common.delete") }}
            </button>
          </div>
        </section>
      </div>
    </DetailDrawer>

    <ConfirmDialog
      :model-value="deleteDialogOpen"
      :busy="deleting"
      :can-confirm="Boolean(selectedSnapshot?.can_delete)"
      :result-mode="deleteDialogPhase === 'result'"
      :confirm-text="deleteDialogPhase === 'submitting' ? t('snapshots.dialogs.deleting') : t('snapshots.dialogs.confirmDelete')"
      :title="t('snapshots.dialogs.confirmSnapshotDelete')"
      :description="selectedSnapshot?.full_name || ''"
      @update:modelValue="deleteDialogOpen = $event"
      @confirm="confirmDeleteSnapshot"
    >
      <div v-if="deleteDialogPhase === 'confirm'" class="dialog-section-list">
        <p class="error-text">{{ t("snapshots.dialogs.deleteWarning") }}</p>
        <ul class="result-list">
          <li class="result-list-item">
            <strong>{{ t("snapshots.columns.dataset") }}</strong>
            <span class="subtle-text">{{ selectedSnapshot?.dataset || "-" }}</span>
          </li>
          <li class="result-list-item">
            <strong>{{ t("snapshots.columns.name") }}</strong>
            <span class="subtle-text">{{ selectedSnapshot?.full_name || "-" }}</span>
          </li>
        </ul>
      </div>

      <div v-else-if="deleteDialogPhase === 'submitting'" class="dialog-section-list">
        <div class="progress-shell">
          <div class="progress-spinner"></div>
          <div>
            <strong>{{ t("snapshots.dialogs.deletingSnapshot") }}</strong>
            <p class="subtle-text">{{ t("snapshots.dialogs.deletingSnapshotDescription") }}</p>
          </div>
        </div>
      </div>

      <div v-else class="dialog-section-list">
        <p v-if="deleteDialogSummary" class="notice-text">{{ deleteDialogSummary }}</p>
        <p v-if="deleteDialogError" class="error-text">{{ deleteDialogError }}</p>

        <section>
          <h4 class="dialog-mini-heading">{{ t("common.result") }}</h4>
          <CommandResultList
            :items="deleteDialogResult ? [{ ...deleteDialogResult, label: deleteDialogResult.snapshot, key: deleteDialogResult.snapshot || 'snapshot' }] : []"
            :empty-text="t('common.noResult')"
          />
        </section>

        <section>
          <h4 class="dialog-mini-heading">{{ t("common.sshTerminalLog") }}</h4>
          <CommandLogPanel :entries="buildDeleteLogLines(deleteDialogResult, selectedSnapshot?.full_name || 'snapshot')" />
        </section>
      </div>
    </ConfirmDialog>

    <ConfirmDialog
      :model-value="rollbackDialogOpen"
      :busy="rollingBack"
      :can-confirm="Boolean(selectedSnapshot?.can_rollback)"
      :result-mode="rollbackDialogPhase === 'result'"
      :confirm-text="rollbackDialogPhase === 'submitting' ? t('snapshots.dialogs.rollingBack') : t('snapshots.dialogs.confirmRollback')"
      :title="t('snapshots.dialogs.confirmSnapshotRollback')"
      :description="selectedSnapshot?.full_name || ''"
      @update:modelValue="rollbackDialogOpen = $event"
      @confirm="confirmRollbackSnapshot"
    >
      <div v-if="rollbackDialogPhase === 'confirm'" class="dialog-section-list">
        <p class="error-text">{{ t("snapshots.dialogs.rollbackWarning") }}</p>
        <section>
          <h4 class="dialog-mini-heading">{{ t("snapshots.rollbackModeTitle") }}</h4>
          <div class="stack-list">
            <label
              v-for="mode in ['safe', 'prune_newer', 'force_dependents']"
              :key="mode"
              class="stack-row"
            >
              <div class="stack-row-head">
                <div class="inline-action-controls">
                  <input v-model="rollbackMode" type="radio" name="snapshot-rollback-mode" :value="mode" />
                  <strong>{{ rollbackModeLabel(mode) }}</strong>
                </div>
              </div>
              <p class="subtle-text">{{ rollbackModeDescription(mode) }}</p>
              <p class="error-text">{{ rollbackModeWarning(mode) }}</p>
            </label>
          </div>
        </section>
        <ul class="result-list">
          <li class="result-list-item">
            <strong>{{ t("snapshots.columns.dataset") }}</strong>
            <span class="subtle-text">{{ selectedSnapshot?.dataset || "-" }}</span>
          </li>
          <li class="result-list-item">
            <strong>{{ t("snapshots.columns.name") }}</strong>
            <span class="subtle-text">{{ selectedSnapshot?.full_name || "-" }}</span>
          </li>
          <li class="result-list-item">
            <strong>{{ t("snapshots.rollbackModeTitle") }}</strong>
            <span class="subtle-text">{{ rollbackModeLabel(rollbackMode) }}</span>
          </li>
        </ul>
      </div>

      <div v-else-if="rollbackDialogPhase === 'submitting'" class="dialog-section-list">
        <div class="progress-shell">
          <div class="progress-spinner"></div>
          <div>
            <strong>{{ t("snapshots.dialogs.rollingBackSnapshot") }}</strong>
            <p class="subtle-text">{{ t("snapshots.dialogs.rollingBackSnapshotDescription") }}</p>
          </div>
        </div>
      </div>

      <div v-else class="dialog-section-list">
        <p v-if="rollbackDialogSummary" class="notice-text">{{ rollbackDialogSummary }}</p>
        <p v-if="rollbackDialogError" class="error-text">{{ rollbackDialogError }}</p>

        <section>
          <h4 class="dialog-mini-heading">{{ t("common.result") }}</h4>
          <CommandResultList
            :items="rollbackDialogResult ? [{ ...rollbackDialogResult, label: rollbackDialogResult.snapshot, key: rollbackDialogResult.snapshot || 'snapshot' }] : []"
            :empty-text="t('common.noResult')"
          />
        </section>

        <section>
          <h4 class="dialog-mini-heading">{{ t("common.sshTerminalLog") }}</h4>
          <CommandLogPanel :entries="buildRollbackLogLines(rollbackDialogResult, selectedSnapshot?.full_name || 'snapshot')" />
        </section>
      </div>
    </ConfirmDialog>
  </section>
</template>
