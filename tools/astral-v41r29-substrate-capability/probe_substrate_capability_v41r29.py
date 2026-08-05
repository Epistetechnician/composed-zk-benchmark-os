"""V41R29 local substrate-capability boundary probe.

Scoring-only base-model capability measurement. No optimizer, no adapter, no
parameter update. Determines, for each pinned local substrate, whether it can
host a V41R27-style full qualification campaign under the frozen preflight gate
(protected arithmetic exactly 1.0 across all 256 rows, acquisition novelty >= 3
per panel, uniform transformer qkvo architecture).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SURROGATE = HERE.parent / "astral-v41r28-local-surrogate" / "surrogate_v41r28.py"

CONTRACT_SHA256 = "sha256:ddf7f95ea4bf9b109dbdb1b02b87542a2a8ea56fd694f508c0b8647bc716ed4e"
ACQUISITION_SHA256 = "sha256:0459d3c39e37c1a3fb7a8ffdbee1dca214b75b316dab456ab3e8d82dd98d1f92"
PROTECTED_SHA256 = "sha256:83e873627f55df68f62a90d9847a73e5838eccc76fe48fb3c77109b6122b503e"

CLAIM_CEILING = "LocalSubstrateCapabilityBoundaryV41R29"
STATE_SLICE = "V41R29LocalSubstrateCapabilityBoundary"
VERSION = "astral.v41r29_substrate_capability_probe.v1"

SUBSTRATES = [
    {"key": "qwen2.5-0.5b", "kind": "transformer",
     "path": str(Path.home() / ".lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"),
     "model_safetensors_sha256": "ddffab9cbc7bf6dde941c6724841eeca8981fcfa81ca20ff8efff1396326d153",
     "tokenizer_json_sha256": "a8506e7111b80c6d8635951a02eab0f4e1a8e4e5772da83846579e97b16f61bf"},
    {"key": "llama-3.2-1b", "kind": "transformer",
     "path": str(Path.home() / ".lmstudio/models/mlx-community/Llama-3.2-1B-Instruct-4bit"),
     "model_safetensors_sha256": "35e396644bca888eec399f9c0f843ec7fa78b8f8c5e06841661be62b4edf96dd",
     "tokenizer_json_sha256": "6b9e4e7fb171f92fd137b777cc2714bf87d11576700a1dcd7a399e7bbe39537b"},
    {"key": "nemotron-3-nano-4b", "kind": "architecture_check",
     "path": str(Path.home() / ".lmstudio/models/mlx_lm_lora/mesh-brain-nemotron-3-nano-4b"),
     "config_json_sha256": "9df35babecfbe4267ad2714b03c238613c21963704c04577dee1d581b225076f",
     "tokenizer_json_sha256": "623c34567aebb18582765289fbe23d901c62704d6518d71866e0e58db892b5b7"},
]


def _load_surrogate() -> Any:
    spec = importlib.util.spec_from_file_location("surrogate_v41r28", SURROGATE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def architecture_check(substrate: dict[str, Any]) -> dict[str, Any]:
    config = json.loads((Path(substrate["path"]) / "config.json").read_text())
    model_type = config.get("model_type", "")
    hybrid = config.get("hybrid_override_pattern")
    has_mamba = bool(hybrid) or config.get("mamba_head_dim") is not None or \
        config.get("ssm_state_size") is not None
    uniform_qkvo = model_type in ("llama", "qwen2", "mistral") and not has_mamba
    compatible = bool(uniform_qkvo)
    return {"model_type": model_type,
            "hybrid_override_pattern_present": bool(hybrid),
            "mamba_markers_present": bool(has_mamba),
            "uniform_qkvo_attention_stack": uniform_qkvo,
            "architecture_compatible_with_v41r27_lora_protocol": compatible,
            "classification": ("architecture_compatible" if compatible
                               else "architecture_incompatible_hybrid_or_nonuniform")}


def score_substrate(S: Any, substrate: dict[str, Any], mx: Any, mlx_load: Any) -> dict[str, Any]:
    model, tokenizer = mlx_load(substrate["path"])
    protected = S.protected_rows()
    cases = S.acquisition_cases()
    started = time.monotonic()
    prot_scored = S.score_rows(model, tokenizer, mx, protected)
    protected_correct = [row.get("correct") is True for row in prot_scored]
    overall_protected = sum(protected_correct) / len(protected_correct)
    per_panel_protected = {}
    for panel in range(16):
        segment = protected_correct[panel * 16:panel * 16 + 16]
        per_panel_protected[f"panel-{panel}"] = sum(segment) / 16
    acq_rows = [{"case_id": c["case_id"], "prompt": c["composition_prompt"],
                 "target": c["target"], "candidates": list(c["candidates"])} for c in cases]
    acq_scored = S.score_rows(model, tokenizer, mx, acq_rows)
    acq_correct = [row.get("correct") is True for row in acq_scored]
    overall_acquisition = sum(acq_correct) / len(acq_correct)
    per_panel_novelty = {}
    for panel in range(16):
        segment = acq_correct[panel * 4:panel * 4 + 4]
        per_panel_novelty[f"panel-{panel}"] = segment.count(False)
    protected_pass = overall_protected == 1.0
    novelty_pass = all(count >= 3 for count in per_panel_novelty.values())
    viable = protected_pass and novelty_pass
    failing = []
    if not protected_pass:
        failing.append("protected_arithmetic_below_1.0")
    if not novelty_pass:
        failing.append("acquisition_novelty_below_3_in_some_panel")
    return {"protected_accuracy_overall": overall_protected,
            "per_panel_protected_accuracy": per_panel_protected,
            "acquisition_baseline_accuracy_overall": overall_acquisition,
            "per_panel_incorrect_before": per_panel_novelty,
            "protected_arithmetic_pass": protected_pass,
            "acquisition_novelty_pass": novelty_pass,
            "panels_below_protected_1.0": sorted(
                panel for panel, acc in per_panel_protected.items() if acc < 1.0),
            "panels_below_novelty_3": sorted(
                panel for panel, count in per_panel_novelty.items() if count < 3),
            "failing_conditions": failing,
            "classification": ("qualification_viable" if viable else "qualification_blocked"),
            "elapsed_seconds": time.monotonic() - started}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        return 0
    S = _load_surrogate()
    assert S.frozen_contract_sha256() == CONTRACT_SHA256
    assert S.V41R27.acquisition()["instrument_sha256"] == ACQUISITION_SHA256
    assert S.V41R27.protected()["instrument_sha256"] == PROTECTED_SHA256
    import mlx.core as mx
    from mlx_lm import load as mlx_load
    substrate_results = {}
    for substrate in SUBSTRATES:
        if substrate["kind"] == "architecture_check":
            substrate_results[substrate["key"]] = {
                "kind": "architecture_check",
                "path": substrate["path"],
                "identity": {k: v for k, v in substrate.items() if k.endswith("_sha256")},
                **architecture_check(substrate)}
        else:
            substrate_results[substrate["key"]] = {
                "kind": "transformer",
                "path": substrate["path"],
                "identity": {k: v for k, v in substrate.items() if k.endswith("_sha256")},
                **score_substrate(S, substrate, mx, mlx_load)}
    viable = sorted(key for key, result in substrate_results.items()
                    if result.get("classification") == "qualification_viable")
    body = {"version": VERSION, "state_slice": STATE_SLICE,
            "classification": "V41R29SubstrateCapabilityBoundaryComplete",
            "contract_sha256": CONTRACT_SHA256,
            "acquisition_instrument_sha256": ACQUISITION_SHA256,
            "protected_instrument_sha256": PROTECTED_SHA256,
            "substrates": substrate_results,
            "qualification_viable_substrates": viable,
            "full_local_qualification_possible": len(viable) > 0,
            "substrate_requirement": ("uniform transformer qkvo architecture AND protected arithmetic "
                                      "exactly 1.0 across all 256 rows AND acquisition novelty >= 3 "
                                      "in all 16 panels"),
            "claim_ceiling": CLAIM_CEILING,
            "tune_opened": False, "assessment_opened": False,
            "adaptive_stopping": False, "production_actions": False,
            "provider_direct_authority": False}
    result = {**body, "result_sha256": S.canonical_hash(body)}
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    result_path = output / "substrate-capability-result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    manifest = f'{sha256_file(result_path)}  {result_path.name}\n'
    (output / "MANIFEST.sha256").write_text(manifest)
    print(json.dumps({"classification": result["classification"],
                      "qualification_viable_substrates": viable,
                      "full_local_qualification_possible": result["full_local_qualification_possible"],
                      "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
