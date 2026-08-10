# Recursive Meta-Harness P0 Roadmap

Status: prospective documentation-only research and implementation plan.

State slice: `recursive-meta-harness-p0-roadmap-v1`.

Claim boundary: `Level0DesignNote`.

This document authorizes no source import, dependency addition, external clone
inside the repository, model call, benchmark execution, provider spend, harness
execution, runtime process, accepted Evidence Ledger mutation, production
deployment, SOTA claim, or breakthrough claim. Every implementation or execution
phase below requires a separately reviewed state slice.

Program-local phase identifiers are `MH-P0` through `MH-P14`. The shorter `P0`
through `P14` labels used below are only readable aliases and do not supersede,
extend, or collide with any existing repository phase authorization.

## 1. Decision

Build a thin, evidence-owning meta-harness that treats complete agent execution
configurations as versioned, routable candidates:

```text
ExecutionConfiguration =
  HarnessVersion
  + ModelLane
  + MemoryPolicy
  + ToolPolicy
  + ContextPolicy
  + RetryPolicy
  + VerifierPolicy
  + BudgetPolicy
```

The system does not become one monolithic harness. Full external harnesses remain
separate executables behind adapters. Only narrow, license-cleared algorithms,
schemas, and evaluators may be selectively adapted. The Rust evidence kernel
owns candidate identity, task identity, trace normalization, cost accounting,
non-compensable constraints, promotion, claim boundaries, and replay.

Any licensed upstream fork or read-only source mirror lives in its own external
repository or disposable external worktree. This monorepo receives only reviewed
wrappers, manifests, independently implemented contracts, or exact-file
adaptations authorized by a later state slice. This roadmap does not authorize
vendoring, subtree merges, or external clones in the current checkout.

The target optimization problem is:

```text
minimize expected full economic cost

subject to:
  verified utility >= preregistered threshold
  pass-all-k reliability >= preregistered threshold
  p95 latency <= preregistered ceiling
  tested false-authority rate == 0
  tested cross-tenant leakage rate == 0
  harm upper confidence bound <= preregistered ceiling
  audit completeness == 100%
```

The primary result is a constrained Pareto frontier. A single composite score is
secondary and may not compensate for an authority, integrity, safety, leakage,
or audit failure.

## 2. Why This Belongs Here

The existing repository already owns several required foundations:

- `zkbench-core` owns deterministic generation, mutation, replay, provenance,
  evidence records, claim boundaries, score reports, resumable soak execution,
  and failure corpora.
- `hsai-agent-admission` owns typed proposals, deterministic admission,
  cost-route metadata, model-lane provenance, audit journals, adversarial corpus
  evaluation, and explicit `authority_granted = false` boundaries.
- Astral research contributes acquisition-versus-retrieval controls, context
  removal, restart, retention, withheld composition, sealed assessment, and
  contamination-lineage discipline.
- Statebook contributes exact state identity, semantic normalization, and the
  principle that terminal state should be graded from typed state rather than
  persuasive model text.

The new system should reuse those concepts without changing their present claim
ceilings. Agent performance and research evidence remain separate lanes.

## 3. Non-Goals

- Do not merge the full source trees of Codex, Claude Code, Kimi Code, Pi,
  Hermes, OpenCode, OpenShell, or any other harness into this repository.
- Do not treat a model response, LLM judge, harness self-report, or successful
  command exit as task truth.
- Do not optimize on a sealed assessment set.
- Do not call retrieval success "learning" without restart/context-removal and
  swapped-memory controls.
- Do not let an optimizer mutate graders, task oracles, thresholds, authority
  policy, pricing snapshots, stop rules, or assessment tasks.
- Do not collapse cost, utility, safety, latency, and reliability into a number
  that hides failure.
- Do not call related descendants independent replications.
- Do not import code whose license is absent, ambiguous, conflicting, or scoped
  only to a subdirectory.
- Do not run provider or benchmark workloads merely because an adapter exists.

## 4. System Architecture

### 4.1 Stable control plane

The stable control plane is intentionally small:

1. **Task Contract Registry** — versioned tasks, initial state, terminal oracle,
   allowed tools, budgets, authority constraints, and hidden split membership.
2. **Execution Configuration Registry** — immutable configuration identities and
   component digests.
3. **Harness Adapter Registry** — capability declarations and normalized event
   conversion for each harness/version.
4. **Trace and Cost Ledger** — append-only normalized events, token/cache/tool/
   compute/human cost, latency, and final artifacts.
5. **Objective Evaluator** — deterministic end-state and artifact grading.
6. **Constraint Evaluator** — non-compensable authority, safety, leakage,
   integrity, and audit checks.
7. **Router** — selects an admitted configuration under cost, quality, latency,
   and risk constraints.
8. **Candidate Evolver** — proposes configuration changes using development data
   only.
