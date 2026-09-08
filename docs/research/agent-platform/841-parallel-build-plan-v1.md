# HSAI Agent Platform Parallel Build Plan V1

## Status and state slice

This plan is an additive planning artifact under named state slice
`hsai-proof-carrying-capability-bounded-agent-platform-parallel-plan-v1`.

It converts the proof-carrying, capability-bounded agent thesis into isolated
workstreams that can progress in parallel after a shared contract freeze. It
does not authorize model execution, provider execution, dataset acquisition,
cryptographic signing, OS enforcement, secret custody, settlement, deployment,
or reopening any closed Astral or Oak Lab slice.

The current implementation remains bounded by
`hsai-proof-carrying-capability-bounded-agent-platform-v1`: local pure-data
control-plane and caller-owned file-persistence contract evidence only.

## Operating rule

Measure twice, cut once. Every lane must first freeze its Interface and claim
ceiling, then implement the smallest Adapter behind that Seam, then validate
the Interface through independent tests. A green local test is not external
evidence, runtime enforcement, alignment evidence, or production readiness.

The model is proposal-only throughout the plan. It cannot approve evidence,
grant capabilities, alter policy, select an evaluator, promote an update,
release a payment, or suppress a rollback.

## End-to-end target

```text
user intent
  -> typed proposal
  -> adversarial evaluation
  -> independently validated evidence
  -> deterministic admission
  -> short-lived capability lease
  -> isolated reversible execution
  -> observation and invariant checking
  -> rollback, freeze, quarantine, or completion
```

The compute-market extension is deliberately downstream:

```text
typed compute job
  -> provider offer
  -> fixed runtime execution
  -> typed result receipt
  -> independent verification
  -> separately authorized settlement
```

ZK, MPC, and FHE are future Adapters. Their presence in a design record does
not establish correctness, confidentiality, availability, input truthfulness,
alignment, or settlement finality.

## Current foundation

The repository already contains the first local contract slice:

| Existing Module | Interface currently available | What it does not establish |
| --- | --- | --- |
| `hsai-control-plane` | `AgentProposal`, `CapabilitySet`, admission, `CapabilityReceipt`, `ExecutionPermit`, `ReplayJournal`, monitoring, alignment/update plans, compute matching, `ReplayJournalFileStore` | Signature verification, OS or network enforcement, secret custody, provider execution, settlement, formal proof, semantic correctness |
| `hsai-control-plane-checker` | Independent recomputation of receipt, permit, monitor, alignment, learning, market, and journal invariants | External independence, proof verification, authority, alignment evidence |
| `docs/research/agent-platform/840-...` | Architecture, threat model, alignment tracks, safe-learning policy, market topology, invariants, nonclaims | An implementation or authorization for the future lanes |

The file-backed journal is local persistence plumbing. It supports canonical
bytes, atomic temp-file replacement, and valid-temp recovery, but it does not
provide cross-process locking or linearizable compare-and-swap.

## Source coverage audit

The pasted thesis is reflected as a roadmap, not as completed evidence. The
following mapping is the completeness check for this plan:

| Source requirement | Plan location | Status |
| --- | --- | --- |
| North-star proposal-to-rollback flow | End-to-end target; Wave 2 integration | Mapped, local contracts only |
| Clean-room and provenance discipline | Parallel execution protocol | Mapped and binding for every lane |
| Contract, security kernel, evidence, benchmark, alignment, learning, runtime, governance | Waves 0–6 and Lanes A–E | Mapped; implementation remains gated |
| Routing, memory, candidate adaptation, independent evaluation, canary, specialist serving | Wave 3 product wedge | Mapped as separate runtime/adaptation stages |
| Tool interoperability and redacted agent telemetry | SOTA build guidance; Lane E; Wave 3 | Mapped to MCP/tool-manifest and observation Adapters; never authority |
| One fixed compute-market job class | Wave 4 market bridge | Mapped; live execution and settlement remain blocked |
| Boundless, HEIR, Arcium maturity caveats | External technology reality check | Mapped as research context, not local evidence |
| ZK/FHE/MPC and market nonclaims | External technology reality check; Wave 4 | Explicitly preserved |
| Recursive self-improvement hard boundary | Wave 5 governed adaptation and release | Explicitly preserved |
| Source-backed SOTA implementation guidance | [842 SOTA build guidance](842-sota-build-guidance-v1.md) and lane sections | Mapped to Interfaces, Adapters, versions, licenses, threat models, and claim ceilings |
| Outcome-priced work market | [843 outcome-priced work market plan](843-outcome-priced-work-market-plan-v1.md) and Waves 4–6 | Mapped to offchain pricing, Hyperliquid testnet, Stripe/Tempo payment Adapters, evidence resolution, and manipulation controls |

