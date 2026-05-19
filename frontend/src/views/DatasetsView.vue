<script>
import { computed, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

import CreateDatasetDrawer from "../components/datasets/CreateDatasetDrawer.vue";
import DatasetActionDialogs from "../components/datasets/DatasetActionDialogs.vue";
import DatasetDetailDrawer from "../components/datasets/DatasetDetailDrawer.vue";
import DatasetTreeTable from "../components/datasets/DatasetTreeTable.vue";
import {
  COMMON_EDITABLE_DATASET_PROPERTIES,
  COMMON_FIXED_DATASET_PROPERTIES,
  CREATE_PROPERTY_FIELDS,
  EDITABLE_DATASET_PROPERTIES,
  EXCLUDED_DATASET_PROPERTIES,
  PROPERTY_INPUTS,
} from "../components/datasets/dataset-form-config.js";
import { formatBytes, formatDateTime } from "../lib/formatters.js";
import { useAppState } from "../store/state.js";

export default {
  components: {
    CreateDatasetDrawer,
    DatasetActionDialogs,
    DatasetDetailDrawer,
    DatasetTreeTable,
  },
  props: {
    state: { type: Object, required: true },
  },
  setup(props) {
    const { t } = useI18n();
    const { createDataset, createSnapshot, destroyDataset, refreshStateOnce, updateDatasetProperties } = useAppState();
    const selectedDataset = ref(null);
    const drawerOpen = ref(false);
    const fixedAdvancedOpen = ref(false);
    const customAdvancedOpen = ref(false);
    const draftValues = ref({});
    const detailDraftDirty = ref(false);
    const confirmDialogOpen = ref(false);
    const dialogPhase = ref("confirm");
    const dialogError = ref("");
    const dialogResults = ref([]);
    const dialogSummary = ref("");
    const submitting = ref(false);
    const propertyForce = ref(false);

    const createDrawerOpen = ref(false);
    const createAdvancedOpen = ref(false);
    const createConfirmDialogOpen = ref(false);
    const createDialogPhase = ref("confirm");
    const createDialogError = ref("");
    const createDialogSummary = ref("");
    const createDialogResult = ref(null);
    const createSubmitting = ref(false);
    const createDraft = ref(createDatasetDraft());
    // Keep live snapshot rebinding from wiping user edits mid-typing.
    const createDraftDirty = ref(false);
    const createParent = ref(null);
    const createForce = ref(false);
    const expandedRows = ref({});
    const showSnapshots = ref(false);
    const destroyConfirmDialogOpen = ref(false);
    const destroyDialogPhase = ref("confirm");
    const destroyDialogError = ref("");
    const destroyDialogSummary = ref("");
    const destroyDialogResult = ref(null);
    const destroySubmitting = ref(false);
    const snapshotDraftName = ref("");
    const snapshotConfirmDialogOpen = ref(false);
    const snapshotDialogPhase = ref("confirm");
    const snapshotDialogError = ref("");
    const snapshotDialogSummary = ref("");
    const snapshotDialogResult = ref(null);
    const snapshotSubmitting = ref(false);

    const pools = computed(() => {
      const value = props.state.snapshot.value?.data?.pools;
      return Array.isArray(value) ? value : [];
    });

    const rows = computed(() => {
      const value = props.state.snapshot.value?.data?.datasets;
      const items = Array.isArray(value) ? value : [];
      return items.map((dataset) => normalizeDataset(dataset, pools.value));
    });
    const filteredRows = computed(() =>
      showSnapshots.value ? rows.value : rows.value.filter((row) => row.type !== "snapshot")
    );
    const treeRows = computed(() => buildVisibleDatasetRows(filteredRows.value, expandedRows.value, t));

    const changedItems = computed(() => {
      const editable = selectedDataset.value?.customProperties?.all || [];
      return editable
        .map((property) => {
          const newValue = normalizeEditableValue(draftValues.value[property.name]);
          const oldValue = normalizeEditableValue(property.rawValue);
          if (newValue === oldValue) {
            return null;
          }
          return {
            property: property.name,
            old_value: property.rawValue ?? null,
            value: newValue,
          };
        })
        .filter(Boolean);
    });

    const createFieldGroups = computed(() => CREATE_PROPERTY_FIELDS[createDraft.value.type]);
    const createCommonFields = computed(() => createFieldGroups.value?.common || []);
    const createAdvancedFields = computed(() => createFieldGroups.value?.advanced || []);
    const createPayload = computed(() => ({
      parent: createDraft.value.parent,
      name: createDraft.value.name.trim(),
      type: createDraft.value.type,
      properties: buildCreateDatasetProperties(createDraft.value),
    }));
    const canDestroyDataset = computed(() => Boolean(selectedDataset.value?.name) && !isRootDataset(selectedDataset.value));
    const canCreateSnapshot = computed(() => {
      const datasetType = String(selectedDataset.value?.type || "");
      return Boolean(selectedDataset.value?.name) && datasetType !== "snapshot";
    });
    const canSubmitSnapshot = computed(() => Boolean(canCreateSnapshot.value && String(snapshotDraftName.value || "").trim()));
    const canSubmitCreate = computed(() => {
      if (!createPayload.value.parent || !createPayload.value.name) {
        return false;
      }
      if (createPayload.value.type === "volume") {
        return createPayload.value.properties.some((property) => property.name === "volsize" && property.value.trim());
      }
      return true;
    });

    const terminalLogLines = computed(() => buildCommandLogLines(dialogResults.value, "property"));
    const createTerminalLogLines = computed(() =>
      buildSingleCommandLogLines(createDialogResult.value, createPayload.value.name || "dataset")
    );
    const destroyTerminalLogLines = computed(() =>
      buildSingleCommandLogLines(destroyDialogResult.value, selectedDataset.value?.name || "dataset")
    );
    const snapshotTerminalLogLines = computed(() =>
      buildSingleCommandLogLines(snapshotDialogResult.value, snapshotDialogResult.value?.snapshot || "snapshot")
    );

    watch(
      () => props.state.snapshot.value?.meta?.last_updated,
      () => {
        if (selectedDataset.value?.name) {
          const updated = rows.value.find((dataset) => dataset.name === selectedDataset.value.name);
          if (!updated) {
            selectedDataset.value = null;
            draftValues.value = {};
            drawerOpen.value = false;
          } else {
            selectedDataset.value = updated;
            if (!submitting.value && !detailDraftDirty.value) {
              initializeDraft(updated);
            }
          }
        }

        if (createParent.value?.name) {
          const updatedParent = rows.value.find((dataset) => dataset.name === createParent.value.name);
          if (!updatedParent || updatedParent.type !== "filesystem") {
            createDrawerOpen.value = false;
            createParent.value = null;
          } else {
            createParent.value = updatedParent;
            // Rebind parent metadata without clobbering fields the user is editing.
            if (!createDraftDirty.value) {
              createDraft.value = {
                ...createDraft.value,
                parent: updatedParent.name,
              };
            }
          }
        }
      }
    );

    watch(
      rows,
      (nextRows) => {
        const nextExpanded = { ...expandedRows.value };
        for (const row of nextRows) {
          if (!(row.name in nextExpanded)) {
            nextExpanded[row.name] = true;
          }
        }
        expandedRows.value = nextExpanded;
      },
      { immediate: true }
    );

    function openDataset(row) {
      selectedDataset.value = row;
      fixedAdvancedOpen.value = false;
      customAdvancedOpen.value = false;
      initializeDraft(row);
      snapshotDraftName.value = row.type === "snapshot" ? "" : buildDefaultSnapshotName();
      resetDialogState();
      resetSnapshotDialogState();
      drawerOpen.value = true;
    }

    function toggleRow(rowName) {
      expandedRows.value = {
        ...expandedRows.value,
        [rowName]: !expandedRows.value[rowName],
      };
    }

    function openCreateDrawer(row) {
      createParent.value = row;
      createAdvancedOpen.value = false;
      createForce.value = false;
      createDraft.value = createDatasetDraft(row.name);
      resetCreateDialogState();
      createDrawerOpen.value = true;
    }

    function initializeDraft(dataset) {
      const nextDraft = {};
      for (const property of dataset?.customProperties?.all || []) {
        nextDraft[property.name] = normalizeEditableValue(property.rawValue);
      }
      draftValues.value = nextDraft;
      detailDraftDirty.value = false;
    }

    function resetDialogState() {
      dialogPhase.value = "confirm";
      dialogError.value = "";
      dialogResults.value = [];
      dialogSummary.value = "";
      submitting.value = false;
    }

    function resetCreateDialogState() {
      createDialogPhase.value = "confirm";
      createDialogError.value = "";
      createDialogSummary.value = "";
      createDialogResult.value = null;
      createSubmitting.value = false;
    }

    function resetDestroyDialogState() {
      destroyDialogPhase.value = "confirm";
      destroyDialogError.value = "";
      destroyDialogSummary.value = "";
      destroyDialogResult.value = null;
      destroySubmitting.value = false;
    }

    function resetSnapshotDialogState() {
      snapshotDialogPhase.value = "confirm";
      snapshotDialogError.value = "";
      snapshotDialogSummary.value = "";
      snapshotDialogResult.value = null;
      snapshotSubmitting.value = false;
    }

    function propertyInput(propertyName) {
      if (propertyName === "compression") {
        return {
          type: "select",
          options: buildCompressionOptions(selectedDataset.value, pools.value),
        };
      }
      return PROPERTY_INPUTS[propertyName] || { type: "text" };
    }

    function createPropertyInput(propertyName) {
      if (propertyName === "compression") {
        return {
          type: "select",
          options: buildCompressionCreateOptions(createDraft.value.type),
        };
      }
      return PROPERTY_INPUTS[propertyName] || { type: "text" };
    }

    function openConfirmDialog() {
      resetDialogState();
      confirmDialogOpen.value = true;
    }

    function openCreateConfirmDialog() {
      resetCreateDialogState();
      createConfirmDialogOpen.value = true;
    }

    function openDestroyConfirmDialog() {
      resetDestroyDialogState();
      destroyConfirmDialogOpen.value = true;
    }

    function openSnapshotConfirmDialog() {
      resetSnapshotDialogState();
      snapshotConfirmDialogOpen.value = true;
    }

    function setDraftValues(value) {
      draftValues.value = value;
      detailDraftDirty.value = true;
    }

    function setCreateDraft(value) {
      createDraft.value = value;
      createDraftDirty.value = true;
    }

    function setSnapshotDraftName(value) {
      snapshotDraftName.value = String(value || "");
    }

    async function confirmPropertyChanges() {
      if (!selectedDataset.value?.name || !changedItems.value.length) {
        return;
      }

      submitting.value = true;
      dialogPhase.value = "submitting";
      dialogError.value = "";
      dialogSummary.value = "";
      dialogResults.value = [];

      try {
        const response = await updateDatasetProperties(selectedDataset.value.name, changedItems.value);
        dialogResults.value = Array.isArray(response?.results) ? response.results : [];
        dialogSummary.value = response?.refreshed
          ? t("datasets.summary.propertiesAppliedAndRefreshed")
          : t("datasets.summary.propertiesAppliedRefreshFailed");
        if (response?.refresh_error) {
          dialogError.value = response.refresh_error;
        }
        dialogPhase.value = "result";
        await refreshStateOnce();
        detailDraftDirty.value = false;
      } catch (error) {
        dialogPhase.value = "result";
        dialogError.value = error instanceof Error ? error.message : String(error);
      } finally {
        submitting.value = false;
      }
    }

    async function confirmCreateDataset() {
      if (!canSubmitCreate.value) {
        return;
      }

      createSubmitting.value = true;
      createDialogPhase.value = "submitting";
      createDialogError.value = "";
      createDialogSummary.value = "";
      createDialogResult.value = null;

      try {
        const response = await createDataset(createPayload.value);
        createDialogResult.value = response;
        createDialogSummary.value = response?.refreshed
          ? t("datasets.summary.createSubmittedAndRefreshed")
          : t("datasets.summary.createSubmittedRefreshFailed");
        if (response?.refresh_error) {
          createDialogError.value = response.refresh_error;
        }
        createDialogPhase.value = "result";
        await refreshStateOnce();
        createDraftDirty.value = false;
      } catch (error) {
        createDialogPhase.value = "result";
        createDialogError.value = error instanceof Error ? error.message : String(error);
      } finally {
        createSubmitting.value = false;
      }
    }

    async function confirmCreateSnapshot() {
      if (!selectedDataset.value?.name || !canSubmitSnapshot.value) {
        return;
      }

      snapshotSubmitting.value = true;
      snapshotDialogPhase.value = "submitting";
      snapshotDialogError.value = "";
      snapshotDialogSummary.value = "";
      snapshotDialogResult.value = null;

      try {
        const response = await createSnapshot(selectedDataset.value.name, {
          name: String(snapshotDraftName.value || "").trim(),
          recursive: false,
        });
        snapshotDialogResult.value = response;
        snapshotDialogSummary.value = response?.refreshed
          ? t("datasets.summary.snapshotSubmittedAndRefreshed")
          : t("datasets.summary.snapshotSubmittedRefreshFailed");
        if (response?.refresh_error) {
          snapshotDialogError.value = response.refresh_error;
        }
        snapshotDialogPhase.value = "result";
        await refreshStateOnce();
        snapshotDraftName.value = buildDefaultSnapshotName();
      } catch (error) {
        snapshotDialogPhase.value = "result";
        snapshotDialogError.value = error instanceof Error ? error.message : String(error);
      } finally {
        snapshotSubmitting.value = false;
      }
    }

    async function confirmDestroyDataset() {
      if (!selectedDataset.value?.name || !canDestroyDataset.value) {
        return;
      }

      destroySubmitting.value = true;
      destroyDialogPhase.value = "submitting";
      destroyDialogError.value = "";
      destroyDialogSummary.value = "";
      destroyDialogResult.value = null;

      try {
        const response = await destroyDataset(selectedDataset.value.name);
        destroyDialogResult.value = response;
        destroyDialogSummary.value = response?.refreshed
          ? t("datasets.summary.destroySubmittedAndRefreshed")
          : t("datasets.summary.destroySubmittedRefreshFailed");
        if (response?.refresh_error) {
          destroyDialogError.value = response.refresh_error;
        }
        destroyDialogPhase.value = "result";
        await refreshStateOnce();
        detailDraftDirty.value = false;
      } catch (error) {
        destroyDialogPhase.value = "result";
        destroyDialogError.value = error instanceof Error ? error.message : String(error);
      } finally {
        destroySubmitting.value = false;
      }
    }

    return {
      canCreateSnapshot,
      canDestroyDataset,
      canSubmitCreate,
      canSubmitSnapshot,
      changedItems,
      confirmDestroyDataset,
      confirmCreateDataset,
      confirmCreateSnapshot,
      confirmDialogOpen,
      confirmPropertyChanges,
      createAdvancedFields,
      createAdvancedOpen,
      createCommonFields,
      createConfirmDialogOpen,
      createDialogError,
      createDialogPhase,
      createDialogResult,
      createDialogSummary,
      createDraft,
      createDrawerOpen,
      createForce,
      createParent,
      createPayload,
      createPropertyInput,
      createSubmitting,
      createTerminalLogLines,
      customAdvancedOpen,
      destroyConfirmDialogOpen,
      destroyDialogError,
      destroyDialogPhase,
      destroyDialogResult,
      destroyDialogSummary,
      destroySubmitting,
      destroyTerminalLogLines,
      dialogError,
      dialogPhase,
      dialogResults,
      dialogSummary,
      drawerOpen,
      draftValues,
      fixedAdvancedOpen,
      openConfirmDialog,
      openCreateConfirmDialog,
      openCreateDrawer,
      openDestroyConfirmDialog,
      openSnapshotConfirmDialog,
      openDataset,
      propertyForce,
      propertyInput,
      rows,
      selectedDataset,
      setCreateDraft,
      setDraftValues,
      setSnapshotDraftName,
      showSnapshots,
      snapshotConfirmDialogOpen,
      snapshotDialogError,
      snapshotDialogPhase,
      snapshotDialogResult,
      snapshotDialogSummary,
      snapshotDraftName,
      snapshotSubmitting,
      snapshotTerminalLogLines,
      submitting,
      terminalLogLines,
      t,
      toggleRow,
      treeRows,
    };
  },
};

function buildDefaultSnapshotName() {
  const now = new Date();
  const parts = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, "0"),
    String(now.getDate()).padStart(2, "0"),
  ];
  const time = [
    String(now.getHours()).padStart(2, "0"),
    String(now.getMinutes()).padStart(2, "0"),
    String(now.getSeconds()).padStart(2, "0"),
  ];
  return `manual-${parts.join("")}-${time.join("")}`;
}

