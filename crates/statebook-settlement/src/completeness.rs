use serde::de::{self, MapAccess, SeqAccess, Visitor};
use serde::ser::SerializeStruct;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use serde_json::{Map, Number, Value};
use sha2::{Digest, Sha256};
use statebook_core::{
    AggregatedPositionReceiptV1, PayoffAssumptionV1, PayoffCompletenessReportV1,
    PayoffCompletenessStatusV1, SemanticCompletenessReport, SemanticCompletenessStatus,
    SemanticField, Sha256Digest, SignedRational, StateEvaluationStatusV1, StateKeyV1,
    UnmodeledResidualClassV1, UnsupportedStateReasonV1, UnsupportedTerm,
};
use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::marker::PhantomData;
use std::ops::{Deref, DerefMut};
use thiserror::Error;

pub const MAX_FIXTURE_BYTES_V1: usize = 1_048_576;
pub const MAX_EXECUTION_LEGS_V1: usize = 64;
pub const MAX_BOOK_LEVELS_PER_LEG_V1: usize = 64;
pub const MAX_CAPITAL_RECEIPTS_V1: usize = 64;
pub const MAX_SETTLEMENT_OBLIGATIONS_V1: usize = 64;
pub const MAX_ASSURANCE_OBSERVATIONS_V1: usize = 128;
pub const MAX_CURRENT_OR_DEPENDENCY_ROOTS_V1: usize = 32;
pub const MAX_RECOVERY_PATHS_V1: usize = 64;
pub const MAX_IN_FLIGHT_RECOVERY_ITEMS_V1: usize = 256;
pub const MAX_CANARY_STAGES_V1: usize = 16;
pub const MAX_SOURCE_EVIDENCE_DIGESTS_V1: usize = 256;
pub const ASSURANCE_PROPERTY_COUNT_V1: usize = 9;
pub const RECOVERY_PATH_COUNT_V1: usize = 14;
pub const RECOVERY_CAPABILITY_COUNT_V1: usize = 5;

const FIXTURE_SCHEMA_V1: &str = "statebook-completeness-fixture:v1";
const PROFILE_ID_V1: &str = "statebook-externalization";
const PROFILE_VERSION_V1: u32 = 1;

const SEMANTIC_DOMAIN: &[u8] = b"statebook:p3-semantic-report:v1\0";
const PAYOFF_DOMAIN: &[u8] = b"statebook:p3-payoff-report:v1\0";
const SUBJECT_DOMAIN: &[u8] = b"statebook:p3-analysis-subject:v1\0";
const EXECUTION_FIXTURE_DOMAIN: &[u8] = b"statebook:p3-execution-fixture:v1\0";
const CAPITAL_FIXTURE_DOMAIN: &[u8] = b"statebook:p3-capital-fixture:v1\0";
const CAPITAL_CONTEXT_DOMAIN: &[u8] = b"statebook:p3-capital-context:v1\0";
const SETTLEMENT_FIXTURE_DOMAIN: &[u8] = b"statebook:p3-settlement-fixture:v1\0";
const ASSURANCE_FIXTURE_DOMAIN: &[u8] = b"statebook:p3-assurance-fixture:v1\0";
const RECOVERY_PROFILE_DOMAIN: &[u8] = b"statebook:p3-recovery-profile:v1\0";
const RECOVERY_FIXTURE_DOMAIN: &[u8] = b"statebook:p3-recovery-fixture:v1\0";
const EXECUTION_REPORT_DOMAIN: &[u8] = b"statebook:p3-execution-report:v1\0";
const CAPITAL_REPORT_DOMAIN: &[u8] = b"statebook:p3-capital-report:v1\0";
const SETTLEMENT_REPORT_DOMAIN: &[u8] = b"statebook:p3-settlement-report:v1\0";
const ASSURANCE_REPORT_DOMAIN: &[u8] = b"statebook:p3-assurance-report:v1\0";
const RECOVERY_REPORT_DOMAIN: &[u8] = b"statebook:p3-recovery-report:v1\0";
const COMPOSITION_DOMAIN: &[u8] = b"statebook:p3-seven-report-composition:v1\0";

#[derive(Clone, Debug, Serialize)]
#[serde(transparent)]
struct BoundedVec<T, const MAXIMUM: usize>(Vec<T>);

impl<T, const MAXIMUM: usize> Deref for BoundedVec<T, MAXIMUM> {
    type Target = [T];
    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl<T, const MAXIMUM: usize> DerefMut for BoundedVec<T, MAXIMUM> {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.0
    }
}

impl<'a, T, const MAXIMUM: usize> IntoIterator for &'a BoundedVec<T, MAXIMUM> {
    type Item = &'a T;
    type IntoIter = std::slice::Iter<'a, T>;
    fn into_iter(self) -> Self::IntoIter {
        self.0.iter()
    }
}

impl<'a, T, const MAXIMUM: usize> IntoIterator for &'a mut BoundedVec<T, MAXIMUM> {
    type Item = &'a mut T;
    type IntoIter = std::slice::IterMut<'a, T>;
    fn into_iter(self) -> Self::IntoIter {
        self.0.iter_mut()
    }
}

impl<'de, T, const MAXIMUM: usize> Deserialize<'de> for BoundedVec<T, MAXIMUM>
where
    T: Deserialize<'de>,
{
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        struct BoundedVisitor<T, const MAXIMUM: usize>(PhantomData<T>);
        impl<'de, T, const MAXIMUM: usize> Visitor<'de> for BoundedVisitor<T, MAXIMUM>
        where
            T: Deserialize<'de>,
        {
            type Value = BoundedVec<T, MAXIMUM>;
            fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
                write!(formatter, "a sequence with at most {MAXIMUM} items")
            }
            fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
            where
                A: SeqAccess<'de>,
            {
                if sequence.size_hint().is_some_and(|size| size > MAXIMUM) {
                    return Err(de::Error::custom(format!(
                        "sequence exceeds {MAXIMUM} items"
                    )));
                }
                let mut values = Vec::with_capacity(sequence.size_hint().unwrap_or(0).min(MAXIMUM));
                while let Some(value) = sequence.next_element::<T>()? {
                    if values.len() == MAXIMUM {
                        return Err(de::Error::custom(format!(
                            "sequence exceeds {MAXIMUM} items"
                        )));
                    }
                    values.push(value);
                }
                Ok(BoundedVec(values))
            }
        }
        deserializer.deserialize_seq(BoundedVisitor(PhantomData))
    }
}

#[derive(Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct DigestV1([u8; 32]);

impl DigestV1 {
    fn from_bytes(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }

    /// Shared constructor for crate-local digest materialization (P3/P4).
    pub fn from_raw_bytes(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }

    fn parse(value: &str) -> Result<Self, FixtureParseErrorV1> {
        if value.len() != 64
            || !value
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        {
            return Err(FixtureParseErrorV1::InvalidDigest(value.to_owned()));
        }
        let mut bytes = [0_u8; 32];
        hex::decode_to_slice(value, &mut bytes)
            .map_err(|_| FixtureParseErrorV1::InvalidDigest(value.to_owned()))?;
        Ok(Self(bytes))
    }

    pub const fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }

    pub fn to_hex(self) -> String {
        hex::encode(self.0)
    }
}

impl fmt::Debug for DigestV1 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_tuple("DigestV1")
            .field(&self.to_hex())
            .finish()
    }
}

