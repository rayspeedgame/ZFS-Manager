import DashboardView from "../views/DashboardView.vue";
import DatasetsView from "../views/DatasetsView.vue";
import DisksView from "../views/DisksView.vue";
import PoolsView from "../views/PoolsView.vue";
import SchedulesView from "../views/SchedulesView.vue";
import SettingsView from "../views/SettingsView.vue";
import SnapshotsView from "../views/SnapshotsView.vue";
import TasksView from "../views/TasksView.vue";

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
    key: "snapshots",
    name: "snapshots",
    path: "/snapshots",
    labelKey: "routes.snapshots.label",
    icon: "camera",
    descriptionKey: "routes.snapshots.description",
    component: SnapshotsView,
  },
  {
    key: "schedules",
    name: "schedules",
    path: "/schedules",
    labelKey: "routes.schedules.label",
    icon: "calendar",
    descriptionKey: "routes.schedules.description",
    component: SchedulesView,
  },
  {
    key: "tasks",
    name: "tasks",
    path: "/tasks",
    labelKey: "routes.tasks.label",
    icon: "pulse",
    descriptionKey: "routes.tasks.description",
    component: TasksView,
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
