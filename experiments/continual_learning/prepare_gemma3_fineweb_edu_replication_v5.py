#!/usr/bin/env python3
"""Pack the fresh V5 FineWeb-Edu source after review acceptance.

State slice: continual-learning-gemma3-fineweb-edu-replication-v5.
The packer only reads pinned raw inputs and publishes one no-overwrite source.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from experiments.continual_learning import gemma3_fineweb_edu_replication_v5_contract as c
from experiments.continual_learning import validate_gemma3_fineweb_edu_replication_v5 as validator


def _staging_path(final: Path) -> Path:
    candidate = final.parent / f".{final.name}.staging-{os.getpid()}-{time.time_ns()}"
    if candidate.exists():
        raise FileExistsError(f"V5 staging root unexpectedly exists: {candidate}")
    return candidate


def _enter_native_sandbox() -> None:
    if sys.platform != "darwin" or c.native_network_denied():
        return
    if os.environ.get("V5_PACK_SANDBOX_REEXEC_ATTEMPTED") == "1":
        raise RuntimeError("V5 native network sandbox could not be proven")
    sandbox = shutil.which("sandbox-exec")
    if sandbox is None:
        raise RuntimeError("V5 sandbox-exec is unavailable; packing is closed")
    environment = os.environ.copy()
    environment["V5_PACK_SANDBOX_REEXEC_ATTEMPTED"] = "1"
    profile = "(version 1) (deny network*) (allow default)"
    os.execvpe(sandbox, [sandbox, "-p", profile, sys.executable, "-B", str(Path(__file__).resolve()), *sys.argv[1:]], environment)


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def _source_input_snapshot(raw: Path, prior: Path) -> dict[str, Any]:
    return {"raw": c.snapshot_files(raw, {f"dataset/{item['path']}" for item in c.DATASET_FILES}, "V5 raw root", allow_cache=True), "prior": c.snapshot_files(prior, {"acquisition-manifest.json", "fit/fineweb_edu.jsonl", "assessment/fineweb_edu.jsonl"}, "V5 prior-pilot source root")}


def _assert_source_input_snapshot(snapshot: dict[str, Any], raw: Path, prior: Path) -> None:
    if _source_input_snapshot(raw, prior) != snapshot:
        raise RuntimeError("V5 raw or prior source changed during packing")


def pack_source(source_root: Path = c.SOURCE_ROOT, raw_root: Path = c.RAW_ROOT, prior_root: Path = c.R1_SOURCE_ROOT, review_receipt: Path = c.REVIEW_RECEIPT_PATH) -> dict[str, Any]:
    final = c.exact_path(source_root, c.SOURCE_ROOT, "V5 source root")
    raw = c.exact_path(raw_root, c.RAW_ROOT, "V5 raw root")
    prior = c.exact_path(prior_root, c.R1_SOURCE_ROOT, "V5 prior-pilot source root")
    review = c.validate_review_receipt(review_receipt)
    review_path = c.exact_path(review_receipt, c.REVIEW_RECEIPT_PATH, "V5 review receipt")
    if final.exists():
        raise FileExistsError(f"V5 source final root already exists; refusing overwrite: {final}")
    c.require_native_network_denial()
    snapshot = c.snapshot_code_and_review()
    input_snapshot = _source_input_snapshot(raw, prior)
    raw_artifacts = validator._audit_raw(raw)
    prior_ids = validator._audit_prior(prior, raw)
    c.assert_code_and_review_snapshot(snapshot)
    _assert_source_input_snapshot(input_snapshot, raw, prior)
    staging = _staging_path(final)
    os.mkdir(staging)
    try:
        fit_dir = staging / "fit"
        assessment_dir = staging / "assessment"
        fit_dir.mkdir()
        assessment_dir.mkdir()
        for split, item in (("fit", c.DATASET_FILES[0]), ("assessment", c.DATASET_FILES[1])):
            rows = list(validator._parquet_rows(raw / "dataset" / item["path"], item, c.FRESH_ROW_START, c.FRESH_ROW_END))
            if len(rows) != c.FRESH_ROW_COUNT or any(row["document_id"] in prior_ids for row in rows):
                raise ValueError(f"V5 {split} source selection is not fresh and disjoint")
            _write_jsonl(staging / split / "fineweb_edu.jsonl", rows)
        _assert_source_input_snapshot(input_snapshot, raw, prior)
        datasets = {}
        for split, item in (("fit", c.DATASET_FILES[0]), ("assessment", c.DATASET_FILES[1])):
            normalized = staging / split / "fineweb_edu.jsonl"
            datasets[f"{split}/fineweb_edu"] = {"source": c.DATASET_SOURCE, "revision": c.DATASET_REVISION, "config": c.DATASET_CONFIG, "split": c.DATASET_SPLIT, "crawl": item["crawl"], "source_path": item["path"], "row_start": c.FRESH_ROW_START, "row_count": c.FRESH_ROW_COUNT, "normalized_path": f"{split}/fineweb_edu.jsonl", "normalized_byte_len": normalized.stat().st_size, "normalized_sha256": c.sha256_file(normalized)}
        manifest = {"schema": c.SOURCE_SCHEMA, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "source_record_schema": "gemma3-source-v1-compatible-with-fineweb-metadata", "selection_policy": "rows-2048-through-18431-two-pinned-crawls-v5", "raw_root": str(c.RAW_ROOT), "prior_pilot_source_root": str(c.R1_SOURCE_ROOT), "prior_pilot_manifest_sha256": c.R1_SOURCE_MANIFEST_SHA256, "review_receipt_sha256": c.sha256_file(review_path), "dataset": validator._expected_dataset(), "fresh_row_range": {"start": c.FRESH_ROW_START, "end_exclusive": c.FRESH_ROW_END, "count_per_shard": c.FRESH_ROW_COUNT}, "prior_pilot_row_range": {"start": 0, "end_exclusive": 2_048, "count_per_shard": 2_048}, "raw_artifacts": raw_artifacts, "datasets": datasets, "network_access": False, "training": False, "scientific_execution": False, "evidence_ledger_mutation": False}
        manifest["manifest_sha256"] = c.digest(manifest)
        _write_json(staging / "acquisition-manifest.json", manifest)
        c.assert_code_and_review_snapshot(snapshot)
        _assert_source_input_snapshot(input_snapshot, raw, prior)
        c.exact_file_set(staging, {"acquisition-manifest.json", "fit/fineweb_edu.jsonl", "assessment/fineweb_edu.jsonl"}, "V5 staged source")
        validator.validate_source(staging, raw, prior, review_path)
        c.assert_code_and_review_snapshot(snapshot)
        _assert_source_input_snapshot(input_snapshot, raw, prior)
        output_files = {"acquisition-manifest.json", "fit/fineweb_edu.jsonl", "assessment/fineweb_edu.jsonl"}
        output_snapshot = c.snapshot_files(staging, output_files, "V5 staged source")
        if c.snapshot_files(staging, output_files, "V5 staged source") != output_snapshot:
            raise RuntimeError("V5 staged source changed before publication")
        c.publish_no_replace(staging, final, "V5 source", output_files)
        return {"published": True, "source_root": str(final), "source_manifest_sha256": c.sha256_file(final / "acquisition-manifest.json"), "reviewer": review["reviewer"]}
    except Exception:
        if staging.exists() and staging.is_dir():
            # Preserve a partial root for forensic inspection; never remove user data.
            pass
        raise


def main() -> int:
    _enter_native_sandbox()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=c.SOURCE_ROOT)
    parser.add_argument("--raw-root", type=Path, default=c.RAW_ROOT)
    parser.add_argument("--prior-root", type=Path, default=c.R1_SOURCE_ROOT)
    parser.add_argument("--review-receipt", type=Path, default=c.REVIEW_RECEIPT_PATH)
    args = parser.parse_args()
    print(json.dumps(pack_source(args.source_root, args.raw_root, args.prior_root, args.review_receipt), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
