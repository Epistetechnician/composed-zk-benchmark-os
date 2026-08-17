# V32 Execution Record: Astral Scoring-Layer Contract

State slice: `astral-scoring-layer-contract-v32`.

Status: `Executed / LocalDevelopmentScoringLayerContract`.

## Scope

This run formalizes scoring-layer routing after V30 and V31. It is a pure
metadata regression test. No model, provider, network, reasoning trace,
secret, PII, V25/V28/V29 artifact, new loss, Stage 0C, Stage 1, or Evidence
Ledger mutation was used.

## Command and result

```text
cargo test -p zkbench-core --test astral_scoring_layers_v32 --quiet
```

Result: three tests passed; zero failed.

The frozen profile matrix produced zero unsupported upward promotions. V30/V31
evidence classified as `mechanism`, not `introspection`. Removing any one of
the introspection prerequisites lowered the result to `mechanism` or
`behavior`, and all current profiles remained at or below
`Level1LocalReplay`.

## Repository validation

The V32 test passed `rustfmt --check` and `git diff --check`. The existing V31,
V30, repository claim-boundary, and full `cargo test -p zkbench-core --quiet`
gates remain passing. No unrelated dirty or untracked path was modified.

## Disposition

V32 establishes a local scoring and claim-routing contract only. It prevents
behavioral or mechanism results from being labeled introspection without the
additional prerequisites. It does not establish self-understanding,
mechanistic faithfulness, consciousness, HSAI security, provider
cryptography, benchmark status, production readiness, Stage 0C, or Stage 1.

Maximum defensible claim:
`LocalDevelopmentScoringLayerContract`.
