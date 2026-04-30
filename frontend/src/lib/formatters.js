export function formatBytes(value) {
  if (value === null || value === undefined || value === "-") {
    return "-";
  }

  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value);
  }

  const units = ["B", "KB", "MB", "GB", "TB", "PB"];
  let size = numeric;
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(size >= 100 || index === 0 ? 0 : 1)} ${units[index]}`;
}

export function formatPercent(value) {
  if (value === null || value === undefined || value === "-") {
    return "-";
  }
  return `${value}%`;
}

export function formatDateTime(value) {
  if (!value) {
    return "Not available";
  }
  return new Date(value).toLocaleString();
}

export function formatSourceLabel(message, snapshotStatus) {
  const lowered = (message || "").toLowerCase();
  if (snapshotStatus === "error") {
    return "Unavailable";
  }
  if (lowered.includes("serving fixture data instead")) {
    return "Fixture Fallback";
  }
  if (lowered.includes("fixture mode")) {
    return "Fixture";
  }
  if (lowered.includes("live ssh data")) {
    return "Live SSH";
  }
  return "Unknown";
}

export function flattenDatasetRows(datasets = []) {
  return datasets.map((dataset) => ({
    ...dataset,
    depth: Math.max(0, String(dataset.name || "").split("/").length - 1),
  }));
}

export function getPropertySourceSummary(properties = {}) {
  const sources = Object.values(properties).map((item) => item?.source).filter(Boolean);
  if (!sources.length) {
    return "Unknown";
  }
  const inheritedOnly = sources.every((source) => String(source).startsWith("inherited from"));
  const localOnly = sources.every((source) => source === "local");
  if (localOnly) {
    return "Local";
  }
  if (inheritedOnly) {
    return "Inherited";
  }
  return "Mixed";
}
