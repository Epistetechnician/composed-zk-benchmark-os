use super::gates::GateResult;
use super::types::{DecisionReasonV1, EvidenceSnapshotV1, ExternalizationRequestV1};

pub fn validate_obligation(
    request: &ExternalizationRequestV1,
    _evidence: &EvidenceSnapshotV1,
) -> GateResult {
    let Some(obligation) = request.obligation() else {
        return GateResult {
            passed: false,
            reason: Some(DecisionReasonV1::GateRiskReducingObligation),
            quarantine: false,
        };
    };
    if obligation.exact_amount != request.total_amount() {
        return GateResult {
            passed: false,
            reason: Some(DecisionReasonV1::GateRiskReducingObligation),
            quarantine: false,
        };
    }
    if !obligation.destination_use_restricted {
        return GateResult {
            passed: false,
            reason: Some(DecisionReasonV1::GateRiskReducingObligation),
            quarantine: false,
        };
    }
    if obligation.exposure_before_digest == obligation.exposure_after_digest {
        return GateResult {
            passed: false,
            reason: Some(DecisionReasonV1::GateRiskReducingObligation),
            quarantine: false,
        };
    }
    if obligation.exposure_after_digest.as_bytes() >= obligation.exposure_before_digest.as_bytes() {
        return GateResult {
            passed: false,
            reason: Some(DecisionReasonV1::GateRiskReducingObligation),
            quarantine: false,
        };
    }
    GateResult {
        passed: true,
        reason: None,
        quarantine: false,
    }
}
