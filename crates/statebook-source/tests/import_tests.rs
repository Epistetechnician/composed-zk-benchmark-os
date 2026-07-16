use statebook_core::parse_source_contract_v1;
use statebook_source::{
    import_captured_terms_v1, EvidenceClassV1, SourceErrorV1, SourceRegistryV1,
    MAX_CLAIM_OR_LIMITATION_COUNT_V1, SYNTHETIC_CLEARING_PROFILE_V1,
};

const ENVELOPE: &[u8] = include_bytes!("fixtures/captured_envelope_v1.json");
const TERMS: &[u8] = include_bytes!("fixtures/terms_payload_v1.json");

#[test]
fn captured_import_roundtrip_parses_with_p1() {
    let mut registry = SourceRegistryV1::new();
    let receipt = import_captured_terms_v1(ENVELOPE, TERMS, &mut registry).expect("import");
    assert_eq!(receipt.profile_id, SYNTHETIC_CLEARING_PROFILE_V1);
    assert_eq!(receipt.evidence_class, EvidenceClassV1::CapturedReplay);
    assert!(receipt
        .adapter_nonclaims
        .iter()
        .any(|claim| claim == "does_not_grant_authority"));
    assert_eq!(receipt.unknown_facts, vec!["legal-classification"]);
    let parsed = parse_source_contract_v1(TERMS).expect("p1 parse");
    assert_eq!(
        parsed.source_document_digest().to_hex(),
        receipt.content_sha256
    );
}

#[test]
fn content_digest_mismatch_rejects() {
    let mut registry = SourceRegistryV1::new();
    let mut envelope: serde_json::Value = serde_json::from_slice(ENVELOPE).unwrap();
    envelope["content_sha256"] =
        serde_json::json!("0000000000000000000000000000000000000000000000000000000000000001");
    let bytes = serde_json::to_vec(&envelope).unwrap();
    assert!(matches!(
        import_captured_terms_v1(&bytes, TERMS, &mut registry),
        Err(SourceErrorV1::ContentDigestMismatch)
    ));
}

#[test]
fn unknown_profile_rejects() {
    let mut registry = SourceRegistryV1::new();
    let mut envelope: serde_json::Value = serde_json::from_slice(ENVELOPE).unwrap();
    envelope["profile_id"] = serde_json::json!("unknown-profile");
    let bytes = serde_json::to_vec(&envelope).unwrap();
    assert!(matches!(
        import_captured_terms_v1(&bytes, TERMS, &mut registry),
        Err(SourceErrorV1::UnknownProfile(_))
    ));
}

#[test]
fn unknown_schema_rejects() {
    let mut registry = SourceRegistryV1::new();
    let mut envelope: serde_json::Value = serde_json::from_slice(ENVELOPE).unwrap();
    envelope["schema_version"] = serde_json::json!("statebook-p6-captured-artifact:v0");
    let bytes = serde_json::to_vec(&envelope).unwrap();
    assert!(matches!(
        import_captured_terms_v1(&bytes, TERMS, &mut registry),
        Err(SourceErrorV1::UnknownSchemaVersion)
    ));
}

#[test]
fn missing_provenance_rejects() {
    let mut registry = SourceRegistryV1::new();
    let mut envelope: serde_json::Value = serde_json::from_slice(ENVELOPE).unwrap();
    envelope.as_object_mut().unwrap().remove("retrieved_at");
    let bytes = serde_json::to_vec(&envelope).unwrap();
    assert!(matches!(
        import_captured_terms_v1(&bytes, TERMS, &mut registry),
        Err(SourceErrorV1::MissingField(_))
    ));
}

#[test]
fn unknown_field_rejects() {
    let mut registry = SourceRegistryV1::new();
    let mut envelope: serde_json::Value = serde_json::from_slice(ENVELOPE).unwrap();
    envelope["extra"] = serde_json::json!("nope");
    let bytes = serde_json::to_vec(&envelope).unwrap();
    assert!(matches!(
        import_captured_terms_v1(&bytes, TERMS, &mut registry),
        Err(SourceErrorV1::UnknownField(_))
    ));
}

#[test]
fn illustrative_narrative_rejects() {
    let mut registry = SourceRegistryV1::new();
    let mut envelope: serde_json::Value = serde_json::from_slice(ENVELOPE).unwrap();
    envelope["evidence_class"] = serde_json::json!("illustrative_narrative");
    let bytes = serde_json::to_vec(&envelope).unwrap();
    assert!(matches!(
        import_captured_terms_v1(&bytes, TERMS, &mut registry),
        Err(SourceErrorV1::IllustrativeNarrativeRejected)
    ));
}

#[test]
fn claim_limit_plus_one_rejects() {
    let mut registry = SourceRegistryV1::new();
    let mut envelope: serde_json::Value = serde_json::from_slice(ENVELOPE).unwrap();
    envelope["supported_claims"] = serde_json::json!((0..=MAX_CLAIM_OR_LIMITATION_COUNT_V1)
        .map(|index| format!("claim-{index}"))
        .collect::<Vec<_>>());
    let bytes = serde_json::to_vec(&envelope).unwrap();
    assert!(matches!(
        import_captured_terms_v1(&bytes, TERMS, &mut registry),
        Err(SourceErrorV1::TooManyClaimsOrLimitations)
    ));
}

#[test]
fn supersede_preserves_historical_digest() {
    let mut registry = SourceRegistryV1::new();
    let receipt = import_captured_terms_v1(ENVELOPE, TERMS, &mut registry).unwrap();
    let before = receipt.registration_digest.clone();
    let superseded = registry
        .supersede(
            &receipt.venue_namespace,
            &receipt.source_contract_id,
            &receipt.source_revision,
        )
        .unwrap();
    assert_ne!(before, superseded.registration_digest);
    assert_eq!(
        superseded.status,
        statebook_source::RegistrationStatusV1::Superseded
    );
    let historical = registry
        .get(
            &receipt.venue_namespace,
            &receipt.source_contract_id,
            &receipt.source_revision,
        )
        .unwrap();
    assert_eq!(historical.content_sha256, receipt.content_sha256);
}
