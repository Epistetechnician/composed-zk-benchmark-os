# Phala Operator Live Path Boundary Spec

## Status And Claim Boundary

This is a docs-first boundary for a future operator-only Phala/dstack live
managed-verifier path. It authorizes no Rust implementation, no examples, no
network access, no live Phala API calls, no credentials, and no generated
artifacts in this slice.

The repository now has a hermetic fake-client verifier surface in
`hsai-attestation-phala`. The next missing boundary is not another in-memory
test double. The missing boundary is the operating contract for a human or
caller-owned process that may later invoke a live Phala managed verifier without
turning that live result into proof, benchmark evidence, local DCAP evidence, or
global software-agent uniqueness.

The strongest future output remains `Attested`, never `Proven`. A successful
operator live verifier response may be admitted only as managed-verifier
attestation evidence under disclosed trust roots. It is not semantic
correctness, not official benchmark evidence, not local Intel DCAP verification,
not proof of global uniqueness, and not authorization to mutate accepted
benchmark Evidence Ledgers.

## State Slice

This docs-first phase may touch only:

```text
docs/81-phala-operator-live-path-boundary-spec.md
docs/12-task-list.md
README.md
AGENTS.md
```

It must not touch Rust source, Cargo metadata, `Cargo.lock`, fixtures, accepted
Evidence Ledgers, benchmark packs, report bundles, audit indexes, generated
artifacts, package runtime files, or operator secrets.

## Purpose

Define the future operator-live contract before any ignored or feature-gated
live path exists.

The future operator path may have exactly one provider and one mode:

```text
provider: Phala/dstack
mode: operator-run live managed verifier
```

The future path must remain outside normal workspace tests. It must not be
required by `cargo test --workspace`, `cargo test --workspace --features
external-runner`, `cargo clippy --workspace --all-targets -- -D warnings`, or
documentation generation.

## Future Secret Boundary

A future implementation must keep all secrets outside git and outside captured
fixtures. Secrets include:

- API tokens;
- bearer tokens;
- cookies;
- private keys;
- cloud account credentials;
- deployment credentials;
- raw credential headers;
- Phala account secrets;
- registry or image-pull credentials;
- operator machine identifiers that are not intended for publication.

Secrets may be supplied only through explicit operator-owned mechanisms, such as
environment variables or caller-owned credential providers. The repository may
name required variables in a future spec, but normal tests must not require
them, and no committed fixture may contain their values.

## Future Environment Contract

A later implementation phase may define an ignored or feature-gated operator
path only if it names every input explicitly. The minimum future environment
contract must include:

```text
PHALA_MANAGED_VERIFIER_ENDPOINT
PHALA_MANAGED_VERIFIER_TOKEN or caller-owned credential provider
HSAI_OPERATOR_LIVE_ACK=I_UNDERSTAND_THIS_IS_ATTESTED_NOT_PROVEN
HSAI_OPERATOR_OUTPUT_DIR
HSAI_OPERATOR_TIMEOUT_SECONDS
HSAI_OPERATOR_RETRY_LIMIT
```

Names may change in the future implementation, but the roles must stay
separate:

- provider endpoint;
- authentication source;
- explicit human acknowledgement;
- non-secret output directory;
- timeout;
- retry bound.

No default environment value may cause a live provider call.

## Future Input Contract

A future operator run may use only non-secret request material already modeled
by the hermetic verifier surface:

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

The future path may additionally carry an operator run id and local output path,
but those must not be used as trust roots.

## Future Output Shape

A future operator run may emit a non-secret local artifact bundle only under a
caller-selected ignored output directory. The bundle shape must be defined
before code exists and must include at least:

```text
operator-live/
  request.json
  normalized-response.json
  trust-roots.json
  redaction-report.json
  audit.json
  raw-response.sha256
```

If a raw response body is retained, it must be caller controlled, non-secret
after redaction, and bound by `raw-response.sha256`. The normalized response
must be sufficient for the existing hermetic verifier to validate the same
claim boundary without a network call.

