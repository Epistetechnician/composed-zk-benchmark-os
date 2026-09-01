#!/usr/bin/env python3
"""Independent strict validator for the V3 Gemma3 replication contract.

State slice: continual-learning-gemma3-fineweb-edu-replication-v3.
The validator is read-only and does not download, train, mutate evidence, or
publish roots. It re-derives raw lineage, tokenizer shape, all controls,
loaded-parameter custody, and the exact counter-hash bootstrap.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Iterator

from experiments.continual_learning import gemma3_fineweb_edu_replication_v3_contract as c

REPO_ROOT = c.REPO_ROOT


def _json(path: Path, label: str) -> dict[str, Any]:
    value = json.loads(c.regular(path, label).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    rows = []
    with c.regular(path, label).open(encoding="utf-8") as handle:
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
    if not isinstance(stored, str) or c.digest({key: item for key, item in value.items() if key != field}) != stored:
        raise ValueError(f"{label} {field} mismatch")


def _expected_dataset() -> dict[str, Any]:
    return {
        "repo": c.DATASET_REPO,
        "source": c.DATASET_SOURCE,
        "revision": c.DATASET_REVISION,
        "config": c.DATASET_CONFIG,
        "split": c.DATASET_SPLIT,
        "selected_file_count": 2,
        "selected_crawls": [item["crawl"] for item in c.DATASET_FILES],
        "parquet_byte_count": c.DATASET_BYTE_COUNT,
    }


def _normalized_from_values(values: dict[str, list[Any]], item: dict[str, Any], source_row_index: int, value_index: int) -> dict[str, Any]:
    text = values["text"][value_index]
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"empty FineWeb-Edu text at row {source_row_index}: {item['path']}")
    upstream_id = values.get("id", [None] * len(values["text"]))[value_index]
    if not isinstance(upstream_id, str) or not upstream_id:
        upstream_id = f"row-{source_row_index:08d}"
    fields = ("id", "url", "date", "dump", "file_path", "language", "language_score", "token_count", "score", "int_score")
    metadata = {
        field: value
        for field in fields
        if field in values and values[field][value_index] is not None
        for value in [values[field][value_index]]
    }
    normalized_metadata = {
        field: value.isoformat() if hasattr(value, "isoformat") else (value if isinstance(value, (str, int, float, bool)) else str(value))
        for field, value in metadata.items()
    }
    return {
        "document_id": f"fineweb-edu:{item['crawl']}:{upstream_id}",
        "text": text,
        "metadata": normalized_metadata,
        "source_crawl": item["crawl"],
        "source_path": item["path"],
        "source_row_index": source_row_index,
    }


def _parquet_rows(path: Path, item: dict[str, Any]) -> Iterator[dict[str, Any]]:
    import pyarrow.parquet as pq

    parquet = pq.ParquetFile(path)
    available = set(parquet.schema.names)
    if "text" not in available:
        raise ValueError(f"FineWeb-Edu shard has no text column: {path}")
    fields = ("id", "url", "date", "dump", "file_path", "language", "language_score", "token_count", "score", "int_score")
    columns = ["text", *[field for field in fields if field in available]]
    global_index = 0
    selected = 0
    for batch in parquet.iter_batches(columns=columns, batch_size=256):
        values = {name: batch.column(name).to_pylist() for name in columns}
        for offset in range(batch.num_rows):
            if c.FRESH_ROW_START <= global_index < c.FRESH_ROW_END:
                yield _normalized_from_values(values, item, global_index, offset)
                selected += 1
            global_index += 1
            if global_index >= c.FRESH_ROW_END:
                break
        if global_index >= c.FRESH_ROW_END:
            break
    if selected != c.FRESH_ROW_COUNT:
        raise ValueError(f"selected {selected} rows from {path}; expected {c.FRESH_ROW_COUNT}")


def _audit_raw(raw_root: Path) -> list[dict[str, Any]]:
    raw_root = c.primary(raw_root, "raw root")
    dataset_root = raw_root / "dataset"
    expected_paths = set()
    artifacts = []
    for item in c.DATASET_FILES:
        path = c.regular(dataset_root / item["path"], "V3 pinned Parquet shard")
        expected_paths.add(path)
        if path.stat().st_size != item["byte_len"] or c.sha256_file(path) != item["sha256"]:
            raise ValueError(f"V3 raw pin mismatch: {path}")
        import pyarrow.parquet as pq

        row_count = pq.ParquetFile(path).metadata.num_rows
        if row_count < c.FRESH_ROW_END:
            raise ValueError(f"V3 raw shard too short: {path}")
        artifacts.append({
            "relative_path": path.relative_to(raw_root).as_posix(),
            "source": f"{c.DATASET_SOURCE}/resolve/{c.DATASET_REVISION}/{item['path']}",
            "crawl": item["crawl"],
            "byte_len": path.stat().st_size,
            "sha256": c.sha256_file(path),
            "lfs_sha256": item["sha256"],
            "row_count": row_count,
        })
    actual_paths = {path for path in dataset_root.rglob("*.parquet") if path.is_file() and not path.is_symlink()}
    if actual_paths != expected_paths:
        raise ValueError("V3 raw Parquet set differs from pinned two-file set")
    return artifacts


def _audit_prior(r1_source_root: Path) -> set[str]:
    root = c.primary(r1_source_root, "prior pilot source root")
    manifest_path = root / "acquisition-manifest.json"
    manifest = _json(manifest_path, "prior pilot source manifest")
    if c.sha256_file(manifest_path) != c.R1_SOURCE_MANIFEST_SHA256 or manifest.get("schema") != "gemma3-fineweb-edu-bounded-acquisition-v1":
        raise ValueError("prior pilot source binding mismatch")
    _check_self_digest(manifest, "manifest_sha256", "prior pilot source manifest")
    if manifest.get("dataset") != _expected_dataset() or manifest.get("selection_policy") != "first-2048-records-from-two-pinned-crawls-document-disjoint-v1":
        raise ValueError("prior pilot source contract mismatch")
    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict):
        raise ValueError("prior pilot dataset entries missing")
    ids: set[str] = set()
    for split, item in (("fit", c.DATASET_FILES[0]), ("assessment", c.DATASET_FILES[1])):
        metadata = datasets.get(f"{split}/fineweb_edu")
        if not isinstance(metadata, dict) or metadata.get("row_start") != 0 or metadata.get("row_count") != 2048:
            raise ValueError(f"prior pilot {split} row contract mismatch")
        if metadata.get("crawl") != item["crawl"] or metadata.get("source_path") != item["path"]:
            raise ValueError(f"prior pilot {split} shard contract mismatch")
        rows = _jsonl(root / metadata["normalized_path"], f"prior pilot {split}")
        if len(rows) != 2048:
            raise ValueError(f"prior pilot {split} count mismatch")
        for ordinal, row in enumerate(rows):
            document_id = row.get("document_id")
            if not isinstance(document_id, str) or not document_id or row.get("source_row_index") != ordinal or row.get("source_crawl") != item["crawl"] or row.get("source_path") != item["path"]:
                raise ValueError(f"prior pilot {split} identity mismatch at {ordinal}")
            if document_id in ids:
                raise ValueError("prior pilot document overlap")
            ids.add(document_id)
    return ids


def _audit_source(source_root: Path, raw_root: Path, r1_source_root: Path) -> dict[str, Any]:
    root = c.primary(source_root, "V3 source root")
    raw_root = c.primary(raw_root, "raw root")
    r1_source_root = c.primary(r1_source_root, "prior pilot source root")
    manifest = _json(root / "acquisition-manifest.json", "V3 source manifest")
    required = (
        ("schema", c.SOURCE_SCHEMA),
        ("state_slice", c.STATE_SLICE),
        ("claim_ceiling", c.CLAIM_CEILING),
        ("source_record_schema", "gemma3-source-v1-compatible-with-fineweb-metadata"),
        ("selection_policy", "rows-2048-through-18431-two-pinned-crawls-v3"),
        ("raw_root", str(raw_root)),
        ("prior_pilot_source_root", str(r1_source_root)),
        ("prior_pilot_manifest_sha256", c.R1_SOURCE_MANIFEST_SHA256),
    )
    if any(manifest.get(key) != value for key, value in required) or manifest.get("dataset") != _expected_dataset():
        raise ValueError("V3 source manifest contract mismatch")
    if manifest.get("fresh_row_range") != {"start": c.FRESH_ROW_START, "end_exclusive": c.FRESH_ROW_END, "count_per_shard": c.FRESH_ROW_COUNT}:
        raise ValueError("V3 fresh row range mismatch")
    for key in ("network_access", "training", "scientific_execution", "evidence_ledger_mutation"):
        if manifest.get(key) is not False:
            raise ValueError(f"V3 source flag mismatch: {key}")
    _check_self_digest(manifest, "manifest_sha256", "V3 source manifest")
    raw_artifacts = _audit_raw(raw_root)
    if manifest.get("raw_artifacts") != raw_artifacts:
        raise ValueError("V3 raw artifact binding mismatch")
    prior_ids = _audit_prior(r1_source_root)
    datasets = manifest.get("datasets")
    if not isinstance(datasets, dict):
        raise ValueError("V3 source datasets missing")
    records_by_split: dict[str, list[dict[str, Any]]] = {}
    all_ids: set[str] = set()
    for split, item in (("fit", c.DATASET_FILES[0]), ("assessment", c.DATASET_FILES[1])):
        key = f"{split}/fineweb_edu"
        metadata = datasets.get(key)
        expected = {"source": c.DATASET_SOURCE, "revision": c.DATASET_REVISION, "config": c.DATASET_CONFIG, "split": c.DATASET_SPLIT, "crawl": item["crawl"], "source_path": item["path"], "row_start": c.FRESH_ROW_START, "row_count": c.FRESH_ROW_COUNT, "normalized_path": f"{split}/fineweb_edu.jsonl"}
        if not isinstance(metadata, dict) or any(metadata.get(k) != v for k, v in expected.items()):
            raise ValueError(f"V3 {key} metadata mismatch")
        path = c.safe_relative(root, metadata["normalized_path"], f"V3 {key} JSONL")
        if c.sha256_file(path) != metadata.get("normalized_sha256"):
            raise ValueError(f"V3 {key} normalized digest mismatch")
        rows = _jsonl(path, f"V3 {key}")
        if len(rows) != c.FRESH_ROW_COUNT:
            raise ValueError(f"V3 {key} count mismatch")
        for ordinal, row in enumerate(rows):
            document_id = row.get("document_id")
            if not isinstance(document_id, str) or not document_id or row.get("source_row_index") != c.FRESH_ROW_START + ordinal or row.get("source_crawl") != item["crawl"] or row.get("source_path") != item["path"] or not document_id.startswith(f"fineweb-edu:{item['crawl']}:"):
                raise ValueError(f"V3 {key} identity mismatch at {ordinal}")
            if document_id in all_ids or document_id in prior_ids:
                raise ValueError(f"V3 document overlap: {document_id}")
            all_ids.add(document_id)
        expected_rows = _parquet_rows(raw_root / "dataset" / item["path"], item)
        for ordinal, (observed, expected_row) in enumerate(zip(rows, expected_rows, strict=True)):
            if observed != expected_row:
                raise ValueError(f"V3 raw lineage mismatch in {key} at {ordinal}")
        records_by_split[split] = rows
    return {"manifest": manifest, "manifest_sha256": manifest["manifest_sha256"], "raw_artifacts": raw_artifacts, "prior_ids": prior_ids, "ids": all_ids, "records_by_split": records_by_split}


def validate_source(source_root: Path, raw_root: Path, r1_source_root: Path) -> dict[str, Any]:
    audit = _audit_source(source_root, raw_root, r1_source_root)
    return {"valid": True, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "source_manifest_sha256": audit["manifest_sha256"], "fit_record_count": len(audit["records_by_split"]["fit"]), "assessment_record_count": len(audit["records_by_split"]["assessment"]), "prior_document_count": len(audit["prior_ids"])}


def _load_tokenizer(model_path: Path) -> Any:
    from mlx_lm.utils import load_tokenizer
    from experiments.continual_learning.mlx_tokenizer_policy import tokenizer_config_from_policy, tokenizer_policy_for_model

    policy = tokenizer_policy_for_model(model_path)
    return load_tokenizer(model_path, tokenizer_config_extra=tokenizer_config_from_policy(policy) or None)


def _audit_corpus(corpus_root: Path, source_root: Path, raw_root: Path, r1_source_root: Path, model_path: Path, source_manifest_sha256: str) -> dict[str, Any]:
    root = c.primary(corpus_root, "V3 corpus root")
    source = _audit_source(source_root, raw_root, r1_source_root)
    if source["manifest_sha256"] != source_manifest_sha256:
        raise ValueError("V3 corpus source binding mismatch")
    manifest = _json(root / "manifest.json", "V3 corpus manifest")
    if manifest.get("schema") != c.CORPUS_SCHEMA or manifest.get("state_slice") != c.STATE_SLICE or manifest.get("claim_ceiling") != c.CLAIM_CEILING or manifest.get("source_manifest_sha256") != source_manifest_sha256 or manifest.get("window_token_count") != c.WINDOW_TOKENS or manifest.get("selection_policy") != c.SELECTION_POLICY:
        raise ValueError("V3 corpus manifest contract mismatch")
    if manifest.get("fit_window_count") != c.FIT_WINDOW_COUNT or manifest.get("assessment_window_count") != c.ASSESSMENT_WINDOW_COUNT:
        raise ValueError("V3 corpus count mismatch")
    for key in ("network_access", "training", "scientific_execution", "evidence_ledger_mutation"):
        expected = False
        if manifest.get(key) is not expected:
            raise ValueError(f"V3 corpus flag mismatch: {key}")
    _check_self_digest(manifest, "manifest_sha256", "V3 corpus manifest")
    source_records = {row["document_id"]: row for rows in source["records_by_split"].values() for row in rows}
    tokenizer = None
    with c.network_block():
        tokenizer = _load_tokenizer(model_path)
    split_ids: dict[str, set[str]] = {}
    split_text_sha: dict[str, dict[str, str]] = {}
    seen_paths: set[str] = set()
    for split, expected_count in (("fit", c.FIT_WINDOW_COUNT), ("assessment", c.ASSESSMENT_WINDOW_COUNT)):
        entries = manifest.get(split)
        if not isinstance(entries, list) or len(entries) != expected_count:
            raise ValueError(f"V3 corpus {split} entry count mismatch")
        ids: set[str] = set()
        text_shas: dict[str, str] = {}
        for ordinal, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ValueError(f"V3 corpus {split} entry is not an object")
            document_id = entry.get("document_id")
            expected_path = f"{split}/fineweb_edu/window-{ordinal:06d}.txt"
            if not isinstance(document_id, str) or document_id in ids or document_id in source["prior_ids"] or document_id not in source["ids"]:
                raise ValueError(f"V3 corpus {split} document identity mismatch")
            if entry.get("path") != expected_path or entry["path"] in seen_paths or entry.get("dataset") != "fineweb_edu" or entry.get("window_ordinal") != 0 or entry.get("token_count") != c.WINDOW_TOKENS:
                raise ValueError(f"V3 corpus {split} path/window contract mismatch")
            source_record = source_records[document_id]
            if entry.get("source_row_index") != source_record["source_row_index"] or entry.get("source_path") != source_record["source_path"]:
                raise ValueError(f"V3 corpus {split} source row binding mismatch")
            expected_source_sha = __import__("hashlib").sha256(source_record["text"].encode("utf-8")).hexdigest()
            if entry.get("source_sha256") != expected_source_sha:
                raise ValueError(f"V3 corpus {split} source text binding mismatch")
            path = c.safe_relative(root, entry["path"], f"V3 corpus {split} window")
            raw_bytes = path.read_bytes()
            text = raw_bytes.decode("utf-8")
            if len(raw_bytes) != entry.get("byte_len") or c.sha256_file(path) != entry.get("text_sha256"):
                raise ValueError(f"V3 corpus {split} text digest mismatch")
            token_ids = list(tokenizer.encode(text, add_special_tokens=False))
            if len(token_ids) != c.WINDOW_TOKENS or list(tokenizer.encode(tokenizer.decode(token_ids), add_special_tokens=False)) != token_ids:
                raise ValueError(f"V3 corpus {split} tokenizer shape mismatch")
            ids.add(document_id)
            text_shas[document_id] = entry["text_sha256"]
            seen_paths.add(entry["path"])
        split_ids[split] = ids
        split_text_sha[split] = text_shas
    if split_ids["fit"] & split_ids["assessment"]:
        raise ValueError("V3 corpus fit/assessment overlap")
    return {"manifest": manifest, "manifest_sha256": manifest["manifest_sha256"], "source": source, "fit_ids": split_ids["fit"], "assessment_ids": split_ids["assessment"], "text_sha": split_text_sha}


def validate_corpus(corpus_root: Path, source_root: Path, raw_root: Path, r1_source_root: Path, model_path: Path, source_manifest_sha256: str) -> dict[str, Any]:
    audit = _audit_corpus(corpus_root, source_root, raw_root, r1_source_root, model_path, source_manifest_sha256)
    return {"valid": True, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "corpus_manifest_sha256": audit["manifest_sha256"], "fit_window_count": len(audit["fit_ids"]), "assessment_window_count": len(audit["assessment_ids"])}


def implementation_manifest() -> dict[str, Any]:
    files = []
    for path in c.IMPLEMENTATION_FILES:
        path = c.regular(path, "V3 reviewed file")
        files.append({"path": path.relative_to(c.REPO_ROOT).as_posix(), "byte_len": path.stat().st_size, "sha256": c.sha256_file(path)})
    body = {"state_slice": c.STATE_SLICE, "files": files}
    return {"manifest": body, "manifest_sha256": c.digest(body)}


def validate_review_receipt(path: Path) -> dict[str, Any]:
    receipt = _json(path, "V3 independent review receipt")
    if receipt.get("schema") != c.REVIEW_SCHEMA or receipt.get("state_slice") != c.STATE_SLICE or receipt.get("claim_ceiling") != c.CLAIM_CEILING or receipt.get("protocol_sha256") != c.sha256_file(c.PROTOCOL_PATH) or receipt.get("protocol_sha256") != c.PROTOCOL_SHA256:
        raise ValueError("V3 review protocol binding mismatch")
    if c.sha256_file(c.REVIEW_PACKET_PATH) != receipt.get("review_packet_sha256") or receipt.get("implementation_manifest_sha256") != implementation_manifest()["manifest_sha256"]:
        raise ValueError("V3 review packet or implementation binding mismatch")
    if receipt.get("review_status") != "ACCEPT" or receipt.get("effects_run") is not False or not isinstance(receipt.get("reviewer"), str) or not receipt["reviewer"] or not isinstance(receipt.get("reviewed_at_utc"), str) or not receipt["reviewed_at_utc"]:
        raise ValueError("V3 review receipt identity/status mismatch")
    findings = receipt.get("findings")
    if not isinstance(findings, dict) or set(findings) != set(c.REVIEW_FINDINGS) or any(findings[key] is not True for key in c.REVIEW_FINDINGS):
        raise ValueError("V3 review findings are incomplete")
    _check_self_digest(receipt, "receipt_digest_sha256", "V3 independent review receipt")
    return receipt


def _finite(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{label} must be finite")
    return float(value)


def _validate_metrics(metrics: Any, ids: set[str], text_sha: dict[str, str], label: str) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        raise ValueError(f"{label} metrics missing")
    _finite(metrics.get("mean_nll"), f"{label} mean_nll")
    _finite(metrics.get("perplexity"), f"{label} perplexity")
    if not isinstance(metrics.get("target_tokens"), int) or isinstance(metrics["target_tokens"], bool) or metrics["target_tokens"] != 1023 * len(ids):
        raise ValueError(f"{label} target token count mismatch")
    rows = metrics.get("rows")
    if not isinstance(rows, list) or len(rows) != len(ids):
        raise ValueError(f"{label} row count mismatch")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{label} row is not an object")
        document_id = row.get("document_id")
        if not isinstance(document_id, str) or document_id not in ids or document_id in seen or row.get("dataset") != "fineweb_edu" or row.get("window_ordinal") != 0 or row.get("token_count") != 1024 or row.get("target_count") != 1023 or row.get("text_sha256") != text_sha[document_id]:
            raise ValueError(f"{label} row identity/shape mismatch")
        _finite(row.get("nll"), f"{label} NLL")
        seen.add(document_id)
    if seen != ids:
        raise ValueError(f"{label} row set mismatch")
    return metrics


def validate_result(result_root: Path, corpus_root: Path, source_root: Path, raw_root: Path, r1_source_root: Path, model_path: Path, review_receipt: Path, corpus_manifest_sha256: str) -> dict[str, Any]:
    root = c.primary(result_root, "V3 result root")
    validate_review_receipt(review_receipt)
    source = _audit_source(source_root, raw_root, r1_source_root)
    corpus = _audit_corpus(corpus_root, source_root, raw_root, r1_source_root, model_path, source["manifest_sha256"])
    if corpus["manifest_sha256"] != corpus_manifest_sha256:
        raise ValueError("V3 result corpus binding mismatch")
    config = _json(root / "config.json", "V3 result config")
    results = _json(root / "results.json", "V3 result body")
    receipt = _json(root / "receipt.json", "V3 result receipt")
    for value, label in ((config, "V3 result config"), (results, "V3 result body"), (receipt, "V3 result receipt")):
        if value.get("schema") != c.RESULT_SCHEMA or value.get("state_slice") != c.STATE_SLICE or value.get("claim_ceiling") != c.CLAIM_CEILING:
            raise ValueError(f"{label} contract mismatch")
    _check_self_digest(config, "config_sha256", "V3 result config")
    _check_self_digest(results, "results_sha256", "V3 result body")
    _check_self_digest(receipt, "receipt_sha256", "V3 result receipt")
    source_sha = source["manifest_sha256"]
    if config.get("protocol_sha256") != c.PROTOCOL_SHA256 or config.get("review_receipt_sha256") != c.sha256_file(review_receipt) or config.get("source_manifest_sha256") != source_sha or config.get("corpus_manifest_sha256") != corpus_manifest_sha256:
        raise ValueError("V3 config digest binding mismatch")
    if results.get("protocol_sha256") != c.PROTOCOL_SHA256 or results.get("source_manifest_sha256") != source_sha or results.get("corpus_manifest_sha256") != corpus_manifest_sha256 or results.get("review_receipt_sha256") != c.sha256_file(review_receipt):
        raise ValueError("V3 result digest binding mismatch")
    if receipt.get("protocol_sha256") != c.PROTOCOL_SHA256 or receipt.get("review_receipt_sha256") != c.sha256_file(review_receipt) or receipt.get("source_manifest_sha256") != source_sha or receipt.get("corpus_manifest_sha256") != corpus_manifest_sha256:
        raise ValueError("V3 receipt digest binding mismatch")
    if c.model_manifest(model_path)["manifest_sha256"] != c.EXPECTED_MODEL_MANIFEST_SHA256 or config.get("model_manifest_sha256") != c.EXPECTED_MODEL_MANIFEST_SHA256 or results.get("model_manifest_sha256") != c.EXPECTED_MODEL_MANIFEST_SHA256:
        raise ValueError("V3 model manifest binding mismatch")
    if config.get("model_path") != str(c.MODEL_PATH) or results.get("model_path") != str(c.MODEL_PATH):
        raise ValueError("V3 exact model path binding mismatch")
    for value, field, expected in ((config, "network_access", False), (config, "training", False), (config, "weights_frozen", True), (config, "evidence_ledger_mutation", False), (config, "assessment_authorized_by_review", True), (results, "network_access", False), (results, "training", False), (results, "weights_frozen", True), (results, "evidence_ledger_mutation", False)):
        if value.get(field) is not expected:
            raise ValueError(f"V3 {field} flag mismatch")
    for value, label in ((config, "V3 result config"), (results, "V3 result body")):
        if value.get("architecture") != "gemma3_text" or value.get("model_type") != "gemma3_text" or value.get("layer_count") != 26:
            raise ValueError(f"{label} model architecture binding mismatch")
    fit_ids = corpus["fit_ids"]
    assessment_ids = corpus["assessment_ids"]
    fit_sha = corpus["text_sha"]["fit"]
    assessment_sha = corpus["text_sha"]["assessment"]
    if config.get("candidate_pairs") != [list(pair) for pair in c.CANDIDATE_PAIRS] or config.get("fit_alpha") != c.FIT_ALPHA or config.get("evaluation_alpha") != c.EVALUATION_ALPHA or config.get("evaluation_beta") != c.EVALUATION_BETA or config.get("temperature_control") != c.TEMPERATURE_CONTROL or config.get("controls") != list(c.CONTROL_NAMES):
        raise ValueError("V3 locked configuration/control list mismatch")
    candidates = results.get("fit_candidates")
    if not isinstance(candidates, list) or len(candidates) != len(c.CANDIDATE_PAIRS):
        raise ValueError("V3 candidate count mismatch")
    candidate_means = []
    for candidate, pair in zip(candidates, c.CANDIDATE_PAIRS, strict=True):
        if not isinstance(candidate, dict) or candidate.get("config", {}).get("source_layer") != pair[0] or candidate.get("config", {}).get("destination_layer") != pair[1] or candidate.get("config", {}).get("alpha") != c.FIT_ALPHA:
            raise ValueError("V3 candidate configuration mismatch")
        metrics = _validate_metrics(candidate.get("metrics"), fit_ids, fit_sha, "V3 fit candidate")
        candidate_means.append((metrics["mean_nll"], pair[0], pair[1]))
    _validate_metrics(results.get("fit_baseline"), fit_ids, fit_sha, "V3 fit baseline")
    expected_pair = min(candidate_means)
    selected_fit = results.get("selected_fit_config")
    locked = results.get("locked_evaluation_config")
    if not isinstance(selected_fit, dict) or (selected_fit.get("source_layer"), selected_fit.get("destination_layer"), selected_fit.get("alpha")) != (expected_pair[1], expected_pair[2], c.FIT_ALPHA):
        raise ValueError("V3 selected fit configuration is not derived from all candidates")
    if not isinstance(locked, dict) or (locked.get("source_layer"), locked.get("destination_layer"), locked.get("alpha")) != (expected_pair[1], expected_pair[2], c.EVALUATION_ALPHA):
        raise ValueError("V3 locked pair does not equal selected pair")
    if config.get("selected_fit_config") != selected_fit or config.get("locked_evaluation_config") != locked or results.get("paper_expected_pair") != {"source_layer": 11, "destination_layer": 4} or config.get("paper_expected_pair") != {"source_layer": 11, "destination_layer": 4}:
        raise ValueError("V3 selected/locked or paper target binding mismatch")
    baseline = _validate_metrics(results.get("assessment_baseline"), assessment_ids, assessment_sha, "V3 assessment baseline")
    selected = _validate_metrics(results.get("assessment_selected"), assessment_ids, assessment_sha, "V3 assessment selected")
    temp_baseline = _validate_metrics(results.get("assessment_temperature_baseline"), assessment_ids, assessment_sha, "V3 temperature baseline")
    temp_selected = _validate_metrics(results.get("assessment_temperature_selected"), assessment_ids, assessment_sha, "V3 temperature intervention")
    repeat = _validate_metrics(results.get("assessment_repeat"), assessment_ids, assessment_sha, "V3 deterministic repeat")
    if repeat != selected:
        raise ValueError("V3 deterministic repeat differs from locked assessment")
    if results.get("controls") != {"native_baseline": baseline, "zero_alpha_identity": results.get("parity"), "all_candidate_evaluations": candidates, "temperature_1.20_baseline": temp_baseline, "temperature_1.20_intervention": temp_selected, "deterministic_repeat": repeat, "frozen_model_manifest": {"before": c.EXPECTED_MODEL_MANIFEST_SHA256, "after": c.EXPECTED_MODEL_MANIFEST_SHA256}, "frozen_model_parameters": {"before": results.get("model_parameter_digest_before"), "after": results.get("model_parameter_digest_after")}}:
        raise ValueError("V3 retained controls mismatch")
    parity = results.get("parity")
    if not isinstance(parity, dict) or parity.get("all_passed") is not True or parity.get("sequence_count") != 128 or not math.isfinite(float(parity.get("max_abs_logit_delta"))):
        raise ValueError("V3 parity control mismatch")
    derived_reach = any(abs(candidate["metrics"]["mean_nll"] - results["fit_baseline"]["mean_nll"]) > 0.0 for candidate in candidates)
    if results.get("qualification", {}).get("nonzero_intervention_reach") is not True or not derived_reach or results.get("deterministic_repeat_passed") is not True:
        raise ValueError("V3 qualification control mismatch")
    per_document = results.get("assessment_per_document")
    selected_rows = {row["document_id"]: row for row in selected["rows"]}
    baseline_rows = {row["document_id"]: row for row in baseline["rows"]}
    if not isinstance(per_document, list) or len(per_document) != len(assessment_ids):
        raise ValueError("V3 per-document count mismatch")
    deltas = []
    seen: set[str] = set()
    for row in per_document:
        document_id = row.get("document_id")
        if not isinstance(document_id, str) or document_id not in assessment_ids or document_id in seen or row.get("dataset") != "fineweb_edu" or row.get("text_sha256") != assessment_sha[document_id] or row.get("target_count") != 1023:
            raise ValueError("V3 per-document identity mismatch")
        if row.get("baseline_nll") != baseline_rows[document_id]["nll"] or row.get("selected_nll") != selected_rows[document_id]["nll"]:
            raise ValueError("V3 per-document metric binding mismatch")
        expected_delta = row["selected_nll"] / row["target_count"] - row["baseline_nll"] / row["target_count"]
        if not math.isclose(float(row.get("delta_selected_minus_baseline")), expected_delta, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError("V3 per-document delta mismatch")
        deltas.append(float(row["delta_selected_minus_baseline"]))
        seen.add(document_id)
    if seen != assessment_ids:
        raise ValueError("V3 per-document set mismatch")
    bootstrap = c.bootstrap_mean_ci(deltas)
    if results.get("bootstrap") != bootstrap or results.get("decision") != c.decide_replication(bootstrap) or receipt.get("bootstrap") != bootstrap or receipt.get("decision") != results.get("decision"):
        raise ValueError("V3 bootstrap or decision mismatch")
    if results.get("assessment_nll_delta_selected_minus_baseline") != selected["mean_nll"] - baseline["mean_nll"]:
        raise ValueError("V3 assessment aggregate mismatch")
    if config.get("model_parameter_digest_before") != config.get("model_parameter_digest_after") or results.get("model_parameter_digest_before") != results.get("model_parameter_digest_after") or config.get("model_parameter_digest_before") != results.get("model_parameter_digest_before"):
        raise ValueError("V3 in-memory parameter custody mismatch")
    # Load the cached model only after all receipt/corpus gates; compare its current parameters independently.
    from experiments.continual_learning import gemma3_paper_recirculation_v1 as engine

    with c.network_block():
        model, _tokenizer, _policy = engine._load_runtime(model_path)
        current_parameter_digest = c.model_parameter_digest(model)
    if current_parameter_digest != results.get("model_parameter_digest_after"):
        raise ValueError("V3 current model parameters differ from recorded frozen digest")
    return {"valid": True, "state_slice": c.STATE_SLICE, "claim_ceiling": c.CLAIM_CEILING, "result_root": str(root), "decision": results["decision"], "results_sha256": results["results_sha256"], "bootstrap": bootstrap, "review_receipt_sha256": c.sha256_file(review_receipt)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--r1-source-root", type=Path, default=c.R1_SOURCE_ROOT)
    parser.add_argument("--corpus-root", type=Path)
    parser.add_argument("--source-manifest-sha256")
    parser.add_argument("--result-root", type=Path)
    parser.add_argument("--model", type=Path, default=c.MODEL_PATH)
    parser.add_argument("--review-receipt", type=Path)
    parser.add_argument("--corpus-manifest-sha256")
    args = parser.parse_args()
    selected = [args.source_root is not None, args.corpus_root is not None, args.result_root is not None]
    if sum(selected) != 1:
        parser.error("choose one of --source-root, --corpus-root, or --result-root")
    if args.source_root is not None:
        value = validate_source(args.source_root, args.raw_root, args.r1_source_root)
    elif args.corpus_root is not None:
        if not args.source_root or not args.model or not args.source_manifest_sha256:
            parser.error("--corpus-root requires --source-root, --model, and --source-manifest-sha256")
        value = validate_corpus(args.corpus_root, args.source_root, args.raw_root, args.r1_source_root, args.model, args.source_manifest_sha256)
    else:
        required = (args.source_root, args.corpus_root, args.model, args.review_receipt, args.corpus_manifest_sha256)
        if any(item is None for item in required):
            parser.error("--result-root requires source/corpus/model/review/corpus manifest bindings")
        value = validate_result(args.result_root, args.corpus_root, args.source_root, args.raw_root, args.r1_source_root, args.model, args.review_receipt, args.corpus_manifest_sha256)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