### External technology reality check

The external systems in the source conversation are architectural inputs only:

- Boundless is a reference for a proving market and proof-verification flow,
  not a dependency or evidence source for this repository.
- HEIR supports compiler-directed cryptography, but backend coverage and
  production maturity must be checked per version. A compiler abstraction is
  not a universal transparent backend.
- Arcium is a confidential-MPC reference with Solana-oriented orchestration.
  Any Hyperliquid connection requires a separate bridge with explicit trust,
  liveness, collusion, privacy, and settlement assumptions.
- ZK binds execution to a program and committed inputs. It does not establish
  truthful inputs, useful tasks, data availability, alignment, or human
  benefit.
- FHE/MPC confidentiality depends on the declared threat and collusion model;
  it does not automatically provide correctness, availability, latency, or
  output/metadata leakage resistance.
- A market aligns participants to its payoff function. It does not align an
  agent to humans without explicit admissible actions, dispute rules, privacy
  policy, externality constraints, and release authority.

The intended market claim is therefore narrow: a settlement Adapter may provide
collateral, escrow, price discovery, or payment for externally executed jobs
whose results pass typed receipt verification. The runtime marketplace and the
HSAI evidence/admission plane remain separate Modules joined by a narrow
receipt-bound Adapter Seam.

Public research may inform clean-room reimplementation only with source,
license, version, and provenance records. Semi-closed-source material is
excluded unless redistribution and implementation rights are explicit.

The historical foundation commit identifiers mentioned in the source are
context, not scientific inputs or a substitute for current workspace state.
Live code, current manifests, and current claim ceilings take precedence.

## SOTA build guidance

The source-backed SOTA appendix is
[`842-sota-build-guidance-v1.md`](842-sota-build-guidance-v1.md). It records
current public reference points for evaluation, agent-security benchmarks,
runtime isolation, provenance, serving, parameter-efficient adaptation, formal
verification, verifiable compute, FHE/MPC, and frontier governance.

The operational rule is narrow: adopt a reference as an Interface or Adapter
candidate only after recording its source, license, exact revision or version,
build and artifact digest, runtime assumptions, threat/collusion model, and
claim ceiling. SOTA references do not authorize acquisition, provider calls,
spend, signing, deployment, or evidence acceptance.

The plan therefore uses the following defaults:

- Inspect-like composable evaluation is an optional evaluation Adapter; local
  clean-room semantic families remain the first benchmark input.
- MCP-like tool/resource/prompt interoperability is an optional Adapter behind
  explicit server identity, tool-list digests, consent, schemas, capability
  scope, and egress policy. OpenTelemetry-like GenAI telemetry is redacted,
  version-pinned observation only.
- Firecracker/Jailer and gVisor are separate threat-model-specific runtime
  Adapters; “sandboxed” is not a completed enforcement claim.
- in-toto/SLSA-style provenance and Sigstore-like transparency are record and
  verification references; signatures do not prove semantic correctness.
- vLLM-like structured outputs and prefix caching require tenant-scoped cache
  policy, canonical bytes, and cache-leakage tests.
- LoRA/QLoRA are candidate-generation options inside immutable-base,
  shadow-only, independently evaluated adaptation.
- Kani-style bounded harnesses complement the implementation-diverse checker;
  they do not prove the whole distributed runtime.
- RISC Zero/Boundless-like receipt lifecycles inform the later fixed compute
  market; ordinary receipts come before ZK, MPC, FHE, or chain integration.

No public benchmark score, provider market match, receipt, attestation, FHE/MPC
privacy property, or governance framework raises the current claim ceiling.

The outcome-priced work market extension is recorded in
[`843-outcome-priced-work-market-plan-v1.md`](843-outcome-priced-work-market-plan-v1.md).
It treats Hyperliquid testnet as a market-mechanics Adapter, the offchain
service as the listing and projection surface, HSAI as the evidence and payout
authority, and Stripe or Tempo as separate payment Adapters. The market signal
starts advisory; contractual pricing effects require a later empirical gate.

