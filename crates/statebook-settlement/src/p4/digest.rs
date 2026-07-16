#![allow(dead_code)]

use crate::DigestV1;
use crate::{
    AssurancePropertyV1, AssuranceRootV1, AssuranceVerdictV1, DependencyDisclosureV1, RootClassV1,
};
use statebook_core::SignedRational;

use super::canonical::{
    digest, encode_bool, encode_i64, encode_rational, encode_sequence, encode_string_set,
    encode_u32, encode_u8, Canonical, DECISION_CONTEXT_DOMAIN, DECISION_RECORD_DOMAIN,
    EVIDENCE_SNAPSHOT_DOMAIN, INTENT_DOMAIN, LEDGER_TIP_DOMAIN, POLICY_DOMAIN,
    RELEASE_ATTEMPT_DOMAIN, SETTLEMENT_STATE_DOMAIN, VALUATION_PROFILE_DOMAIN,
};
use super::types::{
    AtomicLinkedExchangePlanV1, BreakerScopeV1, BudgetAxisV1, BudgetLedgerStateV1,
    ConservativeValuationProfileV1, DecisionOutcomeV1, DecisionReasonV1, DecisionRecordV1,
    DirectionV1, EvidenceObservationV1, EvidenceSnapshotV1, ExternalRiskReducingObligationV1,
    ExternalizationRequestV1, FinancialBasisKindV1, LinkedPlanLegV1, ReleaseClassV1,
    SettlementPolicyV1, SettlementStateV1,
};

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

fn dependency_disclosure_tag(value: DependencyDisclosureV1) -> u8 {
    match value {
        DependencyDisclosureV1::Complete => 1,
        DependencyDisclosureV1::Unknown => 2,
    }
}

fn release_class_tag(value: ReleaseClassV1) -> u8 {
    match value {
        ReleaseClassV1::InternalRiskState => 1,
        ReleaseClassV1::AtomicLinkedExchange => 2,
        ReleaseClassV1::ExternalRiskReducingObligation => 3,
        ReleaseClassV1::ExternalUnconditional => 4,
        ReleaseClassV1::SystemicOrExceptional => 5,
    }
}

fn direction_tag(value: DirectionV1) -> u8 {
    match value {
        DirectionV1::Outbound => 1,
        DirectionV1::Inbound => 2,
    }
}

fn financial_basis_kind_tag(value: FinancialBasisKindV1) -> u8 {
    match value {
        FinancialBasisKindV1::ContractDerived => 1,
        FinancialBasisKindV1::SyntheticAccount => 2,
    }
}

fn encode_root(root: &AssuranceRootV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, root.root_id().as_bytes());
    encoder.field(2, &[root_class_tag(root.root_class())]);
    encoder.finish()
}

fn encode_evidence_observation(observation: &EvidenceObservationV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &[assurance_property_tag(observation.property)]);
    encoder.field(2, &[assurance_verdict_tag(observation.verdict)]);
    encoder.field(
        3,
        &encode_sequence(observation.current_roots.iter().map(encode_root)),
    );
    encoder.field(
        4,
        &encode_sequence(observation.dependency_roots.iter().map(encode_root)),
    );
    encoder.field(
        5,
        &[dependency_disclosure_tag(observation.dependency_disclosure)],
    );
    encoder.field(6, &encode_i64(observation.observed_at));
    encoder.field(7, &encode_i64(observation.expires_at));
    encoder.field(8, observation.bound_request_id.as_bytes());
    encoder.field(9, &encode_bool(observation.replayed));
    encoder.field(10, &encode_bool(observation.equivocated));
    encoder.finish()
}

pub fn evidence_snapshot_digest(snapshot: &EvidenceSnapshotV1) -> DigestV1 {
    let mut encoder = Canonical::new();
    encoder.field(1, snapshot.snapshot_id.as_bytes());
    encoder.field(2, snapshot.request_id.as_bytes());
    encoder.field(3, snapshot.nonce.as_bytes());
    encoder.field(
        4,
        &encode_sequence(
            snapshot
                .observations
                .iter()
                .map(encode_evidence_observation),
        ),
    );
    digest(EVIDENCE_SNAPSHOT_DOMAIN, &encoder.finish())
}

