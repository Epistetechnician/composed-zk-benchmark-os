//! Markdown renderer for dashboard models.

use super::model::{DashboardModel, DashboardPanelKind};

/// Render a dashboard model as plain Markdown.
pub fn render_dashboard_markdown(model: &DashboardModel) -> String {
    let mut out = String::new();
    out.push_str(&format!("# Dashboard: {}\n\n", model.dashboard_id));
    out.push_str(&format!(
        "Maximum claim boundary: {:?}\n\n",
        model.claim_boundary_max
    ));
    for panel in &model.panels {
        out.push_str(&format!("## {}\n\n", panel.title));
        if panel.kind == DashboardPanelKind::AxisScores {
            out.push_str("| Axis | Score | Confidence | Evidence |\n");
            out.push_str("| --- | --- | --- | --- |\n");
            for row in &panel.axis_rows {
                let score = row
                    .score
                    .map(|score| format!("{score:.3}"))
                    .unwrap_or_else(|| "-".to_string());
                let evidence = if row.no_evidence { "none" } else { "present" };
                out.push_str(&format!(
                    "| {} | {} | {:?} | {} |\n",
                    row.axis, score, row.confidence, evidence
                ));
            }
            out.push('\n');
        } else if panel.lines.is_empty() {
            out.push_str("(none)\n\n");
        } else {
            for line in &panel.lines {
                out.push_str(&format!("- {line}\n"));
            }
            out.push('\n');
        }
        out.push_str(&format!("Claim boundary: {:?}\n\n", panel.claim_boundary));
    }
    for note in &model.notes {
        out.push_str(&format!("> {note}\n"));
    }
    out
}
