use serde_json::{json, Value};
use statebook_settlement::{
    decide_and_transition, parse_settlement_scenario_v1, ClockV1, DecisionOutcomeV1,
    DecisionRecordV1, SettlementScenarioV1,
};

use crate::error::EvaluationErrorV1;

const IMMEDIATE: &[u8] =
    include_bytes!("../../statebook-settlement/tests/fixtures/p4/immediate_v1.json");
const QUEUED: &[u8] = include_bytes!("../../statebook-settlement/tests/fixtures/p4/queued_v1.json");

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct CorpusCaseV1 {
    pub id: &'static str,
    pub expected_outcome: DecisionOutcomeV1,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CorpusReplayReceiptV1 {
    pub id: String,
    pub outcome: String,
    pub instant_release_is_zero: bool,
    pub record_digest: String,
}

fn mutate(update: impl FnOnce(&mut Value)) -> Result<SettlementScenarioV1, EvaluationErrorV1> {
    let mut value: Value = serde_json::from_slice(IMMEDIATE)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    update(&mut value);
    parse_settlement_scenario_v1(
        &serde_json::to_vec(&value)
            .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?,
    )
    .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))
}

fn run(scenario: SettlementScenarioV1) -> Result<DecisionRecordV1, EvaluationErrorV1> {
    let (request, state, clock) = scenario.into_kernel_input();
    decide_and_transition(request, state, clock)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))
}

fn receipt(id: &str, record: &DecisionRecordV1) -> CorpusReplayReceiptV1 {
    CorpusReplayReceiptV1 {
        id: id.to_owned(),
        outcome: format!("{:?}", record.outcome()).to_ascii_lowercase(),
        instant_release_is_zero: record.instant_release_amount().is_zero(),
        record_digest: record.record_digest().to_hex(),
    }
}

/// Encoded TD-004 / P4 adversarial cases expressible without kernel edits.
pub fn encodable_corpus_cases_v1() -> &'static [CorpusCaseV1] {
    &[
        CorpusCaseV1 {
            id: "td004_01_oracle_replay",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_06_empty_evidence_roots",
            expected_outcome: DecisionOutcomeV1::Quarantined,
        },
        CorpusCaseV1 {
            id: "td004_07_stale_valuation",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_08_shared_dependency_root",
            expected_outcome: DecisionOutcomeV1::Quarantined,
        },
        CorpusCaseV1 {
            id: "td004_10_reuse_finality_blocked",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_12_budget_exhausted",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_13_linked_dvp_leg_fail",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_14_false_risk_reducing",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_17_breaker_halted",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_18_model_confidence_bypass",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_22_cas_tip_mismatch",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_26_recovery_mismatch",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
    ]
}

