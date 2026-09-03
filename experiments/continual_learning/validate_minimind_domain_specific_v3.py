#!/usr/bin/env python3
"""Independent readback validator for MiniMind continual-learning V3.

State slice: continual-learning-minimind-domain-specific-v3.

This module intentionally duplicates the deterministic synthetic arithmetic and
custody checks instead of importing the runner. A valid result must pass the
independent implementation and every fixed schema check.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


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
REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_PACKET_PATH = REPO_ROOT / "docs/research/continual-learning/284-minimind-domain-specific-v3-review-packet.md"
REVIEWER_REGISTRY_PATH = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v3-reviewer-registry-20260902.json")
TRUST_BUNDLE_PATH = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v3-trust-bundle-20260902.json")
TRUST_BUNDLE_FILE_SHA256 = "6263ffeb3ca674f41b58f62f8f4b90f3a7f2903563677a0e4f8d9a4521d9ac27"
OPERATOR_BINDING_PATH = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v3-operator-binding-20260902.json")
CORPUS_IDENTITY = "continual-learning-minimind-domain-specific-v3-fresh-corpus-20260902"
CORPUS_ROOT_NAME = "continual-learning-minimind-domain-specific-v3-corpus-20260902"
SYNTHETIC_ROOT_NAME = "continual-learning-minimind-domain-specific-v3-synthetic-20260902"
MODEL_ROOT_NAME = "continual-learning-minimind-domain-specific-v3-model-20260902"
FORBIDDEN_PRIOR_ROOTS = tuple(Path(path).resolve() for path in (
    "/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v1-source-20260902",
    "/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v1-synthetic-20260902-r2",
    "/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v2-source-20260902",
    "/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v2-synthetic-20260902-r3",
))
FROZEN_REVIEW_FILES = (
    "docs/research/continual-learning/283-minimind-domain-specific-v3-protocol.md",
    "docs/research/continual-learning/284-minimind-domain-specific-v3-review-packet.md",
    "experiments/continual_learning/minimind_domain_specific_v3.py",
    "experiments/continual_learning/validate_minimind_domain_specific_v3.py",
    "experiments/continual_learning/tests/test_minimind_domain_specific_v3.py",
    "docs/research/continual-learning/285-minimind-domain-specific-v3-implementation-manifest.json",
    "AGENTS.md",
)
DOMAINS = ("materials", "clinical", "finance")
SPLITS = ("fit", "tune", "assessment")
ORDER_DIRECTIONS = ("forward", "reverse")
REPLICATE_SEEDS = (2026090207, 2026090208, 2026090209)
ORDER_SEEDS = (9611, 9612, 9613)
ARMS = ("untouched", "joint_oracle", "sequential_full", "sequential_lora", "sequential_replay", "domain_adapters")
VECTOR_DIMENSION = 8
MAX_FORGETTING = 0.25
MAX_ORDER_DELTA = 0.20
MAX_CHECKPOINT_ERROR = 1e-12
MAX_SEQ_LEN = 340
MODEL_CONFIG = {"model_name": "minimind-3-dense", "hidden_size": 768, "num_hidden_layers": 8, "use_moe": False, "vocab_size": 6400, "max_seq_len": MAX_SEQ_LEN}
REQUIRED_SOURCE_FILES = ("LICENSE", "requirements.txt", "model/model_minimind.py", "model/model_lora.py", "model/tokenizer.json", "model/tokenizer_config.json", "trainer/train_pretrain.py", "trainer/train_full_sft.py", "trainer/train_lora.py", "dataset/lm_dataset.py")
TRIAL_GUARD_KEYS = {"forgetting", "checkpoint_restore", "complete_stage_coverage", "zero_attrition", "equal_token_budget"}
MODEL_GUARD_KEYS = {"receipt_bound", "phase_order", "assessment_after_lock", "prediction_lock", "corpus_freshness", "corpus_disjointness", "prior_artifact_exclusion", "model_repeatability", "equal_token_budget", "zero_attrition", "checkpoint_restore"}
SYNTHETIC_RESULT_KEYS = {"state_slice", "schema_version", "protocol", "claim_ceiling", "source", "corpus", "arms", "replicate_seeds", "order_seeds", "training_executed", "model_loaded", "inference_executed", "network_access", "provider_called", "phase_order", "assessment_began_after_lock", "prediction_lock", "aggregate_trials", "summary", "result_sha256"}


class ValidationError(ValueError):
    """Raised when an artifact violates the V3 contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _strict_load(path: Path) -> Any:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(f"duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValidationError(f"non-finite JSON constant in {path}: {value}")

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates, parse_constant=reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"invalid JSON artifact: {path}") from error


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
    return tuple(_anchor()[component] + scale * _signed("target", domain, seed, component) + 0.015 * _signed("split-noise", domain, split, seed, component) for component in range(VECTOR_DIMENSION))


