//! Local output plumbing for external replay submission preflight reports.
//!
//! This module materializes Phase W preflight reports as deterministic local
//! review metadata only. It writes declared digest-bound files and never runs
//! external replay, submits to an endpoint, reads credentials, mutates accepted
//! ledgers, or populates score axes.

use std::collections::BTreeSet;
use std::fs;
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::{
    build_external_replay_submission_preflight_report, compute_artifact_digest_bytes,
    render_external_replay_submission_preflight_markdown,
    required_external_replay_submission_preflight_non_claims,
    serialize_external_replay_submission_preflight_report_json,
    validate_external_replay_submission_preflight_request, ArtifactDigest, ArtifactKind,
    ArtifactRole, ClaimBoundary, ExternalReplaySubmissionPreflightReport,
    ExternalReplaySubmissionPreflightRequest,
};

/// Relative input manifest JSON path under the caller-selected output root.
pub const EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH: &str =
    "external-replay-submission/input-manifest.json";
/// Relative preflight report JSON path under the caller-selected output root.
pub const EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_PATH: &str =
    "external-replay-submission/preflight-report.json";
/// Relative preflight report Markdown path under the caller-selected output root.
pub const EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_PATH: &str =
    "external-replay-submission/preflight-report.md";
/// Relative redaction report JSON path under the caller-selected output root.
pub const EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_PATH: &str =
    "external-replay-submission/redaction-report.json";
/// Relative submission package digest summary JSON path.
pub const EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_PATH: &str =
    "external-replay-submission/submission-package-digests.json";
/// Relative non-claims Markdown path.
pub const EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_PATH: &str =
    "external-replay-submission/non-claims.md";
/// Relative input manifest digest sidecar path.
pub const EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH: &str =
    "external-replay-submission/digests/input-manifest.sha256";
/// Relative report JSON digest sidecar path.
pub const EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH: &str =
    "external-replay-submission/digests/preflight-report-json.sha256";
/// Relative report Markdown digest sidecar path.
pub const EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_DIGEST_PATH: &str =
    "external-replay-submission/digests/preflight-report-md.sha256";
/// Relative redaction report digest sidecar path.
pub const EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_DIGEST_PATH: &str =
    "external-replay-submission/digests/redaction-report.sha256";
/// Relative package digest summary digest sidecar path.
pub const EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_DIGEST_PATH: &str =
    "external-replay-submission/digests/submission-package-digests.sha256";
/// Relative non-claims digest sidecar path.
pub const EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_DIGEST_PATH: &str =
    "external-replay-submission/digests/non-claims.sha256";

/// Local materialization request for a preflight output bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplaySubmissionPreflightOutputRequest {
    /// Caller-owned output root.
    pub output_root: PathBuf,
    /// Valid Phase W external replay submission preflight request.
    pub preflight_request: ExternalReplaySubmissionPreflightRequest,
    /// Valid Phase W external replay submission preflight report.
    pub preflight_report: ExternalReplaySubmissionPreflightReport,
    /// Protected paths that the output root must not overlap.
    #[serde(default)]
    pub protected_paths: Vec<PathBuf>,
    /// Whether an already valid matching output root may be overwritten.
    pub overwrite: bool,
}

/// Deterministic input manifest written next to the preflight report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplaySubmissionPreflightInputManifest {
    /// Manifest id.
    pub manifest_id: String,
    /// Request captured by the bundle.
    pub preflight_request: ExternalReplaySubmissionPreflightRequest,
    /// Report id captured by the bundle.
    pub preflight_report_id: String,
    /// Declared files that make up the local review bundle.
    pub declared_files: Vec<String>,
    /// Output manifests never run external replay.
    pub runs_external_replay: bool,
    /// Output manifests never submit to official endpoints.
    pub submits_to_official_endpoint: bool,
    /// Output manifests never mutate accepted ledgers.
    pub mutates_accepted_evidence_ledger: bool,
    /// Output manifests never write benchmark artifacts.
    pub writes_generated_benchmark_artifacts: bool,
    /// Output manifests never populate score axes.
    pub populates_score_axes: bool,
    /// Output manifest claim boundary.
    pub claim_boundary: ClaimBoundary,
    /// Required non-claim labels.
    pub non_claims: Vec<String>,
}

