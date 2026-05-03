<script>
import { computed, ref, watch } from "vue";

import ConfirmDialog from "../components/common/ConfirmDialog.vue";
import DetailDrawer from "../components/common/DetailDrawer.vue";
import EmptyState from "../components/common/EmptyState.vue";
import { formatBytes, formatDateTime } from "../lib/formatters.js";
import { useAppState } from "../store/state.js";

const BOOLEAN_OPTIONS = [
  { label: "on", value: "on" },
  { label: "off", value: "off" },
];

const CANMOUNT_OPTIONS = [
  { label: "on", value: "on" },
  { label: "off", value: "off" },
  { label: "noauto", value: "noauto" },
];

const CACHE_OPTIONS = [
  { label: "all", value: "all" },
  { label: "metadata", value: "metadata" },
  { label: "none", value: "none" },
];

const SYNC_OPTIONS = [
  { label: "standard", value: "standard" },
  { label: "always", value: "always" },
  { label: "disabled", value: "disabled" },
];

const LOGBIAS_OPTIONS = [
  { label: "latency", value: "latency" },
  { label: "throughput", value: "throughput" },
];

const SNAPDIR_OPTIONS = [
  { label: "hidden", value: "hidden" },
  { label: "visible", value: "visible" },
];

const SNAPDEV_OPTIONS = [
  { label: "hidden", value: "hidden" },
  { label: "visible", value: "visible" },
];

const ACLTYPE_OPTIONS = [
  { label: "off", value: "off" },
  { label: "posix", value: "posix" },
  { label: "nfsv4", value: "nfsv4" },
];

const ACLINHERIT_OPTIONS = [
  { label: "discard", value: "discard" },
  { label: "noallow", value: "noallow" },
  { label: "restricted", value: "restricted" },
  { label: "passthrough", value: "passthrough" },
  { label: "passthrough-x", value: "passthrough-x" },
];

const ACLMODE_OPTIONS = [
  { label: "discard", value: "discard" },
  { label: "groupmask", value: "groupmask" },
  { label: "passthrough", value: "passthrough" },
  { label: "restricted", value: "restricted" },
];

const CASESENSITIVITY_OPTIONS = [
  { label: "sensitive", value: "sensitive" },
  { label: "insensitive", value: "insensitive" },
  { label: "mixed", value: "mixed" },
];

const NORMALIZATION_OPTIONS = [
  { label: "none", value: "none" },
  { label: "formC", value: "formC" },
  { label: "formD", value: "formD" },
  { label: "formKC", value: "formKC" },
  { label: "formKD", value: "formKD" },
];

const DEDUP_OPTIONS = [
  { label: "off", value: "off" },
  { label: "on", value: "on" },
  { label: "verify", value: "verify" },
];

const CHECKSUM_OPTIONS = [
  { label: "on", value: "on" },
  { label: "off", value: "off" },
  { label: "fletcher2", value: "fletcher2" },
  { label: "fletcher4", value: "fletcher4" },
  { label: "sha256", value: "sha256" },
  { label: "sha512", value: "sha512" },
  { label: "skein", value: "skein" },
  { label: "edonr", value: "edonr" },
];

const COPIES_OPTIONS = [
  { label: "1", value: "1" },
  { label: "2", value: "2" },
  { label: "3", value: "3" },
];

const DNODESIZE_OPTIONS = [
  { label: "legacy", value: "legacy" },
  { label: "auto", value: "auto" },
  { label: "1K", value: "1k" },
  { label: "2K", value: "2k" },
  { label: "4K", value: "4k" },
  { label: "8K", value: "8k" },
  { label: "16K", value: "16k" },
];

const REDUNDANT_METADATA_OPTIONS = [
  { label: "all", value: "all" },
  { label: "most", value: "most" },
  { label: "some", value: "some" },
  { label: "none", value: "none" },
];

const VOLMODE_OPTIONS = [
  { label: "default", value: "default" },
  { label: "full", value: "full" },
  { label: "dev", value: "dev" },
  { label: "none", value: "none" },
];

const RECORD_SIZE_OPTIONS = buildPowerOfTwoSizeOptions(512, 1024 * 1024);

