use serde_json::{json, Value};
use statebook_settlement::{
    apply_cancel_v1, apply_challenge_v1, apply_proven_no_outflow_v1, apply_transfer_submit_v1,
    decide_and_transition, intent_digest, parse_settlement_scenario_v1,
    validate_breaker_transition, BreakerStateV1, ChallengeApplyResultV1, ChallengeKindV1,
    ChallengeSubmissionV1, ClockV1, DecisionOutcomeV1, DecisionReasonV1, DecisionRecordV1,
    DigestV1, SettlementScenarioV1, TransferBudgetResultV1,
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
        CorpusCaseV1 {
            id: "td004_17_breaker_ttl_resolution",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_17_breaker_expired_no_silent_renew",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_31_challenge_valid",
            expected_outcome: DecisionOutcomeV1::Frozen,
        },
        CorpusCaseV1 {
            id: "td004_31_challenge_invalid",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_31_challenge_duplicate",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_31_challenge_censored",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_31_challenge_unavailable",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_31_evidence_expired",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_21_policy_rollback",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_21_policy_relax_rejected",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_25_cancel_race",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_25_destination_without_new_intent",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_16_proven_no_outflow_rejected",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_16_finality_no_capacity_restore",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_26_all_path_halt",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_26_canary_failed",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_02_bound_request_mismatch",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_07_future_valuation",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_07_equivocated_evidence",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_20_valuation_conflict",
            expected_outcome: DecisionOutcomeV1::Rejected,
        },
        CorpusCaseV1 {
            id: "td004_32_halted_to_normal_blocked",
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
        "td004_17_breaker_ttl_resolution" => mutate(|value| {
            value["initial_state"]["breakers"][0] = json!({
                "scope_id": "global",
                "state": "halted",
                "expires_at": 1709999999,
                "renewal_count": 3,
                "renewal_ceiling": 3
            });
        }),
        "td004_17_breaker_expired_no_silent_renew" => mutate(|value| {
            value["initial_state"]["breakers"][0] = json!({
                "scope_id": "global",
                "state": "guarded",
                "expires_at": 1709999999,
                "renewal_count": 1,
                "renewal_ceiling": 3
            });
        }),
        "td004_31_challenge_valid"
        | "td004_31_challenge_invalid"
        | "td004_31_challenge_duplicate"
        | "td004_31_challenge_censored"
        | "td004_31_challenge_unavailable" => mutate(|value| {
            value["initial_state"]["queue"]["status"] = json!("queued");
        }),
        "td004_31_evidence_expired" => mutate(|value| {
            value["initial_state"]["queue"]["status"] = json!("queued");
            value["clock"]["now"] = json!(1_710_003_700);
            value["request"]["expires_at"] = json!(1_710_003_600);
            if let Some(observations) = value["evidence_snapshot"]["observations"].as_array_mut() {
                for observation in observations {
                    observation["expires_at"] = json!(1_710_003_600);
                }
            }
        }),
        "td004_21_policy_rollback" => mutate(|value| {
            let mut active = value["policy"].clone();
            active["policy_version"] = json!(2);
            value["initial_state"]["active_policy"] = active;
            value["initial_state"]["last_policy_change_at"] = json!(1_709_900_000);
            value["policy"]["policy_version"] = json!(1);
        }),
        "td004_21_policy_relax_rejected" => mutate(|value| {
            let mut active = value["policy"].clone();
            active["assurance_tiers"]["currently_assured"]["instant_fraction"] =
                json!({ "numerator": "1", "denominator": "4" });
            value["initial_state"]["active_policy"] = active;
            value["initial_state"]["last_policy_change_at"] = json!(1_710_000_000);
            value["initial_state"]["clean_epochs"] = json!(0);
            value["policy"]["policy_version"] = json!(2);
            value["policy"]["policy_digest"] =
                json!("0000000000000000000000000000000000000000000000000000000000000002");
            value["policy"]["assurance_tiers"]["currently_assured"]["instant_fraction"] =
                json!({ "numerator": "1", "denominator": "2" });
        }),
        "td004_25_cancel_race" => mutate(|_| {}),
        "td004_25_destination_without_new_intent" => mutate(|value| {
            value["request"]["destination"] = json!("dest-replacement");
        }),
        "td004_16_proven_no_outflow_rejected" | "td004_16_finality_no_capacity_restore" => {
            mutate(|_| {})
        }
        "td004_26_all_path_halt" => mutate(|value| {
            value["initial_state"]["recovery"]["halted_paths"] = json!([
                "release-class-all",
                "profitable-close-payout",
                "liquidation-surplus",
                "lp-withdrawal",
                "collateral-withdrawal",
                "linked-exchange-outbound-leg",
                "risk-reducing-obligation-endpoint",
                "bridge",
                "administrative-transfer",
                "emergency-route",
                "transferable-queued-claim",
                "borrowing",
                "margin-reuse",
                "internal-credit-monetization"
            ]);
        }),
        "td004_26_canary_failed" => mutate(|value| {
            value["initial_state"]["recovery"]["canary_failed"] = json!(true);
        }),
        "td004_02_bound_request_mismatch" => mutate(|value| {
            if let Some(observations) = value["evidence_snapshot"]["observations"].as_array_mut() {
                for observation in observations {
                    if observation["property"] == "source_authenticity_and_freshness" {
                        observation["bound_request_id"] = json!("req-other");
                    }
                }
            }
        }),
        "td004_07_future_valuation" => mutate(|value| {
            value["valuation_profile"]["observations"][0]["observed_at"] = json!(1_710_100_000);
        }),
        "td004_07_equivocated_evidence" => mutate(|value| {
            if let Some(observations) = value["evidence_snapshot"]["observations"].as_array_mut() {
                for observation in observations {
                    observation["equivocated"] = json!(true);
                }
            }
        }),
        "td004_20_valuation_conflict" => mutate(|value| {
            value["valuation_profile"]["observations"] = json!([
                {
                    "asset": "ETH",
                    "rate": { "numerator": "2000", "denominator": "1" },
                    "observed_at": 1709999900,
                    "root_id": "oracle-a",
                    "root_class": "data"
                },
                {
                    "asset": "ETH",
                    "rate": { "numerator": "2100", "denominator": "1" },
                    "observed_at": 1709999900,
                    "root_id": "oracle-a",
                    "root_class": "data"
                }
            ]);
        }),
        "td004_32_halted_to_normal_blocked" => mutate(|_| {}),
        _ => Err(EvaluationErrorV1::Settlement(format!(
            "unknown corpus id: {id}"
        ))),
    }
}

