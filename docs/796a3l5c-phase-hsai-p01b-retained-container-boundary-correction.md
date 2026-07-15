# Phase 796-A3L5C HSAI P01B Retained Container Boundary Correction

## Status

Documentation-only correction required before A3L6 implementation can be
accepted or any A3L7/A3L8 command can run.

State slice:
`phase-796a3l5c-hsai-p01b-retained-container-boundary-correction`.

Classification: `P01BRetainedContainerBoundaryCorrected`.

Execution status: `NotRun`.

Evidence ceiling: `Level1LocalReplayOrLower`.

Correspondence remains 2/10. Commercial moat remains 3/10. Defensible
breakthrough evidence remains 2-3/10. No Docker, socket, registry, container,
intentional OOM, publication, review, or acceptance evidence was created by
this phase.

## Reason For Correction

The A3L6 measure-twice audit rejected the original A3L5 implementation route
before runtime. The original boundary sealed `candidate-decision.json` before
`renameatx_np(RENAME_EXCL)` and final-parent fsync, while C09 required those
postpublication facts. A prepublication object therefore could not honestly
set C09 true. The original candidate API also omitted the publication record.
Any implementation that returned C09 true at that point would fabricate class
closure.

The same audit found required observations without frozen raw inputs or capture
grammars: raw mountinfo, exact OOM ordering/readback, complete runtime identity,
signed Docker.app identity, Buildx version, descriptor observations, recovery
intent, and the exact candidate path grammar. This correction supersedes the
conflicting A3L5 sections named below. All unaffected A3L5 controls remain in
force.

## Superseded A3L5 Sections

This document replaces only these parts of A3L5:

- the frozen v2 wire rows for probe results, process records, publication,
  decision, review, aggregate, and final acceptance;
- `Exact Runtime Program` where readiness command cardinality, Docker JSON
  framing, durable intent, and recovery were incomplete;
- `Retained Candidate Shape`;
- `Atomic C02-C10 Acceptance` where raw inputs were underspecified;
- `Review, Keep, And Phase Route` where prepublication and postpublication
  order formed a cycle.

The authorization, direct-argv execution, stream caps, timeout, network,
container-control, claim-boundary, dirty-worktree, exact five-file A3L6 code
slice, and no-partial-credit rules remain unchanged unless explicitly corrected
below.

## Correction State Slice

This docs-first correction may change exactly:

```text
AGENTS.md
README.md
docs/12-task-list.md
docs/796a3l5c-phase-hsai-p01b-retained-container-boundary-correction.md
docs/90-whole-codebase-validation-report.md
```

Concurrent Statebook changes and
`crates/hsai-agent-admission/src/lib.rs` are outside this state slice and remain
unstaged. The stopped A3L6 draft remains untracked and is not accepted,
reviewed, or authorized to run.

After this correction is committed and independently accepted, A3L6 may again
modify exactly the five Python paths authorized by A3L5. No sixth code file,
package metadata, discovery filename, Cargo file, CI file, corpus file, seccomp
file, archive parser, or Rust source is added.

## Corrected Phase Order

```text
796-A3L5C  corrected docs-first boundary, two zero-finding reviews
796-A3L6   five-file hermetic implementation, tests, immutable-code reviews
796-A3L7   retained host/image readiness, final authorization and plans
796-A3L8   network-disabled native/normal/OOM execution and publication
796-A3L9   two independent postpublication reconstructions and final acceptance
```

A3L7 is prohibited until the immutable A3L6 code has two zero-finding reviews.
A3L8 is prohibited until A3L7 emits one accepted readiness result and one final
authorization. A3L9 cannot start until exclusive publication succeeds and its
external publication record is durable. No earlier stage may emit the later
stage's decision.

## Corrected Evidence Graph

The candidate contains payload evidence and one self-excluding manifest. It
contains no class decision.

```text
payload files + expected-bindings document
    -> candidate-manifest.json
    -> prepublication validation
    -> renameatx_np(RENAME_EXCL) + final-parent fsync
    -> external repository-state.json + publication-record.json
    -> external candidate-decision.json
    -> two fresh-validation receipts
    -> two external review records
    -> review-aggregate.json
    -> acceptance-record.json
```

`candidate-manifest.json` inventories every candidate payload file except
itself. The publication record binds the manifest digest, repository-state
digest, and prepublication and postpublication directory identities. The
external decision binds the manifest, expected-bindings, repository-state, and
publication-record digests and is the first object permitted to contain the
ordered C02-C07/C09/C10 results. Review records bind the decision, manifest,
publication, implementation, collector, and validator identities. The aggregate
binds both reviews. The final acceptance binds the aggregate. No later object
is inserted into or changes an earlier object.

The original `candidate-decision.json` path inside `candidate/` is forbidden.

## Corrected Wire Contracts

All JSON retains the A3L5 canonical ASCII, duplicate-key rejecting,
newline-free wire rule. Docker CLI transcript framing is separate and remains
raw evidence.

### Descriptor observation

Schema/domain:

```text
hsai-p01b-descriptor-observation-v1
hsai:p01b-descriptor-observation:v1
```

Exact fields:

```text
schema,role,path,relative_path,before,after,sha256
```

`before` and `after` each contain exactly
`device,inode,mode,uid,gid,link_count,size,mtime_ns,ctime_ns`. Allowed `role`
values added by this correction are exactly `gate-source-pre`,
`gate-source-post`, `gate-sandbox-exec`, and `gate-sandbox-profile` for the
matching materialized-tree/tool/profile reads. The path is
absolute and canonical. `relative_path` is the exact canonical
repository-relative path only for snapshot source/copy roles and these two
gate-source roles, and JSON null for the two gate-sandbox roles and
every other role, including protected repository observations. The
`mode` field is always the canonical decimal JSON integer
`stat.S_IMODE(st_mode)`, never full `st_mode` or an octal string. The
file is opened with `O_RDONLY|O_CLOEXEC|O_NOFOLLOW`,
must be one linked regular file, is streamed once through SHA-256, and is
`fstat`-checked before and after. The two identities must be equal. The record
retains the path and byte count but not the VM image or executable bytes.

Snapshot-source descriptor observations use the same identity map and include
the canonical relative source path. Candidate copies retain the complete source
bytes separately.

An ordered descriptor set has schema/domain
`hsai-p01b-descriptor-set-v1` / `hsai:p01b-descriptor-set:v1` and exact fields
`schema,kind,ordered_observations`. `kind` is `host-tools` or
`docker-desktop`; observations are in bytewise absolute-path order.
`host-tools` contains exactly Docker client, Buildx, and `/usr/bin/codesign`.
`docker-desktop` contains exactly `Info.plist`, `linuxkit/desktop.img`, and
`linuxkit/kernel`; the bundle directory is excluded. Its digest is the domain
digest of that complete object. No digest of an array without this wrapper is
accepted. Snapshot sets use their manifest-bound schema below.

### Durable intent

Schema/domain:

```text
hsai-p01b-container-intent-v1
hsai:p01b-container-intent:v1
```

Exact fields:

```text
schema,campaign_id,attempt_id,authorization_sha256,implementation_commit,
container_name,expected_labels,attempt_plan_sha256,created_monotonic_ns
```

The intent is written mode 0600 under an attempt-owned mode-0700 audit root and
file- and directory-fsynced before `container create`. After create, one
append-only companion record with schema/domain
`hsai-p01b-container-cid-binding-v1` /
`hsai:p01b-container-cid-binding:v1` binds exact fields
`schema,intent_sha256,container_id,create_observation_sha256,
bound_monotonic_ns`. It is also file- and directory-fsynced. No cleanup command
may address a container without the durable intent and either the CID binding
or a durable recovery-inspection observation that supplies the same exact CID,
name, and four labels. If create returns no stable CID, recovery uses only the
already durable inspection plan by name and may mutate only after that exact
observation is file- and directory-fsynced. A write/fsync failure before such a
binding stops without mutation, cannot publish, and requires operator handling;
the boundary does not claim cleanup in the presence of failed durable storage.

### Recovery plans

Recovery is two plans, not one retroactively resolved plan. Their domains are
`hsai:p01b-recovery-inspection-plan:v1` and
`hsai:p01b-recovery-cleanup-plan:v1`:

1. `hsai-p01b-recovery-inspection-plan-v1` contains exact fields
   `schema,intent_sha256,container_name,expected_labels,command` and exactly one
   targeted inspect by the durable name.
2. `hsai-p01b-recovery-cleanup-plan-v1` contains exact fields
   `schema,intent_sha256,cid_binding_sha256,inspection_observation_sha256,
   selected_branch,container_id,expected_labels,commands`.
   `cid_binding_sha256` is a digest for the normal route and JSON null only for
   the recovery-inspection binding route.

The branches are exactly `absent`, `present-running`, `present-stopped`, and
`collision`. The branch is recomputed only from the raw inspection observation:
the exact absent transcript selects `absent`; a valid complete 57-field object
whose name, CID, four labels, and Boolean running state match the durable
binding selects the corresponding `present-*` branch; a valid 57-field object
with any identity mismatch selects `collision`; malformed or failed inspection
selects no branch, emits no cleanup plan or recovery result, and stops without
mutation. That last route emits only
`hsai-p01b-recovery-inspection-failure-v1` /
`hsai:p01b-recovery-inspection-failure:v1` with exact fields
`schema,intent_sha256,inspection_plan_sha256,inspection_receipt_sha256,
failure`; `failure` is exactly `inspection_failed`. Its receipt is the one
complete failed inspection receipt. Null cleanup-plan/branch placeholders are
forbidden because those objects do not exist on this route.

The cleanup wire matrix is exact:

| branch | `container_id` | `cid_binding_sha256` | ordered command roles | complete result |
| --- | --- | --- | --- | --- |
| `absent` | bound 64-lowerhex when a CID binding exists, otherwise null | binding digest or null, matching that route | with binding: `recovery-absence-cid,recovery-absence-name,recovery-absence-label,recovery-daemon-recheck`; without: `recovery-absence-name,recovery-absence-label,recovery-daemon-recheck` | `cleanup_complete=true`, `failure=campaign_failed_container_absent` |
| `present-running` | observed 64-lowerhex, equal to a binding when one exists | binding digest or null, matching that route | `recovery-kill,recovery-wait,recovery-terminal-inspect,recovery-remove,recovery-absence-cid,recovery-absence-name,recovery-absence-label,recovery-daemon-recheck` | `cleanup_complete=true`, `failure=campaign_failed_container_removed` |
| `present-stopped` | observed 64-lowerhex, equal to a binding when one exists | binding digest or null, matching that route | `recovery-kill,recovery-wait,recovery-remove,recovery-absence-cid,recovery-absence-name,recovery-absence-label,recovery-daemon-recheck` | `cleanup_complete=true`, `failure=campaign_failed_container_removed` |
| `collision` | null | binding digest or null, matching that route | empty | `cleanup_complete=false`, `failure=identity_collision` |

For `present-stopped`, kill and wait commands have `activation=never` and emit
exact `not_run` receipts; every later command has `activation=recovery_only`.
For every other nonempty row every listed command has
`activation=recovery_only`. `collision` emits no mutation command and no
synthetic skipped mutation receipt. A command failure stops and retains the
failure root; if the result itself can still be written durably it keeps the
selected branch, sets `cleanup_complete=false`, and sets the only additional
allowed failure value `recovery_incomplete`. Recovery never resumes a workload,
uses `--force`, removes by name, or enumerates unlabeled containers.
For `recovery_incomplete`, the failed command receipt is followed by one
deterministic `not_run` receipt for every unexecuted suffix command in cleanup
plan order. Each suffix receipt binds the same plan, role/argv, preceding
receipt digest, `activation=recovery_only`, `outcome=not_run`, null exit/signal,
zero complete streams, and
`observation_class=prior_recovery_command_failed`; no suffix
command launches. The full receipt-array cardinality therefore always equals
one inspection receipt plus the cleanup-plan command count.

Recovery inspect accepts only the exact absent transcript or one 57-field JSON
array plus LF and empty stderr. Exact presence requires matching name, CID, and
all four labels. Recovery kill/remove succeed only with CID-plus-LF stdout and
empty stderr; recovery wait requires command exit 0, empty stderr, and one
decimal container status plus LF. On `present-running` its value must match the
immediately following complete stopped `recovery-terminal-inspect`; on
`present-stopped` the original recovery inspection is already the retained
terminal object. Recovery absence and daemon roles use the same exact grammars as the
normal attempt. A collision emits no synthetic skipped mutation receipts; the
cleanup plan's command array is empty and the recovery result is reject.

Except for the inspection-failure route above, the failure root retains both
plans, all executed observations and receipts, and one
`hsai-p01b-recovery-result-v1` record with domain
`hsai:p01b-recovery-result:v1` and exact fields
`schema,intent_sha256,inspection_plan_sha256,cleanup_plan_sha256,
ordered_receipt_sha256,selected_branch,cleanup_complete,failure`. Failure while
writing any durable intent, binding, plan, observation, receipt, or result
stops further mutation. A candidate cannot reference a recovery failure.

`selected_branch` in the result equals the cleanup plan and the independently
recomputed raw-inspection branch. `ordered_receipt_sha256` is raw SHA-256 of
the canonical exact receipt array: the inspection receipt first, followed by
one receipt per cleanup-plan command in listed order, including the two
`not_run` receipts for `present-stopped`. The result's complete values are the
matrix values only after every activated command and absence/daemon grammar
succeeds. The closed `failure` vocabulary is exactly
`campaign_failed_container_absent,campaign_failed_container_removed,
identity_collision,recovery_incomplete`; JSON null and any other string reject.

### Publication record

Schema/domain:

```text
hsai-p01b-container-publication-v2
hsai:p01b-container-publication:v2
```

Exact fields:

```text
schema,candidate_manifest_sha256,repository_state_sha256,staging_path,final_path,
parent_identity,prepublication_inventory_sha256,
postpublication_inventory_sha256,staging_identity,final_identity,
ordered_file_reopens,ordered_publication_events,final_manifest_sha256
```

All identities contain exactly `device,inode,mode,uid,gid,link_count`. Each
ordered file
reopen contains exactly `path,prepublication,postpublication`; each nested
record contains `identity,bytes,sha256`. It covers all 201 files after the
candidate manifest is written, once before and once after publication, and the
two records must match. `path` is the exact candidate-relative path, not a
staging/final absolute path. Pre/post inventory digests use domain
`hsai:p01b-publication-inventory:v1` over the canonical ordered array of exact
`path,identity,bytes,sha256` projections in bytewise path order.

Every publication event contains exactly
`ordinal,operation,target,flags,started_monotonic_ns,ended_monotonic_ns,result,
errno,identity,sha256`. Ordinals are contiguous; times are nondecreasing;
`identity` and `sha256` are null unless the operation observes them. Allowed
operations comprise exactly 270 events in this order:

1. 200 `payload-file-fsync` events in manifest-entry order, then one
   `candidate-manifest-fsync` event. Target is the candidate-relative path,
   flags are `[]`, result/errno are `0/0`, identity is the regular-file
   identity, and SHA-256 is the raw file digest.
2. 62 `candidate-directory-fsync` events in deepest-path-first bytewise order,
   ending at the staging root. Target is the candidate-relative directory
   (`.` for root), flags are `[]`, result/errno are `0/0`, identity is the
   directory identity, and SHA-256 is null.
3. One `prepublication-inventory` event with target `.`, empty flags,
   result/errno `0/0`, staging identity, and the prepublication inventory
   domain digest.
4. One `renameatx-np` event. Target is exact
   `{source:<staging-basename>,destination:<final-basename>}`, flags are exactly
   `[RENAME_EXCL]`, result/errno are `0/0`, and identity/SHA-256 are null.
5. One `final-parent-fsync` event with the absolute parent path, empty flags,
   result/errno `0/0`, parent identity, and null SHA-256.
6. One `staging-absence` no-follow lookup with the staging basename, empty
   flags, result/errno `-1/2` (`ENOENT`), and null identity/SHA-256.
7. One `final-root-reopen` with final basename, empty flags, result/errno
   `0/0`, final identity, and null SHA-256.
8. One `postpublication-inventory` with target `.`, empty flags, result/errno
   `0/0`, final identity, and the postpublication inventory domain digest.
9. One `final-manifest-read` with target `candidate-manifest.json`, empty
   flags, result/errno `0/0`, its file identity, and the manifest domain digest.

The final root device/inode equals
the staging identity, and final manifest domain digest equals
`candidate_manifest_sha256` exactly. The record is local ordered driver
evidence under the explicit `host-driver-honest` assumption; it is not an
independent syscall tracer or kernel audit log. The publication record is
written outside the
candidate under
`artifacts/publication/<candidate-manifest-sha256>/publication-record.json` and
is file- and directory-fsynced.

The publication record and retained prepublication descriptor plan are one
cross-bound C09 object pair. Publication `final_path` equals plan
`candidate_root`; publication `parent_identity` equals plan `parent_identity`;
and publication `staging_identity` equals plan `staging_identity`. The
publication staging and final basenames equal the plan-derived
`.p01b-staging-<campaign_id>` and `p01b-candidate-<campaign_id>` basenames.
The `renameatx-np` source/destination target, `final-parent-fsync` target,
`staging-absence` target, and `final-root-reopen` target are derived from those
same plan values and cannot be supplied independently. Every `decide-v3`,
`review-v2`, `aggregate-v2`, and `accept-v2` invocation receives the same
canonical final candidate root, which must equal both publication `final_path`
and plan `candidate_root`. Any mismatch rejects C09 and the atomic result.

The implementation uses `renameatx_np(parent_fd, staging_basename, parent_fd,
final_basename, RENAME_EXCL)` so both names are resolved relative to the
retained parent descriptor. The captured result and errno are reset/read around
that exact syscall. A failed rename, nonzero errno, missing or reordered fsync
event, successful staging lookup, or any reopen mismatch rejects publication.

`repository-state.json` has schema/domain
`hsai-p01b-repository-state-v1` /
`hsai:p01b-repository-state:v1` and exact fields
`schema,plan,implementation_commit,implementation_tree,before,after,
unchanged`. `before` and
`after` each use schema/domain `hsai-p01b-repository-state-capture-v1` /
`hsai:p01b-repository-state-capture:v1` and exact fields
`schema,ordered_commands,protected_observation`.
The embedded plan has schema/domain `hsai-p01b-repository-state-plan-v1` /
`hsai:p01b-repository-state-plan:v1` and exact fields
`schema,git_path,git_sha256,protected_path,environment,cwd,stdin_policy,
commands`; commands are
exactly `git rev-parse HEAD`,
`git rev-parse HEAD^{tree}`, and
`git status --porcelain=v2 -z --untracked-files=all` in that order.

Each `ordered_commands` row has exact
`role,argv,environment,cwd,stdin_policy,executable_path,executable_sha256,
timeout_ns,stdout_cap_bytes,stderr_cap_bytes,started_monotonic_ns,
ended_monotonic_ns,outcome,exit_code,signal,stdout_total_bytes,
stdout_retained_bytes,stdout_truncated,stdout_base64,stdout_sha256,
stderr_total_bytes,stderr_retained_bytes,stderr_truncated,stderr_base64,
stderr_sha256`. All three require exit 0, null signal, empty stderr, and
complete bounded stdout. Total and retained byte counts must equal the decoded
base64 length, each raw digest must match, each count must be within its cap,
and both truncation flags must be false. The HEAD/tree bytes are one lowercase
40-hex value plus LF; status bytes are arbitrary complete porcelain-v2 `-z`
bytes. Each `protected_observation` is a complete descriptor observation for
the admission file.
Before and after raw bytes, parsed commit/tree values, and protected identities
and digests must match exactly; `unchanged` is recomputed rather than trusted.
Candidate `provenance/git.json` is the complete canonical `before` capture; the
external record's `before` must match it byte-for-byte. Thus prepublication Git
provenance has retained command evidence rather than a digest-only assertion.
The record is external because the after capture occurs after publication. It
is written and fsynced before the publication record, whose
`repository_state_sha256` binds it. The publication record is then fsynced
before any decision process starts.

### Postpublication decision

Schema/domain:

```text
hsai-p01b-container-decision-v3
hsai:p01b-container-decision:v3
```

Exact fields:

```text
schema,authorization_sha256,implementation_commit,candidate_manifest_sha256,
expected_bindings_sha256,claim_boundary_sha256,repository_state_sha256,
publication_record_sha256,
class_results,atomic_result,evidence_level,
accepted_evidence_created,level2_plus_created,authority_granted
```

Every class result array contains exactly eight rows with exact fields
`class_id,closed`; class ids are ordered
`C02,C03,C04,C05,C06,C07,C09,C10` and `closed` is Boolean. The decision is
`accept` only when all eight reconstructed predicates are true. Its
`evidence_level` is exactly `Level1LocalReplayOrLower`; all three stronger-
authority booleans are false.
It is stored outside the candidate under
`artifacts/decision/<candidate-manifest-sha256>/candidate-decision.json`.
All stronger-authority booleans remain false.

### Reviews and final acceptance

Review schema/domain are `hsai-p01b-container-review-v2` /
`hsai:p01b-container-review:v2`; exact fields are
`schema,role,reviewer_id,review_session_sha256,review_session_durability_sha256,
candidate_manifest_sha256,candidate_decision_sha256,
implementation_commit,expected_bindings_sha256,claim_boundary_sha256,
repository_state_sha256,
publication_record_sha256,validator_sha256,collector_sha256,
fresh_validation_receipt_sha256,reconstructed_class_results,findings,result`.
The fresh validation receipt schema/domain are
`hsai-p01b-fresh-validation-receipt-v1` /
`hsai:p01b-fresh-validation-receipt:v1`; exact fields are
`schema,role,reviewer_id,review_session_sha256,review_session_durability_sha256,
process_id,python_path,python_sha256,python_version,
argv,environment,cwd,stdin_policy,python_descriptor_observation,
snapshot_copy_manifest_sha256,validator_path,validator_sha256,
collector_path,collector_sha256,started_monotonic_ns,ended_monotonic_ns,
input_digests,reconstructed_class_results,result`. It records a distinct fresh
process invocation procedurally; its process id is telemetry, not identity.
`input_digests` has exact fields
`review_session_sha256,review_session_durability_sha256,authorization_sha256,
candidate_manifest_sha256,candidate_decision_sha256,
expected_bindings_sha256,claim_boundary_sha256,repository_state_sha256,
publication_record_sha256,
a3l6_gate_bundle_sha256,validator_sha256,collector_sha256`. Each is the named
object's domain digest except validator/collector, which are raw file SHA-256.
Receipt class rows must byte-equal the fresh reconstruction. A review's class
rows must byte-equal its receipt and the v3 decision; findings are a sorted,
unique array of nonempty printable ASCII strings of at most 512 bytes each.
Review result is `accept` exactly when findings are empty and all rows close.
Fresh receipt result is `accept` exactly when its fresh reconstruction closes
all eight rows; otherwise it is `reject`.

After the v3 decision output is exclusively written, file-fsynced, and its
parent directory is fsynced, the driver creates exactly one review session.
`hsai-p01b-review-session-v1` / `hsai:p01b-review-session:v1` has exact fields
`schema,session_id,challenge_hex,candidate_manifest_sha256,
candidate_decision_sha256,decision_file_identity,decision_file_sha256,
created_monotonic_ns`. `challenge_hex` is one retained 32-byte `/dev/urandom`
read encoded as 64 lowercase hexadecimal characters; `session_id` is the
64-lowerhex SHA-256 of domain `hsai:p01b-review-session-id:v1`, one zero byte,
the 32 raw challenge bytes, and the 32 raw decision-domain-digest bytes. The
decision identity/digest are obtained by a no-follow reopen after decision
durability. The session path is exclusive and session-id-derived, mode 0600,
file-fsynced, and parent-directory-fsynced.

The separate `hsai-p01b-review-session-durability-v1` /
`hsai:p01b-review-session-durability:v1` record has exact fields
`schema,review_session_sha256,decision_file_identity,review_root_path,
review_root_identity,review_root_inventory_started_monotonic_ns,
review_root_inventory_ended_monotonic_ns,review_root_inventory_before,
review_root_inventory_before_sha256,session_path_absence_observation,
session_file_identity,ordered_events,durable_monotonic_ns`. The four events have exact
`ordinal,operation,target,started_monotonic_ns,ended_monotonic_ns,result,errno,
identity,sha256` and are, in order, successful `decision-reopen`,
`review-session-path-absence`, `review-session-file-fsync`, and
`review-session-parent-fsync`. Their targets,
identities, and SHA nullability are reconstructed; the final event end equals
`durable_monotonic_ns`. This record is itself exclusively written and
file-/directory-fsynced before either review launch under the explicit
`host-driver-honest` assumption. Every receipt, review, launch, aggregate, and
acceptance binds both session and durability domain digests. A session or
session id already present anywhere beneath the retained canonical
`artifacts/reviews/<manifest>/` root is rejected by descriptor-relative scan
and exclusive path creation. No cross-decision challenge-uniqueness claim is
made; decision/session digest binding prevents cross-decision replay.

Before session creation, the retained review-manifest root is opened no-follow
and scanned descriptor-relatively. The embedded inventory is a bytewise-path
ordered, at-most-10,000-row canonical array of exact
`path,type,mode,device,inode,uid,gid,link_count` records for all retained
entries. `review_root_path` is the canonical manifest-scoped review root; the
mandatory first row has `path="."`, type `directory`, and an identity projection
byte-equal to `review_root_identity`. Remaining paths are root-relative. Types
are `directory` or `regular`, symlinks/special files reject, and
its raw canonical-array SHA-256 equals the stored digest. The exact proposed
session directory lookup is separately retained as
`path,parent_identity,started_monotonic_ns,ended_monotonic_ns,result,errno` with
`result=-1,errno=2`; its parent identity equals the inventory `.` row. Timing is
`inventory_started < inventory_ended <= absence.started < absence.ended <=
session.created_monotonic_ns`. The absence event is an explicit projection,
not byte-equal to the observation: event target/time/result/errno equal the
observation path/time/result/errno, while event identity and SHA-256 are null.
The session manifest digest
equals both the v3 decision/common-input manifest digest and canonical
`<manifest>` layout component. Timing requires decision-reopen end no later
than `session.created_monotonic_ns`, which is strictly before the session-file
fsync starts; absence ends before exclusive session path creation. Aggregate
and acceptance replay the inventory digest, ENOENT observation, manifest/path
equalities, and timing rather than trusting a driver reuse Boolean.

Each fresh review process has one external
`hsai-p01b-review-launch-v1` / `hsai:p01b-review-launch:v1` record with exact
fields `schema,review_session_sha256,review_session_durability_sha256,
claim_boundary_sha256,role,
reviewer_id,command_observation,receipt_path,receipt_bytes,receipt_sha256,
receipt_domain_sha256,review_path,review_bytes,review_sha256,
review_domain_sha256`. `command_observation` uses the complete bounded command
schema: it binds the exact executable descriptor/path/hash, argv, environment,
cwd, closed stdin, timing, exit/signal, caps, complete base64 streams, raw
digests, and false truncation. Both stream caps are exactly 16,384 bytes. It
starts strictly after session durability, exits zero with null signal and empty
complete streams, and ends before the
exclusive receipt/review files are reopened no-follow. Raw output byte counts
and SHA-256 values match those reopens; domain digests match the parsed pair.
Launch records are then exclusively written and file-/directory-fsynced. The
two fixed-role launch-domain digests are the aggregate/acceptance ordered launch
array. A child-authored receipt without its matching parent launch observation
cannot be accepted as fresh.

