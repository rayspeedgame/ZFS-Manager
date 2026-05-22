<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

import EmptyState from "../components/common/EmptyState.vue";
import { formatDateTime } from "../lib/formatters.js";
import { useTasksStore } from "../stores/tasks.js";

const { t } = useI18n();
const tasksStore = useTasksStore();
const selectedTaskId = ref("");

const tasks = computed(() => tasksStore.tasks);
const loading = computed(() => tasksStore.loading);
const error = computed(() => tasksStore.error);
const selectedTask = computed(() => tasksStore.selectedTask);
const lastLoadedAt = computed(() => formatDateTime(tasksStore.lastLoadedAt));
const runningCount = computed(() => tasksStore.runningCount);
const completedCount = computed(() => tasksStore.completedCount);
const failedCount = computed(() => tasksStore.failedCount);
const total = computed(() => tasksStore.total);
const filteredTotal = computed(() => tasksStore.filteredTotal);
const page = computed(() => tasksStore.page);
const pageSize = computed(() => tasksStore.pageSize);
const statusFilter = computed(() => tasksStore.statusFilter);
const totalPages = computed(() => tasksStore.totalPages);

watch(tasks, (nextTasks) => {
  if (!nextTasks.length) {
    selectedTaskId.value = "";
    return;
  }
  if (!selectedTaskId.value || !nextTasks.some((item) => item.id === selectedTaskId.value)) {
    selectedTaskId.value = nextTasks[0].id;
  }
}, { immediate: true });

watch(selectedTaskId, (taskId) => {
  if (taskId) {
    tasksStore.loadTask(taskId).catch(() => {
      // The visible list refresh already exposes fetch failures.
    });
  }
}, { immediate: true });

onMounted(async () => {
  try {
    await tasksStore.refreshTasks();
  } catch {
    // Keep the page mounted and show the store-level error state.
  }
  tasksStore.startAutoRefresh();
});

onBeforeUnmount(() => {
  tasksStore.stopAutoRefresh();
});

function selectTask(taskId) {
  selectedTaskId.value = taskId;
}

function taskStatusLabel(status) {
  return t(`tasks.status.${status || "unknown"}`);
}

function taskStatusClass(status) {
  const normalized = String(status || "").toLowerCase();
  if (normalized === "succeeded") {
    return "ready";
  }
  if (normalized === "running" || normalized === "queued" || normalized === "recovering") {
    return "degraded";
  }
  if (normalized === "failed" || normalized === "canceled" || normalized === "needs_attention") {
    return "error";
  }
  return "unknown";
}

function taskScope(task) {
  if (!task?.scope_type || !task?.scope_name) {
    return "-";
  }
  return `${task.scope_type}: ${task.scope_name}`;
}

function taskProgress(task) {
  const value = Number(task?.progress ?? 0);
  if (!Number.isFinite(value)) {
    return 0;
  }
  return Math.max(0, Math.min(100, value));
}

function buildLogText(log) {
  return [
    `$ ${log.command || "N/A"}`,
    log.exit_status !== null && log.exit_status !== undefined ? `exit_status: ${log.exit_status}` : null,
    log.stdout ? `stdout: ${log.stdout}` : null,
    log.stderr ? `stderr: ${log.stderr}` : null,
  ].filter(Boolean).join("\n");
}

function changePage(nextPage) {
  tasksStore.refreshTasks({ page: nextPage }).catch(() => {
    // The page already renders the store-level error state.
  });
}

function changePageSize(event) {
  tasksStore.refreshTasks({ page: 1, pageSize: Number(event.target.value) || 20 }).catch(() => {
    // The page already renders the store-level error state.
  });
}

function changeStatusFilter(event) {
  tasksStore.refreshTasks({ page: 1, statusFilter: String(event.target.value || "") }).catch(() => {
    // The page already renders the store-level error state.
  });
}
</script>

