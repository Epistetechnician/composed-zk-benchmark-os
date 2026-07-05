# Phase 588 HSAI Tiny Z3 Backend Execution Packet Role Artifact Independent Operator Evidence Packet Boundary

State slice: `Phase 588 HSAI tiny Z3 backend execution packet role artifact independent-operator evidence packet boundary`.

Phase 588 defines the docs-first packet boundary for the independent-operator
evidence materials required by Phase 587. It does not create a packet, import
external results, accept independent external reproduction, mutate accepted
evidence, create Level2+ evidence, populate score axes, or advance any public
claim.

## Current Input

The only allowed source is one exact Phase 587 independent-reproduction
requirement metadata record with classification:

```text
PacketRoleArtifactIndependentReproductionEvidenceBlocked
```

That record must bind the exact Phase 585 policy-resolution metadata record,
Phase 583 accepted-result eligibility metadata, Phase 581 import review, Phase
579 quarantined packet-role artifact import candidate, Phase 577 readback,
Phase 575 output metadata, Phase 573 materialization metadata, Phase 571
packet metadata, Phase 569 requirement metadata, Phase 567 policy-resolution
metadata, Phase 565 eligibility metadata, Phase 563 review, Phase 561
candidate, Phase 559 capture, Phase 557 handoff packet, Phase 555 manual
handoff, and inherited backend-execution digests.

## Future Packet Roles

A future implementation may define a local packet only if it is composed of
non-secret, digest-bound records:

1. `operator_identity`: a stable independent operator identifier, distinct
   from the local HSAI authoring process and bound to the operator statement.
2. `operator_statement`: a signed or digest-bound declaration naming the exact
   Phase 577 packet-role artifact bundle, Phase 557 handoff packet, command or
   procedure, timestamp, and nonclaim set.
3. `environment_declaration`: host class, operating system, solver/backend
   version, toolchain version, network policy, working-directory policy, clock
   source declaration, and timestamp.
4. `captured_output_summary`: digest-only stdout/stderr summary, solver
   verdict, elapsed-time class, return status, artifact-index references, and
   packet-role readback digests.
5. `redaction_report`: proof that no secrets, credentials, raw provider
   bodies, undeclared raw logs, operator-private keys, or environment secrets
   are retained.
6. `replay_correspondence`: binding from the reproduced run to the same source
   obligation, Phase 577 artifact bundle, Phase 557 handoff packet, packet
   digest, eligibility/policy-resolution chain, and expected solver result.
7. `import_ownership`: statement that any future result import must pass
   through `zkbench_core` candidate, quarantine, review, owner-decision,
   Level2, and score-axis gates instead of appending accepted evidence.

## Future Packet Digests

A future packet record must expose deterministic digests for:

- the complete packet;
- every packet role;
- the packet role manifest;
- Phase 587 source requirement metadata;
- Phase 585/583/581/579/577/575/573/571/569/567/565/563/561/559/557/555
  source bindings;
- inherited backend-execution source bindings;
- the explicit nonclaim set;
- the redaction report;
- the replay/correspondence statement;
- the import-ownership declaration.

Digest drift must invalidate the packet.

## Future Packet Classifications

A future implementation may classify a packet as:

- `PacketRoleArtifactIndependentOperatorEvidencePacketMissing`;
- `PacketRoleArtifactIndependentOperatorEvidencePacketRejected`;
- `PacketRoleArtifactIndependentOperatorEvidencePacketQuarantined`;
- `PacketRoleArtifactIndependentOperatorEvidencePacketReadyForImportCandidate`.

The only classification justified by the current repository state is:

```text
PacketRoleArtifactIndependentOperatorEvidencePacketMissing
```

## Fail-Closed Rules

A future implementation must fail closed if:

- the Phase 587 source record is not exact;
- the Phase 587 classification is not
  `PacketRoleArtifactIndependentReproductionEvidenceBlocked`;
- any Phase 585/583/581/579/577/575/573/571/569/567/565/563/561/559/557/555
  or inherited backend-execution digest binding drifts;
- any packet role is missing;
- any packet role is not digest-bound;
- the operator identity is local, ambiguous, or not bound to the statement;
- the operator statement does not name the exact Phase 577 packet-role artifact
  bundle and Phase 557 handoff packet;
- the environment declaration omits toolchain, solver/backend version, network
  policy, working-directory policy, or timestamp;
- captured output contains raw stdout, raw stderr, credentials, secrets, raw
  provider bodies, operator-private material, or undeclared logs;
- the redaction report is missing or conflicts with the captured-output
  summary;
- replay/correspondence targets a different obligation, artifact bundle,
  command, source digest, eligibility/policy chain, or expected result;
- import ownership bypasses `zkbench_core`;
- accepted Evidence Ledger mutation is requested;
- Level2, score-axis, proof/checker/solver, benchmark, external-audit, SOTA,
  full-security, semantic-correctness, production-readiness, breakthrough, or
  authority claims are requested.

## Forbidden In This Phase

Phase 588 does not permit:

- Rust implementation code;
- Cargo metadata changes;
- new dependencies;
- binaries or scripts;
- packet materialization;
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

## Future Phase 589 Exit Criteria

A future Phase 589 may implement local packet metadata only if it:

- accepts exactly one Phase 587 requirement metadata record;
- validates all Phase 587, Phase 585, Phase 583, Phase 581, Phase 579, Phase
  577, Phase 575, Phase 573, Phase 571, Phase 569, Phase 567, Phase 565,
  Phase 563, Phase 561, Phase 559, Phase 557, Phase 555, and inherited
  backend-execution digest bindings;
- records `PacketRoleArtifactIndependentOperatorEvidencePacketMissing` under
  the current evidence state;
- defines packet-role data structures and deterministic digest helpers without
  materializing files;
- requires all role-presence flags to remain false under the current state;
- rejects accepted-ledger mutation, external-result import, accepted
  independent reproduction, Level2, score-axis population, proof/checker/solver
  promotion, backend execution evidence, benchmark evidence, external-audit
  evidence, strong public claims, and authority;
- produces no artifact files and mutates no accepted Evidence Ledger;
- adds focused tests for successful missing-packet metadata, Phase 587 drift
  rejection, packet-role drift rejection, and promotion rejection.

## Meaning

Phase 588 moves the path forward by naming the packet-role independent-operator
evidence packet shape needed before the packet-role artifact path can advance.
It still does not make independent external reproduction true.

The correct statement is:

```text
HSAI has local packet-role independent-reproduction requirement metadata and a
documented packet-role independent-operator evidence packet boundary.
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
