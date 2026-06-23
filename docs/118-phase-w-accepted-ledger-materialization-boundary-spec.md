# Phase W Accepted Ledger Materialization Boundary Spec

## Status

Docs-first boundary for materializing a guarded local accepted-ledger append to
an explicit caller-selected JSON ledger path.

## State Slice

This slice is limited to Markdown boundary updates plus a future local
filesystem implementation under `crates/zkbench-core/src/evidence/`.

## Future Contract

A future implementation may load or create one caller-selected local
`EvidenceLedger` JSON file, apply a valid Phase W accepted-ledger append
transaction, and atomically replace that JSON file with the appended ledger.

The implementation must require:

- An explicit non-empty ledger path.
- An existing parent directory.
- No parent-directory path components.
- No symlink ledger path or symlink parent.
- A valid existing ledger if the file already exists.
- Explicit creation permission if the file does not exist.
- The same Phase W preflight, candidate, review, append-preview, digest, and
  ledger-tip checks required by `docs/117-phase-w-accepted-ledger-append-implementation-notes.md`.

## Required Rejections

The materialized append path must reject:

- Missing ledger file unless creation is explicitly enabled.
- Directory targets.
- Symlink targets or symlink parents.
- Stale ledger tips.
- Invalid existing ledgers.
- Official-submission attempts.
- Score-axis population.
- Level2+ or formal evidence claims.
- Network, backend, credential, or official benchmark submission surfaces.

## Non-Goals

This boundary does not authorize official benchmark submission, external replay,
live backend execution, network access, credentials or secrets, generated
benchmark artifacts, durable campaign outputs, command-line tools, UI
dashboards, package runtime additions, score-axis population, ZK backend
performance claims, Level2+ evidence creation, formal evidence creation, broad
leaderboard claims, or treating local ledger JSON as official benchmark
evidence.

## Claim Boundary

Materialized accepted-ledger JSON is local accepted evidence only for the
reviewed Level1-or-below claim represented by the transaction inputs. It is not
official benchmark evidence, not external replay evidence, not Level2+ evidence,
not ZK backend performance evidence, and not semantic correctness evidence.
