import app from "./zh-CN/app.js";
import routes from "./zh-CN/routes.js";
import common from "./zh-CN/common.js";
import dashboard from "./zh-CN/dashboard.js";
import disks from "./zh-CN/disks.js";
import poolsRaw from "./zh-CN/pools.js";
import datasets from "./zh-CN/datasets.js";
import snapshots from "./zh-CN/snapshots.js";
import settings from "./zh-CN/settings.js";
import properties from "./zh-CN/properties.js";
import login from "./zh-CN/login.js";
import tasks from "./zh-CN/tasks.js";
import schedules from "./zh-CN/schedules.js";

// The dedicated zh-CN pools file has older mojibake sections. Keep a small
// merge layer here so newly added pool-maintenance keys stay available
// without rewriting the entire historical locale file in one step.
const pools = {
  ...poolsRaw,
  quickFacts: {
    ...(typeof poolsRaw.quickFacts === "object" ? poolsRaw.quickFacts : {}),
    title: "快速信息",
    scan: (typeof poolsRaw.quickFacts === "object" && poolsRaw.quickFacts.scan) || "扫描",
    errors: (typeof poolsRaw.quickFacts === "object" && poolsRaw.quickFacts.errors) || "错误",
    notReported: (typeof poolsRaw.quickFacts === "object" && poolsRaw.quickFacts.notReported) || "未上报",
  },
  deviceActions: {
    ...(poolsRaw.deviceActions || {}),
    raidzExpand: poolsRaw.deviceActions?.raidzExpand || "扩展 RAID-Z",
  },
  dialogs: {
    ...(poolsRaw.dialogs || {}),
    confirmRaidzExpandTitle: poolsRaw.dialogs?.confirmRaidzExpandTitle || "确认 RAID-Z 扩展",
    confirmRaidzExpand: poolsRaw.dialogs?.confirmRaidzExpand || "确认扩展",
    expandingRaidz: poolsRaw.dialogs?.expandingRaidz || "扩展中...",
    expandingRaidzVdev: poolsRaw.dialogs?.expandingRaidzVdev || "正在扩展 RAID-Z vdev...",
    expandingRaidzVdevDescription:
      poolsRaw.dialogs?.expandingRaidzVdevDescription ||
      "请稍候，后端会对所选 RAID-Z vdev 执行 zpool attach，并刷新最新存储池状态。",
    raidzExpandWarning:
      poolsRaw.dialogs?.raidzExpandWarning ||
      "这会向所选 RAID-Z vdev 添加一块新磁盘。扩展进度会作为长期任务持续跟踪。",
    expansionDevice: poolsRaw.dialogs?.expansionDevice || "扩展设备",
  },
  summary: {
    ...(poolsRaw.summary || {}),
    raidzExpandSucceeded: poolsRaw.summary?.raidzExpandSucceeded || "RAID-Z 扩展命令执行成功。",
    raidzExpandFailed: poolsRaw.summary?.raidzExpandFailed || "RAID-Z 扩展命令执行失败。",
  },
};

export default {
  app,
  routes,
  common,
  dashboard,
  disks,
  pools,
  datasets,
  snapshots,
  settings,
  properties,
  login,
  tasks,
  schedules,
};
