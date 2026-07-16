use thiserror::Error;

#[derive(Debug, Error, PartialEq, Eq)]
pub enum EvaluationErrorV1 {
    #[error("source import failed: {0}")]
    SourceImport(String),
    #[error("semantic pipeline failed: {0}")]
    SemanticPipeline(String),
    #[error("payoff analysis failed: {0}")]
    PayoffAnalysis(String),
    #[error("completeness composition failed: {0}")]
    Completeness(String),
    #[error("settlement decision failed: {0}")]
    Settlement(String),
    #[error("report bundle failed: {0}")]
    ReportBundle(String),
    #[error("authority attach failed: {0}")]
    Authority(String),
    #[error("digest binding mismatch: {0}")]
    DigestBindingMismatch(String),
}
