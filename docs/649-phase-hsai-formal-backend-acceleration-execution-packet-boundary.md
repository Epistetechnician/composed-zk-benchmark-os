# Phase 649 HSAI Formal Backend Acceleration Execution Packet Boundary

State slice: `phase-649-hsai-formal-backend-acceleration-execution-packet-boundary`.

Phase 649 defines the docs-first boundary for a future local formal backend
execution packet over one exact Phase 648 preflight metadata record. It does
not execute Lean, SMT/Z3, COBALT, Rust-to-Lean extraction, Aeneas, Hax, Coq,
TLA+, CBMC, or any model checker. It does not generate proof artifacts, checker
transcripts, solver certificates, accepted evidence, Level2+ evidence, score
axes, benchmark evidence, or strong claims.

## Required Source State

The only future source is a Phase 648
`HsaiFormalBackendAccelerationPreflight` with classification:

```text
LocalPreflightMetadataRecorded
```

That source must bind:

- one Phase 646 blocked accepted-result output policy-resolution digest;
- one lane class;
- non-empty hermetic input manifest digests;
- expected command-role digest;
- expected output-schema digest;
- declared output-root digest;
- replay-rule digest;
- failure-taxonomy digest;
- provenance-requirements digest;
- negative-promotion-requirements digest;
- `Level1LocalReplayOrLower` mapping;
- explicit nonclaims.

If any binding drifts, a future implementation must fail closed.

## Future Execution Packet Fields

A future execution-packet implementation must be inert unless it can record all
of the following before any backend command is allowed:

1. Exact Phase 648 source digest and lane class.
2. Caller-selected local run id.
3. Tool role label and expected tool family.
4. Command descriptor digest, not raw shell text.
5. Input manifest digest set.
6. Output packet schema digest.
7. Transcript redaction policy digest.
8. Solver/checker/proof status vocabulary.
9. Timeout and nondeterminism policy digest.
10. Artifact quarantine policy digest.
11. Replay instruction digest.
12. Nonpromotion digest.

The packet must distinguish between `NotRun`, `RunRequested`, `RunObserved`,
`CheckerFailed`, `SolverUnknown`, `TimedOut`, `TranscriptMismatch`, and
`Rejected`. It must not treat a successful command exit as accepted evidence.

## Future Phase 650 Exit Criteria

A future Phase 650 may implement local execution-packet metadata only if it:

- accepts exactly one valid Phase 648 preflight metadata record;
- records an execution-packet request without invoking any command;
- stores only digests and explicit labels, not raw transcripts or raw proof
  artifacts;
- maps all outputs to `Level1LocalReplay` or lower;
- rejects accepted evidence, Level2+, score-axis population, benchmark
  evidence, semantic correctness, production readiness, SOTA, breakthrough,
  full security, external audit, human-review acceptance, and action authority;
- adds focused tests for valid packet metadata, source drift, missing digest,
  invalid status, and promotion rejection.

## Forbidden In This Phase

Phase 649 does not permit:

- Rust implementation code;
- Cargo metadata changes;
- new dependencies;
- binaries, scripts, or proof assistant setup files;
- external repo clones or vendored source;
- network access;
- command execution;
- Lean execution;
- SMT/Z3 execution;
- COBALT execution;
- Rust-to-Lean extraction;
- Aeneas, Hax, Coq, TLA+, CBMC, or model-checker execution;
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
- human-review acceptance claims;
- authority to execute an action.

## Meaning

The only defensible statement after Phase 649 is:

```text
HSAI has a docs-first local formal backend execution-packet boundary over Phase
648 preflight metadata.
```

It does not justify:

```text
HSAI ran Lean, SMT/Z3, COBALT, or Rust-to-Lean in this phase.
HSAI created proof artifacts, checker transcripts, or solver certificates.
HSAI created accepted formal evidence.
HSAI has Level2+ evidence.
HSAI populated score axes.
HSAI proves semantic correctness.
HSAI is production ready.
HSAI is SOTA.
HSAI is fully secure.
```
