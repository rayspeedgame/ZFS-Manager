const icons = {
  grid: `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z" />
    </svg>
  `,
  disc: `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3a9 9 0 1 0 9 9 9 9 0 0 0-9-9zm0 6a3 3 0 1 1-3 3 3 3 0 0 1 3-3z" />
    </svg>
  `,
  stack: `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3 3 8l9 5 9-5-9-5zm0 8 9-5v5l-9 5-9-5V6zm0 6 9-5v5l-9 5-9-5v-5z" />
    </svg>
  `,
  "folder-tree": `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3 5h6l2 2h10v4H3zm0 8h7v6H3zm11-1h7v3h-7zm0 5h7v3h-7z" />
    </svg>
  `,
};

export default {
  props: {
    routes: { type: Array, required: true },
    currentRouteKey: { type: String, required: true },
  },
  methods: {
    iconMarkup(icon) {
      return icons[icon] ?? icons.grid;
    },
  },
  template: `
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-mark">Z</div>
        <div>
          <strong>ZFS Manager</strong>
          <p>Storage Control</p>
        </div>
      </div>

      <nav class="nav-list" aria-label="Primary">
        <a
          v-for="route in routes"
          :key="route.key"
          :href="route.hash"
          class="nav-link"
          :data-active="route.key === currentRouteKey"
        >
          <span class="nav-icon" v-html="iconMarkup(route.icon)"></span>
          <span>{{ route.label }}</span>
        </a>
      </nav>
    </aside>
  `,
};