function createDatasetDraft(parent = "") {
  return {
    parent,
    name: "",
    type: "filesystem",
    properties: {
      aclinherit: "",
      aclmode: "",
      acltype: "",
      compression: "",
      mountpoint: "",
      readonly: "",
      recordsize: "",
      canmount: "",
      casesensitivity: "",
      quota: "",
      reservation: "",
      sync: "",
      atime: "",
      checksum: "",
      copies: "",
      dedup: "",
      devices: "",
      dnodesize: "",
      exec: "",
      logbias: "",
      nbmand: "",
      normalization: "",
      overlay: "",
      primarycache: "",
      redundant_metadata: "",
      refquota: "",
      refreservation: "",
      relatime: "",
      secondarycache: "",
      setuid: "",
      snapdir: "",
      utf8only: "",
      xattr: "",
      volsize: "",
      volblocksize: "",
      volmode: "",
      snapdev: "",
    },
  };
}

function normalizeDataset(dataset, pools) {
  const normalized = {
    ...dataset,
    compressionDisplay: resolveDatasetCompression(dataset, pools),
  };

  return {
    ...normalized,
    fixedProperties: collectDatasetProperties(normalized, pools, false),
    customProperties: collectDatasetProperties(normalized, pools, true),
  };
}

function buildVisibleDatasetRows(rows, expandedRows, t) {
  const rowNames = new Set(rows.map((row) => row.name));
  const childCountByName = new Map();
  for (const row of rows) {
    const parentName = String(row.parentName || "");
    if (parentName && rowNames.has(parentName)) {
      childCountByName.set(parentName, (childCountByName.get(parentName) || 0) + 1);
    }
  }

  const visibleRows = [];
  let currentPoolName = "";
  for (const row of rows) {
    if (row.poolName !== currentPoolName) {
      currentPoolName = row.poolName;
      visibleRows.push({
        key: `group:${currentPoolName || row.name}`,
        entryType: "group",
        label: t("datasets.group.label", { name: currentPoolName || row.name }),
        meta: t("datasets.group.meta", { name: currentPoolName || row.name }),
      });
    }

    const ancestors = buildDatasetAncestorChain(row, rowNames);
    const hiddenByCollapsedAncestor = ancestors.some((ancestorName) => expandedRows[ancestorName] === false);
    if (hiddenByCollapsedAncestor) {
      continue;
    }

    visibleRows.push({
      key: `dataset:${row.name}`,
      entryType: "dataset",
      ...row,
      expanded: expandedRows[row.name] !== false,
      hasChildren: (childCountByName.get(row.name) || 0) > 0,
      typeLabel: datasetTypeLabel(row.type),
    });
  }

  return visibleRows;
}

