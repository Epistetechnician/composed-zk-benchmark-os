//! Dashboard view model built from existing Score Reports.

use serde::{Deserialize, Serialize};

use crate::error::{Result, ZkBenchError};
use crate::evidence::ClaimBoundary;
use crate::pack::{PackReadinessReport, PackReadinessValidation};
use crate::scoring::{ScoreConfidence, ScoreReport};

/// Dashboard panel kind.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum DashboardPanelKind {
    /// Per-axis score rows.
    AxisScores,
    /// Overall confidence.
    Confidence,
    /// Claim boundary summary.
    ClaimBoundary,
    /// Risk penalties.
    RiskPenalties,
    /// Local pack-readiness metadata summary.
    PackReadiness,
}

/// One axis row in the axis panel.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DashboardAxisRow {
    /// Axis name.
    pub axis: String,
    /// Normalized score, when enough evidence exists.
    #[serde(default)]
    pub score: Option<f64>,
    /// Axis confidence.
    pub confidence: ScoreConfidence,
    /// True when the axis has no evidence yet.
    pub no_evidence: bool,
}

/// Dashboard panel.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DashboardPanel {
    /// Panel id.
    pub panel_id: String,
    /// Panel title.
    pub title: String,
    /// Panel kind.
    pub kind: DashboardPanelKind,
    /// Axis rows, for axis panels.
    #[serde(default)]
    pub axis_rows: Vec<DashboardAxisRow>,
    /// Free-form display lines, for non-axis panels.
    #[serde(default)]
    pub lines: Vec<String>,
    /// Claim boundary of the data shown in this panel.
    pub claim_boundary: ClaimBoundary,
}

/// Dashboard view model.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct DashboardModel {
    /// Dashboard id.
    pub dashboard_id: String,
    /// Model version.
    pub model_version: String,
    /// Panels.
    pub panels: Vec<DashboardPanel>,
    /// Maximum claim boundary across all displayed data.
    pub claim_boundary_max: ClaimBoundary,
    /// Notes.
    #[serde(default)]
    pub notes: Vec<String>,
}

impl DashboardModel {
    /// Dashboards never contain ZK backend performance claims.
    pub fn contains_zk_backend_performance_claims(&self) -> bool {
        false
    }
}

/// Build a dashboard model from one conservative Score Report.
pub fn build_dashboard_model_from_score_report(
    dashboard_id: impl Into<String>,
    report: &ScoreReport,
) -> DashboardModel {
    let axis_rows = vec![
        axis_row(
            "performance",
            report
                .performance
                .as_ref()
                .map(|score| (score.normalized_score, score.confidence)),
        ),
        axis_row(
            "correctness",
            report
                .correctness
                .as_ref()
                .map(|score| (score.alignment_score, score.confidence)),
        ),
        axis_row(
            "soundness_failure_detection",
            report
                .soundness_failure_detection
                .as_ref()
                .map(|score| (score.negative_test_coverage, score.confidence)),
        ),
        axis_row(
            "recursion_stress",
            report
                .recursion_stress
                .as_ref()
                .map(|score| (score.recursion_depth_score, score.confidence)),
        ),
        axis_row(
            "formal_evidence",
            report
                .formal_evidence
                .as_ref()
                .map(|score| (score.scoped_proof_score, score.confidence)),
        ),
        axis_row(
            "reproducibility",
            report
                .reproducibility
                .as_ref()
                .map(|score| (score.reproducibility_score, score.confidence)),
        ),
        axis_row(
            "adapter_portability",
            report
                .adapter_portability
                .as_ref()
                .map(|score| (score.portability_score, score.confidence)),
        ),
    ];
    let panels = vec![
        DashboardPanel {
            panel_id: "axis_scores".to_string(),
            title: "Axis Scores".to_string(),
            kind: DashboardPanelKind::AxisScores,
            axis_rows,
            lines: Vec::new(),
            claim_boundary: report.claim_boundary_max,
        },
        DashboardPanel {
            panel_id: "confidence".to_string(),
            title: "Overall Confidence".to_string(),
            kind: DashboardPanelKind::Confidence,
            axis_rows: Vec::new(),
            lines: vec![format!(
                "confidence: {:?} from {} evidence record(s)",
                report.confidence, report.evidence_count
            )],
            claim_boundary: report.claim_boundary_max,
        },
        DashboardPanel {
            panel_id: "claim_boundary".to_string(),
            title: "Claim Boundary".to_string(),
            kind: DashboardPanelKind::ClaimBoundary,
            axis_rows: Vec::new(),
            lines: vec![format!(
                "maximum claim boundary: {:?}",
                report.claim_boundary_max
            )],
            claim_boundary: report.claim_boundary_max,
        },
        DashboardPanel {
            panel_id: "risk_penalties".to_string(),
            title: "Risk Penalties".to_string(),
            kind: DashboardPanelKind::RiskPenalties,
            axis_rows: Vec::new(),
            lines: report
                .risk_penalties
                .iter()
                .map(|penalty| format!("{penalty:?}"))
                .collect(),
            claim_boundary: report.claim_boundary_max,
        },
    ];
    DashboardModel {
        dashboard_id: dashboard_id.into(),
        model_version: "phase-p-dashboard-v0".to_string(),
        panels,
        claim_boundary_max: report.claim_boundary_max,
        notes: vec![
            "Dashboard is a read-only view of existing reports.".to_string(),
            "No ZK backend performance claims are displayed.".to_string(),
        ],
    }
}

