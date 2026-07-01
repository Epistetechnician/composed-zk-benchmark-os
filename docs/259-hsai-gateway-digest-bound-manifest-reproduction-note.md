# Phase 259 HSAI Gateway Digest-Bound Manifest Reproduction Note

Status: complete for bounded external-share reproduction wording.

## Purpose

This note gives a short, quotable reproduction statement for the Phase 254
public claim packet's structured manifest digest. It is meant to be shared
without promoting the local gateway bridge stack into accepted evidence, live
provider evidence, production readiness, SOTA status, or breakthrough status.

## Digest-Bound Packet

Packet:

```text
docs/254-hsai-gateway-bridge-public-claim-packet.md
```

Structured manifest digest:

```text
manifest_digest_sha256=9cec879e89def697a5fdbb07a5ea1885ea2e4ce330cc6e8c0ed91e69de793fa9
```

Digest rule:

```text
SHA-256 over sorted key=value manifest lines, excluding the
manifest_digest_sha256 line itself, with one newline after each included line.
```

Local checker:

```sh
cargo test -p zkbench-core --test gateway_claim_packet_reproduction --quiet
```

## Shareable Wording

Use:

```text
The HSAI gateway public claim packet includes a structured local manifest bound
by manifest_digest_sha256=9cec879e89def697a5fdbb07a5ea1885ea2e4ce330cc6e8c0ed91e69de793fa9.
The repository has a hermetic checker that recomputes that digest over the
manifest, validates the covered phases, commands, ignored-artifact boundary,
nonclaims, and forbidden public phrases, and rejects local manifest drift.
This is local metadata integrity evidence only; it is not accepted evidence,
live provider evidence, production readiness, SOTA status, or breakthrough
status.
```

Short version:

```text
HSAI's gateway claim packet has a local digest-bound manifest and a hermetic
checker for manifest drift. It proves packet integrity and claim-boundary
discipline only, not live execution or production readiness.
```

## Reproduction Checklist

1. Start from a clean checkout.
2. Confirm the packet contains the digest above.
3. Run:

```sh
cargo test -p zkbench-core --test gateway_claim_packet_reproduction --quiet
```

4. Confirm `.gateway-demo-runs/` remains ignored if local demo output exists:

```sh
git status --short --ignored .gateway-demo-runs
```

5. Keep generated output out of git.

## Explicit Nonclaims

This note does not claim:

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

The next bridge slices added a local public-packet index and a local index
checker that verifies the index against the packet, digest, checker command,
and nonclaims without creating generated artifacts or strengthening the public
claim.
