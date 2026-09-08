# Parallel Executable Strategy for Verified Mathematical and AI-Native Linguistic Discovery V1

## Status and state slice

This is a design and routing artifact under named state slice
`aligned-holistic-continual-learning-interpretability-monorepo-v1`.

Status: `DESIGN_ONLY_PENDING_INDEPENDENT_REVIEW`.

Claim ceiling:
`LocalDevelopmentVerifiedDiscoveryStrategyDesignV1`.

This document does not authorize model execution, training, provider calls,
corpus acquisition, external spend, raw-trace retention, accepted Evidence
Ledger mutation, benchmark submission, or claims of mathematical originality,
linguistic discovery, alignment, introspection, or production readiness.

The strategy combines the original mathematical-discovery thesis with the
repository's existing control-plane, evidence, formal-lane, and causal-monitor
boundaries. It is a plan for producing falsifiable candidates, not a claim that
the current workspace already produces them.

## Operating rule

Measure twice, cut once.

Each future lane receives one state slice, one directory allowlist, one frozen
input packet, one primary metric, one budget, one independent validator, and
one stop condition. The coordinator freezes shared contracts first. A lane
then makes one focused change, verifies it, and keeps or rejects it. A failed
identity closes that identity; it does not authorize retuning under the same
identity.

The model is proposal-only. It cannot select or modify the evaluator,
validator, policy, evidence ledger, custody root, signer, release authority,
or kill path.

## 1. What the strategy is trying to produce

The phrase “original insight” is split into two independently testable objects.

### Mathematical object

`VerifiedMathematicalDiscoveryCandidateV1` is a candidate that:

1. is expressed in a fixed formal environment;
2. is checked by the formal kernel;
3. is not an exact or near duplicate of the declared library and prior-art
   corpus;
4. generalizes to a held-out family or unlocks multiple downstream results;
5. survives independent mathematical review for usefulness and scope; and
6. has a complete provenance record for the proposal, proof search, formal
   environment, and review.

A new proof of a known theorem, a successful benchmark proof, a new
formalization of an informal result, a new definition, and a useful new theory
are different outcomes. The result packet must label which one occurred.

### AI-native linguistic object

`HeldOutCausalModelLanguageGeneralizationV1` is a candidate generalization
about how a declared model or formal system processes language-like structure.
It must:

1. state a precise condition and a measurable prediction;
2. be learned or proposed without assessment-family access;
3. predict behavior on document-, author-, or grammar-disjoint families;
4. survive causal intervention and matched controls rather than probe
   correlation alone;
5. replicate across the declared model/runtime or formal-system set; and
6. be reviewed as a claim about that system, not silently promoted to a claim
   about human language.

The first linguistic target is therefore not “discover a new grammar.” It is a
causal, held-out law of representation or compositional behavior. A separate
formal-language track may generate grammars or type systems and prove their
properties, but that is formal-language invention, not evidence about human
linguistic cognition.

## 2. Claim ladder

| Level | Allowed claim | Required boundary |
| --- | --- | --- |
| `L0` | Strategy design | Complete protocol, source map, nonclaims, and stop rules |
| `L1` | Local contract qualification | Hermetic schemas, digests, state machine, and failure injection pass |
| `L2` | Instrument feasibility | Runtime or formal seam qualifies; no scientific effect claim |
| `L3` | Local verified candidate | Kernel-checked or causally measured candidate under one declared identity |
| `L4` | Held-out independently validated candidate | Fresh assessment, locked prediction, controls, independent validator, and review |
| `L5` | SOTA or public scientific result | Versioned comparison, prior-art audit, independent replication, and domain review |

No level is inherited from a framework, a green test suite, a signed digest,
an agent transcript, or a prior closed experiment. The claim is the meet of the
strongest valid evidence components and their explicit nonclaims.

## 3. Shared architecture

Both scientific tracks use the same bounded path:

```text
research question
  -> typed candidate proposal
  -> formal or causal test plan
  -> isolated execution seam
  -> independent evaluation
  -> evidence and provenance validation
  -> prior-art / novelty adjudication
  -> aggregate claim packet
  -> candidate, no-candidate, or terminal closure
```

The proposal and search layers may be probabilistic. The acceptance layers may
not be.

### Repository mapping

