<script setup>
import { useI18n } from "vue-i18n";

import DetailDrawer from "../common/DetailDrawer.vue";
import PropertyFieldList from "../common/PropertyFieldList.vue";
import PropertySection from "../common/PropertySection.vue";
import CommandResultList from "../common/CommandResultList.vue";

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  selectedPool: { type: Object, default: null },
  advancedReadonlyOpen: { type: Boolean, default: false },
  poolPropertyForce: { type: Boolean, default: false },
  changedItems: { type: Array, required: true },
  draftValues: { type: Object, required: true },
  submitting: { type: Boolean, default: false },
  destroySubmitting: { type: Boolean, default: false },
  propertyInput: { type: Function, required: true },
});

const { t } = useI18n();
const emit = defineEmits([
  "update:modelValue",
  "update:draft-values",
  "toggle-advanced",
  "open-confirm",
  "open-destroy",
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
    :title="t('pools.poolDetails')"
    :description="selectedPool ? selectedPool.name : ''"
    @update:modelValue="emit('update:modelValue', $event)"
  >
    <div v-if="selectedPool" class="drawer-section-list">
      <PropertySection :title="t('pools.readOnlyProperties')">
        <PropertyFieldList
          v-if="selectedPool.immutableProperties.common.length"
          :fields="selectedPool.immutableProperties.common"
          :meta-by-field="toMetaMap(selectedPool.immutableProperties.common)"
          readonly
          grid-class="detail-grid"
        />
        <p v-else class="subtle-text">{{ t("pools.noReadOnlyProperties") }}</p>

        <div v-if="selectedPool.immutableProperties.advanced.length" class="advanced-toggle-row">
          <button type="button" class="ghost-button" @click="emit('toggle-advanced')">
            {{ advancedReadonlyOpen ? t("common.hideAdvanced") : t("common.advanced") }}
          </button>
        </div>
        <PropertyFieldList
          v-if="advancedReadonlyOpen"
          :fields="selectedPool.immutableProperties.advanced"
          :meta-by-field="toMetaMap(selectedPool.immutableProperties.advanced)"
          readonly
          grid-class="detail-grid advanced-detail-grid"
        />
      </PropertySection>

      <PropertySection
        :title="t('pools.editableProperties')"
        :description="t('pools.editablePropertiesDescription')"
      >
        <template #actions>
          <div class="inline-action-controls">
            <label
              class="inline-checkbox"
              data-disabled="true"
              title="zpool set does not provide a force flag."
            >
              <input :checked="poolPropertyForce" type="checkbox" disabled />
              <span>{{ t("common.force") }}</span>
            </label>
            <button
              type="button"
              class="primary-button"
              :disabled="!changedItems.length || submitting"
              @click="emit('open-confirm')"
            >
              {{ submitting ? t("common.saving") : t("common.save") }}
            </button>
          </div>
        </template>

        <PropertyFieldList
          :fields="selectedPool.editableProperties"
          :model-value="draftValues"
          :meta-by-field="toMetaMap(selectedPool.editableProperties, t('common.currentPrefix'))"
          :get-input-spec="propertyInput"
          :disabled="submitting"
          grid-class="detail-grid editable-detail-grid"
          item-class="editable-property-card"
          @update:modelValue="emit('update:draft-values', $event)"
        />
        <p v-if="!selectedPool.editableProperties.length" class="subtle-text">
          {{ t("pools.noEditableProperties") }}
        </p>
      </PropertySection>

      <section v-if="changedItems.length" class="drawer-section">
        <h4>{{ t("common.pendingChanges") }}</h4>
        <CommandResultList :items="changedItems" empty-text="">
          <template #item="{ item }">
            <strong>{{ item.property }}</strong>
            <span class="subtle-text">{{ t("common.valueTransition", { from: item.oldValue || "-", to: item.newValue || "-" }) }}</span>
          </template>
        </CommandResultList>
      </section>

      <section class="drawer-section">
        <div class="drawer-section-header">
          <div>
            <h4>{{ t("common.dangerZone") }}</h4>
            <p class="subtle-text">{{ t("pools.dangerDescription") }}</p>
          </div>
          <button
            type="button"
            class="danger-button"
            :disabled="destroySubmitting"
            @click="emit('open-destroy')"
          >
            {{ t("pools.destroyPool") }}
          </button>
        </div>
      </section>
    </div>
  </DetailDrawer>
</template>
