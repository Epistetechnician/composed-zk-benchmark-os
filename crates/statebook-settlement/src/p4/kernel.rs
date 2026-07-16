use statebook_core::SignedRational;

use super::amounts::validate_amount_before_valuation;
use super::assurance::{evaluate_independence, resolve_assurance_tier};
use super::breaker::{
    apply_ttl_exhaustion_to_state, collect_breaker_block_reasons, global_breaker_state,
};
use super::budget::{gross_reserve_linked_plan, try_reserve, ReservationResult};
use super::challenge::{apply_evidence_expiry_to_state, evidence_is_fresh};
use super::classify::classify_release_class;
use super::digest::{
    decision_context_digest, decision_record_digest, evidence_snapshot_digest, intent_digest,
    ledger_tip_digest, linked_plan_digest, obligation_digest, policy_digest,
    release_attempt_digest, valuation_profile_digest,
};
use super::error::SettlementTransitionErrorV1;
use super::gates::evaluate_hard_gates;
use super::hysteresis::{apply_accepted_policy_to_state, collect_hysteresis_block_reason};
use super::linked_plan::linked_outbound_total;
use super::recovery::recovery_blocks_release;
use super::types::{
    default_nonclaims, zero_rational, AssuranceTierV1, BreakerStateV1, ClockV1, DecisionOutcomeV1,
    DecisionReasonV1, DecisionRecordV1, ExternalizationRequestV1, QueueStatusV1, ReleaseClassV1,
    SettlementStateV1, TransferStatusV1,
};
use super::valuation::evaluate_valuation;