9. **Promotion Controller** — keeps, rejects, quarantines, or rolls back a
   candidate after preregistered gates.
10. **Evidence Exporter** — produces replayable manifests and bounded claims.

### 4.2 External execution plane

Each harness runs outside the evidence kernel through an adapter-owned worker:

```text
Meta-harness request
  -> immutable RunManifest
  -> isolated HarnessAdapter
  -> external harness process or fixture worker
  -> raw trace quarantine
  -> normalized TraceEnvelope
  -> objective evaluation
  -> constraint evaluation
  -> ResultEnvelope
  -> candidate history and evidence proposal
```

P0-P3 use pure-data fixtures and fake workers. Live processes remain disabled
until an explicit execution boundary and sandbox policy are reviewed.

### 4.3 Recursive levels

The same select-execute-verify-promote primitive operates at five levels:

- call: model choice;
- step: context, memory, tool, and verifier choice;
- task: harness/version choice;
- workflow: composition of specialized configurations;
- fleet: candidate generation, specialization, promotion, rollback, and retirement.

Recursion is an implementation property. It is not evidence of self-improvement,
general intelligence, or breakthrough status.

### 4.4 Two evaluation regimes

Results must remain split into two non-interchangeable regimes:

1. **Normalized causal regime** — identical model artifact, task state, exposed
   tools, budgets, timeout, repetitions, and grader across harnesses. This
   estimates the harness treatment effect.
2. **Native-best deployment regime** — each harness uses one preregistered,
   documented best configuration within the same external action and spend
   envelope. This estimates deployable system performance.

No aggregate leaderboard may pool these regimes. A native-best result cannot be
used to identify a causal harness effect, and a normalized result cannot be
presented as the best achievable deployment for that harness.

## 5. Canonical Contracts

P1 must freeze these pure-data contracts before any executable adapter:

### 5.1 `TaskContractV1`

- task id, family id, template id, authoring lineage, and split id;
- initial-state manifest and digest;
- terminal-state oracle id and digest;
- allowed/forbidden tools and external effects;
- time, token, dollar, tool-call, and retry budgets;
- authority and data-boundary policy digests;
- objective grader inputs and partial-credit rules;
- hard constraint list;
- contamination and publication state;
- expected artifact contract.

### 5.2 `ExecutionConfigurationV1`

- harness id, version, source revision, package digest, and adapter id;
- model lane and exact provider/model/artifact identity;
- system prompt/template digest and sampler parameters;
- context selection and compaction policy;
- memory store, ingestion, retrieval, forgetting, and redaction policy;
- tool schema and permission profile;
- retry, recovery, timeout, and termination policy;
- verifier mixture and escalation policy;
- price-table and hardware-accounting snapshot;
- parent configuration and mutation lineage;
- capability and nonclaim declarations.

### 5.3 `TraceEventV1`

- monotonic event sequence and causal parent;
- wall and monotonic timestamps;
- call, tool, file, process, memory, router, verifier, and human-event kinds;
- cached/uncached input, output, and reasoning-token accounting;
- tool/API/compute/storage charges;
- context and memory references by digest, never undeclared raw secrets;
- model and harness state visible at the decision point;
- redacted payload digest and artifact references;
- failure class and recovery transition.

### 5.4 `ResultEnvelopeV1`

- objective task utility in `[0, 1]`;
- each hard-constraint result;
- authority granted/attempted/denied fields;
- task completion, timeout, DNF, infrastructure failure, and refusal class;
- full economic cost and provider-variable cost;
- latency distribution and human-review minutes;
- normalized failure fingerprint;
- audit completeness;
- claim boundary;
- raw and normalized trace digests.

### 5.5 `RouteDecisionV1`

- router id/version and feature-schema digest;
- router-visible state only;
- eligible configuration set and exclusion reasons;
- predicted utility interval, cost interval, latency interval, and harm bound;
- chosen configuration and fallback;
- exploration/exploitation reason;
- abstain/escalate result;
- decision latency and cost.

### 5.6 `PromotionDecisionV1`

- candidate and parent configuration ids;
- development, tune, and sealed-assessment commitments;
- preregistered thresholds;
- non-inferiority, cost, reliability, safety, leakage, and audit results;
- multiple-comparison correction and uncertainty method;
- `keep`, `reject`, `quarantine`, `rollback`, or `needs-independent-review`;
- reviewer identities and evidence bundle digests.

## 6. Full Economic Cost And Verified Utility

For task `i`, repetition `j`, and configuration `z`:

```text
utility(i,j,z) =
  objective_score(i,j,z)
  * indicator(all hard constraints pass)
```

An unsafe completion has zero verified utility even if the business result is
otherwise correct. Harm is also reported as a separate count and rate.

