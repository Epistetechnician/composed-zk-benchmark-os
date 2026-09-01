# Oak Lab selective-credit V3 independent protocol review

State slice: `oaklab-experience-learning-selective-credit-v3`

Reviewer: `independent-agent-review`

Decision: `rejected`

Implementation authorization: `false`

Real-execution authorization: `false`

Astral: `isolated_not_run`

The frozen V3 design is scientifically plausible, but the reviewed bytes do
not define an executable causal, statistical, or resource contract. The
review therefore fails closed before implementation. This decision does not
authorize a learner, synthetic execution, real execution, or use of the V2
energy receipt.

## Exact review identity

- `AGENTS.md`:
  `406c7eca279d03c4c784cee654f827879ebd684b8c4546b17215762527d1e844`
- `experiments/experience_learning/selective_credit_v3_protocol.json`:
  `2701174e4f3d18e82839f2800ac597e6b752f7adce64806719e9a06ec54111a7`
- `docs/research/experience-learning/28-oaklab-selective-credit-v3-protocol.md`:
  `8bbd7863f83942ec5d5e2ba444259237d9412fe27fd9a78cfd15da87e98c6a30`
- `docs/research/experience-learning/27-oaklab-plasticity-guard-permanent-historical-closure.md`:
  `eeaa5bfda3fb9039c046dbabc16b2b74d2c65be80b78c7862782feb4bc357859`
- `docs/research/experience-learning/13-oaklab-selective-credit-theory-v1.md`:
  `cfcbe7a925e06d63cf5f999991f75af88a6e9cade7fbee5a5e4dd7846f6e7fa2`
- `docs/research/experience-learning/15-oaklab-selective-credit-theory-v2.md`:
  `4e781a5892cbc10bba8a9a98bbdaaf36eb2d0e84563be6cd12c3ca6e53a3fec7`
- `docs/research/experience-learning/18-oaklab-selective-credit-v2-terminal-closure.md`:
  `f9d7880057b0d3f6e279d093934a12939bba640af37f7cdcc98900daa0d3f7bd`
- `docs/research/experience-learning/26-oaklab-publication-gate-v2-r6-independent-review-closure.md`:
  `efab31be0564829deb1de6cde594ca1d09b3e17d7372cf2d6520e231f9a19f2f`

## What is sound

The fixed `H=8`, `gamma=0.9`, stride `9`, and `p=0.5` design can support
non-overlapping proximal windows once split-local anchoring is defined. The
assessment rule `beta_0 + beta_1*c < 0` has the correct direction for a
skip-minus-treatment benefit, because a centered regression coefficient uses
the treatment-minus-skip contrast. The recomputed two-sided normal
approximation at `alpha=0.0125`, `n=48`, and standardized effect `0.5` is
`0.8330770040094296`, matching the protocol.

The closure and claim boundaries are also sound: the plasticity guard remains
historical only; V2 energy cannot be reused; batch-one, zero replay, and no
hidden accumulation are explicit; real execution remains sealed; and Astral
is isolated.

Micro-randomized causal excursion effects and weighted-centered least squares
are established methods. The primary methodological references require a
fully specified randomization protocol and treatment-effect working model;
they do not make an underspecified online SGD recurrence causal by itself. See
the [micro-randomized trial design paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC4732571/)
and the [weighted-centered causal-effect moderation paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC6241330/).

## Blocking findings

1. **Assignment is not an executable randomization contract.** The same
   undifferentiated `seed` names stream generation and treatment assignment.
   Tuple framing, byte encoding, digest-to-uniform conversion, threshold,
   assignment balance, and domain separation are absent. Sequential
   exchangeability cannot be mechanically established.

2. **The estimand exceeds the working model.** Without an explicit linear
   treatment-effect assumption, the two beta coefficients define a working-
   model projection, not the stated conditional causal effect for every
   context value. The protocol must bind
   `tau_H(c)=-(beta_0+beta_1*c)`, define every loss as pre-update or post-update,
   and state the exact weighted, centered, ridge-regularized online recurrence,
   including initialization and which coefficients receive ridge terms.

3. **Proximal windows can cross split boundaries.** Each split has 256 items,
   which is not divisible by the stride of nine. There is no split-local anchor
   origin, incomplete-window rule, pending-state reset, or exact snapshot
   definition. The current text permits a fit update to consume tune outcomes
   or tune eligibility to consume assessment outcomes.

