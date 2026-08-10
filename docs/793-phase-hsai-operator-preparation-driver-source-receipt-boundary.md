# Phase 793 HSAI Operator Preparation Driver and Source Receipt Boundary

## Status

Complete as a documentation-first implementation and authority-deferral
boundary.

State slice:
`phase-793-hsai-operator-preparation-driver-source-receipt-boundary`.

Classification: `OperatorPreparationDriverContractResolved`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Verdict

Phase 793 defines the only authorized Phase 794 hermetic driver route. It does
not implement or run a driver, authenticate a real reviewer, acquire a source,
or materialize `P01B`.

The boundary separates three claims that must never be collapsed:

1. a SHA-256 receipt establishes byte correspondence only;
2. a valid detached signature establishes control of one private key only; and
3. only a future externally rooted attempt authorization can establish whether
   that key may approve one exact receipt class for one exact attempt.

No Phase 780 lane closes. Resolved lanes remain `L01-L04,L09`; open lanes
remain `L05-L08,L10-L11`. Historical Phase 779 remains 102 blocked rows and
1,469 blockers without a source-ledger digest.

## Authorized Phase 794 Surface

Phase 794 may change only:

```text
crates/hsai-native-transcript-preparation/Cargo.toml
crates/hsai-native-transcript-preparation/src/lib.rs
crates/hsai-native-transcript-preparation/src/driver.rs
crates/hsai-native-transcript-preparation/tests/operator_preparation_driver.rs
Cargo.lock
docs/794-phase-hsai-hermetic-operator-preparation-driver-implementation.md
README.md
docs/12-task-list.md
docs/90-whole-codebase-validation-report.md
AGENTS.md
```

The only new implementation dependency authorized is:

```toml
p256 = { version = "=0.13.2", features = ["ecdsa"] }
```

It is already locked in the workspace. No network, process, environment,
filesystem write, key-generation, secret-loading, shell, helper, source
acquisition, extraction, compilation, or target-materialization dependency is
authorized.

## Receipt Contract

Phase 794 may implement one strict unsigned receipt body:

```text
schema=hsai-formal-source-receipt-body-v1
receipt_id
attempt_id
subject_class
subject_id
subject_byte_length
subject_sha256
declared_source_authority
declared_source_revision
producer_id
reviewer_id
reviewer_key_id
reviewed_at_utc
not_before_utc
expires_at_utc
decision=accepted
```

Allowed `subject_class` values are closed:

```text
executable_registry_document
operation_order_document
machine_policy
rust_toolchain_manifest
charon_source_tree
aeneas_archive
sandbox_profile
owned_tool
packaged_target
built_target
reviewer_assignments
```

Phase 794 input must contain exactly one receipt for each of these eight input
classes: `executable_registry_document`, `operation_order_document`,
`machine_policy`, `rust_toolchain_manifest`, `charon_source_tree`,
`aeneas_archive`, `sandbox_profile`, and `reviewer_assignments`. `owned_tool`,
`packaged_target`, and `built_target` are Phase 795 output receipt classes and
are rejected as Phase 794 inputs. This prevents a pre-materializer from
accepting declarations for artifacts that do not exist yet.

The eight request bindings are closed:

1. `executable_registry_document` uses request field
   `registry_document_bytes`, subject id `phase787-e83-executable-role-registry`,
   declared source authority `repo:docs/787`, and fixed
   declared source revision `phase787`, byte length `24738`, and
   `REGISTRY_DOCUMENT_SHA256`.
2. `operation_order_document` uses `operation_order_document_bytes`, subject id
   `phase778-operation-order`, declared source authority `repo:docs/778`, and
   the exact compact sorted-key Phase 778 operation-order JSON object with
   declared source revision `phase778` and fixed `OPERATION_ORDER_SHA256`; the
   Phase 778 Markdown file bytes are not this subject.