pub fn valuation_profile_digest(profile: &ConservativeValuationProfileV1) -> DigestV1 {
    let mut encoder = Canonical::new();
    encoder.field(1, profile.profile_id.as_bytes());
    encoder.field(2, profile.numeraire_asset.as_bytes());
    encoder.field(3, &encode_i64(profile.max_age_seconds));
    encoder.field(4, &encode_rational(profile.stress_multiplier));
    encoder.field(
        5,
        &encode_sequence(profile.observations.iter().map(|observation| {
            let mut item = Canonical::new();
            item.field(1, observation.asset.as_bytes());
            item.field(
                2,
                &encode_rational(
                    observation
                        .rate
                        .to_signed_rational()
                        .unwrap_or(SignedRational::new(0, 1).unwrap()),
                ),
            );
            item.field(3, &encode_i64(observation.observed_at));
            item.field(4, observation.root_id.as_bytes());
            item.field(5, &[root_class_tag(observation.root_class)]);
            item.finish()
        })),
    );
    encoder.field(6, &encode_string_set(&profile.independence_roots));
    digest(VALUATION_PROFILE_DOMAIN, &encoder.finish())
}

fn encode_tier_fraction(instant_fraction: SignedRational, delay_seconds: i64) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, &encode_rational(instant_fraction));
    encoder.field(2, &encode_i64(delay_seconds));
    encoder.finish()
}

pub fn policy_digest(policy: &SettlementPolicyV1) -> DigestV1 {
    let mut encoder = Canonical::new();
    encoder.field(1, policy.policy_id.as_bytes());
    encoder.field(2, &encode_u32(policy.policy_version));
    let tiers = &policy.assurance_tiers;
    encoder.field(
        3,
        &encode_tier_fraction(
            tiers.quarantined.instant_fraction,
            tiers.quarantined.delay_seconds,
        ),
    );
    encoder.field(
        4,
        &encode_tier_fraction(
            tiers.unproven_or_novel.instant_fraction,
            tiers.unproven_or_novel.delay_seconds,
        ),
    );
    encoder.field(
        5,
        &encode_tier_fraction(
            tiers.currently_assured.instant_fraction,
            tiers.currently_assured.delay_seconds,
        ),
    );
    encoder.field(
        6,
        &encode_tier_fraction(
            tiers.strong_current_assurance_low_impact.instant_fraction,
            tiers.strong_current_assurance_low_impact.delay_seconds,
        ),
    );
    let hysteresis = &policy.hysteresis;
    encoder.field(7, &encode_i64(hysteresis.min_relax_dwell_seconds));
    encoder.field(8, &encode_u32(hysteresis.required_clean_epochs));
    encoder.field(9, hysteresis.successor_policy_digest.as_bytes());
    digest(POLICY_DOMAIN, &encoder.finish())
}

fn encode_axis(axis: &BudgetAxisV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, axis.axis_id.as_bytes());
    encoder.field(2, axis.asset.as_bytes());
    encoder.field(3, &encode_rational(axis.cap));
    encoder.field(4, &encode_rational(axis.reserved));
    encoder.field(5, &encode_rational(axis.in_flight));
    encoder.field(6, &encode_rational(axis.consumed));
    encoder.finish()
}

pub fn ledger_tip_digest(ledger: &BudgetLedgerStateV1) -> DigestV1 {
    let mut encoder = Canonical::new();
    encoder.field(1, &encode_u32(ledger.epoch));
    encoder.field(2, &encode_sequence(ledger.axes.iter().map(encode_axis)));
    encoder.field(
        3,
        &encode_sequence(ledger.journal.iter().map(|entry| entry.as_bytes().to_vec())),
    );
    digest(LEDGER_TIP_DOMAIN, &encoder.finish())
}

