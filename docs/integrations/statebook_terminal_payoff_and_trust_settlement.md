# Statebook Terminal-Payoff and Assurance-Adjusted Settlement Boundary

## Status And State Slice

Status: `DocumentationOnly`; documentation-first integration boundary complete.
Evidence ceiling: `Level0DesignNote`.

Named state slice:
`statebook-terminal-payoff-and-assurance-adjusted-settlement-boundary`.

The declared Statebook state slice spans exactly:

- this integration specification;
- the integration link in `README.md`;
- the explicit authorization and nonclaim in `AGENTS.md`;
- the bounded task record in `docs/12-task-list.md`;
- the validation record in `docs/90-whole-codebase-validation-report.md`.

This slice adds no Rust, Python, Cargo metadata, fixture, executable adapter,
network access, venue connection, oracle, router, order placement, margin
calculation, asset custody, settlement mechanism, circuit breaker, benchmark
result, accepted Evidence Ledger entry, or action authority. It is Level 0
design work. Every pseudo-type, formula, policy, scenario, and time horizon in
this document is a future contract or analytical hypothesis, not implemented
behavior.

The drafting baseline was repository commit
`a05fc73041ccd87c2f83a9f07da7b552c9a06a17`. That independently committed
predecessor contains Phase 796-A3L5 and is outside this Statebook state slice.
The pre-existing user-owned edit
to `crates/hsai-agent-admission/src/lib.rs` is outside this state slice and is
bound at SHA-256
`41530d449871484b7c0f15869bab9c892c328d6ab982b166bad3223147f173de`
and Git object id `a4feb2f54ca90c3b52789b2dcb0d40af5bbe096a`. This work must not edit,
format, stage, or commit that file.

During closing validation, separately owned and concurrently mutable A3L6 work
began materializing under the five paths authorized by the committed A3L5
boundary: `p01b_container_probe.py`, `p01b_container_evidence.py`,
`p01b_container_execution.py`, `p01b_container_execution_tests.py`, and
`p01b_container_evidence_tests.py` under `tools/hsai-formal-preflight/`. Those
paths are outside this state slice. This Statebook work must not edit, format,
stage, commit, claim stable identity for, or claim validation of them.
A generated untracked Python bytecode cache also appeared beside that
concurrent work. It is outside this state slice and was neither removed nor
validated by the Statebook work.

## Decision

The Statebook concept is relevant to this repository, but it belongs above the
existing HSAI assurance and admission substrate rather than inside the current
claim-envelope algebra.

The retained architecture has two separate semantic systems:

1. A financial contract algebra describes when instruments pay, how portfolios
   combine, and what residual economic exposure remains.
2. The HSAI evidence algebra describes what was observed, which assumptions
   remain open, which trust roots were used, how mature the evidence is, and
   whether an action proposal may advance to a separately owned authority
   boundary.

They may be joined by typed references. They must not be conflated.
`hsai_claim_envelope::conjoin` composes evidence claims; it does not net cashflows,
create collateral offsets, or prove that two contracts are economically
equivalent. `Maturity::Attested` is an assurance level; it is not a financial
contract maturity. The HSAI economy and membrane are bounded in-memory protocol
models; they are not exchange margin, custody, or settlement systems.

The future join key is the canonical financial terms digest carried by
`TerminalContractIR.contract_ref.terms_digest`. A settlement request may refer
to that digest and to separate evidence digests. Evidence must not rewrite the
economic terms, and economic normalization must not manufacture evidence.

The security decision is equally specific:

```text
Preserve immediate market-state updates and risk-reducing execution.
Preserve atomic DvP or PvP only when every linked leg is validated, prefunded,
unencumbered, hard-gated, capped, and conditional.
Do not make large, unconditional, irreversible external release instant by
default.
Determine external release from current evidence, hard safety gates, and a
bounded loss budget, not from reputation or a single aggregate trust score.
```

The useful ratio is therefore not "how much do we trust this actor?" It is:

```text
instant_externalization_ratio =
    immediately_externalized_amount / requested_externalization_amount
```

That ratio is an output of policy. It is never itself evidence.

The policy decomposition is deliberate: hard gates answer whether instant
externalization is admissible; current assurance tier and loss budgets bound how
much; the maximum-of-risks delay determines when the remainder may be reviewed;
and the queue state machine determines how evidence expiry, challenge, failure,
or resolution changes the request. Higher assurance can reduce friction inside
that envelope. It can never purchase an exception to a failed gate or an
exhausted loss budget.

## Why A Statebook

An orderbook organizes bids and offers for one contract. A frontier-risk market
increasingly contains several payoff forms over the same underlying state:

- a binary event claim;
- a threshold or range claim;
- an option or option spread;
- a dated future;
- a perpetual exposure with funding and liquidation rules;
- a compute, power, weather, freight, carbon, insurance, or operational-risk
  contract;
- a structured portfolio made from several of the above.

Putting those products on one screen does not make them one market. Instruments
that mention the same headline variable can differ in observation source,
sampling window, timezone, comparator, rounding, disruption rule, dispute
process, collateral, currency, legal finality, or default treatment. Those
differences can dominate the apparent hedge.

A Statebook is a coherence layer that groups contracts by the states and paths
under which they pay. Its minimum job is to answer five independent questions:

1. Semantic coherence: do the contracts refer to the same economic state under
   compatible observation and settlement rules?
2. Product span: do listed payoffs span the target exposure within a declared
   residual tolerance?
3. Execution completeness: can the proposed portfolio be filled at bounded
   size, price, time, and failure assumptions?
4. Settlement completeness: are the resulting obligations legally and
   operationally capable of final settlement?
5. Capital completeness: will the relevant venue, clearer, custodian, lender,
   or risk engine recognize the offset before margin and liquidation are
   calculated?

Passing one test must not be reported as passing another. A perfect terminal
replication that cannot be filled is not an executable hedge. An executable
cross-venue hedge that receives no collateral offset is not capital-complete.
An onchain atomic fill is not legal equivalence across jurisdictions.

### What the AWS analogy gets right and wrong

The useful part of the AWS analogy is not one dominant brand. It is the move
from bespoke capital infrastructure to metered, programmable primitives with a
stable control surface. A financial substrate similarly needs reusable contract
identity, execution, collateral, risk, clearing, settlement, observability, and
policy interfaces so that a new risk does not require a new vertically
integrated exchange.

The analogy breaks where finance carries entitlement, law, default, and
adversarial value transfer. Compute cycles are operational resources; financial
positions are claims whose meaning can change with benchmark governance,
jurisdiction, insolvency, custody, and finality. A common API cannot erase those
differences. It must preserve them as typed state.

That yields a federated stack rather than one universal venue:

```text
Statebook semantic control plane
  -> contract identity, payoff relations, residuals, completeness
HSAI assurance and admission plane
  -> evidence, assumptions, current policy, proposal-only admission
Venue and clearing data planes
  -> books, fills, netting, margin, default management
Separately owned authority planes
  -> signing, custody, settlement, legal finality
```

The Statebook can make isolated books economically legible to one another. It
cannot manufacture liquidity, legal portability, collateral recognition, or
settlement authority. That separation is the central fit with this repository:
HSAI can harden the evidence-to-proposal boundary while the Statebook defines
what financial state the proposal is actually about.

### Current convergence signals

Several venue directions make the separation concrete as of July 2026:

- Hyperliquid documents alpha portfolio margin that unifies eligible spot and
  perpetual positions under one account while retaining explicit asset, user,
  borrow, supply, and fallback caps. This is movement toward capital coherence
  inside one venue, not proof of cross-venue equivalence.
- Kalshi documents a CFTC-cleared BTC perpetual with its own index, funding,
  margin, clearing, and settlement-cycle terms. A venue associated with event
  contracts can add a perpetual payoff form without making those forms
  interchangeable.
- Architect describes intended cash-settled compute futures and options but
  explicitly says the products remain subject to regulatory review. This is a
  credible direction of travel, not evidence of a mature compute market.
- CME SPAN demonstrates why capital completeness is an institutional risk-model
  decision: portfolio scenarios can inform performance-bond requirements, but
  listing related contracts elsewhere does not make that recognition portable.

The Statebook therefore should not compete with each venue's execution engine or
declare collateral offsets. It should make terms, payoff relations, residuals,
evidence, and missing recognition legible across them.

## Incident-Grounded Security Lesson

### Evidence available on 15 July 2026

Ostium publicly confirmed an issue involving the OLP vault, paused trading, and
said the team was investigating. A later update said trader funds and open
positions were frozen or preserved during the investigation. No final Ostium
postmortem or final loss accounting was available when this boundary was
written.

Blockaid's preliminary public attribution states that an attacker used a
registered `PriceUpKeep` forwarder and what Blockaid called future-dated
authorized oracle reports to create artificial trading profit and trigger an
estimated roughly USD 18 million USDC vault payout. That phrase does not mean
the inspected router accepted a timestamp that was still in the future. The
observed order timestamps equal the block timestamp, and the pinned public
router rejects `timestamp > block.timestamp`. A report prepared earlier for a
later timestamp and consumed when that timestamp arrived is consistent with the
observations; the preparation time is not independently established here. This
is an investigator's preliminary attribution, not an accepted final root cause.
A cited exploit transaction shows only part of the estimated aggregate
movement, so this document does not treat the USD 18 million number as final
transaction-level accounting.

Independent read-only inspection of the cited Arbitrum receipt found ten
`PriceRequestedV2` and ten `PriceReceived` events in one successful transaction.
The requested order types alternate five times between `MARKET_OPEN` and
`MARKET_CLOSE`; every request carries block timestamp `1784125128` (15 July
2026 14:18:48 UTC) and the same feed identifier, while the received prices
alternate between 5,000 and 60,000 in the contract's 18-decimal scale. The same
receipt contains five `MarketOpenExecuted` and five `MarketCloseExecutedV2`
events. The five open events name the same trader, and each close `tradeId`
matches the preceding open `orderId`; the matching close-initiation events also
name that trader. This is primary chain evidence of five completed
same-transaction round trips. It does not establish how the authorized reports
were obtained or who was compromised.

