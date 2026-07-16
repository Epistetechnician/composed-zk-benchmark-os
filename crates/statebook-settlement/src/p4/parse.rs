use std::collections::BTreeSet;

use serde_json::Value;
use statebook_core::SignedRational;

use crate::DigestV1;
use crate::{
    AssurancePropertyV1, AssuranceRootV1, AssuranceVerdictV1, DependencyDisclosureV1, RootClassV1,
};

use super::bounds::MAX_FIXTURE_BYTES_V1;
use super::budget::default_axis;
use super::digest::ledger_tip_digest;
use super::error::SettlementParseErrorV1;
use super::types::{
    AssuranceTierPolicyV1, AtomicLinkedExchangePlanV1, BreakerScopeV1, BreakerStateV1, ClockV1,
    ConservativeValuationProfileV1, DirectionV1, EvidenceObservationV1, EvidenceSnapshotV1,
    ExactRationalV1, ExternalRiskReducingObligationV1, ExternalizationRequestV1,
    FinancialBasisKindV1, FinancialBasisV1, GateOverridesV1, LinkedPlanLegV1, PolicyHysteresisV1,
    QueueStateV1, QueueStatusV1, RecoverySnapshotV1, ReleaseClassV1, SettlementPolicyV1,
    SettlementScenarioV1, SettlementStateV1, TierFractionV1, TransferStateV1, TransferStatusV1,
    ValuationObservationV1,
};

const FIXTURE_SCHEMA_V1: &str = "statebook-settlement-fixture:v1";

fn validate_rational_parse(
    numerator: &str,
    denominator: &str,
) -> Result<SignedRational, SettlementParseErrorV1> {
    if numerator.starts_with('+') || (numerator.starts_with('0') && numerator.len() > 1) {
        return Err(SettlementParseErrorV1::InvalidRational {
            numerator: numerator.to_owned(),
            denominator: denominator.to_owned(),
        });
    }
    SignedRational::parse(numerator, denominator).map_err(|_| {
        SettlementParseErrorV1::InvalidRational {
            numerator: numerator.to_owned(),
            denominator: denominator.to_owned(),
        }
    })
}

pub fn parse_settlement_scenario_v1(
    bytes: &[u8],
) -> Result<SettlementScenarioV1, SettlementParseErrorV1> {
    if bytes.len() > MAX_FIXTURE_BYTES_V1 {
        return Err(SettlementParseErrorV1::FixtureTooLarge {
            max_fixture_bytes_v1: MAX_FIXTURE_BYTES_V1,
        });
    }
    let value = parse_unique_json(bytes)?;
    let object = value
        .as_object()
        .ok_or_else(|| SettlementParseErrorV1::InvalidJson("expected object".to_owned()))?;
    let schema = object
        .get("schema_version")
        .and_then(Value::as_str)
        .ok_or(missing_field("schema_version"))?;
    if schema != FIXTURE_SCHEMA_V1 {
        return Err(SettlementParseErrorV1::InvalidSchemaVersion(
            schema.to_owned(),
        ));
    }
    let scenario_id = required_string(object, "scenario_id")?;
    let clock = parse_clock(object.get("clock").ok_or(missing_field("clock"))?)?;
    let policy = parse_policy(object.get("policy").ok_or(missing_field("policy"))?)?;
    let valuation_profile = parse_valuation(
        object
            .get("valuation_profile")
            .ok_or(missing_field("valuation_profile"))?,
    )?;
    let evidence_snapshot = parse_evidence(
        object
            .get("evidence_snapshot")
            .ok_or(missing_field("evidence_snapshot"))?,
    )?;
    let initial_state = parse_state(
        object
            .get("initial_state")
            .ok_or(missing_field("initial_state"))?,
        &policy,
        clock.now(),
    )?;
    let request = parse_request(
        object.get("request").ok_or(missing_field("request"))?,
        evidence_snapshot.clone(),
        valuation_profile.clone(),
        policy.clone(),
    )?;
    Ok(SettlementScenarioV1 {
        scenario_id,
        clock,
        policy,
        valuation_profile,
        evidence_snapshot,
        initial_state,
        request,
    })
}

