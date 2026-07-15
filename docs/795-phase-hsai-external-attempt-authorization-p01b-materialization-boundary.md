# Phase 795 HSAI External Attempt Authorization and P01B Materialization Boundary

## Status

Complete as a documentation-first boundary; stopped before external
authorization validation, plan construction, or materialization.

State slice:
`phase-795-hsai-external-attempt-authorization-p01b-materialization-boundary`.

Classification:
`ExternalAttemptAuthorizationContractFrozenP01BMaterializationStopped`.

Execution status: `StoppedDocumentationOnly`. Evidence ceiling:
`Level1LocalReplayOrLower`.

## Verdict

Phase 795 does not perform the conditional `P01B` materialization previously
assigned to this phase. Phase 794 proves only correspondence to caller-selected
fixture keys and deliberately returns `materialization_authorized=false`. The
repository still has no independently supplied reviewer-key policy, signed
attempt authorization, exact materialization plan, accepted owned-tool or target
receipts, or preparation handoff.

Additional execution prerequisites are unresolved. The Phase 792
collector closes safe observation but drops its verified descriptors, so a later
pathname launch does not prove that the observed inode is the executed inode.
Phase 789 freezes stage order but not every producer argv, cwd, replacement
environment, child identity, bound, or outcome. The Aeneas archive also has no
P01B-specific exact member inventory and header grammar, while Cargo/Rustc build
children and SDK/linker/loader trust roots are not reconciled with the closed
role set. No concrete trusted reservation-time source, independently
authenticated anti-rollback journal checkpoint, recovery protocol, or durable
audit-root census is frozen either. Materialization remains forbidden until all
of these are closed.

Allowing the Phase 794 caller to supply both verification keys and authority
would be self-authorization. Reusing its host facts as launch-time facts would
also violate the Phase 793 freshness rule. Phase 795 therefore freezes the
missing trust, plan, write, readback, and cleanup contracts and stops without
creating authority.

No Phase 780 lane closes. Resolved lanes remain `L01-L04,L09`; open lanes remain
`L05-L08,L10-L11`. Historical Phase 779 remains 102 blocked rows and 1,469
blockers without a source-ledger digest.

## Closed Trust Inputs

A future authorization validator may accept exactly five in-memory byte objects:

1. one operator-provisioned `P01bTrustAnchor v1`;
2. one canonical Phase 794 `PreparationDriverRequest`;
3. one canonical Phase 794 `PreparationDriverDecision`;
4. one externally supplied `P01bReviewerKeyPolicyEnvelope v1`; and
5. one externally supplied `P01bAttemptAuthorizationEnvelope v1`.

The driver request and decision must be revalidated, not trusted because they
deserialize. The decision must have `fixture_correspondence_valid=true`, empty
issues, exactly eight receipt digests, one through eight profile digests, exactly
eight host-fact digests, and both authorization booleans false. Its recomputed
request identity, receipt/profile digests, declared evaluation time, and decision
digest must equal the values bound by the external authorization.

Every Phase 794 verification profile must project exactly from one accepted
reviewer-key policy entry carrying `phase794_input_review`: reviewer id, key id,
decoded public-key bytes and digest, allowed input subject classes, and validity
window all match. Those profile key ids equal the receipt key-id set. Separate
policy entries carrying `p01b_attempt_authorize`, `p01b_materialize`, or
`p01b_output_review` are not Phase 794 verification profiles and cannot verify
an input receipt. No key or capability is inferred from use. The external
authorization cannot bless a profile, authorizer, operator, or output reviewer
that the accepted policy does not independently authorize for that exact role.

Phase 797 may apply these checks only to test or caller-supplied bytes and return
`static_contract_valid`; it always returns
`runtime_authorization_accepted=false`. Only Phase 798 may combine a byte-
identical static result with trusted time, exclusive journal reservation, and
fresh host facts. No Phase 797 output is a live authorization.

The trust anchor and two external envelopes are non-secret public authorization
inputs. They are
not generated, edited, repaired, or selected by the materializer. The future
operator invocation must pass their exact absolute paths and expected SHA-256
digests through an explicit invocation contract. No repository default,
environment lookup, home-directory search, wildcard, nearest key, fallback key,
embedded receipt key, or network key discovery is allowed.

`P01bTrustAnchor v1` has compact ordered fields `schema`, `trust_root_id`,
`issuer_id`, `issuer_key_id`, `compressed_sec1_key_hex`, `key_sha256`,
`allowed_scope`, `not_before_utc`, and `expires_at_utc`. `allowed_scope` is
exactly `p01b-reviewer-key-policy-only`. Its complete canonical digest is pinned
independently by the operator invocation and bound by the attempt authorization.

## Reviewer Key Policy Wire

The unsigned policy body schema is
`hsai-formal-p01b-reviewer-key-policy-v1`. Its compact JSON fields, in order,
are:

```text
schema
policy_id
authority_scope
attempt_id
issued_at_utc
not_before_utc
expires_at_utc
policy_issuer_id
policy_issuer_key_id
ordered_reviewer_keys
```

`authority_scope` is exactly `p01b-preparation-only`. Each ordered reviewer-key
entry has:

```text
reviewer_id
key_id
compressed_sec1_key_hex
key_sha256
allowed_capabilities
allowed_subject_classes
not_before_utc
expires_at_utc
```

The key order is strict `key_id` order. Key ids and key digests are unique.
Compressed keys are exact P-256 SEC1 compressed points encoded as 66 lowercase
hexadecimal characters. The digest is SHA-256 over the decoded 33 key bytes.
`allowed_capabilities` is a nonempty unique subsequence in this exact order:

```text
phase794_input_review
p01b_attempt_authorize
p01b_materialize
p01b_output_review
p01b_journal_checkpoint
p01b_time_observe
```

Allowed subject classes are a unique subsequence of:

```text
executable_registry_document
operation_order_document
machine_policy
rust_toolchain_manifest
charon_source_tree
aeneas_archive
sandbox_profile
reviewer_assignments
owned_tool
packaged_target
built_target
```

Input, authorizer, materializer, and output-review entries require a nonempty
set. The checkpoint/time entry requires an empty set because its capabilities
authorize journal/time wires, not source subjects. Any other empty set rejects.

The envelope schema is `hsai-formal-p01b-reviewer-key-policy-envelope-v1` with
ordered fields `schema`, `unsigned_policy`, `policy_signature_hex`. Its low-S
raw ES256 signature preimage is:

```text
"hsai-native-transcript-preparation:p01b-reviewer-key-policy:v1\0"
|| serde_json::to_vec(unsigned_policy)
```

The policy issuer key is an operator-provisioned trust root outside this
repository. Phase 795 does not define a universal identity provider or claim
that a local key proves a legal or organizational identity. A future
implementation must require the operator to pin the exact non-secret issuer key
digest before validation and record that digest in the attempt report.

## Attempt Authorization Wire

The unsigned attempt body schema is
`hsai-formal-p01b-attempt-authorization-v1`. Its compact JSON fields, in order,
are:

```text
schema
authorization_id
attempt_id
issued_at_utc
not_before_utc
expires_at_utc
authorizer_id
authorizer_trust_root_id
trust_anchor_sha256
authorizer_key_id
authorizer_public_key_sha256
materialization_operator_id
materialization_operator_key_id
materialization_operator_public_key_sha256
machine_policy_producer_id
machine_policy_reviewer_id
capture_operator_id
fixture_reviewer_id
grammar_reviewer_id
independent_attempt_time_utc
one_shot_nonce
replay_journal_namespace
replay_journal_storage_identity_sha256
replay_journal_checkpoint_authority_sha256
replay_journal_checkpoint_key_id
replay_journal_checkpoint_public_key_sha256
replay_journal_expected_sequence
replay_journal_expected_head_sha256_or_null
trusted_time_source_identity_sha256
reviewer_key_policy_sha256
driver_request_identity_sha256
driver_decision_sha256
ordered_receipt_sha256
ordered_verification_profile_sha256
ordered_host_fact_sha256
machine_policy_sha256
registry_document_sha256
reviewer_assignments_sha256
operation_order_sha256
preparation_contract_sha256
preparation_root
capture_root
attempt_audit_root
capture_root_must_be_absent
ordered_input_authorizations
ordered_output_authorizations
claim_boundary
explicit_nonclaims
decision
```

