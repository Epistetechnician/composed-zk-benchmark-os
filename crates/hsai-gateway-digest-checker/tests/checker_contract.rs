use hsai_gateway_digest_checker::{
    check_gateway_action_proposal_digest_v1, checker_sha256, encode_gateway_action_proposal_v1,
    validate_checker_digest_result, CheckerArtifactDigest, CheckerError, CheckerGatewayActionId,
    CheckerGatewayActionKind, CheckerGatewayActionProposal, CheckerGatewayModelLaneKind,
    CheckerGatewayThreatLabel, CheckerModelLaneProvenance, CheckerNonclaim, CheckerSubjectId,
    CheckerValidationIssue, CHECKER_CLAIM_BOUNDARY, CHECKER_DIGEST_TAG, CHECKER_HASH_PROVIDER_ID,
};

fn fixture() -> CheckerGatewayActionProposal {
    CheckerGatewayActionProposal {
        id: CheckerGatewayActionId("phase660-action".to_owned()),
        subject: CheckerSubjectId("agent-phase660".to_owned()),
        action_kind: CheckerGatewayActionKind::Payment,
        target: "treasury-safe".to_owned(),
        value_units: 50,
        source_artifact_digests: Vec::new(),
        nonclaims: Vec::new(),
        model_lane: CheckerModelLaneProvenance {
            lane_kind: CheckerGatewayModelLaneKind::Deterministic,
            model_family: "model-a".to_owned(),
            artifact_id: "artifact-a".to_owned(),
            runtime: "runtime-a".to_owned(),
            prompt_template_digest: [1; 32],
            input_corpus_digest: [2; 32],
            output_bundle_digest: [3; 32],
            non_secret: true,
        },
        threat_labels: Vec::new(),
        direct_authority_requested: false,
        signer_or_tool_requested_before_admission: false,
    }
}

fn hash_from_hex(value: &str) -> [u8; 32] {
    assert_eq!(value.len(), 64);
    let mut out = [0; 32];
    for (index, byte) in out.iter_mut().enumerate() {
        let start = index * 2;
        *byte =
            u8::from_str_radix(&value[start..start + 2], 16).expect("checker test hash hex parses");
    }
    out
}

#[test]
fn phase662_checker_matches_the_complete_phase660_golden_vector() {
    const EXPECTED_PREIMAGE: &str = concat!(
        r#"["hsai-agent-admission:gateway-action-proposal:v1",{"id":"phase660-action","subject":"agent-phase660","action_kind":"Payment","target":"treasury-safe","value_units":50,"source_artifact_digests":[],"nonclaims":[],"model_lane":{"lane_kind":"Deterministic","model_family":"model-a","artifact_id":"artifact-a","runtime":"runtime-a","prompt_template_digest":[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],"#,
        r#""input_corpus_digest":[2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2],"#,
        r#""output_bundle_digest":[3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3,3],"non_secret":true},"threat_labels":[],"direct_authority_requested":false,"signer_or_tool_requested_before_admission":false}]"#,
    );
    let proposal = fixture();
    let preimage = encode_gateway_action_proposal_v1(&proposal).expect("golden encoding succeeds");
    let result =
        check_gateway_action_proposal_digest_v1(&proposal).expect("golden checker succeeds");

    assert_eq!(preimage, EXPECTED_PREIMAGE.as_bytes());
    assert_eq!(result.encoded_preimage, EXPECTED_PREIMAGE.as_bytes());
    assert_eq!(result.encoded_preimage_length, preimage.len() as u64);
    assert_eq!(
        result.digest,
        hash_from_hex("52de11c37c1492b7c9fb7c42660d693f5a7cbc6ed69f3bb371d66ad2686938fa")
    );
    assert_eq!(result.digest_tag, CHECKER_DIGEST_TAG);
    assert_eq!(result.hash_provider_identity, CHECKER_HASH_PROVIDER_ID);
    assert_eq!(result.claim_boundary, CHECKER_CLAIM_BOUNDARY);
    assert!(result
        .explicit_nonclaims
        .contains(&"not independent formal verification".to_owned()));
    assert!(result.explicit_nonclaims.contains(&"not SOTA".to_owned()));
    assert!(
        validate_checker_digest_result(&proposal, &result)
            .expect("golden result validates")
            .valid
    );
}

