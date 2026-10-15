use std::collections::BTreeSet;

use crate::RecoveryPathProfileV1;

use super::types::SettlementStateV1;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum RecoveryApplyResultV1 {
    Applied,
    Rejected,
}

fn required_paths() -> BTreeSet<String> {
    RecoveryPathProfileV1::statebook_externalization_v1()
        .required_path_ids()
        .clone()
}

/// Halt every frozen externalization path in the fourteen-path inventory.
pub fn apply_recovery_halt_all_v1(state: &mut SettlementStateV1) -> RecoveryApplyResultV1 {
    state.recovery.halted_paths = required_paths();
    RecoveryApplyResultV1::Applied
}

pub fn apply_recovery_reconciliation_v1(
    state: &mut SettlementStateV1,
    mismatch: bool,
) -> RecoveryApplyResultV1 {
    state.recovery.reconciliation_mismatch = mismatch;
    RecoveryApplyResultV1::Applied
}

pub fn apply_recovery_canary_v1(
    state: &mut SettlementStateV1,
    canary_passed: bool,
) -> RecoveryApplyResultV1 {
    state.recovery.canary_failed = !canary_passed;
    RecoveryApplyResultV1::Applied
}

/// Reopen clears the halt inventory only when reconciliation is clean and canary passed.
pub fn apply_recovery_reopen_v1(state: &mut SettlementStateV1) -> RecoveryApplyResultV1 {
    if state.recovery.reconciliation_mismatch || state.recovery.canary_failed {
        return RecoveryApplyResultV1::Rejected;
    }
    state.recovery.halted_paths.clear();
    RecoveryApplyResultV1::Applied
}

pub(crate) fn recovery_blocks_release(state: &SettlementStateV1) -> bool {
    state.recovery.reconciliation_mismatch
        || state.recovery.canary_failed
        || !state.recovery.halted_paths.is_empty()
}
