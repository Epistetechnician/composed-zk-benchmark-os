# Phala Live Managed-Verifier Boundary Spec

## Status And Claim Boundary

This is a docs-first boundary for a future Phala/dstack live managed-verifier
integration. It authorizes no Rust implementation.

This phase exists because the repository now has:

- local managed-token field validation;
- offline ES256 managed-JWT verification over caller-provided public keys;
- Phala/dstack fixture and captured-artifact validation;
- one accepted HSAI-owned non-secret Phala/dstack artifact fixture;
- Phase 4 local anchor-registry semantics.

The missing boundary is not another pure-data model. The missing boundary is a
provider-specific, live managed-verifier profile that can later call a Phala
managed verifier while preserving every existing claim limit.

The strongest future output remains `Attested`, never `Proven`. A live Phala
managed-verifier result may strengthen the provenance of an anchor-validity
envelope, but it does not prove global software-agent uniqueness, competence,
safety, semantic correctness, official benchmark evidence, local DCAP quote
validity, or ZK backend performance.

## State Slice

This docs-first phase may touch only:

```text
docs/78-phala-live-managed-verifier-boundary-spec.md
docs/research/zk_external_source_index.md
docs/12-task-list.md
README.md
AGENTS.md
```

It must not touch Rust source, Cargo metadata, fixtures, accepted evidence
ledgers, benchmark packs, report bundles, audit indexes, generated artifacts, or
operator secrets.

## Source Attribution

This spec cites Phala/dstack source material as provider boundary input. It does
not copy source code, clone repositories, vendor dependencies, call services, or
turn upstream claims into local evidence.