fn parse_unique_json(bytes: &[u8]) -> Result<Value, SettlementParseErrorV1> {
    serde_json::from_slice(bytes)
        .map_err(|error| SettlementParseErrorV1::InvalidJson(error.to_string()))
}

fn missing_field(name: &'static str) -> SettlementParseErrorV1 {
    SettlementParseErrorV1::MissingField(name.to_owned())
}

fn required_string(
    object: &serde_json::Map<String, Value>,
    field: &str,
) -> Result<String, SettlementParseErrorV1> {
    object
        .get(field)
        .and_then(Value::as_str)
        .map(str::to_owned)
        .ok_or_else(|| SettlementParseErrorV1::MissingField(field.to_owned()))
}

fn parse_digest(value: &Value) -> Result<DigestV1, SettlementParseErrorV1> {
    let text = value
        .as_str()
        .ok_or_else(|| SettlementParseErrorV1::InvalidDigest("non-string".to_owned()))?;
    if text.len() != 64
        || !text
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err(SettlementParseErrorV1::InvalidDigest(text.to_owned()));
    }
    let mut bytes = [0_u8; 32];
    hex::decode_to_slice(text, &mut bytes)
        .map_err(|_| SettlementParseErrorV1::InvalidDigest(text.to_owned()))?;
    Ok(DigestV1::from_raw_bytes(bytes))
}

fn parse_rational(value: &Value) -> Result<SignedRational, SettlementParseErrorV1> {
    let object = value
        .as_object()
        .ok_or_else(|| SettlementParseErrorV1::InvalidRational {
            numerator: "missing".to_owned(),
            denominator: "missing".to_owned(),
        })?;
    let numerator = object
        .get("numerator")
        .and_then(Value::as_str)
        .ok_or_else(|| SettlementParseErrorV1::InvalidRational {
            numerator: "missing".to_owned(),
            denominator: "missing".to_owned(),
        })?;
    let denominator = object
        .get("denominator")
        .and_then(Value::as_str)
        .ok_or_else(|| SettlementParseErrorV1::InvalidRational {
            numerator: numerator.to_owned(),
            denominator: "missing".to_owned(),
        })?;
    validate_rational_parse(numerator, denominator)
}

fn parse_clock(value: &Value) -> Result<ClockV1, SettlementParseErrorV1> {
    let object = value.as_object().ok_or(missing_field("clock"))?;
    let now = object
        .get("now")
        .and_then(Value::as_i64)
        .ok_or(missing_field("clock.now"))?;
    Ok(ClockV1::new(now))
}

fn parse_tier_fraction(value: &Value) -> Result<TierFractionV1, SettlementParseErrorV1> {
    let object = value.as_object().ok_or(missing_field("tier_fraction"))?;
    Ok(TierFractionV1 {
        instant_fraction: parse_rational(
            object
                .get("instant_fraction")
                .ok_or(missing_field("instant_fraction"))?,
        )?,
        delay_seconds: object
            .get("delay_seconds")
            .and_then(Value::as_i64)
            .ok_or(missing_field("delay_seconds"))?,
    })
}

