# Compose PRD

## Verifiable Intelligence for Reflexive Markets

**Version:** 0.2\
**Status:** Working product specification\
**Primary objective:** Build a reproducible research system that can
determine whether heterogeneous information flows contain predictive
information not yet incorporated into market prices.\
**Initial deployment:** Historical replay → live shadow mode → paper
trading → tightly risk-limited live experimentation.

------------------------------------------------------------------------

## 1. Executive Summary

Compose is a continual-learning evaluation and market-intelligence
system built around three core subsystems:

1.  **Temporal Lake / Crowd Engine** --- reconstructs what information
    was observable at a given point in time and estimates how beliefs,
    narratives, attention, and information propagate through
    heterogeneous populations.
2.  **Statebook** --- maps heterogeneous tradable instruments onto
    common latent world states and estimates the probability
    distributions implied by capital.
3.  **Compose Evaluation OS** --- evaluates agents, models, data
    transformations, forecasts, and strategy updates through time, with
    reproducibility and cryptographic commitments.

The primary research object is the divergence between informational
belief and priced belief:

\[ D_t(X)=P\_{`\text{info}`{=tex},t}(X)-P\_{`\text{capital}`{=tex},t}(X)
\]

Compose does **not** assume that divergence is alpha. It learns whether
particular divergences, sources, cohorts, regimes, and horizons predict
subsequent repricing or eventual outcomes.

The MVP must answer one question reliably:

> Given a state (X) and timestamp (t), can we reconstruct exactly what
> Compose could have known at (t), generate a forecast, commit to it,
> and score it later without temporal leakage?

If this cannot be guaranteed, more sophisticated modeling should not
proceed.

------------------------------------------------------------------------

## 2. Goals

### 2.1 Product goals

-   Maintain a temporally correct, provenance-aware stream of market and
    information events.
-   Represent multiple financial instruments as claims over common
    states of the world.
-   Estimate crowd beliefs independently from market-implied
    probabilities.
-   Produce timestamped, versioned probability forecasts.
-   Evaluate forecast calibration, information value, robustness, and
    economic utility through time.
-   Support deterministic historical replay.
-   Support live shadow forecasting before any capital deployment.
-   Maintain immutable experiment/model/data lineage.
-   Eventually support privacy-preserving/verifiable evaluation of
    proprietary data and models.

### 2.2 Research goals

Determine whether Compose can identify:

-   information that has not yet propagated into prices;
-   cohorts that systematically lead specific state classes;
-   markets or instruments that lead other markets;
-   regime-dependent information propagation;
-   differences between genuine learning and benchmark/evaluator
    exploitation;
-   degradation, forgetting, calibration drift, and correlated agent
    failure;
-   reflexivity as Compose moves from observer to participant.

### 2.3 Non-goals for MVP

-   High-frequency trading.
-   Full internet ingestion.
-   Fully autonomous capital allocation.
-   Full zkML proof of arbitrary LLM inference.
-   General-purpose sentiment trading.
-   Building a proprietary distributed database from scratch.
-   Claiming alpha based on backtests alone.

------------------------------------------------------------------------

## 3. Core Concepts

### World State

A resolvable or measurable variable about the world.

``` yaml
state_id: btc_usd_2026_12_31
definition: BTC/USD reference price at resolution timestamp
state_space: continuous
resolution_source: canonical_reference
resolution_time: 2026-12-31T23:59:59Z
dependencies: []
```

States may be binary, categorical, ordinal, continuous, or structured.

### Claim

A financial instrument or prediction contract with a payoff dependent on
a state.

\[
f_i(X)=`\text{payoff of claim }`{=tex}i`\text{ if state }`{=tex}X`\text{ occurs}`{=tex}
\]

### Statebook

A mapping from claims and prices to an implied state distribution:

\[ Q_t(X)=P\_{`\text{capital}`{=tex},t}(X) \]

### Crowd State

A representation of beliefs, attention, narrative, credibility, and
velocity across populations:

\[ C\_{c,t}=(B\_{c,t},A\_{c,t},V\_{c,t},K\_{c,t}) \]

### Compose Forecast

A versioned forecast made using only information observable before its
commitment timestamp.

### Experiment

A fully specified replay or live run containing:

-   data snapshot/version;
-   model/agent versions;
-   state definitions;
-   transformations;
-   prompts/configuration;
-   forecast outputs;
-   evaluation methodology;
-   results.

------------------------------------------------------------------------

## 4. System Architecture

