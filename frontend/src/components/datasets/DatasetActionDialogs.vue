<script setup>
import { useI18n } from "vue-i18n";

import ConfirmDialog from "../common/ConfirmDialog.vue";
import CommandLogPanel from "../common/CommandLogPanel.vue";
import CommandResultList from "../common/CommandResultList.vue";

defineProps({
  selectedDataset: { type: Object, default: null },
  changedItems: { type: Array, required: true },
  confirmDialogOpen: { type: Boolean, default: false },
  submitting: { type: Boolean, default: false },
  dialogPhase: { type: String, default: "confirm" },
  dialogSummary: { type: String, default: "" },
  dialogError: { type: String, default: "" },
  dialogResults: { type: Array, default: () => [] },
  terminalLogLines: { type: Array, default: () => [] },
  destroyConfirmDialogOpen: { type: Boolean, default: false },
  destroySubmitting: { type: Boolean, default: false },
  destroyDialogPhase: { type: String, default: "confirm" },
  destroyDialogSummary: { type: String, default: "" },
  destroyDialogError: { type: String, default: "" },
  destroyDialogResult: { type: Object, default: null },
  destroyTerminalLogLines: { type: Array, default: () => [] },
  createConfirmDialogOpen: { type: Boolean, default: false },
  createSubmitting: { type: Boolean, default: false },
  createDialogPhase: { type: String, default: "confirm" },
  createDialogSummary: { type: String, default: "" },
  createDialogError: { type: String, default: "" },
  createDialogResult: { type: Object, default: null },
  createTerminalLogLines: { type: Array, default: () => [] },
  canSubmitCreate: { type: Boolean, default: false },
  canDestroyDataset: { type: Boolean, default: false },
  createDraft: { type: Object, required: true },
  createPayload: { type: Object, required: true },
});

const { t } = useI18n();
const emit = defineEmits([
  "update:confirmDialogOpen",
  "update:destroyConfirmDialogOpen",
  "update:createConfirmDialogOpen",
  "confirm-property",
  "confirm-destroy",
  "confirm-create",
]);
</script>

