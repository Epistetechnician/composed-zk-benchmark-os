from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from v28r3 import (
    PROTOCOL,
    sha256_file,
    sha256_text,
    stable_hash,
    validate_baseline_run,
    validate_corpus,
    validate_fingerprint,
    validate_manifest,
    without_hash,
)


STATE_SLICE = "astral-rgs-v28r3-infrastructure-failure-sealing"


def validate(root: Path, ledger: Path) -> dict[str, Any]:
    errors: list[str] = []
    packet = json.loads((root / "abort-packet.json").read_text(encoding="utf-8"))
    if packet.get("version") != "mesh.astral_v28r3_infrastructure_abort.v1" or packet.get("state_slice") != STATE_SLICE:
        errors.append("abort.version")
    if packet.get("abort_sha256") != stable_hash(without_hash(packet, "abort_sha256")):
        errors.append("abort.hash")
    if packet.get("ledger_sha256") != sha256_file(ledger):
        errors.append("abort.ledger")
    fingerprint = json.loads((root / "predecessor-fingerprint.json").read_text(encoding="utf-8"))
    validate_fingerprint(fingerprint, errors)
    seed_doc = json.loads((root / "seed-material.json").read_text(encoding="utf-8"))
    seed = bytes.fromhex(seed_doc["seed_hex"])
    corpus = json.loads((root / "corpus.json").read_text(encoding="utf-8"))
    families, query_map = validate_corpus(corpus, seed=seed, fingerprint=fingerprint, errors=errors)
    joined, metrics, raw = {}, {}, {}
    for arm in PROTOCOL["baseline_arms"]:
        path = root / "novelty" / arm / "result.json"
        run = json.loads(path.read_text(encoding="utf-8"))
        raw[arm] = run["observations"]
        joined[arm], metrics[arm] = validate_baseline_run(run, arm_id=arm, families=families, query_map=query_map, errors=errors)
        if packet["novelty"]["run_file_sha256s"].get(arm) != sha256_file(path):
            errors.append(f"abort.run_hash.{arm}")
    if raw.get("pre_update") != raw.get("no_update"):
        errors.append("abort.novelty_parity")
    novelty_passed = all(row.get("equivalence_passed") for row in metrics.values())
    if not novelty_passed or packet.get("novelty", {}).get("passed") is not True:
        errors.append("abort.novelty_gate")
    if packet.get("novelty", {}).get("metrics") != metrics:
        errors.append("abort.novelty_metrics")
    process_path = root / "controls/context_only/process.json"
    process = json.loads(process_path.read_text(encoding="utf-8"))
    if process.get("returncode") != -6 or "kIOGPUCommandBufferCallbackErrorOutOfMemory" not in process.get("stderr", ""):
        errors.append("abort.failure_identity")
    if packet.get("failure", {}).get("stderr_sha256") != sha256_text(process["stderr"]):
        errors.append("abort.failure_hash")
    forbidden = [root / "controls/context_only/result.json", root / "cells", root / "campaign.json"]
    if any(path.exists() for path in forbidden):
        errors.append("abort.forbidden_post_failure_state")
    if any(packet.get(key) != value for key, value in {"persistent_cells_started": 0, "updates_started": 0, "adapters_created": 0, "acquisition_assessed": False, "rerun_authorized": False}.items()):
        errors.append("abort.claim_boundary")
    validate_manifest(root, errors)
    core = {
        "version": "astral.v28r3_abort_validation_report.v1",
        "state_slice": STATE_SLICE,
        "valid": not errors,
        "status": "ValidatedInfrastructureFailureAfterNovelty" if not errors else "Invalid",
        "errors": sorted(set(errors)),
        "novelty_metrics": metrics,
        "claim_ceiling": "LocalModelBackedAcquisitionNoveltyPreflightV28R3" if not errors else "NoScientificClaim",
        "acquisition_validated": False,
        "continual_learning_validated": False,
        "independent_replication_validated": False,
    }
    return {**core, "report_sha256": stable_hash(core)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a sealed V28R3 infrastructure abort")
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = validate(args.artifact_root, args.ledger)
    except (AttributeError, KeyError, TypeError, ValueError, OSError) as exc:
        core = {"version": "astral.v28r3_abort_validation_report.v1", "state_slice": STATE_SLICE, "valid": False, "status": "Invalid", "errors": [f"malformed.{type(exc).__name__}"], "claim_ceiling": "NoScientificClaim"}
        result = {**core, "report_sha256": stable_hash(core)}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