`decision` is exactly `accepted`. The eight input authorizations use exact
`SourceSubjectClass::INPUTS` order. Each has ordered fields:

```text
subject_class
subject_id
subject_byte_length
subject_sha256
declared_source_authority
declared_source_revision
source_receipt_sha256
reviewer_id
reviewer_key_id
```

Each output authorization has ordered fields:

```text
subject_class
subject_id
destination_relative_path
source_authority
source_revision
producer_id
producer_operation_id
reviewer_id
reviewer_key_id
```

The output list is exact and ordered: `RUSTC_EXE`, `CARGO_EXE`; packaged
`aeneas`, `charon`, `charon-driver`, `libgmp.10.dylib`; then built `charon` and
`charon-driver`. Subject classes are respectively `owned_tool`,
`packaged_target`, and `built_target`. Paths are the exact Phase 789 handoff
paths. Packaged source authority is the pinned Aeneas release; built source
authority is exact Charon commit
`909ff09ad0f144f83d354f2c3d26f631fb9f8e9a` and producer ordinal `073`.
Unknown or additional output authorization rejects.

`independent_attempt_time_utc` is the authorizer's planned attempt time, not a
substitute for actual reservation time. `materialization_operator_id` is the
exact `producer_id` for all eight output artifacts. Its exact key id and public-
key digest identify one policy entry carrying only the required
`p01b_materialize` capability. The operator is distinct from every source or
policy producer, input or output reviewer, issuer, and authorizer.
`one_shot_nonce` is a 32-byte lowercase hexadecimal replay identity.
`preparation_contract_sha256` binds the complete
closed Phase 796 operation definitions, not a prose document or mutable source
path. Both roots equal the Phase 789 literals and
`capture_root_must_be_absent=true`. `attempt_audit_root` is exactly
`${preparation_root}.audit-${one_shot_nonce}`, is absent initially, is outside
git and protected roots, and is the only durable destination for attempt,
journal-checkpoint, cleanup, and failure records that are not handoff payloads.

The five signed actor labels after the materialization-operator key are not
capabilities. Phase 797 uses them only for static collision rejection. Phase 798
must project them exactly from the digest-bound canonical machine-policy and
reviewer-assignment payloads before reservation-dependent production; a label
that does not project is rejected. `capture_operator_id` remains a separation
identity only and receives no capture capability or capture authority.

The checkpoint-authority digest, key id, and public-key digest project exactly
from one separate reviewer-policy entry carrying exactly
`p01b_journal_checkpoint` and `p01b_time_observe`. That principal is distinct from every other actor.
Its signed checkpoints authenticate journal sequence/head transitions; a local
record hash without its signature is not a checkpoint. The same key signs the
Phase 796 time-source observations so the journal and time sequence share one
authenticated monotonic authority.

The envelope schema is `hsai-formal-p01b-attempt-authorization-envelope-v1`
with ordered fields `schema`, `unsigned_authorization`,
`authorization_signature_hex`. Its low-S raw ES256 signature preimage is:

```text
"hsai-native-transcript-preparation:p01b-attempt-authorization:v1\0"
|| serde_json::to_vec(unsigned_authorization)
```

The authorizer key must occur exactly once in the accepted reviewer-key policy,
bind the same reviewer id and attempt id, carry `p01b_attempt_authorize`, and
authorize all eleven input/output classes used by the attempt. It cannot carry
`phase794_input_review`, `p01b_materialize`, `p01b_output_review`,
`p01b_journal_checkpoint`, or `p01b_time_observe`. It is
authenticated only through that policy's
signature under the separately operator-pinned trust anchor; a key named solely
inside the attempt envelope grants no authority. The policy issuer, attempt
authorizer, machine-policy producer, machine-policy reviewer, materialization
operator, capture operator, fixture reviewer, grammar reviewer, and all eight
output reviewers are pairwise distinct. Every output reviewer carries only
`p01b_output_review`, occurs exactly once, and is authorized for exactly one
output subject. The materialization operator carries `p01b_materialize` and
cannot carry a review or authorization capability.
The authorizer key digest
must equal its exact reviewer-policy entry and the attempt's
`authorizer_trust_root_id` must equal the trust anchor id. A future boundary may
relax no separation without an explicit threat-model revision and independent
review.

## Time and Replay Rules

All timestamps use the strict Phase 794 UTC grammar. Policy, authorization,
receipt, and key windows have inclusive starts and exclusive ends. The durable
journal records a trusted `reservation_observed_at_utc` from the exact Phase 796
platform time-source contract plus a monotonic clock id and tick value. It also
loads the previous durable wall-clock high-water mark before reservation. It
requires:

```text
policy.not_before_utc
<= authorization.issued_at_utc
<= authorization.not_before_utc
<= reservation_observed_at_utc
<  authorization.expires_at_utc
<= policy.expires_at_utc
```

The policy issuer id and key id must equal the trust anchor issuer id and key
id. The policy signature must verify under that exact anchor key, and acceptance
also requires:

```text
anchor.not_before_utc
<= policy.issued_at_utc
<= policy.not_before_utc
<= authorization.issued_at_utc
<= reservation_observed_at_utc
<  policy.expires_at_utc
<= anchor.expires_at_utc
```

`reservation_observed_at_utc` is the actual `attempt_started_at_utc`. It must be
at or after the prior durable high-water mark and within 300 seconds after the
signed `independent_attempt_time_utc`; a future planned time is rejected. The
driver declared evaluation time must be no later than reservation and no more
than 300 seconds earlier. Every receipt and reviewer-key window must still
contain reservation time. Authorization
ids and one-shot nonces are single-use within the authorization-bound journal
namespace and storage identity. The expected sequence and head digest must
match an independently authenticated append-only compare-and-swap checkpoint
whose authority digest equals `replay_journal_checkpoint_authority_sha256`.
Exclusive reservation advances that checkpoint atomically before any mutable
operation. A local hash chain, filesystem lock, restored snapshot, caller-
selected replacement journal, or truncatable file is insufficient. Missing
journal support, an already reserved or consumed id or nonce, a
reversed window, wall-clock rollback below the high-water mark, monotonic clock
regression within one clock id, or an authorization older than the bound driver
decision rejects before plan construction.

Only a checkpoint-authority attested genesis uses expected sequence zero and a
null expected head. Every non-genesis authorization uses a positive sequence and
non-null expected head. The compare-and-swap transition consumes exactly that
pair and returns the reservation record digest plus new authenticated head;
either value drifting rejects.

Every compare-and-swap response is a canonical `P01bJournalCheckpointEnvelope
v1` signed by the policy-bound checkpoint-authority key. The reservation
checkpoint is retained in both handoff provenance and `AUDIT_ROOT`; the terminal
checkpoint is retained in `AUDIT_ROOT`. Independent verification requires both
envelopes and their hash-chain relationship.

