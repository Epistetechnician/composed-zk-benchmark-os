# Phase 299 HSAI Gateway Formal Backend Quarantine Validation-Summary Boundary

State slice: `Phase 299 HSAI gateway formal backend quarantine validation-summary boundary`.

## Status

Complete for the docs-first validation-summary boundary.

## Purpose

Phase 298 hardened the local quarantine output-bundle readback path with
focused drift tests. Phase 299 defines the next artifact boundary: a local
validation summary that records which quarantine output-bundle checks were run
and what they mean.

This phase does not add Rust code. It defines the future implementation
contract.

## Future Artifact

A future implementation may add a local validation-summary artifact for
`gateway-formal-backend-quarantine/*`.

The future summary should be a deterministic pure-data record with:

- `schema_version`;
- `state_slice`;
- `summary_id`;
- quarantine output manifest digest;
- quarantine artifact digest;
- declared files checked;
- sidecars checked;
- readback validation result;
- drift coverage labels;
- undeclared-file coverage labels;
- symlink coverage labels;
- nonpromotion coverage labels;
- claim-boundary coverage labels;
- validation command labels;
- created-at timestamp supplied by the caller;
- local-regression-only flag;
- no backend-executed flag;
- no proof-artifact-promoted flag;
- no checker-transcript-promoted flag;
- no accepted-evidence-mutation flag;
- no Level2+ evidence flag;
- no score-axis population flag;
- no semantic-correctness claim flag;
- no production-readiness claim flag;
- no SOTA claim flag;
- no breakthrough claim flag;
- no full-security claim flag;
- no action-authority flag;
- required nonclaim labels;
- deterministic digest helper.

## Required Coverage Labels

The future summary must be able to name, at minimum, these covered local checks:

- protected output-root rejection;
- overwrite rejection;
- missing sidecar rejection;
- stale sidecar rejection;
- malformed declared JSON rejection;
- authorization binding drift rejection;
- process-status drift rejection;
- stdout summary drift rejection;
- stderr summary drift rejection;
- redaction report drift rejection;
- output inventory drift rejection;
- proof/checker nonpromotion drift rejection;
- nonclaim Markdown drift rejection;
- manifest claim-boundary drift rejection;
- manifest accepted-evidence drift rejection;
- manifest Level2+ drift rejection;
- manifest score-axis drift rejection;
- manifest authority drift rejection;
- undeclared raw stdout rejection;
- undeclared raw stderr rejection;
- undeclared raw prover log rejection;
- undeclared raw checker log rejection;
- undeclared raw solver trace rejection;
- undeclared proof artifact rejection;
- undeclared checker transcript rejection;
- undeclared accepted Evidence Ledger path rejection;
- undeclared benchmark output rejection;
- undeclared source-correspondence bundle path rejection;
- undeclared backend-run bundle path rejection;
- undeclared preflight bundle path rejection;
- undeclared transcript bundle path rejection;
- undeclared authorization bundle path rejection;
- output-root symlink rejection;
- bundle-directory symlink rejection;
- declared file symlink rejection;
- declared sidecar symlink rejection.

## Required Future Validation

The future implementation must reject a validation summary when:

- the summary id is empty or unsafe;
- the schema version is wrong;
- the state slice is wrong;
- a required coverage label is missing;
- an unknown coverage label appears;
- a digest is zeroed;
- the referenced manifest digest is zeroed;
- the referenced quarantine artifact digest is zeroed;
- local-regression-only is false;
- no-backend-executed is false;
- proof artifact promotion is claimed;
- checker transcript promotion is claimed;
- accepted Evidence Ledger mutation is claimed;
- Level2+ evidence is claimed;
- score-axis population is claimed;
- semantic correctness is claimed;
- production readiness is claimed;
- SOTA status is claimed;
- breakthrough status is claimed;
- full security is claimed;
- action authority is claimed;
- required nonclaim labels are missing;
- the deterministic digest changes for the same summary content.

## Evidence Meaning

The validation summary would mean only this:

`The local quarantine output-bundle reader has regression coverage for selected
drift, undeclared-file, symlink, nonpromotion, and claim-boundary rejection
paths.`

It would not mean:

- a formal backend executed;
- Lean executed;
- SMT or Z3 executed;
- COBALT executed;
- Aeneas, Hax, or rust-lean executed;
- a proof artifact is valid;
- a checker transcript is valid;
- a solver certificate is valid;
- a proof corresponds to HSAI source;
- accepted Evidence Ledger state changed;
- Level2+ evidence exists;
- score axes are populated;
- benchmark evidence exists;
- HSAI is semantically correct;
- HSAI is production ready;
- HSAI is SOTA;
- HSAI is a breakthrough;
- HSAI is fully secure;
- the gateway has authority to execute an action.

## Anti-Goals

This phase does not permit:

- Rust implementation changes;
- Cargo metadata changes;
- package runtime files;
- new bundle materialization behavior;
- command execution;
- process spawning;
- backend runner implementation;
- proof assistant setup files;
- external repo clones;
- vendored source;
- Lean, Coq, TLA+, SMT, Z3, CBMC, model-checker, Aeneas, Hax, rust-lean, or
  COBALT execution;
- generated proof artifact promotion;
- generated checker transcript promotion;
- raw prover log retention;
- raw checker log retention;
- raw solver trace retention;
- accepted Evidence Ledger mutation;
- Level2+ evidence;
- score-axis population;
- benchmark evidence;
- official benchmark submission;
- live provider calls;
- credential handling;
- semantic-correctness claims;
- production-readiness claims;
- SOTA claims;
- breakthrough claims;
- full-security claims;
- global software-agent uniqueness claims;
- authority to execute an action.

## Next Slice

Phase 300 implements the local validation-summary data type, digest helper,
validation function, and focused tests under
`crates/hsai-agent-admission/src/lib.rs`. The next responsible slice is a
docs-first boundary for materializing that summary into a local declared-file
output bundle. It should not execute a command, spawn a process, read real
proof artifacts, promote checker transcripts, mutate accepted evidence, create
Level2+ evidence, populate score axes, or change public claims.
