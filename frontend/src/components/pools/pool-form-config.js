import { BOOLEAN_OPTIONS, CACHE_OPTIONS, SYNC_OPTIONS } from "../common/property-options.js";

const FAILMODE_OPTIONS = [
  { label: "wait", value: "wait" },
  { label: "continue", value: "continue" },
  { label: "panic", value: "panic" },
];

const CANMOUNT_OPTIONS = [
  { label: "on", value: "on" },
  { label: "off", value: "off" },
  { label: "noauto", value: "noauto" },
];

const LOGBIAS_OPTIONS = [
  { label: "latency", value: "latency" },
  { label: "throughput", value: "throughput" },
];

const SNAPDIR_OPTIONS = [
  { label: "hidden", value: "hidden" },
  { label: "visible", value: "visible" },
];

const ACLTYPE_OPTIONS = [
  { label: "off", value: "off" },
  { label: "posix", value: "posix" },
  { label: "nfsv4", value: "nfsv4" },
];

const ACLINHERIT_OPTIONS = [
  { label: "discard", value: "discard" },
  { label: "noallow", value: "noallow" },
  { label: "restricted", value: "restricted" },
  { label: "passthrough", value: "passthrough" },
  { label: "passthrough-x", value: "passthrough-x" },
];

const ACLMODE_OPTIONS = [
  { label: "discard", value: "discard" },
  { label: "groupmask", value: "groupmask" },
  { label: "passthrough", value: "passthrough" },
  { label: "restricted", value: "restricted" },
];

const CASESENSITIVITY_OPTIONS = [
  { label: "sensitive", value: "sensitive" },
  { label: "insensitive", value: "insensitive" },
  { label: "mixed", value: "mixed" },
];

const NORMALIZATION_OPTIONS = [
  { label: "none", value: "none" },
  { label: "formC", value: "formC" },
  { label: "formD", value: "formD" },
  { label: "formKC", value: "formKC" },
  { label: "formKD", value: "formKD" },
];

const DEDUP_OPTIONS = [
  { label: "off", value: "off" },
  { label: "on", value: "on" },
  { label: "verify", value: "verify" },
];

const CHECKSUM_OPTIONS = [
  { label: "on", value: "on" },
  { label: "off", value: "off" },
  { label: "fletcher2", value: "fletcher2" },
  { label: "fletcher4", value: "fletcher4" },
  { label: "sha256", value: "sha256" },
  { label: "sha512", value: "sha512" },
  { label: "skein", value: "skein" },
  { label: "edonr", value: "edonr" },
];

const COPIES_OPTIONS = [
  { label: "1", value: "1" },
  { label: "2", value: "2" },
  { label: "3", value: "3" },
];

const DNODESIZE_OPTIONS = [
  { label: "legacy", value: "legacy" },
  { label: "auto", value: "auto" },
  { label: "1K", value: "1k" },
  { label: "2K", value: "2k" },
  { label: "4K", value: "4k" },
  { label: "8K", value: "8k" },
  { label: "16K", value: "16k" },
];

const REDUNDANT_METADATA_OPTIONS = [
  { label: "all", value: "all" },
  { label: "most", value: "most" },
  { label: "some", value: "some" },
  { label: "none", value: "none" },
];

const XATTR_OPTIONS = [
  { label: "on", value: "on" },
  { label: "off", value: "off" },
  { label: "dir", value: "dir" },
  { label: "sa", value: "sa" },
];

export const EDITABLE_POOL_PROPERTIES = new Set([
  "autoexpand",
  "autoreplace",
  "autotrim",
  "bootfs",
  "cachefile",
  "comment",
  "delegation",
  "failmode",
  "listsnapshots",
  "multihost",
]);

export const COMMON_READONLY_POOL_PROPERTIES = new Set([
  "ashift",
  "altroot",
  "bootsize",
  "checkpoint",
  "expandsize",
  "guid",
  "readonly",
  "version",
]);

export const CREATE_POOL_PROPERTY_OPTIONS = {
  ashift: {
    labelKey: "properties.names.ashift",
    type: "select",
    options: [
      { label: "12", value: "12" },
      { label: "13", value: "13" },
    ],
  },
  autoexpand: { labelKey: "properties.names.autoexpand", type: "select", options: BOOLEAN_OPTIONS },
  autoreplace: { labelKey: "properties.names.autoreplace", type: "select", options: BOOLEAN_OPTIONS },
  autotrim: { labelKey: "properties.names.autotrim", type: "select", options: BOOLEAN_OPTIONS },
  failmode: { labelKey: "properties.names.failmode", type: "select", options: FAILMODE_OPTIONS },
  comment: { labelKey: "properties.names.comment", type: "text", placeholderKey: "properties.placeholders.optionalPoolComment" },
};

export const CREATE_DATA_LAYOUT_OPTIONS = [
  { labelKey: "pools.layouts.stripe", value: "stripe" },
  { labelKey: "pools.layouts.mirror", value: "mirror" },
  { labelKey: "pools.layouts.raidz", value: "raidz" },
  { labelKey: "pools.layouts.raidz2", value: "raidz2" },
  { labelKey: "pools.layouts.raidz3", value: "raidz3" },
];

export const TOPOLOGY_CATEGORY_OPTIONS = [
  { labelKey: "pools.categories.log", value: "log" },
  { labelKey: "pools.categories.cache", value: "cache" },
  { labelKey: "pools.categories.special", value: "special" },
  { labelKey: "pools.categories.dedup", value: "dedup" },
  { labelKey: "pools.categories.spare", value: "spare" },
];

