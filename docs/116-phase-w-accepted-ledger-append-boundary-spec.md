# Phase W Accepted Ledger Append Boundary Spec

## Status

Docs-first boundary. This phase defines the next possible accepted Evidence
Ledger append transaction surface after Phase W preflight, but it does not
authorize implementation code or any accepted ledger mutation.

## State Slice

This slice is limited to Markdown boundary updates under `docs/`, `README.md`,
`docs/12-task-list.md`, `docs/90-whole-codebase-validation-report.md`, and
`AGENTS.md`.

It exists because Phase 115 can validate reviewed promotion preflight metadata
and official-submission package metadata, but the repository still has no
accepted Evidence Ledger entry, no official benchmark submission, no external
replay evidence, no Level2+ evidence, and no score-axis population.

## Future Transaction Contract

A future implementation may define a local accepted-ledger append transaction
object only if it keeps the append operation explicit and fail-closed. The
future transaction must require all of the following inputs:

- A valid Phase W reviewed promotion preflight report.
- A valid evidence-record candidate.
- A valid append preview whose `expected_previous_tip` matches the current
  accepted ledger tip.
- A human review decision that approves the exact candidate being appended.
- Artifact digest bindings for every source artifact used by the accepted
  claim.
- External replay provenance for any Level2+ promotion attempt.
- Explicit absence of unresolved quarantine markers and blocking review
  markers.
- Required non-claim labels preserving the distinction between candidates,
  append previews, preflight reports, local campaign artifacts, official
  submission metadata, and accepted evidence.

The future transaction must produce deterministic metadata before any append is
attempted. The deterministic metadata must be enough to audit what would be
appended, why the append was permitted, and which accepted ledger tip was
expected.

## Future Append Rules

A future implementation may append only to a caller-selected local accepted
Evidence Ledger path. It must not infer the ledger path from the repository,
environment, or artifact inputs.

The future append must reject:

- Stale ledger tips.
- Missing or mismatched candidate ids.
- Missing approval for the exact candidate id.
- Missing artifact digests.
- Missing external replay provenance for Level2+ claims.
- Local-only Level2+ promotion.
- Score-axis population from local-only evidence.
- Unresolved quarantine markers.
- Blocking review markers.
- Any official benchmark submission attempt.
- Any forbidden claim text that implies official, accepted, proven, formal,
  leaderboard, soundness, or performance status beyond the reviewed claim.

The future append must be append-only. It must not rewrite, repair, compact, or
delete existing ledger entries.

## Required Future Tests

Any future implementation must include hermetic tests for:

- Valid transaction metadata without appending.
- Append rejection on stale ledger tip.
- Append rejection on candidate or review mismatch.
- Append rejection when external replay provenance is missing for Level2+.
- Append rejection for local-only Level2+ promotion.
- Append rejection for unresolved quarantine or blocking review markers.
- Append rejection for official-submission attempts.
- Append-only behavior over an explicit temp ledger path.
- Source-scan boundaries proving the implementation does not call network,
  credential, backend, official submission, or benchmark-output paths.

Normal test gates must not require network access, credentials, live backend
execution, operator artifacts, Phala calls, DCAP/PCCS/JWKS/TLS paths, official
benchmark endpoints, or external replay infrastructure.

## Explicit Non-Goals

This docs-first slice does not permit:

- Rust source or test changes.
- Cargo metadata changes.
- `Cargo.lock` changes.
- Accepted Evidence Ledger mutation.
- Official benchmark submission.
- External replay execution.
- Live backend execution.
- Network access.
- Credentials or secrets.
- Generated benchmark artifacts.
- Durable campaign output generation.
- Command-line tools.
- UI dashboards.
- JavaScript, TypeScript, or package runtime additions.
- Score-axis population.
- ZK backend performance claims.
- Level2+ evidence creation.
- Formal evidence creation.
- Broad leaderboard claims.

## Claim Boundary

This boundary is not accepted evidence. It is not official benchmark evidence.
It is not external replay evidence. It is not Level2+ evidence. It is not ZK
backend performance evidence. It is not semantic correctness evidence.

The next code phase, if separately authorized, must implement only local
transaction validation and append mechanics over explicit local inputs. It
still must not create an accepted Evidence Ledger entry unless the caller
supplies all qualifying evidence and the implementation validates every
precondition above.
