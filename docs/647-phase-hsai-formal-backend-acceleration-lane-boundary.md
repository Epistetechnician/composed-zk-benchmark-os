# Phase 647 HSAI Formal Backend Acceleration Lane Boundary

State slice: `phase-647-hsai-formal-backend-acceleration-lane-boundary`.

Phase 647 defines the docs-first boundary for moving from the current blocked
accepted-result output policy-resolution chain toward a faster local formal
backend lane. It does not run Lean, SMT/Z3, COBALT, Rust-to-Lean extraction,
Aeneas, Hax, Coq, TLA+, CBMC, or any model checker. It does not import results,
mutate accepted evidence, create Level2+ evidence, populate score axes, or
promote any public claim.

## Current Source State

The only current HSAI accepted-result output state is Phase 646 local blocked
policy-resolution metadata over one Phase 644 evidence eligibility record.
That chain remains blocked by missing independent external reproduction,
missing accepted external result evidence, missing Level2 review, and missing
score-axis preflight.

The current Phase 529/614 tiny-Z3 local verification path remains bounded local
replay evidence. It may be referenced as prior local SMT/Z3 evidence, but it
does not authorize new backend runs, accepted evidence, Level2+ evidence, score
axis population, or strong claims.

## Future Acceleration Lane Classes

A future implementation may define local preflight metadata for these lane
classes:

- `TinyZ3ReplayExtension`: a hermetic local extension of the existing tiny-Z3
  path.
- `LeanRepositoryScalePreflight`: Lean-oriented repository-scale benchmark
  preflight metadata.
- `CobaltContainmentPreflight`: COBALT-style containment or action-boundary
  preflight metadata.
- `RustToLeanExtractionPreflight`: Rust-to-Lean extraction preflight metadata
  for selected pure-data functions.
- `FederatedProofDispatchPreflight`: cross-backend proof-dispatch preflight
  metadata with explicit correspondence certificates.

These names are planning labels only. They are not evidence classes and do not
assert that any backend has run.

## Required Future Implementation Guardrails

A future implementation must fail closed unless it records all of the
following:

1. One named state slice and one lane class.
2. Hermetic input manifest digests.
3. Expected command shape or proof-tool role without invoking the command.
4. Output artifact schema and declared output roots.
5. Replay rules for deterministic local reruns.
6. Failure taxonomy for missing tools, invalid inputs, checker failure, solver
   unknown, timeout, nondeterministic output, and transcript mismatch.
7. Provenance requirements for tool version, command digest, input digest,
   output digest, and transcript digest.
8. Negative promotion tests that reject accepted evidence, Level2+ evidence,
   score-axis population, semantic-correctness claims, production-readiness
   claims, SOTA claims, breakthrough claims, full-security claims, and action
   authority.
9. Explicit mapping to `LocalReplay` / `Level1LocalReplay` or lower unless a
   later reviewed promotion phase accepts the result through the existing
   evidence owner.

## Forbidden In This Phase

Phase 647 does not permit:

- Rust implementation code;
- Cargo metadata changes;
- new dependencies;
- binaries, scripts, or proof assistant setup files;
- external repo clones or vendored source;
- network access;
- command execution for Lean, SMT/Z3, COBALT, Rust-to-Lean, Aeneas, Hax, Coq,
  TLA+, CBMC, or model checkers;
- proof artifact generation;
- checker transcript generation;
- solver certificate generation;
- filesystem artifact writes;
- external-result import;
- accepted Evidence Ledger mutation;
- accepted evidence creation;
- accepted independent external reproduction;
- Level2+ evidence creation;
- score-axis population;
- benchmark evidence creation;
- semantic-correctness claims;
- production-readiness claims;
- SOTA or breakthrough claims;
- full-security claims;
- external-audit claims;
- authority to execute an action.

## Future Phase 648 Exit Criteria

A future Phase 648 may implement local preflight metadata only if it:

- adds typed local metadata under an already authorized crate;
- accepts a lane class, hermetic input declarations, expected output
  declarations, replay rules, failure taxonomy, and provenance requirements;
- records no backend output and executes no backend command;
- maps all current outputs to `Level1LocalReplay` or lower;
- rejects every promotion flag listed in this boundary;
- adds focused tests for valid preflight metadata, lane-class drift, missing
  hermetic inputs, missing provenance fields, and promotion rejection.

## Meaning

The only defensible statement after Phase 647 is:

```text
HSAI has a docs-first formal backend acceleration boundary for future local
Lean/SMT/COBALT/Rust-to-Lean preflight metadata.
```

It does not justify:

```text
HSAI ran Lean, SMT/Z3, COBALT, or Rust-to-Lean in this phase.
HSAI created accepted formal evidence.
HSAI has Level2+ evidence.
HSAI populated score axes.
HSAI proves semantic correctness.
HSAI is production ready.
HSAI is SOTA.
HSAI is fully secure.
```
