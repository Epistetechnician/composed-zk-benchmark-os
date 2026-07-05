# Phase 590 HSAI Tiny Z3 Backend Execution Packet Role Artifact Independent Operator Materialization Boundary

State slice: `Phase 590 HSAI tiny Z3 backend execution packet role artifact independent-operator materialization boundary`.

Phase 590 defines the docs-first boundary for future materialization of the
packet-role artifact independent-operator evidence packet roles named by Phase
589. It does not materialize any packet role, import external results, accept
independent external reproduction, mutate accepted evidence, create Level2+
evidence, populate score axes, or advance any public claim.

## Current Input

The only allowed source is one exact Phase 589 packet-role artifact
independent-operator evidence packet metadata record with classification:

```text
PacketRoleArtifactIndependentOperatorEvidencePacketMissing
```

That record must bind the exact Phase 587 requirement metadata record, Phase
585 policy-resolution metadata, Phase 583 accepted-result eligibility
metadata, Phase 581 import review, Phase 579 quarantined packet-role artifact
import candidate, Phase 577 readback, Phase 575 output metadata, Phase 573
materialization metadata, Phase 571 packet metadata, Phase 569 requirement
metadata, Phase 567 policy-resolution metadata, Phase 565 eligibility
metadata, Phase 563 review, Phase 561 candidate, Phase 559 capture, Phase 557
handoff packet, Phase 555 manual handoff, and inherited backend-execution
digests.

## Future Materialized Role Set

A future implementation may materialize a packet role set only under a
caller-selected output root outside protected repository roots. The declared
logical files must be:

- `packet-role-artifact-independent-operator-packet/operator-identity.json`;
- `packet-role-artifact-independent-operator-packet/operator-statement.json`;
- `packet-role-artifact-independent-operator-packet/environment-declaration.json`;
- `packet-role-artifact-independent-operator-packet/captured-output-summary.json`;
- `packet-role-artifact-independent-operator-packet/redaction-report.json`;
- `packet-role-artifact-independent-operator-packet/replay-correspondence.json`;
- `packet-role-artifact-independent-operator-packet/import-ownership.json`;
- `packet-role-artifact-independent-operator-packet/manifest.json`;
- one `.sha256` sidecar for each declared JSON file.

No raw stdout, raw stderr, raw provider response, credentials, secrets,
operator-private material, undeclared logs, or undeclared files may be written.

## Future Role Content Constraints

A future implementation must require:

- `operator-identity.json`: stable independent operator id, statement digest,
  and explicit non-local-authoring declaration;
- `operator-statement.json`: Phase 577 packet-role artifact bundle digest,
  Phase 557 handoff packet digest, command or procedure digest, timestamp, and
  nonclaim-set digest;
- `environment-declaration.json`: host class, operating system,
  solver/backend version, toolchain version, network policy,
  working-directory policy, clock source declaration, and timestamp;
- `captured-output-summary.json`: digest-only stdout/stderr summaries, solver
  verdict, elapsed-time class, return status, artifact-index references, and
  packet-role readback digests;
- `redaction-report.json`: confirmation that forbidden raw data, private
  operator material, and secrets are absent;
- `replay-correspondence.json`: source obligation digest, Phase 577 artifact
  bundle digest, Phase 557 handoff packet digest, command descriptor digest,
  packet digest, expected-result digest, and correspondence statement;
- `import-ownership.json`: declaration that any future result import must pass
  through `zkbench_core` candidate, quarantine, review, owner-decision,
  Level2, and score-axis gates.

## Future Filesystem Rules

A future implementation must:

- reject empty output roots;
- reject repository roots and explicitly protected roots;
- reject symlinked output roots;
- reject path traversal;
- write only declared logical files and sidecars;
- use staged writes before final placement;
- require explicit overwrite mode;
- reject partial bundles;
- reject undeclared files on readback;
- reject stale sidecar digests;
- reject raw-response retention;
- produce a deterministic manifest digest over file roles and sidecars.

## Future Classifications

A future implementation may classify materialization as:

- `PacketRoleArtifactIndependentOperatorMaterializationMissing`;
- `PacketRoleArtifactIndependentOperatorMaterializationRejected`;
- `PacketRoleArtifactIndependentOperatorMaterializationQuarantinedLocalFiles`;
- `PacketRoleArtifactIndependentOperatorMaterializationReadyForImportCandidateBoundary`.

The only classification justified by the current repository state is:

```text
PacketRoleArtifactIndependentOperatorMaterializationMissing
```

## Fail-Closed Rules

A future implementation must fail closed if:

- the Phase 589 source record is not exact;
- the Phase 589 classification is not
  `PacketRoleArtifactIndependentOperatorEvidencePacketMissing`;
- any Phase 587/585/583/581/579/577/575/573/571/569/567/565/563/561/559/557
  /555 or inherited backend-execution digest binding drifts;
- any declared logical file is missing;
- any sidecar digest is missing or stale;
- any role content omits its required binding;
- the output root is protected, symlinked, or traverses upward;
- undeclared files are present;
- raw stdout, raw stderr, raw provider responses, credentials, secrets,
  operator-private material, or undeclared logs are retained;
- the materialized roles request result import, accepted evidence, accepted
  independent reproduction, Level2, score-axis population,
  proof/checker/solver promotion, backend execution evidence, benchmark
  evidence, external audit evidence, public SOTA/full-security
  /semantic-correctness/production-readiness claims, or authority.

## Forbidden In This Phase

Phase 590 does not permit:

- Rust implementation code;
- Cargo metadata changes;
- new dependencies;
- binaries or scripts;
- packet role materialization;
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

## Future Phase 591 Exit Criteria

A future Phase 591 may implement local packet-role artifact materialization
metadata only if it:

- accepts exactly one Phase 589 packet metadata record;
- validates all Phase 589, Phase 587, Phase 585, Phase 583, Phase 581, Phase
  579, Phase 577, Phase 575, Phase 573, Phase 571, Phase 569, Phase 567,
  Phase 565, Phase 563, Phase 561, Phase 559, Phase 557, Phase 555, and
  inherited backend-execution digest bindings;
- records `PacketRoleArtifactIndependentOperatorMaterializationMissing` under
  the current evidence state;
- defines declared role files, sidecars, manifest shape, output-root policy,
  readback validation, and digest helpers without writing files;
- keeps all file-written flags false under the current state;
- rejects accepted-ledger mutation, external-result import, accepted
  independent reproduction, Level2, score-axis population, proof/checker/solver
  promotion, backend execution evidence, benchmark evidence, external-audit
  evidence, strong public claims, and authority;
- adds focused tests for successful missing-materialization metadata, Phase
  589 drift rejection, declared-role digest drift, output-root policy drift,
  and promotion rejection.

## Meaning

Phase 590 moves the path forward by defining how Phase 589 packet roles may
later be represented as non-secret local artifacts. It still does not create
those artifacts and does not make independent external reproduction true.

The correct statement is:

```text
HSAI has local packet-role independent-operator evidence packet metadata and a
documented packet-role artifact materialization boundary.
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
