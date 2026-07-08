# Phase 629 HSAI Tiny Z3 Packet Role Artifact Independent Operator Accepted Result Independent Reproduction Requirement Boundary

State slice: `Phase 629 HSAI tiny Z3 packet-role artifact independent-operator accepted-result independent-reproduction requirement boundary`.

Phase 629 defines the docs-first boundary for the independent-reproduction
requirement that remains after Phase 628 policy-resolution metadata. It does
not create independent reproduction, import an external result, mutate the
accepted Evidence Ledger, or advance the evidence class.

## Current Input

The only allowed source is one exact Phase 628 policy-resolution metadata record
with classification:

```text
PacketRoleArtifactIndependentOperatorAcceptedResultPolicyResolutionBlocked
```

That record must bind:

- Phase 628 policy-resolution input, digest-map, id-map, label-map, blocker,
  policy, nonpromotion, rule, forbidden-API, and inherited-digest digests;
- Phase 601 eligibility input, digest-map, id-map, label-map, blocker, policy,
  and nonpromotion digests;
- Phase 599 import-review digest, input digest, blocker digest, policy digest,
  and nonpromotion digest;
- Phase 597 import-candidate, candidate, validation, validation-issue, and
  quarantine-record digests;
- exact Phase 597 candidate status `ExternalResultStatus::Quarantined`;
- exact Phase 597 requested boundary `ClaimBoundary::Level0DesignNote`;
- exact Phase 595 manifest, readback, readback-file-map, and request digests;
- direct Phase 593/591/589/587/585 digests;
- inherited Phase 583/581/579/577/575/573/571/569/567/565/563/561/559/557/555
  and backend-execution requirements.

If any binding drifts, a future implementation must fail closed.

## Future Independent-Reproduction Requirement

A future implementation may not classify the Phase 628 blocker as satisfied
unless it has non-secret, digest-bound materials for all of the following:

1. A distinct independent operator identity, separate from the local authoring
   process and local packet producer.
2. An operator statement binding the Phase 628 record, the Phase 595 bundle,
   and the exact replay procedure.
3. A non-secret environment declaration naming host class, operating system,
   solver/backend version, toolchain version, timestamp, and network policy.
4. A captured-output summary with declared stdout/stderr digests, solver
   verdict, elapsed-time observation, and artifact index.
5. A redaction report proving no secrets, credentials, raw provider bodies, or
   undeclared logs are retained.
6. A replay/correspondence statement showing the independent operator targeted
   the same packet-role artifact obligation and not a modified problem.
7. An import-ownership binding showing any later external-result import routes
   through the existing `zkbench_core` import/review owner and not through a
   direct HSAI append path.
8. Explicit nonclaims preserving no accepted evidence, no accepted independent
   external reproduction, no accepted formal evidence, no Level2+ evidence, no
   score-axis population, no proof, no semantic-correctness claim, no
   production-readiness claim, no SOTA claim, no full-security claim, and no
   action authority.

## Future Classifications

A future implementation may classify the requirement as:

- `PacketRoleArtifactIndependentOperatorAcceptedResultIndependentReproductionEvidenceBlocked`;
- `PacketRoleArtifactIndependentOperatorAcceptedResultIndependentReproductionEvidenceRejected`;
- `PacketRoleArtifactIndependentOperatorAcceptedResultIndependentReproductionEvidenceCandidateQuarantined`;
- `PacketRoleArtifactIndependentOperatorAcceptedResultIndependentReproductionEvidenceReadyForImportReview`.

The only classification justified by the current repository state is:

```text
PacketRoleArtifactIndependentOperatorAcceptedResultIndependentReproductionEvidenceBlocked
```

## Fail-Closed Rules

A future implementation must fail closed if:

- the Phase 628 source record is not exact;
- the Phase 628 classification is not
  `PacketRoleArtifactIndependentOperatorAcceptedResultPolicyResolutionBlocked`;
- the Phase 628 promotion state is not
  `packet_role_artifact_independent_operator_accepted_result_policy_resolution_metadata`;
- the Phase 628 next-required state is not
  `independent_external_reproduction_still_required`;
- any Phase 601/599/597/595/593/591/589/587/585 or inherited digest binding
  drifts;
- the independent operator identity is absent or collapses into the local HSAI
  authoring process;
- the operator statement omits Phase 628 and Phase 595 bindings;
- captured output lacks digest sidecars;
- raw stdout, raw stderr, provider bodies, credentials, secrets, or undeclared
  files are retained;
- import ownership bypasses `zkbench_core`;
- any accepted Evidence Ledger mutation is requested;
- any Level2 or score-axis claim is requested;
- any proof/checker/solver artifact is promoted as accepted formal evidence;
- any Lean, additional SMT/Z3, COBALT, Rust-to-Lean, benchmark,
  external-audit, SOTA, full-security, semantic-correctness,
  production-readiness, breakthrough, or authority claim appears.

## Forbidden In This Phase

Phase 629 does not permit:

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

## Future Phase 630 Exit Criteria

A future Phase 630 may implement local independent-reproduction requirement
metadata only if it:

- accepts exactly one Phase 628 policy-resolution metadata record;
- validates all Phase 628/601/599/597/595/593/591/589/587/585 and inherited
  Phase 583/581/579/577/575/573/571/569/567/565/563/561/559/557/555 and
  backend-execution digest bindings;
- records
  `PacketRoleArtifactIndependentOperatorAcceptedResultIndependentReproductionEvidenceBlocked`
  under the current evidence state;
- includes deterministic required-future-evidence digest placeholders for
  independent operator identity, operator statement, environment declaration,
  captured-output summary, redaction report, replay/correspondence statement,
  and import ownership;
- rejects direct accepted-ledger mutation, external replay claims, Level2
  claims, score-axis population, proof/checker/solver promotion, backend
  execution evidence, benchmark evidence, external-audit evidence, strong
  public claims, and authority;
- produces no artifact files and mutates no accepted Evidence Ledger;
- adds focused tests for successful blocked requirement metadata, Phase 628
  drift rejection, inherited digest drift rejection, required-evidence digest
  drift rejection, and promotion rejection.

## Meaning

Phase 629 moves the path forward by naming the next exact evidence gate after
Phase 628 policy-resolution metadata. It still does not satisfy the gate.

The defensible statement after this phase is:

```text
HSAI has local blocked policy-resolution metadata and a documented
independent-reproduction requirement boundary for the packet-role artifact
independent-operator accepted-result path.
```

It does not justify:

```text
HSAI accepted external result evidence.
HSAI accepted independent external reproduction.
HSAI has Level2+ evidence.
HSAI populated score axes.
HSAI has accepted formal evidence.
HSAI ran Lean, COBALT, Rust-to-Lean, or another SMT/Z3 backend in this phase.
HSAI is SOTA.
HSAI is fully secure.
HSAI proves semantic correctness.
HSAI is production ready.
```
