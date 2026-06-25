//! Hermetic source-contract tests for the operator soak campaign runner
//! example. These tests never execute the binary; they assert structural
//! invariants over its source bytes, matching the pattern used by the
//! existing operator-live source-contract tests.

const EXAMPLE_SOURCE: &str = include_str!("../examples/operator_soak_campaign.rs");

const AUTHORIZED_ENV_VARS: &[&str] = &[
    "ZKBENCH_SOAK_ACK",
    "ZKBENCH_SOAK_CAMPAIGN_ID",
    "ZKBENCH_SOAK_ARTIFACT_ROOT",
    "ZKBENCH_SOAK_APPROVED_BY",
    "ZKBENCH_SOAK_APPROVAL_STATEMENT",
    "ZKBENCH_SOAK_PROFILE",
    "ZKBENCH_SOAK_FAMILIES",
    "ZKBENCH_SOAK_SEED_START",
    "ZKBENCH_SOAK_SEED_END",
    "ZKBENCH_SOAK_SHARD_COUNT",
];

#[test]
fn example_source_exists_and_carries_fixed_acknowledgement() {
    assert!(
        !EXAMPLE_SOURCE.is_empty(),
        "operator soak campaign example source must exist"
    );
    assert!(
        EXAMPLE_SOURCE.contains(
            "\"I acknowledge this soak campaign produces local Level0DesignNote telemetry only.\""
        ),
        "operator soak campaign example must embed the fixed acknowledgement literal"
    );
}

#[test]
fn example_source_references_every_authorized_env_var() {
    for name in AUTHORIZED_ENV_VARS {
        assert!(
            EXAMPLE_SOURCE.contains(name),
            "operator soak campaign example must reference authorized env var {name}"
        );
    }
}

#[test]
fn example_source_calls_shipped_library_surface() {
    for required in [
        "plan_soak_shards",
        "run_soak_campaign",
        "validate_soak_campaign_config",
        "build_smoke_soak_config",
        "build_regression_soak_config",
        "SoakCampaignConfig",
        "SoakCampaignApproval",
        "SoakCampaignArtifactRootPolicy",
        "LocalSoakRunnerConfig",
    ] {
        assert!(
            EXAMPLE_SOURCE.contains(required),
            "operator soak campaign example must use shipped library symbol {required}"
        );
    }
}

#[test]
fn example_source_carries_required_nonclaims() {
    assert!(
        EXAMPLE_SOURCE.contains("Local soak telemetry is not official benchmark evidence."),
        "operator soak campaign example must carry the local soak telemetry nonclaim"
    );
    assert!(
        EXAMPLE_SOURCE.contains("Internal timing telemetry is not ZK backend performance."),
        "operator soak campaign example must carry the internal timing nonclaim"
    );
}

#[test]
fn example_source_contains_no_forbidden_claim_substrings() {
    // Forbidden phrases are allowed inside explicit nonclaim disavowals
    // (e.g. "X is not official benchmark evidence") but not as standalone
    // claims. We scan line by line and fail only when a forbidden phrase
    // appears on a line without a negation marker.
    let forbidden_claims = [
        "official benchmark evidence",
        "zk backend performance",
        "Level2",
        "accepted evidence",
        "formal proof",
    ];
    for line in EXAMPLE_SOURCE.lines() {
        let lower = line.to_lowercase();
        let is_negated = lower.contains("is not")
            || lower.contains("not ")
            || lower.contains("never ")
            || lower.contains("must not")
            || lower.contains("//");
        for claim in forbidden_claims {
            if lower.contains(claim) && !is_negated {
                panic!(
                    "operator soak campaign example line contains forbidden claim '{claim}' without negation:\n  {line}"
                );
            }
        }
    }

    // Hard-forbidden substrings never appear, even inside comments. We ban
    // subprocess spawning (`std::process::Command` / `Command::new`) and the
    // CLI/network surface, but `std::process::exit` is allowed because the
    // example legitimately exits non-zero on validation failure.
    for forbidden in [
        "std::env::args",
        "clap",
        "structopt",
        "std::process::Command",
        "Command::new",
        "std::net::",
        "reqwest",
        "ureq",
        "tokio",
    ] {
        assert!(
            !EXAMPLE_SOURCE.contains(forbidden),
            "operator soak campaign example must not contain forbidden substring '{forbidden}'"
        );
    }
}

#[test]
fn example_source_uses_only_authorized_env_var_names() {
    // The example uses const references for env var names, so we assert the
    // positive coverage test (every authorized name appears) and a negative
    // scan for common unauthorized env var prefixes that would indicate
    // credential, network, or token access drift.
    for prefix in [
        "CREDENTIAL",
        "TOKEN",
        "SECRET",
        "API_KEY",
        "PASSWORD",
        "PRIVATE_KEY",
        "HSAI_",
        "PHALA_",
        "AWS_",
        "DATABASE_URL",
    ] {
        assert!(
            !EXAMPLE_SOURCE.contains(prefix),
            "operator soak campaign example must not reference env var prefix '{prefix}'"
        );
    }
}

#[test]
fn example_source_does_not_hardcode_artifact_root_or_campaign_id() {
    // The example must read these from the operator, not bake in defaults.
    assert!(
        !EXAMPLE_SOURCE.contains("/tmp/operator_soak"),
        "operator soak campaign example must not hardcode an artifact root path"
    );
    assert!(
        !EXAMPLE_SOURCE.contains("\"default_campaign\""),
        "operator soak campaign example must not hardcode a default campaign id"
    );
}

#[test]
fn example_source_validates_inputs_fail_closed() {
    // The example must reject empty required values and a non-absolute root
    // before doing any work.
    assert!(
        EXAMPLE_SOURCE.contains("is_empty()"),
        "operator soak campaign example must reject empty required inputs"
    );
    assert!(
        EXAMPLE_SOURCE.contains("is_absolute()"),
        "operator soak campaign example must reject a non-absolute artifact root"
    );
    assert!(
        EXAMPLE_SOURCE.contains("did not match the required acknowledgement"),
        "operator soak campaign example must fail closed on acknowledgement mismatch"
    );
}

#[test]
fn example_source_uses_documented_seed_defaults_independently() {
    assert!(
        EXAMPLE_SOURCE.contains("unwrap_or(0)"),
        "operator soak campaign example must default ZKBENCH_SOAK_SEED_START to 0"
    );
    assert!(
        EXAMPLE_SOURCE.contains("unwrap_or(4)"),
        "operator soak campaign example must default ZKBENCH_SOAK_SEED_END to 4"
    );
    assert!(
        !EXAMPLE_SOURCE.contains("unwrap_or(start + 4)"),
        "operator soak campaign example must not derive the end default from the start"
    );
}

#[test]
fn example_source_enforces_claim_boundary_cap() {
    assert!(
        EXAMPLE_SOURCE.contains("contains_zk_backend_performance_claims"),
        "operator soak campaign example must assert no ZK backend performance claims"
    );
    assert!(
        EXAMPLE_SOURCE.contains("Level0DesignNote"),
        "operator soak campaign example must enforce the Level0DesignNote cap"
    );
}