The pinned public `OstiumVerifier` recovers a signer from signed report data and
checks that the signer is authorized. The pinned public
`OstiumPrivatePriceUpKeep` then checks the decoded report feed and timestamp
against the stored order, but the signed report payload shown in that source does
not contain the order id or an order-specific nonce. Therefore, reports sharing
the accepted feed and timestamp are not visibly order-bound in the inspected
source. This source-level observation is narrower than a final exploit root-cause
claim, but it directly motivates action-bound evidence, one-time consumption,
equivocation checks, and pre-externalization PnL velocity limits.

Because the five alternating cycles completed inside one transaction,
post-transaction monitoring alone could not intervene between them. A relevant
control must synchronously keep abnormal or newly created profit provisional,
give it zero collateral, borrowing, transfer, margin-reuse, or release-budget
value, and place its external payout behind a gate that can be challenged after
the transaction. Only independently verified prefunding may support a separate
obligation, and any resulting externalization still consumes every applicable
cap.

Two public Ostium design facts matter independently of the preliminary root
cause:

- Ostium's documented LP withdrawal flow already imposed a fixed 24 to 48 hour,
  two-settlement delay.
- The public contract source at commit
  `8390ce497f68fb128900840e0ec30683afa945d3` routed profitable close PnL from the
  vault to the trader through `executeUnregisterTrade`, `vault.sendAssets`, and
  an immediate token transfer path.

The narrow inference is strong: delaying only LP redemption cannot contain an
attack that exits through trader-profit realization. A settlement control must
cover every route by which disputed or anomalous accounting becomes an
externally transferable asset, including profit payout, collateral withdrawal,
bridge transfer, redemption, borrow-against-credit, and administrative rescue
paths.

This document does not claim that a delay would have prevented the Ostium
incident. Prevention would require the delay controller, monitoring, challenge
logic, and pause authority to remain uncompromised and to detect the anomaly
before release.

### What "instant settlement" hides

The phrase combines distinct operations with different risk effects:

- Trade execution forms a position or matches intent.
- Internal risk-state transition updates balances, PnL, margin, funding, and
  liquidation state.
- Clearing calculates net obligations and collateral requirements.
- Conditional exchange-of-value settlement delivers all verified linked legs or
  none of them.
- Externalization makes an asset irreversibly usable outside the venue's
  recovery domain.
- Legal finality determines when an obligation cannot be unwound under the
  applicable rules and law.

Slowing all six is not a coherent security policy. Delayed liquidations can
increase losses. Delayed margin updates can hide insolvency. Replacing atomic
delivery-versus-payment with asynchronous legs can reintroduce principal risk.
The control target is unconditional externalization of value whose provenance,
calculation, authorization, solvency support, or destination is not sufficiently
current and bounded.

## Terminal Contract IR Boundary

The first future Statebook slice should be terminal, scalar, cash-settled, and
synthetic. It should not begin with perpetuals, live venue adapters, or capital
netting.

### Proposed pseudo-types

```text
struct SourceContractRef {
  venue_namespace: String,
  source_contract_id: String,
  terms_digest: Hash,
  observed_at: Timestamp,
  source_revision: String,
}

struct EconomicReference {
  namespace: String,
  identifier: String,
  unit: String,
  benchmark_administrator: Option<String>,
  methodology_version: String,
  methodology_digest: Hash,
  fallback_rule: FallbackRule,
  market_calendar: CalendarRef,
  timezone: Timezone,
}

struct TerminalObservation {
  reference: EconomicReference,
  observation_start: Timestamp,
  observation_end: Timestamp,
  sampling_rule: SamplingRule,
  disruption_rule: DisruptionRule,
  correction_rule: CorrectionRule,
}

enum Comparator {
  LessThan(Rational),
  LessThanOrEqual(Rational),
  Equal(Rational),
  GreaterThanOrEqual(Rational),
  GreaterThan(Rational),
  InRange { lower: Rational, upper: Rational, endpoints: EndpointRule },
}

enum TerminalPayoff {
  Fixed { amount: Rational },
  Indicator { comparator: Comparator, amount: Rational },
  Linear { slope: Rational, intercept: Rational },
  PiecewiseLinear { knots: Vec<PayoffKnot> },
}

struct SettlementProfile {
  asset: AssetId,
  unit_scale: Rational,
  rounding: RoundingRule,
  settlement_deadline: Timestamp,
  finality_domain: String,
  dispute_rule: DisputeRule,
  default_rule: DefaultRule,
  governing_rule_ref: Option<String>,
}

struct TerminalContractIR {
  contract_ref: SourceContractRef,
  observation: TerminalObservation,
  payoff: TerminalPayoff,
  settlement: SettlementProfile,
  explicit_non_equivalences: BTreeSet<NonEquivalence>,
}
```

The source terms digest must bind the original terms from which the IR was
lowered. Normalization without source identity creates an unreviewable
translation boundary.

The future IR should map to established financial-domain standards where their
semantics fit. FINOS Common Domain Model already represents product economic
terms, observables, payouts, settlement, collateral, and lifecycle provisions.
Statebook should specialize in cross-payoff state coherence, residual reporting,
and evidence-bound admission rather than silently invent a replacement standard.

### State identity

A terminal Statebook key must include more than an asset ticker:

```text
StateKey = hash(
  reference namespace and identifier,
  unit,
  benchmark administrator, methodology version and digest, and fallback rule,
  calendar and timezone,
  observation window and sampling rule,
  disruption and correction rules,
  settlement asset and scale,
  rounding, settlement deadline, dispute, default, governing-rule reference,
  and finality domains
)
```

Contracts with different keys may still be related. They are not exactly
equivalent by construction.

### Payoff and residual algebra

Let an admissible world state be `omega`, a path up to time `t` be `p`, and the
cashflow functional of contract `i` be:

```text
C_i(omega, p, t, currency, legal_state)
```

For target exposure `G` and quantities `q_i`, the residual is:

```text
R = G - sum_i(q_i * C_i)
```

Exact replication requires `R = 0` for every admissible state, path, payment
time, currency-conversion state, disruption state, and legally relevant default
state declared by the model. Point estimates or historical correlation do not
establish exact replication.

Approximate replication must report at least:

- the state domain over which residuals were evaluated;
- worst-case and scenario residuals;
- model, basis, jump, timing, FX, default, legal, and liquidity residuals;
- quantity, price, and fill assumptions;
- the source and time of every market observation;
- unsupported states rather than silently extrapolating them.

### Perpetuals remain a separate path-dependent profile

A perpetual is not a terminal claim with a missing expiry. Its cashflows depend
on funding, mark construction, liquidation, collateral changes, position
management, oracle availability, market pauses, and exit timing. A future
`PathDependentContractIR` may model those terms, but this terminal boundary must
not imply that a perpetual and a strip of terminal claims are exactly equivalent.
The perpetual can be a continuing hedge beside terminal claims only after its
path and operational residuals are explicit.

### Completeness must be typed

```text
struct CoherenceResult {
  status: Exact | Related | Incompatible | Unknown,
  residual_classes: BTreeSet<ResidualClass>,
  evidence_refs: BTreeSet<EvidenceRef>,
}

struct ProductSpanResult {
  status: Exact | Approximate | Incomplete | Unknown,
  residual_spec: ResidualSpec,
}

struct ExecutionCompletenessResult {
  status: Executable | PartiallyExecutable | NotExecutable | NotObserved,
  size_bound: Amount,
  price_bound: Amount,
  time_bound: Duration,
  leg_failure_model: LegFailureModel,
}

struct SettlementCompletenessResult {
  status: Final | Conditional | Pending | Disputed | Unsupported | Unknown,
  finality_domain: String,
  evidence_refs: BTreeSet<EvidenceRef>,
}

struct CapitalCompletenessResult {
  status: Recognized | PartiallyRecognized | NotRecognized | NotEvaluated,
  authority_ref: Option<String>,
  haircut_and_margin_ref: Option<String>,
}
```

No aggregate `complete=true` field is allowed. The weakest named dimension must
remain visible.

The publication continuation in `docs/statebook-whitepaper.md` further splits
semantic coherence from payoff span and adds assurance completeness and recovery
completeness. The resulting seven-verdict view does not change this terminal IR
or turn the later security dimensions into financial payoff properties. Recovery
passes only when every externalization path can stop, in-flight obligations can
be reconciled, evidence and liabilities can be restored without duplication,
and reopening is staged; a pause switch alone is insufficient.

## Assurance-Adjusted Settlement Policy

### Assurance, not trust

Trust is socially useful but technically ambiguous. A policy should consume
named, current evidence about a proposed release, not a scalar judgment about a
person or institution.

A scalar trust score is rejected for five reasons:

1. It hides which critical assurance lane is weak or absent.
2. Correlated evidence sources can be double-counted as independent support.
3. A compromised high-reputation key can receive the largest and fastest exit.
4. Model weights and thresholds become a hidden governance surface.
5. Reputation can persist after current authorization, solvency, or system state
   has changed.

Reputation may reduce friction only within a hard current-state envelope. It
must never bypass a failed oracle, authorization, solvency, state-integrity,
replay, destination, or system-loss gate.

### Alternatives tested and rejected

The design comparison retained none of these as the governing policy:

- Universal fixed delay: simple and legible, but it targets the wrong path when
  profit, collateral, bridge, or administrative payout bypasses the delayed LP
  redemption route. It also slows atomic linked exchange and risk-reducing exits
  that may lower rather than raise loss.
- Continuous weighted trust score: operationally convenient, but allows strong
  identity or reputation to numerically compensate for failed oracle,
  calculation, solvency, or finality evidence. It hides correlated roots and
  turns model weights into financial authority.