| Existing surface | Use in this strategy | Boundary |
| --- | --- | --- |
| `crates/hsai-control-plane` | Proposal, capability, replay, quarantine, and lifecycle vocabulary | Pure-data control contracts; not runtime enforcement |
| `crates/hsai-control-plane-checker` | Implementation-diverse recomputation of public invariants | Not an independent scientific validator by itself |
| `crates/hsai-claim-envelope` | Meet-only claim composition and explicit nonclaims | Does not raise an evidence level |
| `formal/hsai-gateway-digest/` | Reference for a narrow formal boundary and digest discipline | Not a mathematical-discovery project or scientific input |
| `docs/research/agent-platform/840-...` | Threat model, capability boundary, evidence ladder, and protected surfaces | Architecture context only |
| `docs/research/agent-platform/841-...` | Parallel lane and handoff structure | General agent-platform plan, not discovery evidence |
| `docs/research/agent-platform/842-...` | Source intake, version, license, runtime, and claim-ceiling rules | Design reference only |
| `docs/research/continual-learning/296-...` | Design pattern for fit/tune/assessment, causal monitors, controls, and lock ordering | No corpus, result, model trace, or scientific byte reuse |

Closed Astral and Oak Lab identities remain closed. Their artifacts may explain
why custody, parity, prediction locks, no-op controls, and fail-closed
missingness are necessary; they are not inputs to either discovery track.

## 4. Wave 0 — shared contract freeze

This is coordinator-owned and nonparallel. No scientific lane starts until the
following packet is byte-frozen:

```text
state_slice
question_id
claim_ceiling
source_and_license_manifest
model_or_formal_runtime_identity
dataset_or_generator_identity
fit_tune_assessment_split
primary_estimand
primary_metric_and_threshold
compute_and_time_budget
candidate_and_control_roster
prediction_lock_rule
custody_and_retention_rule
operator_runner_validator_reviewer_identities
failure_dispositions
nonclaims
```

The packet must also state what “novel” means for the lane. At minimum, it must
distinguish exact duplication, library-local recombination, known result with a
new formalization, empirical replication, and materially new result.

### Shared hard gates

- Fit, tune, and assessment inputs are disjoint by the declared unit of
  generalization.
- The evaluator and validator are outside the candidate's control.
- Missing, duplicate, stale, contradictory, non-finite, or out-of-order cells
  fail closed.
- Assessment predictions and evaluator configuration are locked before
  assessment outcomes are loaded.
- Any raw activation, token, prompt, or per-trial result has an external
  owner-only custody root and a fixed expiry; raw data are deleted before final
  validation.
- A changed source, runtime, model, asset, corpus, threshold, or control
  invalidates the packet and requires a fresh review.
- A local test cannot become external, formal, benchmark, SOTA, or production
  evidence by changing its label.

## 5. Parallel lanes after Wave 0

The lanes share only frozen interfaces and aggregate handoff records. They do
not share mutable scientific outputs.

### Lane M — verified mathematical discovery

**Objective:** build a proof-producing discovery loop whose first claim is
kernel-checked candidate generation, not originality.

**Initial seam:** one strong language model, Lean 4, Mathlib, retrieval, and a
compiler/kernel feedback loop. Do not add latent reasoning or multi-agent
search in the baseline.

**Artifacts:** formal statement, dependency blueprint, proof candidates,
kernel-check result, normalized proof-DAG digest, resource accounting,
prior-art search record, and independent review record.

**Engineering metric:** kernel-valid proof rate at a fixed proposal and compute
budget, reported with pass@1 and pass@k on a frozen held-out family.

**Discovery metric:** verified materially-new contribution rate:

```text
VMNCR = accepted materially-new, reusable contributions
        / fixed-budget candidate proposals
```

VMNCR is not an automatic training reward. A candidate counts in the numerator
only after kernel checking, duplicate screening, held-out reuse testing, and
independent domain review. The mechanical prefilter may optimize search; the
scientific claim still requires adjudication.

**Exit gate:** the baseline is reproducible, its formal environment is frozen,
and every candidate can be replayed from exact bytes. Enhancement work starts
only if the baseline produces a stable measurement rather than a moving target.

### Lane L — causal AI-native linguistics

**Objective:** discover held-out causal generalizations about model language
processing or formal language behavior.

**Initial target:** controlled artificial-language families with compositional,
recursive, agreement, and interference transformations. The first protocol
must declare the grammar generator, family unit, training exposure, held-out
transformation, output behavior, and intervention location before any
assessment effects are examined.

**Candidate format:**

```text
generalization_id
conditions
predicted_behavior_delta
intervention_operator
scope_and_exclusions
fit_support
tune_lock
held_out_result
controls
```

