import { computed, ref } from "vue";
import { defineStore } from "pinia";

import { getTask, getTasks } from "../services/api.js";

let refreshTimer = null;

export const useTasksStore = defineStore("tasks", () => {
  const tasks = ref([]);
  const selectedTask = ref(null);
  const loading = ref(false);
  const error = ref("");
  const lastLoadedAt = ref(null);
  const total = ref(0);
  const filteredTotal = ref(0);
  const page = ref(1);
  const pageSize = ref(20);
  const totalPages = ref(1);
  const statusFilter = ref("");
  const runningCount = ref(0);
  const completedCount = ref(0);
  const failedCount = ref(0);

  async function refreshTasks(options = {}) {
    loading.value = true;
    error.value = "";
    try {
      if (options.page !== undefined) {
        page.value = Math.max(1, Number(options.page) || 1);
      }
      if (options.pageSize !== undefined) {
        pageSize.value = Math.max(1, Number(options.pageSize) || 20);
      }
      if (options.statusFilter !== undefined) {
        statusFilter.value = String(options.statusFilter || "");
      }
      const payload = await getTasks({
        page: page.value,
        pageSize: pageSize.value,
        statusFilter: statusFilter.value,
      });
      tasks.value = Array.isArray(payload?.tasks) ? payload.tasks : [];
      total.value = Number(payload?.total ?? tasks.value.length);
      filteredTotal.value = Number(payload?.filtered_total ?? tasks.value.length);
      page.value = Number(payload?.page ?? page.value);
      pageSize.value = Number(payload?.page_size ?? pageSize.value);
      totalPages.value = Number(payload?.total_pages ?? 1);
      runningCount.value = Number(payload?.running_count ?? 0);
      completedCount.value = Number(payload?.completed_count ?? 0);
      failedCount.value = Number(payload?.failed_count ?? 0);
      if (selectedTask.value?.id) {
        selectedTask.value = tasks.value.find((item) => item.id === selectedTask.value.id) || selectedTask.value;
      }
      lastLoadedAt.value = new Date().toISOString();
      return tasks.value;
    } catch (nextError) {
      error.value = nextError instanceof Error ? nextError.message : String(nextError);
      throw nextError;
    } finally {
      loading.value = false;
    }
  }

  async function loadTask(taskId) {
    if (!taskId) {
      selectedTask.value = null;
      return null;
    }
    const payload = await getTask(taskId);
    selectedTask.value = payload?.task || null;
    return selectedTask.value;
  }

  function startAutoRefresh(intervalMs = 5000) {
    stopAutoRefresh();
    refreshTimer = window.setInterval(() => {
      refreshTasks().catch(() => {
        // Keep the last visible data when a periodic refresh fails.
      });
    }, intervalMs);
  }

  function stopAutoRefresh() {
    if (refreshTimer) {
      window.clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }

  return {
    completedCount,
    error,
    failedCount,
    filteredTotal,
    lastLoadedAt,
    loadTask,
    loading,
    page,
    pageSize,
    refreshTasks,
    runningCount,
    selectedTask,
    statusFilter,
    startAutoRefresh,
    stopAutoRefresh,
    tasks,
    total,
    totalPages,
  };
});
