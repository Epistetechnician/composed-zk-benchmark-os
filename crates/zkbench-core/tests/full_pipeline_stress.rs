use std::collections::BTreeSet;

use zkbench_core::{
    apply_mutation_pass, build_local_replay_manifest_for_instance,
    build_local_replay_manifest_for_mutation, generate_instance, BadCountersPass, ClaimBoundary,
    CorruptedGuardsPass, FamilyKind, GeneratorConfig, InstanceParams, LocalJsonAdapter,
    MissingConstraintsPass, MutationClass, ResultClassification,
};

fn config_for_family(family: FamilyKind, seed: u64) -> GeneratorConfig {
    match family {
        FamilyKind::BaselineFsm => GeneratorConfig::baseline_fsm().seed(seed),
        FamilyKind::BranchingFsm => GeneratorConfig::branching_fsm().seed(seed),
        FamilyKind::BoundedCounterLoop => GeneratorConfig::bounded_counter_loop()
            .seed(seed)
            .loop_bound(3),
        _ => unreachable!("stress test only enumerates implemented v0 families"),
    }
}

#[test]
fn deterministic_generation_mutation_replay_stress_stays_claim_capped() {
    let adapter = LocalJsonAdapter::default();
    let families = [
        FamilyKind::BaselineFsm,
        FamilyKind::BranchingFsm,
        FamilyKind::BoundedCounterLoop,
    ];
    let mut generated_count = 0usize;
    let mut mutation_count = 0usize;
    let mut skipped_mutation_count = 0usize;
    let mut applied_mutation_classes = BTreeSet::new();
    let mut local_accepts = 0usize;
    let mut local_rejections = 0usize;

    for family in families {
        assert!(family.is_implemented());
        for seed in 0..2 {
            let instance =
                generate_instance(config_for_family(family, seed), InstanceParams::default())
                    .expect("implemented family should generate");
            generated_count += 1;
            assert!(instance.claim_boundary <= ClaimBoundary::Level1LocalReplay);

            let manifest = build_local_replay_manifest_for_instance(&instance)
                .expect("generated instance manifest should build");
            let replay = adapter
                .replay(&manifest)
                .expect("generated instance should replay locally");
            assert_eq!(replay.claim_boundary, ClaimBoundary::Level1LocalReplay);
            assert!(replay.trace_results.iter().any(|trace| {
                trace.result_classification == ResultClassification::ExpectedAcceptAccepted
            }));
            assert!(replay.trace_results.iter().any(|trace| {
                trace.result_classification == ResultClassification::ExpectedRejectRejected
            }));
            for trace in replay.trace_results {
                match trace.result_classification {
                    ResultClassification::ExpectedAcceptAccepted => local_accepts += 1,
                    ResultClassification::ExpectedRejectRejected => local_rejections += 1,
                    other => panic!(
                        "generated local replay should only produce expected local outcomes, got {other:?}"
                    ),
                }
            }

            for (mutation_class, mutation) in [
                (
                    MutationClass::MissingConstraints,
                    apply_mutation_pass(&instance, &MissingConstraintsPass),
                ),
                (
                    MutationClass::CorruptedGuards,
                    apply_mutation_pass(&instance, &CorruptedGuardsPass),
                ),
                (
                    MutationClass::BadCounters,
                    apply_mutation_pass(&instance, &BadCountersPass),
                ),
            ] {
                let Ok(mutation) = mutation else {
                    skipped_mutation_count += 1;
                    continue;
                };
                mutation_count += 1;
                assert_eq!(mutation.mutation_class, mutation_class);
                applied_mutation_classes.insert(mutation_class);
                assert!(mutation.claim_boundary <= ClaimBoundary::Level1LocalReplay);
                let manifest = build_local_replay_manifest_for_mutation(&mutation)
                    .expect("mutation manifest should build");
                let replay = adapter
                    .replay(&manifest)
                    .expect("mutated instance should replay locally");
                assert_eq!(replay.claim_boundary, ClaimBoundary::Level1LocalReplay);
                assert_eq!(replay.trace_results.len(), 1);
                assert_eq!(replay.evidence_records.len(), 1);
                for trace in replay.trace_results {
                    match trace.result_classification {
                        ResultClassification::ExpectedAcceptAccepted => local_accepts += 1,
                        ResultClassification::ExpectedRejectRejected
                        | ResultClassification::ExpectedAcceptRejected
                        | ResultClassification::ExpectedRejectAcceptedUnsoundCandidate => {
                            local_rejections += 1
                        }
                        ResultClassification::Timeout
                        | ResultClassification::CapabilityGap
                        | ResultClassification::MalformedArtifact => {
                            panic!(
                                "full local pipeline stress must not degrade to {:?}",
                                trace.result_classification
                            );
                        }
                        ResultClassification::ExpectedRejectBackendError
                        | ResultClassification::ExpectedBackendErrorObserved
                        | ResultClassification::Inconclusive
                        | ResultClassification::UnexpectedOutcome => {
                            panic!(
                                "full local pipeline stress must stay deterministic, got {:?}",
                                trace.result_classification
                            );
                        }
                    }
                }
            }
        }
    }

    assert_eq!(generated_count, 6);
    assert!(
        mutation_count >= 12,
        "stress loop should apply most implemented mutation passes"
    );
    assert!(
        skipped_mutation_count > 0,
        "stress loop should document non-eligible local mutation combinations"
    );
    assert_eq!(
        applied_mutation_classes,
        BTreeSet::from([
            MutationClass::MissingConstraints,
            MutationClass::CorruptedGuards,
            MutationClass::BadCounters,
        ])
    );
    assert!(
        local_accepts > 0,
        "stress loop should include accepted local mutation outcomes"
    );
    assert!(
        local_rejections > 0,
        "stress loop should include rejected local mutation outcomes"
    );
}