- Reputation-only release tiers: easier to explain than a continuous score, but
  a compromised established account receives more extraction capacity exactly
  when current evidence should dominate history.
- Monitor after immediate transfer: useful for forensics, sanctions response,
  and future policy, but unable to stop same-transaction recycling or an
  irreversible first transfer.
- Freeze every operation during uncertainty: contains some outflow, but can
  suppress margin additions, liquidations, hedges, and loss recognition,
  converting a bounded incident into a wider solvency event.

The retained policy uses hard current-state gates, discrete named assurance
tiers only after those gates, simultaneous aggregate caps, and challengeable
externalization. This is the smallest design that preserves the distinct risk
effects of execution, clearing, linked settlement, and unilateral release.

### Proposed inputs

```text
enum EconomicReason {
  Profit,
  Collateral,
  Redemption,
  Transfer,
  ContractBackedBorrow,
  Other,
}

enum FinancialBasis {
  NoneForPlainTransfer,
  ContractDerived {
    terms_digest: Hash,
    state_key: StateKey,
    coherence_report_digest: Hash,
    settlement_completeness_digest: Hash,
  },
}

struct ExternalRiskReducingObligation {
  obligation_digest: Hash,
  fixed_beneficiary: DestinationRef,
  restricted_obligation_account: AccountRef,
  asset: AssetId,
  amount: Amount,
  deadline: Timestamp,
  valid_until: Timestamp,
  prefunding_and_segregation_ref: AssuranceRef,
  destination_use_restriction_ref: AssuranceRef,
  destination_finality_policy_ref: AssuranceRef,
  exposure_before_digest: Hash,
  exposure_after_digest: Hash,
  independent_risk_reduction_ref: AssuranceRef,
}

enum LinkedLegDirection {
  OutboundFromRecoveryDomain,
  InboundToRecoveryDomain,
}

struct AtomicLinkedLeg {
  leg_id: String,
  direction: LinkedLegDirection,
  source: AccountRef,
  destination: DestinationRef,
  route_or_bridge: Option<RouteRef>,
  asset: AssetId,
  amount: Amount,
  financial_basis: FinancialBasis,
  budget_axis_refs: BTreeSet<BudgetAxisRef>,
  current_assurance: CurrentAssuranceSet,
  entitlement_ref: AssuranceRef,
  prefunding_and_unencumbered_ref: AssuranceRef,
  finality_ref: AssuranceRef,
}

struct AtomicLinkedExchangePlan {
  exchange_digest: Hash,
  canonical_leg_set_digest: Hash,
  primary_outbound_leg_id: String,
  legs: Vec<AtomicLinkedLeg>,
  atomicity_ref: AssuranceRef,
  exactly_once_ref: AssuranceRef,
  timeout_and_unwind_rule: LinkedUnwindRule,
}

struct ExternalizationRequest {
  request_id: RequestId,
  subject: SubjectId,
  source_account: AccountRef,
  destination: DestinationRef,
  route_or_bridge: Option<RouteRef>,
  asset: AssetId,
  amount: Amount,
  economic_reason: EconomicReason,
  originating_state_transition: Hash,
  financial_basis: FinancialBasis,
  atomic_exchange_plan: Option<AtomicLinkedExchangePlan>,
  risk_reducing_obligation: Option<ExternalRiskReducingObligation>,
  requested_at: Timestamp,
}

struct CurrentAssuranceSet {
  authorization: AssuranceRef,
  source_data_integrity: AssuranceRef,
  calculation_integrity: AssuranceRef,
  state_transition_integrity: AssuranceRef,
  solvency_and_reserves: AssuranceRef,
  destination_integrity: AssuranceRef,
  replay_state: AssuranceRef,
  anomaly_state: AssuranceRef,
  policy_version: PolicyRef,
  trust_root_independence: IndependenceReport,
}

struct BudgetValue {
  atoms: u128,
  scale: u32,
  numeraire: AssetId,
}

struct ValuationObservation {
  asset: AssetId,
  numeraire: AssetId,
  numeraire_atoms_per_asset_unit: Rational,
  source_root: TrustRootRef,
  observation_ref: EvidenceRef,
  observed_at: Timestamp,
}

struct ConservativeValuationProfile {
  profile_digest: Hash,
  numeraire: AssetId,
  observation_set_digest: Hash,
  observations: Vec<ValuationObservation>,
  independent_source_roots: BTreeSet<TrustRootRef>,
  independence_report: IndependenceReport,
  observed_at: Timestamp,
  max_age: Duration,
  aggregation_rule: PolicyDefinedConservativeUpperBound,
  upper_value_stress_multiplier: Rational,
  conflict_or_failure: Reject,
}

struct ExposureBudget {
  request_asset_native_cap: Amount,
  class_rolling_caps: BTreeMap<ReleaseClass, BudgetValue>,
  subject_rolling_cap: BudgetValue,
  destination_rolling_cap: BudgetValue,
  asset_rolling_cap: Amount,
  state_key_rolling_cap: BudgetValue,
  oracle_root_rolling_cap: BudgetValue,
  route_or_bridge_rolling_cap: BudgetValue,
  correlated_dependency_rolling_cap: BudgetValue,
  venue_rolling_cap: BudgetValue,
  system_loss_budget: BudgetValue,
  stress_loss_multiplier: Rational,
}

struct AssuranceTierPolicy {
  policy_version: PolicyRef,
  policy_digest: Hash,
  tier_caps: BTreeMap<AssuranceTier, BudgetValue>,
  minimum_upgrade_dwell: Duration,
  required_clean_epochs: u32,
  relaxation_timelock: Duration,
  refill_epoch_origin: Timestamp,
  refill_epoch_duration: Duration,
  loss_budget_lookback: Duration,
  maximum_common_refill_by_axis: BTreeMap<BudgetAxis, BudgetValue>,
  maximum_native_refill_by_axis: BTreeMap<NativeBudgetAxis, Amount>,
}

struct BudgetCounter {
  limit: BudgetValue,
  consumed: BudgetValue,
  live_reservations: BudgetValue,
  in_flight: BudgetValue,
}

struct NativeBudgetValue {
  asset: AssetId,
  amount: Amount,
}

struct NativeBudgetCounter {
  asset: AssetId,
  limit: Amount,
  consumed: Amount,
  live_reservations: Amount,
  in_flight: Amount,
}

struct ConsumedReleaseEntry {
  release_id: ReleaseId,
  released_at: Timestamp,
  unrefilled_common_debits_by_axis: BTreeMap<BudgetAxis, BudgetValue>,
  unrefilled_native_debits_by_axis: BTreeMap<NativeBudgetAxis, NativeBudgetValue>,
  finality_state: Final | InFlight | FailedUnknown,
  reconciliation_ref: Option<AssuranceRef>,
  correlated_exposure_closed_ref: Option<AssuranceRef>,
}

struct BudgetLedgerState {
  policy_digest: Hash,
  valuation_profile_digest: Hash,
  window_start: Timestamp,
  window_end: Timestamp,
  refill_epoch_index: u64,
  counters_by_axis: BTreeMap<BudgetAxis, BudgetCounter>,
  native_counters_by_asset_axis: BTreeMap<NativeBudgetAxis, NativeBudgetCounter>,
  consumed_release_journal: Vec<ConsumedReleaseEntry>,
  reservation_ids: BTreeSet<ReservationId>,
  in_flight_release_ids: BTreeSet<ReleaseId>,
  reconciled_through: Timestamp,
  ledger_tip: Hash,
}
```

Every assurance reference needs an issuer or verifier identity, observation
time, validity window, provenance digest, assumptions, excludes, and revocation
or supersession state. Missing evidence is not neutral evidence.

`BudgetValue` is the only type used to compare or aggregate different assets.
Every cross-asset budget in one decision must use the same numeraire and scale.
The valuation profile must compute a conservative upper bound on the outflow's
value from roots independent of the source used to create or mark the action.
Stale, missing, unsupported, internally conflicting, or insufficiently
independent conversion evidence rejects instant release. It never falls back to
the potentially compromised action price. Asset-native caps remain separate,
and conversion from an allowed numeraire value back to an asset amount rounds
down so the conservative value cannot exceed the allowed budget.

Every valuation observation binds asset, numeraire, exact rational rate, source,
evidence, and time. The profile digest binds the observation set, aggregation
rule, freshness bound, stress multiplier, and independence report. The policy's
conservative upper-bound rule is deterministic; implementations cannot choose a
friendlier quote after seeing the request.

`FinancialBasis::ContractDerived` is mandatory for profit, redemption, and
contract-backed borrowing, and for collateral whose value derives from a
financial contract. `NoneForPlainTransfer` is permitted only when no financial
contract supplies the entitlement. It cannot be used to relabel contract PnL.

An `AtomicLinkedExchangePlan` is structurally valid only with at least two
nonzero legs, at least one inbound and one outbound leg, unique leg ids, no
duplicate economic legs, and an existing primary outbound leg whose asset,
amount, destination, route, and financial basis exactly match the enclosing
request. Every leg carries current assurance and the complete policy-derived set
of budget axes; missing or extra assurance or axis references reject it.
Canonically sorted complete leg bytes determine `canonical_leg_set_digest`,
which in turn is bound by `exchange_digest` with the atomicity, exactly-once,
timeout, and unwind terms. Missing, extra, duplicate, zero, or digest-mismatched
legs reject the plan. No implementation may discover an undeclared leg after
admission.

### Release classes

The policy first classifies the transfer:

- `InternalRiskState`: bookkeeping, mark, margin, funding, collateral lock, or
  liquidation state that remains inside the recovery domain. It should normally
  update immediately and fail closed if invalid.
