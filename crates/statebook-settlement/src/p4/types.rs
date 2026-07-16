use serde::{Deserialize, Serialize};
use statebook_core::SignedRational;
use std::collections::BTreeSet;

use crate::DigestV1;
use crate::{
    AssurancePropertyV1, AssuranceRootV1, AssuranceVerdictV1, DependencyDisclosureV1, RootClassV1,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DecisionOutcomeV1 {
    Rejected,
    Quarantined,
    Immediate,
    Queued,
    Frozen,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReleaseClassV1 {
    InternalRiskState,
    AtomicLinkedExchange,
    ExternalRiskReducingObligation,
    ExternalUnconditional,
    SystemicOrExceptional,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AssuranceTierV1 {
    Quarantined,
    UnprovenOrNovel,
    CurrentlyAssured,
    StrongCurrentAssuranceLowImpact,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum QueueStatusV1 {
    None,
    Queued,
    Challenged,
    EvidenceExpired,
    Frozen,
    Cancelled,
    RevalidationRequired,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TransferStatusV1 {
    Unreserved,
    Reserved,
    Submitted,
    SourceObserved,
    SourceFinalized,
    DestinationObserved,
    DestinationFinalized,
    Consumed,
    ProvenNoOutflow,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum BreakerStateV1 {
    Normal,
    Guarded,
    Challenged,
    Halted,
    Resolution,
    Recovery,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DirectionV1 {
    Outbound,
    Inbound,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FinancialBasisKindV1 {
    ContractDerived,
    SyntheticAccount,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DecisionReasonV1 {
    AmountZero,
    AmountNegative,
    AmountOverflow,
    AmountNoncanonical,
    AmountWrongSign,
    ReleaseClassUnknown,
    GateActionAuthorization,
    GateSourceAuthenticity,
    GateCalculationIntegrity,
    GateStateTransitionIntegrity,
    GateSolvencySupport,
    GateDestinationRoute,
    GateAnomalyEmergency,
    GateEvidenceIndependence,
    GateFinancialBasisBinding,
    GateReuseFinality,
    GateRiskReducingObligation,
    GateLinkedExchangePlan,
    ValuationStale,
    ValuationMissing,
    ValuationConflict,
    BudgetCasConflict,
    BudgetInsufficient,
    BreakerHalted,
    BreakerFrozen,
    BreakerInvalidTransition,
    BreakerResolutionRequired,
    BreakerRenewalRejected,
    QueueTimerOnly,
    ChallengeInvalid,
    ChallengeDuplicate,
    ChallengeCensored,
    ChallengeUnavailable,
    EvidenceExpired,
    PolicyRollback,
    RecoveryFailed,
    IntentDigestMismatch,
    ModelConfidenceIgnored,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DecisionMissingFactV1 {
    EvidenceObservation,
    ValuationObservation,
    AssuranceRoot,
    CompositionDigest,
    LinkedPlanLeg,
    ObligationExposure,
    BreakerScope,
    RecoveryPath,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DecisionNonclaimV1 {
    NoTransferCommand,
    NoSigningRequest,
    NoAuthority,
    NoValueMovement,
    NoTrustScore,
    NoReleaseSafetyProbability,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ClockV1 {
    now: i64,
}

impl ClockV1 {
    pub const fn new(now: i64) -> Self {
        Self { now }
    }

    pub const fn now(&self) -> i64 {
        self.now
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct ExactRationalV1 {
    pub(crate) numerator: String,
    pub(crate) denominator: String,
}

impl ExactRationalV1 {
    pub fn parse(
        numerator: &str,
        denominator: &str,
    ) -> Result<SignedRational, crate::SettlementParseErrorV1> {
        SignedRational::parse(numerator, denominator).map_err(|_| {
            crate::SettlementParseErrorV1::InvalidRational {
                numerator: numerator.to_owned(),
                denominator: denominator.to_owned(),
            }
        })
    }

    pub fn to_signed_rational(&self) -> Result<SignedRational, crate::SettlementParseErrorV1> {
        Self::parse(&self.numerator, &self.denominator)
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct FinancialBasisV1 {
    pub(crate) kind: FinancialBasisKindV1,
    pub(crate) state_key_digest: Option<DigestV1>,
    pub(crate) terms_digest: Option<DigestV1>,
    pub(crate) composition_digest: Option<DigestV1>,
    pub(crate) analysis_subject_digest: Option<DigestV1>,
}

impl FinancialBasisV1 {
    pub const fn kind(&self) -> FinancialBasisKindV1 {
        self.kind
    }

    pub const fn composition_digest(&self) -> Option<DigestV1> {
        self.composition_digest
    }

    pub const fn analysis_subject_digest(&self) -> Option<DigestV1> {
        self.analysis_subject_digest
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct LinkedPlanLegV1 {
    pub(crate) leg_id: String,
    pub(crate) direction: DirectionV1,
    pub(crate) asset: String,
    pub(crate) amount: SignedRational,
    pub(crate) budget_axis_id: String,
    pub(crate) assurance_tier: AssuranceTierV1,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct AtomicLinkedExchangePlanV1 {
    pub(crate) plan_id: String,
    pub(crate) leg_set_digest: DigestV1,
    pub(crate) primary_outbound_leg_id: String,
    pub(crate) legs: Vec<LinkedPlanLegV1>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ExternalRiskReducingObligationV1 {
    pub(crate) obligation_id: String,
    pub(crate) beneficiary: String,
    pub(crate) obligation_account: String,
    pub(crate) asset: String,
    pub(crate) exact_amount: SignedRational,
    pub(crate) deadline: i64,
    pub(crate) valid_until: i64,
    pub(crate) destination_use_restricted: bool,
    pub(crate) exposure_before_digest: DigestV1,
    pub(crate) exposure_after_digest: DigestV1,
    pub(crate) risk_reduction_ref: DigestV1,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ExternalizationRequestV1 {
    pub(crate) request_id: String,
    pub(crate) declared_release_class: ReleaseClassV1,
    pub(crate) subject: String,
    pub(crate) source_account: String,
    pub(crate) destination: String,
    pub(crate) route: String,
    pub(crate) asset: String,
    pub(crate) direction: DirectionV1,
    pub(crate) total_amount: SignedRational,
    pub(crate) financial_basis: FinancialBasisV1,
    pub(crate) originating_transition: String,
    pub(crate) nonce: String,
    pub(crate) requested_at: i64,
    pub(crate) expires_at: i64,
    pub(crate) action_authorization_digest: DigestV1,
    pub(crate) linked_plan: Option<AtomicLinkedExchangePlanV1>,
    pub(crate) obligation: Option<ExternalRiskReducingObligationV1>,
    pub(crate) reuse_finality_passed: bool,
    pub(crate) gate_overrides: GateOverridesV1,
    pub(crate) evidence_snapshot: EvidenceSnapshotV1,
    pub(crate) valuation_profile: ConservativeValuationProfileV1,
    pub(crate) settlement_policy: SettlementPolicyV1,
}

impl ExternalizationRequestV1 {
    pub fn request_id(&self) -> &str {
        &self.request_id
    }

    pub const fn declared_release_class(&self) -> ReleaseClassV1 {
        self.declared_release_class
    }

    pub const fn total_amount(&self) -> SignedRational {
        self.total_amount
    }

    pub const fn direction(&self) -> DirectionV1 {
        self.direction
    }

    pub fn asset(&self) -> &str {
        &self.asset
    }

    pub const fn financial_basis(&self) -> &FinancialBasisV1 {
        &self.financial_basis
    }

    pub const fn linked_plan(&self) -> Option<&AtomicLinkedExchangePlanV1> {
        self.linked_plan.as_ref()
    }

    pub const fn obligation(&self) -> Option<&ExternalRiskReducingObligationV1> {
        self.obligation.as_ref()
    }

    pub const fn reuse_finality_passed(&self) -> bool {
        self.reuse_finality_passed
    }

    pub const fn gate_overrides(&self) -> &GateOverridesV1 {
        &self.gate_overrides
    }

    pub const fn evidence_snapshot(&self) -> &EvidenceSnapshotV1 {
        &self.evidence_snapshot
    }

    pub const fn valuation_profile(&self) -> &ConservativeValuationProfileV1 {
        &self.valuation_profile
    }

    pub const fn settlement_policy(&self) -> &SettlementPolicyV1 {
        &self.settlement_policy
    }
}

#[derive(Clone, Debug, Default, Eq, PartialEq, Serialize)]
pub struct GateOverridesV1 {
    pub(crate) action_authorized: Option<bool>,
    pub(crate) source_authentic: Option<bool>,
    pub(crate) calculation_valid: Option<bool>,
    pub(crate) transition_valid: Option<bool>,
    pub(crate) solvency_supported: Option<bool>,
    pub(crate) destination_allowed: Option<bool>,
    pub(crate) anomaly_clear: Option<bool>,
    pub(crate) evidence_independent: Option<bool>,
    pub(crate) financial_basis_valid: Option<bool>,
    pub(crate) reuse_finality: Option<bool>,
    pub(crate) obligation_valid: Option<bool>,
    pub(crate) linked_plan_valid: Option<bool>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct EvidenceObservationV1 {
    pub(crate) property: AssurancePropertyV1,
    pub(crate) verdict: AssuranceVerdictV1,
    pub(crate) current_roots: Vec<AssuranceRootV1>,
    pub(crate) dependency_roots: Vec<AssuranceRootV1>,
    pub(crate) dependency_disclosure: DependencyDisclosureV1,
    pub(crate) observed_at: i64,
    pub(crate) expires_at: i64,
    pub(crate) bound_request_id: String,
    pub(crate) replayed: bool,
    pub(crate) equivocated: bool,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct EvidenceSnapshotV1 {
    pub(crate) snapshot_id: String,
    pub(crate) request_id: String,
    pub(crate) nonce: String,
    pub(crate) observations: Vec<EvidenceObservationV1>,
}

impl EvidenceSnapshotV1 {
    pub fn observations(&self) -> &[EvidenceObservationV1] {
        &self.observations
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize, Deserialize)]
pub struct ValuationObservationV1 {
    pub(crate) asset: String,
    pub(crate) rate: ExactRationalV1,
    pub(crate) observed_at: i64,
    pub(crate) root_id: String,
    pub(crate) root_class: RootClassV1,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ConservativeValuationProfileV1 {
    pub(crate) profile_id: String,
    pub(crate) numeraire_asset: String,
    pub(crate) max_age_seconds: i64,
    pub(crate) stress_multiplier: SignedRational,
    pub(crate) observations: Vec<ValuationObservationV1>,
    pub(crate) independence_roots: BTreeSet<String>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct TierFractionV1 {
    pub(crate) instant_fraction: SignedRational,
    pub(crate) delay_seconds: i64,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct AssuranceTierPolicyV1 {
    pub(crate) quarantined: TierFractionV1,
    pub(crate) unproven_or_novel: TierFractionV1,
    pub(crate) currently_assured: TierFractionV1,
    pub(crate) strong_current_assurance_low_impact: TierFractionV1,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct PolicyHysteresisV1 {
    pub(crate) min_relax_dwell_seconds: i64,
    pub(crate) required_clean_epochs: u32,
    pub(crate) successor_policy_digest: DigestV1,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SettlementPolicyV1 {
    pub(crate) policy_id: String,
    pub(crate) policy_version: u32,
    pub(crate) policy_digest: DigestV1,
    pub(crate) assurance_tiers: AssuranceTierPolicyV1,
    pub(crate) hysteresis: PolicyHysteresisV1,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct BudgetAxisV1 {
    pub(crate) axis_id: String,
    pub(crate) asset: String,
    pub(crate) cap: SignedRational,
    pub(crate) reserved: SignedRational,
    pub(crate) in_flight: SignedRational,
    pub(crate) consumed: SignedRational,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct BudgetLedgerStateV1 {
    pub(crate) tip_digest: DigestV1,
    pub(crate) epoch: u32,
    pub(crate) axes: Vec<BudgetAxisV1>,
    pub(crate) journal: Vec<String>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ChallengeKindV1 {
    Valid,
    Invalid,
    Duplicate,
    Censored,
    Unavailable,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ChallengeSubmissionV1 {
    challenge_id: String,
    trust_root_id: String,
    deadline: i64,
    affected_scope_id: String,
    kind: ChallengeKindV1,
}

impl ChallengeSubmissionV1 {
    pub fn new(
        challenge_id: impl Into<String>,
        trust_root_id: impl Into<String>,
        deadline: i64,
        affected_scope_id: impl Into<String>,
        kind: ChallengeKindV1,
    ) -> Self {
        Self {
            challenge_id: challenge_id.into(),
            trust_root_id: trust_root_id.into(),
            deadline,
            affected_scope_id: affected_scope_id.into(),
            kind,
        }
    }

    pub fn challenge_id(&self) -> &str {
        &self.challenge_id
    }

    pub fn trust_root_id(&self) -> &str {
        &self.trust_root_id
    }

    pub const fn deadline(&self) -> i64 {
        self.deadline
    }

    pub fn affected_scope_id(&self) -> &str {
        &self.affected_scope_id
    }

    pub const fn kind(&self) -> ChallengeKindV1 {
        self.kind
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ChallengeApplyResultV1 {
    Accepted,
    Rejected { reason: DecisionReasonV1 },
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct QueuePartV1 {
    part_id: String,
    amount: SignedRational,
    delay_seconds: i64,
    eligible_at: i64,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct QueueStateV1 {
    pub(crate) status: QueueStatusV1,
    pub(crate) parts: Vec<QueuePartV1>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct TransferStateV1 {
    pub(crate) status: TransferStatusV1,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct BreakerScopeV1 {
    pub(crate) scope_id: String,
    pub(crate) state: BreakerStateV1,
    pub(crate) expires_at: Option<i64>,
    pub(crate) renewal_count: u32,
    pub(crate) renewal_ceiling: u32,
}

impl BreakerScopeV1 {
    pub fn scope_id(&self) -> &str {
        &self.scope_id
    }

    pub const fn state(&self) -> BreakerStateV1 {
        self.state
    }

    pub const fn expires_at(&self) -> Option<i64> {
        self.expires_at
    }

    pub const fn renewal_count(&self) -> u32 {
        self.renewal_count
    }

    pub const fn renewal_ceiling(&self) -> u32 {
        self.renewal_ceiling
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct RecoverySnapshotV1 {
    pub(crate) profile_digest: DigestV1,
    pub(crate) halted_paths: BTreeSet<String>,
    pub(crate) reconciliation_mismatch: bool,
    pub(crate) canary_failed: bool,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SettlementStateV1 {
    pub(crate) ledger: BudgetLedgerStateV1,
    pub(crate) queue: QueueStateV1,
    pub(crate) transfer: TransferStateV1,
    pub(crate) breakers: Vec<BreakerScopeV1>,
    pub(crate) recovery: RecoverySnapshotV1,
    pub(crate) expected_ledger_tip: DigestV1,
    pub(crate) applied_challenge_ids: BTreeSet<String>,
}

impl QueueStateV1 {
    pub const fn status(&self) -> QueueStatusV1 {
        self.status
    }
}

impl TransferStateV1 {
    pub const fn status(&self) -> TransferStatusV1 {
        self.status
    }
}

impl SettlementStateV1 {
    pub const fn ledger(&self) -> &BudgetLedgerStateV1 {
        &self.ledger
    }

    pub const fn queue(&self) -> &QueueStateV1 {
        &self.queue
    }

    pub fn breakers(&self) -> &[BreakerScopeV1] {
        &self.breakers
    }

    pub fn transfer_state(&self) -> &TransferStateV1 {
        &self.transfer
    }

    pub const fn recovery(&self) -> &RecoverySnapshotV1 {
        &self.recovery
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct DecisionRecordV1 {
    pub(crate) schema_version: u16,
    pub(crate) outcome: DecisionOutcomeV1,
    pub(crate) release_class: ReleaseClassV1,
    pub(crate) assurance_tier: Option<AssuranceTierV1>,
    pub(crate) instant_release_amount: SignedRational,
    pub(crate) queued_release_amount: SignedRational,
    pub(crate) intent_digest: DigestV1,
    pub(crate) decision_context_digest: DigestV1,
    pub(crate) release_attempt_digest: Option<DigestV1>,
    pub(crate) analysis_subject_digest: Option<DigestV1>,
    pub(crate) composition_digest: Option<DigestV1>,
    pub(crate) evidence_snapshot_digest: DigestV1,
    pub(crate) valuation_profile_digest: DigestV1,
    pub(crate) policy_digest: DigestV1,
    pub(crate) linked_plan_or_obligation_digest: Option<DigestV1>,
    pub(crate) ledger_tip_before: DigestV1,
    pub(crate) ledger_tip_after: DigestV1,
    pub(crate) queue_status_before: QueueStatusV1,
    pub(crate) queue_status_after: QueueStatusV1,
    pub(crate) transfer_status_before: TransferStatusV1,
    pub(crate) transfer_status_after: TransferStatusV1,
    pub(crate) reasons: Vec<DecisionReasonV1>,
    pub(crate) missing_facts: Vec<DecisionMissingFactV1>,
    pub(crate) nonclaims: Vec<DecisionNonclaimV1>,
    pub(crate) evaluated_at: i64,
    pub(crate) record_digest: DigestV1,
    pub(crate) next_state: SettlementStateV1,
}

impl DecisionRecordV1 {
    pub const fn schema_version(&self) -> u16 {
        self.schema_version
    }

    pub const fn outcome(&self) -> DecisionOutcomeV1 {
        self.outcome
    }

    pub const fn instant_release_amount(&self) -> SignedRational {
        self.instant_release_amount
    }

    pub const fn intent_digest(&self) -> DigestV1 {
        self.intent_digest
    }

    pub const fn decision_context_digest(&self) -> DigestV1 {
        self.decision_context_digest
    }

    pub const fn record_digest(&self) -> DigestV1 {
        self.record_digest
    }

    pub fn reasons(&self) -> &[DecisionReasonV1] {
        &self.reasons
    }

    pub const fn next_state(&self) -> &SettlementStateV1 {
        &self.next_state
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SettlementScenarioV1 {
    pub(crate) scenario_id: String,
    pub(crate) clock: ClockV1,
    pub(crate) policy: SettlementPolicyV1,
    pub(crate) valuation_profile: ConservativeValuationProfileV1,
    pub(crate) evidence_snapshot: EvidenceSnapshotV1,
    pub(crate) initial_state: SettlementStateV1,
    pub(crate) request: ExternalizationRequestV1,
}

impl SettlementScenarioV1 {
    pub fn scenario_id(&self) -> &str {
        &self.scenario_id
    }

    pub fn clock(&self) -> &ClockV1 {
        &self.clock
    }

    pub fn policy(&self) -> &SettlementPolicyV1 {
        &self.policy
    }

    pub fn valuation_profile(&self) -> &ConservativeValuationProfileV1 {
        &self.valuation_profile
    }

    pub fn evidence_snapshot(&self) -> &EvidenceSnapshotV1 {
        &self.evidence_snapshot
    }

    pub fn request(&self) -> &ExternalizationRequestV1 {
        &self.request
    }

    pub fn initial_state(&self) -> &SettlementStateV1 {
        &self.initial_state
    }

    pub fn into_kernel_input(self) -> (ExternalizationRequestV1, SettlementStateV1, ClockV1) {
        (self.request, self.initial_state, self.clock)
    }
}

pub(crate) fn default_nonclaims() -> Vec<DecisionNonclaimV1> {
    vec![
        DecisionNonclaimV1::NoTransferCommand,
        DecisionNonclaimV1::NoSigningRequest,
        DecisionNonclaimV1::NoAuthority,
        DecisionNonclaimV1::NoValueMovement,
        DecisionNonclaimV1::NoTrustScore,
        DecisionNonclaimV1::NoReleaseSafetyProbability,
    ]
}

pub(crate) fn zero_rational() -> SignedRational {
    SignedRational::new(0, 1).expect("zero is canonical")
}
