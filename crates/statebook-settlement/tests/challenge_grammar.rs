use statebook_settlement::{
    apply_challenge_v1, decide_and_transition, parse_settlement_scenario_v1,
    ChallengeApplyResultV1, ChallengeKindV1, ChallengeSubmissionV1, ClockV1, DecisionOutcomeV1,
    DecisionReasonV1, QueueStatusV1, SettlementScenarioV1, TransferStatusV1,
};

const QUEUED: &[u8] = include_bytes!("fixtures/p4/queued_v1.json");
const IMMEDIATE: &[u8] = include_bytes!("fixtures/p4/immediate_v1.json");

fn mutate_fixture(
    base: &[u8],
    update: impl FnOnce(&mut serde_json::Value),
) -> SettlementScenarioV1 {
    let mut value: serde_json::Value = serde_json::from_slice(base).unwrap();
    update(&mut value);
    parse_settlement_scenario_v1(&serde_json::to_vec(&value).unwrap()).unwrap()
}

fn challenge(kind: ChallengeKindV1, id: &str, deadline: i64) -> ChallengeSubmissionV1 {
    ChallengeSubmissionV1::new(id, "watcher-root-a", deadline, "scope-global", kind)
}

#[test]
fn valid_challenge_freezes_queued_part() {
    let scenario = mutate_fixture(QUEUED, |value| {
        value["initial_state"]["queue"]["status"] = serde_json::json!("queued");
    });
    let clock = ClockV1::new(scenario.clock().now());
    let (_, mut state, _) = scenario.clone().into_kernel_input();
    let applied = apply_challenge_v1(
        &mut state,
        &challenge(ChallengeKindV1::Valid, "chal-1", clock.now() + 60),
        &clock,
    )
    .unwrap();
    assert_eq!(applied, ChallengeApplyResultV1::Accepted);
    assert_eq!(state.queue().status(), QueueStatusV1::Challenged);

    let (request, _, _) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Frozen);
    assert!(record.instant_release_amount().is_zero());
    assert_eq!(record.next_state().queue().status(), QueueStatusV1::Frozen);
}

#[test]
fn invalid_duplicate_censored_unavailable_reject_without_release() {
    let scenario = mutate_fixture(QUEUED, |value| {
        value["initial_state"]["queue"]["status"] = serde_json::json!("queued");
    });
    let clock = ClockV1::new(scenario.clock().now());
    let (_, mut state, _) = scenario.into_kernel_input();

    for (kind, reason) in [
        (ChallengeKindV1::Invalid, DecisionReasonV1::ChallengeInvalid),
        (
            ChallengeKindV1::Duplicate,
            DecisionReasonV1::ChallengeDuplicate,
        ),
        (
            ChallengeKindV1::Censored,
            DecisionReasonV1::ChallengeCensored,
        ),
        (
            ChallengeKindV1::Unavailable,
            DecisionReasonV1::ChallengeUnavailable,
        ),
    ] {
        let before = state.clone();
        let result = apply_challenge_v1(
            &mut state,
            &challenge(kind, "chal-x", clock.now() + 60),
            &clock,
        )
        .unwrap();
        assert_eq!(result, ChallengeApplyResultV1::Rejected { reason });
        assert_eq!(state, before);
        assert_eq!(state.queue().status(), QueueStatusV1::Queued);
    }
}

#[test]
fn duplicate_challenge_id_rejects_after_valid_accept() {
    let scenario = mutate_fixture(QUEUED, |value| {
        value["initial_state"]["queue"]["status"] = serde_json::json!("queued");
    });
    let clock = ClockV1::new(scenario.clock().now());
    let (_, mut state, _) = scenario.into_kernel_input();
    assert_eq!(
        apply_challenge_v1(
            &mut state,
            &challenge(ChallengeKindV1::Valid, "chal-1", clock.now() + 60),
            &clock,
        )
        .unwrap(),
        ChallengeApplyResultV1::Accepted
    );
    // Second apply against Challenged queue fails combination; reset to Queued with id retained.
    state = mutate_fixture(QUEUED, |value| {
        value["initial_state"]["queue"]["status"] = serde_json::json!("queued");
        value["initial_state"]["applied_challenge_ids"] = serde_json::json!(["chal-1"]);
    })
    .into_kernel_input()
    .1;
    let result = apply_challenge_v1(
        &mut state,
        &challenge(ChallengeKindV1::Valid, "chal-1", clock.now() + 60),
        &clock,
    )
    .unwrap();
    assert_eq!(
        result,
        ChallengeApplyResultV1::Rejected {
            reason: DecisionReasonV1::ChallengeDuplicate
        }
    );
    assert_eq!(state.queue().status(), QueueStatusV1::Queued);
}