- `AtomicLinkedExchange`: all verified legs settle conditionally or none do.
  It may remain immediate only when every leg is prefunded and unencumbered,
  entitlement and provenance are current, solvency remains current, no leg uses
  disputed or pending credit, exactly-once atomic settlement is enforceable,
  each outbound leg consumes its gross applicable native and cross-asset caps,
  and no unilateral extraction remains possible. Inbound legs cannot net or
  replenish those budgets in the same operation. Atomicity reduces linked-leg
  principal risk; it does not prove ownership, price truth, or solvency.
- `ExternalRiskReducingObligation`: a narrowly pre-authorized external payment
  to a fixed clearing, custody, CCP, or venue beneficiary for which independent
  evidence shows that timely payment reduces aggregate exposure and delay
  increases default or contagion risk. It requires an immutable obligation
  digest, asset, amount, beneficiary, and deadline; verified prefunded,
  segregated, and unencumbered resources; no disputed or pending PnL; and a
  dedicated capped expedited lane. Destination evidence must show that the
  funds become non-withdrawable and are applied to the named obligation, with
  a current finality policy capable of completing before the deadline while the
  obligation is still valid. That is ex-ante capability evidence, not proof of a
  future outcome. Post-release finality must be observed before normal
  completion. A credit to a general withdrawable balance is not risk reducing.
  It should use atomic delivery when the receiving domain supports it. It cannot
  classify withdrawals or fabricated profit as risk reducing.
- `ExternalUnconditional`: value leaves the recovery domain without a validated
  linked obligation. It is subject to the instant-release ratio and queue.
- `SystemicOrExceptional`: amount, destination, novelty, concentration, market
  stress, or governance sensitivity exceeds a hard threshold. It receives zero
  instant release and requires a stronger, separately governed path.

Classification itself is fail-closed. Unknown means
`SystemicOrExceptional`, not `InternalRiskState`.

Every class that releases value from the recovery domain, including
`AtomicLinkedExchange` and `ExternalRiskReducingObligation`, must pass every
applicable hard gate, asset-native cap, cross-asset cap, and system loss budget.
The classification changes the permitted timing and obligation structure; it
never creates an uncapped bypass. When classifications conflict, the stricter
class controls.

### Hard gates

Before any ratio is calculated, all applicable critical predicates must pass:

1. The requested action and destination are currently authorized.
2. Source observations are authentic under the declared trust policy, fresh,
   not later than the permitted observation window, monotonic where required,
   one-time consumable, checked for equivocation, and bound to the exact request
   id, order or obligation id, nonce, action, policy, and state transition. A
   report prepared for later consumption must not become reusable merely because
   its timestamp eventually matches the clock.
3. The PnL, collateral, redemption, or transfer calculation recomputes from
   bound inputs under the current policy version.
4. The originating state transition exists once, is internally consistent, and
   cannot be replayed or transplanted.
5. Reserves and liquid resources support the release under normal and declared
   stress conditions.
6. The destination and route pass current allow, novelty, sanctions, bridge,
   and contract-behavior policy where applicable.
7. No critical anomaly, emergency freeze, policy rollback, signer compromise,
   oracle disagreement, or systemic loss-budget exhaustion is active.
8. Independent evidence requirements are satisfied without counting several
   reports derived from the same compromised root as a quorum.
9. A contract-derived profit, redemption, borrowing, or collateral request is
   bound to its canonical terms digest and `StateKey`; the referenced coherence
   and settlement-completeness reports have a policy-acceptable status, expose
   their residuals and finality domain, and are not stale or superseded.
10. Pending anomalous or newly created PnL contributes zero collateral,
    borrowing, transfer, margin-reuse, or release-budget value until finalized.
    Independently verified prefunding remains a separate asset and any release
    against it consumes every applicable budget.
11. An `ExternalRiskReducingObligation` exactly matches the request's asset,
    amount, fixed beneficiary, restricted obligation account, deadline,
    validity interval, and obligation digest; `now <= valid_until`; every
    prefunding, restriction, finality-policy, and risk-reduction reference is
    current;
    independent evidence shows lower aggregate exposure after payment;
    destination evidence proves non-withdrawable application and a mechanism
    capable of finality before the deadline; and the dedicated class budget has
    capacity. Relabeling a withdrawal, general venue credit, or profit does not
    pass. This gate does not claim the future transfer is already final.
12. An `AtomicLinkedExchangePlan` binds every linked asset, amount, direction,
    account, financial basis, complete budget-axis set, entitlement, provenance,
    prefunding, encumbrance, finality, atomicity, unwind, and exactly-once
    condition before any leg can leave the recovery domain. Structural
    validation rejects fewer than two legs, absence of either direction, zero or
    duplicate legs or ids, digest mismatch, an enclosing-request mismatch, and
    any hidden, extra, or axis-incomplete leg. Every outbound leg reserves gross
    caps, resolves to the same active policy version, and independently passes
    every applicable gate above, including authorization, source and calculation
    integrity, state-transition and solvency support, destination novelty and
    integrity, sanctions, route, bridge, contract behavior, finality, anomaly,
    independence, semantic binding, and zero pending-PnL reuse. Inbound legs do
    not create capacity in the same exchange.

Any applicable gate that fails or is unknown sets the instant amount to zero and
routes the request to quarantine or a separately authorized corrective process.
The queue is not permission to release an invalid request after time passes.

### Ratio and cap calculation

For a valid non-atomic request that would externalize asset-native amount `Q`,
calculate named native and common-numeraire caps, not a blended score. For
`ExternalUnconditional`, the result defines the instant ratio. An atomic linked
exchange may execute only when the whole required amount fits; otherwise it
does not partially degrade into two unilateral legs. A risk-reducing obligation
also consumes its dedicated class cap and is all-or-none at its declared amount.
A smaller economically useful tranche must be a separate pre-authorized
obligation with its own amount, digest, and before/after exposure evidence; the
controller never derives a partial tranche. Insufficient capacity rejects the
expedited lane and invokes the predeclared default-resolution path.

```text
active_tier_policy = resolve_active_tier_policy(
  current_assurance.policy_version,
  budget_ledger.policy_digest,
  request.requested_at
)
classified_release_class = classify(request, active_tier_policy)
selected_tier = select_tier(current_assurance, active_tier_policy)
V_Q = conservative_upper_bound_value(Q, asset, valuation_profile)

if any hard gate != Pass or V_Q == Reject:
  instant_amount = 0
else:
  stressed_system_limit = floor_value(
    system_loss_budget / stress_loss_multiplier
  )
  common_value_limit = min(
    V_Q,
    active_tier_policy.tier_caps[selected_tier],
    class_rolling_cap_remaining,
    subject_rolling_cap_remaining,
    destination_rolling_cap_remaining,
    state_key_rolling_cap_remaining,
    oracle_root_rolling_cap_remaining,
    route_or_bridge_rolling_cap_remaining,
    correlated_dependency_rolling_cap_remaining,
    venue_rolling_cap_remaining,
    stressed_system_limit_remaining
  )
  native_value_limit = floor_convert_value_to_native_asset(
    common_value_limit,
    valuation_profile
  )
  candidate_amount = min(
    Q,
    request_asset_native_cap,
    asset_rolling_cap_remaining,
    native_value_limit
  )
  instant_amount = match classified_release_class {
    ExternalUnconditional => candidate_amount,
    ExternalRiskReducingObligation =>
      if candidate_amount == Q then Q else 0,
    SystemicOrExceptional => 0,
  }

instant_externalization_ratio = instant_amount / Q
queued_amount = if classified_release_class == ExternalUnconditional {
  Q - instant_amount
} else {
  0
}
```

`queued_amount` is the ordinary remainder only for `ExternalUnconditional`.
For `ExternalRiskReducingObligation`, a zero all-or-none decision enters the
declared default-resolution path rather than becoming an ordinary withdrawal
queue item.

`AtomicLinkedExchangePlan` uses a separate gross all-leg calculation:

```text
for each outbound leg i:
  V_i = conservative_upper_bound_value(
    leg[i].amount,
    leg[i].asset,
    valuation_profile
  )

gross_common_debit[axis] = sum(
  V_i for each outbound leg whose complete budget_axis_refs include axis
)
gross_native_debit[axis] = sum(
  leg[i].amount for each outbound leg mapped to native axis
)

atomic_release = AllLegs if and only if:
  every structural and every per-leg applicable hard gate passes,
  every V_i succeeds,
  every gross_common_debit[axis] <= common_remaining[axis], and
  every gross_native_debit[axis] <= native_remaining[axis]
otherwise:
  atomic_release = NoLegs
```

Every gross debit is reserved in one compare-and-swap ledger transition before
the all-leg operation. If any axis or leg fails, the transition reserves and
releases nothing. Inbound legs are never subtracted from gross debit and do not
refill capacity in the same operation.

The caps must bind aggregate exposure, not only one transaction. Splitting one
large request across accounts, assets, destinations, blocks, agents, or
correlated venues must not restore the original instant allowance.

The ratio and every conversion must never round up. Zero-amount, mismatched
numeraire, mismatched scale, overflow, and conversion-failure cases fail closed.
All monetary arithmetic should be integer or exact rational arithmetic under a
declared scale. The stress multiplier must be at least one, denominators must be
nonzero, and negative or internally inconsistent capacity rejects the request.

For each common-numeraire or asset-native counter, deterministic remaining
capacity is
`limit - consumed - live_reservations - in_flight`. All applicable counters are
checked and reserved atomically against one versioned ledger tip before release.
A request id and reservation id are exactly-once. An immediately final release
removes the matching reservation and adds it to consumed capacity. A submitted
cross-domain release whose destination finality is not yet observed moves the
same amount from reserved to `in_flight`; observation of finality moves it to
consumed. Timeout or failure may release capacity only with independent proof
that no value left the recovery domain. Otherwise the in-flight exposure stays
counted and enters the predeclared default-resolution path. No failure can
decrement consumed capacity. Concurrent decisions that lose the ledger
compare-and-swap must recompute. Queued requests do not reserve instant capacity
indefinitely: they revalidate and reserve against the then-current ledger only
at finalization.

