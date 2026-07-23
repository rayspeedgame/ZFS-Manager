# services

> [English Version](./README.md)

前端 API 服务层。

## 文件

- `api.js`
  - pool 和 dataset 写请求
  - `scrub` 启动与停止
  - 任务记录列表与详情
  - 计划任务列表、创建、更新和删除
  - 设置读取、保存和 SSH 测试
  - 磁盘 SMART 数据获取（`getDiskSmartData`）与刷新（`refreshDiskSmartData`）
  - 登录状态、登录、退出
  - 共享 API 基础地址辅助函数

## 说明

- 所有请求默认携带 `credentials: "include"`，以便复用后端登录 cookie
- 这一层负责把请求路径和 payload 形状与后端 API 对齐
- 任务记录读取现在支持分页和状态筛选参数
