<script setup>
import { computed } from "vue";
import { useI18n } from "vue-i18n";

const props = defineProps({
  payload: { type: Object, default: null },
});

const { t } = useI18n();
const jsonText = computed(() =>
  props.payload ? JSON.stringify(props.payload, null, 2) : t("common.waitingForState")
);
</script>

<template>
  <article class="surface-panel">
    <div class="section-header">
      <div>
        <h3>{{ t("common.rawJson") }}</h3>
        <p>{{ t("common.rawJsonDescription") }}</p>
      </div>
    </div>
    <pre class="json-panel">{{ jsonText }}</pre>
  </article>
</template>