def _mean_vector(vectors: Sequence[Sequence[float]]) -> tuple[float, ...]:
    _require(bool(vectors), "cannot average an empty vector collection")
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
    _require(direction in ORDER_DIRECTIONS, "unknown order direction")
    indexed = list(enumerate(DOMAINS))
    indexed.sort(key=lambda item: (_unit("order", order_seed, item[1]), item[0]))
    if direction == "reverse":
        indexed.reverse()
    return tuple(domain for _, domain in indexed)


def _prediction_vector(arm: str, shared_state: Sequence[float], adapters: Mapping[str, Sequence[float]], domain: str) -> tuple[float, ...]:
    return _add(shared_state, adapters.get(domain, (0.0,) * VECTOR_DIMENSION)) if arm == "domain_adapters" else tuple(shared_state)


def _trial(arm: str, split: str, seed: int, order_seed: int, direction: str) -> dict[str, Any]:
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
            shared_state = _add(shared_state, _apply_mask(_scale(_sub(current_target, shared_state), 0.78), _domain_mask(domain)))
        elif arm == "sequential_replay":
            seen = [fit_targets[item] for item in order[: stage_index - 1]]
            shared_state = _add(shared_state, _scale(_sub(_mean_vector((current_target, *seen)), shared_state), 0.42))
        elif arm == "domain_adapters":
            before = adapters.get(domain, (0.0,) * VECTOR_DIMENSION)
            adapters[domain] = _add(before, _scale(_sub(_sub(current_target, base), before), 0.78))
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
        stage_metrics.append({"domain": domain, "domain_losses": domain_losses, "mean_loss": sum(domain_losses.values()) / len(DOMAINS), "max_forgetting": max_forgetting})
    base_mean_loss = sum(_loss(base, evaluation_targets[domain]) for domain in DOMAINS) / len(DOMAINS)
    final_mean_loss = stage_metrics[-1]["mean_loss"]
    max_forgetting = max(item["max_forgetting"] for item in stage_metrics)
    checkpoint_error = max(checkpoint_errors, default=0.0)
    return {"arm": arm, "split": split, "replicate_seed": seed, "order_seed": order_seed, "order_direction": direction, "domain_order": list(order), "stage_count": len(stage_metrics), "base_mean_loss": base_mean_loss, "final_mean_loss": final_mean_loss, "primary_improvement": base_mean_loss - final_mean_loss, "max_forgetting": max_forgetting, "compute_units": 9, "token_budget_units": 9 * MAX_SEQ_LEN, "checkpoint_restore_max_abs_error": checkpoint_error, "hard_guards": {"forgetting": max_forgetting <= MAX_FORGETTING, "checkpoint_restore": checkpoint_error <= MAX_CHECKPOINT_ERROR, "complete_stage_coverage": len(stage_metrics) == len(DOMAINS), "zero_attrition": True, "equal_token_budget": True}}


def _expected_identities(splits: Sequence[str], arms: Sequence[str]) -> set[tuple[Any, ...]]:
    return {(arm, split, seed, order_seed, direction) for split in splits for arm in arms for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS) for direction in ORDER_DIRECTIONS}


