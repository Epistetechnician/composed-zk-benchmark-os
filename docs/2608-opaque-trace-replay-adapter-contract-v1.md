# OpaqueTraceReplay Adapter Contract v1

State slice: `research-synthesis-trace-replay-v1-benchmark-adapter-contract`

Status: `ImplementedPureDataContract`

Implementation surface:

- `crates/zkbench-core/src/adapters/opaque_trace_replay.rs`
- `crates/zkbench-core/tests/opaque_trace_replay.rs`
- `crates/zkbench-core/tests/repo_hygiene.rs` for the separate
  `research-synthesis-trace-replay-v1-repo-hygiene-venv-boundary` slice.

## Contract

The adapter contract defines the synthetic `OpaqueTraceReplay` family, ten
mutation variants, typed context binding, predecessor and sequence metadata,
mutation provenance, artifact digests, expected semantic verdicts, quarantine
statuses, adapter observations, and a fixed `Level0DesignNote` claim ceiling.

The semantic oracle owns expected verdicts. Adapter observations remain separate
from semantic verdicts and cannot grant authority. A result with
`authority_granted=true` is invalid. The contract retains no opaque payload,
trace text, credential, PII, or provider signature; injection and secret cases
use marker booleans and synthetic digests only.

## Variants

`valid_same_session`, `wrong_user_replay`, `wrong_session_replay`,
`wrong_model_replay`, `out_of_order_block`, `duplicate_block`,
`stale_or_revoked_block`, `hidden_injection`, `secret_bearing_transcript`, and
`malformed_envelope` are all represented as pure data. The expected verdict and
quarantine status are deterministic functions of the declared variant.

## Non-goals

This slice does not implement a provider API, model execution, cryptographic
verification of any external envelope, trace decoding, benchmark scoring,
production admission, Evidence Ledger append, or authority transition. It does
not establish HSAI security, provider vulnerability, faithful computation,
Astral evidence, Stage 0C, Stage 1, or any claim above `Level0DesignNote`.

## Validation

The focused test covers every variant, context discrimination, stale/revoked
handling, raw-payload retention rejection, claim-boundary escalation rejection,
digest binding, no-authority enforcement, and metadata-only serialization.
