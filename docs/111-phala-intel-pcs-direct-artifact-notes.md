# Phala Intel PCS Direct Artifact Notes

Status: implemented as an operator-only direct Intel PCS QVL artifact path.

This phase closes the narrow production Intel PCS/PCCS-operation gap for the
existing Phala-verified TDX quote. It runs the operator-installed `dcap-qvl`
CLI with `PCCS_URL=https://api.trustedservices.intel.com`, then materializes
only digest-bound local metadata. It does not add a repo-native DCAP verifier
and does not retain raw quote or QVL report bodies in git.

## State Slice

This implementation touches:

- `crates/hsai-attestation-phala/examples/operator_live_intel_pcs_artifact.rs`
- `crates/hsai-attestation-phala/tests/phala_operator_live_intel_pcs_contract.rs`
- `docs/111-phala-intel-pcs-direct-artifact-notes.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `docs/research/zk_external_source_index.md`
- `README.md`
- `AGENTS.md`

No Cargo metadata, `Cargo.lock`, committed credentials, credential fixtures,
committed raw quote, committed QVL report, accepted Evidence Ledger, official
submission artifact, benchmark pack, package runtime file, TLS implementation,
or Phase 4 registry semantic is changed by this slice.

## Operator Flow

The operator fetches the raw quote outside normal tests:

```text
curl -fsS \
  -o <raw-quote.bin> \
  https://cloud-api.phala.com/api/v1/attestations/raw/<checksum>
```

The operator runs direct Intel PCS-backed QVL checks outside normal tests:

```text
dcap-qvl pckinfo <raw-quote.bin> > <pck-info.json>
PCCS_URL=https://api.trustedservices.intel.com \
  dcap-qvl verify <raw-quote.bin> > <intel-pcs-qvl-report.json>
```

The repo example then validates saved, repo-external inputs:

```text
HSAI_PHALA_OPERATOR_ACK=I_ACKNOWLEDGE_OPERATOR_LIVE_PHALA_RUN
HSAI_PHALA_INTEL_PCS_INPUT_JSON=<non-secret-input-json>
cargo run -p hsai-attestation-phala --example operator_live_intel_pcs_artifact
```

The input JSON names:

- `operator_run_id`
- `checksum`
- `raw_quote_path`
- `pck_info_path`
- `qvl_report_path`
- `qvl_stderr_path`
- `qvl_tool`
- `qvl_tool_version`
- `pccs_url`
- `output_root`
- `started_at`
- `finished_at`

The example validates:

- `pccs_url` equals `https://api.trustedservices.intel.com`;
- the raw quote is non-empty;
- PCK info is TDX quote version 4 with `Leaf PCK`, `PCK CA`, and `Root CA`;
- QVL, QE, and platform statuses are all `UpToDate`;
- QVL advisory lists are empty.

It writes only:

- `intel-pcs/summary.json`
- `intel-pcs/raw-quote.sha256`
- `intel-pcs/pck-info.sha256`
- `intel-pcs/qvl-report.sha256`
- `intel-pcs/qvl-stderr.sha256`

It does not retain the raw quote, PCK info, QVL report, or stderr body in the
materialized output.

## Live Run Result

The Phase 111 operator run verified checksum:

```text
5c99c72274ed0745f7788cdf272cc359099c07629833306d1a13f1b8e34596bd
```

The raw quote was fetched as a 5010-byte binary attachment with SHA-256:

```text
7c92c34ddc9634c873ea1ca4953a45883ed5692a0c3865323e2044fc58aaf26e
```

`PCCS_URL=https://api.trustedservices.intel.com dcap-qvl verify` returned the
same QVL report SHA-256 as Phases 108 and 110:

```text
36edac15ac8c8c00da61953afa46b2cc428f1047ef8cc664df528938d329c0a7
```

The verifier stderr SHA-256 was:

```text
0e49aa6e694e9654fb3686b74644d340269946900cdfc67954b35254af30474c
```

The digest-only materialized output was written outside git at:

```text
/tmp/zkbench-intel-pcs-20260622/artifact-output/intel-pcs
```

## Claim Boundary

Successful materialization remains capped at `Attested`. It establishes that an
operator-run local QVL verifier accepted the raw Phala quote while fetching
collateral through Intel's public PCS endpoint.

This is not proof, not a repo-native DCAP verifier implementation, not
managed-service signature/JWKS/JWT verification, not TLS or attested-TLS
channel binding, not benchmark evidence, not official benchmark evidence, not
semantic correctness, not global software-agent uniqueness, and not
authorization to mutate an accepted Evidence Ledger.

## Tests

`crates/hsai-attestation-phala/tests/phala_operator_live_intel_pcs_contract.rs`
is hermetic. It checks that the example requires explicit acknowledgement and
input files, writes digest-only outputs, does not spawn a process, does not use
direct network APIs, does not retain raw QVL outputs, and keeps non-claims
explicit.

Normal workspace tests do not call Phala, do not run `dcap-qvl`, do not contact
Intel PCS, do not require credentials, and do not fetch PCCS collateral.
