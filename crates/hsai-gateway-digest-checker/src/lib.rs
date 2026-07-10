//! Dependency-isolated local checker for the HSAI gateway proposal digest.
//!
//! This crate intentionally does not depend on production HSAI types, Serde,
//! `serde_json`, or `sha2`. Agreement is local implementation-diverse
//! regression evidence, not independent verification or formal proof.

use ring::digest;

pub const CHECKER_SCHEMA_VERSION: &str = "hsai-gateway-digest-checker-v1";
pub const CHECKER_STATE_SLICE: &str =
    "phase-662-hsai-gateway-proposal-digest-local-implementation-diverse-checker";
pub const CHECKER_IMPLEMENTATION_ID: &str = "manual-rust-v1-ring-sha256";
pub const CHECKER_ENCODER_ID: &str = "manual-gateway-action-proposal-v1-json-byte-encoder";
pub const CHECKER_HASH_PROVIDER_ID: &str = "ring-0.17.14-sha256";
pub const CHECKER_DIGEST_TAG: &str = "hsai-agent-admission:gateway-action-proposal:v1";
pub const CHECKER_CLAIM_BOUNDARY: &str =
    "local implementation-diverse gateway proposal digest checker agreement only";

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CheckerGatewayActionId(pub String);

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CheckerSubjectId(pub String);

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CheckerNonclaim(pub String);

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CheckerArtifactDigest {
    pub id: String,
    pub sha256: [u8; 32],
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CheckerGatewayActionKind {
    Payment,
    Trade,
    ToolCall,
    DataAccess,
    ComputeRental,
    Deployment,
    Checkout,
}

impl CheckerGatewayActionKind {
    fn label(self) -> &'static str {
        match self {
            Self::Payment => "Payment",
            Self::Trade => "Trade",
            Self::ToolCall => "ToolCall",
            Self::DataAccess => "DataAccess",
            Self::ComputeRental => "ComputeRental",
            Self::Deployment => "Deployment",
            Self::Checkout => "Checkout",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CheckerGatewayModelLaneKind {
    Deterministic,
    LocalOpenWeight,
    RentedOpenWeight,
    HostedSmall,
    PremiumEscalation,
}

impl CheckerGatewayModelLaneKind {
    fn label(self) -> &'static str {
        match self {
            Self::Deterministic => "Deterministic",
            Self::LocalOpenWeight => "LocalOpenWeight",
            Self::RentedOpenWeight => "RentedOpenWeight",
            Self::HostedSmall => "HostedSmall",
            Self::PremiumEscalation => "PremiumEscalation",
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CheckerGatewayThreatLabel {
    Benign,
    PromptInjectionPayment,
    WrongCounterparty,
    AmountLimitBypass,
    SourceDigestDrift,
    StaleApprovalReplay,
    DuplicateJsonKeyPayload,
    PolicyDowngrade,
    DirectAuthorityRequest,
    ForgedAcceptedDecision,
    MissingNonclaim,
    MissingSourceDigest,
    StaleJournalTip,
    SignerBeforeAdmission,
}

impl CheckerGatewayThreatLabel {
    fn label(self) -> &'static str {
        match self {
            Self::Benign => "Benign",
            Self::PromptInjectionPayment => "PromptInjectionPayment",
            Self::WrongCounterparty => "WrongCounterparty",
            Self::AmountLimitBypass => "AmountLimitBypass",
            Self::SourceDigestDrift => "SourceDigestDrift",
            Self::StaleApprovalReplay => "StaleApprovalReplay",
            Self::DuplicateJsonKeyPayload => "DuplicateJsonKeyPayload",
            Self::PolicyDowngrade => "PolicyDowngrade",
            Self::DirectAuthorityRequest => "DirectAuthorityRequest",
            Self::ForgedAcceptedDecision => "ForgedAcceptedDecision",
            Self::MissingNonclaim => "MissingNonclaim",
            Self::MissingSourceDigest => "MissingSourceDigest",
            Self::StaleJournalTip => "StaleJournalTip",
            Self::SignerBeforeAdmission => "SignerBeforeAdmission",
        }
    }

    fn ordinal(self) -> u8 {
        match self {
            Self::Benign => 0,
            Self::PromptInjectionPayment => 1,
            Self::WrongCounterparty => 2,
            Self::AmountLimitBypass => 3,
            Self::SourceDigestDrift => 4,
            Self::StaleApprovalReplay => 5,
            Self::DuplicateJsonKeyPayload => 6,
            Self::PolicyDowngrade => 7,
            Self::DirectAuthorityRequest => 8,
            Self::ForgedAcceptedDecision => 9,
            Self::MissingNonclaim => 10,
            Self::MissingSourceDigest => 11,
            Self::StaleJournalTip => 12,
            Self::SignerBeforeAdmission => 13,
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CheckerModelLaneProvenance {
    pub lane_kind: CheckerGatewayModelLaneKind,
    pub model_family: String,
    pub artifact_id: String,
    pub runtime: String,
    pub prompt_template_digest: [u8; 32],
    pub input_corpus_digest: [u8; 32],
    pub output_bundle_digest: [u8; 32],
    pub non_secret: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CheckerGatewayActionProposal {
    pub id: CheckerGatewayActionId,
    pub subject: CheckerSubjectId,
    pub action_kind: CheckerGatewayActionKind,
    pub target: String,
    pub value_units: u64,
    pub source_artifact_digests: Vec<CheckerArtifactDigest>,
    pub nonclaims: Vec<CheckerNonclaim>,
    pub model_lane: CheckerModelLaneProvenance,
    pub threat_labels: Vec<CheckerGatewayThreatLabel>,
    pub direct_authority_requested: bool,
    pub signer_or_tool_requested_before_admission: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CheckerIndependenceProfile {
    pub diverse_axes: Vec<String>,
    pub shared_axes: Vec<String>,
    pub imported_trust_axes: Vec<String>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CheckerComparisonClassification {
    LocalImplementationDiverseCheckerAgreement,
    LocalImplementationDiverseCheckerMismatch,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CheckerDigestResult {
    pub schema_version: String,
    pub state_slice: String,
    pub checker_implementation_id: String,
    pub digest_tag: String,
    pub encoded_preimage: Vec<u8>,
    pub encoded_preimage_length: u64,
    pub digest: [u8; 32],
    pub encoder_identity: String,
    pub hash_provider_identity: String,
    pub independence_profile: CheckerIndependenceProfile,
    pub claim_boundary: String,
    pub explicit_nonclaims: Vec<String>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum CheckerError {
    DuplicateSourceArtifact(CheckerArtifactDigest),
    DuplicateNonclaim(CheckerNonclaim),
    DuplicateThreatLabel(CheckerGatewayThreatLabel),
}

#[derive(Clone, Debug, Eq, PartialEq, Ord, PartialOrd)]
pub enum CheckerValidationIssue {
    SchemaVersionMismatch,
    StateSliceMismatch,
    CheckerImplementationIdMismatch,
    DigestTagMismatch,
    EncodedPreimageMismatch,
    EncodedPreimageLengthMismatch,
    DigestMismatch,
    EncoderIdentityMismatch,
    HashProviderIdentityMismatch,
    IndependenceProfileMismatch,
    ClaimBoundaryMismatch,
    ExplicitNonclaimsMismatch,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CheckerValidation {
    pub valid: bool,
    pub issues: Vec<CheckerValidationIssue>,
}

pub fn checker_independence_profile() -> CheckerIndependenceProfile {
    CheckerIndependenceProfile {
        diverse_axes: strings(&[
            "separate source crate and module",
            "checker-owned proposal and enum types",
            "manual field emission and enum mapping",
            "manual set ordering and JSON string escaping",
            "ring SHA-256 instead of production sha2",
            "no production preimage or digest call",
            "no Serde derive or serde_json serializer",
        ]),
        shared_axes: strings(&[
            "Rust language and compiler",
            "Rust standard library",
            "workspace toolchain and build host",
            "CPU operating system and local operator",
            "Phase 660 fixture values",
            "digest tag and schema knowledge",
            "human schema transcription",
            "e2e comparison harness",
        ]),
        imported_trust_axes: strings(&[
            "ring native and assembly implementation correctness",
            "production sha2 implementation correctness",
            "Rust compiler and linker correctness",
            "Phase 660 golden vector correctness",
            "SHA-256 collision resistance",
        ]),
    }
}

pub fn checker_required_nonclaims() -> Vec<String> {
    strings(&[
        "not independent external reproduction",
        "not independent formal verification",
        "not source correspondence proof",
        "not a checker transcript",
        "not accepted evidence",
        "not accepted formal evidence",
        "not Level2+ evidence",
        "no score-axis population",
        "not benchmark evidence",
        "not semantic correctness",
        "not production readiness",
        "not SOTA",
        "not full security",
        "no action authority",
    ])
}

pub fn encode_gateway_action_proposal_v1(
    proposal: &CheckerGatewayActionProposal,
) -> Result<Vec<u8>, CheckerError> {
    let artifacts = sorted_artifacts(proposal)?;
    let nonclaims = sorted_nonclaims(proposal)?;
    let threats = sorted_threats(proposal)?;
    let mut out = Vec::with_capacity(1024);

    out.push(b'[');
    write_json_string(&mut out, CHECKER_DIGEST_TAG);
    out.extend_from_slice(b",{");

    write_field_name(&mut out, "id", false);
    write_json_string(&mut out, &proposal.id.0);
    write_field_name(&mut out, "subject", true);
    write_json_string(&mut out, &proposal.subject.0);
    write_field_name(&mut out, "action_kind", true);
    write_json_string(&mut out, proposal.action_kind.label());
    write_field_name(&mut out, "target", true);
    write_json_string(&mut out, &proposal.target);
    write_field_name(&mut out, "value_units", true);
    write_u64(&mut out, proposal.value_units);

    write_field_name(&mut out, "source_artifact_digests", true);
    out.push(b'[');
    for (index, artifact) in artifacts.iter().enumerate() {
        if index > 0 {
            out.push(b',');
        }
        out.push(b'{');
        write_field_name(&mut out, "id", false);
        write_json_string(&mut out, &artifact.id);
        write_field_name(&mut out, "sha256", true);
        write_byte_array(&mut out, &artifact.sha256);
        out.push(b'}');
    }
    out.push(b']');

    write_field_name(&mut out, "nonclaims", true);
    out.push(b'[');
    for (index, nonclaim) in nonclaims.iter().enumerate() {
        if index > 0 {
            out.push(b',');
        }
        write_json_string(&mut out, &nonclaim.0);
    }
    out.push(b']');

    write_field_name(&mut out, "model_lane", true);
    out.push(b'{');
    write_field_name(&mut out, "lane_kind", false);
    write_json_string(&mut out, proposal.model_lane.lane_kind.label());
    write_field_name(&mut out, "model_family", true);
    write_json_string(&mut out, &proposal.model_lane.model_family);
    write_field_name(&mut out, "artifact_id", true);
    write_json_string(&mut out, &proposal.model_lane.artifact_id);
    write_field_name(&mut out, "runtime", true);
    write_json_string(&mut out, &proposal.model_lane.runtime);
    write_field_name(&mut out, "prompt_template_digest", true);
    write_byte_array(&mut out, &proposal.model_lane.prompt_template_digest);
    write_field_name(&mut out, "input_corpus_digest", true);
    write_byte_array(&mut out, &proposal.model_lane.input_corpus_digest);
    write_field_name(&mut out, "output_bundle_digest", true);
    write_byte_array(&mut out, &proposal.model_lane.output_bundle_digest);
    write_field_name(&mut out, "non_secret", true);
    write_bool(&mut out, proposal.model_lane.non_secret);
    out.push(b'}');

    write_field_name(&mut out, "threat_labels", true);
    out.push(b'[');
    for (index, threat) in threats.iter().enumerate() {
        if index > 0 {
            out.push(b',');
        }
        write_json_string(&mut out, threat.label());
    }
    out.push(b']');

    write_field_name(&mut out, "direct_authority_requested", true);
    write_bool(&mut out, proposal.direct_authority_requested);
    write_field_name(&mut out, "signer_or_tool_requested_before_admission", true);
    write_bool(&mut out, proposal.signer_or_tool_requested_before_admission);
    out.extend_from_slice(b"}]");

    Ok(out)
}

pub fn checker_sha256(bytes: &[u8]) -> [u8; 32] {
    let digest = digest::digest(&digest::SHA256, bytes);
    let mut out = [0; 32];
    out.copy_from_slice(digest.as_ref());
    out
}

pub fn check_gateway_action_proposal_digest_v1(
    proposal: &CheckerGatewayActionProposal,
) -> Result<CheckerDigestResult, CheckerError> {
    let encoded_preimage = encode_gateway_action_proposal_v1(proposal)?;
    Ok(CheckerDigestResult {
        schema_version: CHECKER_SCHEMA_VERSION.to_owned(),
        state_slice: CHECKER_STATE_SLICE.to_owned(),
        checker_implementation_id: CHECKER_IMPLEMENTATION_ID.to_owned(),
        digest_tag: CHECKER_DIGEST_TAG.to_owned(),
        encoded_preimage_length: encoded_preimage.len() as u64,
        digest: checker_sha256(&encoded_preimage),
        encoded_preimage,
        encoder_identity: CHECKER_ENCODER_ID.to_owned(),
        hash_provider_identity: CHECKER_HASH_PROVIDER_ID.to_owned(),
        independence_profile: checker_independence_profile(),
        claim_boundary: CHECKER_CLAIM_BOUNDARY.to_owned(),
        explicit_nonclaims: checker_required_nonclaims(),
    })
}

pub fn validate_checker_digest_result(
    proposal: &CheckerGatewayActionProposal,
    result: &CheckerDigestResult,
) -> Result<CheckerValidation, CheckerError> {
    let expected = check_gateway_action_proposal_digest_v1(proposal)?;
    let mut issues = Vec::new();
    check_equal(
        result.schema_version == expected.schema_version,
        CheckerValidationIssue::SchemaVersionMismatch,
        &mut issues,
    );
    check_equal(
        result.state_slice == expected.state_slice,
        CheckerValidationIssue::StateSliceMismatch,
        &mut issues,
    );
    check_equal(
        result.checker_implementation_id == expected.checker_implementation_id,
        CheckerValidationIssue::CheckerImplementationIdMismatch,
        &mut issues,
    );
    check_equal(
        result.digest_tag == expected.digest_tag,
        CheckerValidationIssue::DigestTagMismatch,
        &mut issues,
    );
    check_equal(
        result.encoded_preimage == expected.encoded_preimage,
        CheckerValidationIssue::EncodedPreimageMismatch,
        &mut issues,
    );
    check_equal(
        result.encoded_preimage_length == expected.encoded_preimage_length,
        CheckerValidationIssue::EncodedPreimageLengthMismatch,
        &mut issues,
    );
    check_equal(
        result.digest == expected.digest,
        CheckerValidationIssue::DigestMismatch,
        &mut issues,
    );
    check_equal(
        result.encoder_identity == expected.encoder_identity,
        CheckerValidationIssue::EncoderIdentityMismatch,
        &mut issues,
    );
    check_equal(
        result.hash_provider_identity == expected.hash_provider_identity,
        CheckerValidationIssue::HashProviderIdentityMismatch,
        &mut issues,
    );
    check_equal(
        result.independence_profile == expected.independence_profile,
        CheckerValidationIssue::IndependenceProfileMismatch,
        &mut issues,
    );
    check_equal(
        result.claim_boundary == expected.claim_boundary,
        CheckerValidationIssue::ClaimBoundaryMismatch,
        &mut issues,
    );
    check_equal(
        result.explicit_nonclaims == expected.explicit_nonclaims,
        CheckerValidationIssue::ExplicitNonclaimsMismatch,
        &mut issues,
    );
    Ok(CheckerValidation {
        valid: issues.is_empty(),
        issues,
    })
}

fn sorted_artifacts(
    proposal: &CheckerGatewayActionProposal,
) -> Result<Vec<&CheckerArtifactDigest>, CheckerError> {
    let mut artifacts = proposal.source_artifact_digests.iter().collect::<Vec<_>>();
    artifacts.sort_by(|left, right| {
        left.id
            .cmp(&right.id)
            .then_with(|| left.sha256.cmp(&right.sha256))
    });
    if let Some(duplicate) = artifacts
        .windows(2)
        .find(|window| window[0] == window[1])
        .map(|window| window[0])
    {
        return Err(CheckerError::DuplicateSourceArtifact(duplicate.clone()));
    }
    Ok(artifacts)
}

fn sorted_nonclaims(
    proposal: &CheckerGatewayActionProposal,
) -> Result<Vec<&CheckerNonclaim>, CheckerError> {
    let mut nonclaims = proposal.nonclaims.iter().collect::<Vec<_>>();
    nonclaims.sort_by(|left, right| left.0.cmp(&right.0));
    if let Some(duplicate) = nonclaims
        .windows(2)
        .find(|window| window[0] == window[1])
        .map(|window| window[0])
    {
        return Err(CheckerError::DuplicateNonclaim(duplicate.clone()));
    }
    Ok(nonclaims)
}

fn sorted_threats(
    proposal: &CheckerGatewayActionProposal,
) -> Result<Vec<CheckerGatewayThreatLabel>, CheckerError> {
    let mut threats = proposal.threat_labels.clone();
    threats.sort_by_key(|threat| threat.ordinal());
    if let Some(duplicate) = threats
        .windows(2)
        .find(|window| window[0] == window[1])
        .map(|window| window[0])
    {
        return Err(CheckerError::DuplicateThreatLabel(duplicate));
    }
    Ok(threats)
}

fn write_field_name(out: &mut Vec<u8>, name: &str, comma: bool) {
    if comma {
        out.push(b',');
    }
    write_json_string(out, name);
    out.push(b':');
}

fn write_json_string(out: &mut Vec<u8>, value: &str) {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    out.push(b'"');
    for &byte in value.as_bytes() {
        match byte {
            b'"' => out.extend_from_slice(br#"\""#),
            b'\\' => out.extend_from_slice(br#"\\"#),
            0x08 => out.extend_from_slice(br#"\b"#),
            b'\t' => out.extend_from_slice(br#"\t"#),
            b'\n' => out.extend_from_slice(br#"\n"#),
            0x0c => out.extend_from_slice(br#"\f"#),
            b'\r' => out.extend_from_slice(br#"\r"#),
            0x00..=0x1f => {
                out.extend_from_slice(br#"\u00"#);
                out.push(HEX[(byte >> 4) as usize]);
                out.push(HEX[(byte & 0x0f) as usize]);
            }
            _ => out.push(byte),
        }
    }
    out.push(b'"');
}

fn write_byte_array(out: &mut Vec<u8>, value: &[u8; 32]) {
    out.push(b'[');
    for (index, byte) in value.iter().enumerate() {
        if index > 0 {
            out.push(b',');
        }
        write_u64(out, u64::from(*byte));
    }
    out.push(b']');
}

fn write_u64(out: &mut Vec<u8>, value: u64) {
    out.extend_from_slice(value.to_string().as_bytes());
}

fn write_bool(out: &mut Vec<u8>, value: bool) {
    out.extend_from_slice(if value { b"true" } else { b"false" });
}

fn strings(values: &[&str]) -> Vec<String> {
    values.iter().map(|value| (*value).to_owned()).collect()
}

fn check_equal(
    equal: bool,
    issue: CheckerValidationIssue,
    issues: &mut Vec<CheckerValidationIssue>,
) {
    if !equal {
        issues.push(issue);
    }
}
