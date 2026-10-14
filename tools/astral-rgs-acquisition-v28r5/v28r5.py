from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
PROTOCOL_PATH = HERE / "protocol.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
SOURCE_LOCK_NAMES = (
    "rgs_corpus",
    "rgs_parity_core",
    "rgs_last_token_worker",
    "rgs_coordinator",
    "astral_protocol",
    "astral_validator",
    "astral_cli",
)


def load_v28r4() -> Any:
    path = HERE.parent / "astral-rgs-acquisition-v28r4" / "v28r4.py"
    spec = importlib.util.spec_from_file_location("astral_v28r4_for_v28r5", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("V28R4 validator seam is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V28R4 = load_v28r4()
stable_hash = V28R4.stable_hash
sha256_file = V28R4.sha256_file
without_hash = V28R4.without_hash


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


def validate_optimized_result(
    result: dict[str, Any],
    *,
    name: str,
    families: list[dict[str, Any]],
    errors: list[str],
) -> None:
    prefix = f"run.{name}"
    if result.get("version") != PROTOCOL["result_version"]:
        errors.append(f"{prefix}.version")
    if result.get("state_slice") != "astral-rgs-v28r5-last-token-projection-preflight-implementation":
        errors.append(f"{prefix}.state_slice")
    if result.get("mode") != "last-token-projection":
        errors.append(f"{prefix}.mode")
    if result.get("batch_size") != PROTOCOL["runs"][name]:
        errors.append(f"{prefix}.batch_size")
    if result.get("result_sha256") != stable_hash(without_hash(result, "result_sha256")):
        errors.append(f"{prefix}.result_hash")
    telemetry = result.get("projection_telemetry")
    if (
        result.get("last_token_projection") is not True
        or result.get("sequence_wide_vocabulary_logits") is not False
        or not isinstance(telemetry, dict)
        or telemetry.get("maximum_sequence_wide_logit_elements") != 0
        or telemetry.get("maximum_batch_rows", 0) > PROTOCOL["runs"][name]
        or telemetry.get("maximum_projected_logit_elements", 0) <= 0
    ):
        errors.append(f"{prefix}.projection")
    synthetic = {
        **result,
        "version": V28R4.PROTOCOL["result_version"],
        "state_slice": "astral-rgs-v28r4-streaming-control-preflight-implementation",
        "mode": "monolithic-reference"
        if name == "optimized_batch8"
        else "streaming-superblock",
    }
    synthetic["result_sha256"] = stable_hash(without_hash(synthetic, "result_sha256"))
    V28R4.validate_result(
        synthetic,
        name="reference_batch8" if name == "optimized_batch8" else "stream_batch64",
        families=families,
        errors=errors,
    )


def validate(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    V28R4.validate_manifest(root, errors)
    paths = {
        "packet": root / "preflight-packet.json",
        "corpus": root / "corpus.json",
        "fingerprint": root / "predecessor-fingerprint.json",
        "receipt": root / "preflight-receipt.json",
        "reference": root / "reference/v28r4-reference-batch8.json",
    }
    if any(not path.is_file() for path in paths.values()):
        errors.append("artifact.required_files")
        return {"valid": False, "qualified": False, "errors": errors}
    packet = json.loads(paths["packet"].read_text(encoding="utf-8"))
    corpus = json.loads(paths["corpus"].read_text(encoding="utf-8"))
    fingerprint = json.loads(paths["fingerprint"].read_text(encoding="utf-8"))
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    reference = json.loads(paths["reference"].read_text(encoding="utf-8"))
    if packet.get("version") != PROTOCOL["packet_version"]:
        errors.append("packet.version")
    if packet.get("packet_sha256") != stable_hash(without_hash(packet, "packet_sha256")):
        errors.append("packet.hash")
    if packet.get("protocol_sha256") != sha256_file(PROTOCOL_PATH):
        errors.append("packet.protocol")
    if packet.get("source_locks") != receipt.get("source_locks"):
        errors.append("packet.source_locks_receipt")
    for repository in ("rgs", "astral"):
        binding = packet.get("source_bindings", {}).get(repository, {})
        if binding.get("dirty") is not False or not binding.get("commit") or not binding.get("tree"):
            errors.append(f"source_binding.{repository}")
    validate_source_locks(root, packet, errors)
    if sha256_file(paths["reference"]) != PROTOCOL["reference_file_sha256"]:
        errors.append("reference.file_hash")
    if packet.get("reference_file_sha256") != PROTOCOL["reference_file_sha256"]:
        errors.append("reference.packet_hash")

    seed = bytes.fromhex(PROTOCOL["fixture_seed_hex"])
    expected_fingerprint = V28R4.empty_fingerprint()
    if fingerprint != expected_fingerprint:
        errors.append("fixture.fingerprint")
    corpus_errors: list[str] = []
    families, _ = V28R4.V28R3.validate_corpus(
        corpus,
        seed=seed,
        fingerprint=fingerprint,
        errors=corpus_errors,
        families_per_kind=PROTOCOL["families_per_fact_kind"],
    )
    errors.extend(f"fixture.{error}" for error in corpus_errors)
    ordered = V28R4.expected_order(families) if families else []
    V28R4.validate_result(
        reference, name="reference_batch8", families=ordered, errors=errors
    )

    results: dict[str, dict[str, Any]] = {}
    for name in PROTOCOL["runs"]:
        result_path = root / "runs" / name / "result.json"
        process_path = root / "runs" / name / "process.json"
        result = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else None
        process = json.loads(process_path.read_text(encoding="utf-8")) if process_path.is_file() else None
        embedded = packet.get("processes", {}).get(name)
        if not isinstance(process, dict) or process != embedded:
            errors.append(f"run.{name}.process")
            process = {}
        returncode = process.get("returncode")
        present = process.get("result_present")
        if returncode == 0:
            if present is not True or not isinstance(result, dict):
                errors.append(f"run.{name}.result_missing")
            else:
                results[name] = result
                if packet.get("run_file_sha256s", {}).get(name) != sha256_file(result_path):
                    errors.append(f"run.{name}.file_hash")
                validate_optimized_result(result, name=name, families=ordered, errors=errors)
        else:
            if not isinstance(returncode, int) or present is not False or result is not None:
                errors.append(f"run.{name}.failed_process")
            if packet.get("run_file_sha256s", {}).get(name) is not None:
                errors.append(f"run.{name}.failed_hash")

    first = V28R4.optional_compare(reference, results.get("optimized_batch8"))
    second = V28R4.optional_compare(
        results.get("optimized_batch8"), results.get("optimized_batch64")
    )
    comparisons = {
        "reference_vs_optimized_batch8": first,
        "optimized_batch8_vs_batch64": second,
    }
    if packet.get("comparisons") != comparisons:
        errors.append("packet.comparisons")
    rows = list(results.values())
    gates = {
        "all_processes_completed": all(
            packet.get("processes", {}).get(name, {}).get("returncode") == 0
            for name in PROTOCOL["runs"]
        ),
        "reference_batch8_parity": bool(first and first["passes"]),
        "optimized_batch64_parity": bool(second and second["passes"]),
        "last_token_projection_only": len(rows) == 2
        and all(
            row.get("last_token_projection") is True
            and row.get("sequence_wide_vocabulary_logits") is False
            and row.get("projection_telemetry", {}).get("maximum_sequence_wide_logit_elements") == 0
            for row in rows
        ),
        "rss_bound": len(rows) == 2
        and all(row.get("peak_rss_bytes", PROTOCOL["max_peak_rss_bytes"] + 1) <= PROTOCOL["max_peak_rss_bytes"] for row in rows),
        "frozen_identities": len(rows) == 2
        and all(
            row.get("checkpoint_sha256") == PROTOCOL["checkpoint_sha256"]
            and row.get("tokenizer_sha256") == PROTOCOL["tokenizer_sha256"]
            for row in rows
        ),
    }
    qualified = all(gates.values())
    if packet.get("gates") != gates or packet.get("qualified") is not qualified:
        errors.append("packet.gates")
    expected_status = "LastTokenProjectionPreflightPassed" if qualified else "LastTokenProjectionPreflightFailed"
    if packet.get("status") != expected_status:
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
        "version": "astral.rgs_acquisition_v28r5.validation_report.v1",
        "state_slice": PROTOCOL["state_slice"],
        "valid": not errors,
        "qualified": qualified and not errors,
        "errors": errors,
        "recomputed_gates": gates,
        "comparisons": comparisons,
        "claim_ceiling": PROTOCOL["claim_ceiling"],
        "scientific_evidence": False,
    }