fn parse_policy(value: &Value) -> Result<SettlementPolicyV1, SettlementParseErrorV1> {
    let object = value.as_object().ok_or(missing_field("policy"))?;
    let assurance = object
        .get("assurance_tiers")
        .ok_or(missing_field("assurance_tiers"))?;
    let assurance_object = assurance
        .as_object()
        .ok_or(missing_field("assurance_tiers"))?;
    let hysteresis = object
        .get("hysteresis")
        .ok_or(missing_field("hysteresis"))?;
    let hysteresis_object = hysteresis.as_object().ok_or(missing_field("hysteresis"))?;
    Ok(SettlementPolicyV1 {
        policy_id: required_string(object, "policy_id")?,
        policy_version: object
            .get("policy_version")
            .and_then(Value::as_u64)
            .ok_or(missing_field("policy_version"))? as u32,
        policy_digest: parse_digest(
            object
                .get("policy_digest")
                .ok_or(missing_field("policy_digest"))?,
        )?,
        assurance_tiers: AssuranceTierPolicyV1 {
            quarantined: parse_tier_fraction(
                assurance_object
                    .get("quarantined")
                    .ok_or(missing_field("quarantined"))?,
            )?,
            unproven_or_novel: parse_tier_fraction(
                assurance_object
                    .get("unproven_or_novel")
                    .ok_or(missing_field("unproven_or_novel"))?,
            )?,
            currently_assured: parse_tier_fraction(
                assurance_object
                    .get("currently_assured")
                    .ok_or(missing_field("currently_assured"))?,
            )?,
            strong_current_assurance_low_impact: parse_tier_fraction(
                assurance_object
                    .get("strong_current_assurance_low_impact")
                    .ok_or(missing_field("strong_current_assurance_low_impact"))?,
            )?,
        },
        hysteresis: PolicyHysteresisV1 {
            min_relax_dwell_seconds: hysteresis_object
                .get("min_relax_dwell_seconds")
                .and_then(Value::as_i64)
                .ok_or(missing_field("min_relax_dwell_seconds"))?,
            required_clean_epochs: hysteresis_object
                .get("required_clean_epochs")
                .and_then(Value::as_u64)
                .ok_or(missing_field("required_clean_epochs"))?
                as u32,
            successor_policy_digest: parse_digest(
                hysteresis_object
                    .get("successor_policy_digest")
                    .ok_or(missing_field("successor_policy_digest"))?,
            )?,
        },
    })
}

fn parse_valuation(
    value: &Value,
) -> Result<ConservativeValuationProfileV1, SettlementParseErrorV1> {
    let object = value
        .as_object()
        .ok_or(missing_field("valuation_profile"))?;
    let observations = object
        .get("observations")
        .and_then(Value::as_array)
        .ok_or(missing_field("observations"))?;
    if observations.len() > super::bounds::MAX_VALUATION_OBSERVATIONS_V1 {
        return Err(SettlementParseErrorV1::CollectionLimit {
            field: "valuation_profile.observations",
        });
    }
    let mut parsed_observations = Vec::new();
    for observation in observations {
        let item = observation
            .as_object()
            .ok_or(missing_field("observation"))?;
        parsed_observations.push(ValuationObservationV1 {
            asset: required_string(item, "asset")?,
            rate: ExactRationalV1 {
                numerator: item
                    .get("rate")
                    .and_then(|v| v.get("numerator"))
                    .and_then(Value::as_str)
                    .unwrap_or("0")
                    .to_owned(),
                denominator: item
                    .get("rate")
                    .and_then(|v| v.get("denominator"))
                    .and_then(Value::as_str)
                    .unwrap_or("1")
                    .to_owned(),
            },
            observed_at: item
                .get("observed_at")
                .and_then(Value::as_i64)
                .ok_or(missing_field("observed_at"))?,
            root_id: required_string(item, "root_id")?,
            root_class: parse_root_class(
                item.get("root_class").ok_or(missing_field("root_class"))?,
            )?,
        });
    }
    let independence = object
        .get("independence_roots")
        .and_then(Value::as_array)
        .ok_or(missing_field("independence_roots"))?;
    Ok(ConservativeValuationProfileV1 {
        profile_id: required_string(object, "profile_id")?,
        numeraire_asset: required_string(object, "numeraire_asset")?,
        max_age_seconds: object
            .get("max_age_seconds")
            .and_then(Value::as_i64)
            .ok_or(missing_field("max_age_seconds"))?,
        stress_multiplier: parse_rational(
            object
                .get("stress_multiplier")
                .ok_or(missing_field("stress_multiplier"))?,
        )?,
        observations: parsed_observations,
        independence_roots: independence
            .iter()
            .filter_map(|value| value.as_str().map(str::to_owned))
            .collect(),
    })
}

