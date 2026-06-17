//! Convenience exports for users of the Level 1 foundation API.

pub use crate::adapters::{
    build_default_zk_harness_adapter_manifest, build_manual_handoff_bundle_from_zk_harness_plan,
    build_zk_harness_dry_run_plan_from_pack, build_zk_harness_manual_handoff_bundle,
    local_json_capabilities, serialize_zk_harness_dry_run_plan_json,
    validate_zk_harness_dry_run_plan, AdapterCapabilitySet, BackendAdapter, BackendTarget,
    LocalJsonAdapter, LocalJsonReplaySummary, ZkHarnessAdapterManifest, ZkHarnessDryRunPlan,
    ZkHarnessDryRunPlanner, ZkHarnessExecutionPolicy, ZkHarnessManualHandoffBundle,
    ZkHarnessMetricMapping, ZkHarnessPackMapping, ZkHarnessPlannedCommand,
};
pub use crate::dsl::{
    evaluate_trace, lower_to_ir, parse_yaml_ast, parse_yaml_spec, ActionSpec, GuardSpec,
    MachineSpec, OracleOutcome, ParsedAst, SemanticIr, SurfaceSpec, TraceSpec,
};
pub use crate::error::{Result, ZkBenchError};
pub use crate::evidence::{
    build_default_evidence_acceptance_policy, build_default_evidence_review_checklist,
    check_level2_eligibility, classify_result, compute_artifact_digest,
    create_evidence_append_preview, create_evidence_record_candidate,
    guard_claim_boundary_escalation, review_evidence_append_proposal,
    validate_evidence_append_preview, validate_evidence_record_candidate,
    validate_evidence_review_decision, ArtifactDigest, ArtifactKind, ArtifactRef, ArtifactRole,
    BackendOutcome, ClaimBoundary, EvidenceAcceptancePolicy, EvidenceAppendPreview, EvidenceLedger,
    EvidenceRecord, EvidenceRecordCandidate, EvidenceReviewDecision, EvidenceReviewDecisionKind,
    EvidenceReviewerRole, ExpectedVerdict, Level2EligibilityChecker, Level2EligibilityReport,
    ResultClassification,
};
pub use crate::external_runner::{
    build_default_artifact_capture_contract, build_default_external_result_import_schema,
    build_default_external_runner_policy, build_default_provenance_contract,
    create_evidence_append_proposal, import_synthetic_result_candidate_json,
    quarantine_external_result_candidate, quarantine_synthetic_result_candidate,
    serialize_evidence_append_proposal_json, serialize_evidence_append_proposal_ledger_json,
    serialize_external_result_candidate_json, serialize_manual_handoff_bundle_json,
    serialize_synthetic_result_import_bundle_json, validate_artifact_capture_contract,
    validate_evidence_append_proposal, validate_external_result_candidate,
    validate_external_runner_policy, validate_manual_handoff_bundle,
    validate_synthetic_result_candidate, ArtifactCaptureContract, ArtifactDigestValidation,
    EvidenceAppendProposal, EvidenceAppendProposalLedger, ExpectedArtifact, ExternalExecutionMode,
    ExternalMetricCandidate, ExternalMetricUnit, ExternalResultCandidate,
    ExternalResultImportSchema, ExternalResultStatus, ExternalRunnerPolicy, ManualHandoffBundle,
    ManualHandoffStep, MetricCandidateValidation, NormalizedExternalResultDraft,
    ProvenanceContract, ProvenanceContractValidation, QuarantineManifest,
    ResultCandidateArtifactResolver, SyntheticImportValidation, SyntheticResultImportBundle,
    SyntheticResultImporter,
};
pub use crate::generator::{
    evaluate_generated_instance, generate_family, generate_instance, BenchmarkFamily,
    BenchmarkInstance, DeterministicGenerator, FamilyKind, GeneratedBenchmarkFamily,
    GeneratedBenchmarkInstance, GeneratorConfig, GeneratorLimits, InstanceParams,
};
pub use crate::mutation::{
    apply_default_mutations, apply_mutation_pass, evaluate_mutated_instance, BadCountersPass,
    CorruptedGuardsPass, MissingConstraintsPass, MutatedBenchmarkInstance, MutationClass,
    MutationEngine, MutationPass, MutationSafetyClass, MutationSpec, MutationVariant,
};
pub use crate::pack::{BenchmarkPackManifest, BenchmarkPackReader, BenchmarkPackWriter};
pub use crate::recursion::{
    build_recursion_adapter_manual_handoff_bundle, compute_recursion_envelope_digest_chain_root,
    validate_recursion_adapter_manual_handoff_bundle, validate_recursion_adapter_preparation_plan,
    validate_recursion_envelope_candidate, RecursionAdapterManualHandoffBundle,
    RecursionAdapterManualHandoffMapping, RecursionAdapterPreparationArtifact,
    RecursionAdapterPreparationArtifactRole, RecursionAdapterPreparationIssueKind,
    RecursionAdapterPreparationPlan, RecursionAdapterPreparationTarget,
    RecursionAdapterPreparationValidation, RecursionEnvelopeCandidate, RecursionEnvelopeInputKind,
    RecursionEnvelopeInputRef, RecursionEnvelopeMetric, RecursionEnvelopeMetricKind,
    RecursionEnvelopeValidation, RecursionEnvelopeValidationIssueKind, RecursionEnvelopeVersion,
    RecursionVerifierAcceptanceStatus,
};
pub use crate::replay::{
    build_local_replay_manifest_for_instance, build_local_replay_manifest_for_mutation,
    run_local_replay, ReplayManifest, ReplayResult, ReplayTraceResult,
};
pub use crate::scoring::{
    score_report_from_evidence, score_report_from_local_mutation_evidence, validate_score_report,
    LocalMutationEvidenceSummary, ScoreReport, ScoreReportValidation, ScoreReportValidationIssue,
};
pub use crate::soak::{
    aggregate_soak_health_reports, build_regression_soak_config, build_smoke_soak_config,
    build_soak_report_bundle, extract_failure_corpus, plan_soak_shards, resume_local_soak_shard,
    run_local_soak_shard, validate_failure_corpus_index, validate_soak_health_report,
    validate_soak_report_bundle, validate_soak_run_config, validate_soak_shard_manifest,
    validate_soak_shard_summary, validate_soak_telemetry_report, FailureCorpus, FailureCorpusEntry,
    FailureCorpusIndex, FailureCorpusKind, FailureReproductionManifest, LocalSoakRunner,
    LocalSoakRunnerConfig, MockTelemetryClock, SoakArtifactLayout, SoakCaseResult, SoakCaseStatus,
    SoakHealthReport, SoakHealthStatus, SoakLimits, SoakOutputPolicy, SoakReportBundle,
    SoakRunConfig, SoakRunProfile, SoakRunResult, SoakRunnerErrorPolicy, SoakShardCheckpoint,
    SoakShardId, SoakShardManifest, SoakShardPlan, SoakShardPlanner, SoakTelemetryCounters,
    SoakTelemetryDurations, SoakTelemetryReport, SystemTelemetryClock,
};
pub use crate::value::{FieldVisibility, Value, ValueType};
