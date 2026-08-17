# Verified metacognitive monitoring/control experiment

State slice: `verified-metacognitive-control-experiment-v1`.

This harness evaluates whether an external monitor/controller reduces costly
workflow failures under paired, fixed-budget conditions. It is aggregate-only:
it does not execute a model, retain raw reasoning, grant authority, or establish
general metacognition.

`controller.py` contains the fixed recommendation policy used by a future live
workflow runner. It returns only `proceed`, `seek_tool`, `revise`, or `abstain`.
Its runtime boundary rejects boolean-as-integer scores/budgets and non-boolean
control flags before making a recommendation.

## Contract smoke

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.run_experiment \
  --input experiments/verified_metacognitive_control/fixtures/smoke_trials.jsonl \
  --output /tmp/verified-metacognitive-control-smoke.json

PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.validate_result \
  /tmp/verified-metacognitive-control-smoke.json \
  --input experiments/verified_metacognitive_control/fixtures/smoke_trials.jsonl
```

Expected classification: `ContractSmokeOnly`. This is contract regression, not
scientific evidence.

## Historical FSM reanalysis

The existing FSM retry pilot can be converted without copying raw prompts or
responses into the new aggregate input:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.import_fsm_replay \
  --root experiments/astral_fsm/runs/2026-08-10-micro-localize-v2 \
  --output /tmp/verified-metacognitive-control-fsm.jsonl

PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.run_experiment \
  --input /tmp/verified-metacognitive-control-fsm.jsonl \
  --output /tmp/verified-metacognitive-control-fsm.json

PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.validate_result \
  /tmp/verified-metacognitive-control-fsm.json \
  --input /tmp/verified-metacognitive-control-fsm.jsonl
```

Expected classification: `HistoricalReanalysisOnly`. The importer preserves the
historical status because the original task and arm decisions were not frozen
under this PRD and the pilot did not use a common fixed end-to-end budget.

## Live capture contract

State slice: `verified-metacognitive-control-repository-workflow-v1`.

The repository-change runner emits one capture manifest followed by one
validator observation per `(task, arm)`. The process-free adapter in
`repository_change_capture.py` converts those observations into the frozen
experiment input. It derives outcomes from validator-owned check statuses,
scope, provenance, timeout, and budget facts; it does not trust a model label
and does not execute commands or mutate a checkout.

The capture manifest must include:

- fixed budgets, the five frozen required check IDs, and the declared arm list;
- model, runtime, and checker digests;
- `prediction_locked_before_assessment=true`;
- `network_access=false`, `raw_reasoning_retained=false`, and
  `authority_granted=false`.

Each observation must include:

- task/family/split and arm;
- controller decision and monitor score/source;
- statuses for exactly `format`, `focused_tests`, `contract_validation`,
  `diff_hygiene`, and `claim_boundary`; JSON object key order is not semantic;
- scope, provenance, timeout, budget, capability-gap, and safe-abstention flags;
- total latency, compute units, tool calls, and attempts;
- monitor overhead;
- prediction-lock, network, raw-retention, and authority flags.

All numeric measurements are required to be finite, nonnegative, and genuinely
numeric at capture and join ingress; `Infinity`, `NaN`, and boolean-as-integer
values are rejected before aggregation.

Run the adapter, evaluator, and independent validator together:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.repository_change_capture \
  --input experiments/verified_metacognitive_control/fixtures/repository_observations_smoke.jsonl \
  --output /tmp/verified-metacognitive-repository-smoke.jsonl

PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.run_experiment \
  --input /tmp/verified-metacognitive-repository-smoke.jsonl \
  --output /tmp/verified-metacognitive-repository-smoke.json

PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.validate_result \
  /tmp/verified-metacognitive-repository-smoke.json \
  --input /tmp/verified-metacognitive-repository-smoke.jsonl
