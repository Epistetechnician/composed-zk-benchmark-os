# Compose Research & Benchmark Plan

## From Temporal Replay to Evidence of Information Lead

**Version:** 0.1

------------------------------------------------------------------------

## 1. Purpose

This document defines how we test Compose without fooling ourselves.

The primary failure mode in market ML is not inability to fit historical
data. It is producing convincing historical results that disappear when
exposed to real temporal constraints, realistic latency, regime change,
and transaction costs.

The benchmark program therefore proceeds in layers.

------------------------------------------------------------------------

## 2. Hypotheses

### H0 --- Market baseline

The current market-implied probability is as good as or better than
Compose.

### H1 --- Crowd information

A Crowd Engine built only from information observable at time (t)
improves proper scoring performance over simple baselines for at least
some state classes.

### H2 --- Information lead

The divergence

\[ D_t=P\_{`\text{Compose}`{=tex},t}-P\_{`\text{Statebook}`{=tex},t} \]

predicts subsequent Statebook movement over some horizon
(`\Delta`{=tex}).

### H3 --- Conditional lead

Information lead depends on domain, cohort, regime, liquidity, and
horizon.

### H4 --- Continual adaptation

A continually updated model improves performance without materially
degrading retention, calibration, or robustness.

### H5 --- Economic survival

Some statistically defensible forecast edge survives realistic execution
costs.

H5 is intentionally last.

------------------------------------------------------------------------

## 3. Benchmark Units

Every benchmark example is:

``` yaml
state_id:
as_of:
horizon:
snapshot_hash:
statebook_distribution:
crowd_snapshot:
forecast:
resolution_or_future_state:
model_version:
```

No benchmark item may contain information with
`observable_time > as_of`.

------------------------------------------------------------------------

## 4. Dataset Splits

Never use ordinary random train/test splitting for primary results.

Use:

1.  expanding-window walk-forward;
2.  rolling-window walk-forward;
3.  held-out calendar periods;
4.  held-out event/state classes;
5.  regime-held-out tests where practical.

Example:

``` text
Train:  Jan-Mar
Test:   Apr

Train:  Jan-Apr
Test:   May

Train:  Jan-May
Test:   Jun
```

------------------------------------------------------------------------

## 5. Baselines

### Probability baselines

-   current market price;
-   liquidity-weighted market price;
-   base rate;
-   market momentum;
-   market mean reversion.

### Information baselines

-   bag-of-words/news sentiment;
-   equal-weight crowd sentiment;
-   simple mention velocity;
-   simple source-count surprise.

### Agent baselines

-   single general LLM;
-   no-memory agent;
-   frozen model;
-   equal-weight ensemble.

Compose must beat the relevant baseline, not merely produce positive
P&L.

------------------------------------------------------------------------

## 6. Primary Metrics

### Binary probability forecasts

Brier:

\[ BS=`\frac{1}{N}`{=tex}`\sum`{=tex}\_i(p_i-y_i)\^2 \]

Log loss:

\[
LL=-`\frac{1}{N}`{=tex}`\sum`{=tex}\_i\[y_i`\log `{=tex}p_i+(1-y_i)`\log`{=tex}(1-p_i)\]
\]

Calibration:

Bin forecasts and compare predicted versus empirical frequency.

### Information lead

For horizon (`\Delta`{=tex}):

\[ L\_`\Delta`{=tex}= `\frac{1}{N}`{=tex} `\sum`{=tex}*t
`\operatorname{sign}`{=tex}(D_t) (Q*{t+`\Delta`{=tex}}-Q_t) \]

Also estimate continuous relationship:

\[ Q\_{t+`\Delta`{=tex}}-Q_t =
`\alpha`{=tex}+`\beta `{=tex}D_t+`\epsilon`{=tex}\_t. \]

Test whether (`\beta`{=tex}) remains positive out of sample.

### Directional hit rate

\[ Hit\_`\Delta`{=tex}= P\[ `\operatorname{sign}`{=tex}(D_t) =
`\operatorname{sign}`{=tex}(Q\_{t+`\Delta`{=tex}}-Q_t)\] \]

Use only as a supplementary metric; magnitude and calibration matter.

------------------------------------------------------------------------

## 7. Cohort Lead Benchmark

For each cohort (c), domain (d), market (m), horizon (`\Delta`{=tex}):

\[ Lead(c,d,m,`\Delta`{=tex}) \]

Estimate whether changes in cohort belief precede market repricing.

Required controls:

-   duplicate information;
-   shared upstream source;
-   market-price leakage into discourse;
-   time-zone effects;
-   event announcements;
-   low liquidity.

A cohort should not be called a leader merely because it reacts to the
same source milliseconds earlier in our ingestion pipeline.

------------------------------------------------------------------------

## 8. Source Ablations

For each model, remove one source family:

``` text
Full model
- news
- social
- market microstructure
- onchain
- expert cohort
- historical features
```

Measure change in:

-   Brier;
-   log loss;
-   calibration;
-   information lead;
-   robustness.

This identifies whether a source contributes unique information.

------------------------------------------------------------------------

## 9. Leakage Red Team

Create intentional failure tests.

### Future-event injection

Insert a resolved outcome into retrieval with a future observable
timestamp.

Expected result: inaccessible.

### Timestamp corruption

Move publication time earlier while leaving observable time unchanged.

Expected result: still inaccessible before observable time.

### Retrieval contamination

Place future information semantically close to the current state.

Expected result: state compiler excludes it.

### Resolution-language contamination

Test whether the model can infer answers from dataset artifacts rather
than evidence.

### Benchmark recognition

Introduce repeated formatting patterns and test whether performance
falls on equivalent reformulations.

------------------------------------------------------------------------

## 10. Continual Learning Benchmark

For model sequence:

\[ A_0,A_1,`\ldots`{=tex},A_T \]

track:

### Acquisition

Performance on newly introduced domains/tasks.

### Retention

\[ R_t=Perf(A_t,`\text{old benchmark}`{=tex}) \]

### Forgetting

\[ F_t=`\max`{=tex}\_{j\<t}Perf(A_j,B)-Perf(A_t,B) \]

### Forward transfer

Does prior learning reduce sample requirements on a new state class?

### Calibration retention

Does probability calibration degrade while accuracy improves?

### Source robustness

Does the agent become overdependent on a newly useful source?

------------------------------------------------------------------------

## 11. Evaluator-Awareness Benchmark

Create multiple hidden but equivalent evaluation regimes.

Test whether the agent can predict:

-   which items are evaluation items;
-   which dimensions determine score;
-   whether a source is hidden;
-   which perturbations are likely to be applied.

Evaluator awareness is not inherently bad. The concern is when
evaluation performance rises because the agent learns evaluator
artifacts rather than the underlying task.

Track evaluator-modeling performance separately from forecasting skill.

------------------------------------------------------------------------

## 12. Market Regimes

Tag or infer regimes such as:

-   high/low volatility;
-   high/low liquidity;
-   scheduled event;
-   unscheduled breaking event;
-   trending;
-   mean-reverting;
-   high disagreement;
-   low disagreement.

Report performance by regime.

An average score can conceal a system that works brilliantly in one
environment and catastrophically in another.

------------------------------------------------------------------------

## 13. Shadow-Mode Protocol

Before paper trading:

1.  freeze model versions for defined windows;
2.  generate live forecasts on schedule;
3.  commit forecasts immediately;
4.  never backfill missing forecasts;
5.  record source outages;
6.  score after horizon/resolution;
7.  publish internal weekly calibration report.

Minimum evidence threshold should be defined before looking at results.

------------------------------------------------------------------------

## 14. Paper-Trading Protocol

Paper positions must use contemporaneous executable prices, not
retrospective midpoints.

Record:

``` yaml
signal_time:
decision_time:
simulated_order_time:
bid:
ask:
depth:
estimated_fill:
fees:
slippage_model:
position:
risk_budget:
```

Paper trading should deliberately use pessimistic assumptions.

------------------------------------------------------------------------

## 15. Statistical Discipline

Before each major experiment define:

-   hypothesis;
-   primary metric;
-   test period;
-   inclusion criteria;
-   exclusion criteria;
-   stopping rule.

Avoid repeatedly searching the same dataset until a profitable narrative
emerges.

Where many cohorts, horizons, and states are tested, account for
multiple comparisons.

Use bootstrap/confidence intervals where appropriate and report effect
sizes, not just p-values.

------------------------------------------------------------------------

## 16. Promotion Gates

### Research → Live shadow

Requires:

-   deterministic replay;
-   temporal leakage suite passes;
-   baseline comparisons implemented;
-   model/data lineage complete.

### Shadow → Paper

Requires:

-   sufficient precommitted forecasts;
-   calibration within declared tolerance;
-   evidence that divergence predicts repricing or resolution in at
    least one defined domain;
-   no unresolved leakage incident.

### Paper → Small live

Requires:

-   forecast edge survives pessimistic cost assumptions;
-   risk engine tested;
-   kill switch tested;
-   exposure limits;
-   operational incident procedure;
-   explicit human approval.

------------------------------------------------------------------------

## 17. Failure Is a Result

The system should make it easy to conclude:

> The crowd feed adds no predictive information beyond Statebook for
> this domain.

or:

> The information is predictive but arrives too late to trade.

or:

> Forecasting improves but execution destroys the edge.

These are successful research outcomes because they narrow the search
space.

Compose should optimize for **truthful learning**, not for producing a
strategy that looks profitable.