function buildDatasetAncestorChain(row, rowNames) {
  const ancestors = [];
  let current = String(row?.parentName || "");
  while (current) {
    if (!rowNames.has(current)) {
      break;
    }
    ancestors.unshift(current);
    current = findDatasetParentName(current);
  }
  return ancestors;
}

function findDatasetParentName(name) {
  const normalized = String(name || "");
  if (!normalized) {
    return "";
  }
  const snapshotIndex = normalized.indexOf("@");
  if (snapshotIndex > 0) {
    return normalized.slice(0, snapshotIndex);
  }
  const separatorIndex = normalized.lastIndexOf("/");
  if (separatorIndex > 0) {
    return normalized.slice(0, separatorIndex);
  }
  return "";
}

function datasetTypeLabel(type) {
  if (type === "filesystem") {
    return "DS";
  }
  if (type === "volume") {
    return "ZV";
  }
  if (type === "snapshot") {
    return "SN";
  }
  return "??";
}

function collectDatasetProperties(dataset, pools, editable) {
  const properties = dataset && typeof dataset.properties === "object" && dataset.properties ? dataset.properties : {};
  const allowedEditableProperties = EDITABLE_DATASET_PROPERTIES[dataset?.type] || new Set();

  const entries = Object.entries(properties)
    .filter(([name]) => !EXCLUDED_DATASET_PROPERTIES.has(name))
    .filter(([name]) => allowedEditableProperties.has(name) === editable)
    .map(([name, property]) => ({
      name,
      value: formatDatasetPropertyValue(name, property?.value, dataset, pools),
      rawValue: property?.value ?? "",
      source: property?.source ?? "unknown",
    }))
    .sort((left, right) => left.name.localeCompare(right.name));

  if (editable) {
    const common = entries.filter((property) => COMMON_EDITABLE_DATASET_PROPERTIES.has(property.name));
    const advanced = entries.filter((property) => !COMMON_EDITABLE_DATASET_PROPERTIES.has(property.name));
    return {
      common,
      advanced,
      all: entries,
    };
  }

  return {
    common: entries.filter((property) => COMMON_FIXED_DATASET_PROPERTIES.has(property.name)),
    advanced: entries.filter((property) => !COMMON_FIXED_DATASET_PROPERTIES.has(property.name)),
  };
}

