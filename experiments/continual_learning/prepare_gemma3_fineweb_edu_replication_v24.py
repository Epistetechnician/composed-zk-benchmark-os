#!/usr/bin/env python3
"""Pack the reviewed V24 fresh FineWeb-Edu source.

State slice: continual-learning-gemma3-fineweb-edu-replication-v24.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from experiments.continual_learning import (
    gemma3_fineweb_edu_replication_v24_contract as c,
)
from experiments.continual_learning import (
    validate_gemma3_fineweb_edu_replication_v24 as v,
)


def _sandbox() -> None:
    if sys.platform != "darwin" or c.native_network_denied():
        return
    if os.environ.get("V24_PACK_REEXEC") == "1":
        raise RuntimeError("V24 native network denial could not be established")
    executable = shutil.which("sandbox-exec")
    if executable is None:
        raise RuntimeError("sandbox-exec is unavailable")
    env = os.environ.copy()
    env["V24_PACK_REEXEC"] = "1"
    os.execvpe(
        executable,
        [
            executable,
            "-p",
            "(version 1) (deny network*) (allow default)",
            sys.executable,
            "-B",
            str(Path(__file__).resolve()),
            *sys.argv[1:],
        ],
        env,
    )


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def _inputs(raw: Path, prior: Path) -> dict[str, Any]:
    return {
        "raw": c.snapshot_files(
            raw, {f"dataset/{item['path']}" for item in c.DATASET_FILES}, "V24 raw"
        ),
        "prior": c.snapshot_files(
            prior,
            {
                "acquisition-manifest.json",
                "fit/fineweb_edu.jsonl",
                "assessment/fineweb_edu.jsonl",
            },
            "V24 prior",
        ),
    }


def pack_source(
    source_root: Path = c.SOURCE_ROOT,
    raw_root: Path = c.RAW_ROOT,
    prior_root: Path = c.PRIOR_ROOT,
    receipt: Path = c.RECEIPT_PATH,
) -> dict[str, Any]:
    final, raw, prior = (
        c.exact_path(source_root, c.SOURCE_ROOT, "V24 source"),
        c.exact_path(raw_root, c.RAW_ROOT, "V24 raw"),
        c.exact_path(prior_root, c.PRIOR_ROOT, "V24 prior"),
    )
    if final.exists():
        raise FileExistsError(f"V24 source exists: {final}")
    c.require_native_network_denial()
    review = c.validate_review_receipt(receipt)
    review_path = c.exact_path(receipt, c.RECEIPT_PATH, "V24 receipt")
    code_snapshot, input_snapshot = c.snapshot_code(), _inputs(raw, prior)
    raw_artifacts, prior_ids = v.audit_raw(raw), v.audit_prior(prior, raw)
    c.assert_code_snapshot(code_snapshot)
    if _inputs(raw, prior) != input_snapshot:
        raise RuntimeError("V24 source inputs changed before packing")
    staging = final.parent / f".{final.name}.staging-{os.getpid()}"
    if staging.exists():
        raise FileExistsError(f"V24 staging exists: {staging}")
    staging.mkdir()
    try:
        for split, item in (
            ("fit", c.DATASET_FILES[0]),
            ("assessment", c.DATASET_FILES[1]),
        ):
            directory = staging / split
            directory.mkdir()
            rows = list(
                v.parquet_rows(
                    raw / "dataset" / item["path"],
                    item,
                    c.FRESH_ROW_START,
                    c.FRESH_ROW_END,
                )
            )
            if len(rows) != c.FRESH_ROW_COUNT or any(
                row["document_id"] in prior_ids for row in rows
            ):
                raise ValueError("V24 source is not fresh and disjoint")
            _write_jsonl(directory / "fineweb_edu.jsonl", rows)
        datasets = {}
        for split, item in (
            ("fit", c.DATASET_FILES[0]),
            ("assessment", c.DATASET_FILES[1]),
        ):
            path = staging / split / "fineweb_edu.jsonl"
            datasets[f"{split}/fineweb_edu"] = {
                "source": c.DATASET_SOURCE,
                "revision": c.DATASET_REVISION,
                "config": c.DATASET_CONFIG,
                "split": c.DATASET_SPLIT,
                "crawl": item["crawl"],
                "source_path": item["path"],
                "row_start": c.FRESH_ROW_START,
                "row_count": c.FRESH_ROW_COUNT,
                "normalized_path": f"{split}/fineweb_edu.jsonl",
                "normalized_byte_len": path.stat().st_size,
                "normalized_sha256": c.sha256_file(path),
            }
        body = {
            "schema": c.SOURCE_SCHEMA,
            "state_slice": c.STATE_SLICE,
            "claim_ceiling": c.CLAIM_CEILING,
            "source_record_schema": "gemma3-source-v1-compatible-with-fineweb-metadata",
                "selection_policy": "rows-18432-through-34815-two-pinned-crawls-v24",
            "raw_root": str(c.RAW_ROOT),
            "prior_root": str(c.PRIOR_ROOT),
            "prior_manifest_sha256": c.PRIOR_MANIFEST_SHA256,
            "review_receipt_sha256": c.sha256_file(review_path),
            "dataset": v.expected_dataset(),
            "fresh_row_range": {
                "start": c.FRESH_ROW_START,
                "end_exclusive": c.FRESH_ROW_END,
                "count_per_shard": c.FRESH_ROW_COUNT,
            },
            "prior_row_range": {
                "start": 0,
                "end_exclusive": 2_048,
                "count_per_shard": 2_048,
            },
            "raw_artifacts": raw_artifacts,
            "prior_history": c.validate_prior_history(),
            "datasets": datasets,
            "network_access": False,
            "training": False,
            "scientific_execution": False,
            "evidence_ledger_mutation": False,
        }
        _write_json(
            staging / "acquisition-manifest.json",
            {**body, "manifest_sha256": c.digest(body)},
        )
        c.assert_code_snapshot(code_snapshot)
        if _inputs(raw, prior) != input_snapshot:
            raise RuntimeError("V24 source inputs changed during packing")
        v.validate_source(staging, raw, prior, receipt)
        c.assert_code_snapshot(code_snapshot)
        if _inputs(raw, prior) != input_snapshot:
            raise RuntimeError("V24 source inputs changed before publication")
        files = {
            "acquisition-manifest.json",
            "fit/fineweb_edu.jsonl",
            "assessment/fineweb_edu.jsonl",
        }
        c.publish_no_replace(
            staging,
            final,
            files,
            "V24 source",
            lambda: (
                c.assert_code_snapshot(code_snapshot),
                None
                if _inputs(raw, prior) == input_snapshot
                else (_ for _ in ()).throw(
                    RuntimeError("V24 source inputs changed after publication")
                ),
            ),
        )
        return {
            "published": True,
            "source_root": str(final),
            "source_manifest_sha256": c.sha256_file(
                final / "acquisition-manifest.json"
            ),
            "reviewer": review["reviewer"],
        }
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise


def main() -> int:
    _sandbox()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=c.SOURCE_ROOT)
    parser.add_argument("--raw-root", type=Path, default=c.RAW_ROOT)
    parser.add_argument("--prior-root", type=Path, default=c.PRIOR_ROOT)
    parser.add_argument("--review-receipt", type=Path, default=c.RECEIPT_PATH)
    args = parser.parse_args()
    print(
        json.dumps(
            pack_source(
                args.source_root, args.raw_root, args.prior_root, args.review_receipt
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())









