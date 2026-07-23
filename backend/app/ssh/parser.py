from __future__ import annotations

import json
import re
from typing import Any

from app.ssh.commands import (
    DISK_OVERVIEW,
    LSBLK_JSON,
    SECTION_PREFIX,
    SMART_INFO,
    ZFS_DATASET_CORE,
    ZFS_DATASET_PROPERTIES,
    ZFS_DATASET_OVERVIEW,
    ZPOOL_CORE,
    ZPOOL_PROPERTIES,
    ZPOOL_OVERVIEW,
    ZPOOL_STATUS,
)


_POOL_HEADER_RE = re.compile(r"^\s*pool:\s*(?P<name>\S+)\s*$")
_STATE_RE = re.compile(r"^\s*state:\s*(?P<state>.+?)\s*$")
_SCAN_RE = re.compile(r"^\s*scan:\s*(?P<scan>.+?)\s*$")
_EXPAND_RE = re.compile(r"^\s*expand:\s*(?P<expand>.+?)\s*$")
_CONFIG_HEADER_RE = re.compile(r"^\s*NAME\s+STATE\s+READ\s+WRITE\s+CKSUM\s*$")
_DEVICE_LINE_RE = re.compile(
    r"^(?P<indent>\s*)(?P<name>\S+)\s+"
    r"(?P<state>\S+)\s+"
    r"(?P<read>\d+)\s+"
    r"(?P<write>\d+)\s+"
    r"(?P<cksum>\d+)"
    r"(?:\s+(?P<notes>.*))?$"
)
_STATE_ONLY_LINE_RE = re.compile(
    r"^(?P<indent>\s*)(?P<name>\S+)\s+"
    r"(?P<state>\S+)"
    r"(?:\s+(?P<notes>.*))?$"
)
_LABEL_ONLY_LINE_RE = re.compile(r"^(?P<indent>\s*)(?P<name>\S+)\s*$")
_ERRORS_RE = re.compile(r"^\s*errors:\s*(?P<errors>.+?)\s*$")
_SECTION_RE = re.compile(rf"^{re.escape(SECTION_PREFIX)}\s+(?P<name>[a-zA-Z0-9_]+)\s*$")
_BLKID_LINE_RE = re.compile(r'^(?P<device>/\S+):\s*(?P<attrs>.*)$')
_BLKID_ATTR_RE = re.compile(r'([A-Z0-9_]+)="([^"]*)"')

_INT_FIELDS = {
    "size",
    "allocated",
    "free",
    "checkpoint",
    "fragmentation",
    "capacity",
    "used",
    "avail",
    "refer",
    "volsize",
    "volblocksize",
    "recordsize",
    "logicalused",
    "logicalreferenced",
    "written",
    "usedbysnapshots",
    "usedbydataset",
    "usedbychildren",
    "usedbyrefreservation",
    "creation",
}


def parse_lsblk_json(raw_output: str) -> dict[str, Any]:
    """Parse lsblk JSON output as-is and validate the top-level shape."""
    data = json.loads(raw_output)
    if not isinstance(data, dict):
        raise ValueError("lsblk output must be a JSON object")
    return data


def parse_findmnt_json(raw_output: str) -> dict[str, Any]:
    """Parse findmnt JSON output as-is and validate the top-level shape."""
    data = json.loads(raw_output)
    if not isinstance(data, dict):
        raise ValueError("findmnt output must be a JSON object")
    return data


def parse_blkid_output(raw_output: str) -> list[dict[str, Any]]:
    """Parse blkid text output into a list of device metadata dictionaries."""
    devices: list[dict[str, Any]] = []
    for line in raw_output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = _BLKID_LINE_RE.match(stripped)
        if not match:
            continue
        attrs = {key.lower(): value for key, value in _BLKID_ATTR_RE.findall(match.group("attrs"))}
        devices.append({"device": match.group("device"), **attrs})
    return devices


def parse_disk_by_id_output(raw_output: str) -> list[dict[str, Any]]:
    """Parse tab-separated by-id output into alias -> device mappings."""
    entries: list[dict[str, Any]] = []
    for line in raw_output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split("\t")
        if len(parts) != 2:
            continue
        alias, target = parts
        entries.append(
            {
                "id": alias,
                "path": target if target.startswith("/dev/") else f"/dev/{target}",
            }
        )
    return entries


def parse_zpool_status(raw_output: str) -> dict[str, Any]:
    """Parse the first zpool status block for backward-compatible callers."""
    statuses = parse_zpool_statuses(raw_output)
    if not statuses:
        return {"pool": None, "state": None, "scan": None, "config": [], "errors": None}
    return next(iter(statuses.values()))


