import { createI18n } from "vue-i18n";

import { messages } from "./messages.js";

const LOCALE_STORAGE_KEY = "zfs-manager-locale";
const supportedLocales = ["en-US", "zh-CN"];
const fallbackLocale = "en-US";

function normalizeLocale(locale) {
  const value = String(locale || "").trim();
  if (supportedLocales.includes(value)) {
    return value;
  }
  if (value.toLowerCase().startsWith("zh")) {
    return "zh-CN";
  }
  if (value.toLowerCase().startsWith("en")) {
    return "en-US";
  }
  return null;
}

function detectBrowserLocale() {
  if (typeof navigator === "undefined") {
    return fallbackLocale;
  }
  return normalizeLocale(navigator.language) || fallbackLocale;
}

function readStoredLocale() {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return normalizeLocale(window.localStorage.getItem(LOCALE_STORAGE_KEY));
  } catch {
    return null;
  }
}

function writeStoredLocale(locale) {
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch {
    // Ignore storage failures and keep the current in-memory locale.
  }
}

function resolveInitialLocale() {
  // Prefer an explicit user choice, then fall back to the browser locale for first-time visitors.
  return readStoredLocale() || detectBrowserLocale() || fallbackLocale;
}

export const i18n = createI18n({
  legacy: false,
  locale: resolveInitialLocale(),
  fallbackLocale,
  messages,
});

export function setLocale(locale) {
  const nextLocale = normalizeLocale(locale) || fallbackLocale;
  i18n.global.locale.value = nextLocale;
  // Keep refreshes and fresh tabs aligned with the most recent user selection.
  writeStoredLocale(nextLocale);
}

export { fallbackLocale, supportedLocales };