function formatDatasetPropertyValue(propertyName, value, dataset, pools) {
  if (propertyName === "compression") {
    return resolveDatasetCompression(
      {
        ...dataset,
        compression: value,
        properties: {
          ...(dataset?.properties || {}),
          compression: {
            ...(dataset?.properties?.compression || {}),
            value,
          },
        },
      },
      pools
    );
  }
  if (propertyName === "recordsize" || propertyName === "volblocksize") {
    return formatDatasetSizeProperty(value);
  }
  if (value === undefined || value === null || value === "") {
    return "-";
  }
  return String(value);
}

function normalizeEditableValue(value) {
  if (value === undefined || value === null) {
    return "";
  }
  return String(value);
}

function buildCompressionOptions() {
  return [
    { label: "Use default algorithm (on)", value: "on" },
    { label: "off", value: "off" },
    { label: "lz4", value: "lz4" },
    { label: "lzjb", value: "lzjb" },
    { label: "zstd", value: "zstd" },
    { label: "zstd-fast", value: "zstd-fast" },
    { label: "gzip", value: "gzip" },
    { label: "gzip-1", value: "gzip-1" },
    { label: "gzip-9", value: "gzip-9" },
    { label: "zle", value: "zle" },
  ].filter((option, index, items) => items.findIndex((entry) => entry.value === option.value) === index);
}

