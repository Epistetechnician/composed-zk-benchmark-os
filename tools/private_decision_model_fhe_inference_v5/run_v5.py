"""Run the frozen V3 synthetic FHE IPC path with a canonical V5 receipt.

State slices: private-decision-model-fhe-local-ipc-receipt-v5 and
global-experiment-assurance-lifecycle-v1. V1-V4 remain frozen.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
V5_DIR = ROOT / "tools" / "private_decision_model_fhe_inference_v5"
V3_DIR = ROOT / "tools" / "private_decision_model_fhe_inference_v3"
V1_DIR = ROOT / "tools" / "private_decision_model_fhe_inference_v1"
PACKET_PATH = ROOT / "docs" / "research" / "private-decision-model-fhe-local-ipc-receipt-v5-packet.json"
sys.path.insert(0, str(V3_DIR))
import run_v3 as frozen_v3_runner  # noqa: E402

STATE_SLICE = "private-decision-model-fhe-local-ipc-receipt-v5"
GOVERNANCE_SLICE = "global-experiment-assurance-lifecycle-v1"

V3_FILES = (
    V3_DIR / "run_v3.py",
    V3_DIR / "server_worker_v3.py",
    V3_DIR / "ipc_contract.py",
    V3_DIR / "tests" / "test_ipc_contract.py",
    V1_DIR / "decision_model.py",
)
COMPOSITE_FILES = (
    V5_DIR / "run_v5.py",
    V5_DIR / "tests" / "test_receipt_digest.py",
    *V3_FILES,
)


def canonical_repo_path(path: Path) -> str:
    """Return a stable repository-relative path for any invocation spelling."""
    return path.resolve().relative_to(ROOT).as_posix()


def source_digest(paths: tuple[Path, ...]) -> str:
    """Hash ordered canonical repository paths and exact file bytes."""
    digest = hashlib.sha256()
    for path in paths:
        digest.update(canonical_repo_path(path).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def v3_source_digest() -> str:
    return source_digest(V3_FILES)


def v5_source_digest() -> str:
    return source_digest(COMPOSITE_FILES)


def validate_frozen_packet() -> tuple[dict[str, Any], str]:
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    for item in packet["source_identity"]["files"]:
        path = ROOT / item["path"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != item["sha256"]:
            raise RuntimeError(f"frozen source digest mismatch: {item['path']}")

    protocol = packet["protocol"]
    protocol_path = ROOT / protocol["path"]
    if hashlib.sha256(protocol_path.read_bytes()).hexdigest() != protocol["sha256"]:
        raise RuntimeError("frozen V5 protocol digest mismatch")

    predecessor_digest = v3_source_digest()
    if predecessor_digest != packet["predecessor"]["v3_source_composite_sha256"]:
        raise RuntimeError("frozen V3 source composite mismatch")

    composite_digest = v5_source_digest()
    if composite_digest != packet["source_identity"]["v5_source_composite_sha256"]:
        raise RuntimeError("frozen V5 source composite mismatch")

    expected_paths = [canonical_repo_path(path) for path in COMPOSITE_FILES]
    if expected_paths != packet["source_identity"]["composite_files"]:
        raise RuntimeError("V5 composite file order does not match the frozen packet")

    packet_digest = hashlib.sha256(
        json.dumps(packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return packet, packet_digest


def execute() -> dict[str, Any]:
    packet, packet_digest = validate_frozen_packet()
    v5_digest = packet["source_identity"]["v5_source_composite_sha256"]
    original_digest_supplier = frozen_v3_runner._source_digest
    frozen_v3_runner._source_digest = lambda: v5_digest
    try:
        result = frozen_v3_runner.execute()
    finally:
        frozen_v3_runner._source_digest = original_digest_supplier

    result.pop("v3_source_sha256", None)
    result["schema"] = "private-decision-model-fhe-local-ipc-receipt-v5-result"
    result["state_slice"] = STATE_SLICE
    result["governance_state_slice"] = GOVERNANCE_SLICE
    result["claim_ceiling"] = packet["claim_ceiling"]
    result["reproducibility_status"] = "single local V5 qualification; not REPRODUCED_LOCAL"
    result["v5_packet_canonical_sha256"] = packet_digest
    result["v5_source_sha256"] = v5_digest
    result["v3_frozen_source_sha256"] = packet["predecessor"]["v3_source_composite_sha256"]
    result["execution"]["source_digest_matches_packet"] = v5_digest == packet["source_identity"]["v5_source_composite_sha256"]
    result["execution"]["source_digest_path_policy"] = "resolved canonical repository-relative paths"
    return result


def main() -> int:
    print(json.dumps(execute(), ensure_ascii=True, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
