use crate::exact::{ExactError, ScaledInteger, SignedRational};
use crate::model::{
    Comparator, ComparatorInputV1, EndpointPolicy, LineageReceiptV1, NormalizationProfileInputV1,
    NormalizedTerminalSemantics, ParsedSourceContractV1, RoundingMode, SemanticCompletenessReport,
    SemanticCompletenessStatus, SemanticField, Sha256Digest, SourceContractInputV1,
    TransformRuleV1, UnsupportedTerm, ValidatedContract, ValidatedNormalizationProfileV1,
    REQUIRED_FIELDS,
};
use crate::{NORMALIZATION_PROFILE_SCHEMA_V1, SOURCE_SCHEMA_V1};
use serde::de::{self, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer};
use serde_json::{Map, Number, Value};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use thiserror::Error;

#[derive(Clone, Debug, Eq, Error, PartialEq)]
pub enum ParseError {
    #[error("invalid or ambiguous JSON: {0}")]
    Json(String),
    #[error("unsupported source schema version: {0}")]
    SchemaVersion(String),
}

#[derive(Clone, Debug, Eq, Error, PartialEq)]
pub enum ProfileError {
    #[error("invalid or ambiguous JSON: {0}")]
    Json(String),
    #[error("unsupported normalization profile schema: {0}")]
    SchemaVersion(String),
    #[error("unsupported source schema in profile: {0}")]
    SourceSchemaVersion(String),
    #[error("profile identifier is invalid")]
    InvalidIdentifier,
    #[error("profile version must be nonzero")]
    InvalidVersion,
    #[error("mapping is duplicated for {0:?}")]
    DuplicateMapping(SemanticField),
    #[error("mapping source and semantic fields differ for {0:?}")]
    NonIdentityMapping(SemanticField),
    #[error("profile is missing mapping for {0:?}")]
    MissingMapping(SemanticField),
}

#[derive(Clone, Debug, Error, PartialEq)]
pub enum LoweringError {
    #[error("semantic input is incomplete")]
    Incomplete(Box<SemanticCompletenessReport>),
    #[error("semantic input contains unknown terms")]
    Unknown(Box<SemanticCompletenessReport>),
    #[error("semantic input contains unsupported material terms")]
    Unsupported(Box<SemanticCompletenessReport>),
    #[error("invalid semantic text in {0:?}")]
    InvalidText(SemanticField),
    #[error("invalid exact value in {field:?}: {source}")]
    Exact {
        field: SemanticField,
        source: ExactError,
    },
    #[error("invalid SHA-256 in {0:?}")]
    InvalidDigest(SemanticField),
    #[error("unsupported comparator: {0}")]
    UnsupportedComparator(String),
    #[error("range comparator is missing an operand or endpoint policy")]
    IncompleteRange,
    #[error("range bounds are unordered or empty under endpoint policy")]
    InvalidRange,
    #[error("observation start exceeds observation end")]
    InvalidObservationWindow,
    #[error("settlement deadline must be strictly after observation end")]
    InvalidSettlementDeadline,
    #[error("settlement scale and rounding quantum must be strictly positive")]
    NonPositiveSettlementValue,
    #[error("duplicate explicit non-equivalence: {0}")]
    DuplicateNonEquivalence(String),
    #[error("unsupported rounding mode: {0}")]
    UnsupportedRoundingMode(String),
}

pub fn parse_source_contract_v1(bytes: &[u8]) -> Result<ParsedSourceContractV1, ParseError> {
    let value = parse_unique_json(bytes).map_err(ParseError::Json)?;
    let input: SourceContractInputV1 =
        serde_json::from_value(value).map_err(|error| ParseError::Json(error.to_string()))?;
    if input.schema_version != SOURCE_SCHEMA_V1 {
        return Err(ParseError::SchemaVersion(input.schema_version));
    }
    Ok(ParsedSourceContractV1 {
        input,
        source_document_digest: digest(bytes),
    })
}

