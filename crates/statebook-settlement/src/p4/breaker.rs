use super::error::SettlementTransitionErrorV1;
use super::types::{BreakerScopeV1, BreakerStateV1, DecisionReasonV1, SettlementStateV1};

pub fn validate_breaker_transition(from: BreakerStateV1, to: BreakerStateV1) -> bool {
    use BreakerStateV1::*;
    matches!(
        (from, to),
        (Normal, Guarded)
            | (Normal, Halted)
            | (Guarded, Challenged)
            | (Guarded, Halted)
            | (Guarded, Resolution)
            | (Challenged, Guarded)
            | (Challenged, Halted)
            | (Challenged, Resolution)
            | (Halted, Resolution)
            | (Resolution, Recovery)
            | (Recovery, Normal)
            | (Recovery, Guarded)
            | (Recovery, Halted)
    )
}

pub fn apply_ttl_exhaustion(scope: &mut BreakerScopeV1, now: i64) {
    if let Some(expires_at) = scope.expires_at {
        if now >= expires_at
            && scope.renewal_count >= scope.renewal_ceiling
            && (validate_breaker_transition(scope.state, BreakerStateV1::Resolution)
                || scope.state == BreakerStateV1::Resolution)
        {
            scope.state = BreakerStateV1::Resolution;
        }
    }
}

pub fn apply_ttl_exhaustion_to_state(state: &mut SettlementStateV1, now: i64) {
    for scope in &mut state.breakers {
        apply_ttl_exhaustion(scope, now);
    }
}

pub fn breaker_blocks_release(scope: &BreakerScopeV1, now: i64) -> Option<DecisionReasonV1> {
    match scope.state {
        BreakerStateV1::Halted => Some(DecisionReasonV1::BreakerHalted),
        // Challenged is handled later as Frozen outcome, not an early Rejected path.
        BreakerStateV1::Challenged => None,
        BreakerStateV1::Resolution => Some(DecisionReasonV1::BreakerResolutionRequired),
        BreakerStateV1::Guarded | BreakerStateV1::Recovery => {
            if scope
                .expires_at
                .map(|expires_at| now >= expires_at)
                .unwrap_or(false)
            {
                // Expired protective scope below ceiling: block without silent renew.
                Some(DecisionReasonV1::BreakerFrozen)
            } else {
                None
            }
        }
        BreakerStateV1::Normal => None,
    }
}

pub fn collect_breaker_block_reasons(state: &SettlementStateV1, now: i64) -> Vec<DecisionReasonV1> {
    let mut reasons = Vec::new();
    for scope in state.breakers() {
        if let Some(reason) = breaker_blocks_release(scope, now) {
            if !reasons.contains(&reason) {
                reasons.push(reason);
            }
        }
    }
    reasons
}

/// Extend a protective breaker expiry when renewals remain. At or above the
/// ceiling, reject without mutating state.
pub fn attempt_breaker_renewal_v1(
    state: &mut SettlementStateV1,
    scope_id: &str,
    now: i64,
    extend_seconds: i64,
) -> Result<(), SettlementTransitionErrorV1> {
    if extend_seconds <= 0 {
        return Err(SettlementTransitionErrorV1::InvalidBreakerRenewal);
    }
    let Some(scope) = state
        .breakers
        .iter_mut()
        .find(|scope| scope.scope_id == scope_id)
    else {
        return Err(SettlementTransitionErrorV1::InvalidBreakerRenewal);
    };
    if scope.renewal_count >= scope.renewal_ceiling {
        return Err(SettlementTransitionErrorV1::BreakerRenewalRejected);
    }
    let Some(expires_at) = scope.expires_at else {
        return Err(SettlementTransitionErrorV1::InvalidBreakerRenewal);
    };
    if now < expires_at {
        // Renewal is only for expired-or-due scopes in this slice.
        return Err(SettlementTransitionErrorV1::InvalidBreakerRenewal);
    }
    scope.renewal_count = scope.renewal_count.saturating_add(1);
    scope.expires_at = Some(
        now.checked_add(extend_seconds)
            .ok_or(SettlementTransitionErrorV1::ArithmeticOverflow)?,
    );
    Ok(())
}

pub fn global_breaker_state(scopes: &[BreakerScopeV1]) -> BreakerStateV1 {
    scopes
        .iter()
        .map(|scope| scope.state)
        .max_by_key(|state| breaker_severity(*state))
        .unwrap_or(BreakerStateV1::Normal)
}

fn breaker_severity(state: BreakerStateV1) -> u8 {
    match state {
        BreakerStateV1::Normal => 0,
        BreakerStateV1::Guarded => 1,
        BreakerStateV1::Recovery => 2,
        BreakerStateV1::Resolution => 3,
        BreakerStateV1::Challenged => 4,
        BreakerStateV1::Halted => 5,
    }
}
