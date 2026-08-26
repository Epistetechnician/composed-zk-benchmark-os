# Continual-learning protocol harness

`benchmark.py` is a deterministic, leakage-controlled setup benchmark. It
separates:

- acquisition after one update with source context removed;
- retention after three interfering task updates;
- recovery after explicit reacquisition;
- a context-only leakage control; and
- bounded replay, sequential-update, and persistent-retrieval controls.

Run the hermetic tests with:

```text
python -m pytest -q experiments/continual_learning/tests
```

Run the protocol into an external artifact directory:

```text
python experiments/continual_learning/benchmark.py --output /tmp/continual-learning-v1
```

This harness validates endpoint definitions and control behavior. It is not a
neural-training result and cannot support breakthrough, transfer, production,
or general continual-learning claims.

The latest signed task/update pilot is documented in
`docs/research/continual-learning/37-v18-route-boundary-representation-record.md`. Its outputs
must stay outside the repository because adapter weights and raw run logs are
generated artifacts, not source fixtures.

## V19 update governance

`update_governance.py` is the digest-only deployment-governance contract for
the next research lane. It validates tenant-scoped update candidates, consent,
safety and utility non-regression, canary outcomes, optimistic parent binding,
append-only promotion, quarantine, rollback, and bundle readback. It executes
no model and grants no deployment authority. The protocol and claim ceiling
are documented in
`docs/research/continual-learning/38-v19-update-governance-protocol.md`.

## V20 source admission

`source_admission.py` is the raw-content-free source-to-update-data boundary
for V19. It binds one tenant and update window to declared source kind,
consent, event/label digests, quality-receipt digests, duplicate/conflict
checks, and explicit poisoning markers. Decisions are `accepted`,
`quarantined`, or `unknown`; only a fully accepted batch emits a deterministic
update-data digest. Bundle export and independent readback are included. The
contract verifies structure only: it does not verify source identity, quality,
expertise, poisoning, consent authority, or any model behavior. The protocol
and claim ceiling are documented in
`docs/research/continual-learning/39-v20-source-admission-protocol.md`.

## V21 fork topology

`fork_topology.py` defines the digest-only persistent state topology needed
before a future learner can update weights or adapters. It separates the
shared model head from tenant heads, rejects cross-tenant and stale-parent
branches, requires explicit reviewed tenant-to-shared merge proposals, keeps
rollback append-only, and emits metadata-only portable lineage manifests. It
does not store weights, execute training or inference, or grant deployment
authority. The protocol and claim ceiling are documented in
`docs/research/continual-learning/40-v21-fork-topology-protocol.md`.

## V22 local model/runtime execution

`runtime_seam.py` loads the already-cached Qwen checkpoint through MLX, runs a
bounded four-label inference probe, and emits an externally stored runtime and
model-manifest receipt. `validate_runtime_receipt.py` independently validates
the receipt. This is local runtime evidence, not a learning, provider, or
production result. The protocol is documented in
`docs/research/continual-learning/41-v22-runtime-execution-protocol.md`.
The runtime receipt also binds a model-config-derived tokenizer policy. The
policy leaves Qwen/Llama unchanged and enables `fix_mistral_regex` only for
`nemotron_h`; bounded training compatibility probes use the explicit
`safe_training_command()`/`safe_mlx_lora.py` path.
`training_seam_smoke.py` and `validate_training_seam_receipt.py` provide the
two-iteration external-artifact smoke and independent readback boundary. It is
training compatibility evidence only, never acquisition or retention evidence.

## V23 independent execution campaign

`independent_replication.py` executes two fixed seed/order cases as separate
subprocesses and invokes the existing benchmark validator as a separate
process. Outputs remain immutable and outside the repository. The protocol and
claim ceiling are documented in
`docs/research/continual-learning/42-v23-independent-replication-protocol.md`.

## V24 provider and production validation

The existing feature-gated Phala/dstack operator-live provider client is
covered by `pnpm run verify:provider`. A live provider call remains operator
controlled and requires an endpoint, non-secret invocation JSON, an
allowlisted out-of-band credential, a named environment, and rollback policy.
The protocol is documented in
`docs/research/continual-learning/43-v24-provider-production-validation-protocol.md`.

