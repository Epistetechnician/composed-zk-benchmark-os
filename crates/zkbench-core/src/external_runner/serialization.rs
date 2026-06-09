//! JSON serialization helpers for Phase H boundary artifacts.

use crate::error::{Result, ZkBenchError};

use super::artifact_capture::ArtifactCaptureContract;
use super::handoff::ManualHandoffBundle;
use super::import_bundle::SyntheticResultImportBundle;
use super::normalization::NormalizedExternalResultDraft;
use super::policy::ExternalRunnerPolicy;
use super::proposal::EvidenceAppendProposal;
use super::proposal_ledger::EvidenceAppendProposalLedger;
use super::provenance::ProvenanceContract;
use super::quarantine::QuarantineManifest;
use super::result_import::{ExternalResultCandidate, ExternalResultImportSchema};

/// Serialize an external-runner policy to deterministic pretty JSON.
pub fn serialize_external_runner_policy_json(policy: &ExternalRunnerPolicy) -> Result<String> {
    serde_json::to_string_pretty(policy).map_err(|error| {
        ZkBenchError::serialization("serialize_external_runner_policy_json", error.to_string())
    })
}

/// Deserialize an external-runner policy from JSON.
pub fn deserialize_external_runner_policy_json(json: &str) -> Result<ExternalRunnerPolicy> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("deserialize_external_runner_policy_json", error.to_string())
    })
}

/// Serialize a manual handoff bundle to deterministic pretty JSON.
pub fn serialize_manual_handoff_bundle_json(bundle: &ManualHandoffBundle) -> Result<String> {
    serde_json::to_string_pretty(bundle).map_err(|error| {
        ZkBenchError::serialization("serialize_manual_handoff_bundle_json", error.to_string())
    })
}

/// Deserialize a manual handoff bundle from JSON.
pub fn deserialize_manual_handoff_bundle_json(json: &str) -> Result<ManualHandoffBundle> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("deserialize_manual_handoff_bundle_json", error.to_string())
    })
}

/// Serialize an artifact capture contract to deterministic pretty JSON.
pub fn serialize_artifact_capture_contract_json(
    contract: &ArtifactCaptureContract,
) -> Result<String> {
    serde_json::to_string_pretty(contract).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_artifact_capture_contract_json",
            error.to_string(),
        )
    })
}

/// Deserialize an artifact capture contract from JSON.
pub fn deserialize_artifact_capture_contract_json(json: &str) -> Result<ArtifactCaptureContract> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_artifact_capture_contract_json",
            error.to_string(),
        )
    })
}

/// Serialize a provenance contract to deterministic pretty JSON.
pub fn serialize_provenance_contract_json(contract: &ProvenanceContract) -> Result<String> {
    serde_json::to_string_pretty(contract).map_err(|error| {
        ZkBenchError::serialization("serialize_provenance_contract_json", error.to_string())
    })
}

/// Deserialize a provenance contract from JSON.
pub fn deserialize_provenance_contract_json(json: &str) -> Result<ProvenanceContract> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("deserialize_provenance_contract_json", error.to_string())
    })
}

/// Serialize an external result import schema to deterministic pretty JSON.
pub fn serialize_external_result_import_schema_json(
    schema: &ExternalResultImportSchema,
) -> Result<String> {
    serde_json::to_string_pretty(schema).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_external_result_import_schema_json",
            error.to_string(),
        )
    })
}

/// Deserialize an external result import schema from JSON.
pub fn deserialize_external_result_import_schema_json(
    json: &str,
) -> Result<ExternalResultImportSchema> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_external_result_import_schema_json",
            error.to_string(),
        )
    })
}

/// Serialize an external result candidate to deterministic pretty JSON.
pub fn serialize_external_result_candidate_json(
    candidate: &ExternalResultCandidate,
) -> Result<String> {
    serde_json::to_string_pretty(candidate).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_external_result_candidate_json",
            error.to_string(),
        )
    })
}

/// Deserialize an external result candidate from JSON.
pub fn deserialize_external_result_candidate_json(json: &str) -> Result<ExternalResultCandidate> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_external_result_candidate_json",
            error.to_string(),
        )
    })
}

/// Serialize a quarantine manifest to deterministic pretty JSON.
pub fn serialize_quarantine_manifest_json(manifest: &QuarantineManifest) -> Result<String> {
    serde_json::to_string_pretty(manifest).map_err(|error| {
        ZkBenchError::serialization("serialize_quarantine_manifest_json", error.to_string())
    })
}

/// Deserialize a quarantine manifest from JSON.
pub fn deserialize_quarantine_manifest_json(json: &str) -> Result<QuarantineManifest> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("deserialize_quarantine_manifest_json", error.to_string())
    })
}

/// Serialize a synthetic result import bundle to deterministic pretty JSON.
pub fn serialize_synthetic_result_import_bundle_json(
    bundle: &SyntheticResultImportBundle,
) -> Result<String> {
    serde_json::to_string_pretty(bundle).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_synthetic_result_import_bundle_json",
            error.to_string(),
        )
    })
}

/// Deserialize a synthetic result import bundle from JSON.
pub fn deserialize_synthetic_result_import_bundle_json(
    json: &str,
) -> Result<SyntheticResultImportBundle> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_synthetic_result_import_bundle_json",
            error.to_string(),
        )
    })
}

/// Serialize a normalized external result draft to deterministic pretty JSON.
pub fn serialize_normalized_external_result_draft_json(
    draft: &NormalizedExternalResultDraft,
) -> Result<String> {
    serde_json::to_string_pretty(draft).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_normalized_external_result_draft_json",
            error.to_string(),
        )
    })
}

/// Deserialize a normalized external result draft from JSON.
pub fn deserialize_normalized_external_result_draft_json(
    json: &str,
) -> Result<NormalizedExternalResultDraft> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_normalized_external_result_draft_json",
            error.to_string(),
        )
    })
}

/// Serialize an evidence append proposal to deterministic pretty JSON.
pub fn serialize_evidence_append_proposal_json(
    proposal: &EvidenceAppendProposal,
) -> Result<String> {
    serde_json::to_string_pretty(proposal).map_err(|error| {
        ZkBenchError::serialization("serialize_evidence_append_proposal_json", error.to_string())
    })
}

/// Deserialize an evidence append proposal from JSON.
pub fn deserialize_evidence_append_proposal_json(json: &str) -> Result<EvidenceAppendProposal> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_evidence_append_proposal_json",
            error.to_string(),
        )
    })
}

/// Serialize an evidence append proposal ledger to deterministic pretty JSON.
pub fn serialize_evidence_append_proposal_ledger_json(
    ledger: &EvidenceAppendProposalLedger,
) -> Result<String> {
    serde_json::to_string_pretty(ledger).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_evidence_append_proposal_ledger_json",
            error.to_string(),
        )
    })
}

/// Deserialize an evidence append proposal ledger from JSON.
pub fn deserialize_evidence_append_proposal_ledger_json(
    json: &str,
) -> Result<EvidenceAppendProposalLedger> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_evidence_append_proposal_ledger_json",
            error.to_string(),
        )
    })
}
