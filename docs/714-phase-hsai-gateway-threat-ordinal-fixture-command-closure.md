# Phase 714 HSAI Gateway Threat Ordinal Fixture Command Closure

## Status

Complete as a documentation-first fixture-sequence correction.

State slice: `phase-714-hsai-gateway-threat-ordinal-fixture-command-closure`.

Classification: `ExactBoundedRunnerFixtureSequenceSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Correction

Phase 715 uses canonical run root `hsai-phase715-efa3782c` and witness
`phase715ExtractedThreatOrdinalWitnesses`.

After the immediate canonical client hash checks, the fixture sequence may
contain only these four bounded-runner producers in order:

1. normal `/bin/echo ok`;
2. child-plus-grandchild timeout;
3. `/usr/bin/yes x` stdout flood; and
4. stderr flood through `/bin/sh`.

One validator may then read their captured outputs and statuses, verify the
grandchild is dead, and require exact byte caps. No fixture-description loop,
argument parser, dry-run, alternate command, or unused no-op is allowed.

After commit, clean-tree, and disk gates, Phase 715 may make one attempt. The
exact Charon toolchain token, canonical UTF-8 client, identity-log allowlist,
component list, run-root order, bounded runner, source/tool pins, cache closure,
sandbox attribution, cleanup, evidence, and claim rules remain.

Phase 714 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.
