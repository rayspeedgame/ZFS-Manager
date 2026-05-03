# Documents

This folder keeps project-facing reference notes for maintainers and future contributors.

## Files

- `agent.md`: quick onboarding notes for a new contributor or coding agent
- `target.md`: current product goals, shipped capabilities, and next steps
- `ProjectStruction.md`: high-level architecture and responsibility split
- `ProjectDirectoryStructure.md`: directory map with the current frontend component split

## Current Focus

- The frontend now uses a container-plus-components layout for `Pools` and `Datasets`.
- Shared property editors, command results, and command log UI now live under `frontend/src/components/common/`.
- Page containers in `frontend/src/views/` own API calls and protect in-progress drafts from live snapshot refreshes.
- The frontend now has a shared `vue-i18n` layer with English and Simplified Chinese resources plus a persistent topbar language switcher.