function buildCompressionCreateOptions(type) {
  const base = [
    { label: "Use default algorithm", value: "on" },
    { label: "off", value: "off" },
    { label: "lz4", value: "lz4" },
    { label: "lzjb", value: "lzjb" },
    { label: "zstd", value: "zstd" },
    { label: "zstd-fast", value: "zstd-fast" },
    { label: "gzip", value: "gzip" },
    { label: "gzip-1", value: "gzip-1" },
    { label: "gzip-9", value: "gzip-9" },
    { label: "zle", value: "zle" },
  ];
  if (type === "volume") {
    return base.filter((option) => option.value !== "zle");
  }
  return base;
}

function resolveDatasetCompression(dataset, pools) {
  const propertyValue = String(dataset?.properties?.compression?.value || dataset?.compression || "").trim().toLowerCase();
  if (!propertyValue) {
    return "none";
  }
  if (propertyValue === "off") {
    return "off";
  }
  if (propertyValue !== "on") {
    return propertyValue;
  }

  const pool = Array.isArray(pools)
    ? pools.find((item) => item?.name === dataset?.poolName)
    : null;
  const lz4Feature = String(pool?.properties?.["feature@lz4_compress"]?.value || "").trim().toLowerCase();
  return ["active", "enabled"].includes(lz4Feature) ? "lz4" : "lzjb";
}