fn parse_root_class(value: &Value) -> Result<RootClassV1, SettlementParseErrorV1> {
    match value.as_str() {
        Some("data") => Ok(RootClassV1::Data),
        Some("operator") => Ok(RootClassV1::Operator),
        Some("cloud") => Ok(RootClassV1::Cloud),
        Some("kms") => Ok(RootClassV1::Kms),
        Some("rpc") => Ok(RootClassV1::Rpc),
        Some("ci_cd") => Ok(RootClassV1::CiCd),
        Some("model") => Ok(RootClassV1::Model),
        Some("signer") => Ok(RootClassV1::Signer),
        _ => Err(SettlementParseErrorV1::InvalidJson("root_class".to_owned())),
    }
}

fn parse_assurance_property(value: &str) -> Result<AssurancePropertyV1, SettlementParseErrorV1> {
    match value {
        "action_authorization" => Ok(AssurancePropertyV1::ActionAuthorization),
        "source_authenticity_and_freshness" => {
            Ok(AssurancePropertyV1::SourceAuthenticityAndFreshness)
        }
        "calculation_integrity" => Ok(AssurancePropertyV1::CalculationIntegrity),
        "state_transition_integrity" => Ok(AssurancePropertyV1::StateTransitionIntegrity),
        "solvency_and_liquid_resource_support" => {
            Ok(AssurancePropertyV1::SolvencyAndLiquidResourceSupport)
        }
        "destination_and_route_policy" => Ok(AssurancePropertyV1::DestinationAndRoutePolicy),
        "anomaly_and_emergency_clearance" => Ok(AssurancePropertyV1::AnomalyAndEmergencyClearance),
        "evidence_root_disclosure" => Ok(AssurancePropertyV1::EvidenceRootDisclosure),
        "financial_basis_binding" => Ok(AssurancePropertyV1::FinancialBasisBinding),
        _ => Err(SettlementParseErrorV1::InvalidJson(value.to_owned())),
    }
}

fn parse_root(value: &Value) -> Result<AssuranceRootV1, SettlementParseErrorV1> {
    let object = value.as_object().ok_or(missing_field("root"))?;
    let root_id = required_string(object, "root_id")?;
    let root_class = object
        .get("root_class")
        .cloned()
        .ok_or(missing_field("root_class"))?;
    let root_class: RootClassV1 = serde_json::from_value(root_class)
        .map_err(|error| SettlementParseErrorV1::InvalidJson(error.to_string()))?;
    Ok(AssuranceRootV1::new(root_class, root_id))
}

fn parse_evidence(value: &Value) -> Result<EvidenceSnapshotV1, SettlementParseErrorV1> {
    let object = value
        .as_object()
        .ok_or(missing_field("evidence_snapshot"))?;
    let observations = object
        .get("observations")
        .and_then(Value::as_array)
        .ok_or(missing_field("observations"))?;
    if observations.len() > super::bounds::MAX_EVIDENCE_OBSERVATIONS_V1 {
        return Err(SettlementParseErrorV1::CollectionLimit {
            field: "evidence_snapshot.observations",
        });
    }
    let mut parsed = Vec::new();
    for observation in observations {
        let item = observation
            .as_object()
            .ok_or(missing_field("observation"))?;
        let current = item
            .get("current_roots")
            .and_then(Value::as_array)
            .map(|values| values.as_slice())
            .unwrap_or(&[]);
        let dependency = item
            .get("dependency_roots")
            .and_then(Value::as_array)
            .map(|values| values.as_slice())
            .unwrap_or(&[]);
        parsed.push(EvidenceObservationV1 {
            property: parse_assurance_property(required_string(item, "property")?.as_str())?,
            verdict: match item.get("verdict").and_then(Value::as_str) {
                Some("pass") => AssuranceVerdictV1::Pass,
                Some("fail") => AssuranceVerdictV1::Fail,
                _ => AssuranceVerdictV1::Unknown,
            },
            current_roots: current.iter().map(parse_root).collect::<Result<_, _>>()?,
            dependency_roots: dependency
                .iter()
                .map(parse_root)
                .collect::<Result<_, _>>()?,
            dependency_disclosure: match item.get("dependency_disclosure").and_then(Value::as_str) {
                Some("complete") => DependencyDisclosureV1::Complete,
                _ => DependencyDisclosureV1::Unknown,
            },
            observed_at: item
                .get("observed_at")
                .and_then(Value::as_i64)
                .ok_or(missing_field("observed_at"))?,
            expires_at: item
                .get("expires_at")
                .and_then(Value::as_i64)
                .ok_or(missing_field("expires_at"))?,
            bound_request_id: required_string(item, "bound_request_id")
                .unwrap_or_else(|_| required_string(item, "request_id").unwrap_or_default()),
            replayed: item
                .get("replayed")
                .and_then(Value::as_bool)
                .unwrap_or(false),
            equivocated: item
                .get("equivocated")
                .and_then(Value::as_bool)
                .unwrap_or(false),
        });
    }
    Ok(EvidenceSnapshotV1 {
        snapshot_id: required_string(object, "snapshot_id")?,
        request_id: required_string(object, "request_id")?,
        nonce: required_string(object, "nonce")?,
        observations: parsed,
    })
}

