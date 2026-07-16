# Statebook P3 Seven Completeness Reports Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Named boundary state slice:
`statebook-p3-seven-completeness-reports-boundary`.

Future implementation state slice:
`statebook-p3-seven-completeness-reports`.

Closed-identity bound correction state slice:
`statebook-p3-closed-identity-bound-correction`.

The correction sets the effective assurance-observation ceiling to the nine
unique closed properties and the effective recovery-path ceiling to the
fourteen implementation-owned path ids. The earlier nominal 128 and 64 values
could not be reached by any valid fixture because duplicate assurance
properties and unknown or duplicate recovery paths reject. This is a
documentation-only consistency correction and grants no new capability.

## Objective

Compose the unchanged P1 semantic-completeness report and unchanged P2
payoff-completeness report with five new hermetic, fixture-qualified reports:
execution, capital, settlement, assurance, and recovery. The result exposes all
seven dimensions separately. It has no aggregate completion boolean, score,
rank, weakest-dimension shortcut, action recommendation, or authority field.

P3 is a local reporting and falsification surface. It does not implement the P4
assurance-resolution, valuation, budget, linked-plan, obligation, queue,
challenge, breaker, release-ratio, or recovery-transition kernel. It does not
implement P5 evidence adapters or portable report bundles.

## Crate and ownership boundary

Future implementation must add one new crate, `statebook-settlement`.

- `statebook-core` remains unchanged. It continues to own P1 semantic identity,
  P2 exact payoff analysis, and their public opaque report APIs.
- `statebook-settlement` may borrow the public P1
  `SemanticCompletenessReport` and P2 `PayoffCompletenessReportV1`, encode them
  independently through public getters, evaluate five closed synthetic fixture
  models, and return one opaque seven-report composition.
- `statebook-settlement` must not reconstruct a `ValidatedContract`, change a
  `StateKeyV1`, reinterpret a P2 residual, or infer a semantic or payoff status.
- No HSAI, admission, `zkbench-core`, venue, custody, execution, clearing,
  signing, pause, transfer, network, process, credential, or filesystem-write
  dependency is permitted.

The new crate may depend only on `statebook-core`, `serde`, `serde_json`,
`sha2`, `hex`, and `thiserror`. A second SHA-256 implementation may be a
dev-dependency only for implementation-diverse golden-vector tests.

## Seven independent dimensions

### 1. Semantic completeness

P3 embeds or borrows the unchanged P1 report and preserves exactly:

- `Complete`;
- `Incomplete`;
- `Unknown`.

The P3 semantic report digest binds the complete public P1 report. P3 may not
promote, demote, replace, or reconstruct the P1 status, missing terms, unknown
terms, unsupported terms, source-terms digest, or normalization-profile digest.

### 2. Payoff completeness

P3 embeds or borrows the unchanged P2 report and preserves exactly:

- `ExactOnDeclaredDomain`;
- `ApproximateOnDeclaredDomain`;
- `Incomplete`.

The P3 payoff report digest binds every public P2 field, including target and
candidate receipts, quantities, contributing validated-contract digests,
domain digest, state observations and statuses, per-asset residuals, worst-case
residuals and tying state ids, assumptions, unmodeled residual classes, and
explicit non-equivalences. P3 may not rerun payoff evaluation or remove an
unsupported state or residual.

### 3. Execution completeness

`ExecutionCompletenessStatusV1` is fixture-qualified:

- `ExecutableInFixture`: every required candidate leg is fully fillable within
  its exact quantity, price, fee, slippage, time, queue-position, atomicity, and
  leg-failure bounds;
- `PartiallyExecutableInFixture`: the retained synthetic book has nonzero
  capacity, but one or more required legs are short or exceed a declared bound;
- `NotExecutableInFixture`: a retained observation proves zero common
  feasibility or a required atomicity or failure condition is explicitly
  unsupported;
- `NotObserved`: the fixture, leg observation, binding, or required bound is
  absent, stale, or unknown.

The report retains every requested and executable leg quantity, exact average
and worst price, exact fees and slippage, queue observation, failure assumption,
time bound, and synthetic unwind residual. A partial result is never an
execution instruction.

