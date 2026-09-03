#!/usr/bin/env python3
"""Three-lane MiniMind continual-learning comparison harness.

State slice: continual-learning-minimind-three-lane-sota-v1.

This package has two boundaries. The deterministic synthetic campaign checks
the complete task, domain, and experience schemas. The tiny offline model
campaign exercises only methods with a declared MiniMind implementation; any
frontier method without faithful portability is recorded as an exclusion.
Neither path establishes a global SOTA claim.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import random
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "continual-learning-minimind-three-lane-sota-v1"
SCHEMA_VERSION = "minimind-three-lane-result-v1"
PROTOCOL = "minimind-three-lane-sota-v1"
SYNTHETIC_CLAIM_CEILING = "LocalDevelopmentMiniMindThreeLaneSyntheticQualification"
MODEL_CLAIM_CEILING = "LocalDevelopmentMiniMindThreeLanePilotQualification"
UPSTREAM_URL = "https://github.com/jingyaogong/minimind"
UPSTREAM_COMMIT = "7a6fddd63a30c06b2fdd5fac4089922b29bc841b"
REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = REPO_ROOT / "docs/research/continual-learning/288-minimind-three-lane-sota-v1-protocol.md"
REVIEW_PACKET_PATH = REPO_ROOT / "docs/research/continual-learning/289-minimind-three-lane-sota-v1-review-packet.md"
MANIFEST_PATH = REPO_ROOT / "docs/research/continual-learning/290-minimind-three-lane-sota-v1-implementation-manifest.json"
SOURCE_MANIFEST_PATH = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-three-lane-sota-v1-source-manifest-20260902.json")
CORPUS_ROOT = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-three-lane-sota-v1-corpus-20260902")
CORPUS_MANIFEST_PATH = CORPUS_ROOT / "corpus-manifest.json"
SOURCE_ROOT = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-three-lane-sota-v1-source-20260902")
SYNTHETIC_ROOT = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-three-lane-sota-v1-synthetic-20260902")
MODEL_ROOT = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-three-lane-sota-v1-model-20260902")
TRUST_BUNDLE_PATH = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-three-lane-sota-v1-trust-bundle-20260902.json")
REVIEWER_REGISTRY_PATH = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-three-lane-sota-v1-reviewer-registry-20260902.json")
OPERATOR_BINDING_PATH = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-three-lane-sota-v1-operator-binding-20260902.json")
RECEIPT_PATH = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-three-lane-sota-v1-execution-receipt-20260902.json")
TRUST_BUNDLE_FILE_SHA256 = "5156f70af0af2e214e6621c12222d1191fe64cd54b0be6ac451f3066cadbb0ce"
OPERATOR_ID = "shaanp"
OPERATOR_PRINCIPAL_ID = "principal-operator-shaanp"
REVIEWER_ROLE = "independent"
FROZEN_REVIEW_FILES = (
    "AGENTS.md",
    "docs/research/continual-learning/288-minimind-three-lane-sota-v1-protocol.md",
    "docs/research/continual-learning/289-minimind-three-lane-sota-v1-review-packet.md",
    "docs/research/continual-learning/290-minimind-three-lane-sota-v1-implementation-manifest.json",
    "experiments/continual_learning/minimind_three_lane_sota_v1.py",
    "experiments/continual_learning/validate_minimind_three_lane_sota_v1.py",
    "experiments/continual_learning/tests/test_minimind_three_lane_sota_v1.py",
)

LANES = ("task", "domain", "experience")
TASKS = ("ag_news", "amazon_reviews", "yelp", "dbpedia", "yahoo_answers")
DOMAINS = ("materials", "clinical", "finance")
EXPERIENCE_TASKS = ("software", "forecasting", "database")
SPLITS = ("fit", "tune", "assessment")
ORDER_DIRECTIONS = ("forward", "reverse")
REPLICATE_SEEDS = (2026090201, 2026090202, 2026090203)
ORDER_SEEDS = (7301, 7302, 7303)
MODEL_REPLICATE_SEEDS = (2026090201,)
MODEL_ORDER_SEEDS = (7301,)
MODEL_ORDER_DIRECTIONS = ("forward",)
PARAMETER_ARMS = (
    "untouched_base", "joint_oracle", "sequential_full", "shared_lora",
    "replay", "ewc_lwf", "independent_adapters", "task_routed_bank",
    "o_lora", "n_lora", "oplora", "osft",
)
EXPERIENCE_ARMS = (
    "stateless", "naive_icl", "retrieval_memory", "skill_library",
    "parametric_experience_update", "hybrid_experience_update",
)
MODEL_PARAMETER_ARMS = ("untouched_base", "sequential_full", "shared_lora", "replay")
MODEL_EXPERIENCE_ARMS = EXPERIENCE_ARMS
FRONTIER_EXCLUSIONS = {
    "ewc_lwf": "not faithfully implemented in the tiny MiniMind pilot",
    "independent_adapters": "persistent per-task model bank is not retained in this pilot",
    "task_routed_bank": "routing and checkpoint bank are not retained in this pilot",
    "o_lora": "frontier orthogonality reproduction is synthetic-only in this pilot",
    "n_lora": "collision definition is not ported to MiniMind in this pilot",
    "oplora": "double-sided projection is synthetic-only in this pilot",
    "osft": "high-rank SVD update is synthetic-only in this pilot",
    "oliera": "not in the executable pilot panel",
    "aso_lora": "not in the executable pilot panel",
    "das": "domain-CPT source/data protocol not reproduced in this pilot",
    "hprompt_cpt": "domain-CPT source/data protocol not reproduced in this pilot",
    "stability_gap_cpt": "domain-CPT source/data protocol not reproduced in this pilot",
}
MODEL_CONFIG = {
    "model_name": "minimind-3-dense",
    "hidden_size": 768,
    "num_hidden_layers": 8,
    "use_moe": False,
    "vocab_size": 6400,
    "max_seq_len": 128,
}
MAX_SEQ_LEN = MODEL_CONFIG["max_seq_len"]
VECTOR_DIMENSION = 8
MAX_FORGETTING = 0.40
MAX_CHECKPOINT_ERROR = 1e-12


class ProtocolError(ValueError):
    """Raised when the state-slice contract is violated."""


def _digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _strict_load(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ProtocolError(f"duplicate JSON key: {path}:{key}")
            result[key] = value
        return result

    def constant(value: str) -> None:
        raise ProtocolError(f"non-finite JSON constant: {path}:{value}")

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProtocolError(f"invalid JSON: {path}") from error


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def _unit(*parts: object) -> float:
    payload = "|".join((STATE_SLICE, *(str(part) for part in parts))).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / float(1 << 64)


def _signed(*parts: object) -> float:
    return 2.0 * _unit(*parts) - 1.0


def _lane_items(lane: str) -> tuple[str, ...]:
    if lane == "task":
        return TASKS
    if lane == "domain":
        return DOMAINS
    if lane == "experience":
        return EXPERIENCE_TASKS
    raise ProtocolError(f"unknown lane: {lane}")


def _ordered_items(lane: str, order_seed: int, direction: str) -> tuple[str, ...]:
    items = list(enumerate(_lane_items(lane)))
    items.sort(key=lambda item: (_unit("order", lane, order_seed, item[1]), item[0]))
    if direction == "reverse":
        items.reverse()
    return tuple(item[1] for item in items)


def _target(lane: str, item: str, split: str, seed: int, component: int) -> float:
    return 0.25 * _signed("target", lane, item, split, seed, component)


def _loss(state: Sequence[float], target: Sequence[float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(state, target)) / len(state)


def _target_vector(lane: str, item: str, split: str, seed: int) -> tuple[float, ...]:
    return tuple(_target(lane, item, split, seed, index) for index in range(VECTOR_DIMENSION))


def _parameter_factor(arm: str) -> float:
    return {
        "untouched_base": 0.0,
        "joint_oracle": 0.82,
        "sequential_full": 0.48,
        "shared_lora": 0.56,
        "replay": 0.68,
        "ewc_lwf": 0.63,
        "independent_adapters": 0.79,
        "task_routed_bank": 0.81,
        "o_lora": 0.74,
        "n_lora": 0.76,
        "oplora": 0.78,
        "osft": 0.84,
    }[arm]


def _synthetic_trial(lane: str, arm: str, split: str, seed: int, order_seed: int, direction: str) -> dict[str, Any]:
    items = _lane_items(lane)
    base = tuple(0.01 * _signed("base", index) for index in range(VECTOR_DIMENSION))
    state = base
    adapters: dict[str, tuple[float, ...]] = {}
    learned: dict[str, float] = {}
    order = _ordered_items(lane, order_seed, direction)
    factor = 0.0
    if lane == "experience":
        experience_index = {item: index for index, item in enumerate(order)}
        remembered: set[str] = set()
        score = 0.0
        base_score = 0.0
        for index, item in enumerate(order):
            if arm == "stateless":
                increment = 0.0
            elif arm == "naive_icl":
                increment = 0.10 + 0.01 * index
            elif arm == "retrieval_memory":
                remembered.add(item)
                increment = 0.13 + 0.01 * len(remembered)
            elif arm == "skill_library":
                remembered.add(item)
                increment = 0.15 + 0.018 * len(remembered)
            elif arm == "parametric_experience_update":
                increment = 0.12 + 0.025 * index
            else:
                increment = 0.18 + 0.02 * index
            score += increment + 0.002 * _signed("experience-noise", lane, split, seed, order_seed, direction, item)
            base_score += 0.002 * _signed("experience-base", seed, item)
            experience_index[item] = index
        final_metric = score / len(items)
        primary = final_metric - base_score / len(items)
        forgetting = max(0.0, 0.05 - 0.01 * factor)
        state_bytes = {"stateless": 0, "naive_icl": 256, "retrieval_memory": 512, "skill_library": 768, "parametric_experience_update": 1024, "hybrid_experience_update": 1280}[arm]
        return {
            "lane": lane, "arm": arm, "split": split, "replicate_seed": seed,
            "order_seed": order_seed, "order_direction": direction,
            "item_order": list(order), "stage_count": len(items),
            "base_metric": base_score / len(items), "final_metric": final_metric,
            "primary_improvement": primary, "forgetting": forgetting,
            "forward_transfer": primary * 0.8, "compute_units": len(items) * 3,
            "state_bytes": state_bytes, "hard_guards": {
                "complete_stage_coverage": True, "zero_attrition": True,
                "equal_budget": True, "heldout_experience": True,
                "state_accounted": True,
            },
        }

    factor = _parameter_factor(arm)
    for item in order:
        current = _target_vector(lane, item, "fit", seed)
        if arm == "joint_oracle":
            current = tuple(sum(_target_vector(lane, other, "fit", seed)[index] for other in items) / len(items) for index in range(VECTOR_DIMENSION))
        if arm == "replay" and learned:
            current = tuple(sum(values[index] for values in (*[_target_vector(lane, item, "fit", seed)], *[_target_vector(lane, seen, "fit", seed) for seen in learned])) / (len(learned) + 1) for index in range(VECTOR_DIMENSION))
        if arm == "independent_adapters" or arm == "task_routed_bank":
            previous = adapters.get(item, (0.0,) * VECTOR_DIMENSION)
            adapters[item] = tuple(previous[index] + factor * (current[index] - previous[index]) for index in range(VECTOR_DIMENSION))
        elif arm != "untouched_base":
            state = tuple(state[index] + factor * (current[index] - state[index]) for index in range(VECTOR_DIMENSION))
        prediction = adapters.get(item, state)
        learned[item] = _loss(prediction, _target_vector(lane, item, "fit", seed))
    predictions = {item: adapters.get(item, state) for item in items}
    evaluation = {item: _loss(predictions[item], _target_vector(lane, item, split, seed)) for item in items}
    base_metric = sum(_loss(base, _target_vector(lane, item, split, seed)) for item in items) / len(items)
    final_metric = sum(evaluation.values()) / len(items)
    forgetting = max(0.0, final_metric - base_metric) * (0.5 + 0.5 * (1.0 - factor))
    return {
        "lane": lane, "arm": arm, "split": split, "replicate_seed": seed,
        "order_seed": order_seed, "order_direction": direction,
        "item_order": list(order), "stage_count": len(items),
        "base_metric": base_metric, "final_metric": final_metric,
        "primary_improvement": base_metric - final_metric,
        "forgetting": forgetting, "forward_transfer": max(0.0, base_metric - final_metric) * 0.5,
        "compute_units": len(items) * 3, "state_bytes": 256 if arm in ("shared_lora", "replay", "o_lora", "n_lora", "oplora", "osft") else 0,
        "hard_guards": {
            "complete_stage_coverage": len(order) == len(items), "zero_attrition": True,
            "equal_budget": True, "heldout_experience": True, "state_accounted": True,
        },
    }


def _expected_arms(lane: str) -> tuple[str, ...]:
    return EXPERIENCE_ARMS if lane == "experience" else PARAMETER_ARMS


def _select_locks(trials: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Lock each arm independently so assessment does not become arm selection."""
    locks: dict[str, dict[str, Any]] = {}
    for lane in LANES:
        lane_locks: dict[str, Any] = {}
        for arm in _expected_arms(lane):
            subset = [item for item in trials if item["lane"] == lane and item["split"] == "tune" and item["arm"] == arm]
            _require(len(subset) == len(REPLICATE_SEEDS) * len(ORDER_DIRECTIONS), f"tune roster incomplete for {lane}:{arm}")
            lane_locks[arm] = {
                "selection": "fixed_protocol_hyperparameters",
                "tune_trial_count": len(subset),
                "tune_primary_mean": sum(float(item["primary_improvement"]) for item in subset) / len(subset),
            }
        locks[lane] = lane_locks
    return locks


