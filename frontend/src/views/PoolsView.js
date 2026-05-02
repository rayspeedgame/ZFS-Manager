import { computed, ref } from "vue";

import DetailDrawer from "../components/common/DetailDrawer.js";
import EmptyState from "../components/common/EmptyState.js";
import { formatBytes, formatPercent } from "../lib/formatters.js";

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
      <ul v-if="node.children?.length" class="topology-children">
        <TopologyNode v-for="child in node.children" :key="child.name" :node="child" />
      </ul>
    </li>
  `,
};
TopologyNode.components = { TopologyNode };

export default {
  components: {
    DetailDrawer,
    EmptyState,
    TopologyNode,
  },
  props: {
    state: { type: Object, required: true },
  },
  setup(props) {
    const selectedPool = ref(null);
    const drawerOpen = ref(false);
    const expandedRows = ref({});
    const advancedReadonlyOpen = ref(false);

    const pools = computed(() => props.state.snapshot.value?.data?.pools || []);

    const normalizedPools = computed(() =>
      pools.value.map((pool) => ({
        ...pool,
        immutableProperties: collectPoolProperties(pool, false),
        editableProperties: collectPoolProperties(pool, true),
        quickFacts: buildPoolQuickFacts(pool),
      }))
    );

    function openPool(pool) {
      selectedPool.value = pool;
      advancedReadonlyOpen.value = false;
      drawerOpen.value = true;
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

    return {
      drawerOpen,
      expandedRows,
      advancedReadonlyOpen,
      isExpanded,
      normalizedPools,
      openPool,
      pools,
      selectedPool,
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
                        <h4>Topology</h4>
                        <ul class="topology-list" v-if="pool.status?.config?.length">
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
        :description="selectedPool?.name || ''"
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
                {{ advancedReadonlyOpen ? 'Hide Advanced' : 'Advanced' }}
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
            <h4>Editable Properties</h4>
            <dl class="detail-grid">
              <div v-for="property in selectedPool.editableProperties" :key="property.name">
                <dt>{{ property.name }}</dt>
                <dd>{{ property.value }} <span class="subtle-text">({{ property.source }})</span></dd>
              </div>
            </dl>
            <p v-if="!selectedPool.editableProperties.length" class="subtle-text">
              No editable properties were reported in the current snapshot.
            </p>
          </section>
        </div>
      </DetailDrawer>
    </section>
  `,
};

function collectPoolProperties(pool, editable) {
  const entries = Object.entries(pool.properties || {})
    .filter(([name]) => !isOverviewProperty(name))
    .filter(([name]) => EDITABLE_POOL_PROPERTIES.has(name) === editable)
    .map(([name, property]) => ({
      name,
      value: property?.value ?? "-",
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
    { label: "Scan", value: pool.status?.scan || "Not reported" },
    { label: "Errors", value: pool.status?.errors || "Not reported" },
  ];

  for (const name of ["ashift", "autoreplace", "autoexpand", "autotrim", "failmode", "comment"]) {
    const property = pool.properties?.[name];
    if (property?.value !== undefined && property?.value !== null) {
      facts.push({
        label: name,
        value: `${property.value}${property.source ? ` (${property.source})` : ""}`,
      });
    }
  }

  return facts;
}
