use hsai_native_transcript_preparation::*;
use sha2::{Digest, Sha256};

fn digest(seed: &str) -> String {
    Sha256::digest(seed.as_bytes())
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn metadata() -> MetadataSnapshot {
    MetadataSnapshot {
        device: 1,
        inode: 2,
        mode: 0o100755,
        owner_uid: 501,
        link_count: 1,
        byte_length: 3,
        modified_seconds: 4,
        modified_nanoseconds: 5,
        changed_seconds: 6,
        changed_nanoseconds: 7,
    }
}

fn requested_path(role: HostExecutableRole) -> String {
    role.expected_fixed_path()
        .map(str::to_string)
        .unwrap_or_else(|| format!("/allowed/{}", role.label().to_ascii_lowercase()))
}

fn complete_candidate() -> PreparationCandidate {
    let entries = HostExecutableRole::ALL
        .iter()
        .copied()
        .map(|role| MachinePolicyEntry {
            role_id: role,
            requested_path: requested_path(role),
            allowed_owner_uids: vec![501],
            admitted_sha256: vec![digest(role.label())],
            acceptance_policy_id: role.expected_policy_id().to_string(),
        })
        .collect::<Vec<_>>();
    let platform = PlatformIdentity {
        os: "macos".to_string(),
        arch: "aarch64".to_string(),
        product_version: "test".to_string(),
        build_version: "test".to_string(),
    };
    let machine_policy = MachinePolicyCandidate {
        schema: MACHINE_POLICY_SCHEMA.to_string(),
        policy_id: "policy-candidate-1".to_string(),
        registry_id: EXECUTABLE_REGISTRY_ID.to_string(),
        registry_document_sha256: REGISTRY_DOCUMENT_SHA256.to_string(),
        operation_order_sha256: OPERATION_ORDER_SHA256.to_string(),
        platform: platform.clone(),
        allowed_roots: vec![
            "/allowed".to_string(),
            "/usr/bin".to_string(),
            "/usr/sbin".to_string(),
        ],
        entries,
        review: PolicyReviewDeclaration {
            policy_object_producer_id: "policy-producer".to_string(),
            reviewer_id: "policy-reviewer".to_string(),
            reviewed_at_utc: "2026-07-14T00:00:00Z".to_string(),
            decision: ReviewDecision::Accepted,
        },
    };
    let policy_sha256 = machine_policy_sha256(&machine_policy).unwrap();
    let executable_facts = HostExecutableRole::ALL
        .iter()
        .copied()
        .map(|role| ExecutableIdentityFact {
            schema: EXECUTABLE_FACT_SCHEMA.to_string(),
            role_id: role,
            registry_id: machine_policy.registry_id.clone(),
            machine_policy_id: machine_policy.policy_id.clone(),
            machine_policy_sha256: policy_sha256.clone(),
            policy_entry_sha256: machine_policy_entry_sha256(
                machine_policy
                    .entries
                    .iter()
                    .find(|entry| entry.role_id == role)
                    .unwrap(),
            )
            .unwrap(),
            acceptance_policy_id: role.expected_policy_id().to_string(),
            decision: ReviewDecision::Accepted,
            declared_platform: platform.clone(),
            observed_platform: ObservedPlatformIdentity {
                os: "macos".to_string(),
                arch: "aarch64".to_string(),
            },
            requested_path: requested_path(role),
            ordered_symlink_hops: vec![],
            canonical_regular_file_path: requested_path(role),
            observed_sha256: digest(role.label()),
            pre_read_metadata: metadata(),
            post_read_metadata: metadata(),
        })
        .collect::<Vec<_>>();
    let owned_tool_receipts = OwnedToolRole::ALL
        .iter()
        .copied()
        .map(|role| OwnedToolReceipt {
            role_id: role,
            relative_path: role.expected_relative_path().to_string(),
            sha256: digest(role.label()),
            source_receipt_sha256: digest(&format!("source-{}", role.label())),
            accepted: true,
        })
        .collect::<Vec<_>>();
    let target_receipts = TargetId::ALL
        .iter()
        .copied()
        .map(|target| TargetReceipt {
            target_id: target,
            relative_path: target.expected_relative_path().to_string(),
            byte_length: 1,
            sha256: target
                .expected_packaged_sha256()
                .map(str::to_string)
                .unwrap_or_else(|| digest(&format!("{target:?}"))),
            source_authority: target.expected_source_authority().to_string(),
            source_receipt_sha256: digest(&format!("receipt:{target:?}")),
            producer_ordinal: if target.is_built() { 73 } else { 0 },
            source_commit: target.is_built().then(|| CHARON_SOURCE_COMMIT.to_string()),
            macho_arch: target.is_built().then(|| "arm64".to_string()),
            ad_hoc_signed: target.is_built().then_some(true),
            team_id: None,
            source_tree_stable: target.is_built().then_some(true),
            accepted: true,
        })
        .collect::<Vec<_>>();

    PreparationCandidate {
        schema: PREPARATION_CANDIDATE_SCHEMA.to_string(),
        state_slice: STATE_SLICE.to_string(),
        claim_boundary: CLAIM_BOUNDARY.to_string(),
        explicit_nonclaims: EXPLICIT_NONCLAIMS
            .iter()
            .map(|value| (*value).to_string())
            .collect(),
        operation_order_sha256: OPERATION_ORDER_SHA256.to_string(),
        preparation_root: PREPARATION_ROOT.to_string(),
        capture_root: CAPTURE_ROOT.to_string(),
        capture_root_declared_absent: true,
        aeneas_archive_url: AENEAS_ARCHIVE_URL.to_string(),
        aeneas_archive_byte_length: AENEAS_ARCHIVE_BYTE_LENGTH,
        aeneas_archive_sha256: AENEAS_ARCHIVE_SHA256.to_string(),
        charon_source_commit: CHARON_SOURCE_COMMIT.to_string(),
        machine_policy,
        executable_facts,
        owned_tool_receipts,
        target_receipts,
        sandbox_profile_bytes: SANDBOX_PROFILE_BYTES.to_vec(),
        sandbox_profile_sha256: SANDBOX_PROFILE_SHA256.to_string(),
        reviewer_assignments: ReviewerAssignments {
            machine_policy_reviewer_id: "policy-reviewer".to_string(),
            capture_operator_id: "capture-operator".to_string(),
            fixture_reviewer_id: "fixture-reviewer".to_string(),
            grammar_reviewer_id: "grammar-reviewer".to_string(),
        },
    }
}

#[test]
fn complete_declared_candidate_validates_without_authorizing_capture() {
    let validation = validate_preparation_candidate(&complete_candidate());
    assert!(validation.structurally_valid, "{:?}", validation.issues);
    assert!(
        validation.declared_inputs_complete,
        "{:?}",
        validation.issues
    );
    assert!(validation.candidate_eligible_for_external_review);
    assert!(!validation.materialization_accepted);
    assert!(!validation.capture_authorized);
}

#[test]
fn pending_policy_and_reviewer_conflicts_fail_closed() {
    let mut candidate = complete_candidate();
    candidate.machine_policy.review.decision = ReviewDecision::Pending;
    candidate.reviewer_assignments.capture_operator_id = "policy-reviewer".to_string();
    candidate.reviewer_assignments.fixture_reviewer_id = "policy-reviewer".to_string();

    let validation = validate_preparation_candidate(&candidate);
    assert!(!validation.structurally_valid);
    assert!(!validation.declared_inputs_complete);
    assert!(!validation.candidate_eligible_for_external_review);
    assert!(!validation.materialization_accepted);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.class == ValidationIssueClass::ExternalAuthority));
    assert!(!validation.capture_authorized);
}

