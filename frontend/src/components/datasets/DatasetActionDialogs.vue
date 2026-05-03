<script setup>
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
    :confirm-text="dialogPhase === 'submitting' ? 'Applying...' : 'Confirm Apply'"
    title="Confirm Dataset Property Changes"
    :description="selectedDataset?.name || ''"
    @update:modelValue="emit('update:confirmDialogOpen', $event)"
    @confirm="emit('confirm-property')"
  >
    <div v-if="dialogPhase === 'confirm'" class="dialog-section-list">
      <p class="subtle-text">These dataset property changes will be sent to the host after confirmation.</p>
      <CommandResultList :items="changedItems" empty-text="">
        <template #item="{ item }">
          <strong>{{ item.property }}</strong>
          <span class="subtle-text">{{ item.old_value ?? "-" }} -> {{ item.value }}</span>
        </template>
      </CommandResultList>
    </div>

    <div v-else-if="dialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>Applying dataset property changes...</strong>
          <p class="subtle-text">Please wait while the backend updates the dataset and refreshes the latest state.</p>
        </div>
      </div>
    </div>

    <div v-else class="dialog-section-list">
      <p v-if="dialogSummary" class="notice-text">{{ dialogSummary }}</p>
      <p v-if="dialogError" class="error-text">{{ dialogError }}</p>

      <section>
        <h4 class="dialog-mini-heading">Result List</h4>
        <CommandResultList :items="dialogResults" />
      </section>

      <section>
        <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
        <CommandLogPanel :entries="terminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>

  <ConfirmDialog
    :model-value="destroyConfirmDialogOpen"
    :busy="destroySubmitting"
    :can-confirm="canDestroyDataset"
    :result-mode="destroyDialogPhase === 'result'"
    :confirm-text="destroyDialogPhase === 'submitting' ? 'Deleting...' : 'Confirm Delete'"
    title="Confirm Dataset Delete"
    :description="selectedDataset?.name || ''"
    @update:modelValue="emit('update:destroyConfirmDialogOpen', $event)"
    @confirm="emit('confirm-destroy')"
  >
    <div v-if="destroyDialogPhase === 'confirm'" class="dialog-section-list">
      <p class="error-text">This will run zfs destroy on the selected dataset and cannot be undone.</p>
      <ul class="result-list">
        <li class="result-list-item">
          <strong>Type</strong>
          <span class="subtle-text">{{ selectedDataset?.type || "-" }}</span>
        </li>
        <li class="result-list-item">
          <strong>Name</strong>
          <span class="subtle-text">{{ selectedDataset?.name || "-" }}</span>
        </li>
      </ul>
    </div>

    <div v-else-if="destroyDialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>Deleting dataset...</strong>
          <p class="subtle-text">Please wait while the backend runs zfs destroy and refreshes the latest state.</p>
        </div>
      </div>
    </div>

    <div v-else class="dialog-section-list">
      <p v-if="destroyDialogSummary" class="notice-text">{{ destroyDialogSummary }}</p>
      <p v-if="destroyDialogError" class="error-text">{{ destroyDialogError }}</p>

      <section>
        <h4 class="dialog-mini-heading">Result</h4>
        <CommandResultList
          :items="destroyDialogResult ? [{ ...destroyDialogResult, label: destroyDialogResult.dataset, key: destroyDialogResult.dataset || 'dataset' }] : []"
          empty-text="No result was returned."
        />
      </section>

      <section>
        <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
        <CommandLogPanel :entries="destroyTerminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>

  <ConfirmDialog
    :model-value="createConfirmDialogOpen"
    :busy="createSubmitting"
    :can-confirm="canSubmitCreate"
    :result-mode="createDialogPhase === 'result'"
    :confirm-text="createDialogPhase === 'submitting' ? 'Creating...' : 'Confirm Create'"
    title="Confirm Dataset Creation"
    :description="createPayload.parent ? createPayload.parent + '/' + createPayload.name : 'New child dataset'"
    @update:modelValue="emit('update:createConfirmDialogOpen', $event)"
    @confirm="emit('confirm-create')"
  >
    <div v-if="createDialogPhase === 'confirm'" class="dialog-section-list">
      <p class="subtle-text">This will run a zfs create command on the remote host.</p>
      <ul class="result-list">
        <li class="result-list-item">
          <strong>Type</strong>
          <span class="subtle-text">{{ createDraft.type === "volume" ? "zvol" : "dataset" }}</span>
        </li>
        <li class="result-list-item">
          <strong>Full Name</strong>
          <span class="subtle-text">{{ createPayload.parent }}/{{ createPayload.name }}</span>
        </li>
        <li class="result-list-item">
          <strong>Properties</strong>
          <span class="subtle-text">{{ createPayload.properties.length ? createPayload.properties.map((item) => item.name + '=' + item.value).join(', ') : 'Default properties only' }}</span>
        </li>
      </ul>
    </div>

    <div v-else-if="createDialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>Creating {{ createDraft.type === "volume" ? "zvol" : "dataset" }}...</strong>
          <p class="subtle-text">Please wait while the backend runs zfs create and refreshes the latest state.</p>
        </div>
      </div>
    </div>

    <div v-else class="dialog-section-list">
      <p v-if="createDialogSummary" class="notice-text">{{ createDialogSummary }}</p>
      <p v-if="createDialogError" class="error-text">{{ createDialogError }}</p>

      <section>
        <h4 class="dialog-mini-heading">Result</h4>
        <CommandResultList
          :items="createDialogResult ? [{ ...createDialogResult, label: createDialogResult.dataset, key: createDialogResult.dataset || 'dataset' }] : []"
          empty-text="No result was returned."
        />
      </section>

      <section>
        <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
        <CommandLogPanel :entries="createTerminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>
</template>
