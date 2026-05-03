import DashboardView from "../views/DashboardView.vue";
import DatasetsView from "../views/DatasetsView.vue";
import DisksView from "../views/DisksView.vue";
import PoolsView from "../views/PoolsView.vue";

export const navigationRoutes = [
  {
    key: "dashboard",
    name: "dashboard",
    path: "/dashboard",
    label: "Dashboard",
    icon: "grid",
    description: "Global storage health and live system summary.",
    component: DashboardView,
  },
  {
    key: "disks",
    name: "disks",
    path: "/disks",
    label: "Disks",
    icon: "disc",
    description: "Physical device inventory and membership details.",
    component: DisksView,
  },
  {
    key: "pools",
    name: "pools",
    path: "/pools",
    label: "Pools",
    icon: "stack",
    description: "Pool capacity, topology, and property overview.",
    component: PoolsView,
  },
  {
    key: "datasets",
    name: "datasets",
    path: "/datasets",
    label: "Datasets",
    icon: "folder-tree",
    description: "Filesystem and volume inventory with inheritance hints.",
    component: DatasetsView,
  },
];

export const routes = navigationRoutes.map((route) => ({
  path: route.path,
  name: route.name,
  component: route.component,
  meta: {
    key: route.key,
    label: route.label,
    icon: route.icon,
    description: route.description,
  },
}));
