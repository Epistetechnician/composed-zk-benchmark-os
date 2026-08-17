# Fresh-Actor Custody Replay Manifest V36

State slice: `astral-fresh-actor-custody-replay-manifest-v36`

Status: `LocalContractValidated / ExecutionNotAuthorized`

## Purpose

V36 turns the V35 in-memory replay guard into a serializable local manifest.
Accepted packets form a zero-based append-only chain with sequence numbers,
previous-entry digests, packet predecessor binding, and entry digests. The
manifest itself has a recomputable digest.

Packets that fail validation, repeat a nonce or packet id, or arrive with the
wrong predecessor are represented by typed quarantine records containing only
packet id, nonce, optional packet digest, and a fixed reason. Rejected packet
payloads are not retained.

## Controls

- fixed schema and state-slice binding;
- `Level0DesignNote` ceiling enforcement;
- accepted-entry sequence and previous-entry digest checks;
- packet predecessor and packet digest checks;
- duplicate nonce and packet-id rejection;
- canonical manifest serialization and digest verification;
- unknown-field rejection; and
- typed quarantine without raw rejected payload retention.

The manifest is a local serialized control artifact. It is not a distributed
replay service, cryptographic signature verifier, provider security result,
attestation, accepted Evidence Ledger record, or execution authorization.

## Claim boundary

V36 establishes only local append-only metadata and quarantine behavior over
synthetic packets. It does not authenticate any source, actor, runtime,
launcher, validator, artifact root, or provider channel. V25, V33, Stage 0C,
and Stage 1 remain unchanged.