export const TOPOLOGY_LAYOUT_OPTIONS = {
  log: [
    { labelKey: "pools.layouts.stripe", value: "stripe" },
    { labelKey: "pools.layouts.mirror", value: "mirror" },
  ],
  cache: [{ labelKey: "pools.layouts.stripe", value: "stripe" }],
  special: [
    { labelKey: "pools.layouts.stripe", value: "stripe" },
    { labelKey: "pools.layouts.mirror", value: "mirror" },
  ],
  dedup: [
    { labelKey: "pools.layouts.stripe", value: "stripe" },
    { labelKey: "pools.layouts.mirror", value: "mirror" },
  ],
  spare: [{ labelKey: "pools.layouts.stripe", value: "stripe" }],
};

export function buildPowerOfTwoSizeOptions(min, max) {
  const options = [];
  for (let value = min; value <= max; value *= 2) {
    options.push({
      label: formatPowerOfTwoSize(value),
      value: formatPowerOfTwoSize(value),
    });
  }
  return options;
}

const RECORD_SIZE_OPTIONS = buildPowerOfTwoSizeOptions(512, 1024 * 1024);

export const PROPERTY_INPUTS = {
  autoexpand: { type: "select", options: BOOLEAN_OPTIONS },
  autoreplace: { type: "select", options: BOOLEAN_OPTIONS },
  autotrim: { type: "select", options: BOOLEAN_OPTIONS },
  bootfs: { type: "select", options: [] },
  cachefile: { type: "text", placeholderKey: "properties.placeholders.cachefilePath" },
  comment: { type: "text", placeholderKey: "properties.placeholders.poolComment" },
  delegation: { type: "select", options: BOOLEAN_OPTIONS },
  failmode: { type: "select", options: FAILMODE_OPTIONS },
  listsnapshots: { type: "select", options: BOOLEAN_OPTIONS },
  multihost: { type: "select", options: BOOLEAN_OPTIONS },
};

export const ROOT_DATASET_PROPERTY_INPUTS = {
  aclinherit: { type: "select", options: ACLINHERIT_OPTIONS },
  aclmode: { type: "select", options: ACLMODE_OPTIONS },
  acltype: { type: "select", options: ACLTYPE_OPTIONS },
  atime: { type: "select", options: BOOLEAN_OPTIONS },
  canmount: { type: "select", options: CANMOUNT_OPTIONS },
  casesensitivity: { type: "select", options: CASESENSITIVITY_OPTIONS },
  checksum: { type: "select", options: CHECKSUM_OPTIONS },
  compression: { type: "select", options: [] },
  copies: { type: "select", options: COPIES_OPTIONS },
  dedup: { type: "select", options: DEDUP_OPTIONS },
  devices: { type: "select", options: BOOLEAN_OPTIONS },
  dnodesize: { type: "select", options: DNODESIZE_OPTIONS },
  exec: { type: "select", options: BOOLEAN_OPTIONS },
  logbias: { type: "select", options: LOGBIAS_OPTIONS },
  mountpoint: { type: "text", placeholderKey: "properties.placeholders.mountpoint" },
  nbmand: { type: "select", options: BOOLEAN_OPTIONS },
  normalization: { type: "select", options: NORMALIZATION_OPTIONS },
  overlay: { type: "select", options: BOOLEAN_OPTIONS },
  primarycache: { type: "select", options: CACHE_OPTIONS },
  quota: { type: "text", placeholderKey: "properties.placeholders.quota" },
  readonly: { type: "select", options: BOOLEAN_OPTIONS },
  recordsize: { type: "select", options: RECORD_SIZE_OPTIONS },
  redundant_metadata: { type: "select", options: REDUNDANT_METADATA_OPTIONS },
  refquota: { type: "text", placeholderKey: "properties.placeholders.quota" },
  refreservation: { type: "text", placeholderKey: "properties.placeholders.refreservation" },
  relatime: { type: "select", options: BOOLEAN_OPTIONS },
  reservation: { type: "text", placeholderKey: "properties.placeholders.reservation" },
  secondarycache: { type: "select", options: CACHE_OPTIONS },
  setuid: { type: "select", options: BOOLEAN_OPTIONS },
  snapdir: { type: "select", options: SNAPDIR_OPTIONS },
  sync: { type: "select", options: SYNC_OPTIONS },
  utf8only: { type: "select", options: BOOLEAN_OPTIONS },
  xattr: { type: "select", options: XATTR_OPTIONS },
};

export const CREATE_ROOT_DATASET_FIELDS = {
  common: [
    "canmount",
    "compression",
    "mountpoint",
    "readonly",
    "recordsize",
    "quota",
    "reservation",
    "sync",
  ],
  advanced: [
    "aclinherit",
    "aclmode",
    "acltype",
    "atime",
    "casesensitivity",
    "checksum",
    "copies",
    "dedup",
    "devices",
    "dnodesize",
    "exec",
    "logbias",
    "nbmand",
    "normalization",
    "overlay",
    "primarycache",
    "redundant_metadata",
    "refquota",
    "refreservation",
    "relatime",
    "secondarycache",
    "setuid",
    "snapdir",
    "utf8only",
    "xattr",
  ],
};

function formatPowerOfTwoSize(bytes) {
  if (bytes < 1024) {
    return `${bytes}B`;
  }
  if (bytes < 1024 * 1024) {
    return `${bytes / 1024}K`;
  }
  return `${bytes / (1024 * 1024)}M`;
}
