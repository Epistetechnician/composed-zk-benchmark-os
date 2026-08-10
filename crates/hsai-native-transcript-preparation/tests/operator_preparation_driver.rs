use hsai_native_transcript_preparation::*;

fn minimal_policy() -> MachinePolicyCandidate {
    MachinePolicyCandidate {
        schema: MACHINE_POLICY_SCHEMA.to_string(),
        policy_id: "policy-794-public".to_string(),
        registry_id: EXECUTABLE_REGISTRY_ID.to_string(),
        registry_document_sha256: REGISTRY_DOCUMENT_SHA256.to_string(),
        operation_order_sha256: OPERATION_ORDER_SHA256.to_string(),
        platform: PlatformIdentity {
            os: "macos".to_string(),
            arch: "aarch64".to_string(),
            product_version: "fixture".to_string(),
            build_version: "fixture".to_string(),
        },
        allowed_roots: vec!["/usr/bin".to_string()],
        entries: Vec::new(),
        review: PolicyReviewDeclaration {
            policy_object_producer_id: "policy-producer".to_string(),
            reviewer_id: "policy-reviewer".to_string(),
            reviewed_at_utc: "2026-07-14T00:00:00Z".to_string(),
            decision: ReviewDecision::Accepted,
        },
    }
}

fn body(class: SourceSubjectClass, index: usize) -> SourceReceiptBody {
    SourceReceiptBody {
        schema: SOURCE_RECEIPT_BODY_SCHEMA.to_string(),
        receipt_id: format!("receipt-{index:02}"),
        attempt_id: "attempt-794-public".to_string(),
        subject_class: class,
        subject_id: format!("subject-{index:02}"),
        subject_byte_length: 1,
        subject_sha256: "00".repeat(32),
        declared_source_authority: "fixture:public".to_string(),
        declared_source_revision: "revision-1".to_string(),
        producer_id: format!("producer-{index:02}"),
        reviewer_id: "fixture-reviewer".to_string(),
        reviewer_key_id: "key-fixture".to_string(),
        reviewed_at_utc: "2026-07-14T00:00:00Z".to_string(),
        not_before_utc: "2026-07-13T00:00:00Z".to_string(),
        expires_at_utc: "2026-07-15T00:00:00Z".to_string(),
        decision: ReviewDecision::Accepted,
    }
}

fn shape_complete_request() -> PreparationDriverRequest {
    let policy = minimal_policy();
    let ordered_receipts = SourceSubjectClass::INPUTS
        .iter()
        .copied()
        .enumerate()
        .map(|(index, class)| SourceReceiptEnvelope {
            schema: SOURCE_RECEIPT_ENVELOPE_SCHEMA.to_string(),
            unsigned_body: body(class, index),
            signature_hex: "00".repeat(64),
        })
        .collect();
    PreparationDriverRequest {
        schema: PREPARATION_DRIVER_REQUEST_SCHEMA.to_string(),
        attempt_id: "attempt-794-public".to_string(),
        evaluation_time_utc: "2026-07-14T12:00:00Z".to_string(),
        machine_policy: policy.clone(),
        registry_document_bytes: Vec::new(),
        operation_order_document_bytes: vec![1],
        machine_policy_bytes: serde_json::to_vec(&policy).unwrap(),
        rust_toolchain_manifest_bytes: vec![1],
        charon_source_manifest_bytes: vec![1],
        aeneas_archive_bytes: vec![1],
        sandbox_profile_bytes: SANDBOX_PROFILE_BYTES.to_vec(),
        reviewer_assignments_bytes: vec![1],
        ordered_receipts,
        ordered_verification_profiles: vec![FixtureVerificationProfile {
            schema: FIXTURE_VERIFICATION_PROFILE_SCHEMA.to_string(),
            profile_id: "profile-fixture".to_string(),
            attempt_id: "attempt-794-public".to_string(),
            reviewer_id: "fixture-reviewer".to_string(),
            key_id: "key-fixture".to_string(),
            compressed_sec1_key_hex: format!("02{}", "00".repeat(32)),
            key_sha256: "00".repeat(32),
            allowed_subject_classes: SourceSubjectClass::INPUTS.to_vec(),
            not_before_utc: "2026-07-12T00:00:00Z".to_string(),
            expires_at_utc: "2026-07-16T00:00:00Z".to_string(),
        }],
    }
}