fn parse_state(
    value: &Value,
    scenario_policy: &SettlementPolicyV1,
    now: i64,
) -> Result<SettlementStateV1, SettlementParseErrorV1> {
    let object = value.as_object().ok_or(missing_field("initial_state"))?;
    let ledger = object.get("ledger").ok_or(missing_field("ledger"))?;
    let ledger_object = ledger.as_object().ok_or(missing_field("ledger"))?;
    let axes = ledger_object
        .get("axes")
        .and_then(Value::as_array)
        .ok_or(missing_field("axes"))?;
    if axes.len() > super::bounds::MAX_BUDGET_AXES_V1 {
        return Err(SettlementParseErrorV1::CollectionLimit {
            field: "ledger.axes",
        });
    }
    let mut parsed_axes = Vec::new();
    for axis in axes {
        let item = axis.as_object().ok_or(missing_field("axis"))?;
        parsed_axes.push(default_axis(
            &required_string(item, "asset")?,
            parse_rational(item.get("cap").ok_or(missing_field("cap"))?)?,
        ));
    }
    let mut ledger_state = super::types::BudgetLedgerStateV1 {
        tip_digest: parse_digest(
            ledger_object
                .get("tip_digest")
                .ok_or(missing_field("tip_digest"))?,
        )?,
        epoch: ledger_object
            .get("epoch")
            .and_then(Value::as_u64)
            .unwrap_or(1) as u32,
        axes: parsed_axes,
        journal: Vec::new(),
    };
    ledger_state.tip_digest = ledger_tip_digest(&ledger_state);
    let queue = object.get("queue").ok_or(missing_field("queue"))?;
    let queue_object = queue.as_object().ok_or(missing_field("queue"))?;
    let transfer = object.get("transfer").ok_or(missing_field("transfer"))?;
    let transfer_object = transfer.as_object().ok_or(missing_field("transfer"))?;
    let breakers = object
        .get("breakers")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    if breakers.len() > super::bounds::MAX_BREAKER_SCOPES_V1 {
        return Err(SettlementParseErrorV1::CollectionLimit { field: "breakers" });
    }
    let recovery = object.get("recovery").ok_or(missing_field("recovery"))?;
    let recovery_object = recovery.as_object().ok_or(missing_field("recovery"))?;
    Ok(SettlementStateV1 {
        ledger: ledger_state.clone(),
        queue: QueueStateV1 {
            status: parse_queue_status(
                queue_object
                    .get("status")
                    .and_then(Value::as_str)
                    .unwrap_or("none"),
            )?,
            parts: Vec::new(),
        },
        transfer: TransferStateV1 {
            status: parse_transfer_status(
                transfer_object
                    .get("status")
                    .and_then(Value::as_str)
                    .unwrap_or("unreserved"),
            )?,
        },
        breakers: breakers
            .iter()
            .map(parse_breaker)
            .collect::<Result<_, _>>()?,
        recovery: RecoverySnapshotV1 {
            profile_digest: parse_digest(
                recovery_object
                    .get("profile_digest")
                    .ok_or(missing_field("profile_digest"))?,
            )?,
            halted_paths: BTreeSet::new(),
            reconciliation_mismatch: recovery_object
                .get("reconciliation_mismatch")
                .and_then(Value::as_bool)
                .unwrap_or(false),
            canary_failed: recovery_object
                .get("canary_failed")
                .and_then(Value::as_bool)
                .unwrap_or(false),
        },
        expected_ledger_tip: match object.get("expected_ledger_tip") {
            Some(value) => parse_digest(value)?,
            None => ledger_state.tip_digest,
        },
        applied_challenge_ids: object
            .get("applied_challenge_ids")
            .and_then(Value::as_array)
            .map(|items| {
                items
                    .iter()
                    .map(|item| {
                        item.as_str().map(str::to_owned).ok_or_else(|| {
                            SettlementParseErrorV1::InvalidIdentifier(
                                "applied_challenge_ids".to_owned(),
                            )
                        })
                    })
                    .collect::<Result<BTreeSet<_>, _>>()
            })
            .transpose()?
            .unwrap_or_default(),
        active_policy: match object.get("active_policy") {
            Some(value) => parse_policy(value)?,
            None => scenario_policy.clone(),
        },
        last_policy_change_at: object
            .get("last_policy_change_at")
            .and_then(Value::as_i64)
            .unwrap_or(now),
        clean_epochs: object
            .get("clean_epochs")
            .and_then(Value::as_u64)
            .unwrap_or(0) as u32,
    })
}

