import { computed, nextTick, ref, watch } from "vue";

import ConfirmDialog from "../components/common/ConfirmDialog.js";
import DetailDrawer from "../components/common/DetailDrawer.js";
import EmptyState from "../components/common/EmptyState.js";
import { formatBytes, formatPercent } from "../lib/formatters.js";
import { useAppState } from "../store/state.js";

const EDITABLE_POOL_PROPERTIES = new Set([
  "autoexpand",
  "autoreplace",
  "autotrim",
  "bootfs",
  "cachefile",
  "comment",
  "delegation",
  "failmode",
  "listsnapshots",
  "multihost",
]);

const COMMON_READONLY_POOL_PROPERTIES = new Set([
  "ashift",
  "altroot",
  "bootsize",
  "checkpoint",
  "expandsize",
  "guid",
  "readonly",
  "version",
]);

const BOOLEAN_OPTIONS = [
  { label: "on", value: "on" },
  { label: "off", value: "off" },
];

const FAILMODE_OPTIONS = [
  { label: "wait", value: "wait" },
  { label: "continue", value: "continue" },
  { label: "panic", value: "panic" },
];

const CREATE_POOL_PROPERTY_OPTIONS = {
  ashift: {
    label: "ashift",
    type: "select",
    options: [
      { label: "12", value: "12" },
      { label: "13", value: "13" },
    ],
  },
  autoexpand: { label: "autoexpand", type: "select", options: BOOLEAN_OPTIONS },
  autoreplace: { label: "autoreplace", type: "select", options: BOOLEAN_OPTIONS },
  autotrim: { label: "autotrim", type: "select", options: BOOLEAN_OPTIONS },
  failmode: { label: "failmode", type: "select", options: FAILMODE_OPTIONS },
  comment: { label: "comment", type: "text", placeholder: "Optional pool comment" },
};

const CREATE_DATA_LAYOUT_OPTIONS = [
  { label: "Stripe", value: "stripe" },
  { label: "Mirror", value: "mirror" },
  { label: "RAIDZ", value: "raidz" },
  { label: "RAIDZ2", value: "raidz2" },
  { label: "RAIDZ3", value: "raidz3" },
];

const TOPOLOGY_CATEGORY_OPTIONS = [
  { label: "Log / ZIL", value: "log" },
  { label: "Cache / L2ARC", value: "cache" },
  { label: "Special", value: "special" },
  { label: "Dedup", value: "dedup" },
  { label: "Spare", value: "spare" },
];

const TOPOLOGY_LAYOUT_OPTIONS = {
  log: [
    { label: "Stripe", value: "stripe" },
    { label: "Mirror", value: "mirror" },
  ],
  cache: [{ label: "Stripe", value: "stripe" }],
  special: [
    { label: "Stripe", value: "stripe" },
    { label: "Mirror", value: "mirror" },
  ],
  dedup: [
    { label: "Stripe", value: "stripe" },
    { label: "Mirror", value: "mirror" },
  ],
  spare: [{ label: "Stripe", value: "stripe" }],
};

const PROPERTY_INPUTS = {
  autoexpand: { type: "select", options: BOOLEAN_OPTIONS },
  autoreplace: { type: "select", options: BOOLEAN_OPTIONS },
  autotrim: { type: "select", options: BOOLEAN_OPTIONS },
  bootfs: { type: "select", options: [] },
  cachefile: { type: "text", placeholder: "Enter cachefile path or none" },
  comment: { type: "text", placeholder: "Enter pool comment" },
  delegation: { type: "select", options: BOOLEAN_OPTIONS },
  failmode: { type: "select", options: FAILMODE_OPTIONS },
  listsnapshots: { type: "select", options: BOOLEAN_OPTIONS },
  multihost: { type: "select", options: BOOLEAN_OPTIONS },
};

const TopologyNode = {
  name: "TopologyNode",
  props: {
    node: { type: Object, required: true },
  },
  computed: {
    isLeaf() {
      return !Array.isArray(this.node.children) || !this.node.children.length;
    },
    displayState() {
      return resolveTopologyState(this.node);
    },
    displayRead() {
      return resolveTopologyMetric(this.node, "read");
    },
    displayWrite() {
      return resolveTopologyMetric(this.node, "write");
    },
    displayCksum() {
      return resolveTopologyMetric(this.node, "cksum");
    },
  },
  template: `
    <li class="topology-node">
      <div class="topology-line">
        <div class="topology-main-line">
          <strong>{{ node.displayName || node.name }}</strong>
          <span v-if="isLeaf && node.diskId" class="topology-disk-id">{{ node.diskId }}</span>
        </div>
        <div class="topology-meta-line">
          <span class="inline-status" :data-health="displayState">{{ displayState }}</span>
          <span v-if="isLeaf" class="subtle-text">Pool status</span>
          <span>R {{ displayRead }}</span>
          <span>W {{ displayWrite }}</span>
          <span>C {{ displayCksum }}</span>
        </div>
      </div>
      <ul v-if="Array.isArray(node.children) && node.children.length" class="topology-children">
        <TopologyNode v-for="child in node.children" :key="child.name + ':' + (child.diskId || '')" :node="child" />
      </ul>
    </li>
  `,
};
TopologyNode.components = { TopologyNode };

