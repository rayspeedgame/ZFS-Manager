<script setup>
import { useI18n } from "vue-i18n";

import DetailDrawer from "../common/DetailDrawer.vue";
import PropertyFieldList from "../common/PropertyFieldList.vue";
import PropertySection from "../common/PropertySection.vue";
import CommandResultList from "../common/CommandResultList.vue";

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  selectedPool: { type: Object, default: null },
  scrubStatus: { type: Object, default: null },
  scrubSubmitting: { type: Boolean, default: false },
  scrubSummary: { type: String, default: "" },
  scrubError: { type: String, default: "" },
  clearSubmitting: { type: Boolean, default: false },
  clearSummary: { type: String, default: "" },
  clearError: { type: String, default: "" },
  canClear: { type: Boolean, default: true },
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
  "start-scrub",
  "stop-scrub",
  "open-clear",
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

      <section class="drawer-section">
        <div class="drawer-section-header">
          <div class="scrub-header-copy">
            <h4>{{ t("pools.scrub.title") }}</h4>
            <p class="subtle-text">{{ t("pools.scrub.description") }}</p>
          </div>
          <div class="inline-action-controls scrub-header-actions">
            <button
              type="button"
              class="ghost-button"
              :disabled="scrubSubmitting || !(scrubStatus && scrubStatus.canStop)"
              @click="emit('stop-scrub')"
            >
              {{ t("pools.scrub.stop") }}
            </button>
            <button
              type="button"
              class="primary-button"
              :disabled="scrubSubmitting || !(scrubStatus && scrubStatus.canStart)"
              @click="emit('start-scrub')"
            >
              {{ t("pools.scrub.start") }}
            </button>
          </div>
        </div>
        <dl class="detail-grid scrub-detail-grid">
          <div class="scrub-scan-row">
            <dt>{{ t("pools.scrub.current") }}</dt>
            <dd>{{ scrubStatus?.raw || t("pools.quickFacts.notReported") }}</dd>
          </div>
          <div>
            <dt>{{ t("pools.scrub.progress") }}</dt>
            <dd>{{ scrubStatus?.active ? `${scrubStatus?.progress ?? 0}%` : "-" }}</dd>
          </div>
          <div>
            <dt>{{ t("pools.scrub.eta") }}</dt>
            <dd>{{ scrubStatus?.eta || "-" }}</dd>
          </div>
          <div>
            <dt>{{ t("pools.scrub.state") }}</dt>
            <dd>{{ scrubStatus?.active ? t("tasks.status.running") : (scrubStatus?.completed ? t("tasks.status.succeeded") : t("tasks.status.unknown")) }}</dd>
          </div>
        </dl>
        <p v-if="scrubSummary" class="notice-text">{{ scrubSummary }}</p>
        <p v-if="scrubError" class="error-text">{{ scrubError }}</p>
      </section>

      <section class="drawer-section">
        <div class="drawer-section-header">
          <div>
            <h4>{{ t("pools.maintenance.title") }}</h4>
            <p class="subtle-text">{{ t("pools.maintenance.description") }}</p>
          </div>
          <button
            type="button"
            class="ghost-button"
            :disabled="clearSubmitting || !canClear"
            @click="emit('open-clear')"
          >
            {{ t("pools.maintenance.clear") }}
          </button>
        </div>
        <p v-if="clearSummary" class="notice-text">{{ clearSummary }}</p>
        <p v-if="clearError" class="error-text">{{ clearError }}</p>
      </section>

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
