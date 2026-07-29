# V28 Gate 1 Acquisition-Qualification Preregistration

State slice:
`astral-rgs-v28-gate1-acquisition-qualification-preregistration`.

Status: `DocsFirstPreregistered / V28R2NoveltyPacketBound /
ImplementationCandidate / UpdateExecutionNotAuthorized /
RetentionRecoverySealed / SelectionSealed / AssessmentSealed`.

## Decision

V28R2 passed only the acquisition-novelty preflight. The model was at chance
on the complete sealed corpus under two byte-identical unchanged-checkpoint
baselines. Gate 1 may therefore ask whether declared update methods can acquire
the hidden source facts after context removal and restart. It may not change or
regenerate the corpus, seed, prompts, answer mappings, scorer, novelty
thresholds, or baseline observations.

This protocol is designed to produce a useful negative result efficiently.
Every persistent arm has nine required seed/order cells, but a method is
disqualified if any required cell fails. Evaluation may stop a cell only when
an exact worst-case completion bound proves that a frozen threshold can no
longer be reached. Once one cell disqualifies an arm, later cells for that arm
remain `NotRunByPreregisteredArmFutility`; they are not statistical evidence
and may not be presented as completed replications.

## Immutable V28R2 input

The only knowledge corpus and unchanged-checkpoint reference are bound by:

- RGS implementation commit
  `c7dfe08dec8f389b9f0bcf84baf0973c4d79cf78`;
- Astral implementation commit
  `4b5baefe05a48d418c0a32b1b41e7b463944e645`;
- V28R2 packet
  `sha256:5e830ee437e8d67faa9dedc667db35114fa5ccf84809a9b2874c60a1ed622ddc`;
- V28R2 validation report
  `sha256:a5a090fa7707b179bd373e3a2b76511085c47daf67f910ff55f874ed0ae5547f`;
- V28R2 artifact manifest
  `sha256:e4bba029e565445f4fe930c7aeea1e7b9f572f111df22085100018ff6ed8efde`;
- identical baseline-observation digest
  `sha256:7739c7afd1d2ca52f8e8c1acd7c01594201fbec1c7fba9500da036da5ce099d2`;
- corpus census: 6,144 families, 73,728 queries, four fact kinds, and three
  query classes.

The fixed no-update accuracy is `0.2500678168402778`. V28R1 and all V27
datasets, outcomes, adapters, and assessment material remain forbidden inputs.

## Frozen comparison matrix

### Nonpersistent controls

1. `context_only`: the exact family source and support documents are appended
   to the evaluation prompt. The base checkpoint remains unchanged.
2. `retrieval`: a deterministic lexical identifier index retrieves exactly
   one family source/support pair before scoring. Retrieval uses only query
   surface identifiers and a locked tie rule; it may not use the answer label
   or expected answer.

These controls measure access to external information. They cannot qualify a
persistent-acquisition claim and require one deterministic full-corpus run
each.

### Persistent native arms

1. `naive_sequential_lora`: one rank-eight adapter updated sequentially over
   all four fact-kind tasks.
2. `replay_lora`: the same adapter and total budget, with a deterministic 25%
   reservoir replay share after the first task.
3. `scol_style_sparse_lora`: a fixed source-only Fisher proxy ranks LoRA
   layers before updates; only the top third remains plastic. This is a
   reproducible SCoL-style sparse-plasticity control, not a reproduction of
   SCoL's learned instruction generator or meta-reinforcement learning.
4. `nested_multiscale_lora`: one adapter with prospectively assigned fast,
   medium, and slow layer groups updated every one, two, and four optimizer
   steps. This tests a bounded multi-timescale design and is not Hope or a
   replication of Nested Learning.
5. `modular_ghost_state`: one task-scoped adapter per fact kind, selected after
   restart by a locked prompt-surface router.
6. `compressed_adapter_recollection`: the modular adapters are quantized into
   content-addressed int8 archives and evaluated only after deterministic
   rehydration.
7. `representation_time_distillation`: one sequential adapter trained with
   current-source language loss plus a frozen prior-task representation anchor.