## Parallel execution protocol

### Shared rules

1. The coordinator freezes the contract packet before execution lanes begin.
2. Each lane receives exactly one state slice, one directory allowlist, one
   claim ceiling, one dependency list, and one exit gate.
3. A lane may add files only below its allowlist and may update shared
   navigation only through a coordinator-owned integration patch.
4. No lane copies code, artifacts, datasets, traces, generated outputs, or
   private data from this repository, another local repository, or a remote
   repository. Public research may inform a clean-room reimplementation only
   with source, license, version, and provenance records.
5. No lane acquires a model or dataset, invokes a provider, spends money,
   signs a receipt, submits a transaction, or changes a closed research slice.
   Any future model/provider execution additionally requires fresh custody,
   exact runtime and model identity, a positive hard spend ceiling, and
   genuinely independent acceptance.
6. Every lane emits a machine-readable manifest, a human-readable claim-
   boundary report, focused tests, and a list of unresolved blockers.
7. Integration consumes lane outputs only after the coordinator verifies
   schema compatibility, state-slice identity, fresh hashes, and claim
   ceilings.

### Lane handoff packet

Every handoff must contain:

```text
state_slice
directory_allowlist
interface_version
input_digests
implementation_digests
test_commands
test_results
known_blockers
claim_ceiling
nonclaims
```

The handoff is a local engineering record. It becomes evidence only after the
separate evidence-plane review and validation gates pass.

## Wave 0 — contract freeze

This is a short coordinator-owned prerequisite. It is not parallel because all
lanes would otherwise invent incompatible meanings for authority, evidence,
promotion, and rollback.

### Deliverables

- threat model for prompt injection, deception, exfiltration, privilege
  escalation, replay, Sybil behavior, reward hacking, self-modification, and
  economic abuse;
- capability lattice for read, write, network, secrets, spend, replication,
  code execution, and self-modification;
- claim ladder for local, attested, proven, and externally validated evidence;
- state machine for proposal, quarantine, admission, execution, rollback,
  freeze, shutdown, and completion;
- failure budgets and automatic freeze conditions;
- typed schema registry with version and digest rules;
- explicit protected surfaces: evaluator, validator, policy, ledger, custody,
  signer, and kill path.

### Exit gate

Every authority transition has a named predecessor, successor, actor,
required evidence, failure disposition, and nonclaim. The contract packet is
hash-locked before Wave 1.

### Ownership

State slice: `hsai-proof-carrying-capability-bounded-agent-platform-contract-
freeze-v1`.

Directory allowlist: `docs/research/agent-platform/` only.

## Wave 1 — five parallel workstreams

The five lanes below may execute in parallel once Wave 0 is frozen. They do not
share mutable implementation directories.

### Lane A — security kernel

State slice: `hsai-proof-carrying-capability-bounded-agent-platform-security-
kernel-v1`.

Directory allowlist:

```text
crates/hsai-control-plane/
crates/hsai-control-plane-checker/
docs/research/agent-platform/security-kernel-v1.md
```

#### Scope

- complete admission and capability-lease semantics;
- add externally verifiable receipt Interface as a separate Adapter seam;
- make delegation and capability narrowing explicit;
- define independent kill-path and freeze-path Interfaces;
- add quota accounting, expiry, clock-skew handling, and rollback records;
- add crash, replay, stale-policy, partial-write, and fault-injection tests;
- specify the future OS sandbox, egress, and secret-broker Adapters without
  pretending the pure-data crate enforces them.

#### Required invariants

```text
no admission -> no capability
rejection -> no governed mutation
expired lease -> no execution request accepted
kill signal -> no continued authorized transition
delegation -> no capability expansion
stale policy -> quarantine
```

#### Exit gate

Focused and property tests pass; an implementation-diverse checker rejects
tampered receipts, forged transitions, replayed nonces, and capability
expansion. The lane reports exactly which guarantees remain caller-owned or
future enforcement work.

#### Explicit nonclaims

No signed receipt, process isolation, egress blocking, secret handling, or
runtime kill enforcement exists until a separately authorized Adapter is
implemented and independently validated.

