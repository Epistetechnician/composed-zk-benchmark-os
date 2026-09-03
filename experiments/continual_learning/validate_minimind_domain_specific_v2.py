#!/usr/bin/env python3
"""Independent V2 validator for the MiniMind continual-learning lane.

State slice: continual-learning-minimind-domain-specific-v2.

This validator does not import the V2 runner. It independently recomputes the
synthetic arithmetic and checks exact identities, source custody, model
contract structure, lock ordering, and aggregate-only output.
"""

from __future__ import annotations

import hashlib
import json
import math
import stat
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "continual-learning-minimind-domain-specific-v2"
SCHEMA_VERSION = "minimind-domain-sequence-result-v2"
PROTOCOL = "minimind-domain-specific-sequence-v2"
SYNTHETIC_CLAIM_CEILING = "LocalDevelopmentMiniMindDomainSequenceSyntheticOnly"
MODEL_CLAIM_CEILING = "LocalDevelopmentMiniMindDomainSequenceQualificationV2"
UPSTREAM_URL = "https://github.com/jingyaogong/minimind"
UPSTREAM_COMMIT = "7a6fddd63a30c06b2fdd5fac4089922b29bc841b"
REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAINS = ("materials", "clinical", "finance")
SPLITS = ("fit", "tune", "assessment")
ORDER_DIRECTIONS = ("forward", "reverse")
REPLICATE_SEEDS = (2026090204, 2026090205, 2026090206)
ORDER_SEEDS = (9511, 9512, 9513)
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
MAX_SEQ_LEN = 340
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


