//! Local official-submission package output plumbing.
//!
//! This module materializes an inert official-submission package for local
//! review only. It writes declared digest-bound files and never submits to an
//! official endpoint, runs external replay, uses credentials, or populates score
//! axes.

use std::collections::BTreeSet;
use std::fs;
use std::path::{Component, Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};

use super::{
    compute_artifact_digest_bytes, render_official_submission_package_markdown,
    serialize_official_submission_package_metadata_json,
    validate_official_submission_package_metadata, ArtifactDigest, ArtifactKind, ArtifactRole,
    EvidenceLedger, OfficialSubmissionPackageMetadata, OfficialSubmissionPackageValidation,
};

/// Relative package metadata JSON path under the caller-selected output root.
pub const OFFICIAL_SUBMISSION_PACKAGE_METADATA_PATH: &str =
    "official-submission-package/package-metadata.json";
/// Relative rendered package Markdown path under the caller-selected output root.
pub const OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_PATH: &str =
    "official-submission-package/package.md";
/// Relative validation report JSON path under the caller-selected output root.
pub const OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH: &str =
    "official-submission-package/validation-report.json";
/// Relative package metadata digest sidecar path.
pub const OFFICIAL_SUBMISSION_PACKAGE_METADATA_DIGEST_PATH: &str =
    "official-submission-package/digests/package-metadata.sha256";
/// Relative package Markdown digest sidecar path.
pub const OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH: &str =
    "official-submission-package/digests/package-md.sha256";
/// Relative validation report digest sidecar path.
pub const OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_DIGEST_PATH: &str =
    "official-submission-package/digests/validation-report.sha256";

/// Local official-submission package materialization request.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OfficialSubmissionPackageOutputRequest {
    /// Caller-owned output root.
    pub output_root: PathBuf,
    /// Existing accepted Evidence Ledger JSON path.
    pub accepted_ledger_path: PathBuf,
    /// Inert official-submission package metadata.
    pub package: OfficialSubmissionPackageMetadata,
    /// Protected paths that the output root must not overlap.
    #[serde(default)]
    pub protected_paths: Vec<PathBuf>,
    /// Whether an already valid matching output root may be overwritten.
    pub overwrite: bool,
}

/// Validation report materialized next to local package files.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OfficialSubmissionPackageOutputValidationReport {
    /// Package id.
    pub package_id: String,
    /// Existing accepted ledger path used for validation.
    pub accepted_ledger_path: PathBuf,
    /// Accepted ledger entry count.
    pub accepted_ledger_entry_count: usize,
    /// Package metadata validation.
    pub package_validation: OfficialSubmissionPackageValidation,
    /// Accepted evidence ids matched in the ledger.
    pub matched_accepted_evidence_ledger_entry_ids: Vec<String>,
    /// Local materialization never creates an official submission.
    pub creates_official_submission: bool,
    /// Local materialization never submits to an official endpoint.
    pub submits_to_official_endpoint: bool,
    /// Local materialization never populates score axes.
    pub populates_score_axes: bool,
    /// Required non-claim labels carried by the package.
    pub non_claims: Vec<String>,
}

/// Digest summary for local package output files.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct OfficialSubmissionPackageOutput {
    /// Package metadata JSON digest.
    pub package_metadata_digest: ArtifactDigest,
    /// Package metadata JSON digest sidecar.
    pub package_metadata_digest_relative_path: String,
    /// Rendered package Markdown digest.
    pub package_markdown_digest: ArtifactDigest,
    /// Rendered package Markdown digest sidecar.
    pub package_markdown_digest_relative_path: String,
    /// Validation report JSON digest.
    pub validation_report_digest: ArtifactDigest,
    /// Validation report digest sidecar.
    pub validation_report_digest_relative_path: String,
    /// Validation report.
    pub validation_report: OfficialSubmissionPackageOutputValidationReport,
}

