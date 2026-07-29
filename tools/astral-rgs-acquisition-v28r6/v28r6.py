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
    "rgs_corpus", "rgs_model_inventory", "rgs_legacy_scorer",
    "rgs_parity_core", "rgs_endurance_worker", "rgs_coordinator",
    "astral_protocol", "astral_validator", "astral_cli",
)


def load_v28r4() -> Any:
    path = HERE.parent / "astral-rgs-acquisition-v28r4" / "v28r4.py"
    spec = importlib.util.spec_from_file_location("astral_v28r4_for_v28r6", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("V28R4 independent fixture validator is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V28R4 = load_v28r4()
stable_hash = V28R4.stable_hash
sha256_file = V28R4.sha256_file
without_hash = V28R4.without_hash


def endpoint_view(result: dict[str, Any], block_index: int) -> dict[str, Any]:
    width = PROTOCOL["superblock_queries"]
    start = block_index * width
    return {"observations": result.get("observations", [])[start : start + width]}


def compare(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_rows = left.get("observations", [])
    right_rows = right.get("observations", [])
    semantic_equal = len(left_rows) == len(right_rows) and all(
        V28R4.semantic_projection(a) == V28R4.semantic_projection(b)
        for a, b in zip(left_rows, right_rows)
    )
    score_shape_valid = len(left_rows) == len(right_rows)
    maximum_delta = 0.0
    for a, b in zip(left_rows, right_rows):
        a_scores, b_scores = a.get("label_scores"), b.get("label_scores")
        if not isinstance(a_scores, list) or not isinstance(b_scores, list) or len(a_scores) != 4 or len(b_scores) != 4:
            score_shape_valid = False
            continue
        maximum_delta = max(
            maximum_delta,
            *(abs(float(x) - float(y)) for x, y in zip(a_scores, b_scores)),
        )
    passes = semantic_equal and score_shape_valid and maximum_delta <= PROTOCOL["score_tolerance"]
    return {
        "observation_count": len(left_rows),
        "semantic_equal": semantic_equal,
        "maximum_absolute_label_score_delta": maximum_delta,
        "score_tolerance": PROTOCOL["score_tolerance"],
        "passes": passes,
    }


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
        errors.append("source_locks.protocol")
    if locks.get("astral_validator") != sha256_file(Path(__file__)):
        errors.append("source_locks.validator")


def validate_observations(
    rows: Any, families: list[dict[str, Any]], *, prefix: str, errors: list[str]
) -> None:
    expected_count = len(families) * PROTOCOL["queries_per_family"]
    if not isinstance(rows, list) or len(rows) != expected_count:
        errors.append(f"{prefix}.observations.census")
        return
    labels = tuple(PROTOCOL["labels"])
    cursor = 0
    for family in families:
        for query in family["queries"]:
            row = rows[cursor]
            expected = {
                "query_id": query["query_id"], "family_id": family["family_id"],
                "retrieved_family_id": family["family_id"], "fact_kind": family["fact_kind"],
                "query_class": query["evaluation_kind"],
                "prompt_sha256": stable_hash(V28R4.external_prompt(family, query)),
                "expected_label": query["expected_label"],
                "external_source_sha256": family["source_sha256"],
                "external_support_sha256": family["support_sha256"],
            }
            if any(row.get(field) != value for field, value in expected.items()):
                errors.append(f"{prefix}.observation.binding:{cursor}")
                cursor += 1
                continue
            tokens, scores = row.get("token_ids"), row.get("label_scores")
            if not isinstance(tokens, list) or not tokens or row.get("tokenized_input_sha256") != stable_hash(tokens):
                errors.append(f"{prefix}.observation.tokens:{cursor}")
            if not isinstance(scores, list) or len(scores) != 4 or any(not isinstance(value, (int, float)) or not math.isfinite(value) for value in scores):
                errors.append(f"{prefix}.observation.scores:{cursor}")
            else:
                selected = max(range(4), key=lambda index: (float(scores[index]), -index))
                if row.get("predicted_label") != labels[selected]:
                    errors.append(f"{prefix}.observation.prediction:{cursor}")
                if row.get("correct") is not (labels[selected] == query["expected_label"]):
                    errors.append(f"{prefix}.observation.correct:{cursor}")
            cursor += 1


def validate_result(
    root: Path, result: dict[str, Any], *, name: str,
    ordered: list[dict[str, Any]], errors: list[str]
) -> None:
    prefix = f"run.{name}"
    spec = PROTOCOL["runs"][name]
    indices = spec["block_indices"]
    families = [
        family for index in indices
        for family in ordered[index * PROTOCOL["superblock_families"] : (index + 1) * PROTOCOL["superblock_families"]]
    ]
    expected = {
        "version": PROTOCOL["result_version"],
        "state_slice": "astral-rgs-v28r6-legacy-batch8-endurance-implementation",
        "arm_id": "context_only", "mode": spec["mode"],
        "selected_block_indices": indices, "batch_size": PROTOCOL["batch_size"],
        "family_count": len(families),
        "query_count": len(families) * PROTOCOL["queries_per_family"],
        "partition_count": len(indices),
        "checkpoint_sha256": PROTOCOL["checkpoint_sha256"],
        "tokenizer_sha256": PROTOCOL["tokenizer_sha256"],
        "update_tokens": 0, "persistent_state_bytes": 0,
        "assessment_opened": False, "candidate_data": False,
    }
    for field, value in expected.items():
        if result.get(field) != value:
            errors.append(f"{prefix}.{field}")
    if result.get("result_sha256") != stable_hash(without_hash(result, "result_sha256")):
        errors.append(f"{prefix}.result_hash")
    rows = result.get("observations")
    if result.get("observations_sha256") != stable_hash(rows):
        errors.append(f"{prefix}.observations.hash")
    validate_observations(rows, families, prefix=prefix, errors=errors)
    receipts = result.get("block_receipts")
    if not isinstance(receipts, list) or len(receipts) != len(indices):
        errors.append(f"{prefix}.receipts.census")
        return
    cursor = 0
    for receipt, index in zip(receipts, indices):
        block_families = ordered[index * 96 : (index + 1) * 96]
        expected_receipt = {
            "block_index": index, "family_count": 96, "query_count": 1_152,
            "observation_start": cursor, "observation_stop": cursor + 1_152,
            "family_ids_sha256": stable_hash([family["family_id"] for family in block_families]),
            "observations_sha256": stable_hash(rows[cursor : cursor + 1_152]),
            "max_materialized_queries": 1_152, "max_materialized_token_rows": 1_152,
        }
        if any(receipt.get(field) != value for field, value in expected_receipt.items()):
            errors.append(f"{prefix}.receipt.binding:{index}")
        if receipt.get("receipt_sha256") != stable_hash(without_hash(receipt, "receipt_sha256")):
            errors.append(f"{prefix}.receipt.hash:{index}")
        progress = root / "runs" / name / "progress" / f"block-{index}.json"
        if not progress.is_file() or json.loads(progress.read_text(encoding="utf-8")) != receipt:
            errors.append(f"{prefix}.receipt.file:{index}")
        cursor += 1_152


def recompute_gates(
    packet: dict[str, Any], results: dict[str, dict[str, Any]], comparisons: dict[str, Any]
) -> dict[str, bool]:
    endurance = results.get("endurance_batch8", {})
    receipts = endurance.get("block_receipts", [])
    growth = (
        int(receipts[-1]["peak_rss_bytes"]) - int(receipts[0]["peak_rss_bytes"])
        if len(receipts) == 8 else PROTOCOL["max_peak_rss_growth_bytes"] + 1
    )
    return {
        "all_processes_completed": all(packet.get("processes", {}).get(name, {}).get("returncode") == 0 for name in PROTOCOL["runs"]),
        "endurance_census": endurance.get("family_count") == 768
        and endurance.get("query_count") == 9_216 and endurance.get("partition_count") == 8
        and len(endurance.get("observations", [])) == 9_216
        and [receipt.get("block_index") for receipt in receipts] == list(range(8))
        and all(receipt.get("query_count") == 1_152 for receipt in receipts),
        "materialization_bound": len(results) == 3 and all(
            result.get("max_materialized_queries", 1_153) <= 1_152
            and result.get("max_materialized_token_rows", 1_153) <= 1_152
            for result in results.values()),
        "first_endpoint_parity": bool(comparisons.get("endurance_first_vs_isolated_first", {}).get("passes")),
        "last_endpoint_parity": bool(comparisons.get("endurance_last_vs_isolated_last", {}).get("passes")),
        "rss_bound": len(results) == 3 and all(int(result.get("peak_rss_bytes", PROTOCOL["max_peak_rss_bytes"] + 1)) <= PROTOCOL["max_peak_rss_bytes"] for result in results.values()),
        "rss_growth_bound": 0 <= growth <= PROTOCOL["max_peak_rss_growth_bytes"],
        "frozen_identities": len(results) == 3 and all(
            result.get("checkpoint_sha256") == PROTOCOL["checkpoint_sha256"]
            and result.get("tokenizer_sha256") == PROTOCOL["tokenizer_sha256"]
            for result in results.values()),
        "zero_persistent_activity": len(results) == 3 and all(
            result.get("update_tokens") == 0 and result.get("persistent_state_bytes") == 0
            and result.get("assessment_opened") is False and result.get("candidate_data") is False
            for result in results.values()),
    }


def validate(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    V28R4.validate_manifest(root, errors)
    required = {name: root / filename for name, filename in {
        "packet": "preflight-packet.json", "corpus": "corpus.json",
        "fingerprint": "predecessor-fingerprint.json", "receipt": "preflight-receipt.json",
        "seed": "fixed-seed.json",
    }.items()}
    if any(not path.is_file() for path in required.values()):
        return {"valid": False, "qualified": False, "errors": errors + ["artifact.required_files"]}
    values = {name: json.loads(path.read_text(encoding="utf-8")) for name, path in required.items()}
    packet, corpus = values["packet"], values["corpus"]
    if packet.get("version") != PROTOCOL["packet_version"]:
        errors.append("packet.version")
    if packet.get("packet_sha256") != stable_hash(without_hash(packet, "packet_sha256")):
        errors.append("packet.hash")
    if packet.get("protocol_sha256") != sha256_file(PROTOCOL_PATH):
        errors.append("packet.protocol")
    if packet.get("source_locks") != values["receipt"].get("source_locks"):
        errors.append("packet.source_locks_receipt")
    for repository in ("rgs", "astral"):
        binding = packet.get("source_bindings", {}).get(repository, {})
        if binding.get("dirty") is not False or not binding.get("commit") or not binding.get("tree"):
            errors.append(f"source_binding.{repository}")
    validate_source_locks(root, packet, errors)
    expected_seed = hashlib.sha256(PROTOCOL["fixture_seed_label"].encode()).hexdigest()
    if expected_seed != PROTOCOL["fixture_seed_hex"] or values["seed"] != {"label": PROTOCOL["fixture_seed_label"], "seed_hex": expected_seed}:
        errors.append("fixture.seed")
    if values["fingerprint"] != V28R4.empty_fingerprint():
        errors.append("fixture.fingerprint")
    corpus_errors: list[str] = []
    families, _ = V28R4.V28R3.validate_corpus(
        corpus, seed=bytes.fromhex(expected_seed), fingerprint=values["fingerprint"],
        errors=corpus_errors, families_per_kind=PROTOCOL["families_per_fact_kind"],
    )
    errors.extend(f"fixture.{error}" for error in corpus_errors)
    ordered = V28R4.expected_order(families) if families else []
    fixture = packet.get("fixture", {})
    expected_fixture = {
        "seed_label": PROTOCOL["fixture_seed_label"], "seed_hex": expected_seed,
        "families_per_kind": 192, "family_count": 768, "query_count": 9_216,
        "corpus_manifest_sha256": corpus.get("manifest_sha256"), "candidate_data": False,
    }
    if fixture != expected_fixture:
        errors.append("fixture.packet")

    results: dict[str, dict[str, Any]] = {}
    for name in PROTOCOL["runs"]:
        result_path = root / "runs" / name / "result.json"
        process_path = root / "runs" / name / "process.json"
        process = json.loads(process_path.read_text(encoding="utf-8")) if process_path.is_file() else None
        if not isinstance(process, dict) or packet.get("processes", {}).get(name) != process:
            errors.append(f"run.{name}.process")
            process = {}
        result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else None
        if process.get("returncode") == 0:
            if not isinstance(result, dict) or process.get("result_present") is not True:
                errors.append(f"run.{name}.successful_result_missing")
            else:
                results[name] = result
                if packet.get("run_file_sha256s", {}).get(name) != sha256_file(result_path):
                    errors.append(f"run.{name}.file_hash")
                validate_result(root, result, name=name, ordered=ordered, errors=errors)
        else:
            if result is not None or process.get("result_present") is not False or packet.get("run_file_sha256s", {}).get(name) is not None:
                errors.append(f"run.{name}.failed_result_state")

    comparisons = {
        "endurance_first_vs_isolated_first": compare(
            endpoint_view(results["endurance_batch8"], 0), results["isolated_first_batch8"]
        ) if "endurance_batch8" in results and "isolated_first_batch8" in results else None,
        "endurance_last_vs_isolated_last": compare(
            endpoint_view(results["endurance_batch8"], 7), results["isolated_last_batch8"]
        ) if "endurance_batch8" in results and "isolated_last_batch8" in results else None,
    }
    if packet.get("comparisons") != comparisons:
        errors.append("packet.comparisons")
    gates = recompute_gates(packet, results, comparisons)
    qualified = all(gates.values())
    if packet.get("gates") != gates or packet.get("qualified") is not qualified:
        errors.append("packet.gates")
    if packet.get("status") != ("LegacyBatch8EndurancePassed" if qualified else "LegacyBatch8EnduranceFailed"):
        errors.append("packet.status")
    boundaries = {
        "persistent_cells_started": 0, "update_tokens": 0, "adapters_created": 0,
        "assessment_opened": False, "scientific_campaign_run": False,
        "claim_ceiling": PROTOCOL["claim_ceiling"],
    }
    for field, expected in boundaries.items():
        if packet.get(field) != expected:
            errors.append(f"boundary.{field}")
    return {
        "version": "astral.rgs_acquisition_v28r6.validation_report.v1",
        "state_slice": PROTOCOL["state_slice"], "valid": not errors,
        "qualified": qualified and not errors, "errors": errors,
        "recomputed_gates": gates, "comparisons": comparisons,
        "claim_ceiling": PROTOCOL["claim_ceiling"], "scientific_evidence": False,
        "validator_source_sha256": sha256_file(Path(__file__)),
    }