3. `machine_policy` uses `machine_policy_bytes`, subject id equal to
   `MachinePolicyCandidate.policy_id`, and bytes exactly equal to
   `serde_json::to_vec(parsed_machine_policy)`. The driver parses these bytes,
   requires byte-identical reserialization, and passes that same parsed value to
   the concrete collector. Its declared source revision is the recomputed
   machine-policy SHA-256. Its declared source authority is
   `repo:machine-policy-fixture`; Phase 794 does not authenticate that
   declaration.
4. `rust_toolchain_manifest` uses `rust_toolchain_manifest_bytes`, subject id
   `phase789-rust-toolchain-manifest`, declared source authority
   `fixture:rust-toolchain-manifest`, and declared source revision equal to the
   recomputed subject SHA-256. Its compact JSON fields, in order, are `schema`,
   `channel`, `manifest_url`, `manifest_sha256`,
   `charon_rust_toolchain_sha256`, `rustc_identity`, `rustc_commit`, and
   `ordered_components`; each component has fields `component`, `target`, and
   `xz_sha256`. Its schema is `hsai-formal-rust-toolchain-manifest-v1`. The
   scalar values and exact seven-component order and digests must equal the
   Phase 668 Rust-toolchain table: channel `nightly-2026-06-01`, target
   `aarch64-apple-darwin` except `rust-src` target `*`, rustc identity
   `rustc 1.98.0-nightly (14210df0e 2026-05-31)`, and rustc commit
   `14210df0e27ccd7d9e6a05b8085cbd438e4bbc65`. Missing, extra, duplicate, or
   reordered components reject. Phase 794 has fixture correspondence only;
   Phase 795 must pin real bytes and source authority separately.
5. `charon_source_tree` uses `charon_source_manifest_bytes`: compact JSON for a
   struct with fields `schema`, `commit`, and `ordered_files`; every file entry
   has fields `relative_path`, `byte_length`, and `sha256`. Its schema is
   `hsai-formal-charon-source-manifest-v1`; `commit` is the exact
   `CHARON_SOURCE_COMMIT`; and `ordered_files` is strictly sorted by normalized
   relative path. The list has exactly the five nonempty Phase 670 entries
   `LICENSE.md`, `README.md`, `charon/Cargo.lock`, `charon/Cargo.toml`, and
   `charon/rust-toolchain`, with their exact Phase 670 SHA-256 values and no
   missing, extra, or duplicate path. The subject id is the fixed
   `CHARON_SOURCE_COMMIT`, its declared source authority is
   `fixture:charon-source-manifest`, and its declared source revision is the
   same fixed commit. Raw directory enumeration is not a signed byte
   representation.
6. `aeneas_archive` uses `aeneas_archive_bytes`, subject id
   `aeneas-macos-aarch64.tar.gz`, declared source authority equal to
   `AENEAS_ARCHIVE_URL`, fixed `AENEAS_ARCHIVE_BYTE_LENGTH`, and fixed
   `AENEAS_ARCHIVE_SHA256`; its declared source revision is
   `nightly-2026.07.10-c2015b8`.
7. `sandbox_profile` uses `sandbox_profile_bytes`, subject id
   `phase776-deny-network-sandbox`, declared source authority `repo:constant`,
   declared source revision `phase776`, and exact equality to
   `SANDBOX_PROFILE_BYTES` and `SANDBOX_PROFILE_SHA256`.
8. `reviewer_assignments` uses `reviewer_assignments_bytes`, subject id equal to
   the attempt id, and bytes exactly equal to compact serialization of the
   existing Phase 790 `ReviewerAssignments` struct. Its ordered fields are
   `machine_policy_reviewer_id`, `capture_operator_id`, `fixture_reviewer_id`,
   and `grammar_reviewer_id`; the existing Phase 790 pairwise-separation rules
   apply unchanged. Its declared source authority is
   `fixture:reviewer-assignments`, and its declared source revision is its
   recomputed SHA-256. Phase 794 treats its signature as fixture correspondence
   only; Phase 795 requires a separately rooted authorization.

