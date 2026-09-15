"""Hermetic tests for the universal harness interoperability contract.

State slice: ``universal-harness-interoperability-v1``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.universal_harness_interoperability_v1 import compiler_v1, protocol_v1, validator_v1


ROOT = Path(__file__).resolve().parents[3]


def test_compiled_manifest_passes_independent_validation() -> None:
    manifest = compiler_v1.compile_manifest()
    validator_v1.validate_manifest(manifest, root=ROOT)
    assert manifest["execution_authorized"] is False
    assert manifest["assessment_open"] is False


def test_protocol_binds_acp_mcp_a2a_and_openssh_without_authority() -> None:
    bindings = protocol_v1.protocol_spec()["bindings"]
    assert [binding["binding_id"] for binding in bindings] == [
        "acp.agent_client.v1",
        "mcp.tool_context.v1",
        "a2a.agent_delegate.v1",
        "openssh.remote_transport.v1",
    ]
    assert all(binding["authority"] in {"proposal_only", "transport_only"} for binding in bindings)
    assert protocol_v1.protocol_spec()["execution_boundary"]["authority_granted"] is False


def test_duplicate_json_keys_are_rejected() -> None:
    with pytest.raises(protocol_v1.ProtocolError, match="duplicate JSON key"):
        protocol_v1.load_json_bytes(b'{"schema_version":"one","schema_version":"two"}')


def test_unknown_binding_is_rejected() -> None:
    manifest = compiler_v1.compile_manifest()
    manifest["protocol"]["bindings"][0]["binding_id"] = "unknown.v1"
    manifest["protocol_sha256"] = protocol_v1.digest(manifest["protocol"])
    manifest["manifest_sha256"] = protocol_v1.digest({key: value for key, value in manifest.items() if key != "manifest_sha256"})

    with pytest.raises(validator_v1.ValidationError, match="binding roster"):
        validator_v1.validate_manifest(manifest, root=ROOT)


def test_transport_mismatch_is_rejected() -> None:
    manifest = compiler_v1.compile_manifest()
    manifest["protocol"]["bindings"][3]["transport_ids"] = ["stdio"]
    manifest["protocol_sha256"] = protocol_v1.digest(manifest["protocol"])
    manifest["manifest_sha256"] = protocol_v1.digest({key: value for key, value in manifest.items() if key != "manifest_sha256"})

    with pytest.raises(validator_v1.ValidationError, match="OpenSSH binding"):
        validator_v1.validate_manifest(manifest, root=ROOT)


def test_non_object_transport_and_binding_entries_are_rejected() -> None:
    manifest = compiler_v1.compile_manifest()
    manifest["protocol"]["transports"][0] = "stdio"
    manifest["protocol_sha256"] = protocol_v1.digest(manifest["protocol"])
    manifest["manifest_sha256"] = protocol_v1.digest({key: value for key, value in manifest.items() if key != "manifest_sha256"})
    with pytest.raises(validator_v1.ValidationError, match="transport object"):
        validator_v1.validate_manifest(manifest, root=ROOT)

    manifest = compiler_v1.compile_manifest()
    manifest["protocol"]["bindings"][0] = "acp.agent_client.v1"
    manifest["protocol_sha256"] = protocol_v1.digest(manifest["protocol"])
    manifest["manifest_sha256"] = protocol_v1.digest({key: value for key, value in manifest.items() if key != "manifest_sha256"})
    with pytest.raises(validator_v1.ValidationError, match="binding object"):
        validator_v1.validate_manifest(manifest, root=ROOT)


def test_authority_escalation_is_rejected_even_when_digests_are_recomputed() -> None:
    manifest = compiler_v1.compile_manifest()
    manifest["protocol"]["execution_boundary"]["remote_ssh_execution_allowed"] = True
    manifest["protocol_sha256"] = protocol_v1.digest(manifest["protocol"])
    manifest["manifest_sha256"] = protocol_v1.digest({key: value for key, value in manifest.items() if key != "manifest_sha256"})

    with pytest.raises(validator_v1.ValidationError, match="execution boundary escalation"):
        validator_v1.validate_manifest(manifest, root=ROOT)


def test_ssh_authority_escalation_is_rejected() -> None:
    manifest = compiler_v1.compile_manifest()
    manifest["protocol"]["bindings"][3]["authority"] = "proposal_only"
    manifest["protocol_sha256"] = protocol_v1.digest(manifest["protocol"])
    manifest["manifest_sha256"] = protocol_v1.digest({key: value for key, value in manifest.items() if key != "manifest_sha256"})

    with pytest.raises(validator_v1.ValidationError, match="OpenSSH binding"):
        validator_v1.validate_manifest(manifest, root=ROOT)


def test_source_identity_and_manifest_digest_tampering_are_rejected() -> None:
    manifest = compiler_v1.compile_manifest()
    manifest["source_identity"][0]["sha256"] = "0" * 64
    with pytest.raises(validator_v1.ValidationError, match="source identity digest"):
        validator_v1.validate_manifest(manifest, root=ROOT)

    manifest = compiler_v1.compile_manifest()
    manifest["manifest_sha256"] = "0" * 64
    with pytest.raises(validator_v1.ValidationError, match="manifest digest recomputation"):
        validator_v1.validate_manifest(manifest, root=ROOT)


def test_manifest_writer_refuses_overwrite(tmp_path: Path) -> None:
    output = tmp_path / "manifest.json"
    compiler_v1.write_manifest(compiler_v1.compile_manifest(), output)
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        compiler_v1.write_manifest(compiler_v1.compile_manifest(), output)
