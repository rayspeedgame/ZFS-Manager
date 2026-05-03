<script setup>
const props = defineProps({
  modelValue: { type: Boolean, required: true },
  title: { type: String, required: true },
  description: { type: String, default: "" },
  busy: { type: Boolean, default: false },
  canConfirm: { type: Boolean, default: true },
  confirmText: { type: String, default: "Confirm" },
  cancelText: { type: String, default: "Cancel" },
  closeText: { type: String, default: "Close" },
  resultMode: { type: Boolean, default: false },
});

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
          {{ props.cancelText }}
        </button>
        <button
          v-if="!props.resultMode"
          type="button"
          class="primary-button"
          :disabled="props.busy || !props.canConfirm"
          @click="confirm"
        >
          {{ props.confirmText }}
        </button>
        <button
          v-if="props.resultMode"
          type="button"
          class="primary-button"
          @click="close"
        >
          {{ props.closeText }}
        </button>
      </div>
    </div>
  </div>
</template>