#[test]
fn public_entrypoint_has_one_request_argument_and_no_fact_input() {
    let _: fn(
        &PreparationDriverRequest,
    ) -> Result<PreparationDriverDecision, PreparationDriverPreIdentityRejection> =
        evaluate_preparation_driver;

    let json = serialize_preparation_driver_request_json(&shape_complete_request()).unwrap();
    let text = String::from_utf8(json).unwrap();
    assert!(!text.contains("executable_facts"));
    assert!(!text.contains("collector"));
    assert!(!text.contains("materialization"));
}

#[test]
fn pre_identity_precedence_and_authority_fields_are_fail_closed() {
    let mut request = shape_complete_request();
    request.schema = "wrong".to_string();
    request.ordered_receipts.clear();
    let rejection = evaluate_preparation_driver(&request).unwrap_err();
    assert_eq!(rejection.stage, PreparationDriverStage::RequestShape);
    assert_eq!(rejection.code, PreparationDriverCode::InvalidSchema);
    assert_eq!(rejection.subject_class, None);
    assert!(!rejection.materialization_authorized);
    assert!(!rejection.capture_authorized);

    for class in [
        SourceSubjectClass::OwnedTool,
        SourceSubjectClass::PackagedTarget,
        SourceSubjectClass::BuiltTarget,
    ] {
        let mut request = shape_complete_request();
        request.ordered_receipts[0].unsigned_body.subject_class = class;
        let rejection = evaluate_preparation_driver(&request).unwrap_err();
        assert_eq!(rejection.code, PreparationDriverCode::InvalidCensus);
        assert_eq!(rejection.subject_class, None);
    }

    let request = shape_complete_request();
    let rejection = evaluate_preparation_driver(&request).unwrap_err();
    assert_eq!(rejection.stage, PreparationDriverStage::SubjectBounds);
    assert_eq!(
        rejection.subject_class,
        Some(SourceSubjectClass::ExecutableRegistryDocument)
    );
    assert_eq!(rejection.code, PreparationDriverCode::LengthOutOfBounds);
}

#[test]
fn strict_json_rejects_unknown_trailing_and_noncanonical_input() {
    let request = shape_complete_request();
    let mut value = serde_json::to_value(&request).unwrap();
    value
        .as_object_mut()
        .unwrap()
        .insert("unknown".to_string(), serde_json::Value::Bool(true));
    assert!(deserialize_preparation_driver_request_json(
        serde_json::to_vec(&value).unwrap().as_slice()
    )
    .is_err());

    let mut bytes = serialize_preparation_driver_request_json(&request).unwrap();
    bytes.extend_from_slice(b" trailing");
    assert!(deserialize_preparation_driver_request_json(&bytes).is_err());

    let canonical = serialize_preparation_driver_request_json(&request).unwrap();
    let mut whitespace = b" ".to_vec();
    whitespace.extend_from_slice(&canonical);
    assert!(deserialize_preparation_driver_request_json(&whitespace).is_err());

    let mut reordered = serde_json::to_value(&request).unwrap();
    let object = reordered.as_object_mut().unwrap();
    let schema = object.remove("schema").unwrap();
    object.insert("schema".to_string(), schema);
    let reordered = serde_json::to_vec(&reordered).unwrap();
    assert_ne!(reordered, canonical);
    assert!(deserialize_preparation_driver_request_json(&reordered).is_err());

    let wildcard = String::from_utf8(canonical).unwrap().replacen(
        "\"executable_registry_document\"",
        "\"*\"",
        1,
    );
    assert!(deserialize_preparation_driver_request_json(wildcard.as_bytes()).is_err());
}