fn challenge_kind_for_corpus(id: &str) -> Option<ChallengeKindV1> {
    match id {
        "td004_31_challenge_valid" => Some(ChallengeKindV1::Valid),
        "td004_31_challenge_invalid" => Some(ChallengeKindV1::Invalid),
        "td004_31_challenge_duplicate" => Some(ChallengeKindV1::Duplicate),
        "td004_31_challenge_censored" => Some(ChallengeKindV1::Censored),
        "td004_31_challenge_unavailable" => Some(ChallengeKindV1::Unavailable),
        _ => None,
    }
}

fn replay_challenge_corpus_case_v1(
    id: &str,
    kind: ChallengeKindV1,
) -> Result<CorpusReplayReceiptV1, EvaluationErrorV1> {
    let scenario = build_corpus_scenario_v1(id)?;
    let clock = ClockV1::new(scenario.clock().now());
    let (request, mut state, _) = scenario.into_kernel_input();
    let submission = ChallengeSubmissionV1::new(
        "chal-corpus-1",
        "watcher-root-a",
        clock.now() + 60,
        "scope-global",
        kind,
    );
    let applied = apply_challenge_v1(&mut state, &submission, &clock)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    match kind {
        ChallengeKindV1::Valid => {
            if applied != ChallengeApplyResultV1::Accepted {
                return Err(EvaluationErrorV1::Settlement(format!(
                    "{id} expected accepted challenge got {applied:?}"
                )));
            }
            let record = decide_and_transition(request, state, clock)
                .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
            Ok(receipt(id, &record))
        }
        _ => {
            if !matches!(applied, ChallengeApplyResultV1::Rejected { .. }) {
                return Err(EvaluationErrorV1::Settlement(format!(
                    "{id} expected rejected challenge got {applied:?}"
                )));
            }
            Ok(CorpusReplayReceiptV1 {
                id: id.to_owned(),
                outcome: "rejected".to_owned(),
                instant_release_is_zero: true,
                record_digest: format!("challenge-reject-{id}"),
            })
        }
    }
}

fn replay_cancel_race_corpus_case_v1(id: &str) -> Result<CorpusReplayReceiptV1, EvaluationErrorV1> {
    let scenario = parse_settlement_scenario_v1(QUEUED)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let first = run(scenario)?;
    if first.outcome() != DecisionOutcomeV1::Queued {
        return Err(EvaluationErrorV1::Settlement(format!(
            "{id} expected Queued setup got {:?}",
            first.outcome()
        )));
    }
    let scenario = parse_settlement_scenario_v1(QUEUED)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let (request, _, _) = scenario.into_kernel_input();
    let bound = first
        .next_state()
        .bound_intent_digest()
        .ok_or_else(|| EvaluationErrorV1::Settlement(format!("{id} missing bound intent")))?;
    let mut state = first.next_state().clone();
    apply_cancel_v1(&mut state, bound, DigestV1::from_raw_bytes([0x25; 32]))
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let record = decide_and_transition(request, state, ClockV1::new(1_710_100_000))
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    Ok(receipt(id, &record))
}