fn encode_linked_leg(leg: &LinkedPlanLegV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, leg.leg_id.as_bytes());
    encoder.field(2, &[direction_tag(leg.direction)]);
    encoder.field(3, leg.asset.as_bytes());
    encoder.field(4, &encode_rational(leg.amount));
    encoder.field(5, leg.budget_axis_id.as_bytes());
    encoder.field(
        6,
        &encode_u8(match leg.assurance_tier {
            super::types::AssuranceTierV1::Quarantined => 1,
            super::types::AssuranceTierV1::UnprovenOrNovel => 2,
            super::types::AssuranceTierV1::CurrentlyAssured => 3,
            super::types::AssuranceTierV1::StrongCurrentAssuranceLowImpact => 4,
        }),
    );
    encoder.finish()
}

pub fn linked_plan_digest(plan: &AtomicLinkedExchangePlanV1) -> DigestV1 {
    let mut encoder = Canonical::new();
    encoder.field(1, plan.plan_id.as_bytes());
    encoder.field(2, plan.leg_set_digest.as_bytes());
    encoder.field(3, plan.primary_outbound_leg_id.as_bytes());
    encoder.field(4, &encode_sequence(plan.legs.iter().map(encode_linked_leg)));
    digest(INTENT_DOMAIN, &encoder.finish())
}

pub fn obligation_digest(obligation: &ExternalRiskReducingObligationV1) -> DigestV1 {
    let mut encoder = Canonical::new();
    encoder.field(1, obligation.obligation_id.as_bytes());
    encoder.field(2, obligation.beneficiary.as_bytes());
    encoder.field(3, obligation.obligation_account.as_bytes());
    encoder.field(4, obligation.asset.as_bytes());
    encoder.field(5, &encode_rational(obligation.exact_amount));
    encoder.field(6, &encode_i64(obligation.deadline));
    encoder.field(7, &encode_i64(obligation.valid_until));
    encoder.field(8, &encode_bool(obligation.destination_use_restricted));
    encoder.field(9, obligation.exposure_before_digest.as_bytes());
    encoder.field(10, obligation.exposure_after_digest.as_bytes());
    encoder.field(11, obligation.risk_reduction_ref.as_bytes());
    digest(INTENT_DOMAIN, &encoder.finish())
}

pub fn intent_payload(request: &ExternalizationRequestV1) -> Vec<u8> {
    let basis = &request.financial_basis;
    let mut encoder = Canonical::new();
    encoder.field(1, &encode_u32(1));
    encoder.field(2, request.subject.as_bytes());
    encoder.field(3, request.source_account.as_bytes());
    encoder.field(4, request.destination.as_bytes());
    encoder.field(5, request.route.as_bytes());
    encoder.field(6, request.asset.as_bytes());
    encoder.field(7, &[direction_tag(request.direction)]);
    encoder.field(8, &encode_rational(request.total_amount));
    encoder.field(9, &[financial_basis_kind_tag(basis.kind)]);
    if let Some(value) = basis.state_key_digest {
        encoder.field(10, value.as_bytes());
    }
    if let Some(value) = basis.terms_digest {
        encoder.field(11, value.as_bytes());
    }
    if let Some(value) = basis.composition_digest {
        encoder.field(12, value.as_bytes());
    }
    encoder.field(13, request.originating_transition.as_bytes());
    if let Some(plan) = &request.linked_plan {
        encoder.field(14, linked_plan_digest(plan).as_bytes());
    } else if let Some(obligation) = &request.obligation {
        encoder.field(14, obligation_digest(obligation).as_bytes());
    } else {
        encoder.field(14, &[]);
    }
    encoder.field(15, request.action_authorization_digest.as_bytes());
    encoder.field(16, &[release_class_tag(request.declared_release_class)]);
    encoder.field(17, request.nonce.as_bytes());
    encoder.field(18, &encode_i64(request.requested_at));
    encoder.field(19, &encode_i64(request.expires_at));
    encoder.finish()
}

pub fn intent_digest(request: &ExternalizationRequestV1) -> DigestV1 {
    digest(INTENT_DOMAIN, &intent_payload(request))
}

