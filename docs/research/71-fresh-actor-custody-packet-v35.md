# Fresh-Actor Custody Packet V35

State slice: `astral-fresh-actor-custody-packet-v35`

Status: `LocalContractValidated / ExecutionNotAuthorized`

## Purpose

V34 validated one typed custody handoff. V35 makes the handoff transport
deterministic and replay-aware without turning it into an attestation or an
execution authorization.

The packet contains a fixed schema version, packet id, lowercase-hex nonce,
optional predecessor digest, the V34 handoff, and a SHA-256 packet digest. The
digest covers canonical compact JSON with the digest field set to null. This
avoids self-reference while binding every other packet field.

## Controls

- deterministic compact JSON serialization;
- exact schema-version matching;
- 64-character lowercase hexadecimal nonce validation;
- packet digest recomputation and comparison;
- unknown-field rejection through `serde(deny_unknown_fields)`;
- nonce uniqueness in a local replay guard; and
- predecessor-digest ordering in a local accepted sequence.

The replay guard is an in-memory local preflight. It is not a durable replay
database, cryptographic verifier, provider-bound channel, or distributed
consensus mechanism.

## Claim boundary

V35 establishes only local integrity and ordering behavior for synthetic typed
metadata. It does not authenticate source, runtime, launcher, validator, or
artifact roots; verify signatures; prove model identity; capture telemetry;
execute a model; or establish a security property for HSAI or a provider.
`Level0DesignNote` remains the maximum ceiling.

## Advancement gate

Any future real custody packet requires separate authorization, independently
verified artifact custody, durable replay-state ownership, and a review of the
trust model. Passing V35 is necessary transport hygiene only.
