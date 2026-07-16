# Statebook P8 Evaluation And Falsification Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p8-evaluation-and-falsification`.

## Outcome

A new composing `statebook-e2e-harness` crate hosts:

- one hermetic P1–P7 golden path via `run_hermetic_golden_path_v1`;
- structured `EvaluationReceiptV1` binding digests and outcomes;
- TD-011 / whitepaper §15 falsifiers for P4 hard-gate failure, P5 readback
  tamper, P7 execution-authority grant rejection, and unbound P7 digest
  binding;
- claim-boundary source scans.

P8 does not mutate P1–P7 crates. Live authority products remain deferred behind
the P7 legal/ops gate. No value moves.

## Golden path

1. P6 captured import (`synthetic-clearing-terms-v1`)
2. P1 parse / lower / StateKey
3. P2 residual analysis over three declared states
4. P3 completeness composition
5. P4 immediate settlement decision
6. P5 handoff (`grants_authority=false`) + materialize/readback
7. P7 authority attach bound to P1 `validated_contract_digest` and P2
   `domain_digest`

## Local validation evidence

```text
cargo fmt -p statebook-e2e-harness -- --check
cargo test -p statebook-e2e-harness --tests
cargo clippy -p statebook-e2e-harness --all-targets -- -D warnings
cargo test -p statebook-core -p statebook-settlement -p statebook-report -p statebook-source -p statebook-authority --tests
```

Nine focused harness tests pass: six golden/falsifier paths and three
claim-boundary scans.

## Remaining gaps vs boundary / TD-011

Minimum golden path and falsifiers are covered. Optional follow-ons:

- broader TD-004 / P4 thirty-seven-scenario adversarial corpus replay;
- labeled semantic precision/recall corpus;
- richer metric serialization without production threshold claims.

## Claim ceiling

This is local hermetic composed P1–P7 regression and falsification-surface
evidence only. It is not live authority, clearing recognition, legal finality,
production metric thresholds, SOTA, independent audit, or full security.
Completing P8 does not satisfy the P7 legal/ops gate. No value moves.