pub fn decision_context_digest(
    intent: DigestV1,
    evidence: DigestV1,
    valuation: DigestV1,
    policy: DigestV1,
    evaluated_at: i64,
) -> DigestV1 {
    let mut encoder = Canonical::new();
    encoder.field(1, intent.as_bytes());
    encoder.field(2, evidence.as_bytes());
    encoder.field(3, valuation.as_bytes());
    encoder.field(4, policy.as_bytes());
    encoder.field(5, &encode_i64(evaluated_at));
    digest(DECISION_CONTEXT_DOMAIN, &encoder.finish())
}

pub fn release_attempt_digest(
    release_part_id: &str,
    decision_context: DigestV1,
    reservation_id: &str,
) -> DigestV1 {
    let mut encoder = Canonical::new();
    encoder.field(1, release_part_id.as_bytes());
    encoder.field(2, decision_context.as_bytes());
    encoder.field(3, reservation_id.as_bytes());
    digest(RELEASE_ATTEMPT_DOMAIN, &encoder.finish())
}

fn encode_breaker(scope: &BreakerScopeV1) -> Vec<u8> {
    let mut encoder = Canonical::new();
    encoder.field(1, scope.scope_id.as_bytes());
    encoder.field(
        2,
        &encode_u8(match scope.state {
            super::types::BreakerStateV1::Normal => 1,
            super::types::BreakerStateV1::Guarded => 2,
            super::types::BreakerStateV1::Challenged => 3,
            super::types::BreakerStateV1::Halted => 4,
            super::types::BreakerStateV1::Resolution => 5,
            super::types::BreakerStateV1::Recovery => 6,
        }),
    );
    encoder.field(
        3,
        &match scope.expires_at {
            None => vec![0],
            Some(value) => {
                let mut out = vec![1];
                out.extend_from_slice(&encode_i64(value));
                out
            }
        },
    );
    encoder.field(4, &encode_u32(scope.renewal_count));
    encoder.field(5, &encode_u32(scope.renewal_ceiling));
    encoder.finish()
}

pub fn settlement_state_digest(state: &SettlementStateV1) -> DigestV1 {
    let mut encoder = Canonical::new();
    encoder.field(1, ledger_tip_digest(&state.ledger).as_bytes());
    encoder.field(
        2,
        &encode_u8(match state.queue.status {
            super::types::QueueStatusV1::None => 1,
            super::types::QueueStatusV1::Queued => 2,
            super::types::QueueStatusV1::Challenged => 3,
            super::types::QueueStatusV1::EvidenceExpired => 4,
            super::types::QueueStatusV1::Frozen => 5,
            super::types::QueueStatusV1::Cancelled => 6,
            super::types::QueueStatusV1::RevalidationRequired => 7,
        }),
    );
    encoder.field(
        3,
        &encode_u8(match state.transfer.status {
            super::types::TransferStatusV1::Unreserved => 1,
            super::types::TransferStatusV1::Reserved => 2,
            super::types::TransferStatusV1::Submitted => 3,
            super::types::TransferStatusV1::SourceObserved => 4,
            super::types::TransferStatusV1::SourceFinalized => 5,
            super::types::TransferStatusV1::DestinationObserved => 6,
            super::types::TransferStatusV1::DestinationFinalized => 7,
            super::types::TransferStatusV1::Consumed => 8,
            super::types::TransferStatusV1::ProvenNoOutflow => 9,
        }),
    );
    encoder.field(
        4,
        &encode_sequence(state.breakers.iter().map(encode_breaker)),
    );
    encoder.field(5, state.recovery.profile_digest.as_bytes());
    encoder.field(6, &encode_string_set(&state.applied_challenge_ids));
    encoder.field(7, state.active_policy.policy_digest.as_bytes());
    encoder.field(8, &encode_u32(state.active_policy.policy_version));
    encoder.field(9, &encode_i64(state.last_policy_change_at));
    encoder.field(10, &encode_u32(state.clean_epochs));
    encoder.field(
        11,
        &match state.bound_intent_digest {
            Some(digest) => digest.as_bytes().to_vec(),
            None => Vec::new(),
        },
    );
    encoder.field(
        12,
        state.bound_destination.as_deref().unwrap_or("").as_bytes(),
    );
    digest(SETTLEMENT_STATE_DOMAIN, &encoder.finish())
}

