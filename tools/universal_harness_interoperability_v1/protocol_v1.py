"""Define the universal harness interoperability contract.

State slice: ``universal-harness-interoperability-v1``.

This module declares protocol and transport bindings only. It does not spawn
agents, invoke MCP tools, open ACP/A2A sessions, call OpenSSH, access a
provider, or grant authority.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


STATE_SLICE = "universal-harness-interoperability-v1"
PROTOCOL_ID = "universal-harness-interoperability-v1"
PROTOCOL_SCHEMA_VERSION = f"{PROTOCOL_ID}-protocol-v1"
MANIFEST_SCHEMA_VERSION = f"{PROTOCOL_ID}-manifest-v1"
CLAIM_CEILING = "LocalDevelopmentUniversalHarnessInteroperabilityContract"

ROLES = (
    "controller",
    "client",
    "agent",
    "tool_server",
    "transport_adapter",
    "remote_node",
    "validator",
)
TRANSPORT_IDS = ("stdio", "streamable_http", "openssh_session", "openssh_sftp")
LIFECYCLE = (
    "discover",
    "negotiate",
    "propose",
    "admit",
    "execute",
    "observe",
    "complete",
    "reconcile",
)
ENVELOPE_FIELDS = (
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
)


class ProtocolError(ValueError):
    """Raised when the interoperability contract is invalid."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def _strict_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    _require(set(value) == expected, f"{label} schema")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in pairs:
        if key in result:
            raise ProtocolError(f"duplicate JSON key: {key}")
        result[key] = item
    return result


def load_json_bytes(raw: bytes) -> Any:
    """Parse strict UTF-8 JSON without duplicate keys or non-standard constants."""

    def reject_constant(value: str) -> Any:
        raise ProtocolError(f"non-standard JSON constant: {value}")

    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProtocolError("invalid UTF-8 JSON") from exc


def canonical_bytes(value: Any) -> bytes:
    """Return the deterministic JSON encoding used for contract digests."""

    try:
        encoded = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise ProtocolError("value is not canonical JSON") from exc
    return encoded.encode("utf-8")


def digest(value: Any) -> str:
    """Hash one canonical JSON value with SHA-256."""

    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _transport_spec() -> list[dict[str, Any]]:
    return [
        {
            "transport_id": "stdio",
            "layer": "local_process",
            "remote": False,
            "security_requirement": "parent_process_boundary",
            "supports_streaming": True,
        },
        {
            "transport_id": "streamable_http",
            "layer": "network",
            "remote": True,
            "security_requirement": "authenticated_tls_and_origin_validation",
            "supports_streaming": True,
        },
        {
            "transport_id": "openssh_session",
            "layer": "secure_remote_transport",
            "remote": True,
            "security_requirement": "verified_host_key_and_dedicated_account",
            "supports_streaming": True,
        },
        {
            "transport_id": "openssh_sftp",
            "layer": "secure_remote_file_transport",
            "remote": True,
            "security_requirement": "verified_host_key_and_dedicated_account",
            "supports_streaming": False,
        },
    ]


def _binding_spec() -> list[dict[str, Any]]:
    return [
        {
            "binding_id": "acp.agent_client.v1",
            "role_pair": ["client", "agent"],
            "wire": "json-rpc-2.0",
            "transport_ids": ["stdio"],
            "methods": [
                "initialize",
                "session/new",
                "session/prompt",
                "session/update",
                "session/request_permission",
                "session/cancel",
            ],
            "authority": "proposal_only",
        },
        {
            "binding_id": "mcp.tool_context.v1",
            "role_pair": ["agent", "tool_server"],
            "wire": "json-rpc-2.0",
            "transport_ids": ["stdio", "streamable_http"],
            "methods": ["initialize", "tools/list", "tools/call", "resources/read"],
            "authority": "proposal_only",
        },
        {
            "binding_id": "a2a.agent_delegate.v1",
            "role_pair": ["agent", "agent"],
            "wire": "a2a-task-model",
            "transport_ids": ["streamable_http"],
            "methods": ["agent-card", "task/send", "task/get", "task/cancel"],
            "authority": "proposal_only",
        },
        {
            "binding_id": "openssh.remote_transport.v1",
            "role_pair": ["transport_adapter", "remote_node"],
            "wire": "ssh-and-sftp",
            "transport_ids": ["openssh_session", "openssh_sftp"],
            "methods": ["exec", "session", "read", "write", "transfer"],
            "authority": "transport_only",
        },
    ]


