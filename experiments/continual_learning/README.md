# Continual-learning protocol harness

## MiniMind domain-specific continual-learning V1

The separately named state slice
`continual-learning-minimind-domain-specific-v1` integrates a pinned external
MiniMind source checkout with an exact-synthetic domain-sequence harness. It
compares untouched, joint-oracle, sequential full-update, cumulative LoRA,
fixed replay, and per-domain adapter controls over three ordered domains.

The canonical synthetic artifact is independently validated and classified
`SyntheticCandidate`, with `domain_adapters` selected on tune data. This is a
contract qualification only: the real MiniMind runner is sealed until a fresh
packet-bound independent Ed25519 `ACCEPT` exists.

Run the fixture and independent readback validator with:

```text
PYTHONDONTWRITEBYTECODE=1 python -B -m experiments.continual_learning.minimind_domain_specific_v1 \
  --synthetic-output /Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v1-synthetic-20260902-r2

PYTHONDONTWRITEBYTECODE=1 python -B -m experiments.continual_learning.validate_minimind_domain_specific_v1 \
  /Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v1-synthetic-20260902-r2
```

After a fresh independent receipt and external corpus manifest open the real
path with:

```text
PYTHONDONTWRITEBYTECODE=1 python -B -m experiments.continual_learning.minimind_domain_specific_v1 \
  --model-output /Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v1-model-YYYYMMDD \
  --source /Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v1-source-20260902 \
  --execution-receipt /external/review/minimind-domain-specific-v1-execution-receipt.json \
  --corpus-manifest /external/corpus/minimind-domain-specific-v1-corpus.json \
  --device cpu \
  --steps-per-stage 1
```

The corpus manifest is a JSON object with exactly `domain_a`, `domain_b`, and
`domain_c`; each domain contains exactly `fit`, `tune`, and `assessment` file
paths to external JSONL files with non-empty `text` fields.

## MiniMind domain-specific continual-learning V2

V2 is a fresh continuation after V1's independent rejection. It uses new
`materials`, `clinical`, and `finance` synthetic domains and does not import
V1 scientific artifacts. Its real path fixes the V1 review findings with
explicit pre-assessment locking, complete receipt digest binding, exact roster
checks, tokenization attrition rejection, serialized checkpoint round trips,
repeatability checks, equal token budgets, and `0700` aggregate output roots.

The V2 synthetic artifact is independently valid as
`SyntheticCandidate`; the fresh independent review returned `REJECT`, so model
execution remains sealed. The rejection is recorded in
`docs/research/continual-learning/282-minimind-domain-specific-v2-independent-review-rejection-2026-09-02.md`.

Run the V2 fixture and validator with:

```text
PYTHONDONTWRITEBYTECODE=1 python -B -m experiments.continual_learning.minimind_domain_specific_v2 \
  --synthetic-output /Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v2-synthetic-20260902-r2 \
  --source /Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v2-source-20260902

PYTHONDONTWRITEBYTECODE=1 python -B -m experiments.continual_learning.validate_minimind_domain_specific_v2 \
  /Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v2-synthetic-20260902-r2
```

V2 protocol, review packet, manifest, and execution record:

- `docs/research/continual-learning/278-minimind-domain-specific-v2-protocol.md`
- `docs/research/continual-learning/279-minimind-domain-specific-v2-review-packet.md`
- `docs/research/continual-learning/280-minimind-domain-specific-v2-implementation-manifest.json`
- `docs/research/continual-learning/281-minimind-domain-specific-v2-execution-record-2026-09-02.md`

## MiniMind domain-specific continual-learning V3

V3 is a fresh continuation after V2's independent `REJECT`. It adds an
external trust-bundle and root-signed reviewer registry, aggregate-only
synthetic/model output schemas, fresh corpus identity with global document and
author disjointness, explicit V1/V2 prior-root exclusion, strict typed guards,
and receipt binding for the current source and corpus manifests. The fresh
synthetic factorial has 108 aggregate trials and independently validates as
`SyntheticCandidate`. A new independent certificate-backed packet-bound
Ed25519 `ACCEPT` was obtained and revalidated before the bounded offline
MiniMind run. The model contract independently validates as
`ModelContractValid` with 78 aggregate trials. This remains qualification
evidence only; no checkpoint was retained and no general continual-learning
or SOTA claim is supported.

