# Phase 762 HSAI Gateway Threat Ordinal Rustup Inventory Stop

## Status

Complete as one cleaned pre-Charon identity stop.

State slice: `phase-762-hsai-gateway-threat-ordinal-rustup-inventory-stop`.

Classification: `RustupInstalledFilterSemanticDrift`.

Diagnostic: `Rustup129EmitsFullInventoryWithInstalledMarkers`.

Execution status: `Succeeded` through isolation, frozen identities, helper
hashes, 30 helper tests, bounded 31-case parser self-test, canonical client
metadata, four exact process fixtures, pinned Rust manifest and installation,
and six bounded identity producers; `Failed` at component-output acceptance;
and `NotRun` for Charon, Aeneas, Lean, Cargo fetch/build, Lake, sandbox
controls, backend extraction, generated source, or kernel checking. Evidence
ceiling: `Level1LocalReplayOrLower`.

## First Failure

Rustup `1.29.0 (28d1352db 2026-03-05)` returned a byte-identical 5,313-byte
full component inventory for all three `component list --installed` producers.
Exactly seven lines ended in ` (installed)`, and those seven names matched the
required component set. The inherited assertion instead required stdout to
contain only seven bare names, so it failed before Charon acquisition.

The surrounding diagnostic shell also lacked immediate failure propagation;
a later negative scan and print could mask the Python assertion status. The
Python assertion remains the authoritative first failure. No same-phase repair
or replay occurred.

## Cleanup And Claims

The isolated Rustup root, run root, and detached worktree were removed. All
other owned persistent roots remained absent. The primary checkout exactly
matched its pre-attempt preservation record, which was then removed.

Phase 762 creates local preflight and tool-identity evidence only. It creates
no Charon result, archive result, backend result, generated source, kernel
result, proof, accepted evidence, Level2+, score axis, semantic correctness,
production readiness, SOTA, breakthrough, full-security claim, external audit,
or action authority.