The SCoL paper motivates learned sparse update locations but requires a
separate meta-training method; the bounded control above must not inherit its
claims. Nested Learning similarly supplies a multi-timescale research design,
not validation of this implementation. OCKL motivates measuring acquisition
and retention separately; Gate 1 measures acquisition only. Primary sources:
[SCoL](https://arxiv.org/abs/2605.07076),
[Nested Learning](https://arxiv.org/abs/2512.24695), and
[OCKL](https://arxiv.org/abs/2311.09632).

## Frozen cells and update budget

Persistent seeds are exactly `280301`, `280303`, and `280307`. Required task
orders are:

- `order-abcd`: nonce, relation, changed-rule, opaque-mapping;
- `order-acdb`: nonce, changed-rule, opaque-mapping, relation;
- `order-bdac`: relation, opaque-mapping, nonce, changed-rule.

Every persistent arm begins from the byte-identical V28R2 checkpoint in every
cell. The common upper budget is:

- LoRA rank `8` over exactly six declared Transformer layers;
- `768` optimizer steps;
- `8` examples per step;
- exactly `128` tokens per example after deterministic padding/truncation;
- exactly `786,432` presented update tokens;
- AdamW learning rate `0.0001`;
- no more than `67,108,864` persistent-state bytes;
- identical source-family census and per-task token allocation.

An arm may deliberately update fewer tensors because its mechanism is sparse
or modular, but it may not exceed any budget or compensate with extra data,
steps, rank, evaluation access, or storage. Training examples contain only
V28R2 source/support text. Evaluation questions, options, labels, raw baseline
scores, and expected answers are unavailable to update processes.

## Restart and evaluation contract

Each cell uses distinct preparation, update, and evaluation processes. The
update process writes a complete declared persistent-state inventory and
terminates. A fresh evaluator loads the frozen base checkpoint plus only that
state. Persistent-arm evaluation has no source documents, retrieval index, or
training rows in its workspace.

The evaluator retains, for every scored query:

- canonical query and prompt hashes;
- tokenizer input IDs and their digest;
- four finite A-D scores;
- deterministic lowest-index tie handling;
- independently recomputed argmax and correctness;
- family, fact-kind, query-class, seed, order, arm, checkpoint, implementation,
  and state bindings.

Context and retrieval controls retain the same fields plus explicit external
payload manifests. Supplied summaries are never authoritative.

## Preregistered blockwise futility

Evaluation order is fixed before training. A checkpoint occurs after each
balanced super-block of 96 complete families: 24 from each fact kind, with all
three query classes and complete template/answer-position cycles.

For every threshold dimension, the validator computes the maximum possible
final accuracy by assigning every unscored query in that dimension as correct:

```text
maximum_final_accuracy =
  (correct_so_far + remaining_query_count) / total_query_count
```

A cell stops as `AcquisitionCellFutile` only when this upper bound is strictly
below `0.70` overall or below `0.60` for any fact kind or query class. No
confidence interval, observed trend, wall time, cost, or favorable result may
trigger early stopping. The complete scored prefix and the exact arithmetic
must be retained. A futile cell is a valid negative cell, not missing data.

Persistent arms run cells in seed-major order using the listed task-order
order. After the first failed, futile, crashed, invalid, or budget-violating
cell, remaining cells for that arm stay `NotRunByPreregisteredArmFutility`.
Passing arms must complete all nine cells and all 663,552 evaluation queries.

## Gate 1 statistics and decision

For each completed cell, report overall accuracy, all four fact-kind
accuracies, all three query-class accuracies, and gain over the immutable
no-update rows. Complete knowledge families are the only statistical clusters.

A persistent arm qualifies only if all nine cells satisfy:

- overall accuracy at least `0.70`;
- every fact-kind accuracy at least `0.60`;
- every query-class accuracy at least `0.60`;
- overall accuracy gain over no-update at least `0.20`;
- a per-cell family-cluster Student-t lower bound, using critical value at least
  `5.0`, above every corresponding accuracy floor;
- exact budget, restart, source-isolation, state, prompt, tokenizer, score,
  argmax, and artifact validation.

After all nine cells pass, the arm-level gain decision additionally uses
10,000 deterministic paired family-cluster bootstrap draws seeded from the
locked packet digest and stratified by fact kind. Its one-sided lower bound
must exceed `0.20`; familywise alpha `0.05` is Bonferroni-corrected across the
seven persistent arms. The fixed per-cell critical value `5.0` conservatively
covers the eight accuracy dimensions without treating prompts as independent.
Seed/order cells are never treated as independent prompt-level replicates.

Gate 1 returns:

- `AcquisitionQualifiedCandidates` only when at least two persistent arms pass;
- `AcquisitionSingleCandidate` when exactly one passes; Gate 2 stays sealed;
- `AcquisitionNoCandidate` when none pass;
- `Invalid` for any provenance, leakage, budget, row, restart, or artifact
  defect.

Crashes, invalid cells, futility stops, exclusions, and null results are
retained. Thresholds, hyperparameters, routing, replay share, sparse-layer
rule, clocks, training rows, and evaluation order cannot change after source
freeze.

## Artifact and claim boundary

One content-addressed external artifact must contain the protocol/config lock,
source and tree receipts, immutable V28R2 input receipts, model/tokenizer and
runtime inventories, every update-process input, state inventory, loss trace,
scored prefix or complete observations, failure, futility calculation,
subprocess record, validator report, and sorted no-symlink manifest.

Gate 2 retention/recovery, Gate 3 Astral selection, assessment, confirmation,
independent replication, benchmark evaluation, and public breakthrough claims
remain sealed. Even two Gate 1 candidates establish only local acquisition on
one synthetic corpus and one checkpoint. This preregistration's maximum claim
is `LocalProspectiveAcquisitionQualificationProtocolV28Gate1`.
