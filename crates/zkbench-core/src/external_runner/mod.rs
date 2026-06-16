//! External-runner boundary, manual handoff, artifact capture, provenance,
//! result import, and quarantine primitives.
//!
//! Phase H is inert by design: external execution is disabled by default,
//! manual handoff bundles are not benchmark results, and result import
//! candidates remain quarantined or pending review until future validation.

pub mod artifact_capture;
pub mod handoff;
pub mod import_bundle;
pub mod importer;
pub mod level2_eligibility;
pub mod normalization;
pub mod policy;
pub mod proposal;
pub mod proposal_ledger;
pub mod proposal_review;
pub mod provenance;
pub mod quarantine;
pub mod result_import;
pub mod review;
pub mod serialization;
pub mod synthetic;
pub mod validation;

pub use artifact_capture::{
    build_default_artifact_capture_contract, validate_artifact_capture_contract,
    ArtifactCaptureContract, ArtifactCaptureContractId, ArtifactCaptureContractVersion,
    ArtifactCaptureRequirement, CapturedArtifactMetadata, CapturedArtifactValidation,
    CapturedArtifactValidationIssue, ExpectedArtifact, ExpectedArtifactFormat,
    ExpectedArtifactRole,
};
pub use handoff::{
    valid_manual_handoff_step_validation, validate_manual_handoff_bundle, ManualHandoffBundle,
    ManualHandoffBundleId, ManualHandoffBundleVersion, ManualHandoffExport,
    ManualHandoffInstruction, ManualHandoffStep, ManualHandoffStepKind, ManualHandoffSubject,
    ManualHandoffValidation, ManualHandoffValidationIssue,
};
pub use import_bundle::{
    SyntheticResultImportBundle, SyntheticResultImportBundleId, SyntheticResultImportBundleVersion,
    SyntheticResultImportReport, SyntheticValidationIssueCount,
};
pub use importer::{
    import_synthetic_result_candidate_json, validate_synthetic_result_candidate,
    validate_synthetic_result_candidate_with_config, ArtifactDigestValidation,
    ClaimBoundaryValidation, FormalClaimDetection, MetricCandidateValidation,
    OfficialClaimDetection, ProvenanceContractValidation, ResultCandidateArtifactLookup,
    ResultCandidateArtifactResolver, ResultCandidateSource, ResultCandidateSourceKind,
    SoundnessClaimDetection, SyntheticImportValidation, SyntheticImportValidationIssue,
    SyntheticImportValidationIssueKind, SyntheticResultImportConfig, SyntheticResultImporter,
};
pub use level2_eligibility::{
    check_level2_eligibility, deserialize_level2_eligibility_report_json,
    serialize_level2_eligibility_report_json, Level2EligibilityBlockingReason,
    Level2EligibilityChecker, Level2EligibilityFinding, Level2EligibilityReport,
    Level2EligibilityRequirement, Level2EligibilityStatus,
};
pub use normalization::{
    normalize_synthetic_result_candidate, NormalizationReport, NormalizationWarning,
    NormalizedArtifactRef, NormalizedExternalResultDraft, NormalizedExternalResultDraftId,
    NormalizedExternalResultDraftStatus, NormalizedMetricDraft, NormalizedProvenanceDraft,
};
pub use policy::{
    build_default_external_runner_policy, validate_external_runner_policy,
    ExternalClaimBoundaryPolicy, ExternalEnvironmentPolicy, ExternalExecutionGate,
    ExternalExecutionMode, ExternalExecutionReviewStatus, ExternalNetworkPolicy,
    ExternalPathPolicy, ExternalResultPolicy, ExternalRunnerPolicy, ExternalRunnerPolicyId,
    ExternalRunnerPolicyVersion, ExternalToolAllowlist,
};
pub use proposal::{
    create_evidence_append_proposal, validate_evidence_append_proposal, EvidenceAppendProposal,
    EvidenceAppendProposalId, EvidenceAppendProposalKind, EvidenceAppendProposalReviewState,
    EvidenceAppendProposalStatus, EvidenceAppendProposalValidation,
    EvidenceAppendProposalValidationIssue, EvidenceAppendProposalVersion,
};
pub use proposal_ledger::{
    EvidenceAppendProposalDigest, EvidenceAppendProposalLedger, EvidenceAppendProposalLedgerEntry,
    EvidenceAppendProposalLedgerSummary, EvidenceAppendProposalLedgerSummaryCount,
    EvidenceAppendProposalLedgerValidation, EvidenceAppendProposalLedgerValidationIssue,
    EvidenceAppendProposalLedgerVersion,
};
pub use proposal_review::{
    build_default_evidence_acceptance_policy, create_evidence_append_preview,
    create_evidence_record_candidate, deserialize_evidence_acceptance_policy_json,
    deserialize_evidence_append_preview_json, deserialize_evidence_record_candidate_json,
    serialize_evidence_acceptance_policy_json, serialize_evidence_append_preview_json,
    serialize_evidence_record_candidate_json, validate_evidence_acceptance_policy,
    validate_evidence_append_preview, validate_evidence_record_candidate,
    EvidenceAcceptanceBlockingReason, EvidenceAcceptancePolicy, EvidenceAcceptancePolicyId,
    EvidenceAcceptancePolicyMode, EvidenceAcceptancePolicyVersion, EvidenceAcceptanceRule,
    EvidenceAcceptanceRuleResult, EvidenceAcceptanceValidation, EvidenceAcceptanceValidationIssue,
    EvidenceAppendPreview, EvidenceAppendPreviewId, EvidenceAppendPreviewIssueKind,
    EvidenceAppendPreviewStatus, EvidenceAppendPreviewValidation,
    EvidenceAppendPreviewValidationIssue, EvidenceAppendPreviewVersion,
    EvidenceLedgerAppendPreviewEntry, EvidenceLedgerAppendTransactionPreview,
    EvidenceRecordCandidate, EvidenceRecordCandidateId, EvidenceRecordCandidateIssueKind,
    EvidenceRecordCandidateKind, EvidenceRecordCandidateSource, EvidenceRecordCandidateStatus,
    EvidenceRecordCandidateValidation, EvidenceRecordCandidateValidationIssue,
    EvidenceRecordCandidateVersion,
};
pub use provenance::{
    build_default_provenance_contract, required_provenance_fields,
    validate_external_run_provenance_draft, validate_provenance_contract, EnvironmentProvenance,
    ExternalRunProvenanceDraft, ExternalToolProvenance, OperatorProvenance, ProvenanceContract,
    ProvenanceFieldRequirement, ProvenanceValidation, ProvenanceValidationIssue,
    RequiredProvenanceField, SourceProvenance,
};
pub use quarantine::{
    quarantine_external_result_candidate, validate_quarantine_manifest, QuarantineEntry,
    QuarantineManifest, QuarantineReason, QuarantineStatus, QuarantineValidation,
    QuarantineValidationIssue,
};
pub use result_import::{
    build_default_external_result_import_schema, external_result_quarantine_record,
    validate_external_result_candidate, validate_external_result_candidate_with_schema,
    validate_external_result_import_schema, ExternalMetricCandidate, ExternalMetricUnit,
    ExternalResultCandidate, ExternalResultCandidateId, ExternalResultImportPolicy,
    ExternalResultImportSchema, ExternalResultImportSchemaId, ExternalResultQuarantineRecord,
    ExternalResultStatus, ExternalResultValidation, ExternalResultValidationIssue,
};
pub use review::{
    build_default_evidence_review_checklist, deserialize_evidence_review_checklist_json,
    deserialize_evidence_review_decision_json, review_evidence_append_proposal,
    serialize_evidence_review_checklist_json, serialize_evidence_review_decision_json,
    validate_evidence_review_decision, EvidenceReviewChecklist, EvidenceReviewChecklistItem,
    EvidenceReviewDecision, EvidenceReviewDecisionId, EvidenceReviewDecisionKind,
    EvidenceReviewDecisionStatus, EvidenceReviewDecisionVersion, EvidenceReviewFinding,
    EvidenceReviewFindingSeverity, EvidenceReviewPolicy, EvidenceReviewReport,
    EvidenceReviewRequirement, EvidenceReviewerRole,
};
pub use serialization::{
    deserialize_artifact_capture_contract_json, deserialize_evidence_append_proposal_json,
    deserialize_evidence_append_proposal_ledger_json, deserialize_external_result_candidate_json,
    deserialize_external_result_import_schema_json, deserialize_external_runner_policy_json,
    deserialize_manual_handoff_bundle_json, deserialize_normalized_external_result_draft_json,
    deserialize_provenance_contract_json, deserialize_quarantine_manifest_json,
    deserialize_synthetic_result_import_bundle_json, serialize_artifact_capture_contract_json,
    serialize_evidence_append_proposal_json, serialize_evidence_append_proposal_ledger_json,
    serialize_external_result_candidate_json, serialize_external_result_import_schema_json,
    serialize_external_runner_policy_json, serialize_manual_handoff_bundle_json,
    serialize_normalized_external_result_draft_json, serialize_provenance_contract_json,
    serialize_quarantine_manifest_json, serialize_synthetic_result_import_bundle_json,
};
pub use synthetic::{quarantine_synthetic_result_candidate, PHASE_I_SYNTHETIC_CLAIM_BOUNDARY};
pub use validation::{
    contains_forbidden_claim_text, contains_formal_claim_text, contains_official_claim_text,
    contains_rejected_path, contains_shell_payload, contains_soundness_claim_text,
    phase_h_actual_claim_allowed, phase_h_design_artifact_claim_allowed, ExternalValidationIssue,
    ExternalValidationIssueSeverity,
};
