#!/usr/bin/env python3
"""Run the fresh-cohort plasticity-guard replication.

State slice: continual-learning-plasticity-guard-replication-v1.

This replication adds an untouched-base/no-update comparator to the frozen
fixed-cadence and plasticity-guard arms. All arms spend the same LoRA update
budget; the no-update arm trains disposable shadow adapters and never applies
one. Base weights are never updated or merged.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning import plasticity_guard_reversible_adapter_v1 as v1

STATE_SLICE = "continual-learning-plasticity-guard-replication-v1"
CLAIM_CEILING = "LocalDevelopmentPlasticityGuardReplication"
DEFAULT_MODEL = v1.DEFAULT_MODEL
DEFAULT_INPUT = v1.DEFAULT_INPUT
PRIMARY_VOLUME = v1.PRIMARY_VOLUME
DAED_VOLUME = v1.DAED_VOLUME
DEFAULT_PRIMARY_ROOT = PRIMARY_VOLUME / (
    "ResearchArtifacts/composed-zk-benchmark-os/"
    "continual-learning-plasticity-guard-replication-v1-20260828-r1"
)
DEFAULT_DAED_ROOT = DAED_VOLUME / (
    "Archives/composed-zk-benchmark-os/"
    "continual-learning-plasticity-guard-replication-v1-20260828-r1"
)
VALIDATOR = Path(__file__).with_name("validate_plasticity_guard_replication_v1.py")

PRIOR_STATE_SLICE = "continual-learning-plasticity-guard-reversible-adapter-v1"
PRIOR_PRIMARY_ROOT = PRIMARY_VOLUME / (
    "ResearchArtifacts/composed-zk-benchmark-os/"
    "continual-learning-plasticity-guard-reversible-adapter-v1-20260828-r1"
)
PRIOR_RESULTS_DIGEST = "46d0654b199205b2957e5a1fb758c1989c377db7d6ab86eaa0f6440de3bd8316"
PRIOR_RECEIPT_DIGEST = "ed707b95864627dbefb00b277dda41bc23ec6ecaa51f36677ff503c0be6798b6"
PRIOR_RESULTS_FILE_SHA256 = "e2c15c2bafa0e6fa1fc5519267ccd51a1d0dabcabf551596b3b7e8a8426aa4ed"
PRIOR_RECEIPT_FILE_SHA256 = "569d1b7f340867f8cd52803c4ff6be0ca09be55e02f18121189a8d9dd84b7a02"

WINDOW_TOKENS = v1.WINDOW_TOKENS
PRIOR_SELECTION_OFFSET = 8
PRIOR_SELECTED_DOCUMENT_COUNT = 12
SELECTION_OFFSET = 20
SELECTED_DOCUMENT_COUNT = 12
FIT_DOCUMENT_COUNT = 6
TUNE_DOCUMENT_COUNT = 3
ASSESSMENT_DOCUMENT_COUNT = 3
SEEDS = (1747, 1749)
ORDERS = {
    "interleave": (0, 3, 1, 4, 2, 5),
    "outer_in": (0, 5, 1, 4, 2, 3),
}
ARMS = ("no_update", "fixed_cadence", "plasticity_guard")
TRAIN_ITERS = v1.TRAIN_ITERS
TRAIN_ROWS = v1.TRAIN_ROWS
TRAIN_NUM_LAYERS = v1.TRAIN_NUM_LAYERS
TRAIN_BATCH_SIZE = v1.TRAIN_BATCH_SIZE
TRAIN_LEARNING_RATE = v1.TRAIN_LEARNING_RATE
TRAIN_MAX_SEQ_LENGTH = v1.TRAIN_MAX_SEQ_LENGTH
MIN_CURRENT_GAIN = v1.MIN_CURRENT_GAIN
MAX_PROTECTED_DEGRADATION = v1.MAX_PROTECTED_DEGRADATION
MAX_FORGETTING_FRACTION = v1.MAX_FORGETTING_FRACTION
MAX_CALIBRATION_ECE_DELTA = v1.MAX_CALIBRATION_ECE_DELTA
PARITY_TOLERANCE = v1.PARITY_TOLERANCE
REPEAT_TOLERANCE = v1.REPEAT_TOLERANCE
ADAPTER_RESTORE_TOLERANCE = v1.ADAPTER_RESTORE_TOLERANCE
ABSOLUTE_EFFECT_THRESHOLD = 0.010
SECONDARY_EFFECT_THRESHOLD = 0.010
PRIMARY_WIN_COUNT = 3
BOOTSTRAP_SEED = 20260829
BOOTSTRAP_REPLICATES = 10_000
NEWSROOM_UPSTREAM = v1.NEWSROOM_UPSTREAM
SOURCE_SCHEMA = "gemma3-newsroom-plasticity-guard-replication-input-v1"
CORPUS_SCHEMA = "gemma3-newsroom-plasticity-guard-replication-corpus-v1"
SELECTION_POLICY = "next-twelve-after-twenty-eligible-newsroom-test-records-v4"

Window = v1.Window
artifact_file_manifest = v1.artifact_file_manifest
copy_adapter = v1.copy_adapter
copy_raw_input = v1.copy_raw_input
evaluate_windows = v1.evaluate_windows
expected_calibration_error = v1.expected_calibration_error
external_path = v1.external_path
load_runtime = v1.load_runtime
load_tokenizer = v1.load_tokenizer
make_zero_adapter = v1.make_zero_adapter
max_abs_delta = v1.max_abs_delta
model_manifest = v1.model_manifest
package_version = v1.package_version
probe_logits = v1.probe_logits
run_training = v1.run_training
sha256_file = v1.sha256_file
training_command = v1.training_command
write_training_dataset = v1.write_training_dataset


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def select_records(input_path: Path, tokenizer: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    eligible: list[dict[str, Any]] = []
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
        eligible.append(
            {
                "line_number": line_number,
                "document_id": f"newsroom-test-line-{line_number:07d}",
                "url": url,
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "token_count": len(token_ids),
                "token_ids": token_ids[:WINDOW_TOKENS],
            }
        )
        if len(eligible) == SELECTION_OFFSET + SELECTED_DOCUMENT_COUNT:
            break
    required = SELECTION_OFFSET + SELECTED_DOCUMENT_COUNT
    if len(eligible) != required:
        raise ValueError(f"NEWSROOM input yielded {len(eligible)} eligible records; expected {required}")
    prior = eligible[PRIOR_SELECTION_OFFSET : PRIOR_SELECTION_OFFSET + PRIOR_SELECTED_DOCUMENT_COUNT]
    selected = eligible[SELECTION_OFFSET : SELECTION_OFFSET + SELECTED_DOCUMENT_COUNT]
    if {item["document_id"] for item in prior} & {item["document_id"] for item in selected}:
        raise ValueError("fresh replication cohort overlaps the frozen prior cohort")
    return selected, prior


def materialize_corpus(
    root: Path, selected: list[dict[str, Any]], tokenizer: Any
) -> tuple[list[Window], list[Window], list[Window], dict[str, Any]]:
    splits = (
        ("fit", FIT_DOCUMENT_COUNT),
        ("tune", TUNE_DOCUMENT_COUNT),
        ("assessment", ASSESSMENT_DOCUMENT_COUNT),
    )
    windows: dict[str, list[Window]] = {name: [] for name, _ in splits}
    entries: dict[str, list[dict[str, Any]]] = {name: [] for name, _ in splits}
    offset = 0
    for split, count in splits:
        for _local_index in range(count):
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
                text_sha256=hashlib.sha256(raw).hexdigest(),
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


def write_input_manifest(
    root: Path,
    input_path: Path,
    raw_path: Path,
    selected: list[dict[str, Any]],
    prior: list[dict[str, Any]],
) -> dict[str, Any]:
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
        "prior_frozen_selection": {
            "state_slice": PRIOR_STATE_SLICE,
            "selection_offset": PRIOR_SELECTION_OFFSET,
            "selected_document_count": PRIOR_SELECTED_DOCUMENT_COUNT,
            "document_ids": [row["document_id"] for row in prior],
        },
        "selected_documents": [
            {key: value for key, value in row.items() if key != "token_ids"}
            for row in selected
        ],
    }
    manifest = {"manifest": body, "manifest_sha256": digest(body)}
    write_json(root / "input-manifest.json", manifest)
    return manifest


def mean_nll(metrics: dict[str, Any]) -> float:
    return float(metrics["mean_nll"])


def plasticity_guard_accept(step: int, current_gain: float, protected_delta: float) -> bool:
    """Use the frozen V1 guard thresholds without post-result tuning."""

    return v1.plasticity_guard_accept(step, current_gain, protected_delta)


def bootstrap_interval(values: Sequence[float], seed: int, replicates: int) -> tuple[float, float]:
    return v1.bootstrap_interval(values, seed, replicates)


def evaluate_adapter_or_base(
    model_path: Path, adapter_path: Path | None, windows: Sequence[Window]
) -> dict[str, Any]:
    model, tokenizer, mx, _policy = load_runtime(model_path, adapter_path)
    return evaluate_windows(model, tokenizer, mx, windows)


def verify_frozen_prior() -> dict[str, Any]:
    root = PRIOR_PRIMARY_ROOT.resolve()
    if not root.is_dir() or root.is_symlink():
        raise FileNotFoundError(f"frozen prior artifact root is missing: {root}")
    results_path = root / "results.json"
    receipt_path = root / "receipt.json"
    if sha256_file(results_path) != PRIOR_RESULTS_FILE_SHA256:
        raise ValueError("frozen prior results digest changed")
    if sha256_file(receipt_path) != PRIOR_RECEIPT_FILE_SHA256:
        raise ValueError("frozen prior receipt digest changed")
    results = json.loads(results_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if results.get("state_slice") != PRIOR_STATE_SLICE or receipt.get("state_slice") != PRIOR_STATE_SLICE:
        raise ValueError("frozen prior state slice mismatch")
    if results.get("results_sha256") != PRIOR_RESULTS_DIGEST or receipt.get("receipt_sha256") != PRIOR_RECEIPT_DIGEST:
        raise ValueError("frozen prior body digest changed")
    if receipt.get("base_weights_unchanged") is not True:
        raise ValueError("frozen prior did not prove base-weight immutability")
    return {
        "state_slice": PRIOR_STATE_SLICE,
        "artifact_root": str(root),
        "results_sha256": PRIOR_RESULTS_DIGEST,
        "receipt_sha256": PRIOR_RECEIPT_DIGEST,
        "results_file_sha256": PRIOR_RESULTS_FILE_SHA256,
        "receipt_file_sha256": PRIOR_RECEIPT_FILE_SHA256,
        "classification": results.get("classification"),
        "primary_mean_delta": results.get("primary_endpoint", {}).get("mean_delta"),
    }


def build_config(
    model_path: Path,
    model_digest: str,
    input_manifest: dict[str, Any],
    corpus_manifest: dict[str, Any],
    prior_receipt: dict[str, Any],
) -> dict[str, Any]:
    source_files = [
        Path(__file__),
        Path(__file__).with_name("plasticity_guard_reversible_adapter_v1.py"),
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
        "prior_frozen_result": prior_receipt,
        "selection_offset": SELECTION_OFFSET,
        "window_token_count": WINDOW_TOKENS,
        "split_counts": {
            "fit": FIT_DOCUMENT_COUNT,
            "tune": TUNE_DOCUMENT_COUNT,
            "assessment": ASSESSMENT_DOCUMENT_COUNT,
        },
        "seeds": list(SEEDS),
        "orders": {name: list(order) for name, order in ORDERS.items()},
        "arms": list(ARMS),
        "primary_endpoint": {
            "name": "absolute_assessment_adaptation_improvement_plasticity_guard_vs_untouched_base",
            "effect_threshold": ABSOLUTE_EFFECT_THRESHOLD,
            "win_count": PRIMARY_WIN_COUNT,
        },
        "secondary_endpoint": {
            "name": "paired_assessment_adaptation_improvement_plasticity_guard_minus_fixed_cadence",
            "effect_threshold": SECONDARY_EFFECT_THRESHOLD,
            "win_count": PRIMARY_WIN_COUNT,
        },
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
            "updates_per_case": FIT_DOCUMENT_COUNT,
            "lora_parameters": {"rank": 8, "dropout": 0.0, "scale": 20.0},
            "no_update_equal_compute": "disposable_shadow_adapter_chain; never applied",
        },
        "plasticity_guard": {
            "current_gain_minimum_nll": MIN_CURRENT_GAIN,
            "protected_degradation_maximum_nll": MAX_PROTECTED_DEGRADATION,
            "protected_buffer": "previously_committed_fit_windows_only",
            "rollback": "candidate_pointer_not_committed; base_unchanged",
            "thresholds_frozen_from": PRIOR_STATE_SLICE,
        },
        "hard_guards": {
            "max_forgetting_fraction": MAX_FORGETTING_FRACTION,
            "max_calibration_ece_delta": MAX_CALIBRATION_ECE_DELTA,
            "adapter_restore_tolerance": ADAPTER_RESTORE_TOLERANCE,
            "native_parity_tolerance": PARITY_TOLERANCE,
            "repeat_tolerance": REPEAT_TOLERANCE,
            "no_update_base_equivalence_tolerance": REPEAT_TOLERANCE,
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


def qualification(root: Path, model_path: Path, fit_probe: Window) -> dict[str, Any]:
    qualification_root = root / "qualification"
    data = qualification_root / "data"
    adapter = qualification_root / "adapter"
    log_path = qualification_root / "training.log"
    write_training_dataset(data, fit_probe)
    training = run_training(model_path, data, adapter, 20260829, None, log_path, root)
    model, tokenizer, mx, policy = load_runtime(model_path)
    candidate_model, candidate_tokenizer, candidate_mx, _ = load_runtime(model_path, adapter)
    zero_adapter = qualification_root / "zero_adapter"
    make_zero_adapter(adapter, zero_adapter)
    zero_model, zero_tokenizer, zero_mx, _ = load_runtime(model_path, zero_adapter)
    restored_adapter = qualification_root / "restored_adapter"
    copy_adapter(adapter, restored_adapter)
    restored_model, restored_tokenizer, restored_mx, _ = load_runtime(model_path, restored_adapter)
    native_probe = probe_logits(model, tokenizer, mx, fit_probe)
    reload_model, reload_tokenizer, reload_mx, _ = load_runtime(model_path)
    repeat_probe = probe_logits(reload_model, reload_tokenizer, reload_mx, fit_probe)
    zero_probe = probe_logits(zero_model, zero_tokenizer, zero_mx, fit_probe)
    candidate_probe = probe_logits(candidate_model, candidate_tokenizer, candidate_mx, fit_probe)
    restored_probe = probe_logits(restored_model, restored_tokenizer, restored_mx, fit_probe)
    native_reload_delta = max_abs_delta(native_probe, repeat_probe, mx)
    zero_delta = max_abs_delta(native_probe, zero_probe, mx)
    candidate_delta = max_abs_delta(native_probe, candidate_probe, mx)
    restore_delta = max_abs_delta(candidate_probe, restored_probe, mx)
    return {
        "state_slice": STATE_SLICE,
        "model_policy": policy,
        "probe_document_id": fit_probe.document_id,
        "training": training,
        "native_reload_max_abs_logit_delta": round(native_reload_delta, 9),
        "zero_adapter_max_abs_logit_delta": round(zero_delta, 9),
        "candidate_max_abs_logit_delta": round(candidate_delta, 9),
        "adapter_restore_max_abs_logit_delta": round(restore_delta, 9),
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


def train_case(
    root: Path,
    model_path: Path,
    base_metrics: dict[str, dict[str, Any]],
    fit: Sequence[Window],
    tune: Sequence[Window],
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
    shadow_adapter: Path | None = None
    protected: list[Window] = []
    updates = []
    for step, fit_index in enumerate(order):
        current = fit[fit_index]
        dataset = data_root / f"step-{step}"
        write_training_dataset(dataset, current)
        candidate = adapter_root / f"step-{step}"
        resume_source = active_adapter if arm != "no_update" else shadow_adapter
        resume_file = resume_source / "adapters.safetensors" if resume_source else None
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
        before_adapter = active_adapter if arm != "no_update" else None
        before_eval = evaluate_adapter_or_base(model_path, before_adapter, before_windows)
        before_rows = {row["document_id"]: row for row in before_eval["rows"]}
        before_metrics = {
            document_id: float(row["nll"]) / float(row["target_count"])
            for document_id, row in before_rows.items()
        }
        candidate_eval = evaluate_adapter_or_base(model_path, candidate, before_windows)
        candidate_rows = {row["document_id"]: row for row in candidate_eval["rows"]}
        current_before = before_metrics[current.document_id]
        current_after = float(candidate_rows[current.document_id]["nll"]) / float(
            candidate_rows[current.document_id]["target_count"]
        )
        current_gain = current_before - current_after
        protected_before = 0.0
        protected_after = 0.0
        protected_delta = 0.0
        if protected:
            protected_before = sum(before_metrics[window.document_id] for window in protected) / len(protected)
            protected_after = sum(
                float(candidate_rows[window.document_id]["nll"])
                / float(candidate_rows[window.document_id]["target_count"])
                for window in protected
            ) / len(protected)
            protected_delta = protected_after - protected_before
        guard_would_accept = plasticity_guard_accept(step, current_gain, protected_delta)
        previous_adapter = active_adapter
        if arm == "no_update":
            decision = "discard"
            committed = False
            shadow_adapter = candidate
        else:
            committed = arm == "fixed_cadence" or guard_would_accept
            decision = "commit" if committed else "rollback"
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
                "decision": decision,
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
    final_adapter = active_adapter
    final_fit = evaluate_adapter_or_base(model_path, final_adapter, fit)
    final_tune = evaluate_adapter_or_base(model_path, final_adapter, tune)
    base_fit = evaluate_adapter_or_base(model_path, None, fit)
    fit_forgetting_delta = mean_nll(final_fit) - mean_nll(base_fit)
    fit_forgetting_fraction = fit_forgetting_delta / mean_nll(base_fit)
    return {
        "state_slice": STATE_SLICE,
        "case": case_name,
        "seed": seed,
        "order_name": order_name,
        "order": list(order),
        "arm": arm,
        "final_adapter": final_adapter.relative_to(root).as_posix() if final_adapter else None,
        "final_model_reference": "untouched_base" if final_adapter is None else "reversible_adapter_pointer",
        "updates": updates,
        "commit_count": sum(update["decision"] == "commit" for update in updates),
        "rollback_count": sum(update["decision"] == "rollback" for update in updates),
        "discard_count": sum(update["decision"] == "discard" for update in updates),
        "fit_after": final_fit,
        "tune_after": final_tune,
        "fit_forgetting_delta": round(fit_forgetting_delta, 9),
        "fit_forgetting_fraction": round(fit_forgetting_fraction, 9),
        "tune_ece_delta": round(float(final_tune["ece"]) - float(base_metrics["__tune__"]["ece"]), 9),
        "assessment_started": False,
    }


def classify_replication(primary_passed: bool, secondary_passed: bool) -> str:
    if primary_passed and secondary_passed:
        return "DevelopmentCandidate"
    if secondary_passed and not primary_passed:
        return "RollbackInfrastructureOnly"
    return "ReplicationFailureClosed"


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


def run_campaign(primary_root: Path, daed_root: Path, input_path: Path, model_path: Path) -> dict[str, Any]:
    primary_root = volume_path(primary_root, PRIMARY_VOLUME, "PrimaryED artifact root")
    daed_root = volume_path(daed_root, DAED_VOLUME, "DAed mirror root")
    input_path = external_path(input_path, "NEWSROOM input")
    model_path = external_path(model_path, "cached model path")
    require_new_root(primary_root, "PrimaryED artifact root")
    require_new_root(daed_root, "DAed mirror root")
    if not input_path.is_file() or not model_path.is_dir():
        raise FileNotFoundError("fresh replication input or cached model is missing")
    prior_receipt = verify_frozen_prior()
    primary_root.parent.mkdir(parents=True, exist_ok=True)
    daed_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{primary_root.name}.staging-", dir=primary_root.parent))
    try:
        before_manifest = model_manifest(model_path)
        raw_path = copy_raw_input(input_path, staging)
        tokenizer = load_tokenizer(model_path)
        selected, prior = select_records(raw_path, tokenizer)
        input_manifest = write_input_manifest(staging, input_path, raw_path, selected, prior)
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
                "mean_nll": float(row["nll"]) / float(row["target_count"]),
                "row": row,
            }
        base_metrics["__fit__"] = evaluate_windows(base_model, base_tokenizer, base_mx, fit)
        base_metrics["__tune__"] = evaluate_windows(base_model, base_tokenizer, base_mx, tune)
        base_metrics["__assessment__"] = evaluate_windows(base_model, base_tokenizer, base_mx, assessment)
        config = build_config(model_path, before_manifest["manifest_sha256"], input_manifest, corpus_manifest, prior_receipt)
        config["tokenizer_policy_receipt"] = tokenizer_policy
        config["config_sha256"] = digest(config)
        write_json(staging / "config.json", config)
        qualification_result = qualification(staging, model_path, fit[0])
        write_json(staging / "qualification.json", qualification_result)
        if not qualification_result["qualification_passed"]:
            raise RuntimeError("cached-model qualification failed")
        case_results = []
        for seed in SEEDS:
            for order_name, order in ORDERS.items():
                for arm in ARMS:
                    case_results.append(train_case(staging, model_path, base_metrics, fit, tune, seed, order_name, order, arm))
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
            final_adapter = staging / result["final_adapter"] if result["final_adapter"] else None
            final_eval = evaluate_adapter_or_base(model_path, final_adapter, assessment)
            final_repeat = evaluate_adapter_or_base(model_path, final_adapter, assessment)
            repeat_delta = abs(mean_nll(final_eval) - mean_nll(final_repeat))
            assessment_gain = mean_nll(base_metrics["__assessment__"]) - mean_nll(final_eval)
            base_equivalence_delta = (
                abs(mean_nll(final_eval) - mean_nll(base_metrics["__assessment__"]))
                if result["arm"] == "no_update"
                else None
            )
            updated = dict(result)
            updated.update(
                {
                    "assessment_after": final_eval,
                    "assessment_repeat": final_repeat,
                    "assessment_repeat_mean_nll_delta": round(repeat_delta, 9),
                    "assessment_adaptation_improvement": round(assessment_gain, 9),
                    "assessment_started": True,
                    "base_equivalence_mean_nll_delta": round(base_equivalence_delta, 9) if base_equivalence_delta is not None else None,
                    "base_equivalence_passed": result["arm"] != "no_update" or base_equivalence_delta <= REPEAT_TOLERANCE,
                    "calibration_guard_passed": result["tune_ece_delta"] <= MAX_CALIBRATION_ECE_DELTA,
                    "forgetting_guard_passed": result["fit_forgetting_fraction"] <= MAX_FORGETTING_FRACTION,
                    "repeat_guard_passed": repeat_delta <= REPEAT_TOLERANCE,
                }
            )
            assessment_results.append(updated)
        by_key = {(result["seed"], result["order_name"], result["arm"]): result for result in assessment_results}
        guard_gains = []
        guard_vs_no_update = []
        guard_vs_fixed = []
        primary_rows = []
        secondary_rows = []
        for seed in SEEDS:
            for order_name in ORDERS:
                key = (seed, order_name)
                no_update = by_key[(*key, "no_update")]
                fixed = by_key[(*key, "fixed_cadence")]
                guarded = by_key[(*key, "plasticity_guard")]
                guard_gain = float(guarded["assessment_adaptation_improvement"])
                no_update_gain = float(no_update["assessment_adaptation_improvement"])
                fixed_gain = float(fixed["assessment_adaptation_improvement"])
                delta_no_update = guard_gain - no_update_gain
                delta_fixed = guard_gain - fixed_gain
                guard_gains.append(guard_gain)
                guard_vs_no_update.append(delta_no_update)
                guard_vs_fixed.append(delta_fixed)
                case_name = f"seed-{seed}-{order_name}"
                primary_rows.append({"case": case_name, "plasticity_guard": guard_gain, "no_update": no_update_gain, "delta": round(delta_no_update, 9)})
                secondary_rows.append({"case": case_name, "fixed": fixed_gain, "plasticity_guard": guard_gain, "delta": round(delta_fixed, 9)})
        primary_lower, primary_upper = bootstrap_interval(guard_gains, BOOTSTRAP_SEED, BOOTSTRAP_REPLICATES)
        secondary_lower, secondary_upper = bootstrap_interval(guard_vs_fixed, BOOTSTRAP_SEED, BOOTSTRAP_REPLICATES)
        primary_wins = sum(delta > 0 for delta in guard_vs_no_update)
        secondary_wins = sum(delta > 0 for delta in guard_vs_fixed)
        hard_guards_passed = all(
            result["calibration_guard_passed"]
            and result["forgetting_guard_passed"]
            and result["repeat_guard_passed"]
            and result["base_equivalence_passed"]
            for result in assessment_results
        )
        primary_passed = (
            sum(guard_gains) / len(guard_gains) >= ABSOLUTE_EFFECT_THRESHOLD
            and primary_lower >= 0.0
            and primary_wins >= PRIMARY_WIN_COUNT
            and hard_guards_passed
        )
        secondary_passed = (
            sum(guard_vs_fixed) / len(guard_vs_fixed) >= SECONDARY_EFFECT_THRESHOLD
            and secondary_lower >= 0.0
            and secondary_wins >= PRIMARY_WIN_COUNT
        )
        classification = classify_replication(primary_passed, secondary_passed)
        results = {
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "base_assessment": base_metrics["__assessment__"],
            "base_fit": base_metrics["__fit__"],
            "base_tune": base_metrics["__tune__"],
            "case_results": assessment_results,
            "primary_endpoint": {
                "name": "absolute_assessment_adaptation_improvement_plasticity_guard_vs_untouched_base",
                "case_values": primary_rows,
                "mean_guard_gain": round(sum(guard_gains) / len(guard_gains), 9),
                "bootstrap_seed": BOOTSTRAP_SEED,
                "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                "bootstrap_95_percent_interval": [round(primary_lower, 9), round(primary_upper, 9)],
                "positive_case_wins_vs_no_update": primary_wins,
                "effect_threshold": ABSOLUTE_EFFECT_THRESHOLD,
                "passed": primary_passed,
            },
            "secondary_endpoint": {
                "name": "paired_assessment_adaptation_improvement_plasticity_guard_minus_fixed_cadence",
                "case_deltas": secondary_rows,
                "mean_delta": round(sum(guard_vs_fixed) / len(guard_vs_fixed), 9),
                "bootstrap_seed": BOOTSTRAP_SEED,
                "bootstrap_replicates": BOOTSTRAP_REPLICATES,
                "bootstrap_95_percent_interval": [round(secondary_lower, 9), round(secondary_upper, 9)],
                "positive_case_wins": secondary_wins,
                "effect_threshold": SECONDARY_EFFECT_THRESHOLD,
                "passed": secondary_passed,
            },
            "hard_guards": {
                "all_passed": hard_guards_passed,
                "max_forgetting_fraction": MAX_FORGETTING_FRACTION,
                "max_calibration_ece_delta": MAX_CALIBRATION_ECE_DELTA,
                "repeat_tolerance": REPEAT_TOLERANCE,
                "no_update_base_equivalence_tolerance": REPEAT_TOLERANCE,
            },
            "classification": classification,
            "decision_rule": (
                "guard_beats_no_update_and_fixed"
                if classification == "DevelopmentCandidate"
                else "guard_beats_fixed_but_not_no_update"
                if classification == "RollbackInfrastructureOnly"
                else "replication_failed_mechanism_closed"
            ),
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
            "classification": classification,
            "decision_rule": results["decision_rule"],
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
            "secondary_endpoint_passed": secondary_passed,
            "astral_integration": "not_run",
            "zk_pqc": "not_run",
        }
        receipt["receipt_sha256"] = digest(receipt)
        write_json(staging / "model-manifest.json", after_manifest)
        write_json(staging / "receipt.json", receipt)
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