4. **The stream cohort is not frozen.** Stream names do not bind generator
   equations, source digests, dimensions, shift points, delayed-reward
   construction, loss functions, oracle features, or event semantics. These
   choices can materially change qualification after review.

5. **The primary analysis is not executable.** The protocol omits family-level
   seed aggregation, scale handling for two-stream families, the paired test
   statistic, sidedness, zero-variance behavior, Holm ordering and tie rules,
   adjusted-p computation, and qualifying-family decision order. The correct
   power arithmetic is therefore not bound to the future test implementation.

6. **Adaptation lag is undefined.** Shift or reward-onset anchors, baseline and
   recovery windows, the recovery threshold, censoring, nonrecovering runs,
   aggregation, and noninferiority evaluation are absent.

7. **Resource accounting is not reproducible.** There is no exact counting
   algebra for forward prediction, gradients, sparse features, updates,
   estimator predictions, and estimator updates. The eight additional scalars
   are not named with lifetimes and widths. Event-count semantics and family
   aggregation are undefined.

8. **Controls and ablations cannot falsify the mechanism.** Noise-floor and
   oracle controls have no pass criteria. `no_moderation` is mandatory but is
   absent from the mechanism gate. The other ablations require only untested
   mean differences. V3 can therefore pass without establishing learnable-
   versus-unlearnable discrimination or context moderation.

9. **Tune eligibility and locking are undefined.** No tune quantities or
   thresholds are frozen. There is no canonical snapshot payload or digest,
   and no validator rule prevents assessment construction or observation
   before an accepted lock.

## Required protocol corrections

A new frozen protocol identity may be reviewed only after it does all of the
following:

1. Separate `data_seed` and independently custodied `assignment_seed`; define
   a domain tag, length-delimited UTF-8 serialization, unsigned SHA-256 integer
   conversion, exact threshold, balance bounds, and rejection behavior.
2. Define the causal estimand as the exact linear working-model projection or
   add the assumption required for the stronger conditional claim. Bind the
   beta/tau sign, loss timing, WCLS objective, per-window state machine, SGD
   recurrence, ridge placement, initialization, and nonfinite handling.
3. Re-anchor inside every split, retain only complete H-step windows, require
   empty pending state at every split boundary, and prohibit any cross-split
   outcome use.
4. Freeze versioned generator definitions and digests for all six streams,
   including dimensions, distributions, shifts, reward delay, targets, oracle
   features, events, and endpoint loss.
5. Freeze the per-seed endpoint, family aggregation, paired test, sidedness,
   variance-zero rule, Holm implementation, tie order, adjusted p-values, and
   the complete gate evaluation order. Align power with that exact test and
   state which composite endpoints are not powered.
6. Define adaptation lag algorithmically for each eligible temporal stream,
   including censoring and nonrecovery.
7. Define a line-item operation and storage algebra, name all additional state,
   and specify aggregation for updates, operations, storage, and events.
8. Add fixed control floors and oracle sanity checks. State whether context
   moderation is part of the mechanism claim; if it is, include
   `no_moderation` in a multiplicity-controlled mechanism gate.
9. Define tune pass/fail quantities, a canonical tune snapshot and lock
   payload, independent lock validation, and a hard rule that assessment bytes
   do not exist before lock acceptance.

## Required validator behavior

The machine-readable companion receipt lists the mandatory fail-closed checks.
At minimum, the validator must recompute assignments, split-local windows,
outcomes, coefficient updates, locks, endpoints, paired statistics, Holm
adjustments, adaptation lag, ablations, operations, storage, and the full gate
from immutable inputs. It must reject missing arms, digest drift, future-field
access, cross-split windows, replay, hidden accumulation, guard reuse, V2
energy reuse, Astral coupling, and any claim above the protocol ceiling.

## Authorization boundary

The rejected bytes remain a reviewed design record only. No implementation,
synthetic qualification, assessment, real panel, energy campaign, publication,
benchmark promotion, SOTA claim, model-bearing execution, production traffic,
plasticity-guard reopening, or Astral integration is authorized.

Canonical review digest:
`330b043c47cdefbc2424d843f9ab0ba4979daa039dfc531506d7b995e7595cdd`.
