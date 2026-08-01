use crate::{
    collect_executable_identity_fact, machine_policy_entry_sha256, machine_policy_sha256,
    validate_machine_policy_candidate, ExecutableIdentityFact, HostExecutableRole,
    MachinePolicyCandidate, ReviewDecision, ReviewerAssignments, AENEAS_ARCHIVE_BYTE_LENGTH,
    AENEAS_ARCHIVE_SHA256, AENEAS_ARCHIVE_URL, CHARON_SOURCE_COMMIT, EXECUTABLE_FACT_SCHEMA,
    EXECUTABLE_REGISTRY_ID, OPERATION_ORDER_SHA256, REGISTRY_DOCUMENT_SHA256,
    SANDBOX_PROFILE_BYTES, SANDBOX_PROFILE_SHA256, STATE_SLICE,
};
use p256::ecdsa::{signature::Verifier, Signature, VerifyingKey};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

pub const SOURCE_RECEIPT_BODY_SCHEMA: &str = "hsai-formal-source-receipt-body-v1";
pub const SOURCE_RECEIPT_ENVELOPE_SCHEMA: &str = "hsai-formal-source-receipt-envelope-v1";
pub const FIXTURE_VERIFICATION_PROFILE_SCHEMA: &str = "hsai-formal-fixture-verification-profile-v1";
pub const PREPARATION_DRIVER_REQUEST_SCHEMA: &str = "hsai-formal-preparation-driver-request-v1";
pub const SUBJECT_IDENTITY_SCHEMA: &str = "hsai-formal-preparation-subject-identity-v1";
pub const PREPARATION_DRIVER_REQUEST_IDENTITY_SCHEMA: &str =
    "hsai-formal-preparation-driver-request-identity-v1";
pub const PREPARATION_DRIVER_DECISION_SCHEMA: &str = "hsai-formal-preparation-driver-decision-v1";
pub const PREPARATION_DRIVER_ISSUE_SCHEMA: &str = "hsai-formal-preparation-driver-issue-v1";
pub const PREPARATION_DRIVER_PRE_IDENTITY_REJECTION_SCHEMA: &str =
    "hsai-formal-preparation-driver-pre-identity-rejection-v1";
pub const RUST_TOOLCHAIN_MANIFEST_SCHEMA: &str = "hsai-formal-rust-toolchain-manifest-v1";
pub const CHARON_SOURCE_MANIFEST_SCHEMA: &str = "hsai-formal-charon-source-manifest-v1";

pub const SOURCE_RECEIPT_SIGNATURE_DOMAIN: &[u8] =
    b"hsai-native-transcript-preparation:source-receipt-signature:v1\0";
pub const SOURCE_RECEIPT_ENVELOPE_DIGEST_DOMAIN: &[u8] =
    b"hsai-native-transcript-preparation:source-receipt-envelope:v1\0";
pub const FIXTURE_VERIFICATION_PROFILE_DIGEST_DOMAIN: &[u8] =
    b"hsai-native-transcript-preparation:fixture-verification-profile:v1\0";
pub const PREPARATION_DRIVER_REQUEST_DIGEST_DOMAIN: &[u8] =
    b"hsai-native-transcript-preparation:driver-request:v1\0";
pub const EXECUTABLE_FACT_DIGEST_DOMAIN: &[u8] =
    b"hsai-native-transcript-preparation:executable-fact:v2\0";
pub const PREPARATION_DRIVER_DECISION_DIGEST_DOMAIN: &[u8] =
    b"hsai-native-transcript-preparation:driver-decision:v1\0";

pub const MAX_SMALL_SUBJECT_BYTES: usize = 1_048_576;
pub const MAX_CHARON_MANIFEST_BYTES: usize = 67_108_864;
pub const REGISTRY_DOCUMENT_BYTE_LENGTH: usize = 24_738;
pub const OPERATION_ORDER_SUBJECT_ID: &str = "phase778-operation-order";
pub const REGISTRY_DECLARED_SOURCE_AUTHORITY: &str = "repo:docs/787";
pub const OPERATION_ORDER_DECLARED_SOURCE_AUTHORITY: &str = "repo:docs/778";
pub const MACHINE_POLICY_DECLARED_SOURCE_AUTHORITY: &str = "repo:machine-policy-fixture";
pub const RUST_MANIFEST_SUBJECT_ID: &str = "phase789-rust-toolchain-manifest";
pub const RUST_MANIFEST_DECLARED_SOURCE_AUTHORITY: &str = "fixture:rust-toolchain-manifest";
pub const CHARON_DECLARED_SOURCE_AUTHORITY: &str = "fixture:charon-source-manifest";
pub const SANDBOX_SUBJECT_ID: &str = "phase776-deny-network-sandbox";
pub const SANDBOX_DECLARED_SOURCE_AUTHORITY: &str = "repo:constant";
pub const REVIEWER_ASSIGNMENTS_DECLARED_SOURCE_AUTHORITY: &str = "fixture:reviewer-assignments";
pub const AENEAS_ARCHIVE_SUBJECT_ID: &str = "aeneas-macos-aarch64.tar.gz";
pub const AENEAS_ARCHIVE_SOURCE_REVISION: &str = "nightly-2026.07.10-c2015b8";

const RUST_CHANNEL: &str = "nightly-2026-06-01";
const RUST_MANIFEST_URL: &str =
    "https://static.rust-lang.org/dist/2026-06-01/channel-rust-nightly.toml";
const RUST_MANIFEST_SHA256: &str =
    "aaf1cb59b5996dd51831c9114b6e3a4a176e197851de91194b473117e142b935";
const CHARON_RUST_TOOLCHAIN_SHA256: &str =
    "27e050e8fc5ac827e1264abf38c27fcaf18e73f4305104c866179cb84721898c";
const RUSTC_IDENTITY: &str = "rustc 1.98.0-nightly (14210df0e 2026-05-31)";
const RUSTC_COMMIT: &str = "14210df0e27ccd7d9e6a05b8085cbd438e4bbc65";

const RUST_COMPONENTS: [(&str, &str, &str); 7] = [
    (
        "cargo",
        "aarch64-apple-darwin",
        "755d86dfcfc4b27526345bd8f510ee3dff0111a0aea3769b0a176ecd02e7f8db",
    ),
    (
        "rustc",
        "aarch64-apple-darwin",
        "6f40295ebcc383b6beb8536a161a39fe5201851a636ffb6eb915bb7dbb6026ed",
    ),
    (
        "rust-std",
        "aarch64-apple-darwin",
        "990006a1faac5e2e71b78b9c45912b528e02cacab19321526d2a2ec75cfdec44",
    ),
    (
        "rustc-dev",
        "aarch64-apple-darwin",
        "eb2d8507fcf1b2d4766598c4c04226c5b1c276fc9d81cff0fa970a90f42ab379",
    ),
    (
        "llvm-tools-preview",
        "aarch64-apple-darwin",
        "d6acc436144d3094e1e067947553d9cce50bf7b710cb089f345e8fcea7e59d02",
    ),
    (
        "rust-src",
        "*",
        "3ce6b9d679b5d1840d3ed276e74c8d6b4b1da5ebef2eeb542b588de04ada039f",
    ),
    (
        "miri-preview",
        "aarch64-apple-darwin",
        "29a9f42fecbfc53fc3ceadfb85407ef4bba06669d093c0b32bc15efcfd17147e",
    ),
];

const CHARON_SOURCE_FILES: [(&str, &str); 5] = [
    (
        "LICENSE.md",
        "c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4",
    ),
    (
        "README.md",
        "be0566d77bef830f6fa019fa7ae460377d130576aa143c2a7db0238341b4214a",
    ),
    (
        "charon/Cargo.lock",
        "4e361622e601cfe93fce40e5a13bf6b5a89a84394875b409f8c8f27ec86272db",
    ),
    (
        "charon/Cargo.toml",
        "a596f9b50a62e142199bca400de2318a0426b914039882896a270a35cd7481b2",
    ),
    (
        "charon/rust-toolchain",
        "27e050e8fc5ac827e1264abf38c27fcaf18e73f4305104c866179cb84721898c",
    ),
];

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum SourceSubjectClass {
    ExecutableRegistryDocument,
    OperationOrderDocument,
    MachinePolicy,
    RustToolchainManifest,
    CharonSourceTree,
    AeneasArchive,
    SandboxProfile,
    ReviewerAssignments,
    OwnedTool,
    PackagedTarget,
    BuiltTarget,
}

impl SourceSubjectClass {
    pub const INPUTS: [Self; 8] = [
        Self::ExecutableRegistryDocument,
        Self::OperationOrderDocument,
        Self::MachinePolicy,
        Self::RustToolchainManifest,
        Self::CharonSourceTree,
        Self::AeneasArchive,
        Self::SandboxProfile,
        Self::ReviewerAssignments,
    ];