function buildCreateDatasetProperties(createDraft) {
  const entries = Object.entries(createDraft.properties || {});
  return entries
    .filter(([, value]) => value !== undefined && value !== null && String(value).trim() !== "")
    .map(([name, value]) => ({ name, value: String(value).trim() }));
}

function isRootDataset(dataset) {
  return Boolean(dataset?.name) && Boolean(dataset?.poolName) && dataset.name === dataset.poolName;
}

function formatPowerOfTwoSize(bytes) {
  if (bytes < 1024) {
    return `${bytes}B`;
  }
  if (bytes < 1024 * 1024) {
    return `${bytes / 1024}K`;
  }
  return `${bytes / (1024 * 1024)}M`;
}

function formatDatasetSizeProperty(value) {
  if (value === undefined || value === null || value === "") {
    return "-";
  }

  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return String(value);
  }

  if (numeric % 1 !== 0) {
    return String(value);
  }

  return formatPowerOfTwoSize(numeric);
}

function buildCommandLogLines(results, primaryKey) {
  if (!Array.isArray(results) || !results.length) {
    return [];
  }

  return results.map((item, index) => ({
    key: `${item[primaryKey] || "item"}:${index}`,
    label: item[primaryKey] || "item",
    success: item.success,
    lines: [
      `$ ${item.command || "N/A"}`,
      item.exit_status !== null && item.exit_status !== undefined ? `exit_status: ${item.exit_status}` : null,
      item.stdout ? `stdout: ${item.stdout}` : null,
      item.stderr ? `stderr: ${item.stderr}` : null,
      !item.stdout && !item.stderr ? item.message : null,
    ].filter(Boolean),
  }));
}

