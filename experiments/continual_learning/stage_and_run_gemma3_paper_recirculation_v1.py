#!/usr/bin/env python3
"""Stage operator-acquired records and run the Gemma3 recirculation campaign.

State slice: continual-learning-gemma3-paper-recirculation-v1.

The source root is acquired by the operator. It contains normalized JSONL
records and an acquisition manifest; this script performs no network access or
downloads. It tokenizes records with the cached Gemma tokenizer, materializes
the paper-shaped external corpus, runs the campaign, and invokes the separate
validator. Existing corpus and result roots are never overwritten.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.continual_learning.gemma3_paper_recirculation_v1 import (
    ASSESSMENT_DATASETS,
    CLAIM_CEILING,
    CORPUS_SCHEMA,
    DEFAULT_MODEL,
    FIT_DATASETS,
    STATE_SLICE,
    WINDOW_TOKENS,
    digest,
    load_corpus,
    sha256_file,
)

SOURCE_SCHEMA = "gemma3-paper-recirculation-acquisition-v1"
PAPER_FIT_WINDOW_COUNTS = {"arxiv": 484, "c4": 488, "pg19": 500}
SOURCE_FILES = {
    ("fit", "arxiv"): Path("fit/arxiv.jsonl"),
    ("fit", "c4"): Path("fit/c4.jsonl"),
    ("fit", "pg19"): Path("fit/pg19.jsonl"),
    ("assessment", "arxiv"): Path("assessment/arxiv.jsonl"),
    ("assessment", "big_patent"): Path("assessment/big_patent.jsonl"),
    ("assessment", "billsum"): Path("assessment/billsum.jsonl"),
    ("assessment", "booksum/book"): Path("assessment/booksum-book.jsonl"),
    ("assessment", "c4/webtextlike"): Path("assessment/c4-webtextlike.jsonl"),
    ("assessment", "gov_report"): Path("assessment/gov_report.jsonl"),
    ("assessment", "lambada"): Path("assessment/lambada.jsonl"),
    ("assessment", "newsroom"): Path("assessment/newsroom.jsonl"),
    ("assessment", "pg19"): Path("assessment/pg19.jsonl"),
    ("assessment", "pubmed"): Path("assessment/pubmed.jsonl"),
}


def _regular_file(path: Path, label: str) -> Path:
    if not path.is_file() or path.is_symlink():
        raise FileNotFoundError(f"{label} must be a regular file: {path}")
    return path


def _external_path(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    repo = REPO_ROOT.resolve()
    if resolved == repo or repo in resolved.parents:
        raise ValueError(f"{label} must be outside the repository: {resolved}")
    return resolved


def _require_absent(path: Path, label: str) -> None:
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite existing {label}: {path}")


def _load_acquisition_manifest(source_root: Path) -> tuple[dict[str, Any], Path]:
    path = _regular_file(source_root / "acquisition-manifest.json", "acquisition manifest")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("acquisition manifest is not valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("acquisition manifest must be an object")
    if value.get("schema") != SOURCE_SCHEMA:
        raise ValueError("acquisition manifest schema mismatch")
    if value.get("state_slice") != STATE_SLICE:
        raise ValueError("acquisition manifest state slice mismatch")
    selection_policy = value.get("selection_policy")
    if not isinstance(selection_policy, str) or not selection_policy:
        raise ValueError("acquisition manifest needs a selection_policy")
    datasets = value.get("datasets")
    expected_keys = {f"fit/{name}" for name in FIT_DATASETS} | {
        f"assessment/{name}" for name in ASSESSMENT_DATASETS
    }
    if not isinstance(datasets, dict) or set(datasets) != expected_keys:
        raise ValueError("acquisition manifest dataset keys do not match the protocol")
    for key, metadata in datasets.items():
        if not isinstance(metadata, dict):
            raise ValueError(f"acquisition metadata must be an object: {key}")
        for field in ("source", "revision", "split"):
            if not isinstance(metadata.get(field), str) or not metadata[field]:
                raise ValueError(f"acquisition metadata needs {field}: {key}")
    return value, path


def _records(path: Path) -> Iterable[tuple[str, str]]:
    _regular_file(path, "source JSONL")
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"blank source JSONL line: {path}:{line_number}")
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid source JSONL: {path}:{line_number}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"source JSONL record must be an object: {path}:{line_number}")
            document_id = value.get("document_id")
            text = value.get("text")
            if not isinstance(document_id, str) or not document_id:
                raise ValueError(f"source record needs document_id: {path}:{line_number}")
            if not isinstance(text, str) or not text:
                raise ValueError(f"source record needs non-empty text: {path}:{line_number}")
            yield document_id, text


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


def _token_windows(
    tokenizer: Any,
    text: str,
    *,
    partial_allowed: bool,
    maximum_windows: int | None,
) -> Iterable[tuple[int, str, int]]:
    token_ids = list(tokenizer.encode(text, add_special_tokens=False))
    for start in range(0, len(token_ids), WINDOW_TOKENS):
        chunk = token_ids[start : start + WINDOW_TOKENS]
        if len(chunk) < WINDOW_TOKENS:
            if not partial_allowed or len(chunk) <= 1:
                break
        window_text = tokenizer.decode(chunk)
        if not isinstance(window_text, str) or not window_text:
            raise ValueError("Gemma tokenizer produced empty window text")
        roundtrip = list(tokenizer.encode(window_text, add_special_tokens=False))
        if roundtrip != chunk:
            raise ValueError("Gemma token decode/re-encode changed a window")
        yield start // WINDOW_TOKENS, window_text, len(chunk)
        if maximum_windows is not None and start // WINDOW_TOKENS + 1 >= maximum_windows:
            break


def _pack_file(
    source_root: Path,
    temp_root: Path,
    tokenizer: Any,
    split: str,
    dataset: str,
    source_relative: Path,
    *,
    target_windows: int | None,
) -> list[dict[str, Any]]:
    source_path = source_root / source_relative
    partial_allowed = split == "assessment" and dataset in {
        "c4/webtextlike",
        "lambada",
        "newsroom",
    }
    destination_stem = source_relative.stem
    entries: list[dict[str, Any]] = []
    seen_documents: set[str] = set()
    for document_id, text in _records(source_path):
        if document_id in seen_documents:
            raise ValueError(f"duplicate {split} document_id in {source_relative}: {document_id}")
        seen_documents.add(document_id)
        maximum_windows = 2 if split == "fit" else None
        for window_ordinal, window_text, token_count in _token_windows(
            tokenizer,
            text,
            partial_allowed=partial_allowed,
            maximum_windows=maximum_windows,
        ):
            if target_windows is not None and len(entries) >= target_windows:
                break
            relative_path = Path(split) / destination_stem / f"window-{len(entries):06d}.txt"
            output_path = temp_root / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(window_text, encoding="utf-8")
            entries.append(
                {
                    "dataset": dataset,
                    "document_id": document_id,
                    "path": relative_path.as_posix(),
                    "window_ordinal": window_ordinal,
                    "token_count": token_count,
                }
            )
        if target_windows is not None and len(entries) >= target_windows:
            break
    if target_windows is not None and len(entries) != target_windows:
        raise ValueError(
            f"{split}/{dataset} produced {len(entries)} windows; "
            f"expected {target_windows}"
        )
    if not entries:
        raise ValueError(f"{split}/{dataset} produced no eligible windows")
    return entries


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stage_corpus(
    source_root: Path,
    corpus_root: Path,
    model_path: Path = DEFAULT_MODEL,
    *,
    fit_target_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Stage a new external corpus atomically; never overwrite a prior root."""

    source_root = _external_path(source_root, "source root")
    corpus_root = _external_path(corpus_root, "corpus root")
    model_path = model_path.expanduser().resolve()
    if not source_root.is_dir():
        raise FileNotFoundError(f"source root does not exist: {source_root}")
    if not model_path.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model_path}")
    _require_absent(corpus_root, "corpus root")
    acquisition_manifest, acquisition_path = _load_acquisition_manifest(source_root)
    tokenizer = _load_tokenizer(model_path)
    fit_targets = fit_target_counts or PAPER_FIT_WINDOW_COUNTS
    if fit_targets != PAPER_FIT_WINDOW_COUNTS:
        raise ValueError("CLI corpus staging is fixed to the paper fit window counts")
    corpus_parent = corpus_root.parent
    corpus_parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        dir=corpus_parent,
        prefix=f".{corpus_root.name}.staging-",
    ) as temporary:
        temp_root = Path(temporary)
        fit_entries = []
        for dataset in FIT_DATASETS:
            fit_entries.extend(
                _pack_file(
                    source_root,
                    temp_root,
                    tokenizer,
                    "fit",
                    dataset,
                    SOURCE_FILES[("fit", dataset)],
                    target_windows=fit_targets[dataset],
                )
            )
        assessment_entries = []
        for dataset in ASSESSMENT_DATASETS:
            assessment_entries.extend(
                _pack_file(
                    source_root,
                    temp_root,
                    tokenizer,
                    "assessment",
                    dataset,
                    SOURCE_FILES[("assessment", dataset)],
                    target_windows=None,
                )
            )
        corpus_manifest = {
            "schema": CORPUS_SCHEMA,
            "window_token_count": WINDOW_TOKENS,
            "fit": fit_entries,
            "assessment": assessment_entries,
        }
        _write_json(temp_root / "manifest.json", corpus_manifest)
        _write_json(temp_root / "acquisition-manifest.json", acquisition_manifest)
        loaded_fit, loaded_assessment, canonical = load_corpus(
            temp_root,
            tokenizer,
            strict_shape=True,
        )
        if len(loaded_fit) != sum(fit_targets.values()):
            raise RuntimeError("staged fit count changed during corpus validation")
        receipt = {
            "state_slice": STATE_SLICE,
            "claim_ceiling": CLAIM_CEILING,
            "source_schema": SOURCE_SCHEMA,
            "source_manifest_sha256": sha256_file(acquisition_path),
            "source_root": str(source_root),
            "selection_policy": acquisition_manifest["selection_policy"],
            "fit_window_counts": {
                dataset: sum(entry["dataset"] == dataset for entry in fit_entries)
                for dataset in FIT_DATASETS
            },
            "assessment_window_count": len(loaded_assessment),
            "corpus_manifest_sha256": canonical["manifest_sha256"],
            "tokenizer_model": str(model_path),
            "network_access": False,
            "training": False,
        }
        receipt["receipt_sha256"] = digest(receipt)
        _write_json(temp_root / "staging-receipt.json", receipt)
        os.replace(temp_root, corpus_root)
    return receipt


