<script setup>
import { useI18n } from "vue-i18n";

import DetailDrawer from "../common/DetailDrawer.vue";
import PropertyFieldList from "../common/PropertyFieldList.vue";
import { formatBytes } from "../../lib/formatters.js";

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  createPoolStepItems: { type: Array, required: true },
  createPoolStep: { type: String, required: true },
  createPoolDraft: { type: Object, required: true },
  createPoolPropertyFields: { type: Array, required: true },
  createPoolRootCommonFields: { type: Array, required: true },
  createPoolRootAdvancedFields: { type: Array, required: true },
  createPoolRootAdvancedOpen: { type: Boolean, default: false },
  createPoolDataLayoutOptions: { type: Array, required: true },
  createPoolAuxLayoutOptions: { type: Array, required: true },
  createPoolAvailableDataDevices: { type: Array, required: true },
  createPoolAvailableAuxDevices: { type: Array, required: true },
  createPoolDataSelectionSummary: { type: Array, required: true },
  createPoolAuxSelectionSummary: { type: Array, required: true },
  createPoolReviewGroups: { type: Array, required: true },
  createPoolPayload: { type: Object, required: true },
  createPoolSubmitting: { type: Boolean, default: false },
  createPoolForce: { type: Boolean, default: false },
  canAdvanceCreatePool: { type: Boolean, default: false },
  canSubmitCreatePool: { type: Boolean, default: false },
  createPoolDeviceSelected: { type: Function, required: true },
  rootDatasetPropertyInput: { type: Function, required: true },
  topologyCategoryOptions: { type: Array, required: true },
  formatTopologyDeviceLabel: { type: Function, required: true },
});

const { t } = useI18n();
const emit = defineEmits([
  "update:modelValue",
  "set-step",
  "prev-step",
  "next-step",
  "update:create-pool-draft",
  "toggle-root-advanced",
  "toggle-device",
  "add-vdev",
  "remove-vdev",
  "update:create-pool-force",
  "open-confirm",
]);

function optionText(option) {
  // Support both legacy `label` options and newer translated `labelKey` options.
  return option?.labelKey ? t(option.labelKey) : option?.label ?? option?.value ?? "";
}

function updateDraft(nextDraft) {
  emit("update:create-pool-draft", nextDraft);
}

function updateBasicProperty(key, value) {
  updateDraft({
    ...props.createPoolDraft,
    [key]: value,
  });
}

function updateNestedDraft(path, key, value) {
  updateDraft({
    ...props.createPoolDraft,
    [path]: {
      ...props.createPoolDraft[path],
      [key]: value,
    },
  });
}

function updatePropertyMap(path, value) {
  updateDraft({
    ...props.createPoolDraft,
    [path]: value,
  });
}
</script>

