export default {
  props: {
    state: { type: String, required: true },
  },
  template: `
    <span class="status-badge" :data-state="state">{{ state }}</span>
  `,
};
