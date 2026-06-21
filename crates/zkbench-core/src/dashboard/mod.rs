//! Phase P dashboard/reporting scaffolding.
//!
//! The dashboard renders existing Score Reports and soak health reports.
//! It is a read-only view layer: it never creates evidence, never promotes
//! claim boundaries, and never shows ZK backend performance claims. Every
//! rendered axis carries its confidence and the claim boundary it came from.

pub mod model;
pub mod render;

pub use model::{
    build_dashboard_model_from_pack_readiness, build_dashboard_model_from_score_report,
    validate_dashboard_model, DashboardAxisRow, DashboardModel, DashboardPanel, DashboardPanelKind,
};
pub use render::render_dashboard_markdown;
