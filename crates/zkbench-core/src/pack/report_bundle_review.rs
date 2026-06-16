//! Sampled report-bundle review for local benchmark packs.
//!
//! A report bundle is a benchmark pack plus its conservative score report.
//! Review reports are Level0DesignNote metadata only.

use std::fs;
use std::path::{Path, PathBuf};

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;
use crate::pack::manifest::BenchmarkPackFileRole;
use crate::scoring::{ScoreConfidence, ScoreReport};

use super::reader::BenchmarkPackReader;

/// Report-bundle review report schema version.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleReviewReportVersion {
    /// Logical version string.
    pub value: String,
}

impl Default for ReportBundleReviewReportVersion {
    fn default() -> Self {
        Self {
            value: "phase-l-report-bundle-review-v0".to_string(),
        }
    }
}

/// Sampling strategy for report-bundle review.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub enum ReportBundleSampleStrategy {
    /// Review every Nth pack in stable sorted order.
    EveryNth {
        /// 1-based stride; 1 means review all packs.
        stride: usize,
    },
    /// Review the first N packs in stable sorted order.
    First {
        /// Maximum packs to review.
        count: usize,
    },
    /// Review all supplied packs.
    All,
}

impl Default for ReportBundleSampleStrategy {
    fn default() -> Self {
        Self::EveryNth { stride: 2 }
    }
}

/// Review plan for sampled report bundles.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleReviewPlan {
    /// Sampling strategy.
    pub sample_strategy: ReportBundleSampleStrategy,
    /// Whether a conservative score report must be present.
    pub require_score_report: bool,
    /// Whether README claim-boundary warnings must be present.
    pub require_readme_warnings: bool,
    /// Maximum claim boundary allowed in reviewed packs.
    pub claim_boundary_cap: ClaimBoundary,
}

impl Default for ReportBundleReviewPlan {
    fn default() -> Self {
        Self {
            sample_strategy: ReportBundleSampleStrategy::EveryNth { stride: 2 },
            require_score_report: true,
            require_readme_warnings: true,
            claim_boundary_cap: ClaimBoundary::Level1LocalReplay,
        }
    }
}

/// Severity for a report-bundle review finding.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum ReportBundleReviewFindingSeverity {
    /// Informational note.
    Info,
    /// Review warning.
    Warning,
    /// Review failure.
    Error,
}

/// One report-bundle review finding.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleReviewFinding {
    /// Pack id under review.
    pub pack_id: String,
    /// Relative pack root path when available.
    #[serde(default)]
    pub pack_root_relative: Option<String>,
    /// Finding severity.
    pub severity: ReportBundleReviewFindingSeverity,
    /// Stable finding code.
    pub code: String,
    /// Human-readable message.
    pub message: String,
}

/// Deterministic sampled review report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ReportBundleReviewReport {
    /// Report schema version.
    pub version: ReportBundleReviewReportVersion,
    /// Claim boundary for this review metadata.
    pub claim_boundary: ClaimBoundary,
    /// Review plan used.
    pub plan: ReportBundleReviewPlan,
    /// Total packs supplied for review.
    pub packs_total: usize,
    /// Packs sampled for review.
    pub packs_sampled: usize,
    /// Packs that passed all checks.
    pub packs_passed: usize,
    /// Packs that failed one or more checks.
    pub packs_failed: usize,
    /// Whether all sampled packs passed.
    pub valid: bool,
    /// Review findings.
    #[serde(default)]
    pub findings: Vec<ReportBundleReviewFinding>,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