At each window opening, the system counter's limit is the declared
`stressed_system_limit`; the other counter limits are the exact versioned tier,
class, common-numeraire exposure, and asset-native exposure-budget values. No
implicit or implementation-local cap is permitted.

Refill is a deterministic ledger transition, not a discretionary conclusion.
The same resolved `active_tier_policy` controls release and refill; its digest
must match current assurance and the ledger. Its `refill_epoch_duration` must be
positive, `epoch_boundary` must not precede
`active_tier_policy.refill_epoch_origin`, and epoch index
is `floor((epoch_boundary - active_tier_policy.refill_epoch_origin) /
active_tier_policy.refill_epoch_duration)`. Epochs are processed sequentially
and exactly once. `window_start` equals
`active_tier_policy.refill_epoch_origin + refill_epoch_index *
active_tier_policy.refill_epoch_duration`; `window_end` is the next boundary. A
missed epoch cannot later be claimed using current evidence; absent evidence at
its boundary records zero refill for that epoch.

A consumed journal debit is refill-eligible only when all of the following were
true at the epoch boundary:
`released_at + active_tier_policy.loss_budget_lookback <= epoch_boundary`;
destination finality was observed; reconciliation covers the release; its
correlated exposure is independently recorded as closed; the required clean
epochs in `active_tier_policy` and anomaly-clear conditions hold; and the value
did not originate from
pending PnL, attacker-supplied circular deposits, same-system IOUs, or queued
credit. Final settlement is necessary but is never sufficient by itself.

For each common and native axis, sort eligible unrefilled journal debits by
`(released_at, release_id)` and calculate:

```text
common_refill[c] = min(
  sum(eligible_unrefilled_common_debits[c]),
  active_tier_policy.maximum_common_refill_by_axis[c]
)
next_common_consumed[c] = current_common_consumed[c] - common_refill[c]

native_refill[n] = min(
  sum(entry.amount for entry in eligible_unrefilled_native_debits[n]
      after require entry.asset == native_counter[n].asset),
  active_tier_policy.maximum_native_refill_by_axis[n]
)
next_native_consumed[n] = current_native_consumed[n] - native_refill[n]
```

Debit the same oldest eligible journal entries by exactly the corresponding
common or native refill. Reservations and in-flight amounts carry forward
unchanged. Counter limits
come only from the fully effective, timelocked policy; a lower new limit yields
zero remaining capacity until exposure decays and never erases exposure. The
new epoch index, counters, journal, evidence references, and prior ledger tip
determine the next ledger tip. Mismatched assets, numeraires, scales, missing
axis limits, underflow, or journal/counter disagreement reject the transition.

### Discrete assurance tiers

Named tiers are preferred to continuous scoring because their requirements and
maximum consequences can be audited.

- `Quarantined`: one or more hard gates fail, evidence conflicts, or an active
  anomaly exists. Instant amount is zero. Time alone cannot release it.
- `UnprovenOrNovel`: gates pass at the minimum accepted boundary, but the
  subject, destination, route, asset, contract, or behavior is new. Only a small
  policy-capped amount may externalize; the remainder receives a long challenge
  window.
- `CurrentlyAssured`: independent current evidence passes, behavior is within
  established bounds, and solvency headroom is adequate. A moderate amount may
  externalize under rolling caps; the remainder receives a shorter challenge
  window.
- `StrongCurrentAssuranceLowImpact`: current evidence is strong across every
  critical lane and the consequence remains below all systemic thresholds. A
  high fraction may externalize, but no reputation tier removes the global loss
  budget or the hard threshold for exceptional value.

Specific fractions and durations are deployment policy, not constants defined
by this design. They must appear in a versioned `AssuranceTierPolicy`, not as an
undeclared implementation choice. Illustrative ranges such as hours versus days
are scenario inputs only and must be stress-tested before any implementation
claim.

Required delay should be bottleneck-based rather than averaged:

```text
required_delay = max(
  action_class_delay,
  destination_novelty_delay,
  authorization_change_delay,
  oracle_risk_delay,
  instrument_novelty_delay,
  economic_impact_delay,
  chain_or_bridge_delay,
  incident_mode_delay,
  policy_change_cooldown
)
```

Where operational evidence exists, a challenge window should cover a measured
high-percentile detection, validation, and intervention interval plus a safety
margin. If continuous watcher and intervention coverage is required but cannot
be demonstrated, the corresponding instant external-release lane is unavailable.

### Challenge queue and state machine

```text
Requested
  -> Rejected
  -> Quarantined
  -> Validated
       -> InstantPartReleased
       -> FullyQueued
       -> PartiallyQueued

Queued
  -> Challenged -> Quarantined | Cancelled | Revalidated
  -> EvidenceExpired -> RevalidationRequired
  -> EmergencyFrozen
  -> ReleasedAfterFreshRevalidation
```

Release after a waiting period requires fresh evidence and budget consumption.
It must not be an automatic timer callback over stale evidence.

The queue needs:

- an append-only request, policy, evidence, cap, and state-transition record;
- independent watchers with explicit trust roots and failure assumptions;
- a bounded challenge grammar with evidence, not arbitrary veto messages;
- a defined response deadline and liveness fallback;
- cancellation and destination-replacement rules that cannot bypass review;
- no freely transferable claim token representing the queued amount unless that
  token is itself treated as externalization;
- zero withdrawal, bridge, transfer, borrowing, collateral, margin-reuse, or
  release-budget value for the pending amount;
- priority rules that resist fee bidding, censorship, and queue MEV;
- recovery and insolvency rules defined before crisis, not during it.

### Fast tightening, slow relaxation

Policy should be asymmetric:

- new risk evidence can reduce caps or lengthen windows immediately;
- evidence expiry immediately removes the affected assurance;
- relaxation requires documented resolution evidence, fresh independent
  evidence, a fixed minimum dwell, the versioned policy's required number of
  clean epochs, and independent approval of the successor policy;
- every cap increase or delay reduction requires a timelock, shadow evaluation
  against retained traffic and incidents, and gradual per-epoch refill bounded
  by the policy's common and native per-axis refill maps;
- emergency overrides cannot silently increase instant release;
- policy-version rollback is a hard failure unless separately proven safe.

This hysteresis limits attacker-induced oscillation and avoids a momentary clean
signal reopening maximum outflow after an anomaly.

### Circuit breakers

Circuit breakers are necessary but dangerous. A bounded breaker may stop one
externalization class, asset, source, destination, oracle, or state key. It must
not become universal discretionary custody.

A breaker action should name:

- the exact affected state slice;
- triggering evidence and confidence;
- scope and expiry;
- who can invoke, renew, narrow, or clear it;
- whether internal risk-reducing transitions continue;
- which user exits remain safe;
- the audit and appeal path;
- the maximum damage if the breaker authority is malicious or unavailable.

One authorized actor may tighten a narrowly scoped lane for one short initial
period. Renewal requires objective continuing evidence and an independently
constituted quorum that does not reduce the original scope controls. Policy must
predeclare a maximum cumulative freeze and a bounded appeal deadline. Settled,
unaffected principal is segregated from disputed profit so that an incident does
not turn every claim into discretionary custody. At the cumulative ceiling, the
request enters a predeclared resolution state with entitlement-based safe exits,
insolvency priority, and adjudication rules. It neither auto-releases disputed
value nor remains in indefinite limbo. Safe exits are determined from current
entitlement and unaffected prefunding, not ad hoc identity, influence, or fee
payment.

## Security Coverage And Limits

### Oracle or authorized-forwarder compromise

Controls that matter:

- reject reports outside a bound request window and prohibit pre-prepared data
  from becoming reusable merely when its timestamp matches;
- bind report data, request and order ids, nonce, market calendar, contract
  state, action, and policy;
- enforce monotonic sequence, one-time consumption, and equivocation detection;
- require independent roots for high-impact profit realization;
- cap aggregate PnL velocity by market, oracle root, subject, and venue;
- queue external profit while preserving immediate position closure and margin
  state;
- freeze the affected source rather than every unrelated market.

Residual risk: if every independent root, monitor, and pause key is compromised,
or if the attacker can monetize the queued credit elsewhere, delay alone fails.

### User or operator signing-key compromise

Controls that matter:

- destination novelty and allowlist policy;
- session- and action-bound authorization;
- rolling caps across correlated accounts;
- fresh reauthentication or multi-party approval for exceptional value;
- challenge notification over an independent channel;
- rapid cap reduction on anomalous velocity.

Residual risk: a compromised recovery or delay-controller key can censor or
fraudulently release funds. Key diversity without operational independence is
not independent assurance.

### Accounting or smart-contract defect

Controls that matter:

- independent recomputation;
- invariant and solvency checks before externalization;
- amount and velocity caps;
- a queue long enough for detection and response;
- staged release rather than one terminal transfer.

Residual risk: defects below thresholds can leak gradually. Monitoring and
budgets must aggregate small releases and detect slow drains.

### Governance attack

Controls that matter:

- policy-change timelocks;
- version-pinned requests;
- no same-transaction policy change and release;
- bounded emergency power;
- fast tightening but delayed relaxation;
- public or independently retained policy and decision digests.

Residual risk: a fully captured governance and legal structure can eventually
authorize harmful behavior. Technical delay provides reaction time, not
legitimacy.

### Bridge, cross-domain, and linked-settlement failure

Controls that matter:

- distinguish verified atomic linked settlement from two independent transfers;
- treat each additional bridge, custodian, sequencer, and legal domain as a new
  dependency;
- cap exposure by correlated trust root;
- require finality evidence before the dependent leg externalizes;
- preserve unwind and timeout semantics.

Residual risk: cross-ledger protocols can reintroduce principal, liquidity, and
reorg risk. A fast source chain does not prove destination finality.

