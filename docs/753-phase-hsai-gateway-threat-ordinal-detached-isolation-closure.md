# Phase 753 HSAI Gateway Threat Ordinal Detached Isolation Closure

## Status

Complete as a documentation-first repository-isolation correction.

State slice:
`phase-753-hsai-gateway-threat-ordinal-detached-isolation-closure`.

Classification: `DirtyPrimaryDetachedExecutionSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

Phase 754 uses run root `hsai-phase754-efa3782c`, detached repository root
`hsai-phase754-repo-efa3782c`, and witness
`phase754ExtractedThreatOrdinalWitnesses`.

This phase supersedes only Phase 744's clean-primary requirement. When unrelated
primary work is present, Phase 754 must:

1. record committed primary `HEAD`, porcelain-v1 status bytes, and SHA-256 for
   every present modified or untracked regular file without staging it;
2. prove both canonical Phase 754 paths absent and unregistered;
3. create one detached worktree from the exact committed `HEAD`;
4. require the detached worktree to be clean and to match every frozen source,
   helper, manifest, lockfile, and method hash before creating the run root;
5. use only the detached worktree as execution `REPO`;
6. never stage, stash, commit, reset, clean, switch, or write the primary
   checkout during the attempt; and
7. after removing and deregistering the detached worktree, require the primary
   `HEAD`, status bytes, file set, and per-file SHA-256 values to match the
   pre-attempt record exactly.

The primary dirty state is operator-owned concurrent work, not evidence and not
an input to the formal attempt. Phase 722's detached-worktree constraints and
every Phase 749-751 helper, token, acquisition, archive, sandbox, extraction,
witness, cleanup, evidence, and claim rule remain.

After this boundary is committed, the canonical roots remain absent, the
detached baseline and helper hashes pass, and at least 20 GiB is free, Phase 754
may make one attempt. The first failed gate stops without same-phase repair.

Phase 753 runs no tool, network, backend, or kernel command and creates no proof,
accepted evidence, Level2+, score axis, semantic correctness, production
readiness, SOTA, breakthrough, full-security claim, external audit, or action
authority.