#[test]
fn phase662_checker_ring_sha256_matches_the_standard_abc_vector() {
    assert_eq!(
        checker_sha256(b"abc"),
        hash_from_hex("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
    );
}

#[test]
fn phase662_checker_orders_set_fields_and_rejects_duplicates() {
    let artifact_a = CheckerArtifactDigest {
        id: "a-artifact".to_owned(),
        sha256: [8; 32],
    };
    let artifact_z = CheckerArtifactDigest {
        id: "z-artifact".to_owned(),
        sha256: [9; 32],
    };
    let mut first = fixture();
    first.source_artifact_digests = vec![artifact_z.clone(), artifact_a.clone()];
    first.nonclaims = vec![
        CheckerNonclaim("z-nonclaim".to_owned()),
        CheckerNonclaim("a-nonclaim".to_owned()),
    ];
    first.threat_labels = vec![
        CheckerGatewayThreatLabel::StaleApprovalReplay,
        CheckerGatewayThreatLabel::Benign,
    ];
    let mut second = fixture();
    second.source_artifact_digests = vec![artifact_a.clone(), artifact_z];
    second.nonclaims = vec![
        CheckerNonclaim("a-nonclaim".to_owned()),
        CheckerNonclaim("z-nonclaim".to_owned()),
    ];
    second.threat_labels = vec![
        CheckerGatewayThreatLabel::Benign,
        CheckerGatewayThreatLabel::StaleApprovalReplay,
    ];

    assert_eq!(
        encode_gateway_action_proposal_v1(&first).expect("first ordering encodes"),
        encode_gateway_action_proposal_v1(&second).expect("second ordering encodes")
    );

    let mut duplicate_artifact = fixture();
    duplicate_artifact.source_artifact_digests = vec![artifact_a.clone(), artifact_a.clone()];
    assert_eq!(
        encode_gateway_action_proposal_v1(&duplicate_artifact),
        Err(CheckerError::DuplicateSourceArtifact(artifact_a))
    );

    let mut duplicate_nonclaim = fixture();
    duplicate_nonclaim.nonclaims = vec![
        CheckerNonclaim("duplicate".to_owned()),
        CheckerNonclaim("duplicate".to_owned()),
    ];
    assert_eq!(
        encode_gateway_action_proposal_v1(&duplicate_nonclaim),
        Err(CheckerError::DuplicateNonclaim(CheckerNonclaim(
            "duplicate".to_owned()
        )))
    );

    let mut duplicate_threat = fixture();
    duplicate_threat.threat_labels = vec![
        CheckerGatewayThreatLabel::Benign,
        CheckerGatewayThreatLabel::Benign,
    ];
    assert_eq!(
        encode_gateway_action_proposal_v1(&duplicate_threat),
        Err(CheckerError::DuplicateThreatLabel(
            CheckerGatewayThreatLabel::Benign
        ))
    );
}

#[test]
fn phase662_checker_locks_all_enum_labels_and_json_encoding_edges() {
    let action_variants = [
        (CheckerGatewayActionKind::Payment, "Payment"),
        (CheckerGatewayActionKind::Trade, "Trade"),
        (CheckerGatewayActionKind::ToolCall, "ToolCall"),
        (CheckerGatewayActionKind::DataAccess, "DataAccess"),
        (CheckerGatewayActionKind::ComputeRental, "ComputeRental"),
        (CheckerGatewayActionKind::Deployment, "Deployment"),
        (CheckerGatewayActionKind::Checkout, "Checkout"),
    ];
    for (variant, label) in action_variants {
        let mut proposal = fixture();
        proposal.action_kind = variant;
        let text = String::from_utf8(
            encode_gateway_action_proposal_v1(&proposal).expect("action variant encodes"),
        )
        .expect("checker output is UTF-8");
        assert!(text.contains(&format!(r#""action_kind":"{label}""#)));
    }

    let lane_variants = [
        (CheckerGatewayModelLaneKind::Deterministic, "Deterministic"),
        (
            CheckerGatewayModelLaneKind::LocalOpenWeight,
            "LocalOpenWeight",
        ),
        (
            CheckerGatewayModelLaneKind::RentedOpenWeight,
            "RentedOpenWeight",
        ),
        (CheckerGatewayModelLaneKind::HostedSmall, "HostedSmall"),
        (
            CheckerGatewayModelLaneKind::PremiumEscalation,
            "PremiumEscalation",
        ),
    ];
    for (variant, label) in lane_variants {
        let mut proposal = fixture();
        proposal.model_lane.lane_kind = variant;
        let text = String::from_utf8(
            encode_gateway_action_proposal_v1(&proposal).expect("lane variant encodes"),
        )
        .expect("checker output is UTF-8");
        assert!(text.contains(&format!(r#""lane_kind":"{label}""#)));
    }

    let threat_variants = [
        (CheckerGatewayThreatLabel::Benign, "Benign"),
        (
            CheckerGatewayThreatLabel::PromptInjectionPayment,
            "PromptInjectionPayment",
        ),
        (
            CheckerGatewayThreatLabel::WrongCounterparty,
            "WrongCounterparty",
        ),
        (
            CheckerGatewayThreatLabel::AmountLimitBypass,
            "AmountLimitBypass",
        ),
        (
            CheckerGatewayThreatLabel::SourceDigestDrift,
            "SourceDigestDrift",
        ),
        (
            CheckerGatewayThreatLabel::StaleApprovalReplay,
            "StaleApprovalReplay",
        ),
        (
            CheckerGatewayThreatLabel::DuplicateJsonKeyPayload,
            "DuplicateJsonKeyPayload",
        ),
        (
            CheckerGatewayThreatLabel::PolicyDowngrade,
            "PolicyDowngrade",
        ),
        (
            CheckerGatewayThreatLabel::DirectAuthorityRequest,
            "DirectAuthorityRequest",
        ),
        (
            CheckerGatewayThreatLabel::ForgedAcceptedDecision,
            "ForgedAcceptedDecision",
        ),
        (
            CheckerGatewayThreatLabel::MissingNonclaim,
            "MissingNonclaim",
        ),
        (
            CheckerGatewayThreatLabel::MissingSourceDigest,
            "MissingSourceDigest",
        ),
        (
            CheckerGatewayThreatLabel::StaleJournalTip,
            "StaleJournalTip",
        ),
        (
            CheckerGatewayThreatLabel::SignerBeforeAdmission,
            "SignerBeforeAdmission",
        ),
    ];
    for (variant, label) in threat_variants {
        let mut proposal = fixture();
        proposal.threat_labels = vec![variant];
        let text = String::from_utf8(
            encode_gateway_action_proposal_v1(&proposal).expect("threat variant encodes"),
        )
        .expect("checker output is UTF-8");
        assert!(text.contains(&format!(r#""threat_labels":["{label}"]"#)));
    }

    let mut edge = fixture();
    edge.target = "quote\" slash\\ backspace\u{0008} tab\t newline\n formfeed\u{000c} carriage\r control\u{0001} snowman \u{2603}".to_owned();
    edge.value_units = u64::MAX;
    edge.source_artifact_digests = vec![CheckerArtifactDigest {
        id: "edge-artifact".to_owned(),
        sha256: [255; 32],
    }];
    edge.nonclaims = vec![CheckerNonclaim("edge nonclaim".to_owned())];
    edge.threat_labels = vec![CheckerGatewayThreatLabel::DuplicateJsonKeyPayload];
    let edge_text =
        String::from_utf8(encode_gateway_action_proposal_v1(&edge).expect("edge proposal encodes"))
            .expect("checker edge output is UTF-8");
    let expected_target = format!(
        r#""target":"quote\" slash\\ backspace\b tab\t newline\n formfeed\f carriage\r control\u0001 snowman {}""#,
        '\u{2603}'
    );
    assert!(edge_text.contains(&expected_target));
    assert!(edge_text.contains(r#""value_units":18446744073709551615"#));
    assert!(!edge_text.ends_with('\n'));
    assert!(!edge_text.contains(": "));
}

#[test]
fn phase662_checker_validation_rejects_metadata_digest_and_claim_drift() {
    let proposal = fixture();
    let baseline =
        check_gateway_action_proposal_digest_v1(&proposal).expect("baseline checker succeeds");
    let mut cases = Vec::new();

    let mut result = baseline.clone();
    result.schema_version = "wrong-schema".to_owned();
    cases.push((CheckerValidationIssue::SchemaVersionMismatch, result));

    let mut result = baseline.clone();
    result.state_slice = "wrong-state".to_owned();
    cases.push((CheckerValidationIssue::StateSliceMismatch, result));

    let mut result = baseline.clone();
    result.checker_implementation_id = "wrong-checker".to_owned();
    cases.push((
        CheckerValidationIssue::CheckerImplementationIdMismatch,
        result,
    ));

    let mut result = baseline.clone();
    result.digest_tag = "hsai-agent-admission:gateway-action-proposal:v2".to_owned();
    cases.push((CheckerValidationIssue::DigestTagMismatch, result));

    let mut result = baseline.clone();
    result.encoded_preimage[0] ^= 1;
    cases.push((CheckerValidationIssue::EncodedPreimageMismatch, result));

    let mut result = baseline.clone();
    result.encoded_preimage_length += 1;
    cases.push((
        CheckerValidationIssue::EncodedPreimageLengthMismatch,
        result,
    ));

    let mut result = baseline.clone();
    result.digest[0] ^= 1;
    cases.push((CheckerValidationIssue::DigestMismatch, result));

    let mut result = baseline.clone();
    result.encoder_identity = "production-serde-encoder".to_owned();
    cases.push((CheckerValidationIssue::EncoderIdentityMismatch, result));

    let mut result = baseline.clone();
    result.hash_provider_identity = "production-sha2".to_owned();
    cases.push((CheckerValidationIssue::HashProviderIdentityMismatch, result));

    let mut result = baseline.clone();
    result.independence_profile.shared_axes.clear();
    cases.push((CheckerValidationIssue::IndependenceProfileMismatch, result));

    let mut result = baseline.clone();
    result.claim_boundary = "independent formal verification".to_owned();
    cases.push((CheckerValidationIssue::ClaimBoundaryMismatch, result));

    let mut result = baseline;
    result.explicit_nonclaims.clear();
    cases.push((CheckerValidationIssue::ExplicitNonclaimsMismatch, result));

    for (expected_issue, result) in cases {
        let validation = validate_checker_digest_result(&proposal, &result)
            .expect("tampered result remains structurally checkable");
        assert!(!validation.valid);
        assert!(validation.issues.contains(&expected_issue));
    }
}
