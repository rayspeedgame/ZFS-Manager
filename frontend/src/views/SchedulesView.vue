<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

import ConfirmDialog from "../components/common/ConfirmDialog.vue";
import EmptyState from "../components/common/EmptyState.vue";
import { formatDateTime } from "../lib/formatters.js";
import { useAppState } from "../store/state.js";

const props = defineProps({
  state: { type: Object, required: true },
});

const { t } = useI18n();
const {
  createTaskSchedule,
  deleteTaskSchedule,
  getTaskSchedules,
  updateTaskSchedule,
} = useAppState();

const loading = ref(false);
const submitting = ref(false);
const error = ref("");
const schedules = ref([]);
const deleteDialogOpen = ref(false);
const deleteDialogPhase = ref("confirm");
const deleteDialogSummary = ref("");
const deleteDialogError = ref("");
const schedulePendingDelete = ref(null);
const scrubForm = ref(createScrubScheduleDraft());
const snapshotForm = ref(createSnapshotScheduleDraft());

const pools = computed(() => {
  const value = props.state.snapshot.value?.data?.pools;
  return Array.isArray(value) ? value : [];
});

const datasets = computed(() => {
  const value = props.state.snapshot.value?.data?.datasets;
  return Array.isArray(value) ? value.filter((item) => String(item?.type || "") !== "snapshot") : [];
});

const poolOptions = computed(() =>
  pools.value
    .map((pool) => ({
      label: String(pool.name || "-"),
      value: String(pool.name || ""),
    }))
    .filter((item) => item.value)
    .sort((left, right) => left.label.localeCompare(right.label))
);

const datasetOptions = computed(() =>
  datasets.value
    .map((dataset) => ({
      label: String(dataset.name || "-"),
      value: String(dataset.name || ""),
      type: String(dataset.type || "filesystem"),
    }))
    .filter((item) => item.value)
    .sort((left, right) => left.label.localeCompare(right.label))
);

const summary = computed(() => {
  const scrubSchedules = schedules.value.filter((item) => item.kind === "pool.scrub.schedule");
  const snapshotSchedules = schedules.value.filter((item) => item.kind === "snapshot.schedule");
  return {
    scrubTotal: scrubSchedules.length,
    scrubEnabled: scrubSchedules.filter((item) => item.enabled).length,
    snapshotTotal: snapshotSchedules.length,
    snapshotEnabled: snapshotSchedules.filter((item) => item.enabled).length,
  };
});

const sortedSchedules = computed(() =>
  [...schedules.value].sort((left, right) => {
    const leftValue = left.next_run_at || left.created_at || "";
    const rightValue = right.next_run_at || right.created_at || "";
    return leftValue.localeCompare(rightValue);
  })
);

const canSubmitScrub = computed(() => Boolean(scrubForm.value.scope_name));
const canSubmitSnapshot = computed(() => {
  return Boolean(snapshotForm.value.scope_name);
});

const snapshotStrategyPreview = computed(() =>
  buildSnapshotStrategyPreview(snapshotForm.value.scope_name, snapshotForm.value.schedule_type, schedules.value)
);

watch(
  poolOptions,
  (nextOptions) => {
    if (!scrubForm.value.scope_name && nextOptions.length) {
      scrubForm.value.scope_name = nextOptions[0].value;
    }
  },
  { immediate: true }
);

watch(
  datasetOptions,
  (nextOptions) => {
    if (!snapshotForm.value.scope_name && nextOptions.length) {
      snapshotForm.value.scope_name = nextOptions[0].value;
    }
  },
  { immediate: true }
);

onMounted(async () => {
  await refreshSchedules();
});

async function refreshSchedules() {
  loading.value = true;
  error.value = "";
  try {
    const payload = await getTaskSchedules();
    schedules.value = Array.isArray(payload?.schedules) ? payload.schedules : [];
  } catch (nextError) {
    error.value = nextError instanceof Error ? nextError.message : String(nextError);
  } finally {
    loading.value = false;
  }
}

