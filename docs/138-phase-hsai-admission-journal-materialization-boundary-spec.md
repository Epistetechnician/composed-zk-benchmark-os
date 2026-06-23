# Phase 138 HSAI Admission Journal Materialization Boundary Spec

Status: docs-first boundary for a future local admission-journal
materialization implementation.

## State Slice

This documentation-only phase may touch only:

- `docs/138-phase-hsai-admission-journal-materialization-boundary-spec.md`
- `README.md`
- `docs/12-task-list.md`
- `docs/90-whole-codebase-validation-report.md`
- `AGENTS.md`

It does not authorize Rust source changes, tests, Cargo metadata changes,
`Cargo.lock` changes, filesystem materialization code, generated output files,
committed admission journal bundles, package runtime files, command-line tools,
network access, provider calls, credentials, accepted Evidence Ledger mutation,
official benchmark submission, score-axis population, or Level2+ evidence.

## Goal

Define the smallest future local output-root contract for a reviewable HSAI
admission journal bundle. The future bundle lets an operator or agent inspect
strict typed admission candidates, accepted/rejected/quarantined decisions,
source digests, required nonclaims, and the append-only journal chain without
promoting the trace into accepted evidence.

## Future Bundle Shape

A future implementation may write exactly one declared logical bundle under a
caller-selected output root:

- `admission-journal/manifest.json`
- `admission-journal/journal.json`
- `admission-journal/decisions.jsonl`
- `admission-journal/source-digests.json`
- `admission-journal/non-claims.md`
- `admission-journal/redaction-report.json`
- `admission-journal/validation-report.json`
- `admission-journal/manifest.json.sha256`
- `admission-journal/journal.json.sha256`
- `admission-journal/decisions.jsonl.sha256`
- `admission-journal/source-digests.json.sha256`
- `admission-journal/non-claims.md.sha256`
- `admission-journal/redaction-report.json.sha256`
- `admission-journal/validation-report.json.sha256`

No undeclared file may be written or accepted during readback. Digest sidecars
must bind the exact bytes of the corresponding declared files.

## Manifest Contract

`manifest.json` must include:

- `schema_version`
- `bundle_id`
- `created_at_unix`
- `admission_policy_id`
- `journal_tip_digest_before`
- `journal_tip_digest_after`
- `entry_count`
- `accepted_count`
- `rejected_count`
- `quarantined_count`
- `declared_files`
- `declared_file_digests`
- `claim_boundary`
- `non_claims`

The manifest must reject empty identifiers, stale counts, undeclared files,
missing digest entries, absolute logical paths, parent-directory components,
platform path separators, and any claim boundary above local admission-trace
metadata.

## Journal Contract

`journal.json` must serialize the local `AgentAdmissionJournal` shape without
adding stronger semantics. A future validator must check:

- sequence numbers are contiguous from zero;
- every `previous_entry_digest` matches the prior serialized entry digest;
- every `candidate_digest` matches the decision's candidate digest;
- every `decision_digest` matches the serialized decision;
- candidate digests are not replayed within the bundle;
- `journal_tip_digest_before` is either absent for a new journal or matches the
  caller-declared previous tip;
- `journal_tip_digest_after` matches the materialized final entry digest.

Rejected and quarantined decisions must be retained as audit metadata. They
must not expose accepted claim envelopes through any future helper or report.

## Decisions JSONL

`decisions.jsonl` is a review index, not a second source of truth. Each line
must carry only non-secret summary fields derived from `journal.json`:

- candidate id;
- policy id;
- verdict;
- reason codes;
- candidate digest;
- decision digest;
- source artifact digest ids;
- whether an accepted envelope exists.

The validator must reject JSONL rows that drift from `journal.json`, introduce
new claims, include raw provider responses, include credentials, include
network transcripts, or mark rejected/quarantined decisions as accepted.

## Source Digests

`source-digests.json` must list non-secret source artifact identifiers and
SHA-256 digests already bound to admission candidates. It must not embed raw
source artifacts, provider responses, operator credentials, raw attestation
quotes, raw JWKS responses, raw TLS exporters, or benchmark output bodies.

## Non-Claims

`non-claims.md` must explicitly state:

- the bundle is not accepted Evidence Ledger mutation;
- the bundle is not official benchmark evidence;
- the bundle is not official benchmark submission;
- the bundle is not external replay evidence;
- the bundle is not provider evidence;
- the bundle is not proof;
- the bundle is not semantic correctness;
- the bundle is not production readiness;
- the bundle does not create Level2+ evidence;
- the bundle does not populate score axes.

## Output-Root Safety

A future implementation must require a caller-selected output root and reject:

- empty output roots;
- repository root or any path inside the repository root;
- existing files where a directory is expected;
- symlink output roots;
- symlink bundle files;
- absolute declared logical paths;
- parent-directory components;
- undeclared files;
- partial bundles;
- stale digest sidecars;
- repair-overwrite when overwrite is not explicit.

The implementation must stage writes before finalizing the bundle and must
fail closed on any write, readback, or validation drift.

## Redaction

`redaction-report.json` must prove by explicit flags that the bundle does not
retain:

- credentials or secrets;
- raw provider responses;
- raw request bodies;
- raw network transcripts;
- raw attestation quotes;
- raw DCAP collateral;
- raw JWKS or OpenID documents;
- raw TLS exporter values;
- benchmark result bodies;
- accepted Evidence Ledger JSON.

Digest-only references to prior non-secret source artifacts are allowed when
they are already present in the admission candidate source digest set.

## Future Implementation Exit Criteria

A later implementation phase must:

- touch only `crates/hsai-agent-admission`, phase notes, and navigation/status
  docs unless another explicit boundary broadens the slice;
- write and read only the declared `admission-journal/*` files;
- validate digest sidecars and reject stale or partial bundles;
- preserve rejected and quarantined decisions as audit metadata;
- prove that rejected and quarantined decisions cannot export accepted
  envelopes;
- reject raw material retention and credential-shaped content;
- preserve normal test hermeticity;
- keep all claims local and below accepted evidence.

## Non-Goals

This boundary does not permit accepted Evidence Ledger mutation, official
benchmark submission, external replay execution, live backend execution,
provider calls, network access, credentials, generated committed artifacts,
score-axis population, local Intel DCAP implementation, PCCS operation, JWKS
fetching, JWT verification changes, TLS or attested-TLS channel binding,
recoverable-ghost runtime import, formal evidence, Level2+ evidence,
production-readiness claims, semantic-correctness claims, proof claims,
benchmark-evidence claims, or global software-agent uniqueness claims.