fn replay_destination_mismatch_corpus_case_v1(
    id: &str,
) -> Result<CorpusReplayReceiptV1, EvaluationErrorV1> {
    let scenario = build_corpus_scenario_v1(id)?;
    let (request, _, _) = scenario.clone().into_kernel_input();
    let intent = intent_digest(&request);
    let scenario = mutate(|value| {
        value["initial_state"]["queue"]["status"] = json!("queued");
        value["initial_state"]["bound_intent_digest"] = json!(intent.to_hex());
        value["initial_state"]["bound_destination"] = json!("dest-original");
        value["request"]["destination"] = json!("dest-replacement");
    })?;
    let record = run(scenario)?;
    Ok(receipt(id, &record))
}

fn replay_proven_no_outflow_reject_v1(
    id: &str,
) -> Result<CorpusReplayReceiptV1, EvaluationErrorV1> {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let first = run(scenario)?;
    let mut state = first.next_state().clone();
    let tip = state.ledger().tip_digest();
    let reserved = state.ledger().axes()[0].reserved();
    apply_transfer_submit_v1(&mut state, "ETH", reserved, tip)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let tip = state.ledger().tip_digest();
    let in_flight = state.ledger().axes()[0].in_flight();
    let result = apply_proven_no_outflow_v1(&mut state, "ETH", in_flight, tip, false)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    if result
        != (TransferBudgetResultV1::Rejected {
            reason: DecisionReasonV1::ProvenNoOutflowRejected,
        })
    {
        return Err(EvaluationErrorV1::Settlement(format!(
            "{id} expected proven-no-outflow reject got {result:?}"
        )));
    }
    if state.ledger().axes()[0].in_flight() != in_flight {
        return Err(EvaluationErrorV1::Settlement(format!(
            "{id} mutated in_flight under invalid proof"
        )));
    }
    Ok(CorpusReplayReceiptV1 {
        id: id.to_owned(),
        outcome: "rejected".to_owned(),
        instant_release_is_zero: true,
        record_digest: format!("proven-no-outflow-reject-{id}"),
    })
}

fn replay_finality_no_capacity_restore_v1(
    id: &str,
) -> Result<CorpusReplayReceiptV1, EvaluationErrorV1> {
    use statebook_settlement::{apply_destination_finality_v1, available_capacity};
    let scenario = parse_settlement_scenario_v1(IMMEDIATE)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let first = run(scenario)?;
    let mut state = first.next_state().clone();
    let tip = state.ledger().tip_digest();
    let reserved = state.ledger().axes()[0].reserved();
    apply_transfer_submit_v1(&mut state, "ETH", reserved, tip)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let available_before = available_capacity(&state.ledger().axes()[0])
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let tip = state.ledger().tip_digest();
    let in_flight = state.ledger().axes()[0].in_flight();
    apply_destination_finality_v1(&mut state, "ETH", in_flight, tip)
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    let available_after = available_capacity(&state.ledger().axes()[0])
        .map_err(|error| EvaluationErrorV1::Settlement(error.to_string()))?;
    if available_after != available_before {
        return Err(EvaluationErrorV1::Settlement(format!(
            "{id} restored capacity on destination finality"
        )));
    }
    Ok(CorpusReplayReceiptV1 {
        id: id.to_owned(),
        outcome: "rejected".to_owned(),
        instant_release_is_zero: true,
        record_digest: format!("finality-no-restore-{id}"),
    })
}

pub fn replay_corpus_case_v1(id: &str) -> Result<CorpusReplayReceiptV1, EvaluationErrorV1> {
    if let Some(kind) = challenge_kind_for_corpus(id) {
        return replay_challenge_corpus_case_v1(id, kind);
    }
    if id == "td004_25_cancel_race" {
        return replay_cancel_race_corpus_case_v1(id);
    }
    if id == "td004_25_destination_without_new_intent" {
        return replay_destination_mismatch_corpus_case_v1(id);
    }
    if id == "td004_16_proven_no_outflow_rejected" {
        return replay_proven_no_outflow_reject_v1(id);
    }
    if id == "td004_16_finality_no_capacity_restore" {
        return replay_finality_no_capacity_restore_v1(id);
    }
    if id == "td004_32_halted_to_normal_blocked" {
        if validate_breaker_transition(BreakerStateV1::Halted, BreakerStateV1::Normal) {
            return Err(EvaluationErrorV1::Settlement(
                "halted→normal must remain forbidden".into(),
            ));
        }
        return Ok(CorpusReplayReceiptV1 {
            id: id.to_owned(),
            outcome: "rejected".to_owned(),
            instant_release_is_zero: true,
            record_digest: format!("halted-to-normal-blocked-{id}"),
        });
    }
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
