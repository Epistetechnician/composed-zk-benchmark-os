#![forbid(unsafe_code)]
//! Core data model for Composed ZK Benchmark OS.
//!
//! This crate implements the Level 1 local foundation only: Surface DSL parsing,
//! Parsed AST validation, canonical Semantic IR lowering, a small local oracle
//! evaluator, result classification, evidence primitives, replay manifests,
//! adapter traits, mutation metadata, and score report primitives.
//!
//! A local oracle acceptance is not proof-system acceptance, not official
//! benchmark evidence, and not a formal proof.

pub mod adapters;
pub mod dsl;
pub mod error;
pub mod evidence;
pub mod external_runner;
pub mod generator;
pub mod ids;
pub mod mutation;
pub mod pack;
pub mod prelude;
pub mod registry;
pub mod replay;
pub mod scoring;
pub mod soak;
pub mod value;

pub use adapters::{
    build_default_gnark_recursion_adapter_manifest, build_default_zk_harness_adapter_manifest,
    build_default_zkml_narrow_adapter_manifest, build_gnark_recursion_envelope_plan,
    build_gnark_recursion_envelope_plan_from_manifest,
    build_manual_handoff_bundle_from_zk_harness_plan, build_zk_harness_dry_run_plan_from_pack,
    build_zk_harness_manual_handoff_bundle, build_zkml_narrow_workload_plan,
    build_zkml_narrow_workload_plan_from_manifest, default_gnark_recursion_capability_declaration,
    default_zk_harness_capability_declaration, default_zk_harness_future_execution_prerequisites,
    default_zkml_narrow_capability_declaration, deserialize_gnark_recursion_envelope_plan_json,
    deserialize_gnark_recursion_manifest_json, deserialize_zk_harness_dry_run_plan_json,
    deserialize_zk_harness_manifest_json, deserialize_zkml_narrow_manifest_json,
    deserialize_zkml_narrow_workload_plan_json, export_pack_to_zk_harness_dry_run_plan,
    gnark_recursion_capabilities, local_json_capabilities,
    serialize_gnark_recursion_envelope_plan_json, serialize_gnark_recursion_manifest_json,
    serialize_zk_harness_dry_run_plan_json, serialize_zk_harness_manifest_json,
    serialize_zkml_narrow_manifest_json, serialize_zkml_narrow_workload_plan_json,
    validate_gnark_recursion_envelope_plan, validate_zk_harness_dry_run_plan,
    validate_zkml_narrow_workload_plan, zk_harness_dry_run_capabilities, zkml_narrow_capabilities,
    AdapterCapabilitySet, BackendAdapter, BackendTarget,
    GnarkRecursionAdapterCapabilityDeclaration, GnarkRecursionAdapterManifest,
    GnarkRecursionAdapterManifestId, GnarkRecursionAdapterManifestVersion,
    GnarkRecursionAdapterRegistryEntry, GnarkRecursionAdapterScope, GnarkRecursionAdapterStatus,
    GnarkRecursionClaimBoundaryPolicy, GnarkRecursionCompatibilityTarget,
    GnarkRecursionEnvelopePlan, GnarkRecursionEnvelopePlanId,
    GnarkRecursionEnvelopePlanRegistryEntry, GnarkRecursionEnvelopePlanVersion,
    GnarkRecursionEnvelopeScope, GnarkRecursionEnvelopeStep, GnarkRecursionEnvelopeStepKind,
    GnarkRecursionEnvelopeValidation, GnarkRecursionEnvelopeValidationIssue,
    GnarkRecursionEvidenceMapping, GnarkRecursionEvidencePolicy, GnarkRecursionExecutionPolicy,
    GnarkRecursionFixtureRef, GnarkRecursionIntegrationPhase, GnarkRecursionPlannedCommand,
    GnarkRecursionReviewStatus, GnarkRecursionSchemaAssumption, GnarkRecursionSourcePolicy,
    GnarkRecursionToolRef, GnarkRecursionUnsupportedFeature, LocalJsonAdapter,
    LocalJsonAdapterConfig, LocalJsonReplayInput, LocalJsonReplayOutput, LocalJsonReplaySummary,
    ZkHarnessAdapterManifest, ZkHarnessAdapterManifestId, ZkHarnessAdapterManifestVersion,
    ZkHarnessAdapterRegistryEntry, ZkHarnessAdapterScope, ZkHarnessAdapterStatus,
    ZkHarnessArtifactExpectation, ZkHarnessArtifactMapping, ZkHarnessClaimBoundaryPolicy,
    ZkHarnessCommandArgument, ZkHarnessCommandArtifact, ZkHarnessCommandEnvironment,
    ZkHarnessCompatibilityTarget, ZkHarnessDryRunPlan, ZkHarnessDryRunPlanId,
    ZkHarnessDryRunPlanRegistryEntry, ZkHarnessDryRunPlanVersion, ZkHarnessDryRunPlanner,
    ZkHarnessDryRunValidation, ZkHarnessDryRunValidationIssue, ZkHarnessEvidenceMapping,
    ZkHarnessEvidencePolicy, ZkHarnessExecutionPolicy, ZkHarnessExpectedOutcomeMapping,
    ZkHarnessExternalToolRef, ZkHarnessFamilyMapping, ZkHarnessFutureExecutionPrerequisite,
    ZkHarnessIntegrationPhase, ZkHarnessManualHandoffBundle, ZkHarnessManualHandoffMapping,
    ZkHarnessMappingWarning, ZkHarnessMetricKind, ZkHarnessMetricMapping, ZkHarnessMutationMapping,
    ZkHarnessPackExportManifest, ZkHarnessPackMapping, ZkHarnessPlanStep, ZkHarnessPlanStepKind,
    ZkHarnessPlanSubject, ZkHarnessPlannedCommand, ZkHarnessResultImportExpectation,
    ZkHarnessReviewStatus, ZkHarnessSchemaAssumption, ZkHarnessSourcePolicy, ZkHarnessTraceMapping,
    ZkHarnessUnsupportedFeature, ZkmlNarrowAdapterCapabilityDeclaration, ZkmlNarrowAdapterManifest,
    ZkmlNarrowAdapterManifestId, ZkmlNarrowAdapterManifestVersion, ZkmlNarrowAdapterRegistryEntry,
    ZkmlNarrowAdapterScope, ZkmlNarrowAdapterStatus, ZkmlNarrowClaimBoundaryPolicy,
    ZkmlNarrowCompatibilityTarget, ZkmlNarrowEvidenceMapping, ZkmlNarrowEvidencePolicy,
    ZkmlNarrowExecutionPolicy, ZkmlNarrowFixtureRef, ZkmlNarrowIntegrationPhase,
    ZkmlNarrowPlannedCommand, ZkmlNarrowReviewStatus, ZkmlNarrowSchemaAssumption,
    ZkmlNarrowSourcePolicy, ZkmlNarrowToolRef, ZkmlNarrowUnsupportedFeature,
    ZkmlNarrowWorkloadPlan, ZkmlNarrowWorkloadPlanId, ZkmlNarrowWorkloadPlanRegistryEntry,
    ZkmlNarrowWorkloadPlanVersion, ZkmlNarrowWorkloadScope, ZkmlNarrowWorkloadStep,
    ZkmlNarrowWorkloadStepKind, ZkmlNarrowWorkloadValidation, ZkmlNarrowWorkloadValidationIssue,
    LOCAL_JSON_ADAPTER_ID,
};
pub use dsl::{
    evaluate_trace, lower_to_ir, parse_yaml_ast, parse_yaml_spec, ActionSpec, CanonicalAction,
    CanonicalField, CanonicalGuard, CanonicalInvariant, CanonicalMachine, CanonicalOracle,
    CanonicalState, CanonicalTransition, EvidenceSpec, FieldSpec, GuardSpec, InvariantSpec,
    LoopSpec, MachineSpec, ObserveSpec, OracleOutcome, OracleSpec, ParsedAst, PrivateWitnessSpec,
    PublicInputSpec, SemanticEquivalenceClass, SemanticIr, StateSpec, SurfaceSpec, TargetSpec,
    TraceSpec, TraceStepSpec, TransitionSpec, WitnessPolicy,
};
pub use error::{Result, ZkBenchError};
pub use evidence::{
    build_default_evidence_acceptance_policy, build_default_evidence_review_checklist,
    canonical_json_bytes, classify_result, compute_artifact_digest, compute_artifact_digest_bytes,
    compute_artifact_digest_for_json, create_evidence_record_candidate,
    deserialize_evidence_acceptance_policy_json, deserialize_evidence_record_candidate_json,
    deserialize_evidence_review_checklist_json, deserialize_evidence_review_decision_json,
    guard_claim_boundary_escalation, review_evidence_append_proposal,
    serialize_evidence_acceptance_policy_json, serialize_evidence_record_candidate_json,
    serialize_evidence_review_checklist_json, serialize_evidence_review_decision_json,
    validate_evidence_acceptance_policy, validate_evidence_record_candidate,
    validate_evidence_review_decision, ArtifactDigest, ArtifactDigestAlgorithm, ArtifactKind,
    ArtifactRef, ArtifactRole, BackendOutcome, ClaimBoundary, ClaimBoundaryEscalationGuard,
    ClaimBoundaryEscalationGuardResult, EvidenceAcceptanceBlockingReason, EvidenceAcceptancePolicy,
    EvidenceAcceptancePolicyId, EvidenceAcceptancePolicyMode, EvidenceAcceptancePolicyVersion,
    EvidenceAcceptanceValidation, EvidenceAppendPolicy, EvidenceChainDigest, EvidenceClass,
    EvidenceLedger, EvidenceLedgerEntry, EvidenceLedgerSummary, EvidenceLedgerSummaryCount,
    EvidenceLedgerValidation, EvidenceLedgerValidationError, EvidenceLedgerVersion, EvidenceRecord,
    EvidenceRecordCandidate, EvidenceRecordCandidateId, EvidenceRecordCandidateIssueKind,
    EvidenceRecordCandidateKind, EvidenceRecordCandidateSource, EvidenceRecordCandidateStatus,
    EvidenceRecordCandidateValidation, EvidenceRecordCandidateValidationIssue,
    EvidenceRecordCandidateVersion, EvidenceReviewChecklist, EvidenceReviewChecklistItem,
    EvidenceReviewDecision, EvidenceReviewDecisionId, EvidenceReviewDecisionKind,
    EvidenceReviewDecisionStatus, EvidenceReviewDecisionVersion, EvidenceReviewFinding,
    EvidenceReviewFindingSeverity, EvidenceReviewPolicy, EvidenceReviewReport,
    EvidenceReviewRequirement, EvidenceReviewerRole, EvidenceStrength, ExpectedVerdict,
    ProvenanceRecord, ResultClassification,
};
pub use external_runner::{
    build_default_artifact_capture_contract, build_default_external_result_import_schema,
    build_default_external_runner_policy, build_default_provenance_contract,
    contains_formal_claim_text, contains_official_claim_text, contains_soundness_claim_text,
    create_evidence_append_proposal, deserialize_artifact_capture_contract_json,
    deserialize_evidence_append_proposal_json, deserialize_evidence_append_proposal_ledger_json,
    deserialize_external_result_candidate_json, deserialize_external_result_import_schema_json,
    deserialize_external_runner_policy_json, deserialize_manual_handoff_bundle_json,
    deserialize_normalized_external_result_draft_json, deserialize_provenance_contract_json,
    deserialize_quarantine_manifest_json, deserialize_synthetic_result_import_bundle_json,
    external_result_quarantine_record, import_synthetic_result_candidate_json,
    normalize_synthetic_result_candidate, quarantine_external_result_candidate,
    quarantine_synthetic_result_candidate, required_provenance_fields,
    serialize_artifact_capture_contract_json, serialize_evidence_append_proposal_json,
    serialize_evidence_append_proposal_ledger_json, serialize_external_result_candidate_json,
    serialize_external_result_import_schema_json, serialize_external_runner_policy_json,
    serialize_manual_handoff_bundle_json, serialize_normalized_external_result_draft_json,
    serialize_provenance_contract_json, serialize_quarantine_manifest_json,
    serialize_synthetic_result_import_bundle_json, validate_artifact_capture_contract,
    validate_evidence_append_proposal, validate_external_result_candidate,
    validate_external_result_candidate_with_schema, validate_external_result_import_schema,
    validate_external_run_provenance_draft, validate_external_runner_policy,
    validate_manual_handoff_bundle, validate_provenance_contract, validate_quarantine_manifest,
    validate_synthetic_result_candidate, validate_synthetic_result_candidate_with_config,
    ArtifactCaptureContract, ArtifactCaptureContractId, ArtifactCaptureContractVersion,
    ArtifactCaptureRequirement, ArtifactDigestValidation, CapturedArtifactMetadata,
    CapturedArtifactValidation, CapturedArtifactValidationIssue, ClaimBoundaryValidation,
    EnvironmentProvenance, EvidenceAppendProposal, EvidenceAppendProposalDigest,
    EvidenceAppendProposalId, EvidenceAppendProposalKind, EvidenceAppendProposalLedger,
    EvidenceAppendProposalLedgerEntry, EvidenceAppendProposalLedgerSummary,
    EvidenceAppendProposalLedgerSummaryCount, EvidenceAppendProposalLedgerValidation,
    EvidenceAppendProposalLedgerValidationIssue, EvidenceAppendProposalLedgerVersion,
    EvidenceAppendProposalReviewState, EvidenceAppendProposalStatus,
    EvidenceAppendProposalValidation, EvidenceAppendProposalValidationIssue,
    EvidenceAppendProposalVersion, ExpectedArtifact, ExpectedArtifactFormat, ExpectedArtifactRole,
    ExternalClaimBoundaryPolicy, ExternalEnvironmentPolicy, ExternalExecutionGate,
    ExternalExecutionMode, ExternalExecutionReviewStatus, ExternalMetricCandidate,
    ExternalMetricUnit, ExternalNetworkPolicy, ExternalPathPolicy, ExternalResultCandidate,
    ExternalResultCandidateId, ExternalResultImportPolicy, ExternalResultImportSchema,
    ExternalResultImportSchemaId, ExternalResultPolicy, ExternalResultQuarantineRecord,
    ExternalResultStatus, ExternalResultValidation, ExternalResultValidationIssue,
    ExternalRunProvenanceDraft, ExternalRunnerPolicy, ExternalRunnerPolicyId,
    ExternalRunnerPolicyVersion, ExternalToolAllowlist, ExternalToolProvenance,
    ExternalValidationIssue, ExternalValidationIssueSeverity, FormalClaimDetection,
    ManualHandoffBundle, ManualHandoffBundleId, ManualHandoffBundleVersion, ManualHandoffExport,
    ManualHandoffInstruction, ManualHandoffStep, ManualHandoffStepKind, ManualHandoffSubject,
    ManualHandoffValidation, ManualHandoffValidationIssue, MetricCandidateValidation,
    NormalizationReport, NormalizationWarning, NormalizedArtifactRef,
    NormalizedExternalResultDraft, NormalizedExternalResultDraftId,
    NormalizedExternalResultDraftStatus, NormalizedMetricDraft, NormalizedProvenanceDraft,
    OfficialClaimDetection, OperatorProvenance, ProvenanceContract, ProvenanceContractValidation,
    ProvenanceFieldRequirement, ProvenanceValidation, ProvenanceValidationIssue, QuarantineEntry,
    QuarantineManifest, QuarantineReason, QuarantineStatus, QuarantineValidation,
    QuarantineValidationIssue, RequiredProvenanceField, ResultCandidateArtifactLookup,
    ResultCandidateArtifactResolver, ResultCandidateSource, ResultCandidateSourceKind,
    SoundnessClaimDetection, SourceProvenance, SyntheticImportValidation,
    SyntheticImportValidationIssue, SyntheticImportValidationIssueKind,
    SyntheticResultImportBundle, SyntheticResultImportBundleId, SyntheticResultImportBundleVersion,
    SyntheticResultImportConfig, SyntheticResultImportReport, SyntheticResultImporter,
    SyntheticValidationIssueCount, PHASE_I_SYNTHETIC_CLAIM_BOUNDARY,
};
pub use generator::{
    evaluate_generated_instance, generate_family, generate_instance, BenchmarkFamily,
    BenchmarkInstance, DeterministicGenerator, FamilyKind, FamilyTemplate,
    GeneratedBenchmarkFamily, GeneratedBenchmarkInstance, GenerationProvenance, GeneratorConfig,
    GeneratorLimits, GeneratorProfile, GeneratorSeed, GeneratorTunables, InstanceParams,
};
pub use mutation::{
    apply_default_mutations, apply_mutation_pass, evaluate_mutated_instance, BadCountersPass,
    CorruptedGuardsPass, MissingConstraintsPass, MutatedBenchmarkInstance, MutationApplication,
    MutationEngine, MutationExpectedVerdict, MutationInput, MutationOutput, MutationPass,
    MutationPlan, MutationProvenance, MutationSafetyClass,
};
pub use mutation::{MutationClass, MutationKind, MutationSeverity, MutationSpec, MutationVariant};
pub use pack::{
    attach_reproduction_bundle_to_pack, deserialize_benchmark_pack_reproduction_metadata_json,
    deserialize_report_bundle_review_report_json, evaluate_level2_eligibility,
    review_report_bundle, review_sampled_report_bundles, review_soak_report_bundles,
    serialize_benchmark_pack_reproduction_metadata_json, serialize_report_bundle_review_report_json,
    validate_benchmark_pack_reproduction_metadata, BenchmarkPackFile, BenchmarkPackFileRole,
    BenchmarkPackId, BenchmarkPackManifest, BenchmarkPackReader, BenchmarkPackReproductionMetadata,
    BenchmarkPackReproductionMetadataVersion, BenchmarkPackSummary, BenchmarkPackValidation,
    BenchmarkPackValidationError, BenchmarkPackVersion, BenchmarkPackWriter,
    ExternalReplayPlanAttachment, ExternalReplayPlanKind, Level2EligibilityBlockingReason,
    Level2EligibilityReport, Level2EligibilityReportVersion, Level2EligibilityStatus,
    ReportBundleReviewFinding, ReportBundleReviewFindingSeverity, ReportBundleReviewPlan,
    ReportBundleReviewReport, ReportBundleReviewReportVersion, ReportBundleSampleStrategy,
};
pub use registry::{
    gnark_recursion_adapter_registry_entry, gnark_recursion_envelope_plan_registry_entry,
    list_available_local_generators, list_local_adapter_targets, local_benchmark_pack_schema,
    resolve_local_generator, zk_harness_adapter_registry_entry,
    zk_harness_dry_run_plan_registry_entry, zkml_narrow_adapter_registry_entry,
    zkml_narrow_workload_plan_registry_entry, LocalGeneratorRegistry, RegistryEntry,
};
pub use replay::{
    build_local_replay_manifest_for_instance, build_local_replay_manifest_for_mutation,
    deserialize_replay_manifest_json, deserialize_replay_result_json, run_local_replay,
    serialize_replay_manifest_json, serialize_replay_result_json, ReplayCommand,
    ReplayExpectedOutcome, ReplayFailureMode, ReplayManifest, ReplayMode, ReplayResult,
    ReplaySerializationVersion, ReplayStatus, ReplaySubject, ReplaySubjectKind, ReplayTraceResult,
    ReplayTraceSelection,
};
pub use scoring::{
    score_report_from_evidence, score_report_from_local_mutation_evidence, AdapterPortabilityScore,
    CorrectnessScore, FormalEvidenceScore, LocalMutationEvidenceSummary, PerformanceScore,
    RecursionStressScore, ReproducibilityScore, RiskPenalty, ScoreConfidence, ScoreReport,
    SoundnessFailureDetectionScore,
};
pub use soak::{
    append_regression_entries, deserialize_soak_execution_report_json, load_regression_corpus,
    quick_campaign_config, quick_three_family_all_passes, quick_three_family_smoke, run_local_soak,
    run_soak_campaign, save_regression_corpus, serialize_regression_corpus_json,
    serialize_soak_campaign_report_json, serialize_soak_execution_report_json,
    soak_config_from_plan, PackSampledReview, RegressionCorpus, RegressionCorpusEntry,
    RegressionCorpusVersion, RegressionFailureKind, SoakCampaignConfig, SoakCampaignReport,
    SoakCampaignReportVersion, SoakConfig, SoakExecutionReport, SoakExecutionReportVersion,
    SoakFailure, SoakPackDescriptor, SoakPlan,
};
