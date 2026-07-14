//! Pure-data candidate validation for HSAI native-transcript preparation.
//!
//! This crate does not inspect a host, acquire or materialize artifacts, launch
//! executables, authenticate reviewers, authorize capture, or create evidence.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::path::{Component, Path, PathBuf};

pub const PREPARATION_CANDIDATE_SCHEMA: &str =
    "hsai-formal-native-transcript-preparation-candidate-v1";
pub const MACHINE_POLICY_SCHEMA: &str = "hsai-formal-machine-executable-policy-v1";
pub const EXECUTABLE_REGISTRY_ID: &str = "phase787-e83-executable-role-registry";
pub const EXECUTABLE_FACT_SCHEMA: &str = "hsai-formal-executable-identity-fact-v1";
pub const MACHINE_POLICY_DIGEST_DOMAIN: &[u8] =
    b"hsai-native-transcript-preparation:machine-policy:v1\0";
pub const CANDIDATE_DIGEST_DOMAIN: &[u8] = b"hsai-native-transcript-preparation:candidate:v1\0";
pub const STATE_SLICE: &str = "phase-790-hsai-native-transcript-preparation-candidate";
pub const OPERATION_ORDER_SHA256: &str =
    "490c30a8098214754d20e4025696e2e3c702df8d4f7114a611157653ea7a4464";
pub const REGISTRY_DOCUMENT_SHA256: &str =
    "e198efaab08ee38e02b7dabf03d380ecb3c48a8e37e7431ec4741443667f6f67";
pub const SANDBOX_PROFILE_SHA256: &str =
    "5c358b8d847211333e7ba22df82d84f796b5f30a41a2682209a949d783adbd08";
pub const SANDBOX_PROFILE_BYTES: &[u8] = b"(version 1)\n(allow default)\n(deny network*)\n";
pub const PREPARATION_ROOT: &str = "/private/tmp/hsai-native-transcript-input-preparation-v1";
pub const CAPTURE_ROOT: &str = "/private/tmp/hsai-native-transcript-capture-v1";
pub const AENEAS_ARCHIVE_BYTE_LENGTH: u64 = 123_234_656;
pub const AENEAS_ARCHIVE_URL: &str =
    "https://github.com/AeneasVerif/aeneas/releases/download/nightly-2026.07.10-c2015b8/aeneas-macos-aarch64.tar.gz";
pub const AENEAS_ARCHIVE_SHA256: &str =
    "fe706e847b01d83178e703898006bf372c5fcac007942b280efce776f5c35d45";
pub const CHARON_SOURCE_COMMIT: &str = "909ff09ad0f144f83d354f2c3d26f631fb9f8e9a";
pub const CLAIM_BOUNDARY: &str =
    "local preparation candidate validation only; capture authorization is always false";
pub const MAX_SYMLINK_HOPS: usize = 32;

pub const EXPLICIT_NONCLAIMS: [&str; 8] = [
    "not an authenticated operator approval",
    "not a materialized preparation handoff",
    "not a native transcript capture",
    "not a transcript grammar",
    "not accepted evidence",
    "not semantic correctness",
    "not production readiness",
    "not full security or SOTA",
];

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum HostExecutableRole {
    CurlExe,
    GitExe,
    TarExe,
    RustupExe,
    SandboxExecExe,
    CodesignExe,
    SpctlExe,
    OtoolExe,
}

impl HostExecutableRole {
    pub const ALL: [Self; 8] = [
        Self::CurlExe,
        Self::GitExe,
        Self::TarExe,
        Self::RustupExe,
        Self::SandboxExecExe,
        Self::CodesignExe,
        Self::SpctlExe,
        Self::OtoolExe,
    ];

