# Verified self-model benchmark

State slice: `verified-self-model-benchmark-v1`.

This package is a process-free, aggregate-only benchmark contract. It scores
forecasted capability, externally verified limitations, fixed counterfactual
variants, and recursive belief updates. It does not execute an agent, call a
model, use the network, retain raw reasoning, grant authority, or establish a
general self-model.

## Contract smoke

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.run_benchmark \
  --input experiments/self_model_benchmark/fixtures/smoke.jsonl \
  --output /tmp/self-model-benchmark-smoke.json

PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.validate_benchmark \
  /tmp/self-model-benchmark-smoke.json \
  --input experiments/self_model_benchmark/fixtures/smoke.jsonl
```

Expected result: `ContractSmokeOnly`, `decision=not_evidence`, and
`scientific_evidence=false`.

## Public execution gate

State slice: `verified-self-model-benchmark-execution-gate-v1`.

The public `run_benchmark.py` and `validate_benchmark.py` CLIs accept only
`contract_smoke_fixture` input. They reject live or unknown sources before
writing or validating a result, until a separately authorized release binds
the live capture to quarantine, manual review, and independent custody. The
pure `evaluate()` function and private contract-test helper remain available
for deterministic protocol tests; neither path creates scientific evidence
or authority.

The protocol and repository-capture validators reject non-object record and
cross-record inputs with the package's domain error rather than leaking parser
or attribute exceptions.

## Repository-change capture adapter

`repository_change_capture.py` is the read-only Stage 1 adapter. It accepts a
capture manifest followed by one aggregate observation per
`(trajectory, variant, horizon)`. The manifest binds the fixed repository
checks, budget, model/runtime/checker digests, validator report digest, and
validator custody. Each observation binds the validator-owned facts and its own
digest. The adapter derives `actual_outcome`, `actual_success`, and
`actual_limitation` from those facts; it never trusts a model-provided outcome.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.repository_change_capture \
  --input experiments/self_model_benchmark/fixtures/repository_change_capture_smoke.jsonl \
  --output /tmp/self-model-repository-input.jsonl

PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.run_benchmark \
  --input /tmp/self-model-repository-input.jsonl \
  --output /tmp/self-model-repository-result.json

PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.validate_benchmark \
  /tmp/self-model-repository-result.json \
  --input /tmp/self-model-repository-input.jsonl
```

The checked-in adapter fixture is intentionally below the live minimum and
returns `ContractSmokeOnly`. It is a handoff and integrity test, not a real
workflow capture. A real capture still requires a separately controlled runner
to provide prediction-locked aggregate forecasts and independent validator
labels. Public conversion rejects live captures until a separately authorized
release phase binds quarantine, review, and custody. The private
contract-test helper exists only for deterministic gate tests. This package
never executes repository checks or an agent.

## Capture preflight

`capture_preflight.py` is the process-free corpus gate between capture and
conversion. It rejects smoke sources and incomplete live-shaped captures when
they lack 60 trajectories, five families, the `24/12/24` split minimums,
paired variants, split-isolated trajectories, contiguous horizons, unique
validator digests, fixed-resource compliance, custody, prediction locking, or
safe flags. A rejected but well-formed capture produces a report with
`status=preflight_rejected`; malformed or unsafe records fail closed.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.capture_preflight \
  --input experiments/self_model_benchmark/fixtures/repository_change_capture_smoke.jsonl \
  --output /tmp/self-model-capture-preflight.json
```

The report is readiness metadata only. `preflight_valid` does not mean that a
workflow ran, that a model was executed, or that benchmark/scientific evidence
exists. Its claim ceiling is `LocalDevelopmentSelfModelCapturePreflightOnly`.

The capture validator enforces the fixed resource envelope on every observation:
latency, compute units, tool calls, and attempts must each remain at or below
the manifest budget. The repository-capture contract tests exercise all four
overage boundaries after recomputing the observation digest.

## Resource accounting

State slice: `verified-self-model-benchmark-resource-accounting-v1`.

`resource_accounting.py` emits a digest-bound, aggregate-only report with
overall and per-variant success/failure counts plus mean and maximum latency,
compute, tool-call, and attempt measurements. It accepts only a complete set
of frozen variants and rechecks every maximum against the capture budget. The
report is local development metadata; it does not convert a live capture,
create external custody, or produce benchmark/scientific evidence.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.resource_accounting \
  --input /path/to/validated-self-model-capture.jsonl \
  --output /tmp/self-model-resource-accounting.json
```

## External-runner handoff

`capture_handoff.py` creates the plan-only packet that a separately controlled
runner would receive before capture. The request binds a 40-character source
revision, task and corpus digests, model/runtime/checker digests, fixed
budgets, the exact five variants and repository checks, expected capture
schemas, and distinct declared runner/validator identities. It requires
prediction locking and validator custody while keeping operator authorization
`not_authorized`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.capture_handoff \
  --input /path/to/self-model-capture-handoff-request.json \
  --output /tmp/self-model-capture-handoff-packet.json
