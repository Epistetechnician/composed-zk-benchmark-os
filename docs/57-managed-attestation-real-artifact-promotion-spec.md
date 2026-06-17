# Managed Attestation Real Artifact Promotion Spec

## Status And Claim Boundary

This is Phase 57 of the managed-attestation track. It was the promotion spec for
the real Phala/dstack artifact path that authorizes the bounded Phase 4
anchor-registry implementation after acceptance of the first HSAI-owned real
artifact.

The repository now has deterministic fixture validation, a captured public
Phala/dstack Trust Center artifact validation path, and one HSAI-owned real
artifact generated with a fresh challenge. That accepted artifact authorizes
`crates/hsai-agent-anchor-registry` only within the Phase 4 boundary.

This phase defines the exact non-secret evidence bundle and challenge protocol
needed before the current `hsai-attestation-phala` crate may be extended to
accept a real HSAI-owned artifact.

The output remains `Attested`, never `Proven`.

## Build Target

This spec now authorizes the bounded Phase 4 crate through the acceptance record
below.

Allowed state slice for the accepted-artifact implementation was:

```text
crates/hsai-attestation-phala
docs/
```

The follow-on Phase 4 implementation may add only the crate and docs authorized
by `docs/51-proof-of-agent-anchor-registry-spec.md`.

## HSAI-Owned Fresh Challenge Protocol

The artifact producer must derive a fresh challenge from the exact HSAI case
being admitted.

Inputs:

- `subject`: the `SubjectId` being evaluated;
- `anchor_id`: the runtime anchor identifier expected by policy;
- `agent_pubkey`: the agent public key bytes, preferably SPKI DER bytes when
  available;
- `nonce`: a verifier-generated unsigned 64-bit value that is single-use within
  the capture session;
- `case_hash`: a deterministic hash of the `AgentCase` fields relevant to
  admission;
- `challenge_created_at`: Unix timestamp for challenge creation;
- `challenge_expires_at`: Unix timestamp after which the challenge is invalid;
- `policy_id`: local identifier for the capture policy.

The expected report data is exactly:

```text
report_data_binding(agent_pubkey, nonce, case_hash)
```

`report_data_binding` is the shipped `hsai-attestation` function. It uses the
`hsai-attestation-report-data:v1` domain separator, length prefixes, big-endian
nonce encoding, and SHA-256. No provider adapter may silently change this
binding. If a provider requires a wrapper format, the wrapper must carry this
digest byte-for-byte and document the wrapper before validation accepts it.

The attested workload must place the expected report data into the provider
custom-data field before quote or managed-verifier response generation.

## Accepted Non-Secret Artifact Bundle

A future real artifact fixture must be small, public, and non-secret. It must not
contain private keys, API tokens, session cookies, bearer tokens, or live service
credentials.

Minimum JSON fields:

```text
schema_version
source
captured_at
challenge_created_at
challenge_expires_at
policy_id
subject
anchor_id
agent_pubkey_spki_hex
nonce
case_hash_hex
expected_report_data_hex
provider
provider_mode
quote_hex or managed_verifier_response
report_data_hex
compose_hash
app_id
instance_id
os_image_hash
rtmrs
rtmr_event_log
docker_image_digests
trust_root_labels
```

`provider_mode` must be one of:

- `local_quote`: local quote/collateral verification is performed by the
  validator;
- `managed_verifier`: a managed verifier response is consumed and the managed
  verifier is an explicit trust root.

The bundle must preserve enough raw fields to let future validators recompute
the local checks. Redacted fields are allowed only when they are not used by any
validation policy.

## Verification Order

Validation must occur in this order:

1. Parse the artifact without network access.
2. Reject expired challenge windows.
3. Recompute `expected_report_data_hex` from `agent_pubkey`, `nonce`, and
   `case_hash`.
4. Check `report_data_hex == expected_report_data_hex`.
5. Check the quote or managed verifier response contains the same report data.
6. Verify quote authenticity or managed verifier authenticity.
7. Check freshness of the observed artifact.
8. Check compose hash equality.
9. Check optional Docker image digest equality when policy requires it.
10. Replay RTMR/event-log data when policy requires it.
11. Check anchor id alignment.
12. Emit all relied-on trust roots in the `ClaimEnvelope`.

For `managed_verifier` mode, the trust roots must include the managed verifier
service. The validator must not collapse managed-verifier evidence into a pure
Intel TDX trust claim.

## Admission Path

The first accepted real artifact must prove only this local path:

```text
AgentCase
  -> report_data_binding(agent_pubkey, nonce, case_hash)
  -> Phala/dstack quote or managed verifier response
  -> hsai-attestation-phala validation
  -> AttestationLane emits Attested anchor-validity
  -> DistinctAgentLane conjoins and closes the distinct-agent assumption
  -> IdentityRegistry registers one subject for one non-reused anchor
```

The path may be used as local regression evidence that the HSAI binding was
carried through a real captured artifact. It is not benchmark evidence, not
backend execution evidence, not global software-agent uniqueness, and not proof.

## Unit Vectors

### RA-1 - Fresh Challenge Binding Accepted

Given a captured artifact generated from an HSAI-owned challenge, validation
accepts only when `report_data_hex` equals
`report_data_binding(agent_pubkey, nonce, case_hash)`.