/// Redaction report for the local preflight output bundle.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplaySubmissionPreflightRedactionReport {
    /// Report id.
    pub report_id: String,
    /// Retained non-secret field classes.
    pub retained_non_secret_fields: Vec<String>,
    /// Raw credentials are excluded.
    pub excludes_raw_credentials: bool,
    /// Raw tokens are excluded.
    pub excludes_raw_tokens: bool,
    /// Raw request bodies are excluded.
    pub excludes_raw_requests: bool,
    /// Raw response bodies are excluded.
    pub excludes_raw_responses: bool,
    /// Raw transport transcripts are excluded.
    pub excludes_raw_transcripts: bool,
    /// Operator-private configuration is excluded.
    pub excludes_operator_private_config: bool,
    /// No raw material is retained.
    pub raw_material_retained: bool,
}

/// Digest summary for the already materialized Phase 121 package inputs.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplaySubmissionPackageDigestSummary {
    /// Expected package metadata digest.
    pub expected_package_metadata_digest: ArtifactDigest,
    /// Expected package validation-report digest.
    pub expected_validation_report_digest: ArtifactDigest,
    /// Source artifact digests declared by the operator.
    pub source_artifact_digests: Vec<ArtifactDigest>,
}

/// Digest summary for the local preflight output files.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExternalReplaySubmissionPreflightOutput {
    /// Input manifest digest.
    pub input_manifest_digest: ArtifactDigest,
    /// Input manifest digest sidecar.
    pub input_manifest_digest_relative_path: String,
    /// Preflight report JSON digest.
    pub preflight_report_json_digest: ArtifactDigest,
    /// Preflight report JSON digest sidecar.
    pub preflight_report_json_digest_relative_path: String,
    /// Preflight report Markdown digest.
    pub preflight_report_markdown_digest: ArtifactDigest,
    /// Preflight report Markdown digest sidecar.
    pub preflight_report_markdown_digest_relative_path: String,
    /// Redaction report digest.
    pub redaction_report_digest: ArtifactDigest,
    /// Redaction report digest sidecar.
    pub redaction_report_digest_relative_path: String,
    /// Submission package digest summary digest.
    pub submission_package_digests_digest: ArtifactDigest,
    /// Submission package digest summary digest sidecar.
    pub submission_package_digests_digest_relative_path: String,
    /// Non-claims Markdown digest.
    pub non_claims_digest: ArtifactDigest,
    /// Non-claims digest sidecar.
    pub non_claims_digest_relative_path: String,
    /// Input manifest.
    pub input_manifest: ExternalReplaySubmissionPreflightInputManifest,
    /// Redaction report.
    pub redaction_report: ExternalReplaySubmissionPreflightRedactionReport,
    /// Submission package digest summary.
    pub package_digest_summary: ExternalReplaySubmissionPackageDigestSummary,
    /// Captured preflight report.
    pub preflight_report: ExternalReplaySubmissionPreflightReport,
}

