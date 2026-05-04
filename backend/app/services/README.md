# services

> [中文版本](./README.zh-CN.md)

This layer is responsible for the core behavior of the backend runtime, especially polling, caching, snapshot assembly, and write operation execution.

## File Descriptions

- `poller.py`: Schedules SSH refresh tasks at different frequencies, maintains snapshot cache, and generates `summary / disks / pools / datasets`
- `pool_creator.py`: Generates and executes atomic `zpool create`
- `property_updater.py`: Executes `zpool set`
- `topology_updater.py`: Executes `zpool add`
- `pool_destroyer.py`: Executes `zpool destroy`
- `pool_remover.py`: Executes `zpool remove`
- `dataset_creator.py`: Executes `zfs create`
- `dataset_property_updater.py`: Executes `zfs set`
- `dataset_destroyer.py`: Executes `zfs destroy`

## Current Design

- `StatePoller` refreshes at different frequencies for `pools / datasets / disks / properties`
- Write endpoints do not directly modify in-memory snapshots, but re-collect real host state
- Dataset hierarchy, parent-child relationships, and display order are uniformly organized by the backend before passing to the frontend