**Primary metric:** family-level held-out causal prediction. A candidate
starting design may use the existing causal-monitor precedent of sign
agreement at least `39/48`, `R^2 >= 0.25`, and a two-sided family bootstrap
interval excluding zero, but those values are design inputs for a fresh review,
not inherited evidence.

**Required controls:** behavioral baseline, raw-activation probe, shuffled
feature identity, matched random projection, constant donor, shuffled donor,
activation-only versus text-only intervention, exact-copy/no-op intervention,
and evaluator-gaming prompts. A probe or reconstruction score cannot replace a
causal intervention.

**Exit gate:** the proposed law predicts the declared held-out families,
survives the controls, replicates across the declared model/runtime set, and
remains bounded as a claim about that system. Human-language interpretation is
blocked until a separate corpus, linguist review, and transfer protocol pass.

### Lane E — evidence, novelty, and independent adjudication

**Objective:** prevent a proof, activation effect, or attractive explanation
from being mistaken for an original or useful insight.

**Scope:**

- canonical candidate and proof-DAG serialization;
- source, license, version, and artifact digests;
- exact fit/tune/assessment and control rosters;
- duplicate and near-duplicate detection against the frozen formal library;
- literature and prior-art search with search date and coverage limits;
- blinded expert review for usefulness, scope, and conceptual compression;
- independent re-execution or replay where the claim requires it;
- aggregate-only release and claim-envelope construction.

**Exit gate:** no accepted candidate lacks a provenance chain, a declared
novelty basis, a reviewer distinct from the operator, and explicit uncertainty
and nonclaims.

### Lane R — clean-room reference and code intake

**Objective:** convert public research into bounded adapter candidates without
vendoring hidden implementation details or treating a paper's result as local
evidence.

**Scope:** source URL, repository, license, exact revision, dependency
requirements, model/data rights, build digest, known limitations, and proposed
interface.

**Exit gate:** every adopted dependency has a legal/provenance record and an
explicit reason it is an Interface or Adapter rather than a scientific input.
Unverified names remain discovery-only references.

### Lane C — control-plane and reproducibility

**Objective:** make the discovery loops interruptible, replayable, and
fail-closed.

**Scope:** state machine, capability scoping, run manifests, quota and timeout
accounting, immutable evaluator configuration, independent checker hooks,
failure injection, custody expiry, and aggregate handoff packets.

**Exit gate:** a candidate cannot invoke an unlisted tool, alter its evaluator,
expand capability, bypass a lock, replay a nonce, or convert a failed lane
state into an accepted result.

## 6. Mathematical execution ladder

The ladder is sequential even though its contract, intake, and evidence lanes
run in parallel.

### M0 — contract qualification

Use only synthetic statements and hermetic formal fixtures. Validate schema
cardinality, canonical bytes, proof-DAG normalization, duplicate detection,
resource counters, and failure paths. No model or external corpus.

### M1 — single-agent formal baseline

Implement:

```text
statement
  -> premise retrieval
  -> proof proposal
  -> Lean compile/check
  -> exact error feedback
  -> bounded repair
```

Measure pass@1, pass@k, kernel-check latency, tokens or search steps, and
replay success. Benchmark scores are baseline diagnostics only.

### M2 — structured planning and repair

Add one blueprint format and one repair policy. Compare against M1 at matched
compute. Keep the change only if it improves the primary metric without
increasing invalid-proof or replay-failure rates.

### M3 — verified proof-DAG evolution

Preserve only kernel-checked lemmas and definitions. Recombine typed sub-DAGs,
run the kernel again, and measure downstream reuse and proof compression.
Evolution is over verified artifacts, not raw model prose.

### M4 — open-ended conjecture and program search

Generate candidate definitions, conjectures, constructions, or programs inside
a fixed domain. Test finite instances and counterexamples before attempting
formal proof. A conjecture that is merely plausible is not a verified result.

Use FunSearch-style program search only as an algorithmic reference. Its public
repository explicitly separates the evolutionary implementation from the
language-model generator, untrusted-code sandbox, and distributed execution;
those missing surfaces must be designed separately.

### M5 — optional latent branch

Only after M1–M4 produce a stable baseline, run a matched ablation:

```text
same model family + same data + same compute budget
text intermediates versus latent intermediates
```

Keep the latent branch only if it improves the predeclared metric, preserves
formal validity and replayability, and shows benefit beyond additional forward
passes or curriculum effects. The official Coconut repository is a research
reference, not a drop-in SOTA component.

### M6 — discovery assessment

Run only after the exact packet, tune lock, independent review, fresh
assessment family, and custody chain pass. Report separately:

- solved known theorem;
- new formalization;
- reusable lemma or definition;
- new construction or bound;
- independently judged materially-new contribution.

Only the last category can support a mathematical-originality claim, and even
then only at the declared domain and scope.

## 7. Linguistic execution ladder

### L0 — generator and intervention qualification

Prove that the synthetic language generator, tokenizer, family assignment,
intervention operator, donor selection, and no-op path are deterministic and
exactly accounted for. This is contract evidence, not a linguistic result.

### L1 — behavioral generalization baseline

Measure model behavior on fit, tune, and assessment grammar families without
activation interpretation. Establish the strongest behavioral baseline before
adding probes or causal features.

### L2 — causal measurement

Add one fixed intervention family. Require native/instrumented parity,
deterministic repeatability, exact no-op identity, nonzero intervention reach,
and complete event accounting before fitting any predictor.

### L3 — locked causal predictor

Fit a fixed low-capacity predictor on fit families, lock it on tune families,
then evaluate once on assessment families. No layer, feature map, wrapper,
donor, threshold, or panel changes after the lock.

### L4 — formal bridge

Translate the candidate generalization into a typed mathematical statement and
prove only the abstract property that is actually being claimed. The proof does
not prove the model's empirical behavior; the causal experiment and the formal
proof remain separate evidence components.

### L5 — transfer and replication

Attempt transfer to a second declared model or a human-language corpus only
after the AI-native result is independently validated. Human-language transfer
requires author/document-disjoint data, linguist review, corpus rights, and a
fresh claim ceiling.

## 8. Agent roles and independence

The first system is one model with tools. Specialization is introduced only as
an ablation, not as an article of faith.

Permitted proposal roles:

- conjecturer or construction proposer;
- blueprint decomposer;
- formalizer;
- prover and bounded repairer;
- counterexample finder;
- experiment designer;
- prior-art summarizer;
- candidate critic.

Protected roles:

- evaluator configuration;
- formal kernel or execution checker;
- evidence validator;
- novelty adjudicator;
- policy and capability broker;
- release authority;
- custody and deletion verifier.

The candidate system may submit evidence to those roles but cannot replace or
reconfigure them.

## 9. Reference intake: use, defer, exclude

### Immediate reference candidates

- **Lean 4 and Mathlib:** formal environment and kernel-checked library.
- **LeanDojo-v2:** programmatic Lean interaction and theorem-proving pipeline.
  The original LeanDojo repository now labels itself deprecated for new work;
  the v2 repository is the relevant intake target.
- **LeanCopilot:** native tactic suggestion, proof search, and premise
  selection inside Lean.
- **Formal Conjectures:** open formalized conjecture statements and a route to
  proof-discovery experiments. Its repository warns that formalized statements
  can contain subtle inaccuracies and that it is not an official Google
  product; human statement review remains mandatory.
- **MiniF2F and PutnamBench:** benchmark diagnostics with frozen version and
  split recorded. Neither is a novelty oracle.
- **FunSearch:** evolutionary program-search architecture and examples of
  computer-assisted mathematical discovery.
- **Coconut:** latent-reasoning reference for a later matched ablation only.

### Deferred until primary-source verification

The pasted exchange names several additional systems and papers. They remain
discovery-only until a primary source, license, exact revision, reproducible
artifact, and actual scope are recorded. This applies to names such as
`ax-prover-base`, `LEAP`, `ProofEvolve`, `Mostik`, `Tensor Logic`,
`AxiomProver`, and `Gauss`. No name in a conversational summary becomes a
dependency by repetition.

### Clean-room intake rule

Public work can inform an independent implementation only through its public
specification and a recorded source/license/version/provenance entry. Do not
copy or vendor code, weights, datasets, traces, generated output, hidden test
bytes, or private implementation details. External repositories remain pinned
references or separately approved adapters.

## 10. Current workspace execution boundary

The current authorized slice permits additive documentation, manifests, and
hermetic contract checks under
`aligned-holistic-continual-learning-interpretability-monorepo-v1`.

Therefore the executable work available now is:

1. freeze this strategy's schemas and claim ceilings;
2. write source and license intake records;
3. define synthetic generators and failure cases as pure-data contracts;
4. define math and linguistic handoff manifests;
5. add hermetic validators for cardinality, lock ordering, digests, and
   nonclaim propagation; and
6. prepare, but do not execute, future model-bearing packets.

The following are closed in the current phase:

- model execution and training;
- provider or paid execution;
- external corpus acquisition;
- raw prompt, token, activation, or trace retention;
- use of prior Astral, Oak Lab, MiniMind, Gemma, Qwen, or other scientific
  result bytes as inputs;
