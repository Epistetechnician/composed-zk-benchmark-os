# Phase 258 HSAI Gateway Structured Manifest Digest Binding Notes

Status: complete for local structured-manifest digest binding.

## Scope

Phase 258 adds a deterministic digest binding to the structured Phase 254
claim-packet manifest and upgrades the local checker to recompute and validate
that digest.

The manifest remains embedded in:

```text
docs/254-hsai-gateway-bridge-public-claim-packet.md
```

The checker remains:

```text
crates/zkbench-core/tests/gateway_claim_packet_reproduction.rs
```

## Digest Rule

The manifest carries:

```text
manifest_digest_sha256=9cec879e89def697a5fdbb07a5ea1885ea2e4ce330cc6e8c0ed91e69de793fa9
```

The digest is SHA-256 over the sorted `key=value` manifest lines, excluding the
`manifest_digest_sha256` line itself, with one newline after each included line.

## Implementation

The checker now:

- validates that the declared digest is 64 lowercase hex characters;
- recomputes the canonical digest;
- rejects digest mismatch;
- preserves contract-level drift checks by recomputing the digest in selected
  malformed in-memory examples;
- adds explicit digest-field and digest-content drift coverage.

No fixture files, ignored demo runs, provider calls, generated artifacts,
credentials, or ledger mutations are involved.

## Validation

```sh
cargo test -p zkbench-core --test gateway_claim_packet_reproduction --quiet
```

## Claim Boundary

This phase adds local manifest integrity binding. It does not strengthen the
public claim.

This phase does not claim:

- accepted evidence;
- final bridge acceptance;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- live provider evidence;
- live attestation capture;
- benchmark evidence;
- score-axis population;
- live gateway execution;
- live model behavior;
- verifier-agent runtime behavior;
- production readiness;
- semantic correctness;
- SOTA status;
- breakthrough status;
- full security;
- global software-agent uniqueness;
- any claim above `Attested`.

## Next Step

The next defensible bridge slice is a small digest-bound manifest reproduction
note for external sharing, still local, hermetic, metadata-only, and
non-promotional.