pub fn parse_normalization_profile_v1(
    bytes: &[u8],
) -> Result<ValidatedNormalizationProfileV1, ProfileError> {
    let value = parse_unique_json(bytes).map_err(ProfileError::Json)?;
    let input: NormalizationProfileInputV1 =
        serde_json::from_value(value).map_err(|error| ProfileError::Json(error.to_string()))?;
    if input.schema_version != NORMALIZATION_PROFILE_SCHEMA_V1 {
        return Err(ProfileError::SchemaVersion(input.schema_version));
    }
    if input.source_schema_version != SOURCE_SCHEMA_V1 {
        return Err(ProfileError::SourceSchemaVersion(
            input.source_schema_version,
        ));
    }
    if input.profile_version == 0 {
        return Err(ProfileError::InvalidVersion);
    }
    if !valid_text(&input.profile_id) {
        return Err(ProfileError::InvalidIdentifier);
    }

    let mut decisions = BTreeMap::new();
    let mut unknown_mappings = BTreeSet::new();
    for mapping in &input.mappings {
        if mapping.source_field != mapping.semantic_field {
            return Err(ProfileError::NonIdentityMapping(mapping.semantic_field));
        }
        if decisions
            .insert(mapping.semantic_field, mapping.transform)
            .is_some()
        {
            return Err(ProfileError::DuplicateMapping(mapping.semantic_field));
        }
        if mapping.transform == TransformRuleV1::Unknown {
            unknown_mappings.insert(mapping.semantic_field);
        }
    }
    for required in REQUIRED_FIELDS {
        if !decisions.contains_key(&required) {
            return Err(ProfileError::MissingMapping(required));
        }
    }

    Ok(ValidatedNormalizationProfileV1 {
        input,
        digest: digest(bytes),
        unknown_mappings,
    })
}

