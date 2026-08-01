use statebook_core::SignedRational;

use crate::DigestV1;

use super::digest::ledger_tip_digest;
use super::error::SettlementTransitionErrorV1;
use super::types::{BudgetAxisV1, BudgetLedgerStateV1, ExternalizationRequestV1};

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
    let available = axis
        .cap
        .checked_sub(axis.reserved)
        .and_then(|value| value.checked_sub(axis.in_flight))
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
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
    let available = axis
        .cap
        .checked_sub(axis.reserved)
        .and_then(|value| value.checked_sub(axis.in_flight))
        .map_err(|_| SettlementTransitionErrorV1::ArithmeticOverflow)?;
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