def _aggregate_summary(trials: Sequence[Mapping[str, Any]], locked_arm: str | None = None) -> dict[str, Any]:
    by_split_arm: dict[str, Any] = {}
    for split in ("fit", "tune"):
        for arm in ARMS:
            subset = [item for item in trials if item["split"] == split and item["arm"] == arm]
            _require(bool(subset), f"missing trials for {split}:{arm}")
            order_deltas = {}
            for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS):
                forward = next(item for item in subset if item["replicate_seed"] == seed and item["order_seed"] == order_seed and item["order_direction"] == "forward")
                reverse = next(item for item in subset if item["replicate_seed"] == seed and item["order_seed"] == order_seed and item["order_direction"] == "reverse")
                order_deltas[str(seed)] = abs(forward["final_mean_loss"] - reverse["final_mean_loss"])
            by_split_arm[f"{split}:{arm}"] = {"trial_count": len(subset), "mean_primary_improvement": sum(item["primary_improvement"] for item in subset) / len(subset), "mean_final_loss": sum(item["final_mean_loss"] for item in subset) / len(subset), "max_forgetting": max(item["max_forgetting"] for item in subset), "order_deltas": order_deltas, "max_order_delta": max(order_deltas.values()), "all_hard_guards_pass": all(set(item["hard_guards"]) == TRIAL_GUARD_KEYS and all(item["hard_guards"].values()) for item in subset) and max(order_deltas.values()) <= MAX_ORDER_DELTA}
    tune = {arm: by_split_arm[f"tune:{arm}"] for arm in ARMS}
    selected = min(ARMS, key=lambda arm: (tune[arm]["mean_final_loss"], ARMS.index(arm)))
    if locked_arm is not None:
        _require(selected == locked_arm, "assessment changed the precomputed tune lock")
    locked_arm = selected if locked_arm is None else locked_arm
    assessment = [item for item in trials if item["split"] == "assessment" and item["arm"] == locked_arm]
    _require(bool(assessment), "locked assessment aggregate is missing")
    order_deltas = {}
    for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS):
        forward = next(item for item in assessment if item["replicate_seed"] == seed and item["order_seed"] == order_seed and item["order_direction"] == "forward")
        reverse = next(item for item in assessment if item["replicate_seed"] == seed and item["order_seed"] == order_seed and item["order_direction"] == "reverse")
        order_deltas[str(seed)] = abs(forward["final_mean_loss"] - reverse["final_mean_loss"])
    assessment_summary = {"trial_count": len(assessment), "mean_primary_improvement": sum(item["primary_improvement"] for item in assessment) / len(assessment), "mean_final_loss": sum(item["final_mean_loss"] for item in assessment) / len(assessment), "max_forgetting": max(item["max_forgetting"] for item in assessment), "order_deltas": order_deltas, "max_order_delta": max(order_deltas.values()), "all_hard_guards_pass": all(set(item["hard_guards"]) == TRIAL_GUARD_KEYS and all(item["hard_guards"].values()) for item in assessment) and max(order_deltas.values()) <= MAX_ORDER_DELTA}
    by_split_arm[f"assessment:{locked_arm}"] = assessment_summary
    return {"by_split_arm": by_split_arm, "prediction_lock": {"selection_split": "tune", "locked_arm": locked_arm, "selection_metric": "mean_final_loss"}, "disposition": "SyntheticCandidate" if assessment_summary["all_hard_guards_pass"] and assessment_summary["mean_primary_improvement"] > 0.0 else "NoCandidate"}


def _validate_artifact_root(root: Path, allowed: set[str], expected_name: str) -> Path:
    resolved = root.resolve()
    _require(not root.is_symlink() and not _has_symlink_component(root), "artifact root must not use symlinked path components")
    _require(resolved != REPO_ROOT and REPO_ROOT not in resolved.parents, "artifact root must remain external")
    _require(resolved.name == expected_name, "artifact root identity mismatch")
    _require(not any(resolved == prior or prior in resolved.parents for prior in FORBIDDEN_PRIOR_ROOTS), "artifact root overlaps prior V1/V2 root")
    _require(resolved.is_dir() and stat.S_IMODE(resolved.stat().st_mode) == 0o700, "artifact root must be owner-only 0700")
    entries = list(resolved.iterdir())
    _require({entry.name for entry in entries} == allowed, "artifact root file set mismatch")
    for entry in entries:
        _require(entry.is_file() and not entry.is_symlink() and stat.S_ISREG(entry.stat().st_mode), f"artifact entry is not a regular file: {entry.name}")
        _require(entry.name not in {".DS_Store", "__pycache__"}, "artifact root contains hidden or cache output")
    return resolved


def _validate_source(observed: Mapping[str, Any]) -> None:
    _require(set(observed) == {"manifest", "manifest_sha256"}, "source manifest schema mismatch")
    manifest = observed["manifest"]
    _require(isinstance(manifest, dict) and observed["manifest_sha256"] == _digest(manifest), "source manifest digest mismatch")
    _require(manifest.get("state_slice") == STATE_SLICE and manifest.get("url") == UPSTREAM_URL and manifest.get("commit") == UPSTREAM_COMMIT and manifest.get("license") == "Apache-2.0", "source manifest identity mismatch")
    root = Path(manifest.get("checkout", "")).resolve()
    _require(root.name == "continual-learning-minimind-domain-specific-v3-source-20260902" and root.is_dir() and root != REPO_ROOT and REPO_ROOT not in root.parents, "source checkout path invalid")
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=False, capture_output=True, text=True)
    status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], check=False, capture_output=True, text=True)
    remote = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"], check=False, capture_output=True, text=True)
    _require(head.returncode == 0 and head.stdout.strip() == UPSTREAM_COMMIT and status.returncode == 0 and status.stdout == "" and remote.returncode == 0 and remote.stdout.strip() in {UPSTREAM_URL, f"{UPSTREAM_URL}.git"}, "source checkout identity mismatch")
    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    _require("Apache License" in license_text and "Version 2.0" in license_text, "source license mismatch")
    rows = manifest.get("required_files")
    _require(isinstance(rows, list) and [row.get("path") for row in rows] == list(REQUIRED_SOURCE_FILES), "source roster mismatch")
    for row in rows:
        path = root / row["path"]
        _require(path.is_file() and not path.is_symlink() and row.get("byte_len") == path.stat().st_size and row.get("sha256") == _sha256_file(path), f"source file digest mismatch: {row.get('path')}")