pub fn assess_semantic_completeness(
    source: &ParsedSourceContractV1,
    profile: &ValidatedNormalizationProfileV1,
) -> SemanticCompletenessReport {
    let mut missing = BTreeSet::new();
    let input = &source.input;
    missing_if_none(
        &mut missing,
        SemanticField::VenueNamespace,
        &input.venue_namespace,
    );
    missing_if_none(
        &mut missing,
        SemanticField::SourceContractId,
        &input.source_contract_id,
    );
    missing_if_none(
        &mut missing,
        SemanticField::SourceRevision,
        &input.source_revision,
    );
    missing_if_none(
        &mut missing,
        SemanticField::SourceObservedAt,
        &input.source_observed_at,
    );

    if let Some(reference) = &input.economic_reference {
        missing_if_none(
            &mut missing,
            SemanticField::ReferenceNamespace,
            &reference.namespace,
        );
        missing_if_none(
            &mut missing,
            SemanticField::ReferenceIdentifier,
            &reference.identifier,
        );
        missing_if_none(&mut missing, SemanticField::ReferenceUnit, &reference.unit);
        missing_if_none(
            &mut missing,
            SemanticField::BenchmarkAdministrator,
            &reference.benchmark_administrator,
        );
        missing_if_none(
            &mut missing,
            SemanticField::MethodologyVersion,
            &reference.methodology_version,
        );
        missing_if_none(
            &mut missing,
            SemanticField::MethodologySha256,
            &reference.methodology_sha256,
        );
        missing_if_none(
            &mut missing,
            SemanticField::FallbackRule,
            &reference.fallback_rule,
        );
        missing_if_none(&mut missing, SemanticField::Calendar, &reference.calendar);
        missing_if_none(&mut missing, SemanticField::Timezone, &reference.timezone);
    } else {
        missing.extend([
            SemanticField::ReferenceNamespace,
            SemanticField::ReferenceIdentifier,
            SemanticField::ReferenceUnit,
            SemanticField::BenchmarkAdministrator,
            SemanticField::MethodologyVersion,
            SemanticField::MethodologySha256,
            SemanticField::FallbackRule,
            SemanticField::Calendar,
            SemanticField::Timezone,
        ]);
    }

    if let Some(observation) = &input.observation {
        missing_if_none(
            &mut missing,
            SemanticField::ObservationStart,
            &observation.start,
        );
        missing_if_none(
            &mut missing,
            SemanticField::ObservationEnd,
            &observation.end,
        );
        missing_if_none(
            &mut missing,
            SemanticField::SamplingRule,
            &observation.sampling_rule,
        );
        missing_if_none(
            &mut missing,
            SemanticField::DisruptionRule,
            &observation.disruption_rule,
        );
        missing_if_none(
            &mut missing,
            SemanticField::CorrectionRule,
            &observation.correction_rule,
        );
    } else {
        missing.extend([
            SemanticField::ObservationStart,
            SemanticField::ObservationEnd,
            SemanticField::SamplingRule,
            SemanticField::DisruptionRule,
            SemanticField::CorrectionRule,
        ]);
    }

    let mut unsupported = BTreeSet::new();
    if let Some(payoff) = &input.payoff {
        missing_if_none(&mut missing, SemanticField::PayoffKind, &payoff.kind);
        missing_if_none(&mut missing, SemanticField::Comparator, &payoff.comparator);
        missing_if_none(&mut missing, SemanticField::PayoffAmount, &payoff.amount);
        if let Some(kind) = &payoff.kind {
            if kind != "indicator" {
                unsupported.insert(UnsupportedTerm::PayoffForm(kind.clone()));
            }
        }
        if let Some(comparator) = &payoff.comparator {
            assess_comparator_shape(comparator, &mut missing, &mut unsupported);
        }
    } else {
        missing.extend([
            SemanticField::PayoffKind,
            SemanticField::Comparator,
            SemanticField::PayoffAmount,
        ]);
    }

    if let Some(settlement) = &input.settlement {
        missing_if_none(
            &mut missing,
            SemanticField::SettlementAsset,
            &settlement.asset,
        );
        missing_if_none(
            &mut missing,
            SemanticField::SettlementUnitScale,
            &settlement.unit_scale,
        );
        missing_if_none(
            &mut missing,
            SemanticField::RoundingMode,
            &settlement.rounding_mode,
        );
        missing_if_none(
            &mut missing,
            SemanticField::RoundingQuantum,
            &settlement.rounding_quantum,
        );
        missing_if_none(
            &mut missing,
            SemanticField::SettlementDeadline,
            &settlement.deadline,
        );
        missing_if_none(
            &mut missing,
            SemanticField::DisputeRule,
            &settlement.dispute_rule,
        );
        missing_if_none(
            &mut missing,
            SemanticField::DefaultRule,
            &settlement.default_rule,
        );
        missing_if_none(
            &mut missing,
            SemanticField::GoverningRule,
            &settlement.governing_rule,
        );
        missing_if_none(
            &mut missing,
            SemanticField::FinalityDomain,
            &settlement.finality_domain,
        );
        if let Some(rounding_mode) = &settlement.rounding_mode {
            if !matches!(
                rounding_mode.as_str(),
                "toward_zero" | "floor" | "ceiling" | "half_even"
            ) {
                unsupported.insert(UnsupportedTerm::RoundingMode(rounding_mode.clone()));
            }
        }
    } else {
        missing.extend([
            SemanticField::SettlementAsset,
            SemanticField::SettlementUnitScale,
            SemanticField::RoundingMode,
            SemanticField::RoundingQuantum,
            SemanticField::SettlementDeadline,
            SemanticField::DisputeRule,
            SemanticField::DefaultRule,
            SemanticField::GoverningRule,
            SemanticField::FinalityDomain,
        ]);
    }
    missing_if_none(
        &mut missing,
        SemanticField::ExplicitNonEquivalences,
        &input.explicit_non_equivalences,
    );

    let mut unknown = input.unknown_terms.clone();
    unknown.extend(profile.unknown_mappings.iter().copied());
    let status = if !missing.is_empty() {
        SemanticCompletenessStatus::Incomplete
    } else if !unknown.is_empty() {
        SemanticCompletenessStatus::Unknown
    } else if unsupported.is_empty() {
        SemanticCompletenessStatus::Complete
    } else {
        SemanticCompletenessStatus::Unknown
    };
    SemanticCompletenessReport::new(
        status,
        missing,
        unknown,
        unsupported,
        source.source_document_digest,
        profile.digest,
    )
}