fn decision_outcome_tag(value: DecisionOutcomeV1) -> u8 {
    match value {
        DecisionOutcomeV1::Rejected => 1,
        DecisionOutcomeV1::Quarantined => 2,
        DecisionOutcomeV1::Immediate => 3,
        DecisionOutcomeV1::Queued => 4,
        DecisionOutcomeV1::Frozen => 5,
    }
}

fn decision_reason_tag(value: DecisionReasonV1) -> u8 {
    match value {
        DecisionReasonV1::AmountZero => 1,
        DecisionReasonV1::AmountNegative => 2,
        DecisionReasonV1::AmountOverflow => 3,
        DecisionReasonV1::AmountNoncanonical => 4,
        DecisionReasonV1::AmountWrongSign => 5,
        DecisionReasonV1::ReleaseClassUnknown => 6,
        DecisionReasonV1::GateActionAuthorization => 7,
        DecisionReasonV1::GateSourceAuthenticity => 8,
        DecisionReasonV1::GateCalculationIntegrity => 9,
        DecisionReasonV1::GateStateTransitionIntegrity => 10,
        DecisionReasonV1::GateSolvencySupport => 11,
        DecisionReasonV1::GateDestinationRoute => 12,
        DecisionReasonV1::GateAnomalyEmergency => 13,
        DecisionReasonV1::GateEvidenceIndependence => 14,
        DecisionReasonV1::GateFinancialBasisBinding => 15,
        DecisionReasonV1::GateReuseFinality => 16,
        DecisionReasonV1::GateRiskReducingObligation => 17,
        DecisionReasonV1::GateLinkedExchangePlan => 18,
        DecisionReasonV1::ValuationStale => 19,
        DecisionReasonV1::ValuationMissing => 20,
        DecisionReasonV1::ValuationConflict => 21,
        DecisionReasonV1::BudgetCasConflict => 22,
        DecisionReasonV1::BudgetInsufficient => 23,
        DecisionReasonV1::BreakerHalted => 24,
        DecisionReasonV1::BreakerFrozen => 25,
        DecisionReasonV1::BreakerInvalidTransition => 26,
        DecisionReasonV1::BreakerResolutionRequired => 34,
        DecisionReasonV1::BreakerRenewalRejected => 35,
        DecisionReasonV1::QueueTimerOnly => 27,
        DecisionReasonV1::ChallengeInvalid => 28,
        DecisionReasonV1::ChallengeDuplicate => 29,
        DecisionReasonV1::ChallengeCensored => 36,
        DecisionReasonV1::ChallengeUnavailable => 37,
        DecisionReasonV1::EvidenceExpired => 38,
        DecisionReasonV1::PolicyRollback => 30,
        DecisionReasonV1::PolicyRelaxRejected => 39,
        DecisionReasonV1::QueueCancelled => 40,
        DecisionReasonV1::RecoveryFailed => 31,
        DecisionReasonV1::IntentDigestMismatch => 32,
        DecisionReasonV1::ModelConfidenceIgnored => 33,
    }
}

pub fn decision_record_digest(record: &DecisionRecordV1) -> DigestV1 {
    let mut encoder = Canonical::new();
    encoder.field(1, &encode_u32(u32::from(record.schema_version)));
    encoder.field(2, &[decision_outcome_tag(record.outcome)]);
    encoder.field(3, record.intent_digest.as_bytes());
    encoder.field(4, record.decision_context_digest.as_bytes());
    encoder.field(5, &encode_rational(record.instant_release_amount));
    encoder.field(6, record.ledger_tip_before.as_bytes());
    encoder.field(7, record.ledger_tip_after.as_bytes());
    encoder.field(
        8,
        &encode_sequence(
            record
                .reasons
                .iter()
                .map(|reason| vec![decision_reason_tag(*reason)]),
        ),
    );
    encoder.field(9, &encode_i64(record.evaluated_at));
    digest(DECISION_RECORD_DOMAIN, &encoder.finish())
}
