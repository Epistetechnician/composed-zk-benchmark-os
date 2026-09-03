# MiniMind state-of-the-art continual-learning comparison audit V1

Date: 2026-09-02.

State slice: `continual-learning-minimind-state-of-the-art-comparison-audit-v1`.

Audit status: `AUDIT_COMPLETE / LARGER_CAMPAIGN_NOT_AUTHORIZED`.

Claim ceiling: `LocalDevelopmentMiniMindStateOfTheArtComparisonDesign`.

## Decision

The existing MiniMind V3 campaign is not a state-of-the-art comparison. It is
valid pipeline qualification: a fresh source and corpus identity, an accepted
execution packet, a bounded offline model run, and an independently validated
aggregate contract. It has no retained checkpoint, no published task-suite
reproduction, no real domain-incremental corpus, and no implementation of the
current orthogonal/projection frontier.

The next campaign must therefore be a new state slice. It must compare methods
on at least one published continual-learning suite and one fresh,
domain-incremental suite, while keeping the MiniMind track separate from
claims made for larger T5, LLaMA, Mistral, or Qwen models. No larger model
campaign, data acquisition, or checkpoint-retaining run is authorized by this
audit alone.

## Research question

For a small decoder-only language model receiving domains or tasks in a fixed
sequence, which update mechanism gives the best validated trade-off between:

1. acquisition on the current domain;
2. retention of earlier domains/tasks;
3. transfer to a later unseen domain/task; and
4. persistent storage and training compute?

The comparison is about continual adaptation, not chat quality, general model
intelligence, production readiness, or an absolute ranking against closed
frontier systems.

## Setting classification

The literature uses several distinct settings that must not be collapsed into
one leaderboard:

### Task-incremental instruction tuning

The model receives a sequence of supervised tasks, typically represented as
instruction/response examples. This is the closest setting to the standard
LLM continual-learning papers and supports direct method comparisons.

The published standard suite to reproduce is the five-task sequence used by
recent LLM continual-learning work: AG News, Amazon Reviews, Yelp Reviews,
DBpedia, and Yahoo Answers. The suite must be versioned and digest-bound; the
exact task order, prompt template, label verbalizers, and evaluation protocol
must be frozen before fitting.

### Domain-incremental continual pre-training

The model receives unlabeled domain corpora sequentially, then is evaluated on
held-out downstream tasks and open-domain retention. This is the relevant
setting for creating small domain-specific models. It is not equivalent to
the five-task instruction-tuning suite.

The primary published references are DAPset and TWEET. DAPset contains six
domains with unlabeled corpora and downstream classification sets. TWEET
represents temporal drift with five chronological periods and downstream
hashtag prediction. A reduced-token mirror may be used for local feasibility,
but it cannot be called a reproduction of the full benchmark.

### Stateful-agent or experience-incremental continual learning

The combined study adds a third lane for learning from ordered experience:
interaction trajectories, tool results, feedback, rewards, retrieved memories,
or extracted skills. The state channel must be declared for every arm:
in-context state, external memory, skill library, adapter/weight update, or a
hybrid. This is a different scientific object from offline task/domain
training, so it receives a separate primary metric and leaderboard. It is
included in the overall research program but must not be mixed into the task
or domain score.

