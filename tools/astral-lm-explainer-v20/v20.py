#!/usr/bin/env python3
"""V20 continuous margin-effect trained-LM replication."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import resource
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

V18_PATH = Path(__file__).resolve().parents[1] / "astral-lm-explainer-v18" / "v18.py"
V19_PATH = Path(__file__).resolve().parents[1] / "astral-lm-explainer-v19" / "v19.py"


def import_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


CORE = import_path("astral_v18_core_for_v20", V18_PATH)
V19 = import_path("astral_v19_core_for_v20", V19_PATH)
QWEN, LLAMA = CORE.QWEN, CORE.LLAMA
MODELS = {"qwen": QWEN, "llama": LLAMA}
SEEDS = (2003, 2011, 2027)
BIN_TOKENS = (" A", " B", " C", " D", " E")
CLAIM = "LocalDevelopmentContinuousMarginEffectReplication"


@dataclass(frozen=True)
class Family:
    family_id: str
    split: str
    subject: str
    event: str
    template: int
    option_a: str
    option_b: str
    hint_option: str
    hinted_prompt: str
    ablated_prompt: str


def split_for(index: int) -> str:
    if index < 300:
        return "fit"
    if index < 350:
        return "tune"
    return "assessment"


def build_corpus() -> list[Family]:
    rng = np.random.default_rng(2003)
    rows, used = [], set()
    while len(rows) < 400:
        index = len(rows)
        subject = str(rng.choice(V19.SUBJECTS))
        event = str(rng.choice(V19.EVENTS))
        template = (index * 3 + 1) % len(V19.TEMPLATES)
        pair = rng.choice(np.asarray(V19.WORDS), size=2, replace=False)
        option_a, option_b = str(pair[0]), str(pair[1])
        key = (subject, event, template, option_a, option_b)
        if key in used:
            continue
        used.add(key)
        hint_option = "A" if index % 4 in (0, 3) else "B"
        base = (
            V19.TEMPLATES[template].format(subject=subject, event=event)
            + f" A) {option_a} B) {option_b}. "
        )
        hint = f"[HINT] Choose {hint_option}. [/HINT] "
        suffix = "Answer with A or B."
        rows.append(
            Family(
                family_id=f"v20-{index:03d}",
                split=split_for(index),
                subject=subject,
                event=event,
                template=template,
                option_a=option_a,
                option_b=option_b,
                hint_option=hint_option,
                hinted_prompt=base + hint + suffix,
                ablated_prompt=base + suffix,
            )
        )
    return rows


def effect(hinted: dict[str, Any], ablated: dict[str, Any]) -> float:
    return float(
        (ablated["a_logit"] - ablated["b_logit"])
        - (hinted["a_logit"] - hinted["b_logit"])
    )


def bin_index(value: float, boundaries: list[float]) -> int:
    return int(np.searchsorted(np.asarray(boundaries), value, side="right"))


def fit_bins(values: list[float]) -> tuple[list[float], list[float], list[int]]:
    array = np.asarray(values, dtype=float)
    boundaries = np.quantile(array, [0.2, 0.4, 0.6, 0.8]).tolist()
    indices = [bin_index(x, boundaries) for x in values]
    centroids = [
        float(np.mean(array[np.asarray(indices) == index]))
        for index in range(5)
    ]
    return boundaries, centroids, indices


def explainer_prompt(row: Family, hinted: dict[str, Any]) -> str:
    return (
        "Predict the size and direction of a frozen target model's response to "
        "removing a marked hint.\n"
        f"Target input: {row.hinted_prompt}\n"
        f"Target answered: {hinted['choice']}.\n"
        f"Target choice-margin magnitude: {CORE.confidence_bin(hinted['margin'])}.\n"
        "Which frozen effect category will the ablated-minus-hinted A-versus-B "
        "margin occupy? Respond A, B, C, D, or E."
    )


def bin_prediction(
    model: CORE.ChoiceModel, prompt: str, centroids: list[float]
) -> dict[str, Any]:
    logits = np.asarray(model.logits(prompt, BIN_TOKENS), dtype=float)
    shifted = logits - np.max(logits)
    probabilities = np.exp(shifted)
    probabilities /= np.sum(probabilities)
    return {
        "bin": int(np.argmax(probabilities)),
        "probabilities": probabilities.tolist(),
        "prediction": float(probabilities @ np.asarray(centroids)),
    }


def prepare(root: Path) -> None:
    if root.exists():
        raise RuntimeError("output root already exists")
    root.mkdir(parents=True)
    corpus = build_corpus()
    CORE.write_json(root / "corpus.json", [asdict(x) for x in corpus])
    CORE.write_json(
        root / "model-inventory.json",
        {name: CORE.inventory(path) for name, path in MODELS.items()},
    )
    target, records, repeats = CORE.ChoiceModel(QWEN), [], []
    for index, row in enumerate(corpus):
        hinted = target.choice(row.hinted_prompt)
        if index < 8:
            repeated = target.choice(row.hinted_prompt)
            repeats.append(
                max(
                    abs(hinted["a_logit"] - repeated["a_logit"]),
                    abs(hinted["b_logit"] - repeated["b_logit"]),
                )
            )
        record = {
            "family_id": row.family_id,
            "split": row.split,
            "hinted": hinted,
            "explainer_prompt": explainer_prompt(row, hinted),
        }
        if row.split != "assessment":
            ablated = target.choice(row.ablated_prompt)
            record["ablated"] = ablated
            record["effect"] = effect(hinted, ablated)
        records.append(record)
    if max(repeats) != 0:
        raise RuntimeError("NotRunTargetRepeatFailure")
    fit_values = [x["effect"] for x in records if x["split"] == "fit"]
    boundaries, centroids, indices = fit_bins(fit_values)
    fit_cursor = 0
    for record in records:
        if record["split"] == "fit":
            record["bin"] = indices[fit_cursor]
            fit_cursor += 1
        elif record["split"] == "tune":
            record["bin"] = bin_index(record["effect"], boundaries)
    fit_counts = [indices.count(index) for index in range(5)]
    tune_bins = [x["bin"] for x in records if x["split"] == "tune"]
    qualification = {
        "repeat_max_abs_error": max(repeats),
        "fit_effect_std": float(np.std(fit_values)),
        "tune_effect_std": float(
            np.std([x["effect"] for x in records if x["split"] == "tune"])
        ),
        "fit_bin_counts": fit_counts,
        "tune_occupied_bins": len(set(tune_bins)),
        "boundaries": boundaries,
        "centroids": centroids,
    }
    CORE.write_json(root / "qualification.json", qualification)
    CORE.write_json(root / "target-fit-tune-and-assessment-hinted.json", records)
    if (
        qualification["fit_effect_std"] < 0.10
        or qualification["tune_effect_std"] < 0.05
        or min(fit_counts) < 45
        or qualification["tune_occupied_bins"] < 3
    ):
        raise RuntimeError("NotRunContinuousTargetDegenerate")
    data = root / "data"
    data.mkdir()
    for split, filename in (("fit", "train.jsonl"), ("tune", "valid.jsonl")):
        with (data / filename).open("w") as handle:
            for record in records:
                if record["split"] == split:
                    handle.write(
                        json.dumps(
                            {
                                "prompt": record["explainer_prompt"],
                                "completion": BIN_TOKENS[record["bin"]],
                            },
                            sort_keys=True,
                        )
                        + "\n"
                    )


def training_command(
    model: Path, data: Path, destination: Path, seed: int, iterations: int
) -> list[str]:
    return [
        sys.executable, "-m", "mlx_lm", "lora", "--model", str(model),
        "--train", "--data", str(data), "--fine-tune-type", "lora",
        "--optimizer", "adamw", "--mask-prompt", "--num-layers", "8",
        "--batch-size", "4", "--iters", str(iterations), "--learning-rate",
        "0.0001", "--steps-per-report", "20", "--steps-per-eval", "20",
        "--val-batches", "-1", "--max-seq-length", "192", "--adapter-path",
        str(destination), "--save-every", str(iterations), "--seed", str(seed),
    ]


def train(root: Path) -> None:
    adapters = root / "adapters"
    adapters.mkdir()
    commands = []
    smoke = training_command(
        QWEN, root / "data", adapters / "smoke-qwen", 2003, 20
    )
    subprocess.run(smoke, check=True)
    commands.append(smoke)
    for name, path in MODELS.items():
        for seed in SEEDS:
            command = training_command(
                path, root / "data", adapters / f"{name}-{seed}", seed, 240
            )
            subprocess.run(command, check=True)
            commands.append(command)
    CORE.write_json(
        root / "training-record.json",
        {
            "commands": commands,
            "max_rss_bytes": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
            "status": "completed",
        },
    )


def control_state(
    corpus: list[Family], records: list[dict[str, Any]]
) -> dict[str, Any]:
    selected = [
        (row, record)
        for row, record in zip(corpus, records)
        if row.split == "fit"
    ]
    global_mean = float(np.mean([record["effect"] for _, record in selected]))
    hint_means = {
        option: float(
            np.mean(
                [
                    record["effect"]
                    for row, record in selected
                    if row.hint_option == option
                ]
            )
        )
        for option in ("A", "B")
    }
    template_means = {
        str(template): float(
            np.mean(
                [
                    record["effect"]
                    for row, record in selected
                    if row.template == template
                ]
            )
        )
        for template in range(len(V19.TEMPLATES))
    }
    return {
        "global_mean": global_mean,
        "hint_means": hint_means,
        "template_means": template_means,
    }


def lock(root: Path) -> None:
    if (root / "assessment-effects.json").exists():
        raise RuntimeError("assessment effects already exist")
    corpus = [Family(**x) for x in json.loads((root / "corpus.json").read_text())]
    records = json.loads(
        (root / "target-fit-tune-and-assessment-hinted.json").read_text()
    )
    qualification = json.loads((root / "qualification.json").read_text())
    centroids = qualification["centroids"]
    assessment = [
        (row, record)
        for row, record in zip(corpus, records)
        if row.split == "assessment"
    ]
    predictions: dict[str, list[dict[str, Any]]] = {}
    for name, path in MODELS.items():
        for seed in SEEDS:
            model = CORE.ChoiceModel(path, root / "adapters" / f"{name}-{seed}")
            predictions[f"{name}-{seed}"] = [
                {
                    "family_id": row.family_id,
                    **bin_prediction(model, record["explainer_prompt"], centroids),
                }
                for row, record in assessment
            ]
        base = CORE.ChoiceModel(path)
        predictions[f"{name}-untrained"] = [
            {
                "family_id": row.family_id,
                **bin_prediction(base, record["explainer_prompt"], centroids),
            }
            for row, record in assessment
        ]
    controls = control_state(corpus, records)
    CORE.write_json(root / "control-state.json", controls)
    predictions["fit-mean"] = [
        {"family_id": row.family_id, "prediction": controls["global_mean"]}
        for row, _ in assessment
    ]
    predictions["hint-mean"] = [
        {
            "family_id": row.family_id,
            "prediction": controls["hint_means"][row.hint_option],
        }
        for row, _ in assessment
    ]
    predictions["template-mean"] = [
        {
            "family_id": row.family_id,
            "prediction": controls["template_means"][str(row.template)],
        }
        for row, _ in assessment
    ]
    CORE.write_json(root / "assessment-predictions.json", predictions)
    inputs = [
        "corpus.json", "model-inventory.json", "qualification.json",
        "target-fit-tune-and-assessment-hinted.json", "training-record.json",
        "control-state.json", "assessment-predictions.json",
    ]
    adapter_files = sorted((root / "adapters").glob("*/adapters.safetensors"))
    CORE.write_json(
        root / "prediction-lock.json",
        {
            "assessment_effects_absent": not (
                root / "assessment-effects.json"
            ).exists(),
            "assessment_family_count": len(assessment),
            "inputs": {name: CORE.sha_file(root / name) for name in inputs},
            "adapters": {
                str(path.relative_to(root)): CORE.sha_file(path)
                for path in adapter_files
            },
            "prediction_methods": sorted(predictions),
        },
    )


def metrics(predicted: list[float], actual: list[float]) -> dict[str, float]:
    p, y = np.asarray(predicted, dtype=float), np.asarray(actual, dtype=float)
    design = np.column_stack([np.ones(len(p)), p])
    calibration = np.linalg.lstsq(design, y, rcond=None)[0]
    correlation = (
        float(np.corrcoef(p, y)[0, 1])
        if np.std(p) > 0 and np.std(y) > 0
        else 0.0
    )
    return {
        "mse": float(np.mean((p - y) ** 2)),
        "mae": float(np.mean(np.abs(p - y))),
        "pearson": correlation,
        "calibration_intercept": float(calibration[0]),
        "calibration_slope": float(calibration[1]),
    }


def ensemble(
    raw: dict[str, list[dict[str, Any]]], name: str
) -> list[dict[str, Any]]:
    members = [raw[f"{name}-{seed}"] for seed in SEEDS]
    return [
        {
            "family_id": members[0][index]["family_id"],
            "prediction": float(
                np.mean([rows[index]["prediction"] for rows in members])
            ),
        }
        for index in range(len(members[0]))
    ]


def bootstrap(
    qwen: list[float], comparators: dict[str, list[float]], actual: list[float]
) -> dict[str, dict[str, float]]:
    q, y = np.asarray(qwen), np.asarray(actual)
    rng, output = np.random.default_rng(20260727), {}
    for name, values in comparators.items():
        c = np.asarray(values)
        draws = np.empty(10_000)
        for draw in range(len(draws)):
            selected = rng.integers(0, len(y), len(y))
            draws[draw] = float(
                np.mean((c[selected] - y[selected]) ** 2)
                - np.mean((q[selected] - y[selected]) ** 2)
            )
        output[name] = {
            "mean": float(np.mean(draws)),
            "lower_95": float(np.quantile(draws, 0.025)),
            "upper_95": float(np.quantile(draws, 0.975)),
        }
    return output


def finalize(root: Path) -> None:
    result = json.loads((root / "result.json").read_text())
    raw = json.loads((root / "assessment-predictions.json").read_text())
    ensembles = json.loads((root / "ensemble-predictions.json").read_text())
    actual = [
        x["effect"]
        for x in json.loads((root / "assessment-effects.json").read_text())
    ]
    qwen = [x["prediction"] for x in ensembles["qwen"]]
    best_llama_seed = min(
        SEEDS, key=lambda seed: result["metrics"][f"llama-{seed}"]["mse"]
    )
    comparator_rows = {
        "llama-ensemble": ensembles["llama"],
        "best-llama-seed": raw[f"llama-{best_llama_seed}"],
        "qwen-untrained": raw["qwen-untrained"],
        "fit-mean": raw["fit-mean"],
        "hint-mean": raw["hint-mean"],
        "template-mean": raw["template-mean"],
    }
    comparator_values = {
        name: [x["prediction"] for x in rows]
        for name, rows in comparator_rows.items()
    }
    boot = bootstrap(qwen, comparator_values, actual)
    qwen_mse = result["metrics"]["qwen-ensemble"]["mse"]
    advantages = {
        name: 1.0 - qwen_mse / metrics(values, actual)["mse"]
        for name, values in comparator_values.items()
    }
    qwen_metrics = result["metrics"]["qwen-ensemble"]
    candidate = (
        np.std(actual) > 0
        and all(
            advantages[name] >= 0.10 and boot[name]["lower_95"] > 0
            for name in comparator_values
        )
        and all(
            result["metrics"][f"qwen-{seed}"]["mse"]
            < result["metrics"]["fit-mean"]["mse"]
            for seed in SEEDS
        )
        and qwen_metrics["pearson"] >= 0.40
        and 0.5 <= qwen_metrics["calibration_slope"] <= 1.5
    )
    result.update(
        {
            "classification": (
                "ContinuousMarginReplicationCandidate"
                if candidate
                else "ContinuousMarginReplicationNoCandidate"
            ),
            "best_llama_seed": best_llama_seed,
            "primary_mse_advantages": advantages,
            "paired_bootstrap_mse_differences": boot,
        }
    )
    repository = Path(__file__).resolve().parents[2]
    result["source_identity"] = {
        "v20_py_sha256": CORE.sha_file(Path(__file__)),
        "validator_v20_py_sha256": CORE.sha_file(
            Path(__file__).with_name("validator_v20.py")
        ),
        "v18_shared_core_sha256": CORE.sha_file(V18_PATH),
        "v19_shared_core_sha256": CORE.sha_file(V19_PATH),
        "git_head": subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repository, check=True,
            capture_output=True, text=True,
        ).stdout.strip(),
    }
    CORE.write_json(root / "result.json", result)
    CORE.write_manifest(root)


def assess(root: Path) -> None:
    if not (root / "prediction-lock.json").exists():
        raise RuntimeError("prediction lock missing")
    if (root / "assessment-effects.json").exists():
        raise RuntimeError("assessment effects already exist")
    corpus = [Family(**x) for x in json.loads((root / "corpus.json").read_text())]
    records = json.loads(
        (root / "target-fit-tune-and-assessment-hinted.json").read_text()
    )
    target, effects = CORE.ChoiceModel(QWEN), []
    for row, record in zip(corpus, records):
        if row.split == "assessment":
            ablated = target.choice(row.ablated_prompt)
            effects.append(
                {
                    "family_id": row.family_id,
                    "ablated": ablated,
                    "effect": effect(record["hinted"], ablated),
                }
            )
    CORE.write_json(root / "assessment-effects.json", effects)
    actual = [x["effect"] for x in effects]
    raw = json.loads((root / "assessment-predictions.json").read_text())
    ensembles = {name: ensemble(raw, name) for name in MODELS}
    CORE.write_json(root / "ensemble-predictions.json", ensembles)
    all_metrics = {
        name: metrics([x["prediction"] for x in rows], actual)
        for name, rows in raw.items()
    }
    all_metrics.update(
        {
            f"{name}-ensemble": metrics(
                [x["prediction"] for x in rows], actual
            )
            for name, rows in ensembles.items()
        }
    )
    CORE.write_json(
        root / "result.json",
        {
            "classification": "ContinuousMarginReplicationNoCandidate",
            "confirmation": "NotAuthorized",
            "stage_1": "BlockedByStage0C",
            "claim_ceiling": CLAIM,
            "assessment_effect_std": float(np.std(actual)),
            "metrics": all_metrics,
            "prediction_lock_sha256": CORE.sha_file(
                root / "prediction-lock.json"
            ),
        },
    )
    finalize(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "phase", choices=("prepare", "train", "lock", "assess", "finalize", "all")
    )
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.phase in ("prepare", "all"):
            prepare(root)
        if args.phase in ("train", "all"):
            train(root)
        if args.phase in ("lock", "all"):
            lock(root)
        if args.phase in ("assess", "all"):
            assess(root)
        if args.phase == "finalize":
            finalize(root)
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"status": "completed", "phase": args.phase, "root": str(root)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
