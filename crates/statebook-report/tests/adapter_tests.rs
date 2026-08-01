use statebook_report::{
    handoff_decision_record_v1, map_fixture_observation_v1, map_hsai_fixture_envelope_v1,
    parse_fixture_adapter_input_v1, DecisionHandoffInputV1,
};

const FIXTURE_ADAPTER: &[u8] = include_bytes!("fixtures/fixture_adapter_v1.json");
const HSAI_FIXTURE: &[u8] = include_bytes!("fixtures/hsai_fixture_envelope_v1.json");

#[test]
fn fixture_adapter_unknown_preservation() {
    let input = parse_fixture_adapter_input_v1(FIXTURE_ADAPTER).expect("parse");
    let mapped = map_fixture_observation_v1(&input).expect("map");
    assert_eq!(mapped.unknown_facts, input.unknown_facts);
    assert!(mapped
        .adapter_nonclaims
        .iter()
        .any(|claim| claim.contains("does_not_prove")));
}

#[test]
fn hsai_fixture_envelope_mapping_nonclaims_and_unknown() {
    let mapped = map_hsai_fixture_envelope_v1(HSAI_FIXTURE).expect("map");
    assert_eq!(mapped.evidence_maturity, "provisional");
    assert_eq!(
        mapped.unknown_facts,
        vec!["finality_status", "legal_classification"]
    );
    assert!(mapped
        .adapter_nonclaims
        .iter()
        .any(|claim| claim == "evidence_maturity_not_financial_expiry"));
    assert!(mapped
        .adapter_nonclaims
        .iter()
        .any(|claim| claim == "does_not_prove_price_or_solvency"));
}

#[test]
fn handoff_grants_authority_false() {
    let json = r#"{
        "record_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "intent_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "decision_context_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "outcome": "immediate"
    }"#;
    let envelope =
        handoff_decision_record_v1(&DecisionHandoffInputV1::DecisionJson(json)).expect("handoff");
    assert!(!envelope.grants_authority);
    assert!(envelope
        .adapter_nonclaims
        .iter()
        .any(|claim| claim == "grants_authority_false"));
}

#[test]
fn digest_bound_handoff_also_rejects_authority() {
    let envelope = handoff_decision_record_v1(&DecisionHandoffInputV1::DigestBound {
        decision_record_digest: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        intent_digest: "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        decision_context_digest: "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        outcome: "queued",
    })
    .expect("handoff");
    assert!(!envelope.grants_authority);
}