function buildSingleCommandLogLines(result, label) {
  if (!result) {
    return [];
  }
  return [
    {
      key: `single:${label}`,
      label,
      success: result.success,
      lines: [
        `$ ${result.command || "N/A"}`,
        result.exit_status !== null && result.exit_status !== undefined ? `exit_status: ${result.exit_status}` : null,
        result.stdout ? `stdout: ${result.stdout}` : null,
        result.stderr ? `stderr: ${result.stderr}` : null,
        !result.stdout && !result.stderr ? result.message : null,
      ].filter(Boolean),
    },
  ];
}
</script>

<template>
  <section class="view-grid">
    <DatasetTreeTable
      :rows="rows"
      :tree-rows="treeRows"
      :show-snapshots="showSnapshots"
      @update:showSnapshots="showSnapshots = $event"
      @toggle-row="toggleRow"
      @open-create="openCreateDrawer"
      @open-dataset="openDataset"
    />

    <DatasetDetailDrawer
      v-model="drawerOpen"
      :selected-dataset="selectedDataset"
      :draft-values="draftValues"
      :changed-items="changedItems"
      :snapshot-draft-name="snapshotDraftName"
      :fixed-advanced-open="fixedAdvancedOpen"
      :custom-advanced-open="customAdvancedOpen"
      :can-destroy-dataset="canDestroyDataset"
      :can-create-snapshot="canCreateSnapshot"
      :can-submit-snapshot="canSubmitSnapshot"
      :property-force="propertyForce"
      :get-property-input="propertyInput"
      @update:draft-values="setDraftValues"
      @update:snapshot-draft-name="setSnapshotDraftName"
      @toggle-fixed-advanced="fixedAdvancedOpen = !fixedAdvancedOpen"
      @toggle-custom-advanced="customAdvancedOpen = !customAdvancedOpen"
      @open-confirm="openConfirmDialog"
      @open-destroy-confirm="openDestroyConfirmDialog"
      @open-snapshot-confirm="openSnapshotConfirmDialog"
    />

    <CreateDatasetDrawer
      v-model="createDrawerOpen"
      :create-parent="createParent"
      :create-draft="createDraft"
      :create-common-fields="createCommonFields"
      :create-advanced-fields="createAdvancedFields"
      :create-advanced-open="createAdvancedOpen"
      :create-force="createForce"
      :can-submit-create="canSubmitCreate"
      :get-property-input="createPropertyInput"
      @update:create-draft="setCreateDraft"
      @toggle-advanced="createAdvancedOpen = !createAdvancedOpen"
      @open-confirm="openCreateConfirmDialog"
    />

    <DatasetActionDialogs
      :selected-dataset="selectedDataset"
      :changed-items="changedItems"
      :confirm-dialog-open="confirmDialogOpen"
      :submitting="submitting"
      :dialog-phase="dialogPhase"
      :dialog-summary="dialogSummary"
      :dialog-error="dialogError"
      :dialog-results="dialogResults"
      :terminal-log-lines="terminalLogLines"
      :destroy-confirm-dialog-open="destroyConfirmDialogOpen"
      :destroy-submitting="destroySubmitting"
      :destroy-dialog-phase="destroyDialogPhase"
      :destroy-dialog-summary="destroyDialogSummary"
      :destroy-dialog-error="destroyDialogError"
      :destroy-dialog-result="destroyDialogResult"
      :destroy-terminal-log-lines="destroyTerminalLogLines"
      :create-confirm-dialog-open="createConfirmDialogOpen"
      :create-submitting="createSubmitting"
      :create-dialog-phase="createDialogPhase"
      :create-dialog-summary="createDialogSummary"
      :create-dialog-error="createDialogError"
      :create-dialog-result="createDialogResult"
      :create-terminal-log-lines="createTerminalLogLines"
      :can-submit-create="canSubmitCreate"
      :can-destroy-dataset="canDestroyDataset"
      :create-draft="createDraft"
      :create-payload="createPayload"
      :snapshot-draft-name="snapshotDraftName"
      :snapshot-confirm-dialog-open="snapshotConfirmDialogOpen"
      :snapshot-submitting="snapshotSubmitting"
      :snapshot-dialog-phase="snapshotDialogPhase"
      :snapshot-dialog-summary="snapshotDialogSummary"
      :snapshot-dialog-error="snapshotDialogError"
      :snapshot-dialog-result="snapshotDialogResult"
      :snapshot-terminal-log-lines="snapshotTerminalLogLines"
      :can-submit-snapshot="canSubmitSnapshot"
      @update:confirmDialogOpen="confirmDialogOpen = $event"
      @update:destroyConfirmDialogOpen="destroyConfirmDialogOpen = $event"
      @update:createConfirmDialogOpen="createConfirmDialogOpen = $event"
      @update:snapshotConfirmDialogOpen="snapshotConfirmDialogOpen = $event"
      @confirm-property="confirmPropertyChanges"
      @confirm-destroy="confirmDestroyDataset"
      @confirm-create="confirmCreateDataset"
      @confirm-snapshot="confirmCreateSnapshot"
    />
  </section>
</template>
