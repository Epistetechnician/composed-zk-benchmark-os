"""Run the V4 offline end-to-end trace qualification.

State slice: astral-trace-completeness-gemma3-end-to-end-v4.
Assessment remains closed by this runner.
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

import adapter_v4 as adapter
import corpus_v4 as corpus
import custody_v4 as custody
import protocol_v4 as protocol
import registry_v4 as registry
import transcoder_v4 as transcoder
import validate_v4 as validator

SOURCE_FILES = (
    "protocol_v4.py",
    "corpus_v4.py",
    "custody_v4.py",
    "registry_v4.py",
    "adapter_v4.py",
    "transcoder_v4.py",
    "validate_v4.py",
    "asset_qc_v4.py",
    "review_v4.py",
    "qualify_v4.py",
    "reconcile_v4.py",
    "expire_reconciled_v4.py",
)
SOURCE_DEPENDENCIES = {
    "v2/protocol_v2.py": Path(__file__).resolve().parents[1] / "astral-trace-completeness-v2" / "protocol_v2.py",
    "v2/registry_v2.py": Path(__file__).resolve().parents[1] / "astral-trace-completeness-v2" / "registry_v2.py",
    "v2/torch_adapter_v2.py": Path(__file__).resolve().parents[1] / "astral-trace-completeness-v2" / "torch_adapter_v2.py",
    "v2/validate_v2.py": Path(__file__).resolve().parents[1] / "astral-trace-completeness-v2" / "validate_v2.py",
}
FEATURE_INPUT_PATH = "model.layers.12.pre_feedforward_layernorm"
FEATURE_OUTPUT_PATH = "model.layers.12.post_feedforward_layernorm"
CAMPAIGN_ID = "v4-hypothesis-2-affine-pooled-20260830"


def _source_manifest() -> dict[str, Any]:
    root = Path(__file__).resolve().parent
    files = {name: protocol.sha256_file(root / name) for name in SOURCE_FILES}
    dependencies = {name: protocol.sha256_file(path) for name, path in SOURCE_DEPENDENCIES.items()}
    value = {"files": files, "dependencies": dependencies}
    return {**value, "manifest_sha256": protocol.digest_json(value)}


def _runtime_manifest() -> dict[str, Any]:
    packages = {name: importlib.metadata.version(name) for name in ("torch", "transformers", "nnsight", "circuit-tracer", "transformer-lens", "safetensors")}
    value = {"python": platform.python_version(), "packages": packages, "offline_execution": os.environ.get("HF_HUB_OFFLINE") == "1" and os.environ.get("TRANSFORMERS_OFFLINE") == "1"}
    return {**value, "manifest_sha256": protocol.digest_json(value)}


def _max_delta(first: tuple[Any, ...], second: tuple[Any, ...]) -> float:
    import torch

    if len(first) != len(second):
        raise protocol.ProtocolError("logit sequence length mismatch")
    return max(float(torch.max(torch.abs(left - right)).item()) for left, right in zip(first, second))


def _write_private(path: Path, value: dict[str, Any]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(protocol.canonical_bytes(value) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _write_capture(root: Path, run: adapter.TraceRun) -> dict[str, Any]:
    from safetensors.torch import save_file

    path = root / "raw" / f"{run.run_id}.captures.safetensors"
    tensors = {f"{key.replace('.', '__')}__{index}": tensor.detach().contiguous().cpu() for key, values in run.captures.items() for index, tensor in enumerate(values)}
    if not tensors:
        raise protocol.ProtocolError("V4 capture set is empty")
    save_file(tensors, str(path))
    os.chmod(path, 0o600)
    value = {"protocol": protocol.PROTOCOL_ID, "state_slice": protocol.STATE_SLICE, "run_id": run.run_id, "relative_path": path.relative_to(root).as_posix(), "sha256": protocol.sha256_file(path), "tensor_count": len(tensors)}
    return {**value, "manifest_sha256": protocol.digest_json(value)}


def _custody_run(root: Path, repository_root: Path, run: adapter.TraceRun) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = custody.write_raw_events(root, repository_root, run.run_id, run.events, event_stream_sha256=str(run.aggregate["event_stream_sha256"]))
    receipt = validator.validate_run(run.aggregate, manifest, custody_root=root, repository_root=repository_root)
    if not receipt["valid"]:
        raise protocol.ProtocolError(f"independent V4 event validation failed: {receipt['errors']}")
    _write_private(root / "aggregate" / f"{run.run_id}.event-manifest.json", manifest)
    _write_private(root / "receipts" / f"{run.run_id}.validator-receipt.json", receipt)
    return manifest, receipt


def _feature_observer(transcoder_model: Any, statistics: list[dict[str, float | int]], stability: list[Any]) -> Any:
    def observe(emitter: adapter.TraceEmitter, captures: dict[str, list[Any]], step: int, logits: Any) -> None:
        import torch

        input_acts = captures[f"{FEATURE_INPUT_PATH}.output"][-1]
        target_acts = captures[f"{FEATURE_OUTPUT_PATH}.output"][-1]
        stats = transcoder.pooled_sufficient_statistics(transcoder_model, input_acts, target_acts)
        stats["step"] = step
        statistics.append(stats)
        with torch.no_grad():
            transcoder_input = input_acts.to(transcoder_model.dtype)
            features = transcoder_model.encode(transcoder_input)
            reconstruction = transcoder_model.decode(features, transcoder_input)
        emitter.emit("sae_features", layer_index=12, module_path=FEATURE_INPUT_PATH, shape=tuple(int(item) for item in features.shape), dtype=str(features.dtype), value_sha256=adapter.tensor_digest(features), metadata={"active_feature_count": int(torch.count_nonzero(features).item())})
        emitter.emit("sae_reconstruction", layer_index=12, module_path=FEATURE_OUTPUT_PATH, shape=tuple(int(item) for item in reconstruction.shape), dtype=str(reconstruction.dtype), value_sha256=adapter.tensor_digest(reconstruction), metadata={"estimand": "pooled_global_centered_nmse"})
        if not stability:
            stability.append(features.detach().clone())

    return observe


def _check_preload_review(custody_root: Path) -> dict[str, Any]:
    review = protocol.strict_json(custody_root / "review" / "preload-review-v4.json")
    if review.get("review_sha256") != protocol.digest_json({key: value for key, value in review.items() if key != "review_sha256"}):
        raise protocol.ProtocolError("V4 pre-load review digest mismatch")
    if review.get("status") != "PRELOAD_ACCEPTED_STATIC_VALIDATOR" or review.get("model_execution") is not False or review.get("assessment_opened") is not False or review.get("signed_assessment_acceptance") is not False:
        raise protocol.ProtocolError("V4 pre-load review is not sealed")
    return review


def execute(repository_root: Path, custody_root: Path, model_root: Path) -> dict[str, Any]:
    import torch
    import transformers

    if custody_root.resolve() != protocol.CUSTODY_ROOT.resolve():
        raise protocol.ProtocolError("V4 custody identity is fixed")
    custody_receipt = protocol.custody_receipt(custody_root, repository_root)
    if not custody_receipt["valid"]:
        raise protocol.ProtocolError("V4 custody root invalid")
    review = _check_preload_review(custody_root)
    asset_qc = protocol.strict_json(custody_root / "aggregate" / "preload-asset-qc.json")
    if asset_qc.get("valid") is not True or asset_qc.get("model_execution") is not False or asset_qc.get("assessment_opened") is not False:
        raise protocol.ProtocolError("V4 asset QC is not sealed")
    runtime = _runtime_manifest()
    if not runtime["offline_execution"]:
        raise protocol.ProtocolError("V4 qualification requires offline execution")
    source = _source_manifest()
    model_manifest = protocol.tree_manifest(model_root)
    model = transformers.AutoModelForCausalLM.from_pretrained(str(model_root), local_files_only=True, dtype=torch.bfloat16, attn_implementation="eager").to("mps")
    module_registry = registry.validate_model(model)
    tokenizer = transformers.AutoTokenizer.from_pretrained(str(model_root), local_files_only=True)
    transcoder_model = transcoder.load(device="mps", dtype=torch.float32)
    generator = adapter.InstrumentedGenerator(model, run_id_factory=lambda: f"{CAMPAIGN_ID}-run-{uuid.uuid4().hex}")
    fit_families = tuple(family for family in corpus.families() if family.split == "fit")
    if len(fit_families) != corpus.SPLIT_SIZE:
        raise protocol.ProtocolError("V4 fit split cardinality mismatch")
    runs, manifests, receipts, captures, statistics, stability = [], {}, {}, [], [], []
    for family in fit_families:
        input_ids = tokenizer(family.prompt(), return_tensors="pt").input_ids.to("mps")
        run = generator.run(input_ids, trial_id=family.family_id, max_new_tokens=1, capture_paths=(FEATURE_INPUT_PATH, FEATURE_OUTPUT_PATH), feature_observer=_feature_observer(transcoder_model, statistics, stability), sae_feature_events_per_step=1, sae_reconstruction_events_per_step=1)
        runs.append(run)
        manifests[run.run_id], receipts[run.run_id] = _custody_run(custody_root, repository_root, run)
        capture_manifest = _write_capture(custody_root, run)
        captures.append(capture_manifest)
        custody.write_aggregate(custody_root, repository_root, f"{run.run_id}.capture-manifest.json", capture_manifest)
    first = runs[0]
    first_input_ids = tokenizer(fit_families[0].prompt(), return_tensors="pt").input_ids.to("mps")
    native_logits, native_tokens = adapter.native_generate(model, first_input_ids, max_new_tokens=1)
    repeat_statistics, repeat_stability = [], []
    repeat = generator.run(first_input_ids, trial_id=f"{fit_families[0].family_id}-repeat", max_new_tokens=1, capture_paths=(FEATURE_INPUT_PATH, FEATURE_OUTPUT_PATH), feature_observer=_feature_observer(transcoder_model, repeat_statistics, repeat_stability), sae_feature_events_per_step=1, sae_reconstruction_events_per_step=1)
    noop = generator.run(first_input_ids, trial_id=f"{fit_families[0].family_id}-noop", max_new_tokens=1, intervention=adapter.InterventionPlan(FEATURE_OUTPUT_PATH, 0, "noop"))
    zero = generator.run(first_input_ids, trial_id=f"{fit_families[0].family_id}-zero", max_new_tokens=1, intervention=adapter.InterventionPlan(FEATURE_OUTPUT_PATH, 0, "zero"))
    for run in (repeat, noop, zero):
        manifests[run.run_id], receipts[run.run_id] = _custody_run(custody_root, repository_root, run)
    all_statistics = statistics + repeat_statistics
    pooled_nmse = transcoder.pooled_global_centered_nmse(all_statistics)
    feature_stability = transcoder.feature_vector_cosine(stability[0], repeat_stability[0]) if stability and repeat_stability else 0.0
    metrics = {
        "native_instrumented_max_abs_logit_delta": _max_delta(native_logits, first.logits),
        "deterministic_repeat_max_abs_logit_delta": _max_delta(first.logits, repeat.logits),
        "noop_identity_max_abs_logit_delta": _max_delta(first.logits, noop.logits),
        "zero_replacement_max_abs_logit_delta": _max_delta(first.logits, zero.logits),
        "native_sampled_token_match": native_tokens == first.sampled_tokens,
        "repeat_sampled_token_match": first.sampled_tokens == repeat.sampled_tokens,
        "event_replay_valid": all(receipt["valid"] for receipt in receipts.values()),
        "fit_row_count": len(all_statistics),
        "fit_coordinate_count": sum(int(item["coordinate_count"]) for item in all_statistics),
        "pooled_global_centered_nmse": pooled_nmse,
        "feature_stability_cosine": feature_stability,
    }
    gates = {
        "native_parity": metrics["native_instrumented_max_abs_logit_delta"] <= 1e-4 and metrics["native_sampled_token_match"],
        "deterministic_repeat": metrics["deterministic_repeat_max_abs_logit_delta"] <= 1e-5 and metrics["repeat_sampled_token_match"],
        "noop_identity": metrics["noop_identity_max_abs_logit_delta"] <= 1e-5,
        "nonzero_intervention_reach": metrics["zero_replacement_max_abs_logit_delta"] > 1e-5,
        "event_replay": metrics["event_replay_valid"],
        "pooled_reconstruction": pooled_nmse <= protocol.RECONSTRUCTION_NMSE_MAX,
        "feature_stability": feature_stability >= protocol.FEATURE_STABILITY_COSINE_MIN,
    }
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "campaign_id": CAMPAIGN_ID,
        "claim_ceiling": protocol.QUALIFICATION_CEILING,
        "status": "QUALIFIED_PREASSESSMENT_OPEN" if all(gates.values()) else "QUALIFICATION_FAILED",
        "assessment_opened": False,
        "network_access_during_execution": False,
        "model": {"id": protocol.MODEL_ID, "manifest_sha256": model_manifest["manifest_sha256"]},
        "runtime": runtime,
        "source": source,
        "asset_qc_sha256": asset_qc["asset_qc_sha256"],
        "preload_review_sha256": review["review_sha256"],
        "corpus": corpus.public_manifest(),
        "module_registry_sha256": module_registry["module_registry_sha256"],
        "custody": custody_receipt,
        "run_aggregate_sha256": {run.run_id: protocol.digest_json(run.aggregate) for run in runs + [repeat, noop, zero]},
        "event_manifest_sha256": {run_id: manifest["manifest_sha256"] for run_id, manifest in manifests.items()},
        "capture_manifest_sha256": [manifest["manifest_sha256"] for manifest in captures],
        "validator_receipt_sha256": {run_id: receipt["receipt_sha256"] for run_id, receipt in receipts.items()},
        "metrics": metrics,
        "gates": gates,
        "raw_retention_hours": protocol.RAW_RETENTION_HOURS,
    }
    value["qualification_sha256"] = protocol.digest_json(value)
    path = custody.write_aggregate(custody_root, repository_root, f"qualification-{CAMPAIGN_ID}.json", value)
    return {**value, "aggregate_path": str(path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--custody-root", type=Path, default=protocol.CUSTODY_ROOT)
    parser.add_argument("--model-root", type=Path, default=protocol.MODEL_ROOT)
    args = parser.parse_args(argv)
    print(json.dumps(execute(args.repository_root.resolve(), args.custody_root.resolve(), args.model_root.resolve()), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
