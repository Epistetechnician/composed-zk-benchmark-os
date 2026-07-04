# Phase 430 HSAI Tiny Z3 Materialized Audit Package Artifact Boundary

State slice: `Phase 430 HSAI tiny Z3 materialized audit package artifact boundary`.

Phase 430 defines a docs-first boundary for a future local materialized
tiny-Z3 audit package artifact path after Phase 429 serialization-preview review
metadata. This boundary does not implement filesystem writes, create package
files, create archives, store raw package bytes, store raw backend output,
mutate the accepted Evidence Ledger, change accepted append policy, create
accepted formal evidence, create Level2+ evidence, populate score axes, generate
proof artifacts, generate checker transcripts, generate solver certificates,
run Lean, run SMT, run COBALT, run Rust-to-Lean extraction, submit benchmarks,
claim semantic correctness, claim production readiness, claim SOTA, claim
breakthrough status, claim full security, or grant authority to execute an
action.

## Future Artifact Purpose

A future materialized tiny-Z3 audit package may make one local Phase 429
serialization-preview review portable for human inspection. It may only
materialize declared metadata files whose contents are already represented by
the Phase 425 package, Phase 427 serialization preview, and Phase 429 review
digests.

The future artifact path must remain outside the accepted formal-evidence path.
It is a local audit convenience, not evidence acceptance, not Level2+ evidence,
not score-axis evidence, and not proof authority.

## Future Declared File Roles

A future implementation may define declared logical files under a single local
artifact namespace:

- `tiny-z3-audit-package/manifest.json`;
- `tiny-z3-audit-package/review.json`;
- `tiny-z3-audit-package/serialization-preview.json`;
- `tiny-z3-audit-package/nonclaims.json`;
- `tiny-z3-audit-package/claim-boundary.txt`;
- `tiny-z3-audit-package/digests.json`.

No undeclared file may be written or read as part of the future package. No raw
backend stdout or stderr, raw proof artifact, raw checker transcript, raw solver
certificate, secret, credential, live backend output, benchmark output, mutable
accepted-ledger state, Level2+ payload, or score-axis payload may appear in the
future package.

## Required Future Inputs

A future materialization request must bind:

- one Phase 429 serialization-preview review digest;
- one Phase 429 review input digest;
- one Phase 427 serialization-preview digest;
- one Phase 427 serialization-preview input digest;
- one Phase 425 audit package digest;
- one Phase 423 review record digest;
- one Phase 421 local reviewed metadata digest;
- one Phase 405 local Z3 output-manifest digest;
- one Phase 404 local Z3 execution digest;
- the current accepted append blocker digest;
- one package manifest digest;
- serialization profile id;
- canonical field-order digest;
- canonical JSON-shape digest;
- canonical JSON-payload digest;
- redaction-policy digest;
- logical preview path digest;
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
- generated artifacts outside the declared `tiny-z3-audit-package/` namespace.

## Required Future Validation

A future implementation must reject a materialization request if:

- any required digest is zero or missing;
- the Phase 429 review digest is drifted;
- the Phase 429 review input digest is drifted;
- the Phase 427 preview digest is drifted;
- the Phase 425 package digest is drifted;
- the Phase 423 review digest is drifted;
- the Phase 421 metadata digest is drifted;
- the Phase 405 output-manifest digest is drifted;
- the Phase 404 execution digest is drifted;
- the accepted append blocker digest is zero, missing, or drifted;
- the Phase 429 review state is promoted beyond local review metadata;
- the Phase 429 review does not preserve
  `tiny_z3_materialized_audit_package_still_blocked` as the next required
  state before materialization;
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
- the request attempts to populate score axes;
- the request attempts to generate or promote proof artifacts, checker
  transcripts, or solver certificates.

## Evidence Meaning

The future materialized package may support this claim only:

```text
HSAI can locally materialize a declared digest-bound tiny-Z3 audit package for
one Phase 429 serialization-preview review while preserving the accepted
formal-evidence blocker.
```

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
- SMT execution evidence beyond the referenced local Phase 404/405 replay
  metadata;
- COBALT execution evidence;
- Rust-to-Lean extraction evidence;
- benchmark evidence;
- semantic correctness;
- production readiness;
- SOTA;
- breakthrough status;
- full security;
- action authority.

## Phase 431 Implementation Exit Criteria

Phase 431 may implement local tiny-Z3 materialized audit package artifact
plumbing only if it:

- stays inside `crates/hsai-agent-admission/src/lib.rs`;
- adds no Cargo metadata;
- writes only declared logical files under a caller-selected output root;
- rejects repository-root output paths;
- rejects symlinks and path traversal;
- rejects undeclared files and partial bundles;
- rejects stale sidecar digests;
- stores no raw backend stdout or stderr, raw proof artifacts, raw checker
  transcripts, raw solver certificates, secrets, credentials, live backend
  outputs, benchmark outputs, Level2+ payloads, score-axis payloads, or mutable
  accepted-ledger state;
- binds one Phase 429 review digest;
- binds one Phase 427 preview digest;
- binds one Phase 425 package digest;
- binds one Phase 423 review record digest;
- binds one Phase 421 local reviewed metadata digest;
- binds Phase 404/405 local Z3 backend replay digests through the review;
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

## Phase 431 Implementation Result

Phase 431 is implemented in
`docs/431-hsai-tiny-z3-materialized-audit-package-artifact-notes.md`.

The implementation stays within the Phase 430 boundary by adding only local
digest-bound `tiny-z3-audit-package/*` artifact plumbing, declared `.sha256`
sidecars, read-back validation, nonclaim validation, and promotion rejection for
one Phase 429 serialization-preview review. It creates no accepted formal
evidence, mutates no accepted Evidence Ledger, changes no accepted append
policy, creates no Level2+ evidence, populates no score axes, and makes no
production/SOTA/security/semantic-correctness claim.