<template>
  <ConfirmDialog
    :model-value="confirmDialogOpen"
    :busy="submitting"
    :can-confirm="Boolean(changedItems.length)"
    :result-mode="dialogPhase === 'result'"
    :confirm-text="dialogPhase === 'submitting' ? t('datasets.dialogs.applying') : t('datasets.dialogs.confirmApply')"
    :title="t('datasets.dialogs.confirmDatasetPropertyChanges')"
    :description="selectedDataset?.name || ''"
    @update:modelValue="emit('update:confirmDialogOpen', $event)"
    @confirm="emit('confirm-property')"
  >
    <div v-if="dialogPhase === 'confirm'" class="dialog-section-list">
      <p class="subtle-text">{{ t("datasets.dialogs.datasetChangesWillBeSent") }}</p>
      <CommandResultList :items="changedItems" empty-text="">
        <template #item="{ item }">
          <strong>{{ item.property }}</strong>
          <span class="subtle-text">{{ t("common.valueTransition", { from: item.old_value ?? '-', to: item.value }) }}</span>
        </template>
      </CommandResultList>
    </div>

    <div v-else-if="dialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>{{ t("datasets.dialogs.applyingDatasetPropertyChanges") }}</strong>
          <p class="subtle-text">{{ t("datasets.dialogs.applyingDatasetPropertyChangesDescription") }}</p>
        </div>
      </div>
    </div>

    <div v-else class="dialog-section-list">
      <p v-if="dialogSummary" class="notice-text">{{ dialogSummary }}</p>
      <p v-if="dialogError" class="error-text">{{ dialogError }}</p>

      <section>
        <h4 class="dialog-mini-heading">{{ t("common.resultList") }}</h4>
        <CommandResultList :items="dialogResults" />
      </section>

      <section>
        <h4 class="dialog-mini-heading">{{ t("common.sshTerminalLog") }}</h4>
        <CommandLogPanel :entries="terminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>

  <ConfirmDialog
    :model-value="destroyConfirmDialogOpen"
    :busy="destroySubmitting"
    :can-confirm="canDestroyDataset"
    :result-mode="destroyDialogPhase === 'result'"
    :confirm-text="destroyDialogPhase === 'submitting' ? t('datasets.dialogs.deleting') : t('datasets.dialogs.confirmDelete')"
    :title="t('datasets.dialogs.confirmDatasetDelete')"
    :description="selectedDataset?.name || ''"
    @update:modelValue="emit('update:destroyConfirmDialogOpen', $event)"
    @confirm="emit('confirm-destroy')"
  >
    <div v-if="destroyDialogPhase === 'confirm'" class="dialog-section-list">
      <p class="error-text">{{ t("datasets.dialogs.deleteWarning") }}</p>
      <ul class="result-list">
        <li class="result-list-item">
          <strong>{{ t("datasets.columns.type") }}</strong>
          <span class="subtle-text">{{ selectedDataset?.type || "-" }}</span>
        </li>
        <li class="result-list-item">
          <strong>{{ t("datasets.columns.name") }}</strong>
          <span class="subtle-text">{{ selectedDataset?.name || "-" }}</span>
        </li>
      </ul>
    </div>

    <div v-else-if="destroyDialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>{{ t("datasets.dialogs.deletingDataset") }}</strong>
          <p class="subtle-text">{{ t("datasets.dialogs.deletingDatasetDescription") }}</p>
        </div>
      </div>
    </div>

    <div v-else class="dialog-section-list">
      <p v-if="destroyDialogSummary" class="notice-text">{{ destroyDialogSummary }}</p>
      <p v-if="destroyDialogError" class="error-text">{{ destroyDialogError }}</p>

      <section>
        <h4 class="dialog-mini-heading">{{ t("common.result") }}</h4>
        <CommandResultList
          :items="destroyDialogResult ? [{ ...destroyDialogResult, label: destroyDialogResult.dataset, key: destroyDialogResult.dataset || 'dataset' }] : []"
          :empty-text="t('common.noResult')"
        />
      </section>

      <section>
        <h4 class="dialog-mini-heading">{{ t("common.sshTerminalLog") }}</h4>
        <CommandLogPanel :entries="destroyTerminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>

  <ConfirmDialog
    :model-value="createConfirmDialogOpen"
    :busy="createSubmitting"
    :can-confirm="canSubmitCreate"
    :result-mode="createDialogPhase === 'result'"
    :confirm-text="createDialogPhase === 'submitting' ? t('datasets.dialogs.creating') : t('datasets.dialogs.confirmCreate')"
    :title="t('datasets.dialogs.confirmDatasetCreation')"
    :description="createPayload.parent ? createPayload.parent + '/' + createPayload.name : t('datasets.dialogs.newChildDataset')"
    @update:modelValue="emit('update:createConfirmDialogOpen', $event)"
    @confirm="emit('confirm-create')"
  >
    <div v-if="createDialogPhase === 'confirm'" class="dialog-section-list">
      <p class="subtle-text">{{ t("datasets.dialogs.createWarning") }}</p>
      <ul class="result-list">
        <li class="result-list-item">
          <strong>{{ t("datasets.columns.type") }}</strong>
          <span class="subtle-text">{{ createDraft.type === "volume" ? "zvol" : t("datasets.create.dataset") }}</span>
        </li>
        <li class="result-list-item">
          <strong>{{ t("datasets.create.fullName") }}</strong>
          <span class="subtle-text">{{ createPayload.parent }}/{{ createPayload.name }}</span>
        </li>
        <li class="result-list-item">
          <strong>{{ t("pools.properties") }}</strong>
          <span class="subtle-text">{{ createPayload.properties.length ? createPayload.properties.map((item) => item.name + '=' + item.value).join(', ') : t('datasets.create.defaultPropertiesOnly') }}</span>
        </li>
      </ul>
    </div>

    <div v-else-if="createDialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>{{ t("datasets.dialogs.creatingTarget", { kind: createDraft.type === 'volume' ? 'zvol' : t('datasets.create.dataset') }) }}</strong>
          <p class="subtle-text">{{ t("datasets.dialogs.creatingTargetDescription") }}</p>
        </div>
      </div>
    </div>

    <div v-else class="dialog-section-list">
      <p v-if="createDialogSummary" class="notice-text">{{ createDialogSummary }}</p>
      <p v-if="createDialogError" class="error-text">{{ createDialogError }}</p>

      <section>
        <h4 class="dialog-mini-heading">{{ t("common.result") }}</h4>
        <CommandResultList
          :items="createDialogResult ? [{ ...createDialogResult, label: createDialogResult.dataset, key: createDialogResult.dataset || 'dataset' }] : []"
          :empty-text="t('common.noResult')"
        />
      </section>

      <section>
        <h4 class="dialog-mini-heading">{{ t("common.sshTerminalLog") }}</h4>
        <CommandLogPanel :entries="createTerminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>
</template>