def parse_zpool_statuses(raw_output: str) -> dict[str, dict[str, Any]]:
    """Parse one or more zpool status blocks into a pool-name map."""
    lines = raw_output.splitlines()
    statuses: dict[str, dict[str, Any]] = {}
    result: dict[str, Any] | None = None
    in_config = False
    stack: list[tuple[int, dict[str, Any]]] = []
    multiline_key: str | None = None

    def commit_current() -> None:
        nonlocal result
        nonlocal multiline_key
        if result is None:
            return
        result["config"] = _normalize_top_level_topology(
            result.get("config", []),
            str(result.get("pool") or ""),
        )
        pool_name = result.get("pool")
        if pool_name:
            statuses[str(pool_name)] = result
        result = None
        multiline_key = None

    for line in lines:
        if match := _POOL_HEADER_RE.match(line):
            commit_current()
            result = {
                "pool": match.group("name"),
                "state": None,
                "scan": None,
                "expand": None,
                "config": [],
                "errors": None,
            }
            in_config = False
            stack.clear()
            multiline_key = None
            continue
        if result is None:
            continue
        if match := _STATE_RE.match(line):
            result["state"] = match.group("state")
            multiline_key = None
            continue
        if match := _SCAN_RE.match(line):
            result["scan"] = match.group("scan")
            multiline_key = "scan"
            continue
        if match := _EXPAND_RE.match(line):
            result["expand"] = match.group("expand")
            multiline_key = "expand"
            continue
        if (
            not in_config
            and multiline_key
            and line.startswith(" ")
            and line.strip()
            and not line.lstrip().startswith("errors:")
            and not _CONFIG_HEADER_RE.match(line)
        ):
            existing = str(result.get(multiline_key) or "").strip()
            addition = line.strip()
            result[multiline_key] = f"{existing}\n{addition}" if existing else addition
            continue
        if _CONFIG_HEADER_RE.match(line):
            in_config = True
            stack.clear()
            multiline_key = None
            continue
        if in_config and (not line.strip() or line.strip() == "config:"):
            continue
        if in_config and (match := _DEVICE_LINE_RE.match(line)):
            _append_config_node(
                result=result,
                stack=stack,
                node={
                    "name": match.group("name"),
                    "state": match.group("state"),
                    "read": int(match.group("read")),
                    "write": int(match.group("write")),
                    "cksum": int(match.group("cksum")),
                    "notes": (match.group("notes") or "").strip() or None,
                    "children": [],
                },
                indent=len(match.group("indent")),
            )
            continue
        if in_config and (match := _STATE_ONLY_LINE_RE.match(line)):
            if str(match.group("name") or "").lower() == "errors:":
                # Fall through so _ERRORS_RE can handle this line.
                pass
            else:
                _append_config_node(
                    result=result,
                    stack=stack,
                    node={
                        "name": match.group("name"),
                        "state": match.group("state"),
                        "read": None,
                        "write": None,
                        "cksum": None,
                        "notes": (match.group("notes") or "").strip() or None,
                        "children": [],
                    },
                    indent=len(match.group("indent")),
                )
                continue
        if in_config and (match := _LABEL_ONLY_LINE_RE.match(line)):
            lowered = str(match.group("name") or "").lower()
            if lowered in {"config:", "name", "errors:"}:
                continue
            _append_config_node(
                result=result,
                stack=stack,
                node={
                    "name": match.group("name"),
                    "state": None,
                    "read": None,
                    "write": None,
                    "cksum": None,
                    "notes": None,
                    "children": [],
                },
                indent=len(match.group("indent")),
            )
            continue
        if match := _ERRORS_RE.match(line):
            result["errors"] = match.group("errors")
            in_config = False
            multiline_key = None
            commit_current()

    commit_current()
    return statuses


def parse_sectioned_output(raw_output: str) -> dict[str, str]:
    """Split a combined command output into named sections."""
    sections: dict[str, list[str]] = {}
    current_name: str | None = None

    for line in raw_output.splitlines():
        if match := _SECTION_RE.match(line):
            current_name = match.group("name")
            sections[current_name] = []
            continue
        if current_name is not None:
            sections[current_name].append(line)

    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def _append_config_node(
    *,
    result: dict[str, Any],
    stack: list[tuple[int, dict[str, Any]]],
    node: dict[str, Any],
    indent: int,
) -> None:
    # zpool status uses indentation to describe the vdev hierarchy.
    while stack and stack[-1][0] >= indent:
        stack.pop()

    if stack:
        stack[-1][1]["children"].append(node)
    else:
        result["config"].append(node)

    stack.append((indent, node))


