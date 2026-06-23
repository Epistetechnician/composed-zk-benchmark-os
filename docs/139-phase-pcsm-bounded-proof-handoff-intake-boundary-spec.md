# Phase 139 PCSM Bounded-Proof Handoff Intake Boundary Spec

Status: docs-first boundary for future intake of a committed
recoverable-ghost-states PCSM CL12 bounded-proof handoff.

## State Slice

This documentation-only phase may touch only:

- `docs/139-phase-pcsm-bounded-proof-handoff-intake-boundary-spec.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

It does not authorize Rust source changes, tests, Cargo metadata changes,
`Cargo.lock` changes, PCSM runtime import or vendoring, recoverable-ghost
artifact import, generated output files, committed intake bundles,
admission-journal materialization, package runtime files, command-line tools,
network access, provider calls, credentials, accepted Evidence Ledger mutation,
official benchmark submission, score-axis population, or Level2+ evidence.

## Goal

Define the smallest future metadata intake contract for a PCSM CL12
bounded-proof handoff produced by recoverable-ghost-states. The future intake
can describe the bounded proof package as local admission metadata, but it must
not import PCSM code, replay PCSM runtime behavior, or convert the handoff into
accepted benchmark evidence.

The source handoff path under recoverable-ghost-states is expected to be:

```text
docs/pcsm-cl12-bounded-proof-handoff.md
```

The future intake may proceed only after the source repo provides a committed
and digest-stable handoff. A local staged or dirty source snapshot is not a
stable intake source.

## Required Source Identity

A future intake manifest must record:

- `source_repo_remote`
- `source_repo_branch`
- `source_repo_commit`
- `source_repo_status`
- `source_handoff_path`
- `source_handoff_sha256`
- `source_handoff_schema`
- `source_handoff_state_slice`

The validator must reject missing source commits, non-hex commit ids, dirty or
ambiguous source status, missing handoff digests, digest drift, absolute source
paths, parent-directory components, and handoff paths outside the declared
source repo.

## Required Bounded-Proof Fields

A future typed intake candidate must capture these fields from the handoff as
data:

- `bounded_breakthrough_evidence_admitted`
- `threshold_admitted`
- `replication_admission_status`
- `blocked_item`
- `pcsm_inputs`
- `pcsm_accepted`
- `pcsm_rejected`
- `pcsm_journal_entries`
- `provider_direct_authority`
- `production_authority`
- `raw_provider_payloads_committed`
- `local_mlx_surrogate_runtime`
- `native_pcsm_governed_state`
- `pcsm_journaled`

The current bounded-proof shape is admissible only when:

- `bounded_breakthrough_evidence_admitted=true`;
- `threshold_admitted=false`;
- `replication_admission_status=blocked_preflight_only`;
- `blocked_item=live_external_runtime_replication`;
- provider direct authority is false;
- production authority is false;
- raw provider payload commitment is false;
- PCSM accepted and rejected counts are both represented;
- PCSM journal entries are represented.

A future stronger claim where `threshold_admitted=true` requires a separate
boundary. It cannot be silently accepted through this bounded-proof intake.

## Required Verifier Status

The future intake must record source verifier statuses for:

- `verify_cl12_local_mlx_pcsm_surrogate`
- `verify_cl12_external_benchmark_replication`
- `verify_breakthrough_threshold_audit`
- `verify_native_pcsm`
- source repo lint gate

The validator must reject missing statuses, failing statuses, verifier names
that drift from the manifest, missing blocked-preflight annotations, missing
native-PCSM authority flags, or source lint status that is not explicitly
reported.

The composed-zk-benchmark-os validator must not run recoverable-ghost-states
commands in normal gates. It may inspect a committed manifest and digest-bound
handoff only after a future implementation phase authorizes a local parser.

## Source Artifact Digest Contract

A future intake may record digest-only references for non-secret source
artifacts named by the handoff, including:

- dataset digest;
- model-identity digest;
- result digest;
- packet digest;
- native PCSM evidence digest;
- PCSM journal digest;
- PCSM transcript digest;
- public metrics digest;
- live-provider registry digest.

It must not embed raw source artifacts, raw PCSM journals, raw provider
payloads, raw network transcripts, credentials, raw benchmark outputs, raw
attestation quotes, raw JWKS/OpenID documents, raw TLS exporters, or accepted
Evidence Ledger JSON.

## Mapping To HSAI Admission

A later implementation phase may map the committed handoff into local admission
metadata using the existing `hsai-agent-admission` concepts:

- `AdmissionSourceKind::ProviderResponse` or a future dedicated source kind for
  external handoff metadata;
- strict typed candidate fields;
- source artifact digests;
- required nonclaims;
- rejected or quarantined status when the handoff asks for authority above the
  local boundary;
- no accepted claim envelope unless a separate local claim-envelope proposal
  passes the existing admission policy.

This boundary authorizes no implementation of that mapping. It only defines the
future contract.

## Required Nonclaims

Any future intake candidate, manifest, review note, or admission-journal bundle
must explicitly state:

- this is not PCSM runtime import;
- this is not recoverable-ghost artifact import;
- this is not accepted Evidence Ledger mutation;
- this is not official benchmark evidence;
- this is not official benchmark submission;
- this is not external runtime replication;
- this is not provider authority;
- this is not production authority;
- this is not serving authority;
- this is not proof;
- this is not semantic correctness;
- this is not production readiness;
- this does not create Level2+ evidence;
- this does not populate score axes;
- this does not admit the full breakthrough threshold.

## Rejection Rules

A future validator must fail closed when:

- the source handoff is not tied to a committed source revision;
- the handoff digest does not match the manifest;
- the source repo status is dirty, staged-only, or otherwise ambiguous;
- the handoff omits explicit nonclaims;
- the handoff claims full breakthrough-threshold admission;
- the handoff claims live external runtime replication without a separate
  boundary;
- provider, production, or serving authority is requested;
- raw provider payloads or credentials are present;
- accepted Evidence Ledger mutation is requested;
- official submission or external replay is requested;
- score-axis population is requested;
- Level2+ evidence creation is requested.

## Future Implementation Exit Criteria

A later implementation phase must:

- touch only a separately authorized local parser surface, phase notes, and
  navigation/status docs;
- parse committed, digest-stable handoff metadata only;
- reject dirty or uncommitted source handoff snapshots;
- bind source repo commit, handoff path, and handoff digest;
- preserve blocked-preflight and threshold-not-admitted status;
- emit local admission metadata only;
- preserve normal test hermeticity;
- avoid running recoverable-ghost commands in normal gates;
- keep all claims local and below accepted evidence.

## Non-Goals

This boundary does not permit PCSM runtime import or vendoring,
recoverable-ghost artifact import, provider calls, network access, credentials,
source repo command execution in normal gates, external replay execution,
official benchmark submission, accepted Evidence Ledger mutation, generated
committed artifacts, admission-journal materialization, score-axis population,
local Intel DCAP implementation, PCCS operation, JWKS fetching, JWT
verification changes, TLS or attested-TLS channel binding, formal evidence,
Level2+ evidence, production-readiness claims, semantic-correctness claims,
proof claims, benchmark-evidence claims, full breakthrough-threshold admission
claims, or global software-agent uniqueness claims.
