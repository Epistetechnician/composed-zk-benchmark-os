# Phase L Qwable Autoresearch Contract

## State Slice

`Phase L local autoresearch soak over core benchmark OS loops with local-model
advisory lane`.

## Purpose

Run an overnight, bounded local autoresearch soak that repeatedly exercises the
benchmark OS core loops and uses a local Qwable model only to propose the next
debugging or hardening hypothesis after mechanical checks finish.

## Core Loops Under Test

- Surface DSL generation.
- Parsed AST and Semantic IR lowering.
- Mutation generation.
- Oracle and Expected Verdict evaluation.
- Local JSON replay.
- Evidence Record candidate creation.
- Proposal, review, and append-preview flow.
- Benchmark pack validation.
- Local soak telemetry.
- Health report aggregation.
- Failure corpus extraction.
- Phase 4 HSAI anchor-registry state invariants as a separate focused lane.

## Local Model Attachment

The attached local advisory model is:

```text
Mia-AiLab/Qwable-3.6-27b:Q4_K_M
```

The local server command is:

```sh
llama-server -hf Mia-AiLab/Qwable-3.6-27b:Q4_K_M -c 8192 --host 127.0.0.1 --port 8080
```

The model is advisory only. It may inspect non-secret local summaries and propose
next hypotheses. It cannot validate artifacts, approve evidence, raise claim
maturity, or replace mechanical verification.

## Mechanical Metric

Primary metric:

```text
zero claim-boundary violations and zero invalid aggregate report bundles
```

Secondary diagnostic counts:

- failed local soak cases;
- invalid failure-corpus entries;
- replay nondeterminism;
- invalid benchmark packs;
- Phase 4 registry invariant failures.

Secondary counts guide triage only. They do not become benchmark scores.

## Verification

Each kept iteration must pass:

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --features external-runner
cargo doc --workspace --no-deps
```

The campaign output must also validate its aggregate health report, report
bundle, and failure corpus under Level 0 local-health claim boundaries.

## Guardrails

- No live zk-Harness execution.
- No external benchmark execution.
- No external result import.
- No official benchmark evidence.
- No Level2+ evidence creation.
- No ZK backend performance claims.
- No use of local soak timing as prover or verifier timing.
- No secrets, `.phala-capture/`, private keys, raw captures, credentials, or
  unreviewed external artifacts sent to the local model.
- No model suggestion is kept unless a mechanical check justifies it.

## Artifact Policy

The durable run folder is:

```text
.autoresearch/phase-l-qwable-overnight/
```

That folder is gitignored. Campaign outputs must live outside the repository or
under a gitignored artifact root. Large outputs must not be committed.

## Stop Rule

Stop at the earlier of:

- the configured overnight wall-clock budget;
- three consecutive iterations with no new mechanical failure class and no
  smaller repro;
- any failed guardrail check;
- any uncertainty about whether a model-visible artifact contains secrets.

## Claim Boundary

All outputs are local operational telemetry or Level 0 design notes. The run does
not produce official benchmark evidence, backend performance evidence, proof, or
accepted evidence records.