export default {
  components: {
    ConfirmDialog,
    DetailDrawer,
    EmptyState,
    TopologyNode,
  },
  props: {
    state: { type: Object, required: true },
  },
  setup(props) {
    const { createPool, destroyPool, removePoolTarget, updatePoolProperties, updatePoolTopology, refreshStateOnce } = useAppState();
    const selectedPool = ref(null);
    const drawerOpen = ref(false);
    const topologyDrawerOpen = ref(false);
    const createPoolDrawerOpen = ref(false);
    const expandedRows = ref({});
    const advancedReadonlyOpen = ref(false);
    const confirmDialogOpen = ref(false);
    const topologyConfirmDialogOpen = ref(false);
    const createPoolConfirmDialogOpen = ref(false);
    const draftValues = ref({});
    const topologyDraft = ref(createTopologyDraft());
    const createPoolStep = ref("basic");
    const createPoolDraft = ref(createPoolWizardDraft());
    const dialogPhase = ref("confirm");
    const dialogError = ref("");
    const dialogResults = ref([]);
    const dialogSummary = ref("");
    const submitting = ref(false);
    const topologyDialogPhase = ref("confirm");
    const topologyDialogError = ref("");
    const topologyDialogResults = ref([]);
    const topologyDialogSummary = ref("");
    const topologySubmitting = ref(false);
    const createPoolDialogPhase = ref("confirm");
    const createPoolDialogError = ref("");
    const createPoolDialogSummary = ref("");
    const createPoolDialogResult = ref(null);
    const createPoolSubmitting = ref(false);
    const destroyConfirmDialogOpen = ref(false);
    const destroyDialogPhase = ref("confirm");
    const destroyDialogError = ref("");
    const destroyDialogSummary = ref("");
    const destroyDialogResult = ref(null);
    const destroySubmitting = ref(false);
    const removeConfirmDialogOpen = ref(false);
    const removeDialogPhase = ref("confirm");
    const removeDialogError = ref("");
    const removeDialogSummary = ref("");
    const removeDialogResult = ref(null);
    const removeSubmitting = ref(false);
    const selectedRemovalTarget = ref(null);

    const pools = computed(() => {
      const value = props.state.snapshot.value?.data?.pools;
      return Array.isArray(value) ? value : [];
    });

    const datasets = computed(() => {
      const value = props.state.snapshot.value?.data?.datasets;
      return Array.isArray(value) ? value : [];
    });

    const allDisks = computed(() => {
      const value = props.state.snapshot.value?.data?.disks;
      return Array.isArray(value) ? value : [];
    });

    const normalizedPools = computed(() =>
      pools.value.map((pool) => ({
        ...pool,
        immutableProperties: collectPoolProperties(pool, false),
        editableProperties: collectPoolProperties(pool, true),
        quickFacts: buildPoolQuickFacts(pool),
      }))
    );

    const bootfsOptions = computed(() => {
      if (!selectedPool.value?.name) {
        return [{ label: "none", value: "none" }];
      }

      const options = datasets.value
        .filter((dataset) => dataset.poolName === selectedPool.value.name && dataset.type === "filesystem")
        .map((dataset) => ({
          label: dataset.name,
          value: dataset.name,
        }))
        .sort((left, right) => left.label.localeCompare(right.label));

      return [{ label: "none", value: "none" }, ...options];
    });

    const changedItems = computed(() => {
      if (!selectedPool.value || !Array.isArray(selectedPool.value.editableProperties)) {
        return [];
      }

      return selectedPool.value.editableProperties
        .map((property) => {
          const newValue = normalizeEditableValue(property.name, draftValues.value[property.name]);
          const oldValue = normalizeEditableValue(property.name, property.rawValue);
          if (newValue === oldValue) {
            return null;
          }
          return {
            property: property.name,
            oldValue,
            newValue,
            old_value: oldValue,
            value: newValue,
          };
        })
        .filter(Boolean);
    });

    const topologyGroupSummary = computed(() => {
      const groups = selectedPool.value?.topologySummary;
      return Array.isArray(groups) ? groups : [];
    });

    const topologyLayoutOptions = computed(() => TOPOLOGY_LAYOUT_OPTIONS[topologyDraft.value.category] || []);

    const availableTopologyDevices = computed(() => {
      const devices = selectedPool.value?.availableTopologyDevices;
      if (!Array.isArray(devices)) {
        return [];
      }
      const category = topologyDraft.value.category;
      return devices.filter((device) => {
        const supported = Array.isArray(device.supportedVdevClasses) ? device.supportedVdevClasses : [];
        return !supported.length || supported.includes(category);
      });
    });

    const topologyPendingAdditions = computed(() => {
      const devices = Array.isArray(topologyDraft.value.devices) ? topologyDraft.value.devices.filter(Boolean) : [];
      if (!selectedPool.value || !devices.length) {
        return [];
      }

      return [
        {
          category: topologyDraft.value.category,
          layout: topologyDraft.value.layout,
          devices,
        },
      ];
    });

    const topologySelectionSummary = computed(() =>
      availableTopologyDevices.value.filter((device) => topologyDraft.value.devices.includes(device.path))
    );

    const topologyConfirmSummary = computed(() =>
      topologyPendingAdditions.value.map((item) => ({
        ...item,
        deviceLabels: item.devices.map((path) => {
          const device = availableTopologyDevices.value.find((entry) => entry.path === path);
          return device ? formatTopologyDeviceLabel(device) : path;
        }),
      }))
    );

    const createPoolPropertyFields = computed(() => Object.entries(CREATE_POOL_PROPERTY_OPTIONS));

    const createPoolStepItems = [
      { key: "basic", label: "Basic" },
      { key: "data", label: "Data VDEVs" },
      { key: "aux", label: "Extra Classes" },
      { key: "review", label: "Review" },
    ];

    const createPoolDataLayoutOptions = computed(() => CREATE_DATA_LAYOUT_OPTIONS);
    const createPoolAuxLayoutOptions = computed(() => TOPOLOGY_LAYOUT_OPTIONS[createPoolDraft.value.auxBuilder.category] || []);

    const createPoolUsedPaths = computed(() => {
      const selected = new Set();
      for (const vdev of createPoolDraft.value.dataVdevs) {
        for (const path of vdev.devices) {
          selected.add(path);
        }
      }
      for (const vdev of createPoolDraft.value.auxVdevs) {
        for (const path of vdev.devices) {
          selected.add(path);
        }
      }
      return selected;
    });

    const createPoolAvailableDataDevices = computed(() =>
      allDisks.value.filter((disk) => isDiskAvailableForCreate(disk) && allowPathForBuilder(disk.path, createPoolUsedPaths.value, createPoolDraft.value.dataBuilder.devices))
    );

    const createPoolAvailableAuxDevices = computed(() =>
      allDisks.value.filter((disk) => isDiskAvailableForCreate(disk) && allowPathForBuilder(disk.path, createPoolUsedPaths.value, createPoolDraft.value.auxBuilder.devices))
    );

    const createPoolDataSelectionSummary = computed(() =>
      createPoolAvailableDataDevices.value.filter((device) => createPoolDraft.value.dataBuilder.devices.includes(device.path))
    );

    const createPoolAuxSelectionSummary = computed(() =>
      createPoolAvailableAuxDevices.value.filter((device) => createPoolDraft.value.auxBuilder.devices.includes(device.path))
    );

    const createPoolPayload = computed(() => ({
      name: createPoolDraft.value.name.trim(),
      properties: buildCreatePoolProperties(createPoolDraft.value.properties),
      vdevs: [
        ...createPoolDraft.value.dataVdevs.map((vdev) => ({ ...vdev })),
        ...createPoolDraft.value.auxVdevs.map((vdev) => ({ ...vdev })),
      ],
    }));

    const createPoolReviewGroups = computed(() => [
      { label: "Data VDEVs", items: createPoolDraft.value.dataVdevs },
      { label: "Extra Classes", items: createPoolDraft.value.auxVdevs },
    ]);

    const canAdvanceCreatePool = computed(() => {
      if (createPoolStep.value === "basic") {
        return Boolean(createPoolDraft.value.name.trim());
      }
      if (createPoolStep.value === "data") {
        return Boolean(createPoolDraft.value.dataVdevs.length);
      }
      if (createPoolStep.value === "aux") {
        return true;
      }
      return Boolean(createPoolPayload.value.name) && Boolean(createPoolPayload.value.vdevs.length);
    });

    const canSubmitCreatePool = computed(() => Boolean(createPoolPayload.value.name) && createPoolDraft.value.dataVdevs.length > 0);

    const createPoolTerminalLogLines = computed(() => buildSingleCommandLogLines(createPoolDialogResult.value, createPoolDraft.value.name || "pool"));
    const destroyTerminalLogLines = computed(() => buildSingleCommandLogLines(destroyDialogResult.value, selectedPool.value?.name || "pool"));
    const removeTerminalLogLines = computed(() => buildSingleCommandLogLines(removeDialogResult.value, selectedRemovalTarget.value?.displayLabel || "target"));

    const terminalLogLines = computed(() => buildCommandLogLines(dialogResults.value, "property"));
    const topologyTerminalLogLines = computed(() => buildCommandLogLines(topologyDialogResults.value, "category"));

    watch(
      () => props.state.snapshot.value?.meta?.last_updated,
      () => {
        if (!selectedPool.value?.name) {
          return;
        }

        const updated = normalizedPools.value.find((pool) => pool.name === selectedPool.value.name);
        if (!updated) {
          drawerOpen.value = false;
          topologyDrawerOpen.value = false;
          selectedPool.value = null;
          draftValues.value = {};
          topologyDraft.value = createTopologyDraft();
          return;
        }

        selectedPool.value = updated;
        if (!submitting.value && !changedItems.value.length) {
          initializeDraft(updated);
        }
      }
    );

    watch(
      () => topologyDraft.value.category,
      (category) => {
        const options = TOPOLOGY_LAYOUT_OPTIONS[category] || [];
        if (!options.some((option) => option.value === topologyDraft.value.layout)) {
          topologyDraft.value = {
            ...topologyDraft.value,
            layout: options[0]?.value || "stripe",
          };
        }
      }
    );

    watch(
      () => createPoolDraft.value.auxBuilder.category,
      (category) => {
        const options = TOPOLOGY_LAYOUT_OPTIONS[category] || [];
        if (!options.some((option) => option.value === createPoolDraft.value.auxBuilder.layout)) {
          createPoolDraft.value = {
            ...createPoolDraft.value,
            auxBuilder: {
              ...createPoolDraft.value.auxBuilder,
              layout: options[0]?.value || "stripe",
            },
          };
        }
      }
    );

    function openPool(pool) {
      selectedPool.value = pool;
      advancedReadonlyOpen.value = false;
      initializeDraft(pool);
      resetDialogState();
      drawerOpen.value = true;
    }

    function openTopologyEditor(pool) {
      selectedPool.value = pool;
      initializeTopologyDraft(pool);
      resetTopologyDialogState();
      topologyDrawerOpen.value = true;
    }

    function openCreatePoolWizard() {
      initializeCreatePoolDraft();
      resetCreatePoolDialogState();
      createPoolStep.value = "basic";
      createPoolDrawerOpen.value = true;
    }

    function initializeDraft(pool) {
      const nextDraft = {};
      const editableProperties = Array.isArray(pool.editableProperties) ? pool.editableProperties : [];
      for (const property of editableProperties) {
        nextDraft[property.name] = normalizeEditableValue(property.name, property.rawValue);
      }
      draftValues.value = nextDraft;
    }

    function initializeTopologyDraft(pool) {
      const currentCategory = topologyDraft.value.category;
      const currentLayout = topologyDraft.value.layout;
      const currentDevices = Array.isArray(topologyDraft.value.devices) ? topologyDraft.value.devices : [];
      const allowedCategories = TOPOLOGY_CATEGORY_OPTIONS.map((option) => option.value);
      const category = allowedCategories.includes(currentCategory) ? currentCategory : "log";
      const layoutOptions = TOPOLOGY_LAYOUT_OPTIONS[category] || [];
      const layout = layoutOptions.some((option) => option.value === currentLayout)
        ? currentLayout
        : (layoutOptions[0]?.value || "stripe");
      const availablePaths = new Set(
        Array.isArray(pool?.availableTopologyDevices)
          ? pool.availableTopologyDevices.map((device) => device.path)
          : []
      );

      topologyDraft.value = {
        category,
        layout,
        devices: currentDevices.filter((path) => availablePaths.has(path)),
      };
    }

    function initializeCreatePoolDraft() {
      createPoolDraft.value = createPoolWizardDraft();
    }

    function resetDialogState() {
      dialogPhase.value = "confirm";
      dialogError.value = "";
      dialogResults.value = [];
      dialogSummary.value = "";
      submitting.value = false;
    }

    function resetTopologyDialogState() {
      topologyDialogPhase.value = "confirm";
      topologyDialogError.value = "";
      topologyDialogResults.value = [];
      topologyDialogSummary.value = "";
      topologySubmitting.value = false;
    }

    function resetCreatePoolDialogState() {
      createPoolDialogPhase.value = "confirm";
      createPoolDialogError.value = "";
      createPoolDialogSummary.value = "";
      createPoolDialogResult.value = null;
      createPoolSubmitting.value = false;
    }

    function resetDestroyDialogState() {
      destroyDialogPhase.value = "confirm";
      destroyDialogError.value = "";
      destroyDialogSummary.value = "";
      destroyDialogResult.value = null;
      destroySubmitting.value = false;
    }

    function resetRemoveDialogState() {
      removeDialogPhase.value = "confirm";
      removeDialogError.value = "";
      removeDialogSummary.value = "";
      removeDialogResult.value = null;
      removeSubmitting.value = false;
    }

    function toggleRow(pool) {
      const key = pool.name;
      expandedRows.value = {
        ...expandedRows.value,
        [key]: !expandedRows.value[key],
      };
    }

    function isExpanded(pool) {
      return Boolean(expandedRows.value[pool.name]);
    }

    function propertyInput(propertyName) {
      if (propertyName === "bootfs") {
        return {
          type: "select",
          options: bootfsOptions.value,
        };
      }
      return PROPERTY_INPUTS[propertyName] || { type: "text" };
    }

    function openConfirmDialog() {
      if (!changedItems.value.length || submitting.value) {
        return;
      }
      resetDialogState();
      confirmDialogOpen.value = true;
    }

    function openTopologyConfirmDialog() {
      if (!topologyPendingAdditions.value.length || topologySubmitting.value) {
        return;
      }
      resetTopologyDialogState();
      topologyConfirmDialogOpen.value = true;
    }

    function openDestroyPoolConfirmDialog() {
      if (!selectedPool.value?.name || destroySubmitting.value) {
        return;
      }
      resetDestroyDialogState();
      destroyConfirmDialogOpen.value = true;
    }

    function openRemoveTargetConfirmDialog(target) {
      if (!target || removeSubmitting.value) {
        return;
      }
      selectedRemovalTarget.value = target;
      resetRemoveDialogState();
      removeConfirmDialogOpen.value = true;
    }

    function toggleTopologyDevice(path) {
      const current = new Set(topologyDraft.value.devices);
      if (current.has(path)) {
        current.delete(path);
      } else {
        current.add(path);
      }
      topologyDraft.value = {
        ...topologyDraft.value,
        devices: Array.from(current).sort(),
      };
    }

    function topologyDeviceSelected(path) {
      return topologyDraft.value.devices.includes(path);
    }

    function resetCreatePoolBuilderSelections() {
      // Clear transient builder selections when the user walks backwards in the
      // wizard so temporary picks do not silently overlap with later steps.
      createPoolDraft.value = {
        ...createPoolDraft.value,
        dataBuilder: {
          ...createPoolDraft.value.dataBuilder,
          devices: [],
        },
        auxBuilder: {
          ...createPoolDraft.value.auxBuilder,
          devices: [],
        },
      };
    }

    function setCreatePoolStep(step) {
      const steps = createPoolStepItems.map((item) => item.key);
      const currentIndex = steps.indexOf(createPoolStep.value);
      const targetIndex = steps.indexOf(step);
      if (targetIndex >= 0 && currentIndex >= 0 && targetIndex < currentIndex) {
        resetCreatePoolBuilderSelections();
      }
      createPoolStep.value = step;
    }

    function nextCreatePoolStep() {
      const steps = createPoolStepItems.map((item) => item.key);
      const currentIndex = steps.indexOf(createPoolStep.value);
      if (currentIndex >= 0 && currentIndex < steps.length - 1 && canAdvanceCreatePool.value) {
        createPoolStep.value = steps[currentIndex + 1];
      }
    }

    function previousCreatePoolStep() {
      const steps = createPoolStepItems.map((item) => item.key);
      const currentIndex = steps.indexOf(createPoolStep.value);
      if (currentIndex > 0) {
        resetCreatePoolBuilderSelections();
        createPoolStep.value = steps[currentIndex - 1];
      }
    }

    function toggleCreatePoolDevice(builderKey, path) {
      const builder = createPoolDraft.value[builderKey];
      const current = new Set(builder.devices);
      if (current.has(path)) {
        current.delete(path);
      } else {
        current.add(path);
      }
      createPoolDraft.value = {
        ...createPoolDraft.value,
        [builderKey]: {
          ...builder,
          devices: Array.from(current).sort(),
        },
      };
    }

    function createPoolDeviceSelected(builderKey, path) {
      return createPoolDraft.value[builderKey].devices.includes(path);
    }

    function getRemovalTarget(item) {
      const targets = Array.isArray(selectedPool.value?.removalTargets) ? selectedPool.value.removalTargets : [];
      return (
        targets.find(
          (target) => target.commandTarget === item.name && target.vdevClass === item.vdevClass && target.nodeKind === item.nodeKind
        ) || null
      );
    }

    function addCreatePoolVdev(builderKey) {
      const builder = createPoolDraft.value[builderKey];
      if (!builder.devices.length) {
        return;
      }
      const targetKey = builderKey === "dataBuilder" ? "dataVdevs" : "auxVdevs";
      createPoolDraft.value = {
        ...createPoolDraft.value,
        [targetKey]: [
          ...createPoolDraft.value[targetKey],
          {
            category: builder.category,
            layout: builder.layout,
            devices: [...builder.devices],
          },
        ],
        [builderKey]: {
          ...builder,
          devices: [],
        },
      };
    }

    function removeCreatePoolVdev(targetKey, index) {
      createPoolDraft.value = {
        ...createPoolDraft.value,
        [targetKey]: createPoolDraft.value[targetKey].filter((_, itemIndex) => itemIndex !== index),
      };
    }

    function openCreatePoolConfirmDialog() {
      if (!canSubmitCreatePool.value || createPoolSubmitting.value) {
        return;
      }
      resetCreatePoolDialogState();
      createPoolConfirmDialogOpen.value = true;
    }

    async function confirmSave() {
      if (!selectedPool.value || !changedItems.value.length) {
        return;
      }

      dialogPhase.value = "submitting";
      dialogError.value = "";
      dialogSummary.value = "";
      dialogResults.value = [];
      submitting.value = true;

      try {
        const response = await updatePoolProperties(selectedPool.value.name, changedItems.value);
        dialogResults.value = Array.isArray(response.results) ? response.results : [];

        const successCount = dialogResults.value.filter((item) => item.success).length;
        const failureCount = dialogResults.value.length - successCount;
        dialogSummary.value = `Submitted ${dialogResults.value.length} changes. Success: ${successCount}. Failed: ${failureCount}.`;

        if (response.refresh_error) {
          dialogError.value = `State refresh failed: ${response.refresh_error}`;
        }

        await rebindSelectedPool();
      } catch (error) {
        dialogError.value = error instanceof Error ? error.message : String(error);
        try {
          await refreshStateOnce();
        } catch {
          // Keep submit error as primary.
        }
      } finally {
        submitting.value = false;
        dialogPhase.value = "result";
      }
    }

    async function confirmTopologySave() {
      if (!selectedPool.value || !topologyPendingAdditions.value.length) {
        return;
      }

      topologyDialogPhase.value = "submitting";
      topologyDialogError.value = "";
      topologyDialogSummary.value = "";
      topologyDialogResults.value = [];
      topologySubmitting.value = true;

      try {
        const response = await updatePoolTopology(selectedPool.value.name, topologyPendingAdditions.value);
        topologyDialogResults.value = Array.isArray(response.results) ? response.results : [];

        const successCount = topologyDialogResults.value.filter((item) => item.success).length;
        const failureCount = topologyDialogResults.value.length - successCount;
        topologyDialogSummary.value = `Submitted ${topologyDialogResults.value.length} topology update. Success: ${successCount}. Failed: ${failureCount}.`;

        if (response.refresh_error) {
          topologyDialogError.value = `State refresh failed: ${response.refresh_error}`;
        }

        await rebindSelectedPool();
        initializeTopologyDraft(selectedPool.value);
      } catch (error) {
        topologyDialogError.value = error instanceof Error ? error.message : String(error);
        try {
          await refreshStateOnce();
        } catch {
          // Keep submit error as primary.
        }
      } finally {
        topologySubmitting.value = false;
        topologyDialogPhase.value = "result";
      }
    }

    async function confirmCreatePool() {
      if (!canSubmitCreatePool.value) {
        return;
      }

      createPoolDialogPhase.value = "submitting";
      createPoolDialogError.value = "";
      createPoolDialogSummary.value = "";
      createPoolDialogResult.value = null;
      createPoolSubmitting.value = true;

      try {
        const response = await createPool(createPoolPayload.value);
        createPoolDialogResult.value = response;
        createPoolDialogSummary.value = response.success
          ? "Pool creation command completed successfully."
          : "Pool creation command failed.";

        if (response.refresh_error) {
          createPoolDialogError.value = `State refresh failed: ${response.refresh_error}`;
        }

        try {
          await refreshStateOnce();
        } catch (refreshError) {
          if (!createPoolDialogError.value) {
            createPoolDialogError.value = refreshError instanceof Error ? refreshError.message : String(refreshError);
          }
        }
      } catch (error) {
        createPoolDialogError.value = error instanceof Error ? error.message : String(error);
        try {
          await refreshStateOnce();
        } catch {
          // Keep create error as primary.
        }
      } finally {
        createPoolSubmitting.value = false;
        createPoolDialogPhase.value = "result";
      }
    }

    async function confirmDestroyPool() {
      if (!selectedPool.value?.name) {
        return;
      }

      destroyDialogPhase.value = "submitting";
      destroyDialogError.value = "";
      destroyDialogSummary.value = "";
      destroyDialogResult.value = null;
      destroySubmitting.value = true;

      try {
        const response = await destroyPool(selectedPool.value.name);
        destroyDialogResult.value = response;
        destroyDialogSummary.value = response.success
          ? "Pool destroy command completed successfully."
          : "Pool destroy command failed.";

        if (response.refresh_error) {
          destroyDialogError.value = `State refresh failed: ${response.refresh_error}`;
        }

        try {
          await refreshStateOnce();
        } catch (refreshError) {
          if (!destroyDialogError.value) {
            destroyDialogError.value = refreshError instanceof Error ? refreshError.message : String(refreshError);
          }
        }
      } catch (error) {
        destroyDialogError.value = error instanceof Error ? error.message : String(error);
        try {
          await refreshStateOnce();
        } catch {
          // Keep destroy error as primary.
        }
      } finally {
        destroySubmitting.value = false;
        destroyDialogPhase.value = "result";
      }
    }

    async function confirmRemoveTarget() {
      if (!selectedPool.value?.name || !selectedRemovalTarget.value?.commandTarget) {
        return;
      }

      removeDialogPhase.value = "submitting";
      removeDialogError.value = "";
      removeDialogSummary.value = "";
      removeDialogResult.value = null;
      removeSubmitting.value = true;

      try {
        const response = await removePoolTarget(selectedPool.value.name, selectedRemovalTarget.value.commandTarget);
        removeDialogResult.value = response;
        removeDialogSummary.value = response.success
          ? "Topology remove command completed successfully."
          : "Topology remove command failed.";

        if (response.refresh_error) {
          removeDialogError.value = `State refresh failed: ${response.refresh_error}`;
        }

        await rebindSelectedPool();
        if (selectedPool.value) {
          initializeTopologyDraft(selectedPool.value);
        }
      } catch (error) {
        removeDialogError.value = error instanceof Error ? error.message : String(error);
        try {
          await refreshStateOnce();
        } catch {
          // Keep remove error as primary.
        }
      } finally {
        removeSubmitting.value = false;
        removeDialogPhase.value = "result";
      }
    }

    async function rebindSelectedPool() {
      try {
        // After a write completes we re-fetch once over REST, then rebind the
        // selected row from the normalized pool list. This avoids waiting for
        // WebSocket timing and keeps the drawer aligned with the new snapshot.
        await refreshStateOnce();
        await nextTick();
        const updatedPool = normalizedPools.value.find((pool) => pool.name === selectedPool.value?.name);
        if (updatedPool) {
          selectedPool.value = updatedPool;
          initializeDraft(updatedPool);
        }
      } catch (refreshError) {
        const message = refreshError instanceof Error ? refreshError.message : String(refreshError);
        if (!dialogError.value && dialogPhase.value === "submitting") {
          dialogError.value = message;
        }
        if (!topologyDialogError.value && topologyDialogPhase.value === "submitting") {
          topologyDialogError.value = message;
        }
      }
    }

    return {
      advancedReadonlyOpen,
      availableTopologyDevices,
      canAdvanceCreatePool,
      canSubmitCreatePool,
      changedItems,
      confirmDialogOpen,
      confirmCreatePool,
      confirmDestroyPool,
      confirmRemoveTarget,
      confirmSave,
      confirmTopologySave,
      createPoolAuxLayoutOptions,
      createPoolAvailableAuxDevices,
      createPoolAvailableDataDevices,
      createPoolConfirmDialogOpen,
      createPoolDataLayoutOptions,
      createPoolDataSelectionSummary,
      createPoolDeviceSelected,
      createPoolDialogError,
      createPoolDialogPhase,
      createPoolDialogResult,
      createPoolDialogSummary,
      createPoolDrawerOpen,
      createPoolDraft,
      createPoolPayload,
      createPoolPropertyFields,
      createPoolReviewGroups,
      createPoolStep,
      createPoolStepItems,
      createPoolSubmitting,
      createPoolTerminalLogLines,
      createPoolAuxSelectionSummary,
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
      draftValues,
      drawerOpen,
      isExpanded,
      normalizedPools,
      openConfirmDialog,
      openCreatePoolConfirmDialog,
      openCreatePoolWizard,
      openDestroyPoolConfirmDialog,
      openPool,
      openRemoveTargetConfirmDialog,
      openTopologyConfirmDialog,
      openTopologyEditor,
      pools,
      previousCreatePoolStep,
      propertyInput,
      selectedPool,
      setCreatePoolStep,
      submitting,
      terminalLogLines,
      toggleCreatePoolDevice,
      toggleRow,
      topologyCategoryOptions: TOPOLOGY_CATEGORY_OPTIONS,
      topologyConfirmDialogOpen,
      topologyConfirmSummary,
      topologyDeviceSelected,
      topologyDialogError,
      topologyDialogPhase,
      topologyDialogResults,
      topologyDialogSummary,
      topologyDrawerOpen,
      topologyDraft,
      topologyGroupSummary,
      topologyLayoutOptions,
      topologyPendingAdditions,
      topologySelectionSummary,
      topologySubmitting,
      topologyTerminalLogLines,
      toggleTopologyDevice,
      addCreatePoolVdev,
      removeCreatePoolVdev,
      removeConfirmDialogOpen,
      removeDialogError,
      removeDialogPhase,
      removeDialogResult,
      removeDialogSummary,
      removeSubmitting,
      removeTerminalLogLines,
      selectedRemovalTarget,
      nextCreatePoolStep,
      formatTopologyDeviceLabel,
      getRemovalTarget,
      formatBytes,
      formatPercent,
    };
  },
  template: `
    <section class="view-grid">
      <article class="surface-panel">
        <div class="section-header">
          <div>
            <h3>Pool Overview</h3>
            <p>Capacity, health, and topology details for each storage pool.</p>
          </div>
          <button type="button" class="primary-button" @click="openCreatePoolWizard">Create Pool</button>
        </div>

        <EmptyState
          v-if="!pools.length"
          title="No pools discovered"
          description="The current snapshot did not report any ZFS pools."
        />

        <div v-else class="table-shell">
          <table class="data-table">
            <thead>
              <tr>
                <th></th>
                <th>Name</th>
                <th>Health</th>
                <th>Size</th>
                <th>Allocated</th>
                <th>Free</th>
                <th>Capacity</th>
                <th>Fragmentation</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <template v-for="pool in normalizedPools" :key="pool.name">
                <tr>
                  <td>
                    <button
                      type="button"
                      class="row-toggle"
                      :data-expanded="isExpanded(pool)"
                      @click="toggleRow(pool)"
                    >
                      ▸
                    </button>
                  </td>
                  <td><strong>{{ pool.name }}</strong></td>
                  <td><span class="inline-status" :data-health="pool.health">{{ pool.health }}</span></td>
                  <td>{{ formatBytes(pool.size) }}</td>
                  <td>{{ formatBytes(pool.allocated) }}</td>
                  <td>{{ formatBytes(pool.free) }}</td>
                  <td>{{ formatPercent(pool.capacity) }}</td>
                  <td>{{ formatPercent(pool.fragmentation) }}</td>
                  <td class="action-cell">
                    <button type="button" class="ghost-button" @click="openPool(pool)">View</button>
                  </td>
                </tr>
                <tr v-if="isExpanded(pool)" class="pool-expand-row">
                  <td colspan="9">
                    <div class="pool-expand-shell">
                      <section class="pool-expand-panel">
                        <div class="pool-panel-header">
                          <h4>Topology</h4>
                          <button type="button" class="ghost-button" @click="openTopologyEditor(pool)">Edit Topology</button>
                        </div>
                        <ul class="topology-list" v-if="pool.status && Array.isArray(pool.status.config) && pool.status.config.length">
                          <TopologyNode v-for="node in pool.status.config" :key="node.name" :node="node" />
                        </ul>
                        <p v-else class="subtle-text">No topology reported for this pool.</p>
                      </section>

                      <section class="pool-expand-panel">
                        <div class="pool-panel-header">
                          <h4>Quick Facts</h4>
                          <button
                            type="button"
                            class="danger-button"
                            :disabled="destroySubmitting"
                            @click="selectedPool = pool; openDestroyPoolConfirmDialog()"
                          >
                            Destroy Pool
                          </button>
                        </div>
                        <dl class="pool-quick-grid">
                          <div v-for="fact in pool.quickFacts" :key="fact.label">
                            <dt>{{ fact.label }}</dt>
                            <dd>{{ fact.value }}</dd>
                          </div>
                        </dl>
                      </section>
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
        title="Pool Details"
        :description="selectedPool ? selectedPool.name : ''"
      >
        <div v-if="selectedPool" class="drawer-section-list">
          <section class="drawer-section">
            <h4>Read-only Properties</h4>
            <dl class="detail-grid">
              <div v-for="property in selectedPool.immutableProperties.common" :key="property.name">
                <dt>{{ property.name }}</dt>
                <dd>{{ property.value }} <span class="subtle-text">({{ property.source }})</span></dd>
              </div>
            </dl>
            <p v-if="!selectedPool.immutableProperties.common.length" class="subtle-text">
              No additional read-only properties were reported.
            </p>
            <div v-if="selectedPool.immutableProperties.advanced.length" class="advanced-toggle-row">
              <button
                type="button"
                class="ghost-button"
                @click="advancedReadonlyOpen = !advancedReadonlyOpen"
              >
                {{ advancedReadonlyOpen ? "Hide Advanced" : "Advanced" }}
              </button>
            </div>
            <dl v-if="advancedReadonlyOpen" class="detail-grid advanced-detail-grid">
              <div v-for="property in selectedPool.immutableProperties.advanced" :key="property.name">
                <dt>{{ property.name }}</dt>
                <dd>{{ property.value }} <span class="subtle-text">({{ property.source }})</span></dd>
              </div>
            </dl>
          </section>

          <section class="drawer-section">
            <div class="drawer-section-header">
              <div>
                <h4>Editable Properties</h4>
                <p class="subtle-text">Adjust supported pool settings and save the changed fields together.</p>
              </div>
              <button
                type="button"
                class="primary-button"
                :disabled="!changedItems.length || submitting"
                @click="openConfirmDialog"
              >
                {{ submitting ? "Saving..." : "Save" }}
              </button>
            </div>

            <dl class="detail-grid editable-detail-grid">
              <div v-for="property in selectedPool.editableProperties" :key="property.name" class="editable-property-card">
                <dt>{{ property.name }}</dt>
                <dd>
                  <select
                    v-if="propertyInput(property.name).type === 'select'"
                    v-model="draftValues[property.name]"
                    class="property-field"
                    :disabled="submitting"
                  >
                    <option
                      v-for="option in propertyInput(property.name).options"
                      :key="option.value"
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
                    :disabled="submitting"
                  />
                  <span class="property-meta">
                    Current: {{ property.value }} <span class="subtle-text">({{ property.source }})</span>
                  </span>
                </dd>
              </div>
            </dl>
            <p v-if="!selectedPool.editableProperties.length" class="subtle-text">
              No editable properties were reported in the current snapshot.
            </p>
          </section>

          <section v-if="changedItems.length" class="drawer-section">
            <h4>Pending Changes</h4>
            <ul class="result-list">
              <li v-for="item in changedItems" :key="item.property" class="result-list-item">
                <strong>{{ item.property }}</strong>
                <span class="subtle-text">{{ item.oldValue || "-" }} -> {{ item.newValue || "-" }}</span>
              </li>
            </ul>
          </section>
          <section class="drawer-section">
            <div class="drawer-section-header">
              <div>
                <h4>Danger Zone</h4>
                <p class="subtle-text">Destroying a pool removes the whole pool from the host.</p>
              </div>
              <button
                type="button"
                class="danger-button"
                :disabled="destroySubmitting"
                @click="openDestroyPoolConfirmDialog"
              >
                Destroy Pool
              </button>
            </div>
          </section>
        </div>
      </DetailDrawer>

      <DetailDrawer
        v-model="topologyDrawerOpen"
        title="Edit Pool Topology"
        :description="selectedPool ? selectedPool.name : ''"
      >
        <div v-if="selectedPool" class="drawer-section-list">
          <section class="drawer-section">
            <h4>Current Topology</h4>
            <div class="topology-group-list" v-if="topologyGroupSummary.length">
              <article v-for="group in topologyGroupSummary" :key="group.name" class="topology-group-card">
                <div class="result-list-head">
                  <strong>{{ group.label }}</strong>
                  <span class="subtle-text">{{ group.items.length }} group{{ group.items.length === 1 ? "" : "s" }}</span>
                </div>
                <ul class="simple-detail-list" v-if="group.items.length">
                  <li v-for="item in group.items" :key="group.name + ':' + item.name">
                    <div class="result-list-head">
                      <strong>{{ item.name }}</strong>
                      <button
                        v-if="getRemovalTarget(item)"
                        type="button"
                        class="danger-button"
                        :disabled="removeSubmitting"
                        @click="openRemoveTargetConfirmDialog(getRemovalTarget(item))"
                      >
                        Remove
                      </button>
                    </div>
                    <span class="subtle-text">Layout: {{ item.layout }} · State: {{ item.state || "UNKNOWN" }}</span>
                    <div class="topology-member-card-list">
                      <article v-for="member in item.members" :key="member.path + ':' + member.diskId" class="topology-member-card">
                        <strong>{{ member.path }}</strong>
                        <div class="subtle-text">{{ member.diskId }}</div>
                        <div class="subtle-text">{{ member.model || "Unknown model" }}</div>
                        <div class="topology-member-meta">
                          <span class="inline-status" :data-health="member.state || 'UNKNOWN'">{{ member.state || "UNKNOWN" }}</span>
                          <span class="subtle-text">R {{ member.read ?? 0 }}</span>
                          <span class="subtle-text">W {{ member.write ?? 0 }}</span>
                          <span class="subtle-text">C {{ member.cksum ?? 0 }}</span>
                        </div>
                      </article>
                    </div>
                  </li>
                </ul>
                <p v-else class="subtle-text">No {{ group.label.toLowerCase() }} reported.</p>
              </article>
            </div>
          </section>

          <section class="drawer-section">
            <div class="drawer-section-header">
              <div>
                <h4>Add Devices</h4>
                <p class="subtle-text">Select the topology role, layout, and exact devices before saving.</p>
              </div>
              <button
                type="button"
                class="primary-button"
                :disabled="!topologyPendingAdditions.length || topologySubmitting"
                @click="openTopologyConfirmDialog"
              >
                {{ topologySubmitting ? "Saving..." : "Save" }}
              </button>
            </div>

            <div class="topology-form-grid">
              <label class="form-field">
                <span>Category</span>
                <select v-model="topologyDraft.category" class="property-field" :disabled="topologySubmitting">
                  <option v-for="option in topologyCategoryOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </label>

              <label class="form-field">
                <span>Layout</span>
                <select v-model="topologyDraft.layout" class="property-field" :disabled="topologySubmitting">
                  <option v-for="option in topologyLayoutOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </label>
            </div>

            <div class="topology-device-picker">
              <div class="result-list-head">
                <strong>Available Devices</strong>
                <span class="subtle-text">{{ availableTopologyDevices.length }} selectable</span>
              </div>
              <div v-if="availableTopologyDevices.length" class="topology-device-list">
                <label
                  v-for="device in availableTopologyDevices"
                  :key="device.path"
                  class="topology-device-option"
                  :data-selected="topologyDeviceSelected(device.path)"
                >
                  <input
                    type="checkbox"
                    :checked="topologyDeviceSelected(device.path)"
                    :disabled="topologySubmitting"
                    @change="toggleTopologyDevice(device.path)"
                  />
                  <div>
                    <strong>{{ device.path }}</strong>
                    <div class="subtle-text">{{ device.diskId }}</div>
                    <div class="subtle-text">{{ device.model || "Unknown model" }}</div>
                    <div class="subtle-text">{{ formatBytes(device.size) }}</div>
                  </div>
                </label>
              </div>
              <p v-else class="subtle-text">No unused disks are currently available for topology changes.</p>
            </div>
          </section>

          <section v-if="topologySelectionSummary.length" class="drawer-section">
            <h4>Pending Topology Addition</h4>
            <ul class="result-list">
              <li class="result-list-item">
                <strong>{{ topologyDraft.category }}</strong>
                <span class="subtle-text">Layout: {{ topologyDraft.layout }}</span>
                <span class="subtle-text">
                  {{ topologySelectionSummary.map(formatTopologyDeviceLabel).join(', ') }}
                </span>
              </li>
            </ul>
          </section>
        </div>
      </DetailDrawer>

      <DetailDrawer
        v-model="createPoolDrawerOpen"
        title="Create Pool"
        description="Build the pool definition step by step, then submit one atomic zpool create command."
      >
        <div class="drawer-section-list">
          <section class="drawer-section">
            <div class="wizard-step-list">
              <button
                v-for="item in createPoolStepItems"
                :key="item.key"
                type="button"
                class="ghost-button"
                :data-active="createPoolStep === item.key"
                @click="setCreatePoolStep(item.key)"
              >
                {{ item.label }}
              </button>
            </div>
          </section>

          <section v-if="createPoolStep === 'basic'" class="drawer-section">
            <h4>Basic</h4>
            <div class="topology-form-grid">
              <label class="form-field">
                <span>Pool Name</span>
                <input v-model="createPoolDraft.name" type="text" class="property-field" placeholder="tank2" :disabled="createPoolSubmitting" />
              </label>
            </div>
            <dl class="detail-grid editable-detail-grid">
              <div v-for="[name, config] in createPoolPropertyFields" :key="name" class="editable-property-card">
                <dt>{{ config.label }}</dt>
                <dd>
                  <select
                    v-if="config.type === 'select'"
                    v-model="createPoolDraft.properties[name]"
                    class="property-field"
                    :disabled="createPoolSubmitting"
                  >
                    <option v-for="option in config.options" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                  <input
                    v-else
                    v-model="createPoolDraft.properties[name]"
                    type="text"
                    class="property-field"
                    :placeholder="config.placeholder || ''"
                    :disabled="createPoolSubmitting"
                  />
                </dd>
              </div>
            </dl>
          </section>

          <section v-if="createPoolStep === 'data'" class="drawer-section">
            <div class="drawer-section-header">
              <div>
                <h4>Data VDEVs</h4>
                <p class="subtle-text">Add one or more required data vdevs before creating the pool.</p>
              </div>
              <button type="button" class="primary-button" :disabled="!createPoolDraft.dataBuilder.devices.length || createPoolSubmitting" @click="addCreatePoolVdev('dataBuilder')">
                Add Data VDEV
              </button>
            </div>
            <div class="topology-form-grid">
              <label class="form-field">
                <span>Layout</span>
                <select v-model="createPoolDraft.dataBuilder.layout" class="property-field" :disabled="createPoolSubmitting">
                  <option v-for="option in createPoolDataLayoutOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </label>
            </div>
            <div class="topology-device-picker">
              <div class="result-list-head">
                <strong>Available Data Devices</strong>
                <span class="subtle-text">{{ createPoolAvailableDataDevices.length }} selectable</span>
              </div>
              <div v-if="createPoolAvailableDataDevices.length" class="topology-device-list">
                <label
                  v-for="device in createPoolAvailableDataDevices"
                  :key="'data-' + device.path"
                  class="topology-device-option"
                  :data-selected="createPoolDeviceSelected('dataBuilder', device.path)"
                >
                  <input
                    type="checkbox"
                    :checked="createPoolDeviceSelected('dataBuilder', device.path)"
                    :disabled="createPoolSubmitting"
                    @change="toggleCreatePoolDevice('dataBuilder', device.path)"
                  />
                  <div>
                    <strong>{{ device.path }}</strong>
                    <div class="subtle-text">{{ device.diskId }}</div>
                    <div class="subtle-text">{{ device.model || "Unknown model" }}</div>
                    <div class="subtle-text">{{ formatBytes(device.size) }}</div>
                  </div>
                </label>
              </div>
            </div>
            <section v-if="createPoolDataSelectionSummary.length || createPoolDraft.dataVdevs.length" class="drawer-section">
              <h4>Planned Data VDEVs</h4>
              <ul class="result-list">
                <li v-for="(item, index) in createPoolDraft.dataVdevs" :key="'data-vdev-' + index" class="result-list-item">
                  <div class="result-list-head">
                    <strong>data</strong>
                    <button type="button" class="ghost-button" :disabled="createPoolSubmitting" @click="removeCreatePoolVdev('dataVdevs', index)">Remove</button>
                  </div>
                  <span class="subtle-text">Layout: {{ item.layout }}</span>
                  <span class="subtle-text">{{ item.devices.join(', ') }}</span>
                </li>
                <li v-if="createPoolDataSelectionSummary.length" class="result-list-item">
                  <strong>Pending builder</strong>
                  <span class="subtle-text">Layout: {{ createPoolDraft.dataBuilder.layout }}</span>
                  <span class="subtle-text">{{ createPoolDataSelectionSummary.map(formatTopologyDeviceLabel).join(', ') }}</span>
                </li>
              </ul>
            </section>
          </section>

          <section v-if="createPoolStep === 'aux'" class="drawer-section">
            <div class="drawer-section-header">
              <div>
                <h4>Extra Classes</h4>
                <p class="subtle-text">Optionally add log, cache, special, dedup, or spare devices.</p>
              </div>
              <button type="button" class="primary-button" :disabled="!createPoolDraft.auxBuilder.devices.length || createPoolSubmitting" @click="addCreatePoolVdev('auxBuilder')">
                Add Class
              </button>
            </div>
            <div class="topology-form-grid">
              <label class="form-field">
                <span>Category</span>
                <select v-model="createPoolDraft.auxBuilder.category" class="property-field" :disabled="createPoolSubmitting">
                  <option v-for="option in topologyCategoryOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </label>
              <label class="form-field">
                <span>Layout</span>
                <select v-model="createPoolDraft.auxBuilder.layout" class="property-field" :disabled="createPoolSubmitting">
                  <option v-for="option in createPoolAuxLayoutOptions" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </label>
            </div>
            <div class="topology-device-picker">
              <div class="result-list-head">
                <strong>Available Devices</strong>
                <span class="subtle-text">{{ createPoolAvailableAuxDevices.length }} selectable</span>
              </div>
              <div v-if="createPoolAvailableAuxDevices.length" class="topology-device-list">
                <label
                  v-for="device in createPoolAvailableAuxDevices"
                  :key="'aux-' + device.path"
                  class="topology-device-option"
                  :data-selected="createPoolDeviceSelected('auxBuilder', device.path)"
                >
                  <input
                    type="checkbox"
                    :checked="createPoolDeviceSelected('auxBuilder', device.path)"
                    :disabled="createPoolSubmitting"
                    @change="toggleCreatePoolDevice('auxBuilder', device.path)"
                  />
                  <div>
                    <strong>{{ device.path }}</strong>
                    <div class="subtle-text">{{ device.diskId }}</div>
                    <div class="subtle-text">{{ device.model || "Unknown model" }}</div>
                    <div class="subtle-text">{{ formatBytes(device.size) }}</div>
                  </div>
                </label>
              </div>
            </div>
            <section v-if="createPoolAuxSelectionSummary.length || createPoolDraft.auxVdevs.length" class="drawer-section">
              <h4>Planned Extra Classes</h4>
              <ul class="result-list">
                <li v-for="(item, index) in createPoolDraft.auxVdevs" :key="'aux-vdev-' + index" class="result-list-item">
                  <div class="result-list-head">
                    <strong>{{ item.category }}</strong>
                    <button type="button" class="ghost-button" :disabled="createPoolSubmitting" @click="removeCreatePoolVdev('auxVdevs', index)">Remove</button>
                  </div>
                  <span class="subtle-text">Layout: {{ item.layout }}</span>
                  <span class="subtle-text">{{ item.devices.join(', ') }}</span>
                </li>
                <li v-if="createPoolAuxSelectionSummary.length" class="result-list-item">
                  <strong>Pending builder</strong>
                  <span class="subtle-text">{{ createPoolDraft.auxBuilder.category }} · {{ createPoolDraft.auxBuilder.layout }}</span>
                  <span class="subtle-text">{{ createPoolAuxSelectionSummary.map(formatTopologyDeviceLabel).join(', ') }}</span>
                </li>
              </ul>
            </section>
          </section>

          <section v-if="createPoolStep === 'review'" class="drawer-section">
            <h4>Review</h4>
            <ul class="result-list">
              <li class="result-list-item">
                <strong>Pool Name</strong>
                <span class="subtle-text">{{ createPoolPayload.name || "-" }}</span>
              </li>
              <li class="result-list-item">
                <strong>Properties</strong>
                <span class="subtle-text">
                  {{ createPoolPayload.properties.length ? createPoolPayload.properties.map((item) => item.name + '=' + item.value).join(', ') : 'No extra properties' }}
                </span>
              </li>
            </ul>
            <div class="topology-group-list">
              <article v-for="group in createPoolReviewGroups" :key="group.label" class="topology-group-card">
                <div class="result-list-head">
                  <strong>{{ group.label }}</strong>
                  <span class="subtle-text">{{ group.items.length }} item{{ group.items.length === 1 ? '' : 's' }}</span>
                </div>
                <ul class="simple-detail-list" v-if="group.items.length">
                  <li v-for="(item, index) in group.items" :key="group.label + ':' + index">
                    <strong>{{ item.category }}</strong>
                    <span class="subtle-text">{{ item.layout }}</span>
                    <span class="subtle-text">{{ item.devices.join(', ') }}</span>
                  </li>
                </ul>
                <p v-else class="subtle-text">No items configured.</p>
              </article>
            </div>
          </section>

          <section class="drawer-section">
            <div class="dialog-actions create-pool-actions">
              <button type="button" class="ghost-button" :disabled="createPoolSubmitting || createPoolStep === 'basic'" @click="previousCreatePoolStep">Back</button>
              <button
                v-if="createPoolStep !== 'review'"
                type="button"
                class="primary-button"
                :disabled="createPoolSubmitting || !canAdvanceCreatePool"
                @click="nextCreatePoolStep"
              >
                Next
              </button>
              <button
                v-else
                type="button"
                class="primary-button"
                :disabled="createPoolSubmitting || !canSubmitCreatePool"
                @click="openCreatePoolConfirmDialog"
              >
                Create Pool
              </button>
            </div>
          </section>
        </div>
      </DetailDrawer>

      <ConfirmDialog
        v-model="confirmDialogOpen"
        :busy="submitting"
        :can-confirm="Boolean(changedItems.length)"
        :result-mode="dialogPhase === 'result'"
        :confirm-text="dialogPhase === 'submitting' ? 'Updating...' : 'Confirm Update'"
        title="Confirm Pool Property Changes"
        :description="selectedPool ? 'Pool: ' + selectedPool.name : ''"
        @confirm="confirmSave"
      >
        <div v-if="dialogPhase === 'confirm'" class="dialog-section-list">
          <p class="subtle-text">These property changes will be sent to the host after confirmation.</p>
          <ul class="result-list">
            <li v-for="item in changedItems" :key="item.property" class="result-list-item">
              <strong>{{ item.property }}</strong>
              <span class="subtle-text">{{ item.oldValue || "-" }} -> {{ item.newValue || "-" }}</span>
            </li>
          </ul>
        </div>

        <div v-else-if="dialogPhase === 'submitting'" class="dialog-section-list">
          <div class="progress-shell">
            <div class="progress-spinner"></div>
            <div>
              <strong>Applying property changes...</strong>
              <p class="subtle-text">Please wait while the backend sends SSH commands and refreshes the latest state.</p>
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
                <p class="subtle-text">{{ item.old_value || "-" }} -> {{ item.new_value || "-" }}</p>
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
                <pre class="terminal-log-block">{{ entry.lines.join('\\n') }}</pre>
              </article>
            </div>
            <p v-else class="subtle-text">No SSH logs are available for this submission.</p>
          </section>
        </div>
      </ConfirmDialog>

      <ConfirmDialog
        v-model="topologyConfirmDialogOpen"
        :busy="topologySubmitting"
        :can-confirm="Boolean(topologyPendingAdditions.length)"
        :result-mode="topologyDialogPhase === 'result'"
        :confirm-text="topologyDialogPhase === 'submitting' ? 'Updating...' : 'Confirm Update'"
        title="Confirm Pool Topology Changes"
        :description="selectedPool ? 'Pool: ' + selectedPool.name : ''"
        @confirm="confirmTopologySave"
      >
        <div v-if="topologyDialogPhase === 'confirm'" class="dialog-section-list">
          <p class="subtle-text">These topology changes will be sent to the host after confirmation.</p>
          <ul class="result-list">
            <li v-for="item in topologyConfirmSummary" :key="item.category + ':' + item.layout" class="result-list-item">
              <strong>{{ item.category }}</strong>
              <span class="subtle-text">Layout: {{ item.layout }}</span>
              <span class="subtle-text">
                {{ item.deviceLabels.join(', ') }}
              </span>
            </li>
          </ul>
        </div>

        <div v-else-if="topologyDialogPhase === 'submitting'" class="dialog-section-list">
          <div class="progress-shell">
            <div class="progress-spinner"></div>
            <div>
              <strong>Applying topology changes...</strong>
              <p class="subtle-text">Please wait while the backend updates the pool and refreshes the latest state.</p>
            </div>
          </div>
        </div>

        <div v-else class="dialog-section-list">
          <p v-if="topologyDialogSummary" class="notice-text">{{ topologyDialogSummary }}</p>
          <p v-if="topologyDialogError" class="error-text">{{ topologyDialogError }}</p>

          <section>
            <h4 class="dialog-mini-heading">Result List</h4>
            <ul class="result-list" v-if="topologyDialogResults.length">
              <li v-for="item in topologyDialogResults" :key="item.category + ':' + item.layout + ':' + item.devices.join(',')" class="result-list-item">
                <div class="result-list-head">
                  <strong>{{ item.category }}</strong>
                  <span class="inline-status" :data-health="item.success ? 'ONLINE' : 'DEGRADED'">
                    {{ item.success ? "Success" : "Failed" }}
                  </span>
                </div>
                <p class="subtle-text">Layout: {{ item.layout }}</p>
                <p class="subtle-text">{{ item.devices.join(', ') }}</p>
                <p class="subtle-text">{{ item.message }}</p>
              </li>
            </ul>
            <p v-else class="subtle-text">No result rows were returned.</p>
          </section>

          <section>
            <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
            <div v-if="topologyTerminalLogLines.length" class="terminal-log-list">
              <article v-for="entry in topologyTerminalLogLines" :key="entry.key" class="terminal-log-card">
                <div class="result-list-head">
                  <strong>{{ entry.label }}</strong>
                  <span class="inline-status" :data-health="entry.success ? 'ONLINE' : 'DEGRADED'">
                    {{ entry.success ? "OK" : "Error" }}
                  </span>
                </div>
                <pre class="terminal-log-block">{{ entry.lines.join('\\n') }}</pre>
              </article>
            </div>
            <p v-else class="subtle-text">No SSH logs are available for this submission.</p>
          </section>
        </div>
      </ConfirmDialog>

      <ConfirmDialog
        v-model="createPoolConfirmDialogOpen"
        :busy="createPoolSubmitting"
        :can-confirm="canSubmitCreatePool"
        :result-mode="createPoolDialogPhase === 'result'"
        :confirm-text="createPoolDialogPhase === 'submitting' ? 'Creating...' : 'Confirm Create'"
        title="Confirm Pool Creation"
        :description="createPoolPayload.name ? 'Pool: ' + createPoolPayload.name : 'New pool'"
        @confirm="confirmCreatePool"
      >
        <div v-if="createPoolDialogPhase === 'confirm'" class="dialog-section-list">
          <p class="subtle-text">This will submit one atomic zpool create command with all selected properties and vdevs.</p>
          <ul class="result-list">
            <li class="result-list-item">
              <strong>Pool Name</strong>
              <span class="subtle-text">{{ createPoolPayload.name }}</span>
            </li>
            <li class="result-list-item">
              <strong>Properties</strong>
              <span class="subtle-text">{{ createPoolPayload.properties.length ? createPoolPayload.properties.map((item) => item.name + '=' + item.value).join(', ') : 'No extra properties' }}</span>
            </li>
            <li v-for="(vdev, index) in createPoolPayload.vdevs" :key="'create-confirm-' + index" class="result-list-item">
              <strong>{{ vdev.category }}</strong>
              <span class="subtle-text">Layout: {{ vdev.layout }}</span>
              <span class="subtle-text">{{ vdev.devices.join(', ') }}</span>
            </li>
          </ul>
        </div>

        <div v-else-if="createPoolDialogPhase === 'submitting'" class="dialog-section-list">
          <div class="progress-shell">
            <div class="progress-spinner"></div>
            <div>
              <strong>Creating pool...</strong>
              <p class="subtle-text">Please wait while the backend runs one zpool create command and refreshes the latest state.</p>
            </div>
          </div>
        </div>

        <div v-else class="dialog-section-list">
          <p v-if="createPoolDialogSummary" class="notice-text">{{ createPoolDialogSummary }}</p>
          <p v-if="createPoolDialogError" class="error-text">{{ createPoolDialogError }}</p>

          <section>
            <h4 class="dialog-mini-heading">Result</h4>
            <ul class="result-list" v-if="createPoolDialogResult">
              <li class="result-list-item">
                <div class="result-list-head">
                  <strong>{{ createPoolDialogResult.pool }}</strong>
                  <span class="inline-status" :data-health="createPoolDialogResult.success ? 'ONLINE' : 'DEGRADED'">
                    {{ createPoolDialogResult.success ? "Success" : "Failed" }}
                  </span>
                </div>
                <p class="subtle-text">{{ createPoolDialogResult.message }}</p>
              </li>
            </ul>
            <p v-else class="subtle-text">No result was returned.</p>
          </section>

          <section>
            <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
            <div v-if="createPoolTerminalLogLines.length" class="terminal-log-list">
              <article v-for="entry in createPoolTerminalLogLines" :key="entry.key" class="terminal-log-card">
                <div class="result-list-head">
                  <strong>{{ entry.label }}</strong>
                  <span class="inline-status" :data-health="entry.success ? 'ONLINE' : 'DEGRADED'">
                    {{ entry.success ? "OK" : "Error" }}
                  </span>
                </div>
                <pre class="terminal-log-block">{{ entry.lines.join('\\n') }}</pre>
              </article>
            </div>
            <p v-else class="subtle-text">No SSH logs are available for this submission.</p>
          </section>
        </div>
      </ConfirmDialog>
      <ConfirmDialog
        v-model="destroyConfirmDialogOpen"
        :busy="destroySubmitting"
        :can-confirm="Boolean(selectedPool && selectedPool.name)"
        :result-mode="destroyDialogPhase === 'result'"
        :confirm-text="destroyDialogPhase === 'submitting' ? 'Destroying...' : 'Confirm Destroy'"
        title="Confirm Pool Destroy"
        :description="selectedPool ? 'Pool: ' + selectedPool.name : ''"
        @confirm="confirmDestroyPool"
      >
        <div v-if="destroyDialogPhase === 'confirm'" class="dialog-section-list">
          <p class="error-text">This will run zpool destroy on the selected pool.</p>
          <ul class="result-list">
            <li class="result-list-item">
              <strong>Pool</strong>
              <span class="subtle-text">{{ selectedPool ? selectedPool.name : '-' }}</span>
            </li>
          </ul>
        </div>

        <div v-else-if="destroyDialogPhase === 'submitting'" class="dialog-section-list">
          <div class="progress-shell">
            <div class="progress-spinner"></div>
            <div>
              <strong>Destroying pool...</strong>
              <p class="subtle-text">Please wait while the backend runs zpool destroy and refreshes the latest state.</p>
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
                  <strong>{{ destroyDialogResult.pool }}</strong>
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
                <pre class="terminal-log-block">{{ entry.lines.join('\\n') }}</pre>
              </article>
            </div>
            <p v-else class="subtle-text">No SSH logs are available for this submission.</p>
          </section>
        </div>
      </ConfirmDialog>

      <ConfirmDialog
        v-model="removeConfirmDialogOpen"
        :busy="removeSubmitting"
        :can-confirm="Boolean(selectedRemovalTarget && selectedRemovalTarget.commandTarget)"
        :result-mode="removeDialogPhase === 'result'"
        :confirm-text="removeDialogPhase === 'submitting' ? 'Removing...' : 'Confirm Remove'"
        title="Confirm Topology Removal"
        :description="selectedPool ? 'Pool: ' + selectedPool.name : ''"
        @confirm="confirmRemoveTarget"
      >
        <div v-if="removeDialogPhase === 'confirm'" class="dialog-section-list">
          <p class="subtle-text">This will remove the selected topology target from the pool.</p>
          <ul class="result-list" v-if="selectedRemovalTarget">
            <li class="result-list-item">
              <strong>{{ selectedRemovalTarget.displayLabel }}</strong>
              <span class="subtle-text">{{ selectedRemovalTarget.vdevClass }} / {{ selectedRemovalTarget.layout }}</span>
              <span class="subtle-text">{{ selectedRemovalTarget.targetType }}</span>
            </li>
          </ul>
        </div>

        <div v-else-if="removeDialogPhase === 'submitting'" class="dialog-section-list">
          <div class="progress-shell">
            <div class="progress-spinner"></div>
            <div>
              <strong>Removing topology target...</strong>
              <p class="subtle-text">Please wait while the backend runs zpool remove and refreshes the latest state.</p>
            </div>
          </div>
        </div>

        <div v-else class="dialog-section-list">
          <p v-if="removeDialogSummary" class="notice-text">{{ removeDialogSummary }}</p>
          <p v-if="removeDialogError" class="error-text">{{ removeDialogError }}</p>

          <section>
            <h4 class="dialog-mini-heading">Result</h4>
            <ul class="result-list" v-if="removeDialogResult">
              <li class="result-list-item">
                <div class="result-list-head">
                  <strong>{{ removeDialogResult.display_label }}</strong>
                  <span class="inline-status" :data-health="removeDialogResult.success ? 'ONLINE' : 'DEGRADED'">
                    {{ removeDialogResult.success ? "Success" : "Failed" }}
                  </span>
                </div>
                <p class="subtle-text">{{ removeDialogResult.message }}</p>
              </li>
            </ul>
            <p v-else class="subtle-text">No result was returned.</p>
          </section>

          <section>
            <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
            <div v-if="removeTerminalLogLines.length" class="terminal-log-list">
              <article v-for="entry in removeTerminalLogLines" :key="entry.key" class="terminal-log-card">
                <div class="result-list-head">
                  <strong>{{ entry.label }}</strong>
                  <span class="inline-status" :data-health="entry.success ? 'ONLINE' : 'DEGRADED'">
                    {{ entry.success ? "OK" : "Error" }}
                  </span>
                </div>
                <pre class="terminal-log-block">{{ entry.lines.join('\\n') }}</pre>
              </article>
            </div>
            <p v-else class="subtle-text">No SSH logs are available for this submission.</p>
          </section>
        </div>
      </ConfirmDialog>
    </section>
  `,
};