- [Phala verify your application](https://docs.phala.com/phala-cloud/attestation/verify-your-application)
  describes the managed verification path used as the provider target.
- [Phala Cloud attestation overview](https://docs.phala.com/phala-cloud/attestation/overview)
  is the provider-level attestation context.
- [dstack overview](https://docs.phala.com/dstack/overview) is the runtime and
  remote-attestation context for dstack applications.
- [Phala get attestation](https://docs.phala.com/phala-cloud/attestation/get-attestation)
  is the reference for quote/report-data capture shape.
- [Phala attestation fields reference](https://docs.phala.com/phala-cloud/attestation/attestation-fields)
  is the reference for TDX quote fields, RTMRs, and report-data semantics.
- [Phala end-to-end attestation verification](https://docs.phala.com/phala-cloud/attestation/verification-guide)
  is a reference for future verification flow boundaries.
- [Dstack-TEE/dstack](https://github.com/Dstack-TEE/dstack),
  [Phala-Network/dstack-cloud](https://github.com/Phala-Network/dstack-cloud),
  and [Phala-Network/trust-center](https://github.com/Phala-Network/trust-center)
  remain implementation-source references only.

Before any code phase, these URLs must be rechecked for current schema, license,
API behavior, trust roots, rate limits, and whether fixture material may be
committed.

## Purpose

Define the exact future live-provider surface before any network-enabled
implementation exists.

The future implementation may have one provider and one mode:

```text
provider: Phala/dstack
mode: live managed verifier
```

The future implementation must not silently expand into:

- local Intel DCAP quote verification;
- PCCS collateral fetching or caching;
- Azure Attestation;
- Intel Trust Authority;
- JWKS fetching for generic managed JWTs;
- attested TLS or transport-channel binding;
- Phala deployment orchestration;
- benchmark execution;
- external result import.

## Future Input Contract

A future Phala live managed-verifier request must be built from non-secret input
material only:

```text
anchor_id
agent_pubkey
case_hash
nonce
expected_report_data_binding
expected_compose_hash
expected_runtime_measurements
expected_image_digest
freshness_window
managed_verifier_endpoint_id
operator_capture_manifest_ref
```

Secrets, bearer tokens, cookies, private keys, account identifiers that should
not be public, and raw operator credentials must remain outside committed
fixtures and outside envelope output.

If an authenticated Phala API call is required, the future implementation must
keep authentication at the caller/operator boundary. The repository may define
request and response validation rules, but it must not commit secrets or create
test paths that require live credentials.

## Future Response Contract

A future live managed-verifier response must be normalized before entering
`VerifiedAttestation`.

Required normalized fields:

```text
provider = "phala-dstack"
verification_mode = "live-managed-verifier"
anchor_id
nonce
report_data
compose_hash
runtime_measurements
image_digest
issued_at
expires_at
raw_response_digest
provider_verdict
provider_trust_roots
```

The raw response body may be retained only as caller-controlled artifact data.
If retained in a fixture, it must be non-secret, license-compatible, and bound by
a digest in the normalized record.

## Verification Order

A future implementation must fail closed in this order:

1. reject missing or malformed live managed-verifier response;
2. reject missing provider identity or unsupported verification mode;
3. reject stale response or freshness-window violation;
4. reject anchor, nonce, or report-data mismatch;
5. reject compose hash, runtime measurement, or image digest mismatch;
6. reject provider verdicts that are not explicit accepts;
7. reject missing trust-root disclosure;
8. map the accepted response to `VerifiedAttestation`;
9. emit an `Attested` claim envelope only.

Rejections must not mutate Phase 4 anchor-registry state, accepted evidence
ledgers, benchmark packs, report bundles, or audit indexes.

## Trust-Root Disclosure

A future accepted envelope must disclose each relied-on root as explicit
`TrustRoot` material. At minimum, the future implementation must distinguish:

```text
Phala managed verifier identity
dstack runtime/report format
Intel TDX hardware root or provider-disclosed hardware root
expected compose/runtime measurement root
expected image digest root
```

If the future code delegates quote appraisal to Phala's managed verifier, the
envelope must say so. It must not imply local DCAP verification.

## Replay And Freshness Rules

A future live managed-verifier implementation must enforce:

- caller-supplied nonce binding;
- one response per nonce inside an in-memory replay guard, or a documented
  caller-provided replay store boundary;
- explicit issued/expires time handling;
- freshness-window rejection;
- digest binding for any persisted raw response;
- no silent acceptance of cached provider accepts without an explicit cache
  policy.

This docs-first phase does not choose persistent storage. Any persistent replay
store requires a separate explicit implementation boundary.

## Required Negative Tests For Future Code

The future code phase must include focused tests for:

- missing response;
- malformed response;
- wrong provider;
- unsupported verification mode;
- stale response;
- replayed nonce;
- anchor mismatch;
- report-data mismatch;
- compose-hash mismatch;
- runtime-measurement mismatch;
- image-digest mismatch;
- provider rejection;
- missing trust root;
- attempted `Maturity::Proven` output;
- attempted Phase 4 registry mutation on rejection.

Network behavior must be isolated behind a test double unless the future phase
explicitly authorizes a live operator-run test. Normal workspace tests must not
depend on live Phala availability.

## Forbidden In This Docs-First Phase

- Rust implementation code.
- Cargo metadata changes.
- Network access in tests or examples.
- Live Phala API calls.
- Phala deployment orchestration.
- Local Intel DCAP quote verification code.
- PCCS or collateral fetch/caching code.
- Managed-service signature/JWKS/JWT fetch code.
- TLS or attested-TLS implementation.
- External repo clones or vendored source.
- Secrets, API keys, cookies, bearer tokens, private keys, or credentials.
- Backend execution.
- Benchmark outputs.
- External result import.
- Accepted Evidence Ledger mutation.
- Phase 4 anchor-registry semantic changes.
- Level2+ evidence.
- Claims above `Attested`.

## Acceptance Criteria For This Docs-First Phase

- This spec names exactly one provider and one mode.
- README navigation links this spec.
- `docs/12-task-list.md` records this as the next managed-attestation boundary.
- `AGENTS.md` authorizes only the docs-first boundary and preserves all
  non-goals.
- `docs/research/zk_external_source_index.md` records the Phala docs used as
  source references.
- Validation confirms no Rust source, Cargo metadata, package runtime, fixture,
  generated artifact, or benchmark output changed.

## Future Code-Phase Exit Criteria

A later code phase may be proposed only after this boundary is accepted. That
phase must:

- name the exact crate/module state slice;
- define the provider client trait and offline test double;
- keep normal tests hermetic;
- keep live calls operator-triggered only;
- keep all accepted outputs capped at `Attested`;
- expose all provider and hardware trust roots;
- document that live managed verification is not proof, not local DCAP, not
  benchmark evidence, and not global software-agent uniqueness.