#[test]
fn missing_wrapper_and_target_digest_drift_are_rejected() {
    let mut candidate = complete_candidate();
    candidate
        .executable_facts
        .retain(|fact| fact.role_id != HostExecutableRole::SandboxExecExe);
    candidate.target_receipts[0].sha256 = digest("drift");

    let validation = validate_preparation_candidate(&candidate);
    assert!(!validation.structurally_valid);
    assert!(!validation.declared_inputs_complete);
    assert!(validation.issues.iter().any(|issue| {
        issue.subject == "SANDBOX_EXEC_EXE" && issue.class == ValidationIssueClass::MissingInput
    }));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.class == ValidationIssueClass::IdentityDrift));
}

#[test]
fn capture_authorization_and_claim_boundary_drift_are_rejected() {
    let mut candidate = complete_candidate();
    candidate.claim_boundary = "capture is authorized".to_string();
    candidate.capture_root_declared_absent = false;
    candidate.sandbox_profile_bytes.push(b' ');

    let validation = validate_preparation_candidate(&candidate);
    assert!(!validation.structurally_valid);
    assert!(!validation.capture_authorized);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.class == ValidationIssueClass::Structural));
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.class == ValidationIssueClass::ClaimBoundary));
}

#[test]
fn candidate_serialization_and_digest_are_deterministic() {
    let candidate = complete_candidate();
    assert!(PREPARATION_CANDIDATE_SCHEMA.ends_with("-v2"));
    assert!(EXECUTABLE_FACT_SCHEMA.ends_with("-v2"));
    assert!(PREPARATION_CANDIDATE_SCHEMA_V1.ends_with("-v1"));
    assert!(EXECUTABLE_FACT_SCHEMA_V1.ends_with("-v1"));
    assert_ne!(CANDIDATE_DIGEST_DOMAIN, CANDIDATE_DIGEST_DOMAIN_V1);
    assert_ne!(STATE_SLICE, STATE_SLICE_V1);
    assert_eq!(
        serialize_candidate_json(&candidate).unwrap(),
        serialize_candidate_json(&candidate).unwrap()
    );
    assert_eq!(
        candidate_sha256(&candidate).unwrap(),
        candidate_sha256(&candidate).unwrap()
    );
}

