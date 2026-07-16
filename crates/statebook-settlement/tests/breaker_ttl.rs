use statebook_settlement::{
    attempt_breaker_renewal_v1, decide_and_transition, parse_settlement_scenario_v1,
    BreakerStateV1, DecisionOutcomeV1, DecisionReasonV1, SettlementScenarioV1,
    SettlementTransitionErrorV1,
};

const IMMEDIATE: &[u8] = include_bytes!("fixtures/p4/immediate_v1.json");

fn mutate_fixture(
    base: &[u8],
    update: impl FnOnce(&mut serde_json::Value),
) -> SettlementScenarioV1 {
    let mut value: serde_json::Value = serde_json::from_slice(base).unwrap();
    update(&mut value);
    parse_settlement_scenario_v1(&serde_json::to_vec(&value).unwrap()).unwrap()
}

#[test]
fn ttl_at_ceiling_enters_resolution_and_rejects_zero_instant() {
    let scenario = mutate_fixture(IMMEDIATE, |value| {
        value["initial_state"]["breakers"][0] = serde_json::json!({
            "scope_id": "global",
            "state": "halted",
            "expires_at": 1709999999,
            "renewal_count": 3,
            "renewal_ceiling": 3
        });
    });
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record.instant_release_amount().is_zero());
    assert!(record
        .reasons()
        .contains(&DecisionReasonV1::BreakerResolutionRequired));
    assert_eq!(
        record.next_state().breakers()[0].state(),
        BreakerStateV1::Resolution
    );
}

#[test]
fn expired_guarded_below_ceiling_blocks_without_silent_renewal() {
    let scenario = mutate_fixture(IMMEDIATE, |value| {
        value["initial_state"]["breakers"][0] = serde_json::json!({
            "scope_id": "global",
            "state": "guarded",
            "expires_at": 1709999999,
            "renewal_count": 1,
            "renewal_ceiling": 3
        });
    });
    let (request, state, clock) = scenario.into_kernel_input();
    let before = state.breakers()[0].renewal_count();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record.instant_release_amount().is_zero());
    assert!(record.reasons().contains(&DecisionReasonV1::BreakerFrozen));
    assert_eq!(
        record.next_state().breakers()[0].state(),
        BreakerStateV1::Guarded
    );
    assert_eq!(record.next_state().breakers()[0].renewal_count(), before);
    assert_eq!(
        record.next_state().breakers()[0].expires_at(),
        Some(1709999999)
    );
}

#[test]
fn renewal_at_ceiling_rejects_without_state_mutation() {
    let scenario = mutate_fixture(IMMEDIATE, |value| {
        value["initial_state"]["breakers"][0] = serde_json::json!({
            "scope_id": "global",
            "state": "halted",
            "expires_at": 1709999999,
            "renewal_count": 3,
            "renewal_ceiling": 3
        });
    });
    let mut state = scenario.into_kernel_input().1;
    let before_count = state.breakers()[0].renewal_count();
    let before_expires = state.breakers()[0].expires_at();
    let before_state = state.breakers()[0].state();
    let error = attempt_breaker_renewal_v1(&mut state, "global", 1710000000, 3600).unwrap_err();
    assert_eq!(error, SettlementTransitionErrorV1::BreakerRenewalRejected);
    assert_eq!(state.breakers()[0].renewal_count(), before_count);
    assert_eq!(state.breakers()[0].expires_at(), before_expires);
    assert_eq!(state.breakers()[0].state(), before_state);
}

#[test]
fn renewal_below_ceiling_extends_expiry() {
    let scenario = mutate_fixture(IMMEDIATE, |value| {
        value["initial_state"]["breakers"][0] = serde_json::json!({
            "scope_id": "global",
            "state": "guarded",
            "expires_at": 1709999999,
            "renewal_count": 1,
            "renewal_ceiling": 3
        });
    });
    let mut state = scenario.into_kernel_input().1;
    attempt_breaker_renewal_v1(&mut state, "global", 1710000000, 3600).unwrap();
    assert_eq!(state.breakers()[0].renewal_count(), 2);
    assert_eq!(state.breakers()[0].expires_at(), Some(1710003600));
    assert_eq!(state.breakers()[0].state(), BreakerStateV1::Guarded);
}

#[test]
fn halted_without_ttl_still_rejects() {
    let scenario = parse_settlement_scenario_v1(
        &serde_json::to_vec(&{
            let mut value: serde_json::Value = serde_json::from_slice(IMMEDIATE).unwrap();
            value["initial_state"]["breakers"][0]["state"] = serde_json::json!("halted");
            value
        })
        .unwrap(),
    )
    .unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record.reasons().contains(&DecisionReasonV1::BreakerHalted));
}
