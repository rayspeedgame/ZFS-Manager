# Pool Maintenance Architecture

> [中文版本](./PoolMaintenanceArchitecture.zh-CN.md)

This document describes how pool-maintenance workflows are layered in the current project and which capabilities are already delivered.

## Goals

- Expose pool maintenance through consistent UI entry points plus the shared task system.
- Separate display identity from execution identity so device-path churn does not break maintenance commands.
- Recover long-running maintenance from `zpool status` whenever possible instead of depending on a single SSH session.

## Delivered Capabilities

- `scrub` start, stop, progress display, and task recovery
- pool-level `clear`
- device-level `offline` / `online`
- device-level `replace` plus `resilver` tracking
- RAID-Z vdev-level `raidz expansion`

## Disk and Member Identity Model

The backend now treats “disk identity” and “pool-member identity” as separate concepts.

- `displayName`
  - UI-facing primary label
- `kernelPath`
  - kernel device path such as `/dev/sdb`
- `byIdPath`
  - stable alias preferred for display and new-device operations
- `commandPath`
  - execution path preferred for disks that are not yet part of a pool
- `commandTarget`
  - exact existing member token from `zpool status -L`, used for `offline / online / remove / replace`
- `rawCommandTarget`
  - raw topology token preserved for audit and recovery
- `aliases`
  - tolerant lookup aliases used across refresh cycles

Partition-backed members also inherit the parent disk’s whole-disk `by-id` aliases. That allows recovery code to treat a stored whole-disk `by-id` and a later `-part1` member as the same physical disk.

## Frontend Layering

### `PoolDetailDrawer`

Owns pool-level information and light maintenance actions:

- `scrub`
- `clear`
- maintenance summary

### `PoolTopologyDrawer`

Owns device-level and vdev-level maintenance actions:

- device `offline / online`
- device `replace`
- RAID-Z vdev `Expand RAID-Z`

The drawer shows alias-first labels for operators, while the backend still resolves the correct execution identity at submit time.

## Backend Layering

### `poller.py`

Responsible for:

- collecting `lsblk`, `blkid`, and `zpool status -L`
- normalizing disk identity
- building `topologySummary`
- exposing `scanStatus` and `expandStatus`
- managing client-aware active/idle refresh cadences (see `client_tracker.py`)

### Dedicated maintenance services

- `pool_scrubber.py`
- `pool_maintainer.py`
- `pool_replacer.py`
- `pool_raidz_expander.py`

Each service owns one command family so route files stay thin.

### `task_recovery.py`

Responsible for recovering:

- `scrub`
- `resilver` after `replace`
- `raidz expansion`

## RAID-Z Expansion Rules

The project implements RAID-Z vdev expansion, not single-disk `online -e` growth:

- the UI entry point is on the RAID-Z vdev item, not on a leaf disk
- the backend runs `zpool attach <pool> <raidz-vdev> <new-device>`
- candidate disks prefer `by-id`
- a new RAID-Z expansion is blocked while the same pool already has an active scan-class task

### Progress and Recovery

Recovery treats RAID-Z expansion as two phases:

1. `expand`
   - parsed from the `expand:` section in `zpool status`
   - contributes the first 40% of total progress
2. automatic `scrub`
   - ZFS starts scrub automatically after the expansion phase finishes
   - parsed from the `scan:` section
   - contributes the second 40% of total progress

The task is only marked complete when all of the following are true:

- `expandStatus.completed = true`
- `scanStatus.completed = true`
- the new member can be recognized in the target vdev member list
- the current member count is greater than the count recorded before submission

If those signals still cannot be confirmed after the observation window, the task moves into an operator-attention state instead of waiting forever.

## Current API Surface

- `POST /api/pools/{pool_name}/offline`
- `POST /api/pools/{pool_name}/online`
- `POST /api/pools/{pool_name}/clear`
- `POST /api/pools/{pool_name}/replace`
- `POST /api/pools/{pool_name}/raidz-expand`

## Important Maintenance Fields in the Current Snapshot

- `pool.status.scan`
- `pool.status.expand`
- `pool.scanStatus`
- `pool.expandStatus`
- `pool.topologySummary[*].items[*].members[*].displayLabel`
- `pool.topologySummary[*].items[*].members[*].kernelPath`
- `pool.topologySummary[*].items[*].members[*].byIdPath`
- `pool.topologySummary[*].items[*].members[*].commandTarget`
- `pool.topologySummary[*].items[*].members[*].rawCommandTarget`
- `pool.topologySummary[*].items[*].members[*].aliases`
- `pool.topologySummary[*].items[*].canRaidzExpand`
- `pool.topologySummary[*].items[*].raidzExpandCandidates`

## Near-Term Direction

- add clearer candidate-disk eligibility explanations for `replace` and `raidz expansion`
- improve maintenance summaries in pool details
- revisit deeper capacity prechecks and richer task audit only when needed