const EDITABLE_DATASET_PROPERTIES = {
  filesystem: new Set([
    "aclinherit",
    "aclmode",
    "acltype",
    "atime",
    "canmount",
    "checksum",
    "compression",
    "copies",
    "dedup",
    "devices",
    "dnodesize",
    "exec",
    "logbias",
    "mountpoint",
    "nbmand",
    "overlay",
    "primarycache",
    "quota",
    "readonly",
    "recordsize",
    "redundant_metadata",
    "refquota",
    "refreservation",
    "relatime",
    "reservation",
    "secondarycache",
    "setuid",
    "snapdir",
    "sync",
    "xattr",
  ]),
  volume: new Set([
    "checksum",
    "compression",
    "copies",
    "dedup",
    "logbias",
    "primarycache",
    "readonly",
    "refreservation",
    "reservation",
    "secondarycache",
    "snapdev",
    "sync",
    "volmode",
    "volsize",
  ]),
  snapshot: new Set(),
};

const COMMON_FIXED_DATASET_PROPERTIES = new Set([
  "compressratio",
  "logicalreferenced",
  "logicalused",
  "mounted",
  "origin",
  "referenced",
  "usedbychildren",
  "usedbydataset",
  "usedbyrefreservation",
  "usedbysnapshots",
  "written",
]);

const COMMON_EDITABLE_DATASET_PROPERTIES = new Set([
  "canmount",
  "compression",
  "mountpoint",
  "quota",
  "readonly",
  "recordsize",
  "reservation",
  "volmode",
  "volsize",
]);

const EXCLUDED_DATASET_PROPERTIES = new Set([
  "available",
  "avail",
  "creation",
  "mounted",
  "name",
  "refer",
  "type",
  "used",
]);

const PROPERTY_INPUTS = {
  aclinherit: { type: "select", options: ACLINHERIT_OPTIONS },
  aclmode: { type: "select", options: ACLMODE_OPTIONS },
  acltype: { type: "select", options: ACLTYPE_OPTIONS },
  atime: { type: "select", options: BOOLEAN_OPTIONS },
  canmount: { type: "select", options: CANMOUNT_OPTIONS },
  casesensitivity: { type: "select", options: CASESENSITIVITY_OPTIONS },
  checksum: { type: "select", options: CHECKSUM_OPTIONS },
  copies: { type: "select", options: COPIES_OPTIONS },
  dedup: { type: "select", options: DEDUP_OPTIONS },
  devices: { type: "select", options: BOOLEAN_OPTIONS },
  dnodesize: { type: "select", options: DNODESIZE_OPTIONS },
  exec: { type: "select", options: BOOLEAN_OPTIONS },
  logbias: { type: "select", options: LOGBIAS_OPTIONS },
  mountpoint: { type: "text", placeholder: "/tank/data" },
  nbmand: { type: "select", options: BOOLEAN_OPTIONS },
  normalization: { type: "select", options: NORMALIZATION_OPTIONS },
  overlay: { type: "select", options: BOOLEAN_OPTIONS },
  primarycache: { type: "select", options: CACHE_OPTIONS },
  quota: { type: "text", placeholder: "none, 100G, 1T" },
  readonly: { type: "select", options: BOOLEAN_OPTIONS },
  recordsize: { type: "select", options: RECORD_SIZE_OPTIONS },
  redundant_metadata: { type: "select", options: REDUNDANT_METADATA_OPTIONS },
  refquota: { type: "text", placeholder: "none, 100G, 1T" },
  refreservation: { type: "text", placeholder: "none, 50G" },
  relatime: { type: "select", options: BOOLEAN_OPTIONS },
  reservation: { type: "text", placeholder: "none, 50G" },
  secondarycache: { type: "select", options: CACHE_OPTIONS },
  setuid: { type: "select", options: BOOLEAN_OPTIONS },
  snapdev: { type: "select", options: SNAPDEV_OPTIONS },
  snapdir: { type: "select", options: SNAPDIR_OPTIONS },
  sync: { type: "select", options: SYNC_OPTIONS },
  utf8only: { type: "select", options: BOOLEAN_OPTIONS },
  volblocksize: { type: "select", options: RECORD_SIZE_OPTIONS },
  volmode: { type: "select", options: VOLMODE_OPTIONS },
  volsize: { type: "text", placeholder: "10G, 500G, 2T" },
  xattr: {
    type: "select",
    options: [
      { label: "on", value: "on" },
      { label: "off", value: "off" },
      { label: "dir", value: "dir" },
      { label: "sa", value: "sa" },
    ],
  },
};

