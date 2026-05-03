<script setup>
defineProps({
  entries: { type: Array, default: () => [] },
  emptyText: { type: String, default: "No SSH logs are available for this submission." },
});
</script>

<template>
  <div v-if="entries.length" class="terminal-log-list">
    <article v-for="entry in entries" :key="entry.key" class="terminal-log-card">
      <div class="result-list-head">
        <strong>{{ entry.label }}</strong>
        <span class="inline-status" :data-health="entry.success ? 'ONLINE' : 'DEGRADED'">
          {{ entry.success ? "OK" : "Error" }}
        </span>
      </div>
      <pre class="terminal-log-block">{{ entry.lines.join('\n') }}</pre>
    </article>
  </div>
  <p v-else class="subtle-text">{{ emptyText }}</p>
</template>