For each fixed role, one exact pair predicate is mandatory. Review and receipt
`role` and `reviewer_id` are byte-equal; the review
`fresh_validation_receipt_sha256` equals that receipt's recomputed domain
digest. Their review-session and durability digests equal the matching launch
and retained session objects. Decision, receipt input, review, launch,
aggregate, and acceptance `claim_boundary_sha256` all equal the parsed embedded
expected-bindings object domain digest; every reconstructor reparses the exact
ordered assumptions/nonclaims. The receipt's Python path/hash/version equal the expected native
identity, its argv equals the exact fresh `review-v2` argv, its environment is
the closed reviewer environment, cwd is `/`, stdin policy is `closed`, and its
complete no-follow Python descriptor observation recomputes to the same
path/hash. `started_monotonic_ns < ended_monotonic_ns`; the two role processes
have distinct positive process ids, but process ids provide no trust claim.
Receipt timing is the child reconstruction interval and obeys
`launch.started <= receipt.started < receipt.ended <= launch.ended`; parent-end
equality is forbidden because that value is unavailable before child output is
closed. Both intervals are strictly after session durability.
Validator and collector paths are the canonical immutable snapshot paths;
their raw hashes equal the corresponding 21-file snapshot-manifest entries,
the review fields, receipt fields, receipt input digests, and expected
bindings. Every other named input digest equals the object passed on the exact
argv. Receipt, review, and v3-decision class rows are byte-equal. Any failed
equality rejects the pair.

The aggregate schema/domain are `hsai-p01b-container-review-aggregate-v2` /
`hsai:p01b-container-review-aggregate:v2`; exact fields are
`schema,review_session_sha256,review_session_durability_sha256,
candidate_manifest_sha256,candidate_decision_sha256,
implementation_commit,expected_bindings_sha256,claim_boundary_sha256,
repository_state_sha256,
publication_record_sha256,validator_sha256,collector_sha256,
ordered_fresh_validation_receipt_sha256,ordered_review_sha256,
ordered_review_launch_sha256,
reconstructed_class_results,atomic_result`. All three ordered digest arrays contain
exactly two values in fixed role order; reviews and receipts are not embedded.
The aggregate result is `accept` only when both receipt/review pairs validate,
all common inputs and rows match, reviewer ids differ, both reviews accept, and
its own fresh reconstruction matches those rows. For each fixed-role index,
the aggregate receipt digest equals the receipt digest referenced by the review
at the same index, and the aggregate review digest equals that review's domain
digest. The aggregate launch digest equals the matching launch record, whose
raw/domain output digests equal that same pair. Both `aggregate-v2` and
`accept-v2` recompute the complete pair
predicate, ordered arrays, common-input equality, and tool/snapshot bindings;
neither trusts the aggregate Boolean or digest arrays.

The final schema/domain are `hsai-p01b-container-acceptance-v2` /
`hsai:p01b-container-acceptance:v2`; exact fields are
`schema,review_session_sha256,review_session_durability_sha256,
candidate_manifest_sha256,candidate_decision_sha256,
review_aggregate_sha256,expected_bindings_sha256,claim_boundary_sha256,
repository_state_sha256,
publication_record_sha256,ordered_review_launch_sha256,
closed_classes,correspondence_score,evidence_level,
accepted_evidence_created,level2_plus_created,authority_granted`.

An accepted final record has `closed_classes` exactly
`["C02","C03","C04","C05","C06","C07","C09","C10"]`,
`correspondence_score="10/10"`,
`evidence_level="Level1LocalReplayOrLower"`, and
`accepted_evidence_created=false,level2_plus_created=false,
authority_granted=false`. Any other value rejects.

`validator_sha256` is the SHA-256 of the immutable
`p01b_container_evidence.py` bytes and `collector_sha256` is the SHA-256 of the
immutable `p01b_container_execution.py` bytes at the accepted A3L6 commit.

The two exact roles remain `security-capability` and
`correspondence-reproducibility`. Reviewer identifiers are distinct internal
ASCII labels. This is procedural independence only, not cryptographic identity
or external audit.

External records use this only-allowed layout; no external record is a
candidate payload:

```text
artifacts/publication/<manifest>/repository-state.json
artifacts/publication/<manifest>/publication-record.json
artifacts/decision/<manifest>/candidate-decision.json
artifacts/reviews/<manifest>/<session-id>/review-session.json
artifacts/reviews/<manifest>/<session-id>/review-session-durability.json
artifacts/reviews/<manifest>/<session-id>/security-capability/{fresh-validation-receipt,review,review-launch}.json
artifacts/reviews/<manifest>/<session-id>/correspondence-reproducibility/{fresh-validation-receipt,review,review-launch}.json
artifacts/reviews/<manifest>/<session-id>/review-aggregate.json
artifacts/reviews/<manifest>/<session-id>/acceptance-record.json
```

Every placeholder is the lowercase value bound in the record graph. All A3L9
argv, record path, and output path fields are reconstructed from this tree;
alternate nesting, omitted session ids, aliases, and extra external records
reject.

## Corrected Readiness Program

A3L7 has exactly six plan-derived direct commands. Only the first two may use
the registry/network:

```text
0 [BX,"imagetools","inspect","--raw",INDEX]
1 [BX,"imagetools","inspect","--raw",PLATFORM]
2 P+["image","inspect","--format={{json .}}",PLATFORM]
3 [BX,"version"]
4 [CS,"--verify","--strict","--verbose=4","/Applications/Docker.app"]
5 [CS,"--display","--verbose=4","/Applications/Docker.app"]
```

The readiness plan schema/domain are
`hsai-p01b-container-readiness-plan-v2` /
`hsai:p01b-container-readiness-plan:v2`; exact fields are
`schema,predecessor_commit,user_authorization_sha256,index_reference,
docker_path,docker_sha256,buildx_path,buildx_sha256,codesign_path,
codesign_sha256,commands,selected_reference_rule`. The result schema/domain are
`hsai-p01b-container-readiness-result-v2` /
`hsai:p01b-container-readiness-result:v2`; exact fields are
`schema,readiness_plan_sha256,ordered_observation_sha256,index_sha256,
selected_descriptor,selected_reference,platform_sha256,
local_image_observation_sha256,buildx_version_observation_sha256,
codesign_verify_observation_sha256,codesign_display_observation_sha256,
ordered_descriptor_set_sha256,context_sha256,image_config_digest,rootfs_diff_ids,
accepted,failure`. The observation digest array has exactly six values in plan
order. `ordered_descriptor_set_sha256` has exactly the `host-tools` and
`docker-desktop` descriptor-set domain digests in that order. `accepted` and
`failure` are recomputed; allowed failures are exactly
`registry_failed,selection_failed,platform_digest_failed,
local_resolution_failed,context_drift,identity_drift,signature_drift,
descriptor_drift,version_transcript_drift`.

`CS=/usr/bin/codesign` and its frozen SHA-256 is
`c91d293ec824037dc4fcb204c5aae32545f73a79a4d6b5f0d113cc856465f209`.
Buildx and Docker identities remain the A3L5 values. Commands use the closed
host environment, cwd `/`, closed stdin, direct argv, 262,144-byte stream caps,
and the existing timeout.

Buildx raw registry stdout is exact content with no appended newline. Docker
CLI `--format` stdout is exactly one duplicate-safe JSON value followed by one
LF; repository-canonical JSON is produced only after parsing. Buildx version
stdout is exactly
`github.com/docker/buildx v0.34.1-desktop.1 c79576280a671664e17eb68da98ec3136b614aed\n`,
stderr is empty, and exit is zero. Codesign stdout is empty and both codesign
roles require exit zero. Codesign verify stderr is bounded ASCII: zero
or more adjacent `--prepared:`/`--validated:` pairs under
`/Applications/Docker.app/`, then exactly
`/Applications/Docker.app: valid on disk\n` and
`/Applications/Docker.app: satisfies its Designated Requirement\n`.
Every adjacent prepared/validated pair must name the same canonical path.

Codesign path components use byte regex
`[A-Za-z0-9](?:[A-Za-z0-9 ._+@%=-]{0,126}[A-Za-z0-9._+@%=-])?` and the
complete canonical path regex
`/Applications/Docker\.app(?:/<component>){0,15}`. A component cannot be `.`,
`..`, empty, slash-containing, or space-terminated; the complete path is at
most 1,024 bytes. Prepared/validated rows use the stricter `<nested-path>`
grammar `/Applications/Docker\.app(?:/<component>){1,15}` and are respectively
anchored as `^--prepared:<nested-path>\n$` and
`^--validated:<nested-path>\n$`. The pair paths are
byte-equal. Unknown verify rows, carriage returns, non-ASCII bytes, or a raw
verify transcript over 262,144 bytes reject.

Codesign display stderr is unique ordered ASCII rows except three adjacent
authority rows. The exact ordered row prefixes are `Executable=`,
`Identifier=`, `Format=`, `CodeDirectory v=`, `Hash type=`,
`CandidateCDHash sha256=`, `CandidateCDHashFull sha256=`, `Hash choices=`,
`CMSDigest=`, `CMSDigestType=`, `Executable Segment base=`,
`Executable Segment limit=`, `Executable Segment flags=`, `Page size=`,
`CDHash=`, `Signature size=`, three `Authority=`, `Timestamp=`,
`Notarization Ticket=`, `Info.plist entries=`, `TeamIdentifier=`,
`Runtime Version=`, `Sealed Resources version=`, and
`Internal requirements count=`. The complete anchored byte regex for each row,
in that order, is frozen below. `<u>` means `(?:0|[1-9][0-9]{0,19})`, `<hex40>`
means `[0-9a-f]{40}`, `<hex64>` means `[0-9a-f]{64}`, `<version>` means
`[0-9]{1,5}(?:\.[0-9]{1,5}){0,3}`, and `<path>` is the canonical path grammar
above.

```text
^Executable=/Applications/Docker\.app/Contents/MacOS/Docker Desktop\n$
^Identifier=com\.docker\.docker\n$
^Format=[A-Za-z0-9][A-Za-z0-9 ._+(),/-]{0,127}\n$
^CodeDirectory v=<u> size=<u> flags=0x[0-9a-f]{1,16}(?:\([A-Za-z0-9,_+-]{1,64}\))? hashes=<u>\+<u> location=embedded\n$
^Hash type=sha256 size=32\n$
^CandidateCDHash sha256=<hex40>\n$
^CandidateCDHashFull sha256=<hex64>\n$
^Hash choices=sha256\n$
^CMSDigest=<hex64>\n$
^CMSDigestType=2\n$
^Executable Segment base=<u>\n$
^Executable Segment limit=<u>\n$
^Executable Segment flags=0x[0-9a-f]{1,16}\n$
^Page size=(?:4096|16384)\n$
^CDHash=<hex40>\n$
^Signature size=<u>\n$
^Authority=Developer ID Application: Docker Inc \(9BNSXJN65R\)\n$
^Authority=Developer ID Certification Authority\n$
^Authority=Apple Root CA\n$
^Timestamp=[A-Z][a-z]{2} (?: [1-9]|[12][0-9]|3[01]), [0-9]{4} at (?:[1-9]|1[0-2]):[0-5][0-9]:[0-5][0-9] [AP]M\n$
^Notarization Ticket=stapled\n$
^Info\.plist entries=<u>\n$
^TeamIdentifier=9BNSXJN65R\n$
^Runtime Version=<version>\n$
^Sealed Resources version=<u> rules=<u> files=<u>\n$
^Internal requirements count=<u> size=<u>\n$
```

Metavariables are expanded before regex compilation; literal angle-bracket
tokens are never accepted. Every row is at most 1,024 bytes and the complete
display transcript is at most 262,144 bytes. Unknown, missing, duplicate,
reordered, non-ASCII, carriage-return, or grammar-invalid rows reject.
`Identifier` is `com.docker.docker`,
`TeamIdentifier` is `9BNSXJN65R`, the full candidate CDHash is 64 lowercase
hexadecimal characters, `CMSDigest` equals it, and both `CandidateCDHash` and
`CDHash` equal its first 40 characters. The transcript is retained raw. This
discloses current signed-app identity under Apple's codesign result;
it does not independently prove Apple trust or eliminate the signed-app honesty
assumption.

The two registry and two signature companion documents use schema/domain
`hsai-p01b-transcript-binding-v1` /
`hsai:p01b-transcript-binding:v1` and exact fields
`schema,kind,observation_sha256,stdout_path,stdout_bytes,stdout_sha256,
stderr_path,stderr_bytes,stderr_sha256,parsed`. Allowed `kind` values are
`registry-index`, `registry-platform`, `codesign-verify`, and
`codesign-display`. Registry `parsed` is the complete duplicate-safe JSON object
reparsed from operation stdout and preserves every provider key; index
validation accepts exactly one selected linux/arm64/v8 descriptor and platform
validation requires its digest, media type, size, config descriptor, and all
layer descriptors to match the raw object. Verify `parsed` has exact
`prepared_paths,validated_paths,valid_on_disk,
satisfies_designated_requirement`; display `parsed` has exact
`ordered_rows,executable,identifier,format,candidate_cdhash,
candidate_cdhash_full,cms_digest,cdhash,authorities,team_identifier,
runtime_version`. The wrapper never substitutes
for the named raw stream.

