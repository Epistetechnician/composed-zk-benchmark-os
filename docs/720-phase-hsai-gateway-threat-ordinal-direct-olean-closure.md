# Phase 720 HSAI Gateway Threat Ordinal Direct Olean Closure

## Status

Complete as a documentation-first Lean module-order correction.

State slice: `phase-720-hsai-gateway-threat-ordinal-direct-olean-closure`.

Classification: `ClientLocalDirectOleanSequenceSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Correction

Phase 721 uses canonical run root `hsai-phase721-efa3782c` and witness
`phase721ExtractedThreatOrdinalWitnesses`.

Before the ordered direct checks, create only this client-owned output
directory beneath the allowed mutable Lake build root:

```text
.lake/build/lib/lean/HsaiGatewayThreatOrdinalAeneas/Extracted
```

The three bounded sandboxed direct checks must pass explicit `-o` destinations
in dependency order:

1. `Types.lean` to `.../Extracted/Types.olean`;
2. `Funs.lean` to `.../Extracted/Funs.olean`; and
3. `Witnesses.lean` to `.../Witnesses.olean`.

Each output must be absent before its producer, become a regular file only on
zero exit, and remain below the existing 120-second and 256-KiB stream bounds.
No output may leave `$CLIENT_ROOT/.lake/build`. The final bounded sandboxed
`lake build` remains mandatory after all three direct checks.

After commit, clean-tree, and disk gates, Phase 721 may make one attempt. The
independent acquisition records, exact `charon version`, fixture sequence,
toolchain token, canonical client, identity allowlist, component list, run-root
order, bounded runner, source/tool pins, cache closure, sandbox attribution,
cleanup, evidence, and claim rules remain.

Phase 720 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.
