# Phase 260 HSAI Gateway Public Packet Index

Status: complete for a local latest-packet index.

## Latest Indexed Packet

Indexed commit:

```text
85a49f546935e5c237ff01811ea94fba38d5d0b5
```

Latest shareable packet:

```text
docs/254-hsai-gateway-bridge-public-claim-packet.md
```

Latest shareable reproduction note:

```text
docs/259-hsai-gateway-digest-bound-manifest-reproduction-note.md
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

Local checker command:

```sh
cargo test -p zkbench-core --test gateway_claim_packet_reproduction --quiet
```

## Current Public Claim

Use this bounded wording:

```text
HSAI has a local digest-bound gateway public claim packet. The packet indexes a
structured local manifest for the gateway-to-attestation-to-preview bridge and
has a hermetic checker that validates the manifest digest, covered phases,
commands, ignored-artifact boundary, nonclaims, and forbidden public phrases.
This is local metadata integrity evidence only.
```

Short version:

```text
HSAI has a local digest-bound gateway packet with a hermetic manifest checker.
It proves packet integrity and claim-boundary discipline only.
```

## Explicit Nonclaims

This index does not claim:

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

## Reproduction Checklist

1. Start from the indexed commit.
2. Confirm the packet and reproduction note paths above exist.
3. Confirm the packet contains the manifest digest above.
4. Run the checker command.
5. Confirm generated demo output remains ignored if it exists:

```sh
git status --short --ignored .gateway-demo-runs
```

6. Keep generated output out of git.

## Next Step

The next bridge slice was a local index checker that verifies this index against
the packet, reproduction note, digest, checker command, and nonclaims without
creating generated artifacts or strengthening the public claim. That checker is
recorded in `docs/261-hsai-gateway-public-packet-index-checker-notes.md`.
