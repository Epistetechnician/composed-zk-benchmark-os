#!/usr/bin/env python3
"""Run the bounded Gemma3 plasticity-guard adapter experiment.

State slice: continual-learning-plasticity-guard-reversible-adapter-v1.

The cached Gemma3 base checkpoint is loaded offline. Every learner update is a
LoRA adapter-only subprocess. The plasticity guard may reject a candidate
adapter, but it never edits or merges the base checkpoint.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_SLICE = "continual-learning-plasticity-guard-reversible-adapter-v1"
CLAIM_CEILING = "LocalDevelopmentPlasticityGuardReversibleAdapterFeasibility"
DEFAULT_MODEL = Path("/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16")
DEFAULT_INPUT = Path(
    "/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/"
    "gemma3-manual-inputs-v1/newsroom/release/test.jsonl.gz"
)
PRIMARY_VOLUME = Path("/Volumes/PrimaryED")
DAED_VOLUME = Path("/Volumes/DAed")
DEFAULT_PRIMARY_ROOT = PRIMARY_VOLUME / (
    "ResearchArtifacts/composed-zk-benchmark-os/"
    "continual-learning-plasticity-guard-reversible-adapter-v1-20260828-r1"
)
DEFAULT_DAED_ROOT = DAED_VOLUME / (
    "Archives/composed-zk-benchmark-os/"
    "continual-learning-plasticity-guard-reversible-adapter-v1-20260828-r1"
)
VALIDATOR = Path(__file__).with_name("validate_plasticity_guard_reversible_adapter_v1.py")

WINDOW_TOKENS = 256
SELECTION_OFFSET = 8
SELECTED_DOCUMENT_COUNT = 12
FIT_DOCUMENT_COUNT = 6
TUNE_DOCUMENT_COUNT = 3
ASSESSMENT_DOCUMENT_COUNT = 3
SEEDS = (1739, 1741)
ORDERS = {
    "forward": tuple(range(FIT_DOCUMENT_COUNT)),
    "reverse": tuple(reversed(range(FIT_DOCUMENT_COUNT))),
}
TRAIN_ITERS = 3
TRAIN_ROWS = 4
TRAIN_NUM_LAYERS = 4
TRAIN_BATCH_SIZE = 1
TRAIN_LEARNING_RATE = 0.0001
TRAIN_MAX_SEQ_LENGTH = WINDOW_TOKENS
MIN_CURRENT_GAIN = 0.001
MAX_PROTECTED_DEGRADATION = 0.010
MAX_FORGETTING_FRACTION = 0.05
MAX_CALIBRATION_ECE_DELTA = 0.05
PARITY_TOLERANCE = 1e-5
REPEAT_TOLERANCE = 1e-8
ADAPTER_RESTORE_TOLERANCE = 1e-6
PRIMARY_EFFECT_THRESHOLD = 0.010
BOOTSTRAP_SEED = 20260828
BOOTSTRAP_REPLICATES = 10_000
PRIMARY_WIN_COUNT = 3
NEWSROOM_UPSTREAM = "https://lil.nlp.cornell.edu/newsroom/download/index.html"
SOURCE_SCHEMA = "gemma3-newsroom-plasticity-guard-input-v1"
CORPUS_SCHEMA = "gemma3-newsroom-plasticity-guard-corpus-v1"
SELECTION_POLICY = "next-twelve-after-eight-eligible-newsroom-test-records-v3"


@dataclass(frozen=True)
class Window:
    split: str
    index: int
    document_id: str
    source_line: int
    url: str
    text: str
    text_sha256: str
    token_count: int
    relative_path: str


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "unavailable"


def model_manifest(model_path: Path) -> dict[str, Any]:
    files = []
    for path in sorted(
        candidate
        for candidate in model_path.rglob("*")
        if candidate.is_file()
        and not candidate.is_symlink()
        and ".cache" not in candidate.relative_to(model_path).parts
    ):
        files.append(
            {
                "path": path.relative_to(model_path).as_posix(),
                "byte_len": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    if not files:
        raise ValueError(f"cached model directory has no stable files: {model_path}")
    body = {"model_name": model_path.name, "files": files}
    return {"manifest": body, "manifest_sha256": digest(body)}


def artifact_file_manifest(root: Path) -> dict[str, Any]:
    files = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "byte_len": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {"root": root.name, "files": files, "manifest_sha256": digest(files)}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def external_path(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        raise ValueError(f"{label} must be outside the repository: {resolved}")
    return resolved


def volume_path(path: Path, volume: Path, label: str) -> Path:
    resolved = external_path(path, label)
    volume = volume.resolve()
    if not volume.is_dir():
        raise FileNotFoundError(f"required external volume is not mounted: {volume}")
    if resolved != volume and volume not in resolved.parents:
        raise ValueError(f"{label} must be under {volume}: {resolved}")
    return resolved


def require_new_root(path: Path, label: str) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite existing {label}: {path}")


def load_tokenizer(model_path: Path) -> Any:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from mlx_lm.utils import load_tokenizer

    from experiments.continual_learning.mlx_tokenizer_policy import (
        tokenizer_config_from_policy,
        tokenizer_policy_for_model,
    )

    policy = tokenizer_policy_for_model(model_path)
    return load_tokenizer(
        model_path,
        tokenizer_config_extra=tokenizer_config_from_policy(policy) or None,
    )


def open_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f"NEWSROOM input must be a regular file: {path}")
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"blank NEWSROOM JSONL line: {line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"NEWSROOM record must be an object: line {line_number}")
            yield line_number, value


def select_records(input_path: Path, tokenizer: Any) -> list[dict[str, Any]]:
    selected = []
    eligible_count = 0
    seen_urls: set[str] = set()
    for line_number, value in open_jsonl(input_path):
        text = value.get("text")
        url = value.get("url")
        if not isinstance(text, str) or not text:
            raise ValueError(f"NEWSROOM record has invalid text: line {line_number}")
        if not isinstance(url, str) or not url:
            raise ValueError(f"NEWSROOM record has invalid url: line {line_number}")
        if url in seen_urls:
            raise ValueError(f"duplicate NEWSROOM URL before selection: {url}")
        seen_urls.add(url)
        token_ids = list(tokenizer.encode(text, add_special_tokens=False))
        if len(token_ids) < WINDOW_TOKENS:
            continue
        if eligible_count < SELECTION_OFFSET:
            eligible_count += 1
            continue
        eligible_count += 1
        selected.append(
            {
                "line_number": line_number,
                "document_id": f"newsroom-test-line-{line_number:07d}",
                "url": url,
                "text_sha256": sha256_bytes(text.encode("utf-8")),
                "token_count": len(token_ids),
                "token_ids": token_ids[:WINDOW_TOKENS],
            }
        )
        if len(selected) == SELECTED_DOCUMENT_COUNT:
            break
    if len(selected) != SELECTED_DOCUMENT_COUNT:
        raise ValueError(
            f"NEWSROOM input yielded {len(selected)} selected records; "
            f"expected {SELECTED_DOCUMENT_COUNT}"
        )
    return selected


def materialize_corpus(root: Path, selected: list[dict[str, Any]], tokenizer: Any) -> tuple[list[Window], list[Window], list[Window], dict[str, Any]]:
    splits = (
        ("fit", FIT_DOCUMENT_COUNT),
        ("tune", TUNE_DOCUMENT_COUNT),
        ("assessment", ASSESSMENT_DOCUMENT_COUNT),
    )
    windows: dict[str, list[Window]] = {name: [] for name, _ in splits}
    entries: dict[str, list[dict[str, Any]]] = {name: [] for name, _ in splits}
    offset = 0
    for split, count in splits:
        for local_index in range(count):
            document = selected[offset]
            offset += 1
            relative_path = Path(split) / "newsroom" / f"window-{offset - 1:06d}.txt"
            text = tokenizer.decode(document["token_ids"])
            if list(tokenizer.encode(text, add_special_tokens=False)) != document["token_ids"]:
                raise ValueError(f"tokenizer round-trip changed {relative_path}")
            output_path = root / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(text, encoding="utf-8")
            raw = text.encode("utf-8")
            window = Window(
                split=split,
                index=offset - 1,
                document_id=document["document_id"],
                source_line=document["line_number"],
                url=document["url"],
                text=text,
                text_sha256=sha256_bytes(raw),
                token_count=WINDOW_TOKENS,
                relative_path=relative_path.as_posix(),
            )
            windows[split].append(window)
            entries[split].append(
                {
                    "dataset": "newsroom",
                    "document_id": window.document_id,
                    "source_line": window.source_line,
                    "url": window.url,
                    "path": window.relative_path,
                    "byte_len": len(raw),
                    "text_sha256": window.text_sha256,
                    "token_count": window.token_count,
                }
            )
    body = {
        "state_slice": STATE_SLICE,
        "schema": CORPUS_SCHEMA,
        "window_token_count": WINDOW_TOKENS,
        "selection_policy": SELECTION_POLICY,
        "fit": entries["fit"],
        "tune": entries["tune"],
        "assessment": entries["assessment"],
        "fit_window_count": len(windows["fit"]),
        "tune_window_count": len(windows["tune"]),
        "assessment_window_count": len(windows["assessment"]),
    }
    manifest = {"manifest": body, "manifest_sha256": digest(body)}
    write_json(root / "manifest.json", manifest)
    return windows["fit"], windows["tune"], windows["assessment"], manifest


def copy_raw_input(input_path: Path, root: Path) -> Path:
    raw_path = root / "raw" / "newsroom" / input_path.name
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_path, raw_path)
    if sha256_file(raw_path) != sha256_file(input_path):
        raise RuntimeError("NEWSROOM raw-input copy checksum mismatch")
    return raw_path


def write_input_manifest(root: Path, input_path: Path, raw_path: Path, selected: list[dict[str, Any]]) -> dict[str, Any]:
    body = {
        "state_slice": STATE_SLICE,
        "schema": SOURCE_SCHEMA,
        "upstream": NEWSROOM_UPSTREAM,
        "source_path": str(input_path),
        "raw_path": raw_path.relative_to(root).as_posix(),
        "raw_byte_len": raw_path.stat().st_size,
        "raw_sha256": sha256_file(raw_path),
        "split": "test",
        "selection_policy": SELECTION_POLICY,
        "selection_offset": SELECTION_OFFSET,
        "selected_documents": [
            {key: value for key, value in row.items() if key != "token_ids"}
            for row in selected
        ],
    }
    manifest = {"manifest": body, "manifest_sha256": digest(body)}
    write_json(root / "input-manifest.json", manifest)
    return manifest


def load_runtime(model_path: Path, adapter_path: Path | None = None) -> tuple[Any, Any, Any, dict[str, Any]]:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    import mlx.core as mx
    from mlx_lm import load

    from experiments.continual_learning.mlx_tokenizer_policy import (
        tokenizer_config_from_policy,
        tokenizer_policy_for_model,
    )

    policy = tokenizer_policy_for_model(model_path)
    model, tokenizer = load(
        str(model_path),
        tokenizer_config=tokenizer_config_from_policy(policy) or None,
        adapter_path=str(adapter_path) if adapter_path else None,
    )
    return model, tokenizer, mx, policy


def evaluate_windows(model: Any, tokenizer: Any, mx: Any, windows: Sequence[Window]) -> dict[str, Any]:
    total_nll = 0.0
    total_tokens = 0
    total_correct = 0
    confidences: list[float] = []
    correctness: list[int] = []
    rows = []
    for window in windows:
        token_ids = list(tokenizer.encode(window.text, add_special_tokens=False))
        if len(token_ids) != WINDOW_TOKENS:
            raise RuntimeError(f"window token count drift: {window.relative_path}")
        logits = model(mx.array([token_ids]))
        mx.eval(logits)
        token_logits = logits[0, :-1, :]
        log_probs = token_logits - mx.logsumexp(token_logits, axis=-1, keepdims=True)
        targets = mx.array(token_ids[1:])
        token_nll = -float(mx.sum(log_probs[mx.arange(len(token_ids) - 1), targets]))
        predicted = mx.argmax(token_logits, axis=-1)
        confidence = mx.max(mx.exp(log_probs), axis=-1)
        correct = (predicted == targets).tolist()
        confidence_values = [float(value) for value in confidence.tolist()]
        target_count = len(token_ids) - 1
        total_nll += token_nll
        total_tokens += target_count
        total_correct += sum(int(value) for value in correct)
        confidences.extend(confidence_values)
        correctness.extend(int(value) for value in correct)
        rows.append(
            {
                "document_id": window.document_id,
                "split": window.split,
                "text_sha256": window.text_sha256,
                "token_count": len(token_ids),
                "target_count": target_count,
                "nll": round(token_nll, 9),
            }
        )
    if total_tokens <= 0:
        raise ValueError("evaluation has no target tokens")
    ece = expected_calibration_error(confidences, correctness)
    mean_nll = total_nll / total_tokens
    return {
        "mean_nll": round(mean_nll, 9),
        "perplexity": round(math.exp(mean_nll), 9),
        "target_tokens": total_tokens,
        "accuracy": round(total_correct / total_tokens, 9),
        "ece": round(ece, 9),
        "rows": rows,
    }


def expected_calibration_error(confidences: Sequence[float], correctness: Sequence[int], bins: int = 10) -> float:
    if len(confidences) != len(correctness) or not confidences:
        raise ValueError("calibration inputs must be non-empty and aligned")
    total = len(confidences)
    error = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        selected = [
            position
            for position, confidence in enumerate(confidences)
            if (lower <= confidence < upper) or (index == bins - 1 and confidence == upper)
        ]
        if not selected:
            continue
        accuracy = sum(correctness[position] for position in selected) / len(selected)
        mean_confidence = sum(confidences[position] for position in selected) / len(selected)
        error += len(selected) / total * abs(accuracy - mean_confidence)
    return error


def probe_logits(model: Any, tokenizer: Any, mx: Any, window: Window) -> Any:
    token_ids = list(tokenizer.encode(window.text, add_special_tokens=False))
    logits = model(mx.array([token_ids]))
    mx.eval(logits)
    return logits[0, -1, :]


def max_abs_delta(left: Any, right: Any, mx: Any) -> float:
    return float(mx.max(mx.abs(left - right)))


def training_command(model: Path, data: Path, adapter: Path, seed: int, resume: Path | None) -> list[str]:
    command = [
        sys.executable,
        "-B",
        "-m",
        "experiments.continual_learning.safe_mlx_lora",
        "--model",
        str(model),
        "--train",
        "--data",
        str(data),
        "--fine-tune-type",
        "lora",
        "--optimizer",
        "adamw",
        "--num-layers",
        str(TRAIN_NUM_LAYERS),
        "--batch-size",
        str(TRAIN_BATCH_SIZE),
        "--iters",
        str(TRAIN_ITERS),
        "--learning-rate",
        str(TRAIN_LEARNING_RATE),
        "--steps-per-report",
        str(TRAIN_ITERS),
        "--steps-per-eval",
        str(TRAIN_ITERS),
        "--val-batches",
        "-1",
        "--max-seq-length",
        str(TRAIN_MAX_SEQ_LENGTH),
        "--adapter-path",
        str(adapter),
        "--save-every",
        str(TRAIN_ITERS),
        "--seed",
        str(seed),
    ]
    if resume is not None:
        command.extend(["--resume-adapter-file", str(resume)])
    return command


def write_training_dataset(path: Path, window: Window) -> None:
    path.mkdir(parents=True, exist_ok=False)
    row = json.dumps({"text": window.text}, sort_keys=True)
    for name in ("train.jsonl", "valid.jsonl", "test.jsonl"):
        (path / name).write_text("\n".join([row] * TRAIN_ROWS) + "\n", encoding="utf-8")


def run_training(
    model: Path,
    data: Path,
    adapter: Path,
    seed: int,
    resume: Path | None,
    log_path: Path,
    artifact_root: Path,
) -> dict[str, Any]:
    command = training_command(model, data, adapter, seed, resume)
    environment = os.environ.copy()
    environment.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    completed = subprocess.run(
        command,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    log_path.write_text(completed.stdout + "\n" + completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise RuntimeError(f"LoRA training failed with exit {completed.returncode}: {log_path}")
    adapter_file = adapter / "adapters.safetensors"
    if not adapter_file.is_file():
        raise RuntimeError(f"LoRA training did not publish adapter file: {adapter_file}")
    return {
        "command": command,
        "command_sha256": digest(command),
        "returncode": completed.returncode,
        "iters": TRAIN_ITERS,
        "rows": TRAIN_ROWS,
        "num_layers": TRAIN_NUM_LAYERS,
        "batch_size": TRAIN_BATCH_SIZE,
        "adapter_file": adapter_file.relative_to(artifact_root).as_posix(),
        "adapter_sha256": sha256_file(adapter_file),
        "adapter_byte_len": adapter_file.stat().st_size,
    }


def make_zero_adapter(source: Path, destination: Path) -> None:
    import mlx.core as mx

    destination.mkdir(parents=True, exist_ok=False)
    config = source / "adapter_config.json"
    if not config.is_file():
        raise FileNotFoundError(f"adapter config missing: {config}")
    shutil.copy2(config, destination / "adapter_config.json")
    weights = mx.load(str(source / "adapters.safetensors"))
    mx.save_safetensors(
        str(destination / "adapters.safetensors"),
        {key: mx.zeros_like(value) for key, value in weights.items()},
    )


def copy_adapter(source: Path, destination: Path) -> None:
    shutil.copytree(source, destination)


def mean_nll(metrics: dict[str, Any]) -> float:
    return float(metrics["mean_nll"])


def plasticity_guard_accept(step: int, current_gain: float, protected_delta: float) -> bool:
    """Apply the preregistered guard without consulting assessment data."""

    if step < 0 or not math.isfinite(current_gain) or not math.isfinite(protected_delta):
        raise ValueError("plasticity guard inputs must be finite and step must be non-negative")
    return step == 0 or (
        current_gain >= MIN_CURRENT_GAIN
        and protected_delta <= MAX_PROTECTED_DEGRADATION
    )


def evaluate_adapter(model_path: Path, adapter_path: Path | None, windows: Sequence[Window]) -> dict[str, Any]:
    model, tokenizer, mx, _policy = load_runtime(model_path, adapter_path)
    return evaluate_windows(model, tokenizer, mx, windows)


def train_case(
    root: Path,
    model_path: Path,
    base_metrics: dict[str, dict[str, Any]],
    fit: Sequence[Window],
    tune: Sequence[Window],
    assessment: Sequence[Window],
    seed: int,
    order_name: str,
    order: Sequence[int],
    arm: str,
) -> dict[str, Any]:
    case_name = f"seed-{seed}-{order_name}"
    case_root = root / "cases" / case_name / arm
    data_root = case_root / "data"
    adapter_root = case_root / "adapters"
    log_root = case_root / "logs"
    adapter_root.mkdir(parents=True, exist_ok=False)
    log_root.mkdir(parents=True, exist_ok=False)
    active_adapter: Path | None = None
    protected: list[Window] = []
    updates = []
    for step, fit_index in enumerate(order):
        current = fit[fit_index]
        dataset = data_root / f"step-{step}"
        write_training_dataset(dataset, current)
        candidate = adapter_root / f"step-{step}"
        resume_file = active_adapter / "adapters.safetensors" if active_adapter else None
        training = run_training(
            model_path,
            dataset,
            candidate,
            seed + step,
            resume_file,
            log_root / f"step-{step}.log",
            root,
        )
        before_windows = [current, *protected]
        if active_adapter is None:
            before_metrics = {
                window.document_id: base_metrics[window.document_id] for window in before_windows
            }
        else:
            before_eval = evaluate_adapter(model_path, active_adapter, before_windows)
            before_metrics = {
                row["document_id"]: row for row in before_eval["rows"]
            }
            before_eval_by_id = {
                row["document_id"]: row for row in before_eval["rows"]
            }
            for window in before_windows:
                before_metrics[window.document_id] = {
                    "mean_nll": before_eval_by_id[window.document_id]["nll"]
                    / before_eval_by_id[window.document_id]["target_count"],
                    "row": before_eval_by_id[window.document_id],
                }
        candidate_eval = evaluate_adapter(model_path, candidate, before_windows)
        candidate_rows = {row["document_id"]: row for row in candidate_eval["rows"]}
        current_before = float(before_metrics[current.document_id]["mean_nll"])
        current_after = candidate_rows[current.document_id]["nll"] / candidate_rows[current.document_id]["target_count"]
        current_gain = current_before - current_after
        protected_before = 0.0
        protected_after = 0.0
        protected_delta = 0.0
        if protected:
            protected_before = sum(
                float(before_metrics[window.document_id]["mean_nll"]) for window in protected
            ) / len(protected)
            protected_after = sum(
                candidate_rows[window.document_id]["nll"] / candidate_rows[window.document_id]["target_count"]
                for window in protected
            ) / len(protected)
            protected_delta = protected_after - protected_before
        guard_would_accept = plasticity_guard_accept(step, current_gain, protected_delta)
        committed = arm == "fixed_cadence" or guard_would_accept
        previous_adapter = active_adapter
        if committed:
            active_adapter = candidate
            protected.append(current)
        updates.append(
            {
                "step": step,
                "fit_index": fit_index,
                "document_id": current.document_id,
                "candidate_adapter": candidate.relative_to(root).as_posix(),
                "candidate_adapter_sha256": training["adapter_sha256"],
                "resume_adapter": resume_file.relative_to(root).as_posix() if resume_file else None,
                "current_before_mean_nll": round(current_before, 9),
                "current_after_mean_nll": round(current_after, 9),
                "current_gain": round(current_gain, 9),
                "protected_before_mean_nll": round(protected_before, 9),
                "protected_after_mean_nll": round(protected_after, 9),
                "protected_delta": round(protected_delta, 9),
                "guard_min_current_gain": MIN_CURRENT_GAIN,
                "guard_max_protected_degradation": MAX_PROTECTED_DEGRADATION,
                "guard_would_accept": guard_would_accept,
                "decision": "commit" if committed else "rollback",
                "active_adapter_after": active_adapter.relative_to(root).as_posix() if active_adapter else None,
                "previous_active_adapter": previous_adapter.relative_to(root).as_posix() if previous_adapter else None,
                "training": training,
                "equal_compute_update": {
                    "rows": TRAIN_ROWS,
                    "iters": TRAIN_ITERS,
                    "num_layers": TRAIN_NUM_LAYERS,
                    "batch_size": TRAIN_BATCH_SIZE,
                },
            }
        )
    if active_adapter is None:
        raise RuntimeError(f"case produced no committed adapter: {case_name}/{arm}")
    final_adapter = active_adapter
    final_fit = evaluate_adapter(model_path, final_adapter, fit)
    final_tune = evaluate_adapter(model_path, final_adapter, tune)
    base_fit = base_metrics["__fit__"]
    fit_forgetting_delta = mean_nll(final_fit) - mean_nll(base_fit)
    fit_forgetting_fraction = fit_forgetting_delta / mean_nll(base_fit)
    return {
        "state_slice": STATE_SLICE,
        "case": case_name,
        "seed": seed,
        "order_name": order_name,
        "order": list(order),
        "arm": arm,
        "final_adapter": final_adapter.relative_to(root).as_posix(),
        "updates": updates,
        "commit_count": sum(update["decision"] == "commit" for update in updates),
        "rollback_count": sum(update["decision"] == "rollback" for update in updates),
        "fit_after": final_fit,
        "tune_after": final_tune,
        "fit_forgetting_delta": round(fit_forgetting_delta, 9),
        "fit_forgetting_fraction": round(fit_forgetting_fraction, 9),
        "tune_ece_delta": round(float(final_tune["ece"]) - float(base_metrics["__tune__"]["ece"]), 9),
        "assessment_started": False,
    }


def bootstrap_interval(values: Sequence[float], seed: int, replicates: int) -> tuple[float, float]:
    if not values:
        raise ValueError("bootstrap requires at least one value")
    rng = random.Random(seed)
    means = []
    for _ in range(replicates):
        means.append(sum(values[rng.randrange(len(values))] for _ in values) / len(values))
    means.sort()
    def percentile(percent: float) -> float:
        position = (len(means) - 1) * percent
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return means[lower]
        return means[lower] + (means[upper] - means[lower]) * (position - lower)
    return percentile(0.025), percentile(0.975)


def build_config(model_path: Path, model_digest: str, input_manifest: dict[str, Any], corpus_manifest: dict[str, Any]) -> dict[str, Any]:
    source_files = [
        Path(__file__),
        Path(__file__).with_name("safe_mlx_lora.py"),
        Path(__file__).with_name("mlx_tokenizer_policy.py"),
        VALIDATOR,
    ]
    return {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "model_name": model_path.name,
        "model_path": str(model_path),
        "model_manifest_sha256": model_digest,
        "architecture": "gemma3_text",
        "expected_layer_count": 26,
        "expected_hidden_size": 1152,
        "runtime": {
            "python": sys.version.split()[0],
            "mlx": package_version("mlx"),
            "mlx_lm": package_version("mlx-lm"),
        },
        "tokenizer_policy": "cached-model-bound-mlx-tokenizer-policy-v1",
        "input_manifest_sha256": input_manifest["manifest_sha256"],
        "corpus_manifest_sha256": corpus_manifest["manifest_sha256"],
        "selection_policy": SELECTION_POLICY,
        "selection_offset": SELECTION_OFFSET,
        "window_token_count": WINDOW_TOKENS,
        "split_counts": {
            "fit": FIT_DOCUMENT_COUNT,
            "tune": TUNE_DOCUMENT_COUNT,
            "assessment": ASSESSMENT_DOCUMENT_COUNT,
        },
        "seeds": list(SEEDS),
        "orders": {name: list(order) for name, order in ORDERS.items()},
        "arms": ["fixed_cadence", "plasticity_guard"],
        "primary_endpoint": "paired_assessment_adaptation_improvement_plasticity_guard_minus_fixed_cadence",
        "primary_effect_threshold": PRIMARY_EFFECT_THRESHOLD,
        "training": {
            "fine_tune_type": "lora",
            "base_weights_updated": False,
            "adapter_merge": False,
            "reversible_adapter": True,
            "optimizer": "adamw",
            "learning_rate": TRAIN_LEARNING_RATE,
            "iters_per_update": TRAIN_ITERS,
            "rows_per_update": TRAIN_ROWS,
            "batch_size": TRAIN_BATCH_SIZE,
            "num_layers": TRAIN_NUM_LAYERS,
            "max_seq_length": TRAIN_MAX_SEQ_LENGTH,
            "lora_parameters": {"rank": 8, "dropout": 0.0, "scale": 20.0},
        },
        "plasticity_guard": {
            "current_gain_minimum_nll": MIN_CURRENT_GAIN,
            "protected_degradation_maximum_nll": MAX_PROTECTED_DEGRADATION,
            "protected_buffer": "previously_committed_fit_windows_only",
            "rollback": "candidate_pointer_not_committed; base_unchanged",
        },
        "hard_guards": {
            "max_forgetting_fraction": MAX_FORGETTING_FRACTION,
            "max_calibration_ece_delta": MAX_CALIBRATION_ECE_DELTA,
            "adapter_restore_tolerance": ADAPTER_RESTORE_TOLERANCE,
            "native_parity_tolerance": PARITY_TOLERANCE,
            "repeat_tolerance": REPEAT_TOLERANCE,
        },
        "bootstrap": {
            "seed": BOOTSTRAP_SEED,
            "replicates": BOOTSTRAP_REPLICATES,
            "unit": "case",
        },
        "network_access": False,
        "offline_environment": {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
        "astral_integration": {
            "status": "not_run",
            "permitted_only": ["causal_effect_prediction", "calibration", "instrumental_correction"],
            "introspection_claims": False,
        },
        "zk_pqc": {"status": "not_run", "fixture_receipts_are_not_cryptographic_evidence": True},
        "source_digests": {
            str(path.relative_to(REPO_ROOT)): sha256_file(path) for path in source_files
        },
    }


def qualification(root: Path, model_path: Path, fit_probe: Window, base_probe: dict[str, Any]) -> dict[str, Any]:
    qualification_root = root / "qualification"
    data = qualification_root / "data"
    adapter = qualification_root / "adapter"
    log_path = qualification_root / "training.log"
    write_training_dataset(data, fit_probe)
    training = run_training(model_path, data, adapter, 20260828, None, log_path, root)
    model, tokenizer, mx, policy = load_runtime(model_path)
    candidate_model, candidate_tokenizer, candidate_mx, _ = load_runtime(model_path, adapter)
    zero_adapter = qualification_root / "zero_adapter"
    make_zero_adapter(adapter, zero_adapter)
    zero_model, zero_tokenizer, zero_mx, _ = load_runtime(model_path, zero_adapter)
    restored_adapter = qualification_root / "restored_adapter"
    copy_adapter(adapter, restored_adapter)
    restored_model, restored_tokenizer, restored_mx, _ = load_runtime(model_path, restored_adapter)
    native_probe = probe_logits(model, tokenizer, mx, fit_probe)
    repeat_probe = probe_logits(*load_runtime(model_path)[:3], fit_probe)
    zero_probe = probe_logits(zero_model, zero_tokenizer, zero_mx, fit_probe)
    candidate_probe = probe_logits(candidate_model, candidate_tokenizer, candidate_mx, fit_probe)
    restored_probe = probe_logits(restored_model, restored_tokenizer, restored_mx, fit_probe)
    native_reload_delta = max_abs_delta(native_probe, repeat_probe, mx)
    zero_delta = max_abs_delta(native_probe, zero_probe, mx)
    candidate_delta = max_abs_delta(native_probe, candidate_probe, mx)
    restore_delta = max_abs_delta(candidate_probe, restored_probe, mx)
    base_eval = evaluate_windows(model, tokenizer, mx, [fit_probe])
    candidate_eval = evaluate_windows(candidate_model, candidate_tokenizer, candidate_mx, [fit_probe])
    return {
        "state_slice": STATE_SLICE,
        "model_policy": policy,
        "probe_document_id": fit_probe.document_id,
        "training": training,
        "native_reload_max_abs_logit_delta": round(native_reload_delta, 9),
        "zero_adapter_max_abs_logit_delta": round(zero_delta, 9),
        "candidate_max_abs_logit_delta": round(candidate_delta, 9),
        "adapter_restore_max_abs_logit_delta": round(restore_delta, 9),
        "base_probe_mean_nll": base_eval["mean_nll"],
        "candidate_probe_mean_nll": candidate_eval["mean_nll"],
        "native_reload_passed": native_reload_delta <= PARITY_TOLERANCE,
        "zero_adapter_passed": zero_delta <= PARITY_TOLERANCE,
        "candidate_nonzero_passed": candidate_delta > 1e-8,
        "adapter_restore_passed": restore_delta <= ADAPTER_RESTORE_TOLERANCE,
        "qualification_passed": (
            native_reload_delta <= PARITY_TOLERANCE
            and zero_delta <= PARITY_TOLERANCE
            and candidate_delta > 1e-8
            and restore_delta <= ADAPTER_RESTORE_TOLERANCE
        ),
    }


def run_campaign(primary_root: Path, daed_root: Path, input_path: Path, model_path: Path) -> dict[str, Any]:
    primary_root = volume_path(primary_root, PRIMARY_VOLUME, "PrimaryED artifact root")
    daed_root = volume_path(daed_root, DAED_VOLUME, "DAed mirror root")
    input_path = external_path(input_path, "NEWSROOM input")
    model_path = external_path(model_path, "cached model path")
    require_new_root(primary_root, "PrimaryED artifact root")
    require_new_root(daed_root, "DAed mirror root")
    if not input_path.is_file():
        raise FileNotFoundError(f"NEWSROOM input does not exist: {input_path}")
    if not model_path.is_dir():
        raise FileNotFoundError(f"cached model does not exist: {model_path}")
    primary_root.parent.mkdir(parents=True, exist_ok=True)
    daed_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{primary_root.name}.staging-", dir=primary_root.parent))
    try:
        before_manifest = model_manifest(model_path)
        raw_path = copy_raw_input(input_path, staging)
        tokenizer = load_tokenizer(model_path)
        selected = select_records(raw_path, tokenizer)
        input_manifest = write_input_manifest(staging, input_path, raw_path, selected)
        fit, tune, assessment, corpus_manifest = materialize_corpus(staging / "corpus", selected, tokenizer)
        base_model, base_tokenizer, base_mx, tokenizer_policy = load_runtime(model_path)
        if getattr(base_model.args, "model_type", None) != "gemma3_text":
            raise RuntimeError("cached checkpoint is not Gemma3 text")
        if len(base_model.model.layers) != 26 or getattr(base_model.args, "hidden_size", None) != 1152:
            raise RuntimeError("cached checkpoint shape contract failed")
        all_windows = [*fit, *tune, *assessment]
        base_all = evaluate_windows(base_model, base_tokenizer, base_mx, all_windows)
        base_by_id = {row["document_id"]: row for row in base_all["rows"]}
        base_metrics: dict[str, Any] = {}
        for window in all_windows:
            row = base_by_id[window.document_id]
            base_metrics[window.document_id] = {
                "mean_nll": row["nll"] / row["target_count"],
                "row": row,
            }
        base_metrics["__fit__"] = evaluate_windows(base_model, base_tokenizer, base_mx, fit)
        base_metrics["__tune__"] = evaluate_windows(base_model, base_tokenizer, base_mx, tune)
        base_metrics["__assessment__"] = evaluate_windows(base_model, base_tokenizer, base_mx, assessment)
        config = build_config(model_path, before_manifest["manifest_sha256"], input_manifest, corpus_manifest)
        config["tokenizer_policy_receipt"] = tokenizer_policy
        config["config_sha256"] = digest(config)
        write_json(staging / "config.json", config)
        qualification_result = qualification(staging, model_path, fit[0], base_metrics)
        write_json(staging / "qualification.json", qualification_result)
        if not qualification_result["qualification_passed"]:
            raise RuntimeError("cached-model qualification failed")
        case_results = []
        for seed in SEEDS:
            for order_name, order in ORDERS.items():
                for arm in ("fixed_cadence", "plasticity_guard"):
                    case_results.append(
                        train_case(
                            staging,
                            model_path,
                            base_metrics,
                            fit,
                            tune,
                            assessment,
                            seed,
                            order_name,
                            order,
                            arm,
                        )
                    )
        lock_body = {
            "state_slice": STATE_SLICE,
            "config_sha256": config["config_sha256"],
            "qualification_sha256": digest(qualification_result),
            "case_count": len(case_results),
            "cases": [
                {
                    "case": result["case"],
                    "arm": result["arm"],
                    "seed": result["seed"],
                    "order": result["order"],
                    "final_adapter": result["final_adapter"],
                    "updates": result["updates"],
                }
                for result in case_results
            ],
            "assessment_started": False,
        }
        prediction_lock = {"lock": lock_body, "lock_sha256": digest(lock_body)}
        write_json(staging / "prediction-lock.json", prediction_lock)
        assessment_results = []
        for result in case_results:
            final_adapter = staging / result["final_adapter"]
            final_eval = evaluate_adapter(model_path, final_adapter, assessment)
            final_repeat = evaluate_adapter(model_path, final_adapter, assessment)
            repeat_delta = abs(mean_nll(final_eval) - mean_nll(final_repeat))
            assessment_gain = mean_nll(base_metrics["__assessment__"]) - mean_nll(final_eval)
            updated = dict(result)
            updated.update(
                {
                    "assessment_after": final_eval,
                    "assessment_repeat": final_repeat,
                    "assessment_repeat_mean_nll_delta": round(repeat_delta, 9),
                    "assessment_adaptation_improvement": round(assessment_gain, 9),
                    "assessment_started": True,
                    "calibration_guard_passed": result["tune_ece_delta"] <= MAX_CALIBRATION_ECE_DELTA,
                    "forgetting_guard_passed": result["fit_forgetting_fraction"] <= MAX_FORGETTING_FRACTION,
                    "repeat_guard_passed": repeat_delta <= REPEAT_TOLERANCE,
                }
            )
            assessment_results.append(updated)
        by_case_arm = {(result["case"], result["arm"]): result for result in assessment_results}
        deltas = []
        wins = 0
        paired_rows = []
        for seed in SEEDS:
            for order_name in ORDERS:
                case = f"seed-{seed}-{order_name}"
                fixed = by_case_arm[(case, "fixed_cadence")]
                guarded = by_case_arm[(case, "plasticity_guard")]
                delta = guarded["assessment_adaptation_improvement"] - fixed["assessment_adaptation_improvement"]
                deltas.append(delta)
                wins += int(delta > 0)
                paired_rows.append({"case": case, "fixed": fixed["assessment_adaptation_improvement"], "plasticity_guard": guarded["assessment_adaptation_improvement"], "delta": round(delta, 9)})
        lower, upper = bootstrap_interval(deltas, BOOTSTRAP_SEED, BOOTSTRAP_REPLICATES)
        hard_guards_passed = all(
            result["calibration_guard_passed"]
            and result["forgetting_guard_passed"]
            and result["repeat_guard_passed"]
            for result in assessment_results
        )
        primary_passed = (
            sum(deltas) / len(deltas) >= PRIMARY_EFFECT_THRESHOLD
            and lower >= 0.0
            and wins >= PRIMARY_WIN_COUNT
            and hard_guards_passed
        )
        results = {
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "base_assessment": base_metrics["__assessment__"],
            "base_fit": base_metrics["__fit__"],
            "base_tune": base_metrics["__tune__"],
            "case_results": assessment_results,
            "primary_endpoint": {
                "name": "paired_assessment_adaptation_improvement_plasticity_guard_minus_fixed_cadence",
                "case_deltas": paired_rows,
                "mean_delta": round(sum(deltas) / len(deltas), 9),
                "bootstrap_seed": BOOTSTRAP_SEED,
                "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                "bootstrap_95_percent_interval": [round(lower, 9), round(upper, 9)],
                "positive_case_wins": wins,
                "effect_threshold": PRIMARY_EFFECT_THRESHOLD,
                "passed": primary_passed,
            },
            "hard_guards": {
                "all_passed": hard_guards_passed,
                "max_forgetting_fraction": MAX_FORGETTING_FRACTION,
                "max_calibration_ece_delta": MAX_CALIBRATION_ECE_DELTA,
                "repeat_tolerance": REPEAT_TOLERANCE,
            },
            "classification": "DevelopmentCandidate" if primary_passed else "DevelopmentNoCandidate",
            "astral_integration": "not_run",
            "zk_pqc": "not_run",
            "assessment_started_only_after_prediction_lock": True,
        }
        results["results_sha256"] = digest(results)
        write_json(staging / "results.json", results)
        after_manifest = model_manifest(model_path)
        if after_manifest != before_manifest:
            raise RuntimeError("cached base model manifest changed during adapter experiment")
        receipt = {
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "classification": results["classification"],
            "config_sha256": config["config_sha256"],
            "qualification_sha256": digest(qualification_result),
            "prediction_lock_sha256": prediction_lock["lock_sha256"],
            "results_sha256": results["results_sha256"],
            "model_manifest_sha256": after_manifest["manifest_sha256"],
            "corpus_manifest_sha256": corpus_manifest["manifest_sha256"],
            "network_access": False,
            "training": True,
            "weights_frozen": True,
            "adapter_only": True,
            "base_weights_unchanged": before_manifest == after_manifest,
            "qualification_passed": qualification_result["qualification_passed"],
            "hard_guards_passed": hard_guards_passed,
            "primary_endpoint_passed": primary_passed,
            "astral_integration": "not_run",
            "zk_pqc": "not_run",
        }
        receipt["receipt_sha256"] = digest(receipt)
        write_json(staging / "model-manifest.json", after_manifest)
        write_json(staging / "receipt.json", receipt)
        primary_root.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staging, primary_root)
        staging = primary_root
        validation = run_validator(primary_root, model_path)
        write_json(primary_root / "validator-receipt.json", validation)
        mirror_staging = Path(tempfile.mkdtemp(prefix=f".{daed_root.name}.staging-", dir=daed_root.parent))
        mirror_staging.rmdir()
        shutil.copytree(primary_root, mirror_staging)
        os.replace(mirror_staging, daed_root)
        mirror_validation = run_validator(daed_root, model_path)
        if artifact_file_manifest(primary_root)["files"] != artifact_file_manifest(daed_root)["files"]:
            raise RuntimeError("PrimaryED and DAed artifact manifests differ")
        return {"results": results, "receipt": receipt, "validation": validation, "mirror_validation": mirror_validation}
    finally:
        if staging.exists() and staging != primary_root:
            shutil.rmtree(staging)


def run_validator(root: Path, model_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-B", str(VALIDATOR), "--artifact-root", str(root), "--model", str(model_path)],
        env={**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"},
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"independent validator failed: {completed.stdout}\n{completed.stderr}")
    result = json.loads(completed.stdout)
    if result.get("valid") is not True:
        raise RuntimeError(f"independent validator rejected artifact: {result}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-root", type=Path, default=DEFAULT_PRIMARY_ROOT)
    parser.add_argument("--daed-root", type=Path, default=DEFAULT_DAED_ROOT)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    print(json.dumps(run_campaign(args.primary_root, args.daed_root, args.input, args.model), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
