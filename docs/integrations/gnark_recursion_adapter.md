# gnark Recursion Adapter Plan

## Why Later Phase

gnark recursion is valuable after the Semantic IR, Oracle, Mutation Engine, Replay Manifest, Evidence Record, and Score Report exist. It should not be first because recursion proof is not semantic proof.

## Recursion Envelope Benchmark Role

The adapter will stress recursion envelopes:

- depth binding,
- proof aggregation shape,
- digest chaining,
- verifier-acceptance behavior,
- recursion tolerance metrics.

## Proof Aggregation Role

gnark can become a proof-envelope lane for aggregating claims such as "this candidate passed these checks." That envelope must bind artifacts and replay manifests by hash.

## Expected Metrics

- recursion depth,
- proof size,
- verifier latency,
- prover time,
- memory use,
- aggregation width,
- envelope verification status.

## Semantic Limitations

- Recursion proof is not semantic proof.
- Verifier acceptance does not prove the source spec is meaningful.
- A recursive proof can aggregate bad evidence if the Evidence Records are weak.

## Evidence Limitations

Claim boundary is capped by the weakest input evidence and the scope of the recursion statement. Recursion cannot promote Level 1 local replay into Level 5 semantic proof.

## Adapter Capability Flags

- supports_execution
- supports_proving
- supports_verification_timing
- supports_recursion
- supports_replay_manifest
- supports_artifact_hashing

## Anti-Goals

- Do not put Go recursion logic into the Rust core.
- Do not start with gnark before core semantics work.
- Do not treat recursion aggregation as full-system verification.
- Do not hide weak source evidence inside a recursive envelope.