const CREATE_PROPERTY_FIELDS = {
  filesystem: {
    common: [
      "canmount",
      "compression",
      "mountpoint",
      "readonly",
      "recordsize",
      "quota",
      "reservation",
      "sync",
    ],
    advanced: [
      "aclinherit",
      "aclmode",
      "acltype",
      "atime",
      "casesensitivity",
      "checksum",
      "copies",
      "dedup",
      "devices",
      "dnodesize",
      "exec",
      "logbias",
      "nbmand",
      "normalization",
      "overlay",
      "primarycache",
      "redundant_metadata",
      "refquota",
      "refreservation",
      "relatime",
      "secondarycache",
      "setuid",
      "snapdir",
      "utf8only",
      "xattr",
    ],
  },
  volume: {
    common: [
      "volsize",
      "volblocksize",
      "volmode",
      "compression",
      "readonly",
      "reservation",
      "sync",
    ],
    advanced: [
      "checksum",
      "copies",
      "dedup",
      "logbias",
      "primarycache",
      "refreservation",
      "secondarycache",
      "snapdev",
    ],
  },
};

export default {
  components: {
    ConfirmDialog,
    DetailDrawer,
    EmptyState,
  },
  props: {
    state: { type: Object, required: true },
  },
  setup(props) {
    const { createDataset, destroyDataset, refreshStateOnce, updateDatasetProperties } = useAppState();
    const selectedDataset = ref(null);
    const drawerOpen = ref(false);
    const fixedAdvancedOpen = ref(false);
    const customAdvancedOpen = ref(false);
    const draftValues = ref({});
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

    const pools = computed(() => {
      const value = props.state.snapshot.value?.data?.pools;
      return Array.isArray(value) ? value : [];
    });

    const rows = computed(() => {
      const value = props.state.snapshot.value?.data?.datasets;
      const items = Array.isArray(value) ? value : [];
      return items.map((dataset) => normalizeDataset(dataset, pools.value));
    });
    // Hide snapshots before tree rendering so collapsed ancestors and sibling
    // ordering stay predictable when the inventory is busy.
    const filteredRows = computed(() =>
      showSnapshots.value ? rows.value : rows.value.filter((row) => row.type !== "snapshot")
    );
    const treeRows = computed(() => buildVisibleDatasetRows(filteredRows.value, expandedRows.value));

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
            if (!submitting.value && !changedItems.value.length) {
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
            createDraft.value = {
              ...createDraft.value,
              parent: updatedParent.name,
            };
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
      resetDialogState();
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
          ? "Dataset properties applied and state refreshed."
          : "Dataset properties applied, but the post-write refresh did not complete.";
        if (response?.refresh_error) {
          dialogError.value = response.refresh_error;
        }
        dialogPhase.value = "result";
        await refreshStateOnce();
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
          ? "Dataset creation submitted and state refreshed."
          : "Dataset creation submitted, but the post-create refresh did not complete.";
        if (response?.refresh_error) {
          createDialogError.value = response.refresh_error;
        }
        createDialogPhase.value = "result";
        await refreshStateOnce();
      } catch (error) {
        createDialogPhase.value = "result";
        createDialogError.value = error instanceof Error ? error.message : String(error);
      } finally {
        createSubmitting.value = false;
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
          ? "Dataset destroy submitted and state refreshed."
          : "Dataset destroy submitted, but the post-destroy refresh did not complete.";
        if (response?.refresh_error) {
          destroyDialogError.value = response.refresh_error;
        }
        destroyDialogPhase.value = "result";
        await refreshStateOnce();
      } catch (error) {
        destroyDialogPhase.value = "result";
        destroyDialogError.value = error instanceof Error ? error.message : String(error);
      } finally {
        destroySubmitting.value = false;
      }
    }

    return {
      canDestroyDataset,
      canSubmitCreate,
      changedItems,
      confirmDestroyDataset,
      confirmCreateDataset,
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
      formatBytes,
      formatDateTime,
      openConfirmDialog,
      openCreateConfirmDialog,
      openCreateDrawer,
      openDestroyConfirmDialog,
      openDataset,
      propertyForce,
      propertyInput,
      rows,
      selectedDataset,
      showSnapshots,
      submitting,
      terminalLogLines,
      toggleRow,
      treeRows,
    };
  },
  };

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

function buildVisibleDatasetRows(rows, expandedRows) {
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
        label: `Pool ${currentPoolName || row.name}`,
        meta: `${currentPoolName || row.name} datasets`,
      });
    }

    const ancestors = buildDatasetAncestorChain(row, rowNames);
    // Ancestor collapse state is evaluated against the backend-provided
    // hierarchy fields instead of recomputing display order on the client.
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