### Insolvency or market-wide stress

Controls that matter:

- real-time internal margin and loss recognition;
- liquidity resources for same-day, intraday, and multiday obligations;
- netting where legally enforceable and operationally reliable;
- conservative collateral haircuts and concentration limits;
- systemic caps that contract as correlations and volatility rise;
- transparent queue priority and recovery rules.

Residual risk: delaying everyone can convert a solvency problem into a run,
create a discount market in queued claims, or privilege insiders. A queue cannot
manufacture assets.

### AI-agent swarm or machine-speed attack

Controls that matter:

- aggregate identity, sponsor, model, policy, destination, and trust-root caps;
- semantic duplicate and coordinated-pattern detection;
- action proposals remain proposal-only until admitted;
- no agent reputation can grant signing or settlement authority;
- compute and transaction budgets decline under correlated behavior;
- deterministic policy precedes model-based anomaly review.

Residual risk: model-generated novelty can outpace rule updates, while shared
models and data create hidden common-mode behavior. An AI reviewer must not be
the sole authority over an AI-originated financial action.

### What mandatory delay does not solve

Delay does not prevent:

- loss that remains internal and already makes the system insolvent;
- liquidation damage caused by stale risk state;
- compromised monitoring, challenge, or pause authority;
- legal reversal or default outside the technical system;
- synthetic externalization through transferable queued claims, borrowing, or
  cross-protocol collateralization;
- slow drains below fragmented caps;
- correlated oracle, cloud, signer, and governance dependencies;
- user harm from censorship, indefinite freezes, or discriminatory review.

## HSAI Integration Boundary

The future composition should be:

```text
venue terms and source evidence
  -> TerminalContractIR lowering
  -> StateKey and payoff portfolio
  -> residual and five-dimensional completeness reports
  -> proposed execution or externalization action
  -> AgentCase / admission candidate
  -> current ClaimEnvelope evidence and explicit assumptions/excludes
  -> deterministic HSAI admission decision
  -> accepted proposal-only handoff
  -> separately authorized signer, venue, custodian, or settlement controller
```

HSAI can eventually provide:

- content-addressed action and policy identity;
- explicit evidence maturity, trust roots, validity windows, assumptions, and
  nonclaims;
- fail-closed admission and quarantine;
- replay and policy-downgrade resistance;
- append-only decision provenance;
- bounded agent, sponsor, economy, and membrane policy signals.

HSAI cannot currently provide:

- market-data truth;
- payoff normalization;
- best execution;
- order placement or atomic routing;
- legal equivalence;
- margin offset recognition;
- custody, solvency, liquidity, or settlement finality;
- live circuit breaking;
- proof of semantic correctness or global agent uniqueness.

The existing Agent Approval Gateway explicitly stops before external authority.
Any future Statebook action adapter must preserve `grants_authority=false` until
a separately reviewed phase defines the downstream capability owner.

## Required Invariants

A future implementation must preserve all of the following:

```text
SB-01  Source identity: normalized terms remain bound to source terms and revision.
SB-02  State honesty: same ticker or narrative does not imply same StateKey.
SB-03  Residual honesty: equivalence is no stronger than the declared state domain.
SB-04  Path honesty: terminal claims do not silently absorb perpetual path risk.
SB-05  Completeness separation: semantic, product, execution, settlement, and
       capital statuses never collapse into one success bit.
SB-06  Evidence separation: ClaimEnvelope composition never performs payoff netting.
SB-07  No authority: analysis and admission never become execution permission.

AS-01  Hard-gate priority: a failed or unknown critical gate forces zero instant release.
AS-02  Current evidence: prior reputation never substitutes for expired current evidence.
AS-03  Weakest-lane visibility: no aggregate score hides a failed critical lane.
AS-04  Bounded consequence: instant release never exceeds any applicable cap.
AS-05  Aggregate caps: transaction splitting cannot expand the total allowance.
AS-06  No round-up: exact arithmetic cannot increase instant release by rounding.
AS-07  Fresh release: queued value is revalidated before release.
AS-08  Queue non-transferability: pending value has zero transfer, borrowing,
       collateral, margin-reuse, or release-budget value.
AS-09  Fast tightening: new risk can reduce authority immediately.
AS-10  Slow relaxation: restored authority requires resolution evidence, minimum
       dwell, clean epochs, timelock, shadow evaluation, and gradual refill.
AS-11  Atomic exception: DvP/PvP remains hard-gated and capped, uses only
       represented, prefunded, unencumbered legs, reserves every gross outbound
       leg, excludes pending credit, and permits no unilateral extraction.
AS-12  Risk continuity: pausing externalization does not silently pause necessary
       margin, liquidation, or loss-recognition state; a pre-authorized external
       risk-reducing obligation remains hard-gated, segregated, destination-
       restricted, finality-capable before deadline, capped, and in-flight until
       destination finality is actually observed.
AS-13  Circuit-breaker bounds: emergency authority is scoped, expiring, auditable,
       independently renewable, cumulatively bounded, and appealable.
AS-14  Insolvency honesty: delay never creates or claims solvency.
AS-15  Budget atomicity: every applicable represented asset-native and
       common-numeraire counter is reserved and consumed exactly once under one
       versioned ledger state.
AS-16  Valuation independence: cross-asset caps never depend solely on the data
       root whose action or PnL they are limiting.
```

## Market And Global-Economy Intersection

### The convergence thesis

The likely convergence is not one universal exchange. It is a stack in which
payoff forms become portable while execution, collateral, law, and distribution
remain partially plural:

```text
economic state descriptions
  -> normalized payoff forms
  -> venue-specific execution
  -> portfolio and residual analysis
  -> evidence-aware authority
  -> clearing, collateral, and settlement domains
```

Onchain systems have structural advantages in shared state, programmability,
conditional composition, and transparent asset movement. Conventional markets
retain structural advantages in legal certainty, benchmark governance, default
management, institutional distribution, and recognized capital treatment. The
near-term winner is more likely to interoperate across these strengths than to
erase either side.

### AI and technology create new risk underlyings

AI is not one sector. It branches into physical and institutional constraints
that can become state variables:

- Compute: accelerator availability, inference capacity, memory, networking,
  cloud concentration, model throughput, and service-level failure.
- Electricity: generation, transmission, interconnection queues, nodal prices,
  firm capacity, fuel supply, cooling, and water.
- Semiconductors: fabrication, advanced packaging, lithography, export controls,
  geographic concentration, and equipment lead times.
- Software and agents: productivity, cyber loss, autonomous spend, model drift,
  data rights, liability, and service interruption.
- Robotics and industrial automation: labor substitution and complementarity,
  warehouse and factory utilization, safety, component supply, and logistics.
- Biotech and health: research milestones, trial outcomes, manufacturing yield,
  reimbursement, regulation, and privacy.
- Defense and geopolitics: compute sovereignty, sanctions, trade routes,
  spectrum, satellites, supply security, and cyber escalation.
- Climate and natural systems: weather, catastrophe, carbon, crop yield, water,
  and energy-demand volatility.
- Finance: AI-capex credit, concentrated equity exposure, collateral correlation,
  stablecoin and tokenized-deposit settlement, insurance, and operational risk.

These variables invite perpetual, event, option, insurance, compute, and
structured payoff forms. They also share common physical roots. Ten nominally
different AI contracts may all be long the same grid connection, chip supply
chain, cloud provider, benchmark administrator, or geopolitical assumption. A
Statebook's main systemic value is making those hidden common roots and residuals
visible before they become collateral offsets or instant settlement authority.

### Progress occurs at several clocks

The software clock is fastest: contract generation, AI-agent activity, market
interfaces, and synthetic product experimentation can change in months.

The assurance clock is slower: reliable data lineage, independent verification,
operational controls, insurance, and institutional risk models require repeated
evidence across incidents and stress regimes.

The market-infrastructure clock is slower again: clearing interoperability,
recognized margin offsets, custody, bankruptcy treatment, and cross-border legal
finality usually advance over years.

The physical clock is uneven and frequently decisive: chips and servers can be
deployed faster than transmission lines, power plants, water systems, fabs, and
large industrial supply chains. The IEA's 2026 update reports that data-centre
electricity demand grew 17% in 2025 and projects it to roughly double from 485
TWh in 2025 to 950 TWh in 2030; AI-focused data-centre consumption grows faster,
roughly tripling over that interval. The same update stresses near-term grid,
equipment, chip, capital, planning, and social-acceptance bottlenecks. Those
constraints create exactly the compute, power, congestion, financing, and
project-completion risks that frontier markets may attempt to price.

The macro clock can move in the opposite direction. The World Bank's June 2026
baseline forecasts global growth slowing from 2.9% in 2025 to 2.5% in 2026 amid
energy and geopolitical stress, while treating broader AI investment and
adoption as upside rather than a guaranteed productivity result. Fast technical
progress can therefore coexist with slower aggregate growth, tight financing,
and uneven diffusion. Frontier-risk markets will price that divergence as much
as they price model capability.

Official baselines also disagree. The IMF's 8 July 2026 update projects 3.0%
global growth in 2026 and 3.4% in 2027, describing an energy shock from the
Middle East war pulling against an AI-driven technology investment cycle. The
World Bank and IMF numbers are not blended into false precision: their timing,
assumptions, and country coverage differ. Forecast dispersion is itself a state
to expose because the value of compute, power, inflation, rates, credit, and
geopolitical contracts depends on which macro path materializes.

### Two-year horizon: 2026-2028

Base case:

- AI-agent proposals and automated financial operations grow faster than
  evidence-aware authorization, increasing demand for pre-signing and
  pre-settlement controls.
- Perpetual, event, tokenized-asset, compute, power, and insurance-like products
  continue to proliferate, but remain fragmented by venue and legal domain.
- Normalized contract metadata and source digests become more valuable than a
  universal payoff engine because basic semantic mismatches are still common.
