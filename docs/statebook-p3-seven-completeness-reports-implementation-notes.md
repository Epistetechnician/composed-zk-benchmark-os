# Statebook P3 Seven Completeness Reports Implementation Notes

Date: 16 July 2026.

State slice: `statebook-p3-seven-completeness-reports`.

## Outcome

The isolated `statebook-settlement` crate now composes the unchanged P1
semantic-completeness report and unchanged P2 payoff-completeness report with
five independent, fixture-qualified reports:

- execution completeness;
- capital completeness;
- settlement completeness;
- assurance completeness; and
- recovery completeness against the implementation-owned
  `statebook-externalization` profile.

The composition exposes all seven dimensions and no aggregate completion
boolean, scalar score, ordering, weakest-dimension shortcut, action,
recommendation, or authority.

## Implemented boundary

All fixture input remains crate-private, uses strict unknown-field rejection,
rejects duplicate JSON object keys, and accepts financial quantities only as
decimal strings inside exact rational objects. SHA-256 values are lowercase
64-character hex. Identifiers are nonempty bounded ASCII without whitespace or
control characters. Negative or reversed observation intervals, pre-observation
execution deadlines, negative evaluation times, malformed bindings, and checked
arithmetic overflow fail closed without a composition.

Every collection is decoded through an internal bounded sequence type. A known
oversized sequence is rejected from its length hint; a streaming sequence stops
on its first over-limit item and does not consume the following item. The gross
document ceiling is 1,048,576 bytes. The closed semantic exact maxima are nine
unique assurance properties and fourteen implementation-owned recovery paths,
not the unreachable nominal parser ceilings.

`ValidatedCompletenessFixtureV1` is an opaque public parse receipt. Its
serialized form discloses only schema version, raw document digest, and the five
dimension-presence flags. The private validated wire data cannot escape.

## Canonical identities

Canonical identity is a domain-separated SHA-256 over tagged,
length-delimited binary fields. It is never a JSON or Serde-rendering hash.
The implementation independently canonicalizes the public P1 semantic and P2
payoff reports, the analysis subject, each fixture, the recovery profile, each
new report, and the seven-report composition.

The capital-context correction uses
`statebook:p3-capital-context:v1\0`. Its preimage binds schema, analysis
subject, synthetic authority, eligible account, model id/version/digest,
haircut, margin rule, jurisdiction, liquidation horizon, and observation
interval. Every capital receipt carries this digest. A mismatch returns
`CapitalContextDigestMismatch` and emits no composition. Coherently changing
both the statement and receipt digest creates a different hermetic fixture; it
does not establish clearing, margin, collateral, liquidation, or legal
authority.

The independent golden test uses a separately written TLV encoder and `ring`'s
SHA-256 implementation. It reproduces the semantic, payoff, subject, five
fixture, capital-context, recovery-profile, five report, and composition
digests from public report getters and fixture JSON semantics.

## Report semantics

Each new report carries schema and dimension, analysis-subject digest,
fixture digest, `HermeticFixtureOnly`, sorted source evidence, typed
assumptions, typed missing facts, typed reasons, evaluation and expiry times,
dimension-specific observations or residuals, and a deterministic digest.

Execution computes the maximal exact fill prefix under declared side, price,
fee, slippage, queue, atomicity, failure, and deadline facts. Capital retains
signed required quantity, nonnegative recognized magnitude, and signed
recognition residual. Settlement retains obligation-scoped six-stage evidence
and uses the fixed dispute, support, missing, pending, conditional, final
precedence. Assurance retains all nine property verdicts plus current and
dependency roots without resolving independence or quorum. Recovery retains all
fourteen paths, five required capabilities, in-flight reconciliation, evidence
and liability checks, and canary observations under the versioned profile.

Freshness and status changes remain dimension-local. Tests mutate each of the
five fixtures separately and prove the other four serialized report bytes and
digests are unchanged.
All semantically unordered fixture collections are canonical-sorted; their
permutation changes only raw document lineage.

## Frozen compatibility

P1 and P2 source and fixtures are unchanged. Regression checks retain:

- P1 canonical preimage length of exactly 701 bytes;
- P1 StateKey `f1662f3fb5a10c074680c0baf76ba488b7230337456358be92f3127d8a632c08`;
- P1 validated-contract digest
  `7634410968adb9b56c62f213de7956796f9f3f62b102d4f6efe7f45d86858788`;
- P2 domain digest
  `67cb8e1807cd3e619f73d569f70de494ef60610f4d44acea236b0ee006e45e6a`;
- P3 analysis-subject digest
  `fd4c10a8b9cadc57e5021b9fdf380ce3abbbb7e270bbb981113de47eded7d73a`;
- recovery-profile digest
  `3d412a89c19e5e2ec4812bde5233784574815cab2fc063dab5653d113730601e`;
- frozen report digests for semantic, payoff, execution, capital, settlement,
  assurance, and recovery; and
- composition digest
  `5becefa3f2ab8239dc516fbdb965544f0126ca341723c871c7babe2aff69086f`.

## Local validation evidence

The following focused gates pass on this worktree:

```text
cargo fmt -p statebook-settlement -- --check
cargo test -p statebook-settlement --tests
cargo clippy -p statebook-settlement --all-targets -- -D warnings
cargo test -p statebook-core
cargo clippy -p statebook-core --all-targets -- -D warnings
```

The P3 package result is one bounded-sequence unit test, four claim-boundary
tests, and twenty-five completeness-report tests. The repository-wide root
Clippy gate is not claimed here; any inherited failure outside the named P3
state slice remains an explicit repository-level caveat rather than P3
evidence.

## Claim ceiling

This is local hermetic fixture regression evidence only. It is not a live book,
fill, clearing statement, capital recognition, legal finality, evidence-root
resolution, successful incident recovery, permitted release, execution or
settlement instruction, benchmark evidence, Level2+ evidence, proof, semantic
correctness, production readiness, independent audit, SOTA, or full security.
It adds no network, process, filesystem output, credentials, HSAI, admission,
zkbench, P4 policy, P5 adapter, runtime action, or external authority.
