"""Qualification, locking, and held-out causal runner for V1.

State slice: astral-trace-completeness-gemma3-causal-feature-effects-v1.

The runner is transport-neutral: a GiveMeANode worker must place the exact
allocation and independent-review receipts in the external custody root, then
invoke this file with the frozen paths. No provider API is guessed or called
from this repository.
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib.metadata
import json
import math
import os
import platform
import uuid
from pathlib import Path
from typing import Any, Mapping, Sequence

import adapter_v1 as adapter
import corpus_v1 as corpus
import custody_v1 as custody
import effects_v1 as effects
import protocol_v1 as protocol
import registry_v1 as registry
import review_v1 as review
import transcoder_v1 as transcoder
import validate_v1 as validator


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN_ID = "v1-givemeanode-causal-feature-effects-20260831"
SOURCE_FILES = review.SOURCE_FILES


def _runtime_manifest() -> dict[str, Any]:
    package_names = (
        "torch",
        "transformers",
        "nnsight",
        "circuit-tracer",
        "cryptography",
        "safetensors",
        "transformer-lens",
    )
    packages: dict[str, str] = {}
    for name in package_names:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "missing"
    value = {
        "python": platform.python_version(),
        "packages": packages,
        "offline_execution": os.environ.get("HF_HUB_OFFLINE") == "1"
        and os.environ.get("TRANSFORMERS_OFFLINE") == "1",
    }
    return {**value, "manifest_sha256": protocol.digest_json(value)}


def _write_private(path: Path, value: Mapping[str, Any]) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(protocol.canonical_bytes(value) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _artifact_names(execution_id: str) -> tuple[str, str]:
    """Return append-only aggregate and raw-expiry artifact names for one run.

    State slice: astral-trace-completeness-gemma3-causal-feature-effects-v1.
    """

    return (
        f"v1-causal-feature-effects-aggregate-{execution_id}.json",
        f"raw-deletion-completion-{execution_id}.json",
    )


def _load_json(path: Path) -> dict[str, Any]:
    value = protocol.strict_json(path)
    if not isinstance(value, dict):
        raise protocol.ProtocolError(f"receipt is not an object: {path}")
    return value


def preflight(
    *,
    repository_root: Path,
    custody_root: Path,
    node_receipt_path: Path | None,
    reviewer_receipt_path: Path | None,
    spend_ceiling_usd: float | None,
) -> dict[str, Any]:
    packet_value = review.packet(repository_root, custody_root)
    node_receipt = _load_json(node_receipt_path) if node_receipt_path and node_receipt_path.is_file() else None
    reviewer_receipt = _load_json(reviewer_receipt_path) if reviewer_receipt_path and reviewer_receipt_path.is_file() else None
    review_value = review.static_review(
        packet_value,
        node_receipt=node_receipt,
        spend_ceiling_usd=spend_ceiling_usd,
        reviewer_receipt=reviewer_receipt,
        custody_root=custody_root,
    )
    custody_value = protocol.custody_receipt(custody_root, repository_root)
    return {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "campaign_id": CAMPAIGN_ID,
        "packet_sha256": packet_value["packet_sha256"],
        "review": review_value,
        "custody": custody_value,
        "node_receipt_present": node_receipt is not None,
        "reviewer_receipt_present": reviewer_receipt is not None,
        "execution_authorized": False,
        "assessment_opened": False,
    }


def _max_delta(first: Sequence[Any], second: Sequence[Any]) -> float:
    import torch

    if len(first) != len(second):
        raise protocol.ProtocolError("logit sequence length mismatch")
    return max(float(torch.max(torch.abs(left - right)).item()) for left, right in zip(first, second))


def _metric(logits: Any, tokenizer: Any, family: corpus.PromptFamily) -> tuple[float, list[float]]:
    import torch

    target = tokenizer.encode(str(family.answer()), add_special_tokens=False)
    distractor = tokenizer.encode(str(family.answer("corrupted")), add_special_tokens=False)
    if len(target) != 1 or len(distractor) != 1 or target[0] == distractor[0]:
        raise protocol.ProtocolError("corpus answer is not represented by distinct single tokens")
    values = torch.softmax(logits[0], dim=-1).detach().float().cpu().tolist()
    return effects.logit_margin(logits[0].detach().float().cpu().tolist(), target[0], distractor[0]), values


def _validate_metric_targets(tokenizer: Any, families: Sequence[corpus.PromptFamily]) -> None:
    for family in families:
        target = tokenizer.encode(str(family.answer()), add_special_tokens=False)
        distractor = tokenizer.encode(str(family.answer("corrupted")), add_special_tokens=False)
        if len(target) != 1 or len(distractor) != 1 or target[0] == distractor[0]:
            raise protocol.ProtocolError(f"corpus target-token qualification failed for {family.family_id}")


def _observer(transcoder_model: Any, feature_store: dict[str, Any], statistics: list[dict[str, Any]]) -> Any:
    def observe(emitter: Any, captures: Mapping[str, Sequence[Any]], step: int, logits: Any) -> None:
        input_activation = captures[f"{protocol.FEATURE_INPUT_PATH}.output"][-1]
        target_activation = captures[f"{protocol.FEATURE_OUTPUT_PATH}.output"][-1]
        features = transcoder.encode_features(transcoder_model, input_activation)
        feature_store["features"] = features.detach().clone()
        feature_store["input"] = input_activation.detach().clone()
        feature_store["target"] = target_activation.detach().clone()
        with __import__("torch").no_grad():
            reconstruction = transcoder_model.decode(features, input_activation.to(transcoder_model.dtype))
        error = reconstruction.float() - target_activation.float()
        statistics.append(
            {
                "sum_squared_error": float((error * error).sum().item()),
                "target_squared_sum": float((target_activation.float() ** 2).sum().item()),
                "target_sum": float(target_activation.float().sum().item()),
                "coordinate_count": int(target_activation.numel()),
            }
        )
        feature_store["reconstruction"] = statistics[-1]
        emitter.emit(
            "sae_features",
            layer_index=12,
            module_path=protocol.FEATURE_INPUT_PATH,
            shape=tuple(int(item) for item in features.shape),
            dtype=str(features.dtype),
            value_sha256=adapter.tensor_digest(features),
            metadata={"feature_width": protocol.FEATURE_WIDTH},
        )
        emitter.emit(
            "sae_reconstruction",
            layer_index=12,
            module_path=protocol.FEATURE_OUTPUT_PATH,
            shape=tuple(int(item) for item in reconstruction.shape),
            dtype=str(reconstruction.dtype),
            value_sha256=adapter.tensor_digest(reconstruction),
            metadata={"estimand": "pooled_global_centered_nmse"},
        )

    return observe


def _capture_manifest(root: Path, run: adapter.TraceRun) -> dict[str, Any]:
    from safetensors.torch import save_file

    path = root / "raw" / f"{run.run_id}.captures.safetensors"
    tensors = {
        f"{key.replace('.', '__')}__{index}": tensor.detach().contiguous().cpu()
        for key, values in run.captures.items()
        for index, tensor in enumerate(values)
    }
    if not tensors:
        raise protocol.ProtocolError("V1 capture set is empty")
    save_file(tensors, str(path))
    os.chmod(path, 0o600)
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "run_id": run.run_id,
        "relative_path": path.relative_to(root).as_posix(),
        "sha256": protocol.sha256_file(path),
        "tensor_count": len(tensors),
    }
    return {**value, "manifest_sha256": protocol.digest_json(value)}


def _custody_run(root: Path, run: adapter.TraceRun) -> dict[str, Any]:
    manifest = custody.write_raw_events(
        root,
        REPOSITORY_ROOT,
        run.run_id,
        run.events,
        event_stream_sha256=str(run.aggregate["event_stream_sha256"]),
    )
    receipt = validator.validate_run(
        dict(run.aggregate),
        manifest,
        custody_root=root,
        repository_root=REPOSITORY_ROOT,
    )
    if not receipt["valid"]:
        raise protocol.ProtocolError(f"independent event replay failed: {receipt['errors']}")
    _write_private(root / "aggregate" / f"{run.run_id}.event-manifest.json", manifest)
    _write_private(root / "receipts" / f"{run.run_id}.validator-receipt.json", receipt)
    return receipt


def _run_one(
    generator: Any,
    tokenizer: Any,
    family: corpus.PromptFamily,
    *,
    intervention: adapter.CausalIntervention | None,
    transcoder_model: Any,
    custody_root: Path,
    capture: bool,
    repeat_index: int = 0,
) -> tuple[adapter.TraceRun, dict[str, Any]]:
    import torch

    torch.manual_seed(protocol.CORPUS_SEED)
    input_ids = tokenizer(family.prompt(), return_tensors="pt").input_ids.to("cuda")
    store: dict[str, Any] = {}
    stats: list[dict[str, Any]] = []
    run = generator.run(
        input_ids,
        trial_id=f"{family.family_id}:{intervention.kind if intervention else 'natural'}",
        max_new_tokens=1,
        intervention=intervention,
        repeat_index=repeat_index,
        capture_paths=(protocol.FEATURE_INPUT_PATH, protocol.FEATURE_OUTPUT_PATH) if capture else (),
        feature_observer=_observer(transcoder_model, store, stats) if capture else None,
        sae_feature_events_per_step=1 if capture else 0,
        sae_reconstruction_events_per_step=1 if capture else 0,
    )
    receipt = _custody_run(custody_root, run)
    if capture:
        manifest = _capture_manifest(custody_root, run)
        custody.write_aggregate(custody_root, REPOSITORY_ROOT, f"{run.run_id}.capture-manifest.json", manifest)
    run._v1_feature_store = store  # type: ignore[attr-defined]
    return run, receipt


def _feature_selection(
    generator: Any,
    tokenizer: Any,
    transcoder_model: Any,
    families: Sequence[corpus.PromptFamily],
    custody_root: Path,
) -> tuple[tuple[int, ...], dict[str, Any]]:
    import torch

    totals: Any | None = None
    squared_error = 0.0
    target_squared_sum = 0.0
    for family in families:
        repeated: list[adapter.TraceRun] = []
        for repeat_index in range(protocol.REPEAT_COUNT):
            repeated.append(
                _run_one(
                    generator,
                    tokenizer,
                    family,
                    intervention=None,
                    transcoder_model=transcoder_model,
                    custody_root=custody_root,
                    capture=True,
                    repeat_index=repeat_index,
                )[0]
            )
        if any(_max_delta((repeated[0].logits), (run.logits)) > protocol.REPEAT_MAX_ABS_DELTA for run in repeated[1:]):
            raise protocol.ProtocolError("feature-selection repeatability gate failed")
        if any(
            _max_delta(
                repeated[0]._v1_feature_store["features"],  # type: ignore[attr-defined]
                run._v1_feature_store["features"],  # type: ignore[attr-defined]
            )
            > protocol.REPEAT_MAX_ABS_DELTA
            for run in repeated[1:]
        ):
            raise protocol.ProtocolError("feature-selection feature stability gate failed")
        features = repeated[0]._v1_feature_store["features"]  # type: ignore[attr-defined]
        reconstruction = repeated[0]._v1_feature_store["reconstruction"]  # type: ignore[attr-defined]
        squared_error += float(reconstruction["sum_squared_error"])
        target_squared_sum += float(reconstruction["target_squared_sum"])
        vector = features[..., -1, :].abs().float().reshape(-1)
        totals = vector if totals is None else totals + vector
    if totals is None:
        raise protocol.ProtocolError("empty fit selection")
    if target_squared_sum <= 0.0:
        raise protocol.ProtocolError("transcoder reconstruction denominator is nonpositive")
    nmse = squared_error / target_squared_sum
    reconstruction_gate = {
        "pooled_nmse": nmse,
        "threshold": protocol.RECONSTRUCTION_MAX_NMSE,
        "pass": nmse <= protocol.RECONSTRUCTION_MAX_NMSE,
        "fit_family_count": len(families),
    }
    if not reconstruction_gate["pass"]:
        raise protocol.ProtocolError("fresh V1 transcoder reconstruction gate failed")
    return (
        tuple(int(index) for index in torch.topk(totals, protocol.FEATURE_SELECTION_COUNT).indices.tolist()),
        reconstruction_gate,
    )


def _effect_row(
    family: corpus.PromptFamily,
    baseline: adapter.TraceRun,
    treatment: adapter.TraceRun,
    tokenizer: Any,
) -> dict[str, Any]:
    baseline_margin, baseline_distribution = _metric(baseline.logits[0], tokenizer, family)
    treatment_margin, treatment_distribution = _metric(treatment.logits[0], tokenizer, family)
    return {
        "family_id": family.family_id,
        "kind": treatment.trial_id.rsplit(":", 1)[-1],
        "margin_delta": treatment_margin - baseline_margin,
        "max_abs_logit_delta": _max_delta(baseline.logits, treatment.logits),
        "output_tv": effects.total_variation(baseline_distribution, treatment_distribution),
        "nonzero": abs(treatment_margin - baseline_margin) > protocol.NONZERO_EFFECT_MIN,
    }


def _repeated_effect_rows(
    family: corpus.PromptFamily,
    baselines: Sequence[adapter.TraceRun],
    intervention: adapter.CausalIntervention,
    *,
    split: str,
    feature_index: int | None,
    generator: Any,
    tokenizer: Any,
    transcoder_model: Any,
    custody_root: Path,
) -> list[dict[str, Any]]:
    treatments: list[adapter.TraceRun] = []
    for repeat_index in range(protocol.REPEAT_COUNT):
        treatments.append(
            _run_one(
                generator,
                tokenizer,
                family,
                intervention=intervention,
                transcoder_model=transcoder_model,
                custody_root=custody_root,
                capture=False,
                repeat_index=repeat_index,
            )[0]
        )
    if any(
        _max_delta(treatments[0].logits, treatment.logits) > protocol.REPEAT_MAX_ABS_DELTA
        for treatment in treatments[1:]
    ):
        raise protocol.ProtocolError(f"{intervention.kind} repeatability gate failed")
    return [
        {
            **_effect_row(family, baselines[repeat_index], treatment, tokenizer),
            "feature_index": feature_index,
            "repeat_index": repeat_index,
            "split": split,
        }
        for repeat_index, treatment in enumerate(treatments)
    ]


def _evaluate_split(
    split: str,
    families: Sequence[corpus.PromptFamily],
    selected_features: Sequence[int],
    generator: Any,
    tokenizer: Any,
    transcoder_model: Any,
    custody_root: Path,
) -> list[dict[str, Any]]:
    import torch

    rows: list[dict[str, Any]] = []
    baseline_records: list[tuple[corpus.PromptFamily, list[adapter.TraceRun], Mapping[str, Any]]] = []
    for family in families:
        baselines = [
            _run_one(
                generator,
                tokenizer,
                family,
                intervention=None,
                transcoder_model=transcoder_model,
                custody_root=custody_root,
                capture=True,
                repeat_index=repeat_index,
            )[0]
            for repeat_index in range(protocol.REPEAT_COUNT)
        ]
        baseline = baselines[0]
        store = baseline._v1_feature_store  # type: ignore[attr-defined]
        if any(_max_delta(baseline.logits, run.logits) > protocol.REPEAT_MAX_ABS_DELTA for run in baselines[1:]):
            raise protocol.ProtocolError("baseline repeatability gate failed")
        baseline_records.append((family, baselines, store))

    for record_index, (family, baselines, store) in enumerate(baseline_records):
        donor_family, _donor_baselines, donor_store = baseline_records[(record_index + 1) % len(baseline_records)]
        donor_features = donor_store["features"]
        activation_donor_family, activation_donor_store = family, store
        recipient_shape = tuple(store["target"].shape)
        for candidate_index in range(1, len(baseline_records) + 1):
            candidate_family, _candidate_baselines, candidate_store = baseline_records[(record_index + candidate_index) % len(baseline_records)]
            if tuple(candidate_store["target"].shape) == recipient_shape:
                activation_donor_family, activation_donor_store = candidate_family, candidate_store
                break
        donor_activation = activation_donor_store["target"]
        for kind in corpus.arm_order(family.family_id):
            if kind == "natural":
                continue
            if kind in {"feature_ablation", "feature_replacement", "shuffled", "constant"}:
                mode = {
                    "feature_ablation": "ablate",
                    "feature_replacement": "replace",
                    "shuffled": "shuffle",
                    "constant": "constant",
                }[kind]
                for feature_index in selected_features:
                    donor_features_for_mode = (
                        torch.roll(donor_features, shifts=1, dims=-2) if mode == "shuffle" else donor_features
                    )
                    donor = adapter.feature_donor(
                        transcoder_model,
                        store["input"],
                        store["target"],
                        feature_index=feature_index,
                        mode=mode,
                        donor_features=donor_features_for_mode,
                    )
                    rows.extend(
                        _repeated_effect_rows(
                            family,
                            baselines,
                            adapter.CausalIntervention(
                                protocol.FEATURE_OUTPUT_PATH,
                                0,
                                kind,
                                donor=donor,
                                feature_index=feature_index,
                                donor_trial_id=(
                                    family.family_id
                                    if kind == "feature_ablation"
                                    else donor_family.family_id
                                ),
                            ),
                            split=split,
                            feature_index=feature_index,
                            generator=generator,
                            tokenizer=tokenizer,
                            transcoder_model=transcoder_model,
                            custody_root=custody_root,
                        )
                    )
                continue
            if kind in {"activation_patch", "path_patch"}:
                donor = donor_activation
                path_id = "layer12-post-feedforward-to-output" if kind == "path_patch" else None
                rows.extend(
                    _repeated_effect_rows(
                        family,
                        baselines,
                        adapter.CausalIntervention(
                            protocol.FEATURE_OUTPUT_PATH,
                            0,
                            kind,
                            donor=donor,
                            path_id=path_id,
                            donor_trial_id=activation_donor_family.family_id,
                        ),
                        split=split,
                        feature_index=None,
                        generator=generator,
                        tokenizer=tokenizer,
                        transcoder_model=transcoder_model,
                        custody_root=custody_root,
                    )
                )
                continue
            donor = store["target"] if kind == "exact_copy" else None
            rows.extend(
                _repeated_effect_rows(
                    family,
                    baselines,
                    adapter.CausalIntervention(
                        protocol.FEATURE_OUTPUT_PATH,
                        0,
                        kind,
                        donor=donor,
                        donor_trial_id=family.family_id,
                    ),
                    split=split,
                    feature_index=None,
                    generator=generator,
                    tokenizer=tokenizer,
                    transcoder_model=transcoder_model,
                    custody_root=custody_root,
                )
            )
    return rows


def _fit_prediction(rows: Sequence[Mapping[str, Any]], selected_features: Sequence[int]) -> dict[str, Any]:
    # The graph is deliberately small and fixed: feature activity predicts the
    # corresponding exact-ablation margin effect. Coefficients are fit once on
    # fit rows and are never changed after the tune lock.
    grouped: dict[int, list[float]] = {feature: [] for feature in selected_features}
    for row in rows:
        if row["kind"] == "feature_ablation" and row["feature_index"] in grouped:
            grouped[int(row["feature_index"])].append(float(row["margin_delta"]))
    coefficients = {str(feature): (sum(values) / len(values) if values else 0.0) for feature, values in grouped.items()}
    value = {
        "graph": "locked-feature-ablation-margin-mean-v1",
        "selected_features": list(selected_features),
        "coefficients": coefficients,
        "fit_row_count": len(rows),
    }
    return {**value, "prediction_lock_sha256": protocol.digest_json(value)}


def _prediction_gate(
    rows: Sequence[Mapping[str, Any]],
    lock: Mapping[str, Any],
    *,
    kind: str = "feature_ablation",
) -> dict[str, Any]:
    observed: list[float] = []
    predicted: list[float] = []
    for row in rows:
        if row["kind"] == kind and row["feature_index"] is not None:
            coefficient = float(lock["coefficients"].get(str(row["feature_index"]), 0.0))
            observed.append(float(row["margin_delta"]))
            predicted.append(coefficient)
    agreement = effects.sign_agreement(observed, predicted) if observed else 0.0
    return {"sign_agreement": agreement, "pass": agreement >= protocol.PRIMARY_PREDICTION_SIGN_MIN, "n": len(observed)}


def _control_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    controls: dict[str, dict[str, Any]] = {}
    for kind, threshold in (
        ("noop", protocol.NOOP_MAX_ABS_DELTA),
        ("exact_copy", protocol.EXACT_COPY_MAX_ABS_DELTA),
    ):
        values = [abs(float(row["max_abs_logit_delta"])) for row in rows if row["kind"] == kind]
        if not values:
            controls[kind] = {"n": 0, "max_abs_logit_delta": None, "pass": False}
        else:
            maximum = max(values)
            controls[kind] = {"n": len(values), "max_abs_logit_delta": maximum, "pass": maximum <= threshold}
    effect_values = [abs(float(row["margin_delta"])) for row in rows if row["kind"] == "feature_ablation"]
    tv_values = [float(row["output_tv"]) for row in rows if row["kind"] == "feature_ablation"]
    controls["intervention_reach"] = {
        "n": len(effect_values),
        "max_abs_margin_delta": max(effect_values) if effect_values else None,
        "pass": bool(effect_values) and max(effect_values) > protocol.NONZERO_EFFECT_MIN,
    }
    controls["output_distribution_movement"] = {
        "n": len(tv_values),
        "max_total_variation": max(tv_values) if tv_values else None,
        "pass": bool(tv_values) and max(tv_values) > protocol.OUTPUT_TV_MIN,
    }
    return {"controls": controls, "pass": all(item["pass"] for item in controls.values())}


def execute(
    *,
    repository_root: Path,
    custody_root: Path,
    model_root: Path,
    asset_root: Path,
    node_receipt_path: Path,
    reviewer_receipt_path: Path,
    spend_ceiling_usd: float,
) -> dict[str, Any]:
    execution_id = uuid.uuid4().hex
    aggregate_filename, expiry_filename = _artifact_names(execution_id)
    node_receipt = _load_json(node_receipt_path)
    reviewer_receipt = _load_json(reviewer_receipt_path)
    packet_value = review.packet(repository_root, custody_root)
    review.validate_signed_acceptance(reviewer_receipt, packet_value["packet_sha256"])
    protocol.require_external_admission(node_receipt, reviewer_receipt, spend_ceiling_usd=spend_ceiling_usd)
    if not protocol.custody_receipt(custody_root, repository_root)["valid"]:
        raise protocol.ProtocolError("V1 custody root is invalid")
    if not model_root.is_dir() or not asset_root.is_dir():
        raise protocol.ProtocolError("model and asset roots must already be present on the node")
    binding_report = protocol.validate_external_bindings(custody_root, packet_value)
    if not binding_report["valid"]:
        raise protocol.ProtocolError(f"V1 external identity bindings failed: {binding_report['errors']}")
    bindings = {
        name: _load_json(path)
        for name, path in protocol.binding_paths(custody_root).items()
    }
    model_manifest = protocol.tree_manifest(model_root)
    if model_manifest != bindings["model"]["payload"]["manifest"]:
        raise protocol.ProtocolError("node model tree does not match the packet-bound model manifest")
    asset_variant_root = asset_root / protocol.ASSET_VARIANT
    if not asset_variant_root.is_dir():
        raise protocol.ProtocolError("node asset variant root is missing")
    asset_manifest = protocol.tree_manifest(asset_variant_root)
    if asset_manifest != bindings["asset"]["payload"]["file_manifest"]:
        raise protocol.ProtocolError("node asset tree does not match the packet-bound asset manifest")
    runtime = _runtime_manifest()
    if runtime != bindings["runtime"]["payload"]["runtime"]:
        raise protocol.ProtocolError("node runtime does not match the packet-bound runtime manifest")
    if corpus.public_manifest()["manifest_sha256"] != bindings["corpus"]["payload"]["manifest_sha256"]:
        raise protocol.ProtocolError("node corpus generator does not match the packet-bound corpus manifest")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise protocol.ProtocolError("V1 model execution requires offline Hugging Face flags")

    import torch
    import transformers

    torch.manual_seed(protocol.CORPUS_SEED)
    model = transformers.AutoModelForCausalLM.from_pretrained(
        str(model_root),
        local_files_only=True,
        dtype=torch.bfloat16,
        attn_implementation="eager",
    ).to("cuda")
    module_registry = registry.validate_model(model)
    tokenizer = transformers.AutoTokenizer.from_pretrained(str(model_root), local_files_only=True)
    transcoder_model = transcoder.load(root=asset_root, device="cuda", dtype=torch.float32)
    generator = adapter.InstrumentedGenerator(model, run_id_factory=lambda: f"{CAMPAIGN_ID}-{uuid.uuid4().hex}")
    fit = tuple(family for family in corpus.families() if family.split == "fit")
    tune = tuple(family for family in corpus.families() if family.split == "tune")
    assessment = tuple(family for family in corpus.families() if family.split == "assessment")
    _validate_metric_targets(tokenizer, (*fit, *tune, *assessment))
    simulated_power = effects.fixed_seed_power_simulation(
        family_count=protocol.SPLIT_SIZE,
        repeat_count=protocol.REPEAT_COUNT,
        standardized_effect=protocol.POWER_STANDARDIZED_EFFECT,
        icc=protocol.POWER_ICC,
        alpha=protocol.PRIMARY_ALPHA,
        simulations=protocol.POWER_SIMULATIONS,
    )
    power_gate = {"simulated_power": simulated_power, "target": protocol.POWER_TARGET, "pass": effects.power_pass(simulated_power)}
    parity_input = tokenizer(fit[0].prompt(), return_tensors="pt").input_ids.to("cuda")
    native_logits, native_tokens = adapter.native_generate(model, parity_input, max_new_tokens=1)
    instrumented_probe, _ = _run_one(
        generator,
        tokenizer,
        fit[0],
        intervention=None,
        transcoder_model=transcoder_model,
        custody_root=custody_root,
        capture=True,
        repeat_index=0,
    )
    parity_delta = _max_delta(native_logits, instrumented_probe.logits)
    parity = {
        "max_abs_logit_delta": parity_delta,
        "native_sample_digest": protocol.digest_json(list(native_tokens)),
        "instrumented_sample_digest": protocol.digest_json(list(instrumented_probe.sampled_tokens)),
        "sample_match": tuple(native_tokens) == tuple(instrumented_probe.sampled_tokens),
        "pass": parity_delta <= protocol.PARITY_MAX_ABS_DELTA
        and tuple(native_tokens) == tuple(instrumented_probe.sampled_tokens),
    }
    if not parity["pass"]:
        raise protocol.ProtocolError("native/instrumented parity gate failed")
    selected, reconstruction_gate = _feature_selection(generator, tokenizer, transcoder_model, fit, custody_root)
    fit_rows = _evaluate_split("fit", fit, selected, generator, tokenizer, transcoder_model, custody_root)
    fit_summary = effects.primary_feature_summary(
        fit_rows,
        selected,
        repeat_count=protocol.REPEAT_COUNT,
        alpha=protocol.PRIMARY_ALPHA,
    )
    prediction_lock = _fit_prediction(fit_rows, selected)
    tune_rows = _evaluate_split("tune", tune, selected, generator, tokenizer, transcoder_model, custody_root)
    tune_summary = effects.primary_feature_summary(
        tune_rows,
        selected,
        repeat_count=protocol.REPEAT_COUNT,
        alpha=protocol.PRIMARY_ALPHA,
    )
    tune_gate = _prediction_gate(tune_rows, prediction_lock)
    tune_controls = _control_gate(tune_rows)
    if not power_gate["pass"] or not fit_summary["all_pass"] or not tune_gate["pass"] or not tune_summary["all_pass"] or not tune_controls["pass"]:
        classification = "NoCandidate"
        assessment_rows: list[dict[str, Any]] = []
        assessment_summary: dict[str, Any] | None = None
        assessment_scrub: dict[str, Any] | None = None
        assessment_controls: dict[str, Any] | None = None
    else:
        assessment_rows = _evaluate_split("assessment", assessment, selected, generator, tokenizer, transcoder_model, custody_root)
        assessment_summary = effects.primary_feature_summary(
            assessment_rows,
            selected,
            repeat_count=protocol.REPEAT_COUNT,
            alpha=protocol.PRIMARY_ALPHA,
        )
        assessment_gate = _prediction_gate(assessment_rows, prediction_lock)
        assessment_scrub = effects.causal_scrub_score(
            assessment_rows,
            prediction_lock,
            repeat_count=protocol.REPEAT_COUNT,
            minimum=protocol.SCRUB_BALANCED_ACCURACY_MIN,
        )
        shuffled_scrub = effects.causal_scrub_score(
            assessment_rows,
            prediction_lock,
            repeat_count=protocol.REPEAT_COUNT,
            kind="shuffled",
            maximum=protocol.SCRUB_SHUFFLED_BALANCED_ACCURACY_MAX,
        )
        constant_scrub = effects.causal_scrub_score(
            assessment_rows,
            prediction_lock,
            repeat_count=protocol.REPEAT_COUNT,
            kind="constant",
            maximum=protocol.SCRUB_SHUFFLED_BALANCED_ACCURACY_MAX,
        )
        assessment_scrub = {
            "feature_ablation": assessment_scrub,
            "shuffled_control": shuffled_scrub,
            "constant_control": constant_scrub,
            "pass": assessment_scrub["pass"]
            and shuffled_scrub["pass"]
            and constant_scrub["pass"],
        }
        assessment_controls = _control_gate(assessment_rows)
        classification = (
            "HeldOutCausalFeatureEffectsAccepted"
            if assessment_gate["pass"]
            and assessment_summary["all_pass"]
            and assessment_scrub["pass"]
            and assessment_controls["pass"]
            else "NoCandidate"
        )
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "campaign_id": CAMPAIGN_ID,
        "execution_id": execution_id,
        "aggregate_artifact": aggregate_filename,
        "raw_expiry_artifact": expiry_filename,
        "classification": classification,
        "claim_ceiling": protocol.ASSESSMENT_CEILING if classification == "HeldOutCausalFeatureEffectsAccepted" else protocol.QUALIFICATION_CEILING,
        "assessment_opened": bool(assessment_rows),
        "model": {"id": protocol.MODEL_ID, "manifest_sha256": protocol.tree_manifest(model_root)["manifest_sha256"]},
        "native_instrumented_parity": parity,
        "reconstruction_gate": reconstruction_gate,
        "runtime": runtime,
        "source": review.source_manifest(repository_root),
        "module_registry": module_registry,
        "corpus_manifest_sha256": corpus.public_manifest()["manifest_sha256"],
        "selected_features": list(selected),
        "prediction_lock": prediction_lock,
        "power_gate": power_gate,
        "fit_effect_summary": fit_summary,
        "tune_prediction_gate": tune_gate,
        "tune_effect_summary": tune_summary,
        "tune_controls": tune_controls,
        "assessment_prediction_gate": _prediction_gate(assessment_rows, prediction_lock) if assessment_rows else None,
        "assessment_effect_summary": assessment_summary,
        "assessment_causal_scrub": assessment_scrub,
        "assessment_controls": assessment_controls,
        "arms": list(protocol.INTERVENTION_KINDS),
        "primary_effect": "paired feature_ablation minus natural target-distractor logit margin",
        "statistics": protocol.public_contract()["statistics"],
        "controls": protocol.public_contract()["thresholds"],
        "node_id": node_receipt["node_id"],
        "review_accept_sha256": reviewer_receipt["receipt_sha256"],
        "raw_expiry_pending": True,
    }
    expiry = custody.expire_raw(custody_root, repository_root)
    value["raw_expiry_pending"] = False
    aggregate = {**value, "aggregate_sha256": protocol.digest_json(value)}
    custody.write_aggregate(custody_root, repository_root, aggregate_filename, aggregate)
    custody.write_aggregate(custody_root, repository_root, expiry_filename, expiry)
    return {**aggregate, "raw_expiry": expiry}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("preflight", "execute"), default="preflight")
    parser.add_argument("--repository-root", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--custody-root", type=Path, default=protocol.CUSTODY_ROOT)
    parser.add_argument("--node-receipt", type=Path, default=protocol.NODE_ALLOCATION_RECEIPT)
    parser.add_argument("--reviewer-receipt", type=Path)
    parser.add_argument("--model-root", type=Path, default=protocol.MODEL_ROOT)
    parser.add_argument("--asset-root", type=Path, required=False)
    parser.add_argument("--spend-ceiling-usd", type=float)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "preflight":
        result = preflight(
            repository_root=args.repository_root,
            custody_root=args.custody_root,
            node_receipt_path=args.node_receipt,
            reviewer_receipt_path=args.reviewer_receipt,
            spend_ceiling_usd=args.spend_ceiling_usd,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return 0 if result["review"]["verdict"] == "ACCEPT" else 2
    if args.asset_root is None or args.reviewer_receipt is None or args.spend_ceiling_usd is None:
        raise protocol.ProtocolError("execute requires asset root, reviewer receipt, and spend ceiling")
    result = execute(
        repository_root=args.repository_root,
        custody_root=args.custody_root,
        model_root=args.model_root,
        asset_root=args.asset_root,
        node_receipt_path=args.node_receipt,
        reviewer_receipt_path=args.reviewer_receipt,
        spend_ceiling_usd=args.spend_ceiling_usd,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
