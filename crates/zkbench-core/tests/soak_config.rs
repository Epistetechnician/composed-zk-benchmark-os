use zkbench_core::{
    build_regression_soak_config, build_smoke_soak_config, deserialize_soak_run_config_json,
    serialize_soak_run_config_json, validate_soak_run_config, ClaimBoundary, FamilyKind,
    MutationClass, SoakLimits, SoakOutputPolicy, SoakRunProfile,
};

#[test]
fn smoke_and_regression_configs_validate() {
    let smoke = build_smoke_soak_config();
    validate_soak_run_config(&smoke).expect("smoke config should validate");
    assert_eq!(smoke.claim_boundary, ClaimBoundary::Level0DesignNote);

    let regression = build_regression_soak_config();
    validate_soak_run_config(&regression).expect("regression config should validate");
    assert_eq!(regression.profile, SoakRunProfile::Regression);
}

#[test]
fn nightly_local_requires_explicit_opt_in() {
    let mut config = build_smoke_soak_config();
    config.profile = SoakRunProfile::NightlyLocal;
    assert!(validate_soak_run_config(&config)
        .expect_err("nightly local should require opt-in")
        .to_string()
        .contains("NightlyLocal"));

    config = config
        .allow_nightly_local(true)
        .with_limits(SoakLimits::nightly_local_explicit())
        .with_seed_range(0..16);
    validate_soak_run_config(&config).expect("explicit nightly local should validate");
}

#[test]
fn excessive_config_values_are_rejected() {
    let config = build_smoke_soak_config().with_seed_range(0..99);
    assert!(validate_soak_run_config(&config)
        .expect_err("excessive seed count should fail")
        .to_string()
        .contains("max_seeds"));

    let config = build_smoke_soak_config().with_shard_count(99);
    assert!(validate_soak_run_config(&config)
        .expect_err("excessive shard count should fail")
        .to_string()
        .contains("max_shards"));

    let config = build_smoke_soak_config()
        .with_output_policy(SoakOutputPolicy::SampledPacks { max_packs: 99 });
    assert!(validate_soak_run_config(&config)
        .expect_err("excessive pack writes should fail")
        .to_string()
        .contains("max_pack_writes"));
}

#[test]
fn config_round_trips_and_contains_no_external_execution_settings() {
    let config = build_smoke_soak_config()
        .with_families(vec![FamilyKind::BaselineFsm])
        .with_mutation_passes(vec![MutationClass::MissingConstraints])
        .with_seed_range(0..1)
        .with_shard_count(1);
    let json = serialize_soak_run_config_json(&config).expect("config should serialize");
    assert!(!json.contains("ExternalExecution"));
    assert!(!json.contains("zk-Harness"));
    let roundtrip = deserialize_soak_run_config_json(&json).expect("config should deserialize");
    assert_eq!(roundtrip, config);
    assert_eq!(roundtrip.claim_boundary, ClaimBoundary::Level0DesignNote);
}
