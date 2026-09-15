"""Independently validate a universal harness interoperability manifest.

State slice: ``universal-harness-interoperability-v1``.

This validator intentionally does not import the compiler. It recomputes
source identities, protocol digests, manifest digests, closed-world bindings,
and non-authorizing execution rules from its own constants.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import protocol_v1


STATE_SLICE = "universal-harness-interoperability-v1"
PROTOCOL_ID = "universal-harness-interoperability-v1"
PROTOCOL_SCHEMA_VERSION = f"{PROTOCOL_ID}-protocol-v1"
MANIFEST_SCHEMA_VERSION = f"{PROTOCOL_ID}-manifest-v1"
CLAIM_CEILING = "LocalDevelopmentUniversalHarnessInteroperabilityContract"
SOURCE_FILES = (
    "tools/universal_harness_interoperability_v1/__init__.py",
    "tools/universal_harness_interoperability_v1/protocol_v1.py",
    "tools/universal_harness_interoperability_v1/compiler_v1.py",
    "tools/universal_harness_interoperability_v1/validator_v1.py",
)
ROLES = ["controller", "client", "agent", "tool_server", "transport_adapter", "remote_node", "validator"]
TRANSPORT_IDS = ["stdio", "streamable_http", "openssh_session", "openssh_sftp"]
LIFECYCLE = ["discover", "negotiate", "propose", "admit", "execute", "observe", "complete", "reconcile"]
ENVELOPE_FIELDS = [
    "message_id",
    "correlation_id",
    "protocol_binding",
    "sender",
    "recipient",
    "capability_digest",
    "policy_digest",
    "artifact_digests",
    "created_at",
    "expires_at",
    "sequence",
    "parent_digest",
    "nonce",
]
BINDING_IDS = [
    "acp.agent_client.v1",
    "mcp.tool_context.v1",
    "a2a.agent_delegate.v1",
    "openssh.remote_transport.v1",
]
HEX_DIGEST = set("0123456789abcdef")


class ValidationError(ValueError):
    """Raised when a manifest violates the independent contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _strict_keys(value: Mapping[str, Any], expected: Sequence[str] | set[str], label: str) -> None:
    _require(set(value) == set(expected), f"{label} schema")


def _canonical_bytes(value: Any) -> bytes:
    try:
        encoded = protocol_v1.canonical_bytes(value)
    except protocol_v1.ProtocolError as exc:
        raise ValidationError("non-canonical JSON") from exc
    return encoded


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX_DIGEST


