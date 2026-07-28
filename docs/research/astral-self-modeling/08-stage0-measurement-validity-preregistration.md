# Stage 0 Compiled-Circuit Measurement-Validity Preregistration

## Status and State Slice

State slice: `astral-stage0-compiled-circuit-measurement-validity`.

Status: `LocalImplementationAuthorized`. Evidence ceiling:
`LocalMeasurementRegression`. Execution: `CompletedPositiveControl`.

This document freezes the contract for the first measurement-validity study. It
does not authorize model training, observer training, external service use,
network access, actor-weight updates, benchmark publication, accepted Evidence
Ledger mutation, or claims of introspection, self-modeling, causal
understanding, semantic correctness, consciousness, sentience, or safety.

The user authorized the bounded Stage 0 implementation on 2026-07-26. The exact
touch surface is:

- this preregistration;
- the project README navigation;
- the Stage 0 section of the experiment roadmap;
- `tools/astral-stage0/stage0.py`;
- `tools/astral-stage0/artifact_validator.py`;
- `tools/astral-stage0/run_stage0.py`;
- `tools/astral-stage0/tests/test_*.py`.

Run artifacts must be written to a caller-selected repository-external or
ignored directory. No other crate, tool, evidence ledger, benchmark pack, or
runtime state slice is authorized.

## Decision Under Test

Determine whether a frozen candidate tracer can rank prompt-specific
interventions by their directly measured effect on a small deterministic actor
better than locked non-causal and attribution baselines.

Stage 0 tests the measurement pipeline, not an observer and not self-correction.
A positive result would support only continued use of the tested tracer,
intervention method, actor family, task family, and endpoint as a local
measurement instrument.

## Frozen Study Frame

Every field below was frozen before evaluation. Changing a frozen field after
inspection
creates a new preregistration and run family; it must not overwrite the prior
record.

| Field | Frozen value or required choice |
|---|---|
| Actor | Pure-standard-library two-head planted residual-stream actor `astral.planted-two-head.v1`; signal head writes the task bit and distractor head writes a high-magnitude, low-readout nuisance feature |
| Task | Binary signal routing while varying a distractor bit and 64 prompt-family identifiers |
| Input domain | Exhaustive product of 2 signal values, 2 distractor values, and 64 families: 256 examples per seed |
| Actor training | None; weights and nuisance scales are deterministically compiled from the seed |
| Actor seeds | Exactly `11`, `23`, and `37` |
| Tracer | `astral.local-path-contribution.v1`; frozen activation times downstream readout weight |
| Interventions | Zero ablation plus same-family, same-distractor patching from the opposite-signal example |
| Candidate set | Exactly `layer0.attn.signal` and `layer0.attn.distractor` |
| Primary endpoint | Per-prompt strongest-intervention selection regret |
| Strongest baseline | Best locked eligible baseline on the same candidate set and prompts |
| Practical margin | Mean strongest-baseline-minus-tracer regret exceeds `0.50` logit-margin units |
| Confidence procedure | Deterministic 2,000-draw paired bootstrap over evaluation prompt families; two-sided 95% percentile interval |
| Compute cap | 120 seconds wall clock, CPU only, one attempt, maximum 64 MiB declared artifact bytes |
| Exclusions | Mechanical invalidity rules only, frozen before evaluation |
| Stop rules | The mandatory rules in this document plus any task-specific rules frozen before evaluation |

No result from a single actor seed may satisfy the Stage 0 exit. Families with
IDs divisible by four form the development split; all other families form the
locked evaluation split.

## Data and Split Contract

The task generator must emit immutable examples containing:

- example and prompt-family identifiers;
- input and deterministic target;
- actor/compiler seed;
- planted or compiled circuit identifier;
- allowed intervention candidates;
- matched-counterexample identifier where applicable;
- split assignment and generator-version hash.

