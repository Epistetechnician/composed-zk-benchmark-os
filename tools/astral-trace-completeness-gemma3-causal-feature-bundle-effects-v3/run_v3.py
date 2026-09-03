"""Qualification, prediction locking, and held-out scrubbing for V3.

State slice: astral-trace-completeness-gemma3-causal-feature-bundle-effects-v3.
The runner is transport-neutral. A node worker must provide the exact
packet-bound node and review receipts before invoking ``execute``. Raw traces
are written only below the external custody root and are deleted before the
aggregate is finalized.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import platform
import uuid
from pathlib import Path
from typing import Any, Mapping, Sequence

import adapter_v3_slice as adapter
import corpus_v3_slice as corpus
import custody_v3_slice as custody
import effects_v3_slice as effects
import protocol_v3_slice as protocol
import registry_v3_slice as registry
import review_v3_slice as review
import transcoder_v3_slice as transcoder
import validate_v3_slice as validator


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CAMPAIGN_ID = "v3-givemeanode-causal-feature-bundle-effects-20260902"
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
    """Return append-only V3 aggregate and raw-deletion artifact names."""

    return (
        f"v3-causal-feature-bundle-aggregate-{execution_id}.json",
        f"v3-raw-deletion-completion-{execution_id}.json",
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
        raise protocol.ProtocolError("V3 capture set is empty")
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
    repeat_index: int,
) -> tuple[adapter.TraceRun, dict[str, Any]]:
    import torch

    torch.manual_seed(protocol.CORPUS_SEED)
    input_ids = tokenizer(family.prompt(), return_tensors="pt").input_ids.to("cuda")
    store: dict[str, Any] = {}
    stats: list[dict[str, Any]] = []
    kind = intervention.kind if intervention else "natural"
    run = generator.run(
        input_ids,
        trial_id=f"{family.family_id}:{kind}",
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
        custody.write_aggregate(custody_root, REPOSITORY_ROOT, f"{run.run_id}.capture-manifest.json", _capture_manifest(custody_root, run))
    run._v3_feature_store = store  # type: ignore[attr-defined]
    return run, receipt


def _pairwise_abs_corr(matrix: Any, left: int, right: int) -> float:
    import torch

    x = matrix[:, left].float()
    y = matrix[:, right].float()
    x = x - x.mean()
    y = y - y.mean()
    denominator = torch.linalg.vector_norm(x) * torch.linalg.vector_norm(y)
    if float(denominator.item()) == 0.0:
        return 0.0
    return abs(float(torch.dot(x, y).item() / denominator.item()))


def _bundle_score(matrix: Any, triple: Sequence[int]) -> float:
    pairs = ((triple[0], triple[1]), (triple[0], triple[2]), (triple[1], triple[2]))
    return min(_pairwise_abs_corr(matrix, left, right) for left, right in pairs)


def _feature_selection(
    generator: Any,
    tokenizer: Any,
    transcoder_model: Any,
    families: Sequence[corpus.PromptFamily],
    custody_root: Path,
) -> tuple[tuple[int, ...], dict[str, Any], dict[str, Any]]:
    import torch

    vectors: list[Any] = []
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
        if any(_max_delta(repeated[0].logits, run.logits) > protocol.REPEAT_MAX_ABS_DELTA for run in repeated[1:]):
            raise protocol.ProtocolError("V3 feature-selection repeatability gate failed")
        stores = [run._v3_feature_store for run in repeated]  # type: ignore[attr-defined]
        if any(_max_delta(stores[0]["features"], store["features"]) > protocol.REPEAT_MAX_ABS_DELTA for store in stores[1:]):
            raise protocol.ProtocolError("V3 feature-selection feature repeatability gate failed")
        store = stores[0]
        squared_error += float(store["reconstruction"]["sum_squared_error"])
        target_squared_sum += float(store["reconstruction"]["target_squared_sum"])
        vectors.append(store["features"][..., -1, :].float().reshape(-1))
    if not vectors or target_squared_sum <= 0.0:
        raise protocol.ProtocolError("V3 feature selection has no finite reconstruction target")
    nmse = squared_error / target_squared_sum
    reconstruction_gate = {
        "pooled_nmse": nmse,
        "threshold": protocol.RECONSTRUCTION_MAX_NMSE,
        "pass": nmse <= protocol.RECONSTRUCTION_MAX_NMSE,
        "fit_family_count": len(families),
    }
    if not reconstruction_gate["pass"]:
        raise protocol.ProtocolError("fresh V3 transcoder reconstruction gate failed")
    if len(vectors) != protocol.SPLIT_SIZE or protocol.FIT_HALF_SIZE * 2 != len(vectors):
        raise protocol.ProtocolError("V3 feature-stability halves are not the frozen fit split")
    matrix = torch.stack(vectors)
    discovery = matrix[: protocol.FIT_HALF_SIZE]
    replication = matrix[protocol.FIT_HALF_SIZE :]
    discovery_scores = discovery.abs().mean(dim=0)
    replication_scores = replication.abs().mean(dim=0)
    discovery_top = set(torch.topk(discovery_scores, protocol.FEATURE_STABILITY_TOP_K).indices.tolist())
    replication_top = set(torch.topk(replication_scores, protocol.FEATURE_STABILITY_TOP_K).indices.tolist())
    intersection = sorted(discovery_top & replication_top)
    if len(intersection) < protocol.FEATURE_STABILITY_MIN_INTERSECTION:
        stability_gate = {
            "intersection_count": len(intersection),
            "minimum_intersection": protocol.FEATURE_STABILITY_MIN_INTERSECTION,
            "selected_bundle": [],
            "pass": False,
        }
        return (), reconstruction_gate, stability_gate
    candidate_triples = effects.candidate_triples(intersection)
    scored: list[tuple[float, float, tuple[int, int, int]]] = []
    for triple in candidate_triples:
        discovery_score = _bundle_score(discovery, triple)
        replication_score = _bundle_score(replication, triple)
        pooled_score = _bundle_score(matrix, triple)
        scored.append((min(discovery_score, replication_score), pooled_score, triple))
    ranked = sorted(scored, key=lambda item: (-item[0], -item[1], item[2]))
    lower_score, pooled_score, selected = ranked[0]
    selected_discovery = _bundle_score(discovery, selected)
    selected_replication = _bundle_score(replication, selected)
    stability_pass = (
        lower_score >= protocol.BUNDLE_PAIRWISE_CORRELATION_MIN
        and selected_discovery >= protocol.BUNDLE_PAIRWISE_CORRELATION_MIN
        and selected_replication >= protocol.BUNDLE_PAIRWISE_CORRELATION_MIN
    )
    stability_gate = {
        "estimand": "minimum pairwise absolute activation correlation for the selected triple, replicated across disjoint fit halves",
        "discovery_family_count": protocol.FIT_HALF_SIZE,
        "replication_family_count": protocol.FIT_HALF_SIZE,
        "top_k_per_half": protocol.FEATURE_STABILITY_TOP_K,
        "discovery_top_k_count": len(discovery_top),
        "replication_top_k_count": len(replication_top),
        "intersection_count": len(intersection),
        "minimum_intersection": protocol.FEATURE_STABILITY_MIN_INTERSECTION,
        "candidate_count": len(candidate_triples),
        "selected_bundle": list(selected),
        "discovery_min_pairwise_abs_corr": selected_discovery,
        "replication_min_pairwise_abs_corr": selected_replication,
        "lower_half_score": lower_score,
        "pooled_score": pooled_score,
        "threshold": protocol.BUNDLE_PAIRWISE_CORRELATION_MIN,
        "pass": stability_pass,
    }
    return selected if stability_pass else (), reconstruction_gate, stability_gate


def _effect_row(
    family: corpus.PromptFamily,
    baseline: adapter.TraceRun,
    treatment: adapter.TraceRun,
    tokenizer: Any,
    *,
    feature_index: int | None,
    bundle_values: Sequence[float] | None,
    donor_bundle_values: Sequence[float] | None,
) -> dict[str, Any]:
    baseline_margin, baseline_distribution = _metric(baseline.logits[0], tokenizer, family)
    treatment_margin, treatment_distribution = _metric(treatment.logits[0], tokenizer, family)
    return {
        "family_id": family.family_id,
        "kind": treatment.trial_id.rsplit(":", 1)[-1],
        "feature_index": feature_index,
        "margin_delta": treatment_margin - baseline_margin,
        "max_abs_logit_delta": _max_delta(baseline.logits, treatment.logits),
        "output_tv": effects.total_variation(baseline_distribution, treatment_distribution),
        "nonzero": abs(treatment_margin - baseline_margin) > protocol.NONZERO_EFFECT_MIN,
        "bundle_values": tuple(float(value) for value in bundle_values) if bundle_values is not None else (),
        "donor_bundle_values": tuple(float(value) for value in donor_bundle_values) if donor_bundle_values is not None else (),
    }


def _repeated_effect_rows(
    family: corpus.PromptFamily,
    baselines: Sequence[adapter.TraceRun],
    intervention: adapter.CausalIntervention,
    *,
    split: str,
    feature_index: int | None,
    bundle_values: Sequence[float] | None,
    donor_bundle_values: Sequence[float] | None,
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
    if any(_max_delta(treatments[0].logits, treatment.logits) > protocol.REPEAT_MAX_ABS_DELTA for treatment in treatments[1:]):
        raise protocol.ProtocolError(f"{intervention.kind} repeatability gate failed")
    return [
        {
            **_effect_row(
                family,
                baselines[repeat_index],
                treatment,
                tokenizer,
                feature_index=feature_index,
                bundle_values=bundle_values,
                donor_bundle_values=donor_bundle_values,
            ),
            "repeat_index": repeat_index,
            "split": split,
        }
        for repeat_index, treatment in enumerate(treatments)
    ]


def _bundle_values(store: Mapping[str, Any], indices: Sequence[int]) -> tuple[float, ...]:
    values = store["features"][..., -1, :].detach().float().reshape(-1)
    return tuple(float(values[index].item()) for index in indices)


def _evaluate_split(
    split: str,
    families: Sequence[corpus.PromptFamily],
    selected_bundle: Sequence[int],
    generator: Any,
    tokenizer: Any,
    transcoder_model: Any,
    custody_root: Path,
) -> list[dict[str, Any]]:
    import torch

    bundle = tuple(int(index) for index in selected_bundle)
    if len(bundle) != protocol.FEATURE_SELECTION_COUNT:
        raise protocol.ProtocolError("V3 effect evaluation requires one locked three-feature bundle")
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
        if any(_max_delta(baselines[0].logits, run.logits) > protocol.REPEAT_MAX_ABS_DELTA for run in baselines[1:]):
            raise protocol.ProtocolError("V3 baseline repeatability gate failed")
        baseline_records.append((family, baselines, baselines[0]._v3_feature_store))  # type: ignore[attr-defined]

    decoy = tuple((index + 1) % protocol.FEATURE_WIDTH for index in bundle)
    for record_index, (family, baselines, store) in enumerate(baseline_records):
        donor_index = (record_index + 1) % len(baseline_records)
        donor_family, _donor_baselines, donor_store = baseline_records[donor_index]
        own_values = _bundle_values(store, bundle)
        donor_values = _bundle_values(donor_store, bundle)
        decoy_values = _bundle_values(store, decoy)
        recipient_shape = tuple(store["target"].shape)
        activation_donor_family, activation_donor_store = donor_family, donor_store
        for offset in range(1, len(baseline_records) + 1):
            candidate = baseline_records[(record_index + offset) % len(baseline_records)]
            if tuple(candidate[2]["target"].shape) == recipient_shape:
                activation_donor_family, activation_donor_store = candidate[0], candidate[2]
                break
        activation_donor = activation_donor_store["target"]
        shuffled_features = torch.roll(donor_store["features"], shifts=1, dims=-1)
        for kind in corpus.arm_order(family.family_id):
            if kind == "natural":
                continue
            if kind == "bundle_ablation":
                donor = adapter.bundle_donor(
                    transcoder_model,
                    store["input"],
                    store["target"],
                    feature_indices=bundle,
                    mode="ablate",
                )
                rows.extend(_repeated_effect_rows(
                    family, baselines,
                    adapter.CausalIntervention(protocol.FEATURE_OUTPUT_PATH, 0, kind, donor=donor, feature_indices=bundle, donor_trial_id=family.family_id),
                    split=split, feature_index=None, bundle_values=own_values, donor_bundle_values=own_values,
                    generator=generator, tokenizer=tokenizer, transcoder_model=transcoder_model, custody_root=custody_root,
                ))
            elif kind == "singleton_ablation":
                for index in bundle:
                    donor = adapter.bundle_donor(
                        transcoder_model, store["input"], store["target"], feature_indices=(index,), mode="ablate"
                    )
                    rows.extend(_repeated_effect_rows(
                        family, baselines,
                        adapter.CausalIntervention(protocol.FEATURE_OUTPUT_PATH, 0, kind, donor=donor, feature_indices=(index,), feature_index=index, donor_trial_id=family.family_id),
                        split=split, feature_index=index, bundle_values=own_values, donor_bundle_values=own_values,
                        generator=generator, tokenizer=tokenizer, transcoder_model=transcoder_model, custody_root=custody_root,
                    ))
            elif kind == "bundle_replacement":
                donor = adapter.bundle_donor(
                    transcoder_model, store["input"], store["target"], feature_indices=bundle, mode="replace", donor_features=donor_store["features"]
                )
                rows.extend(_repeated_effect_rows(
                    family, baselines,
                    adapter.CausalIntervention(protocol.FEATURE_OUTPUT_PATH, 0, kind, donor=donor, feature_indices=bundle, donor_trial_id=donor_family.family_id),
                    split=split, feature_index=None, bundle_values=own_values, donor_bundle_values=donor_values,
                    generator=generator, tokenizer=tokenizer, transcoder_model=transcoder_model, custody_root=custody_root,
                ))
            elif kind in {"shuffled_bundle", "constant_bundle", "decoy_bundle"}:
                if kind == "shuffled_bundle":
                    donor = adapter.bundle_donor(
                        transcoder_model, store["input"], store["target"], feature_indices=bundle, mode="replace", donor_features=shuffled_features
                    )
                    donor_values_for_row = tuple(float(shuffled_features[..., -1, index].item()) for index in bundle)
                elif kind == "constant_bundle":
                    donor = adapter.bundle_donor(
                        transcoder_model, store["input"], store["target"], feature_indices=bundle, mode="constant"
                    )
                    donor_values_for_row = (protocol.CONSTANT_FEATURE_VALUE,) * len(bundle)
                else:
                    donor = adapter.bundle_donor(
                        transcoder_model, store["input"], store["target"], feature_indices=decoy, mode="ablate"
                    )
                    donor_values_for_row = decoy_values
                rows.extend(_repeated_effect_rows(
                    family, baselines,
                    adapter.CausalIntervention(protocol.FEATURE_OUTPUT_PATH, 0, kind, donor=donor, feature_indices=bundle if kind != "decoy_bundle" else decoy, donor_trial_id=family.family_id),
                    split=split, feature_index=None, bundle_values=own_values, donor_bundle_values=donor_values_for_row,
                    generator=generator, tokenizer=tokenizer, transcoder_model=transcoder_model, custody_root=custody_root,
                ))
            elif kind in {"activation_patch", "path_patch"}:
                path_id = "layer12-post-feedforward-to-output" if kind == "path_patch" else None
                rows.extend(_repeated_effect_rows(
                    family, baselines,
                    adapter.CausalIntervention(protocol.FEATURE_OUTPUT_PATH, 0, kind, donor=activation_donor, path_id=path_id, donor_trial_id=activation_donor_family.family_id),
                    split=split, feature_index=None, bundle_values=own_values, donor_bundle_values=donor_values,
                    generator=generator, tokenizer=tokenizer, transcoder_model=transcoder_model, custody_root=custody_root,
                ))
            else:
                donor = store["target"] if kind == "exact_copy" else None
                rows.extend(_repeated_effect_rows(
                    family, baselines,
                    adapter.CausalIntervention(protocol.FEATURE_OUTPUT_PATH, 0, kind, donor=donor, donor_trial_id=family.family_id if donor is not None else None),
                    split=split, feature_index=None, bundle_values=own_values, donor_bundle_values=own_values if donor is not None else (),
                    generator=generator, tokenizer=tokenizer, transcoder_model=transcoder_model, custody_root=custody_root,
                ))
    return rows


def _family_bundle_rows(rows: Sequence[Mapping[str, Any]], kind: str) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("kind") != kind:
            continue
        family_id = str(row["family_id"])
        if row.get("repeat_index") == 0:
            selected[family_id] = dict(row)
    if not selected:
        raise protocol.ProtocolError(f"V3 predictor has no {kind} family rows")
    return [selected[key] for key in sorted(selected)]


def _fit_prediction(rows: Sequence[Mapping[str, Any]], bundle: Sequence[int]) -> dict[str, Any]:
    import torch

    family_rows = _family_bundle_rows(rows, "bundle_ablation")
    raw = torch.tensor([row["bundle_values"] for row in family_rows], dtype=torch.float64)
    target = torch.tensor([float(row["margin_delta"]) for row in family_rows], dtype=torch.float64)
    means = raw.mean(dim=0)
    scales = raw.std(dim=0, unbiased=False)
    scales = torch.where(scales > 0.0, scales, torch.ones_like(scales))
    standardized = (raw - means) / scales
    design = torch.cat((torch.ones((raw.shape[0], 1), dtype=torch.float64), standardized, standardized[:, [0]] * standardized[:, [1]], standardized[:, [0]] * standardized[:, [2]], standardized[:, [1]] * standardized[:, [2]]), dim=1)
    penalty = torch.eye(design.shape[1], dtype=torch.float64)
    penalty[0, 0] = 0.0
    coefficients = torch.linalg.solve(design.T @ design + penalty, design.T @ target)
    value = {
        "graph": "locked-bundle-interchange-polynomial-ridge-v3",
        "bundle_indices": list(bundle),
        "terms": ["intercept", "z0", "z1", "z2", "z0*z1", "z0*z2", "z1*z2"],
        "feature_means": [float(value) for value in means.tolist()],
        "feature_scales": [float(value) for value in scales.tolist()],
        "coefficients": [float(value) for value in coefficients.tolist()],
        "ridge_lambda": 1.0,
        "fit_family_count": len(family_rows),
    }
    return {**value, "prediction_lock_sha256": protocol.digest_json(value)}


def _predict(lock: Mapping[str, Any], values: Sequence[float]) -> float:
    import numpy as np

    means = np.asarray(lock["feature_means"], dtype=float)
    scales = np.asarray(lock["feature_scales"], dtype=float)
    z = (np.asarray(values, dtype=float) - means) / scales
    design = np.asarray([1.0, z[0], z[1], z[2], z[0] * z[1], z[0] * z[2], z[1] * z[2]], dtype=float)
    return float(design @ np.asarray(lock["coefficients"], dtype=float))


def _prediction_gate(rows: Sequence[Mapping[str, Any]], lock: Mapping[str, Any]) -> dict[str, Any]:
    family_rows = _family_bundle_rows(rows, "bundle_ablation")
    observed = [float(row["margin_delta"]) for row in family_rows]
    predicted = [_predict(lock, row["bundle_values"]) for row in family_rows]
    sign = effects.sign_agreement(observed, predicted)
    mean_observed = effects.paired_mean(observed)
    mean_predicted = effects.paired_mean(predicted)
    numerator = sum((actual - estimate) ** 2 for actual, estimate in zip(observed, predicted))
    denominator = sum((actual - mean_observed) ** 2 for actual in observed)
    r2 = 1.0 - numerator / denominator if denominator > 0.0 else 0.0
    return {
        "family_count": len(family_rows),
        "sign_agreement": sign,
        "sign_agreement_min": protocol.PRIMARY_PREDICTION_SIGN_MIN,
        "r2": r2,
        "r2_min": 0.25,
        "pass": sign >= protocol.PRIMARY_PREDICTION_SIGN_MIN and r2 >= 0.25,
    }


def _control_gate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    controls: dict[str, dict[str, Any]] = {}
    for kind, threshold in (("noop", protocol.NOOP_MAX_ABS_DELTA), ("exact_copy", protocol.EXACT_COPY_MAX_ABS_DELTA)):
        values = [abs(float(row["max_abs_logit_delta"])) for row in rows if row["kind"] == kind]
        maximum = max(values) if values else None
        controls[kind] = {"n": len(values), "max_abs_logit_delta": maximum, "pass": bool(values) and maximum <= threshold}
    effect_values = [abs(float(row["margin_delta"])) for row in rows if row["kind"] == "bundle_ablation"]
    tv_values = [float(row["output_tv"]) for row in rows if row["kind"] == "bundle_ablation"]
    controls["joint_intervention_reach"] = {"n": len(effect_values), "max_abs_margin_delta": max(effect_values) if effect_values else None, "pass": bool(effect_values) and max(effect_values) > protocol.NONZERO_EFFECT_MIN}
    controls["output_distribution_movement"] = {"n": len(tv_values), "max_total_variation": max(tv_values) if tv_values else None, "pass": bool(tv_values) and max(tv_values) > protocol.OUTPUT_TV_MIN}
    return {"controls": controls, "pass": all(item["pass"] for item in controls.values())}


def _scrub_rows(rows: Sequence[Mapping[str, Any]], lock: Mapping[str, Any], kind: str, arm: str) -> list[dict[str, Any]]:
    result = []
    for row in rows:
        if row.get("kind") != kind:
            continue
        predicted = _predict(lock, row["donor_bundle_values"]) - _predict(lock, row["bundle_values"])
        observed = float(row["margin_delta"])
        result.append({
            "family_id": row["family_id"],
            "scrub_arm": arm,
            "kind": "scrub",
            "repeat_index": row["repeat_index"],
            "scrub_correct": int(observed != 0.0 and predicted != 0.0 and ((observed > 0.0) == (predicted > 0.0))),
        })
    return result


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
        raise protocol.ProtocolError("V3 custody root is invalid")
    if not model_root.is_dir() or not asset_root.is_dir():
        raise protocol.ProtocolError("model and asset roots must already be present on the node")
    binding_report = protocol.validate_external_bindings(custody_root, packet_value)
    if not binding_report["valid"]:
        raise protocol.ProtocolError(f"V3 external identity bindings failed: {binding_report['errors']}")
    bindings = {name: _load_json(path) for name, path in protocol.binding_paths(custody_root).items()}
    if protocol.tree_manifest(model_root) != bindings["model"]["payload"]["manifest"]:
        raise protocol.ProtocolError("node model tree does not match the packet-bound model manifest")
    asset_variant_root = asset_root / protocol.ASSET_VARIANT
    if not asset_variant_root.is_dir() or protocol.tree_manifest(asset_variant_root) != bindings["asset"]["payload"]["file_manifest"]:
        raise protocol.ProtocolError("node asset tree does not match the packet-bound asset manifest")
    runtime = _runtime_manifest()
    if runtime != bindings["runtime"]["payload"]["runtime"]:
        raise protocol.ProtocolError("node runtime does not match the packet-bound runtime manifest")
    if corpus.public_manifest()["manifest_sha256"] != bindings["corpus"]["payload"]["manifest_sha256"]:
        raise protocol.ProtocolError("node corpus generator does not match the packet-bound corpus manifest")
    if os.environ.get("HF_HUB_OFFLINE") != "1" or os.environ.get("TRANSFORMERS_OFFLINE") != "1":
        raise protocol.ProtocolError("V3 model execution requires offline Hugging Face flags")

    import torch
    import transformers

    torch.manual_seed(protocol.CORPUS_SEED)
    model = transformers.AutoModelForCausalLM.from_pretrained(str(model_root), local_files_only=True, dtype=torch.bfloat16, attn_implementation="eager").to("cuda")
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
    power_gate = {"simulated_power": simulated_power, "target": protocol.POWER_TARGET, "pass": effects.power_pass(simulated_power, protocol.POWER_TARGET)}
    parity_input = tokenizer(fit[0].prompt(), return_tensors="pt").input_ids.to("cuda")
    native_logits, native_tokens = adapter.native_generate(model, parity_input, max_new_tokens=1)
    instrumented_probe, _ = _run_one(generator, tokenizer, fit[0], intervention=None, transcoder_model=transcoder_model, custody_root=custody_root, capture=True, repeat_index=0)
    parity_delta = _max_delta(native_logits, instrumented_probe.logits)
    parity = {
        "max_abs_logit_delta": parity_delta,
        "native_sample_digest": protocol.digest_json(list(native_tokens)),
        "instrumented_sample_digest": protocol.digest_json(list(instrumented_probe.sampled_tokens)),
        "sample_match": tuple(native_tokens) == tuple(instrumented_probe.sampled_tokens),
        "pass": parity_delta <= protocol.PARITY_MAX_ABS_DELTA and tuple(native_tokens) == tuple(instrumented_probe.sampled_tokens),
    }
    if not parity["pass"]:
        raise protocol.ProtocolError("native/instrumented parity gate failed")
    selected, reconstruction_gate, feature_stability_gate = _feature_selection(generator, tokenizer, transcoder_model, fit, custody_root)
    fit_rows = _evaluate_split("fit", fit, selected, generator, tokenizer, transcoder_model, custody_root) if selected else []
    fit_summary = effects.bundle_effect_summary(fit_rows, selected, repeat_count=protocol.REPEAT_COUNT, alpha=protocol.PRIMARY_ALPHA) if selected else {"all_pass": False}
    prediction_lock = _fit_prediction(fit_rows, selected) if selected else {"graph": "not_fit", "prediction_lock_sha256": protocol.digest_json({"graph": "not_fit"})}
    tune_rows = _evaluate_split("tune", tune, selected, generator, tokenizer, transcoder_model, custody_root) if selected else []
    tune_summary = effects.bundle_effect_summary(tune_rows, selected, repeat_count=protocol.REPEAT_COUNT, alpha=protocol.PRIMARY_ALPHA) if selected else {"all_pass": False}
    tune_gate = _prediction_gate(tune_rows, prediction_lock) if selected else {"pass": False, "family_count": 0}
    tune_controls = _control_gate(tune_rows) if selected else {"pass": False, "controls": {}}
    assessment_rows: list[dict[str, Any]] = []
    assessment_summary: dict[str, Any] | None = None
    assessment_scrub: dict[str, Any] | None = None
    assessment_controls: dict[str, Any] | None = None
    if selected and feature_stability_gate["pass"] and power_gate["pass"] and fit_summary["all_pass"] and tune_gate["pass"] and tune_summary["all_pass"] and tune_controls["pass"]:
        assessment_rows = _evaluate_split("assessment", assessment, selected, generator, tokenizer, transcoder_model, custody_root)
        assessment_summary = effects.bundle_effect_summary(assessment_rows, selected, repeat_count=protocol.REPEAT_COUNT, alpha=protocol.PRIMARY_ALPHA)
        true_scrub = effects.causal_scrub_score(_scrub_rows(assessment_rows, prediction_lock, "bundle_replacement", "true"), minimum=protocol.SCRUB_BALANCED_ACCURACY_MIN)
        shuffled_scrub = effects.causal_scrub_score(_scrub_rows(assessment_rows, prediction_lock, "shuffled_bundle", "shuffled"), maximum=protocol.SCRUB_SHUFFLED_BALANCED_ACCURACY_MAX)
        constant_scrub = effects.causal_scrub_score(_scrub_rows(assessment_rows, prediction_lock, "constant_bundle", "constant"), maximum=protocol.SCRUB_SHUFFLED_BALANCED_ACCURACY_MAX)
        assessment_scrub = {"true_interchange": true_scrub, "shuffled_control": shuffled_scrub, "constant_control": constant_scrub, "pass": true_scrub["pass"] and shuffled_scrub["pass"] and constant_scrub["pass"]}
        assessment_controls = _control_gate(assessment_rows)
    classification = "HeldOutCausalFeatureBundleAssessmentV3" if assessment_rows and assessment_summary and assessment_summary["all_pass"] and assessment_scrub and assessment_scrub["pass"] and assessment_controls and assessment_controls["pass"] else "NoCandidate"
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "campaign_id": CAMPAIGN_ID,
        "execution_id": execution_id,
        "aggregate_artifact": aggregate_filename,
        "raw_expiry_artifact": expiry_filename,
        "classification": classification,
        "claim_ceiling": protocol.ASSESSMENT_CEILING if classification == "HeldOutCausalFeatureBundleAssessmentV3" else protocol.QUALIFICATION_CEILING,
        "assessment_opened": bool(assessment_rows),
        "model": {"id": protocol.MODEL_ID, "manifest_sha256": protocol.tree_manifest(model_root)["manifest_sha256"]},
        "native_instrumented_parity": parity,
        "reconstruction_gate": reconstruction_gate,
        "runtime": runtime,
        "source": review.source_manifest(repository_root),
        "module_registry": module_registry,
        "corpus_manifest_sha256": corpus.public_manifest()["manifest_sha256"],
        "selected_bundle": list(selected),
        "feature_stability_gate": feature_stability_gate,
        "prediction_lock": prediction_lock,
        "power_gate": power_gate,
        "fit_effect_summary": fit_summary,
        "tune_prediction_gate": tune_gate,
        "tune_effect_summary": tune_summary,
        "tune_controls": tune_controls,
        "assessment_effect_summary": assessment_summary,
        "assessment_causal_scrub": assessment_scrub,
        "assessment_controls": assessment_controls,
        "arms": list(protocol.INTERVENTION_KINDS),
        "primary_effect": "paired family-level bundle_ablation minus natural target-distractor logit margin",
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
    parser.add_argument("--asset-root", type=Path)
    parser.add_argument("--spend-ceiling-usd", type=float)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "preflight":
        result = preflight(repository_root=args.repository_root, custody_root=args.custody_root, node_receipt_path=args.node_receipt, reviewer_receipt_path=args.reviewer_receipt, spend_ceiling_usd=args.spend_ceiling_usd)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return 0 if result["review"]["verdict"] == "ACCEPT" else 2
    if args.asset_root is None or args.reviewer_receipt is None or args.spend_ceiling_usd is None:
        raise protocol.ProtocolError("execute requires asset root, reviewer receipt, and spend ceiling")
    result = execute(repository_root=args.repository_root, custody_root=args.custody_root, model_root=args.model_root, asset_root=args.asset_root, node_receipt_path=args.node_receipt, reviewer_receipt_path=args.reviewer_receipt, spend_ceiling_usd=args.spend_ceiling_usd)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
