# Phase 734 HSAI Gateway Threat Ordinal Archive Validator Status Closure

## Status

Complete as a documentation-first archive-validation correction.

State slice:
`phase-734-hsai-gateway-threat-ordinal-archive-validator-status-closure`.

Classification: `ExactArchiveRootMarkerAndStatusRulesSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Correction

Phase 735 uses canonical run root `hsai-phase735-efa3782c`, canonical detached
repository root `hsai-phase735-repo-efa3782c`, and witness
`phase735ExtractedThreatOrdinalWitnesses`.

After both Aeneas asset hashes pass, Phase 735 must produce one path inventory
and one verbose inventory per archive. The safety validator may ignore only the
exact archive root markers `.` and `./`. For every other path it must:

1. remove at most one leading `./` for comparison;
2. require a nonempty relative POSIX path;
3. reject absolute paths and every `..` component;
4. reject duplicate raw and normalized paths; and
5. reject symbolic-link and hard-link entries from the verbose inventory.

The validator must run as one bounded producer with separate stdout, stderr,
and numeric status files. Its status must be captured immediately at Python
exit and asserted zero in the next top-level command before any inventory
display, extraction, or other producer. A later command may not overwrite,
mask, reconstruct, or reinterpret that status. Assertion failure is an archive
validator failure and stops before materialization; it is not an unsafe-archive
finding unless the retained validator diagnostic identifies an unsafe entry.

After commit and detached-worktree gates, Phase 735 may make one attempt. The
Phase 732 exact fixtures and loopback controls plus every inherited identity,
independent acquisition/materialization, exact version, token, client, scanner,
component, source, cache, rfl witness, direct `.olean`, cleanup, evidence, and
claim rule remain.

Phase 734 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.