async function submitScrubSchedule() {
  if (!canSubmitScrub.value || submitting.value) {
    return;
  }

  submitting.value = true;
  error.value = "";
  try {
    await createTaskSchedule({
      title: buildScrubScheduleTitle(scrubForm.value.scope_name),
      kind: "pool.scrub.schedule",
      scope_type: "pool",
      scope_name: scrubForm.value.scope_name,
      enabled: true,
      schedule_type: "weekly",
      pattern: {
        weekday: Number(scrubForm.value.weekday),
        hour: Number(scrubForm.value.hour),
        minute: Number(scrubForm.value.minute),
        timezone: "local",
      },
      metadata: {},
    });
    scrubForm.value = createScrubScheduleDraft(scrubForm.value.scope_name);
    await refreshSchedules();
  } catch (nextError) {
    error.value = nextError instanceof Error ? nextError.message : String(nextError);
  } finally {
    submitting.value = false;
  }
}

async function submitSnapshotSchedule() {
  if (!canSubmitSnapshot.value || submitting.value) {
    return;
  }

  submitting.value = true;
  error.value = "";
  try {
    await createTaskSchedule({
      title: buildSnapshotScheduleTitle(snapshotForm.value.scope_name, snapshotStrategyPreview.value),
      kind: "snapshot.schedule",
      scope_type: "dataset",
      scope_name: snapshotForm.value.scope_name,
      enabled: true,
      schedule_type: snapshotForm.value.schedule_type,
      pattern: buildSnapshotPattern(snapshotForm.value),
      metadata: {
        recursive: Boolean(snapshotForm.value.recursive),
        keep_latest: Number(snapshotForm.value.keep_latest) || 0,
      },
    });
    snapshotForm.value = createSnapshotScheduleDraft(snapshotForm.value.scope_name);
    await refreshSchedules();
  } catch (nextError) {
    error.value = nextError instanceof Error ? nextError.message : String(nextError);
  } finally {
    submitting.value = false;
  }
}

async function toggleScheduleEnabled(schedule) {
  if (!schedule?.id || submitting.value) {
    return;
  }
  submitting.value = true;
  error.value = "";
  try {
    await updateTaskSchedule(schedule.id, {
      enabled: !schedule.enabled,
    });
    await refreshSchedules();
  } catch (nextError) {
    error.value = nextError instanceof Error ? nextError.message : String(nextError);
  } finally {
    submitting.value = false;
  }
}

async function removeSchedule(schedule) {
  if (!schedule?.id || submitting.value) {
    return;
  }
  schedulePendingDelete.value = schedule;
  deleteDialogPhase.value = "confirm";
  deleteDialogSummary.value = "";
  deleteDialogError.value = "";
  deleteDialogOpen.value = true;
}

async function confirmDeleteSchedule() {
  if (!schedulePendingDelete.value?.id || submitting.value) {
    return;
  }
  submitting.value = true;
  deleteDialogPhase.value = "submitting";
  deleteDialogSummary.value = "";
  deleteDialogError.value = "";
  error.value = "";
  try {
    await deleteTaskSchedule(schedulePendingDelete.value.id);
    await refreshSchedules();
    deleteDialogSummary.value = t("schedules.deleteSuccess", {
      title: schedulePendingDelete.value.title,
    });
    deleteDialogPhase.value = "result";
  } catch (nextError) {
    const message = nextError instanceof Error ? nextError.message : String(nextError);
    error.value = message;
    deleteDialogError.value = message;
    deleteDialogPhase.value = "result";
  } finally {
    submitting.value = false;
  }
}

function scheduleStatusLabel(schedule) {
  return schedule.enabled ? t("schedules.enabled") : t("schedules.disabled");
}

function scheduleStatusClass(schedule) {
  return schedule.enabled ? "ready" : "unknown";
}

function scheduleLastResult(schedule) {
  const result = schedule?.last_result;
  if (!result) {
    return t("schedules.notRunYet");
  }
  return t(`schedules.results.${result}`, result);
}

function scheduleKindLabel(kind) {
  if (kind === "pool.scrub.schedule") {
    return t("schedules.kindLabels.scrub");
  }
  if (kind === "snapshot.schedule") {
    return t("schedules.kindLabels.snapshot");
  }
  return t("schedules.kindLabels.unknown");
}

