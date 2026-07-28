# Novel-Knowledge Acquisition and Recoverable Consolidation V28

State slice:
`astral-rgs-novel-knowledge-acquisition-recoverable-consolidation-v28`.

Status: `DocsFirstPreregistered / V28R1CorpusNotNovelRetired /
V28R2PoweredProtocolDocsFirstOnly / V28R2ImplementationNotAuthorized /
UpdateArmsNotAuthorized / AssessmentSealedNotAuthorized`.

## Decision

V27 stopped correctly. Its two complete development packets matched every
deterministic scientific lock and the validators failed closed, but the task
could not measure acquisition: `no_update` scored `1.000000`. Every updated arm
scored lower, Astral lost to nonprivileged controls, and the recovery exercise
was only an in-memory byte-corruption roundtrip.

V27 assessment remains unopened. Its corpus, outcomes, assessment commitment,
and selector ranking are retired from candidate generation for V28. Running or
tuning Astral on that task would optimize around a known shortcut and cannot
support a continual-learning claim.

V28 is acquisition-first. It has three ordered gates. A later gate is `NotRun`
unless every earlier gate is valid and qualified.

The first Gate 1 novelty corpus has now run and stopped correctly. V28R1
produced identical `pre_update` and restarted `no_update` point estimates of
`0.2517361111` accuracy against chance `0.25`, but failed the frozen
multiplicity-adjusted family-cluster equivalence intervals. Its authoritative
disposition is `CorpusNotNovel`; its corpus and seed are retired, and no update
arm ran.

A distinct, powered V28R2 replacement corpus is preregistered in
`64-v28r2-powered-acquisition-novelty-preregistration.md`. That docs-only note
freezes 1,536 families per fact kind and complete nonreuse. It does not
authorize implementation or model execution.

## Research question

After all source context is removed and the model process is restarted, can a
bounded update acquire genuinely unseen knowledge while preserving protected
capabilities, calibration, exact recoverability, and honest separation from
retrieval or context-only access? Only if multiple qualified update arms then
show different acquisition-retention tradeoffs may Astral prospectively select
among them.

## Gate 1: acquisition qualification

### Checkpoint-first novelty contract

The starting model, tokenizer, runtime, source commit, and tree are hashed
before any V28 corpus seed or item exists. Corpus generation must bind:

- the starting checkpoint and tokenizer SHA-256 identities;
- a generator implementation digest and immutable configuration digest;
- a seed commitment created after the checkpoint identity;
- a unique V28 namespace that has never appeared in V18-V27 data, prompts,
  adapters, reports, or assessment commitments;
- a closed manifest covering every source form, derived query, answer mapping,
  split, family, and license record.

The corpus contains balanced four-choice instances in four separately reported
fact kinds:

1. nonce facts;
2. entity relations;
3. changed rules that conflict with a declared prior rule;
4. arbitrary symbol or identifier mappings.

Generation must occur after checkpoint hashing. No item, alias, answer token,
or family may be selected from model output. Development, tuning, and future
assessment split by complete knowledge family. V27 items and exposed outcomes
are forbidden.

### Pre-update and no-update falsification

Chance is `0.25`. Define chance-normalized lift as:

```text
chance_normalized_lift = (accuracy - 0.25) / 0.75
```

Both the untouched pre-update model and a separately restarted `no_update` arm
must have absolute chance-normalized lift at most `0.05` overall and within
each fact kind. Systematic below-chance behavior is not near chance and fails
the same gate because it may expose answer inversion or another shortcut. Any
score outside the symmetric interval yields `CorpusNotNovel` and stops V28
before update-arm comparison. A non-chance baseline is a task failure, not
evidence that the model already learned the V28 corpus.

The original V28R1 corpus required at least 24 knowledge families per fact kind
and failed for insufficient interval precision. It is retired. V28R2 freezes
exactly 1,536 knowledge families per fact kind under the disjoint protocol in
`64-v28r2-powered-acquisition-novelty-preregistration.md`. The four queries in
every family/query-class cell rotate the same semantic answer through positions
A-D exactly once. Query-specific answer mappings commit each permutation.
Prompt-template or answer-position leakage invalidates the packet.

### Context-free restart evaluation