```

Expected classification: `LocalDevelopmentNoCandidate`. The fixture proves
the capture-to-evaluation path only; it is intentionally below the 60-task,
five-family, fit/tune/assessment promotion structure.

The live manifest must set `source_type=live_workflow_capture` and
`fixed_budget=true`. The executable promotion guard also requires the five
preregistered promotion arms, at least 60 paired tasks across at least five task
families, split counts of at least `fit=24`, `tune=12`, and `assessment=24`,
task IDs that occur in only one split, unique `(task, split, arm)` rows, and a
shuffled-monitor control that fails the same metric gate. Smoke and historical
inputs cannot become candidates regardless of their point estimates.
The shuffled-control predicate is the same four-threshold predicate used for
promotion; if the shuffled arm passes it, the negative-control gate is false.

Promotion metrics are computed from the sealed `assessment` split only. The
pooled arm summaries remain descriptive context and cannot rescue an assessment
failure.

## Validator preflight

State slice: `verified-metacognitive-control-repository-validator-v1`.

`repository_change_validator.py` is a read-only validator boundary. It accepts
only a fixed profile, invokes commands with `shell=False`, disables Cargo
network resolution, discards stdout/stderr, records only status/exit/timeout
and aggregate resource values, checks the Git base revision, and rejects
out-of-scope paths. Its report is digest-bound and must be carried into the
live capture manifest with `validator_custody=true`. Its output is explicitly
`LocalDevelopmentValidatorPreflightOnly`; it is not an experiment input and
does not establish paired agent execution.

The corpus gate is separate:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.corpus_preflight \
  --input /path/to/frozen-corpus-plan.json \
  --output /tmp/verified-metacognitive-corpus-preflight.json
```

The preflight requires the five frozen promotion arms, 60 paired task IDs, five
task families, split minima of `24/12/24`, split-disjoint IDs, and unique
task-arm rows. A failed preflight cannot be promoted by the evaluator.

The validator report can be produced only from a plan bound to an absolute
checkout top-level and expected Git revision. Non-Git directories and nested
paths are rejected before any fixed check command runs:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.repository_change_validator \
  --plan /path/to/validator-plan.json \
  --output /tmp/verified-metacognitive-validator-report.json
```

The report remains a local validator preflight until a separately controlled
agent runner supplies paired, prediction-locked observations to the capture
adapter.

## Plan-only execution launcher

State slice: `verified-metacognitive-control-execution-launch-v1`.

`corpus_execution_launcher.py` is the deterministic handoff between corpus
preflight and a future agent runner. It accepts only a preflight-valid corpus
with explicit task-spec, controller-config, and per-arm digests. It emits
exactly 300 rows: 60 paired cases multiplied by the five frozen promotion
arms. Every row is bound to the source corpus, task identity, arm identity,
task specification, and controller configuration.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.corpus_execution_launcher \
  --input /path/to/frozen-corpus-plan.json \
  --output /tmp/verified-metacognitive-execution-plan.json
```

The output is `launch_status=planned_not_run` and
`LocalDevelopmentExecutionPlanOnly`. It contains no agent output, validator
custody, provider call, checkout mutation, or experiment evidence. A separate
runner must consume the plan and return prediction-locked aggregate records;
the plan launcher cannot promote itself into an experiment result.

## Paired execution join

State slice: `verified-metacognitive-control-paired-execution-v1`.

`paired_execution_join.py` is the only handoff from validator preflight to
live-shaped capture. It requires:

- the exact plan-only execution matrix and its digest;
- a digest-valid validator report with `validator_custody=true`;
- exactly one agent record for every validator `(task, split, arm)` row;
- matching task-family metadata on each validator/agent row pair;
- distinct candidate-workspace and agent-run digests;
- frozen promotion arms and check IDs;
- prediction locking, no raw reasoning, no network, and no authority.

The plan-bound validator requires every agent record to carry the plan digest,
source corpus digest, task digest, arm digest, task-spec digest, and
controller-config digest from its planned row. It rejects incomplete coverage,
unknown rows, duplicate rows, and any binding mismatch before the join emits a
capture bundle.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.paired_execution_join \
  --validator-report /path/to/validator-report.json \
  --agent-records /path/to/agent-records.jsonl \
  --execution-plan /path/to/execution-plan.json \
  --output /tmp/verified-metacognitive-paired-capture.jsonl