The success route uses exactly thirteen canonical observations in this order:
`reservation`, `packet_production`, `review_receipt_01` through
`review_receipt_08`, `completion`, `terminal_success`, and
`acceptance_commit`. A failure route retains every success-prefix observation
already reached, then exactly one `terminal_failure`; it has no later success or
commit observation. Observation ids are unique, every observation after
reservation binds the previous envelope digest, monotonic ticks strictly
increase within one clock id, and all observations bind the one Phase 796 time-
source identity. Each digest field elsewhere in this contract is the digest of
the corresponding retained envelope, not a bare timestamp or caller label.

The journal reserves the authorization id and nonce before the first mutable
operation and ends in exactly one durable state: `consumed_success` or
`consumed_failure`. Reservation uses exclusive compare-and-append semantics;
two contenders cannot observe and advance the same checkpoint. A failed or
interrupted attempt cannot retry the same id or nonce. Recovery treats every
durable `reserved` record as consumed, removes only its authorization-bound
attempt roots, and appends `consumed_failure`. Reservation, checkpoint,
transition, recovery, or durability failure stops the attempt.

This phase does not implement the journal. Therefore no live authorization can
be accepted yet.

The authorizer-key window must contain both authorization issuance and
reservation. Each output-reviewer key remains valid through its retained review-
receipt observation. The checkpoint-authority key remains valid through the
terminal checkpoint and acceptance-commit time observation. The materialization-
operator key, policy window, and authorization window remain valid through the
commit signature and trusted commit observation. Retained trusted-clock
observations enforce this total order:

```text
reservation_observed_at_utc
<= packet.produced_at_utc
<= packet_observed_at_utc
<= each review.reviewed_at_utc
<= each review_received_at_utc
<= completion_observed_at_utc
<= terminal_success_observed_at_utc
<= terminal_checkpoint.checkpointed_at_utc
<= acceptance_commit.committed_at_utc
<= acceptance_commit_observed_at_utc
<  authorization.expires_at_utc
<= policy.expires_at_utc
<= anchor.expires_at_utc
```

Packet production, each review receipt, and completion observations bind the
exact Phase 796 trusted-time-source identity and observation digest. Signed
timestamps alone never establish current time. Expiry is completion-bound, not
start-only.

## Immediate Host-Fact Recollection

Phase 794 facts are preflight observations only. The future Phase 798
materializer, not the pure Phase 797 template constructor, must call the
concrete Phase 792 collector again for all eight host roles after durable replay
reservation and immediately before instantiating the runtime plan and first
producer step. Recollected facts must equal the authorized policy, entry,
platform, path, owner, mode, metadata, and executable digest bindings. Their
eight ordered digests are bound into the runtime plan instance.

Every executable used by a materializer is recollected again immediately before
its first invocation and rechecked immediately after its final invocation.
Owned `RUSTC_EXE` and `CARGO_EXE` identities require their accepted extraction
receipts before use. No Phase 794 host-fact digest substitutes for these checks.
Any change rejects the attempt and invokes cleanup.

Facts are four disjoint typed sets: eight host-executable roles in the exact
Phase 789 order; two owned-tool roles `RUSTC_EXE`, `CARGO_EXE`; every build-child
executable role in the exact Phase 796 order; and eight produced-artifact
subjects in output-authorization order. Executable roles have pre-use and post-
use facts. Produced artifacts have one post-production fact and are never given
a fictional pre-use executable fact. No fact may occur in two sets.

## Non-Executing Preparation Plan Boundary

Phase 797 may implement only a hermetic static authorization validator and
deterministic `P01bPreparationPlanTemplate v1` constructor. It has no trusted
clock, journal, host observation, or mutation input and therefore cannot assert
freshness, reserve an authorization, or create a runtime plan. The template
schema is `hsai-formal-p01b-preparation-plan-template-v1` with ordered fields:

```text
schema
template_id
attempt_id
authorization_envelope_sha256
reviewer_key_policy_sha256
driver_request_identity_sha256
driver_decision_sha256
preparation_contract_sha256
preparation_root
capture_root
attempt_audit_root
replay_journal_namespace
replay_journal_storage_identity_sha256
replay_journal_checkpoint_authority_sha256
replay_journal_expected_sequence
replay_journal_expected_head_sha256_or_null
trusted_time_source_identity_sha256
ordered_bootstrap_operations
ordered_runtime_success_operations
ordered_failure_operations
ordered_recovery_operations
claim_boundary
explicit_nonclaims
```

Phase 798 may instantiate `P01bPreparationPlan v1` only after trusted time
observation, exclusive durable reservation, and fresh fact recollection. Its
ordered fields are:

```text
schema
plan_id
template_sha256
attempt_id
reservation_record_sha256
reservation_observed_at_utc
replay_journal_reserved_sequence
replay_journal_reserved_head_sha256
ordered_pre_use_host_executable_fact_sha256
preparation_root
capture_root
attempt_audit_root
ordered_runtime_success_operations
ordered_failure_operations
ordered_recovery_operations
claim_boundary
explicit_nonclaims
```

The static template authorizes these exact seven bootstrap operations. They are
the only operations permitted before the runtime plan exists:

```text
load-and-verify-journal-head
observe-trusted-reservation-time
validate-external-authorization
reserve-one-shot-authorization
create-attempt-audit-root
recollect-host-identities
instantiate-preparation-plan
```

The instantiated runtime plan begins after its own construction and contains
these exact 33 success operations, preserving global ordinals 008 through 040:

```text
create-staging-root
acquire-rust-manifest
acquire-rust-toolchain
receipt-owned-rustc
receipt-owned-cargo
acquire-charon-source
acquire-aeneas-archive
validate-aeneas-archive
extract-aeneas-staging
receipt-packaged-aeneas
receipt-packaged-charon
receipt-packaged-charon-driver
receipt-packaged-libgmp
build-charon-ordinal-073
receipt-built-charon
receipt-built-charon-driver
close-network-capability
recollect-post-use-host-identities
materialize-handoff-payloads
construct-payload-manifest
construct-signed-output-review-packet
collect-eight-output-reviews
validate-eight-output-reviews
construct-preparation-candidate
readback-handoff-payloads
construct-validation-and-nonclaims
construct-handoff-manifest
construct-success-decision
publish-final-root-atomically
write-pending-success-audit-record
finalize-replay-journal-success
write-final-attempt-audit-record
write-authenticated-acceptance-commit
```

A rejection before successful reservation performs no mutable operation and
returns no runtime plan. Every failure after reservation but before a durable
`consumed_success` transition branches into this exact ordered eight-operation
cleanup state machine from the last successfully completed operation:

```text
terminate-active-process-group
close-network-capability-on-failure
remove-attempt-created-staging-or-final-root
verify-attempt-created-root-absence
write-failure-decision-if-audit-root-exists
finalize-replay-journal-failure
write-final-attempt-audit-record
verify-audit-and-journal-durability
```

After `finalize-replay-journal-success` returns durably, no failure transition is
legal. Interruption before the acceptance commit instead uses this exact eight-
operation idempotent recovery state machine:

```text
load-consumed-success-journal-checkpoint
verify-published-root-and-success-decision
verify-pending-success-audit-record
construct-final-attempt-audit-record
publish-final-attempt-audit-record-if-absent
verify-final-attempt-audit-durability
construct-authenticated-acceptance-commit
publish-and-verify-acceptance-commit-if-absent
```

Every operation contains a closed kind, exact executable-role sequence, exact
argv template, cwd template, replacement environment, network capability,
input/output artifact ids, timeout, stdout/stderr retention policy, and cleanup
effect. Phase 797 may not guess unresolved argv, tool identities, archive member
allowlists, build environment, or output paths. It returns no template when any field
is unresolved and has no process, network, filesystem-write, or authorization-
consumption API. `template_id` is lowercase SHA-256 over
`"hsai-native-transcript-preparation:p01b-template-id:v1\0"` followed by the
canonical template body with `template_id` omitted. Runtime `plan_id` uses the
parallel `p01b-plan-id:v1` domain over the canonical runtime plan body with
`plan_id` omitted; this derivation is not recursive.

