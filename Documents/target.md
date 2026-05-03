# Target

## 当前目标

把 ZFS Manager 打造成一个面向单机或小规模主机的 ZFS Web 管理界面，让维护者在不直接敲命令的情况下完成大部分常见 pool 和 dataset 操作。

## 已完成能力

### pool

- pool 状态查看
- pool 属性修改
- pool 拓扑展示
- pool 附加设备添加
  - `log`
  - `cache`
  - `special`
  - `dedup`
  - `spare`
- 新建 pool
  - 属性设置
  - root dataset 属性设置
  - `data vdev` 分步选择
  - 附加设备分步选择
  - 单条原子化 `zpool create`
- 删除 pool
- 移除可删除的 topology 目标
- by-id 展示与 inactive `zfs_member` 识别

### dataset

- dataset / zvol inventory
- dataset 树形展示
- snapshot 可选显示
- dataset / zvol 创建
- dataset 属性修改
- dataset 删除

## 当前交互目标

- 高风险操作必须有确认弹窗
- 操作结果必须可回显
- SSH 命令日志必须可查看
- 写操作完成后必须刷新到最新状态

## 下一阶段方向

- snapshot 专用管理流
- `replace`
- `detach`
- `offline / online`
- 更完整的 SMART 联动
- 更细粒度的权限控制
