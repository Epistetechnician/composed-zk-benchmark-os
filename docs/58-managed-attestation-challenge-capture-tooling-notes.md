# Managed Attestation Challenge Capture Tooling Notes

## Status And Claim Boundary

This note records the local tooling added after
`docs/57-managed-attestation-real-artifact-promotion-spec.md`.

The shipped code builds deterministic HSAI-owned challenge packets and
non-secret capture workflow manifests. It does not call Phala, does not contact a
network, does not verify quotes, does not verify managed-service signatures, and
does not create real attestation evidence.

The output remains capture input only. It is not proof, not benchmark evidence,
not backend execution evidence, and not Phase 4 authorization.

## State Slice

```text
crates/hsai-attestation-phala/src/challenge.rs
crates/hsai-attestation-phala/src/lib.rs
crates/hsai-attestation-phala/examples/operator_capture_preflight.rs
docs/58-managed-attestation-challenge-capture-tooling-notes.md
docs/59-operator-capture-runbook.md
README.md
AGENTS.md
```

## Public Utilities

`hsai-attestation-phala` now exports:

- `agent_case_hash`
- `build_agent_case_challenge_packet`
- `build_hsai_challenge_packet`
- `validate_hsai_challenge_packet`
- `capture_workflow_manifest`
- `ChallengeReplayGuard`
- `HsaiChallengeInput`
- `HsaiChallengePacket`
- `CaptureWorkflowManifest`
- `RealArtifactProviderMode`

The challenge packet computes:

```text
expected_report_data_hex = report_data_binding(agent_pubkey, nonce, case_hash)
```

The packet also carries a deterministic `challenge_id` over the normalized
packet fields. Validation recomputes both the report-data binding and the
challenge id.

## Local Replay Guard

`ChallengeReplayGuard` is an in-memory guard for normal tests and operator
preflight. It rejects reuse of the same `challenge_id` inside a capture session.
It is not a distributed replay-prevention service and must not be treated as
remote attestation evidence.

## Capture Manifest

`capture_workflow_manifest` emits the required artifact fields and forbidden
secret fields for a future operator-run capture. The manifest requires the
operator to set the provider custom-data/reportData field to
`challenge.expected_report_data_hex` exactly.

Forbidden committed artifact fields include:

- private keys;
- API tokens;
- session cookies;
- bearer tokens;
- live service credentials.

## Test Coverage

The local tests cover:

- RA-1 fresh challenge binding;
- deterministic packet construction;
- RA-2 replay rejection;
- RA-3 expired challenge rejection;
- RA-4 wrong case-hash rejection;
- challenge-id tamper rejection;
- RA-5 managed-verifier trust-root disclosure through the capture manifest;
- RA-6 Phase 4 still blocked without a real accepted artifact.

## Next Step

The next step is external to normal tests: run an operator-controlled Phala/dstack
capture using the emitted challenge packet, then commit only a small non-secret
artifact fixture if it was actually generated with the HSAI-owned challenge.

`docs/59-operator-capture-runbook.md` is the operator capture runbook.
`crates/hsai-attestation-phala/examples/operator_capture_preflight.rs` is the
operator-facing preflight example that emits the challenge packet and capture
manifest from fixed sample inputs. Both are capture inputs only and must not be
treated as attestation evidence.

Do not fabricate the artifact. Do not commit secrets. Do not build
`crates/hsai-agent-anchor-registry` until a real HSAI-owned artifact passes the
validator.
