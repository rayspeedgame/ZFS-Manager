from __future__ import annotations

import json
import re
from typing import Any

from app.ssh.commands import (
    DISK_OVERVIEW,
    LSBLK_JSON,
    SECTION_PREFIX,
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
_CONFIG_HEADER_RE = re.compile(r"^\s*NAME\s+STATE\s+READ\s+WRITE\s+CKSUM\s*$")
_DEVICE_LINE_RE = re.compile(
    r"^(?P<indent>\s*)(?P<name>\S+)\s+"
    r"(?P<state>\S+)\s+"
    r"(?P<read>\d+)\s+"
    r"(?P<write>\d+)\s+"
    r"(?P<cksum>\d+)"
    r"(?:\s+(?P<notes>.*))?$"
)
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


def parse_zpool_status(raw_output: str) -> dict[str, Any]:
    """Parse the human-readable zpool topology into a nested tree."""
    lines = raw_output.splitlines()
    result: dict[str, Any] = {"pool": None, "state": None, "scan": None, "config": [], "errors": None}
    in_config = False
    stack: list[tuple[int, dict[str, Any]]] = []

    for line in lines:
        if match := _POOL_HEADER_RE.match(line):
            result["pool"] = match.group("name")
            continue
        if match := _STATE_RE.match(line):
            result["state"] = match.group("state")
            continue
        if match := _SCAN_RE.match(line):
            result["scan"] = match.group("scan")
            continue
        if _CONFIG_HEADER_RE.match(line):
            in_config = True
            stack.clear()
            continue
        if in_config and (not line.strip() or line.strip() == "config:"):
            continue
        if in_config and (match := _DEVICE_LINE_RE.match(line)):
            node = {
                "name": match.group("name"),
                "state": match.group("state"),
                "read": int(match.group("read")),
                "write": int(match.group("write")),
                "cksum": int(match.group("cksum")),
                "notes": (match.group("notes") or "").strip() or None,
                "children": [],
            }
            indent = len(match.group("indent"))

            # zpool status uses indentation to describe the vdev hierarchy.
            while stack and stack[-1][0] >= indent:
                stack.pop()

            if stack:
                stack[-1][1]["children"].append(node)
            else:
                result["config"].append(node)

            stack.append((indent, node))
            continue
        if match := _ERRORS_RE.match(line):
            result["errors"] = match.group("errors")
            in_config = False

    return result


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
    }


def parse_zpool_overview(raw_output: str) -> dict[str, Any]:
    """Parse the aggregated zpool overview command into structured sections."""
    sections = parse_sectioned_output(raw_output)
    return {
        "status": parse_zpool_status(sections["zpool_status"]),
        "pools": parse_zpool_list(sections["zpool_list"]),
        "properties": parse_zpool_get(sections["zpool_get"]),
    }


def parse_zpool_core(raw_output: str) -> dict[str, Any]:
    sections = parse_sectioned_output(raw_output)
    return {
        "status": parse_zpool_status(sections["zpool_status"]),
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
