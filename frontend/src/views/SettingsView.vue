<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useI18n } from "vue-i18n";

import { useAppState } from "../store/state.js";

const props = defineProps({
  state: { type: Object, required: true },
});

const { t } = useI18n();
const { getSettings, saveSettings, testSshConnection } = useAppState();

const loading = ref(true);
const saving = ref(false);
const testing = ref(false);
const errorMessage = ref("");
const successMessage = ref("");
const testMessage = ref("");
const testErrorMessage = ref("");
const configPath = ref("");
const snapshot = computed(() => props.state.snapshot.value);
const sourceStatus = computed(() => snapshot.value?.meta?.source_status || "unknown");

const form = reactive(buildEmptyForm());

function buildEmptyForm() {
  return {
    poller: {
      mode: "fixture",
      fallback_to_fixture: true,
      tick_seconds: 1,
      pools_interval_seconds: 5,
      datasets_interval_seconds: 15,
      disks_interval_seconds: 60,
      properties_interval_seconds: 120,
      idle_tick_seconds: 30,
      idle_pools_interval_seconds: 60,
      idle_datasets_interval_seconds: 300,
      idle_disks_interval_seconds: 600,
      idle_properties_interval_seconds: 1200,
    },
    ssh: {
      host: "",
      username: "",
      port: 22,
      password: "",
      key_files_text: "",
      known_hosts: "",
      connect_timeout: 10,
      command_timeout: 30,
      keepalive_interval: 30,
      keepalive_count_max: 3,
    },
    auth: {
      enabled: false,
      password: "",
    },
  };
}

function applyConfig(config) {
  form.poller.mode = config?.poller?.mode || "fixture";
  form.poller.fallback_to_fixture = Boolean(config?.poller?.fallback_to_fixture);
  form.poller.tick_seconds = Number(config?.poller?.tick_seconds ?? 1);
  form.poller.pools_interval_seconds = Number(config?.poller?.pools_interval_seconds ?? 5);
  form.poller.datasets_interval_seconds = Number(config?.poller?.datasets_interval_seconds ?? 15);
  form.poller.disks_interval_seconds = Number(config?.poller?.disks_interval_seconds ?? 60);
  form.poller.properties_interval_seconds = Number(config?.poller?.properties_interval_seconds ?? 120);
  form.poller.idle_tick_seconds = Number(config?.poller?.idle_tick_seconds ?? 30);
  form.poller.idle_pools_interval_seconds = Number(config?.poller?.idle_pools_interval_seconds ?? 60);
  form.poller.idle_datasets_interval_seconds = Number(config?.poller?.idle_datasets_interval_seconds ?? 300);
  form.poller.idle_disks_interval_seconds = Number(config?.poller?.idle_disks_interval_seconds ?? 600);
  form.poller.idle_properties_interval_seconds = Number(config?.poller?.idle_properties_interval_seconds ?? 1200);

  form.ssh.host = config?.ssh?.host || "";
  form.ssh.username = config?.ssh?.username || "";
  form.ssh.port = Number(config?.ssh?.port ?? 22);
  form.ssh.password = config?.ssh?.password || "";
  form.ssh.key_files_text = Array.isArray(config?.ssh?.key_files) ? config.ssh.key_files.join("\n") : "";
  form.ssh.known_hosts = config?.ssh?.known_hosts || "";
  form.ssh.connect_timeout = Number(config?.ssh?.connect_timeout ?? 10);
  form.ssh.command_timeout = Number(config?.ssh?.command_timeout ?? 30);
  form.ssh.keepalive_interval = Number(config?.ssh?.keepalive_interval ?? 30);
  form.ssh.keepalive_count_max = Number(config?.ssh?.keepalive_count_max ?? 3);

  form.auth.enabled = Boolean(config?.auth?.enabled);
  form.auth.password = config?.auth?.password || "";
}

