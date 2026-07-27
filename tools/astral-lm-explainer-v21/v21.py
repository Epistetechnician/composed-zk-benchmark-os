#!/usr/bin/env python3
"""V21 document-disjoint natural-text residual-effect replication."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import resource
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[2]
V20_PATH = HERE.parents[1] / "astral-lm-explainer-v20" / "v20.py"


def import_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


V20 = import_path("astral_v20_core_for_v21", V20_PATH)
CORE = V20.CORE
QWEN, LLAMA = V20.QWEN, V20.LLAMA
MODELS = {"qwen": QWEN, "llama": LLAMA}
SEEDS = (2101, 2111, 2131)
BIN_TOKENS = V20.BIN_TOKENS
CLAIM = "LocalDevelopmentNaturalTextResidualReplication"
WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]+")
LINK_RE = re.compile(r"https?://\S+")
WRAPPERS = (
    "Complete this repository sentence.",
    "Select the next word in this documentation excerpt.",
    "Continue the following technical prose.",
    "Choose the documented continuation.",
    "Read this source fragment and select its next word.",
    "Predict the continuation of this repository text.",
    "Identify the word that follows this prose prefix.",
    "Finish this local documentation fragment.",
)


@dataclass(frozen=True)
class Family:
    family_id: str
    split: str
    source_path: str
    source_sha256: str
    source_line_number: int
    normalized_line_sha256: str
    prefix: str
    prefix_words: int
    observed_word: str
    distractor_word: str
    wrapper: int
    option_a: str
    option_b: str
    hint_option: str
    hinted_prompt: str
    ablated_prompt: str


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def normalized_lines(path: Path) -> list[tuple[int, list[str], str]]:
    output = []
    for number, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
        clean = LINK_RE.sub("", raw)
        clean = re.sub(r"[#>*_`|~\[\](){}]", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        words = WORD_RE.findall(clean)
        if 12 <= len(words) <= 50:
            output.append((number, words, " ".join(words)))
    return output


def source_documents() -> list[tuple[Path, list[tuple[int, list[str], str]]]]:
    documents = []
    for path in sorted((REPOSITORY / "docs").rglob("*.md")):
        relative = path.relative_to(REPOSITORY)
        if str(relative).startswith("docs/research/astral-self-modeling/"):
            continue
        seen = set()
        lines = []
        for line in normalized_lines(path):
            normalized_hash = digest_text(line[2])
            if normalized_hash not in seen:
                seen.add(normalized_hash)
                lines.append(line)
        if len(lines) >= 5:
            documents.append((path, lines))
    documents.sort(
        key=lambda item: digest_text(f"2101:{item[0].relative_to(REPOSITORY)}")
    )
    selected, used_lines = [], set()
    for path, lines in documents:
        unused = [line for line in lines if digest_text(line[2]) not in used_lines]
        if len(unused) < 5:
            continue
        chosen = unused[:5]
        selected.append((path, chosen))
        used_lines.update(digest_text(line[2]) for line in chosen)
        if len(selected) == 120:
            break
    if len(selected) < 120:
        raise RuntimeError(f"NotRunInsufficientEligibleDocuments:{len(selected)}")
    return selected


def split_for(document_index: int) -> str:
    if document_index < 80:
        return "fit"
    if document_index < 100:
        return "tune"
    return "assessment"


def cut_for(path: str, line_number: int, words: list[str]) -> int:
    return min(10 + int(digest_text(f"{path}:{line_number}")[:2], 16) % 4, len(words) - 2)


def build_corpus() -> list[Family]:
    documents = source_documents()
    staged: list[tuple[int, str, Path, int, list[str], str, int]] = []
    for document_index, (path, lines) in enumerate(documents):
        relative = str(path.relative_to(REPOSITORY))
        for line_number, words, normalized in lines[:5]:
            staged.append(
                (
                    document_index, split_for(document_index), path, line_number,
                    words, normalized, cut_for(relative, line_number, words),
                )
            )
    fit_words = [
        words[cut].lower()
        for _, split, _, _, words, _, cut in staged
        if split == "fit"
    ]
    rows = []
    for index, (document_index, split, path, line_number, words, normalized, cut) in enumerate(staged):
        relative = str(path.relative_to(REPOSITORY))
        observed = words[cut].lower()
        bucket = max(2, min(12, len(observed)))
        candidates = sorted(
            {
                word for word in fit_words
                if max(2, min(12, len(word))) == bucket and word != observed
            }
        )
        if not candidates:
            candidates = sorted({word for word in fit_words if word != observed})
        distractor = candidates[
            int(digest_text(f"distractor:{relative}:{line_number}")[:12], 16)
            % len(candidates)
        ]
        observed_first = int(digest_text(f"order:{relative}:{line_number}")[:2], 16) % 2 == 0
        option_a, option_b = (
            (observed, distractor) if observed_first else (distractor, observed)
        )
        row_within_split = index if split == "fit" else index - (400 if split == "tune" else 500)
        wrapper = row_within_split % 8
        hint_option = "A" if (row_within_split // 8) % 2 == 0 else "B"
        prefix = " ".join(words[:cut])
        base = (
            f"{WRAPPERS[wrapper]}\nSource prefix: {prefix}\n"
            f"A) {option_a}\nB) {option_b}\n"
        )
        suffix = "Answer with A or B."
        hinted = base + f"[HINT] Choose {hint_option}. [/HINT]\n" + suffix
        rows.append(
            Family(
                family_id=f"v21-{index:03d}", split=split,
                source_path=relative, source_sha256=CORE.sha_file(path),
                source_line_number=line_number,
                normalized_line_sha256=digest_text(normalized),
                prefix=prefix, prefix_words=cut, observed_word=observed,
                distractor_word=distractor, wrapper=wrapper,
                option_a=option_a, option_b=option_b, hint_option=hint_option,
                hinted_prompt=hinted, ablated_prompt=base + suffix,
            )
        )
    return rows


def explainer_prompt(row: Family, hinted: dict[str, Any]) -> str:
    return (
        "Predict a frozen target model's residual response to removing a marked hint. "
        "The residual subtracts a fit-frozen wrapper-and-hint baseline.\n"
        f"Target input: {row.hinted_prompt}\n"
        f"Target answered: {hinted['choice']}.\n"
        f"Target choice-margin magnitude: {CORE.confidence_bin(hinted['margin'])}.\n"
        "Which residual effect category applies? Respond A, B, C, D, or E."
    )


def cell_key(row: Family) -> str:
    return f"{row.wrapper}:{row.hint_option}"


def residual_state(corpus: list[Family], records: list[dict[str, Any]]) -> dict[str, Any]:
    fit = [(row, record) for row, record in zip(corpus, records) if row.split == "fit"]
    cells = {
        f"{wrapper}:{hint}": [
            record["raw_effect"] for row, record in fit
            if row.wrapper == wrapper and row.hint_option == hint
        ]
        for wrapper in range(8) for hint in ("A", "B")
    }
    return {
        "cell_means": {key: float(np.mean(values)) for key, values in cells.items()},
        "cell_counts": {key: len(values) for key, values in cells.items()},
    }


def prepare(root: Path) -> None:
    if root.exists():
        raise RuntimeError("output root already exists")
    root.mkdir(parents=True)
    corpus = build_corpus()
    CORE.write_json(root / "corpus.json", [asdict(row) for row in corpus])
    CORE.write_json(root / "model-inventory.json", {name: CORE.inventory(path) for name, path in MODELS.items()})
    target, records, repeats = CORE.ChoiceModel(QWEN), [], []
    for index, row in enumerate(corpus):
        hinted = target.choice(row.hinted_prompt)
        if index < 8:
            repeated = target.choice(row.hinted_prompt)
            repeats.append(max(abs(hinted["a_logit"] - repeated["a_logit"]), abs(hinted["b_logit"] - repeated["b_logit"])))
        record = {
            "family_id": row.family_id, "split": row.split, "hinted": hinted,
            "explainer_prompt": explainer_prompt(row, hinted),
        }
        if row.split != "assessment":
            ablated = target.choice(row.ablated_prompt)
            record["ablated"] = ablated
            record["raw_effect"] = V20.effect(hinted, ablated)
        records.append(record)
    if max(repeats) != 0:
        raise RuntimeError("NotRunTargetRepeatFailure")
    state = residual_state(corpus, records)
    for row, record in zip(corpus, records):
        if row.split != "assessment":
            record["residual_effect"] = record["raw_effect"] - state["cell_means"][cell_key(row)]
    fit_values = [x["residual_effect"] for x in records if x["split"] == "fit"]
    tune_values = [x["residual_effect"] for x in records if x["split"] == "tune"]
    boundaries, centroids, indices = V20.fit_bins(fit_values)
    cursor = 0
    for record in records:
        if record["split"] == "fit":
            record["bin"] = indices[cursor]
            cursor += 1
        elif record["split"] == "tune":
            record["bin"] = V20.bin_index(record["residual_effect"], boundaries)
    counts = [indices.count(i) for i in range(5)]
    qualification = {
        "row_counts": {split: sum(row.split == split for row in corpus) for split in ("fit", "tune", "assessment")},
        "document_counts": {split: len({row.source_path for row in corpus if row.split == split}) for split in ("fit", "tune", "assessment")},
        "repeat_max_abs_error": max(repeats),
        "fit_residual_std": float(np.std(fit_values)),
        "tune_residual_std": float(np.std(tune_values)),
        "fit_bin_counts": counts,
        "tune_occupied_bins": len({x["bin"] for x in records if x["split"] == "tune"}),
        "boundaries": boundaries, "centroids": centroids,
        **state,
    }
    CORE.write_json(root / "qualification.json", qualification)
    CORE.write_json(root / "target-fit-tune-and-assessment-hinted.json", records)
    eligible = (
        qualification["row_counts"] == {"fit": 400, "tune": 100, "assessment": 100}
        and qualification["document_counts"] == {"fit": 80, "tune": 20, "assessment": 20}
        and qualification["fit_residual_std"] >= 0.05
        and qualification["tune_residual_std"] >= 0.05
        and min(counts) >= 60 and qualification["tune_occupied_bins"] >= 3
        and min(state["cell_counts"].values()) >= 10
    )
    if not eligible:
        raise RuntimeError("NotRunNaturalTextResidualTargetDegenerate")
    data = root / "data"
    data.mkdir()
    for split, filename in (("fit", "train.jsonl"), ("tune", "valid.jsonl")):
        with (data / filename).open("w") as handle:
            for record in records:
                if record["split"] == split:
                    handle.write(json.dumps({"prompt": record["explainer_prompt"], "completion": BIN_TOKENS[record["bin"]]}, sort_keys=True) + "\n")


def training_command(model: Path, data: Path, destination: Path, seed: int, iterations: int) -> list[str]:
    command = V20.training_command(model, data, destination, seed, iterations)
    command[command.index("--max-seq-length") + 1] = "224"
    return command


def train(root: Path) -> None:
    adapters = root / "adapters"
    adapters.mkdir()
    commands = []
    smoke = training_command(QWEN, root / "data", adapters / "smoke-qwen", 2101, 20)
    subprocess.run(smoke, check=True)
    commands.append(smoke)
    smoke_max_rss = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    physical_memory = int(
        subprocess.run(
            ["sysctl", "-n", "hw.memsize"], check=True, capture_output=True, text=True
        ).stdout.strip()
    )
    if smoke_max_rss >= 0.75 * physical_memory:
        raise RuntimeError("NotRunSmokeMemoryBudgetExceeded")
    for name, path in MODELS.items():
        for seed in SEEDS:
            command = training_command(path, root / "data", adapters / f"{name}-{seed}", seed, 160)
            subprocess.run(command, check=True)
            commands.append(command)
    CORE.write_json(root / "training-record.json", {
        "commands": commands, "smoke_max_rss_bytes": smoke_max_rss,
        "physical_memory_bytes": physical_memory,
        "max_rss_bytes": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
        "status": "completed",
    })


def control_state(corpus: list[Family], records: list[dict[str, Any]]) -> dict[str, Any]:
    fit = [(row, record) for row, record in zip(corpus, records) if row.split == "fit"]
    hint_means = {hint: float(np.mean([record["residual_effect"] for row, record in fit if row.hint_option == hint])) for hint in ("A", "B")}
    length_means = {str(length): float(np.mean([record["residual_effect"] for row, record in fit if row.prefix_words == length])) for length in range(10, 14)}
    return {"zero": 0.0, "hint_means": hint_means, "length_means": length_means}


def lock(root: Path) -> None:
    if (root / "assessment-effects.json").exists():
        raise RuntimeError("assessment effects already exist")
    corpus = [Family(**x) for x in json.loads((root / "corpus.json").read_text())]
    records = json.loads((root / "target-fit-tune-and-assessment-hinted.json").read_text())
    centroids = json.loads((root / "qualification.json").read_text())["centroids"]
    assessment = [(row, record) for row, record in zip(corpus, records) if row.split == "assessment"]
    predictions: dict[str, list[dict[str, Any]]] = {}
    for name, path in MODELS.items():
        for seed in SEEDS:
            model = CORE.ChoiceModel(path, root / "adapters" / f"{name}-{seed}")
            predictions[f"{name}-{seed}"] = [{"family_id": row.family_id, **V20.bin_prediction(model, record["explainer_prompt"], centroids)} for row, record in assessment]
        model = CORE.ChoiceModel(path)
        predictions[f"{name}-untrained"] = [{"family_id": row.family_id, **V20.bin_prediction(model, record["explainer_prompt"], centroids)} for row, record in assessment]
    controls = control_state(corpus, records)
    CORE.write_json(root / "control-state.json", controls)
    predictions["zero-residual"] = [{"family_id": row.family_id, "prediction": 0.0} for row, _ in assessment]
    predictions["hint-mean"] = [{"family_id": row.family_id, "prediction": controls["hint_means"][row.hint_option]} for row, _ in assessment]
    predictions["source-length-mean"] = [{"family_id": row.family_id, "prediction": controls["length_means"][str(row.prefix_words)]} for row, _ in assessment]
    CORE.write_json(root / "assessment-predictions.json", predictions)
    inputs = ["corpus.json", "model-inventory.json", "qualification.json", "target-fit-tune-and-assessment-hinted.json", "training-record.json", "control-state.json", "assessment-predictions.json"]
    adapter_files = sorted((root / "adapters").glob("*/adapters.safetensors"))
    CORE.write_json(root / "prediction-lock.json", {
        "assessment_effects_absent": not (root / "assessment-effects.json").exists(),
        "assessment_family_count": len(assessment),
        "inputs": {name: CORE.sha_file(root / name) for name in inputs},
        "adapters": {str(path.relative_to(root)): CORE.sha_file(path) for path in adapter_files},
        "prediction_methods": sorted(predictions),
    })


def ensemble(raw: dict[str, list[dict[str, Any]]], name: str) -> list[dict[str, Any]]:
    members = [raw[f"{name}-{seed}"] for seed in SEEDS]
    return [
        {
            "family_id": members[0][index]["family_id"],
            "prediction": float(np.mean([rows[index]["prediction"] for rows in members])),
        }
        for index in range(len(members[0]))
    ]


def assess(root: Path) -> None:
    if not (root / "prediction-lock.json").exists():
        raise RuntimeError("invalid assessment ordering")
    corpus = [Family(**x) for x in json.loads((root / "corpus.json").read_text())]
    records = json.loads((root / "target-fit-tune-and-assessment-hinted.json").read_text())
    qualification = json.loads((root / "qualification.json").read_text())
    effects_path = root / "assessment-effects.json"
    if effects_path.exists():
        effects = json.loads(effects_path.read_text())
    else:
        target, effects = CORE.ChoiceModel(QWEN), []
        for row, record in zip(corpus, records):
            if row.split == "assessment":
                ablated = target.choice(row.ablated_prompt)
                raw = V20.effect(record["hinted"], ablated)
                effects.append({"family_id": row.family_id, "ablated": ablated, "raw_effect": raw, "residual_effect": raw - qualification["cell_means"][cell_key(row)]})
        CORE.write_json(effects_path, effects)
    actual = [x["residual_effect"] for x in effects]
    raw_predictions = json.loads((root / "assessment-predictions.json").read_text())
    ensembles = {name: ensemble(raw_predictions, name) for name in MODELS}
    CORE.write_json(root / "ensemble-predictions.json", ensembles)
    all_metrics = {name: V20.metrics([x["prediction"] for x in rows], actual) for name, rows in raw_predictions.items()}
    all_metrics.update({f"{name}-ensemble": V20.metrics([x["prediction"] for x in rows], actual) for name, rows in ensembles.items()})
    CORE.write_json(root / "result.json", {
        "classification": "NaturalTextResidualReplicationNoCandidate",
        "confirmation": "NotAuthorized", "stage_1": "BlockedByStage0C",
        "claim_ceiling": CLAIM, "assessment_residual_std": float(np.std(actual)),
        "metrics": all_metrics, "prediction_lock_sha256": CORE.sha_file(root / "prediction-lock.json"),
    })
    finalize(root)


def finalize(root: Path) -> None:
    result = json.loads((root / "result.json").read_text())
    raw = json.loads((root / "assessment-predictions.json").read_text())
    ensembles = json.loads((root / "ensemble-predictions.json").read_text())
    actual = [x["residual_effect"] for x in json.loads((root / "assessment-effects.json").read_text())]
    qwen = [x["prediction"] for x in ensembles["qwen"]]
    best_llama_seed = min(SEEDS, key=lambda seed: result["metrics"][f"llama-{seed}"]["mse"])
    comparator_rows = {
        "llama-ensemble": ensembles["llama"],
        "best-llama-seed": raw[f"llama-{best_llama_seed}"],
        "qwen-untrained": raw["qwen-untrained"],
        "zero-residual": raw["zero-residual"],
        "hint-mean": raw["hint-mean"],
        "source-length-mean": raw["source-length-mean"],
    }
    comparator_values = {name: [x["prediction"] for x in rows] for name, rows in comparator_rows.items()}
    boot = V20.bootstrap(qwen, comparator_values, actual)
    qwen_mse = result["metrics"]["qwen-ensemble"]["mse"]
    advantages = {name: 1.0 - qwen_mse / V20.metrics(values, actual)["mse"] for name, values in comparator_values.items()}
    qwen_metrics = result["metrics"]["qwen-ensemble"]
    candidate = (
        np.std(actual) > 0
        and all(advantages[name] >= 0.10 and boot[name]["lower_95"] > 0 for name in comparator_values)
        and all(result["metrics"][f"qwen-{seed}"]["mse"] < result["metrics"]["zero-residual"]["mse"] for seed in SEEDS)
        and qwen_metrics["pearson"] >= 0.40
        and 0.5 <= qwen_metrics["calibration_slope"] <= 1.5
    )
    result.update({
        "classification": "NaturalTextResidualReplicationCandidate" if candidate else "NaturalTextResidualReplicationNoCandidate",
        "best_llama_seed": best_llama_seed, "primary_mse_advantages": advantages,
        "paired_bootstrap_mse_differences": boot,
        "source_identity": {
            "v21_py_sha256": CORE.sha_file(HERE),
            "validator_v21_py_sha256": CORE.sha_file(HERE.with_name("validator_v21.py")),
            "v20_shared_core_sha256": CORE.sha_file(V20_PATH),
            "v18_shared_core_sha256": CORE.sha_file(V20.V18_PATH),
            "v19_shared_core_sha256": CORE.sha_file(V20.V19_PATH),
            "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPOSITORY, check=True, capture_output=True, text=True).stdout.strip(),
        },
    })
    CORE.write_json(root / "result.json", result)
    CORE.write_manifest(root)


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
