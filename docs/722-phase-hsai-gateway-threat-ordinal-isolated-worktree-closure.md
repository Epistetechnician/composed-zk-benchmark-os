# Phase 722 HSAI Gateway Threat Ordinal Isolated Worktree Closure

## Status

Complete as a documentation-first repository-isolation correction.

State slice:
`phase-722-hsai-gateway-threat-ordinal-isolated-worktree-closure`.

Classification: `DetachedCleanExecutionWorktreeSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Correction

Phase 723 uses canonical run root `hsai-phase723-efa3782c`, canonical detached
repository root `hsai-phase723-repo-efa3782c`, and witness
`phase723ExtractedThreatOrdinalWitnesses`.

When the primary checkout contains preserved user work, Phase 723 may use one
temporary detached Git worktree created from the exact committed `HEAD`. Before
creation it must:

- record primary `HEAD` and primary porcelain status without modifying it;
- prove the canonical detached-worktree path absent; and
- prove no existing Git worktree registration uses that path.

After `git worktree add --detach`, the detached worktree becomes the sole
execution `REPO`. It must have the exact recorded commit, a clean porcelain
status, the frozen HSAI source/manifest/workspace/lock/method hashes, and the
unique `ordinal` inventory before the attempt root is created. It may not
commit, switch branches, merge, rebase, stash, or import any primary-worktree
change.

On success or failure, all attempt-owned processes must be gone before removing
the detached worktree through `git worktree remove` and verifying both its path
and registration absent. The primary user-owned modification must remain
byte-identical. The detached-worktree registration is operator metadata, not
evidence and not a clean-primary-checkout claim.

After this boundary is committed and the detached-worktree gates pass, Phase
723 may make one attempt. The direct `.olean` sequence, independent acquisition
records, exact `charon version`, fixture sequence, toolchain token, canonical
client, identity allowlist, component list, run-root order, bounded runner,
source/tool pins, cache closure, sandbox attribution, cleanup, evidence, and
claim rules remain.

Phase 722 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.
