<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  emptyText: { type: String, default: "No result rows were returned." },
  statusFormatter: { type: Function, default: null },
});
</script>

<template>
  <ul v-if="items.length" class="result-list">
    <li v-for="item in items" :key="item.key || item.property || item.label || item.name" class="result-list-item">
      <slot name="item" :item="item">
        <div class="result-list-head">
          <strong>{{ item.label || item.property || item.name }}</strong>
          <span v-if="item.success !== undefined" class="inline-status" :data-health="item.success ? 'ONLINE' : 'DEGRADED'">
            {{ statusFormatter ? statusFormatter(item) : item.success ? "Success" : "Failed" }}
          </span>
        </div>
        <p v-if="item.message" class="subtle-text">{{ item.message }}</p>
      </slot>
    </li>
  </ul>
  <p v-else class="subtle-text">{{ emptyText }}</p>
</template>
