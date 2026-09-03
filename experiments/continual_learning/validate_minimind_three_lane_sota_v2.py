#!/usr/bin/env python3
"""Independent aggregate validator for MiniMind three-lane V2.

State slice: continual-learning-minimind-three-lane-sota-v2.
This module intentionally does not import the runner or reproduce its trial
arithmetic. It validates custody, schema, roster, phase order, signatures,
and aggregate-only output from a separate implementation.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import sys
from pathlib import Path
from typing import Any, Mapping


STATE_SLICE = "continual-learning-minimind-three-lane-sota-v2"
SCHEMA_VERSION = "minimind-three-lane-result-v2"
PROTOCOL = "minimind-three-lane-sota-v2"
REPO_ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = REPO_ROOT / "docs/research/continual-learning/292-minimind-three-lane-sota-v2-protocol.md"
REVIEW_PACKET_PATH = REPO_ROOT / "docs/research/continual-learning/293-minimind-three-lane-sota-v2-review-packet.md"
MANIFEST_PATH = REPO_ROOT / "docs/research/continual-learning/294-minimind-three-lane-sota-v2-implementation-manifest.json"
TRUST_BUNDLE_PATH = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-three-lane-sota-v2-trust-bundle-20260903.json")
REVIEWER_REGISTRY_PATH = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-three-lane-sota-v2-reviewer-registry-20260903.json")
OPERATOR_BINDING_PATH = Path("/Users/shaanp/Documents/research-artifacts/continual-learning-minimind-three-lane-sota-v2-operator-binding-20260903.json")
TRUST_BUNDLE_FILE_SHA256 = "5487b231e29e2a6f5ccaed8babb0065caa9fd5f8b700a22a940da614a45adfbd"
OPERATOR_ID = "shaanp"
OPERATOR_PRINCIPAL_ID = "principal-operator-shaanp"
REVIEWER_ROLE = "independent"
LANES = ("task", "domain", "experience")
ITEMS = {
    "task": ("ag_news", "amazon_reviews", "yelp", "dbpedia", "yahoo_answers"),
    "domain": ("materials", "clinical", "finance"),
    "experience": ("software", "forecasting", "database"),
}
SPLITS = ("fit", "tune", "assessment")
ORDER_DIRECTIONS = ("forward", "reverse")
REPLICATE_SEEDS = (2026090301, 2026090302, 2026090303)
ORDER_SEEDS = (7301, 7302, 7303)
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
FROZEN_REVIEW_FILES = (
    "AGENTS.md",
    "docs/research/continual-learning/292-minimind-three-lane-sota-v2-protocol.md",
    "docs/research/continual-learning/293-minimind-three-lane-sota-v2-review-packet.md",
    "docs/research/continual-learning/294-minimind-three-lane-sota-v2-implementation-manifest.json",
    "experiments/continual_learning/minimind_three_lane_sota_v2.py",
    "experiments/continual_learning/validate_minimind_three_lane_sota_v2.py",
    "experiments/continual_learning/tests/test_minimind_three_lane_sota_v2.py",
)


class ValidationError(ValueError):
    """Raised when the external result does not satisfy the frozen contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _strict_load(path: Path) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValidationError(f"duplicate JSON key: {path}:{key}")
            result[key] = value
        return result

    def constant(value: str) -> None:
        raise ValidationError(f"non-finite JSON constant: {path}:{value}")

    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"invalid JSON: {path}") from error


def _unit(*parts: object) -> float:
    payload = "|".join((STATE_SLICE, *(str(part) for part in parts))).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") / float(1 << 64)


def _ordered_items(lane: str, order_seed: int, direction: str) -> list[str]:
    ordered = list(enumerate(ITEMS[lane]))
    ordered.sort(key=lambda item: (_unit("order", lane, order_seed, item[1]), item[0]))
    if direction == "reverse":
        ordered.reverse()
    return [item[1] for item in ordered]


def _frozen_digests() -> dict[str, str]:
    result: dict[str, str] = {}
    for relative in FROZEN_REVIEW_FILES:
        path = REPO_ROOT / relative
        _require(path.is_file() and not path.is_symlink(), f"frozen file missing: {relative}")
        result[relative] = _sha256_file(path)
    return result


def _verify_ed25519(public_key_hex: str, signature_hex: str, message: bytes, failure: str) -> None:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        _require(isinstance(public_key_hex, str) and len(public_key_hex) == 64, "Ed25519 public key encoding mismatch")
        _require(isinstance(signature_hex, str) and len(signature_hex) == 128, "Ed25519 signature encoding mismatch")
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex)).verify(bytes.fromhex(signature_hex), message)
    except (ImportError, InvalidSignature, ValueError, TypeError) as error:
        raise ValidationError(failure) from error