pub fn decide_and_transition(
    request: ExternalizationRequestV1,
    current_state: SettlementStateV1,
    clock: ClockV1,
) -> Result<DecisionRecordV1, SettlementTransitionErrorV1> {
    let evaluated_at = clock.now();
    let release_class = classify_release_class(&request);
    let evidence = request.evidence_snapshot();
    let valuation_profile = request.valuation_profile();
    let policy = request.settlement_policy();

    let intent = intent_digest(&request);
    let evidence_digest = evidence_snapshot_digest(evidence);
    let valuation_digest = valuation_profile_digest(valuation_profile);
    let policy_d = policy_digest(policy);
    let decision_context = decision_context_digest(
        intent,
        evidence_digest,
        valuation_digest,
        policy_d,
        evaluated_at,
    );

    let mut current_state = current_state;
    apply_ttl_exhaustion_to_state(&mut current_state, evaluated_at);

    let mut expiry_values: Vec<i64> = evidence
        .observations()
        .iter()
        .map(|observation| observation.expires_at)
        .collect();
    expiry_values.push(request.expires_at);
    apply_evidence_expiry_to_state(
        &mut current_state,
        expiry_values.iter().copied(),
        evaluated_at,
    );

    let mut revalidating = false;
    if current_state.queue.status == QueueStatusV1::RevalidationRequired {
        if evidence_is_fresh(expiry_values.iter().copied(), evaluated_at) {
            // Fresh evidence binds a new decision context (above) and clears the
            // revalidation block toward Reserved — never timer-alone release.
            current_state.queue.status = QueueStatusV1::None;
            revalidating = true;
        } else {
            let ledger_tip_before = current_state.ledger.tip_digest;
            let queue_status_before = current_state.queue.status;
            let transfer_status_before = current_state.transfer.status;
            return Ok(build_record(
                DecisionOutcomeV1::Rejected,
                None,
                zero_rational(),
                zero_rational(),
                intent,
                decision_context,
                None,
                request.financial_basis.analysis_subject_digest,
                request.financial_basis.composition_digest,
                evidence_digest,
                valuation_digest,
                policy_d,
                linked_or_obligation_digest(&request),
                ledger_tip_before,
                ledger_tip_before,
                queue_status_before,
                QueueStatusV1::RevalidationRequired,
                transfer_status_before,
                transfer_status_before,
                vec![DecisionReasonV1::EvidenceExpired],
                Vec::new(),
                default_nonclaims(),
                evaluated_at,
                release_class,
                current_state,
            ));
        }
    }

    if current_state.queue.status == QueueStatusV1::Cancelled {
        let ledger_tip_before = current_state.ledger.tip_digest;
        let transfer_status_before = current_state.transfer.status;
        return Ok(build_record(
            DecisionOutcomeV1::Rejected,
            None,
            zero_rational(),
            zero_rational(),
            intent,
            decision_context,
            None,
            request.financial_basis.analysis_subject_digest,
            request.financial_basis.composition_digest,
            evidence_digest,
            valuation_digest,
            policy_d,
            linked_or_obligation_digest(&request),
            ledger_tip_before,
            ledger_tip_before,
            QueueStatusV1::Cancelled,
            QueueStatusV1::Cancelled,
            transfer_status_before,
            transfer_status_before,
            vec![DecisionReasonV1::QueueCancelled],
            Vec::new(),
            default_nonclaims(),
            evaluated_at,
            release_class,
            current_state,
        ));
    }

    if let (Some(bound_intent), Some(bound_destination)) = (
        current_state.bound_intent_digest,
        current_state.bound_destination.as_deref(),
    ) {
        if intent == bound_intent && request.destination() != bound_destination {
            let ledger_tip_before = current_state.ledger.tip_digest;
            let queue_status_before = current_state.queue.status;
            let transfer_status_before = current_state.transfer.status;
            return Ok(build_record(
                DecisionOutcomeV1::Rejected,
                None,
                zero_rational(),
                zero_rational(),
                intent,
                decision_context,
                None,
                request.financial_basis.analysis_subject_digest,
                request.financial_basis.composition_digest,
                evidence_digest,
                valuation_digest,
                policy_d,
                linked_or_obligation_digest(&request),
                ledger_tip_before,
                ledger_tip_before,
                queue_status_before,
                queue_status_before,
                transfer_status_before,
                transfer_status_before,
                vec![DecisionReasonV1::IntentDigestMismatch],
                Vec::new(),
                default_nonclaims(),
                evaluated_at,
                release_class,
                current_state,
            ));
        }
    }

    let ledger_tip_before = current_state.ledger.tip_digest;
    let queue_status_before = current_state.queue.status;
    let transfer_status_before = current_state.transfer.status;

    let mut reasons = Vec::new();
    let missing_facts = Vec::new();
    let nonclaims = default_nonclaims();

    reasons.extend(collect_breaker_block_reasons(&current_state, evaluated_at));
    if let Some(reason) = collect_hysteresis_block_reason(&current_state, policy, evaluated_at) {
        reasons.push(reason);
    }
    if recovery_blocks_release(&current_state) {
        reasons.push(DecisionReasonV1::RecoveryFailed);
    }

    if reasons.iter().any(|reason| {
        matches!(
            reason,
            DecisionReasonV1::PolicyRollback | DecisionReasonV1::PolicyRelaxRejected
        )
    }) {
        return Ok(build_record(
            DecisionOutcomeV1::Rejected,
            None,
            zero_rational(),
            zero_rational(),
            intent,
            decision_context,
            None,
            request.financial_basis.analysis_subject_digest,
            request.financial_basis.composition_digest,
            evidence_digest,
            valuation_digest,
            policy_d,
            linked_or_obligation_digest(&request),
            ledger_tip_before,
            ledger_tip_before,
            queue_status_before,
            queue_status_before,
            transfer_status_before,
            transfer_status_before,
            reasons,
            missing_facts,
            nonclaims,
            evaluated_at,
            release_class,
            current_state,
        ));
    }

    let amount = match validate_amount_before_valuation(&request) {
        Ok(value) => value,
        Err(failure) => {
            if let Some(reason) = failure.reason {
                reasons.push(reason);
            }
            return Ok(build_record(
                DecisionOutcomeV1::Rejected,
                None,
                zero_rational(),
                zero_rational(),
                intent,
                decision_context,
                None,
                request.financial_basis.analysis_subject_digest,
                request.financial_basis.composition_digest,
                evidence_digest,
                valuation_digest,
                policy_d,
                linked_or_obligation_digest(&request),
                ledger_tip_before,
                ledger_tip_before,
                queue_status_before,
                queue_status_before,
                transfer_status_before,
                transfer_status_before,
                reasons,
                missing_facts,
                nonclaims,
                evaluated_at,
                release_class,
                current_state,
            ));
        }
    };

    if release_class == ReleaseClassV1::SystemicOrExceptional {
        reasons.push(DecisionReasonV1::ReleaseClassUnknown);
    }

    let gate_results = evaluate_hard_gates(
        &request,
        evidence,
        &current_state,
        release_class,
        request.gate_overrides(),
    );
    let mut quarantined = false;
    for result in gate_results {
        if !result.passed {
            if let Some(reason) = result.reason {
                reasons.push(reason);
            }
            if result.quarantine {
                quarantined = true;
            }
        }
    }

    let valuation = evaluate_valuation(valuation_profile, request.asset(), evaluated_at);
    if !valuation.ok {
        if let Some(reason) = valuation.reason {
            reasons.push(reason);
        }
    }

    if !reasons.is_empty() {
        let outcome = if quarantined {
            DecisionOutcomeV1::Quarantined
        } else {
            DecisionOutcomeV1::Rejected
        };
        return Ok(build_record(
            outcome,
            None,
            zero_rational(),
            zero_rational(),
            intent,
            decision_context,
            None,
            request.financial_basis.analysis_subject_digest,
            request.financial_basis.composition_digest,
            evidence_digest,
            valuation_digest,
            policy_d,
            linked_or_obligation_digest(&request),
            ledger_tip_before,
            ledger_tip_before,
            queue_status_before,
            queue_status_before,
            transfer_status_before,
            transfer_status_before,
            reasons,
            missing_facts,
            nonclaims,
            evaluated_at,
            release_class,
            current_state,
        ));
    }

    let independence_ok = evaluate_independence(evidence).unwrap_or(false);
    let tier = resolve_assurance_tier(evidence, independence_ok);
    if tier == AssuranceTierV1::Quarantined {
        return Ok(build_record(
            DecisionOutcomeV1::Quarantined,
            Some(tier),
            zero_rational(),
            zero_rational(),
            intent,
            decision_context,
            None,
            request.financial_basis.analysis_subject_digest,
            request.financial_basis.composition_digest,
            evidence_digest,
            valuation_digest,
            policy_d,
            linked_or_obligation_digest(&request),
            ledger_tip_before,
            ledger_tip_before,
            queue_status_before,
            queue_status_before,
            transfer_status_before,
            transfer_status_before,
            vec![DecisionReasonV1::GateEvidenceIndependence],
            missing_facts,
            nonclaims,
            evaluated_at,
            release_class,
            current_state,
        ));
    }

    let tier_fraction = tier_fraction_for(policy, tier);
    let instant = amount
        .checked_mul(tier_fraction.instant_fraction)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    let queued = amount
        .checked_sub(instant)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;

    if current_state.queue.status == QueueStatusV1::Queued
        && queued.numerator() > 0
        && instant.is_zero()
    {
        return Ok(build_record(
            DecisionOutcomeV1::Rejected,
            Some(tier),
            zero_rational(),
            zero_rational(),
            intent,
            decision_context,
            None,
            request.financial_basis.analysis_subject_digest,
            request.financial_basis.composition_digest,
            evidence_digest,
            valuation_digest,
            policy_d,
            linked_or_obligation_digest(&request),
            ledger_tip_before,
            ledger_tip_before,
            queue_status_before,
            queue_status_before,
            transfer_status_before,
            transfer_status_before,
            vec![DecisionReasonV1::QueueTimerOnly],
            missing_facts,
            nonclaims,
            evaluated_at,
            release_class,
            current_state,
        ));
    }

    let reserve_amount = if release_class == ReleaseClassV1::AtomicLinkedExchange {
        linked_outbound_total(&request)
    } else {
        instant
    };

    let reservation = if release_class == ReleaseClassV1::AtomicLinkedExchange {
        gross_reserve_linked_plan(
            &current_state.ledger,
            current_state.expected_ledger_tip,
            reserve_amount,
            request.asset(),
        )
        .map(|ledger| ReservationResult { ledger })
    } else {
        try_reserve(
            &current_state.ledger,
            current_state.expected_ledger_tip,
            &request,
            reserve_amount,
        )
    };

    let (mut next_state, ledger_tip_after) = match reservation {
        Ok(result) => {
            let ledger = result.ledger;
            let tip = ledger.tip_digest;
            let mut state = current_state.clone();
            state.ledger = ledger;
            state.expected_ledger_tip = tip;
            (state, tip)
        }
        Err(SettlementTransitionErrorV1::LedgerCasConflict) => {
            reasons.push(DecisionReasonV1::BudgetCasConflict);
            return Ok(build_record(
                DecisionOutcomeV1::Rejected,
                Some(tier),
                zero_rational(),
                zero_rational(),
                intent,
                decision_context,
                None,
                request.financial_basis.analysis_subject_digest,
                request.financial_basis.composition_digest,
                evidence_digest,
                valuation_digest,
                policy_d,
                linked_or_obligation_digest(&request),
                ledger_tip_before,
                ledger_tip_before,
                queue_status_before,
                queue_status_before,
                transfer_status_before,
                transfer_status_before,
                reasons,
                missing_facts,
                nonclaims,
                evaluated_at,
                release_class,
                current_state,
            ));
        }
        Err(error) => return Err(error),
    };

    let release_attempt =
        release_attempt_digest("instant-part-1", decision_context, "reservation-1");

    let (outcome, instant_release, queued_release, queue_after, transfer_after) =
        if global_breaker_state(next_state.breakers()) == BreakerStateV1::Challenged
            || queue_status_before == QueueStatusV1::Challenged
            || next_state.queue.status == QueueStatusV1::Challenged
        {
            next_state.queue.status = QueueStatusV1::Frozen;
            next_state.transfer.status = TransferStatusV1::Unreserved;
            (
                DecisionOutcomeV1::Frozen,
                zero_rational(),
                zero_rational(),
                QueueStatusV1::Frozen,
                TransferStatusV1::Unreserved,
            )
        } else if revalidating && instant.numerator() > 0 {
            next_state.queue.status = QueueStatusV1::None;
            next_state.transfer.status = TransferStatusV1::Reserved;
            (
                DecisionOutcomeV1::Immediate,
                instant,
                zero_rational(),
                QueueStatusV1::None,
                TransferStatusV1::Reserved,
            )
        } else if release_class == ReleaseClassV1::ExternalUnconditional
            && queued.numerator() > 0
            && tier_fraction.delay_seconds > 0
        {
            next_state.queue.status = QueueStatusV1::Queued;
            next_state.transfer.status = TransferStatusV1::Unreserved;
            next_state.bound_intent_digest = Some(intent);
            next_state.bound_destination = Some(request.destination().to_owned());
            (
                DecisionOutcomeV1::Queued,
                instant,
                queued,
                QueueStatusV1::Queued,
                TransferStatusV1::Unreserved,
            )
        } else if instant.numerator() > 0 {
            next_state.transfer.status = TransferStatusV1::Reserved;
            (
                DecisionOutcomeV1::Immediate,
                instant,
                zero_rational(),
                QueueStatusV1::None,
                TransferStatusV1::Reserved,
            )
        } else {
            (
                DecisionOutcomeV1::Rejected,
                zero_rational(),
                zero_rational(),
                queue_status_before,
                transfer_status_before,
            )
        };

    if ledger_tip_after != ledger_tip_digest(&next_state.ledger) {
        next_state.ledger.tip_digest = ledger_tip_digest(&next_state.ledger);
    }

    if matches!(
        outcome,
        DecisionOutcomeV1::Immediate | DecisionOutcomeV1::Queued | DecisionOutcomeV1::Frozen
    ) {
        apply_accepted_policy_to_state(&mut next_state, policy, evaluated_at);
    }

    Ok(build_record(
        outcome,
        Some(tier),
        instant_release,
        queued_release,
        intent,
        decision_context,
        Some(release_attempt),
        request.financial_basis.analysis_subject_digest,
        request.financial_basis.composition_digest,
        evidence_digest,
        valuation_digest,
        policy_d,
        linked_or_obligation_digest(&request),
        ledger_tip_before,
        next_state.ledger.tip_digest,
        queue_status_before,
        queue_after,
        transfer_status_before,
        transfer_after,
        reasons,
        missing_facts,
        nonclaims,
        evaluated_at,
        release_class,
        next_state,
    ))
}

