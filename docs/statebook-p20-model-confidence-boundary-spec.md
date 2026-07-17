# Statebook P20 Model Confidence Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p20-model-confidence-boundary`.

Future implementation state slice:
`statebook-p20-model-confidence`.

## Objective

Authorize hermetic P4 model/AI confidence non-bypass (P4 boundary scenario
#34 / TD-004 #18): claimed model confidence must not override a failed hard
gate or failed valuation. Instant release remains zero. No value moves.

## Authorized behavior

1. Optional `model_confidence_claimed` on requests; when any hard gate fails or
   valuation fails and confidence is claimed, reasons include
   `ModelConfidenceIgnored`.
2. Corpus updates `td004_18_model_confidence_bypass` to claim confidence while
   failing a hard gate.
3. Baseline fixtures without the field keep unchanged digests (field omitted /
   false is not encoded).

## Authorized paths

- additive edits under `crates/statebook-settlement/src/p4/`;
- additive tests under `crates/statebook-settlement/tests/`;
- updated corpus under `crates/statebook-e2e-harness/`;
- implementation notes and standard navigation mirrors.

No `statebook-sim`. No live authority. No network/credentials/process spawn.

## Frozen scenarios

1. Claimed model confidence + failing hard gate → Rejected, gate reason plus
   `ModelConfidenceIgnored`, zero instant.
2. Baseline immediate fixture unchanged when confidence is not claimed.
3. Existing corpus suites remain green.

## Nonclaims

Local hermetic model-confidence fixture regression only. Not artificial-profit
PnL (#23), concurrent finalizer races (#31), complete TD-004 satisfaction, live
authority, production readiness, SOTA, independent audit, or full security. No
value moves.