Run the V3 fixture and independent validator with:

```text
PYTHONDONTWRITEBYTECODE=1 python -B -m experiments.continual_learning.minimind_domain_specific_v3 \
  --synthetic-output /Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v3-synthetic-20260902 \
  --source /Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v3-source-20260902

PYTHONDONTWRITEBYTECODE=1 python -B -m experiments.continual_learning.validate_minimind_domain_specific_v3 \
  /Users/shaanp/Documents/research-artifacts/continual-learning-minimind-domain-specific-v3-synthetic-20260902
```

The fresh corpus manifest is external and must be revalidated before model
import. A valid receipt is required before the tiny offline fit/tune/lock/
assessment campaign.

V3 protocol, review packet, implementation manifest, and execution record:

- `docs/research/continual-learning/283-minimind-domain-specific-v3-protocol.md`
- `docs/research/continual-learning/284-minimind-domain-specific-v3-review-packet.md`
- `docs/research/continual-learning/285-minimind-domain-specific-v3-implementation-manifest.json`
- `docs/research/continual-learning/286-minimind-domain-specific-v3-execution-record-2026-09-02.md`

## MiniMind state-of-the-art comparison audit V1

The fresh audit slice
`continual-learning-minimind-state-of-the-art-comparison-audit-v1` defines
the published task-incremental, domain-incremental, and experience-incremental
lanes, required controls and frontier method roster, local-evidence map,
fair-budget metrics, state-channel accounting, data requirements, and claim
ladder. It does not authorize a larger model campaign. See
`docs/research/continual-learning/287-minimind-state-of-the-art-comparison-audit-v1.md`.

Protocol, review packet, implementation manifest, and execution record:

- `docs/research/continual-learning/273-minimind-domain-specific-v1-protocol.md`
- `docs/research/continual-learning/274-minimind-domain-specific-v1-review-packet.md`
- `docs/research/continual-learning/275-minimind-domain-specific-v1-implementation-manifest.json`
- `docs/research/continual-learning/276-minimind-domain-specific-v1-execution-record-2026-09-02.md`

## Plasticity recovery V1 exact-synthetic factorial

`plasticity_recovery_v1.py` implements the separately authorized
`continual-learning-plasticity-recovery-v1` slice. It is an exact synthetic
adapter analogue with mechanically known state transitions, fresh deterministic
fit/tune/assessment panels, and five equal-compute arms: untouched base,
fixed adapter, bounded replay, selective low-utility reinitialization, and the
combined policy. Tune predictions are sealed before assessment effects.

`validate_plasticity_recovery_v1.py` independently validates the result JSON
without importing or executing the runner. The local artifact is stored at
`/Users/shaanp/Documents/research-artifacts/continual-learning-plasticity-recovery-v1-20260829`.
The result failed the fixed forgetting guard for every updating arm, so no
continual-learning candidate was promoted. Base weights, Astral integration,
and ZK/PQC custody proofs remain untouched or not run. GiveMeANode submission
requires a separate hard USD spend ceiling.

Protocol, authorization, and execution record:

- `docs/research/continual-learning/112-plasticity-recovery-v1-protocol.md`
- `docs/research/continual-learning/113-plasticity-recovery-v1-execution-authorization-2026-08-29.md`
- `docs/research/continual-learning/114-plasticity-recovery-v1-execution-record-2026-08-29.md`

`diagnose_plasticity_recovery_v1.py` performs the read-only V1 forgetting
diagnosis. It attributes protected-shard degradation, unit contributions,
replay targets, reinitialization events, and fit-order sensitivity without
changing the V1 result. Its independent validator is
`validate_plasticity_recovery_diagnosis_v1.py`; the diagnosis artifact is
stored at
`/Users/shaanp/Documents/research-artifacts/continual-learning-plasticity-recovery-v1-forgetting-diagnosis-20260829`.
The diagnosis remains `NoCandidate` and does not authorize a new mechanism.