Training source forms are removed from the prompt, process memory, temporary
files, retrieval index, and evaluation workspace before persistent-arm
evaluation. The evaluator records distinct pre-update, update, and evaluation
process identities. Evaluation loads only the declared post-update persistent
state from a fresh process.

Each knowledge family is evaluated through four distinct held-out queries in
each of three query classes:

- paraphrase;
- multi-hop consequence;
- withheld composition.

Exact training-form prompts are forbidden in evaluation. Training and
evaluation template families are disjoint; evaluation template-family IDs may
repeat only within one query class, while prompt-instance hashes remain unique.
The multi-hop and withheld-composition constructions may not be fitted from
assessment outcomes.

### Acquisition arms and baseline roles

The minimum matched comparison contains:

- `no_update`;
- `context_only`;
- `retrieval`;
- `naive_sequential_lora`;
- `replay`;
- `scol_style_consolidation`.

`nested_multiscale_learning` is an experimental arm, not an assumed winner.
Additional arms must be named and locked before outcomes.

`context_only` and `retrieval` may access their declared external information
at inference and are reported as nonpersistent baselines. They cannot qualify a
persistent-consolidation claim. Every weight- or recoverable-state arm is
evaluated with source context and retrieval disabled after restart.

A persistent arm qualifies Gate 1 only if it reaches at least `0.70` overall,
at least `0.60` in each held-out query class, and improves at least `0.20` over
the restarted `no_update` arm. Acquisition against retrieval is reported but
is not allowed to disappear into a weighted score.

## Gate 2: retention and recovery qualification

Gate 2 stays sealed until at least two native persistent update arms qualify
Gate 1 under matched budgets. It measures acquisition and retention together;
no acquisition-only score can qualify.

Mandatory protected dimensions are:

- general-ability change no worse than `-0.02`;
- instruction-following change no worse than `-0.02`;
- protected factual-retention change no worse than `-0.02`;
- zero hard safety or governance violations;
- stale superseded-fact accuracy at most `0.10` while replacement-fact
  accuracy remains at least `0.70`;
- Brier-score degradation at most `0.02`, reported with abstention behavior;
- the Gate 1 paraphrase, multi-hop, and withheld-composition floors retained
  after later updates.

Recovery is a real process-level experiment. The runner must checkpoint model,
adapter, optimizer, scheduler, replay cursor, random state, corpus cursor, and
policy journal bytes; inject a declared corruption that causes at least `0.10`
score loss; terminate the process; restart; roll back to the last valid state;
and replay the exact accepted update sequence. Qualification requires:

- a different post-corruption process identity;
- byte-exact rollback digests for every declared state component;
- byte-exact replay digests;
- recovered score within `0.01` of the pre-corruption score;
- `100%` success across every preregistered injection;
- retained failure, stderr, and bounded resource records.

An in-memory mutation and reversal does not satisfy this gate.

## Gate 3: prospective Astral selection

Gate 3 stays sealed until Gate 2 passes and the development/tuning results show
a real choice. At least two persistent arms must be feasible and exhibit a
locked, statistically supported acquisition-retention tradeoff. If one arm
dominates every other arm across acquisition, retention, calibration, recovery,
and cost, selector research is unnecessary and Astral remains `NotRun`.

Before assessment outcomes exist, every selector locks its candidate ranking
and predictions for acquisition, retention, calibration, recovery, cost, and
governance. Required matched selectors and controls are:

- Astral telemetry;
- text-only;
- output-only;
- activation-only;
- strongest fixed development arm;
- no update;
- shuffled telemetry;
- wrong or permuted telemetry;
- retrieval;
- SCoL-style consolidation;
- post-hoc oracle, used only as a non-actionable upper bound.

All selectors consume identical candidate states and budgets. Assessment may
not tune features, thresholds, calibration, stopping, update locations, or arm
hyperparameters. Astral must beat text, output, activation, fixed-arm,
no-update, retrieval, SCoL-style, and the strongest matched nonprivileged
baseline; specificity controls must remain null.

## Statistical and artifact contract

