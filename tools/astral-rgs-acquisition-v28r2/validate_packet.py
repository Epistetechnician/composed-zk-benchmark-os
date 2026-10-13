from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import v28r2 as core  # noqa: E402


def _new_absolute_path(path: Path) -> bool:
    return (
        path.is_absolute()
        and not path.exists()
        and not path.is_symlink()
        and path.parent.is_dir()
        and not path.parent.is_symlink()
    )


def _has_symlink_component(path: Path) -> bool:
    return any(candidate.is_symlink() for candidate in (path, *path.parents))


def _write_exclusive(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise OSError("zero-progress report write")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    directory_descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory_descriptor)
    finally:
        os.close(directory_descriptor)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one repository-external V28R2 baseline packet."
    )
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--r1-fingerprint", type=Path, required=True)
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if not _new_absolute_path(args.output):
        parser.exit(1, "error: output must be a new absolute path\n")
    try:
        if (
            not args.bundle_root.is_absolute()
            or not args.bundle_root.is_dir()
            or _has_symlink_component(args.bundle_root)
        ):
            raise ValueError("bundle root must be an absolute real directory")
        expected_packet_path = args.bundle_root / "acquisition-packet.json"
        if (
            args.packet != expected_packet_path
            or not args.packet.is_absolute()
            or not args.packet.is_file()
            or _has_symlink_component(args.packet)
        ):
            raise ValueError(
                "packet must be the real bundle-root acquisition-packet.json"
            )
        protocol = core.load_json_strict(args.protocol)
        fingerprint = core.load_json_strict(args.r1_fingerprint)
        packet = core.load_json_strict(args.packet)
        report = core.validate_packet(
            packet,
            protocol,
            fingerprint,
            args.bundle_root,
            args.packet,
        )
        _write_exclusive(args.output, report)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(1, f"error: {error}\n")
    status = report["status"]
    print(f"status={status}")
    if status == "NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun":
        return 0
    if status == "CorpusNotNovel":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