## Plasticity recovery V2 protected replay

`plasticity_recovery_v2.py` tests one preregistered mechanism suggested by the
V1 diagnosis: an immutable protected replay memory containing the first four
accepted fit shards. It uses fresh panel seeds and order seeds while retaining
the V1 endpoint, thresholds, prediction lock, reversible-adapter boundary,
and hard guards. The 72-case result was independently validated. Protected
replay had the strongest held-out improvement, `0.03220089`, but failed the
unchanged per-case forgetting guard. V2 is therefore `NoCandidate`; no
cached-model, GiveMeANode, Astral, or ZK/PQC continuation is opened.

The independent validator is `validate_plasticity_recovery_v2.py`. Protocol,
authorization, and execution record:

- `docs/research/continual-learning/117-plasticity-recovery-v2-protocol.md`
- `docs/research/continual-learning/118-plasticity-recovery-v2-execution-authorization-2026-08-29.md`
- `docs/research/continual-learning/119-plasticity-recovery-v2-execution-record-2026-08-29.md`

The plasticity-recovery mechanism family is now terminally closed as
`NoCandidate`. Any continuation requires a materially new theory and estimand
addressing adaptation versus forgetting, a fresh protocol and guards, and
separate authorization. See
`docs/research/continual-learning/120-plasticity-recovery-family-terminal-closure-2026-08-29.md`.

## Information-budget frontier V1

The separately authorized
`continual-learning-information-budget-frontier-v1` slice tests a materially
new counterfactual protected-subspace projection theory. Its primary endpoint
is adaptation-forgetting frontier utility (AFFU), with untouched, fixed,
random-projection, and CPSP arms, locked fit/tune selection, and an
independent aggregate-only validator. The five-candidate synthetic run
classified as `NoCandidate`: the locked CPSP arm beat fixed cadence but did
not beat the untouched base. No model, provider, GiveMeANode, Astral, or
ZK/PQC work ran. Protocol, review receipt, and execution record:

- `docs/research/continual-learning/124-information-budget-frontier-v1-protocol.md`
- `docs/research/continual-learning/132-information-budget-frontier-v1-independent-review-receipt-2026-08-29.json`
- `docs/research/continual-learning/133-information-budget-frontier-v1-execution-record-2026-08-29.md`

## Recursive update-policy V1 protocol package

The newly authorized state slice `continual-learning-recursive-update-policy-v1`
defines a bounded test of generational update-policy improvement. The exact
synthetic learner separates adaptation, protected retention, and
post-adaptation plasticity; evaluates untouched-base, fixed-policy,
recursive-policy, and deterministic-random controls; and uses fresh
fit/tune/assessment/probe tasks for four generations. External episodic and
procedural memory is governed by freshness, contradiction, poisoning, deletion,
and promotion rules. Policy proposals are sandboxed, checkpoints are
immutable and rollback-tested, compute is fixed, and prediction locks precede
assessment.

The runner and independent aggregate-only validator are additive:

- `recursive_update_policy_v1.py`
- `validate_recursive_update_policy_v1.py`
- `tests/test_recursive_update_policy_v1.py`

The protocol is pending independent review. Its pure in-memory synthetic
contract computation currently evaluates to `NoCandidate`; this is a
qualification signal, not a retained scientific result, model result, or RSI
claim. Model-bearing execution, reversible adapters,
GiveMeANode, Astral integration, and ZK/PQC custody work remain separately
authorized boundaries. See
`docs/research/continual-learning/137-recursive-update-policy-v1-protocol.md`
and
`.autoresearch/continual-learning-recursive-update-policy-v1/contract.md`.

## Recursive update-policy V1 review and V2 result

The independent V1 review rejected the original package before execution for
non-operative rollback, incomplete custody enforcement, bypassable receipt
requirements, disconnected reserve semantics, an under-specified order guard,
and incomplete result freezing. The V1 protocol and source remain unchanged;
the review record is
`docs/research/continual-learning/138-recursive-update-policy-v1-independent-review-2026-08-29.json`.

