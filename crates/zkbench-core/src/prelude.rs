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
    audit_oracle_completeness, evaluate_trace, lower_to_ir, parse_yaml_ast, parse_yaml_spec,
    ActionSpec, GuardSpec, MachineSpec, OracleCompletenessAudit, OracleCompletenessConstruct,
    OracleCompletenessConstructKind, OracleCompletenessLabel, OracleOutcome, ParsedAst, SemanticIr,
    SurfaceSpec, TraceSpec,
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
pub use crate::formal::{
    derive_formal_property_assertion_template, mandatory_cross_product_nonclaims,
    mandatory_lane_outcome_nonclaims, mutation_class_formal_stress, FormalLane, FormalLaneError,
    FormalLaneOutcome, FormalLaneProof, FormalLaneProofStatus, FormalPropertyAssertion,
    FormalPropertyScope, FormalPropertyScopeKind, FormalVerifier, MutationFormalStressProfile,
    NoopFormalVerifier,
};
pub use crate::generator::{
    evaluate_generated_instance, generate_family, generate_instance, BenchmarkFamily,
    BenchmarkInstance, DeterministicGenerator, FamilyKind, GeneratedBenchmarkFamily,
    GeneratedBenchmarkInstance, GeneratorConfig, GeneratorLimits, InstanceParams,
};
pub use crate::local_artifact_campaign::{
    build_local_artifact_campaign_input_from_phase_u_output, read_local_artifact_campaign_outputs,
    render_local_artifact_campaign_markdown, required_local_artifact_campaign_limitations,
    validate_local_artifact_campaign_manifest, write_local_artifact_campaign_outputs,
    LocalArtifactCampaignInputKind, LocalArtifactCampaignInputRef, LocalArtifactCampaignManifest,
    LocalArtifactCampaignOutput, LocalArtifactCampaignRetentionPolicy,
    LOCAL_ARTIFACT_CAMPAIGN_MANIFEST_PATH, LOCAL_ARTIFACT_CAMPAIGN_MARKDOWN_PATH,
    LOCAL_ARTIFACT_CAMPAIGN_VALIDATION_PATH,
};
pub use crate::local_benchmark_artifact::{
    compute_local_benchmark_artifact_manifest_digest, read_local_benchmark_artifact_outputs,
    render_local_benchmark_artifact_markdown, validate_local_benchmark_artifact_manifest,
    write_local_benchmark_artifact_outputs, LocalBenchmarkArtifactInputKind,
    LocalBenchmarkArtifactInputRef, LocalBenchmarkArtifactManifest, LocalBenchmarkArtifactOutput,
    LOCAL_BENCHMARK_ARTIFACT_MANIFEST_PATH, LOCAL_BENCHMARK_ARTIFACT_MARKDOWN_PATH,
};
pub use crate::mutation::{
    apply_default_mutations, apply_mutation_for_class, apply_mutation_pass,
    evaluate_mutated_instance, BadCountersPass, CorruptedGuardsPass, InvalidUnrollBoundsPass,
    InvariantStrengtheningPass, InvariantWeakeningPass, MissingConstraintsPass,
    MutatedBenchmarkInstance, MutationClass, MutationEngine, MutationPass, MutationSafetyClass,
    MutationSpec, MutationVariant, NondeterministicTransitionInjectionPass,
    ObservationOmissionPass, PublicPrivateBoundaryMismatchPass, RecursionEnvelopeMismatchPass,
    SemanticNoOpDriftPass, StaleStateReadsPass, TraceOrderingCorruptionPass, WitnessAliasingPass,
};
pub use crate::pack::{
    build_pack_readiness_report_from_reader, read_pack_readiness_report,
    read_pack_readiness_validation, validate_pack_readiness_report,
    write_pack_readiness_outputs_for_pack, BenchmarkPackManifest, BenchmarkPackReader,
    BenchmarkPackWriter, PackReadinessCheck, PackReadinessCheckKind, PackReadinessInputKind,
    PackReadinessInputRef, PackReadinessOutput, PackReadinessReplayCommandMetadata,
    PackReadinessReport, PackReadinessValidation, PackReadinessValidationIssueKind,
    PACK_READINESS_REPORT_PATH, PACK_READINESS_VALIDATION_PATH, PACK_VALIDATION_REPORT_PATH,
};
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
pub use crate::report_bundle::{
    build_report_bundle_manifest_from_reports, compute_report_bundle_manifest_digest,
    deserialize_report_bundle_manifest_json, serialize_report_bundle_manifest_json,
    validate_report_bundle_manifest, ReportBundleInputKind, ReportBundleInputRef,
    ReportBundleManifest, ReportBundlePackReadinessInput, ReportBundleRenderedReport,
    ReportBundleValidation, ReportBundleValidationIssueKind,
};
pub use crate::scoring::{
    classify_mutation_distinguishability, mandatory_distinguishability_nonclaims,
    score_report_from_evidence, score_report_from_local_mutation_evidence,
    summarize_mutation_distinguishability, validate_score_report, LocalMutationEvidenceSummary,
    MutationDistinguishabilityAxis, MutationDistinguishabilityCell,
    MutationDistinguishabilityMatrix, MutationDistinguishabilitySummary, ScoreReport,
    ScoreReportValidation, ScoreReportValidationIssue,
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
pub use crate::zkml::{
    compute_zkml_workload_digest_root, validate_zkml_workload_manifest, ZkMlMetric, ZkMlMetricKind,
    ZkMlModelArtifactRef, ZkMlWorkloadInputKind, ZkMlWorkloadInputRef, ZkMlWorkloadManifest,
    ZkMlWorkloadValidation, ZkMlWorkloadValidationIssueKind,
};
