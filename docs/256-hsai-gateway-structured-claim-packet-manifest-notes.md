# Phase 256 HSAI Gateway Structured Claim-Packet Manifest Notes

Status: complete for structured local claim-packet manifest checking.

## Scope

Phase 256 adds a parser-backed manifest block to the Phase 254 public claim
packet and upgrades the Phase 255 reproduction checker to validate that
manifest as structured data.

The manifest is embedded in:

```text
docs/254-hsai-gateway-bridge-public-claim-packet.md
```

The checker remains:

```text
crates/zkbench-core/tests/gateway_claim_packet_reproduction.rs
```

## Manifest Format

The manifest is a fenced `claim-packet-manifest-v1` block using repeated
`key=value` lines. The local test parses the block with standard library code
and validates:

- packet id;
- packet path;
- base commit;
- top commit label;
- covered phases;
- claim level;
- maximum claim maturity;
- ignored demo root and ignored status;
- declared `gateway-acceptance-preview/*` files;
- candidate-only and non-mutating summary flags;
- Phase 253 commands;
- packet-validation commands;
- explicit nonclaims;
- "do not use" phrases.

## Implementation

The checker now parses the manifest and validates singleton fields plus
repeated-value fields. It still reads only committed repository files and
`.gitignore`.

## Validation

```sh
cargo test -p zkbench-core --test gateway_claim_packet_reproduction --quiet
```

## Claim Boundary

This phase makes the Phase 254 packet more machine-checkable. It does not
strengthen the public claim.

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

The next defensible bridge slice is to add manifest drift tests that reject
specific malformed manifest examples without executing the ignored demo or
creating artifacts.