``` text
External Sources
      |
      v
+--------------------+
| Source Connectors  |
+--------------------+
      |
      v
+--------------------+
| Event Bus          |
| Kafka / Redpanda   |
+--------------------+
      |
      v
+--------------------+
| Normalization      |
| Dedup / Provenance |
| Entity Resolution  |
+--------------------+
      |
      +--------------------------+
      |                          |
      v                          v
+--------------------+    +--------------------+
| Hot Store          |    | Immutable Lake     |
| ClickHouse         |    | Iceberg/Object     |
+--------------------+    +--------------------+
      |                          |
      +-------------+------------+
                    |
                    v
             +--------------+
             | State Compiler|
             +--------------+
               /          \
              v            v
       +------------+  +------------+
       | Crowd      |  | Statebook  |
       | Engine     |  | Engine     |
       +------------+  +------------+
              \            /
               v          v
             +--------------+
             | Agent Layer  |
             +--------------+
                    |
                    v
             +--------------+
             | Compose Eval |
             +--------------+
                    |
          +---------+---------+
          |                   |
          v                   v
    Shadow/Paper         Proof/Commitment
       Trading              Registry
```

------------------------------------------------------------------------

## 5. Temporal Event Layer

### 5.1 Canonical schema

``` json
{
  "event_id": "uuid",
  "source_id": "source-native-id",
  "source_type": "trade|book|post|article|filing|resolution|metric",
  "event_time": "source asserted occurrence time",
  "published_time": "optional publication time",
  "ingest_time": "arrival at ingestion service",
  "observable_time": "earliest time agents may consume event",
  "actor_id": "nullable",
  "entity_ids": [],
  "state_candidates": [],
  "market_ids": [],
  "payload_uri": "immutable object location",
  "payload_hash": "sha256",
  "schema_version": 1,
  "provenance": {},
  "quality": {}
}
```

### 5.2 Temporal invariant

An agent executing at time (t) may only consume:

\[ e_i `\quad `{=tex}`\text{where}`{=tex}
`\quad `{=tex}observable_time(e_i)`\leq `{=tex}t \]

`observable_time` is not automatically equal to publication time. It
represents when the system actually had access to the information.

### 5.3 Required properties

-   append-oriented;
-   idempotent ingestion;
-   source-native sequence preservation when available;
-   replayable;
-   explicit late-arriving events;
-   corrections represented as new events, not silent rewrites;
-   payload hashes;
-   clock-skew monitoring;
-   connector health telemetry.

------------------------------------------------------------------------

## 6. Statebook

### 6.1 Purpose

Statebook converts fragmented market prices into coherent claims about
shared world states.

### 6.2 Core entities

``` text
State
Claim
Instrument
Venue
MarketObservation
PayoffFunction
StateDistribution
Dependency
Resolution
```

### 6.3 State graph

States may depend on one another:

``` text
Fed cuts by Dec
      |
      +--> 2Y yield range
      |
      +--> BTC > threshold
      |
      +--> recession probability
```

Dependencies are hypotheses, not assumed causal truths, and must be
versioned.

### 6.4 Pricing layer

For observed instrument (i):

\[ p\_{i,t}`\approx `{=tex}E\_{Q_t}\[f_i(X)\] \]

Statebook solves for a coherent (Q_t), subject to:

-   observed bid/ask rather than midpoint alone;
-   liquidity;
-   fees;
-   settlement differences;
-   venue risk;
-   resolution definitions;
-   arbitrage constraints;
-   uncertainty.

The output must include uncertainty rather than a false point estimate.

``` json
{
  "state_id": "...",
  "timestamp": "...",
  "distribution": {},
  "credible_interval": {},
  "source_claims": [],
  "fit_error": 0.0,
  "liquidity_score": 0.0,
  "method_version": "..."
}
```

### 6.5 Cross-venue identity

Two superficially similar markets are not necessarily the same claim.
Statebook must compare:

-   resolution wording;
-   time zone;
-   reference source;
-   cancellation rules;
-   edge cases;
-   settlement date;
-   counterparty/venue constraints.

A semantic match should never silently imply financial equivalence.

------------------------------------------------------------------------

## 7. Crowd Engine

### 7.1 Purpose

Estimate information-network beliefs separately from capital-market
beliefs.

### 7.2 Pipeline

``` text
Raw information
   ↓
Deduplication
   ↓
Entity/state linking
   ↓
Narrative/event clustering
   ↓
Actor/cohort representation
   ↓
Belief extraction
   ↓
Attention + velocity
   ↓
Credibility calibration
   ↓
Crowd state
```

### 7.3 Cohorts

Cohorts should initially be inferred conservatively and can include:

