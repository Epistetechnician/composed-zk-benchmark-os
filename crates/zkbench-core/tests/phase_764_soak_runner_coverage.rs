//! Focused local soak-runner coverage for remaining family dispatch and
//! pack-write short-circuit without an output directory.
//!
//! Local soak runner coverage is Level0DesignNote / Level1LocalReplay
//! regression only. It is not official benchmark evidence, not accepted
//! evidence, not Level2+ evidence, and not ZK backend performance.

use zkbench_core::{
    build_smoke_soak_config, plan_soak_shards, ClaimBoundary, FamilyKind, LocalSoakRunner,
    MockTelemetryClock, MutationClass, SoakCaseStatus, SoakOutputPolicy, SoakShardId,
};

fn remaining_family_config(family: FamilyKind) -> zkbench_core::SoakRunConfig {
    build_smoke_soak_config()
        .with_families(vec![family])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::NoPacks)
}

#[test]
fn remaining_family_kinds_dispatch_through_local_soak_runner() {
    for family in [
        FamilyKind::RecursiveEnvelope,
        FamilyKind::MemoryHeavyStateMachine,
        FamilyKind::PublicPrivateBoundaryStress,
        FamilyKind::ZkMlControlFlowMixed,
    ] {
        let plan = plan_soak_shards(remaining_family_config(family))
            .unwrap_or_else(|error| panic!("{family:?} plan should build: {error}"));
        let mut runner = LocalSoakRunner::new(plan).with_clock(MockTelemetryClock::default());
        let result = runner
            .run_shard(SoakShardId::from_index(0))
            .unwrap_or_else(|error| panic!("{family:?} soak shard should run: {error}"));

        assert_eq!(result.claim_boundary(), ClaimBoundary::Level0DesignNote);
        assert_eq!(result.case_results.len(), 1);
        assert_eq!(result.case_results[0].family_kind, family);
        assert!(
            matches!(
                result.case_results[0].status,
                SoakCaseStatus::Completed
                    | SoakCaseStatus::CompletedWithLocalRejections
                    | SoakCaseStatus::FailedMutation
                    | SoakCaseStatus::FailedReplay
            ),
            "{family:?} unexpected status {:?}",
            result.case_results[0].status
        );
        assert!(
            result
                .telemetry_report
                .snapshot
                .counters
                .generated_instance_count
                >= 1,
            "{family:?} should generate at least one instance"
        );
    }
}

#[test]
fn sampled_packs_without_output_dir_short_circuit_pack_write() {
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1)
        .with_output_policy(SoakOutputPolicy::SampledPacks { max_packs: 1 });
    let plan = plan_soak_shards(config).expect("plan should build");
    let mut runner = LocalSoakRunner::new(plan).with_clock(MockTelemetryClock::default());

    let result = runner
        .run_shard(SoakShardId::from_index(0))
        .expect("soak without output_dir should still complete");

    assert_eq!(result.claim_boundary(), ClaimBoundary::Level0DesignNote);
    assert_eq!(result.case_results.len(), 1);
    assert_eq!(
        result.telemetry_report.snapshot.counters.pack_write_count, 1,
        "should_write_pack should still count the short-circuited write"
    );
    assert_eq!(
        result
            .telemetry_report
            .snapshot
            .counters
            .pack_read_validation_count,
        1
    );
    assert!(
        matches!(
            result.case_results[0].status,
            SoakCaseStatus::Completed | SoakCaseStatus::CompletedWithLocalRejections
        ),
        "unexpected status {:?}",
        result.case_results[0].status
    );
}
