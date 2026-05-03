<script setup>
import { computed } from "vue";

const props = defineProps({
  payload: { type: Object, default: null },
});

const jsonText = computed(() =>
  props.payload ? JSON.stringify(props.payload, null, 2) : "Waiting for state..."
);
</script>

<template>
  <article class="surface-panel">
    <div class="section-header">
      <div>
        <h3>Raw JSON</h3>
        <p>Development-only snapshot preview.</p>
      </div>
    </div>
    <pre class="json-panel">{{ jsonText }}</pre>
  </article>
</template>