-   domain experts;
-   journalists;
-   retail communities;
-   macro commentators;
-   crypto-native analysts;
-   security researchers;
-   on-chain actors;
-   prediction-market participants;
-   institutional/public research;
-   automated agents.

Avoid demographic inference where it is unnecessary. Cohorts should
primarily describe observable information roles or behavior.

### 7.4 Belief representation

For binary state (X):

\[ B\_{c,t}(X)=P_c(X`\mid `{=tex}I\_{`\le `{=tex}t}) \]

Not every source expresses a numeric probability. The engine may infer a
distribution, but must preserve:

-   source evidence;
-   extraction uncertainty;
-   model version;
-   direct vs inferred belief.

### 7.5 Credibility

Credibility is state-class and horizon dependent:

\[ K(c,d,h,t) \]

A security researcher can have high historical predictive value for
exploit events while carrying no special weight for elections.

### 7.6 Information lead graph

Learn relationships such as:

\[ c_i `\xrightarrow[\Delta t,d]{}`{=tex} m_j \]

where a cohort/source historically leads a market or cohort for domain
(d).

The graph must be learned strictly from past data relative to each
evaluation point.

------------------------------------------------------------------------

## 8. State Compiler

The State Compiler creates bounded, reproducible model inputs.

### Input

``` json
{
  "state_id": "...",
  "as_of": "...",
  "horizon": "...",
  "compiler_version": "..."
}
```

### Output

``` json
{
  "state_definition": {},
  "capital_distribution": {},
  "crowd_distribution": {},
  "cohort_views": [],
  "market_microstructure": [],
  "narratives": [],
  "attention": {},
  "recent_events": [],
  "cross_market_features": [],
  "data_quality": {},
  "provenance_root": "..."
}
```

Every snapshot receives a content hash.

This is the unit agents should consume and the unit experiments should
commit to.

------------------------------------------------------------------------

## 9. Agent System

### 9.1 Initial forecasters

-   Market-implied baseline
-   News forecaster
-   Crowd/social forecaster
-   Microstructure forecaster
-   Cross-market forecaster
-   Historical analogue forecaster
-   Synthesis forecaster

### 9.2 Forecast contract

Every forecast returns:

``` json
{
  "forecast_id": "...",
  "state_id": "...",
  "as_of": "...",
  "horizon": "...",
  "distribution": {},
  "confidence": {},
  "evidence_refs": [],
  "agent_version": "...",
  "snapshot_hash": "...",
  "created_at": "..."
}
```

Agents cannot silently modify forecasts after commitment.

### 9.3 Ensemble

The synthesis layer should learn weights through historical
out-of-sample performance rather than rely solely on an LLM to choose
whose opinion sounds convincing.

------------------------------------------------------------------------

## 10. Compose Evaluation OS

### Forecast metrics

Binary/categorical:

-   Brier score
-   log loss
-   calibration error
-   reliability diagrams
-   resolution-conditioned accuracy

Continuous:

-   CRPS
-   quantile loss
-   calibration/coverage
-   distributional distance

### Market information metrics

Define:

\[ D_t=P\_{`\text{Compose}`{=tex},t}-P\_{`\text{Statebook}`{=tex},t} \]

Measure whether (D_t) predicts:

1.  final resolution;
2.  future price movement;
3.  time-to-incorporation;
4.  magnitude of repricing.

A critical metric:

\[ Lead\_{`\Delta`{=tex}} =
E\[(Q\_{t+`\Delta`{=tex}}-Q_t)`\cdot `{=tex}`\operatorname{sign}`{=tex}(D_t)\]
\]

with appropriate normalization and statistical testing.

### Continual-learning metrics

For model version (A_t):

-   acquisition;
-   retention;
-   forward transfer;
-   backward transfer;
-   calibration drift;
-   regime robustness;
-   source dependence;
-   cohort dependence;
-   catastrophic forgetting;
-   evaluator awareness;
-   data leakage susceptibility.

### Economic metrics

Only after forecast quality is established:

-   expected value after costs;
-   realized P&L;
-   Sharpe/Sortino;
-   drawdown;
-   turnover;
-   slippage;
-   liquidity utilization;
-   tail exposure;
-   correlation to baseline factors.

P&L must never be the sole model-selection metric.

------------------------------------------------------------------------

## 11. Replay Engine

Replay is a first-class product.

``` text
replay(start, end, speed, source_set, model_version)
```

At replay time (t):

1.  release only events with `observable_time <= t`;
2.  update Statebook;
3.  update Crowd Engine;
4.  compile state snapshots;
5.  run scheduled agents;
6.  commit forecasts;
7.  advance clock;
8.  score forecasts only when information becomes observable.

