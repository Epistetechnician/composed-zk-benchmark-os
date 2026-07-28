use statebook_settlement::{
    decide_and_transition, parse_settlement_scenario_v1, DecisionOutcomeV1, DecisionReasonV1,
};

const QUEUED: &[u8] = include_bytes!("fixtures/p4/queued_v1.json");

#[test]
fn monetize_while_queued_rejects() {
    let scenario = parse_settlement_scenario_v1(QUEUED).unwrap();
    let first = {
        let (request, state, clock) = scenario.into_kernel_input();
        decide_and_transition(request, state, clock).unwrap()
    };
    assert_eq!(first.outcome(), DecisionOutcomeV1::Queued);

    let mut value: serde_json::Value = serde_json::from_slice(QUEUED).unwrap();
    value["request"]["monetizes_queued_value"] = serde_json::json!(true);
    let bytes = serde_json::to_vec(&value).unwrap();
    let scenario = parse_settlement_scenario_v1(&bytes).unwrap();
    let (request, _, clock) = scenario.into_kernel_input();
    assert!(request.monetizes_queued_value());
    let second = decide_and_transition(request, first.next_state().clone(), clock).unwrap();
    assert_eq!(second.outcome(), DecisionOutcomeV1::Rejected);
    assert!(second.instant_release_amount().is_zero());
    assert!(second
        .reasons()
        .contains(&DecisionReasonV1::QueuedValueMonetization));
}

#[test]
fn anomaly_after_instant_blocks_queued_remainder() {
    let scenario = parse_settlement_scenario_v1(QUEUED).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let first = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(first.outcome(), DecisionOutcomeV1::Queued);
    assert!(!first.instant_release_amount().is_zero());

    let mut value: serde_json::Value = serde_json::from_slice(QUEUED).unwrap();
    value["request"]["gate_overrides"] = serde_json::json!({ "anomaly_clear": false });
    let bytes = serde_json::to_vec(&value).unwrap();
    let scenario = parse_settlement_scenario_v1(&bytes).unwrap();
    let (request, _, clock) = scenario.into_kernel_input();
    let second = decide_and_transition(request, first.next_state().clone(), clock).unwrap();
    assert_eq!(second.outcome(), DecisionOutcomeV1::Rejected);
    assert!(second.instant_release_amount().is_zero());
    assert!(second
        .reasons()
        .contains(&DecisionReasonV1::GateAnomalyEmergency));
}
