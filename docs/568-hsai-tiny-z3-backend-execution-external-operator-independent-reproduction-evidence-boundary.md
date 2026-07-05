# Phase 568 HSAI Tiny Z3 Backend Execution External Operator Independent Reproduction Evidence Boundary

State slice: `Phase 568 HSAI tiny Z3 backend execution external operator independent reproduction evidence boundary`.

Phase 568 defines the docs-first evidence requirement boundary for the
independent-external-reproduction blocker recorded by Phase 567. It does not
create independent external reproduction. It defines what a future record must
prove before the accepted-result policy path may advance.

## Current Input

The only allowed source is one exact Phase 567 policy-resolution metadata
record with classification:

```text
AcceptedResultPolicyResolutionBlocked
```

That record must bind the exact Phase 565 eligibility record, Phase 563
review, Phase 561 quarantined candidate, Phase 559 capture, Phase 557 handoff
packet, Phase 555 manual handoff, and inherited Phase
553/551/549/547/545/543/541/535/533/531/529/527 digests.

## Future Independent-Reproduction Evidence Requirements

A future implementation may not classify a result as independently reproduced
unless all of the following are present:

1. A distinct operator identity from the local HSAI authoring process.
2. A signed or digest-bound operator statement naming the Phase 557 handoff
   packet and the exact command or procedure used.
3. A non-secret environment declaration with host class, toolchain version,
   solver/backend version, network policy, and timestamp.
4. A captured output summary whose digests match declared stdout, stderr,
   solver verdict, elapsed-time, and artifact-index fields.
5. A redaction report proving no secrets, credentials, raw provider bodies, or
   undeclared raw logs are retained.
6. A replay/correspondence statement showing the reproduced run targets the
   same source obligation and not a changed problem.
7. A quarantine/import candidate path through `zkbench_core` result-import
   primitives, not a direct accepted-evidence append.
8. Explicit nonclaims: not accepted evidence, not Level2+, not score-axis
   population, not formal proof, not semantic correctness, not production
   readiness, not SOTA, not full security, and not authority.

## Future Classifications

A future implementation may classify the requirement as:

- `IndependentReproductionEvidenceBlocked`;
- `IndependentReproductionEvidenceRejected`;
- `IndependentReproductionEvidenceCandidateQuarantined`;
- `IndependentReproductionEvidenceReadyForImportReview`.

The only classification justified by the current repository state is:

```text
IndependentReproductionEvidenceBlocked
```

## Fail-Closed Rules

A future implementation must fail closed if:

- the Phase 567 source record is not exact;
- the Phase 567 classification is not
  `AcceptedResultPolicyResolutionBlocked`;
- any Phase 565/563/561/559/557/555 or inherited digest binding drifts;
- the operator identity is missing or collapses into the local authoring
  process;
- the operator statement omits the Phase 557 packet binding;
- the captured output is missing digest sidecars;
- raw stdout, raw stderr, raw provider bodies, credentials, secrets, or
  undeclared files are retained;
- the result tries to bypass `zkbench_core` import/review ownership;
- any accepted Evidence Ledger mutation is requested;
- any Level2 or score-axis claim is requested;
- any proof/checker/solver artifact is promoted as accepted formal evidence;
- any SOTA, full-security, semantic-correctness, production-readiness,
  benchmark, external-audit, or authority claim appears.

## Forbidden In This Phase

Phase 568 does not permit:

- Rust implementation code;
- Cargo metadata changes;
- new dependencies;
- binaries or scripts;
- filesystem artifact writes;
- external-result artifact writes;
- accepted-evidence artifact writes;
- accepted Evidence Ledger mutation;
- external replay execution;
- backend execution;
- Lean, SMT/Z3, COBALT, Rust-to-Lean, Aeneas, Hax, Coq, TLA+, CBMC, or
  model-checker execution;
- proof artifact generation or promotion;
- checker transcript generation or promotion;
- solver certificate generation or promotion;
- accepted external result evidence;
- accepted independent external reproduction;
- accepted formal evidence;
- Level2+ evidence;
- score-axis population;
- benchmark submission;
- production deployment;
- external-audit claims;
- semantic-correctness claims;
- production-readiness claims;
- SOTA or breakthrough claims;
- full-security claims;
- authority to execute an action.

## Future Implementation Exit Criteria

A future Phase 569 may implement local independent-reproduction requirement
metadata only if it:

- accepts exactly one Phase 567 policy-resolution metadata record;
- validates all Phase 567, Phase 565, Phase 563, Phase 561, Phase 559, Phase
  557, Phase 555, and inherited digest bindings;
- records `IndependentReproductionEvidenceBlocked` under the current evidence
  state;
- includes explicit placeholders for the required future operator identity,
  operator statement, environment declaration, captured output summary,
  redaction report, replay/correspondence statement, and import ownership
  checks;
- rejects accepted-ledger mutation, Level2, score-axis population,
  proof/checker/solver promotion, backend execution evidence, benchmark
  evidence, external-audit evidence, strong public claims, and authority;
- produces no artifact files and mutates no accepted Evidence Ledger;
- adds focused tests for successful blocked requirement metadata, Phase 567
  drift rejection, and promotion rejection.

## Meaning

Phase 568 moves the path forward by naming the independent-reproduction
evidence requirements. It still does not make independent external
reproduction true.

The correct statement is:

```text
HSAI has a local accepted-result policy-resolution path and a documented
independent-reproduction evidence requirement boundary.
```

It does not justify:

```text
HSAI accepted external result evidence.
HSAI has accepted independent external reproduction.
HSAI has Level2+ evidence.
HSAI has accepted formal evidence.
HSAI is SOTA.
HSAI is fully secure.
HSAI proves semantic correctness.
HSAI is production ready.
```