/// Write local preflight output files under a caller-owned root.
pub fn write_external_replay_submission_preflight_outputs(
    request: &ExternalReplaySubmissionPreflightOutputRequest,
) -> Result<ExternalReplaySubmissionPreflightOutput> {
    validate_output_root(&request.output_root, &request.protected_paths)?;
    validate_preflight_inputs(request)?;

    if request.output_root.exists() {
        reject_symlink(&request.output_root)?;
        if request.output_root.is_file() {
            return Err(preflight_output_error(
                request.output_root.display().to_string(),
                "output root is an existing file",
            ));
        }
        if directory_has_entries(&request.output_root)? {
            if !request.overwrite {
                return Err(preflight_output_error(
                    request.output_root.display().to_string(),
                    "output root is not empty; explicit overwrite is required",
                ));
            }
            let existing = read_external_replay_submission_preflight_outputs(
                &request.output_root,
                &request.protected_paths,
            )?;
            if existing.input_manifest.preflight_request != request.preflight_request
                || existing.preflight_report != request.preflight_report
            {
                return Err(preflight_output_error(
                    request.output_root.display().to_string(),
                    "existing output root does not match supplied preflight; refusing repair overwrite",
                ));
            }
        }
    }

    fs::create_dir_all(&request.output_root).map_err(|error| {
        preflight_output_error(request.output_root.display().to_string(), error.to_string())
    })?;

    let input_manifest = build_input_manifest(request);
    let redaction_report = build_redaction_report(&request.preflight_report);
    let package_digest_summary = build_package_digest_summary(&request.preflight_request);

    let input_manifest_json = serialize_input_manifest_json(&input_manifest)?;
    let preflight_report_json =
        serialize_external_replay_submission_preflight_report_json(&request.preflight_report)?;
    let preflight_report_markdown =
        render_external_replay_submission_preflight_markdown(&request.preflight_report)?;
    let redaction_report_json = serialize_redaction_report_json(&redaction_report)?;
    let package_digest_summary_json =
        serialize_package_digest_summary_json(&package_digest_summary)?;
    let non_claims_markdown = render_non_claims_markdown(&request.preflight_report.non_claims)?;

    let input_manifest_digest = digest_preflight_output_bytes(input_manifest_json.as_bytes());
    let preflight_report_json_digest =
        digest_preflight_output_bytes(preflight_report_json.as_bytes());
    let preflight_report_markdown_digest =
        digest_preflight_output_bytes(preflight_report_markdown.as_bytes());
    let redaction_report_digest = digest_preflight_output_bytes(redaction_report_json.as_bytes());
    let submission_package_digests_digest =
        digest_preflight_output_bytes(package_digest_summary_json.as_bytes());
    let non_claims_digest = digest_preflight_output_bytes(non_claims_markdown.as_bytes());

    write_relative_bytes(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
        input_manifest_json.as_bytes(),
    )?;
    write_relative_bytes(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_PATH,
        preflight_report_json.as_bytes(),
    )?;
    write_relative_bytes(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_PATH,
        preflight_report_markdown.as_bytes(),
    )?;
    write_relative_bytes(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_PATH,
        redaction_report_json.as_bytes(),
    )?;
    write_relative_bytes(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_PATH,
        package_digest_summary_json.as_bytes(),
    )?;
    write_relative_bytes(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_PATH,
        non_claims_markdown.as_bytes(),
    )?;
    write_digest_sidecar(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH,
        &input_manifest_digest,
    )?;
    write_digest_sidecar(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH,
        &preflight_report_json_digest,
    )?;
    write_digest_sidecar(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_DIGEST_PATH,
        &preflight_report_markdown_digest,
    )?;
    write_digest_sidecar(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_DIGEST_PATH,
        &redaction_report_digest,
    )?;
    write_digest_sidecar(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_DIGEST_PATH,
        &submission_package_digests_digest,
    )?;
    write_digest_sidecar(
        &request.output_root,
        EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_DIGEST_PATH,
        &non_claims_digest,
    )?;

    Ok(ExternalReplaySubmissionPreflightOutput {
        input_manifest_digest,
        input_manifest_digest_relative_path: EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH
            .to_string(),
        preflight_report_json_digest,
        preflight_report_json_digest_relative_path:
            EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH.to_string(),
        preflight_report_markdown_digest,
        preflight_report_markdown_digest_relative_path:
            EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_DIGEST_PATH.to_string(),
        redaction_report_digest,
        redaction_report_digest_relative_path:
            EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_DIGEST_PATH.to_string(),
        submission_package_digests_digest,
        submission_package_digests_digest_relative_path:
            EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_DIGEST_PATH.to_string(),
        non_claims_digest,
        non_claims_digest_relative_path: EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_DIGEST_PATH
            .to_string(),
        input_manifest,
        redaction_report,
        package_digest_summary,
        preflight_report: request.preflight_report.clone(),
    })
}

