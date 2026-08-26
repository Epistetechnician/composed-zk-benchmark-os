//! Provider-free operator example for
//! `antithesis-inspired-deterministic-exploration-v1`.
//!
//! This example runs a small local validation beam and finalizes one held-out
//! local assessment. It writes no files, uses no network, and emits no
//! accepted evidence or benchmark claim.

use zkbench_core::{
    build_smoke_soak_config, DeterministicExplorer, ExplorationRunConfig, FamilyKind, MutationClass,
};

fn main() {
    let base = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm, FamilyKind::BranchingFsm])
        .with_mutation_passes(vec![
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
        ])
        .with_seed_range(0..4)
        .with_shard_count(2);
    let config = ExplorationRunConfig::new(base)
        .with_run_id("operator_exploration_campaign")
        .with_budgets(2, 1, 4, 23);
    let explorer = DeterministicExplorer::new(config).expect("exploration config must validate");
    let mut result = explorer
        .run_validation()
        .expect("local validation exploration must complete");
    explorer
        .finalize_assessment(&mut result)
        .expect("held-out local assessment must finalize");

    let best = result
        .validation_frontier
        .records
        .first()
        .expect("validation frontier must contain one candidate");
    println!(
        "run={} candidate={} lineage={} validation_cases={} assessment_cases={} claim_boundary={:?}",
        result.run_id,
        best.candidate.candidate_id,
        result.lineage.len(),
        best.evaluation.observation.case_count,
        result
            .assessment_evaluation
            .as_ref()
            .map(|evaluation| evaluation.observation.case_count)
            .unwrap_or(0),
        result.claim_boundary
    );
}
