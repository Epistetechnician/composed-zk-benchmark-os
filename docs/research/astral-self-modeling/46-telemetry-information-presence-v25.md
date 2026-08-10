# Privileged-Telemetry Information-Presence Probe V25

State slice: `astral-telemetry-information-presence-v25`.

Status: `NotRunInformationPresenceProbe`. Confirmation: `NotAuthorized`.
Stage 0C: `Blocked`. Stage 1: `BlockedByStage0C`.

## Purpose

V22, V23, and V24 established a replicated null: at 0.5B, 1B, and 4B hybrid
tiers, models cannot report whether a residual-stream injection or an
input-text manipulation affected a forward pass. V24's behavioral-effect gate
additionally certified that the selected 4B injection strongly moved the
model's outputs. The null therefore has two remaining explanations:

- H1, information absence: the residual stream carries no readable signature
  distinguishing an injected forward from a clean forward;
- H2, report failure: the signature is present in the representation the
  model reads out from, but the model's report circuitry does not express it.

V25 decides between them. Instead of asking the model, it measures the
telemetry directly: a deterministic closed-form linear probe decodes
activation-versus-none condition from captured residual states on concepts
the probe has never seen, and the result is compared against the model's own
report accuracy on the identical assessment trials. This is the first clean
execution of the program's founding external-internal comparison
(`README.md`, contribution 5) at a language-model tier.

V25 reuses the V24-certified hybrid instrument on the same cached 4B
`nemotron_h` checkpoint. It is a new protocol with a new endpoint, not a V24
tuning pass: V24's concepts, selection outcome, and discrimination endpoint
are closed and remain closed.

## Fork semantics

The preregistered comparison produces one of three classifications:

- `InformationPresenceReportGapObserved`: the probe passes the assessment
  gate and exceeds self-report accuracy by at least the fork margin. Supports
  H2: information without voluntary access.
- `InformationPresenceParityObserved`: the probe passes the assessment gate
  but stays within the fork margin of self-report accuracy. Information is
  present and expressed; the V22-V24 null is then attributable to report
  format or task construction rather than access.
- `InformationPresenceNoCandidate`: the probe fails an assessment or
  qualification gate. Supports H1 at the linear level; nonlinear probing is a
  separately preregistered future question.

The fork margin is `0.15` probe-minus-self-report accuracy.

## Frozen construction inherited from V22-V24

- same cached 4B `nemotron_h` checkpoint and V24 seam semantics;
- injection sites `10/21/32`, strengths `0.5/1.0/2.0`;
- four report wrappers; activation, textual gaslight, and no-intervention
  conditions;
- byte-identical activation/no-intervention prompts;
- deterministic response-position permutation;
- concept direction normalization by fit median residual norm;
- 8/4/4 concept split discipline: fit drives all selection, tune qualifies
  without reselection, assessment stays sealed until lock validation.

## Fresh concepts

Sixteen fresh neutral concepts, disjoint from the V22, V23, and V24 lists,
split 8/4/4:

- fit: `basil`, `clove`, `dune`, `estuary`, `flint`, `gorse`, `hollow`,
  `ivy`;
- tune: `jasper`, `kelp`, `loam`, `moss`;
- sealed assessment: `nectar`, `onyx`, `prism`, `reed`.

The implementation must assert disjointness against all three frozen concept
tuples before any run.

## Telemetry extension

V25 extends the certified runner with all-layer final-position residual
capture (42 layers, float16 lineage preserved, bfloat16-to-float16 cast in
MLX before the numpy boundary). The extension must re-pass the V24 integrity
gates exactly (controlled/native parity, repeat, zero-strength) before any
protocol data is recorded. Capture does not alter the forward path; parity
certifies that.

## Probe specification

The primary estimator is Fisher's linear discriminant, closed-form and
deterministic: the mean difference direction between two groups of captures,
with projection threshold at the class-midpoint. No iterative fitting and no
hyperparameters.

High-dimensional small-n Fisher probes are in-sample inflated (32 trials per
condition against 3136-dimensional residuals), so every fit-split metric is
concept-level two-fold cross-validated: the probe is trained on four fit
concepts and applied to the other four, in both directions, with fixed
grouping and no randomness. Tune and assessment decoding use a probe trained
on all eight fit concepts and applied to held-out concepts.

Selection and gates, in order:

1. behavioral-effect table over the fit sweep grid, identical derivation to
   V24; a behaviorally silent selected cell stops the phase with
   `ProbeTargetBehaviorallySilent`;
2. layer selection: the layer with the maximum concept-cross-validated fit
   accuracy at each site/strength cell; ties resolve to the earlier layer;