fn parse_breaker(value: &Value) -> Result<BreakerScopeV1, SettlementParseErrorV1> {
    let object = value.as_object().ok_or(missing_field("breaker"))?;
    Ok(BreakerScopeV1 {
        scope_id: required_string(object, "scope_id")?,
        state: parse_breaker_state(
            object
                .get("state")
                .and_then(Value::as_str)
                .unwrap_or("normal"),
        )?,
        expires_at: object.get("expires_at").and_then(Value::as_i64),
        renewal_count: object
            .get("renewal_count")
            .and_then(Value::as_u64)
            .unwrap_or(0) as u32,
        renewal_ceiling: object
            .get("renewal_ceiling")
            .and_then(Value::as_u64)
            .unwrap_or(1) as u32,
    })
}

fn parse_breaker_state(value: &str) -> Result<BreakerStateV1, SettlementParseErrorV1> {
    match value {
        "normal" => Ok(BreakerStateV1::Normal),
        "guarded" => Ok(BreakerStateV1::Guarded),
        "challenged" => Ok(BreakerStateV1::Challenged),
        "halted" => Ok(BreakerStateV1::Halted),
        "resolution" => Ok(BreakerStateV1::Resolution),
        "recovery" => Ok(BreakerStateV1::Recovery),
        _ => Err(SettlementParseErrorV1::InvalidJson(value.to_owned())),
    }
}

fn parse_queue_status(value: &str) -> Result<QueueStatusV1, SettlementParseErrorV1> {
    match value {
        "none" => Ok(QueueStatusV1::None),
        "queued" => Ok(QueueStatusV1::Queued),
        "challenged" => Ok(QueueStatusV1::Challenged),
        "evidence_expired" => Ok(QueueStatusV1::EvidenceExpired),
        "frozen" => Ok(QueueStatusV1::Frozen),
        "cancelled" => Ok(QueueStatusV1::Cancelled),
        "revalidation_required" => Ok(QueueStatusV1::RevalidationRequired),
        _ => Err(SettlementParseErrorV1::InvalidJson(value.to_owned())),
    }
}

fn parse_transfer_status(value: &str) -> Result<TransferStatusV1, SettlementParseErrorV1> {
    match value {
        "unreserved" => Ok(TransferStatusV1::Unreserved),
        "reserved" => Ok(TransferStatusV1::Reserved),
        "submitted" => Ok(TransferStatusV1::Submitted),
        "source_observed" => Ok(TransferStatusV1::SourceObserved),
        "source_finalized" => Ok(TransferStatusV1::SourceFinalized),
        "destination_observed" => Ok(TransferStatusV1::DestinationObserved),
        "destination_finalized" => Ok(TransferStatusV1::DestinationFinalized),
        "consumed" => Ok(TransferStatusV1::Consumed),
        "proven_no_outflow" => Ok(TransferStatusV1::ProvenNoOutflow),
        _ => Err(SettlementParseErrorV1::InvalidJson(value.to_owned())),
    }
}

