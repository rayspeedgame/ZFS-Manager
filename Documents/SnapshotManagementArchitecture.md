# Snapshot Management Architecture

> [中文版](./SnapshotManagementArchitecture.zh-CN.md)

## Current Baseline

The snapshot module now uses a two-entry structure:

- `DatasetsView` for quick manual snapshot creation
- `SnapshotsView` for centralized snapshot management

This baseline has already been implemented and extended with:

- manual snapshot create and delete
- snapshot rollback with advanced modes
- dedicated snapshot filtering and pagination
- scheduled snapshot workflows
- snapshot retention cleanup

## Naming and Ownership Rules

The project no longer treats long snapshot names as the primary ownership signal.

Current direction:

- Scheduled snapshots use short names in the form:
  - `scheduled-{timestamp}-{random}`
- Schedule identity lives in ZFS user properties
- Snapshot cleanup matches schedule-owned snapshots by stored metadata, not by parsing a long name

Recommended property groups:

- snapshot kind
- schedule id
- strategy name
- schedule level
- retention keep-latest count
- recursive flag
- trigger source

## Retention Model

Current retention is intentionally conservative:

- Each schedule owns only the snapshots it created
- Cleanup is keyed by schedule identity
- Recursive schedules still apply retention per dataset, not as one global count
- Manual snapshots must never be affected by scheduled cleanup

## Schedule Levels

Scheduled snapshot levels now supported:

- minutely
- hourly
- daily
- weekly
- monthly

Recommended product rule:

- Keep schedule creation explicit per level
- Show only the relevant pattern fields for the selected level
- Keep the stored pattern normalized on the backend

## Frontend Responsibilities

- `DatasetsView`: quick manual snapshot initiation
- `SnapshotsView`: manual management, rollback, delete, inspection
- `SchedulesView`: scheduled snapshot creation and retention settings

## Backend Responsibilities

- Build and write ZFS user-property metadata during scheduled snapshot creation
- Reconstruct schedule ownership from ZFS properties during reads
- Keep retention decisions scoped to the schedule that created the snapshots
- Avoid relying on risky or path-heavy snapshot names

## Next Snapshot Work

- Show schedule ownership fields in more snapshot views
- Allow editing existing snapshot schedules
- Add richer retention reporting

> **On "tiered retention":** The current **multi-schedule independent retention** design already covers tiered scenarios. Operators simply create separate schedules for different frequencies (daily, weekly, monthly), each retaining its own latest N snapshots without interference.
> Snapshot ownership is tagged by `schedule_id` in ZFS user properties, and retention cleanup is keyed by schedule identity — it never affects manual snapshots or snapshots from other schedules.
> Therefore no complex tiered retention rules are needed inside a single schedule.
