<script setup>
import { computed, onBeforeUnmount, onMounted } from "vue";
import { RouterView, useRoute } from "vue-router";

import AppSidebar from "./components/app/AppSidebar.vue";
import AppTopbar from "./components/app/AppTopbar.vue";
import { navigationRoutes } from "./router/routes.js";
import { useAppState } from "./store/state.js";

const route = useRoute();
const { state, connect, disconnect } = useAppState();

const currentRoute = computed(() => ({
  key: route.meta.key || "dashboard",
  label: route.meta.label || "Dashboard",
  description: route.meta.description || "Global storage health and live system summary.",
}));

onMounted(() => {
  connect();
});

onBeforeUnmount(() => {
  disconnect();
});
</script>

<template>
  <div class="app-layout">
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
