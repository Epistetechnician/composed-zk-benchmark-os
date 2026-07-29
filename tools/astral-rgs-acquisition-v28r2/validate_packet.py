from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import v28r2  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Independently validate one immutable V28R2 novelty packet."
    )
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--retired-r1-fingerprint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    fingerprint = json.loads(args.retired_r1_fingerprint.read_text(encoding="utf-8"))
    report = v28r2.validate_packet(packet, fingerprint)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, sort_keys=True)
            handle.write("\n")
    except FileExistsError:
        parser.error("output already exists")
    print(f"status={report['status']}")
    print(f"report_sha256={report['report_sha256']}")
    return 0 if report["status"] == "NoveltyPacketCandidate" else 2 if report["status"] == "CorpusNotNovel" else 1


if __name__ == "__main__":
    raise SystemExit(main())