function scheduleSummary(schedule) {
  if (schedule.kind === "pool.scrub.schedule") {
    return t("schedules.scrub.ruleSummary", {
      pool: schedule.scope_name,
      weekday: t(`schedules.weekdays.${schedule.pattern.weekday}`),
      hour: String(schedule.pattern.hour).padStart(2, "0"),
      minute: String(schedule.pattern.minute).padStart(2, "0"),
    });
  }

  const metadata = schedule.metadata || {};
  return t("schedules.snapshot.ruleSummary", {
    dataset: schedule.scope_name,
    strategy: metadata.strategy_name || t("schedules.snapshot.pendingStrategy"),
    levelSummary: buildSnapshotLevelSummary(schedule),
    recursive: metadata.recursive
      ? t("schedules.snapshot.recursiveEnabled")
      : t("schedules.snapshot.recursiveDisabled"),
    keepLatest: Number(metadata.keep_latest || 0),
  });
}

function buildScrubScheduleTitle(poolName) {
  return t("schedules.scrub.autoTitle", { pool: poolName });
}

function buildSnapshotScheduleTitle(datasetName, prefix) {
  return t("schedules.snapshot.autoTitle", {
    dataset: datasetName,
    prefix: String(prefix || "").trim() || t("schedules.snapshot.pendingStrategy"),
  });
}

function createScrubScheduleDraft(poolName = "") {
  return {
    scope_name: poolName,
    weekday: 0,
    hour: 3,
    minute: 0,
  };
}

function createSnapshotScheduleDraft(datasetName = "") {
  return {
    scope_name: datasetName,
    schedule_type: "daily",
    interval: 15,
    weekday: 0,
    day_of_month: 1,
    hour: 2,
    minute: 0,
    recursive: false,
    keep_latest: 7,
  };
}

function buildSnapshotStrategyPreview(datasetName, scheduleType, currentSchedules) {
  const token = sanitizeScheduleToken(String(datasetName || "").replaceAll("/", "__") || "dataset");
  const prefix = `${token}-${sanitizeScheduleToken(scheduleType || "daily")}-`;
  const nextIndex =
    currentSchedules
      .filter((item) => item.kind === "snapshot.schedule" && item.scope_name === datasetName)
      .map((item) => {
        const strategy = String(item?.metadata?.strategy_name || "");
        if (!strategy.startsWith(prefix)) {
          return 0;
        }
        const suffix = strategy.slice(prefix.length);
        const parsed = Number.parseInt(suffix, 10);
        return Number.isFinite(parsed) ? parsed : 0;
      })
      .reduce((max, value) => Math.max(max, value), 0) + 1;
  return `${prefix}${String(nextIndex).padStart(3, "0")}`;
}

function buildSnapshotPattern(form) {
  const scheduleType = String(form.schedule_type || "daily");
  // The backend accepts one normalized pattern shape, but each schedule level
  // only needs a subset of the fields. Build the minimal payload per level so
  // the API stays explicit and future validation remains straightforward.
  if (scheduleType === "minutely") {
    return {
      interval: Number(form.interval) || 1,
      timezone: "local",
    };
  }
  if (scheduleType === "hourly") {
    return {
      interval: Number(form.interval) || 1,
      minute: Number(form.minute) || 0,
      timezone: "local",
    };
  }
  if (scheduleType === "daily") {
    return {
      hour: Number(form.hour) || 0,
      minute: Number(form.minute) || 0,
      timezone: "local",
    };
  }
  if (scheduleType === "weekly") {
    return {
      weekday: Number(form.weekday) || 0,
      hour: Number(form.hour) || 0,
      minute: Number(form.minute) || 0,
      timezone: "local",
    };
  }
  return {
    day_of_month: Number(form.day_of_month) || 1,
    hour: Number(form.hour) || 0,
    minute: Number(form.minute) || 0,
    timezone: "local",
  };
}

function showSnapshotInterval() {
  return ["minutely", "hourly"].includes(snapshotForm.value.schedule_type);
}

function showSnapshotWeekday() {
  return snapshotForm.value.schedule_type === "weekly";
}

function showSnapshotDayOfMonth() {
  return snapshotForm.value.schedule_type === "monthly";
}

function showSnapshotHour() {
  return ["daily", "weekly", "monthly"].includes(snapshotForm.value.schedule_type);
}

function showSnapshotMinute() {
  return snapshotForm.value.schedule_type !== "minutely";
}

function snapshotRuleDescription(scheduleType) {
  return t(`schedules.levelDescriptions.${scheduleType || "daily"}`);
}

function deleteDialogTitle() {
  if (schedulePendingDelete.value?.kind === "snapshot.schedule") {
    return t("schedules.dialogs.confirmSnapshotDeleteTitle");
  }
  return t("schedules.dialogs.confirmDeleteTitle");
}