fn parse_release_class(value: &str) -> Result<ReleaseClassV1, SettlementParseErrorV1> {
    match value {
        "internal_risk_state" => Ok(ReleaseClassV1::InternalRiskState),
        "atomic_linked_exchange" => Ok(ReleaseClassV1::AtomicLinkedExchange),
        "external_risk_reducing_obligation" => Ok(ReleaseClassV1::ExternalRiskReducingObligation),
        "external_unconditional" => Ok(ReleaseClassV1::ExternalUnconditional),
        "systemic_or_exceptional" => Ok(ReleaseClassV1::SystemicOrExceptional),
        _ => Err(SettlementParseErrorV1::InvalidJson(value.to_owned())),
    }
}

fn parse_direction(value: &str) -> Result<DirectionV1, SettlementParseErrorV1> {
    match value {
        "outbound" => Ok(DirectionV1::Outbound),
        "inbound" => Ok(DirectionV1::Inbound),
        _ => Err(SettlementParseErrorV1::InvalidJson(value.to_owned())),
    }
}

fn parse_gate_overrides(value: Option<&Value>) -> GateOverridesV1 {
    let Some(object) = value.and_then(Value::as_object) else {
        return GateOverridesV1::default();
    };
    let flag = |field: &str| object.get(field).and_then(Value::as_bool);
    GateOverridesV1 {
        action_authorized: flag("action_authorized"),
        source_authentic: flag("source_authentic"),
        calculation_valid: flag("calculation_valid"),
        transition_valid: flag("transition_valid"),
        solvency_supported: flag("solvency_supported"),
        destination_allowed: flag("destination_allowed"),
        anomaly_clear: flag("anomaly_clear"),
        evidence_independent: flag("evidence_independent"),
        financial_basis_valid: flag("financial_basis_valid"),
        reuse_finality: flag("reuse_finality"),
        obligation_valid: flag("obligation_valid"),
        linked_plan_valid: flag("linked_plan_valid"),
    }
}

fn parse_request(
    value: &Value,
    evidence_snapshot: EvidenceSnapshotV1,
    valuation_profile: ConservativeValuationProfileV1,
    settlement_policy: SettlementPolicyV1,
) -> Result<ExternalizationRequestV1, SettlementParseErrorV1> {
    let object = value.as_object().ok_or(missing_field("request"))?;
    let financial_basis = object
        .get("financial_basis")
        .ok_or(missing_field("financial_basis"))?;
    let basis_object = financial_basis
        .as_object()
        .ok_or(missing_field("financial_basis"))?;
    let linked_plan = object
        .get("linked_plan")
        .map(parse_linked_plan)
        .transpose()?;
    if linked_plan
        .as_ref()
        .is_some_and(|plan| plan.legs.len() > super::bounds::MAX_LINKED_PLAN_LEGS_V1)
    {
        return Err(SettlementParseErrorV1::CollectionLimit {
            field: "linked_plan.legs",
        });
    }
    let obligation = object.get("obligation").map(parse_obligation).transpose()?;
    Ok(ExternalizationRequestV1 {
        request_id: required_string(object, "request_id")?,
        declared_release_class: parse_release_class(
            required_string(object, "declared_release_class")?.as_str(),
        )?,
        subject: required_string(object, "subject")?,
        source_account: required_string(object, "source_account")?,
        destination: required_string(object, "destination")?,
        route: required_string(object, "route")?,
        asset: required_string(object, "asset")?,
        direction: parse_direction(required_string(object, "direction")?.as_str())?,
        total_amount: parse_rational(
            object
                .get("total_amount")
                .ok_or(missing_field("total_amount"))?,
        )?,
        financial_basis: FinancialBasisV1 {
            kind: match basis_object.get("kind").and_then(Value::as_str) {
                Some("contract_derived") => FinancialBasisKindV1::ContractDerived,
                _ => FinancialBasisKindV1::SyntheticAccount,
            },
            state_key_digest: basis_object
                .get("state_key")
                .map(parse_digest)
                .transpose()?,
            terms_digest: basis_object
                .get("terms_digest")
                .map(parse_digest)
                .transpose()?,
            composition_digest: basis_object
                .get("composition_digest")
                .map(parse_digest)
                .transpose()?,
            analysis_subject_digest: basis_object
                .get("analysis_subject_digest")
                .map(parse_digest)
                .transpose()?,
        },
        originating_transition: required_string(object, "originating_transition")?,
        nonce: required_string(object, "nonce")?,
        requested_at: object
            .get("requested_at")
            .and_then(Value::as_i64)
            .ok_or(missing_field("requested_at"))?,
        expires_at: object
            .get("expires_at")
            .and_then(Value::as_i64)
            .ok_or(missing_field("expires_at"))?,
        action_authorization_digest: parse_digest(
            object
                .get("action_authorization_digest")
                .ok_or(missing_field("action_authorization_digest"))?,
        )?,
        linked_plan,
        obligation,
        reuse_finality_passed: object
            .get("reuse_finality_passed")
            .and_then(Value::as_bool)
            .unwrap_or(true),
        gate_overrides: parse_gate_overrides(object.get("gate_overrides")),
        evidence_snapshot,
        valuation_profile,
        settlement_policy,
    })
}