### 4. Capital completeness

`CapitalCompletenessStatusV1` is fixture-qualified:

- `RecognizedInFixture`;
- `PartiallyRecognizedInFixture`;
- `NotRecognizedInFixture`;
- `NotEvaluated`.

`RecognizedInFixture` requires one current synthetic statement that names the
authority, eligible account, model id, version and digest, haircut, margin rule,
jurisdiction, effective interval, liquidation horizon, bound analysis subject,
and full recognized exact quantity. Partial quantity, partial leg coverage, or
a nonzero unrecognized offset produces `PartiallyRecognizedInFixture`. An
explicit synthetic denial produces `NotRecognizedInFixture`. Missing, stale,
or future-dated data produces `NotEvaluated`.

Deterministic precedence is:

1. no statement, or a syntactically valid stale or future statement ->
   `NotEvaluated`;
2. an explicit denial covering every bound receipt ->
   `NotRecognizedInFixture`;
3. mixed, partial-quantity, or partial-leg recognition ->
   `PartiallyRecognizedInFixture`;
4. exact full current coverage -> `RecognizedInFixture`.

A malformed statement, wrong subject or receipt digest, duplicate receipt, or
arithmetic overflow returns a typed error and produces no composition.

The serialized report must carry `evidence_class = hermetic_fixture_only`.
`RecognizedInFixture` is not clearing, margin, collateral, liquidation, legal,
or capital authority and must never be serialized as bare `recognized`.

### 5. Settlement completeness

`SettlementCompletenessStatusV1` is fixture-qualified:

- `FinalInFixture`;
- `ConditionalInFixture`;
- `PendingInFixture`;
- `DisputedInFixture`;
- `UnsupportedInFixture`;
- `Unknown`.

The fixture reports source observation, source finality, destination
observation, destination finality, operational reconciliation, and legal
finality separately. Deterministic precedence is:

1. explicit dispute, reversal, or reconciliation mismatch ->
   `DisputedInFixture`;
2. incompatible finality domains or a structurally unsupported transition ->
   `UnsupportedInFixture`;
3. missing required policy, insolvency, reversal, or stage facts -> `Unknown`;
4. a known but unfinished stage -> `PendingInFixture`;
5. passed technical and operational stages with conditional or reversible
   legal finality -> `ConditionalInFixture`;
6. every stage passed under one current compatible fixture -> `FinalInFixture`.

The serialized report must carry `evidence_class = hermetic_fixture_only`.
`FinalInFixture` is not evidence that any transfer occurred or that legal
finality exists outside the synthetic scenario.

### 6. Assurance completeness

P3 does not resolve trust policy, evidence independence, quorum, reputation,
or a permitted release. It reports whether the fixture contains current,
subject-bound observations and disclosed current roots for exactly these
required properties:

- action authorization;
- source authenticity and freshness;
- calculation integrity;
- state-transition integrity;
- solvency and liquid-resource support;
- destination and route policy;
- anomaly and emergency clearance;
- evidence-root disclosure;
- financial-basis binding.

Each property retains a fixture verdict `Pass`, `Fail`, or `Unknown`.
`AssuranceCompletenessStatusV1` is:

- `AllRequiredObservedInFixture`: every property has one unique current
  subject-bound `Pass` verdict and complete current-root and dependency-root
  disclosure;
- `ContradictedInFixture`: at least one current bound fixture verdict is
  `Fail`;
- `IncompleteInFixture`: a property, current-root disclosure, binding, or
  verdict is absent, stale, replay-marked, revoked, superseded, equivocated, or
  unknown;
- `NotObserved`: no assurance fixture exists.

Deterministic precedence is:

1. no assurance fixture -> `NotObserved`;
2. any current, subject-bound `Fail` verdict -> `ContradictedInFixture`;
3. any missing property, duplicate property, stale or future observation,
   replay, revocation, supersession, equivocation, `Unknown` verdict, missing
   root, unknown dependency ancestry, or binding mismatch ->
   `IncompleteInFixture`;
4. otherwise -> `AllRequiredObservedInFixture`.

