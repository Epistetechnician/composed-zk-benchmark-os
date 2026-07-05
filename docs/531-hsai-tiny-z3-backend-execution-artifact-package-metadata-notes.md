# Phase 531 HSAI Tiny Z3 Backend Execution Artifact Package Metadata Notes

State slice: `Phase 531 HSAI tiny Z3 backend execution artifact package metadata`.

Phase 531 implements the local package metadata path authorized by
`docs/530-hsai-tiny-z3-backend-execution-artifact-package-boundary.md`:

```text
Phase 529 local hermetic backend execution result
  + explicit local artifact package policy
  -> local backend execution artifact package metadata
```

This phase packages one Phase 529 local SMT/Z3 backend execution observation
as non-accepted local backend-execution metadata. It does not write package
files, mutate accepted evidence, create Level2+ evidence, populate score axes,
or promote formal proof authority.

## Implemented Surface

Phase 531 adds the local Rust metadata model under
`crates/hsai-agent-admission/src/lib.rs`:

- `GatewayFormalTinyZ3BackendExecutionArtifactPackageInput`;
- `GatewayFormalTinyZ3BackendExecutionArtifactPackage`;
- `GatewayFormalTinyZ3BackendExecutionArtifactPackageClassification`;
- `GatewayFormalTinyZ3BackendExecutionArtifactPackageLabel`;
- `GatewayFormalTinyZ3BackendExecutionArtifactPackageIssue`;
- `GatewayFormalTinyZ3BackendExecutionArtifactPackageValidation`;
- deterministic package nonclaim, cap, rule, forbidden-API, inherited-digest,
  digest-binding, id-binding, label-binding, and policy-digest helpers;
- `validate_gateway_formal_tiny_z3_backend_execution_artifact_package_input`;
- `build_gateway_formal_tiny_z3_backend_execution_artifact_package`.

The valid classification is:

```text
BackendExecutionPackagedLocalOnly
```

The package binds:

- the Phase 529 result digest;
- the Phase 529 request digest;
- the Phase 529 candidate digest and candidate input digest;
- Phase 529 lane `LaneAScopedSmtZ3Replay`;
- Phase 529 classification `LaneASmtZ3RunObservedLocalOnly`;
- Phase 527 classification `LaneAExecutionCandidateDeclaredNoRun`;
- the Phase 527 obligation, toolchain, command, expected-output grammar,
  timeout, and scratch-output-root policy digests;
- the actual SMT-LIB2 text digest;
- the executable digest;
- the fixed argv digest;
- the working-directory, environment, and timeout policy digests;
- the exit-code label;
- redacted stdout and stderr summary digests;
- the output-classification digest;
- the parsed solver verdict label;
- package policy, nonclaim, cap, rule, forbidden-API, and inherited-digest
  hashes.

## Guardrails

Phase 531 fails closed if the Phase 529 result is not exact, if it is not a
local observed Lane A SMT/Z3 run, if `process_spawned` or `backend_executed`
is false, if the result timed out, if the exit label is not `exit_0`, if any
required digest is zero, if raw logs or repository-root writes are recorded, or
if the package tries to create accepted evidence, accepted formal evidence,
Level2+ evidence, score axes, proof/checker/solver artifacts, Lean evidence,
COBALT evidence, Rust-to-Lean evidence, benchmark evidence, external-audit
evidence, independent external reproduction, strong public claims, or action
authority.

## Evidence Meaning

Phase 531 supports this claim only:

```text
HSAI packages one local hermetic SMT/Z3 backend execution observation for
review as local backend-execution metadata.
```

The result is still not accepted evidence, not accepted formal evidence, not
Level2+ evidence, not score-axis evidence, not Lean proof, not COBALT
containment evidence, not Rust-to-Lean proof, not checker transcript authority,
not solver certificate authority, not benchmark evidence, not external audit,
not SOTA, not semantic correctness, not production readiness, not full
security, and not authority to execute an action.

## Tests

Focused tests cover:

- successful Phase 531 package metadata over a Phase 529-shaped local backend
  execution result;
- rejection when the Phase 529 result state is invalid;
- rejection of digest drift, package artifact writes, accepted-evidence
  mutation, Level2+, score-axis, Lean, COBALT, Rust-to-Lean, proof/checker/
  solver, benchmark, external-audit, strong-claim, independent-reproduction,
  and action-authority promotion attempts.

## Next Boundary

The next responsible boundary is a review boundary over Phase 531 package
metadata. It must remain non-accepted unless a later explicit owner decision
authorizes an accepted-evidence route for backend-execution package metadata.
