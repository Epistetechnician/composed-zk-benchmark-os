use statebook_core::SignedRational;

use crate::DigestV1;

use super::digest::ledger_tip_digest;
use super::error::SettlementTransitionErrorV1;
use super::types::{
    BudgetAxisV1, BudgetLedgerStateV1, DecisionReasonV1, ExternalizationRequestV1, QueueStatusV1,
    SettlementStateV1, TransferStatusV1,
};

pub struct ReservationResult {
    pub ledger: BudgetLedgerStateV1,
}

pub fn try_reserve(
    ledger: &BudgetLedgerStateV1,
    expected_tip: DigestV1,
    request: &ExternalizationRequestV1,
    amount: SignedRational,
) -> Result<ReservationResult, SettlementTransitionErrorV1> {
    if ledger.tip_digest != expected_tip {
        return Err(SettlementTransitionErrorV1::LedgerCasConflict);
    }
    let mut next = ledger.clone();
    let axis = next
        .axes
        .iter_mut()
        .find(|axis| axis.asset == request.asset())
        .ok_or(SettlementTransitionErrorV1::LedgerCasConflict)?;
    let available = available_capacity(axis)?;
    if available
        .checked_cmp(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?
        == std::cmp::Ordering::Less
    {
        return Err(SettlementTransitionErrorV1::LedgerCasConflict);
    }
    axis.reserved = axis
        .reserved
        .checked_add(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    next.tip_digest = ledger_tip_digest(&next);
    Ok(ReservationResult { ledger: next })
}

pub fn gross_reserve_linked_plan(
    ledger: &BudgetLedgerStateV1,
    expected_tip: DigestV1,
    outbound_total: SignedRational,
    asset: &str,
) -> Result<BudgetLedgerStateV1, SettlementTransitionErrorV1> {
    if ledger.tip_digest != expected_tip {
        return Err(SettlementTransitionErrorV1::LedgerCasConflict);
    }
    let mut next = ledger.clone();
    let axis = next
        .axes
        .iter_mut()
        .find(|axis| axis.asset == asset)
        .ok_or(SettlementTransitionErrorV1::LedgerCasConflict)?;
    let available = available_capacity(axis)?;
    if available
        .checked_cmp(outbound_total)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?
        == std::cmp::Ordering::Less
    {
        return Err(SettlementTransitionErrorV1::LedgerCasConflict);
    }
    axis.reserved = axis
        .reserved
        .checked_add(outbound_total)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    next.tip_digest = ledger_tip_digest(&next);
    Ok(next)
}

pub fn default_axis(asset: &str, cap: SignedRational) -> BudgetAxisV1 {
    BudgetAxisV1 {
        axis_id: format!("native-{asset}"),
        asset: asset.to_owned(),
        cap,
        reserved: SignedRational::new(0, 1).unwrap(),
        in_flight: SignedRational::new(0, 1).unwrap(),
        consumed: SignedRational::new(0, 1).unwrap(),
    }
}

pub fn available_capacity(
    axis: &BudgetAxisV1,
) -> Result<SignedRational, SettlementTransitionErrorV1> {
    axis.cap
        .checked_sub(axis.consumed)
        .and_then(|value| value.checked_sub(axis.reserved))
        .and_then(|value| value.checked_sub(axis.in_flight))
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)
}

fn axis_mut<'a>(
    ledger: &'a mut BudgetLedgerStateV1,
    asset: &str,
) -> Result<&'a mut BudgetAxisV1, SettlementTransitionErrorV1> {
    ledger
        .axes
        .iter_mut()
        .find(|axis| axis.asset == asset)
        .ok_or(SettlementTransitionErrorV1::LedgerCasConflict)
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TransferBudgetResultV1 {
    Applied,
    Rejected { reason: DecisionReasonV1 },
}