Replay output must be deterministic given fixed source snapshots, code,
configuration, and seeds.

------------------------------------------------------------------------

## 12. Experiment Registry

Every experiment stores:

``` yaml
experiment_id:
git_commit:
container_digest:
data_snapshot:
source_versions:
statebook_version:
crowd_engine_version:
compiler_version:
agent_versions:
prompt_hashes:
random_seeds:
start_time:
end_time:
evaluation_config:
artifact_root:
result_hash:
```

No result without lineage should be accepted into the canonical
benchmark history.

------------------------------------------------------------------------

## 13. Cryptographic Commitments and ZK Roadmap

### V0

Hash commitments:

\[ C=H(snapshot_hash `\parallel `{=tex}model_hash
`\parallel `{=tex}forecast `\parallel `{=tex}timestamp) \]

### V1

Merkle commitments over:

-   state snapshots;
-   forecast batches;
-   benchmark datasets;
-   experiment traces.

### V2

Prove statements such as:

-   benchmark was fixed before evaluation;
-   forecast existed before resolution;
-   score was calculated correctly;
-   no excluded observation entered a replay window.

### V3

Selective ZK evaluation for proprietary models/data where proving cost
is justified.

Full LLM inference proof is explicitly not an MVP dependency.

------------------------------------------------------------------------

## 14. Trading / Decision Layer

Trading is downstream from forecasting.

``` text
Forecast
  ↓
Edge estimate
  ↓
Calibration adjustment
  ↓
Transaction costs
  ↓
Liquidity
  ↓
Uncertainty
  ↓
Portfolio correlation
  ↓
Risk constraints
  ↓
No trade / paper position
```

For binary contract price (q) and calibrated Compose probability (p),
raw probability edge is:

\[ e=p-q \]

but executable expected value must incorporate payoff mechanics, fees,
spread, slippage, venue risk, model uncertainty, and position limits.

### Safety gates

-   default `NO_LIVE_EXECUTION=true`;
-   separate credentials for read vs trade;
-   global kill switch;
-   per-market limits;
-   daily loss limits;
-   max portfolio exposure;
-   venue limits;
-   stale-feed lockout;
-   model-version allowlist;
-   manual approval before initial live phase.

------------------------------------------------------------------------

## 15. API Surface

Illustrative endpoints:

``` text
POST /v1/events
GET  /v1/states/{id}
GET  /v1/states/{id}/snapshot?as_of=
GET  /v1/statebook/{id}?as_of=
GET  /v1/crowd/{id}?as_of=
POST /v1/forecasts
GET  /v1/forecasts/{id}
POST /v1/replays
GET  /v1/replays/{id}
GET  /v1/evals/{id}
GET  /v1/lineage/{artifact_hash}
```

Internal event topics:

``` text
raw.*
normalized.*
statebook.observation
crowd.event
state.snapshot
forecast.created
forecast.committed
forecast.scored
experiment.completed
```

------------------------------------------------------------------------

## 16. MVP Scope

### Domain

Start with a bounded set of liquid, clearly resolving prediction-market
states plus directly related public market data.

### Minimum source set

-   one or two prediction-market venues;
-   one high-quality news/event feed;
-   one social/community source where permitted;
-   relevant spot/futures/market data;
-   canonical resolution sources.

### MVP deliverables

-   ingestion adapters;
-   canonical event schema;
-   ClickHouse hot store;
-   immutable raw lake;
-   state registry;
-   claim/state mappings;
-   basic Statebook probability normalization;
-   replay engine;
-   state compiler;
-   two baseline forecasters;
-   forecast commitment service;
-   scoring/evaluation dashboard;
-   live shadow mode.

------------------------------------------------------------------------

## 17. Build Plan

### Sprint 0 --- Temporal correctness

**Target:** 3--5 days

-   repository structure;
-   event schema;
-   source adapter interface;
-   one prediction-market connector;
-   event bus;
-   ClickHouse tables;
-   immutable raw storage;
-   deterministic replay skeleton;
-   observability.

**Exit test:** Query any timestamp and reconstruct the exact order of
observable events.

### Sprint 1 --- Statebook baseline

**Target:** 1 week

-   state registry;
-   claim registry;
-   resolution semantics;
-   cross-market mappings;
-   binary market probability normalization;
-   bid/ask and liquidity handling;
-   Statebook snapshots.

**Exit test:** Reconstruct state-implied probabilities through
historical time.

### Sprint 2 --- Information layer

**Target:** 1 week

