use statebook_settlement::{
    attempt_policy_transition_v1, decide_and_transition, parse_settlement_scenario_v1, ClockV1,
    DecisionOutcomeV1, DecisionReasonV1, PolicyTransitionResultV1, SettlementScenarioV1,
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

fn baseline_policy_json() -> serde_json::Value {
    serde_json::json!({
        "policy_id": "synthetic-tier-policy-v1",
        "policy_version": 1,
        "policy_digest": "0000000000000000000000000000000000000000000000000000000000000001",
        "assurance_tiers": {
            "quarantined": { "instant_fraction": { "numerator": "0", "denominator": "1" }, "delay_seconds": 0 },
            "unproven_or_novel": { "instant_fraction": { "numerator": "1", "denominator": "4" }, "delay_seconds": 3600 },
            "currently_assured": { "instant_fraction": { "numerator": "1", "denominator": "2" }, "delay_seconds": 1800 },
            "strong_current_assurance_low_impact": { "instant_fraction": { "numerator": "1", "denominator": "1" }, "delay_seconds": 0 }
        },
        "hysteresis": {
            "min_relax_dwell_seconds": 86400,
            "required_clean_epochs": 2,
            "successor_policy_digest": "0000000000000000000000000000000000000000000000000000000000000002"
        }
    })
}

#[test]
fn policy_version_rollback_rejects_zero_instant() {
    let mut active = baseline_policy_json();
    active["policy_version"] = serde_json::json!(2);
    let scenario = mutate_fixture(IMMEDIATE, |value| {
        value["initial_state"]["active_policy"] = active.clone();
        value["initial_state"]["last_policy_change_at"] = serde_json::json!(1_709_900_000);
        value["policy"]["policy_version"] = serde_json::json!(1);
    });
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record.reasons().contains(&DecisionReasonV1::PolicyRollback));
    assert!(record.instant_release_amount().is_zero());
}

#[test]
fn tighten_applies_immediately() {
    let mut active = baseline_policy_json();
    active["assurance_tiers"]["currently_assured"]["instant_fraction"] =
        serde_json::json!({ "numerator": "3", "denominator": "4" });
    let scenario = mutate_fixture(IMMEDIATE, |value| {
        value["initial_state"]["active_policy"] = active.clone();
        value["initial_state"]["last_policy_change_at"] = serde_json::json!(1_709_900_000);
        // Proposed policy keeps baseline 1/2 instant — a tighten vs active 3/4.
        value["policy"]["policy_digest"] =
            serde_json::json!("00000000000000000000000000000000000000000000000000000000000000aa");
        value["policy"]["policy_version"] = serde_json::json!(2);
    });
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Immediate);
    assert!(record.instant_release_amount().numerator() > 0);
}

#[test]
fn relax_before_gates_rejects() {
    let mut active = baseline_policy_json();
    active["assurance_tiers"]["currently_assured"]["instant_fraction"] =
        serde_json::json!({ "numerator": "1", "denominator": "4" });
    let scenario = mutate_fixture(IMMEDIATE, |value| {
        value["initial_state"]["active_policy"] = active.clone();
        value["initial_state"]["last_policy_change_at"] = serde_json::json!(1_710_000_000);
        value["initial_state"]["clean_epochs"] = serde_json::json!(0);
        value["policy"]["policy_version"] = serde_json::json!(2);
        value["policy"]["policy_digest"] =
            serde_json::json!("0000000000000000000000000000000000000000000000000000000000000002");
        value["policy"]["assurance_tiers"]["currently_assured"]["instant_fraction"] =
            serde_json::json!({ "numerator": "1", "denominator": "2" });
    });
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record
        .reasons()
        .contains(&DecisionReasonV1::PolicyRelaxRejected));
    assert!(record.instant_release_amount().is_zero());
}

#[test]
fn relax_with_gates_succeeds() {
    let mut active = baseline_policy_json();
    active["assurance_tiers"]["currently_assured"]["instant_fraction"] =
        serde_json::json!({ "numerator": "1", "denominator": "4" });
    let scenario = mutate_fixture(IMMEDIATE, |value| {
        value["initial_state"]["active_policy"] = active.clone();
        value["initial_state"]["last_policy_change_at"] = serde_json::json!(1_709_913_600);
        value["initial_state"]["clean_epochs"] = serde_json::json!(2);
        value["policy"]["policy_version"] = serde_json::json!(2);
        value["policy"]["policy_digest"] =
            serde_json::json!("0000000000000000000000000000000000000000000000000000000000000002");
        value["policy"]["assurance_tiers"]["currently_assured"]["instant_fraction"] =
            serde_json::json!({ "numerator": "1", "denominator": "2" });
    });
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Immediate);
    assert!(record.instant_release_amount().numerator() > 0);
}

#[test]
fn attempt_policy_transition_mirrors_kernel_gates() {
    let mut active = baseline_policy_json();
    active["policy_version"] = serde_json::json!(3);
    let scenario = mutate_fixture(IMMEDIATE, |value| {
        value["initial_state"]["active_policy"] = active.clone();
        value["policy"]["policy_version"] = serde_json::json!(1);
    });
    let clock = ClockV1::new(scenario.clock().now());
    let proposed = scenario.policy().clone();
    let (_, mut state, _) = scenario.into_kernel_input();
    let result = attempt_policy_transition_v1(&mut state, &proposed, &clock);
    assert_eq!(
        result,
        PolicyTransitionResultV1::Rejected {
            reason: DecisionReasonV1::PolicyRollback
        }
    );
}
