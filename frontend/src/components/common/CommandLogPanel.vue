<script setup>
import { useI18n } from "vue-i18n";

const props = defineProps({
  entries: { type: Array, default: () => [] },
  emptyText: { type: String, default: "" },
});

const { t } = useI18n();
</script>

<template>
  <div v-if="entries.length" class="terminal-log-list">
    <article v-for="entry in entries" :key="entry.key" class="terminal-log-card">
      <div class="result-list-head">
        <strong>{{ entry.label }}</strong>
        <span class="inline-status" :data-health="entry.success ? 'ONLINE' : 'DEGRADED'">
          {{ entry.success ? t("common.ok") : t("common.error") }}
        </span>
      </div>
      <pre class="terminal-log-block">{{ entry.lines.join('\n') }}</pre>
    </article>
  </div>
  <p v-else class="subtle-text">{{ props.emptyText || t("common.noSshLogs") }}</p>
</template>
