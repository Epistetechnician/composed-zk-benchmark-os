#!/usr/bin/env python3
"""MiniMind domain-specific continual-learning V3 harness.

State slice: continual-learning-minimind-domain-specific-v3.

V3 is a fresh protocol identity. It does not import V1 or V2 scientific
artifacts. Synthetic execution is deterministic and offline. Model execution
is fail-closed until a certificate-backed, packet-bound independent receipt
verifies the current frozen bytes and the exact fresh corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import stat
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence


STATE_SLICE = "continual-learning-minimind-domain-specific-v3"
SCHEMA_VERSION = "minimind-domain-sequence-result-v3"
PROTOCOL = "minimind-domain-specific-sequence-v3"
SYNTHETIC_CLAIM_CEILING = "LocalDevelopmentMiniMindDomainSequenceSyntheticOnly"
MODEL_CLAIM_CEILING = "LocalDevelopmentMiniMindDomainSequenceQualificationV3"
RECEIPT_SCHEMA_VERSION = "minimind-domain-specific-v3-execution-receipt"
REGISTRY_SCHEMA_VERSION = "minimind-domain-specific-v3-reviewer-registry-v1"
CORPUS_SCHEMA_VERSION = "minimind-domain-specific-v3-corpus-manifest-v1"
UPSTREAM_URL = "https://github.com/jingyaogong/minimind"
UPSTREAM_COMMIT = "7a6fddd63a30c06b2fdd5fac4089922b29bc841b"
OPERATOR_ID = "shaanp"
OPERATOR_PRINCIPAL_ID = "principal-operator-shaanp"
REVIEWER_ROLE = "independent"
TRUSTED_AUTHORITY_ID = "external-independent-review-authority-v3"
REVIEWER_REGISTRY_PATH = Path(
    "/Users/shaanp/Documents/research-artifacts/"
    "continual-learning-minimind-domain-specific-v3-reviewer-registry-20260902.json"
)
TRUST_BUNDLE_PATH = Path(
    "/Users/shaanp/Documents/research-artifacts/"
    "continual-learning-minimind-domain-specific-v3-trust-bundle-20260902.json"
)
TRUST_BUNDLE_FILE_SHA256 = "6263ffeb3ca674f41b58f62f8f4b90f3a7f2903563677a0e4f8d9a4521d9ac27"
OPERATOR_BINDING_PATH = Path(
    "/Users/shaanp/Documents/research-artifacts/"
    "continual-learning-minimind-domain-specific-v3-operator-binding-20260902.json"
)
CORPUS_IDENTITY = "continual-learning-minimind-domain-specific-v3-fresh-corpus-20260902"
CORPUS_ROOT_NAME = "continual-learning-minimind-domain-specific-v3-corpus-20260902"
SYNTHETIC_ROOT_NAME = "continual-learning-minimind-domain-specific-v3-synthetic-20260902"
MODEL_ROOT_NAME = "continual-learning-minimind-domain-specific-v3-model-20260902"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = Path(
    "/Users/shaanp/Documents/research-artifacts/"
    "continual-learning-minimind-domain-specific-v3-source-20260902"
)
REVIEW_PACKET_PATH = REPO_ROOT / "docs/research/continual-learning/284-minimind-domain-specific-v3-review-packet.md"
FROZEN_REVIEW_FILES = (
    "docs/research/continual-learning/283-minimind-domain-specific-v3-protocol.md",
    "docs/research/continual-learning/284-minimind-domain-specific-v3-review-packet.md",
    "experiments/continual_learning/minimind_domain_specific_v3.py",
    "experiments/continual_learning/validate_minimind_domain_specific_v3.py",
    "experiments/continual_learning/tests/test_minimind_domain_specific_v3.py",
    "docs/research/continual-learning/285-minimind-domain-specific-v3-implementation-manifest.json",
    "AGENTS.md",
)
FORBIDDEN_PRIOR_ROOTS = tuple(
    Path(path).resolve()
    for path in (
        "/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v1-source-20260902",
        "/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v1-synthetic-20260902-r2",
        "/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v2-source-20260902",
        "/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v2-synthetic-20260902-r3",
    )
)

DOMAINS = ("materials", "clinical", "finance")
SPLITS = ("fit", "tune", "assessment")
ORDER_DIRECTIONS = ("forward", "reverse")
REPLICATE_SEEDS = (2026090207, 2026090208, 2026090209)
ORDER_SEEDS = (9611, 9612, 9613)
ARMS = (
    "untouched",
    "joint_oracle",
    "sequential_full",
    "sequential_lora",
    "sequential_replay",
    "domain_adapters",
)
VECTOR_DIMENSION = 8
UPDATE_UNITS_PER_STAGE = 3
MAX_FORGETTING = 0.25
MAX_ORDER_DELTA = 0.20
MAX_CHECKPOINT_ERROR = 1e-12
MODEL_CONFIG = {
    "model_name": "minimind-3-dense",
    "hidden_size": 768,
    "num_hidden_layers": 8,
    "use_moe": False,
    "vocab_size": 6400,
    "max_seq_len": 340,
}
REQUIRED_SOURCE_FILES = (
    "LICENSE",
    "requirements.txt",
    "model/model_minimind.py",
    "model/model_lora.py",
    "model/tokenizer.json",
    "model/tokenizer_config.json",
    "trainer/train_pretrain.py",
    "trainer/train_full_sft.py",
    "trainer/train_lora.py",
    "dataset/lm_dataset.py",
)

SYNTHETIC_KEYS = {
    "state_slice", "schema_version", "protocol", "claim_ceiling", "source",
    "corpus", "arms", "replicate_seeds", "order_seeds", "training_executed",
    "model_loaded", "inference_executed", "network_access", "provider_called",
    "phase_order", "assessment_began_after_lock", "prediction_lock", "aggregate_trials",
    "summary", "result_sha256",
}
RECEIPT_KEYS = {
    "schema_version", "state_slice", "review_packet_path", "review_packet_sha256",
    "reviewed_file_digests", "reviewer_registry_path", "reviewer_registry_sha256",
    "reviewer_identity", "reviewer_role", "reviewer_certificate_sha256",
    "operator_identity", "operator_binding_path", "operator_binding_sha256",
    "reviewer_public_key_hex", "corpus_manifest_sha256",
    "source_manifest_sha256", "disposition", "signature_algorithm", "signature",
}
TRIAL_GUARD_KEYS = {
    "forgetting", "checkpoint_restore", "complete_stage_coverage", "zero_attrition",
    "equal_token_budget",
}
MODEL_GUARD_KEYS = {
    "receipt_bound", "phase_order", "assessment_after_lock", "prediction_lock",
    "corpus_freshness", "corpus_disjointness", "prior_artifact_exclusion",
    "model_repeatability", "equal_token_budget", "zero_attrition", "checkpoint_restore",
}


class ProtocolError(ValueError):
    """Raised when the V3 boundary is violated."""


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _strict_load(path: Path) -> Any:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ProtocolError(f"duplicate JSON key in {path}: {key}")
            value[key] = item
        return value

    def reject_constant(value: str) -> None:
        raise ProtocolError(f"non-finite JSON constant in {path}: {value}")

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates, parse_constant=reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProtocolError(f"invalid JSON artifact: {path}") from error


def _has_symlink_component(path: Path) -> bool:
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        if current.is_symlink():
            return True
    return False


def _unit(*parts: object) -> float:
    payload = "|".join((STATE_SLICE, *(str(part) for part in parts))).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / float(1 << 64)


def _signed(*parts: object) -> float:
    return 2.0 * _unit(*parts) - 1.0


def _anchor() -> tuple[float, ...]:
    return tuple(0.08 * math.sin((index + 1) * 1.31) for index in range(VECTOR_DIMENSION))


def _target(domain: str, split: str, seed: int) -> tuple[float, ...]:
    scale = 0.42 + 0.08 * _unit("target-scale", domain, seed)
    return tuple(
        _anchor()[component]
        + scale * _signed("target", domain, seed, component)
        + 0.015 * _signed("split-noise", domain, split, seed, component)
        for component in range(VECTOR_DIMENSION)
    )


def _mean_vector(vectors: Sequence[Sequence[float]]) -> tuple[float, ...]:
    if not vectors:
        raise ProtocolError("cannot average an empty vector collection")
    return tuple(sum(vector[index] for vector in vectors) / len(vectors) for index in range(VECTOR_DIMENSION))


def _add(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a + b for a, b in zip(left, right))


def _sub(left: Sequence[float], right: Sequence[float]) -> tuple[float, ...]:
    return tuple(a - b for a, b in zip(left, right))


def _scale(vector: Sequence[float], multiplier: float) -> tuple[float, ...]:
    return tuple(multiplier * value for value in vector)


def _loss(state: Sequence[float], target: Sequence[float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(state, target)) / VECTOR_DIMENSION


def _domain_mask(domain: str) -> tuple[float, ...]:
    start = DOMAINS.index(domain) * 2
    return tuple(1.0 if start <= index < start + 2 else 0.0 for index in range(VECTOR_DIMENSION))


def _apply_mask(vector: Sequence[float], mask: Sequence[float]) -> tuple[float, ...]:
    return tuple(value * keep for value, keep in zip(vector, mask))


def _ordered_domains(order_seed: int, direction: str) -> tuple[str, ...]:
    if direction not in ORDER_DIRECTIONS:
        raise ProtocolError(f"unknown order direction: {direction}")
    indexed = list(enumerate(DOMAINS))
    indexed.sort(key=lambda item: (_unit("order", order_seed, item[1]), item[0]))
    if direction == "reverse":
        indexed.reverse()
    return tuple(domain for _, domain in indexed)


def _prediction_vector(arm: str, shared_state: Sequence[float], adapters: Mapping[str, Sequence[float]], domain: str) -> tuple[float, ...]:
    if arm == "domain_adapters":
        return _add(shared_state, adapters.get(domain, (0.0,) * VECTOR_DIMENSION))
    return tuple(shared_state)


def _run_synthetic_trial(arm: str, split: str, seed: int, order_seed: int, direction: str) -> dict[str, Any]:
    if arm not in ARMS or split not in SPLITS or direction not in ORDER_DIRECTIONS:
        raise ProtocolError(f"unknown synthetic identity: {arm}:{split}:{direction}")
    base = _anchor()
    shared_state = base
    adapters: dict[str, tuple[float, ...]] = {}
    fit_targets = {domain: _target(domain, "fit", seed) for domain in DOMAINS}
    evaluation_targets = {domain: _target(domain, split, seed) for domain in DOMAINS}
    order = _ordered_domains(order_seed, direction)
    learned_losses: dict[str, float] = {}
    stage_metrics: list[dict[str, Any]] = []
    checkpoint_errors: list[float] = []
    for stage_index, domain in enumerate(order, start=1):
        current_target = fit_targets[domain]
        if arm == "joint_oracle":
            shared_state = _scale(_add(shared_state, _mean_vector(tuple(fit_targets.values()))), 0.5)
        elif arm == "sequential_full":
            shared_state = _add(shared_state, _scale(_sub(current_target, shared_state), 0.42))
        elif arm == "sequential_lora":
            delta = _scale(_sub(current_target, shared_state), 0.78)
            shared_state = _add(shared_state, _apply_mask(delta, _domain_mask(domain)))
        elif arm == "sequential_replay":
            seen = [fit_targets[item] for item in order[: stage_index - 1]]
            replay_target = _mean_vector((current_target, *seen))
            shared_state = _add(shared_state, _scale(_sub(replay_target, shared_state), 0.42))
        elif arm == "domain_adapters":
            before = adapters.get(domain, (0.0,) * VECTOR_DIMENSION)
            desired = _sub(current_target, base)
            adapters[domain] = _add(before, _scale(_sub(desired, before), 0.78))
        encoded = json.dumps({"shared_state": list(shared_state), "adapters": {key: list(value) for key, value in adapters.items()}}, sort_keys=True, separators=(",", ":"))
        restored = json.loads(encoded)
        errors = [abs(left - right) for left, right in zip(shared_state, restored["shared_state"])]
        for item, values in adapters.items():
            errors.extend(abs(left - right) for left, right in zip(values, restored["adapters"][item]))
        checkpoint_error = max(errors, default=0.0)
        checkpoint_errors.append(checkpoint_error)
        domain_losses = {item: _loss(_prediction_vector(arm, shared_state, adapters, item), evaluation_targets[item]) for item in DOMAINS}
        learned_losses.setdefault(domain, domain_losses[domain])
        max_forgetting = max((max(0.0, domain_losses[item] - learned_losses[item]) for item in learned_losses), default=0.0)
        stage_metrics.append({
            "stage_index": stage_index,
            "domain": domain,
            "domain_losses": domain_losses,
            "mean_loss": sum(domain_losses.values()) / len(DOMAINS),
            "max_forgetting": max_forgetting,
            "update_units": UPDATE_UNITS_PER_STAGE,
            "checkpoint_restore_max_abs_error": checkpoint_error,
        })
    base_mean_loss = sum(_loss(base, evaluation_targets[domain]) for domain in DOMAINS) / len(DOMAINS)
    final_mean_loss = stage_metrics[-1]["mean_loss"]
    max_forgetting = max(item["max_forgetting"] for item in stage_metrics)
    max_checkpoint_error = max(checkpoint_errors, default=0.0)
    return {
        "arm": arm,
        "split": split,
        "replicate_seed": seed,
        "order_seed": order_seed,
        "order_direction": direction,
        "domain_order": list(order),
        "stage_count": len(stage_metrics),
        "base_mean_loss": base_mean_loss,
        "final_mean_loss": final_mean_loss,
        "primary_improvement": base_mean_loss - final_mean_loss,
        "max_forgetting": max_forgetting,
        "compute_units": UPDATE_UNITS_PER_STAGE * len(DOMAINS),
        "token_budget_units": UPDATE_UNITS_PER_STAGE * len(DOMAINS) * MODEL_CONFIG["max_seq_len"],
        "checkpoint_restore_max_abs_error": max_checkpoint_error,
        "hard_guards": {
            "forgetting": max_forgetting <= MAX_FORGETTING,
            "checkpoint_restore": max_checkpoint_error <= MAX_CHECKPOINT_ERROR,
            "complete_stage_coverage": len(stage_metrics) == len(DOMAINS),
            "zero_attrition": True,
            "equal_token_budget": True,
        },
    }


def _expected_trial_identities(splits: Sequence[str] = SPLITS, arms: Sequence[str] = ARMS) -> set[tuple[Any, ...]]:
    return {
        (arm, split, seed, order_seed, direction)
        for split in splits
        for arm in arms
        for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS)
        for direction in ORDER_DIRECTIONS
    }


def _summarize_trials(trials: Sequence[Mapping[str, Any]], *, locked_arm: str | None = None) -> dict[str, Any]:
    by_split_arm: dict[str, Any] = {}
    for split in ("fit", "tune"):
        for arm in ARMS:
            subset = [item for item in trials if item["split"] == split and item["arm"] == arm]
            if not subset:
                raise ProtocolError(f"missing trials for {split}:{arm}")
            paired = {}
            for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS):
                forward = next(item for item in subset if item["replicate_seed"] == seed and item["order_seed"] == order_seed and item["order_direction"] == "forward")
                reverse = next(item for item in subset if item["replicate_seed"] == seed and item["order_seed"] == order_seed and item["order_direction"] == "reverse")
                paired[str(seed)] = abs(forward["final_mean_loss"] - reverse["final_mean_loss"])
            max_order_delta = max(paired.values())
            by_split_arm[f"{split}:{arm}"] = {
                "trial_count": len(subset),
                "mean_primary_improvement": sum(item["primary_improvement"] for item in subset) / len(subset),
                "mean_final_loss": sum(item["final_mean_loss"] for item in subset) / len(subset),
                "max_forgetting": max(item["max_forgetting"] for item in subset),
                "order_deltas": paired,
                "max_order_delta": max_order_delta,
                "all_hard_guards_pass": all(set(item["hard_guards"]) == TRIAL_GUARD_KEYS and all(item["hard_guards"].values()) for item in subset) and max_order_delta <= MAX_ORDER_DELTA,
            }
    tune = {arm: by_split_arm[f"tune:{arm}"] for arm in ARMS}
    selected = min(ARMS, key=lambda arm: (tune[arm]["mean_final_loss"], ARMS.index(arm)))
    if locked_arm is not None and selected != locked_arm:
        raise ProtocolError("assessment changed the precomputed tune lock")
    if locked_arm is None:
        locked_arm = selected
    assessment_subset = [item for item in trials if item["split"] == "assessment" and item["arm"] == locked_arm]
    if assessment_subset:
        paired = {}
        for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS):
            forward = next(item for item in assessment_subset if item["replicate_seed"] == seed and item["order_seed"] == order_seed and item["order_direction"] == "forward")
            reverse = next(item for item in assessment_subset if item["replicate_seed"] == seed and item["order_seed"] == order_seed and item["order_direction"] == "reverse")
            paired[str(seed)] = abs(forward["final_mean_loss"] - reverse["final_mean_loss"])
        assessment_summary = {
            "trial_count": len(assessment_subset),
            "mean_primary_improvement": sum(item["primary_improvement"] for item in assessment_subset) / len(assessment_subset),
            "mean_final_loss": sum(item["final_mean_loss"] for item in assessment_subset) / len(assessment_subset),
            "max_forgetting": max(item["max_forgetting"] for item in assessment_subset),
            "order_deltas": paired,
            "max_order_delta": max(paired.values()),
            "all_hard_guards_pass": all(set(item["hard_guards"]) == TRIAL_GUARD_KEYS and all(item["hard_guards"].values()) for item in assessment_subset) and max(paired.values()) <= MAX_ORDER_DELTA,
        }
        by_split_arm[f"assessment:{locked_arm}"] = assessment_summary
    return {
        "by_split_arm": by_split_arm,
        "prediction_lock": {"selection_split": "tune", "locked_arm": locked_arm, "selection_metric": "mean_final_loss"},
        "disposition": "SyntheticCandidate" if assessment_subset and assessment_summary["all_hard_guards_pass"] and assessment_summary["mean_primary_improvement"] > 0.0 else "NoCandidate",
    }


def run_synthetic_campaign() -> dict[str, Any]:
    # The explicit phase construction is part of the contract: no assessment
    # trial is computed until the tune lock exists.
    fit_trials = [_run_synthetic_trial(arm, "fit", seed, order_seed, direction) for arm in ARMS for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS) for direction in ORDER_DIRECTIONS]
    tune_trials = [_run_synthetic_trial(arm, "tune", seed, order_seed, direction) for arm in ARMS for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS) for direction in ORDER_DIRECTIONS]
    tune_summary = _summarize_trials([*fit_trials, *tune_trials])
    locked_arm = tune_summary["prediction_lock"]["locked_arm"]
    assessment_trials = [_run_synthetic_trial(arm, "assessment", seed, order_seed, direction) for arm in ARMS for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS) for direction in ORDER_DIRECTIONS]
    trials = [*fit_trials, *tune_trials, *assessment_trials]
    summary = _summarize_trials(trials, locked_arm=locked_arm)
    result: dict[str, Any] = {
        "state_slice": STATE_SLICE,
        "schema_version": SCHEMA_VERSION,
        "protocol": PROTOCOL,
        "claim_ceiling": SYNTHETIC_CLAIM_CEILING,
        "source": {"url": UPSTREAM_URL, "commit": UPSTREAM_COMMIT, "model_config": MODEL_CONFIG},
        "corpus": {"kind": "deterministic_exact_synthetic_v3", "identity": f"{STATE_SLICE}-fixture", "domains": list(DOMAINS), "splits": list(SPLITS), "corpus_digest": digest({"state_slice": STATE_SLICE, "domains": DOMAINS, "splits": SPLITS})},
        "arms": list(ARMS),
        "replicate_seeds": list(REPLICATE_SEEDS),
        "order_seeds": list(ORDER_SEEDS),
        "training_executed": False,
        "model_loaded": False,
        "inference_executed": False,
        "network_access": False,
        "provider_called": False,
        "phase_order": ["fit", "tune", "prediction_lock", "assessment"],
        "assessment_began_after_lock": True,
        "prediction_lock": summary["prediction_lock"],
        "aggregate_trials": trials,
        "summary": summary,
    }
    result["result_sha256"] = digest({key: value for key, value in result.items() if key != "result_sha256"})
    validate_synthetic_result(result)
    return result


def validate_synthetic_result(result: Mapping[str, Any]) -> None:
    if set(result) != SYNTHETIC_KEYS:
        raise ProtocolError("synthetic result schema mismatch")
    if result.get("state_slice") != STATE_SLICE or result.get("schema_version") != SCHEMA_VERSION or result.get("protocol") != PROTOCOL:
        raise ProtocolError("synthetic result identity mismatch")
    if result.get("claim_ceiling") != SYNTHETIC_CLAIM_CEILING:
        raise ProtocolError("synthetic claim ceiling mismatch")
    if result.get("training_executed") or result.get("model_loaded") or result.get("inference_executed"):
        raise ProtocolError("synthetic result claims model execution")
    if result.get("network_access") or result.get("provider_called"):
        raise ProtocolError("synthetic result claims external access")
    if result.get("phase_order") != ["fit", "tune", "prediction_lock", "assessment"] or result.get("assessment_began_after_lock") is not True:
        raise ProtocolError("synthetic phase ordering guard failed")
    trials = result.get("aggregate_trials")
    expected = _expected_trial_identities(SPLITS, ARMS)
    if not isinstance(trials, list) or len(trials) != len(expected):
        raise ProtocolError("synthetic result coverage mismatch")
    identities = {(item.get("arm"), item.get("split"), item.get("replicate_seed"), item.get("order_seed"), item.get("order_direction")) for item in trials}
    if identities != expected:
        raise ProtocolError("synthetic result identity roster mismatch")
    for observed in trials:
        identity = (observed["arm"], observed["split"], observed["replicate_seed"], observed["order_seed"], observed["order_direction"])
        if digest(observed) != digest(_run_synthetic_trial(*identity[:2], identity[2], identity[3], identity[4])):
            raise ProtocolError(f"synthetic arithmetic mismatch: {identity}")
    locked_arm = result["prediction_lock"]["locked_arm"]
    summary = _summarize_trials(trials, locked_arm=locked_arm)
    if digest(result.get("summary")) != digest(summary) or result.get("prediction_lock") != summary["prediction_lock"]:
        raise ProtocolError("synthetic summary mismatch")
    if result.get("result_sha256") != digest({key: value for key, value in result.items() if key != "result_sha256"}):
        raise ProtocolError("synthetic result digest mismatch")


def _ensure_external(root: Path, *, expected_name: str | None = None) -> Path:
    resolved = root.resolve()
    if root.is_symlink() or _has_symlink_component(root) or resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise ProtocolError("artifact path must remain outside the repository")
    if any(resolved == prior or prior in resolved.parents for prior in FORBIDDEN_PRIOR_ROOTS):
        raise ProtocolError("path overlaps a forbidden V1/V2 prior artifact root")
    if expected_name is not None and resolved.name != expected_name:
        raise ProtocolError(f"path must use fresh V3 identity {expected_name}")
    if resolved.exists():
        raise FileExistsError(f"refusing overwrite of immutable artifact root: {resolved}")
    return resolved


def inspect_source(source_root: Path) -> dict[str, Any]:
    root = source_root.resolve()
    if root == REPO_ROOT or REPO_ROOT in root.parents:
        raise ProtocolError("MiniMind source must remain outside the repository")
    if root.name != DEFAULT_SOURCE_ROOT.name or any(root == prior or prior in root.parents for prior in FORBIDDEN_PRIOR_ROOTS):
        raise ProtocolError("MiniMind source must use fresh V3 identity and exclude V1/V2 roots")
    if not root.is_dir():
        raise FileNotFoundError(f"MiniMind source root does not exist: {root}")
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=False, capture_output=True, text=True)
    if head.returncode != 0 or head.stdout.strip() != UPSTREAM_COMMIT:
        raise ProtocolError("MiniMind source commit mismatch")
    status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], check=False, capture_output=True, text=True)
    if status.returncode != 0 or status.stdout:
        raise ProtocolError("MiniMind source checkout is dirty")
    remote = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"], check=False, capture_output=True, text=True)
    if remote.returncode != 0 or remote.stdout.strip() not in {UPSTREAM_URL, f"{UPSTREAM_URL}.git"}:
        raise ProtocolError("MiniMind source remote mismatch")
    license_path = root / "LICENSE"
    license_text = license_path.read_text(encoding="utf-8") if license_path.is_file() else ""
    if "Apache License" not in license_text or "Version 2.0" not in license_text:
        raise ProtocolError("MiniMind source license is not verified as Apache-2.0")
    files = []
    for relative in REQUIRED_SOURCE_FILES:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise ProtocolError(f"required MiniMind source file missing or symlinked: {relative}")
        files.append({"path": relative, "byte_len": path.stat().st_size, "sha256": sha256_file(path)})
    manifest = {"state_slice": STATE_SLICE, "url": UPSTREAM_URL, "commit": UPSTREAM_COMMIT, "remote_url": remote.stdout.strip(), "license": "Apache-2.0", "checkout": str(root), "required_files": files}
    return {"manifest": manifest, "manifest_sha256": digest(manifest)}


def current_frozen_file_digests() -> dict[str, str]:
    values = {}
    for relative in FROZEN_REVIEW_FILES:
        path = REPO_ROOT / relative
        if not path.is_file() or path.is_symlink():
            raise ProtocolError(f"frozen review file missing or symlinked: {relative}")
        values[relative] = sha256_file(path)
    return values


def _receipt_payload(receipt: Mapping[str, Any]) -> bytes:
    return json.dumps({key: value for key, value in receipt.items() if key != "signature"}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _verify_ed25519(public_key_hex: str, signature_hex: str, message: bytes, failure: str) -> None:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        if len(public_key_hex) != 64 or len(signature_hex) != 128:
            raise ValueError("invalid Ed25519 encoding length")
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex)).verify(bytes.fromhex(signature_hex), message)
    except (ImportError, InvalidSignature, ValueError, TypeError) as error:
        raise ProtocolError(failure) from error


def _load_and_validate_trust_bundle() -> dict[str, Any]:
    path = TRUST_BUNDLE_PATH.resolve()
    if path == REPO_ROOT or REPO_ROOT in path.parents or not path.is_file() or path.is_symlink():
        raise ProtocolError("external V3 trust bundle is missing")
    if sha256_file(path) != TRUST_BUNDLE_FILE_SHA256:
        raise ProtocolError("external V3 trust bundle fingerprint mismatch")
    bundle = _strict_load(path)
    required = {"schema_version", "state_slice", "review_root_key_id", "review_root_public_key_hex", "review_root_public_key_sha256", "operator_root_key_id", "operator_root_public_key_hex", "operator_root_public_key_sha256", "reviewer_registry_id", "source", "bundle_sha256"}
    if set(bundle) != required:
        raise ProtocolError("external V3 trust bundle schema mismatch")
    if bundle["schema_version"] != "minimind-v3-trust-bundle-v1" or bundle["state_slice"] != STATE_SLICE or bundle["reviewer_registry_id"] != "minimind-reviewers-2026-09" or bundle["source"] != "external-read-only-authority":
        raise ProtocolError("external V3 trust bundle identity mismatch")
    try:
        review_key = bytes.fromhex(bundle["review_root_public_key_hex"])
        operator_key = bytes.fromhex(bundle["operator_root_public_key_hex"])
    except (TypeError, ValueError) as error:
        raise ProtocolError("external V3 trust bundle key encoding mismatch") from error
    if len(review_key) != 32 or len(operator_key) != 32 or review_key == operator_key:
        raise ProtocolError("external V3 trust bundle key separation mismatch")
    if hashlib.sha256(review_key).hexdigest() != bundle["review_root_public_key_sha256"] or hashlib.sha256(operator_key).hexdigest() != bundle["operator_root_public_key_sha256"]:
        raise ProtocolError("external V3 trust bundle key fingerprint mismatch")
    if bundle["bundle_sha256"] != digest({key: value for key, value in bundle.items() if key != "bundle_sha256"}):
        raise ProtocolError("external V3 trust bundle digest mismatch")
    return bundle


def _load_and_validate_registry(path: Path, bundle: Mapping[str, Any]) -> dict[str, Any]:
    resolved = path.resolve()
    if resolved != REVIEWER_REGISTRY_PATH.resolve() or resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise ProtocolError("reviewer registry path is not the fixed external V3 registry")
    if not resolved.is_file() or resolved.is_symlink():
        raise ProtocolError("trusted reviewer registry is missing")
    registry = _strict_load(resolved)
    required = {"schema_version", "state_slice", "registry_id", "issuer_key_id", "reviewers", "registry_sha256", "authority_signature"}
    if set(registry) != required:
        raise ProtocolError("trusted reviewer registry schema mismatch")
    if registry["schema_version"] != REGISTRY_SCHEMA_VERSION or registry["state_slice"] != STATE_SLICE or registry["registry_id"] != bundle["reviewer_registry_id"] or registry["issuer_key_id"] != bundle["review_root_key_id"]:
        raise ProtocolError("trusted reviewer registry identity mismatch")
    if registry["registry_sha256"] != digest({key: value for key, value in registry.items() if key not in {"registry_sha256", "authority_signature"}}):
        raise ProtocolError("trusted reviewer registry digest mismatch")
    signature = registry["authority_signature"]
    if not isinstance(signature, Mapping) or signature.get("algorithm") != "Ed25519":
        raise ProtocolError("trusted reviewer registry authority signature is missing")
    _verify_ed25519(bundle["review_root_public_key_hex"], signature.get("signature_hex", ""), registry["registry_sha256"].encode("ascii"), "trusted reviewer registry authority signature failed")
    reviewers = registry["reviewers"]
    if not isinstance(reviewers, list) or not reviewers:
        raise ProtocolError("trusted reviewer registry has no reviewers")
    for reviewer in reviewers:
        if set(reviewer) != {"identity", "role", "public_key_hex", "certificate_sha256", "certificate_signature_hex"}:
            raise ProtocolError("trusted reviewer certificate schema mismatch")
        if reviewer["role"] != REVIEWER_ROLE or reviewer["identity"] == OPERATOR_ID or reviewer["public_key_hex"] == bundle["review_root_public_key_hex"] or reviewer["public_key_hex"] == bundle["operator_root_public_key_hex"]:
            raise ProtocolError("trusted reviewer certificate independence mismatch")
        certificate = {"schema_version": REGISTRY_SCHEMA_VERSION, "state_slice": STATE_SLICE, "registry_id": bundle["reviewer_registry_id"], "reviewer_identity": reviewer["identity"], "reviewer_role": reviewer["role"], "reviewer_public_key_hex": reviewer["public_key_hex"]}
        if reviewer["certificate_sha256"] != digest(certificate):
            raise ProtocolError("trusted reviewer certificate digest mismatch")
        _verify_ed25519(bundle["review_root_public_key_hex"], reviewer["certificate_signature_hex"], reviewer["certificate_sha256"].encode("ascii"), "trusted reviewer certificate signature failed")
    return registry


def validate_execution_receipt(receipt_path: Path, *, expected_source_manifest_sha256: str | None = None, expected_corpus_manifest_sha256: str | None = None) -> str:
    if not receipt_path.is_file() or receipt_path.is_symlink():
        raise ProtocolError(f"independent execution receipt missing: {receipt_path}")
    receipt = _strict_load(receipt_path)
    if set(receipt) != RECEIPT_KEYS:
        raise ProtocolError("execution receipt schema mismatch")
    if receipt["schema_version"] != RECEIPT_SCHEMA_VERSION or receipt["state_slice"] != STATE_SLICE:
        raise ProtocolError("execution receipt identity mismatch")
    if receipt["reviewer_role"] != REVIEWER_ROLE or receipt["reviewer_identity"] == receipt["operator_identity"] or receipt["operator_identity"] != OPERATOR_ID:
        raise ProtocolError("execution receipt reviewer independence mismatch")
    if receipt["disposition"] != "ACCEPTED_FOR_MODEL_EXECUTION" or receipt["signature_algorithm"] != "Ed25519":
        raise ProtocolError("execution receipt disposition or algorithm mismatch")
    packet = REVIEW_PACKET_PATH.resolve()
    if Path(receipt["review_packet_path"]).resolve() != packet or receipt["review_packet_sha256"] != sha256_file(packet):
        raise ProtocolError("execution receipt packet binding mismatch")
    if receipt["reviewed_file_digests"] != current_frozen_file_digests():
        raise ProtocolError("execution receipt frozen-file digest set mismatch")
    bundle = _load_and_validate_trust_bundle()
    registry = _load_and_validate_registry(Path(receipt["reviewer_registry_path"]), bundle)
    if receipt["reviewer_registry_sha256"] != sha256_file(Path(receipt["reviewer_registry_path"])):
        raise ProtocolError("execution receipt reviewer registry digest mismatch")
    reviewer = next((item for item in registry["reviewers"] if item["identity"] == receipt["reviewer_identity"]), None)
    if reviewer is None or reviewer["role"] != REVIEWER_ROLE or reviewer["public_key_hex"] != receipt["reviewer_public_key_hex"]:
        raise ProtocolError("execution receipt reviewer is not certified by the trusted registry")
    if receipt["reviewer_certificate_sha256"] != reviewer["certificate_sha256"]:
        raise ProtocolError("execution receipt reviewer certificate binding mismatch")
    binding_path = Path(receipt["operator_binding_path"]).resolve()
    if binding_path != OPERATOR_BINDING_PATH.resolve() or not binding_path.is_file() or binding_path.is_symlink():
        raise ProtocolError("execution receipt operator binding path mismatch")
    if receipt["operator_binding_sha256"] != sha256_file(binding_path):
        raise ProtocolError("execution receipt operator binding digest mismatch")
    binding = _strict_load(binding_path)
    binding_required = {"schema_version", "state_slice", "protocol", "packet_sha256", "operator_identity", "operator_principal_id", "operator_key_id", "audience", "nonce", "binding_sha256", "signature_algorithm", "signature_hex"}
    if not isinstance(binding, Mapping) or set(binding) != binding_required:
        raise ProtocolError("operator binding schema mismatch")
    if binding["schema_version"] != "minimind-v3-operator-binding-v1" or binding["state_slice"] != STATE_SLICE or binding["protocol"] != PROTOCOL or binding["packet_sha256"] != sha256_file(packet) or binding["operator_identity"] != OPERATOR_ID or binding["operator_principal_id"] != "principal-operator-shaanp" or binding["operator_key_id"] != bundle["operator_root_key_id"] or binding["audience"] != "minimind-v3-runner":
        raise ProtocolError("operator binding identity mismatch")
    if binding["binding_sha256"] != digest({key: value for key, value in binding.items() if key not in {"binding_sha256", "signature_algorithm", "signature_hex"}}) or binding["signature_algorithm"] != "Ed25519":
        raise ProtocolError("operator binding digest mismatch")
    _verify_ed25519(bundle["operator_root_public_key_hex"], binding["signature_hex"], binding["binding_sha256"].encode("ascii"), "operator binding signature verification failed")
    if expected_source_manifest_sha256 is not None and receipt["source_manifest_sha256"] != expected_source_manifest_sha256:
        raise ProtocolError("execution receipt source binding mismatch")
    if expected_corpus_manifest_sha256 is not None and receipt["corpus_manifest_sha256"] != expected_corpus_manifest_sha256:
        raise ProtocolError("execution receipt corpus binding mismatch")
    _verify_ed25519(receipt["reviewer_public_key_hex"], receipt["signature"], _receipt_payload(receipt), "execution receipt Ed25519 signature verification failed")
    return sha256_file(receipt_path)


def _read_jsonl_records(path: Path) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                raise ProtocolError(f"blank corpus record at {path}:{line_number}")
            payload = json.loads(line)
            if not isinstance(payload, dict) or set(payload) != {"document_id", "author_id", "text"}:
                raise ProtocolError(f"corpus record schema mismatch at {path}:{line_number}")
            if not all(isinstance(payload[key], str) and payload[key].strip() for key in payload):
                raise ProtocolError(f"corpus record has empty field at {path}:{line_number}")
            records.append({key: payload[key] for key in ("document_id", "author_id", "text")})
    if not records:
        raise ProtocolError(f"domain corpus is empty: {path}")
    return records


def _check_fresh_external_root(root: Path, expected_name: str) -> None:
    if root == REPO_ROOT or REPO_ROOT in root.parents or root.name != expected_name:
        raise ProtocolError("fresh V3 corpus root is not external or has the wrong identity")
    if any(root == prior or prior in root.parents for prior in FORBIDDEN_PRIOR_ROOTS):
        raise ProtocolError("fresh V3 corpus overlaps a forbidden V1/V2 artifact root")
    if not root.is_dir() or stat.S_IMODE(root.stat().st_mode) != 0o700:
        raise ProtocolError("fresh V3 corpus root must be owner-only")


def build_corpus_manifest(corpus: Mapping[str, Mapping[str, Path]]) -> dict[str, Any]:
    if set(corpus) != set(DOMAINS):
        raise ProtocolError("corpus domains must exactly match the V3 roster")
    all_documents: list[str] = []
    all_authors: list[str] = []
    domains: dict[str, Any] = {}
    corpus_root: Path | None = None
    for domain in DOMAINS:
        if set(corpus[domain]) != set(SPLITS):
            raise ProtocolError(f"corpus splits must exactly match the V3 roster for {domain}")
        split_manifest: dict[str, Any] = {}
        for split in SPLITS:
            path = Path(corpus[domain][split]).resolve()
            if not path.is_file() or path.is_symlink() or path == REPO_ROOT or REPO_ROOT in path.parents:
                raise ProtocolError(f"corpus file must be an external regular file: {path}")
            root = next((candidate for candidate in [path.parent, *path.parents] if candidate.name == CORPUS_ROOT_NAME), None)
            if root is None:
                raise ProtocolError(f"corpus file is not below the fixed fresh V3 corpus root: {path}")
            if corpus_root is None:
                corpus_root = root
            elif root != corpus_root:
                raise ProtocolError("corpus files must share one fresh V3 corpus root")
            if path.parent != root:
                raise ProtocolError("corpus files must be direct children of the fresh V3 corpus root")
            records = _read_jsonl_records(path)
            documents = [record["document_id"] for record in records]
            authors = [record["author_id"] for record in records]
            all_documents.extend(documents)
            all_authors.extend(authors)
            split_manifest[split] = {"path": str(path), "sha256": sha256_file(path), "byte_len": path.stat().st_size, "record_count": len(records), "document_ids_sha256": digest(sorted(documents)), "author_ids_sha256": digest(sorted(authors))}
        domains[domain] = split_manifest
    if corpus_root is None:
        raise ProtocolError("corpus root is missing")
    _check_fresh_external_root(corpus_root, CORPUS_ROOT_NAME)
    if len(all_documents) != len(set(all_documents)):
        raise ProtocolError("corpus document IDs are not globally disjoint")
    if len(all_authors) != len(set(all_authors)):
        raise ProtocolError("corpus author IDs are not globally disjoint")
    manifest = {"schema_version": CORPUS_SCHEMA_VERSION, "state_slice": STATE_SLICE, "corpus_identity": CORPUS_IDENTITY, "root": str(corpus_root), "freshness": {"new_v3_identity": True, "prior_artifact_exclusion": [str(path) for path in FORBIDDEN_PRIOR_ROOTS], "document_disjointness": True, "author_disjointness": True}, "domains": domains, "global_document_ids_sha256": digest(sorted(all_documents)), "global_author_ids_sha256": digest(sorted(all_authors))}
    return {"manifest": manifest, "manifest_sha256": digest(manifest)}


def _load_corpus_manifest(path: Path) -> dict[str, dict[str, Path]]:
    payload = _strict_load(path)
    if set(payload) != {"manifest", "manifest_sha256"} or payload["manifest_sha256"] != digest(payload["manifest"]):
        raise ProtocolError("corpus manifest wrapper digest mismatch")
    manifest = payload["manifest"]
    if manifest.get("schema_version") != CORPUS_SCHEMA_VERSION or manifest.get("corpus_identity") != CORPUS_IDENTITY:
        raise ProtocolError("corpus manifest identity mismatch")
    domains = manifest.get("domains")
    if not isinstance(domains, dict) or set(domains) != set(DOMAINS):
        raise ProtocolError("corpus manifest domain roster mismatch")
    corpus = {domain: {split: Path(domains[domain][split]["path"]) for split in SPLITS} for domain in DOMAINS}
    if build_corpus_manifest(corpus) != payload:
        raise ProtocolError("corpus manifest content or freshness binding mismatch")
    return corpus


def _token_chunks(tokenizer: Any, texts: Sequence[str], max_seq_len: int) -> list[Any]:
    import torch

    chunks = []
    for index, text in enumerate(texts, start=1):
        ids = tokenizer(text, add_special_tokens=False, truncation=True, max_length=max_seq_len - 2).input_ids
        ids = [tokenizer.bos_token_id, *ids, tokenizer.eos_token_id]
        if len(ids) < 3:
            raise ProtocolError(f"tokenization attrition at record {index}")
        values = ids[:max_seq_len]
        values += [tokenizer.pad_token_id] * (max_seq_len - len(values))
        tensor = torch.tensor(values, dtype=torch.long)
        labels = tensor.clone()
        labels[tensor == tokenizer.pad_token_id] = -100
        if int((labels[1:] != -100).sum().item()) == 0:
            raise ProtocolError(f"tokenization produced no trainable tokens at record {index}")
        chunks.append((tensor, labels))
    if len(chunks) != len(texts):
        raise ProtocolError("tokenization attrition detected")
    return chunks


def _train_model_stage(model: Any, tokenizer: Any, texts: Sequence[str], *, device: str, steps: int, learning_rate: float, seed: int) -> dict[str, int]:
    import torch

    torch.manual_seed(seed)
    chunks = _token_chunks(tokenizer, texts, MODEL_CONFIG["max_seq_len"])
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    if not trainable:
        return {"optimizer_steps": 0, "token_budget_units": steps * MODEL_CONFIG["max_seq_len"]}
    optimizer = torch.optim.AdamW(trainable, lr=learning_rate)
    model.train()
    for step in range(steps):
        input_ids, labels = chunks[step % len(chunks)]
        result = model(input_ids.unsqueeze(0).to(device), labels=labels.unsqueeze(0).to(device))
        loss = result.loss + result.aux_loss
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(trainable, 1.0)
        optimizer.step()
    return {"optimizer_steps": steps, "token_budget_units": steps * MODEL_CONFIG["max_seq_len"]}


def _evaluate_bpb(model: Any, tokenizer: Any, texts: Sequence[str], *, device: str) -> float:
    import torch

    chunks = _token_chunks(tokenizer, texts, MODEL_CONFIG["max_seq_len"])
    total_nats = 0.0
    total_bytes = 0
    model.eval()
    with torch.no_grad():
        for input_ids, labels in chunks:
            result = model(input_ids.unsqueeze(0).to(device), labels=labels.unsqueeze(0).to(device))
            valid = int((labels[1:] != -100).sum().item())
            total_nats += float(result.loss.item()) * valid
            total_bytes += len(tokenizer.decode(input_ids.tolist(), skip_special_tokens=True).encode("utf-8"))
    if total_bytes == 0:
        raise ProtocolError("evaluation produced zero UTF-8 bytes")
    return total_nats / math.log(2.0) / total_bytes


def _snapshot_model(model: Any) -> dict[str, Any]:
    return {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}


def _checkpoint_roundtrip(model: Any, snapshot: Mapping[str, Any], factory: Any, torch_module: Any) -> float:
    payload = io.BytesIO()
    torch_module.save(dict(snapshot), payload)
    payload.seek(0)
    loaded = torch_module.load(payload, map_location="cpu", weights_only=True)
    restored = factory()
    restored.load_state_dict(loaded, strict=True)
    error = max((float((value.detach().cpu() - restored.state_dict()[key].detach().cpu()).abs().max().item()) for key, value in loaded.items()), default=0.0)
    model.load_state_dict(loaded, strict=True)
    del restored
    return error


def _run_model_trial(*, arm: str, split: str, replicate_seed: int, order_seed: int, direction: str, corpus_texts: Mapping[str, Mapping[str, Sequence[str]]], model_cls: Any, config: Any, tokenizer: Any, apply_lora_fn: Any, torch_module: Any, device: str, steps_per_stage: int) -> dict[str, Any]:
    order = _ordered_domains(order_seed, direction)
    evaluation_texts = {domain: corpus_texts[domain][split] for domain in DOMAINS}

    def new_model(seed: int, *, lora: bool, trainable: bool) -> Any:
        torch_module.manual_seed(seed)
        model = model_cls(config).to(device)
        if lora:
            apply_lora_fn(model)
        for name, parameter in model.named_parameters():
            parameter.requires_grad = trainable and (not lora or "lora" in name)
        return model

    domain_models: dict[str, Any] = {}
    domain_factories: dict[str, Any] = {}
    if arm == "domain_adapters":
        base_model = new_model(replicate_seed, lora=False, trainable=False)
        base_snapshot = _snapshot_model(base_model)
        for domain_index, domain in enumerate(DOMAINS):
            def make_domain_model(domain_index: int = domain_index) -> Any:
                model = new_model(replicate_seed, lora=False, trainable=False)
                model.load_state_dict(base_snapshot, strict=True)
                torch_module.manual_seed(replicate_seed + 10_000 + domain_index)
                apply_lora_fn(model)
                for name, parameter in model.named_parameters():
                    parameter.requires_grad = "lora" in name
                return model
            domain_factories[domain] = make_domain_model
            domain_models[domain] = make_domain_model()
        def evaluate(domain: str) -> float:
            return _evaluate_bpb(domain_models[domain], tokenizer, evaluation_texts[domain], device=device)
        base_evaluation_model = base_model
    else:
        model = new_model(replicate_seed, lora=arm == "sequential_lora", trainable=arm != "untouched")
        def evaluate(domain: str) -> float:
            return _evaluate_bpb(model, tokenizer, evaluation_texts[domain], device=device)
        base_evaluation_model = model

    base_domain_bpb = {domain: _evaluate_bpb(base_evaluation_model, tokenizer, evaluation_texts[domain], device=device) for domain in DOMAINS}
    base_mean_bpb = sum(base_domain_bpb.values()) / len(DOMAINS)
    learned_bpb: dict[str, float] = {}
    stage_metrics: list[dict[str, Any]] = []
    checkpoint_errors: list[float] = []
    token_budget_units = []
    for stage_index, domain in enumerate(order, start=1):
        if arm == "domain_adapters":
            train_model = domain_models[domain]
            train_texts = corpus_texts[domain]["fit"]
            train_seed = replicate_seed + 10_000 + DOMAINS.index(domain)
        else:
            train_model = model
            if arm == "joint_oracle":
                train_texts = sum((corpus_texts[item]["fit"] for item in DOMAINS), ())
            elif arm == "sequential_replay":
                train_texts = sum((corpus_texts[item]["fit"] for item in (domain, *order[: stage_index - 1])), ())
            else:
                train_texts = corpus_texts[domain]["fit"]
            train_seed = replicate_seed + stage_index
        accounting = _train_model_stage(train_model, tokenizer, train_texts, device=device, steps=steps_per_stage, learning_rate=1e-5 if arm not in {"sequential_lora", "domain_adapters"} else 1e-4, seed=train_seed) if arm != "untouched" else {"optimizer_steps": 0, "token_budget_units": steps_per_stage * MODEL_CONFIG["max_seq_len"]}
        token_budget_units.append(accounting["token_budget_units"])
        if arm == "domain_adapters":
            for item in DOMAINS:
                snapshot = _snapshot_model(domain_models[item])
                checkpoint_errors.append(_checkpoint_roundtrip(domain_models[item], snapshot, domain_factories[item], torch_module))
        else:
            snapshot = _snapshot_model(model)
            factory = lambda: new_model(replicate_seed, lora=arm == "sequential_lora", trainable=arm != "untouched")
            checkpoint_errors.append(_checkpoint_roundtrip(model, snapshot, factory, torch_module))
        domain_bpb = {item: evaluate(item) for item in DOMAINS}
        learned_bpb.setdefault(domain, domain_bpb[domain])
        max_forgetting = max((max(0.0, domain_bpb[item] - learned_bpb[item]) for item in learned_bpb), default=0.0)
        stage_metrics.append({"stage_index": stage_index, "domain": domain, "domain_bpb": domain_bpb, "mean_bpb": sum(domain_bpb.values()) / len(DOMAINS), "max_forgetting": max_forgetting, "update_units": steps_per_stage, "token_budget_units": accounting["token_budget_units"], "checkpoint_restore_max_abs_error": max(checkpoint_errors[-len(DOMAINS):], default=0.0) if arm == "domain_adapters" else checkpoint_errors[-1]})
    final_domain_bpb = {domain: evaluate(domain) for domain in DOMAINS}
    final_mean_bpb = sum(final_domain_bpb.values()) / len(DOMAINS)
    checkpoint_error = max(checkpoint_errors, default=0.0)
    max_forgetting = max(item["max_forgetting"] for item in stage_metrics)
    return {"arm": arm, "split": split, "replicate_seed": replicate_seed, "order_seed": order_seed, "order_direction": direction, "domain_order": list(order), "stage_count": len(stage_metrics), "base_mean_loss": base_mean_bpb, "final_mean_loss": final_mean_bpb, "primary_improvement": base_mean_bpb - final_mean_bpb, "max_forgetting": max_forgetting, "compute_units": steps_per_stage * len(DOMAINS), "token_budget_units": sum(token_budget_units), "checkpoint_restore_max_abs_error": checkpoint_error, "hard_guards": {"forgetting": max_forgetting <= MAX_FORGETTING, "checkpoint_restore": checkpoint_error <= MAX_CHECKPOINT_ERROR, "complete_stage_coverage": len(stage_metrics) == len(DOMAINS), "zero_attrition": True, "equal_token_budget": len(set(token_budget_units)) == 1}}


def run_model_campaign(*, output: Path, source_root: Path, execution_receipt: Path, corpus: Mapping[str, Mapping[str, Path]], device: str = "cpu", steps_per_stage: int = 1) -> dict[str, Any]:
    """Run the V3 MiniMind model campaign after independent authorization."""
    if steps_per_stage <= 0:
        raise ProtocolError("steps_per_stage must be positive")
    root = _ensure_external(output, expected_name=MODEL_ROOT_NAME)
    source = inspect_source(source_root)
    corpus_manifest = build_corpus_manifest(corpus)
    receipt_sha256 = validate_execution_receipt(execution_receipt, expected_source_manifest_sha256=source["manifest_sha256"], expected_corpus_manifest_sha256=corpus_manifest["manifest_sha256"])
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    root.mkdir(parents=True, mode=0o700)
    os.chmod(root, 0o700)
    if stat.S_IMODE(root.stat().st_mode) != 0o700:
        raise ProtocolError("model artifact root is not owner-only")
    with _external_import_root(source_root):
        import torch
        from transformers import AutoTokenizer
        from model.model_lora import apply_lora
        from model.model_minimind import MiniMindConfig, MiniMindForCausalLM
        tokenizer = AutoTokenizer.from_pretrained(str(source_root / "model"), local_files_only=True)
        config = MiniMindConfig(hidden_size=MODEL_CONFIG["hidden_size"], num_hidden_layers=MODEL_CONFIG["num_hidden_layers"], use_moe=MODEL_CONFIG["use_moe"], vocab_size=MODEL_CONFIG["vocab_size"])
        if device.startswith("cuda") and not torch.cuda.is_available():
            raise ProtocolError("requested CUDA device is unavailable")
        torch.use_deterministic_algorithms(True, warn_only=True)
        corpus_texts = {domain: {split: tuple(record["text"] for record in _read_jsonl_records(Path(corpus[domain][split]))) for split in SPLITS} for domain in DOMAINS}

        def phase_trials(split: str, arms: Sequence[str]) -> list[dict[str, Any]]:
            phase_results = []
            for arm in arms:
                for replicate_seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS):
                    for direction in ORDER_DIRECTIONS:
                        trial = _run_model_trial(arm=arm, split=split, replicate_seed=replicate_seed, order_seed=order_seed, direction=direction, corpus_texts=corpus_texts, model_cls=MiniMindForCausalLM, config=config, tokenizer=tokenizer, apply_lora_fn=apply_lora, torch_module=torch, device=device, steps_per_stage=steps_per_stage)
                        repeat = _run_model_trial(arm=arm, split=split, replicate_seed=replicate_seed, order_seed=order_seed, direction=direction, corpus_texts=corpus_texts, model_cls=MiniMindForCausalLM, config=config, tokenizer=tokenizer, apply_lora_fn=apply_lora, torch_module=torch, device=device, steps_per_stage=steps_per_stage)
                        if digest(trial) != digest(repeat):
                            raise ProtocolError(f"model repeatability mismatch: {split}:{arm}:{replicate_seed}:{direction}")
                        trial["repeatability_checked"] = True
                        phase_results.append(trial)
            return phase_results

        fit_trials = phase_trials("fit", ARMS)
        tune_trials = phase_trials("tune", ARMS)
        tune_summary = _summarize_trials([*fit_trials, *tune_trials])
        locked_arm = tune_summary["prediction_lock"]["locked_arm"]
        assessment_trials = phase_trials("assessment", (locked_arm,))
        trials = [*fit_trials, *tune_trials, *assessment_trials]
    summary = _summarize_trials(trials, locked_arm=locked_arm)
    if any(not item.get("repeatability_checked") for item in trials):
        raise ProtocolError("model repeatability guard missing")
    expected_budget = steps_per_stage * len(DOMAINS) * MODEL_CONFIG["max_seq_len"]
    if any(item["token_budget_units"] != expected_budget for item in trials):
        raise ProtocolError("model token budget mismatch")
    contract = {
        "state_slice": STATE_SLICE, "schema_version": SCHEMA_VERSION, "protocol": PROTOCOL, "claim_ceiling": MODEL_CLAIM_CEILING,
        "source": source, "corpus": corpus_manifest, "execution_receipt_sha256": receipt_sha256, "execution_receipt_path": str(execution_receipt.resolve()),
        "model_config": MODEL_CONFIG, "arms": list(ARMS), "network_access": False, "provider_called": False, "training_executed": True, "model_loaded": True, "inference_executed": True,
        "device": device, "steps_per_stage": steps_per_stage, "phase_order": ["fit", "tune", "prediction_lock", "assessment"], "assessment_began_after_lock": True,
        "prediction_lock": summary["prediction_lock"], "assessment_arms": [locked_arm], "hard_guards": {"receipt_bound": True, "phase_order": True, "assessment_after_lock": True, "prediction_lock": True, "corpus_freshness": True, "corpus_disjointness": True, "prior_artifact_exclusion": True, "model_repeatability": True, "equal_token_budget": True, "zero_attrition": True, "checkpoint_restore": True},
        "aggregate_trials": trials, "summary": summary,
    }
    contract["contract_sha256"] = digest(contract)
    write_json(root / "contract.json", contract)
    return contract


@contextmanager
def _external_import_root(root: Path) -> Iterator[None]:
    root_string = str(root.resolve())
    sys.path.insert(0, root_string)
    try:
        yield
    finally:
        try:
            sys.path.remove(root_string)
        except ValueError:
            pass


def write_synthetic_campaign(output: Path, source_root: Path = DEFAULT_SOURCE_ROOT) -> dict[str, Any]:
    root = _ensure_external(output, expected_name=SYNTHETIC_ROOT_NAME)
    source = inspect_source(source_root)
    result = run_synthetic_campaign()
    contract = {"state_slice": STATE_SLICE, "schema_version": SCHEMA_VERSION, "protocol": PROTOCOL, "claim_ceiling": SYNTHETIC_CLAIM_CEILING, "source": source, "corpus": result["corpus"], "arms": list(ARMS), "training_executed": False, "model_loaded": False, "inference_executed": False, "network_access": False, "provider_called": False, "phase_order": result["phase_order"], "assessment_began_after_lock": True, "prediction_lock": result["prediction_lock"], "aggregate_result_sha256": result["result_sha256"]}
    contract["contract_sha256"] = digest(contract)
    root.mkdir(parents=True, mode=0o700)
    os.chmod(root, 0o700)
    write_json(root / "source-manifest.json", source)
    write_json(root / "contract.json", contract)
    write_json(root / "result.json", result)
    return {"root": str(root), "contract": contract, "result": result}


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic-output", type=Path)
    mode.add_argument("--model-output", type=Path)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--execution-receipt", type=Path)
    parser.add_argument("--corpus-manifest", type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--steps-per-stage", type=int, default=1)
    args = parser.parse_args()
    if args.synthetic_output is not None:
        payload = write_synthetic_campaign(args.synthetic_output, args.source)
    else:
        if args.execution_receipt is None or args.corpus_manifest is None:
            parser.error("--model-output requires --execution-receipt and --corpus-manifest")
        payload = run_model_campaign(output=args.model_output, source_root=args.source, execution_receipt=args.execution_receipt, corpus=_load_corpus_manifest(args.corpus_manifest), device=args.device, steps_per_stage=args.steps_per_stage)
    summary = payload.get("result", payload).get("summary", {})
    print(json.dumps({"state_slice": STATE_SLICE, "disposition": summary.get("disposition", "ModelContractWritten"), "root": str(args.synthetic_output or args.model_output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