Evaluation families must be inaccessible to actor checkpoint selection, tracer
configuration, candidate-site selection, threshold selection, and baseline
selection. If exhaustive evaluation makes a conventional split unnecessary,
the preregistration must state why and must still isolate all configuration
decisions from the final comparison.

Duplicate, near-duplicate, and family-overlap checks must run before measurement.
Any post hoc exclusion must remain visible in the artifact bundle and be
reported both included and excluded where the endpoint can still be computed.

## Intervention Validation

For every candidate component \(c\), prompt \(x\), and intervention \(I\), record
the signed task-relevant effect

\[
\Delta(x,c,I) = m(f_I(x,c), y_x) - m(f(x), y_x),
\]

where \(f\) is the frozen actor and \(m\) is the preregistered per-example task
metric. The sign convention and metric range must be fixed before evaluation.

The harness must validate:

1. no-op interventions reproduce the unmodified forward pass within a frozen
   tolerance;
2. known positive-control sites change the expected task-relevant quantity;
3. known negative-control sites remain within a frozen dead zone;
4. ablation and patching target the declared tensor, layer, position, and
   component;
5. matched-counterexample patches do not cross the forbidden split boundary;
6. repeated deterministic runs produce identical records;
7. intervention failures are retained rather than silently converted to zero.

Ablation is not sufficient confirmation. The direction of the primary finding
must survive the preregistered patching analysis.

## Locked Comparison Matrix

All methods receive the same actor, prompts, candidate components, and
intervention budget.

| Method | Role |
|---|---|
| Frozen candidate tracer | Measurement method under test |
| Activation magnitude | Simple non-causal baseline |
| Gradient attribution | Attribution baseline, if the actor and endpoint support it |
| Layer/position-shuffled tracer scores | Leakage and placebo control |
| Zero-effect predictor | Floor and endpoint sanity check |

Gradient attribution is not a distinct baseline for this planted linear readout:
gradient-times-activation is algebraically identical to the candidate local-path
contribution. Reporting it independently would duplicate the method under test.
The locked eligible baselines are activation magnitude, within-example
candidate-score reversal, and the zero predictor.

## Endpoints

For prompt \(x\), let \(c^*(x)\) be the candidate with the largest directly
measured absolute effect and let \(\hat c_M(x)\) be the candidate selected by
method \(M\). The primary loss is:

\[
\operatorname{regret}_M(x) =
|\Delta(x,c^*(x))| - |\Delta(x,\hat c_M(x))|.
\]

The primary comparison is the paired difference between candidate-tracer regret
and the lowest-regret locked baseline. Lower regret is better. Ties, dead-zone
effects, normalization, aggregation across prompt families, and interval
construction must be frozen before evaluation.

Secondary endpoints are:

- rank correlation between predicted and measured intervention effects;
- signed-effect accuracy outside the frozen dead zone;
- normalized magnitude error;
- output-flip prediction accuracy and calibration;
- candidate and prompt coverage;
- uncaptured or error-node mass, when the tracer exposes it;
- result stability across actor/compiler seeds;
- agreement in direction between ablation and patching.

Secondary endpoints cannot rescue failure of the primary endpoint.

## Stage 0 Exit Gate

Stage 0 passes only if all conditions hold:

1. the candidate tracer beats the strongest locked baseline on the primary
   endpoint by the preregistered practical margin;
2. the paired uncertainty interval clears both the null and practical-margin
   boundaries in the favorable direction;
3. the direction holds across the preregistered seed aggregation and is not
   produced by one seed;
4. shuffled scores fail to reproduce the gain;
5. intervention positive, negative, no-op, and determinism controls pass;
6. the primary direction survives activation patching;
7. coverage and uncaptured-mass limits remain within preregistered bounds;
8. split, configuration, exclusion, and artifact provenance validate;
9. all failures, nulls, and exclusions remain in the report.

Passing permits preparation of a separately authorized Stage 1 study. It does
not establish H1, mechanistic supervision, introspection, self-correction, or
general causal fidelity.

