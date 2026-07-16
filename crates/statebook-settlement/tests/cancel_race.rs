use statebook_settlement::{
    apply_cancel_v1, decide_and_transition, intent_digest, parse_settlement_scenario_v1,
    CancelApplyResultV1, ClockV1, DecisionOutcomeV1, DecisionReasonV1, DigestV1, QueueStatusV1,
    SettlementScenarioV1,
};

const QUEUED: &[u8] = include_bytes!("fixtures/p4/queued_v1.json");

fn mutate_fixture(
    base: &[u8],
    update: impl FnOnce(&mut serde_json::Value),
) -> SettlementScenarioV1 {
    let mut value: serde_json::Value = serde_json::from_slice(base).unwrap();
    update(&mut value);
    parse_settlement_scenario_v1(&serde_json::to_vec(&value).unwrap()).unwrap()
}

fn queue_once() -> (
    statebook_settlement::ExternalizationRequestV1,
    statebook_settlement::SettlementStateV1,
    DigestV1,
) {
    let scenario = mutate_fixture(QUEUED, |_| {});
    let (request, state, clock) = scenario.into_kernel_input();
    let intent = intent_digest(&request);
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Queued);
    assert_eq!(record.next_state().bound_intent_digest(), Some(intent));
    let scenario = mutate_fixture(QUEUED, |_| {});
    let (request, _, _) = scenario.into_kernel_input();
    (request, record.next_state().clone(), intent)
}

#[test]
fn cancel_with_new_intent_marks_cancelled() {
    let (_request, mut state, bound) = queue_once();
    let cancel_intent = DigestV1::from_raw_bytes([0xab; 32]);
    let result = apply_cancel_v1(&mut state, bound, cancel_intent).unwrap();
    assert_eq!(result, CancelApplyResultV1::Accepted);
    assert_eq!(state.queue().status(), QueueStatusV1::Cancelled);
    assert_eq!(state.bound_intent_digest(), None);
}

#[test]
fn cancel_with_same_intent_rejects() {
    let (_request, mut state, bound) = queue_once();
    let before = state.clone();
    let result = apply_cancel_v1(&mut state, bound, bound).unwrap();
    assert_eq!(
        result,
        CancelApplyResultV1::Rejected {
            reason: DecisionReasonV1::IntentDigestMismatch
        }
    );
    assert_eq!(state, before);
}

#[test]
fn decide_on_cancelled_rejects_zero_instant() {
    let (request, mut state, bound) = queue_once();
    apply_cancel_v1(&mut state, bound, DigestV1::from_raw_bytes([0xcd; 32])).unwrap();
    let record = decide_and_transition(request, state, ClockV1::new(1_710_000_000)).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record.reasons().contains(&DecisionReasonV1::QueueCancelled));
    assert!(record.instant_release_amount().is_zero());
}

#[test]
fn destination_replacement_without_new_intent_rejects() {
    let scenario = mutate_fixture(QUEUED, |value| {
        value["request"]["destination"] = serde_json::json!("dest-replacement");
    });
    let (request, _, _) = scenario.into_kernel_input();
    let intent = intent_digest(&request);
    let scenario = mutate_fixture(QUEUED, |value| {
        value["initial_state"]["queue"]["status"] = serde_json::json!("queued");
        value["initial_state"]["bound_intent_digest"] = serde_json::json!(intent.to_hex());
        value["initial_state"]["bound_destination"] = serde_json::json!("dest-original");
        value["request"]["destination"] = serde_json::json!("dest-replacement");
    });
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record
        .reasons()
        .contains(&DecisionReasonV1::IntentDigestMismatch));
    assert!(record.instant_release_amount().is_zero());
}

#[test]
fn cancel_then_decide_race_zero_instant() {
    let (request, mut state, bound) = queue_once();
    apply_cancel_v1(&mut state, bound, DigestV1::from_raw_bytes([0x11; 32])).unwrap();
    let record = decide_and_transition(request, state, ClockV1::new(1_710_100_000)).unwrap();
    assert!(record.instant_release_amount().is_zero());
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
}