def _validate_trust_and_receipt(receipt_path: Path, source_sha: str, corpus_sha: str) -> str:
    _require(receipt_path.is_file() and not receipt_path.is_symlink() and stat.S_IMODE(receipt_path.stat().st_mode) == 0o600, "execution receipt custody mismatch")
    receipt = _strict_load(receipt_path)
    expected = {"schema_version", "state_slice", "protocol", "review_packet_path", "review_packet_sha256", "reviewed_file_digests", "reviewer_registry_path", "reviewer_registry_sha256", "reviewer_identity", "reviewer_role", "reviewer_certificate_sha256", "reviewer_public_key_hex", "operator_identity", "operator_binding_path", "operator_binding_sha256", "source_manifest_sha256", "corpus_manifest_sha256", "disposition", "signature_algorithm", "signature"}
    _require(set(receipt) == expected and receipt["schema_version"] == "minimind-three-lane-sota-v2-execution-receipt" and receipt["state_slice"] == STATE_SLICE and receipt["protocol"] == PROTOCOL, "execution receipt schema mismatch")
    _require(receipt["reviewer_role"] == REVIEWER_ROLE and receipt["reviewer_identity"] != OPERATOR_ID and receipt["operator_identity"] == OPERATOR_ID and receipt["disposition"] == "ACCEPTED_FOR_MODEL_EXECUTION" and receipt["signature_algorithm"] == "Ed25519", "execution receipt identity or disposition mismatch")
    _require(receipt["review_packet_path"] == str(REVIEW_PACKET_PATH) and receipt["review_packet_sha256"] == _sha256_file(REVIEW_PACKET_PATH), "execution receipt packet binding mismatch")
    _require(receipt["reviewed_file_digests"] == _frozen_digests(), "execution receipt frozen-file digest mismatch")
    _require(receipt["source_manifest_sha256"] == source_sha and receipt["corpus_manifest_sha256"] == corpus_sha, "execution receipt corpus/source binding mismatch")
    bundle = _strict_load(TRUST_BUNDLE_PATH)
    _require(TRUST_BUNDLE_PATH.is_file() and not TRUST_BUNDLE_PATH.is_symlink() and _sha256_file(TRUST_BUNDLE_PATH) == TRUST_BUNDLE_FILE_SHA256, "trust bundle fingerprint mismatch")
    _require(bundle["state_slice"] == STATE_SLICE and bundle["schema_version"] == "minimind-three-lane-sota-trust-bundle-v2", "trust bundle identity mismatch")
    review_root = bundle["authority"]["review_root"]
    operator_root = bundle["authority"]["operator_root"]
    _require(hashlib.sha256(bytes.fromhex(review_root["public_key_hex"])).hexdigest() == review_root["public_key_sha256"] and hashlib.sha256(bytes.fromhex(operator_root["public_key_hex"])).hexdigest() == operator_root["public_key_sha256"] and review_root["public_key_hex"] != operator_root["public_key_hex"], "trust root binding mismatch")
    _require(bundle["bundle_sha256"] == _digest({key: value for key, value in bundle.items() if key not in {"bundle_sha256", "bundle_signature"}}), "trust bundle digest mismatch")
    bundle_body = {key: value for key, value in bundle.items() if key not in {"bundle_sha256", "bundle_signature"}}
    _verify_ed25519(review_root["public_key_hex"], bundle["bundle_signature"]["signature_hex"], json.dumps(bundle_body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"), "trust bundle signature failed")
    registry_path = Path(receipt["reviewer_registry_path"]).resolve()
    _require(registry_path == REVIEWER_REGISTRY_PATH.resolve() and registry_path.is_file() and not registry_path.is_symlink() and _sha256_file(registry_path) == receipt["reviewer_registry_sha256"], "reviewer registry path or digest mismatch")
    registry = _strict_load(registry_path)
    _require(registry == bundle["reviewer_registry"], "reviewer registry is not trust-bundle bound")
    reviewer = next((item for item in registry["reviewers"] if item.get("identity") == receipt["reviewer_identity"]), None)
    _require(reviewer is not None and reviewer["role"] == REVIEWER_ROLE and reviewer["public_key_hex"] == receipt["reviewer_public_key_hex"] and reviewer["certificate_sha256"] == receipt["reviewer_certificate_sha256"], "reviewer certificate resolution mismatch")
    _verify_ed25519(review_root["public_key_hex"], reviewer["certificate_signature"]["signature_hex"], json.dumps(reviewer["certificate"], sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"), "reviewer certificate signature failed")
    binding_path = Path(receipt["operator_binding_path"]).resolve()
    _require(binding_path == OPERATOR_BINDING_PATH.resolve() and binding_path.is_file() and not binding_path.is_symlink() and _sha256_file(binding_path) == receipt["operator_binding_sha256"], "operator binding path or digest mismatch")
    binding = _strict_load(binding_path)
    required_binding = {"schema_version", "state_slice", "protocol", "packet_sha256", "operator_identity", "operator_principal_id", "operator_key_id", "audience", "nonce", "binding_sha256", "signature_algorithm", "signature_hex"}
    _require(set(binding) == required_binding and binding["schema_version"] == "minimind-three-lane-sota-v2-operator-binding-v2" and binding["state_slice"] == STATE_SLICE and binding["protocol"] == PROTOCOL and binding["packet_sha256"] == _sha256_file(REVIEW_PACKET_PATH) and binding["operator_identity"] == OPERATOR_ID and binding["operator_principal_id"] == OPERATOR_PRINCIPAL_ID and binding["operator_key_id"] == operator_root["key_id"] and binding["audience"] == "minimind-three-lane-sota-v2-runner", "operator binding identity mismatch")
    _require(binding["binding_sha256"] == _digest({key: value for key, value in binding.items() if key not in {"binding_sha256", "signature_algorithm", "signature_hex"}}), "operator binding digest mismatch")
    binding_body = {key: value for key, value in binding.items() if key not in {"binding_sha256", "signature_algorithm", "signature_hex"}}
    _verify_ed25519(operator_root["public_key_hex"], binding["signature_hex"], json.dumps(binding_body, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8"), "operator binding signature failed")
    receipt_payload = json.dumps({key: value for key, value in receipt.items() if key != "signature"}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    _verify_ed25519(receipt["reviewer_public_key_hex"], receipt["signature"], receipt_payload, "execution receipt signature failed")
    return _sha256_file(receipt_path)


def _validate_source_manifest(source: Mapping[str, Any]) -> None:
    expected = {"schema_version", "state_slice", "url", "commit", "remote", "license", "checkout", "required_files", "manifest_sha256"}
    _require(set(source) == expected and source["schema_version"] == "minimind-three-lane-source-manifest-v2" and source["state_slice"] == STATE_SLICE, "source manifest schema mismatch")
    _require(source["manifest_sha256"] == _digest({key: value for key, value in source.items() if key != "manifest_sha256"}), "source manifest digest mismatch")
    _require(source["commit"] == "7a6fddd63a30c06b2fdd5fac4089922b29bc841b" and "jingyaogong/minimind" in source["remote"] and source["license"] == "Apache-2.0", "source identity mismatch")
    root = Path(source["checkout"]).resolve()
    _require(root.is_dir() and not root.is_symlink(), "source checkout custody mismatch")
    for relative, expected_sha in source["required_files"].items():
        path = root / relative
        _require(path.is_file() and not path.is_symlink() and _sha256_file(path) == expected_sha, f"source file digest mismatch: {relative}")


def _validate_corpus_manifest(corpus: Mapping[str, Any]) -> None:
    expected = {"schema_version", "state_slice", "corpus_identity", "root", "fixture_only", "published_benchmark_reproduced", "prior_artifact_exclusion", "files", "global_record_ids_sha256", "global_author_ids_sha256", "manifest_sha256"}
    _require(set(corpus) == expected and corpus["schema_version"] == "minimind-three-lane-corpus-manifest-v2" and corpus["state_slice"] == STATE_SLICE, "corpus manifest schema mismatch")
    _require(corpus["manifest_sha256"] == _digest({key: value for key, value in corpus.items() if key != "manifest_sha256"}) and corpus["fixture_only"] is True and corpus["published_benchmark_reproduced"] is False and corpus["prior_artifact_exclusion"] is True, "corpus identity or digest mismatch")
    root = Path(corpus["root"]).resolve()
    _require(root.is_dir() and not root.is_symlink() and stat.S_IMODE(root.stat().st_mode) == 0o700, "corpus root custody mismatch")
    expected_keys = {(lane, split) for lane in LANES for split in SPLITS}
    observed: set[tuple[str, str]] = set()
    record_ids: list[str] = []
    author_ids: list[str] = []
    for entry in corpus["files"]:
        _require(set(entry) == {"lane", "split", "path", "sha256", "record_count"}, "corpus file schema mismatch")
        key = (entry["lane"], entry["split"])
        path = Path(entry["path"]).resolve()
        _require(key in expected_keys and key not in observed and path.parent == root and path.is_file() and not path.is_symlink() and _sha256_file(path) == entry["sha256"], "corpus file custody mismatch")
        observed.add(key)
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            _require(set(row) == {"record_id", "author_id", "text", "target"} and all(isinstance(row[key], str) and row[key] for key in row), "corpus record schema mismatch")
            rows.append(row)
        _require(len(rows) == entry["record_count"] == len(ITEMS[entry["lane"]]), "corpus record count mismatch")
        record_ids.extend(row["record_id"] for row in rows)
        author_ids.extend(row["author_id"] for row in rows)
    _require(observed == expected_keys and len(record_ids) == len(set(record_ids)) and len(author_ids) == len(set(author_ids)), "corpus roster or disjointness mismatch")
    _require(corpus["global_record_ids_sha256"] == _digest(sorted(record_ids)) and corpus["global_author_ids_sha256"] == _digest(sorted(author_ids)), "corpus global identity digest mismatch")


def _validate_trial(trial: Mapping[str, Any], *, model: bool) -> None:
    expected = {"lane", "arm", "split", "replicate_seed", "order_seed", "order_direction", "item_order", "stage_count", "base_metric", "final_metric", "primary_improvement", "forgetting", "forward_transfer", "compute_units", "state_bytes", "hard_guards"}
    if model:
        expected |= {"checkpoint_restore_max_abs_error", "repeatability_max_abs_error", "train_tokens", "eval_tokens", "context_tokens", "optimizer_steps", "trainable_parameters", "memory_reads", "memory_writes"}
    _require(set(trial) == expected, "trial schema mismatch")
    lane = trial["lane"]
    arms = MODEL_EXPERIENCE_ARMS if lane == "experience" and model else EXPERIENCE_ARMS if lane == "experience" else MODEL_PARAMETER_ARMS if model else PARAMETER_ARMS
    _require(lane in LANES and trial["arm"] in arms and trial["split"] in SPLITS and trial["order_direction"] in ORDER_DIRECTIONS, "trial identity mismatch")
    _require(trial["item_order"] == _ordered_items(lane, trial["order_seed"], trial["order_direction"]) and trial["stage_count"] == len(ITEMS[lane]) and trial["compute_units"] > 0 and trial["state_bytes"] >= 0, "trial order or accounting mismatch")
    for key in ("base_metric", "final_metric", "primary_improvement", "forgetting", "forward_transfer") + (("checkpoint_restore_max_abs_error", "repeatability_max_abs_error") if model else ()):
        _require(isinstance(trial[key], (int, float)) and not isinstance(trial[key], bool) and math.isfinite(trial[key]), f"trial numeric field invalid: {key}")
    if model:
        for key in ("train_tokens", "eval_tokens", "context_tokens", "optimizer_steps", "trainable_parameters", "memory_reads", "memory_writes"):
            _require(isinstance(trial[key], int) and not isinstance(trial[key], bool) and trial[key] >= 0, f"trial accounting field invalid: {key}")
    guard_keys = {"complete_stage_coverage", "zero_attrition", "equal_budget", "heldout_experience", "state_accounted"} | ({"checkpoint_restore", "repeatability"} if model else set())
    _require(set(trial["hard_guards"]) == guard_keys and all(value is True for value in trial["hard_guards"].values()), "trial hard guard failure")
    if model:
        _require(trial["checkpoint_restore_max_abs_error"] <= 1e-12 and trial["repeatability_max_abs_error"] <= 1e-12, "model repeatability or checkpoint restore tolerance exceeded")


def _validate_campaign(root: Path, kind: str) -> dict[str, Any]:
    _require(kind in {"synthetic", "model"}, "unknown validation kind")
    root = root.resolve()
    _require(root.is_dir() and not root.is_symlink() and stat.S_IMODE(root.stat().st_mode) == 0o700, "artifact root custody mismatch")
    required = {"contract.json", "result.json", "source-manifest.json"} if kind == "synthetic" else {"contract.json"}
    _require({path.name for path in root.iterdir()} == required, "artifact root must contain aggregate-only files")
    contract = _strict_load(root / "contract.json")
    _require(contract["state_slice"] == STATE_SLICE and contract["schema_version"] == SCHEMA_VERSION and contract["protocol"] == PROTOCOL and contract["contract_sha256"] == _digest({key: value for key, value in contract.items() if key != "contract_sha256"}), "contract identity or digest mismatch")
    _require(contract["published_benchmark_reproduced"] is False and contract["real_local_corpus"] is False and contract["network_access"] is False and contract["provider_called"] is False and contract["phase_order"] == ["fit", "tune", "prediction_lock", "assessment"] and contract["assessment_began_after_lock"] is True, "campaign claim or phase boundary mismatch")
    if kind == "synthetic":
        source_manifest = _strict_load(root / "source-manifest.json")
        _require(source_manifest == contract["source"], "synthetic source binding mismatch")
        result = _strict_load(root / "result.json")
        _require(result["result_sha256"] == _digest({key: value for key, value in result.items() if key != "result_sha256"}) and contract["aggregate_result_sha256"] == result["result_sha256"], "synthetic result digest mismatch")
        _require(contract["training_executed"] is False and contract["model_loaded"] is False and contract["inference_executed"] is False, "synthetic execution boundary mismatch")
        trials = result["aggregate_trials"]
        locks = result["prediction_locks"]
        expected_per_arm = len(REPLICATE_SEEDS) * len(ORDER_DIRECTIONS)
        expected_arms = {lane: (EXPERIENCE_ARMS if lane == "experience" else PARAMETER_ARMS) for lane in LANES}
    else:
        _require(contract["training_executed"] is True and contract["model_loaded"] is True and contract["inference_executed"] is True and contract["device"] == "cpu", "model execution boundary mismatch")
        _validate_source_manifest(contract["source"])
        source_manifest_path = Path(contract["source_manifest_path"]).resolve()
        _require(source_manifest_path.is_file() and not source_manifest_path.is_symlink() and _strict_load(source_manifest_path) == contract["source"], "model source manifest path binding mismatch")
        _validate_corpus_manifest(contract["corpus"])
        _require(Path(contract["corpus_manifest_path"]).resolve() == Path(contract["corpus"]["root"]).resolve() / "corpus-manifest.json", "model corpus manifest path binding mismatch")
        receipt_path = Path(contract["execution_receipt_path"]).resolve()
        _require(contract["execution_receipt_sha256"] == _validate_trust_and_receipt(receipt_path, contract["source"]["manifest_sha256"], contract["corpus"]["manifest_sha256"]), "model receipt binding mismatch")
        trials = contract["aggregate_trials"]
        locks = contract["prediction_locks"]
        expected_per_arm = 1
        expected_arms = {lane: (MODEL_EXPERIENCE_ARMS if lane == "experience" else MODEL_PARAMETER_ARMS) for lane in LANES}
    _require(isinstance(trials, list) and isinstance(locks, dict) and set(locks) == set(LANES), "campaign roster container mismatch")
    expected_keys: set[tuple[str, str, str, int, int, str]] = set()
    for trial in trials:
        _validate_trial(trial, model=kind == "model")
        identity = (trial["lane"], trial["arm"], trial["split"], trial["replicate_seed"], trial["order_seed"], trial["order_direction"])
        _require(identity not in expected_keys, "duplicate aggregate trial")
        expected_keys.add(identity)
    for lane in LANES:
        _require(set(locks[lane]) == set(expected_arms[lane]), f"prediction lock roster mismatch: {lane}")
        for arm in expected_arms[lane]:
            for split in SPLITS:
                expected = {(lane, arm, split, seed, order_seed, direction) for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS) for direction in ORDER_DIRECTIONS} if kind == "synthetic" else {(lane, arm, split, 2026090301, 7301, "forward")}
                observed = {identity for identity in expected_keys if identity[:3] == (lane, arm, split)}
                _require(observed == expected, f"exact trial roster mismatch: {lane}:{arm}:{split}")
    expected_trial_count = (len(PARAMETER_ARMS) * 2 + len(EXPERIENCE_ARMS)) * 3 * len(REPLICATE_SEEDS) * len(ORDER_DIRECTIONS) if kind == "synthetic" else (len(MODEL_PARAMETER_ARMS) * 2 + len(MODEL_EXPERIENCE_ARMS)) * 3
    _require(len(trials) == expected_trial_count, "trial count mismatch")
    return {"kind": kind, "root": str(root), "disposition": "IndependentAggregateValid", "trial_count": len(trials), "state_slice": STATE_SLICE}


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] not in {"synthetic", "model"}:
        raise SystemExit("usage: validate_minimind_three_lane_sota_v2.py synthetic|model ARTIFACT_ROOT")
    try:
        print(json.dumps(_validate_campaign(Path(sys.argv[2]), sys.argv[1]), sort_keys=True))
        return 0
    except ValidationError as error:
        print(f"VALIDATION_REJECTED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
