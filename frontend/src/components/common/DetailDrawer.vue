<script setup>
import { useI18n } from "vue-i18n";

const props = defineProps({
  title: { type: String, required: true },
  description: { type: String, default: "" },
  modelValue: { type: Boolean, required: true },
});

const { t } = useI18n();
const emit = defineEmits(["update:modelValue"]);

function close() {
  emit("update:modelValue", false);
}
</script>

<template>
  <div v-if="props.modelValue" class="drawer-backdrop" @click.self="close">
    <aside class="detail-drawer">
      <div class="drawer-header">
        <div>
          <h3>{{ title }}</h3>
          <p>{{ description }}</p>
        </div>
        <button type="button" class="drawer-close" @click="close">{{ t("common.close") }}</button>
      </div>
      <div class="drawer-body">
        <slot />
      </div>
    </aside>
  </div>
</template>
