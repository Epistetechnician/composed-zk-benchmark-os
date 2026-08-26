#!/usr/bin/env python3
"""Independent validator for V27 second-model replication artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.continual_learning import validate_routed_adapter_bank_candidate_v26 as v26


STATE_SLICE = "continual-learning-replication-task-routed-adapter-bank-v27"
CLAIM_CEILING = "LocalDevelopmentTaskRoutedAdapterBankReplication"
EXCLUDED_MODEL = "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def validate(root: Path) -> dict:
    config = json.loads((root / "config.json").read_text(encoding="utf8"))
    result = json.loads((root / "result.json").read_text(encoding="utf8"))
    model = Path(config.get("model", "")).resolve()
    if config.get("state_slice") != STATE_SLICE or result.get("state_slice") != STATE_SLICE:
        raise ValueError("V27 state slice drift")
    if result.get("claim_ceiling") != CLAIM_CEILING:
        raise ValueError("V27 claim ceiling drift")
    if config.get("candidate_claim_ceiling") != CLAIM_CEILING:
        raise ValueError("V27 candidate claim ceiling drift")
    if str(model) == str(Path(EXCLUDED_MODEL).resolve()):
        raise ValueError("V27 reused the V26 parent model")
    for key in ("runtime_preflight_manifest_sha256", "runtime_preflight_receipt_sha256"):
        if not SHA256.fullmatch(config.get(key, "")):
            raise ValueError(f"invalid runtime preflight digest: {key}")
    if result.get("breakthrough_claim_eligible") is not False or result.get("production_claim_eligible") is not False:
        raise ValueError("V27 claim boundary drift")

    # Delegate the frozen V26 structural checks after rebinding only the
    # model and state constants in this independent validator process.
    v26.MODEL_DEFAULT = str(model)
    v26.STATE_SLICE = STATE_SLICE
    validated = v26.validate(root)
    validated.update(
        {
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "runtime_preflight_manifest_sha256": config["runtime_preflight_manifest_sha256"],
        }
    )
    return validated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(args.root.resolve()), sort_keys=True))
    except Exception as exc:
        print(json.dumps({"valid": False, "reason": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