/// Review one local report bundle at `pack_root`.
pub fn review_report_bundle(
    pack_root: impl AsRef<Path>,
    plan: &ReportBundleReviewPlan,
) -> Result<ReportBundleReviewReport> {
    validate_review_plan(plan)?;
    let pack_root = pack_root.as_ref();
    let reader = BenchmarkPackReader::read(pack_root)?;
    let pack_id = reader.manifest().id.clone();
    let findings = review_single_pack(&reader, plan, None)?;
    let packs_failed = usize::from(
        findings
            .iter()
            .any(|finding| finding.severity == ReportBundleReviewFindingSeverity::Error),
    );
    let packs_passed = 1usize.saturating_sub(packs_failed);
    Ok(ReportBundleReviewReport {
        version: ReportBundleReviewReportVersion::default(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        plan: plan.clone(),
        packs_total: 1,
        packs_sampled: 1,
        packs_passed,
        packs_failed,
        valid: packs_failed == 0,
        findings,
        notes: vec![
            format!("Reviewed pack '{pack_id}'."),
            "Report-bundle review is not official benchmark evidence.".to_string(),
        ],
    })
}

/// Review a sampled subset of report bundles under `soak_root` or from explicit paths.
pub fn review_sampled_report_bundles(
    pack_roots: &[PathBuf],
    plan: &ReportBundleReviewPlan,
) -> Result<ReportBundleReviewReport> {
    validate_review_plan(plan)?;
    let mut sorted_roots = pack_roots.to_vec();
    sorted_roots.sort();

    let sampled = sample_pack_roots(&sorted_roots, &plan.sample_strategy);
    let mut findings = Vec::new();
    let mut packs_failed = 0usize;

    for pack_root in &sampled {
        let reader = BenchmarkPackReader::read(pack_root)?;
        let pack_id = reader.manifest().id.clone();
        let pack_root_relative = pack_root
            .file_name()
            .and_then(|name| name.to_str())
            .map(str::to_string);
        let pack_findings = review_single_pack(&reader, plan, pack_root_relative)?;
        if pack_findings
            .iter()
            .any(|finding| finding.severity == ReportBundleReviewFindingSeverity::Error)
        {
            packs_failed += 1;
        }
        findings.extend(pack_findings);
        let _ = pack_id;
    }

    let packs_sampled = sampled.len();
    let packs_passed = packs_sampled.saturating_sub(packs_failed);
    Ok(ReportBundleReviewReport {
        version: ReportBundleReviewReportVersion::default(),
        claim_boundary: ClaimBoundary::Level0DesignNote,
        plan: plan.clone(),
        packs_total: sorted_roots.len(),
        packs_sampled,
        packs_passed,
        packs_failed,
        valid: packs_failed == 0,
        findings,
        notes: vec![
            "Sampled report-bundle review is not official benchmark evidence.".to_string(),
            "Reviewed packs remain Level1LocalReplay at most.".to_string(),
        ],
    })
}

/// Review packs listed in a soak execution report.
pub fn review_soak_report_bundles(
    soak_root: impl AsRef<Path>,
    soak_report: &crate::soak::SoakExecutionReport,
    plan: &ReportBundleReviewPlan,
) -> Result<ReportBundleReviewReport> {
    let soak_root = soak_root.as_ref();
    let pack_roots = soak_report
        .pack_descriptors
        .iter()
        .map(|descriptor| soak_root.join(&descriptor.pack_root_relative))
        .collect::<Vec<_>>();
    review_sampled_report_bundles(&pack_roots, plan)
}

/// Serialize a report-bundle review report to deterministic pretty JSON.
pub fn serialize_report_bundle_review_report_json(
    report: &ReportBundleReviewReport,
) -> Result<String> {
    serde_json::to_string_pretty(report).map_err(|error| {
        ZkBenchError::serialization("report_bundle_review.report", error.to_string())
    })
}

/// Deserialize a report-bundle review report from JSON.
pub fn deserialize_report_bundle_review_report_json(
    json: &str,
) -> Result<ReportBundleReviewReport> {
    serde_json::from_str(json).map_err(|error| {
        ZkBenchError::deserialization("report_bundle_review.report", error.to_string())
    })
}

fn validate_review_plan(plan: &ReportBundleReviewPlan) -> Result<()> {
    if plan.claim_boundary_cap > ClaimBoundary::Level1LocalReplay {
        return Err(ZkBenchError::benchmark_pack(
            "report_bundle_review.plan",
            "review claim boundary cap must not exceed Level1LocalReplay",
        ));
    }
    match plan.sample_strategy {
        ReportBundleSampleStrategy::EveryNth { stride } if stride == 0 => {
            Err(ZkBenchError::benchmark_pack(
                "report_bundle_review.plan",
                "EveryNth stride must be at least 1",
            ))
        }
        ReportBundleSampleStrategy::First { count } if count == 0 => {
            Err(ZkBenchError::benchmark_pack(
                "report_bundle_review.plan",
                "First count must be at least 1",
            ))
        }
        _ => Ok(()),
    }
}

fn sample_pack_roots(
    pack_roots: &[PathBuf],
    strategy: &ReportBundleSampleStrategy,
) -> Vec<PathBuf> {
    match strategy {
        ReportBundleSampleStrategy::All => pack_roots.to_vec(),
        ReportBundleSampleStrategy::First { count } => {
            pack_roots.iter().take(*count).cloned().collect()
        }
        ReportBundleSampleStrategy::EveryNth { stride } => pack_roots
            .iter()
            .enumerate()
            .filter_map(|(index, path)| {
                if index % stride == 0 {
                    Some(path.clone())
                } else {
                    None
                }
            })
            .collect(),
    }
}

fn review_single_pack(
    reader: &BenchmarkPackReader,
    plan: &ReportBundleReviewPlan,
    pack_root_relative: Option<String>,
) -> Result<Vec<ReportBundleReviewFinding>> {
    let manifest = reader.manifest();
    let pack_id = manifest.id.clone();
    let mut findings = Vec::new();

    let validation = reader.validate();
    if !validation.valid {
        for error in validation.errors {
            findings.push(finding(
                &pack_id,
                pack_root_relative.clone(),
                ReportBundleReviewFindingSeverity::Error,
                "pack_validation_failed",
                format!("{}: {}", error.path, error.message),
            ));
        }
    }

    if manifest.claim_boundary > plan.claim_boundary_cap {
        findings.push(finding(
            &pack_id,
            pack_root_relative.clone(),
            ReportBundleReviewFindingSeverity::Error,
            "claim_boundary_exceeded",
            format!(
                "pack claim boundary {:?} exceeds review cap {:?}",
                manifest.claim_boundary, plan.claim_boundary_cap
            ),
        ));
    }

    if plan.require_readme_warnings {
        findings.extend(check_readme_warnings(
            reader,
            &pack_id,
            pack_root_relative.clone(),
        )?);
    }

    if plan.require_score_report {
        findings.extend(check_score_report(
            reader,
            &pack_id,
            pack_root_relative.clone(),
        )?);
    }

    findings.extend(check_ledger_alignment(
        reader,
        &pack_id,
        pack_root_relative.clone(),
    )?);

    Ok(findings)
}

fn check_readme_warnings(
    reader: &BenchmarkPackReader,
    pack_id: &str,
    pack_root_relative: Option<String>,
) -> Result<Vec<ReportBundleReviewFinding>> {
    let readme_path = reader.root().join("README.md");
    let readme = fs::read_to_string(&readme_path).map_err(|error| {
        ZkBenchError::benchmark_pack(readme_path.display().to_string(), error.to_string())
    })?;
    let required_phrases = [
        "This pack contains local replay artifacts only.",
        "local replay is not official benchmark evidence",
        "a benchmark pass is not proof",
        "recursion proof is not semantic proof",
        "no external backend was invoked by this pack",
        "claim boundary is Level1LocalReplay or lower",
    ];
    let mut findings = Vec::new();
    for phrase in required_phrases {
        if !readme.contains(phrase) {
            findings.push(finding(
                pack_id,
                pack_root_relative.clone(),
                ReportBundleReviewFindingSeverity::Error,
                "readme_warning_missing",
                format!("README.md missing required phrase: {phrase}"),
            ));
        }
    }
    Ok(findings)
}

fn check_score_report(
    reader: &BenchmarkPackReader,
    pack_id: &str,
    pack_root_relative: Option<String>,
) -> Result<Vec<ReportBundleReviewFinding>> {
    let score_report_path = reader
        .manifest()
        .files
        .iter()
        .find(|file| file.role == BenchmarkPackFileRole::ScoreReport)
        .map(|file| reader.root().join(&file.relative_path));

    let Some(score_report_path) = score_report_path else {
        return Ok(vec![finding(
            pack_id,
            pack_root_relative,
            ReportBundleReviewFindingSeverity::Error,
            "score_report_missing",
            "required score report file is missing from pack manifest",
        )]);
    };

    let json = fs::read_to_string(&score_report_path).map_err(|error| {
        ZkBenchError::benchmark_pack(score_report_path.display().to_string(), error.to_string())
    })?;
    let report: ScoreReport = serde_json::from_str(&json).map_err(|error| {
        ZkBenchError::deserialization("report_bundle_review.score_report", error.to_string())
    })?;

    let mut findings = Vec::new();
    if report.claim_boundary_max > ClaimBoundary::Level1LocalReplay {
        findings.push(finding(
            pack_id,
            pack_root_relative.clone(),
            ReportBundleReviewFindingSeverity::Error,
            "score_report_claim_boundary_exceeded",
            format!(
                "score report claim boundary {:?} exceeds Level1LocalReplay",
                report.claim_boundary_max
            ),
        ));
    }
    if report.confidence != ScoreConfidence::Low {
        findings.push(finding(
            pack_id,
            pack_root_relative.clone(),
            ReportBundleReviewFindingSeverity::Error,
            "score_report_confidence_not_low",
            format!(
                "score report confidence {:?} must remain Low for local soak packs",
                report.confidence
            ),
        ));
    }
    if report.performance.is_some() {
        findings.push(finding(
            pack_id,
            pack_root_relative,
            ReportBundleReviewFindingSeverity::Error,
            "score_report_performance_populated",
            "score report must not populate performance metrics in Phase L",
        ));
    }
    Ok(findings)
}

fn check_ledger_alignment(
    reader: &BenchmarkPackReader,
    pack_id: &str,
    pack_root_relative: Option<String>,
) -> Result<Vec<ReportBundleReviewFinding>> {
    let manifest = reader.manifest();
    let ledger = reader.load_evidence_ledger()?;
    let Some(ledger) = ledger else {
        return Ok(vec![finding(
            pack_id,
            pack_root_relative,
            ReportBundleReviewFindingSeverity::Error,
            "evidence_ledger_missing",
            "required evidence ledger is missing",
        )]);
    };

    let mut findings = Vec::new();
    if ledger.summary.entry_count != manifest.summary.evidence_record_count {
        findings.push(finding(
            pack_id,
            pack_root_relative.clone(),
            ReportBundleReviewFindingSeverity::Error,
            "ledger_evidence_count_mismatch",
            format!(
                "ledger entry count {} does not match manifest evidence record count {}",
                ledger.summary.entry_count, manifest.summary.evidence_record_count
            ),
        ));
    }
    for entry in &ledger.entries {
        if entry.evidence_record.claim_boundary > ClaimBoundary::Level1LocalReplay {
            findings.push(finding(
                pack_id,
                pack_root_relative.clone(),
                ReportBundleReviewFindingSeverity::Error,
                "ledger_claim_boundary_exceeded",
                format!(
                    "ledger entry {} claim boundary {:?} exceeds Level1LocalReplay",
                    entry.sequence_number, entry.evidence_record.claim_boundary
                ),
            ));
        }
    }
    Ok(findings)
}

fn finding(
    pack_id: &str,
    pack_root_relative: Option<String>,
    severity: ReportBundleReviewFindingSeverity,
    code: &str,
    message: impl Into<String>,
) -> ReportBundleReviewFinding {
    ReportBundleReviewFinding {
        pack_id: pack_id.to_string(),
        pack_root_relative,
        severity,
        code: code.to_string(),
        message: message.into(),
    }
}
