use tempfile::tempdir;
use zkbench_core::{
    apply_mutation_pass, build_local_replay_manifest_for_instance,
    build_zk_harness_dry_run_plan_from_pack, evaluate_generated_instance, evaluate_trace,
    list_available_local_generators, run_local_replay, BadCountersPass, BenchmarkPackReader,
    BenchmarkPackWriter, ClaimBoundary, CorruptedGuardsPass, EvidenceLedger, FamilyKind,
    FamilyTemplate, GeneratorConfig, InstanceParams, LocalJsonAdapter, LocalJsonReplayInput,
    MissingConstraintsPass, MutationClass, OracleOutcome, ResultClassification,
};

fn assert_family_generates_and_evaluates(config: GeneratorConfig, expected_kind: FamilyKind) {
    let family = zkbench_core::generate_family(config.clone())
        .unwrap_or_else(|err| panic!("{expected_kind:?} family should generate: {err:?}"));
    assert_eq!(family.family_kind, expected_kind);
    assert_eq!(
        family.claim_boundary,
        ClaimBoundary::Level1LocalReplay,
        "{expected_kind:?} must not exceed the local replay claim boundary"
    );

    let instance = family
        .instances
        .first()
        .unwrap_or_else(|| panic!("{expected_kind:?} family must produce a default instance"));
    let outcomes = evaluate_generated_instance(instance)
        .unwrap_or_else(|err| panic!("{expected_kind:?} traces must evaluate: {err:?}"));
    assert_eq!(
        outcomes.len(),
        2,
        "{expected_kind:?} must carry exactly one accepted and one rejected trace"
    );
    assert_eq!(
        outcomes[0],
        OracleOutcome::Accepted,
        "{expected_kind:?} accepted trace must evaluate to Accept"
    );
    assert!(
        matches!(outcomes[1], OracleOutcome::Rejected { .. }),
        "{expected_kind:?} rejected trace must evaluate to Reject"
    );
    assert!(
        family
            .evidence_notes
            .iter()
            .any(|note| note.contains("local semantic fixture")),
        "{expected_kind:?} must preserve the local semantic fixture nonclaim"
    );
}

#[test]
fn nested_loop_family_generates_and_evaluates() {
    assert_family_generates_and_evaluates(
        GeneratorConfig::nested_loop().seed(3).loop_bound(3),
        FamilyKind::NestedLoop,
    );
}

#[test]
fn guard_heavy_machine_family_generates_and_evaluates() {
    assert_family_generates_and_evaluates(
        GeneratorConfig::guard_heavy_machine().seed(5).loop_bound(4),
        FamilyKind::GuardHeavyMachine,
    );
}

#[test]
fn new_families_are_marked_implemented_in_registry() {
    assert!(FamilyKind::NestedLoop.is_implemented());
    assert!(FamilyKind::GuardHeavyMachine.is_implemented());

    let templates: Vec<FamilyKind> = list_available_local_generators()
        .into_iter()
        .map(|template: FamilyTemplate| template.kind)
        .collect();
    assert!(templates.contains(&FamilyKind::NestedLoop));
    assert!(templates.contains(&FamilyKind::GuardHeavyMachine));

    for template in list_available_local_generators() {
        if template.kind == FamilyKind::NestedLoop || template.kind == FamilyKind::GuardHeavyMachine
        {
            assert!(template.implemented);
            assert!(
                !template.supported_oracle_features.is_empty(),
                "{:?} template must declare supported oracle features",
                template.kind
            );
            assert!(
                template.description.contains("Generated"),
                "{:?} template must keep a deterministic description",
                template.kind
            );
        }
    }
}

