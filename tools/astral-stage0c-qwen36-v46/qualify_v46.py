#!/usr/bin/env python3
"""Run V46 qualification before any panel-effect measurement.

State slice: astral-stage0c-qwen36-answer-aligned-causal-target-v46.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import protocol_v46 as protocol


V45_SOURCE = Path(__file__).resolve().parents[1] / "astral-stage0c-qwen36-v45"
sys.path.insert(0, str(V45_SOURCE))
import qualify_v45 as qualification_engine  # noqa: E402


DEFAULT_MODEL = Path("/Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit")


def qualify(model_root: Path, output_root: Path, repository_root: Path) -> Path:
    qualification_engine.protocol = protocol
    root = qualification_engine.qualify(model_root, output_root, repository_root)
    result_path = root / "qualification-result.json"
    result = protocol.read_json(result_path)
    result["claim_ceiling"] = "LocalDevelopmentV46InstrumentFeasibilityOnly"
    result["protocol"] = protocol.PROTOCOL_ID
    result["state_slice"] = protocol.STATE_SLICE
    result["qualification_id"] = protocol.QUALIFICATION_ID
    result["runner_source_sha256"] = protocol.sha256_file(Path(__file__).resolve())
    protocol.write_json(result_path, result)
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = qualify(args.model, args.output_root, args.repository_root.resolve())
        result = protocol.read_json(root / "qualification-result.json")
    except (OSError, ImportError, KeyError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    valid = result.get("classification") == "InstrumentFeasibility" and all(result.get("gates", {}).values())
    print(json.dumps({"qualification_root": str(root), "classification": result.get("classification"), "valid": valid}, indent=2))
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
