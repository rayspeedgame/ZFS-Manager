<script setup>
import { useI18n } from "vue-i18n";

import DetailDrawer from "../common/DetailDrawer.vue";
import PropertyFieldList from "../common/PropertyFieldList.vue";
import PropertySection from "../common/PropertySection.vue";

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  createParent: { type: Object, default: null },
  createDraft: { type: Object, required: true },
  createCommonFields: { type: Array, required: true },
  createAdvancedFields: { type: Array, required: true },
  createAdvancedOpen: { type: Boolean, default: false },
  createForce: { type: Boolean, default: false },
  canSubmitCreate: { type: Boolean, default: false },
  getPropertyInput: { type: Function, required: true },
});

const { t } = useI18n();
const emit = defineEmits([
  "update:modelValue",
  "update:create-draft",
  "toggle-advanced",
  "open-confirm",
]);

function updateDraft(partial) {
  emit("update:create-draft", partial);
}

function updateBasics(key, value) {
  updateDraft({
    ...props.createDraft,
    [key]: value,
  });
}

function updateProperties(properties) {
  updateDraft({
    ...props.createDraft,
    properties,
  });
}
</script>

<template>
  <DetailDrawer
    :model-value="modelValue"
    :title="t('datasets.createChildDataset')"
    :description="createParent?.name || ''"
    @update:modelValue="emit('update:modelValue', $event)"
  >
    <div class="drawer-section-list">
      <section class="drawer-section">
        <h4>{{ t("pools.basic") }}</h4>
        <div class="topology-form-grid">
          <label class="form-field">
            <span>{{ t("datasets.columns.parent") }}</span>
            <input :value="createDraft.parent" type="text" class="property-field" disabled />
          </label>
          <label class="form-field">
            <span>{{ t("datasets.columns.type") }}</span>
            <select :value="createDraft.type" class="property-field" @change="updateBasics('type', $event.target.value)">
              <option value="filesystem">{{ t("datasets.create.dataset") }}</option>
              <option value="volume">zvol</option>
            </select>
          </label>
          <label class="form-field">
            <span>{{ t("datasets.columns.name") }}</span>
            <input
              :value="createDraft.name"
              type="text"
              class="property-field"
              placeholder="media"
              @input="updateBasics('name', $event.target.value)"
            />
          </label>
        </div>
      </section>

      <PropertySection
        :title="t('datasets.propertiesTitle')"
        :description="t('datasets.createDescription', { kind: createDraft.type === 'volume' ? 'zvol' : t('datasets.create.dataset') })"
      >
        <template #actions>
          <div class="inline-action-controls">
            <label
              class="inline-checkbox"
              data-disabled="true"
              :title="t('datasets.noForceInCreate')"
            >
              <input :checked="createForce" type="checkbox" disabled />
              <span>{{ t("common.force") }}</span>
            </label>
            <button type="button" class="primary-button" :disabled="!canSubmitCreate" @click="emit('open-confirm')">
              {{ t("common.create") }}
            </button>
          </div>
        </template>

        <PropertyFieldList
          :fields="createCommonFields"
          :model-value="createDraft.properties"
          :get-input-spec="getPropertyInput"
          :default-option-label="t('common.default')"
          grid-class="detail-grid editable-detail-grid"
          item-class="editable-property-card"
          @update:modelValue="updateProperties"
        />

        <div class="advanced-toggle-row">
          <button type="button" class="ghost-button" @click="emit('toggle-advanced')">
            {{ createAdvancedOpen ? t("common.hideAdvanced") : t("common.advanced") }}
          </button>
        </div>

        <PropertyFieldList
          v-if="createAdvancedOpen"
          :fields="createAdvancedFields"
          :model-value="createDraft.properties"
          :get-input-spec="getPropertyInput"
          :default-option-label="t('common.default')"
          grid-class="detail-grid editable-detail-grid advanced-detail-grid"
          item-class="editable-property-card"
          @update:modelValue="updateProperties"
        />
      </PropertySection>
    </div>
  </DetailDrawer>
</template>
