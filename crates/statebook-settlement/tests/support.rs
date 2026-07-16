use ring::digest::{digest as ring_digest, SHA256};
use statebook_settlement::{intent_digest, intent_payload, parse_settlement_scenario_v1};

pub fn mutate_fixture(
    base: &[u8],
    update: impl FnOnce(&mut serde_json::Value),
) -> statebook_settlement::SettlementScenarioV1 {
    let mut value: serde_json::Value = serde_json::from_slice(base).unwrap();
    update(&mut value);
    parse_settlement_scenario_v1(&serde_json::to_vec(&value).unwrap()).unwrap()
}

pub fn try_mutate_fixture(
    base: &[u8],
    update: impl FnOnce(&mut serde_json::Value),
) -> Result<statebook_settlement::SettlementScenarioV1, String> {
    let mut value: serde_json::Value = serde_json::from_slice(base).unwrap();
    update(&mut value);
    parse_settlement_scenario_v1(&serde_json::to_vec(&value).unwrap())
        .map_err(|error| error.to_string())
}

pub fn gate_override_fixture(
    field: &str,
    pass: bool,
) -> statebook_settlement::SettlementScenarioV1 {
    mutate_fixture(include_bytes!("fixtures/p4/immediate_v1.json"), |value| {
        value["request"]["gate_overrides"] = serde_json::json!({ field: pass });
    })
}

pub fn linked_plan_scenario(valid: bool) -> statebook_settlement::SettlementScenarioV1 {
    mutate_fixture(include_bytes!("fixtures/p4/immediate_v1.json"), |value| {
        value["request"]["declared_release_class"] = serde_json::json!("atomic_linked_exchange");
        value["request"]["linked_plan"] = serde_json::json!({
            "plan_id": "plan-1",
            "leg_set_digest": "00000000000000000000000000000000000000000000000000000000000000aa",
            "primary_outbound_leg_id": "leg-out",
            "legs": [
                {
                    "leg_id": "leg-out",
                    "direction": "outbound",
                    "asset": "ETH",
                    "amount": { "numerator": "4", "denominator": "1" },
                    "budget_axis_id": "native-ETH"
                },
                {
                    "leg_id": "leg-in",
                    "direction": if valid { "inbound" } else { "outbound" },
                    "asset": "USD",
                    "amount": { "numerator": "8000", "denominator": "1" },
                    "budget_axis_id": "native-USD"
                }
            ]
        });
    })
}

pub fn obligation_scenario(valid: bool) -> statebook_settlement::SettlementScenarioV1 {
    mutate_fixture(include_bytes!("fixtures/p4/immediate_v1.json"), |value| {
        value["request"]["declared_release_class"] =
            serde_json::json!("external_risk_reducing_obligation");
        value["request"]["total_amount"] =
            serde_json::json!({ "numerator": "5", "denominator": "1" });
        value["request"]["obligation"] = serde_json::json!({
            "obligation_id": "obl-1",
            "beneficiary": "ben-1",
            "obligation_account": "obl-acct",
            "asset": "ETH",
            "exact_amount": { "numerator": if valid { "5" } else { "6" }, "denominator": "1" },
            "deadline": 1710003600,
            "valid_until": 1710003600,
            "destination_use_restricted": true,
            "exposure_before_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            "exposure_after_digest": "0000000000000000000000000000000000000000000000000000000000000001",
            "risk_reduction_ref": "0000000000000000000000000000000000000000000000000000000000000004"
        });
    })
}

pub fn linked_plan_with_legs(
    count: usize,
) -> Result<statebook_settlement::SettlementScenarioV1, String> {
    let legs: Vec<_> = (0..count)
        .map(|index| {
            serde_json::json!({
                "leg_id": format!("leg-{index}"),
                "direction": if index % 2 == 0 { "outbound" } else { "inbound" },
                "asset": "ETH",
                "amount": { "numerator": "1", "denominator": "1" },
                "budget_axis_id": "native-ETH"
            })
        })
        .collect();
    try_mutate_fixture(include_bytes!("fixtures/p4/immediate_v1.json"), |value| {
        value["request"]["declared_release_class"] = serde_json::json!("atomic_linked_exchange");
        value["request"]["linked_plan"] = serde_json::json!({
            "plan_id": "plan-big",
            "leg_set_digest": "00000000000000000000000000000000000000000000000000000000000000bb",
            "primary_outbound_leg_id": "leg-0",
            "legs": legs
        });
    })
}

pub fn state_with_axes(count: usize) -> Result<statebook_settlement::SettlementScenarioV1, String> {
    let mut value: serde_json::Value =
        serde_json::from_slice(include_bytes!("fixtures/p4/immediate_v1.json")).unwrap();
    let axes: Vec<_> = (0..count)
        .map(|index| {
            serde_json::json!({
                "asset": format!("ASSET{index}"),
                "cap": { "numerator": "1", "denominator": "1" }
            })
        })
        .collect();
    value["initial_state"]["ledger"]["axes"] = serde_json::json!(axes);
    parse_settlement_scenario_v1(&serde_json::to_vec(&value).unwrap())
        .map_err(|error| error.to_string())
}

pub fn assert_ring_golden_vectors() {
    let scenario =
        parse_settlement_scenario_v1(include_bytes!("fixtures/p4/immediate_v1.json")).unwrap();
    let request = scenario.request();
    let intent = intent_digest(request);
    let ring_hex = ring_domain_digest(b"statebook:p4-intent:v1\0", &intent_payload(request));
    assert_eq!(intent.to_hex(), ring_hex);
}

fn ring_domain_digest(domain: &[u8], payload: &[u8]) -> String {
    let mut input = Vec::with_capacity(domain.len() + 2 + payload.len());
    input.extend_from_slice(domain);
    input.extend_from_slice(&1_u16.to_be_bytes());
    input.extend_from_slice(payload);
    hex::encode(ring_digest(&SHA256, &input).as_ref())
}

pub fn run_scenario(
    scenario: statebook_settlement::SettlementScenarioV1,
) -> statebook_settlement::DecisionRecordV1 {
    let (request, state, clock) = scenario.into_kernel_input();
    statebook_settlement::decide_and_transition(request, state, clock).unwrap()
}
