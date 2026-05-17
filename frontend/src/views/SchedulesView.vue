<script setup>
import { computed, onMounted, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

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
const form = ref(createScrubScheduleDraft());

const pools = computed(() => {
  const value = props.state.snapshot.value?.data?.pools;
  return Array.isArray(value) ? value : [];
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

const summary = computed(() => ({
  total: schedules.value.length,
  enabled: schedules.value.filter((item) => item.enabled).length,
  disabled: schedules.value.filter((item) => !item.enabled).length,
}));

const sortedSchedules = computed(() =>
  [...schedules.value].sort((left, right) => {
    const leftValue = left.next_run_at || left.created_at || "";
    const rightValue = right.next_run_at || right.created_at || "";
    return leftValue.localeCompare(rightValue);
  })
);

const canSubmit = computed(() => Boolean(form.value.scope_name));

watch(poolOptions, (nextOptions) => {
  if (!form.value.scope_name && nextOptions.length) {
    form.value.scope_name = nextOptions[0].value;
  }
}, { immediate: true });

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
  if (!canSubmit.value || submitting.value) {
    return;
  }

  submitting.value = true;
  error.value = "";
  try {
    await createTaskSchedule({
      title: buildScheduleTitle(form.value.scope_name),
      kind: "pool.scrub.schedule",
      scope_type: "pool",
      scope_name: form.value.scope_name,
      enabled: true,
      schedule_type: "weekly",
      pattern: {
        weekday: Number(form.value.weekday),
        hour: Number(form.value.hour),
        minute: Number(form.value.minute),
        timezone: "local",
      },
      metadata: {},
    });
    form.value = createScrubScheduleDraft(form.value.scope_name);
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
  submitting.value = true;
  error.value = "";
  try {
    await deleteTaskSchedule(schedule.id);
    await refreshSchedules();
  } catch (nextError) {
    error.value = nextError instanceof Error ? nextError.message : String(nextError);
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

function buildScheduleTitle(poolName) {
  return t("schedules.scrub.autoTitle", { pool: poolName });
}

function createScrubScheduleDraft(poolName = "") {
  return {
    scope_name: poolName,
    weekday: 0,
    hour: 3,
    minute: 0,
  };
}
</script>

<template>
  <section class="view-grid">
    <div class="summary-grid">
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("schedules.summary.total") }}</span>
        <strong class="summary-value">{{ summary.total }}</strong>
        <span class="summary-meta">{{ t("schedules.summary.totalDescription") }}</span>
      </article>
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("schedules.summary.enabled") }}</span>
        <strong class="summary-value">{{ summary.enabled }}</strong>
        <span class="summary-meta">{{ t("schedules.summary.enabledDescription") }}</span>
      </article>
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("schedules.summary.disabled") }}</span>
        <strong class="summary-value">{{ summary.disabled }}</strong>
        <span class="summary-meta">{{ t("schedules.summary.disabledDescription") }}</span>
      </article>
      <article class="surface-panel summary-card">
        <span class="summary-label">{{ t("schedules.summary.types") }}</span>
        <strong class="summary-value">{{ t("schedules.summary.currentTypes") }}</strong>
        <span class="summary-meta">{{ t("schedules.summary.typesDescription") }}</span>
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
            <select v-model="form.scope_name" class="property-field">
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
            <select v-model="form.weekday" class="property-field">
              <option v-for="day in 7" :key="day - 1" :value="day - 1">
                {{ t(`schedules.weekdays.${day - 1}`) }}
              </option>
            </select>
          </label>

          <label class="form-field">
            <span>{{ t("schedules.fields.hour") }}</span>
            <input v-model.number="form.hour" class="property-field" type="number" min="0" max="23" />
          </label>

          <label class="form-field">
            <span>{{ t("schedules.fields.minute") }}</span>
            <input v-model.number="form.minute" class="property-field" type="number" min="0" max="59" />
          </label>
        </div>

        <div class="dialog-actions schedule-actions">
          <button type="button" class="ghost-button" :disabled="loading || submitting" @click="refreshSchedules">
            {{ loading ? t("schedules.refreshing") : t("schedules.refresh") }}
          </button>
          <button type="button" class="primary-button" :disabled="!canSubmit || submitting" @click="submitScrubSchedule">
            {{ submitting ? t("schedules.creating") : t("schedules.create") }}
          </button>
        </div>
      </article>

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
              <strong>{{ schedule.title }}</strong>
              <span class="status-badge" :data-state="scheduleStatusClass(schedule)">
                {{ scheduleStatusLabel(schedule) }}
              </span>
            </div>

            <p class="subtle-text">
              {{ t("schedules.scrub.ruleSummary", {
                pool: schedule.scope_name,
                weekday: t(`schedules.weekdays.${schedule.pattern.weekday}`),
                hour: String(schedule.pattern.hour).padStart(2, "0"),
                minute: String(schedule.pattern.minute).padStart(2, "0"),
              }) }}
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
    </div>

    <article class="surface-panel placeholder-panel">
      <div class="section-header">
        <div>
          <h3>{{ t("schedules.snapshot.title") }}</h3>
          <p>{{ t("schedules.snapshot.description") }}</p>
        </div>
      </div>
      <EmptyState
        :title="t('schedules.snapshot.placeholderTitle')"
        :description="t('schedules.snapshot.placeholderDescription')"
      />
    </article>
  </section>
</template>
