# Statebook P4 Settlement Simulator Boundary

Date: 16 July 2026.

Status: documentation-first boundary complete; implementation requires a
separate commit.

Evidence ceiling for this document: `DocumentationOnly` at
`Level0DesignNote`.

Named boundary state slice:
`statebook-p4-settlement-simulator-boundary`.

Future implementation state slice:
`statebook-p4-settlement-simulator`.

## Objective

Implement one pure deterministic settlement transition kernel inside the
existing `statebook-settlement` crate. The kernel evaluates synthetic
externalization requests against hard gates, assurance resolution, conservative
valuation, linked-plan and obligation validation, multi-axis exactly-once
budgets, queue and challenge transitions, circuit breakers, hysteresis, and
recovery transitions under an injected clock.

P4 addresses the policy and transition surface that P3 explicitly deferred:
assurance resolution, independence and quorum, tier selection, valuation,
budgets, linked plans, obligations, queues, challenges, breakers, release
ratios, and recovery transitions. The output is a non-authoritative decision
record. No value moves.

P4 does not implement P5 evidence adapters or portable report bundles, P6 live
or captured external sources, or P7 authority integration.

## Crate and ownership boundary

Future implementation must extend `crates/statebook-settlement` only.

- `statebook-core` remains unchanged. P1 semantic identity and P2 payoff
  analysis stay byte-identical.
- Existing P3 completeness reports, fixtures, digests, statuses, and public
  APIs remain unchanged. P4 may borrow public P3 getters and composition
  digests; it may not rewrite semantic, payoff, execution, capital, settlement,
  assurance, or recovery completeness statuses.
- No new workspace crate is authorized. In particular, `statebook-sim` remains
  unauthorized. Deterministic scenario execution for the frozen adversarial
  corpus lives as hermetic tests and minimal injected-clock helpers inside
  `statebook-settlement`.
- No HSAI, admission, `zkbench-core`, venue, custody, execution, clearing,
  signing, pause, transfer, network, process, credential, or filesystem-write
  dependency is permitted.

Allowed crate dependencies remain those already authorized for
`statebook-settlement`, plus any additive hermetic test-only SHA-256 diversity
already used by P3. No new runtime network, crypto-protocol, or process crate
is authorized.

## Settlement transition kernel

The single public kernel surface is:

```text
decide_and_transition(request, current_state) -> DecisionRecordV1
```

`DecisionRecordV1` is a non-authoritative, serialize-only opaque record. Its
closed outcome enum is exactly:

- `Rejected`
- `Quarantined`
- `Immediate`
- `Queued`
- `Frozen`

The record must bind, via domain-separated digests:

- intent digest;
- analysis-subject digest from P3 when the financial basis is contract-derived;
- seven-completeness composition digest when required by gate 9;
- evidence snapshot digest;
- valuation profile digest;
- policy digest;
- linked-plan or obligation digest when present;
- budget ledger tip before and after the attempted transition;
- queue and transfer status transitions;
- typed reasons, missing facts, and nonclaims;
- evaluation time from the injected clock.

The kernel must not emit a transfer command, signing request, pause order,
custody instruction, margin award, or venue control message. Callers may not
mutate queue, budget, breaker, or recovery state outside the kernel.

## Release classification

Before gates, every request classifies into exactly one closed class:

- `InternalRiskState`
- `AtomicLinkedExchange`
- `ExternalRiskReducingObligation`
- `ExternalUnconditional`
- `SystemicOrExceptional`

Classification is fail-closed. Unknown, contradictory, or underspecified
classification becomes `SystemicOrExceptional`, never `InternalRiskState`.

Only `ExternalUnconditional` may receive an ordinary queued remainder after a
partial instant release. A risk-reducing obligation that cannot fill its
declared amount is all-or-none zero and routes to the default-resolution path,
not a withdrawal queue.

## Hard gates

Any applicable hard gate that fails or is unknown sets the instant release
amount to zero and routes to `Rejected` or `Quarantined`. The queue is not
permission to release an invalid request after time passes.