    pub fn label(self) -> &'static str {
        match self {
            Self::CurlExe => "CURL_EXE",
            Self::GitExe => "GIT_EXE",
            Self::TarExe => "TAR_EXE",
            Self::RustupExe => "RUSTUP_EXE",
            Self::SandboxExecExe => "SANDBOX_EXEC_EXE",
            Self::CodesignExe => "CODESIGN_EXE",
            Self::SpctlExe => "SPCTL_EXE",
            Self::OtoolExe => "OTOOL_EXE",
        }
    }

    pub fn expected_policy_id(self) -> &'static str {
        match self {
            Self::GitExe | Self::RustupExe => "host-declared-sha256-v1",
            _ => "host-fixed-sha256-v1",
        }
    }

    pub fn expected_fixed_path(self) -> Option<&'static str> {
        match self {
            Self::CurlExe => Some("/usr/bin/curl"),
            Self::GitExe | Self::RustupExe => None,
            Self::TarExe => Some("/usr/bin/tar"),
            Self::SandboxExecExe => Some("/usr/bin/sandbox-exec"),
            Self::CodesignExe => Some("/usr/bin/codesign"),
            Self::SpctlExe => Some("/usr/sbin/spctl"),
            Self::OtoolExe => Some("/usr/bin/otool"),
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum OwnedToolRole {
    RustcExe,
    CargoExe,
}

impl OwnedToolRole {
    pub const ALL: [Self; 2] = [Self::RustcExe, Self::CargoExe];

    pub fn label(self) -> &'static str {
        match self {
            Self::RustcExe => "RUSTC_EXE",
            Self::CargoExe => "CARGO_EXE",
        }
    }

    pub fn expected_relative_path(self) -> &'static str {
        match self {
            Self::RustcExe => "owned-toolchain/RUSTC_EXE.json",
            Self::CargoExe => "owned-toolchain/CARGO_EXE.json",
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum TargetId {
    PackagedAeneas,
    PackagedCharon,
    PackagedCharonDriver,
    PackagedLibgmp,
    BuiltCharon,
    BuiltCharonDriver,
}

impl TargetId {
    pub const ALL: [Self; 6] = [
        Self::PackagedAeneas,
        Self::PackagedCharon,
        Self::PackagedCharonDriver,
        Self::PackagedLibgmp,
        Self::BuiltCharon,
        Self::BuiltCharonDriver,
    ];

    pub fn expected_relative_path(self) -> &'static str {
        match self {
            Self::PackagedAeneas => "targets/packaged/aeneas",
            Self::PackagedCharon => "targets/packaged/charon",
            Self::PackagedCharonDriver => "targets/packaged/charon-driver",
            Self::PackagedLibgmp => "targets/packaged/libgmp.10.dylib",
            Self::BuiltCharon => "targets/built/charon",
            Self::BuiltCharonDriver => "targets/built/charon-driver",
        }
    }

    pub fn expected_packaged_sha256(self) -> Option<&'static str> {
        match self {
            Self::PackagedAeneas => {
                Some("9b9acc9b8c0820de5650fa72b8f66c6caf5e85bce616f8b6cb91c3b5f30d877a")
            }
            Self::PackagedCharon => {
                Some("a71675cd16831f8dbba6936c8d9f85b2a2e171259d5c1cd2746bba99781be90a")
            }
            Self::PackagedCharonDriver => {
                Some("dde11d6bfedd3bd6b3c8b56c54b96992245c68e784c8d112aaada1d6618bed86")
            }
            Self::PackagedLibgmp => {
                Some("1b0ae61990da7a4661f2c8c601f55f6c9950279bbfef12453dd5bb0c01e4b0df")
            }
            Self::BuiltCharon | Self::BuiltCharonDriver => None,
        }
    }

    pub fn expected_source_authority(self) -> &'static str {
        match self {
            Self::PackagedAeneas
            | Self::PackagedCharon
            | Self::PackagedCharonDriver
            | Self::PackagedLibgmp => "phase-667-aeneas-release-archive",
            Self::BuiltCharon | Self::BuiltCharonDriver => "phase-778-ordinal-073-charon-build",
        }
    }

    pub fn is_built(self) -> bool {
        matches!(self, Self::BuiltCharon | Self::BuiltCharonDriver)
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ReviewDecision {
    Pending,
    Accepted,
    Rejected,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PlatformIdentity {
    pub os: String,
    pub arch: String,
    pub product_version: String,
    pub build_version: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PolicyReviewDeclaration {
    pub policy_object_producer_id: String,
    pub reviewer_id: String,
    pub reviewed_at_utc: String,
    pub decision: ReviewDecision,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MachinePolicyEntry {
    pub role_id: HostExecutableRole,
    pub requested_path: String,
    pub allowed_owner_uids: Vec<u32>,
    pub admitted_sha256: Vec<String>,
    pub acceptance_policy_id: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MachinePolicyCandidate {
    pub schema: String,
    pub policy_id: String,
    pub registry_id: String,
    pub registry_document_sha256: String,
    pub operation_order_sha256: String,
    pub platform: PlatformIdentity,
    pub allowed_roots: Vec<String>,
    pub entries: Vec<MachinePolicyEntry>,
    pub review: PolicyReviewDeclaration,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SymlinkHop {
    pub path: String,
    pub link_text: String,
    pub resolved_path: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MetadataSnapshot {
    pub device: u64,
    pub inode: u64,
    pub byte_length: u64,
    pub mode: u32,
    pub owner_uid: u32,
    pub modified_seconds: i64,
    pub modified_nanoseconds: i64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ExecutableIdentityFact {
    pub schema: String,
    pub role_id: HostExecutableRole,
    pub machine_policy_sha256: String,
    pub platform: PlatformIdentity,
    pub requested_path: String,
    pub ordered_symlink_hops: Vec<SymlinkHop>,
    pub canonical_regular_file_path: String,
    pub observed_sha256: String,
    pub pre_read_metadata: MetadataSnapshot,
    pub post_read_metadata: MetadataSnapshot,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct OwnedToolReceipt {
    pub role_id: OwnedToolRole,
    pub relative_path: String,
    pub sha256: String,
    pub source_receipt_sha256: String,
    pub accepted: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct TargetReceipt {
    pub target_id: TargetId,
    pub relative_path: String,
    pub byte_length: u64,
    pub sha256: String,
    pub source_authority: String,
    pub source_receipt_sha256: String,
    pub producer_ordinal: u16,
    pub source_commit: Option<String>,
    pub macho_arch: Option<String>,
    pub ad_hoc_signed: Option<bool>,
    pub team_id: Option<String>,
    pub source_tree_stable: Option<bool>,
    pub accepted: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ReviewerAssignments {
    pub machine_policy_reviewer_id: String,
    pub capture_operator_id: String,
    pub fixture_reviewer_id: String,
    pub grammar_reviewer_id: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PreparationCandidate {
    pub schema: String,
    pub state_slice: String,
    pub claim_boundary: String,
    pub explicit_nonclaims: Vec<String>,
    pub operation_order_sha256: String,
    pub preparation_root: String,
    pub capture_root: String,
    pub capture_root_declared_absent: bool,
    pub aeneas_archive_url: String,
    pub aeneas_archive_byte_length: u64,
    pub aeneas_archive_sha256: String,
    pub charon_source_commit: String,
    pub machine_policy: MachinePolicyCandidate,
    pub executable_facts: Vec<ExecutableIdentityFact>,
    pub owned_tool_receipts: Vec<OwnedToolReceipt>,
    pub target_receipts: Vec<TargetReceipt>,
    pub sandbox_profile_bytes: Vec<u8>,
    pub sandbox_profile_sha256: String,
    pub reviewer_assignments: ReviewerAssignments,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ValidationIssueClass {
    Structural,
    MissingInput,
    ExternalAuthority,
    IdentityDrift,
    ClaimBoundary,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ValidationIssue {
    pub class: ValidationIssueClass,
    pub subject: String,
    pub detail: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PreparationValidation {
    pub structurally_valid: bool,
    pub declared_inputs_complete: bool,
    pub candidate_eligible_for_external_review: bool,
    pub materialization_accepted: bool,
    pub capture_authorized: bool,
    pub issues: Vec<ValidationIssue>,
}

pub fn validate_preparation_candidate(candidate: &PreparationCandidate) -> PreparationValidation {
    let mut issues = Vec::new();
    structural_contract_checks(candidate, &mut issues);
    validate_machine_policy(&candidate.machine_policy, &mut issues);
    validate_executable_facts(candidate, &mut issues);
    validate_owned_tools(candidate, &mut issues);
    validate_targets(candidate, &mut issues);
    validate_reviewers(&candidate.reviewer_assignments, &mut issues);
    if candidate.machine_policy.review.reviewer_id
        != candidate.reviewer_assignments.machine_policy_reviewer_id
    {
        push_issue(
            &mut issues,
            ValidationIssueClass::ExternalAuthority,
            "reviewer_assignments.machine_policy_reviewer_id",
            "assignment does not bind the declared machine-policy review",
        );
    }

    if candidate.sandbox_profile_sha256 != SANDBOX_PROFILE_SHA256 {
        push_issue(
            &mut issues,
            ValidationIssueClass::IdentityDrift,
            "sandbox_profile_sha256",
            "sandbox profile digest does not match Phase 776",
        );
    }
    if candidate.sandbox_profile_bytes != SANDBOX_PROFILE_BYTES
        || hex_digest(&Sha256::digest(&candidate.sandbox_profile_bytes))
            != candidate.sandbox_profile_sha256
    {
        push_issue(
            &mut issues,
            ValidationIssueClass::IdentityDrift,
            "sandbox_profile_bytes",
            "sandbox profile bytes or their computed digest do not match Phase 776",
        );
    }

    issues.sort();
    issues.dedup();
    let structurally_valid = !issues.iter().any(|issue| {
        matches!(
            issue.class,
            ValidationIssueClass::Structural
                | ValidationIssueClass::IdentityDrift
                | ValidationIssueClass::ClaimBoundary
        )
    });
    let declared_inputs_complete = issues.is_empty();
    PreparationValidation {
        structurally_valid,
        declared_inputs_complete,
        candidate_eligible_for_external_review: declared_inputs_complete,
        materialization_accepted: false,
        capture_authorized: false,
        issues,
    }
}

fn structural_contract_checks(candidate: &PreparationCandidate, issues: &mut Vec<ValidationIssue>) {
    check_equal(
        issues,
        "schema",
        &candidate.schema,
        PREPARATION_CANDIDATE_SCHEMA,
    );
    check_equal(issues, "state_slice", &candidate.state_slice, STATE_SLICE);
    check_equal(
        issues,
        "claim_boundary",
        &candidate.claim_boundary,
        CLAIM_BOUNDARY,
    );
    check_equal(
        issues,
        "operation_order_sha256",
        &candidate.operation_order_sha256,
        OPERATION_ORDER_SHA256,
    );
    check_equal(
        issues,
        "preparation_root",
        &candidate.preparation_root,
        PREPARATION_ROOT,
    );
    check_equal(
        issues,
        "capture_root",
        &candidate.capture_root,
        CAPTURE_ROOT,
    );
    if !candidate.capture_root_declared_absent {
        push_issue(
            issues,
            ValidationIssueClass::ClaimBoundary,
            "capture_root_declared_absent",
            "the preparation candidate must declare the capture root absent",
        );
    }
    if candidate.aeneas_archive_byte_length != AENEAS_ARCHIVE_BYTE_LENGTH {
        push_issue(
            issues,
            ValidationIssueClass::IdentityDrift,
            "aeneas_archive_byte_length",
            "archive length does not match the Phase 788 source authority",
        );
    }
    check_equal(
        issues,
        "aeneas_archive_url",
        &candidate.aeneas_archive_url,
        AENEAS_ARCHIVE_URL,
    );
    check_equal(
        issues,
        "aeneas_archive_sha256",
        &candidate.aeneas_archive_sha256,
        AENEAS_ARCHIVE_SHA256,
    );
    check_equal(
        issues,
        "charon_source_commit",
        &candidate.charon_source_commit,
        CHARON_SOURCE_COMMIT,
    );
    let expected_nonclaims = EXPLICIT_NONCLAIMS
        .iter()
        .map(|value| (*value).to_string())
        .collect::<Vec<_>>();
    if candidate.explicit_nonclaims != expected_nonclaims {
        push_issue(
            issues,
            ValidationIssueClass::ClaimBoundary,
            "explicit_nonclaims",
            "explicit nonclaims do not match the closed Phase 790 list",
        );
    }
}

fn validate_machine_policy(policy: &MachinePolicyCandidate, issues: &mut Vec<ValidationIssue>) {
    check_equal(
        issues,
        "machine_policy.schema",
        &policy.schema,
        MACHINE_POLICY_SCHEMA,
    );
    check_equal(
        issues,
        "machine_policy.operation_order_sha256",
        &policy.operation_order_sha256,
        OPERATION_ORDER_SHA256,
    );
    check_nonempty(issues, "machine_policy.policy_id", &policy.policy_id);
    check_equal(
        issues,
        "machine_policy.registry_id",
        &policy.registry_id,
        EXECUTABLE_REGISTRY_ID,
    );
    check_sha256(
        issues,
        "machine_policy.registry_document_sha256",
        &policy.registry_document_sha256,
    );
    check_equal(
        issues,
        "machine_policy.registry_document_sha256",
        &policy.registry_document_sha256,
        REGISTRY_DOCUMENT_SHA256,
    );
    for (subject, value) in [
        ("platform.os", policy.platform.os.as_str()),
        ("platform.arch", policy.platform.arch.as_str()),
        (
            "platform.product_version",
            policy.platform.product_version.as_str(),
        ),
        (
            "platform.build_version",
            policy.platform.build_version.as_str(),
        ),
    ] {
        check_nonempty(issues, subject, value);
    }

    if policy.allowed_roots.is_empty() {
        push_issue(
            issues,
            ValidationIssueClass::MissingInput,
            "machine_policy.allowed_roots",
            "at least one allowed root is required",
        );
    }
    check_sorted_unique(
        issues,
        "machine_policy.allowed_roots",
        &policy.allowed_roots,
    );
    for root in &policy.allowed_roots {
        if !is_normal_absolute_path(root) {
            push_issue(
                issues,
                ValidationIssueClass::Structural,
                "machine_policy.allowed_roots",
                "allowed roots must be normalized absolute paths",
            );
        }
    }

    let declared_entry_order = policy
        .entries
        .iter()
        .map(|entry| entry.role_id)
        .collect::<Vec<_>>();
    if declared_entry_order != HostExecutableRole::ALL {
        push_issue(
            issues,
            ValidationIssueClass::Structural,
            "machine_policy.entries",
            "machine-policy entries must use the closed host-role order",
        );
    }

    let mut entries = BTreeMap::new();
    for entry in &policy.entries {
        if entries.insert(entry.role_id, entry).is_some() {
            push_issue(
                issues,
                ValidationIssueClass::Structural,
                entry.role_id.label(),
                "duplicate machine-policy role entry",
            );
        }
        if !is_normal_absolute_path(&entry.requested_path) {
            push_issue(
                issues,
                ValidationIssueClass::Structural,
                entry.role_id.label(),
                "requested path must be normalized and absolute",
            );
        }
        if let Some(expected) = entry.role_id.expected_fixed_path() {
            if entry.requested_path != expected {
                push_issue(
                    issues,
                    ValidationIssueClass::IdentityDrift,
                    entry.role_id.label(),
                    "fixed host role path does not match the Phase 787 registry",
                );
            }
        }
        if entry.acceptance_policy_id != entry.role_id.expected_policy_id() {
            push_issue(
                issues,
                ValidationIssueClass::Structural,
                entry.role_id.label(),
                "acceptance policy does not match the Phase 787 role",
            );
        }
        if entry.allowed_owner_uids.is_empty() || entry.admitted_sha256.is_empty() {
            push_issue(
                issues,
                ValidationIssueClass::MissingInput,
                entry.role_id.label(),
                "owner and digest allowlists must both be nonempty",
            );
        }
        check_sorted_unique(
            issues,
            &format!("{}.allowed_owner_uids", entry.role_id.label()),
            &entry.allowed_owner_uids,
        );
        check_sorted_unique(
            issues,
            &format!("{}.admitted_sha256", entry.role_id.label()),
            &entry.admitted_sha256,
        );
        for digest in &entry.admitted_sha256 {
            check_sha256(issues, entry.role_id.label(), digest);
        }
    }
    for role in HostExecutableRole::ALL {
        if !entries.contains_key(&role) {
            push_issue(
                issues,
                ValidationIssueClass::MissingInput,
                role.label(),
                "required machine-policy role entry is absent",
            );
        }
    }

    check_nonempty(
        issues,
        "machine_policy.review.reviewer_id",
        &policy.review.reviewer_id,
    );
    check_nonempty(
        issues,
        "machine_policy.review.policy_object_producer_id",
        &policy.review.policy_object_producer_id,
    );
    check_nonempty(
        issues,
        "machine_policy.review.reviewed_at_utc",
        &policy.review.reviewed_at_utc,
    );
    if policy.review.decision != ReviewDecision::Accepted {
        push_issue(
            issues,
            ValidationIssueClass::ExternalAuthority,
            "machine_policy.review.decision",
            "declared machine-policy review is not accepted",
        );
    }
    if policy.review.policy_object_producer_id == policy.review.reviewer_id {
        push_issue(
            issues,
            ValidationIssueClass::ExternalAuthority,
            "machine_policy.review.reviewer_id",
            "machine-policy producer and reviewer must be distinct",
        );
    }
}

fn validate_executable_facts(candidate: &PreparationCandidate, issues: &mut Vec<ValidationIssue>) {
    let expected_policy_sha256 = machine_policy_sha256(&candidate.machine_policy)
        .expect("serializing a Rust data structure cannot fail");
    let entries = candidate
        .machine_policy
        .entries
        .iter()
        .map(|entry| (entry.role_id, entry))
        .collect::<BTreeMap<_, _>>();
    let allowed_roots = candidate
        .machine_policy
        .allowed_roots
        .iter()
        .map(PathBuf::from)
        .collect::<Vec<_>>();
    let mut facts = BTreeMap::new();
    let declared_fact_order = candidate
        .executable_facts
        .iter()
        .map(|fact| fact.role_id)
        .collect::<Vec<_>>();
    if declared_fact_order != HostExecutableRole::ALL {
        push_issue(
            issues,
            ValidationIssueClass::Structural,
            "executable_facts",
            "executable facts must use the closed host-role order",
        );
    }
    for fact in &candidate.executable_facts {
        if facts.insert(fact.role_id, fact).is_some() {
            push_issue(
                issues,
                ValidationIssueClass::Structural,
                fact.role_id.label(),
                "duplicate executable fact",
            );
        }
        check_equal(
            issues,
            fact.role_id.label(),
            &fact.schema,
            EXECUTABLE_FACT_SCHEMA,
        );
        if fact.machine_policy_sha256 != expected_policy_sha256 {
            push_issue(
                issues,
                ValidationIssueClass::IdentityDrift,
                fact.role_id.label(),
                "executable fact does not bind the reviewed machine-policy object",
            );
        }
        if fact.platform != candidate.machine_policy.platform {
            push_issue(
                issues,
                ValidationIssueClass::IdentityDrift,
                fact.role_id.label(),
                "executable fact platform does not match the machine policy",
            );
        }
        check_sha256(issues, fact.role_id.label(), &fact.observed_sha256);
        if fact.pre_read_metadata != fact.post_read_metadata {
            push_issue(
                issues,
                ValidationIssueClass::IdentityDrift,
                fact.role_id.label(),
                "pre-read and post-read metadata differ",
            );
        }
        if fact.ordered_symlink_hops.len() > MAX_SYMLINK_HOPS {
            push_issue(
                issues,
                ValidationIssueClass::IdentityDrift,
                fact.role_id.label(),
                "declared symlink chain exceeds the Phase 787 bound",
            );
        }
        let mode = fact.pre_read_metadata.mode;
        if fact.pre_read_metadata.byte_length == 0
            || mode & 0o170000 != 0o100000
            || mode & 0o7000 != 0
            || mode & 0o022 != 0
            || mode & 0o111 == 0
        {
            push_issue(
                issues,
                ValidationIssueClass::IdentityDrift,
                fact.role_id.label(),
                "declared executable metadata is empty or has an unsafe mode",
            );
        }
        let canonical = Path::new(&fact.canonical_regular_file_path);
        if !is_normal_absolute_path(&fact.canonical_regular_file_path)
            || !inside_any_root(canonical, &allowed_roots)
        {
            push_issue(
                issues,
                ValidationIssueClass::IdentityDrift,
                fact.role_id.label(),
                "canonical executable path is outside allowed roots",
            );
        }
        let mut seen_hops = BTreeSet::new();
        for hop in &fact.ordered_symlink_hops {
            if !seen_hops.insert(hop.path.as_str()) {
                push_issue(
                    issues,
                    ValidationIssueClass::IdentityDrift,
                    fact.role_id.label(),
                    "declared symlink chain repeats a path",
                );
            }
            if !is_normal_absolute_path(&hop.path)
                || !is_normal_absolute_path(&hop.resolved_path)
                || !inside_any_root(Path::new(&hop.path), &allowed_roots)
                || !inside_any_root(Path::new(&hop.resolved_path), &allowed_roots)
            {
                push_issue(
                    issues,
                    ValidationIssueClass::IdentityDrift,
                    fact.role_id.label(),
                    "symlink hop escapes allowed roots",
                );
            }
        }
        if let Some(entry) = entries.get(&fact.role_id) {
            if fact.requested_path != entry.requested_path
                || !entry
                    .allowed_owner_uids
                    .contains(&fact.pre_read_metadata.owner_uid)
                || !entry.admitted_sha256.contains(&fact.observed_sha256)
            {
                push_issue(
                    issues,
                    ValidationIssueClass::IdentityDrift,
                    fact.role_id.label(),
                    "executable fact is not admitted by the declared policy entry",
                );
            }
        }
    }
    for role in HostExecutableRole::ALL {
        if !facts.contains_key(&role) {
            push_issue(
                issues,
                ValidationIssueClass::MissingInput,
                role.label(),
                "required executable identity fact is absent",
            );
        }
    }
}

fn validate_owned_tools(candidate: &PreparationCandidate, issues: &mut Vec<ValidationIssue>) {
    let mut receipts = BTreeMap::new();
    let declared_order = candidate
        .owned_tool_receipts
        .iter()
        .map(|receipt| receipt.role_id)
        .collect::<Vec<_>>();
    if declared_order != OwnedToolRole::ALL {
        push_issue(
            issues,
            ValidationIssueClass::Structural,
            "owned_tool_receipts",
            "owned-tool receipts must use the closed role order",
        );
    }
    for receipt in &candidate.owned_tool_receipts {
        if receipts.insert(receipt.role_id, receipt).is_some() {
            push_issue(
                issues,
                ValidationIssueClass::Structural,
                receipt.role_id.label(),
                "duplicate owned-tool receipt",
            );
        }
        if !is_portable_relative_path(&receipt.relative_path)
            || receipt.relative_path != receipt.role_id.expected_relative_path()
        {
            push_issue(
                issues,
                ValidationIssueClass::Structural,
                receipt.role_id.label(),
                "owned-tool receipt path must match the closed portable role path",
            );
        }
        check_sha256(issues, receipt.role_id.label(), &receipt.sha256);
        check_sha256(
            issues,
            &format!("{}.source_receipt", receipt.role_id.label()),
            &receipt.source_receipt_sha256,
        );
        if !receipt.accepted {
            push_issue(
                issues,
                ValidationIssueClass::MissingInput,
                receipt.role_id.label(),
                "owned-tool receipt is not declared accepted",
            );
        }
    }
    for role in OwnedToolRole::ALL {
        if !receipts.contains_key(&role) {
            push_issue(
                issues,
                ValidationIssueClass::MissingInput,
                role.label(),
                "required owned-tool receipt is absent",
            );
        }
    }
}

fn validate_targets(candidate: &PreparationCandidate, issues: &mut Vec<ValidationIssue>) {
    let mut receipts = BTreeMap::new();
    let declared_order = candidate
        .target_receipts
        .iter()
        .map(|receipt| receipt.target_id)
        .collect::<Vec<_>>();
    if declared_order != TargetId::ALL {
        push_issue(
            issues,
            ValidationIssueClass::Structural,
            "target_receipts",
            "target receipts must use the closed six-target order",
        );
    }
    for receipt in &candidate.target_receipts {
        if receipts.insert(receipt.target_id, receipt).is_some() {
            push_issue(
                issues,
                ValidationIssueClass::Structural,
                format!("{:?}", receipt.target_id),
                "duplicate target receipt",
            );
        }
        if receipt.relative_path != receipt.target_id.expected_relative_path() {
            push_issue(
                issues,
                ValidationIssueClass::Structural,
                format!("{:?}", receipt.target_id),
                "target receipt path does not match the closed six-slot tree",
            );
        }
        check_sha256(issues, &format!("{:?}", receipt.target_id), &receipt.sha256);
        check_sha256(
            issues,
            &format!("{:?}.source_receipt", receipt.target_id),
            &receipt.source_receipt_sha256,
        );
        check_nonempty(
            issues,
            &format!("{:?}.source_authority", receipt.target_id),
            &receipt.source_authority,
        );
        if receipt.source_authority != receipt.target_id.expected_source_authority() {
            push_issue(
                issues,
                ValidationIssueClass::IdentityDrift,
                format!("{:?}", receipt.target_id),
                "target source authority does not match the closed Phase 790 route",
            );
        }
        if receipt.byte_length == 0 || !receipt.accepted {
            push_issue(
                issues,
                ValidationIssueClass::MissingInput,
                format!("{:?}", receipt.target_id),
                "target receipt must be nonempty and declared accepted",
            );
        }
        if let Some(expected) = receipt.target_id.expected_packaged_sha256() {
            if receipt.sha256 != expected {
                push_issue(
                    issues,
                    ValidationIssueClass::IdentityDrift,
                    format!("{:?}", receipt.target_id),
                    "packaged target digest does not match Phase 788",
                );
            }
            if receipt.producer_ordinal != 0
                || receipt.source_commit.is_some()
                || receipt.macho_arch.is_some()
                || receipt.ad_hoc_signed.is_some()
                || receipt.team_id.is_some()
                || receipt.source_tree_stable.is_some()
            {
                push_issue(
                    issues,
                    ValidationIssueClass::Structural,
                    format!("{:?}", receipt.target_id),
                    "packaged receipt contains built-target acceptance fields",
                );
            }
        } else if receipt.producer_ordinal != 73
            || receipt.source_commit.as_deref() != Some(CHARON_SOURCE_COMMIT)
            || receipt.macho_arch.as_deref() != Some("arm64")
            || receipt.ad_hoc_signed != Some(true)
            || receipt.team_id.is_some()
            || receipt.source_tree_stable != Some(true)
        {
            push_issue(
                issues,
                ValidationIssueClass::IdentityDrift,
                format!("{:?}", receipt.target_id),
                "built target lacks exact ordinal-073 source and Mach-O acceptance",
            );
        }
    }
    for target in TargetId::ALL {
        if !receipts.contains_key(&target) {
            push_issue(
                issues,
                ValidationIssueClass::MissingInput,
                format!("{:?}", target),
                "required target receipt is absent",
            );
        }
    }
}

fn validate_reviewers(reviewers: &ReviewerAssignments, issues: &mut Vec<ValidationIssue>) {
    for (subject, value) in [
        (
            "machine_policy_reviewer_id",
            reviewers.machine_policy_reviewer_id.as_str(),
        ),
        (
            "capture_operator_id",
            reviewers.capture_operator_id.as_str(),
        ),
        (
            "fixture_reviewer_id",
            reviewers.fixture_reviewer_id.as_str(),
        ),
        (
            "grammar_reviewer_id",
            reviewers.grammar_reviewer_id.as_str(),
        ),
    ] {
        check_nonempty(issues, subject, value);
    }
    if reviewers.machine_policy_reviewer_id == reviewers.capture_operator_id {
        push_issue(
            issues,
            ValidationIssueClass::ExternalAuthority,
            "reviewer_assignments",
            "machine-policy reviewer must differ from capture operator",
        );
    }
    let roles = [
        reviewers.machine_policy_reviewer_id.as_str(),
        reviewers.capture_operator_id.as_str(),
        reviewers.fixture_reviewer_id.as_str(),
        reviewers.grammar_reviewer_id.as_str(),
    ];
    if roles.iter().collect::<BTreeSet<_>>().len() != roles.len() {
        push_issue(
            issues,
            ValidationIssueClass::ExternalAuthority,
            "reviewer_assignments",
            "all four declared preparation and capture principals must be distinct",
        );
    }
}

pub fn serialize_candidate_json(
    candidate: &PreparationCandidate,
) -> Result<Vec<u8>, serde_json::Error> {
    serde_json::to_vec(candidate)
}

pub fn machine_policy_sha256(policy: &MachinePolicyCandidate) -> Result<String, serde_json::Error> {
    let bytes = serde_json::to_vec(policy)?;
    let mut hasher = Sha256::new();
    hasher.update(MACHINE_POLICY_DIGEST_DOMAIN);
    hasher.update(bytes);
    Ok(hex_digest(&hasher.finalize()))
}

pub fn candidate_sha256(candidate: &PreparationCandidate) -> Result<String, serde_json::Error> {
    let bytes = serialize_candidate_json(candidate)?;
    let mut hasher = Sha256::new();
    hasher.update(CANDIDATE_DIGEST_DOMAIN);
    hasher.update(bytes);
    Ok(hex_digest(&hasher.finalize()))
}

fn check_equal(issues: &mut Vec<ValidationIssue>, subject: &str, actual: &str, expected: &str) {
    if actual != expected {
        push_issue(
            issues,
            ValidationIssueClass::Structural,
            subject,
            format!("expected {expected}"),
        );
    }
}

fn check_nonempty(issues: &mut Vec<ValidationIssue>, subject: &str, value: &str) {
    if value.trim().is_empty() {
        push_issue(
            issues,
            ValidationIssueClass::MissingInput,
            subject,
            "value must be nonempty",
        );
    }
}

fn check_sha256(issues: &mut Vec<ValidationIssue>, subject: &str, value: &str) {
    if !is_sha256(value) {
        push_issue(
            issues,
            ValidationIssueClass::Structural,
            subject,
            "value must be 64 lowercase hexadecimal characters",
        );
    }
}

fn check_sorted_unique<T: Ord>(issues: &mut Vec<ValidationIssue>, subject: &str, values: &[T]) {
    if values.windows(2).any(|pair| pair[0] >= pair[1]) {
        push_issue(
            issues,
            ValidationIssueClass::Structural,
            subject,
            "values must be strictly sorted and unique",
        );
    }
}

fn inside_any_root(path: &Path, roots: &[PathBuf]) -> bool {
    roots.iter().any(|root| path.starts_with(root))
}

fn is_portable_relative_path(value: &str) -> bool {
    let path = Path::new(value);
    !value.is_empty()
        && !path.is_absolute()
        && path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}

fn is_normal_absolute_path(value: &str) -> bool {
    let path = Path::new(value);
    path.is_absolute()
        && path
            .components()
            .all(|component| matches!(component, Component::RootDir | Component::Normal(_)))
}

fn is_sha256(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
}

fn push_issue(
    issues: &mut Vec<ValidationIssue>,
    class: ValidationIssueClass,
    subject: impl Into<String>,
    detail: impl Into<String>,
) {
    issues.push(ValidationIssue {
        class,
        subject: subject.into(),
        detail: detail.into(),
    });
}

fn hex_digest(bytes: &[u8]) -> String {
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        use std::fmt::Write as _;
        write!(&mut output, "{byte:02x}").expect("writing to String cannot fail");
    }
    output
}