V28R2 baseline novelty qualification uses exactly one `pre_update` run and one
separately prepared and restarted `no_update` run; complete knowledge families,
not duplicated processes, are its statistical clusters. Every later persistent
update-arm qualification uses at least three update seeds, at least three task
orders, paired candidate outcomes, frozen per-seed/order family-cluster
interval rules, multiplicity correction, and separate confidence intervals for
acquisition, retention, calibration, recovery, and selector regret.

Required repository-external artifacts include exact source and tree
identities, model and tokenizer hashes, checkpoint-before-generation receipt,
corpus generator and manifest, closed split census, licenses, raw prompts and
outputs, update-state inventories, process records, restart records, corruption
journals, rollback and replay digests, selector locks, all failures and
exclusions, and a sorted no-symlink content manifest. Astral independently
recomputes every gate from raw rows. Supplied summaries are never authoritative.

Valid dispositions are explicit:

- `NotRun` for an absent later-stage packet;
- `Invalid` for malformed, contaminated, unsealed, or provenance-incomplete
  input;
- `CorpusNotNovel` when pre-update or no-update exceeds the novelty ceiling;
- `AcquisitionNoCandidate` when no persistent arm passes Gate 1;
- `RetentionRecoveryNoCandidate` when Gate 2 fails;
- `NoSelectorQuestion` when qualified arms do not exhibit a real tradeoff;
- `ProspectiveSelectionNegative` when Astral fails a confirmatory or
  specificity gate;
- a bounded local candidate only when every applicable gate passes.

Negative, null, crashed, and rejected packets are retained. No threshold may be
repaired after assessment exposure.

## Breakthrough gate

The protocol-level breakthrough criterion is:

> After context removal and restart, the system acquires genuinely unseen
> knowledge better than no-update, retrieval, sequential LoRA, replay, and the
> strongest matched baseline while preserving retention and calibration,
> surviving exact injected recovery, and reproducing across model families and
> an independent implementation.

This criterion cannot be satisfied by this preregistration, a local validator,
synthetic fixtures, author replay, one model family, or an unreviewed external
packet.

## Stop rules

- Stop before corpus generation if checkpoint, tokenizer, source, runtime, or
  generator identity is incomplete.
- Stop before updates if pre-update or restarted no-update exceeds the novelty
  ceiling.
- Invalidate training-form overlap, answer-position cues, source-context
  leakage, retrieval leakage into a persistent arm, family overlap, or model-
  output-guided corpus selection.
- Stop before Gate 2 unless two native persistent arms qualify acquisition.
- Stop before Astral prediction work unless Gate 2 passes and a real arm
  tradeoff exists.
- Stop assessment on any outcome exposure before configuration and prediction
  locks.
- Never pool V27 development outcomes with V28.

## Claim ceiling

The maximum status of this slice is
`LocalProspectiveNovelKnowledgeAcquisitionProtocolV28`. It is a preregistered
local design, not implementation evidence, model-backed acquisition,
continual-learning qualification, independent replication, benchmark evidence,
autonomous self-improvement, introspection, self-modeling, Stage 0C, Stage 1,
production readiness, or a breakthrough.

## Primary source basis and design additions

- TRACE motivates novel continual-learning data and explicit general-ability
  and instruction-following retention measures:
  <https://arxiv.org/abs/2310.06762>.
- Eva-KELLM v1 motivates provenance-sensitive edits, paraphrase evaluation,
  altered-knowledge reasoning, and unrelated-knowledge retention:
  <https://arxiv.org/abs/2308.09954v1>.
- DocTER v2 is the later retitled revision used specifically for explicit
  multi-hop consequences and RAG comparisons:
  <https://arxiv.org/abs/2308.09954v2>.
- Online Continual Knowledge Learning motivates joint acquisition and retention
  measurement:
  <https://arxiv.org/abs/2311.09632>.
- Self-Consolidating Language Models motivates context-to-weight consolidation,
  update-location selection, and explicit context-versus-update baselines:
  <https://arxiv.org/abs/2605.07076>.
- Nested Learning motivates a multiscale experimental arm but does not establish
  it as a matched drop-in winner:
  <https://arxiv.org/abs/2512.24695>.

Checkpoint-first generation, the numerical novelty ceiling, withheld
compositions, process restart and corruption recovery, calibration thresholds,
Astral prediction locking, cross-family reproduction, and independent
implementation are stronger V28 design safeguards. They are not findings
claimed by those papers.