The closed gate set is exactly:

1. Action and destination currently authorized.
2. Source observations authentic, fresh, monotonic, one-time consumable,
   equivocation-checked, and bound to the exact request id, order or
   obligation id, nonce, action, policy, and originating state transition.
   Pre-prepared reports must not become reusable merely because a later
   timestamp matches.
3. PnL, collateral, redemption, or transfer amounts recomputed from bound
   inputs under the current policy.
4. Originating state transition exists once, is consistent, and is
   non-replayable.
5. Reserves and liquid resources support the release under normal and declared
   stress assumptions.
6. Destination and route pass allow, novelty, sanctions, bridge, and
   contract-behavior policy.
7. No critical anomaly, freeze, rollback, compromise, oracle disagreement, or
   exhausted system loss budget is active for the affected scope.
8. Independent evidence does not count a shared compromised root as quorum.
9. Contract-derived value binds terms digest, `StateKeyV1`, and acceptable
   coherence and settlement completeness digests that are not stale or
   superseded.
10. Pending or anomalous PnL has zero reuse value until every `ReuseFinality`
    predicate passes; prefunding is tracked separately.
11. An `ExternalRiskReducingObligation` matches exactly, strictly decreases
    exposure, uses a non-withdrawable destination, and is finality-capable
    before its deadline.
12. An `AtomicLinkedExchangePlan` passes structural and per-leg gates; outbound
    capacity is reserved gross; inbound legs never create same-operation
    capacity.

Zero, negative, wrong-sign, overflowed, or noncanonical amounts reject before
valuation, gates, reservation, or ratio calculation. Rounding must never favour
release.

## Assurance resolution and tiers

P4 resolves the assurance observations that P3 only discloses. Resolution may
select a named tier only after every applicable hard gate passes.

Closed tier names:

- `Quarantined`
- `UnprovenOrNovel`
- `CurrentlyAssured`
- `StrongCurrentAssuranceLowImpact`

Tier fractions, delays, and refill parameters are versioned synthetic
`AssuranceTierPolicy` fixture data. They are not empirically calibrated
production constants and must not appear as undeclared implementation magic
numbers.

Assurance resolution must:

- evaluate root independence; vendor count is not quorum;
- refuse one property substituting for another;
- refuse shared dependency roots counting as independent witnesses;
- treat unknown independence as gate failure or unknown, never pass;
- never emit a scalar trust score, reputation score, or release-safety
  probability.

## Conservative valuation

Cross-asset capacity uses a conservative upper-bound valuation profile:

- exact rational observation rates only;
- declared numeraire, max age, aggregation rule, and stress multiplier;
- independence report over source roots;
- stale, missing, or conflicting observations reject;
- action-oracle or PnL-derived prices must not become the budget valuation
  fallback.

The resulting ratio is a capacity bound, not a probability of correctness or an
actor reputation score.

## Exposure budgets and ledger

P4 owns the synthetic multi-axis budget ledger:

- native asset counters and common-numeraire counters;
- live reservations and in-flight amounts;
- consumed-release journal;
- versioned ledger tip with compare-and-swap semantics;
- exactly-once request and reservation ids;
- deterministic refill epochs that are sequential, capped, and never backfill.

At most one concurrent tip mutation may succeed for a given expected tip.
Splitting a request across subjects, destinations, assets, or blocks must not
expand aggregate caps. Destination finality moves in-flight to consumed without
restoring capacity. Capacity returns only through validated
`ProvenNoOutflow` evidence.

## Linked plans and obligations

### Atomic linked exchange

A plan requires at least two legs, both directions, unique leg ids, a canonical
leg-set digest, and a primary outbound leg matching the enclosing request. Every
leg carries financial basis, budget-axis refs, and current assurance. Evaluation
is all-or-none: either every leg passes and gross outbound capacity is reserved,
or no leg reserves.

### External risk-reducing obligation

