<script setup>
defineProps({
  state: { type: String, required: true },
});
</script>

<template>
  <span class="status-badge" :data-state="state">{{ state }}</span>
</template>
