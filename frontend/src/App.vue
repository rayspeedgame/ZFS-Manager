<script setup>
import { computed, onBeforeUnmount, onMounted } from "vue";
import { RouterView, useRoute } from "vue-router";
import { useI18n } from "vue-i18n";

import AppLoginGate from "./components/app/AppLoginGate.vue";
import AppSidebar from "./components/app/AppSidebar.vue";
import AppTopbar from "./components/app/AppTopbar.vue";
import { navigationRoutes } from "./router/routes.js";
import { useAppState } from "./store/state.js";

const route = useRoute();
const { t } = useI18n();
const { state, disconnect, refreshAuthStatus } = useAppState();

const currentRoute = computed(() => ({
  key: route.meta.key || "dashboard",
  label: t(route.meta.labelKey || "routes.dashboard.label"),
  description: t(route.meta.descriptionKey || "routes.dashboard.description"),
}));
const authChecking = computed(() => state.authChecking.value);
const authEnabled = computed(() => state.authEnabled.value);
const authenticated = computed(() => state.authenticated.value);

onMounted(() => {
  // Resolve the auth gate before rendering the main shell so protected pages
  // do not briefly flash underneath the login screen.
  refreshAuthStatus();
});

onBeforeUnmount(() => {
  disconnect();
});
</script>

<template>
  <div v-if="authChecking" class="login-shell">
    <section class="login-card">
      <p class="eyebrow">{{ t("login.loadingTitle") }}</p>
      <h1>{{ t("login.loadingTitle") }}</h1>
      <p class="topbar-description">{{ t("login.loadingDescription") }}</p>
    </section>
  </div>
  <AppLoginGate v-else-if="authEnabled && !authenticated" />
  <div v-else class="app-layout">
    <AppSidebar :routes="navigationRoutes" :current-route-key="currentRoute.key" />

    <div class="app-main">
      <AppTopbar
        :title="currentRoute.label"
        :description="currentRoute.description"
        :state="state"
      />

      <main class="view-shell">
        <RouterView v-slot="{ Component }">
          <component :is="Component" :state="state" />
        </RouterView>
      </main>
    </div>
  </div>
</template>