## Future Materializer Safety Contract

A later separately authorized implementation may consume only one byte-identical
static template for the seven bootstrap operations and the one runtime plan that
template deterministically authorizes. It must enforce all of these rules:

- final `PREPARATION_ROOT` and `CAPTURE_ROOT` remain absent while the nonce-bound
  sibling `STAGING_ROOT=${PREPARATION_ROOT}.staging-${one_shot_nonce}` is created
  exclusively with mode `0700`; the separate nonce-bound `AUDIT_ROOT` is also
  created exclusively with mode `0700`; all four paths are outside repository
  and protected roots and have no symlink ancestor;
- all directories are descriptor-relative, owner-contained, mode `0700`, and
  non-symlink; all files are newly created regular files with mode `0600` or
  accepted executable mode where the target contract requires it;
- acquisition uses only exact authorized network operations before one explicit
  irreversible network-closure barrier; no parent environment, credential,
  proxy, askpass, SSH, dynamic-loader, or user configuration value is inherited;
- archive intake verifies URL, byte length, SHA-256, regular-file type, member
  allowlist, exact header grammar, exact ordered member inventory, path
  normalization, no absolute or traversing paths, no links/devices/FIFOs/sockets,
  no sparse or unsupported extension entry, per-file and aggregate expanded-size
  bounds, rejected ownership/mode metadata, and duplicate-member rejection before
  extraction;
- extraction occurs in an absent staging directory and cannot write directly to
  final handoff slots;
- the ordinal-073 build uses exact Charon source receipts, exact owned-tool
  receipts, the byte-exact deny-network sandbox profile, and a closed replacement
  environment; every linker, SDK, loader, build script, and child executable
  trust root is either identity-bound in the closed plan or the build is rejected;
- every executable descriptor remains retained from final verification through
  launch and the kernel-bound launch mechanism proves that the executed object is
  the verified inode; pathname recollection alone is insufficient and an
  unsupported platform mechanism stops before launch;
- each of the six target files is copied once into an absent slot, read back
  through no-follow descriptors, and checked against its accepted receipt;
- the acyclic canonical handoff manifest binds every admitted payload, review,
  candidate, validation, and nonclaim path plus its length and digest, but
  explicitly excludes itself and `materialization-decision.json`;
- after complete independent output review and readback, `validation.json` and
  `NONCLAIMS.md` are written, then `handoff-manifest.json`, then the success
  `materialization-decision.json`; each later object may bind earlier digests
  and no earlier object binds a later object;
- any failure terminates the process group, closes network capability, removes
  only the retained attempt-created staging or published inode tree descriptor-
  relatively, verifies its absence, writes a failure decision only under
  `AUDIT_ROOT`, durably marks the reserved authorization id and nonce
  `consumed_failure`, and emits no accepted handoff digest. Cleanup failure is
  recorded under `AUDIT_ROOT`, never converted to success, and requires operator
  remediation before any later attempt may use the preparation path.

Staging and publication occur on one verified local filesystem. Every bounded
file write is followed by file and directory durability checks. Final publication
is one atomic same-filesystem rename from the retained, exclusively created
`STAGING_ROOT` descriptor to the still-absent `PREPARATION_ROOT`. Mount substitution, cross-device rename,
hard-linked content, and durability failure reject. Cleanup failure leaves a
failed audit record and never grants authority.

`AUDIT_ROOT` is never renamed into `PREPARATION_ROOT` and is not a preparation
handoff. It stores the reservation record, terminal journal checkpoint,
materialization decision copy, cleanup report, and final `P01bAttemptAuditRecord
v1`. The acyclic terminal chain is reservation record -> handoff decision (or
failure decision) -> terminal journal record -> final attempt-audit record. The
attempt-audit record, rather than the handoff decision, binds the terminal
journal digest so no signature or digest cycle is introduced.

Its closed logical tree is:

```text
replay/reservation-record.json
replay/reservation-checkpoint.json
replay/terminal-record.json
replay/terminal-checkpoint.json
time/reached/{each reached pre-terminal observation phase}.json
time/terminal-success.json
time/terminal-failure.json
time/acceptance-commit.json
materialization-decision.json
cleanup-report.json
pending-success-audit-record.json
acceptance-commit.json
operations/success/{each reached global success ordinal 001 through 039}.json
operations/failure/{001,002,003,004,005,006}.json
operations/recovery/{001,002,003,004,005,006}.json
attempt-audit-record.json
```

Every completed operation writes its audit copy durably before the next mutable
operation. Only the pre-audit operations actually reached are present; the final
audit record carries their exact ordered path/digest inventory. Its own write
and durability-verification operations cannot be members of that record. Missing
reached operations, present unreached operations, an extra file, or a digest
mismatch rejects the audit.

Exactly one of `time/terminal-success.json` and
`time/terminal-failure.json` is present according to the terminal journal state.
`time/acceptance-commit.json` is present only on the success route.
Every signed pre-terminal observation reached by either route is copied durably
to `time/reached/` before the next mutable operation. Immediately after audit-
root creation, the reservation observation is backfilled with the bootstrap
records. Failure cleanup never removes `AUDIT_ROOT`; therefore a terminal-
failure observation always binds a retained prior envelope or the retained
reservation envelope. Missing links reject the audit.

Immediately after `create-attempt-audit-root`, the materializer backfills the
already completed bootstrap operation records 001 through 005 before operation
006. Failure before that backfill is represented by the authenticated journal
checkpoint and `audit_root_unavailable`, never by an incomplete fabricated tree.

`pending-success-audit-record.json` is present only on the success route. It is
durable before the terminal compare-and-swap and binds the exact precomputed
`consumed_success` journal-record digest. If interruption occurs after that
compare-and-swap, recovery verifies the published root and decision, obtains the
authenticated terminal checkpoint, and publishes the one deterministic final
audit record. Until that record is durable, the handoff is not accepted even
though the nonce is irreversibly consumed. Recovery never rewrites the terminal
journal state or re-executes a producer.

Publication alone is never acceptance. A consumer must verify the conjunction
of the handoff decision and manifest, the checkpoint-authority-signed
`consumed_success` checkpoint, the final audit record, and
`acceptance-commit.json`. The acceptance commit is a materialization-operator-
signed envelope over those digests and the operation-039 transcript. It is the
only externally consumable commit marker; its absence makes a visible
`PREPARATION_ROOT` pending and unusable. Recovery may create the same
deterministic commit exactly once after validating the terminal checkpoint.
Its operator-signature preimage is
`"hsai-native-transcript-preparation:p01b-acceptance-commit:v1\0"` followed by
the canonical unsigned commit bytes.

On the normal route, `ordered_completion_operation_records` contains only global
operation 039. On recovery it contains recovery operations 001 through 006 in
order. Any mixed, missing, extra, duplicated, or reordered completion record
rejects.

If `create-attempt-audit-root` itself fails after reservation, the terminal
journal record uses outcome `audit_root_unavailable`; no audit tree or failure
decision is fabricated, the authorization remains consumed, and operator
remediation is required. The independently authenticated journal checkpoint is
the durable failure authority for this one case.

Overwrite, resume, repair, partial acceptance, existing-root reuse, symlink
following, hard-link aliasing, pathname fallback, shell execution, and cleanup
that ignores an error are forbidden.

## Complete Handoff Additions

Phase 795 extends the Phase 789 closed handoff tree with these required paths;
all earlier Phase 789 paths remain required and no other path is admitted:

