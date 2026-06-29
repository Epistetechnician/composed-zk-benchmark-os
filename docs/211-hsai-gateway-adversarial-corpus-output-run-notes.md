# Phase 211 HSAI Gateway Adversarial Corpus Output Run Notes

Status: complete for local hermetic implementation.

## State Slice

This phase touched only:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/211-hsai-gateway-adversarial-corpus-output-run-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Purpose

Compose the Phase 210 adversarial-corpus validation surface with the Phase 207
one-shot output-run helper. A caller can now validate a typed adversarial
corpus and model-lane registry before local replay and report-bundle
materialization.

The ordering is fail closed:

1. validate the adversarial corpus and model-lane registry;
2. stop before output creation if corpus validation fails;
3. evaluate the typed cases only after validation passes;
4. materialize the existing `gateway-report/*` bundle only after evaluation and
   report validation pass.

## Implemented

Phase 211 adds:

- `GatewayCorpusOutputRunError::CorpusValidation`
- `materialize_gateway_adversarial_corpus_output_run`

The new helper reuses `validate_gateway_adversarial_corpus`,
`materialize_gateway_corpus_output_run`, and the existing Phase 206 report
output materializer. It does not change report bundle shape.

## Tests

Focused tests cover:

- valid adversarial corpus validation followed by report materialization;
- invalid corpus validation stopping before output creation;
- protected output roots still failing through the existing materialization
  path after corpus validation passes.

## Claim Boundary

This is local typed metadata validation, local replay, and local report
materialization only. It is not corpus generation, not model execution, not
model download, not prompt storage, not provider verification, not hosted-model
calls, not external replay, not benchmark evidence, not Level2+ evidence, not
accepted Evidence Ledger mutation, not score-axis population, not production
readiness, not semantic correctness, not signer/tool integration, not custody,
not fully secure, and not a claim above `Attested`.

## Validation

Run from repository root:

```sh
cargo fmt --all --check
cargo test -p hsai-agent-admission --lib
cargo test -p zkbench-core --test repo_hygiene
cargo test -p zkbench-core --test repo_claim_boundary_docs
cargo test --workspace --quiet
```
