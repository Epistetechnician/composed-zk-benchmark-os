# Managed JWKS Fetch Artifact Notes

Status: implemented as an operator-only managed JWKS fetch artifact path.

This phase closes the narrow live JWKS-fetching gap for one public managed
attestation provider endpoint. It fetches Intel Trust Authority OpenID metadata
and JWKS outside normal tests, validates the saved JSON responses locally, and
materializes only digest-bound metadata. It does not accept or verify any
managed JWT, and it does not add network access to normal tests.

## State Slice

This implementation touches:

- `crates/hsai-attestation/examples/operator_live_jwks_artifact.rs`
- `crates/hsai-attestation/tests/managed_jwks_artifact_contract.rs`
- `docs/109-managed-jwks-fetch-artifact-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `docs/research/zk_external_source_index.md`
- `README.md`
- `AGENTS.md`

No Cargo metadata, `Cargo.lock`, committed credentials, credential fixtures,
committed raw OpenID or JWKS responses, accepted Evidence Ledger, official
submission artifact, benchmark pack, local PCCS service configuration, TLS
channel binding, or Phase 4 registry semantic is changed by this slice.

## Operator Flow

The operator fetches the public OpenID metadata and JWKS outside normal tests:

```text
curl -fsS \
  -o <openid.json> \
  https://portal.trustauthority.intel.com/.well-known/openid-configuration

curl -fsS \
  -o <certs.json> \
  https://portal.trustauthority.intel.com/certs
```

The repo example then validates saved, repo-external inputs:

```text
HSAI_MANAGED_JWKS_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_JWKS_FETCH
HSAI_MANAGED_JWKS_INPUT_JSON=<non-secret-input-json>
cargo run -p hsai-attestation --example operator_live_jwks_artifact
```

The input JSON names:

- `operator_run_id`
- `provider`
- `issuer`
- `openid_configuration_url`
- `jwks_uri`
- `openid_response_path`
- `jwks_response_path`
- `output_root`
- `started_at`
- `finished_at`

The example validates:

- the input issuer, OpenID configuration URL, and JWKS URI are HTTPS;
- the saved OpenID issuer matches the input issuer;
- the saved OpenID `jwks_uri` matches the input JWKS URI;
- `response_types_supported` includes `id_token`;
- `claims_supported` includes `iss`, `exp`, and `nbf`;
- OpenID signing algorithms are non-empty;
- the JWKS `keys` array is non-empty;
- each key has non-empty `kid`, `alg`, RSA `kty`, RSA modulus `n`, and exponent
  `e`;
- each key algorithm is advertised by OpenID metadata;
- each `kid` plus algorithm pair is unique.

It writes only:

- `managed-jwks/summary.json`
- `managed-jwks/openid-configuration.sha256`
- `managed-jwks/jwks.sha256`

It does not retain the raw OpenID metadata or JWKS body in the materialized
output.

## Live Run Result

The Phase 109 operator run fetched:

```text
https://portal.trustauthority.intel.com/.well-known/openid-configuration
https://portal.trustauthority.intel.com/certs
```

The OpenID metadata response was 663 bytes with SHA-256:

```text
a330c2032a986845f959284c4202972bc5e698d7ea652423ca5cebc4ea33edea
```

The JWKS response was 11562 bytes with SHA-256:

```text
4e1d55c79b698cde4987d791594495e70432879be621a1b6e42a9daafc84bee3
```

The saved OpenID metadata advertised issuer
`https://portal.trustauthority.intel.com`, JWKS URI
`https://portal.trustauthority.intel.com/certs`, response type `id_token`, and
signing algorithms `PS384` and `RS256`. The saved JWKS contained two RSA key
entries. The digest-only materialized output was written outside git at:

```text
/tmp/zkbench-managed-jwks-20260622/artifact-output/managed-jwks
```

## Claim Boundary

Successful materialization remains capped at `Attested`. It establishes only
that an operator fetched a public managed-attestation OpenID/JWKS endpoint, that
the saved metadata and JWKS are structurally consistent, and that digest-only
metadata can be materialized without committing raw responses.

This is not proof, not token acceptance, not managed-JWT signature verification,
not DCAP quote verification, not PCCS service operation, not TLS or
attested-TLS channel binding, not benchmark evidence, not official benchmark
evidence, not semantic correctness, not global software-agent uniqueness, and
not authorization to mutate an accepted Evidence Ledger.

## Tests

`crates/hsai-attestation/tests/managed_jwks_artifact_contract.rs` is hermetic.
It checks that the example requires explicit acknowledgement and input files,
writes digest-only outputs, does not spawn a process, does not use direct
network APIs, does not retain raw OpenID/JWKS responses, and keeps non-claims
explicit.

Normal workspace tests do not fetch OpenID metadata, do not fetch JWKS, do not
require credentials, and do not verify a live managed JWT.
