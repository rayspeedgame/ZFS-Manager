# fixtures

> [English Version](./README.md)

这里存放后端测试和调试使用的静态样例数据。

## 当前用途

- 模拟 `lsblk`、`findmnt`、`blkid`
- 模拟 `zpool` 和 `zfs` 输出
- 模拟 SMART 数据（`smart_info_sample.txt` 包含 ATA 和 NVMe 样例）
- 支持解析器测试与调试脚本

如果后续新增更复杂的 dataset 树、snapshot 场景或 pool 拓扑，建议优先把真实输出样例补到这里。
