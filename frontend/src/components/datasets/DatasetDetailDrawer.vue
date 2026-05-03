<script setup>
import DetailDrawer from "../common/DetailDrawer.vue";
import PropertyFieldList from "../common/PropertyFieldList.vue";
import PropertySection from "../common/PropertySection.vue";
import CommandResultList from "../common/CommandResultList.vue";
import { formatBytes, formatDateTime } from "../../lib/formatters.js";

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  selectedDataset: { type: Object, default: null },
  draftValues: { type: Object, required: true },
  changedItems: { type: Array, required: true },
  fixedAdvancedOpen: { type: Boolean, default: false },
  customAdvancedOpen: { type: Boolean, default: false },
  canDestroyDataset: { type: Boolean, default: false },
  propertyForce: { type: Boolean, default: false },
  getPropertyInput: { type: Function, required: true },
});

const emit = defineEmits([
  "update:modelValue",
  "update:draft-values",
  "toggle-fixed-advanced",
  "toggle-custom-advanced",
  "open-confirm",
  "open-destroy-confirm",
]);

function toMetaMap(items, prefix = "") {
  return Object.fromEntries(
    items.map((item) => [
      item.name,
      {
        value: item.value,
        source: item.source,
        prefix,
      },
    ])
  );
}
</script>

<template>
  <DetailDrawer
    :model-value="modelValue"
    title="Dataset Details"
    :description="selectedDataset?.name || ''"
    @update:modelValue="emit('update:modelValue', $event)"
  >
    <div v-if="selectedDataset" class="drawer-section-list">
      <section class="drawer-section">
        <h4>Overview</h4>
        <dl class="detail-grid">
          <div><dt>Type</dt><dd>{{ selectedDataset.type }}</dd></div>
          <div><dt>Mountpoint</dt><dd>{{ selectedDataset.mountpoint || "-" }}</dd></div>
          <div><dt>Used</dt><dd>{{ formatBytes(selectedDataset.used) }}</dd></div>
          <div><dt>Available</dt><dd>{{ formatBytes(selectedDataset.avail) }}</dd></div>
          <div><dt>Referenced</dt><dd>{{ formatBytes(selectedDataset.refer) }}</dd></div>
          <div><dt>Compression</dt><dd>{{ selectedDataset.compressionDisplay }}</dd></div>
          <div><dt>Created</dt><dd>{{ formatDateTime(Number(selectedDataset.creation || 0) * 1000) }}</dd></div>
          <div><dt>Readonly</dt><dd>{{ selectedDataset.readonly || "-" }}</dd></div>
        </dl>
      </section>

      <PropertySection
        title="Fixed Properties"
        description="Read-only properties for the current dataset."
      >
        <PropertyFieldList
          v-if="selectedDataset.fixedProperties.common.length"
          :fields="selectedDataset.fixedProperties.common"
          :meta-by-field="toMetaMap(selectedDataset.fixedProperties.common)"
          readonly
          grid-class="detail-grid"
        />
        <p v-else class="subtle-text">No common fixed properties were reported.</p>

        <div class="advanced-toggle-row">
          <button type="button" class="ghost-button" @click="emit('toggle-fixed-advanced')">
            {{ fixedAdvancedOpen ? "Hide Advanced" : "Advanced" }}
          </button>
        </div>

        <PropertyFieldList
          v-if="fixedAdvancedOpen && selectedDataset.fixedProperties.advanced.length"
          :fields="selectedDataset.fixedProperties.advanced"
          :meta-by-field="toMetaMap(selectedDataset.fixedProperties.advanced)"
          readonly
          grid-class="detail-grid advanced-detail-grid"
        />
        <p v-else-if="fixedAdvancedOpen" class="subtle-text">No advanced fixed properties were reported.</p>
      </PropertySection>

      <PropertySection
        title="Custom Properties"
        description="Editable dataset properties. Changes follow the same confirm-and-refresh flow as pools."
      >
        <template #actions>
          <div class="inline-action-controls">
            <label
              class="inline-checkbox"
              data-disabled="true"
              title="zfs set does not provide a force flag."
            >
              <input :checked="propertyForce" type="checkbox" disabled />
              <span>Force</span>
            </label>
            <button type="button" class="primary-button" :disabled="!changedItems.length" @click="emit('open-confirm')">
              Apply Changes
            </button>
          </div>
        </template>

        <PropertyFieldList
          v-if="selectedDataset.customProperties.common.length"
          :fields="selectedDataset.customProperties.common"
          :model-value="draftValues"
          :meta-by-field="toMetaMap(selectedDataset.customProperties.common, 'Current: ')"
          :get-input-spec="getPropertyInput"
          grid-class="detail-grid editable-detail-grid"
          item-class="editable-property-card"
          @update:modelValue="emit('update:draft-values', $event)"
        />
        <p v-else class="subtle-text">No common editable properties are available for this dataset type.</p>

        <div class="advanced-toggle-row">
          <button type="button" class="ghost-button" @click="emit('toggle-custom-advanced')">
            {{ customAdvancedOpen ? "Hide Advanced" : "Advanced" }}
          </button>
        </div>

        <PropertyFieldList
          v-if="customAdvancedOpen && selectedDataset.customProperties.advanced.length"
          :fields="selectedDataset.customProperties.advanced"
          :model-value="draftValues"
          :meta-by-field="toMetaMap(selectedDataset.customProperties.advanced, 'Current: ')"
          :get-input-spec="getPropertyInput"
          grid-class="detail-grid editable-detail-grid advanced-detail-grid"
          item-class="editable-property-card"
          @update:modelValue="emit('update:draft-values', $event)"
        />
        <p v-else-if="customAdvancedOpen" class="subtle-text">No advanced editable properties are available for this dataset type.</p>
      </PropertySection>

      <section class="drawer-section">
        <div class="drawer-section-header">
          <div>
            <h4>Danger Zone</h4>
            <p class="subtle-text">
              Permanently delete this {{ selectedDataset.type === "volume" ? "zvol" : selectedDataset.type }} with the same SSH confirmation flow.
            </p>
          </div>
          <button
            type="button"
            class="danger-button"
            :disabled="!canDestroyDataset"
            @click="emit('open-destroy-confirm')"
          >
            Delete
          </button>
        </div>
        <p v-if="!canDestroyDataset" class="subtle-text">
          Root datasets are protected here. Use pool destroy from the Pools view if you really need to remove the whole pool.
        </p>
      </section>

      <section v-if="changedItems.length" class="drawer-section">
        <h4>Pending Changes</h4>
        <CommandResultList :items="changedItems" empty-text="" :status-formatter="null">
          <template #item="{ item }">
            <strong>{{ item.property }}</strong>
            <span class="subtle-text">{{ item.old_value ?? "-" }} -> {{ item.value }}</span>
          </template>
        </CommandResultList>
      </section>
    </div>
  </DetailDrawer>
</template>