function buildPayload() {
  return {
    poller: {
      mode: form.poller.mode,
      fallback_to_fixture: Boolean(form.poller.fallback_to_fixture),
      tick_seconds: Number(form.poller.tick_seconds),
      pools_interval_seconds: Number(form.poller.pools_interval_seconds),
      datasets_interval_seconds: Number(form.poller.datasets_interval_seconds),
      disks_interval_seconds: Number(form.poller.disks_interval_seconds),
      properties_interval_seconds: Number(form.poller.properties_interval_seconds),
      idle_tick_seconds: Number(form.poller.idle_tick_seconds),
      idle_pools_interval_seconds: Number(form.poller.idle_pools_interval_seconds),
      idle_datasets_interval_seconds: Number(form.poller.idle_datasets_interval_seconds),
      idle_disks_interval_seconds: Number(form.poller.idle_disks_interval_seconds),
      idle_properties_interval_seconds: Number(form.poller.idle_properties_interval_seconds),
    },
    ssh: {
      host: form.ssh.host.trim(),
      username: form.ssh.username.trim(),
      port: Number(form.ssh.port),
      password: form.ssh.password || null,
      key_files: form.ssh.key_files_text
        .split(/\r?\n/)
        .map((item) => item.trim())
        .filter(Boolean),
      known_hosts: form.ssh.known_hosts.trim() || null,
      connect_timeout: Number(form.ssh.connect_timeout),
      command_timeout: Number(form.ssh.command_timeout),
      keepalive_interval: Number(form.ssh.keepalive_interval),
      keepalive_count_max: Number(form.ssh.keepalive_count_max),
    },
    auth: {
      enabled: Boolean(form.auth.enabled),
      password: form.auth.password || null,
    },
  };
}

function buildSshTestPayload() {
  return {
    ssh: buildPayload().ssh,
  };
}

async function loadSettings() {
  loading.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  testMessage.value = "";
  testErrorMessage.value = "";
  try {
    const config = await getSettings();
    applyConfig(config);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    loading.value = false;
  }
}

async function submitSettings() {
  saving.value = true;
  errorMessage.value = "";
  successMessage.value = "";
  try {
    const response = await saveSettings(buildPayload());
    applyConfig(response.config);
    configPath.value = response.config_path || "";
    successMessage.value = response.message || t("settings.saveSuccess");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    saving.value = false;
  }
}

async function submitSshTest() {
  testing.value = true;
  testMessage.value = "";
  testErrorMessage.value = "";
  try {
    const response = await testSshConnection(buildSshTestPayload());
    testMessage.value = response.message || t("settings.testSuccess");
  } catch (error) {
    testErrorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    testing.value = false;
  }
}

onMounted(() => {
  loadSettings();
});
</script>

