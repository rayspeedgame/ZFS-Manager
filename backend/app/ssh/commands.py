"""Read-only commands used to collect storage state with minimal SSH round-trips."""

from __future__ import annotations

SECTION_PREFIX = "__ZFS_MANAGER_SECTION__"

LSBLK_JSON = "lsblk --json -O"
ZPOOL_STATUS = "zpool status -LP"

# Each overview command intentionally groups several read-only queries into a
# single SSH invocation. This keeps polling efficient and reduces latency from
# repeated connection round-trips.
DISK_OVERVIEW = (
    "sh -lc '"
    f'printf "{SECTION_PREFIX} lsblk_json\\n"; '
    "lsblk --json -O; "
    f'printf "\\n{SECTION_PREFIX} findmnt_json\\n"; '
    "findmnt --json -A; "
    f'printf "\\n{SECTION_PREFIX} blkid\\n"; '
    "blkid -o full; "
    f'printf "\\n{SECTION_PREFIX} disk_by_id\\n"; '
    "for entry in /dev/disk/by-id/*; do "
    '[ -e "$entry" ] || continue; '
    'printf "%s\\t%s\\n" "$(basename "$entry")" "$(readlink -f "$entry")"; '
    "done 2>/dev/null || true"
    "'"
)

ZPOOL_CORE = (
    "sh -lc '"
    f'printf "{SECTION_PREFIX} zpool_status\\n"; '
    "zpool status -LP; "
    f'printf "\\n{SECTION_PREFIX} zpool_list\\n"; '
    "zpool list -Hp -o name,size,allocated,free,checkpoint,fragmentation,capacity,dedupratio,health,altroot"
    "'"
)

ZPOOL_PROPERTIES = "zpool get -Hp all"

ZPOOL_OVERVIEW = (
    "sh -lc '"
    f'printf "{SECTION_PREFIX} zpool_status\\n"; '
    "zpool status -LP; "
    f'printf "\\n{SECTION_PREFIX} zpool_list\\n"; '
    "zpool list -Hp -o name,size,allocated,free,checkpoint,fragmentation,capacity,dedupratio,health,altroot; "
    f'printf "\\n{SECTION_PREFIX} zpool_get\\n"; '
    "zpool get -Hp all"
    "'"
)

ZFS_DATASET_CORE = (
    "sh -lc '"
    f'printf "{SECTION_PREFIX} zfs_list\\n"; '
    "zfs list -Hp -t filesystem,volume,snapshot "
    "-o name,type,used,avail,refer,mountpoint,compression,volsize,volblocksize,recordsize,readonly,"
    "logicalused,logicalreferenced,written,usedbysnapshots,usedbydataset,usedbychildren,usedbyrefreservation,creation"
    "'"
)

ZFS_DATASET_PROPERTIES = "zfs get -Hp -t filesystem,volume,snapshot all"

ZFS_DATASET_OVERVIEW = (
    "sh -lc '"
    f'printf "{SECTION_PREFIX} zfs_list\\n"; '
    "zfs list -Hp -t filesystem,volume,snapshot "
    "-o name,type,used,avail,refer,mountpoint,compression,volsize,volblocksize,recordsize,readonly,"
    "logicalused,logicalreferenced,written,usedbysnapshots,usedbydataset,usedbychildren,usedbyrefreservation,creation; "
    f'printf "\\n{SECTION_PREFIX} zfs_get\\n"; '
    "zfs get -Hp -t filesystem,volume,snapshot all"
    "'"
)

COMMANDS = {
    "lsblk": LSBLK_JSON,
    "zpool": ZPOOL_STATUS,
    "disk_overview": DISK_OVERVIEW,
    "zpool_core": ZPOOL_CORE,
    "zpool_properties": ZPOOL_PROPERTIES,
    "zpool_overview": ZPOOL_OVERVIEW,
    "dataset_core": ZFS_DATASET_CORE,
    "dataset_properties": ZFS_DATASET_PROPERTIES,
    "dataset_overview": ZFS_DATASET_OVERVIEW,
}


def resolve_command(name: str) -> str:
    """Resolve a stable command alias to the actual shell command string."""
    try:
        return COMMANDS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown command alias: {name}") from exc
