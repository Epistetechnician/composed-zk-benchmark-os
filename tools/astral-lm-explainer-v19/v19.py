#!/usr/bin/env python3
"""V19 opaque-preference trained-LM replication."""

from __future__ import annotations

import argparse
import importlib.util
import json
import resource
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

V18_PATH = Path(__file__).resolve().parents[1] / "astral-lm-explainer-v18" / "v18.py"
SPEC = importlib.util.spec_from_file_location("astral_v18_core", V18_PATH)
CORE = importlib.util.module_from_spec(SPEC)
sys.modules["astral_v18_core"] = CORE
assert SPEC.loader
SPEC.loader.exec_module(CORE)

QWEN = CORE.QWEN
LLAMA = CORE.LLAMA
MODELS = {"qwen": QWEN, "llama": LLAMA}
SEEDS = (1901, 1913, 1931)
CLAIM = "LocalDevelopmentOpaquePreferenceReplication"

SUBJECTS = (
    "traveler", "teacher", "musician", "engineer", "gardener", "writer",
    "doctor", "student", "pilot", "chef", "artist", "farmer", "scientist",
    "driver", "sailor", "dancer",
)
EVENTS = (
    "meeting", "journey", "storm", "performance", "inspection", "interview",
    "experiment", "celebration", "lesson", "competition", "repair", "delivery",
    "rehearsal", "discussion", "training", "ceremony",
)
WORDS = (
    "calm", "alert", "focused", "patient", "eager", "quiet", "careful",
    "curious", "steady", "hopeful", "ready", "serious", "thoughtful",
    "relaxed", "confident", "attentive", "gentle", "restless", "cheerful",
    "cautious", "precise", "grateful", "reserved", "determined", "observant",
    "energetic", "practical", "creative", "concerned", "surprised", "content",
    "uncertain",
)
TEMPLATES = (
    'Which continuation sounds more natural? "The {subject} seemed ___ after the {event}."',
    'Which word better completes the sentence? "During the {event}, the {subject} remained ___."',
    'Choose the more plausible continuation: "Before the {event}, the {subject} felt ___."',
    'Choose the preferred description: "Everyone found the {subject} unusually ___ during the {event}."',
)


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
    if index < 240:
        return "fit"
    if index < 280:
        return "tune"
    return "assessment"


def build_corpus() -> list[Family]:
    rng = np.random.default_rng(1901)
    rows: list[Family] = []
    used: set[tuple[str, str, int, str, str]] = set()
    while len(rows) < 320:
        index = len(rows)
        subject = str(rng.choice(SUBJECTS))
        event = str(rng.choice(EVENTS))
        template = index % len(TEMPLATES)
        pair = rng.choice(np.asarray(WORDS), size=2, replace=False)
        option_a, option_b = str(pair[0]), str(pair[1])
        key = (subject, event, template, option_a, option_b)
        if key in used:
            continue
        used.add(key)
        hint_option = "A" if (index * 7 + 3) % 4 in (0, 1) else "B"
        base = (
            TEMPLATES[template].format(subject=subject, event=event)
            + f" A) {option_a} B) {option_b}. "
        )
        hint = f"[HINT] Choose {hint_option}. [/HINT] "
        suffix = "Answer with A or B."
        rows.append(
            Family(
                family_id=f"v19-{index:03d}",
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


def explainer_prompt(row: Family, hinted: dict[str, Any]) -> str:
    return (
        "Predict a frozen target language model's behavior.\n"
        f"Target input: {row.hinted_prompt}\n"
        f"Target answered: {hinted['choice']}.\n"
        f"Target choice-margin magnitude: {CORE.confidence_bin(hinted['margin'])}.\n"
        "Will removing the complete marked [HINT] span change the target answer?\n"
        "Respond YES or NO."
    )


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
    target = CORE.ChoiceModel(QWEN)
    records, repeats = [], []
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
            record["label"] = (
                "YES" if hinted["choice"] != ablated["choice"] else "NO"
            )
            record["margin_effect"] = (
                ablated["a_logit"]
                - ablated["b_logit"]
                - hinted["a_logit"]
                + hinted["b_logit"]
            )
        records.append(record)
    if max(repeats) != 0:
        raise RuntimeError("NotRunTargetRepeatFailure")
    qualification = {"repeat_max_abs_error": max(repeats), "splits": {}}
    for split in ("fit", "tune"):
        selected = [
            (row, record)
            for row, record in zip(corpus, records)
            if row.split == split
        ]
        labels = [record["label"] for _, record in selected]
        counts = {label: labels.count(label) for label in ("YES", "NO")}
        hints = {
            option: sum(row.hint_option == option for row, _ in selected)
            for option in ("A", "B")
        }
        minority = min(counts.values()) / len(labels)
        qualification["splits"][split] = {
            "counts": counts,
            "hint_counts": hints,
            "minority_fraction": minority,
        }
        if minority < 0.20 or min(hints.values()) == 0:
            CORE.write_json(root / "qualification.json", qualification)
            raise RuntimeError("NotRunTargetLabelImbalance")
    CORE.write_json(
        root / "target-fit-tune-and-assessment-hinted.json", records
    )
    CORE.write_json(root / "qualification.json", qualification)
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
                                "completion": " " + record["label"],
                            },
                            sort_keys=True,
                        )
                        + "\n"
                    )