The parsed reviewer assignments must satisfy the existing Phase 790 rule that
all four principals are nonempty and pairwise distinct. The `machine_policy`
receipt and its verification profile use `machine_policy_reviewer_id`; the
other seven input receipts and their profiles use `fixture_reviewer_id`.
The machine-policy receipt's `producer_id`, `reviewer_id`, and
`reviewed_at_utc` must respectively equal
`machine_policy.review.policy_object_producer_id`,
`machine_policy.review.reviewer_id`, and
`machine_policy.review.reviewed_at_utc`; the embedded review decision must be
`Accepted`. The embedded reviewer must equal
`reviewer_assignments.machine_policy_reviewer_id`.
`capture_operator_id` and `grammar_reviewer_id` are bound for Phase 795/796 use
but grant no Phase 794 capability. Every receipt producer remains distinct from
its mapped reviewer.

Every receipt's `subject_id`, `declared_source_authority`,
`declared_source_revision`, length, and digest must equal its class binding.
These source fields are signed declarations, not authenticated authorities. A
second byte object for any typed request field is forbidden.

Production validation uses only these closed bindings. Because the pinned
Aeneas archive is not committed and acquisition is forbidden, the Phase 794
hermetic suite may use a private `cfg(test)` binding table with tiny deterministic
subject bytes. That table and its driver helper are not public and are absent
from non-test builds. Production success still requires the exact constants
above; tests may not weaken, replace, or inject production bindings through the
public API.

Production length bounds are checked before hashing or parsing: the Aeneas
archive must equal `AENEAS_ARCHIVE_BYTE_LENGTH`; the registry document must be
`24738` bytes; the sandbox profile must equal `SANDBOX_PROFILE_BYTES.len()`;
the operation-order document, machine policy, Rust manifest, and reviewer
assignments are each at most 1 MiB; and the Charon source manifest is at most 64
MiB. The complete request is rejected before cryptographic work when any field
exceeds its class bound.

The body uses compact UTF-8 JSON in declared struct-field order, no maps,
strict unknown-field rejection, sorted unique lists, and integer-only lengths.
The signature preimage is:

```text
"hsai-native-transcript-preparation:source-receipt-signature:v1\0"
|| serde_json::to_vec(unsigned_body)
```

The detached ES256 signature is exactly 64 raw `r || s` bytes encoded as 128
lowercase hexadecimal characters. The compressed SEC1 public key is exactly 33
bytes encoded as 66 lowercase hexadecimal characters. No DER, PEM, JWT, JWK,
base64, alternate curve, alternate hash, or encoding fallback is accepted.

ID fields use ASCII `[a-z0-9][a-z0-9._:-]{0,127}`. Declared source-authority
fields are nonempty printable ASCII with no whitespace or control bytes and a
512-byte maximum; class bindings above further require exact values. Digests,
hex, and key ids are lowercase. Timestamps use exactly 20-byte UTC
`YYYY-MM-DDTHH:MM:SSZ` form with calendar validation; offsets, fractions, leap
seconds, and normalization are rejected.

The wire identities and digest preimages are exact:

```text
SourceReceiptEnvelope v1 fields:
schema, unsigned_body, signature_hex
schema value: hsai-formal-source-receipt-envelope-v1
digest domain:
"hsai-native-transcript-preparation:source-receipt-envelope:v1\0"
|| serde_json::to_vec(envelope)

FixtureVerificationProfile v1 fields:
schema, profile_id, attempt_id, reviewer_id, key_id,
compressed_sec1_key_hex, key_sha256, allowed_subject_classes,
not_before_utc, expires_at_utc
schema value: hsai-formal-fixture-verification-profile-v1
digest domain:
"hsai-native-transcript-preparation:fixture-verification-profile:v1\0"
|| serde_json::to_vec(profile)

PreparationDriverRequest v1 fields:
schema, attempt_id, evaluation_time_utc, machine_policy,
registry_document_bytes, operation_order_document_bytes,
machine_policy_bytes, rust_toolchain_manifest_bytes,
charon_source_manifest_bytes, aeneas_archive_bytes,
sandbox_profile_bytes, reviewer_assignments_bytes,
ordered_receipts, ordered_verification_profiles
schema value: hsai-formal-preparation-driver-request-v1

SubjectIdentity v1 fields:
schema, subject_class, subject_id, byte_length, sha256
schema value: hsai-formal-preparation-subject-identity-v1

PreparationDriverRequestIdentity v1 fields:
schema, request_schema, attempt_id, evaluation_time_utc,
machine_policy_sha256, ordered_subject_identities,
ordered_receipt_sha256, ordered_verification_profile_sha256
schema value: hsai-formal-preparation-driver-request-identity-v1
digest domain:
"hsai-native-transcript-preparation:driver-request:v1\0"
|| serde_json::to_vec(request_identity)

ExecutableIdentityFact v2 digest domain:
"hsai-native-transcript-preparation:executable-fact:v2\0"
|| serde_json::to_vec(fact)

PreparationDriverDecision v1 fields:
schema, request_identity_sha256, ordered_receipt_sha256,
ordered_verification_profile_sha256, ordered_host_fact_sha256,
declared_evaluation_time_utc, fixture_correspondence_valid,
materialization_authorized, capture_authorized, ordered_issues
schema value: hsai-formal-preparation-driver-decision-v1
digest domain:
"hsai-native-transcript-preparation:driver-decision:v1\0"
|| serde_json::to_vec(decision)

PreparationDriverIssue v1 fields:
schema, stage, subject_class, code
schema value: hsai-formal-preparation-driver-issue-v1

PreparationDriverPreIdentityRejection v1 fields:
schema, stage, subject_class, code,
materialization_authorized, capture_authorized
schema value: hsai-formal-preparation-driver-pre-identity-rejection-v1
```

All named structures are deny-unknown-fields structs. All ordered receipt and
subject arrays use the eight-class order above. Each profile's allowed classes
are the unique subsequence of that same order, and profiles are strictly sorted
by key id. Host facts use `HostExecutableRole::ALL`. Issues use fixed validation
stage, then eight-class, then code order. The closed stage order is
`request_shape`, `subject_bounds`, `subject_binding`, `profile_binding`,
`signature`, `collector`, `fact_binding`, `decision`. A global issue uses a null
`subject_class`. The closed code order is:

```text
invalid_schema
invalid_identifier
invalid_timestamp
invalid_census
invalid_order
duplicate_entry
length_out_of_bounds
length_mismatch
digest_mismatch
binding_mismatch
parse_failed
reserialization_mismatch
profile_missing
profile_not_yet_valid
profile_expired
window_mismatch
producer_reviewer_collision
decision_not_accepted
key_encoding_invalid
key_digest_mismatch
signature_encoding_invalid
signature_high_s
signature_invalid
collector_failed
fact_role_mismatch
fact_policy_mismatch
fact_entry_mismatch
fact_platform_mismatch
fact_digest_rejected
internal_invariant
```

Maps, duplicate entries, alternate ordering, omitted booleans, and
reserialization drift reject. Code ordering is declaration order above, not
lexicographic order.

The request identity is built only after every subject length and SHA-256 has
been recomputed. `machine_policy_sha256` is the value returned by the existing
domain-separated free function
`machine_policy_sha256(&MachinePolicyCandidate)`. The compact identity prevents
raw archive bytes from being expanded into a JSON integer array solely to
compute a request digest.

The three plural SHA-256 fields in the decision are vectors of lowercase
64-character digest strings, never aggregate digests. Receipt digests contain
exactly eight entries in subject-class order. Verification-profile digests
contain one through eight entries in strict key-id order. Host-fact digests
contain exactly eight entries in `HostExecutableRole::ALL` order on success;
on failure they contain only the successfully collected prefix, or are empty
when collection did not start. Structural and cryptographic validation completes
before collection, so no fact digest exists for a request rejected at an earlier
stage. Every returned failure decision has
`fixture_correspondence_valid=false`, both authorization booleans false, and at
least one ordered issue.

