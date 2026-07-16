use crate::DigestV1;

use super::error::SettlementTransitionErrorV1;
use super::types::{
    CancelApplyResultV1, DecisionReasonV1, QueueStatusV1, SettlementStateV1, TransferStatusV1,
};

pub fn apply_cancel_v1(
    state: &mut SettlementStateV1,
    expected_bound_intent: DigestV1,
    cancellation_intent: DigestV1,
) -> Result<CancelApplyResultV1, SettlementTransitionErrorV1> {
    if state.queue.status != QueueStatusV1::Queued
        || state.transfer.status != TransferStatusV1::Unreserved
    {
        return Err(SettlementTransitionErrorV1::InvalidQueueTransferCombination);
    }
    let Some(bound) = state.bound_intent_digest else {
        return Err(SettlementTransitionErrorV1::InvalidQueueTransferCombination);
    };
    if bound != expected_bound_intent {
        return Ok(CancelApplyResultV1::Rejected {
            reason: DecisionReasonV1::IntentDigestMismatch,
        });
    }
    if cancellation_intent == bound {
        return Ok(CancelApplyResultV1::Rejected {
            reason: DecisionReasonV1::IntentDigestMismatch,
        });
    }
    state.queue.status = QueueStatusV1::Cancelled;
    state.bound_intent_digest = None;
    state.bound_destination = None;
    Ok(CancelApplyResultV1::Accepted)
}