/// Read and validate local preflight output files.
pub fn read_external_replay_submission_preflight_outputs(
    output_root: &Path,
    protected_paths: &[PathBuf],
) -> Result<ExternalReplaySubmissionPreflightOutput> {
    validate_output_root(output_root, protected_paths)?;
    reject_symlink(output_root)?;
    if !output_root.is_dir() {
        return Err(preflight_output_error(
            output_root.display().to_string(),
            "output root must be a directory",
        ));
    }
    reject_unexpected_existing_paths(output_root)?;

    let input_manifest_bytes =
        read_relative_bytes(output_root, EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH)?;
    let preflight_report_json_bytes =
        read_relative_bytes(output_root, EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_PATH)?;
    let preflight_report_markdown_bytes =
        read_relative_bytes(output_root, EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_PATH)?;
    let redaction_report_bytes =
        read_relative_bytes(output_root, EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_PATH)?;
    let package_digests_bytes =
        read_relative_bytes(output_root, EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_PATH)?;
    let non_claims_bytes =
        read_relative_bytes(output_root, EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_PATH)?;

    let input_manifest_digest = digest_preflight_output_bytes(&input_manifest_bytes);
    let preflight_report_json_digest = digest_preflight_output_bytes(&preflight_report_json_bytes);
    let preflight_report_markdown_digest =
        digest_preflight_output_bytes(&preflight_report_markdown_bytes);
    let redaction_report_digest = digest_preflight_output_bytes(&redaction_report_bytes);
    let submission_package_digests_digest = digest_preflight_output_bytes(&package_digests_bytes);
    let non_claims_digest = digest_preflight_output_bytes(&non_claims_bytes);

    verify_digest_sidecar(
        output_root,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH,
        &input_manifest_digest,
        "input manifest bytes do not match digest sidecar",
    )?;
    verify_digest_sidecar(
        output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH,
        &preflight_report_json_digest,
        "preflight report JSON bytes do not match digest sidecar",
    )?;
    verify_digest_sidecar(
        output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_DIGEST_PATH,
        &preflight_report_markdown_digest,
        "preflight report Markdown bytes do not match digest sidecar",
    )?;
    verify_digest_sidecar(
        output_root,
        EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_DIGEST_PATH,
        &redaction_report_digest,
        "redaction report bytes do not match digest sidecar",
    )?;
    verify_digest_sidecar(
        output_root,
        EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_DIGEST_PATH,
        &submission_package_digests_digest,
        "submission package digest summary bytes do not match digest sidecar",
    )?;
    verify_digest_sidecar(
        output_root,
        EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_DIGEST_PATH,
        &non_claims_digest,
        "non-claims bytes do not match digest sidecar",
    )?;

    let input_manifest =
        deserialize_input_manifest_json(&utf8(input_manifest_bytes, "input manifest")?)?;
    let preflight_report = super::deserialize_external_replay_submission_preflight_report_json(
        &utf8(preflight_report_json_bytes, "preflight report JSON")?,
    )?;
    let preflight_report_markdown =
        utf8(preflight_report_markdown_bytes, "preflight report Markdown")?;
    let redaction_report =
        deserialize_redaction_report_json(&utf8(redaction_report_bytes, "redaction report")?)?;
    let package_digest_summary = deserialize_package_digest_summary_json(&utf8(
        package_digests_bytes,
        "submission package digest summary",
    )?)?;
    let non_claims_markdown = utf8(non_claims_bytes, "non-claims Markdown")?;

    validate_readback_consistency(
        &input_manifest,
        &preflight_report,
        &preflight_report_markdown,
        &redaction_report,
        &package_digest_summary,
        &non_claims_markdown,
    )?;

    Ok(ExternalReplaySubmissionPreflightOutput {
        input_manifest_digest,
        input_manifest_digest_relative_path: EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH
            .to_string(),
        preflight_report_json_digest,
        preflight_report_json_digest_relative_path:
            EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH.to_string(),
        preflight_report_markdown_digest,
        preflight_report_markdown_digest_relative_path:
            EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_DIGEST_PATH.to_string(),
        redaction_report_digest,
        redaction_report_digest_relative_path:
            EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_DIGEST_PATH.to_string(),
        submission_package_digests_digest,
        submission_package_digests_digest_relative_path:
            EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_DIGEST_PATH.to_string(),
        non_claims_digest,
        non_claims_digest_relative_path: EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_DIGEST_PATH
            .to_string(),
        input_manifest,
        redaction_report,
        package_digest_summary,
        preflight_report,
    })
}

fn validate_preflight_inputs(
    request: &ExternalReplaySubmissionPreflightOutputRequest,
) -> Result<()> {
    let validation =
        validate_external_replay_submission_preflight_request(&request.preflight_request);
    if !validation.valid {
        return Err(preflight_output_error(
            "preflight_request",
            format!("preflight request is invalid: {:?}", validation.issues),
        ));
    }
    let expected_report =
        build_external_replay_submission_preflight_report(&request.preflight_request);
    if expected_report != request.preflight_report {
        return Err(preflight_output_error(
            "preflight_report",
            "preflight report does not match supplied request",
        ));
    }
    validate_report_side_effects(&request.preflight_report)?;
    if !redaction_policy_declares_raw_exclusion(&request.preflight_request.redaction_policy) {
        return Err(preflight_output_error(
            "preflight_request.redaction_policy",
            "redaction policy must exclude raw credentials, tokens, requests, responses, transcripts, and operator-private configuration",
        ));
    }
    Ok(())
}

