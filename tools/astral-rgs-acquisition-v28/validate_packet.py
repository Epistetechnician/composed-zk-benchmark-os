from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import v28  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate one V28 acquisition packet without executing a model."
    )
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    report = v28.validate_packet(packet)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError:
        parser.error("output already exists")
    print(f"status={report['status']}")
    print(f"report_sha256={report['report_sha256']}")
    print(f"output={args.output.resolve()}")
    if report["status"] in {
        "NoveltyPacketCandidateUnverifiedAcquisitionArmsNotRun",
        "AcquisitionPacketCandidateUnverified",
    }:
        return 0
    if report["status"] in {
        "CorpusNotNovel",
        "AcquisitionPacketNoCandidateUnverified",
    }:
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
