// Operator-facing local gateway/operator bridge bundle runner.
//
// This example materializes local metadata only under the ignored
// `.gateway-demo-runs/` root. It creates one gateway report bundle and one
// gateway-bridge bundle that references a repo-external operator-live artifact
// by digest. It does not read raw provider artifacts, call a provider, execute
// a model, mutate an accepted Evidence Ledger, or grant action authority.
// Nonclaims: not production readiness; not semantic correctness; not live provider evidence; not accepted Evidence Ledger mutation; not benchmark evidence; not authority to execute an action.

use hsai_agent_admission::{
    build_gateway_attestation_challenge_binding, build_gateway_operator_bridge_bundle,
    gateway_local_default_policy, gateway_operator_bridge_required_nonclaims,
    materialize_gateway_corpus_output_run, materialize_gateway_operator_bridge_bundle,
    read_gateway_operator_bridge_bundle, AdmissionPolicyId, AdmissionVerdict, ArtifactDigest,
    GatewayActionId, GatewayActionKind, GatewayActionPolicy, GatewayActionProposal,
    GatewayAttestationChallengeBinding, GatewayCorpusCase, GatewayModelLaneKind,
    GatewayModelLaneProvenance, GatewayOperatorArtifactReference,
    GatewayOperatorBridgeMaterializationRequest, GatewayReportMaterializationRequest,
    NonClaimLabel,
};
use hsai_claim_envelope::{Hash, SubjectId};
use serde::Serialize;
use std::collections::{BTreeSet, HashSet};
use std::fs;
use std::path::{Path, PathBuf};

const ENV_ACK: &str = "HSAI_GATEWAY_BRIDGE_ACK";
const ENV_OUTPUT_ROOT: &str = "HSAI_GATEWAY_BRIDGE_OUTPUT_ROOT";
const ENV_BUNDLE_ID: &str = "HSAI_GATEWAY_BRIDGE_BUNDLE_ID";
const ENV_CREATED_AT_UNIX: &str = "HSAI_GATEWAY_BRIDGE_CREATED_AT_UNIX";
const ENV_OVERWRITE: &str = "HSAI_GATEWAY_BRIDGE_OVERWRITE";

const FIXED_ACK: &str =
    "I acknowledge this bridge demo writes local metadata only under .gateway-demo-runs.";

#[derive(Debug, Serialize)]
struct GatewayBridgeDemoSummary {
    schema_version: String,
    bundle_id: String,
    report_output_root: String,
    bridge_output_root: String,
    gateway_report_digest: String,
    gateway_report_manifest_digest: String,
    attestation_binding_digest: String,
    operator_artifact_reference_digest: String,
    declared_files: Vec<String>,
    claim_boundary: String,
    authority_granted: bool,
    accepted_evidence_mutation: bool,
    nonclaims: Vec<String>,
}

fn fail(message: &str) -> ! {
    panic!("gateway_operator_bridge_bundle: {message}");
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
        model_family: "qwen-small-local-bridge-demo".to_owned(),
        artifact_id: "qwen-small-local-bridge-demo-q4".to_owned(),
        runtime: "local-bridge-demo-fixture".to_owned(),
        prompt_template_digest: digest(31),
        input_corpus_digest: digest(32),
        output_bundle_digest: digest(33),
        non_secret: true,
    }
}

fn proposal(lane: &GatewayModelLaneProvenance) -> GatewayActionProposal {
    GatewayActionProposal {
        id: GatewayActionId("phase-250-bridge-demo-action".to_owned()),
        subject: SubjectId("phase-250-bridge-demo-agent".to_owned()),
        action_kind: GatewayActionKind::Payment,
        target: "treasury-safe".to_owned(),
        value_units: 50,
        source_artifact_digests: BTreeSet::from([ArtifactDigest {
            id: "phase-250-bridge-demo-source".to_owned(),
            sha256: digest(30),
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
        "phase-250-gateway-bridge-policy",
        BTreeSet::from([GatewayActionKind::Payment]),
        BTreeSet::from(["treasury-safe".to_owned()]),
        100,
    )
}

fn attestation_binding(proposal: &GatewayActionProposal) -> GatewayAttestationChallengeBinding {
    build_gateway_attestation_challenge_binding(
        proposal,
        AdmissionPolicyId("phase-250-gateway-bridge-policy".to_owned()),
        "phase-250-attested-runtime-anchor",
        "a1".repeat(91),
        42,
        0,
        600,
    )
    .unwrap_or_else(|err| fail(&format!("attestation binding failed: {err:?}")))
}

fn operator_reference() -> GatewayOperatorArtifactReference {
    GatewayOperatorArtifactReference {
        reference_id: "phase-250-repo-external-operator-live-reference".to_owned(),
        provider: "phala-dstack".to_owned(),
        artifact_kind: "operator-live".to_owned(),
        operator_run_id: "phase-250-repo-external-run".to_owned(),
        artifact_digest: ArtifactDigest {
            id: "repo-external-operator-live-bundle".to_owned(),
            sha256: digest(88),
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
        optional_env(ENV_BUNDLE_ID).unwrap_or_else(|| "phase-250-gateway-bridge".to_owned());
    let created_at_unix = parse_created_at(optional_env(ENV_CREATED_AT_UNIX));
    let overwrite = parse_bool_env(ENV_OVERWRITE, optional_env(ENV_OVERWRITE), true);
    let current_dir =
        std::env::current_dir().unwrap_or_else(|err| fail(&format!("current_dir failed: {err}")));

    let report_output_root = output_root.join("gateway-report-output");
    let bridge_output_root = output_root.join("gateway-bridge-output");
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
        bundle_id,
        created_at_unix,
        overwrite,
        protected_roots,
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
    let readback = read_gateway_operator_bridge_bundle(&bridge_output_root)
        .unwrap_or_else(|err| fail(&format!("bridge bundle readback failed: {err:?}")));
    if readback != bridge_manifest {
        fail("bridge bundle readback drifted");
    }

    let summary = GatewayBridgeDemoSummary {
        schema_version: "hsai-gateway-bridge-demo-summary-v1".to_owned(),
        bundle_id: bridge_manifest.bundle_id,
        report_output_root: report_output_root.display().to_string(),
        bridge_output_root: bridge_output_root.display().to_string(),
        gateway_report_digest: hash_hex(bridge_manifest.gateway_report_digest),
        gateway_report_manifest_digest: hash_hex(bridge_manifest.gateway_report_manifest_digest),
        attestation_binding_digest: hash_hex(bridge_manifest.attestation_binding_digest),
        operator_artifact_reference_digest: hash_hex(
            bridge_manifest.operator_artifact_reference_digest,
        ),
        declared_files: bridge_manifest.declared_files,
        claim_boundary: bridge_manifest.claim_boundary,
        authority_granted: bridge_manifest.authority_granted,
        accepted_evidence_mutation: bridge_manifest.accepted_evidence_mutation,
        nonclaims: nonclaims(&bridge_manifest.nonclaims),
    };
    match serde_json::to_string_pretty(&summary) {
        Ok(json) => println!("{json}"),
        Err(err) => fail(&format!("summary serialization failed: {err}")),
    }
}