A3L7 also performs no-follow descriptor reads for Docker, Buildx, codesign,
Docker
Desktop `Info.plist`, `linuxkit/desktop.img`, `linuxkit/kernel`, and the Docker
context metadata. Exact descriptor-observation records are retained. Context
and Info.plist bytes are retained in full; executable, VM-image, and kernel
bytes are not copied into the candidate. Docker, Buildx, VM-image, kernel, and
context streamed digests must equal the frozen A3L5 values. The Info.plist
digest is measured at readiness, bound into expected bindings, and its parsed
version must agree with the signed app and tool transcripts. Descriptor drift
stops readiness.

The six non-context, non-Git provenance JSON documents use schema/domain
`hsai-p01b-host-provenance-v1` / `hsai:p01b-host-provenance:v1` and exact outer
fields `schema,kind,ordered_source_observation_sha256,descriptor_set_sha256,
descriptor_set,facts,assumptions`. Allowed `kind` and exact `facts`
fields are:

```text
docker-desktop: info_plist_sha256,bundle_version,short_version,
                vm_image_sha256,kernel_sha256,codesign_verify_sha256,
                codesign_display_sha256,candidate_cdhash_full,team_identifier
docker-client: path,sha256,client_version,api_version,go_version,os,arch
buildx: path,sha256,version,revision,buildx_version_stdout_sha256
docker-daemon: host,context_name,server_version,api_version,os,arch,
               kernel_version,operating_system,docker_root_dir,
               containerd_version,containerd_commit,runc_version,runc_commit,
               version_observation_sha256,info_observation_sha256
image-config: platform_reference,image_id,config_descriptor_digest,
              architecture,os,variant,config_sha256
rootfs: image_id,rootfs_type,ordered_diff_ids
```

Every fact is parsed from the retained raw Info.plist/context bytes or the raw
readiness/campaign transcript it names; missing, duplicate, or additional facts
reject. `ordered_source_observation_sha256` is the exact array of one or more
operation-observation digests in this frozen role order:
`docker-desktop=[readiness/codesign-verify,readiness/codesign-display]`,
`docker-client=[campaign/docker-version]`,
`buildx=[readiness/buildx-version]`,
`docker-daemon=[campaign/docker-version,campaign/docker-info]`,
`image-config=[campaign/image-config]`, and
`rootfs=[campaign/image-config]`. The named observation role and its recomputed
digest must both match; a semantically compatible observation from another
plan or role rejects. `descriptor_set_sha256` is a descriptor-set
domain digest for `docker-desktop`,
`docker-client`, and `buildx`, and JSON null for `docker-daemon`,
`image-config`, and `rootfs`; other nullability rejects. `docker-client` and
`buildx` each embed the complete byte-identical `host-tools` descriptor-set
object. `docker-desktop` embeds the complete `docker-desktop` object.
`descriptor_set` is JSON null exactly when its digest is null. The Docker.app
bundle directory is never passed to the regular-file schema. `assumptions` is an exact sorted
set. `docker-desktop` requires exactly `signed-docker-app-honest,
host-driver-honest`; `docker-daemon`, `image-config`, and `rootfs` require
exactly `docker-daemon-honest,host-driver-honest`; `docker-client` and `buildx`
require exactly `host-driver-honest`. No other set is accepted. Host
OS/kernel/architecture must agree
across Docker info, image inspection, descriptor observations, and probe
runtime identity at the level applicable to host versus Linux VM; cross-OS
values are labeled, never equated.

All six readiness observations reconstruct one completion-ordered v2 receipt
chain whose first previous digest is null. The four campaign observations do
the same. No receipt may omit a raw operation directory or cross a namespace.

Every `receipts.json` wrapper uses schema/domain
`hsai-p01b-container-receipt-chain-v1` /
`hsai:p01b-container-receipt-chain:v1` and exact fields
`schema,kind,plan_sha256,ordered_receipts,chain_sha256`. `kind` is exactly one
of `readiness,campaign,normal,oom`; the candidate's `reference/receipts.json`
has kind `campaign`. `ordered_receipts` contains only validated v2 receipts in
completion order. `chain_sha256` is raw SHA-256 of the canonical exact ordered
receipt array, and every previous-receipt/observation digest plus raw stream
path is recomputed.

## Corrected Attempt Program

Each attempt has one timing record with schema/domain
`hsai-p01b-attempt-timing-v1` / `hsai:p01b-attempt-timing:v1` and exact fields
`schema,campaign_id,attempt_id,start_monotonic_ns,deadline_monotonic_ns,
end_monotonic_ns,ordered_durability_events,deadline_met`. Each durability event
has exact `ordinal,operation,target,started_monotonic_ns,ended_monotonic_ns,
result,errno,sha256`. It records intent-file fsync, intent-directory fsync,
create start/end, CID-binding-file fsync, and CID-binding-directory fsync.
The success route has exactly five events: `intent-file-fsync` targets
`intent.json`, result/errno `0/0`, and the intent domain digest;
`intent-directory-fsync` targets `.`, result/errno `0/0`, and null SHA-256;
`container-create` targets the planned container name, spans the raw create
observation, uses its command exit as result, null errno, and observation
domain digest; an accepted route requires result 0. `cid-binding-file-fsync`
targets `cid-binding.json`, uses
`0/0`, and the binding domain digest; `cid-binding-directory-fsync` targets
`.`, uses `0/0`, and null SHA-256. The recovery-inspection binding route
substitutes `recovery-inspection-file-fsync` and
`recovery-inspection-directory-fsync` at ordinals 3/4 with the analogous
observation digest/null SHA rules. All targets are audit-root-relative
canonical paths; other operation names, targets, nullability, results, or
errnos reject. Exact ordering requires intent-directory
fsync end no later than create start and create end no later than the binding
directory fsync end. This is local driver evidence under `host-driver-honest`,
not a kernel audit log. The deadline is exactly
`start_monotonic_ns + 1800000000000`; every observation begins at or after
start, the final absence/daemon observation ends no later than end, and
`end_monotonic_ns <= deadline_monotonic_ns`. Timeout routes to recovery and
cannot produce a candidate.

Before every command launch, the executor computes
`effective_timeout_ns=min(command.timeout_ns,
deadline_monotonic_ns-current_monotonic_ns)`. A nonpositive remainder rejects
without launch; no command receives time beyond the attempt deadline.

This correction removes inherited create arguments `--pid=private` and
`--uts=private`; Docker/Moby does not accept those mode values. Their flags are
absent, inspect requires `HostConfig.PidMode=""` and
`HostConfig.UTSMode=""`. The probe retains raw container parent/child PID/UTS
namespace identities and checks their internal relationships against inspect
under `docker-daemon-honest`; a macOS collector has no comparable Linux
namespace identity, so no host-versus-container namespace claim is made.
Private IPC and private cgroup namespace arguments remain.

Successful command outcomes are closed as follows:

- readiness registry index/platform: command exit 0, empty stderr, exact raw
  manifest stdout with no appended LF;
- readiness local image, campaign Docker version/info/image: command exit 0,
  empty stderr, one JSON value plus exactly one LF;
- readiness Buildx version and codesign roles: the exact framing already frozen
  above;
- native reference: command exit 0, empty stderr, one canonical probe result
  with no LF;
- `absence-name-pre`, `absence-cid`, and `absence-name`: command exit 1,
  empty stdout, and the exact subject-specific Docker 29.5.3 no-such-container
  stderr;
- `absence-label-pre` and `absence-label`: command exit 0 with both streams
  empty;
- `create`: command exit 0, empty stderr, and one 64-lowercase-hex CID plus LF;
- both inspect roles: command exit 0, empty stderr, and one 57-element JSON
  array plus exactly one LF;
- `start-attach`: command exit 0, empty stderr, exactly one valid retained
  readiness line, and no bytes after that line;
- `export-running`: command exit 0, empty stderr, and one strict bounded Docker
  copy TAR whose sole accepted result member reconstructs the probe result;
- `release` and `remove`: command exit 0, empty stderr, and the exact CID plus
  LF; `emergency-kill` is `not_run` on an accepted attempt;
- `wait`: command exit 0, empty stderr, and `0\n`, because the survivor probe is
  the container init and returns zero after independently recording the OOM
  child's SIGKILL;
- `daemon-recheck`: command exit 0, empty stderr, one JSON value plus one LF.

Any other outcome, extra byte, truncation, timeout, actual emergency kill, or
unknown skipped role rejects the attempt. Parsed inspect/result JSON stored
under `attempts/` is canonical and newline-free; the corresponding raw Docker
stdout including its required LF remains under `operations/`.

The egress certificate is rebuilt from the raw readiness stream, TAR, result,
export, release, and completed-start observations; its ordering predicate is
never accepted from the driver. The cleanup certificate is rebuilt from exact
CID/name error transcripts, empty label listing, remove observation, and final
daemon response. It cannot set `absent=true` from exit codes alone. Both reuse
the closed A3L5 certificate field and predicate sets and retain all stronger
authority booleans as false.

### Exact inspect evaluator

Every one of the 57 ordered inspect fields is evaluated, not merely counted:

```text
Id,Name,Path,Args,Platform,AppArmorProfile,Config.Image,Config.User,
Config.Entrypoint,Config.Cmd,Config.Env,Config.WorkingDir,Config.Hostname,
Config.Healthcheck,Config.OpenStdin,Config.Tty,Config.Labels,
HostConfig.Runtime,HostConfig.NetworkMode,HostConfig.IpcMode,
HostConfig.PidMode,HostConfig.UTSMode,HostConfig.CgroupnsMode,
HostConfig.CgroupParent,HostConfig.UsernsMode,HostConfig.ReadonlyRootfs,
HostConfig.Privileged,HostConfig.CapAdd,HostConfig.CapDrop,
HostConfig.SecurityOpt,HostConfig.Memory,HostConfig.MemorySwap,
HostConfig.MemorySwappiness,HostConfig.OomKillDisable,HostConfig.PidsLimit,
HostConfig.CpuPeriod,HostConfig.CpuQuota,HostConfig.Ulimits,HostConfig.Tmpfs,
HostConfig.ShmSize,HostConfig.LogConfig,HostConfig.RestartPolicy,
HostConfig.AutoRemove,HostConfig.Devices,HostConfig.DeviceRequests,
HostConfig.GroupAdd,Mounts,NetworkSettings.Networks,State.Status,
State.Running,State.ExitCode,State.OOMKilled,State.Error,State.Pid,
State.StartedAt,State.FinishedAt
```

- `Id,Name` equal the durable CID and slash-prefixed planned name;
  `Path,Args` equal the command derived from the exact create argv;
  `Platform=linux`; `AppArmorProfile=docker-default` maps only to raw LSM bytes
  `docker-default (enforce)\n`, while an empty AppArmor profile maps only to
  `unconfined\n`. This is an identity correspondence under the explicit LSM
  nonclaim, not a host-kernel enforcement proof.
- Every `Config.*` value is reconstructed from the exact image-inspect config
  and create argv. Image, user, entrypoint, command, closed environment,
  working directory, hostname, disabled healthcheck, closed stdin, no TTY, and
  the four exact labels must match. Docker's only accepted absent
  representation is JSON `null`; empty arrays, objects, and strings are never
  treated as interchangeable with null. Disabled healthcheck is exactly
  `{"Test":["NONE"]}`.
- `HostConfig.Runtime=runc`, `NetworkMode=none`, `IpcMode=private`,
  `PidMode=""`, `UTSMode=""`, `CgroupnsMode=private`,
  `CgroupParent=""`, `UsernsMode=""`, `ReadonlyRootfs=true`,
  `Privileged=false`, `CapAdd=null`, and `CapDrop=["ALL"]`.
- `SecurityOpt` parses to exactly the no-new-privileges setting plus seccomp
  JSON equal to the retained profile. Memory and swap are 536870912,
  swappiness is 0, OOM-kill-disable is false, pids limit is 16, CPU period and
  quota are 100000, and the four ulimits equal the create plan without order
  substitution.
- `Tmpfs` contains only `/work` with the exact option set; `ShmSize=1048576`;
  log config is only `none`; restart is only `no`; auto-remove is false;
  `Devices=[]`, `DeviceRequests=null`, and `GroupAdd=null`.
- `Mounts` contains exactly the one `/input` bind described by the ingress
  rule. `NetworkSettings.Networks` contains exactly the `none` key and the
  complete endpoint object in both states. Its exact ordered-independent key
  set is `IPAMConfig,Links,Aliases,MacAddress,DriverOpts,GwPriority,NetworkID,
  EndpointID,Gateway,IPAddress,IPPrefixLen,IPv6Gateway,GlobalIPv6Address,
  GlobalIPv6PrefixLen,DNSNames`; unknown or missing keys reject. In both
  objects, `IPAMConfig,Links,Aliases,DriverOpts,DNSNames` are JSON null,
  `MacAddress,Gateway,IPAddress,IPv6Gateway,GlobalIPv6Address` are empty
  strings, and `GwPriority,IPPrefixLen,GlobalIPv6PrefixLen` are integer zero.
  Prestart `NetworkID` and `EndpointID` are both empty strings. Terminal
  `NetworkID` is exactly one 64-character lowercase hexadecimal string and
  terminal `EndpointID` is exactly the empty string, matching the pinned
  exited-container endpoint teardown shape. Any other transition rejects.
  Those two identifiers are the only fields permitted to change.
  No routable network key or nonempty address is present. The two complete
  objects are evaluated separately, not required byte-equal. This closes the
  exact pinned API response shape only; a daemon version that adds or removes
  endpoint keys fails readiness rather than silently changing the evaluator.
