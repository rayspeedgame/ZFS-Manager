import { useAppStore } from "../stores/app.js";
import {
  createDataset,
  createPool,
  destroyDataset,
  destroyPool,
  removePoolTarget,
  updateDatasetProperties,
  updatePoolProperties,
  updatePoolTopology,
} from "../services/api.js";

export function useAppState() {
  const appStore = useAppStore();

  return {
    state: appStore.state,
    connect: appStore.connect,
    createDataset,
    destroyDataset,
    disconnect: appStore.disconnect,
    forceRefreshState: appStore.forceRefreshState,
    createPool,
    destroyPool,
    removePoolTarget,
    refreshStateOnce: appStore.refreshStateOnce,
    updateDatasetProperties,
    updatePoolProperties,
    updatePoolTopology,
  };
}
