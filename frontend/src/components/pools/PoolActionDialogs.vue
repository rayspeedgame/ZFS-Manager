<script setup>
import { useI18n } from "vue-i18n";

import ConfirmDialog from "../common/ConfirmDialog.vue";
import CommandResultList from "../common/CommandResultList.vue";
import CommandLogPanel from "../common/CommandLogPanel.vue";

defineProps({
  selectedPool: { type: Object, default: null },
  selectedRemovalTarget: { type: Object, default: null },
  changedItems: { type: Array, required: true },
  confirmDialogOpen: { type: Boolean, default: false },
  submitting: { type: Boolean, default: false },
  dialogPhase: { type: String, default: "confirm" },
  dialogSummary: { type: String, default: "" },
  dialogError: { type: String, default: "" },
  dialogResults: { type: Array, default: () => [] },
  terminalLogLines: { type: Array, default: () => [] },
  topologyConfirmDialogOpen: { type: Boolean, default: false },
  topologySubmitting: { type: Boolean, default: false },
  topologyDialogPhase: { type: String, default: "confirm" },
  topologyDialogSummary: { type: String, default: "" },
  topologyDialogError: { type: String, default: "" },
  topologyDialogResults: { type: Array, default: () => [] },
  topologyTerminalLogLines: { type: Array, default: () => [] },
  topologyPendingAdditions: { type: Array, default: () => [] },
  topologyForce: { type: Boolean, default: false },
  topologyConfirmSummary: { type: Array, default: () => [] },
  createPoolConfirmDialogOpen: { type: Boolean, default: false },
  createPoolSubmitting: { type: Boolean, default: false },
  createPoolDialogPhase: { type: String, default: "confirm" },
  createPoolDialogSummary: { type: String, default: "" },
  createPoolDialogError: { type: String, default: "" },
  createPoolDialogResult: { type: Object, default: null },
  createPoolTerminalLogLines: { type: Array, default: () => [] },
  createPoolPayload: { type: Object, required: true },
  canSubmitCreatePool: { type: Boolean, default: false },
  destroyConfirmDialogOpen: { type: Boolean, default: false },
  destroySubmitting: { type: Boolean, default: false },
  destroyDialogPhase: { type: String, default: "confirm" },
  destroyDialogSummary: { type: String, default: "" },
  destroyDialogError: { type: String, default: "" },
  destroyDialogResult: { type: Object, default: null },
  destroyTerminalLogLines: { type: Array, default: () => [] },
  removeConfirmDialogOpen: { type: Boolean, default: false },
  removeSubmitting: { type: Boolean, default: false },
  removeDialogPhase: { type: String, default: "confirm" },
  removeDialogSummary: { type: String, default: "" },
  removeDialogError: { type: String, default: "" },
  removeDialogResult: { type: Object, default: null },
  removeTerminalLogLines: { type: Array, default: () => [] },
});

const { t } = useI18n();
const emit = defineEmits([
  "update:confirmDialogOpen",
  "update:topologyConfirmDialogOpen",
  "update:createPoolConfirmDialogOpen",
  "update:destroyConfirmDialogOpen",
  "update:removeConfirmDialogOpen",
  "confirm-save",
  "confirm-topology",
  "confirm-create-pool",
  "confirm-destroy-pool",
  "confirm-remove-target",
]);
</script>