<template>
  <section class="view-grid">
    <article class="surface-panel">
      <div class="section-header">
        <div>
          <h3>{{ t("settings.title") }}</h3>
          <p>{{ t("settings.description") }}</p>
        </div>
        <div class="inline-button-row">
          <button type="button" class="ghost-button" :disabled="loading || saving || testing" @click="submitSshTest">
            {{ testing ? t("settings.testing") : t("settings.testConnection") }}
          </button>
          <button type="button" class="ghost-button" :disabled="loading || saving" @click="loadSettings">
            {{ t("settings.reload") }}
          </button>
          <button type="button" class="primary-button" :disabled="loading || saving" @click="submitSettings">
            {{ saving ? t("common.saving") : t("common.save") }}
          </button>
        </div>
      </div>

      <p class="notice-text" v-if="configPath">
        {{ t("settings.configPath", { path: configPath }) }}
      </p>
      <p class="notice-text" v-else>
        {{ t("settings.activeSource", { status: sourceStatus }) }}
      </p>
      <p v-if="successMessage" class="notice-text">{{ successMessage }}</p>
      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-if="testMessage" class="notice-text">{{ testMessage }}</p>
      <p v-if="testErrorMessage" class="error-text">{{ testErrorMessage }}</p>

      <div v-if="loading" class="empty-state">
        <strong>{{ t("settings.loadingTitle") }}</strong>
        <span>{{ t("settings.loadingDescription") }}</span>
      </div>

      <div v-else class="settings-grid">
        <section class="surface-panel settings-subpanel">
          <div class="section-header">
            <div>
              <h3>{{ t("settings.poller.title") }}</h3>
              <p>{{ t("settings.poller.description") }}</p>
            </div>
          </div>

          <div class="settings-form-grid">
            <label class="form-field">
              <span>{{ t("settings.fields.mode") }}</span>
              <select v-model="form.poller.mode" class="property-field">
                <option value="fixture">fixture</option>
                <option value="ssh">ssh</option>
              </select>
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.tickSeconds") }}</span>
              <input v-model.number="form.poller.tick_seconds" type="number" min="1" class="property-field" />
              <small class="property-meta">{{ t("settings.poller.tickHint") }}</small>
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.poolsIntervalSeconds") }}</span>
              <input v-model.number="form.poller.pools_interval_seconds" type="number" min="1" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.datasetsIntervalSeconds") }}</span>
              <input v-model.number="form.poller.datasets_interval_seconds" type="number" min="1" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.disksIntervalSeconds") }}</span>
              <input v-model.number="form.poller.disks_interval_seconds" type="number" min="1" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.propertiesIntervalSeconds") }}</span>
              <input v-model.number="form.poller.properties_interval_seconds" type="number" min="1" class="property-field" />
            </label>

            <div class="form-field form-field-checkbox">
              <span>{{ t("settings.fields.fallbackToFixture") }}</span>
              <label class="inline-checkbox">
                <input v-model="form.poller.fallback_to_fixture" type="checkbox" />
                <span>{{ t("settings.fallbackHelp") }}</span>
              </label>
            </div>
          </div>

          <p class="property-meta" style="margin-bottom: 12px;">{{ t("settings.poller.modeSwitchHint") }}</p>

          <div class="settings-subsection-header">
            <h4>{{ t("settings.poller.idleTitle") }}</h4>
            <p>{{ t("settings.poller.idleDescription") }}</p>
          </div>

          <div class="settings-form-grid">
            <label class="form-field">
              <span>{{ t("settings.fields.idleTickSeconds") }}</span>
              <input v-model.number="form.poller.idle_tick_seconds" type="number" min="1" class="property-field" />
              <small class="property-meta">{{ t("settings.poller.tickHint") }}</small>
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.idlePoolsIntervalSeconds") }}</span>
              <input v-model.number="form.poller.idle_pools_interval_seconds" type="number" min="1" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.idleDatasetsIntervalSeconds") }}</span>
              <input v-model.number="form.poller.idle_datasets_interval_seconds" type="number" min="1" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.idleDisksIntervalSeconds") }}</span>
              <input v-model.number="form.poller.idle_disks_interval_seconds" type="number" min="1" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.idlePropertiesIntervalSeconds") }}</span>
              <input v-model.number="form.poller.idle_properties_interval_seconds" type="number" min="1" class="property-field" />
            </label>
          </div>
        </section>

        <section class="surface-panel settings-subpanel">
          <div class="section-header">
            <div>
              <h3>{{ t("settings.ssh.title") }}</h3>
              <p>{{ t("settings.ssh.description") }}</p>
            </div>
          </div>

          <div class="settings-form-grid">
            <label class="form-field">
              <span>{{ t("settings.fields.host") }}</span>
              <input v-model="form.ssh.host" type="text" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.username") }}</span>
              <input v-model="form.ssh.username" type="text" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.port") }}</span>
              <input v-model.number="form.ssh.port" type="number" min="1" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.password") }}</span>
              <input v-model="form.ssh.password" type="password" class="property-field" />
            </label>

            <label class="form-field settings-form-span-2">
              <span>{{ t("settings.fields.keyFiles") }}</span>
              <textarea v-model="form.ssh.key_files_text" rows="4" class="property-field settings-textarea"></textarea>
              <small class="property-meta">{{ t("settings.keyFilesHelp") }}</small>
            </label>

            <label class="form-field settings-form-span-2">
              <span>{{ t("settings.fields.knownHosts") }}</span>
              <input v-model="form.ssh.known_hosts" type="text" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.connectTimeout") }}</span>
              <input v-model.number="form.ssh.connect_timeout" type="number" min="1" step="0.5" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.commandTimeout") }}</span>
              <input v-model.number="form.ssh.command_timeout" type="number" min="1" step="0.5" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.keepaliveInterval") }}</span>
              <input v-model.number="form.ssh.keepalive_interval" type="number" min="1" step="0.5" class="property-field" />
            </label>

            <label class="form-field">
              <span>{{ t("settings.fields.keepaliveCountMax") }}</span>
              <input v-model.number="form.ssh.keepalive_count_max" type="number" min="1" class="property-field" />
            </label>
          </div>
        </section>

        <section class="surface-panel settings-subpanel">
          <div class="section-header">
            <div>
              <h3>{{ t("settings.auth.title") }}</h3>
              <p>{{ t("settings.auth.description") }}</p>
            </div>
          </div>

          <div class="settings-form-grid">
            <div class="form-field form-field-checkbox settings-form-span-2">
              <span>{{ t("settings.fields.passwordLoginEnabled") }}</span>
              <label class="inline-checkbox">
                <input v-model="form.auth.enabled" type="checkbox" />
                <span>{{ t("settings.auth.enableHelp") }}</span>
              </label>
            </div>

            <label class="form-field settings-form-span-2">
              <span>{{ t("settings.fields.loginPassword") }}</span>
              <input
                v-model="form.auth.password"
                type="password"
                class="property-field"
                :placeholder="t('settings.auth.passwordPlaceholder')"
              />
              <small class="property-meta">{{ t("settings.auth.passwordHelp") }}</small>
            </label>
          </div>
        </section>
      </div>
    </article>
  </section>
</template>
