# Phase 155 Operator Soak Campaign Runner Implementation Notes

Status: implemented.

## State Slice

This phase touched only the state slice authorized by
`docs/155-phase-operator-soak-campaign-runner-boundary-spec.md`:

- `crates/zkbench-core/examples/operator_soak_campaign.rs` (new example)
- `crates/zkbench-core/tests/operator_soak_campaign_contract.rs` (new
  hermetic source-contract test)
- `docs/155-phase-operator-soak-campaign-runner-boundary-spec.md`
- `docs/155-phase-operator-soak-campaign-runner-implementation-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

No `Cargo.toml`, `Cargo.lock`, dependency, library API, library behavior,
soak semantics, claim boundary, validation, or artifact layout was touched.

## Operator Entry Point

`crates/zkbench-core/examples/operator_soak_campaign.rs` is the single
operator-facing entry point. It is auto-discovered by Cargo as an example
binary (`cargo run -p zkbench-core --example operator_soak_campaign`) and is
not a shipped `[[bin]]` target, not an installable command, and not a
package runtime file.

The example follows the same env-driven pattern as the existing
`operator_live_*` examples under `crates/hsai-attestation-phala/examples/`
and `crates/hsai-attestation/examples/`: no CLI flag parsing, no
argument-parsing dependency, every input read from a fixed authorized set of
environment variables.

## Environment Contract

Required:

- `ZKBENCH_SOAK_ACK` — must equal the fixed acknowledgement literal
  `"I acknowledge this soak campaign produces local Level0DesignNote telemetry only."`.
  Empty or mismatched values cause immediate non-zero exit.
- `ZKBENCH_SOAK_CAMPAIGN_ID` — portable single-segment campaign id.
- `ZKBENCH_SOAK_ARTIFACT_ROOT` — absolute path to a repo-external or
  git-ignored artifact root. The example does not create the root.
- `ZKBENCH_SOAK_APPROVED_BY` — non-empty operator handle.
- `ZKBENCH_SOAK_APPROVAL_STATEMENT` — non-empty operator approval statement.

Optional:

- `ZKBENCH_SOAK_PROFILE` — `smoke` (default) or `regression`.
- `ZKBENCH_SOAK_FAMILIES` — comma-separated family id segments from
  `FamilyKind::id_segment()`. Empty/unset selects
  `SoakFamilySelection::implemented_v0()`.
- `ZKBENCH_SOAK_SEED_START` — inclusive seed range start (default `0`).
- `ZKBENCH_SOAK_SEED_END` — exclusive seed range end (default `start + 4`).
- `ZKBENCH_SOAK_SHARD_COUNT` — shard count (default `1`).

## Execution Flow

1. Read and validate `ZKBENCH_SOAK_ACK`. Fail closed on mismatch.
2. Read and validate the four required string inputs. Fail closed on empty.
3. Validate `ZKBENCH_SOAK_ARTIFACT_ROOT` is absolute. Fail closed otherwise.
4. Build a `SoakRunConfig` from the chosen profile, override family
   selection, seed range, and shard count, and call `config.validate()`.
5. Call `plan_soak_shards(config)`.
6. Build a `SoakCampaignConfig` with the supplied approval, the absolute
   artifact root, `declared_outside_repo_or_ignored = true`, default
   `LocalSoakRunnerConfig`, and the two required nonclaims as notes.
7. Call `validate_soak_campaign_config` then `run_soak_campaign`.
8. Assert `result.contains_zk_backend_performance_claims()` is false and
   `result.claim_boundary <= Level0DesignNote`. Fail closed on violation.
9. Print a non-secret summary JSON to stdout.
10. Exit `0` on success, non-zero on any error.

## Summary Output

The summary JSON is non-secret and safe to share. It contains:

- `campaign_id`, `claim_boundary`, `profile`, `shard_count`, `case_count`;
- replay counters (`replay_completed_count`, `replay_failed_count`);
- oracle counters (`traces_evaluated`, `local_oracle_accepted_count`,
  `local_oracle_rejected_count`, `local_oracle_capability_gap_count`);
- mutation counters (`mutation_variant_count`, `mutation_no_target_count`);
- pipeline counters (`pack_write_count`, `failure_count`);
- `nonclaims`: the two required nonclaim strings.

It contains no source code, no witness data, no operator credentials, no raw
command bodies, and no score axis.

## Hermetic Source-Contract Tests

`crates/zkbench-core/tests/operator_soak_campaign_contract.rs` contains 9
tests that never execute the binary. They `include_str!` the example source
and assert:

- the fixed acknowledgement literal is embedded;
- every authorized env var name is referenced;
- the shipped library surface (`plan_soak_shards`, `run_soak_campaign`,
  `validate_soak_campaign_config`, `build_smoke_soak_config`,
  `build_regression_soak_config`, `SoakCampaignConfig`,
  `SoakCampaignApproval`, `SoakCampaignArtifactRootPolicy`,
  `LocalSoakRunnerConfig`) is used;
- the two required nonclaims are present;
- no forbidden claim substrings appear except inside explicit negations;
- no subprocess spawning (`std::process::Command`, `Command::new`), no CLI
  parsing (`std::env::args`, `clap`, `structopt`), no network stack
  (`std::net::`, `reqwest`, `ureq`, `tokio`);
- no unauthorized env var prefixes (`CREDENTIAL`, `TOKEN`, `SECRET`,
  `API_KEY`, `PASSWORD`, `PRIVATE_KEY`, `HSAI_`, `PHALA_`, `AWS_`,
  `DATABASE_URL`);
- no hardcoded artifact root or default campaign id;
- inputs are validated fail-closed (empty rejection, absolute-path check,
  acknowledgement mismatch);
- the claim boundary cap is enforced.

## Claim Boundary

The example produces `Level0DesignNote` local soak telemetry only. It is
not official benchmark evidence, not accepted evidence, not external replay
evidence, not ZK backend performance, not formal evidence, not proof, not
semantic correctness, not production readiness, and not global
software-agent uniqueness.

## Validation

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --features external-runner
cargo doc --workspace --no-deps
rg "std::process::Command|Command::new|std::net::|reqwest|ureq|tokio|clap|structopt|std::env::args" \
   crates/zkbench-core/examples crates/zkbench-core/src || true
```
