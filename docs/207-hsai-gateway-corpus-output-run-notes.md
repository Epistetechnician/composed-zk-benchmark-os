# Phase 207 HSAI Gateway Corpus Output Run Notes

Status: implemented for local, hermetic corpus output runs.

State slice:

- `crates/hsai-agent-admission/src/lib.rs`
- `docs/207-hsai-gateway-corpus-output-run-notes.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

## Goal

Phase 204 evaluates typed gateway cases. Phase 205 renders deterministic report
artifacts. Phase 206 materializes those artifacts. Phase 207 connects the three
steps into a single fail-closed local API so callers cannot accidentally
materialize stale or partially evaluated report state.

## Implemented Surface

New local types:

- `GatewayCorpusOutputRun`
- `GatewayCorpusOutputRunError`

New local helper:

- `materialize_gateway_corpus_output_run`

The helper evaluates a typed `GatewayCorpusCase` slice with a
`GatewayActionPolicy`, then materializes the resulting report bundle only after
successful evaluation and report validation.

## Validation Behavior

The one-shot API:

- returns evaluation errors before writing output;
- propagates output-root safety failures;
- produces the same declared `gateway-report/*` files as Phase 206;
- preserves the accepted-only handoff boundary;
- keeps metrics local and non-benchmark.

## Focused Tests

Implemented tests cover:

- successful typed corpus evaluation plus output materialization;
- duplicate/replayed gateway candidates failing before any output root is
  created;
- protected output-root rejection propagation.

## Claim Boundary

Phase 207 does not permit Cargo metadata changes, dependencies, package runtime
files, CLI/server/UI/dashboard work, model execution/download, committed
generated gateway report bundles, generated corpora/output bundles, secrets,
credentials, external replay execution, signer/wallet/exchange/custody/ACP/MCP
integration code, accepted Evidence Ledger mutation, score-axis population,
benchmark output, Level2+ evidence, production-readiness claims,
semantic-correctness claims, global software-agent uniqueness claims, "fully
secure" claims, or claims above `Attested`.
