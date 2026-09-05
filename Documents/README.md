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
- The frontend has eight top-level pages: Dashboard, Disks, Pools, Datasets, Snapshots, Schedules, Tasks, and Settings.
- The task system now includes SQLite persistence, startup recovery, pagination, and status filtering.
- Snapshot scheduling supports levels from minutely through monthly.
- Scheduled snapshots use short names while schedule ownership is written into ZFS user properties.
- Pool maintenance now covers:
  - `scrub`
  - `clear`
  - `offline / online`
  - `replace`
  - RAID-Z `expansion`
- Disk identity and SMART health monitoring:
  - `displayName`, `commandPath`, `commandTarget`, `rawCommandTarget`, `aliases`
  - SMART auto-polling with smartctl, inline health column, full attribute dialog, ATA/NVMe support, non-physical device filtering
- **Client-aware polling** — the poller automatically switches between active (fast) and idle (slow) refresh cadences based on WebSocket client presence. A `client_tracker` module tracks connected clients, and the poller decouples 1-second mode detection from configurable wake‑up / job refresh intervals. All idle intervals are configurable in the Settings UI.
- Settings support runtime rebuild on save, no-save SSH testing, and optional web login; the project ships a single-container Docker/Nginx deployment.

## Current Rules

- New disks that are not yet part of a pool should prefer `by-id`.
- Existing pool-member maintenance must use the exact member token from `zpool status -L`.
- Long-running workflows should treat ZFS and host state as the source of truth whenever possible.
- RAID-Z expansion recovery must consider both the `expand:` phase and the automatic `scrub` phase, plus the observed member change.
- Existing-pool topology updates currently expose supported auxiliary classes only and reject new data vdevs.
- Recurring scrub is currently weekly-only; recurring snapshots support minutely through monthly schedules.
- SMART requires `smartmontools` on the remote host; fixture mode does not currently load SMART sample data.