def protocol_spec() -> dict[str, Any]:
    """Return the complete closed-world interoperability specification."""

    return {
        "identity": {
            "state_slice": STATE_SLICE,
            "protocol_id": PROTOCOL_ID,
            "schema_version": PROTOCOL_SCHEMA_VERSION,
            "claim_ceiling": CLAIM_CEILING,
            "execution_authorized": False,
            "assessment_open": False,
        },
        "roles": list(ROLES),
        "transports": _transport_spec(),
        "bindings": _binding_spec(),
        "lifecycle": list(LIFECYCLE),
        "required_envelope_fields": list(ENVELOPE_FIELDS),
        "capability_policy": {
            "default_effect": "deny",
            "discovery_grants_authority": False,
            "ssh_grants_authority": False,
            "tool_call_requires_admission": True,
            "delegation_requires_receipt": True,
            "replay_requires_unique_nonce": True,
            "egress_requires_allowlist": True,
            "validator_recomputes_aggregates": True,
        },
        "trust_zones": [
            {"zone_id": "controller", "trust": "policy_owner", "may_grant_authority": False},
            {"zone_id": "agent_runtime", "trust": "untrusted_proposer", "may_grant_authority": False},
            {"zone_id": "tool_server", "trust": "capability_provider", "may_grant_authority": False},
            {"zone_id": "remote_node", "trust": "external_execution_target", "may_grant_authority": False},
            {"zone_id": "validator", "trust": "independent_recomputation", "may_grant_authority": False},
        ],
        "artifact_policy": {
            "raw_payload_retention": "forbidden",
            "aggregate_only_publication": True,
            "external_custody_required": True,
            "overwrite_policy": "reject",
            "generated_artifacts_committed": False,
        },
        "observability": {
            "event_record": "redacted_digest_bound",
            "raw_payload": "not_recorded",
            "journal": "append_only_hash_chain",
        },
        "execution_boundary": {
            "model_execution_allowed": False,
            "provider_calls_allowed": False,
            "network_during_execution_allowed": False,
            "remote_ssh_execution_allowed": False,
            "credential_materialization_allowed": False,
            "accepted_evidence_writes_allowed": False,
            "authority_granted": False,
        },
        "anti_goals": [
            "protocol_binding_is_not_authority",
            "transport_reachability_is_not_identity",
            "tool_discovery_is_not_approval",
            "model_output_is_not_evidence",
            "local_replay_is_not_independent_validation",
            "ssh_access_is_not_remote_policy_enforcement",
        ],
    }


def validate_protocol_spec(value: Mapping[str, Any]) -> None:
    """Validate the compiler-owned closed-world protocol specification."""

    _strict_keys(
        value,
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
    _require(dict(value) == protocol_spec(), "protocol differs from closed-world specification")


def validate_manifest_shape(manifest: Mapping[str, Any]) -> None:
    """Validate the compiler-owned manifest shape before serialization."""

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
    _require(
        manifest["schema_version"] == MANIFEST_SCHEMA_VERSION
        and manifest["state_slice"] == STATE_SLICE
        and manifest["protocol_id"] == PROTOCOL_ID,
        "manifest identity",
    )
    _require(manifest["claim_ceiling"] == CLAIM_CEILING, "manifest claim ceiling")
    _require(manifest["execution_authorized"] is False and manifest["assessment_open"] is False, "manifest authority")
    _require(isinstance(manifest["source_identity"], list) and bool(manifest["source_identity"]), "source identity")
    _require(isinstance(manifest["protocol_sha256"], str) and len(manifest["protocol_sha256"]) == 64, "protocol digest")
    _require(isinstance(manifest["manifest_sha256"], str) and len(manifest["manifest_sha256"]) == 64, "manifest digest")
    _require(isinstance(manifest["protocol"], Mapping), "protocol object")
    validate_protocol_spec(manifest["protocol"])

