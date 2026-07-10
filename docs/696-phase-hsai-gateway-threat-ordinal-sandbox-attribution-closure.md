# Phase 696 HSAI Gateway Threat Ordinal Sandbox Attribution Closure

## Status

Complete as a documentation-first network-control correction.

State slice: `phase-696-hsai-gateway-threat-ordinal-sandbox-attribution-closure`.

Classification: `SandboxAttributionProtocolSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Correction

Phase 697 uses canonical run root `hsai-phase697-efa3782c` and witness
`phase697ExtractedThreatOrdinalWitnesses`.

During the final network-enabled acquisition stage, resolve `example.com` once
outside the sandbox and record at least one address. After permanent network
closure, require the same hostname lookup to fail inside the deny-network
sandbox. Attribution is the paired pre-closure success and post-closure
failure; generic `getaddrinfo` text alone is insufficient.

The direct-IP control must run `/usr/bin/nc -v -G 2 -z 1.1.1.1 443` inside the
sandbox, return nonzero, and emit `Operation not permitted` in a bounded
captured stream. The `/usr/bin/true` positive control remains mandatory. No
fallback network probe, relaxed profile, or network-enabled build is allowed.

After commit, clean-tree, and disk gates, Phase 697 may make one attempt. All
pins, cache closure, checkpoints, sandboxing, cleanup, evidence, and claim
rules remain.

Phase 696 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.

