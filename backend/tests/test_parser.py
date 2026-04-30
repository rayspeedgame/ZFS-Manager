from __future__ import annotations

import json
from pathlib import Path

from app.ssh.commands import DISK_OVERVIEW, ZFS_DATASET_OVERVIEW, ZPOOL_OVERVIEW
from app.ssh.parser import (
    parse_blkid_output,
    parse_command_output,
    parse_dataset_overview,
    parse_disk_overview,
    parse_lsblk_json,
    parse_zpool_overview,
    parse_zpool_status,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_lsblk_json() -> None:
    raw = (FIXTURES_DIR / "lsblk_sample.json").read_text(encoding="utf-8")
    parsed = parse_lsblk_json(raw)

    assert parsed["blockdevices"][0]["name"] == "sda"
    assert parsed["blockdevices"][0]["children"][0]["mountpoints"] == ["/tank"]


def test_parse_blkid_output() -> None:
    raw = (FIXTURES_DIR / "blkid_sample.txt").read_text(encoding="utf-8")
    parsed = parse_blkid_output(raw)

    assert parsed[0]["device"] == "/dev/sda1"
    assert parsed[0]["type"] == "zfs_member"
    assert parsed[1]["label"] == "EFI"


def test_parse_zpool_status() -> None:
    raw = (FIXTURES_DIR / "zpool_status_sample.txt").read_text(encoding="utf-8")
    parsed = parse_zpool_status(raw)

    assert parsed["pool"] == "tank"
    assert parsed["state"] == "ONLINE"
    assert parsed["config"][0]["name"] == "tank"
    assert parsed["config"][0]["children"][0]["name"] == "mirror-0"
    assert parsed["config"][0]["children"][0]["children"][1]["name"] == "sdb"
    assert parsed["errors"] == "No known data errors"


def test_parse_disk_overview() -> None:
    raw = (FIXTURES_DIR / "disk_overview_sample.txt").read_text(encoding="utf-8")
    parsed = parse_disk_overview(raw)

    assert parsed["lsblk"]["blockdevices"][0]["name"] == "sda"
    assert parsed["findmnt"]["filesystems"][0]["target"] == "/tank"
    assert parsed["blkid"][0]["uuid"] == "1111-2222"


def test_parse_zpool_overview() -> None:
    raw = (FIXTURES_DIR / "zpool_overview_sample.txt").read_text(encoding="utf-8")
    parsed = parse_zpool_overview(raw)

    assert parsed["status"]["pool"] == "tank"
    assert parsed["pools"][0]["size"] == 1999844147200
    assert parsed["properties"]["tank"]["ashift"]["value"] == "12"


def test_parse_dataset_overview() -> None:
    raw = (FIXTURES_DIR / "dataset_overview_sample.txt").read_text(encoding="utf-8")
    parsed = parse_dataset_overview(raw)

    assert parsed["datasets"][0]["name"] == "tank"
    assert parsed["datasets"][1]["mountpoint"] == "/tank/media"
    assert parsed["properties"]["tank/media"]["compression"]["value"] == "zstd"


def test_parse_command_output_dispatch() -> None:
    disk_raw = (FIXTURES_DIR / "disk_overview_sample.txt").read_text(encoding="utf-8")
    zpool_raw = (FIXTURES_DIR / "zpool_overview_sample.txt").read_text(encoding="utf-8")
    dataset_raw = (FIXTURES_DIR / "dataset_overview_sample.txt").read_text(encoding="utf-8")

    assert "findmnt" in parse_command_output(DISK_OVERVIEW, disk_raw)
    assert "properties" in parse_command_output(ZPOOL_OVERVIEW, zpool_raw)
    assert "datasets" in parse_command_output(ZFS_DATASET_OVERVIEW, dataset_raw)


def test_fixture_lsblk_is_valid_json() -> None:
    raw = (FIXTURES_DIR / "lsblk_sample.json").read_text(encoding="utf-8")
    assert isinstance(json.loads(raw), dict)
