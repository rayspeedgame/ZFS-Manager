import { computed, ref } from "vue";

import DetailDrawer from "../components/common/DetailDrawer.js";
import EmptyState from "../components/common/EmptyState.js";
import { formatBytes, formatPercent } from "../lib/formatters.js";

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

    const pools = computed(() => props.state.snapshot.value?.zpool_overview?.pools || []);
    const status = computed(() => props.state.snapshot.value?.zpool_overview?.status || {});
    const properties = computed(() => props.state.snapshot.value?.zpool_overview?.properties || {});

    function openPool(pool) {
      selectedPool.value = {
        ...pool,
        status: status.value.pool === pool.name ? status.value : null,
        properties: properties.value[pool.name] || {},
      };
      drawerOpen.value = true;
    }

    return {
      drawerOpen,
      openPool,
      pools,
      selectedPool,
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
              <tr v-for="pool in pools" :key="pool.name">
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
            <h4>Overview</h4>
            <dl class="detail-grid">
              <div><dt>Health</dt><dd>{{ selectedPool.health }}</dd></div>
              <div><dt>Size</dt><dd>{{ formatBytes(selectedPool.size) }}</dd></div>
              <div><dt>Allocated</dt><dd>{{ formatBytes(selectedPool.allocated) }}</dd></div>
              <div><dt>Free</dt><dd>{{ formatBytes(selectedPool.free) }}</dd></div>
            </dl>
          </section>

          <section class="drawer-section" v-if="selectedPool.status">
            <h4>Topology</h4>
            <ul class="topology-list">
              <TopologyNode v-for="node in selectedPool.status.config" :key="node.name" :node="node" />
            </ul>
          </section>

          <section class="drawer-section">
            <h4>Key Properties</h4>
            <dl class="detail-grid">
              <div v-for="(property, name) in selectedPool.properties" :key="name">
                <dt>{{ name }}</dt>
                <dd>{{ property.value }} <span class="subtle-text">({{ property.source }})</span></dd>
              </div>
            </dl>
          </section>
        </div>
      </DetailDrawer>
    </section>
  `,
};