`AllRequiredObservedInFixture` means complete fixture coverage, not that the
system is safe. P3 must expose repeated or shared dependency roots but must not
calculate independent quorum, collapse roots, choose a tier, or allow one
property to substitute for another. Those are P4 policy functions.

### 7. Recovery completeness

The expected externalization-path inventory comes from the implementation-owned
opaque `RecoveryPathProfileV1::statebook_externalization_v1()`, not from the
observations being tested and not from caller-supplied fixture bytes. The
profile binds schema version 1, profile id `statebook-externalization`, profile
version 1, its digest, and these required path ids:

- `release-class-all`;
- `profitable-close-payout`;
- `liquidation-surplus`;
- `lp-withdrawal`;
- `collateral-withdrawal`;
- `linked-exchange-outbound-leg`;
- `risk-reducing-obligation-endpoint`;
- `bridge`;
- `administrative-transfer`;
- `emergency-route`;
- `transferable-queued-claim`;
- `borrowing`;
- `margin-reuse`;
- `internal-credit-monetization`.

It also binds these five required capabilities:

- stop externalization;
- reconcile every in-flight item;
- preserve evidence;
- restore liabilities without duplication;
- reopen through bounded canary stages.

`RecoveryCompletenessStatusV1` is fixture-qualified:

- `CompleteOnVersionedFixtureProfile`: every profile-required path and capability
  has a passing current observation, the in-flight inventory reconciles, the
  liability restoration is duplicate-free, and at least one bounded canary
  stage is present;
- `IncompleteOnVersionedFixtureProfile`: a required path, capability, item,
  observation, or canary stage is missing or unknown;
- `FailedInFixture`: a fixture explicitly shows an unstoppable path,
  reconciliation mismatch, evidence loss, duplicated liability, or failed
  canary;
- `NotObserved`: no recovery fixture exists.

Deterministic precedence is:

1. no recovery fixture -> `NotObserved`;
2. any explicit failed observation, unstoppable required path, reconciliation
   mismatch, evidence loss, duplicated liability, or failed canary ->
   `FailedInFixture`;
3. any missing, stale, future, or unknown required profile path, capability,
   in-flight item, observation, or canary stage ->
   `IncompleteOnVersionedFixtureProfile`;
4. otherwise -> `CompleteOnVersionedFixtureProfile`.

A pause switch alone is incomplete. The status is confined to the versioned
fixture profile and never implies solvency, operational readiness, or successful
incident recovery. The fixture carries only the expected profile digest. The
evaluator receives the implementation-owned profile separately and rejects a
missing or mismatched digest. A fixture author cannot add, remove, or rename a
required path.

## Common opaque vocabulary

All public P3 structs must have private fields, implement `Serialize` but not
`Deserialize`, expose immutable getters, and be constructible only through the
validated parser and evaluator. Fixture-input structs remain crate-private,
derive `Deserialize` with `deny_unknown_fields`, and cannot escape validation.

Each of the five new reports includes:

- schema version and dimension;
- analysis-subject digest;
- optional canonical fixture digest and `HermeticFixtureOnly` evidence class;
- typed status;
- sorted source-evidence digests;
- typed assumptions, missing facts, and reasons;
- explicit `evaluated_at` and optional `expires_at`;
- dimension-specific residuals;
- deterministic report digest.

The fixture digest and expiry are `None` only when that dimension's fixture is
absent. A stale or future fixture retains its original `Some` digest and
`Some(expires_at)`.

The seven-report composition contains the unchanged semantic and payoff reports
plus the five new reports. One composition-level lineage field retains the
combined `fixture_document_sha256`; it is excluded from every dimension report
and from canonical fixture, report, and composition identity. At composition
level it must not expose `complete`,
`all_complete`, `weakest`, `score`, `rank`, `safe`, `authorized`, `executable`,
`release`, or an equivalent aggregate helper. Dimension-specific accessors such
as `execution()` and fixture-qualified statuses such as `ExecutableInFixture`
remain required. Tests inspect the top-level serialized schema and public API
shape rather than rejecting those dimension-specific words lexically.

## Analysis subject and binding

