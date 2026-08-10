# Phase 796-A3L5G HSAI P01B Snapshot Binding Graph Correction

## Status

Documentation-only correction required before A3L6 can be accepted and before
any A3L7/A3L8 command can run.

Named state slice:
`phase-796a3l5g-hsai-p01b-snapshot-binding-graph-correction`.

Execution status: `NotRun`. Correspondence remains `2/10`. Commercial moat
remains `3/10`; defensible breakthrough evidence remains `2-3/10`.

## Measured Contradiction

A3L5F correctly requires normal/OOM probe argv to carry the frozen
`snapshot_copy_manifest_sha256`. It also says that value is present in the
attempt plan and final authorization. The unchanged A3L5 exact attempt-plan
field set has only `source_manifest_sha256`; the A3L5C authorization-v3 field
set has no source or snapshot manifest field. Adding either field would change
a frozen schema and its domain vector.

No Docker, network, A3L7, or A3L8 execution discovered this contradiction.

## Correction

For normal/OOM attempt plans only, the existing
`source_manifest_sha256` field is superseded semantically to contain the exact
domain digest of the `hsai-p01b-snapshot-copy-manifest-v1` object. The same
value is the required `--input-manifest-sha256` argument in create argv and the
probe result. The field name is retained for wire compatibility; it does not
authorize a raw-list digest, a source-manifest digest, or a caller assertion.

The source manifest remains separately bound as
`expected_bindings.snapshot_source_manifest_sha256`. The copy manifest remains
separately bound as
`expected_bindings.snapshot_copy_manifest_sha256`. A3L7 constructs and
descriptor-validates both exact 21-entry manifests before final authorization,
and requires the attempt-plan field to equal the latter.

Authorization-v3 binds the copy-manifest digest transitively and without a new
field:

```text
authorization.expected_bindings_sha256
  == domain(expected-bindings)
expected-bindings.snapshot_copy_manifest_sha256
  == attempt-plan.source_manifest_sha256
  == create argv --input-manifest-sha256
  == probe result input_manifest_sha256
```

The authorization root binds the same expected-bindings domain digest. A3L9
reparses the complete objects and recomputes this equality chain; a matching
outer digest without the inner snapshot equality rejects.

## Keep Gate

A3L5G is kept only if two independent reviewers confirm that it resolves the
field-set contradiction without changing any schema/domain vector, preserves
both source and copy manifest validation, prohibits caller-supplied ambient
digests, and leaves all honesty assumptions, nonclaims, evidence ceilings, and
runtime prohibitions unchanged.

A3L6 remains unaccepted until its exact five-file immutable gate and two code
reviews pass. A3L7/A3L8 remain prohibited. No runtime evidence, class closure,
score movement, accepted Evidence Ledger evidence, Level2+ evidence, benchmark
evidence, proof, production-readiness, SOTA, breakthrough, full-security, or
external-audit claim is created by this correction.
