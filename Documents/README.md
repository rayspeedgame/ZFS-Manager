# Documents

> [中文版](./README.zh-CN.md)

`Documents/` holds the project-level design notes, delivery roadmap, and codebase maps.

## Index

- `agent.md`: Handoff notes, implementation conventions, and extension hints
- `target.md`: Product goals and delivered capability summary
- `Roadmap.md`: Delivery roadmap and next-stage priorities
- `TaskSystemArchitecture.md`: Task persistence, recovery, scheduling, and extensibility design
- `SnapshotManagementArchitecture.md`: Snapshot module structure, dedicated page design, scheduling, and retention direction
- `ProjectStruction.md`: High-level project structure overview
- `ProjectDirectoryStructure.md`: Expanded directory-by-directory code map

## Current Focus

- The backend uses SSH polling plus REST write operations
- The task system now includes:
  - SQLite-backed task and schedule persistence
  - startup recovery and active-task reconciliation
  - scheduled `scrub`
  - scheduled `snapshot`
  - schedule-scoped snapshot retention cleanup
- The snapshot module now includes:
  - dataset quick-create entry
  - dedicated snapshot page
  - rollback flows
  - advanced rollback mode selection
  - scheduled snapshot workflows from minutely to monthly
  - ZFS user-property tagging for scheduled snapshot ownership and retention identity

## Notes

- Runtime configuration lives under `backend/config/`
- Long-running workflow truth should come from ZFS and host state whenever possible
- Scheduled snapshot cleanup now keys off schedule metadata written into snapshot user properties instead of relying on long snapshot names