#[test]
fn queued_expired_evidence_requires_revalidation() {
    let scenario = mutate_fixture(QUEUED, |value| {
        value["initial_state"]["queue"]["status"] = serde_json::json!("queued");
        value["clock"]["now"] = serde_json::json!(1_710_003_700);
        value["request"]["expires_at"] = serde_json::json!(1_710_003_600);
        if let Some(observations) = value["evidence_snapshot"]["observations"].as_array_mut() {
            for observation in observations {
                observation["expires_at"] = serde_json::json!(1_710_003_600);
            }
        }
    });
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record
        .reasons()
        .contains(&DecisionReasonV1::EvidenceExpired));
    assert!(record.instant_release_amount().is_zero());
    assert_eq!(
        record.next_state().queue().status(),
        QueueStatusV1::RevalidationRequired
    );
}

#[test]
fn fresh_evidence_after_revalidation_creates_new_context_not_timer_release() {
    let stale = mutate_fixture(QUEUED, |value| {
        value["initial_state"]["queue"]["status"] = serde_json::json!("queued");
        value["clock"]["now"] = serde_json::json!(1_710_003_700);
        value["request"]["expires_at"] = serde_json::json!(1_710_003_600);
        if let Some(observations) = value["evidence_snapshot"]["observations"].as_array_mut() {
            for observation in observations {
                observation["expires_at"] = serde_json::json!(1_710_003_600);
            }
        }
    });
    let (request, state, clock) = stale.into_kernel_input();
    let stale_record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(stale_record.outcome(), DecisionOutcomeV1::Rejected);
    let stale_context = stale_record.decision_context_digest();

    let fresh = mutate_fixture(QUEUED, |value| {
        value["initial_state"]["queue"]["status"] = serde_json::json!("revalidation_required");
        // Stay inside original valuation freshness window while presenting fresh evidence.
        value["clock"]["now"] = serde_json::json!(1_710_000_100);
        value["request"]["expires_at"] = serde_json::json!(1_710_003_600);
        value["request"]["nonce"] = serde_json::json!("nonce-revalidation-1");
        value["evidence_snapshot"]["nonce"] = serde_json::json!("nonce-revalidation-1");
        if let Some(observations) = value["evidence_snapshot"]["observations"].as_array_mut() {
            for observation in observations {
                observation["expires_at"] = serde_json::json!(1_710_003_600);
                observation["observed_at"] = serde_json::json!(1_710_000_050);
            }
        }
    });
    let (request, state, clock) = fresh.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_ne!(record.decision_context_digest(), stale_context);
    assert!(!record.reasons().contains(&DecisionReasonV1::QueueTimerOnly));
    assert_eq!(record.outcome(), DecisionOutcomeV1::Immediate);
    assert_eq!(
        record.next_state().transfer_state().status(),
        TransferStatusV1::Reserved
    );
    assert_eq!(record.next_state().queue().status(), QueueStatusV1::None);
}

#[test]
fn timer_alone_chain_still_zero_instant() {
    let first = mutate_fixture(QUEUED, |_| {});
    let (request, state, clock) = first.into_kernel_input();
    let queued = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(queued.outcome(), DecisionOutcomeV1::Queued);

    let again = mutate_fixture(QUEUED, |_| {});
    let (request, _, _) = again.into_kernel_input();
    let second = decide_and_transition(
        request,
        queued.next_state().clone(),
        ClockV1::new(1_710_100_000),
    )
    .unwrap();
    assert!(second.instant_release_amount().is_zero());
}

#[test]
fn immediate_fixture_unaffected_by_challenge_surface() {
    let scenario = parse_settlement_scenario_v1(IMMEDIATE).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Immediate);
}
