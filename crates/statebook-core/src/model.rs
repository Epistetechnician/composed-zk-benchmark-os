use crate::exact::{RationalInput, ScaledInteger, SignedRational};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;
use std::fmt;

#[derive(Clone, Copy, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
pub struct Sha256Digest([u8; 32]);

impl Sha256Digest {
    pub(crate) const fn from_bytes(bytes: [u8; 32]) -> Self {
        Self(bytes)
    }

    pub(crate) fn from_hex(value: &str) -> Result<Self, hex::FromHexError> {
        let mut bytes = [0_u8; 32];
        hex::decode_to_slice(value, &mut bytes)?;
        Ok(Self(bytes))
    }

    pub const fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }

    pub fn to_hex(self) -> String {
        hex::encode(self.0)
    }
}

impl fmt::Debug for Sha256Digest {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_tuple("Sha256Digest")
            .field(&self.to_hex())
            .finish()
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SemanticField {
    VenueNamespace,
    SourceContractId,
    SourceRevision,
    SourceObservedAt,
    ReferenceNamespace,
    ReferenceIdentifier,
    ReferenceUnit,
    BenchmarkAdministrator,
    MethodologyVersion,
    MethodologySha256,
    FallbackRule,
    Calendar,
    Timezone,
    ObservationStart,
    ObservationEnd,
    SamplingRule,
    DisruptionRule,
    CorrectionRule,
    PayoffKind,
    Comparator,
    PayoffAmount,
    SettlementAsset,
    SettlementUnitScale,
    RoundingMode,
    RoundingQuantum,
    SettlementDeadline,
    DisputeRule,
    DefaultRule,
    GoverningRule,
    FinalityDomain,
    ExplicitNonEquivalences,
}

pub(crate) const REQUIRED_FIELDS: [SemanticField; 31] = [
    SemanticField::VenueNamespace,
    SemanticField::SourceContractId,
    SemanticField::SourceRevision,
    SemanticField::SourceObservedAt,
    SemanticField::ReferenceNamespace,
    SemanticField::ReferenceIdentifier,
    SemanticField::ReferenceUnit,
    SemanticField::BenchmarkAdministrator,
    SemanticField::MethodologyVersion,
    SemanticField::MethodologySha256,
    SemanticField::FallbackRule,
    SemanticField::Calendar,
    SemanticField::Timezone,
    SemanticField::ObservationStart,
    SemanticField::ObservationEnd,
    SemanticField::SamplingRule,
    SemanticField::DisruptionRule,
    SemanticField::CorrectionRule,
    SemanticField::PayoffKind,
    SemanticField::Comparator,
    SemanticField::PayoffAmount,
    SemanticField::SettlementAsset,
    SemanticField::SettlementUnitScale,
    SemanticField::RoundingMode,
    SemanticField::RoundingQuantum,
    SemanticField::SettlementDeadline,
    SemanticField::DisputeRule,
    SemanticField::DefaultRule,
    SemanticField::GoverningRule,
    SemanticField::FinalityDomain,
    SemanticField::ExplicitNonEquivalences,
];

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum UnsupportedTerm {
    PayoffForm(String),
    Comparator(String),
    ComparatorShape(String),
    RoundingMode(String),
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SemanticCompletenessStatus {
    Complete,
    Incomplete,
    Unknown,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct SemanticCompletenessReport {
    status: SemanticCompletenessStatus,
    missing_terms: BTreeSet<SemanticField>,
    unknown_terms: BTreeSet<SemanticField>,
    unsupported_terms: BTreeSet<UnsupportedTerm>,
    source_terms_digest: Sha256Digest,
    normalization_profile_digest: Sha256Digest,
}

impl SemanticCompletenessReport {
    pub(crate) fn new(
        status: SemanticCompletenessStatus,
        missing_terms: BTreeSet<SemanticField>,
        unknown_terms: BTreeSet<SemanticField>,
        unsupported_terms: BTreeSet<UnsupportedTerm>,
        source_terms_digest: Sha256Digest,
        normalization_profile_digest: Sha256Digest,
    ) -> Self {
        Self {
            status,
            missing_terms,
            unknown_terms,
            unsupported_terms,
            source_terms_digest,
            normalization_profile_digest,
        }
    }

    pub const fn status(&self) -> SemanticCompletenessStatus {
        self.status
    }

    pub const fn missing_terms(&self) -> &BTreeSet<SemanticField> {
        &self.missing_terms
    }

    pub const fn unknown_terms(&self) -> &BTreeSet<SemanticField> {
        &self.unknown_terms
    }

    pub const fn unsupported_terms(&self) -> &BTreeSet<UnsupportedTerm> {
        &self.unsupported_terms
    }

    pub const fn source_terms_digest(&self) -> Sha256Digest {
        self.source_terms_digest
    }

    pub const fn normalization_profile_digest(&self) -> Sha256Digest {
        self.normalization_profile_digest
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EndpointPolicy {
    OpenOpen,
    OpenClosed,
    ClosedOpen,
    ClosedClosed,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Comparator {
    LessThan {
        threshold: SignedRational,
    },
    LessThanOrEqual {
        threshold: SignedRational,
    },
    Equal {
        threshold: SignedRational,
    },
    GreaterThanOrEqual {
        threshold: SignedRational,
    },
    GreaterThan {
        threshold: SignedRational,
    },
    InRange {
        lower: SignedRational,
        upper: SignedRational,
        endpoints: EndpointPolicy,
    },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RoundingMode {
    TowardZero,
    Floor,
    Ceiling,
    HalfEven,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct NormalizedTerminalSemantics {
    pub(crate) reference_namespace: String,
    pub(crate) reference_identifier: String,
    pub(crate) reference_unit: String,
    pub(crate) benchmark_administrator: String,
    pub(crate) methodology_version: String,
    pub(crate) methodology_sha256: Sha256Digest,
    pub(crate) fallback_rule: String,
    pub(crate) calendar: String,
    pub(crate) timezone: String,
    pub(crate) observation_start: i64,
    pub(crate) observation_end: i64,
    pub(crate) sampling_rule: String,
    pub(crate) disruption_rule: String,
    pub(crate) correction_rule: String,
    pub(crate) comparator: Comparator,
    pub(crate) payoff_amount: SignedRational,
    pub(crate) settlement_asset: String,
    pub(crate) settlement_unit_scale: ScaledInteger,
    pub(crate) rounding_mode: RoundingMode,
    pub(crate) rounding_quantum: ScaledInteger,
    pub(crate) settlement_deadline: i64,
    pub(crate) dispute_rule: String,
    pub(crate) default_rule: String,
    pub(crate) governing_rule: String,
    pub(crate) finality_domain: String,
    pub(crate) explicit_non_equivalences: BTreeSet<String>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct LineageReceiptV1 {
    venue_namespace: String,
    source_contract_id: String,
    source_revision: String,
    source_observed_at: i64,
    source_document_digest: Sha256Digest,
    normalization_profile_id: String,
    normalization_profile_version: u32,
    normalization_profile_digest: Sha256Digest,
}

impl LineageReceiptV1 {
    pub(crate) fn new(
        source: &ParsedSourceContractV1,
        profile: &ValidatedNormalizationProfileV1,
    ) -> Self {
        Self {
            venue_namespace: source.input.venue_namespace.clone().unwrap_or_default(),
            source_contract_id: source.input.source_contract_id.clone().unwrap_or_default(),
            source_revision: source.input.source_revision.clone().unwrap_or_default(),
            source_observed_at: source.input.source_observed_at.unwrap_or_default(),
            source_document_digest: source.source_document_digest,
            normalization_profile_id: profile.input.profile_id.clone(),
            normalization_profile_version: profile.input.profile_version,
            normalization_profile_digest: profile.digest,
        }
    }

    pub const fn source_document_digest(&self) -> Sha256Digest {
        self.source_document_digest
    }

    pub const fn normalization_profile_digest(&self) -> Sha256Digest {
        self.normalization_profile_digest
    }

    pub const fn normalization_profile_version(&self) -> u32 {
        self.normalization_profile_version
    }

    pub const fn source_observed_at(&self) -> i64 {
        self.source_observed_at
    }

    pub fn venue_namespace(&self) -> &str {
        &self.venue_namespace
    }

    pub fn source_contract_id(&self) -> &str {
        &self.source_contract_id
    }

    pub fn source_revision(&self) -> &str {
        &self.source_revision
    }

    pub fn normalization_profile_id(&self) -> &str {
        &self.normalization_profile_id
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ValidatedContract {
    pub(crate) semantics: NormalizedTerminalSemantics,
    pub(crate) lineage: LineageReceiptV1,
    pub(crate) completeness: SemanticCompletenessReport,
}

impl ValidatedContract {
    pub const fn semantics(&self) -> &NormalizedTerminalSemantics {
        &self.semantics
    }

    pub const fn lineage(&self) -> &LineageReceiptV1 {
        &self.lineage
    }

    pub const fn completeness(&self) -> &SemanticCompletenessReport {
        &self.completeness
    }
}

#[derive(Clone, Copy, Eq, Hash, PartialEq, Serialize)]
pub struct StateKeyV1(Sha256Digest);

impl StateKeyV1 {
    pub(crate) const fn new(digest: Sha256Digest) -> Self {
        Self(digest)
    }

    pub const fn digest(self) -> Sha256Digest {
        self.0
    }

    pub fn to_hex(self) -> String {
        self.0.to_hex()
    }
}

impl fmt::Debug for StateKeyV1 {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_tuple("StateKeyV1")
            .field(&self.to_hex())
            .finish()
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StateKeyReceiptV1 {
    pub(crate) state_key: StateKeyV1,
    pub(crate) canonical_preimage: Vec<u8>,
    pub(crate) validated_contract_digest: Sha256Digest,
    pub(crate) lineage: LineageReceiptV1,
}

impl StateKeyReceiptV1 {
    pub const fn state_key(&self) -> StateKeyV1 {
        self.state_key
    }

    pub fn canonical_preimage(&self) -> &[u8] {
        &self.canonical_preimage
    }

    pub const fn validated_contract_digest(&self) -> Sha256Digest {
        self.validated_contract_digest
    }

    pub const fn lineage(&self) -> &LineageReceiptV1 {
        &self.lineage
    }
}

#[derive(Clone, Debug)]
pub struct ParsedSourceContractV1 {
    pub(crate) input: SourceContractInputV1,
    pub(crate) source_document_digest: Sha256Digest,
}

impl ParsedSourceContractV1 {
    pub const fn source_document_digest(&self) -> Sha256Digest {
        self.source_document_digest
    }
}

#[derive(Clone, Debug)]
pub struct ValidatedNormalizationProfileV1 {
    pub(crate) input: NormalizationProfileInputV1,
    pub(crate) digest: Sha256Digest,
    pub(crate) unknown_mappings: BTreeSet<SemanticField>,
}

impl ValidatedNormalizationProfileV1 {
    pub const fn digest(&self) -> Sha256Digest {
        self.digest
    }

    pub fn profile_id(&self) -> &str {
        &self.input.profile_id
    }

    pub const fn profile_version(&self) -> u32 {
        self.input.profile_version
    }
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct SourceContractInputV1 {
    pub schema_version: String,
    pub venue_namespace: Option<String>,
    pub source_contract_id: Option<String>,
    pub source_revision: Option<String>,
    pub source_observed_at: Option<i64>,
    pub economic_reference: Option<EconomicReferenceInputV1>,
    pub observation: Option<ObservationInputV1>,
    pub payoff: Option<PayoffInputV1>,
    pub settlement: Option<SettlementInputV1>,
    pub explicit_non_equivalences: Option<Vec<String>>,
    #[serde(default)]
    pub unknown_terms: BTreeSet<SemanticField>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct EconomicReferenceInputV1 {
    pub namespace: Option<String>,
    pub identifier: Option<String>,
    pub unit: Option<String>,
    pub benchmark_administrator: Option<String>,
    pub methodology_version: Option<String>,
    pub methodology_sha256: Option<String>,
    pub fallback_rule: Option<String>,
    pub calendar: Option<String>,
    pub timezone: Option<String>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct ObservationInputV1 {
    pub start: Option<i64>,
    pub end: Option<i64>,
    pub sampling_rule: Option<String>,
    pub disruption_rule: Option<String>,
    pub correction_rule: Option<String>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct PayoffInputV1 {
    pub kind: Option<String>,
    pub comparator: Option<ComparatorInputV1>,
    pub amount: Option<RationalInput>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct ComparatorInputV1 {
    pub kind: String,
    pub threshold: Option<RationalInput>,
    pub lower: Option<RationalInput>,
    pub upper: Option<RationalInput>,
    pub endpoints: Option<String>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct SettlementInputV1 {
    pub asset: Option<String>,
    pub unit_scale: Option<String>,
    pub rounding_mode: Option<String>,
    pub rounding_quantum: Option<String>,
    pub deadline: Option<i64>,
    pub dispute_rule: Option<String>,
    pub default_rule: Option<String>,
    pub governing_rule: Option<String>,
    pub finality_domain: Option<String>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct NormalizationProfileInputV1 {
    pub schema_version: String,
    pub profile_id: String,
    pub profile_version: u32,
    pub source_schema_version: String,
    pub mappings: Vec<MappingDecisionV1>,
}

#[derive(Clone, Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct MappingDecisionV1 {
    pub semantic_field: SemanticField,
    pub source_field: SemanticField,
    pub transform: TransformRuleV1,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "snake_case")]
pub(crate) enum TransformRuleV1 {
    Exact,
    Unknown,
}
