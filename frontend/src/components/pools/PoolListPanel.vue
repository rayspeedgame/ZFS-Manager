<script setup>
import EmptyState from "../common/EmptyState.vue";
import TopologyNode from "./TopologyNode.vue";
import { formatBytes, formatPercent } from "../../lib/formatters.js";

defineProps({
  pools: { type: Array, required: true },
  normalizedPools: { type: Array, required: true },
  isExpanded: { type: Function, required: true },
  destroySubmitting: { type: Boolean, default: false },
});

const emit = defineEmits([
  "create-pool",
  "toggle-row",
  "open-pool",
  "open-topology",
  "destroy-pool",
]);
</script>

<template>
  <article class="surface-panel">
    <div class="section-header">
      <div>
        <h3>Pool Overview</h3>
        <p>Capacity, health, and topology details for each storage pool.</p>
      </div>
      <button type="button" class="primary-button" @click="emit('create-pool')">Create Pool</button>
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
                  @click="emit('toggle-row', pool)"
                >
                  >
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
                <button type="button" class="ghost-button" @click="emit('open-pool', pool)">View</button>
              </td>
            </tr>
            <tr v-if="isExpanded(pool)" class="pool-expand-row">
              <td colspan="9">
                <div class="pool-expand-shell">
                  <section class="pool-expand-panel">
                    <div class="pool-panel-header">
                      <h4>Topology</h4>
                      <button type="button" class="ghost-button" @click="emit('open-topology', pool)">Edit Topology</button>
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
                        @click="emit('destroy-pool', pool)"
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
</template>
