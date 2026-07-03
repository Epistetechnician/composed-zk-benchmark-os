# Phase 334 HSAI Accepted Formal Evidence Handoff Boundary

State slice: `Phase 334 HSAI accepted formal-evidence handoff boundary`.

## Boundary

Phase 334 defines a docs-first handoff boundary from Phase 333 local reviewed
formal-evidence record metadata toward a future accepted formal-evidence path.
It does not implement accepted formal evidence, mutate the accepted Evidence
Ledger, create Level2+ evidence, populate score axes, generate proof artifacts,
generate checker transcripts, generate solver certificates, execute Lean,
execute COBALT, run Rust-to-Lean extraction, submit benchmarks, or deploy to
production.

The current accepted-ledger append transaction remains authoritative for local
accepted evidence mutation. Its local append boundary rejects formal evidence
classes and claim boundaries above `Level1LocalReplay`. Phase 334 does not
bypass that guard and does not create a parallel accepted-evidence path.

## Current Evidence Ladder

The HSAI formal-evidence lane now has this local ladder:

```text
quarantined_output
-> formal_evidence_candidate
-> reviewed_formal_evidence_preview
-> reviewed_formal_evidence
-> future_accepted_formal_evidence_handoff
```

The final state above is only a future handoff target. It is not implemented by
Phase 334.

## Required Future Handoff Inputs

A future accepted formal-evidence handoff package must bind:

- Phase 333 reviewed-record digest.
- Phase 333 reviewed-record input digest.
- Phase 331 review-preview digest.
- Phase 331 preview-input digest.
- Phase 329 candidate digest.
- Phase 329 candidate-input digest.
- Phase 327 output-bundle manifest digest.
- Phase 325 preflight digest.
- Phase 323 source-manifest digest.
- reviewer and verifier policy ids.
- reviewer decision id, timestamp, and label.
- reviewed-scope statement digest.
- accepted-evidence-disabled acknowledgement digest.
- requested accepted-evidence class.
- requested claim boundary.
- accepted append policy version.
- formal-evidence acceptance policy version.
- explicit nonclaims for accepted evidence.
- rejection proof that no Level2+, score-axis, benchmark/SOTA, semantic
  correctness, production-readiness, full-security, or authority claim is being
  made.

## Required Future Policy Decision

Before implementation, the repository must make one explicit policy decision:

```text
Does accepted formal evidence remain forbidden by the accepted append path,
or does a new bounded formal-evidence class become admissible under a new
claim boundary below Level2+?
```

Until that decision is implemented in code and tests, Phase 333 reviewed-record
metadata cannot become accepted formal evidence.

## Forbidden Shortcuts

A future implementation must reject:

- direct mutation of the accepted Evidence Ledger from `hsai-agent-admission`;
- any append path that bypasses `zkbench-core` accepted append policy;
- any accepted formal-evidence record that lacks Phase 333 reviewed-record
  digest binding;
- any accepted formal-evidence record that lacks Phase 331 and Phase 329
  provenance binding;
- any accepted formal-evidence record that claims Level2+ evidence;
- any accepted formal-evidence record that populates score axes;
- any accepted formal-evidence record that claims benchmark comparison or SOTA;
- any accepted formal-evidence record that claims semantic correctness,
  production readiness, full security, breakthrough status, or action
  authority;
- any accepted formal-evidence record that treats a solver verdict, checker
  transcript, certificate, or reviewed metadata as proof authority without a
  separate proof/checker policy.

## Evidence Meaning

The maximum claim after Phase 334 is:

```text
HSAI has a documented handoff boundary from local reviewed formal-evidence
metadata to a future accepted formal-evidence path, while preserving the current
accepted append guard that blocks formal evidence and Level2+ claims.
```

That still is not:

- accepted formal evidence;
- Level2+ evidence;
- score-axis evidence;
- a Lean proof;
- a COBALT containment proof;
- a Rust-to-Lean proof;
- a checker transcript;
- a solver certificate;
- whole-system proof;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- authority to execute an action.

## Future Code Phase Exit Criteria

A future Phase 335 implementation may add local handoff metadata only if it:

- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create accepted formal evidence;
- binds Phase 333, Phase 331, Phase 329, Phase 327, Phase 325, and Phase 323
  digests;
- records the current accepted append formal-evidence blocker explicitly;
- records the future policy decision as unresolved;
- rejects Level2+, score-axis, benchmark/SOTA, semantic-correctness,
  production-readiness, full-security, and authority claims.
