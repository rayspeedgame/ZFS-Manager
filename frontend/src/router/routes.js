import DashboardView from "../views/DashboardView.js";
import DatasetsView from "../views/DatasetsView.js";
import DisksView from "../views/DisksView.js";
import PoolsView from "../views/PoolsView.js";

export const routes = [
  {
    key: "dashboard",
    hash: "#/dashboard",
    label: "Dashboard",
    icon: "grid",
    description: "Global storage health and live system summary.",
    component: DashboardView,
  },
  {
    key: "disks",
    hash: "#/disks",
    label: "Disks",
    icon: "disc",
    description: "Physical device inventory and membership details.",
    component: DisksView,
  },
  {
    key: "pools",
    hash: "#/pools",
    label: "Pools",
    icon: "stack",
    description: "Pool capacity, topology, and property overview.",
    component: PoolsView,
  },
  {
    key: "datasets",
    hash: "#/datasets",
    label: "Datasets",
    icon: "folder-tree",
    description: "Filesystem and volume inventory with inheritance hints.",
    component: DatasetsView,
  },
];
