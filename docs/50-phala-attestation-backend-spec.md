# Phala Attestation Backend - Phase 3 Spec

## Status And Claim Boundary

This is the implementation spec for Phase 3 of the managed-attestation track. In
the current Level 1 repository state it builds a deterministic fixture-oriented
Phala/dstack backend preparation crate behind the shipped `AttestationVerifier`
trait. It does not yet perform real TDX quote verification, real managed-service
signature verification, or live Phala API calls.

The backend target is Phala/dstack, selected as `viable-first` in
`docs/48-managed-attestation-feasibility.md`.

This phase may verify deterministic fixture-shaped Phala/dstack evidence, map
accepted evidence into `VerifiedAttestation`, and emit `Attested`
anchor-validity envelopes through the existing `hsai-attestation` lane. It must
not emit `Proven`. It must not claim real hardware verification, external
attestation evidence, global agent uniqueness, competence, safety, semantic
correctness, or a regenerative economy.

## Build Target

Build exactly one new crate:

```text
crates/hsai-attestation-phala
```

This crate depends on:

- `hsai-attestation`
- `hsai-claim-envelope`
- `hsai-distinct-agent`
- `serde`
- `serde_json`
- cryptographic/JWT/quote verification crates only after fixture format is pinned

It does not modify existing crates.

## Integration Shape

The crate exports a backend implementing:

```text
impl AttestationVerifier for PhalaAttestationVerifier
```

The backend accepts Phala/dstack evidence, verifies it according to a local trust
policy, and returns `VerifiedAttestation` only when all HSAI bindings match.

The crate should separate parsing, policy, and verification:

```text
PhalaEvidence
PhalaTrustPolicy
PhalaVerifyMode::{Local, ManagedApi}
PhalaAttestationVerifier
PhalaError
```

## Phala Evidence Model

First fixture-oriented shape:

```text
struct PhalaEvidence {
  anchor_id:          String,
  quote_hex:          String,
  report_data:        Vec<u8>,
  compose_hash:       Vec<u8>,
  event_log:          Option<Vec<u8>>,
  docker_image_digest: Option<Vec<u8>>,
  not_before:         u64,
  not_after:          u64,
}
```

This shape may evolve after captured Phala fixtures are inspected. The first rule
is that all parser changes remain behind the crate's own `PhalaEvidence` boundary
and do not alter `hsai-attestation::Token`.

## Trust Policy

```text
struct PhalaTrustPolicy {
  expected_anchor_id:          String,
  expected_report_data:        Vec<u8>,
  expected_compose_hash:       Vec<u8>,
  expected_docker_image_digest: Option<Vec<u8>>,
  require_event_log_replay:    bool,
  allow_managed_api:           bool,
  now:                         u64,
}
```

The HSAI report-data profile is fixed:

```text
reportData = hash(agent_pubkey || nonce || case_hash)
```

Phase 1 exposes this profile as
`hsai_attestation::report_data_binding(agent_pubkey, nonce, case_hash)`. The hash
algorithm is `sha2::Sha256`. Any provider-specific deviation required by Phala's
exact report-data format must be documented before implementation.

## Verification Modes

### Local Mode

Preferred target.

Responsibilities:

- verify TDX quote/report signature locally;
- verify report data;
- verify compose hash;
- optionally replay RTMR/event log;
- optionally verify Docker image digest;
- check freshness;
- check anchor id.

### Managed API Mode

Allowed only as an explicitly labeled PoC mode.

Responsibilities:

- call Phala verifier API or consume its response;
- verify report data and compose hash locally after the managed verifier says the
  quote is valid;
- treat Phala Cloud verifier as an explicit `TrustRoot`;
- never hide managed-verifier dependence behind Intel TDX alone.

Managed API mode must be rejectable by policy:

```text
allow_managed_api = false
```

## Public Functions

```text
fn report_data_binding(agent_pubkey: &[u8], nonce: u64, case_hash: &[u8]) -> Vec<u8>;

fn parse_phala_evidence(bytes: &[u8]) -> Result<PhalaEvidence, PhalaError>;

fn verify_report_data_binding(evidence: &PhalaEvidence, expected: &[u8])
  -> Result<(), PhalaError>;

fn verify_compose_hash(evidence: &PhalaEvidence, expected: &[u8])
  -> Result<(), PhalaError>;

fn verify_freshness(evidence: &PhalaEvidence, now: u64)
  -> Result<(), PhalaError>;

fn map_phala_to_verified_attestation(evidence: &PhalaEvidence)
  -> VerifiedAttestation;
```

Local quote verification should be a distinct function once the exact Phala quote
fixture format is pinned:

```text
fn verify_phala_quote_or_report(evidence: &PhalaEvidence, policy: &PhalaTrustPolicy)
  -> Result<(), PhalaError>;
```

