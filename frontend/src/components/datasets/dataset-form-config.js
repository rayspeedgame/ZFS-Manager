import { BOOLEAN_OPTIONS, CACHE_OPTIONS, SYNC_OPTIONS } from "../common/property-options.js";

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

const SNAPDEV_OPTIONS = [
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

const VOLMODE_OPTIONS = [
  { label: "default", value: "default" },
  { label: "full", value: "full" },
  { label: "dev", value: "dev" },
  { label: "none", value: "none" },
];

const XATTR_OPTIONS = [
  { label: "on", value: "on" },
  { label: "off", value: "off" },
  { label: "dir", value: "dir" },
  { label: "sa", value: "sa" },
];

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

export const EDITABLE_DATASET_PROPERTIES = {
  filesystem: new Set([
    "aclinherit",
    "aclmode",
    "acltype",
    "atime",
    "canmount",
    "checksum",
    "compression",
    "copies",
    "dedup",
    "devices",
    "dnodesize",
    "exec",
    "logbias",
    "mountpoint",
    "nbmand",
    "overlay",
    "primarycache",
    "quota",
    "readonly",
    "recordsize",
    "redundant_metadata",
    "refquota",
    "refreservation",
    "relatime",
    "reservation",
    "secondarycache",
    "setuid",
    "snapdir",
    "sync",
    "xattr",
  ]),
  volume: new Set([
    "checksum",
    "compression",
    "copies",
    "dedup",
    "logbias",
    "primarycache",
    "readonly",
    "refreservation",
    "reservation",
    "secondarycache",
    "snapdev",
    "sync",
    "volmode",
    "volsize",
  ]),
  snapshot: new Set(),
};

export const COMMON_FIXED_DATASET_PROPERTIES = new Set([
  "compressratio",
  "logicalreferenced",
  "logicalused",
  "mounted",
  "origin",
  "referenced",
  "usedbychildren",
  "usedbydataset",
  "usedbyrefreservation",
  "usedbysnapshots",
  "written",
]);

export const COMMON_EDITABLE_DATASET_PROPERTIES = new Set([
  "canmount",
  "compression",
  "mountpoint",
  "quota",
  "readonly",
  "recordsize",
  "reservation",
  "volmode",
  "volsize",
]);

export const EXCLUDED_DATASET_PROPERTIES = new Set([
  "available",
  "avail",
  "creation",
  "mounted",
  "name",
  "refer",
  "type",
  "used",
]);

export const PROPERTY_INPUTS = {
  aclinherit: { type: "select", options: ACLINHERIT_OPTIONS },
  aclmode: { type: "select", options: ACLMODE_OPTIONS },
  acltype: { type: "select", options: ACLTYPE_OPTIONS },
  atime: { type: "select", options: BOOLEAN_OPTIONS },
  canmount: { type: "select", options: CANMOUNT_OPTIONS },
  casesensitivity: { type: "select", options: CASESENSITIVITY_OPTIONS },
  checksum: { type: "select", options: CHECKSUM_OPTIONS },
  copies: { type: "select", options: COPIES_OPTIONS },
  dedup: { type: "select", options: DEDUP_OPTIONS },
  devices: { type: "select", options: BOOLEAN_OPTIONS },
  dnodesize: { type: "select", options: DNODESIZE_OPTIONS },
  exec: { type: "select", options: BOOLEAN_OPTIONS },
  logbias: { type: "select", options: LOGBIAS_OPTIONS },
  mountpoint: { type: "text", placeholder: "/tank/data" },
  nbmand: { type: "select", options: BOOLEAN_OPTIONS },
  normalization: { type: "select", options: NORMALIZATION_OPTIONS },
  overlay: { type: "select", options: BOOLEAN_OPTIONS },
  primarycache: { type: "select", options: CACHE_OPTIONS },
  quota: { type: "text", placeholder: "none, 100G, 1T" },
  readonly: { type: "select", options: BOOLEAN_OPTIONS },
  recordsize: { type: "select", options: RECORD_SIZE_OPTIONS },
  redundant_metadata: { type: "select", options: REDUNDANT_METADATA_OPTIONS },
  refquota: { type: "text", placeholder: "none, 100G, 1T" },
  refreservation: { type: "text", placeholder: "none, 50G" },
  relatime: { type: "select", options: BOOLEAN_OPTIONS },
  reservation: { type: "text", placeholder: "none, 50G" },
  secondarycache: { type: "select", options: CACHE_OPTIONS },
  setuid: { type: "select", options: BOOLEAN_OPTIONS },
  snapdev: { type: "select", options: SNAPDEV_OPTIONS },
  snapdir: { type: "select", options: SNAPDIR_OPTIONS },
  sync: { type: "select", options: SYNC_OPTIONS },
  utf8only: { type: "select", options: BOOLEAN_OPTIONS },
  volblocksize: { type: "select", options: RECORD_SIZE_OPTIONS },
  volmode: { type: "select", options: VOLMODE_OPTIONS },
  volsize: { type: "text", placeholder: "10G, 500G, 2T" },
  xattr: { type: "select", options: XATTR_OPTIONS },
};

export const CREATE_PROPERTY_FIELDS = {
  filesystem: {
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
  },
  volume: {
    common: [
      "volsize",
      "volblocksize",
      "volmode",
      "compression",
      "readonly",
      "reservation",
      "sync",
    ],
    advanced: [
      "checksum",
      "copies",
      "dedup",
      "logbias",
      "primarycache",
      "refreservation",
      "secondarycache",
      "snapdev",
    ],
  },
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
