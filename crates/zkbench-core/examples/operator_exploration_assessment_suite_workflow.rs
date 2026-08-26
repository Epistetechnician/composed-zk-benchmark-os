//! Provider-free persistent operator workflow for independent assessment suites.
//!
//! Usage:
//!
//! ```text
//! cargo run -p zkbench-core --example operator_exploration_assessment_suite_workflow -- run <root>
//! cargo run -p zkbench-core --example operator_exploration_assessment_suite_workflow -- resume <root>
//! cargo run -p zkbench-core --example operator_exploration_assessment_suite_workflow -- finalize <root>
//! cargo run -p zkbench-core --example operator_exploration_assessment_suite_workflow -- report <root>
//! ```
//!
//! The workflow is local-only. It uses no credentials, network, provider,
//! process execution, evidence mutation, or benchmark claim surface.

use std::env;
use std::path::PathBuf;
use std::process::ExitCode;

use zkbench_core::{
    build_smoke_soak_config, BaselineCampaignConfig, ExplorationRunConfig, FamilyKind,
    IndependentCampaignSuiteConfig, IndependentSuiteOperatorReport, IndependentSuiteOperatorStore,
    MutationClass, SUITE_OPERATOR_FINALIZED_PATH, SUITE_OPERATOR_REPORT_MARKDOWN_PATH,
};

fn campaign(start: u64, end: u64, suffix: &str) -> BaselineCampaignConfig {
    let base = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm, FamilyKind::BranchingFsm])
        .with_mutation_passes(vec![
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
        ])
        .with_seed_range(start..end)
        .with_shard_count(2);
    BaselineCampaignConfig::new(
        ExplorationRunConfig::new(base)
            .with_run_id(format!("suite_operator_workflow_{suffix}"))
            .with_budgets(2, 1, 4, 17),
    )
    .with_campaign_id(format!("suite_operator_workflow_campaign_{suffix}"))
}

fn build_config() -> IndependentCampaignSuiteConfig {
    IndependentCampaignSuiteConfig::new(
        "suite_operator_workflow",
        vec![campaign(0, 4, "a"), campaign(4, 8, "b")],
    )
}

fn usage() {
    eprintln!(
        "usage: operator_exploration_assessment_suite_workflow <run|resume|finalize|report> <root>"
    );
}

fn main() -> ExitCode {
    let mut args = env::args().skip(1);
    let Some(command) = args.next() else {
        usage();
        return ExitCode::from(2);
    };
    let Some(root) = args.next().map(PathBuf::from) else {
        usage();
        return ExitCode::from(2);
    };
    let store = match IndependentSuiteOperatorStore::new(root) {
        Ok(store) => store,
        Err(error) => {
            eprintln!("suite operator root rejected: {error}");
            return ExitCode::from(1);
        }
    };
    let config = if command == "run" {
        build_config()
    } else {
        match store.read_config() {
            Ok(config) => config,
            Err(error) => {
                eprintln!("retained suite config unavailable: {error}");
                return ExitCode::from(1);
            }
        }
    };
    let outcome = match command.as_str() {
        "run" => store.run_validation(&config).map(|result| {
            println!(
                "validation retained: suite={} campaigns={} report={} finalized=false",
                result.suite_id,
                result.validation_campaigns.len(),
                SUITE_OPERATOR_REPORT_MARKDOWN_PATH
            );
        }),
        "resume" => store.resume_validation(&config).map(|result| {
            println!(
                "validation resumed exactly: suite={} campaigns={} finalized=false",
                result.suite_id,
                result.validation_campaigns.len()
            );
        }),
        "finalize" => store.finalize_assessment(&config).map(|result| {
            let gate = result
                .promotion_gate
                .as_ref()
                .expect("finalized suite must contain a promotion gate");
            println!(
                "assessment finalized: suite={} improvements={}/{} promoted={} artifact={} finalized=true",
                result.suite_id,
                gate.observed_assessment_improvements,
                gate.required_assessment_improvements,
                gate.promoted,
                SUITE_OPERATOR_FINALIZED_PATH
            );
        }),
        "report" => store
            .read_report()
            .map(|report: IndependentSuiteOperatorReport| {
                print!("{}", report.render_markdown());
            }),
        _ => {
            usage();
            return ExitCode::from(2);
        }
    };
    match outcome {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("suite operator workflow failed: {error}");
            ExitCode::from(1)
        }
    }
}