pub fn validate_and_lower(
    source: ParsedSourceContractV1,
    profile: &ValidatedNormalizationProfileV1,
) -> Result<ValidatedContract, LoweringError> {
    let completeness = assess_semantic_completeness(&source, profile);
    if !completeness.unsupported_terms().is_empty() {
        return Err(LoweringError::Unsupported(Box::new(completeness)));
    }
    match completeness.status() {
        SemanticCompletenessStatus::Incomplete => {
            return Err(LoweringError::Incomplete(Box::new(completeness)));
        }
        SemanticCompletenessStatus::Unknown => {
            return Err(LoweringError::Unknown(Box::new(completeness)));
        }
        SemanticCompletenessStatus::Complete => {}
    }

    let input = &source.input;
    validate_lineage_text(input)?;
    let reference = input
        .economic_reference
        .as_ref()
        .expect("completeness checked");
    let observation = input.observation.as_ref().expect("completeness checked");
    let payoff = input.payoff.as_ref().expect("completeness checked");
    let settlement = input.settlement.as_ref().expect("completeness checked");

    let reference_namespace = text(
        reference.namespace.as_ref(),
        SemanticField::ReferenceNamespace,
    )?;
    let reference_identifier = text(
        reference.identifier.as_ref(),
        SemanticField::ReferenceIdentifier,
    )?;
    let reference_unit = text(reference.unit.as_ref(), SemanticField::ReferenceUnit)?;
    let benchmark_administrator = text(
        reference.benchmark_administrator.as_ref(),
        SemanticField::BenchmarkAdministrator,
    )?;
    let methodology_version = text(
        reference.methodology_version.as_ref(),
        SemanticField::MethodologyVersion,
    )?;
    let methodology_sha256 = Sha256Digest::from_hex(
        reference
            .methodology_sha256
            .as_ref()
            .expect("completeness checked"),
    )
    .map_err(|_| LoweringError::InvalidDigest(SemanticField::MethodologySha256))?;
    let fallback_rule = text(
        reference.fallback_rule.as_ref(),
        SemanticField::FallbackRule,
    )?;
    let calendar = text(reference.calendar.as_ref(), SemanticField::Calendar)?;
    let timezone = text(reference.timezone.as_ref(), SemanticField::Timezone)?;

    let observation_start = observation.start.expect("completeness checked");
    let observation_end = observation.end.expect("completeness checked");
    if observation_start > observation_end {
        return Err(LoweringError::InvalidObservationWindow);
    }

    let comparator = lower_comparator(payoff.comparator.as_ref().expect("completeness checked"))?;
    let payoff_amount = rational(
        payoff.amount.as_ref().expect("completeness checked"),
        SemanticField::PayoffAmount,
    )?;
    let settlement_unit_scale = decimal(
        settlement.unit_scale.as_ref(),
        SemanticField::SettlementUnitScale,
    )?;
    let rounding_quantum = decimal(
        settlement.rounding_quantum.as_ref(),
        SemanticField::RoundingQuantum,
    )?;
    if settlement_unit_scale.coefficient() <= 0 || rounding_quantum.coefficient() <= 0 {
        return Err(LoweringError::NonPositiveSettlementValue);
    }
    let settlement_deadline = settlement.deadline.expect("completeness checked");
    if settlement_deadline <= observation_end {
        return Err(LoweringError::InvalidSettlementDeadline);
    }
    let rounding_mode = match settlement
        .rounding_mode
        .as_deref()
        .expect("completeness checked")
    {
        "toward_zero" => RoundingMode::TowardZero,
        "floor" => RoundingMode::Floor,
        "ceiling" => RoundingMode::Ceiling,
        "half_even" => RoundingMode::HalfEven,
        other => return Err(LoweringError::UnsupportedRoundingMode(other.to_owned())),
    };

    let mut explicit_non_equivalences = BTreeSet::new();
    for value in input
        .explicit_non_equivalences
        .as_ref()
        .expect("completeness checked")
    {
        if !valid_text(value) {
            return Err(LoweringError::InvalidText(
                SemanticField::ExplicitNonEquivalences,
            ));
        }
        if !explicit_non_equivalences.insert(value.clone()) {
            return Err(LoweringError::DuplicateNonEquivalence(value.clone()));
        }
    }

    let semantics = NormalizedTerminalSemantics {
        reference_namespace,
        reference_identifier,
        reference_unit,
        benchmark_administrator,
        methodology_version,
        methodology_sha256,
        fallback_rule,
        calendar,
        timezone,
        observation_start,
        observation_end,
        sampling_rule: text(
            observation.sampling_rule.as_ref(),
            SemanticField::SamplingRule,
        )?,
        disruption_rule: text(
            observation.disruption_rule.as_ref(),
            SemanticField::DisruptionRule,
        )?,
        correction_rule: text(
            observation.correction_rule.as_ref(),
            SemanticField::CorrectionRule,
        )?,
        comparator,
        payoff_amount,
        settlement_asset: text(settlement.asset.as_ref(), SemanticField::SettlementAsset)?,
        settlement_unit_scale,
        rounding_mode,
        rounding_quantum,
        settlement_deadline,
        dispute_rule: text(settlement.dispute_rule.as_ref(), SemanticField::DisputeRule)?,
        default_rule: text(settlement.default_rule.as_ref(), SemanticField::DefaultRule)?,
        governing_rule: text(
            settlement.governing_rule.as_ref(),
            SemanticField::GoverningRule,
        )?,
        finality_domain: text(
            settlement.finality_domain.as_ref(),
            SemanticField::FinalityDomain,
        )?,
        explicit_non_equivalences,
    };

    Ok(ValidatedContract {
        semantics,
        lineage: LineageReceiptV1::new(&source, profile),
        completeness,
    })
}