fn parse_linked_plan(value: &Value) -> Result<AtomicLinkedExchangePlanV1, SettlementParseErrorV1> {
    let object = value.as_object().ok_or(missing_field("linked_plan"))?;
    let legs = object
        .get("legs")
        .and_then(Value::as_array)
        .ok_or(missing_field("legs"))?;
    Ok(AtomicLinkedExchangePlanV1 {
        plan_id: required_string(object, "plan_id")?,
        leg_set_digest: parse_digest(
            object
                .get("leg_set_digest")
                .ok_or(missing_field("leg_set_digest"))?,
        )?,
        primary_outbound_leg_id: required_string(object, "primary_outbound_leg_id")?,
        legs: legs
            .iter()
            .map(|leg| {
                let item = leg.as_object().ok_or(missing_field("leg"))?;
                Ok(LinkedPlanLegV1 {
                    leg_id: required_string(item, "leg_id")?,
                    direction: parse_direction(required_string(item, "direction")?.as_str())?,
                    asset: required_string(item, "asset")?,
                    amount: parse_rational(item.get("amount").ok_or(missing_field("amount"))?)?,
                    budget_axis_id: required_string(item, "budget_axis_id")
                        .unwrap_or_else(|_| "default".to_owned()),
                    assurance_tier: super::types::AssuranceTierV1::CurrentlyAssured,
                })
            })
            .collect::<Result<_, _>>()?,
    })
}

fn parse_obligation(
    value: &Value,
) -> Result<ExternalRiskReducingObligationV1, SettlementParseErrorV1> {
    let object = value.as_object().ok_or(missing_field("obligation"))?;
    Ok(ExternalRiskReducingObligationV1 {
        obligation_id: required_string(object, "obligation_id")?,
        beneficiary: required_string(object, "beneficiary")?,
        obligation_account: required_string(object, "obligation_account")?,
        asset: required_string(object, "asset")?,
        exact_amount: parse_rational(
            object
                .get("exact_amount")
                .ok_or(missing_field("exact_amount"))?,
        )?,
        deadline: object
            .get("deadline")
            .and_then(Value::as_i64)
            .ok_or(missing_field("deadline"))?,
        valid_until: object
            .get("valid_until")
            .and_then(Value::as_i64)
            .ok_or(missing_field("valid_until"))?,
        destination_use_restricted: object
            .get("destination_use_restricted")
            .and_then(Value::as_bool)
            .unwrap_or(true),
        exposure_before_digest: parse_digest(
            object
                .get("exposure_before_digest")
                .ok_or(missing_field("exposure_before_digest"))?,
        )?,
        exposure_after_digest: parse_digest(
            object
                .get("exposure_after_digest")
                .ok_or(missing_field("exposure_after_digest"))?,
        )?,
        risk_reduction_ref: parse_digest(
            object
                .get("risk_reduction_ref")
                .ok_or(missing_field("risk_reduction_ref"))?,
        )?,
    })
}