## V26 task-routed adapter-bank candidate

`routed_adapter_bank_candidate_v26.py` evaluates an append-only task-routed
adapter bank against shared sequential and replay baselines under a frozen
held-out task contract. `validate_routed_adapter_bank_candidate_v26.py`
independently checks prompt bytes, dataset membership, route freshness,
digests, and candidate gates. The three-case result is documented in
`docs/research/continual-learning/46-v26-task-routed-adapter-bank-candidate-record.md`.
It is local candidate evidence only; it does not authorize provider or
production claims.

## V27 second-model replication

`routed_adapter_bank_replication_v27.py` reuses the frozen V26 route contract
against the separately cached Llama-3.2-1B-Instruct-4bit model after an
offline runtime-receipt preflight. `run_routed_adapter_bank_replication_v27.py`
executes three fresh subprocess cases and invokes the independent V27
validator. The protocol is documented in
`docs/research/continual-learning/47-v27-second-model-replication.md`.
This remains local replication evidence only; it does not authorize provider
or production claims.

The sealed V27 campaign was not replicated: all three Llama cases failed at
`2/8` routed-bank acquisition and retention. The read-only failure diagnosis
found constant-output task adapters rather than measurable interference. See
`docs/research/continual-learning/49-v27-failure-diagnosis.md`.

## V28 model eligibility

`model_eligibility_preflight_v28.py` independently validates sealed V26/V27
adapter-bank cases and runs inference-only train/held-out acquisition checks
before any future retention campaign. It rejects constant target output,
aggregate-loss-only reasoning, and any task that does not beat its own
no-update baseline. The protocol is documented in
`docs/research/continual-learning/50-v28-model-eligibility-preflight.md`.

## V29 model-candidate runtime preflight

The existing offline runtime seam and independent receipt validator accepted
the complete cached `Qwen3.6-35B-A3B-MLX-4bit` model and its exact four-label
route-bound readout. The corrected acquisition-only preflight completed four
fresh 160-step task adapters, but failed all four frozen model-eligibility
gates: T0 remained `2/8` and constant-output, while only T1 reached `4/8`.
This is runtime-compatible but not acquisition-eligible evidence. The
boundary is documented in
`docs/research/continual-learning/51-v29-model-candidate-runtime-preflight.md`.

## V30 raw-text parity repair

`routed_adapter_bank_acquisition_v30.py` tests a narrow raw-text training
serialization repair for the Qwen3.6 acquisition failure. A transient run was
quarantined; the durable rerun completed all four task adapters and the
independent validator still rejected model eligibility. The record is
documented in
`docs/research/continual-learning/52-v30-raw-text-parity-repair-record.md`.

## V31 resumable acquisition control plane

`resumable_routed_adapter_bank_acquisition_v31.py` validates V30 artifacts as
read-only input and emits immutable per-task status events, source digests, and
resource-guard receipts. Its independent validator preserves the boundary
between task-artifact readiness and assessment eligibility. The executed
control-plane receipt is documented in
`docs/research/continual-learning/53-v31-resumable-acquisition-control-plane.md`.

## V32 Qwen2.5 acquisition eligibility

`qwen25_acquisition_eligibility_v32.py` executes three fixed, disjoint
Qwen2.5 acquisition-only cases and validates each case independently before
aggregating the campaign. Two cases pass the four eligibility gates; one case
fails the all-task acquisition gate, so the campaign remains ineligible and
does not authorize retention. The record is documented in
`docs/research/continual-learning/54-v32-qwen25-acquisition-eligibility-record.md`.

## V33 Qwen2.5 acquisition diagnosis

`diagnose_qwen25_acquisition_v33.py` is a read-only diagnosis over V32. It
shows that target T0 acquisition is robust and the blocker is non-target
acquisition instability: one case ties baseline on T3 and another has a
constant-output partial acquisition on T1. The diagnosis is documented in
`docs/research/continual-learning/55-v33-qwen25-acquisition-diagnosis.md`.

## V34 Qwen2.5 raw-text acquisition repair

