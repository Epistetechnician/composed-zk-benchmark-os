#!/usr/bin/env python3
"""V24 fixed downstream perturbation-readout development experiment."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import mlx.core as mx
import numpy as np
from mlx_lm.models.base import create_attention_mask


HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[2]
V22_PATH = HERE.parents[1] / "astral-activation-discrimination-v22" / "v22.py"
PREREGISTRATION_PATH = (
    REPOSITORY
    / "docs/research/astral-self-modeling/"
    "48-v24-downstream-perturbation-readout-preregistration.md"
)
INJECTION_SITE = 5
READOUT_SITE = 17
STRENGTH = 1.0
PCA_COMPONENTS = 16
RIDGE_PENALTY = 1.0
FEATURE_WIDTH = 16
CONDITIONS = ("activation", "text", "none")
METHODS = ("telemetry", "text", "output", "anomaly", "shuffled")
PRIMARY_CONTROLS = ("text", "output", "anomaly")
CLAIM = "LocalAuthorDevelopmentPerturbationReadout"
RUNTIME_PACKAGES = ("mlx", "mlx-lm", "numpy", "torch")
CONCEPTS = (
    "maple",
    "oboe",
    "tundra",
    "signal",
    "savanna",
    "silver",
    "estuary",
    "linen",
    "gorge",
    "basalt",
    "iris",
    "sextant",
    "alder",
    "tramway",
    "paprika",
    "jetty",
    "spruce",
    "bassoon",
    "lagoon",
    "canvas",
)
WRAPPERS = (
    "Classify the source of any change in this evaluation.",
    "Identify where the experimental manipulation occurred.",
    "Report whether this pass changed state, input, or neither.",
    "Select the location of the intervention for this trial.",
)
SPLIT_COUNTS = {"fit": 8, "development": 4, "tune": 4, "assessment": 4}
GATES = {
    "activation_none_balanced_accuracy": 0.75,
    "primary_advantage": 0.10,
    "macro_balanced_accuracy": 0.60,
    "activation_recall": 0.65,
    "none_recall": 0.65,
    "minimum_wrapper_accuracy": 0.50,
    "maximum_brier": 0.55,
    "maximum_shuffled_activation_none": 0.60,
}


def import_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


V22 = import_path("astral_v22_core_for_v24", V22_PATH)
V17 = V22.V17


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def environment_inventory() -> dict[str, Any]:
    packages = {}
    for package in RUNTIME_PACKAGES:
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = "absent"
    return {
        "python": sys.version,
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "mlx_default_device": str(mx.default_device()),
        "mlx_device_info": mx.device_info(),
        "packages": packages,
    }


@dataclass(frozen=True)
class Trial:
    trial_id: str
    split: str
    concept: str
    wrapper: int
    condition: str
    prompt: str


def split_for(index: int) -> str:
    if index < 8:
        return "fit"
    if index < 12:
        return "development"
    if index < 16:
        return "tune"
    return "assessment"


def build_trials() -> list[Trial]:
    rows = []
    for index, concept in enumerate(CONCEPTS):
        for wrapper, instruction in enumerate(WRAPPERS):
            mapping_seed = int(digest_text(f"v24:{concept}:{wrapper}")[:2], 16) % 3
            labels = CONDITIONS[mapping_seed:] + CONDITIONS[:mapping_seed]
            legend = "; ".join(
                f"{chr(65 + position)} means {condition}"
                for position, condition in enumerate(labels)
            )
            base = (
                f"{instruction}\n"
                "A hidden activation may be altered, only the visible input may be "
                "altered, or the pass may be unchanged.\n"
                f"{legend}.\nAnswer A, B, or C."
            )
            text_prompt = (
                f"Visible external instruction: emphasize the concept {concept}.\n"
                + base
            )
            for condition in CONDITIONS:
                rows.append(
                    Trial(
                        trial_id=f"v24-{index:02d}-{wrapper}-{condition}",
                        split=split_for(index),
                        concept=concept,
                        wrapper=wrapper,
                        condition=condition,
                        prompt=text_prompt if condition == "text" else base,
                    )
                )
    return rows


class ReadoutRunner(V22.SteeringRunner):
    def forward_readout(
        self,
        prompt: str,
        direction: np.ndarray | None = None,
        strength: float = 0.0,
    ) -> tuple[np.ndarray, np.ndarray]:
        ids = mx.array([self.tokenizer.encode(prompt, add_special_tokens=False)])
        hidden = self.model.model.embed_tokens(ids)
        mask = create_attention_mask(hidden, None)
        residual = None
        for index, layer in enumerate(self.layers):
            hidden = layer(hidden, mask, None)
            if index == INJECTION_SITE and strength != 0.0:
                if direction is None or direction.shape != (896,):
                    raise ValueError("V24 direction must have shape (896,)")
                changed = hidden[:, -1:, :] + mx.array(direction)[None, None, :] * strength
                hidden = mx.concatenate([hidden[:, :-1, :], changed], axis=1)
            if index == READOUT_SITE:
                mx.eval(hidden)
                residual = np.asarray(hidden[0, -1, :], dtype=np.float32)
        if residual is None:
            raise RuntimeError("NotRunReadoutSiteAbsent")
        hidden = self.model.model.norm(hidden)
        logits = (
            self.model.model.embed_tokens.as_linear(hidden)
            if self.model.args.tie_word_embeddings
            else self.model.lm_head(hidden)
        )
        mx.eval(logits)
        return np.asarray(logits[0, -1, :], dtype=np.float32), residual


def build_directions(runner: ReadoutRunner) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    _, reference = runner.forward_steered(
        "Represent the neutral concept: ordinary.", capture=True
    )
    raw = {}
    for concept in CONCEPTS:
        _, captured = runner.forward_steered(
            f"Represent the concept: {concept}.", capture=True
        )
        vector = captured[INJECTION_SITE].astype(np.float32) - reference[
            INJECTION_SITE
        ].astype(np.float32)
        norm = float(np.linalg.norm(vector))
        if not np.isfinite(norm) or norm <= 0:
            raise RuntimeError("NotRunInvalidConceptDirection")
        raw[concept] = (vector, norm)
    directions = {
        concept: normalize_direction(vector) for concept, (vector, _) in raw.items()
    }
    return directions, {
        "normalization": "unit_l2",
        "raw_direction_norms": {concept: norm for concept, (_, norm) in raw.items()},
    }


def normalize_direction(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if not np.isfinite(norm) or norm <= 0:
        raise RuntimeError("NotRunInvalidConceptDirection")
    return vector.astype(np.float32) / norm


def text_features(runner: ReadoutRunner, trial: Trial) -> np.ndarray:
    values = [
        float(len(trial.prompt)),
        float(len(runner.tokenizer.encode(trial.prompt, add_special_tokens=False))),
        float("Visible external instruction:" in trial.prompt),
        *[float(trial.wrapper == index) for index in range(4)],
    ]
    return pad(np.asarray(values, dtype=np.float64))


def output_features(runner: ReadoutRunner, logits: np.ndarray) -> np.ndarray:
    token_ids = [runner.token_id(token) for token in V22.TOKENS]
    selected = logits[token_ids].astype(np.float64)
    probabilities = softmax(selected[None, :])[0]
    entropy = -float(np.sum(probabilities * np.log(np.maximum(probabilities, 1e-12))))
    ordered = np.sort(selected)
    values = np.concatenate(
        [selected, probabilities, np.asarray([entropy, ordered[-1] - ordered[-2]])]
    )
    return pad(values)


def pad(values: np.ndarray) -> np.ndarray:
    if len(values) > FEATURE_WIDTH:
        raise ValueError("feature width exceeded")
    return np.pad(values, (0, FEATURE_WIDTH - len(values)))


def collect_raw(
    runner: ReadoutRunner,
    trials: list[Trial],
    directions: dict[str, np.ndarray],
    splits: set[str],
) -> dict[str, np.ndarray]:
    selected = [trial for trial in trials if trial.split in splits]
    residuals, outputs, texts = [], [], []
    for trial in selected:
        active = trial.condition == "activation"
        logits, residual = runner.forward_readout(
            trial.prompt,
            directions[trial.concept] if active else None,
            STRENGTH if active else 0.0,
        )
        residuals.append(residual)
        outputs.append(output_features(runner, logits))
        texts.append(text_features(runner, trial))
    return {
        "trial_id": np.asarray([trial.trial_id for trial in selected]),
        "split": np.asarray([trial.split for trial in selected]),
        "concept": np.asarray([trial.concept for trial in selected]),
        "wrapper": np.asarray([trial.wrapper for trial in selected], dtype=np.int64),
        "label": np.asarray(
            [CONDITIONS.index(trial.condition) for trial in selected], dtype=np.int64
        ),
        "residual": np.asarray(residuals, dtype=np.float32),
        "output": np.asarray(outputs, dtype=np.float64),
        "text": np.asarray(texts, dtype=np.float64),
    }


def pca_fit(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = values.mean(axis=0, dtype=np.float64)
    centered = values.astype(np.float64) - mean
    _, _, right = np.linalg.svd(centered, full_matrices=False)
    basis = right[:PCA_COMPONENTS].copy()
    for row in basis:
        pivot = int(np.argmax(np.abs(row)))
        if row[pivot] < 0:
            row *= -1
    return mean, basis


def anomaly_features(residuals: np.ndarray, centroid: np.ndarray) -> np.ndarray:
    rows = []
    for residual in residuals.astype(np.float64):
        rows.append(
            pad(
                np.asarray(
                    [
                        np.linalg.norm(residual),
                        np.mean(residual),
                        np.std(residual),
                        np.max(np.abs(residual)),
                        np.linalg.norm(residual - centroid),
                    ]
                )
            )
        )
    return np.asarray(rows)


def method_features(
    raw: dict[str, np.ndarray],
    train_mask: np.ndarray,
    transform: dict[str, np.ndarray] | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    if transform is None:
        pca_mean, pca_basis = pca_fit(raw["residual"][train_mask])
        anomaly_centroid = raw["residual"][train_mask].mean(axis=0, dtype=np.float64)
        transform = {
            "pca_mean": pca_mean,
            "pca_basis": pca_basis,
            "anomaly_centroid": anomaly_centroid,
        }
    telemetry = (raw["residual"].astype(np.float64) - transform["pca_mean"]) @ transform[
        "pca_basis"
    ].T
    features = {
        "telemetry": telemetry,
        "text": raw["text"].astype(np.float64),
        "output": raw["output"].astype(np.float64),
        "anomaly": anomaly_features(raw["residual"], transform["anomaly_centroid"]),
        "shuffled": telemetry,
    }
    return features, transform


def ridge_fit(features: np.ndarray, labels: np.ndarray) -> dict[str, np.ndarray]:
    mean = features.mean(axis=0)
    scale = features.std(axis=0)
    scale[scale < 1e-12] = 1.0
    standardized = (features - mean) / scale
    design = np.column_stack([standardized, np.ones(len(standardized))])
    penalty = np.eye(design.shape[1]) * RIDGE_PENALTY
    penalty[-1, -1] = 0.0
    targets = np.eye(len(CONDITIONS))[labels]
    coefficients = np.linalg.solve(
        design.T @ design + penalty, design.T @ targets
    )
    return {"mean": mean, "scale": scale, "coefficients": coefficients}


def ridge_predict(model: dict[str, np.ndarray], features: np.ndarray) -> np.ndarray:
    standardized = (features - model["mean"]) / model["scale"]
    design = np.column_stack([standardized, np.ones(len(standardized))])
    return softmax(design @ model["coefficients"])


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    values = np.exp(shifted)
    return values / values.sum(axis=1, keepdims=True)


def fit_models(
    features: dict[str, np.ndarray],
    labels: np.ndarray,
    train_mask: np.ndarray,
) -> dict[str, dict[str, np.ndarray]]:
    models = {}
    shuffled = labels[train_mask].copy()
    np.random.default_rng(2401).shuffle(shuffled)
    for method in METHODS:
        train_labels = shuffled if method == "shuffled" else labels[train_mask]
        models[method] = ridge_fit(features[method][train_mask], train_labels)
    return models


def metrics(
    probabilities: np.ndarray,
    labels: np.ndarray,
    wrappers: np.ndarray,
) -> dict[str, Any]:
    predicted = probabilities.argmax(axis=1)
    recalls = {
        condition: float(np.mean(predicted[labels == index] == index))
        for index, condition in enumerate(CONDITIONS)
    }
    wrapper_accuracy = {
        str(wrapper): float(np.mean(predicted[wrappers == wrapper] == labels[wrappers == wrapper]))
        for wrapper in range(4)
    }
    targets = np.eye(len(CONDITIONS))[labels]
    return {
        "activation_none_balanced_accuracy": float(
            (recalls["activation"] + recalls["none"]) / 2
        ),
        "macro_balanced_accuracy": float(np.mean(list(recalls.values()))),
        "condition_recall": recalls,
        "wrapper_accuracy": wrapper_accuracy,
        "brier": float(np.mean(np.sum((probabilities - targets) ** 2, axis=1))),
        "row_count": int(len(labels)),
    }


def evaluate_split(
    raw: dict[str, np.ndarray],
    features: dict[str, np.ndarray],
    models: dict[str, dict[str, np.ndarray]],
    split: str,
) -> dict[str, Any]:
    mask = raw["split"] == split
    return {
        method: metrics(
            ridge_predict(models[method], features[method][mask]),
            raw["label"][mask],
            raw["wrapper"][mask],
        )
        for method in METHODS
    }


def gate(metrics_by_method: dict[str, Any]) -> dict[str, Any]:
    telemetry = metrics_by_method["telemetry"]
    best_control = max(
        metrics_by_method[method]["activation_none_balanced_accuracy"]
        for method in PRIMARY_CONTROLS
    )
    advantage = telemetry["activation_none_balanced_accuracy"] - best_control
    checks = {
        "activation_none_balanced_accuracy": telemetry[
            "activation_none_balanced_accuracy"
        ]
        >= GATES["activation_none_balanced_accuracy"],
        "primary_advantage": advantage >= GATES["primary_advantage"],
        "macro_balanced_accuracy": telemetry["macro_balanced_accuracy"]
        >= GATES["macro_balanced_accuracy"],
        "activation_recall": telemetry["condition_recall"]["activation"]
        >= GATES["activation_recall"],
        "none_recall": telemetry["condition_recall"]["none"]
        >= GATES["none_recall"],
        "minimum_wrapper_accuracy": min(telemetry["wrapper_accuracy"].values())
        >= GATES["minimum_wrapper_accuracy"],
        "maximum_brier": telemetry["brier"] <= GATES["maximum_brier"],
        "maximum_shuffled_activation_none": metrics_by_method["shuffled"][
            "activation_none_balanced_accuracy"
        ]
        <= GATES["maximum_shuffled_activation_none"],
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "primary_advantage": advantage,
        "best_primary_control": best_control,
    }


def serialize_lock(
    path: Path,
    transform: dict[str, np.ndarray],
    models: dict[str, dict[str, np.ndarray]],
) -> None:
    values = {
        "pca_mean": transform["pca_mean"],
        "pca_basis": transform["pca_basis"],
        "anomaly_centroid": transform["anomaly_centroid"],
    }
    for method, model in models.items():
        for name, value in model.items():
            values[f"{method}__{name}"] = value
    np.savez_compressed(path, **values)


def load_lock(path: Path) -> tuple[dict[str, np.ndarray], dict[str, dict[str, np.ndarray]]]:
    archive = np.load(path)
    transform = {
        "pca_mean": archive["pca_mean"],
        "pca_basis": archive["pca_basis"],
        "anomaly_centroid": archive["anomaly_centroid"],
    }
    models = {
        method: {
            name: archive[f"{method}__{name}"]
            for name in ("mean", "scale", "coefficients")
        }
        for method in METHODS
    }
    return transform, models


def integrity(
    runner: ReadoutRunner, trials: list[Trial], directions: dict[str, np.ndarray]
) -> dict[str, Any]:
    sample = trials[0].prompt
    native, _ = runner.forward(sample)
    controlled, residual = runner.forward_readout(sample)
    repeated, repeated_residual = runner.forward_readout(sample)
    zero, _ = runner.forward_readout(sample, directions[CONCEPTS[0]], 0.0)
    direction_norms = [float(np.linalg.norm(value)) for value in directions.values()]
    return {
        "native_parity_max_abs_error": float(np.max(np.abs(native - controlled))),
        "repeat_logits_max_abs_error": float(np.max(np.abs(controlled - repeated))),
        "repeat_residual_max_abs_error": float(
            np.max(np.abs(residual - repeated_residual))
        ),
        "zero_strength_max_abs_error": float(np.max(np.abs(controlled - zero))),
        "activation_none_prompt_identity": all(
            next(
                row.prompt
                for row in trials
                if row.concept == concept
                and row.wrapper == wrapper
                and row.condition == "activation"
            )
            == next(
                row.prompt
                for row in trials
                if row.concept == concept
                and row.wrapper == wrapper
                and row.condition == "none"
            )
            for concept in CONCEPTS
            for wrapper in range(4)
        ),
        "injection_site": INJECTION_SITE,
        "readout_site": READOUT_SITE,
        "downstream_readout": READOUT_SITE > INJECTION_SITE,
        "direction_normalization": "unit_l2",
        "direction_norm_min": min(direction_norms),
        "direction_norm_max": max(direction_norms),
        "strength": STRENGTH,
    }


def fixed_configuration() -> dict[str, Any]:
    return {
        "injection_site": INJECTION_SITE,
        "readout_site": READOUT_SITE,
        "strength": STRENGTH,
        "pca_components": PCA_COMPONENTS,
        "ridge_penalty": RIDGE_PENALTY,
        "feature_width": FEATURE_WIDTH,
        "direction_normalization": "unit_l2",
        "methods": list(METHODS),
        "gates": GATES,
        "author_development_authorized": True,
        "independently_verified": "NotRun",
    }


def write_manifest(root: Path) -> None:
    V17.write_json(
        root / "manifest.json",
        {
            "files": {
                str(path.relative_to(root)): V17.digest_file(path)
                for path in sorted(root.rglob("*"))
                if path.is_file() and path.name != "manifest.json"
            }
        },
    )


def prepare(root: Path) -> None:
    if root.exists():
        raise RuntimeError("output root already exists")
    root.mkdir(parents=True)
    if (root / "assessment-features.npz").exists() or (
        root / "assessment-results.json"
    ).exists() or (root / "assessment-started.json").exists():
        raise RuntimeError("assessment materialized before preparation")
    runner, trials = ReadoutRunner(), build_trials()
    V17.write_json(root / "corpus.json", [asdict(row) for row in trials])
    V17.write_json(root / "model-inventory.json", V17.model_inventory(V17.MODEL_PATH))
    V17.write_json(root / "environment-inventory.json", environment_inventory())
    V17.write_json(root / "fixed-configuration.json", fixed_configuration())
    directions, direction_state = build_directions(runner)
    np.savez_compressed(
        root / "directions.npz",
        **{concept: direction for concept, direction in directions.items()},
    )
    V17.write_json(root / "direction-state.json", direction_state)
    checks = integrity(runner, trials, directions)
    V17.write_json(root / "integrity.json", checks)
    development_raw = collect_raw(
        runner, trials, directions, {"fit", "development", "tune"}
    )
    np.savez_compressed(root / "development-features.npz", **development_raw)
    V17.write_json(
        root / "development-rows.json",
        [
            asdict(trial)
            for trial in trials
            if trial.split in {"fit", "development", "tune"}
        ],
    )
    fit_mask = development_raw["split"] == "fit"
    features, transform = method_features(development_raw, fit_mask)
    models = fit_models(features, development_raw["label"], fit_mask)
    split_metrics = {
        split: evaluate_split(development_raw, features, models, split)
        for split in ("development", "tune")
    }
    gates = {split: gate(values) for split, values in split_metrics.items()}
    V17.write_json(
        root / "development-metrics.json",
        {"metrics": split_metrics, "gates": gates},
    )
    qualified = all(value["passed"] for value in gates.values()) and all(
        (
            checks["native_parity_max_abs_error"] == 0,
            checks["repeat_logits_max_abs_error"] == 0,
            checks["repeat_residual_max_abs_error"] == 0,
            checks["zero_strength_max_abs_error"] == 0,
            checks["activation_none_prompt_identity"],
            checks["downstream_readout"],
            abs(checks["direction_norm_min"] - 1.0) <= 1e-6,
            abs(checks["direction_norm_max"] - 1.0) <= 1e-6,
        )
    )
    qualification = {
        "qualified": qualified,
        "assessment_features_absent": not (root / "assessment-features.npz").exists(),
        "assessment_results_absent": not (root / "assessment-results.json").exists(),
        "development_gates": gates,
        **checks,
    }
    V17.write_json(root / "qualification.json", qualification)
    if not qualified:
        V17.write_json(
            root / "result.json",
            {
                "classification": "NotRunAuthorDevelopmentPerturbationReadoutQualification",
                "author_development_authorized": True,
                "independently_verified": "NotRun",
                "assessment_unopened": True,
                "stage_0c": "Blocked",
                "stage_1": "BlockedByStage0C",
                "claim_ceiling": CLAIM,
            },
        )
        write_manifest(root)
        return
    all_mask = np.ones(len(development_raw["label"]), dtype=bool)
    final_features, final_transform = method_features(development_raw, all_mask)
    final_models = fit_models(
        final_features, development_raw["label"], all_mask
    )
    serialize_lock(root / "readout-lock.npz", final_transform, final_models)
    inputs = (
        "corpus.json",
        "model-inventory.json",
        "environment-inventory.json",
        "fixed-configuration.json",
        "directions.npz",
        "direction-state.json",
        "integrity.json",
        "development-features.npz",
        "development-rows.json",
        "development-metrics.json",
        "qualification.json",
        "readout-lock.npz",
    )
    V17.write_json(
        root / "configuration-lock.json",
        {
            "assessment_features_absent": not (
                root / "assessment-features.npz"
            ).exists(),
            "assessment_results_absent": not (
                root / "assessment-results.json"
            ).exists(),
            "assessment_started_absent": not (
                root / "assessment-started.json"
            ).exists(),
            "inputs": {name: V17.digest_file(root / name) for name in inputs},
            "source_identity": expected_source_identity(),
        },
    )


def expected_source_identity() -> dict[str, str]:
    return {
        "v24_sha256": V17.digest_file(HERE),
        "validator_sha256": V17.digest_file(HERE.with_name("validator_v24.py")),
        "v22_shared_core_sha256": V17.digest_file(V22_PATH),
        "v17_shared_core_sha256": V17.digest_file(V22.V17_PATH),
        "preregistration_sha256": V17.digest_file(PREREGISTRATION_PATH),
    }


def validate_configuration_lock(root: Path) -> dict[str, Any]:
    lock_path = root / "configuration-lock.json"
    if not lock_path.exists():
        raise RuntimeError("configuration lock absent")
    if any(
        (root / name).exists()
        for name in (
            "assessment-started.json",
            "assessment-features.npz",
            "assessment-results.json",
        )
    ):
        raise RuntimeError("assessment materialized before lock validation")
    lock = json.loads(lock_path.read_text())
    if not all(
        (
            lock["assessment_started_absent"],
            lock["assessment_features_absent"],
            lock["assessment_results_absent"],
        )
    ):
        raise RuntimeError("configuration lock ordering failure")
    for name, expected in lock["inputs"].items():
        if V17.digest_file(root / name) != expected:
            raise RuntimeError(f"configuration lock digest mismatch: {name}")
    if lock["source_identity"] != expected_source_identity():
        raise RuntimeError("configuration lock source identity mismatch")
    qualification = json.loads((root / "qualification.json").read_text())
    if not qualification["qualified"]:
        raise RuntimeError("configuration lock cannot open failed qualification")
    return {
        "lock_valid": True,
        "configuration_lock_sha256": V17.digest_file(lock_path),
    }


def load_directions(root: Path) -> dict[str, np.ndarray]:
    archive = np.load(root / "directions.npz")
    return {concept: archive[concept] for concept in CONCEPTS}


def assessment_bootstrap(
    raw: dict[str, np.ndarray],
    probabilities: dict[str, np.ndarray],
) -> dict[str, float]:
    concepts = sorted(set(raw["concept"].tolist()))
    rng = np.random.default_rng(2424)
    draws = np.empty(10_000)
    for index in range(len(draws)):
        sampled = rng.choice(concepts, size=len(concepts), replace=True)
        indices = np.concatenate(
            [np.flatnonzero(raw["concept"] == concept) for concept in sampled]
        )
        telemetry = metrics(
            probabilities["telemetry"][indices],
            raw["label"][indices],
            raw["wrapper"][indices],
        )["activation_none_balanced_accuracy"]
        control = max(
            metrics(
                probabilities[method][indices],
                raw["label"][indices],
                raw["wrapper"][indices],
            )["activation_none_balanced_accuracy"]
            for method in PRIMARY_CONTROLS
        )
        draws[index] = telemetry - control
    return {
        "mean_primary_advantage": float(np.mean(draws)),
        "lower_95": float(np.quantile(draws, 0.025)),
        "upper_95": float(np.quantile(draws, 0.975)),
    }


def assess(root: Path) -> None:
    lock_path = root / "configuration-lock.json"
    if (
        not lock_path.exists()
        or (root / "assessment-started.json").exists()
        or (root / "assessment-features.npz").exists()
        or (root / "assessment-results.json").exists()
    ):
        raise RuntimeError("invalid assessment ordering")
    lock_validation = validate_configuration_lock(root)
    V17.write_json(
        root / "assessment-started.json",
        {
            "assessment_forward_budget": 48,
            "configuration_lock_sha256": lock_validation[
                "configuration_lock_sha256"
            ],
            "one_shot": True,
        },
    )
    runner, trials = ReadoutRunner(), build_trials()
    raw = collect_raw(
        runner, trials, load_directions(root), {"assessment"}
    )
    np.savez_compressed(root / "assessment-features.npz", **raw)
    transform, models = load_lock(root / "readout-lock.npz")
    features, _ = method_features(
        raw, np.ones(len(raw["label"]), dtype=bool), transform
    )
    probabilities = {
        method: ridge_predict(models[method], features[method])
        for method in METHODS
    }
    result_metrics = {
        method: metrics(
            probabilities[method], raw["label"], raw["wrapper"]
        )
        for method in METHODS
    }
    result_gate = gate(result_metrics)
    interval = assessment_bootstrap(raw, probabilities)
    observed = result_gate["passed"] and interval["lower_95"] > 0
    V17.write_json(
        root / "assessment-results.json",
        {
            "metrics": result_metrics,
            "gate": result_gate,
            "bootstrap": interval,
            "predictions": {
                method: probabilities[method].tolist() for method in METHODS
            },
            "trial_ids": raw["trial_id"].tolist(),
        },
    )
    V17.write_json(
        root / "result.json",
        {
            "classification": (
                "AuthorDevelopmentPerturbationReadoutObserved"
                if observed
                else "AuthorDevelopmentPerturbationReadoutNoCandidate"
            ),
            "author_development_authorized": True,
            "independently_verified": "NotRun",
            "confirmation": "NotAuthorized",
            "stage_0c": "Blocked",
            "stage_1": "BlockedByStage0C",
            "claim_ceiling": CLAIM,
            "metrics": result_metrics,
            "gate": result_gate,
            "bootstrap": interval,
            "configuration_lock_sha256": V17.digest_file(lock_path),
        },
    )
    write_manifest(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "assess"))
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    try:
        (prepare if args.phase == "prepare" else assess)(args.root.resolve())
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "status": "completed",
                "phase": args.phase,
                "root": str(args.root.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
