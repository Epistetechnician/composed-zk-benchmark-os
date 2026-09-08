# HSAI Outcome-Priced Work Market Plan V1

## Status and state slice

This is an additive planning artifact under named state slice
`hsai-proof-carrying-capability-bounded-agent-platform-outcome-priced-work-market-v1`.

It extends the parallel agent-platform plan with an outcome-priced work market:
buyers publish measurable work objectives, providers compete to deliver them,
participants price the probability or value of the result, and payment follows
independent verification. The plan covers an offchain marketplace, Hyperliquid
testnet experimentation, and Stripe and Tempo payment Adapters.

This artifact does not authorize live model or provider execution, real-money
trading, payment processing, wallet creation, testnet deployment, market
creation, cryptographic signing, benchmark acquisition, or changes to any
closed Astral or Oak Lab slice. The current implementation ceiling remains
local pure-data control-plane and caller-owned file-persistence contract
evidence.

Wave 1 is now implemented locally in `hsai-outcome-work-market` with an
implementation-diverse `hsai-outcome-work-market-checker`. The slice provides
canonical job, market, observation, market-state, evidence, resolution, and
payout-intent records; fail-closed validation; replay-protected observations;
and a deterministic advisory TWAP. It does not execute a provider, call
Hyperliquid, move Stripe or Tempo value, verify a signature or proof, or grant
authority.

## Product definition

The product is an outcome-priced work market, not a generic prediction market.
It combines four related instruments:

| Instrument | Question | Primary user | Settlement object |
| --- | --- | --- | --- |
| Work bounty | Who will deliver the specified result? | Buyer and provider | Verified artifact and provider payment |
| Outcome quote | What should the buyer pay for a provider or job with this success profile? | Buyer, provider, liquidity provider | Locked quote or price band |
| Performance contract | Will the job meet its declared quality, cost, latency, or deadline target? | Buyer and provider | Verified metric vector |
| Prediction position | What do participants believe about a future work outcome? | Forecasters and market makers | Resolved outcome claim |

The first product combines a bounty with an advisory outcome market. A market
price can inform matching, budget allocation, milestone funding, and provider
selection. It does not itself prove that work is useful or authorize payment.
The evidence and admission planes remain authoritative for acceptance.

The proposed customer promise is:

> Publish a measurable job, obtain competing execution offers and a market
> forecast, fund the selected work, and release payment only when the frozen
> acceptance procedure validates the delivered result.

## Existing adjacent work

