use statebook_core::SignedRational;
use statebook_settlement::{
    apply_destination_finality_v1, apply_proven_no_outflow_v1, apply_transfer_submit_v1,
    available_capacity, decide_and_transition, parse_settlement_scenario_v1, DecisionOutcomeV1,
    DecisionReasonV1, TransferBudgetResultV1, TransferStatusV1,
};

const IMMEDIATE: &[u8] = include_bytes!("fixtures/p4/immediate_v1.json");

fn amount(n: i128) -> SignedRational {
    SignedRational::new(n, 1).unwrap()
}

#[test]
fn submit_moves_reserved_to_in_flight() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Immediate);
    let mut state = record.next_state().clone();
    let tip = state.ledger().tip_digest();
    let reserved_before = state.ledger().axes()[0].reserved();
    assert!(reserved_before.numerator() > 0);
    let result = apply_transfer_submit_v1(&mut state, "ETH", reserved_before, tip).unwrap();
    assert_eq!(result, TransferBudgetResultV1::Applied);
    assert_eq!(state.transfer_state().status(), TransferStatusV1::Submitted);
    assert_eq!(state.ledger().axes()[0].reserved(), amount(0));
    assert_eq!(state.ledger().axes()[0].in_flight(), reserved_before);
}

#[test]
fn destination_finality_consumes_without_restoring_capacity() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    let mut state = record.next_state().clone();
    let tip = state.ledger().tip_digest();
    let reserved = state.ledger().axes()[0].reserved();
    apply_transfer_submit_v1(&mut state, "ETH", reserved, tip).unwrap();
    let available_before = available_capacity(&state.ledger().axes()[0]).unwrap();
    let tip = state.ledger().tip_digest();
    let in_flight = state.ledger().axes()[0].in_flight();
    let result = apply_destination_finality_v1(&mut state, "ETH", in_flight, tip).unwrap();
    assert_eq!(result, TransferBudgetResultV1::Applied);
    assert_eq!(state.transfer_state().status(), TransferStatusV1::Consumed);
    assert_eq!(state.ledger().axes()[0].in_flight(), amount(0));
    assert_eq!(state.ledger().axes()[0].consumed(), in_flight);
    let available_after = available_capacity(&state.ledger().axes()[0]).unwrap();
    // Consumed does not free capacity: available stays the same as post-submit.
    assert_eq!(available_after, available_before);
}

#[test]
fn proven_no_outflow_valid_restores_capacity() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    let mut state = record.next_state().clone();
    let tip = state.ledger().tip_digest();
    let reserved = state.ledger().axes()[0].reserved();
    apply_transfer_submit_v1(&mut state, "ETH", reserved, tip).unwrap();
    let available_before = available_capacity(&state.ledger().axes()[0]).unwrap();
    let tip = state.ledger().tip_digest();
    let in_flight = state.ledger().axes()[0].in_flight();
    let result = apply_proven_no_outflow_v1(&mut state, "ETH", in_flight, tip, true).unwrap();
    assert_eq!(result, TransferBudgetResultV1::Applied);
    assert_eq!(
        state.transfer_state().status(),
        TransferStatusV1::ProvenNoOutflow
    );
    assert_eq!(state.ledger().axes()[0].in_flight(), amount(0));
    assert_eq!(state.ledger().axes()[0].consumed(), amount(0));
    let available_after = available_capacity(&state.ledger().axes()[0]).unwrap();
    assert!(available_after.numerator() > available_before.numerator());
}

#[test]
fn proven_no_outflow_invalid_leaves_in_flight() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    let mut state = record.next_state().clone();
    let tip = state.ledger().tip_digest();
    let reserved = state.ledger().axes()[0].reserved();
    apply_transfer_submit_v1(&mut state, "ETH", reserved, tip).unwrap();
    let tip = state.ledger().tip_digest();
    let in_flight = state.ledger().axes()[0].in_flight();
    let before = state.clone();
    let result = apply_proven_no_outflow_v1(&mut state, "ETH", in_flight, tip, false).unwrap();
    assert_eq!(
        result,
        TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::ProvenNoOutflowRejected
        }
    );
    assert_eq!(
        state.ledger().axes()[0].in_flight(),
        before.ledger().axes()[0].in_flight()
    );
    assert_eq!(state.transfer_state().status(), TransferStatusV1::Submitted);
}