/// Build a read-only dashboard model from local pack-readiness metadata.
pub fn build_dashboard_model_from_pack_readiness(
    dashboard_id: impl Into<String>,
    report: &PackReadinessReport,
    validation: &PackReadinessValidation,
) -> DashboardModel {
    let passed_checks = report.checks.iter().filter(|check| check.passed).count();
    let failed_checks = report.checks.len().saturating_sub(passed_checks);
    let panels = vec![
        DashboardPanel {
            panel_id: "pack_readiness".to_string(),
            title: "Pack Readiness".to_string(),
            kind: DashboardPanelKind::PackReadiness,
            axis_rows: Vec::new(),
            lines: vec![
                format!("source pack: {}", report.source_pack_id),
                format!("readiness validation: {}", validation.valid),
                format!("checks passed: {passed_checks}"),
                format!("checks failed: {failed_checks}"),
                format!(
                    "external replay authorized: {}",
                    report.external_replay_authorized
                ),
                format!(
                    "creates Level2 evidence: {}",
                    report.creates_level2_evidence
                ),
                format!(
                    "official benchmark evidence: {}",
                    report.official_benchmark_evidence
                ),
                format!(
                    "ZK backend performance claims: {}",
                    report.zk_backend_performance_claims
                ),
            ],
            claim_boundary: ClaimBoundary::Level0DesignNote,
        },
        DashboardPanel {
            panel_id: "claim_boundary".to_string(),
            title: "Claim Boundary".to_string(),
            kind: DashboardPanelKind::ClaimBoundary,
            axis_rows: Vec::new(),
            lines: vec![
                "maximum claim boundary: Level0DesignNote".to_string(),
                "pack-readiness is not Level2 evidence".to_string(),
                "local replay is not official benchmark evidence".to_string(),
                "replay command metadata is not execution evidence".to_string(),
            ],
            claim_boundary: ClaimBoundary::Level0DesignNote,
        },
    ];
    DashboardModel {
        dashboard_id: dashboard_id.into(),
        model_version: "phase-p-dashboard-v0".to_string(),
        panels,
        claim_boundary_max: ClaimBoundary::Level0DesignNote,
        notes: vec![
            "Dashboard is a read-only view of existing pack-readiness metadata.".to_string(),
            "No ZK backend performance claims are displayed.".to_string(),
            "No official benchmark evidence is displayed.".to_string(),
        ],
    }
}

fn axis_row(axis: &str, score: Option<(Option<f64>, ScoreConfidence)>) -> DashboardAxisRow {
    match score {
        Some((score, confidence)) => DashboardAxisRow {
            axis: axis.to_string(),
            score,
            confidence,
            no_evidence: false,
        },
        None => DashboardAxisRow {
            axis: axis.to_string(),
            score: None,
            confidence: ScoreConfidence::Low,
            no_evidence: true,
        },
    }
}

/// Validate a dashboard model.
pub fn validate_dashboard_model(model: &DashboardModel) -> Result<()> {
    if model.dashboard_id.trim().is_empty() {
        return Err(ZkBenchError::validation(
            "dashboard.dashboard_id",
            "dashboard id is empty",
        ));
    }
    if model.panels.is_empty() {
        return Err(ZkBenchError::validation(
            "dashboard.panels",
            "dashboard must have at least one panel",
        ));
    }
    for panel in &model.panels {
        if panel.claim_boundary > model.claim_boundary_max {
            return Err(ZkBenchError::validation(
                format!("dashboard.panels.{}", panel.panel_id),
                "panel claim boundary exceeds the dashboard maximum",
            ));
        }
        if model.claim_boundary_max <= ClaimBoundary::Level1LocalReplay
            && panel.kind == DashboardPanelKind::PackReadiness
            && panel.claim_boundary != ClaimBoundary::Level0DesignNote
        {
            return Err(ZkBenchError::validation(
                format!("dashboard.panels.{}", panel.panel_id),
                "pack-readiness panels must remain Level0DesignNote",
            ));
        }
        if model.claim_boundary_max <= ClaimBoundary::Level1LocalReplay
            && panel.kind == DashboardPanelKind::AxisScores
            && panel
                .axis_rows
                .iter()
                .any(|row| row.score.is_some() || !row.no_evidence)
        {
            return Err(ZkBenchError::validation(
                format!("dashboard.panels.{}", panel.panel_id),
                "local dashboard score axes must remain unpopulated",
            ));
        }
    }
    let has_claim_panel = model
        .panels
        .iter()
        .any(|panel| panel.kind == DashboardPanelKind::ClaimBoundary);
    if !has_claim_panel {
        return Err(ZkBenchError::validation(
            "dashboard.panels",
            "dashboard must display a claim boundary panel",
        ));
    }
    Ok(())
}
