"""Independent validator for the frozen Oak Lab H100 V9 packet.

State slice: ``oaklab-experience-learning-h100-replication-v9``.
The validator is fail-closed and performs no learner, provider, H100, energy,
real-data, or assessment execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .compile_oaklab_h100_v9_protocol import (
    CAMPAIGN_ARTIFACT_PATH,
    COMPILED_PATH,
    ROOT,
    SOURCE_PATH,
    STATE_SLICE,
    canonical,
    compile_protocol,
    digest,
    sha256_file,
)


SOURCE = ROOT / SOURCE_PATH
COMPILED = ROOT / COMPILED_PATH
ARTIFACT = ROOT / CAMPAIGN_ARTIFACT_PATH
PACKET = ROOT / "docs/research/experience-learning/67-oaklab-h100-replication-v9-review-packet.md"
SCHEMA = "oaklab.experience-learning.h100-replication-v9.compiled.v1"


def _hex(value: Any, label: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{label} must be a 64-character digest")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"{label} is not hexadecimal") from exc


def _closed(value: Any, keys: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} object is not closed")


def validate_campaign_artifact(source_sha256: str, compiled_sha256: str) -> dict[str, Any]:
    if not ARTIFACT.is_file():
        raise ValueError("V9 campaign-manifest artifact is missing")
    artifact = json.loads(ARTIFACT.read_bytes())
    keys = {"schema", "state_slice", "source_sha256", "compiler_sha256", "validator_sha256", "tests_sha256", "agents_sha256", "campaign_manifest_artifact_sha256", "compiled_protocol_file_sha256", "review_packet_sha256", "backend_sha256", "guard_sha256", "model_sha256", "data_sha256", "fit_lock_sha256", "tune_lock_sha256", "tune_lock_receipt_sha256", "provider_allocation_sha256", "provider_cost_sha256", "provider_stop_sha256", "energy_receipt_sha256", "result_root_sha256", "hard_usd_ceiling", "manifest_sha256"}
    _closed(artifact, keys, "campaign manifest artifact")
    if artifact["schema"] != "oaklab.h100.v9.campaign-manifest-artifact.v1" or artifact["state_slice"] != STATE_SLICE:
        raise ValueError("campaign artifact identity mismatch")
    if artifact["source_sha256"] != source_sha256 or artifact["compiled_protocol_file_sha256"] != sha256_file(COMPILED):
        raise ValueError("campaign artifact is stale against source or compiled bytes")
    if artifact["compiler_sha256"] != sha256_file(ROOT / "experiments/experience_learning/compile_oaklab_h100_v9_protocol.py") or artifact["validator_sha256"] != sha256_file(ROOT / "experiments/experience_learning/validate_oaklab_h100_v9_protocol.py"):
        raise ValueError("campaign artifact compiler/validator binding mismatch")
    if artifact["tests_sha256"] != sha256_file(ROOT / "experiments/experience_learning/tests/test_oaklab_h100_v9_protocol.py") or artifact["agents_sha256"] != sha256_file(ROOT / "AGENTS.md"):
        raise ValueError("campaign artifact tests/AGENTS binding mismatch")
    if artifact["review_packet_sha256"] != sha256_file(PACKET):
        raise ValueError("campaign artifact review-packet binding mismatch")
    for key in keys - {"schema", "state_slice", "hard_usd_ceiling", "manifest_sha256"}:
        _hex(artifact[key], key)
    if artifact["hard_usd_ceiling"] != 25:
        raise ValueError("V9 hard USD ceiling changed")
    expected = digest({key: value for key, value in artifact.items() if key != "manifest_sha256"})
    if artifact["manifest_sha256"] != expected:
        raise ValueError("campaign artifact self-digest mismatch")
    return artifact


def validate_compiled() -> dict[str, Any]:
    source = json.loads(SOURCE.read_bytes())
    expected = compile_protocol(source)
    compiled = json.loads(COMPILED.read_bytes())
    if compiled != expected:
        raise ValueError("compiled V9 artifact does not reproduce from current source")
    if compiled["schema"] != SCHEMA or compiled["state_slice"] != STATE_SLICE:
        raise ValueError("compiled V9 identity mismatch")
    _hex(compiled["compiled_protocol_sha256"], "compiled_protocol_sha256")
    return {"source_sha256": sha256_file(SOURCE), "compiled_sha256": sha256_file(COMPILED), "compiled_self_digest": compiled["compiled_protocol_sha256"]}


def validate() -> dict[str, Any]:
    current = validate_compiled()
    artifact = validate_campaign_artifact(current["source_sha256"], current["compiled_sha256"])
    if not PACKET.is_file():
        raise ValueError("V9 review packet is missing")
    return {"valid": True, "state_slice": STATE_SLICE, "source_sha256": current["source_sha256"], "compiled_sha256": current["compiled_sha256"], "compiled_self_digest": current["compiled_self_digest"], "campaign_manifest_sha256": artifact["manifest_sha256"], "assessment_materialization_state": "absent", "real_execution": "prohibited", "provider": "prohibited"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()
    print(json.dumps(validate(), sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
