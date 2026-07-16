use statebook_core::SignedRational;
use statebook_settlement::{
    apply_budget_refill_v1, apply_destination_finality_v1, apply_transfer_submit_v1,
    available_capacity, decide_and_transition, parse_settlement_scenario_v1, DecisionOutcomeV1,
    DecisionReasonV1, TransferBudgetResultV1, MAX_REFILL_PER_EPOCH_V1,
};

const IMMEDIATE: &[u8] = include_bytes!("fixtures/p4/immediate_v1.json");

fn amount(n: i128) -> SignedRational {
    SignedRational::new(n, 1).unwrap()
}

fn consume_instant_release() -> statebook_settlement::SettlementStateV1 {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Immediate);
    let mut state = record.next_state().clone();
    let tip = state.ledger().tip_digest();
    let reserved = state.ledger().axes()[0].reserved();
    apply_transfer_submit_v1(&mut state, "ETH", reserved, tip).unwrap();
    let tip = state.ledger().tip_digest();
    let in_flight = state.ledger().axes()[0].in_flight();
    apply_destination_finality_v1(&mut state, "ETH", in_flight, tip).unwrap();
    state
}

#[test]
fn sequential_refill_restores_capacity_and_bumps_epoch() {
    let mut state = consume_instant_release();
    assert_eq!(state.ledger().epoch(), 1);
    assert!(state.ledger().axes()[0].consumed().numerator() > 0);
    let available_before = available_capacity(&state.ledger().axes()[0]).unwrap();
    let tip = state.ledger().tip_digest();
    let refill = amount(5);
    let result = apply_budget_refill_v1(&mut state, "ETH", refill, 2, tip).unwrap();
    assert_eq!(result, TransferBudgetResultV1::Applied);
    assert_eq!(state.ledger().epoch(), 2);
    let available_after = available_capacity(&state.ledger().axes()[0]).unwrap();
    assert!(available_after.numerator() > available_before.numerator());
}

#[test]
fn skip_epoch_and_backfill_reject() {
    let mut state = consume_instant_release();
    let tip = state.ledger().tip_digest();
    let skip = apply_budget_refill_v1(&mut state, "ETH", amount(1), 3, tip).unwrap();
    assert_eq!(
        skip,
        TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::BudgetRefillRejected
        }
    );
    assert_eq!(state.ledger().epoch(), 1);
    let backfill = apply_budget_refill_v1(&mut state, "ETH", amount(1), 1, tip).unwrap();
    assert_eq!(
        backfill,
        TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::BudgetRefillRejected
        }
    );
}

#[test]
fn over_ceiling_and_non_positive_reject() {
    let mut state = consume_instant_release();
    let tip = state.ledger().tip_digest();
    let over = apply_budget_refill_v1(
        &mut state,
        "ETH",
        amount(MAX_REFILL_PER_EPOCH_V1 + 1),
        2,
        tip,
    )
    .unwrap();
    assert_eq!(
        over,
        TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::BudgetRefillRejected
        }
    );
    let zero = apply_budget_refill_v1(&mut state, "ETH", amount(0), 2, tip).unwrap();
    assert_eq!(
        zero,
        TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::BudgetRefillRejected
        }
    );
}

#[test]
fn refill_stale_tip_is_cas_conflict() {
    let mut state = consume_instant_release();
    let tip = state.ledger().tip_digest();
    let applied = apply_budget_refill_v1(&mut state, "ETH", amount(1), 2, tip).unwrap();
    assert_eq!(applied, TransferBudgetResultV1::Applied);
    // Contended tip: second refill with the pre-success tip must not apply.
    let conflict = apply_budget_refill_v1(&mut state, "ETH", amount(1), 3, tip);
    assert!(matches!(
        conflict,
        Err(statebook_settlement::SettlementTransitionErrorV1::LedgerCasConflict)
    ));
    assert_eq!(state.ledger().epoch(), 2);
}
