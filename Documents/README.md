# Documents

> [中文版本](./README.zh-CN.md)

`Documents/` contains project-facing design notes, structure guides, and roadmap material.

## Index

- `agent.md`: Developer handoff notes, implementation conventions, and extension hints
- `target.md`: Product direction and current delivered capability summary
- `Roadmap.md`: Delivery roadmap, implementation order, and next-stage priorities
- `TaskSystemArchitecture.md`: Task persistence, recovery, scheduling, and extensibility design
- `ProjectStruction.md`: High-level project structure overview
- `ProjectDirectoryStructure.md`: Expanded directory-by-directory code map

## Current Notes

- Runtime configuration lives under `backend/config/`
- The backend is centered on SSH polling, REST write operations, task persistence, and recovery
- The frontend is centered on routed views, Pinia state, i18n, and live snapshot consumption
- The task system now covers:
  - SQLite-backed task history
  - startup recovery
  - scheduled scrub definitions
  - paged and filterable task records
- ZFS and host state remain the primary source of truth for long-running workflow recovery