The public driver returns
`Result<PreparationDriverDecision, PreparationDriverPreIdentityRejection>`.
Request schema, identifier, timestamp, census, order, duplicate-entry, and
subject-bound failures occur before complete subject hashing and therefore use
the typed rejection path. Its `stage` is only `request_shape` or
`subject_bounds`; its `code` is only `invalid_schema`, `invalid_identifier`,
`invalid_timestamp`, `invalid_census`, `invalid_order`, `duplicate_entry`, or
`length_out_of_bounds`; and both authorization booleans are always false. It
has deliberately no digest and cannot be serialized as a driver decision.
Request-shape rejections use null `subject_class`; a subject-bound rejection
uses that subject's exact closed class value. Golden tests cover both encodings.
After all bounded subject hashes and the request identity exist, every later
failure returns a digest-bound decision. Raw JSON deserialization failure occurs
before the typed public driver and produces neither type.

The receipt envelope binds the unsigned body and signature. Public-key SHA-256
is computed over the exact 33 decoded compressed SEC1 bytes, not hexadecimal
text. The key itself is supplied through a separate fixture-verification input;
embedding or naming a key in the receipt does not authorize it.

## Fixture Verification and Deferred Authority

The future driver accepts in-memory `FixtureVerificationProfile` values
containing exact key id, SEC1 key bytes, key SHA-256, expected reviewer id,
allowed subject classes, attempt id, and validity window. Profiles are unique by
key id; multiple receipts may map to one profile. It rejects:

- missing, duplicate, wildcard, or fallback keys;
- key-id, key-digest, reviewer-id, attempt-id, class, or time-window mismatch;
- producer and reviewer identity equality;
- pending or rejected decisions;
- expired, not-yet-valid, malformed, high-S, or invalid signatures; and
- a receipt body whose declared bytes do not match the independently supplied
  subject bytes.

Phase 794 tests may use only deterministic fixture keys. A verification profile
proves correspondence to a caller-selected fixture key; it is not a trust root,
reviewer authority, or self-authorization check. Phase 795 may authorize real
materialization only after a separate external attempt record pins exact
non-secret reviewer public-key digests and subject classes. Phase 794 cannot
create or validate that external authorization.

Validity windows are closed and use second-resolution UTC comparisons. For each
receipt/profile pair the driver requires:

```text
profile.not_before_utc
<= receipt.not_before_utc
<= receipt.reviewed_at_utc
<= request.evaluation_time_utc
<  receipt.expires_at_utc
<= profile.expires_at_utc
```

Both windows therefore use inclusive starts and exclusive ends. Equal start
values and equal expiry values are allowed; an evaluation exactly at either
expiry is rejected. Reversed or zero-length windows reject. The request's
caller-declared evaluation time remains fixture input, not a trusted clock.

## Hermetic Driver Contract

The Phase 794 public driver accepts exactly one in-memory value:

```text
PreparationDriverRequest v1
```

Every typed object, exact subject byte object, receipt envelope, fixture
verification profile, attempt id, and evaluation time is a field of that
request. No duplicate top-level argument is accepted. In particular, the
request's `machine_policy` must be the same value obtained by strict parsing and
byte-identical compact reserialization of `machine_policy_bytes`.

`PreparationDriverRequest` is a pre-materialization request, not a
`PreparationCandidate`. It contains no owned-tool receipt, target receipt,
target bytes, output root, handoff, or materialization result. Phase 795 may
construct a full `PreparationCandidate v2` only after producing and validating
those outputs.

Its order is fixed:

1. validate only the request schema, attempt id, evaluation timestamp, exact
   eight-class census and order, one-to-one subject/receipt sets, unique
   verification-profile ordering, and all subject length bounds;