function deleteDialogDescription() {
  return schedulePendingDelete.value?.title || "";
}

function formatScheduleNumber(value) {
  if (value === null || value === undefined || value === "") {
    return "--";
  }
  return String(value).padStart(2, "0");
}

function buildSnapshotLevelSummary(schedule) {
  const type = String(schedule.schedule_type || "daily");
  const pattern = schedule.pattern || {};
  if (type === "minutely") {
    return t("schedules.levelSummary.minutely", { interval: pattern.interval ?? 1 });
  }
  if (type === "hourly") {
    return t("schedules.levelSummary.hourly", {
      interval: pattern.interval ?? 1,
      minute: formatScheduleNumber(pattern.minute),
    });
  }
  if (type === "daily") {
    return t("schedules.levelSummary.daily", {
      hour: formatScheduleNumber(pattern.hour),
      minute: formatScheduleNumber(pattern.minute),
    });
  }
  if (type === "weekly") {
    return t("schedules.levelSummary.weekly", {
      weekday: t(`schedules.weekdays.${pattern.weekday ?? 0}`),
      hour: formatScheduleNumber(pattern.hour),
      minute: formatScheduleNumber(pattern.minute),
    });
  }
  return t("schedules.levelSummary.monthly", {
    dayOfMonth: pattern.day_of_month ?? 1,
    hour: formatScheduleNumber(pattern.hour),
    minute: formatScheduleNumber(pattern.minute),
  });
}

function sanitizeScheduleToken(value) {
  const normalized = String(value || "")
    .trim()
    .replace(/[^A-Za-z0-9._-]+/g, "_")
    .replace(/^[._-]+|[._-]+$/g, "");
  return normalized || "item";
}
</script>

