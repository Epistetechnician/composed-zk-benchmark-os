#!/usr/bin/env python3
"""Deterministic Astral V25 synthetic continual-correction simulation."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import random
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


HERE = Path(__file__).resolve().parent
CONTRACT_PATH = HERE / "experiment-contract.json"
MANIFEST = "MANIFEST.sha256"
SOURCE_NAMES = ("Dockerfile", "experiment-contract.json", "v25.py")
PRIMARY = "telemetry"


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def write_json(path: Path, value: object) -> None:
    path.write_bytes(json.dumps(value, indent=2, sort_keys=True).encode() + b"\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("wb") as handle:
        for row in rows:
            handle.write(canonical_bytes(row))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def stable_rng(*parts: object) -> random.Random:
    material = canonical_bytes([str(part) for part in parts])
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def add(left: list[float], right: list[float]) -> list[float]:
    return [a + b for a, b in zip(left, right, strict=True)]


def scale(value: list[float], factor: float) -> list[float]:
    return [item * factor for item in value]


def sigmoid(value: float) -> float:
    if value >= 0:
        inverse = math.exp(-min(value, 60.0))
        return 1.0 / (1.0 + inverse)
    forward = math.exp(max(value, -60.0))
    return forward / (1.0 + forward)


def vector_norm(value: list[float]) -> float:
    return math.sqrt(dot(value, value))


def norm_match(value: list[float], target: list[float]) -> list[float]:
    denominator = vector_norm(value)
    if denominator == 0:
        raise ValueError("cannot normalize zero vector")
    return scale(value, vector_norm(target) / denominator)


def task_delta(seed: int, task: int, dimension: int) -> list[float]:
    rng = stable_rng("target", seed, task)
    return [0.0] + [rng.choice((-1.0, 1.0)) * rng.uniform(0.9, 1.4) for _ in range(dimension - 1)]


def example_rows(
    seed: int,
    task: int,
    split: str,
    count: int,
    base: list[float],
    delta: list[float],
) -> list[dict[str, Any]]:
    rng = stable_rng("examples", seed, task, split)
    target = add(base, delta)
    rows = []
    for index in range(count):
        features = [rng.gauss(0.0, 1.0) for _ in base]
        label = int(dot(target, features) >= 0.0)
        rows.append(
            {
                "features": [round(value, 12) for value in features],
                "index": index,
                "label": label,
                "seed": seed,
                "split": split,
                "task": task,
            }
        )
    return rows


def telemetry_signal(
    world: str,
    condition: str,
    seed: int,
    task: int,
    slot: int,
    deltas: list[list[float]],
    noise: float,
) -> list[float]:
    target = deltas[task]
    signal_task = task
    multiplier = 1.0
    if condition == "shuffled_telemetry":
        signal_task = (task + 1) % len(deltas)
        target = deltas[signal_task]
    elif condition == "incorrect_telemetry":
        multiplier = -1.0
    if world == "positive_control" and condition != "random_direction":
        rng = stable_rng("telemetry-noise", world, condition, seed, signal_task, slot)
        value = [multiplier * component + rng.gauss(0.0, noise) for component in target]
        value[0] = 0.0
        return value
    rng = stable_rng("independent-telemetry", world, condition, seed, task, slot)
    random_value = [0.0] + [rng.gauss(0.0, 1.0) for _ in target[1:]]
    value = norm_match(random_value, target)
    return scale(value, multiplier)


def update_condition(
    condition: str,
    world: str,
    seed: int,
    task: int,
    adaptation: list[dict[str, Any]],
    deltas: list[list[float]],
    contract: dict[str, Any],
) -> tuple[list[float], float, list[list[float]]]:
    dimension = contract["actor_dimension"]
    base = [float(value) for value in contract["base_weights"]]
    learning_rate = float(contract["learning_rate"])
    adapter = [0.0] * dimension
    bias = 0.0
    signals: list[list[float]] = []
    if condition == "frozen":
        return adapter, bias, signals
    if condition == "reflection":
        residuals = []
        for row in adaptation:
            probability = sigmoid(dot(base, row["features"]))
            residuals.append(row["label"] - probability)
        bias = sum(residuals) / len(residuals)
        return adapter, bias, signals
    if condition == "critic":
        for row in adaptation:
            probability = sigmoid(dot(base, row["features"]) + bias)
            bias += learning_rate * (row["label"] - probability)
        return adapter, bias, signals
    if condition == "ordinary_update":
        for row in adaptation:
            probability = sigmoid(dot(add(base, adapter), row["features"]))
            error = row["label"] - probability
            adapter = add(adapter, scale(row["features"], learning_rate * error))
        return adapter, bias, signals
    if condition not in {
        "telemetry",
        "shuffled_telemetry",
        "incorrect_telemetry",
        "random_direction",
    }:
        raise ValueError(f"unknown condition: {condition}")
    for slot in range(contract["update_slots"]):
        signals.append(
            telemetry_signal(
                world,
                condition,
                seed,
                task,
                slot,
                deltas,
                float(contract["telemetry_noise"]),
            )
        )
    adapter = [sum(signal[index] for signal in signals) / len(signals) for index in range(dimension)]
    return adapter, bias, signals


def probability(
    base: list[float], adapter: list[float], bias: float, features: list[float]
) -> float:
    return sigmoid(dot(add(base, adapter), features) + bias)


def accuracy(rows: list[dict[str, Any]]) -> float:
    return sum(row["prediction"] == row["label"] for row in rows) / len(rows)


def brier(rows: list[dict[str, Any]]) -> float:
    return sum((row["probability"] - row["label"]) ** 2 for row in rows) / len(rows)


def percentile(sorted_values: list[float], fraction: float) -> float:
    position = (len(sorted_values) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def bootstrap_interval(differences: list[float], draws: int, world: str) -> dict[str, float]:
    rng = stable_rng("bootstrap", world, draws, len(differences))
    values = []
    for _ in range(draws):
        values.append(sum(rng.choice(differences) for _ in differences) / len(differences))
    values.sort()
    return {
        "lower_95": percentile(values, 0.025),
        "mean": sum(values) / len(values),
        "upper_95": percentile(values, 0.975),
    }


def aggregate_world(
    world: str,
    observations: list[dict[str, Any]],
    replay: list[dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, Any]:
    selected = [row for row in observations if row["world"] == world]
    condition_metrics = {}
    cells: dict[str, dict[tuple[int, int], list[dict[str, Any]]]] = {}
    for condition in contract["conditions"]:
        rows = [row for row in selected if row["condition"] == condition]
        condition_metrics[condition] = {"accuracy": accuracy(rows), "brier": brier(rows)}
        grouped: dict[tuple[int, int], list[dict[str, Any]]] = {}
        for row in rows:
            grouped.setdefault((row["seed"], row["task"]), []).append(row)
        cells[condition] = grouped
    controls = [condition for condition in contract["conditions"] if condition != PRIMARY]
    strongest = min(
        controls,
        key=lambda condition: (-condition_metrics[condition]["accuracy"], condition),
    )
    differences = [
        accuracy(cells[PRIMARY][cell]) - accuracy(cells[strongest][cell])
        for cell in sorted(cells[PRIMARY])
    ]
    interval = bootstrap_interval(differences, contract["bootstrap_draws"], world)
    replay_rows = [
        row for row in replay if row["world"] == world and row["condition"] == PRIMARY
    ]
    maximum_retention_drop = max(
        (row["before_accuracy"] - row["after_accuracy"] for row in replay_rows),
        default=0.0,
    )
    gates = contract["gates"]
    checks = {
        "brier_guard": condition_metrics[PRIMARY]["brier"]
        <= condition_metrics[strongest]["brier"] + gates["maximum_brier_degradation"],
        "future_accuracy": condition_metrics[PRIMARY]["accuracy"]
        >= gates["minimum_future_accuracy"],
        "primary_advantage": sum(differences) / len(differences)
        >= gates["minimum_primary_advantage"],
        "retention": maximum_retention_drop <= gates["maximum_retention_drop"],
        "uncertainty": interval["lower_95"] > gates["minimum_bootstrap_lower_95"],
    }
    return {
        "bootstrap": interval,
        "condition_metrics": condition_metrics,
        "gates": {**checks, "passed": all(checks.values())},
        "maximum_retention_drop": maximum_retention_drop,
        "mean_primary_advantage": sum(differences) / len(differences),
        "paired_cell_count": len(differences),
        "strongest_control": strongest,
        "world": world,
    }


def summarize(
    observations: list[dict[str, Any]],
    replay: list[dict[str, Any]],
    contract: dict[str, Any],
) -> dict[str, Any]:
    worlds = {
        world: aggregate_world(world, observations, replay, contract)
        for world in contract["worlds"]
    }
    positive = worlds["positive_control"]
    null = worlds["null_control"]
    null_specificity = (
        not null["gates"]["passed"]
        and null["mean_primary_advantage"] <= contract["gates"]["maximum_null_advantage"]
    )
    qualified = positive["gates"]["passed"] and null_specificity
    return {
        "classification": (
            contract["claim_ceiling"]
            if qualified
            else "SyntheticDockerContinualCorrectionHarnessNoCandidate"
        ),
        "claim_ceiling": contract["claim_ceiling"],
        "external_states": {
            "confirmation": "NotAuthorized",
            "independently_verified": "NotRun",
            "model_backed_continual_learning": "NotRun",
            "stage_0c": "Blocked",
            "stage_1": "BlockedByStage0C",
            "thesis": "NotValidated",
        },
        "null_specificity_passed": null_specificity,
        "qualified": qualified,
        "worlds": worlds,
    }


def simulate(contract: dict[str, Any]) -> dict[str, Any]:
    base = [float(value) for value in contract["base_weights"]]
    adaptation_rows: list[dict[str, Any]] = []
    update_rows: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    replay_rows: list[dict[str, Any]] = []
    for seed in contract["seeds"]:
        deltas = [task_delta(seed, task, contract["actor_dimension"]) for task in range(contract["tasks_per_seed"])]
        task_data = {}
        for task, delta in enumerate(deltas):
            task_data[task] = {
                "adaptation": example_rows(seed, task, "adaptation", contract["adaptation_examples"], base, delta),
                "future": example_rows(seed, task, "future", contract["future_examples"], base, delta),
                "replay": example_rows(seed, task, "replay", contract["replay_examples"], base, delta),
            }
            for row in task_data[task]["adaptation"]:
                adaptation_rows.append({**row, "target_delta": deltas[task]})
        for world in contract["worlds"]:
            policies: dict[str, dict[int, tuple[list[float], float]]] = {
                condition: {} for condition in contract["conditions"]
            }
            for task in range(contract["tasks_per_seed"]):
                before = {condition: dict(values) for condition, values in policies.items()}
                for condition in contract["conditions"]:
                    adapter, bias, signals = update_condition(
                        condition,
                        world,
                        seed,
                        task,
                        task_data[task]["adaptation"],
                        deltas,
                        contract,
                    )
                    policies[condition][task] = (adapter, bias)
                    update_rows.append(
                        {
                            "adapter": [round(value, 12) for value in adapter],
                            "bias": round(bias, 12),
                            "condition": condition,
                            "seed": seed,
                            "signals": [[round(value, 12) for value in signal] for signal in signals],
                            "task": task,
                            "update_slots_consumed": contract["update_slots"] if condition != "frozen" else 0,
                            "world": world,
                        }
                    )
                    for row in task_data[task]["future"]:
                        observed = probability(base, adapter, bias, row["features"])
                        observations.append(
                            {
                                "condition": condition,
                                "index": row["index"],
                                "label": row["label"],
                                "prediction": int(observed >= 0.5),
                                "probability": round(observed, 12),
                                "seed": seed,
                                "task": task,
                                "world": world,
                            }
                        )
                for prior_task in range(task):
                    replay_examples = task_data[prior_task]["replay"]
                    for condition in contract["conditions"]:
                        before_adapter, before_bias = before[condition][prior_task]
                        after_adapter, after_bias = policies[condition][prior_task]
                        before_predictions = [
                            int(probability(base, before_adapter, before_bias, row["features"]) >= 0.5)
                            for row in replay_examples
                        ]
                        after_predictions = [
                            int(probability(base, after_adapter, after_bias, row["features"]) >= 0.5)
                            for row in replay_examples
                        ]
                        replay_rows.append(
                            {
                                "after_accuracy": sum(prediction == row["label"] for prediction, row in zip(after_predictions, replay_examples, strict=True)) / len(replay_examples),
                                "before_accuracy": sum(prediction == row["label"] for prediction, row in zip(before_predictions, replay_examples, strict=True)) / len(replay_examples),
                                "condition": condition,
                                "current_task": task,
                                "prior_task": prior_task,
                                "seed": seed,
                                "world": world,
                            }
                        )
    return {
        "adaptation": adaptation_rows,
        "observations": observations,
        "replay": replay_rows,
        "result": summarize(observations, replay_rows, contract),
        "updates": update_rows,
    }


def source_inventory() -> dict[str, str]:
    source_root = HERE / "source"
    if source_root.is_dir():
        return {name: sha256(source_root / name) for name in SOURCE_NAMES}
    return {name: sha256(HERE / name) for name in SOURCE_NAMES}


def runtime_identity() -> dict[str, Any]:
    return {
        "base_image_digest": os.environ.get("ASTRAL_V25_BASE_IMAGE_DIGEST", "host-run"),
        "container_image_id": os.environ.get("ASTRAL_V25_IMAGE_ID", "host-run"),
        "implementation": platform.python_implementation(),
        "machine": platform.machine(),
        "platform": platform.platform(),
        "python": sys.version,
        "python_executable": Path(sys.executable).name,
    }


def safe_relative(value: str) -> bool:
    path = PurePosixPath(value)
    return value == path.as_posix() and value not in ("", ".") and not path.is_absolute() and ".." not in path.parts


def write_manifest(root: Path) -> str:
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("symlinks are forbidden in V25 artifacts")
        if path.is_file() and path.name != MANIFEST:
            relative = path.relative_to(root).as_posix()
            if not safe_relative(relative):
                raise ValueError("unsafe artifact path")
            rows.append(f"{sha256(path)}  {relative}")
    (root / MANIFEST).write_text("\n".join(rows) + "\n")
    return sha256(root / MANIFEST)


def execute(root: Path) -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text())
    if root.exists():
        raise ValueError("output root already exists")
    if root.name != "astral-v25-building":
        raise ValueError("output root must end in astral-v25-building")
    root.mkdir(parents=True)
    first = simulate(contract)
    second = simulate(contract)
    first_digest = hashlib.sha256(canonical_bytes(first["result"])).hexdigest()
    second_digest = hashlib.sha256(canonical_bytes(second["result"])).hexdigest()
    if first_digest != second_digest or first != second:
        raise RuntimeError("deterministic replay mismatch")
    write_json(root / "experiment-contract.json", contract)
    write_json(root / "runtime.json", runtime_identity())
    write_json(root / "source-inventory.json", source_inventory())
    write_jsonl(root / "adaptation.jsonl", first["adaptation"])
    write_jsonl(root / "updates.jsonl", first["updates"])
    write_jsonl(root / "observations.jsonl", first["observations"])
    write_jsonl(root / "replay-checks.jsonl", first["replay"])
    write_json(root / "result.json", first["result"])
    write_json(
        root / "determinism.json",
        {
            "byte_equivalent_structures": True,
            "first_result_sha256": first_digest,
            "second_result_sha256": second_digest,
        },
    )
    identity = write_manifest(root)
    destination = root.with_name(f"astral-v25-{identity}")
    if destination.exists():
        raise ValueError("content-addressed destination already exists")
    root.rename(destination)
    return {
        "artifact": str(destination),
        "classification": first["result"]["classification"],
        "manifest_sha256": identity,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run",))
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = execute(args.root.resolve())
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"status": "completed", **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