fn validate_report_side_effects(report: &ExternalReplaySubmissionPreflightReport) -> Result<()> {
    if !report.validation.valid {
        return Err(preflight_output_error(
            "preflight_report.validation",
            "preflight report validation must be valid before output materialization",
        ));
    }
    if report.runs_external_replay
        || report.submits_to_official_endpoint
        || report.mutates_accepted_evidence_ledger
        || report.writes_generated_artifacts
        || report.populates_score_axes
        || report.claim_boundary != ClaimBoundary::Level0DesignNote
    {
        return Err(preflight_output_error(
            "preflight_report",
            "preflight report claims a forbidden side effect or claim boundary",
        ));
    }
    for required in required_external_replay_submission_preflight_non_claims() {
        if !report
            .non_claims
            .iter()
            .any(|non_claim| non_claim == required)
        {
            return Err(preflight_output_error(
                "preflight_report.non_claims",
                format!("missing required non-claim label: {required}"),
            ));
        }
    }
    Ok(())
}

fn validate_readback_consistency(
    input_manifest: &ExternalReplaySubmissionPreflightInputManifest,
    preflight_report: &ExternalReplaySubmissionPreflightReport,
    preflight_report_markdown: &str,
    redaction_report: &ExternalReplaySubmissionPreflightRedactionReport,
    package_digest_summary: &ExternalReplaySubmissionPackageDigestSummary,
    non_claims_markdown: &str,
) -> Result<()> {
    validate_manifest_side_effects(input_manifest)?;
    validate_report_side_effects(preflight_report)?;
    validate_redaction_report(redaction_report)?;
    if input_manifest.preflight_report_id != preflight_report.report_id {
        return Err(preflight_output_error(
            EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
            "input manifest report id does not match preflight report",
        ));
    }
    if input_manifest.preflight_request.id != preflight_report.source_summary.request_id {
        return Err(preflight_output_error(
            EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
            "input manifest request id does not match preflight report",
        ));
    }
    if input_manifest.declared_files != declared_file_paths() {
        return Err(preflight_output_error(
            EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
            "input manifest declared files do not match the Phase 125 contract",
        ));
    }
    let expected_markdown = render_external_replay_submission_preflight_markdown(preflight_report)?;
    if preflight_report_markdown != expected_markdown {
        return Err(preflight_output_error(
            EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_PATH,
            "preflight report Markdown does not match report JSON",
        ));
    }
    if package_digest_summary.expected_package_metadata_digest
        != input_manifest
            .preflight_request
            .expected_package_metadata_digest
        || package_digest_summary.expected_validation_report_digest
            != input_manifest
                .preflight_request
                .expected_validation_report_digest
        || package_digest_summary.source_artifact_digests
            != input_manifest.preflight_request.source_artifact_digests
    {
        return Err(preflight_output_error(
            EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_PATH,
            "package digest summary does not match input manifest request",
        ));
    }
    if non_claims_markdown != render_non_claims_markdown(&preflight_report.non_claims)? {
        return Err(preflight_output_error(
            EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_PATH,
            "non-claims Markdown does not match preflight report",
        ));
    }
    if scan_for_raw_retention_terms(non_claims_markdown)
        || scan_for_raw_retention_terms(preflight_report_markdown)
    {
        return Err(preflight_output_error(
            "external-replay-submission",
            "rendered Markdown contains raw retained material markers",
        ));
    }
    Ok(())
}

fn validate_manifest_side_effects(
    manifest: &ExternalReplaySubmissionPreflightInputManifest,
) -> Result<()> {
    if manifest.runs_external_replay
        || manifest.submits_to_official_endpoint
        || manifest.mutates_accepted_evidence_ledger
        || manifest.writes_generated_benchmark_artifacts
        || manifest.populates_score_axes
        || manifest.claim_boundary != ClaimBoundary::Level0DesignNote
    {
        return Err(preflight_output_error(
            EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
            "input manifest claims a forbidden side effect or claim boundary",
        ));
    }
    Ok(())
}

fn validate_redaction_report(
    report: &ExternalReplaySubmissionPreflightRedactionReport,
) -> Result<()> {
    if !report.excludes_raw_credentials
        || !report.excludes_raw_tokens
        || !report.excludes_raw_requests
        || !report.excludes_raw_responses
        || !report.excludes_raw_transcripts
        || !report.excludes_operator_private_config
        || report.raw_material_retained
    {
        return Err(preflight_output_error(
            EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_PATH,
            "redaction report must exclude all raw live/operator material",
        ));
    }
    Ok(())
}

