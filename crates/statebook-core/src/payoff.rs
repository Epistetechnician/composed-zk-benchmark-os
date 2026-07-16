use crate::exact::sum_rationals_canonical;
use crate::model::{
    Comparator, EndpointPolicy, NormalizedTerminalSemantics, SemanticField, Sha256Digest,
    StateKeyV1, ValidatedContract,
};
use crate::{derive_state_key, quantize_exact, ExactError, SignedRational};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};
use thiserror::Error;

pub const MAX_DECLARED_STATES_V1: usize = 256;
pub const MAX_PORTFOLIO_LEGS_V1: usize = 64;
pub const DECLARED_STATE_DOMAIN_V1: &[u8] = b"statebook:declared-state-domain:v1\0";

#[derive(Clone, Debug, Eq, Error, PartialEq)]
pub enum PayoffAnalysisError {
    #[error("declared state domain is empty")]
    EmptyStateDomain,
    #[error("declared state count {actual} exceeds maximum {maximum}")]
    TooManyStates { actual: usize, maximum: usize },
    #[error("candidate leg count {actual} exceeds maximum {maximum}")]
    TooManyPortfolioLegs { actual: usize, maximum: usize },
    #[error("state identifier is invalid: {0}")]
    InvalidStateId(String),
    #[error("state identifier is duplicated: {0}")]
    DuplicateStateId(String),
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct DeclaredTerminalStateV1 {
    id: String,
    observation: SignedRational,
}

impl DeclaredTerminalStateV1 {
    pub fn try_new(
        id: impl Into<String>,
        observation: SignedRational,
    ) -> Result<Self, PayoffAnalysisError> {
        let id = id.into();
        if !valid_state_id(&id) {
            return Err(PayoffAnalysisError::InvalidStateId(id));
        }
        Ok(Self { id, observation })
    }

    pub fn id(&self) -> &str {
        &self.id
    }

    pub const fn observation(&self) -> SignedRational {
        self.observation
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct DeclaredStateDomainV1 {
    states: BTreeMap<String, SignedRational>,
    digest: Sha256Digest,
}

impl DeclaredStateDomainV1 {
    pub fn try_new(
        states: impl IntoIterator<Item = DeclaredTerminalStateV1>,
    ) -> Result<Self, PayoffAnalysisError> {
        let mut ordered = BTreeMap::new();
        for state in states {
            let actual = ordered.len() + 1;
            if actual > MAX_DECLARED_STATES_V1 {
                return Err(PayoffAnalysisError::TooManyStates {
                    actual,
                    maximum: MAX_DECLARED_STATES_V1,
                });
            }
            let id = state.id;
            if ordered.insert(id.clone(), state.observation).is_some() {
                return Err(PayoffAnalysisError::DuplicateStateId(id));
            }
        }
        if ordered.is_empty() {
            return Err(PayoffAnalysisError::EmptyStateDomain);
        }
        let digest = state_domain_digest(&ordered);
        Ok(Self {
            states: ordered,
            digest,
        })
    }

    pub const fn digest(&self) -> Sha256Digest {
        self.digest
    }

    pub fn len(&self) -> usize {
        self.states.len()
    }

    pub fn is_empty(&self) -> bool {
        self.states.is_empty()
    }
}

#[derive(Clone, Copy, Debug)]
pub struct ContractPositionV1<'a> {
    contract: &'a ValidatedContract,
    quantity: SignedRational,
}

impl<'a> ContractPositionV1<'a> {
    pub const fn new(contract: &'a ValidatedContract, quantity: SignedRational) -> Self {
        Self { contract, quantity }
    }

    pub const fn contract(&self) -> &'a ValidatedContract {
        self.contract
    }