/// Write local official-submission package outputs under a caller-owned root.
pub fn write_official_submission_package_outputs(
    request: &OfficialSubmissionPackageOutputRequest,
) -> Result<OfficialSubmissionPackageOutput> {
    validate_output_root(&request.output_root, &request.protected_paths)?;
    validate_accepted_ledger_path(&request.accepted_ledger_path)?;
    let ledger = load_valid_ledger(&request.accepted_ledger_path)?;
    let validation_report = build_validation_report(request, &ledger)?;

    if request.output_root.exists() {
        reject_symlink(&request.output_root)?;
        if request.output_root.is_file() {
            return Err(package_error(
                request.output_root.display().to_string(),
                "output root is an existing file",
            ));
        }
        if directory_has_entries(&request.output_root)? {
            if !request.overwrite {
                return Err(package_error(
                    request.output_root.display().to_string(),
                    "output root is not empty; explicit overwrite is required",
                ));
            }
            let existing = read_official_submission_package_outputs(
                &request.output_root,
                &request.protected_paths,
            )?;
            let existing_package = read_package_metadata(&request.output_root)?;
            if existing_package != request.package
                || existing.validation_report.package_id != request.package.package_id
            {
                return Err(package_error(
                    request.output_root.display().to_string(),
                    "existing output root does not match supplied package; refusing repair overwrite",
                ));
            }
        }
    }

    fs::create_dir_all(&request.output_root).map_err(|error| {
        package_error(request.output_root.display().to_string(), error.to_string())
    })?;

    let package_json = serialize_official_submission_package_metadata_json(&request.package)?;
    let package_markdown = render_official_submission_package_markdown(&request.package)?;
    let validation_json = serialize_validation_report_json(&validation_report)?;

    let package_metadata_digest = digest_package_output_bytes(package_json.as_bytes());
    let package_markdown_digest = digest_package_output_bytes(package_markdown.as_bytes());
    let validation_report_digest = digest_package_output_bytes(validation_json.as_bytes());

    write_relative_bytes(
        &request.output_root,
        OFFICIAL_SUBMISSION_PACKAGE_METADATA_PATH,
        package_json.as_bytes(),
    )?;
    write_relative_bytes(
        &request.output_root,
        OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_PATH,
        package_markdown.as_bytes(),
    )?;
    write_relative_bytes(
        &request.output_root,
        OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH,
        validation_json.as_bytes(),
    )?;
    write_digest_sidecar(
        &request.output_root,
        OFFICIAL_SUBMISSION_PACKAGE_METADATA_DIGEST_PATH,
        &package_metadata_digest,
    )?;
    write_digest_sidecar(
        &request.output_root,
        OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH,
        &package_markdown_digest,
    )?;
    write_digest_sidecar(
        &request.output_root,
        OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_DIGEST_PATH,
        &validation_report_digest,
    )?;

    Ok(OfficialSubmissionPackageOutput {
        package_metadata_digest,
        package_metadata_digest_relative_path: OFFICIAL_SUBMISSION_PACKAGE_METADATA_DIGEST_PATH
            .to_string(),
        package_markdown_digest,
        package_markdown_digest_relative_path: OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH
            .to_string(),
        validation_report_digest,
        validation_report_digest_relative_path: OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_DIGEST_PATH
            .to_string(),
        validation_report,
    })
}

/// Read and validate local official-submission package outputs.
pub fn read_official_submission_package_outputs(
    output_root: &Path,
    protected_paths: &[PathBuf],
) -> Result<OfficialSubmissionPackageOutput> {
    validate_output_root(output_root, protected_paths)?;
    reject_symlink(output_root)?;
    if !output_root.is_dir() {
        return Err(package_error(
            output_root.display().to_string(),
            "output root must be a directory",
        ));
    }
    reject_unexpected_existing_paths(output_root)?;

    let package_json_bytes =
        read_relative_bytes(output_root, OFFICIAL_SUBMISSION_PACKAGE_METADATA_PATH)?;
    let package_markdown_bytes =
        read_relative_bytes(output_root, OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_PATH)?;
    let validation_json_bytes =
        read_relative_bytes(output_root, OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH)?;

    let package_metadata_digest = digest_package_output_bytes(&package_json_bytes);
    let package_markdown_digest = digest_package_output_bytes(&package_markdown_bytes);
    let validation_report_digest = digest_package_output_bytes(&validation_json_bytes);

    verify_digest_sidecar(
        output_root,
        OFFICIAL_SUBMISSION_PACKAGE_METADATA_DIGEST_PATH,
        &package_metadata_digest,
        "package metadata JSON bytes do not match digest sidecar",
    )?;
    verify_digest_sidecar(
        output_root,
        OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH,
        &package_markdown_digest,
        "package Markdown bytes do not match digest sidecar",
    )?;
    verify_digest_sidecar(
        output_root,
        OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_DIGEST_PATH,
        &validation_report_digest,
        "validation report JSON bytes do not match digest sidecar",
    )?;

    let package_json = String::from_utf8(package_json_bytes).map_err(|error| {
        package_error(
            OFFICIAL_SUBMISSION_PACKAGE_METADATA_PATH,
            format!("package metadata JSON is not UTF-8: {error}"),
        )
    })?;
    let package_markdown = String::from_utf8(package_markdown_bytes).map_err(|error| {
        package_error(
            OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_PATH,
            format!("package Markdown is not UTF-8: {error}"),
        )
    })?;
    let validation_json = String::from_utf8(validation_json_bytes).map_err(|error| {
        package_error(
            OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH,
            format!("validation report JSON is not UTF-8: {error}"),
        )
    })?;

    let package = super::deserialize_official_submission_package_metadata_json(&package_json)?;
    let expected_markdown = render_official_submission_package_markdown(&package)?;
    if package_markdown != expected_markdown {
        return Err(package_error(
            OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_PATH,
            "package Markdown does not match package metadata",
        ));
    }
    let validation_report = deserialize_validation_report_json(&validation_json)?;
    if validation_report.package_id != package.package_id {
        return Err(package_error(
            OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH,
            "validation report package id does not match package metadata",
        ));
    }
    if validation_report.creates_official_submission
        || validation_report.submits_to_official_endpoint
        || validation_report.populates_score_axes
    {
        return Err(package_error(
            OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH,
            "validation report claims an external submission or score-axis side effect",
        ));
    }

    Ok(OfficialSubmissionPackageOutput {
        package_metadata_digest,
        package_metadata_digest_relative_path: OFFICIAL_SUBMISSION_PACKAGE_METADATA_DIGEST_PATH
            .to_string(),
        package_markdown_digest,
        package_markdown_digest_relative_path: OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH
            .to_string(),
        validation_report_digest,
        validation_report_digest_relative_path: OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_DIGEST_PATH
            .to_string(),
        validation_report,
    })
}