```

The packet is always `ready_for_external_runner` and `not_captured`. It cannot
execute the runner, grant authority, use the network, or become benchmark or
scientific evidence. Its claim ceiling is
`LocalDevelopmentSelfModelCaptureHandoffOnly`. Declared identity separation
is a contract check, not proof of independent custody.

## Capture admission

`capture_admission.py` is the process-free receipt gate after an external
runner returns a capture. It recomputes the capture-manifest digest and
preflight report, then requires the validator receipt to bind both to the
handoff packet, task/corpus lineage, model/runtime/checker digests, and
declared runner/validator identities. A live-shaped capture becomes
`eligible_for_manual_review`; a smoke or incomplete capture becomes
`rejected_preflight`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.capture_admission \
  --handoff /path/to/self-model-capture-handoff-packet.json \
  --capture /path/to/self-model-repository-capture.jsonl \
  --receipt /path/to/external-validator-receipt.json \
  --output /tmp/self-model-capture-admission.json
```

The operator-authorization reference in the receipt is presence metadata only;
this package does not verify the operator, grant authority, accept evidence, or
prove independent custody. The admission claim ceiling is
`LocalDevelopmentSelfModelCaptureAdmissionOnly`.

## Capture quarantine

`capture_quarantine.py` makes the post-admission hold explicit. It accepts a
validated admission report, binds the admission, handoff, capture, preflight,
and receipt digests, and emits `release_status=held`. An eligible live capture
becomes `pending_manual_review`; a smoke or rejected capture remains
`rejected_preflight`. Both states are non-promoting and retain no raw material.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.capture_quarantine \
  --admission-report /path/to/self-model-capture-admission.json \
  --output /tmp/self-model-capture-quarantine.json
```

The quarantine manifest is local holding metadata, not external custody,
manual review, benchmark input, evidence acceptance, or scientific evidence.
Its claim ceiling is `LocalDevelopmentSelfModelCaptureQuarantineOnly`.

## Manual review boundary

`capture_review.py` converts only an eligible, held quarantine manifest into a
pending review packet. The packet freezes the quarantine and admission
digests, requires human review, and offers only `not_evidence`,
`request_recapture`, or `reject`. It sets `conversion_eligible=false` and
cannot become benchmark input.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.capture_review \
  --quarantine-manifest /tmp/self-model-capture-quarantine.json \
  --output /tmp/self-model-capture-review-packet.json
```

`capture_review_decision.py` records the explicit disposition. Reviewer
references and notes are accepted only transiently and stored as digests; raw
prose is not retained. Every disposition remains
`conversion_eligible=false`, `accepted=false`, and
`scientific_evidence=false`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.self_model_benchmark.capture_review_decision \
  --review-packet /tmp/self-model-capture-review-packet.json \
  --decision not_evidence \
  --reviewer-ref /path/to/operator-reference \
  --notes 'Checklist reviewed; retain no raw material.' \
  --output /tmp/self-model-capture-review-decision.json
```

The reviewer reference is a supplied identifier, not verified identity or
authority. A review decision closes the local review state only; it does not
release quarantine, authorize external custody, convert a capture, append
evidence, or establish a scientific result. The packet and decision claim
ceilings are
`LocalDevelopmentSelfModelCaptureReviewOnly` and
`LocalDevelopmentSelfModelCaptureReviewDecisionOnly`.

## Local control-plane E2E

State slice: `verified-self-model-benchmark-control-plane-e2e-v1`.

`test_control_plane_e2e.py` composes the synthetic live-shaped path both
through direct calls and through the five CLI process boundaries: handoff,
admission, quarantine, manual review, and a `not_evidence` decision. It
asserts digest-bound workflow continuity and that every post-capture artifact
remains held, non-accepted, non-conversion-eligible, non-scientific,
non-authoritative, and offline. It also asserts that the public adapter still
rejects conversion of the same live-shaped capture. Its tamper matrix rewrites
valid artifact digests after attempting authorization, admission, release,
conversion, and acceptance mutations; each validator must reject the forged
state.
This is a local composition contract, not a live workflow or benchmark result.

## Live-shaped benchmark

A live capture must contain at least 60 trajectories across five task families,
with fit/tune/assessment minimums of `24/12/24`. Every trajectory contains the
same five variants: `base`, `tool_augmented`, `budget_extended`, `memory_reset`,
and `policy_restricted`. The validator requires digest-bound trial records,
externally verified aggregate outcomes, prediction locking before assessment,
and continuous prior/posterior belief updates across horizons.

The current live-shaped unit test creates 300 rows: 60 trajectories multiplied
by five variants. It is a contract test, not a live run and not scientific
evidence. A future separately controlled runner must produce a fresh capture,
pass capture preflight, and then bind those rows to one real workflow without
adding model execution or authority to this package.

## Claim boundary

The benchmark can produce only a local development candidate after all gates
pass. It cannot prove introspection, consciousness, mechanistic self-knowledge,
causal understanding, production readiness, or Astral Stage 0C/Stage 1 status.