```text
authorization/reviewer-key-policy.json
authorization/attempt-authorization.json
authorization/trust-anchor.json
authorization/phase794-driver-request.json
authorization/phase794-driver-decision.json
authorization/preparation-plan-template.json
authorization/preparation-plan.json
provenance/replay-reservation.json
provenance/replay-reservation-checkpoint.json
provenance/time/reservation.json
provenance/time/packet-production.json
provenance/time/review-receipt-01.json
provenance/time/review-receipt-02.json
provenance/time/review-receipt-03.json
provenance/time/review-receipt-04.json
provenance/time/review-receipt-05.json
provenance/time/review-receipt-06.json
provenance/time/review-receipt-07.json
provenance/time/review-receipt-08.json
provenance/time/completion.json
inputs/rust-manifest.toml
inputs/rust-toolchain.toml
inputs/charon-source-tree.tar
inputs/aeneas-archive.tar.gz
payload-manifest.json
source-receipts/input/executable-registry-document.json
source-receipts/input/operation-order-document.json
source-receipts/input/machine-policy.json
source-receipts/input/rust-toolchain-manifest.json
source-receipts/input/charon-source-tree.json
source-receipts/input/aeneas-archive.json
source-receipts/input/sandbox-profile.json
source-receipts/input/reviewer-assignments.json
source-receipts/output/owned-rustc.json
source-receipts/output/owned-cargo.json
source-receipts/output/packaged-aeneas.json
source-receipts/output/packaged-charon.json
source-receipts/output/packaged-charon-driver.json
source-receipts/output/packaged-libgmp.json
source-receipts/output/built-charon.json
source-receipts/output/built-charon-driver.json
output-review-packet.json
preparation-candidate.json
materialization-decision.json
```

The tree also requires these closed provenance path families:

```text
provenance/host-facts/pre/{CURL_EXE,GIT_EXE,TAR_EXE,RUSTUP_EXE,
  SANDBOX_EXEC_EXE,CODESIGN_EXE,SPCTL_EXE,OTOOL_EXE}.json
provenance/host-facts/post/{CURL_EXE,GIT_EXE,TAR_EXE,RUSTUP_EXE,
  SANDBOX_EXEC_EXE,CODESIGN_EXE,SPCTL_EXE,OTOOL_EXE}.json
provenance/owned-tool-facts/pre/{RUSTC_EXE,CARGO_EXE}.json
provenance/owned-tool-facts/post/{RUSTC_EXE,CARGO_EXE}.json
provenance/build-child-facts/pre/{each exact Phase 796 build-child role}.json
provenance/build-child-facts/post/{each exact Phase 796 build-child role}.json
provenance/produced-artifact-facts/{each of the eight output subject ids}.json
provenance/operations/{each of success operations 001 through 033}.json
provenance/build-trust-roots/{each exact Phase 796 build-role id}.json
```

The braces above denote a closed expansion, not wildcard lookup. Phase 796 must
replace every build-role placeholder with one exact ordered role id and freeze
the resulting path census; zero roles or an unresolved role stops Phase 797.
The payload manifest binds success-operation transcripts 001 through 026. The
packet additionally binds transcript 027 for `construct-payload-manifest`; the
packet and later review/decision operations cannot recursively bind their own
transcripts. The final handoff manifest binds transcripts 001 through 033,
ending with `construct-validation-and-nonclaims`. `AUDIT_ROOT` retains audit
copies of every reached global success transcript 001 through 039, failure
transcripts 001 through 006, and recovery transcripts 001 through 006. Failure
and recovery operations 007-008 write or verify the final audit/commit and cannot
be members of the object they finalize. Nothing outside these exact ranges is
retained, so no object binds its own construction transcript.

The digest dependency graph is exact and acyclic:

```text
payload files
  -> payload-manifest.json
  -> output-review-packet.json and its operator signature
  -> eight output-review envelopes
  -> preparation-candidate.json
  -> validation.json and NONCLAIMS.md
  -> handoff-manifest.json
  -> materialization-decision.json
```

`payload-manifest.json` excludes itself and every later object. The handoff
manifest excludes itself and the materialization decision. The materialization
decision binds `handoff_manifest_sha256_or_null`; nothing inside the handoff
manifest binds the decision. Readback recomputes every edge in this order.

`P01bPayloadManifest.ordered_files` is the bytewise ascending union of: every
Phase 789 handoff path except `handoff-manifest.json`, `validation.json`, and
`NONCLAIMS.md`; the seven `authorization/*` paths; both reservation provenance
paths; `provenance/time/reservation.json`; the four retained `inputs/*` paths;
all eight `source-receipts/input/*` paths; exactly `28 + (2 * B)` fact paths,
where `B` is the nonzero Phase 796 build-child role count (16 host + 4 owned-tool
+ 2B build-child + 8 produced-artifact); all success-operation transcript paths
001 through 026; and every Phase 796 build-trust-root path. It excludes all eight
`source-receipts/output/*` review envelopes, `payload-manifest.json`,
`output-review-packet.json`, `preparation-candidate.json`, `validation.json`,
`NONCLAIMS.md`, `handoff-manifest.json`, and `materialization-decision.json`.
Missing, extra, duplicate, or reordered entries reject. This census is not
closed until Phase 796 replaces the build-role family with exact paths.

The materializer first produces a canonical signed `output-review-packet.json`
envelope whose unsigned packet binds
source inputs, complete source and build inventories, exact operation and
transcript digests, pre/post executable facts, sandbox and network-closure state,
output metadata, source stability, and all disclosed build trust roots.
Its signature uses the policy-authenticated materialization-operator key.
Independent reviewers then return eight signed `P01bOutputReviewEnvelope v1`
values under the exact output authorization mapping. Legacy
`SourceReceiptEnvelope v1` does not bind this packet and cannot authorize an
output. The materialization operator cannot review its own output. No final root
is published while a signature, review class, or binding is missing.

The packet envelope uses ordered fields `schema`, `unsigned_packet`, and
`operator_signature_hex`. Its signature preimage is:

```text
"hsai-native-transcript-preparation:p01b-output-review-packet:v1\0"
|| serde_json::to_vec(unsigned_packet)
```

The operator signature and every other ES256 signature in this contract are
exactly 64 raw bytes `r || s`, encoded as 128 lowercase hexadecimal characters,
with `s` in the lower half order. DER, JOSE base64url, variable-width integers,
high-S, and alternate encodings reject.

Checkpoint signatures use the same raw low-S encoding over
`"hsai-native-transcript-preparation:p01b-journal-checkpoint:v1\0"` followed by
the canonical unsigned checkpoint bytes.
Trusted-time signatures use
`"hsai-native-transcript-preparation:p01b-trusted-time-observation:v1\0"`
followed by the canonical unsigned observation bytes.

`P01bOutputReviewDecision v1` uses schema
`hsai-formal-p01b-output-review-decision-v1` and ordered fields:

```text
schema
review_id
attempt_id
authorization_envelope_sha256
preparation_plan_sha256
output_review_packet_envelope_sha256
subject_class
subject_id
subject_byte_length
subject_sha256
source_authority
source_revision
producer_id
producer_operation_id
reviewer_id
reviewer_key_id
reviewed_at_utc
decision
```

The envelope schema is `hsai-formal-p01b-output-review-envelope-v1` with ordered
fields `schema`, `unsigned_review`, `review_signature_hex`,
`review_received_at_utc`, and `receipt_time_observation_sha256`. The final two
fields are materializer observations outside the reviewer signature but inside
the canonical envelope digest. Its exact low-S raw ES256 signature preimage is:

```text
"hsai-native-transcript-preparation:p01b-output-review:v1\0"
|| serde_json::to_vec(unsigned_review)
```