#[test]
fn phase_164_families_are_marked_implemented_in_registry() {
    for kind in [
        FamilyKind::RecursiveEnvelope,
        FamilyKind::MemoryHeavyStateMachine,
        FamilyKind::PublicPrivateBoundaryStress,
        FamilyKind::ZkMlControlFlowMixed,
    ] {
        assert!(kind.is_implemented());
    }

    for template in list_available_local_generators() {
        if matches!(
            template.kind,
            FamilyKind::RecursiveEnvelope
                | FamilyKind::MemoryHeavyStateMachine
                | FamilyKind::PublicPrivateBoundaryStress
                | FamilyKind::ZkMlControlFlowMixed
        ) {
            assert!(template.implemented);
            assert!(!template.supported_oracle_features.is_empty());
        }
    }
}

#[test]
fn recursive_envelope_family_generates_and_evaluates() {
    assert_family_generates_and_evaluates(
        GeneratorConfig::recursive_envelope().seed(7).loop_bound(2),
        FamilyKind::RecursiveEnvelope,
    );
}

#[test]
fn memory_heavy_state_machine_family_generates_and_evaluates() {
    assert_family_generates_and_evaluates(
        GeneratorConfig::memory_heavy_state_machine().seed(11),
        FamilyKind::MemoryHeavyStateMachine,
    );
}

#[test]
fn public_private_boundary_stress_family_generates_and_evaluates() {
    assert_family_generates_and_evaluates(
        GeneratorConfig::public_private_boundary_stress().seed(13),
        FamilyKind::PublicPrivateBoundaryStress,
    );
}

#[test]
fn zkml_control_flow_mixed_family_generates_and_evaluates() {
    assert_family_generates_and_evaluates(
        GeneratorConfig::zkml_control_flow_mixed()
            .seed(17)
            .loop_bound(5),
        FamilyKind::ZkMlControlFlowMixed,
    );
}

#[test]
fn nested_loop_family_id_is_deterministic_and_seed_sensitive() {
    let base = GeneratorConfig::nested_loop().loop_bound(2);
    let left = zkbench_core::generate_family(base.clone())
        .expect("nested loop family should generate for id determinism");
    let right = zkbench_core::generate_family(base.clone())
        .expect("nested loop family should generate deterministically");
    assert_eq!(left.id, right.id);

    let shifted_seed = zkbench_core::generate_family(base.clone().seed(99))
        .expect("nested loop family should generate with shifted seed");
    assert_ne!(left.id, shifted_seed.id);

    let shifted_bound = zkbench_core::generate_family(base.loop_bound(3))
        .expect("nested loop family should generate with shifted bound");
    assert_ne!(left.id, shifted_bound.id);
}

#[test]
fn guard_heavy_machine_family_id_is_deterministic_and_seed_sensitive() {
    let base = GeneratorConfig::guard_heavy_machine().loop_bound(2);
    let left = zkbench_core::generate_family(base.clone())
        .expect("guard heavy machine family should generate for id determinism");
    let right = zkbench_core::generate_family(base.clone())
        .expect("guard heavy machine family should generate deterministically");
    assert_eq!(left.id, right.id);

    let shifted_seed = zkbench_core::generate_family(base.clone().seed(123))
        .expect("guard heavy machine family should generate with shifted seed");
    assert_ne!(left.id, shifted_seed.id);

    let shifted_bound = zkbench_core::generate_family(base.loop_bound(3))
        .expect("guard heavy machine family should generate with shifted bound");
    assert_ne!(left.id, shifted_bound.id);
}

