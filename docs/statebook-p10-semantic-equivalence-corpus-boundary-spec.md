# Statebook P10 Semantic Equivalence Corpus Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p10-semantic-equivalence-corpus-boundary`.

Future implementation state slice:
`statebook-p10-semantic-equivalence-corpus`.

## Objective

Authorize a hermetic, human-reviewed labeled corpus that measures StateKey
semantic-equivalence precision, recall, and false-equivalence rate under
whitepaper §15 and PRD **TD-011** / **TD-008** (fixture-backed mapping metrics
only; no AI oracle).

P10 does not discover economic equivalence automatically, grant legal
equivalence, or move value.

## Relationship to prior phases

- P1 remains the sole terms parser, normalization, and StateKey identity
  source.
- P8/P9 remain the composing evaluation and adversarial-corpus surfaces.
- P10 consumes public P1 APIs (`parse_source_contract_v1`,
  `parse_normalization_profile_v1`, `validate_and_lower`, `derive_state_key`)
  and existing hermetic fixtures. It does not mutate P1–P9 crates' kernels or
  public APIs.
- Completing P10 does not satisfy the P7 legal/ops gate.

## Crate and ownership boundary

Future implementation may change only:

1. additive modules, fixtures, and tests under
   `crates/statebook-e2e-harness/**`;
2. root `Cargo.toml` / `Cargo.lock` only if already-allowed hermetic test
   dependencies require it;
3. new
   `docs/statebook-p10-semantic-equivalence-corpus-implementation-notes.md`;
4. `README.md`, `AGENTS.md`, `docs/12-task-list.md`,
   `docs/90-whole-codebase-validation-report.md`.

No `statebook-sim`. No new workspace crate. No P1–P9 crate mutation.

## Frozen labeled corpus

Labels are binary on StateKey identity (not validated-contract digest):

| Label | Meaning |
|-------|---------|
| `equivalent` | pair must share `StateKeyV1` |
| `distinct` | pair must not share `StateKeyV1` |

Minimum corpus contents:

1. **Equivalent lineage pairs** — baseline vs changes to venue namespace,
   source contract id, and/or source revision only;
2. **Equivalent profile-version pair** — same terms under profile version bump
   that must not change StateKey;
3. **Distinct material pairs** — every declared material mutation from the
   frozen P1 `terminal_contract_cases_v1.json` fixture versus baseline.

## Metrics (structured receipt only)

The harness must compute and record:

- true/false positives and negatives for the `equivalent` class;
- precision = TP / (TP + FP);
- recall = TP / (TP + FN);
- false-equivalence rate = FP / |distinct labels|;

Hard acceptance for this hermetic corpus:

- false-equivalence rate must be exactly `0`;
- precision and recall for `equivalent` must be exactly `1`
  (denominator-safe: corpus must include ≥1 equivalent and ≥1 distinct label).

No production threshold calibration beyond this fixture-local acceptance.

## Acceptance gates

- labeled corpus replays with exact metric acceptance above;
- focused format/test/Clippy pass for `statebook-e2e-harness`;
- unchanged P1–P9 tests pass;
- claim-boundary scan continues to forbid network/process/live-authority
  surfaces and AI-as-oracle claims.

## Nonclaims

P10 creates no automatic discovery of true economic equivalence, legal
fungibility, live venue authority, AI oracle, production metric thresholds,
SOTA, independent audit, or full-security claim. Local hermetic labeled-fixture
regression only. No value moves.