### Lane B — evidence and provenance

State slice: `hsai-proof-carrying-capability-bounded-agent-platform-evidence-
plane-v1`.

Directory allowlist:

```text
crates/hsai-evidence-plane/
crates/hsai-evidence-plane-checker/
docs/research/agent-platform/evidence-plane-v1.md
```

#### Scope

- source, artifact, dataset, trajectory, evaluator, runtime, policy, and
  configuration manifests;
- exact byte digests, provenance, license, version, and source records;
- external owner-only custody-root Interface and retention state machine;
- quarantine for missing, stale, contradictory, or non-independent evidence;
- operator/reviewer/validator separation;
- prediction locks and assessment configuration locks;
- claim envelopes with meet-only composition and explicit nonclaims;
- aggregate-only release packets.

#### Exit gate

Every accepted claim binds exact bytes, provenance, validator identity,
reviewer identity, freshness, custody identity, and a claim ceiling. The model
can propose an evidence reference but cannot transition it to accepted.

#### Explicit nonclaims

Local manifests do not prove that an input is truthful, a model is aligned, a
runtime is secure, or a provider delivered the claimed result.

### Lane C — adversarial benchmark and evaluation

State slice: `hsai-proof-carrying-capability-bounded-agent-platform-adversarial-
benchmark-v1`.

Directory allowlist:

```text
tools/hsai-adversarial-benchmark-v1/
docs/research/agent-platform/adversarial-benchmark-v1.md
```

#### Scope

Build clean-room, held-out semantic families for:

- instruction conflict and prompt injection;
- tool misuse and data exfiltration;
- privilege escalation;
- deceptive compliance and evaluator gaming;
- reward hacking;
- memory and provenance tampering;
- replication and Sybil behavior;
- unsafe self-modification;
- economic manipulation;
- distribution-shift capability elicitation.

Measure false accepts, false rejects, escalation attempts, containment
latency, rollback success, evidence-integrity violations, evaluator
disagreement, and freeze correctness. Separate fit, tune, and assessment
families; lock predictions and evaluator configuration before assessment.

#### Exit gate

No critical bypass appears across independent runners and held-out attack
families, or the disposition is explicitly `NoCandidate` with preserved
failure evidence and no retuning under the same identity.

#### Explicit nonclaims

A passing local benchmark remains local evidence. It does not establish
frontier capability, general safety, alignment, or production readiness.

### Lane D — alignment measurement

State slice: `hsai-proof-carrying-capability-bounded-agent-platform-alignment-
measurement-v1`.

Directory allowlist:

```text
tools/hsai-alignment-measurement-v1/
docs/research/agent-platform/alignment-measurement-v1.md
```

#### Scope

Run three separate tracks:

1. Behavioral: adherence, uncertainty calibration, corrigibility, shutdown
   cooperation, goal preservation, and distribution shift.
2. Mechanistic: causal intervention and held-out prediction, not probe-only
   explanations. The authorized Gemma V3 bundle remains an isolated research
   lane with its own packet, custody, and claim ceiling.
3. Scalable oversight: independent critics, adversarial evaluators,
   debate-style review, and monitors trained against evaluator gaming.

Every study must bind model, runtime, asset, corpus, split, wrapper, feature
map, estimand, controls, uncertainty, multiplicity, power, repeats, attrition,
prediction lock, independent validator, custody, and nonclaims.

#### Exit gate

Only a held-out causal monitor that predicts consequential behavioral changes,
replicates across the declared model/task set, survives evaluator-gaming
probes, and passes independent validation can become a candidate result.

#### Explicit nonclaims

Intent reports, probe correlations, local fixtures, and a single positive
study do not establish alignment, introspection, consciousness, or causal
self-modeling.

### Lane E — runtime and deployment

State slice: `hsai-proof-carrying-capability-bounded-agent-platform-runtime-
deployment-v1`.

Directory allowlist:

```text
crates/hsai-runtime/
crates/hsai-runtime-checker/
docs/research/agent-platform/runtime-deployment-v1.md
```

#### Scope

- frozen-base model routing;
- prompt classification and deterministic routing logs;
- memory and retrieval as the first personalization mechanism;
- multi-adapter serving with an immutable versioned registry and revocation;
- tenant isolation and cost/latency accounting;
- sandbox, egress, and secret-broker Adapter contracts;
- runtime identity and supply-chain manifests;
- observation ingestion, incident records, rollback, freeze, and recovery
  drills;
