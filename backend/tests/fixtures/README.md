# fixtures

这里存放后端测试和调试使用的静态样例数据。

## 当前用途

- 模拟 `lsblk`、`blkid`、`findmnt`
- 模拟 `zpool` 和 `zfs` 输出
- 支持解析器测试与调试脚本

如果后续新增真实环境特例，比如更复杂的多 pool 拓扑、cache/log/spare 设备或属性边界值，建议优先补充到这里。
