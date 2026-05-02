export default {
  props: {
    modelValue: { type: Boolean, required: true },
    title: { type: String, required: true },
    description: { type: String, default: "" },
    busy: { type: Boolean, default: false },
    canConfirm: { type: Boolean, default: true },
    confirmText: { type: String, default: "Confirm" },
    cancelText: { type: String, default: "Cancel" },
    closeText: { type: String, default: "Close" },
    resultMode: { type: Boolean, default: false },
  },
  emits: ["update:modelValue", "confirm"],
  methods: {
    close() {
      if (this.busy) {
        return;
      }
      this.$emit("update:modelValue", false);
    },
    confirm() {
      if (this.busy || !this.canConfirm) {
        return;
      }
      this.$emit("confirm");
    },
  },
  template: `
    <div v-if="modelValue" class="dialog-backdrop" @click.self="close">
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
            v-if="!resultMode"
            type="button"
            class="ghost-button"
            :disabled="busy"
            @click="close"
          >
            {{ cancelText }}
          </button>
          <button
            v-if="!resultMode"
            type="button"
            class="primary-button"
            :disabled="busy || !canConfirm"
            @click="confirm"
          >
            {{ confirmText }}
          </button>
          <button
            v-if="resultMode"
            type="button"
            class="primary-button"
            @click="close"
          >
            {{ closeText }}
          </button>
        </div>
      </div>
    </div>
  `,
};
