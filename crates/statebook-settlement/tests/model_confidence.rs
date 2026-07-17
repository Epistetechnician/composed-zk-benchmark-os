use statebook_settlement::{
    decide_and_transition, parse_settlement_scenario_v1, DecisionOutcomeV1, DecisionReasonV1,
};

const IMMEDIATE: &[u8] = include_bytes!("fixtures/p4/immediate_v1.json");

fn mutate_json(mutator: impl FnOnce(&mut serde_json::Value)) -> serde_json::Value {
    let mut value: serde_json::Value = serde_json::from_slice(IMMEDIATE).unwrap();
    mutator(&mut value);
    value
}

#[test]
fn model_confidence_cannot_bypass_failed_hard_gate() {
    let value = mutate_json(|value| {
        value["request"]["gate_overrides"] = serde_json::json!({ "calculation_valid": false });
        value["request"]["model_confidence_claimed"] = serde_json::json!(true);
    });
    let bytes = serde_json::to_vec(&value).unwrap();
    let scenario = parse_settlement_scenario_v1(&bytes).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    assert!(request.model_confidence_claimed());
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record.instant_release_amount().is_zero());
    assert!(record
        .reasons()
        .contains(&DecisionReasonV1::GateCalculationIntegrity));
    assert!(record
        .reasons()
        .contains(&DecisionReasonV1::ModelConfidenceIgnored));
}

#[test]
fn baseline_immediate_unchanged_without_confidence_claim() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    assert!(!request.model_confidence_claimed());
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Immediate);
    assert!(!record.instant_release_amount().is_zero());
    assert!(!record
        .reasons()
        .contains(&DecisionReasonV1::ModelConfidenceIgnored));
}
