# Documents

> [中文版本](./README.zh-CN.md)

`Documents/` stores project-level design notes, roadmaps, and structure maps.

## Index

- `agent.md`
  - collaboration and handoff notes
- `target.md`
  - current product goal and delivered capability summary
- `Roadmap.md`
  - staged roadmap and near-term priorities
- `TaskSystemArchitecture.md`
  - task persistence, recovery, scheduling, and extensibility
- `SnapshotManagementArchitecture.md`
  - snapshot page, recurring snapshot, and retention design
- `PoolMaintenanceArchitecture.md`
  - pool maintenance, device identity, replace, and RAID-Z expansion design
- `ProjectStruction.md`
  - high-level structure overview
- `ProjectDirectoryStructure.md`
  - expanded directory-by-directory structure notes

## Current Focus

- The backend uses SSH polling plus REST write execution.
- The task system now includes SQLite persistence, startup recovery, pagination, and status filtering.
- Snapshot scheduling supports levels from minutely through monthly.
- Scheduled snapshots use short names while schedule ownership is written into ZFS user properties.
- Pool maintenance now covers:
  - `scrub`
  - `clear`
  - `offline / online`
  - `replace`
  - RAID-Z `expansion`
- The disk identity model now separates display-facing and execution-facing fields:
  - `displayName`
  - `commandPath`
  - `commandTarget`
  - `rawCommandTarget`
  - `aliases`
- **Client-aware polling** — the poller automatically switches between active (fast) and idle (slow) refresh cadences based on WebSocket client presence. A `client_tracker` module tracks connected clients, and the poller decouples 1-second mode detection from configurable wake‑up / job refresh intervals. All idle intervals are configurable in the Settings UI.

## Current Rules

- New disks that are not yet part of a pool should prefer `by-id`.
- Existing pool-member maintenance must use the exact member token from `zpool status -L`.
- Long-running workflows should treat ZFS and host state as the source of truth whenever possible.
- RAID-Z expansion recovery must consider both the `expand:` phase and the automatic `scrub` phase, plus the observed member change.
