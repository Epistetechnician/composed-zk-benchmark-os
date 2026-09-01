#!/usr/bin/env python3
"""Stage and run the bounded OpenWebText Gemma3 recirculation substitute.

State slice: continual-learning-gemma3-paper-recirculation-openwebtext-substitute-v1.

This runner consumes only the independently validated external OpenWebText
source bundle. It stages document-disjoint 1024-token windows, runs the
cached Gemma3 1B BF16 MLX checkpoint offline with frozen weights, and invokes
the separate result validator. It is a local substitute pilot, not an exact
TFDS ``c4/webtextlike`` replication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_VOLUME = Path("/Volumes/PrimaryED")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning import gemma3_paper_recirculation_v1 as engine
from experiments.continual_learning.validate_gemma3_openwebtext_substitute_v1 import (
    ASSESSMENT_WINDOW_COUNT,
    CLAIM_CEILING,
    CORPUS_SCHEMA,
    FIT_WINDOW_COUNT,
    PARITY_TOLERANCE,
    PILOT_PAIRS,
    RESULT_SCHEMA,
    SOURCE_SCHEMA,
    STATE_SLICE,
    WINDOW_TOKENS,
    validate_corpus,
    validate_result,
    validate_source,
)

RAW_SOURCE_FILES = {
    "fit/openwebtext": Path("fit/openwebtext.jsonl"),
    "assessment/openwebtext": Path("assessment/openwebtext.jsonl"),
}
SELECTION_POLICY = "first-sixteen-full-1024-token-windows-per-disjoint-row-range-v1"
FIT_ALPHA = 0.10
EVALUATION_ALPHA = 0.15
EVALUATION_BETA = 0.85
TEMPERATURE_CONTROL = 1.2
DEFAULT_MODEL = Path(
    "/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16"
)
DEFAULT_SOURCE_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-openwebtext-substitute-source-v1"
)
DEFAULT_CORPUS_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-openwebtext-substitute-corpus-v1"
)
DEFAULT_OUTPUT_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "gemma3-openwebtext-substitute-recirculation-v1"
)
VALIDATOR = Path(__file__).with_name("validate_gemma3_openwebtext_substitute_v1.py")


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


def _external(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    repository = REPO_ROOT.resolve()
    if resolved == repository or repository in resolved.parents:
        raise ValueError(f"{label} must be outside the repository: {resolved}")
    return resolved


def _primary(path: Path, label: str) -> Path:
    resolved = _external(path, label)
    volume = PRIMARY_VOLUME.resolve()
    if not volume.is_dir():
        raise FileNotFoundError(f"required external volume is not mounted: {volume}")
    if resolved != volume and volume not in resolved.parents:
        raise ValueError(f"{label} must be under {volume}: {resolved}")
    return resolved


def _regular(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file: {path}")
    return path


def _read_json(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(_regular(path, label).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _read_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    rows = []
    with _regular(path, label).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{label} has a blank line at {line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{label} line {line_number} is not an object")
            rows.append(value)
    return rows


def _load_tokenizer(model_path: Path) -> Any:
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


def _window_from_row(
    tokenizer: Any,
    split: str,
    ordinal: int,
    row: dict[str, Any],
    relative_path: Path,
) -> tuple[engine.CorpusWindow | None, dict[str, Any]]:
    document_id = row.get("document_id")
    text = row.get("text")
    if not isinstance(document_id, str) or not document_id:
        raise ValueError(f"{split} row {ordinal} has invalid document_id")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{split} row {ordinal} has empty text")
    token_ids = list(tokenizer.encode(text, add_special_tokens=False))
    if len(token_ids) < WINDOW_TOKENS:
        return None, {
            "document_id": document_id,
            "token_count": len(token_ids),
            "reason": "shorter_than_fixed_1024_token_window",
        }
    selected_ids = token_ids[:WINDOW_TOKENS]
    window_text = tokenizer.decode(selected_ids)
    if list(tokenizer.encode(window_text, add_special_tokens=False)) != selected_ids:
        raise ValueError(f"tokenizer round-trip changed window: {document_id}")
    window_bytes = window_text.encode("utf-8")
    return (
        engine.CorpusWindow(
            dataset="openwebtext",
            document_id=document_id,
            relative_path=relative_path.as_posix(),
            window_ordinal=0,
            text=window_text,
            byte_len=len(window_bytes),
            source_sha256=sha256_bytes(text.encode("utf-8")),
            text_sha256=sha256_bytes(window_bytes),
            token_count=WINDOW_TOKENS,
        ),
        {},
    )


def stage_corpus(source_root: Path, corpus_root: Path, model_path: Path) -> dict[str, Any]:
    source_root = _primary(source_root, "source root")
    corpus_root = _primary(corpus_root, "corpus root")
    model_path = _external(model_path, "model path")
    if corpus_root.exists() or corpus_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite corpus root: {corpus_root}")
    if not model_path.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model_path}")
    source_validation = validate_source(source_root)
    source_manifest = _read_json(source_root / "acquisition-manifest.json", "source manifest")
    tokenizer = _load_tokenizer(model_path)
    staging = Path(tempfile.mkdtemp(prefix=f".{corpus_root.name}.staging-", dir=corpus_root.parent))
    try:
        windows: dict[str, list[engine.CorpusWindow]] = {"fit": [], "assessment": []}
        entries: dict[str, list[dict[str, Any]]] = {"fit": [], "assessment": []}
        excluded: dict[str, list[dict[str, Any]]] = {"fit": [], "assessment": []}
        deferred: dict[str, int] = {"fit": 0, "assessment": 0}
        for split, key, target in (
            ("fit", "fit/openwebtext", FIT_WINDOW_COUNT),
            ("assessment", "assessment/openwebtext", ASSESSMENT_WINDOW_COUNT),
        ):
            metadata = source_manifest["datasets"][key]
            path = _regular(source_root / metadata["normalized_path"], f"normalized {key}")
            rows = _read_jsonl(path, f"normalized {key}")
            for ordinal, row in enumerate(rows):
                relative = Path(split) / "openwebtext" / f"window-{len(windows[split]):06d}.txt"
                window, skipped = _window_from_row(tokenizer, split, ordinal, row, relative)
                if window is None:
                    excluded[split].append(skipped)
                    continue
                if len(windows[split]) >= target:
                    deferred[split] += 1
                    continue
                output_path = staging / relative
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(window.text, encoding="utf-8")
                windows[split].append(window)
                entries[split].append(
                    {
                        "dataset": window.dataset,
                        "document_id": window.document_id,
                        "path": window.relative_path,
                        "window_ordinal": window.window_ordinal,
                        "byte_len": window.byte_len,
                        "source_sha256": window.source_sha256,
                        "text_sha256": window.text_sha256,
                        "token_count": window.token_count,
                    }
                )
                if len(windows[split]) == target:
                    deferred[split] = len(rows) - ordinal - 1
                    break
            if len(windows[split]) != target:
                raise ValueError(
                    f"{split} has only {len(windows[split])} eligible 1024-token windows; expected {target}"
                )
        body = {
            "schema": CORPUS_SCHEMA,
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "window_token_count": WINDOW_TOKENS,
            "source_manifest_sha256": source_manifest["manifest_sha256"],
            "selection_policy": SELECTION_POLICY,
            "fit": entries["fit"],
            "assessment": entries["assessment"],
            "fit_window_count": len(windows["fit"]),
            "assessment_window_count": len(windows["assessment"]),
            "excluded_short_records": excluded,
            "deferred_record_count": deferred,
            "network_access": False,
            "training": False,
        }
        manifest = {**body, "manifest_sha256": digest(body)}
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        receipt = {
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "source_manifest_sha256": source_manifest["manifest_sha256"],
            "corpus_manifest_sha256": manifest["manifest_sha256"],
            "fit_window_count": FIT_WINDOW_COUNT,
            "assessment_window_count": ASSESSMENT_WINDOW_COUNT,
            "window_token_count": WINDOW_TOKENS,
            "network_access": False,
            "training": False,
        }
        receipt["receipt_sha256"] = digest(receipt)
        (staging / "staging-receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        validate_corpus(staging, source_manifest["manifest_sha256"])
        os.replace(staging, corpus_root)
        return {"source_validation": source_validation, "staging_receipt": receipt}
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def _run_validator(result_root: Path, corpus_manifest_sha256: str, model_path: Path) -> dict[str, Any]:
    validator_env = os.environ.copy()
    existing_pythonpath = validator_env.get("PYTHONPATH")
    validator_env["PYTHONPATH"] = os.pathsep.join(
        value for value in (str(REPO_ROOT), existing_pythonpath) if value
    )
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(VALIDATOR),
            "--result-root",
            str(result_root),
            "--corpus-manifest-sha256",
            corpus_manifest_sha256,
            "--model",
            str(model_path),
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        env=validator_env,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "independent OpenWebText substitute result validation failed: "
            f"stdout={completed.stdout}\nstderr={completed.stderr}"
        )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict) or value.get("valid") is not True:
        raise RuntimeError(f"independent validator returned invalid result: {value}")
    return value


def run_campaign(source_root: Path, corpus_root: Path, output_root: Path, model_path: Path) -> dict[str, Any]:
    source_root = _primary(source_root, "source root")
    corpus_root = _primary(corpus_root, "corpus root")
    output_root = _primary(output_root, "output root")
    model_path = _external(model_path, "model path")
    if output_root.exists() or output_root.is_symlink():
        raise FileExistsError(f"refusing to overwrite output root: {output_root}")
    source_validation = validate_source(source_root)
    corpus_validation = validate_corpus(corpus_root, source_validation["source_manifest_sha256"])
    model_files_before = engine.model_manifest(model_path)
    model, tokenizer, tokenizer_policy = engine._load_runtime(model_path)
    layer_count = len(model.model.layers)
    if getattr(model.args, "model_type", None) != "gemma3_text" or layer_count != 26:
        raise ValueError(f"expected cached Gemma3 1B PT text model with 26 layers, found {layer_count}")
    manifest = _read_json(corpus_root / "manifest.json", "corpus manifest")

    def load_windows(split: str) -> list[engine.CorpusWindow]:
        result = []
        for entry in manifest[split]:
            path = _regular(corpus_root / entry["path"], f"{split} window")
            text = path.read_text(encoding="utf-8")
            result.append(
                engine.CorpusWindow(
                    dataset="openwebtext",
                    document_id=entry["document_id"],
                    relative_path=entry["path"],
                    window_ordinal=entry["window_ordinal"],
                    text=text,
                    byte_len=len(text.encode("utf-8")),
                    source_sha256=entry["source_sha256"],
                    text_sha256=entry["text_sha256"],
                    token_count=entry["token_count"],
                )
            )
        return result

    fit = load_windows("fit")
    assessment = load_windows("assessment")
    all_windows = (*fit, *assessment)
    parity_checks = [engine.parity_check(model, tokenizer, window.text) for window in all_windows]
    if not all(check["passed"] for check in parity_checks):
        raise RuntimeError("zero-alpha parity gate failed")
    fit_baseline = engine.evaluate_windows(model, tokenizer, fit, None, include_rows=True)
    fit_candidates = []
    for source, destination in PILOT_PAIRS:
        config = engine.RecirculationConfig(source, destination, FIT_ALPHA)
        fit_candidates.append(
            {
                "config": asdict(config),
                "metrics": engine.evaluate_windows(model, tokenizer, fit, config, include_rows=True),
            }
        )
    selected = min(
        fit_candidates,
        key=lambda item: (
            item["metrics"]["mean_nll"],
            item["config"]["source_layer"],
            item["config"]["destination_layer"],
        ),
    )
    selected_config = engine.RecirculationConfig(**selected["config"])
    locked_config = engine.RecirculationConfig(
        selected_config.source_layer,
        selected_config.destination_layer,
        EVALUATION_ALPHA,
    )
    assessment_baseline = engine.evaluate_windows(model, tokenizer, assessment, None, include_rows=True)
    assessment_selected = engine.evaluate_windows(model, tokenizer, assessment, locked_config, include_rows=True)
    assessment_temperature_baseline = engine.evaluate_windows(
        model, tokenizer, assessment, None, temperature=TEMPERATURE_CONTROL, include_rows=True
    )
    assessment_temperature_selected = engine.evaluate_windows(
        model, tokenizer, assessment, locked_config, temperature=TEMPERATURE_CONTROL, include_rows=True
    )
    assessment_repeat = engine.evaluate_windows(model, tokenizer, assessment, locked_config, include_rows=True)
    repeat_delta = max(
        abs(assessment_selected["mean_nll"] - assessment_repeat["mean_nll"]),
        abs(assessment_selected["perplexity"] - assessment_repeat["perplexity"]),
    )
    model_files_after = engine.model_manifest(model_path)
    if model_files_after != model_files_before:
        raise RuntimeError("cached model manifest changed during frozen inference")
    config = {
        "schema": RESULT_SCHEMA,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "source_schema": SOURCE_SCHEMA,
        "corpus_schema": CORPUS_SCHEMA,
        "source_manifest_sha256": source_validation["source_manifest_sha256"],
        "corpus_manifest_sha256": corpus_validation["corpus_manifest_sha256"],
        "model_name": model_path.name,
        "model_path": str(model_path),
        "architecture": "gemma3_text",
        "layer_count": layer_count,
        "protocol": "openwebtext-substitute-1024-token-mechanics-v1",
        "mechanism_source": "arxiv:2608.17981",
        "paper_alignment": "mechanism_only_not_c4_webtextlike_replication",
        "window_token_count": WINDOW_TOKENS,
        "fit_window_count": len(fit),
        "assessment_window_count": len(assessment),
        "candidate_pairs": [list(pair) for pair in PILOT_PAIRS],
        "fit_alpha": FIT_ALPHA,
        "evaluation_alpha": EVALUATION_ALPHA,
        "evaluation_beta": EVALUATION_BETA,
        "temperature_control": TEMPERATURE_CONTROL,
        "normalization": "source_l2_norm_to_destination_l2_norm",
        "selected_fit_config": asdict(selected_config),
        "paper_expected_pair": {"source_layer": 11, "destination_layer": 4},
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "runtime": {
            "python": engine.package_version("pip"),
            "mlx": engine.package_version("mlx"),
            "mlx_lm": engine.package_version("mlx-lm"),
        },
        "tokenizer_policy": tokenizer_policy,
        "model_manifest_sha256": model_files_after["manifest_sha256"],
        "selection_policy": SELECTION_POLICY,
    }
    config["config_sha256"] = digest(config)
    results = {
        "schema": RESULT_SCHEMA,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "source_manifest_sha256": source_validation["source_manifest_sha256"],
        "corpus_manifest_sha256": corpus_validation["corpus_manifest_sha256"],
        "model_manifest_sha256": model_files_after["manifest_sha256"],
        "parity": {
            "sequence_count": len(parity_checks),
            "max_abs_logit_delta": max(check["max_abs_logit_delta"] for check in parity_checks),
            "tolerance": PARITY_TOLERANCE,
            "all_passed": all(check["passed"] for check in parity_checks),
        },
        "fit_baseline": fit_baseline,
        "fit_candidates": fit_candidates,
        "selected_fit_config": asdict(selected_config),
        "locked_evaluation_config": asdict(locked_config),
        "assessment_baseline": assessment_baseline,
        "assessment_selected": assessment_selected,
        "assessment_temperature_baseline": assessment_temperature_baseline,
        "assessment_temperature_selected": assessment_temperature_selected,
        "assessment_repeat": assessment_repeat,
        "assessment_repeat_max_metric_delta": round(repeat_delta, 12),
        "assessment_nll_delta_selected_minus_baseline": round(
            assessment_selected["mean_nll"] - assessment_baseline["mean_nll"], 9
        ),
        "assessment_perplexity_delta_selected_minus_baseline": round(
            assessment_selected["perplexity"] - assessment_baseline["perplexity"], 9
        ),
        "paper_expected_pair_recovered": selected_config.source_layer == 11 and selected_config.destination_layer == 4,
        "performance_result_is_local_openwebtext_substitute_pilot_only": True,
    }
    results["results_sha256"] = digest(results)
    receipt = {
        "schema": RESULT_SCHEMA,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "config_sha256": config["config_sha256"],
        "results_sha256": results["results_sha256"],
        "source_manifest_sha256": source_validation["source_manifest_sha256"],
        "corpus_manifest_sha256": corpus_validation["corpus_manifest_sha256"],
        "model_manifest_sha256": model_files_after["manifest_sha256"],
        "zero_alpha_parity_passed": results["parity"]["all_passed"],
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "deterministic_repeat_passed": repeat_delta <= PARITY_TOLERANCE,
        "assessment_mean_nll_delta_selected_minus_baseline": results["assessment_nll_delta_selected_minus_baseline"],
        "performance_improved_on_assessment": results["assessment_nll_delta_selected_minus_baseline"] < 0,
    }
    receipt["receipt_sha256"] = digest(receipt)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_root.name}.staging-", dir=output_root.parent))
    try:
        for name, value in (("config.json", config), ("results.json", results), ("receipt.json", receipt), ("model-manifest.json", model_files_after)):
            (staging / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        validator_receipt = _run_validator(staging, corpus_validation["corpus_manifest_sha256"], model_path)
        (staging / "validator-receipt.json").write_text(
            json.dumps(validator_receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(staging, output_root)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return {
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "output_root": str(output_root),
        "receipt": receipt,
        "validator": validator_receipt,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--corpus-root", type=Path, default=DEFAULT_CORPUS_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--pack-only", action="store_true")
    args = parser.parse_args()
    if args.pack_only:
        print(json.dumps(stage_corpus(args.source_root, args.corpus_root, args.model), indent=2, sort_keys=True))
    else:
        print(json.dumps(run_campaign(args.source_root, args.corpus_root, args.output_root, args.model), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