impl Serialize for DigestV1 {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        serializer.serialize_str(&self.to_hex())
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EvidenceClassV1 {
    HermeticFixtureOnly,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CompletenessDimensionV1 {
    Execution,
    Capital,
    Settlement,
    Assurance,
    Recovery,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CompletenessAssumptionV1 {
    HermeticFixtureOnly,
    NoLiveAuthority,
    NoCrossDimensionInference,
    FixedWidthExactArithmetic,
    CurrentRootsDisclosedNotResolved,
    VersionedRecoveryProfileOnly,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CompletenessReasonV1 {
    MissingFixture,
    StaleOrFutureObservation,
    MissingObservation,
    ExplicitlyUnsupported,
    PartialQuantity,
    ZeroExecutableQuantity,
    ExplicitDenial,
    PartialRecognition,
    DisputedOrReversed,
    IncompatibleFinalityDomain,
    PendingStage,
    ConditionalLegalFinality,
    MissingAssuranceProperty,
    UnknownAssuranceVerdict,
    MissingCurrentRoot,
    UnknownDependencyAncestry,
    ReplayOrRevocationState,
    ExplicitAssuranceFailure,
    MissingRecoveryPath,
    MissingRecoveryCapability,
    RecoveryControlFailure,
    ReconciliationMismatch,
    EvidenceLoss,
    DuplicateLiability,
    MissingOrFailedCanary,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CompletenessMissingFactV1 {
    Fixture,
    CurrentObservation,
    RequiredExecutionLeg,
    RequiredCapitalReceipt,
    SettlementPolicyOrStage,
    AssuranceProperty,
    CurrentAssuranceRoot,
    DependencyAncestry,
    RecoveryPath,
    RecoveryCapability,
    InFlightReconciliation,
    CanaryStage,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionCompletenessStatusV1 {
    ExecutableInFixture,
    PartiallyExecutableInFixture,
    NotExecutableInFixture,
    NotObserved,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CapitalCompletenessStatusV1 {
    RecognizedInFixture,
    PartiallyRecognizedInFixture,
    NotRecognizedInFixture,
    NotEvaluated,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SettlementCompletenessStatusV1 {
    FinalInFixture,
    ConditionalInFixture,
    PendingInFixture,
    DisputedInFixture,
    UnsupportedInFixture,
    Unknown,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AssuranceCompletenessStatusV1 {
    AllRequiredObservedInFixture,
    ContradictedInFixture,
    IncompleteInFixture,
    NotObserved,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RecoveryCompletenessStatusV1 {
    CompleteOnVersionedFixtureProfile,
    IncompleteOnVersionedFixtureProfile,
    FailedInFixture,
    NotObserved,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AssurancePropertyV1 {
    ActionAuthorization,
    SourceAuthenticityAndFreshness,
    CalculationIntegrity,
    StateTransitionIntegrity,
    SolvencyAndLiquidResourceSupport,
    DestinationAndRoutePolicy,
    AnomalyAndEmergencyClearance,
    EvidenceRootDisclosure,
    FinancialBasisBinding,
}

const REQUIRED_ASSURANCE_PROPERTIES: [AssurancePropertyV1; ASSURANCE_PROPERTY_COUNT_V1] = [
    AssurancePropertyV1::ActionAuthorization,
    AssurancePropertyV1::SourceAuthenticityAndFreshness,
    AssurancePropertyV1::CalculationIntegrity,
    AssurancePropertyV1::StateTransitionIntegrity,
    AssurancePropertyV1::SolvencyAndLiquidResourceSupport,
    AssurancePropertyV1::DestinationAndRoutePolicy,
    AssurancePropertyV1::AnomalyAndEmergencyClearance,
    AssurancePropertyV1::EvidenceRootDisclosure,
    AssurancePropertyV1::FinancialBasisBinding,
];

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum AssuranceVerdictV1 {
    Pass,
    Fail,
    Unknown,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RootClassV1 {
    Data,
    Operator,
    Cloud,
    Kms,
    Rpc,
    CiCd,
    Model,
    Signer,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DependencyDisclosureV1 {
    Complete,
    Unknown,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RecoveryCapabilityV1 {
    StopExternalization,
    ReconcileEveryInFlightItem,
    PreserveEvidence,
    RestoreLiabilitiesWithoutDuplication,
    ReopenThroughBoundedCanaryStages,
}

const REQUIRED_RECOVERY_CAPABILITIES: [RecoveryCapabilityV1; RECOVERY_CAPABILITY_COUNT_V1] = [
    RecoveryCapabilityV1::StopExternalization,
    RecoveryCapabilityV1::ReconcileEveryInFlightItem,
    RecoveryCapabilityV1::PreserveEvidence,
    RecoveryCapabilityV1::RestoreLiabilitiesWithoutDuplication,
    RecoveryCapabilityV1::ReopenThroughBoundedCanaryStages,
];

const REQUIRED_RECOVERY_PATHS: [&str; 14] = [
    "release-class-all",
    "profitable-close-payout",
    "liquidation-surplus",
    "lp-withdrawal",
    "collateral-withdrawal",
    "linked-exchange-outbound-leg",
    "risk-reducing-obligation-endpoint",
    "bridge",
    "administrative-transfer",
    "emergency-route",
    "transferable-queued-claim",
    "borrowing",
    "margin-reuse",
    "internal-credit-monetization",
];

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
pub struct AssuranceRootV1 {
    root_class: RootClassV1,
    root_id: String,
}

impl AssuranceRootV1 {
    pub fn new(root_class: RootClassV1, root_id: impl Into<String>) -> Self {
        Self {
            root_class,
            root_id: root_id.into(),
        }
    }

    pub const fn root_class(&self) -> RootClassV1 {
        self.root_class
    }
    pub fn root_id(&self) -> &str {
        &self.root_id
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct AnalysisSubjectV1 {
    schema_version: u16,
    digest: DigestV1,
    semantic_report_digest: DigestV1,
    payoff_report_digest: DigestV1,
    #[serde(skip)]
    candidate_quantities: BTreeMap<StateKeyV1, SignedRational>,
}

impl AnalysisSubjectV1 {
    pub const fn schema_version(&self) -> u16 {
        self.schema_version
    }
    pub const fn digest(&self) -> DigestV1 {
        self.digest
    }
    pub const fn semantic_report_digest(&self) -> DigestV1 {
        self.semantic_report_digest
    }
    pub const fn payoff_report_digest(&self) -> DigestV1 {
        self.payoff_report_digest
    }
    pub const fn candidate_quantities(&self) -> &BTreeMap<StateKeyV1, SignedRational> {
        &self.candidate_quantities
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
struct ReportMetaV1 {
    schema_version: u16,
    dimension: CompletenessDimensionV1,
    analysis_subject_digest: DigestV1,
    fixture_digest: Option<DigestV1>,
    evidence_class: EvidenceClassV1,
    source_evidence_digests: BTreeSet<DigestV1>,
    assumptions: BTreeSet<CompletenessAssumptionV1>,
    reasons: BTreeSet<CompletenessReasonV1>,
    missing_facts: BTreeSet<CompletenessMissingFactV1>,
    evaluated_at: i64,
    expires_at: Option<i64>,
    report_digest: DigestV1,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ExecutionLegResultV1 {
    leg_id: String,
    asset: String,
    requested_quantity: SignedRational,
    executable_quantity: SignedRational,
    unfilled_quantity: SignedRational,
    gross_notional: SignedRational,
    average_price: Option<SignedRational>,
    worst_price: Option<SignedRational>,
    fee: SignedRational,
    slippage: Option<SignedRational>,
    side: ExecutionSideV1,
    reference_price: SignedRational,
    price_bound: SignedRational,
    fee_rate: SignedRational,
    maximum_fee: SignedRational,
    maximum_slippage: SignedRational,
    queue: FixtureSupportV1,
    atomicity: FixtureSupportV1,
    leg_failure_model: FixtureSupportV1,
    deadline: i64,
}

impl ExecutionLegResultV1 {
    pub fn leg_id(&self) -> &str {
        &self.leg_id
    }
    pub fn asset(&self) -> &str {
        &self.asset
    }
    pub const fn requested_quantity(&self) -> SignedRational {
        self.requested_quantity
    }
    pub const fn executable_quantity(&self) -> SignedRational {
        self.executable_quantity
    }
    pub const fn unfilled_quantity(&self) -> SignedRational {
        self.unfilled_quantity
    }
    pub const fn gross_notional(&self) -> SignedRational {
        self.gross_notional
    }
    pub const fn average_price(&self) -> Option<SignedRational> {
        self.average_price
    }
    pub const fn worst_price(&self) -> Option<SignedRational> {
        self.worst_price
    }
    pub const fn fee(&self) -> SignedRational {
        self.fee
    }
    pub const fn slippage(&self) -> Option<SignedRational> {
        self.slippage
    }
    pub const fn side(&self) -> ExecutionSideV1 {
        self.side
    }
    pub const fn reference_price(&self) -> SignedRational {
        self.reference_price
    }
    pub const fn price_bound(&self) -> SignedRational {
        self.price_bound
    }
    pub const fn fee_rate(&self) -> SignedRational {
        self.fee_rate
    }
    pub const fn maximum_fee(&self) -> SignedRational {
        self.maximum_fee
    }
    pub const fn maximum_slippage(&self) -> SignedRational {
        self.maximum_slippage
    }
    pub const fn queue(&self) -> FixtureSupportV1 {
        self.queue
    }
    pub const fn atomicity(&self) -> FixtureSupportV1 {
        self.atomicity
    }
    pub const fn leg_failure_model(&self) -> FixtureSupportV1 {
        self.leg_failure_model
    }
    pub const fn deadline(&self) -> i64 {
        self.deadline
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ExecutionContextV1 {
    venue_id: String,
    account_id: String,
    observed_at: i64,
}
impl ExecutionContextV1 {
    pub fn venue_id(&self) -> &str {
        &self.venue_id
    }
    pub fn account_id(&self) -> &str {
        &self.account_id
    }
    pub const fn observed_at(&self) -> i64 {
        self.observed_at
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CapitalReceiptResultV1 {
    state_key: StateKeyV1,
    required_quantity: SignedRational,
    recognized_quantity: SignedRational,
    recognition_residual: SignedRational,
    capital_context_digest: DigestV1,
    verdict: CapitalFixtureVerdictV1,
}

impl CapitalReceiptResultV1 {
    pub const fn state_key(&self) -> StateKeyV1 {
        self.state_key
    }
    pub const fn required_quantity(&self) -> SignedRational {
        self.required_quantity
    }
    pub const fn recognized_quantity(&self) -> SignedRational {
        self.recognized_quantity
    }
    pub const fn recognition_residual(&self) -> SignedRational {
        self.recognition_residual
    }
    pub const fn capital_context_digest(&self) -> DigestV1 {
        self.capital_context_digest
    }
    pub const fn verdict(&self) -> CapitalFixtureVerdictV1 {
        self.verdict
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CapitalContextV1 {
    authority_id: String,
    eligible_account: String,
    model_id: String,
    model_version: u32,
    model_digest: DigestV1,
    haircut: SignedRational,
    margin_rule_id: String,
    jurisdiction: String,
    liquidation_horizon_seconds: u64,
    observed_at: i64,
    capital_context_digest: DigestV1,
}
impl CapitalContextV1 {
    pub fn authority_id(&self) -> &str {
        &self.authority_id
    }
    pub fn eligible_account(&self) -> &str {
        &self.eligible_account
    }
    pub fn model_id(&self) -> &str {
        &self.model_id
    }
    pub const fn model_version(&self) -> u32 {
        self.model_version
    }
    pub const fn model_digest(&self) -> DigestV1 {
        self.model_digest
    }
    pub const fn haircut(&self) -> SignedRational {
        self.haircut
    }
    pub fn margin_rule_id(&self) -> &str {
        &self.margin_rule_id
    }
    pub fn jurisdiction(&self) -> &str {
        &self.jurisdiction
    }
    pub const fn liquidation_horizon_seconds(&self) -> u64 {
        self.liquidation_horizon_seconds
    }
    pub const fn observed_at(&self) -> i64 {
        self.observed_at
    }
    pub const fn capital_context_digest(&self) -> DigestV1 {
        self.capital_context_digest
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SettlementStageV1 {
    SourceObservation,
    SourceFinality,
    DestinationObservation,
    DestinationFinality,
    OperationalReconciliation,
    LegalFinality,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum StageVerdictV1 {
    Passed,
    Pending,
    Conditional,
    Unknown,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SettlementStageObservationV1 {
    obligation_id: String,
    stage: SettlementStageV1,
    verdict: StageVerdictV1,
}

impl SettlementStageObservationV1 {
    pub fn obligation_id(&self) -> &str {
        &self.obligation_id
    }
    pub const fn stage(&self) -> SettlementStageV1 {
        self.stage
    }
    pub const fn verdict(&self) -> StageVerdictV1 {
        self.verdict
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SettlementContextV1 {
    source_finality_domain: String,
    destination_finality_domain: String,
    domains_compatible: bool,
    transition_supported: bool,
    reversal_rule: Option<String>,
    insolvency_rule: Option<String>,
    disputed: bool,
    reversed: bool,
    reconciliation_mismatch: bool,
    observed_at: i64,
}
impl SettlementContextV1 {
    pub fn source_finality_domain(&self) -> &str {
        &self.source_finality_domain
    }
    pub fn destination_finality_domain(&self) -> &str {
        &self.destination_finality_domain
    }
    pub const fn domains_compatible(&self) -> bool {
        self.domains_compatible
    }
    pub const fn transition_supported(&self) -> bool {
        self.transition_supported
    }
    pub fn reversal_rule(&self) -> Option<&str> {
        self.reversal_rule.as_deref()
    }
    pub fn insolvency_rule(&self) -> Option<&str> {
        self.insolvency_rule.as_deref()
    }
    pub const fn disputed(&self) -> bool {
        self.disputed
    }
    pub const fn reversed(&self) -> bool {
        self.reversed
    }
    pub const fn reconciliation_mismatch(&self) -> bool {
        self.reconciliation_mismatch
    }
    pub const fn observed_at(&self) -> i64 {
        self.observed_at
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct AssurancePropertyObservationV1 {
    property: AssurancePropertyV1,
    verdict: AssuranceVerdictV1,
    current_roots: BTreeSet<AssuranceRootV1>,
    dependency_roots: BTreeSet<AssuranceRootV1>,
    dependency_disclosure: DependencyDisclosureV1,
    replayed: bool,
    revoked: bool,
    superseded: bool,
    equivocated: bool,
}

impl AssurancePropertyObservationV1 {
    pub const fn property(&self) -> AssurancePropertyV1 {
        self.property
    }
    pub const fn verdict(&self) -> AssuranceVerdictV1 {
        self.verdict
    }
    pub const fn current_roots(&self) -> &BTreeSet<AssuranceRootV1> {
        &self.current_roots
    }
    pub const fn dependency_roots(&self) -> &BTreeSet<AssuranceRootV1> {
        &self.dependency_roots
    }
    pub const fn dependency_disclosure(&self) -> DependencyDisclosureV1 {
        self.dependency_disclosure
    }
    pub const fn replayed(&self) -> bool {
        self.replayed
    }
    pub const fn revoked(&self) -> bool {
        self.revoked
    }
    pub const fn superseded(&self) -> bool {
        self.superseded
    }
    pub const fn equivocated(&self) -> bool {
        self.equivocated
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct AssuranceContextV1 {
    issuer_id: String,
    subject_id: String,
    scope_digest: DigestV1,
    nonce: String,
    observed_at: i64,
}
impl AssuranceContextV1 {
    pub fn issuer_id(&self) -> &str {
        &self.issuer_id
    }
    pub fn subject_id(&self) -> &str {
        &self.subject_id
    }
    pub const fn scope_digest(&self) -> DigestV1 {
        self.scope_digest
    }
    pub fn nonce(&self) -> &str {
        &self.nonce
    }
    pub const fn observed_at(&self) -> i64 {
        self.observed_at
    }
    pub const fn issued_at(&self) -> i64 {
        self.observed_at
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct RecoveryPathObservationV1 {
    path_id: String,
    capabilities: BTreeMap<RecoveryCapabilityV1, AssuranceVerdictV1>,
}

impl RecoveryPathObservationV1 {
    pub fn path_id(&self) -> &str {
        &self.path_id
    }
    pub const fn capabilities(&self) -> &BTreeMap<RecoveryCapabilityV1, AssuranceVerdictV1> {
        &self.capabilities
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct InFlightReconciliationV1 {
    item_id: String,
    expected_digest: DigestV1,
    observed_digest: DigestV1,
}
impl InFlightReconciliationV1 {
    pub fn item_id(&self) -> &str {
        &self.item_id
    }
    pub const fn expected_digest(&self) -> DigestV1 {
        self.expected_digest
    }
    pub const fn observed_digest(&self) -> DigestV1 {
        self.observed_digest
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct RecoveryContextV1 {
    in_flight_items: Vec<InFlightReconciliationV1>,
    evidence_preserved: AssuranceVerdictV1,
    liabilities_duplicate_free: AssuranceVerdictV1,
    canary_stages: Vec<AssuranceVerdictV1>,
    evidence_preservation_ref: String,
    liability_before_digest: DigestV1,
    liability_after_digest: DigestV1,
    observed_at: i64,
}
impl RecoveryContextV1 {
    pub fn in_flight_items(&self) -> &[InFlightReconciliationV1] {
        &self.in_flight_items
    }
    pub const fn evidence_preserved(&self) -> AssuranceVerdictV1 {
        self.evidence_preserved
    }
    pub const fn liabilities_duplicate_free(&self) -> AssuranceVerdictV1 {
        self.liabilities_duplicate_free
    }
    pub fn canary_stages(&self) -> &[AssuranceVerdictV1] {
        &self.canary_stages
    }
    pub const fn observed_at(&self) -> i64 {
        self.observed_at
    }
    pub fn evidence_preservation_ref(&self) -> &str {
        &self.evidence_preservation_ref
    }
    pub const fn liability_before_digest(&self) -> DigestV1 {
        self.liability_before_digest
    }
    pub const fn liability_after_digest(&self) -> DigestV1 {
        self.liability_after_digest
    }
}

macro_rules! report_type {
    ($name:ident, $status:ty, $extra_name:ident, $extra_ty:ty, $context:ty) => {
        #[derive(Clone, Debug, Eq, PartialEq, Serialize)]
        pub struct $name {
            #[serde(flatten)]
            meta: ReportMetaV1,
            status: $status,
            $extra_name: $extra_ty,
            context: Option<$context>,
        }
        impl $name {
            pub const fn status(&self) -> $status {
                self.status
            }
            pub const fn schema_version(&self) -> u16 {
                self.meta.schema_version
            }
            pub const fn dimension(&self) -> CompletenessDimensionV1 {
                self.meta.dimension
            }
            pub const fn evidence_class(&self) -> EvidenceClassV1 {
                self.meta.evidence_class
            }
            pub const fn analysis_subject_digest(&self) -> DigestV1 {
                self.meta.analysis_subject_digest
            }
            pub const fn fixture_digest(&self) -> Option<DigestV1> {
                self.meta.fixture_digest
            }
            pub const fn source_evidence_digests(&self) -> &BTreeSet<DigestV1> {
                &self.meta.source_evidence_digests
            }
            pub const fn assumptions(&self) -> &BTreeSet<CompletenessAssumptionV1> {
                &self.meta.assumptions
            }
            pub const fn reasons(&self) -> &BTreeSet<CompletenessReasonV1> {
                &self.meta.reasons
            }
            pub const fn missing_facts(&self) -> &BTreeSet<CompletenessMissingFactV1> {
                &self.meta.missing_facts
            }
            pub const fn evaluated_at(&self) -> i64 {
                self.meta.evaluated_at
            }
            pub const fn expires_at(&self) -> Option<i64> {
                self.meta.expires_at
            }
            pub const fn report_digest(&self) -> DigestV1 {
                self.meta.report_digest
            }
            pub const fn $extra_name(&self) -> &$extra_ty {
                &self.$extra_name
            }
            pub const fn context(&self) -> Option<&$context> {
                self.context.as_ref()
            }
        }
    };
}

report_type!(
    ExecutionCompletenessReportV1,
    ExecutionCompletenessStatusV1,
    legs,
    Vec<ExecutionLegResultV1>,
    ExecutionContextV1
);
report_type!(
    CapitalCompletenessReportV1,
    CapitalCompletenessStatusV1,
    receipts,
    Vec<CapitalReceiptResultV1>,
    CapitalContextV1
);
report_type!(
    SettlementCompletenessReportV1,
    SettlementCompletenessStatusV1,
    stages,
    Vec<SettlementStageObservationV1>,
    SettlementContextV1
);
report_type!(
    AssuranceCompletenessReportV1,
    AssuranceCompletenessStatusV1,
    properties,
    Vec<AssurancePropertyObservationV1>,
    AssuranceContextV1
);
report_type!(
    RecoveryCompletenessReportV1,
    RecoveryCompletenessStatusV1,
    paths,
    Vec<RecoveryPathObservationV1>,
    RecoveryContextV1
);

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct RecoveryPathProfileV1 {
    schema_version: u16,
    profile_id: String,
    profile_version: u32,
    required_path_ids: BTreeSet<String>,
    required_capabilities: BTreeSet<RecoveryCapabilityV1>,
    digest: DigestV1,
}

impl RecoveryPathProfileV1 {
    pub fn statebook_externalization_v1() -> Self {
        let required_path_ids = REQUIRED_RECOVERY_PATHS
            .iter()
            .map(|value| (*value).to_owned())
            .collect();
        let required_capabilities = REQUIRED_RECOVERY_CAPABILITIES.into_iter().collect();
        let mut value = Self {
            schema_version: 1,
            profile_id: PROFILE_ID_V1.to_owned(),
            profile_version: PROFILE_VERSION_V1,
            required_path_ids,
            required_capabilities,
            digest: DigestV1([0; 32]),
        };
        value.digest = digest(RECOVERY_PROFILE_DOMAIN, &encode_recovery_profile(&value));
        value
    }
    pub fn profile_id(&self) -> &str {
        &self.profile_id
    }
    pub const fn schema_version(&self) -> u16 {
        self.schema_version
    }
    pub const fn profile_version(&self) -> u32 {
        self.profile_version
    }
    pub const fn required_path_ids(&self) -> &BTreeSet<String> {
        &self.required_path_ids
    }
    pub const fn required_capabilities(&self) -> &BTreeSet<RecoveryCapabilityV1> {
        &self.required_capabilities
    }
    pub const fn digest(&self) -> DigestV1 {
        self.digest
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SevenCompletenessReportsV1 {
    schema_version: u16,
    analysis_subject: AnalysisSubjectV1,
    semantic: SemanticCompletenessReport,
    semantic_report_digest: DigestV1,
    payoff: PayoffCompletenessReportV1,
    payoff_report_digest: DigestV1,
    execution: ExecutionCompletenessReportV1,
    capital: CapitalCompletenessReportV1,
    settlement: SettlementCompletenessReportV1,
    assurance: AssuranceCompletenessReportV1,
    recovery: RecoveryCompletenessReportV1,
    recovery_profile_digest: DigestV1,
    evaluated_at: i64,
    fixture_document_sha256: DigestV1,
    composition_digest: DigestV1,
}

impl SevenCompletenessReportsV1 {
    pub const fn schema_version(&self) -> u16 {
        self.schema_version
    }
    pub const fn analysis_subject(&self) -> &AnalysisSubjectV1 {
        &self.analysis_subject
    }
    pub const fn semantic(&self) -> &SemanticCompletenessReport {
        &self.semantic
    }
    pub const fn semantic_report_digest(&self) -> DigestV1 {
        self.semantic_report_digest
    }
    pub const fn payoff(&self) -> &PayoffCompletenessReportV1 {
        &self.payoff
    }
    pub const fn payoff_report_digest(&self) -> DigestV1 {
        self.payoff_report_digest
    }
    pub const fn execution(&self) -> &ExecutionCompletenessReportV1 {
        &self.execution
    }
    pub const fn capital(&self) -> &CapitalCompletenessReportV1 {
        &self.capital
    }
    pub const fn settlement(&self) -> &SettlementCompletenessReportV1 {
        &self.settlement
    }
    pub const fn assurance(&self) -> &AssuranceCompletenessReportV1 {
        &self.assurance
    }
    pub const fn recovery(&self) -> &RecoveryCompletenessReportV1 {
        &self.recovery
    }
    pub const fn recovery_profile_digest(&self) -> DigestV1 {
        self.recovery_profile_digest
    }
    pub const fn evaluated_at(&self) -> i64 {
        self.evaluated_at
    }
    pub const fn fixture_document_sha256(&self) -> DigestV1 {
        self.fixture_document_sha256
    }
    pub const fn composition_digest(&self) -> DigestV1 {
        self.composition_digest
    }
}

#[derive(Clone, Debug)]
pub struct ValidatedCompletenessFixtureV1 {
    input: FixtureDocumentWire,
    fixture_document_sha256: DigestV1,
}

impl ValidatedCompletenessFixtureV1 {
    pub fn schema_version(&self) -> &str {
        &self.input.schema_version
    }
    pub const fn fixture_document_sha256(&self) -> DigestV1 {
        self.fixture_document_sha256
    }
    pub const fn has_execution(&self) -> bool {
        self.input.execution.is_some()
    }
    pub const fn has_capital(&self) -> bool {
        self.input.capital.is_some()
    }
    pub const fn has_settlement(&self) -> bool {
        self.input.settlement.is_some()
    }
    pub const fn has_assurance(&self) -> bool {
        self.input.assurance.is_some()
    }
    pub const fn has_recovery(&self) -> bool {
        self.input.recovery.is_some()
    }
}

impl Serialize for ValidatedCompletenessFixtureV1 {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut receipt = serializer.serialize_struct("ValidatedCompletenessFixtureV1", 7)?;
        receipt.serialize_field("schema_version", self.schema_version())?;
        receipt.serialize_field("fixture_document_sha256", &self.fixture_document_sha256)?;
        receipt.serialize_field("has_execution", &self.has_execution())?;
        receipt.serialize_field("has_capital", &self.has_capital())?;
        receipt.serialize_field("has_settlement", &self.has_settlement())?;
        receipt.serialize_field("has_assurance", &self.has_assurance())?;
        receipt.serialize_field("has_recovery", &self.has_recovery())?;
        receipt.end()
    }
}

#[derive(Clone, Debug, Eq, Error, PartialEq)]
pub enum FixtureParseErrorV1 {
    #[error("fixture document exceeds {maximum} bytes")]
    TooLarge { maximum: usize },
    #[error("invalid or ambiguous JSON: {0}")]
    Json(String),
    #[error("unsupported fixture schema: {0}")]
    SchemaVersion(String),
    #[error("invalid identifier: {0}")]
    InvalidIdentifier(String),
    #[error("invalid SHA-256 digest: {0}")]
    InvalidDigest(String),
    #[error("invalid exact rational: {0}")]
    InvalidRational(String),
    #[error("invalid observation interval")]
    InvalidInterval,
    #[error("resource bound exceeded: {0}")]
    ResourceBound(&'static str),
    #[error("duplicate semantic identity: {0}")]
    DuplicateIdentity(String),
    #[error("fixture violates closed input contract: {0}")]
    InvalidFixture(&'static str),
}

#[derive(Clone, Debug, Eq, Error, PartialEq)]
pub enum CompletenessEvaluationErrorV1 {
    #[error("fixture analysis-subject digest mismatch")]
    SubjectDigestMismatch,
    #[error("recovery-profile digest mismatch")]
    RecoveryProfileDigestMismatch,
    #[error("fixture receipt does not belong to the analysis subject")]
    UnknownReceipt,
    #[error("capital receipt context digest mismatch")]
    CapitalContextDigestMismatch,
    #[error("exact arithmetic overflow")]
    ArithmeticOverflow,
    #[error("invalid evaluated-at time")]
    InvalidEvaluationTime,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct FixtureDocumentWire {
    schema_version: String,
    execution: Option<ExecutionFixtureWire>,
    capital: Option<CapitalFixtureWire>,
    settlement: Option<SettlementFixtureWire>,
    assurance: Option<AssuranceFixtureWire>,
    recovery: Option<RecoveryFixtureWire>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct RationalWire {
    numerator: String,
    denominator: String,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum SideWire {
    Buy,
    Sell,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum SupportWire {
    Supported,
    Unsupported,
    Unknown,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum FixtureSupportV1 {
    Supported,
    Unsupported,
    Unknown,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ExecutionSideV1 {
    Buy,
    Sell,
}
impl From<SideWire> for ExecutionSideV1 {
    fn from(value: SideWire) -> Self {
        match value {
            SideWire::Buy => Self::Buy,
            SideWire::Sell => Self::Sell,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CapitalFixtureVerdictV1 {
    #[serde(rename = "recognized_in_fixture")]
    Recognized,
    #[serde(rename = "denied_in_fixture")]
    Denied,
}
impl From<CapitalVerdictWire> for CapitalFixtureVerdictV1 {
    fn from(value: CapitalVerdictWire) -> Self {
        match value {
            CapitalVerdictWire::Recognized => Self::Recognized,
            CapitalVerdictWire::Denied => Self::Denied,
        }
    }
}

impl From<SupportWire> for FixtureSupportV1 {
    fn from(value: SupportWire) -> Self {
        match value {
            SupportWire::Supported => Self::Supported,
            SupportWire::Unsupported => Self::Unsupported,
            SupportWire::Unknown => Self::Unknown,
        }
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct BookLevelWire {
    level_id: String,
    price: RationalWire,
    quantity: RationalWire,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct ExecutionLegWire {
    leg_id: String,
    state_key: String,
    asset: String,
    side: SideWire,
    requested_quantity: RationalWire,
    reference_price: RationalWire,
    price_bound: RationalWire,
    fee_rate: RationalWire,
    maximum_fee: RationalWire,
    maximum_slippage: RationalWire,
    deadline: i64,
    queue: SupportWire,
    atomicity: SupportWire,
    leg_failure_model: SupportWire,
    levels: BoundedVec<BookLevelWire, MAX_BOOK_LEVELS_PER_LEG_V1>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct ExecutionFixtureWire {
    analysis_subject_digest: String,
    observed_at: i64,
    expires_at: i64,
    venue_id: String,
    account_id: String,
    legs: BoundedVec<ExecutionLegWire, MAX_EXECUTION_LEGS_V1>,
    source_evidence_digests: BoundedVec<String, MAX_SOURCE_EVIDENCE_DIGESTS_V1>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum CapitalVerdictWire {
    Recognized,
    Denied,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct CapitalReceiptWire {
    state_key: String,
    recognized_quantity: RationalWire,
    verdict: CapitalVerdictWire,
    capital_context_digest: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct CapitalFixtureWire {
    analysis_subject_digest: String,
    observed_at: i64,
    expires_at: i64,
    authority_id: String,
    eligible_account: String,
    model_id: String,
    model_version: u32,
    model_digest: String,
    haircut: RationalWire,
    margin_rule_id: String,
    jurisdiction: String,
    liquidation_horizon_seconds: u64,
    receipts: BoundedVec<CapitalReceiptWire, MAX_CAPITAL_RECEIPTS_V1>,
    source_evidence_digests: BoundedVec<String, MAX_SOURCE_EVIDENCE_DIGESTS_V1>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct StageWire {
    obligation_id: String,
    stage: SettlementStageV1,
    verdict: StageVerdictV1,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct SettlementFixtureWire {
    analysis_subject_digest: String,
    observed_at: i64,
    expires_at: i64,
    source_finality_domain: String,
    destination_finality_domain: String,
    domains_compatible: bool,
    transition_supported: bool,
    reversal_rule: Option<String>,
    insolvency_rule: Option<String>,
    disputed: bool,
    reversed: bool,
    reconciliation_mismatch: bool,
    stages: BoundedVec<StageWire, { MAX_SETTLEMENT_OBLIGATIONS_V1 * 6 }>,
    source_evidence_digests: BoundedVec<String, MAX_SOURCE_EVIDENCE_DIGESTS_V1>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct RootWire {
    root_class: RootClassV1,
    root_id: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct AssuranceObservationWire {
    property: AssurancePropertyV1,
    verdict: AssuranceVerdictV1,
    current_roots: BoundedVec<RootWire, MAX_CURRENT_OR_DEPENDENCY_ROOTS_V1>,
    dependency_roots: BoundedVec<RootWire, MAX_CURRENT_OR_DEPENDENCY_ROOTS_V1>,
    dependency_disclosure: DependencyDisclosureV1,
    replayed: bool,
    revoked: bool,
    superseded: bool,
    equivocated: bool,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct AssuranceFixtureWire {
    analysis_subject_digest: String,
    observed_at: i64,
    expires_at: i64,
    issuer_id: String,
    subject_id: String,
    scope_digest: String,
    nonce: String,
    observations: BoundedVec<AssuranceObservationWire, MAX_ASSURANCE_OBSERVATIONS_V1>,
    source_evidence_digests: BoundedVec<String, MAX_SOURCE_EVIDENCE_DIGESTS_V1>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct CapabilityWire {
    capability: RecoveryCapabilityV1,
    verdict: AssuranceVerdictV1,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct RecoveryPathWire {
    path_id: String,
    capabilities: BoundedVec<CapabilityWire, RECOVERY_CAPABILITY_COUNT_V1>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct InFlightWire {
    item_id: String,
    expected_digest: String,
    observed_digest: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct RecoveryFixtureWire {
    analysis_subject_digest: String,
    recovery_profile_digest: String,
    observed_at: i64,
    expires_at: i64,
    paths: BoundedVec<RecoveryPathWire, MAX_RECOVERY_PATHS_V1>,
    in_flight_items: BoundedVec<InFlightWire, MAX_IN_FLIGHT_RECOVERY_ITEMS_V1>,
    evidence_preservation_ref: String,
    liability_before_digest: String,
    liability_after_digest: String,
    evidence_preserved: AssuranceVerdictV1,
    liabilities_duplicate_free: AssuranceVerdictV1,
    canary_stages: BoundedVec<AssuranceVerdictV1, MAX_CANARY_STAGES_V1>,
    source_evidence_digests: BoundedVec<String, MAX_SOURCE_EVIDENCE_DIGESTS_V1>,
}

pub fn parse_completeness_fixture_v1(
    bytes: &[u8],
) -> Result<ValidatedCompletenessFixtureV1, FixtureParseErrorV1> {
    if bytes.len() > MAX_FIXTURE_BYTES_V1 {
        return Err(FixtureParseErrorV1::TooLarge {
            maximum: MAX_FIXTURE_BYTES_V1,
        });
    }
    let value = parse_unique_json(bytes).map_err(FixtureParseErrorV1::Json)?;
    let input: FixtureDocumentWire = serde_json::from_value(value)
        .map_err(|error| FixtureParseErrorV1::Json(error.to_string()))?;
    if input.schema_version != FIXTURE_SCHEMA_V1 {
        return Err(FixtureParseErrorV1::SchemaVersion(input.schema_version));
    }
    validate_fixture(&input)?;
    Ok(ValidatedCompletenessFixtureV1 {
        input,
        fixture_document_sha256: raw_digest(bytes),
    })
}

fn validate_fixture(input: &FixtureDocumentWire) -> Result<(), FixtureParseErrorV1> {
    if let Some(fixture) = &input.execution {
        validate_interval(fixture.observed_at, fixture.expires_at)?;
        parse_digest(&fixture.analysis_subject_digest)?;
        validate_identifier(&fixture.venue_id)?;
        validate_identifier(&fixture.account_id)?;
        validate_evidence(&fixture.source_evidence_digests)?;
        if fixture.legs.is_empty() {
            return Err(FixtureParseErrorV1::InvalidFixture(
                "execution legs are empty",
            ));
        }
        if fixture.legs.len() > MAX_EXECUTION_LEGS_V1 {
            return Err(FixtureParseErrorV1::ResourceBound("execution legs"));
        }
        let mut leg_ids = BTreeSet::new();
        let mut state_keys = BTreeSet::new();
        let mut total_levels = 0_usize;
        for leg in &fixture.legs {
            validate_identifier(&leg.leg_id)?;
            validate_identifier(&leg.asset)?;
            parse_digest(&leg.state_key)?;
            if !leg_ids.insert(leg.leg_id.clone()) {
                return Err(FixtureParseErrorV1::DuplicateIdentity(leg.leg_id.clone()));
            }
            if !state_keys.insert(leg.state_key.clone()) {
                return Err(FixtureParseErrorV1::DuplicateIdentity(
                    leg.state_key.clone(),
                ));
            }
            let requested = parse_rational(&leg.requested_quantity)?;
            let reference = parse_rational(&leg.reference_price)?;
            let bound = parse_rational(&leg.price_bound)?;
            let fee_rate = parse_rational(&leg.fee_rate)?;
            let maximum_fee = parse_rational(&leg.maximum_fee)?;
            let maximum_slippage = parse_rational(&leg.maximum_slippage)?;
            if !is_positive(requested)? || !is_positive(reference)? || !is_positive(bound)? {
                return Err(FixtureParseErrorV1::InvalidFixture(
                    "execution quantity and prices must be positive",
                ));
            }
            if leg.deadline < fixture.observed_at {
                return Err(FixtureParseErrorV1::InvalidInterval);
            }
            if is_negative(fee_rate) || is_negative(maximum_fee) || is_negative(maximum_slippage) {
                return Err(FixtureParseErrorV1::InvalidFixture(
                    "execution fee and slippage bounds must be nonnegative",
                ));
            }
            if leg.levels.len() > MAX_BOOK_LEVELS_PER_LEG_V1 {
                return Err(FixtureParseErrorV1::ResourceBound("book levels per leg"));
            }
            total_levels = total_levels
                .checked_add(leg.levels.len())
                .ok_or(FixtureParseErrorV1::ResourceBound("total book levels"))?;
            if total_levels > MAX_EXECUTION_LEGS_V1 * MAX_BOOK_LEVELS_PER_LEG_V1 {
                return Err(FixtureParseErrorV1::ResourceBound("total book levels"));
            }
            let mut level_ids = BTreeSet::new();
            for level in &leg.levels {
                validate_identifier(&level.level_id)?;
                if !level_ids.insert(level.level_id.clone()) {
                    return Err(FixtureParseErrorV1::DuplicateIdentity(
                        level.level_id.clone(),
                    ));
                }
                if !is_positive(parse_rational(&level.price)?)?
                    || !is_positive(parse_rational(&level.quantity)?)?
                {
                    return Err(FixtureParseErrorV1::InvalidFixture(
                        "book level price and quantity must be positive",
                    ));
                }
            }
        }
    }

    if let Some(fixture) = &input.capital {
        validate_interval(fixture.observed_at, fixture.expires_at)?;
        parse_digest(&fixture.analysis_subject_digest)?;
        for value in [
            &fixture.authority_id,
            &fixture.eligible_account,
            &fixture.model_id,
            &fixture.margin_rule_id,
            &fixture.jurisdiction,
        ] {
            validate_identifier(value)?;
        }
        if fixture.model_version == 0 || fixture.liquidation_horizon_seconds == 0 {
            return Err(FixtureParseErrorV1::InvalidFixture(
                "capital model version and horizon must be positive",
            ));
        }
        parse_digest(&fixture.model_digest)?;
        let haircut = parse_rational(&fixture.haircut)?;
        if is_negative(haircut) || haircut.checked_cmp(one()).map_err(exact_parse)?.is_gt() {
            return Err(FixtureParseErrorV1::InvalidFixture(
                "haircut must be in [0,1]",
            ));
        }
        validate_evidence(&fixture.source_evidence_digests)?;
        if fixture.receipts.len() > MAX_CAPITAL_RECEIPTS_V1 {
            return Err(FixtureParseErrorV1::ResourceBound("capital receipts"));
        }
        let mut keys = BTreeSet::new();
        for receipt in &fixture.receipts {
            parse_digest(&receipt.state_key)?;
            parse_digest(&receipt.capital_context_digest)?;
            if !keys.insert(receipt.state_key.clone()) {
                return Err(FixtureParseErrorV1::DuplicateIdentity(
                    receipt.state_key.clone(),
                ));
            }
            let recognized = parse_rational(&receipt.recognized_quantity)?;
            if is_negative(recognized) {
                return Err(FixtureParseErrorV1::InvalidFixture(
                    "recognized quantity must be nonnegative",
                ));
            }
            if receipt.verdict == CapitalVerdictWire::Denied && !recognized.is_zero() {
                return Err(FixtureParseErrorV1::InvalidFixture(
                    "denied capital receipt must recognize zero quantity",
                ));
            }
        }
    }

    if let Some(fixture) = &input.settlement {
        validate_interval(fixture.observed_at, fixture.expires_at)?;
        parse_digest(&fixture.analysis_subject_digest)?;
        validate_identifier(&fixture.source_finality_domain)?;
        validate_identifier(&fixture.destination_finality_domain)?;
        if let Some(value) = &fixture.reversal_rule {
            validate_identifier(value)?;
        }
        if let Some(value) = &fixture.insolvency_rule {
            validate_identifier(value)?;
        }
        validate_evidence(&fixture.source_evidence_digests)?;
        let mut obligations = BTreeSet::new();
        let mut stages = BTreeSet::new();
        for stage in &fixture.stages {
            validate_identifier(&stage.obligation_id)?;
            obligations.insert(stage.obligation_id.clone());
            if !stages.insert((stage.obligation_id.clone(), stage.stage)) {
                return Err(FixtureParseErrorV1::DuplicateIdentity(format!(
                    "{}:{:?}",
                    stage.obligation_id, stage.stage
                )));
            }
        }
        if obligations.len() > MAX_SETTLEMENT_OBLIGATIONS_V1 {
            return Err(FixtureParseErrorV1::ResourceBound("settlement obligations"));
        }
    }

    if let Some(fixture) = &input.assurance {
        validate_interval(fixture.observed_at, fixture.expires_at)?;
        parse_digest(&fixture.analysis_subject_digest)?;
        parse_digest(&fixture.scope_digest)?;
        for value in [&fixture.issuer_id, &fixture.subject_id, &fixture.nonce] {
            validate_identifier(value)?;
        }
        validate_evidence(&fixture.source_evidence_digests)?;
        if fixture.observations.len() > MAX_ASSURANCE_OBSERVATIONS_V1 {
            return Err(FixtureParseErrorV1::ResourceBound("assurance observations"));
        }
        let mut properties = BTreeSet::new();
        for observation in &fixture.observations {
            if !properties.insert(observation.property) {
                return Err(FixtureParseErrorV1::DuplicateIdentity(format!(
                    "{:?}",
                    observation.property
                )));
            }
            validate_roots(&observation.current_roots)?;
            validate_roots(&observation.dependency_roots)?;
        }
    }

    if let Some(fixture) = &input.recovery {
        validate_interval(fixture.observed_at, fixture.expires_at)?;
        parse_digest(&fixture.analysis_subject_digest)?;
        parse_digest(&fixture.recovery_profile_digest)?;
        validate_identifier(&fixture.evidence_preservation_ref)?;
        parse_digest(&fixture.liability_before_digest)?;
        parse_digest(&fixture.liability_after_digest)?;
        validate_evidence(&fixture.source_evidence_digests)?;
        if fixture.paths.len() > MAX_RECOVERY_PATHS_V1 {
            return Err(FixtureParseErrorV1::ResourceBound("recovery paths"));
        }
        let expected: BTreeSet<&str> = REQUIRED_RECOVERY_PATHS.into_iter().collect();
        let mut paths = BTreeSet::new();
        for path in &fixture.paths {
            validate_identifier(&path.path_id)?;
            if !expected.contains(path.path_id.as_str()) {
                return Err(FixtureParseErrorV1::InvalidFixture("unknown recovery path"));
            }
            if !paths.insert(path.path_id.clone()) {
                return Err(FixtureParseErrorV1::DuplicateIdentity(path.path_id.clone()));
            }
            let mut capabilities = BTreeSet::new();
            for capability in &path.capabilities {
                if !capabilities.insert(capability.capability) {
                    return Err(FixtureParseErrorV1::DuplicateIdentity(format!(
                        "{}:{:?}",
                        path.path_id, capability.capability
                    )));
                }
            }
        }
        if fixture.in_flight_items.len() > MAX_IN_FLIGHT_RECOVERY_ITEMS_V1 {
            return Err(FixtureParseErrorV1::ResourceBound(
                "in-flight recovery items",
            ));
        }
        let mut items = BTreeSet::new();
        for item in &fixture.in_flight_items {
            validate_identifier(&item.item_id)?;
            parse_digest(&item.expected_digest)?;
            parse_digest(&item.observed_digest)?;
            if !items.insert(item.item_id.clone()) {
                return Err(FixtureParseErrorV1::DuplicateIdentity(item.item_id.clone()));
            }
        }
        if fixture.canary_stages.len() > MAX_CANARY_STAGES_V1 {
            return Err(FixtureParseErrorV1::ResourceBound("canary stages"));
        }
    }
    Ok(())
}

fn validate_roots(roots: &[RootWire]) -> Result<(), FixtureParseErrorV1> {
    if roots.len() > MAX_CURRENT_OR_DEPENDENCY_ROOTS_V1 {
        return Err(FixtureParseErrorV1::ResourceBound("assurance roots"));
    }
    let mut identities = BTreeSet::new();
    for root in roots {
        validate_identifier(&root.root_id)?;
        if !identities.insert((root.root_class, root.root_id.clone())) {
            return Err(FixtureParseErrorV1::DuplicateIdentity(root.root_id.clone()));
        }
    }
    Ok(())
}

fn validate_evidence(values: &[String]) -> Result<(), FixtureParseErrorV1> {
    if values.len() > MAX_SOURCE_EVIDENCE_DIGESTS_V1 {
        return Err(FixtureParseErrorV1::ResourceBound(
            "source evidence digests",
        ));
    }
    let mut unique = BTreeSet::new();
    for value in values {
        parse_digest(value)?;
        if !unique.insert(value) {
            return Err(FixtureParseErrorV1::DuplicateIdentity(value.clone()));
        }
    }
    Ok(())
}

fn validate_identifier(value: &str) -> Result<(), FixtureParseErrorV1> {
    if value.is_empty()
        || value.len() > 128
        || !value.bytes().all(|byte| (0x21..=0x7e).contains(&byte))
    {
        return Err(FixtureParseErrorV1::InvalidIdentifier(value.to_owned()));
    }
    Ok(())
}

fn validate_interval(observed_at: i64, expires_at: i64) -> Result<(), FixtureParseErrorV1> {
    if observed_at < 0 || expires_at < 0 || observed_at > expires_at {
        return Err(FixtureParseErrorV1::InvalidInterval);
    }
    Ok(())
}

fn parse_digest(value: &str) -> Result<DigestV1, FixtureParseErrorV1> {
    DigestV1::parse(value)
}

fn parse_rational(value: &RationalWire) -> Result<SignedRational, FixtureParseErrorV1> {
    SignedRational::parse(&value.numerator, &value.denominator)
        .map_err(|error| FixtureParseErrorV1::InvalidRational(error.to_string()))
}

fn exact_parse(error: statebook_core::ExactError) -> FixtureParseErrorV1 {
    FixtureParseErrorV1::InvalidRational(error.to_string())
}

fn is_positive(value: SignedRational) -> Result<bool, FixtureParseErrorV1> {
    value
        .checked_cmp(zero())
        .map(|order| order.is_gt())
        .map_err(exact_parse)
}

fn is_negative(value: SignedRational) -> bool {
    value.numerator().is_negative()
}

fn zero() -> SignedRational {
    SignedRational::new(0, 1).expect("canonical zero")
}
fn one() -> SignedRational {
    SignedRational::new(1, 1).expect("canonical one")
}

fn parse_unique_json(bytes: &[u8]) -> Result<Value, String> {
    let mut deserializer = serde_json::Deserializer::from_slice(bytes);
    let value = UniqueValue::deserialize(&mut deserializer).map_err(|error| error.to_string())?;
    deserializer.end().map_err(|error| error.to_string())?;
    Ok(value.0)
}

struct UniqueValue(Value);

impl<'de> Deserialize<'de> for UniqueValue {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        deserializer.deserialize_any(UniqueValueVisitor)
    }
}

struct UniqueValueVisitor;

impl<'de> Visitor<'de> for UniqueValueVisitor {
    type Value = UniqueValue;
    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("a JSON value without duplicate object keys")
    }
    fn visit_bool<E>(self, value: bool) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::Bool(value)))
    }
    fn visit_i64<E>(self, value: i64) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::Number(Number::from(value))))
    }
    fn visit_u64<E>(self, value: u64) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::Number(Number::from(value))))
    }
    fn visit_str<E>(self, value: &str) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::String(value.to_owned())))
    }
    fn visit_string<E>(self, value: String) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::String(value)))
    }
    fn visit_none<E>(self) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::Null))
    }
    fn visit_unit<E>(self) -> Result<Self::Value, E> {
        Ok(UniqueValue(Value::Null))
    }
    fn visit_seq<A>(self, mut sequence: A) -> Result<Self::Value, A::Error>
    where
        A: SeqAccess<'de>,
    {
        let mut values = Vec::new();
        while let Some(value) = sequence.next_element::<UniqueValue>()? {
            values.push(value.0);
        }
        Ok(UniqueValue(Value::Array(values)))
    }
    fn visit_map<A>(self, mut access: A) -> Result<Self::Value, A::Error>
    where
        A: MapAccess<'de>,
    {
        let mut values = Map::new();
        while let Some(key) = access.next_key::<String>()? {
            if values.contains_key(&key) {
                return Err(de::Error::custom(format!("duplicate JSON key: {key}")));
            }
            let value = access.next_value::<UniqueValue>()?;
            values.insert(key, value.0);
        }
        Ok(UniqueValue(Value::Object(values)))
    }
}

fn raw_digest(bytes: &[u8]) -> DigestV1 {
    let digest: [u8; 32] = Sha256::digest(bytes).into();
    DigestV1::from_bytes(digest)
}

fn digest(domain: &[u8], payload: &[u8]) -> DigestV1 {
    let mut hasher = Sha256::new();
    hasher.update(domain);
    hasher.update(1_u16.to_be_bytes());
    hasher.update(payload);
    DigestV1::from_bytes(hasher.finalize().into())
}

fn encode_recovery_profile(profile: &RecoveryPathProfileV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &profile.schema_version.to_be_bytes());
    encoder.field(2, profile.profile_id.as_bytes());
    encoder.field(3, &profile.profile_version.to_be_bytes());
    encoder.field(4, &encode_string_set(&profile.required_path_ids));
    encoder.field(
        5,
        &encode_enum_set(
            profile
                .required_capabilities
                .iter()
                .map(|value| recovery_capability_tag(*value)),
        ),
    );
    encoder.finish()
}

struct Canonical {
    bytes: Vec<u8>,
}

impl Canonical {
    fn new() -> Self {
        Self { bytes: Vec::new() }
    }
    fn field(&mut self, tag: u16, value: &[u8]) {
        self.bytes.extend_from_slice(&tag.to_be_bytes());
        self.bytes.extend_from_slice(
            &u32::try_from(value.len())
                .expect("bounded canonical field")
                .to_be_bytes(),
        );
        self.bytes.extend_from_slice(value);
    }
    fn finish(self) -> Vec<u8> {
        self.bytes
    }
}

fn encode_sequence<I>(values: I) -> Vec<u8>
where
    I: IntoIterator<Item = Vec<u8>>,
{
    let values: Vec<Vec<u8>> = values.into_iter().collect();
    let mut out = Vec::new();
    out.extend_from_slice(
        &u32::try_from(values.len())
            .expect("bounded canonical sequence")
            .to_be_bytes(),
    );
    for value in values {
        out.extend_from_slice(
            &u32::try_from(value.len())
                .expect("bounded canonical item")
                .to_be_bytes(),
        );
        out.extend_from_slice(&value);
    }
    out
}

fn encode_string_set(values: &BTreeSet<String>) -> Vec<u8> {
    encode_sequence(values.iter().map(|value| value.as_bytes().to_vec()))
}

fn encode_enum_set<I>(values: I) -> Vec<u8>
where
    I: IntoIterator<Item = u8>,
{
    encode_sequence(values.into_iter().map(|value| vec![value]))
}

fn encode_digest_set(values: &BTreeSet<DigestV1>) -> Vec<u8> {
    encode_sequence(values.iter().map(|value| value.as_bytes().to_vec()))
}

fn encode_core_digest(value: Sha256Digest) -> Vec<u8> {
    value.as_bytes().to_vec()
}
fn encode_state_key(value: StateKeyV1) -> Vec<u8> {
    value.digest().as_bytes().to_vec()
}
fn encode_rational(value: SignedRational) -> Vec<u8> {
    let mut out = Vec::with_capacity(32);
    out.extend_from_slice(&value.numerator().to_be_bytes());
    out.extend_from_slice(&value.denominator().to_be_bytes());
    out
}
fn encode_optional_rational(value: Option<SignedRational>) -> Vec<u8> {
    match value {
        None => vec![0],
        Some(value) => {
            let mut out = vec![1];
            out.extend_from_slice(&encode_rational(value));
            out
        }
    }
}
fn encode_bool(value: bool) -> Vec<u8> {
    vec![u8::from(value)]
}

pub fn derive_analysis_subject_v1(
    semantic: &SemanticCompletenessReport,
    payoff: &PayoffCompletenessReportV1,
) -> AnalysisSubjectV1 {
    let semantic_report_digest = digest(SEMANTIC_DOMAIN, &encode_semantic_report(semantic));
    let payoff_report_digest = digest(PAYOFF_DOMAIN, &encode_payoff_report(payoff));
    let mut candidate_quantities = BTreeMap::new();
    for receipt in payoff.candidate() {
        candidate_quantities.insert(receipt.state_key(), receipt.quantity());
    }
    let mut encoder = Canonical::new();
    encoder.field(1, semantic_report_digest.as_bytes());
    encoder.field(2, &encode_receipt(payoff.target()));
    encoder.field(
        3,
        &encode_sequence(payoff.candidate().iter().map(encode_receipt)),
    );
    encoder.field(4, payoff.domain_digest().as_bytes());
    encoder.field(5, payoff_report_digest.as_bytes());
    let digest = digest(SUBJECT_DOMAIN, &encoder.finish());
    AnalysisSubjectV1 {
        schema_version: 1,
        digest,
        semantic_report_digest,
        payoff_report_digest,
        candidate_quantities,
    }
}

fn encode_semantic_report(report: &SemanticCompletenessReport) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &[semantic_status_tag(report.status())]);
    encoder.field(
        2,
        &encode_enum_set(
            report
                .missing_terms()
                .iter()
                .map(|value| semantic_field_tag(*value)),
        ),
    );
    encoder.field(
        3,
        &encode_enum_set(
            report
                .unknown_terms()
                .iter()
                .map(|value| semantic_field_tag(*value)),
        ),
    );
    encoder.field(
        4,
        &encode_sequence(
            report
                .unsupported_terms()
                .iter()
                .map(encode_unsupported_term),
        ),
    );
    encoder.field(5, report.source_terms_digest().as_bytes());
    encoder.field(6, report.normalization_profile_digest().as_bytes());
    encoder.finish()
}

fn encode_payoff_report(report: &PayoffCompletenessReportV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &[payoff_status_tag(report.status())]);
    encoder.field(2, &encode_receipt(report.target()));
    encoder.field(
        3,
        &encode_sequence(report.candidate().iter().map(encode_receipt)),
    );
    encoder.field(4, report.domain_digest().as_bytes());
    encoder.field(
        5,
        &encode_sequence(report.states().iter().map(|state| {
            let mut value = Canonical::new();
            value.field(1, state.state_id().as_bytes());
            value.field(2, &encode_rational(state.observation()));
            value.field(3, &encode_state_evaluation(state.status()));
            value.field(
                4,
                &encode_sequence(state.residual_by_asset().iter().map(|(asset, amount)| {
                    let mut item = Canonical::new();
                    item.field(1, asset.as_bytes());
                    item.field(2, &encode_rational(*amount));
                    item.finish()
                })),
            );
            value.finish()
        })),
    );
    encoder.field(
        6,
        &encode_sequence(report.worst_case_by_asset().iter().map(|worst| {
            let mut value = Canonical::new();
            value.field(1, worst.asset().as_bytes());
            value.field(2, &encode_rational(worst.absolute_amount()));
            value.field(3, &encode_string_set(worst.state_ids()));
            value.finish()
        })),
    );
    encoder.field(
        7,
        &encode_enum_set(
            report
                .assumptions()
                .iter()
                .map(|value| payoff_assumption_tag(*value)),
        ),
    );
    encoder.field(
        8,
        &encode_enum_set(
            report
                .unmodeled_residual_classes()
                .iter()
                .map(|value| unmodeled_tag(*value)),
        ),
    );
    encoder.field(9, &encode_string_set(report.explicit_non_equivalences()));
    encoder.finish()
}

fn encode_receipt(receipt: &AggregatedPositionReceiptV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &encode_state_key(receipt.state_key()));
    encoder.field(
        2,
        &encode_sequence(
            receipt
                .validated_contract_digests()
                .iter()
                .map(|value| encode_core_digest(*value)),
        ),
    );
    encoder.field(3, &encode_rational(receipt.quantity()));
    encoder.finish()
}

fn encode_state_evaluation(status: &StateEvaluationStatusV1) -> Vec<u8> {
    match status {
        StateEvaluationStatusV1::Evaluated => vec![1],
        StateEvaluationStatusV1::Unsupported { reasons } => {
            let mut out = vec![2];
            out.extend_from_slice(&encode_sequence(
                reasons.iter().map(encode_unsupported_reason),
            ));
            out
        }
    }
}

fn encode_unsupported_reason(reason: &UnsupportedStateReasonV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    match reason {
        UnsupportedStateReasonV1::ObservationCoordinateMismatch {
            leg_state_key,
            differing_fields,
        } => {
            encoder.field(1, &[1]);
            encoder.field(2, &encode_state_key(*leg_state_key));
            encoder.field(
                3,
                &encode_enum_set(
                    differing_fields
                        .iter()
                        .map(|value| semantic_field_tag(*value)),
                ),
            );
        }
        UnsupportedStateReasonV1::ExactArithmeticOverflow { leg_state_key } => {
            encoder.field(1, &[2]);
            encoder.field(2, &encode_state_key(*leg_state_key));
        }
        UnsupportedStateReasonV1::PortfolioAggregationOverflow {
            leg_state_key,
            validated_contract_digests,
        } => {
            encoder.field(1, &[3]);
            encoder.field(2, &encode_state_key(*leg_state_key));
            encoder.field(
                3,
                &encode_sequence(
                    validated_contract_digests
                        .iter()
                        .map(|value| encode_core_digest(*value)),
                ),
            );
        }
        UnsupportedStateReasonV1::ResidualComparisonOverflow { asset } => {
            encoder.field(1, &[4]);
            encoder.field(2, asset.as_bytes());
        }
    }
    encoder.finish()
}

fn encode_unsupported_term(value: &UnsupportedTerm) -> Vec<u8> {
    let (tag, text) = match value {
        UnsupportedTerm::PayoffForm(text) => (1, text),
        UnsupportedTerm::Comparator(text) => (2, text),
        UnsupportedTerm::ComparatorShape(text) => (3, text),
        UnsupportedTerm::RoundingMode(text) => (4, text),
    };
    let mut encoder = Canonical::new();
    encoder.field(1, &[tag]);
    encoder.field(2, text.as_bytes());
    encoder.finish()
}

fn semantic_status_tag(value: SemanticCompletenessStatus) -> u8 {
    match value {
        SemanticCompletenessStatus::Complete => 1,
        SemanticCompletenessStatus::Incomplete => 2,
        SemanticCompletenessStatus::Unknown => 3,
    }
}
fn payoff_status_tag(value: PayoffCompletenessStatusV1) -> u8 {
    match value {
        PayoffCompletenessStatusV1::ExactOnDeclaredDomain => 1,
        PayoffCompletenessStatusV1::ApproximateOnDeclaredDomain => 2,
        PayoffCompletenessStatusV1::Incomplete => 3,
    }
}
fn payoff_assumption_tag(value: PayoffAssumptionV1) -> u8 {
    match value {
        PayoffAssumptionV1::FiniteDeclaredDomainOnly => 1,
        PayoffAssumptionV1::ObservationIsFinalCorrectedNormalizedValue => 2,
        PayoffAssumptionV1::ContractRoundingPrecedesPositionQuantity => 3,
        PayoffAssumptionV1::NoAssetConversion => 4,
    }
}
fn unmodeled_tag(value: UnmodeledResidualClassV1) -> u8 {
    match value {
        UnmodeledResidualClassV1::BasisOutsideNormalizedReference => 1,
        UnmodeledResidualClassV1::TimingOutsideTerminalObservation => 2,
        UnmodeledResidualClassV1::FxConversion => 3,
        UnmodeledResidualClassV1::DefaultRealization => 4,
        UnmodeledResidualClassV1::LegalEnforceability => 5,
        UnmodeledResidualClassV1::Liquidity => 6,
        UnmodeledResidualClassV1::JumpBetweenDeclaredStates => 7,
        UnmodeledResidualClassV1::ModelOutsideDeclaredDomain => 8,
    }
}
fn semantic_field_tag(value: SemanticField) -> u8 {
    match value {
        SemanticField::VenueNamespace => 1,
        SemanticField::SourceContractId => 2,
        SemanticField::SourceRevision => 3,
        SemanticField::SourceObservedAt => 4,
        SemanticField::ReferenceNamespace => 5,
        SemanticField::ReferenceIdentifier => 6,
        SemanticField::ReferenceUnit => 7,
        SemanticField::BenchmarkAdministrator => 8,
        SemanticField::MethodologyVersion => 9,
        SemanticField::MethodologySha256 => 10,
        SemanticField::FallbackRule => 11,
        SemanticField::Calendar => 12,
        SemanticField::Timezone => 13,
        SemanticField::ObservationStart => 14,
        SemanticField::ObservationEnd => 15,
        SemanticField::SamplingRule => 16,
        SemanticField::DisruptionRule => 17,
        SemanticField::CorrectionRule => 18,
        SemanticField::PayoffKind => 19,
        SemanticField::Comparator => 20,
        SemanticField::PayoffAmount => 21,
        SemanticField::SettlementAsset => 22,
        SemanticField::SettlementUnitScale => 23,
        SemanticField::RoundingMode => 24,
        SemanticField::RoundingQuantum => 25,
        SemanticField::SettlementDeadline => 26,
        SemanticField::DisputeRule => 27,
        SemanticField::DefaultRule => 28,
        SemanticField::GoverningRule => 29,
        SemanticField::FinalityDomain => 30,
        SemanticField::ExplicitNonEquivalences => 31,
    }
}
fn recovery_capability_tag(value: RecoveryCapabilityV1) -> u8 {
    match value {
        RecoveryCapabilityV1::StopExternalization => 1,
        RecoveryCapabilityV1::ReconcileEveryInFlightItem => 2,
        RecoveryCapabilityV1::PreserveEvidence => 3,
        RecoveryCapabilityV1::RestoreLiabilitiesWithoutDuplication => 4,
        RecoveryCapabilityV1::ReopenThroughBoundedCanaryStages => 5,
    }
}

pub fn compose_completeness_reports_v1(
    semantic: &SemanticCompletenessReport,
    payoff: &PayoffCompletenessReportV1,
    fixture: &ValidatedCompletenessFixtureV1,
    evaluated_at: i64,
) -> Result<SevenCompletenessReportsV1, CompletenessEvaluationErrorV1> {
    if evaluated_at < 0 {
        return Err(CompletenessEvaluationErrorV1::InvalidEvaluationTime);
    }
    let subject = derive_analysis_subject_v1(semantic, payoff);
    let profile = RecoveryPathProfileV1::statebook_externalization_v1();
    validate_bindings(&fixture.input, subject.digest(), profile.digest())?;
    let execution = evaluate_execution(fixture.input.execution.as_ref(), &subject, evaluated_at)?;
    let capital = evaluate_capital(fixture.input.capital.as_ref(), &subject, evaluated_at)?;
    let settlement =
        evaluate_settlement(fixture.input.settlement.as_ref(), &subject, evaluated_at)?;
    let assurance = evaluate_assurance(fixture.input.assurance.as_ref(), &subject, evaluated_at)?;
    let recovery = evaluate_recovery(
        fixture.input.recovery.as_ref(),
        &subject,
        &profile,
        evaluated_at,
    )?;
    let mut encoder = Canonical::new();
    encoder.field(1, subject.digest().as_bytes());
    encoder.field(2, &evaluated_at.to_be_bytes());
    encoder.field(3, profile.digest().as_bytes());
    encoder.field(4, subject.semantic_report_digest().as_bytes());
    encoder.field(5, subject.payoff_report_digest().as_bytes());
    encoder.field(6, execution.report_digest().as_bytes());
    encoder.field(7, capital.report_digest().as_bytes());
    encoder.field(8, settlement.report_digest().as_bytes());
    encoder.field(9, assurance.report_digest().as_bytes());
    encoder.field(10, recovery.report_digest().as_bytes());
    let composition_digest = digest(COMPOSITION_DOMAIN, &encoder.finish());
    Ok(SevenCompletenessReportsV1 {
        schema_version: 1,
        analysis_subject: subject.clone(),
        semantic: semantic.clone(),
        semantic_report_digest: subject.semantic_report_digest(),
        payoff: payoff.clone(),
        payoff_report_digest: subject.payoff_report_digest(),
        execution,
        capital,
        settlement,
        assurance,
        recovery,
        recovery_profile_digest: profile.digest(),
        evaluated_at,
        fixture_document_sha256: fixture.fixture_document_sha256,
        composition_digest,
    })
}

fn validate_bindings(
    input: &FixtureDocumentWire,
    subject: DigestV1,
    profile: DigestV1,
) -> Result<(), CompletenessEvaluationErrorV1> {
    for value in [
        input
            .execution
            .as_ref()
            .map(|value| value.analysis_subject_digest.as_str()),
        input
            .capital
            .as_ref()
            .map(|value| value.analysis_subject_digest.as_str()),
        input
            .settlement
            .as_ref()
            .map(|value| value.analysis_subject_digest.as_str()),
        input
            .assurance
            .as_ref()
            .map(|value| value.analysis_subject_digest.as_str()),
        input
            .recovery
            .as_ref()
            .map(|value| value.analysis_subject_digest.as_str()),
    ]
    .into_iter()
    .flatten()
    {
        if DigestV1::parse(value)
            .map_err(|_| CompletenessEvaluationErrorV1::SubjectDigestMismatch)?
            != subject
        {
            return Err(CompletenessEvaluationErrorV1::SubjectDigestMismatch);
        }
    }
    if let Some(recovery) = &input.recovery {
        if DigestV1::parse(&recovery.recovery_profile_digest)
            .map_err(|_| CompletenessEvaluationErrorV1::RecoveryProfileDigestMismatch)?
            != profile
        {
            return Err(CompletenessEvaluationErrorV1::RecoveryProfileDigestMismatch);
        }
    }
    Ok(())
}

fn base_assumptions(extra: Option<CompletenessAssumptionV1>) -> BTreeSet<CompletenessAssumptionV1> {
    let mut values = BTreeSet::from([
        CompletenessAssumptionV1::HermeticFixtureOnly,
        CompletenessAssumptionV1::NoLiveAuthority,
        CompletenessAssumptionV1::NoCrossDimensionInference,
        CompletenessAssumptionV1::FixedWidthExactArithmetic,
    ]);
    if let Some(extra) = extra {
        values.insert(extra);
    }
    values
}

fn evidence(values: &[String]) -> BTreeSet<DigestV1> {
    values
        .iter()
        .map(|value| DigestV1::parse(value).expect("validated digest"))
        .collect()
}

fn missing_facts(
    dimension: CompletenessDimensionV1,
    reasons: &BTreeSet<CompletenessReasonV1>,
) -> BTreeSet<CompletenessMissingFactV1> {
    let mut facts = BTreeSet::new();
    for reason in reasons {
        match reason {
            CompletenessReasonV1::MissingFixture => {
                facts.insert(CompletenessMissingFactV1::Fixture);
            }
            CompletenessReasonV1::StaleOrFutureObservation => {
                facts.insert(CompletenessMissingFactV1::CurrentObservation);
            }
            CompletenessReasonV1::MissingObservation => {
                facts.insert(match dimension {
                    CompletenessDimensionV1::Execution => {
                        CompletenessMissingFactV1::RequiredExecutionLeg
                    }
                    CompletenessDimensionV1::Capital => {
                        CompletenessMissingFactV1::RequiredCapitalReceipt
                    }
                    CompletenessDimensionV1::Settlement => {
                        CompletenessMissingFactV1::SettlementPolicyOrStage
                    }
                    CompletenessDimensionV1::Assurance => {
                        CompletenessMissingFactV1::AssuranceProperty
                    }
                    CompletenessDimensionV1::Recovery => {
                        CompletenessMissingFactV1::InFlightReconciliation
                    }
                });
            }
            CompletenessReasonV1::MissingAssuranceProperty
            | CompletenessReasonV1::UnknownAssuranceVerdict => {
                facts.insert(CompletenessMissingFactV1::AssuranceProperty);
            }
            CompletenessReasonV1::MissingCurrentRoot => {
                facts.insert(CompletenessMissingFactV1::CurrentAssuranceRoot);
            }
            CompletenessReasonV1::UnknownDependencyAncestry => {
                facts.insert(CompletenessMissingFactV1::DependencyAncestry);
            }
            CompletenessReasonV1::MissingRecoveryPath => {
                facts.insert(CompletenessMissingFactV1::RecoveryPath);
            }
            CompletenessReasonV1::MissingRecoveryCapability => {
                facts.insert(CompletenessMissingFactV1::RecoveryCapability);
            }
            CompletenessReasonV1::MissingOrFailedCanary => {
                facts.insert(CompletenessMissingFactV1::CanaryStage);
            }
            _ => {}
        }
    }
    facts
}

fn absent_meta(
    subject: DigestV1,
    evaluated_at: i64,
    dimension: CompletenessDimensionV1,
    extra: Option<CompletenessAssumptionV1>,
) -> ReportMetaV1 {
    let reasons = BTreeSet::from([CompletenessReasonV1::MissingFixture]);
    ReportMetaV1 {
        schema_version: 1,
        dimension,
        analysis_subject_digest: subject,
        fixture_digest: None,
        evidence_class: EvidenceClassV1::HermeticFixtureOnly,
        source_evidence_digests: BTreeSet::new(),
        assumptions: base_assumptions(extra),
        missing_facts: missing_facts(dimension, &reasons),
        reasons,
        evaluated_at,
        expires_at: None,
        report_digest: DigestV1([0; 32]),
    }
}

fn present_meta(
    subject: DigestV1,
    dimension: CompletenessDimensionV1,
    fixture_digest: DigestV1,
    source_evidence_digests: BTreeSet<DigestV1>,
    reasons: BTreeSet<CompletenessReasonV1>,
    evaluated_at: i64,
    expires_at: i64,
) -> ReportMetaV1 {
    let extra = match dimension {
        CompletenessDimensionV1::Assurance => {
            Some(CompletenessAssumptionV1::CurrentRootsDisclosedNotResolved)
        }
        CompletenessDimensionV1::Recovery => {
            Some(CompletenessAssumptionV1::VersionedRecoveryProfileOnly)
        }
        _ => None,
    };
    let missing_facts = missing_facts(dimension, &reasons);
    ReportMetaV1 {
        schema_version: 1,
        dimension,
        analysis_subject_digest: subject,
        fixture_digest: Some(fixture_digest),
        evidence_class: EvidenceClassV1::HermeticFixtureOnly,
        source_evidence_digests,
        assumptions: base_assumptions(extra),
        reasons,
        missing_facts,
        evaluated_at,
        expires_at: Some(expires_at),
        report_digest: DigestV1([0; 32]),
    }
}

fn current(observed_at: i64, expires_at: i64, evaluated_at: i64) -> bool {
    observed_at <= evaluated_at && evaluated_at <= expires_at
}

fn evaluate_execution(
    fixture: Option<&ExecutionFixtureWire>,
    subject: &AnalysisSubjectV1,
    evaluated_at: i64,
) -> Result<ExecutionCompletenessReportV1, CompletenessEvaluationErrorV1> {
    let Some(fixture) = fixture else {
        let mut report = ExecutionCompletenessReportV1 {
            meta: absent_meta(
                subject.digest(),
                evaluated_at,
                CompletenessDimensionV1::Execution,
                None,
            ),
            status: ExecutionCompletenessStatusV1::NotObserved,
            legs: Vec::new(),
            context: None,
        };
        report.meta.report_digest =
            digest(EXECUTION_REPORT_DOMAIN, &encode_execution_report(&report));
        return Ok(report);
    };
    let fixture_digest = digest(EXECUTION_FIXTURE_DOMAIN, &encode_execution_fixture(fixture));
    let mut reasons = BTreeSet::new();
    let mut legs = Vec::new();
    let is_current = current(fixture.observed_at, fixture.expires_at, evaluated_at);
    if !is_current {
        reasons.insert(CompletenessReasonV1::StaleOrFutureObservation);
    }
    let mut has_unknown = false;
    let mut has_unsupported = false;
    let mut has_zero = false;
    let mut has_partial = false;
    let mut presented_keys = BTreeSet::new();
    for leg in &fixture.legs {
        let state_key = find_candidate_key(&leg.state_key, subject)?;
        presented_keys.insert(state_key);
        let required = subject
            .candidate_quantities
            .get(&state_key)
            .ok_or(CompletenessEvaluationErrorV1::UnknownReceipt)?;
        let requested = exact(&leg.requested_quantity)?;
        let required_magnitude = required.checked_abs().map_err(arithmetic)?;
        let side_matches = (required.numerator().is_positive() && leg.side == SideWire::Buy)
            || (required.numerator().is_negative() && leg.side == SideWire::Sell);
        if requested != required_magnitude || !side_matches || required.is_zero() {
            return Err(CompletenessEvaluationErrorV1::UnknownReceipt);
        }
        has_unknown |= matches!(leg.queue, SupportWire::Unknown)
            || matches!(leg.atomicity, SupportWire::Unknown)
            || matches!(leg.leg_failure_model, SupportWire::Unknown);
        has_unsupported |= matches!(leg.queue, SupportWire::Unsupported)
            || matches!(leg.atomicity, SupportWire::Unsupported)
            || matches!(leg.leg_failure_model, SupportWire::Unsupported);
        let result = evaluate_execution_leg(leg)?;
        has_zero |= result.executable_quantity.is_zero();
        has_partial |= result.executable_quantity != result.requested_quantity;
        legs.push(result);
    }
    if presented_keys != subject.candidate_quantities.keys().copied().collect() {
        has_unknown = true;
        reasons.insert(CompletenessReasonV1::MissingObservation);
    }
    legs.sort_by(|a, b| a.leg_id.cmp(&b.leg_id));
    let status =
        if !is_current || has_unknown || fixture.legs.iter().any(|leg| evaluated_at > leg.deadline)
        {
            reasons.insert(CompletenessReasonV1::MissingObservation);
            ExecutionCompletenessStatusV1::NotObserved
        } else if has_unsupported || has_zero {
            reasons.insert(if has_unsupported {
                CompletenessReasonV1::ExplicitlyUnsupported
            } else {
                CompletenessReasonV1::ZeroExecutableQuantity
            });
            ExecutionCompletenessStatusV1::NotExecutableInFixture
        } else if has_partial {
            reasons.insert(CompletenessReasonV1::PartialQuantity);
            ExecutionCompletenessStatusV1::PartiallyExecutableInFixture
        } else {
            ExecutionCompletenessStatusV1::ExecutableInFixture
        };
    let mut report = ExecutionCompletenessReportV1 {
        meta: present_meta(
            subject.digest(),
            CompletenessDimensionV1::Execution,
            fixture_digest,
            evidence(&fixture.source_evidence_digests),
            reasons,
            evaluated_at,
            fixture.expires_at,
        ),
        status,
        legs,
        context: Some(ExecutionContextV1 {
            venue_id: fixture.venue_id.clone(),
            account_id: fixture.account_id.clone(),
            observed_at: fixture.observed_at,
        }),
    };
    report.meta.report_digest = digest(EXECUTION_REPORT_DOMAIN, &encode_execution_report(&report));
    Ok(report)
}

fn find_candidate_key(
    value: &str,
    subject: &AnalysisSubjectV1,
) -> Result<StateKeyV1, CompletenessEvaluationErrorV1> {
    subject
        .candidate_quantities
        .keys()
        .find(|key| key.to_hex() == value)
        .copied()
        .ok_or(CompletenessEvaluationErrorV1::UnknownReceipt)
}

fn evaluate_execution_leg(
    leg: &ExecutionLegWire,
) -> Result<ExecutionLegResultV1, CompletenessEvaluationErrorV1> {
    let requested = exact(&leg.requested_quantity)?;
    let reference = exact(&leg.reference_price)?;
    let price_bound = exact(&leg.price_bound)?;
    let fee_rate = exact(&leg.fee_rate)?;
    let maximum_fee = exact(&leg.maximum_fee)?;
    let maximum_slippage = exact(&leg.maximum_slippage)?;
    let mut levels: Vec<(&BookLevelWire, SignedRational, SignedRational)> = leg
        .levels
        .iter()
        .map(|level| Ok((level, exact(&level.price)?, exact(&level.quantity)?)))
        .collect::<Result<_, CompletenessEvaluationErrorV1>>()?;
    sort_levels(&mut levels, leg.side)?;
    let mut quantity = zero();
    let mut notional = zero();
    let mut fee = zero();
    let mut worst_price = None;
    let slip_bound = match leg.side {
        SideWire::Buy => reference
            .checked_mul(one().checked_add(maximum_slippage).map_err(arithmetic)?)
            .map_err(arithmetic)?,
        SideWire::Sell => reference
            .checked_mul(one().checked_sub(maximum_slippage).map_err(arithmetic)?)
            .map_err(arithmetic)?,
    };
    for (_, price, available) in levels {
        let price_ok = match leg.side {
            SideWire::Buy => !price.checked_cmp(price_bound).map_err(arithmetic)?.is_gt(),
            SideWire::Sell => !price.checked_cmp(price_bound).map_err(arithmetic)?.is_lt(),
        };
        if !price_ok {
            break;
        }
        let remaining = requested.checked_sub(quantity).map_err(arithmetic)?;
        if remaining.is_zero() {
            break;
        }
        let mut allowed = min_exact(remaining, available)?;
        if !fee_rate.is_zero() {
            let fee_per_quantity = fee_rate.checked_mul(price).map_err(arithmetic)?;
            let fee_remaining = maximum_fee.checked_sub(fee).map_err(arithmetic)?;
            if fee_remaining.numerator().is_negative() {
                allowed = zero();
            } else {
                allowed = min_exact(
                    allowed,
                    fee_remaining
                        .checked_div(fee_per_quantity)
                        .map_err(arithmetic)?,
                )?;
            }
        }
        let tentative_quantity = quantity.checked_add(allowed).map_err(arithmetic)?;
        let tentative_notional = notional
            .checked_add(price.checked_mul(allowed).map_err(arithmetic)?)
            .map_err(arithmetic)?;
        let violates_slippage = match leg.side {
            SideWire::Buy => tentative_notional
                .checked_cmp(
                    slip_bound
                        .checked_mul(tentative_quantity)
                        .map_err(arithmetic)?,
                )
                .map_err(arithmetic)?
                .is_gt(),
            SideWire::Sell => tentative_notional
                .checked_cmp(
                    slip_bound
                        .checked_mul(tentative_quantity)
                        .map_err(arithmetic)?,
                )
                .map_err(arithmetic)?
                .is_lt(),
        };
        if violates_slippage {
            let numerator = match leg.side {
                SideWire::Buy => slip_bound
                    .checked_mul(quantity)
                    .map_err(arithmetic)?
                    .checked_sub(notional)
                    .map_err(arithmetic)?,
                SideWire::Sell => notional
                    .checked_sub(slip_bound.checked_mul(quantity).map_err(arithmetic)?)
                    .map_err(arithmetic)?,
            };
            let denominator = match leg.side {
                SideWire::Buy => price.checked_sub(slip_bound),
                SideWire::Sell => slip_bound.checked_sub(price),
            }
            .map_err(arithmetic)?;
            let slip_allowed = if numerator.numerator().is_negative() {
                zero()
            } else {
                numerator.checked_div(denominator).map_err(arithmetic)?
            };
            allowed = min_exact(allowed, slip_allowed)?;
        }
        if allowed.is_zero() {
            break;
        }
        let added_notional = price.checked_mul(allowed).map_err(arithmetic)?;
        quantity = quantity.checked_add(allowed).map_err(arithmetic)?;
        notional = notional.checked_add(added_notional).map_err(arithmetic)?;
        fee = fee
            .checked_add(fee_rate.checked_mul(added_notional).map_err(arithmetic)?)
            .map_err(arithmetic)?;
        worst_price = Some(price);
    }
    let average_price = if quantity.is_zero() {
        None
    } else {
        Some(notional.checked_div(quantity).map_err(arithmetic)?)
    };
    let slippage = match average_price {
        None => None,
        Some(average) => Some(
            match leg.side {
                SideWire::Buy => average.checked_sub(reference),
                SideWire::Sell => reference.checked_sub(average),
            }
            .map_err(arithmetic)?
            .checked_div(reference)
            .map_err(arithmetic)?,
        ),
    };
    Ok(ExecutionLegResultV1 {
        leg_id: leg.leg_id.clone(),
        asset: leg.asset.clone(),
        requested_quantity: requested,
        executable_quantity: quantity,
        unfilled_quantity: requested.checked_sub(quantity).map_err(arithmetic)?,
        gross_notional: notional,
        average_price,
        worst_price,
        fee,
        slippage,
        side: leg.side.into(),
        reference_price: reference,
        price_bound,
        fee_rate,
        maximum_fee,
        maximum_slippage,
        queue: leg.queue.into(),
        atomicity: leg.atomicity.into(),
        leg_failure_model: leg.leg_failure_model.into(),
        deadline: leg.deadline,
    })
}

fn sort_levels(
    levels: &mut [(&BookLevelWire, SignedRational, SignedRational)],
    side: SideWire,
) -> Result<(), CompletenessEvaluationErrorV1> {
    for left in 0..levels.len() {
        for right in (left + 1)..levels.len() {
            let order = levels[left]
                .1
                .checked_cmp(levels[right].1)
                .map_err(arithmetic)?;
            let should_swap = match side {
                SideWire::Buy => order.is_gt(),
                SideWire::Sell => order.is_lt(),
            } || (order.is_eq()
                && levels[left].0.level_id > levels[right].0.level_id);
            if should_swap {
                levels.swap(left, right);
            }
        }
    }
    Ok(())
}

fn min_exact(
    left: SignedRational,
    right: SignedRational,
) -> Result<SignedRational, CompletenessEvaluationErrorV1> {
    Ok(if left.checked_cmp(right).map_err(arithmetic)?.is_gt() {
        right
    } else {
        left
    })
}

fn exact(value: &RationalWire) -> Result<SignedRational, CompletenessEvaluationErrorV1> {
    SignedRational::parse(&value.numerator, &value.denominator).map_err(arithmetic)
}

fn arithmetic(_: statebook_core::ExactError) -> CompletenessEvaluationErrorV1 {
    CompletenessEvaluationErrorV1::ArithmeticOverflow
}

fn evaluate_capital(
    fixture: Option<&CapitalFixtureWire>,
    subject: &AnalysisSubjectV1,
    evaluated_at: i64,
) -> Result<CapitalCompletenessReportV1, CompletenessEvaluationErrorV1> {
    let Some(fixture) = fixture else {
        let mut report = CapitalCompletenessReportV1 {
            meta: absent_meta(
                subject.digest(),
                evaluated_at,
                CompletenessDimensionV1::Capital,
                None,
            ),
            status: CapitalCompletenessStatusV1::NotEvaluated,
            receipts: Vec::new(),
            context: None,
        };
        report.meta.report_digest = digest(CAPITAL_REPORT_DOMAIN, &encode_capital_report(&report));
        return Ok(report);
    };
    let fixture_digest = digest(CAPITAL_FIXTURE_DOMAIN, &encode_capital_fixture(fixture));
    let capital_context_digest = digest(CAPITAL_CONTEXT_DOMAIN, &encode_capital_context(fixture));
    let mut reasons = BTreeSet::new();
    let mut results = Vec::new();
    let mut denied = 0_usize;
    let mut full = 0_usize;
    for receipt in &fixture.receipts {
        if parse_digest(&receipt.capital_context_digest).expect("validated")
            != capital_context_digest
        {
            return Err(CompletenessEvaluationErrorV1::CapitalContextDigestMismatch);
        }
        let state_key = find_candidate_key(&receipt.state_key, subject)?;
        let required = *subject
            .candidate_quantities
            .get(&state_key)
            .ok_or(CompletenessEvaluationErrorV1::UnknownReceipt)?;
        let recognized = exact(&receipt.recognized_quantity)?;
        let required_magnitude = required.checked_abs().map_err(arithmetic)?;
        if receipt.verdict == CapitalVerdictWire::Denied {
            denied += 1;
        } else if recognized == required_magnitude {
            full += 1;
        }
        results.push(CapitalReceiptResultV1 {
            state_key,
            required_quantity: required,
            recognized_quantity: recognized,
            recognition_residual: required_magnitude
                .checked_sub(recognized)
                .map_err(arithmetic)?,
            capital_context_digest,
            verdict: receipt.verdict.into(),
        });
    }
    results.sort_by_key(|value| value.state_key);
    let current = current(fixture.observed_at, fixture.expires_at, evaluated_at);
    let status = if !current {
        reasons.insert(CompletenessReasonV1::StaleOrFutureObservation);
        CapitalCompletenessStatusV1::NotEvaluated
    } else if subject.candidate_quantities.is_empty() || fixture.receipts.is_empty() {
        reasons.insert(CompletenessReasonV1::MissingObservation);
        CapitalCompletenessStatusV1::NotEvaluated
    } else if !subject.candidate_quantities.is_empty()
        && denied == subject.candidate_quantities.len()
        && results.len() == subject.candidate_quantities.len()
    {
        reasons.insert(CompletenessReasonV1::ExplicitDenial);
        CapitalCompletenessStatusV1::NotRecognizedInFixture
    } else if results.len() != subject.candidate_quantities.len()
        || full != subject.candidate_quantities.len()
    {
        reasons.insert(CompletenessReasonV1::PartialRecognition);
        CapitalCompletenessStatusV1::PartiallyRecognizedInFixture
    } else {
        CapitalCompletenessStatusV1::RecognizedInFixture
    };
    let mut report = CapitalCompletenessReportV1 {
        meta: present_meta(
            subject.digest(),
            CompletenessDimensionV1::Capital,
            fixture_digest,
            evidence(&fixture.source_evidence_digests),
            reasons,
            evaluated_at,
            fixture.expires_at,
        ),
        status,
        receipts: results,
        context: Some(CapitalContextV1 {
            authority_id: fixture.authority_id.clone(),
            eligible_account: fixture.eligible_account.clone(),
            model_id: fixture.model_id.clone(),
            model_version: fixture.model_version,
            model_digest: parse_digest(&fixture.model_digest).expect("validated"),
            haircut: exact(&fixture.haircut)?,
            margin_rule_id: fixture.margin_rule_id.clone(),
            jurisdiction: fixture.jurisdiction.clone(),
            liquidation_horizon_seconds: fixture.liquidation_horizon_seconds,
            observed_at: fixture.observed_at,
            capital_context_digest,
        }),
    };
    report.meta.report_digest = digest(CAPITAL_REPORT_DOMAIN, &encode_capital_report(&report));
    Ok(report)
}

fn evaluate_settlement(
    fixture: Option<&SettlementFixtureWire>,
    subject: &AnalysisSubjectV1,
    evaluated_at: i64,
) -> Result<SettlementCompletenessReportV1, CompletenessEvaluationErrorV1> {
    let Some(fixture) = fixture else {
        let mut report = SettlementCompletenessReportV1 {
            meta: absent_meta(
                subject.digest(),
                evaluated_at,
                CompletenessDimensionV1::Settlement,
                None,
            ),
            status: SettlementCompletenessStatusV1::Unknown,
            stages: Vec::new(),
            context: None,
        };
        report.meta.report_digest =
            digest(SETTLEMENT_REPORT_DOMAIN, &encode_settlement_report(&report));
        return Ok(report);
    };
    let fixture_digest = digest(
        SETTLEMENT_FIXTURE_DOMAIN,
        &encode_settlement_fixture(fixture),
    );
    let mut reasons = BTreeSet::new();
    let mut stages: Vec<_> = fixture
        .stages
        .iter()
        .map(|value| SettlementStageObservationV1 {
            obligation_id: value.obligation_id.clone(),
            stage: value.stage,
            verdict: value.verdict,
        })
        .collect();
    stages.sort_by(|a, b| {
        a.obligation_id
            .cmp(&b.obligation_id)
            .then(a.stage.cmp(&b.stage))
    });
    let required: BTreeSet<_> = [
        SettlementStageV1::SourceObservation,
        SettlementStageV1::SourceFinality,
        SettlementStageV1::DestinationObservation,
        SettlementStageV1::DestinationFinality,
        SettlementStageV1::OperationalReconciliation,
        SettlementStageV1::LegalFinality,
    ]
    .into_iter()
    .collect();
    let obligation_ids: BTreeSet<_> = stages
        .iter()
        .map(|value| value.obligation_id.clone())
        .collect();
    let complete_stage_coverage = !obligation_ids.is_empty()
        && obligation_ids.iter().all(|obligation_id| {
            stages
                .iter()
                .filter(|value| &value.obligation_id == obligation_id)
                .map(|value| value.stage)
                .collect::<BTreeSet<_>>()
                == required
        });
    let status = if !current(fixture.observed_at, fixture.expires_at, evaluated_at) {
        reasons.insert(CompletenessReasonV1::StaleOrFutureObservation);
        SettlementCompletenessStatusV1::Unknown
    } else if fixture.disputed || fixture.reversed || fixture.reconciliation_mismatch {
        reasons.insert(CompletenessReasonV1::DisputedOrReversed);
        SettlementCompletenessStatusV1::DisputedInFixture
    } else if !fixture.domains_compatible || !fixture.transition_supported {
        reasons.insert(CompletenessReasonV1::IncompatibleFinalityDomain);
        SettlementCompletenessStatusV1::UnsupportedInFixture
    } else if !complete_stage_coverage
        || fixture.reversal_rule.is_none()
        || fixture.insolvency_rule.is_none()
        || stages
            .iter()
            .any(|value| value.verdict == StageVerdictV1::Unknown)
    {
        reasons.insert(CompletenessReasonV1::MissingObservation);
        SettlementCompletenessStatusV1::Unknown
    } else if stages.iter().any(|value| {
        value.verdict == StageVerdictV1::Pending
            || (value.verdict == StageVerdictV1::Conditional
                && value.stage != SettlementStageV1::LegalFinality)
    }) {
        reasons.insert(CompletenessReasonV1::PendingStage);
        SettlementCompletenessStatusV1::PendingInFixture
    } else if stages.iter().any(|value| {
        value.stage == SettlementStageV1::LegalFinality
            && value.verdict == StageVerdictV1::Conditional
    }) {
        reasons.insert(CompletenessReasonV1::ConditionalLegalFinality);
        SettlementCompletenessStatusV1::ConditionalInFixture
    } else {
        SettlementCompletenessStatusV1::FinalInFixture
    };
    let mut report = SettlementCompletenessReportV1 {
        meta: present_meta(
            subject.digest(),
            CompletenessDimensionV1::Settlement,
            fixture_digest,
            evidence(&fixture.source_evidence_digests),
            reasons,
            evaluated_at,
            fixture.expires_at,
        ),
        status,
        stages,
        context: Some(SettlementContextV1 {
            source_finality_domain: fixture.source_finality_domain.clone(),
            destination_finality_domain: fixture.destination_finality_domain.clone(),
            domains_compatible: fixture.domains_compatible,
            transition_supported: fixture.transition_supported,
            reversal_rule: fixture.reversal_rule.clone(),
            insolvency_rule: fixture.insolvency_rule.clone(),
            disputed: fixture.disputed,
            reversed: fixture.reversed,
            reconciliation_mismatch: fixture.reconciliation_mismatch,
            observed_at: fixture.observed_at,
        }),
    };
    report.meta.report_digest =
        digest(SETTLEMENT_REPORT_DOMAIN, &encode_settlement_report(&report));
    Ok(report)
}

fn evaluate_assurance(
    fixture: Option<&AssuranceFixtureWire>,
    subject: &AnalysisSubjectV1,
    evaluated_at: i64,
) -> Result<AssuranceCompletenessReportV1, CompletenessEvaluationErrorV1> {
    let Some(fixture) = fixture else {
        let mut report = AssuranceCompletenessReportV1 {
            meta: absent_meta(
                subject.digest(),
                evaluated_at,
                CompletenessDimensionV1::Assurance,
                Some(CompletenessAssumptionV1::CurrentRootsDisclosedNotResolved),
            ),
            status: AssuranceCompletenessStatusV1::NotObserved,
            properties: Vec::new(),
            context: None,
        };
        report.meta.report_digest =
            digest(ASSURANCE_REPORT_DOMAIN, &encode_assurance_report(&report));
        return Ok(report);
    };
    let fixture_digest = digest(ASSURANCE_FIXTURE_DOMAIN, &encode_assurance_fixture(fixture));
    let mut reasons = BTreeSet::new();
    let mut properties = Vec::new();
    let mut explicit_fail = false;
    let fixture_current = current(fixture.observed_at, fixture.expires_at, evaluated_at);
    let mut incomplete = !fixture_current;
    if incomplete {
        reasons.insert(CompletenessReasonV1::StaleOrFutureObservation);
    }
    for observation in &fixture.observations {
        let current_roots = roots(&observation.current_roots);
        let dependency_roots = roots(&observation.dependency_roots);
        explicit_fail |= observation.verdict == AssuranceVerdictV1::Fail && fixture_current;
        if observation.verdict == AssuranceVerdictV1::Unknown {
            incomplete = true;
            reasons.insert(CompletenessReasonV1::UnknownAssuranceVerdict);
        }
        if observation.verdict == AssuranceVerdictV1::Pass && current_roots.is_empty() {
            incomplete = true;
            reasons.insert(CompletenessReasonV1::MissingCurrentRoot);
        }
        if observation.dependency_disclosure == DependencyDisclosureV1::Unknown {
            incomplete = true;
            reasons.insert(CompletenessReasonV1::UnknownDependencyAncestry);
        }
        if observation.replayed
            || observation.revoked
            || observation.superseded
            || observation.equivocated
        {
            incomplete = true;
            reasons.insert(CompletenessReasonV1::ReplayOrRevocationState);
        }
        properties.push(AssurancePropertyObservationV1 {
            property: observation.property,
            verdict: observation.verdict,
            current_roots,
            dependency_roots,
            dependency_disclosure: observation.dependency_disclosure,
            replayed: observation.replayed,
            revoked: observation.revoked,
            superseded: observation.superseded,
            equivocated: observation.equivocated,
        });
    }
    properties.sort_by_key(|value| value.property);
    let present: BTreeSet<_> = properties.iter().map(|value| value.property).collect();
    let required: BTreeSet<_> = REQUIRED_ASSURANCE_PROPERTIES.into_iter().collect();
    if present != required {
        incomplete = true;
        reasons.insert(CompletenessReasonV1::MissingAssuranceProperty);
    }
    let status = if explicit_fail {
        reasons.insert(CompletenessReasonV1::ExplicitAssuranceFailure);
        AssuranceCompletenessStatusV1::ContradictedInFixture
    } else if incomplete {
        AssuranceCompletenessStatusV1::IncompleteInFixture
    } else {
        AssuranceCompletenessStatusV1::AllRequiredObservedInFixture
    };
    let mut report = AssuranceCompletenessReportV1 {
        meta: present_meta(
            subject.digest(),
            CompletenessDimensionV1::Assurance,
            fixture_digest,
            evidence(&fixture.source_evidence_digests),
            reasons,
            evaluated_at,
            fixture.expires_at,
        ),
        status,
        properties,
        context: Some(AssuranceContextV1 {
            issuer_id: fixture.issuer_id.clone(),
            subject_id: fixture.subject_id.clone(),
            scope_digest: parse_digest(&fixture.scope_digest).expect("validated"),
            nonce: fixture.nonce.clone(),
            observed_at: fixture.observed_at,
        }),
    };
    report.meta.report_digest = digest(ASSURANCE_REPORT_DOMAIN, &encode_assurance_report(&report));
    Ok(report)
}

fn roots(values: &[RootWire]) -> BTreeSet<AssuranceRootV1> {
    values
        .iter()
        .map(|value| AssuranceRootV1 {
            root_class: value.root_class,
            root_id: value.root_id.clone(),
        })
        .collect()
}

fn evaluate_recovery(
    fixture: Option<&RecoveryFixtureWire>,
    subject: &AnalysisSubjectV1,
    profile: &RecoveryPathProfileV1,
    evaluated_at: i64,
) -> Result<RecoveryCompletenessReportV1, CompletenessEvaluationErrorV1> {
    let Some(fixture) = fixture else {
        let mut report = RecoveryCompletenessReportV1 {
            meta: absent_meta(
                subject.digest(),
                evaluated_at,
                CompletenessDimensionV1::Recovery,
                Some(CompletenessAssumptionV1::VersionedRecoveryProfileOnly),
            ),
            status: RecoveryCompletenessStatusV1::NotObserved,
            paths: Vec::new(),
            context: None,
        };
        report.meta.report_digest =
            digest(RECOVERY_REPORT_DOMAIN, &encode_recovery_report(&report));
        return Ok(report);
    };
    let fixture_digest = digest(RECOVERY_FIXTURE_DOMAIN, &encode_recovery_fixture(fixture));
    let mut reasons = BTreeSet::new();
    let mut paths = Vec::new();
    let mut failed = false;
    let fixture_current = current(fixture.observed_at, fixture.expires_at, evaluated_at);
    let mut incomplete = !fixture_current;
    if incomplete {
        reasons.insert(CompletenessReasonV1::StaleOrFutureObservation);
    }
    for path in &fixture.paths {
        let capabilities: BTreeMap<_, _> = path
            .capabilities
            .iter()
            .map(|value| (value.capability, value.verdict))
            .collect();
        failed |= capabilities
            .values()
            .any(|value| *value == AssuranceVerdictV1::Fail);
        incomplete |=
            capabilities.keys().copied().collect::<BTreeSet<_>>() != profile.required_capabilities;
        let has_unknown_capability = capabilities
            .values()
            .any(|value| *value == AssuranceVerdictV1::Unknown);
        incomplete |= has_unknown_capability;
        if has_unknown_capability {
            reasons.insert(CompletenessReasonV1::MissingRecoveryCapability);
        }
        paths.push(RecoveryPathObservationV1 {
            path_id: path.path_id.clone(),
            capabilities,
        });
    }
    paths.sort_by(|a, b| a.path_id.cmp(&b.path_id));
    let present: BTreeSet<_> = paths.iter().map(|value| value.path_id.clone()).collect();
    if present != profile.required_path_ids {
        incomplete = true;
        reasons.insert(CompletenessReasonV1::MissingRecoveryPath);
    }
    if paths
        .iter()
        .any(|path| path.capabilities.len() != RECOVERY_CAPABILITY_COUNT_V1)
    {
        reasons.insert(CompletenessReasonV1::MissingRecoveryCapability);
    }
    for item in &fixture.in_flight_items {
        if parse_digest(&item.expected_digest).expect("validated")
            != parse_digest(&item.observed_digest).expect("validated")
        {
            failed = true;
            reasons.insert(CompletenessReasonV1::ReconciliationMismatch);
        }
    }
    match fixture.evidence_preserved {
        AssuranceVerdictV1::Fail => {
            failed = true;
            reasons.insert(CompletenessReasonV1::EvidenceLoss);
        }
        AssuranceVerdictV1::Unknown => {
            incomplete = true;
            reasons.insert(CompletenessReasonV1::MissingRecoveryCapability);
        }
        AssuranceVerdictV1::Pass => {}
    }
    match fixture.liabilities_duplicate_free {
        AssuranceVerdictV1::Fail => {
            failed = true;
            reasons.insert(CompletenessReasonV1::DuplicateLiability);
        }
        AssuranceVerdictV1::Unknown => {
            incomplete = true;
            reasons.insert(CompletenessReasonV1::MissingRecoveryCapability);
        }
        AssuranceVerdictV1::Pass => {}
    }
    if fixture.canary_stages.is_empty()
        || fixture.canary_stages.contains(&AssuranceVerdictV1::Unknown)
    {
        incomplete = true;
        reasons.insert(CompletenessReasonV1::MissingOrFailedCanary);
    }
    if fixture.canary_stages.contains(&AssuranceVerdictV1::Fail) {
        failed = true;
        reasons.insert(CompletenessReasonV1::MissingOrFailedCanary);
    }
    let status = if !fixture_current {
        RecoveryCompletenessStatusV1::IncompleteOnVersionedFixtureProfile
    } else if failed {
        reasons.insert(CompletenessReasonV1::RecoveryControlFailure);
        RecoveryCompletenessStatusV1::FailedInFixture
    } else if incomplete {
        RecoveryCompletenessStatusV1::IncompleteOnVersionedFixtureProfile
    } else {
        RecoveryCompletenessStatusV1::CompleteOnVersionedFixtureProfile
    };
    let mut report = RecoveryCompletenessReportV1 {
        meta: present_meta(
            subject.digest(),
            CompletenessDimensionV1::Recovery,
            fixture_digest,
            evidence(&fixture.source_evidence_digests),
            reasons,
            evaluated_at,
            fixture.expires_at,
        ),
        status,
        paths,
        context: Some(RecoveryContextV1 {
            in_flight_items: {
                let mut values: Vec<_> = fixture
                    .in_flight_items
                    .iter()
                    .map(|item| InFlightReconciliationV1 {
                        item_id: item.item_id.clone(),
                        expected_digest: parse_digest(&item.expected_digest).expect("validated"),
                        observed_digest: parse_digest(&item.observed_digest).expect("validated"),
                    })
                    .collect();
                values.sort_by(|a, b| a.item_id.cmp(&b.item_id));
                values
            },
            evidence_preserved: fixture.evidence_preserved,
            liabilities_duplicate_free: fixture.liabilities_duplicate_free,
            canary_stages: {
                let mut values = fixture.canary_stages.clone();
                values.sort_by_key(|value| assurance_verdict_tag(*value));
                values.to_vec()
            },
            evidence_preservation_ref: fixture.evidence_preservation_ref.clone(),
            liability_before_digest: parse_digest(&fixture.liability_before_digest)
                .expect("validated"),
            liability_after_digest: parse_digest(&fixture.liability_after_digest)
                .expect("validated"),
            observed_at: fixture.observed_at,
        }),
    };
    report.meta.report_digest = digest(RECOVERY_REPORT_DOMAIN, &encode_recovery_report(&report));
    Ok(report)
}

fn encode_meta(meta: &ReportMetaV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &meta.schema_version.to_be_bytes());
    encoder.field(2, &[dimension_tag(meta.dimension)]);
    encoder.field(3, meta.analysis_subject_digest.as_bytes());
    encoder.field(4, &encode_optional_digest(meta.fixture_digest));
    encoder.field(5, &[1]);
    encoder.field(6, &encode_digest_set(&meta.source_evidence_digests));
    encoder.field(
        7,
        &encode_enum_set(meta.assumptions.iter().map(|value| assumption_tag(*value))),
    );
    encoder.field(
        8,
        &encode_enum_set(meta.reasons.iter().map(|value| reason_tag(*value))),
    );
    encoder.field(9, &meta.evaluated_at.to_be_bytes());
    encoder.field(10, &encode_optional_i64(meta.expires_at));
    encoder.field(
        11,
        &encode_enum_set(
            meta.missing_facts
                .iter()
                .map(|value| missing_fact_tag(*value)),
        ),
    );
    encoder.finish()
}

fn encode_optional_digest(value: Option<DigestV1>) -> Vec<u8> {
    match value {
        None => vec![0],
        Some(value) => {
            let mut out = vec![1];
            out.extend_from_slice(value.as_bytes());
            out
        }
    }
}
fn encode_optional_i64(value: Option<i64>) -> Vec<u8> {
    match value {
        None => vec![0],
        Some(value) => {
            let mut out = vec![1];
            out.extend_from_slice(&value.to_be_bytes());
            out
        }
    }
}

fn encode_execution_report(report: &ExecutionCompletenessReportV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &encode_meta(&report.meta));
    encoder.field(2, &[execution_status_tag(report.status)]);
    encoder.field(
        3,
        &encode_sequence(report.legs.iter().map(|leg| {
            let mut item = Canonical::new();
            item.field(1, leg.leg_id.as_bytes());
            item.field(2, leg.asset.as_bytes());
            item.field(3, &encode_rational(leg.requested_quantity));
            item.field(4, &encode_rational(leg.executable_quantity));
            item.field(5, &encode_rational(leg.unfilled_quantity));
            item.field(6, &encode_rational(leg.gross_notional));
            item.field(7, &encode_optional_rational(leg.average_price));
            item.field(8, &encode_optional_rational(leg.worst_price));
            item.field(9, &encode_rational(leg.fee));
            item.field(10, &encode_optional_rational(leg.slippage));
            item.field(11, &[fixture_support_tag(leg.queue)]);
            item.field(12, &[fixture_support_tag(leg.atomicity)]);
            item.field(13, &[fixture_support_tag(leg.leg_failure_model)]);
            item.field(14, &leg.deadline.to_be_bytes());
            item.field(15, &[execution_side_tag(leg.side)]);
            item.field(16, &encode_rational(leg.reference_price));
            item.field(17, &encode_rational(leg.price_bound));
            item.field(18, &encode_rational(leg.fee_rate));
            item.field(19, &encode_rational(leg.maximum_fee));
            item.field(20, &encode_rational(leg.maximum_slippage));
            item.finish()
        })),
    );
    encoder.field(
        4,
        &match &report.context {
            None => vec![0],
            Some(value) => {
                let mut item = Canonical::new();
                item.field(1, value.venue_id.as_bytes());
                item.field(2, value.account_id.as_bytes());
                item.field(3, &value.observed_at.to_be_bytes());
                let mut out = vec![1];
                out.extend_from_slice(&item.finish());
                out
            }
        },
    );
    encoder.finish()
}
fn encode_capital_report(report: &CapitalCompletenessReportV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &encode_meta(&report.meta));
    encoder.field(2, &[capital_status_tag(report.status)]);
    encoder.field(
        3,
        &encode_sequence(report.receipts.iter().map(|receipt| {
            let mut item = Canonical::new();
            item.field(1, &encode_state_key(receipt.state_key));
            item.field(2, &encode_rational(receipt.required_quantity));
            item.field(3, &encode_rational(receipt.recognized_quantity));
            item.field(4, &[capital_fixture_verdict_tag(receipt.verdict)]);
            item.field(5, &encode_rational(receipt.recognition_residual));
            item.field(6, receipt.capital_context_digest.as_bytes());
            item.finish()
        })),
    );
    encoder.field(
        4,
        &match &report.context {
            None => vec![0],
            Some(value) => {
                let mut item = Canonical::new();
                item.field(1, value.authority_id.as_bytes());
                item.field(2, value.eligible_account.as_bytes());
                item.field(3, value.model_id.as_bytes());
                item.field(4, &value.model_version.to_be_bytes());
                item.field(5, value.model_digest.as_bytes());
                item.field(6, &encode_rational(value.haircut));
                item.field(7, value.margin_rule_id.as_bytes());
                item.field(8, value.jurisdiction.as_bytes());
                item.field(9, &value.liquidation_horizon_seconds.to_be_bytes());
                item.field(10, &value.observed_at.to_be_bytes());
                item.field(11, value.capital_context_digest.as_bytes());
                let mut out = vec![1];
                out.extend_from_slice(&item.finish());
                out
            }
        },
    );
    encoder.finish()
}
fn encode_settlement_report(report: &SettlementCompletenessReportV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &encode_meta(&report.meta));
    encoder.field(2, &[settlement_status_tag(report.status)]);
    encoder.field(
        3,
        &encode_sequence(report.stages.iter().map(|stage| {
            let mut value = Canonical::new();
            value.field(1, stage.obligation_id.as_bytes());
            value.field(2, &[settlement_stage_tag(stage.stage)]);
            value.field(3, &[stage_verdict_tag(stage.verdict)]);
            value.finish()
        })),
    );
    encoder.field(
        4,
        &match &report.context {
            None => vec![0],
            Some(value) => {
                let mut item = Canonical::new();
                item.field(1, value.source_finality_domain.as_bytes());
                item.field(2, value.destination_finality_domain.as_bytes());
                item.field(3, &encode_optional_string(value.reversal_rule.as_deref()));
                item.field(4, &encode_optional_string(value.insolvency_rule.as_deref()));
                item.field(5, &encode_bool(value.disputed));
                item.field(6, &encode_bool(value.reversed));
                item.field(7, &encode_bool(value.reconciliation_mismatch));
                item.field(8, &encode_bool(value.domains_compatible));
                item.field(9, &encode_bool(value.transition_supported));
                item.field(10, &value.observed_at.to_be_bytes());
                let mut out = vec![1];
                out.extend_from_slice(&item.finish());
                out
            }
        },
    );
    encoder.finish()
}
fn encode_assurance_report(report: &AssuranceCompletenessReportV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &encode_meta(&report.meta));
    encoder.field(2, &[assurance_status_tag(report.status)]);
    encoder.field(
        3,
        &encode_sequence(report.properties.iter().map(|property| {
            let mut item = Canonical::new();
            item.field(1, &[assurance_property_tag(property.property)]);
            item.field(2, &[assurance_verdict_tag(property.verdict)]);
            item.field(3, &encode_root_set(&property.current_roots));
            item.field(4, &encode_root_set(&property.dependency_roots));
            item.field(
                5,
                &[dependency_disclosure_tag(property.dependency_disclosure)],
            );
            item.field(6, &encode_bool(property.replayed));
            item.field(7, &encode_bool(property.revoked));
            item.field(8, &encode_bool(property.superseded));
            item.field(9, &encode_bool(property.equivocated));
            item.finish()
        })),
    );
    encoder.field(
        4,
        &match &report.context {
            None => vec![0],
            Some(value) => {
                let mut item = Canonical::new();
                item.field(1, value.issuer_id.as_bytes());
                item.field(2, value.subject_id.as_bytes());
                item.field(3, value.scope_digest.as_bytes());
                item.field(4, value.nonce.as_bytes());
                item.field(5, &value.observed_at.to_be_bytes());
                let mut out = vec![1];
                out.extend_from_slice(&item.finish());
                out
            }
        },
    );
    encoder.finish()
}
fn encode_recovery_report(report: &RecoveryCompletenessReportV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &encode_meta(&report.meta));
    encoder.field(2, &[recovery_status_tag(report.status)]);
    encoder.field(
        3,
        &encode_sequence(report.paths.iter().map(|path| {
            let mut item = Canonical::new();
            item.field(1, path.path_id.as_bytes());
            item.field(
                2,
                &encode_sequence(path.capabilities.iter().map(|(capability, verdict)| {
                    vec![
                        recovery_capability_tag(*capability),
                        assurance_verdict_tag(*verdict),
                    ]
                })),
            );
            item.finish()
        })),
    );
    encoder.field(
        4,
        &match &report.context {
            None => vec![0],
            Some(value) => {
                let mut item = Canonical::new();
                item.field(
                    1,
                    &encode_sequence(value.in_flight_items.iter().map(|entry| {
                        let mut value = Canonical::new();
                        value.field(1, entry.item_id.as_bytes());
                        value.field(2, entry.expected_digest.as_bytes());
                        value.field(3, entry.observed_digest.as_bytes());
                        value.finish()
                    })),
                );
                item.field(2, &[assurance_verdict_tag(value.evidence_preserved)]);
                item.field(
                    3,
                    &[assurance_verdict_tag(value.liabilities_duplicate_free)],
                );
                item.field(
                    4,
                    &encode_sequence(
                        value
                            .canary_stages
                            .iter()
                            .map(|stage| vec![assurance_verdict_tag(*stage)]),
                    ),
                );
                item.field(5, &value.observed_at.to_be_bytes());
                item.field(6, value.evidence_preservation_ref.as_bytes());
                item.field(7, value.liability_before_digest.as_bytes());
                item.field(8, value.liability_after_digest.as_bytes());
                let mut out = vec![1];
                out.extend_from_slice(&item.finish());
                out
            }
        },
    );
    encoder.finish()
}

fn encode_execution_fixture(fixture: &ExecutionFixtureWire) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(
        1,
        parse_digest(&fixture.analysis_subject_digest)
            .expect("validated")
            .as_bytes(),
    );
    encoder.field(2, &fixture.observed_at.to_be_bytes());
    encoder.field(3, &fixture.expires_at.to_be_bytes());
    encoder.field(4, fixture.venue_id.as_bytes());
    encoder.field(5, fixture.account_id.as_bytes());
    let mut legs: Vec<_> = fixture.legs.iter().collect();
    legs.sort_by(|a, b| a.leg_id.cmp(&b.leg_id));
    encoder.field(
        6,
        &encode_sequence(legs.into_iter().map(|leg| {
            let mut item = Canonical::new();
            item.field(1, leg.leg_id.as_bytes());
            item.field(
                2,
                parse_digest(&leg.state_key).expect("validated").as_bytes(),
            );
            item.field(3, leg.asset.as_bytes());
            item.field(4, &[side_tag(leg.side)]);
            item.field(5, &encode_wire_rational(&leg.requested_quantity));
            item.field(6, &encode_wire_rational(&leg.reference_price));
            item.field(7, &encode_wire_rational(&leg.price_bound));
            item.field(8, &encode_wire_rational(&leg.fee_rate));
            item.field(9, &encode_wire_rational(&leg.maximum_fee));
            item.field(10, &encode_wire_rational(&leg.maximum_slippage));
            item.field(11, &leg.deadline.to_be_bytes());
            item.field(12, &[support_tag(leg.queue)]);
            item.field(13, &[support_tag(leg.atomicity)]);
            item.field(14, &[support_tag(leg.leg_failure_model)]);
            let mut levels: Vec<_> = leg.levels.iter().collect();
            levels.sort_by(|a, b| a.level_id.cmp(&b.level_id));
            item.field(
                15,
                &encode_sequence(levels.into_iter().map(|level| {
                    let mut value = Canonical::new();
                    value.field(1, level.level_id.as_bytes());
                    value.field(2, &encode_wire_rational(&level.price));
                    value.field(3, &encode_wire_rational(&level.quantity));
                    value.finish()
                })),
            );
            item.finish()
        })),
    );
    encoder.field(7, &encode_wire_digest_set(&fixture.source_evidence_digests));
    encoder.finish()
}
fn encode_capital_fixture(fixture: &CapitalFixtureWire) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(
        1,
        parse_digest(&fixture.analysis_subject_digest)
            .expect("validated")
            .as_bytes(),
    );
    encoder.field(2, &fixture.observed_at.to_be_bytes());
    encoder.field(3, &fixture.expires_at.to_be_bytes());
    encoder.field(4, fixture.authority_id.as_bytes());
    encoder.field(5, fixture.eligible_account.as_bytes());
    encoder.field(6, fixture.model_id.as_bytes());
    encoder.field(7, &fixture.model_version.to_be_bytes());
    encoder.field(
        8,
        parse_digest(&fixture.model_digest)
            .expect("validated")
            .as_bytes(),
    );
    encoder.field(9, &encode_wire_rational(&fixture.haircut));
    encoder.field(10, fixture.margin_rule_id.as_bytes());
    encoder.field(11, fixture.jurisdiction.as_bytes());
    encoder.field(12, &fixture.liquidation_horizon_seconds.to_be_bytes());
    let mut receipts: Vec<_> = fixture.receipts.iter().collect();
    receipts.sort_by(|a, b| a.state_key.cmp(&b.state_key));
    encoder.field(
        13,
        &encode_sequence(receipts.into_iter().map(|receipt| {
            let mut item = Canonical::new();
            item.field(
                1,
                parse_digest(&receipt.state_key)
                    .expect("validated")
                    .as_bytes(),
            );
            item.field(2, &encode_wire_rational(&receipt.recognized_quantity));
            item.field(3, &[capital_verdict_tag(receipt.verdict)]);
            item.field(
                4,
                parse_digest(&receipt.capital_context_digest)
                    .expect("validated")
                    .as_bytes(),
            );
            item.finish()
        })),
    );
    encoder.field(
        14,
        &encode_wire_digest_set(&fixture.source_evidence_digests),
    );
    encoder.finish()
}

fn encode_capital_context(fixture: &CapitalFixtureWire) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &1_u16.to_be_bytes());
    encoder.field(
        2,
        parse_digest(&fixture.analysis_subject_digest)
            .expect("validated")
            .as_bytes(),
    );
    encoder.field(3, fixture.authority_id.as_bytes());
    encoder.field(4, fixture.eligible_account.as_bytes());
    encoder.field(5, fixture.model_id.as_bytes());
    encoder.field(6, &fixture.model_version.to_be_bytes());
    encoder.field(
        7,
        parse_digest(&fixture.model_digest)
            .expect("validated")
            .as_bytes(),
    );
    encoder.field(8, &encode_wire_rational(&fixture.haircut));
    encoder.field(9, fixture.margin_rule_id.as_bytes());
    encoder.field(10, fixture.jurisdiction.as_bytes());
    encoder.field(11, &fixture.liquidation_horizon_seconds.to_be_bytes());
    encoder.field(12, &fixture.observed_at.to_be_bytes());
    encoder.field(13, &fixture.expires_at.to_be_bytes());
    encoder.finish()
}
fn encode_settlement_fixture(fixture: &SettlementFixtureWire) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(
        1,
        parse_digest(&fixture.analysis_subject_digest)
            .expect("validated")
            .as_bytes(),
    );
    encoder.field(2, &fixture.observed_at.to_be_bytes());
    encoder.field(3, &fixture.expires_at.to_be_bytes());
    encoder.field(4, fixture.source_finality_domain.as_bytes());
    encoder.field(5, fixture.destination_finality_domain.as_bytes());
    encoder.field(6, &encode_bool(fixture.domains_compatible));
    encoder.field(7, &encode_bool(fixture.transition_supported));
    encoder.field(8, &encode_optional_string(fixture.reversal_rule.as_deref()));
    encoder.field(
        9,
        &encode_optional_string(fixture.insolvency_rule.as_deref()),
    );
    encoder.field(10, &encode_bool(fixture.disputed));
    encoder.field(11, &encode_bool(fixture.reversed));
    encoder.field(12, &encode_bool(fixture.reconciliation_mismatch));
    let mut stages: Vec<_> = fixture.stages.iter().collect();
    stages.sort_by(|a, b| {
        a.obligation_id
            .cmp(&b.obligation_id)
            .then(a.stage.cmp(&b.stage))
    });
    encoder.field(
        13,
        &encode_sequence(stages.into_iter().map(|stage| {
            let mut value = Canonical::new();
            value.field(1, stage.obligation_id.as_bytes());
            value.field(2, &[settlement_stage_tag(stage.stage)]);
            value.field(3, &[stage_verdict_tag(stage.verdict)]);
            value.finish()
        })),
    );
    encoder.field(
        14,
        &encode_wire_digest_set(&fixture.source_evidence_digests),
    );
    encoder.finish()
}
fn encode_assurance_fixture(fixture: &AssuranceFixtureWire) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(
        1,
        parse_digest(&fixture.analysis_subject_digest)
            .expect("validated")
            .as_bytes(),
    );
    encoder.field(2, &fixture.observed_at.to_be_bytes());
    encoder.field(3, &fixture.expires_at.to_be_bytes());
    encoder.field(4, fixture.issuer_id.as_bytes());
    encoder.field(5, fixture.subject_id.as_bytes());
    encoder.field(
        6,
        parse_digest(&fixture.scope_digest)
            .expect("validated")
            .as_bytes(),
    );
    encoder.field(7, fixture.nonce.as_bytes());
    let mut observations: Vec<_> = fixture.observations.iter().collect();
    observations.sort_by_key(|value| value.property);
    encoder.field(
        8,
        &encode_sequence(observations.into_iter().map(|observation| {
            let mut item = Canonical::new();
            item.field(1, &[assurance_property_tag(observation.property)]);
            item.field(2, &[assurance_verdict_tag(observation.verdict)]);
            item.field(3, &encode_root_wires(&observation.current_roots));
            item.field(4, &encode_root_wires(&observation.dependency_roots));
            item.field(
                5,
                &[dependency_disclosure_tag(observation.dependency_disclosure)],
            );
            item.field(6, &encode_bool(observation.replayed));
            item.field(7, &encode_bool(observation.revoked));
            item.field(8, &encode_bool(observation.superseded));
            item.field(9, &encode_bool(observation.equivocated));
            item.finish()
        })),
    );
    encoder.field(9, &encode_wire_digest_set(&fixture.source_evidence_digests));
    encoder.finish()
}
fn encode_recovery_fixture(fixture: &RecoveryFixtureWire) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(
        1,
        parse_digest(&fixture.analysis_subject_digest)
            .expect("validated")
            .as_bytes(),
    );
    encoder.field(
        2,
        parse_digest(&fixture.recovery_profile_digest)
            .expect("validated")
            .as_bytes(),
    );
    encoder.field(3, &fixture.observed_at.to_be_bytes());
    encoder.field(4, &fixture.expires_at.to_be_bytes());
    let mut paths: Vec<_> = fixture.paths.iter().collect();
    paths.sort_by(|a, b| a.path_id.cmp(&b.path_id));
    encoder.field(
        5,
        &encode_sequence(paths.into_iter().map(|path| {
            let mut item = Canonical::new();
            item.field(1, path.path_id.as_bytes());
            let mut capabilities: Vec<_> = path.capabilities.iter().collect();
            capabilities.sort_by_key(|value| value.capability);
            item.field(
                2,
                &encode_sequence(capabilities.into_iter().map(|value| {
                    vec![
                        recovery_capability_tag(value.capability),
                        assurance_verdict_tag(value.verdict),
                    ]
                })),
            );
            item.finish()
        })),
    );
    let mut items: Vec<_> = fixture.in_flight_items.iter().collect();
    items.sort_by(|a, b| a.item_id.cmp(&b.item_id));
    encoder.field(
        6,
        &encode_sequence(items.into_iter().map(|item| {
            let mut value = Canonical::new();
            value.field(1, item.item_id.as_bytes());
            value.field(
                2,
                parse_digest(&item.expected_digest)
                    .expect("validated")
                    .as_bytes(),
            );
            value.field(
                3,
                parse_digest(&item.observed_digest)
                    .expect("validated")
                    .as_bytes(),
            );
            value.finish()
        })),
    );
    encoder.field(7, fixture.evidence_preservation_ref.as_bytes());
    encoder.field(
        8,
        parse_digest(&fixture.liability_before_digest)
            .expect("validated")
            .as_bytes(),
    );
    encoder.field(
        9,
        parse_digest(&fixture.liability_after_digest)
            .expect("validated")
            .as_bytes(),
    );
    encoder.field(10, &[assurance_verdict_tag(fixture.evidence_preserved)]);
    encoder.field(
        11,
        &[assurance_verdict_tag(fixture.liabilities_duplicate_free)],
    );
    let mut canary_stages = fixture.canary_stages.clone();
    canary_stages.sort_by_key(|value| assurance_verdict_tag(*value));
    encoder.field(
        12,
        &encode_sequence(
            canary_stages
                .iter()
                .map(|value| vec![assurance_verdict_tag(*value)]),
        ),
    );
    encoder.field(
        13,
        &encode_wire_digest_set(&fixture.source_evidence_digests),
    );
    encoder.finish()
}

fn encode_wire_rational(value: &RationalWire) -> Vec<u8> {
    encode_rational(parse_rational(value).expect("validated rational"))
}
fn encode_wire_digest_set(values: &[String]) -> Vec<u8> {
    let set: BTreeSet<_> = values
        .iter()
        .map(|value| parse_digest(value).expect("validated digest"))
        .collect();
    encode_digest_set(&set)
}
fn encode_optional_string(value: Option<&str>) -> Vec<u8> {
    match value {
        None => vec![0],
        Some(value) => {
            let mut out = vec![1];
            out.extend_from_slice(
                &u32::try_from(value.len())
                    .expect("bounded string")
                    .to_be_bytes(),
            );
            out.extend_from_slice(value.as_bytes());
            out
        }
    }
}
fn encode_root_wires(values: &[RootWire]) -> Vec<u8> {
    let set: BTreeSet<_> = values
        .iter()
        .map(|value| AssuranceRootV1 {
            root_class: value.root_class,
            root_id: value.root_id.clone(),
        })
        .collect();
    encode_root_set(&set)
}
fn encode_root_set(values: &BTreeSet<AssuranceRootV1>) -> Vec<u8> {
    encode_sequence(values.iter().map(|value| {
        let mut item = Canonical::new();
        item.field(1, &[root_class_tag(value.root_class)]);
        item.field(2, value.root_id.as_bytes());
        item.finish()
    }))
}

fn execution_status_tag(value: ExecutionCompletenessStatusV1) -> u8 {
    match value {
        ExecutionCompletenessStatusV1::ExecutableInFixture => 1,
        ExecutionCompletenessStatusV1::PartiallyExecutableInFixture => 2,
        ExecutionCompletenessStatusV1::NotExecutableInFixture => 3,
        ExecutionCompletenessStatusV1::NotObserved => 4,
    }
}
fn capital_status_tag(value: CapitalCompletenessStatusV1) -> u8 {
    match value {
        CapitalCompletenessStatusV1::RecognizedInFixture => 1,
        CapitalCompletenessStatusV1::PartiallyRecognizedInFixture => 2,
        CapitalCompletenessStatusV1::NotRecognizedInFixture => 3,
        CapitalCompletenessStatusV1::NotEvaluated => 4,
    }
}
fn settlement_status_tag(value: SettlementCompletenessStatusV1) -> u8 {
    match value {
        SettlementCompletenessStatusV1::FinalInFixture => 1,
        SettlementCompletenessStatusV1::ConditionalInFixture => 2,
        SettlementCompletenessStatusV1::PendingInFixture => 3,
        SettlementCompletenessStatusV1::DisputedInFixture => 4,
        SettlementCompletenessStatusV1::UnsupportedInFixture => 5,
        SettlementCompletenessStatusV1::Unknown => 6,
    }
}
fn assurance_status_tag(value: AssuranceCompletenessStatusV1) -> u8 {
    match value {
        AssuranceCompletenessStatusV1::AllRequiredObservedInFixture => 1,
        AssuranceCompletenessStatusV1::ContradictedInFixture => 2,
        AssuranceCompletenessStatusV1::IncompleteInFixture => 3,
        AssuranceCompletenessStatusV1::NotObserved => 4,
    }
}
fn recovery_status_tag(value: RecoveryCompletenessStatusV1) -> u8 {
    match value {
        RecoveryCompletenessStatusV1::CompleteOnVersionedFixtureProfile => 1,
        RecoveryCompletenessStatusV1::IncompleteOnVersionedFixtureProfile => 2,
        RecoveryCompletenessStatusV1::FailedInFixture => 3,
        RecoveryCompletenessStatusV1::NotObserved => 4,
    }
}
fn side_tag(value: SideWire) -> u8 {
    match value {
        SideWire::Buy => 1,
        SideWire::Sell => 2,
    }
}
fn support_tag(value: SupportWire) -> u8 {
    match value {
        SupportWire::Supported => 1,
        SupportWire::Unsupported => 2,
        SupportWire::Unknown => 3,
    }
}
fn fixture_support_tag(value: FixtureSupportV1) -> u8 {
    match value {
        FixtureSupportV1::Supported => 1,
        FixtureSupportV1::Unsupported => 2,
        FixtureSupportV1::Unknown => 3,
    }
}
fn execution_side_tag(value: ExecutionSideV1) -> u8 {
    match value {
        ExecutionSideV1::Buy => 1,
        ExecutionSideV1::Sell => 2,
    }
}
fn capital_fixture_verdict_tag(value: CapitalFixtureVerdictV1) -> u8 {
    match value {
        CapitalFixtureVerdictV1::Recognized => 1,
        CapitalFixtureVerdictV1::Denied => 2,
    }
}
fn dimension_tag(value: CompletenessDimensionV1) -> u8 {
    match value {
        CompletenessDimensionV1::Execution => 1,
        CompletenessDimensionV1::Capital => 2,
        CompletenessDimensionV1::Settlement => 3,
        CompletenessDimensionV1::Assurance => 4,
        CompletenessDimensionV1::Recovery => 5,
    }
}
fn capital_verdict_tag(value: CapitalVerdictWire) -> u8 {
    match value {
        CapitalVerdictWire::Recognized => 1,
        CapitalVerdictWire::Denied => 2,
    }
}
fn settlement_stage_tag(value: SettlementStageV1) -> u8 {
    match value {
        SettlementStageV1::SourceObservation => 1,
        SettlementStageV1::SourceFinality => 2,
        SettlementStageV1::DestinationObservation => 3,
        SettlementStageV1::DestinationFinality => 4,
        SettlementStageV1::OperationalReconciliation => 5,
        SettlementStageV1::LegalFinality => 6,
    }
}
fn stage_verdict_tag(value: StageVerdictV1) -> u8 {
    match value {
        StageVerdictV1::Passed => 1,
        StageVerdictV1::Pending => 2,
        StageVerdictV1::Conditional => 3,
        StageVerdictV1::Unknown => 4,
    }
}
fn assurance_property_tag(value: AssurancePropertyV1) -> u8 {
    match value {
        AssurancePropertyV1::ActionAuthorization => 1,
        AssurancePropertyV1::SourceAuthenticityAndFreshness => 2,
        AssurancePropertyV1::CalculationIntegrity => 3,
        AssurancePropertyV1::StateTransitionIntegrity => 4,
        AssurancePropertyV1::SolvencyAndLiquidResourceSupport => 5,
        AssurancePropertyV1::DestinationAndRoutePolicy => 6,
        AssurancePropertyV1::AnomalyAndEmergencyClearance => 7,
        AssurancePropertyV1::EvidenceRootDisclosure => 8,
        AssurancePropertyV1::FinancialBasisBinding => 9,
    }
}
fn assurance_verdict_tag(value: AssuranceVerdictV1) -> u8 {
    match value {
        AssuranceVerdictV1::Pass => 1,
        AssuranceVerdictV1::Fail => 2,
        AssuranceVerdictV1::Unknown => 3,
    }
}
fn dependency_disclosure_tag(value: DependencyDisclosureV1) -> u8 {
    match value {
        DependencyDisclosureV1::Complete => 1,
        DependencyDisclosureV1::Unknown => 2,
    }
}
fn root_class_tag(value: RootClassV1) -> u8 {
    match value {
        RootClassV1::Data => 1,
        RootClassV1::Operator => 2,
        RootClassV1::Cloud => 3,
        RootClassV1::Kms => 4,
        RootClassV1::Rpc => 5,
        RootClassV1::CiCd => 6,
        RootClassV1::Model => 7,
        RootClassV1::Signer => 8,
    }
}
fn assumption_tag(value: CompletenessAssumptionV1) -> u8 {
    match value {
        CompletenessAssumptionV1::HermeticFixtureOnly => 1,
        CompletenessAssumptionV1::NoLiveAuthority => 2,
        CompletenessAssumptionV1::NoCrossDimensionInference => 3,
        CompletenessAssumptionV1::FixedWidthExactArithmetic => 4,
        CompletenessAssumptionV1::CurrentRootsDisclosedNotResolved => 5,
        CompletenessAssumptionV1::VersionedRecoveryProfileOnly => 6,
    }
}
fn reason_tag(value: CompletenessReasonV1) -> u8 {
    value as u8 + 1
}

fn missing_fact_tag(value: CompletenessMissingFactV1) -> u8 {
    value as u8 + 1
}

#[cfg(test)]
mod bounded_sequence_tests {
    use super::BoundedVec;

    #[test]
    fn first_over_limit_item_rejects_without_consuming_the_following_item() {
        let error = serde_json::from_slice::<BoundedVec<u8, 2>>(b"[0,1,2,not-json]")
            .expect_err("the first over-limit item must reject");
        assert!(error.to_string().contains("sequence exceeds 2 items"));
    }
}