`qwen25_raw_text_acquisition_v34.py` tests one narrow serialization change
against the V33 diagnosis: raw-text update rows with the exact route-bound
prompt and unmasked completion labels. It executes three fresh fixed Qwen2.5
acquisition-only cases, validates each case independently, and aggregates
only after validation. Retention, provider, and production work remain
closed. The execution record is documented in
`docs/research/continual-learning/56-v34-qwen25-raw-text-acquisition-record.md`.

## V35 cross-campaign diagnosis

`diagnose_qwen25_cross_campaign_v35.py` independently validates V32 and V34
and compares non-target acquisition stability without executing a model. The
V34 raw-text boundary is consistent with 9/9 non-target stable task cases
versus 7/9 for V32, but target T0 remains seed-sensitive and both campaigns
remain 2/3 eligible. The comparison is explicitly not causal proof because
the seed sets are disjoint. The record is documented in
`docs/research/continual-learning/57-v35-cross-campaign-diagnosis.md`.

## V36 T0 task-seed versus optimizer-seed diagnosis

`qwen25_t0_seed_factorial_v36.py` separates the V34 coupling between task
construction and trainer seed. Its fixed-task/varied-optimizer and
fixed-optimizer/varied-task arms each train only T0 under the unchanged
raw-text and readout contracts. It is a diagnosis only; retention, provider,
and production work remain closed. The record is documented in
`docs/research/continual-learning/58-v36-t0-seed-factorial-diagnosis.md`.

## V37 fixed-optimizer acquisition preflight

`qwen25_fixed_optimizer_acquisition_v37.py` validates the V36 optimizer-seed
diagnosis at full four-task scale with task seeds `20260856..20260858` and
fixed optimizer seed base `20260856` plus task-id offsets. This is explicitly
a post-diagnosis repair validation, not independent confirmation. Retention,
provider, and production work remain closed. The record is documented in
`docs/research/continual-learning/59-v37-fixed-optimizer-acquisition-record.md`.

## V37 optimizer-seed policy boundary

The docs-only V37 boundary freezes one deterministic optimizer seed
(`20260856`) and three fresh task seeds (`20260859`, `20260860`, and
`20260861`) for a future separately authorized full acquisition campaign. The
policy forbids per-case seed changes, adaptive tuning, and retention before a
campaign-wide acquisition pass. Model executions are recorded separately in
the V37 repair and V40 fresh-task records. The boundary is documented in
`docs/research/continual-learning/59-v37-optimizer-seed-policy-boundary.md`.

## V38 fixed-optimizer retention preflight

`qwen25_fixed_optimizer_retention_v38.py` consumes only the durable,
campaign-eligible V37 acquisition artifacts. It independently trains raw-text
naive and bounded-replay sequential controls under the fixed optimizer-seed
policy, evaluates acquisition, post-interference retention, and recovery, and
requires replay retention to exceed naive retention. The independent case and
campaign validators preserve the source digest and retention/production
claim boundaries. The record is documented in
`docs/research/continual-learning/60-v38-fixed-optimizer-retention-record.md`.

## V39 task-order retention replication

`qwen25_fixed_optimizer_order_replication_v39.py` crosses the three V38 task
seeds with frozen orders `0213`, `0312`, and `0132`. It reuses only the
validated V37 acquisition source and independently executes the V38 retention
panel for each arm. The case and campaign validators preserve order binding,
source custody, digests, and claim ceilings. The record is documented in
`docs/research/continual-learning/61-v39-order-replication-record.md`.

## V40 fresh-task acquisition eligibility

`qwen25_fresh_fixed_optimizer_acquisition_v40.py` executes the frozen V37
repair policy on fresh task seeds `20260859`, `20260860`, and `20260861`.
It preserves the cached Qwen2.5 model, route-bound raw-text prompt, fixed
optimizer seed base `20260856`, order `0123`, and the independent acquisition
gates. Retention is fail-closed until all three acquisition cases are valid
and eligible. The record is documented in
`docs/research/continual-learning/62-v40-fresh-acquisition-record.md`.

The bounded retention continuation is implemented by
`qwen25_fresh_fixed_optimizer_retention_v40.py` and is allowed to run only
against the durable V40 acquisition root after independent campaign
validation. It preserves the V38 replay capacity, recovery budget, fixed
optimizer, and retention gate; provider and production execution remain
disabled.