- Security incidents push high-value protocols toward per-path rate limits,
  withdrawal queues, oracle diversity, monitoring, and scoped circuit breakers.
- Institutions favor shorter settlement and atomic linked settlement where it
  reduces principal risk, while retaining netting and liquidity-saving functions.

Constraint case: geopolitical shocks, power and chip bottlenecks, weak AI
productivity realization, regulation, or another series of infrastructure
failures slows capital formation and raises the price of liquidity and assurance.

Acceleration case: reliable agent productivity, clearer digital-asset rules,
better tokenized cash, and interoperable identity/evidence standards move
selected markets from metadata comparison to executable cross-venue portfolios.

### Five-year horizon: 2029-2031

Base case:

- `TerminalContractIR` profiles become useful inside particular ecosystems and
  asset families; global canonicalization remains incomplete.
- Some clearing and collateral systems recognize bounded cross-product offsets,
  but legal entity, jurisdiction, default waterfall, and liquidity differences
  prevent universal capital completeness.
- AI infrastructure becomes a material bridge between technology markets and
  energy, utilities, commodities, industrial policy, credit, and real estate.
- Autonomous procurement and treasury systems make machine identity, delegated
  limits, action provenance, and reversible settlement windows standard control
  questions.
- Dynamic settlement policy becomes more granular: instant low-impact flows,
  delayed high-impact externalization, atomic linked legs, and stress-responsive
  system caps coexist.

Constraint case: concentrated AI returns, energy scarcity, debt stress,
cybersecurity losses, or fragmented regulation keep markets siloed and turn
settlement queues into liquidity discounts.

Acceleration case: cheaper inference, durable productivity gains, abundant firm
power, trusted digital cash, and common legal standards enable meaningful
cross-venue routing with evidence-bound residual and capital reports.

### Ten-year horizon: 2032-2036

Base case:

- State-oriented market views exist for major economic references, but execution
  and finality remain federated across regulated, onchain, bilateral, and
  sovereign domains.
- AI, energy, compute, robotics, biotech, climate, defense, and logistics risks
  produce richer synthetic markets and more correlated tail exposure.
- The scarce infrastructure is not contract creation. It is trustworthy
  observation, enforceable settlement, liquidity under stress, and governance of
  shared risk models.
- Mature systems expose assurance and residual vectors rather than a single
  trust, risk, or completeness score.
- Settlement speed becomes a priced service level constrained by current
  evidence and loss capacity, not a universal ideological property.

Constraint case: physical bottlenecks, public-debt pressure, geopolitical blocs,
cyber conflict, institutional distrust, and legal fragmentation restrict the
Statebook to analysis and bilateral interoperability.

Acceleration case: broadly distributed AI productivity, infrastructure buildout,
reliable machine-readable law and contracts, strong privacy-preserving evidence,
and interoperable settlement assets produce a genuine multi-venue market
substrate. Even in that case, systemic externalization remains capped because
faster autonomous systems increase both useful throughput and attack velocity.

These horizons are scenarios, not forecasts. Their purpose is to expose the
dependencies that would accelerate or falsify the architecture.

### Macro feedback loops

Several loops deserve explicit stress treatment:

1. AI-capex loop: expected productivity raises compute investment; investment
   raises power, chip, construction, and credit demand; bottlenecks raise prices;
   disappointment reprices concentrated technology and infrastructure assets.
2. Automation-distribution loop: productivity may raise aggregate output while
   gains concentrate by country, firm, occupation, and capital ownership;
   political response changes tax, labor, trade, and data rules.
3. Liquidity-speed loop: faster gross settlement reduces some counterparty risk
   but increases prefunding and intraday liquidity demand; netting reduces
   liquidity needs but accumulates replacement and default exposure.
4. Security-speed loop: machine-speed markets improve risk response and capital
   use, while also allowing compromised credentials or data to externalize losses
   before humans can intervene.
5. Assurance-concentration loop: a small number of clouds, oracle operators,
   identity providers, chip vendors, and settlement assets make integration
   easier while increasing common-mode failure.
6. Delay-shadow-liquidity loop: long queues create discounts, borrowing, and
   transferable claims around pending value, potentially recreating instant exit
   outside the monitored boundary.
7. Monetary-policy loop: AI investment can raise near-term demand for capital,
   labor, power, and imported equipment before productivity expands supply;
   interest rates and financing costs then determine which infrastructure
   projects survive long enough to deliver that productivity.
8. Grid-allocation loop: concentrated data-centre demand can finance generation
   and transmission while shifting congestion, reliability, water, and cost
   burdens to other users; political allocation decisions feed back into project
   permits and regional compute prices.
9. Sovereignty loop: chip, cloud, data, model, payment, and energy dependencies
   drive subsidies, export controls, local-content rules, and strategic reserves;
   fragmentation raises resilience within some blocs while reducing global
   liquidity and comparability.
10. Development-divide loop: countries with reliable power, connectivity,
    compute, skills, institutions, and capital compound AI gains, while countries
    without them face higher import dependence and fewer locally relevant models;
    open technology can narrow but does not automatically close this gap.
11. Climate-insurance loop: AI and electrification change load and emissions
    paths while better forecasting and automation improve system efficiency;
    catastrophe, water, and transition risks then reprice infrastructure credit
    and insurance capacity.
12. Capital-offset leverage loop: better semantic and portfolio recognition can
    reduce duplicative margin, but the released capital can support larger gross
    positions; leverage and common-mode exposure may rise faster than genuine
    diversification.
13. Insurance-moral-hazard loop: coverage, emergency funds, or socialized loss
    can improve recovery while weakening incentives to control oracle,
    governance, and settlement risk unless premiums, deductibles, and recourse
    preserve consequence.
14. Semantic-automation correlation loop: common Statebook definitions make
    comparison easier, while shared agent models and strategy templates can
    interpret the same state identically and crowd into correlated positions or
    exits.

A Statebook should make each loop's shared state variables and trust roots
queryable. It should not pretend to predict them with one probability.

### Evaluation metrics and rejection criteria

The horizon cases remain hypotheses. Before a simulator or pilot sees outcome
data, it must freeze numerical thresholds for the following observables under a
versioned evaluation plan. Symbols below are parameters, not empirically
calibrated values in this Level 0 document:

- semantic quality: false-equivalence and missed-counterexample rates must stay
  below `E_max`; every unsupported state remains explicit. Exceeding `E_max`
  rejects use of Statebook output for routing or capital decisions;
- security utility: conservatively estimated prevented external loss must exceed
  legitimate liquidity, funding, and failed-payment cost by the pre-registered
  factor `B_min`. Failure rejects the retained release policy for that lane;
- liveness and fairness: false-quarantine rate, appeal-resolution time, and
  outcome disparity across equivalently entitled users must remain below
  `F_max`, `A_max`, and `D_max`. Breach disables the affected tier or breaker;
- intervention adequacy: measured high-percentile detection plus validation plus
  intervention latency, with safety margin, must fit inside the challenge
  window. Otherwise the corresponding instant lane is unavailable;
- shadow liquidity: queue discount, borrowing against pending value, and
  transferable-receipt volume must stay below `S_max`. A breach means the queue
  is recreating externalization outside the controller and must be redesigned;
- governance dependence: manual override frequency, renewal frequency,
  challenger unavailability, and trust-root concentration must stay below their
  frozen limits. A breach rejects the claimed assurance tier even if no loss has
  yet occurred;
- capital effect: gross-to-net reduction, recognized-margin reduction, gross
  leverage, concentration, and wrong-way exposure are measured together.
  Capital recognition fails if leverage or stress loss crosses its frozen limit
  despite lower reported margin;
- machine correlation: common model, sponsor, policy, destination, and position
  factors are measured across agents. A coordinated-position or run threshold
  breach contracts the shared budget rather than treating agents as independent;
- insurance behavior: control investment, incident frequency, deductible
  retention, recovery-fund depletion, and loss socialization are compared before
  and after coverage. Evidence that coverage raises unmanaged risk beyond
  `M_max` rejects the assumed resilience benefit.

No architecture is validated by one quiet period. The policy is rejected or
re-scoped when these pre-registered criteria fail under benign volume, adversarial
replay, correlated-source failure, liquidity stress, and insolvency cases. A
later phase must publish the actual thresholds, sampling windows, counterfactual
method, and uncertainty bounds before calling any scenario supported.

## Retained Development Sequence

### Stage 0: this boundary

Documentation only. Freeze terminology, separation rules, pseudo-types,
security policy, invariants, scenarios, claim ceiling, and source basis.

### Stage 1: synthetic terminal-payoff fixtures

A separately authorized phase may add a small, local fixture set for scalar,
cash-settled terminal claims. It should prove parsing and deterministic
normalization only. It must include near-miss contracts whose ticker matches but
calendar, comparator, source, settlement asset, rounding, or default rule does
not.

### Stage 2: local payoff and residual engine

Add exact rational evaluation over a bounded state domain, portfolio
composition, exact-versus-approximate status, unsupported-state reporting, and
property tests for the Statebook invariants. Still no market data or execution.

### Stage 3: hermetic execution-completeness model

Use synthetic books and deterministic failure cases to separate theoretical
span from fills, slippage, partial legs, timing, and unwind residuals. No live
venue adapter.

### Stage 4: assurance-adjusted settlement simulator

Use synthetic requests, evidence, caps, anomalies, and queues to test the hard
gates, independent cross-asset valuation, atomic budget reservations,
aggregation, hysteresis, challenge, circuit-breaker, atomic-linked and
risk-reducing-obligation classes, evaluation rejection criteria, and insolvency
nonclaims. The simulator must not control assets.

### Stage 5: external evidence boundary

Specify one venue or clearing source, source revision, legal status, operator
workflow, credential handling, hermetic test double, and fail-closed import
contract before any network implementation.

### Stage 6: separately owned authority integration

