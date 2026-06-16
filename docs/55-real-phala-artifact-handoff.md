# Real Phala Artifact Handoff

## Purpose

This note defines the evidence needed before the fixture-oriented
`hsai-attestation-phala` crate can become a real hardware-backed Phala/dstack
backend.

The current crate validates deterministic fixture evidence only. It does not
verify real TDX quote signatures, Intel collateral, Phala managed verifier
responses, or live CVM endpoints.

## Required Captured Artifacts

A future real backend phase needs a small, non-secret captured bundle:

- raw TDX quote bytes or hex from the running dstack application;
- `report_data` exactly as exposed by the application;
- compose hash expected for the deployed application;
- event log / RTMR replay data when advanced verification is in scope;
- Docker image digest if the policy binds image identity;
- validity timestamp or observed timestamp;
- application anchor id used by HSAI;
- agent public key, nonce, and case hash used to compute HSAI report data;
- provider mode: local quote verification or managed Phala verifier response;
- if managed mode is used, the full verifier response and the trust root label
  identifying Phala's verifier dependency.

The bundle must not contain private keys, secrets, API tokens, or live service
credentials.

## Verification Boundary

The future real phase must verify, in this order:

1. Quote or managed-verifier authenticity.
2. Freshness.
3. `report_data == report_data_binding(agent_pubkey, nonce, case_hash)`.
4. Compose hash equality.
5. Optional Docker image digest equality.
6. Optional event-log replay / RTMR equality.
7. Anchor id alignment.
8. Trust roots visible in the emitted envelope.

The result remains `Attested`, never `Proven`.

## Minimum Promotion Rule

Do not implement `crates/hsai-agent-anchor-registry` from
`docs/51-proof-of-agent-anchor-registry-spec.md` until a real hardware-backed
backend has accepted at least one captured artifact bundle under the above
checks.

Fixture acceptance does not satisfy this prerequisite.

## Source Boundary

Phala's public verification documentation describes checking custom
`reportData`, application configuration such as `compose-hash`, and genuine Intel
TDX hardware. dstack's public documentation describes generating TDX quotes for
applications. Intel's TDX guidance describes quote verification as signature
validation, TCB checks, expected measurements, and expected report data.