def run_end_to_end(
    source_root: Path,
    corpus_root: Path,
    output_root: Path | None,
    model_path: Path = DEFAULT_MODEL,
    *,
    pack_only: bool = False,
) -> dict[str, Any]:
    """Stage, execute, and independently validate one immutable campaign."""

    if not pack_only:
        if output_root is None:
            raise ValueError("output root is required for an execution run")
        output_root = _external_path(output_root, "output root")
        _require_absent(output_root, "output root")
    staging_receipt = stage_corpus(source_root, corpus_root, model_path)
    if pack_only:
        return {"staging_receipt": staging_receipt, "pack_only": True}

    assert output_root is not None
    model_path = model_path.expanduser().resolve()
    runner = Path(__file__).with_name("gemma3_paper_recirculation_v1.py")
    validator = Path(__file__).with_name("validate_gemma3_paper_recirculation_v1.py")
    environment = os.environ.copy()
    environment.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    subprocess.run(
        [
            sys.executable,
            "-B",
            str(runner),
            "--model",
            str(model_path),
            "--corpus-root",
            str(corpus_root),
            "--output",
            str(output_root),
        ],
        cwd=REPO_ROOT,
        env=environment,
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-B",
            str(validator),
            "--model",
            str(model_path),
            "--corpus-root",
            str(corpus_root),
            "--root",
            str(output_root),
        ],
        cwd=REPO_ROOT,
        env=environment,
        check=True,
    )
    return {
        "staging_receipt": staging_receipt,
        "corpus_root": str(corpus_root.resolve()),
        "output_root": str(output_root),
        "validator_passed": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument(
        "--pack-only",
        action="store_true",
        help="stage and validate the external corpus without executing the model",
    )
    args = parser.parse_args()
    if not args.pack_only and args.output is None:
        parser.error("--output is required unless --pack-only is used")
    print(
        json.dumps(
            run_end_to_end(
                args.source_root,
                args.corpus_root,
                args.output,
                args.model,
                pack_only=args.pack_only,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
