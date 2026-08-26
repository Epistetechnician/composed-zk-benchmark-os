# Verified Self-Model Benchmark PRD

State slice: `verified-self-model-benchmark-prd-v1`.

Status: `Proposed / LocalDevelopmentOnly`.

## Executive decision

Build a bounded benchmark for predictive self-modeling as a speculative research
instrument. Keep verified metacognitive monitoring/control as the product lane.
The benchmark measures whether an agent can forecast its own success,
limitations, counterfactual variant effects, and belief updates under externally
verified outcomes. It does not establish a complete self-model, consciousness,
introspection, mechanistic causal knowledge, or production readiness.

The current implementation is a process-free, aggregate-only contract harness.
The smoke fixture is `ContractSmokeOnly`; no live agent, model, network, or
external runner has been authorized by this slice.

## Why this benchmark exists

The useful near-term question is not whether an agent can narrate its internal
state. It is whether a controller can make calibrated, falsifiable predictions
about the agent's operating envelope and update those predictions after
verified outcomes.

The benchmark therefore separates four capabilities:

1. `capability_forecast`: probability that the next bounded task succeeds.
2. `limitation_detection`: the externally verified reason a task failed or was
   constrained.
3. `counterfactual_variant_model`: predicted effect of a fixed tool, budget,
   memory, or policy change.
4. `recursive_belief_update`: whether the next forecast starts from the prior
   posterior and moves in the verified direction.

The fourth dimension is the recursive gate. A collection of accurate independent
predictions is insufficient if the model does not maintain state across a
trajectory.

## Frozen protocol

State slice: `verified-self-model-benchmark-v1`.

Each input is one manifest followed by aggregate trial records. The manifest
freezes the workflow, budget, model/runtime/checker digests for live captures,
variant order, external validator custody, and prediction locking. Each
trajectory must contain all five variants:

| Variant | Controlled change |
|---|---|
| `base` | Reference capability under the fixed workflow |
| `tool_augmented` | Additional declared tool capability |
| `budget_extended` | Larger declared resource envelope |
| `memory_reset` | Reduced retained task memory |
| `policy_restricted` | Narrower action policy/scope |

The benchmark records forecasts and verified aggregate outcomes only. Raw
prompts, raw model outputs, chain-of-thought, credentials, PII, and provider
artifacts are rejected by the schema. Authority, network access, and raw
reasoning retention must be explicitly false.

## Experimental design

The live-shaped gate requires at least 60 trajectories across at least five task
families, split into fit/tune/assessment with minimum counts `24/12/24`.
Assessment predictions must be locked before assessment outcomes are available.
Task families and splits must be disjoint at the trajectory level, and each
variant must use the same horizon sequence.

Each trajectory is recursive: for horizon `t+1`,
`prior_belief(t+1) = posterior_belief(t)`. The validator rejects duplicate
horizons, gaps, variant imbalance, metadata drift, and broken prior/posterior
links before scoring.

The initial preregistered gates are:

| Metric | Gate |
|---|---:|
| Capability Brier score | `<= 0.20` |
| Limitation classification accuracy | `>= 0.75` |
| Variant-effect mean absolute error | `<= 0.25` |
| Variant-effect direction accuracy | `>= 0.70` |
| Recursive update direction accuracy | `>= 0.75` |
| Unsafe overconfidence on failures | `<= 0.10` |

All thresholds are local-development gates, not universal scientific cutoffs.
They must be frozen before a live assessment and independently recomputed from
the input bundle.

## End-to-end execution plan

### Stage 0: contract smoke

Run the checked-in fixture, recompute the result, and confirm the output is
`ContractSmokeOnly` with `scientific_evidence=false`. This stage is complete in
the current slice.

### Stage 1: capture adapter

The read-only adapter now exists at
`experiments/self_model_benchmark/repository_change_capture.py`. It accepts a
validator-owned repository-change capture shape, requires fixed budgets,
model/runtime/checker digests, validator report custody, exact repository check
IDs, and a digest per observation. It derives outcome and limitation labels from
validator facts and emits the frozen benchmark input. The adapter executes no
commands, calls no model, retains no raw model material, and grants no
authority.

The checked-in adapter fixture is still contract smoke. The remaining Stage 1
gate is a fresh capture from one separately controlled repository-change
runner. `experiments/self_model_benchmark/capture_preflight.py` now provides
the intervening process-free readiness gate: live source type, 60 trajectories,
five families, `24/12/24` split coverage, paired variants, split isolation,
contiguous horizons, unique validator digests, resource bounds, custody,
prediction locking, and safe flags. It emits
`LocalDevelopmentSelfModelCapturePreflightOnly` metadata and cannot execute a
workflow, create validator custody, or promote its own fixture. A preflight
pass is necessary for Stage 1 capture but is not benchmark or scientific
evidence.

The capture validator enforces the fixed resource envelope on every
observation: latency, compute units, tool calls, and attempts must each remain
at or below the manifest budget. Contract tests cover all four overage
boundaries after recomputing the observation digest, so the check is semantic
budget enforcement rather than stale-digest detection.

State slice `verified-self-model-benchmark-resource-accounting-v1` adds a
digest-bound, aggregate-only resource report. It preserves overall and
per-variant success/failure counts plus mean and maximum latency, compute,
tool-call, and attempt measurements, and rechecks each maximum against the
capture budget. This report is local development metadata only; it does not
convert live captures, create external custody, or produce benchmark or
scientific evidence.

