<script>
import { computed, nextTick, ref, watch } from "vue";
import { useI18n } from "vue-i18n";

import CreatePoolDrawer from "../components/pools/CreatePoolDrawer.vue";
import PoolActionDialogs from "../components/pools/PoolActionDialogs.vue";
import PoolDetailDrawer from "../components/pools/PoolDetailDrawer.vue";
import PoolListPanel from "../components/pools/PoolListPanel.vue";
import PoolTopologyDrawer from "../components/pools/PoolTopologyDrawer.vue";
import {
  COMMON_READONLY_POOL_PROPERTIES,
  CREATE_DATA_LAYOUT_OPTIONS,
  CREATE_POOL_PROPERTY_OPTIONS,
  CREATE_ROOT_DATASET_FIELDS,
  EDITABLE_POOL_PROPERTIES,
  PROPERTY_INPUTS,
  ROOT_DATASET_PROPERTY_INPUTS,
  TOPOLOGY_CATEGORY_OPTIONS,
  TOPOLOGY_LAYOUT_OPTIONS,
} from "../components/pools/pool-form-config.js";
import { formatBytes, formatPercent } from "../lib/formatters.js";
import { useAppState } from "../store/state.js";

export default {
  components: {
    CreatePoolDrawer,
    PoolActionDialogs,
    PoolDetailDrawer,
    PoolListPanel,
    PoolTopologyDrawer,
  },
  props: {
    state: { type: Object, required: true },
  },
  setup(props) {
    const { t } = useI18n();
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
    // Keep live snapshot rebinding from wiping user edits mid-typing.
    const detailDraftDirty = ref(false);
    const topologyDraft = ref(createTopologyDraft());
    const topologyDraftDirty = ref(false);
    const createPoolStep = ref("basic");
    const createPoolDraft = ref(createPoolWizardDraft());
    const createPoolDraftDirty = ref(false);
    const createPoolRootAdvancedOpen = ref(false);
    const poolPropertyForce = ref(false);
    const topologyForce = ref(false);
    const createPoolForce = ref(false);
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
        quickFacts: buildPoolQuickFacts(pool, t),
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
    const createPoolRootCommonFields = computed(() => CREATE_ROOT_DATASET_FIELDS.common);
    const createPoolRootAdvancedFields = computed(() => CREATE_ROOT_DATASET_FIELDS.advanced);

    // Keep wizard step labels reactive so locale changes update the open drawer immediately.
    const createPoolStepItems = computed(() => [
      { key: "basic", label: t("pools.createSteps.basic") },
      { key: "rootfs", label: t("pools.createSteps.rootfs") },
      { key: "data", label: t("pools.createSteps.data") },
      { key: "aux", label: t("pools.createSteps.aux") },
      { key: "review", label: t("pools.createSteps.review") },
    ]);

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
      force: createPoolForce.value,
      properties: buildCreatePoolProperties(createPoolDraft.value.properties),
      root_dataset_properties: buildCreatePoolProperties(createPoolDraft.value.rootDatasetProperties),
      vdevs: [
        ...createPoolDraft.value.dataVdevs.map((vdev) => ({ ...vdev })),
        ...createPoolDraft.value.auxVdevs.map((vdev) => ({ ...vdev })),
      ],
    }));

    const createPoolReviewGroups = computed(() => [
      { label: t("pools.dataVdevs"), items: createPoolDraft.value.dataVdevs },
      { label: t("pools.extraClasses"), items: createPoolDraft.value.auxVdevs },
    ]);

    const canAdvanceCreatePool = computed(() => {
      if (createPoolStep.value === "basic") {
        return Boolean(createPoolDraft.value.name.trim());
      }
      if (createPoolStep.value === "rootfs") {
        return true;
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
          if (!topologyDraftDirty.value) {
            topologyDraft.value = createTopologyDraft();
          }
          return;
        }

        selectedPool.value = updated;
        // Rebind live data for the selected pool, but leave any in-progress drafts alone.
        if (!submitting.value && !detailDraftDirty.value) {
          initializeDraft(updated);
        }
        if (!topologySubmitting.value && !removeSubmitting.value && !topologyDraftDirty.value) {
          initializeTopologyDraft(updated);
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
      poolPropertyForce.value = false;
      initializeDraft(pool);
      resetDialogState();
      drawerOpen.value = true;
    }

    function openTopologyEditor(pool) {
      selectedPool.value = pool;
      topologyForce.value = false;
      initializeTopologyDraft(pool);
      resetTopologyDialogState();
      topologyDrawerOpen.value = true;
    }

    function openCreatePoolWizard() {
      initializeCreatePoolDraft();
      resetCreatePoolDialogState();
      createPoolStep.value = "basic";
      createPoolRootAdvancedOpen.value = false;
      createPoolForce.value = false;
      createPoolDrawerOpen.value = true;
    }

    function initializeDraft(pool) {
      const nextDraft = {};
      const editableProperties = Array.isArray(pool.editableProperties) ? pool.editableProperties : [];
      for (const property of editableProperties) {
        nextDraft[property.name] = normalizeEditableValue(property.name, property.rawValue);
      }
      draftValues.value = nextDraft;
      detailDraftDirty.value = false;
    }

    function initializeTopologyDraft(pool) {
      // Preserve the current builder choices when they still match the latest device inventory.
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
      topologyDraftDirty.value = false;
    }

    function initializeCreatePoolDraft() {
      createPoolDraft.value = createPoolWizardDraft();
      createPoolDraftDirty.value = false;
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

    function rootDatasetPropertyInput(propertyName) {
      if (propertyName === "compression") {
        return {
          type: "select",
          options: buildCompressionCreateOptions(),
        };
      }
      return ROOT_DATASET_PROPERTY_INPUTS[propertyName] || { type: "text" };
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
      topologyDraftDirty.value = true;
    }

    function topologyDeviceSelected(path) {
      return topologyDraft.value.devices.includes(path);
    }

    function resetCreatePoolBuilderSelections() {
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
      createPoolDraftDirty.value = true;
    }

    function setCreatePoolStep(step) {
      const steps = createPoolStepItems.value.map((item) => item.key);
      const currentIndex = steps.indexOf(createPoolStep.value);
      const targetIndex = steps.indexOf(step);
      if (targetIndex >= 0 && currentIndex >= 0 && targetIndex < currentIndex) {
        resetCreatePoolBuilderSelections();
      }
      createPoolStep.value = step;
    }

    function nextCreatePoolStep() {
      const steps = createPoolStepItems.value.map((item) => item.key);
      const currentIndex = steps.indexOf(createPoolStep.value);
      if (currentIndex >= 0 && currentIndex < steps.length - 1 && canAdvanceCreatePool.value) {
        createPoolStep.value = steps[currentIndex + 1];
      }
    }

    function previousCreatePoolStep() {
      const steps = createPoolStepItems.value.map((item) => item.key);
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
      createPoolDraftDirty.value = true;
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
      createPoolDraftDirty.value = true;
    }

    function removeCreatePoolVdev(targetKey, index) {
      createPoolDraft.value = {
        ...createPoolDraft.value,
        [targetKey]: createPoolDraft.value[targetKey].filter((_, itemIndex) => itemIndex !== index),
      };
      createPoolDraftDirty.value = true;
    }

    function openCreatePoolConfirmDialog() {
      if (!canSubmitCreatePool.value || createPoolSubmitting.value) {
        return;
      }
      resetCreatePoolDialogState();
      createPoolConfirmDialogOpen.value = true;
    }

    function setDraftValues(value) {
      draftValues.value = value;
      detailDraftDirty.value = true;
    }

    function setTopologyDraft(value) {
      topologyDraft.value = value;
      topologyDraftDirty.value = true;
    }

    function setCreatePoolDraft(value) {
      createPoolDraft.value = value;
      createPoolDraftDirty.value = true;
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
        dialogSummary.value = t("pools.summary.submittedChanges", {
          total: dialogResults.value.length,
          success: successCount,
          failed: failureCount,
        });

        if (response.refresh_error) {
          dialogError.value = t("pools.summary.stateRefreshFailed", { error: response.refresh_error });
        }

        await rebindSelectedPool();
        detailDraftDirty.value = false;
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
        const response = await updatePoolTopology(selectedPool.value.name, topologyPendingAdditions.value, topologyForce.value);
        topologyDialogResults.value = Array.isArray(response.results) ? response.results : [];

        const successCount = topologyDialogResults.value.filter((item) => item.success).length;
        const failureCount = topologyDialogResults.value.length - successCount;
        topologyDialogSummary.value = t("pools.summary.submittedTopologyUpdate", {
          total: topologyDialogResults.value.length,
          success: successCount,
          failed: failureCount,
        });

        if (response.refresh_error) {
          topologyDialogError.value = t("pools.summary.stateRefreshFailed", { error: response.refresh_error });
        }

        await rebindSelectedPool();
        initializeTopologyDraft(selectedPool.value);
        topologyDraftDirty.value = false;
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
          ? t("pools.summary.createCommandSucceeded")
          : t("pools.summary.createCommandFailed");

        if (response.refresh_error) {
          createPoolDialogError.value = t("pools.summary.stateRefreshFailed", { error: response.refresh_error });
        }

        try {
          await refreshStateOnce();
        } catch (refreshError) {
          if (!createPoolDialogError.value) {
            createPoolDialogError.value = refreshError instanceof Error ? refreshError.message : String(refreshError);
          }
        }
        createPoolDraftDirty.value = false;
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
          ? t("pools.summary.destroyCommandSucceeded")
          : t("pools.summary.destroyCommandFailed");

        if (response.refresh_error) {
          destroyDialogError.value = t("pools.summary.stateRefreshFailed", { error: response.refresh_error });
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
          ? t("pools.summary.removeSucceeded")
          : t("pools.summary.removeFailed");

        if (response.refresh_error) {
          removeDialogError.value = t("pools.summary.stateRefreshFailed", { error: response.refresh_error });
        }

        await rebindSelectedPool();
        if (selectedPool.value) {
          initializeTopologyDraft(selectedPool.value);
        }
        topologyDraftDirty.value = false;
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
      createPoolAuxSelectionSummary,
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
      createPoolForce,
      createPoolPayload,
      createPoolPropertyFields,
      createPoolReviewGroups,
      createPoolRootAdvancedFields,
      createPoolRootAdvancedOpen,
      createPoolRootCommonFields,
      createPoolStep,
      createPoolStepItems,
      createPoolSubmitting,
      createPoolTerminalLogLines,
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
      nextCreatePoolStep,
      openConfirmDialog,
      openCreatePoolConfirmDialog,
      openCreatePoolWizard,
      openDestroyPoolConfirmDialog,
      openPool,
      openRemoveTargetConfirmDialog,
      openTopologyConfirmDialog,
      openTopologyEditor,
      poolPropertyForce,
      pools,
      previousCreatePoolStep,
      propertyInput,
      removeConfirmDialogOpen,
      removeCreatePoolVdev,
      removeDialogError,
      removeDialogPhase,
      removeDialogResult,
      removeDialogSummary,
      removeSubmitting,
      removeTerminalLogLines,
      rootDatasetPropertyInput,
      selectedPool,
      selectedRemovalTarget,
      setCreatePoolDraft,
      setCreatePoolStep,
      setDraftValues,
      setTopologyDraft,
      submitting,
      terminalLogLines,
      toggleCreatePoolDevice,
      toggleRow,
      toggleTopologyDevice,
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
      topologyForce,
      topologyGroupSummary,
      topologyLayoutOptions,
      topologyPendingAdditions,
      topologySelectionSummary,
      topologySubmitting,
      topologyTerminalLogLines,
      addCreatePoolVdev,
      formatTopologyDeviceLabel,
      getRemovalTarget,
    };
  },
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

function buildPoolQuickFacts(pool, t) {
  const facts = [
    { label: t("pools.quickFacts.scan"), value: pool?.status?.scan || t("pools.quickFacts.notReported") },
    { label: t("pools.quickFacts.errors"), value: pool?.status?.errors || t("pools.quickFacts.notReported") },
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
    rootDatasetProperties: {
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

function buildCompressionCreateOptions() {
  return [
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
    <PoolListPanel
      :pools="pools"
      :normalized-pools="normalizedPools"
      :is-expanded="isExpanded"
      :destroy-submitting="destroySubmitting"
      @create-pool="openCreatePoolWizard"
      @toggle-row="toggleRow"
      @open-pool="openPool"
      @open-topology="openTopologyEditor"
      @destroy-pool="selectedPool = $event; openDestroyPoolConfirmDialog()"
    />

    <PoolDetailDrawer
      v-model="drawerOpen"
      :selected-pool="selectedPool"
      :advanced-readonly-open="advancedReadonlyOpen"
      :pool-property-force="poolPropertyForce"
      :changed-items="changedItems"
      :draft-values="draftValues"
      :submitting="submitting"
      :destroy-submitting="destroySubmitting"
      :property-input="propertyInput"
      @update:draft-values="setDraftValues"
      @toggle-advanced="advancedReadonlyOpen = !advancedReadonlyOpen"
      @open-confirm="openConfirmDialog"
      @open-destroy="openDestroyPoolConfirmDialog"
    />

    <PoolTopologyDrawer
      v-model="topologyDrawerOpen"
      :selected-pool="selectedPool"
      :topology-group-summary="topologyGroupSummary"
      :topology-draft="topologyDraft"
      :topology-category-options="topologyCategoryOptions"
      :topology-layout-options="topologyLayoutOptions"
      :available-topology-devices="availableTopologyDevices"
      :topology-pending-additions="topologyPendingAdditions"
      :topology-selection-summary="topologySelectionSummary"
      :topology-force="topologyForce"
      :topology-submitting="topologySubmitting"
      :remove-submitting="removeSubmitting"
      :topology-device-selected="topologyDeviceSelected"
      :format-topology-device-label="formatTopologyDeviceLabel"
      :get-removal-target="getRemovalTarget"
      @update:topology-draft="setTopologyDraft"
      @update:topology-force="topologyForce = $event"
      @toggle-device="toggleTopologyDevice"
      @open-confirm="openTopologyConfirmDialog"
      @remove-target="openRemoveTargetConfirmDialog"
    />

    <CreatePoolDrawer
      v-model="createPoolDrawerOpen"
      :create-pool-step-items="createPoolStepItems"
      :create-pool-step="createPoolStep"
      :create-pool-draft="createPoolDraft"
      :create-pool-property-fields="createPoolPropertyFields"
      :create-pool-root-common-fields="createPoolRootCommonFields"
      :create-pool-root-advanced-fields="createPoolRootAdvancedFields"
      :create-pool-root-advanced-open="createPoolRootAdvancedOpen"
      :create-pool-data-layout-options="createPoolDataLayoutOptions"
      :create-pool-aux-layout-options="createPoolAuxLayoutOptions"
      :create-pool-available-data-devices="createPoolAvailableDataDevices"
      :create-pool-available-aux-devices="createPoolAvailableAuxDevices"
      :create-pool-data-selection-summary="createPoolDataSelectionSummary"
      :create-pool-aux-selection-summary="createPoolAuxSelectionSummary"
      :create-pool-review-groups="createPoolReviewGroups"
      :create-pool-payload="createPoolPayload"
      :create-pool-submitting="createPoolSubmitting"
      :create-pool-force="createPoolForce"
      :can-advance-create-pool="canAdvanceCreatePool"
      :can-submit-create-pool="canSubmitCreatePool"
      :create-pool-device-selected="createPoolDeviceSelected"
      :root-dataset-property-input="rootDatasetPropertyInput"
      :topology-category-options="topologyCategoryOptions"
      :format-topology-device-label="formatTopologyDeviceLabel"
      @set-step="setCreatePoolStep"
      @prev-step="previousCreatePoolStep"
      @next-step="nextCreatePoolStep"
      @update:create-pool-draft="setCreatePoolDraft"
      @toggle-root-advanced="createPoolRootAdvancedOpen = !createPoolRootAdvancedOpen"
      @toggle-device="toggleCreatePoolDevice"
      @add-vdev="addCreatePoolVdev"
      @remove-vdev="removeCreatePoolVdev"
      @update:create-pool-force="createPoolForce = $event"
      @open-confirm="openCreatePoolConfirmDialog"
    />

    <PoolActionDialogs
      :selected-pool="selectedPool"
      :selected-removal-target="selectedRemovalTarget"
      :changed-items="changedItems"
      :confirm-dialog-open="confirmDialogOpen"
      :submitting="submitting"
      :dialog-phase="dialogPhase"
      :dialog-summary="dialogSummary"
      :dialog-error="dialogError"
      :dialog-results="dialogResults"
      :terminal-log-lines="terminalLogLines"
      :topology-confirm-dialog-open="topologyConfirmDialogOpen"
      :topology-submitting="topologySubmitting"
      :topology-dialog-phase="topologyDialogPhase"
      :topology-dialog-summary="topologyDialogSummary"
      :topology-dialog-error="topologyDialogError"
      :topology-dialog-results="topologyDialogResults"
      :topology-terminal-log-lines="topologyTerminalLogLines"
      :topology-pending-additions="topologyPendingAdditions"
      :topology-force="topologyForce"
      :topology-confirm-summary="topologyConfirmSummary"
      :create-pool-confirm-dialog-open="createPoolConfirmDialogOpen"
      :create-pool-submitting="createPoolSubmitting"
      :create-pool-dialog-phase="createPoolDialogPhase"
      :create-pool-dialog-summary="createPoolDialogSummary"
      :create-pool-dialog-error="createPoolDialogError"
      :create-pool-dialog-result="createPoolDialogResult"
      :create-pool-terminal-log-lines="createPoolTerminalLogLines"
      :create-pool-payload="createPoolPayload"
      :can-submit-create-pool="canSubmitCreatePool"
      :destroy-confirm-dialog-open="destroyConfirmDialogOpen"
      :destroy-submitting="destroySubmitting"
      :destroy-dialog-phase="destroyDialogPhase"
      :destroy-dialog-summary="destroyDialogSummary"
      :destroy-dialog-error="destroyDialogError"
      :destroy-dialog-result="destroyDialogResult"
      :destroy-terminal-log-lines="destroyTerminalLogLines"
      :remove-confirm-dialog-open="removeConfirmDialogOpen"
      :remove-submitting="removeSubmitting"
      :remove-dialog-phase="removeDialogPhase"
      :remove-dialog-summary="removeDialogSummary"
      :remove-dialog-error="removeDialogError"
      :remove-dialog-result="removeDialogResult"
      :remove-terminal-log-lines="removeTerminalLogLines"
      @update:confirmDialogOpen="confirmDialogOpen = $event"
      @update:topologyConfirmDialogOpen="topologyConfirmDialogOpen = $event"
      @update:createPoolConfirmDialogOpen="createPoolConfirmDialogOpen = $event"
      @update:destroyConfirmDialogOpen="destroyConfirmDialogOpen = $event"
      @update:removeConfirmDialogOpen="removeConfirmDialogOpen = $event"
      @confirm-save="confirmSave"
      @confirm-topology="confirmTopologySave"
      @confirm-create-pool="confirmCreatePool"
      @confirm-destroy-pool="confirmDestroyPool"
      @confirm-remove-target="confirmRemoveTarget"
    />
  </section>
</template>
