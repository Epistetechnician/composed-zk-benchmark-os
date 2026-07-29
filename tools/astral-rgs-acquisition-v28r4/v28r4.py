from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "protocol.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
SOURCE_LOCK_NAMES = (
    "rgs_corpus",
    "rgs_model_inventory",
    "rgs_streaming_worker",
    "rgs_coordinator",
    "astral_protocol",
    "astral_validator",
    "astral_cli",
)


def _load_v28r3() -> Any:
    path = HERE.parent / "astral-rgs-acquisition-v28r3" / "v28r3.py"
    spec = importlib.util.spec_from_file_location("astral_v28r3_for_v28r4", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("V28R3 clean-room fixture implementation is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V28R3 = _load_v28r3()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def stable_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def without_hash(value: dict[str, Any], field: str) -> dict[str, Any]:
    return {key: item for key, item in value.items() if key != field}


def empty_fingerprint() -> dict[str, Any]:
    body = {
        "version": "mesh.astral_v28r3_predecessor_fingerprint.v1",
        "source_manifest_sha256s": [],
        "exact_string_sha256s": [],
        "normalized_surface_skeleton_sha256s": [],
        "structural_seven_gram_sha256s": [],
        "semantic_ast_sha256s": [],
        "template_ids": [],
    }
    return {**body, "fingerprint_sha256": stable_hash(body)}


def expected_order(families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fact_kinds = tuple(PROTOCOL["fact_kinds"])
    return sorted(
        families,
        key=lambda family: (
            int(family["block_index"]),
            fact_kinds.index(family["fact_kind"]),
            int(family["family_in_block"]),
            family["family_id"],
        ),
    )


def external_prompt(family: dict[str, Any], query: dict[str, Any]) -> str:
    return (
        "External dossier for this query:\n"
        + family["source_document"]
        + family["support_document"]
        + "\nAnswer using the dossier, then follow the query output contract.\n"
        + query["prompt"]
    )


def semantic_projection(row: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "query_id",
        "family_id",
        "retrieved_family_id",
        "fact_kind",
        "query_class",
        "prompt_sha256",
        "token_ids",
        "tokenized_input_sha256",
        "predicted_label",
        "expected_label",
        "correct",
        "external_source_sha256",
        "external_support_sha256",
    )
    return {field: row.get(field) for field in fields}


def compare(reference: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    left = reference.get("observations", [])
    right = candidate.get("observations", [])
    semantic_equal = len(left) == len(right) and all(
        semantic_projection(a) == semantic_projection(b) for a, b in zip(left, right)
    )
    maximum_delta = 0.0
    score_shape_valid = len(left) == len(right)
    for a, b in zip(left, right):
        a_scores = a.get("label_scores")
        b_scores = b.get("label_scores")
        if not isinstance(a_scores, list) or not isinstance(b_scores, list) or len(a_scores) != 4 or len(b_scores) != 4:
            score_shape_valid = False
            continue
        maximum_delta = max(
            maximum_delta,
            *(abs(float(x) - float(y)) for x, y in zip(a_scores, b_scores)),
        )
    passes = (
        semantic_equal
        and score_shape_valid
        and maximum_delta <= float(PROTOCOL["score_tolerance"])
    )
    return {
        "observation_count": len(left),
        "semantic_equal": semantic_equal,
        "maximum_absolute_label_score_delta": maximum_delta,
        "score_tolerance": float(PROTOCOL["score_tolerance"]),
        "passes": passes,
    }


def validate_manifest(root: Path, errors: list[str]) -> dict[str, Any]:
    path = root / "artifact-manifest.json"
    if not path.is_file():
        errors.append("artifact.manifest.missing")
        return {}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    files = manifest.get("files")
    if not isinstance(files, list) or manifest.get("manifest_sha256") != stable_hash(files):
        errors.append("artifact.manifest.hash")
        return manifest
    seen: set[str] = set()
    for entry in files:
        relative = entry.get("path") if isinstance(entry, dict) else None
        if not isinstance(relative, str) or relative in seen or relative.startswith("/") or ".." in Path(relative).parts:
            errors.append("artifact.manifest.path")
            continue
        seen.add(relative)
        item = root / relative
        if item.is_symlink() or not item.is_file():
            errors.append(f"artifact.file.missing:{relative}")
            continue
        if sha256_file(item) != entry.get("sha256") or item.stat().st_size != entry.get("size_bytes"):
            errors.append(f"artifact.file.mismatch:{relative}")
    return manifest


def validate_source_locks(root: Path, packet: dict[str, Any], errors: list[str]) -> None:
    locks = packet.get("source_locks")
    if not isinstance(locks, dict) or set(locks) != set(SOURCE_LOCK_NAMES):
        errors.append("source_locks.census")
        return
    for name in SOURCE_LOCK_NAMES:
        path = root / "source-locks" / f"{name}.source"
        if not path.is_file() or sha256_file(path) != locks.get(name):
            errors.append(f"source_locks.hash:{name}")
    if locks.get("astral_protocol") != sha256_file(PROTOCOL_PATH):
        errors.append("source_locks.active_protocol")
    if locks.get("astral_validator") != sha256_file(Path(__file__)):
        errors.append("source_locks.active_validator")


def validate_result(
    result: Any,
    *,
    name: str,
    families: list[dict[str, Any]],
    errors: list[str],
) -> None:
    spec = PROTOCOL["runs"][name]
    prefix = f"run.{name}"
    if not isinstance(result, dict):
        errors.append(f"{prefix}.missing")
        return
    if result.get("version") != PROTOCOL["result_version"]:
        errors.append(f"{prefix}.version")
    if result.get("state_slice") != "astral-rgs-v28r4-streaming-control-preflight-implementation":
        errors.append(f"{prefix}.state_slice")
    expected_scalars = {
        "arm_id": "context_only",
        "mode": spec["mode"],
        "batch_size": spec["batch_size"],
        "family_count": PROTOCOL["family_count"],
        "query_count": PROTOCOL["query_count"],
        "checkpoint_sha256": PROTOCOL["checkpoint_sha256"],
        "tokenizer_sha256": PROTOCOL["tokenizer_sha256"],
        "update_tokens": 0,
        "persistent_state_bytes": 0,
        "assessment_opened": False,
    }
    for field, expected in expected_scalars.items():
        if result.get(field) != expected:
            errors.append(f"{prefix}.{field}")
    if result.get("result_sha256") != stable_hash(without_hash(result, "result_sha256")):
        errors.append(f"{prefix}.result_hash")
    observations = result.get("observations")
    if not isinstance(observations, list) or len(observations) != PROTOCOL["query_count"]:
        errors.append(f"{prefix}.observations.census")
        return
    if result.get("observations_sha256") != stable_hash(observations):
        errors.append(f"{prefix}.observations.hash")
    cursor = 0
    labels = tuple(PROTOCOL["labels"])
    for family in families:
        for query in family["queries"]:
            row = observations[cursor]
            cursor += 1
            expected = {
                "query_id": query["query_id"],
                "family_id": family["family_id"],
                "retrieved_family_id": family["family_id"],
                "fact_kind": family["fact_kind"],
                "query_class": query["evaluation_kind"],
                "prompt_sha256": stable_hash(external_prompt(family, query)),
                "expected_label": query["expected_label"],
                "external_source_sha256": family["source_sha256"],
                "external_support_sha256": family["support_sha256"],
            }
            if any(row.get(field) != value for field, value in expected.items()):
                errors.append(f"{prefix}.observation.binding:{cursor - 1}")
                continue
            token_ids = row.get("token_ids")
            scores = row.get("label_scores")
            if not isinstance(token_ids, list) or not token_ids or row.get("tokenized_input_sha256") != stable_hash(token_ids):
                errors.append(f"{prefix}.observation.tokens:{cursor - 1}")
                continue
            if not isinstance(scores, list) or len(scores) != 4 or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in scores):
                errors.append(f"{prefix}.observation.scores:{cursor - 1}")
                continue
            selected = max(range(4), key=lambda index: (float(scores[index]), -index))
            if row.get("predicted_label") != labels[selected]:
                errors.append(f"{prefix}.observation.prediction:{cursor - 1}")
            if row.get("correct") is not (labels[selected] == query["expected_label"]):
                errors.append(f"{prefix}.observation.correct:{cursor - 1}")


def validate(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    validate_manifest(root, errors)
    required = {
        "packet": root / "preflight-packet.json",
        "corpus": root / "corpus.json",
        "fingerprint": root / "predecessor-fingerprint.json",
        "receipt": root / "preflight-receipt.json",
    }
    if any(not path.is_file() for path in required.values()):
        errors.append("artifact.required_files")
        return {"valid": False, "qualified": False, "errors": errors}
    packet = json.loads(required["packet"].read_text(encoding="utf-8"))
    corpus = json.loads(required["corpus"].read_text(encoding="utf-8"))
    fingerprint = json.loads(required["fingerprint"].read_text(encoding="utf-8"))
    receipt = json.loads(required["receipt"].read_text(encoding="utf-8"))
    if packet.get("version") != PROTOCOL["packet_version"]:
        errors.append("packet.version")
    if packet.get("packet_sha256") != stable_hash(without_hash(packet, "packet_sha256")):
        errors.append("packet.hash")
    if packet.get("protocol_sha256") != sha256_file(PROTOCOL_PATH):
        errors.append("packet.protocol_hash")
    if packet.get("source_locks") != receipt.get("source_locks"):
        errors.append("packet.source_locks_receipt")
    for repository in ("rgs", "astral"):
        binding = packet.get("source_bindings", {}).get(repository, {})
        if binding.get("dirty") is not False or not binding.get("commit") or not binding.get("tree"):
            errors.append(f"source_binding.{repository}")
    validate_source_locks(root, packet, errors)

    if fingerprint != empty_fingerprint():
        errors.append("fixture.fingerprint")
    seed = bytes.fromhex(PROTOCOL["fixture_seed_hex"])
    corpus_errors: list[str] = []
    families, _ = V28R3.validate_corpus(
        corpus,
        seed=seed,
        fingerprint=fingerprint,
        errors=corpus_errors,
        families_per_kind=PROTOCOL["families_per_fact_kind"],
    )
    errors.extend(f"fixture.{error}" for error in corpus_errors)
    ordered = expected_order(families) if families else []
    fixture = packet.get("fixture", {})
    if (
        fixture.get("seed_hex") != PROTOCOL["fixture_seed_hex"]
        or fixture.get("family_count") != PROTOCOL["family_count"]
        or fixture.get("query_count") != PROTOCOL["query_count"]
        or fixture.get("candidate_data") is not False
        or fixture.get("corpus_manifest_sha256") != corpus.get("manifest_sha256")
    ):
        errors.append("fixture.packet_binding")

    results: dict[str, dict[str, Any]] = {}
    for name in PROTOCOL["runs"]:
        result_path = root / "runs" / name / "result.json"
        process_path = root / "runs" / name / "process.json"
        result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else None
        process = json.loads(process_path.read_text(encoding="utf-8")) if process_path.is_file() else None
        if not isinstance(process, dict) or process.get("returncode") != 0 or process.get("result_present") is not True:
            errors.append(f"run.{name}.process")
        if isinstance(result, dict):
            results[name] = result
            if packet.get("run_file_sha256s", {}).get(name) != sha256_file(result_path):
                errors.append(f"run.{name}.file_hash")
        validate_result(result, name=name, families=ordered, errors=errors)

    recomputed_8 = compare(results.get("reference_batch8", {}), results.get("stream_batch8", {}))
    recomputed_64 = compare(results.get("stream_batch8", {}), results.get("stream_batch64", {}))
    if packet.get("reference_vs_stream_batch8") != recomputed_8:
        errors.append("parity.batch8.packet")
    if packet.get("stream_batch8_vs_batch64") != recomputed_64:
        errors.append("parity.batch64.packet")
    streaming = [results.get("stream_batch8", {}), results.get("stream_batch64", {})]
    recomputed_gates = {
        "all_processes_completed": all(
            packet.get("processes", {}).get(name, {}).get("returncode") == 0
            for name in PROTOCOL["runs"]
        ),
        "streaming_materialization_bound": all(
            result.get("max_materialized_queries", PROTOCOL["query_count"] + 1)
            <= PROTOCOL["max_materialized_query_rows"]
            and result.get("max_materialized_token_rows", PROTOCOL["query_count"] + 1)
            <= PROTOCOL["max_materialized_token_rows"]
            for result in streaming
        ),
        "batch8_reference_parity": recomputed_8["passes"],
        "batch64_semantic_parity": recomputed_64["passes"],
        "rss_bound": all(
            result.get("peak_rss_bytes", PROTOCOL["max_peak_rss_bytes"] + 1)
            <= PROTOCOL["max_peak_rss_bytes"]
            for result in results.values()
        )
        and len(results) == len(PROTOCOL["runs"]),
        "frozen_identities": all(
            result.get("checkpoint_sha256") == PROTOCOL["checkpoint_sha256"]
            and result.get("tokenizer_sha256") == PROTOCOL["tokenizer_sha256"]
            for result in results.values()
        )
        and len(results) == len(PROTOCOL["runs"]),
    }
    qualified = all(recomputed_gates.values())
    if packet.get("gates") != recomputed_gates or packet.get("qualified") is not qualified:
        errors.append("packet.gates")
    if packet.get("status") != (
        "StreamingControlPreflightPassed" if qualified else "StreamingControlPreflightFailed"
    ):
        errors.append("packet.status")
    boundaries = {
        "persistent_cells_started": 0,
        "update_tokens": 0,
        "adapters_created": 0,
        "assessment_opened": False,
        "scientific_campaign_run": False,
        "claim_ceiling": PROTOCOL["claim_ceiling"],
    }
    for field, expected in boundaries.items():
        if packet.get(field) != expected:
            errors.append(f"boundary.{field}")
    return {
        "version": "astral.rgs_acquisition_v28r4.validation_report.v1",
        "state_slice": PROTOCOL["state_slice"],
        "valid": not errors,
        "qualified": qualified and not errors,
        "errors": errors,
        "recomputed_gates": recomputed_gates,
        "reference_vs_stream_batch8": recomputed_8,
        "stream_batch8_vs_batch64": recomputed_64,
        "claim_ceiling": PROTOCOL["claim_ceiling"],
        "scientific_evidence": False,
    }
