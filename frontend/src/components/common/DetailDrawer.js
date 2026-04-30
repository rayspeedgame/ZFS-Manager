export default {
  props: {
    title: { type: String, required: true },
    description: { type: String, default: "" },
    modelValue: { type: Boolean, required: true },
  },
  emits: ["update:modelValue"],
  methods: {
    close() {
      this.$emit("update:modelValue", false);
    },
  },
  template: `
    <div v-if="modelValue" class="drawer-backdrop" @click.self="close">
      <aside class="detail-drawer">
        <div class="drawer-header">
          <div>
            <h3>{{ title }}</h3>
            <p>{{ description }}</p>
          </div>
          <button type="button" class="drawer-close" @click="close">Close</button>
        </div>
        <div class="drawer-body">
          <slot />
        </div>
      </aside>
    </div>
  `,
};
