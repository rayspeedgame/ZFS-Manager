# backend/tests/fixtures

This folder stores saved command output samples used for parser development and
tests.

## Why fixtures matter

They make parser and polling work fast and repeatable:

- no SSH dependency during local parser iteration
- stable test input
- easier debugging of edge cases
- repeatable validation for snapshot assembly

## Current fixture types

- `lsblk` JSON output
- `blkid` text output
- `findmnt` JSON output
- aggregated disk overview output
- aggregated zpool overview output
- aggregated dataset overview output
- `zpool status` text output
