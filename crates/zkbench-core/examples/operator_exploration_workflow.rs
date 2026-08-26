//! Provider-free persistent operator workflow for deterministic exploration.
//!
//! Usage:
//!
//! ```text
//! cargo run -p zkbench-core --example operator_exploration_workflow -- run <root>
//! cargo run -p zkbench-core --example operator_exploration_workflow -- resume <root>
//! cargo run -p zkbench-core --example operator_exploration_workflow -- finalize <root>
//! cargo run -p zkbench-core --example operator_exploration_workflow -- report <root>
//! cargo run -p zkbench-core --example operator_exploration_workflow -- corpus <root>
//! cargo run -p zkbench-core --example operator_exploration_workflow -- export-minimized <root> <entry-id>
//! ```
//!
//! The example is local-only. It uses no credentials, network, provider,
//! process execution, evidence mutation, or benchmark claim surface.

use std::env;
use std::path::PathBuf;
use std::process::ExitCode;

use zkbench_core::{
    build_smoke_soak_config, BaselineCampaignConfig, ExplorationOperatorReport,
    ExplorationOperatorStore, ExplorationRunConfig, FamilyKind, MutationClass,
    OPERATOR_FINALIZED_PATH, OPERATOR_REPORT_MARKDOWN_PATH,
};

fn build_config() -> BaselineCampaignConfig {
    let base = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm, FamilyKind::BranchingFsm])
        .with_mutation_passes(vec![
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
        ])
        .with_seed_range(0..4)
        .with_shard_count(2);
    BaselineCampaignConfig::new(
        ExplorationRunConfig::new(base)
            .with_run_id("operator_exploration_workflow")
            .with_budgets(2, 1, 4, 17),
    )
    .with_campaign_id("operator_exploration_workflow")
}

fn usage() {
    eprintln!(
        "usage: operator_exploration_workflow <run|resume|finalize|report|corpus|export-minimized> <root> [entry-id]"
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
    let store = match ExplorationOperatorStore::new(root) {
        Ok(store) => store,
        Err(error) => {
            eprintln!("operator root rejected: {error}");
            return ExitCode::from(1);
        }
    };
    let config = if command == "run" {
        build_config()
    } else {
        match store.read_config() {
            Ok(config) => config,
            Err(error) => {
                eprintln!("retained campaign config unavailable: {error}");
                return ExitCode::from(1);
            }
        }
    };
    let outcome = match command.as_str() {
        "run" => store.run_validation(&config).map(|result| {
            println!(
                "validation retained: campaign={} winner={:?} report={} finalized=false",
                result.campaign_id, result.validation_winner, OPERATOR_REPORT_MARKDOWN_PATH
            );
        }),
        "resume" => store.resume_validation(&config).map(|result| {
            println!(
                "validation resumed exactly: campaign={} winner={:?} finalized=false",
                result.campaign_id, result.validation_winner
            );
        }),
        "finalize" => store.finalize_assessment(&config).map(|result| {
            println!(
                "assessment finalized: campaign={} report={} finalized=true",
                result.campaign_id, OPERATOR_FINALIZED_PATH
            );
        }),
        "report" => store.read_active_result(&config).and_then(|result| {
            let report = ExplorationOperatorReport::from_result(&result)?;
            print!("{}", report.render_markdown());
            Ok(())
        }),
        "corpus" => store.failure_corpus(&config).map(|corpus| {
            println!(
                "failure corpus: id={} entries={} claim_boundary={:?}",
                corpus.corpus_id, corpus.summary.entry_count, corpus.claim_boundary
            );
            for entry in corpus.entries {
                println!(
                    "{}\t{:?}\t{:?}\t{}",
                    entry.entry_id,
                    entry.failure_kind,
                    entry.triage_status,
                    entry.source_soak_case_id
                );
            }
        }),
        "export-minimized" => {
            let Some(entry_id) = args.next() else {
                usage();
                return ExitCode::from(2);
            };
            store
                .export_minimized_replay(&config, &entry_id)
                .map(|export| {
                    println!(
                        "minimized replay retained: entry={} manifest={} steps={} claim_boundary={:?}",
                        export.failure_entry.entry_id,
                        export.reduction.replay_manifest_id,
                        export.reduction.retained_steps.len(),
                        export.claim_boundary
                    );
                })
        }
        _ => {
            usage();
            return ExitCode::from(2);
        }
    };
    match outcome {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("operator workflow failed: {error}");
            ExitCode::from(1)
        }
    }
}
