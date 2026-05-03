<script setup>
import { useI18n } from "vue-i18n";

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  title: { type: String, required: true },
  description: { type: String, default: "" },
  busy: { type: Boolean, default: false },
  canConfirm: { type: Boolean, default: true },
  confirmText: { type: String, default: "" },
  cancelText: { type: String, default: "" },
  closeText: { type: String, default: "" },
  resultMode: { type: Boolean, default: false },
});

const { t } = useI18n();
const emit = defineEmits(["update:modelValue", "confirm"]);

function close() {
  if (props.busy) {
    return;
  }
  emit("update:modelValue", false);
}

function confirm() {
  if (props.busy || !props.canConfirm) {
    return;
  }
  emit("confirm");
}
</script>

<template>
  <div v-if="props.modelValue" class="dialog-backdrop" @click.self="close">
    <div class="confirm-dialog">
      <div class="dialog-header">
        <div>
          <h3>{{ title }}</h3>
          <p>{{ description }}</p>
        </div>
      </div>
      <div class="dialog-body">
        <slot />
      </div>
      <div class="dialog-actions">
        <button
          v-if="!props.resultMode"
          type="button"
          class="ghost-button"
          :disabled="props.busy"
          @click="close"
        >
          {{ props.cancelText || t("common.cancel") }}
        </button>
        <button
          v-if="!props.resultMode"
          type="button"
          class="primary-button"
          :disabled="props.busy || !props.canConfirm"
          @click="confirm"
        >
          {{ props.confirmText || t("common.confirm") }}
        </button>
        <button
          v-if="props.resultMode"
          type="button"
          class="primary-button"
          @click="close"
        >
          {{ props.closeText || t("common.close") }}
        </button>
      </div>
    </div>
  </div>
</template>
