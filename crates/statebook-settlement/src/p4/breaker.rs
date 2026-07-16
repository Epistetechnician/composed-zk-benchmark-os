#![allow(dead_code)]

use super::types::{BreakerScopeV1, BreakerStateV1, DecisionReasonV1};

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
        if now >= expires_at && scope.renewal_count >= scope.renewal_ceiling {
            scope.state = BreakerStateV1::Resolution;
        }
    }
}

pub fn breaker_blocks_release(scope: &BreakerScopeV1) -> Option<DecisionReasonV1> {
    match scope.state {
        BreakerStateV1::Halted => Some(DecisionReasonV1::BreakerHalted),
        BreakerStateV1::Challenged => Some(DecisionReasonV1::BreakerFrozen),
        _ => None,
    }
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