- mutation of the accepted Evidence Ledger;
- benchmark, SOTA, alignment, introspection, or production claims.

The existing repository formal lane is currently a declared-only interface and
contract surface. It is not a completed Lean-backed mathematical-discovery
engine. A future real formal backend must receive its own state slice, source
identity, exact toolchain, independent proof validation, and claim ceiling.

## 11. Future implementation boundaries

After a separate review opens implementation, the intended clean boundaries are:

```text
formal/math-discovery-v1/              # separate Lean project and proof artifacts
tools/math-discovery-v1/               # proposal, retrieval, search, and replay seams
tools/ai-native-linguistics-v1/        # generator, intervention, runner, validator
tools/discovery-evidence-v1/           # novelty, provenance, locks, and aggregates
docs/research/math-discovery/          # protocol and execution records
docs/research/ai-native-linguistics/   # protocol and execution records
```

Those paths are future allowlists, not current authorization. The discovery
projects must not import historical scientific artifacts or silently attach to
the unrelated `formal/hsai-gateway-digest` project.

## 12. Keep/reject matrix

| Candidate change | Keep only if | Reject or close if |
| --- | --- | --- |
| Retrieval | Improves held-out kernel-valid rate at matched budget | Only improves memorized or contaminated items |
| Blueprint planning | Improves multi-lemma completion and replay | Adds prose without measurable gain |
| Multi-agent roles | Beats the single-model baseline in a fixed-cost ablation | Cost rises or errors become harder to attribute |
| Proof-DAG evolution | Increases verified downstream reuse | Recombines invalid, duplicated, or untracked fragments |
| Conjecture search | Produces testable candidates and useful verified artifacts | Produces untested plausible prose |
| Latent reasoning | Wins a matched compute ablation and preserves auditability | Benefit is explained by extra passes or curriculum alone |
| Activation features | Predict held-out effects under causal intervention | Only correlate or depend on probe/reconstruction scores |
| Formal bridge | Proves the exact abstract statement | Formalizes a changed or weaker claim after seeing results |
| Human-language transfer | Replicates under fresh rights, splits, and linguist review | Generalizes from synthetic or model-internal evidence by assertion |

## 13. Stop conditions

Close the current identity when any of the following occurs:

- the packet is stale or internally inconsistent;
- a required source, runtime, model, asset, corpus, or reviewer is missing;
- the baseline cannot be reproduced at the declared budget;
- assessment data influence the predictor, threshold, feature map, wrapper, or
  candidate selection;
- an evaluator, validator, or protected policy surface is model-controlled;
- a critical no-op, parity, custody, or event-accounting gate fails;
- the candidate's novelty claim cannot be independently bounded;
- a result is positive only under retuning, selected-position exclusion,
  hidden accumulation, or undocumented retry;
- local tests are being described as external, formal, benchmark, SOTA, or
  production evidence.

A continuation requires a new protocol identity, fresh bytes, and fresh review.

## 14. Definition of success

The strategy succeeds first when it produces a reproducible, bounded candidate
pipeline with independent rejection behavior. It succeeds scientifically only
when at least one track produces a candidate that is:

```text
kernel-checked or causally measured
  + held-out
  + materially non-duplicate
  + independently reviewed as useful
  + independently reproducible
  + published with exact nonclaims
```

That is the threshold for an original mathematical or AI-native linguistic
insight claim. Higher-level “breakthrough” language requires evidence beyond
this document: a fresh benchmark comparison, prior-art audit, replication, and
domain-expert judgment.

## Source register

The following are design references, not frozen dependencies or local evidence:

- [LeanDojo-v2](https://github.com/lean-dojo/LeanDojo-v2)
- [LeanCopilot](https://github.com/lean-dojo/LeanCopilot)
- [Formal Conjectures](https://github.com/google-deepmind/formal-conjectures)
- [MiniF2F](https://github.com/facebookresearch/miniF2F)
- [PutnamBench](https://papers.neurips.cc/paper_files/paper/2024/file/1582eaf9e0cf349e1e5a6ee453100aa1-Paper-Datasets_and_Benchmarks_Track.pdf)
- [FunSearch](https://github.com/google-deepmind/funsearch)
- [Coconut](https://github.com/facebookresearch/coconut)
- [AlphaProof and AlphaGeometry overview](https://deepmind.google/science/)

Every future implementation must refresh this register, verify the current
revision and license, and bind the adopted source to a new packet.
