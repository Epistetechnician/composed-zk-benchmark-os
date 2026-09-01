"""Run the all-baseline matrix on deterministic real-derived task streams.

State slice: ``oaklab-experience-learning-benchmark-v2``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .custody import load_custodied_jsonl
from .derive_real_streams_v1 import validate_manifest
from .real_benchmark_v1 import _digest, run_dataset


def run(root: Path) -> dict:
    custody = validate_manifest(root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    outputs = {}
    for record in manifest["datasets"]:
        rows, _ = load_custodied_jsonl(str(root / record["derived_file"]), record["kind"], record["derived_sha256"])
        result = run_dataset(rows, record["name"])
        result["custody"] = {"manifest_sha256": custody["manifest_sha256"], "derived_sha256": record["derived_sha256"], "rows": len(rows)}
        result["result_digest"] = _digest({key: value for key, value in result.items() if key != "result_digest"})
        outputs[record["name"]] = result
    payload = {"schema_version": "oaklab.experience-learning.real-derived-matrix.v1",
               "state_slice": "oaklab-experience-learning-benchmark-v2",
               "custody": custody, "datasets": outputs}
    payload["result_digest"] = _digest(payload)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(result["result_digest"])


if __name__ == "__main__":
    main()