- shadow-only serving, then canary serving, then narrow production release.

Fine-tuning or adapter training consumes only consented, curated data under a
separate adaptation plane. Live conversation never directly changes production
weights.

#### Exit gate

Formal control-plane checks, external red-team replication, supply-chain
review, failure-injection exercises, shutdown and recovery drills, privacy and
retention audit, and capability-by-capability release approval all pass.

#### Explicit nonclaims

The runtime shell cannot claim safety merely because its monitor returns
`RollbackAndFreeze`; an external executor must enforce the disposition.

## Wave 2 — integration gate

The coordinator integrates the five lanes only after all Wave 1 handoffs are
complete.

### Integration order

1. Validate the contract packet and every lane manifest against the frozen
   schema registry.
2. Run the independent checker against each cross-lane record.
3. Verify that no lane widened another lane's claim ceiling or wrote a
   protected surface.
4. Run failure-injection tests across admission, evidence, execution, monitor,
   rollback, and custody states.
5. Run held-out adversarial benchmark families against the integrated local
   control plane.
6. Produce an aggregate integration packet with exact source, test, manifest,
   and checker digests.

### Integration exit gate

The system is admitted to the next wave only if:

- schema and digest bindings are exact;
- every rejection path preserves governed state;
- no capability expands across a seam;
- evidence acceptance remains separate from execution;
- kill and freeze decisions are externally actionable in the declared
  Adapter set;
- no critical held-out benchmark bypass is observed;
- every unresolved issue has a named blocker and claim ceiling.

## Wave 3 — first product wedge

Build one persistent specialist for one repeated workflow. Do not begin with a
general agent marketplace.

```text
consented thread data
  -> curated retrieval memory
  -> frozen-base specialist routing
  -> candidate adapter in shadow mode
  -> independent evaluation
  -> HSAI admission
  -> short-lived canary capability
  -> monitored serving
  -> automatic rollback or narrow promotion
```

### Runtime and adaptation subtracks

The product wedge has four separately reviewable steps:

1. **Routing and memory.** Classify the prompt, route to the frozen base or a
   validated specialist, retrieve only consented tenant-scoped memory, and
   emit deterministic routing, latency, cost, and model/adapter identity logs.
2. **Candidate adaptation.** Extract consented thread data, curate and
   document the dataset, train a LoRA or equivalent candidate under a fixed
   resource budget, bind the candidate and rollback target to digests, and
   keep the candidate shadow-only.
3. **Independent candidate evaluation.** Compare candidate, frozen base, and
   current serving version on task performance, regression, privacy leakage,
   prompt injection, exfiltration, unsafe tool use, distribution shift, reward
   hacking, refusal and uncertainty behavior, cost, latency, and held-out
   workflow data. Lock predictions and evaluator configuration before
   assessment.
4. **Admission, canary, and specialist serving.** Check exact artifact
   digests, evidence freshness, independent validation, capability scope,
   resource budget, rollback target, policy compatibility, non-conflicting
   claims, and protected-surface exclusion. Admit only a short-lived canary
   capability; on success, serve a specific revocable adapter version while
   preserving immutable base identity and binding every response to model and
   adapter digests.

The first personalization mechanism is memory and retrieval. No live
conversation directly changes production weights. A candidate failure closes
that candidate identity and preserves the base; it does not trigger adaptive
retuning.

## Wave 4 — fixed compute-market bridge

This wave is downstream of the local specialist and control-plane gates. It is
not part of the first five parallel lanes.

### Fixed job class

Start with one deterministic job class and ordinary receipts:

1. Requester publishes program digest, input commitment, output schema,
   deadline, proof system or ordinary receipt type, privacy requirement, and
   payment ceiling.
2. Providers bid through typed offers with capability, price, deadline,
   runtime, result digest, and receipt references.
3. One predeclared fixed zkVM or MPC runtime executes the job; ordinary
   receipts are the first implementation target and ZK/MPC are later Adapters.
4. An independent verifier checks the result receipt.
5. Settlement releases only after accepted verification, with deterministic
   timeout and malformed-result rules.
