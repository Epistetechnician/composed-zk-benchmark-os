// Operator-facing local gateway bridge acceptance-preview bundle runner.
//
// This example materializes local metadata only under the ignored
// `.gateway-demo-runs/` root. It creates one gateway report bundle, one
// gateway-bridge bundle, and one candidate-only acceptance-preview bundle.
// It does not read raw provider artifacts, call a provider, execute a model,
// mutate an accepted Evidence Ledger, create Level2+ evidence, populate score
// axes, or grant action authority.
// Nonclaims: not final acceptance; not accepted evidence; not production readiness; not semantic correctness; not live provider evidence; not accepted Evidence Ledger mutation; not Level2+ evidence; not benchmark evidence; not authority to execute an action.

use hsai_agent_admission::{
    build_gateway_attestation_challenge_binding,
    build_gateway_operator_bridge_acceptance_preview_report, build_gateway_operator_bridge_bundle,
    build_gateway_operator_bridge_promotion_preflight_report, gateway_local_default_policy,
    gateway_operator_bridge_acceptance_preview_claim_boundary,
    gateway_operator_bridge_acceptance_preview_request_schema_version,
    gateway_operator_bridge_acceptance_preview_required_nonclaims,
    gateway_operator_bridge_promotion_preflight_claim_boundary,
    gateway_operator_bridge_promotion_preflight_request_schema_version,
    gateway_operator_bridge_promotion_preflight_required_nonclaims,
    gateway_operator_bridge_required_nonclaims, materialize_gateway_corpus_output_run,
    materialize_gateway_operator_bridge_acceptance_preview_bundle,
    materialize_gateway_operator_bridge_bundle,
    read_gateway_operator_bridge_acceptance_preview_bundle, AdmissionPolicyId, AdmissionVerdict,
    ArtifactDigest, GatewayActionId, GatewayActionKind, GatewayActionPolicy, GatewayActionProposal,
    GatewayAttestationChallengeBinding, GatewayCorpusCase, GatewayModelLaneKind,
    GatewayModelLaneProvenance, GatewayOperatorArtifactReference,
    GatewayOperatorBridgeAcceptancePreviewDecision,
    GatewayOperatorBridgeAcceptancePreviewMaterializationRequest,
    GatewayOperatorBridgeAcceptancePreviewRequest, GatewayOperatorBridgeMaterializationRequest,
    GatewayOperatorBridgePromotionPreflightRequest, GatewayOperatorBridgePromotionReviewDecision,
    GatewayReportMaterializationRequest, NonClaimLabel,
};
use hsai_claim_envelope::{Hash, SubjectId};
use serde::Serialize;
use std::collections::{BTreeSet, HashSet};
use std::fs;
use std::path::{Path, PathBuf};

const ENV_ACK: &str = "HSAI_GATEWAY_ACCEPTANCE_PREVIEW_ACK";
const ENV_OUTPUT_ROOT: &str = "HSAI_GATEWAY_ACCEPTANCE_PREVIEW_OUTPUT_ROOT";
const ENV_BUNDLE_ID: &str = "HSAI_GATEWAY_ACCEPTANCE_PREVIEW_BUNDLE_ID";
const ENV_CREATED_AT_UNIX: &str = "HSAI_GATEWAY_ACCEPTANCE_PREVIEW_CREATED_AT_UNIX";
const ENV_OVERWRITE: &str = "HSAI_GATEWAY_ACCEPTANCE_PREVIEW_OVERWRITE";

const FIXED_ACK: &str =
    "I acknowledge this preview demo writes local metadata only under .gateway-demo-runs.";

#[derive(Debug, Serialize)]
struct GatewayAcceptancePreviewDemoSummary {
    schema_version: String,
    bundle_id: String,
    report_output_root: String,
    bridge_output_root: String,
    preview_output_root: String,
    source_preflight_report_digest: String,
    acceptance_preview_report_digest: String,
    preview_output_manifest_digest: String,
    bridge_bundle_digest: String,
    bridge_manifest_digest: String,
    gateway_report_digest: String,
    attestation_binding_digest: String,
    operator_artifact_reference_digest: String,
    declared_files: Vec<String>,
    claim_boundary: String,
    candidate_only: bool,
    mutates_accepted_evidence_ledger: bool,
    creates_level2_evidence: bool,
    populates_score_axes: bool,
    grants_authority: bool,
    retains_raw_provider_artifacts: bool,
    retains_credentials_or_secrets: bool,
    nonclaims: Vec<String>,
}