function collectPoolProperties(pool, editable) {
  const properties = pool && typeof pool.properties === "object" && pool.properties ? pool.properties : {};
  const entries = Object.entries(properties)
    .filter(([name]) => !isOverviewProperty(name))
    .filter(([name]) => EDITABLE_POOL_PROPERTIES.has(name) === editable)
    .map(([name, property]) => ({
      name,
      value: formatPropertyValue(property?.value),
      rawValue: property?.value ?? "",
      source: property?.source ?? "unknown",
    }))
    .sort((left, right) => left.name.localeCompare(right.name));

  if (editable) {
    return entries;
  }

  return {
    common: entries.filter((property) => COMMON_READONLY_POOL_PROPERTIES.has(property.name)),
    advanced: entries.filter((property) => !COMMON_READONLY_POOL_PROPERTIES.has(property.name)),
  };
}

function isOverviewProperty(name) {
  return new Set([
    "allocated",
    "capacity",
    "dedupratio",
    "fragmentation",
    "free",
    "health",
    "size",
  ]).has(name);
}

function buildPoolQuickFacts(pool) {
  const facts = [
    { label: "Scan", value: pool?.status?.scan || "Not reported" },
    { label: "Errors", value: pool?.status?.errors || "Not reported" },
  ];

  for (const name of ["ashift", "autoreplace", "autoexpand", "autotrim", "failmode", "comment"]) {
    const property = pool?.properties?.[name];
    if (property?.value !== undefined && property?.value !== null) {
      facts.push({
        label: name,
        value: `${property.value}${property.source ? ` (${property.source})` : ""}`,
      });
    }
  }

  return facts;
}

