#!/usr/bin/env python3
"""Independent validator for the MiniMind domain-sequence fixture.

State slice: continual-learning-minimind-domain-specific-v1.

This file deliberately does not import the campaign runner. It recomputes the
synthetic trials, summary, source manifest digest, coverage, and fail-closed
execution flags from the frozen contract.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence


STATE_SLICE = "continual-learning-minimind-domain-specific-v1"
SCHEMA_VERSION = "continual-learning-minimind-domain-sequence-result-v1"
PROTOCOL = "minimind-domain-specific-sequence-v1"
CLAIM_CEILING = "LocalDevelopmentMiniMindDomainSequenceSyntheticOnly"
UPSTREAM_URL = "https://github.com/jingyaogong/minimind.git"
UPSTREAM_COMMIT = "7a6fddd63a30c06b2fdd5fac4089922b29bc841b"
DOMAINS = ("domain_a", "domain_b", "domain_c")
SPLITS = ("fit", "tune", "assessment")
ORDER_DIRECTIONS = ("forward", "reverse")
REPLICATE_SEEDS = (2026090201, 2026090202, 2026090203)
ORDER_SEEDS = (9401, 9402, 9403)
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
    """Raised when an artifact violates the independent contract."""


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
    return tuple(1.0 if start <= index < start + 2 else 0.0 for index in range(VECTOR_DIMENSION)
    )


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
            }
        )

    base_mean_loss = sum(_loss(base, evaluation_targets[domain]) for domain in DOMAINS) / len(DOMAINS)
    final_mean_loss = stage_metrics[-1]["mean_loss"]
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
        "max_forgetting": max(item["max_forgetting"] for item in stage_metrics),
        "compute_units": UPDATE_UNITS_PER_STAGE * len(DOMAINS),
        "checkpoint_restore_max_abs_error": 0.0,
        "hard_guards": {
            "forgetting": max(item["max_forgetting"] for item in stage_metrics) <= MAX_FORGETTING,
            "checkpoint_restore": True,
            "complete_stage_coverage": len(stage_metrics) == len(DOMAINS),
        },
    }


def _summary(trials: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_split_arm: dict[str, Any] = {}
    for split in SPLITS:
        for arm in ARMS:
            subset = [item for item in trials if item["split"] == split and item["arm"] == arm]
            by_split_arm[f"{split}:{arm}"] = {
                "trial_count": len(subset),
                "mean_primary_improvement": sum(item["primary_improvement"] for item in subset) / len(subset),
                "mean_final_loss": sum(item["final_mean_loss"] for item in subset) / len(subset),
                "max_forgetting": max(item["max_forgetting"] for item in subset),
                "order_deltas": {
                    str(seed): abs(
                        next(item for item in subset if item["replicate_seed"] == seed and item["order_direction"] == "forward")["final_mean_loss"]
                        - next(item for item in subset if item["replicate_seed"] == seed and item["order_direction"] == "reverse")["final_mean_loss"]
                    )
                    for seed in REPLICATE_SEEDS
                },
            }
            by_split_arm[f"{split}:{arm}"]["max_order_delta"] = max(by_split_arm[f"{split}:{arm}"]["order_deltas"].values())
            by_split_arm[f"{split}:{arm}"]["all_hard_guards_pass"] = (
                all(
                    item["hard_guards"]["forgetting"]
                    and item["hard_guards"]["checkpoint_restore"]
                    and item["hard_guards"]["complete_stage_coverage"]
                    for item in subset
                )
                and by_split_arm[f"{split}:{arm}"]["max_order_delta"] <= MAX_ORDER_DELTA
            )
    tune = {arm: by_split_arm[f"tune:{arm}"] for arm in ARMS}
    locked_arm = min(ARMS, key=lambda arm: (tune[arm]["mean_final_loss"], ARMS.index(arm)))
    assessment = by_split_arm[f"assessment:{locked_arm}"]
    disposition = (
        "SyntheticCandidate"
        if assessment["all_hard_guards_pass"] and assessment["mean_primary_improvement"] > 0.0
        else "NoCandidate"
    )
    return {
        "by_split_arm": by_split_arm,
        "prediction_lock": {
            "selection_split": "tune",
            "locked_arm": locked_arm,
            "selection_metric": "mean_final_loss",
        },
        "disposition": disposition,
    }


def _validate_source(root: Path, observed: Mapping[str, Any]) -> None:
    manifest = observed.get("manifest")
    _require(isinstance(manifest, dict), "source manifest missing manifest object")
    _require(observed.get("manifest_sha256") == _digest(manifest), "source manifest digest mismatch")
    _require(manifest.get("state_slice") == STATE_SLICE, "source manifest state slice mismatch")
    _require(manifest.get("url") == UPSTREAM_URL, "source manifest URL mismatch")
    _require(manifest.get("commit") == UPSTREAM_COMMIT, "source manifest commit mismatch")
    source_root = Path(manifest.get("checkout", "")).resolve()
    _require(source_root == root.resolve(), "source manifest checkout path mismatch")
    _require(root.is_dir(), "source checkout does not exist")
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=False, capture_output=True, text=True)
    _require(head.returncode == 0 and head.stdout.strip() == UPSTREAM_COMMIT, "source checkout commit mismatch")
    status = subprocess.run(["git", "-C", str(root), "status", "--porcelain"], check=False, capture_output=True, text=True)
    _require(status.returncode == 0 and status.stdout == "", "source checkout is dirty")
    rows = manifest.get("required_files")
    _require(isinstance(rows, list), "source manifest file roster missing")
    _require(rows == sorted(rows, key=lambda item: REQUIRED_SOURCE_FILES.index(item["path"])), "source manifest file order mismatch")
    _require([item.get("path") for item in rows] == list(REQUIRED_SOURCE_FILES), "source manifest file roster mismatch")
    for row in rows:
        path = root / row["path"]
        _require(path.is_file() and not path.is_symlink(), f"source file missing or symlinked: {row['path']}")
        _require(row.get("byte_len") == path.stat().st_size, f"source byte length mismatch: {row['path']}")
        _require(row.get("sha256") == _sha256_file(path), f"source digest mismatch: {row['path']}")


def validate_artifact(root: Path) -> dict[str, Any]:
    root = root.resolve()
    contract_path = root / "contract.json"
    source_path = root / "source-manifest.json"
    result_path = root / "result.json"
    _require(contract_path.is_file(), "contract.json missing")
    _require(source_path.is_file(), "source-manifest.json missing")
    _require(result_path.is_file(), "result.json missing")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    source = json.loads(source_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    _require(contract.get("state_slice") == STATE_SLICE, "contract state slice mismatch")
    _require(contract.get("schema_version") == SCHEMA_VERSION, "contract schema mismatch")
    _require(contract.get("protocol") == PROTOCOL, "contract protocol mismatch")
    _require(contract.get("claim_ceiling") == CLAIM_CEILING, "contract claim ceiling mismatch")
    _require(contract.get("contract_sha256") == _digest({key: value for key, value in contract.items() if key != "contract_sha256"}), "contract digest mismatch")
    _validate_source(Path(source["manifest"]["checkout"]), source)
    _require(contract.get("source") == source, "contract/source manifest mismatch")
    _require(result.get("state_slice") == STATE_SLICE, "result state slice mismatch")
    _require(result.get("schema_version") == SCHEMA_VERSION, "result schema mismatch")
    _require(result.get("protocol") == PROTOCOL, "result protocol mismatch")
    _require(result.get("claim_ceiling") == CLAIM_CEILING, "result claim ceiling mismatch")
    _require(result.get("training_executed") is False, "synthetic result reports training")
    _require(result.get("model_loaded") is False, "synthetic result reports model load")
    _require(result.get("inference_executed") is False, "synthetic result reports inference")
    _require(result.get("network_access") is False, "synthetic result reports network access")
    _require(result.get("source", {}).get("commit") == UPSTREAM_COMMIT, "result source commit mismatch")
    trials = result.get("trials")
    expected_count = len(SPLITS) * len(ARMS) * len(REPLICATE_SEEDS) * len(ORDER_DIRECTIONS)
    _require(isinstance(trials, list) and len(trials) == expected_count, "result trial coverage mismatch")
    identities = set()
    for observed in trials:
        identity = (observed.get("arm"), observed.get("split"), observed.get("replicate_seed"), observed.get("order_seed"), observed.get("order_direction"))
        _require(identity not in identities, "result has duplicate trial identity")
        identities.add(identity)
        _require(_digest(observed) == _digest(_trial(*identity[:2], identity[2], identity[3], identity[4])), f"trial arithmetic mismatch: {identity}")
    _require(_digest(result.get("summary")) == _digest(_summary(trials)), "summary arithmetic mismatch")
    _require(result.get("result_sha256") == _digest({key: value for key, value in result.items() if key != "result_sha256"}), "result digest mismatch")
    return {"valid": True, "state_slice": STATE_SLICE, "claim_ceiling": CLAIM_CEILING, "disposition": result["summary"]["disposition"], "trial_count": len(trials)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate_artifact(args.artifact_root), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