def _source_identity(root: Path) -> list[dict[str, str]]:
    result = []
    for relative in SOURCE_FILES:
        path = root / Path(relative)
        _require(path.is_file() and not path.is_symlink(), f"source file unavailable: {relative}")
        result.append({"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return result


def _validate_protocol(protocol: Mapping[str, Any]) -> None:
    _strict_keys(
        protocol,
        {
            "identity",
            "roles",
            "transports",
            "bindings",
            "lifecycle",
            "required_envelope_fields",
            "capability_policy",
            "trust_zones",
            "artifact_policy",
            "observability",
            "execution_boundary",
            "anti_goals",
        },
        "protocol",
    )
    identity = protocol["identity"]
    _require(isinstance(identity, Mapping), "protocol identity object")
    _strict_keys(identity, {"state_slice", "protocol_id", "schema_version", "claim_ceiling", "execution_authorized", "assessment_open"}, "protocol identity")
    _require(
        dict(identity)
        == {
            "state_slice": STATE_SLICE,
            "protocol_id": PROTOCOL_ID,
            "schema_version": PROTOCOL_SCHEMA_VERSION,
            "claim_ceiling": CLAIM_CEILING,
            "execution_authorized": False,
            "assessment_open": False,
        },
        "protocol identity values",
    )
    _require(protocol["roles"] == ROLES, "role roster")
    _require(protocol["lifecycle"] == LIFECYCLE, "lifecycle")
    _require(protocol["required_envelope_fields"] == ENVELOPE_FIELDS, "envelope fields")
    _validate_transports(protocol["transports"])
    _validate_bindings(protocol["bindings"])
    _validate_policy(protocol)


def _validate_transports(transports: Any) -> None:
    _require(isinstance(transports, list), "transport roster")
    _require(all(isinstance(item, Mapping) for item in transports), "transport object")
    _require([item["transport_id"] for item in transports] == TRANSPORT_IDS, "transport roster")
    for item in transports:
        _require(isinstance(item, Mapping), "transport object")
        _strict_keys(item, {"transport_id", "layer", "remote", "security_requirement", "supports_streaming"}, "transport")
        _require(isinstance(item["transport_id"], str) and item["transport_id"] in TRANSPORT_IDS, "transport id")
        _require(isinstance(item["remote"], bool) and isinstance(item["supports_streaming"], bool), "transport flags")
        if item["transport_id"] == "stdio":
            _require(item["remote"] is False and item["security_requirement"] == "parent_process_boundary", "stdio transport")
        elif item["transport_id"].startswith("openssh"):
            _require(item["remote"] is True and item["security_requirement"] == "verified_host_key_and_dedicated_account", "OpenSSH transport security")
        else:
            _require(item["remote"] is True and item["security_requirement"] == "authenticated_tls_and_origin_validation", "HTTP transport security")


def _validate_bindings(bindings: Any) -> None:
    _require(isinstance(bindings, list), "binding roster")
    _require(all(isinstance(item, Mapping) for item in bindings), "binding object")
    _require([item["binding_id"] for item in bindings] == BINDING_IDS, "binding roster")
    for item in bindings:
        _require(isinstance(item, Mapping), "binding object")
        _strict_keys(item, {"binding_id", "role_pair", "wire", "transport_ids", "methods", "authority"}, "binding")
        _require(item["binding_id"] in BINDING_IDS, "binding id")
        _require(isinstance(item["role_pair"], list) and len(item["role_pair"]) == 2, "binding role pair")
        _require(all(role in ROLES for role in item["role_pair"]), "binding role")
        _require(isinstance(item["transport_ids"], list) and item["transport_ids"] and all(transport in TRANSPORT_IDS for transport in item["transport_ids"]), "binding transport")
        _require(isinstance(item["methods"], list) and item["methods"] and all(isinstance(method, str) and method for method in item["methods"]), "binding methods")
        _require(item["authority"] in {"proposal_only", "transport_only"}, "binding authority")
    acp = bindings[0]
    _require(acp["role_pair"] == ["client", "agent"] and acp["wire"] == "json-rpc-2.0" and acp["transport_ids"] == ["stdio"] and acp["authority"] == "proposal_only", "ACP binding")
    mcp = bindings[1]
    _require(mcp["role_pair"] == ["agent", "tool_server"] and mcp["wire"] == "json-rpc-2.0" and mcp["transport_ids"] == ["stdio", "streamable_http"] and mcp["authority"] == "proposal_only", "MCP binding")
    a2a = bindings[2]
    _require(a2a["role_pair"] == ["agent", "agent"] and a2a["wire"] == "a2a-task-model" and a2a["transport_ids"] == ["streamable_http"] and a2a["authority"] == "proposal_only", "A2A binding")
    ssh = bindings[3]
    _require(ssh["role_pair"] == ["transport_adapter", "remote_node"] and ssh["wire"] == "ssh-and-sftp" and ssh["transport_ids"] == ["openssh_session", "openssh_sftp"] and ssh["authority"] == "transport_only", "OpenSSH binding")


def _validate_policy(protocol: Mapping[str, Any]) -> None:
    policy = protocol["capability_policy"]
    _require(isinstance(policy, Mapping), "capability policy object")
    _strict_keys(policy, {"default_effect", "discovery_grants_authority", "ssh_grants_authority", "tool_call_requires_admission", "delegation_requires_receipt", "replay_requires_unique_nonce", "egress_requires_allowlist", "validator_recomputes_aggregates"}, "capability policy")
    _require(policy["default_effect"] == "deny", "capability default")
    for field in ("discovery_grants_authority", "ssh_grants_authority"):
        _require(policy[field] is False, f"capability escalation: {field}")
    for field in ("tool_call_requires_admission", "delegation_requires_receipt", "replay_requires_unique_nonce", "egress_requires_allowlist", "validator_recomputes_aggregates"):
        _require(policy[field] is True, f"capability control missing: {field}")
    boundary = protocol["execution_boundary"]
    _require(isinstance(boundary, Mapping), "execution boundary object")
    _strict_keys(boundary, {"model_execution_allowed", "provider_calls_allowed", "network_during_execution_allowed", "remote_ssh_execution_allowed", "credential_materialization_allowed", "accepted_evidence_writes_allowed", "authority_granted"}, "execution boundary")
    _require(all(value is False for value in boundary.values()), "execution boundary escalation")
    artifacts = protocol["artifact_policy"]
    _require(isinstance(artifacts, Mapping), "artifact policy object")
    _strict_keys(artifacts, {"raw_payload_retention", "aggregate_only_publication", "external_custody_required", "overwrite_policy", "generated_artifacts_committed"}, "artifact policy")
    _require(dict(artifacts) == {"raw_payload_retention": "forbidden", "aggregate_only_publication": True, "external_custody_required": True, "overwrite_policy": "reject", "generated_artifacts_committed": False}, "artifact policy values")
    observability = protocol["observability"]
    _require(isinstance(observability, Mapping), "observability object")
    _strict_keys(observability, {"event_record", "raw_payload", "journal"}, "observability")
    _require(dict(observability) == {"event_record": "redacted_digest_bound", "raw_payload": "not_recorded", "journal": "append_only_hash_chain"}, "observability values")
    zones = protocol["trust_zones"]
    _require(isinstance(zones, list) and bool(zones), "trust zones")
    for zone in zones:
        _require(isinstance(zone, Mapping), "trust zone object")
        _strict_keys(zone, {"zone_id", "trust", "may_grant_authority"}, "trust zone")
        _require(zone["may_grant_authority"] is False, "trust zone authority")
    _require(protocol["anti_goals"] == ["protocol_binding_is_not_authority", "transport_reachability_is_not_identity", "tool_discovery_is_not_approval", "model_output_is_not_evidence", "local_replay_is_not_independent_validation", "ssh_access_is_not_remote_policy_enforcement"], "anti-goals")


def validate_manifest(manifest: Mapping[str, Any], *, root: Path | None = None) -> None:
    """Validate one manifest without importing the compiler."""

    _strict_keys(
        manifest,
        {
            "schema_version",
            "state_slice",
            "protocol_id",
            "claim_ceiling",
            "execution_authorized",
            "assessment_open",
            "source_identity",
            "protocol_sha256",
            "protocol",
            "manifest_sha256",
        },
        "manifest",
    )
    _require(manifest["schema_version"] == MANIFEST_SCHEMA_VERSION and manifest["state_slice"] == STATE_SLICE and manifest["protocol_id"] == PROTOCOL_ID, "manifest identity")
    _require(manifest["claim_ceiling"] == CLAIM_CEILING and manifest["execution_authorized"] is False and manifest["assessment_open"] is False, "manifest boundary")
    _require(isinstance(manifest["source_identity"], list) and manifest["source_identity"], "source identity")
    _require(root is not None, "validator repository root")
    _require(manifest["source_identity"] == _source_identity(root), "source identity digest")
    _require(_is_digest(manifest["protocol_sha256"]) and _is_digest(manifest["manifest_sha256"]), "manifest digests")
    protocol = manifest["protocol"]
    _require(isinstance(protocol, Mapping), "manifest protocol")
    _validate_protocol(protocol)
    _require(_digest(protocol) == manifest["protocol_sha256"], "protocol digest recomputation")
    body = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    _require(_digest(body) == manifest["manifest_sha256"], "manifest digest recomputation")


def main() -> int:
    parser = argparse.ArgumentParser(description="validate a universal harness interoperability manifest")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    manifest = protocol_v1.load_json_bytes(args.manifest.read_bytes())
    _require(isinstance(manifest, Mapping), "manifest object")
    validate_manifest(manifest, root=args.root)
    print(json.dumps({"state_slice": STATE_SLICE, "valid": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
