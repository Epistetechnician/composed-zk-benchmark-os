from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("astral_v31_corrected", HERE / "v31.py")
assert SPEC is not None and SPEC.loader is not None
V31 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = V31
SPEC.loader.exec_module(V31)


def corrected_report(root: Path) -> dict[str, object]:
    original = V31.V30.read(root / "astral-validation-report.json")
    result = V31.V30.read(root / "model-result.json")
    if original.get("valid") is not True or original.get("errors") != []:
        raise ValueError("V31R2 original validation was not clean")
    phases = result["phases"]
    post, reload = phases["post_direct"], phases["reload_direct"]
    delta = max(abs(a["candidate_scores"][word] - b["candidate_scores"][word]) for a, b in zip(post, reload, strict=True) for word in a["candidates"])
    stripped = lambda rows: [{key: value for key, value in row.items() if key != "phase"} for row in rows]
    exact = stripped(phases["pre_direct"]) == stripped(phases["no_update_direct"])
    summary = V31.summarize(phases, delta, exact)
    if summary["status"] != "TinyAcquisitionBlocked" or not all(summary["gates"][key] is False for key in ("post_direct", "improvement", "paraphrase", "protected")):
        raise ValueError("V31R2 correction unexpectedly changes the decisive negative")
    return {
        "version": "astral.v31r2_corrected_validation_report.v1",
        "valid": True, "status": summary["status"], "errors": [],
        "original_report_sha256": V31.V30.sha256_file(root / "astral-validation-report.json"),
        "model_result_sha256": result["result_sha256"], "corrected_summary": summary,
        "correction": "ignore phase label only when comparing no-update replay rows",
        "outcome_changed": False, "model_execution": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply the read-only V31R2 replay-equality correction")
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = corrected_report(args.artifact_root.resolve())
    encoded = (json.dumps(report, allow_nan=False, indent=2, sort_keys=True) + "\n").encode()
    with args.output.open("xb") as handle:
        handle.write(encoded); handle.flush(); os.fsync(handle.fileno())
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
