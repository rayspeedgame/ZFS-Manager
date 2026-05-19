<script setup>
import { useI18n } from "vue-i18n";

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
  snapshotDraftName: { type: String, default: "" },
  fixedAdvancedOpen: { type: Boolean, default: false },
  customAdvancedOpen: { type: Boolean, default: false },
  canDestroyDataset: { type: Boolean, default: false },
  canCreateSnapshot: { type: Boolean, default: false },
  canSubmitSnapshot: { type: Boolean, default: false },
  propertyForce: { type: Boolean, default: false },
  getPropertyInput: { type: Function, required: true },
});

const { t } = useI18n();
const emit = defineEmits([
  "update:modelValue",
  "update:draft-values",
  "toggle-fixed-advanced",
  "toggle-custom-advanced",
  "update:snapshot-draft-name",
  "open-confirm",
  "open-destroy-confirm",
  "open-snapshot-confirm",
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
    :title="t('datasets.datasetDetails')"
    :description="selectedDataset?.name || ''"
    @update:modelValue="emit('update:modelValue', $event)"
  >
    <div v-if="selectedDataset" class="drawer-section-list">
      <section class="drawer-section">
        <h4>{{ t("common.overview") }}</h4>
        <dl class="detail-grid">
          <div><dt>{{ t("datasets.detail.type") }}</dt><dd>{{ selectedDataset.type }}</dd></div>
          <div><dt>{{ t("datasets.detail.mountpoint") }}</dt><dd>{{ selectedDataset.mountpoint || "-" }}</dd></div>
          <div><dt>{{ t("datasets.detail.used") }}</dt><dd>{{ formatBytes(selectedDataset.used) }}</dd></div>
          <div><dt>{{ t("datasets.detail.available") }}</dt><dd>{{ formatBytes(selectedDataset.avail) }}</dd></div>
          <div><dt>{{ t("datasets.detail.referenced") }}</dt><dd>{{ formatBytes(selectedDataset.refer) }}</dd></div>
          <div><dt>{{ t("datasets.detail.compression") }}</dt><dd>{{ selectedDataset.compressionDisplay }}</dd></div>
          <div><dt>{{ t("datasets.detail.created") }}</dt><dd>{{ formatDateTime(Number(selectedDataset.creation || 0) * 1000) }}</dd></div>
          <div><dt>{{ t("datasets.detail.readonly") }}</dt><dd>{{ selectedDataset.readonly || "-" }}</dd></div>
        </dl>
      </section>

      <section v-if="canCreateSnapshot" class="drawer-section">
        <div class="drawer-section-header">
          <div>
            <h4>{{ t("datasets.snapshot.title") }}</h4>
            <p class="subtle-text">{{ t("datasets.snapshot.description") }}</p>
          </div>
          <button
            type="button"
            class="primary-button"
            :disabled="!canSubmitSnapshot"
            @click="emit('open-snapshot-confirm')"
          >
            {{ t("datasets.snapshot.create") }}
          </button>
        </div>
        <div class="detail-grid editable-detail-grid">
          <label class="editable-property-card">
            <span>{{ t("datasets.snapshot.name") }}</span>
            <input
              class="property-field"
              type="text"
              :value="snapshotDraftName"
              :placeholder="t('datasets.snapshot.placeholder')"
              @input="emit('update:snapshot-draft-name', $event.target.value)"
            />
          </label>
          <div class="editable-property-card">
            <span>{{ t("datasets.snapshot.preview") }}</span>
            <strong>{{ selectedDataset?.name }}@{{ snapshotDraftName || t("datasets.snapshot.placeholderName") }}</strong>
          </div>
        </div>
      </section>

      <PropertySection
        :title="t('datasets.fixedProperties')"
        :description="t('datasets.fixedPropertiesDescription')"
      >
        <PropertyFieldList
          v-if="selectedDataset.fixedProperties.common.length"
          :fields="selectedDataset.fixedProperties.common"
          :meta-by-field="toMetaMap(selectedDataset.fixedProperties.common)"
          readonly
          grid-class="detail-grid"
        />
        <p v-else class="subtle-text">{{ t("datasets.noCommonFixedProperties") }}</p>

        <div class="advanced-toggle-row">
          <button type="button" class="ghost-button" @click="emit('toggle-fixed-advanced')">
            {{ fixedAdvancedOpen ? t("common.hideAdvanced") : t("common.advanced") }}
          </button>
        </div>

        <PropertyFieldList
          v-if="fixedAdvancedOpen && selectedDataset.fixedProperties.advanced.length"
          :fields="selectedDataset.fixedProperties.advanced"
          :meta-by-field="toMetaMap(selectedDataset.fixedProperties.advanced)"
          readonly
          grid-class="detail-grid advanced-detail-grid"
        />
        <p v-else-if="fixedAdvancedOpen" class="subtle-text">{{ t("datasets.noAdvancedFixedProperties") }}</p>
      </PropertySection>

      <PropertySection
        :title="t('datasets.customProperties')"
        :description="t('datasets.customPropertiesDescription')"
      >
        <template #actions>
          <div class="inline-action-controls">
            <label
              class="inline-checkbox"
              data-disabled="true"
              :title="t('datasets.noForceInSet')"
            >
              <input :checked="propertyForce" type="checkbox" disabled />
              <span>{{ t("common.force") }}</span>
            </label>
            <button type="button" class="primary-button" :disabled="!changedItems.length" @click="emit('open-confirm')">
              {{ t("datasets.applyChanges") }}
            </button>
          </div>
        </template>

        <PropertyFieldList
          v-if="selectedDataset.customProperties.common.length"
          :fields="selectedDataset.customProperties.common"
          :model-value="draftValues"
          :meta-by-field="toMetaMap(selectedDataset.customProperties.common, t('common.currentPrefix'))"
          :get-input-spec="getPropertyInput"
          grid-class="detail-grid editable-detail-grid"
          item-class="editable-property-card"
          @update:modelValue="emit('update:draft-values', $event)"
        />
        <p v-else class="subtle-text">{{ t("datasets.noCommonEditableProperties") }}</p>

        <div class="advanced-toggle-row">
          <button type="button" class="ghost-button" @click="emit('toggle-custom-advanced')">
            {{ customAdvancedOpen ? t("common.hideAdvanced") : t("common.advanced") }}
          </button>
        </div>

        <PropertyFieldList
          v-if="customAdvancedOpen && selectedDataset.customProperties.advanced.length"
          :fields="selectedDataset.customProperties.advanced"
          :model-value="draftValues"
          :meta-by-field="toMetaMap(selectedDataset.customProperties.advanced, t('common.currentPrefix'))"
          :get-input-spec="getPropertyInput"
          grid-class="detail-grid editable-detail-grid advanced-detail-grid"
          item-class="editable-property-card"
          @update:modelValue="emit('update:draft-values', $event)"
        />
        <p v-else-if="customAdvancedOpen" class="subtle-text">{{ t("datasets.noAdvancedEditableProperties") }}</p>
      </PropertySection>

      <section class="drawer-section">
        <div class="drawer-section-header">
          <div>
            <h4>{{ t("common.dangerZone") }}</h4>
            <p class="subtle-text">
              {{ t("datasets.dangerDescription", { kind: selectedDataset.type === 'volume' ? 'zvol' : selectedDataset.type }) }}
            </p>
          </div>
          <button
            type="button"
            class="danger-button"
            :disabled="!canDestroyDataset"
            @click="emit('open-destroy-confirm')"
          >
            {{ t("common.delete") }}
          </button>
        </div>
        <p v-if="!canDestroyDataset" class="subtle-text">
          {{ t("datasets.rootDatasetProtected") }}
        </p>
      </section>

      <section v-if="changedItems.length" class="drawer-section">
        <h4>{{ t("common.pendingChanges") }}</h4>
        <CommandResultList :items="changedItems" empty-text="" :status-formatter="null">
          <template #item="{ item }">
            <strong>{{ item.property }}</strong>
            <span class="subtle-text">{{ t("common.valueTransition", { from: item.old_value ?? "-", to: item.value }) }}</span>
          </template>
        </CommandResultList>
      </section>
    </div>
  </DetailDrawer>
</template>
