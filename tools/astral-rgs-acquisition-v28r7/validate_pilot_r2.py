from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from v28r7 import validate


def main() -> int:
    started_ns = time.time_ns()
    parser = argparse.ArgumentParser(description="Run the corrected read-only V28R7 R2 validator")
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--process-output", type=Path, required=True)
    args = parser.parse_args()
    result = validate(args.artifact_root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    returncode = 0 if result["valid"] else 1
    process = {
        "version": "astral.rgs_acquisition_v28r7.validation_process.r2",
        "argv": sys.argv, "started_ns": started_ns, "finished_ns": time.time_ns(),
        "returncode": returncode, "model_execution": False,
        "artifact_mutation": "late_validation_files_only",
    }
    with args.process_output.open("x", encoding="utf-8") as handle:
        json.dump(process, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
