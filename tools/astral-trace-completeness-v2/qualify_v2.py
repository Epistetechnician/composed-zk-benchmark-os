"""Run the authorized offline Gemma 3 V2 trace qualification.

State slice: astral-trace-completeness-gemma3-end-to-end-v2.
Assessment is not opened by this runner.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import uuid
from pathlib import Path
from typing import Any

import corpus_v2 as corpus
import custody_v2 as custody
import protocol_v2 as protocol
import registry_v2 as registry
import torch_adapter_v2 as adapter
import transcoder_v2
import validate_v2


SOURCE_FILES = (
    "protocol_v2.py",
    "corpus_v2.py",
    "registry_v2.py",
    "custody_v2.py",
    "torch_adapter_v2.py",
    "transcoder_v2.py",
    "validate_v2.py",
    "qualify_v2.py",
)
FEATURE_LAYER = 12
FEATURE_INPUT_PATH = f"model.layers.{FEATURE_LAYER}.pre_feedforward_layernorm"
FEATURE_OUTPUT_PATH = f"model.layers.{FEATURE_LAYER}.post_feedforward_layernorm"


def _source_manifest() -> dict[str, Any]:
    root = Path(__file__).resolve().parent
    value = {
        path.name: protocol.sha256_file(path)
        for path in (root / name for name in SOURCE_FILES)
    }
    return {"files": value, "manifest_sha256": protocol.digest_json(value)}


def _runtime_manifest() -> dict[str, Any]:
    packages = {}
    for name in ("torch", "transformers", "nnsight", "circuit-tracer", "transformer-lens", "safetensors"):
        packages[name] = importlib.metadata.version(name)
    value = {
        "python": platform.python_version(),
        "packages": packages,
        "offline_execution": os.environ.get("HF_HUB_OFFLINE") == "1" and os.environ.get("TRANSFORMERS_OFFLINE") == "1",
    }
    return {**value, "manifest_sha256": protocol.digest_json(value)}


def _max_delta(first: tuple[Any, ...], second: tuple[Any, ...]) -> float:
    import torch

    if len(first) != len(second):
        raise protocol.ProtocolError("logit sequence length mismatch")
    return max(float(torch.max(torch.abs(left - right)).item()) for left, right in zip(first, second))


def _feature_observer(transcoder: Any, measurements: list[dict[str, Any]]):
    import torch

    def observe(emitter: adapter.TraceEmitter, captures: dict[str, list[Any]], step: int, logits: Any) -> None:
        input_acts = captures[f"{FEATURE_INPUT_PATH}.output"][-1]
        target_acts = captures[f"{FEATURE_OUTPUT_PATH}.output"][-1]
        with torch.no_grad():
            features = transcoder.encode(input_acts)
            reconstruction = transcoder.decode(features, input_acts)
            nmse = transcoder_v2.normalized_reconstruction_mse(transcoder, input_acts, target_acts)
            active = int(torch.count_nonzero(features).item())
            feature_index, feature_value = transcoder_v2.top_feature(transcoder, input_acts)
        emitter.emit(
            "sae_features",
            layer_index=FEATURE_LAYER,
            module_path=FEATURE_INPUT_PATH,
            shape=tuple(int(item) for item in features.shape),
            dtype=str(features.dtype),
            value_sha256=adapter.tensor_digest(features),
            metadata={"active_feature_count": active, "top_feature_index": feature_index, "top_feature_value": feature_value},
        )
        emitter.emit(
            "sae_reconstruction",
            layer_index=FEATURE_LAYER,
            module_path=FEATURE_OUTPUT_PATH,
            shape=tuple(int(item) for item in reconstruction.shape),
            dtype=str(reconstruction.dtype),
            value_sha256=adapter.tensor_digest(reconstruction),
            metadata={"normalized_mse": nmse},
        )
        measurements.append({"step": step, "normalized_mse": nmse, "active_feature_count": active, "top_feature_index": feature_index})

    return observe


def _write_capture(root: Path, run: adapter.TraceRun) -> dict[str, Any]:
    from safetensors.torch import save_file

    path = root / "raw" / f"{run.run_id}.captures.safetensors"
    if path.exists():
        raise protocol.ProtocolError("raw capture path already exists")
    tensors = {
        f"{key.replace('.', '__')}__{index}": tensor.detach().contiguous().cpu()
        for key, values in run.captures.items()
        for index, tensor in enumerate(values)
    }
    if not tensors:
        raise protocol.ProtocolError("capture set is empty")
    save_file(tensors, str(path))
    os.chmod(path, 0o600)
    value = {
        "run_id": run.run_id,
        "relative_path": path.relative_to(root).as_posix(),
        "sha256": protocol.sha256_file(path),
        "tensor_count": len(tensors),
    }
    return {**value, "manifest_sha256": protocol.digest_json(value)}


def _custody_run(root: Path, repository_root: Path, run: adapter.TraceRun) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = custody.write_raw_events(
        root,
        repository_root,
        run.run_id,
        run.events,
        event_stream_sha256=str(run.aggregate["event_stream_sha256"]),
    )
    receipt = validate_v2.validate_run(
        dict(run.aggregate),
        manifest,
        custody_root=root,
        repository_root=repository_root,
    )
    if not receipt["valid"]:
        raise protocol.ProtocolError(f"independent event validation failed: {receipt['errors']}")
    return manifest, receipt


def execute(repository_root: Path, custody_root: Path, model_root: Path) -> dict[str, Any]:
    import torch
    import transformers

    custody_receipt = custody.validate_root(custody_root, repository_root)
    if not custody_receipt["valid"]:
        raise protocol.ProtocolError(f"custody root invalid: {custody_receipt['errors']}")
    runtime = _runtime_manifest()
    if not runtime["offline_execution"]:
        raise protocol.ProtocolError("qualification requires offline execution environment")
    source = _source_manifest()
    model_manifest = protocol.tree_manifest(model_root)
    assets = transcoder_v2.asset_manifest()
    model = transformers.AutoModelForCausalLM.from_pretrained(
        str(model_root),
        local_files_only=True,
        dtype=torch.bfloat16,
        attn_implementation="eager",
    ).to("mps")
    module_registry = registry.validate_model(model)
    tokenizer = transformers.AutoTokenizer.from_pretrained(str(model_root), local_files_only=True)
    family = corpus.families()[0]
    if family.split != "fit":
        raise protocol.ProtocolError("qualification prompt is not in fit split")
    input_ids = tokenizer(family.prompt(), return_tensors="pt").input_ids.to("mps")
    target_ids = tokenizer(" " + str(family.answer()), add_special_tokens=False).input_ids
    target_token = int(target_ids[0]) if target_ids else None
    native_logits, native_tokens = adapter.native_generate(model, input_ids, max_new_tokens=2)
    transcoder = transcoder_v2.load_transcoder(FEATURE_LAYER, device="mps", dtype=torch.float32)
    generator = adapter.InstrumentedGenerator(model)
    measurements_a: list[dict[str, Any]] = []
    run_a = generator.run(
        input_ids,
        trial_id=f"{family.family_id}-repeat-a",
        max_new_tokens=2,
        target_token_ids=(target_token,) if target_token is not None else (),
        capture_paths=(FEATURE_INPUT_PATH, FEATURE_OUTPUT_PATH),
        feature_observer=_feature_observer(transcoder, measurements_a),
        sae_feature_events_per_step=1,
        sae_reconstruction_events_per_step=1,
    )
    measurements_b: list[dict[str, Any]] = []
    run_b = generator.run(
        input_ids,
        trial_id=f"{family.family_id}-repeat-b",
        max_new_tokens=2,
        target_token_ids=(target_token,) if target_token is not None else (),
        capture_paths=(FEATURE_INPUT_PATH, FEATURE_OUTPUT_PATH),
        feature_observer=_feature_observer(transcoder, measurements_b),
        sae_feature_events_per_step=1,
        sae_reconstruction_events_per_step=1,
    )
    noop = generator.run(
        input_ids,
        trial_id=f"{family.family_id}-noop",
        max_new_tokens=2,
        intervention=adapter.InterventionPlan(FEATURE_OUTPUT_PATH, 0, "noop"),
    )
    zero = generator.run(
        input_ids,
        trial_id=f"{family.family_id}-zero",
        max_new_tokens=2,
        intervention=adapter.InterventionPlan(FEATURE_OUTPUT_PATH, 0, "zero"),
    )
    manifests = {}
    validator_receipts = {}
    for run in (run_a, run_b, noop, zero):
        manifest, receipt = _custody_run(custody_root, repository_root, run)
        manifests[run.run_id] = manifest
        validator_receipts[run.run_id] = receipt
    capture_manifests = [_write_capture(custody_root, run_a), _write_capture(custody_root, run_b)]
    feature_stability = transcoder_v2.feature_stability_cosine(
        transcoder,
        run_a.captures[f"{FEATURE_INPUT_PATH}.output"][0],
        run_b.captures[f"{FEATURE_INPUT_PATH}.output"][0],
    )
    metrics = {
        "native_instrumented_max_abs_logit_delta": _max_delta(native_logits, run_a.logits),
        "deterministic_repeat_max_abs_logit_delta": _max_delta(run_a.logits, run_b.logits),
        "noop_identity_max_abs_logit_delta": _max_delta(run_a.logits, noop.logits),
        "zero_replacement_max_abs_logit_delta": _max_delta(run_a.logits, zero.logits),
        "native_sampled_token_match": native_tokens == run_a.sampled_tokens,
        "repeat_sampled_token_match": run_a.sampled_tokens == run_b.sampled_tokens,
        "noop_sampled_token_match": run_a.sampled_tokens == noop.sampled_tokens,
        "sae_normalized_reconstruction_mse_max": max(item["normalized_mse"] for item in measurements_a + measurements_b),
        "sae_feature_stability_cosine": feature_stability,
    }
    gates = {
        "native_parity": metrics["native_instrumented_max_abs_logit_delta"] <= protocol.PARITY_MAX_ABS_DELTA and metrics["native_sampled_token_match"],
        "deterministic_repeat": metrics["deterministic_repeat_max_abs_logit_delta"] <= protocol.REPEAT_MAX_ABS_DELTA and metrics["repeat_sampled_token_match"],
        "noop_identity": metrics["noop_identity_max_abs_logit_delta"] <= protocol.NOOP_MAX_ABS_DELTA and metrics["noop_sampled_token_match"],
        "nonzero_intervention_reach": metrics["zero_replacement_max_abs_logit_delta"] > protocol.REPEAT_MAX_ABS_DELTA,
        "event_completeness": all(receipt["valid"] for receipt in validator_receipts.values()),
        "sae_reconstruction": metrics["sae_normalized_reconstruction_mse_max"] <= protocol.SAE_RECONSTRUCTION_NMSE_MAX,
        "sae_feature_stability": metrics["sae_feature_stability_cosine"] >= protocol.FEATURE_STABILITY_COSINE_MIN,
    }
    campaign_id = uuid.uuid4().hex
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "campaign_id": campaign_id,
        "claim_ceiling": protocol.QUALIFICATION_CEILING,
        "status": "QUALIFIED_PREASSESSMENT_OPEN" if all(gates.values()) else "QUALIFICATION_FAILED",
        "assessment_opened": False,
        "network_access_during_execution": False,
        "model": {"id": protocol.MODEL_ID, "manifest_sha256": model_manifest["manifest_sha256"]},
        "runtime": runtime,
        "source": source,
        "assets": assets,
        "corpus": corpus.public_manifest(),
        "module_registry_sha256": module_registry["module_registry_sha256"],
        "custody": custody_receipt,
        "run_aggregate_sha256": {run.run_id: protocol.digest_json(run.aggregate) for run in (run_a, run_b, noop, zero)},
        "event_manifest_sha256": {run_id: manifest["manifest_sha256"] for run_id, manifest in manifests.items()},
        "capture_manifest_sha256": [manifest["manifest_sha256"] for manifest in capture_manifests],
        "validator_receipt_sha256": {run_id: receipt["receipt_sha256"] for run_id, receipt in validator_receipts.items()},
        "metrics": metrics,
        "gates": gates,
        "raw_retention_hours": protocol.RAW_RETENTION_HOURS,
    }
    value["qualification_sha256"] = protocol.digest_json(value)
    path = custody.write_aggregate(custody_root, repository_root, f"qualification-{campaign_id}.json", value)
    return {**value, "aggregate_path": str(path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--custody-root", type=Path, default=protocol.CUSTODY_ROOT)
    parser.add_argument("--model-root", type=Path, default=protocol.MODEL_ROOT)
    args = parser.parse_args(argv)
    result = execute(args.repository_root.resolve(), args.custody_root.resolve(), args.model_root.resolve())
    print(json.dumps({key: result[key] for key in ("status", "qualification_sha256", "metrics", "gates", "aggregate_path")}, sort_keys=True))
    return 0 if result["status"] == "QUALIFIED_PREASSESSMENT_OPEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())