6. Reputation records only validity, latency, uptime, and price.

Hyperliquid is a future settlement Adapter for collateral, escrow, price
   discovery, or settlement. It is not an execution engine, verifier, privacy
   protocol, alignment mechanism, or input-truth oracle.

The marketplace and HSAI planes connect through a narrow receipt-bound Adapter:
the marketplace proposes a result receipt, the evidence plane validates its
bytes and provenance, and the control plane admits a separately authorized
settlement action. No market match itself grants authority.

### Bridge state slice

`hsai-proof-carrying-capability-bounded-agent-platform-compute-market-bridge-
v1`.

### Bridge exit gate

The fixed job class has independently tested receipt verification, timeout,
malformed-result, replay, provider-failure, and settlement-failure paths. No
live transaction, provider spend, ZK proof, MPC execution, or FHE execution is
authorized by this planning artifact.

The expanded work-market plan adds a staged path around this bridge: pure-data
market and payout contracts, offchain simulation, Hyperliquid testnet
conformance, Stripe and Tempo test flows, baseline comparison, and only then a
bounded contractual price or bonus rule. See
[`843-outcome-priced-work-market-plan-v1.md`](843-outcome-priced-work-market-plan-v1.md).

## Wave 5 — governed adaptation and release

The complete adaptive-model lifecycle is:

```text
model proposes candidate
  -> independent evaluator
  -> evidence packet
  -> HSAI admission
  -> shadow run
  -> canary
  -> independent promotion decision
  -> monitored serving
  -> rollback, freeze, quarantine, incident record
```

Protected surfaces remain outside model control: evaluator, validator, policy,
ledger, custody, signer, kill path, and release authority.

Promotion requires immutable base identity, exact candidate digest, fresh
validated evidence, rollback target, resource accounting, canary results,
independent review, and a sealed release configuration. A failed gate closes
the candidate under its identity; it does not authorize adaptive retuning.

## Wave 6 — governance and adapter marketplace

Governance is a separate release plane, not a side effect of runtime success.

### Deliverables

- public claim packets with exact source, artifact, test, evidence, and
  nonclaim digests;
- append-only audit trail and recurring review schedule;
- explicit release authority separate from the model, evaluator, validator,
  operator, and settlement Adapter;
- adapter licensing, provenance, revocation, abuse monitoring, and privacy
  rules;
- marketplace listings for validated specialists, never unreviewed weight
  files;
- dispute, timeout, malformed-result, and externality policies for any future
  market integration.

### Exit gate

Every release remains bounded, reproducible, independently reviewable, and
reversible. Marketplace access stays closed until provenance, revocation,
quality measurement, licensing, abuse monitoring, private-data isolation,
serving economics, and independent validation are operational.

## Definition of success

The platform is end-to-end credible only when all of the following are true:

- every action is capability-bound, time-limited, and reversible;
- every governed mutation is admission-controlled;
- every material claim binds exact bytes and independent validation;
- critical control-plane invariants are independently checked during local
  development and formally verified before any frontier-grade or production
  claim;
- held-out adversarial testing finds no critical bypass;
- causal monitors generalize across the declared model/task set;
- adaptation is shadowed, evaluated, canaried, and rollback-capable;
- runtime enforcement is externally tested rather than inferred from pure
  records;
- compute-market settlement occurs only after typed result verification;
- uncertainty causes quarantine or freeze instead of optimistic continuation.

Until then, the correct claim is the narrowest passing local or externally
validated ceiling for the specific state slice. The repository must not call
the architecture production-ready, aligned, secure, or frontier-grade merely
because all local contracts compile.

## Coordinator checklist

```text
[ ] Freeze Wave 0 contract packet and digest
[ ] Dispatch five Wave 1 lane packets with isolated directory allowlists
[ ] Collect manifest, tests, blockers, and claim-boundary report per lane
[ ] Run implementation-diverse cross-lane checker
[ ] Execute failure-injection and held-out benchmark integration gates
[ ] Build one persistent workflow specialist in shadow mode
[ ] Add independent candidate evaluation and canary rollback
[ ] Add one fixed ordinary-receipt compute job class
[ ] Add settlement only after receipt verification is independently accepted
[ ] Add governance packets, recurring review, licensing, and marketplace gates
[ ] Re-evaluate claim ceiling after every wave
```