def training_command(
    model: Path, data: Path, destination: Path, seed: int, iterations: int
) -> list[str]:
    return [
        sys.executable,
        "-m",
        "mlx_lm",
        "lora",
        "--model",
        str(model),
        "--train",
        "--data",
        str(data),
        "--fine-tune-type",
        "lora",
        "--optimizer",
        "adamw",
        "--mask-prompt",
        "--num-layers",
        "8",
        "--batch-size",
        "4",
        "--iters",
        str(iterations),
        "--learning-rate",
        "0.0001",
        "--steps-per-report",
        "20",
        "--steps-per-eval",
        "20",
        "--val-batches",
        "-1",
        "--max-seq-length",
        "192",
        "--adapter-path",
        str(destination),
        "--save-every",
        str(iterations),
        "--seed",
        str(seed),
    ]


def train(root: Path) -> None:
    adapters = root / "adapters"
    adapters.mkdir()
    commands = []
    smoke = training_command(
        QWEN, root / "data", adapters / "smoke-qwen", 1901, 20
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


def hint_lookup(records: list[dict[str, Any]], corpus: list[Family]) -> dict[str, str]:
    labels = [x["label"] for x in records if x["split"] == "fit"]
    global_majority = max(("YES", "NO"), key=labels.count)
    output = {}
    for option in ("A", "B"):
        selected = [
            record["label"]
            for row, record in zip(corpus, records)
            if row.split == "fit" and row.hint_option == option
        ]
        yes, no = selected.count("YES"), selected.count("NO")
        output[option] = (
            "YES" if yes > no else "NO" if no > yes else global_majority
        )
    return output


def lock(root: Path) -> None:
    if (root / "assessment-effects.json").exists():
        raise RuntimeError("assessment effects already exist")
    corpus = [Family(**x) for x in json.loads((root / "corpus.json").read_text())]
    records = json.loads(
        (root / "target-fit-tune-and-assessment-hinted.json").read_text()
    )
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
                    **model.explain(record["explainer_prompt"]),
                }
                for row, record in assessment
            ]
        base = CORE.ChoiceModel(path)
        predictions[f"{name}-untrained"] = [
            {
                "family_id": row.family_id,
                **base.explain(record["explainer_prompt"]),
            }
            for row, record in assessment
        ]
    fit_labels = [x["label"] for x in records if x["split"] == "fit"]
    majority = max(("YES", "NO"), key=fit_labels.count)
    lookup = hint_lookup(records, corpus)
    predictions["majority"] = [
        {
            "family_id": row.family_id,
            "prediction": majority,
            "yes_probability": float(majority == "YES"),
        }
        for row, _ in assessment
    ]
    predictions["hint-option-lookup"] = [
        {
            "family_id": row.family_id,
            "prediction": lookup[row.hint_option],
            "yes_probability": float(lookup[row.hint_option] == "YES"),
        }
        for row, _ in assessment
    ]
    CORE.write_json(root / "assessment-predictions.json", predictions)
    input_names = [
        "corpus.json",
        "model-inventory.json",
        "qualification.json",
        "target-fit-tune-and-assessment-hinted.json",
        "training-record.json",
        "assessment-predictions.json",
    ]
    adapters = sorted((root / "adapters").glob("*/adapters.safetensors"))
    CORE.write_json(
        root / "prediction-lock.json",
        {
            "assessment_effects_absent": not (
                root / "assessment-effects.json"
            ).exists(),
            "inputs": {
                name: CORE.sha_file(root / name) for name in input_names
            },
            "adapters": {
                str(path.relative_to(root)): CORE.sha_file(path)
                for path in adapters
            },
            "assessment_family_count": len(assessment),
            "prediction_methods": sorted(predictions),
        },
    )


