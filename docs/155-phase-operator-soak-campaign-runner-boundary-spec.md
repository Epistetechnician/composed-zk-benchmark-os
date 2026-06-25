# Phase 155 Operator Soak Campaign Runner Boundary Spec

Status: docs-first boundary for an operator-facing soak campaign runner example.

## Purpose

The local soak campaign API in `crates/zkbench-core` ships as a library only.
Running a campaign today requires writing Rust code that builds a
`SoakRunConfig`, plans shards, builds a `SoakCampaignConfig` with an explicit
approval record and an absolute repo-external artifact root, calls
`run_soak_campaign`, and prints a summary. There is no operator entry point.

This boundary authorizes exactly one operator-facing example binary under
`crates/zkbench-core/examples/` that wraps the existing shipped library
surface. It is not a general command-line tool: it takes no CLI flags, uses
no argument-parsing dependency, and reads every input from fixed environment
variables following the same pattern as the existing `operator_live_*`
examples under `crates/hsai-attestation-phala/examples/` and
`crates/hsai-attestation/examples/`.

## State Slice

This phase may touch only:

- `crates/zkbench-core/examples/operator_soak_campaign.rs` (new example)
- `crates/zkbench-core/tests/operator_soak_campaign_contract.rs` (new
  hermetic source-contract test)
- `docs/155-phase-operator-soak-campaign-runner-boundary-spec.md`
- `docs/155-phase-operator-soak-campaign-runner-implementation-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

It does not authorize any Cargo metadata change (`Cargo.toml`, `Cargo.lock`),
dependency change, new library API, new library behavior, change to existing
soak semantics, change to existing claim boundaries, change to existing
validation, change to existing artifact layouts, package runtime file, shipped
binary target, installable command, CLI argument parsing, network access,
credential path, secret fixture, generated committed artifact, accepted
Evidence Ledger mutation, official benchmark submission, external replay
execution, live backend execution, score-axis population, ZK backend
performance claim, Level2+ evidence, formal evidence, proof, semantic
correctness, production readiness, global software-agent uniqueness, or 100%
coverage claim.

## Operator Entry Point Contract

The single example binary `operator_soak_campaign` reads exactly these
environment variables and nothing else:

- `ZKBENCH_SOAK_ACK` — explicit operator acknowledgement string. Must equal a
  fixed acknowledgement literal embedded in the example. Empty or mismatched
  values cause the binary to exit with an error before any work.
- `ZKBENCH_SOAK_CAMPAIGN_ID` — campaign id. Must be one portable path
  segment (the existing `validate_soak_campaign_config` rule).
- `ZKBENCH_SOAK_ARTIFACT_ROOT` — absolute path to a repo-external or
  git-ignored artifact root. Must be absolute (existing rule). The binary does
  not create the root; the operator creates it. The binary joins
  `campaign_id` under the root using the existing `run_soak_campaign` logic.
- `ZKBENCH_SOAK_APPROVED_BY` — non-empty operator handle for the
  `SoakCampaignApproval`.
- `ZKBENCH_SOAK_APPROVAL_STATEMENT` — non-empty operator approval statement
  for the `SoakCampaignApproval`.
- `ZKBENCH_SOAK_PROFILE` — optional. One of `smoke` or `regression`. Defaults
  to `smoke`.
- `ZKBENCH_SOAK_FAMILIES` — optional. Comma-separated family id segments from
  `FamilyKind::id_segment()` (for example `baseline_fsm,branching_fsm`). Empty
  or unset selects the existing `SoakFamilySelection::implemented_v0()` set.
- `ZKBENCH_SOAK_SEED_START` — optional. Inclusive seed range start.
  Defaults to `0`.
- `ZKBENCH_SOAK_SEED_END` — optional. Exclusive seed range end. Defaults to
  `4`.
- `ZKBENCH_SOAK_SHARD_COUNT` — optional. Shard count. Defaults to `1`.

The binary performs these steps in order:

1. Read and validate `ZKBENCH_SOAK_ACK`. Fail closed on mismatch.
2. Read and validate `ZKBENCH_SOAK_CAMPAIGN_ID`,
   `ZKBENCH_SOAK_ARTIFACT_ROOT`, `ZKBENCH_SOAK_APPROVED_BY`, and
   `ZKBENCH_SOAK_APPROVAL_STATEMENT`. Fail closed on empty values.
3. Build a `SoakRunConfig` from the chosen profile (`smoke` or `regression`),
   override the family selection, seed range, and shard count from the
   remaining env vars, and call `config.validate()`.
4. Call `plan_soak_shards(&config)`.
5. Build a `SoakCampaignConfig` with the supplied approval record, the
   absolute artifact root, `declared_outside_repo_or_ignored = true`, and the
   default `LocalSoakRunnerConfig`.
6. Call `run_soak_campaign(&campaign_config, plan)`.
7. Print a non-secret summary JSON document to stdout containing: campaign
   id, claim boundary, shard count, case count, replay completed count,
   replay failed count, traces evaluated, local oracle accepted count, local
   oracle rejected count, capability gap count, and the explicit nonclaim
   strings `"Local soak telemetry is not official benchmark evidence."` and
   `"Internal timing telemetry is not ZK backend performance."`.
8. Exit `0` on success, non-zero on any error from any step.

The binary performs no filesystem writes outside the declared artifact root,
makes no network calls, reads no credentials, retains no raw command bodies,
and emits no score axis population. The summary JSON is non-secret and safe
to share; it carries no source code, no witness data, and no operator
credentials.

## Required Hermetic Tests

`crates/zkbench-core/tests/operator_soak_campaign_contract.rs` must prove:

- the example source exists and contains the fixed acknowledgement literal;
- the example source contains no `std::process::Command`, no `Command::new`,
  no `std::net::`, no `reqwest`, no `ureq`, no `tokio`, no `clap`, no
  `structopt`, no argument vector inspection (`std::env::args`), and no
  `std::env::var` access for any name not in the authorized env var list
  above;
- the example source references every authorized env var name and no others;
- the example source calls `plan_soak_shards`, `run_soak_campaign`, and
  `config.validate()` (or the profile builder that validates);
- the example source contains the two required nonclaim strings;
- the example source does not contain forbidden benchmark-evidence language
  (`"official benchmark evidence"`, `"zk backend performance"` as a claim,
  `"Level2"`, `"accepted evidence"`, `"formal proof"`).

These tests are source-contract tests over the example file's bytes, matching
the pattern used by the existing operator-live source-contract tests under
`crates/hsai-attestation-phala/tests/`. They do not execute the binary, do
not require an artifact root, do not require credentials, and run as normal
workspace tests.

## Claim Boundary

The example is an operator entry point over already-shipped local soak
library behavior. A successful run produces `Level0DesignNote` local soak
telemetry only. It is not official benchmark evidence, not accepted Evidence
Ledger material, not external replay evidence, not ZK backend performance
evidence, not formal evidence, not proof, not semantic correctness, not
production readiness, and not global software-agent uniqueness.

## Non-Goals

This phase does not add a CLI argument parser, installable binary target,
shipped `[[bin]]` entry, package runtime file, dashboard, browser app,
JavaScript/TypeScript surface, new library API, new soak profile, new claim
boundary, credential path, network path, or external execution path. It does
not change existing soak campaign semantics, artifact layouts, validation,
or nonclaims. It does not promote any local soak output to accepted evidence.

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