```

The resulting capture can then pass through `repository_change_capture.py`,
`run_experiment.py`, and `validate_result.py`. The joiner does not execute an
agent and cannot create scientific evidence by itself.

## Campaign artifact-chain verification

State slice: `verified-metacognitive-control-campaign-verification-v1`.

`campaign_verifier.py` is the final local consistency gate. It recomputes the
plan-bound execution join, compares the committed capture to that join,
compares the protocol input to deterministic capture conversion, and
recomputes the aggregate result. It performs no agent or provider execution.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.campaign_verifier \
  --execution-plan /path/to/execution-plan.json \
  --validator-report /path/to/validator-report.json \
  --agent-records /path/to/agent-records.jsonl \
  --capture /path/to/capture.jsonl \
  --protocol-input /path/to/protocol-input.jsonl \
  --result /path/to/result.json \
  --output /tmp/verified-metacognitive-campaign-verification.json
```

The report is `LocalDevelopmentCampaignVerificationOnly` with
`scientific_evidence=false`. It verifies artifact consistency; it does not
authorize a live run, promote a candidate, or establish production readiness.
An independent result validator rejects `keep_candidate` unless this report is
also supplied and its digest matches the result. This keeps a live-shaped
result from being accepted outside the verified artifact chain. During report
generation, the verifier may recompute a candidate-shaped result only as a
pending artifact-chain output; that internal recomputation flag is not exposed
by the result validator CLI and cannot approve the candidate by itself.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s experiments/verified_metacognitive_control/tests -p 'test_*.py' -v
```

The independent validator requires `--input` so every CLI result is
recomputed from its manifest-plus-trial source. It returns JSON with
`valid=false` and exit code `2` for missing, malformed, or inconsistent result
or input documents; protocol failures do not escape as a traceback. Candidate
acceptance additionally requires
`--campaign-verification /path/to/verification.json`.

## Operational campaign ledger

State slice: `verified-metacognitive-control-campaign-ledger-v1`.

`campaign_ledger.py` materializes a digest-chained operational handoff ledger
after the campaign verifier succeeds. Its legal frontier is monotonic:
planned → execution → validator → capture → protocol input → result → verified
local chain. Each event binds an artifact digest, event digest, predecessor
digest, and fixed record count where applicable.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.campaign_ledger \
  --execution-plan /path/to/execution-plan.json \
  --validator-report /path/to/validator-report.json \
  --agent-records /path/to/agent-records.jsonl \
  --capture /path/to/capture.jsonl \
  --protocol-input /path/to/protocol-input.jsonl \
  --result /path/to/result.json \
  --campaign-verification /path/to/verification.json \
  --output /tmp/verified-metacognitive-campaign-ledger.json
```

The ledger is `LocalDevelopmentCampaignLedgerOnly`; it is not the repository
Evidence Ledger, not scientific evidence, and not an authority or production
readiness record. A partial ledger can be resumed only by appending the next
legal event; tampered or skipped frontiers fail closed.

## Pending human-review gate

State slice: `verified-metacognitive-control-campaign-review-v1`.

`campaign_review.py` consumes the verified result, campaign verification
report, and complete operational ledger. It emits a digest-bound review packet
with a bounded recommendation: `keep_candidate`, `revert_candidate`, or
`not_evidence`. The packet always remains `pending_manual_review` with
`accepted=false` and `human_review_required=true`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.campaign_review \
  --result /path/to/result.json \
  --campaign-verification /path/to/verification.json \
  --campaign-ledger /path/to/campaign-ledger.json \
  --output /tmp/verified-metacognitive-review-packet.json
```

This is `LocalDevelopmentCampaignReviewOnly`. It does not append to the
repository Evidence Ledger, authorize a candidate, or establish production
readiness.

## Explicit review decision

State slice: `verified-metacognitive-control-campaign-review-decision-v1`.

`campaign_review_decision.py` records the disposition after a human has
reviewed the pending packet. The allowed dispositions are
`keep_candidate`, `revert_candidate`, and `not_evidence`; changing the packet
recommendation requires an override reason. Reviewer identity, notes, and
override rationale are stored only as SHA-256 digests, so the decision artifact
does not retain review prose or raw reasoning.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.campaign_review_decision \
  --review-packet /path/to/verified-metacognitive-review-packet.json \
  --decision not_evidence \
  --reviewer-ref operator-ref-1 \
  --notes "reviewed verified artifact chain and bounded disposition" \
  --output /tmp/verified-metacognitive-review-decision.json
```

