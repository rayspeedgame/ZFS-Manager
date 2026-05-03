<script setup>
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
    :confirm-text="dialogPhase === 'submitting' ? 'Updating...' : 'Confirm Update'"
    title="Confirm Pool Property Changes"
    :description="selectedPool ? 'Pool: ' + selectedPool.name : ''"
    @update:modelValue="emit('update:confirmDialogOpen', $event)"
    @confirm="emit('confirm-save')"
  >
    <div v-if="dialogPhase === 'confirm'" class="dialog-section-list">
      <p class="subtle-text">These property changes will be sent to the host after confirmation.</p>
      <CommandResultList :items="changedItems" empty-text="">
        <template #item="{ item }">
          <strong>{{ item.property }}</strong>
          <span class="subtle-text">{{ item.oldValue || "-" }} -> {{ item.newValue || "-" }}</span>
        </template>
      </CommandResultList>
    </div>
    <div v-else-if="dialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>Applying property changes...</strong>
          <p class="subtle-text">Please wait while the backend sends SSH commands and refreshes the latest state.</p>
        </div>
      </div>
    </div>
    <div v-else class="dialog-section-list">
      <p v-if="dialogSummary" class="notice-text">{{ dialogSummary }}</p>
      <p v-if="dialogError" class="error-text">{{ dialogError }}</p>
      <section>
        <h4 class="dialog-mini-heading">Result List</h4>
        <CommandResultList :items="dialogResults">
          <template #item="{ item }">
            <div class="result-list-head">
              <strong>{{ item.property }}</strong>
              <span class="inline-status" :data-health="item.success ? 'ONLINE' : 'DEGRADED'">
                {{ item.success ? "Success" : "Failed" }}
              </span>
            </div>
            <p class="subtle-text">{{ item.old_value || "-" }} -> {{ item.new_value || "-" }}</p>
            <p class="subtle-text">{{ item.message }}</p>
          </template>
        </CommandResultList>
      </section>
      <section>
        <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
        <CommandLogPanel :entries="terminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>

  <ConfirmDialog
    :model-value="topologyConfirmDialogOpen"
    :busy="topologySubmitting"
    :can-confirm="Boolean(topologyPendingAdditions.length)"
    :result-mode="topologyDialogPhase === 'result'"
    :confirm-text="topologyDialogPhase === 'submitting' ? 'Updating...' : 'Confirm Update'"
    title="Confirm Pool Topology Changes"
    :description="selectedPool ? 'Pool: ' + selectedPool.name : ''"
    @update:modelValue="emit('update:topologyConfirmDialogOpen', $event)"
    @confirm="emit('confirm-topology')"
  >
    <div v-if="topologyDialogPhase === 'confirm'" class="dialog-section-list">
      <p class="subtle-text">These topology changes will be sent to the host after confirmation.</p>
      <ul class="result-list">
        <li class="result-list-item">
          <strong>Force</strong>
          <span class="subtle-text">{{ topologyForce ? "on" : "off" }}</span>
        </li>
        <li v-for="item in topologyConfirmSummary" :key="item.category + ':' + item.layout" class="result-list-item">
          <strong>{{ item.category }}</strong>
          <span class="subtle-text">Layout: {{ item.layout }}</span>
          <span class="subtle-text">{{ item.deviceLabels.join(', ') }}</span>
        </li>
      </ul>
    </div>
    <div v-else-if="topologyDialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>Applying topology changes...</strong>
          <p class="subtle-text">Please wait while the backend updates the pool and refreshes the latest state.</p>
        </div>
      </div>
    </div>
    <div v-else class="dialog-section-list">
      <p v-if="topologyDialogSummary" class="notice-text">{{ topologyDialogSummary }}</p>
      <p v-if="topologyDialogError" class="error-text">{{ topologyDialogError }}</p>
      <section>
        <h4 class="dialog-mini-heading">Result List</h4>
        <CommandResultList :items="topologyDialogResults">
          <template #item="{ item }">
            <div class="result-list-head">
              <strong>{{ item.category }}</strong>
              <span class="inline-status" :data-health="item.success ? 'ONLINE' : 'DEGRADED'">
                {{ item.success ? "Success" : "Failed" }}
              </span>
            </div>
            <p class="subtle-text">Layout: {{ item.layout }}</p>
            <p class="subtle-text">{{ item.devices.join(', ') }}</p>
            <p class="subtle-text">{{ item.message }}</p>
          </template>
        </CommandResultList>
      </section>
      <section>
        <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
        <CommandLogPanel :entries="topologyTerminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>

  <ConfirmDialog
    :model-value="createPoolConfirmDialogOpen"
    :busy="createPoolSubmitting"
    :can-confirm="canSubmitCreatePool"
    :result-mode="createPoolDialogPhase === 'result'"
    :confirm-text="createPoolDialogPhase === 'submitting' ? 'Creating...' : 'Confirm Create'"
    title="Confirm Pool Creation"
    :description="createPoolPayload.name ? 'Pool: ' + createPoolPayload.name : 'New pool'"
    @update:modelValue="emit('update:createPoolConfirmDialogOpen', $event)"
    @confirm="emit('confirm-create-pool')"
  >
    <div v-if="createPoolDialogPhase === 'confirm'" class="dialog-section-list">
      <p class="subtle-text">This will submit one atomic zpool create command with all selected properties and vdevs.</p>
      <ul class="result-list">
        <li class="result-list-item">
          <strong>Pool Name</strong>
          <span class="subtle-text">{{ createPoolPayload.name }}</span>
        </li>
        <li class="result-list-item">
          <strong>Force</strong>
          <span class="subtle-text">{{ createPoolPayload.force ? "on" : "off" }}</span>
        </li>
        <li class="result-list-item">
          <strong>Properties</strong>
          <span class="subtle-text">{{ createPoolPayload.properties.length ? createPoolPayload.properties.map((item) => item.name + '=' + item.value).join(', ') : 'No extra properties' }}</span>
        </li>
        <li class="result-list-item">
          <strong>Root Dataset Properties</strong>
          <span class="subtle-text">{{ createPoolPayload.root_dataset_properties.length ? createPoolPayload.root_dataset_properties.map((item) => item.name + '=' + item.value).join(', ') : 'Default root dataset properties' }}</span>
        </li>
        <li v-for="(vdev, index) in createPoolPayload.vdevs" :key="'create-confirm-' + index" class="result-list-item">
          <strong>{{ vdev.category }}</strong>
          <span class="subtle-text">Layout: {{ vdev.layout }}</span>
          <span class="subtle-text">{{ vdev.devices.join(', ') }}</span>
        </li>
      </ul>
    </div>
    <div v-else-if="createPoolDialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>Creating pool...</strong>
          <p class="subtle-text">Please wait while the backend runs one zpool create command and refreshes the latest state.</p>
        </div>
      </div>
    </div>
    <div v-else class="dialog-section-list">
      <p v-if="createPoolDialogSummary" class="notice-text">{{ createPoolDialogSummary }}</p>
      <p v-if="createPoolDialogError" class="error-text">{{ createPoolDialogError }}</p>
      <section>
        <h4 class="dialog-mini-heading">Result</h4>
        <CommandResultList
          :items="createPoolDialogResult ? [{ ...createPoolDialogResult, label: createPoolDialogResult.pool, key: createPoolDialogResult.pool || 'pool' }] : []"
          empty-text="No result was returned."
        />
      </section>
      <section>
        <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
        <CommandLogPanel :entries="createPoolTerminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>

  <ConfirmDialog
    :model-value="destroyConfirmDialogOpen"
    :busy="destroySubmitting"
    :can-confirm="Boolean(selectedPool && selectedPool.name)"
    :result-mode="destroyDialogPhase === 'result'"
    :confirm-text="destroyDialogPhase === 'submitting' ? 'Destroying...' : 'Confirm Destroy'"
    title="Confirm Pool Destroy"
    :description="selectedPool ? 'Pool: ' + selectedPool.name : ''"
    @update:modelValue="emit('update:destroyConfirmDialogOpen', $event)"
    @confirm="emit('confirm-destroy-pool')"
  >
    <div v-if="destroyDialogPhase === 'confirm'" class="dialog-section-list">
      <p class="error-text">This will run zpool destroy on the selected pool.</p>
      <ul class="result-list">
        <li class="result-list-item">
          <strong>Pool</strong>
          <span class="subtle-text">{{ selectedPool ? selectedPool.name : '-' }}</span>
        </li>
      </ul>
    </div>
    <div v-else-if="destroyDialogPhase === 'submitting'" class="dialog-section-list">
      <div class="progress-shell">
        <div class="progress-spinner"></div>
        <div>
          <strong>Destroying pool...</strong>
          <p class="subtle-text">Please wait while the backend runs zpool destroy and refreshes the latest state.</p>
        </div>
      </div>
    </div>
    <div v-else class="dialog-section-list">
      <p v-if="destroyDialogSummary" class="notice-text">{{ destroyDialogSummary }}</p>
      <p v-if="destroyDialogError" class="error-text">{{ destroyDialogError }}</p>
      <section>
        <h4 class="dialog-mini-heading">Result</h4>
        <CommandResultList
          :items="destroyDialogResult ? [{ ...destroyDialogResult, label: destroyDialogResult.pool, key: destroyDialogResult.pool || 'pool' }] : []"
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
    :model-value="removeConfirmDialogOpen"
    :busy="removeSubmitting"
    :can-confirm="Boolean(selectedRemovalTarget && selectedRemovalTarget.commandTarget)"
    :result-mode="removeDialogPhase === 'result'"
    :confirm-text="removeDialogPhase === 'submitting' ? 'Removing...' : 'Confirm Remove'"
    title="Confirm Topology Removal"
    :description="selectedPool ? 'Pool: ' + selectedPool.name : ''"
    @update:modelValue="emit('update:removeConfirmDialogOpen', $event)"
    @confirm="emit('confirm-remove-target')"
  >
    <div v-if="removeDialogPhase === 'confirm'" class="dialog-section-list">
      <p class="subtle-text">This will remove the selected topology target from the pool.</p>
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
          <strong>Removing topology target...</strong>
          <p class="subtle-text">Please wait while the backend runs zpool remove and refreshes the latest state.</p>
        </div>
      </div>
    </div>
    <div v-else class="dialog-section-list">
      <p v-if="removeDialogSummary" class="notice-text">{{ removeDialogSummary }}</p>
      <p v-if="removeDialogError" class="error-text">{{ removeDialogError }}</p>
      <section>
        <h4 class="dialog-mini-heading">Result</h4>
        <CommandResultList
          :items="removeDialogResult ? [{ ...removeDialogResult, label: removeDialogResult.display_label, key: removeDialogResult.display_label || 'target' }] : []"
          empty-text="No result was returned."
        />
      </section>
      <section>
        <h4 class="dialog-mini-heading">SSH Terminal Log</h4>
        <CommandLogPanel :entries="removeTerminalLogLines" />
      </section>
    </div>
  </ConfirmDialog>
</template>