    pub const fn quantity(&self) -> SignedRational {
        self.quantity
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PayoffCompletenessStatusV1 {
    ExactOnDeclaredDomain,
    ApproximateOnDeclaredDomain,
    Incomplete,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum UnsupportedStateReasonV1 {
    ObservationCoordinateMismatch {
        leg_state_key: StateKeyV1,
        differing_fields: BTreeSet<SemanticField>,
    },
    ExactArithmeticOverflow {
        leg_state_key: StateKeyV1,
    },
    PortfolioAggregationOverflow {
        leg_state_key: StateKeyV1,
        validated_contract_digests: BTreeSet<Sha256Digest>,
    },
    ResidualComparisonOverflow {
        asset: String,
    },
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum UnmodeledResidualClassV1 {
    BasisOutsideNormalizedReference,
    TimingOutsideTerminalObservation,
    FxConversion,
    DefaultRealization,
    LegalEnforceability,
    Liquidity,
    JumpBetweenDeclaredStates,
    ModelOutsideDeclaredDomain,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PayoffAssumptionV1 {
    FiniteDeclaredDomainOnly,
    ObservationIsFinalCorrectedNormalizedValue,
    ContractRoundingPrecedesPositionQuantity,
    NoAssetConversion,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum StateEvaluationStatusV1 {
    Evaluated,
    Unsupported {
        reasons: BTreeSet<UnsupportedStateReasonV1>,
    },
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct StateResidualV1 {
    state_id: String,
    observation: SignedRational,
    status: StateEvaluationStatusV1,
    residual_by_asset: BTreeMap<String, SignedRational>,
}

impl StateResidualV1 {
    pub fn state_id(&self) -> &str {
        &self.state_id
    }

    pub const fn observation(&self) -> SignedRational {
        self.observation
    }

    pub const fn status(&self) -> &StateEvaluationStatusV1 {
        &self.status
    }

    pub const fn residual_by_asset(&self) -> &BTreeMap<String, SignedRational> {
        &self.residual_by_asset
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct WorstCaseAssetResidualV1 {
    asset: String,
    absolute_amount: SignedRational,
    state_ids: BTreeSet<String>,
}

impl WorstCaseAssetResidualV1 {
    pub fn asset(&self) -> &str {
        &self.asset
    }

    pub const fn absolute_amount(&self) -> SignedRational {
        self.absolute_amount
    }

    pub const fn state_ids(&self) -> &BTreeSet<String> {
        &self.state_ids
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct AggregatedPositionReceiptV1 {
    state_key: StateKeyV1,
    validated_contract_digests: BTreeSet<Sha256Digest>,
    quantity: SignedRational,
}

impl AggregatedPositionReceiptV1 {
    pub const fn state_key(&self) -> StateKeyV1 {
        self.state_key
    }

    pub const fn validated_contract_digests(&self) -> &BTreeSet<Sha256Digest> {
        &self.validated_contract_digests
    }

    pub const fn quantity(&self) -> SignedRational {
        self.quantity
    }
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct PayoffCompletenessReportV1 {
    status: PayoffCompletenessStatusV1,
    target: AggregatedPositionReceiptV1,
    candidate: Vec<AggregatedPositionReceiptV1>,
    domain_digest: Sha256Digest,
    states: Vec<StateResidualV1>,
    worst_case_by_asset: Vec<WorstCaseAssetResidualV1>,
    assumptions: BTreeSet<PayoffAssumptionV1>,
    unmodeled_residual_classes: BTreeSet<UnmodeledResidualClassV1>,
    explicit_non_equivalences: BTreeSet<String>,
}

impl PayoffCompletenessReportV1 {
    pub const fn status(&self) -> PayoffCompletenessStatusV1 {
        self.status
    }

    pub const fn target(&self) -> &AggregatedPositionReceiptV1 {
        &self.target
    }

    pub fn candidate(&self) -> &[AggregatedPositionReceiptV1] {
        &self.candidate
    }

    pub const fn domain_digest(&self) -> Sha256Digest {
        self.domain_digest
    }

    pub fn states(&self) -> &[StateResidualV1] {
        &self.states
    }

    pub fn worst_case_by_asset(&self) -> &[WorstCaseAssetResidualV1] {
        &self.worst_case_by_asset
    }

    pub const fn assumptions(&self) -> &BTreeSet<PayoffAssumptionV1> {
        &self.assumptions
    }

    pub const fn unmodeled_residual_classes(&self) -> &BTreeSet<UnmodeledResidualClassV1> {
        &self.unmodeled_residual_classes
    }

    pub const fn explicit_non_equivalences(&self) -> &BTreeSet<String> {
        &self.explicit_non_equivalences
    }
}

struct WorkingPosition<'a> {
    contract: &'a ValidatedContract,
    quantity: SignedRational,
    digests: BTreeSet<Sha256Digest>,
}

struct PositionGroup<'a> {
    contract: &'a ValidatedContract,
    quantities: Vec<SignedRational>,
    digests: BTreeSet<Sha256Digest>,
}

pub fn analyze_terminal_residual_v1(
    target: ContractPositionV1<'_>,
    candidate: &[ContractPositionV1<'_>],
    domain: &DeclaredStateDomainV1,
) -> Result<PayoffCompletenessReportV1, PayoffAnalysisError> {
    if candidate.len() > MAX_PORTFOLIO_LEGS_V1 {
        return Err(PayoffAnalysisError::TooManyPortfolioLegs {
            actual: candidate.len(),
            maximum: MAX_PORTFOLIO_LEGS_V1,
        });
    }

    let target_key = derive_state_key(target.contract);
    let target_receipt = AggregatedPositionReceiptV1 {
        state_key: target_key.state_key(),
        validated_contract_digests: BTreeSet::from([target_key.validated_contract_digest()]),
        quantity: target.quantity,
    };
    let mut explicit_non_equivalences = target
        .contract
        .semantics()
        .explicit_non_equivalences
        .clone();

    let mut groups: BTreeMap<StateKeyV1, PositionGroup<'_>> = BTreeMap::new();
    for leg in candidate {
        let receipt = derive_state_key(leg.contract);
        let state_key = receipt.state_key();
        explicit_non_equivalences.extend(
            leg.contract
                .semantics()
                .explicit_non_equivalences
                .iter()
                .cloned(),
        );
        if let Some(existing) = groups.get_mut(&state_key) {
            existing.digests.insert(receipt.validated_contract_digest());
            existing.quantities.push(leg.quantity);
        } else {
            groups.insert(
                state_key,
                PositionGroup {
                    contract: leg.contract,
                    quantities: vec![leg.quantity],
                    digests: BTreeSet::from([receipt.validated_contract_digest()]),
                },
            );
        }
    }
    let mut positions = BTreeMap::new();
    let mut aggregation_failures = BTreeSet::new();
    for (state_key, group) in groups {
        match sum_rationals_canonical(&group.quantities) {
            Ok(quantity) if !quantity.is_zero() => {
                positions.insert(
                    state_key,
                    WorkingPosition {
                        contract: group.contract,
                        quantity,
                        digests: group.digests,
                    },
                );
            }
            Ok(_) => {}
            Err(_) => {
                aggregation_failures.insert(
                    UnsupportedStateReasonV1::PortfolioAggregationOverflow {
                        leg_state_key: state_key,
                        validated_contract_digests: group.digests,
                    },
                );
            }
        }
    }

    if !aggregation_failures.is_empty() {
        return Ok(incomplete_for_every_state(
            target_receipt,
            receipts(&positions),
            domain,
            aggregation_failures,
            explicit_non_equivalences,
        ));
    }

    let mut mismatches = BTreeSet::new();
    for (state_key, position) in &positions {
        let differing_fields =
            coordinate_differences(target.contract.semantics(), position.contract.semantics());
        if !differing_fields.is_empty() {
            mismatches.insert(UnsupportedStateReasonV1::ObservationCoordinateMismatch {
                leg_state_key: *state_key,
                differing_fields,
            });
        }
    }
    if !mismatches.is_empty() {
        return Ok(incomplete_for_every_state(
            target_receipt,
            receipts(&positions),
            domain,
            mismatches,
            explicit_non_equivalences,
        ));
    }

    let mut states = Vec::with_capacity(domain.states.len());
    let zero = SignedRational::new(0, 1).expect("canonical zero is representable");
    let mut active_assets = BTreeSet::from([target.contract.semantics().settlement_asset.clone()]);
    active_assets.extend(
        positions
            .values()
            .map(|position| position.contract.semantics().settlement_asset.clone()),
    );
    let mut worst: BTreeMap<String, (SignedRational, BTreeSet<String>)> = active_assets
        .iter()
        .map(|asset| (asset.clone(), (zero, BTreeSet::new())))
        .collect();
    let mut any_nonzero = false;
    let mut arithmetic_failures = BTreeSet::new();

    for (state_id, observation) in &domain.states {
        let mut residual = BTreeMap::new();
        let mut state_failure = None;
        match evaluate_position(target.contract, target.quantity, *observation) {
            Ok((asset, amount)) => {
                if add_asset(&mut residual, asset, amount).is_err() {
                    state_failure = Some(target_key.state_key());
                }
            }
            Err(_) => state_failure = Some(target_key.state_key()),
        }
        if state_failure.is_none() {
            for (state_key, position) in &positions {
                match evaluate_position(position.contract, position.quantity, *observation)
                    .and_then(|(asset, amount)| {
                        subtract_asset(&mut residual, asset, amount).map(|_| ())
                    }) {
                    Ok(()) => {}
                    Err(_) => {
                        state_failure = Some(*state_key);
                        break;
                    }
                }
            }
        }

        residual.retain(|_, amount| !amount.is_zero());
        if let Some(state_key) = state_failure {
            arithmetic_failures.insert(UnsupportedStateReasonV1::ExactArithmeticOverflow {
                leg_state_key: state_key,
            });
            states.push(StateResidualV1 {
                state_id: state_id.clone(),
                observation: *observation,
                status: StateEvaluationStatusV1::Unsupported {
                    reasons: BTreeSet::from([UnsupportedStateReasonV1::ExactArithmeticOverflow {
                        leg_state_key: state_key,
                    }]),
                },
                residual_by_asset: BTreeMap::new(),
            });
            continue;
        }

        let mut next_worst = worst.clone();
        let mut worst_failure = None;
        for asset in &active_assets {
            let amount = residual.get(asset).copied().unwrap_or(zero);
            let magnitude = match amount.checked_abs() {
                Ok(value) => value,
                Err(_) => {
                    worst_failure = Some(asset.clone());
                    break;
                }
            };
            match next_worst.get_mut(asset) {
                Some((current, state_ids)) => match magnitude.checked_cmp(*current) {
                    Ok(Ordering::Greater) => {
                        *current = magnitude;
                        *state_ids = BTreeSet::from([state_id.clone()]);
                    }
                    Ok(Ordering::Equal) => {
                        state_ids.insert(state_id.clone());
                    }
                    Ok(Ordering::Less) => {}
                    Err(_) => {
                        worst_failure = Some(asset.clone());
                        break;
                    }
                },
                None => {
                    next_worst.insert(
                        asset.clone(),
                        (magnitude, BTreeSet::from([state_id.clone()])),
                    );
                }
            }
        }
        if let Some(asset) = worst_failure {
            let reason = UnsupportedStateReasonV1::ResidualComparisonOverflow { asset };
            arithmetic_failures.insert(reason.clone());
            states.push(StateResidualV1 {
                state_id: state_id.clone(),
                observation: *observation,
                status: StateEvaluationStatusV1::Unsupported {
                    reasons: BTreeSet::from([reason]),
                },
                residual_by_asset: BTreeMap::new(),
            });
            continue;
        }

        any_nonzero |= !residual.is_empty();
        worst = next_worst;
        states.push(StateResidualV1 {
            state_id: state_id.clone(),
            observation: *observation,
            status: StateEvaluationStatusV1::Evaluated,
            residual_by_asset: residual,
        });
    }

    if !arithmetic_failures.is_empty() {
        return Ok(incomplete_for_every_state(
            target_receipt,
            receipts(&positions),
            domain,
            arithmetic_failures,
            explicit_non_equivalences,
        ));
    }

    let status = if any_nonzero {
        PayoffCompletenessStatusV1::ApproximateOnDeclaredDomain
    } else {
        PayoffCompletenessStatusV1::ExactOnDeclaredDomain
    };
    let worst_case_by_asset = worst
        .into_iter()
        .map(
            |(asset, (absolute_amount, state_ids))| WorstCaseAssetResidualV1 {
                asset,
                absolute_amount,
                state_ids,
            },
        )
        .collect();

    Ok(PayoffCompletenessReportV1 {
        status,
        target: target_receipt,
        candidate: receipts(&positions),
        domain_digest: domain.digest,
        states,
        worst_case_by_asset,
        assumptions: assumptions(),
        unmodeled_residual_classes: unmodeled_residual_classes(),
        explicit_non_equivalences,
    })
}

fn evaluate_position(
    contract: &ValidatedContract,
    quantity: SignedRational,
    observation: SignedRational,
) -> Result<(String, SignedRational), ExactError> {
    let semantics = contract.semantics();
    let amount = if comparator_matches(&semantics.comparator, observation)? {
        let unit_scale = SignedRational::from_scaled(semantics.settlement_unit_scale)?;
        let quantum = SignedRational::from_scaled(semantics.rounding_quantum)?;
        let raw = semantics.payoff_amount.checked_mul(unit_scale)?;
        quantize_exact(raw, quantum, semantics.rounding_mode)?
    } else {
        SignedRational::new(0, 1)?
    };
    Ok((
        semantics.settlement_asset.clone(),
        quantity.checked_mul(amount)?,
    ))
}

fn comparator_matches(
    comparator: &Comparator,
    observation: SignedRational,
) -> Result<bool, ExactError> {
    Ok(match comparator {
        Comparator::LessThan { threshold } => observation.checked_cmp(*threshold)?.is_lt(),
        Comparator::LessThanOrEqual { threshold } => !observation.checked_cmp(*threshold)?.is_gt(),
        Comparator::Equal { threshold } => observation.checked_cmp(*threshold)?.is_eq(),
        Comparator::GreaterThanOrEqual { threshold } => {
            !observation.checked_cmp(*threshold)?.is_lt()
        }
        Comparator::GreaterThan { threshold } => observation.checked_cmp(*threshold)?.is_gt(),
        Comparator::InRange {
            lower,
            upper,
            endpoints,
        } => {
            let lower_cmp = observation.checked_cmp(*lower)?;
            let upper_cmp = observation.checked_cmp(*upper)?;
            let lower_matches = match endpoints {
                EndpointPolicy::OpenOpen | EndpointPolicy::OpenClosed => lower_cmp.is_gt(),
                EndpointPolicy::ClosedOpen | EndpointPolicy::ClosedClosed => !lower_cmp.is_lt(),
            };
            let upper_matches = match endpoints {
                EndpointPolicy::OpenOpen | EndpointPolicy::ClosedOpen => upper_cmp.is_lt(),
                EndpointPolicy::OpenClosed | EndpointPolicy::ClosedClosed => !upper_cmp.is_gt(),
            };
            lower_matches && upper_matches
        }
    })
}

fn add_asset(
    residual: &mut BTreeMap<String, SignedRational>,
    asset: String,
    amount: SignedRational,
) -> Result<(), ExactError> {
    let next = match residual.get(&asset) {
        Some(current) => current.checked_add(amount)?,
        None => amount,
    };
    residual.insert(asset, next);
    Ok(())
}

fn subtract_asset(
    residual: &mut BTreeMap<String, SignedRational>,
    asset: String,
    amount: SignedRational,
) -> Result<(), ExactError> {
    let current = residual
        .get(&asset)
        .copied()
        .unwrap_or(SignedRational::new(0, 1)?);
    residual.insert(asset, current.checked_sub(amount)?);
    Ok(())
}

fn coordinate_differences(
    target: &NormalizedTerminalSemantics,
    candidate: &NormalizedTerminalSemantics,
) -> BTreeSet<SemanticField> {
    let mut fields = BTreeSet::new();
    macro_rules! differs {
        ($field:ident, $variant:ident) => {
            if target.$field != candidate.$field {
                fields.insert(SemanticField::$variant);
            }
        };
    }
    differs!(reference_namespace, ReferenceNamespace);
    differs!(reference_identifier, ReferenceIdentifier);
    differs!(reference_unit, ReferenceUnit);
    differs!(benchmark_administrator, BenchmarkAdministrator);
    differs!(methodology_version, MethodologyVersion);
    differs!(methodology_sha256, MethodologySha256);
    differs!(fallback_rule, FallbackRule);
    differs!(calendar, Calendar);
    differs!(timezone, Timezone);
    differs!(observation_start, ObservationStart);
    differs!(observation_end, ObservationEnd);
    differs!(sampling_rule, SamplingRule);
    differs!(disruption_rule, DisruptionRule);
    differs!(correction_rule, CorrectionRule);
    fields
}

fn receipts(
    positions: &BTreeMap<StateKeyV1, WorkingPosition<'_>>,
) -> Vec<AggregatedPositionReceiptV1> {
    positions
        .iter()
        .map(|(state_key, position)| AggregatedPositionReceiptV1 {
            state_key: *state_key,
            validated_contract_digests: position.digests.clone(),
            quantity: position.quantity,
        })
        .collect()
}

fn incomplete_for_every_state(
    target: AggregatedPositionReceiptV1,
    candidate: Vec<AggregatedPositionReceiptV1>,
    domain: &DeclaredStateDomainV1,
    reasons: BTreeSet<UnsupportedStateReasonV1>,
    explicit_non_equivalences: BTreeSet<String>,
) -> PayoffCompletenessReportV1 {
    PayoffCompletenessReportV1 {
        status: PayoffCompletenessStatusV1::Incomplete,
        target,
        candidate,
        domain_digest: domain.digest,
        states: domain
            .states
            .iter()
            .map(|(state_id, observation)| StateResidualV1 {
                state_id: state_id.clone(),
                observation: *observation,
                status: StateEvaluationStatusV1::Unsupported {
                    reasons: reasons.clone(),
                },
                residual_by_asset: BTreeMap::new(),
            })
            .collect(),
        worst_case_by_asset: Vec::new(),
        assumptions: assumptions(),
        unmodeled_residual_classes: unmodeled_residual_classes(),
        explicit_non_equivalences,
    }
}

fn assumptions() -> BTreeSet<PayoffAssumptionV1> {
    BTreeSet::from([
        PayoffAssumptionV1::FiniteDeclaredDomainOnly,
        PayoffAssumptionV1::ObservationIsFinalCorrectedNormalizedValue,
        PayoffAssumptionV1::ContractRoundingPrecedesPositionQuantity,
        PayoffAssumptionV1::NoAssetConversion,
    ])
}

fn unmodeled_residual_classes() -> BTreeSet<UnmodeledResidualClassV1> {
    BTreeSet::from([
        UnmodeledResidualClassV1::BasisOutsideNormalizedReference,
        UnmodeledResidualClassV1::TimingOutsideTerminalObservation,
        UnmodeledResidualClassV1::FxConversion,
        UnmodeledResidualClassV1::DefaultRealization,
        UnmodeledResidualClassV1::LegalEnforceability,
        UnmodeledResidualClassV1::Liquidity,
        UnmodeledResidualClassV1::JumpBetweenDeclaredStates,
        UnmodeledResidualClassV1::ModelOutsideDeclaredDomain,
    ])
}

fn state_domain_digest(states: &BTreeMap<String, SignedRational>) -> Sha256Digest {
    let mut preimage = DECLARED_STATE_DOMAIN_V1.to_vec();
    preimage.extend_from_slice(&1_u16.to_be_bytes());
    preimage.extend_from_slice(
        &u32::try_from(states.len())
            .expect("bounded P2 state count fits u32")
            .to_be_bytes(),
    );
    for (id, observation) in states {
        preimage.extend_from_slice(
            &u32::try_from(id.len())
                .expect("bounded P2 state identifier length fits u32")
                .to_be_bytes(),
        );
        preimage.extend_from_slice(id.as_bytes());
        preimage.extend_from_slice(&observation.numerator().to_be_bytes());
        preimage.extend_from_slice(&observation.denominator().to_be_bytes());
    }
    Sha256Digest::from_bytes(Sha256::digest(preimage).into())
}

fn valid_state_id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 128
        && value.bytes().all(|byte| {
            byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b':' | b'/' | b'-')
        })
}
