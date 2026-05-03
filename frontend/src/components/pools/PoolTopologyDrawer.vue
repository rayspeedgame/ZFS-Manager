<script setup>
import DetailDrawer from "../common/DetailDrawer.vue";
import PropertySection from "../common/PropertySection.vue";
import { formatBytes } from "../../lib/formatters.js";

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  selectedPool: { type: Object, default: null },
  topologyGroupSummary: { type: Array, required: true },
  topologyDraft: { type: Object, required: true },
  topologyCategoryOptions: { type: Array, required: true },
  topologyLayoutOptions: { type: Array, required: true },
  availableTopologyDevices: { type: Array, required: true },
  topologyPendingAdditions: { type: Array, required: true },
  topologySelectionSummary: { type: Array, required: true },
  topologyForce: { type: Boolean, default: false },
  topologySubmitting: { type: Boolean, default: false },
  removeSubmitting: { type: Boolean, default: false },
  topologyDeviceSelected: { type: Function, required: true },
  formatTopologyDeviceLabel: { type: Function, required: true },
  getRemovalTarget: { type: Function, required: true },
});

const emit = defineEmits([
  "update:modelValue",
  "update:topology-draft",
  "update:topology-force",
  "toggle-device",
  "open-confirm",
  "remove-target",
]);

function updateDraft(key, value) {
  emit("update:topology-draft", {
    ...props.topologyDraft,
    [key]: value,
  });
}
</script>

<template>
  <DetailDrawer
    :model-value="modelValue"
    title="Edit Pool Topology"
    :description="selectedPool ? selectedPool.name : ''"
    @update:modelValue="emit('update:modelValue', $event)"
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
                    @click="emit('remove-target', getRemovalTarget(item))"
                  >
                    Remove
                  </button>
                </div>
                <span class="subtle-text">Layout: {{ item.layout }} / State: {{ item.state || "UNKNOWN" }}</span>
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

      <PropertySection
        title="Add Devices"
        description="Select the topology role, layout, and exact devices before saving."
      >
        <template #actions>
          <div class="inline-action-controls">
            <label class="inline-checkbox">
              <input
                :checked="topologyForce"
                type="checkbox"
                @change="emit('update:topology-force', $event.target.checked)"
              />
              <span>Force</span>
            </label>
            <button
              type="button"
              class="primary-button"
              :disabled="!topologyPendingAdditions.length || topologySubmitting"
              @click="emit('open-confirm')"
            >
              {{ topologySubmitting ? "Saving..." : "Save" }}
            </button>
          </div>
        </template>

        <div class="topology-form-grid">
          <label class="form-field">
            <span>Category</span>
            <select
              :value="topologyDraft.category"
              class="property-field"
              :disabled="topologySubmitting"
              @change="updateDraft('category', $event.target.value)"
            >
              <option v-for="option in topologyCategoryOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </label>

          <label class="form-field">
            <span>Layout</span>
            <select
              :value="topologyDraft.layout"
              class="property-field"
              :disabled="topologySubmitting"
              @change="updateDraft('layout', $event.target.value)"
            >
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
                @change="emit('toggle-device', device.path)"
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
      </PropertySection>

      <section v-if="topologySelectionSummary.length" class="drawer-section">
        <h4>Pending Topology Addition</h4>
        <ul class="result-list">
          <li class="result-list-item">
            <strong>{{ topologyDraft.category }}</strong>
            <span class="subtle-text">Layout: {{ topologyDraft.layout }}</span>
            <span class="subtle-text">
              {{ topologySelectionSummary.map(formatTopologyDeviceLabel).join(", ") }}
            </span>
          </li>
        </ul>
      </section>
    </div>
  </DetailDrawer>
</template>