<template>
  <section class="view-grid">
    <div class="summary-grid">
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("tasks.summary.total") }}</span>
        <strong class="summary-value">{{ total }}</strong>
        <span class="summary-meta">{{ t("tasks.summary.lastLoaded", { value: lastLoadedAt }) }}</span>
      </article>
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("tasks.summary.running") }}</span>
        <strong class="summary-value">{{ runningCount }}</strong>
        <span class="summary-meta">{{ t("tasks.summary.runningDescription") }}</span>
      </article>
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("tasks.summary.completed") }}</span>
        <strong class="summary-value">{{ completedCount }}</strong>
        <span class="summary-meta">{{ t("tasks.summary.completedDescription") }}</span>
      </article>
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("tasks.summary.failed") }}</span>
        <strong class="summary-value">{{ failedCount }}</strong>
        <span class="summary-meta">{{ t("tasks.summary.failedDescription") }}</span>
      </article>
    </div>

    <div v-if="error" class="surface-panel">
      <p class="error-text">{{ error }}</p>
    </div>

    <div v-if="loading && !tasks.length && total === 0" class="surface-panel">
      <p class="subtle-text">{{ t("tasks.loading") }}</p>
    </div>

    <EmptyState
      v-else-if="total === 0"
      :title="t('tasks.emptyTitle')"
      :description="t('tasks.emptyDescription')"
    />

    <div v-else class="tasks-layout">
      <article class="surface-panel task-list-panel">
        <div class="section-header">
          <div>
            <h3>{{ t("tasks.listTitle") }}</h3>
            <p>{{ t("tasks.listDescription") }}</p>
          </div>
          <div class="inline-action-controls">
            <label class="inline-select">
              <span>{{ t("tasks.filters.status") }}</span>
              <select class="property-field compact-field" :value="statusFilter" @change="changeStatusFilter">
                <option value="">{{ t("tasks.filters.allStatuses") }}</option>
                <option value="queued">{{ t("tasks.status.queued") }}</option>
                <option value="running">{{ t("tasks.status.running") }}</option>
                <option value="recovering">{{ t("tasks.status.recovering") }}</option>
                <option value="succeeded">{{ t("tasks.status.succeeded") }}</option>
                <option value="failed">{{ t("tasks.status.failed") }}</option>
                <option value="canceled">{{ t("tasks.status.canceled") }}</option>
                <option value="unknown">{{ t("tasks.status.unknown") }}</option>
                <option value="needs_attention">{{ t("tasks.status.needs_attention") }}</option>
              </select>
            </label>
            <label class="inline-select">
              <span>{{ t("tasks.pagination.pageSize") }}</span>
              <select class="property-field compact-field" :value="pageSize" @change="changePageSize">
                <option :value="10">10</option>
                <option :value="20">20</option>
                <option :value="50">50</option>
              </select>
            </label>
            <button type="button" class="ghost-button" :disabled="loading" @click="tasksStore.refreshTasks()">
              {{ loading ? t("tasks.refreshing") : t("tasks.refresh") }}
            </button>
          </div>
        </div>

        <EmptyState
          v-if="!tasks.length"
          :title="t('tasks.filteredEmptyTitle')"
          :description="t('tasks.filteredEmptyDescription')"
        />

        <div v-else class="task-list">
          <button
            v-for="task in tasks"
            :key="task.id"
            type="button"
            class="task-card"
            :data-selected="task.id === selectedTaskId"
            @click="selectTask(task.id)"
          >
            <div class="task-card-head">
              <strong>{{ task.title }}</strong>
              <span class="status-badge" :data-state="taskStatusClass(task.status)">
                {{ taskStatusLabel(task.status) }}
              </span>
            </div>
            <p class="subtle-text">{{ task.message || t("tasks.noMessage") }}</p>
            <div class="task-progress-row">
              <div class="usage-bar">
                <span class="usage-bar-fill" :style="{ width: `${taskProgress(task)}%` }"></span>
              </div>
              <strong>{{ taskProgress(task) }}%</strong>
            </div>
            <div class="task-card-meta">
              <span>{{ taskScope(task) }}</span>
              <span>{{ formatDateTime(task.created_at) }}</span>
            </div>
          </button>
        </div>

        <div class="pagination-row">
          <p class="subtle-text">
            {{ t("tasks.pagination.summary", { page, totalPages, total: filteredTotal, allTotal: total }) }}
          </p>
          <div class="inline-action-controls">
            <button
              type="button"
              class="ghost-button"
              :disabled="loading || page <= 1"
              @click="changePage(page - 1)"
            >
              {{ t("tasks.pagination.previous") }}
            </button>
            <button
              type="button"
              class="ghost-button"
              :disabled="loading || page >= totalPages"
              @click="changePage(page + 1)"
            >
              {{ t("tasks.pagination.next") }}
            </button>
          </div>
        </div>
      </article>

      <article v-if="selectedTask" class="surface-panel task-detail-panel">
        <div class="section-header">
          <div>
            <h3>{{ selectedTask.title }}</h3>
            <p>{{ selectedTask.message || t("tasks.noMessage") }}</p>
          </div>
          <span class="status-badge" :data-state="taskStatusClass(selectedTask.status)">
            {{ taskStatusLabel(selectedTask.status) }}
          </span>
        </div>

        <dl class="detail-grid">
          <div>
            <dt>{{ t("tasks.detail.kind") }}</dt>
            <dd>{{ selectedTask.kind }}</dd>
          </div>
          <div>
            <dt>{{ t("tasks.detail.scope") }}</dt>
            <dd>{{ taskScope(selectedTask) }}</dd>
          </div>
          <div>
            <dt>{{ t("tasks.detail.stage") }}</dt>
            <dd>{{ selectedTask.stage || "-" }}</dd>
          </div>
          <div>
            <dt>{{ t("tasks.detail.progress") }}</dt>
            <dd>{{ taskProgress(selectedTask) }}%</dd>
          </div>
          <div>
            <dt>{{ t("tasks.detail.createdAt") }}</dt>
            <dd>{{ formatDateTime(selectedTask.created_at) }}</dd>
          </div>
          <div>
            <dt>{{ t("tasks.detail.startedAt") }}</dt>
            <dd>{{ formatDateTime(selectedTask.started_at) }}</dd>
          </div>
          <div>
            <dt>{{ t("tasks.detail.finishedAt") }}</dt>
            <dd>{{ formatDateTime(selectedTask.finished_at) }}</dd>
          </div>
          <div>
            <dt>{{ t("tasks.detail.taskId") }}</dt>
            <dd>{{ selectedTask.id }}</dd>
          </div>
        </dl>

        <section class="drawer-section">
          <h4>{{ t("tasks.logsTitle") }}</h4>
          <EmptyState
            v-if="!selectedTask.command_logs?.length"
            :title="t('tasks.logsEmptyTitle')"
            :description="t('tasks.logsEmptyDescription')"
          />
          <div v-else class="terminal-log-list">
            <article
              v-for="log in selectedTask.command_logs"
              :key="`${selectedTask.id}:${log.label}:${log.command}`"
              class="terminal-log-card"
            >
              <div class="result-list-head">
                <strong>{{ log.label }}</strong>
                <span class="status-badge" :data-state="log.success ? 'ready' : 'error'">
                  {{ log.success ? t("tasks.logSuccess") : t("tasks.logFailed") }}
                </span>
              </div>
              <p class="subtle-text">{{ log.message }}</p>
              <pre class="terminal-log-block">{{ buildLogText(log) }}</pre>
            </article>
          </div>
        </section>
      </article>
    </div>
  </section>
</template>