<template>
  <ConfirmDialog
    :model-value="confirmDialogOpen"
    :busy="submitting"
    :can-confirm="Boolean(changedItems.length)"
    :result-mode="dialogPhase === 'result'"
    :confirm-text="dialogPhase === 'submitting' ? t('pools.dialogs.updating') : t('pools.dialogs.confirmUpdate')"
    :title="t('pools.dialogs.confirmPoolPropertyChanges')"
    :description="selectedPool ? t('pools.dialogs.poolDescription', { name: selectedPool.name }) : ''"
    @update:modelValue="emit('update:confirmDialogOpen', $event)"
    @confirm="emit('confirm-save')"
  >
    <div v-if="dialogPhase === 'confirm'" class="dialog-section-list">
      <p class="subtle-text">{{ t("pools.dialogs.propertyChangesWillBeSent") }}</p>
      <CommandResultList :items="changedItems" empty-text="">
        <template #item="{ item }">
          <strong>{{ item.property }}</strong>
          <span class="subtle-text">{{ t("common.valueTransition", { from: item.oldValue || "-", to: item.newValue || "-" }) }}</span>
        </template>
      </CommandResultList>
    </div>
    <div v-else-if="dialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>{{ t("pools.dialogs.applyingPropertyChanges") }}</strong>
          <p class="subtle-text">{{ t("pools.dialogs.applyingPropertyChangesDescription") }}</p>
        </div>
      </div>
    </div>
    <div v-else class="dialog-section-list">
      <p v-if="dialogSummary" class="notice-text">{{ dialogSummary }}</p>
      <p v-if="dialogError" class="error-text">{{ dialogError }}</p>
      <section>
        <h4 class="dialog-mini-heading">{{ t("common.resultList") }}</h4>
        <CommandResultList :items="dialogResults">
          <template #item="{ item }">
            <div class="result-list-head">
              <strong>{{ item.property }}</strong>
              <span class="inline-status" :data-health="item.success ? 'ONLINE' : 'DEGRADED'">
                {{ item.success ? t("common.success") : t("common.failed") }}
              </span>
            </div>
            <p class="subtle-text">{{ t("common.valueTransition", { from: item.old_value || "-", to: item.new_value || "-" }) }}</p>
            <p class="subtle-text">{{ item.message }}</p>
          </template>
        </CommandResultList>
      </section>
      <section>
        <h4 class="dialog-mini-heading">{{ t("common.sshTerminalLog") }}</h4>
        <CommandLogPanel :entries="terminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>

  <ConfirmDialog
    :model-value="topologyConfirmDialogOpen"
    :busy="topologySubmitting"
    :can-confirm="Boolean(topologyPendingAdditions.length)"
    :result-mode="topologyDialogPhase === 'result'"
    :confirm-text="topologyDialogPhase === 'submitting' ? t('pools.dialogs.updating') : t('pools.dialogs.confirmUpdate')"
    :title="t('pools.dialogs.confirmPoolTopologyChanges')"
    :description="selectedPool ? t('pools.dialogs.poolDescription', { name: selectedPool.name }) : ''"
    @update:modelValue="emit('update:topologyConfirmDialogOpen', $event)"
    @confirm="emit('confirm-topology')"
  >
    <div v-if="topologyDialogPhase === 'confirm'" class="dialog-section-list">
      <p class="subtle-text">{{ t("pools.dialogs.topologyChangesWillBeSent") }}</p>
      <ul class="result-list">
        <li class="result-list-item">
          <strong>{{ t("common.force") }}</strong>
          <span class="subtle-text">{{ topologyForce ? "on" : "off" }}</span>
        </li>
        <li v-for="item in topologyConfirmSummary" :key="item.category + ':' + item.layout" class="result-list-item">
          <strong>{{ item.category }}</strong>
          <span class="subtle-text">{{ t("pools.layoutValue", { value: item.layout }) }}</span>
          <span class="subtle-text">{{ item.deviceLabels.join(', ') }}</span>
        </li>
      </ul>
    </div>
    <div v-else-if="topologyDialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>{{ t("pools.dialogs.applyingTopologyChanges") }}</strong>
          <p class="subtle-text">{{ t("pools.dialogs.applyingTopologyChangesDescription") }}</p>
        </div>
      </div>
    </div>
    <div v-else class="dialog-section-list">
      <p v-if="topologyDialogSummary" class="notice-text">{{ topologyDialogSummary }}</p>
      <p v-if="topologyDialogError" class="error-text">{{ topologyDialogError }}</p>
      <section>
        <h4 class="dialog-mini-heading">{{ t("common.resultList") }}</h4>
        <CommandResultList :items="topologyDialogResults">
          <template #item="{ item }">
            <div class="result-list-head">
              <strong>{{ item.category }}</strong>
              <span class="inline-status" :data-health="item.success ? 'ONLINE' : 'DEGRADED'">
                {{ item.success ? t("common.success") : t("common.failed") }}
              </span>
            </div>
            <p class="subtle-text">{{ t("pools.layoutValue", { value: item.layout }) }}</p>
            <p class="subtle-text">{{ item.devices.join(', ') }}</p>
            <p class="subtle-text">{{ item.message }}</p>
          </template>
        </CommandResultList>
      </section>
      <section>
        <h4 class="dialog-mini-heading">{{ t("common.sshTerminalLog") }}</h4>
        <CommandLogPanel :entries="topologyTerminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>

  <ConfirmDialog
    :model-value="createPoolConfirmDialogOpen"
    :busy="createPoolSubmitting"
    :can-confirm="canSubmitCreatePool"
    :result-mode="createPoolDialogPhase === 'result'"
    :confirm-text="createPoolDialogPhase === 'submitting' ? t('pools.dialogs.creating') : t('pools.dialogs.confirmCreate')"
    :title="t('pools.dialogs.confirmPoolCreation')"
    :description="createPoolPayload.name ? t('pools.dialogs.poolDescription', { name: createPoolPayload.name }) : t('pools.dialogs.newPool')"
    @update:modelValue="emit('update:createPoolConfirmDialogOpen', $event)"
    @confirm="emit('confirm-create-pool')"
  >
    <div v-if="createPoolDialogPhase === 'confirm'" class="dialog-section-list">
      <p class="subtle-text">{{ t("pools.dialogs.createConfirmationDescription") }}</p>
      <ul class="result-list">
        <li class="result-list-item">
          <strong>{{ t("pools.poolName") }}</strong>
          <span class="subtle-text">{{ createPoolPayload.name }}</span>
        </li>
        <li class="result-list-item">
          <strong>{{ t("common.force") }}</strong>
          <span class="subtle-text">{{ createPoolPayload.force ? "on" : "off" }}</span>
        </li>
        <li class="result-list-item">
          <strong>{{ t("pools.properties") }}</strong>
          <span class="subtle-text">{{ createPoolPayload.properties.length ? createPoolPayload.properties.map((item) => item.name + '=' + item.value).join(', ') : t('pools.noExtraProperties') }}</span>
        </li>
        <li class="result-list-item">
          <strong>{{ t("pools.rootDatasetProperties") }}</strong>
          <span class="subtle-text">{{ createPoolPayload.root_dataset_properties.length ? createPoolPayload.root_dataset_properties.map((item) => item.name + '=' + item.value).join(', ') : t('pools.defaultRootDatasetProperties') }}</span>
        </li>
        <li v-for="(vdev, index) in createPoolPayload.vdevs" :key="'create-confirm-' + index" class="result-list-item">
          <strong>{{ vdev.category }}</strong>
          <span class="subtle-text">{{ t("pools.layoutValue", { value: vdev.layout }) }}</span>
          <span class="subtle-text">{{ vdev.devices.join(', ') }}</span>
        </li>
      </ul>
    </div>
    <div v-else-if="createPoolDialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>{{ t("pools.dialogs.creatingPool") }}</strong>
          <p class="subtle-text">{{ t("pools.dialogs.creatingPoolDescription") }}</p>
        </div>
      </div>
    </div>
    <div v-else class="dialog-section-list">
      <p v-if="createPoolDialogSummary" class="notice-text">{{ createPoolDialogSummary }}</p>
      <p v-if="createPoolDialogError" class="error-text">{{ createPoolDialogError }}</p>
      <section>
        <h4 class="dialog-mini-heading">{{ t("common.result") }}</h4>
        <CommandResultList
          :items="createPoolDialogResult ? [{ ...createPoolDialogResult, label: createPoolDialogResult.pool, key: createPoolDialogResult.pool || 'pool' }] : []"
          :empty-text="t('common.noResult')"
        />
      </section>
      <section>
        <h4 class="dialog-mini-heading">{{ t("common.sshTerminalLog") }}</h4>
        <CommandLogPanel :entries="createPoolTerminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>

  <ConfirmDialog
    :model-value="destroyConfirmDialogOpen"
    :busy="destroySubmitting"
    :can-confirm="Boolean(selectedPool && selectedPool.name)"
    :result-mode="destroyDialogPhase === 'result'"
    :confirm-text="destroyDialogPhase === 'submitting' ? t('pools.dialogs.destroying') : t('pools.dialogs.confirmDestroy')"
    :title="t('pools.dialogs.confirmPoolDestroy')"
    :description="selectedPool ? t('pools.dialogs.poolDescription', { name: selectedPool.name }) : ''"
    @update:modelValue="emit('update:destroyConfirmDialogOpen', $event)"
    @confirm="emit('confirm-destroy-pool')"
  >
    <div v-if="destroyDialogPhase === 'confirm'" class="dialog-section-list">
      <p class="error-text">{{ t("pools.dialogs.destroyWarning") }}</p>
      <ul class="result-list">
        <li class="result-list-item">
          <strong>{{ t("pools.poolName") }}</strong>
          <span class="subtle-text">{{ selectedPool ? selectedPool.name : '-' }}</span>
        </li>
      </ul>
    </div>
    <div v-else-if="destroyDialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>{{ t("pools.dialogs.destroyingPool") }}</strong>
          <p class="subtle-text">{{ t("pools.dialogs.destroyingPoolDescription") }}</p>
        </div>
      </div>
    </div>
    <div v-else class="dialog-section-list">
      <p v-if="destroyDialogSummary" class="notice-text">{{ destroyDialogSummary }}</p>
      <p v-if="destroyDialogError" class="error-text">{{ destroyDialogError }}</p>
      <section>
        <h4 class="dialog-mini-heading">{{ t("common.result") }}</h4>
        <CommandResultList
          :items="destroyDialogResult ? [{ ...destroyDialogResult, label: destroyDialogResult.pool, key: destroyDialogResult.pool || 'pool' }] : []"
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
    :model-value="removeConfirmDialogOpen"
    :busy="removeSubmitting"
    :can-confirm="Boolean(selectedRemovalTarget && selectedRemovalTarget.commandTarget)"
    :result-mode="removeDialogPhase === 'result'"
    :confirm-text="removeDialogPhase === 'submitting' ? t('pools.dialogs.removing') : t('pools.dialogs.confirmRemove')"
    :title="t('pools.dialogs.confirmTopologyRemoval')"
    :description="selectedPool ? t('pools.dialogs.poolDescription', { name: selectedPool.name }) : ''"
    @update:modelValue="emit('update:removeConfirmDialogOpen', $event)"
    @confirm="emit('confirm-remove-target')"
  >
    <div v-if="removeDialogPhase === 'confirm'" class="dialog-section-list">
      <p class="subtle-text">{{ t("pools.dialogs.removeWarning") }}</p>
      <ul class="result-list" v-if="selectedRemovalTarget">
        <li class="result-list-item">
          <strong>{{ selectedRemovalTarget.displayLabel }}</strong>
          <span class="subtle-text">{{ selectedRemovalTarget.vdevClass }} / {{ selectedRemovalTarget.layout }}</span>
          <span class="subtle-text">{{ selectedRemovalTarget.targetType }}</span>
        </li>
      </ul>
    </div>
    <div v-else-if="removeDialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>{{ t("pools.dialogs.removingTarget") }}</strong>
          <p class="subtle-text">{{ t("pools.dialogs.removingTargetDescription") }}</p>
        </div>
      </div>
    </div>
    <div v-else class="dialog-section-list">
      <p v-if="removeDialogSummary" class="notice-text">{{ removeDialogSummary }}</p>
      <p v-if="removeDialogError" class="error-text">{{ removeDialogError }}</p>
      <section>
        <h4 class="dialog-mini-heading">{{ t("common.result") }}</h4>
        <CommandResultList
          :items="removeDialogResult ? [{ ...removeDialogResult, label: removeDialogResult.display_label, key: removeDialogResult.display_label || 'target' }] : []"
          :empty-text="t('common.noResult')"
        />
      </section>
      <section>
        <h4 class="dialog-mini-heading">{{ t("common.sshTerminalLog") }}</h4>
        <CommandLogPanel :entries="removeTerminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>
</template>
