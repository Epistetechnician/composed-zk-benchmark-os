#!/usr/bin/env python3
"""Run a small, immutable Gemma3 recirculation mechanics pilot.

State slice: continual-learning-gemma3-local-pilot-v1.

This pilot deliberately does not claim the paper's dataset or result. It uses
four document-disjoint windows from the operator-supplied NEWSROOM test file,
with 256 Gemma tokens per window, to exercise the frozen Gemma3 inference
mechanism end to end on the local Metal runtime. PrimaryED holds the active
artifact and DAed receives an immutable mirror. Both roots are outside the
repository and existing roots are never overwritten.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.gemma3_paper_recirculation_v1 import (
    PARITY_TOLERANCE,
    RecirculationConfig,
    CorpusWindow,
    evaluate_windows,
    model_manifest,
    package_version,
    parity_check,
    sha256_bytes,
    sha256_file,
)

STATE_SLICE = "continual-learning-gemma3-local-pilot-v1"
CLAIM_CEILING = "LocalDevelopmentGemma3NewsroomRecirculationMechanicsPilot"
CORPUS_SCHEMA = "gemma3-newsroom-recirculation-pilot-corpus-v1"
SOURCE_SCHEMA = "gemma3-newsroom-recirculation-pilot-input-v1"
WINDOW_TOKENS = 256
FIT_WINDOW_COUNT = 2
ASSESSMENT_WINDOW_COUNT = 2
SELECTED_DOCUMENT_COUNT = FIT_WINDOW_COUNT + ASSESSMENT_WINDOW_COUNT
FIT_ALPHA = 0.10
EVALUATION_ALPHA = 0.15
EVALUATION_BETA = 0.85
PILOT_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
NEWSROOM_UPSTREAM = "https://lil.nlp.cornell.edu/newsroom/download/index.html"
DEFAULT_MODEL = Path(
    "/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16"
)
DEFAULT_INPUT = Path(
    "/Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/"
    "gemma3-manual-inputs-v1/newsroom/release/test.jsonl.gz"
)
DEFAULT_PRIMARY_ROOT = Path(
    "/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/"
    "continual-learning-gemma3-local-pilot-v1-20260827-r1"
)
DEFAULT_DAED_ROOT = Path(
    "/Volumes/DAed/Archives/composed-zk-benchmark-os/"
    "continual-learning-gemma3-local-pilot-v1-20260827-r1"
)
PRIMARY_VOLUME = Path("/Volumes/PrimaryED")
DAED_VOLUME = Path("/Volumes/DAed")
VALIDATOR = Path(__file__).with_name("validate_gemma3_local_pilot_v1.py")


@dataclass(frozen=True)
class PilotSpec:
    """Immutable experiment identity shared by V1 and the fresh V2 cohort."""

    state_slice: str
    claim_ceiling: str
    corpus_schema: str
    source_schema: str
    protocol: str
    selection_offset: int
    selection_policy: str


DEFAULT_SPEC = PilotSpec(
    state_slice=STATE_SLICE,
    claim_ceiling=CLAIM_CEILING,
    corpus_schema=CORPUS_SCHEMA,
    source_schema=SOURCE_SCHEMA,
    protocol="mechanism-only-newsroom-256-token-pilot-v1",
    selection_offset=0,
    selection_policy="first-four-eligible-newsroom-test-records-v1",
)


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _external_path(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    repo = REPO_ROOT.resolve()
    if resolved == repo or repo in resolved.parents:
        raise ValueError(f"{label} must be outside the repository: {resolved}")
    return resolved


def _volume_path(path: Path, volume: Path, label: str) -> Path:
    resolved = _external_path(path, label)
    volume = volume.resolve()
    if not volume.is_dir():
        raise FileNotFoundError(f"required external volume is not mounted: {volume}")
    if resolved != volume and volume not in resolved.parents:
        raise ValueError(f"{label} must be under {volume}: {resolved}")
    return resolved


def _require_new_root(path: Path, label: str) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite existing {label}: {path}")


def _open_jsonl(path: Path) -> Iterator[tuple[int, dict[str, Any]]]:
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f"NEWSROOM input must be a regular file: {path}")
    opener = gzip.open if path.suffix == ".gz" else Path.open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"blank NEWSROOM JSONL line: {path}:{line_number}")
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid NEWSROOM JSONL: {path}:{line_number}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"NEWSROOM record must be an object: {path}:{line_number}")
            yield line_number, value


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


def _select_documents(
    input_path: Path,
    tokenizer: Any,
    *,
    selection_offset: int = 0,
) -> list[dict[str, Any]]:
    if selection_offset < 0:
        raise ValueError("selection offset must be non-negative")
    selected: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    eligible_count = 0
    for line_number, value in _open_jsonl(input_path):
        text = value.get("text")
        url = value.get("url")
        if not isinstance(text, str) or not text:
            raise ValueError(f"NEWSROOM record has invalid text: line {line_number}")
        if not isinstance(url, str) or not url:
            raise ValueError(f"NEWSROOM record has invalid url: line {line_number}")
        if url in seen_urls:
            raise ValueError(f"duplicate NEWSROOM url before selection: {url}")
        seen_urls.add(url)
        token_ids = list(tokenizer.encode(text, add_special_tokens=False))
        if len(token_ids) < WINDOW_TOKENS:
            continue
        if eligible_count < selection_offset:
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
            f"NEWSROOM input yielded {len(selected)} eligible documents; "
            f"expected {SELECTED_DOCUMENT_COUNT}"
        )
    return selected


def _materialize_corpus(
    root: Path,
    selected: list[dict[str, Any]],
    tokenizer: Any,
    spec: PilotSpec = DEFAULT_SPEC,
) -> tuple[list[CorpusWindow], list[CorpusWindow], dict[str, Any]]:
    fit: list[CorpusWindow] = []
    assessment: list[CorpusWindow] = []
    entries: dict[str, list[dict[str, Any]]] = {"fit": [], "assessment": []}
    for index, document in enumerate(selected):
        split = "fit" if index < FIT_WINDOW_COUNT else "assessment"
        relative_path = Path(split) / "newsroom" / f"window-{index:06d}.txt"
        window_text = tokenizer.decode(document["token_ids"])
        if not isinstance(window_text, str) or not window_text:
            raise ValueError(f"tokenizer produced empty pilot window: {relative_path}")
        roundtrip = list(tokenizer.encode(window_text, add_special_tokens=False))
        if roundtrip != document["token_ids"]:
            raise ValueError(f"Gemma token decode/re-encode changed {relative_path}")
        output_path = root / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(window_text, encoding="utf-8")
        raw_bytes = window_text.encode("utf-8")
        window = CorpusWindow(
            dataset="newsroom",
            document_id=document["document_id"],
            relative_path=relative_path.as_posix(),
            window_ordinal=0,
            text=window_text,
            byte_len=len(raw_bytes),
            source_sha256=sha256_bytes(raw_bytes),
            text_sha256=sha256_bytes(raw_bytes),
            token_count=WINDOW_TOKENS,
        )
        target = fit if split == "fit" else assessment
        target.append(window)
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
    body = {
        "state_slice": spec.state_slice,
        "schema": spec.corpus_schema,
        "window_token_count": WINDOW_TOKENS,
        "fit": entries["fit"],
        "assessment": entries["assessment"],
        "fit_window_count": len(fit),
        "assessment_window_count": len(assessment),
        "selection_policy": spec.selection_policy,
    }
    manifest = {"manifest": body, "manifest_sha256": digest(body)}
    _write_json(root / "corpus-manifest.json", manifest)
    return fit, assessment, manifest


def _copy_raw_input(input_path: Path, root: Path) -> Path:
    input_path = _external_path(input_path, "NEWSROOM input")
    raw_path = root / "raw" / "newsroom" / input_path.name
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_path, raw_path)
    if sha256_file(raw_path) != sha256_file(input_path):
        raise RuntimeError("NEWSROOM raw-input copy checksum mismatch")
    return raw_path


def _write_input_manifest(
    root: Path,
    input_path: Path,
    raw_path: Path,
    selected: list[dict[str, Any]],
    spec: PilotSpec = DEFAULT_SPEC,
) -> dict[str, Any]:
    body = {
        "state_slice": spec.state_slice,
        "schema": spec.source_schema,
        "upstream": NEWSROOM_UPSTREAM,
        "source_path": str(input_path.resolve()),
        "raw_path": raw_path.relative_to(root).as_posix(),
        "raw_byte_len": raw_path.stat().st_size,
        "raw_sha256": sha256_file(raw_path),
        "split": "test",
        "selection_policy": spec.selection_policy,
        "selection_offset": spec.selection_offset,
        "window_token_count": WINDOW_TOKENS,
        "selected_documents": [
            {
                key: value
                for key, value in document.items()
                if key != "token_ids"
            }
            for document in selected
        ],
    }
    manifest = {"manifest": body, "manifest_sha256": digest(body)}
    _write_json(root / "input-manifest.json", manifest)
    return manifest


def _pilot_configs(layer_count: int) -> tuple[RecirculationConfig, ...]:
    configs = tuple(
        RecirculationConfig(source_layer=source, destination_layer=destination, alpha=FIT_ALPHA)
        for source, destination in PILOT_PAIRS
    )
    for config in configs:
        config.validate(layer_count)
    return configs


def _run_validator(
    root: Path,
    model_path: Path,
    validator: Path = VALIDATOR,
) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(validator),
            "--artifact-root",
            str(root),
            "--model",
            str(model_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "independent pilot validation failed:\n"
            f"stdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
        )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("independent validator did not return JSON") from exc
    if not isinstance(result, dict) or result.get("valid") is not True:
        raise RuntimeError(f"independent validator returned invalid result: {result}")
    return result


def run_campaign(
    primary_root: Path = DEFAULT_PRIMARY_ROOT,
    daed_root: Path = DEFAULT_DAED_ROOT,
    input_path: Path = DEFAULT_INPUT,
    model_path: Path = DEFAULT_MODEL,
    *,
    spec: PilotSpec = DEFAULT_SPEC,
    validator: Path = VALIDATOR,
) -> dict[str, Any]:
    primary_root = _volume_path(primary_root, PRIMARY_VOLUME, "PrimaryED artifact root")
    daed_root = _volume_path(daed_root, DAED_VOLUME, "DAed mirror root")
    input_path = _external_path(input_path, "NEWSROOM input")
    model_path = _external_path(model_path, "model path")
    _require_new_root(primary_root, "PrimaryED artifact root")
    _require_new_root(daed_root, "DAed mirror root")
    if not input_path.is_file():
        raise FileNotFoundError(f"NEWSROOM input does not exist: {input_path}")
    if not model_path.is_dir():
        raise FileNotFoundError(f"cached Gemma3 model does not exist: {model_path}")
    primary_root.parent.mkdir(parents=True, exist_ok=True)
    daed_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{primary_root.name}.staging-", dir=primary_root.parent))
    mirror_staging: Path | None = None
    try:
        raw_path = _copy_raw_input(input_path, staging)
        model_files_before = model_manifest(model_path)
        tokenizer = _load_tokenizer(model_path)
        selected_documents = _select_documents(
            raw_path, tokenizer, selection_offset=spec.selection_offset
        )
        input_manifest = _write_input_manifest(
            staging, input_path, raw_path, selected_documents, spec
        )
        fit, assessment, corpus_manifest = _materialize_corpus(
            staging / "corpus", selected_documents, tokenizer, spec
        )
        model, tokenizer, tokenizer_policy = __import__(
            "experiments.continual_learning.gemma3_paper_recirculation_v1",
            fromlist=["_load_runtime"],
        )._load_runtime(model_path)
        layer_count = len(model.model.layers)
        if getattr(model.args, "model_type", None) != "gemma3_text":
            raise ValueError("loaded checkpoint is not the expected Gemma3 text model")
        if layer_count != 26:
            raise ValueError(f"expected Gemma3 1B PT to have 26 layers, found {layer_count}")
        parity_checks = [
            parity_check(model, tokenizer, window.text)
            for window in (*fit, *assessment)
        ]
        if not all(check["passed"] for check in parity_checks):
            raise RuntimeError("zero-alpha parity gate failed")
        fit_baseline = evaluate_windows(model, tokenizer, fit, None, include_rows=True)
        fit_candidates = []
        for config in _pilot_configs(layer_count):
            fit_candidates.append(
                {
                    "config": asdict(config),
                    "metrics": evaluate_windows(
                        model, tokenizer, fit, config, include_rows=True
                    ),
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
        selected_config = RecirculationConfig(**selected["config"])
        locked_config = RecirculationConfig(
            selected_config.source_layer,
            selected_config.destination_layer,
            EVALUATION_ALPHA,
        )
        assessment_baseline = evaluate_windows(
            model, tokenizer, assessment, None, include_rows=True
        )
        assessment_selected = evaluate_windows(
            model, tokenizer, assessment, locked_config, include_rows=True
        )
        assessment_temperature_baseline = evaluate_windows(
            model, tokenizer, assessment, None, temperature=1.2, include_rows=True
        )
        assessment_temperature_selected = evaluate_windows(
            model,
            tokenizer,
            assessment,
            locked_config,
            temperature=1.2,
            include_rows=True,
        )
        assessment_repeat = evaluate_windows(
            model, tokenizer, assessment, locked_config, include_rows=True
        )
        repeat_delta = max(
            abs(assessment_selected["mean_nll"] - assessment_repeat["mean_nll"]),
            abs(assessment_selected["perplexity"] - assessment_repeat["perplexity"]),
        )
        model_files_after = model_manifest(model_path)
        if model_files_after != model_files_before:
            raise RuntimeError("cached model manifest changed during frozen inference")
        config = {
            "state_slice": spec.state_slice,
            "claim_ceiling": spec.claim_ceiling,
            "model_name": model_path.name,
            "model_path": str(model_path),
            "architecture": "gemma3_text",
            "layer_count": layer_count,
            "protocol": spec.protocol,
            "mechanism_source": "arxiv:2608.17981",
            "paper_alignment": "mechanism_only_not_paper_replication",
            "input_manifest_sha256": input_manifest["manifest_sha256"],
            "corpus_manifest_sha256": corpus_manifest["manifest_sha256"],
            "selection_offset": spec.selection_offset,
            "selection_policy": spec.selection_policy,
            "dataset": "newsroom",
            "window_token_count": WINDOW_TOKENS,
            "fit_window_count": len(fit),
            "assessment_window_count": len(assessment),
            "candidate_pairs": [list(pair) for pair in PILOT_PAIRS],
            "fit_alpha": FIT_ALPHA,
            "evaluation_alpha": EVALUATION_ALPHA,
            "evaluation_beta": EVALUATION_BETA,
            "normalization": "source_l2_norm_to_destination_l2_norm",
            "selected_fit_config": {
                "source_layer": selected_config.source_layer,
                "destination_layer": selected_config.destination_layer,
            },
            "paper_expected_pair": {"source_layer": 11, "destination_layer": 4},
            "network_access": False,
            "training": False,
            "weights_frozen": True,
            "runtime": {
                "python": package_version("pip"),
                "mlx": package_version("mlx"),
                "mlx_lm": package_version("mlx-lm"),
            },
            "tokenizer_policy": tokenizer_policy,
            "model_manifest_sha256": model_files_after["manifest_sha256"],
        }
        config["config_sha256"] = digest(config)
        results = {
            "state_slice": spec.state_slice,
            "claim_ceiling": spec.claim_ceiling,
            "input_manifest_sha256": input_manifest["manifest_sha256"],
            "corpus_manifest_sha256": corpus_manifest["manifest_sha256"],
            "model_manifest_sha256": model_files_after["manifest_sha256"],
            "parity": {
                "sequence_count": len(parity_checks),
                "max_abs_logit_delta": max(
                    check["max_abs_logit_delta"] for check in parity_checks
                ),
                "tolerance": PARITY_TOLERANCE,
                "all_passed": all(check["passed"] for check in parity_checks),
                "checks": parity_checks,
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
            "paper_expected_pair_recovered": (
                selected_config.source_layer == 11
                and selected_config.destination_layer == 4
            ),
            "performance_result_is_local_mechanics_pilot_only": True,
        }
        results["results_sha256"] = digest(results)
        selected_delta = (
            assessment_selected["mean_nll"] - assessment_baseline["mean_nll"]
        )
        receipt = {
            "state_slice": spec.state_slice,
            "claim_ceiling": spec.claim_ceiling,
            "config_sha256": config["config_sha256"],
            "results_sha256": results["results_sha256"],
            "input_manifest_sha256": input_manifest["manifest_sha256"],
            "corpus_manifest_sha256": corpus_manifest["manifest_sha256"],
            "model_manifest_sha256": model_files_after["manifest_sha256"],
            "zero_alpha_parity_passed": results["parity"]["all_passed"],
            "network_access": False,
            "training": False,
            "weights_frozen": True,
            "deterministic_repeat_passed": repeat_delta <= PARITY_TOLERANCE,
            "assessment_mean_nll_delta_selected_minus_baseline": round(selected_delta, 9),
            "performance_improved_on_assessment": selected_delta < 0,
        }
        receipt["receipt_sha256"] = digest(receipt)
        _write_json(staging / "config.json", config)
        _write_json(staging / "results.json", results)
        _write_json(staging / "model-manifest.json", model_files_after)
        _write_json(staging / "receipt.json", receipt)
        validator_receipt = _run_validator(staging, model_path, validator)
        _write_json(staging / "validator-receipt.json", validator_receipt)
        os.replace(staging, primary_root)
        staging = primary_root
        mirror_staging = Path(
            tempfile.mkdtemp(prefix=f".{daed_root.name}.staging-", dir=daed_root.parent)
        )
        shutil.copytree(
            primary_root,
            mirror_staging,
            dirs_exist_ok=True,
            copy_function=shutil.copy2,
        )
        os.replace(mirror_staging, daed_root)
        mirror_staging = daed_root
        primary_validation = _run_validator(primary_root, model_path, validator)
        daed_validation = _run_validator(daed_root, model_path, validator)
        return {
            "state_slice": spec.state_slice,
            "claim_ceiling": spec.claim_ceiling,
            "primary_root": str(primary_root),
            "daed_root": str(daed_root),
            "receipt": receipt,
            "primary_validation": primary_validation,
            "daed_validation": daed_validation,
        }
    finally:
        if staging != primary_root and staging.exists():
            shutil.rmtree(staging)
        if mirror_staging is not None and mirror_staging != daed_root and mirror_staging.exists():
            shutil.rmtree(mirror_staging)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-root", type=Path, default=DEFAULT_PRIMARY_ROOT)
    parser.add_argument("--daed-root", type=Path, default=DEFAULT_DAED_ROOT)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    print(
        json.dumps(
            run_campaign(args.primary_root, args.daed_root, args.input, args.model),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
