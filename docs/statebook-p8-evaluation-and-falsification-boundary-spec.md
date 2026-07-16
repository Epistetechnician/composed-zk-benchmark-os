# Statebook P8 Evaluation And Falsification Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p8-evaluation-and-falsification-boundary`.

Future implementation state slice:
`statebook-p8-evaluation-and-falsification`.

## Objective

Authorize a hermetic composing evaluation harness that exercises the public
P1–P7 surfaces end to end under whitepaper §15 and PRD **TD-011**.

P8 proves digest binding, deterministic replay, readback integrity, and
claim-boundary compliance across composed library APIs. It records structured
pass/fail and digest evidence only.

P8 does not calibrate production thresholds, grant live authority, or move
value.

## Relationship to prior phases

- P1–P7 remain the sole identity sources for terms, residuals, completeness,
  settlement decisions, audit bundles, captured import, and synthetic authority
  statements.
- P8 consumes public APIs as a library composer. It does not reimplement
  parsers, kernels, adapters, or digests.
- P8 may embed or relative-include existing hermetic fixtures from P1–P7 test
  trees. It must not mutate those crates.
- Completing P8 does not satisfy the P7 legal/ops gate for live authority
  products.

## Crate and ownership boundary

Future implementation may add at most one new workspace crate:

1. `crates/statebook-e2e-harness` — hermetic golden-path composition,
   falsification checks, structured evaluation receipts, and claim-boundary
   scans.

No `statebook-sim`. No second new crate. No generic evaluation-adapter trait.

Ownership rules:

- `statebook-core`, `statebook-settlement`, `statebook-report`,
  `statebook-source`, and `statebook-authority` public APIs, digests, fixtures,
  kernels, bundles, and import/attach behavior remain unchanged.
- Path dependencies on those five crates are required.
- Network clients, credentials, process spawn, HSAI admission mutation, and
  Evidence Ledger append are forbidden.
- Filesystem writes are permitted only inside bounded temporary roots for P5
  materialize/readback tests.

## Frozen golden path

The future implementation must compose one hermetic golden path:

1. P6 `import_captured_terms_v1` for `synthetic-clearing-terms-v1`;
2. P1 `parse_source_contract_v1` → `validate_and_lower` → `derive_state_key`
   on the imported terms bytes with the frozen normalization profile;
3. P2 `analyze_terminal_residual_v1` over a finite declared state domain;
4. P3 `compose_completeness_reports_v1` using the semantic and payoff reports
   from steps 2–3 plus the frozen completeness fixture;
5. P4 `parse_settlement_scenario_v1` + `decide_and_transition` for the frozen
   immediate scenario;
6. P5 `handoff_decision_record_v1` with `grants_authority=false`, then
   `materialize_audit_bundle_v1` + `readback_validate_audit_bundle_v1` under a
   temporary root;
7. P7 `attach_authority_statement_v1` with
   `subject_terms_digest = validated_contract_digest` and
   `economic_residual_digest = payoff.domain_digest`, then
   `evaluate_attached_statement_v1`.

Every successful golden-path receipt must record the bound digests and
outcomes without introducing an aggregate trust score.

## Frozen falsification surfaces

Minimum falsifiers:

1. P4 hard-gate failure yields `Rejected` (or non-immediate) with zero instant
   release;
2. P5 readback after tamper rejects;
3. P7 `grants_execution_authority=true` rejects;
4. harness binding check rejects attaching a P7 statement whose
   `subject_terms_digest` does not equal the golden-path
   `validated_contract_digest`.

## Structured evaluation receipt

The harness may emit a serialize-only evaluation receipt binding:

- schema / profile ids;
- P1 state key and validated-contract digest;
- P2 domain digest and payoff status;
- P3 capital overlay/status summary where available;
- P4 decision outcome and record digest;
- P5 manifest / readback digests;
- P6 import receipt digest;
- P7 attach receipt digest and capital overlay status;
- permanent nonclaims including no live authority and no value movement.

JSON or Serde hashes remain forbidden for identity. New digest families, if
any, must be domain-separated TLV SHA-256 with an independent encoder.

## Closed inputs

Allowed:

- existing hermetic P1–P7 fixtures via relative include or copied fixtures;
- temporary filesystem roots for P5 readback;
- public P1–P7 library APIs.

Forbidden:

- live execution, custody, signing, pause, transfer, withdrawal, bridge, or
  settlement commands;
- live network clients or credentials;
- mutation of P1–P7 crates;
- production threshold selection or empirical calibration claims;
- `grants_authority=true` / `grants_execution_authority=true`;
- scalar trust scores or release-safety probabilities;
- `statebook-sim`.

## Resource bounds

Reuse existing P1–P7 ceilings. The harness must not raise them. Temporary
bundle roots must be caller-scoped and cleaned by tests.

## Authorized future implementation paths

The future implementation may change only:

- root `Cargo.toml` and resulting `Cargo.lock` solely for
  `statebook-e2e-harness` membership and hermetic dependencies;
- new `crates/statebook-e2e-harness/**`;
- new
  `docs/statebook-p8-evaluation-and-falsification-implementation-notes.md`;
- `README.md`;
- `AGENTS.md`;
- `docs/12-task-list.md`;
- `docs/90-whole-codebase-validation-report.md`.

No P1–P7 crate mutation. No publication PDF rewrite.

## Acceptance gates

- unchanged P1–P7 public APIs, fixtures, digests, and tests;
- golden path passes with digest binding across P1/P2/P7 and P4/P5 readback;
- every listed falsifier fails closed;
- focused format, tests, and warning-denied Clippy pass for
  `statebook-e2e-harness`;
- unchanged P1–P7 crate tests pass;
- claim-boundary source scan rejects network/process/live-authority surfaces.

## Nonclaims

P8 creates no live order, fill, routing, custody, signing, pause action,
withdrawal, transfer, bridge, real margin award, clearinghouse recognition,
legal finality, asset control, oracle truth, venue solvency, empirical
calibration, scalar trust score, release-safety probability, admission
authority, Evidence Ledger mutation, production readiness, SOTA, independent
audit, or full-security claim. Hermetic composed regression evidence only.
No value moves. Completing P8 does not satisfy the P7 legal/ops gate.