| Reference | Relevant contribution | Boundary relative to this plan |
| --- | --- | --- |
| [GSD at Work / Caritas experiment](https://caritas.ventures/blog/bounties-prediction-markets-llms-oh-my-christian-ulstrup-yba6e/) | A website task was connected to a programmable bounty and a Manifold prediction market; a completed GitHub event reportedly triggered both payment and resolution | Demonstrates an end-to-end work experiment, but does not establish that market price determined compensation or that assessment was independently cryptographic |
| [Futarchy Labs](https://docs.futarchy.fi/) | Decision markets, agent-market research, task pricing, review forecasting, contribution measurement, and market-informed allocation | Live public systems focus on governance; agent work markets are an emerging direction |
| [MetaDAO](https://docs.metadao.fi/governance/overview) | Onchain decision markets and time-weighted resolution for proposals | Selects or rejects decisions; it is not a compute-delivery verifier |
| [Math Market](https://openreview.net/pdf?id=uQPYAOHyPf) | Market incentives for multi-agent theorem proving, bounties, intermediate artifacts, and verified proofs | Research prototype for formal mathematics rather than a general commercial labor market |
| [Diagon](https://arxiv.org/abs/2604.06688) | Research environment for job posting, bidding, negotiation, execution, payment, and reputation among agents | Agent labor-market infrastructure without the complete outcome-market and evidence-payment seam |
| [Boundless](https://docs.boundless.network/provers/proving-stack) | Prover competition, job bidding, proof generation, verification, and conditional payment | Specialized proving market; it does not provide a general work specification, human-value metric, or payment rail |
| [Kalshi compute contracts](https://www.pokernews.com/prediction-markets/news/2026/08/kalshis-new-ai-compute-markets-explained-52156.htm) | Market pricing for future GPU rental prices and forward curves | Prices compute inputs rather than the successful delivery of a specified work product |

The opening is an integrated protocol that makes the work specification,
market signal, evidence packet, and payment decision share one immutable job
identity. This is an architecture opportunity, not a claim that the market
will be accurate or that incentives will be aligned automatically.

## System topology

```text
buyer intent
  -> typed job specification
  -> HSAI policy and capability preflight
  -> offchain listing and provider bids
  -> testnet outcome-price experiment
  -> selected provider and locked funding terms
  -> isolated execution
  -> evidence packet and independent validation
  -> outcome resolution
  -> Stripe or Tempo payout
  -> offchain index, reputation, and market analytics
```

### Module ownership

| Module | Interface | Implementation boundary |
| --- | --- | --- |
| Job registry | `WorkJobV1` | Canonical objective, inputs, outputs, deadline, resource budget, acceptance policy, and claim ceiling |
| Market service | `OutcomeMarketV1` | Offchain listing, order or quote state, liquidity, prices, and testnet mirror identifiers |
| HSAI control plane | `AdmissionDecisionV1` | Capability narrowing, evidence acceptance, release authority, replay, freeze, and rollback decisions |
| Evidence plane | `WorkEvidencePacketV1` | Artifact digest, evaluator result, provenance, custody, validator identity, and contradiction state |
| Execution Adapter | `ExecutionReceiptV1` | Provider runtime, resource accounting, logs or proofs, and result delivery |
| Hyperliquid Adapter | `HyperliquidMirrorV1` | Testnet market or contract state, transaction identifiers, confirmations, and reconciliation |
| Stripe Adapter | `StripePayoutV1` | Customer charge, connected account, transfer, refund, chargeback, and idempotency state |
| Tempo Adapter | `TempoPaymentV1` | Stablecoin transfer, memo, chain confirmation, sponsor or fee state, and reconciliation |
| Indexer | `SettlementProjectionV1` | Rebuildable view of accepted evidence, market resolution, payment state, and onchain events |

The market service may quote and match. Only the control plane can issue a
payment-release decision. Only a payment Adapter can move payment. Only the
evidence plane can transition a job from submitted to accepted.

## Canonical job contract

Every market and payment record binds to the same `job_id` and `job_digest`.
The canonical job includes:

```text
job_id
buyer_identity
objective_text_digest
program_or_workflow_digest
input_commitment
output_schema_digest
acceptance_policy_digest
assessment_set_commitment
quality_metrics and thresholds
resource_budget and accounting method
deadline and grace period
privacy and retention policy
allowed execution capabilities
provider eligibility and bond policy
market instrument and quote rule
payment currency, amount, and release schedule
dispute, timeout, cancellation, and refund rules
claim ceiling
```

The buyer chooses the objective and acceptance policy. Providers choose
whether to bid. Traders express beliefs about success or value. Independent
validators determine whether the submitted evidence satisfies the frozen
policy. No participant may change the policy after trading or execution
begins.

## Market design

### Initial instrument: verified-success outcome

For each fixed job, create a binary outcome:

```text
YES: the submitted artifact satisfies the frozen acceptance policy by deadline
NO:  the artifact does not satisfy the policy by deadline
```

The market price is an informational signal. A price of `0.72` may be
interpreted as an approximate 72% market-implied probability only after
accounting for spread, fees, liquidity, inventory, selection bias, and market
manipulation. It is not a calibrated probability by default.

The initial market should be advisory and testnet-backed. It can influence
provider ranking, buyer budget recommendations, review allocation, milestone
size, or a bounded provider bond. It should not directly decide high-value
spending, capability expansion, evidence acceptance, or irreversible actions.

### Later instruments

After the binary market is validated, add quality bands, independently settled
milestones, conditional Provider A versus Provider B markets, counterfactual
model/runtime/adapter markets, and declared latency, cost, energy, or proof-size
thresholds. Preserve the metric vector; derive composite scores through a
versioned policy instead of collapsing unrelated outcomes into one number.

### Price-to-work rules

| Mode | Use | Release requirement |
| --- | --- | --- |
| Advisory | Display forecast and confidence band | No automated effect |
| Bounded allocation | Adjust queue priority, review budget, or provisional provider score within fixed limits | HSAI checks bounds and policy |
| Contractual | Set a predeclared bonus, bond, or milestone amount | Frozen formula, accepted evidence, and payment authorization |

The first implementation is advisory. A later contractual rule could be:

```text
provider_payout = base_bounty
                 + bounded_bonus(market_TWAP, declared_quality)
                 - accepted_penalty(provider_failure)
```

The formula, observation window, liquidity minimum, price band, and maximum
bonus or penalty must be frozen before the job opens. A market price observed
after a failure cannot retroactively change the payment obligation.

## Hyperliquid testnet role

HyperEVM testnet documents chain ID `998` and RPC endpoint
`https://rpc.hyperliquid-testnet.xyz/evm`. Hyperliquid's API documentation
states that API requests can use the corresponding testnet endpoint. These are
integration facts to verify at implementation time, not evidence that our
custom work market is already available. [HyperEVM documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm)
[API documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api)

HIP-4 defines fully collateralized, bounded outcome contracts and documents a
staged initial release. Its first documented market is a recurring binary
outcome tied to the BTC mark price; additional markets and multi-outcome
support are staged features. We must verify which market-creation and
resolution operations are available before claiming support for custom work
outcomes. [HIP-4 documentation](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-4-outcome-markets)

The Adapter supports two paths:

| Path | Meaning | Entry condition |
| --- | --- | --- |
| Native outcome mirror | A supported Hyperliquid outcome market represents the job | Testnet conformance establishes creation, trading, and resolution behavior |
| Contract mirror | A HyperEVM contract records escrow, positions, or resolution while the offchain service provides the orderbook | Testnet deployment, verifier interface, and reconciliation pass |

The first milestone is a no-value simulation using faucet assets or internal
credits. Every event records chain ID, RPC identity, contract or market
identifier, transaction hash, block reference, finality status, and Adapter
version. A transaction is `pending` until independently observed as confirmed.
Testnet state is never treated as proof of compute correctness.

## Stripe and Tempo payment roles

Stripe Connect supports marketplace flows including separate charges and
transfers. That can model a customer charge followed by a provider transfer
after accepted delivery. The platform remains exposed to fees, refunds, and
chargebacks under that arrangement. [Stripe Connect](https://docs.stripe.com/connect/separate-charges-and-transfers)

Stripe eligibility must be checked before production integration. Its
restricted-business guidance includes gambling, some prediction or advisory
services related to online gaming, and certain financial or crypto activities.
Actual eligibility depends on product design, jurisdiction, disclosures,
underwriting, and account review. [Stripe restricted businesses](https://stripe.com/legal/restricted-businesses)

The first Stripe path is ordinary work procurement: the customer pays for a
specified service and the provider receives a transfer after accepted
delivery. A tradable real-money prediction product requires a separate legal,
payments, and market-structure review.

Tempo describes stablecoin transfers, payment memos, sponsored fees, and
machine-payment flows. It is a candidate stablecoin Adapter for provider
payouts and agent-to-service payments. [Tempo documentation](https://docs.tempo.xyz/)

The Tempo Adapter binds the job and payment authorization digests, sender and
recipient, token and amount, memo, chain and transaction identity, confirmation
rule, and duplicate or refund state. Stripe and Tempo are alternative rails.
A single payout intent needs one idempotency key and a durable state machine so
one job cannot pay on both rails.

## Resolution and evidence protocol

```text
JobDraft -> Frozen -> Listed -> BidAccepted -> Funded -> Executing
  -> Submitted -> UnderReview
  -> Accepted or Rejected or Unknown
  -> Resolved -> Paid or Refunded or Disputed
```

The result packet binds the job and specification digests; provider and
execution identity; program, model, runtime, and input commitments; output and
artifact digests; resource and deadline accounting; evaluator version and
assessment-set commitment; independent validator identity; result status and
claim ceiling; market resolution reference; and payment authorization digest.

`Unknown` is the fail-closed state for an unresolvable or integrity-failed
attempt until a separately authorized dispute path handles it. It must not be
silently converted to success, failure, or a zero-priced result.

The market oracle reports an evidence state. It does not infer that an artifact
is valuable because it ran, that inputs were truthful because they were
committed, or that a provider was aligned because it was profitable.

## Manipulation and market-health controls

Controls include freezing the specification before trading; separating
provider execution and trading identities where permitted; disclosing conflicts;
capping self-trading and position size; requiring liquidity and an observation
window; using a bounded lagging TWAP or equivalent instead of the last trade;
rejecting prices outside a predeclared band; maintaining a fallback resolver;
preventing positions from changing evaluator thresholds; limiting submissions;
keeping assessment data committed and private; and preserving a dispute window
before irreversible payout.

TWAP reduces some last-second manipulation but does not solve thin liquidity,
collusion, insider information, oracle capture, or outcome-dependent work
behavior. Keep the market advisory until repeated-job evidence supports a
bounded contractual use.

Track forecast calibration, Brier or log score, price impact, spread, depth,
time to first bid, provider-selection lift, accepted-result lift, cost
efficiency, manipulation loss, resolution latency, dispute rate, and duplicate,
stuck, refunded, or charged-back payment rate.

Compare three arms on the same job families:

1. fixed bounty with ordinary provider selection;
2. competitive auction without outcome trading;
3. outcome-priced work market with the same provider pool.

Synthetic and public-only development jobs come first. Testnet credits,
simulated agents, and replayed transactions are not production market
evidence.

## Parallel build waves

### Wave 0 — contract and jurisdiction freeze

State slice:
`hsai-proof-carrying-capability-bounded-agent-platform-outcome-priced-work-market-contract-v1`.

Freeze the job schema, outcome semantics, price-to-work rule, payment states,
testnet chain identity, data-retention policy, dispute rules, allowed users,
and claim ceiling. Classify ordinary work procurement separately from any
tradable outcome product. No live funds or market creation occur here.

Exit gate: every authority transition, external dependency, and unresolved
state has a named owner and deterministic disposition.

### Wave 1 — market and evidence contracts

State slice:
`hsai-proof-carrying-capability-bounded-agent-platform-outcome-priced-work-market-contracts-v1`.

Implement pure-data Interfaces for `WorkJobV1`, `OutcomeMarketV1`,
`MarketObservationV1`, `WorkEvidencePacketV1`, `ResolutionDecisionV1`, and
`PayoutIntentV1`. Add canonical digests, replay protection, idempotency keys,
state transitions, rejection immutability, and an independent checker.

Exit gate: malformed, stale, contradictory, duplicate, and out-of-order input
cannot produce an accepted resolution or duplicate payout intent.

Current local evidence: four contract tests and three independent-checker tests
pass, including a complete local work-to-payout path. The observed market
signal remains `advisory_only=true`, and every payout intent remains
`PendingAuthorization` with `authority_granted=false`.

The next bounded implementation slice is also present in
`hsai-outcome-work-market-adapters` under state slice
`hsai-proof-carrying-capability-bounded-agent-platform-outcome-priced-work-market-adapters-v1`.
It prepares and reconciles local Hyperliquid testnet observation records and
Stripe/Tempo-compatible payout records without network calls, transaction
signing, value movement, or authority. One focused test covers the complete
dry-run path and rejects a payment transition back to `Prepared`.

The offchain simulation slice is implemented in
`hsai-outcome-work-market-offchain` under state slice
`hsai-proof-carrying-capability-bounded-agent-platform-offchain-work-market-v1`.
It provides an append-only local event log, deterministic replay, advisory
budget projection, and explicit fixed-bounty/provider-auction comparison
records. It now also validates provider bids, deterministically selects the
lowest eligible bid with stable tie-breaks, records fills, and rejects duplicate
or post-close fills during replay. Its three focused tests cover replay
determinism, post-close rejection, and matching. It uses no external credits,
provider execution, or settlement.

Provider capacity is enforced across fills: each allocation carries unit
count, repeated matches consume the quoted capacity, exhausted quotes are
skipped, and aggregate over-allocation fails closed during replay.

The event log also has a canonical JSON encode/decode boundary that preserves
the log digest and replay projection across readback; malformed bytes fail
closed. This is restart-readiness evidence for the local contract only, not a
durable production journal or cross-process consistency guarantee.

The caller-owned file-backed journal is implemented under state slice
`hsai-proof-carrying-capability-bounded-agent-platform-offchain-journal-v1`.
`OffchainMarketLogFileStore` provides canonical readback, atomic temporary-file
replacement, expected-digest compare-and-replace, and fail-closed malformed,
stale, invalid, and orphan-temporary handling. Its claim ceiling is local
deterministic file-persistence contract evidence only; it does not provide
cross-process linearizability or live settlement.

### Wave 2 — offchain market simulation

State slice:
`hsai-proof-carrying-capability-bounded-agent-platform-offchain-work-market-v1`.

Build listings, orders or quotes, liquidity, market data, and resolution
projection using internal credits and deterministic fixtures. Implement
advisory pricing and baseline comparison against fixed bounties and auctions.

Exit gate: an independent replay reconstructs every price, fill, resolution,
and projection from the event log without hidden mutable state.

The current implementation is a deterministic event-log simulation for this
wave. Richer listings, multi-unit capacity allocation, liquidity provision,
auction clearing, and independent replay of a richer fill model remain future
work.

An implementation-diverse replay checker is implemented in
`hsai-outcome-work-market-offchain-checker` under state slice
`hsai-proof-carrying-capability-bounded-agent-platform-offchain-work-market-checker-v1`.
It independently validates event ordering, quote/fill bindings, close
semantics, capacity accounting, and projection fields. Its two focused tests accept a valid
projection and reject forged projection or event data. This remains local
contract evidence, not independent economic or production validation.

### Wave 3 — Hyperliquid testnet Adapter

State slice:
`hsai-proof-carrying-capability-bounded-agent-platform-hyperliquid-testnet-outcome-adapter-v1`.

Implement testnet configuration, wallet boundary, native or contract-mirror
selection, event ingestion, confirmation tracking, reconciliation, and failure
recovery. Use a dedicated testnet identity and test-only assets. Conformance
cases cover identity mismatch, unknown market, duplicate event, stale
confirmation, partial fill, resolution disagreement, projection outage, and
Adapter or market digest drift.

The current adapter crate provides only the dry-run configuration, observation,
confirmation, and payment-reconciliation records. Live RPC/API ingestion,
wallet custody, signing, and testnet deployment remain future work.

Exit gate: restart and reconciliation tests produce the same projection, and
no testnet event can authorize a real payment by itself.

### Wave 4 — Stripe and Tempo payment Adapters

State slice:
`hsai-proof-carrying-capability-bounded-agent-platform-work-market-payments-v1`.

Implement both rails behind a common payout Interface. Start with Stripe test
mode and a Tempo nonproduction environment. Use one payout intent, one
idempotency key, and one durable state machine per job. Model refunds,
chargebacks, failed transfers, stuck blockchain transactions, wrong recipients,
wrong amounts, and duplicate attempts.

The current adapter crate stops at a local `Prepared` record and accepts an
external reference only as a caller-supplied reconciliation fixture. It does
not call Stripe or Tempo and cannot authorize a payout.

Exit gate: a job cannot reach `Paid` without accepted evidence and an
authorized payout intent; reconciliation remains correct after restart.

### Wave 5 — provider and buyer pilot

State slice:
`hsai-proof-carrying-capability-bounded-agent-platform-outcome-priced-work-pilot-v1`.

Run deterministic work classes with known validators, such as proof
generation, optimization, test-suite repair, or structured data transformation.
Keep pricing advisory and compare the three baseline arms. Publish aggregates
only.

Exit gate: the market improves a preregistered metric without exceeding the
declared budgets for critical failure, privacy, duplicate payment, or disputes.

### Wave 6 — bounded contractual use and public release

State slice:
`hsai-proof-carrying-capability-bounded-agent-platform-public-work-market-v1`.

Only after the pilot passes may a frozen market statistic determine a bounded
bonus, bond, review allocation, or milestone amount. Keep hard payout caps,
manual release authority, dispute windows, and a kill switch. Public release
also requires licensing, identity and jurisdiction review, privacy retention,
market-abuse controls, payment-rail eligibility, incident response, and
recurring claim review.

Exit gate: external red-team, payment reconciliation, market manipulation,
privacy, resolution, and release-freeze reviews pass.

## Responsibilities and failure policy

The existing parallel lanes remain intact. Security owns capability scope for
listing, bidding, execution, resolution, and payout. Evidence owns job,
artifact, evaluator, custody, resolution, and payment bindings. Evaluation
owns work families, hidden assessment, calibration, manipulation, and baseline
arms. Runtime owns sandbox, egress, secrets, resource, and receipt Adapters.
The market lane owns offchain pricing, Hyperliquid mirroring, and reconciliation.
The payment lane owns Stripe and Tempo test flows and payout reconciliation.

```text
missing evidence       -> Unknown and quarantine
stale market state      -> freeze projection
unconfirmed transaction -> Pending, never Paid
payment mismatch        -> freeze payout and incident record
validator disagreement  -> dispute or Unknown
market manipulation     -> freeze price-to-work rule
provider timeout        -> deterministic failure or refund
Stripe chargeback       -> payment incident; preserve evidence state
Tempo failure           -> retry by idempotency key or refund policy
Hyperliquid outage      -> preserve offchain state; no forced resolution
```

Each lane receives one directory boundary, one state slice, one Interface,
one claim ceiling, one dependency list, and one exit gate. Shared README and
task-ledger updates are coordinator-owned integration mutations.

## Definition of success

One narrow work class must demonstrate, with independently replayable records,
that buyers can publish immutable acceptance policies, providers can bid and
execute within declared capabilities, the offchain market can reproduce a
price signal, Hyperliquid testnet can mirror or run the intended mechanics,
evidence validation resolves the outcome independently of trading, and Stripe
or Tempo can execute exactly one authorized test payment. The pilot must also
measure whether the market improves a preregistered allocation or pricing
metric while containing manipulation, evaluator gaming, privacy, and payment
failures.

## Explicit nonclaims

This plan does not claim that outcome markets are accurate, calibrated, or
manipulation-resistant; that prices establish truth, usefulness, alignment, or
human benefit; that Hyperliquid currently supports our custom work market on
testnet; that testnet collateral secures production funds; that Stripe will
approve a tradable prediction product; that Tempo and Stripe balances are
interchangeable; that payment confirmation proves work correctness; that any
ZK, FHE, MPC, or TEE receipt exists; that an offchain index is authoritative
without replay and reconciliation; or that this repository currently
integrates Hyperliquid, Stripe, Tempo, or a live provider.

## Source register reviewed 2026-09-07

- Hyperliquid [HIP-4](https://hyperliquid.gitbook.io/hyperliquid-docs/hyperliquid-improvement-proposals-hips/hip-4-outcome-markets), [HyperEVM](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/hyperevm), and [API](https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api).
- Stripe [Connect](https://docs.stripe.com/connect/separate-charges-and-transfers) and [restricted businesses](https://stripe.com/legal/restricted-businesses).
- Tempo [payments](https://docs.tempo.xyz/).
- Futarchy Labs [overview](https://docs.futarchy.fi/), MetaDAO [decision markets](https://docs.metadao.fi/governance/overview), Caritas [work experiment](https://caritas.ventures/blog/bounties-prediction-markets-llms-oh-my-christian-ulstrup-yba6e/), Math Market [research](https://openreview.net/pdf?id=uQPYAOHyPf), and Diagon [research](https://arxiv.org/abs/2604.06688).
- Boundless [proving stack](https://docs.boundless.network/provers/proving-stack) and [proof lifecycle](https://docs.boundless.network/developers/proof-lifecycle).

The register provides design context and integration targets. It does not
grant redistribution rights, establish availability beyond the cited source,
or raise any repository claim ceiling.
