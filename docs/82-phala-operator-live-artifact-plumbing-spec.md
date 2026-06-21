# Phala Operator Live Artifact Plumbing Spec

## Status And Claim Boundary

This is a docs-first boundary for future local artifact plumbing around the
operator-only Phala/dstack live managed-verifier path. It authorizes no Rust
implementation, no examples, no scripts, no network access, no live Phala API
calls, no credentials, no operator live tests, and no generated artifacts in
this slice.

The future plumbing exists only to make a later operator run auditable without
making that run proof. The strongest future successful output remains
`Attested`, never `Proven`. Artifact plumbing is not semantic correctness, not
official benchmark evidence, not local Intel DCAP verification, not proof of
global software-agent uniqueness, and not authorization to mutate accepted
benchmark Evidence Ledgers.

## State Slice

This docs-first phase may touch only:

```text
docs/82-phala-operator-live-artifact-plumbing-spec.md
docs/12-task-list.md
README.md
AGENTS.md
```

It must not touch Rust source, Cargo metadata, `Cargo.lock`, fixtures, accepted
Evidence Ledgers, benchmark packs, report bundles, audit indexes, generated
artifacts, package runtime files, examples, scripts, or operator secrets.

## Purpose

Narrow the future implementation contract before any code writes or reads
operator-live artifacts.

The future artifact plumbing may have exactly one provider family and one
operator mode:

```text
provider: Phala/dstack
mode: operator-run live managed verifier
```

The future implementation must remain local and bounded. It may write and read
declared non-secret artifacts under an operator-selected output directory, but
it must not perform live provider calls unless a later, separate phase
explicitly authorizes that runtime path.

## Future Code Touch Surface

A later implementation phase may be limited to:

```text
crates/hsai-attestation-phala/src/lib.rs
crates/hsai-attestation-phala/tests/
docs/<future-phase-notes>.md
README.md
AGENTS.md
```

A later implementation may broaden that list only if its own state slice names
the additional files explicitly.

The preferred first code phase should implement local artifact data types,
validation, redaction-report validation, digest checks, and hermetic fake-client
tests. It should not implement provider HTTP, credential loading, or ignored
operator-run tests in the same first code slice.

## Future Artifact Bundle Contract

A future local artifact bundle must be rooted under an operator-selected
directory and must use this logical shape:

```text
operator-live/
  request.json
  normalized-response.json
  trust-roots.json
  redaction-report.json
  audit.json
  raw-response.sha256
```

The bundle root must be portable metadata. It must not be interpreted as a trust
root. The future implementation must reject path traversal, absolute paths
inside bundle metadata, missing files, duplicate logical files, and undeclared
extra files unless a future spec explicitly allows extension fields.

## Future File Roles

`request.json` must contain only non-secret request material equivalent to the
existing hermetic verifier request:

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
request_time
```

`normalized-response.json` must contain the provider verdict and normalized
attestation fields needed by the hermetic verifier. It must be sufficient to
re-run local validation without a network call.

`trust-roots.json` must disclose managed-verifier trust roots and their source
labels. Trust-root disclosure is required for accepted responses, but disclosure
does not raise the claim above `Attested`.

`redaction-report.json` must state which fields were removed, hashed, retained,
or dropped as forbidden secret-shaped data. It must fail closed if any required
redaction decision is missing.

`audit.json` must bind the bundle together and state:

```text
schema_version
operator_run_id
provider
verification_mode
request_digest
normalized_response_digest
trust_roots_digest
redaction_report_digest
raw_response_digest
started_at
finished_at
timeout_seconds
retry_limit
provider_verdict
claim_boundary
non_claims
```

`raw-response.sha256` must contain only a digest of a raw response body. A later
implementation must not require the raw response body to be present, and normal
workspace tests must not depend on raw provider output.

## Future Digest And Schema Rules

A later implementation must make artifact validation deterministic:

- every JSON artifact must carry a schema version;
- digests must use SHA-256 unless a future spec names another algorithm;
- digest inputs must use a stable byte representation;
- missing required digests must fail closed;
- mismatched digests must fail closed;
- stale normalized responses must fail closed;
- rejected provider verdicts must emit no guarantees and no trust roots through
  the attestation lane;
- accepted provider verdicts must map only to `Attested`.

The future implementation may expose helper constructors for tests, but helper
defaults must never imply a live provider call.

## Future Redaction Validation

Artifact plumbing must validate redaction reports before accepting or writing a
bundle. Forbidden output shapes include:

- bearer tokens;
- API keys;
- private keys;
- cookies;
- authorization headers;
- registry credentials;
- cloud credentials;
- deployment credentials;
- raw credential headers;
- Phala account secrets.

If a field is retained, the redaction report must explain why the retained value
is non-secret. If that explanation is absent, the bundle must be rejected.

## Required Future Tests

A future implementation phase must include hermetic tests for:

- valid bundle round trip;
- missing required file;
- undeclared extra file;
- path traversal rejection;
- digest mismatch rejection;
- missing schema version rejection;
- stale normalized response rejection;
- missing trust roots on accepted response;
- redaction report missing retained-field rationale;
- token-shaped value rejection;
- attempted claim above `Attested`;
- rejected provider verdict emitting no guarantees or trust roots;
- normal workspace tests requiring no live credentials and no network.

Any future operator-run test that performs a live call must be ignored,
feature-gated, or otherwise excluded from normal workspace gates, and must be
authorized by a separate state slice.

## Forbidden In This Slice

- Rust source changes.
- Cargo metadata changes.
- `Cargo.lock` changes.
- Package runtime files.
- Examples or scripts.
- Network access.
- Live Phala API calls.
- Operator live tests.
- Credential handling code.
- Secret fixtures.
- Generated operator artifacts.
- Local Intel DCAP quote verification code.
- PCCS or collateral fetch/caching code.
- Generic JWKS/JWT fetch code.
- TLS or attested-TLS implementation.
- Deployment orchestration.
- External repo clones or vendored source.
- Backend execution.
- Benchmark outputs.
- External result import.
- Accepted Evidence Ledger mutation.
- Phase 4 anchor-registry semantic changes.
- Level2+ evidence.
- Claims above `Attested`.

## Acceptance Criteria For This Slice

- This spec exists and names the future artifact-plumbing boundary.
- README navigation links this spec.
- `docs/12-task-list.md` records this docs-first boundary.
- `AGENTS.md` authorizes only this Markdown planning slice.
- Validation confirms no Rust source, Cargo metadata, package runtime, fixture,
  generated artifact, benchmark output, or accepted Evidence Ledger changed.

## Future Implementation Exit Criteria

A later implementation phase may complete only when:

- artifact validation is deterministic;
- bundle paths are local and traversal-safe;
- required digests bind all declared files;
- redaction-report validation fails closed;
- normalized responses remain reusable by hermetic verification;
- rejected responses emit no guarantees or trust roots;
- successful responses remain `Attested` only;
- normal workspace tests require no live credentials and no network;
- docs state all non-claims.
