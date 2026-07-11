# Phase 718 HSAI Gateway Threat Ordinal Acquisition Producer Closure

## Status

Complete as a documentation-first acquisition-provenance correction.

State slice:
`phase-718-hsai-gateway-threat-ordinal-acquisition-producer-closure`.

Classification: `ExactAcquisitionProducerSequenceSpecified`.

Execution status: `NotRun`. Evidence ceiling: `Level1LocalReplayOrLower`.

## Controlling Correction

Phase 719 uses canonical run root `hsai-phase719-efa3782c` and witness
`phase719ExtractedThreatOrdinalWitnesses`.

Every network acquisition producer must execute as its own top-level shell
command. Before any dependent assertion or next producer, each command must
record:

- numeric exit status;
- stdout and stderr in separate regular files;
- both stream sizes at or below 256 KiB; and
- one exact success checkpoint label.

This applies independently to the Rust channel manifest, Rust installation,
Charon commit fetch, Aeneas main asset, Aeneas Lean-build asset, Lean archive,
Charon Cargo fetch, client Lake update, and Mathlib cache acquisition. A shared
shell block, command chain, helper function, or content-hash-only acceptance is
prohibited even when every downloaded byte matches.

After commit, clean-tree, and disk gates, Phase 719 may make one attempt. The
exact `charon version` subcommand, fixture sequence, toolchain token, canonical
client, identity allowlist, component list, run-root order, bounded runner,
source/tool pins, cache closure, sandbox attribution, cleanup, evidence, and
claim rules remain.

Phase 718 runs no tool or backend and creates no proof, accepted evidence,
Level2+, score axis, semantic correctness, production readiness, SOTA,
breakthrough, or full-security claim.