fn build_input_manifest(
    request: &ExternalReplaySubmissionPreflightOutputRequest,
) -> ExternalReplaySubmissionPreflightInputManifest {
    ExternalReplaySubmissionPreflightInputManifest {
        manifest_id: format!(
            "external_replay_submission_preflight_output_{}",
            request.preflight_request.id
        ),
        preflight_request: request.preflight_request.clone(),
        preflight_report_id: request.preflight_report.report_id.clone(),
        declared_files: declared_file_paths(),
        runs_external_replay: false,
        submits_to_official_endpoint: false,
        mutates_accepted_evidence_ledger: false,
        writes_generated_benchmark_artifacts: false,
        populates_score_axes: false,
        claim_boundary: ClaimBoundary::Level0DesignNote,
        non_claims: request.preflight_report.non_claims.clone(),
    }
}

fn build_redaction_report(
    report: &ExternalReplaySubmissionPreflightReport,
) -> ExternalReplaySubmissionPreflightRedactionReport {
    ExternalReplaySubmissionPreflightRedactionReport {
        report_id: report.report_id.clone(),
        retained_non_secret_fields: vec![
            "preflight request metadata".to_string(),
            "preflight report metadata".to_string(),
            "artifact digests".to_string(),
            "redaction decisions".to_string(),
            "required non-claim labels".to_string(),
        ],
        excludes_raw_credentials: true,
        excludes_raw_tokens: true,
        excludes_raw_requests: true,
        excludes_raw_responses: true,
        excludes_raw_transcripts: true,
        excludes_operator_private_config: true,
        raw_material_retained: false,
    }
}

fn build_package_digest_summary(
    request: &ExternalReplaySubmissionPreflightRequest,
) -> ExternalReplaySubmissionPackageDigestSummary {
    ExternalReplaySubmissionPackageDigestSummary {
        expected_package_metadata_digest: request.expected_package_metadata_digest.clone(),
        expected_validation_report_digest: request.expected_validation_report_digest.clone(),
        source_artifact_digests: request.source_artifact_digests.clone(),
    }
}

fn redaction_policy_declares_raw_exclusion(redaction_policy: &[String]) -> bool {
    let normalized = redaction_policy
        .join(" ")
        .to_ascii_lowercase()
        .replace('-', " ");
    [
        "credential",
        "token",
        "request",
        "response",
        "transcript",
        "private",
    ]
    .iter()
    .all(|required| normalized.contains(required))
        && (normalized.contains("exclude") || normalized.contains("not retain"))
}

fn render_non_claims_markdown(non_claims: &[String]) -> Result<String> {
    for required in required_external_replay_submission_preflight_non_claims() {
        if !non_claims.iter().any(|non_claim| non_claim == required) {
            return Err(preflight_output_error(
                EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_PATH,
                format!("missing required non-claim label: {required}"),
            ));
        }
    }
    let mut markdown = String::new();
    markdown.push_str("# External Replay Submission Preflight Non-Claims\n\n");
    for non_claim in non_claims {
        markdown.push_str("- ");
        markdown.push_str(non_claim);
        markdown.push('\n');
    }
    Ok(markdown)
}

fn serialize_input_manifest_json(
    manifest: &ExternalReplaySubmissionPreflightInputManifest,
) -> Result<String> {
    serde_json::to_string_pretty(manifest).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_external_replay_submission_preflight_input_manifest_json",
            error.to_string(),
        )
    })
}

fn deserialize_input_manifest_json(
    json: &str,
) -> Result<ExternalReplaySubmissionPreflightInputManifest> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_external_replay_submission_preflight_input_manifest_json",
            error.to_string(),
        )
    })
}

fn serialize_redaction_report_json(
    report: &ExternalReplaySubmissionPreflightRedactionReport,
) -> Result<String> {
    serde_json::to_string_pretty(report).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_external_replay_submission_preflight_redaction_report_json",
            error.to_string(),
        )
    })
}

fn deserialize_redaction_report_json(
    json: &str,
) -> Result<ExternalReplaySubmissionPreflightRedactionReport> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_external_replay_submission_preflight_redaction_report_json",
            error.to_string(),
        )
    })
}

fn serialize_package_digest_summary_json(
    summary: &ExternalReplaySubmissionPackageDigestSummary,
) -> Result<String> {
    serde_json::to_string_pretty(summary).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_external_replay_submission_package_digest_summary_json",
            error.to_string(),
        )
    })
}

fn deserialize_package_digest_summary_json(
    json: &str,
) -> Result<ExternalReplaySubmissionPackageDigestSummary> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_external_replay_submission_package_digest_summary_json",
            error.to_string(),
        )
    })
}

fn digest_preflight_output_bytes(bytes: &[u8]) -> ArtifactDigest {
    compute_artifact_digest_bytes(bytes, Some(ArtifactKind::Other), Some(ArtifactRole::Report))
}

