import DashboardView from "../views/DashboardView.vue";
import DatasetsView from "../views/DatasetsView.vue";
import DisksView from "../views/DisksView.vue";
import PoolsView from "../views/PoolsView.vue";
import SettingsView from "../views/SettingsView.vue";

export const navigationRoutes = [
  {
    key: "dashboard",
    name: "dashboard",
    path: "/dashboard",
    labelKey: "routes.dashboard.label",
    icon: "grid",
    descriptionKey: "routes.dashboard.description",
    component: DashboardView,
  },
  {
    key: "disks",
    name: "disks",
    path: "/disks",
    labelKey: "routes.disks.label",
    icon: "disc",
    descriptionKey: "routes.disks.description",
    component: DisksView,
  },
  {
    key: "pools",
    name: "pools",
    path: "/pools",
    labelKey: "routes.pools.label",
    icon: "stack",
    descriptionKey: "routes.pools.description",
    component: PoolsView,
  },
  {
    key: "datasets",
    name: "datasets",
    path: "/datasets",
    labelKey: "routes.datasets.label",
    icon: "folder-tree",
    descriptionKey: "routes.datasets.description",
    component: DatasetsView,
  },
  {
    key: "settings",
    name: "settings",
    path: "/settings",
    labelKey: "routes.settings.label",
    icon: "gear",
    descriptionKey: "routes.settings.description",
    component: SettingsView,
  },
];

export const routes = navigationRoutes.map((route) => ({
  path: route.path,
  name: route.name,
  component: route.component,
  meta: {
    key: route.key,
    labelKey: route.labelKey,
    icon: route.icon,
    descriptionKey: route.descriptionKey,
  },
}));
