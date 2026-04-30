export default {
  props: {
    title: { type: String, required: true },
    description: { type: String, required: true },
  },
  template: `
    <div class="empty-state">
      <strong>{{ title }}</strong>
      <p>{{ description }}</p>
    </div>
  `,
};
