use super::bounds::MAX_CHALLENGES_V1;
use super::error::SettlementTransitionErrorV1;
use super::types::{
    ChallengeApplyResultV1, ChallengeKindV1, ChallengeSubmissionV1, ClockV1, DecisionReasonV1,
    QueueStatusV1, SettlementStateV1, TransferStatusV1,
};

pub fn apply_challenge_v1(
    state: &mut SettlementStateV1,
    challenge: &ChallengeSubmissionV1,
    clock: &ClockV1,
) -> Result<ChallengeApplyResultV1, SettlementTransitionErrorV1> {
    if challenge.challenge_id().is_empty()
        || challenge.trust_root_id().is_empty()
        || challenge.affected_scope_id().is_empty()
    {
        return Ok(ChallengeApplyResultV1::Rejected {
            reason: DecisionReasonV1::ChallengeInvalid,
        });
    }

    match challenge.kind() {
        ChallengeKindV1::Invalid => {
            return Ok(ChallengeApplyResultV1::Rejected {
                reason: DecisionReasonV1::ChallengeInvalid,
            });
        }
        ChallengeKindV1::Duplicate => {
            return Ok(ChallengeApplyResultV1::Rejected {
                reason: DecisionReasonV1::ChallengeDuplicate,
            });
        }
        ChallengeKindV1::Censored => {
            return Ok(ChallengeApplyResultV1::Rejected {
                reason: DecisionReasonV1::ChallengeCensored,
            });
        }
        ChallengeKindV1::Unavailable => {
            return Ok(ChallengeApplyResultV1::Rejected {
                reason: DecisionReasonV1::ChallengeUnavailable,
            });
        }
        ChallengeKindV1::Valid => {}
    }

    if state
        .applied_challenge_ids
        .contains(challenge.challenge_id())
    {
        return Ok(ChallengeApplyResultV1::Rejected {
            reason: DecisionReasonV1::ChallengeDuplicate,
        });
    }
    if state.applied_challenge_ids.len() >= MAX_CHALLENGES_V1 {
        return Err(SettlementTransitionErrorV1::ChallengeLimitExceeded);
    }
    if challenge.deadline() <= clock.now() {
        return Ok(ChallengeApplyResultV1::Rejected {
            reason: DecisionReasonV1::ChallengeUnavailable,
        });
    }
    if state.queue.status != QueueStatusV1::Queued
        || state.transfer.status != TransferStatusV1::Unreserved
    {
        return Err(SettlementTransitionErrorV1::InvalidQueueTransferCombination);
    }

    state.queue.status = QueueStatusV1::Challenged;
    state
        .applied_challenge_ids
        .insert(challenge.challenge_id().to_owned());
    Ok(ChallengeApplyResultV1::Accepted)
}

pub(crate) fn evidence_is_fresh(
    expires_at_values: impl IntoIterator<Item = i64>,
    now: i64,
) -> bool {
    expires_at_values
        .into_iter()
        .all(|expires_at| now < expires_at)
}

pub(crate) fn apply_evidence_expiry_to_state(
    state: &mut SettlementStateV1,
    expires_at_values: impl IntoIterator<Item = i64>,
    now: i64,
) {
    if state.queue.status != QueueStatusV1::Queued {
        return;
    }
    if !evidence_is_fresh(expires_at_values, now) {
        state.queue.status = QueueStatusV1::RevalidationRequired;
    }
}