2. recompute every bounded subject length and SHA-256, compute receipt and
   profile digests, and construct the compact request identity;
3. validate the machine-policy parse and byte-identical reserialization, all
   fixed subject bindings and digests, sandbox bytes, and Phase 792 state
   identity;
4. validate every fixture-profile/key identity and validity window;
5. verify every detached ES256 signature over the exact unsigned body;
6. enforce producer/reviewer separation and accepted decisions;
7. invoke the concrete Phase 792 `collect_executable_identity_fact` function
   once for each of the eight host roles in `HostExecutableRole::ALL` order;
8. require each fresh fact to bind the request policy, entry, declared
   platform, internally observed OS/architecture, and accepted digest;
9. compute one domain-separated driver decision digest; and
10. return `fixture_correspondence_valid=true` only when every check succeeds,
    while always returning `materialization_authorized=false` and
    `capture_authorized=false`.

The public production entrypoint has no collector or fact parameter. A private
test-only helper may inject a collector closure for deterministic failure
coverage, but that helper is neither public nor compiled into non-test builds.
Duplicate calls, missing roles, reordered roles, or facts produced before
receipt validation reject the decision.

The Phase 794 evaluation time is explicitly caller-declared hermetic input. It
can test validity-window logic but cannot establish real freshness. Any Phase
795 authorization must bind an independently recorded attempt time and reject
a driver decision whose declared time or validity window does not match it.

## Freshness and Use Boundary

Phase 794 facts are preflight observations, not launch authority. Phase 795
must verify the same receipt and externally authorized key objects again,
recollect each host fact immediately before first use, bind the post-use
identity, and reject any policy, key, source, path, metadata, or digest drift.
It may not reuse a Phase 794 fact as proof that an executable remains unchanged.

The Phase 794 decision contains no output root, command argv, executable step,
network capability, acquisition instruction, or materialization callback.

## Required Phase 794 Tests

The hermetic suite must cover:

- one complete deterministic eight-class private test-binding decision and
  stable decision digest, plus proof that production bindings are not
  injectable;
- golden compact-JSON bytes and digest vectors for every v1 envelope, profile,
  request identity, fact, and decision domain, plus golden pre-identity
  rejection JSON;
- exact machine-policy parse, byte-identical reserialization, receipt binding,
  and collector-input identity;
- mutation of every unsigned receipt field and subject byte object;
- malformed key/signature hex, wrong curve point, wrong key, wrong signature,
  high-S signature, and exact signature-preimage domain separation;
- unknown, duplicate, wildcard, expired, future, wrong-attempt, and wrong-class
  fixture profiles;
- many-receipts-to-one-profile acceptance and duplicate-key-profile rejection;
- producer/reviewer collision and non-accepted decisions;
- missing, duplicate, reordered, stale-policy, stale-entry, wrong-platform,
  rejected-digest, and collector-error host facts;
- proof that no caller-supplied `ExecutableIdentityFact` input exists;
- proof that collector injection is private, test-only, and absent from the
  non-test public API;
- rejection of owned-tool and target receipt classes as Phase 794 inputs;
- proof that both authorization booleans remain false on success, digest-bound
  failure, and pre-identity rejection;
- source scans for process, network, environment, filesystem-write, secret,
  shell, helper, and materialization surfaces; and
- current toolchain plus locked Rust 1.74 tests.

## Claim Boundary

Phase 793 is a source-receipt and hermetic-driver design boundary. It is not an
implemented driver, cryptographic review of a real source, authenticated real
reviewer, operator approval, machine policy, durable machine observation,
source acquisition, target build, target receipt, preparation handoff, `P01B`
materialization, native transcript capture, fixture authority, grammar,
source-ledger digest, plan v2, executor binding, backend execution, Lean/SMT/Z3
or COBALT run, proof artifact, checker transcript, accepted evidence, Level2+,
score axis, semantic correctness, production readiness, SOTA, breakthrough,
full security, external audit, or action authority.
