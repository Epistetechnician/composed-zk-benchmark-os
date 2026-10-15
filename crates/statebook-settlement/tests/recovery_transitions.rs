use statebook_settlement::{
    apply_recovery_canary_v1, apply_recovery_halt_all_v1, apply_recovery_reconciliation_v1,
    apply_recovery_reopen_v1, decide_and_transition, parse_settlement_scenario_v1,
    DecisionOutcomeV1, DecisionReasonV1, RecoveryApplyResultV1, RECOVERY_PATH_COUNT_V1,
};

const IMMEDIATE: &[u8] = include_bytes!("fixtures/p4/immediate_v1.json");

#[test]
fn all_path_halt_rejects_zero_instant() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, mut state, clock) = scenario.into_kernel_input();
    assert_eq!(
        apply_recovery_halt_all_v1(&mut state),
        RecoveryApplyResultV1::Applied
    );
    assert_eq!(
        state.recovery().halted_paths().len(),
        RECOVERY_PATH_COUNT_V1
    );
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record.reasons().contains(&DecisionReasonV1::RecoveryFailed));
    assert!(record.instant_release_amount().is_zero());
}

#[test]
fn canary_failed_rejects() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, mut state, clock) = scenario.into_kernel_input();
    apply_recovery_canary_v1(&mut state, false);
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record.reasons().contains(&DecisionReasonV1::RecoveryFailed));
}

#[test]
fn reopen_rejected_while_mismatch_or_canary_failed() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (_, mut state, _) = scenario.into_kernel_input();
    apply_recovery_halt_all_v1(&mut state);
    apply_recovery_reconciliation_v1(&mut state, true);
    assert_eq!(
        apply_recovery_reopen_v1(&mut state),
        RecoveryApplyResultV1::Rejected
    );
    assert_eq!(
        state.recovery().halted_paths().len(),
        RECOVERY_PATH_COUNT_V1
    );

    apply_recovery_reconciliation_v1(&mut state, false);
    apply_recovery_canary_v1(&mut state, false);
    assert_eq!(
        apply_recovery_reopen_v1(&mut state),
        RecoveryApplyResultV1::Rejected
    );
    assert!(!state.recovery().halted_paths().is_empty());
}

#[test]
fn reopen_clears_halt_when_clean() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, mut state, clock) = scenario.into_kernel_input();
    apply_recovery_halt_all_v1(&mut state);
    apply_recovery_reconciliation_v1(&mut state, false);
    apply_recovery_canary_v1(&mut state, true);
    assert_eq!(
        apply_recovery_reopen_v1(&mut state),
        RecoveryApplyResultV1::Applied
    );
    assert!(state.recovery().halted_paths().is_empty());
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Immediate);
}