#[test]
fn local_json_adapter_replays_new_families_without_external_claims() {
    for (config, kind) in [
        (
            GeneratorConfig::nested_loop().loop_bound(3),
            FamilyKind::NestedLoop,
        ),
        (
            GeneratorConfig::guard_heavy_machine().loop_bound(3),
            FamilyKind::GuardHeavyMachine,
        ),
    ] {
        let instance = zkbench_core::generate_instance(config, InstanceParams::default())
            .unwrap_or_else(|err| panic!("{kind:?} instance should generate: {err:?}"));
        let manifest = build_local_replay_manifest_for_instance(&instance)
            .unwrap_or_else(|err| panic!("{kind:?} replay manifest should build: {err:?}"));

        let output = LocalJsonAdapter::default()
            .replay_with_summary(LocalJsonReplayInput { manifest })
            .unwrap_or_else(|err| panic!("{kind:?} local JSON replay should run: {err:?}"));

        assert!(
            output.summary.local_accepted_count >= 1,
            "{kind:?} should produce at least one accepted local trace"
        );
        assert!(
            output.replay_result.trace_results.iter().any(|trace| {
                trace.result_classification == ResultClassification::ExpectedAcceptAccepted
            }),
            "{kind:?} should classify at least one trace as ExpectedAcceptAccepted"
        );
        assert_eq!(
            output.replay_result.claim_boundary,
            ClaimBoundary::Level1LocalReplay,
            "{kind:?} local replay must not exceed the local replay claim boundary"
        );
    }
}

#[test]
fn zk_harness_dry_run_exposes_new_family_labels() {
    let nested = zkbench_core::generate_instance(
        GeneratorConfig::nested_loop().seed(11),
        InstanceParams::default(),
    )
    .expect("nested loop instance should generate");
    let guard = zkbench_core::generate_instance(
        GeneratorConfig::guard_heavy_machine().seed(13),
        InstanceParams::default(),
    )
    .expect("guard heavy machine instance should generate");

    let nested_manifest = build_local_replay_manifest_for_instance(&nested)
        .expect("nested loop replay manifest should build");
    let nested_result = run_local_replay(&nested_manifest).expect("nested replay should run");
    let mut ledger = EvidenceLedger::new();
    ledger
        .append_replay_result(&nested_result)
        .expect("nested replay evidence should append");

    let dir = tempdir().expect("tempdir should be available");
    BenchmarkPackWriter::new("phase_154_new_families_pack")
        .with_generated_instance(nested)
        .with_generated_instance(guard)
        .with_replay_manifest(nested_manifest)
        .with_replay_result(nested_result)
        .with_evidence_ledger(ledger)
        .write_to(dir.path())
        .expect("new families pack should write");

    let reader = BenchmarkPackReader::read(dir.path()).expect("pack reader should load");
    let plan = build_zk_harness_dry_run_plan_from_pack(&reader)
        .expect("dry-run plan should build for new families");

    let family_labels = plan
        .pack_mapping
        .family_mappings
        .iter()
        .map(|mapping| mapping.candidate_workload_label.as_str())
        .collect::<Vec<_>>();
    assert!(
        family_labels.contains(&"control_flow_nested_loop"),
        "zk-Harness dry-run plan must expose the NestedLoop inert label, got {family_labels:?}"
    );
    assert!(
        family_labels.contains(&"control_flow_guard_heavy_machine"),
        "zk-Harness dry-run plan must expose the GuardHeavyMachine inert label, got {family_labels:?}"
    );

    let json = zkbench_core::serialize_zk_harness_dry_run_plan_json(&plan)
        .expect("dry-run plan should serialize");
    assert!(json.contains("control_flow_nested_loop"));
    assert!(json.contains("control_flow_guard_heavy_machine"));
    assert!(
        !json.to_lowercase().contains("official benchmark evidence"),
        "zk-Harness dry-run plan must not claim official benchmark evidence"
    );
}

