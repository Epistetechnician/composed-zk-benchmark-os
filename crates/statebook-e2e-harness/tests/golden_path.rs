use statebook_e2e_harness::{
    reject_unbound_authority_statement_v1, run_hermetic_golden_path_v1, EvaluationErrorV1,
    EVALUATION_RECEIPT_SCHEMA_V1, GOLDEN_PATH_PROFILE_V1,
};
use statebook_settlement::{
    decide_and_transition, parse_settlement_scenario_v1, DecisionOutcomeV1,
};
use tempfile::tempdir;

const P4_IMMEDIATE: &[u8] =
    include_bytes!("../../statebook-settlement/tests/fixtures/p4/immediate_v1.json");
const P4_REJECTED: &[u8] =
    include_bytes!("../../statebook-settlement/tests/fixtures/p4/rejected_gate_fail_v1.json");

#[test]
fn hermetic_p1_to_p7_golden_path_binds_digests() {
    let dir = tempdir().unwrap();
    let receipt = run_hermetic_golden_path_v1(dir.path()).expect("golden path");
    assert_eq!(receipt.schema_version, EVALUATION_RECEIPT_SCHEMA_V1);
    assert_eq!(receipt.profile_id, GOLDEN_PATH_PROFILE_V1);
    assert_eq!(receipt.decision_outcome, "immediate");
    assert!(!receipt.handoff_grants_authority);
    assert!(!receipt.grants_execution_authority);
    assert_eq!(receipt.authority_overlay_status, "recognized_in_fixture");
    assert_eq!(
        receipt.validated_contract_digest,
        "7634410968adb9b56c62f213de7956796f9f3f62b102d4f6efe7f45d86858788"
    );
    assert_eq!(
        receipt.payoff_domain_digest,
        "67cb8e1807cd3e619f73d569f70de494ef60610f4d44acea236b0ee006e45e6a"
    );
    assert!(receipt
        .nonclaims
        .iter()
        .any(|claim| claim == "no_value_movement"));
    assert!(receipt
        .nonclaims
        .iter()
        .any(|claim| claim == "p7_legal_ops_gate_unsatisfied"));
}

#[test]
fn p4_hard_gate_failure_yields_zero_instant_release() {
    let scenario = parse_settlement_scenario_v1(P4_REJECTED).unwrap();
    let (request, state, clock) = scenario.into_kernel_input();
    let record = decide_and_transition(request, state, clock).unwrap();
    assert_eq!(record.outcome(), DecisionOutcomeV1::Rejected);
    assert!(record.instant_release_amount().is_zero());
}

#[test]
fn p5_readback_tamper_rejects_after_golden_materialize() {
    let dir = tempdir().unwrap();
    run_hermetic_golden_path_v1(dir.path()).unwrap();
    std::fs::write(dir.path().join("records/decision.json"), b"{}\n").unwrap();
    assert!(statebook_report::readback_validate_audit_bundle_v1(dir.path()).is_err());
}

#[test]
fn p7_execution_authority_grant_rejects() {
    let mut registry = statebook_authority::AuthorityRegistryV1::new();
    let statement = serde_json::json!({
        "schema_version": "statebook-p7-authority-statement:v1",
        "profile_id": "synthetic-clearing-authority-v1",
        "authority_namespace": "synthetic.clearing.authority.v1",
        "authority_id": "synthetic-clearing-officer-v1",
        "statement_revision": "bad-rev",
        "eligible_account": "acct-fixture-001",
        "model_id": "synthetic-margin-model-v1",
        "model_version": "1",
        "model_digest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "margin_rule_id": "synthetic-margin-rule-v1",
        "jurisdiction": "synthetic-jurisdiction-v1",
        "subject_terms_digest": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "economic_residual_digest": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
        "recognized_numerator": "1",
        "recognized_denominator": "1",
        "issued_at": 1000,
        "expires_at": 2000,
        "grants_execution_authority": true,
        "limitations": ["synthetic-non-authoritative"]
    });
    let bytes = serde_json::to_vec(&statement).unwrap();
    assert!(matches!(
        statebook_authority::attach_authority_statement_v1(&bytes, &mut registry, 1500),
        Err(statebook_authority::AuthorityErrorV1::ExecutionAuthorityGrantForbidden)
    ));
}

#[test]
fn unbound_authority_digest_is_rejected_by_harness() {
    assert!(matches!(
        reject_unbound_authority_statement_v1(
            "7634410968adb9b56c62f213de7956796f9f3f62b102d4f6efe7f45d86858788",
            "0000000000000000000000000000000000000000000000000000000000000001",
        ),
        Err(EvaluationErrorV1::DigestBindingMismatch(_))
    ));
}

#[test]
fn immediate_fixture_still_parses_for_regression_anchor() {
    let scenario = parse_settlement_scenario_v1(P4_IMMEDIATE).unwrap();
    assert_eq!(scenario.clock().now(), scenario.clock().now());
}