/// Reserved → Submitted: move amount from reserved to in_flight under CAS.
pub fn apply_transfer_submit_v1(
    state: &mut SettlementStateV1,
    asset: &str,
    amount: SignedRational,
    expected_tip: DigestV1,
) -> Result<TransferBudgetResultV1, SettlementTransitionErrorV1> {
    if amount.is_zero() || amount.numerator() < 0 {
        return Err(SettlementTransitionErrorV1::ArithmeticOverflow);
    }
    if state.transfer.status != TransferStatusV1::Reserved
        || state.queue.status != QueueStatusV1::None
    {
        return Err(SettlementTransitionErrorV1::InvalidQueueTransferCombination);
    }
    if state.ledger.tip_digest != expected_tip {
        return Err(SettlementTransitionErrorV1::LedgerCasConflict);
    }
    let axis = axis_mut(&mut state.ledger, asset)?;
    if axis
        .reserved
        .checked_cmp(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?
        == std::cmp::Ordering::Less
    {
        return Ok(TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::BudgetInsufficient,
        });
    }
    axis.reserved = axis
        .reserved
        .checked_sub(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    axis.in_flight = axis
        .in_flight
        .checked_add(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    state.transfer.status = TransferStatusV1::Submitted;
    state.ledger.tip_digest = ledger_tip_digest(&state.ledger);
    state.expected_ledger_tip = state.ledger.tip_digest;
    Ok(TransferBudgetResultV1::Applied)
}

/// Destination finality: in_flight → consumed; available capacity does not increase.
pub fn apply_destination_finality_v1(
    state: &mut SettlementStateV1,
    asset: &str,
    amount: SignedRational,
    expected_tip: DigestV1,
) -> Result<TransferBudgetResultV1, SettlementTransitionErrorV1> {
    if amount.is_zero() || amount.numerator() < 0 {
        return Err(SettlementTransitionErrorV1::ArithmeticOverflow);
    }
    if !matches!(
        state.transfer.status,
        TransferStatusV1::Submitted
            | TransferStatusV1::SourceObserved
            | TransferStatusV1::SourceFinalized
            | TransferStatusV1::DestinationObserved
            | TransferStatusV1::DestinationFinalized
    ) || state.queue.status != QueueStatusV1::None
    {
        return Err(SettlementTransitionErrorV1::InvalidQueueTransferCombination);
    }
    if state.ledger.tip_digest != expected_tip {
        return Err(SettlementTransitionErrorV1::LedgerCasConflict);
    }
    let axis = axis_mut(&mut state.ledger, asset)?;
    if axis
        .in_flight
        .checked_cmp(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?
        == std::cmp::Ordering::Less
    {
        return Ok(TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::BudgetInsufficient,
        });
    }
    axis.in_flight = axis
        .in_flight
        .checked_sub(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    axis.consumed = axis
        .consumed
        .checked_add(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    state.transfer.status = TransferStatusV1::Consumed;
    state.ledger.tip_digest = ledger_tip_digest(&state.ledger);
    state.expected_ledger_tip = state.ledger.tip_digest;
    Ok(TransferBudgetResultV1::Applied)
}

/// Validated ProvenNoOutflow restores capacity; ambiguous/invalid evidence leaves exposure.
pub fn apply_proven_no_outflow_v1(
    state: &mut SettlementStateV1,
    asset: &str,
    amount: SignedRational,
    expected_tip: DigestV1,
    evidence_valid: bool,
) -> Result<TransferBudgetResultV1, SettlementTransitionErrorV1> {
    if amount.is_zero() || amount.numerator() < 0 {
        return Err(SettlementTransitionErrorV1::ArithmeticOverflow);
    }
    if state.queue.status != QueueStatusV1::None {
        return Err(SettlementTransitionErrorV1::InvalidQueueTransferCombination);
    }
    if !evidence_valid {
        return Ok(TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::ProvenNoOutflowRejected,
        });
    }
    if state.ledger.tip_digest != expected_tip {
        return Err(SettlementTransitionErrorV1::LedgerCasConflict);
    }
    let axis = axis_mut(&mut state.ledger, asset)?;
    if axis
        .in_flight
        .checked_cmp(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?
        != std::cmp::Ordering::Less
    {
        axis.in_flight = axis
            .in_flight
            .checked_sub(amount)
            .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    } else if axis
        .reserved
        .checked_cmp(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?
        != std::cmp::Ordering::Less
    {
        axis.reserved = axis
            .reserved
            .checked_sub(amount)
            .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    } else {
        return Ok(TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::BudgetInsufficient,
        });
    }
    state.transfer.status = TransferStatusV1::ProvenNoOutflow;
    state.queue.status = QueueStatusV1::None;
    state.ledger.tip_digest = ledger_tip_digest(&state.ledger);
    state.expected_ledger_tip = state.ledger.tip_digest;
    Ok(TransferBudgetResultV1::Applied)
}

/// Failed-transfer rollback: release reserved (or in-flight) exposure under CAS.
pub fn apply_failed_transfer_rollback_v1(
    state: &mut SettlementStateV1,
    asset: &str,
    amount: SignedRational,
    expected_tip: DigestV1,
) -> Result<TransferBudgetResultV1, SettlementTransitionErrorV1> {
    if amount.is_zero() || amount.numerator() < 0 {
        return Ok(TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::FailedTransferRollbackRejected,
        });
    }
    if state.ledger.tip_digest != expected_tip {
        return Err(SettlementTransitionErrorV1::LedgerCasConflict);
    }
    let axis = axis_mut(&mut state.ledger, asset)?;
    if axis
        .reserved
        .checked_cmp(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?
        != std::cmp::Ordering::Less
    {
        axis.reserved = axis
            .reserved
            .checked_sub(amount)
            .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    } else if axis
        .in_flight
        .checked_cmp(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?
        != std::cmp::Ordering::Less
    {
        axis.in_flight = axis
            .in_flight
            .checked_sub(amount)
            .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    } else {
        return Ok(TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::FailedTransferRollbackRejected,
        });
    }
    state.transfer.status = TransferStatusV1::Unreserved;
    state.ledger.tip_digest = ledger_tip_digest(&state.ledger);
    state.expected_ledger_tip = state.ledger.tip_digest;
    Ok(TransferBudgetResultV1::Applied)
}

/// Sequential epoch refill: reduce consumed (restore capacity) without backfill or cap increase.
pub fn apply_budget_refill_v1(
    state: &mut SettlementStateV1,
    asset: &str,
    amount: SignedRational,
    target_epoch: u32,
    expected_tip: DigestV1,
) -> Result<TransferBudgetResultV1, SettlementTransitionErrorV1> {
    use super::bounds::MAX_REFILL_PER_EPOCH_V1;

    if amount.is_zero() || amount.numerator() < 0 {
        return Ok(TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::BudgetRefillRejected,
        });
    }
    let ceiling = SignedRational::new(MAX_REFILL_PER_EPOCH_V1, 1)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    if amount
        .checked_cmp(ceiling)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?
        == std::cmp::Ordering::Greater
    {
        return Ok(TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::BudgetRefillRejected,
        });
    }
    if target_epoch != state.ledger.epoch.saturating_add(1) {
        return Ok(TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::BudgetRefillRejected,
        });
    }
    if state.ledger.tip_digest != expected_tip {
        return Err(SettlementTransitionErrorV1::LedgerCasConflict);
    }
    let axis = axis_mut(&mut state.ledger, asset)?;
    let refill = if axis
        .consumed
        .checked_cmp(amount)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?
        == std::cmp::Ordering::Less
    {
        axis.consumed
    } else {
        amount
    };
    axis.consumed = axis
        .consumed
        .checked_sub(refill)
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
    state.ledger.epoch = target_epoch;
    state.ledger.tip_digest = ledger_tip_digest(&state.ledger);
    state.expected_ledger_tip = state.ledger.tip_digest;
    Ok(TransferBudgetResultV1::Applied)
}
