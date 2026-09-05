# ssh

> [中文版本](./README.zh-CN.md)

This layer is responsible for interacting with remote hosts and parsing command output.

## File Descriptions

- `commands.py`: Defines grouped read-only commands
- `client.py`: Establishes SSH connection and executes commands
- `parser.py`: Parses command output into structured data

## Current Capabilities

- Supports polling-required read-only command groups
- Supports SSH command execution for pool, dataset, snapshot, and scheduled write operations
- `client.py` returns detailed execution results including `stdout / stderr / exit_status`
- `SMART_INFO` command collects `smartctl -a --json` for all non-virtual block devices, excluding `loop`, `ram`, `fd`, `sr`, `zd`, and `zram`

## Current Parsing Focus

- `zpool status` supports multi-pool topology parsing
- `zfs list/get` covers filesystem, volume, and snapshot simultaneously
- `smartctl --json` output is parsed into structured `SmartOverview` with per-device `DiskSmartInfo`:
  - ATA attributes (`ata_smart_attributes.table`) and NVMe health log (`nvme_smart_health_information_log`) are both supported
  - Protocol normalization: `sat` → `sata`, others preserved
- Overview parsing results serve both debugging and final structured page data

## Remote Requirements

- The target host must provide `zpool`, `zfs`, `lsblk`, `findmnt`, `blkid`, and `smartctl`
- SMART collection requires remote `smartmontools`; the SSH account needs permission to read disk health and execute any enabled write operations
- Fixture mode loads the existing state fixtures only; it does not automatically load `tests/fixtures/smart_info_sample.txt` as SMART poll data