The eight review envelopes use output-authorization order, unique review ids,
eight pairwise-distinct reviewer principals, exact producer id equal to
`materialization_operator_id`, exact reviewer-policy keys and classes, a review
time inside all windows, and `decision=accepted`. No output reviewer may be the
policy issuer, attempt authorizer, materialization operator, input reviewer,
machine-policy actor, capture operator, fixture reviewer, or grammar reviewer.

The two owned-tool and six target receipts also populate one complete
`PreparationCandidate v2`, which must pass the existing validator without
reinterpreting its always-false `materialization_accepted` field. Caller-populated
`accepted` booleans are not provenance and cannot substitute for the signed
output envelopes or review packet. Every candidate receipt field, including
subject id, class, path, byte length, digest, authority, revision, producer,
producer operation, reviewer id, reviewer key id, and acceptance value, must
project exactly from its output authorization, operator-signed packet entry, and
accepted output-review decision. Any field not derivable from those three
objects rejects; the existing validator alone is insufficient.

`P01bMaterializationDecision v1` is a separate acceptance object with ordered
fields:

```text
schema
attempt_id
authorization_envelope_sha256
reviewer_key_policy_sha256
preparation_plan_sha256
reservation_record_sha256
driver_request_identity_sha256
driver_decision_sha256
preparation_candidate_sha256
output_review_packet_envelope_sha256
handoff_manifest_sha256_or_null
ordered_pre_use_host_executable_fact_sha256
ordered_post_use_host_executable_fact_sha256
ordered_pre_use_owned_tool_fact_sha256
ordered_post_use_owned_tool_fact_sha256
ordered_pre_use_build_child_fact_sha256
ordered_post_use_build_child_fact_sha256
ordered_produced_artifact_fact_sha256
completion_observed_at_utc
completion_time_observation_sha256
cleanup_status
materialization_completed
capture_authorized
ordered_issues
claim_boundary
explicit_nonclaims
```

Success requires eight pre-use and eight post-use host facts, two pre-use and
two post-use owned-tool facts, the exact Phase 796 build-child pre/post census,
eight produced-artifact facts, empty issues,
`cleanup_status=not_required`, `materialization_completed=true`, and
`capture_authorized=false`, and a non-null handoff-manifest digest. Failure requires
`materialization_completed=false`, `capture_authorized=false`, no handoff
manifest digest, at least one issue, and `cleanup_status=completed` or `failed`.
`failed` additionally requires a `cleanup_failed` issue and an operator-
remediation-required audit outcome. Cleanup failure is a terminal distinct
result and cannot be represented as success.

## Canonical Materialization Wires

Every Phase 795/797/798 JSON object is a deny-unknown-fields struct serialized as
compact UTF-8 JSON in declared field order. Parsing requires byte-identical
reserialization. Maps, floats, duplicate fields, alternate order, omitted
booleans, uppercase hexadecimal, trailing bytes, and null outside an explicitly
nullable field reject.

The remaining schema values and ordered fields are frozen here:

```text
P01bTrustAnchor v1
schema=hsai-formal-p01b-trust-anchor-v1
fields: schema, trust_root_id, issuer_id, issuer_key_id,
        compressed_sec1_key_hex, key_sha256, allowed_scope,
        not_before_utc, expires_at_utc

P01bReplayJournalRecord v1
schema=hsai-formal-p01b-replay-journal-record-v1
fields: schema, journal_namespace, journal_storage_identity_sha256,
        journal_checkpoint_authority_sha256, sequence,
        prior_record_sha256_or_null,
        authorization_id, one_shot_nonce, attempt_id,
        reservation_observed_at_utc, monotonic_clock_id,
        monotonic_ticks, time_observation_envelope_sha256,
        state, outcome_code_or_null, recorded_at_utc

P01bJournalCheckpoint v1
schema=hsai-formal-p01b-journal-checkpoint-v1
fields: schema, journal_namespace, journal_storage_identity_sha256,
        checkpoint_authority_id, checkpoint_authority_key_id,
        checkpoint_authority_public_key_sha256, sequence,
        head_record_sha256, prior_checkpoint_sha256_or_null,
        checkpointed_at_utc

P01bJournalCheckpointEnvelope v1
schema=hsai-formal-p01b-journal-checkpoint-envelope-v1
fields: schema, unsigned_checkpoint, checkpoint_signature_hex

P01bTrustedTimeObservation v1
schema=hsai-formal-p01b-trusted-time-observation-v1
fields: schema, observation_id, attempt_id, observation_phase,
        time_source_identity_sha256, observed_at_utc,
        monotonic_clock_id, monotonic_ticks,
        prior_time_observation_sha256_or_null

P01bTrustedTimeObservationEnvelope v1
schema=hsai-formal-p01b-trusted-time-observation-envelope-v1
fields: schema, unsigned_observation, checkpoint_authority_signature_hex

P01bPayloadManifest v1
schema=hsai-formal-p01b-payload-manifest-v1
fields: schema, attempt_id, authorization_envelope_sha256,
        preparation_plan_sha256, ordered_files
file fields: relative_path, byte_length, sha256

P01bPreparationOperation v1
fields: operation_id, operation_kind, ordered_executable_roles,
        argv_template, cwd_template, ordered_environment,
        stdin_policy, network_capability, ordered_input_artifact_ids,
        ordered_output_artifact_ids, timeout_milliseconds,
        stdout_policy, stderr_policy, cleanup_effect

P01bPreparationPlanTemplate v1
schema=hsai-formal-p01b-preparation-plan-template-v1
fields: schema, template_id, attempt_id,
        authorization_envelope_sha256, reviewer_key_policy_sha256,
        driver_request_identity_sha256, driver_decision_sha256,
        preparation_contract_sha256, preparation_root, capture_root,
        attempt_audit_root, replay_journal_namespace,
        replay_journal_storage_identity_sha256,
        replay_journal_checkpoint_authority_sha256,
        replay_journal_expected_sequence,
        replay_journal_expected_head_sha256_or_null,
        trusted_time_source_identity_sha256,
        ordered_bootstrap_operations, ordered_runtime_success_operations,
        ordered_failure_operations,
        ordered_recovery_operations,
        claim_boundary, explicit_nonclaims

P01bPreparationPlan v1
schema=hsai-formal-p01b-preparation-plan-v1
fields: schema, plan_id, template_sha256, attempt_id,
        reservation_record_sha256, reservation_observed_at_utc,
        replay_journal_reserved_sequence,
        replay_journal_reserved_head_sha256,
        ordered_pre_use_host_executable_fact_sha256, preparation_root,
        capture_root, attempt_audit_root, ordered_runtime_success_operations,
        ordered_failure_operations, ordered_recovery_operations,
        claim_boundary, explicit_nonclaims

P01bOutputReviewPacket v1
schema=hsai-formal-p01b-output-review-packet-v1
fields: schema, attempt_id, authorization_envelope_sha256,
        preparation_plan_sha256, payload_manifest_sha256,
        ordered_source_inputs, ordered_build_inputs,
        ordered_operation_transcripts,
        ordered_pre_use_host_executable_facts,
        ordered_post_use_host_executable_facts,
        ordered_pre_use_owned_tool_facts,
        ordered_post_use_owned_tool_facts,
        ordered_pre_use_build_child_facts,
        ordered_post_use_build_child_facts,
        ordered_produced_artifact_facts, sandbox_profile_sha256,
        network_closed_at_operation_id, ordered_output_subjects,
        ordered_build_trust_roots, producer_id, producer_key_id,
        producer_public_key_sha256, produced_at_utc,
        packet_observed_at_utc, production_time_observation_sha256
role-digest fields: role_id, relative_path, byte_length, sha256
output-subject fields: subject_class, subject_id,
        destination_relative_path, subject_byte_length, subject_sha256,
        source_authority, source_revision, producer_id,
        producer_operation_id, produced_artifact_fact_sha256

P01bOutputReviewPacketEnvelope v1
schema=hsai-formal-p01b-output-review-packet-envelope-v1
fields: schema, unsigned_packet, operator_signature_hex

P01bMaterializationValidation v1
schema=hsai-formal-p01b-materialization-validation-v1
fields: schema, attempt_id, payload_manifest_sha256,
        output_review_packet_envelope_sha256,
        ordered_output_review_sha256,
        preparation_candidate_sha256, complete, capture_authorized,
        ordered_issues

P01bHandoffManifest v1
schema=hsai-formal-p01b-handoff-manifest-v1
fields: schema, attempt_id, authorization_envelope_sha256,
        preparation_plan_sha256, payload_manifest_sha256,
        output_review_packet_envelope_sha256,
        ordered_output_review_sha256,
        preparation_candidate_sha256, validation_sha256,
        nonclaims_sha256, ordered_declared_files
declared-file fields: relative_path, byte_length, sha256

P01bMaterializationDecision v1
schema=hsai-formal-p01b-materialization-decision-v1
fields: schema, attempt_id, authorization_envelope_sha256,
        reviewer_key_policy_sha256, preparation_plan_sha256,
        reservation_record_sha256,
        driver_request_identity_sha256, driver_decision_sha256,
        preparation_candidate_sha256,
        output_review_packet_envelope_sha256,
        handoff_manifest_sha256_or_null,
        ordered_pre_use_host_executable_fact_sha256,
        ordered_post_use_host_executable_fact_sha256,
        ordered_pre_use_owned_tool_fact_sha256,
        ordered_post_use_owned_tool_fact_sha256,
        ordered_pre_use_build_child_fact_sha256,
        ordered_post_use_build_child_fact_sha256,
        ordered_produced_artifact_fact_sha256,
        completion_observed_at_utc,
        completion_time_observation_sha256, cleanup_status,
        materialization_completed, capture_authorized, ordered_issues,
        claim_boundary, explicit_nonclaims

P01bAttemptAuditRecord v1
schema=hsai-formal-p01b-attempt-audit-record-v1
fields: schema, attempt_id, authorization_envelope_sha256,
        reservation_record_sha256, materialization_decision_sha256,
        pending_success_audit_record_sha256_or_null,
        terminal_journal_record_sha256,
        terminal_journal_checkpoint_sha256, preparation_root_state,
        capture_root_state, cleanup_status, cleanup_report_sha256,
        ordered_operation_records, outcome,
        recorded_at_utc, claim_boundary, explicit_nonclaims
operation-record fields: relative_path, byte_length, sha256

P01bPendingSuccessAuditRecord v1
schema=hsai-formal-p01b-pending-success-audit-record-v1
fields: schema, attempt_id, authorization_envelope_sha256,
        reservation_record_sha256, materialization_decision_sha256,
        handoff_manifest_sha256,
        expected_terminal_journal_record_sha256,
        preparation_root_state, capture_root_state, created_at_utc,
        claim_boundary, explicit_nonclaims

P01bAcceptanceCommit v1
schema=hsai-formal-p01b-acceptance-commit-v1
fields: schema, attempt_id, authorization_envelope_sha256,
        materialization_decision_sha256,
        terminal_journal_checkpoint_sha256,
        attempt_audit_record_sha256,
        ordered_completion_operation_records, committed_at_utc,
        acceptance_commit_observed_at_utc,
        commit_time_observation_sha256,
        claim_boundary, explicit_nonclaims
operation-record fields: relative_path, byte_length, sha256

P01bAcceptanceCommitEnvelope v1
schema=hsai-formal-p01b-acceptance-commit-envelope-v1
fields: schema, unsigned_commit, operator_signature_hex
```