The separate
`continual-learning-recursive-update-policy-v2` revision repaired those defects
with a causal reserve equation, stable procedural-memory prototypes, real
checkpoint restoration, exact custody-root enforcement, canonical review
receipts, an explicit base-state digest, and mechanically recomputed
classification. Its approved bounded synthetic campaign was independently
validated and classified `NoCandidate`: recursive selection lost to random
selection (`U=-0.0011354145513036448`) and compounding stayed below the locked
threshold (`G=0.004179722339390019`). All hard guards passed, but the protocol
identity is closed under its preregistered rules.

Protocol, review receipt, runner, validator, and execution record:

- `docs/research/continual-learning/139-recursive-update-policy-v2-protocol.md`
- `/Users/shaanp/Documents/research-artifacts/continual-learning-recursive-update-policy-v2-review-receipt-20260829.json`
- `recursive_update_policy_v2.py`
- `validate_recursive_update_policy_v2.py`
- `tests/test_recursive_update_policy_v2.py`
- `docs/research/continual-learning/140-recursive-update-policy-v2-execution-record-2026-08-29.md`

No cached model, reversible adapter, GiveMeANode/provider, Astral, or ZK/PQC
execution is authorized by this result. Astral remains limited to causal-effect
prediction, calibration, or instrumental correction.

## Plasticity guard with reversible adapters V1

The separately authorized state slice
`continual-learning-plasticity-guard-reversible-adapter-v1` tests only the
surviving synthetic `plasticity_guard` mechanism against the already-cached
Gemma3 1B PT checkpoint. It uses a new document-disjoint NEWSROOM cohort,
fixed forward/reverse orders and seeds, equal LoRA update budgets, per-update
candidate adapters, and rollback by active-adapter pointer. The base model is
never updated or merged. The primary endpoint is paired held-out adaptation
improvement of the guarded arm over fixed cadence; forgetting, calibration,
repeatability, adapter restore fidelity, custody, and independent validation
are hard guards. Astral integration is not run and remains limited to future
causal-effect prediction, calibration, or instrumental correction. Protocol,
authorization, and execution status are recorded in
`docs/research/continual-learning/89-plasticity-guard-reversible-adapter-v1-protocol.md`,
`90-plasticity-guard-reversible-adapter-v1-execution-authorization-2026-08-28.md`,
and `91-plasticity-guard-reversible-adapter-v1-execution-record-2026-08-28.md`.
The completed bounded run classified as `DevelopmentCandidate` with a
`0.064052287` NLL/token paired endpoint; both independent artifact-root
validations passed and the base model manifest was unchanged.

## Plasticity guard replication V1

The separately authorized state slice
`continual-learning-plasticity-guard-replication-v1` freezes the V1 result and
runs a fresh, document-disjoint NEWSROOM cohort with new seeds and permutation
orders. It adds an untouched-base/no-update arm that spends the same disposable
LoRA training budget without applying an adapter, alongside fixed cadence and
the unchanged `plasticity_guard`. Absolute held-out improvement versus the
untouched base is primary; guarded-minus-fixed improvement is secondary. The
base model remains byte-identical, adapters remain reversible, and Astral
integration is not run. Protocol, authorization, and execution status are
recorded in
`docs/research/continual-learning/105-plasticity-guard-replication-v1-protocol.md`,
`106-plasticity-guard-replication-v1-execution-authorization-2026-08-28.md`,
and `107-plasticity-guard-replication-v1-execution-record-2026-08-28.md`.
The replication classified as `RollbackInfrastructureOnly`: the guard's
absolute improvement versus the untouched base was `-0.041830065` NLL/token,
while its secondary improvement over fixed cadence was `0.117647059`.

## Gemma3 paper recirculation acquisition

### Gemma3 local mechanics pilot

