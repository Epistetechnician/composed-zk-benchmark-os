use hsai_agent_admission::{
    evaluate_mesh_hsai_admission_request, mesh_repo_patch_admission_policy, MeshAttestationRef,
    MeshEvidenceGate, MeshHsaiAdmissionRequest, MeshHsaiAdmissionVerdict, NonClaimLabel,
    MESH_COMBINED_PROOF_PACKET_SCHEMA_VERSION, MESH_HSAI_ADMISSION_DECISION_SCHEMA_VERSION,
    MESH_HSAI_ADMISSION_REQUEST_SCHEMA_VERSION,
};
use hsai_claim_envelope::Hash;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::fmt;
use std::str::FromStr;

pub(crate) const MAX_INPUT_BYTES: usize = 1024 * 1024;
const MAX_NESTING_DEPTH: usize = 64;
const ACTION_KIND: &str = "repo_patch";
const STATE_SLICE: &str = "phase-747-hsai-mesh-evidence-aware-admission-cli";
const REQUEST_V2: &str = "mesh.hsai_admission_request.v2";
const PRE_EXECUTION_EVIDENCE_V1: &str = "mesh.repo_patch_pre_execution_evidence.v1";
const PREFLIGHT_STATE_SLICE: &str = "mesh.repo_patch_disposable_worktree.v1";
const BACKEND_V1: &str = "hsai-rust-v1-parity-cli";
const BACKEND_RUN_ID_V1: &str = "local_rust_v1_parity";
const NONCLAIM_V1: &str = "Rust v1 parity admission metadata only; the request binds but does not embed the pre-execution evidence packet; not formal proof, accepted evidence, production certification, or authority to execute a patch";
const BACKEND_V2: &str = "hsai-rust-v2-evidence-aware-cli";
const BACKEND_RUN_ID_V2: &str = "local_rust_v2_structural_preflight";
const NONCLAIM_V2: &str = "Structural local preflight validation only; validates embedded bytes and declarations but is not proof that the declared commands ran, not formal proof, accepted evidence, production certification, or authority to execute a patch";

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum Error {
    EmptyCurrentPolicyId,
    InputTooLarge,
    ExcessiveNesting,
    MalformedOrDuplicateJson,
    InvalidWireShape,
    DuplicateSetEntry(&'static str),
    MalformedDigest(&'static str),
    DigestMismatch(&'static str),
    UnsupportedActionKind,
    InvalidActorRef,
    InvalidCreatedAt,
    Serialization,
}

impl fmt::Display for Error {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::EmptyCurrentPolicyId => formatter.write_str("current policy id is empty"),
            Self::InputTooLarge => formatter.write_str("Mesh admission input exceeds 1 MiB"),
            Self::ExcessiveNesting => {
                formatter.write_str("Mesh admission input exceeds the nesting limit")
            }
            Self::MalformedOrDuplicateJson => formatter.write_str(
                "Mesh admission input is malformed, has duplicate keys, or has trailing data",
            ),
            Self::InvalidWireShape => {
                formatter.write_str("Mesh admission input does not match a supported wire shape")
            }
            Self::DuplicateSetEntry(field) => {
                write!(
                    formatter,
                    "Mesh admission input contains a duplicate {field} entry"
                )
            }
            Self::MalformedDigest(field) => {
                write!(
                    formatter,
                    "Mesh admission input contains a malformed {field} digest"
                )
            }
            Self::DigestMismatch(field) => {
                write!(formatter, "Mesh admission input {field} digest mismatch")
            }
            Self::UnsupportedActionKind => {
                formatter.write_str("Mesh admission input action_kind is not repo_patch")
            }
            Self::InvalidActorRef => formatter.write_str("Mesh admission actor_ref is invalid"),
            Self::InvalidCreatedAt => formatter.write_str("Mesh admission created_at is invalid"),
            Self::Serialization => formatter.write_str("Mesh admission serialization failed"),
        }
    }
}

impl std::error::Error for Error {}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct ActorRef {
    actor_id: String,
    team_id: String,
}

#[derive(Clone, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(deny_unknown_fields)]
struct AttestationRef {
    kind: String,
    digest: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct WireRequestV1 {
    schema_version: String,
    mesh_run_id: String,
    mesh_action_id: String,
    action_kind: String,
    actor_ref: ActorRef,
    mesh_policy_id: String,
    action_proposal_digest: String,
    candidate_payload_digest: String,
    evidence_packet_digest: String,
    attestation_refs: Vec<AttestationRef>,
    requested_claims: Vec<String>,
    explicit_nonclaims: Vec<String>,
    created_at: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct CandidatePatchTemplate {
    target_file: String,
    find: String,
    replace: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct CandidateParameters {
    repo_path: String,
    allowed_paths: Vec<String>,
    protected_paths: Vec<String>,
    patch_template: CandidatePatchTemplate,
    test_commands: Vec<Vec<String>>,
    mesh_run_id: String,
    mesh_action_id: String,
    mesh_policy_id: String,
    actor_ref: ActorRef,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct CandidateExecutionPlan {
    system: String,
    action: String,
    parameters: CandidateParameters,
    rollback_plan: String,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct CandidatePayload {
    decision_id: String,
    trigger_id: String,
    decision_type: String,
    autonomy_tier: String,
    summary: String,
    reasoning: Value,
    expected_outcome: Value,
    risk: Value,
    confidence: Value,
    execution_plan: CandidateExecutionPlan,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PreflightTestResult {
    argv: Vec<String>,
    returncode: i32,
    stdout_digest: String,
    stderr_digest: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PreflightReceipt {
    state_slice: String,
    base_commit: String,
    base_tree: String,
    target_path: String,
    target_preimage_digest: String,
    target_postimage_digest: String,
    authorized_diff_digest: String,
    changed_paths: Vec<String>,
    test_results: Vec<PreflightTestResult>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct PreExecutionEvidence {
    schema_version: String,
    decision_id: String,
    evaluation_id: String,
    evaluation_passed: bool,
    final_recommendation: String,
    blocking_reasons: Vec<String>,
    stage_results: Value,
    stage_results_digest: String,
    preflight_receipt: PreflightReceipt,
}

#[derive(Clone, Debug, Deserialize, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct WireRequestV2 {
    schema_version: String,
    mesh_run_id: String,
    mesh_action_id: String,
    action_kind: String,
    actor_ref: ActorRef,
    mesh_policy_id: String,
    action_proposal_digest: String,
    candidate_payload_digest: String,
    evidence_packet_digest: String,
    attestation_refs: Vec<AttestationRef>,
    requested_claims: Vec<String>,
    explicit_nonclaims: Vec<String>,
    created_at: String,
    candidate_payload: CandidatePayload,
    pre_execution_evidence: PreExecutionEvidence,
}

struct DecisionContext<'a> {
    mesh_run_id: &'a str,
    mesh_action_id: &'a str,
    action_kind: &'a str,
    mesh_policy_id: &'a str,
    candidate_payload_digest: &'a str,
    evidence_packet_digest: &'a str,
    created_at: &'a str,
    backend: &'a str,
    backend_run_id: &'a str,
    nonclaim: &'a str,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct GateResult {
    gate: String,
    result: String,
    metadata_digest: String,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
struct FormalEvidenceMetadata {
    backend: String,
    backend_run_id: String,
    metadata_digest: String,
    nonclaim: String,
    state_slice: String,
    grants_authority: bool,
    production_readiness_claimed: bool,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct WireDecision {
    schema_version: String,
    decision_id: String,
    mesh_run_id: String,
    mesh_action_id: String,
    action_kind: String,
    request_digest: String,
    candidate_digest: String,
    decision: String,
    admission_policy_id: String,
    gate_results: Vec<GateResult>,
    accepted_claims: Vec<String>,
    enforced_nonclaims: Vec<String>,
    formal_evidence_metadata: FormalEvidenceMetadata,
    reason_codes: Vec<String>,
    decision_digest: String,
    created_at: String,
}

pub(crate) fn evaluate(input: &[u8], current_policy_id: &str) -> Result<WireDecision, Error> {
    if current_policy_id.trim().is_empty() || current_policy_id.trim() != current_policy_id {
        return Err(Error::EmptyCurrentPolicyId);
    }
    if input.len() > MAX_INPUT_BYTES {
        return Err(Error::InputTooLarge);
    }
    validate_nesting_depth(input)?;
    let original = DuplicateRejectingParser::parse(input)?;
    if !original.is_object() {
        return Err(Error::InvalidWireShape);
    }
    match original.get("schema_version").and_then(Value::as_str) {
        Some(MESH_HSAI_ADMISSION_REQUEST_SCHEMA_VERSION) => {
            evaluate_v1_value(original, current_policy_id)
        }
        Some(REQUEST_V2) => evaluate_v2_value(original, current_policy_id),
        _ => Err(Error::InvalidWireShape),
    }
}

fn evaluate_v1_value(original: Value, current_policy_id: &str) -> Result<WireDecision, Error> {
    let wire: WireRequestV1 =
        serde_json::from_value(original.clone()).map_err(|_| Error::InvalidWireShape)?;
    if serde_json::to_value(&wire).map_err(|_| Error::Serialization)? != original {
        return Err(Error::InvalidWireShape);
    }
    validate_wire_request(&wire)?;

    let request_digest = canonical_sha256(&original)?;
    let candidate_digest =
        parse_sha256_uri(&wire.candidate_payload_digest, "candidate_payload_digest")?;
    let evidence_digest = parse_sha256_uri(&wire.evidence_packet_digest, "evidence_packet")?;
    parse_sha256_uri(&wire.action_proposal_digest, "action_proposal")?;

    let attestation_refs = wire
        .attestation_refs
        .iter()
        .map(|reference| {
            Ok(MeshAttestationRef {
                ref_id: reference.kind.clone(),
                digest: parse_sha256_uri(&reference.digest, "attestation_ref")?,
                claim_binding: reference.kind.clone(),
            })
        })
        .collect::<Result<BTreeSet<_>, Error>>()?;
    let evidence_binding_passed = attestation_refs
        .iter()
        .any(|reference| reference.digest == evidence_digest);
    let evidence_reasons = if evidence_binding_passed {
        Vec::new()
    } else {
        vec!["evidence_packet_attestation_binding_mismatch".to_owned()]
    };
    let domain_request = MeshHsaiAdmissionRequest {
        schema_version: wire.schema_version.clone(),
        mesh_run_id: wire.mesh_run_id.clone(),
        mesh_action_id: wire.mesh_action_id.clone(),
        mesh_policy_id: wire.mesh_policy_id.clone(),
        candidate_digest,
        evidence_packet_schema_version: MESH_COMBINED_PROOF_PACKET_SCHEMA_VERSION.to_owned(),
        evidence_packet_digest: evidence_digest,
        attestation_refs,
        requested_claims: wire.requested_claims.iter().cloned().collect(),
        explicit_nonclaims: wire
            .explicit_nonclaims
            .iter()
            .cloned()
            .map(NonClaimLabel)
            .collect(),
        claim_weakenings: Vec::new(),
        candidate_evidence_gate: MeshEvidenceGate {
            gate_id: "candidate_evidence_gate".to_owned(),
            passed: evidence_binding_passed,
            evidence_digest,
            reason_codes: evidence_reasons.clone(),
        },
        accepted_evidence_gate: MeshEvidenceGate {
            gate_id: "accepted_evidence_gate".to_owned(),
            passed: evidence_binding_passed,
            evidence_digest,
            reason_codes: evidence_reasons,
        },
        formal_evidence_metadata: None,
        backend_run_metadata: None,
    };
    let policy = mesh_repo_patch_admission_policy(current_policy_id);
    let domain = evaluate_mesh_hsai_admission_request(&domain_request, &policy);
    if domain.grants_authority || domain.production_readiness_claimed {
        return Err(Error::Serialization);
    }
    map_decision(
        DecisionContext {
            mesh_run_id: &wire.mesh_run_id,
            mesh_action_id: &wire.mesh_action_id,
            action_kind: &wire.action_kind,
            mesh_policy_id: &wire.mesh_policy_id,
            candidate_payload_digest: &wire.candidate_payload_digest,
            evidence_packet_digest: &wire.evidence_packet_digest,
            created_at: &wire.created_at,
            backend: BACKEND_V1,
            backend_run_id: BACKEND_RUN_ID_V1,
            nonclaim: NONCLAIM_V1,
        },
        &domain,
        &request_digest,
    )
}

fn evaluate_v2_value(original: Value, current_policy_id: &str) -> Result<WireDecision, Error> {
    let wire: WireRequestV2 =
        serde_json::from_value(original.clone()).map_err(|_| Error::InvalidWireShape)?;
    if serde_json::to_value(&wire).map_err(|_| Error::Serialization)? != original {
        return Err(Error::InvalidWireShape);
    }
    validate_wire_request_v2(&wire)?;

    let request_digest = canonical_sha256(&original)?;
    let candidate_digest =
        parse_sha256_uri(&wire.candidate_payload_digest, "candidate_payload_digest")?;
    let expected_candidate_digest = canonical_sha256(&original["candidate_payload"])?;
    if wire.candidate_payload_digest != expected_candidate_digest {
        return Err(Error::DigestMismatch("candidate_payload"));
    }
    let evidence_digest = parse_sha256_uri(&wire.evidence_packet_digest, "evidence_packet")?;
    let expected_evidence_digest = canonical_sha256(&original["pre_execution_evidence"])?;
    if wire.evidence_packet_digest != expected_evidence_digest {
        return Err(Error::DigestMismatch("pre_execution_evidence"));
    }
    parse_sha256_uri(&wire.action_proposal_digest, "action_proposal")?;
    let expected_action_proposal_digest = canonical_sha256(&serde_json::json!({
        "decision_id": wire.candidate_payload.decision_id,
        "execution_plan": wire.candidate_payload.execution_plan,
        "risk": wire.candidate_payload.risk,
    }))?;
    if wire.action_proposal_digest != expected_action_proposal_digest {
        return Err(Error::DigestMismatch("action_proposal"));
    }
    parse_sha256_uri(
        &wire.pre_execution_evidence.stage_results_digest,
        "stage_results",
    )?;
    let expected_stage_results_digest =
        canonical_sha256(&original["pre_execution_evidence"]["stage_results"])?;
    if wire.pre_execution_evidence.stage_results_digest != expected_stage_results_digest {
        return Err(Error::DigestMismatch("stage_results"));
    }
    validate_preflight_digests(&wire.pre_execution_evidence.preflight_receipt)?;

    let attestation_refs = wire
        .attestation_refs
        .iter()
        .map(|reference| {
            Ok(MeshAttestationRef {
                ref_id: reference.kind.clone(),
                digest: parse_sha256_uri(&reference.digest, "attestation_ref")?,
                claim_binding: reference.kind.clone(),
            })
        })
        .collect::<Result<BTreeSet<_>, Error>>()?;

    let mut gate_reasons = Vec::new();
    validate_v2_bindings(&wire, current_policy_id, &mut gate_reasons);
    validate_v2_paths_and_tests(&wire, &mut gate_reasons);
    if !attestation_refs
        .iter()
        .any(|reference| reference.digest == evidence_digest)
    {
        push_reason(
            &mut gate_reasons,
            "evidence_packet_attestation_binding_mismatch",
        );
    }
    let gates_passed = gate_reasons.is_empty();
    let domain_request = MeshHsaiAdmissionRequest {
        schema_version: MESH_HSAI_ADMISSION_REQUEST_SCHEMA_VERSION.to_owned(),
        mesh_run_id: wire.mesh_run_id.clone(),
        mesh_action_id: wire.mesh_action_id.clone(),
        mesh_policy_id: wire.mesh_policy_id.clone(),
        candidate_digest,
        evidence_packet_schema_version: MESH_COMBINED_PROOF_PACKET_SCHEMA_VERSION.to_owned(),
        evidence_packet_digest: evidence_digest,
        attestation_refs,
        requested_claims: wire.requested_claims.iter().cloned().collect(),
        explicit_nonclaims: wire
            .explicit_nonclaims
            .iter()
            .cloned()
            .map(NonClaimLabel)
            .collect(),
        claim_weakenings: Vec::new(),
        candidate_evidence_gate: MeshEvidenceGate {
            gate_id: "candidate_evidence_gate".to_owned(),
            passed: gates_passed,
            evidence_digest,
            reason_codes: gate_reasons.clone(),
        },
        accepted_evidence_gate: MeshEvidenceGate {
            gate_id: "accepted_evidence_gate".to_owned(),
            passed: gates_passed,
            evidence_digest,
            reason_codes: gate_reasons,
        },
        formal_evidence_metadata: None,
        backend_run_metadata: None,
    };
    let policy = mesh_repo_patch_admission_policy(current_policy_id);
    let domain = evaluate_mesh_hsai_admission_request(&domain_request, &policy);
    if domain.grants_authority || domain.production_readiness_claimed {
        return Err(Error::Serialization);
    }
    map_decision(
        DecisionContext {
            mesh_run_id: &wire.mesh_run_id,
            mesh_action_id: &wire.mesh_action_id,
            action_kind: &wire.action_kind,
            mesh_policy_id: &wire.mesh_policy_id,
            candidate_payload_digest: &wire.candidate_payload_digest,
            evidence_packet_digest: &wire.evidence_packet_digest,
            created_at: &wire.created_at,
            backend: BACKEND_V2,
            backend_run_id: BACKEND_RUN_ID_V2,
            nonclaim: NONCLAIM_V2,
        },
        &domain,
        &request_digest,
    )
}

fn validate_wire_request_v2(wire: &WireRequestV2) -> Result<(), Error> {
    if wire.schema_version != REQUEST_V2 {
        return Err(Error::InvalidWireShape);
    }
    if wire.action_kind != ACTION_KIND {
        return Err(Error::UnsupportedActionKind);
    }
    if !is_trimmed_nonempty(&wire.actor_ref.actor_id)
        || !is_trimmed_nonempty(&wire.actor_ref.team_id)
    {
        return Err(Error::InvalidActorRef);
    }
    if !is_trimmed_nonempty(&wire.created_at) {
        return Err(Error::InvalidCreatedAt);
    }
    reject_duplicate_strings(&wire.requested_claims, "requested_claims")?;
    reject_duplicate_strings(&wire.explicit_nonclaims, "explicit_nonclaims")?;
    reject_duplicate_attestation_refs(&wire.attestation_refs)?;
    reject_duplicate_strings(
        &wire.pre_execution_evidence.blocking_reasons,
        "blocking_reasons",
    )?;
    reject_duplicate_strings(
        &wire
            .candidate_payload
            .execution_plan
            .parameters
            .allowed_paths,
        "allowed_paths",
    )?;
    reject_duplicate_strings(
        &wire
            .candidate_payload
            .execution_plan
            .parameters
            .protected_paths,
        "protected_paths",
    )?;
    reject_duplicate_strings(
        &wire.pre_execution_evidence.preflight_receipt.changed_paths,
        "changed_paths",
    )?;
    reject_duplicate_argv(
        &wire
            .candidate_payload
            .execution_plan
            .parameters
            .test_commands,
        "test_commands",
    )?;
    let result_argv = wire
        .pre_execution_evidence
        .preflight_receipt
        .test_results
        .iter()
        .map(|result| result.argv.clone())
        .collect::<Vec<_>>();
    reject_duplicate_argv(&result_argv, "test_results")
}

fn validate_v2_bindings(wire: &WireRequestV2, current_policy_id: &str, reasons: &mut Vec<String>) {
    let candidate = &wire.candidate_payload;
    let parameters = &candidate.execution_plan.parameters;
    let evidence = &wire.pre_execution_evidence;
    if candidate.decision_id != wire.mesh_action_id
        || parameters.mesh_action_id != wire.mesh_action_id
        || evidence.decision_id != wire.mesh_action_id
    {
        push_reason(reasons, "decision_action_binding_mismatch");
    }
    if parameters.mesh_run_id != wire.mesh_run_id {
        push_reason(reasons, "run_binding_mismatch");
    }
    if parameters.mesh_policy_id != wire.mesh_policy_id || wire.mesh_policy_id != current_policy_id
    {
        push_reason(reasons, "policy_binding_mismatch");
    }
    if parameters.actor_ref != wire.actor_ref {
        push_reason(reasons, "actor_binding_mismatch");
    }
    if candidate.decision_type != "investigate_and_patch"
        || candidate.execution_plan.system != "repo_patch_service"
        || candidate.execution_plan.action != "investigate_and_patch"
    {
        push_reason(reasons, "repo_patch_action_binding_mismatch");
    }
    if evidence.schema_version != PRE_EXECUTION_EVIDENCE_V1 {
        push_reason(reasons, "unsupported_pre_execution_evidence_schema");
    }
    if !is_trimmed_nonempty(&evidence.evaluation_id) {
        push_reason(reasons, "missing_evaluation_id");
    }
    if !evidence.evaluation_passed {
        push_reason(reasons, "mesh_evaluation_not_passed");
    }
    if evidence.final_recommendation != "execute" {
        push_reason(reasons, "mesh_recommendation_not_execute");
    }
    if !evidence.blocking_reasons.is_empty() {
        push_reason(reasons, "mesh_blocking_reasons_present");
    }
    if evidence.preflight_receipt.state_slice != PREFLIGHT_STATE_SLICE {
        push_reason(reasons, "preflight_state_slice_mismatch");
    }
}

fn validate_v2_paths_and_tests(wire: &WireRequestV2, reasons: &mut Vec<String>) {
    let parameters = &wire.candidate_payload.execution_plan.parameters;
    let preflight = &wire.pre_execution_evidence.preflight_receipt;
    let target = &parameters.patch_template.target_file;
    let paths_are_portable = is_portable_path(target)
        && is_portable_path(&preflight.target_path)
        && parameters
            .allowed_paths
            .iter()
            .all(|path| is_portable_path(path))
        && parameters
            .protected_paths
            .iter()
            .all(|path| is_portable_path(path))
        && preflight
            .changed_paths
            .iter()
            .all(|path| is_portable_path(path));
    if !paths_are_portable {
        push_reason(reasons, "nonportable_preflight_path");
    }
    if preflight.target_path != *target {
        push_reason(reasons, "preflight_target_binding_mismatch");
    }
    if !parameters.allowed_paths.contains(target)
        || preflight
            .changed_paths
            .iter()
            .any(|path| !parameters.allowed_paths.contains(path))
    {
        push_reason(reasons, "preflight_path_outside_allowed_paths");
    }
    if preflight.changed_paths.len() != 1 || preflight.changed_paths.first() != Some(target) {
        push_reason(reasons, "preflight_changed_paths_mismatch");
    }
    if preflight.changed_paths.iter().any(|changed| {
        parameters
            .protected_paths
            .iter()
            .any(|protected| path_is_same_or_descendant(changed, protected))
    }) {
        push_reason(reasons, "protected_path_modified");
    }
    if parameters.patch_template.find.is_empty()
        || parameters.patch_template.find == parameters.patch_template.replace
    {
        push_reason(reasons, "invalid_patch_template");
    }
    if !is_trimmed_nonempty(&parameters.repo_path) {
        push_reason(reasons, "invalid_repo_path");
    }
    if parameters.test_commands.is_empty() || preflight.test_results.is_empty() {
        push_reason(reasons, "preflight_test_results_empty");
    }
    if preflight
        .test_results
        .iter()
        .any(|result| result.argv.is_empty() || result.argv.iter().any(|value| value.is_empty()))
    {
        push_reason(reasons, "preflight_test_argv_invalid");
    }
    let result_argv = preflight
        .test_results
        .iter()
        .map(|result| result.argv.clone())
        .collect::<Vec<_>>();
    if result_argv != parameters.test_commands {
        push_reason(reasons, "preflight_test_command_binding_mismatch");
    }
    if preflight
        .test_results
        .iter()
        .any(|result| result.returncode != 0)
    {
        push_reason(reasons, "preflight_test_failed");
    }
    if preflight.target_preimage_digest == preflight.target_postimage_digest {
        push_reason(reasons, "preflight_preimage_postimage_equal");
    }
}

fn validate_preflight_digests(preflight: &PreflightReceipt) -> Result<(), Error> {
    if !is_git_object_id(&preflight.base_commit) || !is_git_object_id(&preflight.base_tree) {
        return Err(Error::MalformedDigest("base_git_object"));
    }
    parse_sha256_uri(&preflight.target_preimage_digest, "target_preimage")?;
    parse_sha256_uri(&preflight.target_postimage_digest, "target_postimage")?;
    parse_sha256_uri(&preflight.authorized_diff_digest, "authorized_diff")?;
    for result in &preflight.test_results {
        parse_sha256_uri(&result.stdout_digest, "test_stdout")?;
        parse_sha256_uri(&result.stderr_digest, "test_stderr")?;
    }
    Ok(())
}

fn validate_wire_request(wire: &WireRequestV1) -> Result<(), Error> {
    if wire.schema_version != MESH_HSAI_ADMISSION_REQUEST_SCHEMA_VERSION {
        return Err(Error::InvalidWireShape);
    }
    if wire.action_kind != ACTION_KIND {
        return Err(Error::UnsupportedActionKind);
    }
    if !is_trimmed_nonempty(&wire.actor_ref.actor_id)
        || !is_trimmed_nonempty(&wire.actor_ref.team_id)
    {
        return Err(Error::InvalidActorRef);
    }
    if !is_trimmed_nonempty(&wire.created_at) {
        return Err(Error::InvalidCreatedAt);
    }
    reject_duplicate_strings(&wire.requested_claims, "requested_claims")?;
    reject_duplicate_strings(&wire.explicit_nonclaims, "explicit_nonclaims")?;
    let mut refs = BTreeSet::new();
    for reference in &wire.attestation_refs {
        if !refs.insert((reference.kind.clone(), reference.digest.clone())) {
            return Err(Error::DuplicateSetEntry("attestation_refs"));
        }
    }
    Ok(())
}

fn reject_duplicate_strings(values: &[String], field: &'static str) -> Result<(), Error> {
    let mut seen = BTreeSet::new();
    for value in values {
        if !seen.insert(value) {
            return Err(Error::DuplicateSetEntry(field));
        }
    }
    Ok(())
}

fn reject_duplicate_attestation_refs(values: &[AttestationRef]) -> Result<(), Error> {
    let mut seen = BTreeSet::new();
    for value in values {
        if !seen.insert((value.kind.clone(), value.digest.clone())) {
            return Err(Error::DuplicateSetEntry("attestation_refs"));
        }
    }
    Ok(())
}

fn reject_duplicate_argv(values: &[Vec<String>], field: &'static str) -> Result<(), Error> {
    let mut seen = BTreeSet::new();
    for value in values {
        if !seen.insert(value) {
            return Err(Error::DuplicateSetEntry(field));
        }
    }
    Ok(())
}

fn is_portable_path(path: &str) -> bool {
    !path.is_empty()
        && path.trim() == path
        && !path.starts_with('/')
        && !path.ends_with('/')
        && !path.contains('\\')
        && path.split('/').all(|segment| {
            !segment.is_empty()
                && !matches!(segment, "." | "..")
                && segment
                    .chars()
                    .all(|ch| ch.is_ascii_alphanumeric() || matches!(ch, '-' | '_' | '.'))
        })
}

fn path_is_same_or_descendant(path: &str, ancestor: &str) -> bool {
    path == ancestor
        || path
            .strip_prefix(ancestor)
            .is_some_and(|suffix| suffix.starts_with('/'))
}

fn is_git_object_id(value: &str) -> bool {
    matches!(value.len(), 40 | 64)
        && value
            .as_bytes()
            .iter()
            .all(|byte| byte.is_ascii_digit() || matches!(*byte, b'a'..=b'f'))
}

fn push_reason(reasons: &mut Vec<String>, reason: &str) {
    if !reasons.iter().any(|existing| existing == reason) {
        reasons.push(reason.to_owned());
    }
}

fn validate_nesting_depth(input: &[u8]) -> Result<(), Error> {
    let mut depth = 0usize;
    let mut in_string = false;
    let mut escaped = false;
    for byte in input {
        if in_string {
            if escaped {
                escaped = false;
            } else if *byte == b'\\' {
                escaped = true;
            } else if *byte == b'"' {
                in_string = false;
            }
        } else if *byte == b'"' {
            in_string = true;
        } else if matches!(*byte, b'{' | b'[') {
            depth = depth.saturating_add(1);
            if depth > MAX_NESTING_DEPTH {
                return Err(Error::ExcessiveNesting);
            }
        } else if matches!(*byte, b'}' | b']') {
            depth = depth.saturating_sub(1);
        }
    }
    Ok(())
}

fn parse_sha256_uri(value: &str, field: &'static str) -> Result<Hash, Error> {
    let Some(hex) = value.strip_prefix("sha256:") else {
        return Err(Error::MalformedDigest(field));
    };
    if hex.len() != 64
        || !hex
            .as_bytes()
            .iter()
            .all(|byte| byte.is_ascii_digit() || matches!(*byte, b'a'..=b'f'))
    {
        return Err(Error::MalformedDigest(field));
    }
    let mut out = [0u8; 32];
    for (index, pair) in hex.as_bytes().chunks_exact(2).enumerate() {
        out[index] = (hex_nibble(pair[0]) << 4) | hex_nibble(pair[1]);
    }
    if out == [0; 32] {
        return Err(Error::MalformedDigest(field));
    }
    Ok(Hash(out))
}

fn hex_nibble(byte: u8) -> u8 {
    match byte {
        b'0'..=b'9' => byte - b'0',
        b'a'..=b'f' => 10 + byte - b'a',
        _ => 0,
    }
}

fn map_decision(
    context: DecisionContext<'_>,
    domain: &hsai_agent_admission::MeshHsaiAdmissionDecision,
    request_digest: &str,
) -> Result<WireDecision, Error> {
    let allowed = domain.verdict == MeshHsaiAdmissionVerdict::Allow;
    let gate_result = if allowed { "pass" } else { "fail" };
    let metadata_input = serde_json::json!({
        "backend": context.backend,
        "candidate_digest": context.candidate_payload_digest,
        "evidence_packet_digest": context.evidence_packet_digest,
        "request_digest": request_digest,
        "state_slice": STATE_SLICE,
    });
    let metadata_digest = canonical_sha256(&metadata_input)?;
    let mut decision = WireDecision {
        schema_version: MESH_HSAI_ADMISSION_DECISION_SCHEMA_VERSION.to_owned(),
        decision_id: format!("hsai_decision_{}", context.mesh_action_id),
        mesh_run_id: context.mesh_run_id.to_owned(),
        mesh_action_id: context.mesh_action_id.to_owned(),
        action_kind: context.action_kind.to_owned(),
        request_digest: request_digest.to_owned(),
        candidate_digest: context.candidate_payload_digest.to_owned(),
        decision: if allowed { "allow" } else { "deny" }.to_owned(),
        admission_policy_id: context.mesh_policy_id.to_owned(),
        gate_results: vec![
            GateResult {
                gate: "candidate_evidence".to_owned(),
                result: gate_result.to_owned(),
                metadata_digest: context.evidence_packet_digest.to_owned(),
            },
            GateResult {
                gate: "nonclaim_enforcement".to_owned(),
                result: gate_result.to_owned(),
                metadata_digest: metadata_digest.clone(),
            },
        ],
        accepted_claims: domain.accepted_claims.iter().cloned().collect(),
        enforced_nonclaims: domain
            .enforced_nonclaims
            .iter()
            .map(|nonclaim| nonclaim.0.clone())
            .collect(),
        formal_evidence_metadata: FormalEvidenceMetadata {
            backend: context.backend.to_owned(),
            backend_run_id: context.backend_run_id.to_owned(),
            metadata_digest,
            nonclaim: context.nonclaim.to_owned(),
            state_slice: STATE_SLICE.to_owned(),
            grants_authority: domain.grants_authority,
            production_readiness_claimed: domain.production_readiness_claimed,
        },
        reason_codes: domain.reason_codes.clone(),
        decision_digest: String::new(),
        created_at: context.created_at.to_owned(),
    };
    let mut decision_value = serde_json::to_value(&decision).map_err(|_| Error::Serialization)?;
    decision_value
        .as_object_mut()
        .ok_or(Error::Serialization)?
        .remove("decision_digest");
    decision.decision_digest = canonical_sha256(&decision_value)?;
    Ok(decision)
}

fn canonical_sha256(value: &Value) -> Result<String, Error> {
    let encoded = canonical_json(value)?;
    let digest = Sha256::digest(encoded.as_bytes());
    Ok(format!("sha256:{}", hex_bytes(&digest)))
}

fn canonical_json(value: &Value) -> Result<String, Error> {
    match value {
        Value::Null => Ok("null".to_owned()),
        Value::Bool(value) => Ok(value.to_string()),
        Value::Number(value) => Ok(value.to_string()),
        Value::String(value) => serde_json::to_string(value).map_err(|_| Error::Serialization),
        Value::Array(values) => {
            let body = values
                .iter()
                .map(canonical_json)
                .collect::<Result<Vec<_>, _>>()?
                .join(",");
            Ok(format!("[{body}]"))
        }
        Value::Object(map) => {
            let mut entries = map.iter().collect::<Vec<_>>();
            entries.sort_by(|(left, _), (right, _)| left.cmp(right));
            let body = entries
                .into_iter()
                .map(|(key, value)| {
                    Ok(format!(
                        "{}:{}",
                        serde_json::to_string(key).map_err(|_| Error::Serialization)?,
                        canonical_json(value)?
                    ))
                })
                .collect::<Result<Vec<_>, Error>>()?
                .join(",");
            Ok(format!("{{{body}}}"))
        }
    }
}

fn hex_bytes(bytes: &[u8]) -> String {
    let mut encoded = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        use std::fmt::Write as _;
        write!(&mut encoded, "{byte:02x}").expect("writing to String cannot fail");
    }
    encoded
}

fn is_trimmed_nonempty(value: &str) -> bool {
    !value.is_empty() && value.trim() == value
}

struct DuplicateRejectingParser<'a> {
    input: &'a [u8],
    pos: usize,
}

impl<'a> DuplicateRejectingParser<'a> {
    fn parse(input: &'a [u8]) -> Result<Value, Error> {
        let mut parser = Self { input, pos: 0 };
        let value = parser.parse_value()?;
        parser.skip_whitespace();
        if parser.peek().is_some() {
            return Err(Error::MalformedOrDuplicateJson);
        }
        Ok(value)
    }

    fn remaining(&self) -> &'a [u8] {
        &self.input[self.pos..]
    }

    fn peek(&self) -> Option<u8> {
        self.remaining().first().copied()
    }

    fn bump(&mut self) -> Result<u8, Error> {
        let byte = self.peek().ok_or(Error::MalformedOrDuplicateJson)?;
        self.pos += 1;
        Ok(byte)
    }

    fn skip_whitespace(&mut self) {
        while matches!(self.peek(), Some(b' ' | b'\n' | b'\r' | b'\t')) {
            self.pos += 1;
        }
    }

    fn expect_byte(&mut self, expected: u8) -> Result<(), Error> {
        if self.bump()? == expected {
            Ok(())
        } else {
            Err(Error::MalformedOrDuplicateJson)
        }
    }

    fn parse_value(&mut self) -> Result<Value, Error> {
        self.skip_whitespace();
        match self.peek() {
            Some(b'n') => self.parse_null(),
            Some(b't') | Some(b'f') => self.parse_bool(),
            Some(b'"') => self.parse_string().map(Value::String),
            Some(b'[') => self.parse_array(),
            Some(b'{') => self.parse_object(),
            Some(b'0'..=b'9') | Some(b'-') => self.parse_number(),
            _ => Err(Error::MalformedOrDuplicateJson),
        }
    }

    fn parse_null(&mut self) -> Result<Value, Error> {
        if self.remaining().starts_with(b"null") {
            self.pos += 4;
            Ok(Value::Null)
        } else {
            Err(Error::MalformedOrDuplicateJson)
        }
    }

    fn parse_bool(&mut self) -> Result<Value, Error> {
        if self.remaining().starts_with(b"true") {
            self.pos += 4;
            Ok(Value::Bool(true))
        } else if self.remaining().starts_with(b"false") {
            self.pos += 5;
            Ok(Value::Bool(false))
        } else {
            Err(Error::MalformedOrDuplicateJson)
        }
    }

    fn parse_string(&mut self) -> Result<String, Error> {
        let start = self.pos;
        self.expect_byte(b'"')?;
        loop {
            match self.bump()? {
                b'"' => {
                    return serde_json::from_slice(&self.input[start..self.pos])
                        .map_err(|_| Error::MalformedOrDuplicateJson);
                }
                b'\\' => {
                    self.bump()?;
                }
                _ => {}
            }
        }
    }

    fn parse_number(&mut self) -> Result<Value, Error> {
        let start = self.pos;
        if self.peek() == Some(b'-') {
            self.pos += 1;
        }
        if self.peek() == Some(b'0') {
            self.pos += 1;
        } else {
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.pos += 1;
            }
        }
        if self.peek() == Some(b'.') {
            self.pos += 1;
            if !matches!(self.peek(), Some(b'0'..=b'9')) {
                return Err(Error::MalformedOrDuplicateJson);
            }
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.pos += 1;
            }
        }
        if matches!(self.peek(), Some(b'e' | b'E')) {
            self.pos += 1;
            if matches!(self.peek(), Some(b'+' | b'-')) {
                self.pos += 1;
            }
            if !matches!(self.peek(), Some(b'0'..=b'9')) {
                return Err(Error::MalformedOrDuplicateJson);
            }
            while matches!(self.peek(), Some(b'0'..=b'9')) {
                self.pos += 1;
            }
        }
        let text = std::str::from_utf8(&self.input[start..self.pos])
            .map_err(|_| Error::MalformedOrDuplicateJson)?;
        let number =
            serde_json::Number::from_str(text).map_err(|_| Error::MalformedOrDuplicateJson)?;
        Ok(Value::Number(number))
    }

    fn parse_array(&mut self) -> Result<Value, Error> {
        self.expect_byte(b'[')?;
        self.skip_whitespace();
        let mut values = Vec::new();
        if self.peek() == Some(b']') {
            self.pos += 1;
            return Ok(Value::Array(values));
        }
        loop {
            values.push(self.parse_value()?);
            self.skip_whitespace();
            match self.peek() {
                Some(b',') => {
                    self.pos += 1;
                    self.skip_whitespace();
                }
                Some(b']') => {
                    self.pos += 1;
                    break;
                }
                _ => return Err(Error::MalformedOrDuplicateJson),
            }
        }
        Ok(Value::Array(values))
    }

    fn parse_object(&mut self) -> Result<Value, Error> {
        self.expect_byte(b'{')?;
        self.skip_whitespace();
        let mut map = serde_json::Map::new();
        let mut keys = BTreeSet::new();
        if self.peek() == Some(b'}') {
            self.pos += 1;
            return Ok(Value::Object(map));
        }
        loop {
            self.skip_whitespace();
            let key = self.parse_string()?;
            if !keys.insert(key.clone()) {
                return Err(Error::MalformedOrDuplicateJson);
            }
            self.skip_whitespace();
            self.expect_byte(b':')?;
            map.insert(key, self.parse_value()?);
            self.skip_whitespace();
            match self.peek() {
                Some(b',') => {
                    self.pos += 1;
                    self.skip_whitespace();
                }
                Some(b'}') => {
                    self.pos += 1;
                    break;
                }
                _ => return Err(Error::MalformedOrDuplicateJson),
            }
        }
        Ok(Value::Object(map))
    }
}