#[test]
fn digest_domains_are_distinct_and_lowercase() {
    let body = body(SourceSubjectClass::MachinePolicy, 2);
    let envelope = SourceReceiptEnvelope {
        schema: SOURCE_RECEIPT_ENVELOPE_SCHEMA.to_string(),
        unsigned_body: body,
        signature_hex: "00".repeat(64),
    };
    let mut request = shape_complete_request();
    let profile = request.ordered_verification_profiles.remove(0);
    let envelope_digest = source_receipt_envelope_sha256(&envelope).unwrap();
    let profile_digest = fixture_verification_profile_sha256(&profile).unwrap();
    assert_eq!(envelope_digest.len(), 64);
    assert_eq!(profile_digest.len(), 64);
    assert_ne!(envelope_digest, profile_digest);
    assert!(envelope_digest
        .bytes()
        .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)));
}

#[test]
fn driver_source_has_no_forbidden_execution_or_io_surface() {
    let source = include_str!("../src/driver.rs");
    let production = source.split("#[cfg(test)]\nmod tests").next().unwrap();
    for forbidden in [
        "std::process",
        "std::net",
        "std::fs",
        "std::env",
        "env!(",
        "option_env!(",
        "std::io::Write",
        "Command::new",
        "TcpStream",
        "UdpSocket",
        "write_all",
        "write(",
        "create_dir",
        "remove_file",
        "rename(",
        "OpenOptions",
        "File::create",
        "SigningKey",
        "SecretKey",
        "PrivateKey",
        "from_pkcs8",
        "materialize(",
        "materializer",
        "output_root",
        "callback",
        "sh -c",
        "bash",
        "zsh",
        "shell",
        "helper",
    ] {
        assert!(
            !production.contains(forbidden),
            "forbidden driver surface: {forbidden}"
        );
    }
}

#[test]
fn pre_identity_rejection_wire_is_exact() {
    let rejection = PreparationDriverPreIdentityRejection {
        schema: PREPARATION_DRIVER_PRE_IDENTITY_REJECTION_SCHEMA.to_string(),
        stage: PreparationDriverStage::RequestShape,
        subject_class: None,
        code: PreparationDriverCode::InvalidSchema,
        materialization_authorized: false,
        capture_authorized: false,
    };
    assert_eq!(
        serde_json::to_string(&rejection).unwrap(),
        "{\"schema\":\"hsai-formal-preparation-driver-pre-identity-rejection-v1\",\"stage\":\"request_shape\",\"subject_class\":null,\"code\":\"invalid_schema\",\"materialization_authorized\":false,\"capture_authorized\":false}"
    );
}