`AnalysisSubjectV1` binds one P1/P2 analysis without changing either crate. It
is constructed in `statebook-settlement` only from public P1/P2 report APIs. Its
canonical preimage binds:

- schema version;
- semantic-completeness report digest;
- P2 target StateKey, exact quantity, and sorted validated-contract digests;
- sorted P2 candidate receipts, including each StateKey, exact quantity, and
  sorted contributing validated-contract digests;
- P2 declared-domain digest;
- complete P2 payoff-completeness report digest.

Every supplied fixture carries this analysis-subject digest. A mismatch rejects
composition; it does not create a plausible downgraded report.

## Canonical identity

No identity is a hash of JSON or a hash of a Serde rendering. The new crate uses
a tagged, length-delimited canonical binary stream:

```text
domain = fixed ASCII bytes ending in NUL
schema = u16 big-endian
field  = u16 tag || u32 big-endian length || value bytes
```

Booleans and enums use fixed one-byte discriminants. Signed integers use
fixed-width big-endian two's-complement bytes. Unsigned integers use fixed-width
big-endian bytes. `SignedRational` uses its canonical fixed-width `i128`
numerator followed by fixed-width `u128` denominator. Strings are exact
validated ASCII bytes. Digests are raw 32-byte values. Optional values use a
one-byte absence/presence marker. Sets and maps encode a count followed by
lexicographically sorted encoded members. No platform-width integer enters a
preimage.

Domains are distinct:

```text
statebook:p3-semantic-report:v1\0
statebook:p3-payoff-report:v1\0
statebook:p3-analysis-subject:v1\0
statebook:p3-execution-fixture:v1\0
statebook:p3-capital-fixture:v1\0
statebook:p3-settlement-fixture:v1\0
statebook:p3-assurance-fixture:v1\0
statebook:p3-recovery-profile:v1\0
statebook:p3-recovery-fixture:v1\0
statebook:p3-execution-report:v1\0
statebook:p3-capital-report:v1\0
statebook:p3-settlement-report:v1\0
statebook:p3-assurance-report:v1\0
statebook:p3-recovery-report:v1\0
statebook:p3-seven-report-composition:v1\0
```

The composition digest binds schema, analysis-subject digest, injected
evaluation time, recovery-profile digest, and the seven report digests in the
fixed dimension order above. P1 StateKey bytes and P2 state-domain bytes remain
unchanged.

The duplicate-key-aware parser also computes SHA-256 over the exact input
document bytes as `fixture_document_sha256`. This digest appears once in the
composition-level lineage and never enters any dimension report or canonical
fixture, report, or composition identity. Reordering a semantically unordered
collection changes the raw document digest while the canonical fixture,
dimension-report, and composition digests remain unchanged.

## Fixed-width exact arithmetic

All prices, quantities, fees, slippage, haircuts, recognized amounts, and
residuals use the existing public `SignedRational` value and its checked
fixed-width operations. Floating point, saturation, lossy conversion, implicit
currency conversion, implicit asset netting, platform-width financial
arithmetic, and release-favouring rounding are forbidden.

Execution depth walking is deterministic: levels sort by declared side and
exact price, then stable level id; quantity consumes in that order; exact
notional, average price, fee, and slippage calculations use checked operations.
Any overflow returns `CompletenessEvaluationErrorV1::ArithmeticOverflow`, emits
no report or composition, and cannot alter P1 or P2 output.

For each execution leg, `evaluated_at` must fall in the closed interval
`[observed_at, expires_at]` and at or before the leg deadline; otherwise the
execution status is `NotObserved`. A buy admits only
levels at or below `maximum_price` and consumes them in ascending price then
level-id order. A sell admits only levels at or above `minimum_price` and
consumes them in descending price then level-id order. Each consumed quantity
is `min(remaining_requested, level_quantity)`. Gross notional is the exact sum
of `consumed_quantity * level_price`; exact average price is gross notional
divided by filled quantity. The sole fee rule is an exact nonnegative rate over
absolute gross notional, applied after depth consumption. The positive
reference price is named by the fixture. Buy slippage is
`(average_price - reference_price) / reference_price`; sell slippage is
`(reference_price - average_price) / reference_price`; favorable negative
slippage is retained and is within every nonnegative maximum-slippage bound.
Requested quantities and level prices must be strictly positive. Fee rates,
maximum fees, and maximum-slippage bounds must be nonnegative.

