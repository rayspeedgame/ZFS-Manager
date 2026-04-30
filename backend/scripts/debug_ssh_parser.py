from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.ssh.client import SSHClient, SSHConfig
from app.ssh.commands import resolve_command
from app.ssh.parser import parse_command_output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 1 SSH + parser debug script")
    parser.add_argument("--source", choices=("ssh", "file"), default="file")
    parser.add_argument(
        "--command",
        choices=("lsblk", "zpool", "disk_overview", "zpool_overview", "dataset_overview"),
        default="lsblk",
    )
    parser.add_argument("--input-file", type=Path, help="Read previously captured output from disk")
    parser.add_argument("--save-output", type=Path, help="Save successful raw output for offline parser work")
    parser.add_argument("--host")
    parser.add_argument("--username")
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--password")
    parser.add_argument("--key-file", type=Path)
    parser.add_argument("--known-hosts", default=None)
    return parser
async def load_raw_output(args: argparse.Namespace) -> str:
    if args.source == "file":
        if not args.input_file:
            raise ValueError("--source file requires --input-file")
        return args.input_file.read_text(encoding="utf-8")

    if not args.host or not args.username:
        raise ValueError("--source ssh requires --host and --username")

    config = SSHConfig(
        host=args.host,
        username=args.username,
        port=args.port,
        password=args.password,
        known_hosts=args.known_hosts,
        client_keys=[args.key_file] if args.key_file else None,
    )

    # Keep the debug script thin: it exercises the same SSH client used by the
    # backend code path, so captured samples stay representative.
    async with SSHClient(config) as client:
        raw = await client.run(resolve_command(args.command))
    return raw


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    raw_output = await load_raw_output(args)

    if args.save_output:
        args.save_output.parent.mkdir(parents=True, exist_ok=True)
        args.save_output.write_text(raw_output, encoding="utf-8")

    # Pretty-print JSON so the parsed structure is easy to inspect in a debugger
    # or compare against expected fixture output.
    parsed = parse_command_output(resolve_command(args.command), raw_output)
    print(json.dumps(parsed, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
