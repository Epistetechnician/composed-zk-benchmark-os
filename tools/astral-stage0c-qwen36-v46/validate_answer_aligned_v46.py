#!/usr/bin/env python3
"""Independently validate aggregate-only V46 fit/tune output.

State slice: astral-stage0c-qwen36-answer-aligned-causal-target-v46.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import protocol_v46 as protocol


V45_SOURCE = Path(__file__).resolve().parents[1] / "astral-stage0c-qwen36-v45"
sys.path.insert(0, str(V45_SOURCE))
import validate_canonical_task_v45 as validator_engine  # noqa: E402


def validate(measurement_root: Path, panel_root: Path, qualification_root: Path, model_root: Path, repository_root: Path) -> dict[str, Any]:
    validator_engine.protocol = protocol
    receipt = validator_engine.validate(measurement_root, panel_root, qualification_root, model_root, repository_root)
    result_path = measurement_root.resolve() / "canonical-task-result.json"
    try:
        result = protocol.read_json(result_path)
        sources = result.get("source_sha256", {})
        if sources.get("wrapper") != protocol.sha256_file(Path(__file__).with_name("run_answer_aligned_v46.py")):
            receipt["valid"] = False
            receipt.setdefault("errors", []).append("wrapper_source_digest_binding")
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        receipt["valid"] = False
        receipt.setdefault("errors", []).append("result_wrapper_source_read_failure")
    receipt["protocol"] = protocol.PROTOCOL_ID
    receipt["state_slice"] = protocol.STATE_SLICE
    receipt["claim_ceiling"] = "LocalDevelopmentV46AnswerAlignedValidated" if receipt["valid"] else "LocalDevelopmentV46ValidationFailed"
    receipt["classification"] = "AnswerAlignedValidated" if receipt["valid"] else "AnswerAlignedInvalid"
    receipt["independent_validation"] = True
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("measurement_root", type=Path)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--write-receipt", action="store_true")
    args = parser.parse_args(argv)
    receipt = validate(args.measurement_root, args.panel_root, args.qualification_root, args.model, args.repository_root.resolve())
    if args.write_receipt:
        protocol.write_json(args.measurement_root.resolve() / "validator-receipt.json", receipt)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["valid"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
