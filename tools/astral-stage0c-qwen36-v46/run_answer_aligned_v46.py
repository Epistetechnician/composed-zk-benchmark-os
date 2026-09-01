#!/usr/bin/env python3
"""Run V46 fit/tune prediction locking with assessment closed.

State slice: astral-stage0c-qwen36-answer-aligned-causal-target-v46.
The only V45 dependency is its already-qualified, generic local execution
kernel. V46 supplies a new protocol, corpus, panel, feature, and custody chain.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np

import protocol_v46 as protocol


V45_SOURCE = Path(__file__).resolve().parents[1] / "astral-stage0c-qwen36-v45"
sys.path.insert(0, str(V45_SOURCE))
import run_canonical_task_v45 as measurement_engine  # noqa: E402


CLAIM_CEILING_NO_CANDIDATE = "LocalDevelopmentV46AnswerAlignedNoCandidate"
CLAIM_CEILING_REVIEW = "LocalDevelopmentV46AnswerAlignedReviewRequired"


def _install_v46_contract() -> None:
    measurement_engine.protocol = protocol
    measurement_engine.CLAIM_CEILING_NO_CANDIDATE = CLAIM_CEILING_NO_CANDIDATE
    measurement_engine.CLAIM_CEILING_REVIEW = CLAIM_CEILING_REVIEW


def _answer_feature(head: Any, response_ids: dict[str, int], mx: Any):
    def feature(vector_pair: dict[str, np.ndarray]) -> np.ndarray:
        ordinary = vector_pair["ordinary"].astype(np.float32, copy=False)
        counterfactual = vector_pair["counterfactual"].astype(np.float32, copy=False)
        difference = mx.array((counterfactual - ordinary)[None, :])
        response_logits = head(difference)
        mx.eval(response_logits)
        value = response_logits[0, response_ids["A"]] - response_logits[0, response_ids["B"]]
        mx.eval(value)
        scalar = float(np.asarray(value, dtype=np.float64).item())
        if not np.isfinite(scalar):
            raise protocol.ProtocolError("non-finite response-margin feature")
        return np.asarray([scalar], dtype=np.float64)

    return feature


def run(panel_root: Path, qualification_root: Path, model_root: Path, output_root: Path, repository_root: Path) -> Path:
    _install_v46_contract()
    import mlx.core as mx
    from mlx_lm import load

    model, tokenizer = load(str(model_root.resolve()), lazy=True)
    response_ids: dict[str, int] = {}
    for label, token in protocol.RESPONSE_TOKENS.items():
        encoded = list(tokenizer.encode(token))
        if len(encoded) != 1:
            raise protocol.ProtocolError(f"response token is not one tokenizer token: {label}")
        response_ids[label] = int(encoded[0])
    measurement_engine._feature = _answer_feature(model.language_model.lm_head, response_ids, mx)
    root = measurement_engine.run(panel_root, qualification_root, model_root, output_root, repository_root)
    result_path = root / "canonical-task-result.json"
    result = protocol.read_json(result_path)
    if result.get("classification") == "CanonicalTaskNoCandidate":
        result["classification"] = "AnswerAlignedNoCandidate"
        result["claim_ceiling"] = CLAIM_CEILING_NO_CANDIDATE
    elif result.get("classification") == "ReviewRequired":
        result["classification"] = "AnswerAlignedReviewRequired"
        result["claim_ceiling"] = CLAIM_CEILING_REVIEW
    result["source_sha256"]["wrapper"] = protocol.sha256_file(Path(__file__).resolve())
    protocol.write_json(result_path, result)
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel-root", type=Path, required=True)
    parser.add_argument("--qualification-root", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        root = run(args.panel_root, args.qualification_root, args.model, args.output_root, args.repository_root.resolve())
        result = protocol.read_json(root / "canonical-task-result.json")
    except (OSError, ImportError, KeyError, TypeError, ValueError, json.JSONDecodeError, protocol.ProtocolError) as exc:
        print(json.dumps({"valid": False, "error": f"{type(exc).__name__}:{exc}"}, indent=2))
        return 2
    print(json.dumps({"measurement_root": str(root), "classification": result["classification"], "selected_target": result["selected_target"], "valid": True}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
