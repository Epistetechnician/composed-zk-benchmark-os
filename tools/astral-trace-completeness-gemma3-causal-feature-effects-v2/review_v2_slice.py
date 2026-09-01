"""Packet compiler and independent-review admission boundary for V2.

State slice: astral-trace-completeness-gemma3-causal-feature-effects-v2.

This module never manufactures an ACCEPT. A reviewer outside the operator
identity must provide the signed packet-bound receipt.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

import protocol_v2_slice as protocol


SOURCE_FILES = (
    "protocol_v2_slice.py",
    "corpus_v2_slice.py",
    "custody_v2_slice.py",
    "registry_v2_slice.py",
    "adapter_v2_slice.py",
    "transcoder_v2_slice.py",
    "effects_v2_slice.py",
    "review_v2_slice.py",
    "validate_v2_slice.py",
    "run_v2.py",
)
DEPENDENCY_FILES = (
    "tools/astral-trace-completeness-v2/protocol_v2.py",
    "tools/astral-trace-completeness-v2/registry_v2.py",
    "tools/astral-trace-completeness-v2/torch_adapter_v2.py",
)

# The packet must be reproducible on the node even though the checkout path is
# different there. The custody receipt records the concrete local path; this
# field binds the source identity without binding it to one filesystem layout.
REPOSITORY_IDENTITY = "composed-zk-benchmark-os"


def source_manifest(repository_root: Path) -> dict[str, Any]:
    root = Path(__file__).resolve().parent
    files = {
        f"tools/astral-trace-completeness-gemma3-causal-feature-effects-v2/{name}": protocol.sha256_file(root / name)
        for name in SOURCE_FILES
        if (root / name).is_file()
    }
    repository_root = repository_root.resolve()
    files.update(
        {
            name: protocol.sha256_file(repository_root / name)
            for name in DEPENDENCY_FILES
            if (repository_root / name).is_file()
        }
    )
    expected_files = {
        *(f"tools/astral-trace-completeness-gemma3-causal-feature-effects-v2/{name}" for name in SOURCE_FILES),
        *DEPENDENCY_FILES,
    }
    value = {
        "repository_identity": REPOSITORY_IDENTITY,
        "state_slice": protocol.STATE_SLICE,
        "files": files,
        "source_file_set_complete": set(files) == expected_files,
    }
    return {**value, "manifest_sha256": protocol.digest_json(value)}


def packet(repository_root: Path, custody_root: Path = protocol.CUSTODY_ROOT) -> dict[str, Any]:
    contract = protocol.public_contract()
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "v4_freeze": {
            "state_slice": "astral-trace-completeness-gemma3-end-to-end-v4",
            "qualification_sha256": "9c90364b29e6992539323acea147ba0e9bd746578f40b69f0d9f3f1438493eab",
            "freeze_rule": "historical V4 source, corpus, effects, prediction, and results are immutable and are not V2 scientific inputs",
        },
        "contract": contract,
        "contract_sha256": contract["contract_sha256"],
        "source_manifest": source_manifest(repository_root),
        "required_external_bindings": {
            "givemeanode_allocation_receipt": str(protocol.NODE_ALLOCATION_RECEIPT),
            "exact_node_id": True,
            "hard_spend_ceiling_usd": "positive finite user-authorized value",
            "fresh_v2_slice_model_manifest": True,
            "fresh_v2_slice_runtime_manifest": True,
            "fresh_v2_slice_asset_qc": True,
            "fresh_v2_slice_corpus_custody": True,
            "signed_independent_accept": True,
        },
        "external_binding_digests": protocol.binding_digest_map(custody_root),
        "assessment_authorized": False,
        "model_execution_authorized": False,
        "operator_may_self_sign_accept": False,
    }
    return {**value, "packet_sha256": protocol.digest_json(value)}


def validate_signed_acceptance(receipt: Mapping[str, Any], packet_digest: str) -> None:
    if receipt.get("protocol") != protocol.PROTOCOL_ID or receipt.get("state_slice") != protocol.STATE_SLICE:
        raise protocol.ProtocolError("review receipt identity is not bound to V2")
    if receipt.get("verdict") != "ACCEPT":
        raise protocol.ProtocolError("review receipt is not ACCEPT")
    if receipt.get("reviewer_role") != protocol.REVIEWER_ROLE:
        raise protocol.ProtocolError("reviewer role is not the frozen independent role")
    if receipt.get("operator") != protocol.OPERATOR_ID:
        raise protocol.ProtocolError("review receipt does not name the frozen operator")
    if receipt.get("claim_ceiling") != protocol.QUALIFICATION_CEILING:
        raise protocol.ProtocolError("review receipt claim ceiling is not the qualification ceiling")
    if receipt.get("packet_sha256") != packet_digest:
        raise protocol.ProtocolError("review receipt is not packet-bound")
    signature = receipt.get("signature")
    if not isinstance(signature, Mapping) or signature.get("algorithm") != "ed25519":
        raise protocol.ProtocolError("review receipt lacks an Ed25519 signature")
    if not isinstance(signature.get("public_key_hex"), str) or len(signature["public_key_hex"]) != 64:
        raise protocol.ProtocolError("review public key is malformed")
    if not isinstance(signature.get("signature_hex"), str) or len(signature["signature_hex"]) != 128:
        raise protocol.ProtocolError("review signature is malformed")
    if receipt.get("receipt_sha256") != protocol.digest_json(
        {key: value for key, value in receipt.items() if key not in {"signature", "receipt_sha256"}}
    ):
        raise protocol.ProtocolError("review receipt digest is malformed")
    unsigned = {
        key: value
        for key, value in receipt.items()
        if key not in {"signature", "receipt_sha256"}
    }
    message = protocol.canonical_bytes({**unsigned, "receipt_sha256": receipt["receipt_sha256"]})
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(signature["public_key_hex"]))
        public_key.verify(bytes.fromhex(signature["signature_hex"]), message)
    except (ImportError, InvalidSignature, ValueError) as exc:
        raise protocol.ProtocolError("review Ed25519 signature cannot be verified") from exc


def static_review(packet_value: Mapping[str, Any], *, node_receipt: Mapping[str, Any] | None, spend_ceiling_usd: float | None, reviewer_receipt: Mapping[str, Any] | None, custody_root: Path = protocol.CUSTODY_ROOT) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    if node_receipt is None:
        findings.append({"id": "V2-NODE-001", "severity": "critical", "finding": "exact GiveMeANode allocation receipt and node_id are absent"})
    else:
        try:
            protocol.require_node_admission(
                node_receipt,
                spend_ceiling_usd=spend_ceiling_usd or 0.0,
            )
        except protocol.ProtocolError as exc:
            findings.append({"id": "V2-NODE-002", "severity": "critical", "finding": str(exc)})
    if spend_ceiling_usd is None or spend_ceiling_usd <= 0:
        findings.append({"id": "V2-COST-001", "severity": "critical", "finding": "positive hard USD spend ceiling is absent"})
    binding_report = protocol.validate_external_bindings(custody_root, packet_value)
    if not binding_report["valid"]:
        findings.append({"id": "V2-BINDING-001", "severity": "critical", "finding": "; ".join(binding_report["errors"])})
    if reviewer_receipt is None:
        findings.append({"id": "V2-REVIEW-001", "severity": "critical", "finding": "genuinely independent packet-bound signed ACCEPT is absent"})
    else:
        try:
            validate_signed_acceptance(reviewer_receipt, str(packet_value["packet_sha256"]))
        except protocol.ProtocolError as exc:
            findings.append({"id": "V2-REVIEW-002", "severity": "critical", "finding": str(exc)})
    value = {
        "protocol": protocol.PROTOCOL_ID,
        "state_slice": protocol.STATE_SLICE,
        "packet_sha256": packet_value["packet_sha256"],
        "reviewer_role": protocol.REVIEWER_ROLE,
        "verdict": "ACCEPT" if not findings else "REJECT",
        "assessment_authorized": False,
        "model_execution_authorized": False,
        "findings": findings,
    }
    return {**value, "review_sha256": protocol.digest_json(value)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--packet-output", type=Path, required=True)
    parser.add_argument("--node-receipt", type=Path, default=protocol.NODE_ALLOCATION_RECEIPT)
    parser.add_argument("--spend-ceiling-usd", type=float, default=protocol.HARD_SPEND_CEILING_USD)
    args = parser.parse_args()
    packet_value = packet(args.repository_root)
    node_receipt = None
    if args.node_receipt.is_file():
        loaded = protocol.strict_json(args.node_receipt)
        if not isinstance(loaded, dict):
            raise protocol.ProtocolError("node receipt is not an object")
        node_receipt = loaded
    review = static_review(
        packet_value,
        node_receipt=node_receipt,
        spend_ceiling_usd=args.spend_ceiling_usd,
        reviewer_receipt=None,
    )
    args.packet_output.parent.mkdir(parents=True, exist_ok=True)
    args.packet_output.write_text(json.dumps({"packet": packet_value, "review": review}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0 if review["verdict"] == "ACCEPT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
