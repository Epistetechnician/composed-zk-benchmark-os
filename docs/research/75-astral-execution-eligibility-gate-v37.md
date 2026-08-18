# Astral Execution-Eligibility Gate V37

State slice: `astral-execution-eligibility-gate-v37`

Status: `LocalContractValidated / ExecutionNotAuthorized`

## Purpose

V37 composes the V36 replay manifest with the minimum declarations required
before a future Astral run could be considered by a separate human
authorization step.

The gate requires:

- a valid, non-empty V36 replay manifest and matching digest;
- a declared fresh, non-reserved actor;
- a declared per-layer intervention surface;
- recorded independent review;
- a reviewer identity;
- explicit nonclaim acknowledgement;
- a `Level0DesignNote` request ceiling;
- a closed assessment; and
- external execution still disabled.

The only positive result is `EligibleForSeparateHumanAuthorization`. The gate
cannot authorize, launch, or open an assessment.

## Claim boundary

The declarations are inputs to a local gate, not proof that an actor, runtime,
launcher, validator, reviewer, or instrument is authentic. V37 establishes
only fail-closed decision behavior over synthetic metadata. It does not
establish scientific validity, provider security, HSAI security, mechanistic
interpretability, or model introspection.

V25, V33, Stage 0C, Stage 1, and the repository claim ceiling remain unchanged.