def majority_ensemble(
    raw: dict[str, list[dict[str, Any]]], name: str
) -> list[dict[str, Any]]:
    members = [raw[f"{name}-{seed}"] for seed in SEEDS]
    output = []
    for index in range(len(members[0])):
        votes = [rows[index]["prediction"] for rows in members]
        probabilities = [rows[index]["yes_probability"] for rows in members]
        prediction = "YES" if votes.count("YES") >= 2 else "NO"
        output.append(
            {
                "family_id": members[0][index]["family_id"],
                "prediction": prediction,
                "yes_probability": float(np.median(probabilities)),
            }
        )
    return output


def finalize(root: Path) -> None:
    result = json.loads((root / "result.json").read_text())
    effects = json.loads((root / "assessment-effects.json").read_text())
    labels = [x["label"] for x in effects]
    raw = json.loads((root / "assessment-predictions.json").read_text())
    ensembles = json.loads((root / "ensemble-predictions.json").read_text())
    qwen = [x["prediction"] for x in ensembles["qwen"]]
    llama_seed_scores = {
        seed: result["metrics"][f"llama-{seed}"]["balanced_accuracy"]
        for seed in SEEDS
    }
    best_llama_seed = max(SEEDS, key=lambda seed: llama_seed_scores[seed])
    comparison_rows = {
        "llama-ensemble": ensembles["llama"],
        "best-llama-seed": raw[f"llama-{best_llama_seed}"],
        "qwen-untrained": raw["qwen-untrained"],
        "majority": raw["majority"],
        "hint-option-lookup": raw["hint-option-lookup"],
    }
    bootstrap = CORE.bootstrap_balanced_accuracy_advantages(
        qwen,
        {
            name: [x["prediction"] for x in rows]
            for name, rows in comparison_rows.items()
        },
        labels,
    )
    result["best_llama_seed"] = best_llama_seed
    result["best_llama_seed_balanced_accuracy"] = llama_seed_scores[
        best_llama_seed
    ]
    result["paired_bootstrap_balanced_accuracy_advantages"] = bootstrap
    score = result["metrics"]["qwen-ensemble"]["balanced_accuracy"]
    result["primary_comparison_advantages"] = {
        name: score
        - CORE.binary_metrics(
            [x["prediction"] for x in rows],
            [x["yes_probability"] for x in rows],
            labels,
        )["balanced_accuracy"]
        for name, rows in comparison_rows.items()
    }
    candidate = (
        min(
            result["assessment_yes_prevalence"],
            1 - result["assessment_yes_prevalence"],
        )
        >= 0.15
        and score >= 0.70
        and min(
            result["metrics"][f"qwen-{seed}"]["balanced_accuracy"]
            for seed in SEEDS
        )
        >= 0.60
        and all(
            result["primary_comparison_advantages"][name] >= 0.05
            and bootstrap[name]["lower_95"] > 0
            for name in comparison_rows
        )
        and result["metrics"]["qwen-ensemble"]["brier"]
        < result["metrics"]["llama-ensemble"]["brier"]
        and result["metrics"]["qwen-ensemble"]["brier"]
        < result["metrics"]["qwen-untrained"]["brier"]
    )
    result["classification"] = (
        "OpaquePreferenceReplicationCandidate"
        if candidate
        else "OpaquePreferenceReplicationNoCandidate"
    )
    repository = Path(__file__).resolve().parents[2]
    validator = Path(__file__).with_name("validator_v19.py")
    result["source_identity"] = {
        "v19_py_sha256": CORE.sha_file(Path(__file__)),
        "validator_v19_py_sha256": CORE.sha_file(validator),
        "v18_shared_core_sha256": CORE.sha_file(V18_PATH),
        "git_head": subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip(),
        "git_status_sha256": CORE.sha_bytes(
            subprocess.run(
                ["git", "status", "--porcelain=v1"],
                cwd=repository,
                check=True,
                capture_output=True,
            ).stdout
        ),
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
    target = CORE.ChoiceModel(QWEN)
    effects = []
    for row, record in zip(corpus, records):
        if row.split != "assessment":
            continue
        ablated = target.choice(row.ablated_prompt)
        effects.append(
            {
                "family_id": row.family_id,
                "ablated": ablated,
                "label": (
                    "YES"
                    if record["hinted"]["choice"] != ablated["choice"]
                    else "NO"
                ),
            }
        )
    CORE.write_json(root / "assessment-effects.json", effects)
    labels = [x["label"] for x in effects]
    raw = json.loads((root / "assessment-predictions.json").read_text())
    metrics = {
        method: CORE.binary_metrics(
            [x["prediction"] for x in rows],
            [x["yes_probability"] for x in rows],
            labels,
        )
        for method, rows in raw.items()
    }
    ensembles = {
        name: majority_ensemble(raw, name) for name in MODELS
    }
    for name, rows in ensembles.items():
        metrics[f"{name}-ensemble"] = CORE.binary_metrics(
            [x["prediction"] for x in rows],
            [x["yes_probability"] for x in rows],
            labels,
        )
    CORE.write_json(root / "ensemble-predictions.json", ensembles)
    CORE.write_json(
        root / "result.json",
        {
            "classification": "OpaquePreferenceReplicationNoCandidate",
            "confirmation": "NotAuthorized",
            "stage_1": "BlockedByStage0C",
            "claim_ceiling": CLAIM,
            "assessment_yes_prevalence": labels.count("YES") / len(labels),
            "metrics": metrics,
            "prediction_lock_sha256": CORE.sha_file(
                root / "prediction-lock.json"
            ),
        },
    )
    finalize(root)


def record_blocked(root: Path) -> None:
    qualification = json.loads((root / "qualification.json").read_text())
    if (
        qualification.get("splits", {})
        .get("fit", {})
        .get("minority_fraction", 1.0)
        >= 0.20
    ):
        raise RuntimeError("blocked classification not supported by qualification")
    repository = Path(__file__).resolve().parents[2]
    validator = Path(__file__).with_name("validator_v19.py")
    CORE.write_json(
        root / "result.json",
        {
            "classification": "NotRunTargetLabelImbalance",
            "confirmation": "NotAuthorized",
            "stage_1": "BlockedByStage0C",
            "claim_ceiling": CLAIM,
            "qualification": qualification,
            "assessment_unhinted_outputs_generated": False,
            "adapters_trained": False,
            "source_identity": {
                "v19_py_sha256": CORE.sha_file(Path(__file__)),
                "validator_v19_py_sha256": CORE.sha_file(validator),
                "v18_shared_core_sha256": CORE.sha_file(V18_PATH),
                "git_head": subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    cwd=repository,
                    check=True,
                    capture_output=True,
                    text=True,
                ).stdout.strip(),
            },
        },
    )
    CORE.write_manifest(root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "phase",
        choices=("prepare", "train", "lock", "assess", "finalize", "record-blocked", "all"),
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
        if args.phase == "record-blocked":
            record_blocked(root)
    except Exception as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {"status": "completed", "phase": args.phase, "root": str(root)},
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
