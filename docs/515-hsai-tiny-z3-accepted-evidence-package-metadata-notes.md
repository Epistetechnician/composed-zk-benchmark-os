# Phase 515 HSAI Tiny Z3 Accepted Evidence Package Metadata Notes

State slice: `Phase 515 HSAI tiny Z3 accepted evidence package metadata`.

Phase 515 implements the local accepted-evidence package metadata path
authorized by
`docs/514-hsai-tiny-z3-accepted-evidence-package-boundary.md`:

```text
Phase 513 materialized accepted append metadata
  + explicit local evidence package policy
  -> local Level1LocalReplay package metadata
```

This phase is pure metadata. It does not write package artifact files, add a
new dependency, add a binary, add a script, spawn a process, call the network,
run a solver, run a proof assistant, run a benchmark, populate score axes, or
create proof/checker/solver artifacts.

## Implemented Surface

Phase 515 adds the local Rust metadata model under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyZ3AcceptedEvidencePackageInput`;
- `GatewayFormalTinyZ3AcceptedEvidencePackage`;
- `GatewayFormalTinyZ3AcceptedEvidencePackageIssue`;
- `GatewayFormalTinyZ3AcceptedEvidencePackageValidation`;
- deterministic nonclaim, cap, rule, forbidden-API, inherited-digest,
  package-policy, digest-binding, id-binding, and label-binding helpers;
- `validate_gateway_formal_tiny_z3_accepted_evidence_package_input`;
- `build_gateway_formal_tiny_z3_accepted_evidence_package`.

The builder validates one exact Phase 513 materialized append metadata record,
then records local package metadata only. It binds:

- the Phase 513 materialization digest and input digest;
- the Phase 513 digest, id, and label binding map digests;
- the Phase 513 explicit nonclaim, materialization-rule, forbidden-API, and
  inherited-digest digests;
- the Phase 513 Phase 511 mutation digest;
- the Phase 513 ledger path identity digest;
- the Phase 513 ledger path policy digest;
- the Phase 513 materialized append report digest;
- the Phase 513 materialized ledger artifact digest;
- the Phase 513 materialized ledger artifact byte length;
- the Phase 511 appended evidence class;
- the Phase 511 appended claim boundary;
- the package policy digest;
- the package nonclaim digest;
- the package cap digest.

## Guardrails

Phase 515 fails closed if the Phase 513 materialized append metadata state is
not exact, if Phase 513 did not route through the `zkbench-core` materialized
owner, if Phase 513 did not create materialized accepted ledger output, if the
materialized ledger artifact digest is zero, if the materialized ledger artifact
byte length is zero, if the appended evidence class is not `LocalReplay`, if
the appended claim boundary is not `Level1LocalReplay`, or if package policy,
nonclaim, rule, forbidden-API, inherited-digest, or cap bindings drift.

It also rejects package artifact writes, accepted formal evidence, Level2+
evidence, score axes, proof/checker/solver promotion, backend execution
evidence, benchmark evidence, external-audit evidence, semantic-correctness
claims, production-readiness claims, SOTA claims, breakthrough claims,
full-security claims, and action authority.

## Evidence Meaning

Phase 515 supports this claim only:

```text
HSAI packages one local Level1LocalReplay accepted-ledger artifact as scoped
local accepted evidence for a reviewed tiny-Z3 gateway path.
```

The result is still not accepted formal evidence, not Level2+ evidence, not
score-axis evidence, not Lean proof, not SMT proof authority, not COBALT
containment evidence, not Rust-to-Lean proof, not checker transcript authority,
not solver certificate authority, not benchmark evidence, not external audit,
not SOTA, not semantic correctness, not production readiness, not full
security, and not authority to execute an action.

## Tests

Focused tests cover:

- successful Phase 515 local package metadata over a real Phase 513
  materialized append metadata record;
- rejection when the Phase 513 materialization state is invalid;
- rejection of package artifact writes, formal-evidence, Level2+, score-axis,
  proof/checker/solver, backend, benchmark, external-audit, strong-claim, and
  action-authority promotion attempts.

The tests assert that the package remains `LocalReplay` /
`Level1LocalReplay`, binds package policy/nonclaim/cap digests, creates no
package artifact file, and creates no formal evidence, Level2+ evidence, score
axes, backend execution evidence, benchmark evidence, external audit evidence,
or action authority.

## Next Responsible Slice

The next responsible boundary is still not SOTA, full security, semantic
correctness, production readiness, Level2+, score axes, or backend proof
authority.

The next slice should define a score-axis boundary that explains exactly what
would be required before this local package could contribute to score axes.
That boundary must keep `LocalReplay` package evidence separate from Level2+
benchmark evidence and formal backend proof evidence.