```text
CostPerVerifiedUtility(z) =
  sum(full_economic_cost(i,j,z))
  / sum(task_weight(i) * utility(i,j,z))
```

Zero verified utility produces infinite cost per verified utility.

`full_economic_cost` includes:

- cached and uncached input tokens;
- output and separately billed reasoning tokens;
- router, verifier, retry, compaction, and summarization calls;
- embeddings, memory ingestion, retrieval, storage, and deletion;
- tool and external API charges;
- local CPU/GPU energy and amortized hardware;
- sandbox and infrastructure charges;
- failure cleanup;
- human review and intervention minutes at a declared rate.

Provider-variable cost and full economic cost are reported separately. Price
tables are versioned observations, not timeless constants.

## 7. Upstream Source Integration Policy

### 7.1 Four source dispositions

- **DEPEND/PIN** — consume the upstream package or executable at an exact version
  behind our adapter; no copied implementation.
- **ADAPT/FORK** — copy only named files or algorithms from an exact licensed
  revision, retain notices, and maintain a local modification ledger.
- **BEHAVIORAL ORACLE** — run or replay upstream behavior only to verify our
  independent interface/algorithm.
- **REFERENCE-ONLY** — use published architecture or experimental results; copy
  no code.

### 7.2 Required provenance for every imported file

- canonical repository URL;
- exact commit SHA and branch/tag;
- source path;
- SPDX license and license-file digest;
- copyright notice;
- import date;
- local destination;
- transformation description;
- local maintainer;
- upstream tests retained or re-expressed;
- semantic-difference tests;
- update and retirement policy.

All imported code must be entered in a machine-readable `upstream-sources.toml`
before merge. A later implementation slice should make missing or changed source
identity fail closed.

### 7.3 P0 source ledger snapshot — 2026-08-01

#### Primary optimization and routing sources