`gemma3_local_pilot_v1.py` runs the separately scoped
`continual-learning-gemma3-local-pilot-v1` slice against the cached Gemma3 1B
BF16 MLX conversion. It uses four document-disjoint 256-token windows from
the registered NEWSROOM test file, stores the active immutable artifact on
PrimaryED, mirrors it to DAed, and invokes the independent
`validate_gemma3_local_pilot_v1.py` readback validator on both roots. This is a
mechanics-only local pilot, not a C4/Gemma paper replication or a general
recirculation claim. The frozen protocol and claim ceiling are documented in
`docs/research/continual-learning/78-gemma3-local-pilot-v1.md`; the completed
execution record is documented in
`docs/research/continual-learning/79-gemma3-local-pilot-execution-20260827.md`.

`gemma3_local_pilot_v2.py` is the independent fresh-cohort continuation. It
uses the next four eligible NEWSROOM test documents after V1 under the new
`continual-learning-gemma3-local-pilot-v2` slice, with new immutable roots on
PrimaryED and DAed. Its result must remain separate from V1 and below the
paper-replication claim ceiling. The completed execution record is documented
in `docs/research/continual-learning/81-gemma3-local-pilot-v2-execution-20260827.md`.

The acquisition checkpoint staged the documented OpenWebText URL lists and
the exact `OpenWebText.zip` manual input on PrimaryED with a byte-identical
DAed mirror. It did not produce the required C4 `train.jsonl` or
`validation.jsonl`; the paper-aligned acquisition gate remains blocked on the
Common Crawl WET preparation step. See
`docs/research/continual-learning/82-gemma3-c4-openwebtext-staging-20260827.md`.

The separately named bounded follow-up
`continual-learning-gemma3-paper-recirculation-c4-bounded-v1` is implemented
by `acquire_gemma3_bounded_webtextlike_wet_v1.py`. It downloads a fixed bounded
set of WET
objects from each pinned Common Crawl collection, filters locally against the
staged OpenWebText URLs, and writes only to the external PrimaryED root. It
produces a bounded WebText-like panel, not the exact TFDS `c4/webtextlike`
dataset. Its default guard is 2,000 records and 4 GiB, and its independent
readback gate is `validate_gemma3_bounded_webtextlike_wet_v1.py`. The earlier
CDX range utility remains available for small targeted probes. The protocol,
usage, and claim ceiling are documented in
`docs/research/continual-learning/83-gemma3-bounded-webtextlike-acquisition-v1.md`.

`gemma3_bounded_webtextlike_recirculation_v1.py` is the bounded execution
adapter for that validated bundle. It converts the acquired records into
256-token windows, runs the cached Gemma3 1B checkpoint offline with frozen
weights, evaluates the fixed four-pair pilot grid, locks evaluation at
`alpha=0.15` and `beta=0.85`, and writes an external result bundle. Its
independent validator is
`validate_gemma3_bounded_webtextlike_recirculation_v1.py`. This remains a
bounded local mechanics pilot and cannot be passed to the exact paper runner.

`acquire_gemma3_paper_recirculation_v1.py` is the separately authorized,
network-enabled acquisition slice for the paper-aligned Gemma3 recirculation
lane. It downloads only pinned upstream sources, requires external manual
inputs for TFDS C4 WebText-like and registered NEWSROOM data, computes raw and
normalized checksums, and publishes only an independently validated external
`gemma3-source-v1` bundle. It does not train, run the model, or mutate the
Evidence Ledger. The protocol and exact source map are documented in
`docs/research/continual-learning/77-gemma3-paper-recirculation-acquisition-v1.md`.

`validate_gemma3_paper_recirculation_acquisition_v1.py` is an independent
readback gate. The existing `stage_and_run_gemma3_paper_recirculation_v1.py`
remains offline and must not be run until this acquisition validator passes.

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

## Gemma3 paper-aligned recirculation V1

The activated state slice
`continual-learning-gemma3-paper-recirculation-v1` includes an offline Gemma3
1B PT runner, an independent validator, and
`stage_and_run_gemma3_paper_recirculation_v1.py`, an operator-facing
orchestrator. The orchestrator consumes locally acquired normalized JSONL and
an acquisition manifest, materializes the immutable external corpus with the
paper's fit counts, runs the campaign, and invokes the independent validator.
It never downloads data, overwrites existing roots, or writes experiment
artifacts into the repository. The runner uses the already-cached checkpoint
and BF16 MLX conversion, paper-shaped fit and evaluation panels, locked
configuration, parity and control gates, and external result retention. No
Gemma3 execution or result artifact exists yet. The authorization and claim
boundary are documented in
`docs/research/continual-learning/76-gemma3-paper-recirculation-authorization-proposal-v1.md`.

