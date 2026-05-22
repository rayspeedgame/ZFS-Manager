<script setup>
import { useI18n } from "vue-i18n";

import EmptyState from "../common/EmptyState.vue";
import TopologyNode from "./TopologyNode.vue";
import { formatBytes, formatPercent } from "../../lib/formatters.js";

defineProps({
  pools: { type: Array, required: true },
  normalizedPools: { type: Array, required: true },
  isExpanded: { type: Function, required: true },
  destroySubmitting: { type: Boolean, default: false },
});

const { t } = useI18n();
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
          <h3>{{ t("pools.overview") }}</h3>
          <p>{{ t("pools.overviewDescription") }}</p>
        </div>
      <button type="button" class="primary-button" @click="emit('create-pool')">{{ t("pools.createPool") }}</button>
    </div>

    <EmptyState
      v-if="!pools.length"
      :title="t('pools.emptyTitle')"
      :description="t('pools.emptyDescription')"
    />

    <div v-else class="table-shell">
      <table class="data-table">
        <thead>
          <tr>
            <th></th>
            <th>{{ t("pools.columns.name") }}</th>
            <th>{{ t("pools.columns.health") }}</th>
            <th>{{ t("pools.columns.size") }}</th>
            <th>{{ t("pools.columns.allocated") }}</th>
            <th>{{ t("pools.columns.free") }}</th>
            <th>{{ t("pools.columns.capacity") }}</th>
            <th>{{ t("pools.columns.fragmentation") }}</th>
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
                <button type="button" class="ghost-button" @click="emit('open-pool', pool)">{{ t("common.view") }}</button>
              </td>
            </tr>
            <tr v-if="isExpanded(pool)" class="pool-expand-row">
              <td colspan="9">
                <div class="pool-expand-shell">
                  <section class="pool-expand-panel">
                    <div class="pool-panel-header">
                      <h4>{{ t("pools.topology") }}</h4>
                      <button type="button" class="ghost-button" @click="emit('open-topology', pool)">{{ t("pools.editTopology") }}</button>
                    </div>
                    <ul class="topology-list" v-if="pool.status && Array.isArray(pool.status.config) && pool.status.config.length">
                      <TopologyNode v-for="node in pool.status.config" :key="node.name" :node="node" />
                    </ul>
                    <p v-else class="subtle-text">{{ t("pools.noTopology") }}</p>
                  </section>

                  <section class="pool-expand-panel">
                    <div class="pool-panel-header">
                      <h4>{{ t("pools.quickFacts.title") }}</h4>
                      <button
                        type="button"
                        class="danger-button"
                        :disabled="destroySubmitting"
                        @click="emit('destroy-pool', pool)"
                      >
                        {{ t("pools.destroyPool") }}
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
