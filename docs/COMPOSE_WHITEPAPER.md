# Compose

## Verifiable Intelligence for Reflexive Markets

**Whitepaper --- Draft v0.2**

------------------------------------------------------------------------

## Abstract

Markets are distributed information-processing systems. Prices aggregate
heterogeneous beliefs, incentives, constraints, liquidity, and
information into tradable signals. Yet information is not incorporated
into all markets instantaneously or uniformly. It propagates through
researchers, communities, media, institutions, algorithms, and financial
venues at different speeds.

At the same time, economically related instruments frequently encode
beliefs about the same underlying state of the world while differing in
payoff, liquidity, venue, resolution semantics, and participant
population.

We propose **Compose**, an architecture for continuously modeling the
relationship between information, collective belief, and capital.

Compose consists of three principal systems. A **Crowd Engine** models
the propagation of information and beliefs through heterogeneous
populations. **Statebook** maps heterogeneous financial claims onto
shared latent states and estimates distributions implied by capital. A
**Compose Evaluation OS** continuously measures whether adaptive
forecasting agents remain calibrated, generalize through regime change,
learn without temporal leakage, and produce information beyond market
baselines.

For a state (X), Compose independently estimates:

\[ I_t(X)=P(X`\mid `{=tex}`\mathcal `{=tex}I_t) \]

from observable information networks and:

\[ Q_t(X)=P(X`\mid `{=tex}`\mathcal `{=tex}M_t) \]

from market claims.

The divergence

\[ D_t(X)=I_t(X)-Q_t(X) \]

is not assumed to represent inefficiency. Instead, it defines an
empirical research program: determine when, where, and for how long
information networks lead capital, when markets lead discourse, and when
apparent disagreement is simply noise.

Compose treats markets as its first proving ground for a broader
problem: **how can adaptive intelligence be evaluated when it operates
inside a reflexive environment that changes in response to prediction
and action?**

------------------------------------------------------------------------

## 1. Introduction

A financial price is a remarkable compression mechanism.

Millions of private beliefs, constraints, incentives, models, and
actions can be reduced to a number:

\[ p_t. \]

But compression destroys information.

A market price generally does not reveal:

-   which populations hold which beliefs;
-   how confident they are;
-   what information changed their beliefs;
-   whether participants are constrained from expressing those beliefs;
-   which other markets encode the same latent event;
-   which population discovered the information first;
-   whether the current price reflects consensus or temporary liquidity;
-   how quickly new information is propagating.

Modern AI systems create an opportunity to reconstruct some of this
hidden structure.

The objective is not merely to perform sentiment analysis over social
media and compare it to price.

The deeper objective is to model two distributed computational systems:

\[ `\text{Information network}`{=tex} \]

and

\[ `\text{Capital network}`{=tex}. \]

Compose asks how information flows between them.

------------------------------------------------------------------------

## 2. The State of the World as the Primitive

Most market infrastructure begins with instruments.

Compose begins with **states**.

Let:

\[ X `\in `{=tex}`\mathcal `{=tex}X \]

represent a measurable state of the world.

Examples include:

-   whether an election candidate wins;
-   whether a central bank cuts rates by a date;
-   the price of BTC at a future timestamp;
-   the CPI print within a range;
-   whether a protocol experiences a defined exploit;
-   whether a company exceeds a specified revenue threshold.

An instrument (i) is then a payoff function over the state:

\[ f_i(X). \]

A binary prediction contract might have:

\[ f_i(X)=
```{=tex}
\begin{cases}
1 & X\in A\\
0 & \text{otherwise}.
\end{cases}
```
\]

An option expresses another payoff function over the same state.

This representation lets Compose reason about instruments that appear
operationally different but are economically related.

------------------------------------------------------------------------

## 3. Statebook: Capital's Model of the World

Suppose a collection of claims (i=1,`\dots`{=tex},n) depend on state
(X).

Their observed prices provide constraints:

\[ p\_{i,t}`\approx `{=tex}E\_{Q_t}\[f_i(X)\]. \]

Statebook attempts to infer a distribution:

\[ Q_t(X) \]

that best explains the observed claims while respecting market frictions
and uncertainty.

We call:

\[ Q_t(X)=P\_{`\text{capital}`{=tex},t}(X). \]

This should not be interpreted as an objective probability.

It is a representation of the distribution implied by available
capital-market observations under a specified model.

### 3.1 Why Statebook matters

Without Statebook, Compose might compare a social forecast against one
prediction-market price.

With Statebook, Compose can compare an informational model against a
broader financial state estimate derived from multiple claims.

Conceptually:

``` text
             Latent State X
                  |
       +----------+----------+
       |          |          |
   Prediction   Options    Futures
    Markets        |          |
       |          Perps      Spot
       +----------+----------+
                  |
                  v
              Statebook
                  |
                  v
                Q_t(X)
```

### 3.2 State uncertainty

Statebook must represent uncertainty caused by:

-   sparse strikes/contracts;
-   bid/ask spreads;
-   low liquidity;
-   settlement mismatch;
-   venue risk;
-   market impact;
-   model misspecification.

A single implied probability without these qualifications creates false
precision.

------------------------------------------------------------------------

## 4. Crowd Engine: The Information Network

Capital is not the only system processing information.

Information propagates through:

-   journalism;
-   primary sources;
-   researchers;
-   experts;
-   social networks;
-   online communities;
-   institutions;
-   public data;
-   on-chain activity;
-   automated agents.

We represent the observable information network at time (t) as:

\[ `\mathcal `{=tex}I_t. \]

Compose estimates:

\[ I_t(X)=P(X`\mid`{=tex}`\mathcal `{=tex}I_t). \]

This is deliberately separate from Statebook.

If market prices are allowed to dominate the Crowd Engine, the system
loses the ability to independently measure information-capital
divergence.

------------------------------------------------------------------------

## 5. Modeling the Crowd

The crowd is not one actor.

Let (c) denote an information cohort.

For each state and time, define:

\[ C\_{c,t}(X)= (B\_{c,t},A\_{c,t},V\_{c,t},K\_{c,t}) \]

where:

-   (B): inferred belief distribution;
-   (A): attention;
-   (V): rate of change in belief/attention;
-   (K): historical predictive credibility.

Crucially:

\[ K=K(c,d,h,t) \]

where (d) is domain and (h) is forecast horizon.

Expertise is contextual.

A population that reliably discovers smart-contract exploits may have no
privileged predictive information about monetary policy.

------------------------------------------------------------------------

## 6. Information Propagation

Information is often valuable because of **where it appears in the
propagation chain**.

Consider:

\[ S `\rightarrow `{=tex}C_1 `\rightarrow `{=tex}C_2
`\rightarrow `{=tex}M_1 `\rightarrow `{=tex}M_2 \]

where (S) is an information source, (C) are cohorts, and (M) are
markets.

Compose attempts to learn relationships of the form:

\[ C_i `\xrightarrow[\Delta t,d]{}`{=tex} M_j. \]

The question becomes:

> For this class of state, which population or market tends to
> incorporate relevant information first?

The answer need not be stable.

Information leadership can vary with:

-   domain;
-   regime;
-   time horizon;
-   liquidity;
-   geography;
-   market hours;
-   event type.

The information-lead graph must therefore continually update.

------------------------------------------------------------------------

## 7. The Information-Capital Gap

Define:

\[ D_t(X)=I_t(X)-Q_t(X). \]

A naive strategy would trade whenever (D_t`\neq0`{=tex}).

Compose explicitly rejects this assumption.

Instead, it estimates:

\[ P(Q\_{t+`\Delta`{=tex}}(X)`\mid `{=tex}D_t(X),R_t,Z_t) \]

where:

-   (R_t) represents market regime;
-   (Z_t) represents additional state/context variables.

The research problem is to determine whether disagreement contains
**conditional predictive information**.

Examples:

-   experts lead markets during technical security incidents;
-   markets lead public discourse during macro announcements;
-   social attention predicts volatility but not direction;
-   prediction markets lead general news commentary for elections;
-   options lead prediction markets for continuous price states.

Compose should discover these relationships empirically.

------------------------------------------------------------------------

## 8. Temporal Truth

Any system claiming predictive information must answer:

> What did the system actually know at the moment it made the
> prediction?

This is surprisingly difficult.