def _normalize_top_level_topology(config: list[dict[str, Any]], pool_name: str) -> list[dict[str, Any]]:
    if not config or not pool_name:
        return config
    root_index = next((index for index, node in enumerate(config) if str(node.get("name") or "") == pool_name), None)
    if root_index is None:
        return config

    root = config[root_index]
    siblings = [node for index, node in enumerate(config) if index != root_index]
    if siblings:
        root["children"] = [*(root.get("children") or []), *siblings]
    return [root]


def parse_tsv_lines(raw_output: str, columns: list[str]) -> list[dict[str, Any]]:
    """Parse tab-separated command output into typed dictionaries."""
    rows: list[dict[str, Any]] = []
    for line in raw_output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split("\t")
        if len(parts) != len(columns):
            raise ValueError(f"Expected {len(columns)} columns, got {len(parts)} for line: {line}")
        row = {column: _coerce_value(column, value) for column, value in zip(columns, parts, strict=True)}
        rows.append(row)
    return rows


def parse_zpool_list(raw_output: str) -> list[dict[str, Any]]:
    columns = [
        "name",
        "size",
        "allocated",
        "free",
        "checkpoint",
        "fragmentation",
        "capacity",
        "dedupratio",
        "health",
        "altroot",
    ]
    return parse_tsv_lines(raw_output, columns)


def parse_zpool_get(raw_output: str) -> dict[str, dict[str, dict[str, Any]]]:
    """Group zpool properties by pool name and property name."""
    rows = parse_tsv_lines(raw_output, ["name", "property", "value", "source"])
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        name = str(row["name"])
        prop = str(row["property"])
        grouped.setdefault(name, {})[prop] = {"value": row["value"], "source": row["source"]}
    return grouped


def parse_zfs_list(raw_output: str) -> list[dict[str, Any]]:
    columns = [
        "name",
        "type",
        "used",
        "avail",
        "refer",
        "mountpoint",
        "compression",
        "volsize",
        "volblocksize",
        "recordsize",
        "readonly",
        "logicalused",
        "logicalreferenced",
        "written",
        "usedbysnapshots",
        "usedbydataset",
        "usedbychildren",
        "usedbyrefreservation",
        "creation",
    ]
    return parse_tsv_lines(raw_output, columns)


def parse_zfs_get(raw_output: str) -> dict[str, dict[str, dict[str, Any]]]:
    """Group dataset properties by dataset name and property name."""
    rows = parse_tsv_lines(raw_output, ["name", "property", "value", "source"])
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        name = str(row["name"])
        prop = str(row["property"])
        grouped.setdefault(name, {})[prop] = {"value": row["value"], "source": row["source"]}
    return grouped


def parse_disk_overview(raw_output: str) -> dict[str, Any]:
    """Parse the aggregated disk overview command into structured sections."""
    sections = parse_sectioned_output(raw_output)
    return {
        "lsblk": parse_lsblk_json(sections["lsblk_json"]),
        "findmnt": parse_findmnt_json(sections["findmnt_json"]),
        "blkid": parse_blkid_output(sections["blkid"]),
        "by_id": parse_disk_by_id_output(sections.get("disk_by_id", "")),
    }


def parse_zpool_overview(raw_output: str) -> dict[str, Any]:
    """Parse the aggregated zpool overview command into structured sections."""
    sections = parse_sectioned_output(raw_output)
    status_by_pool = parse_zpool_statuses(sections["zpool_status"])
    return {
        "status": next(
            iter(status_by_pool.values()),
            {"pool": None, "state": None, "scan": None, "config": [], "errors": None},
        ),
        "status_by_pool": status_by_pool,
        "pools": parse_zpool_list(sections["zpool_list"]),
        "properties": parse_zpool_get(sections["zpool_get"]),
    }


def parse_zpool_core(raw_output: str) -> dict[str, Any]:
    sections = parse_sectioned_output(raw_output)
    status_by_pool = parse_zpool_statuses(sections["zpool_status"])
    return {
        "status": next(
            iter(status_by_pool.values()),
            {"pool": None, "state": None, "scan": None, "config": [], "errors": None},
        ),
        "status_by_pool": status_by_pool,
        "pools": parse_zpool_list(sections["zpool_list"]),
    }


def parse_zpool_properties(raw_output: str) -> dict[str, Any]:
    return {"properties": parse_zpool_get(raw_output)}


def parse_dataset_overview(raw_output: str) -> dict[str, Any]:
    """Parse the aggregated dataset overview command into structured sections."""
    sections = parse_sectioned_output(raw_output)
    return {
        "datasets": parse_zfs_list(sections["zfs_list"]),
        "properties": parse_zfs_get(sections["zfs_get"]),
    }


