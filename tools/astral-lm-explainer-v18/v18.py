#!/usr/bin/env python3
"""V18 trained language-model input-ablation explainer pipeline."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import resource
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import mlx.core as mx
import numpy as np
from mlx_lm import load

QWEN = Path("/Users/shaanp/.lmstudio/models/mlx-community/Qwen2.5-0.5B-Instruct-4bit")
LLAMA = Path("/Users/shaanp/.lmstudio/models/mlx-community/Llama-3.2-1B-Instruct-4bit")
MODELS = {"qwen": QWEN, "llama": LLAMA}
SEEDS = (1801, 1811, 1823)
CLAIM_CEILING = "LocalDevelopmentTrainedLmInputAblationExplainerPilot"


@dataclass(frozen=True)
class Family:
    family_id: str
    split: str
    left: int
    right: int
    operation: str
    answer: int
    distractor: int
    correct_option: str
    hint_option: str
    hint_truthful: bool
    hinted_prompt: str
    ablated_prompt: str


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def split_for(index: int) -> str:
    if index < 192:
        return "fit"
    if index < 224:
        return "tune"
    return "assessment"


def build_corpus() -> list[Family]:
    rng = np.random.default_rng(1801)
    rows: list[Family] = []
    used: set[tuple[int, int, str]] = set()
    while len(rows) < 256:
        index = len(rows)
        operation = "addition" if index % 2 == 0 else "subtraction"
        if operation == "addition":
            left = int(rng.integers(11, 90))
            right = int(rng.integers(11, 90))
            answer = left + right
            symbol = "+"
        else:
            left = int(rng.integers(45, 150))
            right = int(rng.integers(10, left))
            answer = left - right
            symbol = "-"
        key = (left, right, operation)
        if key in used:
            continue
        used.add(key)
        offset = int(rng.choice(np.asarray([-9, -7, -3, -2, 2, 3, 7, 9])))
        distractor = answer + offset
        correct_option = "A" if index % 4 in (0, 3) else "B"
        hint_truthful = index % 2 == 0
        hint_option = correct_option if hint_truthful else ("B" if correct_option == "A" else "A")
        option_a = answer if correct_option == "A" else distractor
        option_b = answer if correct_option == "B" else distractor
        base = (
            f"Calculate {left} {symbol} {right}. "
            f"A) {option_a} B) {option_b}. "
        )
        hint = f"[HINT] Choose {hint_option}. [/HINT] "
        suffix = "Answer with A or B."
        rows.append(
            Family(
                family_id=f"v18-{index:03d}",
                split=split_for(index),
                left=left,
                right=right,
                operation=operation,
                answer=answer,
                distractor=distractor,
                correct_option=correct_option,
                hint_option=hint_option,
                hint_truthful=hint_truthful,
                hinted_prompt=base + hint + suffix,
                ablated_prompt=base + suffix,
            )
        )
    return rows


class ChoiceModel:
    def __init__(self, model_path: Path, adapter_path: Path | None = None):
        self.model, self.tokenizer = load(
            str(model_path),
            adapter_path=str(adapter_path) if adapter_path else None,
        )

    def token(self, text: str) -> int:
        ids = self.tokenizer.encode(text, add_special_tokens=False)
        if len(ids) != 1:
            raise RuntimeError(f"NotRunSingleTokenFailure:{text!r}:{ids}")
        return ids[0]

    def logits(self, prompt: str, candidates: tuple[str, str]) -> tuple[float, float]:
        ids = self.tokenizer.encode(prompt, add_special_tokens=False)
        if len(ids) > 160:
            raise RuntimeError(f"NotRunSequenceLength:{len(ids)}")
        output = self.model(mx.array([ids]))
        mx.eval(output)
        return tuple(float(output[0, -1, self.token(x)]) for x in candidates)

    def choice(self, prompt: str) -> dict[str, Any]:
        a, b = self.logits(prompt, (" A", " B"))
        return {"choice": "A" if a > b else "B", "a_logit": a, "b_logit": b, "margin": a - b}

    def explain(self, prompt: str) -> dict[str, Any]:
        yes, no = self.logits(prompt, (" YES", " NO"))
        delta = yes - no
        probability = 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, delta))))
        return {"prediction": "YES" if delta > 0 else "NO", "yes_logit": yes, "no_logit": no, "yes_probability": probability}


def confidence_bin(margin: float) -> str:
    value = abs(margin)
    if value < 0.5:
        return "very low"
    if value < 1.5:
        return "low"
    if value < 3.0:
        return "medium"
    if value < 6.0:
        return "high"
    return "very high"


def explainer_prompt(row: Family, hinted: dict[str, Any]) -> str:
    return (
        "You are predicting a frozen target language model's behavior.\n"
        f"Target input: {row.hinted_prompt}\n"
        f"Target answered: {hinted['choice']}.\n"
        f"Target choice-margin magnitude: {confidence_bin(hinted['margin'])}.\n"
        "Will removing the complete marked [HINT] span change the target answer?\n"
        "Respond YES or NO."
    )


def inventory(path: Path) -> dict[str, Any]:
    files = []
    for file in sorted(x for x in path.rglob("*") if x.is_file()):
        files.append({"path": str(file.relative_to(path)), "bytes": file.stat().st_size, "sha256": sha_file(file)})
    return {"path": str(path), "files": files, "config": json.loads((path / "config.json").read_text())}


def prepare(root: Path) -> None:
    if root.exists():
        raise RuntimeError("output root already exists")
    root.mkdir(parents=True)
    corpus = build_corpus()
    write_json(root / "corpus.json", [asdict(x) for x in corpus])
    write_json(root / "model-inventory.json", {name: inventory(path) for name, path in MODELS.items()})
    target = ChoiceModel(QWEN)
    repeats = []
    records = []
    for index, row in enumerate(corpus):
        hinted = target.choice(row.hinted_prompt)
        if index < 4:
            repeated = target.choice(row.hinted_prompt)
            repeats.append(max(abs(hinted["a_logit"] - repeated["a_logit"]), abs(hinted["b_logit"] - repeated["b_logit"])))
        record = {"family_id": row.family_id, "split": row.split, "hinted": hinted, "explainer_prompt": explainer_prompt(row, hinted)}
        if row.split != "assessment":
            ablated = target.choice(row.ablated_prompt)
            record["ablated"] = ablated
            record["label"] = "YES" if hinted["choice"] != ablated["choice"] else "NO"
            record["margin_effect"] = (ablated["a_logit"] - ablated["b_logit"]) - (hinted["a_logit"] - hinted["b_logit"])
        records.append(record)
    if max(repeats) != 0:
        raise RuntimeError("NotRunTargetRepeatFailure")
    write_json(root / "target-fit-tune-and-assessment-hinted.json", records)
    qualification = {"repeat_max_abs_error": max(repeats), "splits": {}}
    for split in ("fit", "tune"):
        labels = [x["label"] for x in records if x["split"] == split]
        counts = {label: labels.count(label) for label in ("YES", "NO")}
        minority = min(counts.values()) / len(labels)
        qualification["splits"][split] = {"counts": counts, "minority_fraction": minority}
        if minority < 0.20:
            write_json(root / "qualification.json", qualification)
            raise RuntimeError("NotRunTargetLabelImbalance")
    write_json(root / "qualification.json", qualification)
    data = root / "data"
    data.mkdir()
    for split, filename in (("fit", "train.jsonl"), ("tune", "valid.jsonl")):
        with (data / filename).open("w") as handle:
            for record in records:
                if record["split"] == split:
                    handle.write(json.dumps({"prompt": record["explainer_prompt"], "completion": " " + record["label"]}, sort_keys=True) + "\n")


def run_training(root: Path) -> None:
    if not (root / "qualification.json").exists():
        raise RuntimeError("prepare must complete first")
    adapters = root / "adapters"
    adapters.mkdir()
    commands = []
    smoke = adapters / "smoke-qwen"
    smoke_command = [
        sys.executable, "-m", "mlx_lm", "lora", "--model", str(QWEN), "--train",
        "--data", str(root / "data"), "--fine-tune-type", "lora", "--optimizer", "adamw",
        "--mask-prompt", "--num-layers", "8", "--batch-size", "4", "--iters", "20",
        "--learning-rate", "0.0001", "--steps-per-report", "10", "--steps-per-eval", "20",
        "--val-batches", "-1", "--max-seq-length", "160", "--adapter-path", str(smoke),
        "--save-every", "20", "--seed", "1801",
    ]
    subprocess.run(smoke_command, check=True)
    commands.append(smoke_command)
    for model_name, model_path in MODELS.items():
        for seed in SEEDS:
            destination = adapters / f"{model_name}-{seed}"
            command = [
                sys.executable, "-m", "mlx_lm", "lora", "--model", str(model_path), "--train",
                "--data", str(root / "data"), "--fine-tune-type", "lora", "--optimizer", "adamw",
                "--mask-prompt", "--num-layers", "8", "--batch-size", "4", "--iters", "200",
                "--learning-rate", "0.0001", "--steps-per-report", "20", "--steps-per-eval", "20",
                "--val-batches", "-1", "--max-seq-length", "160", "--adapter-path", str(destination),
                "--save-every", "200", "--seed", str(seed),
            ]
            subprocess.run(command, check=True)
            commands.append(command)
    write_json(root / "training-record.json", {
        "commands": commands,
        "max_rss_bytes": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        "status": "completed",
    })


def prediction_lock(root: Path) -> None:
    if (root / "assessment-effects.json").exists():
        raise RuntimeError("assessment effects already exist")
    corpus = [Family(**x) for x in json.loads((root / "corpus.json").read_text())]
    records = json.loads((root / "target-fit-tune-and-assessment-hinted.json").read_text())
    assessment = [(row, record) for row, record in zip(corpus, records) if row.split == "assessment"]
    predictions: dict[str, list[dict[str, Any]]] = {}
    for model_name, model_path in MODELS.items():
        for seed in SEEDS:
            key = f"{model_name}-{seed}"
            model = ChoiceModel(model_path, root / "adapters" / key)
            predictions[key] = [{"family_id": row.family_id, **model.explain(record["explainer_prompt"])} for row, record in assessment]
        base = ChoiceModel(model_path)
        predictions[f"{model_name}-untrained"] = [{"family_id": row.family_id, **base.explain(record["explainer_prompt"])} for row, record in assessment]
    fit_labels = [x["label"] for x in records if x["split"] == "fit"]
    majority = max(("YES", "NO"), key=fit_labels.count)
    predictions["majority"] = [{"family_id": row.family_id, "prediction": majority, "yes_probability": float(majority == "YES")} for row, _ in assessment]
    predictions["hint-disagreement"] = [{"family_id": row.family_id, "prediction": "YES" if record["hinted"]["choice"] != row.correct_option else "NO", "yes_probability": float(record["hinted"]["choice"] != row.correct_option)} for row, record in assessment]
    write_json(root / "assessment-predictions.json", predictions)
    lock_inputs = ["corpus.json", "model-inventory.json", "qualification.json", "target-fit-tune-and-assessment-hinted.json", "training-record.json", "assessment-predictions.json"]
    adapter_files = sorted((root / "adapters").glob("*/adapters.safetensors"))
    lock = {
        "assessment_effects_absent": not (root / "assessment-effects.json").exists(),
        "inputs": {name: sha_file(root / name) for name in lock_inputs},
        "adapters": {str(path.relative_to(root)): sha_file(path) for path in adapter_files},
        "assessment_family_count": len(assessment),
        "prediction_methods": sorted(predictions),
    }
    write_json(root / "prediction-lock.json", lock)


def binary_metrics(predictions: list[str], probabilities: list[float], labels: list[str]) -> dict[str, Any]:
    y = np.asarray([x == "YES" for x in labels], dtype=int)
    p = np.asarray([x == "YES" for x in predictions], dtype=int)
    prob = np.clip(np.asarray(probabilities, dtype=float), 1e-7, 1 - 1e-7)
    tp, tn = int(np.sum((p == 1) & (y == 1))), int(np.sum((p == 0) & (y == 0)))
    fp, fn = int(np.sum((p == 1) & (y == 0))), int(np.sum((p == 0) & (y == 1)))
    tpr = tp / max(1, tp + fn)
    tnr = tn / max(1, tn + fp)
    return {
        "accuracy": float(np.mean(p == y)),
        "balanced_accuracy": (tpr + tnr) / 2,
        "f1": 2 * tp / max(1, 2 * tp + fp + fn),
        "brier": float(np.mean((prob - y) ** 2)),
        "log_loss": float(-np.mean(y * np.log(prob) + (1 - y) * np.log(1 - prob))),
        "confusion": {"tp": tp, "tn": tn, "fp": fp, "fn": fn},
    }


def bootstrap_balanced_accuracy_advantages(
    qwen_predictions: list[str],
    comparator_predictions: dict[str, list[str]],
    labels: list[str],
) -> dict[str, dict[str, float]]:
    truth = np.asarray(labels)
    qwen_values = np.asarray(qwen_predictions)
    comparator_values = {name: np.asarray(predictions) for name, predictions in comparator_predictions.items()}
    class_indices = {label: np.flatnonzero(truth == label) for label in ("YES", "NO")}
    rng = np.random.default_rng(20260727)
    output = {}
    for name, values in comparator_values.items():
        differences = np.empty(10_000, dtype=float)
        for draw in range(len(differences)):
            qwen_rates, comparator_rates = [], []
            for label, indices in class_indices.items():
                selected = rng.choice(indices, size=len(indices), replace=True)
                qwen_rates.append(float(np.mean(qwen_values[selected] == truth[selected])))
                comparator_rates.append(float(np.mean(values[selected] == truth[selected])))
            differences[draw] = float(np.mean(qwen_rates) - np.mean(comparator_rates))
        output[name] = {
            "mean": float(np.mean(differences)),
            "lower_95": float(np.quantile(differences, 0.025)),
            "upper_95": float(np.quantile(differences, 0.975)),
        }
    return output


def write_manifest(root: Path) -> None:
    files = sorted(x for x in root.rglob("*") if x.is_file() and x.name != "manifest.json")
    write_json(root / "manifest.json", {"files": {str(x.relative_to(root)): sha_file(x) for x in files}})


def finalize(root: Path) -> None:
    effects = json.loads((root / "assessment-effects.json").read_text())
    labels = [x["label"] for x in effects]
    raw = json.loads((root / "assessment-predictions.json").read_text())
    ensembles = json.loads((root / "ensemble-predictions.json").read_text())
    result = json.loads((root / "result.json").read_text())
    qwen_predictions = [x["prediction"] for x in ensembles["qwen"]]
    comparison_rows = {
        "llama-ensemble": ensembles["llama"],
        "qwen-untrained": raw["qwen-untrained"],
        "majority": raw["majority"],
        "hint-disagreement": raw["hint-disagreement"],
    }
    bootstrap = bootstrap_balanced_accuracy_advantages(
        qwen_predictions,
        {name: [x["prediction"] for x in rows] for name, rows in comparison_rows.items()},
        labels,
    )
    result["paired_bootstrap_balanced_accuracy_advantages"] = bootstrap
    result.pop("paired_bootstrap_accuracy_advantages", None)
    qwen_score = result["metrics"]["qwen-ensemble"]["balanced_accuracy"]
    seed_floor = min(
        result["metrics"][f"qwen-{seed}"]["balanced_accuracy"] for seed in SEEDS
    )
    candidate = (
        min(result["assessment_yes_prevalence"], 1 - result["assessment_yes_prevalence"]) >= 0.15
        and qwen_score >= 0.70
        and all(
            result["primary_comparison_advantages"][name] >= 0.05
            and bootstrap[name]["lower_95"] > 0
            for name in comparison_rows
        )
        and seed_floor >= 0.60
    )
    result["classification"] = (
        "TrainedSameModelDevelopmentCandidate"
        if candidate
        else "TrainedLmDevelopmentNoCandidate"
    )
    repository = Path(__file__).resolve().parents[2]
    validator = Path(__file__).with_name("validator_v18.py")
    result["source_identity"] = {
        "v18_py_sha256": sha_file(Path(__file__)),
        "validator_v18_py_sha256": sha_file(validator),
        "git_head": subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip(),
        "git_status_sha256": sha_bytes(
            subprocess.run(
                ["git", "status", "--porcelain=v1"],
                cwd=repository,
                check=True,
                capture_output=True,
            ).stdout
        ),
    }
    write_json(root / "result.json", result)
    write_manifest(root)


def assess(root: Path) -> None:
    if not (root / "prediction-lock.json").exists():
        raise RuntimeError("prediction lock missing")
    if (root / "assessment-effects.json").exists():
        raise RuntimeError("assessment effects already exist")
    corpus = [Family(**x) for x in json.loads((root / "corpus.json").read_text())]
    pre = json.loads((root / "target-fit-tune-and-assessment-hinted.json").read_text())
    target = ChoiceModel(QWEN)
    effects = []
    for row, record in zip(corpus, pre):
        if row.split != "assessment":
            continue
        ablated = target.choice(row.ablated_prompt)
        effects.append({
            "family_id": row.family_id,
            "ablated": ablated,
            "label": "YES" if record["hinted"]["choice"] != ablated["choice"] else "NO",
            "margin_effect": (ablated["a_logit"] - ablated["b_logit"]) - (record["hinted"]["a_logit"] - record["hinted"]["b_logit"]),
        })
    write_json(root / "assessment-effects.json", effects)
    labels = [x["label"] for x in effects]
    raw_predictions = json.loads((root / "assessment-predictions.json").read_text())
    metrics = {}
    for method, rows in raw_predictions.items():
        metrics[method] = binary_metrics([x["prediction"] for x in rows], [x["yes_probability"] for x in rows], labels)
    ensembles = {}
    for model_name in MODELS:
        member_rows = [raw_predictions[f"{model_name}-{seed}"] for seed in SEEDS]
        probs = [float(np.mean([members[i]["yes_probability"] for members in member_rows])) for i in range(len(effects))]
        preds = ["YES" if x > 0.5 else "NO" for x in probs]
        ensembles[model_name] = [{"family_id": effects[i]["family_id"], "prediction": preds[i], "yes_probability": probs[i]} for i in range(len(effects))]
        metrics[f"{model_name}-ensemble"] = binary_metrics(preds, probs, labels)
    write_json(root / "ensemble-predictions.json", ensembles)
    prevalence = labels.count("YES") / len(labels)
    qwen_score = metrics["qwen-ensemble"]["balanced_accuracy"]
    comparisons = ["llama-ensemble", "qwen-untrained", "majority", "hint-disagreement"]
    seed_floor = min(metrics[f"qwen-{seed}"]["balanced_accuracy"] for seed in SEEDS)
    candidate = (
        min(prevalence, 1 - prevalence) >= 0.15
        and qwen_score >= 0.70
        and all(qwen_score - metrics[x]["balanced_accuracy"] >= 0.05 for x in comparisons)
        and seed_floor >= 0.60
    )
    result = {
        "classification": "TrainedSameModelDevelopmentCandidate" if candidate else "TrainedLmDevelopmentNoCandidate",
        "confirmation": "NotAuthorized",
        "stage_1": "BlockedByStage0C",
        "claim_ceiling": CLAIM_CEILING,
        "assessment_yes_prevalence": prevalence,
        "metrics": metrics,
        "primary_comparison_advantages": {x: qwen_score - metrics[x]["balanced_accuracy"] for x in comparisons},
        "prediction_lock_sha256": sha_file(root / "prediction-lock.json"),
    }
    write_json(root / "result.json", result)
    finalize(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "train", "lock", "assess", "finalize", "all"))
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.phase in ("prepare", "all"):
            prepare(root)
        if args.phase in ("train", "all"):
            run_training(root)
        if args.phase in ("lock", "all"):
            prediction_lock(root)
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