fn write_digest_sidecar(
    output_root: &Path,
    relative_path: &str,
    digest: &ArtifactDigest,
) -> Result<()> {
    write_relative_bytes(
        output_root,
        relative_path,
        format!("{}\n", digest.hex_digest).as_bytes(),
    )
}

fn verify_digest_sidecar(
    output_root: &Path,
    relative_path: &str,
    expected: &ArtifactDigest,
    message: &str,
) -> Result<()> {
    let sidecar =
        String::from_utf8(read_relative_bytes(output_root, relative_path)?).map_err(|error| {
            preflight_output_error(
                relative_path,
                format!("digest sidecar is not UTF-8: {error}"),
            )
        })?;
    if sidecar.trim() != expected.hex_digest {
        return Err(preflight_output_error(relative_path, message));
    }
    Ok(())
}

fn write_relative_bytes(output_root: &Path, relative_path: &str, bytes: &[u8]) -> Result<()> {
    validate_relative_output_path(relative_path)?;
    let path = output_root.join(relative_path);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|error| {
            preflight_output_error(parent.display().to_string(), error.to_string())
        })?;
    }
    fs::write(&path, bytes)
        .map_err(|error| preflight_output_error(path.display().to_string(), error.to_string()))
}

fn read_relative_bytes(output_root: &Path, relative_path: &str) -> Result<Vec<u8>> {
    validate_relative_output_path(relative_path)?;
    let path = output_root.join(relative_path);
    reject_symlink(&path)?;
    fs::read(&path)
        .map_err(|error| preflight_output_error(path.display().to_string(), error.to_string()))
}

fn validate_relative_output_path(relative_path: &str) -> Result<()> {
    let path = Path::new(relative_path);
    if relative_path.trim().is_empty()
        || path.is_absolute()
        || relative_path.contains("..")
        || relative_path.contains('\\')
        || relative_path.contains("://")
        || relative_path.contains('|')
        || relative_path.contains(';')
        || relative_path.contains('$')
    {
        return Err(preflight_output_error(
            relative_path,
            "relative output path is not portable",
        ));
    }
    Ok(())
}

fn reject_unexpected_existing_paths(output_root: &Path) -> Result<()> {
    let expected = declared_relative_paths();
    for path in collect_relative_paths(output_root, output_root)? {
        let path = path.to_string_lossy().replace('\\', "/");
        if !expected.contains(path.as_str()) {
            return Err(preflight_output_error(
                path,
                "output root contains unexpected file or directory",
            ));
        }
    }
    Ok(())
}

fn collect_relative_paths(output_root: &Path, current: &Path) -> Result<Vec<PathBuf>> {
    let mut paths = Vec::new();
    for entry in fs::read_dir(current)
        .map_err(|error| preflight_output_error(current.display().to_string(), error.to_string()))?
    {
        let entry = entry.map_err(|error| {
            preflight_output_error(current.display().to_string(), error.to_string())
        })?;
        let path = entry.path();
        reject_symlink(&path)?;
        let relative = path.strip_prefix(output_root).map_err(|error| {
            preflight_output_error(path.display().to_string(), error.to_string())
        })?;
        paths.push(relative.to_path_buf());
        if path.is_dir() {
            paths.extend(collect_relative_paths(output_root, &path)?);
        }
    }
    Ok(paths)
}

fn validate_output_root(output_root: &Path, protected_paths: &[PathBuf]) -> Result<()> {
    if output_root.as_os_str().is_empty() {
        return Err(preflight_output_error(
            "output_root",
            "output root must be non-empty",
        ));
    }
    validate_no_parent_components(output_root, "output root")?;
    let normalized_output = normalize_path(output_root)?;
    let resolved_output = resolve_existing_prefix(output_root)?;
    let repo_root = std::env::current_dir().map_err(|error| {
        preflight_output_error(output_root.display().to_string(), error.to_string())
    })?;
    if paths_overlap(&normalized_output, &repo_root) || paths_overlap(&resolved_output, &repo_root)
    {
        return Err(preflight_output_error(
            output_root.display().to_string(),
            "output root overlaps repository root",
        ));
    }
    for protected in protected_paths {
        validate_no_parent_components(protected, "protected path")?;
        let normalized_protected = normalize_path(protected)?;
        let resolved_protected = resolve_existing_prefix(protected)?;
        if paths_overlap(&normalized_output, &normalized_protected)
            || paths_overlap(&resolved_output, &resolved_protected)
        {
            return Err(preflight_output_error(
                output_root.display().to_string(),
                format!(
                    "output root overlaps protected path {}",
                    protected.display()
                ),
            ));
        }
    }
    Ok(())
}

