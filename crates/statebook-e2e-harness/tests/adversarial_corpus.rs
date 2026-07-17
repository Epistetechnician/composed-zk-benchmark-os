use statebook_e2e_harness::{
    encodable_corpus_cases_v1, replay_corpus_case_v1, replay_encodable_corpus_v1,
    replay_timer_alone_chain_v1,
};
use statebook_settlement::DecisionOutcomeV1;

#[test]
fn encodable_td004_corpus_replays_fail_closed() {
    let receipts = replay_encodable_corpus_v1().expect("corpus replay");
    assert_eq!(receipts.len(), encodable_corpus_cases_v1().len());
    for receipt in &receipts {
        assert!(
            receipt.instant_release_is_zero,
            "{} must not move value",
            receipt.id
        );
        assert_ne!(receipt.outcome, "immediate", "{} must not pass", receipt.id);
    }
}

#[test]
fn each_corpus_case_matches_expected_outcome() {
    for case in encodable_corpus_cases_v1() {
        let receipt = replay_corpus_case_v1(case.id).unwrap_or_else(|error| {
            panic!("{} failed: {error}", case.id);
        });
        let expected = format!("{:?}", case.expected_outcome).to_ascii_lowercase();
        assert_eq!(receipt.outcome, expected, "{}", case.id);
        if case.expected_outcome != DecisionOutcomeV1::Immediate {
            assert!(receipt.instant_release_is_zero, "{}", case.id);
        }
    }
}

#[test]
fn timer_alone_chain_never_releases() {
    let receipt = replay_timer_alone_chain_v1().expect("timer chain");
    assert_eq!(receipt.id, "td004_11_timer_alone");
    assert!(receipt.instant_release_is_zero);
}

#[test]
fn corpus_case_ids_are_stable() {
    let ids: Vec<&str> = encodable_corpus_cases_v1()
        .iter()
        .map(|case| case.id)
        .collect();
    assert!(ids.contains(&"td004_01_oracle_replay"));
    assert!(ids.contains(&"td004_18_model_confidence_bypass"));
    assert!(ids.contains(&"td004_26_recovery_mismatch"));
    assert_eq!(ids.len(), 40);
    assert!(ids.contains(&"td004_17_breaker_ttl_resolution"));
    assert!(ids.contains(&"td004_31_challenge_valid"));
    assert!(ids.contains(&"td004_31_evidence_expired"));
    assert!(ids.contains(&"td004_21_policy_rollback"));
    assert!(ids.contains(&"td004_25_cancel_race"));
    assert!(ids.contains(&"td004_16_proven_no_outflow_rejected"));
    assert!(ids.contains(&"td004_26_all_path_halt"));
    assert!(ids.contains(&"td004_07_future_valuation"));
    assert!(ids.contains(&"td004_32_halted_to_normal_blocked"));
    assert!(ids.contains(&"td004_30_slow_drain"));
    assert!(ids.contains(&"td004_08_split_cannot_expand_caps"));
    assert!(ids.contains(&"td004_52_refill_skip_epoch"));
    assert!(ids.contains(&"td004_20_prepared_later_fresh_transport"));
    assert!(ids.contains(&"td004_21_stale_content_fresh_transport"));
    assert!(ids.contains(&"td004_22_dual_vendor_compromised_upstream"));
    assert!(ids.contains(&"td004_32_action_oracle_valuation_blocked"));
}
