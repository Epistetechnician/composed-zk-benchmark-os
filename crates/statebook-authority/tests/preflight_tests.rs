use statebook_authority::{
    evaluate_authority_preflight_v1, AuthorityErrorV1, PreflightOutcomeV1, MAX_CONTROLLER_NAMES_V1,
};

const DENIED: &[u8] = include_bytes!("fixtures/denied_package_v1.json");

#[test]
fn denied_package_yields_denied_receipt_without_authority() {
    let (package, receipt) = evaluate_authority_preflight_v1(DENIED).expect("preflight");
    assert_eq!(receipt.outcome, PreflightOutcomeV1::Denied);
    assert!(!receipt.grants_authority);
    assert!(!package.handoff.grants_authority);
    assert!(receipt
        .adapter_nonclaims
        .iter()
        .any(|claim| claim == "no_controller_invoked"));
    assert!(receipt
        .adapter_nonclaims
        .iter()
        .any(|claim| claim == "authorized_gate_forbidden_in_this_slice"));
}

#[test]
fn incomplete_gate_yields_incomplete() {
    let mut value: serde_json::Value = serde_json::from_slice(DENIED).unwrap();
    value["production_gate"] = serde_json::json!("incomplete");
    let bytes = serde_json::to_vec(&value).unwrap();
    let (_, receipt) = evaluate_authority_preflight_v1(&bytes).unwrap();
    assert_eq!(receipt.outcome, PreflightOutcomeV1::Incomplete);
    assert!(!receipt.grants_authority);
}

#[test]
fn authorized_gate_rejects() {
    let mut value: serde_json::Value = serde_json::from_slice(DENIED).unwrap();
    value["production_gate"] = serde_json::json!("authorized");
    let bytes = serde_json::to_vec(&value).unwrap();
    assert!(matches!(
        evaluate_authority_preflight_v1(&bytes),
        Err(AuthorityErrorV1::AuthorizedGateRejected)
    ));
}

#[test]
fn missing_owner_rejects() {
    let mut value: serde_json::Value = serde_json::from_slice(DENIED).unwrap();
    value.as_object_mut().unwrap().remove("authority_owner");
    let bytes = serde_json::to_vec(&value).unwrap();
    assert!(matches!(
        evaluate_authority_preflight_v1(&bytes),
        Err(AuthorityErrorV1::MissingField(_))
    ));
}

#[test]
fn missing_maximum_loss_rejects() {
    let mut value: serde_json::Value = serde_json::from_slice(DENIED).unwrap();
    value.as_object_mut().unwrap().remove("maximum_loss");
    let bytes = serde_json::to_vec(&value).unwrap();
    assert!(matches!(
        evaluate_authority_preflight_v1(&bytes),
        Err(AuthorityErrorV1::MissingField(_))
    ));
}

#[test]
fn malformed_loss_rejects() {
    let mut value: serde_json::Value = serde_json::from_slice(DENIED).unwrap();
    value["maximum_loss"]["denominator"] = serde_json::json!("0");
    let bytes = serde_json::to_vec(&value).unwrap();
    assert!(matches!(
        evaluate_authority_preflight_v1(&bytes),
        Err(AuthorityErrorV1::MalformedExactRational)
    ));
}

#[test]
fn unknown_enum_rejects() {
    let mut value: serde_json::Value = serde_json::from_slice(DENIED).unwrap();
    value["rollback_semantics"] = serde_json::json!("explode");
    let bytes = serde_json::to_vec(&value).unwrap();
    assert!(matches!(
        evaluate_authority_preflight_v1(&bytes),
        Err(AuthorityErrorV1::UnknownEnum(_))
    ));
}

#[test]
fn handoff_grants_authority_true_rejects() {
    let mut value: serde_json::Value = serde_json::from_slice(DENIED).unwrap();
    value["handoff"]["grants_authority"] = serde_json::json!(true);
    let bytes = serde_json::to_vec(&value).unwrap();
    assert!(matches!(
        evaluate_authority_preflight_v1(&bytes),
        Err(AuthorityErrorV1::HandoffGrantsAuthority)
    ));
}

#[test]
fn noncanonical_handoff_digest_rejects() {
    let mut value: serde_json::Value = serde_json::from_slice(DENIED).unwrap();
    value["handoff"]["decision_record_digest"] = serde_json::json!("not-a-digest");
    let bytes = serde_json::to_vec(&value).unwrap();
    assert!(matches!(
        evaluate_authority_preflight_v1(&bytes),
        Err(AuthorityErrorV1::NoncanonicalDigest)
    ));
}

#[test]
fn unknown_field_rejects() {
    let mut value: serde_json::Value = serde_json::from_slice(DENIED).unwrap();
    value["extra"] = serde_json::json!("nope");
    let bytes = serde_json::to_vec(&value).unwrap();
    assert!(matches!(
        evaluate_authority_preflight_v1(&bytes),
        Err(AuthorityErrorV1::UnknownField(_))
    ));
}

#[test]
fn controller_limit_plus_one_rejects() {
    let mut value: serde_json::Value = serde_json::from_slice(DENIED).unwrap();
    value["controller_names"] = serde_json::json!((0..=MAX_CONTROLLER_NAMES_V1)
        .map(|index| format!("controller-{index}"))
        .collect::<Vec<_>>());
    let bytes = serde_json::to_vec(&value).unwrap();
    assert!(matches!(
        evaluate_authority_preflight_v1(&bytes),
        Err(AuthorityErrorV1::TooManyControllerNames)
    ));
}
