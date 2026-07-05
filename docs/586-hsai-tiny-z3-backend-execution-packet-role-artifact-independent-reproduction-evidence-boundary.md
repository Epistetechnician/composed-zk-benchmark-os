# Phase 586 HSAI Tiny Z3 Backend Execution Packet Role Artifact Independent Reproduction Evidence Boundary

State slice: `Phase 586 HSAI tiny Z3 backend execution packet role artifact independent-external-reproduction evidence requirement boundary`.

Phase 586 defines the docs-first evidence requirement boundary for the
independent-external-reproduction blocker recorded by Phase 585. It does not
create independent external reproduction. It defines what a future record must
prove before the packet-role accepted-result policy path may advance.

## Current Input

The only allowed source is one exact Phase 585 policy-resolution metadata
record with classification:

```text
PacketRoleArtifactAcceptedResultPolicyResolutionBlocked
```

That record must bind:

- Phase 585 policy-resolution input, policy, blocker, and nonpromotion
  digests;
- Phase 583 eligibility digest, input digest, digest-map digest, id-map
  digest, label-map digest, blocker digest, policy digest, and nonpromotion
  digest;
- Phase 581 import-review digest, input digest, classification, blocker
  digest, policy digest, and nonpromotion digest;
- Phase 579 import-candidate, candidate, validation, validation-issue, and
  quarantine-record digests;
- exact Phase 579 candidate status `ExternalResultStatus::Quarantined`;
- exact Phase 579 requested boundary `ClaimBoundary::Level0DesignNote`;
- Phase 577 manifest, readback, readback-file-map, and request digests;
- Phase 575 output, output-input, policy, nonpromotion, and request digests;
- Phase 573 materialization, declared-role, and declared-sidecar digests;
- Phase 571 packet, Phase 569 requirement, Phase 567 resolution, Phase 565
  eligibility, Phase 563 review, Phase 561 candidate, Phase 559 capture, Phase
  557 packet, and Phase 555 manual-handoff digests;
- inherited backend-execution digests from Phase 553/551/549/547/545/543/541
  /535/533/531/529/527.

If any of those bindings drift, a future independent-reproduction
implementation must fail closed.

## Future Independent-Reproduction Evidence Requirements

A future implementation may not classify a packet-role result as independently
reproduced unless all of the following are present:

1. A distinct operator identity from the local HSAI authoring process.
2. A signed or digest-bound operator statement naming the Phase 577 packet-role
   artifact bundle, the Phase 557 handoff packet, and the exact command or
   procedure used.
3. A non-secret environment declaration with host class, toolchain version,
   solver/backend version, network policy, working-directory policy, and
   timestamp.
4. A captured output summary whose digests match declared stdout, stderr,
   solver verdict, elapsed-time, artifact index, and packet-role readback
   fields.
5. A redaction report proving no secrets, credentials, raw provider bodies,
   undeclared raw logs, or operator-private material are retained.
6. A replay/correspondence statement showing the reproduced run targets the
   same source obligation, same packet-role artifact bundle, and same
   eligibility/policy-resolution chain, not a changed problem.
7. A quarantine/import candidate path through `zkbench_core` result-import
   primitives, not a direct accepted-evidence append.
8. Explicit nonclaims: not accepted evidence, not Level2+, not score-axis
   population, not accepted formal proof, not semantic correctness, not
   production readiness, not SOTA, not full security, and not authority.

## Future Classifications

A future implementation may classify the requirement as:

- `PacketRoleArtifactIndependentReproductionEvidenceBlocked`;
- `PacketRoleArtifactIndependentReproductionEvidenceRejected`;
- `PacketRoleArtifactIndependentReproductionEvidenceCandidateQuarantined`;
- `PacketRoleArtifactIndependentReproductionEvidenceReadyForImportReview`.

The only classification justified by the current repository state is:

```text
PacketRoleArtifactIndependentReproductionEvidenceBlocked
```

## Fail-Closed Rules

A future implementation must fail closed if:

- the Phase 585 source record is not exact;
- the Phase 585 classification is not
  `PacketRoleArtifactAcceptedResultPolicyResolutionBlocked`;
- any Phase 583/581/579/577/575/573/571/569/567/565/563/561/559/557/555 or
  inherited backend-execution digest binding drifts;
- the operator identity is missing or collapses into the local authoring
  process;
- the operator statement omits the Phase 577 packet-role artifact bundle or
  Phase 557 handoff packet binding;
- the captured output is missing digest sidecars;
- raw stdout, raw stderr, raw provider bodies, credentials, secrets, operator
  private keys, or undeclared files are retained;
- the result tries to bypass `zkbench_core` import/review ownership;
- any accepted Evidence Ledger mutation is requested;
- any Level2 or score-axis claim is requested;
- any proof/checker/solver artifact is promoted as accepted formal evidence;
- any SOTA, full-security, semantic-correctness, production-readiness,
  benchmark, external-audit, or authority claim appears.

## Forbidden In This Phase

Phase 586 does not permit:

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

## Future Phase 587 Exit Criteria

A future Phase 587 may implement local independent-reproduction requirement
metadata only if it:

- accepts exactly one Phase 585 policy-resolution metadata record;
- validates all Phase 585, Phase 583, Phase 581, Phase 579, Phase 577, Phase
  575, Phase 573, Phase 571, Phase 569, Phase 567, Phase 565, Phase 563,
  Phase 561, Phase 559, Phase 557, Phase 555, and inherited backend-execution
  digest bindings;
- records `PacketRoleArtifactIndependentReproductionEvidenceBlocked` under the
  current evidence state;
- includes explicit placeholders for the required future operator identity,
  operator statement, environment declaration, captured output summary,
  redaction report, replay/correspondence statement, and import ownership
  checks;
- rejects accepted-ledger mutation, Level2, score-axis population,
  proof/checker/solver promotion, backend execution evidence, benchmark
  evidence, external-audit evidence, strong public claims, and authority;
- produces no artifact files and mutates no accepted Evidence Ledger;
- adds focused tests for successful blocked requirement metadata, Phase 585
  drift rejection, inherited Phase 583/581 digest drift rejection, required
  evidence digest drift rejection, and promotion rejection.

## Meaning

Phase 586 moves the path forward by naming the packet-role independent
reproduction evidence requirements. It still does not make independent external
reproduction true.

The correct statement is:

```text
HSAI has local packet-role accepted-result policy-resolution metadata and a
documented independent-reproduction evidence requirement boundary.
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