### RA-2 - Replayed Challenge Rejected

Reusing a nonce after the local capture session marks it consumed is rejected.

### RA-3 - Expired Challenge Rejected

An artifact captured after `challenge_expires_at` is rejected even if all other
fields match.

### RA-4 - Wrong Case Hash Rejected

Changing `case_hash` without changing the attested report data rejects the
artifact.

### RA-5 - Managed Verifier Trust Root Visible

In `managed_verifier` mode, accepted evidence includes the managed verifier
trust root and does not claim local DCAP verification.

### RA-6 - Phase 4 Blocked Without Acceptance

If no real HSAI-owned artifact fixture passes validation, Phase 4 remains
blocked.

## Definition Of Done

- `docs/57-managed-attestation-real-artifact-promotion-spec.md` exists and is
  linked from `README.md`.
- The Phase 4 crate is added only after the first real HSAI-owned artifact
  fixture passes validation and records its trust roots and non-claims.
- No live API call is required by normal validation.
- No secret material is committed.
- A future implementation adds a small non-secret artifact fixture only after it
  was generated with the HSAI-owned challenge protocol above.
- The validator caps emitted maturity at `Attested`.
- The full workspace gates pass:

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
cargo test --workspace --features external-runner
cargo doc --workspace --no-deps
```

## Out Of Scope

- `crates/hsai-agent-anchor-registry`.
- Live Phala API calls in normal tests.
- Network access.
- Private key or credential handling.
- Fabricated quote, verifier, or benchmark artifacts.
- Local Intel DCAP implementation unless a future spec explicitly allows it.
- Managed-service signature/JWKS/JWT verification unless a future spec
  explicitly allows it.
- External rails.
- Backend execution.
- Benchmark outputs.
- Any claim above `Attested`.

## First Real HSAI-Owned Artifact Capture Record (2026-06-16)

A first real HSAI-owned Phala/dstack artifact was captured and accepted under
this spec on 2026-06-16. This section records the exact acceptance facts so that
future phases can audit the trust roots and non-claims. It satisfies the Phase 4
Recheck Rule for the bounded `crates/hsai-agent-anchor-registry` implementation.

Capture facts:

- Challenge protocol: HSAI-owned fresh challenge via
  `build_agent_case_challenge_packet`, producing a 64 hex char (32-byte
  SHA-256) `expected_report_data_hex` from `report_data_binding`.
- Capture target: a real `tdx.small` CVM on Phala Cloud, with the HSAI
  `expected_report_data_hex` injected into the dstack `reportData` field.
- Binding verification (RA-1): the TDX quote's report data equals the HSAI
  challenge's `expected_report_data_hex`. The validator recomputes
  `report_data_binding(pubkey, nonce, case_hash)` and checks equality.
- Internal consistency: `compose_hash` equals `SHA256(app_compose_json)`; the
  RTMR3 hash chain replays to the stated RTMR3; the RTMR3 event-log payloads
  for app-id, instance-id, compose-hash, and os-image-hash match the bundle
  fields.
- Agent keypair: a real P-256 key generated for this capture. The public key
  (SPKI DER, 91 bytes) is in the fixture. The private key is not in the repo.
- Fixture:
  `crates/hsai-attestation-phala/tests/fixtures/phala_hsai_owned_real_2026_06_16.json`.
- Integration test:
  `crates/hsai-attestation-phala/tests/phala_hsai_owned_real.rs`.

Trust roots relied on (all managed-verifier; none are local DCAP):

- `managed:phala-trust-center` (Phala Trust Center, managed verifier)
- `managed:intel-trust-authority` (Intel Trust Authority, managed verifier)
- `dstack-os:<os_image_hash>` (boot measurement, unverified locally)
- `compose:<compose_hash>` (app compose measurement, unverified locally)

Explicit non-claims for this capture:

- The managed-service signature was not verified locally (JWKS/JWT/DCAP
  out of scope). Hardware authenticity is managed-verifier only.
- The fixture is local regression evidence that the HSAI binding mechanism
  works against real TDX hardware. It is not proof, not benchmark evidence,
  not backend execution evidence, and not global software-agent uniqueness.
- The agent keypair is real but single-purpose for this capture. It is not a
  registered production identity.
- A replayed or expired challenge would still be rejected (RA-2, RA-3).

Validator change required to accept this artifact: the report-data binding
check now supports two formats — the Phase 3 captured-artifact format
(128 hex chars, `nonce_hex || case_hash_hex || ...`) and the Phase 57
HSAI-owned format (64 hex chars, recomputed `report_data_binding`). The
discriminator is the hex length. The existing Phase 3 fixture
(`phala_trust_center_app_2026_06_16.json`) continues to validate unchanged.

## Phase 4 Recheck Rule

Phase 4 may start only after at least one real HSAI-owned artifact passes
validation under this spec or a later stricter successor. The acceptance record
must state the exact trust roots and non-claims.

The 2026-06-16 acceptance record satisfies this rule for the bounded local
anchor registry. It does not authorize local Intel DCAP verification,
managed-service signature/JWKS/JWT verification, network access, backend
execution, benchmark outputs, external rails, global software-agent uniqueness
claims, or any claim above `Attested`.
