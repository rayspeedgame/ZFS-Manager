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
  template: `
    <li class="topology-node">
      <div class="topology-line">
        <strong>{{ node.name }}</strong>
        <span>{{ node.state }}</span>
        <span>R {{ node.read }}</span>
        <span>W {{ node.write }}</span>
        <span>C {{ node.cksum }}</span>
      </div>
      <ul v-if="Array.isArray(node.children) && node.children.length" class="topology-children">
        <TopologyNode v-for="child in node.children" :key="child.name" :node="child" />
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
    const { updatePoolProperties, refreshStateOnce } = useAppState();
    const selectedPool = ref(null);
    const drawerOpen = ref(false);
    const expandedRows = ref({});
    const advancedReadonlyOpen = ref(false);
    const confirmDialogOpen = ref(false);
    const draftValues = ref({});
    const dialogPhase = ref("confirm");
    const dialogError = ref("");
    const dialogResults = ref([]);
    const dialogSummary = ref("");
    const submitting = ref(false);

    const pools = computed(() => {
      const value = props.state.snapshot.value?.data?.pools;
      return Array.isArray(value) ? value : [];
    });

    const datasets = computed(() => {
      const value = props.state.snapshot.value?.data?.datasets;
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

    const terminalLogLines = computed(() => {
      if (!Array.isArray(dialogResults.value) || !dialogResults.value.length) {
        return [];
      }

      return dialogResults.value.map((item) => ({
        property: item.property,
        success: item.success,
        lines: [
          `$ ${item.command || "N/A"}`,
          item.exit_status !== null && item.exit_status !== undefined ? `exit_status: ${item.exit_status}` : null,
          item.stdout ? `stdout: ${item.stdout}` : null,
          item.stderr ? `stderr: ${item.stderr}` : null,
          !item.stdout && !item.stderr ? item.message : null,
        ].filter(Boolean),
      }));
    });

    watch(
      () => props.state.snapshot.value?.meta?.last_updated,
      () => {
        if (!selectedPool.value?.name) {
          return;
        }

        const updated = normalizedPools.value.find((pool) => pool.name === selectedPool.value.name);
        if (!updated) {
          drawerOpen.value = false;
          selectedPool.value = null;
          draftValues.value = {};
          return;
        }

        selectedPool.value = updated;
        // Once the backend refreshes a successful write, reset the local draft to the new source of truth.
        if (!submitting.value && !changedItems.value.length) {
          initializeDraft(updated);
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

    function initializeDraft(pool) {
      const nextDraft = {};
      const editableProperties = Array.isArray(pool.editableProperties) ? pool.editableProperties : [];
      for (const property of editableProperties) {
        nextDraft[property.name] = normalizeEditableValue(property.name, property.rawValue);
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

        try {
          await refreshStateOnce();
          await nextTick();
          // Rebind the drawer to the freshly refreshed pool row before clearing pending changes.
          const updatedPool = normalizedPools.value.find((pool) => pool.name === selectedPool.value?.name);
          if (updatedPool) {
            selectedPool.value = updatedPool;
            initializeDraft(updatedPool);
          }
        } catch (refreshError) {
          if (!dialogError.value) {
            dialogError.value = refreshError instanceof Error ? refreshError.message : String(refreshError);
          }
        }
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

    return {
      advancedReadonlyOpen,
      changedItems,
      confirmDialogOpen,
      confirmSave,
      dialogError,
      dialogPhase,
      dialogResults,
      dialogSummary,
      draftValues,
      drawerOpen,
      isExpanded,
      normalizedPools,
      openConfirmDialog,
      openPool,
      pools,
      propertyInput,
      selectedPool,
      submitting,
      terminalLogLines,
      toggleRow,
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
                      ▶
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
                        <h4>Topology</h4>
                        <ul class="topology-list" v-if="pool.status && Array.isArray(pool.status.config) && pool.status.config.length">
                          <TopologyNode v-for="node in pool.status.config" :key="node.name" :node="node" />
                        </ul>
                        <p v-else class="subtle-text">No topology reported for this pool.</p>
                      </section>

                      <section class="pool-expand-panel">
                        <h4>Quick Facts</h4>
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
              <article v-for="entry in terminalLogLines" :key="entry.property" class="terminal-log-card">
                <div class="result-list-head">
                  <strong>{{ entry.property }}</strong>
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
