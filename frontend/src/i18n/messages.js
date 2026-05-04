import enUS from "./messages/en-US.js";
import zhCN from "./messages/zh-CN.js";

// Keep one stable export shape for vue-i18n while letting each language split
// its copy into smaller module files.
export const messages = {
  "en-US": enUS,
  "zh-CN": zhCN,
};