fn validate_no_parent_components(path: &Path, label: &str) -> Result<()> {
    if path
        .components()
        .any(|component| component == Component::ParentDir)
    {
        return Err(preflight_output_error(
            path.display().to_string(),
            format!("{label} must not contain parent-directory components"),
        ));
    }
    Ok(())
}

fn reject_symlink(path: &Path) -> Result<()> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| preflight_output_error(path.display().to_string(), error.to_string()))?;
    if metadata.file_type().is_symlink() {
        return Err(preflight_output_error(
            path.display().to_string(),
            "external replay preflight output path must not be a symlink",
        ));
    }
    Ok(())
}

fn directory_has_entries(path: &Path) -> Result<bool> {
    Ok(fs::read_dir(path)
        .map_err(|error| preflight_output_error(path.display().to_string(), error.to_string()))?
        .next()
        .is_some())
}

fn normalize_path(path: &Path) -> Result<PathBuf> {
    let mut normalized = if path.is_absolute() {
        PathBuf::new()
    } else {
        std::env::current_dir().map_err(|error| {
            preflight_output_error(path.display().to_string(), error.to_string())
        })?
    };
    for component in path.components() {
        match component {
            Component::Prefix(prefix) => normalized.push(prefix.as_os_str()),
            Component::RootDir => normalized.push(component.as_os_str()),
            Component::CurDir => {}
            Component::Normal(segment) => normalized.push(segment),
            Component::ParentDir => {
                return Err(preflight_output_error(
                    path.display().to_string(),
                    "paths must not contain parent-directory components",
                ));
            }
        }
    }
    Ok(normalized)
}

fn resolve_existing_prefix(path: &Path) -> Result<PathBuf> {
    let normalized = normalize_path(path)?;
    let mut missing = Vec::new();
    let mut cursor = normalized.as_path();
    loop {
        match fs::canonicalize(cursor) {
            Ok(mut resolved) => {
                for segment in missing.iter().rev() {
                    resolved.push(segment);
                }
                return Ok(resolved);
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                let Some(segment) = cursor.file_name() else {
                    return Ok(normalized);
                };
                missing.push(segment.to_os_string());
                let Some(parent) = cursor.parent() else {
                    return Ok(normalized);
                };
                cursor = parent;
            }
            Err(error) => {
                return Err(preflight_output_error(
                    cursor.display().to_string(),
                    error.to_string(),
                ));
            }
        }
    }
}

fn paths_overlap(left: &Path, right: &Path) -> bool {
    left.starts_with(right) || right.starts_with(left)
}

fn declared_file_paths() -> Vec<String> {
    vec![
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH.to_string(),
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_PATH.to_string(),
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_PATH.to_string(),
        EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_PATH.to_string(),
        EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_PATH.to_string(),
        EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_PATH.to_string(),
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH.to_string(),
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH.to_string(),
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_DIGEST_PATH.to_string(),
        EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_DIGEST_PATH.to_string(),
        EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_DIGEST_PATH.to_string(),
        EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_DIGEST_PATH.to_string(),
    ]
}

fn declared_relative_paths() -> BTreeSet<&'static str> {
    BTreeSet::from([
        "external-replay-submission",
        "external-replay-submission/digests",
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_INPUT_MANIFEST_DIGEST_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_JSON_DIGEST_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REPORT_MARKDOWN_DIGEST_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_REDACTION_REPORT_DIGEST_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_PACKAGE_DIGESTS_DIGEST_PATH,
        EXTERNAL_REPLAY_PREFLIGHT_NON_CLAIMS_DIGEST_PATH,
    ])
}

fn utf8(bytes: Vec<u8>, label: &str) -> Result<String> {
    String::from_utf8(bytes).map_err(|error| {
        preflight_output_error(label, format!("materialized file is not UTF-8: {error}"))
    })
}

fn scan_for_raw_retention_terms(text: &str) -> bool {
    let normalized = text.to_ascii_lowercase();
    [
        "raw credential retained",
        "raw token retained",
        "raw request retained",
        "raw response retained",
        "raw transcript retained",
        "operator private retained",
    ]
    .iter()
    .any(|marker| normalized.contains(marker))
}

fn preflight_output_error(path: impl Into<String>, message: impl Into<String>) -> ZkBenchError {
    ZkBenchError::artifact(path, message)
}
