# Documents

> [中文版本](./README.zh-CN.md)

This directory contains project documentation intended for maintainers and future developers.

## Files

- `agent.md`: Quick start guide for new collaborators or coding agents
- `target.md`: Current product goals, shipped capabilities, and future direction
- `Roadmap.md`: Planned feature roadmap, implementation order, and snapshot UI direction
- `TaskSystemArchitecture.md`: Task persistence, recovery, and extensibility design
- `ProjectStruction.md`: High-level architecture and responsibility layers
- `ProjectDirectoryStructure.md`: Current directory structure and key module distribution

## Current Focus

- Backend configuration files have been consolidated into `backend/config/`
- Frontend added a settings page for editing SSH, polling, and login configurations
- Backend provides settings read, save, SSH test, login status, login, and logout endpoints
- Frontend supports optional password login gate, disabled by default
- Frontend internationalization has been split into language + module structure for easy extension
- The task system design treats remote ZFS state as the primary recovery source