    pub fn is_input(self) -> bool {
        Self::INPUTS.contains(&self)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceReceiptBody {
    pub schema: String,
    pub receipt_id: String,
    pub attempt_id: String,
    pub subject_class: SourceSubjectClass,
    pub subject_id: String,
    pub subject_byte_length: u64,
    pub subject_sha256: String,
    pub declared_source_authority: String,
    pub declared_source_revision: String,
    pub producer_id: String,
    pub reviewer_id: String,
    pub reviewer_key_id: String,
    pub reviewed_at_utc: String,
    pub not_before_utc: String,
    pub expires_at_utc: String,
    pub decision: ReviewDecision,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceReceiptEnvelope {
    pub schema: String,
    pub unsigned_body: SourceReceiptBody,
    pub signature_hex: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct FixtureVerificationProfile {
    pub schema: String,
    pub profile_id: String,
    pub attempt_id: String,
    pub reviewer_id: String,
    pub key_id: String,
    pub compressed_sec1_key_hex: String,
    pub key_sha256: String,
    pub allowed_subject_classes: Vec<SourceSubjectClass>,
    pub not_before_utc: String,
    pub expires_at_utc: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RustToolchainComponent {
    pub component: String,
    pub target: String,
    pub xz_sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RustToolchainManifest {
    pub schema: String,
    pub channel: String,
    pub manifest_url: String,
    pub manifest_sha256: String,
    pub charon_rust_toolchain_sha256: String,
    pub rustc_identity: String,
    pub rustc_commit: String,
    pub ordered_components: Vec<RustToolchainComponent>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CharonSourceFile {
    pub relative_path: String,
    pub byte_length: u64,
    pub sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CharonSourceManifest {
    pub schema: String,
    pub commit: String,
    pub ordered_files: Vec<CharonSourceFile>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PreparationDriverRequest {
    pub schema: String,
    pub attempt_id: String,
    pub evaluation_time_utc: String,
    pub machine_policy: MachinePolicyCandidate,
    pub registry_document_bytes: Vec<u8>,
    pub operation_order_document_bytes: Vec<u8>,
    pub machine_policy_bytes: Vec<u8>,
    pub rust_toolchain_manifest_bytes: Vec<u8>,
    pub charon_source_manifest_bytes: Vec<u8>,
    pub aeneas_archive_bytes: Vec<u8>,
    pub sandbox_profile_bytes: Vec<u8>,
    pub reviewer_assignments_bytes: Vec<u8>,
    pub ordered_receipts: Vec<SourceReceiptEnvelope>,
    pub ordered_verification_profiles: Vec<FixtureVerificationProfile>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SubjectIdentity {
    pub schema: String,
    pub subject_class: SourceSubjectClass,
    pub subject_id: String,
    pub byte_length: u64,
    pub sha256: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PreparationDriverRequestIdentity {
    pub schema: String,
    pub request_schema: String,
    pub attempt_id: String,
    pub evaluation_time_utc: String,
    pub machine_policy_sha256: String,
    pub ordered_subject_identities: Vec<SubjectIdentity>,
    pub ordered_receipt_sha256: Vec<String>,
    pub ordered_verification_profile_sha256: Vec<String>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PreparationDriverStage {
    RequestShape,
    SubjectBounds,
    SubjectBinding,
    ProfileBinding,
    Signature,
    Collector,
    FactBinding,
    Decision,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum PreparationDriverCode {
    InvalidSchema,
    InvalidIdentifier,
    InvalidTimestamp,
    InvalidCensus,
    InvalidOrder,
    DuplicateEntry,
    LengthOutOfBounds,
    LengthMismatch,
    DigestMismatch,
    BindingMismatch,
    ParseFailed,
    ReserializationMismatch,
    ProfileMissing,
    ProfileNotYetValid,
    ProfileExpired,
    WindowMismatch,
    ProducerReviewerCollision,
    DecisionNotAccepted,
    KeyEncodingInvalid,
    KeyDigestMismatch,
    SignatureEncodingInvalid,
    SignatureHighS,
    SignatureInvalid,
    CollectorFailed,
    FactRoleMismatch,
    FactPolicyMismatch,
    FactEntryMismatch,
    FactPlatformMismatch,
    FactDigestRejected,
    InternalInvariant,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PreparationDriverIssue {
    pub schema: String,
    pub stage: PreparationDriverStage,
    pub subject_class: Option<SourceSubjectClass>,
    pub code: PreparationDriverCode,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PreparationDriverPreIdentityRejection {
    pub schema: String,
    pub stage: PreparationDriverStage,
    pub subject_class: Option<SourceSubjectClass>,
    pub code: PreparationDriverCode,
    pub materialization_authorized: bool,
    pub capture_authorized: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PreparationDriverDecision {
    pub schema: String,
    pub request_identity_sha256: String,
    pub ordered_receipt_sha256: Vec<String>,
    pub ordered_verification_profile_sha256: Vec<String>,
    pub ordered_host_fact_sha256: Vec<String>,
    pub declared_evaluation_time_utc: String,
    pub fixture_correspondence_valid: bool,
    pub materialization_authorized: bool,
    pub capture_authorized: bool,
    pub ordered_issues: Vec<PreparationDriverIssue>,
}

#[derive(Clone, Copy)]
enum BindingMode {
    Production,
    #[cfg(test)]
    Test,
}

struct PreparedRequest {
    policy: MachinePolicyCandidate,
    evaluation_time_utc: String,
    request_identity_sha256: String,
    ordered_receipt_sha256: Vec<String>,
    ordered_profile_sha256: Vec<String>,
}

struct SubjectView<'a> {
    class: SourceSubjectClass,
    id: String,
    bytes: &'a [u8],
}

pub fn serialize_preparation_driver_request_json(
    request: &PreparationDriverRequest,
) -> Result<Vec<u8>, serde_json::Error> {
    serde_json::to_vec(request)
}

pub fn deserialize_preparation_driver_request_json(
    bytes: &[u8],
) -> Result<PreparationDriverRequest, serde_json::Error> {
    let request: PreparationDriverRequest = serde_json::from_slice(bytes)?;
    if serde_json::to_vec(&request)? != bytes {
        return Err(<serde_json::Error as serde::de::Error>::custom(
            "preparation driver request is not canonical compact JSON",
        ));
    }
    Ok(request)
}

pub fn source_receipt_signature_preimage(
    body: &SourceReceiptBody,
) -> Result<Vec<u8>, serde_json::Error> {
    domain_preimage(SOURCE_RECEIPT_SIGNATURE_DOMAIN, body)
}

pub fn source_receipt_envelope_sha256(
    envelope: &SourceReceiptEnvelope,
) -> Result<String, serde_json::Error> {
    domain_digest(SOURCE_RECEIPT_ENVELOPE_DIGEST_DOMAIN, envelope)
}

pub fn fixture_verification_profile_sha256(
    profile: &FixtureVerificationProfile,
) -> Result<String, serde_json::Error> {
    domain_digest(FIXTURE_VERIFICATION_PROFILE_DIGEST_DOMAIN, profile)
}

pub fn preparation_driver_request_identity_sha256(
    identity: &PreparationDriverRequestIdentity,
) -> Result<String, serde_json::Error> {
    domain_digest(PREPARATION_DRIVER_REQUEST_DIGEST_DOMAIN, identity)
}

pub fn executable_identity_fact_sha256(
    fact: &ExecutableIdentityFact,
) -> Result<String, serde_json::Error> {
    domain_digest(EXECUTABLE_FACT_DIGEST_DOMAIN, fact)
}

pub fn preparation_driver_decision_sha256(
    decision: &PreparationDriverDecision,
) -> Result<String, serde_json::Error> {
    domain_digest(PREPARATION_DRIVER_DECISION_DIGEST_DOMAIN, decision)
}

pub fn evaluate_preparation_driver(
    request: &PreparationDriverRequest,
) -> Result<PreparationDriverDecision, PreparationDriverPreIdentityRejection> {
    let (prepared, issues) = prepare_request(request, BindingMode::Production)?;
    if !issues.is_empty() {
        return Ok(decision(prepared, Vec::new(), issues));
    }

    let mut fact_digests = Vec::new();
    let mut fact_issues = Vec::new();
    for role in HostExecutableRole::ALL.iter().copied() {
        let fact = match collect_executable_identity_fact(&prepared.policy, role) {
            Ok(fact) => fact,
            Err(_) => {
                push_issue(
                    &mut fact_issues,
                    PreparationDriverStage::Collector,
                    None,
                    PreparationDriverCode::CollectorFailed,
                );
                break;
            }
        };
        if let Some(code) = validate_fact(&prepared.policy, role, &fact) {
            push_issue(
                &mut fact_issues,
                PreparationDriverStage::FactBinding,
                None,
                code,
            );
            break;
        }
        fact_digests.push(infallible_domain_digest(
            EXECUTABLE_FACT_DIGEST_DOMAIN,
            &fact,
        ));
    }
    if fact_digests.len() != HostExecutableRole::ALL.len() && fact_issues.is_empty() {
        push_issue(
            &mut fact_issues,
            PreparationDriverStage::Decision,
            None,
            PreparationDriverCode::InternalInvariant,
        );
    }
    Ok(decision(prepared, fact_digests, fact_issues))
}

fn prepare_request(
    request: &PreparationDriverRequest,
    mode: BindingMode,
) -> Result<(PreparedRequest, Vec<PreparationDriverIssue>), PreparationDriverPreIdentityRejection> {
    pre_identity_checks(request, mode)?;

    let subjects = subject_views(request);
    let subject_identities = subjects
        .iter()
        .map(|subject| SubjectIdentity {
            schema: SUBJECT_IDENTITY_SCHEMA.to_string(),
            subject_class: subject.class,
            subject_id: subject.id.clone(),
            byte_length: subject.bytes.len() as u64,
            sha256: hex_sha256(subject.bytes),
        })
        .collect::<Vec<_>>();
    let receipt_digests = request
        .ordered_receipts
        .iter()
        .map(|receipt| infallible_domain_digest(SOURCE_RECEIPT_ENVELOPE_DIGEST_DOMAIN, receipt))
        .collect::<Vec<_>>();
    let profile_digests = request
        .ordered_verification_profiles
        .iter()
        .map(|profile| {
            infallible_domain_digest(FIXTURE_VERIFICATION_PROFILE_DIGEST_DOMAIN, profile)
        })
        .collect::<Vec<_>>();
    let policy_digest = infallible_machine_policy_digest(&request.machine_policy);
    let identity = PreparationDriverRequestIdentity {
        schema: PREPARATION_DRIVER_REQUEST_IDENTITY_SCHEMA.to_string(),
        request_schema: request.schema.clone(),
        attempt_id: request.attempt_id.clone(),
        evaluation_time_utc: request.evaluation_time_utc.clone(),
        machine_policy_sha256: policy_digest.clone(),
        ordered_subject_identities: subject_identities.clone(),
        ordered_receipt_sha256: receipt_digests.clone(),
        ordered_verification_profile_sha256: profile_digests.clone(),
    };
    let request_identity_sha256 =
        infallible_domain_digest(PREPARATION_DRIVER_REQUEST_DIGEST_DOMAIN, &identity);

    let mut issues = Vec::new();
    let parsed_policy =
        match serde_json::from_slice::<MachinePolicyCandidate>(&request.machine_policy_bytes) {
            Ok(policy) => Some(policy),
            Err(_) => {
                push_issue(
                    &mut issues,
                    PreparationDriverStage::SubjectBinding,
                    Some(SourceSubjectClass::MachinePolicy),
                    PreparationDriverCode::ParseFailed,
                );
                None
            }
        };
    if let Some(policy) = parsed_policy.as_ref() {
        if serde_json::to_vec(policy).ok().as_deref()
            != Some(request.machine_policy_bytes.as_slice())
        {
            push_issue(
                &mut issues,
                PreparationDriverStage::SubjectBinding,
                Some(SourceSubjectClass::MachinePolicy),
                PreparationDriverCode::ReserializationMismatch,
            );
        }
        if policy != &request.machine_policy
            || !validate_machine_policy_candidate(policy).is_empty()
        {
            push_issue(
                &mut issues,
                PreparationDriverStage::SubjectBinding,
                Some(SourceSubjectClass::MachinePolicy),
                PreparationDriverCode::BindingMismatch,
            );
        }
    }
    if STATE_SLICE != "phase-792-hsai-native-transcript-descriptor-relative-collector" {
        push_issue(
            &mut issues,
            PreparationDriverStage::SubjectBinding,
            None,
            PreparationDriverCode::InternalInvariant,
        );
    }

    let reviewers =
        match serde_json::from_slice::<ReviewerAssignments>(&request.reviewer_assignments_bytes) {
            Ok(reviewers) => Some(reviewers),
            Err(_) => {
                push_issue(
                    &mut issues,
                    PreparationDriverStage::SubjectBinding,
                    Some(SourceSubjectClass::ReviewerAssignments),
                    PreparationDriverCode::ParseFailed,
                );
                None
            }
        };
    if let Some(reviewers) = reviewers.as_ref() {
        if serde_json::to_vec(reviewers).ok().as_deref()
            != Some(request.reviewer_assignments_bytes.as_slice())
        {
            push_issue(
                &mut issues,
                PreparationDriverStage::SubjectBinding,
                Some(SourceSubjectClass::ReviewerAssignments),
                PreparationDriverCode::ReserializationMismatch,
            );
        }
        validate_reviewer_assignments(reviewers, &mut issues);
    }

    validate_rust_manifest(&request.rust_toolchain_manifest_bytes, &mut issues);
    validate_charon_manifest(&request.charon_source_manifest_bytes, &mut issues);
    validate_subject_bindings(
        request,
        mode,
        &subjects,
        &subject_identities,
        &policy_digest,
        reviewers.as_ref(),
        &mut issues,
    );
    validate_profiles_and_signatures(request, reviewers.as_ref(), &mut issues);

    sort_issues(&mut issues);
    Ok((
        PreparedRequest {
            policy: parsed_policy.unwrap_or_else(|| request.machine_policy.clone()),
            evaluation_time_utc: request.evaluation_time_utc.clone(),
            request_identity_sha256,
            ordered_receipt_sha256: receipt_digests,
            ordered_profile_sha256: profile_digests,
        },
        issues,
    ))
}

fn pre_identity_checks(
    request: &PreparationDriverRequest,
    mode: BindingMode,
) -> Result<(), PreparationDriverPreIdentityRejection> {
    if request.schema != PREPARATION_DRIVER_REQUEST_SCHEMA {
        return Err(pre_rejection(
            PreparationDriverStage::RequestShape,
            None,
            PreparationDriverCode::InvalidSchema,
        ));
    }
    for receipt in &request.ordered_receipts {
        if receipt.schema != SOURCE_RECEIPT_ENVELOPE_SCHEMA
            || receipt.unsigned_body.schema != SOURCE_RECEIPT_BODY_SCHEMA
        {
            return Err(pre_rejection(
                PreparationDriverStage::RequestShape,
                None,
                PreparationDriverCode::InvalidSchema,
            ));
        }
    }
    if request
        .ordered_verification_profiles
        .iter()
        .any(|profile| profile.schema != FIXTURE_VERIFICATION_PROFILE_SCHEMA)
    {
        return Err(pre_rejection(
            PreparationDriverStage::RequestShape,
            None,
            PreparationDriverCode::InvalidSchema,
        ));
    }

    if !is_identifier(&request.attempt_id) || !is_identifier(&request.machine_policy.policy_id) {
        return Err(pre_rejection(
            PreparationDriverStage::RequestShape,
            None,
            PreparationDriverCode::InvalidIdentifier,
        ));
    }
    for receipt in &request.ordered_receipts {
        let body = &receipt.unsigned_body;
        if [
            body.receipt_id.as_str(),
            body.attempt_id.as_str(),
            body.subject_id.as_str(),
            body.producer_id.as_str(),
            body.reviewer_id.as_str(),
            body.reviewer_key_id.as_str(),
        ]
        .iter()
        .any(|value| !is_identifier(value))
        {
            return Err(pre_rejection(
                PreparationDriverStage::RequestShape,
                None,
                PreparationDriverCode::InvalidIdentifier,
            ));
        }
    }
    for profile in &request.ordered_verification_profiles {
        if [
            profile.profile_id.as_str(),
            profile.attempt_id.as_str(),
            profile.reviewer_id.as_str(),
            profile.key_id.as_str(),
        ]
        .iter()
        .any(|value| !is_identifier(value))
        {
            return Err(pre_rejection(
                PreparationDriverStage::RequestShape,
                None,
                PreparationDriverCode::InvalidIdentifier,
            ));
        }
    }

    if !is_utc_timestamp(&request.evaluation_time_utc) {
        return Err(pre_rejection(
            PreparationDriverStage::RequestShape,
            None,
            PreparationDriverCode::InvalidTimestamp,
        ));
    }
    for receipt in &request.ordered_receipts {
        let body = &receipt.unsigned_body;
        if !is_utc_timestamp(&body.reviewed_at_utc)
            || !is_utc_timestamp(&body.not_before_utc)
            || !is_utc_timestamp(&body.expires_at_utc)
        {
            return Err(pre_rejection(
                PreparationDriverStage::RequestShape,
                None,
                PreparationDriverCode::InvalidTimestamp,
            ));
        }
    }
    if request.ordered_verification_profiles.iter().any(|profile| {
        !is_utc_timestamp(&profile.not_before_utc) || !is_utc_timestamp(&profile.expires_at_utc)
    }) {
        return Err(pre_rejection(
            PreparationDriverStage::RequestShape,
            None,
            PreparationDriverCode::InvalidTimestamp,
        ));
    }

    if request.ordered_receipts.len() != SourceSubjectClass::INPUTS.len()
        || request.ordered_verification_profiles.is_empty()
        || request.ordered_verification_profiles.len() > SourceSubjectClass::INPUTS.len()
    {
        return Err(pre_rejection(
            PreparationDriverStage::RequestShape,
            None,
            PreparationDriverCode::InvalidCensus,
        ));
    }

    let expected_classes = SourceSubjectClass::INPUTS
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    let receipt_classes = request
        .ordered_receipts
        .iter()
        .map(|receipt| receipt.unsigned_body.subject_class)
        .collect::<BTreeSet<_>>();
    let referenced_key_ids = request
        .ordered_receipts
        .iter()
        .map(|receipt| receipt.unsigned_body.reviewer_key_id.as_str())
        .collect::<BTreeSet<_>>();
    let profile_key_ids = request
        .ordered_verification_profiles
        .iter()
        .map(|profile| profile.key_id.as_str())
        .collect::<BTreeSet<_>>();
    if receipt_classes != expected_classes || profile_key_ids != referenced_key_ids {
        return Err(pre_rejection(
            PreparationDriverStage::RequestShape,
            None,
            PreparationDriverCode::InvalidCensus,
        ));
    }
    for profile in &request.ordered_verification_profiles {
        let referenced_classes = request
            .ordered_receipts
            .iter()
            .filter(|receipt| receipt.unsigned_body.reviewer_key_id == profile.key_id)
            .map(|receipt| receipt.unsigned_body.subject_class)
            .collect::<BTreeSet<_>>();
        let allowed_classes = profile
            .allowed_subject_classes
            .iter()
            .copied()
            .collect::<BTreeSet<_>>();
        if allowed_classes != referenced_classes {
            return Err(pre_rejection(
                PreparationDriverStage::RequestShape,
                None,
                PreparationDriverCode::InvalidCensus,
            ));
        }
    }

    let mut receipt_ids = BTreeSet::new();
    for (index, receipt) in request.ordered_receipts.iter().enumerate() {
        let class = receipt.unsigned_body.subject_class;
        if class != SourceSubjectClass::INPUTS[index] || !class.is_input() {
            return Err(pre_rejection(
                PreparationDriverStage::RequestShape,
                None,
                PreparationDriverCode::InvalidOrder,
            ));
        }
        if !receipt_ids.insert(receipt.unsigned_body.receipt_id.as_str()) {
            return Err(pre_rejection(
                PreparationDriverStage::RequestShape,
                None,
                PreparationDriverCode::DuplicateEntry,
            ));
        }
    }

    let mut profile_ids = BTreeSet::new();
    let mut profile_key_ids = BTreeSet::new();
    let mut previous_key: Option<&str> = None;
    for profile in &request.ordered_verification_profiles {
        if previous_key.is_some_and(|key| key >= profile.key_id.as_str()) {
            return Err(pre_rejection(
                PreparationDriverStage::RequestShape,
                None,
                if previous_key == Some(profile.key_id.as_str()) {
                    PreparationDriverCode::DuplicateEntry
                } else {
                    PreparationDriverCode::InvalidOrder
                },
            ));
        }
        previous_key = Some(&profile.key_id);
        if !profile_ids.insert(profile.profile_id.as_str())
            || !profile_key_ids.insert(profile.key_id.as_str())
        {
            return Err(pre_rejection(
                PreparationDriverStage::RequestShape,
                None,
                PreparationDriverCode::DuplicateEntry,
            ));
        }
        if !is_unique_input_subsequence(&profile.allowed_subject_classes) {
            return Err(pre_rejection(
                PreparationDriverStage::RequestShape,
                None,
                PreparationDriverCode::InvalidOrder,
            ));
        }
    }

    if let Some(class) = unbounded_metadata_subject(request) {
        return Err(pre_rejection(
            PreparationDriverStage::SubjectBounds,
            Some(class),
            PreparationDriverCode::LengthOutOfBounds,
        ));
    }

    for subject in subject_views(request) {
        let accepted = match subject.class {
            SourceSubjectClass::ExecutableRegistryDocument => match mode {
                BindingMode::Production => subject.bytes.len() == REGISTRY_DOCUMENT_BYTE_LENGTH,
                #[cfg(test)]
                BindingMode::Test => subject.bytes.len() == TEST_REGISTRY_BYTES.len(),
            },
            SourceSubjectClass::OperationOrderDocument
            | SourceSubjectClass::RustToolchainManifest
            | SourceSubjectClass::ReviewerAssignments => {
                !subject.bytes.is_empty() && subject.bytes.len() <= MAX_SMALL_SUBJECT_BYTES
            }
            SourceSubjectClass::MachinePolicy => {
                !subject.bytes.is_empty()
                    && subject.bytes.len() <= MAX_SMALL_SUBJECT_BYTES
                    && machine_policy_shape_is_bounded(&request.machine_policy)
                    && serde_json::to_vec(&request.machine_policy)
                        .is_ok_and(|bytes| bytes.len() <= MAX_SMALL_SUBJECT_BYTES)
            }
            SourceSubjectClass::CharonSourceTree => {
                !subject.bytes.is_empty() && subject.bytes.len() <= MAX_CHARON_MANIFEST_BYTES
            }
            SourceSubjectClass::AeneasArchive => match mode {
                BindingMode::Production => subject.bytes.len() as u64 == AENEAS_ARCHIVE_BYTE_LENGTH,
                #[cfg(test)]
                BindingMode::Test => subject.bytes.len() == TEST_AENEAS_BYTES.len(),
            },
            SourceSubjectClass::SandboxProfile => {
                subject.bytes.len() == SANDBOX_PROFILE_BYTES.len()
            }
            SourceSubjectClass::OwnedTool
            | SourceSubjectClass::PackagedTarget
            | SourceSubjectClass::BuiltTarget => false,
        };
        if !accepted {
            return Err(pre_rejection(
                PreparationDriverStage::SubjectBounds,
                Some(subject.class),
                PreparationDriverCode::LengthOutOfBounds,
            ));
        }
    }
    Ok(())
}

fn subject_views(request: &PreparationDriverRequest) -> Vec<SubjectView<'_>> {
    vec![
        SubjectView {
            class: SourceSubjectClass::ExecutableRegistryDocument,
            id: EXECUTABLE_REGISTRY_ID.to_string(),
            bytes: &request.registry_document_bytes,
        },
        SubjectView {
            class: SourceSubjectClass::OperationOrderDocument,
            id: OPERATION_ORDER_SUBJECT_ID.to_string(),
            bytes: &request.operation_order_document_bytes,
        },
        SubjectView {
            class: SourceSubjectClass::MachinePolicy,
            id: request.machine_policy.policy_id.clone(),
            bytes: &request.machine_policy_bytes,
        },
        SubjectView {
            class: SourceSubjectClass::RustToolchainManifest,
            id: RUST_MANIFEST_SUBJECT_ID.to_string(),
            bytes: &request.rust_toolchain_manifest_bytes,
        },
        SubjectView {
            class: SourceSubjectClass::CharonSourceTree,
            id: CHARON_SOURCE_COMMIT.to_string(),
            bytes: &request.charon_source_manifest_bytes,
        },
        SubjectView {
            class: SourceSubjectClass::AeneasArchive,
            id: AENEAS_ARCHIVE_SUBJECT_ID.to_string(),
            bytes: &request.aeneas_archive_bytes,
        },
        SubjectView {
            class: SourceSubjectClass::SandboxProfile,
            id: SANDBOX_SUBJECT_ID.to_string(),
            bytes: &request.sandbox_profile_bytes,
        },
        SubjectView {
            class: SourceSubjectClass::ReviewerAssignments,
            id: request.attempt_id.clone(),
            bytes: &request.reviewer_assignments_bytes,
        },
    ]
}

fn validate_subject_bindings(
    request: &PreparationDriverRequest,
    mode: BindingMode,
    subjects: &[SubjectView<'_>],
    identities: &[SubjectIdentity],
    policy_digest: &str,
    reviewers: Option<&ReviewerAssignments>,
    issues: &mut Vec<PreparationDriverIssue>,
) {
    for ((receipt, subject), identity) in request
        .ordered_receipts
        .iter()
        .zip(subjects)
        .zip(identities)
    {
        let body = &receipt.unsigned_body;
        let (authority, revision) =
            expected_authority_revision(subject.class, request, identity, policy_digest);
        if body.attempt_id != request.attempt_id
            || body.subject_class != subject.class
            || body.subject_id != subject.id
            || body.declared_source_authority != authority
            || body.declared_source_revision != revision
        {
            push_issue(
                issues,
                PreparationDriverStage::SubjectBinding,
                Some(subject.class),
                PreparationDriverCode::BindingMismatch,
            );
        }
        if body.subject_byte_length != identity.byte_length {
            push_issue(
                issues,
                PreparationDriverStage::SubjectBinding,
                Some(subject.class),
                PreparationDriverCode::LengthMismatch,
            );
        }
        if body.subject_sha256 != identity.sha256 {
            push_issue(
                issues,
                PreparationDriverStage::SubjectBinding,
                Some(subject.class),
                PreparationDriverCode::DigestMismatch,
            );
        }
        if !is_source_authority(&body.declared_source_authority) {
            push_issue(
                issues,
                PreparationDriverStage::SubjectBinding,
                Some(subject.class),
                PreparationDriverCode::BindingMismatch,
            );
        }
        if body.decision != ReviewDecision::Accepted {
            push_issue(
                issues,
                PreparationDriverStage::SubjectBinding,
                Some(subject.class),
                PreparationDriverCode::DecisionNotAccepted,
            );
        }
    }

    let expected_registry = match mode {
        BindingMode::Production => REGISTRY_DOCUMENT_SHA256.to_string(),
        #[cfg(test)]
        BindingMode::Test => hex_sha256(TEST_REGISTRY_BYTES),
    };
    if identities[0].sha256 != expected_registry {
        push_issue(
            issues,
            PreparationDriverStage::SubjectBinding,
            Some(SourceSubjectClass::ExecutableRegistryDocument),
            PreparationDriverCode::DigestMismatch,
        );
    }
    let expected_order = match mode {
        BindingMode::Production => OPERATION_ORDER_SHA256.to_string(),
        #[cfg(test)]
        BindingMode::Test => hex_sha256(TEST_OPERATION_ORDER_BYTES),
    };
    if identities[1].sha256 != expected_order {
        push_issue(
            issues,
            PreparationDriverStage::SubjectBinding,
            Some(SourceSubjectClass::OperationOrderDocument),
            PreparationDriverCode::DigestMismatch,
        );
    }
    let expected_archive = match mode {
        BindingMode::Production => AENEAS_ARCHIVE_SHA256.to_string(),
        #[cfg(test)]
        BindingMode::Test => hex_sha256(TEST_AENEAS_BYTES),
    };
    if identities[5].sha256 != expected_archive {
        push_issue(
            issues,
            PreparationDriverStage::SubjectBinding,
            Some(SourceSubjectClass::AeneasArchive),
            PreparationDriverCode::DigestMismatch,
        );
    }
    if request.sandbox_profile_bytes != SANDBOX_PROFILE_BYTES
        || identities[6].sha256 != SANDBOX_PROFILE_SHA256
    {
        push_issue(
            issues,
            PreparationDriverStage::SubjectBinding,
            Some(SourceSubjectClass::SandboxProfile),
            PreparationDriverCode::DigestMismatch,
        );
    }

    if let Some(reviewers) = reviewers {
        let machine_receipt = &request.ordered_receipts[2].unsigned_body;
        if machine_receipt.producer_id != request.machine_policy.review.policy_object_producer_id
            || machine_receipt.reviewer_id != request.machine_policy.review.reviewer_id
            || machine_receipt.reviewed_at_utc != request.machine_policy.review.reviewed_at_utc
            || request.machine_policy.review.decision != ReviewDecision::Accepted
            || request.machine_policy.review.reviewer_id != reviewers.machine_policy_reviewer_id
        {
            push_issue(
                issues,
                PreparationDriverStage::SubjectBinding,
                Some(SourceSubjectClass::MachinePolicy),
                PreparationDriverCode::BindingMismatch,
            );
        }
        for receipt in &request.ordered_receipts {
            let expected_reviewer =
                if receipt.unsigned_body.subject_class == SourceSubjectClass::MachinePolicy {
                    reviewers.machine_policy_reviewer_id.as_str()
                } else {
                    reviewers.fixture_reviewer_id.as_str()
                };
            if receipt.unsigned_body.reviewer_id != expected_reviewer {
                push_issue(
                    issues,
                    PreparationDriverStage::SubjectBinding,
                    Some(receipt.unsigned_body.subject_class),
                    PreparationDriverCode::BindingMismatch,
                );
            }
            if receipt.unsigned_body.producer_id == receipt.unsigned_body.reviewer_id {
                push_issue(
                    issues,
                    PreparationDriverStage::SubjectBinding,
                    Some(receipt.unsigned_body.subject_class),
                    PreparationDriverCode::ProducerReviewerCollision,
                );
            }
        }
    }
}

fn expected_authority_revision(
    class: SourceSubjectClass,
    request: &PreparationDriverRequest,
    identity: &SubjectIdentity,
    policy_digest: &str,
) -> (String, String) {
    match class {
        SourceSubjectClass::ExecutableRegistryDocument => (
            REGISTRY_DECLARED_SOURCE_AUTHORITY.to_string(),
            "phase787".to_string(),
        ),
        SourceSubjectClass::OperationOrderDocument => (
            OPERATION_ORDER_DECLARED_SOURCE_AUTHORITY.to_string(),
            "phase778".to_string(),
        ),
        SourceSubjectClass::MachinePolicy => (
            MACHINE_POLICY_DECLARED_SOURCE_AUTHORITY.to_string(),
            policy_digest.to_string(),
        ),
        SourceSubjectClass::RustToolchainManifest => (
            RUST_MANIFEST_DECLARED_SOURCE_AUTHORITY.to_string(),
            identity.sha256.clone(),
        ),
        SourceSubjectClass::CharonSourceTree => (
            CHARON_DECLARED_SOURCE_AUTHORITY.to_string(),
            CHARON_SOURCE_COMMIT.to_string(),
        ),
        SourceSubjectClass::AeneasArchive => (
            AENEAS_ARCHIVE_URL.to_string(),
            AENEAS_ARCHIVE_SOURCE_REVISION.to_string(),
        ),
        SourceSubjectClass::SandboxProfile => (
            SANDBOX_DECLARED_SOURCE_AUTHORITY.to_string(),
            "phase776".to_string(),
        ),
        SourceSubjectClass::ReviewerAssignments => (
            REVIEWER_ASSIGNMENTS_DECLARED_SOURCE_AUTHORITY.to_string(),
            identity.sha256.clone(),
        ),
        SourceSubjectClass::OwnedTool
        | SourceSubjectClass::PackagedTarget
        | SourceSubjectClass::BuiltTarget => (String::new(), request.attempt_id.clone()),
    }
}

fn validate_profiles_and_signatures(
    request: &PreparationDriverRequest,
    reviewers: Option<&ReviewerAssignments>,
    issues: &mut Vec<PreparationDriverIssue>,
) {
    for receipt in &request.ordered_receipts {
        let body = &receipt.unsigned_body;
        let class = body.subject_class;
        let profile = request
            .ordered_verification_profiles
            .iter()
            .find(|profile| profile.key_id == body.reviewer_key_id);
        let Some(profile) = profile else {
            push_issue(
                issues,
                PreparationDriverStage::ProfileBinding,
                Some(class),
                PreparationDriverCode::ProfileMissing,
            );
            continue;
        };
        let expected_reviewer = reviewers.map(|reviewers| {
            if class == SourceSubjectClass::MachinePolicy {
                reviewers.machine_policy_reviewer_id.as_str()
            } else {
                reviewers.fixture_reviewer_id.as_str()
            }
        });
        if profile.attempt_id != request.attempt_id
            || profile.reviewer_id != body.reviewer_id
            || expected_reviewer != Some(profile.reviewer_id.as_str())
            || !profile.allowed_subject_classes.contains(&class)
        {
            push_issue(
                issues,
                PreparationDriverStage::ProfileBinding,
                Some(class),
                PreparationDriverCode::BindingMismatch,
            );
        }
        if profile.not_before_utc > body.not_before_utc
            || body.not_before_utc > body.reviewed_at_utc
            || body.reviewed_at_utc > request.evaluation_time_utc
            || request.evaluation_time_utc >= body.expires_at_utc
            || body.expires_at_utc > profile.expires_at_utc
            || profile.not_before_utc >= profile.expires_at_utc
            || body.not_before_utc >= body.expires_at_utc
        {
            let code = if request.evaluation_time_utc < body.not_before_utc
                || request.evaluation_time_utc < profile.not_before_utc
            {
                PreparationDriverCode::ProfileNotYetValid
            } else if request.evaluation_time_utc >= body.expires_at_utc
                || request.evaluation_time_utc >= profile.expires_at_utc
            {
                PreparationDriverCode::ProfileExpired
            } else {
                PreparationDriverCode::WindowMismatch
            };
            push_issue(
                issues,
                PreparationDriverStage::ProfileBinding,
                Some(class),
                code,
            );
        }

        let key_bytes = match decode_lower_hex(&profile.compressed_sec1_key_hex, 33) {
            Some(bytes) => bytes,
            None => {
                push_issue(
                    issues,
                    PreparationDriverStage::ProfileBinding,
                    Some(class),
                    PreparationDriverCode::KeyEncodingInvalid,
                );
                continue;
            }
        };
        if !matches!(key_bytes.first(), Some(0x02 | 0x03)) {
            push_issue(
                issues,
                PreparationDriverStage::ProfileBinding,
                Some(class),
                PreparationDriverCode::KeyEncodingInvalid,
            );
            continue;
        }
        if hex_sha256(&key_bytes) != profile.key_sha256 {
            push_issue(
                issues,
                PreparationDriverStage::ProfileBinding,
                Some(class),
                PreparationDriverCode::KeyDigestMismatch,
            );
            continue;
        }
        let verifying_key = match VerifyingKey::from_sec1_bytes(&key_bytes) {
            Ok(key) => key,
            Err(_) => {
                push_issue(
                    issues,
                    PreparationDriverStage::ProfileBinding,
                    Some(class),
                    PreparationDriverCode::KeyEncodingInvalid,
                );
                continue;
            }
        };
        let signature_bytes = match decode_lower_hex(&receipt.signature_hex, 64) {
            Some(bytes) => bytes,
            None => {
                push_issue(
                    issues,
                    PreparationDriverStage::Signature,
                    Some(class),
                    PreparationDriverCode::SignatureEncodingInvalid,
                );
                continue;
            }
        };
        let signature = match Signature::from_slice(&signature_bytes) {
            Ok(signature) => signature,
            Err(_) => {
                push_issue(
                    issues,
                    PreparationDriverStage::Signature,
                    Some(class),
                    PreparationDriverCode::SignatureEncodingInvalid,
                );
                continue;
            }
        };
        if signature.normalize_s().is_some() {
            push_issue(
                issues,
                PreparationDriverStage::Signature,
                Some(class),
                PreparationDriverCode::SignatureHighS,
            );
            continue;
        }
        let preimage = infallible_domain_preimage(SOURCE_RECEIPT_SIGNATURE_DOMAIN, body);
        if verifying_key.verify(&preimage, &signature).is_err() {
            push_issue(
                issues,
                PreparationDriverStage::Signature,
                Some(class),
                PreparationDriverCode::SignatureInvalid,
            );
        }
    }
}

fn validate_rust_manifest(bytes: &[u8], issues: &mut Vec<PreparationDriverIssue>) {
    let manifest = match serde_json::from_slice::<RustToolchainManifest>(bytes) {
        Ok(manifest) => manifest,
        Err(_) => {
            push_issue(
                issues,
                PreparationDriverStage::SubjectBinding,
                Some(SourceSubjectClass::RustToolchainManifest),
                PreparationDriverCode::ParseFailed,
            );
            return;
        }
    };
    if serde_json::to_vec(&manifest).ok().as_deref() != Some(bytes) {
        push_issue(
            issues,
            PreparationDriverStage::SubjectBinding,
            Some(SourceSubjectClass::RustToolchainManifest),
            PreparationDriverCode::ReserializationMismatch,
        );
    }
    let expected_components = RUST_COMPONENTS
        .iter()
        .map(|(component, target, xz_sha256)| RustToolchainComponent {
            component: (*component).to_string(),
            target: (*target).to_string(),
            xz_sha256: (*xz_sha256).to_string(),
        })
        .collect::<Vec<_>>();
    if manifest.schema != RUST_TOOLCHAIN_MANIFEST_SCHEMA
        || manifest.channel != RUST_CHANNEL
        || manifest.manifest_url != RUST_MANIFEST_URL
        || manifest.manifest_sha256 != RUST_MANIFEST_SHA256
        || manifest.charon_rust_toolchain_sha256 != CHARON_RUST_TOOLCHAIN_SHA256
        || manifest.rustc_identity != RUSTC_IDENTITY
        || manifest.rustc_commit != RUSTC_COMMIT
        || manifest.ordered_components != expected_components
    {
        push_issue(
            issues,
            PreparationDriverStage::SubjectBinding,
            Some(SourceSubjectClass::RustToolchainManifest),
            PreparationDriverCode::BindingMismatch,
        );
    }
}

fn validate_charon_manifest(bytes: &[u8], issues: &mut Vec<PreparationDriverIssue>) {
    let manifest = match serde_json::from_slice::<CharonSourceManifest>(bytes) {
        Ok(manifest) => manifest,
        Err(_) => {
            push_issue(
                issues,
                PreparationDriverStage::SubjectBinding,
                Some(SourceSubjectClass::CharonSourceTree),
                PreparationDriverCode::ParseFailed,
            );
            return;
        }
    };
    if serde_json::to_vec(&manifest).ok().as_deref() != Some(bytes) {
        push_issue(
            issues,
            PreparationDriverStage::SubjectBinding,
            Some(SourceSubjectClass::CharonSourceTree),
            PreparationDriverCode::ReserializationMismatch,
        );
    }
    let expected_files = CHARON_SOURCE_FILES
        .iter()
        .map(|(relative_path, sha256)| (relative_path.to_string(), sha256.to_string()))
        .collect::<Vec<_>>();
    let actual_files = manifest
        .ordered_files
        .iter()
        .map(|file| (file.relative_path.clone(), file.sha256.clone()))
        .collect::<Vec<_>>();
    if manifest.schema != CHARON_SOURCE_MANIFEST_SCHEMA
        || manifest.commit != CHARON_SOURCE_COMMIT
        || actual_files != expected_files
        || manifest
            .ordered_files
            .iter()
            .any(|file| file.byte_length == 0)
    {
        push_issue(
            issues,
            PreparationDriverStage::SubjectBinding,
            Some(SourceSubjectClass::CharonSourceTree),
            PreparationDriverCode::BindingMismatch,
        );
    }
}

fn validate_reviewer_assignments(
    reviewers: &ReviewerAssignments,
    issues: &mut Vec<PreparationDriverIssue>,
) {
    let roles = [
        reviewers.machine_policy_reviewer_id.as_str(),
        reviewers.capture_operator_id.as_str(),
        reviewers.fixture_reviewer_id.as_str(),
        reviewers.grammar_reviewer_id.as_str(),
    ];
    if roles.iter().any(|role| !is_identifier(role))
        || roles.iter().copied().collect::<BTreeSet<_>>().len() != roles.len()
    {
        push_issue(
            issues,
            PreparationDriverStage::SubjectBinding,
            Some(SourceSubjectClass::ReviewerAssignments),
            PreparationDriverCode::BindingMismatch,
        );
    }
}

fn validate_fact(
    policy: &MachinePolicyCandidate,
    role: HostExecutableRole,
    fact: &ExecutableIdentityFact,
) -> Option<PreparationDriverCode> {
    if fact.schema != EXECUTABLE_FACT_SCHEMA || fact.role_id != role {
        return Some(PreparationDriverCode::FactRoleMismatch);
    }
    let Some(entry) = policy.entries.iter().find(|entry| entry.role_id == role) else {
        return Some(PreparationDriverCode::FactEntryMismatch);
    };
    let policy_digest = infallible_machine_policy_digest(policy);
    let entry_digest = match machine_policy_entry_sha256(entry) {
        Ok(digest) => digest,
        Err(_) => return Some(PreparationDriverCode::InternalInvariant),
    };
    if fact.registry_id != policy.registry_id
        || fact.machine_policy_id != policy.policy_id
        || fact.machine_policy_sha256 != policy_digest
        || fact.decision != ReviewDecision::Accepted
    {
        return Some(PreparationDriverCode::FactPolicyMismatch);
    }
    if fact.policy_entry_sha256 != entry_digest
        || fact.acceptance_policy_id != entry.acceptance_policy_id
        || fact.requested_path != entry.requested_path
    {
        return Some(PreparationDriverCode::FactEntryMismatch);
    }
    if fact.declared_platform != policy.platform
        || fact.observed_platform.os != policy.platform.os
        || fact.observed_platform.arch != policy.platform.arch
    {
        return Some(PreparationDriverCode::FactPlatformMismatch);
    }
    if !entry.admitted_sha256.contains(&fact.observed_sha256)
        || fact.pre_read_metadata != fact.post_read_metadata
    {
        return Some(PreparationDriverCode::FactDigestRejected);
    }
    None
}

fn decision(
    prepared: PreparedRequest,
    fact_digests: Vec<String>,
    mut issues: Vec<PreparationDriverIssue>,
) -> PreparationDriverDecision {
    sort_issues(&mut issues);
    PreparationDriverDecision {
        schema: PREPARATION_DRIVER_DECISION_SCHEMA.to_string(),
        request_identity_sha256: prepared.request_identity_sha256,
        ordered_receipt_sha256: prepared.ordered_receipt_sha256,
        ordered_verification_profile_sha256: prepared.ordered_profile_sha256,
        ordered_host_fact_sha256: fact_digests,
        declared_evaluation_time_utc: prepared.evaluation_time_utc,
        fixture_correspondence_valid: issues.is_empty(),
        materialization_authorized: false,
        capture_authorized: false,
        ordered_issues: issues,
    }
}

fn push_issue(
    issues: &mut Vec<PreparationDriverIssue>,
    stage: PreparationDriverStage,
    subject_class: Option<SourceSubjectClass>,
    code: PreparationDriverCode,
) {
    issues.push(PreparationDriverIssue {
        schema: PREPARATION_DRIVER_ISSUE_SCHEMA.to_string(),
        stage,
        subject_class,
        code,
    });
}

fn sort_issues(issues: &mut Vec<PreparationDriverIssue>) {
    issues.sort();
    issues.dedup();
}

fn pre_rejection(
    stage: PreparationDriverStage,
    subject_class: Option<SourceSubjectClass>,
    code: PreparationDriverCode,
) -> PreparationDriverPreIdentityRejection {
    let subject_class = if stage == PreparationDriverStage::RequestShape {
        None
    } else {
        subject_class
    };
    PreparationDriverPreIdentityRejection {
        schema: PREPARATION_DRIVER_PRE_IDENTITY_REJECTION_SCHEMA.to_string(),
        stage,
        subject_class,
        code,
        materialization_authorized: false,
        capture_authorized: false,
    }
}

fn unbounded_metadata_subject(request: &PreparationDriverRequest) -> Option<SourceSubjectClass> {
    for receipt in &request.ordered_receipts {
        let body = &receipt.unsigned_body;
        if receipt.signature_hex.len() > 128
            || body.subject_sha256.len() > 64
            || body.declared_source_authority.len() > 512
            || body.declared_source_revision.len() > 128
        {
            return Some(body.subject_class);
        }
    }
    for profile in &request.ordered_verification_profiles {
        if profile.compressed_sec1_key_hex.len() > 66 || profile.key_sha256.len() > 64 {
            return profile.allowed_subject_classes.first().copied();
        }
    }
    None
}

fn machine_policy_shape_is_bounded(policy: &MachinePolicyCandidate) -> bool {
    if policy.entries.len() > HostExecutableRole::ALL.len()
        || policy.allowed_roots.len() > 32
        || policy.allowed_roots.iter().any(|root| root.len() > 4_096)
        || [
            policy.schema.as_str(),
            policy.policy_id.as_str(),
            policy.registry_id.as_str(),
            policy.registry_document_sha256.as_str(),
            policy.operation_order_sha256.as_str(),
            policy.platform.os.as_str(),
            policy.platform.arch.as_str(),
            policy.platform.product_version.as_str(),
            policy.platform.build_version.as_str(),
            policy.review.policy_object_producer_id.as_str(),
            policy.review.reviewer_id.as_str(),
            policy.review.reviewed_at_utc.as_str(),
        ]
        .iter()
        .any(|value| value.len() > 4_096)
    {
        return false;
    }
    policy.entries.iter().all(|entry| {
        entry.requested_path.len() <= 4_096
            && entry.acceptance_policy_id.len() <= 128
            && entry.allowed_owner_uids.len() <= 64
            && entry.admitted_sha256.len() <= 64
            && entry
                .admitted_sha256
                .iter()
                .all(|digest| digest.len() <= 64)
    })
}

fn is_unique_input_subsequence(classes: &[SourceSubjectClass]) -> bool {
    if classes.is_empty() {
        return false;
    }
    let mut previous = None;
    for class in classes {
        let Some(index) = SourceSubjectClass::INPUTS
            .iter()
            .position(|item| item == class)
        else {
            return false;
        };
        if previous.is_some_and(|previous| previous >= index) {
            return false;
        }
        previous = Some(index);
    }
    true
}

fn is_identifier(value: &str) -> bool {
    let bytes = value.as_bytes();
    if bytes.is_empty()
        || bytes.len() > 128
        || !bytes[0].is_ascii_lowercase() && !bytes[0].is_ascii_digit()
    {
        return false;
    }
    bytes[1..].iter().all(|byte| {
        byte.is_ascii_lowercase()
            || byte.is_ascii_digit()
            || matches!(*byte, b'.' | b'_' | b':' | b'-')
    })
}

fn is_source_authority(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 512
        && value
            .bytes()
            .all(|byte| byte.is_ascii_graphic() && !byte.is_ascii_whitespace())
}

fn is_utc_timestamp(value: &str) -> bool {
    let bytes = value.as_bytes();
    if bytes.len() != 20
        || bytes[4] != b'-'
        || bytes[7] != b'-'
        || bytes[10] != b'T'
        || bytes[13] != b':'
        || bytes[16] != b':'
        || bytes[19] != b'Z'
        || bytes.iter().enumerate().any(|(index, byte)| {
            !matches!(index, 4 | 7 | 10 | 13 | 16 | 19) && !byte.is_ascii_digit()
        })
    {
        return false;
    }
    let year = decimal(&bytes[0..4]);
    let month = decimal(&bytes[5..7]);
    let day = decimal(&bytes[8..10]);
    let hour = decimal(&bytes[11..13]);
    let minute = decimal(&bytes[14..16]);
    let second = decimal(&bytes[17..19]);
    if year == 0 || !(1..=12).contains(&month) || hour > 23 || minute > 59 || second > 59 {
        return false;
    }
    let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
    let max_day = match month {
        2 if leap => 29,
        2 => 28,
        4 | 6 | 9 | 11 => 30,
        _ => 31,
    };
    (1..=max_day).contains(&day)
}

fn decimal(bytes: &[u8]) -> u32 {
    bytes
        .iter()
        .fold(0, |value, byte| value * 10 + u32::from(byte - b'0'))
}

fn decode_lower_hex(value: &str, expected_bytes: usize) -> Option<Vec<u8>> {
    if value.len() != expected_bytes * 2
        || value
            .bytes()
            .any(|byte| !byte.is_ascii_digit() && !(b'a'..=b'f').contains(&byte))
    {
        return None;
    }
    value
        .as_bytes()
        .chunks_exact(2)
        .map(|pair| Some((hex_nibble(pair[0])? << 4) | hex_nibble(pair[1])?))
        .collect()
}

fn hex_nibble(byte: u8) -> Option<u8> {
    match byte {
        b'0'..=b'9' => Some(byte - b'0'),
        b'a'..=b'f' => Some(byte - b'a' + 10),
        _ => None,
    }
}

fn hex_sha256(bytes: &[u8]) -> String {
    encode_lower_hex(&Sha256::digest(bytes))
}

fn encode_lower_hex(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        output.push(char::from(HEX[(byte >> 4) as usize]));
        output.push(char::from(HEX[(byte & 0x0f) as usize]));
    }
    output
}

fn domain_preimage<T: Serialize>(domain: &[u8], value: &T) -> Result<Vec<u8>, serde_json::Error> {
    let bytes = serde_json::to_vec(value)?;
    let mut preimage = Vec::with_capacity(domain.len() + bytes.len());
    preimage.extend_from_slice(domain);
    preimage.extend_from_slice(&bytes);
    Ok(preimage)
}

fn infallible_domain_preimage<T: Serialize>(domain: &[u8], value: &T) -> Vec<u8> {
    domain_preimage(domain, value).expect("serializing a closed driver value cannot fail")
}

fn domain_digest<T: Serialize>(domain: &[u8], value: &T) -> Result<String, serde_json::Error> {
    Ok(hex_sha256(&domain_preimage(domain, value)?))
}

fn infallible_domain_digest<T: Serialize>(domain: &[u8], value: &T) -> String {
    domain_digest(domain, value).expect("serializing a closed driver value cannot fail")
}

fn infallible_machine_policy_digest(policy: &MachinePolicyCandidate) -> String {
    machine_policy_sha256(policy).expect("serializing a machine policy cannot fail")
}

#[cfg(test)]
const TEST_REGISTRY_BYTES: &[u8] = b"phase-794-registry-fixture\n";
#[cfg(test)]
const TEST_OPERATION_ORDER_BYTES: &[u8] = b"phase-794-operation-order-fixture\n";
#[cfg(test)]
const TEST_AENEAS_BYTES: &[u8] = b"phase-794-aeneas-archive-fixture\n";

#[cfg(test)]
fn evaluate_with_test_bindings<F>(
    request: &PreparationDriverRequest,
    mut collector: F,
) -> Result<PreparationDriverDecision, PreparationDriverPreIdentityRejection>
where
    F: FnMut(&MachinePolicyCandidate, HostExecutableRole) -> Result<ExecutableIdentityFact, ()>,
{
    let (prepared, issues) = prepare_request(request, BindingMode::Test)?;
    if !issues.is_empty() {
        return Ok(decision(prepared, Vec::new(), issues));
    }

    let mut fact_digests = Vec::new();
    let mut fact_issues = Vec::new();
    for role in HostExecutableRole::ALL.iter().copied() {
        let fact = match collector(&prepared.policy, role) {
            Ok(fact) => fact,
            Err(()) => {
                push_issue(
                    &mut fact_issues,
                    PreparationDriverStage::Collector,
                    None,
                    PreparationDriverCode::CollectorFailed,
                );
                break;
            }
        };
        if let Some(code) = validate_fact(&prepared.policy, role, &fact) {
            push_issue(
                &mut fact_issues,
                PreparationDriverStage::FactBinding,
                None,
                code,
            );
            break;
        }
        fact_digests.push(infallible_domain_digest(
            EXECUTABLE_FACT_DIGEST_DOMAIN,
            &fact,
        ));
    }
    if fact_digests.len() != HostExecutableRole::ALL.len() && fact_issues.is_empty() {
        push_issue(
            &mut fact_issues,
            PreparationDriverStage::Decision,
            None,
            PreparationDriverCode::InternalInvariant,
        );
    }
    Ok(decision(prepared, fact_digests, fact_issues))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{
        MachinePolicyEntry, MetadataSnapshot, ObservedPlatformIdentity, PlatformIdentity,
        PolicyReviewDeclaration,
    };
    use p256::ecdsa::{signature::Signer, SigningKey};
    use p256::elliptic_curve::ff::PrimeField;

    const EVALUATION_TIME: &str = "2026-07-14T12:00:00Z";
    const REVIEWED_AT: &str = "2026-07-14T00:00:00Z";
    const NOT_BEFORE: &str = "2026-07-13T00:00:00Z";
    const EXPIRES_AT: &str = "2026-07-15T00:00:00Z";
    const PROFILE_NOT_BEFORE: &str = "2026-07-12T00:00:00Z";
    const PROFILE_EXPIRES_AT: &str = "2026-07-16T00:00:00Z";

    struct Fixture {
        request: PreparationDriverRequest,
        machine_key: SigningKey,
        fixture_key: SigningKey,
    }

    impl Fixture {
        fn new() -> Self {
            let machine_key = signing_key(1);
            let fixture_key = signing_key(2);
            let machine_policy = machine_policy();
            let reviewers = ReviewerAssignments {
                machine_policy_reviewer_id: "policy-reviewer".to_string(),
                capture_operator_id: "capture-operator".to_string(),
                fixture_reviewer_id: "fixture-reviewer".to_string(),
                grammar_reviewer_id: "grammar-reviewer".to_string(),
            };
            let machine_policy_bytes = serde_json::to_vec(&machine_policy).unwrap();
            let rust_toolchain_manifest_bytes = serde_json::to_vec(&rust_manifest()).unwrap();
            let charon_source_manifest_bytes = serde_json::to_vec(&charon_manifest()).unwrap();
            let reviewer_assignments_bytes = serde_json::to_vec(&reviewers).unwrap();
            let mut request = PreparationDriverRequest {
                schema: PREPARATION_DRIVER_REQUEST_SCHEMA.to_string(),
                attempt_id: "attempt-794".to_string(),
                evaluation_time_utc: EVALUATION_TIME.to_string(),
                machine_policy,
                registry_document_bytes: TEST_REGISTRY_BYTES.to_vec(),
                operation_order_document_bytes: TEST_OPERATION_ORDER_BYTES.to_vec(),
                machine_policy_bytes,
                rust_toolchain_manifest_bytes,
                charon_source_manifest_bytes,
                aeneas_archive_bytes: TEST_AENEAS_BYTES.to_vec(),
                sandbox_profile_bytes: SANDBOX_PROFILE_BYTES.to_vec(),
                reviewer_assignments_bytes,
                ordered_receipts: Vec::new(),
                ordered_verification_profiles: Vec::new(),
            };
            request.ordered_receipts = signed_receipts(&request, &machine_key, &fixture_key);
            request.ordered_verification_profiles = vec![
                profile(
                    "profile-fixture",
                    "key-fixture",
                    "fixture-reviewer",
                    &fixture_key,
                    SourceSubjectClass::INPUTS
                        .iter()
                        .copied()
                        .filter(|class| *class != SourceSubjectClass::MachinePolicy)
                        .collect(),
                ),
                profile(
                    "profile-machine",
                    "key-machine",
                    "policy-reviewer",
                    &machine_key,
                    vec![SourceSubjectClass::MachinePolicy],
                ),
            ];
            Self {
                request,
                machine_key,
                fixture_key,
            }
        }

        fn resign(&mut self, index: usize) {
            let key = if self.request.ordered_receipts[index]
                .unsigned_body
                .subject_class
                == SourceSubjectClass::MachinePolicy
            {
                &self.machine_key
            } else {
                &self.fixture_key
            };
            self.request.ordered_receipts[index].signature_hex =
                sign_body(&self.request.ordered_receipts[index].unsigned_body, key);
        }
    }

    fn signing_key(seed: u8) -> SigningKey {
        let bytes = p256::FieldBytes::from([seed; 32]);
        SigningKey::from_bytes(&bytes).unwrap()
    }

    fn machine_policy() -> MachinePolicyCandidate {
        let entries = HostExecutableRole::ALL
            .iter()
            .copied()
            .map(|role| MachinePolicyEntry {
                role_id: role,
                requested_path: role
                    .expected_fixed_path()
                    .map(str::to_string)
                    .unwrap_or_else(|| format!("/allowed/{}", role.label().to_ascii_lowercase())),
                allowed_owner_uids: vec![501],
                admitted_sha256: vec![role_digest(role)],
                acceptance_policy_id: role.expected_policy_id().to_string(),
            })
            .collect();
        MachinePolicyCandidate {
            schema: crate::MACHINE_POLICY_SCHEMA.to_string(),
            policy_id: "policy-794".to_string(),
            registry_id: EXECUTABLE_REGISTRY_ID.to_string(),
            registry_document_sha256: REGISTRY_DOCUMENT_SHA256.to_string(),
            operation_order_sha256: OPERATION_ORDER_SHA256.to_string(),
            platform: PlatformIdentity {
                os: "macos".to_string(),
                arch: "aarch64".to_string(),
                product_version: "fixture".to_string(),
                build_version: "fixture".to_string(),
            },
            allowed_roots: vec![
                "/allowed".to_string(),
                "/usr/bin".to_string(),
                "/usr/sbin".to_string(),
            ],
            entries,
            review: PolicyReviewDeclaration {
                policy_object_producer_id: "policy-producer".to_string(),
                reviewer_id: "policy-reviewer".to_string(),
                reviewed_at_utc: REVIEWED_AT.to_string(),
                decision: ReviewDecision::Accepted,
            },
        }
    }

    fn rust_manifest() -> RustToolchainManifest {
        RustToolchainManifest {
            schema: RUST_TOOLCHAIN_MANIFEST_SCHEMA.to_string(),
            channel: RUST_CHANNEL.to_string(),
            manifest_url: RUST_MANIFEST_URL.to_string(),
            manifest_sha256: RUST_MANIFEST_SHA256.to_string(),
            charon_rust_toolchain_sha256: CHARON_RUST_TOOLCHAIN_SHA256.to_string(),
            rustc_identity: RUSTC_IDENTITY.to_string(),
            rustc_commit: RUSTC_COMMIT.to_string(),
            ordered_components: RUST_COMPONENTS
                .iter()
                .map(|(component, target, xz_sha256)| RustToolchainComponent {
                    component: (*component).to_string(),
                    target: (*target).to_string(),
                    xz_sha256: (*xz_sha256).to_string(),
                })
                .collect(),
        }
    }

    fn charon_manifest() -> CharonSourceManifest {
        CharonSourceManifest {
            schema: CHARON_SOURCE_MANIFEST_SCHEMA.to_string(),
            commit: CHARON_SOURCE_COMMIT.to_string(),
            ordered_files: CHARON_SOURCE_FILES
                .iter()
                .map(|(relative_path, sha256)| CharonSourceFile {
                    relative_path: (*relative_path).to_string(),
                    byte_length: 1,
                    sha256: (*sha256).to_string(),
                })
                .collect(),
        }
    }

    fn signed_receipts(
        request: &PreparationDriverRequest,
        machine_key: &SigningKey,
        fixture_key: &SigningKey,
    ) -> Vec<SourceReceiptEnvelope> {
        let policy_digest = machine_policy_sha256(&request.machine_policy).unwrap();
        subject_views(request)
            .iter()
            .enumerate()
            .map(|(index, subject)| {
                let identity = SubjectIdentity {
                    schema: SUBJECT_IDENTITY_SCHEMA.to_string(),
                    subject_class: subject.class,
                    subject_id: subject.id.clone(),
                    byte_length: subject.bytes.len() as u64,
                    sha256: hex_sha256(subject.bytes),
                };
                let (authority, revision) =
                    expected_authority_revision(subject.class, request, &identity, &policy_digest);
                let machine = subject.class == SourceSubjectClass::MachinePolicy;
                let body = SourceReceiptBody {
                    schema: SOURCE_RECEIPT_BODY_SCHEMA.to_string(),
                    receipt_id: format!("receipt-{index:02}"),
                    attempt_id: request.attempt_id.clone(),
                    subject_class: subject.class,
                    subject_id: subject.id.clone(),
                    subject_byte_length: subject.bytes.len() as u64,
                    subject_sha256: identity.sha256,
                    declared_source_authority: authority,
                    declared_source_revision: revision,
                    producer_id: if machine {
                        "policy-producer".to_string()
                    } else {
                        format!("producer-{index:02}")
                    },
                    reviewer_id: if machine {
                        "policy-reviewer".to_string()
                    } else {
                        "fixture-reviewer".to_string()
                    },
                    reviewer_key_id: if machine {
                        "key-machine".to_string()
                    } else {
                        "key-fixture".to_string()
                    },
                    reviewed_at_utc: REVIEWED_AT.to_string(),
                    not_before_utc: NOT_BEFORE.to_string(),
                    expires_at_utc: EXPIRES_AT.to_string(),
                    decision: ReviewDecision::Accepted,
                };
                SourceReceiptEnvelope {
                    schema: SOURCE_RECEIPT_ENVELOPE_SCHEMA.to_string(),
                    signature_hex: sign_body(
                        &body,
                        if machine { machine_key } else { fixture_key },
                    ),
                    unsigned_body: body,
                }
            })
            .collect()
    }

    fn profile(
        profile_id: &str,
        key_id: &str,
        reviewer_id: &str,
        key: &SigningKey,
        allowed_subject_classes: Vec<SourceSubjectClass>,
    ) -> FixtureVerificationProfile {
        let key_bytes = key.verifying_key().to_encoded_point(true);
        FixtureVerificationProfile {
            schema: FIXTURE_VERIFICATION_PROFILE_SCHEMA.to_string(),
            profile_id: profile_id.to_string(),
            attempt_id: "attempt-794".to_string(),
            reviewer_id: reviewer_id.to_string(),
            key_id: key_id.to_string(),
            compressed_sec1_key_hex: encode_lower_hex(key_bytes.as_bytes()),
            key_sha256: hex_sha256(key_bytes.as_bytes()),
            allowed_subject_classes,
            not_before_utc: PROFILE_NOT_BEFORE.to_string(),
            expires_at_utc: PROFILE_EXPIRES_AT.to_string(),
        }
    }

    fn sign_body(body: &SourceReceiptBody, key: &SigningKey) -> String {
        let preimage = source_receipt_signature_preimage(body).unwrap();
        let signature: Signature = key.sign(&preimage);
        let signature = signature.normalize_s().unwrap_or(signature);
        encode_lower_hex(&signature.to_bytes())
    }

    fn role_digest(role: HostExecutableRole) -> String {
        hex_sha256(role.label().as_bytes())
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

    fn fact(policy: &MachinePolicyCandidate, role: HostExecutableRole) -> ExecutableIdentityFact {
        let entry = policy
            .entries
            .iter()
            .find(|entry| entry.role_id == role)
            .unwrap();
        ExecutableIdentityFact {
            schema: EXECUTABLE_FACT_SCHEMA.to_string(),
            role_id: role,
            registry_id: policy.registry_id.clone(),
            machine_policy_id: policy.policy_id.clone(),
            machine_policy_sha256: machine_policy_sha256(policy).unwrap(),
            policy_entry_sha256: machine_policy_entry_sha256(entry).unwrap(),
            acceptance_policy_id: entry.acceptance_policy_id.clone(),
            decision: ReviewDecision::Accepted,
            declared_platform: policy.platform.clone(),
            observed_platform: ObservedPlatformIdentity {
                os: policy.platform.os.clone(),
                arch: policy.platform.arch.clone(),
            },
            requested_path: entry.requested_path.clone(),
            ordered_symlink_hops: Vec::new(),
            canonical_regular_file_path: entry.requested_path.clone(),
            observed_sha256: entry.admitted_sha256[0].clone(),
            pre_read_metadata: metadata(),
            post_read_metadata: metadata(),
        }
    }

    #[test]
    fn deterministic_complete_fixture_is_valid_without_authority() {
        let fixture = Fixture::new();
        let decision =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(
            decision.fixture_correspondence_valid,
            "{:?}",
            decision.ordered_issues
        );
        assert!(!decision.materialization_authorized);
        assert!(!decision.capture_authorized);
        assert_eq!(decision.ordered_host_fact_sha256.len(), 8);
        assert_eq!(decision.ordered_receipt_sha256.len(), 8);
        assert_eq!(decision.ordered_verification_profile_sha256.len(), 2);
        assert_eq!(decision.declared_evaluation_time_utc, EVALUATION_TIME);
        assert_eq!(
            decision.request_identity_sha256,
            "19e1f36f30b590cc7a530efc232745777a20109b209639bda4e57cc035521563"
        );
        assert_eq!(
            decision.ordered_receipt_sha256[0],
            "eccf6451d039a29952e2ee5456a44b3c58a49cb2a88d0b337e636e67fd1fc2dd"
        );
        assert_eq!(
            decision.ordered_verification_profile_sha256[0],
            "983337bc81ad495c3e90070a57a5294eabb132f56eb292332843394fee952e2e"
        );
        assert_eq!(
            decision.ordered_host_fact_sha256[0],
            "9794f0e986418a283675e30ef09f0573cb3c346ebb0356dd6252bee0206785ae"
        );
        assert_eq!(
            preparation_driver_decision_sha256(&decision).unwrap(),
            "7f5b2d09c53a84b84a73a8452a379153180314e856380782d1c152961333735c"
        );
    }

    #[test]
    fn public_driver_cannot_inject_test_subject_bindings() {
        let fixture = Fixture::new();
        let rejection = evaluate_preparation_driver(&fixture.request).unwrap_err();
        assert_eq!(
            rejection,
            pre_rejection(
                PreparationDriverStage::SubjectBounds,
                Some(SourceSubjectClass::ExecutableRegistryDocument),
                PreparationDriverCode::LengthOutOfBounds,
            )
        );
        assert!(!rejection.materialization_authorized);
        assert!(!rejection.capture_authorized);
    }

    #[test]
    fn malformed_and_wrong_signatures_fail_after_request_identity() {
        let mut malformed = Fixture::new();
        malformed.request.ordered_receipts[0].signature_hex = "00".to_string();
        let decision =
            evaluate_with_test_bindings(&malformed.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(!decision.fixture_correspondence_valid);
        assert!(decision.ordered_host_fact_sha256.is_empty());
        assert!(decision.ordered_issues.iter().any(|issue| {
            issue.stage == PreparationDriverStage::Signature
                && issue.code == PreparationDriverCode::SignatureEncodingInvalid
        }));

        let mut wrong = Fixture::new();
        wrong.request.ordered_receipts[0].signature_hex = sign_body(
            &wrong.request.ordered_receipts[0].unsigned_body,
            &wrong.machine_key,
        );
        let decision =
            evaluate_with_test_bindings(&wrong.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(decision
            .ordered_issues
            .iter()
            .any(|issue| issue.code == PreparationDriverCode::SignatureInvalid));
    }

    #[test]
    fn high_s_signature_is_rejected_before_verification() {
        let mut fixture = Fixture::new();
        let bytes =
            decode_lower_hex(&fixture.request.ordered_receipts[0].signature_hex, 64).unwrap();
        let signature = Signature::from_slice(&bytes).unwrap();
        let (r, s) = signature.split_bytes();
        let scalar = Option::<p256::Scalar>::from(p256::Scalar::from_repr(s)).unwrap();
        let high = Signature::from_scalars(r, (-scalar).to_bytes()).unwrap();
        assert!(high.normalize_s().is_some());
        fixture.request.ordered_receipts[0].signature_hex = encode_lower_hex(&high.to_bytes());

        let decision =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(decision
            .ordered_issues
            .iter()
            .any(|issue| issue.code == PreparationDriverCode::SignatureHighS));
        assert!(decision.ordered_host_fact_sha256.is_empty());
    }

    #[test]
    fn key_encoding_and_digest_mismatches_fail_closed() {
        let mut fixture = Fixture::new();
        fixture.request.ordered_verification_profiles[0].compressed_sec1_key_hex =
            format!("04{}", "00".repeat(32));
        let decision =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(decision
            .ordered_issues
            .iter()
            .any(|issue| issue.code == PreparationDriverCode::KeyEncodingInvalid));

        let mut fixture = Fixture::new();
        fixture.request.ordered_verification_profiles[0].key_sha256 = "00".repeat(32);
        let decision =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(decision
            .ordered_issues
            .iter()
            .any(|issue| issue.code == PreparationDriverCode::KeyDigestMismatch));
    }

    #[test]
    fn every_unsigned_receipt_field_is_covered_by_fail_closed_validation() {
        for case in 0..16 {
            let mut fixture = Fixture::new();
            let body = &mut fixture.request.ordered_receipts[0].unsigned_body;
            match case {
                0 => body.schema = "wrong".to_string(),
                1 => body.receipt_id = "receipt-01".to_string(),
                2 => body.attempt_id = "attempt-other".to_string(),
                3 => body.subject_class = SourceSubjectClass::OwnedTool,
                4 => body.subject_id = "subject-other".to_string(),
                5 => body.subject_byte_length += 1,
                6 => body.subject_sha256 = "00".repeat(32),
                7 => body.declared_source_authority = "fixture:other".to_string(),
                8 => body.declared_source_revision = "phase788".to_string(),
                9 => body.producer_id = "producer-other".to_string(),
                10 => body.reviewer_id = "reviewer-other".to_string(),
                11 => body.reviewer_key_id = "key-other".to_string(),
                12 => body.reviewed_at_utc = "2026-07-14T01:00:00Z".to_string(),
                13 => body.not_before_utc = "2026-07-13T01:00:00Z".to_string(),
                14 => body.expires_at_utc = "2026-07-15T01:00:00Z".to_string(),
                15 => body.decision = ReviewDecision::Pending,
                _ => unreachable!(),
            }
            let outcome = evaluate_with_test_bindings(&fixture.request, |policy, role| {
                Ok(fact(policy, role))
            });
            match outcome {
                Ok(decision) => {
                    assert!(!decision.fixture_correspondence_valid, "case {case}");
                    assert!(!decision.materialization_authorized);
                    assert!(!decision.capture_authorized);
                    assert!(!decision.ordered_issues.is_empty());
                }
                Err(rejection) => {
                    assert!(!rejection.materialization_authorized);
                    assert!(!rejection.capture_authorized);
                }
            }
        }
    }

    #[test]
    fn every_subject_byte_object_is_digest_bound() {
        for class in SourceSubjectClass::INPUTS {
            let mut fixture = Fixture::new();
            let bytes = match class {
                SourceSubjectClass::ExecutableRegistryDocument => {
                    &mut fixture.request.registry_document_bytes
                }
                SourceSubjectClass::OperationOrderDocument => {
                    &mut fixture.request.operation_order_document_bytes
                }
                SourceSubjectClass::MachinePolicy => &mut fixture.request.machine_policy_bytes,
                SourceSubjectClass::RustToolchainManifest => {
                    &mut fixture.request.rust_toolchain_manifest_bytes
                }
                SourceSubjectClass::CharonSourceTree => {
                    &mut fixture.request.charon_source_manifest_bytes
                }
                SourceSubjectClass::AeneasArchive => &mut fixture.request.aeneas_archive_bytes,
                SourceSubjectClass::SandboxProfile => &mut fixture.request.sandbox_profile_bytes,
                SourceSubjectClass::ReviewerAssignments => {
                    &mut fixture.request.reviewer_assignments_bytes
                }
                SourceSubjectClass::OwnedTool
                | SourceSubjectClass::PackagedTarget
                | SourceSubjectClass::BuiltTarget => unreachable!(),
            };
            bytes[0] ^= 1;
            let decision = evaluate_with_test_bindings(&fixture.request, |policy, role| {
                Ok(fact(policy, role))
            })
            .unwrap();
            assert!(!decision.fixture_correspondence_valid, "{class:?}");
            assert!(decision.ordered_host_fact_sha256.is_empty());
            assert!(decision.ordered_issues.iter().any(|issue| {
                issue.subject_class == Some(class)
                    && matches!(
                        issue.code,
                        PreparationDriverCode::DigestMismatch
                            | PreparationDriverCode::ParseFailed
                            | PreparationDriverCode::ReserializationMismatch
                    )
            }));
        }
    }

    #[test]
    fn receipt_field_and_subject_mutations_fail_closed() {
        let mut fixture = Fixture::new();
        fixture.request.ordered_receipts[0]
            .unsigned_body
            .declared_source_revision = "phase788".to_string();
        fixture.resign(0);
        let decision =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(decision.ordered_issues.iter().any(|issue| {
            issue.subject_class == Some(SourceSubjectClass::ExecutableRegistryDocument)
                && issue.code == PreparationDriverCode::BindingMismatch
        }));

        let mut fixture = Fixture::new();
        fixture.request.rust_toolchain_manifest_bytes.push(b' ');
        let decision =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(decision.ordered_issues.iter().any(|issue| {
            issue.subject_class == Some(SourceSubjectClass::RustToolchainManifest)
                && matches!(
                    issue.code,
                    PreparationDriverCode::DigestMismatch
                        | PreparationDriverCode::ReserializationMismatch
                )
        }));
    }

    #[test]
    fn profile_census_order_and_windows_fail_before_collection() {
        let mut fixture = Fixture::new();
        fixture.request.ordered_verification_profiles[1].profile_id =
            fixture.request.ordered_verification_profiles[0]
                .profile_id
                .clone();
        let rejection =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap_err();
        assert_eq!(rejection.code, PreparationDriverCode::DuplicateEntry);

        let mut fixture = Fixture::new();
        for receipt in &mut fixture.request.ordered_receipts {
            receipt.unsigned_body.reviewer_key_id = "key-fixture".to_string();
        }
        for profile in &mut fixture.request.ordered_verification_profiles {
            profile.key_id = "key-fixture".to_string();
            profile.allowed_subject_classes = SourceSubjectClass::INPUTS.to_vec();
        }
        let rejection =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap_err();
        assert_eq!(rejection.code, PreparationDriverCode::DuplicateEntry);

        let mut fixture = Fixture::new();
        fixture.request.ordered_receipts[0]
            .unsigned_body
            .expires_at_utc = EVALUATION_TIME.to_string();
        fixture.resign(0);
        let decision =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(decision
            .ordered_issues
            .iter()
            .any(|issue| issue.code == PreparationDriverCode::ProfileExpired));
    }

    #[test]
    fn collector_failure_and_invalid_fact_preserve_only_valid_prefix() {
        let fixture = Fixture::new();
        let decision = evaluate_with_test_bindings(&fixture.request, |policy, role| {
            if role == HostExecutableRole::TarExe {
                Err(())
            } else {
                Ok(fact(policy, role))
            }
        })
        .unwrap();
        assert_eq!(decision.ordered_host_fact_sha256.len(), 2);
        assert!(decision
            .ordered_issues
            .iter()
            .any(|issue| issue.code == PreparationDriverCode::CollectorFailed));

        let fixture = Fixture::new();
        let decision = evaluate_with_test_bindings(&fixture.request, |policy, role| {
            let mut value = fact(policy, role);
            if role == HostExecutableRole::TarExe {
                value.role_id = HostExecutableRole::CurlExe;
            }
            Ok(value)
        })
        .unwrap();
        assert_eq!(decision.ordered_host_fact_sha256.len(), 2);
        assert!(decision
            .ordered_issues
            .iter()
            .any(|issue| issue.code == PreparationDriverCode::FactRoleMismatch));
    }

    #[test]
    fn every_fact_binding_failure_code_is_reached_explicitly() {
        for (case, expected) in [
            (0, PreparationDriverCode::FactPolicyMismatch),
            (1, PreparationDriverCode::FactEntryMismatch),
            (2, PreparationDriverCode::FactPlatformMismatch),
            (3, PreparationDriverCode::FactDigestRejected),
        ] {
            let fixture = Fixture::new();
            let decision = evaluate_with_test_bindings(&fixture.request, |policy, role| {
                let mut value = fact(policy, role);
                if role == HostExecutableRole::TarExe {
                    match case {
                        0 => value.machine_policy_id = "policy-other".to_string(),
                        1 => value.requested_path = "/usr/bin/other".to_string(),
                        2 => value.observed_platform.arch = "x86_64".to_string(),
                        3 => value.observed_sha256 = "00".repeat(32),
                        _ => unreachable!(),
                    }
                }
                Ok(value)
            })
            .unwrap();
            assert_eq!(decision.ordered_host_fact_sha256.len(), 2);
            assert!(decision.ordered_issues.iter().any(|issue| {
                issue.stage == PreparationDriverStage::FactBinding && issue.code == expected
            }));
        }
    }

    #[test]
    fn profile_attempt_class_time_and_reviewer_separation_fail_closed() {
        let mut fixture = Fixture::new();
        fixture.request.ordered_verification_profiles[0].attempt_id = "attempt-other".to_string();
        let decision =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(decision.ordered_issues.iter().any(|issue| {
            issue.stage == PreparationDriverStage::ProfileBinding
                && issue.code == PreparationDriverCode::BindingMismatch
        }));

        let mut fixture = Fixture::new();
        fixture.request.ordered_verification_profiles[0].not_before_utc =
            "2026-07-15T12:00:00Z".to_string();
        let decision =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(decision
            .ordered_issues
            .iter()
            .any(|issue| issue.code == PreparationDriverCode::ProfileNotYetValid));

        let mut fixture = Fixture::new();
        fixture.request.ordered_verification_profiles[0]
            .allowed_subject_classes
            .pop();
        let rejection =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap_err();
        assert_eq!(rejection.code, PreparationDriverCode::InvalidCensus);

        let mut fixture = Fixture::new();
        fixture.request.ordered_receipts[0]
            .unsigned_body
            .producer_id = "fixture-reviewer".to_string();
        fixture.resign(0);
        let decision =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(decision
            .ordered_issues
            .iter()
            .any(|issue| issue.code == PreparationDriverCode::ProducerReviewerCollision));
    }

    #[test]
    fn invalid_curve_point_and_valid_length_invalid_scalar_reject() {
        let mut fixture = Fixture::new();
        let invalid_point = (0u8..=u8::MAX)
            .find_map(|seed| {
                let mut bytes = vec![seed; 33];
                bytes[0] = 0x02;
                VerifyingKey::from_sec1_bytes(&bytes)
                    .is_err()
                    .then_some(bytes)
            })
            .expect("at least one compressed x-coordinate is not on P-256");
        fixture.request.ordered_verification_profiles[0].compressed_sec1_key_hex =
            encode_lower_hex(&invalid_point);
        fixture.request.ordered_verification_profiles[0].key_sha256 = hex_sha256(
            &decode_lower_hex(
                &fixture.request.ordered_verification_profiles[0].compressed_sec1_key_hex,
                33,
            )
            .unwrap(),
        );
        let decision =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(decision
            .ordered_issues
            .iter()
            .any(|issue| issue.code == PreparationDriverCode::KeyEncodingInvalid));

        let mut fixture = Fixture::new();
        fixture.request.ordered_receipts[0].signature_hex = "00".repeat(64);
        let decision =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap();
        assert!(decision
            .ordered_issues
            .iter()
            .any(|issue| issue.code == PreparationDriverCode::SignatureEncodingInvalid));
    }

    #[test]
    fn oversized_wire_metadata_rejects_before_digest_construction() {
        let mut fixture = Fixture::new();
        fixture.request.ordered_receipts[0].signature_hex = "0".repeat(129);
        let rejection =
            evaluate_with_test_bindings(&fixture.request, |policy, role| Ok(fact(policy, role)))
                .unwrap_err();
        assert_eq!(rejection.stage, PreparationDriverStage::SubjectBounds);
        assert_eq!(
            rejection.subject_class,
            Some(SourceSubjectClass::ExecutableRegistryDocument)
        );
        assert_eq!(rejection.code, PreparationDriverCode::LengthOutOfBounds);
    }

    #[test]
    fn timestamp_and_hex_grammars_are_strict() {
        assert!(is_utc_timestamp("2026-02-28T23:59:59Z"));
        assert!(is_utc_timestamp("2024-02-29T00:00:00Z"));
        assert!(!is_utc_timestamp("0000-01-01T00:00:00Z"));
        assert!(!is_utc_timestamp("2026-02-29T00:00:00Z"));
        assert!(!is_utc_timestamp("2026-01-01T00:00:60Z"));
        assert!(!is_utc_timestamp("2026-01-01T00:00:00.0Z"));
        assert!(decode_lower_hex(&"ab".repeat(33), 33).is_some());
        assert!(decode_lower_hex(&"AB".repeat(33), 33).is_none());
    }
}