Future output files must remain local operator artifacts. They must not be
inserted into benchmark packs, report bundles, audit indexes, accepted Evidence
Ledgers, or source fixtures without a later reviewed acceptance phase.

## Redaction Rules

A future implementation must redact before writing any operator artifact. It
must fail closed if redaction cannot prove that output is non-secret.

The redaction report must state:

- which fields were removed;
- which fields were hashed;
- which fields were retained;
- why retained fields are non-secret;
- the digest algorithm used for raw response binding;
- whether any provider field was dropped because it matched a forbidden secret
  shape.

Forbidden output shapes include bearer tokens, API keys, private keys, cookies,
authorization headers, registry credentials, cloud credentials, and deployment
credentials.

## Timeout And Retry Policy

A future live path must be bounded:

- finite timeout per provider call;
- finite retry count;
- no exponential retry loop without a maximum wall-clock bound;
- no background daemon;
- no watch mode;
- no automatic deployment;
- no automatic Evidence Ledger append;
- no automatic Phase 4 registry mutation on rejected responses.

Timeouts, transport errors, and provider errors must map to diagnostic failure
states only. They must not become proof claims or benchmark results.

## Audit Output

A future operator audit record must disclose:

```text
schema_version
operator_run_id
provider
verification_mode
request_digest
normalized_response_digest
raw_response_digest
redaction_report_digest
trust_roots
started_at
finished_at
timeout_seconds
retry_limit
provider_verdict
claim_boundary
non_claims
```

The `claim_boundary` must be at most `Attested`. The `non_claims` list must
state that the run is not proof, not local DCAP verification, not benchmark
evidence, not global software-agent uniqueness, and not semantic correctness.

## Future Verification Order

A future implementation must fail closed in this order:

1. require explicit operator acknowledgement;
2. load credentials from the caller-owned boundary only;
3. build a non-secret request;
4. call the provider with a finite timeout and retry bound;
5. redact and digest any raw response before writing it;
6. normalize the response;
7. validate provider, mode, freshness, replay, report data, compose hash,
   runtime measurements, image digest, and trust roots;
8. write only the declared non-secret output files;
9. emit an `Attested` result only.

Any rejection must emit no guarantees and no verifier trust roots through the
attestation lane.

## Required Future Tests

A future implementation phase must include hermetic tests for:

- missing operator acknowledgement;
- missing credential source;
- timeout mapping;
- retry exhaustion mapping;
- redaction of token-shaped fields;
- refusal to write raw unredacted provider bodies;
- output bundle digest validation;
- stale normalized response rejection;
- provider rejection;
- missing trust root;
- attempted claim above `Attested`;
- attempted accepted Evidence Ledger mutation;
- normal workspace tests requiring no live credentials and no network.

If a future operator-run test is added, it must be ignored, feature gated, or
otherwise excluded from normal workspace gates.

## Forbidden In This Slice

- Rust source changes.
- Cargo metadata changes.
- `Cargo.lock` changes.
- Package runtime files.
- Network access.
- Live Phala API calls.
- Operator live tests.
- Examples or scripts that call Phala.
- Credential handling code.
- Secret fixtures.
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

- This spec exists and names the future operator-live boundary.
- README navigation links this spec.
- `docs/12-task-list.md` records this docs-first boundary.
- `AGENTS.md` authorizes only this Markdown planning slice.
- Validation confirms no Rust source, Cargo metadata, package runtime, fixture,
  generated artifact, benchmark output, or accepted Evidence Ledger changed.

## Future Implementation Exit Criteria

A later implementation phase may complete only when:

- the operator-live path is excluded from normal tests;
- live calls require explicit acknowledgement;
- credentials stay outside git;
- output artifacts are redacted and digest-bound;
- the normalized response is reusable by hermetic verification;
- rejected responses emit no guarantees or trust roots;
- successful responses remain `Attested` only;
- docs state all non-claims.
