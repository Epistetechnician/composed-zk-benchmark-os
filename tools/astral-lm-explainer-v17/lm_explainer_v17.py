#!/usr/bin/env python3
"""Prospective V17 local pretrained-LM intervention-effect pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import resource
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import mlx.core as mx
import numpy as np
import torch
from mlx_lm import load
from mlx_lm.models.base import create_attention_mask

MODEL_PATH = Path(
    "/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit"
)
SITES = (5, 11, 17)
FIT_FAMILIES = range(0, 24)
TUNE_FAMILIES = range(24, 32)
ASSESS_FAMILIES = range(32, 40)
SEEDS = (1701, 1703, 1709)
METHODS = ("telemetry", "activation", "text_io", "shuffled")
MODEL_CLAIM = "LocalDevelopmentPretrainedModelEffectExplainerPilot"

NOUNS = (
    ("key", "keys", "cabinet", "cabinets"),
    ("letter", "letters", "drawer", "drawers"),
    ("picture", "pictures", "frame", "frames"),
    ("bottle", "bottles", "shelf", "shelves"),
    ("coin", "coins", "purse", "purses"),
    ("ticket", "tickets", "folder", "folders"),
    ("book", "books", "table", "tables"),
    ("lamp", "lamps", "window", "windows"),
    ("flower", "flowers", "vase", "vases"),
    ("card", "cards", "box", "boxes"),
    ("spoon", "spoons", "basket", "baskets"),
    ("phone", "phones", "desk", "desks"),
    ("ring", "rings", "case", "cases"),
    ("apple", "apples", "bowl", "bowls"),
    ("note", "notes", "packet", "packets"),
    ("brush", "brushes", "bag", "bags"),
    ("clock", "clocks", "wall", "walls"),
    ("plate", "plates", "counter", "counters"),
    ("shoe", "shoes", "rack", "racks"),
    ("tool", "tools", "bench", "benches"),
    ("photo", "photos", "album", "albums"),
    ("label", "labels", "jar", "jars"),
    ("button", "buttons", "coat", "coats"),
    ("pencil", "pencils", "cup", "cups"),
    ("map", "maps", "cabinet", "cabinets"),
    ("recipe", "recipes", "book", "books"),
    ("blanket", "blankets", "chair", "chairs"),
    ("report", "reports", "binder", "binders"),
    ("candle", "candles", "table", "tables"),
    ("poster", "posters", "door", "doors"),
    ("badge", "badges", "uniform", "uniforms"),
    ("folder", "folders", "shelf", "shelves"),
    ("stamp", "stamps", "envelope", "envelopes"),
    ("marker", "markers", "board", "boards"),
    ("cable", "cables", "device", "devices"),
    ("packet", "packets", "crate", "crates"),
    ("mirror", "mirrors", "room", "rooms"),
    ("towel", "towels", "basket", "baskets"),
    ("helmet", "helmets", "locker", "lockers"),
    ("parcel", "parcels", "cart", "carts"),
)


@dataclass(frozen=True)
class Example:
    example_id: str
    family: int
    split: str
    subject_plural: int
    distractor_plural: int
    surface: int
    prompt: str
    correct: str
    incorrect: str


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def split_for(family: int) -> str:
    if family in FIT_FAMILIES:
        return "fit"
    if family in TUNE_FAMILIES:
        return "tune"
    return "assessment"


def build_corpus() -> list[Example]:
    examples: list[Example] = []
    for family, (ss, sp, ds, dp) in enumerate(NOUNS):
        for subject_plural in (0, 1):
            for distractor_plural in (0, 1):
                for surface in (0, 1):
                    subject = sp if subject_plural else ss
                    distractor = dp if distractor_plural else ds
                    relation = "near" if surface == 0 else "beside"
                    prompt = (
                        "Complete the sentence with is or are. "
                        f"The {subject} {relation} the {distractor}"
                    )
                    correct = " are" if subject_plural else " is"
                    incorrect = " is" if subject_plural else " are"
                    examples.append(
                        Example(
                            f"lm-agreement-v17-{family:03d}-"
                            f"s{subject_plural}d{distractor_plural}v{surface}",
                            family,
                            split_for(family),
                            subject_plural,
                            distractor_plural,
                            surface,
                            prompt,
                            correct,
                            incorrect,
                        )
                    )
    assert len(examples) == 320
    return examples


class QwenRunner:
    def __init__(self, model_path: Path = MODEL_PATH):
        self.model_path = model_path
        self.model, self.tokenizer = load(str(model_path))
        self.layers = self.model.model.layers
        if len(self.layers) != 24 or self.model.args.hidden_size != 896:
            raise RuntimeError("NotRunModelRevisionMismatch")

    def token_id(self, completion: str) -> int:
        ids = self.tokenizer.encode(completion, add_special_tokens=False)
        if len(ids) != 1:
            raise RuntimeError(f"NotRunCompletionNotSingleToken:{completion!r}:{ids}")
        return ids[0]

    def forward(
        self,
        prompt: str,
        patch_site: int | None = None,
        replacement: np.ndarray | None = None,
        capture: bool = False,
    ) -> tuple[np.ndarray, dict[int, np.ndarray]]:
        ids = mx.array([self.tokenizer.encode(prompt, add_special_tokens=False)])
        h = self.model.model.embed_tokens(ids)
        mask = create_attention_mask(h, None)
        captured: dict[int, np.ndarray] = {}
        for index, layer in enumerate(self.layers):
            h = layer(h, mask, None)
            if index == patch_site:
                if replacement is None or replacement.shape != (896,):
                    raise ValueError("replacement must have shape (896,)")
                replacement_row = mx.array(replacement)[None, None, :]
                h = mx.concatenate([h[:, :-1, :], replacement_row], axis=1)
            if capture and index in SITES:
                mx.eval(h)
                # Preserve the model's float16 residual exactly across the
                # capture/replacement boundary; later statistics upcast.
                captured[index] = np.asarray(h[0, -1, :], dtype=np.float16)
        h = self.model.model.norm(h)
        logits = (
            self.model.model.embed_tokens.as_linear(h)
            if self.model.args.tie_word_embeddings
            else self.model.lm_head(h)
        )
        mx.eval(logits)
        return np.asarray(logits[0, -1, :], dtype=np.float32), captured


def model_inventory(model_path: Path) -> dict[str, Any]:
    files = []
    for path in sorted(p for p in model_path.rglob("*") if p.is_file()):
        files.append(
            {
                "path": str(path.relative_to(model_path)),
                "bytes": path.stat().st_size,
                "sha256": digest_file(path),
            }
        )
    config = json.loads((model_path / "config.json").read_text())
    return {
        "path": str(model_path),
        "files": files,
        "config": config,
        "precision": "local 4-bit conversion",
        "backend": "mlx",
    }


def qualify(runner: QwenRunner, examples: list[Example]) -> tuple[dict[str, Any], dict[str, Any]]:
    is_id, are_id = runner.token_id(" is"), runner.token_id(" are")
    rows: dict[str, Any] = {}
    parity_errors: list[float] = []
    repeat_errors: list[float] = []
    no_op_errors: list[float] = []
    started = time.time()
    for i, ex in enumerate(examples):
        logits, captures = runner.forward(ex.prompt, capture=True)
        correct_id = are_id if ex.subject_plural else is_id
        incorrect_id = is_id if ex.subject_plural else are_id
        row = {
            "clean_correct": float(logits[correct_id]),
            "clean_incorrect": float(logits[incorrect_id]),
            "margin": float(logits[correct_id] - logits[incorrect_id]),
            "correct": bool(logits[correct_id] > logits[incorrect_id]),
            "telemetry": np.concatenate([captures[s] for s in SITES]),
            "captures": captures,
        }
        rows[ex.example_id] = row
        if i < 4:
            native = np.asarray(
                runner.model(
                    mx.array(
                        [runner.tokenizer.encode(ex.prompt, add_special_tokens=False)]
                    )
                )[0, -1, :],
                dtype=np.float32,
            )
            parity_errors.append(float(np.max(np.abs(native - logits))))
            repeated, _ = runner.forward(ex.prompt)
            repeat_errors.append(float(np.max(np.abs(repeated - logits))))
            for site in SITES:
                no_op, _ = runner.forward(
                    ex.prompt, patch_site=site, replacement=captures[site]
                )
                no_op_errors.append(float(np.max(np.abs(no_op - logits))))
    metrics: dict[str, Any] = {}
    for split in ("fit", "tune", "assessment"):
        selected = [rows[x.example_id]["correct"] for x in examples if x.split == split]
        metrics[f"{split}_accuracy"] = float(np.mean(selected))
        metrics[f"{split}_count"] = len(selected)
    metrics.update(
        {
            "controlled_native_max_abs_error": max(parity_errors),
            "deterministic_repeat_max_abs_error": max(repeat_errors),
            "noop_replacement_max_abs_error": max(no_op_errors),
            "elapsed_seconds": time.time() - started,
            "max_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        }
    )
    if max(parity_errors) != 0.0:
        raise RuntimeError("NotRunControlledForwardParityFailure")
    if max(repeat_errors) != 0.0 or max(no_op_errors) != 0.0:
        raise RuntimeError("NotRunInterventionUnsupported")
    if (
        metrics["fit_accuracy"] < 0.70
        or metrics["tune_accuracy"] < 0.70
        or metrics["assessment_accuracy"] < 0.65
    ):
        raise RuntimeError("NotRunTaskQualificationFailure")
    return metrics, rows


def effect_rows(
    runner: QwenRunner,
    examples: list[Example],
    clean: dict[str, Any],
    means: dict[int, np.ndarray],
) -> np.ndarray:
    by_key = {
        (e.family, e.subject_plural, e.distractor_plural, e.surface): e
        for e in examples
    }
    targets = []
    for ex in examples:
        correct_id = runner.token_id(ex.correct)
        incorrect_id = runner.token_id(ex.incorrect)
        clean_margin = clean[ex.example_id]["margin"]
        effects = []
        for operator in ("mean", "patch"):
            for site in SITES:
                if operator == "mean":
                    replacement = means[site]
                else:
                    donor = by_key[
                        (ex.family, 1 - ex.subject_plural, ex.distractor_plural, ex.surface)
                    ]
                    replacement = clean[donor.example_id]["captures"][site]
                logits, _ = runner.forward(
                    ex.prompt, patch_site=site, replacement=replacement
                )
                margin = float(logits[correct_id] - logits[incorrect_id])
                effects.append(margin - clean_margin)
        targets.append(effects)
    return np.asarray(targets, dtype=np.float32)


def prefix(examples: list[Example], clean: dict[str, Any]) -> np.ndarray:
    rows = []
    for ex in examples:
        row = clean[ex.example_id]
        values = [
            ex.subject_plural,
            ex.distractor_plural,
            ex.surface,
            1 - ex.surface,
            row["clean_correct"],
            row["clean_incorrect"],
            row["margin"],
            int(row["margin"] > 0),
        ]
        rows.append(values + [0.0] * 8)
    return np.asarray(rows, dtype=np.float32)


def telemetry(examples: list[Example], clean: dict[str, Any]) -> np.ndarray:
    return np.stack([clean[e.example_id]["telemetry"] for e in examples])


def activation(examples: list[Example], clean: dict[str, Any]) -> np.ndarray:
    rows = []
    for ex in examples:
        values = []
        for site in SITES:
            x = clean[ex.example_id]["captures"][site].astype(np.float64)
            values += [np.linalg.norm(x), np.mean(x), np.std(x), np.max(np.abs(x))]
        rows.append(values + [0.0] * 52)
    return np.asarray(rows, dtype=np.float32)


def pca_fit(x: np.ndarray, components: int = 64) -> dict[str, np.ndarray]:
    mean = x.mean(axis=0, dtype=np.float64)
    centered = x.astype(np.float64) - mean
    _, singular, vt = np.linalg.svd(centered, full_matrices=False)
    basis = vt[:components].copy()
    for row in basis:
        pivot = int(np.argmax(np.abs(row)))
        if row[pivot] < 0:
            row *= -1
    variance = singular[:components] ** 2
    explained = variance / max(float(np.sum(singular**2)), np.finfo(float).eps)
    return {"mean": mean, "basis": basis, "explained": explained}


def pca_apply(x: np.ndarray, state: dict[str, np.ndarray]) -> np.ndarray:
    projected = (x.astype(np.float64) - state["mean"]) @ state["basis"].T
    if projected.shape[1] < 64:
        projected = np.pad(projected, ((0, 0), (0, 64 - projected.shape[1])))
    return projected[:, :64].astype(np.float32)


def standardize_fit(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = x.mean(axis=0, dtype=np.float64)
    scale = x.std(axis=0, dtype=np.float64)
    scale[scale < 1e-8] = 1.0
    return mean.astype(np.float32), scale.astype(np.float32)


class Predictor(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(80, 64),
            torch.nn.GELU(),
            torch.nn.Linear(64, 32),
            torch.nn.GELU(),
            torch.nn.Linear(32, 6),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def fit_predictor(
    x_fit: np.ndarray,
    y_fit: np.ndarray,
    x_tune: np.ndarray,
    y_tune: np.ndarray,
    seed: int,
) -> tuple[Predictor, dict[str, Any]]:
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    model = Predictor()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.001, weight_decay=0.0001)
    xf = torch.tensor(x_fit)
    yf = torch.tensor(y_fit)
    xt = torch.tensor(x_tune)
    yt = torch.tensor(y_tune)
    generator = torch.Generator().manual_seed(seed)
    best_loss, best_state, best_step = math.inf, None, 0
    for step in range(1, 501):
        order = torch.randperm(len(xf), generator=generator)
        for start in range(0, len(xf), 32):
            idx = order[start : start + 32]
            optimizer.zero_grad()
            loss = torch.mean((model(xf[idx]) - yf[idx]) ** 2)
            loss.backward()
            optimizer.step()
        if step % 25 == 0:
            with torch.no_grad():
                tune_loss = float(torch.mean((model(xt) - yt) ** 2))
            if tune_loss < best_loss:
                best_loss = tune_loss
                best_step = step
                best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    assert best_state is not None
    model.load_state_dict(best_state)
    return model, {"seed": seed, "best_step": best_step, "tune_mse": best_loss}


def shuffled_fit_telemetry(examples: list[Example], raw: np.ndarray) -> np.ndarray:
    result = raw.copy()
    fit_indices = [i for i, e in enumerate(examples) if e.split == "fit"]
    groups: dict[tuple[int, int], list[int]] = {}
    for i in fit_indices:
        groups.setdefault((examples[i].family, examples[i].subject_plural), []).append(i)
    rng = np.random.default_rng(1707)
    for indices in groups.values():
        donors = np.asarray(indices)[rng.permutation(len(indices))]
        result[indices] = raw[donors]
    return result


def mse_by_operator(pred: np.ndarray, actual: np.ndarray) -> dict[str, float]:
    return {
        "mean": float(np.mean((pred[:, :3] - actual[:, :3]) ** 2)),
        "patch": float(np.mean((pred[:, 3:] - actual[:, 3:]) ** 2)),
    }


def operator_diagnostics(
    pred: np.ndarray,
    actual: np.ndarray,
    activation_pred: np.ndarray,
) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {}
    rng = np.random.default_rng(20260804)
    for name, columns in (("mean", slice(0, 3)), ("patch", slice(3, 6))):
        p = pred[:, columns].astype(np.float64)
        y = actual[:, columns].astype(np.float64)
        a = activation_pred[:, columns].astype(np.float64)
        p_flat, y_flat = p.ravel(), y.ravel()
        correlation = (
            float(np.corrcoef(p_flat, y_flat)[0, 1])
            if np.std(p_flat) > 0 and np.std(y_flat) > 0
            else 0.0
        )
        design = np.column_stack([np.ones(len(p_flat)), p_flat])
        calibration = np.linalg.lstsq(design, y_flat, rcond=None)[0]
        family_diffs = []
        for family_offset in range(8):
            rows = slice(family_offset * 8, (family_offset + 1) * 8)
            family_diffs.append(
                float(np.mean((a[rows] - y[rows]) ** 2) - np.mean((p[rows] - y[rows]) ** 2))
            )
        draws = np.empty(10_000, dtype=np.float64)
        family_diffs_array = np.asarray(family_diffs)
        for draw in range(len(draws)):
            selected = rng.integers(0, 8, size=8)
            draws[draw] = float(np.mean(family_diffs_array[selected]))
        per_site_advantage = [
            1.0
            - float(np.mean((p[:, site] - y[:, site]) ** 2))
            / float(np.mean((a[:, site] - y[:, site]) ** 2))
            for site in range(3)
        ]
        diagnostics[name] = {
            "pearson": correlation,
            "calibration_intercept": float(calibration[0]),
            "calibration_slope": float(calibration[1]),
            "per_site_activation_advantage": per_site_advantage,
            "paired_family_bootstrap_difference_lower_95": float(
                np.quantile(draws, 0.025)
            ),
            "paired_family_bootstrap_difference_mean": float(np.mean(draws)),
        }
    return diagnostics


def run(output: Path) -> dict[str, Any]:
    if output.exists():
        raise RuntimeError("output root already exists")
    output.mkdir(parents=True)
    examples = build_corpus()
    corpus_value = [asdict(x) for x in examples]
    write_json(output / "prompt-families.json", corpus_value)
    runner = QwenRunner()
    inventory = model_inventory(MODEL_PATH)
    write_json(output / "model-inventory.json", inventory)
    qualification, clean = qualify(runner, examples)
    write_json(output / "qualification.json", qualification)

    fit_idx = np.array([i for i, e in enumerate(examples) if e.split == "fit"])
    tune_idx = np.array([i for i, e in enumerate(examples) if e.split == "tune"])
    assess_idx = np.array([i for i, e in enumerate(examples) if e.split == "assessment"])
    means = {
        site: np.mean(
            np.stack([clean[examples[i].example_id]["captures"][site] for i in fit_idx]),
            axis=0,
        )
        for site in SITES
    }
    y_fit_tune = effect_rows(
        runner, [examples[i] for i in np.concatenate([fit_idx, tune_idx])], clean, means
    )
    y_fit, y_tune = y_fit_tune[: len(fit_idx)], y_fit_tune[len(fit_idx) :]
    raw = telemetry(examples, clean)
    shuffled_raw = shuffled_fit_telemetry(examples, raw)
    pca = pca_fit(raw[fit_idx])
    shuffled_pca = pca_fit(shuffled_raw[fit_idx])
    fields = {
        "telemetry": pca_apply(raw, pca),
        "activation": activation(examples, clean),
        "text_io": np.zeros((len(examples), 64), dtype=np.float32),
        "shuffled": pca_apply(shuffled_raw, shuffled_pca),
    }
    shared = prefix(examples, clean)
    predictions: dict[str, np.ndarray] = {}
    training: dict[str, Any] = {}
    saved: dict[str, Any] = {}
    for method in METHODS:
        x = np.concatenate([shared, fields[method]], axis=1)
        mean, scale = standardize_fit(x[fit_idx])
        xz = (x - mean) / scale
        ensemble = []
        training[method] = []
        saved[method] = {"mean": mean.tolist(), "scale": scale.tolist(), "states": []}
        for seed in SEEDS:
            model, record = fit_predictor(
                xz[fit_idx], y_fit, xz[tune_idx], y_tune, seed
            )
            with torch.no_grad():
                ensemble.append(model(torch.tensor(xz[assess_idx])).numpy())
            training[method].append(record)
            saved[method]["states"].append(
                {k: v.numpy().tolist() for k, v in model.state_dict().items()}
            )
        predictions[method] = np.mean(ensemble, axis=0)
    predictions["constant"] = np.repeat(
        y_fit.mean(axis=0, keepdims=True), len(assess_idx), axis=0
    )
    ridge_x = np.concatenate([shared, fields["telemetry"]], axis=1)
    ridge_mean, ridge_scale = standardize_fit(ridge_x[fit_idx])
    ridge_fit = (ridge_x[fit_idx] - ridge_mean) / ridge_scale
    design = np.column_stack([np.ones(len(ridge_fit)), ridge_fit])
    penalty = np.eye(design.shape[1]) * 0.001
    penalty[0, 0] = 0
    weights = np.linalg.solve(design.T @ design + penalty, design.T @ y_fit)
    ridge_assess = (ridge_x[assess_idx] - ridge_mean) / ridge_scale
    predictions["linear_telemetry"] = np.column_stack(
        [np.ones(len(ridge_assess)), ridge_assess]
    ) @ weights

    np.savez_compressed(
        output / "fit-state.npz",
        fit_effects=y_fit,
        tune_effects=y_tune,
        pca_mean=pca["mean"],
        pca_basis=pca["basis"],
        pca_explained=pca["explained"],
        fit_means=np.stack([means[s] for s in SITES]),
    )
    write_json(output / "training-record.json", training)
    torch.save(saved, output / "explainer-checkpoints.pt")
    np.savez_compressed(
        output / "assessment-telemetry.npz",
        prefix=shared[assess_idx],
        telemetry=raw[assess_idx].astype(np.float16),
        activation=fields["activation"][assess_idx],
    )
    with (output / "assessment-predictions.jsonl").open("w") as handle:
        for local_i, global_i in enumerate(assess_idx):
            handle.write(
                json.dumps(
                    {
                        "example_id": examples[global_i].example_id,
                        "predictions": {
                            method: predictions[method][local_i].tolist()
                            for method in sorted(predictions)
                        },
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    lock_inputs = [
        "prompt-families.json",
        "model-inventory.json",
        "qualification.json",
        "fit-state.npz",
        "training-record.json",
        "explainer-checkpoints.pt",
        "assessment-telemetry.npz",
        "assessment-predictions.jsonl",
    ]
    lock = {
        "state_slice": "astral-lm-explainer-feasibility-and-prospective-pilot-v17",
        "branch": "SingleModelFeasibilityOnly",
        "sites": list(SITES),
        "operators": ["fit_mean_replace", "matched_subject_flip_patch"],
        "assessment_effects_absent": not (output / "assessment-effects.npz").exists(),
        "inputs": {name: digest_file(output / name) for name in lock_inputs},
        "prediction_count": int(len(assess_idx) * len(predictions) * 6),
    }
    write_json(output / "prediction-lock.json", lock)
    lock_digest = digest_file(output / "prediction-lock.json")

    y_assess = effect_rows(
        runner, [examples[i] for i in assess_idx], clean, means
    )
    np.savez_compressed(output / "assessment-effects.npz", effects=y_assess)
    metrics = {
        method: mse_by_operator(value, y_assess)
        for method, value in predictions.items()
    }
    advantages = {
        operator: 1.0
        - metrics["telemetry"][operator] / metrics["activation"][operator]
        for operator in ("mean", "patch")
    }
    diagnostics = operator_diagnostics(
        predictions["telemetry"], y_assess, predictions["activation"]
    )
    full_gate = all(
        advantages[o] >= 0.10
        and diagnostics[o]["paired_family_bootstrap_difference_lower_95"] > 0
        and diagnostics[o]["pearson"] > 0
        and 0.5 <= diagnostics[o]["calibration_slope"] <= 1.5
        and all(x > 0 for x in diagnostics[o]["per_site_activation_advantage"])
        for o in ("mean", "patch")
    ) and all(
        metrics["telemetry"][o] < metrics[m][o]
        for o in ("mean", "patch")
        for m in ("text_io", "shuffled", "constant")
    )
    classification = (
        "SingleModelTelemetryFeasibilityObserved"
        if full_gate
        else "SingleModelFeasibilityNoCandidate"
    )
    result = {
        "state_slice": "astral-lm-explainer-feasibility-and-prospective-pilot-v17",
        "classification": classification,
        "confirmation": "NotAuthorized",
        "stage_1": "BlockedByStage0C",
        "claim_ceiling": MODEL_CLAIM,
        "prediction_lock_sha256": lock_digest,
        "metrics": metrics,
        "telemetry_activation_advantage": advantages,
        "telemetry_diagnostics": diagnostics,
    }
    write_json(output / "result.json", result)
    manifest_files = sorted(p for p in output.iterdir() if p.name != "manifest.json")
    manifest = {
        "files": {p.name: digest_file(p) for p in manifest_files},
        "prediction_lock_sha256": lock_digest,
    }
    write_json(output / "manifest.json", manifest)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        result = run(args.output.resolve())
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
