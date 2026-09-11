# Compose ASAP Build Roadmap

## 30-Day Research MVP

**Objective:** Get from zero to a temporally correct live shadow
forecasting system as quickly as possible without compromising the
validity of the experiment.

------------------------------------------------------------------------

## Guiding Rule

Do not optimize models before the temporal substrate is trustworthy.

The critical path is:

``` text
Feed
→ Temporal correctness
→ Replay
→ Statebook
→ State Compiler
→ Baseline forecasts
→ Crowd Engine
→ Evaluation
→ Live shadow
```

------------------------------------------------------------------------

## Days 1--3 --- Repository + Event Backbone

### Deliverables

-   monorepo;
-   Docker Compose local stack;
-   Postgres for metadata;
-   ClickHouse for hot analytical events;
-   Redpanda/Kafka;
-   object storage;
-   canonical event schema;
-   connector interface;
-   structured logging;
-   basic telemetry.

### Suggested repo

``` text
compose/
├── apps/
│   ├── api/
│   ├── dashboard/
│   └── worker/
├── services/
│   ├── ingest/
│   ├── normalizer/
│   ├── replay/
│   ├── statebook/
│   ├── crowd/
│   ├── compiler/
│   ├── forecaster/
│   └── evaluator/
├── packages/
│   ├── schemas/
│   ├── states/
│   ├── provenance/
│   └── clients/
├── research/
│   ├── notebooks/
│   ├── experiments/
│   └── benchmarks/
├── infra/
└── docs/
```

### Hard requirement

Every incoming observation gets:

``` text
event_time
ingest_time
observable_time
payload_hash
```

------------------------------------------------------------------------

## Days 3--5 --- First Market Feed

Choose one initial prediction-market venue/domain.

Build:

-   market discovery;
-   contract metadata;
-   order-book snapshots/updates;
-   trades;
-   resolutions;
-   reconnect logic;
-   sequence-gap detection;
-   raw payload archive.

### Exit condition

Historical query:

> Show me everything Compose could observe between 14:32:00 and
> 14:32:10.

must be reliable.

------------------------------------------------------------------------

## Days 5--7 --- Replay Engine

Implement virtual clock.

``` text
ReplayClock
EventCursor
SnapshotManager
ForecastScheduler
```

Features:

-   pause;
-   resume;
-   speed multiplier;
-   deterministic seed;
-   exact event ordering;
-   checkpoint;
-   replay from checkpoint.

### Exit condition

Two identical replay runs generate identical snapshot hashes.

------------------------------------------------------------------------

## Week 2 --- Statebook V0

Start with binary states.

### Components

-   state registry;
-   claim registry;
-   market→state mapping;
-   resolution rule storage;
-   bid/ask probability representation;
-   liquidity score;
-   cross-venue normalization.

### Statebook output

``` json
{
  "state_id": "example",
  "as_of": "...",
  "p_market": 0.63,
  "lower": 0.61,
  "upper": 0.65,
  "liquidity": 0.78,
  "claims": []
}
```

Do not overengineer continuous options surfaces in V0.

------------------------------------------------------------------------

## Week 2 --- Forecast Registry

Implement forecast API before sophisticated models.

``` text
POST /forecast
→ validate snapshot
→ store forecast
→ create commitment
→ immutable forecast record
```

Hash:

\[ H(state_id \|\| as_of \|\| snapshot_hash \|\| model_version \|\|
prediction) \]

This gives us a trustworthy history immediately.

------------------------------------------------------------------------

## Week 2 --- Baselines

Implement:

1.  Statebook current probability;
2.  Statebook momentum;
3.  historical base rate;
4.  simple news model.

These become permanent benchmark competitors.

------------------------------------------------------------------------

## Week 3 --- Crowd Feed V0

Add only a small number of high-signal information sources.

Pipeline:

``` text
information event
↓
dedupe
↓
entity linking
↓
state linking
↓
claim/belief extraction
↓
attention
↓
crowd snapshot
```

Do not start with millions of accounts.

Start with data quality and timing.

------------------------------------------------------------------------

## Week 3 --- Crowd Engine V0

Represent:

``` json
{
  "state_id": "...",
  "as_of": "...",
  "belief": 0.71,
  "uncertainty": 0.12,
  "attention": 0.84,
  "velocity": 0.27,
  "evidence": []
}
```

Then compare:

\[ D_t=P\_{`\text{crowd}`{=tex}}-P\_{`\text{statebook}`{=tex}}. \]

------------------------------------------------------------------------

## Week 3 --- Lead/Lag Research

For horizons:

``` text
1m
5m
15m
1h
6h
24h
resolution
```

test whether (D_t) predicts subsequent Statebook movement.

Generate heatmap/table:

``` text
domain × source/cohort × horizon × effect
```

This is one of the first outputs colleagues should inspect.

------------------------------------------------------------------------

## Week 4 --- Agent Ensemble

Only now introduce more capable agents.

Suggested initial roles:

``` text
market_agent
news_agent
crowd_agent
historical_agent
synthesis_agent
```

Every agent receives the same versioned StateSnapshot interface.

No unrestricted internet browsing during benchmark replay.

------------------------------------------------------------------------

## Week 4 --- Live Shadow Deployment

Deploy continuous system.

For every tracked state:

``` text
T0 ingest
T1 state compile
T2 forecast
T3 commitment
T4 future market observation
T5 score
```

Dashboard:

-   current Statebook;
-   current Compose forecast;
-   divergence;
-   calibration;
-   source health;
-   forecast history;
-   model version;
-   information lead;
-   unresolved forecasts.

------------------------------------------------------------------------

## Engineering Priorities

### P0

-   temporal correctness;
-   provenance;
-   deterministic replay;
-   source reliability;
-   baseline evaluation.

### P1

-   state mapping;
-   Crowd Engine;
-   ensemble forecasting;
-   experiment registry.

### P2

-   ZK proofs;
-   sophisticated graph inference;
-   continuous option-state surfaces;
-   autonomous execution;
-   distributed/federated ingestion.

------------------------------------------------------------------------

## Team Split

A four-person team could divide:

### Data/Infra

Feeds, event bus, ClickHouse, raw lake, replay.

### Markets/Statebook

State ontology, claims, pricing normalization, resolution semantics.

### ML/Research

Crowd Engine, forecasters, calibration, lead/lag experiments.

### Product/Eval

Experiment registry, dashboards, commitments, benchmark harness,
deployment.

With two people, combine Data+Markets and ML+Product.

------------------------------------------------------------------------

## Daily Research Artifact

Every day the system should automatically produce:

``` text
data health
source gaps
number of forecasts
calibration
Statebook baseline score
Compose score
largest divergences
resolved forecasts
lead/lag metrics
model/config changes
```

No undocumented model changes during a live evaluation window.

------------------------------------------------------------------------

## Day-30 Definition of Done

By day 30 we should be able to show a colleague:

1.  a live state;
2.  all information available to Compose at a historical timestamp;
3.  Statebook's probability at that timestamp;
4.  the Crowd Engine's estimate;
5.  Compose's precommitted forecast;
6.  what the market did afterward;
7.  the eventual resolution when available;
8.  exact model/data lineage;
9.  aggregate out-of-sample calibration and lead/lag statistics.

If we can do those nine things reliably, we have a research platform.

If the platform also demonstrates information lead, we have the
beginning of a trading hypothesis.
