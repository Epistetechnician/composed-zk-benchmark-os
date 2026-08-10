#!/usr/bin/env python3
"""V25 privileged-telemetry information-presence probe on the 4B hybrid tier.

Decides the V22-V24 null fork: does the residual stream carry a
concept-independent linear signature of activation injection that the
model's own report does not express? Closed-form Fisher probe, sealed
assessment, preregistered fork margin against self-report.
Protocol: docs/research/astral-self-modeling/46-telemetry-information-presence-v25.md
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import mlx.core as mx
import numpy as np

HERE = Path(__file__).resolve()
V24_PATH = HERE.parents[1] / "astral-hybrid-instrument-v24" / "v24.py"
V22_PATH = HERE.parents[1] / "astral-activation-discrimination-v22" / "v22.py"
SITES = (10, 21, 32)
FIT_PROBE_GATE = 0.70
TUNE_PROBE_GATE = 0.65
ASSESS_PROBE_GATE = 0.75
SHUFFLED_LABEL_FLOOR = 0.55
TEXT_SANITY_FLOOR = 0.90
FORK_MARGIN = 0.15
BOOTSTRAP_SEED = 2501
BOOTSTRAP_DRAWS = 10_000
CONCEPTS = (
    "basil", "clove", "dune", "estuary", "flint", "gorse", "hollow", "ivy",
    "jasper", "kelp", "loam", "moss",
    "nectar", "onyx", "prism", "reed",
)
V22_FROZEN_CONCEPTS = (
    "cedar", "violin", "glacier", "lantern", "meadow", "copper", "harbor", "velvet",
    "canyon", "marble", "orchid", "compass",
    "willow", "tunnel", "saffron", "anchor",
)
V23_FROZEN_CONCEPTS = (
    "birch", "cello", "fjord", "beacon", "prairie", "bronze", "marina", "satin",
    "ravine", "granite", "lilac", "astrolabe",
    "poplar", "subway", "turmeric", "mooring",
)
V24_FROZEN_CONCEPTS = (
    "alcove", "bramble", "cinder", "driftwood", "ember", "fern", "gable", "heather",
    "inlet", "juniper", "kettle", "lagoon",
    "obsidian", "pebble", "quartz", "thicket",
)
CLAIM = "LocalDevelopmentPrivilegedTelemetryInformationPresence"

if set(CONCEPTS) & (set(V22_FROZEN_CONCEPTS) | set(V23_FROZEN_CONCEPTS) | set(V24_FROZEN_CONCEPTS)):
    raise RuntimeError("ConceptCollisionWithFrozenPhase")
if len(set(CONCEPTS)) != len(CONCEPTS):
    raise RuntimeError("ConceptDuplicateWithinV25")


def import_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


V24 = import_path("astral_v24_for_v25", V24_PATH)
V22 = import_path("astral_v22_core_for_v25", V22_PATH)
V22.SITES = SITES
V22.CONCEPTS = CONCEPTS
V22.CLAIM = CLAIM
V17 = V22.V17
HIDDEN_SIZE = V24.HIDDEN_SIZE
LAYER_COUNT = V24.EXPECTED_LAYER_COUNT


class TelemetryRunner(V24.NemotronRunner):
    """V24-certified seam extended with all-layer final-position capture.

    The forward path is operation-identical to the certified V24 loop; only
    the capture set widens from the three injection sites to every layer.
    Parity is re-validated on this runner before any protocol data.
    """

    def _forward(
        self, prompt: str, site: int | None = None,
        direction: np.ndarray | None = None, strength: float = 0.0,
        capture: bool = False,
    ) -> tuple[np.ndarray, dict[int, np.ndarray]]:
        ids = mx.array([self.tokenizer.encode(prompt, add_special_tokens=False)])
        hidden = self.model.backbone.embeddings(ids)
        attn_mask = V24.create_attention_mask(hidden, None)
        ssm_mask = V24.create_ssm_mask(hidden, None)
        captured: dict[int, np.ndarray] = {}
        for index, layer in enumerate(self.layers):
            mask = attn_mask if layer.block_type == "*" else ssm_mask
            hidden = layer(hidden, mask=mask, cache=None)
            if index == site and strength != 0.0:
                if direction is None or direction.shape != (HIDDEN_SIZE,):
                    raise ValueError(f"direction must have shape ({HIDDEN_SIZE},)")
                steered = hidden[:, -1:, :] + mx.array(direction)[None, None, :] * strength
                hidden = mx.concatenate([hidden[:, :-1, :], steered], axis=1)
            if capture:
                mx.eval(hidden)
                captured[index] = np.asarray(
                    hidden[0, -1, :].astype(mx.float16), dtype=np.float16
                )
        hidden = self.model.backbone.norm_f(hidden)
        logits = self.model.lm_head(hidden)
        mx.eval(logits)
        return np.asarray(logits[0, -1, :].astype(mx.float32), dtype=np.float32), captured


def write_manifest(root: Path) -> None:
    V17.write_json(root / "manifest.json", {
        "files": {
            str(path.relative_to(root)): V17.digest_file(path)
            for path in sorted(root.rglob("*"))
            if path.is_file() and path.name != "manifest.json"
        }
    })


def integrity(
    runner: TelemetryRunner, trials: list[Any],
    directions: dict[str, dict[int, np.ndarray]],
) -> dict[str, Any]:
    sample = trials[0].prompt
    ids = mx.array([runner.tokenizer.encode(sample, add_special_tokens=False)])
    native = np.asarray(runner.model(ids)[0, -1, :].astype(mx.float32), dtype=np.float32)
    controlled, _ = runner.forward_steered(sample)
    repeated, _ = runner.forward_steered(sample)
    zero, _ = runner.forward_steered(
        sample, site=SITES[0], direction=directions[CONCEPTS[0]][SITES[0]],
        strength=0.0,
    )
    return {
        "native_parity_max_abs_error": float(np.max(np.abs(native - controlled))),
        "repeat_max_abs_error": float(np.max(np.abs(controlled - repeated))),
        "zero_strength_max_abs_error": float(np.max(np.abs(controlled - zero))),
        "completion_token_ids": {token: runner.token_id(token) for token in V22.TOKENS},
        "activation_none_prompt_identity": all(
            next(row.prompt for row in trials if row.concept == concept and row.wrapper == wrapper and row.condition == "activation")
            == next(row.prompt for row in trials if row.concept == concept and row.wrapper == wrapper and row.condition == "none")
            for concept in CONCEPTS for wrapper in range(4)
        ),
    }


def instrument_metadata(runner: TelemetryRunner) -> dict[str, Any]:
    return {
        "model_type": V24.EXPECTED_MODEL_TYPE,
        "num_hidden_layers": LAYER_COUNT,
        "hidden_size": HIDDEN_SIZE,
        "hybrid_override_pattern": "".join(runner.pattern),
        "sites": list(SITES),
        "site_layer_types": {str(site): runner.pattern[site] for site in SITES},
        "seam": "manual-hybrid-loop-v1-reused-from-v24",
        "capture_mode": "all-layer-final-position",
        "capture_layer_count": LAYER_COUNT,
        "compute_dtype": "bfloat16",
        "capture_dtype_conversion": "bfloat16-to-float16-in-mlx",
        "logit_dtype_conversion": "bfloat16-to-float32-in-mlx",
    }


def collect_cell(
    runner: TelemetryRunner, trials: list[Any],
    directions: dict[str, dict[int, np.ndarray]], split: str,
    site: int, strength: float,
) -> tuple[list[dict[str, Any]], list[dict[int, np.ndarray]]]:
    rows, captures = [], []
    for trial in trials:
        if trial.split != split:
            continue
        active = trial.condition == "activation"
        logits, captured = runner.forward_steered(
            trial.prompt, site=site if active else None,
            direction=directions[trial.concept][site] if active else None,
            strength=strength if active else 0.0,
            capture=True,
        )
        rows.append({**asdict(trial), **V22.prediction(runner, logits)})
        captures.append(captured)
    return rows, captures


def _stack_condition(captures: list[dict[int, np.ndarray]], rows: list[dict[str, Any]], condition: str, layer: int) -> np.ndarray:
    return np.stack([
        np.asarray(capture[layer], dtype=np.float32)
        for capture, row in zip(captures, rows) if row["condition"] == condition
    ])


def fisher_probe(
    captures: list[dict[int, np.ndarray]], rows: list[dict[str, Any]],
    layer: int, positive: str = "activation", negative: str = "none",
) -> dict[str, Any] | None:
    """Closed-form Fisher direction on one layer; deterministic, no fitting."""
    pos = _stack_condition(captures, rows, positive, layer)
    neg = _stack_condition(captures, rows, negative, layer)
    direction = pos.mean(axis=0) - neg.mean(axis=0)
    norm = float(np.linalg.norm(direction))
    if not np.isfinite(norm) or norm == 0:
        return None
    proj_pos = pos @ direction
    proj_neg = neg @ direction
    threshold = float((proj_pos.mean() + proj_neg.mean()) / 2)
    separation = float(
        (proj_pos.mean() - proj_neg.mean())
        / np.sqrt((proj_pos.var() + proj_neg.var()) / 2 + 1e-12)
    )
    accuracy = float(
        (np.concatenate([proj_pos > threshold, proj_neg <= threshold]).mean())
    )
    return {
        "direction": direction, "threshold": threshold,
        "separation": separation, "accuracy": accuracy,
        "positive_mean_projection": float(proj_pos.mean()),
        "negative_mean_projection": float(proj_neg.mean()),
    }


def apply_probe(
    probe: dict[str, Any], captures: list[dict[int, np.ndarray]],
    rows: list[dict[str, Any]], layer: int,
    positive: str = "activation", negative: str = "none",
) -> float:
    pos = _stack_condition(captures, rows, positive, layer)
    neg = _stack_condition(captures, rows, negative, layer)
    proj_pos = pos @ probe["direction"]
    proj_neg = neg @ probe["direction"]
    return float(np.concatenate([proj_pos > probe["threshold"], proj_neg <= probe["threshold"]]).mean())


def concept_cross_validated_accuracy(
    captures: list[dict[int, np.ndarray]], rows: list[dict[str, Any]], layer: int,
    positive: str = "activation", negative: str = "none",
) -> float:
    """Two-fold concept-level cross-validation on the eight fit concepts.

    High-dimensional small-n Fisher probes are in-sample inflated, so all
    fit-split metrics use probes trained on four fit concepts and applied to
    the other four, in both directions. Deterministic grouping, no rng.
    """
    fit_concepts = list(CONCEPTS[:8])
    groups = (set(fit_concepts[:4]), set(fit_concepts[4:]))
    accuracies = []
    for train_group in groups:
        test_group = groups[1] if train_group is groups[0] else groups[0]
        train_rows, train_caps, test_rows, test_caps = [], [], [], []
        for capture, row in zip(captures, rows):
            if row["condition"] not in (positive, negative):
                continue
            if row["concept"] in train_group:
                train_rows.append(row)
                train_caps.append(capture)
            elif row["concept"] in test_group:
                test_rows.append(row)
                test_caps.append(capture)
        probe = fisher_probe(train_caps, train_rows, layer, positive, negative)
        if probe is None:
            return 0.5
        accuracies.append(apply_probe(probe, test_caps, test_rows, layer, positive, negative))
    return float(np.mean(accuracies))


def shuffled_label_accuracy(
    captures: list[dict[int, np.ndarray]], rows: list[dict[str, Any]], layer: int,
) -> float:
    indices = [index for index, row in enumerate(rows) if row["condition"] in ("activation", "none")]
    permuted = np.random.default_rng(BOOTSTRAP_SEED).permutation(len(indices))
    shuffled_pairs = []
    for target, source in zip(indices, permuted):
        row = dict(rows[target])
        row["condition"] = rows[indices[source]]["condition"]
        shuffled_pairs.append((captures[target], row))
    shuffled_captures = [capture for capture, _ in shuffled_pairs]
    shuffled_rows = [row for _, row in shuffled_pairs]
    return concept_cross_validated_accuracy(shuffled_captures, shuffled_rows, layer)


def cell_analysis(
    captures: list[dict[int, np.ndarray]], rows: list[dict[str, Any]],
) -> dict[str, Any]:
    layer_accuracies: dict[int, float] = {}
    text_layer_accuracies: dict[int, float] = {}
    for layer in range(LAYER_COUNT):
        layer_accuracies[layer] = concept_cross_validated_accuracy(captures, rows, layer)
        text_layer_accuracies[layer] = concept_cross_validated_accuracy(
            captures, rows, layer, positive="text", negative="none"
        )
    best_layer = max(range(LAYER_COUNT), key=lambda layer: (layer_accuracies[layer], -layer))
    return {
        "best_layer": best_layer,
        "layer_accuracies": [layer_accuracies[layer] for layer in range(LAYER_COUNT)],
        "fit_probe_accuracy": layer_accuracies[best_layer],
        "shuffled_label_accuracy": shuffled_label_accuracy(captures, rows, best_layer),
        "text_vs_none_accuracy": max(text_layer_accuracies.values()),
        "text_vs_none_best_layer": max(range(LAYER_COUNT), key=lambda layer: (text_layer_accuracies[layer], -layer)),
    }


def behavioral_effect(rows: list[dict[str, Any]], site: int, strength: float) -> dict[str, Any]:
    pairs: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    for row in rows:
        if row["condition"] in ("activation", "none"):
            pairs.setdefault((row["concept"], row["wrapper"]), {})[row["condition"]] = row
    shifts: list[float] = []
    top1_changes = 0
    for (_, _), pair in sorted(pairs.items()):
        activation_logits = np.asarray(pair["activation"]["logits"], dtype=np.float64)
        none_logits = np.asarray(pair["none"]["logits"], dtype=np.float64)
        shifts.append(float(np.max(np.abs(activation_logits - none_logits))))
        if int(np.argmax(activation_logits)) != int(np.argmax(none_logits)):
            top1_changes += 1
    pair_count = len(shifts)
    max_shift = float(np.max(shifts))
    return {
        "site": site,
        "strength": strength,
        "pair_count": pair_count,
        "mean_abs_logit_shift": float(np.mean(shifts)),
        "max_abs_logit_shift": max_shift,
        "top1_token_change_rate": top1_changes / pair_count,
        "silent": bool(max_shift < V24.BEHAVIORAL_SILENCE_LOGIT_SHIFT and top1_changes == 0),
    }


def bootstrap_binary(rows: list[dict[str, Any]]) -> dict[str, float]:
    by_concept = {
        concept: float(np.mean([row["probe_correct"] for row in rows if row["concept"] == concept]))
        for concept in CONCEPTS[12:]
    }
    values = np.asarray(list(by_concept.values()))
    rng, draws = np.random.default_rng(BOOTSTRAP_SEED), np.empty(BOOTSTRAP_DRAWS)
    for index in range(len(draws)):
        draws[index] = float(np.mean(values[rng.integers(0, len(values), len(values))]) - 0.5)
    return {"mean_over_chance": float(np.mean(draws)), "lower_95": float(np.quantile(draws, 0.025)), "upper_95": float(np.quantile(draws, 0.975))}


def prepare(root: Path) -> None:
    if root.exists():
        raise RuntimeError("output root already exists")
    root.mkdir(parents=True)
    runner, trials = TelemetryRunner(), V22.build_trials()
    V17.write_json(root / "corpus.json", [asdict(row) for row in trials])
    V17.write_json(root / "model-inventory.json", V17.model_inventory(V24.MODEL_PATH))
    V17.write_json(root / "instrument.json", instrument_metadata(runner))
    directions, direction_state = V22.build_directions(runner)
    np.savez_compressed(
        root / "directions.npz",
        **{f"{concept}__{site}": vector for concept, values in directions.items() for site, vector in values.items()},
    )
    V17.write_json(root / "direction-state.json", direction_state)
    checks = integrity(runner, trials, directions)
    V17.write_json(root / "integrity.json", checks)
    sweep, behavioral = [], []
    for site in SITES:
        for strength in V22.STRENGTHS:
            rows, captures = collect_cell(runner, trials, directions, "fit", site, strength)
            analysis = cell_analysis(captures, rows)
            sweep.append({
                "site": site, "strength": strength,
                "best_layer": analysis["best_layer"],
                "fit_probe_accuracy": analysis["fit_probe_accuracy"],
                "shuffled_label_accuracy": analysis["shuffled_label_accuracy"],
                "text_vs_none_accuracy": analysis["text_vs_none_accuracy"],
                "text_vs_none_best_layer": analysis["text_vs_none_best_layer"],
                "layer_accuracies": analysis["layer_accuracies"],
            })
            behavioral.append(behavioral_effect(rows, site, strength))
    selected = sorted(
        sweep,
        key=lambda row: (-row["fit_probe_accuracy"], row["strength"], row["site"]),
    )[0]
    selected_behavioral = next(
        cell for cell in behavioral
        if cell["site"] == selected["site"] and cell["strength"] == selected["strength"]
    )
    V17.write_json(root / "probe-fit.json", sweep)
    V17.write_json(root / "behavioral-effect.json", behavioral)
    V17.write_json(root / "selected-configuration.json", {
        "site": selected["site"], "strength": selected["strength"],
        "layer": selected["best_layer"],
    })
    if selected_behavioral["silent"]:
        V17.write_json(root / "result.json", {
            "classification": "ProbeTargetBehaviorallySilent",
            "confirmation": "NotAuthorized", "stage_0c": "Blocked",
            "stage_1": "BlockedByStage0C", "claim_ceiling": CLAIM,
            "assessment_unopened": True,
            "selected_configuration": {"site": selected["site"], "strength": selected["strength"], "layer": selected["best_layer"]},
            "selected_behavioral_effect": selected_behavioral,
        })
        write_manifest(root)
        return
    floor_violations = []
    if selected["shuffled_label_accuracy"] > SHUFFLED_LABEL_FLOOR:
        floor_violations.append("shuffled_label_above_floor")
    if selected["text_vs_none_accuracy"] < TEXT_SANITY_FLOOR:
        floor_violations.append("text_sanity_below_floor")
    if floor_violations:
        V17.write_json(root / "result.json", {
            "classification": "ProbeControlFloorViolation",
            "confirmation": "NotAuthorized", "stage_0c": "Blocked",
            "stage_1": "BlockedByStage0C", "claim_ceiling": CLAIM,
            "assessment_unopened": True,
            "violations": floor_violations,
            "selected_configuration": {"site": selected["site"], "strength": selected["strength"], "layer": selected["best_layer"]},
            "shuffled_label_accuracy": selected["shuffled_label_accuracy"],
            "text_vs_none_accuracy": selected["text_vs_none_accuracy"],
        })
        write_manifest(root)
        return
    tune_rows, tune_captures = collect_cell(runner, trials, directions, "tune", selected["site"], selected["strength"])
    fit_rows, fit_captures = collect_cell(runner, trials, directions, "fit", selected["site"], selected["strength"])
    fit_probe = fisher_probe(fit_captures, fit_rows, selected["best_layer"])
    tune_accuracy = apply_probe(fit_probe, tune_captures, tune_rows, selected["best_layer"])
    tune_result = {
        "fit_probe_accuracy": fit_probe["accuracy"],
        "tune_probe_accuracy": tune_accuracy,
        "probe_threshold": fit_probe["threshold"],
        "probe_direction_norm": float(np.linalg.norm(fit_probe["direction"])),
        "fit_separation": fit_probe["separation"],
    }
    V17.write_json(root / "tune-results.json", tune_result)
    qualified = (
        checks["native_parity_max_abs_error"] == 0
        and checks["repeat_max_abs_error"] == 0
        and checks["zero_strength_max_abs_error"] == 0
        and checks["activation_none_prompt_identity"]
        and fit_probe["accuracy"] >= FIT_PROBE_GATE
        and tune_accuracy >= TUNE_PROBE_GATE
    )
    qualification = {"qualified": qualified, **tune_result, **checks}
    V17.write_json(root / "qualification.json", qualification)
    if not qualified:
        V17.write_json(root / "result.json", {
            "classification": "NotRunInformationPresenceProbe",
            "confirmation": "NotAuthorized", "stage_0c": "Blocked",
            "stage_1": "BlockedByStage0C", "claim_ceiling": CLAIM,
            "assessment_unopened": True,
        })
        write_manifest(root)
        return
    inputs = (
        "corpus.json", "model-inventory.json", "instrument.json", "directions.npz",
        "direction-state.json", "integrity.json", "behavioral-effect.json",
        "probe-fit.json", "selected-configuration.json", "tune-results.json",
        "qualification.json",
    )
    V17.write_json(root / "configuration-lock.json", {
        "assessment_results_absent": not (root / "assessment-results.json").exists(),
        "inputs": {name: V17.digest_file(root / name) for name in inputs},
        "source_identity": {
            "v25_sha256": V17.digest_file(HERE),
            "validator_sha256": V17.digest_file(HERE.with_name("validator_v25.py")),
            "v24_tool_sha256": V17.digest_file(V24_PATH),
            "v22_shared_core_sha256": V17.digest_file(V22_PATH),
            "v17_shared_core_sha256": V17.digest_file(V22.V17_PATH),
        },
    })


def load_directions(root: Path) -> dict[str, dict[int, np.ndarray]]:
    archive = np.load(root / "directions.npz")
    return {concept: {site: archive[f"{concept}__{site}"] for site in SITES} for concept in CONCEPTS}


def assess(root: Path) -> None:
    lock_path = root / "configuration-lock.json"
    if not lock_path.exists() or (root / "assessment-results.json").exists():
        raise RuntimeError("invalid assessment ordering")
    config = json.loads((root / "selected-configuration.json").read_text())
    runner, trials = TelemetryRunner(), V22.build_trials()
    directions = load_directions(root)
    fit_rows, fit_captures = collect_cell(runner, trials, directions, "fit", config["site"], config["strength"])
    fit_probe = fisher_probe(fit_captures, fit_rows, config["layer"])
    assessment_rows, assessment_captures = collect_cell(runner, trials, directions, "assessment", config["site"], config["strength"])
    assessment_accuracy = apply_probe(fit_probe, assessment_captures, assessment_rows, config["layer"])
    probe_direction = fit_probe["direction"]
    threshold = fit_probe["threshold"]
    probe_correct = []
    for capture, row in zip(assessment_captures, assessment_rows):
        if row["condition"] not in ("activation", "none"):
            continue
        projection = float(np.asarray(capture[config["layer"]], dtype=np.float32) @ probe_direction)
        predicted_activation = projection > threshold
        probe_correct.append(predicted_activation == (row["condition"] == "activation"))
    scored_rows = [
        {**row, "probe_correct": correct}
        for row, correct in zip(
            (row for row in assessment_rows if row["condition"] in ("activation", "none")),
            probe_correct,
        )
    ]
    interval = bootstrap_binary(scored_rows)
    self_report_metrics = V22.metrics(assessment_rows)
    self_report_accuracy = self_report_metrics["activation_vs_none_accuracy"]
    probe_pass = assessment_accuracy >= ASSESS_PROBE_GATE and interval["lower_95"] > 0
    if probe_pass:
        classification = (
            "InformationPresenceReportGapObserved"
            if assessment_accuracy - self_report_accuracy >= FORK_MARGIN
            else "InformationPresenceParityObserved"
        )
    else:
        classification = "InformationPresenceNoCandidate"
    V17.write_json(root / "assessment-results.json", {
        "probe_accuracy": assessment_accuracy,
        "probe_correct": probe_correct,
        "self_report_accuracy": self_report_accuracy,
        "self_report_metrics": self_report_metrics,
        "bootstrap": interval,
        "probe_threshold": threshold,
        "probe_direction_norm": float(np.linalg.norm(probe_direction)),
    })
    V17.write_json(root / "result.json", {
        "classification": classification,
        "confirmation": "NotAuthorized", "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C", "claim_ceiling": CLAIM,
        "probe_accuracy": assessment_accuracy,
        "self_report_accuracy": self_report_accuracy,
        "fork_margin_observed": assessment_accuracy - self_report_accuracy,
        "bootstrap": interval,
        "configuration_lock_sha256": V17.digest_file(lock_path),
    })
    write_manifest(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "assess"))
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    try:
        (prepare if args.phase == "prepare" else assess)(args.root.resolve())
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"status": "completed", "phase": args.phase, "root": str(args.root.resolve())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
