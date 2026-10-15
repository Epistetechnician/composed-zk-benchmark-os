use core::cmp::Ordering;

use super::types::{
    ClockV1, DecisionReasonV1, SettlementPolicyV1, SettlementStateV1, TierFractionV1,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PolicyTransitionResultV1 {
    Unchanged,
    Tightened,
    Relaxed,
    Rejected { reason: DecisionReasonV1 },
}

fn tier_pairs(policy: &SettlementPolicyV1) -> [&TierFractionV1; 4] {
    [
        &policy.assurance_tiers.quarantined,
        &policy.assurance_tiers.unproven_or_novel,
        &policy.assurance_tiers.currently_assured,
        &policy.assurance_tiers.strong_current_assurance_low_impact,
    ]
}

fn instant_cmp(left: &TierFractionV1, right: &TierFractionV1) -> Ordering {
    left.instant_fraction
        .checked_cmp(right.instant_fraction)
        .unwrap_or(Ordering::Equal)
}

fn has_tighten(active: &SettlementPolicyV1, proposed: &SettlementPolicyV1) -> bool {
    for (old, new) in tier_pairs(active).into_iter().zip(tier_pairs(proposed)) {
        if instant_cmp(new, old) == Ordering::Less || new.delay_seconds > old.delay_seconds {
            return true;
        }
    }
    false
}

fn has_relax(active: &SettlementPolicyV1, proposed: &SettlementPolicyV1) -> bool {
    for (old, new) in tier_pairs(active).into_iter().zip(tier_pairs(proposed)) {
        if instant_cmp(new, old) == Ordering::Greater || new.delay_seconds < old.delay_seconds {
            return true;
        }
    }
    false
}

pub fn evaluate_policy_transition_v1(
    state: &SettlementStateV1,
    proposed: &SettlementPolicyV1,
    clock: &ClockV1,
) -> PolicyTransitionResultV1 {
    let active = &state.active_policy;
    if proposed.policy_digest == active.policy_digest
        && proposed.policy_version == active.policy_version
    {
        return PolicyTransitionResultV1::Unchanged;
    }
    if proposed.policy_version < active.policy_version {
        return PolicyTransitionResultV1::Rejected {
            reason: DecisionReasonV1::PolicyRollback,
        };
    }
    let tighten = has_tighten(active, proposed);
    let relax = has_relax(active, proposed);
    if relax {
        let dwell_ok = clock.now().saturating_sub(state.last_policy_change_at)
            >= active.hysteresis.min_relax_dwell_seconds;
        let epochs_ok = state.clean_epochs >= active.hysteresis.required_clean_epochs;
        let successor_ok = proposed.policy_digest == active.hysteresis.successor_policy_digest;
        let version_ok = proposed.policy_version > active.policy_version;
        if dwell_ok && epochs_ok && successor_ok && version_ok {
            return PolicyTransitionResultV1::Relaxed;
        }
        return PolicyTransitionResultV1::Rejected {
            reason: DecisionReasonV1::PolicyRelaxRejected,
        };
    }
    if tighten || proposed.policy_digest != active.policy_digest {
        return PolicyTransitionResultV1::Tightened;
    }
    PolicyTransitionResultV1::Unchanged
}

pub fn attempt_policy_transition_v1(
    state: &mut SettlementStateV1,
    proposed: &SettlementPolicyV1,
    clock: &ClockV1,
) -> PolicyTransitionResultV1 {
    let result = evaluate_policy_transition_v1(state, proposed, clock);
    match result {
        PolicyTransitionResultV1::Tightened | PolicyTransitionResultV1::Relaxed => {
            state.active_policy = proposed.clone();
            state.last_policy_change_at = clock.now();
            if matches!(result, PolicyTransitionResultV1::Tightened) {
                state.clean_epochs = 0;
            }
        }
        PolicyTransitionResultV1::Unchanged | PolicyTransitionResultV1::Rejected { .. } => {}
    }
    result
}

pub(crate) fn collect_hysteresis_block_reason(
    state: &SettlementStateV1,
    proposed: &SettlementPolicyV1,
    now: i64,
) -> Option<DecisionReasonV1> {
    match evaluate_policy_transition_v1(state, proposed, &ClockV1::new(now)) {
        PolicyTransitionResultV1::Rejected { reason } => Some(reason),
        _ => None,
    }
}

pub(crate) fn apply_accepted_policy_to_state(
    state: &mut SettlementStateV1,
    proposed: &SettlementPolicyV1,
    now: i64,
) {
    let clock = ClockV1::new(now);
    let _ = attempt_policy_transition_v1(state, proposed, &clock);
}
