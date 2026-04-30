import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import AppSidebar from "./components/app/AppSidebar.js";
import AppTopbar from "./components/app/AppTopbar.js";
import { routes } from "./router/routes.js";
import { useAppState } from "./store/state.js";

const routeMap = Object.fromEntries(routes.map((route) => [route.key, route]));

function resolveRouteFromHash(hash) {
  const normalized = hash.replace(/^#\/?/, "");
  return routeMap[normalized] ? normalized : "dashboard";
}

export default {
  components: {
    AppSidebar,
    AppTopbar,
  },
  setup() {
    const currentRouteKey = ref(resolveRouteFromHash(window.location.hash));
    const { state, connect, disconnect } = useAppState();

    const currentRoute = computed(() => routeMap[currentRouteKey.value] ?? routeMap.dashboard);
    const currentView = computed(() => currentRoute.value.component);

    function syncRoute() {
      currentRouteKey.value = resolveRouteFromHash(window.location.hash);
    }

    onMounted(() => {
      if (!window.location.hash) {
        window.location.hash = routes[0].hash;
      }
      window.addEventListener("hashchange", syncRoute);
      connect();
    });

    onBeforeUnmount(() => {
      window.removeEventListener("hashchange", syncRoute);
      disconnect();
    });

    return {
      currentRoute,
      currentView,
      routes,
      state,
    };
  },
  template: `
    <div class="app-layout">
      <AppSidebar :routes="routes" :current-route-key="currentRoute.key" />

      <div class="app-main">
        <AppTopbar
          :title="currentRoute.label"
          :description="currentRoute.description"
          :state="state"
        />

        <main class="view-shell">
          <component :is="currentView" :state="state" />
        </main>
      </div>
    </div>
  `,
};
