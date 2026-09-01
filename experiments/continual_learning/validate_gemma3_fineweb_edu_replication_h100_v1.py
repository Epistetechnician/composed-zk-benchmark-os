#!/usr/bin/env python3
"""Independent aggregate-only validator for the H100 replication result.

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v1.

This validator never imports or executes the H100 runner, never loads model
weights, and never contacts GiveMeANode.  It rederives corpus bindings,
configuration, controls, bootstrap uncertainty, and the final decision from
the retained scalar result.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import platform
import re
from pathlib import Path
from typing import Any, Sequence


STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-h100-v1"
RESULT_SCHEMA = "gemma3-fineweb-edu-replication-h100-v1-result"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-h100-v1-corpus"
WINDOW_TOKENS = 1024
WINDOW_COUNT = 64
FIT_ALPHA, FIT_BETA = 0.10, 0.90
EVALUATION_ALPHA, EVALUATION_BETA = 0.15, 0.85
TEMPERATURE_CONTROL = 1.20
PARITY_TOLERANCE = 1e-5
CANDIDATE_PAIRS = ((7, 2), (9, 3), (11, 4), (12, 5))
BOOTSTRAP_RESAMPLES, BOOTSTRAP_SEED, BOOTSTRAP_CONFIDENCE = 10_000, 2_026_0829, 0.95
CONTROL_NAMES = (
    "native_baseline",
    "zero_alpha_identity",
    "all_candidate_evaluations",
    "temperature_1.20_baseline",
    "temperature_1.20_intervention",
    "deterministic_repeat",
    "frozen_model_manifest",
    "frozen_model_parameters",
)
RESULT_KEYS = {
    "schema", "state_slice", "claim_ceiling", "runtime", "launch_manifest_sha256",
    "protocol_sha256", "packet_sha256", "review_receipt_sha256",
    "implementation_manifest_sha256", "code_bundle_sha256", "runtime_lock_sha256", "data_manifest_sha256",
    "source_manifest_sha256",
    "container_digest",
    "hard_usd_ceiling", "estimated_max_total_usd", "model_manifest_sha256",
    "model_parameter_digest_before", "model_parameter_digest_after",
    "corpus_manifest_sha256", "candidate_pairs", "fit_alpha", "fit_beta",
    "evaluation_alpha", "evaluation_beta", "temperature_control", "normalization",
    "selected_fit_config", "locked_evaluation_config", "paper_expected_pair",
    "paper_expected_pair_recovered", "fit_baseline", "fit_candidates",
    "assessment_baseline", "assessment_selected", "assessment_temperature_baseline",
    "assessment_temperature_selected", "assessment_repeat", "assessment_per_document",
    "controls", "qualification", "bootstrap", "decision", "training",
    "weights_frozen", "network_access", "evidence_ledger_mutation", "effects_run",
    "assessment_authorized_by_review", "assessment_windows_per_h100_minute",
    "elapsed_seconds", "results_sha256",
}
METRIC_KEYS = {"temperature", "evaluation_config", "mean_nll", "perplexity", "target_tokens", "rows"}
METRIC_ROW_KEYS = {"dataset", "document_id", "relative_path", "window_ordinal", "source_sha256", "source_row_sha256", "source_row_index", "source_row_id", "text_sha256", "token_count", "target_count", "nll"}
LAUNCH_KEYS = {
    "schema", "state_slice", "provider", "node_type", "job_mode",
    "hard_usd_ceiling", "quoted_gpu_usd_per_minute", "max_runtime_minutes",
    "estimated_max_total_usd", "provider_project", "container_image",
    "container_digest", "cuda_driver_version", "container_network_mode", "code_bundle_path", "code_bundle_sha256",
    "runner_entrypoint", "runtime_lock_path", "runtime_lock_sha256",
    "network_lock", "implementation_manifest_path",
    "implementation_manifest_sha256", "model_bundle_path",
    "model_manifest_sha256", "data_bundle_path", "data_manifest_sha256",
    "source_manifest_sha256",
    "external_storage_namespace", "review_receipt_path",
    "review_receipt_sha256", "protocol_sha256", "packet_sha256",
    "launch_command", "launch_command_sha256", "stop_rule",
    "assessment_enabled", "training_enabled", "network_during_effects",
    "effects_run", "manifest_sha256",
}
REVIEW_FINDINGS = {
    "custody_and_fresh_disjoint_cohort",
    "provider_shape_and_hard_budget_gate",
    "runtime_and_model_freeze",
    "qualification_and_network_boundary",
    "locked_recurrence_controls_and_uncertainty",
    "independent_validator_and_publication_order",
    "v31_identity_preserved_without_cross_runtime_claim",
}
REVIEWED_FILES = (
    "docs/research/continual-learning/252-gemma3-fineweb-edu-replication-h100-v1-protocol.md",
    "docs/research/continual-learning/253-gemma3-fineweb-edu-replication-h100-v1-review-packet.md",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v1_preflight.py",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v1.py",
    "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_h100_v1.py",
    "experiments/continual_learning/pack_gemma3_fineweb_edu_replication_h100_v1.py",
    "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v1_preflight.py",
    "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v1.py",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v1_provider/Dockerfile",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v1_provider/requirements.lock",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v1_provider/runtime-lock.json",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v1_provider/run_h100_v1.sh",
    "AGENTS.md",
    "docs/research/continual-learning/254-gemma3-fineweb-edu-replication-h100-v1-implementation-manifest.json",
)
IMPLEMENTATION_FILES = tuple(
    path for path in REVIEWED_FILES
    if path != "docs/research/continual-learning/254-gemma3-fineweb-edu-replication-h100-v1-implementation-manifest.json"
)
REVIEW_RECEIPT_KEYS = {
    "schema", "state_slice", "review_decision", "reviewer", "reviewed_at_utc",
    "reviewed_files", "reviewed_file_sha256", "protocol_sha256",
    "review_packet_sha256", "implementation_manifest_sha256", "findings",
    "effects_run", "receipt_sha256",
}
STOP_RULE = "terminate at first failed gate or budget boundary"
PROVIDER_RECEIPT_SCHEMA = "gemma3-fineweb-edu-replication-h100-v1-provider-receipt"
PROVIDER_RECEIPT_KEYS = {
    "schema",
    "state_slice",
    "provider",
    "provider_project",
    "node_type",
    "job_mode",
    "allocation_id",
    "node_id",
    "start_utc",
    "stop_utc",
    "quoted_gpu_usd_per_minute",
    "charged_usd",
    "hard_usd_ceiling",
    "stop_reason",
    "launch_manifest_sha256",
    "container_digest",
    "receipt_sha256",
}
DATASET_REPO = "HuggingFaceFW/fineweb-edu"
DATASET_REVISION = "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
DATASET_SOURCE = f"https://huggingface.co/datasets/{DATASET_REPO}"
DATASET_CONFIG = "fineweb-edu-crawl-shards"
DATASET_SPLIT = "train"
DATASET_FILES = (
    {"crawl": "CC-MAIN-2013-20", "path": "data/CC-MAIN-2013-20/train-00000-of-00014.parquet", "byte_len": 2_369_456_837, "sha256": "fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03"},
    {"crawl": "CC-MAIN-2024-10", "path": "data/CC-MAIN-2024-10/000_00000.parquet", "byte_len": 1_911_528_585, "sha256": "89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484"},
)
FRESH_START, FRESH_END = 34_816, 51_200
EXCLUSION_RANGES = (("prior-pilot", 0, 2_048), ("prior-v31", 2_048, 18_432), ("discarded", 18_432, FRESH_START))
SOURCE_ROW_KEYS = {"document_id", "text", "metadata", "source_crawl", "source_path", "source_row_index", "source_row_id", "source_row_sha256"}


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(value: dict[str, Any], field: str) -> str:
    return hashlib.sha256(canonical({key: item for key, item in value.items() if key != field})).hexdigest()


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def canonical_jsonl(rows: Sequence[dict[str, Any]]) -> bytes:
    return b"".join(
        (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for row in rows
    )


def external_runtime_path(path: Path, repo_root: Path, label: str) -> Path:
    path = path.expanduser()
    if path.is_symlink():
        raise ValueError(f"{label} must not be a symlink")
    resolved = path.resolve()
    repository = repo_root.expanduser().resolve()
    if resolved == repository or repository in resolved.parents:
        raise ValueError(f"{label} must be outside the provider code root")
    if not resolved.is_absolute():
        raise ValueError(f"{label} must be absolute")
    return resolved


def finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{label} must be finite non-boolean numeric")
    return float(value)


def hex_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be SHA-256 hex")
    try:
        int(value, 16)
    except ValueError as error:
        raise ValueError(f"{label} must be SHA-256 hex") from error
    return value


def obj(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} must be a regular file")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def require_read_only_tree(root: Path, label: str) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"{label} root is not a real directory")
    if root.stat().st_mode & 0o222:
        raise ValueError(f"{label} root is mutable")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"{label} contains symlink")
        if path.stat().st_mode & 0o222:
            raise ValueError(f"{label} contains mutable entry: {path}")


def validate_provider_receipt(path: Path, launch: dict[str, Any], launch_sha256: str) -> dict[str, Any]:
    receipt = obj(path, "provider receipt")
    if set(receipt) != PROVIDER_RECEIPT_KEYS:
        raise ValueError("provider receipt schema is not closed")
    if (
        receipt["schema"] != PROVIDER_RECEIPT_SCHEMA
        or receipt["state_slice"] != STATE_SLICE
        or receipt["provider"] != launch["provider"]
        or receipt["provider_project"] != launch["provider_project"]
        or receipt["node_type"] != launch["node_type"]
        or receipt["job_mode"] != launch["job_mode"]
        or receipt["container_digest"] != launch["container_digest"]
        or receipt["launch_manifest_sha256"] != launch_sha256
    ):
        raise ValueError("provider receipt identity or launch binding mismatch")
    for field in ("allocation_id", "node_id", "stop_reason"):
        if not isinstance(receipt[field], str) or not receipt[field].strip():
            raise ValueError(f"provider receipt {field} is missing")
    for field in ("start_utc", "stop_utc"):
        if not isinstance(receipt[field], str) or not receipt[field].endswith("Z"):
            raise ValueError(f"provider receipt {field} is invalid")
        try:
            timestamp = dt.datetime.fromisoformat(receipt[field].replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError(f"provider receipt {field} is invalid") from error
        if timestamp.tzinfo is None or timestamp.utcoffset() != dt.timedelta(0):
            raise ValueError(f"provider receipt {field} is not UTC")
    quote = finite(receipt["quoted_gpu_usd_per_minute"], "provider quote")
    charged = finite(receipt["charged_usd"], "provider charged USD")
    ceiling = finite(receipt["hard_usd_ceiling"], "provider hard USD ceiling")
    if charged < 0:
        raise ValueError("provider charged USD must be nonnegative")
    if quote <= 0 or ceiling <= 0:
        raise ValueError("provider receipt quote/ceiling must be positive")
    if quote != finite(launch["quoted_gpu_usd_per_minute"], "launch quote"):
        raise ValueError("provider quote does not match launch manifest")
    if ceiling != finite(launch["hard_usd_ceiling"], "launch hard USD ceiling"):
        raise ValueError("provider ceiling does not match launch manifest")
    if charged > ceiling or charged > finite(launch["estimated_max_total_usd"], "launch estimated USD"):
        raise ValueError("provider charge exceeds the sealed budget")
    if receipt["receipt_sha256"] != digest(receipt, "receipt_sha256"):
        raise ValueError("provider receipt self digest mismatch")
    return receipt


def _json_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _parquet_rows(path: Path, item: dict[str, Any], start: int, end: int) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    if "text" not in parquet.schema.names:
        raise ValueError(f"raw shard lacks text column: {path}")
    fields = [field for field in ("id", "url", "date", "dump", "file_path", "language", "language_score", "token_count", "score", "int_score") if field in parquet.schema.names]
    columns = ["text", *fields]
    rows: list[dict[str, Any]] = []
    position = 0
    for batch in parquet.iter_batches(columns=columns, batch_size=256):
        values = {name: batch.column(name).to_pylist() for name in columns}
        for offset in range(batch.num_rows):
            if start <= position < end:
                text = values["text"][offset]
                if not isinstance(text, str) or not text.strip():
                    raise ValueError(f"raw row text invalid: {path}:{position}")
                source_row_id = values.get("id", [None] * batch.num_rows)[offset]
                if not isinstance(source_row_id, str) or not source_row_id:
                    source_row_id = f"row-{position:08d}"
                body = {
                    "document_id": f"fineweb-edu:{item['crawl']}:{source_row_id}",
                    "text": text,
                    "metadata": {field: _json_value(values[field][offset]) for field in fields if values[field][offset] is not None},
                    "source_crawl": item["crawl"],
                    "source_path": item["path"],
                    "source_row_index": position,
                    "source_row_id": source_row_id,
                }
                rows.append({**body, "source_row_sha256": digest(body, "source_row_sha256")})
            position += 1
            if position >= end:
                break
        if position >= end:
            break
    if len(rows) != end - start:
        raise ValueError(f"raw row range count mismatch: {path}")
    return rows


def _raw_artifacts(raw_root: Path) -> list[dict[str, Any]]:
    import pyarrow.parquet as pq

    dataset_root = raw_root / "dataset"
    expected = {Path("dataset") / item["path"] for item in DATASET_FILES}
    actual = set()
    for path in raw_root.rglob("*"):
        if path.is_symlink():
            raise ValueError("raw bundle contains symlink")
        if path.is_file():
            actual.add(path.relative_to(raw_root))
    if actual != expected:
        raise ValueError("raw bundle exact Parquet file set mismatch")
    artifacts = []
    for item in DATASET_FILES:
        path = obj_path = raw_root / "dataset" / item["path"]
        if obj_path.stat().st_size != item["byte_len"] or sha256_file(obj_path) != item["sha256"]:
            raise ValueError(f"raw Parquet pin mismatch: {path}")
        count = pq.ParquetFile(obj_path).metadata.num_rows
        if count < FRESH_END:
            raise ValueError("raw Parquet shard is shorter than the fresh range")
        artifacts.append({"crawl": item["crawl"], "relative_path": obj_path.relative_to(raw_root).as_posix(), "source": f"{DATASET_SOURCE}/resolve/{DATASET_REVISION}/{item['path']}", "byte_len": obj_path.stat().st_size, "sha256": sha256_file(obj_path), "row_count": count})
    return artifacts


def source_bundle(raw_root: Path, source_root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    require_read_only_tree(raw_root, "raw bundle")
    require_read_only_tree(source_root, "source bundle")
    expected_paths = {"manifest.json", "fit/fineweb_edu.jsonl", "assessment/fineweb_edu.jsonl"}
    actual_paths = {path.relative_to(source_root).as_posix() for path in source_root.rglob("*") if path.is_file()}
    if actual_paths != expected_paths:
        raise ValueError("source bundle exact file set mismatch")
    manifest = obj(source_root / "manifest.json", "source manifest")
    required = {"schema", "state_slice", "dataset", "raw_root", "raw_artifacts", "fresh_row_range", "split_sources", "excluded_ranges", "excluded_id_sha256", "network_access", "training", "scientific_execution", "evidence_ledger_mutation", "manifest_sha256"}
    if set(manifest) != required or manifest["schema"] != "gemma3-fineweb-edu-replication-h100-v1-source" or manifest["state_slice"] != STATE_SLICE or manifest["dataset"] != {"repo": DATASET_REPO, "source": DATASET_SOURCE, "revision": DATASET_REVISION, "config": DATASET_CONFIG, "split": DATASET_SPLIT} or manifest["raw_root"] != "raw" or manifest["fresh_row_range"] != {"start": FRESH_START, "end_exclusive": FRESH_END, "count_per_shard": FRESH_END - FRESH_START} or manifest["excluded_ranges"] != [{"name": n, "start": s, "end_exclusive": e, "count_per_shard": e - s} for n, s, e in EXCLUSION_RANGES] or any(manifest[name] is not False for name in ("network_access", "training", "scientific_execution", "evidence_ledger_mutation")) or manifest["manifest_sha256"] != digest(manifest, "manifest_sha256"):
        raise ValueError("source manifest contract mismatch")
    if manifest["raw_artifacts"] != _raw_artifacts(raw_root):
        raise ValueError("source raw artifact binding mismatch")
    excluded_ids = []
    for item in DATASET_FILES:
        for _name, start, end in EXCLUSION_RANGES:
            excluded_ids.extend(row["document_id"] for row in _parquet_rows(raw_root / "dataset" / item["path"], item, start, end))
    if len(excluded_ids) != 2 * FRESH_START or len(set(excluded_ids)) != len(excluded_ids) or manifest["excluded_id_sha256"] != hashlib.sha256(canonical(excluded_ids)).hexdigest():
        raise ValueError("source exclusion identity mismatch")
    rows_by_id: dict[str, dict[str, Any]] = {}
    split_sources = manifest["split_sources"]
    if not isinstance(split_sources, dict) or set(split_sources) != {"fit", "assessment"}:
        raise ValueError("source split metadata schema mismatch")
    for split, item in (("fit", DATASET_FILES[0]), ("assessment", DATASET_FILES[1])):
        metadata = split_sources[split]
        expected_metadata = {"crawl": item["crawl"], "source_path": item["path"], "row_start": FRESH_START, "row_end_exclusive": FRESH_END, "normalized_path": f"{split}/fineweb_edu.jsonl"}
        if not isinstance(metadata, dict) or set(metadata) != set(expected_metadata) | {"normalized_sha256"} or any(metadata.get(key) != value for key, value in expected_metadata.items()):
            raise ValueError(f"source {split} metadata mismatch")
        path = source_root / metadata["normalized_path"]
        if sha256_file(path) != metadata.get("normalized_sha256"):
            raise ValueError(f"source {split} digest mismatch")
        observed = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        expected = _parquet_rows(raw_root / "dataset" / item["path"], item, FRESH_START, FRESH_END)
        if path.read_bytes() != canonical_jsonl(expected) or len(observed) != len(expected) or any(not isinstance(row, dict) or set(row) != SOURCE_ROW_KEYS for row in observed) or observed != expected:
            raise ValueError(f"source {split} rows do not rederive from raw custody")
        for row in observed:
            if row["document_id"] in rows_by_id:
                raise ValueError("source fit/assessment IDs overlap")
            rows_by_id[row["document_id"]] = row
    return manifest, rows_by_id


def validate_tree_manifest(root: Path, expected_sha256: str) -> None:
    require_read_only_tree(root, "model bundle")
    manifest = obj(root / "model-manifest.json", "model manifest")
    if set(manifest) != {"schema", "files", "manifest_sha256"} or manifest["schema"] != "sealed-file-tree-v1":
        raise ValueError("model manifest schema mismatch")
    if manifest["manifest_sha256"] != digest(manifest, "manifest_sha256") or manifest["manifest_sha256"] != expected_sha256:
        raise ValueError("model manifest digest mismatch")
    entries = manifest["files"]
    if not isinstance(entries, list) or len({item.get("path") for item in entries if isinstance(item, dict)}) != len(entries):
        raise ValueError("model manifest entries invalid")
    actual = set()
    for candidate in root.rglob("*"):
        if candidate.is_symlink():
            raise ValueError("model bundle contains symlink")
        if candidate.is_file() and candidate.name != "model-manifest.json":
            actual.add(candidate.relative_to(root).as_posix())
    expected = set()
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"path", "byte_len", "sha256"}:
            raise ValueError("model manifest entry schema mismatch")
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("model manifest path unsafe")
        expected.add(relative.as_posix())
        path = root / relative
        hex_digest(item["sha256"], "model file digest")
        if path.is_symlink() or not path.is_file() or path.stat().st_size != item["byte_len"] or sha256_file(path) != item["sha256"]:
            raise ValueError(f"model file custody mismatch: {relative}")
    if actual != expected:
        raise ValueError("model manifest file set mismatch")


def validate_launch_binding(path: Path, repo_root: Path, result: dict[str, Any]) -> None:
    launch = obj(path, "launch manifest")
    if set(launch) != LAUNCH_KEYS or launch.get("schema") != "gemma3-fineweb-edu-replication-h100-v1-launch-manifest" or launch.get("state_slice") != STATE_SLICE:
        raise ValueError("launch manifest identity mismatch")
    if launch.get("manifest_sha256") != digest(launch, "manifest_sha256"):
        raise ValueError("launch manifest self digest mismatch")
    if launch.get("provider") != "givemeanode" or launch.get("node_type") != "h100-1" or launch.get("job_mode") != "batch":
        raise ValueError("launch provider shape mismatch")
    if launch.get("container_network_mode") != "none":
        raise ValueError("launch container network mode is not none")
    if launch.get("assessment_enabled") is not True or launch.get("training_enabled") is not False or launch.get("network_during_effects") is not False or launch.get("effects_run") is not False:
        raise ValueError("launch safety flags invalid")
    ceiling = finite(launch.get("hard_usd_ceiling"), "launch hard USD ceiling")
    estimate = finite(launch.get("estimated_max_total_usd"), "launch estimated USD")
    rate = finite(launch.get("quoted_gpu_usd_per_minute"), "launch quote")
    minutes = finite(launch.get("max_runtime_minutes"), "launch maximum runtime")
    if min(ceiling, estimate, rate, minutes) <= 0 or rate * minutes > estimate or estimate > ceiling:
        raise ValueError("launch budget arithmetic invalid")
    if launch.get("runner_entrypoint") != "run_h100_v1.sh" or launch.get("launch_command") != "./run_h100_v1.sh" or launch.get("network_lock") != "network-none-v1" or launch.get("launch_command_sha256") != hashlib.sha256(b"./run_h100_v1.sh").hexdigest():
        raise ValueError("launch command/network binding invalid")
    if launch.get("stop_rule") != STOP_RULE:
        raise ValueError("launch stop rule is not exact")
    if launch.get("runtime_lock_path") != "runtime-lock.json":
        raise ValueError("launch runtime lock path is not the reviewed provider lock")
    for field in ("review_receipt_path", "implementation_manifest_path"):
        relative = Path(launch[field])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"launch {field} must be repository-relative")
    for field in ("protocol_sha256", "packet_sha256", "review_receipt_sha256", "implementation_manifest_sha256", "code_bundle_sha256", "runtime_lock_sha256", "model_manifest_sha256", "data_manifest_sha256", "source_manifest_sha256"):
        hex_digest(launch.get(field), f"launch {field}")
    if not isinstance(launch.get("container_digest"), str) or not launch["container_digest"].startswith("sha256:"):
        raise ValueError("launch container digest invalid")
    hex_digest(launch["container_digest"][7:], "launch container digest")
    if launch["manifest_sha256"] != result["launch_manifest_sha256"] or launch["hard_usd_ceiling"] != result["hard_usd_ceiling"] or launch["estimated_max_total_usd"] != result["estimated_max_total_usd"]:
        raise ValueError("result launch binding mismatch")
    for field in ("protocol_sha256", "packet_sha256", "review_receipt_sha256", "implementation_manifest_sha256", "code_bundle_sha256", "runtime_lock_sha256", "data_manifest_sha256", "source_manifest_sha256", "container_digest"):
        if launch[field] != result[field]:
            raise ValueError(f"result launch {field} mismatch")
    protocol = repo_root / "docs/research/continual-learning/252-gemma3-fineweb-edu-replication-h100-v1-protocol.md"
    packet = repo_root / "docs/research/continual-learning/253-gemma3-fineweb-edu-replication-h100-v1-review-packet.md"
    if sha256_file(protocol) != launch["protocol_sha256"] or sha256_file(packet) != launch["packet_sha256"]:
        raise ValueError("launch reviewed bytes changed")
    review_path = Path(launch["review_receipt_path"])
    if not review_path.is_absolute():
        review_path = repo_root / review_path
    review = obj(review_path, "review receipt")
    if set(review) != REVIEW_RECEIPT_KEYS or review.get("schema") != "gemma3-fineweb-edu-replication-h100-v1-independent-review":
        raise ValueError("launch review receipt schema mismatch")
    if (
        review.get("state_slice") != STATE_SLICE
        or review.get("review_decision") != "ACCEPT"
        or review.get("effects_run") is not False
        or not isinstance(review.get("reviewer"), str)
        or not review["reviewer"].strip()
        or not isinstance(review.get("reviewed_at_utc"), str)
        or not review["reviewed_at_utc"].endswith("Z")
        or review.get("protocol_sha256") != launch["protocol_sha256"]
        or review.get("review_packet_sha256") != launch["packet_sha256"]
        or review.get("implementation_manifest_sha256") != launch["implementation_manifest_sha256"]
        or set(review.get("findings", {})) != REVIEW_FINDINGS
        or any(review["findings"].get(name) is not True for name in REVIEW_FINDINGS)
    ):
        raise ValueError("launch review receipt is not a bound ACCEPT")
    try:
        timestamp = dt.datetime.fromisoformat(review["reviewed_at_utc"].replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("launch review timestamp invalid") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() != dt.timedelta(0):
        raise ValueError("launch review timestamp is not UTC")
    if review.get("reviewed_files") != list(REVIEWED_FILES):
        raise ValueError("launch review receipt file binding mismatch")
    if not isinstance(review.get("reviewed_file_sha256"), dict) or set(review["reviewed_file_sha256"]) != set(REVIEWED_FILES):
        raise ValueError("launch review receipt digest map mismatch")
    for relative in REVIEWED_FILES:
        reviewed_path = repo_root / relative
        if reviewed_path.is_symlink() or not reviewed_path.is_file() or review["reviewed_file_sha256"][relative] != sha256_file(reviewed_path):
            raise ValueError(f"launch review current-byte mismatch: {relative}")
    if not isinstance(review.get("findings"), dict) or set(review["findings"]) != REVIEW_FINDINGS or any(review["findings"].get(name) is not True for name in REVIEW_FINDINGS):
        raise ValueError("launch review findings mismatch")
    if review.get("receipt_sha256") != digest(review, "receipt_sha256"):
        raise ValueError("launch review receipt self digest mismatch")
    if sha256_file(review_path) != launch["review_receipt_sha256"]:
        raise ValueError("launch review receipt digest mismatch")
    implementation_path = Path(launch["implementation_manifest_path"])
    if not implementation_path.is_absolute():
        implementation_path = repo_root / implementation_path
    implementation = obj(implementation_path, "implementation manifest")
    if implementation.get("manifest_sha256") != launch["implementation_manifest_sha256"] or implementation.get("manifest_sha256") != digest(implementation, "manifest_sha256"):
        raise ValueError("launch implementation manifest digest mismatch")
    if implementation.get("schema") != "gemma3-fineweb-edu-replication-h100-v1-implementation" or implementation.get("state_slice") != STATE_SLICE or [item.get("path") for item in implementation.get("files", [])] != list(IMPLEMENTATION_FILES):
        raise ValueError("launch implementation manifest file set mismatch")
    for item in implementation.get("files", []):
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise ValueError("launch implementation manifest entry invalid")
        relative = Path(item["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("launch implementation manifest path unsafe")
        implementation_file = repo_root / relative
        if implementation_file.is_symlink() or not implementation_file.is_file() or sha256_file(implementation_file) != item["sha256"]:
            raise ValueError(f"launch implementation file mismatch: {item.get('path')}")
    runtime_path = Path(launch["runtime_lock_path"])
    if runtime_path.is_absolute() or ".." in runtime_path.parts:
        raise ValueError("launch runtime lock path unsafe")
    if not runtime_path.is_absolute():
        runtime_path = repo_root / runtime_path
    if runtime_path.is_symlink() or not runtime_path.is_file() or sha256_file(runtime_path) != launch["runtime_lock_sha256"]:
        raise ValueError("launch runtime lock digest mismatch")
    runtime_lock = obj(runtime_path, "runtime lock")
    if set(runtime_lock) != {"schema", "state_slice", "python", "accelerate", "pytorch", "transformers", "safetensors", "tokenizers", "pyarrow", "cuda_runtime", "dtype", "gpu_required", "network_policy", "package_install_at_runtime"} or runtime_lock["schema"] != "gemma3-fineweb-edu-replication-h100-v1-runtime-lock" or runtime_lock["state_slice"] != STATE_SLICE or runtime_lock["dtype"] != "bfloat16" or runtime_lock["gpu_required"] != "NVIDIA H100" or runtime_lock["network_policy"] != "network-none-v1" or runtime_lock["package_install_at_runtime"] is not False:
        raise ValueError("runtime lock contract mismatch")


def corpus(
    root: Path,
    source_rows: dict[str, dict[str, Any]],
    source_manifest_sha256: str,
    tokenizer: Any,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], str]:
    require_read_only_tree(root, "corpus")
    expected = {"manifest.json", "fit/windows.jsonl", "assessment/windows.jsonl"}
    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}
    if actual != expected:
        raise ValueError("corpus exact file set mismatch")
    manifest = obj(root / "manifest.json", "corpus manifest")
    if set(manifest) != {"schema", "state_slice", "source_manifest_sha256", "model_bundle_path", "model_manifest_sha256", "fit_sha256", "assessment_sha256", "window_tokens", "fit_window_count", "assessment_window_count", "manifest_sha256"}:
        raise ValueError("corpus manifest schema mismatch")
    if manifest["schema"] != CORPUS_SCHEMA or manifest["state_slice"] != STATE_SLICE or manifest["source_manifest_sha256"] != source_manifest_sha256 or manifest["model_bundle_path"] != "model" or manifest["window_tokens"] != WINDOW_TOKENS or manifest["fit_window_count"] != WINDOW_COUNT or manifest["assessment_window_count"] != WINDOW_COUNT or manifest["manifest_sha256"] != digest(manifest, "manifest_sha256"):
        raise ValueError("corpus manifest identity/digest mismatch")
    rows_by_split: dict[str, dict[str, dict[str, Any]]] = {}
    for split in ("fit", "assessment"):
        path = root / f"{split}/windows.jsonl"
        if sha256_file(path) != manifest[f"{split}_sha256"]:
            raise ValueError(f"corpus {split} digest mismatch")
        rows: dict[str, dict[str, Any]] = {}
        with path.open(encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                value = json.loads(line)
                if not isinstance(value, dict) or set(value) != {
                    "dataset", "document_id", "relative_path", "window_ordinal", "text",
                    "source_sha256", "source_row_sha256", "source_row_index", "source_row_id",
                    "text_sha256", "token_count", "token_ids",
                }:
                    raise ValueError(f"corpus {split} row {number} schema mismatch")
                if not all(isinstance(value[key], str) and value[key].strip() for key in ("dataset", "document_id", "relative_path", "text")):
                    raise ValueError(f"corpus {split} row {number} string field mismatch")
                if value["dataset"] != "fineweb_edu" or value["relative_path"] != f"{split}/window-{number - 1:06d}.txt":
                    raise ValueError(f"corpus {split} row {number} location mismatch")
                if isinstance(value["window_ordinal"], bool) or value["window_ordinal"] != 0 or isinstance(value["token_count"], bool) or not isinstance(value["token_count"], int) or value["token_count"] != WINDOW_TOKENS or not isinstance(value["token_ids"], list) or len(value["token_ids"]) != WINDOW_TOKENS or any(isinstance(token, bool) or not isinstance(token, int) for token in value["token_ids"]):
                    raise ValueError(f"corpus {split} row {number} shape mismatch")
                hex_digest(value["source_sha256"], "corpus source digest")
                hex_digest(value["source_row_sha256"], "corpus source row digest")
                hex_digest(value["text_sha256"], "corpus text digest")
                if hashlib.sha256(value["text"].encode()).hexdigest() != value["text_sha256"]:
                    raise ValueError(f"corpus {split} row {number} text digest mismatch")
                if isinstance(value["source_row_index"], bool) or not isinstance(value["source_row_index"], int) or not isinstance(value["source_row_id"], str) or not value["source_row_id"]:
                    raise ValueError(f"corpus {split} row {number} source identity mismatch")
                source = source_rows.get(value["document_id"])
                expected_source_sha256 = hashlib.sha256(source["text"].encode()).hexdigest() if source is not None else None
                if source is None or any(value[key] != source[key] for key in ("source_row_sha256", "source_row_index", "source_row_id")) or value["source_sha256"] != expected_source_sha256:
                    raise ValueError(f"corpus {split} row {number} source binding mismatch")
                source_ids = tuple(tokenizer.encode(source["text"], add_special_tokens=False))
                window_ids = tuple(tokenizer.encode(value["text"], add_special_tokens=False))
                if source_ids[:WINDOW_TOKENS] != tuple(value["token_ids"]) or window_ids != tuple(value["token_ids"]):
                    raise ValueError(f"corpus {split} row {number} tokenization mismatch")
                if value["document_id"] in rows:
                    raise ValueError(f"corpus {split} duplicate document")
                rows[value["document_id"]] = value
        if len(rows) != WINDOW_COUNT:
            raise ValueError(f"corpus {split} count mismatch")
        rows_by_split[split] = rows
    if set(rows_by_split["fit"]) & set(rows_by_split["assessment"]):
        raise ValueError("corpus fit/assessment overlap")
    return rows_by_split["fit"], rows_by_split["assessment"], manifest["manifest_sha256"]


def config(value: Any, expected_alpha: float, expected_beta: float, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"source_layer", "destination_layer", "alpha", "beta", "epsilon"}:
        raise ValueError(f"{label} schema mismatch")
    if isinstance(value["source_layer"], bool) or not isinstance(value["source_layer"], int) or isinstance(value["destination_layer"], bool) or not isinstance(value["destination_layer"], int) or (value["source_layer"], value["destination_layer"]) not in CANDIDATE_PAIRS:
        raise ValueError(f"{label} layer pair invalid")
    if finite(value["alpha"], f"{label} alpha") != expected_alpha or finite(value["beta"], f"{label} beta") != expected_beta or finite(value["epsilon"], f"{label} epsilon") != 1e-6:
        raise ValueError(f"{label} constants invalid")
    return value


def metric(value: Any, windows: dict[str, dict[str, Any]], expected_temperature: float, expected_config: dict[str, Any] | None, label: str) -> None:
    if not isinstance(value, dict) or set(value) != METRIC_KEYS:
        raise ValueError(f"{label} metric schema mismatch")
    if finite(value["temperature"], f"{label} temperature") != expected_temperature or value["evaluation_config"] != expected_config:
        raise ValueError(f"{label} metric configuration mismatch")
    rows = value["rows"]
    if not isinstance(rows, list) or len(rows) != WINDOW_COUNT or isinstance(value["target_tokens"], bool) or not isinstance(value["target_tokens"], int) or value["target_tokens"] != WINDOW_COUNT * (WINDOW_TOKENS - 1):
        raise ValueError(f"{label} metric count mismatch")
    seen: set[str] = set()
    total = 0.0
    for row in rows:
        if not isinstance(row, dict) or set(row) != METRIC_ROW_KEYS:
            raise ValueError(f"{label} row schema mismatch")
        document = row["document_id"]
        if not isinstance(document, str):
            raise ValueError(f"{label} row document type mismatch")
        if document in seen or document not in windows:
            raise ValueError(f"{label} row document mismatch")
        seen.add(document)
        source = windows[document]
        if isinstance(row["window_ordinal"], bool) or isinstance(row["token_count"], bool) or not isinstance(row["token_count"], int) or isinstance(row["target_count"], bool) or not isinstance(row["target_count"], int) or isinstance(row["source_row_index"], bool) or not isinstance(row["source_row_index"], int) or not isinstance(row["source_row_id"], str) or not row["source_row_id"] or any(row[key] != source[key] for key in ("dataset", "relative_path", "window_ordinal", "source_sha256", "source_row_sha256", "source_row_index", "source_row_id", "text_sha256")) or row["token_count"] != WINDOW_TOKENS or row["target_count"] != WINDOW_TOKENS - 1:
            raise ValueError(f"{label} row corpus binding mismatch")
        hex_digest(row["source_row_sha256"], f"{label} source row digest")
        total += finite(row["nll"], f"{label} nll")
    expected_mean = round(total / (WINDOW_COUNT * (WINDOW_TOKENS - 1)), 9)
    if value["mean_nll"] != expected_mean or value["perplexity"] != round(math.exp(expected_mean), 9):
        raise ValueError(f"{label} aggregate mismatch")


def bootstrap(deltas: Sequence[float]) -> dict[str, Any]:
    values = [finite(value, "delta") for value in deltas]
    if not values:
        raise ValueError("bootstrap requires data")
    samples = []
    for resample in range(BOOTSTRAP_RESAMPLES):
        total = 0.0
        for position in range(len(values)):
            counter = f"{BOOTSTRAP_SEED}:{resample}:{position}".encode()
            total += values[int.from_bytes(hashlib.sha256(counter).digest()[:8], "big") % len(values)]
        samples.append(total / len(values))
    samples.sort()

    def rank(q: float) -> float:
        return samples[max(1, min(BOOTSTRAP_RESAMPLES, math.ceil(q * BOOTSTRAP_RESAMPLES))) - 1]

    return {
        "mean_delta": sum(values) / len(values),
        "lower": rank(0.025),
        "upper": rank(0.975),
        "resamples": BOOTSTRAP_RESAMPLES,
        "seed": BOOTSTRAP_SEED,
        "confidence": BOOTSTRAP_CONFIDENCE,
        "prng": "sha256-counter-v1",
        "statistic": "mean paired per-document NLL delta selected_minus_baseline",
        "percentile": "nearest-rank-1-indexed",
        "nonfinite": "reject",
    }


def validate_pre_effect_bundle(raw_root: Path, source_root: Path, corpus_root: Path, model_root: Path, launch_manifest: Path, repo_root: Path) -> dict[str, Any]:
    from experiments.continual_learning import gemma3_fineweb_edu_replication_h100_v1_preflight as preflight
    launch = preflight.validate_launch_manifest(launch_manifest, repo_root)
    raw_root = external_runtime_path(raw_root, repo_root, "raw root")
    source_root = external_runtime_path(source_root, repo_root, "source root")
    corpus_root = external_runtime_path(corpus_root, repo_root, "corpus root")
    model_root = external_runtime_path(model_root, repo_root, "model root")
    launch_model_path = Path(launch["model_bundle_path"]).expanduser()
    if launch_model_path.is_symlink():
        raise ValueError("launch-manifest model bundle must not be a symlink")
    if model_root != launch_model_path.resolve():
        raise ValueError("pre-effect model path is not the exact launch-manifest model bundle")
    validate_tree_manifest(model_root, launch["model_manifest_sha256"])
    source_manifest, source_rows = source_bundle(raw_root, source_root)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_root, local_files_only=True, use_fast=True)
    _fit, _assessment, corpus_sha = corpus(corpus_root, source_rows, source_manifest["manifest_sha256"], tokenizer)
    if corpus_sha != launch["data_manifest_sha256"] or source_manifest["manifest_sha256"] != launch["source_manifest_sha256"]:
        raise ValueError("pre-effect data binding mismatch")
    return {"valid": True, "state_slice": STATE_SLICE, "pre_effect": True, "corpus_manifest_sha256": corpus_sha, "source_manifest_sha256": source_manifest["manifest_sha256"]}


def validate(result_root: Path, raw_root: Path, source_root: Path, corpus_root: Path, model_root: Path, launch_manifest: Path, repo_root: Path) -> dict[str, Any]:
    result_root = external_runtime_path(result_root, repo_root, "result root")
    raw_root = external_runtime_path(raw_root, repo_root, "raw root")
    source_root = external_runtime_path(source_root, repo_root, "source root")
    corpus_root = external_runtime_path(corpus_root, repo_root, "corpus root")
    model_root = external_runtime_path(model_root, repo_root, "model root")
    actual = set()
    for path in result_root.rglob("*"):
        relative = path.relative_to(result_root)
        if path.is_symlink():
            raise ValueError(f"result root contains symlink: {relative.as_posix()}")
        if not path.is_file():
            raise ValueError(f"result root contains unexpected directory: {relative.as_posix()}")
        actual.add(relative.as_posix())
    if actual != {"provider-receipt.json", "result.json", "result-receipt.json"}:
        raise ValueError("result exact file set mismatch")
    result = obj(result_root / "result.json", "result")
    receipt = obj(result_root / "result-receipt.json", "result receipt")
    if set(result) != RESULT_KEYS or result["schema"] != RESULT_SCHEMA or result["state_slice"] != STATE_SLICE:
        raise ValueError("result schema or identity mismatch")
    if result["results_sha256"] != digest(result, "results_sha256"):
        raise ValueError("result self digest mismatch")
    validate_launch_binding(launch_manifest, repo_root, result)
    launch = obj(launch_manifest, "launch manifest")
    provider_receipt = validate_provider_receipt(
        result_root / "provider-receipt.json",
        launch,
        sha256_file(launch_manifest),
    )
    launch_model_path = Path(launch["model_bundle_path"]).expanduser()
    if launch_model_path.is_symlink():
        raise ValueError("launch-manifest model bundle must not be a symlink")
    if model_root.expanduser().resolve() != launch_model_path.resolve():
        raise ValueError("model path is not the exact launch-manifest model bundle")
    if set(receipt) != {"schema", "state_slice", "result_sha256", "result_file_sha256", "receipt_sha256"} or receipt["schema"] != "gemma3-fineweb-edu-replication-h100-v1-result-receipt" or receipt["state_slice"] != STATE_SLICE or receipt["result_sha256"] != result["results_sha256"] or receipt["result_file_sha256"] != sha256_file(result_root / "result.json") or receipt["receipt_sha256"] != digest(receipt, "receipt_sha256"):
        raise ValueError("result receipt mismatch")
    for field in ("launch_manifest_sha256", "protocol_sha256", "packet_sha256", "review_receipt_sha256", "implementation_manifest_sha256", "code_bundle_sha256", "runtime_lock_sha256", "data_manifest_sha256", "source_manifest_sha256", "model_manifest_sha256", "corpus_manifest_sha256", "model_parameter_digest_before", "model_parameter_digest_after"):
        hex_digest(result[field], field)
    if not isinstance(result["container_digest"], str) or not result["container_digest"].startswith("sha256:"):
        raise ValueError("result container digest invalid")
    hex_digest(result["container_digest"][7:], "result container digest")
    if result["training"] is not False or result["weights_frozen"] is not True or result["network_access"] is not False or result["evidence_ledger_mutation"] is not False or result["effects_run"] is not True or result["assessment_authorized_by_review"] is not True:
        raise ValueError("result safety flags invalid")
    if result["model_parameter_digest_before"] != result["model_parameter_digest_after"]:
        raise ValueError("model parameters were not frozen")
    if finite(result["hard_usd_ceiling"], "hard USD ceiling") <= 0 or finite(result["estimated_max_total_usd"], "estimated total USD") <= 0:
        raise ValueError("result budget is not positive")
    runtime = result["runtime"]
    # State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v1.
    # The provider image copies the reviewed lock to its repository root and
    # the launch contract requires the relative path runtime-lock.json.
    runtime_lock = obj(repo_root / "runtime-lock.json", "runtime lock")
    runtime_keys = {"python", "accelerate", "pytorch", "transformers", "safetensors", "tokenizers", "pyarrow", "cuda_runtime", "cuda_driver_version", "gpu_name", "gpu_count", "dtype", "network"}
    lock_fields = ("python", "accelerate", "pytorch", "transformers", "safetensors", "tokenizers", "pyarrow", "cuda_runtime")
    runtime_string_fields = (*lock_fields, "cuda_driver_version", "gpu_name", "dtype", "network")
    if (
        not isinstance(runtime, dict)
        or set(runtime) != runtime_keys
        or any(not isinstance(runtime[key], str) for key in runtime_string_fields)
        or "H100" not in runtime["gpu_name"].upper()
        or runtime["gpu_count"] != 1
        or runtime["dtype"] != runtime_lock["dtype"]
        or re.fullmatch(r"[0-9][0-9.]*", runtime["cuda_driver_version"]) is None
        or runtime["cuda_driver_version"] != launch["cuda_driver_version"]
        or runtime["network"] != "offline-process-block-v1"
        or any(runtime[key] != runtime_lock[key] for key in lock_fields)
    ):
        raise ValueError("runtime identity is not the locked H100 runtime")
    source_manifest, source_rows = source_bundle(raw_root, source_root)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_root, local_files_only=True, use_fast=True)
    fit, assessment, corpus_sha = corpus(corpus_root, source_rows, source_manifest["manifest_sha256"], tokenizer)
    if result["corpus_manifest_sha256"] != corpus_sha or result["data_manifest_sha256"] != corpus_sha:
        raise ValueError("result corpus binding mismatch")
    if result["source_manifest_sha256"] != source_manifest["manifest_sha256"]:
        raise ValueError("result source binding mismatch")
    validate_tree_manifest(model_root, result["model_manifest_sha256"])
    if result["candidate_pairs"] != [list(pair) for pair in CANDIDATE_PAIRS] or result["fit_alpha"] != FIT_ALPHA or result["fit_beta"] != FIT_BETA or result["evaluation_alpha"] != EVALUATION_ALPHA or result["evaluation_beta"] != EVALUATION_BETA or result["temperature_control"] != TEMPERATURE_CONTROL or result["normalization"] != "source_l2_norm_to_destination_l2_norm":
        raise ValueError("locked constants mismatch")
    selected = config(result["selected_fit_config"], FIT_ALPHA, FIT_BETA, "selected fit")
    locked = config(result["locked_evaluation_config"], EVALUATION_ALPHA, EVALUATION_BETA, "locked evaluation")
    if (selected["source_layer"], selected["destination_layer"]) != (locked["source_layer"], locked["destination_layer"]):
        raise ValueError("locked pair differs from selected pair")
    if result["paper_expected_pair"] != {"source_layer": 11, "destination_layer": 4} or result["paper_expected_pair_recovered"] != ((selected["source_layer"], selected["destination_layer"]) == (11, 4)):
        raise ValueError("paper target treatment mismatch")
    metric(result["fit_baseline"], fit, 1.0, None, "fit baseline")
    candidates = result["fit_candidates"]
    if not isinstance(candidates, list) or len(candidates) != len(CANDIDATE_PAIRS):
        raise ValueError("fit candidate count mismatch")
    for candidate, pair in zip(candidates, CANDIDATE_PAIRS, strict=True):
        if not isinstance(candidate, dict) or set(candidate) != {"config", "metrics"}:
            raise ValueError("fit candidate schema mismatch")
        candidate_config = config(candidate["config"], FIT_ALPHA, FIT_BETA, "fit candidate")
        if (candidate_config["source_layer"], candidate_config["destination_layer"]) != pair:
            raise ValueError("fit candidate order mismatch")
        metric(candidate["metrics"], fit, 1.0, candidate["config"], "fit candidate metric")
    selected_mean, selected_index, _selected_candidate = min(
        (item["metrics"]["mean_nll"], index, item)
        for index, item in enumerate(candidates)
    )
    selected_pair = (selected["source_layer"], selected["destination_layer"])
    expected_pair = CANDIDATE_PAIRS[selected_index]
    if selected_pair != expected_pair or result["selected_fit_config"] != candidates[selected_index]["config"]:
        raise ValueError("fit selection is not rederived")
    metric(result["assessment_baseline"], assessment, 1.0, None, "assessment baseline")
    metric(result["assessment_selected"], assessment, 1.0, result["locked_evaluation_config"], "assessment selected")
    metric(result["assessment_temperature_baseline"], assessment, TEMPERATURE_CONTROL, None, "temperature baseline")
    metric(result["assessment_temperature_selected"], assessment, TEMPERATURE_CONTROL, result["locked_evaluation_config"], "temperature selected")
    metric(result["assessment_repeat"], assessment, 1.0, result["locked_evaluation_config"], "assessment repeat")
    controls = result["controls"]
    if not isinstance(controls, dict) or set(controls) != set(CONTROL_NAMES) | {"names"} or controls["names"] != list(CONTROL_NAMES):
        raise ValueError("controls schema mismatch")
    if controls["native_baseline"] != result["assessment_baseline"] or controls["all_candidate_evaluations"] != candidates or controls["temperature_1.20_baseline"] != result["assessment_temperature_baseline"] or controls["temperature_1.20_intervention"] != result["assessment_temperature_selected"] or controls["deterministic_repeat"] != result["assessment_repeat"]:
        raise ValueError("controls are not bound to result metrics")
    if controls["frozen_model_manifest"] != {"manifest_sha256": result["model_manifest_sha256"]}:
        raise ValueError("frozen model manifest control mismatch")
    if result["assessment_repeat"] != result["assessment_selected"]:
        raise ValueError("deterministic repeat mismatch")
    zero = controls["zero_alpha_identity"]
    expected_zero_keys = {f"{source}->{destination}" for source, destination in CANDIDATE_PAIRS}
    if not isinstance(zero, dict) or set(zero) != expected_zero_keys:
        raise ValueError("zero-alpha control schema mismatch")
    for source_layer, destination_layer in CANDIDATE_PAIRS:
        pair = f"{source_layer}->{destination_layer}"
        entry = zero[pair]
        if not isinstance(entry, dict) or set(entry) != {"metrics", "max_abs_nll_delta"}:
            raise ValueError("zero-alpha pair control schema mismatch")
        zero_config = config(entry["metrics"]["evaluation_config"], 0.0, 1.0, "zero alpha")
        if (zero_config["source_layer"], zero_config["destination_layer"]) != (source_layer, destination_layer):
            raise ValueError("zero-alpha pair binding mismatch")
        metric(entry["metrics"], assessment, 1.0, zero_config, "zero-alpha metrics")
        if finite(entry["max_abs_nll_delta"], "zero-alpha delta") > PARITY_TOLERANCE:
            raise ValueError("zero-alpha identity tolerance failed")
    frozen = controls["frozen_model_parameters"]
    if frozen != {"before": result["model_parameter_digest_before"], "after": result["model_parameter_digest_after"]}:
        raise ValueError("frozen parameter control mismatch")
    per_document = result["assessment_per_document"]
    if not isinstance(per_document, list) or len(per_document) != WINDOW_COUNT:
        raise ValueError("per-document count mismatch")
    baseline = {row["document_id"]: row for row in result["assessment_baseline"]["rows"]}
    selected_rows = {row["document_id"]: row for row in result["assessment_selected"]["rows"]}
    deltas = []
    seen = set()
    for row in per_document:
        required = {"dataset", "document_id", "relative_path", "window_ordinal", "source_sha256", "source_row_sha256", "source_row_index", "source_row_id", "text_sha256", "token_count", "target_count", "baseline_nll", "selected_nll", "delta_selected_minus_baseline"}
        if not isinstance(row, dict) or set(row) != required or row["document_id"] in seen or row["document_id"] not in assessment:
            raise ValueError("per-document row schema/binding mismatch")
        seen.add(row["document_id"])
        source = assessment[row["document_id"]]
        if row["text_sha256"] != source["text_sha256"] or row["source_sha256"] != source["source_sha256"] or row["source_row_sha256"] != source["source_row_sha256"] or row["source_row_index"] != source["source_row_index"] or row["source_row_id"] != source["source_row_id"] or row["baseline_nll"] != baseline[row["document_id"]]["nll"] or row["selected_nll"] != selected_rows[row["document_id"]]["nll"]:
            raise ValueError("per-document custody or metric mismatch")
        expected_delta = row["selected_nll"] / 1023 - row["baseline_nll"] / 1023
        if not math.isclose(finite(row["delta_selected_minus_baseline"], "per-document delta"), expected_delta, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("per-document delta mismatch")
        deltas.append(row["delta_selected_minus_baseline"])
    expected_bootstrap = bootstrap(deltas)
    if result["bootstrap"] != expected_bootstrap or result["decision"] != ("ReplicationCandidate" if expected_bootstrap["mean_delta"] < 0 and expected_bootstrap["upper"] < 0 else "NoCandidate"):
        raise ValueError("bootstrap or decision mismatch")
    reach = result["qualification"]
    if not isinstance(reach, dict) or set(reach) != {"nonzero_intervention_reach", "reach_evidence", "zero_alpha_identity_passed", "parity_tolerance"} or reach["nonzero_intervention_reach"] is not True or reach["zero_alpha_identity_passed"] is not True or reach["parity_tolerance"] != PARITY_TOLERANCE:
        raise ValueError("qualification schema mismatch")
    evidence = reach["reach_evidence"]
    if not isinstance(evidence, list) or len(evidence) != len(CANDIDATE_PAIRS) or {(item.get("source_layer"), item.get("destination_layer")) for item in evidence} != set(CANDIDATE_PAIRS) or not all(isinstance(item, dict) and set(item) == {"source_layer", "destination_layer", "max_abs_fit_nll_delta", "reached"} and item.get("reached") is True and finite(item.get("max_abs_fit_nll_delta"), "reach delta") > 0 for item in evidence):
        raise ValueError("intervention reach evidence mismatch")
    return {
        "valid": True,
        "state_slice": STATE_SLICE,
        "decision": result["decision"],
        "results_sha256": result["results_sha256"],
        "provider_receipt_sha256": provider_receipt["receipt_sha256"],
        "provider_charged_usd": provider_receipt["charged_usd"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pre-effect", action="store_true")
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--launch-manifest", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.pre_effect:
            output = validate_pre_effect_bundle(args.raw_root, args.source_root, args.corpus_root, args.model_root, args.launch_manifest, args.repo_root)
        else:
            if args.result_root is None:
                raise ValueError("--result-root is required after effects")
            output = validate(args.result_root, args.raw_root, args.source_root, args.corpus_root, args.model_root, args.launch_manifest, args.repo_root)
        print(json.dumps(output, indent=2, sort_keys=True))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