class ValidationError(ValueError):
    """Raised when an artifact violates the V2 contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


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
    indexed = list(enumerate(DOMAINS))
    indexed.sort(key=lambda item: (_unit("order", order_seed, item[1]), item[0]))
    if direction == "reverse":
        indexed.reverse()
    return tuple(domain for _, domain in indexed)


def _prediction_vector(
    arm: str,
    shared_state: Sequence[float],
    adapters: Mapping[str, Sequence[float]],
    domain: str,
) -> tuple[float, ...]:
    if arm == "domain_adapters":
        return _add(shared_state, adapters.get(domain, (0.0,) * VECTOR_DIMENSION))
    return tuple(shared_state)


def _trial(arm: str, split: str, seed: int, order_seed: int, direction: str) -> dict[str, Any]:
    base = _anchor()
    shared_state = base
    adapters: dict[str, tuple[float, ...]] = {}
    fit_targets = {domain: _target(domain, "fit", seed) for domain in DOMAINS}
    evaluation_targets = {domain: _target(domain, split, seed) for domain in DOMAINS}
    order = _ordered_domains(order_seed, direction)
    learned_losses: dict[str, float] = {}
    stage_metrics: list[dict[str, Any]] = []
    checkpoint_errors = []
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

        encoded = json.dumps(
            {"shared_state": list(shared_state), "adapters": {key: list(value) for key, value in adapters.items()}},
            sort_keys=True,
            separators=(",", ":"),
        )
        restored = json.loads(encoded)
        errors = [abs(left - right) for left, right in zip(shared_state, restored["shared_state"])]
        for item, values in adapters.items():
            errors.extend(abs(left - right) for left, right in zip(values, restored["adapters"][item]))
        checkpoint_error = max(errors, default=0.0)
        checkpoint_errors.append(checkpoint_error)
        domain_losses = {
            item: _loss(_prediction_vector(arm, shared_state, adapters, item), evaluation_targets[item])
            for item in DOMAINS
        }
        learned_losses.setdefault(domain, domain_losses[domain])
        max_forgetting = max(
            (max(0.0, domain_losses[item] - learned_losses[item]) for item in learned_losses),
            default=0.0,
        )
        stage_metrics.append(
            {
                "stage_index": stage_index,
                "domain": domain,
                "domain_losses": domain_losses,
                "mean_loss": sum(domain_losses.values()) / len(DOMAINS),
                "max_forgetting": max_forgetting,
                "update_units": UPDATE_UNITS_PER_STAGE,
                "checkpoint_restore_max_abs_error": checkpoint_error,
            }
        )
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
        "stage_metrics": stage_metrics,
        "base_mean_loss": base_mean_loss,
        "final_mean_loss": final_mean_loss,
        "primary_improvement": base_mean_loss - final_mean_loss,
        "max_forgetting": max_forgetting,
        "compute_units": UPDATE_UNITS_PER_STAGE * len(DOMAINS),
        "token_budget_units": UPDATE_UNITS_PER_STAGE * len(DOMAINS) * MAX_SEQ_LEN,
        "checkpoint_restore_max_abs_error": max_checkpoint_error,
        "hard_guards": {
            "forgetting": max_forgetting <= MAX_FORGETTING,
            "checkpoint_restore": max_checkpoint_error <= MAX_CHECKPOINT_ERROR,
            "complete_stage_coverage": len(stage_metrics) == len(DOMAINS),
            "zero_attrition": True,
            "equal_token_budget": True,
        },
    }


def _expected_identities() -> set[tuple[Any, ...]]:
    return {
        (arm, split, seed, order_seed, direction)
        for split in SPLITS
        for arm in ARMS
        for seed, order_seed in zip(REPLICATE_SEEDS, ORDER_SEEDS)
        for direction in ORDER_DIRECTIONS
    }


def _summary(trials: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_split_arm: dict[str, Any] = {}
    for split in SPLITS:
        for arm in ARMS:
            subset = [item for item in trials if item["split"] == split and item["arm"] == arm]
            _require(subset, f"missing trials for {split}:{arm}")
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
                "all_hard_guards_pass": all(all(item["hard_guards"].values()) for item in subset)
                and max_order_delta <= MAX_ORDER_DELTA,
            }
    tune = {arm: by_split_arm[f"tune:{arm}"] for arm in ARMS}
    locked_arm = min(ARMS, key=lambda arm: (tune[arm]["mean_final_loss"], ARMS.index(arm)))
    assessment = by_split_arm[f"assessment:{locked_arm}"]
    return {
        "by_split_arm": by_split_arm,
        "prediction_lock": {"selection_split": "tune", "locked_arm": locked_arm, "selection_metric": "mean_final_loss"},
        "disposition": "SyntheticCandidate" if assessment["all_hard_guards_pass"] and assessment["mean_primary_improvement"] > 0.0 else "NoCandidate",
    }


def _validate_source(observed: Mapping[str, Any]) -> None:
    manifest = observed.get("manifest")
    _require(isinstance(manifest, dict), "source manifest object missing")
    _require(observed.get("manifest_sha256") == _digest(manifest), "source manifest digest mismatch")
    _require(manifest.get("state_slice") == STATE_SLICE, "source state slice mismatch")
    _require(manifest.get("url") == UPSTREAM_URL, "source URL mismatch")
    _require(manifest.get("commit") == UPSTREAM_COMMIT, "source commit mismatch")
    _require(manifest.get("license") == "Apache-2.0", "source license mismatch")
    root = Path(manifest.get("checkout", "")).resolve()
    _require(root.is_dir() and REPO_ROOT not in root.parents, "source checkout path invalid")
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=False, capture_output=True, text=True)
    _require(head.returncode == 0 and head.stdout.strip() == UPSTREAM_COMMIT, "source checkout commit mismatch")
    status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], check=False, capture_output=True, text=True)
    _require(status.returncode == 0 and status.stdout == "", "source checkout is dirty")
    remote = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"], check=False, capture_output=True, text=True)
    _require(remote.stdout.strip() in {UPSTREAM_URL, f"{UPSTREAM_URL}.git"}, "source remote mismatch")
    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    _require("Apache License" in license_text and "Version 2.0" in license_text, "source license is not Apache-2.0")
    rows = manifest.get("required_files")
    _require([item.get("path") for item in rows] == list(REQUIRED_SOURCE_FILES), "source file roster mismatch")
    for row in rows:
        path = root / row["path"]
        _require(path.is_file() and not path.is_symlink(), f"source file missing: {row['path']}")
        _require(row.get("byte_len") == path.stat().st_size, f"source byte length mismatch: {row['path']}")
        _require(row.get("sha256") == _sha256_file(path), f"source digest mismatch: {row['path']}")


def _validate_corpus(observed: Mapping[str, Any]) -> None:
    manifest = observed.get("manifest")
    _require(isinstance(manifest, dict), "corpus manifest object missing")
    _require(observed.get("manifest_sha256") == _digest(manifest), "corpus manifest digest mismatch")
    _require(manifest.get("state_slice") == STATE_SLICE, "corpus state slice mismatch")
    domains = manifest.get("domains")
    _require(isinstance(domains, dict) and set(domains) == set(DOMAINS), "corpus domain roster mismatch")
    for domain in DOMAINS:
        entries = domains[domain]
        _require(set(entries) == set(SPLITS), f"corpus split roster mismatch for {domain}")
        for split in SPLITS:
            row = entries[split]
            path = Path(row["path"]).resolve()
            _require(path.is_file() and not path.is_symlink() and REPO_ROOT not in path.parents, f"corpus path invalid: {path}")
            _require(row.get("sha256") == _sha256_file(path), f"corpus digest mismatch: {path}")
            _require(isinstance(row.get("record_count"), int) and row["record_count"] > 0, f"corpus record count invalid: {path}")


def _validate_trial_roster(trials: Any) -> None:
    _require(isinstance(trials, list), "trial list missing")
    _require(len(trials) == len(_expected_identities()), "trial count mismatch")
    identities = {
        (item.get("arm"), item.get("split"), item.get("replicate_seed"), item.get("order_seed"), item.get("order_direction"))
        for item in trials
    }
    _require(identities == _expected_identities(), "exact trial identity roster mismatch")


def validate_artifact(root: Path) -> dict[str, Any]:
    root = root.resolve()
    contract_path = root / "contract.json"
    _require(contract_path.is_file(), "contract.json missing")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("claim_ceiling") == MODEL_CLAIM_CEILING:
        return validate_model_contract(root, contract)
    _require((root / "source-manifest.json").is_file(), "source-manifest.json missing")
    _require((root / "result.json").is_file(), "result.json missing")
    source = json.loads((root / "source-manifest.json").read_text(encoding="utf-8"))
    result = json.loads((root / "result.json").read_text(encoding="utf-8"))
    _require(contract.get("state_slice") == STATE_SLICE, "contract state slice mismatch")
    _require(contract.get("schema_version") == SCHEMA_VERSION, "contract schema mismatch")
    _require(contract.get("protocol") == PROTOCOL, "contract protocol mismatch")
    _require(contract.get("claim_ceiling") == SYNTHETIC_CLAIM_CEILING, "synthetic claim ceiling mismatch")
    _require(contract.get("contract_sha256") == _digest({key: value for key, value in contract.items() if key != "contract_sha256"}), "contract digest mismatch")
    _validate_source(source)
    _require(contract.get("source") == source, "contract/source mismatch")
    _require(result.get("state_slice") == STATE_SLICE and result.get("schema_version") == SCHEMA_VERSION, "result identity mismatch")
    _require(result.get("claim_ceiling") == SYNTHETIC_CLAIM_CEILING, "result claim ceiling mismatch")
    _require(result.get("training_executed") is False and result.get("model_loaded") is False and result.get("inference_executed") is False, "synthetic execution flags mismatch")
    _require(result.get("network_access") is False and result.get("provider_called") is False, "synthetic external access flags mismatch")
    _validate_trial_roster(result.get("trials"))
    for observed in result["trials"]:
        identity = (observed["arm"], observed["split"], observed["replicate_seed"], observed["order_seed"], observed["order_direction"])
        _require(_digest(observed) == _digest(_trial(*identity[:2], identity[2], identity[3], identity[4])), f"synthetic arithmetic mismatch: {identity}")
    _require(_digest(result.get("summary")) == _digest(_summary(result["trials"])), "synthetic summary mismatch")
    _require(result.get("result_sha256") == _digest({key: value for key, value in result.items() if key != "result_sha256"}), "result digest mismatch")
    return {"valid": True, "state_slice": STATE_SLICE, "claim_ceiling": SYNTHETIC_CLAIM_CEILING, "disposition": result["summary"]["disposition"], "trial_count": len(result["trials"])}


def validate_model_contract(root: Path, contract: Mapping[str, Any] | None = None) -> dict[str, Any]:
    root = root.resolve()
    if contract is None:
        contract = json.loads((root / "contract.json").read_text(encoding="utf-8"))
    _require(root != REPO_ROOT and REPO_ROOT not in root.parents, "model output root must remain external")
    _require(stat.S_IMODE(root.stat().st_mode) == 0o700, "model output root is not owner-only")
    _require(set(path.name for path in root.iterdir()) == {"contract.json"}, "model output contains non-aggregate files")
    _require(contract.get("state_slice") == STATE_SLICE, "model contract state slice mismatch")
    _require(contract.get("schema_version") == SCHEMA_VERSION, "model contract schema mismatch")
    _require(contract.get("protocol") == PROTOCOL, "model contract protocol mismatch")
    _require(contract.get("claim_ceiling") == MODEL_CLAIM_CEILING, "model claim ceiling mismatch")
    _require(contract.get("contract_sha256") == _digest({key: value for key, value in contract.items() if key != "contract_sha256"}), "model contract digest mismatch")
    _require(contract.get("training_executed") is True and contract.get("model_loaded") is True and contract.get("inference_executed") is True, "model execution flags mismatch")
    _require(contract.get("network_access") is False and contract.get("provider_called") is False, "model external access flags mismatch")
    _require(contract.get("phase_order") == ["fit", "tune", "prediction_lock", "assessment"], "model phase order mismatch")
    _require(contract.get("assessment_began_after_lock") is True, "assessment-before-lock guard failed")
    _validate_source(contract["source"])
    _validate_corpus(contract["corpus"])
    _validate_trial_roster(contract.get("trials"))
    for item in contract["trials"]:
        _require(item.get("repeatability_checked") is True, "model repeatability guard missing")
        _require(item.get("token_budget_units") == contract["steps_per_stage"] * len(DOMAINS) * MAX_SEQ_LEN, "model token budget mismatch")
        _require(all(item.get("hard_guards", {}).values()), "model hard guard failed")
    _require(contract.get("prediction_lock") == contract["summary"]["prediction_lock"], "model lock mismatch")
    _require(_digest(contract.get("summary")) == _digest(_summary(contract["trials"])), "model summary mismatch")
    return {"valid": True, "state_slice": STATE_SLICE, "claim_ceiling": MODEL_CLAIM_CEILING, "disposition": "ModelContractValid", "trial_count": len(contract["trials"])}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_artifact(args.artifact_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