def parse_dataset_core(raw_output: str) -> dict[str, Any]:
    sections = parse_sectioned_output(raw_output)
    return {"datasets": parse_zfs_list(sections["zfs_list"])}


def parse_dataset_properties(raw_output: str) -> dict[str, Any]:
    return {"properties": parse_zfs_get(raw_output)}


# ── SMART parsers ──────────────────────────────────────────────────


def _normalize_smart_protocol(protocol: str | None) -> str | None:
    """Normalize smartctl protocol strings for display."""
    if protocol is None:
        return None
    p = protocol.lower().strip()
    # "sat" = SCSI ATA Translation (common for SATA disks behind a SAT layer)
    if p in ("sat", "sata"):
        return "sata"
    if p in ("ata", "pata"):
        return "ata"
    if p == "nvme":
        return "nvme"
    if p == "scsi":
        return "scsi"
    return protocol


def parse_smartctl_output(raw_text: str, device_name: str) -> dict[str, Any]:
    """Parse a single smartctl JSON section into a normalized dict.

    Handles both ATA (ata_smart_attributes.table) and NVMe
    (nvme_smart_health_information_log) output shapes.
    """
    raw_text = raw_text.strip()
    if not raw_text:
        return {"device_path": device_name, "raw_data_available": False}

    try:
        data = json.loads(raw_text)
    except (json.JSONDecodeError, ValueError):
        return {"device_path": device_name, "raw_data_available": False, "error": "Failed to parse smartctl JSON output"}

    if not isinstance(data, dict):
        return {"device_path": device_name, "raw_data_available": False, "error": "smartctl output was not a JSON object"}

    exit_status = data.get("smartctl", {}).get("exit_status", 0)
    if exit_status == 1 and not data.get("device"):
        return {"device_path": device_name, "raw_data_available": False, "error": "smartctl failed — is smartmontools installed?"}
    if exit_status == 2 and not data.get("device"):
        return {"device_path": device_name, "raw_data_available": False, "error": "smartctl failed to open device (permission or missing device)"}

    device_info = data.get("device", {}) or {}
    result: dict[str, Any] = {
        "device_path": device_info.get("name") or device_name,
        "model_name": data.get("model_name") or data.get("model_family") or None,
        "serial_number": data.get("serial_number") or None,
        "firmware_version": data.get("firmware_version") or None,
        "protocol": _normalize_smart_protocol(device_info.get("type")),
        "smart_supported": bool(data.get("smart_support", {}).get("supported", False) if isinstance(data.get("smart_support"), dict) else False),
        "smart_enabled": bool(data.get("smart_support", {}).get("enabled", False) if isinstance(data.get("smart_support"), dict) else False),
        "smart_status_passed": None,
        "temperature": None,
        "power_on_hours": None,
        "attributes": [],
        "raw_data_available": True,
        "error": None,
    }

    # Determine the protocol for parsing logic
    protocol = result["protocol"]

    # SMART overall status — common to ATA and NVMe
    smart_status = data.get("smart_status")
    if isinstance(smart_status, dict):
        result["smart_status_passed"] = bool(smart_status.get("passed", False))

    # Temperature — common
    temp = data.get("temperature")
    if isinstance(temp, dict):
        result["temperature"] = temp.get("current")
    elif isinstance(temp, (int, float)):
        result["temperature"] = temp

    # Power-on time — common
    pot = data.get("power_on_time")
    if isinstance(pot, dict):
        result["power_on_hours"] = pot.get("hours")

    # ATA-specific attributes
    if protocol in ("ata", "sata", None) or isinstance(data.get("ata_smart_attributes"), dict):
        ata_attrs = data.get("ata_smart_attributes", {}) if isinstance(data.get("ata_smart_attributes"), dict) else {}
        attr_table = ata_attrs.get("table", []) if isinstance(ata_attrs.get("table"), list) else []
        result["attributes"] = [
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "value": item.get("value"),
                "worst": item.get("worst"),
                "threshold": item.get("threshold"),
                "raw": _coerce_smart_raw_value(item.get("raw", {}).get("value") if isinstance(item.get("raw"), dict) else item.get("raw")),
                "when_failed": item.get("when_failed"),
            }
            for item in attr_table
            if isinstance(item, dict) and item.get("name")
        ]

    # NVMe-specific health log
    nvme_log = data.get("nvme_smart_health_information_log")
    if isinstance(nvme_log, dict):
        result["temperature"] = nvme_log.get("temperature") if nvme_log.get("temperature") is not None else result["temperature"]
        result["power_on_hours"] = nvme_log.get("power_on_hours") if nvme_log.get("power_on_hours") is not None else result["power_on_hours"]
        # Build a synthetic attribute list for NVMe controller health
        nvme_fields = [
            ("critical_warning", "critical_warning", nvme_log.get("critical_warning")),
            ("media_errors", "media_errors", nvme_log.get("media_errors")),
            ("num_err_log_entries", "num_err_log_entries", nvme_log.get("num_err_log_entries")),
            ("percentage_used", "percentage_used", nvme_log.get("percentage_used")),
            ("available_spare", "available_spare", nvme_log.get("available_spare")),
            ("available_spare_threshold", "available_spare_threshold", nvme_log.get("available_spare_threshold")),
            ("controller_busy_time", "controller_busy_time", nvme_log.get("controller_busy_time")),
            ("warning_temp_time", "warning_temp_time", nvme_log.get("warning_temp_time")),
            ("critical_comp_time", "critical_comp_time", nvme_log.get("critical_comp_time")),
        ]
        for attr_name, label, attr_value in nvme_fields:
            if attr_value is not None:
                result["attributes"].append({
                    "id": None,
                    "name": label,
                    "value": attr_value if isinstance(attr_value, int) else int(str(attr_value)) if attr_value else None,
                    "worst": None,
                    "threshold": None,
                    "raw": str(attr_value) if attr_value is not None else None,
                    "when_failed": None,
                })

    return result


