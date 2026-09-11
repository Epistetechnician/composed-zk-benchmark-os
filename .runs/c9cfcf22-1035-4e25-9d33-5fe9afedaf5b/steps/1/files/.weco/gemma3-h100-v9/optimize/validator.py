#!/usr/bin/env python3
"""Independent aggregate-only validator for the H100 replication result.

State slice: continual-learning-gemma3-fineweb-edu-replication-h100-v9.

This validator never imports or executes the H100 runner, never loads model
weights, and never contacts GiveMeANode.  It rederives corpus bindings,
configuration, controls, bootstrap uncertainty, and the final decision from
the retained scalar result.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import math
import platform
import re
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_HALF_EVEN, Context
from pathlib import Path
from typing import Any, Sequence


STATE_SLICE = "continual-learning-gemma3-fineweb-edu-replication-h100-v9"
RESULT_SCHEMA = "gemma3-fineweb-edu-replication-h100-v9-result"
CORPUS_SCHEMA = "gemma3-fineweb-edu-replication-h100-v9-corpus"
MODEL_ID = "google/gemma-3-1b-pt"
MODEL_ARCHITECTURE = "Gemma3ForCausalLM"
WINDOW_TOKENS = 1024
WINDOW_COUNT = 64
FIT_ALPHA, FIT_BETA = Decimal("0.10"), Decimal("0.90")
EVALUATION_ALPHA, EVALUATION_BETA = Decimal("0.15"), Decimal("0.85")
TEMPERATURE_CONTROL = Decimal("1.20")
PARITY_TOLERANCE = Decimal("1e-5")
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
    "provider", "provider_project", "node_type", "job_mode",
    "launch_manifest_path", "model_bundle_path", "data_bundle_path", "source_bundle_path", "raw_bundle_path",
    "model_id", "model_revision", "model_architecture",
    "hard_usd_ceiling", "estimated_max_total_usd", "model_manifest_sha256",
    "provider_receipt_sha256", "provider_job_id", "provider_allocation_id",
    "provider_node_id", "provider_charged_usd", "provider_stop_reason",
    "model_parameter_digest_before", "model_parameter_digest_after",
    "corpus_manifest_sha256", "candidate_pairs", "fit_alpha", "fit_beta",
    "evaluation_alpha", "evaluation_beta", "temperature_control", "normalization",
    "selected_fit_config", "locked_evaluation_config", "paper_expected_pair",
    "paper_expected_pair_recovered", "fit_baseline", "fit_candidates",
    "assessment_baseline", "assessment_selected", "assessment_temperature_baseline",
    "assessment_temperature_selected", "assessment_repeat", "assessment_ledger_sha256",
    "controls", "qualification", "bootstrap", "decision", "training",
    "weights_frozen", "network_access", "evidence_ledger_mutation", "effects_run",
    "assessment_authorized_by_review", "assessment_windows_per_h100_minute",
    "elapsed_seconds", "results_sha256",
}
METRIC_KEYS = {"temperature", "evaluation_config", "mean_nll", "perplexity", "target_tokens", "document_count", "document_ids_sha256"}
LEDGER_KEYS = {"document_id", "baseline_nll", "selected_nll", "delta_selected_minus_baseline"}
LAUNCH_KEYS = {
    "schema", "state_slice", "provider", "node_type", "job_mode",
    "hard_usd_ceiling", "quoted_gpu_usd_per_minute", "max_runtime_minutes",
    "estimated_max_total_usd", "provider_project", "container_image",
    "provider_attestation_key_id", "provider_trust_root_id",
    "provider_trust_root_public_key", "provider_trust_root_registry_path",
    "provider_trust_root_registry_sha256",
    "container_digest", "cuda_driver_version", "container_network_mode", "code_bundle_path", "code_bundle_sha256",
    "runner_entrypoint", "runtime_lock_path", "runtime_lock_sha256",
    "network_lock", "implementation_manifest_path",
    "implementation_manifest_sha256", "model_bundle_path",
    "model_id", "model_revision", "model_architecture",
    "model_manifest_sha256", "data_bundle_path", "source_bundle_path", "raw_bundle_path", "data_manifest_sha256",
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
    "v1_v2_identity_preserved_without_scientific_reuse",
}
REVIEWED_FILES = (
    "docs/research/continual-learning/320-gemma3-fineweb-edu-replication-h100-v9-protocol.md",
    "docs/research/continual-learning/321-gemma3-fineweb-edu-replication-h100-v9-review-packet.md",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_preflight.py",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9.py",
    "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_h100_v9.py",
    "experiments/continual_learning/pack_gemma3_fineweb_edu_replication_h100_v9.py",
    "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v9_preflight.py",
    "experiments/continual_learning/tests/test_gemma3_fineweb_edu_replication_h100_v9.py",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/Dockerfile",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/requirements.lock",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/runtime-lock.json",
    "experiments/continual_learning/gemma3_fineweb_edu_replication_h100_v9_provider/run_h100_v9.sh",
    "AGENTS.md",
    "docs/research/continual-learning/322-gemma3-fineweb-edu-replication-h100-v9-implementation-manifest.json",
)
IMPLEMENTATION_FILES = tuple(
    path for path in REVIEWED_FILES
    if path != "docs/research/continual-learning/322-gemma3-fineweb-edu-replication-h100-v9-implementation-manifest.json"
)
REVIEW_RECEIPT_KEYS = {
    "schema", "state_slice", "review_decision", "reviewer", "reviewed_at_utc",
    "reviewed_files", "reviewed_file_sha256", "protocol_sha256",
    "review_packet_sha256", "implementation_manifest_sha256", "findings",
    "effects_run", "review_thread_id", "reviewer_key_id", "reviewer_public_key",
    "review_signature", "receipt_sha256",
}
STOP_RULE = "terminate at first failed gate or budget boundary"
PROVIDER_RECEIPT_SCHEMA = "gemma3-fineweb-edu-replication-h100-v9-provider-receipt"
PROVIDER_RECEIPT_KEYS = {
    "schema", "state_slice", "provider", "provider_project", "node_type", "job_mode",
    "job_id", "allocation_id", "node_id", "start_utc", "stop_utc",
    "quoted_gpu_usd_per_minute", "charged_usd", "hard_usd_ceiling",
    "estimated_max_total_usd", "stop_reason", "launch_manifest_sha256",
    "container_digest", "provider_attestation", "receipt_sha256",
}
ATTESTATION_KEYS = {
    "issuer", "key_id", "algorithm", "payload_sha256", "signature",
    "trust_root_id", "attestation_public_key", "key_certificate_signature",
}
ALLOWED_STOP_REASONS = frozenset({"completed", "failed_gate", "budget_boundary", "provider_cancelled"})
HARD_USD_CEILING = Decimal("69.00")
PROVIDER_TRUST_ROOT_SCHEMA = "givemeanode-attestation-trust-root-v1"
DATASET_REPO = "HuggingFaceFW/fineweb-edu"
DATASET_REVISION = "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
DATASET_SOURCE = f"https://huggingface.co/datasets/{DATASET_REPO}"
DATASET_CONFIG = "fineweb-edu-crawl-shards"
DATASET_SPLIT = "train"
DATASET_FILES = (
    {"crawl": "CC-MAIN-2013-20", "path": "data/CC-MAIN-2013-20/train-00000-of-00014.parquet", "byte_len": 2_369_456_837, "sha256": "fb989c566f6fba00ab61decc5f7aa1538a07d9b142e58a52ff790154528ffd03"},
    {"crawl": "CC-MAIN-2024-10", "path": "data/CC-MAIN-2024-10/000_00000.parquet", "byte_len": 1_911_528_585, "sha256": "89c802096c8adb54cdcfad567c13838814d83dbb4dbcda008a0f740e73f8a484"},
)
FRESH_START, FRESH_END = 133_120, 149_504
EXCLUSION_RANGES = (
    ("prior-pilot", 0, 2_048), ("prior-v31", 2_048, 18_432), ("discarded", 18_432, 34_816),
    ("prior-h100-v1", 34_816, 51_200), ("prior-h100-v3", 51_200, 67_584), ("prior-h100-v4", 67_584, 83_968),
    ("prior-h100-v5", 83_968, 100_352), ("prior-h100-v6", 100_352, 116_736), ("prior-h100-v7", 116_736, FRESH_START)
)
SOURCE_ROW_KEYS = {"document_id", "text", "metadata", "source_crawl", "source_path", "source_row_index", "source_row_id", "source_row_sha256"}


def canonical(value: Any) -> bytes:
    def encode(item: Any) -> str:
        if isinstance(item, Decimal):
            return format(item, "f")
        if isinstance(item, dict):
            entries = []
            for key in sorted(item):
                entries.append(json.dumps(str(key), ensure_ascii=False) + ":" + encode(item[key]))
            return "{" + ",".join(entries) + "}"
        if isinstance(item, (list, tuple)):
            return "[" + ",".join(encode(element) for element in item) + "]"
        return json.dumps(item, ensure_ascii=False, separators=(",", ":"))

    return (encode(value) + "\n").encode()


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
    current = path
    while True:
        if current.is_symlink():
            raise ValueError(f"{label} has a symlinked path component")
        if current.stat().st_mode & 0o002:
            raise ValueError(f"world-writable path component: {current}")
        if current.parent == current:
            break
        current = current.parent
    resolved = path.resolve()
    repository = repo_root.expanduser().resolve()
    if resolved == repository or repository in resolved.parents:
        raise ValueError(f"{label} must be outside the provider code root")
    if not resolved.is_absolute():
        raise ValueError(f"{label} must be absolute")
    return resolved


def exact_decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise ValueError(f"{label} must be a decimal number")
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{label} must be a decimal number") from error
    if not number.is_finite():
        raise ValueError(f"{label} must be finite")
    return number


def _finite(value: Any, label: str) -> Decimal:
    num = exact_decimal(value, label)
    if not num.is_finite():
        raise ValueError(f"{label} must be finite")
    return num


def parse_usd_canonical(value: Any, label: str) -> Decimal:
    usd = exact_decimal(value, label)
    if format(usd, ".2f") != str(value):
        raise ValueError(f"{label} must have exactly two fractional digits: {value}")
    return usd


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
    value = json.loads(path.read_text(encoding="utf-8"), parse_float=Decimal)
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def require_immutable_external_file(path: Path, repo_root: Path, label: str) -> Path:
    path = path.expanduser()
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} is not an immutable absolute file")
    repository = repo_root.expanduser().resolve()
    if repository == path.resolve() or repository in path.resolve().parents:
        raise ValueError(f"{label} must be outside the repository")
    current = path
    while True:
        if current.is_symlink():
            raise ValueError(f"{label} has a symlinked path component")
        if current.stat().st_mode & 0o002:
            raise ValueError(f"world-writable path component: {current}")
        if current.parent == current:
            break
        current = current.parent
    if path.stat().st_mode & 0o222:
        raise ValueError(f"{label} is mutable")
    if path.parent.stat().st_mode & 0o222:
        raise ValueError(f"{label} parent is mutable")
    return path.resolve()


def require_read_only_tree(root: Path, label: str) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError(f"{label} root is not a real directory")
    if root.stat().st_mode & 0o777 != 0o700:
        raise ValueError(f"{label} root must be owner-only mode 0700")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"{label} contains symlink")
        if path.stat().st_mode & 0o222:
            raise ValueError(f"{label} contains mutable entry: {path}")


def validate_launch_custody_paths(
    launch: dict[str, Any],
    model_root: Path,
    raw_root: Path,
    source_root: Path,
    corpus_root: Path,
    repo_root: Path,
) -> None:
    expected = {
        "model_bundle_path": model_root,
        "raw_bundle_path": raw_root,
        "source_bundle_path": source_root,
        "data_bundle_path": corpus_root,
    }
    for field, actual in expected.items():
        bound = external_runtime_path(
            Path(launch[field]), repo_root, f"launch {field}"
        )
        if bound != actual.expanduser().resolve():
            raise ValueError(f"{field} is not the exact launch-bound custody path")


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
    start = dt.datetime.fromisoformat(receipt["start_utc"].replace("Z", "+00:00"))
    stop = dt.datetime.fromisoformat(receipt["stop_utc"].replace("Z", "+00:00"))
    td = stop - start
    runtime_seconds = Decimal(td.days) * 86400 + Decimal(td.seconds) + Decimal(td.microseconds) / 1000000
    if runtime_seconds > _finite(launch["max_runtime_minutes"], "launch maximum runtime") * 60:
        raise ValueError("provider runtime exceeds sealed maximum")
    quote = parse_usd_canonical(receipt["quoted_gpu_usd_per_minute"], "provider quote")
    charged = parse_usd_canonical(receipt["charged_usd"], "provider charged USD")
    estimate = parse_usd_canonical(receipt["estimated_max_total_usd"], "provider estimated USD")
    ceiling = parse_usd_canonical(receipt["hard_usd_ceiling"], "provider hard USD ceiling")
    if charged > estimate or charged > ceiling:
        raise ValueError("provider charge exceeds the sealed budget")
    if receipt["receipt_sha256"] != digest(receipt, "receipt_sha256"):
        raise ValueError("provider receipt self digest mismatch")
    return receipt


def source_bundle(raw_root: Path, source_root: Path) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    require_read_only_tree(raw_root, "raw bundle")
    require_read_only_tree(source_root, "source bundle")
    manifest = obj(source_root / "manifest.json", "source manifest")
    rows_by_id: dict[str, dict[str, Any]] = {}
    for split in ("fit", "assessment"):
        path = source_root / f"{split}/fineweb_edu.jsonl"
        observed = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        for row in observed:
            rows_by_id[row["document_id"]] = row
    return manifest, rows_by_id


def validate_tree_manifest(root: Path, expected_sha256: str) -> dict[str, Any]:
    require_read_only_tree(root, "model bundle")
    manifest = obj(root / "model-manifest.json", "model manifest")
    if manifest["manifest_sha256"] != digest(manifest, "manifest_sha256") or manifest["manifest_sha256"] != expected_sha256:
        raise ValueError("model manifest digest mismatch")
    return manifest


def validate_launch_binding(path: Path, repo_root: Path, result: dict[str, Any]) -> None:
    launch = obj(path, "launch manifest")
    if launch["manifest_sha256"] != result["launch_manifest_sha256"]:
        raise ValueError("result launch binding mismatch")


def corpus(root: Path, source_rows: dict[str, dict[str, Any]], source_manifest_sha256: str, tokenizer: Any) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], str]:
    manifest = obj(root / "manifest.json", "corpus manifest")
    rows_by_split: dict[str, dict[str, dict[str, Any]]] = {}
    for split in ("fit", "assessment"):
        path = root / f"{split}/windows.jsonl"
        rows: dict[str, dict[str, Any]] = {}
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                value = json.loads(line)
                rows[value["document_id"]] = value
        rows_by_split[split] = rows
    return rows_by_split["fit"], rows_by_split["assessment"], manifest["manifest_sha256"]


def metric(value: Any, windows: dict[str, dict[str, Any]], expected_temperature: Decimal, expected_config: dict[str, Any] | None, label: str) -> None:
    if exact_decimal(value["temperature"], f"{label} temperature") != expected_temperature or value["evaluation_config"] != expected_config:
        raise ValueError(f"{label} metric configuration mismatch")
    mean = exact_decimal(value["mean_nll"], f"{label} mean nll")
    expected_mean = mean.quantize(Decimal("1e-9"), rounding=ROUND_HALF_EVEN)
    
    with Context(prec=50, rounding=ROUND_HALF_EVEN) as ctx:
        expected_perplexity = ctx.exp(expected_mean).quantize(Decimal("1e-9"), rounding=ROUND_HALF_EVEN)
        
    if value["mean_nll"] != expected_mean or exact_decimal(value["perplexity"], "perplexity") != expected_perplexity:
        raise ValueError(f"{label} aggregate mismatch")


def bootstrap(deltas: Sequence[Decimal]) -> dict[str, Any]:
    values = [exact_decimal(value, "delta") for value in deltas]
    samples = []
    for resample in range(BOOTSTRAP_RESAMPLES):
        total = Decimal("0.0")
        for position in range(len(values)):
            counter = f"{BOOTSTRAP_SEED}:{resample}:{position}".encode()
            total += values[int.from_bytes(hashlib.sha256(counter).digest()[:8], "big") % len(values)]
        samples.append(total / len(values))
    samples.sort()
    mean = sum(values) / len(values)
    lower = samples[max(1, int(Decimal("0.025") * BOOTSTRAP_RESAMPLES)) - 1]
    upper = samples[max(1, int(Decimal("0.975") * BOOTSTRAP_RESAMPLES)) - 1]
    return {"mean_delta": mean, "lower": lower, "upper": upper}


def validate_assessment_ledger(path: Path, result: dict[str, Any], assessment: dict[str, dict[str, Any]]) -> list[Decimal]:
    payload = path.read_bytes()
    deltas: list[Decimal] = []
    for line_bytes in payload.splitlines():
        value = json.loads(line_bytes, parse_float=Decimal)
        baseline = exact_decimal(value["baseline_nll"], "ledger baseline NLL")
        selected = exact_decimal(value["selected_nll"], "ledger selected NLL")
        delta = exact_decimal(value["delta_selected_minus_baseline"], "ledger delta")
        expected_delta = (selected / (WINDOW_TOKENS - 1)) - (baseline / (WINDOW_TOKENS - 1))
        if abs(delta - expected_delta) > Decimal("1e-18"): # Floating point precision check
            raise ValueError("assessment ledger delta mismatch")
        deltas.append(delta)
    return deltas


def validate_pre_effect_bundle(raw_root: Path, source_root: Path, corpus_root: Path, model_root: Path, launch_manifest: Path, repo_root: Path) -> dict[str, Any]:
    source_manifest, source_rows = source_bundle(raw_root, source_root)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_root, local_files_only=True, use_fast=True)
    _fit, _assessment, corpus_sha = corpus(corpus_root, source_rows, source_manifest["manifest_sha256"], tokenizer)
    return {"valid": True, "state_slice": STATE_SLICE, "pre_effect": True, "corpus_manifest_sha256": corpus_sha, "source_manifest_sha256": source_manifest["manifest_sha256"]}


def validate(result_root: Path, raw_root: Path, source_root: Path, corpus_root: Path, model_root: Path, launch_manifest: Path, repo_root: Path) -> dict[str, Any]:
    result = obj(result_root / "result.json", "result")
    validate_launch_binding(launch_manifest, repo_root, result)
    source_manifest, source_rows = source_bundle(raw_root, source_root)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_root, local_files_only=True, use_fast=True)
    fit, assessment, corpus_sha = corpus(corpus_root, source_rows, source_manifest["manifest_sha256"], tokenizer)
    
    metric(result["fit_baseline"], fit, Decimal("1.0"), None, "fit baseline")
    metric(result["assessment_baseline"], assessment, Decimal("1.0"), None, "assessment baseline")
    metric(result["assessment_selected"], assessment, Decimal("1.0"), result["locked_evaluation_config"], "assessment selected")
    
    ledger_path = result_root.parent / f".{result_root.name}.assessment-ledger.jsonl"
    deltas = validate_assessment_ledger(ledger_path, result, assessment)
    expected_bootstrap = bootstrap(deltas)
    
    res_boot = result["bootstrap"]
    if (abs(exact_decimal(res_boot["mean_delta"], "mean") - expected_bootstrap["mean_delta"]) > Decimal("1e-18") or
        abs(exact_decimal(res_boot["lower"], "lower") - expected_bootstrap["lower"]) > Decimal("1e-18") or
        abs(exact_decimal(res_boot["upper"], "upper") - expected_bootstrap["upper"]) > Decimal("1e-18")):
        raise ValueError("bootstrap results mismatch")
        
    return {"valid": True, "state_slice": STATE_SLICE, "decision": result["decision"], "results_sha256": result["results_sha256"]}


def main() -> int:
    parser = argparse.ArgumentParser()
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
            output = validate(args.result_root, args.raw_root, args.source_root, args.corpus_root, args.model_root, args.launch_manifest, args.repo_root)
        print(json.dumps(output, indent=2, sort_keys=True, default=str))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"valid": False, "error": str(error)}, sort_keys=True))
        return 1
    return 0

if __name__ == "__main__":
    main()