def _read_records(path: Path) -> list[dict[str, str]]:
    records = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            _require(bool(line.strip()), f"blank corpus record at {path}:{line_number}")
            payload = json.loads(line)
            _require(isinstance(payload, dict) and set(payload) == {"document_id", "author_id", "text"}, f"corpus record schema mismatch at {path}:{line_number}")
            _require(all(isinstance(payload[key], str) and payload[key].strip() for key in payload), f"corpus record empty field at {path}:{line_number}")
            records.append(payload)
    _require(bool(records), f"empty corpus file: {path}")
    return records


def _validate_corpus(observed: Mapping[str, Any]) -> None:
    _require(set(observed) == {"manifest", "manifest_sha256"}, "corpus manifest wrapper schema mismatch")
    manifest = observed["manifest"]
    _require(isinstance(manifest, dict) and observed["manifest_sha256"] == _digest(manifest), "corpus manifest digest mismatch")
    _require(manifest.get("schema_version") == CORPUS_SCHEMA_VERSION and manifest.get("state_slice") == STATE_SLICE and manifest.get("corpus_identity") == CORPUS_IDENTITY, "corpus identity mismatch")
    root = Path(manifest.get("root", "")).resolve()
    _require(root.name == CORPUS_ROOT_NAME and root.is_dir() and not _has_symlink_component(root) and root != REPO_ROOT and REPO_ROOT not in root.parents and stat.S_IMODE(root.stat().st_mode) == 0o700, "corpus root custody mismatch")
    _require(not any(root == prior or prior in root.parents for prior in FORBIDDEN_PRIOR_ROOTS), "corpus overlaps prior V1/V2 root")
    freshness = manifest.get("freshness")
    _require(isinstance(freshness, dict) and freshness == {"new_v3_identity": True, "prior_artifact_exclusion": [str(path) for path in FORBIDDEN_PRIOR_ROOTS], "document_disjointness": True, "author_disjointness": True}, "corpus freshness contract mismatch")
    domains = manifest.get("domains")
    _require(isinstance(domains, dict) and set(domains) == set(DOMAINS), "corpus domain roster mismatch")
    documents: list[str] = []
    authors: list[str] = []
    seen_paths: set[Path] = set()
    for domain in DOMAINS:
        _require(isinstance(domains[domain], dict) and set(domains[domain]) == set(SPLITS), f"corpus split roster mismatch: {domain}")
        for split in SPLITS:
            row = domains[domain][split]
            _require(set(row) == {"path", "sha256", "byte_len", "record_count", "document_ids_sha256", "author_ids_sha256"}, f"corpus file manifest schema mismatch: {domain}/{split}")
            path = Path(row["path"]).resolve()
            _require(path.parent == root and path.is_file() and not path.is_symlink() and path not in seen_paths, f"corpus file path mismatch: {path}")
            seen_paths.add(path)
            _require(row["sha256"] == _sha256_file(path) and row["byte_len"] == path.stat().st_size, f"corpus file digest mismatch: {path}")
            records = _read_records(path)
            _require(row["record_count"] == len(records), f"corpus record count mismatch: {path}")
            file_documents = [record["document_id"] for record in records]
            file_authors = [record["author_id"] for record in records]
            _require(row["document_ids_sha256"] == _digest(sorted(file_documents)) and row["author_ids_sha256"] == _digest(sorted(file_authors)), f"corpus identity digest mismatch: {path}")
            documents.extend(file_documents)
            authors.extend(file_authors)
    _require(len(documents) == len(set(documents)) and len(authors) == len(set(authors)), "corpus document/author IDs are not globally disjoint")
    _require(manifest["global_document_ids_sha256"] == _digest(sorted(documents)) and manifest["global_author_ids_sha256"] == _digest(sorted(authors)), "corpus global identity digest mismatch")


