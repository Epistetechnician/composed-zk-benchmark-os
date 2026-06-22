# Phala Local PCCS Service Artifact Notes

Status: implemented as an operator-only local PCCS-compatible replay service
artifact path.

This phase closes the narrow local PCCS service-operation gap for the existing
Phala-verified TDX quote. It fetches the raw quote and Phala collateral outside
git, serves the collateral from a localhost-only PCCS-shaped service, runs
`dcap-qvl verify` with `PCCS_URL` pointed at that localhost service, then
materializes only digest-bound local metadata. It does not operate Intel PCS or
a production PCCS, and it does not add a repo-native DCAP verifier.

## State Slice

This implementation touches:

- `crates/hsai-attestation-phala/examples/operator_live_local_pccs_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_local_pccs_contract.rs`
- `docs/110-phala-local-pccs-service-artifact-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `docs/research/zk_external_source_index.md`
- `README.md`
- `AGENTS.md`

No Cargo metadata, `Cargo.lock`, committed credentials, credential fixtures,
committed raw quote, committed QVL report, committed PCCS access log, accepted
Evidence Ledger, official submission artifact, benchmark pack, package runtime
file, production PCCS configuration, or Phase 4 registry semantic is changed by
this slice.

## Operator Flow

The operator fetches the raw quote and collateral outside normal tests:

```text
curl -fsS \
  -o <raw-quote.bin> \
  https://cloud-api.phala.com/api/v1/attestations/raw/<checksum>

phala api /attestations/collateral/<checksum> > <raw-collateral-json>
```

The operator serves the saved collateral through a localhost-only service whose
routes match the `dcap-qvl` PCCS client:

```text
/sgx/certification/v4/pckcrl?ca=<processor-or-platform>&encoding=der
/tdx/certification/v4/tcb?fmspc=<FMSPC>
/tdx/certification/v4/qe/identity?update=standard
/sgx/certification/v4/rootcacrl
```

The operator runs local QVL checks against the local service:

```text
PCCS_URL=http://127.0.0.1:<port> dcap-qvl verify <raw-quote.bin> \
  > <local-pccs-qvl-report.json>
```

The repo example then validates saved, repo-external inputs:

```text
HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN
HSAI_PHALA_LOCAL_PCCS_INPUT_JSON=<non-secret-input-json>
cargo run -p hsai-attestation-phala --example operator_live_local_pccs_artifact
```

The input JSON names:

- `operator_run_id`
- `checksum`
- `raw_quote_path`
- `pck_info_path`
- `qvl_report_path`
- `access_log_path`
- `pck_crl_response_path`
- `tcb_response_path`
- `qe_identity_response_path`
- `root_ca_crl_response_path`
- `qvl_tool`
- `qvl_tool_version`
- `pccs_url`
- `output_root`
- `started_at`
- `finished_at`

The example validates:

- the configured `pccs_url` is an explicit localhost HTTP endpoint;
- the raw quote is non-empty;
- PCK info is TDX quote version 4 with `Leaf PCK`, `PCK CA`, and `Root CA`;
- QVL, QE, and platform statuses are all `UpToDate`;
- QVL advisory lists are empty;
- the access log contains only successful `GET` calls to the expected PCCS
  routes;
- access-log response digests match the declared saved response bodies.

It writes only:

- `local-pccs/summary.json`
- `local-pccs/raw-quote.sha256`
- `local-pccs/pck-info.sha256`
- `local-pccs/qvl-report.sha256`
- `local-pccs/access-log.sha256`
- `local-pccs/pck-crl-response.sha256`
- `local-pccs/tcb-response.sha256`
- `local-pccs/qe-identity-response.sha256`
- `local-pccs/root-ca-crl-response.sha256`

It does not retain the raw quote, QVL report, access log, or PCCS response
bodies in the materialized output.

## Live Run Result

The Phase 110 operator run verified checksum:

```text
5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd
```

The raw quote was fetched as a 5010-byte binary attachment with SHA-256:

```text
7c92c34ddc9634c873ea1ca4953a45883ed5692a0c3865323e2044fc58aaf26e
```

The Phala collateral response SHA-256 was:

```text
b2261f05766f1830053a1db66d6b89075f01b42cfcc488701f60cbba740bfcde
```

The localhost PCCS response body SHA-256 values were:

```text
pck_crl.der=e3af55430db8197cd27be746993132b9809489fa3ce2e7d254b90da7ad69aaf9
tcb.json=1991390f28fae9481050630d494aff840aeb51205e061095fba0fb76119e1372
qe_identity.json=fb4db03ddf8c89e36c9f5a32ab121bb9907b6db8b0ffa9856b1894f6809a7eb2
root_ca_crl.hex=a275a88576a9d9d8a514f03e4d588cedf4f1453176ab00e1ba60509ab9d49133
```

`PCCS_URL=http://127.0.0.1:38119 dcap-qvl verify` fetched four localhost
endpoints and returned the same QVL report SHA-256 as Phase 108:

```text
36edac15ac8c8c00da61953afa46b2cc428f1047ef8cc664df528938d329c0a7
```

The final localhost access log SHA-256 was:

```text
936d86e8e080df2e7b68bfb559b6d43aca5e6df5cbb7ffb1ca2152698531fd77
```

The digest-only materialized output was written outside git at:

```text
/tmp/zkbench-local-pccs-20260622/artifact-output/local-pccs
```

## Claim Boundary

Successful materialization remains capped at `Attested`. It establishes that
the operator-run QVL verifier accepted the raw Phala quote while fetching the
required collateral from a localhost PCCS-compatible replay service.

This is not proof, not production Intel PCS/PCCS operation, not fresh collateral
authority, not a repo-native DCAP verifier implementation, not managed-service
signature/JWKS/JWT verification, not TLS or attested-TLS channel binding, not
benchmark evidence, not official benchmark evidence, not semantic correctness,
not global software-agent uniqueness, and not authorization to mutate an
accepted Evidence Ledger.

## Tests

`crates/hsai-attestation-phala/tests/phala_operator_live_local_pccs_contract.rs`
is hermetic. It checks that the example requires explicit acknowledgement and
input files, writes digest-only outputs, does not spawn a process, does not use
direct network APIs, does not retain raw local PCCS outputs, and keeps
non-claims explicit.

Normal workspace tests do not call Phala, do not run `dcap-qvl`, do not start a
local PCCS service, do not require credentials, and do not fetch PCCS
collateral.
