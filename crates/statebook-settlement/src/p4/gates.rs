use crate::{AssurancePropertyV1, AssuranceVerdictV1};

use super::types::{
    DecisionReasonV1, EvidenceObservationV1, EvidenceSnapshotV1, ExternalizationRequestV1,
    FinancialBasisKindV1, GateOverridesV1, ReleaseClassV1, SettlementStateV1,
};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct GateResult {
    pub passed: bool,
    pub reason: Option<DecisionReasonV1>,
    pub quarantine: bool,
}

impl GateResult {
    fn pass() -> Self {
        Self {
            passed: true,
            reason: None,
            quarantine: false,
        }
    }

    fn fail(reason: DecisionReasonV1, quarantine: bool) -> Self {
        Self {
            passed: false,
            reason: Some(reason),
            quarantine,
        }
    }
}

fn observation_for(
    snapshot: &EvidenceSnapshotV1,
    property: AssurancePropertyV1,
) -> Option<&EvidenceObservationV1> {
    snapshot
        .observations()
        .iter()
        .find(|observation| observation.property == property)
}

fn verdict_passes(verdict: AssuranceVerdictV1) -> bool {
    verdict == AssuranceVerdictV1::Pass
}

fn gate_from_observation(
    observation: Option<&EvidenceObservationV1>,
    fail_reason: DecisionReasonV1,
) -> GateResult {
    match observation {
        Some(value) if verdict_passes(value.verdict) && !value.replayed && !value.equivocated => {
            GateResult::pass()
        }
        Some(value) if value.verdict == AssuranceVerdictV1::Unknown => {
            GateResult::fail(fail_reason, true)
        }
        _ => GateResult::fail(fail_reason, false),
    }
}

pub fn evaluate_hard_gates(
    request: &ExternalizationRequestV1,
    evidence: &EvidenceSnapshotV1,
    state: &SettlementStateV1,
    release_class: ReleaseClassV1,
    overrides: &GateOverridesV1,
    now: i64,
) -> Vec<GateResult> {
    use super::bounds::MAX_EVIDENCE_CONTENT_AGE_SECONDS_V1;

    let mut results = Vec::with_capacity(12);

    results.push(if overrides.action_authorized == Some(false) {
        GateResult::fail(DecisionReasonV1::GateActionAuthorization, false)
    } else {
        gate_from_observation(
            observation_for(evidence, AssurancePropertyV1::ActionAuthorization),
            DecisionReasonV1::GateActionAuthorization,
        )
    });

    results.push(if overrides.source_authentic == Some(false) {
        GateResult::fail(DecisionReasonV1::GateSourceAuthenticity, false)
    } else {
        let observation = observation_for(
            evidence,
            AssurancePropertyV1::SourceAuthenticityAndFreshness,
        );
        match observation {
            Some(value) if value.prepared_earlier => {
                GateResult::fail(DecisionReasonV1::GatePreparedEarlierReuse, false)
            }
            Some(value)
                if value.content_observed_at > now
                    || now.saturating_sub(value.content_observed_at)
                        > MAX_EVIDENCE_CONTENT_AGE_SECONDS_V1 =>
            {
                GateResult::fail(DecisionReasonV1::GateSourceContentStale, false)
            }
            Some(value)
                if verdict_passes(value.verdict)
                    && value.bound_request_id == request.request_id()
                    && !value.replayed
                    && !value.equivocated =>
            {
                GateResult::pass()
            }
            Some(value) if value.verdict == AssuranceVerdictV1::Unknown => {
                GateResult::fail(DecisionReasonV1::GateSourceAuthenticity, true)
            }
            _ => GateResult::fail(DecisionReasonV1::GateSourceAuthenticity, false),
        }
    });

    results.push(if overrides.calculation_valid == Some(false) {
        GateResult::fail(DecisionReasonV1::GateCalculationIntegrity, false)
    } else {
        gate_from_observation(
            observation_for(evidence, AssurancePropertyV1::CalculationIntegrity),
            DecisionReasonV1::GateCalculationIntegrity,
        )
    });

    results.push(if overrides.transition_valid == Some(false) {
        GateResult::fail(DecisionReasonV1::GateStateTransitionIntegrity, false)
    } else {
        gate_from_observation(
            observation_for(evidence, AssurancePropertyV1::StateTransitionIntegrity),
            DecisionReasonV1::GateStateTransitionIntegrity,
        )
    });

    results.push(if overrides.solvency_supported == Some(false) {
        GateResult::fail(DecisionReasonV1::GateSolvencySupport, false)
    } else {
        gate_from_observation(
            observation_for(
                evidence,
                AssurancePropertyV1::SolvencyAndLiquidResourceSupport,
            ),
            DecisionReasonV1::GateSolvencySupport,
        )
    });

    results.push(if overrides.destination_allowed == Some(false) {
        GateResult::fail(DecisionReasonV1::GateDestinationRoute, false)
    } else {
        gate_from_observation(
            observation_for(evidence, AssurancePropertyV1::DestinationAndRoutePolicy),
            DecisionReasonV1::GateDestinationRoute,
        )
    });

    results.push(
        if overrides.anomaly_clear == Some(false) || state.recovery().reconciliation_mismatch {
            GateResult::fail(DecisionReasonV1::GateAnomalyEmergency, false)
        } else {
            gate_from_observation(
                observation_for(evidence, AssurancePropertyV1::AnomalyAndEmergencyClearance),
                DecisionReasonV1::GateAnomalyEmergency,
            )
        },
    );

    results.push(if overrides.evidence_independent == Some(false) {
        GateResult::fail(DecisionReasonV1::GateEvidenceIndependence, true)
    } else {
        super::assurance::evaluate_independence(evidence)
            .map(|passed| {
                if passed {
                    GateResult::pass()
                } else {
                    GateResult::fail(DecisionReasonV1::GateEvidenceIndependence, true)
                }
            })
            .unwrap_or_else(|| GateResult::fail(DecisionReasonV1::GateEvidenceIndependence, true))
    });

    results.push(if overrides.financial_basis_valid == Some(false) {
        GateResult::fail(DecisionReasonV1::GateFinancialBasisBinding, false)
    } else if request.financial_basis().kind() == FinancialBasisKindV1::ContractDerived {
        let basis = request.financial_basis();
        if basis.composition_digest().is_none() || basis.analysis_subject_digest().is_none() {
            GateResult::fail(DecisionReasonV1::GateFinancialBasisBinding, false)
        } else {
            gate_from_observation(
                observation_for(evidence, AssurancePropertyV1::FinancialBasisBinding),
                DecisionReasonV1::GateFinancialBasisBinding,
            )
        }
    } else {
        GateResult::pass()
    });

    results.push(
        if overrides.reuse_finality == Some(false) || !request.reuse_finality_passed() {
            GateResult::fail(DecisionReasonV1::GateReuseFinality, false)
        } else {
            GateResult::pass()
        },
    );

    results.push(
        if release_class == ReleaseClassV1::ExternalRiskReducingObligation {
            if overrides.obligation_valid == Some(false) {
                GateResult::fail(DecisionReasonV1::GateRiskReducingObligation, false)
            } else {
                super::obligation::validate_obligation(request, evidence)
            }
        } else {
            GateResult::pass()
        },
    );

    results.push(if release_class == ReleaseClassV1::AtomicLinkedExchange {
        if overrides.linked_plan_valid == Some(false) {
            GateResult::fail(DecisionReasonV1::GateLinkedExchangePlan, false)
        } else {
            super::linked_plan::validate_linked_plan(request)
        }
    } else {
        GateResult::pass()
    });

    results
}