def _load_trust_bundle() -> dict[str, Any]:
    _require(TRUST_BUNDLE_PATH.is_file() and not TRUST_BUNDLE_PATH.is_symlink() and TRUST_BUNDLE_PATH.resolve() != REPO_ROOT and REPO_ROOT not in TRUST_BUNDLE_PATH.resolve().parents, "external V3 trust bundle missing")
    _require(_sha256_file(TRUST_BUNDLE_PATH) == TRUST_BUNDLE_FILE_SHA256, "external V3 trust bundle fingerprint mismatch")
    bundle = _strict_load(TRUST_BUNDLE_PATH)
    required = {"schema_version", "state_slice", "review_root_key_id", "review_root_public_key_hex", "review_root_public_key_sha256", "operator_root_key_id", "operator_root_public_key_hex", "operator_root_public_key_sha256", "reviewer_registry_id", "source", "bundle_sha256"}
    _require(isinstance(bundle, dict) and set(bundle) == required, "trust bundle schema mismatch")
    _require(bundle["schema_version"] == "minimind-v3-trust-bundle-v1" and bundle["state_slice"] == STATE_SLICE and bundle["reviewer_registry_id"] == "minimind-reviewers-2026-09" and bundle["source"] == "external-read-only-authority", "trust bundle identity mismatch")
    review_key = bytes.fromhex(bundle["review_root_public_key_hex"])
    operator_key = bytes.fromhex(bundle["operator_root_public_key_hex"])
    _require(len(review_key) == 32 and len(operator_key) == 32 and review_key != operator_key and hashlib.sha256(review_key).hexdigest() == bundle["review_root_public_key_sha256"] and hashlib.sha256(operator_key).hexdigest() == bundle["operator_root_public_key_sha256"], "trust bundle key binding mismatch")
    _require(bundle["bundle_sha256"] == _digest({key: value for key, value in bundle.items() if key != "bundle_sha256"}), "trust bundle digest mismatch")
    return bundle


def _verify(public_key_hex: str, signature_hex: str, message: bytes, message_error: str) -> None:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        _require(len(public_key_hex) == 64 and len(signature_hex) == 128, "Ed25519 encoding mismatch")
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex)).verify(bytes.fromhex(signature_hex), message)
    except (ImportError, InvalidSignature, ValueError, TypeError) as error:
        raise ValidationError(message_error) from error