## V41 fresh-task order retention replication

`qwen25_fresh_fixed_optimizer_order_retention_v41.py` crosses the V40 fresh
task seeds with frozen orders `0213`, `0312`, and `0132`. It consumes only the
durable V40 acquisition source and independently validates each retention
case. This is same-model order replication; it does not close the second-model
or provider/production gaps. The record is documented in
`docs/research/continual-learning/63-v41-order-retention-record.md`.

## V42 Nemotron target-acquisition recovery

`nemotron_target_acquisition_recovery_v42.py` recovers the exact completed
160-step target-only Nemotron adapter into durable external custody and runs
fresh isolated no-update, adapter-train, and adapter-held-out readouts.
`validate_nemotron_target_acquisition_recovery_v42.py` independently checks
source, model, task, assessment, and receipt digests. The recovered adapter
remains constant-output at `0.25` train and held-out accuracy, so all four
acquisition gates fail and retention remains closed. The source training log
does not carry the later safe-wrapper tokenizer-policy event; the receipt
records that training-policy provenance limitation explicitly. The record is
documented in
`docs/research/continual-learning/64-v42-nemotron-target-acquisition-recovery.md`.

## V43 Qwen2.5 local candidate dossier

`qwen25_candidate_dossier_v43.py` aggregates the immutable V40 fresh-acquisition,
V40 canonical-retention, and V41 order-replication campaigns into a separately
validated local-candidate decision. The frozen metric requires all three source
campaigns to remain valid and eligible with exactly 15 total cases.

`validate_qwen25_candidate_dossier_v43.py` independently reruns every source
validator, verifies source and dossier identities, and preserves the V42
Nemotron result as a valid negative boundary. This slice performs no training,
inference, network, provider, or production operation and cannot establish
provider validation, production validation, or second-model replication.

## V44 second-model replication

`qwen25_second_model_replication_v44.py` freezes the V40/V41 mechanism for the
cached Llama 3.2 1B checkpoint, fresh task seeds, and fresh order units.
`validate_qwen25_second_model_replication_v44.py` independently validates the
runtime receipt, V43 parent dossier, every isolated case, saved case
validation, and fail-closed aggregate. The artifact root is immutable and
repository-external; network, provider, production, adaptive tuning, and
positive relabeling of prior negative results remain prohibited. The protocol
record is `docs/research/continual-learning/66-v44-qwen25-second-model-replication.md`.

## V45 V44 failure diagnosis

`diagnose_qwen25_second_model_failure_v45.py` is a read-only diagnosis over the
immutable V44 source root. It independently reproduces the V44 eligibility
stop, checks task manifests, raw JSONL, adapter custody, and training receipts,
and records the conservative `TaskSpecificTargetAcquisitionFailureWithConstantReadout`
classification. `validate_qwen25_second_model_failure_v45.py` reruns the V44
validator, rechecks the complete source inventory, and recomputes every case
summary. V45 does not execute a model, mutate V44, tune the protocol, or
promote V44 as positive evidence. The protocol record is
`docs/research/continual-learning/67-v45-qwen25-second-model-failure-diagnosis.md`.

## V46 codebook-alignment counterfactual boundary

The docs-first V46 boundary freezes a paired Llama counterfactual for the
unresolved V45 task-0 codebook-alignment hypothesis. It changes only the
target codebook shift across fresh task seeds, binds identical underlying
facts across the paired arms, and keeps the V44 model, optimizer, route
prompt, and training budget fixed. V46 is diagnostic only: it does not execute
a model, mutate V44, tune after observing results, run retention, call a
provider, or authorize production. The boundary is recorded in
`docs/research/continual-learning/68-v46-llama-codebook-alignment-counterfactual-boundary.md`.

## V47 codebook-alignment counterfactual execution

`llama_codebook_alignment_counterfactual_v47.py` executes the frozen V46
paired arms against the cached Llama checkpoint. Each fresh task seed has an
identity-target arm and a matched-shift-target arm; the runner writes separate
external roots and the independent validator checks paired underlying-fact
digests, target mappings, datasets, adapters, receipts, and the held-out
accuracy delta. V47 stops after acquisition and is diagnostic only. The
execution record is
`docs/research/continual-learning/69-v47-llama-codebook-alignment-counterfactual-execution.md`.