The primary experience references are [CL-Bench](https://arxiv.org/abs/2606.05661),
which evaluates stateful learning across six expert-validated real-world
domains, and [ContinualSkillBench](https://arxiv.org/abs/2608.03874), which
evaluates in-context skill reuse across five domains with ordered subtasks.
They are benchmark references, not permission to claim that a MiniMind agent
has matched frontier systems.

## Frontier literature inventory

The following primary research sources were checked on 2026-09-02. Their
reported results are hypotheses and comparison targets, not independently
validated facts in this repository.

| Method or line | Mechanism | Relevance to MiniMind comparison | Required treatment |
| --- | --- | --- | --- |
| [O-LoRA, EMNLP Findings 2023](https://aclanthology.org/2023.findings-emnlp.715/) | Sequential task-specific LoRA subspaces with orthogonality regularization | Directly applicable to decoder-only PEFT | Mandatory frontier reproduction |
| [N-LoRA, COLING 2025](https://aclanthology.org/2025.coling-main.286/) | Reduces parameter collision between task updates | Directly tests the local interference hypothesis | Mandatory if the released implementation/specification is portable |
| [OPLoRA, AAAI 2026](https://ojs.aaai.org/index.php/AAAI/article/view/40703) | Double-sided projection away from dominant singular directions | Direct projection baseline with an explicit retention invariant | Mandatory frontier reproduction |
| [OSFT, ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/22620cccae29bbb3f18d226ea0320ff5-Abstract-Conference.html) | SVD-preserved high-rank subspace with orthogonal constrained updates | Strong current fixed-parameter comparator | Mandatory if faithful implementation is feasible; otherwise report exclusion |
| [OLieRA, 2025](https://arxiv.org/abs/2509.06100) | Multiplicative Lie-group updates plus orthogonal task subspaces | Current orthogonality frontier with a different update geometry | Tier-2 reproduction; no “SOTA” claim without faithful implementation |
| [ASO-LoRA, ACL 2026](https://aclanthology.org/2026.acl-long.842/) | Attribution-guided soft orthogonality and task subspace sharing | Current knowledge-sharing frontier | Tier-2 reproduction; requires exact attribution and routing semantics |
| [DAS / continual DAP, 2023](https://arxiv.org/abs/2302.03241) | Soft masking and knowledge integration during continual pre-training | Domain-incremental baseline | Mandatory in the CPT lane |
| [HPrompt-CPT, Findings EMNLP 2023](https://aclanthology.org/2023.findings-emnlp.808/) | Prompt/hypernetwork adaptation with replay and competing CPT baselines | Published DAPset/TWEET protocol and metric reference | Mandatory domain-lane reference; reproduce only where data is available |
| [Efficient domain CPT, Findings ACL 2024](https://aclanthology.org/2024.findings-acl.606/) | Domain data selection for continual pre-training | Tests whether data selection, not update geometry, explains gains | Mandatory domain-lane ablation or explicitly excluded |
| [Stability-gap CPT, ACL 2025](https://aclanthology.org/2025.acl-long.1578/) | Sampling/epoch strategy for the early stability gap | Resource-matched CPT comparator | Tier-2 domain-lane comparator |
| [Specialized medical CPT and merging, ACL 2026](https://aclanthology.org/2026.acl-long.17/) | Domain CPT followed by model merging and instruction restoration | Relevant deployment pattern for specialists | Contextual reference; not a same-task baseline unless its data/task protocol is reproduced |
| [CL-Bench, 2026](https://arxiv.org/abs/2606.05661) | Stateful interaction, memory, and online experience | Primary experience-incremental benchmark | Mandatory experience-lane reference |
| [ContinualSkillBench, 2026](https://arxiv.org/abs/2608.03874) | In-context skill acquisition and cross-task reuse | Primary skill-consolidation benchmark | Mandatory experience-lane reference |
| [LifelongAgentBench, 2025](https://arxiv.org/abs/2505.11942) | Lifelong agent skill learning | Secondary experience benchmark | Include if its task and evaluation artifacts are reproducible |
| [SkillLearnBench, 2026](https://arxiv.org/abs/2604.20087) | Skill generation on real-world tasks | Secondary experience benchmark | Include if its task and evaluation artifacts are reproducible |

The inventory intentionally separates methods that update shared weights,
methods that allocate task-specific parameters, methods that preserve a
subspace, and methods that change the data stream. A method is not admitted as
a baseline merely because its paper uses the phrase “continual learning.”
The implementation audit must confirm the same task setting, model family,
access to past data, task-ID assumptions, compute budget, and evaluation
estimand.

## Local research inventory

The local record supplies useful hypotheses and failure gates, but its results
are not interchangeable and must not be pooled into a new score.

| Local line | Valid bounded finding | Implication for the SOTA comparison |
| --- | --- | --- |
| Task-routed adapter bank V26 | Candidate on Qwen2.5 under a route-bound task protocol; not a general CL result | Include as a local modular-adapter comparator, with route overhead reported |
| Second-model replication V27/V44 | Target-task non-acquisition on Llama; later Qwen3.6 acquisition eligibility also failed | Add per-task acquisition and nonconstant-output gates before retention analysis |
| Fixed optimizer / retention / order replications V37–V41 | Replay improved retention over naive sequential controls in a bounded local lane | Include replay, but report model- and prompt-specific scope |
| Plasticity guard V1 and replication | Guard beat fixed cadence once, then lost to untouched base on replication | Include guarded admission only as a negative/control mechanism; never rank against methods that did not pass acquisition |
| Plasticity recovery V1/V2 | Mechanism family closed `NoCandidate` under fixed forgetting guard | Do not retune or silently reuse its thresholds; retain as historical negative evidence |
| Functional plasticity frontier V1 | Function-space projection lost to fixed updates on the locked fresh-task estimand | Include projection as a falsification-motivated comparator, not as a positive prior |
| MiniMind V1/V2/V3 | V1/V2 rejected or closed; V3 synthetic and model contracts validated | V3 is infrastructure qualification, not a benchmark result; no V3 checkpoint exists |

The local inventory establishes a non-negotiable acquisition gate: a method
that does not learn its own current task cannot be interpreted as retaining it.
Aggregate loss alone is insufficient; exact task readout or held-out domain
performance must be inspected before any forgetting comparison.

## Required comparison panel

The larger study is a three-lane comparison. The parameter-update panel below
applies to the task- and domain-incremental lanes. The experience lane has its
own stateful panel and may include a parameter-update bridge arm. Methods
omitted for portability or data reasons remain listed as explicit exclusions.

### Controls and reference points

1. `untouched_base`: no update; measures headroom and the cost of changing the
   model.
2. `joint_oracle`: all task/domain data available jointly; an adaptation upper
   reference, not a continual method.
3. `sequential_full`: ordinary sequential full-parameter update; catastrophic
   forgetting reference.
4. `sequential_lora`: one shared cumulative LoRA; PEFT reference.
5. `independent_adapters`: one isolated adapter per task/domain; storage and
   routing reference.

### Required mechanism baselines

6. `replay`: fixed-size, predeclared rehearsal buffer with exact replay-token
   accounting.
7. `ewc_or_lwf`: one regularization baseline, with Fisher/KL construction and
   all coefficients frozen before assessment.
8. `task_routed_bank`: the local V26 mechanism, reimplemented against the new
   data and model contract rather than importing V26 artifacts.
9. `o_lora`: faithful O-LoRA reproduction.
10. `n_lora`: faithful N-LoRA reproduction where its collision definition can
    be made exact on the MiniMind architecture.
11. `oplora`: faithful double-sided projection reproduction.
12. `osft`: faithful high-rank orthogonal-subspace reproduction if its exact
    SVD/update contract is portable.

### Tier-2 frontier methods

`oliera`, `aso_lora`, `das`, `hprompt_cpt`, stability-gap sampling, and
data-selection methods are admitted only after a source audit proves that the
MiniMind implementation can reproduce the paper's update, routing, and
objective semantics. If a method cannot be reproduced exactly, the report
must state the blocker and cannot call the panel complete SOTA coverage.

“Inspired by” implementations are separate exploratory arms and cannot be
renamed after the published method.

### Experience-incremental panel

1. `stateless`: every interaction starts without persistent experience state.
2. `naive_icl`: the permitted prior interaction context is passed directly at
   inference, with context-token cost counted.
3. `retrieval_memory`: a fixed retrieval memory stores prior observations and
   exposes only the declared retrieved items.
4. `skill_library`: prior experience is summarized into reusable skill records
   under a fixed write, update, deletion, and retrieval contract.
5. `parametric_experience_update`: MiniMind updates a fresh adapter or
   checkpoint from the declared experience stream.
6. `hybrid_experience_update`: combines the declared memory channel with the
   declared adapter/weight channel.

Experience arms must use identical interaction sequences, feedback, tool
availability, observation budgets, and held-out tasks. Memory state, skill
records, adapter bytes, and model weights are separate accounting categories.
An experience arm cannot claim learning merely because its context grew; it
must improve on held-out instances relative to `stateless`.

## Dataset plan

### Published task-incremental lane

- Five-task suite: AG News, Amazon Reviews, Yelp Reviews, DBpedia, Yahoo
  Answers.
- Fixed instruction template and output vocabulary.
- Document/example-disjoint fit, tune, and assessment partitions.
- At least three predeclared task orders and three replicate seeds.
- Full task readout, not only aggregate language-model loss.

### Published domain-incremental lane

- Primary target: DAPset, preserving its six-domain order and downstream
  evaluation semantics.
- Secondary target: TWEET, preserving chronology and its five-period order.
- The full benchmark and any reduced-token mirror receive separate identities.
- If licensing, retrieval, or storage prevents a faithful reproduction, the
  lane is marked `not_reproduced`; a synthetic replacement cannot inherit its
  benchmark claim.

### Fresh local domain lane

The local MiniMind demonstration must be replaced with a fresh, real,
license-audited corpus. Candidate domains are finance, biomedical/clinical,
and legal or technical text, but exact sources are not frozen by this audit.
The later corpus manifest must bind source license, document identity, author
identity where available, temporal cut, tokenizer, deduplication rule, and
global fit/tune/assessment disjointness. The old V1/V2/V3 MiniMind corpus and
all prior scientific result roots remain excluded.

The local lane is useful for feasibility and domain specialization. It cannot
be used to claim reproduction of DAPset, TWEET, or any paper's benchmark.

### Experience lane

- Primary benchmark: CL-Bench, preserving its task construction, experience
  order, reward/feedback semantics, and normalized-gain evaluation.
- Secondary benchmark: ContinualSkillBench, preserving its domain/task order,
  skill-write semantics, and transfer evaluation.
- Optional secondary references: LifelongAgentBench and SkillLearnBench, only
  if their official task and evaluator artifacts can be independently
  reproduced.
- Fresh local experience suite: a new task-trajectory panel with explicit
  feedback, reset, deletion, and held-out transfer rules. It may use the
  local materials, clinical, and finance themes, but cannot reuse V1/V2/V3
  MiniMind corpus records or prior result roots.

The experience lane must record whether each gain comes from in-context
context, retrieval, skill abstraction, adapter/weight change, or a hybrid.
No experience trajectory, memory state, or feedback artifact may enter the
task/domain lanes.

## Metrics and estimands

There is no valid single scalar that combines supervised task accuracy and
language-model BPB across lanes. Each lane therefore has one primary metric,
with the same secondary metrics and guards.

### Task-incremental primary metric

`final_macro_accuracy`: macro-average held-out accuracy across all learned
tasks after the final task. This captures adaptation and retention in one
standard task-suite quantity. Current-task acquisition, backward forgetting,
forward transfer, and general-task retention are secondary outcomes.

### Domain-incremental primary metric

`final_macro_heldout_bpb`: macro-average held-out bits-per-byte across all
domains after the final domain. Lower is better. Domain adaptation, backward
forgetting, out-of-domain retention, and downstream task performance are
secondary outcomes.

### Experience-incremental primary metric

`normalized_heldout_gain`: the macro-average improvement on held-out
post-experience instances relative to the `stateless` arm, normalized per
task before aggregation. Higher is better. The metric must use held-out
instances or tasks that were not available in the experience state, so simple
memorization and context carryover cannot substitute for reusable learning.

### Shared secondary outcomes

- current-stage acquisition relative to `untouched_base`;
- backward forgetting per prior task/domain and macro-average forgetting;
- forward transfer on the next unseen task/domain;
- general-language or instruction-following retention;
- trainable parameters and persistent artifact bytes;
- total input tokens, replay tokens, optimizer steps, and wall time;
- adapter count, routing dependence, and whether task IDs are available;
- persistent experience-state bytes, memory writes/reads, skill count, stale
  state rate, deletion correctness, and state-reset fidelity;
- deterministic rerun error and serialized checkpoint restoration error.

Every endpoint is computed per case first, then aggregated over the
predeclared seed/order units. Token rows are not treated as independent
replicates.

## Fairness and reproducibility contract

All admitted arms must use:

- the same frozen base checkpoint and tokenizer;
- the same data partitions, task/domain order, and replicate seeds;
- the same maximum sequence length and token budget;
- the same optimizer-step budget, including replay and shadow work;
- the same fit/tune/assessment boundary;
- a preassessment prediction/configuration lock;
- explicit task-ID, memory, replay, and persistent-parameter accounting;
- explicit experience-channel accounting: context, retrieval, skills, adapter
  updates, weights, feedback, and rewards;
- exact stateless reset and persistent-state deletion tests;
- model-eligibility readouts before retention interpretation;
- separate process execution and independent aggregate validation;
- checkpoint save/restore and deterministic repeatability checks;
- external owner-only custody for raw data and checkpoint-bearing outputs.

Adapters that store one module per task are not “free” because training FLOPs
are equal. Persistent bytes and inference routing must be reported as part of
the method's cost profile.

## Claim ladder

The future report may make only the strongest claim whose gates pass:

1. `LocalDevelopmentMiniMindStateOfTheArtComparisonDesign`: this audit and
   frozen comparison contract exist.
2. `LocalDevelopmentMiniMindPublishedSuiteComparison`: the published suite,
   method roster, and independent validator all pass, with no unreported
   exclusions.
3. `LocalDevelopmentMiniMindDomainIncrementalComparison`: the fresh real
   domain lane passes its custody, disjointness, and metric gates.
4. `LocalDevelopmentMiniMindCrossModelReplication`: the locked effect survives
   one additional eligible small decoder-only model.
5. `LocalDevelopmentMiniMindExperienceComparison`: the experience lane passes
   its state-custody, held-out-transfer, reset, and independent validation
   gates.

“State of the art” is permitted only as a bounded comparison statement such
as “best among the admitted methods on the declared MiniMind panel and
benchmark.” It is not permitted as a global claim about all LLMs or all
continual-learning research.

No rung authorizes chat deployment, production traffic, provider spend,
publication, Evidence Ledger mutation, or claims about general intelligence.

## Pre-execution gates

Before any larger campaign:

1. freeze a new protocol identity; do not patch V3;
2. audit every method's paper, code revision, objective, task-ID assumption,
   memory access, and reported benchmark;
3. record inclusion/exclusion decisions and source digests;
4. resolve dataset license, version, deduplication, contamination, and
   fit/tune/assessment disjointness;
5. compile exact model, tokenizer, runtime, optimizer, and budget contracts;
6. implement acquisition-eligibility and exact-readout gates;
7. define the experience environment, feedback/reward channel, state schema,
   stateless baseline, reset/deletion behavior, and held-out transfer tasks;
8. run hermetic synthetic regression only;
9. obtain a fresh independent certificate-backed signed `ACCEPT` bound to the
   complete packet and current repository instructions;
10. run model qualification before any assessment effects;
11. validate the final aggregate-only artifacts independently.

Any failed method implementation, missing benchmark data, unresolved license,
nonportable frontier method, validator disagreement, or model-acquisition
failure is reported as an exclusion or negative result. It is not repaired by
changing the comparison after seeing assessment outcomes.

## Current conclusion

The correct next artifact is a fresh reviewed three-lane comparison protocol
derived from this audit. The V3 MiniMind campaign should remain a
qualification record. A larger run becomes a credible SOTA-style comparison
only after the method roster, benchmark identities, fresh local domain and
experience panels, state-channel accounting, cost accounting, claim ladder,
and independent review are frozen.

Every mutation in this phase names state slice
`continual-learning-minimind-state-of-the-art-comparison-audit-v1`.