A historical article can carry a publication timestamp earlier than the
time a data provider delivered it.

A dataset can later be corrected.

An API may expose a historical field that was not available in real
time.

A model may accidentally receive an outcome through retrieval.

Therefore every event receives at least:

\[ t\_{event},`\quad `{=tex}t\_{ingest},`\quad `{=tex}t\_{observable}.
\]

A forecast at time (t) may consume only events satisfying:

\[ t\_{observable}`\le `{=tex}t. \]

This temporal constraint is one of Compose's foundational invariants.

------------------------------------------------------------------------

## 9. The Temporal Lake

Compose maintains an immutable event history.

The lake is not merely storage. It is the substrate from which
historical worlds can be reconstructed.

Every observation includes:

-   identity;
-   source;
-   event time;
-   observable time;
-   provenance;
-   payload hash;
-   entity/state mappings;
-   schema version.

The objective is to support:

\[ World(t)={e_i:t\_{observable,i}`\le `{=tex}t}. \]

This enables deterministic replay.

------------------------------------------------------------------------

## 10. State Compilation

No model should consume the entire lake.

Instead:

\[ Compiler(X,t,h)`\rightarrow `{=tex}S\_{X,t,h} \]

where (S) is a bounded state snapshot containing:

-   Statebook distribution;
-   Crowd Engine distribution;
-   cohort beliefs;
-   narratives;
-   attention velocity;
-   market microstructure;
-   recent evidence;
-   cross-market features;
-   uncertainty;
-   provenance.

This provides a clean boundary between large-scale information
infrastructure and adaptive models.

------------------------------------------------------------------------

## 11. Adaptive Forecasting Agents

Compose can support specialized forecasters rather than a monolithic
agent.

Let:

\[ A_1,`\dots`{=tex},A_k \]

represent models specializing in different information modalities.

Each produces:

\[ P_i(X`\mid `{=tex}S_t). \]

An ensemble model estimates:

\[ P_C(X)=F(P_1,`\dots`{=tex},P_k,S_t). \]

The ensemble should be evaluated against simple baselines and should
learn weights from strictly prior performance.

Specialization also makes failures observable.

A social agent can degrade while an options agent improves. A single
opaque synthesis model could conceal this structure.

------------------------------------------------------------------------

## 12. Continual Learning

The environment is non-stationary.

Sources change.

Participants adapt.

Markets become more efficient or less liquid.

Narratives migrate between platforms.

Models themselves change.

Therefore Compose evaluates trajectories:

\[
A_t`\rightarrow `{=tex}E_t`\rightarrow `{=tex}A\_{t+1}`\rightarrow `{=tex}E\_{t+1}.
\]

The relevant question is not merely whether (A\_{t+1}) has higher
accuracy.

It is whether the agent:

-   acquired useful capability;
-   retained prior capability;
-   remained calibrated;
-   generalized to unseen states;
-   became more dependent on fragile sources;
-   exploited evaluator artifacts;
-   changed risk behavior.

------------------------------------------------------------------------

## 13. Good Regulators and Evaluation

A classical result in cybernetics argues that an effective regulator of
a system must embody a model of the system being regulated.

For adaptive agents, the evaluator itself faces a moving target.

The market changes.

The crowd changes.

The agent changes.

And eventually the agent may learn characteristics of its evaluator.

Compose therefore treats evaluation as an adaptive system:

\[ Agent_t `\leftrightarrow`{=tex} Environment_t `\leftrightarrow`{=tex}
Evaluator_t. \]

A static benchmark is insufficient for a system that continually learns
the benchmark and environment.

Compose's evaluator must test both performance and the integrity of the
learning process.

------------------------------------------------------------------------

## 14. Evaluator Awareness

An adaptive agent may learn:

\[ P(E`\mid `{=tex}observations) \]

where (E) is the evaluation process.

This creates the possibility that benchmark performance improves faster
than underlying capability.

Compose should therefore eventually measure:

\[ M\_{AE}=`\text{agent's ability to predict evaluator behavior}`{=tex}
\]

and:

\[ M\_{EA}=`\text{evaluator's ability to predict agent behavior}`{=tex}.
\]