fn build_validation_report(
    request: &OfficialSubmissionPackageOutputRequest,
    ledger: &EvidenceLedger,
) -> Result<OfficialSubmissionPackageOutputValidationReport> {
    let package_validation = validate_official_submission_package_metadata(&request.package);
    if !package_validation.valid {
        return Err(package_error(
            "official_submission_package.package",
            format!(
                "package metadata is invalid: {:?}",
                package_validation.issues
            ),
        ));
    }
    let matched =
        matched_accepted_ids(&request.package.accepted_evidence_ledger_entry_ids, ledger)?;
    Ok(OfficialSubmissionPackageOutputValidationReport {
        package_id: request.package.package_id.clone(),
        accepted_ledger_path: request.accepted_ledger_path.clone(),
        accepted_ledger_entry_count: ledger.entries.len(),
        package_validation,
        matched_accepted_evidence_ledger_entry_ids: matched,
        creates_official_submission: false,
        submits_to_official_endpoint: false,
        populates_score_axes: false,
        non_claims: request.package.non_claims.clone(),
    })
}

fn matched_accepted_ids(ids: &[String], ledger: &EvidenceLedger) -> Result<Vec<String>> {
    let mut ledger_ids = BTreeSet::new();
    for entry in &ledger.entries {
        ledger_ids.insert(entry.sequence_number.to_string());
        ledger_ids.insert(entry.entry_digest.hex_digest.clone());
    }
    let mut matched = Vec::new();
    for id in ids {
        if !ledger_ids.contains(id) {
            return Err(package_error(
                "package.accepted_evidence_ledger_entry_ids",
                format!("accepted evidence id {id:?} is absent from accepted ledger"),
            ));
        }
        matched.push(id.clone());
    }
    Ok(matched)
}

fn load_valid_ledger(path: &Path) -> Result<EvidenceLedger> {
    let ledger = EvidenceLedger::load_json(path)?;
    let validation = ledger.validate();
    if !validation.valid {
        return Err(package_error(
            path.display().to_string(),
            format!("accepted ledger is invalid: {:?}", validation.errors),
        ));
    }
    Ok(ledger)
}

fn read_package_metadata(output_root: &Path) -> Result<OfficialSubmissionPackageMetadata> {
    let package_json_bytes =
        read_relative_bytes(output_root, OFFICIAL_SUBMISSION_PACKAGE_METADATA_PATH)?;
    let package_json = String::from_utf8(package_json_bytes).map_err(|error| {
        package_error(
            OFFICIAL_SUBMISSION_PACKAGE_METADATA_PATH,
            format!("package metadata JSON is not UTF-8: {error}"),
        )
    })?;
    super::deserialize_official_submission_package_metadata_json(&package_json)
}

fn validate_accepted_ledger_path(path: &Path) -> Result<()> {
    validate_no_parent_components(path, "accepted ledger path")?;
    if !path.exists() {
        return Err(package_error(
            path.display().to_string(),
            "accepted ledger file is missing",
        ));
    }
    reject_symlink(path)?;
    if path.is_dir() {
        return Err(package_error(
            path.display().to_string(),
            "accepted ledger path must be a JSON file, not a directory",
        ));
    }
    Ok(())
}