pub fn build_corpus_scenario_v1(id: &str) -> Result<SettlementScenarioV1, EvaluationErrorV1> {
    match id {
        "td004_01_oracle_replay" => mutate(|value| {
            if let Some(observations) = value["evidence_snapshot"]["observations"].as_array_mut() {
                for observation in observations.iter_mut() {
                    observation["replayed"] = json!(true);
                }
            }
        }),
        "td004_06_empty_evidence_roots" => mutate(|value| {
            if let Some(observations) = value["evidence_snapshot"]["observations"].as_array_mut() {
                for observation in observations.iter_mut() {
                    if observation["property"] == "evidence_root_disclosure" {
                        observation["current_roots"] = json!([]);
                    }
                }
            }
        }),
        "td004_07_stale_valuation" => mutate(|value| {
            value["valuation_profile"]["observations"][0]["observed_at"] = json!(1);
        }),
        "td004_08_shared_dependency_root" => mutate(|value| {
            if let Some(observations) = value["evidence_snapshot"]["observations"].as_array_mut() {
                for observation in observations.iter_mut() {
                    if observation["property"] == "evidence_root_disclosure" {
                        observation["dependency_roots"] = json!([{
                            "root_id": "root-a",
                            "root_class": "data"
                        }]);
                    }
                }
            }
        }),
        "td004_10_reuse_finality_blocked" => mutate(|value| {
            value["request"]["reuse_finality_passed"] = json!(false);
        }),
        "td004_12_budget_exhausted" => mutate(|value| {
            // Axes parse only the cap; a tiny cap vs large request exhausts capacity.
            value["initial_state"]["ledger"]["axes"] = json!([{
                "asset": "ETH",
                "cap": { "numerator": "1", "denominator": "1" }
            }]);
            value["request"]["total_amount"] = json!({ "numerator": "10", "denominator": "1" });
        }),
        "td004_13_linked_dvp_leg_fail" => mutate(|value| {
            value["request"]["declared_release_class"] = json!("atomic_linked_exchange");
            value["request"]["linked_plan"] = json!({
                "plan_id": "plan-1",
                "leg_set_digest": "00000000000000000000000000000000000000000000000000000000000000aa",
                "primary_outbound_leg_id": "leg-out",
                "legs": [
                    {
                        "leg_id": "leg-out",
                        "direction": "outbound",
                        "asset": "ETH",
                        "amount": { "numerator": "4", "denominator": "1" },
                        "budget_axis_id": "native-ETH"
                    },
                    {
                        "leg_id": "leg-in",
                        "direction": "outbound",
                        "asset": "USD",
                        "amount": { "numerator": "8000", "denominator": "1" },
                        "budget_axis_id": "native-USD"
                    }
                ]
            });
        }),
        "td004_14_false_risk_reducing" => mutate(|value| {
            value["request"]["declared_release_class"] = json!("external_risk_reducing_obligation");
            value["request"]["total_amount"] = json!({ "numerator": "5", "denominator": "1" });
            value["request"]["obligation"] = json!({
                "obligation_id": "obl-1",
                "beneficiary": "ben-1",
                "obligation_account": "obl-acct",
                "asset": "ETH",
                "exact_amount": { "numerator": "6", "denominator": "1" },
                "deadline": 1710003600,
                "valid_until": 1710003600,
                "destination_use_restricted": true,
                "exposure_before_digest": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
                "exposure_after_digest": "0000000000000000000000000000000000000000000000000000000000000001",
                "risk_reduction_ref": "0000000000000000000000000000000000000000000000000000000000000004"
            });
        }),
        "td004_17_breaker_halted" => mutate(|value| {
            value["initial_state"]["breakers"][0]["state"] = json!("halted");
        }),
        "td004_18_model_confidence_bypass" => mutate(|value| {
            value["request"]["gate_overrides"] = json!({ "calculation_valid": false });
        }),
        "td004_22_cas_tip_mismatch" => mutate(|value| {
            value["initial_state"]["expected_ledger_tip"] =
                json!("9999999999999999999999999999999999999999999999999999999999999999");
        }),
        "td004_26_recovery_mismatch" => mutate(|value| {
            value["initial_state"]["recovery"]["reconciliation_mismatch"] = json!(true);
        }),
        _ => Err(EvaluationErrorV1::Settlement(format!(
            "unknown corpus id: {id}"
        ))),
    }
}

pub fn replay_corpus_case_v1(id: &str) -> Result<CorpusReplayReceiptV1, EvaluationErrorV1> {
    let scenario = build_corpus_scenario_v1(id)?;
    let record = run(scenario)?;
    Ok(receipt(id, &record))
}

pub fn replay_encodable_corpus_v1() -> Result<Vec<CorpusReplayReceiptV1>, EvaluationErrorV1> {
    let mut out = Vec::new();
    for case in encodable_corpus_cases_v1() {
        let replayed = replay_corpus_case_v1(case.id)?;
        if format!("{:?}", case.expected_outcome).to_ascii_lowercase() != replayed.outcome {
            return Err(EvaluationErrorV1::Settlement(format!(
                "{} expected {:?} got {}",
                case.id, case.expected_outcome, replayed.outcome
            )));
        }
        if case.expected_outcome != DecisionOutcomeV1::Immediate
            && !replayed.instant_release_is_zero
        {
            return Err(EvaluationErrorV1::Settlement(format!(
                "{} emitted nonzero instant release",
                case.id
            )));
        }
        out.push(replayed);
    }
    Ok(out)
}

/// TD-004 #11: timer passage alone never releases a queued part.
pub fn replay_timer_alone_chain_v1() -> Result<CorpusReplayReceiptV1, EvaluationErrorV1> {
    let scenario = parse_settlement_scenario_v1(QUEUED)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let first = run(scenario)?;
    if first.outcome() != DecisionOutcomeV1::Queued {
        return Err(EvaluationErrorV1::Settlement(format!(
            "queued fixture expected Queued got {:?}",
            first.outcome()
        )));
    }
    let scenario = parse_settlement_scenario_v1(QUEUED)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let (request, _, _) = scenario.into_kernel_input();
    let second = decide_and_transition(
        request,
        first.next_state().clone(),
        ClockV1::new(1710100000),
    )
    .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    if !second.instant_release_amount().is_zero() {
        return Err(EvaluationErrorV1::Settlement(
            "timer-alone chain released value".into(),
        ));
    }
    Ok(receipt("td004_11_timer_alone", &second))
}