fn fail(message: &str) -> ! {
    panic!("gateway_acceptance_preview_bundle: {message}");
}

fn require_env(name: &str) -> String {
    match std::env::var(name) {
        Ok(value) if !value.trim().is_empty() => value,
        Ok(_) => fail(&format!("{name} must be non-empty")),
        Err(_) => fail(&format!("{name} must be set")),
    }
}

fn optional_env(name: &str) -> Option<String> {
    match std::env::var(name) {
        Ok(value) if !value.trim().is_empty() => Some(value),
        _ => None,
    }
}

fn parse_bool_env(name: &str, raw: Option<String>, default: bool) -> bool {
    match raw.as_deref() {
        None => default,
        Some("true") => true,
        Some("false") => false,
        Some(other) => fail(&format!("{name} must be 'true' or 'false', got '{other}'")),
    }
}

fn parse_created_at(raw: Option<String>) -> u64 {
    match raw {
        None => 0,
        Some(value) => value.parse::<u64>().unwrap_or_else(|_| {
            fail(&format!(
                "{ENV_CREATED_AT_UNIX} must be a non-negative integer"
            ))
        }),
    }
}

fn digest(seed: u8) -> Hash {
    Hash([seed; 32])
}

fn hash_hex(hash: Hash) -> String {
    let mut out = String::with_capacity(64);
    for byte in hash.0 {
        out.push_str(&format!("{byte:02x}"));
    }
    out
}

fn model_lane() -> GatewayModelLaneProvenance {
    GatewayModelLaneProvenance {
        lane_kind: GatewayModelLaneKind::LocalOpenWeight,
        model_family: "qwen-small-local-preview-demo".to_owned(),
        artifact_id: "qwen-small-local-preview-demo-q4".to_owned(),
        runtime: "local-preview-demo-fixture".to_owned(),
        prompt_template_digest: digest(41),
        input_corpus_digest: digest(42),
        output_bundle_digest: digest(43),
        non_secret: true,
    }
}

fn proposal(lane: &GatewayModelLaneProvenance) -> GatewayActionProposal {
    GatewayActionProposal {
        id: GatewayActionId("phase-253-preview-demo-action".to_owned()),
        subject: SubjectId("phase-253-preview-demo-agent".to_owned()),
        action_kind: GatewayActionKind::Payment,
        target: "treasury-safe".to_owned(),
        value_units: 50,
        source_artifact_digests: BTreeSet::from([ArtifactDigest {
            id: "phase-253-preview-demo-source".to_owned(),
            sha256: digest(40),
        }]),
        nonclaims: hsai_agent_admission::gateway_required_nonclaims(),
        model_lane: lane.clone(),
        threat_labels: BTreeSet::from([hsai_agent_admission::GatewayThreatLabel::Benign]),
        direct_authority_requested: false,
        signer_or_tool_requested_before_admission: false,
    }
}

fn gateway_policy() -> GatewayActionPolicy {
    gateway_local_default_policy(
        "phase-253-gateway-preview-policy",
        BTreeSet::from([GatewayActionKind::Payment]),
        BTreeSet::from(["treasury-safe".to_owned()]),
        100,
    )
}

fn attestation_binding(proposal: &GatewayActionProposal) -> GatewayAttestationChallengeBinding {
    build_gateway_attestation_challenge_binding(
        proposal,
        AdmissionPolicyId("phase-253-gateway-preview-policy".to_owned()),
        "phase-253-attested-runtime-anchor",
        "b2".repeat(91),
        43,
        0,
        600,
    )
    .unwrap_or_else(|err| fail(&format!("attestation binding failed: {err:?}")))
}

fn operator_reference() -> GatewayOperatorArtifactReference {
    GatewayOperatorArtifactReference {
        reference_id: "phase-253-repo-external-operator-live-reference".to_owned(),
        provider: "phala-dstack".to_owned(),
        artifact_kind: "operator-live".to_owned(),
        operator_run_id: "phase-253-repo-external-run".to_owned(),
        artifact_digest: ArtifactDigest {
            id: "repo-external-operator-live-bundle".to_owned(),
            sha256: digest(89),
        },
        repo_external: true,
        claim_boundary: "operator-live artifact reference only; not accepted evidence".to_owned(),
        nonclaims: gateway_operator_bridge_required_nonclaims(),
    }
}

