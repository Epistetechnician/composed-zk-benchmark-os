# Statebook P4 Settlement Simulator Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p4-settlement-simulator`.

## Outcome

The existing `statebook-settlement` crate now hosts a pure deterministic settlement
transition kernel:

- `decide_and_transition(request, current_state, clock) -> DecisionRecordV1`;
- `parse_settlement_scenario_v1(bytes) -> SettlementScenarioV1` for hermetic fixtures;
- closed five-way outcomes (`Rejected`, `Quarantined`, `Immediate`, `Queued`, `Frozen`);
- fail-closed hard gates 1–12 with zero instant release on fail or unknown;
- conservative valuation, assurance tier selection, linked-plan and obligation checks;
- multi-axis budget ledger reservations with compare-and-swap tip semantics;
- queue, breaker, and recovery interaction under an injected clock.

Decision records are serialize-only, non-authoritative, and contain no transfer
command. No value moves.

## Implemented boundary

P4 extends `statebook-settlement` only. P3 `completeness.rs` logic, fixtures,
digests, and public APIs remain unchanged aside from two additive crate-internal
constructors required for P4 digest construction and fixture root parsing:

- `DigestV1::from_raw_bytes`;
- `Deserialize` on `AssuranceRootV1`.

Resource ceilings are frozen:

| Constant | Value |
|----------|------:|
| `MAX_FIXTURE_BYTES_V1` | 1,048,576 |
| `MAX_LINKED_PLAN_LEGS_V1` | 8 |
| `MAX_BUDGET_AXES_V1` | 16 |
| `MAX_LEDGER_JOURNAL_ENTRIES_V1` | 256 |
| `MAX_QUEUE_PARTS_V1` | 4 |
| `MAX_QUEUE_DEPTH_V1` | 64 |
| `MAX_CHALLENGES_V1` | 16 |
| `MAX_BREAKER_SCOPES_V1` | 8 |
| `MAX_EVIDENCE_OBSERVATIONS_V1` | 128 |
| `MAX_EVIDENCE_ROOTS_V1` | 32 |
| `MAX_VALUATION_OBSERVATIONS_V1` | 32 |
| `MAX_IN_FLIGHT_TRANSFERS_V1` | 64 |
| `MAX_SCENARIO_STEPS_V1` | 16 |

Canonical identity duplicates the P3 TLV pattern in an independent P4 module with
domain-separated SHA-256 tags:

- `statebook:p4-intent:v1\0`
- `statebook:p4-decision-context:v1\0`
- `statebook:p4-release-attempt:v1\0`
- `statebook:p4-evidence-snapshot:v1\0`
- `statebook:p4-valuation-profile:v1\0`
- `statebook:p4-policy:v1\0`
- `statebook:p4-ledger-tip:v1\0`
- `statebook:p4-settlement-state:v1\0`
- `statebook:p4-decision-record:v1\0`

An independent `ring` SHA-256 test reproduces the intent digest golden vector from
`intent_payload`.

## Local validation evidence

The following focused gates pass on this worktree:

```text
cargo fmt -p statebook-settlement -- --check
cargo test -p statebook-settlement --tests
cargo clippy -p statebook-settlement --all-targets -- -D warnings
cargo test -p statebook-core
```

The P4 package adds thirteen kernel regression tests, five claim-boundary scans,
and five hermetic JSON fixtures under `tests/fixtures/p4/`. Together with unchanged
P3 tests, the crate reports forty-eight passing integration tests.

## Remaining gaps vs boundary frozen scenarios

The implementation satisfies the minimum acceptance slice and required tests.
The full thirty-seven-scenario adversarial corpus from the boundary spec is not
 exhaustively encoded as named fixtures in this commit. Not yet covered as
 dedicated replay fixtures include, among others:

- fresh revalidation after challenge window with new decision context;
- cancel and destination replacement intent digest rotation;
- full challenge grammar variants (duplicate, censored, unavailable);
- evidence expiry while queued to `RevalidationRequired`;
- breaker TTL exhaustion into `Resolution` and malicious renewal rejection;
- hysteresis rollback and policy downgrade timing;
- destination finality capacity consumption and `ProvenNoOutflow` restoration;
- recovery halt, reconciliation mismatch, canary failure, and reopen stages;
- prepared-later oracle reuse and stale-data/fresh-transport cases;
- compromised shared upstream root quorum failures;
- artificial profit payout, split-agent cap expansion, slow drain, and concurrent
  finalizer races;
- model-confidence bypass attempts.

These remain documented deferrals for follow-on fixture expansion; the kernel
surface is present and fail-closed for the implemented paths.

## Claim ceiling

This is local hermetic fixture regression evidence only. It is not a live book,
fill, clearing statement, capital recognition, legal finality, evidence-root
resolution, successful incident recovery, permitted release, execution or
settlement instruction, benchmark evidence, production readiness, SOTA,
independent audit, or full security. No value moves.
