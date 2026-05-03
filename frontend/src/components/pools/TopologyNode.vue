<script setup>
import { computed } from "vue";

defineOptions({
  name: "TopologyNode",
});

const props = defineProps({
  node: { type: Object, required: true },
});

const isLeaf = computed(() => !Array.isArray(props.node.children) || !props.node.children.length);
const displayState = computed(() => resolveTopologyState(props.node));
const displayRead = computed(() => resolveTopologyMetric(props.node, "read"));
const displayWrite = computed(() => resolveTopologyMetric(props.node, "write"));
const displayCksum = computed(() => resolveTopologyMetric(props.node, "cksum"));

function resolveTopologyState(node) {
  const states = collectTopologyStates(node);
  if (!states.length) {
    return "UNKNOWN";
  }
  return states.reduce((worst, current) =>
    topologyStateSeverity(current) > topologyStateSeverity(worst) ? current : worst
  );
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
  return (
    {
      ONLINE: 1,
      AVAIL: 1,
      DEGRADED: 2,
      SUSPENDED: 3,
      OFFLINE: 4,
      REMOVED: 4,
      FAULTED: 5,
      UNAVAIL: 5,
      UNKNOWN: 6,
    }[state || "UNKNOWN"] || 6
  );
}
</script>

<template>
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
</template>