fn validate_output_root(output_root: &Path, protected_paths: &[PathBuf]) -> Result<()> {
    if output_root.as_os_str().is_empty() {
        return Err(package_error(
            "output_root",
            "output root must be non-empty",
        ));
    }
    validate_no_parent_components(output_root, "output root")?;
    let normalized_output = normalize_path(output_root)?;
    let resolved_output = resolve_existing_prefix(output_root)?;
    for protected in protected_paths {
        validate_no_parent_components(protected, "protected path")?;
        let normalized_protected = normalize_path(protected)?;
        let resolved_protected = resolve_existing_prefix(protected)?;
        if paths_overlap(&normalized_output, &normalized_protected)
            || paths_overlap(&resolved_output, &resolved_protected)
        {
            return Err(package_error(
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
        return Err(package_error(
            path.display().to_string(),
            format!("{label} must not contain parent-directory components"),
        ));
    }
    Ok(())
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
            package_error(
                relative_path,
                format!("digest sidecar is not UTF-8: {error}"),
            )
        })?;
    if sidecar.trim() != expected.hex_digest {
        return Err(package_error(relative_path, message));
    }
    Ok(())
}

fn serialize_validation_report_json(
    report: &OfficialSubmissionPackageOutputValidationReport,
) -> Result<String> {
    serde_json::to_string_pretty(report).map_err(|error| {
        ZkBenchError::serialization(
            "serialize_official_submission_package_output_validation_report_json",
            error.to_string(),
        )
    })
}

fn deserialize_validation_report_json(
    json: &str,
) -> Result<OfficialSubmissionPackageOutputValidationReport> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization(
            "deserialize_official_submission_package_output_validation_report_json",
            error.to_string(),
        )
    })
}

fn digest_package_output_bytes(bytes: &[u8]) -> ArtifactDigest {
    compute_artifact_digest_bytes(bytes, Some(ArtifactKind::Other), Some(ArtifactRole::Report))
}

fn declared_relative_paths() -> BTreeSet<&'static str> {
    BTreeSet::from([
        "official-submission-package",
        "official-submission-package/digests",
        OFFICIAL_SUBMISSION_PACKAGE_METADATA_PATH,
        OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_PATH,
        OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_PATH,
        OFFICIAL_SUBMISSION_PACKAGE_METADATA_DIGEST_PATH,
        OFFICIAL_SUBMISSION_PACKAGE_MARKDOWN_DIGEST_PATH,
        OFFICIAL_SUBMISSION_PACKAGE_VALIDATION_DIGEST_PATH,
    ])
}

fn write_relative_bytes(output_root: &Path, relative_path: &str, bytes: &[u8]) -> Result<()> {
    validate_relative_output_path(relative_path)?;
    let path = output_root.join(relative_path);
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| package_error(parent.display().to_string(), error.to_string()))?;
    }
    fs::write(&path, bytes)
        .map_err(|error| package_error(path.display().to_string(), error.to_string()))
}

fn read_relative_bytes(output_root: &Path, relative_path: &str) -> Result<Vec<u8>> {
    validate_relative_output_path(relative_path)?;
    let path = output_root.join(relative_path);
    reject_symlink(&path)?;
    fs::read(&path).map_err(|error| package_error(path.display().to_string(), error.to_string()))
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
        return Err(package_error(
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
            return Err(package_error(
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
        .map_err(|error| package_error(current.display().to_string(), error.to_string()))?
    {
        let entry = entry
            .map_err(|error| package_error(current.display().to_string(), error.to_string()))?;
        let path = entry.path();
        reject_symlink(&path)?;
        let relative = path
            .strip_prefix(output_root)
            .map_err(|error| package_error(path.display().to_string(), error.to_string()))?;
        paths.push(relative.to_path_buf());
        if path.is_dir() {
            paths.extend(collect_relative_paths(output_root, &path)?);
        }
    }
    Ok(paths)
}

fn directory_has_entries(path: &Path) -> Result<bool> {
    Ok(fs::read_dir(path)
        .map_err(|error| package_error(path.display().to_string(), error.to_string()))?
        .next()
        .is_some())
}

fn reject_symlink(path: &Path) -> Result<()> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| package_error(path.display().to_string(), error.to_string()))?;
    if metadata.file_type().is_symlink() {
        return Err(package_error(
            path.display().to_string(),
            "official-submission package output path must not be a symlink",
        ));
    }
    Ok(())
}

fn normalize_path(path: &Path) -> Result<PathBuf> {
    let mut normalized = if path.is_absolute() {
        PathBuf::new()
    } else {
        std::env::current_dir()
            .map_err(|error| package_error(path.display().to_string(), error.to_string()))?
    };
    for component in path.components() {
        match component {
            Component::Prefix(prefix) => normalized.push(prefix.as_os_str()),
            Component::RootDir => normalized.push(component.as_os_str()),
            Component::CurDir => {}
            Component::Normal(segment) => normalized.push(segment),
            Component::ParentDir => {
                return Err(package_error(
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
                return Err(package_error(
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

fn package_error(path: impl Into<String>, message: impl Into<String>) -> ZkBenchError {
    ZkBenchError::artifact(path, message)
}
