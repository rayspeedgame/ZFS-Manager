<script setup>
import { useI18n } from "vue-i18n";

const props = defineProps({
  items: { type: Array, default: () => [] },
  emptyText: { type: String, default: "" },
  statusFormatter: { type: Function, default: null },
});

const { t } = useI18n();
</script>

<template>
  <ul v-if="items.length" class="result-list">
    <li v-for="item in items" :key="item.key || item.property || item.label || item.name" class="result-list-item">
      <slot name="item" :item="item">
        <div class="result-list-head">
          <strong>{{ item.label || item.property || item.name }}</strong>
          <span v-if="item.success !== undefined" class="inline-status" :data-health="item.success ? 'ONLINE' : 'DEGRADED'">
            {{ props.statusFormatter ? props.statusFormatter(item) : item.success ? t("common.success") : t("common.failed") }}
          </span>
        </div>
        <p v-if="item.message" class="subtle-text">{{ item.message }}</p>
      </slot>
    </li>
  </ul>
  <p v-else class="subtle-text">{{ props.emptyText || t("common.noResultRows") }}</p>
</template>
