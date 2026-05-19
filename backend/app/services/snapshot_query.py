from __future__ import annotations

from datetime import UTC, datetime

from app.schemas.snapshot import SnapshotListItem
from app.schemas.zfs_state import AppState
from app.services.snapshot_metadata import (
    SCHEDULE_ID_PROPERTY,
    SCHEDULE_LEVEL_PROPERTY,
    SNAPSHOT_KIND_PROPERTY,
    STRATEGY_NAME_PROPERTY,
    read_snapshot_user_property,
)


def list_snapshots(
    state: AppState,
    *,
    page: int = 1,
    page_size: int = 25,
    search: str = "",
    pool: str = "",
    dataset: str = "",
    snapshot_type: str = "",
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[SnapshotListItem], int, int, int, int]:
    items = _build_snapshot_items(state)

    normalized_search = str(search or "").strip().lower()
    normalized_pool = str(pool or "").strip()
    normalized_dataset = str(dataset or "").strip()
    normalized_type = str(snapshot_type or "").strip().lower()

    filtered: list[SnapshotListItem] = []
    for item in items:
        if normalized_search:
            haystack = f"{item.full_name} {item.dataset}".lower()
            if normalized_search not in haystack:
                continue
        if normalized_pool and item.pool != normalized_pool:
            continue
        if normalized_dataset and item.dataset != normalized_dataset:
            continue
        if normalized_type and item.snapshot_type != normalized_type:
            continue
        filtered.append(item)

    reverse = str(sort_order or "desc").lower() != "asc"
    filtered.sort(key=lambda item: _sort_key(item, sort_by), reverse=reverse)

    total = len(filtered)
    normalized_page_size = max(1, page_size)
    total_pages = max(1, (total + normalized_page_size - 1) // normalized_page_size)
    normalized_page = min(max(1, page), total_pages)
    start = (normalized_page - 1) * normalized_page_size
    end = start + normalized_page_size
    return filtered[start:end], total, normalized_page, normalized_page_size, total_pages


def get_snapshot(state: AppState, snapshot_name: str) -> SnapshotListItem | None:
    normalized = str(snapshot_name or "")
    return next((item for item in _build_snapshot_items(state) if item.full_name == normalized), None)


def list_dataset_snapshots(state: AppState, dataset_name: str, *, limit: int = 5) -> list[SnapshotListItem]:
    normalized = str(dataset_name or "")
    items = [item for item in _build_snapshot_items(state) if item.dataset == normalized]
    items.sort(key=lambda item: _sort_key(item, "created_at"), reverse=True)
    return items[: max(1, limit)]


def snapshot_filters(state: AppState) -> tuple[list[str], list[str], list[str]]:
    items = _build_snapshot_items(state)
    pools = sorted({item.pool for item in items if item.pool})
    datasets = sorted({item.dataset for item in items if item.dataset})
    types = sorted({item.snapshot_type for item in items if item.snapshot_type})
    return pools, datasets, types


def snapshot_exists(state: AppState, snapshot_name: str) -> bool:
    normalized = str(snapshot_name or "")
    return any(item.full_name == normalized for item in _build_snapshot_items(state))


def _build_snapshot_items(state: AppState) -> list[SnapshotListItem]:
    items: list[SnapshotListItem] = []
    dataset_names = {
        str(item.get("name") or "")
        for item in (state.data.datasets or [])
        if str(item.get("type") or "") != "snapshot"
    }
    for row in state.data.datasets or []:
        if str(row.get("type") or "") != "snapshot":
            continue
        full_name = str(row.get("name") or "")
        dataset_name, snapshot_name = _split_snapshot_name(full_name)
        if not dataset_name or not snapshot_name:
            continue
        userrefs = _coerce_int(_read_property_value(row, "userrefs"), default=0)
        strategy_name = read_snapshot_user_property(row, STRATEGY_NAME_PROPERTY)
        schedule_id = read_snapshot_user_property(row, SCHEDULE_ID_PROPERTY)
        schedule_level = read_snapshot_user_property(row, SCHEDULE_LEVEL_PROPERTY)
        can_delete = userrefs <= 0
        delete_reason = None if can_delete else "Snapshot has active user references."
        can_rollback = dataset_name in dataset_names
        rollback_reason = None if can_rollback else "Parent dataset is not available in the current snapshot."
        items.append(
            SnapshotListItem(
                id=full_name,
                name=snapshot_name,
                full_name=full_name,
                dataset=dataset_name,
                pool=str(row.get("poolName") or dataset_name.split("/", 1)[0]),
                created_at=_parse_creation(row.get("creation")),
                used=_coerce_number_or_text(row.get("used")),
                referenced=_coerce_number_or_text(row.get("refer")),
                snapshot_type=_infer_snapshot_type(row, snapshot_name),
                userrefs=userrefs,
                strategy_name=strategy_name,
                schedule_id=schedule_id,
                schedule_level=schedule_level,
                can_delete=can_delete,
                can_rollback=can_rollback,
                delete_reason=delete_reason,
                rollback_reason=rollback_reason,
            )
        )
    return items


def _split_snapshot_name(full_name: str) -> tuple[str, str]:
    normalized = str(full_name or "")
    if "@" not in normalized:
        return "", ""
    return normalized.split("@", 1)


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


def _read_property_value(row: dict, property_name: str):
    properties = row.get("properties")
    if not isinstance(properties, dict):
        return None
    value = properties.get(property_name)
    if isinstance(value, dict):
        return value.get("value")
    return None


def _coerce_int(value, *, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _coerce_number_or_text(value):
    try:
        numeric = int(str(value))
        return numeric
    except (TypeError, ValueError):
        try:
            return int(float(str(value)))
        except (TypeError, ValueError):
            if value in (None, ""):
                return None
            return str(value)


def _infer_snapshot_type(row: dict, snapshot_name: str) -> str:
    property_value = read_snapshot_user_property(row, SNAPSHOT_KIND_PROPERTY)
    if property_value:
        return property_value.lower()
    normalized = str(snapshot_name or "").lower()
    if normalized.startswith("manual-"):
        return "manual"
    if normalized.startswith("scheduled-") or normalized.startswith("auto-") or normalized.startswith("sched-"):
        return "scheduled"
    return "unknown"


def _sort_key(item: SnapshotListItem, sort_by: str):
    normalized = str(sort_by or "created_at").lower()
    if normalized == "name":
        return item.name.lower()
    if normalized == "dataset":
        return item.dataset.lower()
    if normalized == "pool":
        return item.pool.lower()
    if normalized == "used":
        return _sortable_number(item.used)
    if normalized == "referenced":
        return _sortable_number(item.referenced)
    return item.created_at or datetime.fromtimestamp(0, tz=UTC)


def _sortable_number(value) -> int:
    if isinstance(value, int):
        return value
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return -1
