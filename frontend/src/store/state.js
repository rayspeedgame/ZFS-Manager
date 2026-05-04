import { useAppStore } from "../stores/app.js";
import {
  createDataset,
  createPool,
  destroyDataset,
  destroyPool,
  getSettings,
  removePoolTarget,
  saveSettings,
  testSshConnection,
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
    getSettings,
    login: appStore.login,
    createPool,
    destroyPool,
    logout: appStore.logout,
    removePoolTarget,
    refreshAuthStatus: appStore.refreshAuthStatus,
    refreshStateOnce: appStore.refreshStateOnce,
    saveSettings,
    testSshConnection,
    updateDatasetProperties,
    updatePoolProperties,
    updatePoolTopology,
  };
}