def _validate_receipt(receipt_path: Path, *, expected_source: str | None = None, expected_corpus: str | None = None) -> str:
    _require(receipt_path.is_file() and not receipt_path.is_symlink() and receipt_path.resolve() != REPO_ROOT and REPO_ROOT not in receipt_path.resolve().parents, "execution receipt path invalid")
    receipt = _strict_load(receipt_path)
    required = {"schema_version", "state_slice", "review_packet_path", "review_packet_sha256", "reviewed_file_digests", "reviewer_registry_path", "reviewer_registry_sha256", "reviewer_identity", "reviewer_role", "reviewer_certificate_sha256", "operator_identity", "operator_binding_path", "operator_binding_sha256", "reviewer_public_key_hex", "corpus_manifest_sha256", "source_manifest_sha256", "disposition", "signature_algorithm", "signature"}
    _require(isinstance(receipt, dict) and set(receipt) == required, "execution receipt schema mismatch")
    _require(receipt["schema_version"] == RECEIPT_SCHEMA_VERSION and receipt["state_slice"] == STATE_SLICE and receipt["reviewer_role"] == "independent" and receipt["operator_identity"] == OPERATOR_ID and receipt["reviewer_identity"] != OPERATOR_ID, "execution receipt identity mismatch")
    _require(receipt["disposition"] == "ACCEPTED_FOR_MODEL_EXECUTION" and receipt["signature_algorithm"] == "Ed25519", "execution receipt disposition mismatch")
    _require(Path(receipt["review_packet_path"]).resolve() == REVIEW_PACKET_PATH.resolve() and receipt["review_packet_sha256"] == _sha256_file(REVIEW_PACKET_PATH), "execution receipt packet binding mismatch")
    observed = receipt["reviewed_file_digests"]
    _require(observed == {relative: _sha256_file(REPO_ROOT / relative) for relative in FROZEN_REVIEW_FILES}, "execution receipt frozen digest set mismatch")
    bundle = _load_trust_bundle()
    registry_path = Path(receipt["reviewer_registry_path"]).resolve()
    _require(registry_path == REVIEWER_REGISTRY_PATH.resolve() and registry_path.is_file() and not registry_path.is_symlink(), "execution receipt registry path mismatch")
    _require(receipt["reviewer_registry_sha256"] == _sha256_file(registry_path), "execution receipt registry digest mismatch")
    registry = _strict_load(registry_path)
    required_registry = {"schema_version", "state_slice", "registry_id", "issuer_key_id", "reviewers", "registry_sha256", "authority_signature"}
    _require(isinstance(registry, dict) and set(registry) == required_registry and registry["schema_version"] == REGISTRY_SCHEMA_VERSION and registry["state_slice"] == STATE_SLICE and registry["registry_id"] == bundle["reviewer_registry_id"] and registry["issuer_key_id"] == bundle["review_root_key_id"], "reviewer registry schema or identity mismatch")
    _require(registry["registry_sha256"] == _digest({key: value for key, value in registry.items() if key not in {"registry_sha256", "authority_signature"}}), "reviewer registry digest mismatch")
    _require(isinstance(registry["authority_signature"], dict) and registry["authority_signature"].get("algorithm") == "Ed25519", "reviewer registry authority signature missing")
    _verify(bundle["review_root_public_key_hex"], registry["authority_signature"].get("signature_hex", ""), registry["registry_sha256"].encode("ascii"), "reviewer registry authority signature failed")
    matches = [item for item in registry["reviewers"] if isinstance(item, dict) and item.get("identity") == receipt["reviewer_identity"]]
    _require(len(matches) == 1, "reviewer identity is not registry-certified")
    reviewer = matches[0]
    _require(set(reviewer) == {"identity", "role", "public_key_hex", "certificate_sha256", "certificate_signature_hex"} and reviewer["role"] == REVIEWER_ROLE and reviewer["public_key_hex"] != bundle["review_root_public_key_hex"] and reviewer["public_key_hex"] != bundle["operator_root_public_key_hex"] and reviewer["public_key_hex"] == receipt["reviewer_public_key_hex"] and reviewer["certificate_sha256"] == receipt["reviewer_certificate_sha256"], "reviewer certificate binding mismatch")
    certificate = {"schema_version": REGISTRY_SCHEMA_VERSION, "state_slice": STATE_SLICE, "registry_id": bundle["reviewer_registry_id"], "reviewer_identity": reviewer["identity"], "reviewer_role": reviewer["role"], "reviewer_public_key_hex": reviewer["public_key_hex"]}
    _require(reviewer["certificate_sha256"] == _digest(certificate), "reviewer certificate digest mismatch")
    _verify(bundle["review_root_public_key_hex"], reviewer["certificate_signature_hex"], reviewer["certificate_sha256"].encode("ascii"), "reviewer certificate signature failed")
    binding_path = Path(receipt["operator_binding_path"]).resolve()
    _require(binding_path == OPERATOR_BINDING_PATH.resolve() and binding_path.is_file() and not binding_path.is_symlink(), "operator binding path mismatch")
    _require(receipt["operator_binding_sha256"] == _sha256_file(binding_path), "operator binding digest mismatch")
    binding = _strict_load(binding_path)
    required_binding = {"schema_version", "state_slice", "protocol", "packet_sha256", "operator_identity", "operator_principal_id", "operator_key_id", "audience", "nonce", "binding_sha256", "signature_algorithm", "signature_hex"}
    _require(isinstance(binding, dict) and set(binding) == required_binding, "operator binding schema mismatch")
    _require(binding["schema_version"] == "minimind-v3-operator-binding-v1" and binding["state_slice"] == STATE_SLICE and binding["protocol"] == PROTOCOL and binding["packet_sha256"] == _sha256_file(REVIEW_PACKET_PATH) and binding["operator_identity"] == OPERATOR_ID and binding["operator_principal_id"] == OPERATOR_PRINCIPAL_ID and binding["operator_key_id"] == bundle["operator_root_key_id"] and binding["audience"] == "minimind-v3-runner", "operator binding identity mismatch")
    _require(binding["binding_sha256"] == _digest({key: value for key, value in binding.items() if key not in {"binding_sha256", "signature_algorithm", "signature_hex"}}) and binding["signature_algorithm"] == "Ed25519", "operator binding digest mismatch")
    _verify(bundle["operator_root_public_key_hex"], binding["signature_hex"], binding["binding_sha256"].encode("ascii"), "operator binding signature failed")
    if expected_source is not None:
        _require(receipt["source_manifest_sha256"] == expected_source, "execution receipt source binding mismatch")
    if expected_corpus is not None:
        _require(receipt["corpus_manifest_sha256"] == expected_corpus, "execution receipt corpus binding mismatch")
    _verify(receipt["reviewer_public_key_hex"], receipt["signature"], json.dumps({key: value for key, value in receipt.items() if key != "signature"}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"), "execution receipt signature failed")
    return _sha256_file(receipt_path)


def _validate_trial_shape(item: Mapping[str, Any], *, model: bool) -> None:
    expected = {"arm", "split", "replicate_seed", "order_seed", "order_direction", "domain_order", "stage_count", "base_mean_loss", "final_mean_loss", "primary_improvement", "max_forgetting", "compute_units", "token_budget_units", "checkpoint_restore_max_abs_error", "hard_guards"}
    if model:
        expected.add("repeatability_checked")
    _require(set(item) == expected, "aggregate trial schema mismatch")
    _require(item["arm"] in ARMS and item["split"] in SPLITS and item["order_direction"] in ORDER_DIRECTIONS and item["domain_order"] == list(_ordered_domains(item["order_seed"], item["order_direction"])), "aggregate trial identity mismatch")
    _require(item["stage_count"] == 3 and item["compute_units"] > 0 and item["token_budget_units"] > 0, "aggregate trial accounting mismatch")
    for key in ("base_mean_loss", "final_mean_loss", "primary_improvement", "max_forgetting", "checkpoint_restore_max_abs_error"):
        _require(isinstance(item[key], (int, float)) and not isinstance(item[key], bool) and math.isfinite(item[key]), f"aggregate trial numeric field invalid: {key}")
    _require(isinstance(item["hard_guards"], dict) and set(item["hard_guards"]) == TRIAL_GUARD_KEYS and all(isinstance(value, bool) for value in item["hard_guards"].values()), "aggregate trial hard-guard schema mismatch")
    if model:
        _require(item["repeatability_checked"] is True, "model repeatability guard missing")


def _validate_synthetic(root: Path) -> dict[str, Any]:
    resolved = _validate_artifact_root(root, {"source-manifest.json", "contract.json", "result.json"}, SYNTHETIC_ROOT_NAME)
    contract = _strict_load(resolved / "contract.json")
    source = _strict_load(resolved / "source-manifest.json")
    result = _strict_load(resolved / "result.json")
    expected_contract = {"state_slice", "schema_version", "protocol", "claim_ceiling", "source", "corpus", "arms", "training_executed", "model_loaded", "inference_executed", "network_access", "provider_called", "phase_order", "assessment_began_after_lock", "prediction_lock", "aggregate_result_sha256", "contract_sha256"}
    _require(set(contract) == expected_contract, "synthetic contract schema mismatch")
    _require(contract["contract_sha256"] == _digest({key: value for key, value in contract.items() if key != "contract_sha256"}), "synthetic contract digest mismatch")
    _validate_source(source)
    _require(contract["source"] == source and contract["aggregate_result_sha256"] == result["result_sha256"], "synthetic contract binding mismatch")
    _require(set(result) == SYNTHETIC_RESULT_KEYS and result["state_slice"] == STATE_SLICE and result["schema_version"] == SCHEMA_VERSION and result["protocol"] == PROTOCOL and result["claim_ceiling"] == SYNTHETIC_CLAIM_CEILING, "synthetic result schema or identity mismatch")
    _require(result["training_executed"] is False and result["model_loaded"] is False and result["inference_executed"] is False and result["network_access"] is False and result["provider_called"] is False, "synthetic execution flags mismatch")
    _require(result["arms"] == list(ARMS) and result["replicate_seeds"] == list(REPLICATE_SEEDS) and result["order_seeds"] == list(ORDER_SEEDS) and result["phase_order"] == ["fit", "tune", "prediction_lock", "assessment"] and result["assessment_began_after_lock"] is True, "synthetic roster or phase guard mismatch")
    trials = result["aggregate_trials"]
    _require(isinstance(trials, list), "synthetic aggregate trial list missing")
    _require(len(trials) == 108, "synthetic factorial must contain 108 aggregate trials")
    identities = {(item.get("arm"), item.get("split"), item.get("replicate_seed"), item.get("order_seed"), item.get("order_direction")) for item in trials}
    locked_arm = result["prediction_lock"].get("locked_arm") if isinstance(result["prediction_lock"], dict) else None
    _require(identities == _expected_identities(SPLITS, ARMS), "synthetic exact 108-trial identity roster mismatch")
    for item in trials:
        _validate_trial_shape(item, model=False)
        identity = (item["arm"], item["split"], item["replicate_seed"], item["order_seed"], item["order_direction"])
        _require(_digest(item) == _digest(_trial(*identity[:2], identity[2], identity[3], identity[4])), f"synthetic arithmetic mismatch: {identity}")
    _require(isinstance(locked_arm, str) and locked_arm in ARMS, "synthetic prediction lock schema mismatch")
    summary = _aggregate_summary(trials, locked_arm=locked_arm)
    _require(result["prediction_lock"] == summary["prediction_lock"] and result["summary"] == summary, "synthetic summary or prediction lock mismatch")
    _require(result["result_sha256"] == _digest({key: value for key, value in result.items() if key != "result_sha256"}), "synthetic result digest mismatch")
    return {"valid": True, "state_slice": STATE_SLICE, "claim_ceiling": SYNTHETIC_CLAIM_CEILING, "disposition": summary["disposition"], "trial_count": len(trials)}


def _validate_model_contract(root: Path) -> dict[str, Any]:
    resolved = _validate_artifact_root(root, {"contract.json"}, MODEL_ROOT_NAME)
    contract = _strict_load(resolved / "contract.json")
    expected = {"state_slice", "schema_version", "protocol", "claim_ceiling", "source", "corpus", "execution_receipt_sha256", "execution_receipt_path", "model_config", "arms", "network_access", "provider_called", "training_executed", "model_loaded", "inference_executed", "device", "steps_per_stage", "phase_order", "assessment_began_after_lock", "prediction_lock", "assessment_arms", "hard_guards", "aggregate_trials", "summary", "contract_sha256"}
    _require(set(contract) == expected, "model contract schema mismatch")
    _require(contract["contract_sha256"] == _digest({key: value for key, value in contract.items() if key != "contract_sha256"}), "model contract digest mismatch")
    _require(contract["state_slice"] == STATE_SLICE and contract["schema_version"] == SCHEMA_VERSION and contract["protocol"] == PROTOCOL and contract["claim_ceiling"] == MODEL_CLAIM_CEILING, "model contract identity mismatch")
    _require(contract["model_config"] == MODEL_CONFIG and contract["arms"] == list(ARMS) and contract["phase_order"] == ["fit", "tune", "prediction_lock", "assessment"] and contract["assessment_began_after_lock"] is True and contract["training_executed"] is True and contract["model_loaded"] is True and contract["inference_executed"] is True and contract["network_access"] is False and contract["provider_called"] is False, "model contract fixed fields mismatch")
    _require(isinstance(contract["steps_per_stage"], int) and not isinstance(contract["steps_per_stage"], bool) and contract["steps_per_stage"] > 0 and isinstance(contract["device"], str), "model contract runtime schema mismatch")
    _validate_source(contract["source"])
    _validate_corpus(contract["corpus"])
    receipt_path = Path(contract["execution_receipt_path"]).resolve()
    _require(contract["execution_receipt_sha256"] == _validate_receipt(receipt_path, expected_source=contract["source"]["manifest_sha256"], expected_corpus=contract["corpus"]["manifest_sha256"]), "model execution receipt binding mismatch")
    _require(isinstance(contract["hard_guards"], dict) and set(contract["hard_guards"]) == MODEL_GUARD_KEYS and all(isinstance(value, bool) for value in contract["hard_guards"].values()) and all(contract["hard_guards"].values()), "model hard-guard schema mismatch")
    trials = contract["aggregate_trials"]
    _require(isinstance(trials, list), "model aggregate trial list missing")
    tune_lock = contract["prediction_lock"].get("locked_arm") if isinstance(contract["prediction_lock"], dict) else None
    _require(isinstance(tune_lock, str) and tune_lock in ARMS and contract["assessment_arms"] == [tune_lock], "model prediction lock schema mismatch")
    _require({(item.get("arm"), item.get("split"), item.get("replicate_seed"), item.get("order_seed"), item.get("order_direction")) for item in trials} == (_expected_identities(("fit", "tune"), ARMS) | _expected_identities(("assessment",), (tune_lock,))), "model exact phase roster mismatch")
    expected_budget = contract["steps_per_stage"] * len(DOMAINS) * MAX_SEQ_LEN
    for item in trials:
        _validate_trial_shape(item, model=True)
        _require(item["token_budget_units"] == expected_budget and all(item["hard_guards"].values()), "model aggregate trial guard or budget failed")
    summary = _aggregate_summary(trials, locked_arm=tune_lock)
    _require(contract["summary"] == summary and contract["prediction_lock"] == summary["prediction_lock"], "model summary or tune lock mismatch")
    return {"valid": True, "state_slice": STATE_SLICE, "claim_ceiling": MODEL_CLAIM_CEILING, "disposition": "ModelContractValid", "trial_count": len(trials)}


def validate_artifact(root: Path) -> dict[str, Any]:
    contract_path = root.resolve() / "contract.json"
    _require(contract_path.is_file() and not contract_path.is_symlink(), "contract.json missing")
    contract = _strict_load(contract_path)
    ceiling = contract.get("claim_ceiling") if isinstance(contract, dict) else None
    if ceiling == SYNTHETIC_CLAIM_CEILING:
        return _validate_synthetic(root)
    if ceiling == MODEL_CLAIM_CEILING:
        return _validate_model_contract(root)
    raise ValidationError("unknown claim ceiling")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("usage: validate_minimind_domain_specific_v3.py ARTIFACT_ROOT")
    print(json.dumps(validate_artifact(Path(sys.argv[1])), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
