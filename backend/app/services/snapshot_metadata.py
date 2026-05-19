from __future__ import annotations

USER_PROPERTY_PREFIX = "org.zfsmanager"

SNAPSHOT_KIND_PROPERTY = f"{USER_PROPERTY_PREFIX}:snapshot-kind"
SCHEDULE_ID_PROPERTY = f"{USER_PROPERTY_PREFIX}:schedule-id"
STRATEGY_NAME_PROPERTY = f"{USER_PROPERTY_PREFIX}:strategy-name"
SCHEDULE_LEVEL_PROPERTY = f"{USER_PROPERTY_PREFIX}:schedule-level"
RETENTION_KEEP_LATEST_PROPERTY = f"{USER_PROPERTY_PREFIX}:retention-keep-latest"
TRIGGER_PROPERTY = f"{USER_PROPERTY_PREFIX}:trigger"
RECURSIVE_PROPERTY = f"{USER_PROPERTY_PREFIX}:recursive"


def build_scheduled_snapshot_properties(
    *,
    schedule_id: str,
    strategy_name: str,
    schedule_level: str,
    keep_latest: int,
    recursive: bool,
) -> dict[str, str]:
    return {
        SNAPSHOT_KIND_PROPERTY: "scheduled",
        SCHEDULE_ID_PROPERTY: str(schedule_id),
        STRATEGY_NAME_PROPERTY: str(strategy_name),
        SCHEDULE_LEVEL_PROPERTY: str(schedule_level),
        RETENTION_KEEP_LATEST_PROPERTY: str(max(0, int(keep_latest))),
        TRIGGER_PROPERTY: "scheduler",
        RECURSIVE_PROPERTY: "true" if recursive else "false",
    }


def read_snapshot_user_property(row: dict, property_name: str) -> str | None:
    properties = row.get("properties")
    if not isinstance(properties, dict):
        return None
    value = properties.get(property_name)
    if isinstance(value, dict):
        raw = value.get("value")
    else:
        raw = value
    if raw in (None, "", "-"):
        return None
    return str(raw)