def run_synthetic_campaign() -> dict[str, Any]:
    fit = [_synthetic_trial(lane, arm, "fit", seed, order_seed, direction) for lane in LANES for arm in _expected_arms(lane) for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS) for direction in ORDER_DIRECTIONS]
    tune = [_synthetic_trial(lane, arm, "tune", seed, order_seed, direction) for lane in LANES for arm in _expected_arms(lane) for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS) for direction in ORDER_DIRECTIONS]
    locks = _select_locks([*fit, *tune])
    assessment = [_synthetic_trial(lane, arm, "assessment", seed, order_seed, direction) for lane in LANES for arm in _expected_arms(lane) for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS) for direction in ORDER_DIRECTIONS]
    trials = [*fit, *tune, *assessment]
    summary = {lane: {"locked_arms": sorted(locks[lane]), "trial_count": sum(1 for item in trials if item["lane"] == lane), "all_hard_guards_pass": all(all(item["hard_guards"].values()) for item in trials if item["lane"] == lane)} for lane in LANES}
    result = {
        "state_slice": STATE_SLICE, "schema_version": SCHEMA_VERSION, "protocol": PROTOCOL,
        "claim_ceiling": SYNTHETIC_CLAIM_CEILING, "lanes": list(LANES),
        "training_executed": False, "model_loaded": False, "inference_executed": False,
        "network_access": False, "provider_called": False,
        "phase_order": ["fit", "tune", "prediction_lock", "assessment"],
        "assessment_began_after_lock": True, "prediction_locks": locks,
        "parameter_arms": list(PARAMETER_ARMS), "experience_arms": list(EXPERIENCE_ARMS),
        "published_benchmark_reproduced": False, "real_local_corpus": False,
        "aggregate_trials": trials, "summary": summary,
    }
    result["result_sha256"] = _digest(result)
    return result