`ordered_declared_files` excludes `handoff-manifest.json` and
`materialization-decision.json`. The closed replay states are `reserved`,
`consumed_success`, and `consumed_failure`. Journal sequence is strictly
increasing and every record after the first binds the previous record digest.
The first record has `prior_record_sha256_or_null=null`; every later record has
the lowercase SHA-256 of the immediately preceding canonical journal record.
`reserved` requires `outcome_code_or_null=null`. Terminal records require one
closed outcome code: `success`, `validation_failure`, `execution_failure`,
`review_failure`, `cleanup_completed_after_failure`, `cleanup_failed`, or
`audit_root_unavailable`.

All ordered digest lists contain 64-character lowercase SHA-256 strings and
reject duplicates. `ordered_environment` entries have exact fields `name` and
`value`; variable names are unique and in bytewise ascending order. Every argv
element is one literal string or one typed placeholder frozen by Phase 796;
shell fragments and implicit interpolation reject. Closed operation kinds,
stdin policies, network capabilities, output policies, cleanup effects, and
artifact ids are frozen by Phase 796 and are not implementation-selected.

`ordered_output_subjects` uses the eight output-authorization entries in their
exact authorized order. `ordered_build_trust_roots` uses the exact role
order frozen by Phase 796. `ordered_output_review_sha256` uses that same eight-
subject order. `ordered_declared_files` uses bytewise ascending relative-path
order. The only cleanup statuses are `not_required`, `completed`, and `failed`.
The only nullable fields in these wires are the explicitly suffixed
`_or_null` fields.

The other typed packet arrays use these exact unique orders and cardinalities:

```text
ordered_source_inputs:
  the eight SourceSubjectClass::INPUTS entries in declared enum order
ordered_build_inputs:
  rust-manifest -> inputs/rust-manifest.toml
  rust-toolchain -> inputs/rust-toolchain.toml
  charon-source-tree -> inputs/charon-source-tree.tar
  aeneas-archive -> inputs/aeneas-archive.tar.gz
  sandbox-profile -> sandbox.sb
  reviewer-assignments -> reviewer-assignments.json
ordered_operation_transcripts:
  global success ordinals 001 through 027
ordered_pre_use_host_executable_facts and ordered_post_use_host_executable_facts:
  CURL_EXE, GIT_EXE, TAR_EXE, RUSTUP_EXE, SANDBOX_EXEC_EXE,
  CODESIGN_EXE, SPCTL_EXE, OTOOL_EXE
ordered_pre_use_owned_tool_facts and ordered_post_use_owned_tool_facts:
  RUSTC_EXE, CARGO_EXE
ordered_pre_use_build_child_facts and ordered_post_use_build_child_facts:
  exact Phase 796 build-child role order
ordered_produced_artifact_facts:
  exact eight-subject output-authorization order
```

Every role-digest entry's `relative_path` must equal the one canonical path for
its role in the closed handoff census. Cross-role reuse, duplicate digest entry,
wrong cardinality, alternate path, or reordered entry rejects.

`preparation_root_state` is exactly `published`, `absent`, or
`cleanup_incomplete`; capture root state is always `absent`. Audit outcomes are `success`, `failed_clean`, and
`failed_cleanup_incomplete`. A success audit requires a published preparation
root, terminal `consumed_success`, and `not_required` cleanup. A failed audit
requires an absent preparation root and terminal `consumed_failure`, except
`failed_cleanup_incomplete`, which requires
`preparation_root_state=cleanup_incomplete`, `cleanup_status=failed`, and grants
no authority. Success requires a non-null pending-success audit digest; every
failure requires that field to be null.

Every `claim_boundary` field is the exact string
`Level1LocalReplayOrLower`. Every `explicit_nonclaims` field is this exact
ordered array with no additions, omissions, or alternate spelling:

```text
backend_execution
lean_smt_z3_cobalt_run
proof_artifact
checker_transcript
accepted_evidence
level2_or_higher_evidence
score_axis_population
semantic_correctness
production_readiness
sota
breakthrough
full_security
external_audit
action_authority
```

