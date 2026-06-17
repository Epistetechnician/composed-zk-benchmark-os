use std::collections::BTreeSet;

use zkbench_core::{
    build_smoke_soak_config, deserialize_soak_shard_manifest_json, plan_soak_shards,
    serialize_soak_shard_manifest_json, validate_soak_shard_manifest, ClaimBoundary, FamilyKind,
    MutationClass,
};

#[test]
fn same_config_produces_identical_shard_plan() {
    let config = build_smoke_soak_config()
        .with_families(vec![
            FamilyKind::BaselineFsm,
            FamilyKind::BoundedCounterLoop,
        ])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..3)
        .with_shard_count(2);

    let first = plan_soak_shards(config.clone()).expect("first plan should build");
    let second = plan_soak_shards(config).expect("second plan should build");
    assert_eq!(first, second);
    assert_eq!(first.shard_manifests[0].shard_id.value, "shard-0000");
    assert_eq!(first.shard_manifests[1].shard_id.value, "shard-0001");
}

#[test]
fn all_cases_are_assigned_exactly_once() {
    let plan = plan_soak_shards(
        build_smoke_soak_config()
            .with_families(vec![FamilyKind::BaselineFsm, FamilyKind::BranchingFsm])
            .with_seed_range(0..2)
            .with_shard_count(2),
    )
    .expect("plan should build");

    let planned = plan
        .case_plans
        .iter()
        .map(|case| case.id.clone())
        .collect::<BTreeSet<_>>();
    let assigned = plan
        .shard_manifests
        .iter()
        .flat_map(|manifest| manifest.assigned_case_ids.clone())
        .collect::<BTreeSet<_>>();
    assert_eq!(assigned, planned);
}

#[test]
fn changing_seed_range_changes_plan_predictably() {
    let base = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let changed = base.clone().with_seed_range(0..2);
    let base_plan = plan_soak_shards(base).expect("base plan should build");
    let changed_plan = plan_soak_shards(changed).expect("changed plan should build");
    assert_eq!(base_plan.case_plans.len(), 1);
    assert_eq!(changed_plan.case_plans.len(), 2);
    assert!(changed_plan.case_plans[1]
        .id
        .contains("seed_0000000000000001"));
}

#[test]
fn shard_manifest_roundtrips_and_uses_relative_refs() {
    let plan = plan_soak_shards(
        build_smoke_soak_config()
            .with_families(vec![FamilyKind::BaselineFsm])
            .with_seed_range(0..1)
            .with_shard_count(1),
    )
    .expect("plan should build");
    let manifest = &plan.shard_manifests[0];
    let validation = validate_soak_shard_manifest(manifest);
    assert!(validation.valid, "manifest issues: {:?}", validation.issues);
    assert_eq!(manifest.claim_boundary, ClaimBoundary::Level0DesignNote);
    assert!(manifest
        .relative_artifact_refs
        .iter()
        .all(|path| !path.starts_with('/')));

    let json = serialize_soak_shard_manifest_json(manifest).expect("manifest should serialize");
    let roundtrip =
        deserialize_soak_shard_manifest_json(&json).expect("manifest should deserialize");
    assert_eq!(&roundtrip, manifest);
}

#[test]
fn shard_manifest_rejects_duplicate_and_empty_case_ids() {
    let plan = plan_soak_shards(
        build_smoke_soak_config()
            .with_families(vec![FamilyKind::BaselineFsm])
            .with_seed_range(0..2)
            .with_shard_count(1),
    )
    .expect("plan should build");
    let mut manifest = plan.shard_manifests[0].clone();
    manifest
        .assigned_case_ids
        .push(manifest.assigned_case_ids[0].clone());
    manifest.expected_case_count = manifest.assigned_case_ids.len();

    let validation = validate_soak_shard_manifest(&manifest);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.message.contains("duplicated")));

    manifest.assigned_case_ids[1] = String::new();
    let validation = validate_soak_shard_manifest(&manifest);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.message.contains("empty")));
}

#[test]
fn shard_manifest_rejects_empty_artifact_refs() {
    let plan = plan_soak_shards(
        build_smoke_soak_config()
            .with_families(vec![FamilyKind::BaselineFsm])
            .with_seed_range(0..1)
            .with_shard_count(1),
    )
    .expect("plan should build");
    let mut manifest = plan.shard_manifests[0].clone();
    manifest.relative_artifact_refs.push(String::new());

    let validation = validate_soak_shard_manifest(&manifest);

    assert!(!validation.valid);
    assert!(validation
        .issues
        .iter()
        .any(|issue| issue.message.contains("artifact ref is empty")));
}