#[test]
fn compact_wire_and_signature_preimage_golden_vectors_are_exact() {
    let body = body(SourceSubjectClass::MachinePolicy, 2);
    let body_json = concat!(
        "{\"schema\":\"hsai-formal-source-receipt-body-v1\",",
        "\"receipt_id\":\"receipt-02\",",
        "\"attempt_id\":\"attempt-794-public\",",
        "\"subject_class\":\"machine_policy\",",
        "\"subject_id\":\"subject-02\",",
        "\"subject_byte_length\":1,",
        "\"subject_sha256\":\"0000000000000000000000000000000000000000000000000000000000000000\",",
        "\"declared_source_authority\":\"fixture:public\",",
        "\"declared_source_revision\":\"revision-1\",",
        "\"producer_id\":\"producer-02\",",
        "\"reviewer_id\":\"fixture-reviewer\",",
        "\"reviewer_key_id\":\"key-fixture\",",
        "\"reviewed_at_utc\":\"2026-07-14T00:00:00Z\",",
        "\"not_before_utc\":\"2026-07-13T00:00:00Z\",",
        "\"expires_at_utc\":\"2026-07-15T00:00:00Z\",",
        "\"decision\":\"accepted\"}"
    );
    assert_eq!(serde_json::to_string(&body).unwrap(), body_json);

    let envelope = SourceReceiptEnvelope {
        schema: SOURCE_RECEIPT_ENVELOPE_SCHEMA.to_string(),
        unsigned_body: body.clone(),
        signature_hex: "00".repeat(64),
    };
    let expected_envelope = format!(
        "{{\"schema\":\"hsai-formal-source-receipt-envelope-v1\",\"unsigned_body\":{body_json},\"signature_hex\":\"{}\"}}",
        "00".repeat(64)
    );
    assert_eq!(serde_json::to_string(&envelope).unwrap(), expected_envelope);

    let mut expected_preimage =
        b"hsai-native-transcript-preparation:source-receipt-signature:v1\0".to_vec();
    expected_preimage.extend_from_slice(body_json.as_bytes());
    assert_eq!(
        source_receipt_signature_preimage(&body).unwrap(),
        expected_preimage
    );

    let mut request = shape_complete_request();
    let profile = request.ordered_verification_profiles.remove(0);
    let expected_profile = format!(
        "{{\"schema\":\"hsai-formal-fixture-verification-profile-v1\",\"profile_id\":\"profile-fixture\",\"attempt_id\":\"attempt-794-public\",\"reviewer_id\":\"fixture-reviewer\",\"key_id\":\"key-fixture\",\"compressed_sec1_key_hex\":\"02{}\",\"key_sha256\":\"{}\",\"allowed_subject_classes\":[\"executable_registry_document\",\"operation_order_document\",\"machine_policy\",\"rust_toolchain_manifest\",\"charon_source_tree\",\"aeneas_archive\",\"sandbox_profile\",\"reviewer_assignments\"],\"not_before_utc\":\"2026-07-12T00:00:00Z\",\"expires_at_utc\":\"2026-07-16T00:00:00Z\"}}",
        "00".repeat(32),
        "00".repeat(32)
    );
    assert_eq!(serde_json::to_string(&profile).unwrap(), expected_profile);

    let identity = PreparationDriverRequestIdentity {
        schema: PREPARATION_DRIVER_REQUEST_IDENTITY_SCHEMA.to_string(),
        request_schema: PREPARATION_DRIVER_REQUEST_SCHEMA.to_string(),
        attempt_id: "attempt-794-public".to_string(),
        evaluation_time_utc: "2026-07-14T12:00:00Z".to_string(),
        machine_policy_sha256: "11".repeat(32),
        ordered_subject_identities: Vec::new(),
        ordered_receipt_sha256: Vec::new(),
        ordered_verification_profile_sha256: Vec::new(),
    };
    assert_eq!(
        serde_json::to_string(&identity).unwrap(),
        format!(
            "{{\"schema\":\"hsai-formal-preparation-driver-request-identity-v1\",\"request_schema\":\"hsai-formal-preparation-driver-request-v1\",\"attempt_id\":\"attempt-794-public\",\"evaluation_time_utc\":\"2026-07-14T12:00:00Z\",\"machine_policy_sha256\":\"{}\",\"ordered_subject_identities\":[],\"ordered_receipt_sha256\":[],\"ordered_verification_profile_sha256\":[]}}",
            "11".repeat(32)
        )
    );

    let metadata = MetadataSnapshot {
        device: 1,
        inode: 2,
        mode: 3,
        owner_uid: 4,
        link_count: 5,
        byte_length: 6,
        modified_seconds: 7,
        modified_nanoseconds: 8,
        changed_seconds: 9,
        changed_nanoseconds: 10,
    };
    let fact = ExecutableIdentityFact {
        schema: EXECUTABLE_FACT_SCHEMA.to_string(),
        role_id: HostExecutableRole::CurlExe,
        registry_id: "registry".to_string(),
        machine_policy_id: "policy".to_string(),
        machine_policy_sha256: "11".repeat(32),
        policy_entry_sha256: "22".repeat(32),
        acceptance_policy_id: "acceptance".to_string(),
        decision: ReviewDecision::Accepted,
        declared_platform: PlatformIdentity {
            os: "macos".to_string(),
            arch: "aarch64".to_string(),
            product_version: "product".to_string(),
            build_version: "build".to_string(),
        },
        observed_platform: ObservedPlatformIdentity {
            os: "macos".to_string(),
            arch: "aarch64".to_string(),
        },
        requested_path: "/usr/bin/curl".to_string(),
        ordered_symlink_hops: Vec::new(),
        canonical_regular_file_path: "/usr/bin/curl".to_string(),
        observed_sha256: "33".repeat(32),
        pre_read_metadata: metadata.clone(),
        post_read_metadata: metadata,
    };
    let fact_json = serde_json::to_string(&fact).unwrap();
    assert_eq!(
        fact_json,
        format!(
            "{{\"schema\":\"hsai-formal-executable-identity-fact-v2\",\"role_id\":\"CURL_EXE\",\"registry_id\":\"registry\",\"machine_policy_id\":\"policy\",\"machine_policy_sha256\":\"{}\",\"policy_entry_sha256\":\"{}\",\"acceptance_policy_id\":\"acceptance\",\"decision\":\"accepted\",\"declared_platform\":{{\"os\":\"macos\",\"arch\":\"aarch64\",\"product_version\":\"product\",\"build_version\":\"build\"}},\"observed_platform\":{{\"os\":\"macos\",\"arch\":\"aarch64\"}},\"requested_path\":\"/usr/bin/curl\",\"ordered_symlink_hops\":[],\"canonical_regular_file_path\":\"/usr/bin/curl\",\"observed_sha256\":\"{}\",\"pre_read_metadata\":{{\"device\":1,\"inode\":2,\"mode\":3,\"owner_uid\":4,\"link_count\":5,\"byte_length\":6,\"modified_seconds\":7,\"modified_nanoseconds\":8,\"changed_seconds\":9,\"changed_nanoseconds\":10}},\"post_read_metadata\":{{\"device\":1,\"inode\":2,\"mode\":3,\"owner_uid\":4,\"link_count\":5,\"byte_length\":6,\"modified_seconds\":7,\"modified_nanoseconds\":8,\"changed_seconds\":9,\"changed_nanoseconds\":10}}}}",
            "11".repeat(32),
            "22".repeat(32),
            "33".repeat(32)
        )
    );

    let decision = PreparationDriverDecision {
        schema: PREPARATION_DRIVER_DECISION_SCHEMA.to_string(),
        request_identity_sha256: "44".repeat(32),
        ordered_receipt_sha256: Vec::new(),
        ordered_verification_profile_sha256: Vec::new(),
        ordered_host_fact_sha256: Vec::new(),
        declared_evaluation_time_utc: "2026-07-14T12:00:00Z".to_string(),
        fixture_correspondence_valid: false,
        materialization_authorized: false,
        capture_authorized: false,
        ordered_issues: Vec::new(),
    };
    assert_eq!(
        serde_json::to_string(&decision).unwrap(),
        format!(
            "{{\"schema\":\"hsai-formal-preparation-driver-decision-v1\",\"request_identity_sha256\":\"{}\",\"ordered_receipt_sha256\":[],\"ordered_verification_profile_sha256\":[],\"ordered_host_fact_sha256\":[],\"declared_evaluation_time_utc\":\"2026-07-14T12:00:00Z\",\"fixture_correspondence_valid\":false,\"materialization_authorized\":false,\"capture_authorized\":false,\"ordered_issues\":[]}}",
            "44".repeat(32)
        )
    );
}
