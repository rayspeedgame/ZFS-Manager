# fixtures

> [中文版本](./README.zh-CN.md)

Static sample data for backend testing and debugging.

## Current Usage

- Simulate `lsblk`, `findmnt`, `blkid`
- Simulate `zpool` and `zfs` output
- Simulate SMART data (`smart_info_sample.txt` contains ATA and NVMe samples)
- Support parser testing and debugging scripts

If more complex dataset trees, snapshot scenarios, or pool topologies are added later, it is recommended to prioritize adding real output samples here.