An obligation requires fixed beneficiary, restricted obligation account, asset,
exact amount, deadline, valid-until, prefunding and segregation refs, destination
use restriction, destination finality policy, exposure-before and exposure-after
digests, and an independent risk-reduction ref. Partial fill is forbidden. A
false risk-reducing label, withdrawable destination, or non-decreasing exposure
rejects.

## Queue, challenge, and release parts

Closed queue statuses:

- `None`
- `Queued`
- `Challenged`
- `EvidenceExpired`
- `Frozen`
- `Cancelled`
- `RevalidationRequired`

Closed transfer statuses:

- `Unreserved`
- `Reserved`
- `Submitted`
- `SourceObserved`
- `SourceFinalized`
- `DestinationObserved`
- `DestinationFinalized`
- `Consumed`
- `ProvenNoOutflow`

Valid combinations are closed. In particular:

- `Queued`, `EvidenceExpired`, `Cancelled`, and `RevalidationRequired` require
  `Unreserved`;
- `Challenged` and `Frozen` block new reservation or submission but not
  observation, finality, or reconciliation of already-submitted transfers;
- `Consumed` and `ProvenNoOutflow` require queue `None` and are terminal;
- timer passage alone cannot release;
- release after a waiting period requires a fresh decision context and attempt
  over fresh evidence and budgets;
- cancel or destination replacement requires a new parent intent digest;
- pending queued value has zero withdrawal, bridge, transfer, borrow,
  collateral, margin-reuse, or release-budget value.

Challenges use a bounded evidence grammar with explicit trust roots, deadline,
and affected scope. Arbitrary veto messages are rejected.

## Circuit breakers and hysteresis

Closed breaker states and edges:

```text
Normal     -> Guarded | Halted
Guarded    -> Challenged | Halted | Resolution
Challenged -> Guarded | Halted | Resolution
Halted     -> Resolution
Resolution -> Recovery
Recovery   -> Normal | Guarded | Halted
```

There is no direct `Halted -> Normal` transition. TTL or cumulative-renewal
exhaustion enters `Resolution`. A breaker action must name exact scope, trigger
evidence, expiry, renewal ceiling, invoking authority, whether internal
risk-reducing model transitions continue, safe exits, and the audit or appeal
path. Emergency overrides cannot silently increase instant release.

Policy hysteresis is asymmetric:

- new risk evidence may tighten immediately;
- evidence expiry immediately removes affected assurance;
- relaxation requires documented resolution evidence, fresh independent
  evidence, minimum dwell, required clean epochs, and independent approval of a
  successor policy digest;
- every cap increase or delay reduction requires timelock and per-epoch refill
  bounds from the active policy;
- policy-version rollback is a hard failure unless a separately proven-safe
  successor path is present in the fixture.

## Recovery transitions

P4 binds the unchanged P3 `RecoveryPathProfileV1::statebook_externalization_v1`
fourteen-path inventory. Fixtures may not rename, add, or remove path ids.

Recovery transitions cover, as local deterministic model steps only:

- all-path halt inventory;
- read-only continuity;
- reconciliation of in-flight items;
- stale snapshot detection;
- canary reopen stages;
- restored-cap ramp under the active policy.

A pause observation alone remains incomplete. Reconciliation mismatch, evidence
loss, duplicate liability, or failed canary remains failed. Local recovery
drills create no production-readiness claim.

## Composition with seven completeness reports

When financial basis is contract-derived, the kernel consumes the P3
`AnalysisSubjectV1` and seven-report composition digests. It must not:

- reconstruct a `ValidatedContract` or `StateKeyV1`;
- rerun P2 payoff evaluation;
- promote, demote, or aggregate the seven dimension statuses;
- invent missing completeness evidence;
- treat fixture-qualified P3 statuses as live recognition, finality, or
  authority.

Missing, stale, or mismatched completeness digests fail gate 9.

## Canonical identity

P4 identities use domain-separated tagged length-delimited binary encodings and
SHA-256. JSON or Serde rendering hashes are forbidden for identity.

Required new digest families include at least:

```text
intent_digest = H(canonical_encode(
  domain_tag, schema_version, subject, source_account, destination, route,
  asset, direction, total_amount, StateKey_or_financial_basis,
  originating_transition, linked_plan_or_obligation_digest,
  action_authorization_digest, declared_release_class, nonce,
  requested_at, expires_at
))

decision_context_digest = H(canonical_encode(
  intent_digest, evidence_snapshot_digest, valuation_profile_digest,
  policy_digest, evaluated_at
))

release_attempt_digest = H(canonical_encode(
  release_part_id, decision_context_digest, reservation_id
))
```

Same parent intent id with a different immutable intent digest rejects. Fresh
evidence, valuation, or policy creates a new decision context and attempt. At
most one live or submitted attempt may exist per release part. An
implementation-diverse second SHA-256 encoder must reproduce frozen golden
vectors for every new public digest family.

Frozen P1 and P2 identities remain byte-identical:

- P1 701-byte preimage and StateKey
  `f1662f3fb5a10c074680c0baf76ba488b7230337456358be92f3127d8a632c08`;
- P1 validated-contract digest
  `7634410968adb9b56c62f213de7956796f9f3f62b102d4f6efe7f45d86858788`;
- P2 domain digest
  `67cb8e1807cd3e619f73d569f70de494ef60610f4d44acea236b0ee006e45e6a`.

All P3 subject, fixture, report, capital-context, recovery-profile, and
composition digests remain unchanged.

## Closed synthetic inputs

All inputs are hermetic fixtures with strict unknown-field rejection, duplicate
JSON key rejection, exact rational decimal strings, lowercase 64-hex digests,
and nonempty bounded ASCII identifiers. Financial amounts accept no JSON
numbers and no floating point.

Allowed synthetic categories:

- `ExternalizationRequest` and nested linked-plan or obligation objects;
- `CurrentAssuranceSet` and evidence snapshots;
- `ConservativeValuationProfile`;
- `ExposureBudget` and `AssuranceTierPolicy`;
- `BudgetLedgerState`;
- challenges, breaker actions, and recovery observations;
- injected clock, seed, and schedule;
- unchanged public P1, P2, and P3 opaque reports.

Forbidden inputs:

- live or captured venue terms or books;
- HSAI claim envelopes or admission candidates;
- network, credentials, process spawn, or filesystem writes outside bounded
  report tests;
- media, tweets, or memes as assurance evidence;
- caller-supplied recovery path sets;
- empirically claimed production-calibrated caps, ratios, or delays.

## Resource bounds

Future implementation must freeze exact resource ceilings for request size,
leg count, budget axes, journal entries, queue depth, challenge count, breaker
scopes, and evidence snapshot size. Every exact limit must succeed and every
limit-plus-one must reject. Until implementation freezes numbers, the boundary
requires fail-closed bounded collections and a gross document ceiling no larger
than the existing P3 one-mebibyte fixture document cap.

## Frozen scenarios

The future implementation must cover at least:

1. one fully populated hermetic decision with all five outcomes reachable under
   distinct fixtures and no aggregate trust score;
2. every hard gate fail and unknown path yields zero instant release;
3. amount rejection before valuation for zero, negative, overflow, and
   noncanonical encodings;
4. stale, missing, and conflicting valuation profiles reject;
5. atomic linked plan all-or-none reservation and inbound non-offset;
6. risk-reducing obligation exact-amount and exposure-decrease checks;
7. pending or anomalous PnL blocked from reuse, borrow, collateral, and
   release-budget credit;
8. request splitting cannot expand aggregate caps;
9. exactly one CAS success under contended expected ledger tips;
10. timer passage alone never releases a queued part;
11. fresh revalidation after challenge window creates a new decision context;
12. cancel and destination replacement require a new intent digest;
13. challenge valid, invalid, duplicate, censored, and unavailable variants;
14. evidence expiry while queued enters `RevalidationRequired` or equivalent
    fail-closed state;
15. breaker edges including no direct `Halted -> Normal`, TTL exhaustion into
    `Resolution`, and malicious renewal rejection;