`NONCLAIMS.md` is exact UTF-8 ASCII bytes, including the final newline:

```text
# Nonclaims

This P01B preparation handoff is Level 1 local preparation evidence only.
It does not establish backend execution, a Lean/SMT/Z3/COBALT run, a proof
artifact, a checker transcript, accepted evidence, Level 2 or higher evidence,
score-axis population, semantic correctness, production readiness, SOTA, a
breakthrough, full security, an external audit, or action authority.
```

The versioned digest preimages are:

```text
"hsai-native-transcript-preparation:p01b-trust-anchor:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-reviewer-key-policy-envelope:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-attempt-authorization-envelope:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-preparation-plan-template:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-preparation-plan:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-replay-journal-record:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-journal-checkpoint-envelope:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-trusted-time-observation-envelope:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-payload-manifest:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-output-review-packet-envelope:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-output-review-envelope:v1\0" || canonical object
"hsai-native-transcript-preparation:candidate:v2\0" || canonical PreparationCandidate v2
"hsai-native-transcript-preparation:p01b-materialization-validation:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-handoff-manifest:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-materialization-decision:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-pending-success-audit-record:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-attempt-audit-record:v1\0" || canonical object
"hsai-native-transcript-preparation:p01b-acceptance-commit-envelope:v1\0" || canonical object
```

Each digest is lowercase SHA-256 over the exact domain bytes followed by the
canonical object bytes. Signature preimages remain the separately specified
unsigned-body domains and never sign an envelope digest recursively.

## Required Phase 797 Tests

The future hermetic validator/plan suite must include:

- independent golden compact JSON and domain digest vectors for every trust,
  authorization, plan, journal, payload, review, validation, manifest, and
  decision wire;
- exact low-S ES256 policy and authorization verification against separately
  pinned non-secret issuer/reviewer public keys, plus operator packet and output-
  review signature vectors;
- malformed, wrong-curve, wrong-key, wrong-digest, high-S, structurally reversed
  time window, wildcard, fallback, unknown-field, reordered, and noncanonical
  wire rejection;
- every actor collision, capability collision, reviewer reuse, and unauthorized
  subject class;
- mutation of every Phase 794 digest binding and every output authorization;
- driver decision rejection for false correspondence, issues, wrong cardinality,
  or either authorization boolean set true;
- exact census/order/cardinality for all eight input authorizations, eight output
  authorizations, seven bootstrap operations, 33 runtime-success operations,
  eight failure operations, and eight recovery operations;
- anchor-policy identity/window-chain rejection, journal namespace/storage/head
  binding rejection, exact claim/nonclaim constants, exact payload census, and
  field-by-field output-review-to-candidate projection rejection;
- proof that no process, network, environment, filesystem-write, secret-loading,
  shell, materialization, journal-mutation, capture, or backend surface exists;
  and
- current-toolchain, strict-clippy, and locked Rust 1.74 gates.

Phase 798, not Phase 797, must test trusted-clock expiry/future rejection,
concurrent reservation, replay, rollback, checkpoint mismatch, interruption at
every mutable operation, consumed-success audit recovery, and idempotent recovery
without producer re-execution.

## Phase 796 Resolution Boundary

Phase 796 is documentation-only. It must freeze every P01B argv, cwd,
replacement environment, stdin policy, timeout, output cap, executable-role and
child-identity set, network transition, typed input/output, accepted outcome,
kernel-bound launch mechanism, archive grammar and exact member inventory,
aggregate extraction limit, Charon build child and trust-root inventory,
trusted time source, anti-rollback checkpoint authority and compare-and-swap
protocol, recovery rule, transaction state, audit-root inventory, durability
rule, and cleanup outcome. It may not modify Rust
or Cargo, create a plan, or run any producer. A single unresolved field produces
another stop.

The P01B-specific archive inventory in Phase 796 is an input-preparation
prerequisite only. It does not close Phase 780 lane `L07`, whose later 102-row
archive-inventory contract remains separately scheduled.

## Corrected Forward Schedule

This schedule supersedes the Phase 790 schedule from Phase 795 onward without
rewriting historical decisions:

```text
795 external attempt authorization and P01B materialization boundary; no run
796 P01B execution correspondence, archive inventory, build-trust contract
797 hermetic static authorization validation and deterministic plan template
798 conditional reservation, runtime plan, P01B materializer, accepted handoff
799 conditional P02 identity-bound native transcript corpus capture
800 L05 native transcript grammars, typed outputs, acceptance IDs, fixtures
801 L06 Charon driver preflight argv contract
802 L07 archive inventory contracts
803 L08 mutable output inventory contracts
804 L10 canonical JSONL serialization profile and conformance vectors
805 L11 row expansion tranche 001-038
806 L11 row expansion tranche 039-064
807 L11 row expansion tranche 065-102
808 independent whole-ledger audit and conditional digest publication
809 earliest possible plan-v2 boundary, only after Phase 808 success
```

After plan v2, later explicit phases must still implement the executor, resolve
fresh complete-plan machine identities, implement retention, run a dry preflight,
and obtain live-attempt authorization. Only then may bounded backend execution be
considered.

Phase 799 may consume a preparation handoff only when the caller supplies both
the published `PREPARATION_ROOT` and its authorization-bound `AUDIT_ROOT` and
independently verifies the acceptance commit conjunction. A visible handoff root
without that commit is pending, not accepted capture input.

## Phase 797 Conditional Authorization

Phase 797 is conditionally authorized only after Phase 796 closes every field,
and only for additive pure-data Rust source and
focused tests under `crates/hsai-native-transcript-preparation`, one implementation
note, and standard mirrors. It may implement the two external envelope types,
strict canonical parsing, domain-separated digests, low-S ES256 verification,
closed static validation decisions, and deterministic
`P01bPreparationPlanTemplate` construction.

Phase 797 may not create or consume a real authorization packet, mutate a replay
journal, collect a host fact, read or write a filesystem path, use process,
network, environment, shell, helper, secret, or credential APIs, acquire or
extract source, invoke Rustup/Cargo/Charon/Aeneas/native tools, create a
preparation or capture root, materialize a target or handoff, capture a
transcript, create an attempt-audit root, close a Phase 780 lane, publish a
source-ledger digest, create plan
v2, execute a backend, create proof artifacts or checker transcripts, mutate an
accepted Evidence Ledger, create Level2+ evidence, populate score axes, or grant
action authority.

## Claim Boundary

Phase 795 is a documentation-first trust and materialization boundary. It is not
an authenticated reviewer, accepted external authorization, replay journal,
materialization plan, machine observation, source acquisition, archive safety
result, target build, output receipt, preparation handoff, native transcript
capture, fixture corpus, grammar, Phase 780 lane closure, zero-blocker audit,
source-ledger digest, plan v2, executor, retention result, dry preflight,
live-attempt authorization, backend execution, Lean/SMT/Z3/COBALT run, proof
artifact, checker transcript, accepted evidence, Level2+, score axis, semantic
correctness, production readiness, SOTA, breakthrough, full security, external
audit, or action authority.

## Phase 796 Forward Result

Phase 796 audited the conditional closure requirements and stopped. The
operation-family order is derivable, but the strict descriptor-bound launch
property has no accepted documented macOS mechanism; the byte-complete archive
ledger was not retained and its exact extraction bounds are not frozen; build
descendants and loader trust roots have not been
observed; trusted-time and anti-rollback transaction authorities are not
provisioned; and the 56 operation wires remain incomplete. No
`preparation_contract_sha256` is published. The conditional Phase 797
authorization above is therefore not activated. See
`docs/796-phase-hsai-p01b-execution-correspondence-transaction-authority-stop.md`.
