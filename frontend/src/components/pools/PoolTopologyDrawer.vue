<script setup>
import { useI18n } from "vue-i18n";

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

const { t } = useI18n();
const emit = defineEmits([
  "update:modelValue",
  "update:topology-draft",
  "update:topology-force",
  "toggle-device",
  "open-confirm",
  "remove-target",
]);

function optionText(option) {
  // Support both legacy `label` options and newer translated `labelKey` options.
  return option?.labelKey ? t(option.labelKey) : option?.label ?? option?.value ?? "";
}

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
    :title="t('pools.editTopologyTitle')"
    :description="selectedPool ? selectedPool.name : ''"
    @update:modelValue="emit('update:modelValue', $event)"
  >
    <div v-if="selectedPool" class="drawer-section-list">
      <section class="drawer-section">
        <h4>{{ t("pools.currentTopology") }}</h4>
        <div class="topology-group-list" v-if="topologyGroupSummary.length">
          <article v-for="group in topologyGroupSummary" :key="group.name" class="topology-group-card">
            <div class="result-list-head">
              <strong>{{ group.label }}</strong>
              <span class="subtle-text">{{ t("common.groupCount", { count: group.items.length }) }}</span>
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
                    {{ t("pools.remove") }}
                  </button>
                </div>
                <span class="subtle-text">{{ t("pools.layoutValue", { value: item.layout }) }} / {{ t("pools.stateValue", { value: item.state || "UNKNOWN" }) }}</span>
                <div class="topology-member-card-list">
                  <article v-for="member in item.members" :key="member.path + ':' + member.diskId" class="topology-member-card">
                    <strong>{{ member.path }}</strong>
                    <div class="subtle-text">{{ member.diskId }}</div>
                    <div class="subtle-text">{{ member.model || t("common.unknownModel") }}</div>
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
            <p v-else class="subtle-text">{{ t("pools.currentGroupEmpty", { name: group.label.toLowerCase() }) }}</p>
          </article>
        </div>
      </section>

      <PropertySection
        :title="t('pools.addDevices')"
        :description="t('pools.addDevicesDescription')"
      >
        <template #actions>
          <div class="inline-action-controls">
            <label class="inline-checkbox">
              <input
                :checked="topologyForce"
                type="checkbox"
                @change="emit('update:topology-force', $event.target.checked)"
              />
              <span>{{ t("common.force") }}</span>
            </label>
            <button
              type="button"
              class="primary-button"
              :disabled="!topologyPendingAdditions.length || topologySubmitting"
              @click="emit('open-confirm')"
            >
              {{ topologySubmitting ? t("common.saving") : t("common.save") }}
            </button>
          </div>
        </template>

        <div class="topology-form-grid">
          <label class="form-field">
            <span>{{ t("pools.category") }}</span>
            <select
              :value="topologyDraft.category"
              class="property-field"
              :disabled="topologySubmitting"
              @change="updateDraft('category', $event.target.value)"
            >
              <option v-for="option in topologyCategoryOptions" :key="option.value" :value="option.value">
                {{ optionText(option) }}
              </option>
            </select>
          </label>

          <label class="form-field">
            <span>{{ t("pools.layout") }}</span>
            <select
              :value="topologyDraft.layout"
              class="property-field"
              :disabled="topologySubmitting"
              @change="updateDraft('layout', $event.target.value)"
            >
              <option v-for="option in topologyLayoutOptions" :key="option.value" :value="option.value">
                {{ optionText(option) }}
              </option>
            </select>
          </label>
        </div>

        <div class="topology-device-picker">
          <div class="result-list-head">
            <strong>{{ t("pools.availableDevices") }}</strong>
            <span class="subtle-text">{{ t("common.selectableCount", { count: availableTopologyDevices.length }) }}</span>
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
                <div class="subtle-text">{{ device.model || t("common.unknownModel") }}</div>
                <div class="subtle-text">{{ formatBytes(device.size) }}</div>
              </div>
            </label>
          </div>
          <p v-else class="subtle-text">{{ t("pools.noAvailableTopologyDevices") }}</p>
        </div>
      </PropertySection>

      <section v-if="topologySelectionSummary.length" class="drawer-section">
        <h4>{{ t("pools.pendingTopologyAddition") }}</h4>
        <ul class="result-list">
          <li class="result-list-item">
            <strong>{{ topologyDraft.category }}</strong>
            <span class="subtle-text">{{ t("pools.layoutValue", { value: topologyDraft.layout }) }}</span>
            <span class="subtle-text">
              {{ topologySelectionSummary.map(formatTopologyDeviceLabel).join(", ") }}
            </span>
          </li>
        </ul>
      </section>
    </div>
  </DetailDrawer>
</template>
