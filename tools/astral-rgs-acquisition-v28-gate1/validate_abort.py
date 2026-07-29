from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True

STATE_SLICE = "astral-rgs-v28-gate1-infrastructure-abort-remediation"
EXPECTED_ERROR = "ModuleNotFoundError: No module named 'mlx'"
EXPECTED_RGS_COMMIT = "438fdef2b24eee7ea3299a986b20122337d84cdc"
EXPECTED_ASTRAL_COMMIT = "6e7490fc5871e58d1b90932c4c6bc8ae5c2ce946"


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


def validate(*, packet: Any, artifact_root: Path, ledger_path: Path) -> dict[str, Any]:
    errors = []
    if not isinstance(packet, dict):
        errors.append("packet:not_object")
        packet = {}
    body = {key: value for key, value in packet.items() if key != "abort_packet_sha256"}
    if packet.get("abort_packet_sha256") != stable_hash(body):
        errors.append("packet:hash")
    expected = {
        "version": "mesh.astral_v28_gate1_infrastructure_abort.v1",
        "state_slice": STATE_SLICE,
        "status": "InvalidInfrastructureAbortBeforeModelLoad",
        "scientific_disposition": "NoGate1Result",
        "campaign_consumed": True,
        "replacement_campaign_allowed": False,
        "model_loaded": False,
        "tokenizer_loaded": False,
        "optimizer_steps": 0,
        "adapter_states_created": 0,
        "persistent_cells_started": 0,
        "model_outcomes_created": 0,
        "failure_error": EXPECTED_ERROR,
        "claim_ceiling": "RetainedInfrastructureAbortNoModelOutcomeV28Gate1",
        "retention_recovery_run": False,
        "selection_run": False,
        "assessment_opened": False,
        "confirmation_run": False,
        "independent_replication": False,
    }
    for key, value in expected.items():
        if packet.get(key) != value:
            errors.append(f"packet:{key}")
    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        ledger_body = {key: value for key, value in ledger.items() if key != "ledger_sha256"}
        if ledger.get("ledger_sha256") != stable_hash(ledger_body):
            errors.append("ledger:hash")
        if packet.get("ledger_sha256") != ledger.get("ledger_sha256"):
            errors.append("packet:ledger_binding")
        if packet.get("ledger_file_sha256") != sha256_file(ledger_path):
            errors.append("packet:ledger_file")
        if ledger.get("rgs_source", {}).get("commit") != EXPECTED_RGS_COMMIT:
            errors.append("ledger:rgs_commit")
        if ledger.get("astral_source", {}).get("commit") != EXPECTED_ASTRAL_COMMIT:
            errors.append("ledger:astral_commit")
    except Exception:
        errors.append("ledger:unreadable")
    process_path = artifact_root / "controls" / "context_only" / "process.json"
    failure_path = artifact_root / "campaign-failure.json"
    try:
        process = json.loads(process_path.read_text(encoding="utf-8"))
        if process.get("returncode") != 1 or EXPECTED_ERROR not in str(process.get("stderr")):
            errors.append("process:error")
        if "import mlx.core as mx" not in str(process.get("stderr")):
            errors.append("process:failure_stage")
        if packet.get("process_record_sha256") != sha256_file(process_path):
            errors.append("packet:process_binding")
    except Exception:
        errors.append("process:unreadable")
    try:
        if packet.get("campaign_failure_sha256") != sha256_file(failure_path):
            errors.append("packet:failure_binding")
    except Exception:
        errors.append("artifact:failure_missing")
    if (artifact_root / "controls" / "context_only" / "result.json").exists():
        errors.append("artifact:unexpected_model_result")
    if (artifact_root / "cells").exists():
        errors.append("artifact:unexpected_persistent_cells")
    valid = not errors
    return {
        "version": "astral.v28_gate1_abort_validation_report.v1",
        "state_slice": STATE_SLICE,
        "valid_failure_record": valid,
        "scientific_result_valid": False,
        "status": packet.get("status") if valid else "InvalidFailureRecord",
        "abort_packet_sha256": packet.get("abort_packet_sha256"),
        "claim_ceiling": (
            "RetainedInfrastructureAbortNoModelOutcomeV28Gate1" if valid else "NoClaim"
        ),
        "errors": errors,
    }


def write_exclusive(path: Path, value: dict[str, Any]) -> None:
    data = json.dumps(value, indent=2, sort_keys=True).encode() + b"\n"
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the retained V28 Gate 1 abort")
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    report = validate(packet=packet, artifact_root=args.artifact_root, ledger_path=args.ledger)
    write_exclusive(args.output, report)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["valid_failure_record"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