## Error Model

```text
enum PhalaError {
  Parse,
  AnchorMismatch,
  ReportDataMismatch,
  ComposeHashMismatch,
  DockerImageDigestMismatch,
  EventLogReplayMismatch,
  QuoteVerificationFailed,
  ManagedApiRejected,
  ManagedApiDisallowed,
  Expired,
  NotYetValid,
}
```

Mapping into `hsai-attestation::VerifyError`:

```text
AnchorMismatch          -> VerifyError::AnchorMismatch
ReportDataMismatch      -> VerifyError::ReportDataMismatch
ComposeHashMismatch     -> VerifyError::MeasurementMismatch
DockerImageMismatch     -> VerifyError::MeasurementMismatch
EventLogReplayMismatch  -> VerifyError::MeasurementMismatch
QuoteVerificationFailed -> VerifyError::SignatureUnverified
ManagedApiRejected      -> VerifyError::SignatureUnverified
Expired / NotYetValid   -> VerifyError::Expired
```

## First End-To-End Slice

The first real backend demonstration should be:

```text
Minimal agent-case emitter inside Phala CVM
  -> emits agent_pubkey, nonce, case_hash
  -> dstack/Phala quote binds reportData
  -> hsai-attestation-phala verifies evidence
  -> AttestationLane emits Attested anchor-validity envelope
  -> conjoin with DistinctAgentLane closes assumptions
  -> IdentityRegistry registers subject
  -> Economy earns once
  -> Membrane freeze blocks conversion
```

The first implementation uses deterministic fixture evidence only. Live Phala API
calls and real quote verification should wait until captured artifact formats,
parser behavior, and trust-root mapping are stable.

## Unit Vectors

### PH-1 - Report Data Binding

Given `agent_pubkey`, `nonce`, and `case_hash`, `report_data_binding` returns
the expected digest. Evidence with matching `report_data` passes binding
verification.

### PH-2 - Report Data Mismatch

Evidence with wrong `report_data` maps to `VerifyError::MeasurementMismatch`.

### PH-3 - Compose Hash Mismatch

Evidence with wrong `compose_hash` maps to `VerifyError::MeasurementMismatch`.

### PH-4 - Expired Evidence

Evidence where `now > not_after` maps to `VerifyError::Expired`.

### PH-5 - Managed API Disallowed

If `PhalaVerifyMode::ManagedApi` is requested but policy has
`allow_managed_api = false`, verification fails and emits no trust root.

### PH-6 - Accepted Evidence Closes Distinctness

Accepted Phala evidence, routed through `AttestationLane<PhalaAttestationVerifier>`,
conjoined with `DistinctAgentLane`, produces a closed `Attested` distinctness
envelope admitted by `require_closed`.

### PH-7 - Managed API Trust Root Is Visible

If managed API mode is used, the resulting trust roots include the managed Phala
verifier root in addition to the hardware/runtime roots actually relied on.

## Property Tests

### PHP-1 - Determinism

For generated fixture evidence and policies, verification is byte-deterministic.

### PHP-2 - Single Field Mutation Rejects

For accepted fixture evidence, mutating any one of `report_data`, `compose_hash`,
`anchor_id`, or validity window causes rejection.

### PHP-3 - Maturity Ceiling

Any envelope emitted through the Phala verifier path has maturity `<= Attested`.

### PHP-4 - No Hidden Trust Root

For each verification mode, the emitted trust roots exactly match the roots the
policy relied on. Managed API mode must not emit only Intel TDX.

## Definition Of Done

- New crate `crates/hsai-attestation-phala` is added to workspace members.
- No existing crate is modified.
- Captured or synthetic deterministic Phala fixtures are committed only if small
  and non-secret.
- PH-1..PH-7 unit tests pass.
- PHP-1..PHP-4 property tests pass.
- Commands pass:

```sh
cargo test -p hsai-attestation-phala
cargo fmt --all --check
cargo clippy -p hsai-attestation-phala --all-targets -- -D warnings
```

## Out Of Scope

- Azure Attestation backend.
- Intel Trust Authority backend.
- Apple/Darkbloom provider-key backend.
- zkTLS.
- Proof of Agent governance.
- External rails.
- Onchain verification.
- ZK wrapping or `Attested -> Proven`.
- Any claim stronger than hardware-bounded `Attested` runtime anchoring.

## Sources

- Phala verify application: https://docs.phala.com/phala-cloud/attestation/verify-your-application
- Phala dstack overview: https://docs.phala.com/dstack/overview
- dstack repository: https://github.com/Dstack-TEE/dstack
- dstack audit: https://reports.zksecurity.xyz/reports/phala-dstack/
