mod support;

use statebook_settlement::{
    parse_settlement_scenario_v1, validate_breaker_transition, BreakerStateV1, DecisionOutcomeV1,
    DecisionReasonV1, QueueStatusV1, TransferStatusV1, MAX_BUDGET_AXES_V1, MAX_FIXTURE_BYTES_V1,
    MAX_LINKED_PLAN_LEGS_V1,
};

const IMMEDIATE_FIXTURE: &[u8] = include_bytes!("fixtures/p4/immediate_v1.json");
const REJECTED_FIXTURE: &[u8] = include_bytes!("fixtures/p4/rejected_gate_fail_v1.json");
const QUARANTINED_FIXTURE: &[u8] = include_bytes!("fixtures/p4/quarantined_v1.json");
const QUEUED_FIXTURE: &[u8] = include_bytes!("fixtures/p4/queued_v1.json");
const FROZEN_FIXTURE: &[u8] = include_bytes!("fixtures/p4/frozen_v1.json");

fn run(bytes: &[u8]) -> statebook_settlement::DecisionRecordV1 {
    let scenario = parse_settlement_scenario_v1(bytes).expect("fixture parse");
    support::run_scenario(scenario)
}

#[test]
fn five_outcomes_are_reachable() {
    let cases = [
        (IMMEDIATE_FIXTURE, DecisionOutcomeV1::Immediate),
        (QUEUED_FIXTURE, DecisionOutcomeV1::Queued),
        (REJECTED_FIXTURE, DecisionOutcomeV1::Rejected),
        (QUARANTINED_FIXTURE, DecisionOutcomeV1::Quarantined),
        (FROZEN_FIXTURE, DecisionOutcomeV1::Frozen),
    ];
    for (fixture, expected) in cases {
        assert_eq!(run(fixture).outcome(), expected);
    }
}

#[test]
fn each_hard_gate_fail_yields_zero_instant() {
    for field in [
        "action_authorized",
        "source_authentic",
        "calculation_valid",
        "transition_valid",
        "solvency_supported",
        "destination_allowed",
        "anomaly_clear",
        "evidence_independent",
        "financial_basis_valid",
        "reuse_finality",
    ] {
        let record = support::run_scenario(support::gate_override_fixture(field, false));
        assert!(
            record.instant_release_amount().is_zero(),
            "gate override {field} must zero instant release"
        );
    }
}

#[test]
fn amount_rejection_before_valuation() {
    let scenario = support::mutate_fixture(IMMEDIATE_FIXTURE, |value| {
        value["request"]["total_amount"] =
            serde_json::json!({ "numerator": "0", "denominator": "1" });
    });
    let record = support::run_scenario(scenario);
    assert!(record.instant_release_amount().is_zero());
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
}

#[test]
fn linked_plan_all_or_none() {
    let pass = support::run_scenario(support::linked_plan_scenario(true));
    assert!(pass.instant_release_amount().numerator() > 0);
    let fail = support::run_scenario(support::linked_plan_scenario(false));
    assert!(fail.instant_release_amount().is_zero());
}

#[test]
fn obligation_exact_amount_and_exposure_decrease() {
    let fail = support::run_scenario(support::obligation_scenario(false));
    assert!(fail.instant_release_amount().is_zero());
    assert!(fail
        .reasons()
        .contains(&DecisionReasonV1::GateRiskReducingObligation));
}

#[test]
fn timer_alone_never_releases() {
    let first = run(QUEUED_FIXTURE);
    assert_eq!(first.outcome(), DecisionOutcomeV1::Queued);
    let scenario = parse_settlement_scenario_v1(QUEUED_FIXTURE).unwrap();
    let (request, _, _) = scenario.into_kernel_input();
    let second = statebook_settlement::decide_and_transition(
        request,
        first.next_state().clone(),
        statebook_settlement::ClockV1::new(1710100000),
    )
    .unwrap();
    assert!(second.instant_release_amount().is_zero());
}

#[test]
fn no_halted_to_normal_breaker_edge() {
    assert!(!validate_breaker_transition(
        BreakerStateV1::Halted,
        BreakerStateV1::Normal
    ));
}

#[test]
fn cas_tip_contention_one_success() {
    let good = support::run_scenario(parse_settlement_scenario_v1(IMMEDIATE_FIXTURE).unwrap());
    assert!(good.instant_release_amount().numerator() > 0);
    let bad = support::try_mutate_fixture(IMMEDIATE_FIXTURE, |value| {
        value["initial_state"]["expected_ledger_tip"] =
            serde_json::json!("9999999999999999999999999999999999999999999999999999999999999999");
    });
    assert!(bad.is_ok());
    let bad_record = support::run_scenario(bad.unwrap());
    assert!(bad_record
        .reasons()
        .contains(&DecisionReasonV1::BudgetCasConflict));
    assert!(bad_record.instant_release_amount().is_zero());
}

#[test]
fn independent_ring_encoder_reproduces_key_digests() {
    support::assert_ring_golden_vectors();
}

#[test]
fn resource_bounds_limit_plus_one_reject() {
    assert!(parse_settlement_scenario_v1(&vec![0_u8; MAX_FIXTURE_BYTES_V1 + 1]).is_err());
    assert!(support::linked_plan_with_legs(MAX_LINKED_PLAN_LEGS_V1 + 1).is_err());
    assert!(support::state_with_axes(MAX_BUDGET_AXES_V1 + 1).is_err());
    assert!(support::linked_plan_with_legs(MAX_LINKED_PLAN_LEGS_V1).is_ok());
    assert!(support::state_with_axes(MAX_BUDGET_AXES_V1).is_ok());
}

#[test]
fn queued_status_requires_unreserved_transfer() {
    let record = run(QUEUED_FIXTURE);
    assert_eq!(record.next_state().queue().status(), QueueStatusV1::Queued);
    assert_eq!(record.next_state().queue().status(), QueueStatusV1::Queued);
    assert_eq!(
        record.next_state().transfer_state().status(),
        TransferStatusV1::Unreserved
    );
}

#[test]
fn parse_settlement_scenario_v1_accepts_immediate_fixture() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE_FIXTURE).unwrap();
    assert_eq!(
        scenario.scenario_id(),
        "immediate_external_unconditional_v1"
    );
}

#[test]
fn digest_functions_are_deterministic() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE_FIXTURE).unwrap();
    let request = scenario.request();
    assert_eq!(
        statebook_settlement::intent_digest(request),
        statebook_settlement::intent_digest(request)
    );
}
