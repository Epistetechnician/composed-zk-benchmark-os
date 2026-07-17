use statebook_settlement::{
    decide_and_transition, parse_settlement_scenario_v1, DecisionOutcomeV1, DecisionReasonV1,
};

const IMMEDIATE: &[u8] = include_bytes!("fixtures/p4/immediate_v1.json");

fn mutate_json(mutator: impl FnOnce(&mut serde_json::Value)) -> serde_json::Value {
    let mut value: serde_json::Value = serde_json::from_slice(IMMEDIATE).unwrap();
    mutator(&mut value);
    value
}

fn run(value: serde_json::Value) -> statebook_settlement::DecisionRecordV1 {
    let bytes = serde_json::to_vec(&value).unwrap();
    let scenario = parse_settlement_scenario_v1(&bytes).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    decide_and_transition(request, state, clock).unwrap()
}

#[test]
fn prepared_earlier_rejects_despite_fresh_transport() {
    let value = mutate_json(|value| {
        if let Some(observations) = value["evidence_snapshot"]["observations"].as_array_mut() {
            for observation in observations.iter_mut() {
                if observation["property"] == "source_authenticity_and_freshness" {
                    observation["prepared_earlier"] = serde_json::json!(true);
                    observation["replayed"] = serde_json::json!(false);
                }
            }
        }
    });
    let record = run(value);
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record.instant_release_amount().is_zero());
    assert!(record
        .reasons()
        .contains(&DecisionReasonV1::GatePreparedEarlierReuse));
}

#[test]
fn stale_content_rejects_despite_fresh_transport() {
    let value = mutate_json(|value| {
        if let Some(observations) = value["evidence_snapshot"]["observations"].as_array_mut() {
            for observation in observations.iter_mut() {
                if observation["property"] == "source_authenticity_and_freshness" {
                    observation["observed_at"] = serde_json::json!(1_709_999_950);
                    observation["content_observed_at"] = serde_json::json!(1);
                }
            }
        }
    });
    let record = run(value);
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record.instant_release_amount().is_zero());
    assert!(record
        .reasons()
        .contains(&DecisionReasonV1::GateSourceContentStale));
}

#[test]
fn dual_vendor_shared_upstream_quarantines() {
    let value = mutate_json(|value| {
        if let Some(observations) = value["evidence_snapshot"]["observations"].as_array_mut() {
            for observation in observations.iter_mut() {
                let property = observation["property"].as_str().unwrap_or("").to_owned();
                if property == "calculation_integrity" {
                    observation["current_roots"] =
                        serde_json::json!([{ "root_id": "vendor-a", "root_class": "data" }]);
                    observation["dependency_roots"] = serde_json::json!([{
                        "root_id": "compromised-upstream",
                        "root_class": "data"
                    }]);
                }
                if property == "solvency_and_liquid_resource_support" {
                    observation["current_roots"] =
                        serde_json::json!([{ "root_id": "vendor-b", "root_class": "data" }]);
                    observation["dependency_roots"] = serde_json::json!([{
                        "root_id": "compromised-upstream",
                        "root_class": "data"
                    }]);
                }
                if property == "evidence_root_disclosure" {
                    observation["current_roots"] = serde_json::json!([
                        { "root_id": "vendor-a", "root_class": "data" },
                        { "root_id": "vendor-b", "root_class": "data" }
                    ]);
                }
            }
        }
    });
    let record = run(value);
    assert_eq!(record.outcome(), DecisionOutcomeV1::Quarantined);
    assert!(record.instant_release_amount().is_zero());
    assert!(record
        .reasons()
        .contains(&DecisionReasonV1::GateEvidenceIndependence));
}

#[test]
fn action_oracle_valuation_root_overlap_rejects() {
    let value = mutate_json(|value| {
        value["valuation_profile"]["observations"][0]["root_id"] = serde_json::json!("calc-a");
        value["valuation_profile"]["independence_roots"] = serde_json::json!(["calc-a"]);
    });
    let record = run(value);
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record.instant_release_amount().is_zero());
    assert!(record
        .reasons()
        .contains(&DecisionReasonV1::ValuationActionOracleFallback));
}

#[test]
fn baseline_immediate_still_passes() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Immediate);
    assert!(!record.instant_release_amount().is_zero());
}