fn tier_fraction_for(
    policy: &super::types::SettlementPolicyV1,
    tier: AssuranceTierV1,
) -> super::types::TierFractionV1 {
    match tier {
        AssuranceTierV1::Quarantined => policy.assurance_tiers.quarantined.clone(),
        AssuranceTierV1::UnprovenOrNovel => policy.assurance_tiers.unproven_or_novel.clone(),
        AssuranceTierV1::CurrentlyAssured => policy.assurance_tiers.currently_assured.clone(),
        AssuranceTierV1::StrongCurrentAssuranceLowImpact => policy
            .assurance_tiers
            .strong_current_assurance_low_impact
            .clone(),
    }
}

fn linked_or_obligation_digest(request: &ExternalizationRequestV1) -> Option<crate::DigestV1> {
    request
        .linked_plan()
        .map(linked_plan_digest)
        .or_else(|| request.obligation().map(obligation_digest))
}

#[allow(clippy::too_many_arguments)]
fn build_record(
    outcome: DecisionOutcomeV1,
    assurance_tier: Option<AssuranceTierV1>,
    instant_release_amount: SignedRational,
    queued_release_amount: SignedRational,
    intent_digest: crate::DigestV1,
    decision_context_digest: crate::DigestV1,
    release_attempt_digest: Option<crate::DigestV1>,
    analysis_subject_digest: Option<crate::DigestV1>,
    composition_digest: Option<crate::DigestV1>,
    evidence_snapshot_digest: crate::DigestV1,
    valuation_profile_digest: crate::DigestV1,
    policy_digest: crate::DigestV1,
    linked_plan_or_obligation_digest: Option<crate::DigestV1>,
    ledger_tip_before: crate::DigestV1,
    ledger_tip_after: crate::DigestV1,
    queue_status_before: QueueStatusV1,
    queue_status_after: QueueStatusV1,
    transfer_status_before: TransferStatusV1,
    transfer_status_after: TransferStatusV1,
    reasons: Vec<DecisionReasonV1>,
    missing_facts: Vec<super::types::DecisionMissingFactV1>,
    nonclaims: Vec<super::types::DecisionNonclaimV1>,
    evaluated_at: i64,
    release_class: ReleaseClassV1,
    next_state: SettlementStateV1,
) -> DecisionRecordV1 {
    let mut record = DecisionRecordV1 {
        schema_version: 1,
        outcome,
        release_class,
        assurance_tier,
        instant_release_amount,
        queued_release_amount,
        intent_digest,
        decision_context_digest,
        release_attempt_digest,
        analysis_subject_digest,
        composition_digest,
        evidence_snapshot_digest,
        valuation_profile_digest,
        policy_digest,
        linked_plan_or_obligation_digest,
        ledger_tip_before,
        ledger_tip_after,
        queue_status_before,
        queue_status_after,
        transfer_status_before,
        transfer_status_after,
        reasons,
        missing_facts,
        nonclaims,
        evaluated_at,
        record_digest: crate::DigestV1::from_raw_bytes([0; 32]),
        next_state,
    };
    record.record_digest = decision_record_digest(&record);
    record
}
