use statebook_authority::{
    attach_authority_statement_v1, evaluate_attached_statement_v1, AuthorityErrorV1,
    AuthorityRegistryV1, CapitalOverlayStatusV1, StatementStatusV1,
    MAX_LIMITATION_OR_NONCLAIM_COUNT_V1, SYNTHETIC_AUTHORITY_PROFILE_V1,
};

const STATEMENT: &[u8] = include_bytes!("fixtures/authority_statement_v1.json");

#[test]
fn attach_roundtrip_preserves_economic_residual_and_nonclaims() {
    let mut registry = AuthorityRegistryV1::new();
    let receipt = attach_authority_statement_v1(STATEMENT, &mut registry, 1500).expect("attach");
    assert_eq!(receipt.profile_id, SYNTHETIC_AUTHORITY_PROFILE_V1);
    assert!(!receipt.grants_execution_authority);
    assert_eq!(
        receipt.economic_residual_digest,
        "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
    );
    assert_eq!(
        receipt.capital_overlay.status,
        CapitalOverlayStatusV1::RecognizedInFixture
    );
    assert!(receipt
        .adapter_nonclaims
        .iter()
        .any(|claim| claim == "does_not_grant_execution_authority"));
    assert!(receipt
        .legal_ops_gate_deferred
        .iter()
        .any(|gate| gate == "live-execution-custody-signing-pause-margin-settlement-deferred"));
}

#[test]
fn revoke_changes_capital_overlay_only() {
    let mut registry = AuthorityRegistryV1::new();
    let receipt = attach_authority_statement_v1(STATEMENT, &mut registry, 1500).unwrap();
    let residual_before = receipt.economic_residual_digest.clone();
    let statement_before = receipt.statement_digest.clone();
    let revoked = registry
        .revoke(
            &receipt.authority_namespace,
            &receipt.authority_id,
            &receipt.statement_revision,
        )
        .unwrap();
    assert_eq!(revoked.status, StatementStatusV1::Revoked);
    assert_eq!(revoked.statement_digest, statement_before);
    assert_eq!(revoked.economic_residual_digest, residual_before);
    let overlay = evaluate_attached_statement_v1(
        &registry,
        &receipt.authority_namespace,
        &receipt.authority_id,
        &receipt.statement_revision,
        1500,
    )
    .unwrap();
    assert_eq!(
        overlay.status,
        CapitalOverlayStatusV1::NotRecognizedInFixture
    );
    assert_eq!(overlay.economic_residual_digest, residual_before);
}

#[test]
fn expired_evaluation_is_not_recognized() {
    let mut registry = AuthorityRegistryV1::new();
    let receipt = attach_authority_statement_v1(STATEMENT, &mut registry, 1500).unwrap();
    let overlay = evaluate_attached_statement_v1(
        &registry,
        &receipt.authority_namespace,
        &receipt.authority_id,
        &receipt.statement_revision,
        2000,
    )
    .unwrap();
    assert_eq!(
        overlay.status,
        CapitalOverlayStatusV1::NotRecognizedInFixture
    );
    assert_eq!(
        overlay.economic_residual_digest,
        receipt.economic_residual_digest
    );
}

#[test]
fn grants_execution_authority_true_rejects() {
    let mut registry = AuthorityRegistryV1::new();
    let mut statement: serde_json::Value = serde_json::from_slice(STATEMENT).unwrap();
    statement["grants_execution_authority"] = serde_json::json!(true);
    let bytes = serde_json::to_vec(&statement).unwrap();
    assert!(matches!(
        attach_authority_statement_v1(&bytes, &mut registry, 1500),
        Err(AuthorityErrorV1::ExecutionAuthorityGrantForbidden)
    ));
}

#[test]
fn unknown_profile_rejects() {
    let mut registry = AuthorityRegistryV1::new();
    let mut statement: serde_json::Value = serde_json::from_slice(STATEMENT).unwrap();
    statement["profile_id"] = serde_json::json!("unknown-profile");
    let bytes = serde_json::to_vec(&statement).unwrap();
    assert!(matches!(
        attach_authority_statement_v1(&bytes, &mut registry, 1500),
        Err(AuthorityErrorV1::UnknownProfile(_))
    ));
}

#[test]
fn unknown_schema_rejects() {
    let mut registry = AuthorityRegistryV1::new();
    let mut statement: serde_json::Value = serde_json::from_slice(STATEMENT).unwrap();
    statement["schema_version"] = serde_json::json!("statebook-p7-authority-statement:v0");
    let bytes = serde_json::to_vec(&statement).unwrap();
    assert!(matches!(
        attach_authority_statement_v1(&bytes, &mut registry, 1500),
        Err(AuthorityErrorV1::UnknownSchemaVersion)
    ));
}

#[test]
fn missing_field_rejects() {
    let mut registry = AuthorityRegistryV1::new();
    let mut statement: serde_json::Value = serde_json::from_slice(STATEMENT).unwrap();
    statement.as_object_mut().unwrap().remove("expires_at");
    let bytes = serde_json::to_vec(&statement).unwrap();
    assert!(matches!(
        attach_authority_statement_v1(&bytes, &mut registry, 1500),
        Err(AuthorityErrorV1::MissingField(_))
    ));
}

#[test]
fn unknown_field_rejects() {
    let mut registry = AuthorityRegistryV1::new();
    let mut statement: serde_json::Value = serde_json::from_slice(STATEMENT).unwrap();
    statement["extra"] = serde_json::json!("nope");
    let bytes = serde_json::to_vec(&statement).unwrap();
    assert!(matches!(
        attach_authority_statement_v1(&bytes, &mut registry, 1500),
        Err(AuthorityErrorV1::UnknownField(_))
    ));
}

#[test]
fn invalid_validity_window_rejects() {
    let mut registry = AuthorityRegistryV1::new();
    let mut statement: serde_json::Value = serde_json::from_slice(STATEMENT).unwrap();
    statement["issued_at"] = serde_json::json!(2000);
    statement["expires_at"] = serde_json::json!(2000);
    let bytes = serde_json::to_vec(&statement).unwrap();
    assert!(matches!(
        attach_authority_statement_v1(&bytes, &mut registry, 1500),
        Err(AuthorityErrorV1::InvalidValidityWindow)
    ));
}

#[test]
fn limitation_limit_plus_one_rejects() {
    let mut registry = AuthorityRegistryV1::new();
    let mut statement: serde_json::Value = serde_json::from_slice(STATEMENT).unwrap();
    statement["limitations"] = serde_json::json!((0..=MAX_LIMITATION_OR_NONCLAIM_COUNT_V1)
        .map(|index| format!("limit-{index}"))
        .collect::<Vec<_>>());
    let bytes = serde_json::to_vec(&statement).unwrap();
    assert!(matches!(
        attach_authority_statement_v1(&bytes, &mut registry, 1500),
        Err(AuthorityErrorV1::TooManyLimitationsOrNonclaims)
    ));
}

#[test]
fn partial_recognition_uses_partial_status() {
    let mut registry = AuthorityRegistryV1::new();
    let mut statement: serde_json::Value = serde_json::from_slice(STATEMENT).unwrap();
    statement["recognized_numerator"] = serde_json::json!("1");
    statement["recognized_denominator"] = serde_json::json!("2");
    let bytes = serde_json::to_vec(&statement).unwrap();
    let receipt = attach_authority_statement_v1(&bytes, &mut registry, 1500).unwrap();
    assert_eq!(
        receipt.capital_overlay.status,
        CapitalOverlayStatusV1::PartiallyRecognizedInFixture
    );
}