def parse_smart_info(raw_output: str) -> dict[str, Any]:
    """Parse SMART-info sectioned output into a map keyed by device path."""
    sections = parse_sectioned_output(raw_output)
    devices: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    unhealthy_count = 0
    unsupported_count = 0

    for section_name, section_text in sections.items():
        if not section_name.startswith("smart_"):
            continue
        device_name = f"/dev/{section_name.removeprefix('smart_')}"
        parsed = parse_smartctl_output(section_text, device_name)
        dev_path = parsed.get("device_path") or device_name
        devices[dev_path] = parsed

        if parsed.get("error"):
            errors.append(f"{dev_path}: {parsed['error']}")
        if parsed.get("raw_data_available") and parsed.get("smart_status_passed") is False:
            unhealthy_count += 1
        if not parsed.get("raw_data_available") or not parsed.get("smart_supported"):
            unsupported_count += 1

    # If a device was skipped entirely (lsblk reported it but smartctl didn't
    # produce a section), leave it absent from the map — the frontend will show
    # "no data" for its device path.
    return {
        "devices": devices,
        "collected_at": None,  # Timestamp filled by the caller
        "unhealthy_count": unhealthy_count,
        "unsupported_count": unsupported_count,
        "total_queried": len(devices),
        "error": "; ".join(errors) if errors else None,
    }


def _coerce_smart_raw_value(value: Any) -> int | str | None:
    """Coerce a SMART raw attribute value to int when possible."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        str_val = str(value).strip()
        return str_val if str_val else None


def parse_command_output(command: str, raw_output: str) -> dict[str, Any]:
    """Dispatch raw command output to the matching parser."""
    normalized = command.strip()
    lowered = normalized.lower()

    if normalized == DISK_OVERVIEW:
        return parse_disk_overview(raw_output)
    if normalized == ZPOOL_CORE:
        return parse_zpool_core(raw_output)
    if normalized == ZPOOL_PROPERTIES:
        return parse_zpool_properties(raw_output)
    if normalized == ZPOOL_OVERVIEW:
        return parse_zpool_overview(raw_output)
    if normalized == ZFS_DATASET_CORE:
        return parse_dataset_core(raw_output)
    if normalized == ZFS_DATASET_PROPERTIES:
        return parse_dataset_properties(raw_output)
    if normalized == ZFS_DATASET_OVERVIEW:
        return parse_dataset_overview(raw_output)
    if normalized == SMART_INFO:
        return parse_smart_info(raw_output)
    if normalized == LSBLK_JSON or (lowered.startswith("lsblk") and "--json" in lowered):
        return parse_lsblk_json(raw_output)
    if normalized == ZPOOL_STATUS or lowered.startswith("zpool status"):
        return parse_zpool_status(raw_output)
    raise ValueError(f"Unsupported command for parser: {command}")


def _coerce_value(column: str, value: str) -> Any:
    # ZFS tools often use "-" as a placeholder for "not applicable".
    if value == "-":
        return None
    if column in _INT_FIELDS:
        try:
            return int(value)
        except ValueError:
            return value
    return value
