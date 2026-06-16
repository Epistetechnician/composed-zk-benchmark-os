//! Long local soak execution for deterministic Level 1 benchmark packs.
//!
//! Soak runs are local-only. They do not invoke external backends, do not
//! produce official benchmark evidence, and do not elevate claim boundaries
//! beyond Level1LocalReplay.

pub mod campaign;
pub mod config;
pub mod plans;
pub mod regression_corpus;
pub mod runner;

pub use campaign::{
    run_soak_campaign, serialize_soak_campaign_report_json, PackSampledReview, SoakCampaignConfig,
    SoakCampaignReport, SoakCampaignReportVersion,
};
pub use config::{
    SoakConfig, SoakExecutionReportVersion, SoakFailure, SoakPackDescriptor, SoakPlan,
};
pub use plans::{
    quick_campaign_config, quick_three_family_all_passes, quick_three_family_smoke,
    soak_config_from_plan,
};
pub use regression_corpus::{
    append_regression_entries, load_regression_corpus, save_regression_corpus,
    serialize_regression_corpus_json, RegressionCorpus, RegressionCorpusEntry,
    RegressionCorpusVersion, RegressionFailureKind,
};
pub use runner::{
    deserialize_soak_execution_report_json, run_local_soak, serialize_soak_execution_report_json,
    SoakExecutionReport,
};