Prepare an external source root with `acquisition-manifest.json` and one
normalized JSONL file per protocol dataset. Each JSONL record must contain
only a stable `document_id` and raw UTF-8 `text`; the source manifest must
record each dataset source, revision, and split. The operator orchestrator
then tokenizes and windows those records with the cached Gemma tokenizer,
materializes the paper-shaped corpus, runs the campaign, and invokes the
independent validator. Existing corpus and result roots are rejected rather
than overwritten.

Example source-root shape:

```text
/external/gemma3-source-v1/
  acquisition-manifest.json
  fit/arxiv.jsonl
  fit/c4.jsonl
  fit/pg19.jsonl
  assessment/arxiv.jsonl
  assessment/big_patent.jsonl
  assessment/billsum.jsonl
  assessment/booksum-book.jsonl
  assessment/c4-webtextlike.jsonl
  assessment/gov_report.jsonl
  assessment/lambada.jsonl
  assessment/newsroom.jsonl
  assessment/pg19.jsonl
  assessment/pubmed.jsonl
```

The acquisition manifest schema is
`gemma3-paper-recirculation-acquisition-v1` and its dataset keys are
`fit/arxiv`, `fit/c4`, `fit/pg19`, plus `assessment/` followed by each exact
assessment dataset name. A dataset entry has `source`, `revision`, and
`split` strings. Run the end-to-end orchestrator with:

```text
python experiments/continual_learning/stage_and_run_gemma3_paper_recirculation_v1.py \
  --source-root /external/gemma3-source-v1 \
  --corpus-root /external/gemma3-paper-corpus-v1 \
  --model /Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16 \
  --output /Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/gemma3-paper-recirculation-v1-r1
```

Use `--pack-only` first to validate the external source and corpus without
loading the model. Acquisition itself remains operator-controlled and is not
performed by this script.

## Gemma3 OpenWebText substitute pilot

The named state slice
`continual-learning-gemma3-paper-recirculation-openwebtext-substitute-v1`
provides a bounded local substitute for the blocked TFDS `c4/webtextlike`
input. It pins `Skylion007/openwebtext`, stores 80 raw Parquet shards and
normalized source records outside the repository, mirrors them to the
dedicated GiveMeANode bucket `gemma3-openwebtext-substitute-v1`, and runs
frozen Gemma3 inference offline. The completed run used disjoint 1024-token
fit/assessment windows, fixed controls, and an independent validator; it
selected `(source=11, destination=4)` and measured a selected-minus-baseline
assessment mean-NLL delta of `-0.071975952`. The claim ceiling is
`LocalDevelopmentGemma3OpenWebTextSubstitutePilot`; this is not exact C4,
full-paper replication, general recirculation evidence, benchmark evidence,
or production readiness. See the [protocol](../../docs/research/continual-learning/84-gemma3-openwebtext-substitute-v1.md)
and [execution record](../../docs/research/continual-learning/85-gemma3-openwebtext-substitute-execution-20260828.md).

## Gemma3 FineWeb-Edu H100 replication V1

The state slice continual-learning-gemma3-fineweb-edu-replication-h100-v1 is
terminally closed as `ProtocolReviewRejectedNoExecution`. Independent review
rejected the exact packet for an invalid implementation-manifest self-digest,
missing provider cost/stop-receipt binding, and incomplete result-root
closure. No provider job, H100, model execution, or result exists. Do not
patch or retune this identity. See the [rejection receipt](../../docs/research/continual-learning/255-gemma3-fineweb-edu-replication-h100-v1-independent-review-rejection.json),
[review record](../../docs/research/continual-learning/256-gemma3-fineweb-edu-replication-h100-v1-independent-review.md),
and [terminal closure](../../docs/research/continual-learning/257-gemma3-fineweb-edu-replication-h100-v1-terminal-closure-2026-08-31.md).
