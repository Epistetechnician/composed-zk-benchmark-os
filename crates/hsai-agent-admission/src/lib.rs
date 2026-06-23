use hsai_agent_case::AgentCase;
use hsai_claim_envelope::{ClaimEnvelope, Hash, SubjectId};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

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
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub enum AdmissionClaimBoundary {
    LocalOnly,
    Level1Local,
    Level2OrHigher,
    Formal,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AgentAdmissionCandidate {
    pub id: AdmissionCandidateId,
    pub subject: SubjectId,
    pub source_kind: AdmissionSourceKind,
    pub strict_typed: bool,
    pub case: Option<AgentCase>,
    pub proposed_envelope: Option<ClaimEnvelope>,
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
    ProviderDirectAuthorityClaimed,
    ProductionAuthorityClaimed,
    RawProviderPayloadsCommitted,
    LocalMlxSurrogateMissing,
    NativePcsmGovernanceMissing,
    PcsmJournalMissing,
    MissingVerifierStatus(&'static str),
    FailedVerifierStatus(String),
    MissingSourceArtifactDigest,
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

    for required in REQUIRED_PCSM_VERIFIERS {
        match intake
            .verifier_statuses
            .iter()
            .find(|status| status.name == *required)
        {
            Some(status) if status.outcome == PcsmVerifierOutcome::Pass => {}
            Some(status) => errors.push(PcsmHandoffIntakeError::FailedVerifierStatus(
                status.name.clone(),
            )),
            None => errors.push(PcsmHandoffIntakeError::MissingVerifierStatus(required)),
        }
    }

    if intake.source_artifact_digests.is_empty() {
        errors.push(PcsmHandoffIntakeError::MissingSourceArtifactDigest);
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

    Ok(AgentAdmissionCandidate {
        id: AdmissionCandidateId(id.into()),
        subject,
        source_kind: AdmissionSourceKind::PcsmBoundedProofHandoff,
        strict_typed: true,
        case: None,
        proposed_envelope: None,
        requested_claim_boundary: AdmissionClaimBoundary::LocalOnly,
        source_artifact_digests: intake.source_artifact_digests.clone(),
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

    pub fn accepted_envelope(&self) -> Option<&ClaimEnvelope> {
        self.accepted_envelope.as_ref()
    }
}

pub fn evaluate_admission(
    candidate: &AgentAdmissionCandidate,
    policy: &AgentAdmissionPolicy,
) -> AgentAdmissionDecision {
    let mut reasons = Vec::new();

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
    let accepted_envelope = if verdict == AdmissionVerdict::Accepted {
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

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct AgentAdmissionJournalEntry {
    pub sequence_number: u64,
    pub previous_entry_digest: Option<Hash>,
    pub candidate_id: AdmissionCandidateId,
    pub candidate_digest: Hash,
    pub decision_digest: Hash,
    pub source_artifact_digests: BTreeSet<ArtifactDigest>,
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

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub enum JournalError {
    CandidateMismatch,
    CandidateDigestMismatch,
    DecisionDigestMismatch,
    SequenceMismatch { expected: u64, actual: u64 },
    PreviousDigestMismatch,
    ReplayedCandidate(Hash),
    InvalidExistingJournal,
}

impl AgentAdmissionJournal {
    pub fn append_decision(
        &mut self,
        candidate: &AgentAdmissionCandidate,
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
            if entry.decision.candidate_digest != entry.candidate_digest {
                errors.push(JournalError::CandidateDigestMismatch);
            }
            if entry.decision.digest() != entry.decision_digest {
                errors.push(JournalError::DecisionDigestMismatch);
            }
            if !seen.insert(entry.candidate_digest) {
                errors.push(JournalError::ReplayedCandidate(entry.candidate_digest));
            }
            previous_digest = Some(entry.digest());
        }

        errors
    }
}

pub fn accepted_claim_envelope(decision: &AgentAdmissionDecision) -> Option<&ClaimEnvelope> {
    if decision.verdict == AdmissionVerdict::Accepted {
        decision.accepted_envelope.as_ref()
    } else {
        None
    }
}

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

    #[test]
    fn accepted_candidate_exports_envelope_and_appends_journal_entry() {
        let candidate = accepted_candidate();
        let decision = evaluate_admission(&candidate, &policy());

        assert_eq!(decision.verdict, AdmissionVerdict::Accepted);
        assert!(decision.reasons.is_empty());
        assert_eq!(
            accepted_claim_envelope(&decision),
            candidate.proposed_envelope.as_ref()
        );

        let mut journal = AgentAdmissionJournal::default();
        let entry = journal
            .append_decision(&candidate, decision)
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

        let decision = evaluate_admission(&candidate, &policy());
        assert_eq!(decision.verdict, AdmissionVerdict::Rejected);
        assert_eq!(
            decision.reasons,
            vec![AdmissionReason(
                "provider_direct_authority_forbidden".to_owned()
            )]
        );
        assert!(accepted_claim_envelope(&decision).is_none());

        let mut journal = AgentAdmissionJournal::default();
        let entry = journal
            .append_decision(&candidate, decision)
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
            vec![reason("strict_typed_candidate_required")]
        );
        assert!(decision.accepted_envelope.is_none());
    }

    #[test]
    fn journal_rejects_replay_and_detects_stale_tip() {
        let candidate = accepted_candidate();
        let decision = evaluate_admission(&candidate, &policy());
        let mut journal = AgentAdmissionJournal::default();
        journal
            .append_decision(&candidate, decision.clone())
            .expect("first append should work");

        assert_eq!(
            journal.append_decision(&candidate, decision),
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
        let decision = evaluate_admission(&candidate, &policy());
        let mut journal = AgentAdmissionJournal::default();
        journal
            .append_decision(&candidate, decision)
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
        assert_eq!(
            candidate.source_artifact_digests,
            intake.source_artifact_digests
        );

        let decision = evaluate_admission(
            &candidate,
            &AgentAdmissionPolicy::local_default(pcsm_bounded_proof_required_nonclaims()),
        );
        assert_eq!(decision.verdict, AdmissionVerdict::Accepted);
        assert!(accepted_claim_envelope(&decision).is_none());

        let mut journal = AgentAdmissionJournal::default();
        journal
            .append_decision(&candidate, decision)
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
}