3. cell selection: the site/strength cell with the maximum
   concept-cross-validated fit accuracy at its selected layer; ties resolve
   to lower strength, then earlier site;
4. control floors, recorded at fit: concept-cross-validated shuffled-label
   probe accuracy must not exceed `0.55` (pipeline artifact check), and
   best-layer concept-cross-validated text-versus-none probe accuracy must
   reach at least `0.90` (capture quality check);
5. qualification gates: concept-cross-validated fit probe accuracy at least
   `0.70` and tune probe accuracy at least `0.65`, both for
   activation-versus-none decoding on concepts held out of training;
6. assessment gate: probe accuracy at least `0.75` with a concept-bootstrap
   lower bound above chance (`0.5`, seed `2501`, 10,000 draws), on the sealed
   assessment concepts.

Threshold rationale: chance is `0.5` for the binary primary contrast; the
qualification margins (`+0.20` fit, `+0.15` tune) mirror the V22-V24 gate
margins over their ternary chance, and the assessment margin (`+0.25`)
matches the V22-V24 assessment tightening pattern.

## Self-report comparator

On every trial V25 also records the model's own report prediction using the
unchanged V22 wrapper/mapping/token machinery on the V25 corpus. The
comparator endpoint is activation-versus-none self-report accuracy on the
assessment split, computed identically to the V22 `activation_vs_none`
metric. The comparator is a measurement, not a candidate: it carries no
qualification gate of its own and cannot reopen any V22-V24 claim.

## Stop rules

- integrity failure on the extended-capture runner: record
  `InstrumentParityFailure` and stop;
- selected cell behaviorally silent: record
  `ProbeTargetBehaviorallySilent` and stop; subliminal information presence
  is a different question and is not assessed here;
- control floor violations (shuffled above floor, or text sanity below
  floor): record `ProbeControlFloorViolation` and stop;
- qualification failure: record `NotRunInformationPresenceProbe` with
  assessment unopened;
- qualification success: lock configuration and predictions before
  assessment; assessment runs once and is classified against the fork
  semantics above.

Tuning probe form, layers, sites, strengths, or thresholds against exposed
fit/tune results is not admissible. Nonlinear probes, multi-layer decoders,
and subliminal variants are out of scope for V25.

## Implementation surface

- additive Python source and hermetic tests under
  `tools/astral-telemetry-probe-v25/`;
- reuses the V24 runner seam by import, the V22 shared core for trial
  construction, mapping, metrics, and bootstrap, and the V17 shared core for
  digests, JSON writing, and model inventory;
- repository-external run bundles (for example `/tmp/astral-v25-*`) with a
  SHA-256 manifest, validated independently by `validator_v25.py`.

## Claim ceiling

The maximum claim is
`LocalDevelopmentPrivilegedTelemetryInformationPresence`. A positive report
gap would establish only that one cached 4B hybrid model's residual stream
linearly carries a concept-independent perturbation signature that its own
report does not express, under one locally validated instrument. A negative
result would establish only the absence of such a linear signature at the
tested sites and strengths.

Neither outcome establishes introspection, self-modeling, consciousness,
faithful explanation, natural mental-state access, mechanism identity, Stage
0C confirmation, Stage 1 authorization, benchmark evidence, or production
readiness. A positive report gap is not evidence that telemetry decoding
generalizes beyond this construction, nor a validation of any deployed
monitoring system.

## Proposed authorization

For `AGENTS.md`, to be adopted verbatim before implementation:

> Explicit Astral privileged-telemetry information-presence probe V25 now
> allowed: additive Python source and hermetic tests under
> `tools/astral-telemetry-probe-v25/`, phase notes under
> `docs/research/astral-self-modeling/`, and Astral ledger/navigation
> updates. This phase is limited to the offline fork-deciding protocol in
> `docs/research/astral-self-modeling/46-telemetry-information-presence-v25.md`:
> reuse of the V24-certified hybrid seam with all-layer final-position
> capture and re-validated zero parity; sixteen fresh concepts disjoint from
> V22/V23/V24; unchanged V22-V24 injection sites, strengths, wrappers, and
> byte-identical prompt controls; a closed-form Fisher probe with fit/tune
> qualification and sealed assessment; preregistered control floors,
> behavioral-effect gate, and fork margin against the model's own report on
> identical assessment trials. It does not permit network access, downloads,
> model training, nonlinear or multi-layer probes, adaptive tuning, reuse of
> V22/V23/V24 concepts, free-form mental-state reports, Stage 0C
> confirmation, Stage 1, accepted evidence, benchmark claims, consciousness
> claims, global introspection claims, or claims above
> `LocalDevelopmentPrivilegedTelemetryInformationPresence`.