The output is `LocalDevelopmentCampaignReviewDecisionOnly` with
`reviewed=true` and `accepted=false`. It is a human-review record, not
candidate acceptance, a repository Evidence Ledger append, authority, or
production readiness. This tooling records no real disposition until an
operator supplies the reviewer reference, notes, and decision.

## Sealed-pilot preflight

State slice: `verified-metacognitive-control-sealed-pilot-preflight-v1`.

`sealed_pilot_preflight.py` verifies the complete plan, validator, execution,
capture, protocol, result, verification, operational-ledger, review-packet,
and review-decision chain. It then freezes the configuration for a possible
future sealed pilot. It does not run that pilot. The source corpus is marked
non-reusable, a fresh future corpus is required, assessment outcomes remain
sealed from the controller, and authorization remains `not_granted`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.sealed_pilot_preflight \
  --execution-plan /path/to/execution-plan.json \
  --validator-report /path/to/validator-report.json \
  --agent-records /path/to/agent-records.jsonl \
  --capture /path/to/capture.jsonl \
  --protocol-input /path/to/protocol-input.jsonl \
  --result /path/to/result.json \
  --campaign-verification /path/to/verification.json \
  --campaign-ledger /path/to/campaign-ledger.json \
  --review-packet /path/to/review-packet.json \
  --review-decision /path/to/review-decision.json \
  --output /tmp/verified-metacognitive-sealed-pilot-preflight.json
```

The preflight is either `ready_for_sealed_pilot_authorization` or `blocked`.
The ready state is only a local preflight outcome; it is not authorization,
execution, candidate acceptance, Evidence Ledger mutation, scientific
evidence, or production readiness. Contract smoke and synthetic all-success
inputs correctly remain blocked because they do not establish the live
candidate gate.

## Fresh-corpus admission

State slice: `verified-metacognitive-control-fresh-corpus-admission-v1`.

`fresh_corpus_admission.py` accepts only a ready sealed-pilot preflight and a
new preflight-valid corpus plan. It rejects source-corpus digest reuse, source
case-set reuse, workflow-id reuse, task/controller/arm drift, and any plan that
is not exactly the frozen 60-task, five-arm, `24/12/24` matrix. It embeds the
new 300-row plan for deterministic replay, but leaves execution
`not_started` and authorization `not_granted`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.fresh_corpus_admission \
  --sealed-pilot-preflight /path/to/sealed-pilot-preflight.json \
  --fresh-corpus /path/to/fresh-corpus-plan.json \
  --output /tmp/verified-metacognitive-fresh-corpus-admission.json
```

The output is `LocalDevelopmentFreshCorpusAdmissionOnly`. It is a
plan-only admission proposal, not semantic proof that task content is novel,
not execution authorization, not candidate acceptance, not Evidence Ledger
mutation, and not scientific or production evidence.

## Sealed-pilot execution request

State slice: `verified-metacognitive-control-sealed-pilot-execution-request-v1`.

`sealed_pilot_execution_request.py` creates the final local handoff before an
external runner. It binds the fresh-corpus admission and 300-row execution
matrix, requires explicit operator checks, requires external runner custody,
and declares the aggregate artifacts that must return for independent
verification. It remains `pending_operator_authorization` with execution
`not_started` and authorization `not_granted`.

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m experiments.verified_metacognitive_control.sealed_pilot_execution_request \
  --fresh-corpus-admission /path/to/fresh-corpus-admission.json \
  --output /tmp/verified-metacognitive-sealed-pilot-execution-request.json
```

The output is `LocalDevelopmentSealedPilotExecutionRequestOnly`. It is a
request envelope, not operator authorization, pilot execution, candidate
acceptance, Evidence Ledger mutation, scientific evidence, or production
readiness.