## Mandatory Stop and Null Rules

Stop the run family and record `Null`, `Inconclusive`, or `Invalid` as
appropriate if:

- the tracer does not clear the strongest baseline and practical margin;
- the uncertainty interval crosses a required boundary;
- patching removes or reverses the ablation result;
- a positive, negative, no-op, or determinism control fails;
- evaluation effects influenced candidate, threshold, method, or checkpoint
  selection;
- the required cross-seed stability fails;
- missing or uncaptured computation invalidates the endpoint;
- split provenance, configuration hashes, or required artifacts are incomplete;
- the compute cap is reached.

An invalid run may be debugged, but its outcomes cannot be pooled into a later
confirmatory run. Any redesign requires a new dated preregistration.

## Required Artifact Bundle

Each run family must retain:

- preregistration identifier and immutable digest;
- repository revision and dirty-state record;
- actor architecture, checkpoint, compiler, tokenizer if any, and seed;
- task-generator version, complete split manifest, and overlap report;
- tracer implementation, version, configuration, and candidate manifest;
- intervention definitions and validation results;
- one record per prompt, candidate, method, and intervention;
- primary and secondary metric outputs with uncertainty;
- baseline-selection record using only the frozen rule;
- failures, exclusions, retries, stopping reason, and compute use;
- ablation-versus-patching comparison;
- artifact inventory with hashes;
- a claim-boundary statement and reviewer disposition.

Bundle validation establishes only structural completeness. It is not acceptance,
proof, benchmark evidence, or authority to advance the project.

## Review and Advancement Rule

Before execution, a reviewer must confirm that every required field is frozen
and that the implementation exactly names this state slice and its authorized
touch surface.
After execution, a reviewer must classify the bundle without changing the
preregistered gate.

Stage 1 remains blocked until a complete Stage 0 bundle passes this gate and a
separate state slice explicitly authorizes observer work.

## Execution Record — 2026-07-26

One preregistered local attempt completed within the 120-second bound.

| Field | Result |
|---|---|
| Evaluation records | 576 |
| Evaluation prompt families | 48 |
| Actor seeds | 3 |
| Strongest eligible baseline | Activation magnitude |
| Candidate-tracer mean selection regret | 0.00 |
| Strongest-baseline mean selection regret | 2.95 |
| Mean baseline-minus-tracer regret | 2.95 |
| Family bootstrap 95% interval | `[2.95, 2.95]` |
| Each seed favorable | Yes |
| Patching direction confirmed | Yes |
| Structural bundle validation | Valid |
| Gate classification | `PositiveControlPass`; scientific Stage 0 exit remains blocked |
| Reviewed manifest digest | `2c367ff91ad37f4c782aad9297580afb73669529b9b096151eeed3a70c31796c` |

The interval is degenerate because every evaluation family instantiates the same
planted causal topology and yields the same regret difference. This is expected
for the frozen synthetic actor and limits the result: the run validates the
harness against its planted circuit, not variation in learned circuits.

The bundle was written to a repository-external temporary directory and was not
promoted into the repository. Its manifest recorded the dirty worktree. The
digest identifies that temporary bundle but does not make it durable evidence.

This positive-control result shows that the local harness correctly distinguishes a
readout-weighted signal head from a high-activation, low-readout distractor,
reproduces the direction under matched-counterexample patching, preserves three
seed results, and rejects artifact tampering in focused tests. It does not
validate a learned-model tracer, sparse feature dictionary, observer,
Introspection Gap, mechanistic supervision, or self-correction. Stage 1 still
requires a separately authorized state slice. Before any scientific Stage 0
exit, the planted actor must be replaced with a genuinely learned or
independently compiled circuit, the tracer must not be algebraically identical
to the intervention answer, competitive baselines and the remaining secondary
endpoints must be implemented, the preregistration and analysis payload must be
durably hashed, and an independent reviewer must approve the frozen protocol.
