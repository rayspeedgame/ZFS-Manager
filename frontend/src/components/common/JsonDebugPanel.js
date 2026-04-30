export default {
  props: {
    payload: { type: Object, default: null },
  },
  computed: {
    jsonText() {
      return this.payload ? JSON.stringify(this.payload, null, 2) : "Waiting for state...";
    },
  },
  template: `
    <article class="surface-panel">
      <div class="section-header">
        <div>
          <h3>Raw JSON</h3>
          <p>Development-only snapshot preview.</p>
        </div>
      </div>
      <pre class="json-panel">{{ jsonText }}</pre>
    </article>
  `,
};
