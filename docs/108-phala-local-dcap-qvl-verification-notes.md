# Phala Local DCAP QVL Verification Notes

Status: implemented as an operator-only local QVL verification artifact path.

This phase closes the local DCAP/QVL verification-exercised gap for the
existing Phala-verified TDX quote. It downloads the raw quote outside git,
verifies it with the operator-installed `dcap-qvl` CLI, then materializes only
digest-bound local metadata. It does not add a repo-native DCAP verifier and
does not operate a local PCCS service.

## State Slice

This implementation touches:

- `crates/hsai-attestation-phala/examples/operator_live_dcap_qvl_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_dcap_qvl_contract.rs`
- `docs/108-phala-local-dcap-qvl-verification-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `docs/research/zk_external_source_index.md`
- `README.md`
- `AGENTS.md`

No Cargo metadata, `Cargo.lock`, committed credentials, credential fixtures,
committed raw quote, committed QVL report, accepted Evidence Ledger, official
submission artifact, benchmark pack, package runtime file, local PCCS service
configuration, or Phase 4 registry semantic is changed by this slice.

## Operator Flow

The operator fetches the raw quote outside normal tests:

```text
curl -fsS \
  -o <raw-quote.bin> \
  https://cloud-api.phala.com/api/v1/attestations/raw/<checksum>
```

The operator runs local QVL checks outside normal tests:

```text
dcap-qvl decode <raw-quote.bin> > <decoded-quote.json>
dcap-qvl pckinfo <raw-quote.bin> > <pck-info.json>
dcap-qvl verify <raw-quote.bin> > <qvl-report.json>
```

For the Phase 108 run, `dcap-qvl verify` fetched collateral from
`https://pccs.phala.network`, returned `status=UpToDate`,
`qe_status=UpToDate`, `platform_status=UpToDate`, and no advisory IDs.

The repo example then validates saved, repo-external inputs:

```text
HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN
HSAI_PHALA_DCAP_QVL_INPUT_JSON=<non-secret-input-json>
cargo run -p hsai-attestation-phala --example operator_live_dcap_qvl_artifact
```

The input JSON names:

- `operator_run_id`
- `checksum`
- `phala_verify_response_path`
- `raw_quote_path`
- `decoded_quote_path`
- `pck_info_path`
- `qvl_report_path`
- `qvl_tool`
- `qvl_tool_version`
- `pccs_url`
- `output_root`
- `started_at`
- `finished_at`

The example validates:

- the saved Phala response accepted the same checksum as `TEE_TDX`;
- the raw quote is non-empty;
- decoded quote and PCK info are TDX quote version 4;
- PCK certificate roles are `Leaf PCK`, `PCK CA`, and `Root CA`;
- QVL, QE, and platform statuses are all `UpToDate`;
- QVL advisory lists are empty;
- Phala parsed measurements match decoded quote and QVL report measurements for
  report data, RTMR0-3, MRTD, MRSEAM, and MRSIGNERSEAM.

It writes only:

- `dcap-qvl/summary.json`
- `dcap-qvl/raw-quote.sha256`
- `dcap-qvl/decoded-quote.sha256`
- `dcap-qvl/pck-info.sha256`
- `dcap-qvl/qvl-report.sha256`

It does not retain the raw quote, decoded quote, PCK info, or QVL report body in
the materialized output.

## Live Run Result

The Phase 108 operator run verified checksum:

```text
5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd
```

The raw quote was fetched as a 5010-byte binary attachment with SHA-256:

```text
7c92c34ddc9634c873ea1ca4953a45883ed5692a0c3865323e2044fc58aaf26e
```

The local QVL report SHA-256 is:

```text
36edac15ac8c8c00da61953afa46b2cc428f1047ef8cc664df528938d329c0a7
```

The digest-only materialized output was written outside git at:

```text
/tmp/zkbench-phala-dcap-qvl-20260622/artifact-output/dcap-qvl
```

## Claim Boundary

Successful materialization remains capped at `Attested`. It establishes that an
operator-run local QVL verifier accepted the raw Phala quote with `UpToDate`
QVL, QE, and platform status, and that the QVL measurements match the Phala
parsed measurements for the same saved response.

This is not proof, not a repo-native DCAP verifier implementation, not local
PCCS service operation, not managed-service signature/JWKS/JWT verification,
not TLS or attested-TLS channel binding, not benchmark evidence, not official
benchmark evidence, not semantic correctness, not global software-agent
uniqueness, and not authorization to mutate an accepted Evidence Ledger.

## Tests

`crates/hsai-attestation-phala/tests/phala_operator_live_dcap_qvl_contract.rs`
is hermetic. It checks that the example requires explicit acknowledgement and
input files, writes digest-only outputs, does not spawn a process, does not use
direct network APIs, does not retain raw QVL outputs, and keeps non-claims
explicit.

Normal workspace tests do not call Phala, do not run `dcap-qvl`, do not require
credentials, and do not fetch PCCS collateral.