- Prestart state is exactly `created,false,0,false,"",0` for
  status/running/exit/OOM/error/PID and uses Docker's exact zero time strings.
  Terminal state is `exited,false,0,false,"",0`; its nonzero RFC3339
  start/finish timestamps are retained and strictly ordered. Docker's terminal
  OOM flag is not used as child-OOM evidence; the raw child wait and cgroup
  deltas provide that evidence.

Each expected value is constructed independently from the plan, raw
image-inspect document, expected-bindings document, and raw probe inputs. No
driver-supplied inspect certificate boolean is accepted.

## Corrected Probe Results

The A3L5 probe result schema is superseded by
`hsai-p01b-probe-result-v2`. It adds raw inputs required for independent
reconstruction.

The probe result `schema` is exactly that value in all three modes. Its
`probe_sha256` is the raw SHA-256 of the retained snapshot copy of
`tools/hsai-formal-preflight/p01b_container_probe.py`; the source and snapshot
descriptor observations and manifest must independently bind the same bytes.
The native/normal exact top-level field sets remain the A3L5 sets plus the v2
runtime fields below; the OOM set remains the A3L5 set plus the v2 security,
process, workload, and cgroup fields below. Unknown or omitted fields reject.

Runtime adds exactly:

```text
sys_version,sysconfig_paths,linker_version_argv,
linker_version_stdout_base64
```

`sysconfig_paths` is the complete sorted key/value result of
`sysconfig.get_paths()`. Container runtime requires exact raw
`/usr/bin/ldd --version` stdout. Native Darwin records the exact empty
`linker_version_argv` and empty bytes because `/usr/bin/ldd` does not exist;
raw `otool -L` remains the dependency transcript already retained.
Inventory domain digests are independently recomputed from their rows. Symlink
chains retain traversal order and are never alphabetically resorted. Each chain
row has exactly `kind,path,mode,target_base64,bytes,sha256`: symlink rows use
`kind=symlink` and retain/hash the exact link-target bytes; the final regular
row uses `kind=regular`, `target_base64=null`, and hashes the complete file.
Each dependency has exact `reported_path,identity` and is a nested identity tied
to one absolute path parsed from raw linker output rather than a flattened row
set. The dependency output itself is retained raw, so missing shared-cache
objects are explicit reported paths with `identity=null`, not silently dropped.
Interpreter, dependency, stdlib, package, VM, kernel, Docker, and Buildx files
are streamed and identity-hashed but are not copied wholesale into the
candidate. C02/C07 therefore claim recorded local identity under probe/driver
honesty, not independent redistribution or byte-for-byte third-party replay of
those binaries.

Security adds exactly:

```text
cgroup_base64,oom_score_adj_base64
```

The raw `/proc/<pid>/cgroup` and `oom_score_adj` bytes must parse to the
normalized cgroup path and integer. Status parsing requires exact `Uid:` and
`Gid:` rows with four decimal `65532` values, exact tab-delimited zero
capability rows, exact `NoNewPrivs:\t1`, `Seccomp:\t2`, and a positive exact
decimal `Seccomp_filters` row. Whitespace-normalized substitutes reject.

Mounts add exactly `mountinfo_base64`. Its SHA-256 must equal
`mountinfo_sha256`, and the `/work` and `/dev/shm` rows are independently
reparsed from those bytes. `/work` is 16 MiB, mode 0700, uid/gid 65532, and
`rw,nosuid,nodev,noexec`. `/dev/shm` is private tmpfs, 1 MiB, mode 01777, and
`rw,nosuid,nodev,noexec`; its retained uid/gid are telemetry and do not create
an ownership claim.

Container rlimits add exact `proc_limits_base64`. The raw
`/proc/self/limits` bytes are reparsed under the fixed ASCII column grammar;
Max cpu time is 900/900 seconds, Max file size is 67108864/67108864 bytes, Max
open files is 32/32, and Max core file size is 0/0. The normalized `rlimits`
map must equal that reparse exactly.

Each OOM process record adds exact `cgroup_base64`,
`oom_score_adj_base64`, and `namespaces`. The child values are captured before
release. The OOM workload adds:

```text
barrier_transcript_base64,child_cgroup_read_monotonic_ns,
score_write_monotonic_ns,score_readback_monotonic_ns,
child_ready_monotonic_ns,release_monotonic_ns,
allocation_started_monotonic_ns,child_wait_monotonic_ns,raw_wait_status
```

The exact transcript is `P01B_OOM_CHILD_READY\n` followed by
`P01B_OOM_CHILD_RELEASE\n`. Times must satisfy
`child_cgroup_read < score_write < score_readback <= child_ready < release <
allocation_started < child_wait`. The retained child `oom_score_adj_base64`
must be the exact readback after the write and parse to the normalized value.
`raw_wait_status` independently decodes to signaled termination by SIGKILL.
The existing local cgroup event deltas and terminal process census remain
mandatory.

Each cgroup snapshot adds exact `observed_monotonic_ns` and
`raw_files_base64`. `raw_files_base64` contains exactly the same 19 keys as the
inherited normalized `files` map and their complete bytes; every normalized
value is reparsed from those bytes and exact map/key/value equality is
required. Pre must precede terminal. `cgroup.events` is parsed as
`populated`/`frozen` state, not a monotonic counter. Delta comparison applies
to `memory.events`, `memory.events.local`, `memory.swap.events`, `pids.events`,
and `cpu.stat`; OOM closure requires a
strict `oom` and `oom_kill` increment in both applicable event files, no
`oom_group_kill` increment, and agreement with the child wait status.

Native and normal projection validation reconstructs the original canonical
manifest and status by merging the normalized projections with the exact closed
excluded-telemetry key sets. Manifest exclusions are exactly
`python_version,zlib_version,archive_device,archive_inode,archive_mode,
archive_owner_uid,archive_link_count,archive_modified_seconds,
archive_modified_nanoseconds,archive_changed_seconds,
archive_changed_nanoseconds`. Status exclusions are exactly
`manifest_bytes,manifest_sha256`. Native and normal must match on fixture, header
ledger, inventory ledger, reconstructed manifest/status excluding only the
declared telemetry values, projection digest, and probe digest. Unknown or
missing excluded telemetry rejects.

## Corrected Manifest Semantics

The 151-test and 172-test numbers are different gates:

- 151 is the exact in-container normal workload from the frozen A3L3 corpus;
- 172 is the host repository's normal formal-preflight discovery count before
  the five non-discovery A3L6 files are imported directly by focused tests.

Neither count substitutes for the other.

The 11-file A3L3 corpus source manifest and the 21-file A3L8 snapshot are also
different objects:

- the corpus checker continues to validate its frozen 11 source files;
- A3L7 builds a new 21-file `snapshot-source-manifest-v1` from the immutable
  A3L6 commit and exact ordered source-path list;
- normal and OOM `input_manifest_sha256` bind the 21-file snapshot manifest;
- candidate snapshot files are separate mode-0600 copies of the mounted
mode-0444 snapshot and must reproduce the same bytes and ordered manifest.
The pair's top-level `implementation_commit` and `implementation_tree` equal
the gate source manifest, gate plan, gate bundle, and expected bindings; its
source/copy entries equal all 21 gate source rows. A3L9 replays this complete
identity chain, not only the entry byte-count/SHA projection.

`source-manifest.json` is a pair document with schema/domain
`hsai-p01b-snapshot-manifest-pair-v1` /
`hsai:p01b-snapshot-manifest-pair:v1` and exact fields
`schema,implementation_commit,implementation_tree,source_manifest,
snapshot_manifest`. Each nested manifest has schema/domain
`hsai-p01b-snapshot-source-manifest-v1` /
`hsai:p01b-snapshot-source-manifest:v1` or
`hsai-p01b-snapshot-copy-manifest-v1` /
`hsai:p01b-snapshot-copy-manifest:v1` and exact fields
`schema,ordered_entries`. Each of the 21 ordered entries contains exactly
`path,mode,bytes,sha256,descriptor_observation_sha256`; source entries retain
their committed modes and snapshot entries require mode 0444. Corresponding
bytes and SHA-256 values must match. `source-descriptor-observations.json`
uses schema/domain `hsai-p01b-snapshot-descriptor-set-v1` /
`hsai:p01b-snapshot-descriptor-set:v1` and exact fields
`schema,kind,manifest_sha256,ordered_observations`; `kind` is `source` and the
array has exactly 21 complete descriptor observations in manifest order.

`ingress-observations.json` uses the same schema with `kind=snapshot`, the
snapshot manifest digest, and exactly 21 observations over the mode-0444
mounted snapshot. `ingress-certificates.json` contains exactly two certificate
objects, one per attempt. The certificate predicate is reconstructed from the
prestart inspect mount object: one and only one mount has `Source` equal to the
snapshot root, `Destination=/input`, `Type=bind`, `RW=false`, and
`Propagation=rprivate`. The driver may not supply `container_mount_read_only`
as an unevaluated boolean.

The exact ordered 21 paths are:

```text
docs/796a-phase-hsai-p01b-archive-ledger-parser-and-acquisition-separation-boundary.md
tools/hsai-formal-preflight/bounded_runner.py
tools/hsai-formal-preflight/execution_state_machine.py
tools/hsai-formal-preflight/fixture_validator.py
tools/hsai-formal-preflight/p01b_archive_ledger.py
tools/hsai-formal-preflight/raw_archive_validator.py
tools/hsai-formal-preflight/tests/test_bounded_runner.py
tools/hsai-formal-preflight/tests/test_execution_state_machine.py
tools/hsai-formal-preflight/tests/test_fixture_validator.py
tools/hsai-formal-preflight/tests/test_p01b_archive_ledger.py
tools/hsai-formal-preflight/tests/test_raw_archive_validator.py
tools/hsai-formal-preflight/p01b_container_corpus.py
tools/hsai-formal-preflight/p01b_container_test_corpus.json
tools/hsai-formal-preflight/p01b_container_seccomp.json
tools/hsai-formal-preflight/p01b_container_seccomp_license.txt
tools/hsai-formal-preflight/p01b_container_seccomp_provenance.json
tools/hsai-formal-preflight/p01b_container_probe.py
tools/hsai-formal-preflight/p01b_container_evidence.py
tools/hsai-formal-preflight/p01b_container_execution.py
tools/hsai-formal-preflight/p01b_container_execution_tests.py
tools/hsai-formal-preflight/p01b_container_evidence_tests.py
```

## Exact Candidate Grammar

The candidate root contains no undeclared file or symlink. Fixed JSON files are
canonical and newline-free. Raw transcript files retain exact bytes.

```text
candidate/
  authority/{action,policy,evidence-bundle,a3l6-gate-bundle,admission-decision,authorization-root,expected-bindings}.json
  authority/user-authorization.txt
  readiness/{preauthorization-plan,readiness-result,authorization,campaign-plan,normal-plan,oom-plan,receipts}.json
  provenance/{git,docker-desktop,docker-client,buildx,docker-daemon,docker-context,image-config,rootfs}.json
  provenance/{docker-context,info-plist}.raw
  provenance/registry/{index,platform-manifest}.json
  provenance/signature/{verify,display}.json
  snapshot/{source-manifest,source-descriptor-observations,ingress-observations,ingress-certificates}.json
  snapshot/files/<exact 21 canonical relative paths>
  operations/readiness/<exact six zero-padded completion-role directories>/{observation.json,stdout.bin,stderr.bin}
  operations/campaign/<exact four zero-padded role directories>/{observation.json,stdout.bin,stderr.bin}
  operations/normal/<exact fifteen zero-padded role directories>/{observation.json,stdout.bin,stderr.bin}
  operations/oom/<exact fifteen zero-padded role directories>/{observation.json,stdout.bin,stderr.bin}
  reference/{native-result,projection,receipts}.json
  attempts/normal/{intent,cid-binding,timing,receipts,result,readiness-event,inspect-prestart,inspect-terminal,egress-certificate,cleanup-certificate}.json
  attempts/normal/export.tar
  attempts/oom/{intent,cid-binding,timing,receipts,result,readiness-event,inspect-prestart,inspect-terminal,egress-certificate,cleanup-certificate}.json
  attempts/oom/export.tar
  publication/prepublication-descriptor-plan.json
  candidate-manifest.json
```

The six readiness roles are `registry-index`, `registry-platform`,
`local-platform`, `buildx-version`, `codesign-verify`, and `codesign-display`.
The four campaign roles are `native-reference`, `docker-version`,
`docker-info`, and `image-config`. Raw command
bytes live exactly once under `operations/`; provenance registry/signature JSON
binds their observation and stream digests. Attempt role directories use the
zero-padded completion ordinal and exact role. Observation launch ordinals still
bind the plan, so export, release, and completed start retain their true
completion order. The emergency-kill role is always present as either an actual
observation or a `not_run` observation. `candidate-manifest.json` inventories
every other file.

The literal operation directory basenames are:

```text
readiness: 000-registry-index 001-registry-platform 002-local-platform
           003-buildx-version 004-codesign-verify 005-codesign-display
campaign:  000-native-reference 001-docker-version 002-docker-info
           003-image-config
normal:    000-absence-name-pre 001-absence-label-pre 002-create
           003-inspect-prestart 004-export-running 005-release
           006-start-attach 007-emergency-kill 008-wait
           009-inspect-terminal 010-remove 011-absence-cid
           012-absence-name 013-absence-label 014-daemon-recheck
oom:       the exact same fifteen basenames as normal
```

Names use lowercase ASCII exactly as shown. The start command retains launch
ordinal 4 while completion ordinal 6 records its spanning completion after
export and release. No directory is keyed only by launch ordinal. Every
observation's `stdout_path` and `stderr_path` must equal its canonical
candidate-relative operation paths, and each of the four receipt chains must
reconstruct those paths and the exact previous-digest sequence independently.