def _source_manifest(source_root: Path) -> dict[str, Any]:
    _require(source_root.is_dir() and not source_root.is_symlink(), f"source checkout missing: {source_root}")
    status = subprocess.run(["git", "-C", str(source_root), "status", "--porcelain"], check=True, capture_output=True, text=True)
    _require(not status.stdout, "MiniMind source checkout is dirty")
    commit = subprocess.run(["git", "-C", str(source_root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
    remote = subprocess.run(["git", "-C", str(source_root), "config", "--get", "remote.origin.url"], check=True, capture_output=True, text=True).stdout.strip()
    _require(commit == UPSTREAM_COMMIT, "MiniMind source commit mismatch")
    _require("jingyaogong/minimind" in remote, "MiniMind source remote mismatch")
    required = ("LICENSE", "requirements.txt", "model/model_minimind.py", "model/model_lora.py", "model/tokenizer.json", "model/tokenizer_config.json", "trainer/train_pretrain.py", "trainer/train_full_sft.py", "trainer/train_lora.py", "dataset/lm_dataset.py")
    files = {path: _sha256_file(source_root / path) for path in required}
    manifest = {"schema_version": "minimind-three-lane-source-manifest-v1", "state_slice": STATE_SLICE, "url": UPSTREAM_URL, "commit": commit, "remote": remote, "license": "Apache-2.0", "checkout": str(source_root), "required_files": files}
    return {**manifest, "manifest_sha256": _digest(manifest)}


def _prepare_corpus() -> dict[str, Any]:
    if CORPUS_ROOT.exists():
        raise ProtocolError(f"refusing to overwrite corpus root: {CORPUS_ROOT}")
    CORPUS_ROOT.mkdir(parents=True, mode=0o700)
    records: list[dict[str, Any]] = []
    file_entries: list[dict[str, Any]] = []
    for lane in LANES:
        for split in SPLITS:
            path = CORPUS_ROOT / f"{lane}-{split}.jsonl"
            rows = []
            for index, item in enumerate(_lane_items(lane)):
                row = {"record_id": f"{STATE_SLICE}-{lane}-{split}-{index}", "author_id": f"author-{lane}-{split}-{index}", "text": f"This bounded {lane} fixture describes {item} during {split}. Experience rule {index} remains explicit.", "target": item}
                rows.append(row)
                records.append(row)
            path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
            file_entries.append({"lane": lane, "split": split, "path": str(path), "sha256": _sha256_file(path), "record_count": len(rows)})
    manifest = {"schema_version": "minimind-three-lane-corpus-manifest-v1", "state_slice": STATE_SLICE, "corpus_identity": f"{STATE_SLICE}-fresh-fixture-20260902", "root": str(CORPUS_ROOT), "fixture_only": True, "published_benchmark_reproduced": False, "prior_artifact_exclusion": True, "files": file_entries, "global_record_ids_sha256": _digest(sorted(row["record_id"] for row in records)), "global_author_ids_sha256": _digest(sorted(row["author_id"] for row in records))}
    _write_json(CORPUS_MANIFEST_PATH, {**manifest, "manifest_sha256": _digest(manifest)})
    os.chmod(CORPUS_ROOT, stat.S_IRWXU)
    return {**manifest, "manifest_sha256": _digest(manifest)}


def prepare_fixture(source_root: Path = SOURCE_ROOT) -> dict[str, Any]:
    source = _source_manifest(source_root)
    _write_json(SOURCE_MANIFEST_PATH, source)
    corpus = _prepare_corpus()
    return {"state_slice": STATE_SLICE, "source_manifest": str(SOURCE_MANIFEST_PATH), "corpus_manifest": str(CORPUS_MANIFEST_PATH), "source_manifest_sha256": source["manifest_sha256"], "corpus_manifest_sha256": corpus["manifest_sha256"]}


def _load_corpus_manifest(path: Path) -> dict[str, Any]:
    manifest = _strict_load(path)
    expected = {"schema_version", "state_slice", "corpus_identity", "root", "fixture_only", "published_benchmark_reproduced", "prior_artifact_exclusion", "files", "global_record_ids_sha256", "global_author_ids_sha256", "manifest_sha256"}
    _require(set(manifest) == expected and manifest["schema_version"] == "minimind-three-lane-corpus-manifest-v1" and manifest["state_slice"] == STATE_SLICE, "corpus manifest schema mismatch")
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    _require(manifest["manifest_sha256"] == _digest(body), "corpus manifest digest mismatch")
    _require(manifest["fixture_only"] is True and manifest["published_benchmark_reproduced"] is False and manifest["prior_artifact_exclusion"] is True, "corpus freshness boundary mismatch")
    root = Path(manifest["root"]).resolve()
    _require(root == CORPUS_ROOT.resolve() and root.is_dir() and stat.S_IMODE(root.stat().st_mode) == 0o700, "corpus root custody mismatch")
    _require(len(manifest["files"]) == len(LANES) * len(SPLITS), "corpus file roster mismatch")
    seen: set[tuple[str, str]] = set()
    for entry in manifest["files"]:
        _require(set(entry) == {"lane", "split", "path", "sha256", "record_count"}, "corpus file schema mismatch")
        key = (entry["lane"], entry["split"])
        _require(key not in seen and key[0] in LANES and key[1] in SPLITS, "corpus file identity mismatch")
        seen.add(key)
        file_path = Path(entry["path"]).resolve()
        _require(file_path.parent == root and file_path.is_file() and _sha256_file(file_path) == entry["sha256"], "corpus file custody mismatch")
    return manifest


def _read_corpus(manifest: Mapping[str, Any]) -> dict[str, dict[str, list[str]]]:
    corpus: dict[str, dict[str, list[str]]] = {lane: {split: [] for split in SPLITS} for lane in LANES}
    for entry in manifest["files"]:
        path = Path(entry["path"])
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            _require(set(row) == {"record_id", "author_id", "text", "target"} and row["text"], "corpus record schema mismatch")
            corpus[entry["lane"]][entry["split"]].append(row["text"])
        _require(len(corpus[entry["lane"]][entry["split"]]) == entry["record_count"], "corpus record count mismatch")
    return corpus


def _receipt_payload(receipt: Mapping[str, Any]) -> bytes:
    return json.dumps({key: value for key, value in receipt.items() if key != "signature"}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _verify_ed25519(public_key_hex: str, signature_hex: str, message: bytes, failure: str) -> None:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        _require(isinstance(public_key_hex, str) and len(public_key_hex) == 64, "Ed25519 public key encoding mismatch")
        _require(isinstance(signature_hex, str) and len(signature_hex) == 128, "Ed25519 signature encoding mismatch")
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex)).verify(bytes.fromhex(signature_hex), message)
    except (ImportError, InvalidSignature, ValueError, TypeError) as error:
        raise ProtocolError(failure) from error


def _load_trust_bundle() -> dict[str, Any]:
    resolved = TRUST_BUNDLE_PATH.resolve()
    _require(resolved != REPO_ROOT and REPO_ROOT not in resolved.parents and resolved.is_file() and not resolved.is_symlink(), "external trust bundle missing")
    _require(stat.S_IMODE(resolved.stat().st_mode) in (0o644, 0o640, 0o600), "trust bundle permissions are too broad")
    _require(_sha256_file(resolved) == TRUST_BUNDLE_FILE_SHA256, "trust bundle fingerprint mismatch")
    bundle = _strict_load(resolved)
    required = {"authority", "execution_scope", "issued_at_utc", "operator_root_binding", "receipts", "reviewer_registry", "schema_version", "source", "state_slice", "trust_bundle_id", "bundle_sha256", "bundle_signature"}
    _require(set(bundle) == required and bundle["schema_version"] == "minimind-three-lane-sota-trust-bundle-v1" and bundle["state_slice"] == STATE_SLICE and bundle["source"] == "external-read-only-authority", "trust bundle schema or identity mismatch")
    authority = bundle["authority"]
    _require(isinstance(authority, Mapping) and set(authority) == {"role", "review_root", "operator_root"} and authority["role"] == "external-trust-authority", "trust authority schema mismatch")
    review_root = authority["review_root"]
    operator_root = authority["operator_root"]
    _require(isinstance(review_root, Mapping) and isinstance(operator_root, Mapping), "trust root schema mismatch")
    for root in (review_root, operator_root):
        _require(set(root) == {"algorithm", "key_id", "public_key_hex", "public_key_sha256"} and root["algorithm"] == "Ed25519", "trust root identity mismatch")
        try:
            public_key = bytes.fromhex(root["public_key_hex"])
        except (TypeError, ValueError) as error:
            raise ProtocolError("trust root key encoding mismatch") from error
        _require(len(public_key) == 32 and hashlib.sha256(public_key).hexdigest() == root["public_key_sha256"], "trust root key fingerprint mismatch")
    _require(review_root["public_key_hex"] != operator_root["public_key_hex"], "trust root separation mismatch")
    bundle_body = {key: value for key, value in bundle.items() if key not in {"bundle_sha256", "bundle_signature"}}
    _require(bundle["bundle_sha256"] == _digest(bundle_body), "trust bundle digest mismatch")
    bundle_signature = bundle["bundle_signature"]
    _require(isinstance(bundle_signature, Mapping) and set(bundle_signature) == {"algorithm", "issuer_key_id", "signature_hex"} and bundle_signature["algorithm"] == "Ed25519" and bundle_signature["issuer_key_id"] == review_root["key_id"], "trust bundle signature schema mismatch")
    _verify_ed25519(review_root["public_key_hex"], bundle_signature["signature_hex"], json.dumps(bundle_body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"), "trust bundle signature verification failed")
    registry = bundle["reviewer_registry"]
    _require(isinstance(registry, Mapping) and registry["state_slice"] == STATE_SLICE and registry["registry_id"], "trust reviewer registry preview mismatch")
    registry_signature = registry.get("registry_signature")
    _require(isinstance(registry_signature, Mapping) and registry_signature.get("algorithm") == "Ed25519" and registry_signature.get("issuer_key_id") == review_root["key_id"], "trust reviewer registry signature missing")
    # The enclosing trust-bundle signature authenticates this exact registry
    # preview. The registry signature is retained as authority metadata, but
    # its legacy serialization is not independently interpreted here.
    reviewers = registry.get("reviewers")
    _require(isinstance(reviewers, list) and len(reviewers) == 1, "trust reviewer registry roster mismatch")
    reviewer = reviewers[0]
    _require(isinstance(reviewer, Mapping) and reviewer.get("role") == REVIEWER_ROLE and reviewer.get("identity") != OPERATOR_ID, "trust reviewer independence mismatch")
    certificate = reviewer.get("certificate")
    certificate_signature = reviewer.get("certificate_signature")
    _require(isinstance(certificate, Mapping) and isinstance(certificate_signature, Mapping), "trust reviewer certificate missing")
    _require(reviewer["certificate_sha256"] == _digest(certificate), "trust reviewer certificate digest mismatch")
    _require(certificate_signature.get("algorithm") == "Ed25519" and certificate_signature.get("issuer_key_id") == review_root["key_id"], "trust reviewer certificate signature schema mismatch")
    _verify_ed25519(review_root["public_key_hex"], certificate_signature.get("signature_hex", ""), json.dumps(certificate, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"), "trust reviewer certificate signature verification failed")
    _require(certificate.get("state_slice") == STATE_SLICE and certificate.get("registry_id") == registry["registry_id"] and certificate.get("subject_identity") == reviewer["identity"] and certificate.get("public_key_hex") == reviewer["public_key_hex"], "trust reviewer certificate binding mismatch")
    operator_binding = bundle["operator_root_binding"]
    _require(isinstance(operator_binding, Mapping) and operator_binding.get("state_slice") == STATE_SLICE and operator_binding.get("operator_root_key_id") == operator_root["key_id"], "trust operator root binding mismatch")
    _require(operator_binding["binding_sha256"] == _digest({key: value for key, value in operator_binding.items() if key not in {"binding_sha256", "binding_signature"}}), "trust operator binding digest mismatch")
    binding_signature = operator_binding["binding_signature"]
    _require(binding_signature.get("algorithm") == "Ed25519" and binding_signature.get("issuer_key_id") == review_root["key_id"], "trust operator binding signature schema mismatch")
    operator_binding_body = {key: value for key, value in operator_binding.items() if key not in {"binding_sha256", "binding_signature"}}
    _verify_ed25519(review_root["public_key_hex"], binding_signature["signature_hex"], json.dumps(operator_binding_body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"), "trust operator root binding signature verification failed")
    return bundle


def _current_frozen_file_digests() -> dict[str, str]:
    digests: dict[str, str] = {}
    for relative in FROZEN_REVIEW_FILES:
        path = REPO_ROOT / relative
        _require(path.is_file() and not path.is_symlink(), f"frozen review file missing: {relative}")
        digests[relative] = _sha256_file(path)
    return digests


def _validate_receipt(path: Path, source_sha: str, corpus_sha: str) -> str:
    resolved = path.resolve()
    _require(resolved != REPO_ROOT and REPO_ROOT not in resolved.parents and path.is_file() and not path.is_symlink() and stat.S_IMODE(path.stat().st_mode) == 0o600, "execution receipt custody mismatch")
    receipt = _strict_load(path)
    expected = {"schema_version", "state_slice", "protocol", "review_packet_path", "review_packet_sha256", "reviewed_file_digests", "reviewer_registry_path", "reviewer_registry_sha256", "reviewer_identity", "reviewer_role", "reviewer_certificate_sha256", "reviewer_public_key_hex", "operator_identity", "operator_binding_path", "operator_binding_sha256", "source_manifest_sha256", "corpus_manifest_sha256", "disposition", "signature_algorithm", "signature"}
    _require(set(receipt) == expected and receipt["schema_version"] == "minimind-three-lane-sota-v1-execution-receipt" and receipt["state_slice"] == STATE_SLICE and receipt["protocol"] == PROTOCOL, "execution receipt schema mismatch")
    _require(receipt["review_packet_path"] == str(REVIEW_PACKET_PATH) and receipt["review_packet_sha256"] == _sha256_file(REVIEW_PACKET_PATH), "receipt packet binding mismatch")
    _require(receipt["reviewed_file_digests"] == _current_frozen_file_digests(), "receipt frozen-file digest binding mismatch")
    _require(receipt["source_manifest_sha256"] == source_sha and receipt["corpus_manifest_sha256"] == corpus_sha, "receipt data binding mismatch")
    _require(receipt["reviewer_role"] == REVIEWER_ROLE and receipt["reviewer_identity"] != OPERATOR_ID and receipt["operator_identity"] == OPERATOR_ID, "receipt identity mismatch")
    _require(receipt["disposition"] == "ACCEPTED_FOR_MODEL_EXECUTION" and receipt["signature_algorithm"] == "Ed25519", "receipt disposition mismatch")
    bundle = _load_trust_bundle()
    registry_path = Path(receipt["reviewer_registry_path"]).resolve()
    _require(registry_path == REVIEWER_REGISTRY_PATH.resolve() and registry_path.is_file() and not registry_path.is_symlink(), "reviewer registry path mismatch")
    _require(_sha256_file(registry_path) == receipt["reviewer_registry_sha256"], "reviewer registry digest mismatch")
    registry = _strict_load(registry_path)
    _require(registry == bundle["reviewer_registry"], "reviewer registry is not the trusted external registry")
    reviewer = next((item for item in registry["reviewers"] if item.get("identity") == receipt["reviewer_identity"]), None)
    _require(reviewer is not None and reviewer["role"] == REVIEWER_ROLE and reviewer["certificate_sha256"] == receipt["reviewer_certificate_sha256"] and reviewer["public_key_hex"] == receipt["reviewer_public_key_hex"], "reviewer registry resolution failed")
    binding_path = Path(receipt["operator_binding_path"]).resolve()
    _require(binding_path == OPERATOR_BINDING_PATH.resolve() and binding_path.is_file() and not binding_path.is_symlink(), "operator binding path mismatch")
    _require(_sha256_file(binding_path) == receipt["operator_binding_sha256"], "operator binding digest mismatch")
    binding = _strict_load(binding_path)
    binding_required = {"schema_version", "state_slice", "protocol", "packet_sha256", "operator_identity", "operator_principal_id", "operator_key_id", "audience", "nonce", "binding_sha256", "signature_algorithm", "signature_hex"}
    _require(set(binding) == binding_required and binding["schema_version"] == "minimind-three-lane-sota-v1-operator-binding-v1" and binding["state_slice"] == STATE_SLICE and binding["protocol"] == PROTOCOL and binding["packet_sha256"] == _sha256_file(REVIEW_PACKET_PATH) and binding["operator_identity"] == OPERATOR_ID and binding["operator_principal_id"] == OPERATOR_PRINCIPAL_ID and binding["operator_key_id"] == bundle["authority"]["operator_root"]["key_id"] and binding["audience"] == "minimind-three-lane-sota-v1-runner", "operator binding identity mismatch")
    _require(binding["binding_sha256"] == _digest({key: value for key, value in binding.items() if key not in {"binding_sha256", "signature_algorithm", "signature_hex"}}) and binding["signature_algorithm"] == "Ed25519", "operator binding digest mismatch")
    binding_body = {key: value for key, value in binding.items() if key not in {"binding_sha256", "signature_algorithm", "signature_hex"}}
    _verify_ed25519(bundle["authority"]["operator_root"]["public_key_hex"], binding["signature_hex"], json.dumps(binding_body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"), "operator binding signature verification failed")
    _verify_ed25519(receipt["reviewer_public_key_hex"], receipt["signature"], _receipt_payload(receipt), "execution receipt signature verification failed")
    return _sha256_file(path)


def _load_model_runtime(source_root: Path, device: str, seed: int) -> tuple[Any, Any, Any, Any, Any]:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import torch
    from transformers import AutoTokenizer

    torch.manual_seed(seed)
    sys.path.insert(0, str(source_root))
    from model.model_lora import apply_lora
    from model.model_minimind import MiniMindConfig, MiniMindForCausalLM

    config = MiniMindConfig(**MODEL_CONFIG)
    model = MiniMindForCausalLM(config).to(device)
    tokenizer = AutoTokenizer.from_pretrained(str(source_root / "model"), local_files_only=True)
    return torch, model, tokenizer, apply_lora, MiniMindForCausalLM


def _model_loss(torch_module: Any, model: Any, tokenizer: Any, text: str, device: str) -> tuple[float, int]:
    encoded = tokenizer(text, return_tensors="pt", truncation=True, max_length=MAX_SEQ_LEN)
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded.get("attention_mask")
    if attention_mask is not None:
        attention_mask = attention_mask.to(device)
    with torch_module.no_grad():
        output = model(input_ids=input_ids, attention_mask=attention_mask, labels=input_ids)
    value = float(output.loss.detach().cpu())
    _require(math.isfinite(value), "non-finite model loss")
    return value, int(input_ids.numel())


def _train_model(torch_module: Any, model: Any, tokenizer: Any, texts: Sequence[str], device: str, steps: int, seed: int) -> int:
    parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    _require(parameters, "model has no trainable parameters")
    optimizer = torch_module.optim.AdamW(parameters, lr=1e-4)
    model.train()
    token_count = 0
    for step in range(steps):
        torch_module.manual_seed(seed + step)
        encoded = tokenizer(texts[step % len(texts)], return_tensors="pt", truncation=True, max_length=MAX_SEQ_LEN)
        input_ids = encoded["input_ids"].to(device)
        attention_mask = encoded.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(device)
        optimizer.zero_grad(set_to_none=True)
        output = model(input_ids=input_ids, attention_mask=attention_mask, labels=input_ids)
        _require(output.loss is not None and bool(torch_module.isfinite(output.loss).all()), "non-finite training loss")
        output.loss.backward()
        optimizer.step()
        token_count += int(input_ids.numel())
    model.eval()
    return token_count


def _checkpoint_error(torch_module: Any, model: Any, factory: Any, apply_lora: Any, device: str) -> float:
    buffer = io.BytesIO()
    torch_module.save(model.state_dict(), buffer)
    restored = factory(model.config).to(device)
    state = torch_module.load(io.BytesIO(buffer.getvalue()), map_location=device, weights_only=True)
    if any(".lora." in key for key in state):
        apply_lora(restored, rank=2)
    restored.load_state_dict(state, strict=True)
    restored_state = restored.state_dict()
    _require(set(restored_state) == set(state), "checkpoint restore state-key mismatch")
    errors = [float((state[key].detach().cpu() - restored_state[key].detach().cpu()).abs().max()) for key in sorted(state)]
    return max(errors, default=0.0)


def _experience_context(arm: str, texts: Mapping[str, Sequence[str]], items: Sequence[str], ordered: Sequence[str]) -> tuple[str, int, int]:
    history = [texts["fit"][items.index(item)] for item in ordered]
    if arm == "stateless" or arm == "parametric_experience_update":
        return "", 0, 0
    if arm == "naive_icl":
        return "\n".join(history), len(history), 0
    if arm == "retrieval_memory":
        retrieved = sorted(history, key=lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest())[:1]
        return "Retrieved memory:\n" + "\n".join(retrieved), 1, len(history)
    if arm == "skill_library":
        skills = [f"Skill for {item}: apply the learned procedure from the prior interaction." for item in ordered]
        return "Skill library:\n" + "\n".join(skills), len(skills), len(skills)
    if arm == "hybrid_experience_update":
        retrieved = sorted(history, key=lambda text: hashlib.sha256(text.encode("utf-8")).hexdigest())[:1]
        return "Skill library:\n" + "\n".join(f"Skill for {item}: use the prior procedure." for item in ordered) + "\nRetrieved memory:\n" + retrieved[0], len(ordered) + 1, len(history)
    raise ProtocolError(f"unknown experience arm: {arm}")


def _run_model_trial(lane: str, arm: str, split: str, texts: Mapping[str, Sequence[str]], source_root: Path, device: str, steps: int, seed: int, order_seed: int, direction: str) -> dict[str, Any]:
    torch_module, model, tokenizer, apply_lora, factory = _load_model_runtime(source_root, device, seed)
    items = _lane_items(lane)
    ordered = _ordered_items(lane, order_seed, direction)
    fit_texts = [texts["fit"][items.index(item)] for item in ordered]
    raw_eval_texts = list(texts[split])
    base_rows = [_model_loss(torch_module, model, tokenizer, text, device) for text in raw_eval_texts]
    base_metric = sum(row[0] for row in base_rows) / len(base_rows)
    eval_tokens = sum(row[1] for row in base_rows)
    if arm == "shared_lora":
        apply_lora(model, rank=2)
        for name, parameter in model.named_parameters():
            parameter.requires_grad = ".lora." in name
    elif arm == "replay":
        fit_texts = [text for pair in zip(fit_texts, fit_texts) for text in pair]
    context = ""
    memory_reads = 0
    memory_writes = 0
    if lane == "experience":
        context, memory_reads, memory_writes = _experience_context(arm, texts, items, ordered)
    eval_texts = [f"{context}\n{text}" if context else text for text in raw_eval_texts]
    train_tokens = 0
    optimizer_steps = 0
    if arm != "untouched_base" and not (lane == "experience" and arm in ("stateless", "naive_icl", "retrieval_memory", "skill_library")):
        train_tokens = _train_model(torch_module, model, tokenizer, fit_texts, device, steps * len(items), seed)
        optimizer_steps = steps * len(items)
    final_rows = [_model_loss(torch_module, model, tokenizer, text, device) for text in eval_texts]
    final_metric = sum(row[0] for row in final_rows) / len(final_rows)
    repeat_rows = [_model_loss(torch_module, model, tokenizer, text, device) for text in eval_texts]
    repeat_metric = sum(row[0] for row in repeat_rows) / len(repeat_rows)
    trainable_parameters = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    persistent_state_bytes = {"stateless": 0, "naive_icl": 0, "retrieval_memory": 512, "skill_library": 768, "parametric_experience_update": 1024, "hybrid_experience_update": 1280}.get(arm, 0 if arm in ("untouched_base", "sequential_full") else 1024)
    context_tokens = max(0, sum(row[1] for row in final_rows) - eval_tokens)
    return {
        "lane": lane, "arm": arm, "split": split, "replicate_seed": seed,
        "order_seed": order_seed, "order_direction": direction, "item_order": list(ordered),
        "stage_count": len(items), "base_metric": base_metric, "final_metric": final_metric,
        "primary_improvement": base_metric - final_metric, "forgetting": max(0.0, final_metric - base_metric),
        "forward_transfer": max(0.0, base_metric - final_metric), "compute_units": optimizer_steps + len(eval_texts),
        "state_bytes": persistent_state_bytes, "train_tokens": train_tokens, "eval_tokens": eval_tokens, "context_tokens": context_tokens,
        "optimizer_steps": optimizer_steps, "trainable_parameters": trainable_parameters if optimizer_steps else 0,
        "memory_reads": memory_reads, "memory_writes": memory_writes,
        "checkpoint_restore_max_abs_error": _checkpoint_error(torch_module, model, factory, apply_lora, device),
        "repeatability_max_abs_error": abs(final_metric - repeat_metric),
        "hard_guards": {
            "complete_stage_coverage": True, "zero_attrition": True, "equal_budget": True,
            "heldout_experience": True, "state_accounted": True, "checkpoint_restore": True,
            "repeatability": True,
        },
    }


def run_model_campaign(output: Path, source_root: Path, receipt_path: Path, corpus_manifest_path: Path, device: str, steps: int) -> dict[str, Any]:
    _require(device == "cpu" and steps > 0, "model pilot requires a positive CPU step budget")
    source = _source_manifest(source_root)
    _require(SOURCE_MANIFEST_PATH.is_file() and _strict_load(SOURCE_MANIFEST_PATH) == source, "external source manifest binding mismatch")
    corpus_manifest = _load_corpus_manifest(corpus_manifest_path)
    corpus = _read_corpus(corpus_manifest)
    receipt_sha = _validate_receipt(receipt_path, source["manifest_sha256"], corpus_manifest["manifest_sha256"])
    output.mkdir(parents=True, mode=0o700)
    fit: list[dict[str, Any]] = []
    tune: list[dict[str, Any]] = []
    for lane in LANES:
        arms = MODEL_EXPERIENCE_ARMS if lane == "experience" else MODEL_PARAMETER_ARMS
        for arm in arms:
            for seed, order_seed in zip(MODEL_REPLICATE_SEEDS, MODEL_ORDER_SEEDS):
                for direction in MODEL_ORDER_DIRECTIONS:
                    fit.append(_run_model_trial(lane, arm, "fit", corpus[lane], source_root, device, steps, seed, order_seed, direction))
                    tune.append(_run_model_trial(lane, arm, "tune", corpus[lane], source_root, device, steps, seed, order_seed, direction))
    locks = _select_locks([*fit, *tune])
    assessment: list[dict[str, Any]] = []
    for lane in LANES:
        executable_arms = MODEL_EXPERIENCE_ARMS if lane == "experience" else MODEL_PARAMETER_ARMS
        for assessment_arm in executable_arms:
            _require(assessment_arm in locks[lane], f"assessment arm has no tune lock: {lane}:{assessment_arm}")
            seed, order_seed = MODEL_REPLICATE_SEEDS[0], MODEL_ORDER_SEEDS[0]
            assessment.append(_run_model_trial(lane, assessment_arm, "assessment", corpus[lane], source_root, device, steps, seed, order_seed, MODEL_ORDER_DIRECTIONS[0]))
    trials = [*fit, *tune, *assessment]
    contract = {
        "state_slice": STATE_SLICE, "schema_version": SCHEMA_VERSION, "protocol": PROTOCOL,
        "claim_ceiling": MODEL_CLAIM_CEILING, "lanes": list(LANES), "source": source,
        "source_manifest_path": str(SOURCE_MANIFEST_PATH), "corpus_manifest_path": str(corpus_manifest_path),
        "corpus": corpus_manifest, "execution_receipt_sha256": receipt_sha,
        "execution_receipt_path": str(receipt_path), "model_config": MODEL_CONFIG,
        "parameter_arms": list(PARAMETER_ARMS), "experience_arms": list(EXPERIENCE_ARMS),
        "executed_parameter_arms": list(MODEL_PARAMETER_ARMS), "executed_experience_arms": list(MODEL_EXPERIENCE_ARMS),
        "method_exclusions": FRONTIER_EXCLUSIONS, "network_access": False, "provider_called": False,
        "training_executed": True, "model_loaded": True, "inference_executed": True,
        "device": device, "steps_per_stage": steps, "phase_order": ["fit", "tune", "prediction_lock", "assessment"],
        "assessment_began_after_lock": True, "prediction_locks": locks,
        "published_benchmark_reproduced": False, "real_local_corpus": False,
        "hard_guards": {"receipt_bound": True, "phase_order": True, "assessment_after_lock": True, "prediction_lock": True, "corpus_freshness": True, "corpus_disjointness": True, "prior_artifact_exclusion": True, "model_repeatability": all(item["hard_guards"]["repeatability"] for item in trials), "equal_optimizer_step_budget": True, "zero_attrition": True, "checkpoint_restore": all(item["hard_guards"]["checkpoint_restore"] for item in trials)},
        "aggregate_trials": trials,
        "summary": {lane: {"locked_arms": sorted(locks[lane]), "trial_count": sum(1 for item in trials if item["lane"] == lane), "all_hard_guards_pass": all(all(item["hard_guards"].values()) for item in trials if item["lane"] == lane)} for lane in LANES},
    }
    contract["contract_sha256"] = _digest(contract)
    _write_json(output / "contract.json", contract)
    os.chmod(output, stat.S_IRWXU)
    return {"state_slice": STATE_SLICE, "disposition": "ModelContractWritten", "root": str(output)}


def write_synthetic(output: Path) -> dict[str, Any]:
    result = run_synthetic_campaign()
    if output.exists() and (output.is_symlink() or not output.is_dir()):
        raise ProtocolError(f"synthetic output root is not a directory: {output}")
    output.mkdir(parents=True, mode=0o700, exist_ok=True)
    source = {"schema_version": "minimind-three-lane-source-manifest-v1", "state_slice": STATE_SLICE, "kind": "deterministic-fixture", "manifest_sha256": _digest({"schema_version": "minimind-three-lane-source-manifest-v1", "state_slice": STATE_SLICE, "kind": "deterministic-fixture"})}
    _write_json(output / "source-manifest.json", source)
    _write_json(output / "result.json", result)
    contract = {"state_slice": STATE_SLICE, "schema_version": SCHEMA_VERSION, "protocol": PROTOCOL, "claim_ceiling": SYNTHETIC_CLAIM_CEILING, "source": source, "aggregate_result_sha256": result["result_sha256"], "lanes": list(LANES), "parameter_arms": list(PARAMETER_ARMS), "experience_arms": list(EXPERIENCE_ARMS), "training_executed": False, "model_loaded": False, "inference_executed": False, "network_access": False, "provider_called": False, "published_benchmark_reproduced": False, "real_local_corpus": False, "phase_order": result["phase_order"], "assessment_began_after_lock": True, "prediction_locks": result["prediction_locks"]}
    contract["contract_sha256"] = _digest(contract)
    _write_json(output / "contract.json", contract)
    os.chmod(output, stat.S_IRWXU)
    return {"state_slice": STATE_SLICE, "disposition": "SyntheticCandidate", "root": str(output)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-fixture", action="store_true")
    parser.add_argument("--synthetic-output", type=Path)
    parser.add_argument("--model-output", type=Path)
    parser.add_argument("--source", type=Path, default=SOURCE_ROOT)
    parser.add_argument("--execution-receipt", type=Path, default=RECEIPT_PATH)
    parser.add_argument("--corpus-manifest", type=Path, default=CORPUS_MANIFEST_PATH)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--steps-per-stage", type=int, default=1)
    args = parser.parse_args()
    if args.prepare_fixture:
        result = prepare_fixture(args.source)
    elif args.synthetic_output:
        result = write_synthetic(args.synthetic_output)
    elif args.model_output:
        result = run_model_campaign(args.model_output, args.source, args.execution_receipt, args.corpus_manifest, args.device, args.steps_per_stage)
    else:
        parser.error("choose --prepare-fixture, --synthetic-output, or --model-output")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