The evaluator derives one deterministic maximal acceptable prefix. At each
ordered level it takes the minimum of remaining requested quantity, remaining
level quantity, the exact quantity allowed by `maximum_fee`, and the exact
quantity allowed by `maximum_slippage`. For a buy, define
`slippage_price_bound = reference_price * (1 + maximum_slippage)`; if the next
price exceeds that bound, the additional quantity is at most
`(slippage_price_bound * current_quantity - current_notional) /
(next_price - slippage_price_bound)`. For a sell, define
`slippage_price_bound = reference_price * (1 - maximum_slippage)`; if the next
price is below that bound, the additional quantity is at most
`(current_notional - slippage_price_bound * current_quantity) /
(slippage_price_bound - next_price)`. With a positive fee rate, the additional
quantity is also at most
`(maximum_fee - current_fee) / (fee_rate * next_price)`; a zero fee rate adds no
fee limit. Negative numerators give zero additional quantity. Checked exact
rational comparison selects the minimum without rounding. The evaluator stops
when the next acceptable quantity is zero and reports only the accepted prefix
as executable quantity.

`ExecutableInFixture` requires every leg's acceptable quantity to equal its
full requested quantity and every bound to pass. `PartiallyExecutableInFixture`
requires every required leg to have positive acceptable quantity, at least one
required leg to have acceptable quantity below its requested quantity, and no
explicitly unsupported required condition. `NotExecutableInFixture` results if
any required leg has zero acceptable quantity or a required atomicity, queue,
or leg-failure condition is explicitly unsupported. A missing or unknown
required observation yields `NotObserved`. Synthetic unwind residuals are only
the exact unfilled quantities keyed by bound leg id and asset; P3 never reruns
or modifies P2 payoff residuals.

## Closed fixture inputs

One duplicate-key-aware parser may validate a combined
`CompletenessFixtureSetV1`. Semantic and payoff reports are supplied as opaque
Rust values, not reconstructed from JSON.

Absent dimension input is valid and produces that dimension's absence status.
Syntactically valid stale or future evidence produces the frozen
dimension-specific nonpositive status while retaining lineage. Malformed JSON
or fields, wrong analysis-subject or profile binding, digest mismatch,
duplicate semantic identity, invalid exact arithmetic, or overflow returns a
typed `FixtureParseErrorV1` or `CompletenessEvaluationErrorV1` and produces no
seven-report composition. A valid explicit negative observation produces its
dimension's negative status.

Execution fixture fields are limited to subject digest, observation interval,
venue and account ids, candidate-leg and StateKey bindings, side, exact
requested quantity, exact price/quantity depth levels, price/fee/slippage/time
bounds, queue observation, atomicity observation, leg-failure model, and source
digests.

Capital fixture fields are limited to subject digest, observation interval,
named synthetic authority and account, model id/version/digest, haircut and
margin-rule refs, jurisdiction, liquidation horizon, recognized receipt refs
and exact quantities, explicit fixture verdict, and source digests.

Settlement fixture fields are limited to subject digest, source and destination
finality domains, six distinct stage observations, reversal and insolvency
rules, dispute/reversal flags, observation interval, and source digests.

Assurance fixture fields are limited to subject digest, the nine property
observations, issuer, subject, scope digest, nonce, issue/expiry times, fixture
verdict, current trust roots, dependency roots, dependency-disclosure status,
revoked/superseded/replayed/equivocated flags, and source digests.
Both current and dependency roots use one closed `AssuranceRootV1` record with
a `RootClassV1` of `Data`, `Operator`, `Cloud`, `Kms`, `Rpc`, `CiCd`, `Model`,
or `Signer`, plus a validated root id. Every passing property requires at least
one current root. Duplicate `(root_class, root_id)` identities reject rather
than overwrite.
`DependencyDisclosureV1` is `Complete` or `Unknown`. `Unknown` ancestry blocks
`AllRequiredObservedInFixture`. Shared root ids remain visible, but P3 performs
no independence or quorum calculation. These are disclosed facts, not a
resolved assurance policy.

