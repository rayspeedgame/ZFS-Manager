# fixtures

> [中文版本](./README.zh-CN.md)

Static sample data for backend testing and debugging.

## Current Usage

- Simulate `lsblk`, `findmnt`, `blkid`
- Simulate `zpool` and `zfs` output
- Provide SMART parser/debugging samples (`smart_info_sample.txt` contains ATA and NVMe output)
- Support parser testing and debugging scripts

If more complex dataset trees, snapshot scenarios, or pool topologies are added later, it is recommended to prioritize adding real output samples here.

Note: the automated tests do not currently read the SMART sample, and the fixture-mode poller does not inject it into `smart_overview`.