function formatPropertyValue(value) {
  if (value === undefined || value === null || value === "") {
    return "-";
  }
  return String(value);
}

function normalizeEditableValue(propertyName, value) {
  if (value === undefined || value === null) {
    return propertyName === "bootfs" || propertyName === "cachefile" ? "none" : "";
  }
  return String(value);
}

function createTopologyDraft() {
  return {
    category: "log",
    layout: "stripe",
    devices: [],
  };
}

function createPoolWizardDraft() {
  return {
    name: "",
    properties: {
      ashift: "12",
      autoexpand: "off",
      autoreplace: "off",
      autotrim: "off",
      failmode: "wait",
      comment: "",
    },
    dataBuilder: {
      category: "data",
      layout: "mirror",
      devices: [],
    },
    auxBuilder: {
      category: "log",
      layout: "stripe",
      devices: [],
    },
    dataVdevs: [],
    auxVdevs: [],
  };
}

function buildCreatePoolProperties(properties) {
  const items = [];
  for (const [name, value] of Object.entries(properties || {})) {
    if (value === undefined || value === null || value === "") {
      continue;
    }
    items.push({ name, value: String(value) });
  }
  return items;
}

function isDiskAvailableForCreate(disk) {
  if (!disk?.path) {
    return false;
  }
  if (disk.poolName && disk.poolName !== "-") {
    return false;
  }
  const filesystem = String(disk.filesystem || "-").toLowerCase();
  if (!isReusableFilesystem(filesystem, disk.poolName)) {
    return false;
  }
  const partitions = Array.isArray(disk.partitions) ? disk.partitions : [];
  return partitions.every((partition) => {
    const partitionPool = partition.poolName;
    const partitionFilesystem = String(partition.filesystem || "-").toLowerCase();
    return (!partitionPool || partitionPool === "-") && isReusableFilesystem(partitionFilesystem, partitionPool);
  });
}

