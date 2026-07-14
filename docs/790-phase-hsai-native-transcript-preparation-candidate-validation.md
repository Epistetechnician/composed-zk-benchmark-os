# Phase 790 HSAI Native Transcript Preparation Candidate Validation

## Status

Implemented as a pure-data validator; stopped before `P01B` materialization.

State slice: `phase-790-hsai-native-transcript-preparation-candidate`.

Classification: `CandidateValidatorImplementedMaterializationStopped`.

Execution status: `LocalValidationOnly`. Evidence ceiling:
`Level1LocalReplayOrLower`.

## Verdict

Phase 790 does not satisfy the Phase 789 `P01B` materialization gate. It adds a
closed Rust schema and pure-data validator for a future preparation candidate,
then stops because the required external authority and materialized inputs do
not exist.

The implementation cannot inspect a host, read an environment variable, open
a file, create either root, acquire an archive, run a command, authenticate a
reviewer, accept materialization, or authorize capture. `capture_authorized`
is not an input field. Every validation result sets both
`materialization_accepted` and `capture_authorized` to `false`; a clean result
means only `candidate_eligible_for_external_review=true`.

No Phase 780 lane closes. Resolved lanes remain `L01-L04,L09`; open lanes
remain `L05-L08,L10-L11`. Historical Phase 779 JSONL remains unchanged with
1,469 blockers, 102 blocked rows, and no source-ledger digest.

## Implemented Surface

The standalone `hsai-native-transcript-preparation` crate validates declared
candidate data for:

- the Phase 778 operation-order digest and Phase 787 registry digest;
- separate fixed preparation and capture roots, with capture-root absence;
- exactly eight host roles: `CURL_EXE`, `GIT_EXE`, `TAR_EXE`, `RUSTUP_EXE`,
  `SANDBOX_EXEC_EXE`, `CODESIGN_EXE`, `SPCTL_EXE`, and `OTOOL_EXE`;
- fixed paths for the six Phase 787 fixed-path roles and external absolute
  paths for `GIT_EXE` and `RUSTUP_EXE`;
- sorted nonempty owner and SHA-256 allowlists;
- exactly one declared executable fact per host role, bound to the reviewed
  machine-policy digest and exact platform tuple;
- bounded symlink-hop declarations, stable pre/post metadata, regular
  executable mode, owner admission, digest admission, and allowed roots;
- exactly two accepted owned-tool receipts for `RUSTC_EXE` and `CARGO_EXE`;
- the Phase 788 Aeneas archive URL, length, and SHA-256;
- exactly six target receipts with the four fixed packaged digests;
- exact Charon commit, ordinal 073, `arm64`, ad-hoc signature, absent Team ID,
  and stable-source declarations for both built targets;
- the byte-exact Phase 776 sandbox profile and its recomputed digest;
- distinct policy producer, policy reviewer, capture operator, fixture
  reviewer, and grammar reviewer roles where the closed schema requires
  separation; and
- strict unknown-field rejection and domain-separated deterministic candidate
  and machine-policy digests.

These checks validate correspondence among caller-supplied declarations. They
do not establish that any declaration is true.

## Collector Safety Stop

An initial host collector design was rejected before commit. Resolving a path
with pathname metadata calls and applying `O_NOFOLLOW` only to the terminal
open does not prevent an ancestor directory from being replaced between
checks. That design could produce a race-vulnerable identity statement.

A future collector must use descriptor-relative component traversal from an
accepted root, no-follow opens for every path component, directory and terminal
descriptor identity checks, bounded symlink handling, stable pre/post metadata,
and adversarial replacement tests. The pure-data validator deliberately has no
filesystem API while that contract is absent.

## Why Materialization Stopped

The repository still does not contain or authenticate:

1. an accepted machine-policy instance for all eight host roles;
2. safe, descriptor-derived identity observations for those roles;
3. accepted owned-tool receipts for the future preparation attempt;
4. the exact Aeneas archive or its four admitted packaged target bytes;
5. an accepted ordinal-073 build receipt and its two retained targets;
6. named external principals and authenticated review decisions; or
7. an accepted preparation handoff digest.

Unit-test objects are synthetic declarations. They are regression fixtures,
not machine observations, target receipts, reviewer approvals, or evidence.

## Validation

The focused gate is:

```text
cargo test -p hsai-native-transcript-preparation
```

Eight integration tests cover a complete synthetic declaration, pending review
and principal collision, missing wrapper observation, packaged digest drift,
built-target ordinal/source drift, capture-root and claim drift, deterministic
serialization/digests, unknown-field rejection, and non-normalized or
non-regular executable declarations.

## Corrected Forward Schedule

This schedule supersedes the Phase 789 schedule from Phase 790 onward without
rewriting the historical decision:

```text
790 pure-data preparation-candidate validator; P01B stopped
791 descriptor-relative executable-fact collector boundary
792 conditional safe collector implementation and adversarial tests
793 operator preparation-driver and source-receipt boundary
794 conditional hermetic driver implementation and fixture tests
795 conditional P01B machine-policy, identity, and six-target materialization
796 conditional P02 identity-bound native transcript corpus capture
797 L05 native transcript grammars, typed outputs, acceptance IDs, fixtures
798 L06 Charon driver preflight argv contract
799 L07 archive inventory contracts
800 L08 mutable output inventory contracts
801 L10 canonical JSONL serialization profile and conformance vectors
802 L11 row expansion tranche 001-038
803 L11 row expansion tranche 039-064
804 L11 row expansion tranche 065-102
805 independent whole-ledger audit and conditional digest publication
806 earliest possible plan-v2 boundary, only after Phase 805 success
```

Phases 791-794 are not authorization to use network access, run a native audit,
or materialize real inputs. Each requires its own explicit state slice. Phase
795 remains conditional on external policy and reviewer authority.

## Claim Boundary

Phase 790 is a local pure-data validation surface. It is not safe host fact
collection, an authenticated policy, a machine observation, artifact
acquisition, target materialization, a build receipt, a reviewer approval,
handoff acceptance, native transcript capture, a fixture corpus, a grammar, an
acceptance operation, plan v2, executor binding, backend execution, generated
Lean, an SMT or COBALT run, a proof artifact, checker transcript, accepted
evidence, Level2+, a score axis, semantic correctness, production readiness,
SOTA, breakthrough, full security, external audit, or action authority.

## Phase 791 Forward Result

Phase 791 completed the descriptor-relative collector boundary without adding
or running collector code. Phase 792 is the only conditional implementation
route and must satisfy
`docs/791-phase-hsai-native-transcript-descriptor-relative-collector-boundary.md`.
