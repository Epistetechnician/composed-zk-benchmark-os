#!/usr/bin/env python3
"""Independently validate the FineWeb-Edu bounded Gemma3 custody chain.

State slice: continual-learning-gemma3-fineweb-edu-bounded-v1.

This validator performs read-only source, corpus, and result checks. It does
not download data, load a model unless result validation requests its frozen
manifest, train, or mutate repository evidence.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_VOLUME = Path("/Volumes/PrimaryED")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

STATE_SLICE = "continual-learning-gemma3-fineweb-edu-bounded-v1"
CLAIM_CEILING = "LocalDevelopmentGemma3FineWebEduBoundedPilot"
SOURCE_SCHEMA = "gemma3-fineweb-edu-bounded-acquisition-v1"
CORPUS_SCHEMA = "gemma3-fineweb-edu-bounded-corpus-v1"
RESULT_SCHEMA = "gemma3-fineweb-edu-bounded-result-v1"
DATASET_REPO = "HuggingFaceFW/fineweb-edu"
DATASET_REVISION = "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
DATASET_SOURCE = f"https://huggingface.co/datasets/{DATASET_REPO}"
DATASET_FILES = (
    {
        "crawl": "CC-MAIN-2013-20",
        "path": "data/CC-MAIN-2013-20/train-00000-of-00014.parquet",
        "byte_len": 2_369_456_837,
        "sha256": "fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03",
        "lfs_sha256": "fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03",
    },
    {
        "crawl": "CC-MAIN-2024-10",
        "path": "data/CC-MAIN-2024-10/000_00000.parquet",
        "byte_len": 1_911_528_585,
        "sha256": "89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484",
        "lfs_sha256": "89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484",
    },
)
DATASET_BYTE_COUNT = sum(item["byte_len"] for item in DATASET_FILES)
ROWS_PER_PANEL = 2048
WINDOW_TOKENS = 1024
FIT_CRAWL = DATASET_FILES[0]["crawl"]
ASSESSMENT_CRAWL = DATASET_FILES[1]["crawl"]
PILOT_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
PARITY_TOLERANCE = 1e-5


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


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


def _json(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(_regular(path, label).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with _regular(path, label).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{label} has a blank line at {line_number}")
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{label} line {line_number} is not an object")
            rows.append(value)
    return rows


def _check_self_digest(value: dict[str, Any], field: str, label: str) -> None:
    stored = value.get(field)
    if not isinstance(stored, str) or not stored:
        raise ValueError(f"{label} is missing {field}")
    body = {key: item for key, item in value.items() if key != field}
    if digest(body) != stored:
        raise ValueError(f"{label} {field} mismatch")


def validate_source(source_root: Path) -> dict[str, Any]:
    source_root = _primary(source_root, "source root")
    manifest = _json(source_root / "acquisition-manifest.json", "source manifest")
    if manifest.get("schema") != SOURCE_SCHEMA:
        raise ValueError("source schema mismatch")
    if manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("source state slice mismatch")
    if manifest.get("claim_ceiling") != CLAIM_CEILING:
        raise ValueError("source claim ceiling mismatch")
    _check_self_digest(manifest, "manifest_sha256", "source manifest")
    if manifest.get("network_access") is not True or manifest.get("training") is not False:
        raise ValueError("source network/training flags mismatch")
    if manifest.get("scientific_execution") is not False:
        raise ValueError("source must not claim scientific execution")
    if manifest.get("evidence_ledger_mutation") is not False:
        raise ValueError("source must not mutate the Evidence Ledger")
    if manifest.get("selection_policy") != "first-2048-records-from-two-pinned-crawls-document-disjoint-v1":
        raise ValueError("source selection policy mismatch")
    if manifest.get("paper_alignment") != "mechanism_only_not_c4_webtextlike_replication":
        raise ValueError("source paper alignment mismatch")
    if manifest.get("dataset") != {
        "repo": DATASET_REPO,
        "source": DATASET_SOURCE,
        "revision": DATASET_REVISION,
        "config": "fineweb-edu-crawl-shards",
        "split": "train",
        "selected_file_count": 2,
        "selected_crawls": [FIT_CRAWL, ASSESSMENT_CRAWL],
        "parquet_byte_count": DATASET_BYTE_COUNT,
    }:
        raise ValueError("FineWeb-Edu pin mismatch")

    raw_root_value = manifest.get("raw_root")
    if not isinstance(raw_root_value, str):
        raise ValueError("source raw_root is missing")
    raw_root = _primary(Path(raw_root_value), "raw root")
    raw_artifacts = manifest.get("raw_artifacts")
    if not isinstance(raw_artifacts, list) or len(raw_artifacts) != len(DATASET_FILES):
        raise ValueError("raw artifact count mismatch")
    expected_by_path = {
        f"dataset/{item['path']}": item for item in DATASET_FILES
    }
    seen_paths: set[str] = set()
    total_bytes = 0
    total_rows = 0
    import pyarrow.parquet as pq

    for artifact in raw_artifacts:
        if not isinstance(artifact, dict):
            raise ValueError("raw artifact must be an object")
        relative = artifact.get("relative_path")
        if relative not in expected_by_path or relative in seen_paths:
            raise ValueError(f"unexpected or duplicate raw artifact: {relative}")
        seen_paths.add(relative)
        expected = expected_by_path[relative]
        path = _regular(raw_root / relative, "raw artifact")
        if artifact.get("crawl") != expected["crawl"]:
            raise ValueError(f"raw crawl mismatch: {relative}")
        if artifact.get("byte_len") != expected["byte_len"] or path.stat().st_size != expected["byte_len"]:
            raise ValueError(f"raw byte length mismatch: {relative}")
        if artifact.get("lfs_sha256") != expected["lfs_sha256"]:
            raise ValueError(f"raw LFS digest mismatch: {relative}")
        if artifact.get("sha256") != expected["sha256"] or sha256_file(path) != expected["sha256"]:
            raise ValueError(f"raw checksum mismatch: {relative}")
        row_count = pq.ParquetFile(path).metadata.num_rows
        if artifact.get("row_count") != row_count or row_count <= 0:
            raise ValueError(f"raw row count mismatch: {relative}")
        total_bytes += path.stat().st_size
        total_rows += row_count
    if seen_paths != set(expected_by_path) or total_bytes != DATASET_BYTE_COUNT:
        raise ValueError("raw aggregate mismatch")

    datasets = manifest.get("datasets")
    expected_keys = {"fit/fineweb_edu", "assessment/fineweb_edu"}
    if not isinstance(datasets, dict) or set(datasets) != expected_keys:
        raise ValueError("source dataset keys mismatch")
    all_ids: set[str] = set()
    for key, crawl in (("fit/fineweb_edu", FIT_CRAWL), ("assessment/fineweb_edu", ASSESSMENT_CRAWL)):
        metadata = datasets[key]
        if not isinstance(metadata, dict):
            raise ValueError(f"source metadata is not an object: {key}")
        item = next(value for value in DATASET_FILES if value["crawl"] == crawl)
        for field, expected in {
            "source": DATASET_SOURCE,
            "revision": DATASET_REVISION,
            "config": "fineweb-edu-crawl-shards",
            "split": "train",
            "crawl": crawl,
            "source_path": item["path"],
            "row_start": 0,
            "row_count": ROWS_PER_PANEL,
        }.items():
            if metadata.get(field) != expected:
                raise ValueError(f"source metadata mismatch: {key}:{field}")
        path = _regular(source_root / metadata["normalized_path"], f"normalized {key}")
        rows = _jsonl(path, f"normalized {key}")
        if len(rows) != ROWS_PER_PANEL or sha256_file(path) != metadata.get("normalized_sha256"):
            raise ValueError(f"normalized source mismatch: {key}")
        for index, row in enumerate(rows):
            document_id = row.get("document_id")
            if not isinstance(document_id, str) or not document_id.startswith(f"fineweb-edu:{crawl}:"):
                raise ValueError(f"document identity mismatch: {key}:{index}")
            if document_id in all_ids:
                raise ValueError("fit and assessment document identities overlap")
            all_ids.add(document_id)
            if row.get("source_crawl") != crawl or row.get("source_path") != item["path"]:
                raise ValueError(f"normalized provenance mismatch: {key}:{index}")
            if row.get("source_row_index") != index:
                raise ValueError(f"normalized row index mismatch: {key}:{index}")
            if not isinstance(row.get("text"), str) or not row["text"].strip():
                raise ValueError(f"normalized text missing: {key}:{index}")
            if not isinstance(row.get("metadata"), dict):
                raise ValueError(f"normalized metadata missing: {key}:{index}")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "source_manifest_sha256": manifest["manifest_sha256"],
        "raw_artifact_count": len(raw_artifacts),
        "raw_byte_count": total_bytes,
        "raw_row_count": total_rows,
        "fit_record_count": ROWS_PER_PANEL,
        "assessment_record_count": ROWS_PER_PANEL,
    }


def _validate_window_files(root: Path, entries: Any, split: str) -> int:
    if not isinstance(entries, list):
        raise ValueError(f"corpus {split} entries are missing")
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError(f"corpus {split} entry is not an object")
        relative = entry.get("path")
        if not isinstance(relative, str) or Path(relative).is_absolute() or relative in seen:
            raise ValueError(f"invalid corpus {split} path")
        seen.add(relative)
        path = _regular(root / relative, f"corpus {split} window")
        data = path.read_bytes()
        if len(data) != entry.get("byte_len") or sha256_file(path) != entry.get("text_sha256"):
            raise ValueError(f"corpus {split} window digest mismatch: {relative}")
        if entry.get("token_count") != WINDOW_TOKENS or entry.get("dataset") != "fineweb_edu":
            raise ValueError(f"corpus {split} window metadata mismatch: {relative}")
        if not isinstance(entry.get("document_id"), str) or not entry["document_id"]:
            raise ValueError(f"corpus {split} document identity missing: {relative}")
    return len(entries)


def validate_corpus(corpus_root: Path, source_manifest_sha256: str) -> dict[str, Any]:
    corpus_root = _primary(corpus_root, "corpus root")
    manifest = _json(corpus_root / "manifest.json", "corpus manifest")
    if manifest.get("schema") != CORPUS_SCHEMA or manifest.get("state_slice") != STATE_SLICE:
        raise ValueError("corpus schema or state slice mismatch")
    if manifest.get("claim_ceiling") != CLAIM_CEILING or manifest.get("window_token_count") != WINDOW_TOKENS:
        raise ValueError("corpus identity or window length mismatch")
    _check_self_digest(manifest, "manifest_sha256", "corpus manifest")
    if manifest.get("source_manifest_sha256") != source_manifest_sha256:
        raise ValueError("corpus source binding mismatch")
    fit_count = _validate_window_files(corpus_root, manifest.get("fit"), "fit")
    assessment_count = _validate_window_files(corpus_root, manifest.get("assessment"), "assessment")
    if fit_count != 16 or assessment_count != 16:
        raise ValueError("corpus window counts mismatch")
    fit_ids = {entry["document_id"] for entry in manifest["fit"]}
    assessment_ids = {entry["document_id"] for entry in manifest["assessment"]}
    if fit_ids & assessment_ids:
        raise ValueError("corpus fit/assessment identity overlap")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "corpus_manifest_sha256": manifest["manifest_sha256"],
        "fit_window_count": fit_count,
        "assessment_window_count": assessment_count,
    }


def validate_result(result_root: Path, model_path: Path, corpus_manifest_sha256: str) -> dict[str, Any]:
    result_root = _primary(result_root, "result root")
    model_path = _external(model_path, "model path")
    config = _json(result_root / "config.json", "result config")
    results = _json(result_root / "results.json", "result results")
    receipt = _json(result_root / "receipt.json", "result receipt")
    for value, label in ((config, "config"), (results, "results"), (receipt, "receipt")):
        if value.get("schema") not in {RESULT_SCHEMA, None}:
            raise ValueError(f"{label} schema mismatch")
        if value.get("state_slice") != STATE_SLICE or value.get("claim_ceiling") != CLAIM_CEILING:
            raise ValueError(f"{label} identity mismatch")
    _check_self_digest(config, "config_sha256", "config")
    _check_self_digest(results, "results_sha256", "results")
    _check_self_digest(receipt, "receipt_sha256", "receipt")
    if config.get("source_schema") != SOURCE_SCHEMA or config.get("corpus_schema") != CORPUS_SCHEMA:
        raise ValueError("result schema binding mismatch")
    for value in (config, results, receipt):
        if value.get("corpus_manifest_sha256") != corpus_manifest_sha256:
            raise ValueError("result corpus binding mismatch")
    if config.get("dataset") != "fineweb_edu" or config.get("window_token_count") != WINDOW_TOKENS:
        raise ValueError("result dataset or window length mismatch")
    if config.get("candidate_pairs") != [list(pair) for pair in PILOT_PAIRS]:
        raise ValueError("candidate pair panel mismatch")
    for field, expected in {
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "evidence_ledger_mutation": False,
        "fit_window_count": 16,
        "assessment_window_count": 16,
        "evaluation_alpha": 0.15,
        "evaluation_beta": 0.85,
        "temperature_control": 1.2,
    }.items():
        if config.get(field) != expected:
            raise ValueError(f"result config mismatch: {field}")
    selected = config.get("selected_fit_config")
    if not isinstance(selected, dict) or [selected.get("source_layer"), selected.get("destination_layer")] not in [list(pair) for pair in PILOT_PAIRS]:
        raise ValueError("selected fit configuration is outside frozen panel")
    parity = results.get("parity")
    if not isinstance(parity, dict) or parity.get("all_passed") is not True:
        raise ValueError("parity gate did not pass")
    repeat_delta = results.get("assessment_repeat_max_metric_delta")
    if not isinstance(repeat_delta, (int, float)) or not math.isfinite(repeat_delta) or repeat_delta > PARITY_TOLERANCE:
        raise ValueError("deterministic repeat gate did not pass")
    if receipt.get("zero_alpha_parity_passed") is not True or receipt.get("deterministic_repeat_passed") is not True:
        raise ValueError("receipt controls did not pass")
    if not model_path.is_dir():
        raise FileNotFoundError(f"model path does not exist: {model_path}")
    if results.get("model_manifest_sha256") != config.get("model_manifest_sha256"):
        raise ValueError("model manifest binding is missing")
    from experiments.continual_learning import gemma3_paper_recirculation_v1 as engine

    if engine.model_manifest(model_path)["manifest_sha256"] != config["model_manifest_sha256"]:
        raise ValueError("cached model manifest changed or is incorrectly bound")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "claim_ceiling": CLAIM_CEILING,
        "config_sha256": config["config_sha256"],
        "results_sha256": results["results_sha256"],
        "receipt_sha256": receipt["receipt_sha256"],
        "assessment_mean_nll_delta_selected_minus_baseline": receipt.get("assessment_mean_nll_delta_selected_minus_baseline"),
        "paper_expected_pair_recovered": results.get("paper_expected_pair_recovered"),
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-root", type=Path)
    group.add_argument("--corpus-root", type=Path)
    group.add_argument("--result-root", type=Path)
    parser.add_argument("--source-manifest-sha256")
    parser.add_argument("--corpus-manifest-sha256")
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.source_root is not None:
        value = validate_source(args.source_root)
    elif args.corpus_root is not None:
        if not args.source_manifest_sha256:
            parser.error("--source-manifest-sha256 is required with --corpus-root")
        value = validate_corpus(args.corpus_root, args.source_manifest_sha256)
    else:
        if not args.corpus_manifest_sha256 or args.model is None:
            parser.error("--corpus-manifest-sha256 and --model are required with --result-root")
        value = validate_result(args.result_root, args.model, args.corpus_manifest_sha256)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