<template>
  <DetailDrawer
    :model-value="modelValue"
    :title="t('pools.createPoolTitle')"
    :description="t('pools.createPoolDescription')"
    @update:modelValue="emit('update:modelValue', $event)"
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
            @click="emit('set-step', item.key)"
          >
            {{ item.label }}
          </button>
        </div>
      </section>

      <section v-if="createPoolStep === 'basic'" class="drawer-section">
        <h4>{{ t("pools.basic") }}</h4>
        <div class="topology-form-grid">
          <label class="form-field">
            <span>{{ t("pools.poolName") }}</span>
            <input
              :value="createPoolDraft.name"
              type="text"
              class="property-field"
              placeholder="tank2"
              :disabled="createPoolSubmitting"
              @input="updateBasicProperty('name', $event.target.value)"
            />
          </label>
        </div>
        <PropertyFieldList
          :fields="createPoolPropertyFields.map(([name, config]) => ({ name, labelKey: config.labelKey, label: config.label }))"
          :model-value="createPoolDraft.properties"
          :get-input-spec="(name) => createPoolPropertyFields.find(([field]) => field === name)?.[1]"
          :disabled="createPoolSubmitting"
          grid-class="detail-grid editable-detail-grid"
          item-class="editable-property-card"
          @update:modelValue="updatePropertyMap('properties', $event)"
        />
      </section>

      <section v-if="createPoolStep === 'rootfs'" class="drawer-section">
        <div class="drawer-section-header">
          <div>
            <h4>{{ t("pools.rootDataset") }}</h4>
            <p class="subtle-text">{{ t("pools.rootDatasetDescription") }}</p>
          </div>
        </div>

        <PropertyFieldList
          :fields="createPoolRootCommonFields"
          :model-value="createPoolDraft.rootDatasetProperties"
          :get-input-spec="rootDatasetPropertyInput"
          :default-option-label="t('common.default')"
          :disabled="createPoolSubmitting"
          grid-class="detail-grid editable-detail-grid"
          item-class="editable-property-card"
          @update:modelValue="updatePropertyMap('rootDatasetProperties', $event)"
        />

        <div class="advanced-toggle-row">
          <button type="button" class="ghost-button" @click="emit('toggle-root-advanced')">
            {{ createPoolRootAdvancedOpen ? t("common.hideAdvanced") : t("common.advanced") }}
          </button>
        </div>

        <PropertyFieldList
          v-if="createPoolRootAdvancedOpen"
          :fields="createPoolRootAdvancedFields"
          :model-value="createPoolDraft.rootDatasetProperties"
          :get-input-spec="rootDatasetPropertyInput"
          :default-option-label="t('common.default')"
          :disabled="createPoolSubmitting"
          grid-class="detail-grid editable-detail-grid advanced-detail-grid"
          item-class="editable-property-card"
          @update:modelValue="updatePropertyMap('rootDatasetProperties', $event)"
        />
      </section>

      <section v-if="createPoolStep === 'data'" class="drawer-section">
        <div class="drawer-section-header">
          <div>
            <h4>{{ t("pools.dataVdevs") }}</h4>
            <p class="subtle-text">{{ t("pools.dataVdevsDescription") }}</p>
          </div>
          <button type="button" class="primary-button" :disabled="!createPoolDraft.dataBuilder.devices.length || createPoolSubmitting" @click="emit('add-vdev', 'dataBuilder')">
            {{ t("pools.addDataVdev") }}
          </button>
        </div>
        <div class="topology-form-grid">
          <label class="form-field">
            <span>{{ t("pools.layout") }}</span>
            <select
              :value="createPoolDraft.dataBuilder.layout"
              class="property-field"
              :disabled="createPoolSubmitting"
              @change="updateNestedDraft('dataBuilder', 'layout', $event.target.value)"
            >
              <option v-for="option in createPoolDataLayoutOptions" :key="option.value" :value="option.value">{{ optionText(option) }}</option>
            </select>
          </label>
        </div>
        <div class="topology-device-picker">
          <div class="result-list-head">
            <strong>{{ t("pools.availableDataDevices") }}</strong>
            <span class="subtle-text">{{ t("common.selectableCount", { count: createPoolAvailableDataDevices.length }) }}</span>
          </div>
          <div v-if="createPoolAvailableDataDevices.length" class="topology-device-list">
            <label
              v-for="device in createPoolAvailableDataDevices"
              :key="'data-' + (device.commandPath || device.path)"
              class="topology-device-option"
              :data-selected="createPoolDeviceSelected('dataBuilder', device.commandPath || device.path)"
            >
              <input
                type="checkbox"
                :checked="createPoolDeviceSelected('dataBuilder', device.commandPath || device.path)"
                :disabled="createPoolSubmitting"
                @change="emit('toggle-device', 'dataBuilder', device.commandPath || device.path)"
              />
              <div>
                <strong>{{ device.displayName || device.path }}</strong>
                <div class="subtle-text">{{ device.diskId }}</div>
                <div class="subtle-text">{{ device.kernelPath || device.path }}</div>
                <div v-if="device.byIdPath" class="subtle-text">{{ device.byIdPath }}</div>
                <div class="subtle-text">{{ device.model || t("common.unknownModel") }}</div>
                <div class="subtle-text">{{ formatBytes(device.size) }}</div>
              </div>
            </label>
          </div>
        </div>
        <section v-if="createPoolDataSelectionSummary.length || createPoolDraft.dataVdevs.length" class="drawer-section">
          <h4>{{ t("pools.plannedDataVdevs") }}</h4>
          <ul class="result-list">
            <li v-for="(item, index) in createPoolDraft.dataVdevs" :key="'data-vdev-' + index" class="result-list-item">
              <div class="result-list-head">
                <strong>{{ t("pools.categories.data") }}</strong>
                <button type="button" class="ghost-button" :disabled="createPoolSubmitting" @click="emit('remove-vdev', 'dataVdevs', index)">{{ t("pools.remove") }}</button>
              </div>
              <span class="subtle-text">{{ t("pools.layoutValue", { value: item.layout }) }}</span>
              <span class="subtle-text">{{ item.devices.join(', ') }}</span>
            </li>
            <li v-if="createPoolDataSelectionSummary.length" class="result-list-item">
              <strong>{{ t("pools.pendingBuilder") }}</strong>
              <span class="subtle-text">{{ t("pools.layoutValue", { value: createPoolDraft.dataBuilder.layout }) }}</span>
              <span class="subtle-text">{{ createPoolDataSelectionSummary.map(formatTopologyDeviceLabel).join(', ') }}</span>
            </li>
          </ul>
        </section>
      </section>

      <section v-if="createPoolStep === 'aux'" class="drawer-section">
        <div class="drawer-section-header">
          <div>
            <h4>{{ t("pools.extraClasses") }}</h4>
            <p class="subtle-text">{{ t("pools.extraClassesDescription") }}</p>
          </div>
          <button type="button" class="primary-button" :disabled="!createPoolDraft.auxBuilder.devices.length || createPoolSubmitting" @click="emit('add-vdev', 'auxBuilder')">
            {{ t("pools.addClass") }}
          </button>
        </div>
        <div class="topology-form-grid">
          <label class="form-field">
            <span>{{ t("pools.category") }}</span>
            <select
              :value="createPoolDraft.auxBuilder.category"
              class="property-field"
              :disabled="createPoolSubmitting"
              @change="updateNestedDraft('auxBuilder', 'category', $event.target.value)"
            >
              <option v-for="option in topologyCategoryOptions" :key="option.value" :value="option.value">{{ optionText(option) }}</option>
            </select>
          </label>
          <label class="form-field">
            <span>{{ t("pools.layout") }}</span>
            <select
              :value="createPoolDraft.auxBuilder.layout"
              class="property-field"
              :disabled="createPoolSubmitting"
              @change="updateNestedDraft('auxBuilder', 'layout', $event.target.value)"
            >
              <option v-for="option in createPoolAuxLayoutOptions" :key="option.value" :value="option.value">{{ optionText(option) }}</option>
            </select>
          </label>
        </div>
        <div class="topology-device-picker">
          <div class="result-list-head">
            <strong>{{ t("pools.availableDevices") }}</strong>
            <span class="subtle-text">{{ t("common.selectableCount", { count: createPoolAvailableAuxDevices.length }) }}</span>
          </div>
          <div v-if="createPoolAvailableAuxDevices.length" class="topology-device-list">
            <label
              v-for="device in createPoolAvailableAuxDevices"
              :key="'aux-' + (device.commandPath || device.path)"
              class="topology-device-option"
              :data-selected="createPoolDeviceSelected('auxBuilder', device.commandPath || device.path)"
            >
              <input
                type="checkbox"
                :checked="createPoolDeviceSelected('auxBuilder', device.commandPath || device.path)"
                :disabled="createPoolSubmitting"
                @change="emit('toggle-device', 'auxBuilder', device.commandPath || device.path)"
              />
              <div>
                <strong>{{ device.displayName || device.path }}</strong>
                <div class="subtle-text">{{ device.diskId }}</div>
                <div class="subtle-text">{{ device.kernelPath || device.path }}</div>
                <div v-if="device.byIdPath" class="subtle-text">{{ device.byIdPath }}</div>
                <div class="subtle-text">{{ device.model || t("common.unknownModel") }}</div>
                <div class="subtle-text">{{ formatBytes(device.size) }}</div>
              </div>
            </label>
          </div>
        </div>
        <section v-if="createPoolAuxSelectionSummary.length || createPoolDraft.auxVdevs.length" class="drawer-section">
          <h4>{{ t("pools.plannedExtraClasses") }}</h4>
          <ul class="result-list">
            <li v-for="(item, index) in createPoolDraft.auxVdevs" :key="'aux-vdev-' + index" class="result-list-item">
              <div class="result-list-head">
                <strong>{{ item.category }}</strong>
                <button type="button" class="ghost-button" :disabled="createPoolSubmitting" @click="emit('remove-vdev', 'auxVdevs', index)">{{ t("pools.remove") }}</button>
              </div>
              <span class="subtle-text">{{ t("pools.layoutValue", { value: item.layout }) }}</span>
              <span class="subtle-text">{{ item.devices.join(', ') }}</span>
            </li>
            <li v-if="createPoolAuxSelectionSummary.length" class="result-list-item">
              <strong>{{ t("pools.pendingBuilder") }}</strong>
              <span class="subtle-text">{{ createPoolDraft.auxBuilder.category }} / {{ createPoolDraft.auxBuilder.layout }}</span>
              <span class="subtle-text">{{ createPoolAuxSelectionSummary.map(formatTopologyDeviceLabel).join(', ') }}</span>
            </li>
          </ul>
        </section>
      </section>

      <section v-if="createPoolStep === 'review'" class="drawer-section">
        <h4>{{ t("pools.review") }}</h4>
        <ul class="result-list">
          <li class="result-list-item">
            <strong>{{ t("pools.poolName") }}</strong>
            <span class="subtle-text">{{ createPoolPayload.name || "-" }}</span>
          </li>
          <li class="result-list-item">
            <strong>{{ t("common.force") }}</strong>
            <span class="subtle-text">{{ createPoolPayload.force ? "on" : "off" }}</span>
          </li>
          <li class="result-list-item">
            <strong>{{ t("pools.properties") }}</strong>
            <span class="subtle-text">
              {{ createPoolPayload.properties.length ? createPoolPayload.properties.map((item) => item.name + '=' + item.value).join(', ') : t('pools.noExtraProperties') }}
            </span>
          </li>
          <li class="result-list-item">
            <strong>{{ t("pools.rootDatasetProperties") }}</strong>
            <span class="subtle-text">
              {{ createPoolPayload.root_dataset_properties.length ? createPoolPayload.root_dataset_properties.map((item) => item.name + '=' + item.value).join(', ') : t('pools.defaultRootDatasetProperties') }}
            </span>
          </li>
        </ul>
        <div class="topology-group-list">
          <article v-for="group in createPoolReviewGroups" :key="group.label" class="topology-group-card">
            <div class="result-list-head">
              <strong>{{ group.label }}</strong>
              <span class="subtle-text">{{ t("common.itemCount", { count: group.items.length }) }}</span>
            </div>
            <ul class="simple-detail-list" v-if="group.items.length">
              <li v-for="(item, index) in group.items" :key="group.label + ':' + index">
                <strong>{{ item.category }}</strong>
                <span class="subtle-text">{{ item.layout }}</span>
                <span class="subtle-text">{{ item.devices.join(', ') }}</span>
              </li>
            </ul>
            <p v-else class="subtle-text">{{ t("pools.reviewNoItems") }}</p>
          </article>
        </div>
      </section>

      <section class="drawer-section">
        <div class="dialog-actions create-pool-actions">
          <button type="button" class="ghost-button" :disabled="createPoolSubmitting || createPoolStep === 'basic'" @click="emit('prev-step')">{{ t("common.back") }}</button>
          <button
            v-if="createPoolStep !== 'review'"
            type="button"
            class="primary-button"
            :disabled="createPoolSubmitting || !canAdvanceCreatePool"
            @click="emit('next-step')"
          >
            {{ t("common.next") }}
          </button>
          <label v-if="createPoolStep === 'review'" class="inline-checkbox">
            <input
              :checked="createPoolForce"
              type="checkbox"
              @change="emit('update:create-pool-force', $event.target.checked)"
            />
            <span>{{ t("common.force") }}</span>
          </label>
          <button
            v-if="createPoolStep === 'review'"
            type="button"
            class="primary-button"
            :disabled="createPoolSubmitting || !canSubmitCreatePool"
            @click="emit('open-confirm')"
          >
            {{ t("pools.createPool") }}
          </button>
        </div>
      </section>
    </div>
  </DetailDrawer>
</template>