| Source | Pinned revision | License status | Intended use | Disposition |
|---|---|---|---|---|
| [Adaptive Auto-Harness / A-Evolve release branch](https://github.com/A-EVO-Lab/a-evolve/tree/release/adaptive-auto-harness) | `17bc9ebb7d4d142af1b109b43ef160031967cc9a` | MIT in the release branch; current `main` lacks a root `LICENSE` | Adaptation registry, whole-store/tree/retrieval operators, evolution history, versioning, guarded harness-tree selection | ADAPT/FORK only the pinned licensed release branch |
| [TwinRouterBench](https://github.com/CommonstackAI/TwinRouterBench) | `430acecac71141de77afd8e5e13690d236d58e93` | Apache-2.0 | Static/dynamic router conformance, locked pool/pricing, realized-cost audit, step-level route baselines | ADAPT/FORK evaluator and schemas; audit dataset licenses separately |
| [OpenSquilla](https://github.com/opensquilla/opensquilla) | `186b3c147cdc583a9248bc4ceae6faccffc78907` | Apache-2.0 | Harness-state routing policy, decision records, promotion gates, cost rollups, memory quarantine/receipts | ADAPT pure-data interfaces and gates; never import serialized model assets without hash pin and sandbox |
| [RouteLLM](https://github.com/lm-sys/RouteLLM) | `0b64fdafe049e596a3f5657c219329f24af24198` | Apache-2.0 | Strong/weak query-level baseline and threshold calibration | DEPEND/PIN or small adapter; not the production router |
| [GEPA](https://github.com/gepa-ai/gepa) | `ba30ee24e8f63dfdb9e557ed8cfaaec7aa09a6df` | MIT | Candidate generation and reflective mutation over declared tunable components | DEPEND/PIN behind a candidate-proposer adapter; never owns assessment or promotion |
| [Stanford Meta-Harness](https://github.com/stanford-iris-lab/meta-harness) | `44b9942127847f7421db70d8c7e48407f09a3c70` | MIT | Behavioral oracle for harness editing, Terminal-Bench integration, and memory ablations | ADAPT tests/protocol; do not wholesale fork |
| [Microsoft Trace](https://github.com/microsoft/Trace) | `8190d032e43ffe18943a8cad9ea9ee99e43d6773` | MIT | Computation-graph tracing and feedback-propagation design | REFERENCE initially; consider isolated adapter after P4 |
| [World Model Optimizer](https://github.com/experientiallabs/world-model-optimizer) | `7ce2de04eab744ed02241611b113817d9cf7ca47` | No root license or root project license declaration found | Pareto, policy, reward, sweep, evaluation, leak-free retrieval, distillation architecture | REFERENCE-ONLY until an explicit license grant exists |
| [BudgetMem](https://github.com/ViktorAxelsen/BudgetMem) | `91c17435f3b7634711a22fe9cb303ec15069a7aa` | Root `LICENSE` says Apache-2.0; package metadata says MIT | Low/Mid/High memory-budget contract and cost-aware memory routing | REFERENCE-ONLY until license conflict is clarified |

The exact high-value source seams are:

- A-Evolve: `agent_evolve/protocol/adaptation/`,
  `agent_evolve/engine/{base,history,loop,trial,versioning,observer}.py`, and
  `agent_evolve/algorithms/navigation/`.
- TwinRouterBench: `main/{metrics,pricing,router_llm}.py`,
  `swerouter/{router,usage,pricing,trace_cost_audit}.py`, `swerouter/routers/`,
  and `data/dynamic/{model_pool,model_pricing,tier_to_model,ttl_policy}.json`.
- OpenSquilla: `engine/routing/`, `engine/steps/router_decision_record.py`,
  `squilla_router/self_learning/`, `persistence/router_decision_writer.py`,
  `session/cost_rollup.py`, and memory evidence/quarantine/receipt contracts.
- GEPA: `src/gepa/core/`, proposer interfaces, and acceptance/evaluation/candidate
  policy abstractions. GEPA may propose; our promotion controller decides.
- Meta-Harness: Terminal-Bench controller/wrapper tests and text-classification
  memory ablation reference.

#### Harness subjects

| Harness | Pinned source snapshot | License/use decision |
|---|---|---|
| [Pi mono](https://github.com/badlogic/pi-mono) | `aa0ec808b970db31822e07835a46647cb51d9d66` | No root license detected in P0 audit; executable adapter only until clarified |
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | `7f4d155159e2a5d4098bb2f27d3fccb01ff84c3d` | MIT; executable adapter first, selective source study later |
| [OpenCode](https://github.com/anomalyco/opencode) | `dev` at `32f278b48f1a495611165d8a9f1ace0b512933e2` | MIT; executable adapter, not source merge |
| [Codex](https://github.com/openai/codex) | `e22479a62eed9c3b78a67b313f4332c2c0ba9670` | Apache-2.0; executable adapter and trace normalizer |
| [Kimi Code](https://github.com/MoonshotAI/kimi-code) | `4a550effdfcb29a25a5d325bf935296cc50cd417` | MIT; executable adapter and version-pinned comparison |
| [Kimi CLI legacy](https://github.com/MoonshotAI/kimi-cli) | version pin required in P2 | Apache-2.0; legacy comparison only because the project is being wound down |
| Claude Code | vendor-distributed executable | No source fork; black-box executable adapter subject to terms and exportable trace surface |

The harness adapter evaluates native behavior. It must not force all harnesses
into a fake shared internal loop. External conditions are shared—task state,
tools, budgets, timeouts, model identity, and grader—while native planning,
context management, retries, and termination remain observable treatment
variables.

#### Runtime and memory references

| Source | Revision/license | Role |
|---|---|---|
| [NVIDIA OpenShell](https://github.com/NVIDIA/OpenShell) | `736e431d454c7de8a71e0fcdd3221ad6f9a552cb`, Apache-2.0 | Candidate sandbox/runtime backend; integrate as an adapter, never make it evidence authority |
| [Mem0](https://github.com/mem0ai/mem0) | `50bdaaea0c02744720ed374d88584fd01494eeb7`, Apache-2.0 | Memory-system benchmark subject and adapter |
| [Letta](https://github.com/letta-ai/letta) | `ff19ffeafeb54bd2a7dc5d4a552f10191732a235`, Apache-2.0 | Stateful-memory benchmark subject and adapter |
| [Harness-Bench](https://arxiv.org/abs/2605.27922) | paper and released artifacts must be pinned in P0B | Task/evaluation design reference; 106 tasks and 5,194 trajectories motivate configuration-level reporting |

## 8. Repository Shape

No code path below is authorized by this document. The proposed implementation
shape is:

```text
crates/
  meta-harness-protocol/           # pure-data contracts and tagged hashing
  meta-harness-eval/               # objective, constraint, trace, and cost evaluation
  meta-harness-memory/             # memory-policy contracts and causal controls
  meta-harness-router/             # deterministic baselines; learned artifact adapter later
  meta-harness-runtime/            # worker protocol; no accepted-evidence writes
  meta-harness-optimizer/          # immutable-bundle candidate evaluation
  meta-harness-admission-bridge/   # one-way bridge to existing HSAI admission

tools/
  meta-harness-worker/             # later Python worker, isolated from Rust evidence authority
  meta-harness-analysis/           # statistics, plots, bootstrap, power simulation

docs/research/
  recursive-meta-harness-p0-roadmap.md

repository-external artifacts/
  source-mirrors/                  # pinned upstream worktrees, never evidence by presence alone
  runs/                            # immutable run manifests and raw traces
  normalized/                      # normalized trace/result envelopes
  assessments/                     # sealed commitments and results
```

Dependency boundaries are directional: `meta-harness-protocol` depends only on
pure serialization and hashing foundations; `zkbench-core` never depends on a
meta-harness crate; the existing `hsai-agent-admission` crate remains independent;
only `meta-harness-admission-bridge` may depend on both sides. Runtime code never
writes accepted evidence. The optimizer consumes immutable run bundles. No
runtime crate depends on Astral Python. The exact executable adapter seam remains
unfrozen until P0B has pinned and compared at least two real adapters.

The pure-data Rust crates may depend on stable existing local types only where
semantics and claim boundaries match exactly. A future Python worker never writes
an accepted Evidence Ledger and never grants authority. Cross-language exchange
uses closed JSON schemas, strict unknown-field rejection, digests, and independent
Rust readback.

## 9. End-to-End Phase Plan

### P0 — Charter, threat model, source bill of materials, and baseline freeze

**Goal:** close the research question and legal/provenance boundary before code.

**Deliverables:**

- this roadmap reviewed as a `Level0DesignNote`;
- exact metric definitions, non-compensable constraints, and claim ladder;
- machine-readable candidate source ledger with SHA and SPDX status;
- data/dataset license ledger separate from code licenses;
- optimizer threat model: grader tampering, prompt leakage, memory poisoning,
  route manipulation, cost falsification, artifact substitution, lineage fraud,
  unsafe exploration, and benchmark overfit;
- frozen initial harness/model/version matrix;
- compute, provider, tool, and human-review budget proposal;
- P1 pure-data contract spec.

**Gate:** zero unknown-license items in the future copy/import set; every
reference-only item explicitly excluded from copied code; no runtime authorized.

**Stop:** any required code has no compatible license or cannot be isolated from
assessment/evidence authority.

### P0B — Upstream behavioral and dependency audit

**Goal:** understand the exact seams before choosing what to adapt.

**Deliverables:**

- repository-external, read-only checkouts at the pinned revisions;
- software bill of materials and transitive-license report;
- source-to-local interface mapping;
- retained upstream tests and semantic-difference test plan;
- malicious serialized-artifact audit, especially `.pkl` and `.joblib`;
- network, filesystem, subprocess, credential, telemetry, and model-download
  surface census;
- decision record for each source: depend, adapt, oracle, or reference-only.

**Gate:** two-person review of license and execution-surface census before any
file enters the repository.

### P1 — Pure-data meta-harness protocol

**Goal:** freeze identities and contracts without executing a harness.

**Deliverables:**

- standalone Rust protocol crate;
- types from Section 5 with closed enums and strict validation;
- deterministic domain-separated hashing;
- schema-version and capability negotiation;
- parent/descendant lineage and contamination ancestry;
- fixtures for valid and invalid manifests;
- serialization round-trip and unknown-field rejection tests;
- source-provenance manifest type.

**Source use:** independent local implementation; upstream schemas are references
only at this phase.

**Gate:** focused tests, contract tests, formatting, source scans proving no
process/network/filesystem/model dependencies, and existing claim-boundary docs
gate.

**Exit:** two implementations can independently compute identical identities
from the same fixture bytes.

### P2 — Harness adapter conformance protocol

**Goal:** normalize heterogeneous harness behavior without erasing native
differences.

**Deliverables:**

- `HarnessAdapter` capability and event-conversion contract;
- pure-data fixture adapters for Pi, Hermes, OpenCode, Codex, Kimi Code, and
  Claude Code trace shapes;
- adapter conformance suite covering tool calls, file changes, model calls,
  memory access, retries, compaction, timeout, refusal, recovery, and terminal
  state;
- raw-trace quarantine and lossless artifact references;
- unsupported-feature and missing-telemetry classifications;
- version-drift detector.

**Source use:** executable/source subjects remain external. No full harness source
is copied. Adapter-owned parsers may use public schemas or independently observed
non-secret trace fixtures.

**Gate:** identical fixture bytes normalize deterministically; missing telemetry
cannot silently become zero; adapter errors remain distinct from task failures.

### P3 — Trace, pricing, and full-cost ledger

**Goal:** make cost and execution history independently recomputable.

**Deliverables:**

- append-only normalized trace ledger;
- locked pricing and cache-policy snapshots;
- token/cache/tool/compute/storage/human-review cost accounting;
- infrastructure-failure and timeout accounting;
- cost recomputation and drift reports;
- exact-cents or fixed-point arithmetic—no floating monetary authority;
- audit completeness score with fail-closed missing-event handling.

**Source use:** adapt TwinRouterBench pricing, usage, and trace-cost audit
semantics under Apache-2.0; preserve source notices and add semantic-difference
tests. OpenSquilla cost rollup is a comparison oracle.

**Gate:** independently recomputed totals match fixture expectations; price drift
changes result identity; zero-cost missing telemetry is impossible.

### P4 — Objective task and benchmark plane

**Goal:** establish real terminal-state graders before optimizing anything.

**Task families:**

- repository coding and repair;
- structured-data reconciliation and audit;
- multi-application workflows with exact end states;
- research/evidence synthesis with source constraints;
- long-horizon resume/recovery;
- authority-sensitive actions executed only against inert fixtures;
- memory update, contradiction, forgetting, and provenance cases;
- adversarial tool/prompt/memory injection cases.

**Deliverables:**

- 8-12 families with 20-30 independently authored templates per family;
- deterministic or state-based graders wherever possible;
- partial-credit components with no LLM-only final authority;
- hidden mutation generator and canaries;
- fixed development/tune/assessment split by author and template lineage;
- task-cluster identity and contamination registry;
- sample-size power simulation from pilot variance.

**Source use:** Harness-Bench and Composio-style end-state evaluation are design
references. TwinRouterBench supplies a separate routing benchmark, not the only
task distribution.

**Gate:** every task is solvable, oracle-checkable, mutation-tested, and reviewed;
assessment content is sealed before optimizer access.

### P5 — Fixed-harness baseline campaign

**Goal:** reproduce the motivating harness effect before building a router.

**Matrix:**

- same model across all compatible harnesses;
- native harness behavior preserved;
- memory off and routing off;
- common task state, tool exposure, budget, and timeout policy;
- at least five stochastic repetitions per cell after power review;
- randomized execution order blocked by task, seed, provider time window, and
  model snapshot.

**Baselines:** each native harness/version, a minimal loop, and no-action/control
failure cases.

**Metrics:** verified utility, pass-all-k, timeouts, DNFs, latency, token/tool
counts, provider-variable cost, full cost, human interventions, failure
fingerprints, and audit completeness.

**Gate:** task-cluster bootstrap intervals and paired tests published with all
timeouts and failures. No winner language from point estimates alone.

The normalized causal campaign completes first. A separately labeled native-best
campaign may follow after each harness configuration is frozen. Its results are
reported in a separate table and evidence bundle.

### P6 — Memory plane and causal memory evaluation

**Goal:** determine when memory creates verified utility rather than retrieval
appearance or contamination.

**Memory modes:**

- no memory;
- full transcript;
- raw retrieval;
- structured episodic memory;
- procedural/runbook memory;
- summary/compaction memory;
- Low/Mid/High budget tiers;
- oracle memory as an upper bound.

**Adversarial controls:**

- stale and contradictory memory;
- irrelevant decoys;
- poisoned and prompt-injected memory;
- swapped-memory counterfactuals;
- cross-user and cross-tenant leakage;
- selective forgetting and deletion verification;
- restart and context removal;
- withheld paraphrase, multi-hop, and composition cases;
- source-provenance and citation integrity.

**Source use:** Mem0 and Letta are adapters/subjects; BudgetMem is concept-only
until its license conflict is resolved; OpenSquilla memory quarantine and
receipt contracts may be adapted after P0B review.

**Gate:** report utility lift over no-memory at matched full cost, retrieval
precision/recall, stale-reliance, poison-execution, leakage, forgetting, and
retention. Memory cannot enter the router candidate set until hard leakage and
poisoning gates pass.

### P7 — Deterministic routing baselines

**Goal:** quantify routing headroom before learned routing.

**Routes:**

- always cheapest;
- always strongest;
- random admitted configuration;
- round robin;
- fixed task-family map;
- static risk/value thresholds;
- RouteLLM-style strong/weak query baseline;
- oracle best configuration, computed post hoc only;
- worst configuration diagnostic.

The router selects a complete execution configuration, not only a model.

**Source use:** TwinRouterBench router interface and deterministic metrics adapted;
RouteLLM pinned as a legacy query-level baseline.

**Gate:** routing overhead is included; route exclusions and abstentions are
auditable; the oracle is never available at solve time.

### P8 — Learned harness-state router

**Goal:** select the cheapest configuration meeting calibrated utility and risk
constraints.

**Initial model:** interpretable ranker or calibrated tree model over preregistered
router-visible features. No opaque frontier-model router is the first baseline.

**Features:** task contract, tool requirements, state size, failure history,
context pressure, memory need, risk/value class, latency budget, and admitted
configuration capabilities. Never include hidden outcomes or assessment labels.

**Outputs:** utility/cost/latency intervals, harm upper bound, chosen
configuration, fallback, abstention, and escalation.

**Source use:** adapt OpenSquilla's pure routing policy, decision record, dataset,
evaluation, and promotion-gate concepts. Do not import trained `.pkl`/`.joblib`
artifacts. Train from our development traces or remain rule-based.

**Metrics:** calibration error, selective risk-coverage, oracle regret,
escalation rate, route churn, overhead, utility non-inferiority, and cost delta.

**Gate:** preregistered non-inferiority on verified utility and reliability,
meaningful full-cost reduction, no hard-constraint regression, and stable hidden
mutation performance.

### P9 — Candidate evolution and harness tree

**Goal:** generate specialized configuration candidates without granting the
optimizer control of evidence or assessment.

**Candidate edit space:** prompts, tool descriptions, context policy, memory
policy, retry/termination policy, verifier depth, route thresholds, and bounded
adapter configuration. Model weights, task graders, hard constraints, sealed
tasks, claim logic, and evidence acceptance remain outside the edit space.

**Source use:**

- adapt the pinned licensed Adaptive Auto-Harness release interfaces and
  tree/retrieval/filter operators;
- depend on GEPA as one candidate proposer;
- use Stanford Meta-Harness as a behavioral oracle;
- study WMO architecture without copying code.

**Required mechanics:** isolated candidate worktree, mutation manifest, parent
lineage, fixed trial budget, development-only feedback, rollback, candidate
quarantine, and immutable evaluator identity.

**Gate:** every candidate is reproducible from parent plus mutation manifest;
shared-history descendants are one lineage; a candidate cannot modify its own
gate or evidence record.

### P10 — Continual and distribution-shift program

**Goal:** test whether improvements compound rather than overfit one frozen
benchmark.

**Protocol:** chronological task batches, frozen previous champion, fixed
optimization budgets, new-family arrival, regressions on prior tasks, and
specialist-versus-generalist routing.

**Measures:** lifelong average verified utility, backward transfer, forward
transfer, regression count, specialization gain, routing capture of oracle
headroom, and cost of adaptation.

**Stop:** halt promotion when the candidate improves the new batch but violates
prior non-inferiority, safety, leakage, or audit gates.

### P11 — Adversarial governance and authority boundary

**Goal:** ensure the optimizer cannot turn operational improvement into
unauthorized action.

**Attacks:** grader gaming, task leakage, route manipulation, forged cost rows,
policy downgrade, stale approvals, trace deletion, duplicate JSON keys,
artifact substitution, prompt/tool injection, memory poisoning, cross-tenant
retrieval, unsafe exploration, candidate self-promotion, and reviewer collision.

**Integration:** HSAI admission remains the authority gate. Meta-harness output
is proposal and evaluation metadata. `authority_granted` remains false unless a
separate existing admission path accepts an explicitly bounded handoff.

**Gate:** deterministic adversarial corpus, negative controls, replay, tamper
detection, independent digest recomputation, and zero tested false-authority
events.

### P12 — Sealed confirmation

**Goal:** evaluate one frozen champion and named baselines on unseen tasks.

**Rules:**

- configuration, router, prompts, memory policy, weights, thresholds, price
  snapshot, and stop rules lock before assessment access;
- assessment tasks remain inaccessible to evolvers and memories;
- no adaptive assessment tuning;
- all runs, including failures and timeouts, are retained;
- confirmatory analysis follows the preregistered statistical plan;
- unexpected analysis is labeled exploratory.

**Gate:** statistically supported Pareto improvement across at least three
materially different domains, utility/reliability non-inferiority, meaningful
full-cost reduction, hard constraints satisfied, and complete replay artifacts.

**Claim ceiling:** `LocalDevelopmentMetaHarnessCandidate` or another separately
reviewed local claim. Not independent, production, or SOTA evidence.

### P13 — External replay and independent reproduction

**Goal:** move from local candidate evidence to reproducible and independently
reproduced evidence.

**Deliverables:** non-secret source bundle, exact container/runtime identities,
task and grader commitments, configuration registry, price snapshots, raw and
normalized traces, analysis code, failure corpus, and verifier instructions.

**Gate:** a separate team reproduces the result without shared mutable history,
private assessment leakage, or hidden manual corrections.

**SOTA language is allowed only if:**

- named current baselines are included;
- the improvement is statistically supported;
- the system Pareto-dominates or extends the frontier under preregistered
  utility, reliability, latency, cost, and safety constraints;
- the result holds across at least three domains and hidden mutations;
- independent reproduction is complete;
- claims identify the exact task distribution and configuration set.

### P14 — Bounded production pilot

**Goal:** test operational value without silently widening authority.

**Requirements:** explicit buyer/task scope, sandboxed tools, reversible actions,
human escalation, per-run and aggregate budget caps, kill switch, privacy and
retention policy, incident response, price/availability drift monitoring,
router fallback, champion rollback, and deployment-readiness evidence separate
from benchmark evidence.

**Gate:** production safety review, external security review, service-level
observability, documented on-call ownership, and explicit authorization.

## 10. Statistical Plan

- Use task as the paired unit and task family/template as clustering levels.
- Determine repetitions and final sample size by power simulation from P5 pilot
  variance; five repetitions per cell is a starting floor, not a guarantee.
- Randomize run order and block on task, seed, provider time window, model
  snapshot, and infrastructure class.
- Use hierarchical models for harness, model, memory, router, and interaction
  effects.
- Use task-cluster bootstrap intervals for cost and utility.
- Use paired binary tests for exact pass/fail comparisons and correct multiple
  comparisons.
- Predeclare a utility non-inferiority margin and minimum meaningful cost
  reduction before assessment. An initial planning value may be no more than a
  two-percentage-point verified-utility loss with at least 20% lower full cost,
  but P0 must justify the final values from buyer/task risk.
- Report pass-all-k reliability, not pass@k alone.
- Publish timeouts, DNFs, refusals, infrastructure failures, and human rescues.
- Separate exploratory, tune, confirmatory, and independently reproduced results.

## 11. Anti-Goodhart And Contamination Controls

- Objective state-based graders dominate LLM judges.
- Evaluator and constraint code are immutable to candidate workers.
- Hidden mutations rotate after every optimization cycle.
- Assessment tasks are withheld until configuration locking.
- Task families split by author, template, and semantic lineage.
- Memory stores are scrubbed of assessment content before confirmation.
- Restart/context-removal and swapped-memory controls distinguish retained
  capability from contextual support.
- Optimizer-generated task or grader changes enter a separately reviewed corpus
  proposal lane and never affect the current candidate's score.
- Route features are logged and checked for outcome leakage.
- All candidate and worker ancestry is recorded.
- Only immutable frozen-worker artifacts may enter evidence review.

## 12. Fork And Update Workflow

Every adapted upstream follows this sequence:

1. Create a repository-external read-only checkout at the reviewed SHA.
2. Verify commit, tree, license, and source-file digests twice.
3. Review dependencies, network/process/filesystem behavior, and serialized
   executable artifacts.
4. Record the disposition and exact allowed source paths.
5. Import the smallest coherent seam with original notices.
6. Add source-parity tests and local semantic-difference tests.
7. Add a local change ledger; never obscure which lines were adapted.
8. Run focused tests, contract gates, and the heavy repository gate appropriate
   to that future implementation slice.
9. Review and merge one upstream at a time.
10. Treat every future upstream update as a new source identity with a fresh
    review; never float branches or dependency ranges in evidence runs.

Unlicensed WMO root code and license-conflicted BudgetMem code are hard stops for
copying. Architectural similarity does not create permission.

## 13. Critical Path And Parallel Work

Critical path:

```text
P0 -> P0B -> P1 -> P2 -> P3 -> P4 -> P5
                                   |
                                   +-> P6 -> P7 -> P8 -> P9
                                                    |
                                                    +-> P10 -> P11 -> P12
                                                                   |
                                                                   +-> P13 -> P14
```

Safe parallel work after P1:

- adapter-fixture development;
- cost-ledger implementation;
- task authoring and oracle review;
- source-license and dependency audits;
- memory threat-corpus authoring;
- statistical power simulation.

Unsafe parallelism:

- adapting several upstream optimizers into the same mutable branch;
- exposing assessment tasks while candidate evolution is running;
- sharing memory/history between purported independent replications;
- starting live provider runs before trace and cost completeness exist.

## 14. First Executable Tracer Bullet

The first implementation should be deliberately small:

1. Three deterministic fixture tasks.
2. Two fake harness adapters with visibly different retry and context policies.
3. One fixed model lane represented by fixture calls.
4. Memory disabled.
5. Three routers: always-A, always-B, and task-family map.
6. Exact trace and cost ledger.
7. Objective terminal-state grader.
8. One authority-violation negative case.
9. Deterministic result and promotion preview.

Success means the system can prove which configuration was selected, reconstruct
its cost, grade its terminal state, reject the authority violation, and reproduce
the same result from fixtures. It does not mean real agent or model performance.

## 15. P0 Exit Checklist

- [ ] Objective and non-goals accepted.
- [ ] Primary metric and hard constraints accepted.
- [ ] Source dispositions reviewed.
- [ ] A-Evolve release SHA and license pinned; moving `main` excluded.
- [ ] WMO marked reference-only.
- [ ] BudgetMem license conflict remains a copying stop.
- [ ] Dataset licenses separated from code licenses.
- [ ] Pure-data P1 state slice authorized separately.
- [ ] No runtime, model, network, spend, or benchmark execution authorized.
- [ ] Repository-external artifact and source-mirror policy accepted.
- [ ] Independent-reproduction criterion accepted before any SOTA language.

## 16. Current Claim

This roadmap establishes a coherent research and implementation sequence for a
recursive, evidence-bound meta-harness. It records current source candidates and
legal/technical dispositions. It does not establish that the architecture is
novel, implemented, useful, cost-saving, safe, production-ready, SOTA, or a
breakthrough.