The authority input root must contain exactly its eight named files. The raw
UTF-8 user-authorization text is the exact user instruction authorizing this
program and its SHA-256 equals `user_authorization_sha256`. The canonical
expected-bindings document has its own domain digest and is copied into the
candidate; expected constants outside that bound document cannot close a class.
The readiness root must contain exactly its seven named canonical files plus the
fixed provenance transcript inputs named above. Copying an arbitrary tree or
accepting extras is forbidden.

The exact payload census is 200 files and the manifest is file 201. Each JSON
or result is at most 1,048,576 bytes, each metadata/raw registry stream is at
most 262,144 bytes, each ordinary stream is at most 16,384 bytes, each TAR is
at most 16,777,216 bytes, each snapshot file is at most 16,777,216 bytes, and
the aggregate candidate is at most 134,217,728 bytes. A different census or
larger aggregate rejects.

The prepublication descriptor plan has schema/domain
`hsai-p01b-prepublication-descriptor-plan-v1` /
`hsai:p01b-prepublication-descriptor-plan:v1` and exactly
`schema,candidate_root,parent_identity,staging_identity,expected_file_count,
expected_manifest_path,overwrite_policy`. Overwrite policy is `exclusive`.
`expected_file_count` is exactly 201.
The caller-selected output parent is outside the repository and audit/failure
roots. For lowercase identifier `campaign_id`, staging and final basenames are
exactly `.p01b-staging-<campaign_id>` and `p01b-candidate-<campaign_id>` in that
same retained parent descriptor. Neither basename contains the candidate
manifest digest, preventing a self-reference cycle. `candidate_root` is the
canonical final path and `expected_manifest_path` is its exact child
`candidate-manifest.json`.

The canonical expected-bindings document has schema/domain
`hsai-p01b-expected-bindings-v1` /
`hsai:p01b-expected-bindings:v1` and exact fields:

```text
schema,predecessor_commit,implementation_commit,implementation_tree,
user_authorization_sha256,claim_boundary,claim_boundary_sha256,
a3l6_audit_commit,a3l6_gate_plan_sha256,
a3l6_gate_source_manifest_sha256,a3l6_gate_bundle_sha256,
expected_focused_test_ids_sha256,validator_sha256,collector_sha256,
expected_focused_test_count,protected_path,protected_sha256,
native_python_path,native_python_sha256,native_python_version,
sandbox_exec_path,sandbox_exec_sha256,gate_sandbox_profile_sha256,
normal_python_path,normal_python_version,normal_interpreter_policy,
git_path,git_sha256,docker_path,docker_sha256,buildx_path,buildx_sha256,
codesign_path,codesign_sha256,docker_desktop_info_plist_path,
docker_desktop_info_plist_sha256,docker_desktop_vm_path,
docker_desktop_vm_sha256,docker_desktop_kernel_path,
docker_desktop_kernel_sha256,docker_app_candidate_cdhash_full,
docker_app_team_identifier,docker_context_path,docker_context_sha256,
index_reference,index_manifest_sha256,selected_platform,
selected_descriptor_digest,selected_descriptor_size,
selected_descriptor_media_type,platform_reference,platform_manifest_sha256,
platform_manifest_size,platform_manifest_media_type,image_config_digest,
rootfs_diff_ids,snapshot_source_manifest_sha256,snapshot_copy_manifest_sha256,
seccomp_sha256,normal_expected_test_count,discovery_expected_test_count,
candidate_payload_count,attempt_deadline_ns,class_order,evidence_level
```

The exact user authorization bytes are UTF-8, contain the complete user message
that authorized retained normal/OOM execution and independent acceptance, and
have no normalization or appended newline. Its raw SHA-256 must equal
`user_authorization_sha256`. The implementation accepts no ambient default or
CLI override for any expected binding. Readiness fills only values derived from
the two raw registry responses and local observations, then freezes and hashes
this document before final authorization; A3L8 cannot alter it.

The embedded claim boundary has schema/domain
`hsai-p01b-local-claim-boundary-v1` /
`hsai:p01b-local-claim-boundary:v1` and exact fields
`schema,evidence_level,ordered_honesty_assumptions,ordered_nonclaims`.
`evidence_level` is `Level1LocalReplayOrLower`. The assumption array is exactly
`["signed-docker-app-honest","docker-daemon-honest","probe-code-honest",
"host-driver-honest","native-python-runtime-stdlib-honest",
"host-system-tool-honest","reviewed-gate-test-code-honest"]` in that order.
The nonclaim array is exactly
`["not-level2","not-external-reproduction","not-benchmark-evidence",
"not-semantic-proof","not-production-readiness","not-sota",
"not-breakthrough","not-full-security","not-external-audit",
"not-accepted-evidence-ledger-evidence"]` in that order. Its recomputed domain
digest equals `claim_boundary_sha256`. Expected bindings embeds both object and
digest; a digest-only or reordered substitute rejects.

Native interpreter expectations are exactly `/usr/bin/python3`, SHA-256
`7f30f076d0e9c38f772a76449fca9da8cf97f6a3d43b94c90a00e4f9ce7ad39e`,
and version `3.9.6`. Normal expectations are exactly
`/usr/local/bin/python3`, version `3.11.15`, and policy
`probe-observed-ordered-chain-under-probe-honesty`. The normal terminal binary
hash and ordered chain are retained observations rather than preauthorized
constants; C02 closes correspondence to that observed identity under probe
honesty, not independently redistributed interpreter bytes.
`expected_focused_test_count` is 64 and `candidate_payload_count` is 200.
`validator_sha256` and `collector_sha256` equal the gate source-manifest rows
for `p01b_container_evidence.py` and `p01b_container_execution.py`
respectively and the same immutable snapshot entries.

`authority/evidence-bundle.json` retains the prior validated HSAI admission
evidence schema and semantics. The distinct
`authority/a3l6-gate-bundle.json` is the A3L6 immutable gate bundle with
schema/domain `hsai-p01b-a3l6-gate-bundle-v1` /
`hsai:p01b-a3l6-gate-bundle:v1` and exact fields
`schema,gate_plan,gate_source_manifest,implementation_commit,implementation_tree,
python_path,python_sha256,
python_version,python_version_observation,ordered_gate_observations,focused_test_ids,
focused_test_count,discovery_test_count,ordered_review_records,result`.

The embedded gate plan has schema/domain `hsai-p01b-a3l6-gate-plan-v1` /
`hsai:p01b-a3l6-gate-plan:v1` and exact fields
`schema,implementation_commit,implementation_tree,audit_commit,python_path,
python_sha256,python_version,environment,gate_source_root,
gate_source_root_identity,gate_temp_root,sandbox_exec_path,
sandbox_exec_sha256,sandbox_profile_path,sandbox_profile_sha256,
gate_source_manifest_sha256,cwd,commands,reviewed_paths,
expected_focused_test_ids,expected_focused_test_count,
expected_discovery_test_count`. Environment is exactly `HOME=/nonexistent,
LANG=C,LC_ALL=C,PATH=/usr/bin:/bin,PYTHONDONTWRITEBYTECODE=1,
TMPDIR=<gate_temp_root>` with no additional key.
`gate_source_root` is the canonical external immutable tree described below;
cwd equals it. Gate source binding is defined before the three direct-argv rows.

The embedded gate source manifest has schema/domain
`hsai-p01b-a3l6-gate-source-manifest-v1` /
`hsai:p01b-a3l6-gate-source-manifest:v1` and exact fields
`schema,implementation_commit,implementation_tree,audit_commit,git_path,
git_sha256,environment,repository_cwd,materialized_root,
materialized_root_identity,gate_temp_root,sandbox_exec_descriptor_observation,
sandbox_profile_path,sandbox_profile_descriptor_observation,
sandbox_profile_base64,sandbox_profile_sha256,
materialized_inventory_before_sha256,
materialized_inventory_before,materialized_inventory_after_sha256,
materialized_inventory_after,head_observation,tree_observation,
status_before_observation,ordered_blob_observations,ordered_sources,
pre_gate_capture_ended_monotonic_ns,post_gate_capture_started_monotonic_ns,
status_after_observation`. Source observations use the complete bounded
command-observation schema below. Their exact direct argv are, in order,
`git rev-parse HEAD`, `git rev-parse <implementation_commit>^{tree}`,
`git status --porcelain=v2 -z --untracked-files=all`, 21
`git cat-file blob <implementation_commit>:<source-path>` commands for every
path in the exact ordered 21-path list above, and the identical status command
after all three gates.
HEAD equals `audit_commit`; the tree equals `implementation_tree`; both status
byte strings are complete and byte-equal. Parsed status may disclose unrelated
dirty paths, but none of the 21 source paths, their ancestor path types,
or `.gitmodules` may be modified, deleted, renamed, type-changed, or untracked.
Every source-capture observation uses the frozen Git path/hash, plan
environment, repository cwd, closed stdin, 60-second timeout, 16,384-byte stderr cap, exit
zero, null signal, empty stderr, false truncation, and complete raw SHA-256.
HEAD/tree stdout caps are 4,096 bytes, status caps are 1,048,576 bytes, and
blob stdout caps are 16,777,216 bytes.
For both streams of every HEAD/tree/status/blob observation,
`total_bytes == retained_bytes == decoded_base64_length <= configured_cap`,
the truncation flag is false, and the recorded SHA-256 equals the digest of the
decoded complete bytes.

Each of the 21 ordered source rows contains exactly
`path,git_object_expression,git_blob_oid,bytes,sha256,
pre_gate_started_monotonic_ns,pre_gate_ended_monotonic_ns,
pre_gate_descriptor_observation,post_gate_started_monotonic_ns,
post_gate_ended_monotonic_ns,post_gate_descriptor_observation`. The object
expression is `<implementation_commit>:<path>`. `git_blob_oid` is independently
recomputed as 40-lowerhex SHA-1 over
`b"blob " + decimal_byte_length + b"\0" + exact_blob_bytes`; raw
stdout bytes are written directly through exclusive descriptor-relative opens
to `materialized_root/<path>`. Both complete descriptor observations have that
materialized path and repository-relative path, equal each other,
and bind the same byte count and SHA-256. All four row timestamps and the two
manifest capture timestamps are integers with strict start/end ordering:
every pre-gate descriptor read and source observation ends no later
than `pre_gate_capture_ended_monotonic_ns`, that value is no later than the
first gate start, the last gate end is no later than
`post_gate_capture_started_monotonic_ns`, and every post-gate descriptor read
and final status observation starts at or after that value.
The materialized root is outside the repository, audit, candidate, and output
roots under a new mode-0700 parent. The parent path is exactly
`/private/tmp/hsai-p01b-gate-<32-lowerhex>`; source, scratch, and profile paths
are its exact children `source`, `scratch`, and `gate.sb`. The identifier is
ASCII lowercase hex, so every substituted Seatbelt path matches safe grammar
`/[A-Za-z0-9._/-]+` and contains no quote, backslash, whitespace, control byte,
or escape sequence. Construction rejects a preexisting root,
symlink, hard link, special file, path traversal, duplicate path, or extra
entry. It creates exactly the directories implied by the ordered 21 paths,
writes exactly those 21 verified Git-blob bytes as mode 0444 regular files,
then changes every implied directory and the tree root to mode 0555. The
parent remains mode 0700 and retained by the gate driver. Before and after all
gates, descriptor-relative no-follow traversal must find exactly those 21
files and implied directories, no `.pyc`, `__pycache__`, shadow module,
symlink, or extra entry. Both complete embedded inventory arrays contain exact
rows `path,type,mode,device,inode,uid,gid,link_count,bytes,sha256`. `path` is
`.` for the root and otherwise the canonical root-relative path; rows are in
bytewise path order with `.` first. `type` is exactly `directory` or `regular`.
`mode` is the canonical decimal JSON integer `stat.S_IMODE(st_mode)`.
Directory mode is `365` (octal 0555) and `bytes,sha256` are null; regular mode is `292` (octal 0444),
`link_count=1`, `bytes` is a nonnegative integer, and `sha256` is 64 lowerhex.
All identities are nonnegative integers, all regular-file `(device,inode)`
pairs are unique, and the row set is exactly the root, implied directories,
and 21 declared files. `materialized_root_identity` contains exactly
`device,inode,mode,uid,gid,link_count` and equals the `.` row projection.
Before/after arrays are byte-equal. Each stored inventory SHA-256 is raw
SHA-256 of its canonical array and the two digests equal. The gate never makes
the tree writable.
Every regular inventory row's
`path,mode,device,inode,uid,gid,link_count,bytes,sha256` projection byte-equals
the same projection from both matching pre/post gate-source descriptor
observations. Internally stable but cross-inconsistent inventories reject.
Concretely, inventory `bytes` equals
`pre.before.size == pre.after.size == post.before.size == post.after.size`;
mode/device/inode/uid/gid/link_count equal every corresponding nested
`before`/`after` identity field; and inventory SHA-256 equals both descriptor
top-level SHA-256 values.

The system-enforced gate wrapper is `/usr/bin/sandbox-exec`, frozen SHA-256
`556b22a255f0c6d5f3811194a2622c165cfcfabbfbe50f95d92190ff81e99470`.
Its complete no-follow descriptor observation and profile bytes are embedded;
path/hash equal the plan and expected bindings. The profile is a canonical
UTF-8 Seatbelt expression with final LF, `deny default`, process/signal,
sysctl-read and global metadata-read allowances; byte-read
allowances are exactly the materialized root, gate temp root,
`/System/Library`, `/usr/lib`, `/usr/bin`, `/bin`,
`/Library/Developer/CommandLineTools`, `/private/etc`, `/dev/null`, and
`/dev/urandom`; byte-write allowance is exactly the gate temp root and
`/dev/null`; and `network*` remains denied. Substituted roots are canonical
quoted literals in these exact bytes:

