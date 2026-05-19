from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.zfs_state import AppState
from app.services.snapshot_metadata import SCHEDULE_ID_PROPERTY, read_snapshot_user_property


@dataclass(slots=True)
class SnapshotRetentionPlan:
    keep_latest: int
    kept: list[str]
    delete: list[str]


def build_scheduled_snapshot_name(*, triggered_at: datetime) -> str:
    random_suffix = uuid4().hex[:6]
    return f"scheduled-{triggered_at.astimezone(UTC).strftime('%Y%m%d-%H%M%S')}-{random_suffix}"


def plan_snapshot_retention(
    state: AppState,
    *,
    schedule_id: str,
    keep_latest: int,
) -> SnapshotRetentionPlan:
    normalized_keep = max(0, int(keep_latest))
    # Recursive schedules can create snapshots across multiple datasets. We
    # therefore group by dataset first and then keep the latest N inside each
    # dataset, instead of applying one global count to the whole tree.
    groups = _matching_snapshots_by_dataset(state, schedule_id=str(schedule_id or ""))
    kept: list[str] = []
    delete: list[str] = []
    for snapshots in groups.values():
        kept.extend(item["full_name"] for item in snapshots[:normalized_keep])
        delete.extend(item["full_name"] for item in snapshots[normalized_keep:])
    return SnapshotRetentionPlan(
        keep_latest=normalized_keep,
        kept=kept,
        delete=delete,
    )


def _matching_snapshots_by_dataset(state: AppState, *, schedule_id: str) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    normalized_schedule_id = str(schedule_id or "")
    for row in state.data.datasets or []:
        if str(row.get("type") or "") != "snapshot":
            continue
        property_schedule_id = read_snapshot_user_property(row, SCHEDULE_ID_PROPERTY)
        if property_schedule_id != normalized_schedule_id:
            continue
        full_name = str(row.get("name") or "")
        if "@" not in full_name:
            continue
        dataset_name, _snapshot_name = full_name.split("@", 1)
        groups[dataset_name].append(
            {
                "full_name": full_name,
                "created_at": _parse_creation(row.get("creation")),
            }
        )
    for snapshots in groups.values():
        snapshots.sort(
            key=lambda item: (
                item["created_at"] or datetime.fromtimestamp(0, tz=UTC),
                item["full_name"].lower(),
            ),
            reverse=True,
        )
    return groups


def _parse_creation(value) -> datetime | None:
    if value in (None, "", "-"):
        return None
    try:
        timestamp = int(float(value))
    except (TypeError, ValueError):
        return None
    if timestamp <= 0:
        return None
    return datetime.fromtimestamp(timestamp, tz=UTC)