fn ensure_ignored_demo_root(output_root: &Path) {
    if !output_root.is_absolute() {
        fail(&format!(
            "{ENV_OUTPUT_ROOT} must be absolute, got '{}'",
            output_root.display()
        ));
    }
    let current_dir =
        std::env::current_dir().unwrap_or_else(|err| fail(&format!("current_dir failed: {err}")));
    let ignored_root = current_dir.join(".gateway-demo-runs");
    if !output_root.starts_with(&ignored_root) {
        fail(&format!(
            "{ENV_OUTPUT_ROOT} must be under ignored root '{}'",
            ignored_root.display()
        ));
    }
    fs::create_dir_all(&ignored_root)
        .unwrap_or_else(|err| fail(&format!("failed to create ignored demo root: {err}")));
}

fn nonclaims(labels: &BTreeSet<NonClaimLabel>) -> Vec<String> {
    let mut seen = HashSet::new();
    let mut out = Vec::new();
    for label in labels {
        if seen.insert(label.0.clone()) {
            out.push(label.0.clone());
        }
    }
    out
}

fn main() {
    let ack = require_env(ENV_ACK);
    if ack != FIXED_ACK {
        fail(&format!(
            "{ENV_ACK} did not match the required acknowledgement literal"
        ));
    }

    let output_root = PathBuf::from(require_env(ENV_OUTPUT_ROOT));
    ensure_ignored_demo_root(&output_root);
    fs::create_dir_all(&output_root)
        .unwrap_or_else(|err| fail(&format!("failed to create ignored output root: {err}")));
    let bundle_id =
        optional_env(ENV_BUNDLE_ID).unwrap_or_else(|| "phase-253-gateway-preview".to_owned());
    let created_at_unix = parse_created_at(optional_env(ENV_CREATED_AT_UNIX));
    let overwrite = parse_bool_env(ENV_OVERWRITE, optional_env(ENV_OVERWRITE), true);
    let current_dir =
        std::env::current_dir().unwrap_or_else(|err| fail(&format!("current_dir failed: {err}")));

    let report_output_root = output_root.join("gateway-report-output");
    let bridge_output_root = output_root.join("gateway-bridge-output");
    let preview_output_root = output_root.join("gateway-acceptance-preview-output");
    let protected_roots = vec![
        current_dir.join(".git"),
        current_dir.join("crates"),
        current_dir.join("docs"),
        current_dir.join("target"),
    ];

    let lane = model_lane();
    let proposal = proposal(&lane);
    let policy = gateway_policy();
    let report_request = GatewayReportMaterializationRequest {
        bundle_id: format!("{bundle_id}-report"),
        created_at_unix,
        overwrite,
        protected_roots: protected_roots.clone(),
    };
    let report_run = materialize_gateway_corpus_output_run(
        &report_output_root,
        &[GatewayCorpusCase {
            proposal: proposal.clone(),
            expected_verdict: AdmissionVerdict::Accepted,
        }],
        &policy,
        &report_request,
    )
    .unwrap_or_else(|err| fail(&format!("gateway report materialization failed: {err:?}")));

    let bridge_request = GatewayOperatorBridgeMaterializationRequest {
        bundle_id: format!("{bundle_id}-bridge"),
        created_at_unix,
        overwrite,
        protected_roots: protected_roots.clone(),
    };
    let bridge_bundle = build_gateway_operator_bridge_bundle(
        &report_run.output_manifest,
        attestation_binding(&proposal),
        operator_reference(),
        &bridge_request,
    )
    .unwrap_or_else(|err| fail(&format!("bridge bundle build failed: {err:?}")));
    let bridge_manifest = materialize_gateway_operator_bridge_bundle(
        &bridge_output_root,
        &bridge_bundle,
        &bridge_request,
    )
    .unwrap_or_else(|err| fail(&format!("bridge bundle materialization failed: {err:?}")));

    let preflight_request = GatewayOperatorBridgePromotionPreflightRequest {
        schema_version: gateway_operator_bridge_promotion_preflight_request_schema_version()
            .to_owned(),
        preflight_id: format!("{bundle_id}-preflight"),
        reviewer_id: "local-reviewer".to_owned(),
        review_decision: GatewayOperatorBridgePromotionReviewDecision::ApprovedMetadataOnly,
        bridge_bundle,
        bridge_manifest,
        requested_claim_boundary: gateway_operator_bridge_promotion_preflight_claim_boundary(),
        retains_raw_provider_artifacts: false,
        retains_credentials_or_secrets: false,
        accepted_evidence_mutation_requested: false,
        level2_evidence_requested: false,
        score_axis_population_requested: false,
        production_readiness_claimed: false,
        semantic_correctness_claimed: false,
        live_provider_evidence_claimed: false,
        claim_text: Vec::new(),
        nonclaims: gateway_operator_bridge_promotion_preflight_required_nonclaims(),
    };
    let preflight_report =
        build_gateway_operator_bridge_promotion_preflight_report(&preflight_request);
    let preview_request = GatewayOperatorBridgeAcceptancePreviewRequest {
        schema_version: gateway_operator_bridge_acceptance_preview_request_schema_version()
            .to_owned(),
        preview_id: format!("{bundle_id}-acceptance-preview"),
        reviewer_id: "local-reviewer".to_owned(),
        decision: GatewayOperatorBridgeAcceptancePreviewDecision::ApproveCandidateOnly,
        expected_preflight_report_digest: preflight_report.digest(),
        source_preflight_report: preflight_report,
        requested_claim_boundary: gateway_operator_bridge_acceptance_preview_claim_boundary(),
        candidate_only: true,
        accepted_evidence_mutation_requested: false,
        level2_evidence_requested: false,
        score_axis_population_requested: false,
        production_readiness_claimed: false,
        semantic_correctness_claimed: false,
        live_provider_evidence_claimed: false,
        raw_provider_artifact_retention_requested: false,
        credential_retention_requested: false,
        authority_grant_requested: false,
        claim_text: Vec::new(),
        nonclaims: gateway_operator_bridge_acceptance_preview_required_nonclaims(),
    };
    let preview_report = build_gateway_operator_bridge_acceptance_preview_report(&preview_request);
    let preview_materialization_request =
        GatewayOperatorBridgeAcceptancePreviewMaterializationRequest {
            bundle_id,
            created_at_unix,
            overwrite,
            protected_roots,
        };
    let preview_manifest = materialize_gateway_operator_bridge_acceptance_preview_bundle(
        &preview_output_root,
        &preview_request,
        &preview_materialization_request,
    )
    .unwrap_or_else(|err| {
        fail(&format!(
            "acceptance preview bundle materialization failed: {err:?}"
        ))
    });
    let readback = read_gateway_operator_bridge_acceptance_preview_bundle(&preview_output_root)
        .unwrap_or_else(|err| fail(&format!("acceptance preview readback failed: {err:?}")));
    if readback != preview_manifest {
        fail("acceptance preview bundle readback drifted");
    }

    let summary = GatewayAcceptancePreviewDemoSummary {
        schema_version: "hsai-gateway-acceptance-preview-demo-summary-v1".to_owned(),
        bundle_id: preview_manifest.bundle_id.clone(),
        report_output_root: report_output_root.display().to_string(),
        bridge_output_root: bridge_output_root.display().to_string(),
        preview_output_root: preview_output_root.display().to_string(),
        source_preflight_report_digest: hash_hex(preview_manifest.source_preflight_report_digest),
        acceptance_preview_report_digest: hash_hex(
            preview_manifest.acceptance_preview_report_digest,
        ),
        preview_output_manifest_digest: hash_hex(preview_manifest.digest()),
        bridge_bundle_digest: hash_hex(preview_manifest.bridge_bundle_digest),
        bridge_manifest_digest: hash_hex(preview_manifest.bridge_manifest_digest),
        gateway_report_digest: hash_hex(preview_manifest.gateway_report_digest),
        attestation_binding_digest: hash_hex(preview_manifest.attestation_binding_digest),
        operator_artifact_reference_digest: hash_hex(
            preview_manifest.operator_artifact_reference_digest,
        ),
        declared_files: preview_manifest.declared_files.clone(),
        claim_boundary: preview_manifest.claim_boundary.clone(),
        candidate_only: preview_manifest.candidate_only,
        mutates_accepted_evidence_ledger: preview_manifest.mutates_accepted_evidence_ledger,
        creates_level2_evidence: preview_manifest.creates_level2_evidence,
        populates_score_axes: preview_manifest.populates_score_axes,
        grants_authority: preview_manifest.grants_authority,
        retains_raw_provider_artifacts: preview_manifest.retains_raw_provider_artifacts,
        retains_credentials_or_secrets: preview_manifest.retains_credentials_or_secrets,
        nonclaims: nonclaims(&preview_report.nonclaims),
    };
    match serde_json::to_string_pretty(&summary) {
        Ok(json) => println!("{json}"),
        Err(err) => fail(&format!("summary serialization failed: {err}")),
    }
}