-   news connector;
-   social/community connector;
-   deduplication;
-   entity/state linker;
-   narrative clusters;
-   baseline belief extraction;
-   Crowd Engine snapshot.

**Exit test:** Generate a reproducible crowd state for each tracked
state.

### Sprint 3 --- Forecast/eval loop

**Target:** 1 week

-   baseline agents;
-   state compiler;
-   forecast schema;
-   commitment registry;
-   Brier/log-loss scoring;
-   lead/lag analysis;
-   walk-forward experiment harness.

**Exit test:** Complete historical walk-forward experiment with zero
known leakage.

### Sprint 4 --- Live shadow

**Target:** 1--2 weeks

-   continuous snapshots;
-   scheduled forecasting;
-   live commitment;
-   monitoring;
-   dashboard;
-   incident logging.

**Exit test:** Accumulate genuine pre-outcome forecasts without capital.

### Sprint 5 --- Paper portfolio

Only after sufficient live-shadow evidence.

------------------------------------------------------------------------

## 18. Testing

### Data tests

-   duplicate ingestion;
-   out-of-order events;
-   late events;
-   malformed source timestamps;
-   source corrections;
-   dropped WebSocket messages;
-   stale source;
-   reconnect gaps.

### Temporal leakage tests

Automated invariant:

``` python
assert max(input.observable_time) <= forecast.as_of
```

Additional red-team tests intentionally inject future observations and
require the system to reject them.

### Statebook tests

-   equivalent payoff consistency;
-   contradictory claims;
-   crossed implied probabilities;
-   illiquid markets;
-   settlement mismatch;
-   venue outage.

### Model tests

-   calibration;
-   source ablation;
-   cohort ablation;
-   random-label control;
-   shuffled-time control;
-   delayed-feed control;
-   market-only baseline;
-   naive crowd baseline.

If Compose cannot beat deliberately simple baselines out of sample,
complexity should be removed rather than rationalized.

------------------------------------------------------------------------

## 19. Success Criteria

### Infrastructure

-   deterministic replay;
-   complete event provenance;
-   measurable ingestion lag;
-   no known temporal leakage;
-   versioned snapshots and models.

### Forecasting

Compose must outperform appropriate market-only and naive baselines out
of sample on proper scoring rules.

### Information lead

When Compose disagrees with Statebook, the disagreement should contain
statistically defensible information about subsequent price movement
and/or resolution.

### Generalization

Performance must persist across held-out time windows and preferably
held-out state classes.

### Deployment

No live trading until shadow-mode results demonstrate stable calibration
and the risk layer has been independently tested.

------------------------------------------------------------------------

## 20. Key Risks

### Data licensing and source durability

Mitigation: adapter abstraction, explicit provenance, replaceable
sources, compliance review.

### Hindsight contamination

Mitigation: observable-time semantics, immutable snapshots, replay
invariants, forecast commitments.

### Overfitting

Mitigation: walk-forward evaluation, held-out regimes, simple baselines,
predeclared metrics.

### False crowd consensus

Mitigation: source diversity, bot/duplication controls, cohort
decomposition, uncertainty.

### Market microstructure distortion

Mitigation: bid/ask, depth, costs, liquidity and venue constraints.

### Reflexivity

Mitigation: shadow mode, impact estimates, size limits, evaluator
separated from trader.

### Correlated agent errors

Mitigation: agent specialization, independent scoring, source ablations,
ensemble diversity metrics.

------------------------------------------------------------------------

## 21. Open Questions

-   What is the canonical ontology for states and dependencies?
-   How should continuous state distributions be recovered across
    heterogeneous instruments?
-   Which information sources provide sufficiently precise observable
    timestamps?
-   How do we distinguish copied information from independent evidence?
-   How should cohort identity persist through time?
-   What constitutes statistically sufficient evidence of information
    lead?
-   When should Statebook uncertainty dominate the apparent crowd/market
    divergence?
-   Which parts of the evaluation pipeline justify ZK proving versus
    ordinary commitments?
-   How should evaluator-awareness be operationalized for market agents?
-   At what deployment scale does Compose's own activity become a
    material part of the state?

------------------------------------------------------------------------

## 22. Immediate Engineering Decision

Do not begin with a large agent framework.

Begin with:

``` text
ONE state family
ONE market connector
ONE temporal event schema
ONE replay engine
ONE Statebook baseline
ONE market-only forecaster
```

Then prove temporal correctness.

The first meaningful milestone is not profitable paper trading. It is:

> **We can make a forecast at historical or live time (t), prove exactly
> what information was available to the system at (t), and reproduce the
> result later.**

Everything else compounds from that foundation.
