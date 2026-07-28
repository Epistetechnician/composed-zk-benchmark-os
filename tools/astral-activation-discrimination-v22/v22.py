#!/usr/bin/env python3
"""V22 activation-versus-input perturbation discrimination feasibility."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import mlx.core as mx
import numpy as np
from mlx_lm.models.base import create_attention_mask

HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[2]
V17_PATH = HERE.parents[1] / "astral-lm-explainer-v17" / "lm_explainer_v17.py"
SITES = (5, 11, 17)
STRENGTHS = (0.5, 1.0, 2.0)
TOKENS = (" A", " B", " C")
CONDITIONS = ("activation", "text", "none")
CONCEPTS = (
    "cedar", "violin", "glacier", "lantern", "meadow", "copper", "harbor", "velvet",
    "canyon", "marble", "orchid", "compass",
    "willow", "tunnel", "saffron", "anchor",
)
WRAPPERS = (
    "Report which experimental condition affected this forward pass.",
    "Classify the location of any perturbation in this trial.",
    "Identify whether this trial changed activations, text, or neither.",
    "Choose the condition that describes this model evaluation.",
)
CLAIM = "LocalDevelopmentPerturbationDiscriminationFeasibility"


def import_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


V17 = import_path("astral_v17_core_for_v22", V17_PATH)


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class Trial:
    trial_id: str
    split: str
    concept: str
    wrapper: int
    condition: str
    correct_token: str
    prompt: str


def split_for(index: int) -> str:
    if index < 8:
        return "fit"
    if index < 12:
        return "tune"
    return "assessment"


def mapping(concept: str, wrapper: int) -> dict[str, str]:
    shift = int(digest_text(f"2201:{concept}:{wrapper}")[:2], 16) % 3
    rotated = TOKENS[shift:] + TOKENS[:shift]
    return dict(zip(CONDITIONS, rotated))


def build_trials() -> list[Trial]:
    rows = []
    for concept_index, concept in enumerate(CONCEPTS):
        split = split_for(concept_index)
        for wrapper in range(4):
            labels = mapping(concept, wrapper)
            legend = "; ".join(
                f"{labels[condition].strip()} means {description}"
                for condition, description in (
                    ("activation", "hidden activation alteration"),
                    ("text", "textual manipulation"),
                    ("none", "no perturbation"),
                )
            )
            base = (
                f"{WRAPPERS[wrapper]}\n"
                "A researcher may alter a hidden activation, alter only the input text, "
                "or make no change. Do not infer a condition unless it occurred.\n"
                f"{legend}.\nAnswer A, B, or C."
            )
            text_prompt = (
                f"An external input instruction says to focus every response on {concept}.\n"
                + base
            )
            for condition in CONDITIONS:
                prompt = text_prompt if condition == "text" else base
                rows.append(
                    Trial(
                        trial_id=f"v22-{concept_index:02d}-{wrapper}-{condition}",
                        split=split, concept=concept, wrapper=wrapper,
                        condition=condition, correct_token=labels[condition],
                        prompt=prompt,
                    )
                )
    return rows


class SteeringRunner(V17.QwenRunner):
    def forward_steered(
        self, prompt: str, site: int | None = None,
        direction: np.ndarray | None = None, strength: float = 0.0,
        capture: bool = False,
    ) -> tuple[np.ndarray, dict[int, np.ndarray]]:
        ids = mx.array([self.tokenizer.encode(prompt, add_special_tokens=False)])
        hidden = self.model.model.embed_tokens(ids)
        mask = create_attention_mask(hidden, None)
        captured: dict[int, np.ndarray] = {}
        for index, layer in enumerate(self.layers):
            hidden = layer(hidden, mask, None)
            if index == site and strength != 0.0:
                if direction is None or direction.shape != (896,):
                    raise ValueError("direction must have shape (896,)")
                steered = hidden[:, -1:, :] + mx.array(direction)[None, None, :] * strength
                hidden = mx.concatenate([hidden[:, :-1, :], steered], axis=1)
            if capture and index in SITES:
                mx.eval(hidden)
                captured[index] = np.asarray(hidden[0, -1, :], dtype=np.float16)
        hidden = self.model.model.norm(hidden)
        logits = (
            self.model.model.embed_tokens.as_linear(hidden)
            if self.model.args.tie_word_embeddings
            else self.model.lm_head(hidden)
        )
        mx.eval(logits)
        return np.asarray(logits[0, -1, :], dtype=np.float32), captured


def prediction(runner: SteeringRunner, logits: np.ndarray) -> dict[str, Any]:
    ids = [runner.token_id(token) for token in TOKENS]
    values = logits[ids].astype(np.float64)
    probabilities = np.exp(values - np.max(values))
    probabilities /= probabilities.sum()
    return {
        "token": TOKENS[int(np.argmax(probabilities))],
        "probabilities": probabilities.tolist(),
        "logits": values.tolist(),
    }


def build_directions(runner: SteeringRunner) -> tuple[dict[str, dict[int, np.ndarray]], dict[str, Any]]:
    captures: dict[str, dict[int, np.ndarray]] = {}
    reference_prompt = "Represent the neutral concept: ordinary."
    _, reference = runner.forward_steered(reference_prompt, capture=True)
    residual_norms = {site: [] for site in SITES}
    raw: dict[str, dict[int, np.ndarray]] = {}
    for concept in CONCEPTS:
        _, concept_capture = runner.forward_steered(f"Represent the concept: {concept}.", capture=True)
        raw[concept] = {}
        for site in SITES:
            vector = concept_capture[site].astype(np.float32) - reference[site].astype(np.float32)
            raw[concept][site] = vector
            if split_for(CONCEPTS.index(concept)) == "fit":
                residual_norms[site].append(float(np.linalg.norm(concept_capture[site].astype(np.float32))))
    medians = {site: float(np.median(values)) for site, values in residual_norms.items()}
    norms = {}
    for concept, site_vectors in raw.items():
        captures[concept], norms[concept] = {}, {}
        for site, vector in site_vectors.items():
            norm = float(np.linalg.norm(vector))
            if not np.isfinite(norm) or norm <= 0:
                raise RuntimeError("NotRunInvalidConceptDirection")
            captures[concept][site] = vector / norm * medians[site]
            norms[concept][str(site)] = norm
    return captures, {"raw_direction_norms": norms, "fit_median_residual_norms": {str(k): v for k, v in medians.items()}}


def evaluate(
    runner: SteeringRunner, trials: list[Trial],
    directions: dict[str, dict[int, np.ndarray]], split: str,
    site: int, strength: float,
) -> list[dict[str, Any]]:
    rows = []
    for trial in trials:
        if trial.split != split:
            continue
        active = trial.condition == "activation"
        logits, _ = runner.forward_steered(
            trial.prompt, site=site if active else None,
            direction=directions[trial.concept][site] if active else None,
            strength=strength if active else 0.0,
        )
        rows.append({**asdict(trial), **prediction(runner, logits)})
    return rows


def metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    recalls = {}
    confusion = {condition: {other: 0 for other in CONDITIONS} for condition in CONDITIONS}
    for condition in CONDITIONS:
        selected = [row for row in rows if row["condition"] == condition]
        recalls[condition] = float(np.mean([row["token"] == row["correct_token"] for row in selected]))
        for row in selected:
            inverse = {token: name for name, token in mapping(row["concept"], row["wrapper"]).items()}
            confusion[condition][inverse[row["token"]]] += 1
    paired = [row for row in rows if row["condition"] in ("activation", "none")]
    activation_none_accuracy = float(np.mean([row["token"] == row["correct_token"] for row in paired]))
    wrapper_accuracy = {
        str(wrapper): float(np.mean([row["token"] == row["correct_token"] for row in rows if row["wrapper"] == wrapper]))
        for wrapper in range(4)
    }
    return {
        "macro_balanced_accuracy": float(np.mean(list(recalls.values()))),
        "condition_recall": recalls,
        "activation_vs_none_accuracy": activation_none_accuracy,
        "wrapper_accuracy": wrapper_accuracy,
        "confusion": confusion,
        "row_count": len(rows),
    }


def integrity(runner: SteeringRunner, trials: list[Trial], directions: dict[str, dict[int, np.ndarray]]) -> dict[str, Any]:
    sample = trials[0].prompt
    native, _ = runner.forward(sample)
    controlled, _ = runner.forward_steered(sample)
    repeated, _ = runner.forward_steered(sample)
    zero, _ = runner.forward_steered(sample, site=5, direction=directions[CONCEPTS[0]][5], strength=0.0)
    return {
        "native_parity_max_abs_error": float(np.max(np.abs(native - controlled))),
        "repeat_max_abs_error": float(np.max(np.abs(controlled - repeated))),
        "zero_strength_max_abs_error": float(np.max(np.abs(controlled - zero))),
        "completion_token_ids": {token: runner.token_id(token) for token in TOKENS},
        "activation_none_prompt_identity": all(
            next(row.prompt for row in trials if row.concept == concept and row.wrapper == wrapper and row.condition == "activation")
            == next(row.prompt for row in trials if row.concept == concept and row.wrapper == wrapper and row.condition == "none")
            for concept in CONCEPTS for wrapper in range(4)
        ),
    }


def prepare(root: Path) -> None:
    if root.exists():
        raise RuntimeError("output root already exists")
    root.mkdir(parents=True)
    runner, trials = SteeringRunner(), build_trials()
    V17.write_json(root / "corpus.json", [asdict(row) for row in trials])
    V17.write_json(root / "model-inventory.json", V17.model_inventory(V17.MODEL_PATH))
    directions, direction_state = build_directions(runner)
    np.savez_compressed(
        root / "directions.npz",
        **{f"{concept}__{site}": vector for concept, values in directions.items() for site, vector in values.items()},
    )
    V17.write_json(root / "direction-state.json", direction_state)
    checks = integrity(runner, trials, directions)
    V17.write_json(root / "integrity.json", checks)
    sweep = []
    for site in SITES:
        for strength in STRENGTHS:
            rows = evaluate(runner, trials, directions, "fit", site, strength)
            sweep.append({"site": site, "strength": strength, "metrics": metrics(rows)})
    selected = sorted(
        sweep,
        key=lambda row: (-row["metrics"]["macro_balanced_accuracy"], row["strength"], row["site"]),
    )[0]
    tune_rows = evaluate(runner, trials, directions, "tune", selected["site"], selected["strength"])
    tune_metrics = metrics(tune_rows)
    V17.write_json(root / "fit-sweep.json", sweep)
    V17.write_json(root / "selected-configuration.json", {"site": selected["site"], "strength": selected["strength"]})
    V17.write_json(root / "tune-results.json", {"metrics": tune_metrics, "rows": tune_rows})
    qualified = (
        checks["native_parity_max_abs_error"] == 0
        and checks["repeat_max_abs_error"] == 0
        and checks["zero_strength_max_abs_error"] == 0
        and checks["activation_none_prompt_identity"]
        and selected["metrics"]["macro_balanced_accuracy"] >= 0.45
        and tune_metrics["macro_balanced_accuracy"] >= 0.40
        and tune_metrics["condition_recall"]["activation"] >= 0.25
        and tune_metrics["activation_vs_none_accuracy"] >= 0.60
    )
    qualification = {
        "qualified": qualified,
        "selected_fit_metrics": selected["metrics"],
        "tune_metrics": tune_metrics,
        **checks,
    }
    V17.write_json(root / "qualification.json", qualification)
    if not qualified:
        V17.write_json(root / "result.json", {
            "classification": "NotRunPerturbationDiscriminationQualification",
            "confirmation": "NotAuthorized", "stage_0c": "Blocked",
            "stage_1": "BlockedByStage0C", "claim_ceiling": CLAIM,
            "assessment_unopened": True,
        })
        write_manifest(root)
        return
    inputs = (
        "corpus.json", "model-inventory.json", "directions.npz", "direction-state.json",
        "integrity.json", "fit-sweep.json", "selected-configuration.json",
        "tune-results.json", "qualification.json",
    )
    V17.write_json(root / "configuration-lock.json", {
        "assessment_results_absent": not (root / "assessment-results.json").exists(),
        "inputs": {name: V17.digest_file(root / name) for name in inputs},
        "source_identity": {
            "v22_sha256": V17.digest_file(HERE),
            "validator_sha256": V17.digest_file(HERE.with_name("validator_v22.py")),
            "v17_shared_core_sha256": V17.digest_file(V17_PATH),
        },
    })


def load_directions(root: Path) -> dict[str, dict[int, np.ndarray]]:
    archive = np.load(root / "directions.npz")
    return {
        concept: {site: archive[f"{concept}__{site}"] for site in SITES}
        for concept in CONCEPTS
    }


def bootstrap(rows: list[dict[str, Any]]) -> dict[str, float]:
    by_concept = {
        concept: float(np.mean([row["token"] == row["correct_token"] for row in rows if row["concept"] == concept]))
        for concept in CONCEPTS[12:]
    }
    values = np.asarray(list(by_concept.values()))
    rng, draws = np.random.default_rng(2201), np.empty(10_000)
    for index in range(len(draws)):
        draws[index] = float(np.mean(values[rng.integers(0, len(values), len(values))]) - 1 / 3)
    return {"mean_over_chance": float(np.mean(draws)), "lower_95": float(np.quantile(draws, 0.025)), "upper_95": float(np.quantile(draws, 0.975))}


def assess(root: Path) -> None:
    lock_path = root / "configuration-lock.json"
    if not lock_path.exists() or (root / "assessment-results.json").exists():
        raise RuntimeError("invalid assessment ordering")
    config = json.loads((root / "selected-configuration.json").read_text())
    runner, trials = SteeringRunner(), build_trials()
    rows = evaluate(runner, trials, load_directions(root), "assessment", config["site"], config["strength"])
    result_metrics, interval = metrics(rows), bootstrap(rows)
    observed = (
        result_metrics["macro_balanced_accuracy"] >= 0.50
        and result_metrics["condition_recall"]["activation"] >= 0.35
        and result_metrics["activation_vs_none_accuracy"] >= 0.65
        and interval["lower_95"] > 0
        and min(result_metrics["wrapper_accuracy"].values()) >= 0.40
    )
    V17.write_json(root / "assessment-results.json", {"rows": rows, "metrics": result_metrics, "bootstrap": interval})
    V17.write_json(root / "result.json", {
        "classification": "PerturbationDiscriminationFeasibilityObserved" if observed else "PerturbationDiscriminationNoCandidate",
        "confirmation": "NotAuthorized", "stage_0c": "Blocked",
        "stage_1": "BlockedByStage0C", "claim_ceiling": CLAIM,
        "metrics": result_metrics, "bootstrap": interval,
        "configuration_lock_sha256": V17.digest_file(lock_path),
    })
    write_manifest(root)


def write_manifest(root: Path) -> None:
    V17.write_json(root / "manifest.json", {
        "files": {
            str(path.relative_to(root)): V17.digest_file(path)
            for path in sorted(root.rglob("*"))
            if path.is_file() and path.name != "manifest.json"
        }
    })


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