```text
(version 1)
(deny default)
(allow process*)
(allow signal)
(allow sysctl-read)
(allow file-read-metadata)
(allow file-read* (subpath "<materialized_root>") (subpath "<gate_temp_root>") (subpath "/System/Library") (subpath "/usr/lib") (subpath "/usr/bin") (subpath "/bin") (subpath "/Library/Developer/CommandLineTools") (subpath "/private/etc") (literal "/dev/null") (literal "/dev/urandom"))
(allow file-write* (subpath "<gate_temp_root>") (literal "/dev/null"))
(deny network*)
```

There is exactly one LF after every rendered line including the last, and no
literal angle-bracket token remains. The base64-decoded bytes hash to `sandbox_profile_sha256`,
the exclusive profile file is mode 0400 under the retained parent, and its
no-follow reopen matches before every gate. No unsandboxed fallback exists.

`gate_temp_root` is a separate empty mode-0700 directory under the retained
parent, is exported as `TMPDIR`, and is the only general write/read/execute
scratch root. It is not an import root at gate start. A3L6 negative tests must
show direct IPv4, IPv6, DNS, and arbitrary Mach-service lookup fail under the
exact profile while process/tempfile controls succeed. The sandbox denial is
inherited by child processes, so same-UID gate code cannot chmod, replace, or
read alternate user code outside the declared roots. System framework,
stdlib, dynamic-library, and system-tool bytes remain under the explicit
`native-python-runtime-stdlib-honest` and `host-system-tool-honest`
assumptions; this is project-source execution-byte closure, not a claim that
macOS/Python system runtime bytes were redistributed or independently proved.
Verified tests deliberately generate and execute bounded helper programs under
scratch for executor regressions. Those dynamic scratch bytes are not imported
project modules and are not claimed content-bound; their behavior is under the
explicit `reviewed-gate-test-code-honest` assumption. Therefore the narrower
claim is immutable initial project-source/import closure, not closure of every
byte later generated by the tests.

Wrapped Python argv adds `-E -s -S -B` in that order. `-E/-s/-S` excludes
environment, user-site, and site-package import roots; `-B` plus the no-extra
read-only tree excludes source-tree bytecode. Every plan command begins
`[/usr/bin/sandbox-exec,-f,<sandbox_profile_path>,/usr/bin/python3]`. Every
gate observation executable identity is sandbox-exec; its argv element three
and the separately retained Python identity/version observation bind the native
interpreter. Every gate observation cwd equals `materialized_root`; it embeds
exact `cwd_identity_before,cwd_identity_after`, both equal each other and the
plan/source-manifest root identity. The executor opens the root no-follow,
verifies identity, and uses `fchdir` on that retained descriptor immediately
before spawn. Under `host-driver-honest`, the retained mode-0700 parent is not
concurrently mutated. Thus the gates execute the materialized Git-blob project
sources rather than mutable worktree paths.

The manifest domain digest
equals `expected_bindings.a3l6_gate_source_manifest_sha256`; every A3L6 review
binds that digest. The A3L7 immutable 21-file source manifest entries for these
21 paths must repeat the same byte counts and SHA-256 values, and A3L9
replays the Git-blob, descriptor, gate, review, and snapshot equalities.

The three exact direct-argv roles are:

```text
evidence-focused:  /usr/bin/sandbox-exec -f <profile> /usr/bin/python3 -E -s -S -B tools/hsai-formal-preflight/p01b_container_evidence_tests.py -v
execution-focused: /usr/bin/sandbox-exec -f <profile> /usr/bin/python3 -E -s -S -B tools/hsai-formal-preflight/p01b_container_execution_tests.py -v
formal-discovery:  /usr/bin/sandbox-exec -f <profile> /usr/bin/python3 -E -s -S -B -m unittest discover -s tools/hsai-formal-preflight/tests -p test_*.py -v
```

Each `commands` row has exactly
`role,argv,environment,cwd,stdin_policy,timeout_ns,stdout_cap_bytes,
stderr_cap_bytes,activation,expected_exit_code,expected_signal`. Values are the
role and argv above, the exact plan environment and cwd, `stdin_policy=closed`,
`timeout_ns=600000000000`, both stream caps `262144`, `activation=always`,
`expected_exit_code=0`, and null `expected_signal`. No shell, inherited
environment, ambient working directory, stdin byte, alternate activation, or
per-role override is accepted.

The first two roles run exactly 32 immutable test ids each, 64 total; the
discovery role runs exactly 172. Focused ids are a sorted, unique, complete
AST/TestLoader census of all `test_*` methods in the two non-discovery files,
with exact per-file count 32. The A3L6 audit commit freezes the literal 64-id
array before readiness, and two code reviewers validate the category census:
canonical/schema/domain, candidate/path/manifest, probe/raw reconstruction,
inspect/certificate/class atomicity, bounded executor, readiness/provenance,
snapshot/descriptor, lifecycle/intent/recovery, publication/repository state,
and external CLI/review acceptance. `expected_focused_test_ids_sha256` is raw
SHA-256 of the canonical literal array. `reviewed_paths` is exactly the five
A3L6 Python paths `p01b_container_probe.py`, `p01b_container_evidence.py`,
`p01b_container_execution.py`, `p01b_container_evidence_tests.py`, and
`p01b_container_execution_tests.py` under `tools/hsai-formal-preflight/`, in
that order. The gate-plan domain digest
must equal `a3l6_gate_plan_sha256` in expected bindings.

The gate plan is cross-bound, not merely digest-adjacent:
`gate_plan.audit_commit == expected_bindings.a3l6_audit_commit`;
`gate_plan.gate_source_manifest_sha256` equals the embedded source-manifest
domain digest and `expected_bindings.a3l6_gate_source_manifest_sha256`;
plan/source-manifest `gate_source_root` and root identity are byte-equal;
plan/source-manifest/expected-binding sandbox-exec and profile hashes are
byte-equal;
`gate_plan.expected_focused_test_ids` canonical array SHA-256 equals
`expected_bindings.expected_focused_test_ids_sha256`;
`gate_plan.expected_focused_test_count ==
expected_bindings.expected_focused_test_count`; and
`gate_plan.expected_discovery_test_count ==
expected_bindings.discovery_expected_test_count`. The audit commit is an
observed Git identity: it equals the parsed HEAD from candidate
`provenance/git.json` and the external repository-state `before` capture.
Calling it authorized metadata without that retained observation is forbidden.
The Python identity is one equality chain:
`gate_plan.python_path == gate_bundle.python_path ==
expected_bindings.native_python_path == /usr/bin/python3`;
the three corresponding SHA-256 values equal
`expected_bindings.native_python_sha256`; and all versions equal
`expected_bindings.native_python_version == 3.9.6`. Every gate argv element
three equals that Python path. Every gate argv element zero and observation
`executable_path`/`executable_sha256` equals the plan/expected sandbox-exec
path/digest; element one is `-f`, and element two is the exact profile path.
The bundle's `python_version_observation` uses the full
bounded observation schema for exact direct argv
`[/usr/bin/python3,--version]`, the plan environment/cwd/closed stdin, 16,384
byte caps, exit zero, null signal, false truncation, exact stdout
`Python 3.9.6\n`, and empty stderr. Its executable path/hash equals the same
chain. Any digest-adjacent but unequal identity rejects.

Each gate observation has exactly
`role,argv,environment,cwd,stdin_policy,executable_path,executable_sha256,
cwd_identity_before,cwd_identity_after,
timeout_ns,stdout_cap_bytes,stderr_cap_bytes,started_monotonic_ns,
ended_monotonic_ns,outcome,exit_code,signal,stdout_total_bytes,
stdout_retained_bytes,stdout_truncated,stdout_base64,stdout_sha256,
stderr_total_bytes,stderr_retained_bytes,stderr_truncated,stderr_base64,
stderr_sha256`. It must match its plan row. `outcome` is `completed`; time is
strictly increasing and within timeout; total and retained byte counts equal
the decoded complete base64 length; raw digests match; counts do not exceed
caps; and both truncation flags are false.
Observations occur in fixed role order and do not overlap. For every gate row,
`pre_gate_capture_ended_monotonic_ns <= started_monotonic_ns <
ended_monotonic_ns <= post_gate_capture_started_monotonic_ns`; the first/last
terms are therefore the minimum start and maximum end over all three rows, not
unquantified aliases. Every post-gate descriptor and final inventory/status
capture starts after that maximum end.
All three require command exit 0, null signal, no truncation, empty stdout, and
verbose unittest stderr whose ordered test ids equal the plan. Focused summaries
must parse `Ran 32 tests in <finite-decimal>s` and discovery must parse
`Ran 172 tests in <finite-decimal>s`; each ends with exactly `OK\n` after the
standard separator. A skipped/error/failure/unexpected id rejects.
Review records use schema/domain `hsai-p01b-a3l6-code-review-v1` /
`hsai:p01b-a3l6-code-review:v1` and exact fields
`schema,role,reviewer_id,implementation_commit,implementation_tree,
ordered_file_sha256,gate_plan_sha256,gate_source_manifest_sha256,
gate_observation_sha256,findings,result`.
`gate_plan_sha256` equals the embedded gate plan's domain digest and
`a3l6_gate_plan_sha256` in expected bindings. `gate_source_manifest_sha256`
equals the embedded manifest's domain digest and the expected-binding value.
The ordered file array has exactly the five A3L6 paths and raw SHA-256 values;
it byte-equals the five reviewed-path projection of the embedded 21-row source
manifest, those five Git cat-file byte hashes, and the corresponding A3L7
snapshot-manifest entries. Roles are
`security-capability` and `correspondence-reproducibility`; reviewer ids differ;
findings use the same closed grammar as A3L9; result is accept only when empty.
`gate_observation_sha256` is raw SHA-256 of the canonical ordered gate
observation array. Review records are embedded in fixed role order.
The result is `accept` only when every gate exits zero, exact focused ids and
counts match, discovery count is 172, both reviews have no findings, and all
implementation identities agree. Bundle acceptance also recomputes the
embedded gate-plan domain digest, requires both review `gate_plan_sha256`
values to equal it, recomputes and cross-binds the gate source manifest and
both ordered file arrays, revalidates the Git/status/descriptor bracketing, and
applies every gate-plan/expected-bindings/Python cross-equality above. Both
A3L9 reviews revalidate this complete embedded bundle; a test-count constant
alone is invalid C06 evidence.
`a3l6_gate_bundle_sha256` in expected bindings, preauthorization,
authorization root, final authorization, and fresh-review input digests must
all equal the domain digest of `authority/a3l6-gate-bundle.json`.
`evidence_bundle_sha256` must separately equal the domain digest of the prior
`authority/evidence-bundle.json`; the two digests and schemas may not be
interchanged.

`authority/authorization-root.json` has schema/domain
`hsai-p01b-local-authorization-root-v1` /
`hsai:p01b-local-authorization-root:v1` and exact fields
`schema,user_authorization_sha256,action_sha256,policy_sha256,
evidence_bundle_sha256,a3l6_gate_bundle_sha256,admission_decision_sha256,
preauthorization_sha256,
expected_bindings_sha256,readiness_sha256,implementation_commit,
implementation_tree,authority_granted`. It validates the parsed local action,
claim ceiling, implementation, and no-network A3L8 scope; `authority_granted`
must be true and means only this bounded local program. It is distinct from the
decision/receipt/acceptance evidence-authority booleans, which remain false;
it never grants accepted evidence or Level2+ authority.

The preauthorization plan has schema/domain
`hsai-p01b-container-preauthorization-plan-v2` /
`hsai:p01b-container-preauthorization-plan:v2` and exact fields
`schema,user_authorization_sha256,predecessor_commit,action_sha256,
policy_sha256,evidence_bundle_sha256,a3l6_gate_bundle_sha256,
admission_decision_sha256,
implementation_commit,implementation_tree,readiness_plan_sha256`. The final
authorization has schema/domain `hsai-p01b-container-authorization-v3` /
`hsai:p01b-container-authorization:v3` and exact fields
`schema,authorization_id,authorization_root_sha256,user_authorization_sha256,
action_sha256,policy_sha256,
evidence_bundle_sha256,a3l6_gate_bundle_sha256,admission_decision_sha256,
expected_bindings_sha256,
implementation_commit,implementation_tree,readiness_sha256`. It is emitted only
after an accepted readiness result. Campaign/normal/OOM plans then bind this
authorization digest one-way; authorization never hashes those plans, so no
authorization-plan cycle exists. The action,
policy, evidence bundle, admission decision, and authorization root retain
their prior validated HSAI schemas and must all authorize this exact local
container action, commit, claim ceiling, and no-network A3L8 plan. A digest
match without parsed semantic authorization rejects.

`docker-context.raw` is the complete no-follow context metadata file. Its
companion JSON has schema/domain `hsai-p01b-docker-context-v1` /
`hsai:p01b-docker-context:v1` and exact fields
`schema,path,descriptor_observation,descriptor_observation_sha256,bytes,sha256,name,host,
skip_tls_verify`. The raw bytes must parse with duplicate-key rejection to the
single `desktop-linux` endpoint bound by the final authorization; unrecognized
context keys or endpoints reject.
The embedded complete descriptor observation uses the descriptor schema above;
its recomputed domain digest equals `descriptor_observation_sha256`, its path
and streamed byte count/digest equal the companion fields and retained raw
file, and its before/after identities are revalidated. A digest-only context
descriptor is invalid.

### Corrected empty-object domain vectors

For canonical `{}` bytes, the newly frozen domains produce exactly:

```text
descriptor-observation 7d075cc4f12c129ae6462455bddfc4d4d660906934c60fae7139a48bd87e461d
descriptor-set         9cadf313980658146a10eb1ab0dd32224e436bf074a8765834406de43da1c03f
transcript-binding     d952bf58ab94dae5069c7b75954bd20a2d27d433727c3db00be90a85eb9b5035
host-provenance       3aedd7d473bf4667af8767a5ee41671c1961531035a8e129dd9f281551fb1896
readiness-plan-v2      22468c0f1d4e4b6e84916f22075bbd9cecb5e504859001683c84198a3d36dcd6
readiness-result-v2    5aa3a99093842a6158edfc8ce635d946effdd9a132999d1472884125f5af7cc0
container-intent       323965bcf7fa6487e628241d1e389bf920a0dadc8ac0ebafa7cad4a02945a35e
cid-binding            849b872bc564e12e837daa37c28af9e4e5dc0ba25250b879faa555c41a0bd9b8
recovery-inspection    6f5e171a8a3c508aceb49be68bf0febb8e03938cd1d3d6cd1a093ad20d8c4787
recovery-inspect-fail  5749dc1105444219cfdf128b62592fd61f0a768d018e428050b3ee5da3dc59a4
recovery-cleanup       5820a836f3b38cd21a750a73658d1cd641c07a4049f7f332cb1b21f16c55e737
recovery-result        d0a267583ffa38485370c97817a500b69a6e9e63b9bddd58175d19505aad3776
publication-v2         a97ea598ea7f4407319c9938578f7954ca1b0173876823e8e369e4d5e093d774
publication-inventory  16a3e6b263facfc1cef814a2848fb4ce23da665a7979e8c06c2098fbed4e7950
repository-state       bfa43a6596fa21e89efa05f355af5df20a589ece52adb9db5f7f9b8a390a8ba7
repository-state-plan  45e1aa74157473add63f741b40f174769e47b7f421c747dfdd630e96e3eb8b5f
repository-capture     5f99736abd662c4a14f920e27d9294da31852e0aaeeeae59142ef791bf41dd07
decision-v3            8bd19a6cfb664faee136e0f56a8b3e5cec4c0f5dfa987f618609a80d6262a1b5
review-v2              51359945d7a223b0ba7b338f39e01fed591122c7c161c866a5a1d4926e0e029a
review-session         118a5bc1291451881914a75ec6cc57a777113ff7b11497980b397d6b7d140757
review-session-durable d95d9da5a21efa057501ea2aa314817b9a26201ec7597ed060ec4f820bca04f4
review-launch          56c5c43962abb4cbbafed4a84d3ea9cc651c557098c3afb2b2e40d846cb4224e
fresh-validation       ff1aeaf4762a843a89e3aa55abd154de900643c5d510e1dbe8bfa3bfa925cfbd
aggregate-v2           2a40a172f911ac06bb17111bdb5583c04ed07fbcd0d7c472c2d579b66dfab879
acceptance-v2          bdff1e0fdbb07f0c0ca92af173b319e7caad84e4f344cda25dd8dbb298064821
attempt-timing         571510140b0b6af682e737afca2b8948d31bba2cee271bbbd50b4ba589e1d396
snapshot-pair          4205228c67a1ee6edcca726a5d4fd51dcbb95109d0d465d0a58d86878f0b3d80
snapshot-source        0b61239a19ca0dd4c42c47f31c439d8538a2833998f4e637b6c4e66b86d3a654
snapshot-copy          da14ad924c103743ef65b1a6e6ccb9b66d505e0ccaff67e7f4e4fbff3a469fa2
snapshot-descriptor    27e6a1754d4839a9413c57afd1e854d59cf61375acc2e7a735f99a9d9fed7a79
prepublication-plan    db6460690b998fdba8c502e6c3fe485c527fcd7e9651ea2cf9e660140b912437
expected-bindings      89dde07525c79c731ab77e9f8fa3636fd9fa11f99821e5047a4ba34958d82543
claim-boundary         2788053e1498a8730b1bad7bba62bbe83455351802ef0ae82c234f31ec6d0912
docker-context         200f13d823d114f4955e6147aeb6adf6bf54c95abce0ff0c412e93a43e9ef928
a3l6-gate-bundle       de53fc8e310fe4330f7bccd04e83f256e348fed1487bb08fd23ff7c6b3af0341
a3l6-gate-plan         217a1e5d5e0fde2423460954d23be7ecd6b75c7af7837f8dea65b6eb3e73616c
a3l6-gate-source       77695148772b5dafdbfcdb028053417f80c23cbe2c030e6ebb8cba460e67b07e
a3l6-code-review       f28f323dd2a54c51b981985696a6d7eba41d0446a12ee555e4d35664581d20fe
authorization-root     3475fc80467ec7140cf2f33d72c33d099316fc4bd8d09f2076cbb77ef33b384f
receipt-chain          3459a485884ebdcb01810739187d2bc602ef6488ad194b0996e735db6132286b
preauthorization-v2    93a0f949d4da91fecb607cdec7f29984c44368d0157c2023590b36b4f1c8ca9b
authorization-v3       65e0ffed10bbdea3705a0d3f7dbd27d5d493996f1b54c6e2b5678fc258ddcf64
```

## Corrected Class Reconstruction

`p01b_container_evidence.py` exposes pure-data reconstruction in two steps:

```text
validate_prepublication_candidate(files, manifest, expected_bindings)
reconstruct_published_candidate(files, manifest, publication_record,
                                repository_state, expected_bindings)
```

The driver materializes all payloads, builds and writes the manifest, then calls
the first function over exactly the 200-file payload byte map and the separate
manifest bytes before publication. It rejects unless the supplied expected
bindings parse byte-identically to `authority/expected-bindings.json`. It
returns no class decision. The second additionally validates the v2
publication record and repository-state record, recomputes every predicate from
retained raw bytes and explicitly labeled local observation records, and
returns the ordered eight class booleans. Third-party executable/VM/kernel
bytes are not redistributed; their recorded hashes close only probe/driver-
observed identity under the named honesty assumptions. Neither accepts
certificate predicates, driver
booleans, expected constants, receipts, or the prior decision as substitutes
for raw reconstruction.

C02 requires native/normal projection correspondence plus exact interpreter and
snapshot bindings. C03 requires raw OOM readback/order/wait/cgroup
correspondence. C04 requires raw proc/security bytes, exact seccomp snapshot
bytes, targeted inspect controls, namespace identities, and the explicit LSM
identity/nonclaim. C05 requires both complete raw cgroup censuses and exact
deltas. C06 requires mountinfo, rlimits, command controls, streams, wall bounds,
and the hermetic executor regressions. C07 requires both raw registry manifests,
local image resolution, current descriptor observations, signature/Buildx
transcripts, daemon/info/image transcripts, and probe runtime identities. The
platform manifest's config descriptor must equal the Docker daemon's exact
`image inspect` config id and the expected RootFS diff IDs. No raw OCI config
blob is retained because the authorization permits only two registry reads;
C07 is therefore local index/platform-manifest-to-daemon correspondence under
the explicit Docker-daemon honesty assumption, not raw registry config-blob
reconstruction. C09
requires the exact snapshot, running export/TAR result, v2 publication record,
final reopen, and staging absence. C10 requires authorization, plan-derived
commands, raw observation-to-receipt reconstruction, durable intent/CID
binding, exact lifecycle order, cleanup absence, and daemon reachability.

Any missing or false predicate causes reconstruction failure or an atomic
reject. The driver never supplies class truth.

## A3L9 Reviewer Execution

The execution module exposes hermetic filesystem-reader subcommands only after
publication:

```text
decide-v3
review-v2
aggregate-v2
accept-v2
```

Each is invoked as a fresh direct-argv `/usr/bin/python3 -I -B` process against
the immutable 21-file snapshot. The exact argv prefix is
`[/usr/bin/python3,-I,-B,<absolute-snapshot>/tools/hsai-formal-preflight/
p01b_container_execution.py,<subcommand>]`; no other entrypoint is accepted.
Every A3L9 process environment is exactly
`HOME=/nonexistent,LANG=C,LC_ALL=C,PATH=/usr/bin:/bin,
PYTHONDONTWRITEBYTECODE=1` with no extra key; cwd is `/` and stdin is closed.
`decide-v3` requires explicit
`--candidate-root`, `--publication-record`, `--repository-state`,
`--expected-bindings`, `--implementation-commit`, and exclusive
`--decision-output` arguments. It is the only route that emits the external v3
decision. `review-v2` requires explicit
`--candidate-root`, `--publication-record`, `--repository-state`,
`--candidate-decision`, `--expected-bindings`, `--review-session`,
`--review-session-durability`, `--role`, `--reviewer-id`,
`--implementation-commit`, `--receipt-output`, and `--review-output` arguments.
The complete `review-v2` option order is exactly
`--candidate-root <canonical-final-root> --publication-record <canonical-abs>
--repository-state <canonical-abs> --candidate-decision <canonical-abs>
--expected-bindings <canonical-abs> --review-session <canonical-abs>
--review-session-durability <canonical-abs> --role <fixed-role>
--reviewer-id <bounded-id> --implementation-commit <40-lowerhex>
--receipt-output <canonical-exclusive-abs> --review-output
<canonical-exclusive-abs>`. The two output paths are distinct and derived from
the session id and role. No option reordering, abbreviation, duplicate, omitted
value, alternate path spelling, or extra option is accepted. The receipt's
stored argv and parent launch observation byte-equal this reconstructed array.
`aggregate-v2` requires two explicit receipt paths, two explicit review paths,
and two explicit review-launch paths in fixed role order, the review session
and durability paths, plus all common input paths and one exclusive aggregate
output. `accept-v2` requires the same four receipt/review paths, the two launch
paths, session/durability paths, aggregate, all common inputs, and one exclusive
acceptance output. No
implicit artifact discovery, ambient `PYTHONPATH`, module execution, or network
access is permitted.

The execution script opens the sibling `p01b_container_evidence.py` no-follow,
reads its complete bytes through the retained descriptor, verifies fstat
before/after, snapshot-manifest hash, and expected raw SHA-256, then compiles
those exact bytes with the verified canonical filename and executes that code
object in a newly constructed module namespace. It does not call a path-based
source loader or reopen the pathname. Bare sibling import is forbidden, so
isolated mode cannot silently select another module. The same rule applies to
every fresh subcommand.

`review-v2` takes the final candidate root, publication record, exact expected
bindings, role, reviewer id, immutable implementation commit, and an exclusive
output path. It opens candidate files no-follow, rejects extras, rechecks mode,
link count, bytes, and manifest, calls only
`reconstruct_published_candidate`, and emits one review record. It does not run
Docker or mutate the candidate.

Two separately invoked fresh processes produce the fixed roles with distinct
internal reviewer ids. `aggregate-v2` validates the two receipt/review pairs,
reopens every common input, calls the reconstructor itself, and writes the
aggregate. `accept-v2` revalidates the same four records, independently
reconstructs the aggregate and classes, revalidates the external v3 decision,
and only then writes the final record. All outputs are exclusive,
mode 0600, file-fsynced, and parent-directory-fsynced under the ignored
artifact root. No CLI self-assigns two reviewer identities in one invocation.

## Durability And Failure Rules

Output-parent, audit-root, staging, final, publication, decision, review, and
acceptance traversal is descriptor-relative and rejects symlinks, wrong owner,
wrong mode, unexpected device changes, and nonempty pre-existing destinations.
Candidate construction fsyncs files, then directories bottom-up, then reopens
and rehashes the complete inventory before rename. Publication is exclusive.

A durable failure root and pre-create intent exist before each create. Every
failure after a stable CID routes through the exact two-plan recovery program
unless durable audit storage itself has failed, in which case no unrecorded
mutation is authorized and no completeness claim is made.
Failure-audit write failure does not authorize an unrecorded cleanup. Cleanup
failure stops the campaign and retains all safe available observations; it does
not publish a candidate or earn partial class credit.

## Corrected Keep Gates

A3L5C is kept only after two independent zero-finding documentation reviews.
A3L6 is kept only after the original gates plus focused negative tests for every
new raw field, publication cycle, exact candidate path, codesign framing,
descriptor drift, intent/recovery branch, and postpublication reviewer path.

A3L8 is kept only when both attempts finish and recovery is unnecessary,
candidate validation passes before publication, exclusive
publication succeeds, repository state is unchanged, and the protected dirty
file digest is unchanged. A3L8 emits no class decision or review.

An exact recovery cleanup is a safe rejected campaign only. It never resumes
the failed workload, publishes a candidate, closes a class, or moves a score.

A3L9 first emits the v3 decision, then accepts only two zero-finding
postpublication reviews over the same
manifest, publication, v3 decision, implementation, expected bindings, and
validator. No failure changes correspondence above 2/10.

## Claim Ceiling

Only the final A3L9 acceptance record may move local mechanical correspondence
to 10/10 and the two estimates to at most 4/10. That result remains one
synthetic, single-host, Docker Desktop Level 1 observation under explicit
signed-app, Docker-daemon, probe-code, host-driver,
native-Python-runtime/stdlib, host-system-tool, and reviewed-gate-test-code
honesty assumptions. The canonical reconstruction assumption set contains the
exact corresponding labels `signed-docker-app-honest,docker-daemon-honest,
probe-code-honest,host-driver-honest,native-python-runtime-stdlib-honest,
host-system-tool-honest,reviewed-gate-test-code-honest`; no omission is
accepted. It
is not Level2, external reproduction, benchmark evidence, semantic proof,
production readiness, SOTA, breakthrough, full security, external audit, or
accepted Evidence Ledger evidence.