fn validate_lineage_text(input: &SourceContractInputV1) -> Result<(), LoweringError> {
    text(
        input.venue_namespace.as_ref(),
        SemanticField::VenueNamespace,
    )?;
    text(
        input.source_contract_id.as_ref(),
        SemanticField::SourceContractId,
    )?;
    text(
        input.source_revision.as_ref(),
        SemanticField::SourceRevision,
    )?;
    Ok(())
}

fn lower_comparator(input: &ComparatorInputV1) -> Result<Comparator, LoweringError> {
    let scalar_shape = input.threshold.is_some()
        && input.lower.is_none()
        && input.upper.is_none()
        && input.endpoints.is_none();
    let range_shape = input.threshold.is_none()
        && input.lower.is_some()
        && input.upper.is_some()
        && input.endpoints.is_some();
    let known_scalar = matches!(
        input.kind.as_str(),
        "less_than" | "less_than_or_equal" | "equal" | "greater_than_or_equal" | "greater_than"
    );
    if (known_scalar && !scalar_shape) || (input.kind == "in_range" && !range_shape) {
        return Err(LoweringError::IncompleteRange);
    }
    let threshold = || {
        input
            .threshold
            .as_ref()
            .ok_or(LoweringError::IncompleteRange)
            .and_then(|value| rational(value, SemanticField::Comparator))
    };
    match input.kind.as_str() {
        "less_than" => Ok(Comparator::LessThan {
            threshold: threshold()?,
        }),
        "less_than_or_equal" => Ok(Comparator::LessThanOrEqual {
            threshold: threshold()?,
        }),
        "equal" => Ok(Comparator::Equal {
            threshold: threshold()?,
        }),
        "greater_than_or_equal" => Ok(Comparator::GreaterThanOrEqual {
            threshold: threshold()?,
        }),
        "greater_than" => Ok(Comparator::GreaterThan {
            threshold: threshold()?,
        }),
        "in_range" => {
            let lower = input
                .lower
                .as_ref()
                .ok_or(LoweringError::IncompleteRange)
                .and_then(|value| rational(value, SemanticField::Comparator))?;
            let upper = input
                .upper
                .as_ref()
                .ok_or(LoweringError::IncompleteRange)
                .and_then(|value| rational(value, SemanticField::Comparator))?;
            let endpoints = match input
                .endpoints
                .as_deref()
                .ok_or(LoweringError::IncompleteRange)?
            {
                "open_open" => EndpointPolicy::OpenOpen,
                "open_closed" => EndpointPolicy::OpenClosed,
                "closed_open" => EndpointPolicy::ClosedOpen,
                "closed_closed" => EndpointPolicy::ClosedClosed,
                other => return Err(LoweringError::UnsupportedComparator(other.to_owned())),
            };
            let ordering = lower
                .checked_cmp(upper)
                .map_err(|source| LoweringError::Exact {
                    field: SemanticField::Comparator,
                    source,
                })?;
            if ordering.is_gt() || (ordering.is_eq() && endpoints != EndpointPolicy::ClosedClosed) {
                return Err(LoweringError::InvalidRange);
            }
            Ok(Comparator::InRange {
                lower,
                upper,
                endpoints,
            })
        }
        other => Err(LoweringError::UnsupportedComparator(other.to_owned())),
    }
}