Recovery fixture inputs are limited to the implementation-owned profile digest,
subject digest, observations for its five capabilities, in-flight item
inventory and reconciliation digests, evidence-preservation ref, before/after liability
digests, duplicate-prevention observation, bounded canary stages, observation
interval, and source digests.

## Resource bounds

Future implementation freezes:

- fixture document: at most 1,048,576 bytes;
- validated ASCII identifier: 1 through 128 bytes;
- P2 declared states: unchanged maximum of 256;
- candidate execution legs: unchanged maximum of 64;
- book depth: at most 64 levels per leg and 4,096 total;
- capital receipt references: at most 64;
- settlement obligations: at most 64;
- assurance observations: at most 9, one for each unique required property;
- current or dependency roots per observation: at most 32 each;
- recovery-profile paths: exactly the 14 implementation-owned path ids, with a
  parser ceiling of 14;
- in-flight recovery items: at most 256;
- canary stages: at most 16;
- source-evidence digests per dimension: at most 256.

Collection constructors reject on the first item over the limit and must not
consume one additional caller item. Duplicate ids, duplicate JSON keys, unknown
fields or enums, JSON numeric financial values, non-ASCII or control-bearing
identifiers, malformed digests, invalid times, nonpositive required quantities,
invalid price ordering, wrong subject bindings, and checked-arithmetic overflow
fail closed.

## Cross-dimension composition rules

1. No dimension implies or modifies another.
2. P1 and P2 reports remain byte-for-byte semantically unchanged.
3. Missing optional fixture input yields only that dimension's
   `NotObserved`, `NotEvaluated`, or `Unknown` result.
4. A present malformed, wrongly bound, digest-mismatched, duplicate, or
   overflowing fixture returns a typed error and produces no composition.
5. Exact payoff does not imply a fill, recognized offset, finality, assurance,
   or recoverability.
6. Execution does not imply payoff, capital, settlement, assurance, or
   recovery.
7. Capital status is never inferred from residual, collateral amount,
   execution, an authority name, or another dimension.
8. Settlement finality is never inferred from only source finality,
   destination observation, or technical completion.
9. Assurance evidence can populate only its declared property. Current roots
   and correlations remain visible; P3 does not resolve quorum or independence.
10. Recovery completeness is measured against the versioned expected-path
    profile, never a self-declared observed subset.
11. Expiry changes only the dimension that owns the expired fixture.
12. P3 defines no total order over statuses and makes no policy or action
    decision.

Expired or future execution observations map to `NotObserved`; expired or
future capital statements map to `NotEvaluated`; expired or future settlement
evidence maps to `Unknown`; expired or future assurance observations map to
`IncompleteInFixture`; and expired or future recovery observations map to
`IncompleteOnVersionedFixtureProfile`. A malformed present fixture rejects before
status derivation.

## Frozen scenarios

The future implementation must cover:

1. one fully populated hermetic composition with seven visible dimensions and
   no aggregate boolean;
2. exact P2 payoff plus absent or stale book -> execution `NotObserved`;
3. one short book leg -> `PartiallyExecutableInFixture` with explicit unwind
   residual;
4. explicitly unsupported required atomicity or zero common capacity ->
   `NotExecutableInFixture`;
5. full, partial, denied, absent, and expired synthetic capital statements;
6. capital subject, authority, account, model, or time mismatch cannot produce
   fixture recognition;
7. all six settlement statuses and the fixed precedence order;
8. source finality alone cannot produce `FinalInFixture`;
9. all nine assurance properties present with current-root disclosure;
10. wrong-property, missing-root, stale, replayed, revoked, superseded,
    equivocated, and unknown assurance observations cannot produce complete
    fixture coverage;
11. shared dependency roots remain visible and are not counted or collapsed;
12. a pause observation alone -> recovery incomplete;
13. an expected path absent from the recovery fixture -> recovery incomplete;
14. reconciliation mismatch, evidence loss, duplicate liability, or failed
    canary -> recovery failed;