#[test]
fn built_target_without_ordinal_073_acceptance_is_rejected() {
    let mut candidate = complete_candidate();
    let receipt = candidate
        .target_receipts
        .iter_mut()
        .find(|receipt| receipt.target_id == TargetId::BuiltCharon)
        .unwrap();
    receipt.producer_ordinal = 671;
    receipt.source_tree_stable = Some(false);

    let validation = validate_preparation_candidate(&candidate);
    assert!(!validation.structurally_valid);
    assert!(!validation.declared_inputs_complete);
    assert!(!validation.capture_authorized);
}

#[test]
fn unknown_candidate_fields_are_rejected() {
    let candidate = complete_candidate();
    let mut value = serde_json::to_value(candidate).unwrap();
    value.as_object_mut().unwrap().insert(
        "capture_authorized".to_string(),
        serde_json::Value::Bool(true),
    );

    assert!(serde_json::from_value::<PreparationCandidate>(value).is_err());
}

#[test]
fn non_normalized_or_non_regular_executable_facts_are_rejected() {
    let mut candidate = complete_candidate();
    let fact = candidate
        .executable_facts
        .iter_mut()
        .find(|fact| fact.role_id == HostExecutableRole::GitExe)
        .unwrap();
    fact.canonical_regular_file_path = "/allowed/bin/../git".to_string();
    fact.pre_read_metadata.mode = 0o040755;
    fact.post_read_metadata.mode = 0o040755;

    let validation = validate_preparation_candidate(&candidate);
    assert!(!validation.structurally_valid);
    assert!(!validation.candidate_eligible_for_external_review);
    assert!(!validation.materialization_accepted);
    assert!(!validation.capture_authorized);
}