fn assess_comparator_shape(
    input: &ComparatorInputV1,
    missing: &mut BTreeSet<SemanticField>,
    unsupported: &mut BTreeSet<UnsupportedTerm>,
) {
    let scalar = matches!(
        input.kind.as_str(),
        "less_than" | "less_than_or_equal" | "equal" | "greater_than_or_equal" | "greater_than"
    );
    if scalar {
        if input.threshold.is_none() {
            missing.insert(SemanticField::Comparator);
        }
        if input.lower.is_some() || input.upper.is_some() || input.endpoints.is_some() {
            unsupported.insert(UnsupportedTerm::ComparatorShape(input.kind.clone()));
        }
    } else if input.kind == "in_range" {
        if input.lower.is_none() || input.upper.is_none() || input.endpoints.is_none() {
            missing.insert(SemanticField::Comparator);
        }
        if input.threshold.is_some() {
            unsupported.insert(UnsupportedTerm::ComparatorShape(input.kind.clone()));
        }
    } else {
        unsupported.insert(UnsupportedTerm::Comparator(input.kind.clone()));
    }
}

fn rational(
    input: &crate::exact::RationalInput,
    field: SemanticField,
) -> Result<SignedRational, LoweringError> {
    SignedRational::parse(&input.numerator, &input.denominator)
        .map_err(|source| LoweringError::Exact { field, source })
}

fn decimal(input: Option<&String>, field: SemanticField) -> Result<ScaledInteger, LoweringError> {
    ScaledInteger::parse(input.expect("completeness checked"))
        .map_err(|source| LoweringError::Exact { field, source })
}

fn text(input: Option<&String>, field: SemanticField) -> Result<String, LoweringError> {
    let value = input.expect("completeness checked");
    if valid_text(value) {
        Ok(value.clone())
    } else {
        Err(LoweringError::InvalidText(field))
    }
}

fn valid_text(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 256
        && value.is_ascii()
        && value.trim() == value
        && !value.bytes().any(|byte| byte.is_ascii_control())
}

fn missing_if_none<T>(set: &mut BTreeSet<SemanticField>, field: SemanticField, value: &Option<T>) {
    if value.is_none() {
        set.insert(field);
    }
}

fn digest(bytes: &[u8]) -> Sha256Digest {
    Sha256Digest::from_bytes(Sha256::digest(bytes).into())
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

    fn visit_f64<E>(self, value: f64) -> Result<Self::Value, E>
    where
        E: de::Error,
    {
        Number::from_f64(value)
            .map(Value::Number)
            .map(UniqueValue)
            .ok_or_else(|| E::custom("non-finite JSON number"))
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
