use hsai_agent_case::AgentCase;
use hsai_attestation::report_data_binding;
use hsai_claim_envelope::{ClaimEnvelope, Hash, SubjectId};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::str::FromStr;

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct AdmissionCandidateId(pub String);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct AdmissionPolicyId(pub String);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct AdmissionReason(pub String);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct NonClaimLabel(pub String);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct ArtifactDigest {
    pub id: String,
    pub sha256: Hash,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum AdmissionSourceKind {
    AgentCase,
    ClaimEnvelopeProposal,
    ProviderResponse,
    BenchmarkResultProposal,
    PcsmBoundedProofHandoff,
    GatewayActionProposal,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum AdmissionClaimBoundary {
    LocalOnly,
    Level1Local,
    Level2OrHigher,
    Formal,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct GatewayActionId(pub String);

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayActionKind {
    Payment,
    Trade,
    ToolCall,
    DataAccess,
    ComputeRental,
    Deployment,
    Checkout,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayThreatLabel {
    Benign,
    PromptInjectionPayment,
    WrongCounterparty,
    AmountLimitBypass,
    SourceDigestDrift,
    StaleApprovalReplay,
    DuplicateJsonKeyPayload,
    PolicyDowngrade,
    DirectAuthorityRequest,
    ForgedAcceptedDecision,
    MissingNonclaim,
    MissingSourceDigest,
    StaleJournalTip,
    SignerBeforeAdmission,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayModelLaneKind {
    Deterministic,
    LocalOpenWeight,
    RentedOpenWeight,
    HostedSmall,
    PremiumEscalation,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayModelLaneProvenance {
    pub lane_kind: GatewayModelLaneKind,
    pub model_family: String,
    pub artifact_id: String,
    pub runtime: String,
    pub prompt_template_digest: Hash,
    pub input_corpus_digest: Hash,
    pub output_bundle_digest: Hash,
    pub non_secret: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayModelLaneRegistryEntry {
    pub lane_id: String,
    pub provenance: GatewayModelLaneProvenance,
    pub expected_output_bundle_digest: Hash,
    pub max_cases_per_run: Option<u64>,
    pub max_cost_units_per_case: Option<u64>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayModelLaneRegistry {
    pub schema_version: String,
    pub entries: Vec<GatewayModelLaneRegistryEntry>,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayModelLaneRegistryIssue {
    InvalidLaneId(String),
    DuplicateLaneId(String),
    MissingModelId(String),
    MissingPromptTemplateDigest(String),
    MissingNonSecretStatement(String),
    StaleOutputDigest(String),
    UnboundedRentedModelMetadata(String),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayAdversarialCorpus {
    pub schema_version: String,
    pub corpus_id: String,
    pub cases: Vec<GatewayCorpusCase>,
    pub required_threat_labels: BTreeSet<GatewayThreatLabel>,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayAdversarialCorpusIssue {
    InvalidCorpusId,
    EmptyCorpus,
    DuplicateCaseId(GatewayActionId),
    MissingRequiredThreatLabel(GatewayThreatLabel),
    MissingAcceptedBenignCase,
    UnsafeThreatExpectedAccepted(GatewayActionId),
    UnknownModelLane(GatewayActionId),
    InvalidModelLaneRegistry,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayCostRoute {
    DeterministicOnly,
    LocalOpenWeightReview,
    VerifierMixture,
    PremiumEscalation,
    OperatorReviewRequired,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayCostRouteReason {
    DeterministicPolicyViolation,
    RoutineLowValueAction,
    LocalReviewForModerateValue,
    ThreatLabelNeedsVerifierMixture,
    HighValueNeedsPremiumEscalation,
    PremiumEscalationBudgetExceeded,
    OperatorOnlyActionKind,
    OperatorValueLimitExceeded,
    NoAuthorityGrantedByRouter,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayCostRouterPolicy {
    pub id: AdmissionPolicyId,
    pub local_review_value_ceiling: u64,
    pub verifier_mixture_value_ceiling: u64,
    pub premium_escalation_value_ceiling: u64,
    pub local_review_cost_units: u64,
    pub verifier_mixture_cost_units: u64,
    pub premium_escalation_cost_units: u64,
    pub operator_review_cost_units: u64,
    pub premium_escalation_budget_units: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayCostRouteDecision {
    pub action_id: GatewayActionId,
    pub policy_id: AdmissionPolicyId,
    pub route: GatewayCostRoute,
    pub reasons: BTreeSet<GatewayCostRouteReason>,
    pub estimated_cost_units: u64,
    pub authority_granted: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayActionProposal {
    pub id: GatewayActionId,
    pub subject: SubjectId,
    pub action_kind: GatewayActionKind,
    pub target: String,
    pub value_units: u64,
    pub source_artifact_digests: BTreeSet<ArtifactDigest>,
    pub nonclaims: BTreeSet<NonClaimLabel>,
    pub model_lane: GatewayModelLaneProvenance,
    pub threat_labels: BTreeSet<GatewayThreatLabel>,
    pub direct_authority_requested: bool,
    pub signer_or_tool_requested_before_admission: bool,
}

impl GatewayActionProposal {
    pub fn digest(&self) -> Hash {
        hash_tagged("hsai-agent-admission:gateway-action-proposal:v1", self)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayPolicyViolation {
    InvalidActionId,
    InvalidTarget,
    UnsupportedActionKind,
    UnauthorizedTarget,
    AmountLimitExceeded,
    MissingModelLaneProvenance,
    ModelLaneNotNonSecret,
    DirectAuthorityRequested,
    SignerOrToolRequestedBeforeAdmission,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayActionPolicy {
    pub id: AdmissionPolicyId,
    pub admission_policy: AgentAdmissionPolicy,
    pub allowed_action_kinds: BTreeSet<GatewayActionKind>,
    pub allowed_targets: BTreeSet<String>,
    pub max_value_units: u64,
    pub require_non_secret_model_lane: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayAcceptedHandoff {
    pub action_id: GatewayActionId,
    pub subject: SubjectId,
    pub action_kind: GatewayActionKind,
    pub target: String,
    pub value_units: u64,
    pub candidate_digest: Hash,
    pub decision_digest: Hash,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayActionOutcome {
    pub proposal_id: GatewayActionId,
    pub candidate_id: AdmissionCandidateId,
    pub action_digest: Hash,
    pub decision: AgentAdmissionDecision,
    pub accepted_handoff: Option<GatewayAcceptedHandoff>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayCorpusCase {
    pub proposal: GatewayActionProposal,
    pub expected_verdict: AdmissionVerdict,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayRunMetrics {
    pub total_cases: u64,
    pub accepted_count: u64,
    pub rejected_count: u64,
    pub quarantined_count: u64,
    pub unsafe_action_blocked_count: u64,
    pub false_rejection_count: u64,
    pub replay_or_tamper_detection_count: u64,
    pub duplicate_key_detection_count: u64,
    pub policy_downgrade_detection_count: u64,
    pub decision_recomputation_agreement_count: u64,
    pub audit_bundle_complete: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayCorpusReport {
    pub journal: AgentAdmissionJournal,
    pub outcomes: Vec<GatewayActionOutcome>,
    pub metrics: GatewayRunMetrics,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayBaselineKind {
    NoApprovalGateway,
    StaticAllowlist,
    WalletPolicyOnly,
    OpaPolicyOnly,
    AgentFrameworkGuardrails,
    LlmJudgeOnly,
    ManualReview,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayBaselineDecision {
    pub proposal_id: GatewayActionId,
    pub verdict: AdmissionVerdict,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayBaselineRun {
    pub baseline_id: String,
    pub baseline_kind: GatewayBaselineKind,
    pub decisions: Vec<GatewayBaselineDecision>,
    pub nonclaims: BTreeSet<NonClaimLabel>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayBaselineComparison {
    pub baseline_id: String,
    pub baseline_kind: GatewayBaselineKind,
    pub total_cases: u64,
    pub hsai_unsafe_accepted_count: u64,
    pub baseline_unsafe_accepted_count: u64,
    pub hsai_false_rejection_count: u64,
    pub baseline_false_rejection_count: u64,
    pub hsai_audit_bundle_complete: bool,
    pub baseline_audit_bundle_complete: bool,
    pub claim_boundary: String,
    pub authority_granted: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayThreatCoverageRow {
    pub threat_label: GatewayThreatLabel,
    pub case_count: u64,
    pub blocked_count: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayEffectivenessSummary {
    pub total_cases: u64,
    pub unsafe_case_count: u64,
    pub benign_expected_accept_count: u64,
    pub unsafe_action_block_rate_basis_points: u64,
    pub false_rejection_rate_basis_points: u64,
    pub quarantine_rate_basis_points: u64,
    pub decision_recomputation_agreement_rate_basis_points: u64,
    pub audit_bundle_complete: bool,
    pub covered_threat_labels: BTreeSet<GatewayThreatLabel>,
    pub threat_coverage: Vec<GatewayThreatCoverageRow>,
    pub claim_boundary: String,
    pub authority_granted: bool,
}

pub const GATEWAY_ATTESTATION_BINDING_SCHEMA_VERSION: &str = "hsai-gateway-attestation-binding:v1";
pub const GATEWAY_ATTESTATION_BINDING_CLAIM_BOUNDARY: &str = "Gateway-to-attestation challenge binding only; not attestation evidence, proof, live provider evidence, accepted evidence, benchmark evidence, SOTA, breakthrough, production readiness, semantic correctness, full security, or authority to execute an action.";

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayAttestationChallengeBinding {
    pub schema_version: String,
    pub challenge_id: String,
    pub proposal_id: GatewayActionId,
    pub subject: SubjectId,
    pub policy_id: AdmissionPolicyId,
    pub anchor_id: String,
    pub agent_pubkey_spki_hex: String,
    pub nonce: u64,
    pub challenge_created_at: u64,
    pub challenge_expires_at: u64,
    pub gateway_case_hash_hex: String,
    pub expected_report_data_hex: String,
    pub claim_boundary: String,
    pub authority_granted: bool,
    pub nonclaims: BTreeSet<NonClaimLabel>,
}

impl GatewayAttestationChallengeBinding {
    pub fn digest(&self) -> Hash {
        hash_tagged(
            "hsai-agent-admission:gateway-attestation-challenge-binding:v1",
            self,
        )
    }
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayAttestationBindingError {
    EmptyField(&'static str),
    InvalidHex { field: &'static str, value: String },
    InvalidWindow { created_at: u64, expires_at: u64 },
    NotYetValid { now: u64, created_at: u64 },
    ExpiredChallenge { now: u64, expires_at: u64 },
    SchemaMismatch(String),
    ProposalIdMismatch,
    SubjectMismatch,
    PolicyIdMismatch,
    GatewayCaseHashMismatch { actual: String, expected: String },
    ReportDataMismatch { actual: String, expected: String },
    ChallengeIdMismatch { actual: String, expected: String },
    AuthorityGranted,
    MissingRequiredNonclaim(String),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayOperatorArtifactReference {
    pub reference_id: String,
    pub provider: String,
    pub artifact_kind: String,
    pub operator_run_id: String,
    pub artifact_digest: ArtifactDigest,
    pub repo_external: bool,
    pub claim_boundary: String,
    pub nonclaims: BTreeSet<NonClaimLabel>,
}

impl GatewayOperatorArtifactReference {
    pub fn digest(&self) -> Hash {
        hash_tagged(
            "hsai-agent-admission:gateway-operator-artifact-reference:v1",
            self,
        )
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayOperatorBridgeBundle {
    pub schema_version: String,
    pub bundle_id: String,
    pub created_at_unix: u64,
    pub gateway_report_digest: Hash,
    pub gateway_report_manifest_digest: Hash,
    pub attestation_binding: GatewayAttestationChallengeBinding,
    pub operator_artifact_reference: GatewayOperatorArtifactReference,
    pub claim_boundary: String,
    pub authority_granted: bool,
    pub accepted_evidence_mutation: bool,
    pub nonclaims: BTreeSet<NonClaimLabel>,
}

impl GatewayOperatorBridgeBundle {
    pub fn digest(&self) -> Hash {
        hash_tagged(
            "hsai-agent-admission:gateway-operator-bridge-bundle:v1",
            self,
        )
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayOperatorBridgeMaterializationRequest {
    pub bundle_id: String,
    pub created_at_unix: u64,
    pub overwrite: bool,
    pub protected_roots: Vec<PathBuf>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayOperatorBridgeOutputManifest {
    pub schema_version: String,
    pub bundle_id: String,
    pub created_at_unix: u64,
    pub bridge_bundle_digest: Hash,
    pub gateway_report_digest: Hash,
    pub gateway_report_manifest_digest: Hash,
    pub attestation_binding_digest: Hash,
    pub operator_artifact_reference_digest: Hash,
    pub declared_files: Vec<String>,
    pub declared_file_digests: BTreeMap<String, Hash>,
    pub claim_boundary: String,
    pub authority_granted: bool,
    pub accepted_evidence_mutation: bool,
    pub nonclaims: BTreeSet<NonClaimLabel>,
}

impl GatewayOperatorBridgeOutputManifest {
    pub fn digest(&self) -> Hash {
        hash_tagged(
            "hsai-agent-admission:gateway-operator-bridge-output-manifest:v1",
            self,
        )
    }
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayOperatorBridgePromotionReviewDecision {
    ApprovedMetadataOnly,
    Rejected,
    Unreviewed,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayOperatorBridgePromotionPreflightRequest {
    pub schema_version: String,
    pub preflight_id: String,
    pub reviewer_id: String,
    pub review_decision: GatewayOperatorBridgePromotionReviewDecision,
    pub bridge_bundle: GatewayOperatorBridgeBundle,
    pub bridge_manifest: GatewayOperatorBridgeOutputManifest,
    pub requested_claim_boundary: String,
    pub retains_raw_provider_artifacts: bool,
    pub retains_credentials_or_secrets: bool,
    pub accepted_evidence_mutation_requested: bool,
    pub level2_evidence_requested: bool,
    pub score_axis_population_requested: bool,
    pub production_readiness_claimed: bool,
    pub semantic_correctness_claimed: bool,
    pub live_provider_evidence_claimed: bool,
    pub claim_text: Vec<String>,
    pub nonclaims: BTreeSet<NonClaimLabel>,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayOperatorBridgePromotionPreflightIssue {
    InvalidSchemaVersion,
    InvalidPreflightId,
    MissingReviewer,
    ReviewNotApprovedMetadataOnly,
    InvalidBridgeBundle,
    BridgeManifestMismatch,
    OperatorArtifactNotRepoExternal,
    RawProviderArtifactRetained,
    CredentialsOrSecretsRetained,
    AcceptedEvidenceMutationRequested,
    Level2EvidenceRequested,
    ScoreAxisPopulationRequested,
    ProductionReadinessClaimed,
    SemanticCorrectnessClaimed,
    LiveProviderEvidenceClaimed,
    RequestedClaimBoundaryMismatch,
    ForbiddenClaimText(String),
    MissingRequiredNonclaim(String),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayOperatorBridgePromotionPreflightValidation {
    pub valid: bool,
    pub issues: Vec<GatewayOperatorBridgePromotionPreflightIssue>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayOperatorBridgePromotionPreflightReport {
    pub schema_version: String,
    pub preflight_id: String,
    pub bridge_bundle_digest: Hash,
    pub bridge_manifest_digest: Hash,
    pub gateway_report_digest: Hash,
    pub attestation_binding_digest: Hash,
    pub operator_artifact_reference_digest: Hash,
    pub validation: GatewayOperatorBridgePromotionPreflightValidation,
    pub claim_boundary: String,
    pub mutates_accepted_evidence_ledger: bool,
    pub creates_level2_evidence: bool,
    pub populates_score_axes: bool,
    pub grants_authority: bool,
    pub retains_raw_provider_artifacts: bool,
    pub retains_credentials_or_secrets: bool,
    pub nonclaims: BTreeSet<NonClaimLabel>,
}

impl GatewayOperatorBridgePromotionPreflightReport {
    pub fn digest(&self) -> Hash {
        hash_tagged(
            "hsai-agent-admission:gateway-operator-bridge-promotion-preflight-report:v1",
            self,
        )
    }
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayOperatorBridgeAcceptancePreviewDecision {
    ApproveCandidateOnly,
    Reject,
    Unreviewed,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayOperatorBridgeAcceptancePreviewRequest {
    pub schema_version: String,
    pub preview_id: String,
    pub reviewer_id: String,
    pub decision: GatewayOperatorBridgeAcceptancePreviewDecision,
    pub source_preflight_report: GatewayOperatorBridgePromotionPreflightReport,
    pub expected_preflight_report_digest: Hash,
    pub requested_claim_boundary: String,
    pub candidate_only: bool,
    pub accepted_evidence_mutation_requested: bool,
    pub level2_evidence_requested: bool,
    pub score_axis_population_requested: bool,
    pub production_readiness_claimed: bool,
    pub semantic_correctness_claimed: bool,
    pub live_provider_evidence_claimed: bool,
    pub raw_provider_artifact_retention_requested: bool,
    pub credential_retention_requested: bool,
    pub authority_grant_requested: bool,
    pub claim_text: Vec<String>,
    pub nonclaims: BTreeSet<NonClaimLabel>,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayOperatorBridgeAcceptancePreviewIssue {
    InvalidSchemaVersion,
    InvalidPreviewId,
    MissingReviewer,
    ReviewNotCandidateOnlyApproval,
    SourcePreflightInvalid,
    PreflightDigestMismatch,
    RequestedClaimBoundaryMismatch,
    NotCandidateOnly,
    AcceptedEvidenceMutationRequested,
    Level2EvidenceRequested,
    ScoreAxisPopulationRequested,
    ProductionReadinessClaimed,
    SemanticCorrectnessClaimed,
    LiveProviderEvidenceClaimed,
    RawProviderArtifactRetentionRequested,
    CredentialRetentionRequested,
    AuthorityGrantRequested,
    ForbiddenClaimText(String),
    MissingRequiredNonclaim(String),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayOperatorBridgeAcceptancePreviewValidation {
    pub valid: bool,
    pub issues: Vec<GatewayOperatorBridgeAcceptancePreviewIssue>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayOperatorBridgeAcceptancePreviewReport {
    pub schema_version: String,
    pub preview_id: String,
    pub source_preflight_report_digest: Hash,
    pub bridge_bundle_digest: Hash,
    pub bridge_manifest_digest: Hash,
    pub gateway_report_digest: Hash,
    pub attestation_binding_digest: Hash,
    pub operator_artifact_reference_digest: Hash,
    pub validation: GatewayOperatorBridgeAcceptancePreviewValidation,
    pub claim_boundary: String,
    pub candidate_only: bool,
    pub mutates_accepted_evidence_ledger: bool,
    pub creates_level2_evidence: bool,
    pub populates_score_axes: bool,
    pub grants_authority: bool,
    pub retains_raw_provider_artifacts: bool,
    pub retains_credentials_or_secrets: bool,
    pub nonclaims: BTreeSet<NonClaimLabel>,
}

impl GatewayOperatorBridgeAcceptancePreviewReport {
    pub fn digest(&self) -> Hash {
        hash_tagged(
            "hsai-agent-admission:gateway-operator-bridge-acceptance-preview-report:v1",
            self,
        )
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayOperatorBridgeValidationReport {
    pub schema_version: String,
    pub bundle_id: String,
    pub valid: bool,
    pub issue_count: u64,
    pub checked_files: Vec<String>,
    pub claim_boundary: String,
    pub authority_granted: bool,
    pub accepted_evidence_mutation: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayOperatorBridgeIssue {
    InvalidBundleId,
    MissingGatewayReportDigest,
    MissingGatewayReportManifestDigest,
    InvalidAttestationBinding,
    InvalidOperatorReference,
    OperatorArtifactNotRepoExternal,
    AuthorityGranted,
    AcceptedEvidenceMutationRequested,
    ClaimBoundaryMismatch,
    MissingRequiredNonclaim(String),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum GatewayOperatorBridgeMaterializationError {
    InvalidBundle(Vec<GatewayOperatorBridgeIssue>),
    EmptyBundleId,
    EmptyOutputRoot,
    ProtectedOutputRoot,
    OutputRootExistsWithoutOverwrite,
    OutputRootIsFile,
    OutputRootIsSymlink,
    BundleFileIsSymlink(String),
    SidecarIsSymlink(String),
    DeclaredFileTypeMismatch(String),
    UndeclaredFile(String),
    DigestMismatch(String),
    MalformedDeclaredFile(String),
    ManifestSemanticMismatch,
    NonclaimMismatch,
    ValidationReportMismatch,
    Io(String),
    Serialization(String),
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayBaselineComparisonIssue {
    InvalidBaselineId,
    MissingRequiredNonclaim(NonClaimLabel),
    DuplicateBaselineDecision(GatewayActionId),
    MissingBaselineDecision(GatewayActionId),
    UnknownBaselineDecision(GatewayActionId),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum GatewayBaselineComparisonError {
    InvalidReport(Vec<GatewayReportValidationIssue>),
    InvalidBaseline(Vec<GatewayBaselineComparisonIssue>),
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum GatewayReportValidationIssue {
    JournalInvalid,
    MetricsTotalMismatch,
    MetricsVerdictCountMismatch,
    MetricsAcceptedHandoffMismatch,
    MetricsDecisionRecomputationMismatch,
    MetricsAuditBundleCompletenessMismatch,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum GatewayReportArtifactError {
    InvalidReport(Vec<GatewayReportValidationIssue>),
    Serialization(String),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayReportArtifactManifest {
    pub schema_version: String,
    pub claim_boundary: String,
    pub policy_id: AdmissionPolicyId,
    pub report_digest: Hash,
    pub journal_tip_digest_after: Option<Hash>,
    pub report_json_sha256: Hash,
    pub report_markdown_sha256: Hash,
    pub nonclaims: BTreeSet<NonClaimLabel>,
    pub metrics: GatewayRunMetrics,
}

impl GatewayReportArtifactManifest {
    pub fn digest(&self) -> Hash {
        hash_tagged(
            "hsai-agent-admission:gateway-report-artifact-manifest:v1",
            self,
        )
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GatewayReportArtifact {
    pub manifest: GatewayReportArtifactManifest,
    pub report_json: Vec<u8>,
    pub report_markdown: Vec<u8>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GatewayReportMaterializationRequest {
    pub bundle_id: String,
    pub created_at_unix: u64,
    pub overwrite: bool,
    pub protected_roots: Vec<PathBuf>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayReportOutputManifest {
    pub schema_version: String,
    pub bundle_id: String,
    pub created_at_unix: u64,
    pub gateway_policy: GatewayActionPolicy,
    pub artifact_manifest: GatewayReportArtifactManifest,
    pub declared_files: Vec<String>,
    pub declared_file_digests: BTreeMap<String, Hash>,
    pub claim_boundary: String,
}

impl GatewayReportOutputManifest {
    pub fn digest(&self) -> Hash {
        hash_tagged(
            "hsai-agent-admission:gateway-report-output-manifest:v1",
            self,
        )
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct GatewayReportOutputValidationReport {
    pub schema_version: String,
    pub bundle_id: String,
    pub valid: bool,
    pub report_issue_count: u64,
    pub claim_boundary: String,
    pub checked_files: Vec<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum GatewayReportMaterializationError {
    EmptyBundleId,
    InvalidReport(Vec<GatewayReportValidationIssue>),
    EmptyOutputRoot,
    ProtectedOutputRoot,
    OutputRootExistsWithoutOverwrite,
    OutputRootIsFile,
    OutputRootIsSymlink,
    BundleFileIsSymlink(String),
    SidecarIsSymlink(String),
    DeclaredFileTypeMismatch(String),
    UndeclaredFile(String),
    DigestMismatch(String),
    MalformedDeclaredFile(String),
    ManifestSemanticMismatch,
    NonclaimMismatch,
    ValidationReportMismatch,
    Io(String),
    Serialization(String),
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GatewayCorpusOutputRun {
    pub report: GatewayCorpusReport,
    pub output_manifest: GatewayReportOutputManifest,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum GatewayCorpusOutputRunError {
    CorpusValidation(Vec<GatewayAdversarialCorpusIssue>),
    Evaluation(JournalError),
    Materialization(GatewayReportMaterializationError),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AgentAdmissionCandidate {
    pub id: AdmissionCandidateId,
    pub subject: SubjectId,
    pub source_kind: AdmissionSourceKind,
    pub strict_typed: bool,
    pub case: Option<AgentCase>,
    pub proposed_envelope: Option<ClaimEnvelope>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub gateway_action: Option<GatewayActionProposal>,
    #[serde(default, skip_serializing_if = "BTreeSet::is_empty")]
    pub gateway_policy_violations: BTreeSet<GatewayPolicyViolation>,
    pub requested_claim_boundary: AdmissionClaimBoundary,
    pub source_artifact_digests: BTreeSet<ArtifactDigest>,
    pub nonclaims: BTreeSet<NonClaimLabel>,
    pub provider_direct_authority_requested: bool,
    pub accepted_ledger_mutation_requested: bool,
    pub score_axis_population_requested: bool,
    pub external_or_formal_evidence_claimed: bool,
}

impl AgentAdmissionCandidate {
    pub fn from_case(
        id: impl Into<String>,
        case: AgentCase,
        source_artifact_digests: BTreeSet<ArtifactDigest>,
        nonclaims: BTreeSet<NonClaimLabel>,
    ) -> Self {
        Self {
            id: AdmissionCandidateId(id.into()),
            subject: case.subject.clone(),
            source_kind: AdmissionSourceKind::AgentCase,
            strict_typed: true,
            case: Some(case),
            proposed_envelope: None,
            gateway_action: None,
            gateway_policy_violations: BTreeSet::new(),
            requested_claim_boundary: AdmissionClaimBoundary::LocalOnly,
            source_artifact_digests,
            nonclaims,
            provider_direct_authority_requested: false,
            accepted_ledger_mutation_requested: false,
            score_axis_population_requested: false,
            external_or_formal_evidence_claimed: false,
        }
    }

    pub fn from_envelope(
        id: impl Into<String>,
        subject: SubjectId,
        envelope: ClaimEnvelope,
        source_artifact_digests: BTreeSet<ArtifactDigest>,
        nonclaims: BTreeSet<NonClaimLabel>,
    ) -> Self {
        Self {
            id: AdmissionCandidateId(id.into()),
            subject,
            source_kind: AdmissionSourceKind::ClaimEnvelopeProposal,
            strict_typed: true,
            case: None,
            proposed_envelope: Some(envelope),
            gateway_action: None,
            gateway_policy_violations: BTreeSet::new(),
            requested_claim_boundary: AdmissionClaimBoundary::Level1Local,
            source_artifact_digests,
            nonclaims,
            provider_direct_authority_requested: false,
            accepted_ledger_mutation_requested: false,
            score_axis_population_requested: false,
            external_or_formal_evidence_claimed: false,
        }
    }

    pub fn digest(&self) -> Hash {
        hash_tagged("hsai-agent-admission:candidate:v1", self)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AgentAdmissionPolicy {
    pub id: AdmissionPolicyId,
    pub max_claim_boundary: AdmissionClaimBoundary,
    pub required_nonclaims: BTreeSet<NonClaimLabel>,
    pub require_source_artifacts: bool,
    pub allow_provider_direct_authority: bool,
}

impl AgentAdmissionPolicy {
    pub fn local_default(required_nonclaims: BTreeSet<NonClaimLabel>) -> Self {
        Self {
            id: AdmissionPolicyId("hsai-agent-admission-local-v1".to_owned()),
            max_claim_boundary: AdmissionClaimBoundary::Level1Local,
            required_nonclaims,
            require_source_artifacts: true,
            allow_provider_direct_authority: false,
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum PcsmSourceRepoStatus {
    Clean,
    Dirty,
    StagedOnly,
    Ambiguous,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum PcsmVerifierOutcome {
    Pass,
    Fail,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct PcsmVerifierStatus {
    pub name: String,
    pub outcome: PcsmVerifierOutcome,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct PcsmBoundedProofHandoffIntake {
    pub source_repo_remote: String,
    pub source_repo_branch: String,
    pub source_repo_commit: String,
    pub source_repo_status: PcsmSourceRepoStatus,
    pub source_handoff_path: String,
    pub source_handoff_sha256: Hash,
    pub source_handoff_schema: String,
    pub source_handoff_state_slice: String,
    pub bounded_breakthrough_evidence_admitted: bool,
    pub threshold_admitted: bool,
    pub replication_admission_status: String,
    pub blocked_item: String,
    pub pcsm_inputs: u64,
    pub pcsm_accepted: u64,
    pub pcsm_rejected: u64,
    pub pcsm_journal_entries: u64,
    pub provider_direct_authority: bool,
    pub production_authority: bool,
    pub raw_provider_payloads_committed: bool,
    pub local_mlx_surrogate_runtime: bool,
    pub native_pcsm_governed_state: bool,
    pub pcsm_journaled: bool,
    pub verifier_statuses: BTreeSet<PcsmVerifierStatus>,
    pub source_artifact_digests: BTreeSet<ArtifactDigest>,
    pub nonclaims: BTreeSet<NonClaimLabel>,
    pub accepted_ledger_mutation_requested: bool,
    pub official_submission_requested: bool,
    pub external_replay_requested: bool,
    pub score_axis_population_requested: bool,
    pub level2_evidence_requested: bool,
}

impl PcsmBoundedProofHandoffIntake {
    pub fn digest(&self) -> Hash {
        hash_tagged("hsai-agent-admission:pcsm-bounded-proof-intake:v1", self)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum PcsmHandoffIntakeError {
    MissingSourceIdentity(&'static str),
    InvalidSourceCommit,
    SourceRepoNotClean(PcsmSourceRepoStatus),
    UnsafeSourceHandoffPath,
    MissingHandoffDigest,
    BoundedEvidenceNotAdmitted,
    ThresholdAdmitted,
    ReplicationStatusNotBlockedPreflight,
    BlockedItemMismatch,
    MissingPcsmCounts,
    PcsmCountOverflow,
    PcsmCountMismatch,
    ProviderDirectAuthorityClaimed,
    ProductionAuthorityClaimed,
    RawProviderPayloadsCommitted,
    LocalMlxSurrogateMissing,
    NativePcsmGovernanceMissing,
    PcsmJournalMissing,
    MissingVerifierStatus(&'static str),
    FailedVerifierStatus(String),
    DuplicateVerifierStatus(String),
    UnexpectedVerifierStatus(String),
    MissingSourceArtifactDigest,
    InvalidSourceArtifactId(String),
    ZeroSourceArtifactDigest(String),
    ConflictingSourceArtifactDigestId(String),
    ReservedIntakeDigestCollision,
    MissingRequiredNonclaim(String),
    AcceptedLedgerMutationRequested,
    OfficialSubmissionRequested,
    ExternalReplayRequested,
    ScoreAxisPopulationRequested,
    Level2EvidenceRequested,
}

pub fn pcsm_bounded_proof_required_nonclaims() -> BTreeSet<NonClaimLabel> {
    BTreeSet::from([
        NonClaimLabel("not PCSM runtime import".to_owned()),
        NonClaimLabel("not recoverable-ghost artifact import".to_owned()),
        NonClaimLabel("not accepted Evidence Ledger mutation".to_owned()),
        NonClaimLabel("not official benchmark evidence".to_owned()),
        NonClaimLabel("not official benchmark submission".to_owned()),
        NonClaimLabel("not external runtime replication".to_owned()),
        NonClaimLabel("not provider authority".to_owned()),
        NonClaimLabel("not production authority".to_owned()),
        NonClaimLabel("not serving authority".to_owned()),
        NonClaimLabel("not proof".to_owned()),
        NonClaimLabel("not semantic correctness".to_owned()),
        NonClaimLabel("not production readiness".to_owned()),
        NonClaimLabel("not Level2+ evidence".to_owned()),
        NonClaimLabel("no score-axis population".to_owned()),
        NonClaimLabel("full breakthrough threshold not admitted".to_owned()),
    ])
}

pub fn validate_pcsm_bounded_proof_handoff_intake(
    intake: &PcsmBoundedProofHandoffIntake,
) -> Vec<PcsmHandoffIntakeError> {
    let mut errors = Vec::new();

    if intake.source_repo_remote.trim().is_empty() {
        errors.push(PcsmHandoffIntakeError::MissingSourceIdentity(
            "source_repo_remote",
        ));
    }
    if intake.source_repo_branch.trim().is_empty() {
        errors.push(PcsmHandoffIntakeError::MissingSourceIdentity(
            "source_repo_branch",
        ));
    }
    if intake.source_handoff_schema.trim().is_empty() {
        errors.push(PcsmHandoffIntakeError::MissingSourceIdentity(
            "source_handoff_schema",
        ));
    }
    if intake.source_handoff_state_slice.trim().is_empty() {
        errors.push(PcsmHandoffIntakeError::MissingSourceIdentity(
            "source_handoff_state_slice",
        ));
    }
    if !is_full_hex_sha(&intake.source_repo_commit) {
        errors.push(PcsmHandoffIntakeError::InvalidSourceCommit);
    }
    if intake.source_repo_status != PcsmSourceRepoStatus::Clean {
        errors.push(PcsmHandoffIntakeError::SourceRepoNotClean(
            intake.source_repo_status.clone(),
        ));
    }
    if !is_safe_relative_path(&intake.source_handoff_path)
        || intake.source_handoff_path != "docs/pcsm-cl12-bounded-proof-handoff.md"
    {
        errors.push(PcsmHandoffIntakeError::UnsafeSourceHandoffPath);
    }
    if intake.source_handoff_sha256 == Hash([0; 32]) {
        errors.push(PcsmHandoffIntakeError::MissingHandoffDigest);
    }
    if !intake.bounded_breakthrough_evidence_admitted {
        errors.push(PcsmHandoffIntakeError::BoundedEvidenceNotAdmitted);
    }
    if intake.threshold_admitted {
        errors.push(PcsmHandoffIntakeError::ThresholdAdmitted);
    }
    if intake.replication_admission_status != "blocked_preflight_only" {
        errors.push(PcsmHandoffIntakeError::ReplicationStatusNotBlockedPreflight);
    }
    if intake.blocked_item != "live_external_runtime_replication" {
        errors.push(PcsmHandoffIntakeError::BlockedItemMismatch);
    }
    if intake.pcsm_inputs == 0
        || intake.pcsm_accepted == 0
        || intake.pcsm_rejected == 0
        || intake.pcsm_journal_entries == 0
    {
        errors.push(PcsmHandoffIntakeError::MissingPcsmCounts);
    }
    match intake.pcsm_accepted.checked_add(intake.pcsm_rejected) {
        None => errors.push(PcsmHandoffIntakeError::PcsmCountOverflow),
        Some(total)
            if total != intake.pcsm_inputs || intake.pcsm_journal_entries != intake.pcsm_inputs =>
        {
            errors.push(PcsmHandoffIntakeError::PcsmCountMismatch);
        }
        Some(_) => {}
    }
    if intake.provider_direct_authority {
        errors.push(PcsmHandoffIntakeError::ProviderDirectAuthorityClaimed);
    }
    if intake.production_authority {
        errors.push(PcsmHandoffIntakeError::ProductionAuthorityClaimed);
    }
    if intake.raw_provider_payloads_committed {
        errors.push(PcsmHandoffIntakeError::RawProviderPayloadsCommitted);
    }
    if !intake.local_mlx_surrogate_runtime {
        errors.push(PcsmHandoffIntakeError::LocalMlxSurrogateMissing);
    }
    if !intake.native_pcsm_governed_state {
        errors.push(PcsmHandoffIntakeError::NativePcsmGovernanceMissing);
    }
    if !intake.pcsm_journaled {
        errors.push(PcsmHandoffIntakeError::PcsmJournalMissing);
    }

    let required_verifiers: BTreeSet<&str> = REQUIRED_PCSM_VERIFIERS.iter().copied().collect();
    let mut verifier_outcomes = BTreeMap::new();
    for status in &intake.verifier_statuses {
        if !required_verifiers.contains(status.name.as_str()) {
            errors.push(PcsmHandoffIntakeError::UnexpectedVerifierStatus(
                status.name.clone(),
            ));
            continue;
        }
        if verifier_outcomes
            .insert(status.name.as_str(), &status.outcome)
            .is_some()
        {
            errors.push(PcsmHandoffIntakeError::DuplicateVerifierStatus(
                status.name.clone(),
            ));
        }
    }
    for required in REQUIRED_PCSM_VERIFIERS {
        match verifier_outcomes.get(required) {
            Some(status) if **status == PcsmVerifierOutcome::Pass => {}
            Some(_) => errors.push(PcsmHandoffIntakeError::FailedVerifierStatus(
                (*required).to_owned(),
            )),
            None => errors.push(PcsmHandoffIntakeError::MissingVerifierStatus(required)),
        }
    }

    if intake.source_artifact_digests.is_empty() {
        errors.push(PcsmHandoffIntakeError::MissingSourceArtifactDigest);
    }
    for artifact_error in validate_artifact_digests(&intake.source_artifact_digests) {
        match artifact_error {
            ArtifactDigestValidationError::InvalidId(id) => {
                errors.push(PcsmHandoffIntakeError::InvalidSourceArtifactId(id));
            }
            ArtifactDigestValidationError::ZeroDigest(id) => {
                errors.push(PcsmHandoffIntakeError::ZeroSourceArtifactDigest(id));
            }
            ArtifactDigestValidationError::ConflictingId(id) => {
                errors.push(PcsmHandoffIntakeError::ConflictingSourceArtifactDigestId(
                    id,
                ));
            }
        }
    }
    if intake
        .source_artifact_digests
        .iter()
        .any(|digest| digest.id == PCSM_BOUNDED_PROOF_INTAKE_DIGEST_ID)
    {
        errors.push(PcsmHandoffIntakeError::ReservedIntakeDigestCollision);
    }
    for required in pcsm_bounded_proof_required_nonclaims() {
        if !intake.nonclaims.contains(&required) {
            errors.push(PcsmHandoffIntakeError::MissingRequiredNonclaim(required.0));
        }
    }
    if intake.accepted_ledger_mutation_requested {
        errors.push(PcsmHandoffIntakeError::AcceptedLedgerMutationRequested);
    }
    if intake.official_submission_requested {
        errors.push(PcsmHandoffIntakeError::OfficialSubmissionRequested);
    }
    if intake.external_replay_requested {
        errors.push(PcsmHandoffIntakeError::ExternalReplayRequested);
    }
    if intake.score_axis_population_requested {
        errors.push(PcsmHandoffIntakeError::ScoreAxisPopulationRequested);
    }
    if intake.level2_evidence_requested {
        errors.push(PcsmHandoffIntakeError::Level2EvidenceRequested);
    }

    errors
}

pub fn pcsm_bounded_proof_handoff_candidate(
    id: impl Into<String>,
    subject: SubjectId,
    intake: &PcsmBoundedProofHandoffIntake,
) -> Result<AgentAdmissionCandidate, Vec<PcsmHandoffIntakeError>> {
    let errors = validate_pcsm_bounded_proof_handoff_intake(intake);
    if !errors.is_empty() {
        return Err(errors);
    }

    let mut source_artifact_digests = intake.source_artifact_digests.clone();
    source_artifact_digests.insert(ArtifactDigest {
        id: PCSM_BOUNDED_PROOF_INTAKE_DIGEST_ID.to_owned(),
        sha256: intake.digest(),
    });

    Ok(AgentAdmissionCandidate {
        id: AdmissionCandidateId(id.into()),
        subject,
        source_kind: AdmissionSourceKind::PcsmBoundedProofHandoff,
        strict_typed: true,
        case: None,
        proposed_envelope: None,
        gateway_action: None,
        gateway_policy_violations: BTreeSet::new(),
        requested_claim_boundary: AdmissionClaimBoundary::LocalOnly,
        source_artifact_digests,
        nonclaims: intake.nonclaims.clone(),
        provider_direct_authority_requested: intake.provider_direct_authority,
        accepted_ledger_mutation_requested: intake.accepted_ledger_mutation_requested,
        score_axis_population_requested: intake.score_axis_population_requested,
        external_or_formal_evidence_claimed: intake.level2_evidence_requested,
    })
}

const REQUIRED_PCSM_VERIFIERS: &[&str] = &[
    "verify_cl12_local_mlx_pcsm_surrogate",
    "verify_cl12_external_benchmark_replication",
    "verify_breakthrough_threshold_audit",
    "verify_native_pcsm",
    "source_lint_gate",
];

const PCSM_BOUNDED_PROOF_INTAKE_DIGEST_ID: &str = "pcsm-bounded-proof-intake";

#[derive(Clone, Debug, Eq, PartialEq)]
enum ArtifactDigestValidationError {
    InvalidId(String),
    ZeroDigest(String),
    ConflictingId(String),
}

fn validate_artifact_digests(
    digests: &BTreeSet<ArtifactDigest>,
) -> Vec<ArtifactDigestValidationError> {
    let mut errors = Vec::new();
    let mut by_id = BTreeMap::new();
    for digest in digests {
        if !is_portable_artifact_id(&digest.id) {
            errors.push(ArtifactDigestValidationError::InvalidId(digest.id.clone()));
        }
        if digest.sha256 == Hash([0; 32]) {
            errors.push(ArtifactDigestValidationError::ZeroDigest(digest.id.clone()));
        }
        if let Some(existing) = by_id.insert(digest.id.clone(), digest.sha256) {
            if existing != digest.sha256 {
                errors.push(ArtifactDigestValidationError::ConflictingId(
                    digest.id.clone(),
                ));
            }
        }
    }
    errors
}

fn is_portable_artifact_id(id: &str) -> bool {
    let trimmed = id.trim();
    !trimmed.is_empty()
        && trimmed == id
        && !trimmed.contains("..")
        && trimmed
            .chars()
            .all(|ch| ch.is_ascii_alphanumeric() || matches!(ch, '-' | '_' | '.'))
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum AdmissionVerdict {
    Accepted,
    Rejected,
    Quarantined,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AgentAdmissionDecision {
    pub candidate_id: AdmissionCandidateId,
    pub policy_id: AdmissionPolicyId,
    pub verdict: AdmissionVerdict,
    pub reasons: Vec<AdmissionReason>,
    pub candidate_digest: Hash,
    pub accepted_envelope: Option<ClaimEnvelope>,
}

impl AgentAdmissionDecision {
    pub fn digest(&self) -> Hash {
        hash_tagged("hsai-agent-admission:decision:v1", self)
    }
}

pub fn evaluate_admission(
    candidate: &AgentAdmissionCandidate,
    policy: &AgentAdmissionPolicy,
) -> AgentAdmissionDecision {
    let mut reasons = Vec::new();

    if !is_portable_candidate_id(&candidate.id.0) {
        reasons.push(reason("invalid_candidate_id"));
    }
    if candidate.subject.0.trim().is_empty() || candidate.subject.0.trim() != candidate.subject.0 {
        reasons.push(reason("invalid_candidate_subject"));
    }
    match candidate.source_kind {
        AdmissionSourceKind::AgentCase => {
            if candidate.case.is_none() {
                reasons.push(reason("agent_case_payload_required"));
            }
            if candidate.proposed_envelope.is_some() {
                reasons.push(reason("agent_case_envelope_forbidden"));
            }
            if candidate.gateway_action.is_some() {
                reasons.push(reason("agent_case_gateway_action_forbidden"));
            }
            if candidate
                .case
                .as_ref()
                .is_some_and(|case| case.subject != candidate.subject)
            {
                reasons.push(reason("agent_case_subject_mismatch"));
            }
        }
        AdmissionSourceKind::ClaimEnvelopeProposal => {
            if candidate.case.is_some() {
                reasons.push(reason("claim_envelope_case_forbidden"));
            }
            if candidate.proposed_envelope.is_none() {
                reasons.push(reason("claim_envelope_payload_required"));
            }
            if candidate.gateway_action.is_some() {
                reasons.push(reason("claim_envelope_gateway_action_forbidden"));
            }
        }
        AdmissionSourceKind::ProviderResponse => {
            if candidate.case.is_some() {
                reasons.push(reason("provider_response_case_forbidden"));
            }
            if candidate.proposed_envelope.is_some() {
                reasons.push(reason("provider_response_envelope_forbidden"));
            }
            if candidate.gateway_action.is_some() {
                reasons.push(reason("provider_response_gateway_action_forbidden"));
            }
            if candidate.strict_typed {
                reasons.push(reason("provider_response_requires_typed_conversion"));
            }
        }
        AdmissionSourceKind::BenchmarkResultProposal => {
            if candidate.case.is_some() {
                reasons.push(reason("benchmark_result_case_forbidden"));
            }
            if candidate.proposed_envelope.is_some() {
                reasons.push(reason("benchmark_result_envelope_forbidden"));
            }
            if candidate.gateway_action.is_some() {
                reasons.push(reason("benchmark_result_gateway_action_forbidden"));
            }
        }
        AdmissionSourceKind::PcsmBoundedProofHandoff => {
            if candidate.case.is_some() {
                reasons.push(reason("pcsm_handoff_case_forbidden"));
            }
            if candidate.proposed_envelope.is_some() {
                reasons.push(reason("pcsm_handoff_envelope_forbidden"));
            }
            if candidate.gateway_action.is_some() {
                reasons.push(reason("pcsm_handoff_gateway_action_forbidden"));
            }
        }
        AdmissionSourceKind::GatewayActionProposal => {
            if candidate.case.is_some() {
                reasons.push(reason("gateway_action_case_forbidden"));
            }
            if candidate.proposed_envelope.is_some() {
                reasons.push(reason("gateway_action_envelope_forbidden"));
            }
            match &candidate.gateway_action {
                Some(action) if action.subject == candidate.subject => {}
                Some(_) => reasons.push(reason("gateway_action_subject_mismatch")),
                None => reasons.push(reason("gateway_action_payload_required")),
            }
        }
    }
    for violation in &candidate.gateway_policy_violations {
        reasons.push(gateway_violation_reason(violation));
    }
    if candidate.requested_claim_boundary != expected_claim_boundary(&candidate.source_kind) {
        reasons.push(reason("source_kind_claim_boundary_mismatch"));
    }
    let has_reserved_pcsm_digest = candidate
        .source_artifact_digests
        .iter()
        .any(|digest| digest.id == PCSM_BOUNDED_PROOF_INTAKE_DIGEST_ID);
    if candidate.source_kind == AdmissionSourceKind::PcsmBoundedProofHandoff {
        if !has_reserved_pcsm_digest {
            reasons.push(reason("pcsm_intake_digest_required"));
        }
    } else if has_reserved_pcsm_digest {
        reasons.push(reason("pcsm_intake_digest_forbidden"));
    }
    for artifact_error in validate_artifact_digests(&candidate.source_artifact_digests) {
        match artifact_error {
            ArtifactDigestValidationError::InvalidId(id) => {
                reasons.push(AdmissionReason(format!("invalid_source_artifact_id:{id}")))
            }
            ArtifactDigestValidationError::ZeroDigest(id) => {
                reasons.push(AdmissionReason(format!("zero_source_artifact_digest:{id}")))
            }
            ArtifactDigestValidationError::ConflictingId(id) => reasons.push(AdmissionReason(
                format!("conflicting_source_artifact_digest_id:{id}"),
            )),
        }
    }
    if !candidate.strict_typed {
        reasons.push(reason("strict_typed_candidate_required"));
    }
    if candidate.provider_direct_authority_requested && !policy.allow_provider_direct_authority {
        reasons.push(reason("provider_direct_authority_forbidden"));
    }
    if candidate.requested_claim_boundary > policy.max_claim_boundary {
        reasons.push(reason("claim_boundary_elevation_forbidden"));
    }
    if policy.require_source_artifacts && candidate.source_artifact_digests.is_empty() {
        reasons.push(reason("source_artifact_digest_required"));
    }
    for required in &policy.required_nonclaims {
        if !candidate.nonclaims.contains(required) {
            reasons.push(AdmissionReason(format!("missing_nonclaim:{}", required.0)));
        }
    }
    if candidate.accepted_ledger_mutation_requested {
        reasons.push(reason("accepted_ledger_mutation_requires_separate_phase"));
    }
    if candidate.score_axis_population_requested {
        reasons.push(reason("score_axis_population_forbidden"));
    }
    if candidate.external_or_formal_evidence_claimed {
        reasons.push(reason("external_or_formal_evidence_claim_forbidden"));
    }

    let verdict = if reasons.is_empty() {
        AdmissionVerdict::Accepted
    } else if candidate.strict_typed {
        AdmissionVerdict::Rejected
    } else {
        AdmissionVerdict::Quarantined
    };
    let accepted_envelope = if verdict == AdmissionVerdict::Accepted
        && candidate.source_kind == AdmissionSourceKind::ClaimEnvelopeProposal
    {
        candidate.proposed_envelope.clone()
    } else {
        None
    };

    AgentAdmissionDecision {
        candidate_id: candidate.id.clone(),
        policy_id: policy.id.clone(),
        verdict,
        reasons,
        candidate_digest: candidate.digest(),
        accepted_envelope,
    }
}

fn is_portable_candidate_id(id: &str) -> bool {
    is_portable_artifact_id(id)
}

fn expected_claim_boundary(source_kind: &AdmissionSourceKind) -> AdmissionClaimBoundary {
    match source_kind {
        AdmissionSourceKind::ClaimEnvelopeProposal => AdmissionClaimBoundary::Level1Local,
        AdmissionSourceKind::AgentCase
        | AdmissionSourceKind::ProviderResponse
        | AdmissionSourceKind::BenchmarkResultProposal
        | AdmissionSourceKind::PcsmBoundedProofHandoff
        | AdmissionSourceKind::GatewayActionProposal => AdmissionClaimBoundary::LocalOnly,
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AgentAdmissionJournalEntry {
    pub sequence_number: u64,
    pub previous_entry_digest: Option<Hash>,
    pub candidate_id: AdmissionCandidateId,
    pub candidate_digest: Hash,
    pub decision_digest: Hash,
    pub source_artifact_digests: BTreeSet<ArtifactDigest>,
    pub candidate: AgentAdmissionCandidate,
    pub policy: AgentAdmissionPolicy,
    pub decision: AgentAdmissionDecision,
}

impl AgentAdmissionJournalEntry {
    pub fn digest(&self) -> Hash {
        hash_tagged("hsai-agent-admission:journal-entry:v1", self)
    }
}

#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
pub struct AgentAdmissionJournal {
    pub entries: Vec<AgentAdmissionJournalEntry>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdmissionJournalMaterializationRequest {
    pub bundle_id: String,
    pub created_at_unix: u64,
    pub admission_policy_id: AdmissionPolicyId,
    pub journal_tip_digest_before: Option<Hash>,
    pub nonclaims: BTreeSet<NonClaimLabel>,
    pub overwrite: bool,
    pub protected_roots: Vec<PathBuf>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AdmissionJournalBundleManifest {
    pub schema_version: String,
    pub bundle_id: String,
    pub created_at_unix: u64,
    pub admission_policy_id: AdmissionPolicyId,
    pub journal_tip_digest_before: Option<Hash>,
    pub journal_tip_digest_after: Option<Hash>,
    pub entry_count: u64,
    pub accepted_count: u64,
    pub rejected_count: u64,
    pub quarantined_count: u64,
    pub declared_files: Vec<String>,
    pub declared_file_digests: BTreeMap<String, Hash>,
    pub claim_boundary: String,
    pub non_claims: BTreeSet<NonClaimLabel>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AdmissionDecisionReviewRow {
    pub candidate_id: AdmissionCandidateId,
    pub policy_id: AdmissionPolicyId,
    pub verdict: AdmissionVerdict,
    pub reason_codes: Vec<AdmissionReason>,
    pub candidate_digest: Hash,
    pub decision_digest: Hash,
    pub source_artifact_digest_ids: Vec<String>,
    pub accepted_envelope_exists: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AdmissionSourceDigestIndex {
    pub source_artifact_digests: BTreeSet<ArtifactDigest>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AdmissionJournalRedactionReport {
    pub retains_credentials_or_secrets: bool,
    pub retains_raw_provider_responses: bool,
    pub retains_raw_request_bodies: bool,
    pub retains_raw_network_transcripts: bool,
    pub retains_raw_attestation_quotes: bool,
    pub retains_raw_dcap_collateral: bool,
    pub retains_raw_jwks_or_openid_documents: bool,
    pub retains_raw_tls_exporter_values: bool,
    pub retains_benchmark_result_bodies: bool,
    pub retains_accepted_evidence_ledger_json: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AdmissionJournalValidationReport {
    pub schema_version: String,
    pub bundle_id: String,
    pub valid: bool,
    pub journal_error_count: u64,
    pub claim_boundary: String,
    pub checked_files: Vec<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum AdmissionJournalMaterializationError {
    EmptyBundleId,
    MissingRequiredNonclaim(String),
    InvalidJournal(Vec<JournalError>),
    StaleJournalTip,
    EmptyOutputRoot,
    ProtectedOutputRoot,
    OutputRootExistsWithoutOverwrite,
    OutputRootIsFile,
    OutputRootIsSymlink,
    BundleFileIsSymlink(String),
    SidecarIsSymlink(String),
    DeclaredFileTypeMismatch(String),
    UndeclaredFile(String),
    DigestMismatch(String),
    MalformedDeclaredFile(String),
    ManifestSemanticMismatch,
    InvalidSerializedJournal(Vec<JournalError>),
    DecisionIndexMismatch,
    SourceDigestIndexMismatch,
    NonclaimMismatch,
    UnsafeRedactionReport,
    ValidationReportMismatch,
    Io(String),
    Serialization(String),
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum JournalError {
    CandidateMismatch,
    CandidateDigestMismatch,
    CandidateSnapshotMismatch,
    PolicySnapshotMismatch,
    SourceArtifactSnapshotMismatch,
    DecisionEvaluationMismatch,
    DecisionDigestMismatch,
    SequenceMismatch { expected: u64, actual: u64 },
    PreviousDigestMismatch,
    ReplayedCandidate(Hash),
    NonAcceptedVerdictRetainsEnvelope,
    InvalidExistingJournal,
}

impl AgentAdmissionJournal {
    pub fn append_decision(
        &mut self,
        candidate: &AgentAdmissionCandidate,
        policy: &AgentAdmissionPolicy,
        decision: AgentAdmissionDecision,
    ) -> Result<&AgentAdmissionJournalEntry, JournalError> {
        if !self.validate().is_empty() {
            return Err(JournalError::InvalidExistingJournal);
        }
        if decision.candidate_id != candidate.id {
            return Err(JournalError::CandidateMismatch);
        }
        if decision.candidate_digest != candidate.digest() {
            return Err(JournalError::CandidateDigestMismatch);
        }
        if decision != evaluate_admission(candidate, policy) {
            return Err(JournalError::DecisionEvaluationMismatch);
        }
        if self
            .entries
            .iter()
            .any(|entry| entry.candidate_digest == decision.candidate_digest)
        {
            return Err(JournalError::ReplayedCandidate(decision.candidate_digest));
        }

        let entry = AgentAdmissionJournalEntry {
            sequence_number: self.entries.len() as u64,
            previous_entry_digest: self.entries.last().map(AgentAdmissionJournalEntry::digest),
            candidate_id: candidate.id.clone(),
            candidate_digest: candidate.digest(),
            decision_digest: decision.digest(),
            source_artifact_digests: candidate.source_artifact_digests.clone(),
            candidate: candidate.clone(),
            policy: policy.clone(),
            decision,
        };
        self.entries.push(entry);
        Ok(self
            .entries
            .last()
            .expect("entry was just appended and must exist"))
    }

    pub fn validate(&self) -> Vec<JournalError> {
        let mut errors = Vec::new();
        let mut seen = BTreeSet::new();
        let mut previous_digest = None;

        for (index, entry) in self.entries.iter().enumerate() {
            let expected_sequence = index as u64;
            if entry.sequence_number != expected_sequence {
                errors.push(JournalError::SequenceMismatch {
                    expected: expected_sequence,
                    actual: entry.sequence_number,
                });
            }
            if entry.previous_entry_digest != previous_digest {
                errors.push(JournalError::PreviousDigestMismatch);
            }
            if entry.decision.candidate_id != entry.candidate_id {
                errors.push(JournalError::CandidateMismatch);
            }
            if entry.candidate.id != entry.candidate_id {
                errors.push(JournalError::CandidateSnapshotMismatch);
            }
            if entry.candidate.digest() != entry.candidate_digest {
                errors.push(JournalError::CandidateDigestMismatch);
            }
            if entry.decision.candidate_digest != entry.candidate_digest {
                errors.push(JournalError::CandidateDigestMismatch);
            }
            if entry.policy.id != entry.decision.policy_id {
                errors.push(JournalError::PolicySnapshotMismatch);
            }
            if entry.source_artifact_digests != entry.candidate.source_artifact_digests {
                errors.push(JournalError::SourceArtifactSnapshotMismatch);
            }
            if entry.decision != evaluate_admission(&entry.candidate, &entry.policy) {
                errors.push(JournalError::DecisionEvaluationMismatch);
            }
            if entry.decision.digest() != entry.decision_digest {
                errors.push(JournalError::DecisionDigestMismatch);
            }
            if entry.decision.verdict != AdmissionVerdict::Accepted
                && entry.decision.accepted_envelope.is_some()
            {
                errors.push(JournalError::NonAcceptedVerdictRetainsEnvelope);
            }
            if !seen.insert(entry.candidate_digest) {
                errors.push(JournalError::ReplayedCandidate(entry.candidate_digest));
            }
            previous_digest = Some(entry.digest());
        }

        errors
    }
}

pub fn admission_journal_required_nonclaims() -> BTreeSet<NonClaimLabel> {
    BTreeSet::from([
        NonClaimLabel("not accepted Evidence Ledger mutation".to_owned()),
        NonClaimLabel("not official benchmark evidence".to_owned()),
        NonClaimLabel("not official benchmark submission".to_owned()),
        NonClaimLabel("not external replay evidence".to_owned()),
        NonClaimLabel("not provider evidence".to_owned()),
        NonClaimLabel("not proof".to_owned()),
        NonClaimLabel("not semantic correctness".to_owned()),
        NonClaimLabel("not production readiness".to_owned()),
        NonClaimLabel("not Level2+ evidence".to_owned()),
        NonClaimLabel("no score-axis population".to_owned()),
    ])
}

pub fn materialize_admission_journal_bundle(
    output_root: &Path,
    journal: &AgentAdmissionJournal,
    request: &AdmissionJournalMaterializationRequest,
) -> Result<AdmissionJournalBundleManifest, AdmissionJournalMaterializationError> {
    validate_materialization_request(output_root, journal, request)?;

    let bundle_dir = output_root.join("admission-journal");
    let staging_root = staging_root_for(output_root, &request.bundle_id)?;
    if staging_root.exists() {
        remove_dir_all_checked(&staging_root)?;
    }
    fs::create_dir_all(staging_root.join("admission-journal")).map_err(materialization_io_error)?;

    let files = build_admission_journal_bundle_files(journal, request)?;
    for (logical_path, bytes) in &files {
        let target = staging_root.join(logical_path);
        if let Some(parent) = target.parent() {
            fs::create_dir_all(parent).map_err(materialization_io_error)?;
        }
        fs::write(&target, bytes).map_err(materialization_io_error)?;
        fs::write(
            sidecar_path(&target),
            hash_hex(hash_bytes(bytes)).into_bytes(),
        )
        .map_err(materialization_io_error)?;
    }

    if output_root.exists() {
        if !request.overwrite {
            remove_dir_all_checked(&staging_root)?;
            return Err(AdmissionJournalMaterializationError::OutputRootExistsWithoutOverwrite);
        }
        remove_dir_all_checked(output_root)?;
    }
    fs::rename(&staging_root, output_root).map_err(materialization_io_error)?;

    let manifest = read_admission_journal_bundle(output_root)?;
    if !bundle_dir.exists() {
        return Err(AdmissionJournalMaterializationError::Io(
            "admission-journal directory was not materialized".to_owned(),
        ));
    }
    Ok(manifest)
}

pub fn read_admission_journal_bundle(
    output_root: &Path,
) -> Result<AdmissionJournalBundleManifest, AdmissionJournalMaterializationError> {
    let output_metadata = fs::symlink_metadata(output_root).map_err(materialization_io_error)?;
    if output_metadata.file_type().is_symlink() {
        return Err(AdmissionJournalMaterializationError::OutputRootIsSymlink);
    }
    if !output_metadata.is_dir() {
        return Err(AdmissionJournalMaterializationError::OutputRootIsFile);
    }
    let bundle_dir = output_root.join("admission-journal");
    let bundle_metadata = fs::symlink_metadata(&bundle_dir).map_err(materialization_io_error)?;
    if bundle_metadata.file_type().is_symlink() {
        return Err(AdmissionJournalMaterializationError::BundleFileIsSymlink(
            "admission-journal".to_owned(),
        ));
    }
    if !bundle_metadata.is_dir() {
        return Err(
            AdmissionJournalMaterializationError::DeclaredFileTypeMismatch(
                "admission-journal".to_owned(),
            ),
        );
    }
    reject_undeclared_bundle_files(output_root)?;
    let mut file_bytes = BTreeMap::new();
    for logical_path in ADMISSION_JOURNAL_DECLARED_FILES {
        let path = output_root.join(logical_path);
        let metadata = fs::symlink_metadata(&path).map_err(materialization_io_error)?;
        if metadata.file_type().is_symlink() {
            return Err(AdmissionJournalMaterializationError::BundleFileIsSymlink(
                (*logical_path).to_owned(),
            ));
        }
        if !metadata.is_file() {
            return Err(
                AdmissionJournalMaterializationError::DeclaredFileTypeMismatch(
                    (*logical_path).to_owned(),
                ),
            );
        }
        let sidecar = sidecar_path(&path);
        let sidecar_metadata = fs::symlink_metadata(&sidecar).map_err(materialization_io_error)?;
        if sidecar_metadata.file_type().is_symlink() {
            return Err(AdmissionJournalMaterializationError::SidecarIsSymlink(
                format!("{logical_path}.sha256"),
            ));
        }
        if !sidecar_metadata.is_file() {
            return Err(
                AdmissionJournalMaterializationError::DeclaredFileTypeMismatch(format!(
                    "{logical_path}.sha256"
                )),
            );
        }
        let bytes = fs::read(&path).map_err(materialization_io_error)?;
        let expected = fs::read_to_string(sidecar).map_err(materialization_io_error)?;
        if expected != hash_hex(hash_bytes(&bytes)) {
            return Err(AdmissionJournalMaterializationError::DigestMismatch(
                (*logical_path).to_owned(),
            ));
        }
        file_bytes.insert((*logical_path).to_owned(), bytes);
    }

    validate_admission_journal_bundle_semantics(&file_bytes)
}

fn validate_admission_journal_bundle_semantics(
    files: &BTreeMap<String, Vec<u8>>,
) -> Result<AdmissionJournalBundleManifest, AdmissionJournalMaterializationError> {
    let manifest: AdmissionJournalBundleManifest =
        parse_declared_json(files, "admission-journal/manifest.json")?;
    let journal: AgentAdmissionJournal =
        parse_declared_json(files, "admission-journal/journal.json")?;
    let journal_errors = journal.validate();
    if !journal_errors.is_empty() {
        return Err(AdmissionJournalMaterializationError::InvalidSerializedJournal(journal_errors));
    }

    validate_manifest_semantics(&manifest, &journal, files)?;

    let decisions_bytes = declared_bytes(files, "admission-journal/decisions.jsonl")?;
    let mut parsed_rows = Vec::new();
    if !decisions_bytes.is_empty() {
        if !decisions_bytes.ends_with(b"\n") {
            return Err(AdmissionJournalMaterializationError::DecisionIndexMismatch);
        }
        for line in decisions_bytes[..decisions_bytes.len() - 1].split(|byte| *byte == b'\n') {
            if line.is_empty() {
                return Err(AdmissionJournalMaterializationError::DecisionIndexMismatch);
            }
            parsed_rows.push(parse_strict_json_bytes::<AdmissionDecisionReviewRow>(
                line,
                "admission-journal/decisions.jsonl",
            )?);
        }
    }
    let expected_rows = decision_rows(&journal);
    if parsed_rows != expected_rows {
        return Err(AdmissionJournalMaterializationError::DecisionIndexMismatch);
    }

    let source_index: AdmissionSourceDigestIndex =
        parse_declared_json(files, "admission-journal/source-digests.json")?;
    let expected_source_index = source_digest_index(&journal);
    if source_index != expected_source_index
        || has_conflicting_artifact_digest_ids(&source_index.source_artifact_digests)
    {
        return Err(AdmissionJournalMaterializationError::SourceDigestIndexMismatch);
    }

    let nonclaims_bytes = declared_bytes(files, "admission-journal/non-claims.md")?;
    if nonclaims_bytes != nonclaims_markdown(&manifest.non_claims).as_bytes() {
        return Err(AdmissionJournalMaterializationError::NonclaimMismatch);
    }

    let redaction: AdmissionJournalRedactionReport =
        parse_declared_json(files, "admission-journal/redaction-report.json")?;
    if redaction != redaction_report() {
        return Err(AdmissionJournalMaterializationError::UnsafeRedactionReport);
    }

    let validation: AdmissionJournalValidationReport =
        parse_declared_json(files, "admission-journal/validation-report.json")?;
    let expected_validation = AdmissionJournalValidationReport {
        schema_version: "hsai-admission-journal-validation-v1".to_owned(),
        bundle_id: manifest.bundle_id.clone(),
        valid: true,
        journal_error_count: 0,
        claim_boundary: ADMISSION_JOURNAL_CLAIM_BOUNDARY.to_owned(),
        checked_files: canonical_declared_files(),
    };
    if validation != expected_validation {
        return Err(AdmissionJournalMaterializationError::ValidationReportMismatch);
    }

    Ok(manifest)
}

fn validate_manifest_semantics(
    manifest: &AdmissionJournalBundleManifest,
    journal: &AgentAdmissionJournal,
    files: &BTreeMap<String, Vec<u8>>,
) -> Result<(), AdmissionJournalMaterializationError> {
    let expected_digest_paths: BTreeSet<String> = ADMISSION_JOURNAL_DECLARED_FILES
        .iter()
        .filter(|path| **path != "admission-journal/manifest.json")
        .map(|path| (*path).to_owned())
        .collect();
    let actual_digest_paths: BTreeSet<String> =
        manifest.declared_file_digests.keys().cloned().collect();
    let required_nonclaims = admission_journal_required_nonclaims();
    let first_previous_tip = journal
        .entries
        .first()
        .and_then(|entry| entry.previous_entry_digest);

    if manifest.schema_version != "hsai-admission-journal-bundle-v1"
        || manifest.bundle_id.trim().is_empty()
        || !is_safe_relative_path(&manifest.bundle_id)
        || manifest.bundle_id.contains(['/', '\\'])
        || manifest.declared_files != canonical_declared_files()
        || actual_digest_paths != expected_digest_paths
        || manifest.claim_boundary != ADMISSION_JOURNAL_CLAIM_BOUNDARY
        || !required_nonclaims.is_subset(&manifest.non_claims)
        || manifest.journal_tip_digest_before != first_previous_tip
        || manifest.journal_tip_digest_after
            != journal
                .entries
                .last()
                .map(AgentAdmissionJournalEntry::digest)
        || manifest.entry_count != journal.entries.len() as u64
        || manifest.accepted_count != verdict_count(journal, AdmissionVerdict::Accepted)
        || manifest.rejected_count != verdict_count(journal, AdmissionVerdict::Rejected)
        || manifest.quarantined_count != verdict_count(journal, AdmissionVerdict::Quarantined)
        || journal
            .entries
            .iter()
            .any(|entry| entry.decision.policy_id != manifest.admission_policy_id)
    {
        return Err(AdmissionJournalMaterializationError::ManifestSemanticMismatch);
    }

    for (logical_path, expected_digest) in &manifest.declared_file_digests {
        if hash_bytes(declared_bytes(files, logical_path)?) != *expected_digest {
            return Err(AdmissionJournalMaterializationError::ManifestSemanticMismatch);
        }
    }
    Ok(())
}

fn canonical_declared_files() -> Vec<String> {
    ADMISSION_JOURNAL_DECLARED_FILES
        .iter()
        .map(|value| (*value).to_owned())
        .collect()
}

fn verdict_count(journal: &AgentAdmissionJournal, verdict: AdmissionVerdict) -> u64 {
    journal
        .entries
        .iter()
        .filter(|entry| entry.decision.verdict == verdict)
        .count() as u64
}

fn declared_bytes<'a>(
    files: &'a BTreeMap<String, Vec<u8>>,
    logical_path: &str,
) -> Result<&'a [u8], AdmissionJournalMaterializationError> {
    files.get(logical_path).map(Vec::as_slice).ok_or_else(|| {
        AdmissionJournalMaterializationError::Io(format!("declared file missing: {logical_path}"))
    })
}

fn parse_declared_json<T: for<'de> Deserialize<'de> + Serialize>(
    files: &BTreeMap<String, Vec<u8>>,
    logical_path: &str,
) -> Result<T, AdmissionJournalMaterializationError> {
    parse_strict_json_bytes(declared_bytes(files, logical_path)?, logical_path)
}

fn parse_json_value_rejecting_duplicate_keys(bytes: &[u8]) -> Result<serde_json::Value, ()> {
    let mut parser = DuplicateRejectingJsonParser::new(bytes);
    let value = parser.parse_value()?;
    parser.skip_whitespace();
    if parser.peek().is_some() {
        return Err(());
    }
    Ok(value)
}

struct DuplicateRejectingJsonParser<'a> {
    input: &'a [u8],
    pos: usize,
}

impl<'a> DuplicateRejectingJsonParser<'a> {
    fn new(input: &'a [u8]) -> Self {
        Self { input, pos: 0 }
    }

    fn remaining(&self) -> &'a [u8] {
        &self.input[self.pos..]
    }

    fn peek(&self) -> Option<u8> {
        self.remaining().first().copied()
    }

    fn bump(&mut self) -> Option<u8> {
        let byte = self.peek()?;
        self.pos += 1;
        Some(byte)
    }

    fn skip_whitespace(&mut self) {
        while matches!(self.peek(), Some(b' ' | b'\n' | b'\r' | b'\t')) {
            self.pos += 1;
        }
    }

    fn expect_byte(&mut self, expected: u8) -> Result<(), ()> {
        if self.bump() == Some(expected) {
            Ok(())
        } else {
            Err(())
        }
    }

    fn parse_value(&mut self) -> Result<serde_json::Value, ()> {
        self.skip_whitespace();
        match self.peek() {
            Some(b'n') => self.parse_null(),
            Some(b't') | Some(b'f') => self.parse_bool(),
            Some(b'"') => self.parse_string().map(serde_json::Value::String),
            Some(b'[') => self.parse_array(),
            Some(b'{') => self.parse_object(),
            Some(b'0'..=b'9') | Some(b'-') => self.parse_number(),
            _ => Err(()),
        }
    }

    fn parse_null(&mut self) -> Result<serde_json::Value, ()> {
        if self.remaining().starts_with(b"null") {
            self.pos += 4;
            Ok(serde_json::Value::Null)
        } else {
            Err(())
        }
    }

    fn parse_bool(&mut self) -> Result<serde_json::Value, ()> {
        if self.remaining().starts_with(b"true") {
            self.pos += 4;
            Ok(serde_json::Value::Bool(true))
        } else if self.remaining().starts_with(b"false") {
            self.pos += 5;
            Ok(serde_json::Value::Bool(false))
        } else {
            Err(())
        }
    }

    fn parse_string(&mut self) -> Result<String, ()> {
        let start = self.pos;
        self.expect_byte(b'"')?;
        loop {
            let byte = self.bump().ok_or(())?;
            match byte {
                b'"' => {
                    return serde_json::from_slice(&self.input[start..self.pos]).map_err(|_| ());
                }
                b'\\' => {
                    self.bump().ok_or(())?;
                }
                _ => {}
            }
        }
    }

    fn parse_number(&mut self) -> Result<serde_json::Value, ()> {
        let start = self.pos;
        if self.peek() == Some(b'-') {
            self.pos += 1;
        }
        if self.peek() == Some(b'0') {
            self.pos += 1;
        } else {
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.pos += 1;
            }
        }
        if self.peek() == Some(b'.') {
            self.pos += 1;
            if !matches!(self.peek(), Some(b'0'..=b'9')) {
                return Err(());
            }
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.pos += 1;
            }
        }
        if matches!(self.peek(), Some(b'e' | b'E')) {
            self.pos += 1;
            if matches!(self.peek(), Some(b'+' | b'-')) {
                self.pos += 1;
            }
            if !matches!(self.peek(), Some(b'0'..=b'9')) {
                return Err(());
            }
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.pos += 1;
            }
        }
        let number_text = std::str::from_utf8(&self.input[start..self.pos]).map_err(|_| ())?;
        let number = serde_json::Number::from_str(number_text).map_err(|_| ())?;
        Ok(serde_json::Value::Number(number))
    }

    fn parse_array(&mut self) -> Result<serde_json::Value, ()> {
        self.expect_byte(b'[')?;
        self.skip_whitespace();
        let mut values = Vec::new();
        if self.peek() == Some(b']') {
            self.pos += 1;
            return Ok(serde_json::Value::Array(values));
        }
        loop {
            values.push(self.parse_value()?);
            self.skip_whitespace();
            match self.peek() {
                Some(b',') => {
                    self.pos += 1;
                    self.skip_whitespace();
                }
                Some(b']') => {
                    self.pos += 1;
                    break;
                }
                _ => return Err(()),
            }
        }
        Ok(serde_json::Value::Array(values))
    }

    fn parse_object(&mut self) -> Result<serde_json::Value, ()> {
        self.expect_byte(b'{')?;
        self.skip_whitespace();
        let mut map = serde_json::Map::new();
        let mut keys = BTreeSet::new();
        if self.peek() == Some(b'}') {
            self.pos += 1;
            return Ok(serde_json::Value::Object(map));
        }
        loop {
            self.skip_whitespace();
            let key = self.parse_string()?;
            if !keys.insert(key.clone()) {
                return Err(());
            }
            self.skip_whitespace();
            self.expect_byte(b':')?;
            let value = self.parse_value()?;
            map.insert(key, value);
            self.skip_whitespace();
            match self.peek() {
                Some(b',') => {
                    self.pos += 1;
                    self.skip_whitespace();
                }
                Some(b'}') => {
                    self.pos += 1;
                    break;
                }
                _ => return Err(()),
            }
        }
        Ok(serde_json::Value::Object(map))
    }
}

fn parse_strict_json_bytes<T: for<'de> Deserialize<'de> + Serialize>(
    bytes: &[u8],
    logical_path: &str,
) -> Result<T, AdmissionJournalMaterializationError> {
    let original = parse_json_value_rejecting_duplicate_keys(bytes).map_err(|_| {
        AdmissionJournalMaterializationError::MalformedDeclaredFile(logical_path.to_owned())
    })?;
    let parsed: T = serde_json::from_value(original.clone()).map_err(|_| {
        AdmissionJournalMaterializationError::MalformedDeclaredFile(logical_path.to_owned())
    })?;
    let canonical = serde_json::to_value(&parsed).map_err(materialization_serde_error)?;
    if canonical != original {
        return Err(AdmissionJournalMaterializationError::MalformedDeclaredFile(
            logical_path.to_owned(),
        ));
    }
    Ok(parsed)
}

fn has_conflicting_artifact_digest_ids(digests: &BTreeSet<ArtifactDigest>) -> bool {
    validate_artifact_digests(digests)
        .iter()
        .any(|error| matches!(error, ArtifactDigestValidationError::ConflictingId(_)))
}

fn validate_materialization_request(
    output_root: &Path,
    journal: &AgentAdmissionJournal,
    request: &AdmissionJournalMaterializationRequest,
) -> Result<(), AdmissionJournalMaterializationError> {
    if request.bundle_id.trim().is_empty() {
        return Err(AdmissionJournalMaterializationError::EmptyBundleId);
    }
    if !is_safe_relative_path(&request.bundle_id) || request.bundle_id.contains(['/', '\\']) {
        return Err(AdmissionJournalMaterializationError::EmptyBundleId);
    }
    for required in admission_journal_required_nonclaims() {
        if !request.nonclaims.contains(&required) {
            return Err(AdmissionJournalMaterializationError::MissingRequiredNonclaim(required.0));
        }
    }
    let journal_errors = journal.validate();
    if !journal_errors.is_empty() {
        return Err(AdmissionJournalMaterializationError::InvalidJournal(
            journal_errors,
        ));
    }
    if has_conflicting_artifact_digest_ids(&source_digest_index(journal).source_artifact_digests) {
        return Err(AdmissionJournalMaterializationError::SourceDigestIndexMismatch);
    }
    if journal
        .entries
        .iter()
        .any(|entry| entry.decision.policy_id != request.admission_policy_id)
    {
        return Err(AdmissionJournalMaterializationError::ManifestSemanticMismatch);
    }
    let first_previous_tip = journal
        .entries
        .first()
        .and_then(|entry| entry.previous_entry_digest);
    if request.journal_tip_digest_before != first_previous_tip {
        return Err(AdmissionJournalMaterializationError::StaleJournalTip);
    }
    validate_output_root(output_root, &request.protected_roots, request.overwrite)
}

fn validate_output_root(
    output_root: &Path,
    protected_roots: &[PathBuf],
    overwrite: bool,
) -> Result<(), AdmissionJournalMaterializationError> {
    if output_root.as_os_str().is_empty() {
        return Err(AdmissionJournalMaterializationError::EmptyOutputRoot);
    }
    if output_root.exists() {
        let metadata = fs::symlink_metadata(output_root).map_err(materialization_io_error)?;
        if metadata.file_type().is_symlink() {
            return Err(AdmissionJournalMaterializationError::OutputRootIsSymlink);
        }
        if metadata.is_file() {
            return Err(AdmissionJournalMaterializationError::OutputRootIsFile);
        }
        if !overwrite {
            return Err(AdmissionJournalMaterializationError::OutputRootExistsWithoutOverwrite);
        }
    }
    let normalized_output = normalize_for_prefix_check(output_root)?;
    for protected in protected_roots {
        let normalized_protected = normalize_for_prefix_check(protected)?;
        if normalized_output == normalized_protected
            || normalized_output.starts_with(&normalized_protected)
            || normalized_protected.starts_with(&normalized_output)
        {
            return Err(AdmissionJournalMaterializationError::ProtectedOutputRoot);
        }
    }
    Ok(())
}

fn build_admission_journal_bundle_files(
    journal: &AgentAdmissionJournal,
    request: &AdmissionJournalMaterializationRequest,
) -> Result<BTreeMap<String, Vec<u8>>, AdmissionJournalMaterializationError> {
    let journal_bytes = serde_json::to_vec_pretty(journal).map_err(materialization_serde_error)?;
    let decisions_bytes = decision_rows_jsonl(journal)?;
    let source_digest_bytes = serde_json::to_vec_pretty(&source_digest_index(journal))
        .map_err(materialization_serde_error)?;
    let non_claims_bytes = nonclaims_markdown(&request.nonclaims).into_bytes();
    let redaction_report_bytes =
        serde_json::to_vec_pretty(&redaction_report()).map_err(materialization_serde_error)?;
    let validation_report_bytes = serde_json::to_vec_pretty(&AdmissionJournalValidationReport {
        schema_version: "hsai-admission-journal-validation-v1".to_owned(),
        bundle_id: request.bundle_id.clone(),
        valid: true,
        journal_error_count: 0,
        claim_boundary: ADMISSION_JOURNAL_CLAIM_BOUNDARY.to_owned(),
        checked_files: ADMISSION_JOURNAL_DECLARED_FILES
            .iter()
            .map(|value| (*value).to_owned())
            .collect(),
    })
    .map_err(materialization_serde_error)?;

    let mut files = BTreeMap::from([
        ("admission-journal/journal.json".to_owned(), journal_bytes),
        (
            "admission-journal/decisions.jsonl".to_owned(),
            decisions_bytes,
        ),
        (
            "admission-journal/source-digests.json".to_owned(),
            source_digest_bytes,
        ),
        (
            "admission-journal/non-claims.md".to_owned(),
            non_claims_bytes,
        ),
        (
            "admission-journal/redaction-report.json".to_owned(),
            redaction_report_bytes,
        ),
        (
            "admission-journal/validation-report.json".to_owned(),
            validation_report_bytes,
        ),
    ]);

    let manifest = manifest_for_files(journal, request, &files);
    files.insert(
        "admission-journal/manifest.json".to_owned(),
        serde_json::to_vec_pretty(&manifest).map_err(materialization_serde_error)?,
    );
    Ok(files)
}

fn manifest_for_files(
    journal: &AgentAdmissionJournal,
    request: &AdmissionJournalMaterializationRequest,
    files: &BTreeMap<String, Vec<u8>>,
) -> AdmissionJournalBundleManifest {
    let mut declared_file_digests = BTreeMap::new();
    for (logical_path, bytes) in files {
        declared_file_digests.insert(logical_path.clone(), hash_bytes(bytes));
    }

    AdmissionJournalBundleManifest {
        schema_version: "hsai-admission-journal-bundle-v1".to_owned(),
        bundle_id: request.bundle_id.clone(),
        created_at_unix: request.created_at_unix,
        admission_policy_id: request.admission_policy_id.clone(),
        journal_tip_digest_before: request.journal_tip_digest_before,
        journal_tip_digest_after: journal
            .entries
            .last()
            .map(AgentAdmissionJournalEntry::digest),
        entry_count: journal.entries.len() as u64,
        accepted_count: journal
            .entries
            .iter()
            .filter(|entry| entry.decision.verdict == AdmissionVerdict::Accepted)
            .count() as u64,
        rejected_count: journal
            .entries
            .iter()
            .filter(|entry| entry.decision.verdict == AdmissionVerdict::Rejected)
            .count() as u64,
        quarantined_count: journal
            .entries
            .iter()
            .filter(|entry| entry.decision.verdict == AdmissionVerdict::Quarantined)
            .count() as u64,
        declared_files: ADMISSION_JOURNAL_DECLARED_FILES
            .iter()
            .map(|value| (*value).to_owned())
            .collect(),
        declared_file_digests,
        claim_boundary: ADMISSION_JOURNAL_CLAIM_BOUNDARY.to_owned(),
        non_claims: request.nonclaims.clone(),
    }
}

fn decision_rows_jsonl(
    journal: &AgentAdmissionJournal,
) -> Result<Vec<u8>, AdmissionJournalMaterializationError> {
    let mut out = Vec::new();
    for row in decision_rows(journal) {
        out.extend(serde_json::to_vec(&row).map_err(materialization_serde_error)?);
        out.push(b'\n');
    }
    Ok(out)
}

fn decision_rows(journal: &AgentAdmissionJournal) -> Vec<AdmissionDecisionReviewRow> {
    journal
        .entries
        .iter()
        .map(|entry| AdmissionDecisionReviewRow {
            candidate_id: entry.candidate_id.clone(),
            policy_id: entry.decision.policy_id.clone(),
            verdict: entry.decision.verdict.clone(),
            reason_codes: entry.decision.reasons.clone(),
            candidate_digest: entry.candidate_digest,
            decision_digest: entry.decision_digest,
            source_artifact_digest_ids: entry
                .source_artifact_digests
                .iter()
                .map(|digest| digest.id.clone())
                .collect(),
            accepted_envelope_exists: entry.decision.accepted_envelope.is_some(),
        })
        .collect()
}

fn source_digest_index(journal: &AgentAdmissionJournal) -> AdmissionSourceDigestIndex {
    AdmissionSourceDigestIndex {
        source_artifact_digests: journal
            .entries
            .iter()
            .flat_map(|entry| entry.source_artifact_digests.iter().cloned())
            .collect(),
    }
}

fn nonclaims_markdown(nonclaims: &BTreeSet<NonClaimLabel>) -> String {
    let mut out = String::from("# Admission Journal Non-Claims\n\n");
    for nonclaim in nonclaims {
        out.push_str("- ");
        out.push_str(&nonclaim.0);
        out.push('\n');
    }
    out
}

fn redaction_report() -> AdmissionJournalRedactionReport {
    AdmissionJournalRedactionReport {
        retains_credentials_or_secrets: false,
        retains_raw_provider_responses: false,
        retains_raw_request_bodies: false,
        retains_raw_network_transcripts: false,
        retains_raw_attestation_quotes: false,
        retains_raw_dcap_collateral: false,
        retains_raw_jwks_or_openid_documents: false,
        retains_raw_tls_exporter_values: false,
        retains_benchmark_result_bodies: false,
        retains_accepted_evidence_ledger_json: false,
    }
}

pub fn accepted_claim_envelope<'a>(
    candidate: &AgentAdmissionCandidate,
    policy: &AgentAdmissionPolicy,
    decision: &'a AgentAdmissionDecision,
) -> Option<&'a ClaimEnvelope> {
    if candidate.source_kind == AdmissionSourceKind::ClaimEnvelopeProposal
        && decision == &evaluate_admission(candidate, policy)
        && decision.verdict == AdmissionVerdict::Accepted
    {
        decision.accepted_envelope.as_ref()
    } else {
        None
    }
}

pub fn gateway_required_nonclaims() -> BTreeSet<NonClaimLabel> {
    BTreeSet::from([
        NonClaimLabel("not direct authority".to_owned()),
        NonClaimLabel("not model-granted authority".to_owned()),
        NonClaimLabel("not semantic correctness".to_owned()),
        NonClaimLabel("not production readiness".to_owned()),
        NonClaimLabel("not Level2+ evidence".to_owned()),
        NonClaimLabel("not accepted Evidence Ledger mutation".to_owned()),
        NonClaimLabel("no score-axis population".to_owned()),
    ])
}

pub fn gateway_attestation_binding_required_nonclaims() -> BTreeSet<NonClaimLabel> {
    BTreeSet::from([
        NonClaimLabel("not attestation evidence".to_owned()),
        NonClaimLabel("not proof".to_owned()),
        NonClaimLabel("not live provider evidence".to_owned()),
        NonClaimLabel("not accepted Evidence Ledger mutation".to_owned()),
        NonClaimLabel("not benchmark evidence".to_owned()),
        NonClaimLabel("not SOTA status".to_owned()),
        NonClaimLabel("not breakthrough status".to_owned()),
        NonClaimLabel("not production readiness".to_owned()),
        NonClaimLabel("not semantic correctness".to_owned()),
        NonClaimLabel("not authority to execute an action".to_owned()),
    ])
}

pub fn build_gateway_attestation_challenge_binding(
    proposal: &GatewayActionProposal,
    policy_id: AdmissionPolicyId,
    anchor_id: impl Into<String>,
    agent_pubkey_spki_hex: impl Into<String>,
    nonce: u64,
    challenge_created_at: u64,
    challenge_expires_at: u64,
) -> Result<GatewayAttestationChallengeBinding, Vec<GatewayAttestationBindingError>> {
    let anchor_id = anchor_id.into();
    let agent_pubkey_spki_hex = agent_pubkey_spki_hex.into();
    let mut errors = Vec::new();

    if policy_id.0.trim().is_empty() {
        errors.push(GatewayAttestationBindingError::EmptyField("policy_id"));
    }
    if anchor_id.trim().is_empty() {
        errors.push(GatewayAttestationBindingError::EmptyField("anchor_id"));
    }
    if challenge_created_at >= challenge_expires_at {
        errors.push(GatewayAttestationBindingError::InvalidWindow {
            created_at: challenge_created_at,
            expires_at: challenge_expires_at,
        });
    }
    let agent_pubkey = match decode_lower_hex("agent_pubkey_spki_hex", &agent_pubkey_spki_hex) {
        Ok(bytes) if !bytes.is_empty() => bytes,
        Ok(_) => {
            errors.push(GatewayAttestationBindingError::EmptyField(
                "agent_pubkey_spki_hex",
            ));
            Vec::new()
        }
        Err(error) => {
            errors.push(error);
            Vec::new()
        }
    };
    if !errors.is_empty() {
        return Err(errors);
    }

    let gateway_case_hash = proposal.digest();
    let expected_report_data =
        report_data_binding(&agent_pubkey, nonce, gateway_case_hash.0.as_slice());
    let mut binding = GatewayAttestationChallengeBinding {
        schema_version: GATEWAY_ATTESTATION_BINDING_SCHEMA_VERSION.to_owned(),
        challenge_id: String::new(),
        proposal_id: proposal.id.clone(),
        subject: proposal.subject.clone(),
        policy_id,
        anchor_id,
        agent_pubkey_spki_hex: normalize_lower_hex(&agent_pubkey_spki_hex),
        nonce,
        challenge_created_at,
        challenge_expires_at,
        gateway_case_hash_hex: hash_hex(gateway_case_hash),
        expected_report_data_hex: bytes_hex(&expected_report_data),
        claim_boundary: GATEWAY_ATTESTATION_BINDING_CLAIM_BOUNDARY.to_owned(),
        authority_granted: false,
        nonclaims: gateway_attestation_binding_required_nonclaims(),
    };
    binding.challenge_id = gateway_attestation_challenge_id(&binding);
    Ok(binding)
}

pub fn validate_gateway_attestation_challenge_binding(
    proposal: &GatewayActionProposal,
    policy_id: &AdmissionPolicyId,
    binding: &GatewayAttestationChallengeBinding,
    now: u64,
) -> Vec<GatewayAttestationBindingError> {
    let mut errors = Vec::new();
    if binding.schema_version != GATEWAY_ATTESTATION_BINDING_SCHEMA_VERSION {
        errors.push(GatewayAttestationBindingError::SchemaMismatch(
            binding.schema_version.clone(),
        ));
    }
    if binding.proposal_id != proposal.id {
        errors.push(GatewayAttestationBindingError::ProposalIdMismatch);
    }
    if binding.subject != proposal.subject {
        errors.push(GatewayAttestationBindingError::SubjectMismatch);
    }
    if &binding.policy_id != policy_id {
        errors.push(GatewayAttestationBindingError::PolicyIdMismatch);
    }
    if binding.anchor_id.trim().is_empty() {
        errors.push(GatewayAttestationBindingError::EmptyField("anchor_id"));
    }
    if binding.challenge_created_at >= binding.challenge_expires_at {
        errors.push(GatewayAttestationBindingError::InvalidWindow {
            created_at: binding.challenge_created_at,
            expires_at: binding.challenge_expires_at,
        });
    } else if now < binding.challenge_created_at {
        errors.push(GatewayAttestationBindingError::NotYetValid {
            now,
            created_at: binding.challenge_created_at,
        });
    } else if now > binding.challenge_expires_at {
        errors.push(GatewayAttestationBindingError::ExpiredChallenge {
            now,
            expires_at: binding.challenge_expires_at,
        });
    }

    let expected_case_hash = hash_hex(proposal.digest());
    if binding.gateway_case_hash_hex != expected_case_hash {
        errors.push(GatewayAttestationBindingError::GatewayCaseHashMismatch {
            actual: binding.gateway_case_hash_hex.clone(),
            expected: expected_case_hash.clone(),
        });
    }

    let agent_pubkey =
        match decode_lower_hex("agent_pubkey_spki_hex", &binding.agent_pubkey_spki_hex) {
            Ok(bytes) if !bytes.is_empty() => Some(bytes),
            Ok(_) => {
                errors.push(GatewayAttestationBindingError::EmptyField(
                    "agent_pubkey_spki_hex",
                ));
                None
            }
            Err(error) => {
                errors.push(error);
                None
            }
        };
    match decode_lower_hex(
        "expected_report_data_hex",
        &binding.expected_report_data_hex,
    ) {
        Ok(bytes) if bytes.len() == 32 => {}
        Ok(_) => errors.push(GatewayAttestationBindingError::InvalidHex {
            field: "expected_report_data_hex",
            value: binding.expected_report_data_hex.clone(),
        }),
        Err(error) => errors.push(error),
    }
    if let Some(agent_pubkey) = agent_pubkey {
        let expected_report_data =
            report_data_binding(&agent_pubkey, binding.nonce, proposal.digest().0.as_slice());
        let expected_report_data_hex = bytes_hex(&expected_report_data);
        if binding.expected_report_data_hex != expected_report_data_hex {
            errors.push(GatewayAttestationBindingError::ReportDataMismatch {
                actual: binding.expected_report_data_hex.clone(),
                expected: expected_report_data_hex,
            });
        }
    }

    if binding.authority_granted {
        errors.push(GatewayAttestationBindingError::AuthorityGranted);
    }
    for required in gateway_attestation_binding_required_nonclaims() {
        if !binding.nonclaims.contains(&required) {
            errors.push(GatewayAttestationBindingError::MissingRequiredNonclaim(
                required.0,
            ));
        }
    }
    let expected_challenge_id = gateway_attestation_challenge_id(binding);
    if binding.challenge_id != expected_challenge_id {
        errors.push(GatewayAttestationBindingError::ChallengeIdMismatch {
            actual: binding.challenge_id.clone(),
            expected: expected_challenge_id,
        });
    }
    errors
}

pub fn gateway_operator_bridge_required_nonclaims() -> BTreeSet<NonClaimLabel> {
    BTreeSet::from([
        NonClaimLabel("not attestation evidence".to_owned()),
        NonClaimLabel("not proof".to_owned()),
        NonClaimLabel("not live provider evidence".to_owned()),
        NonClaimLabel("not accepted Evidence Ledger mutation".to_owned()),
        NonClaimLabel("not benchmark evidence".to_owned()),
        NonClaimLabel("not SOTA status".to_owned()),
        NonClaimLabel("not breakthrough status".to_owned()),
        NonClaimLabel("not production readiness".to_owned()),
        NonClaimLabel("not semantic correctness".to_owned()),
        NonClaimLabel("not authority to execute an action".to_owned()),
    ])
}

pub fn gateway_operator_bridge_claim_boundary() -> String {
    "local gateway/operator bridge metadata only; not attestation evidence, proof, live provider evidence, accepted evidence, benchmark evidence, production readiness, semantic correctness, SOTA, breakthrough, full security, or authority to execute an action".to_owned()
}

pub fn gateway_operator_bridge_promotion_preflight_required_nonclaims() -> BTreeSet<NonClaimLabel> {
    let mut nonclaims = gateway_operator_bridge_required_nonclaims();
    nonclaims.extend([
        NonClaimLabel("not bridge promotion".to_owned()),
        NonClaimLabel("not reviewed evidence acceptance".to_owned()),
        NonClaimLabel("not Level2+ evidence".to_owned()),
        NonClaimLabel("not score-axis population".to_owned()),
        NonClaimLabel("not raw provider artifact validation".to_owned()),
        NonClaimLabel("not credential handling".to_owned()),
    ]);
    nonclaims
}

pub fn gateway_operator_bridge_promotion_preflight_request_schema_version() -> &'static str {
    GATEWAY_OPERATOR_BRIDGE_PROMOTION_PREFLIGHT_REQUEST_SCHEMA_VERSION
}

pub fn gateway_operator_bridge_promotion_preflight_claim_boundary() -> String {
    "reviewed local gateway/operator bridge preflight metadata only; not promotion, accepted evidence, Level2+ evidence, live provider evidence, production readiness, semantic correctness, SOTA, breakthrough, full security, score-axis population, or authority to execute an action".to_owned()
}

pub fn gateway_operator_bridge_acceptance_preview_required_nonclaims() -> BTreeSet<NonClaimLabel> {
    let mut nonclaims = gateway_operator_bridge_promotion_preflight_required_nonclaims();
    nonclaims.extend([
        NonClaimLabel("not accepted bridge evidence".to_owned()),
        NonClaimLabel("candidate-only acceptance preview".to_owned()),
        NonClaimLabel("not ledger append".to_owned()),
        NonClaimLabel("not final acceptance".to_owned()),
    ]);
    nonclaims
}

pub fn gateway_operator_bridge_acceptance_preview_request_schema_version() -> &'static str {
    GATEWAY_OPERATOR_BRIDGE_ACCEPTANCE_PREVIEW_REQUEST_SCHEMA_VERSION
}

pub fn gateway_operator_bridge_acceptance_preview_claim_boundary() -> String {
    "candidate-only gateway/operator bridge acceptance preview metadata; not accepted evidence, final acceptance, ledger append, Level2+ evidence, live provider evidence, production readiness, semantic correctness, SOTA, breakthrough, full security, score-axis population, or authority to execute an action".to_owned()
}

pub fn build_gateway_operator_bridge_bundle(
    gateway_report_manifest: &GatewayReportOutputManifest,
    attestation_binding: GatewayAttestationChallengeBinding,
    operator_artifact_reference: GatewayOperatorArtifactReference,
    request: &GatewayOperatorBridgeMaterializationRequest,
) -> Result<GatewayOperatorBridgeBundle, Vec<GatewayOperatorBridgeIssue>> {
    let bundle = GatewayOperatorBridgeBundle {
        schema_version: GATEWAY_OPERATOR_BRIDGE_BUNDLE_SCHEMA_VERSION.to_owned(),
        bundle_id: request.bundle_id.clone(),
        created_at_unix: request.created_at_unix,
        gateway_report_digest: gateway_report_manifest.artifact_manifest.report_digest,
        gateway_report_manifest_digest: gateway_report_manifest.digest(),
        attestation_binding,
        operator_artifact_reference,
        claim_boundary: gateway_operator_bridge_claim_boundary(),
        authority_granted: false,
        accepted_evidence_mutation: false,
        nonclaims: gateway_operator_bridge_required_nonclaims(),
    };
    let issues = validate_gateway_operator_bridge_bundle(&bundle);
    if issues.is_empty() {
        Ok(bundle)
    } else {
        Err(issues)
    }
}

pub fn validate_gateway_operator_bridge_bundle(
    bundle: &GatewayOperatorBridgeBundle,
) -> Vec<GatewayOperatorBridgeIssue> {
    let mut issues = Vec::new();
    if bundle.schema_version != GATEWAY_OPERATOR_BRIDGE_BUNDLE_SCHEMA_VERSION
        || bundle.bundle_id.trim().is_empty()
        || !is_safe_relative_path(&bundle.bundle_id)
        || bundle.bundle_id.contains(['/', '\\'])
    {
        issues.push(GatewayOperatorBridgeIssue::InvalidBundleId);
    }
    if bundle.gateway_report_digest == Hash([0; 32]) {
        issues.push(GatewayOperatorBridgeIssue::MissingGatewayReportDigest);
    }
    if bundle.gateway_report_manifest_digest == Hash([0; 32]) {
        issues.push(GatewayOperatorBridgeIssue::MissingGatewayReportManifestDigest);
    }
    if bundle.attestation_binding.schema_version != GATEWAY_ATTESTATION_BINDING_SCHEMA_VERSION
        || bundle.attestation_binding.authority_granted
        || bundle.attestation_binding.claim_boundary != GATEWAY_ATTESTATION_BINDING_CLAIM_BOUNDARY
    {
        issues.push(GatewayOperatorBridgeIssue::InvalidAttestationBinding);
    }
    if validate_operator_artifact_reference(&bundle.operator_artifact_reference).is_err() {
        issues.push(GatewayOperatorBridgeIssue::InvalidOperatorReference);
    }
    if !bundle.operator_artifact_reference.repo_external {
        issues.push(GatewayOperatorBridgeIssue::OperatorArtifactNotRepoExternal);
    }
    if bundle.authority_granted {
        issues.push(GatewayOperatorBridgeIssue::AuthorityGranted);
    }
    if bundle.accepted_evidence_mutation {
        issues.push(GatewayOperatorBridgeIssue::AcceptedEvidenceMutationRequested);
    }
    if bundle.claim_boundary != gateway_operator_bridge_claim_boundary() {
        issues.push(GatewayOperatorBridgeIssue::ClaimBoundaryMismatch);
    }
    for required in gateway_operator_bridge_required_nonclaims() {
        if !bundle.nonclaims.contains(&required) {
            issues.push(GatewayOperatorBridgeIssue::MissingRequiredNonclaim(
                required.0,
            ));
        }
    }
    issues
}

pub fn build_gateway_operator_bridge_promotion_preflight_report(
    request: &GatewayOperatorBridgePromotionPreflightRequest,
) -> GatewayOperatorBridgePromotionPreflightReport {
    GatewayOperatorBridgePromotionPreflightReport {
        schema_version: GATEWAY_OPERATOR_BRIDGE_PROMOTION_PREFLIGHT_REPORT_SCHEMA_VERSION
            .to_owned(),
        preflight_id: request.preflight_id.clone(),
        bridge_bundle_digest: request.bridge_bundle.digest(),
        bridge_manifest_digest: request.bridge_manifest.digest(),
        gateway_report_digest: request.bridge_manifest.gateway_report_digest,
        attestation_binding_digest: request.bridge_manifest.attestation_binding_digest,
        operator_artifact_reference_digest: request
            .bridge_manifest
            .operator_artifact_reference_digest,
        validation: validate_gateway_operator_bridge_promotion_preflight_request(request),
        claim_boundary: gateway_operator_bridge_promotion_preflight_claim_boundary(),
        mutates_accepted_evidence_ledger: false,
        creates_level2_evidence: false,
        populates_score_axes: false,
        grants_authority: false,
        retains_raw_provider_artifacts: false,
        retains_credentials_or_secrets: false,
        nonclaims: gateway_operator_bridge_promotion_preflight_required_nonclaims(),
    }
}

pub fn validate_gateway_operator_bridge_promotion_preflight_request(
    request: &GatewayOperatorBridgePromotionPreflightRequest,
) -> GatewayOperatorBridgePromotionPreflightValidation {
    let mut issues = Vec::new();
    if request.schema_version != GATEWAY_OPERATOR_BRIDGE_PROMOTION_PREFLIGHT_REQUEST_SCHEMA_VERSION
    {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::InvalidSchemaVersion);
    }
    if request.preflight_id.trim().is_empty()
        || !is_safe_relative_path(&request.preflight_id)
        || request.preflight_id.contains(['/', '\\'])
    {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::InvalidPreflightId);
    }
    if request.reviewer_id.trim().is_empty() {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::MissingReviewer);
    }
    if request.review_decision != GatewayOperatorBridgePromotionReviewDecision::ApprovedMetadataOnly
    {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::ReviewNotApprovedMetadataOnly);
    }
    if !validate_gateway_operator_bridge_bundle(&request.bridge_bundle).is_empty() {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::InvalidBridgeBundle);
    }
    if !request
        .bridge_bundle
        .operator_artifact_reference
        .repo_external
    {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::OperatorArtifactNotRepoExternal);
    }
    if !gateway_operator_bridge_manifest_matches_bundle(
        &request.bridge_manifest,
        &request.bridge_bundle,
    ) {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::BridgeManifestMismatch);
    }
    if request.retains_raw_provider_artifacts {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::RawProviderArtifactRetained);
    }
    if request.retains_credentials_or_secrets {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::CredentialsOrSecretsRetained);
    }
    if request.accepted_evidence_mutation_requested {
        issues
            .push(GatewayOperatorBridgePromotionPreflightIssue::AcceptedEvidenceMutationRequested);
    }
    if request.level2_evidence_requested {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::Level2EvidenceRequested);
    }
    if request.score_axis_population_requested {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::ScoreAxisPopulationRequested);
    }
    if request.production_readiness_claimed {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::ProductionReadinessClaimed);
    }
    if request.semantic_correctness_claimed {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::SemanticCorrectnessClaimed);
    }
    if request.live_provider_evidence_claimed {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::LiveProviderEvidenceClaimed);
    }
    if request.requested_claim_boundary
        != gateway_operator_bridge_promotion_preflight_claim_boundary()
    {
        issues.push(GatewayOperatorBridgePromotionPreflightIssue::RequestedClaimBoundaryMismatch);
    }
    for forbidden in gateway_operator_bridge_promotion_forbidden_claim_fragments() {
        if request
            .claim_text
            .iter()
            .any(|text| text.to_ascii_lowercase().contains(forbidden))
        {
            issues.push(
                GatewayOperatorBridgePromotionPreflightIssue::ForbiddenClaimText(
                    (*forbidden).to_owned(),
                ),
            );
        }
    }
    for required in gateway_operator_bridge_promotion_preflight_required_nonclaims() {
        if !request.nonclaims.contains(&required) {
            issues.push(
                GatewayOperatorBridgePromotionPreflightIssue::MissingRequiredNonclaim(required.0),
            );
        }
    }
    GatewayOperatorBridgePromotionPreflightValidation {
        valid: issues.is_empty(),
        issues,
    }
}

pub fn build_gateway_operator_bridge_acceptance_preview_report(
    request: &GatewayOperatorBridgeAcceptancePreviewRequest,
) -> GatewayOperatorBridgeAcceptancePreviewReport {
    GatewayOperatorBridgeAcceptancePreviewReport {
        schema_version: GATEWAY_OPERATOR_BRIDGE_ACCEPTANCE_PREVIEW_REPORT_SCHEMA_VERSION.to_owned(),
        preview_id: request.preview_id.clone(),
        source_preflight_report_digest: request.source_preflight_report.digest(),
        bridge_bundle_digest: request.source_preflight_report.bridge_bundle_digest,
        bridge_manifest_digest: request.source_preflight_report.bridge_manifest_digest,
        gateway_report_digest: request.source_preflight_report.gateway_report_digest,
        attestation_binding_digest: request.source_preflight_report.attestation_binding_digest,
        operator_artifact_reference_digest: request
            .source_preflight_report
            .operator_artifact_reference_digest,
        validation: validate_gateway_operator_bridge_acceptance_preview_request(request),
        claim_boundary: gateway_operator_bridge_acceptance_preview_claim_boundary(),
        candidate_only: true,
        mutates_accepted_evidence_ledger: false,
        creates_level2_evidence: false,
        populates_score_axes: false,
        grants_authority: false,
        retains_raw_provider_artifacts: false,
        retains_credentials_or_secrets: false,
        nonclaims: gateway_operator_bridge_acceptance_preview_required_nonclaims(),
    }
}

pub fn validate_gateway_operator_bridge_acceptance_preview_request(
    request: &GatewayOperatorBridgeAcceptancePreviewRequest,
) -> GatewayOperatorBridgeAcceptancePreviewValidation {
    let mut issues = Vec::new();
    if request.schema_version != GATEWAY_OPERATOR_BRIDGE_ACCEPTANCE_PREVIEW_REQUEST_SCHEMA_VERSION {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::InvalidSchemaVersion);
    }
    if request.preview_id.trim().is_empty()
        || !is_safe_relative_path(&request.preview_id)
        || request.preview_id.contains(['/', '\\'])
    {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::InvalidPreviewId);
    }
    if request.reviewer_id.trim().is_empty() {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::MissingReviewer);
    }
    if request.decision != GatewayOperatorBridgeAcceptancePreviewDecision::ApproveCandidateOnly {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::ReviewNotCandidateOnlyApproval);
    }
    if !request.source_preflight_report.validation.valid
        || request
            .source_preflight_report
            .mutates_accepted_evidence_ledger
        || request.source_preflight_report.creates_level2_evidence
        || request.source_preflight_report.populates_score_axes
        || request.source_preflight_report.grants_authority
        || request
            .source_preflight_report
            .retains_raw_provider_artifacts
        || request
            .source_preflight_report
            .retains_credentials_or_secrets
        || request.source_preflight_report.claim_boundary
            != gateway_operator_bridge_promotion_preflight_claim_boundary()
    {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::SourcePreflightInvalid);
    }
    if request.expected_preflight_report_digest != request.source_preflight_report.digest() {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::PreflightDigestMismatch);
    }
    if request.requested_claim_boundary
        != gateway_operator_bridge_acceptance_preview_claim_boundary()
    {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::RequestedClaimBoundaryMismatch);
    }
    if !request.candidate_only {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::NotCandidateOnly);
    }
    if request.accepted_evidence_mutation_requested {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::AcceptedEvidenceMutationRequested);
    }
    if request.level2_evidence_requested {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::Level2EvidenceRequested);
    }
    if request.score_axis_population_requested {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::ScoreAxisPopulationRequested);
    }
    if request.production_readiness_claimed {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::ProductionReadinessClaimed);
    }
    if request.semantic_correctness_claimed {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::SemanticCorrectnessClaimed);
    }
    if request.live_provider_evidence_claimed {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::LiveProviderEvidenceClaimed);
    }
    if request.raw_provider_artifact_retention_requested {
        issues.push(
            GatewayOperatorBridgeAcceptancePreviewIssue::RawProviderArtifactRetentionRequested,
        );
    }
    if request.credential_retention_requested {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::CredentialRetentionRequested);
    }
    if request.authority_grant_requested {
        issues.push(GatewayOperatorBridgeAcceptancePreviewIssue::AuthorityGrantRequested);
    }
    for forbidden in gateway_operator_bridge_promotion_forbidden_claim_fragments() {
        if request
            .claim_text
            .iter()
            .any(|text| text.to_ascii_lowercase().contains(forbidden))
        {
            issues.push(
                GatewayOperatorBridgeAcceptancePreviewIssue::ForbiddenClaimText(
                    (*forbidden).to_owned(),
                ),
            );
        }
    }
    for required in gateway_operator_bridge_acceptance_preview_required_nonclaims() {
        if !request.nonclaims.contains(&required) {
            issues.push(
                GatewayOperatorBridgeAcceptancePreviewIssue::MissingRequiredNonclaim(required.0),
            );
        }
    }
    GatewayOperatorBridgeAcceptancePreviewValidation {
        valid: issues.is_empty(),
        issues,
    }
}

pub fn materialize_gateway_operator_bridge_bundle(
    output_root: &Path,
    bundle: &GatewayOperatorBridgeBundle,
    request: &GatewayOperatorBridgeMaterializationRequest,
) -> Result<GatewayOperatorBridgeOutputManifest, GatewayOperatorBridgeMaterializationError> {
    validate_gateway_operator_bridge_materialization_request(output_root, bundle, request)?;

    let staging_root = gateway_staging_root_for(output_root, &request.bundle_id)
        .map_err(gateway_bridge_from_report_error)?;
    if staging_root.exists() {
        remove_gateway_dir_all_checked(&staging_root).map_err(gateway_bridge_from_report_error)?;
    }
    fs::create_dir_all(staging_root.join("gateway-bridge")).map_err(gateway_bridge_io_error)?;

    let files = build_gateway_operator_bridge_files(bundle)?;
    for (logical_path, bytes) in &files {
        let target = staging_root.join(logical_path);
        if let Some(parent) = target.parent() {
            fs::create_dir_all(parent).map_err(gateway_bridge_io_error)?;
        }
        fs::write(&target, bytes).map_err(gateway_bridge_io_error)?;
        fs::write(
            sidecar_path(&target),
            hash_hex(hash_bytes(bytes)).into_bytes(),
        )
        .map_err(gateway_bridge_io_error)?;
    }

    if output_root.exists() {
        if !request.overwrite {
            remove_gateway_dir_all_checked(&staging_root)
                .map_err(gateway_bridge_from_report_error)?;
            return Err(
                GatewayOperatorBridgeMaterializationError::OutputRootExistsWithoutOverwrite,
            );
        }
        remove_gateway_dir_all_checked(output_root).map_err(gateway_bridge_from_report_error)?;
    }
    fs::rename(&staging_root, output_root).map_err(gateway_bridge_io_error)?;
    read_gateway_operator_bridge_bundle(output_root)
}

pub fn read_gateway_operator_bridge_bundle(
    output_root: &Path,
) -> Result<GatewayOperatorBridgeOutputManifest, GatewayOperatorBridgeMaterializationError> {
    let output_metadata = fs::symlink_metadata(output_root).map_err(gateway_bridge_io_error)?;
    if output_metadata.file_type().is_symlink() {
        return Err(GatewayOperatorBridgeMaterializationError::OutputRootIsSymlink);
    }
    if !output_metadata.is_dir() {
        return Err(GatewayOperatorBridgeMaterializationError::OutputRootIsFile);
    }
    let bundle_dir = output_root.join("gateway-bridge");
    let bundle_metadata = fs::symlink_metadata(&bundle_dir).map_err(gateway_bridge_io_error)?;
    if bundle_metadata.file_type().is_symlink() {
        return Err(
            GatewayOperatorBridgeMaterializationError::BundleFileIsSymlink(
                "gateway-bridge".to_owned(),
            ),
        );
    }
    if !bundle_metadata.is_dir() {
        return Err(
            GatewayOperatorBridgeMaterializationError::DeclaredFileTypeMismatch(
                "gateway-bridge".to_owned(),
            ),
        );
    }

    reject_undeclared_gateway_bridge_files(output_root)?;
    let mut file_bytes = BTreeMap::new();
    for logical_path in GATEWAY_OPERATOR_BRIDGE_DECLARED_FILES {
        let path = output_root.join(logical_path);
        let metadata = fs::symlink_metadata(&path).map_err(gateway_bridge_io_error)?;
        if metadata.file_type().is_symlink() {
            return Err(
                GatewayOperatorBridgeMaterializationError::BundleFileIsSymlink(
                    (*logical_path).to_owned(),
                ),
            );
        }
        if !metadata.is_file() {
            return Err(
                GatewayOperatorBridgeMaterializationError::DeclaredFileTypeMismatch(
                    (*logical_path).to_owned(),
                ),
            );
        }
        let sidecar = sidecar_path(&path);
        let sidecar_metadata = fs::symlink_metadata(&sidecar).map_err(gateway_bridge_io_error)?;
        if sidecar_metadata.file_type().is_symlink() {
            return Err(GatewayOperatorBridgeMaterializationError::SidecarIsSymlink(
                format!("{logical_path}.sha256"),
            ));
        }
        if !sidecar_metadata.is_file() {
            return Err(
                GatewayOperatorBridgeMaterializationError::DeclaredFileTypeMismatch(format!(
                    "{logical_path}.sha256"
                )),
            );
        }
        let bytes = fs::read(&path).map_err(gateway_bridge_io_error)?;
        let expected = fs::read_to_string(sidecar).map_err(gateway_bridge_io_error)?;
        if expected != hash_hex(hash_bytes(&bytes)) {
            return Err(GatewayOperatorBridgeMaterializationError::DigestMismatch(
                (*logical_path).to_owned(),
            ));
        }
        file_bytes.insert((*logical_path).to_owned(), bytes);
    }
    validate_gateway_operator_bridge_files(&file_bytes)
}

pub fn gateway_local_default_policy(
    id: impl Into<String>,
    allowed_action_kinds: BTreeSet<GatewayActionKind>,
    allowed_targets: BTreeSet<String>,
    max_value_units: u64,
) -> GatewayActionPolicy {
    GatewayActionPolicy {
        id: AdmissionPolicyId(id.into()),
        admission_policy: AgentAdmissionPolicy::local_default(gateway_required_nonclaims()),
        allowed_action_kinds,
        allowed_targets,
        max_value_units,
        require_non_secret_model_lane: true,
    }
}

pub fn validate_gateway_model_lane_registry(
    registry: &GatewayModelLaneRegistry,
) -> Vec<GatewayModelLaneRegistryIssue> {
    let mut issues = Vec::new();
    let mut seen_lane_ids = BTreeSet::new();

    for entry in &registry.entries {
        if !is_portable_artifact_id(&entry.lane_id) {
            issues.push(GatewayModelLaneRegistryIssue::InvalidLaneId(
                entry.lane_id.clone(),
            ));
        }
        if !seen_lane_ids.insert(entry.lane_id.clone()) {
            issues.push(GatewayModelLaneRegistryIssue::DuplicateLaneId(
                entry.lane_id.clone(),
            ));
        }
        if !is_portable_artifact_id(&entry.provenance.model_family)
            || !is_portable_artifact_id(&entry.provenance.artifact_id)
        {
            issues.push(GatewayModelLaneRegistryIssue::MissingModelId(
                entry.lane_id.clone(),
            ));
        }
        if entry.provenance.prompt_template_digest == Hash([0; 32]) {
            issues.push(GatewayModelLaneRegistryIssue::MissingPromptTemplateDigest(
                entry.lane_id.clone(),
            ));
        }
        if !entry.provenance.non_secret {
            issues.push(GatewayModelLaneRegistryIssue::MissingNonSecretStatement(
                entry.lane_id.clone(),
            ));
        }
        if entry.expected_output_bundle_digest == Hash([0; 32])
            || entry.expected_output_bundle_digest != entry.provenance.output_bundle_digest
        {
            issues.push(GatewayModelLaneRegistryIssue::StaleOutputDigest(
                entry.lane_id.clone(),
            ));
        }
        if gateway_model_lane_requires_external_bounds(&entry.provenance.lane_kind)
            && (entry.max_cases_per_run.unwrap_or(0) == 0
                || entry.max_cost_units_per_case.unwrap_or(0) == 0)
        {
            issues.push(GatewayModelLaneRegistryIssue::UnboundedRentedModelMetadata(
                entry.lane_id.clone(),
            ));
        }
    }

    issues
}

pub fn gateway_required_adversarial_threat_labels() -> BTreeSet<GatewayThreatLabel> {
    BTreeSet::from([
        GatewayThreatLabel::PromptInjectionPayment,
        GatewayThreatLabel::WrongCounterparty,
        GatewayThreatLabel::AmountLimitBypass,
        GatewayThreatLabel::SourceDigestDrift,
        GatewayThreatLabel::StaleApprovalReplay,
        GatewayThreatLabel::DuplicateJsonKeyPayload,
        GatewayThreatLabel::PolicyDowngrade,
        GatewayThreatLabel::DirectAuthorityRequest,
        GatewayThreatLabel::ForgedAcceptedDecision,
        GatewayThreatLabel::MissingNonclaim,
        GatewayThreatLabel::MissingSourceDigest,
        GatewayThreatLabel::StaleJournalTip,
        GatewayThreatLabel::SignerBeforeAdmission,
    ])
}

pub fn validate_gateway_adversarial_corpus(
    corpus: &GatewayAdversarialCorpus,
    model_lane_registry: &GatewayModelLaneRegistry,
) -> Vec<GatewayAdversarialCorpusIssue> {
    let mut issues = Vec::new();
    let mut seen_case_ids = BTreeSet::new();
    let mut covered_threat_labels = BTreeSet::new();
    let mut has_accepted_benign_case = false;

    if !is_portable_artifact_id(&corpus.corpus_id) {
        issues.push(GatewayAdversarialCorpusIssue::InvalidCorpusId);
    }
    if corpus.cases.is_empty() {
        issues.push(GatewayAdversarialCorpusIssue::EmptyCorpus);
    }
    if !validate_gateway_model_lane_registry(model_lane_registry).is_empty() {
        issues.push(GatewayAdversarialCorpusIssue::InvalidModelLaneRegistry);
    }

    for case in &corpus.cases {
        if !seen_case_ids.insert(case.proposal.id.clone()) {
            issues.push(GatewayAdversarialCorpusIssue::DuplicateCaseId(
                case.proposal.id.clone(),
            ));
        }

        covered_threat_labels.extend(case.proposal.threat_labels.iter().cloned());

        let has_non_benign_threat = case
            .proposal
            .threat_labels
            .iter()
            .any(|label| label != &GatewayThreatLabel::Benign);
        if has_non_benign_threat && case.expected_verdict == AdmissionVerdict::Accepted {
            issues.push(GatewayAdversarialCorpusIssue::UnsafeThreatExpectedAccepted(
                case.proposal.id.clone(),
            ));
        }
        if !has_non_benign_threat
            && case
                .proposal
                .threat_labels
                .contains(&GatewayThreatLabel::Benign)
            && case.expected_verdict == AdmissionVerdict::Accepted
        {
            has_accepted_benign_case = true;
        }
        if !gateway_model_lane_registry_contains(model_lane_registry, &case.proposal.model_lane) {
            issues.push(GatewayAdversarialCorpusIssue::UnknownModelLane(
                case.proposal.id.clone(),
            ));
        }
    }

    for label in &corpus.required_threat_labels {
        if !covered_threat_labels.contains(label) {
            issues.push(GatewayAdversarialCorpusIssue::MissingRequiredThreatLabel(
                label.clone(),
            ));
        }
    }
    if !has_accepted_benign_case {
        issues.push(GatewayAdversarialCorpusIssue::MissingAcceptedBenignCase);
    }

    issues
}

pub fn gateway_cost_router_default_policy(id: impl Into<String>) -> GatewayCostRouterPolicy {
    GatewayCostRouterPolicy {
        id: AdmissionPolicyId(id.into()),
        local_review_value_ceiling: 25,
        verifier_mixture_value_ceiling: 100,
        premium_escalation_value_ceiling: 500,
        local_review_cost_units: 1,
        verifier_mixture_cost_units: 3,
        premium_escalation_cost_units: 20,
        operator_review_cost_units: 50,
        premium_escalation_budget_units: 20,
    }
}

pub fn route_gateway_action_cost(
    proposal: &GatewayActionProposal,
    gateway_policy: &GatewayActionPolicy,
    router_policy: &GatewayCostRouterPolicy,
) -> GatewayCostRouteDecision {
    let candidate = gateway_action_candidate(proposal, gateway_policy);
    let mut reasons = BTreeSet::from([GatewayCostRouteReason::NoAuthorityGrantedByRouter]);

    if !candidate.gateway_policy_violations.is_empty() {
        reasons.insert(GatewayCostRouteReason::DeterministicPolicyViolation);
        return GatewayCostRouteDecision {
            action_id: proposal.id.clone(),
            policy_id: router_policy.id.clone(),
            route: GatewayCostRoute::DeterministicOnly,
            reasons,
            estimated_cost_units: 0,
            authority_granted: false,
        };
    }

    if proposal.action_kind == GatewayActionKind::Deployment {
        reasons.insert(GatewayCostRouteReason::OperatorOnlyActionKind);
        return gateway_cost_route_decision(
            proposal,
            router_policy,
            GatewayCostRoute::OperatorReviewRequired,
            reasons,
            router_policy.operator_review_cost_units,
        );
    }

    if proposal.value_units > router_policy.premium_escalation_value_ceiling {
        reasons.insert(GatewayCostRouteReason::OperatorValueLimitExceeded);
        return gateway_cost_route_decision(
            proposal,
            router_policy,
            GatewayCostRoute::OperatorReviewRequired,
            reasons,
            router_policy.operator_review_cost_units,
        );
    }

    if proposal.value_units > router_policy.verifier_mixture_value_ceiling {
        reasons.insert(GatewayCostRouteReason::HighValueNeedsPremiumEscalation);
        if router_policy.premium_escalation_cost_units
            <= router_policy.premium_escalation_budget_units
        {
            return gateway_cost_route_decision(
                proposal,
                router_policy,
                GatewayCostRoute::PremiumEscalation,
                reasons,
                router_policy.premium_escalation_cost_units,
            );
        }
        reasons.insert(GatewayCostRouteReason::PremiumEscalationBudgetExceeded);
        return gateway_cost_route_decision(
            proposal,
            router_policy,
            GatewayCostRoute::OperatorReviewRequired,
            reasons,
            router_policy.operator_review_cost_units,
        );
    }

    if gateway_threat_labels_need_verifier_mixture(&proposal.threat_labels) {
        reasons.insert(GatewayCostRouteReason::ThreatLabelNeedsVerifierMixture);
        return gateway_cost_route_decision(
            proposal,
            router_policy,
            GatewayCostRoute::VerifierMixture,
            reasons,
            router_policy.verifier_mixture_cost_units,
        );
    }

    if proposal.value_units > router_policy.local_review_value_ceiling {
        reasons.insert(GatewayCostRouteReason::LocalReviewForModerateValue);
        return gateway_cost_route_decision(
            proposal,
            router_policy,
            GatewayCostRoute::LocalOpenWeightReview,
            reasons,
            router_policy.local_review_cost_units,
        );
    }

    reasons.insert(GatewayCostRouteReason::RoutineLowValueAction);
    gateway_cost_route_decision(
        proposal,
        router_policy,
        GatewayCostRoute::DeterministicOnly,
        reasons,
        0,
    )
}

pub fn gateway_action_candidate(
    proposal: &GatewayActionProposal,
    policy: &GatewayActionPolicy,
) -> AgentAdmissionCandidate {
    let mut violations = BTreeSet::new();

    if !is_portable_candidate_id(&proposal.id.0) {
        violations.insert(GatewayPolicyViolation::InvalidActionId);
    }
    if !is_gateway_target_safe(&proposal.target) {
        violations.insert(GatewayPolicyViolation::InvalidTarget);
    }
    if !policy.allowed_action_kinds.contains(&proposal.action_kind) {
        violations.insert(GatewayPolicyViolation::UnsupportedActionKind);
    }
    if !policy.allowed_targets.contains(&proposal.target) {
        violations.insert(GatewayPolicyViolation::UnauthorizedTarget);
    }
    if proposal.value_units > policy.max_value_units {
        violations.insert(GatewayPolicyViolation::AmountLimitExceeded);
    }
    if !model_lane_provenance_is_complete(&proposal.model_lane) {
        violations.insert(GatewayPolicyViolation::MissingModelLaneProvenance);
    }
    if policy.require_non_secret_model_lane && !proposal.model_lane.non_secret {
        violations.insert(GatewayPolicyViolation::ModelLaneNotNonSecret);
    }
    if proposal.direct_authority_requested {
        violations.insert(GatewayPolicyViolation::DirectAuthorityRequested);
    }
    if proposal.signer_or_tool_requested_before_admission {
        violations.insert(GatewayPolicyViolation::SignerOrToolRequestedBeforeAdmission);
    }

    AgentAdmissionCandidate {
        id: AdmissionCandidateId(proposal.id.0.clone()),
        subject: proposal.subject.clone(),
        source_kind: AdmissionSourceKind::GatewayActionProposal,
        strict_typed: true,
        case: None,
        proposed_envelope: None,
        gateway_action: Some(proposal.clone()),
        gateway_policy_violations: violations,
        requested_claim_boundary: AdmissionClaimBoundary::LocalOnly,
        source_artifact_digests: proposal.source_artifact_digests.clone(),
        nonclaims: proposal.nonclaims.clone(),
        provider_direct_authority_requested: proposal.direct_authority_requested,
        accepted_ledger_mutation_requested: false,
        score_axis_population_requested: false,
        external_or_formal_evidence_claimed: false,
    }
}

pub fn evaluate_gateway_action(
    proposal: &GatewayActionProposal,
    policy: &GatewayActionPolicy,
    journal: &mut AgentAdmissionJournal,
) -> Result<GatewayActionOutcome, JournalError> {
    let candidate = gateway_action_candidate(proposal, policy);
    let decision = evaluate_admission(&candidate, &policy.admission_policy);
    journal.append_decision(&candidate, &policy.admission_policy, decision.clone())?;
    let accepted_handoff =
        accepted_gateway_handoff(&candidate, &policy.admission_policy, &decision);

    Ok(GatewayActionOutcome {
        proposal_id: proposal.id.clone(),
        candidate_id: candidate.id,
        action_digest: proposal.digest(),
        decision,
        accepted_handoff,
    })
}

pub fn accepted_gateway_handoff(
    candidate: &AgentAdmissionCandidate,
    policy: &AgentAdmissionPolicy,
    decision: &AgentAdmissionDecision,
) -> Option<GatewayAcceptedHandoff> {
    if candidate.source_kind != AdmissionSourceKind::GatewayActionProposal
        || decision != &evaluate_admission(candidate, policy)
        || decision.verdict != AdmissionVerdict::Accepted
    {
        return None;
    }
    let action = candidate.gateway_action.as_ref()?;
    Some(GatewayAcceptedHandoff {
        action_id: action.id.clone(),
        subject: action.subject.clone(),
        action_kind: action.action_kind.clone(),
        target: action.target.clone(),
        value_units: action.value_units,
        candidate_digest: candidate.digest(),
        decision_digest: decision.digest(),
    })
}

pub fn evaluate_gateway_corpus(
    cases: &[GatewayCorpusCase],
    policy: &GatewayActionPolicy,
) -> Result<GatewayCorpusReport, JournalError> {
    let mut journal = AgentAdmissionJournal::default();
    let mut outcomes = Vec::new();
    for case in cases {
        outcomes.push(evaluate_gateway_action(
            &case.proposal,
            policy,
            &mut journal,
        )?);
    }
    let metrics = gateway_run_metrics(cases, &outcomes, &journal, policy);
    Ok(GatewayCorpusReport {
        journal,
        outcomes,
        metrics,
    })
}

pub fn gateway_run_metrics(
    cases: &[GatewayCorpusCase],
    outcomes: &[GatewayActionOutcome],
    journal: &AgentAdmissionJournal,
    policy: &GatewayActionPolicy,
) -> GatewayRunMetrics {
    let mut unsafe_action_blocked_count = 0;
    let mut false_rejection_count = 0;
    let mut replay_or_tamper_detection_count = 0;
    let mut duplicate_key_detection_count = 0;
    let mut policy_downgrade_detection_count = 0;
    let mut decision_recomputation_agreement_count = 0;

    for (case, outcome) in cases.iter().zip(outcomes) {
        if case.expected_verdict != AdmissionVerdict::Accepted
            && outcome.decision.verdict != AdmissionVerdict::Accepted
        {
            unsafe_action_blocked_count += 1;
        }
        if case.expected_verdict == AdmissionVerdict::Accepted
            && outcome.decision.verdict != AdmissionVerdict::Accepted
        {
            false_rejection_count += 1;
        }
        if case
            .proposal
            .threat_labels
            .contains(&GatewayThreatLabel::StaleApprovalReplay)
            || case
                .proposal
                .threat_labels
                .contains(&GatewayThreatLabel::SourceDigestDrift)
            || case
                .proposal
                .threat_labels
                .contains(&GatewayThreatLabel::ForgedAcceptedDecision)
        {
            replay_or_tamper_detection_count +=
                u64::from(outcome.decision.verdict != AdmissionVerdict::Accepted);
        }
        if case
            .proposal
            .threat_labels
            .contains(&GatewayThreatLabel::DuplicateJsonKeyPayload)
        {
            duplicate_key_detection_count +=
                u64::from(outcome.decision.verdict != AdmissionVerdict::Accepted);
        }
        if case
            .proposal
            .threat_labels
            .contains(&GatewayThreatLabel::PolicyDowngrade)
        {
            policy_downgrade_detection_count +=
                u64::from(outcome.decision.verdict != AdmissionVerdict::Accepted);
        }
    }

    for entry in &journal.entries {
        if entry.decision == evaluate_admission(&entry.candidate, &policy.admission_policy) {
            decision_recomputation_agreement_count += 1;
        }
    }

    GatewayRunMetrics {
        total_cases: outcomes.len() as u64,
        accepted_count: outcomes
            .iter()
            .filter(|outcome| outcome.decision.verdict == AdmissionVerdict::Accepted)
            .count() as u64,
        rejected_count: outcomes
            .iter()
            .filter(|outcome| outcome.decision.verdict == AdmissionVerdict::Rejected)
            .count() as u64,
        quarantined_count: outcomes
            .iter()
            .filter(|outcome| outcome.decision.verdict == AdmissionVerdict::Quarantined)
            .count() as u64,
        unsafe_action_blocked_count,
        false_rejection_count,
        replay_or_tamper_detection_count,
        duplicate_key_detection_count,
        policy_downgrade_detection_count,
        decision_recomputation_agreement_count,
        audit_bundle_complete: journal.validate().is_empty()
            && journal.entries.len() == outcomes.len(),
    }
}

pub fn gateway_baseline_required_nonclaims() -> BTreeSet<NonClaimLabel> {
    BTreeSet::from([
        NonClaimLabel("not benchmark evidence".to_owned()),
        NonClaimLabel("not production readiness".to_owned()),
        NonClaimLabel("not semantic correctness".to_owned()),
        NonClaimLabel("not fully secure".to_owned()),
    ])
}

pub fn compare_gateway_baseline(
    cases: &[GatewayCorpusCase],
    report: &GatewayCorpusReport,
    policy: &GatewayActionPolicy,
    baseline: &GatewayBaselineRun,
) -> Result<GatewayBaselineComparison, GatewayBaselineComparisonError> {
    let report_issues = validate_gateway_corpus_report(report, policy);
    if !report_issues.is_empty() {
        return Err(GatewayBaselineComparisonError::InvalidReport(report_issues));
    }

    let baseline_issues = validate_gateway_baseline_run(cases, baseline);
    if !baseline_issues.is_empty() {
        return Err(GatewayBaselineComparisonError::InvalidBaseline(
            baseline_issues,
        ));
    }

    let baseline_decisions = baseline
        .decisions
        .iter()
        .map(|decision| (&decision.proposal_id, &decision.verdict))
        .collect::<BTreeMap<_, _>>();

    let hsai_decisions = report
        .outcomes
        .iter()
        .map(|outcome| (&outcome.proposal_id, &outcome.decision.verdict))
        .collect::<BTreeMap<_, _>>();

    let mut hsai_unsafe_accepted_count = 0;
    let mut hsai_false_rejection_count = 0;
    let mut baseline_unsafe_accepted_count = 0;
    let mut baseline_false_rejection_count = 0;
    for case in cases {
        let hsai_verdict = hsai_decisions
            .get(&case.proposal.id)
            .expect("validated report outcome exists");
        let baseline_verdict = baseline_decisions
            .get(&case.proposal.id)
            .expect("validated baseline decision exists");
        if case.expected_verdict != AdmissionVerdict::Accepted
            && **hsai_verdict == AdmissionVerdict::Accepted
        {
            hsai_unsafe_accepted_count += 1;
        }
        if case.expected_verdict == AdmissionVerdict::Accepted
            && **hsai_verdict != AdmissionVerdict::Accepted
        {
            hsai_false_rejection_count += 1;
        }
        if case.expected_verdict != AdmissionVerdict::Accepted
            && **baseline_verdict == AdmissionVerdict::Accepted
        {
            baseline_unsafe_accepted_count += 1;
        }
        if case.expected_verdict == AdmissionVerdict::Accepted
            && **baseline_verdict != AdmissionVerdict::Accepted
        {
            baseline_false_rejection_count += 1;
        }
    }

    Ok(GatewayBaselineComparison {
        baseline_id: baseline.baseline_id.clone(),
        baseline_kind: baseline.baseline_kind.clone(),
        total_cases: cases.len() as u64,
        hsai_unsafe_accepted_count,
        baseline_unsafe_accepted_count,
        hsai_false_rejection_count,
        baseline_false_rejection_count,
        hsai_audit_bundle_complete: report.metrics.audit_bundle_complete,
        baseline_audit_bundle_complete: false,
        claim_boundary: GATEWAY_BASELINE_COMPARISON_CLAIM_BOUNDARY.to_owned(),
        authority_granted: false,
    })
}

pub fn gateway_effectiveness_summary(
    cases: &[GatewayCorpusCase],
    report: &GatewayCorpusReport,
    policy: &GatewayActionPolicy,
) -> Result<GatewayEffectivenessSummary, Vec<GatewayReportValidationIssue>> {
    let report_issues = validate_gateway_corpus_report(report, policy);
    if !report_issues.is_empty() {
        return Err(report_issues);
    }

    let outcome_verdicts = report
        .outcomes
        .iter()
        .map(|outcome| (&outcome.proposal_id, &outcome.decision.verdict))
        .collect::<BTreeMap<_, _>>();
    let unsafe_case_count = cases
        .iter()
        .filter(|case| case.expected_verdict != AdmissionVerdict::Accepted)
        .count() as u64;
    let benign_expected_accept_count = cases
        .iter()
        .filter(|case| case.expected_verdict == AdmissionVerdict::Accepted)
        .count() as u64;

    let mut covered_threat_labels = BTreeSet::new();
    let mut threat_counts = BTreeMap::<GatewayThreatLabel, (u64, u64)>::new();
    for case in cases {
        let verdict = outcome_verdicts
            .get(&case.proposal.id)
            .expect("validated report outcome exists");
        for label in &case.proposal.threat_labels {
            covered_threat_labels.insert(label.clone());
            let entry = threat_counts.entry(label.clone()).or_insert((0, 0));
            entry.0 += 1;
            if case.expected_verdict != AdmissionVerdict::Accepted
                && **verdict != AdmissionVerdict::Accepted
            {
                entry.1 += 1;
            }
        }
    }

    Ok(GatewayEffectivenessSummary {
        total_cases: cases.len() as u64,
        unsafe_case_count,
        benign_expected_accept_count,
        unsafe_action_block_rate_basis_points: basis_points(
            report.metrics.unsafe_action_blocked_count,
            unsafe_case_count,
        ),
        false_rejection_rate_basis_points: basis_points(
            report.metrics.false_rejection_count,
            benign_expected_accept_count,
        ),
        quarantine_rate_basis_points: basis_points(
            report.metrics.quarantined_count,
            cases.len() as u64,
        ),
        decision_recomputation_agreement_rate_basis_points: basis_points(
            report.metrics.decision_recomputation_agreement_count,
            cases.len() as u64,
        ),
        audit_bundle_complete: report.metrics.audit_bundle_complete,
        covered_threat_labels,
        threat_coverage: threat_counts
            .into_iter()
            .map(
                |(threat_label, (case_count, blocked_count))| GatewayThreatCoverageRow {
                    threat_label,
                    case_count,
                    blocked_count,
                },
            )
            .collect(),
        claim_boundary: GATEWAY_EFFECTIVENESS_SUMMARY_CLAIM_BOUNDARY.to_owned(),
        authority_granted: false,
    })
}

pub fn gateway_report_required_nonclaims() -> BTreeSet<NonClaimLabel> {
    let mut nonclaims = gateway_required_nonclaims();
    nonclaims.insert(NonClaimLabel("not benchmark evidence".to_owned()));
    nonclaims.insert(NonClaimLabel("not model evaluation".to_owned()));
    nonclaims.insert(NonClaimLabel("not fully secure".to_owned()));
    nonclaims
}

pub fn validate_gateway_corpus_report(
    report: &GatewayCorpusReport,
    policy: &GatewayActionPolicy,
) -> Vec<GatewayReportValidationIssue> {
    let mut issues = Vec::new();
    let journal_errors = report.journal.validate();
    if !journal_errors.is_empty() {
        issues.push(GatewayReportValidationIssue::JournalInvalid);
    }

    if report.metrics.total_cases != report.outcomes.len() as u64 {
        issues.push(GatewayReportValidationIssue::MetricsTotalMismatch);
    }

    let accepted_count = report
        .outcomes
        .iter()
        .filter(|outcome| outcome.decision.verdict == AdmissionVerdict::Accepted)
        .count() as u64;
    let rejected_count = report
        .outcomes
        .iter()
        .filter(|outcome| outcome.decision.verdict == AdmissionVerdict::Rejected)
        .count() as u64;
    let quarantined_count = report
        .outcomes
        .iter()
        .filter(|outcome| outcome.decision.verdict == AdmissionVerdict::Quarantined)
        .count() as u64;
    if report.metrics.accepted_count != accepted_count
        || report.metrics.rejected_count != rejected_count
        || report.metrics.quarantined_count != quarantined_count
        || accepted_count + rejected_count + quarantined_count != report.outcomes.len() as u64
    {
        issues.push(GatewayReportValidationIssue::MetricsVerdictCountMismatch);
    }

    let accepted_handoff_count = report
        .outcomes
        .iter()
        .filter(|outcome| outcome.accepted_handoff.is_some())
        .count() as u64;
    if accepted_handoff_count != accepted_count {
        issues.push(GatewayReportValidationIssue::MetricsAcceptedHandoffMismatch);
    }

    let recomputed_agreement_count = report
        .journal
        .entries
        .iter()
        .filter(|entry| {
            entry.decision == evaluate_admission(&entry.candidate, &policy.admission_policy)
        })
        .count() as u64;
    if report.metrics.decision_recomputation_agreement_count != recomputed_agreement_count {
        issues.push(GatewayReportValidationIssue::MetricsDecisionRecomputationMismatch);
    }

    let audit_bundle_complete =
        journal_errors.is_empty() && report.journal.entries.len() == report.outcomes.len();
    if report.metrics.audit_bundle_complete != audit_bundle_complete {
        issues.push(GatewayReportValidationIssue::MetricsAuditBundleCompletenessMismatch);
    }

    issues
}

pub fn gateway_report_artifact(
    report: &GatewayCorpusReport,
    policy: &GatewayActionPolicy,
) -> Result<GatewayReportArtifact, GatewayReportArtifactError> {
    let issues = validate_gateway_corpus_report(report, policy);
    if !issues.is_empty() {
        return Err(GatewayReportArtifactError::InvalidReport(issues));
    }

    let report_json = serde_json::to_vec_pretty(report)
        .map_err(|error| GatewayReportArtifactError::Serialization(error.to_string()))?;
    let report_markdown = render_gateway_report_markdown(report, policy).into_bytes();
    let manifest = GatewayReportArtifactManifest {
        schema_version: "hsai-gateway-report-artifact-v1".to_owned(),
        claim_boundary: GATEWAY_REPORT_CLAIM_BOUNDARY.to_owned(),
        policy_id: policy.id.clone(),
        report_digest: hash_tagged("hsai-agent-admission:gateway-corpus-report:v1", report),
        journal_tip_digest_after: report
            .journal
            .entries
            .last()
            .map(AgentAdmissionJournalEntry::digest),
        report_json_sha256: hash_bytes(&report_json),
        report_markdown_sha256: hash_bytes(&report_markdown),
        nonclaims: gateway_report_required_nonclaims(),
        metrics: report.metrics.clone(),
    };

    Ok(GatewayReportArtifact {
        manifest,
        report_json,
        report_markdown,
    })
}

pub fn render_gateway_report_markdown(
    report: &GatewayCorpusReport,
    policy: &GatewayActionPolicy,
) -> String {
    let mut markdown = String::new();
    markdown.push_str("# HSAI Gateway Local Report\n\n");
    markdown.push_str(GATEWAY_REPORT_CLAIM_BOUNDARY);
    markdown.push_str("\n\n");
    markdown.push_str("## Policy\n\n");
    markdown.push_str("- policy_id: `");
    markdown.push_str(&policy.id.0);
    markdown.push_str("`\n");
    markdown.push_str("- max_value_units: `");
    markdown.push_str(&policy.max_value_units.to_string());
    markdown.push_str("`\n");
    markdown.push_str("- require_non_secret_model_lane: `");
    markdown.push_str(if policy.require_non_secret_model_lane {
        "true"
    } else {
        "false"
    });
    markdown.push_str("`\n\n");

    markdown.push_str("## Metrics\n\n");
    markdown.push_str("| metric | value |\n");
    markdown.push_str("| --- | ---: |\n");
    append_metric_row(&mut markdown, "total_cases", report.metrics.total_cases);
    append_metric_row(
        &mut markdown,
        "accepted_count",
        report.metrics.accepted_count,
    );
    append_metric_row(
        &mut markdown,
        "rejected_count",
        report.metrics.rejected_count,
    );
    append_metric_row(
        &mut markdown,
        "quarantined_count",
        report.metrics.quarantined_count,
    );
    append_metric_row(
        &mut markdown,
        "unsafe_action_blocked_count",
        report.metrics.unsafe_action_blocked_count,
    );
    append_metric_row(
        &mut markdown,
        "false_rejection_count",
        report.metrics.false_rejection_count,
    );
    append_metric_row(
        &mut markdown,
        "replay_or_tamper_detection_count",
        report.metrics.replay_or_tamper_detection_count,
    );
    append_metric_row(
        &mut markdown,
        "duplicate_key_detection_count",
        report.metrics.duplicate_key_detection_count,
    );
    append_metric_row(
        &mut markdown,
        "policy_downgrade_detection_count",
        report.metrics.policy_downgrade_detection_count,
    );
    append_metric_row(
        &mut markdown,
        "decision_recomputation_agreement_count",
        report.metrics.decision_recomputation_agreement_count,
    );
    markdown.push_str("| audit_bundle_complete | ");
    markdown.push_str(if report.metrics.audit_bundle_complete {
        "true"
    } else {
        "false"
    });
    markdown.push_str(" |\n\n");

    markdown.push_str("## Outcomes\n\n");
    markdown.push_str("| proposal | verdict | handoff | action_digest |\n");
    markdown.push_str("| --- | --- | --- | --- |\n");
    for outcome in &report.outcomes {
        markdown.push_str("| `");
        markdown.push_str(&outcome.proposal_id.0);
        markdown.push_str("` | `");
        markdown.push_str(match outcome.decision.verdict {
            AdmissionVerdict::Accepted => "accepted",
            AdmissionVerdict::Rejected => "rejected",
            AdmissionVerdict::Quarantined => "quarantined",
        });
        markdown.push_str("` | `");
        markdown.push_str(if outcome.accepted_handoff.is_some() {
            "accepted-only"
        } else {
            "none"
        });
        markdown.push_str("` | `");
        markdown.push_str(&hash_hex(outcome.action_digest));
        markdown.push_str("` |\n");
    }

    markdown.push_str("\n## Nonclaims\n\n");
    for label in gateway_report_required_nonclaims() {
        markdown.push_str("- ");
        markdown.push_str(&label.0);
        markdown.push('\n');
    }

    markdown
}

pub fn materialize_gateway_report_bundle(
    output_root: &Path,
    report: &GatewayCorpusReport,
    policy: &GatewayActionPolicy,
    request: &GatewayReportMaterializationRequest,
) -> Result<GatewayReportOutputManifest, GatewayReportMaterializationError> {
    validate_gateway_report_materialization_request(output_root, report, policy, request)?;

    let staging_root = gateway_staging_root_for(output_root, &request.bundle_id)?;
    if staging_root.exists() {
        remove_gateway_dir_all_checked(&staging_root)?;
    }
    fs::create_dir_all(staging_root.join("gateway-report")).map_err(gateway_io_error)?;

    let artifact = gateway_report_artifact(report, policy).map_err(gateway_artifact_error)?;
    let files = build_gateway_report_bundle_files(&artifact, policy, request)?;
    for (logical_path, bytes) in &files {
        let target = staging_root.join(logical_path);
        if let Some(parent) = target.parent() {
            fs::create_dir_all(parent).map_err(gateway_io_error)?;
        }
        fs::write(&target, bytes).map_err(gateway_io_error)?;
        fs::write(
            sidecar_path(&target),
            hash_hex(hash_bytes(bytes)).into_bytes(),
        )
        .map_err(gateway_io_error)?;
    }

    if output_root.exists() {
        if !request.overwrite {
            remove_gateway_dir_all_checked(&staging_root)?;
            return Err(GatewayReportMaterializationError::OutputRootExistsWithoutOverwrite);
        }
        remove_gateway_dir_all_checked(output_root)?;
    }
    fs::rename(&staging_root, output_root).map_err(gateway_io_error)?;
    read_gateway_report_bundle(output_root)
}

pub fn read_gateway_report_bundle(
    output_root: &Path,
) -> Result<GatewayReportOutputManifest, GatewayReportMaterializationError> {
    let output_metadata = fs::symlink_metadata(output_root).map_err(gateway_io_error)?;
    if output_metadata.file_type().is_symlink() {
        return Err(GatewayReportMaterializationError::OutputRootIsSymlink);
    }
    if !output_metadata.is_dir() {
        return Err(GatewayReportMaterializationError::OutputRootIsFile);
    }
    let bundle_dir = output_root.join("gateway-report");
    let bundle_metadata = fs::symlink_metadata(&bundle_dir).map_err(gateway_io_error)?;
    if bundle_metadata.file_type().is_symlink() {
        return Err(GatewayReportMaterializationError::BundleFileIsSymlink(
            "gateway-report".to_owned(),
        ));
    }
    if !bundle_metadata.is_dir() {
        return Err(GatewayReportMaterializationError::DeclaredFileTypeMismatch(
            "gateway-report".to_owned(),
        ));
    }

    reject_undeclared_gateway_report_files(output_root)?;
    let mut file_bytes = BTreeMap::new();
    for logical_path in GATEWAY_REPORT_DECLARED_FILES {
        let path = output_root.join(logical_path);
        let metadata = fs::symlink_metadata(&path).map_err(gateway_io_error)?;
        if metadata.file_type().is_symlink() {
            return Err(GatewayReportMaterializationError::BundleFileIsSymlink(
                (*logical_path).to_owned(),
            ));
        }
        if !metadata.is_file() {
            return Err(GatewayReportMaterializationError::DeclaredFileTypeMismatch(
                (*logical_path).to_owned(),
            ));
        }
        let sidecar = sidecar_path(&path);
        let sidecar_metadata = fs::symlink_metadata(&sidecar).map_err(gateway_io_error)?;
        if sidecar_metadata.file_type().is_symlink() {
            return Err(GatewayReportMaterializationError::SidecarIsSymlink(
                format!("{logical_path}.sha256"),
            ));
        }
        if !sidecar_metadata.is_file() {
            return Err(GatewayReportMaterializationError::DeclaredFileTypeMismatch(
                format!("{logical_path}.sha256"),
            ));
        }
        let bytes = fs::read(&path).map_err(gateway_io_error)?;
        let expected = fs::read_to_string(sidecar).map_err(gateway_io_error)?;
        if expected != hash_hex(hash_bytes(&bytes)) {
            return Err(GatewayReportMaterializationError::DigestMismatch(
                (*logical_path).to_owned(),
            ));
        }
        file_bytes.insert((*logical_path).to_owned(), bytes);
    }

    validate_gateway_report_bundle_semantics(&file_bytes)
}

pub fn materialize_gateway_corpus_output_run(
    output_root: &Path,
    cases: &[GatewayCorpusCase],
    policy: &GatewayActionPolicy,
    request: &GatewayReportMaterializationRequest,
) -> Result<GatewayCorpusOutputRun, GatewayCorpusOutputRunError> {
    let report =
        evaluate_gateway_corpus(cases, policy).map_err(GatewayCorpusOutputRunError::Evaluation)?;
    let output_manifest = materialize_gateway_report_bundle(output_root, &report, policy, request)
        .map_err(GatewayCorpusOutputRunError::Materialization)?;
    Ok(GatewayCorpusOutputRun {
        report,
        output_manifest,
    })
}

pub fn materialize_gateway_adversarial_corpus_output_run(
    output_root: &Path,
    corpus: &GatewayAdversarialCorpus,
    model_lane_registry: &GatewayModelLaneRegistry,
    policy: &GatewayActionPolicy,
    request: &GatewayReportMaterializationRequest,
) -> Result<GatewayCorpusOutputRun, GatewayCorpusOutputRunError> {
    let corpus_issues = validate_gateway_adversarial_corpus(corpus, model_lane_registry);
    if !corpus_issues.is_empty() {
        return Err(GatewayCorpusOutputRunError::CorpusValidation(corpus_issues));
    }
    materialize_gateway_corpus_output_run(output_root, &corpus.cases, policy, request)
}

const ADMISSION_JOURNAL_CLAIM_BOUNDARY: &str =
    "local admission-trace metadata only; not accepted evidence, proof, or benchmark evidence";

const GATEWAY_REPORT_CLAIM_BOUNDARY: &str =
    "local gateway report metadata only; not benchmark evidence, proof, production readiness, semantic correctness, global uniqueness, or a fully secure system";

const GATEWAY_BASELINE_COMPARISON_CLAIM_BOUNDARY: &str =
    "local gateway baseline comparison metadata only; not benchmark evidence, production readiness, semantic correctness, global uniqueness, or a fully secure system";

const GATEWAY_EFFECTIVENESS_SUMMARY_CLAIM_BOUNDARY: &str =
    "local gateway effectiveness summary metadata only; not benchmark evidence, production readiness, semantic correctness, global uniqueness, or a fully secure system";

const GATEWAY_OPERATOR_BRIDGE_BUNDLE_SCHEMA_VERSION: &str =
    "hsai-gateway-operator-bridge-bundle-v1";

const GATEWAY_OPERATOR_BRIDGE_OUTPUT_SCHEMA_VERSION: &str =
    "hsai-gateway-operator-bridge-output-v1";

const GATEWAY_OPERATOR_BRIDGE_VALIDATION_SCHEMA_VERSION: &str =
    "hsai-gateway-operator-bridge-validation-v1";

const GATEWAY_OPERATOR_BRIDGE_PROMOTION_PREFLIGHT_REQUEST_SCHEMA_VERSION: &str =
    "hsai-gateway-operator-bridge-promotion-preflight-request-v1";

const GATEWAY_OPERATOR_BRIDGE_PROMOTION_PREFLIGHT_REPORT_SCHEMA_VERSION: &str =
    "hsai-gateway-operator-bridge-promotion-preflight-report-v1";

const GATEWAY_OPERATOR_BRIDGE_ACCEPTANCE_PREVIEW_REQUEST_SCHEMA_VERSION: &str =
    "hsai-gateway-operator-bridge-acceptance-preview-request-v1";

const GATEWAY_OPERATOR_BRIDGE_ACCEPTANCE_PREVIEW_REPORT_SCHEMA_VERSION: &str =
    "hsai-gateway-operator-bridge-acceptance-preview-report-v1";

const GATEWAY_REPORT_DECLARED_FILES: &[&str] = &[
    "gateway-report/manifest.json",
    "gateway-report/report.json",
    "gateway-report/report.md",
    "gateway-report/non-claims.md",
    "gateway-report/validation-report.json",
];

const GATEWAY_REPORT_DECLARED_SIDECARS: &[&str] = &[
    "gateway-report/manifest.json.sha256",
    "gateway-report/report.json.sha256",
    "gateway-report/report.md.sha256",
    "gateway-report/non-claims.md.sha256",
    "gateway-report/validation-report.json.sha256",
];

const GATEWAY_OPERATOR_BRIDGE_DECLARED_FILES: &[&str] = &[
    "gateway-bridge/manifest.json",
    "gateway-bridge/bridge-bundle.json",
    "gateway-bridge/attestation-binding.json",
    "gateway-bridge/operator-artifact-reference.json",
    "gateway-bridge/non-claims.md",
    "gateway-bridge/validation-report.json",
];

const GATEWAY_OPERATOR_BRIDGE_DECLARED_SIDECARS: &[&str] = &[
    "gateway-bridge/manifest.json.sha256",
    "gateway-bridge/bridge-bundle.json.sha256",
    "gateway-bridge/attestation-binding.json.sha256",
    "gateway-bridge/operator-artifact-reference.json.sha256",
    "gateway-bridge/non-claims.md.sha256",
    "gateway-bridge/validation-report.json.sha256",
];

const ADMISSION_JOURNAL_DECLARED_FILES: &[&str] = &[
    "admission-journal/manifest.json",
    "admission-journal/journal.json",
    "admission-journal/decisions.jsonl",
    "admission-journal/source-digests.json",
    "admission-journal/non-claims.md",
    "admission-journal/redaction-report.json",
    "admission-journal/validation-report.json",
];

const ADMISSION_JOURNAL_DECLARED_SIDECARS: &[&str] = &[
    "admission-journal/manifest.json.sha256",
    "admission-journal/journal.json.sha256",
    "admission-journal/decisions.jsonl.sha256",
    "admission-journal/source-digests.json.sha256",
    "admission-journal/non-claims.md.sha256",
    "admission-journal/redaction-report.json.sha256",
    "admission-journal/validation-report.json.sha256",
];

fn is_full_hex_sha(value: &str) -> bool {
    value.len() == 40 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn is_safe_relative_path(value: &str) -> bool {
    !value.is_empty()
        && !value.starts_with('/')
        && !value.starts_with('\\')
        && !value.contains('\\')
        && !value
            .split('/')
            .any(|part| part.is_empty() || part == "." || part == ".." || part.contains(':'))
}

fn hash_bytes(bytes: &[u8]) -> Hash {
    let digest = Sha256::digest(bytes);
    let mut out = [0; 32];
    out.copy_from_slice(&digest);
    Hash(out)
}

fn hash_hex(hash: Hash) -> String {
    let mut out = String::with_capacity(64);
    for byte in hash.0 {
        out.push_str(&format!("{byte:02x}"));
    }
    out
}

fn bytes_hex(bytes: &[u8]) -> String {
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        out.push_str(&format!("{byte:02x}"));
    }
    out
}

fn normalize_lower_hex(value: &str) -> String {
    value.trim().to_ascii_lowercase()
}

fn decode_lower_hex(
    field: &'static str,
    value: &str,
) -> Result<Vec<u8>, GatewayAttestationBindingError> {
    let normalized = normalize_lower_hex(value);
    if normalized.is_empty() || normalized.len() % 2 != 0 {
        return Err(GatewayAttestationBindingError::InvalidHex {
            field,
            value: value.to_owned(),
        });
    }
    let mut out = Vec::with_capacity(normalized.len() / 2);
    for chunk in normalized.as_bytes().chunks_exact(2) {
        let hex =
            std::str::from_utf8(chunk).map_err(|_| GatewayAttestationBindingError::InvalidHex {
                field,
                value: value.to_owned(),
            })?;
        let byte = u8::from_str_radix(hex, 16).map_err(|_| {
            GatewayAttestationBindingError::InvalidHex {
                field,
                value: value.to_owned(),
            }
        })?;
        out.push(byte);
    }
    Ok(out)
}

fn gateway_attestation_challenge_id(binding: &GatewayAttestationChallengeBinding) -> String {
    #[derive(Serialize)]
    struct ChallengeIdMaterial<'a> {
        schema_version: &'a str,
        proposal_id: &'a GatewayActionId,
        subject: &'a SubjectId,
        policy_id: &'a AdmissionPolicyId,
        anchor_id: &'a str,
        agent_pubkey_spki_hex: &'a str,
        nonce: u64,
        challenge_created_at: u64,
        challenge_expires_at: u64,
        gateway_case_hash_hex: &'a str,
        expected_report_data_hex: &'a str,
        claim_boundary: &'a str,
        authority_granted: bool,
        nonclaims: &'a BTreeSet<NonClaimLabel>,
    }

    hash_hex(hash_tagged(
        "hsai-agent-admission:gateway-attestation-challenge-id:v1",
        &ChallengeIdMaterial {
            schema_version: &binding.schema_version,
            proposal_id: &binding.proposal_id,
            subject: &binding.subject,
            policy_id: &binding.policy_id,
            anchor_id: &binding.anchor_id,
            agent_pubkey_spki_hex: &binding.agent_pubkey_spki_hex,
            nonce: binding.nonce,
            challenge_created_at: binding.challenge_created_at,
            challenge_expires_at: binding.challenge_expires_at,
            gateway_case_hash_hex: &binding.gateway_case_hash_hex,
            expected_report_data_hex: &binding.expected_report_data_hex,
            claim_boundary: &binding.claim_boundary,
            authority_granted: binding.authority_granted,
            nonclaims: &binding.nonclaims,
        },
    ))
}

fn append_metric_row(markdown: &mut String, name: &str, value: u64) {
    markdown.push_str("| ");
    markdown.push_str(name);
    markdown.push_str(" | ");
    markdown.push_str(&value.to_string());
    markdown.push_str(" |\n");
}

fn validate_gateway_report_materialization_request(
    output_root: &Path,
    report: &GatewayCorpusReport,
    policy: &GatewayActionPolicy,
    request: &GatewayReportMaterializationRequest,
) -> Result<(), GatewayReportMaterializationError> {
    if request.bundle_id.trim().is_empty()
        || !is_safe_relative_path(&request.bundle_id)
        || request.bundle_id.contains(['/', '\\'])
    {
        return Err(GatewayReportMaterializationError::EmptyBundleId);
    }
    let issues = validate_gateway_corpus_report(report, policy);
    if !issues.is_empty() {
        return Err(GatewayReportMaterializationError::InvalidReport(issues));
    }
    validate_gateway_output_root(output_root, &request.protected_roots, request.overwrite)
}

fn build_gateway_report_bundle_files(
    artifact: &GatewayReportArtifact,
    policy: &GatewayActionPolicy,
    request: &GatewayReportMaterializationRequest,
) -> Result<BTreeMap<String, Vec<u8>>, GatewayReportMaterializationError> {
    let nonclaims = gateway_report_nonclaims_markdown(&artifact.manifest.nonclaims).into_bytes();
    let validation = GatewayReportOutputValidationReport {
        schema_version: "hsai-gateway-report-output-validation-v1".to_owned(),
        bundle_id: request.bundle_id.clone(),
        valid: true,
        report_issue_count: 0,
        claim_boundary: GATEWAY_REPORT_CLAIM_BOUNDARY.to_owned(),
        checked_files: gateway_report_declared_files(),
    };
    let validation_bytes = serde_json::to_vec_pretty(&validation).map_err(gateway_serde_error)?;
    let mut files = BTreeMap::from([
        (
            "gateway-report/report.json".to_owned(),
            artifact.report_json.clone(),
        ),
        (
            "gateway-report/report.md".to_owned(),
            artifact.report_markdown.clone(),
        ),
        ("gateway-report/non-claims.md".to_owned(), nonclaims),
        (
            "gateway-report/validation-report.json".to_owned(),
            validation_bytes,
        ),
    ]);
    let manifest = gateway_report_output_manifest_for_files(artifact, policy, request, &files);
    files.insert(
        "gateway-report/manifest.json".to_owned(),
        serde_json::to_vec_pretty(&manifest).map_err(gateway_serde_error)?,
    );
    Ok(files)
}

fn gateway_report_output_manifest_for_files(
    artifact: &GatewayReportArtifact,
    policy: &GatewayActionPolicy,
    request: &GatewayReportMaterializationRequest,
    files: &BTreeMap<String, Vec<u8>>,
) -> GatewayReportOutputManifest {
    let mut declared_file_digests = BTreeMap::new();
    for (logical_path, bytes) in files {
        declared_file_digests.insert(logical_path.clone(), hash_bytes(bytes));
    }
    GatewayReportOutputManifest {
        schema_version: "hsai-gateway-report-output-v1".to_owned(),
        bundle_id: request.bundle_id.clone(),
        created_at_unix: request.created_at_unix,
        gateway_policy: policy.clone(),
        artifact_manifest: artifact.manifest.clone(),
        declared_files: gateway_report_declared_files(),
        declared_file_digests,
        claim_boundary: GATEWAY_REPORT_CLAIM_BOUNDARY.to_owned(),
    }
}

fn validate_gateway_report_bundle_semantics(
    files: &BTreeMap<String, Vec<u8>>,
) -> Result<GatewayReportOutputManifest, GatewayReportMaterializationError> {
    let manifest: GatewayReportOutputManifest =
        parse_gateway_declared_json(files, "gateway-report/manifest.json")?;
    let report: GatewayCorpusReport =
        parse_gateway_declared_json(files, "gateway-report/report.json")?;
    let issues = validate_gateway_corpus_report(&report, &manifest.gateway_policy);
    if !issues.is_empty() {
        return Err(GatewayReportMaterializationError::InvalidReport(issues));
    }

    validate_gateway_report_manifest_semantics(&manifest, &report, files)?;

    let report_markdown = declared_gateway_bytes(files, "gateway-report/report.md")?;
    if report_markdown
        != render_gateway_report_markdown(&report, &manifest.gateway_policy).as_bytes()
    {
        return Err(GatewayReportMaterializationError::ManifestSemanticMismatch);
    }

    let nonclaims = declared_gateway_bytes(files, "gateway-report/non-claims.md")?;
    if nonclaims
        != gateway_report_nonclaims_markdown(&manifest.artifact_manifest.nonclaims).as_bytes()
    {
        return Err(GatewayReportMaterializationError::NonclaimMismatch);
    }

    let validation: GatewayReportOutputValidationReport =
        parse_gateway_declared_json(files, "gateway-report/validation-report.json")?;
    let expected_validation = GatewayReportOutputValidationReport {
        schema_version: "hsai-gateway-report-output-validation-v1".to_owned(),
        bundle_id: manifest.bundle_id.clone(),
        valid: true,
        report_issue_count: 0,
        claim_boundary: GATEWAY_REPORT_CLAIM_BOUNDARY.to_owned(),
        checked_files: gateway_report_declared_files(),
    };
    if validation != expected_validation {
        return Err(GatewayReportMaterializationError::ValidationReportMismatch);
    }

    Ok(manifest)
}

fn validate_operator_artifact_reference(
    reference: &GatewayOperatorArtifactReference,
) -> Result<(), ()> {
    if !is_portable_artifact_id(&reference.reference_id)
        || reference.provider.trim().is_empty()
        || reference.artifact_kind.trim().is_empty()
        || reference.operator_run_id.trim().is_empty()
        || reference.artifact_digest.sha256 == Hash([0; 32])
        || !is_portable_artifact_id(&reference.artifact_digest.id)
        || !reference.repo_external
        || reference.claim_boundary.trim().is_empty()
    {
        return Err(());
    }
    for required in gateway_operator_bridge_required_nonclaims() {
        if !reference.nonclaims.contains(&required) {
            return Err(());
        }
    }
    Ok(())
}

fn gateway_operator_bridge_manifest_matches_bundle(
    manifest: &GatewayOperatorBridgeOutputManifest,
    bundle: &GatewayOperatorBridgeBundle,
) -> bool {
    let expected_digest_paths: BTreeSet<String> = GATEWAY_OPERATOR_BRIDGE_DECLARED_FILES
        .iter()
        .filter(|path| **path != "gateway-bridge/manifest.json")
        .map(|path| (*path).to_owned())
        .collect();
    let actual_digest_paths: BTreeSet<String> =
        manifest.declared_file_digests.keys().cloned().collect();
    manifest.schema_version == GATEWAY_OPERATOR_BRIDGE_OUTPUT_SCHEMA_VERSION
        && manifest.bundle_id == bundle.bundle_id
        && manifest.created_at_unix == bundle.created_at_unix
        && manifest.bridge_bundle_digest == bundle.digest()
        && manifest.gateway_report_digest == bundle.gateway_report_digest
        && manifest.gateway_report_manifest_digest == bundle.gateway_report_manifest_digest
        && manifest.attestation_binding_digest == bundle.attestation_binding.digest()
        && manifest.operator_artifact_reference_digest
            == bundle.operator_artifact_reference.digest()
        && manifest.declared_files == gateway_operator_bridge_declared_files()
        && actual_digest_paths == expected_digest_paths
        && manifest
            .declared_file_digests
            .values()
            .all(|digest| *digest != Hash([0; 32]))
        && manifest.claim_boundary == bundle.claim_boundary
        && !manifest.authority_granted
        && !manifest.accepted_evidence_mutation
        && manifest.nonclaims == bundle.nonclaims
}

fn gateway_operator_bridge_promotion_forbidden_claim_fragments() -> &'static [&'static str] {
    &[
        "sota",
        "state of the art",
        "breakthrough",
        "production ready",
        "production readiness",
        "semantically correct",
        "semantic correctness",
        "live provider evidence",
        "level2",
        "level 2",
        "accepted evidence",
        "fully secure",
        "full security",
    ]
}

fn validate_gateway_operator_bridge_materialization_request(
    output_root: &Path,
    bundle: &GatewayOperatorBridgeBundle,
    request: &GatewayOperatorBridgeMaterializationRequest,
) -> Result<(), GatewayOperatorBridgeMaterializationError> {
    if request.bundle_id.trim().is_empty()
        || !is_safe_relative_path(&request.bundle_id)
        || request.bundle_id.contains(['/', '\\'])
        || request.bundle_id != bundle.bundle_id
    {
        return Err(GatewayOperatorBridgeMaterializationError::EmptyBundleId);
    }
    let issues = validate_gateway_operator_bridge_bundle(bundle);
    if !issues.is_empty() {
        return Err(GatewayOperatorBridgeMaterializationError::InvalidBundle(
            issues,
        ));
    }
    validate_gateway_output_root(output_root, &request.protected_roots, request.overwrite)
        .map_err(gateway_bridge_from_report_error)
}

fn build_gateway_operator_bridge_files(
    bundle: &GatewayOperatorBridgeBundle,
) -> Result<BTreeMap<String, Vec<u8>>, GatewayOperatorBridgeMaterializationError> {
    let nonclaims = gateway_bridge_nonclaims_markdown(&bundle.nonclaims).into_bytes();
    let validation = GatewayOperatorBridgeValidationReport {
        schema_version: GATEWAY_OPERATOR_BRIDGE_VALIDATION_SCHEMA_VERSION.to_owned(),
        bundle_id: bundle.bundle_id.clone(),
        valid: true,
        issue_count: 0,
        checked_files: gateway_operator_bridge_declared_files(),
        claim_boundary: bundle.claim_boundary.clone(),
        authority_granted: false,
        accepted_evidence_mutation: false,
    };
    let validation_bytes =
        serde_json::to_vec_pretty(&validation).map_err(gateway_bridge_serde_error)?;
    let mut files = BTreeMap::from([
        (
            "gateway-bridge/bridge-bundle.json".to_owned(),
            serde_json::to_vec_pretty(bundle).map_err(gateway_bridge_serde_error)?,
        ),
        (
            "gateway-bridge/attestation-binding.json".to_owned(),
            serde_json::to_vec_pretty(&bundle.attestation_binding)
                .map_err(gateway_bridge_serde_error)?,
        ),
        (
            "gateway-bridge/operator-artifact-reference.json".to_owned(),
            serde_json::to_vec_pretty(&bundle.operator_artifact_reference)
                .map_err(gateway_bridge_serde_error)?,
        ),
        ("gateway-bridge/non-claims.md".to_owned(), nonclaims),
        (
            "gateway-bridge/validation-report.json".to_owned(),
            validation_bytes,
        ),
    ]);
    let manifest = gateway_operator_bridge_output_manifest_for_files(bundle, &files);
    files.insert(
        "gateway-bridge/manifest.json".to_owned(),
        serde_json::to_vec_pretty(&manifest).map_err(gateway_bridge_serde_error)?,
    );
    Ok(files)
}

fn gateway_operator_bridge_output_manifest_for_files(
    bundle: &GatewayOperatorBridgeBundle,
    files: &BTreeMap<String, Vec<u8>>,
) -> GatewayOperatorBridgeOutputManifest {
    let mut declared_file_digests = BTreeMap::new();
    for (logical_path, bytes) in files {
        declared_file_digests.insert(logical_path.clone(), hash_bytes(bytes));
    }
    GatewayOperatorBridgeOutputManifest {
        schema_version: GATEWAY_OPERATOR_BRIDGE_OUTPUT_SCHEMA_VERSION.to_owned(),
        bundle_id: bundle.bundle_id.clone(),
        created_at_unix: bundle.created_at_unix,
        bridge_bundle_digest: bundle.digest(),
        gateway_report_digest: bundle.gateway_report_digest,
        gateway_report_manifest_digest: bundle.gateway_report_manifest_digest,
        attestation_binding_digest: bundle.attestation_binding.digest(),
        operator_artifact_reference_digest: bundle.operator_artifact_reference.digest(),
        declared_files: gateway_operator_bridge_declared_files(),
        declared_file_digests,
        claim_boundary: bundle.claim_boundary.clone(),
        authority_granted: false,
        accepted_evidence_mutation: false,
        nonclaims: bundle.nonclaims.clone(),
    }
}

fn validate_gateway_operator_bridge_files(
    files: &BTreeMap<String, Vec<u8>>,
) -> Result<GatewayOperatorBridgeOutputManifest, GatewayOperatorBridgeMaterializationError> {
    let manifest: GatewayOperatorBridgeOutputManifest =
        parse_gateway_bridge_declared_json(files, "gateway-bridge/manifest.json")?;
    let bundle: GatewayOperatorBridgeBundle =
        parse_gateway_bridge_declared_json(files, "gateway-bridge/bridge-bundle.json")?;
    let binding: GatewayAttestationChallengeBinding =
        parse_gateway_bridge_declared_json(files, "gateway-bridge/attestation-binding.json")?;
    let reference: GatewayOperatorArtifactReference = parse_gateway_bridge_declared_json(
        files,
        "gateway-bridge/operator-artifact-reference.json",
    )?;

    if binding != bundle.attestation_binding || reference != bundle.operator_artifact_reference {
        return Err(GatewayOperatorBridgeMaterializationError::ManifestSemanticMismatch);
    }
    let issues = validate_gateway_operator_bridge_bundle(&bundle);
    if !issues.is_empty() {
        return Err(GatewayOperatorBridgeMaterializationError::InvalidBundle(
            issues,
        ));
    }
    validate_gateway_operator_bridge_manifest_semantics(&manifest, &bundle, files)?;

    let nonclaims = declared_gateway_bridge_bytes(files, "gateway-bridge/non-claims.md")?;
    if nonclaims != gateway_bridge_nonclaims_markdown(&bundle.nonclaims).as_bytes() {
        return Err(GatewayOperatorBridgeMaterializationError::NonclaimMismatch);
    }

    let validation: GatewayOperatorBridgeValidationReport =
        parse_gateway_bridge_declared_json(files, "gateway-bridge/validation-report.json")?;
    let expected_validation = GatewayOperatorBridgeValidationReport {
        schema_version: GATEWAY_OPERATOR_BRIDGE_VALIDATION_SCHEMA_VERSION.to_owned(),
        bundle_id: bundle.bundle_id.clone(),
        valid: true,
        issue_count: 0,
        checked_files: gateway_operator_bridge_declared_files(),
        claim_boundary: bundle.claim_boundary.clone(),
        authority_granted: false,
        accepted_evidence_mutation: false,
    };
    if validation != expected_validation {
        return Err(GatewayOperatorBridgeMaterializationError::ValidationReportMismatch);
    }

    Ok(manifest)
}

fn validate_gateway_operator_bridge_manifest_semantics(
    manifest: &GatewayOperatorBridgeOutputManifest,
    bundle: &GatewayOperatorBridgeBundle,
    files: &BTreeMap<String, Vec<u8>>,
) -> Result<(), GatewayOperatorBridgeMaterializationError> {
    let expected_digest_paths: BTreeSet<String> = GATEWAY_OPERATOR_BRIDGE_DECLARED_FILES
        .iter()
        .filter(|path| **path != "gateway-bridge/manifest.json")
        .map(|path| (*path).to_owned())
        .collect();
    let actual_digest_paths: BTreeSet<String> =
        manifest.declared_file_digests.keys().cloned().collect();

    if manifest.schema_version != GATEWAY_OPERATOR_BRIDGE_OUTPUT_SCHEMA_VERSION
        || manifest.bundle_id != bundle.bundle_id
        || manifest.created_at_unix != bundle.created_at_unix
        || manifest.bridge_bundle_digest != bundle.digest()
        || manifest.gateway_report_digest != bundle.gateway_report_digest
        || manifest.gateway_report_manifest_digest != bundle.gateway_report_manifest_digest
        || manifest.attestation_binding_digest != bundle.attestation_binding.digest()
        || manifest.operator_artifact_reference_digest
            != bundle.operator_artifact_reference.digest()
        || manifest.declared_files != gateway_operator_bridge_declared_files()
        || actual_digest_paths != expected_digest_paths
        || manifest.claim_boundary != bundle.claim_boundary
        || manifest.authority_granted
        || manifest.accepted_evidence_mutation
        || manifest.nonclaims != bundle.nonclaims
    {
        return Err(GatewayOperatorBridgeMaterializationError::ManifestSemanticMismatch);
    }

    for (logical_path, expected_digest) in &manifest.declared_file_digests {
        if hash_bytes(declared_gateway_bridge_bytes(files, logical_path)?) != *expected_digest {
            return Err(GatewayOperatorBridgeMaterializationError::ManifestSemanticMismatch);
        }
    }
    Ok(())
}

fn gateway_operator_bridge_declared_files() -> Vec<String> {
    GATEWAY_OPERATOR_BRIDGE_DECLARED_FILES
        .iter()
        .map(|value| (*value).to_owned())
        .collect()
}

fn declared_gateway_bridge_bytes<'a>(
    files: &'a BTreeMap<String, Vec<u8>>,
    logical_path: &str,
) -> Result<&'a [u8], GatewayOperatorBridgeMaterializationError> {
    files.get(logical_path).map(Vec::as_slice).ok_or_else(|| {
        GatewayOperatorBridgeMaterializationError::Io(format!(
            "declared file missing: {logical_path}"
        ))
    })
}

fn parse_gateway_bridge_declared_json<T: for<'de> Deserialize<'de> + Serialize>(
    files: &BTreeMap<String, Vec<u8>>,
    logical_path: &str,
) -> Result<T, GatewayOperatorBridgeMaterializationError> {
    let bytes = declared_gateway_bridge_bytes(files, logical_path)?;
    let original = parse_json_value_rejecting_duplicate_keys(bytes).map_err(|_| {
        GatewayOperatorBridgeMaterializationError::MalformedDeclaredFile(logical_path.to_owned())
    })?;
    let parsed: T = serde_json::from_value(original.clone()).map_err(|_| {
        GatewayOperatorBridgeMaterializationError::MalformedDeclaredFile(logical_path.to_owned())
    })?;
    let canonical = serde_json::to_value(&parsed).map_err(gateway_bridge_serde_error)?;
    if canonical != original {
        return Err(
            GatewayOperatorBridgeMaterializationError::MalformedDeclaredFile(
                logical_path.to_owned(),
            ),
        );
    }
    Ok(parsed)
}

fn gateway_bridge_nonclaims_markdown(nonclaims: &BTreeSet<NonClaimLabel>) -> String {
    let mut out = String::from("# Gateway Operator Bridge Non-Claims\n\n");
    for nonclaim in nonclaims {
        out.push_str("- ");
        out.push_str(&nonclaim.0);
        out.push('\n');
    }
    out
}

fn reject_undeclared_gateway_bridge_files(
    output_root: &Path,
) -> Result<(), GatewayOperatorBridgeMaterializationError> {
    let mut declared: BTreeSet<String> = GATEWAY_OPERATOR_BRIDGE_DECLARED_FILES
        .iter()
        .chain(GATEWAY_OPERATOR_BRIDGE_DECLARED_SIDECARS.iter())
        .map(|value| (*value).to_owned())
        .collect();
    let bundle_dir = output_root.join("gateway-bridge");
    for entry in fs::read_dir(&bundle_dir).map_err(gateway_bridge_io_error)? {
        let entry = entry.map_err(gateway_bridge_io_error)?;
        let logical_path = entry
            .path()
            .strip_prefix(output_root)
            .map_err(|error| GatewayOperatorBridgeMaterializationError::Io(error.to_string()))?
            .to_string_lossy()
            .replace('\\', "/");
        if !declared.remove(&logical_path) {
            return Err(GatewayOperatorBridgeMaterializationError::UndeclaredFile(
                logical_path,
            ));
        }
    }
    if let Some(missing) = declared.into_iter().next() {
        return Err(GatewayOperatorBridgeMaterializationError::Io(format!(
            "declared file missing: {missing}"
        )));
    }
    Ok(())
}

fn validate_gateway_report_manifest_semantics(
    manifest: &GatewayReportOutputManifest,
    report: &GatewayCorpusReport,
    files: &BTreeMap<String, Vec<u8>>,
) -> Result<(), GatewayReportMaterializationError> {
    let expected_digest_paths: BTreeSet<String> = GATEWAY_REPORT_DECLARED_FILES
        .iter()
        .filter(|path| **path != "gateway-report/manifest.json")
        .map(|path| (*path).to_owned())
        .collect();
    let actual_digest_paths: BTreeSet<String> =
        manifest.declared_file_digests.keys().cloned().collect();
    let expected_artifact = gateway_report_artifact(report, &manifest.gateway_policy)
        .map_err(gateway_artifact_error)?;

    if manifest.schema_version != "hsai-gateway-report-output-v1"
        || manifest.bundle_id.trim().is_empty()
        || !is_safe_relative_path(&manifest.bundle_id)
        || manifest.bundle_id.contains(['/', '\\'])
        || manifest.declared_files != gateway_report_declared_files()
        || actual_digest_paths != expected_digest_paths
        || manifest.claim_boundary != GATEWAY_REPORT_CLAIM_BOUNDARY
        || manifest.artifact_manifest != expected_artifact.manifest
    {
        return Err(GatewayReportMaterializationError::ManifestSemanticMismatch);
    }

    for (logical_path, expected_digest) in &manifest.declared_file_digests {
        if hash_bytes(declared_gateway_bytes(files, logical_path)?) != *expected_digest {
            return Err(GatewayReportMaterializationError::ManifestSemanticMismatch);
        }
    }
    Ok(())
}

fn gateway_report_declared_files() -> Vec<String> {
    GATEWAY_REPORT_DECLARED_FILES
        .iter()
        .map(|value| (*value).to_owned())
        .collect()
}

fn declared_gateway_bytes<'a>(
    files: &'a BTreeMap<String, Vec<u8>>,
    logical_path: &str,
) -> Result<&'a [u8], GatewayReportMaterializationError> {
    files.get(logical_path).map(Vec::as_slice).ok_or_else(|| {
        GatewayReportMaterializationError::Io(format!("declared file missing: {logical_path}"))
    })
}

fn parse_gateway_declared_json<T: for<'de> Deserialize<'de> + Serialize>(
    files: &BTreeMap<String, Vec<u8>>,
    logical_path: &str,
) -> Result<T, GatewayReportMaterializationError> {
    let bytes = declared_gateway_bytes(files, logical_path)?;
    let original = parse_json_value_rejecting_duplicate_keys(bytes).map_err(|_| {
        GatewayReportMaterializationError::MalformedDeclaredFile(logical_path.to_owned())
    })?;
    let parsed: T = serde_json::from_value(original.clone()).map_err(|_| {
        GatewayReportMaterializationError::MalformedDeclaredFile(logical_path.to_owned())
    })?;
    let canonical = serde_json::to_value(&parsed).map_err(gateway_serde_error)?;
    if canonical != original {
        return Err(GatewayReportMaterializationError::MalformedDeclaredFile(
            logical_path.to_owned(),
        ));
    }
    Ok(parsed)
}

fn gateway_report_nonclaims_markdown(nonclaims: &BTreeSet<NonClaimLabel>) -> String {
    let mut out = String::from("# Gateway Report Non-Claims\n\n");
    for nonclaim in nonclaims {
        out.push_str("- ");
        out.push_str(&nonclaim.0);
        out.push('\n');
    }
    out
}

fn reject_undeclared_gateway_report_files(
    output_root: &Path,
) -> Result<(), GatewayReportMaterializationError> {
    let mut declared: BTreeSet<String> = GATEWAY_REPORT_DECLARED_FILES
        .iter()
        .chain(GATEWAY_REPORT_DECLARED_SIDECARS.iter())
        .map(|value| (*value).to_owned())
        .collect();
    let bundle_dir = output_root.join("gateway-report");
    for entry in fs::read_dir(&bundle_dir).map_err(gateway_io_error)? {
        let entry = entry.map_err(gateway_io_error)?;
        let logical_path = entry
            .path()
            .strip_prefix(output_root)
            .map_err(|error| GatewayReportMaterializationError::Io(error.to_string()))?
            .to_string_lossy()
            .replace('\\', "/");
        if !declared.remove(&logical_path) {
            return Err(GatewayReportMaterializationError::UndeclaredFile(
                logical_path,
            ));
        }
    }
    if let Some(missing) = declared.into_iter().next() {
        return Err(GatewayReportMaterializationError::Io(format!(
            "declared file missing: {missing}"
        )));
    }
    Ok(())
}

fn validate_gateway_output_root(
    output_root: &Path,
    protected_roots: &[PathBuf],
    overwrite: bool,
) -> Result<(), GatewayReportMaterializationError> {
    match validate_output_root(output_root, protected_roots, overwrite) {
        Ok(()) => Ok(()),
        Err(AdmissionJournalMaterializationError::EmptyOutputRoot) => {
            Err(GatewayReportMaterializationError::EmptyOutputRoot)
        }
        Err(AdmissionJournalMaterializationError::ProtectedOutputRoot) => {
            Err(GatewayReportMaterializationError::ProtectedOutputRoot)
        }
        Err(AdmissionJournalMaterializationError::OutputRootExistsWithoutOverwrite) => {
            Err(GatewayReportMaterializationError::OutputRootExistsWithoutOverwrite)
        }
        Err(AdmissionJournalMaterializationError::OutputRootIsFile) => {
            Err(GatewayReportMaterializationError::OutputRootIsFile)
        }
        Err(AdmissionJournalMaterializationError::OutputRootIsSymlink) => {
            Err(GatewayReportMaterializationError::OutputRootIsSymlink)
        }
        Err(AdmissionJournalMaterializationError::Io(error)) => {
            Err(GatewayReportMaterializationError::Io(error))
        }
        Err(other) => Err(GatewayReportMaterializationError::Io(format!("{other:?}"))),
    }
}

fn gateway_staging_root_for(
    output_root: &Path,
    bundle_id: &str,
) -> Result<PathBuf, GatewayReportMaterializationError> {
    let parent = output_root
        .parent()
        .ok_or(GatewayReportMaterializationError::EmptyOutputRoot)?;
    let name = output_root
        .file_name()
        .map(|value| value.to_string_lossy().into_owned())
        .ok_or(GatewayReportMaterializationError::EmptyOutputRoot)?;
    Ok(parent.join(format!(".{name}.{bundle_id}.staging")))
}

fn remove_gateway_dir_all_checked(path: &Path) -> Result<(), GatewayReportMaterializationError> {
    if !path.exists() {
        return Ok(());
    }
    if fs::symlink_metadata(path)
        .map_err(gateway_io_error)?
        .file_type()
        .is_symlink()
    {
        return Err(GatewayReportMaterializationError::OutputRootIsSymlink);
    }
    fs::remove_dir_all(path).map_err(gateway_io_error)
}

fn gateway_artifact_error(error: GatewayReportArtifactError) -> GatewayReportMaterializationError {
    match error {
        GatewayReportArtifactError::InvalidReport(issues) => {
            GatewayReportMaterializationError::InvalidReport(issues)
        }
        GatewayReportArtifactError::Serialization(error) => {
            GatewayReportMaterializationError::Serialization(error)
        }
    }
}

fn gateway_io_error(error: io::Error) -> GatewayReportMaterializationError {
    GatewayReportMaterializationError::Io(error.to_string())
}

fn gateway_serde_error(error: serde_json::Error) -> GatewayReportMaterializationError {
    GatewayReportMaterializationError::Serialization(error.to_string())
}

fn gateway_bridge_from_report_error(
    error: GatewayReportMaterializationError,
) -> GatewayOperatorBridgeMaterializationError {
    match error {
        GatewayReportMaterializationError::EmptyOutputRoot => {
            GatewayOperatorBridgeMaterializationError::EmptyOutputRoot
        }
        GatewayReportMaterializationError::ProtectedOutputRoot => {
            GatewayOperatorBridgeMaterializationError::ProtectedOutputRoot
        }
        GatewayReportMaterializationError::OutputRootExistsWithoutOverwrite => {
            GatewayOperatorBridgeMaterializationError::OutputRootExistsWithoutOverwrite
        }
        GatewayReportMaterializationError::OutputRootIsFile => {
            GatewayOperatorBridgeMaterializationError::OutputRootIsFile
        }
        GatewayReportMaterializationError::OutputRootIsSymlink => {
            GatewayOperatorBridgeMaterializationError::OutputRootIsSymlink
        }
        GatewayReportMaterializationError::Io(error) => {
            GatewayOperatorBridgeMaterializationError::Io(error)
        }
        GatewayReportMaterializationError::Serialization(error) => {
            GatewayOperatorBridgeMaterializationError::Serialization(error)
        }
        other => GatewayOperatorBridgeMaterializationError::Io(format!("{other:?}")),
    }
}

fn gateway_bridge_io_error(error: io::Error) -> GatewayOperatorBridgeMaterializationError {
    GatewayOperatorBridgeMaterializationError::Io(error.to_string())
}

fn gateway_bridge_serde_error(
    error: serde_json::Error,
) -> GatewayOperatorBridgeMaterializationError {
    GatewayOperatorBridgeMaterializationError::Serialization(error.to_string())
}

fn sidecar_path(path: &Path) -> PathBuf {
    let filename = path
        .file_name()
        .map(|name| name.to_string_lossy().into_owned())
        .unwrap_or_default();
    path.with_file_name(format!("{filename}.sha256"))
}

fn staging_root_for(
    output_root: &Path,
    bundle_id: &str,
) -> Result<PathBuf, AdmissionJournalMaterializationError> {
    let parent = output_root
        .parent()
        .ok_or(AdmissionJournalMaterializationError::EmptyOutputRoot)?;
    let name = output_root
        .file_name()
        .map(|value| value.to_string_lossy().into_owned())
        .ok_or(AdmissionJournalMaterializationError::EmptyOutputRoot)?;
    Ok(parent.join(format!(".{name}.{bundle_id}.staging")))
}

fn normalize_for_prefix_check(
    path: &Path,
) -> Result<PathBuf, AdmissionJournalMaterializationError> {
    if path.exists() {
        path.canonicalize().map_err(materialization_io_error)
    } else {
        let parent = path
            .parent()
            .ok_or(AdmissionJournalMaterializationError::EmptyOutputRoot)?;
        let filename = path
            .file_name()
            .ok_or(AdmissionJournalMaterializationError::EmptyOutputRoot)?;
        Ok(parent
            .canonicalize()
            .map_err(materialization_io_error)?
            .join(filename))
    }
}

fn reject_undeclared_bundle_files(
    output_root: &Path,
) -> Result<(), AdmissionJournalMaterializationError> {
    let mut declared: BTreeSet<String> = ADMISSION_JOURNAL_DECLARED_FILES
        .iter()
        .chain(ADMISSION_JOURNAL_DECLARED_SIDECARS.iter())
        .map(|value| (*value).to_owned())
        .collect();
    let bundle_dir = output_root.join("admission-journal");
    for entry in fs::read_dir(&bundle_dir).map_err(materialization_io_error)? {
        let entry = entry.map_err(materialization_io_error)?;
        let path = entry.path();
        let logical_path = path
            .strip_prefix(output_root)
            .map_err(|error| AdmissionJournalMaterializationError::Io(error.to_string()))?
            .to_string_lossy()
            .replace('\\', "/");
        if !declared.remove(&logical_path) {
            return Err(AdmissionJournalMaterializationError::UndeclaredFile(
                logical_path,
            ));
        }
    }
    if let Some(missing) = declared.into_iter().next() {
        return Err(AdmissionJournalMaterializationError::Io(format!(
            "declared file missing: {missing}"
        )));
    }
    Ok(())
}

fn remove_dir_all_checked(path: &Path) -> Result<(), AdmissionJournalMaterializationError> {
    if !path.exists() {
        return Ok(());
    }
    if fs::symlink_metadata(path)
        .map_err(materialization_io_error)?
        .file_type()
        .is_symlink()
    {
        return Err(AdmissionJournalMaterializationError::OutputRootIsSymlink);
    }
    fs::remove_dir_all(path).map_err(materialization_io_error)
}

fn materialization_io_error(error: io::Error) -> AdmissionJournalMaterializationError {
    AdmissionJournalMaterializationError::Io(error.to_string())
}

fn materialization_serde_error(error: serde_json::Error) -> AdmissionJournalMaterializationError {
    AdmissionJournalMaterializationError::Serialization(error.to_string())
}

fn is_gateway_target_safe(target: &str) -> bool {
    is_portable_artifact_id(target)
}

fn model_lane_provenance_is_complete(lane: &GatewayModelLaneProvenance) -> bool {
    is_portable_artifact_id(&lane.model_family)
        && is_portable_artifact_id(&lane.artifact_id)
        && !lane.runtime.trim().is_empty()
        && lane.runtime.trim() == lane.runtime
        && lane.prompt_template_digest != Hash([0; 32])
        && lane.input_corpus_digest != Hash([0; 32])
        && lane.output_bundle_digest != Hash([0; 32])
}

fn gateway_model_lane_requires_external_bounds(kind: &GatewayModelLaneKind) -> bool {
    matches!(
        kind,
        GatewayModelLaneKind::RentedOpenWeight
            | GatewayModelLaneKind::HostedSmall
            | GatewayModelLaneKind::PremiumEscalation
    )
}

fn gateway_model_lane_registry_contains(
    registry: &GatewayModelLaneRegistry,
    provenance: &GatewayModelLaneProvenance,
) -> bool {
    registry
        .entries
        .iter()
        .any(|entry| &entry.provenance == provenance)
}

fn validate_gateway_baseline_run(
    cases: &[GatewayCorpusCase],
    baseline: &GatewayBaselineRun,
) -> Vec<GatewayBaselineComparisonIssue> {
    let mut issues = Vec::new();
    if !is_portable_artifact_id(&baseline.baseline_id) {
        issues.push(GatewayBaselineComparisonIssue::InvalidBaselineId);
    }
    for required in gateway_baseline_required_nonclaims() {
        if !baseline.nonclaims.contains(&required) {
            issues.push(GatewayBaselineComparisonIssue::MissingRequiredNonclaim(
                required,
            ));
        }
    }

    let case_ids = cases
        .iter()
        .map(|case| case.proposal.id.clone())
        .collect::<BTreeSet<_>>();
    let mut seen_decision_ids = BTreeSet::new();
    for decision in &baseline.decisions {
        if !seen_decision_ids.insert(decision.proposal_id.clone()) {
            issues.push(GatewayBaselineComparisonIssue::DuplicateBaselineDecision(
                decision.proposal_id.clone(),
            ));
        }
        if !case_ids.contains(&decision.proposal_id) {
            issues.push(GatewayBaselineComparisonIssue::UnknownBaselineDecision(
                decision.proposal_id.clone(),
            ));
        }
    }
    for case_id in case_ids {
        if !seen_decision_ids.contains(&case_id) {
            issues.push(GatewayBaselineComparisonIssue::MissingBaselineDecision(
                case_id,
            ));
        }
    }

    issues
}

fn basis_points(numerator: u64, denominator: u64) -> u64 {
    if denominator == 0 {
        0
    } else {
        numerator.saturating_mul(10_000) / denominator
    }
}

fn gateway_cost_route_decision(
    proposal: &GatewayActionProposal,
    router_policy: &GatewayCostRouterPolicy,
    route: GatewayCostRoute,
    reasons: BTreeSet<GatewayCostRouteReason>,
    estimated_cost_units: u64,
) -> GatewayCostRouteDecision {
    GatewayCostRouteDecision {
        action_id: proposal.id.clone(),
        policy_id: router_policy.id.clone(),
        route,
        reasons,
        estimated_cost_units,
        authority_granted: false,
    }
}

fn gateway_threat_labels_need_verifier_mixture(labels: &BTreeSet<GatewayThreatLabel>) -> bool {
    labels
        .iter()
        .any(|label| label != &GatewayThreatLabel::Benign)
}

fn gateway_violation_reason(violation: &GatewayPolicyViolation) -> AdmissionReason {
    reason(match violation {
        GatewayPolicyViolation::InvalidActionId => "gateway_invalid_action_id",
        GatewayPolicyViolation::InvalidTarget => "gateway_invalid_target",
        GatewayPolicyViolation::UnsupportedActionKind => "gateway_unsupported_action_kind",
        GatewayPolicyViolation::UnauthorizedTarget => "gateway_unauthorized_target",
        GatewayPolicyViolation::AmountLimitExceeded => "gateway_amount_limit_exceeded",
        GatewayPolicyViolation::MissingModelLaneProvenance => {
            "gateway_missing_model_lane_provenance"
        }
        GatewayPolicyViolation::ModelLaneNotNonSecret => "gateway_model_lane_not_non_secret",
        GatewayPolicyViolation::DirectAuthorityRequested => "gateway_direct_authority_requested",
        GatewayPolicyViolation::SignerOrToolRequestedBeforeAdmission => {
            "gateway_signer_or_tool_requested_before_admission"
        }
    })
}

fn reason(value: &str) -> AdmissionReason {
    AdmissionReason(value.to_owned())
}

fn hash_tagged<T: Serialize>(tag: &str, value: &T) -> Hash {
    let bytes = serde_json::to_vec(&(tag, value))
        .expect("agent admission values must serialize for deterministic hashing");
    let digest = Sha256::digest(bytes);
    let mut out = [0; 32];
    out.copy_from_slice(&digest);
    Hash(out)
}

#[cfg(test)]
mod tests {
    use super::*;
    use hsai_agent_case::{ActionId, MemoryRoot, ModelId, OracleContract, Verdict};
    use hsai_claim_envelope::{LaneId, Maturity, Predicate, PropertyKind, TimeWindow};
    use std::time::{SystemTime, UNIX_EPOCH};

    fn subject(id: &str) -> SubjectId {
        SubjectId(id.to_owned())
    }

    fn nonclaim(value: &str) -> NonClaimLabel {
        NonClaimLabel(value.to_owned())
    }

    fn artifact(id: &str, byte: u8) -> ArtifactDigest {
        ArtifactDigest {
            id: id.to_owned(),
            sha256: Hash([byte; 32]),
        }
    }

    fn predicate(subject_id: &str, property: PropertyKind) -> Predicate {
        Predicate {
            subject: subject(subject_id),
            property,
        }
    }

    fn case() -> AgentCase {
        AgentCase {
            action: ActionId("action-1".to_owned()),
            subject: subject("agent-a"),
            claimed_model: ModelId("model-a".to_owned()),
            memory_root: MemoryRoot([7; 32]),
            observed_at: 10,
            oracle: OracleContract {
                expected: Verdict::Accept,
                target_guarantees: BTreeSet::from([predicate(
                    "agent-a",
                    PropertyKind::PolicyCompliance,
                )]),
                excluded: BTreeSet::from([predicate(
                    "action-1",
                    PropertyKind::SemanticCorrectness,
                )]),
            },
        }
    }

    fn envelope() -> ClaimEnvelope {
        ClaimEnvelope::new(
            BTreeSet::from([predicate("agent-a", PropertyKind::PolicyCompliance)]),
            BTreeSet::new(),
            BTreeSet::from([predicate("action-1", PropertyKind::SemanticCorrectness)]),
            Maturity::Local,
            BTreeSet::new(),
            TimeWindow {
                start: 10,
                end: 100,
            },
            LaneId::Named("local-policy".to_owned()),
        )
    }

    fn policy() -> AgentAdmissionPolicy {
        AgentAdmissionPolicy::local_default(BTreeSet::from([
            nonclaim("not semantic correctness"),
            nonclaim("not accepted evidence"),
        ]))
    }

    fn accepted_candidate() -> AgentAdmissionCandidate {
        AgentAdmissionCandidate::from_envelope(
            "candidate-1",
            subject("agent-a"),
            envelope(),
            BTreeSet::from([artifact("case", 1), artifact("envelope", 2)]),
            BTreeSet::from([
                nonclaim("not semantic correctness"),
                nonclaim("not accepted evidence"),
            ]),
        )
    }

    fn gateway_model_lane() -> GatewayModelLaneProvenance {
        GatewayModelLaneProvenance {
            lane_kind: GatewayModelLaneKind::LocalOpenWeight,
            model_family: "qwen-small".to_owned(),
            artifact_id: "qwen-small-q4".to_owned(),
            runtime: "llama-server-local".to_owned(),
            prompt_template_digest: Hash([21; 32]),
            input_corpus_digest: Hash([22; 32]),
            output_bundle_digest: Hash([23; 32]),
            non_secret: true,
        }
    }

    fn gateway_model_lane_registry_entry(
        lane_id: &str,
        provenance: GatewayModelLaneProvenance,
    ) -> GatewayModelLaneRegistryEntry {
        GatewayModelLaneRegistryEntry {
            lane_id: lane_id.to_owned(),
            expected_output_bundle_digest: provenance.output_bundle_digest,
            provenance,
            max_cases_per_run: Some(16),
            max_cost_units_per_case: Some(2),
        }
    }

    fn gateway_model_lane_registry() -> GatewayModelLaneRegistry {
        GatewayModelLaneRegistry {
            schema_version: "hsai-gateway-model-lane-registry-v1".to_owned(),
            entries: vec![gateway_model_lane_registry_entry(
                "local-qwen",
                gateway_model_lane(),
            )],
        }
    }

    fn gateway_policy() -> GatewayActionPolicy {
        gateway_local_default_policy(
            "gateway-local-policy-v1",
            BTreeSet::from([
                GatewayActionKind::Payment,
                GatewayActionKind::ToolCall,
                GatewayActionKind::ComputeRental,
            ]),
            BTreeSet::from(["treasury-safe".to_owned(), "mcp-safe-tool".to_owned()]),
            100,
        )
    }

    fn gateway_cost_policy() -> GatewayCostRouterPolicy {
        gateway_cost_router_default_policy("gateway-cost-router-v1")
    }

    fn gateway_proposal(id: &str) -> GatewayActionProposal {
        GatewayActionProposal {
            id: GatewayActionId(id.to_owned()),
            subject: subject("agent-a"),
            action_kind: GatewayActionKind::Payment,
            target: "treasury-safe".to_owned(),
            value_units: 50,
            source_artifact_digests: BTreeSet::from([artifact("gateway-action", 20)]),
            nonclaims: gateway_required_nonclaims(),
            model_lane: gateway_model_lane(),
            threat_labels: BTreeSet::from([GatewayThreatLabel::Benign]),
            direct_authority_requested: false,
            signer_or_tool_requested_before_admission: false,
        }
    }

    fn gateway_adversarial_case(id: &str, threat_label: GatewayThreatLabel) -> GatewayCorpusCase {
        let mut proposal = gateway_proposal(id);
        proposal.threat_labels = BTreeSet::from([threat_label.clone()]);
        match threat_label {
            GatewayThreatLabel::Benign => GatewayCorpusCase {
                proposal,
                expected_verdict: AdmissionVerdict::Accepted,
            },
            GatewayThreatLabel::WrongCounterparty => {
                proposal.target = "wrong-counterparty".to_owned();
                GatewayCorpusCase {
                    proposal,
                    expected_verdict: AdmissionVerdict::Rejected,
                }
            }
            GatewayThreatLabel::AmountLimitBypass => {
                proposal.value_units = 500;
                GatewayCorpusCase {
                    proposal,
                    expected_verdict: AdmissionVerdict::Rejected,
                }
            }
            GatewayThreatLabel::DirectAuthorityRequest => {
                proposal.direct_authority_requested = true;
                GatewayCorpusCase {
                    proposal,
                    expected_verdict: AdmissionVerdict::Rejected,
                }
            }
            GatewayThreatLabel::SignerBeforeAdmission => {
                proposal.signer_or_tool_requested_before_admission = true;
                GatewayCorpusCase {
                    proposal,
                    expected_verdict: AdmissionVerdict::Rejected,
                }
            }
            _ => {
                proposal.direct_authority_requested = true;
                GatewayCorpusCase {
                    proposal,
                    expected_verdict: AdmissionVerdict::Rejected,
                }
            }
        }
    }

    fn gateway_full_adversarial_corpus() -> GatewayAdversarialCorpus {
        let mut cases = vec![gateway_adversarial_case(
            "gateway-corpus-benign",
            GatewayThreatLabel::Benign,
        )];
        for (index, label) in gateway_required_adversarial_threat_labels()
            .into_iter()
            .enumerate()
        {
            cases.push(gateway_adversarial_case(
                &format!("gateway-corpus-threat-{index}"),
                label,
            ));
        }
        GatewayAdversarialCorpus {
            schema_version: "hsai-gateway-adversarial-corpus-v1".to_owned(),
            corpus_id: "gateway-local-adversarial-corpus-v1".to_owned(),
            cases,
            required_threat_labels: gateway_required_adversarial_threat_labels(),
        }
    }

    fn gateway_baseline_run(
        baseline_id: &str,
        cases: &[GatewayCorpusCase],
        verdict: AdmissionVerdict,
    ) -> GatewayBaselineRun {
        GatewayBaselineRun {
            baseline_id: baseline_id.to_owned(),
            baseline_kind: GatewayBaselineKind::NoApprovalGateway,
            decisions: cases
                .iter()
                .map(|case| GatewayBaselineDecision {
                    proposal_id: case.proposal.id.clone(),
                    verdict: verdict.clone(),
                })
                .collect(),
            nonclaims: gateway_baseline_required_nonclaims(),
        }
    }

    fn materialization_request(
        bundle_id: &str,
        output_root: &Path,
    ) -> AdmissionJournalMaterializationRequest {
        AdmissionJournalMaterializationRequest {
            bundle_id: bundle_id.to_owned(),
            created_at_unix: 1_800_000_000,
            admission_policy_id: policy().id,
            journal_tip_digest_before: None,
            nonclaims: admission_journal_required_nonclaims(),
            overwrite: false,
            protected_roots: vec![output_root
                .parent()
                .expect("temp output root has a parent")
                .join("protected-repo")],
        }
    }

    fn gateway_report_request(
        bundle_id: &str,
        output_root: &Path,
    ) -> GatewayReportMaterializationRequest {
        GatewayReportMaterializationRequest {
            bundle_id: bundle_id.to_owned(),
            created_at_unix: 1_800_000_001,
            overwrite: false,
            protected_roots: vec![output_root
                .parent()
                .expect("temp output root has a parent")
                .join("protected-repo")],
        }
    }

    fn temp_output_root(name: &str) -> PathBuf {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("system clock is usable")
            .as_nanos();
        std::env::temp_dir().join(format!("hsai-agent-admission-{name}-{nonce}"))
    }

    fn rewrite_bundle_file(output_root: &Path, logical_path: &str, bytes: &[u8]) {
        let path = output_root.join(logical_path);
        fs::write(&path, bytes).expect("tampered declared file writes");
        fs::write(
            sidecar_path(&path),
            hash_hex(hash_bytes(bytes)).into_bytes(),
        )
        .expect("tampered sidecar writes");
    }

    fn rewrite_gateway_file_and_manifest_digest(
        output_root: &Path,
        logical_path: &str,
        bytes: &[u8],
    ) {
        rewrite_bundle_file(output_root, logical_path, bytes);
        let manifest_path = output_root.join("gateway-report/manifest.json");
        let mut manifest: GatewayReportOutputManifest =
            serde_json::from_slice(&fs::read(&manifest_path).expect("gateway manifest reads"))
                .expect("gateway manifest parses");
        manifest
            .declared_file_digests
            .insert(logical_path.to_owned(), hash_bytes(bytes));
        rewrite_bundle_file(
            output_root,
            "gateway-report/manifest.json",
            &serde_json::to_vec_pretty(&manifest).expect("gateway manifest serializes"),
        );
    }

    fn rewrite_content_and_manifest_digest(output_root: &Path, logical_path: &str, bytes: &[u8]) {
        rewrite_bundle_file(output_root, logical_path, bytes);
        let manifest_path = output_root.join("admission-journal/manifest.json");
        let mut manifest: AdmissionJournalBundleManifest =
            serde_json::from_slice(&fs::read(&manifest_path).expect("manifest reads for mutation"))
                .expect("manifest parses for mutation");
        manifest
            .declared_file_digests
            .insert(logical_path.to_owned(), hash_bytes(bytes));
        let manifest_bytes =
            serde_json::to_vec_pretty(&manifest).expect("mutated manifest serializes");
        rewrite_bundle_file(
            output_root,
            "admission-journal/manifest.json",
            &manifest_bytes,
        );
    }

    fn materialized_test_bundle(name: &str) -> (PathBuf, AgentAdmissionJournal) {
        let output_root = temp_output_root(name);
        let journal = two_entry_journal();
        materialize_admission_journal_bundle(
            &output_root,
            &journal,
            &materialization_request(name, &output_root),
        )
        .expect("test bundle materializes");
        (output_root, journal)
    }

    fn assert_malformed_declared_json(logical_path: &str) {
        let name = logical_path
            .rsplit('/')
            .next()
            .expect("logical path has a filename")
            .replace('.', "-");
        let (output_root, _) = materialized_test_bundle(&format!("malformed-{name}"));
        if logical_path == "admission-journal/manifest.json" {
            rewrite_bundle_file(&output_root, logical_path, b"{");
        } else {
            rewrite_content_and_manifest_digest(&output_root, logical_path, b"{");
        }
        assert_eq!(
            read_admission_journal_bundle(&output_root),
            Err(AdmissionJournalMaterializationError::MalformedDeclaredFile(
                logical_path.to_owned()
            ))
        );
        fs::remove_dir_all(&output_root).expect("malformed bundle cleanup succeeds");
    }

    fn two_entry_journal() -> AgentAdmissionJournal {
        let accepted = accepted_candidate();
        let rejected = {
            let mut candidate = AgentAdmissionCandidate::from_case(
                "candidate-rejected-materialized",
                case(),
                BTreeSet::from([artifact("case-rejected", 11)]),
                BTreeSet::from([
                    nonclaim("not semantic correctness"),
                    nonclaim("not accepted evidence"),
                ]),
            );
            candidate.provider_direct_authority_requested = true;
            candidate
        };

        let admission_policy = policy();
        let mut journal = AgentAdmissionJournal::default();
        journal
            .append_decision(
                &accepted,
                &admission_policy,
                evaluate_admission(&accepted, &admission_policy),
            )
            .expect("accepted decision appends");
        journal
            .append_decision(
                &rejected,
                &admission_policy,
                evaluate_admission(&rejected, &admission_policy),
            )
            .expect("rejected decision appends");
        journal
    }

    fn pcsm_verifier(name: &str) -> PcsmVerifierStatus {
        PcsmVerifierStatus {
            name: name.to_owned(),
            outcome: PcsmVerifierOutcome::Pass,
        }
    }

    fn valid_pcsm_intake() -> PcsmBoundedProofHandoffIntake {
        PcsmBoundedProofHandoffIntake {
            source_repo_remote: "https://github.com/example/recoverable-ghost-states.git"
                .to_owned(),
            source_repo_branch: "main".to_owned(),
            source_repo_commit: "0123456789abcdef0123456789abcdef01234567".to_owned(),
            source_repo_status: PcsmSourceRepoStatus::Clean,
            source_handoff_path: "docs/pcsm-cl12-bounded-proof-handoff.md".to_owned(),
            source_handoff_sha256: Hash([9; 32]),
            source_handoff_schema: "pcsm-cl12-bounded-proof-handoff-v1".to_owned(),
            source_handoff_state_slice: "pcsm-cl12-bounded-proof-package".to_owned(),
            bounded_breakthrough_evidence_admitted: true,
            threshold_admitted: false,
            replication_admission_status: "blocked_preflight_only".to_owned(),
            blocked_item: "live_external_runtime_replication".to_owned(),
            pcsm_inputs: 5,
            pcsm_accepted: 4,
            pcsm_rejected: 1,
            pcsm_journal_entries: 5,
            provider_direct_authority: false,
            production_authority: false,
            raw_provider_payloads_committed: false,
            local_mlx_surrogate_runtime: true,
            native_pcsm_governed_state: true,
            pcsm_journaled: true,
            verifier_statuses: BTreeSet::from([
                pcsm_verifier("verify_cl12_local_mlx_pcsm_surrogate"),
                pcsm_verifier("verify_cl12_external_benchmark_replication"),
                pcsm_verifier("verify_breakthrough_threshold_audit"),
                pcsm_verifier("verify_native_pcsm"),
                pcsm_verifier("source_lint_gate"),
            ]),
            source_artifact_digests: BTreeSet::from([
                artifact("source-handoff", 9),
                artifact("pcsm-journal", 10),
            ]),
            nonclaims: pcsm_bounded_proof_required_nonclaims(),
            accepted_ledger_mutation_requested: false,
            official_submission_requested: false,
            external_replay_requested: false,
            score_axis_population_requested: false,
            level2_evidence_requested: false,
        }
    }

    fn gateway_attestation_pubkey_hex() -> String {
        "a1".repeat(91)
    }

    fn gateway_attestation_binding() -> GatewayAttestationChallengeBinding {
        build_gateway_attestation_challenge_binding(
            &gateway_proposal("gateway-attestation-action"),
            AdmissionPolicyId("gateway-attestation-policy-v1".to_owned()),
            "anchor-gateway-runtime-1",
            gateway_attestation_pubkey_hex(),
            42,
            100,
            200,
        )
        .expect("gateway attestation binding should build")
    }

    fn gateway_operator_bridge_request(
        bundle_id: &str,
        output_root: &Path,
    ) -> GatewayOperatorBridgeMaterializationRequest {
        GatewayOperatorBridgeMaterializationRequest {
            bundle_id: bundle_id.to_owned(),
            created_at_unix: 1_800_000_250,
            overwrite: false,
            protected_roots: vec![output_root
                .parent()
                .expect("temp output root has a parent")
                .join("protected-repo")],
        }
    }

    fn gateway_operator_reference() -> GatewayOperatorArtifactReference {
        GatewayOperatorArtifactReference {
            reference_id: "phase-250-operator-live-reference".to_owned(),
            provider: "phala-dstack".to_owned(),
            artifact_kind: "operator-live".to_owned(),
            operator_run_id: "phase-250-repo-external-run".to_owned(),
            artifact_digest: ArtifactDigest {
                id: "repo-external-operator-live-bundle".to_owned(),
                sha256: Hash([88; 32]),
            },
            repo_external: true,
            claim_boundary: "operator-live artifact reference only; not accepted evidence"
                .to_owned(),
            nonclaims: gateway_operator_bridge_required_nonclaims(),
        }
    }

    fn gateway_report_manifest_for_bridge(
        proposal: GatewayActionProposal,
        output_root: &Path,
    ) -> GatewayReportOutputManifest {
        let policy = gateway_policy();
        let report = evaluate_gateway_corpus(
            &[GatewayCorpusCase {
                proposal,
                expected_verdict: AdmissionVerdict::Accepted,
            }],
            &policy,
        )
        .expect("gateway report evaluates");
        materialize_gateway_report_bundle(
            output_root,
            &report,
            &policy,
            &gateway_report_request("gateway-report-for-bridge", output_root),
        )
        .expect("gateway report materializes")
    }

    fn gateway_operator_bridge_bundle(
        proposal: &GatewayActionProposal,
        report_manifest: &GatewayReportOutputManifest,
        output_root: &Path,
    ) -> GatewayOperatorBridgeBundle {
        let request = gateway_operator_bridge_request("gateway-operator-bridge", output_root);
        let binding = build_gateway_attestation_challenge_binding(
            proposal,
            AdmissionPolicyId("gateway-attestation-policy-v1".to_owned()),
            "anchor-gateway-runtime-1",
            gateway_attestation_pubkey_hex(),
            42,
            100,
            200,
        )
        .expect("binding builds");
        build_gateway_operator_bridge_bundle(
            report_manifest,
            binding,
            gateway_operator_reference(),
            &request,
        )
        .expect("bridge bundle builds")
    }

    fn gateway_operator_bridge_promotion_preflight_request(
        proposal: &GatewayActionProposal,
        report_manifest: &GatewayReportOutputManifest,
        output_root: &Path,
    ) -> GatewayOperatorBridgePromotionPreflightRequest {
        let bundle = gateway_operator_bridge_bundle(proposal, report_manifest, output_root);
        let request = gateway_operator_bridge_request("gateway-operator-bridge", output_root);
        let manifest = materialize_gateway_operator_bridge_bundle(output_root, &bundle, &request)
            .expect("bridge bundle materializes for preflight");
        GatewayOperatorBridgePromotionPreflightRequest {
            schema_version: gateway_operator_bridge_promotion_preflight_request_schema_version()
                .to_owned(),
            preflight_id: "gateway-operator-bridge-promotion-preflight".to_owned(),
            reviewer_id: "local-reviewer".to_owned(),
            review_decision: GatewayOperatorBridgePromotionReviewDecision::ApprovedMetadataOnly,
            bridge_bundle: bundle,
            bridge_manifest: manifest,
            requested_claim_boundary: gateway_operator_bridge_promotion_preflight_claim_boundary(),
            retains_raw_provider_artifacts: false,
            retains_credentials_or_secrets: false,
            accepted_evidence_mutation_requested: false,
            level2_evidence_requested: false,
            score_axis_population_requested: false,
            production_readiness_claimed: false,
            semantic_correctness_claimed: false,
            live_provider_evidence_claimed: false,
            claim_text: Vec::new(),
            nonclaims: gateway_operator_bridge_promotion_preflight_required_nonclaims(),
        }
    }

    fn gateway_operator_bridge_acceptance_preview_request(
        proposal: &GatewayActionProposal,
        report_manifest: &GatewayReportOutputManifest,
        output_root: &Path,
    ) -> GatewayOperatorBridgeAcceptancePreviewRequest {
        let preflight_request = gateway_operator_bridge_promotion_preflight_request(
            proposal,
            report_manifest,
            output_root,
        );
        let preflight_report =
            build_gateway_operator_bridge_promotion_preflight_report(&preflight_request);
        GatewayOperatorBridgeAcceptancePreviewRequest {
            schema_version: gateway_operator_bridge_acceptance_preview_request_schema_version()
                .to_owned(),
            preview_id: "gateway-operator-bridge-acceptance-preview".to_owned(),
            reviewer_id: "local-reviewer".to_owned(),
            decision: GatewayOperatorBridgeAcceptancePreviewDecision::ApproveCandidateOnly,
            expected_preflight_report_digest: preflight_report.digest(),
            source_preflight_report: preflight_report,
            requested_claim_boundary: gateway_operator_bridge_acceptance_preview_claim_boundary(),
            candidate_only: true,
            accepted_evidence_mutation_requested: false,
            level2_evidence_requested: false,
            score_axis_population_requested: false,
            production_readiness_claimed: false,
            semantic_correctness_claimed: false,
            live_provider_evidence_claimed: false,
            raw_provider_artifact_retention_requested: false,
            credential_retention_requested: false,
            authority_grant_requested: false,
            claim_text: Vec::new(),
            nonclaims: gateway_operator_bridge_acceptance_preview_required_nonclaims(),
        }
    }

    #[test]
    fn accepted_candidate_exports_envelope_and_appends_journal_entry() {
        let candidate = accepted_candidate();
        let admission_policy = policy();
        let decision = evaluate_admission(&candidate, &admission_policy);

        assert_eq!(decision.verdict, AdmissionVerdict::Accepted);
        assert!(decision.reasons.is_empty());
        assert_eq!(
            accepted_claim_envelope(&candidate, &admission_policy, &decision),
            candidate.proposed_envelope.as_ref()
        );

        let mut journal = AgentAdmissionJournal::default();
        let entry = journal
            .append_decision(&candidate, &admission_policy, decision)
            .expect("accepted decision should append");

        assert_eq!(entry.sequence_number, 0);
        assert_eq!(entry.previous_entry_digest, None);
        assert_eq!(
            entry.source_artifact_digests,
            candidate.source_artifact_digests
        );
        assert!(journal.validate().is_empty());
    }

    #[test]
    fn gateway_attestation_binding_uses_proposal_digest_as_case_hash() {
        let proposal = gateway_proposal("gateway-attestation-action");
        let binding = build_gateway_attestation_challenge_binding(
            &proposal,
            AdmissionPolicyId("gateway-attestation-policy-v1".to_owned()),
            "anchor-gateway-runtime-1",
            gateway_attestation_pubkey_hex(),
            42,
            100,
            200,
        )
        .expect("gateway attestation binding should build");

        let pubkey = decode_lower_hex("agent_pubkey_spki_hex", &gateway_attestation_pubkey_hex())
            .expect("test pubkey hex decodes");
        let expected = bytes_hex(&report_data_binding(
            &pubkey,
            42,
            proposal.digest().0.as_slice(),
        ));

        assert_eq!(
            binding.schema_version,
            GATEWAY_ATTESTATION_BINDING_SCHEMA_VERSION
        );
        assert_eq!(binding.gateway_case_hash_hex, hash_hex(proposal.digest()));
        assert_eq!(binding.expected_report_data_hex, expected);
        assert_eq!(
            validate_gateway_attestation_challenge_binding(
                &proposal,
                &AdmissionPolicyId("gateway-attestation-policy-v1".to_owned()),
                &binding,
                150,
            ),
            Vec::new()
        );
        assert!(!binding.challenge_id.is_empty());
        assert!(!binding.authority_granted);
    }

    #[test]
    fn gateway_attestation_binding_is_deterministic_and_nonce_sensitive() {
        let proposal = gateway_proposal("gateway-attestation-action");
        let first = build_gateway_attestation_challenge_binding(
            &proposal,
            AdmissionPolicyId("gateway-attestation-policy-v1".to_owned()),
            "anchor-gateway-runtime-1",
            gateway_attestation_pubkey_hex(),
            42,
            100,
            200,
        )
        .expect("first binding builds");
        let second = build_gateway_attestation_challenge_binding(
            &proposal,
            AdmissionPolicyId("gateway-attestation-policy-v1".to_owned()),
            "anchor-gateway-runtime-1",
            gateway_attestation_pubkey_hex(),
            42,
            100,
            200,
        )
        .expect("second binding builds");
        let changed_nonce = build_gateway_attestation_challenge_binding(
            &proposal,
            AdmissionPolicyId("gateway-attestation-policy-v1".to_owned()),
            "anchor-gateway-runtime-1",
            gateway_attestation_pubkey_hex(),
            43,
            100,
            200,
        )
        .expect("changed nonce binding builds");

        assert_eq!(first, second);
        assert_ne!(
            first.expected_report_data_hex,
            changed_nonce.expected_report_data_hex
        );
        assert_ne!(first.challenge_id, changed_nonce.challenge_id);
    }

    #[test]
    fn gateway_attestation_binding_rejects_gateway_case_tamper() {
        let original = gateway_proposal("gateway-attestation-action");
        let mut tampered = original.clone();
        tampered.target = "wrong-counterparty".to_owned();
        let binding = build_gateway_attestation_challenge_binding(
            &original,
            AdmissionPolicyId("gateway-attestation-policy-v1".to_owned()),
            "anchor-gateway-runtime-1",
            gateway_attestation_pubkey_hex(),
            42,
            100,
            200,
        )
        .expect("binding builds");

        let errors = validate_gateway_attestation_challenge_binding(
            &tampered,
            &AdmissionPolicyId("gateway-attestation-policy-v1".to_owned()),
            &binding,
            150,
        );

        assert!(errors.iter().any(|error| matches!(
            error,
            GatewayAttestationBindingError::GatewayCaseHashMismatch { .. }
        )));
        assert!(errors.iter().any(|error| matches!(
            error,
            GatewayAttestationBindingError::ReportDataMismatch { .. }
        )));
    }

    #[test]
    fn gateway_attestation_binding_rejects_expiry_and_challenge_id_tamper() {
        let proposal = gateway_proposal("gateway-attestation-action");
        let mut binding = gateway_attestation_binding();
        binding.challenge_id.replace_range(0..2, "ff");

        let errors = validate_gateway_attestation_challenge_binding(
            &proposal,
            &AdmissionPolicyId("gateway-attestation-policy-v1".to_owned()),
            &binding,
            201,
        );

        assert!(errors.iter().any(|error| matches!(
            error,
            GatewayAttestationBindingError::ExpiredChallenge { .. }
        )));
        assert!(errors.iter().any(|error| matches!(
            error,
            GatewayAttestationBindingError::ChallengeIdMismatch { .. }
        )));
    }

    #[test]
    fn gateway_attestation_binding_rejects_authority_and_missing_nonclaim() {
        let proposal = gateway_proposal("gateway-attestation-action");
        let mut binding = gateway_attestation_binding();
        binding.authority_granted = true;
        binding
            .nonclaims
            .remove(&NonClaimLabel("not proof".to_owned()));

        let errors = validate_gateway_attestation_challenge_binding(
            &proposal,
            &AdmissionPolicyId("gateway-attestation-policy-v1".to_owned()),
            &binding,
            150,
        );

        assert!(errors
            .iter()
            .any(|error| error == &GatewayAttestationBindingError::AuthorityGranted));
        assert!(errors.iter().any(|error| {
            error
                == &GatewayAttestationBindingError::MissingRequiredNonclaim("not proof".to_owned())
        }));
        assert!(errors.iter().any(|error| matches!(
            error,
            GatewayAttestationBindingError::ChallengeIdMismatch { .. }
        )));
    }

    #[test]
    fn gateway_operator_bridge_bundle_materializes_declared_files_and_readback() {
        let proposal = gateway_proposal("gateway-bridge-action");
        let report_root = temp_output_root("gateway-bridge-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-bundle");
        let bundle = gateway_operator_bridge_bundle(&proposal, &report_manifest, &output_root);
        let request = gateway_operator_bridge_request("gateway-operator-bridge", &output_root);

        let manifest = materialize_gateway_operator_bridge_bundle(&output_root, &bundle, &request)
            .expect("bridge bundle materializes");

        assert_eq!(manifest.bundle_id, "gateway-operator-bridge");
        assert_eq!(
            manifest.declared_files,
            gateway_operator_bridge_declared_files()
        );
        assert_eq!(
            manifest.gateway_report_digest,
            report_manifest.artifact_manifest.report_digest
        );
        assert_eq!(
            manifest.attestation_binding_digest,
            bundle.attestation_binding.digest()
        );
        assert_eq!(
            manifest.operator_artifact_reference_digest,
            bundle.operator_artifact_reference.digest()
        );
        assert!(!manifest.authority_granted);
        assert!(!manifest.accepted_evidence_mutation);
        assert_eq!(
            read_gateway_operator_bridge_bundle(&output_root).expect("readback validates"),
            manifest
        );
        let _ = fs::remove_dir_all(report_root);
        let _ = fs::remove_dir_all(output_root);
    }

    #[test]
    fn gateway_operator_bridge_bundle_rejects_raw_operator_artifacts() {
        let proposal = gateway_proposal("gateway-bridge-action");
        let report_root = temp_output_root("gateway-bridge-raw-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-raw");
        let bundle = gateway_operator_bridge_bundle(&proposal, &report_manifest, &output_root);
        let request = gateway_operator_bridge_request("gateway-operator-bridge", &output_root);
        materialize_gateway_operator_bridge_bundle(&output_root, &bundle, &request)
            .expect("bridge bundle materializes");
        fs::write(output_root.join("gateway-bridge/raw-response.json"), b"{}")
            .expect("raw extra writes");

        assert_eq!(
            read_gateway_operator_bridge_bundle(&output_root),
            Err(GatewayOperatorBridgeMaterializationError::UndeclaredFile(
                "gateway-bridge/raw-response.json".to_owned()
            ))
        );
        let _ = fs::remove_dir_all(report_root);
        let _ = fs::remove_dir_all(output_root);
    }

    #[test]
    fn gateway_operator_bridge_bundle_rejects_accepted_evidence_escalation() {
        let proposal = gateway_proposal("gateway-bridge-action");
        let report_root = temp_output_root("gateway-bridge-escalation-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-escalation");
        let mut bundle = gateway_operator_bridge_bundle(&proposal, &report_manifest, &output_root);
        bundle.accepted_evidence_mutation = true;
        let request = gateway_operator_bridge_request("gateway-operator-bridge", &output_root);

        assert!(matches!(
            materialize_gateway_operator_bridge_bundle(&output_root, &bundle, &request),
            Err(GatewayOperatorBridgeMaterializationError::InvalidBundle(issues))
                if issues.contains(&GatewayOperatorBridgeIssue::AcceptedEvidenceMutationRequested)
        ));
        let _ = fs::remove_dir_all(report_root);
    }

    #[test]
    fn gateway_operator_bridge_readback_rejects_binding_drift() {
        let proposal = gateway_proposal("gateway-bridge-action");
        let report_root = temp_output_root("gateway-bridge-drift-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-drift");
        let bundle = gateway_operator_bridge_bundle(&proposal, &report_manifest, &output_root);
        let request = gateway_operator_bridge_request("gateway-operator-bridge", &output_root);
        materialize_gateway_operator_bridge_bundle(&output_root, &bundle, &request)
            .expect("bridge bundle materializes");
        let mut tampered = bundle.attestation_binding.clone();
        tampered.nonce += 1;
        rewrite_bundle_file(
            &output_root,
            "gateway-bridge/attestation-binding.json",
            &serde_json::to_vec_pretty(&tampered).expect("tampered binding serializes"),
        );

        assert_eq!(
            read_gateway_operator_bridge_bundle(&output_root),
            Err(GatewayOperatorBridgeMaterializationError::ManifestSemanticMismatch)
        );
        let _ = fs::remove_dir_all(report_root);
        let _ = fs::remove_dir_all(output_root);
    }

    #[test]
    fn gateway_operator_bridge_promotion_preflight_accepts_local_metadata_only() {
        let proposal = gateway_proposal("gateway-bridge-preflight-action");
        let report_root = temp_output_root("gateway-bridge-preflight-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-preflight");
        let request = gateway_operator_bridge_promotion_preflight_request(
            &proposal,
            &report_manifest,
            &output_root,
        );

        let report = build_gateway_operator_bridge_promotion_preflight_report(&request);

        assert!(report.validation.valid);
        assert_eq!(report.preflight_id, request.preflight_id);
        assert_eq!(report.bridge_bundle_digest, request.bridge_bundle.digest());
        assert_eq!(
            report.bridge_manifest_digest,
            request.bridge_manifest.digest()
        );
        assert_eq!(
            report.operator_artifact_reference_digest,
            request.bridge_bundle.operator_artifact_reference.digest()
        );
        assert!(!report.mutates_accepted_evidence_ledger);
        assert!(!report.creates_level2_evidence);
        assert!(!report.populates_score_axes);
        assert!(!report.grants_authority);
        assert!(!report.retains_raw_provider_artifacts);
        assert!(!report.retains_credentials_or_secrets);
        assert_eq!(
            report.nonclaims,
            gateway_operator_bridge_promotion_preflight_required_nonclaims()
        );
        assert_ne!(report.digest(), Hash([0; 32]));
        let _ = fs::remove_dir_all(report_root);
        let _ = fs::remove_dir_all(output_root);
    }

    #[test]
    fn gateway_operator_bridge_promotion_preflight_rejects_escalation_flags() {
        let proposal = gateway_proposal("gateway-bridge-preflight-escalation-action");
        let report_root = temp_output_root("gateway-bridge-preflight-escalation-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-preflight-escalation");
        let mut request = gateway_operator_bridge_promotion_preflight_request(
            &proposal,
            &report_manifest,
            &output_root,
        );
        request.retains_raw_provider_artifacts = true;
        request.retains_credentials_or_secrets = true;
        request.accepted_evidence_mutation_requested = true;
        request.level2_evidence_requested = true;
        request.score_axis_population_requested = true;

        let validation = validate_gateway_operator_bridge_promotion_preflight_request(&request);

        assert!(!validation.valid);
        assert!(validation
            .issues
            .contains(&GatewayOperatorBridgePromotionPreflightIssue::RawProviderArtifactRetained));
        assert!(validation
            .issues
            .contains(&GatewayOperatorBridgePromotionPreflightIssue::CredentialsOrSecretsRetained));
        assert!(validation.issues.contains(
            &GatewayOperatorBridgePromotionPreflightIssue::AcceptedEvidenceMutationRequested
        ));
        assert!(validation
            .issues
            .contains(&GatewayOperatorBridgePromotionPreflightIssue::Level2EvidenceRequested));
        assert!(validation
            .issues
            .contains(&GatewayOperatorBridgePromotionPreflightIssue::ScoreAxisPopulationRequested));
        let _ = fs::remove_dir_all(report_root);
        let _ = fs::remove_dir_all(output_root);
    }

    #[test]
    fn gateway_operator_bridge_promotion_preflight_rejects_manifest_drift() {
        let proposal = gateway_proposal("gateway-bridge-preflight-drift-action");
        let report_root = temp_output_root("gateway-bridge-preflight-drift-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-preflight-drift");
        let mut request = gateway_operator_bridge_promotion_preflight_request(
            &proposal,
            &report_manifest,
            &output_root,
        );
        request.bridge_manifest.operator_artifact_reference_digest = Hash([9; 32]);

        let validation = validate_gateway_operator_bridge_promotion_preflight_request(&request);

        assert_eq!(
            validation.issues,
            vec![GatewayOperatorBridgePromotionPreflightIssue::BridgeManifestMismatch]
        );
        let _ = fs::remove_dir_all(report_root);
        let _ = fs::remove_dir_all(output_root);
    }

    #[test]
    fn gateway_operator_bridge_promotion_preflight_rejects_breakthrough_claim_text() {
        let proposal = gateway_proposal("gateway-bridge-preflight-claim-action");
        let report_root = temp_output_root("gateway-bridge-preflight-claim-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-preflight-claim");
        let mut request = gateway_operator_bridge_promotion_preflight_request(
            &proposal,
            &report_manifest,
            &output_root,
        );
        request.claim_text = vec!["This is a SOTA breakthrough bridge.".to_owned()];

        let validation = validate_gateway_operator_bridge_promotion_preflight_request(&request);

        assert!(!validation.valid);
        assert!(validation.issues.contains(
            &GatewayOperatorBridgePromotionPreflightIssue::ForbiddenClaimText("sota".to_owned())
        ));
        assert!(validation.issues.contains(
            &GatewayOperatorBridgePromotionPreflightIssue::ForbiddenClaimText(
                "breakthrough".to_owned()
            )
        ));
        let _ = fs::remove_dir_all(report_root);
        let _ = fs::remove_dir_all(output_root);
    }

    #[test]
    fn gateway_operator_bridge_acceptance_preview_accepts_candidate_only_metadata() {
        let proposal = gateway_proposal("gateway-bridge-acceptance-preview-action");
        let report_root = temp_output_root("gateway-bridge-acceptance-preview-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-acceptance-preview");
        let request = gateway_operator_bridge_acceptance_preview_request(
            &proposal,
            &report_manifest,
            &output_root,
        );

        let report = build_gateway_operator_bridge_acceptance_preview_report(&request);

        assert!(report.validation.valid);
        assert_eq!(report.preview_id, request.preview_id);
        assert_eq!(
            report.source_preflight_report_digest,
            request.source_preflight_report.digest()
        );
        assert_eq!(
            report.bridge_bundle_digest,
            request.source_preflight_report.bridge_bundle_digest
        );
        assert!(report.candidate_only);
        assert!(!report.mutates_accepted_evidence_ledger);
        assert!(!report.creates_level2_evidence);
        assert!(!report.populates_score_axes);
        assert!(!report.grants_authority);
        assert!(!report.retains_raw_provider_artifacts);
        assert!(!report.retains_credentials_or_secrets);
        assert_eq!(
            report.nonclaims,
            gateway_operator_bridge_acceptance_preview_required_nonclaims()
        );
        assert_ne!(report.digest(), Hash([0; 32]));
        let _ = fs::remove_dir_all(report_root);
        let _ = fs::remove_dir_all(output_root);
    }

    #[test]
    fn gateway_operator_bridge_acceptance_preview_rejects_ledger_and_authority_escalation() {
        let proposal = gateway_proposal("gateway-bridge-acceptance-escalation-action");
        let report_root = temp_output_root("gateway-bridge-acceptance-escalation-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-acceptance-escalation");
        let mut request = gateway_operator_bridge_acceptance_preview_request(
            &proposal,
            &report_manifest,
            &output_root,
        );
        request.candidate_only = false;
        request.accepted_evidence_mutation_requested = true;
        request.level2_evidence_requested = true;
        request.score_axis_population_requested = true;
        request.authority_grant_requested = true;

        let validation = validate_gateway_operator_bridge_acceptance_preview_request(&request);

        assert!(!validation.valid);
        assert!(validation
            .issues
            .contains(&GatewayOperatorBridgeAcceptancePreviewIssue::NotCandidateOnly));
        assert!(validation.issues.contains(
            &GatewayOperatorBridgeAcceptancePreviewIssue::AcceptedEvidenceMutationRequested
        ));
        assert!(validation
            .issues
            .contains(&GatewayOperatorBridgeAcceptancePreviewIssue::Level2EvidenceRequested));
        assert!(validation
            .issues
            .contains(&GatewayOperatorBridgeAcceptancePreviewIssue::ScoreAxisPopulationRequested));
        assert!(validation
            .issues
            .contains(&GatewayOperatorBridgeAcceptancePreviewIssue::AuthorityGrantRequested));
        let _ = fs::remove_dir_all(report_root);
        let _ = fs::remove_dir_all(output_root);
    }

    #[test]
    fn gateway_operator_bridge_acceptance_preview_rejects_preflight_digest_drift() {
        let proposal = gateway_proposal("gateway-bridge-acceptance-digest-action");
        let report_root = temp_output_root("gateway-bridge-acceptance-digest-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-acceptance-digest");
        let mut request = gateway_operator_bridge_acceptance_preview_request(
            &proposal,
            &report_manifest,
            &output_root,
        );
        request.expected_preflight_report_digest = Hash([7; 32]);

        let validation = validate_gateway_operator_bridge_acceptance_preview_request(&request);

        assert_eq!(
            validation.issues,
            vec![GatewayOperatorBridgeAcceptancePreviewIssue::PreflightDigestMismatch]
        );
        let _ = fs::remove_dir_all(report_root);
        let _ = fs::remove_dir_all(output_root);
    }

    #[test]
    fn gateway_operator_bridge_acceptance_preview_rejects_invalid_source_preflight() {
        let proposal = gateway_proposal("gateway-bridge-acceptance-source-action");
        let report_root = temp_output_root("gateway-bridge-acceptance-source-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-acceptance-source");
        let mut request = gateway_operator_bridge_acceptance_preview_request(
            &proposal,
            &report_manifest,
            &output_root,
        );
        request
            .source_preflight_report
            .mutates_accepted_evidence_ledger = true;
        request.expected_preflight_report_digest = request.source_preflight_report.digest();

        let validation = validate_gateway_operator_bridge_acceptance_preview_request(&request);

        assert_eq!(
            validation.issues,
            vec![GatewayOperatorBridgeAcceptancePreviewIssue::SourcePreflightInvalid]
        );
        let _ = fs::remove_dir_all(report_root);
        let _ = fs::remove_dir_all(output_root);
    }

    #[test]
    fn gateway_operator_bridge_acceptance_preview_rejects_production_claim_text() {
        let proposal = gateway_proposal("gateway-bridge-acceptance-claim-action");
        let report_root = temp_output_root("gateway-bridge-acceptance-claim-report");
        let report_manifest = gateway_report_manifest_for_bridge(proposal.clone(), &report_root);
        let output_root = temp_output_root("gateway-bridge-acceptance-claim");
        let mut request = gateway_operator_bridge_acceptance_preview_request(
            &proposal,
            &report_manifest,
            &output_root,
        );
        request.claim_text = vec!["Production ready accepted evidence.".to_owned()];

        let validation = validate_gateway_operator_bridge_acceptance_preview_request(&request);

        assert!(!validation.valid);
        assert!(validation.issues.contains(
            &GatewayOperatorBridgeAcceptancePreviewIssue::ForbiddenClaimText(
                "production ready".to_owned()
            )
        ));
        assert!(validation.issues.contains(
            &GatewayOperatorBridgeAcceptancePreviewIssue::ForbiddenClaimText(
                "accepted evidence".to_owned()
            )
        ));
        let _ = fs::remove_dir_all(report_root);
        let _ = fs::remove_dir_all(output_root);
    }

    #[test]
    fn gateway_action_acceptance_exposes_handoff_only_after_admission() {
        let proposal = gateway_proposal("gateway-payment-1");
        let policy = gateway_policy();
        let mut journal = AgentAdmissionJournal::default();

        let outcome = evaluate_gateway_action(&proposal, &policy, &mut journal)
            .expect("gateway proposal should evaluate and append");

        assert_eq!(outcome.decision.verdict, AdmissionVerdict::Accepted);
        assert!(outcome.decision.accepted_envelope.is_none());
        let handoff = outcome
            .accepted_handoff
            .expect("accepted gateway action exposes accepted handoff");
        assert_eq!(handoff.action_id, proposal.id);
        assert_eq!(handoff.target, "treasury-safe");
        assert_eq!(journal.entries.len(), 1);
        assert!(journal.validate().is_empty());
    }

    #[test]
    fn gateway_action_rejection_preserves_audit_without_handoff() {
        let mut proposal = gateway_proposal("gateway-payment-rejected");
        proposal.target = "attacker-wallet".to_owned();
        proposal.value_units = 500;
        proposal.direct_authority_requested = true;
        proposal.signer_or_tool_requested_before_admission = true;
        proposal
            .threat_labels
            .insert(GatewayThreatLabel::WrongCounterparty);
        proposal
            .threat_labels
            .insert(GatewayThreatLabel::AmountLimitBypass);

        let policy = gateway_policy();
        let mut journal = AgentAdmissionJournal::default();
        let outcome = evaluate_gateway_action(&proposal, &policy, &mut journal)
            .expect("rejected gateway proposal should still append audit metadata");

        assert_eq!(outcome.decision.verdict, AdmissionVerdict::Rejected);
        assert!(outcome.accepted_handoff.is_none());
        assert!(outcome
            .decision
            .reasons
            .contains(&AdmissionReason("gateway_unauthorized_target".to_owned())));
        assert!(outcome
            .decision
            .reasons
            .contains(&AdmissionReason("gateway_amount_limit_exceeded".to_owned())));
        assert!(outcome.decision.reasons.contains(&AdmissionReason(
            "gateway_signer_or_tool_requested_before_admission".to_owned()
        )));
        assert!(journal.validate().is_empty());
    }

    #[test]
    fn gateway_model_lane_registry_accepts_bounded_local_and_rented_lanes() {
        let local = gateway_model_lane_registry_entry("local-qwen", gateway_model_lane());
        let mut rented_provenance = gateway_model_lane();
        rented_provenance.lane_kind = GatewayModelLaneKind::RentedOpenWeight;
        rented_provenance.artifact_id = "rented-qwen-q4".to_owned();
        rented_provenance.output_bundle_digest = Hash([31; 32]);
        let rented = gateway_model_lane_registry_entry("rented-qwen", rented_provenance);
        let registry = GatewayModelLaneRegistry {
            schema_version: "hsai-gateway-model-lane-registry-v1".to_owned(),
            entries: vec![local, rented],
        };

        assert!(validate_gateway_model_lane_registry(&registry).is_empty());
    }

    #[test]
    fn gateway_model_lane_registry_rejects_missing_model_and_prompt_metadata() {
        let mut provenance = gateway_model_lane();
        provenance.model_family.clear();
        provenance.artifact_id.clear();
        provenance.prompt_template_digest = Hash([0; 32]);
        let registry = GatewayModelLaneRegistry {
            schema_version: "hsai-gateway-model-lane-registry-v1".to_owned(),
            entries: vec![gateway_model_lane_registry_entry("bad-model", provenance)],
        };

        assert_eq!(
            validate_gateway_model_lane_registry(&registry),
            vec![
                GatewayModelLaneRegistryIssue::MissingModelId("bad-model".to_owned()),
                GatewayModelLaneRegistryIssue::MissingPromptTemplateDigest("bad-model".to_owned()),
            ]
        );
    }

    #[test]
    fn gateway_model_lane_registry_rejects_missing_nonsecret_and_stale_output() {
        let mut provenance = gateway_model_lane();
        provenance.non_secret = false;
        provenance.output_bundle_digest = Hash([41; 32]);
        let mut entry = gateway_model_lane_registry_entry("stale-output", provenance);
        entry.expected_output_bundle_digest = Hash([42; 32]);
        let registry = GatewayModelLaneRegistry {
            schema_version: "hsai-gateway-model-lane-registry-v1".to_owned(),
            entries: vec![entry],
        };

        assert_eq!(
            validate_gateway_model_lane_registry(&registry),
            vec![
                GatewayModelLaneRegistryIssue::MissingNonSecretStatement("stale-output".to_owned()),
                GatewayModelLaneRegistryIssue::StaleOutputDigest("stale-output".to_owned()),
            ]
        );
    }

    #[test]
    fn gateway_model_lane_registry_rejects_unbounded_rented_metadata() {
        let mut provenance = gateway_model_lane();
        provenance.lane_kind = GatewayModelLaneKind::RentedOpenWeight;
        let mut entry = gateway_model_lane_registry_entry("rented-unbounded", provenance);
        entry.max_cases_per_run = None;
        entry.max_cost_units_per_case = Some(0);
        let registry = GatewayModelLaneRegistry {
            schema_version: "hsai-gateway-model-lane-registry-v1".to_owned(),
            entries: vec![entry],
        };

        assert_eq!(
            validate_gateway_model_lane_registry(&registry),
            vec![GatewayModelLaneRegistryIssue::UnboundedRentedModelMetadata(
                "rented-unbounded".to_owned()
            )]
        );
    }

    #[test]
    fn gateway_model_lane_registry_rejects_invalid_and_duplicate_lane_ids() {
        let first = gateway_model_lane_registry_entry("duplicate-lane", gateway_model_lane());
        let duplicate = gateway_model_lane_registry_entry("duplicate-lane", gateway_model_lane());
        let invalid = gateway_model_lane_registry_entry("bad lane id", gateway_model_lane());
        let registry = GatewayModelLaneRegistry {
            schema_version: "hsai-gateway-model-lane-registry-v1".to_owned(),
            entries: vec![first, duplicate, invalid],
        };

        assert_eq!(
            validate_gateway_model_lane_registry(&registry),
            vec![
                GatewayModelLaneRegistryIssue::DuplicateLaneId("duplicate-lane".to_owned()),
                GatewayModelLaneRegistryIssue::InvalidLaneId("bad lane id".to_owned()),
            ]
        );
    }

    #[test]
    fn gateway_adversarial_corpus_accepts_full_required_threat_coverage() {
        let corpus = gateway_full_adversarial_corpus();

        assert_eq!(corpus.cases.len(), 14);
        assert_eq!(
            validate_gateway_adversarial_corpus(&corpus, &gateway_model_lane_registry()),
            Vec::<GatewayAdversarialCorpusIssue>::new()
        );
    }

    #[test]
    fn gateway_adversarial_corpus_rejects_invalid_empty_and_missing_benign() {
        let corpus = GatewayAdversarialCorpus {
            schema_version: "hsai-gateway-adversarial-corpus-v1".to_owned(),
            corpus_id: "bad corpus id".to_owned(),
            cases: Vec::new(),
            required_threat_labels: BTreeSet::new(),
        };

        assert_eq!(
            validate_gateway_adversarial_corpus(&corpus, &gateway_model_lane_registry()),
            vec![
                GatewayAdversarialCorpusIssue::InvalidCorpusId,
                GatewayAdversarialCorpusIssue::EmptyCorpus,
                GatewayAdversarialCorpusIssue::MissingAcceptedBenignCase,
            ]
        );
    }

    #[test]
    fn gateway_adversarial_corpus_rejects_duplicate_case_ids() {
        let case = gateway_adversarial_case("gateway-corpus-duplicate", GatewayThreatLabel::Benign);
        let corpus = GatewayAdversarialCorpus {
            schema_version: "hsai-gateway-adversarial-corpus-v1".to_owned(),
            corpus_id: "gateway-duplicate-corpus".to_owned(),
            cases: vec![case.clone(), case],
            required_threat_labels: BTreeSet::new(),
        };

        assert_eq!(
            validate_gateway_adversarial_corpus(&corpus, &gateway_model_lane_registry()),
            vec![GatewayAdversarialCorpusIssue::DuplicateCaseId(
                GatewayActionId("gateway-corpus-duplicate".to_owned())
            )]
        );
    }

    #[test]
    fn gateway_adversarial_corpus_rejects_missing_required_threat_label() {
        let corpus = GatewayAdversarialCorpus {
            schema_version: "hsai-gateway-adversarial-corpus-v1".to_owned(),
            corpus_id: "gateway-missing-threat-corpus".to_owned(),
            cases: vec![gateway_adversarial_case(
                "gateway-corpus-benign-only",
                GatewayThreatLabel::Benign,
            )],
            required_threat_labels: BTreeSet::from([GatewayThreatLabel::WrongCounterparty]),
        };

        assert_eq!(
            validate_gateway_adversarial_corpus(&corpus, &gateway_model_lane_registry()),
            vec![GatewayAdversarialCorpusIssue::MissingRequiredThreatLabel(
                GatewayThreatLabel::WrongCounterparty
            )]
        );
    }

    #[test]
    fn gateway_adversarial_corpus_rejects_unsafe_expected_acceptance() {
        let mut case = gateway_adversarial_case(
            "gateway-corpus-unsafe-accepted",
            GatewayThreatLabel::PromptInjectionPayment,
        );
        case.expected_verdict = AdmissionVerdict::Accepted;
        let corpus = GatewayAdversarialCorpus {
            schema_version: "hsai-gateway-adversarial-corpus-v1".to_owned(),
            corpus_id: "gateway-unsafe-accepted-corpus".to_owned(),
            cases: vec![
                gateway_adversarial_case("gateway-corpus-benign", GatewayThreatLabel::Benign),
                case,
            ],
            required_threat_labels: BTreeSet::new(),
        };

        assert_eq!(
            validate_gateway_adversarial_corpus(&corpus, &gateway_model_lane_registry()),
            vec![GatewayAdversarialCorpusIssue::UnsafeThreatExpectedAccepted(
                GatewayActionId("gateway-corpus-unsafe-accepted".to_owned())
            )]
        );
    }

    #[test]
    fn gateway_adversarial_corpus_rejects_unknown_or_invalid_model_lanes() {
        let mut case =
            gateway_adversarial_case("gateway-corpus-unknown-lane", GatewayThreatLabel::Benign);
        case.proposal.model_lane.artifact_id = "unregistered-model".to_owned();
        let corpus = GatewayAdversarialCorpus {
            schema_version: "hsai-gateway-adversarial-corpus-v1".to_owned(),
            corpus_id: "gateway-unknown-lane-corpus".to_owned(),
            cases: vec![case],
            required_threat_labels: BTreeSet::new(),
        };
        let mut registry = gateway_model_lane_registry();
        registry.entries[0].provenance.non_secret = false;

        assert_eq!(
            validate_gateway_adversarial_corpus(&corpus, &registry),
            vec![
                GatewayAdversarialCorpusIssue::InvalidModelLaneRegistry,
                GatewayAdversarialCorpusIssue::UnknownModelLane(GatewayActionId(
                    "gateway-corpus-unknown-lane".to_owned()
                )),
            ]
        );
    }

    #[test]
    fn gateway_adversarial_corpus_output_run_validates_and_materializes() {
        let corpus = gateway_full_adversarial_corpus();
        let model_lane_registry = gateway_model_lane_registry();
        let policy = gateway_policy();
        let output_root = temp_output_root("gateway-adversarial-output-run");
        let request = gateway_report_request("gateway-adversarial-output-run", &output_root);

        let run = materialize_gateway_adversarial_corpus_output_run(
            &output_root,
            &corpus,
            &model_lane_registry,
            &policy,
            &request,
        )
        .expect("valid adversarial corpus output run succeeds");

        assert_eq!(run.report.metrics.total_cases, 14);
        assert_eq!(run.report.metrics.accepted_count, 1);
        assert_eq!(run.report.metrics.rejected_count, 13);
        assert_eq!(
            run.output_manifest.bundle_id,
            "gateway-adversarial-output-run"
        );
        assert_eq!(
            read_gateway_report_bundle(&output_root)
                .expect("adversarial output readback validates"),
            run.output_manifest
        );

        fs::remove_dir_all(&output_root).expect("temp gateway adversarial output cleanup succeeds");
    }

    #[test]
    fn gateway_adversarial_corpus_output_run_stops_before_output_on_validation_error() {
        let corpus = GatewayAdversarialCorpus {
            schema_version: "hsai-gateway-adversarial-corpus-v1".to_owned(),
            corpus_id: "bad corpus id".to_owned(),
            cases: Vec::new(),
            required_threat_labels: BTreeSet::new(),
        };
        let output_root = temp_output_root("gateway-adversarial-output-invalid");
        let request = gateway_report_request("gateway-adversarial-output-invalid", &output_root);

        assert_eq!(
            materialize_gateway_adversarial_corpus_output_run(
                &output_root,
                &corpus,
                &gateway_model_lane_registry(),
                &gateway_policy(),
                &request,
            ),
            Err(GatewayCorpusOutputRunError::CorpusValidation(vec![
                GatewayAdversarialCorpusIssue::InvalidCorpusId,
                GatewayAdversarialCorpusIssue::EmptyCorpus,
                GatewayAdversarialCorpusIssue::MissingAcceptedBenignCase,
            ]))
        );
        assert!(!output_root.exists());
    }

    #[test]
    fn gateway_adversarial_corpus_output_run_propagates_materialization_rejection() {
        let corpus = gateway_full_adversarial_corpus();
        let output_root = temp_output_root("gateway-adversarial-output-protected");
        let mut request =
            gateway_report_request("gateway-adversarial-output-protected", &output_root);
        request.protected_roots = vec![output_root
            .parent()
            .expect("temp output root has parent")
            .to_path_buf()];

        assert_eq!(
            materialize_gateway_adversarial_corpus_output_run(
                &output_root,
                &corpus,
                &gateway_model_lane_registry(),
                &gateway_policy(),
                &request,
            ),
            Err(GatewayCorpusOutputRunError::Materialization(
                GatewayReportMaterializationError::ProtectedOutputRoot
            ))
        );
        assert!(!output_root.exists());
    }

    #[test]
    fn gateway_baseline_comparison_counts_unsafe_accepts_without_authority() {
        let corpus = gateway_full_adversarial_corpus();
        let policy = gateway_policy();
        let report =
            evaluate_gateway_corpus(&corpus.cases, &policy).expect("gateway corpus evaluates");
        let baseline = gateway_baseline_run(
            "baseline-no-approval",
            &corpus.cases,
            AdmissionVerdict::Accepted,
        );

        let comparison = compare_gateway_baseline(&corpus.cases, &report, &policy, &baseline)
            .expect("baseline comparison succeeds");

        assert_eq!(comparison.total_cases, 14);
        assert_eq!(comparison.hsai_unsafe_accepted_count, 0);
        assert_eq!(comparison.baseline_unsafe_accepted_count, 13);
        assert_eq!(comparison.hsai_false_rejection_count, 0);
        assert_eq!(comparison.baseline_false_rejection_count, 0);
        assert!(comparison.hsai_audit_bundle_complete);
        assert!(!comparison.baseline_audit_bundle_complete);
        assert!(!comparison.authority_granted);
        assert_eq!(
            comparison.claim_boundary,
            GATEWAY_BASELINE_COMPARISON_CLAIM_BOUNDARY
        );
    }

    #[test]
    fn gateway_baseline_comparison_rejects_invalid_report() {
        let corpus = gateway_full_adversarial_corpus();
        let policy = gateway_policy();
        let mut report =
            evaluate_gateway_corpus(&corpus.cases, &policy).expect("gateway corpus evaluates");
        report.metrics.total_cases = 99;
        let baseline = gateway_baseline_run(
            "baseline-invalid-report",
            &corpus.cases,
            AdmissionVerdict::Accepted,
        );

        assert_eq!(
            compare_gateway_baseline(&corpus.cases, &report, &policy, &baseline),
            Err(GatewayBaselineComparisonError::InvalidReport(vec![
                GatewayReportValidationIssue::MetricsTotalMismatch,
            ]))
        );
    }

    #[test]
    fn gateway_baseline_comparison_rejects_missing_required_nonclaim() {
        let cases = vec![gateway_adversarial_case(
            "gateway-baseline-benign",
            GatewayThreatLabel::Benign,
        )];
        let policy = gateway_policy();
        let report = evaluate_gateway_corpus(&cases, &policy).expect("gateway corpus evaluates");
        let mut baseline = gateway_baseline_run(
            "baseline-missing-nonclaim",
            &cases,
            AdmissionVerdict::Accepted,
        );
        baseline
            .nonclaims
            .remove(&NonClaimLabel("not fully secure".to_owned()));

        assert_eq!(
            compare_gateway_baseline(&cases, &report, &policy, &baseline),
            Err(GatewayBaselineComparisonError::InvalidBaseline(vec![
                GatewayBaselineComparisonIssue::MissingRequiredNonclaim(NonClaimLabel(
                    "not fully secure".to_owned()
                )),
            ]))
        );
    }

    #[test]
    fn gateway_baseline_comparison_rejects_duplicate_missing_and_unknown_decisions() {
        let cases = vec![
            gateway_adversarial_case("gateway-baseline-a", GatewayThreatLabel::Benign),
            gateway_adversarial_case("gateway-baseline-b", GatewayThreatLabel::WrongCounterparty),
        ];
        let policy = gateway_policy();
        let report = evaluate_gateway_corpus(&cases, &policy).expect("gateway corpus evaluates");
        let baseline = GatewayBaselineRun {
            baseline_id: "baseline-shape-drift".to_owned(),
            baseline_kind: GatewayBaselineKind::StaticAllowlist,
            decisions: vec![
                GatewayBaselineDecision {
                    proposal_id: cases[0].proposal.id.clone(),
                    verdict: AdmissionVerdict::Accepted,
                },
                GatewayBaselineDecision {
                    proposal_id: cases[0].proposal.id.clone(),
                    verdict: AdmissionVerdict::Accepted,
                },
                GatewayBaselineDecision {
                    proposal_id: GatewayActionId("gateway-baseline-unknown".to_owned()),
                    verdict: AdmissionVerdict::Accepted,
                },
            ],
            nonclaims: gateway_baseline_required_nonclaims(),
        };

        assert_eq!(
            compare_gateway_baseline(&cases, &report, &policy, &baseline),
            Err(GatewayBaselineComparisonError::InvalidBaseline(vec![
                GatewayBaselineComparisonIssue::DuplicateBaselineDecision(GatewayActionId(
                    "gateway-baseline-a".to_owned()
                )),
                GatewayBaselineComparisonIssue::UnknownBaselineDecision(GatewayActionId(
                    "gateway-baseline-unknown".to_owned()
                )),
                GatewayBaselineComparisonIssue::MissingBaselineDecision(GatewayActionId(
                    "gateway-baseline-b".to_owned()
                )),
            ]))
        );
    }

    #[test]
    fn gateway_effectiveness_summary_computes_local_rates_and_threat_coverage() {
        let corpus = gateway_full_adversarial_corpus();
        let policy = gateway_policy();
        let report =
            evaluate_gateway_corpus(&corpus.cases, &policy).expect("gateway corpus evaluates");

        let summary = gateway_effectiveness_summary(&corpus.cases, &report, &policy)
            .expect("effectiveness summary computes");

        assert_eq!(summary.total_cases, 14);
        assert_eq!(summary.unsafe_case_count, 13);
        assert_eq!(summary.benign_expected_accept_count, 1);
        assert_eq!(summary.unsafe_action_block_rate_basis_points, 10_000);
        assert_eq!(summary.false_rejection_rate_basis_points, 0);
        assert_eq!(summary.quarantine_rate_basis_points, 0);
        assert_eq!(
            summary.decision_recomputation_agreement_rate_basis_points,
            10_000
        );
        assert!(summary.audit_bundle_complete);
        assert!(summary
            .covered_threat_labels
            .is_superset(&gateway_required_adversarial_threat_labels()));
        assert!(summary.threat_coverage.iter().any(|row| {
            row.threat_label == GatewayThreatLabel::WrongCounterparty
                && row.case_count == 1
                && row.blocked_count == 1
        }));
        assert_eq!(
            summary.claim_boundary,
            GATEWAY_EFFECTIVENESS_SUMMARY_CLAIM_BOUNDARY
        );
        assert!(!summary.authority_granted);
    }

    #[test]
    fn gateway_effectiveness_summary_rejects_invalid_report() {
        let corpus = gateway_full_adversarial_corpus();
        let policy = gateway_policy();
        let mut report =
            evaluate_gateway_corpus(&corpus.cases, &policy).expect("gateway corpus evaluates");
        report.metrics.total_cases = 99;

        assert_eq!(
            gateway_effectiveness_summary(&corpus.cases, &report, &policy),
            Err(vec![GatewayReportValidationIssue::MetricsTotalMismatch])
        );
    }

    #[test]
    fn gateway_effectiveness_summary_handles_empty_local_denominators() {
        let cases = vec![gateway_adversarial_case(
            "gateway-summary-benign",
            GatewayThreatLabel::Benign,
        )];
        let policy = gateway_policy();
        let report = evaluate_gateway_corpus(&cases, &policy).expect("gateway corpus evaluates");

        let summary = gateway_effectiveness_summary(&cases, &report, &policy)
            .expect("effectiveness summary computes");

        assert_eq!(summary.unsafe_case_count, 0);
        assert_eq!(summary.unsafe_action_block_rate_basis_points, 0);
        assert_eq!(summary.false_rejection_rate_basis_points, 0);
        assert_eq!(summary.quarantine_rate_basis_points, 0);
        assert_eq!(
            summary.decision_recomputation_agreement_rate_basis_points,
            10_000
        );
    }

    #[test]
    fn gateway_cost_router_uses_no_model_for_deterministic_policy_violation() {
        let mut proposal = gateway_proposal("gateway-cost-reject");
        proposal.target = "attacker-wallet".to_owned();
        proposal.value_units = 500;
        proposal
            .threat_labels
            .insert(GatewayThreatLabel::WrongCounterparty);

        let decision =
            route_gateway_action_cost(&proposal, &gateway_policy(), &gateway_cost_policy());

        assert_eq!(decision.route, GatewayCostRoute::DeterministicOnly);
        assert_eq!(decision.estimated_cost_units, 0);
        assert!(!decision.authority_granted);
        assert!(decision
            .reasons
            .contains(&GatewayCostRouteReason::DeterministicPolicyViolation));
        assert!(decision
            .reasons
            .contains(&GatewayCostRouteReason::NoAuthorityGrantedByRouter));
    }

    #[test]
    fn gateway_cost_router_routes_moderate_clean_actions_to_local_review() {
        let mut proposal = gateway_proposal("gateway-cost-local-review");
        proposal.value_units = 50;

        let decision =
            route_gateway_action_cost(&proposal, &gateway_policy(), &gateway_cost_policy());

        assert_eq!(decision.route, GatewayCostRoute::LocalOpenWeightReview);
        assert_eq!(decision.estimated_cost_units, 1);
        assert!(!decision.authority_granted);
        assert!(decision
            .reasons
            .contains(&GatewayCostRouteReason::LocalReviewForModerateValue));
    }

    #[test]
    fn gateway_cost_router_uses_verifier_mixture_for_threat_labels() {
        let mut proposal = gateway_proposal("gateway-cost-verifier");
        proposal.value_units = 20;
        proposal
            .threat_labels
            .insert(GatewayThreatLabel::PromptInjectionPayment);

        let decision =
            route_gateway_action_cost(&proposal, &gateway_policy(), &gateway_cost_policy());

        assert_eq!(decision.route, GatewayCostRoute::VerifierMixture);
        assert_eq!(decision.estimated_cost_units, 3);
        assert!(!decision.authority_granted);
        assert!(decision
            .reasons
            .contains(&GatewayCostRouteReason::ThreatLabelNeedsVerifierMixture));
    }

    #[test]
    fn gateway_cost_router_premium_budget_exhaustion_fails_to_operator_review() {
        let mut proposal = gateway_proposal("gateway-cost-budget");
        proposal.value_units = 250;
        let gateway_policy = gateway_local_default_policy(
            "gateway-cost-high-value-policy",
            BTreeSet::from([GatewayActionKind::Payment]),
            BTreeSet::from(["treasury-safe".to_owned()]),
            500,
        );
        let mut router_policy = gateway_cost_policy();
        router_policy.premium_escalation_budget_units = 19;

        let decision = route_gateway_action_cost(&proposal, &gateway_policy, &router_policy);

        assert_eq!(decision.route, GatewayCostRoute::OperatorReviewRequired);
        assert_eq!(decision.estimated_cost_units, 50);
        assert!(!decision.authority_granted);
        assert!(decision
            .reasons
            .contains(&GatewayCostRouteReason::HighValueNeedsPremiumEscalation));
        assert!(decision
            .reasons
            .contains(&GatewayCostRouteReason::PremiumEscalationBudgetExceeded));
    }

    #[test]
    fn gateway_cost_router_never_routes_deployments_without_operator_review() {
        let mut proposal = gateway_proposal("gateway-cost-deploy");
        proposal.action_kind = GatewayActionKind::Deployment;
        proposal.target = "mcp-safe-tool".to_owned();
        let mut policy = gateway_policy();
        policy
            .allowed_action_kinds
            .insert(GatewayActionKind::Deployment);

        let decision = route_gateway_action_cost(&proposal, &policy, &gateway_cost_policy());

        assert_eq!(decision.route, GatewayCostRoute::OperatorReviewRequired);
        assert_eq!(decision.estimated_cost_units, 50);
        assert!(!decision.authority_granted);
        assert!(decision
            .reasons
            .contains(&GatewayCostRouteReason::OperatorOnlyActionKind));
    }

    #[test]
    fn gateway_corpus_metrics_cover_blocking_and_recomputation() {
        let accepted = GatewayCorpusCase {
            proposal: gateway_proposal("gateway-benign"),
            expected_verdict: AdmissionVerdict::Accepted,
        };
        let mut duplicate_key = gateway_proposal("gateway-duplicate-key");
        duplicate_key.signer_or_tool_requested_before_admission = true;
        duplicate_key
            .threat_labels
            .insert(GatewayThreatLabel::DuplicateJsonKeyPayload);
        let mut policy_downgrade = gateway_proposal("gateway-policy-downgrade");
        policy_downgrade.target = "unknown-target".to_owned();
        policy_downgrade
            .threat_labels
            .insert(GatewayThreatLabel::PolicyDowngrade);
        let cases = vec![
            accepted,
            GatewayCorpusCase {
                proposal: duplicate_key,
                expected_verdict: AdmissionVerdict::Rejected,
            },
            GatewayCorpusCase {
                proposal: policy_downgrade,
                expected_verdict: AdmissionVerdict::Rejected,
            },
        ];

        let report = evaluate_gateway_corpus(&cases, &gateway_policy())
            .expect("gateway corpus should evaluate");

        assert_eq!(report.metrics.total_cases, 3);
        assert_eq!(report.metrics.accepted_count, 1);
        assert_eq!(report.metrics.rejected_count, 2);
        assert_eq!(report.metrics.unsafe_action_blocked_count, 2);
        assert_eq!(report.metrics.false_rejection_count, 0);
        assert_eq!(report.metrics.duplicate_key_detection_count, 1);
        assert_eq!(report.metrics.policy_downgrade_detection_count, 1);
        assert_eq!(report.metrics.decision_recomputation_agreement_count, 3);
        assert!(report.metrics.audit_bundle_complete);
    }

    #[test]
    fn gateway_report_artifact_binds_json_markdown_and_nonclaims() {
        let cases = vec![GatewayCorpusCase {
            proposal: gateway_proposal("gateway-report-benign"),
            expected_verdict: AdmissionVerdict::Accepted,
        }];
        let policy = gateway_policy();
        let report =
            evaluate_gateway_corpus(&cases, &policy).expect("gateway corpus should evaluate");

        let artifact =
            gateway_report_artifact(&report, &policy).expect("valid report should render");

        assert_eq!(
            artifact.manifest.schema_version,
            "hsai-gateway-report-artifact-v1"
        );
        assert_eq!(artifact.manifest.policy_id, policy.id);
        assert_eq!(
            artifact.manifest.report_json_sha256,
            hash_bytes(&artifact.report_json)
        );
        assert_eq!(
            artifact.manifest.report_markdown_sha256,
            hash_bytes(&artifact.report_markdown)
        );
        assert!(artifact
            .manifest
            .nonclaims
            .contains(&NonClaimLabel("not benchmark evidence".to_owned())));
        assert!(artifact
            .manifest
            .nonclaims
            .contains(&NonClaimLabel("not fully secure".to_owned())));

        let markdown =
            String::from_utf8(artifact.report_markdown).expect("gateway report markdown is utf-8");
        assert!(markdown.contains("local gateway report metadata only"));
        assert!(markdown.contains("gateway-report-benign"));
        assert!(markdown.contains("accepted-only"));
        assert!(markdown.contains("not production readiness"));
    }

    #[test]
    fn gateway_report_artifact_is_deterministic_for_same_report() {
        let cases = vec![
            GatewayCorpusCase {
                proposal: gateway_proposal("gateway-report-a"),
                expected_verdict: AdmissionVerdict::Accepted,
            },
            GatewayCorpusCase {
                proposal: {
                    let mut proposal = gateway_proposal("gateway-report-b");
                    proposal.target = "unknown-target".to_owned();
                    proposal
                        .threat_labels
                        .insert(GatewayThreatLabel::PolicyDowngrade);
                    proposal
                },
                expected_verdict: AdmissionVerdict::Rejected,
            },
        ];
        let policy = gateway_policy();
        let report =
            evaluate_gateway_corpus(&cases, &policy).expect("gateway corpus should evaluate");

        let first = gateway_report_artifact(&report, &policy).expect("first render succeeds");
        let second = gateway_report_artifact(&report, &policy).expect("second render succeeds");

        assert_eq!(first.manifest, second.manifest);
        assert_eq!(first.manifest.digest(), second.manifest.digest());
        assert_eq!(first.report_json, second.report_json);
        assert_eq!(first.report_markdown, second.report_markdown);
    }

    #[test]
    fn gateway_report_artifact_rejects_stale_metrics() {
        let cases = vec![GatewayCorpusCase {
            proposal: gateway_proposal("gateway-report-stale"),
            expected_verdict: AdmissionVerdict::Accepted,
        }];
        let policy = gateway_policy();
        let mut report =
            evaluate_gateway_corpus(&cases, &policy).expect("gateway corpus should evaluate");
        report.metrics.total_cases = 99;
        report.metrics.accepted_count = 0;

        assert_eq!(
            gateway_report_artifact(&report, &policy),
            Err(GatewayReportArtifactError::InvalidReport(vec![
                GatewayReportValidationIssue::MetricsTotalMismatch,
                GatewayReportValidationIssue::MetricsVerdictCountMismatch,
            ]))
        );
    }

    #[test]
    fn gateway_report_bundle_materializes_declared_files_and_readback() {
        let cases = vec![
            GatewayCorpusCase {
                proposal: gateway_proposal("gateway-output-accepted"),
                expected_verdict: AdmissionVerdict::Accepted,
            },
            GatewayCorpusCase {
                proposal: {
                    let mut proposal = gateway_proposal("gateway-output-rejected");
                    proposal.target = "unknown-target".to_owned();
                    proposal
                        .threat_labels
                        .insert(GatewayThreatLabel::PolicyDowngrade);
                    proposal
                },
                expected_verdict: AdmissionVerdict::Rejected,
            },
        ];
        let policy = gateway_policy();
        let report =
            evaluate_gateway_corpus(&cases, &policy).expect("gateway corpus should evaluate");
        let output_root = temp_output_root("gateway-report-bundle");
        let request = gateway_report_request("gateway-report-bundle", &output_root);

        let manifest = materialize_gateway_report_bundle(&output_root, &report, &policy, &request)
            .expect("valid gateway report materializes");

        assert_eq!(manifest.bundle_id, "gateway-report-bundle");
        assert_eq!(manifest.gateway_policy, policy);
        assert_eq!(manifest.artifact_manifest.metrics.total_cases, 2);
        assert_eq!(manifest.artifact_manifest.metrics.accepted_count, 1);
        assert_eq!(manifest.artifact_manifest.metrics.rejected_count, 1);
        assert!(manifest
            .declared_files
            .contains(&"gateway-report/manifest.json".to_owned()));
        assert!(!manifest
            .declared_file_digests
            .contains_key("gateway-report/manifest.json"));

        for logical_path in GATEWAY_REPORT_DECLARED_FILES {
            let path = output_root.join(logical_path);
            assert!(path.is_file(), "{logical_path} should exist");
            assert!(
                sidecar_path(&path).is_file(),
                "{logical_path} sidecar should exist"
            );
        }

        let markdown = fs::read_to_string(output_root.join("gateway-report/report.md"))
            .expect("gateway report markdown is readable");
        assert!(markdown.contains("gateway-output-accepted"));
        assert!(markdown.contains("gateway-output-rejected"));
        assert!(markdown.contains("local gateway report metadata only"));

        let readback = read_gateway_report_bundle(&output_root).expect("readback validates");
        assert_eq!(readback, manifest);

        fs::remove_dir_all(&output_root).expect("temp gateway report cleanup succeeds");
    }

    #[test]
    fn gateway_report_bundle_rejects_protected_roots_and_undeclared_files() {
        let cases = vec![GatewayCorpusCase {
            proposal: gateway_proposal("gateway-output-protected"),
            expected_verdict: AdmissionVerdict::Accepted,
        }];
        let policy = gateway_policy();
        let report =
            evaluate_gateway_corpus(&cases, &policy).expect("gateway corpus should evaluate");
        let output_root = temp_output_root("gateway-report-protected");
        let protected = output_root
            .parent()
            .expect("temp output root has parent")
            .to_path_buf();
        let mut request = gateway_report_request("gateway-report-protected", &output_root);
        request.protected_roots = vec![protected];

        assert_eq!(
            materialize_gateway_report_bundle(&output_root, &report, &policy, &request),
            Err(GatewayReportMaterializationError::ProtectedOutputRoot)
        );

        let request = gateway_report_request("gateway-report-undeclared", &output_root);
        materialize_gateway_report_bundle(&output_root, &report, &policy, &request)
            .expect("valid gateway report materializes");
        fs::write(
            output_root.join("gateway-report/unexpected.txt"),
            b"unexpected",
        )
        .expect("unexpected gateway file writes");
        assert_eq!(
            read_gateway_report_bundle(&output_root),
            Err(GatewayReportMaterializationError::UndeclaredFile(
                "gateway-report/unexpected.txt".to_owned()
            ))
        );

        fs::remove_dir_all(&output_root).expect("temp gateway report cleanup succeeds");
    }

    #[test]
    fn gateway_report_bundle_readback_rejects_tampered_report() {
        let cases = vec![GatewayCorpusCase {
            proposal: gateway_proposal("gateway-output-tamper"),
            expected_verdict: AdmissionVerdict::Accepted,
        }];
        let policy = gateway_policy();
        let mut report =
            evaluate_gateway_corpus(&cases, &policy).expect("gateway corpus should evaluate");
        let output_root = temp_output_root("gateway-report-tamper");
        let request = gateway_report_request("gateway-report-tamper", &output_root);
        materialize_gateway_report_bundle(&output_root, &report, &policy, &request)
            .expect("valid gateway report materializes");

        report.metrics.total_cases = 99;
        rewrite_gateway_file_and_manifest_digest(
            &output_root,
            "gateway-report/report.json",
            &serde_json::to_vec_pretty(&report).expect("tampered report serializes"),
        );
        assert_eq!(
            read_gateway_report_bundle(&output_root),
            Err(GatewayReportMaterializationError::InvalidReport(vec![
                GatewayReportValidationIssue::MetricsTotalMismatch,
            ]))
        );

        fs::remove_dir_all(&output_root).expect("temp gateway report cleanup succeeds");
    }

    #[test]
    fn gateway_corpus_output_run_evaluates_and_materializes() {
        let cases = vec![
            GatewayCorpusCase {
                proposal: gateway_proposal("gateway-run-accepted"),
                expected_verdict: AdmissionVerdict::Accepted,
            },
            GatewayCorpusCase {
                proposal: {
                    let mut proposal = gateway_proposal("gateway-run-rejected");
                    proposal.target = "unknown-target".to_owned();
                    proposal
                        .threat_labels
                        .insert(GatewayThreatLabel::PolicyDowngrade);
                    proposal
                },
                expected_verdict: AdmissionVerdict::Rejected,
            },
        ];
        let policy = gateway_policy();
        let output_root = temp_output_root("gateway-output-run");
        let request = gateway_report_request("gateway-output-run", &output_root);

        let run = materialize_gateway_corpus_output_run(&output_root, &cases, &policy, &request)
            .expect("gateway output run succeeds");

        assert_eq!(run.report.metrics.total_cases, 2);
        assert_eq!(run.report.metrics.accepted_count, 1);
        assert_eq!(run.output_manifest.bundle_id, "gateway-output-run");
        assert_eq!(
            read_gateway_report_bundle(&output_root).expect("output run readback validates"),
            run.output_manifest
        );

        fs::remove_dir_all(&output_root).expect("temp gateway output run cleanup succeeds");
    }

    #[test]
    fn gateway_corpus_output_run_stops_before_output_on_evaluation_error() {
        let proposal = gateway_proposal("gateway-run-duplicate");
        let cases = vec![
            GatewayCorpusCase {
                proposal: proposal.clone(),
                expected_verdict: AdmissionVerdict::Accepted,
            },
            GatewayCorpusCase {
                proposal,
                expected_verdict: AdmissionVerdict::Accepted,
            },
        ];
        let policy = gateway_policy();
        let output_root = temp_output_root("gateway-output-run-duplicate");
        let request = gateway_report_request("gateway-output-run-duplicate", &output_root);

        assert!(matches!(
            materialize_gateway_corpus_output_run(&output_root, &cases, &policy, &request),
            Err(GatewayCorpusOutputRunError::Evaluation(
                JournalError::ReplayedCandidate(_)
            ))
        ));
        assert!(!output_root.exists());
    }

    #[test]
    fn gateway_corpus_output_run_propagates_output_rejection() {
        let cases = vec![GatewayCorpusCase {
            proposal: gateway_proposal("gateway-run-protected"),
            expected_verdict: AdmissionVerdict::Accepted,
        }];
        let policy = gateway_policy();
        let output_root = temp_output_root("gateway-output-run-protected");
        let mut request = gateway_report_request("gateway-output-run-protected", &output_root);
        request.protected_roots = vec![output_root
            .parent()
            .expect("temp output root has parent")
            .to_path_buf()];

        assert_eq!(
            materialize_gateway_corpus_output_run(&output_root, &cases, &policy, &request),
            Err(GatewayCorpusOutputRunError::Materialization(
                GatewayReportMaterializationError::ProtectedOutputRoot
            ))
        );
        assert!(!output_root.exists());
    }

    #[test]
    fn gateway_replay_rejected_by_existing_journal_chain() {
        let proposal = gateway_proposal("gateway-replayed");
        let policy = gateway_policy();
        let mut journal = AgentAdmissionJournal::default();

        evaluate_gateway_action(&proposal, &policy, &mut journal)
            .expect("first gateway action appends");
        assert_eq!(
            evaluate_gateway_action(&proposal, &policy, &mut journal),
            Err(JournalError::ReplayedCandidate(
                gateway_action_candidate(&proposal, &policy).digest()
            ))
        );
    }

    #[test]
    fn rejected_candidate_appends_audit_metadata_without_envelope() {
        let mut candidate = AgentAdmissionCandidate::from_case(
            "candidate-2",
            case(),
            BTreeSet::from([artifact("case", 3)]),
            BTreeSet::from([
                nonclaim("not semantic correctness"),
                nonclaim("not accepted evidence"),
            ]),
        );
        candidate.provider_direct_authority_requested = true;

        let admission_policy = policy();
        let decision = evaluate_admission(&candidate, &admission_policy);
        assert_eq!(decision.verdict, AdmissionVerdict::Rejected);
        assert_eq!(
            decision.reasons,
            vec![AdmissionReason(
                "provider_direct_authority_forbidden".to_owned()
            )]
        );
        assert!(accepted_claim_envelope(&candidate, &admission_policy, &decision).is_none());

        let mut journal = AgentAdmissionJournal::default();
        let entry = journal
            .append_decision(&candidate, &admission_policy, decision)
            .expect("rejected decision should still append audit metadata");
        assert_eq!(entry.sequence_number, 0);
        assert_eq!(entry.decision.verdict, AdmissionVerdict::Rejected);
        assert!(journal.validate().is_empty());
    }

    #[test]
    fn policy_rejects_boundary_nonclaim_digest_score_and_mutation_drift() {
        let mut candidate = accepted_candidate();
        candidate.requested_claim_boundary = AdmissionClaimBoundary::Level2OrHigher;
        candidate.source_artifact_digests.clear();
        candidate
            .nonclaims
            .remove(&nonclaim("not accepted evidence"));
        candidate.accepted_ledger_mutation_requested = true;
        candidate.score_axis_population_requested = true;
        candidate.external_or_formal_evidence_claimed = true;

        let decision = evaluate_admission(&candidate, &policy());
        assert_eq!(decision.verdict, AdmissionVerdict::Rejected);
        assert_eq!(
            decision.reasons,
            vec![
                reason("source_kind_claim_boundary_mismatch"),
                reason("claim_boundary_elevation_forbidden"),
                reason("source_artifact_digest_required"),
                AdmissionReason("missing_nonclaim:not accepted evidence".to_owned()),
                reason("accepted_ledger_mutation_requires_separate_phase"),
                reason("score_axis_population_forbidden"),
                reason("external_or_formal_evidence_claim_forbidden"),
            ]
        );
        assert!(decision.accepted_envelope.is_none());
    }

    #[test]
    fn raw_provider_output_is_quarantined_until_strictly_decoded() {
        let mut candidate = accepted_candidate();
        candidate.id = AdmissionCandidateId("candidate-raw-provider".to_owned());
        candidate.source_kind = AdmissionSourceKind::ProviderResponse;
        candidate.strict_typed = false;

        let decision = evaluate_admission(&candidate, &policy());
        assert_eq!(decision.verdict, AdmissionVerdict::Quarantined);
        assert_eq!(
            decision.reasons,
            vec![
                reason("provider_response_envelope_forbidden"),
                reason("source_kind_claim_boundary_mismatch"),
                reason("strict_typed_candidate_required"),
            ]
        );
        assert!(decision.accepted_envelope.is_none());
    }

    #[test]
    fn admission_rejects_source_kind_shape_drift() {
        let mut missing_envelope = accepted_candidate();
        missing_envelope.proposed_envelope = None;
        assert!(evaluate_admission(&missing_envelope, &policy())
            .reasons
            .contains(&reason("claim_envelope_payload_required")));

        let mut injected_case = accepted_candidate();
        injected_case.case = Some(case());
        assert!(evaluate_admission(&injected_case, &policy())
            .reasons
            .contains(&reason("claim_envelope_case_forbidden")));

        let mut case_with_envelope = AgentAdmissionCandidate::from_case(
            "case-with-envelope",
            case(),
            BTreeSet::from([artifact("case", 1)]),
            policy().required_nonclaims,
        );
        case_with_envelope.proposed_envelope = Some(envelope());
        assert!(evaluate_admission(&case_with_envelope, &policy())
            .reasons
            .contains(&reason("agent_case_envelope_forbidden")));

        let mut subject_mismatch = case_with_envelope;
        subject_mismatch.proposed_envelope = None;
        subject_mismatch.subject = subject("different-agent");
        assert!(evaluate_admission(&subject_mismatch, &policy())
            .reasons
            .contains(&reason("agent_case_subject_mismatch")));

        let mut strict_provider = accepted_candidate();
        strict_provider.source_kind = AdmissionSourceKind::ProviderResponse;
        strict_provider.proposed_envelope = None;
        assert_eq!(
            evaluate_admission(&strict_provider, &policy()).verdict,
            AdmissionVerdict::Rejected
        );
        assert!(evaluate_admission(&strict_provider, &policy())
            .reasons
            .contains(&reason("provider_response_requires_typed_conversion")));

        let mut benchmark_with_envelope = accepted_candidate();
        benchmark_with_envelope.source_kind = AdmissionSourceKind::BenchmarkResultProposal;
        assert!(evaluate_admission(&benchmark_with_envelope, &policy())
            .reasons
            .contains(&reason("benchmark_result_envelope_forbidden")));

        let intake = valid_pcsm_intake();
        let mut pcsm = pcsm_bounded_proof_handoff_candidate("pcsm-shape", subject("pcsm"), &intake)
            .expect("valid PCSM candidate maps");
        pcsm.proposed_envelope = Some(envelope());
        assert!(evaluate_admission(
            &pcsm,
            &AgentAdmissionPolicy::local_default(pcsm_bounded_proof_required_nonclaims())
        )
        .reasons
        .contains(&reason("pcsm_handoff_envelope_forbidden")));
    }

    #[test]
    fn admission_rejects_invalid_artifact_digests() {
        let mut candidate = accepted_candidate();
        candidate.source_artifact_digests = BTreeSet::from([
            artifact("", 5),
            artifact(" bad", 1),
            artifact("bad$id", 6),
            artifact("bad..id", 7),
            artifact("path/artifact", 2),
            artifact("zero", 0),
            artifact("conflict", 3),
            artifact("conflict", 4),
        ]);

        let reasons = evaluate_admission(&candidate, &policy()).reasons;
        assert!(reasons.contains(&AdmissionReason("invalid_source_artifact_id:".to_owned())));
        assert!(reasons.contains(&AdmissionReason(
            "invalid_source_artifact_id: bad".to_owned()
        )));
        assert!(reasons.contains(&AdmissionReason(
            "invalid_source_artifact_id:bad$id".to_owned()
        )));
        assert!(reasons.contains(&AdmissionReason(
            "invalid_source_artifact_id:bad..id".to_owned()
        )));
        assert!(reasons.contains(&AdmissionReason(
            "invalid_source_artifact_id:path/artifact".to_owned()
        )));
        assert!(reasons.contains(&AdmissionReason(
            "zero_source_artifact_digest:zero".to_owned()
        )));
        assert!(reasons.contains(&AdmissionReason(
            "conflicting_source_artifact_digest_id:conflict".to_owned()
        )));

        let mut intake = valid_pcsm_intake();
        intake.source_artifact_digests = candidate.source_artifact_digests;
        let errors = validate_pcsm_bounded_proof_handoff_intake(&intake);
        assert!(
            errors.contains(&PcsmHandoffIntakeError::InvalidSourceArtifactId(
                String::new()
            ))
        );
        assert!(
            errors.contains(&PcsmHandoffIntakeError::InvalidSourceArtifactId(
                " bad".to_owned()
            ))
        );
        assert!(
            errors.contains(&PcsmHandoffIntakeError::InvalidSourceArtifactId(
                "bad$id".to_owned()
            ))
        );
        assert!(
            errors.contains(&PcsmHandoffIntakeError::InvalidSourceArtifactId(
                "bad..id".to_owned()
            ))
        );
        assert!(
            errors.contains(&PcsmHandoffIntakeError::InvalidSourceArtifactId(
                "path/artifact".to_owned()
            ))
        );
        assert!(
            errors.contains(&PcsmHandoffIntakeError::ZeroSourceArtifactDigest(
                "zero".to_owned()
            ))
        );
        assert!(
            errors.contains(&PcsmHandoffIntakeError::ConflictingSourceArtifactDigestId(
                "conflict".to_owned()
            ))
        );
    }

    #[test]
    fn admission_rejects_invalid_identity_boundary_and_reserved_digest_placement() {
        for invalid_id in [
            "",
            " ",
            " candidate",
            "candidate ",
            "a/b",
            r"a\b",
            "a..b",
            "a$b",
        ] {
            let mut candidate = accepted_candidate();
            candidate.id = AdmissionCandidateId(invalid_id.to_owned());
            assert!(evaluate_admission(&candidate, &policy())
                .reasons
                .contains(&reason("invalid_candidate_id")));
        }

        for invalid_subject in ["", " ", " agent-a", "agent-a "] {
            let mut candidate = accepted_candidate();
            candidate.subject = subject(invalid_subject);
            assert!(evaluate_admission(&candidate, &policy())
                .reasons
                .contains(&reason("invalid_candidate_subject")));
        }

        let boundaries = [
            AdmissionClaimBoundary::LocalOnly,
            AdmissionClaimBoundary::Level1Local,
            AdmissionClaimBoundary::Level2OrHigher,
            AdmissionClaimBoundary::Formal,
        ];
        for (source_kind, expected) in [
            (
                AdmissionSourceKind::AgentCase,
                AdmissionClaimBoundary::LocalOnly,
            ),
            (
                AdmissionSourceKind::ClaimEnvelopeProposal,
                AdmissionClaimBoundary::Level1Local,
            ),
            (
                AdmissionSourceKind::ProviderResponse,
                AdmissionClaimBoundary::LocalOnly,
            ),
            (
                AdmissionSourceKind::BenchmarkResultProposal,
                AdmissionClaimBoundary::LocalOnly,
            ),
            (
                AdmissionSourceKind::PcsmBoundedProofHandoff,
                AdmissionClaimBoundary::LocalOnly,
            ),
        ] {
            for boundary in &boundaries {
                let mut candidate = accepted_candidate();
                candidate.source_kind = source_kind.clone();
                candidate.requested_claim_boundary = boundary.clone();
                candidate.case = None;
                candidate.proposed_envelope =
                    (source_kind == AdmissionSourceKind::ClaimEnvelopeProposal).then(envelope);
                if source_kind == AdmissionSourceKind::ProviderResponse {
                    candidate.strict_typed = false;
                }
                if source_kind == AdmissionSourceKind::PcsmBoundedProofHandoff {
                    candidate.source_artifact_digests.insert(ArtifactDigest {
                        id: PCSM_BOUNDED_PROOF_INTAKE_DIGEST_ID.to_owned(),
                        sha256: Hash([9; 32]),
                    });
                }
                let reasons = evaluate_admission(&candidate, &policy()).reasons;
                assert_eq!(
                    reasons.contains(&reason("source_kind_claim_boundary_mismatch")),
                    *boundary != expected
                );
            }
        }

        let mut non_pcsm = accepted_candidate();
        non_pcsm.source_artifact_digests.insert(ArtifactDigest {
            id: PCSM_BOUNDED_PROOF_INTAKE_DIGEST_ID.to_owned(),
            sha256: Hash([9; 32]),
        });
        assert!(evaluate_admission(&non_pcsm, &policy())
            .reasons
            .contains(&reason("pcsm_intake_digest_forbidden")));

        let intake = valid_pcsm_intake();
        let pcsm_policy =
            AgentAdmissionPolicy::local_default(pcsm_bounded_proof_required_nonclaims());
        let mut pcsm =
            pcsm_bounded_proof_handoff_candidate("pcsm-reserved", subject("pcsm"), &intake)
                .expect("valid PCSM candidate maps");
        pcsm.source_artifact_digests
            .retain(|digest| digest.id != PCSM_BOUNDED_PROOF_INTAKE_DIGEST_ID);
        assert!(evaluate_admission(&pcsm, &pcsm_policy)
            .reasons
            .contains(&reason("pcsm_intake_digest_required")));
    }

    #[test]
    fn accepted_envelope_export_requires_exact_evaluated_envelope_candidate() {
        let candidate = accepted_candidate();
        let admission_policy = policy();
        let decision = evaluate_admission(&candidate, &admission_policy);
        assert_eq!(
            accepted_claim_envelope(&candidate, &admission_policy, &decision),
            candidate.proposed_envelope.as_ref()
        );

        let mut forged = decision.clone();
        forged.reasons.push(reason("forged"));
        assert!(accepted_claim_envelope(&candidate, &admission_policy, &forged).is_none());

        let case_candidate = AgentAdmissionCandidate::from_case(
            "case-no-export",
            case(),
            BTreeSet::from([artifact("case", 1)]),
            admission_policy.required_nonclaims.clone(),
        );
        let case_decision = evaluate_admission(&case_candidate, &admission_policy);
        assert_eq!(case_decision.verdict, AdmissionVerdict::Accepted);
        assert!(
            accepted_claim_envelope(&case_candidate, &admission_policy, &case_decision).is_none()
        );
    }

    #[test]
    fn journal_rejects_replay_and_detects_stale_tip() {
        let candidate = accepted_candidate();
        let admission_policy = policy();
        let decision = evaluate_admission(&candidate, &admission_policy);
        let mut journal = AgentAdmissionJournal::default();
        journal
            .append_decision(&candidate, &admission_policy, decision.clone())
            .expect("first append should work");

        assert_eq!(
            journal.append_decision(&candidate, &admission_policy, decision),
            Err(JournalError::ReplayedCandidate(candidate.digest()))
        );

        let mut tampered = journal.clone();
        tampered.entries[0].previous_entry_digest = Some(Hash([9; 32]));
        assert!(tampered
            .validate()
            .contains(&JournalError::PreviousDigestMismatch));

        let mut stale_sequence = journal.clone();
        stale_sequence.entries[0].sequence_number = 9;
        assert!(stale_sequence
            .validate()
            .contains(&JournalError::SequenceMismatch {
                expected: 0,
                actual: 9,
            }));
    }

    #[test]
    fn decision_digest_binds_decision_content() {
        let candidate = accepted_candidate();
        let admission_policy = policy();
        let decision = evaluate_admission(&candidate, &admission_policy);
        let mut journal = AgentAdmissionJournal::default();
        journal
            .append_decision(&candidate, &admission_policy, decision)
            .expect("append should work");

        let mut tampered = journal.clone();
        tampered.entries[0]
            .decision
            .reasons
            .push(reason("late_mutation"));
        assert!(tampered
            .validate()
            .contains(&JournalError::DecisionDigestMismatch));
    }

    #[test]
    fn pcsm_bounded_handoff_intake_becomes_local_metadata_candidate_only() {
        let intake = valid_pcsm_intake();
        assert!(validate_pcsm_bounded_proof_handoff_intake(&intake).is_empty());

        let candidate =
            pcsm_bounded_proof_handoff_candidate("pcsm-handoff-1", subject("pcsm-source"), &intake)
                .expect("valid bounded handoff metadata should become a candidate");

        assert_eq!(
            candidate.source_kind,
            AdmissionSourceKind::PcsmBoundedProofHandoff
        );
        assert_eq!(
            candidate.requested_claim_boundary,
            AdmissionClaimBoundary::LocalOnly
        );
        assert!(candidate.proposed_envelope.is_none());
        assert!(intake
            .source_artifact_digests
            .is_subset(&candidate.source_artifact_digests));
        assert_eq!(
            candidate
                .source_artifact_digests
                .iter()
                .find(|digest| digest.id == PCSM_BOUNDED_PROOF_INTAKE_DIGEST_ID)
                .map(|digest| digest.sha256),
            Some(intake.digest())
        );

        let pcsm_policy =
            AgentAdmissionPolicy::local_default(pcsm_bounded_proof_required_nonclaims());
        let decision = evaluate_admission(&candidate, &pcsm_policy);
        assert_eq!(decision.verdict, AdmissionVerdict::Accepted);
        assert!(accepted_claim_envelope(&candidate, &pcsm_policy, &decision).is_none());

        let mut journal = AgentAdmissionJournal::default();
        journal
            .append_decision(&candidate, &pcsm_policy, decision)
            .expect("local metadata admission decision should append");
        assert!(journal.validate().is_empty());
    }

    #[test]
    fn pcsm_bounded_handoff_rejects_dirty_or_staged_source_snapshots() {
        let mut intake = valid_pcsm_intake();
        intake.source_repo_status = PcsmSourceRepoStatus::StagedOnly;
        intake.source_repo_commit = "not-a-commit".to_owned();
        intake.source_handoff_path = "../docs/pcsm-cl12-bounded-proof-handoff.md".to_owned();
        intake.source_handoff_sha256 = Hash([0; 32]);

        let errors = validate_pcsm_bounded_proof_handoff_intake(&intake);
        assert!(errors.contains(&PcsmHandoffIntakeError::SourceRepoNotClean(
            PcsmSourceRepoStatus::StagedOnly
        )));
        assert!(errors.contains(&PcsmHandoffIntakeError::InvalidSourceCommit));
        assert!(errors.contains(&PcsmHandoffIntakeError::UnsafeSourceHandoffPath));
        assert!(errors.contains(&PcsmHandoffIntakeError::MissingHandoffDigest));
        assert_eq!(
            pcsm_bounded_proof_handoff_candidate("pcsm-handoff-dirty", subject("pcsm"), &intake),
            Err(errors)
        );
    }

    #[test]
    fn pcsm_bounded_handoff_rejects_threshold_and_authority_escalation() {
        let mut intake = valid_pcsm_intake();
        intake.threshold_admitted = true;
        intake.replication_admission_status = "admitted_live_external_runtime".to_owned();
        intake.blocked_item = "none".to_owned();
        intake.provider_direct_authority = true;
        intake.production_authority = true;
        intake.raw_provider_payloads_committed = true;
        intake.accepted_ledger_mutation_requested = true;
        intake.official_submission_requested = true;
        intake.external_replay_requested = true;
        intake.score_axis_population_requested = true;
        intake.level2_evidence_requested = true;

        let errors = validate_pcsm_bounded_proof_handoff_intake(&intake);
        assert!(errors.contains(&PcsmHandoffIntakeError::ThresholdAdmitted));
        assert!(errors.contains(&PcsmHandoffIntakeError::ReplicationStatusNotBlockedPreflight));
        assert!(errors.contains(&PcsmHandoffIntakeError::BlockedItemMismatch));
        assert!(errors.contains(&PcsmHandoffIntakeError::ProviderDirectAuthorityClaimed));
        assert!(errors.contains(&PcsmHandoffIntakeError::ProductionAuthorityClaimed));
        assert!(errors.contains(&PcsmHandoffIntakeError::RawProviderPayloadsCommitted));
        assert!(errors.contains(&PcsmHandoffIntakeError::AcceptedLedgerMutationRequested));
        assert!(errors.contains(&PcsmHandoffIntakeError::OfficialSubmissionRequested));
        assert!(errors.contains(&PcsmHandoffIntakeError::ExternalReplayRequested));
        assert!(errors.contains(&PcsmHandoffIntakeError::ScoreAxisPopulationRequested));
        assert!(errors.contains(&PcsmHandoffIntakeError::Level2EvidenceRequested));
    }

    #[test]
    fn pcsm_bounded_handoff_rejects_missing_verifier_nonclaim_and_counts() {
        let mut intake = valid_pcsm_intake();
        intake.pcsm_accepted = 0;
        intake.pcsm_rejected = 0;
        intake
            .verifier_statuses
            .remove(&pcsm_verifier("source_lint_gate"));
        intake
            .verifier_statuses
            .remove(&pcsm_verifier("verify_native_pcsm"));
        intake.verifier_statuses.replace(PcsmVerifierStatus {
            name: "verify_native_pcsm".to_owned(),
            outcome: PcsmVerifierOutcome::Fail,
        });
        intake
            .nonclaims
            .remove(&NonClaimLabel("not proof".to_owned()));
        intake.source_artifact_digests.clear();

        let errors = validate_pcsm_bounded_proof_handoff_intake(&intake);
        assert!(errors.contains(&PcsmHandoffIntakeError::MissingPcsmCounts));
        assert!(
            errors.contains(&PcsmHandoffIntakeError::MissingVerifierStatus(
                "source_lint_gate"
            ))
        );
        assert!(
            errors.contains(&PcsmHandoffIntakeError::FailedVerifierStatus(
                "verify_native_pcsm".to_owned()
            ))
        );
        assert!(
            errors.contains(&PcsmHandoffIntakeError::MissingRequiredNonclaim(
                "not proof".to_owned()
            ))
        );
        assert!(errors.contains(&PcsmHandoffIntakeError::MissingSourceArtifactDigest));
    }

    #[test]
    fn pcsm_bounded_handoff_rejects_inconsistent_and_overflowing_counts() {
        let mut inconsistent = valid_pcsm_intake();
        inconsistent.pcsm_accepted = 5;
        inconsistent.pcsm_rejected = 1;
        assert!(validate_pcsm_bounded_proof_handoff_intake(&inconsistent)
            .contains(&PcsmHandoffIntakeError::PcsmCountMismatch));

        let mut journal_mismatch = valid_pcsm_intake();
        journal_mismatch.pcsm_journal_entries = 4;
        assert!(
            validate_pcsm_bounded_proof_handoff_intake(&journal_mismatch)
                .contains(&PcsmHandoffIntakeError::PcsmCountMismatch)
        );

        let mut overflowing = valid_pcsm_intake();
        overflowing.pcsm_inputs = u64::MAX;
        overflowing.pcsm_accepted = u64::MAX;
        overflowing.pcsm_rejected = 1;
        overflowing.pcsm_journal_entries = u64::MAX;
        assert!(validate_pcsm_bounded_proof_handoff_intake(&overflowing)
            .contains(&PcsmHandoffIntakeError::PcsmCountOverflow));
    }

    #[test]
    fn pcsm_bounded_handoff_rejects_duplicate_and_unknown_verifiers() {
        let mut intake = valid_pcsm_intake();
        intake.verifier_statuses.insert(PcsmVerifierStatus {
            name: "verify_native_pcsm".to_owned(),
            outcome: PcsmVerifierOutcome::Fail,
        });
        intake
            .verifier_statuses
            .insert(pcsm_verifier("unknown_verifier"));

        let errors = validate_pcsm_bounded_proof_handoff_intake(&intake);
        assert!(
            errors.contains(&PcsmHandoffIntakeError::DuplicateVerifierStatus(
                "verify_native_pcsm".to_owned()
            ))
        );
        assert!(
            errors.contains(&PcsmHandoffIntakeError::FailedVerifierStatus(
                "verify_native_pcsm".to_owned()
            ))
        );
        assert!(
            errors.contains(&PcsmHandoffIntakeError::UnexpectedVerifierStatus(
                "unknown_verifier".to_owned()
            ))
        );
    }

    #[test]
    fn pcsm_bounded_handoff_rejects_missing_identity_and_governance_prerequisites() {
        let mut intake = valid_pcsm_intake();
        intake.source_repo_remote.clear();
        intake.source_repo_branch.clear();
        intake.source_handoff_schema.clear();
        intake.source_handoff_state_slice.clear();
        intake.bounded_breakthrough_evidence_admitted = false;
        intake.local_mlx_surrogate_runtime = false;
        intake.native_pcsm_governed_state = false;
        intake.pcsm_journaled = false;

        let errors = validate_pcsm_bounded_proof_handoff_intake(&intake);
        for field in [
            "source_repo_remote",
            "source_repo_branch",
            "source_handoff_schema",
            "source_handoff_state_slice",
        ] {
            assert!(errors.contains(&PcsmHandoffIntakeError::MissingSourceIdentity(field)));
        }
        assert!(errors.contains(&PcsmHandoffIntakeError::BoundedEvidenceNotAdmitted));
        assert!(errors.contains(&PcsmHandoffIntakeError::LocalMlxSurrogateMissing));
        assert!(errors.contains(&PcsmHandoffIntakeError::NativePcsmGovernanceMissing));
        assert!(errors.contains(&PcsmHandoffIntakeError::PcsmJournalMissing));
    }

    #[test]
    fn pcsm_bounded_handoff_binds_full_intake_digest_and_rejects_reserved_collision() {
        let intake = valid_pcsm_intake();
        let candidate =
            pcsm_bounded_proof_handoff_candidate("pcsm-bound", subject("pcsm"), &intake)
                .expect("valid intake maps");
        assert_eq!(
            candidate
                .source_artifact_digests
                .iter()
                .find(|digest| digest.id == PCSM_BOUNDED_PROOF_INTAKE_DIGEST_ID),
            Some(&ArtifactDigest {
                id: PCSM_BOUNDED_PROOF_INTAKE_DIGEST_ID.to_owned(),
                sha256: intake.digest(),
            })
        );

        let mut changed = intake.clone();
        changed.source_repo_commit = "fedcba9876543210fedcba9876543210fedcba98".to_owned();
        let changed_candidate =
            pcsm_bounded_proof_handoff_candidate("pcsm-bound", subject("pcsm"), &changed)
                .expect("changed valid intake maps");
        assert_ne!(candidate.digest(), changed_candidate.digest());

        let mut collision = intake;
        collision.source_artifact_digests.insert(ArtifactDigest {
            id: PCSM_BOUNDED_PROOF_INTAKE_DIGEST_ID.to_owned(),
            sha256: Hash([44; 32]),
        });
        assert!(validate_pcsm_bounded_proof_handoff_intake(&collision)
            .contains(&PcsmHandoffIntakeError::ReservedIntakeDigestCollision));
    }

    #[test]
    fn journal_rejects_forged_decisions_and_snapshot_drift() {
        let mut rejected_candidate = accepted_candidate();
        rejected_candidate.provider_direct_authority_requested = true;
        let admission_policy = policy();
        let expected_rejected = evaluate_admission(&rejected_candidate, &admission_policy);
        assert_eq!(expected_rejected.verdict, AdmissionVerdict::Rejected);

        let mut forged_accepted = expected_rejected.clone();
        forged_accepted.verdict = AdmissionVerdict::Accepted;
        forged_accepted.reasons.clear();
        forged_accepted.accepted_envelope = rejected_candidate.proposed_envelope.clone();
        assert_eq!(
            AgentAdmissionJournal::default().append_decision(
                &rejected_candidate,
                &admission_policy,
                forged_accepted,
            ),
            Err(JournalError::DecisionEvaluationMismatch)
        );

        let accepted = accepted_candidate();
        let expected_accepted = evaluate_admission(&accepted, &admission_policy);
        let mut forged_rejected = expected_accepted.clone();
        forged_rejected.verdict = AdmissionVerdict::Rejected;
        forged_rejected.reasons = vec![reason("forged_rejection")];
        forged_rejected.accepted_envelope = None;
        assert_eq!(
            AgentAdmissionJournal::default().append_decision(
                &accepted,
                &admission_policy,
                forged_rejected,
            ),
            Err(JournalError::DecisionEvaluationMismatch)
        );

        let mut journal = AgentAdmissionJournal::default();
        journal
            .append_decision(&accepted, &admission_policy, expected_accepted)
            .expect("valid decision appends");

        let mut candidate_drift = journal.clone();
        candidate_drift.entries[0].candidate.id =
            AdmissionCandidateId("candidate-drift".to_owned());
        assert!(candidate_drift
            .validate()
            .contains(&JournalError::CandidateSnapshotMismatch));

        let mut policy_drift = journal.clone();
        policy_drift.entries[0].policy.max_claim_boundary = AdmissionClaimBoundary::LocalOnly;
        assert!(policy_drift
            .validate()
            .contains(&JournalError::DecisionEvaluationMismatch));

        let mut policy_id_drift = journal.clone();
        policy_id_drift.entries[0].policy.id = AdmissionPolicyId("policy-drift".to_owned());
        assert!(policy_id_drift
            .validate()
            .contains(&JournalError::PolicySnapshotMismatch));

        let mut source_drift = journal;
        source_drift.entries[0].source_artifact_digests.clear();
        assert!(source_drift
            .validate()
            .contains(&JournalError::SourceArtifactSnapshotMismatch));
    }

    #[test]
    fn admission_journal_bundle_materializes_declared_files_and_sidecars() {
        let output_root = temp_output_root("bundle");
        let journal = two_entry_journal();
        let request = materialization_request("bundle-1", &output_root);

        let manifest = materialize_admission_journal_bundle(&output_root, &journal, &request)
            .expect("valid journal materializes");

        assert_eq!(manifest.bundle_id, "bundle-1");
        assert_eq!(manifest.entry_count, 2);
        assert_eq!(manifest.accepted_count, 1);
        assert_eq!(manifest.rejected_count, 1);
        assert_eq!(manifest.quarantined_count, 0);
        assert_eq!(
            manifest.journal_tip_digest_after,
            journal
                .entries
                .last()
                .map(AgentAdmissionJournalEntry::digest)
        );
        assert!(manifest
            .declared_files
            .contains(&"admission-journal/manifest.json".to_owned()));
        assert!(!manifest
            .declared_file_digests
            .contains_key("admission-journal/manifest.json"));

        for logical_path in ADMISSION_JOURNAL_DECLARED_FILES {
            let path = output_root.join(logical_path);
            assert!(path.is_file(), "{logical_path} should exist");
            assert!(
                sidecar_path(&path).is_file(),
                "{logical_path} sidecar should exist"
            );
        }

        let decisions = fs::read_to_string(output_root.join("admission-journal/decisions.jsonl"))
            .expect("decisions index is readable");
        assert!(decisions.contains("\"accepted_envelope_exists\":true"));
        assert!(decisions.contains("\"accepted_envelope_exists\":false"));

        let redaction: AdmissionJournalRedactionReport = serde_json::from_slice(
            &fs::read(output_root.join("admission-journal/redaction-report.json"))
                .expect("redaction report is readable"),
        )
        .expect("redaction report parses");
        assert!(!redaction.retains_credentials_or_secrets);
        assert!(!redaction.retains_raw_provider_responses);

        let readback = read_admission_journal_bundle(&output_root).expect("readback validates");
        assert_eq!(readback, manifest);

        fs::remove_dir_all(&output_root).expect("temp bundle cleanup succeeds");
    }

    #[test]
    fn admission_journal_bundle_rejects_missing_nonclaim_stale_tip_and_invalid_journal() {
        let output_root = temp_output_root("rejects");
        let journal = two_entry_journal();
        let mut request = materialization_request("bundle-2", &output_root);
        request
            .nonclaims
            .remove(&NonClaimLabel("not proof".to_owned()));
        assert_eq!(
            materialize_admission_journal_bundle(&output_root, &journal, &request),
            Err(
                AdmissionJournalMaterializationError::MissingRequiredNonclaim(
                    "not proof".to_owned()
                )
            )
        );

        let mut stale = materialization_request("bundle-3", &output_root);
        stale.journal_tip_digest_before = Some(Hash([4; 32]));
        assert_eq!(
            materialize_admission_journal_bundle(&output_root, &journal, &stale),
            Err(AdmissionJournalMaterializationError::StaleJournalTip)
        );

        let mut invalid = journal.clone();
        invalid.entries[0].sequence_number = 99;
        assert!(matches!(
            materialize_admission_journal_bundle(
                &output_root,
                &invalid,
                &materialization_request("bundle-4", &output_root),
            ),
            Err(AdmissionJournalMaterializationError::InvalidJournal(_))
        ));
    }

    #[test]
    fn admission_journal_bundle_rejects_protected_roots_and_undeclared_files() {
        let output_root = temp_output_root("protected");
        let protected = output_root
            .parent()
            .expect("temp output root has a parent")
            .to_path_buf();
        let journal = two_entry_journal();
        let mut request = materialization_request("bundle-5", &output_root);
        request.protected_roots = vec![protected];

        assert_eq!(
            materialize_admission_journal_bundle(&output_root, &journal, &request),
            Err(AdmissionJournalMaterializationError::ProtectedOutputRoot)
        );

        let request = materialization_request("bundle-6", &output_root);
        materialize_admission_journal_bundle(&output_root, &journal, &request)
            .expect("valid bundle materializes");
        fs::write(
            output_root.join("admission-journal/unexpected.txt"),
            b"unexpected",
        )
        .expect("unexpected file can be inserted for negative test");
        assert_eq!(
            read_admission_journal_bundle(&output_root),
            Err(AdmissionJournalMaterializationError::UndeclaredFile(
                "admission-journal/unexpected.txt".to_owned()
            ))
        );

        fs::remove_dir_all(&output_root).expect("temp bundle cleanup succeeds");
    }

    #[test]
    fn admission_journal_semantic_readback_rejects_digest_consistent_drift() {
        let journal = two_entry_journal();

        let manifest_root = temp_output_root("semantic-manifest");
        materialize_admission_journal_bundle(
            &manifest_root,
            &journal,
            &materialization_request("semantic-manifest", &manifest_root),
        )
        .expect("manifest test bundle materializes");
        let manifest_path = manifest_root.join("admission-journal/manifest.json");
        let mut manifest: AdmissionJournalBundleManifest =
            serde_json::from_slice(&fs::read(&manifest_path).expect("manifest reads"))
                .expect("manifest parses");
        manifest.accepted_count = 99;
        rewrite_bundle_file(
            &manifest_root,
            "admission-journal/manifest.json",
            &serde_json::to_vec_pretty(&manifest).expect("manifest serializes"),
        );
        assert_eq!(
            read_admission_journal_bundle(&manifest_root),
            Err(AdmissionJournalMaterializationError::ManifestSemanticMismatch)
        );
        fs::remove_dir_all(&manifest_root).expect("manifest test cleanup succeeds");

        let journal_root = temp_output_root("semantic-journal");
        materialize_admission_journal_bundle(
            &journal_root,
            &journal,
            &materialization_request("semantic-journal", &journal_root),
        )
        .expect("journal test bundle materializes");
        let mut serialized_journal: AgentAdmissionJournal = serde_json::from_slice(
            &fs::read(journal_root.join("admission-journal/journal.json")).expect("journal reads"),
        )
        .expect("journal parses");
        serialized_journal.entries[0].sequence_number = 9;
        rewrite_content_and_manifest_digest(
            &journal_root,
            "admission-journal/journal.json",
            &serde_json::to_vec_pretty(&serialized_journal).expect("journal serializes"),
        );
        assert!(matches!(
            read_admission_journal_bundle(&journal_root),
            Err(AdmissionJournalMaterializationError::InvalidSerializedJournal(_))
        ));
        fs::remove_dir_all(&journal_root).expect("journal test cleanup succeeds");

        let decisions_root = temp_output_root("semantic-decisions");
        materialize_admission_journal_bundle(
            &decisions_root,
            &journal,
            &materialization_request("semantic-decisions", &decisions_root),
        )
        .expect("decisions test bundle materializes");
        let mut decisions =
            fs::read_to_string(decisions_root.join("admission-journal/decisions.jsonl"))
                .expect("decisions read");
        decisions = decisions.replacen(
            "\"accepted_envelope_exists\":true",
            "\"accepted_envelope_exists\":false",
            1,
        );
        rewrite_content_and_manifest_digest(
            &decisions_root,
            "admission-journal/decisions.jsonl",
            decisions.as_bytes(),
        );
        assert_eq!(
            read_admission_journal_bundle(&decisions_root),
            Err(AdmissionJournalMaterializationError::DecisionIndexMismatch)
        );
        fs::remove_dir_all(&decisions_root).expect("decisions test cleanup succeeds");
    }

    #[test]
    fn admission_journal_semantic_readback_rejects_policy_file_drift() {
        let journal = two_entry_journal();

        let source_root = temp_output_root("semantic-source");
        materialize_admission_journal_bundle(
            &source_root,
            &journal,
            &materialization_request("semantic-source", &source_root),
        )
        .expect("source test bundle materializes");
        let empty_source = serde_json::to_vec_pretty(&AdmissionSourceDigestIndex {
            source_artifact_digests: BTreeSet::new(),
        })
        .expect("source index serializes");
        rewrite_content_and_manifest_digest(
            &source_root,
            "admission-journal/source-digests.json",
            &empty_source,
        );
        assert_eq!(
            read_admission_journal_bundle(&source_root),
            Err(AdmissionJournalMaterializationError::SourceDigestIndexMismatch)
        );
        fs::remove_dir_all(&source_root).expect("source test cleanup succeeds");

        let nonclaim_root = temp_output_root("semantic-nonclaim");
        materialize_admission_journal_bundle(
            &nonclaim_root,
            &journal,
            &materialization_request("semantic-nonclaim", &nonclaim_root),
        )
        .expect("nonclaim test bundle materializes");
        rewrite_content_and_manifest_digest(
            &nonclaim_root,
            "admission-journal/non-claims.md",
            b"# Admission Journal Non-Claims\n\n- not proof\n",
        );
        assert_eq!(
            read_admission_journal_bundle(&nonclaim_root),
            Err(AdmissionJournalMaterializationError::NonclaimMismatch)
        );
        fs::remove_dir_all(&nonclaim_root).expect("nonclaim test cleanup succeeds");

        let redaction_root = temp_output_root("semantic-redaction");
        materialize_admission_journal_bundle(
            &redaction_root,
            &journal,
            &materialization_request("semantic-redaction", &redaction_root),
        )
        .expect("redaction test bundle materializes");
        let mut redaction = redaction_report();
        redaction.retains_credentials_or_secrets = true;
        rewrite_content_and_manifest_digest(
            &redaction_root,
            "admission-journal/redaction-report.json",
            &serde_json::to_vec_pretty(&redaction).expect("redaction serializes"),
        );
        assert_eq!(
            read_admission_journal_bundle(&redaction_root),
            Err(AdmissionJournalMaterializationError::UnsafeRedactionReport)
        );
        fs::remove_dir_all(&redaction_root).expect("redaction test cleanup succeeds");

        let validation_root = temp_output_root("semantic-validation");
        materialize_admission_journal_bundle(
            &validation_root,
            &journal,
            &materialization_request("semantic-validation", &validation_root),
        )
        .expect("validation test bundle materializes");
        let mut validation: AdmissionJournalValidationReport = serde_json::from_slice(
            &fs::read(validation_root.join("admission-journal/validation-report.json"))
                .expect("validation report reads"),
        )
        .expect("validation report parses");
        validation.valid = false;
        rewrite_content_and_manifest_digest(
            &validation_root,
            "admission-journal/validation-report.json",
            &serde_json::to_vec_pretty(&validation).expect("validation report serializes"),
        );
        assert_eq!(
            read_admission_journal_bundle(&validation_root),
            Err(AdmissionJournalMaterializationError::ValidationReportMismatch)
        );
        fs::remove_dir_all(&validation_root).expect("validation test cleanup succeeds");
    }

    #[test]
    fn pcsm_intake_round_trips_through_semantic_bundle_readback() {
        let intake = valid_pcsm_intake();
        let candidate =
            pcsm_bounded_proof_handoff_candidate("pcsm-semantic", subject("pcsm"), &intake)
                .expect("valid PCSM intake maps to local candidate");
        let pcsm_policy =
            AgentAdmissionPolicy::local_default(pcsm_bounded_proof_required_nonclaims());
        let decision = evaluate_admission(&candidate, &pcsm_policy);
        assert_eq!(decision.verdict, AdmissionVerdict::Accepted);
        assert!(decision.accepted_envelope.is_none());

        let mut journal = AgentAdmissionJournal::default();
        journal
            .append_decision(&candidate, &pcsm_policy, decision)
            .expect("PCSM decision appends");
        let output_root = temp_output_root("pcsm-semantic-roundtrip");
        let mut request = materialization_request("pcsm-semantic-roundtrip", &output_root);
        request.admission_policy_id = pcsm_policy.id;
        let manifest = materialize_admission_journal_bundle(&output_root, &journal, &request)
            .expect("PCSM journal materializes and validates semantically");
        assert_eq!(
            read_admission_journal_bundle(&output_root).expect("semantic readback succeeds"),
            manifest
        );
        assert_eq!(manifest.entry_count, 1);
        assert_eq!(manifest.accepted_count, 1);
        fs::remove_dir_all(&output_root).expect("PCSM roundtrip cleanup succeeds");
    }

    #[cfg(unix)]
    #[test]
    fn admission_journal_semantic_readback_rejects_sidecar_symlink() {
        use std::os::unix::fs::symlink;

        let output_root = temp_output_root("semantic-sidecar-symlink");
        let journal = two_entry_journal();
        materialize_admission_journal_bundle(
            &output_root,
            &journal,
            &materialization_request("semantic-sidecar-symlink", &output_root),
        )
        .expect("sidecar test bundle materializes");
        let journal_path = output_root.join("admission-journal/journal.json");
        let sidecar = sidecar_path(&journal_path);
        fs::remove_file(&sidecar).expect("sidecar removal succeeds");
        symlink(
            output_root.join("admission-journal/manifest.json.sha256"),
            &sidecar,
        )
        .expect("sidecar symlink creation succeeds");

        assert_eq!(
            read_admission_journal_bundle(&output_root),
            Err(AdmissionJournalMaterializationError::SidecarIsSymlink(
                "admission-journal/journal.json.sha256".to_owned()
            ))
        );
        fs::remove_dir_all(&output_root).expect("sidecar test cleanup succeeds");
    }

    #[test]
    fn admission_journal_readback_rejects_missing_partial_and_digest_drift() {
        let (missing_primary_root, _) = materialized_test_bundle("missing-primary");
        fs::remove_file(missing_primary_root.join("admission-journal/journal.json"))
            .expect("primary file removal succeeds");
        assert!(matches!(
            read_admission_journal_bundle(&missing_primary_root),
            Err(AdmissionJournalMaterializationError::Io(message))
                if message.contains("declared file missing")
        ));
        fs::remove_dir_all(&missing_primary_root).expect("missing primary cleanup succeeds");

        let (missing_sidecar_root, _) = materialized_test_bundle("missing-sidecar");
        fs::remove_file(missing_sidecar_root.join("admission-journal/journal.json.sha256"))
            .expect("sidecar removal succeeds");
        assert!(matches!(
            read_admission_journal_bundle(&missing_sidecar_root),
            Err(AdmissionJournalMaterializationError::Io(message))
                if message.contains("declared file missing")
        ));
        fs::remove_dir_all(&missing_sidecar_root).expect("missing sidecar cleanup succeeds");

        let (digest_root, _) = materialized_test_bundle("digest-drift");
        fs::write(
            digest_root.join("admission-journal/journal.json"),
            b"digest drift",
        )
        .expect("digest drift writes");
        assert_eq!(
            read_admission_journal_bundle(&digest_root),
            Err(AdmissionJournalMaterializationError::DigestMismatch(
                "admission-journal/journal.json".to_owned()
            ))
        );
        fs::remove_dir_all(&digest_root).expect("digest drift cleanup succeeds");

        let (nested_root, _) = materialized_test_bundle("nested-undeclared");
        fs::create_dir(nested_root.join("admission-journal/unexpected"))
            .expect("undeclared directory creation succeeds");
        assert_eq!(
            read_admission_journal_bundle(&nested_root),
            Err(AdmissionJournalMaterializationError::UndeclaredFile(
                "admission-journal/unexpected".to_owned()
            ))
        );
        fs::remove_dir_all(&nested_root).expect("nested directory cleanup succeeds");
    }

    #[test]
    fn admission_journal_readback_rejects_malformed_declared_json() {
        for logical_path in [
            "admission-journal/manifest.json",
            "admission-journal/journal.json",
            "admission-journal/source-digests.json",
            "admission-journal/redaction-report.json",
            "admission-journal/validation-report.json",
        ] {
            assert_malformed_declared_json(logical_path);
        }
    }

    #[test]
    fn admission_journal_readback_rejects_decision_index_shape_drift() {
        for (name, mutate) in [
            ("missing-newline", "remove-final-newline"),
            ("blank-row", "insert-blank-row"),
            ("malformed-row", "malformed-row"),
            ("duplicate-row", "duplicate-row"),
            ("omitted-row", "omit-row"),
            ("reordered-row", "reorder-row"),
        ] {
            let (output_root, _) = materialized_test_bundle(name);
            let original =
                fs::read_to_string(output_root.join("admission-journal/decisions.jsonl"))
                    .expect("decision rows read");
            let rows: Vec<&str> = original.lines().collect();
            let changed = match mutate {
                "remove-final-newline" => original.trim_end_matches('\n').to_owned(),
                "insert-blank-row" => format!("{}\n\n{}\n", rows[0], rows[1]),
                "malformed-row" => format!("{{\n{}\n", rows[1]),
                "duplicate-row" => format!("{}\n{}\n{}\n", rows[0], rows[0], rows[1]),
                "omit-row" => format!("{}\n", rows[0]),
                "reorder-row" => format!("{}\n{}\n", rows[1], rows[0]),
                _ => unreachable!("known mutation"),
            };
            rewrite_content_and_manifest_digest(
                &output_root,
                "admission-journal/decisions.jsonl",
                changed.as_bytes(),
            );
            assert!(matches!(
                read_admission_journal_bundle(&output_root),
                Err(AdmissionJournalMaterializationError::DecisionIndexMismatch)
                    | Err(AdmissionJournalMaterializationError::MalformedDeclaredFile(
                        _
                    ))
            ));
            fs::remove_dir_all(&output_root).expect("decision mutation cleanup succeeds");
        }
    }

    #[test]
    fn admission_journal_readback_rejects_manifest_contract_drift() {
        for drift in [
            "schema",
            "bundle-id",
            "declared-order",
            "digest-map",
            "claim-boundary",
            "policy",
            "tip",
        ] {
            let (output_root, _) = materialized_test_bundle(&format!("manifest-{drift}"));
            let manifest_path = output_root.join("admission-journal/manifest.json");
            let mut manifest: AdmissionJournalBundleManifest =
                serde_json::from_slice(&fs::read(&manifest_path).expect("manifest reads"))
                    .expect("manifest parses");
            match drift {
                "schema" => manifest.schema_version = "unknown".to_owned(),
                "bundle-id" => manifest.bundle_id = "../unsafe".to_owned(),
                "declared-order" => manifest.declared_files.swap(0, 1),
                "digest-map" => {
                    manifest
                        .declared_file_digests
                        .remove("admission-journal/journal.json");
                }
                "claim-boundary" => manifest.claim_boundary = "accepted evidence".to_owned(),
                "policy" => {
                    manifest.admission_policy_id = AdmissionPolicyId("other-policy".to_owned())
                }
                "tip" => manifest.journal_tip_digest_after = Some(Hash([42; 32])),
                _ => unreachable!("known drift"),
            }
            rewrite_bundle_file(
                &output_root,
                "admission-journal/manifest.json",
                &serde_json::to_vec_pretty(&manifest).expect("manifest serializes"),
            );
            assert_eq!(
                read_admission_journal_bundle(&output_root),
                Err(AdmissionJournalMaterializationError::ManifestSemanticMismatch)
            );
            fs::remove_dir_all(&output_root).expect("manifest drift cleanup succeeds");
        }
    }

    #[test]
    fn admission_journal_materialization_rejects_unsafe_roots_and_allows_overwrite() {
        let journal = two_entry_journal();
        let empty_request = AdmissionJournalMaterializationRequest {
            bundle_id: "empty-root".to_owned(),
            created_at_unix: 1_800_000_000,
            admission_policy_id: policy().id,
            journal_tip_digest_before: None,
            nonclaims: admission_journal_required_nonclaims(),
            overwrite: false,
            protected_roots: Vec::new(),
        };
        assert_eq!(
            materialize_admission_journal_bundle(Path::new(""), &journal, &empty_request),
            Err(AdmissionJournalMaterializationError::EmptyOutputRoot)
        );

        let file_root = temp_output_root("file-root");
        fs::write(&file_root, b"file").expect("file root writes");
        assert_eq!(
            materialize_admission_journal_bundle(
                &file_root,
                &journal,
                &materialization_request("file-root", &file_root),
            ),
            Err(AdmissionJournalMaterializationError::OutputRootIsFile)
        );
        fs::remove_file(&file_root).expect("file root cleanup succeeds");

        let existing_root = temp_output_root("existing-root");
        let request = materialization_request("existing-root", &existing_root);
        materialize_admission_journal_bundle(&existing_root, &journal, &request)
            .expect("initial materialization succeeds");
        assert_eq!(
            materialize_admission_journal_bundle(&existing_root, &journal, &request),
            Err(AdmissionJournalMaterializationError::OutputRootExistsWithoutOverwrite)
        );
        let mut overwrite = request;
        overwrite.overwrite = true;
        assert_eq!(
            materialize_admission_journal_bundle(&existing_root, &journal, &overwrite)
                .expect("explicit overwrite succeeds")
                .entry_count,
            2
        );
        fs::remove_dir_all(&existing_root).expect("existing root cleanup succeeds");

        let ancestor_root = temp_output_root("ancestor-root");
        let protected_descendant = ancestor_root.join("protected");
        fs::create_dir_all(&protected_descendant).expect("protected descendant creates");
        let mut ancestor_request = materialization_request("ancestor-root", &ancestor_root);
        ancestor_request.overwrite = true;
        ancestor_request.protected_roots = vec![protected_descendant.clone()];
        assert_eq!(
            materialize_admission_journal_bundle(&ancestor_root, &journal, &ancestor_request),
            Err(AdmissionJournalMaterializationError::ProtectedOutputRoot)
        );
        assert!(protected_descendant.is_dir());
        fs::remove_dir_all(&ancestor_root).expect("ancestor root cleanup succeeds");

        let sibling_root = temp_output_root("sibling-root");
        let sibling_protected = sibling_root
            .parent()
            .expect("sibling root has parent")
            .join("sibling-protected");
        fs::create_dir_all(&sibling_protected).expect("sibling protected creates");
        let mut sibling_request = materialization_request("sibling-root", &sibling_root);
        sibling_request.protected_roots = vec![sibling_protected.clone()];
        assert_eq!(
            materialize_admission_journal_bundle(&sibling_root, &journal, &sibling_request)
                .expect("sibling output remains allowed")
                .entry_count,
            2
        );
        fs::remove_dir_all(&sibling_root).expect("sibling output cleanup succeeds");
        fs::remove_dir_all(&sibling_protected).expect("sibling protected cleanup succeeds");
    }

    #[test]
    fn semantic_readback_rejects_fully_rehashed_candidate_and_policy_snapshot_drift() {
        for drift in ["candidate", "policy", "source"] {
            let (output_root, _) = materialized_test_bundle(&format!("snapshot-{drift}"));
            let journal_path = output_root.join("admission-journal/journal.json");
            let mut journal: AgentAdmissionJournal =
                serde_json::from_slice(&fs::read(&journal_path).expect("journal reads"))
                    .expect("journal parses");
            match drift {
                "candidate" => {
                    journal.entries[0].candidate.id =
                        AdmissionCandidateId("snapshot-drift".to_owned());
                }
                "policy" => {
                    journal.entries[0].policy.max_claim_boundary =
                        AdmissionClaimBoundary::LocalOnly;
                }
                "source" => journal.entries[0].source_artifact_digests.clear(),
                _ => unreachable!("known drift"),
            }
            rewrite_content_and_manifest_digest(
                &output_root,
                "admission-journal/journal.json",
                &serde_json::to_vec_pretty(&journal).expect("journal serializes"),
            );
            assert!(matches!(
                read_admission_journal_bundle(&output_root),
                Err(AdmissionJournalMaterializationError::InvalidSerializedJournal(_))
            ));
            fs::remove_dir_all(&output_root).expect("snapshot drift cleanup succeeds");
        }
    }

    #[cfg(unix)]
    #[test]
    fn admission_journal_readback_rejects_primary_symlink_and_file_directories() {
        use std::os::unix::fs::symlink;

        let (symlink_root, _) = materialized_test_bundle("primary-symlink");
        let journal_path = symlink_root.join("admission-journal/journal.json");
        fs::remove_file(&journal_path).expect("journal removal succeeds");
        symlink(
            symlink_root.join("admission-journal/manifest.json"),
            &journal_path,
        )
        .expect("primary symlink creation succeeds");
        assert_eq!(
            read_admission_journal_bundle(&symlink_root),
            Err(AdmissionJournalMaterializationError::BundleFileIsSymlink(
                "admission-journal/journal.json".to_owned()
            ))
        );
        fs::remove_dir_all(&symlink_root).expect("primary symlink cleanup succeeds");

        let (directory_root, _) = materialized_test_bundle("primary-directory");
        let source_path = directory_root.join("admission-journal/source-digests.json");
        fs::remove_file(&source_path).expect("source index removal succeeds");
        fs::create_dir(&source_path).expect("source directory substitution succeeds");
        assert_eq!(
            read_admission_journal_bundle(&directory_root),
            Err(
                AdmissionJournalMaterializationError::DeclaredFileTypeMismatch(
                    "admission-journal/source-digests.json".to_owned()
                )
            )
        );
        fs::remove_dir_all(&directory_root).expect("primary directory cleanup succeeds");

        let symlink_output = temp_output_root("output-symlink");
        let target = temp_output_root("output-symlink-target");
        fs::create_dir(&target).expect("symlink target creation succeeds");
        symlink(&target, &symlink_output).expect("output symlink creation succeeds");
        assert_eq!(
            materialize_admission_journal_bundle(
                &symlink_output,
                &two_entry_journal(),
                &materialization_request("output-symlink", &symlink_output),
            ),
            Err(AdmissionJournalMaterializationError::OutputRootIsSymlink)
        );
        fs::remove_file(&symlink_output).expect("output symlink cleanup succeeds");
        fs::remove_dir_all(&target).expect("output symlink target cleanup succeeds");
    }

    #[test]
    fn non_accepted_decisions_never_expose_or_validate_retained_envelopes() {
        for verdict in [AdmissionVerdict::Rejected, AdmissionVerdict::Quarantined] {
            let candidate = accepted_candidate();
            let admission_policy = policy();
            let mut decision = evaluate_admission(&candidate, &admission_policy);
            decision.verdict = verdict;
            decision
                .reasons
                .push(reason("adversarial_non_accepted_envelope"));
            assert!(accepted_claim_envelope(&candidate, &admission_policy, &decision).is_none());

            let mut journal = AgentAdmissionJournal::default();
            let entry = AgentAdmissionJournalEntry {
                sequence_number: 0,
                previous_entry_digest: None,
                candidate_id: candidate.id.clone(),
                candidate_digest: candidate.digest(),
                decision_digest: decision.digest(),
                source_artifact_digests: candidate.source_artifact_digests.clone(),
                candidate: candidate.clone(),
                policy: admission_policy.clone(),
                decision,
            };
            journal.entries.push(entry);
            assert!(journal
                .validate()
                .contains(&JournalError::NonAcceptedVerdictRetainsEnvelope));
            assert_eq!(
                journal.append_decision(
                    &candidate,
                    &admission_policy,
                    evaluate_admission(&candidate, &admission_policy)
                ),
                Err(JournalError::InvalidExistingJournal)
            );

            let output_root = temp_output_root("invalid-retained-envelope");
            assert!(matches!(
                materialize_admission_journal_bundle(
                    &output_root,
                    &journal,
                    &materialization_request("invalid-retained-envelope", &output_root),
                ),
                Err(AdmissionJournalMaterializationError::InvalidJournal(errors))
                    if errors.contains(&JournalError::NonAcceptedVerdictRetainsEnvelope)
            ));
            assert!(!output_root.exists());
        }

        let candidate = accepted_candidate();
        let admission_policy = policy();
        let mut journal = AgentAdmissionJournal::default();
        journal
            .append_decision(
                &candidate,
                &admission_policy,
                evaluate_admission(&candidate, &admission_policy),
            )
            .expect("accepted decision appends");
        let output_root = temp_output_root("rehashed-retained-envelope");
        materialize_admission_journal_bundle(
            &output_root,
            &journal,
            &materialization_request("rehashed-retained-envelope", &output_root),
        )
        .expect("baseline bundle materializes");
        let mut tampered: AgentAdmissionJournal = serde_json::from_slice(
            &fs::read(output_root.join("admission-journal/journal.json")).expect("journal reads"),
        )
        .expect("journal parses");
        tampered.entries[0].decision.verdict = AdmissionVerdict::Rejected;
        tampered.entries[0]
            .decision
            .reasons
            .push(reason("adversarial_rehashed_rejection"));
        tampered.entries[0].decision_digest = tampered.entries[0].decision.digest();
        rewrite_content_and_manifest_digest(
            &output_root,
            "admission-journal/journal.json",
            &serde_json::to_vec_pretty(&tampered).expect("tampered journal serializes"),
        );
        assert!(matches!(
            read_admission_journal_bundle(&output_root),
            Err(AdmissionJournalMaterializationError::InvalidSerializedJournal(errors))
                if errors.contains(&JournalError::NonAcceptedVerdictRetainsEnvelope)
        ));
        fs::remove_dir_all(&output_root).expect("rehashed bundle cleanup succeeds");
    }

    #[test]
    fn admission_journal_readback_rejects_unknown_json_fields() {
        for (name, logical_path, field) in [
            (
                "unknown-manifest",
                "admission-journal/manifest.json",
                "raw_provider_response",
            ),
            (
                "unknown-journal",
                "admission-journal/journal.json",
                "raw_network_transcript",
            ),
            (
                "unknown-source",
                "admission-journal/source-digests.json",
                "raw_artifact",
            ),
            (
                "unknown-redaction",
                "admission-journal/redaction-report.json",
                "raw_secret",
            ),
            (
                "unknown-validation",
                "admission-journal/validation-report.json",
                "raw_response",
            ),
        ] {
            let (output_root, _) = materialized_test_bundle(name);
            let path = output_root.join(logical_path);
            let mut value: serde_json::Value =
                serde_json::from_slice(&fs::read(&path).expect("declared JSON reads"))
                    .expect("declared JSON parses");
            value
                .as_object_mut()
                .expect("top-level JSON is an object")
                .insert(field.to_owned(), serde_json::json!("retained"));
            let bytes = serde_json::to_vec_pretty(&value).expect("unknown-field JSON serializes");
            if logical_path == "admission-journal/manifest.json" {
                rewrite_bundle_file(&output_root, logical_path, &bytes);
            } else {
                rewrite_content_and_manifest_digest(&output_root, logical_path, &bytes);
            }
            assert_eq!(
                read_admission_journal_bundle(&output_root),
                Err(AdmissionJournalMaterializationError::MalformedDeclaredFile(
                    logical_path.to_owned()
                ))
            );
            fs::remove_dir_all(&output_root).expect("unknown-field cleanup succeeds");
        }

        let (decision_root, _) = materialized_test_bundle("unknown-decision-row");
        let decisions_path = decision_root.join("admission-journal/decisions.jsonl");
        let original = fs::read_to_string(&decisions_path).expect("decision rows read");
        let mut rows = Vec::new();
        for line in original.lines() {
            let mut row: serde_json::Value =
                serde_json::from_str(line).expect("decision row parses");
            row.as_object_mut().expect("decision row is object").insert(
                "raw_provider_response".to_owned(),
                serde_json::json!("retained"),
            );
            rows.push(serde_json::to_string(&row).expect("decision row serializes"));
        }
        let changed = format!("{}\n", rows.join("\n"));
        rewrite_content_and_manifest_digest(
            &decision_root,
            "admission-journal/decisions.jsonl",
            changed.as_bytes(),
        );
        assert_eq!(
            read_admission_journal_bundle(&decision_root),
            Err(AdmissionJournalMaterializationError::MalformedDeclaredFile(
                "admission-journal/decisions.jsonl".to_owned()
            ))
        );
        fs::remove_dir_all(&decision_root).expect("unknown decision cleanup succeeds");

        let (nested_root, _) = materialized_test_bundle("unknown-nested-decision");
        let journal_path = nested_root.join("admission-journal/journal.json");
        let mut journal_value: serde_json::Value =
            serde_json::from_slice(&fs::read(&journal_path).expect("journal reads"))
                .expect("journal parses");
        journal_value["entries"][0]["decision"]
            .as_object_mut()
            .expect("nested decision is object")
            .insert(
                "raw_provider_response".to_owned(),
                serde_json::json!("retained"),
            );
        rewrite_content_and_manifest_digest(
            &nested_root,
            "admission-journal/journal.json",
            &serde_json::to_vec_pretty(&journal_value).expect("journal serializes"),
        );
        assert_eq!(
            read_admission_journal_bundle(&nested_root),
            Err(AdmissionJournalMaterializationError::MalformedDeclaredFile(
                "admission-journal/journal.json".to_owned()
            ))
        );
        fs::remove_dir_all(&nested_root).expect("unknown nested cleanup succeeds");

        let (entry_root, _) = materialized_test_bundle("unknown-journal-entry");
        let mut entry_value: serde_json::Value = serde_json::from_slice(
            &fs::read(entry_root.join("admission-journal/journal.json")).expect("journal reads"),
        )
        .expect("journal parses");
        entry_value["entries"][0]
            .as_object_mut()
            .expect("journal entry is object")
            .insert("raw_payload".to_owned(), serde_json::json!("retained"));
        rewrite_content_and_manifest_digest(
            &entry_root,
            "admission-journal/journal.json",
            &serde_json::to_vec_pretty(&entry_value).expect("journal serializes"),
        );
        assert_eq!(
            read_admission_journal_bundle(&entry_root),
            Err(AdmissionJournalMaterializationError::MalformedDeclaredFile(
                "admission-journal/journal.json".to_owned()
            ))
        );
        fs::remove_dir_all(&entry_root).expect("unknown entry cleanup succeeds");

        let (artifact_root, _) = materialized_test_bundle("unknown-source-artifact");
        let mut artifact_value: serde_json::Value = serde_json::from_slice(
            &fs::read(artifact_root.join("admission-journal/source-digests.json"))
                .expect("source index reads"),
        )
        .expect("source index parses");
        artifact_value["source_artifact_digests"][0]
            .as_object_mut()
            .expect("artifact digest is object")
            .insert("raw_artifact".to_owned(), serde_json::json!("retained"));
        rewrite_content_and_manifest_digest(
            &artifact_root,
            "admission-journal/source-digests.json",
            &serde_json::to_vec_pretty(&artifact_value).expect("source index serializes"),
        );
        assert_eq!(
            read_admission_journal_bundle(&artifact_root),
            Err(AdmissionJournalMaterializationError::MalformedDeclaredFile(
                "admission-journal/source-digests.json".to_owned()
            ))
        );
        fs::remove_dir_all(&artifact_root).expect("unknown artifact cleanup succeeds");
    }

    fn inject_duplicate_key_after_open_brace(bytes: &[u8], key: &str, value: &str) -> Vec<u8> {
        assert_eq!(bytes.first(), Some(&b'{'));
        let mut out = Vec::with_capacity(bytes.len() + key.len() + value.len() + 8);
        out.push(b'{');
        out.extend_from_slice(format!(r#""{key}":"{value}","#).as_bytes());
        out.extend_from_slice(&bytes[1..]);
        out
    }

    fn inject_duplicate_key_in_nested_object(
        bytes: &[u8],
        parent_key: &str,
        dup_key: &str,
        dup_value: &str,
    ) -> Vec<u8> {
        let text = std::str::from_utf8(bytes).expect("declared JSON is UTF-8");
        let parent_needle = format!("\"{parent_key}\":");
        let parent_pos = text.find(&parent_needle).expect("parent key present");
        let brace_pos = text[parent_pos..]
            .find('{')
            .map(|offset| parent_pos + offset)
            .expect("parent object brace");
        let mut out = String::with_capacity(text.len() + dup_key.len() + dup_value.len() + 16);
        out.push_str(&text[..=brace_pos]);
        out.push_str(&format!(r#""{dup_key}":"{dup_value}","#));
        out.push_str(&text[brace_pos + 1..]);
        out.into_bytes()
    }

    fn inject_duplicate_top_level_key(bytes: &[u8], key: &str, value: &str) -> Vec<u8> {
        let text = std::str::from_utf8(bytes).expect("declared JSON is UTF-8");
        let needle = format!("\"{key}\":");
        let pos = text.find(&needle).expect("top-level key present");
        let mut out = String::with_capacity(text.len() + key.len() + value.len() + 8);
        out.push_str(&text[..pos]);
        out.push_str(&format!(r#""{key}":"{value}","#));
        out.push_str(&text[pos..]);
        out.into_bytes()
    }

    fn inject_duplicate_key_in_first_array_object(
        bytes: &[u8],
        array_key: &str,
        dup_key: &str,
        dup_value: &str,
    ) -> Vec<u8> {
        let text = std::str::from_utf8(bytes).expect("declared JSON is UTF-8");
        let array_needle = format!("\"{array_key}\":");
        let array_pos = text.find(&array_needle).expect("array key present");
        let brace_pos = text[array_pos..]
            .find('{')
            .map(|offset| array_pos + offset)
            .expect("first array object brace");
        let mut out = String::with_capacity(text.len() + dup_key.len() + dup_value.len() + 16);
        out.push_str(&text[..=brace_pos]);
        out.push_str(&format!(r#""{dup_key}":"{dup_value}","#));
        out.push_str(&text[brace_pos + 1..]);
        out.into_bytes()
    }

    fn assert_duplicate_key_rejected_on_root(
        output_root: &Path,
        logical_path: &str,
        tampered_bytes: Vec<u8>,
    ) {
        if logical_path == "admission-journal/manifest.json" {
            rewrite_bundle_file(output_root, logical_path, &tampered_bytes);
        } else {
            rewrite_content_and_manifest_digest(output_root, logical_path, &tampered_bytes);
        }
        assert_eq!(
            read_admission_journal_bundle(output_root),
            Err(AdmissionJournalMaterializationError::MalformedDeclaredFile(
                logical_path.to_owned()
            ))
        );
    }

    #[test]
    fn duplicate_json_parser_allows_same_key_in_separate_scopes() {
        let bytes = br#"{"outer":{"name":"a"},"inner":{"name":"b"}}"#;
        let value =
            parse_json_value_rejecting_duplicate_keys(bytes).expect("separate scopes parse");
        assert_eq!(value["outer"]["name"], "a");
        assert_eq!(value["inner"]["name"], "b");
    }

    #[test]
    fn duplicate_json_parser_rejects_trailing_data() {
        assert!(parse_json_value_rejecting_duplicate_keys(br#"{"valid":true} trailing"#).is_err());
    }

    #[test]
    fn duplicate_json_parser_preserves_valid_unicode_strings() {
        let mut bytes = br#"{"raw":"Sacred AI "#.to_vec();
        bytes.extend_from_slice(&[0xF0, 0x9F, 0x94, 0x92]);
        bytes.extend_from_slice(br#"","escaped":"\uD83D\uDD12","accent":"caf\u00e9"}"#);
        let value =
            parse_json_value_rejecting_duplicate_keys(&bytes).expect("unicode JSON strings parse");
        assert_eq!(value["raw"], "Sacred AI \u{1f512}");
        assert_eq!(value["escaped"], "\u{1f512}");
        assert_eq!(value["accent"], "caf\u{e9}");
    }

    #[test]
    fn duplicate_json_parser_rejects_unicode_equivalent_duplicate_keys() {
        assert!(parse_json_value_rejecting_duplicate_keys(br#"{"name":1,"\u006eame":2}"#).is_err());
    }

    #[test]
    fn admission_journal_readback_rejects_duplicate_json_keys() {
        let (manifest_root, _) = materialized_test_bundle("dup-manifest-top");
        let manifest_bytes = fs::read(manifest_root.join("admission-journal/manifest.json"))
            .expect("manifest reads");
        assert_duplicate_key_rejected_on_root(
            &manifest_root,
            "admission-journal/manifest.json",
            inject_duplicate_key_after_open_brace(&manifest_bytes, "bundle_id", "dup"),
        );
        fs::remove_dir_all(&manifest_root).expect("dup manifest root cleanup succeeds");

        let (digest_root, _) = materialized_test_bundle("dup-manifest-digest");
        let digest_bytes =
            fs::read(digest_root.join("admission-journal/manifest.json")).expect("manifest reads");
        assert_duplicate_key_rejected_on_root(
            &digest_root,
            "admission-journal/manifest.json",
            inject_duplicate_key_in_nested_object(
                &digest_bytes,
                "declared_file_digests",
                "admission-journal/journal.json",
                "dup",
            ),
        );
        fs::remove_dir_all(&digest_root).expect("dup digest root cleanup succeeds");

        let (journal_root, _) = materialized_test_bundle("dup-journal-top");
        let journal_bytes =
            fs::read(journal_root.join("admission-journal/journal.json")).expect("journal reads");
        assert_duplicate_key_rejected_on_root(
            &journal_root,
            "admission-journal/journal.json",
            inject_duplicate_key_after_open_brace(&journal_bytes, "entries", "[]"),
        );
        fs::remove_dir_all(&journal_root).expect("dup journal root cleanup succeeds");

        let (candidate_root, _) = materialized_test_bundle("dup-journal-candidate");
        let candidate_bytes =
            fs::read(candidate_root.join("admission-journal/journal.json")).expect("journal reads");
        assert_duplicate_key_rejected_on_root(
            &candidate_root,
            "admission-journal/journal.json",
            inject_duplicate_key_in_nested_object(
                &candidate_bytes,
                "candidate",
                "id",
                "dup-candidate",
            ),
        );
        fs::remove_dir_all(&candidate_root).expect("dup candidate root cleanup succeeds");

        let (policy_root, _) = materialized_test_bundle("dup-journal-policy");
        let policy_bytes =
            fs::read(policy_root.join("admission-journal/journal.json")).expect("journal reads");
        assert_duplicate_key_rejected_on_root(
            &policy_root,
            "admission-journal/journal.json",
            inject_duplicate_key_in_nested_object(&policy_bytes, "policy", "id", "dup-policy"),
        );
        fs::remove_dir_all(&policy_root).expect("dup policy root cleanup succeeds");

        let (decision_root, _) = materialized_test_bundle("dup-journal-decision");
        let decision_bytes =
            fs::read(decision_root.join("admission-journal/journal.json")).expect("journal reads");
        assert_duplicate_key_rejected_on_root(
            &decision_root,
            "admission-journal/journal.json",
            inject_duplicate_key_in_nested_object(
                &decision_bytes,
                "decision",
                "policy_id",
                "dup-policy",
            ),
        );
        fs::remove_dir_all(&decision_root).expect("dup decision root cleanup succeeds");

        let (artifact_root, _) = materialized_test_bundle("dup-journal-artifact");
        let artifact_bytes =
            fs::read(artifact_root.join("admission-journal/journal.json")).expect("journal reads");
        assert_duplicate_key_rejected_on_root(
            &artifact_root,
            "admission-journal/journal.json",
            inject_duplicate_key_in_first_array_object(
                &artifact_bytes,
                "source_artifact_digests",
                "id",
                "dup-artifact",
            ),
        );
        fs::remove_dir_all(&artifact_root).expect("dup artifact root cleanup succeeds");

        let (row_root, _) = materialized_test_bundle("dup-decision-row");
        let decisions =
            fs::read(row_root.join("admission-journal/decisions.jsonl")).expect("decisions read");
        let first_line_end = decisions
            .iter()
            .position(|byte| *byte == b'\n')
            .expect("newline");
        let first_line = &decisions[..first_line_end];
        let tampered_line =
            inject_duplicate_key_after_open_brace(first_line, "candidate_id", "dup");
        let tampered = format!(
            "{}\n{}",
            std::str::from_utf8(&tampered_line).expect("utf8"),
            {
                let rest = &decisions[first_line_end + 1..];
                std::str::from_utf8(rest).expect("utf8")
            }
        );
        assert_duplicate_key_rejected_on_root(
            &row_root,
            "admission-journal/decisions.jsonl",
            tampered.into_bytes(),
        );
        fs::remove_dir_all(&row_root).expect("dup row root cleanup succeeds");

        let (source_root, _) = materialized_test_bundle("dup-source-index");
        let source_bytes = fs::read(source_root.join("admission-journal/source-digests.json"))
            .expect("source index reads");
        assert_duplicate_key_rejected_on_root(
            &source_root,
            "admission-journal/source-digests.json",
            inject_duplicate_key_after_open_brace(&source_bytes, "source_artifact_digests", "[]"),
        );
        fs::remove_dir_all(&source_root).expect("dup source root cleanup succeeds");

        let (source_artifact_root, _) = materialized_test_bundle("dup-source-artifact");
        let source_artifact_bytes =
            fs::read(source_artifact_root.join("admission-journal/source-digests.json"))
                .expect("source index reads");
        assert_duplicate_key_rejected_on_root(
            &source_artifact_root,
            "admission-journal/source-digests.json",
            inject_duplicate_key_in_first_array_object(
                &source_artifact_bytes,
                "source_artifact_digests",
                "id",
                "dup-artifact",
            ),
        );
        fs::remove_dir_all(&source_artifact_root)
            .expect("dup source artifact root cleanup succeeds");

        let (redaction_root, _) = materialized_test_bundle("dup-redaction");
        let redaction_bytes =
            fs::read(redaction_root.join("admission-journal/redaction-report.json"))
                .expect("redaction reads");
        assert_duplicate_key_rejected_on_root(
            &redaction_root,
            "admission-journal/redaction-report.json",
            inject_duplicate_key_after_open_brace(
                &redaction_bytes,
                "retains_credentials_or_secrets",
                "true",
            ),
        );
        fs::remove_dir_all(&redaction_root).expect("dup redaction root cleanup succeeds");

        let (validation_root, _) = materialized_test_bundle("dup-validation");
        let validation_bytes =
            fs::read(validation_root.join("admission-journal/validation-report.json"))
                .expect("validation reads");
        assert_duplicate_key_rejected_on_root(
            &validation_root,
            "admission-journal/validation-report.json",
            inject_duplicate_key_after_open_brace(&validation_bytes, "valid", "false"),
        );
        fs::remove_dir_all(&validation_root).expect("dup validation root cleanup succeeds");

        let (equal_root, _) = materialized_test_bundle("dup-equal-values");
        let equal_bytes = fs::read(equal_root.join("admission-journal/validation-report.json"))
            .expect("validation reads");
        assert_duplicate_key_rejected_on_root(
            &equal_root,
            "admission-journal/validation-report.json",
            inject_duplicate_top_level_key(&equal_bytes, "valid", "true"),
        );
        fs::remove_dir_all(&equal_root).expect("dup equal root cleanup succeeds");

        let (array_root, _) = materialized_test_bundle("dup-array-nested");
        let array_bytes =
            fs::read(array_root.join("admission-journal/journal.json")).expect("journal reads");
        let array_text = std::str::from_utf8(&array_bytes).expect("journal UTF-8");
        let entries_pos = array_text
            .find("\"entries\":")
            .expect("entries array present");
        let bracket_pos = array_text[entries_pos..]
            .find('[')
            .map(|offset| entries_pos + offset)
            .expect("entries array bracket");
        let tampered_array = format!(
            "{}{}",
            &array_text[..=bracket_pos],
            r#"{"dup_in_array":1,"dup_in_array":2},"#
        );
        let tampered_array = format!("{}{}", tampered_array, &array_text[bracket_pos + 1..]);
        assert_duplicate_key_rejected_on_root(
            &array_root,
            "admission-journal/journal.json",
            tampered_array.into_bytes(),
        );
        fs::remove_dir_all(&array_root).expect("dup array root cleanup succeeds");

        let (trailing_root, _) = materialized_test_bundle("dup-trailing");
        let trailing_bytes =
            fs::read(trailing_root.join("admission-journal/redaction-report.json"))
                .expect("redaction reads");
        let mut trailing = trailing_bytes;
        trailing.extend_from_slice(b" trailing");
        assert_duplicate_key_rejected_on_root(
            &trailing_root,
            "admission-journal/redaction-report.json",
            trailing,
        );
        fs::remove_dir_all(&trailing_root).expect("dup trailing root cleanup succeeds");

        let (digest_consistent_root, _) = materialized_test_bundle("dup-digest-consistent");
        let digest_consistent_bytes =
            fs::read(digest_consistent_root.join("admission-journal/validation-report.json"))
                .expect("validation reads");
        let tampered =
            inject_duplicate_key_after_open_brace(&digest_consistent_bytes, "valid", "true");
        rewrite_content_and_manifest_digest(
            &digest_consistent_root,
            "admission-journal/validation-report.json",
            &tampered,
        );
        assert_eq!(
            read_admission_journal_bundle(&digest_consistent_root),
            Err(AdmissionJournalMaterializationError::MalformedDeclaredFile(
                "admission-journal/validation-report.json".to_owned()
            ))
        );
        fs::remove_dir_all(&digest_consistent_root)
            .expect("dup digest consistent cleanup succeeds");
    }

    #[cfg(unix)]
    #[test]
    fn admission_journal_readback_rejects_root_and_bundle_directory_symlinks() {
        use std::os::unix::fs::symlink;

        let (target_root, _) = materialized_test_bundle("readback-root-target");
        let symlink_root = temp_output_root("readback-root-symlink");
        symlink(&target_root, &symlink_root).expect("root symlink creation succeeds");
        assert_eq!(
            read_admission_journal_bundle(&symlink_root),
            Err(AdmissionJournalMaterializationError::OutputRootIsSymlink)
        );
        fs::remove_file(&symlink_root).expect("root symlink cleanup succeeds");
        fs::remove_dir_all(&target_root).expect("root target cleanup succeeds");

        let (bundle_target_root, _) = materialized_test_bundle("bundle-dir-target");
        let bundle_symlink_root = temp_output_root("bundle-dir-symlink");
        fs::create_dir(&bundle_symlink_root).expect("bundle symlink root creation succeeds");
        symlink(
            bundle_target_root.join("admission-journal"),
            bundle_symlink_root.join("admission-journal"),
        )
        .expect("bundle directory symlink creation succeeds");
        assert_eq!(
            read_admission_journal_bundle(&bundle_symlink_root),
            Err(AdmissionJournalMaterializationError::BundleFileIsSymlink(
                "admission-journal".to_owned()
            ))
        );
        fs::remove_dir_all(&bundle_symlink_root).expect("bundle symlink cleanup succeeds");
        fs::remove_dir_all(&bundle_target_root).expect("bundle target cleanup succeeds");
    }
}