16. fast tighten and slow relax hysteresis, including rollback rejection;
17. destination finality consumes in-flight without restoring capacity;
18. `ProvenNoOutflow` returns capacity only with validated evidence;
19. recovery halt, reconciliation mismatch, canary failure, and reopen stages;
20. prepared-later oracle report reuse when timestamp later matches;
21. stale data with fresh transport timestamp;
22. two reports derived from one compromised upstream source;
23. artificial profit with immediate payout request;
24. valid liquidation whose external payout is frozen while risk-state model
    update remains separately classified;
25. large request split across agents, destinations, assets, and blocks;
26. policy downgrade immediately before release;
27. anomaly after instant-part release but before queued-part release;
28. false risk-reducing label and general withdrawable destination credit;
29. transferable receipt or loan attempting to monetize queued value;
30. slow drain below per-transaction limits but above aggregate budget;
31. concurrent finalizers racing every cap and failed-transfer reservation
    rollback;
32. action-oracle conflicting with independent budget-valuation roots;
33. solvent and insolvent venues with identical queue data remain distinct;
34. AI or model confidence cannot bypass a failed hard gate;
35. unchanged P1, P2, and P3 golden digests and public report bytes;
36. independent test encoding reproduces every new P4 golden digest;
37. source and serialized-output scans reject network, process, filesystem
    write, unsafe code, floating-point financial arithmetic, credentials,
    HSAI, admission, `zkbench`, scalar trust score, transfer command, and
    runtime authority surfaces.

Named frozen adversarial fixtures may encode the broader PRD TD-004 corpus and
integration Stage-4 scenario list. Full multi-policy sweep minimization APIs
are out of scope for this slice; deterministic replay of the frozen corpus is
required.

## Authorized future implementation paths

The future implementation may change only:

- additive Rust modules and tests under `crates/statebook-settlement/`;
- additive hermetic JSON fixtures under
  `crates/statebook-settlement/tests/fixtures/`;
- resulting `Cargo.lock` dependency records only if an already-allowed
  hermetic test dependency requires it;
- new
  `docs/statebook-p4-settlement-simulator-implementation-notes.md`;
- `README.md`;
- `AGENTS.md`;
- `docs/12-task-list.md`;
- `docs/90-whole-codebase-validation-report.md`.

No `statebook-core` mutation, new workspace crate, HSAI, admission,
`zkbench-core`, tool, script, publication PDF, whitepaper, PRD, source-index,
media, or external adapter path is authorized.

## Acceptance gates

- no P1, P2, or P3 source, fixture, canonical bytes, digest, status, or public
  API behavior changes;
- kernel outcomes remain the closed five-way enum with typed reasons;
- every hard-gate fail or unknown path yields zero instant release;
- decision records remain non-authoritative and contain no transfer command;
- exact arithmetic and valuation fail closed without partial numeric output;
- queue timer passage alone never releases;
- breaker graph forbids `Halted -> Normal`;
- all frozen scenarios and resource bounds pass;
- an implementation-diverse encoder reproduces all new golden digests;
- focused format, tests, and warning-denied Clippy pass for
  `statebook-settlement`;
- unchanged `statebook-core` tests and Clippy pass;
- repository documentation and hygiene tests pass;
- clean-tree workspace tests run;
- clean-tree workspace Clippy findings outside P4 are reported, not absorbed;
- independent scope/claim-boundary and kernel/digest/arithmetic reviews
  complete.

## Nonclaims

P4 creates no live order, fill, routing, optimization, custody, signing, pause
action, withdrawal, transfer, bridge, margin award, clearing recognition, legal
finality, asset control, oracle truth, venue solvency, empirical calibration of
caps or ratios, scalar trust score, release-safety probability, HSAI evidence,
admission decision, P5 portable bundle, P6 external source, P7 authority
integration, accepted Evidence Ledger mutation, benchmark evidence, proof,
semantic-correctness claim, production readiness, SOTA, independent audit, or
full-security claim. A simulated `Immediate` or `Queued` decision is local
hermetic regression evidence only and never moves value.
