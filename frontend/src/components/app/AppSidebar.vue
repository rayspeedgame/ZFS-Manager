<script setup>
import { RouterLink } from "vue-router";
import { useI18n } from "vue-i18n";

const props = defineProps({
  routes: { type: Array, required: true },
  currentRouteKey: { type: String, required: true },
});

const { t } = useI18n();

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
  gear: `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M19.14 12.94c.04-.31.06-.63.06-.94s-.02-.63-.06-.94l2.03-1.58a.5.5 0 0 0 .12-.64l-1.92-3.32a.5.5 0 0 0-.6-.22l-2.39.96a7.03 7.03 0 0 0-1.63-.94l-.36-2.54a.5.5 0 0 0-.49-.42h-3.84a.5.5 0 0 0-.49.42l-.36 2.54c-.58.23-1.12.54-1.63.94l-2.39-.96a.5.5 0 0 0-.6.22L2.7 8.84a.5.5 0 0 0 .12.64l2.03 1.58c-.04.31-.06.63-.06.94s.02.63.06.94L2.82 14.52a.5.5 0 0 0-.12.64l1.92 3.32a.5.5 0 0 0 .6.22l2.39-.96c.5.39 1.05.71 1.63.94l.36 2.54a.5.5 0 0 0 .49.42h3.84a.5.5 0 0 0 .49-.42l.36-2.54c.58-.23 1.12-.54 1.63-.94l2.39.96a.5.5 0 0 0 .6-.22l1.92-3.32a.5.5 0 0 0-.12-.64zM12 15.5A3.5 3.5 0 1 1 12 8.5a3.5 3.5 0 0 1 0 7z" />
    </svg>
  `,
};

function iconMarkup(icon) {
  return icons[icon] ?? icons.grid;
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <div class="brand-mark">Z</div>
      <div>
        <strong>{{ t("app.brandTitle") }}</strong>
        <p>{{ t("app.brandSubtitle") }}</p>
      </div>
    </div>

    <nav class="nav-list" :aria-label="t('common.primaryNav')">
      <RouterLink
        v-for="route in props.routes"
        :key="route.key"
        :to="{ name: route.name }"
        class="nav-link"
        :data-active="route.key === props.currentRouteKey"
      >
        <span class="nav-icon" v-html="iconMarkup(route.icon)"></span>
        <span>{{ t(route.labelKey) }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>