15. co-shrinking recovery observations cannot change the implementation-owned
    path profile, and a wrong profile digest rejects composition;
16. every single-dimension fixture mutation leaves the other dimension report
    bytes and digests unchanged;
17. input and set permutation invariance, with changed raw document digest but
    unchanged canonical fixture/report identity for reordered semantic sets;
18. every exact effective resource limit succeeds and limit plus one rejects,
    including the closed nine-property assurance and fourteen-path recovery
    identity ceilings;
19. duplicate-key, unknown-field, JSON-number, malformed digest/time,
    noncanonical identifier, and overflow negatives;
20. independent test encoding reproduces frozen semantic, payoff, subject,
    fixture, recovery-profile, five report, and composition digests;
21. unchanged P1 701-byte preimage, StateKey
    `f1662f3fb5a10c074680c0baf76ba488b7230337456358be92f3127d8a632c08`,
    and validated-contract digest
    `7634410968adb9b56c62f213de7956796f9f3f62b102d4f6efe7f45d86858788`;
22. unchanged P2 domain digest
    `67cb8e1807cd3e619f73d569f70de494ef60610f4d44acea236b0ee006e45e6a`,
    payoff vectors, exact arithmetic, and status behavior;
23. serialized-output and source scans reject an aggregate completeness boolean,
    scalar trust score, network, process, filesystem write, unsafe code,
    floating point, credentials, HSAI, admission, `zkbench`, P4 transitions,
    P5 adapters, and runtime authority.

## Authorized future implementation paths

The future implementation may change only:

- root `Cargo.toml`, solely to add `crates/statebook-settlement` as a workspace
  member;
- resulting `Cargo.lock` dependency records;
- new `crates/statebook-settlement/Cargo.toml`;
- new `crates/statebook-settlement/src/lib.rs`;
- new `crates/statebook-settlement/src/completeness.rs`;
- new `crates/statebook-settlement/tests/claim_boundary.rs`;
- new `crates/statebook-settlement/tests/completeness_reports.rs`;
- new
  `crates/statebook-settlement/tests/fixtures/completeness_reports_v1.json`;
- new
  `docs/statebook-p3-seven-completeness-reports-implementation-notes.md`;
- `README.md`;
- `AGENTS.md`;
- `docs/12-task-list.md`;
- `docs/90-whole-codebase-validation-report.md`.

No `statebook-core`, HSAI, admission, `zkbench-core`, tool, script, publication
PDF, whitepaper, PRD, source-index, media, or external adapter path is
authorized.

## Acceptance gates

- no P1 or P2 source, fixture, canonical bytes, digest, status, or test changes;
- the five new reports remain fixture-qualified in Rust and serialized names;
- every report carries typed reasons, residuals, evidence refs, evaluation
  time, expiry, and a deterministic digest;
- no aggregate boolean, score, rank, weakest result, recommendation, or action
  field exists;
- exact arithmetic fails closed without partial numeric output;
- missing observations never become pass, recognized, executable, or final;
- the recovery fixture is checked against a separately versioned path profile;
- current roots and dependency roots remain disclosed without P4 resolution;
- all frozen scenarios and bounds pass;
- an implementation-diverse encoder reproduces all golden digests;
- focused format, tests, and warning-denied Clippy pass;
- repository documentation and hygiene tests pass;
- clean-tree workspace tests run;
- clean-tree workspace Clippy findings outside P3 are reported, not absorbed;
- independent scope/claim-boundary and fixture/digest/arithmetic reviews
  complete.

The root contains no `package.json` or `pnpm-lock.yaml`; no pnpm or npm command
is available for this slice.

## Nonclaims

P3 creates no live order book, market data, price truth, order, fill, routing,
optimization, margin award, collateral mutation, clearing recognition, legal
finality, transfer, signing, custody, pause action, withdrawal delay, release
ratio, cap, reservation, queue, challenge, externalization, settlement or
recovery transition, network access, process execution, filesystem output,
credential handling, HSAI evidence, admission decision, P4 policy resolution,
P5 adapter, accepted Evidence Ledger mutation, benchmark evidence, proof,
semantic-correctness claim, production readiness, SOTA, independent audit, or
full-security claim.