function isReusableFilesystem(filesystem, poolName) {
  if (["-", "", "none", "unknown"].includes(String(filesystem || "-").toLowerCase())) {
    return true;
  }
  return String(filesystem || "-").toLowerCase() === "zfs_member" && (!poolName || poolName === "-");
}

function allowPathForBuilder(path, usedPaths, currentBuilderPaths) {
  return !usedPaths.has(path) || currentBuilderPaths.includes(path);
}

function formatTopologyDeviceLabel(device) {
  return `${device.path} [${device.diskId}]`;
}

function resolveTopologyState(node) {
  const states = collectTopologyStates(node);
  if (!states.length) {
    return "UNKNOWN";
  }
  return states.reduce((worst, current) => (
    topologyStateSeverity(current) > topologyStateSeverity(worst) ? current : worst
  ));
}

function collectTopologyStates(node) {
  const current = node?.state ? [node.state] : [];
  const children = Array.isArray(node?.children) ? node.children : [];
  return children.reduce((states, child) => states.concat(collectTopologyStates(child)), current);
}

function resolveTopologyMetric(node, key) {
  const total = aggregateTopologyMetric(node, key);
  if (total === null) {
    return "-";
  }
  return total;
}

function aggregateTopologyMetric(node, key) {
  const children = Array.isArray(node?.children) ? node.children : [];
  if (children.length) {
    const totals = children
      .map((child) => aggregateTopologyMetric(child, key))
      .filter((value) => value !== null);
    if (!totals.length) {
      return null;
    }
    return totals.reduce((sum, value) => sum + value, 0);
  }
  if (node?.[key] === null || node?.[key] === undefined) {
    return null;
  }
  return Number(node[key]) || 0;
}

function topologyStateSeverity(state) {
  return {
    ONLINE: 1,
    AVAIL: 1,
    DEGRADED: 2,
    SUSPENDED: 3,
    OFFLINE: 4,
    REMOVED: 4,
    FAULTED: 5,
    UNAVAIL: 5,
    UNKNOWN: 6,
  }[state || "UNKNOWN"] || 6;
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