## Qwen inference-time recirculation V1

`qwen_inference_recirculation_v1.py` implements the inference-time mechanism
from arXiv:2608.17981 for the already-cached Qwen2.5 checkpoint: a normalized
deep source residual from step `t` is mixed into a shallower destination layer
at step `t+1`, with the original weights frozen. It first requires exact
manual-path/native-path parity at `alpha=0`, then selects a fixed pair on fit
text and evaluates on disjoint fixed assessment text. The independent
validator is `validate_qwen_inference_recirculation_v1.py`; the canonical
external artifact is the `...qwen-inference-recirculation-v1-20260826-r3`
root. The result is local feasibility evidence only, not a paper replication,
general Qwen result, accepted scientific evidence, provider result, or
production authorization. The protocol record is
`docs/research/continual-learning/70-qwen-inference-recirculation-v1.md`.

## Qwen inference-time recirculation V2

`qwen_inference_recirculation_v2.py` keeps the V1 frozen inference mechanism
and broadens only the evaluation surface to 12 fit and 12 disjoint assessment
prose sequences from six repository-owned Markdown sources. It stores source
and text-unit digests without raw corpus text, selects the configuration on fit
only, and repeats the locked assessment. The independent validator is
`validate_qwen_inference_recirculation_v2.py`. V2 remains local feasibility
evidence only and does not authorize training, a paper replication, provider
execution, production, or accepted evidence. Its docs-first boundary is
`docs/research/continual-learning/71-qwen-inference-recirculation-v2-boundary.md`.
The canonical `r2` artifact is independently valid with zero-alpha parity and
deterministic repeat, but the assessment mean NLL increased by `0.001677023`.
The execution record is
`docs/research/continual-learning/72-qwen-inference-recirculation-v2-execution.md`.

## Qwen inference-time recirculation V3

`qwen_inference_recirculation_v3.py` makes the single V2 successor change of
expanding the fit-only alpha grid to `0.04`, `0.07`, `0.10`, and `0.16`, the
values used by [arXiv:2608.17981](https://arxiv.org/abs/2608.17981). The Qwen
checkpoint, frozen manual/native seam, source/destination pairs, corpus, and
assessment remain unchanged. The independent validator is
`validate_qwen_inference_recirculation_v3.py`; the canonical external artifact
is the `...qwen-inference-recirculation-v3-20260826-r1` root. V3 is a small,
mixed local feasibility signal only: it does not establish general
recirculation, reproduce the source paper, authorize training/provider use,
or create accepted scientific evidence. The protocol record is
`docs/research/continual-learning/73-qwen-inference-recirculation-v3.md`.

## Qwen inference-time recirculation V4

`qwen_inference_recirculation_v4.py` changes only the evaluation corpus from
V3. It uses eight fresh, source-disjoint repository Markdown files, producing
16 fit and 16 assessment sequences, while retaining the cached Qwen2.5 model,
frozen recurrence, four layer pairs, four paper-aligned alphas, fit-only
selection, and locked repeat. The independent validator is
`validate_qwen_inference_recirculation_v4.py`; the canonical external artifact
is the `...qwen-inference-recirculation-v4-20260826-r1` root. V4 is directional
local feasibility evidence only: it does not establish general recirculation,
reproduce the source paper, authorize training/provider use, or create accepted
scientific evidence. The protocol record is
`docs/research/continual-learning/74-qwen-inference-recirculation-v4.md`.

## Qwen inference-time recirculation V5

`qwen_inference_recirculation_v5.py` performs a fixed-transfer holdout from
V4. It carries V4's fit-selected `(12,5,0.07)` configuration into eight new,
source-disjoint repository Markdown files, producing 16 fit and 16 assessment
sequences without searching the V5 corpus. The independent validator is
`validate_qwen_inference_recirculation_v5.py`; the canonical external artifact
is the `...qwen-inference-recirculation-v5-20260826-r1` root. The transfer
result is valid but negative and remains local evidence only. The protocol
record is `docs/research/continual-learning/75-qwen-inference-recirculation-v5.md`.
