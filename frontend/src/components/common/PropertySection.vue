<script setup>
defineProps({
  title: { type: String, required: true },
  description: { type: String, default: "" },
});
</script>

<template>
  <section class="drawer-section">
    <div class="drawer-section-header">
      <div>
        <h4>{{ title }}</h4>
        <p v-if="description" class="subtle-text">{{ description }}</p>
      </div>
      <slot name="actions" />
    </div>

    <slot />
  </section>
</template>
