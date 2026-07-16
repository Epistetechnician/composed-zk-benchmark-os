use super::gates::GateResult;
use super::types::{DecisionReasonV1, DirectionV1, ExternalizationRequestV1};

pub fn validate_linked_plan(request: &ExternalizationRequestV1) -> GateResult {
    let Some(plan) = request.linked_plan() else {
        return GateResult {
            passed: false,
            reason: Some(DecisionReasonV1::GateLinkedExchangePlan),
            quarantine: false,
        };
    };
    if plan.legs.len() < 2 {
        return GateResult {
            passed: false,
            reason: Some(DecisionReasonV1::GateLinkedExchangePlan),
            quarantine: false,
        };
    }
    let mut has_outbound = false;
    let mut has_inbound = false;
    let mut leg_ids = std::collections::BTreeSet::new();
    for leg in &plan.legs {
        if !leg_ids.insert(leg.leg_id.clone()) {
            return GateResult {
                passed: false,
                reason: Some(DecisionReasonV1::GateLinkedExchangePlan),
                quarantine: false,
            };
        }
        match leg.direction {
            DirectionV1::Outbound => has_outbound = true,
            DirectionV1::Inbound => has_inbound = true,
        }
    }
    if !has_outbound || !has_inbound {
        return GateResult {
            passed: false,
            reason: Some(DecisionReasonV1::GateLinkedExchangePlan),
            quarantine: false,
        };
    }
    if !plan
        .legs
        .iter()
        .any(|leg| leg.leg_id == plan.primary_outbound_leg_id)
    {
        return GateResult {
            passed: false,
            reason: Some(DecisionReasonV1::GateLinkedExchangePlan),
            quarantine: false,
        };
    }
    GateResult {
        passed: true,
        reason: None,
        quarantine: false,
    }
}

pub fn linked_outbound_total(request: &ExternalizationRequestV1) -> statebook_core::SignedRational {
    let Some(plan) = request.linked_plan() else {
        return statebook_core::SignedRational::new(0, 1).unwrap();
    };
    plan.legs
        .iter()
        .filter(|leg| leg.direction == DirectionV1::Outbound)
        .fold(
            statebook_core::SignedRational::new(0, 1).unwrap(),
            |acc, leg| {
                acc.checked_add(leg.amount)
                    .unwrap_or(statebook_core::SignedRational::new(0, 1).unwrap())
            },
        )
}