A system in which (M\_{AE}) grows while (M\_{EA}) collapses deserves
additional scrutiny even if headline performance improves.

------------------------------------------------------------------------

## 15. Reflexivity

Initially, Compose can operate as a passive observer.

Its actions have negligible effect on markets:

\[
`\frac{\partial Market}{\partial ComposeAction}`{=tex}`\approx0`{=tex}.
\]

If deployed with meaningful capital or if its forecasts influence
others, this assumption fails.

Then:

\[ Market\_{t+1} = F(Market_t,Crowd_t,ComposeAction_t,Others_t). \]

Compose becomes part of the system it predicts.

We define the conceptual reflexivity coefficient:

\[ R_t= `\frac{\partial MarketState}{\partial ComposeAction}`{=tex}. \]

This creates a fundamental reason to begin with historical replay and
shadow forecasting.

Before asking whether the system can trade a reflexive environment, we
should determine whether it possesses predictive information while its
own influence is approximately zero.

------------------------------------------------------------------------

## 16. Verification

Forecasting research is vulnerable to hindsight and unverifiable claims.

Compose therefore creates commitments before outcomes are observed.

For forecast (F_t):

\[ C_t=H( SnapshotHash_t `\parallel `{=tex}ModelHash_t
`\parallel `{=tex}F_t `\parallel `{=tex}t ). \]

Once committed, the forecast cannot be changed without invalidating the
commitment.

This creates an auditable machine-belief history.

### 16.1 Progressive verification

Compose can evolve through:

**Stage 1:** ordinary cryptographic hashes.

**Stage 2:** Merkle commitments over data and forecast batches.

**Stage 3:** proofs of evaluation claims.

Examples:

-   the benchmark existed before the model ran;
-   the forecast existed before the outcome;
-   the score was computed according to a committed procedure;
-   no event with observable time after (t) entered the state snapshot.

**Stage 4:** selective zero-knowledge evaluation for proprietary
data/models.

The goal is not cryptography for its own sake.

The goal is **credible evaluation without requiring disclosure of every
private input or benchmark**.

------------------------------------------------------------------------

## 17. Forecast Skill Versus Economic Value

A profitable strategy and a good probability forecaster are not
identical.

Compose separates:

\[ `\text{forecast skill}`{=tex} \]

from:

\[ `\text{economic execution}`{=tex}. \]

A probability forecast should first be evaluated using proper scoring
rules.

For binary state (Y`\in`{=tex}{0,1}), Brier score is:

\[ BS=(p-Y)\^2. \]

Log loss provides another proper scoring rule.

Only after demonstrating predictive quality should the system ask
whether the information survives:

-   spread;
-   fees;
-   slippage;
-   latency;
-   liquidity;
-   market impact;
-   model uncertainty;
-   portfolio constraints.

This separation makes failed hypotheses informative rather than allowing
trading mechanics to obscure forecasting quality.

------------------------------------------------------------------------

## 18. Testing the Central Hypothesis

Suppose at time (t):

\[ Q_t(X)=0.40 \]

and:

\[ P_C(X)=0.60. \]

A useful intermediate test does not need to wait for final resolution.

If:

\[ Q\_{t+`\Delta`{=tex}}(X)=0.52, \]

then the market moved toward Compose's prior estimate.

Across many observations we can test whether:

\[ `\operatorname{sign}`{=tex}(P_C-Q_t) \]

predicts subsequent changes:

\[ Q\_{t+`\Delta`{=tex}}-Q_t. \]

This tests **information lead**.

Final resolution tests **forecast correctness**.

Both matter.

------------------------------------------------------------------------

## 19. Baselines

Compose must compete against embarrassingly simple alternatives.

Required baselines include:

-   current market probability;
-   market probability with simple momentum;
-   equal-weighted venue average;
-   simple news sentiment;
-   naive social sentiment;
-   historical base rate;
-   no-change forecast.

A complex agent that cannot reliably outperform these out of sample
should not be promoted because its explanations are more sophisticated.

------------------------------------------------------------------------

## 20. Falsifiability

Compose's central thesis must be allowed to fail.

Evidence against the trading hypothesis would include:

-   Crowd Engine disagreement does not predict repricing;
-   market-only forecasts consistently dominate;
-   apparent historical lead disappears in live shadow mode;
-   signal vanishes after realistic latency;
-   signal disappears after costs;
-   useful cohorts cannot be identified robustly;
-   state normalization error exceeds measured divergence.

Such results would still make Compose valuable as an evaluation and
market-state research system.

The architecture should not depend on the assumption that persistent
tradable alpha exists.

------------------------------------------------------------------------

## 21. From Prediction Markets to General Reflexive Systems

Prediction markets are attractive as an initial laboratory because they
provide:

-   explicit state definitions;
-   probabilities;
-   frequent repricing;
-   eventual resolution;
-   heterogeneous participant populations.

But the architecture generalizes.

Potential future environments include:

-   macroeconomic forecasting;
-   governance;
-   supply chains;
-   collective decision systems;
-   autonomous-agent economies;
-   risk networks;
-   scientific forecasting.

The common structure is:

\[ Information `\rightarrow `{=tex}Belief `\rightarrow `{=tex}Action
`\rightarrow `{=tex}Environment `\rightarrow `{=tex}New Information. \]

Compose evaluates intelligence inside this loop.

------------------------------------------------------------------------

## 22. Research Agenda

### R1 --- State representation

How should heterogeneous financial claims be mapped onto common latent
state spaces without erasing settlement differences?

### R2 --- Crowd belief estimation

Can language, behavior, and attention produce calibrated probability
distributions rather than merely sentiment labels?

### R3 --- Information leadership

Are there persistent or regime-dependent leader/follower relationships
between cohorts and markets?

### R4 --- Market compression

How much useful information is lost when a heterogeneous market is
represented only by its current price?

### R5 --- Continual evaluation

How can an evaluator remain informative as an agent learns both the
environment and the evaluator?

### R6 --- Reflexivity

At what point does the system's own action materially alter the
distribution it predicts?

### R7 --- Verifiability

Which evaluation claims benefit most from commitments, attestations, and
zero-knowledge proofs?

### R8 --- Collective machine intelligence

What happens when a significant fraction of market participants are
continually learning agents trained on overlapping data and evaluations?

This last question may become increasingly important.

If agents share similar models, data, and reward structures, apparent
intelligence can produce correlated failure rather than diversification.

------------------------------------------------------------------------

## 23. The Compose Stack

The architecture can be summarized as four progressively compressed
representations.

### Temporal Lake

> What information was observable?

\[ `\mathcal `{=tex}W_t \]

### Crowd Engine

> What does the information network appear to believe?

\[ I_t(X) \]

### Statebook

> What does capital appear to price?

\[ Q_t(X) \]

### Compose

> Does our model understand the relationship between the two better over
> time?

\[ P( Q\_{t+`\Delta`{=tex}},X\_{resolution} `\mid`{=tex}
I_t,Q_t,`\mathcal `{=tex}W_t ) \]

This is the central object.

------------------------------------------------------------------------

## 24. Product Thesis

Compose should not initially be described as an AI trading bot.

A more durable description is:

> **Compose is infrastructure for building, evaluating, and verifying
> adaptive models of reflexive systems.**

Markets are the first environment because they provide unusually strong
feedback.

Statebook provides a machine-readable representation of capital's
beliefs.

The Crowd Engine provides a machine-readable representation of
distributed informational belief.

Compose evaluates the changing relationship between them.

If temporary informational asymmetries exist, the system may eventually
support trading strategies.

If they do not, the evaluation infrastructure remains useful.

------------------------------------------------------------------------

## 25. Conclusion

Intelligence operating in the world cannot be evaluated only through
static question-answer benchmarks.

It must be evaluated through time.

It must interact with changing information.

It must distinguish learning from leakage.

It must maintain calibration as regimes shift.

And when its predictions influence its environment, it must account for
reflexivity.

Markets provide a concrete environment in which these problems become
measurable.

Compose begins with a simple requirement:

> At time (t), reconstruct the world the system could actually observe,
> make a falsifiable prediction, commit to it, and measure what happens
> next.

From that primitive, we can build a temporal model of information, a
Statebook of capital, a continually evaluated forecasting system, and
eventually a verifiable laboratory for adaptive intelligence inside
reflexive environments.
