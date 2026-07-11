# Phase 712 HSAI Gateway Threat Ordinal Charon Toolchain Token Closure

## Status

Complete as a documentation-first Charon environment correction.

State slice:
`phase-712-hsai-gateway-threat-ordinal-charon-toolchain-token-closure`.

Classification: `ExactCharonToolchainTokenSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Correction

Phase 713 uses canonical run root `hsai-phase713-efa3782c` and witness
`phase713ExtractedThreatOrdinalWitnesses`.

Every Charon dependency-fetch, source-build, driver-load, and extraction
environment must set this exact assignment:

```text
RUSTUP_TOOLCHAIN=nightly-2026-06-01
```

No shortened date, alternate nightly, implicit directory override, or
semantically unused wrong token is allowed. The command record must capture the
exact token before launch and compare it byte-for-byte. A mismatch stops before
the producer starts as `UnexpectedCommand`.

After commit, clean-tree, and disk gates, Phase 713 may make one attempt. The
canonical UTF-8 client, identity-log allowlist, exact component list, run-root
order, bounded runner, source/tool pins, cache closure, sandbox attribution,
cleanup, evidence, and claim rules remain.

Phase 712 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.