function datasetTypeRank(type) {
  if (type === "filesystem") {
    return 0;
  }
  if (type === "volume") {
    return 1;
  }
  if (type === "snapshot") {
    return 2;
  }
  return 3;
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

function buildCompressionOptions(dataset, pools) {
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

function buildPowerOfTwoSizeOptions(min, max) {
  const options = [];
  for (let value = min; value <= max; value *= 2) {
    options.push({
      label: formatPowerOfTwoSize(value),
      value: formatPowerOfTwoSize(value),
    });
  }
  return options;
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
      <article class="surface-panel">
        <div class="section-header">
          <div>
            <h3>Dataset Inventory</h3>
            <p>Filesystem and volume inventory with manage and create workflows.</p>
          </div>
          <label class="inline-checkbox">
            <input v-model="showSnapshots" type="checkbox" />
            <span>Show snapshots</span>
          </label>
        </div>

        <EmptyState
          v-if="!rows.length"
          title="No datasets discovered"
          description="The current snapshot did not report any datasets."
        />

        <div v-else class="table-shell">
          <table class="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Mountpoint</th>
                <th>Used</th>
                <th>Available</th>
                <th>Compression</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <template v-for="row in treeRows" :key="row.key">
                <tr v-if="row.entryType === 'group'" class="dataset-group-row">
                  <td colspan="7">
                    <div class="dataset-group-header">
                      <strong>{{ row.label }}</strong>
                      <span class="subtle-text">{{ row.meta }}</span>
                    </div>
                  </td>
                </tr>
                <tr v-else>
                  <td>
                    <div class="dataset-name-cell" :style="{ paddingLeft: (row.depth * 18) + 'px' }">
                      <button
                        v-if="row.hasChildren"
                        type="button"
                        class="dataset-name-toggle"
                        :data-expanded="row.expanded ? 'true' : 'false'"
                        :aria-label="row.expanded ? 'Collapse dataset' : 'Expand dataset'"
                        @click="toggleRow(row.name)"
                      >
                        ▶
                      </button>
                      <span v-else class="dataset-name-toggle-placeholder"></span>
                      <span class="dataset-type-pill" :data-type="row.type">{{ row.typeLabel }}</span>
                      <div class="dataset-name-stack">
                        <div class="dataset-name-main">
                          <strong>{{ row.shortName }}</strong>
                          <span v-if="row.depth === 0" class="dataset-root-badge">root</span>
                        </div>
                        <span class="subtle-text">{{ row.name }}</span>
                      </div>
                    </div>
                  </td>
                  <td>{{ row.type }}</td>
                  <td>{{ row.mountpoint || '-' }}</td>
                  <td>{{ formatBytes(row.used) }}</td>
                  <td>{{ formatBytes(row.avail) }}</td>
                  <td>{{ row.compressionDisplay }}</td>
                  <td class="action-cell">
                    <div class="inline-button-row">
                      <button
                        v-if="row.type === 'filesystem'"
                        type="button"
                        class="ghost-button"
                        @click="openCreateDrawer(row)"
                      >
                        New
                      </button>
                      <button type="button" class="ghost-button" @click="openDataset(row)">Manage</button>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
        </div>
      </article>

      <DetailDrawer
        v-model="drawerOpen"
        title="Dataset Details"
        :description="selectedDataset?.name || ''"
      >
        <div v-if="selectedDataset" class="drawer-section-list">
          <section class="drawer-section">
            <h4>Overview</h4>
            <dl class="detail-grid">
              <div><dt>Type</dt><dd>{{ selectedDataset.type }}</dd></div>
              <div><dt>Mountpoint</dt><dd>{{ selectedDataset.mountpoint || '-' }}</dd></div>
              <div><dt>Used</dt><dd>{{ formatBytes(selectedDataset.used) }}</dd></div>
              <div><dt>Available</dt><dd>{{ formatBytes(selectedDataset.avail) }}</dd></div>
              <div><dt>Referenced</dt><dd>{{ formatBytes(selectedDataset.refer) }}</dd></div>
              <div><dt>Compression</dt><dd>{{ selectedDataset.compressionDisplay }}</dd></div>
              <div><dt>Created</dt><dd>{{ formatDateTime(Number(selectedDataset.creation || 0) * 1000) }}</dd></div>
              <div><dt>Readonly</dt><dd>{{ selectedDataset.readonly || '-' }}</dd></div>
            </dl>
          </section>

          <section class="drawer-section">
            <div class="drawer-section-header">
              <div>
                <h4>Fixed Properties</h4>
                <p class="subtle-text">Read-only properties for the current dataset.</p>
              </div>
            </div>

            <dl v-if="selectedDataset.fixedProperties.common.length" class="detail-grid">
              <div v-for="property in selectedDataset.fixedProperties.common" :key="'fixed:' + property.name">
                <dt>{{ property.name }}</dt>
                <dd>{{ property.value }} <span class="subtle-text">({{ property.source }})</span></dd>
              </div>
            </dl>
            <p v-else class="subtle-text">No common fixed properties were reported.</p>

            <div class="advanced-toggle-row">
              <button type="button" class="ghost-button" @click="fixedAdvancedOpen = !fixedAdvancedOpen">
                {{ fixedAdvancedOpen ? "Hide Advanced" : "Advanced" }}
              </button>
            </div>

            <dl v-if="fixedAdvancedOpen && selectedDataset.fixedProperties.advanced.length" class="detail-grid advanced-detail-grid">
              <div v-for="property in selectedDataset.fixedProperties.advanced" :key="'fixed-advanced:' + property.name">
                <dt>{{ property.name }}</dt>
                <dd>{{ property.value }} <span class="subtle-text">({{ property.source }})</span></dd>
              </div>
            </dl>
            <p v-else-if="fixedAdvancedOpen" class="subtle-text">No advanced fixed properties were reported.</p>
          </section>

          <section class="drawer-section">
            <div class="drawer-section-header">
              <div>
                <h4>Custom Properties</h4>
                <p class="subtle-text">Editable dataset properties. Changes follow the same confirm-and-refresh flow as pools.</p>
              </div>
              <div class="inline-action-controls">
                <label
                  class="inline-checkbox"
                  data-disabled="true"
                  title="zfs set does not provide a force flag."
                >
                  <input v-model="propertyForce" type="checkbox" disabled />
                  <span>Force</span>
                </label>
                <button type="button" class="primary-button" :disabled="!changedItems.length" @click="openConfirmDialog">
                  Apply Changes
                </button>
              </div>
            </div>

            <dl v-if="selectedDataset.customProperties.common.length" class="detail-grid editable-detail-grid">
              <div v-for="property in selectedDataset.customProperties.common" :key="'custom:' + property.name" class="editable-property-card">
                <dt>{{ property.name }}</dt>
                <dd>
                  <select
                    v-if="propertyInput(property.name).type === 'select'"
                    v-model="draftValues[property.name]"
                    class="property-field"
                  >
                    <option
                      v-for="option in propertyInput(property.name).options"
                      :key="property.name + ':' + option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                  <input
                    v-else
                    v-model="draftValues[property.name]"
                    type="text"
                    class="property-field"
                    :placeholder="propertyInput(property.name).placeholder || ''"
                  />
                  <span class="property-meta">
                    Current: {{ property.value }} <span class="subtle-text">({{ property.source }})</span>
                  </span>
                </dd>
              </div>
            </dl>
            <p v-else class="subtle-text">No common editable properties are available for this dataset type.</p>

            <div class="advanced-toggle-row">
              <button type="button" class="ghost-button" @click="customAdvancedOpen = !customAdvancedOpen">
                {{ customAdvancedOpen ? "Hide Advanced" : "Advanced" }}
              </button>
            </div>

            <dl v-if="customAdvancedOpen && selectedDataset.customProperties.advanced.length" class="detail-grid editable-detail-grid advanced-detail-grid">
              <div v-for="property in selectedDataset.customProperties.advanced" :key="'custom-advanced:' + property.name" class="editable-property-card">
                <dt>{{ property.name }}</dt>
                <dd>
                  <select
                    v-if="propertyInput(property.name).type === 'select'"
                    v-model="draftValues[property.name]"
                    class="property-field"
                  >
                    <option
                      v-for="option in propertyInput(property.name).options"
                      :key="property.name + ':advanced:' + option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                  <input
                    v-else
                    v-model="draftValues[property.name]"
                    type="text"
                    class="property-field"
                    :placeholder="propertyInput(property.name).placeholder || ''"
                  />
                  <span class="property-meta">
                    Current: {{ property.value }} <span class="subtle-text">({{ property.source }})</span>
                  </span>
                </dd>
              </div>
            </dl>
            <p v-else-if="customAdvancedOpen" class="subtle-text">No advanced editable properties are available for this dataset type.</p>
          </section>

          <section class="drawer-section">
            <div class="drawer-section-header">
              <div>
                <h4>Danger Zone</h4>
                <p class="subtle-text">
                  Permanently delete this {{ selectedDataset.type === 'volume' ? 'zvol' : selectedDataset.type }} with the same SSH confirmation flow.
                </p>
              </div>
              <button
                type="button"
                class="danger-button"
                :disabled="!canDestroyDataset"
                @click="openDestroyConfirmDialog"
              >
                Delete
              </button>
            </div>
            <p v-if="!canDestroyDataset" class="subtle-text">
              Root datasets are protected here. Use pool destroy from the Pools view if you really need to remove the whole pool.
            </p>
          </section>
        </div>
      </DetailDrawer>

      <DetailDrawer
        v-model="createDrawerOpen"
        title="Create Child Dataset"
        :description="createParent?.name || ''"
      >
        <div class="drawer-section-list">
          <section class="drawer-section">
            <h4>Basics</h4>
            <div class="topology-form-grid">
              <label class="form-field">
                <span>Parent</span>
                <input :value="createDraft.parent" type="text" class="property-field" disabled />
              </label>
              <label class="form-field">
                <span>Type</span>
                <select v-model="createDraft.type" class="property-field">
                  <option value="filesystem">dataset</option>
                  <option value="volume">zvol</option>
                </select>
              </label>
              <label class="form-field">
                <span>Name</span>
                <input v-model="createDraft.name" type="text" class="property-field" placeholder="media" />
              </label>
            </div>
          </section>

          <section class="drawer-section">
            <div class="drawer-section-header">
              <div>
                <h4>Properties</h4>
                <p class="subtle-text">Choose properties for the new {{ createDraft.type === 'volume' ? 'zvol' : 'dataset' }}.</p>
              </div>
              <div class="inline-action-controls">
                <label
                  class="inline-checkbox"
                  data-disabled="true"
                  title="zfs create does not provide a force flag in this workflow."
                >
                  <input v-model="createForce" type="checkbox" disabled />
                  <span>Force</span>
                </label>
                <button type="button" class="primary-button" :disabled="!canSubmitCreate" @click="openCreateConfirmDialog">
                  Create
                </button>
              </div>
            </div>

            <dl class="detail-grid editable-detail-grid">
              <div v-for="name in createCommonFields" :key="'create:' + name" class="editable-property-card">
                <dt>{{ name }}</dt>
                <dd>
                  <select
                    v-if="createPropertyInput(name).type === 'select'"
                    v-model="createDraft.properties[name]"
                    class="property-field"
                  >
                    <option value="">Default</option>
                    <option
                      v-for="option in createPropertyInput(name).options"
                      :key="'create:' + name + ':' + option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                  <input
                    v-else
                    v-model="createDraft.properties[name]"
                    type="text"
                    class="property-field"
                    :placeholder="createPropertyInput(name).placeholder || ''"
                  />
                </dd>
              </div>
            </dl>

            <div class="advanced-toggle-row">
              <button type="button" class="ghost-button" @click="createAdvancedOpen = !createAdvancedOpen">
                {{ createAdvancedOpen ? "Hide Advanced" : "Advanced" }}
              </button>
            </div>

            <dl v-if="createAdvancedOpen" class="detail-grid editable-detail-grid advanced-detail-grid">
              <div v-for="name in createAdvancedFields" :key="'create-advanced:' + name" class="editable-property-card">
                <dt>{{ name }}</dt>
                <dd>
                  <select
                    v-if="createPropertyInput(name).type === 'select'"
                    v-model="createDraft.properties[name]"
                    class="property-field"
                  >
                    <option value="">Default</option>
                    <option
                      v-for="option in createPropertyInput(name).options"
                      :key="'create-advanced:' + name + ':' + option.value"
                      :value="option.value"
                    >
                      {{ option.label }}
                    </option>
                  </select>
                  <input
                    v-else
                    v-model="createDraft.properties[name]"
                    type="text"
                    class="property-field"
                    :placeholder="createPropertyInput(name).placeholder || ''"
                  />
                </dd>
              </div>
            </dl>
          </section>
        </div>
      </DetailDrawer>

      <ConfirmDialog
        v-model="confirmDialogOpen"
        :busy="submitting"
        :can-confirm="Boolean(changedItems.length)"
        :result-mode="dialogPhase === 'result'"
        :confirm-text="dialogPhase === 'submitting' ? 'Applying...' : 'Confirm Apply'"
        title="Confirm Dataset Property Changes"
        :description="selectedDataset?.name || ''"
        @confirm="confirmPropertyChanges"
      >
        <div v-if="dialogPhase === 'confirm'" class="dialog-section-list">
          <p class="subtle-text">These dataset property changes will be sent to the host after confirmation.</p>
          <ul class="result-list">
            <li v-for="item in changedItems" :key="item.property" class="result-list-item">
              <strong>{{ item.property }}</strong>
              <span class="subtle-text">{{ item.old_value ?? '-' }} -> {{ item.value }}</span>
            </li>
          </ul>
        </div>

        <div v-else-if="dialogPhase === 'submitting'" class="dialog-section-list">
          <div class="progress-shell">
            <div class="progress-spinner"></div>
            <div>
              <strong>Applying dataset property changes...</strong>
              <p class="subtle-text">Please wait while the backend updates the dataset and refreshes the latest state.</p>
            </div>
          </div>
        </div>

        <div v-else class="dialog-section-list">
          <p v-if="dialogSummary" class="notice-text">{{ dialogSummary }}</p>
          <p v-if="dialogError" class="error-text">{{ dialogError }}</p>

          <section>
            <h4 class="dialog-mini-heading">Result List</h4>
            <ul class="result-list" v-if="dialogResults.length">
              <li v-for="item in dialogResults" :key="item.property" class="result-list-item">
                <div class="result-list-head">
                  <strong>{{ item.property }}</strong>
                  <span class="inline-status" :data-health="item.success ? 'ONLINE' : 'DEGRADED'">
                    {{ item.success ? "Success" : "Failed" }}
                  </span>
                </div>
                <p class="subtle-text">{{ item.message }}</p>
              </li>
            </ul>
            <p v-else class="subtle-text">No result rows were returned.</p>
          </section>

          <section>
            <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
            <div v-if="terminalLogLines.length" class="terminal-log-list">
              <article v-for="entry in terminalLogLines" :key="entry.key" class="terminal-log-card">
                <div class="result-list-head">
                  <strong>{{ entry.label }}</strong>
                  <span class="inline-status" :data-health="entry.success ? 'ONLINE' : 'DEGRADED'">
                    {{ entry.success ? "OK" : "Error" }}
                  </span>
                </div>
                <pre class="terminal-log-block">{{ entry.lines.join('\n') }}</pre>
              </article>
            </div>
            <p v-else class="subtle-text">No SSH logs are available for this submission.</p>
          </section>
        </div>
      </ConfirmDialog>

      <ConfirmDialog
        v-model="destroyConfirmDialogOpen"
        :busy="destroySubmitting"
        :can-confirm="canDestroyDataset"
        :result-mode="destroyDialogPhase === 'result'"
        :confirm-text="destroyDialogPhase === 'submitting' ? 'Deleting...' : 'Confirm Delete'"
        title="Confirm Dataset Delete"
        :description="selectedDataset?.name || ''"
        @confirm="confirmDestroyDataset"
      >
        <div v-if="destroyDialogPhase === 'confirm'" class="dialog-section-list">
          <p class="error-text">This will run zfs destroy on the selected dataset and cannot be undone.</p>
          <ul class="result-list">
            <li class="result-list-item">
              <strong>Type</strong>
              <span class="subtle-text">{{ selectedDataset?.type || '-' }}</span>
            </li>
            <li class="result-list-item">
              <strong>Name</strong>
              <span class="subtle-text">{{ selectedDataset?.name || '-' }}</span>
            </li>
          </ul>
        </div>

        <div v-else-if="destroyDialogPhase === 'submitting'" class="dialog-section-list">
          <div class="progress-shell">
            <div class="progress-spinner"></div>
            <div>
              <strong>Deleting dataset...</strong>
              <p class="subtle-text">Please wait while the backend runs zfs destroy and refreshes the latest state.</p>
            </div>
          </div>
        </div>

        <div v-else class="dialog-section-list">
          <p v-if="destroyDialogSummary" class="notice-text">{{ destroyDialogSummary }}</p>
          <p v-if="destroyDialogError" class="error-text">{{ destroyDialogError }}</p>

          <section>
            <h4 class="dialog-mini-heading">Result</h4>
            <ul class="result-list" v-if="destroyDialogResult">
              <li class="result-list-item">
                <div class="result-list-head">
                  <strong>{{ destroyDialogResult.dataset }}</strong>
                  <span class="inline-status" :data-health="destroyDialogResult.success ? 'ONLINE' : 'DEGRADED'">
                    {{ destroyDialogResult.success ? "Success" : "Failed" }}
                  </span>
                </div>
                <p class="subtle-text">{{ destroyDialogResult.message }}</p>
              </li>
            </ul>
            <p v-else class="subtle-text">No result was returned.</p>
          </section>

          <section>
            <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
            <div v-if="destroyTerminalLogLines.length" class="terminal-log-list">
              <article v-for="entry in destroyTerminalLogLines" :key="entry.key" class="terminal-log-card">
                <div class="result-list-head">
                  <strong>{{ entry.label }}</strong>
                  <span class="inline-status" :data-health="entry.success ? 'ONLINE' : 'DEGRADED'">
                    {{ entry.success ? "OK" : "Error" }}
                  </span>
                </div>
                <pre class="terminal-log-block">{{ entry.lines.join('\n') }}</pre>
              </article>
            </div>
            <p v-else class="subtle-text">No SSH logs are available for this submission.</p>
          </section>
        </div>
      </ConfirmDialog>

      <ConfirmDialog
        v-model="createConfirmDialogOpen"
        :busy="createSubmitting"
        :can-confirm="canSubmitCreate"
        :result-mode="createDialogPhase === 'result'"
        :confirm-text="createDialogPhase === 'submitting' ? 'Creating...' : 'Confirm Create'"
        title="Confirm Dataset Creation"
        :description="createPayload.parent ? createPayload.parent + '/' + createPayload.name : 'New child dataset'"
        @confirm="confirmCreateDataset"
      >
        <div v-if="createDialogPhase === 'confirm'" class="dialog-section-list">
          <p class="subtle-text">This will run a zfs create command on the remote host.</p>
          <ul class="result-list">
            <li class="result-list-item">
              <strong>Type</strong>
              <span class="subtle-text">{{ createDraft.type === 'volume' ? 'zvol' : 'dataset' }}</span>
            </li>
            <li class="result-list-item">
              <strong>Full Name</strong>
              <span class="subtle-text">{{ createPayload.parent }}/{{ createPayload.name }}</span>
            </li>
            <li class="result-list-item">
              <strong>Properties</strong>
              <span class="subtle-text">{{ createPayload.properties.length ? createPayload.properties.map((item) => item.name + '=' + item.value).join(', ') : 'Default properties only' }}</span>
            </li>
          </ul>
        </div>

        <div v-else-if="createDialogPhase === 'submitting'" class="dialog-section-list">
          <div class="progress-shell">
            <div class="progress-spinner"></div>
            <div>
              <strong>Creating {{ createDraft.type === 'volume' ? 'zvol' : 'dataset' }}...</strong>
              <p class="subtle-text">Please wait while the backend runs zfs create and refreshes the latest state.</p>
            </div>
          </div>
        </div>

        <div v-else class="dialog-section-list">
          <p v-if="createDialogSummary" class="notice-text">{{ createDialogSummary }}</p>
          <p v-if="createDialogError" class="error-text">{{ createDialogError }}</p>

          <section>
            <h4 class="dialog-mini-heading">Result</h4>
            <ul class="result-list" v-if="createDialogResult">
              <li class="result-list-item">
                <div class="result-list-head">
                  <strong>{{ createDialogResult.dataset }}</strong>
                  <span class="inline-status" :data-health="createDialogResult.success ? 'ONLINE' : 'DEGRADED'">
                    {{ createDialogResult.success ? "Success" : "Failed" }}
                  </span>
                </div>
                <p class="subtle-text">{{ createDialogResult.message }}</p>
              </li>
            </ul>
            <p v-else class="subtle-text">No result was returned.</p>
          </section>

          <section>
            <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
            <div v-if="createTerminalLogLines.length" class="terminal-log-list">
              <article v-for="entry in createTerminalLogLines" :key="entry.key" class="terminal-log-card">
                <div class="result-list-head">
                  <strong>{{ entry.label }}</strong>
                  <span class="inline-status" :data-health="entry.success ? 'ONLINE' : 'DEGRADED'">
                    {{ entry.success ? "OK" : "Error" }}
                  </span>
                </div>
                <pre class="terminal-log-block">{{ entry.lines.join('\n') }}</pre>
              </article>
            </div>
            <p v-else class="subtle-text">No SSH logs are available for this submission.</p>
          </section>
        </div>
      </ConfirmDialog>
    </section>
</template>