#[test]
fn mutation_passes_apply_to_new_families_where_eligible() {
    let nested = zkbench_core::generate_instance(
        GeneratorConfig::nested_loop().loop_bound(2),
        InstanceParams::default(),
    )
    .expect("nested loop instance should generate");
    let guard = zkbench_core::generate_instance(
        GeneratorConfig::guard_heavy_machine().loop_bound(2),
        InstanceParams::default(),
    )
    .expect("guard heavy machine instance should generate");

    let mut eligible = 0usize;
    let mut skipped = 0usize;
    for (instance, class, pass) in [
        (
            &nested,
            MutationClass::BadCounters,
            &BadCountersPass as &dyn zkbench_core::MutationPass,
        ),
        (
            &nested,
            MutationClass::MissingConstraints,
            &MissingConstraintsPass as &dyn zkbench_core::MutationPass,
        ),
        (
            &guard,
            MutationClass::BadCounters,
            &BadCountersPass as &dyn zkbench_core::MutationPass,
        ),
        (
            &guard,
            MutationClass::CorruptedGuards,
            &CorruptedGuardsPass as &dyn zkbench_core::MutationPass,
        ),
    ] {
        match apply_mutation_pass(instance, pass) {
            Ok(mutated) => {
                eligible += 1;
                let outcome = evaluate_trace(&mutated.semantic_ir, &mutated.primary_trace)
                    .expect("mutated trace must evaluate");
                assert!(
                    matches!(
                        outcome,
                        OracleOutcome::Rejected { .. } | OracleOutcome::Accepted
                    ),
                    "mutated {class:?} trace should be Accepted or Rejected, got {outcome:?}"
                );
            }
            Err(_) => skipped += 1,
        }
    }
    assert!(
        eligible >= 2,
        "at least two new-family mutation combinations should be eligible, got {eligible}"
    );
    assert!(
        skipped <= 2,
        "skipped combinations should remain applicability telemetry only"
    );
}

#[test]
fn soak_runner_handles_new_families_through_lib_api() {
    use zkbench_core::{
        build_smoke_soak_config, plan_soak_shards, run_soak_campaign, validate_soak_report_bundle,
        LocalSoakRunnerConfig, SoakCampaignApproval, SoakCampaignArtifactRootPolicy,
        SoakCampaignConfig, SoakOutputPolicy,
    };

    fn approved_config(campaign_id: &str, artifact_root: std::path::PathBuf) -> SoakCampaignConfig {
        SoakCampaignConfig {
            campaign_id: campaign_id.to_string(),
            approval: SoakCampaignApproval {
                approved_by: "local_user".to_string(),
                approval_statement: "approved local new-family soak".to_string(),
                approved_at_ms: 0,
            },
            artifact_root_policy: SoakCampaignArtifactRootPolicy {
                artifact_root,
                declared_outside_repo_or_ignored: true,
            },
            runner_config: LocalSoakRunnerConfig::default(),
            notes: Vec::new(),
        }
    }

    for (kind, label) in [
        (FamilyKind::NestedLoop, "nested_loop"),
        (FamilyKind::GuardHeavyMachine, "guard_heavy_machine"),
    ] {
        let soak_config = build_smoke_soak_config()
            .with_families(vec![kind])
            .with_mutation_passes(vec![
                MutationClass::BadCounters,
                MutationClass::CorruptedGuards,
            ])
            .with_seed_range(0..2)
            .with_shard_count(1)
            .with_output_policy(SoakOutputPolicy::FailurePacksOnly {
                max_failure_packs: 2,
            });

        let plan = plan_soak_shards(soak_config).expect("shard plan should build");
        assert!(
            !plan.case_plans.is_empty(),
            "{kind:?} soak should plan at least one case"
        );
        assert!(
            !plan.shard_manifests.is_empty(),
            "{kind:?} soak should plan at least one shard"
        );

        let dir = tempdir().expect("tempdir should be available");
        let config = approved_config(&format!("phase_154_soak_{label}"), dir.path().to_path_buf());
        let result = run_soak_campaign(&config, plan)
            .unwrap_or_else(|err| panic!("{kind:?} soak campaign should run: {err:?}"));
        assert_eq!(
            result.claim_boundary,
            ClaimBoundary::Level0DesignNote,
            "{kind:?} soak must stay Level0DesignNote"
        );
        assert!(
            !result.contains_zk_backend_performance_claims(),
            "{kind:?} soak must not claim ZK backend performance"
        );

        let bundle_validation = validate_soak_report_bundle(&result.report_bundle);
        assert!(
            bundle_validation.valid,
            "{kind:?} soak report bundle invalid: {:?}",
            bundle_validation.issues
        );
    }
}