Only a new reviewed phase may connect an accepted proposal to an execution,
custody, margin, or settlement controller. It must name who owns authority,
maximum loss, rollback and pause semantics, audit retention, legal domain, and
production gate. Nothing in this document authorizes that phase.

## Future Scenario Corpus

A future simulator should include at least:

- a correctly signed report prepared for later use and consumed when its
  timestamp matches, but lacking request-, order-, or nonce-specific binding;
- stale data with a fresh transport timestamp;
- two reports derived from one compromised upstream source;
- a valid close with artificial profit and an immediate payout request;
- a valid liquidation whose external payout is frozen but whose risk state must
  still update;
- a large request split across agents, destinations, assets, and blocks;
- a known subject using a new bridge or contract destination;
- a policy downgrade immediately before release;
- anomaly activation after instant-part release but before queued-part release;
- evidence expiry while queued;
- a challenge that is valid, invalid, duplicated, censored, or unavailable;
- a compromised breaker key attempting to widen release;
- malicious breaker renewal, selective censorship, challenger outage, maximum
  cumulative-freeze exhaustion, and the predeclared resolution transition;
- a legal or operational finality mismatch across two otherwise equal payoffs;
- atomic DvP with one leg lacking finality evidence, prefunding, entitlement, or
  unencumbered status, a hidden outbound leg, same-operation inbound netting,
  and a leg backed by pending PnL;
- a time-critical external margin obligation that genuinely reduces contagion,
  an expired obligation, a general withdrawable destination credit, and a
  withdrawal falsely labeled as that obligation;
- an obligation whose cap fits only a harmful partial amount, and a separately
  authorized smaller tranche with its own exposure evidence;
- a transferable receipt or loan that monetizes queued value;
- a slow drain below per-transaction limits but above the aggregate budget;
- concurrent finalizers racing every cap, a failed-transfer reservation rollback,
  and a queued request attempting to reserve capacity indefinitely;
- cross-asset requests whose action oracle conflicts with the independent
  budget-valuation roots;
- a stressed but solvent venue and an insolvent venue with identical queue data;
- an AI-agent swarm coordinated through one model, sponsor, or destination;
- benign high volume that tests liveness without weakening hard gates.

## Evidence And Source Basis

Incident and Ostium design sources, observed 15 July 2026:

- Ostium incident acknowledgement and trading pause:
  <https://x.com/Ostium/status/2077412452392652917>
- Ostium investigation update:
  <https://x.com/Ostium/status/2077438120354603396>
- Blockaid preliminary attribution:
  <https://x.com/blockaid_/status/2077405527428989363>
- Cited Arbitrum transaction:
  <https://arbiscan.io/tx/0x359f8c05b86a4409d60cfba02084334313fd94b19f74a294fb7fc4ea7d4870e0>
- Ostium LP withdrawal documentation:
  <https://ostium-labs.gitbook.io/ostium-docs/vault/withdraw>
- Ostium oracle documentation:
  <https://ostium-labs.gitbook.io/ostium-docs/supporting-infrastructure/price-oracle>
- Ostium automation and authorized-forwarder documentation:
  <https://ostium-labs.gitbook.io/ostium-docs/supporting-infrastructure/automations>
- Ostium public profitable-close path at the pinned source commit:
  <https://github.com/0xOstium/smart-contracts-public/blob/8390ce497f68fb128900840e0ec30683afa945d3/src/lib/TradingCallbacksLib.sol#L620-L653>
- Ostium public vault transfer path at the pinned source commit:
  <https://github.com/0xOstium/smart-contracts-public/blob/8390ce497f68fb128900840e0ec30683afa945d3/src/OstiumVault.sol#L731-L754>
- Ostium public authorized-signer verifier at the pinned source commit:
  <https://github.com/0xOstium/smart-contracts-public/blob/8390ce497f68fb128900840e0ec30683afa945d3/src/OstiumVerifier.sol#L51-L64>
- Ostium public private-price upkeep binding at the pinned source commit:
  <https://github.com/0xOstium/smart-contracts-public/blob/8390ce497f68fb128900840e0ec30683afa945d3/src/OstiumPrivatePriceUpKeep.sol#L77-L121>
- Ostium public router timestamp bound at the pinned source commit:
  <https://github.com/0xOstium/smart-contracts-public/blob/8390ce497f68fb128900840e0ec30683afa945d3/src/OstiumPriceRouter.sol#L70-L87>

Settlement, risk, and assurance sources:

- Hyperliquid portfolio-margin documentation:
  <https://hyperliquid.gitbook.io/hyperliquid-docs/trading/portfolio-margin>
- Kalshi BTC perpetual contract specification:
  <https://help.kalshi.com/en/articles/15357587-btc-perpetual-futures-contract-specifications>
- Architect intended compute-futures product page and regulatory-review
  disclosure:
  <https://architect.co/resources/press/architect-ornn-compute-futures/>
- CME SPAN portfolio-risk and performance-bond methodology overview:
  <https://www.cmegroup.com/solutions/risk-management/performance-bonds-margins/span-methodology-overview.html>
- FINOS Common Domain Model product model:
  <https://cdm.finos.org/docs/product-model/>
- SEC staff statement distinguishing issuer-sponsored, custodial third-party,
  and synthetic third-party tokenized securities and their differing rights:
  <https://www.sec.gov/newsroom/speeches-statements/corp-fin-statement-tokenized-securities-012826-statement-tokenized-securities>
- CFTC 2026 event-contract and prediction-market rulemaking inquiry, which shows
  that product convergence remains subject to active public-law boundaries:
  <https://www.cftc.gov/PressRoom/PressReleases/9194-26>
- CPMI tokenisation report on atomic DvP/PvP, principal risk, governance, risk
  management, liquidity, and netting tradeoffs:
  <https://www.bis.org/cpmi/publ/d225.htm>
- BIS review of securities-settlement credit and liquidity tradeoffs:
  <https://www.bis.org/publ/qtrpdf/r_qt2003i.htm>
- CPMI-IOSCO Principles for Financial Market Infrastructures, especially legal
  basis, credit, collateral, margin, liquidity, finality, linked obligations,
  default, operational risk, links, and disclosure:
  <https://www.bis.org/pfmi/help/principleid.htm>
- CPMI fast-payments analysis of immediate final-funds availability, fraud,
  credit, liquidity, security, and consumer-protection tradeoffs:
  <https://www.bis.org/cpmi/publ/d154.pdf>
- CFTC Staff Advisory 26-16 on 24/7 derivatives-trading risk management,
  surveillance, reference-market closures, liquidity, and operational controls:
  <https://www.cftc.gov/csl/26-16/download>
- NIST zero-trust definition requiring no implicit trust and continuous
  verification from multiple sources:
  <https://csrc.nist.gov/glossary/term/zero_trust_architecture>
- NIST session-monitoring guidance on ongoing fraud evaluation and response:
  <https://pages.nist.gov/800-63-4/sp800-63b/session/>
- IETF RATS architecture separating attestation evidence, appraisal policy,
  results, and relying-party decisions:
  <https://www.rfc-editor.org/rfc/rfc9334.html>

AI and global-economy sources:

- IEA 2026 `Key Questions on Energy and AI` update on 2025 electricity growth,
  the 2030 central projection, AI-focused demand, capital, grid, equipment, chip,
  and social-acceptance constraints:
  <https://www.iea.org/reports/key-questions-on-energy-and-ai/executive-summary>
- IMF April 2026 World Economic Outlook on global growth, geopolitical
  fragmentation, public debt, and AI-productivity upside and downside:
  <https://www.imf.org/en/publications/weo/issues/2026/04/14/world-economic-outlook-april-2026>
- IMF 8 July 2026 World Economic Outlook Update on the opposing energy-shock and
  technology-investment forces, uneven country exposure, and updated 2026-2027
  global growth projection:
  <https://www.imf.org/en/publications/weo/issues/2026/07/08/world-economic-outlook-update-july-2026>
- World Bank Digital Progress and Trends Report 2025 on unequal AI compute,
  innovation, skills, connectivity, and adoption:
  <https://www.worldbank.org/en/publication/dptr2025-ai-foundations/report>
- World Bank June 2026 Global Economic Prospects on current growth, energy and
  geopolitical stress, AI investment, productivity uncertainty, and uneven
  emerging-market diffusion:
  <https://thedocs.worldbank.org/en/doc/2b672b3b0415d6b66c45b66579db4ef5-0050012026/original/GEP-Jun-2026.pdf>
- BIS 2026 Annual Economic Report chapter on trust, tokenisation, governance,
  composability, and the monetary system:
  <https://www.bis.org/publ/arpdf/ar2026e3.htm>
- Financial Stability Board monitoring report on AI adoption, third-party
  dependencies, market correlation, cyber risk, and model governance in finance:
  <https://www.fsb.org/2025/10/monitoring-adoption-of-artificial-intelligence-and-related-vulnerabilities-in-the-financial-sector/>

These sources support the problem framing and scenario assumptions. They do not
validate the proposed Statebook types, prove that the settlement policy prevents
loss, or authorize implementation.

## Completion And Nonclaims

This boundary is complete when its five declared documentation files point to
the same state slice, the source links are present, repository claim-boundary
and hygiene tests pass, no executable surface changes, and the pre-existing
dirty state remains byte-identical.

This boundary does not claim:

- that a Statebook is implemented;
- that the Ostium root cause or final loss is known;
- that mandatory delay would have prevented the incident;
- that any market pair is economically equivalent;
- that any portfolio is executable or receives margin offset;
- that HSAI verifies prices, solvency, legality, or settlement;
- that HSAI has exchange, custody, pause, routing, or signing authority;
- that a trust, assurance, or instant-settlement ratio is empirically calibrated;
- that the global-economy scenarios are forecasts;
- that local documentation is benchmark evidence, production readiness, SOTA,
  semantic correctness, full security, or independently reproduced evidence.