The public adapter conversion path is deliberately closed for live captures in
the current state slice; only the private deterministic contract-test helper
can build synthetic live-shaped protocol input. A future separately authorized
release phase must bind the held quarantine, manual-review decision, and
independent custody before live capture conversion is enabled.

The public execution boundary is also closed for live inputs in state slice
`verified-self-model-benchmark-execution-gate-v1`. Both `run_benchmark.py` and
`validate_benchmark.py` accept only the checked-in contract-smoke source and
reject live or unknown sources before producing or validating results. The
pure evaluator remains testable so recursive metrics and fail-closed gates can
be verified without turning synthetic live-shaped data into benchmark
evidence.

The next handoff boundary is implemented at
`experiments/self_model_benchmark/capture_handoff.py`. It builds a deterministic
plan-only packet binding the source revision, task/corpus digests,
model/runtime/checker digests, fixed budgets, expected capture schemas, and
distinct declared runner/validator identities. The packet requires prediction
locking and validator custody but remains `operator_authorization_status=
not_authorized`, `packet_status=ready_for_external_runner`, and
`capture_status=not_captured`. It is a handoff contract, not execution,
custody, benchmark evidence, or scientific evidence. Declared identity
separation does not establish independent custody.

The received-capture boundary is implemented at
`experiments/self_model_benchmark/capture_admission.py`. It recomputes the
capture-manifest and preflight digests and requires an external-validator
receipt to bind them to the handoff packet, task/corpus lineage,
model/runtime/checker digests, and declared runner/validator identities. A
fully valid result is only `eligible_for_manual_review`; smoke or incomplete
captures are `rejected_preflight`. The operator-authorization reference is
presence metadata, not verified authority. This slice cannot grant authority,
prove independent custody, accept evidence, or establish scientific results.

The quarantine boundary is implemented by
`experiments/self_model_benchmark/capture_quarantine.py`. It binds the
admission, handoff, capture, preflight, and validator-receipt digests into a
held manifest. Eligible live captures enter `pending_manual_review`; rejected
or smoke captures remain `rejected_preflight`. Both states force
`release_status=held`, `conversion_eligible=false`, `accepted=false`, and
`scientific_evidence=false`. This is local holding metadata, not external
custody, benchmark input, evidence acceptance, or scientific execution.

The manual-review boundary is implemented by
`experiments/self_model_benchmark/capture_review.py` and
`capture_review_decision.py`. Only an eligible live admission can produce a
pending review packet. The packet binds the held quarantine and admission
digests, freezes the review checklist, and offers only `not_evidence`,
`request_recapture`, or `reject`. The explicit decision records reviewer and
notes digests without retaining prose, and both packet and decision force
`conversion_eligible=false`, `accepted=false`, and `scientific_evidence=false`.
This is a review-state transition, not a quarantine release, benchmark input,
evidence acceptance, operator authorization, independent-custody proof, or
scientific execution. Reviewer references are supplied metadata and are not
identity verification.

The local composition test in
`experiments/self_model_benchmark/tests/test_control_plane_e2e.py` now wires
the synthetic live-shaped path through every current control-plane boundary,
both directly and through the five CLI process boundaries: handoff, admission,
quarantine, manual review, and an explicit `not_evidence` decision. It verifies
digest-bound workflow continuity and asserts that the chain remains held,
non-accepted, non-conversion-eligible, non-scientific, non-authoritative, and
offline. The test also verifies that the public adapter rejects conversion of
the same live-shaped input. A semantic tamper matrix recomputes each artifact
digest after attempting to forge authorization, admission, release,
conversion, or acceptance; all five forged states are rejected by their
boundary validators. This is composition evidence for local contracts only; it
is not external execution, custody, benchmark evidence, or scientific evidence.

### Stage 2: fit/tune corpus

Capture fresh trajectories across five task families. Fit and tune only
closed-form calibration or fixed policy parameters. No assessment outcome may
change the configuration.

### Stage 3: sealed assessment

Lock the configuration and capture the assessment split. Run the independent
validator, recompute the result from the sealed bundle, and publish aggregate
metrics plus failure counts. A candidate requires every structural, integrity,
calibration, limitation, counterfactual, recursive, and overconfidence gate.

### Stage 4: replication or stop

`keep_candidate` authorizes only a preregistered local replication. A failed
gate is a `revert_candidate` result, not a rationale to retune on assessment.
Neither result authorizes Astral Stage 0C, Stage 1, external deployment, or a
general self-model claim.

## Resource allocation

The program remains:

- `70% control-plane productization`: verified observations, bounded controller,
  audit records, and one real workflow;
- `20% evaluation`: fresh families, validator custody, negative controls,
  chronological holdout, and replication;
- `10% Astral exploration`: separately authorized telemetry research only.

The self-model benchmark cannot consume the control-plane budget by silently
becoming an execution or introspection project.

## Acceptance criteria for this slice

- The smoke fixture runs and independently validates.
- The live-shaped 60-trajectory test passes every frozen gate.
- A broken recursive prior is rejected.
- Raw/sensitive and authority-bearing fields fail closed.
- The package has no model execution, network access, authority path, or raw
  reasoning retention.
- Repository and Rust gates pass without changing Astral research boundaries.

Current claim ceiling: `ContractSmokeOnly` for the checked-in fixture;
`LocalDevelopmentSelfModelBenchmarkCandidate` is reserved for a fresh,
fully-gated live-shaped capture and remains explicitly non-scientific,
non-authoritative local evidence.
