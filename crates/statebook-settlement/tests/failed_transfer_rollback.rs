use statebook_settlement::{
    apply_destination_finality_v1, apply_failed_transfer_rollback_v1, apply_transfer_submit_v1,
    available_capacity, decide_and_transition, parse_settlement_scenario_v1, DecisionOutcomeV1,
    DecisionReasonV1, TransferBudgetResultV1,
};

const IMMEDIATE: &[u8] = include_bytes!("fixtures/p4/immediate_v1.json");

#[test]
fn explicit_rollback_restores_available_capacity() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Immediate);
    let mut state = record.next_state().clone();
    let reserved = state.ledger().axes()[0].reserved();
    let available_before = available_capacity(&state.ledger().axes()[0]).unwrap();
    let tip = state.ledger().tip_digest();
    let result = apply_failed_transfer_rollback_v1(&mut state, "ETH", reserved, tip).unwrap();
    assert_eq!(result, TransferBudgetResultV1::Applied);
    assert!(state.ledger().axes()[0].reserved().is_zero());
    let available_after = available_capacity(&state.ledger().axes()[0]).unwrap();
    assert_eq!(
        available_after,
        available_before.checked_add(reserved).unwrap()
    );
}

#[test]
fn double_rollback_rejects() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    let mut state = record.next_state().clone();
    let reserved = state.ledger().axes()[0].reserved();
    let tip = state.ledger().tip_digest();
    apply_failed_transfer_rollback_v1(&mut state, "ETH", reserved, tip).unwrap();
    let tip = state.ledger().tip_digest();
    let again = apply_failed_transfer_rollback_v1(&mut state, "ETH", reserved, tip).unwrap();
    assert_eq!(
        again,
        TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::FailedTransferRollbackRejected,
        }
    );
}

#[test]
fn sequential_finalizer_stale_tip_one_success() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    let mut state = record.next_state().clone();
    let reserved = state.ledger().axes()[0].reserved();
    let tip_before_submit = state.ledger().tip_digest();
    apply_transfer_submit_v1(&mut state, "ETH", reserved, tip_before_submit).unwrap();
    let tip_after_submit = state.ledger().tip_digest();
    let in_flight = state.ledger().axes()[0].in_flight();
    let stale = apply_destination_finality_v1(&mut state, "ETH", in_flight, tip_before_submit);
    assert!(matches!(
        stale,
        Err(statebook_settlement::SettlementTransitionErrorV1::LedgerCasConflict)
    ));
    let ok = apply_destination_finality_v1(&mut state, "ETH", in_flight, tip_after_submit).unwrap();
    assert_eq!(ok, TransferBudgetResultV1::Applied);
}

#[test]
fn frozen_path_does_not_leak_reserved_exposure() {
    let mut value: serde_json::Value = serde_json::from_slice(IMMEDIATE).unwrap();
    value["initial_state"]["queue"]["status"] = serde_json::json!("challenged");
    let bytes = serde_json::to_vec(&value).unwrap();
    let scenario = parse_settlement_scenario_v1(&bytes).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let available_before = available_capacity(&state.ledger().axes()[0]).unwrap();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Frozen);
    assert!(record.instant_release_amount().is_zero());
    let next = record.next_state();
    assert!(next.ledger().axes()[0].reserved().is_zero());
    assert!(next.ledger().axes()[0].in_flight().is_zero());
    let available_after = available_capacity(&next.ledger().axes()[0]).unwrap();
    assert_eq!(available_after, available_before);
}
