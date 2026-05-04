<script setup>
import { ref } from "vue";
import { useI18n } from "vue-i18n";

import { useAppState } from "../../store/state.js";

const { t } = useI18n();
const { login } = useAppState();

const password = ref("");
const loading = ref(false);
const errorMessage = ref("");

async function submit() {
  loading.value = true;
  errorMessage.value = "";
  try {
    await login(password.value);
    password.value = "";
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : String(error);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="login-shell">
    <section class="login-card">
      <p class="eyebrow">{{ t("login.eyebrow") }}</p>
      <h1>{{ t("login.title") }}</h1>
      <p class="topbar-description">{{ t("login.description") }}</p>

      <label class="form-field">
        <span>{{ t("login.password") }}</span>
        <input
          v-model="password"
          type="password"
          class="property-field"
          :placeholder="t('login.passwordPlaceholder')"
          @keyup.enter="submit"
        />
      </label>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>

      <button type="button" class="primary-button login-submit" :disabled="loading || !password" @click="submit">
        {{ loading ? t("login.loggingIn") : t("login.submit") }}
      </button>
    </section>
  </main>
</template>