<template>
  <section class="view-grid">
    <div class="summary-grid">
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("schedules.summary.scrub") }}</span>
        <strong class="summary-value">{{ summary.scrubEnabled }}/{{ summary.scrubTotal }}</strong>
        <span class="summary-meta">{{ t("schedules.summary.scrubDescription") }}</span>
      </article>
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("schedules.summary.snapshot") }}</span>
        <strong class="summary-value">{{ summary.snapshotEnabled }}/{{ summary.snapshotTotal }}</strong>
        <span class="summary-meta">{{ t("schedules.summary.snapshotDescription") }}</span>
      </article>
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("schedules.summary.placeholderOne") }}</span>
        <strong class="summary-value">{{ t("schedules.summary.placeholderValue") }}</strong>
        <span class="summary-meta">{{ t("schedules.summary.placeholderDescription") }}</span>
      </article>
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("schedules.summary.placeholderTwo") }}</span>
        <strong class="summary-value">{{ t("schedules.summary.placeholderValue") }}</strong>
        <span class="summary-meta">{{ t("schedules.summary.placeholderDescription") }}</span>
      </article>
    </div>

    <div v-if="error" class="surface-panel">
      <p class="error-text">{{ error }}</p>
    </div>

    <div class="schedule-layout">
      <article class="surface-panel">
        <div class="section-header">
          <div>
            <h3>{{ t("schedules.scrub.title") }}</h3>
            <p>{{ t("schedules.scrub.description") }}</p>
          </div>
        </div>

        <div class="schedule-form-grid">
          <label class="form-field">
            <span>{{ t("schedules.fields.pool") }}</span>
            <select v-model="scrubForm.scope_name" class="property-field">
              <option
                v-for="option in poolOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </label>

          <label class="form-field">
            <span>{{ t("schedules.fields.weekday") }}</span>
            <select v-model="scrubForm.weekday" class="property-field">
              <option v-for="day in 7" :key="day - 1" :value="day - 1">
                {{ t(`schedules.weekdays.${day - 1}`) }}
              </option>
            </select>
          </label>

          <label class="form-field">
            <span>{{ t("schedules.fields.hour") }}</span>
            <input v-model.number="scrubForm.hour" class="property-field" type="number" min="0" max="23" />
          </label>

          <label class="form-field">
            <span>{{ t("schedules.fields.minute") }}</span>
            <input v-model.number="scrubForm.minute" class="property-field" type="number" min="0" max="59" />
          </label>
        </div>

        <div class="dialog-actions schedule-actions">
          <button type="button" class="ghost-button" :disabled="loading || submitting" @click="refreshSchedules">
            {{ loading ? t("schedules.refreshing") : t("schedules.refresh") }}
          </button>
          <button type="button" class="primary-button" :disabled="!canSubmitScrub || submitting" @click="submitScrubSchedule">
            {{ submitting ? t("schedules.creating") : t("schedules.create") }}
          </button>
        </div>
      </article>

      <article class="surface-panel">
        <div class="section-header">
          <div>
            <h3>{{ t("schedules.snapshot.title") }}</h3>
            <p>{{ t("schedules.snapshot.description") }}</p>
          </div>
        </div>

        <div class="schedule-form-grid">
          <label class="form-field">
            <span>{{ t("schedules.fields.dataset") }}</span>
            <select v-model="snapshotForm.scope_name" class="property-field">
              <option
                v-for="option in datasetOptions"
                :key="option.value"
                :value="option.value"
              >
                {{ option.label }}
              </option>
            </select>
          </label>

          <label class="form-field">
            <span>{{ t("schedules.fields.strategyName") }}</span>
            <input :value="snapshotStrategyPreview" class="property-field" type="text" readonly />
          </label>

          <label class="form-field">
            <span>{{ t("schedules.fields.level") }}</span>
            <select v-model="snapshotForm.schedule_type" class="property-field">
              <option value="minutely">{{ t("schedules.levels.minutely") }}</option>
              <option value="hourly">{{ t("schedules.levels.hourly") }}</option>
              <option value="daily">{{ t("schedules.levels.daily") }}</option>
              <option value="weekly">{{ t("schedules.levels.weekly") }}</option>
              <option value="monthly">{{ t("schedules.levels.monthly") }}</option>
            </select>
          </label>

          <label v-if="showSnapshotInterval()" class="form-field">
            <span>{{ t("schedules.fields.interval") }}</span>
            <input v-model.number="snapshotForm.interval" class="property-field" type="number" min="1" max="60" />
          </label>

          <label v-if="showSnapshotWeekday()" class="form-field">
            <span>{{ t("schedules.fields.weekday") }}</span>
            <select v-model="snapshotForm.weekday" class="property-field">
              <option v-for="day in 7" :key="day - 1" :value="day - 1">
                {{ t(`schedules.weekdays.${day - 1}`) }}
              </option>
            </select>
          </label>

          <label v-if="showSnapshotDayOfMonth()" class="form-field">
            <span>{{ t("schedules.fields.dayOfMonth") }}</span>
            <input v-model.number="snapshotForm.day_of_month" class="property-field" type="number" min="1" max="31" />
          </label>

          <label v-if="showSnapshotHour()" class="form-field">
            <span>{{ t("schedules.fields.hour") }}</span>
            <input v-model.number="snapshotForm.hour" class="property-field" type="number" min="0" max="23" />
          </label>

          <label v-if="showSnapshotMinute()" class="form-field">
            <span>{{ t("schedules.fields.minute") }}</span>
            <input v-model.number="snapshotForm.minute" class="property-field" type="number" min="0" max="59" />
          </label>

          <label class="form-field">
            <span>{{ t("schedules.fields.keepLatest") }}</span>
            <input v-model.number="snapshotForm.keep_latest" class="property-field" type="number" min="0" />
          </label>

        </div>

        <p class="subtle-text">
          {{ t("schedules.snapshot.retentionHint", { strategy: snapshotStrategyPreview }) }}
        </p>
        <p class="subtle-text">
          {{ snapshotRuleDescription(snapshotForm.schedule_type) }}
        </p>

        <div class="dialog-actions schedule-actions">
          <label class="inline-action-controls subtle-text">
            <input v-model="snapshotForm.recursive" type="checkbox" />
            <span>{{ t("schedules.fields.recursive") }}</span>
          </label>
          <button type="button" class="ghost-button" :disabled="loading || submitting" @click="refreshSchedules">
            {{ loading ? t("schedules.refreshing") : t("schedules.refresh") }}
          </button>
          <button type="button" class="primary-button" :disabled="!canSubmitSnapshot || submitting" @click="submitSnapshotSchedule">
            {{ submitting ? t("schedules.creating") : t("schedules.snapshot.create") }}
          </button>
        </div>
      </article>
    </div>

    <article class="surface-panel">
      <div class="section-header">
        <div>
          <h3>{{ t("schedules.listTitle") }}</h3>
          <p>{{ t("schedules.listDescription") }}</p>
        </div>
      </div>

      <EmptyState
        v-if="!sortedSchedules.length && !loading"
        :title="t('schedules.emptyTitle')"
        :description="t('schedules.emptyDescription')"
      />

      <div v-else class="schedule-card-list">
        <article
          v-for="schedule in sortedSchedules"
          :key="schedule.id"
          class="schedule-card"
        >
          <div class="task-card-head">
            <div>
              <strong>{{ schedule.title }}</strong>
              <p class="subtle-text">{{ scheduleKindLabel(schedule.kind) }}</p>
            </div>
            <span class="status-badge" :data-state="scheduleStatusClass(schedule)">
              {{ scheduleStatusLabel(schedule) }}
            </span>
          </div>

          <p class="subtle-text">
            {{ scheduleSummary(schedule) }}
          </p>

          <dl class="schedule-meta-grid">
            <div>
              <dt>{{ t("schedules.fields.nextRun") }}</dt>
              <dd>{{ formatDateTime(schedule.next_run_at) }}</dd>
            </div>
            <div>
              <dt>{{ t("schedules.fields.lastRun") }}</dt>
              <dd>{{ formatDateTime(schedule.last_run_at) }}</dd>
            </div>
            <div>
              <dt>{{ t("schedules.fields.lastResult") }}</dt>
              <dd>{{ scheduleLastResult(schedule) }}</dd>
            </div>
            <div>
              <dt>{{ t("schedules.fields.lastTask") }}</dt>
              <dd>{{ schedule.last_task_id || "-" }}</dd>
            </div>
          </dl>

          <div class="inline-action-controls schedule-card-actions">
            <button
              type="button"
              class="ghost-button"
              :disabled="submitting"
              @click="toggleScheduleEnabled(schedule)"
            >
              {{ schedule.enabled ? t("schedules.disable") : t("schedules.enable") }}
            </button>
            <button
              type="button"
              class="danger-button"
              :disabled="submitting"
              @click="removeSchedule(schedule)"
            >
              {{ t("schedules.delete") }}
            </button>
          </div>
        </article>
      </div>
    </article>

    <ConfirmDialog
      :model-value="deleteDialogOpen"
      :busy="submitting"
      :can-confirm="Boolean(schedulePendingDelete?.id)"
      :result-mode="deleteDialogPhase === 'result'"
      :confirm-text="deleteDialogPhase === 'submitting' ? t('schedules.dialogs.deleting') : t('schedules.dialogs.confirmDelete')"
      :title="deleteDialogTitle()"
      :description="deleteDialogDescription()"
      @update:modelValue="deleteDialogOpen = $event"
      @confirm="confirmDeleteSchedule"
    >
      <div v-if="deleteDialogPhase === 'confirm'" class="dialog-section-list">
        <p class="error-text">
          {{
            schedulePendingDelete?.kind === "snapshot.schedule"
              ? t("schedules.dialogs.snapshotDeleteWarning")
              : t("schedules.dialogs.deleteWarning")
          }}
        </p>
        <ul class="result-list">
          <li class="result-list-item">
            <strong>{{ t("schedules.fields.type") }}</strong>
            <span class="subtle-text">{{ scheduleKindLabel(schedulePendingDelete?.kind) }}</span>
          </li>
          <li class="result-list-item">
            <strong>{{ t("schedules.fields.title") }}</strong>
            <span class="subtle-text">{{ schedulePendingDelete?.title || "-" }}</span>
          </li>
          <li class="result-list-item">
            <strong>{{ t("schedules.fields.scope") }}</strong>
            <span class="subtle-text">{{ schedulePendingDelete?.scope_name || "-" }}</span>
          </li>
        </ul>
      </div>

      <div v-else-if="deleteDialogPhase === 'submitting'" class="dialog-section-list">
        <div class="progress-shell">
          <div class="progress-spinner"></div>
          <div>
            <strong>{{ t("schedules.dialogs.deletingSchedule") }}</strong>
            <p class="subtle-text">{{ t("schedules.dialogs.deletingScheduleDescription") }}</p>
          </div>
        </div>
      </div>

      <div v-else class="dialog-section-list">
        <p v-if="deleteDialogSummary" class="notice-text">{{ deleteDialogSummary }}</p>
        <p v-if="deleteDialogError" class="error-text">{{ deleteDialogError }}</p>
      </div>
    </ConfirmDialog>
  </section>
</template>
