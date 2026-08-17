# Fresh-Actor Custody Handoff V34

State slice: `astral-fresh-actor-custody-handoff-v34`

Status: `LocalContractValidated / ExecutionNotAuthorized`

## Purpose

V33 stopped because no non-reserved actor with a validated per-layer
intervention surface and complete custody packet was available. V34 makes that
handoff boundary executable without treating a metadata packet as model
execution or scientific evidence.

The contract is implemented in
`crates/zkbench-core/src/external_runner/actor_custody.rs` and exercised by
`crates/zkbench-core/tests/astral_fresh_actor_custody_handoff_v34.rs`.

## Required typed fields

Every prospective handoff must bind:

- a fresh actor identifier and actor/checkpoint digest;
- source/archive digest;
- runtime digest;
- launcher-byte digest and launcher-argument-plan digest;
- frozen split-manifest digest;
- validator identity;
- planned artifact-root digest;
- the V34 state slice and `Level0DesignNote` ceiling;
- explicit custody completeness and closed assessment status.

The schema denies unknown fields. Raw traces, credentials, PII, opaque
signatures, and untyped provider artifacts are not accepted fields or retained
payloads.

## Fail-closed rules

Validation rejects:

1. missing identifiers or validator identity;
2. a state-slice mismatch;
3. reserved actor identities `V22`, `V23`, `V24`, or `V25`;
4. any digest that is not a non-empty-payload, lowercase SHA-256 digest;
5. incomplete custody metadata;
6. an opened assessment;
7. any claim boundary above `Level0DesignNote`;
8. any forbidden-material marker; and
9. unknown serialized fields such as `raw_trace` or `credential`.

## Claim boundary

This contract establishes only that a typed synthetic handoff is accepted or
rejected by local validation. It does not establish source authenticity,
runtime authenticity, model behavior, telemetry parity, intervention effects,
privacy safety, provider security, or Astral introspection. It does not create
custody, open an assessment, load a model, or authorize V33/V26 execution.

## Advancement gate

A future execution authorization requires a separately reviewed handoff with a
fresh actor, independently checked source/runtime/launcher custody, a frozen
split manifest, an identified validator, and an external artifact root. The
V34 validator is a necessary preflight, not sufficient authorization.
