# Phase 352 HSAI Materialized Audit Package Artifact Boundary

State slice: `Phase 352 HSAI materialized audit package artifact boundary`.

Phase 352 defines a docs-first boundary for a future local materialized audit
package artifact path after Phase 351 serialization-preview review metadata.
This boundary does not implement filesystem writes, create package files, store
raw proof artifacts, mutate the accepted Evidence Ledger, change accepted append
policy, create accepted formal evidence, create Level2+ evidence, populate score
axes, generate proof artifacts, generate checker transcripts, generate solver
certificates, run Lean, run SMT, run COBALT, run Rust-to-Lean extraction, submit
benchmarks, claim semantic correctness, claim production readiness, claim SOTA,
claim breakthrough status, claim full security, or grant authority to execute an
action.

## Future Artifact Purpose

A future materialized audit package may make one local Phase 351
serialization-preview review portable for human inspection. It may only
materialize declared metadata files whose contents are already represented by
the Phase 347 package, Phase 349 serialization preview, and Phase 351 review
digests.

The future artifact path must remain outside the accepted formal-evidence path.
It is a local audit convenience, not evidence acceptance.

## Future Declared File Roles

A future implementation may define declared logical files under a single local
artifact namespace:

- `audit-package/manifest.json`;
- `audit-package/review.json`;
- `audit-package/serialization-preview.json`;
- `audit-package/nonclaims.json`;
- `audit-package/claim-boundary.txt`;
- `audit-package/digests.json`.

No undeclared file may be written or read as part of the future package. No raw
proof artifact, raw checker transcript, raw solver certificate, secret,
credential, live backend output, benchmark output, or mutable accepted-ledger
state may appear in the future package.

## Required Future Inputs

A future materialization request must bind:

- one Phase 351 serialization-preview review digest;
- one Phase 351 review input digest;
- one Phase 349 serialization-preview digest;
- one Phase 349 serialization-preview input digest;
- one Phase 347 audit package digest;
- one Phase 345 review record digest;
- one Phase 343 local reviewed metadata digest;
- the current accepted append blocker digest;
- serialization profile id;
- canonical field-order digest;
- canonical JSON shape digest;
- expected package bytes digest;
- artifact profile id;
- declared logical file list digest;
- expected materialized manifest digest;
- explicit nonclaim digest.

## Required Future Path Policy

A future implementation must reject:

- missing caller-selected output root;
- repository-root output paths;
- current-working-directory output paths;
- absolute paths inside declared logical artifact names;
- path traversal;
- symlinks;
- undeclared files;
- partial bundles;
- stale sidecar digests;
- overwrite attempts unless an explicit overwrite mode is set;
- raw response-body retention;
- generated artifacts outside the declared artifact namespace.

## Required Future Validation

A future implementation must reject a materialization request if:

- any required digest is zero or missing;
- the Phase 351 review digest is drifted;
- the Phase 351 review input digest is drifted;
- the Phase 349 preview digest is drifted;
- the Phase 347 package digest is drifted;
- the accepted append blocker digest is zero, missing, or drifted;
- the Phase 351 review state is promoted beyond local review metadata;
- the Phase 351 review does not preserve `materialized_audit_package_still_blocked`
  as the next required state before materialization;
- explicit nonclaims are missing or drifted;
- the artifact profile id is missing or not a single-segment id;
- the declared logical file list digest is missing or drifted;
- the expected materialized manifest digest is missing or drifted;
- any package text claims accepted evidence, Level2+ evidence, score-axis
  evidence, proof authority, checker authority, solver-certificate authority,
  benchmark evidence, semantic correctness, production readiness, SOTA,
  breakthrough status, full security, or action authority;
- the request attempts to mutate the accepted Evidence Ledger;
- the request attempts to change accepted append policy;
- the request attempts to create accepted formal evidence;
- the request attempts to create Level2+ evidence;
- the request attempts to populate score axes.

## Meaning Limit

The future materialized package may support this claim only:

HSAI can locally materialize a declared digest-bound audit package for one Phase
351 serialization-preview review while preserving the accepted formal-evidence
blocker.

It cannot support:

- accepted formal evidence;
- accepted Evidence Ledger mutation;
- accepted append policy change;
- Level2+ evidence;
- score-axis evidence;
- proof authority;
- checker transcript authority;
- solver certificate authority;
- Lean execution evidence;
- SMT execution evidence;
- COBALT execution evidence;
- Rust-to-Lean extraction evidence;
- benchmark evidence;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- action authority.

## Phase 353 Implementation Exit Criteria

Phase 353 may implement local materialized audit package artifact plumbing only
if it:

- remains additive and local;
- writes only declared logical files under a caller-selected output root;
- rejects repository-root output paths;
- rejects symlinks and path traversal;
- rejects undeclared files and partial bundles;
- stores no raw proof artifacts, raw checker transcripts, raw solver
  certificates, secrets, credentials, live backend outputs, benchmark outputs,
  or mutable accepted-ledger state;
- binds one Phase 351 review digest;
- binds one Phase 349 preview digest;
- binds one Phase 347 package digest;
- binds one Phase 345 review record digest;
- binds one Phase 343 local reviewed metadata digest;
- binds the current accepted append blocker digest;
- validates all nonclaims;
- rejects all promotion attempts listed in this boundary;
- does not mutate the accepted Evidence Ledger;
- does not change accepted append policy;
- does not create accepted formal evidence;
- does not create Level2+ evidence;
- does not populate score axes;
- does not generate or promote proof artifacts, checker transcripts, or solver
  certificates;
- does not run Lean, SMT, COBALT, or Rust-to-Lean extraction;
- does not submit benchmarks;
- does not claim semantic correctness, production readiness, SOTA, breakthrough
  status, full security, or action authority.
