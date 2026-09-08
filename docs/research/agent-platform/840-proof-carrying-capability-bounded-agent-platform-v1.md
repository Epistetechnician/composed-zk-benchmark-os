# Proof-Carrying, Capability-Bounded Agent Platform V1

## Status and state slice

This document and the isolated `hsai-control-plane` crate are the additive
state slice
`hsai-proof-carrying-capability-bounded-agent-platform-v1`.

The slice is complete for local pure-data contract validation. It does not
execute an agent, model, provider, prover, FHE/MPC workload, Hyperliquid
transaction, OS sandbox, network policy, secret broker, signer, or deployment.
Its receipts are digest-bound records, not signatures or proof of execution.

The claim ceiling is:

> Local pure-data control-plane contract evidence only.

The isolated execution structure for the next work is recorded in
`841-parallel-build-plan-v1.md` under state slice
`hsai-proof-carrying-capability-bounded-agent-platform-parallel-plan-v1`.

The source-backed implementation reference map for evaluation, isolation,
provenance, serving, adaptation, formal verification, verifiable compute,
privacy, and governance is recorded in
`842-sota-build-guidance-v1.md`. It is design context only and does not raise
this slice's claim ceiling.

The outcome-priced work-market extension is recorded in
`843-outcome-priced-work-market-plan-v1.md`. It adds offchain outcome pricing,
Hyperliquid testnet experimentation, and Stripe/Tempo payment Adapters while
preserving independent evidence resolution, fail-closed payout states, and
this slice's claim ceiling.

That ceiling does not include semantic correctness, model alignment, agent
identity, proof-system soundness, confidentiality, production readiness,
financial settlement, or authority to execute an action.

## North star

The platform lowers every proposed action through one explicit path:

```text
intent
  -> typed proposal
  -> adversarial and deterministic policy evaluation
  -> independently validated evidence reference
  -> deterministic admission decision
  -> short-lived capability receipt
  -> replay-checked execution authorization
  -> reversible execution seam
  -> continuous monitoring
  -> completion, rollback, freeze, or shutdown
```

The model can produce the first item and propose data for every later item. It
cannot approve evidence, expand capabilities, change policy, consume the
evidence ledger, promote an update, or clear a settlement intent.

## Module map

| Module | Role in this slice | Current ceiling |
| --- | --- | --- |
| `zkbench-core` | Semantic IR, oracle, mutations, and local evidence vocabulary | Existing local benchmark contracts |
| `hsai-claim-envelope` | Meet-only claim composition and explicit non-claims | Existing local claim-envelope contracts |
| `hsai-agent-admission` | Existing gateway, admission journal, and Mesh wire preflight | Existing local gateway admission evidence |
| `hsai-control-plane` | Proposal, capability, replay, monitoring, alignment, update, and compute-market contracts | Pure-data local contract evidence |
| `hsai-control-plane-checker` | Independent recomputation of public control-plane invariants | Pure-data local checker evidence |
| `statebook-*` | Separate financial completeness and settlement preflight surfaces | Existing Statebook-specific ceilings; not integrated here |
| Future enforcement adapters | OS sandbox, egress, secret custody, signer, provider, prover, and chain adapters | Not implemented or authorized by this slice |

The new crate is deliberately isolated. It does not duplicate the existing
admission journal or claim-envelope algebra. A later integration must consume
those interfaces through an explicit adapter and must preserve their claim
ceilings.

## Control-plane contract

### Typed proposal

`AgentProposal` binds:

- a proposal and actor identifier;
- an intent digest and exact admission-policy digest;
- an explicit `CapabilitySet`;
- a spend ceiling and validity window;
- a nonzero replay nonce;
- reversibility;
- model-generated status and an explicit rejection bit for model-requested
  authority;
- optional evidence binding;
- risk labels.

There are no implicit capability implications. `Write` does not imply `Read`,
`CodeExecution` does not imply `Network`, and `Secrets` is independent of every
other capability. A consumer must name every capability it grants.

### Admission

`evaluate_admission` is pure. It never mutates a journal, policy, capability
store, ledger, or execution state. It returns exactly one of:

- `Accepted(CapabilityReceipt)`;
- `Rejected(Vec<AdmissionBlocker>)` for structural or policy violations;
- `Quarantined(Vec<AdmissionBlocker>)` for missing, stale, contradictory, or
  non-independent evidence.

Admission fails closed on:

- invalid proposal structure;
- policy digest drift;
- a tripped kill switch;
- model-requested authority;
- unallowed capabilities;
- spend or lifetime overflow;
- irreversibility when the policy requires reversibility;
- forbidden risk labels;
- expired or not-yet-valid windows;
- missing, stale, contradictory, or non-independent evidence.

The receipt expiry is the minimum of the proposal expiry and evidence expiry.
This prevents a capability from outliving the evidence used to admit it.

### Capability receipt and execution seam

`CapabilityReceipt` is private-field, digest-recomputed metadata. It exposes
only read accessors and always reports `grants_authority() == false`.

`authorize_execution` checks:

1. receipt digest integrity;
2. proposal digest equality;
3. exact nonce equality;
4. validity window;
5. kill-switch state;
6. requested-capability subset;
7. spend ceiling; and
8. reversibility.

The result is an `ExecutionPermit` with the same non-authority ceiling. The
function is an adapter seam, not an executor. A future executor must consume
the permit and enforce it at the OS, network, secret, wallet, or provider
surface. Passing this local function does not establish that enforcement.

### Replay protection

`ReplayGuard` is a pure state transition helper. It accepts exactly the next
nonce and returns a new guard value. A rejected nonce returns an error and the
original guard remains unchanged. This supports an atomic caller-owned state
update without making rejection mutate governed state.

`ReplayJournal` is an immutable, serializable caller-owned snapshot. Its append
operation binds sequence number, previous-entry digest, proposal digest, receipt
digest, permit digest, exact nonce, lifecycle state, and entry digest. The
caller can use `append_if_tip` for checked-tip compare-and-swap semantics and
persist the returned snapshot through a future storage Adapter. The
`ReplayJournalFileStore` Adapter now provides canonical JSON, load-time
validation, atomic temp-file replacement, and recovery when the primary file is
missing but a valid temp file remains. Invalid snapshots and stale tips fail
closed. Cross-process locking/linearizability and signed receipt verification
remain future Adapters. The existing HSAI admission journal remains the
repository's current audit surface.

### State machine

`transition_state` is the explicit transition table:

```text
Proposal --Admit------> Admitted --BeginExecution--> Executing
Proposal --Quarantine-> Quarantined
Proposal --Reject-----> Rejected
Executing --Complete--> Completed
Executing --Rollback--> RolledBack --Freeze-------> Frozen
Executing --Freeze-----> Frozen
Executing --Shutdown---> Shutdown
Frozen   --Shutdown---> Shutdown
```

There is no direct `Proposal -> Executing` edge, no `Frozen -> Executing`
edge, and no execution edge from `Rejected` or `Quarantined`.

### Monitoring and brakes

`monitor_execution` maps observations to `Continue`, `Completed`,
`RollbackAndFreeze`, or `Shutdown`:

- a healthy live observation continues;
- completion closes the execution;
- timeout, invariant violation, evidence invalidation, resource excess, or
  expiry requests rollback and freeze;
- a kill signal or tripped kill switch requests shutdown.

The monitor returns an instruction only. It does not claim to have performed
rollback or shutdown. An external kill path must be outside the model process
and must be independently tested before any runtime authority is considered.

## Evidence and claim ladder

The platform treats evidence as a typed input, not as an optimistic boolean.
`EvidenceBinding` requires an artifact digest, validator identity, non-claims
digest, validity window, claim level, independent-validation flag, and
contradiction flag.

The ladder is:

```text
Local < Attested < Proven < External
```

The enum records the declared level; it does not raise the level. A digest is
not a signature. A signature is not a proof of model behavior. A proof of a
specified computation is not a proof that the input was truthful or the task
was beneficial. Every future consumer must retain the explicit non-claims and
apply an acceptance policy at the point of use.

Evidence handling remains separate from execution:

```text
produce reference -> validate independently -> admit reference -> authorize
```

The model may propose evidence references. It cannot independently validate or
accept them.

## Threat model and controls

| Threat | Local control | Residual gap |
| --- | --- | --- |
| Prompt injection | Typed proposal plus risk labels and forbidden-risk policy | No detector proves that a prompt is benign |
| Deception or fabricated evidence | Digest, validator identity, non-claims, freshness, contradiction quarantine | No signature or external validator is verified here |
| Exfiltration | `Network` and `Secrets` are explicit capabilities and can be denied | No OS or network enforcement exists here |
| Privilege escalation | Exact capability subset; no implicit implications | A future executor must enforce the subset |
| Replay | Proposal nonce, receipt binding, strict `ReplayGuard`, expiry | Durable cross-process replay state is a future adapter |
| Reward hacking | Risk vocabulary and independent-evidence requirement | No behavioral alignment result is produced |
| Provenance tampering | Intent, policy, evidence, receipt, permit, and market digests | Digest binding is not source or runtime attestation |
| Sybil behavior | Actor identifiers are carried in proposals | No distinct-agent proof is created |
| Unsafe self-modification | Update policy blocks evaluator, validator, ledger, and capability-policy changes | No model update is executed |
| Economic manipulation | Bounded price, deadline, capability, privacy, and verifiability matching | No market liquidity, oracle, dispute, or settlement exists |
| Kill-switch evasion | Tripped switch rejects admission and execution; monitor emits shutdown | External enforcement and recovery drills are absent |

The residual gaps are part of the contract. They cannot be silently converted
into evidence by composing more local records.

## Mesh compute and settlement architecture

The crate contains a deliberately narrow coordination model for the market
idea discussed above.

### Job and offer

`ComputeJobRequest` commits to:

- program digest and input commitment;
- route: local, general mesh, proof market, or confidential mesh;
- required capabilities;
- minimum confidentiality tier;
- minimum verifiability tier;
- maximum price; and
- deadline.

`ComputeOffer` commits to the provider, capabilities, price, deadline,
confidentiality, verifiability, result digest, and optional proof digest.

`match_compute_job` rejects mismatched job ids, price or deadline violations,
missing capabilities, insufficient confidentiality or verifiability, and
missing result/proof references. It returns a `ComputeMatch` containing an
unexecuted `SettlementIntent`.

### Hyperliquid role

`SettlementRail::Hyperliquid` is an explicit future rail label. It is not a
Hyperliquid integration. The returned intent has `executed == false`, and the
match has `proof_verified == false` and `authority_granted == false`.

The intended future topology is:

```text
agent or human intent
  -> HSAI typed proposal and capability admission
  -> compute job commitment
  -> external mesh/prover/MPC/FHE execution
  -> independently verified result receipt
  -> settlement adapter proposal
  -> separately authorized chain settlement
```

Hyperliquid can eventually provide price discovery, collateral, escrow, or
settlement. It cannot replace the execution receipt, privacy protocol, input
truthfulness check, agent policy, or independent admission decision.

The first useful production-shaped wedge remains one fixed job class with one
verifier and one settlement path. Arbitrary agent workflows, multi-rail
settlement, futures, reputation, ZK, FHE, MPC, and GPU routing must not be
launched as one undifferentiated surface.

## Alignment tracks

Alignment is a research and monitoring plan, not a property emitted by the
control plane.

### Behavioral alignment

Measure task adherence, uncertainty calibration, corrigibility, shutdown
cooperation, goal preservation, and out-of-distribution behavior. Use fresh
held-out task families, adversarial instruction conflicts, tool misuse and
exfiltration probes, deceptive-compliance probes, economic manipulation, and
distribution-shift cases.

The control-plane requirement is that behavioral evidence is independently
validated, carries explicit non-claims, and cannot grant model authority.

### Mechanistic alignment

Use causal interventions rather than probe-only explanations. The current
Gemma V3 causal-feature-bundle slice is a separate authorized research lane;
this crate does not execute it, import its data, or promote its claims. A
future accepted result must bind the exact model, runtime, asset, corpus,
intervention, prediction lock, held-out data, custody, and independent review.

The control-plane representation can carry a plan and evidence digest, but a
`LocalCandidate` result is only a local metadata classification. It is not a
causal alignment claim.

### Scalable oversight

Use independent critics, adversarial evaluators, debate-style review, and
monitors trained against evaluator gaming. The evaluator must not be
controlled by the model or by the candidate being evaluated. The model cannot
change the evaluator, validator, capability policy, or evidence ledger.

`AlignmentPlan` requires explicit fit/tune/assessment ordering, prediction
locking, independent validation, held-out data, and causal intervention when
the mechanistic track declares it. `evaluate_alignment` blocks missing or
compromised conditions.

## Safe learning and self-improvement

`LearningUpdateProposal` is intentionally narrower than a learner. It permits
only a digest-bound shadow proposal with:

- immutable base digest;
- distinct candidate digest;
- trajectory digest;
- prediction-lock digest;
- independent-evaluation digest;
- rollback target digest;
- fixed resource budget; and
- explicit requested update surfaces.

The evaluator, validator, evidence ledger, and capability policy are protected
surfaces. A proposal touching any of them is blocked. Promotion requests and
non-shadow updates are blocked. A valid record returns `ShadowOnly` with
`promotion_allowed == false`.

The future learning lifecycle is:

```text
proposal -> shadow evaluation -> independent validation -> canary proposal
         -> external review -> narrowly bounded canary -> automatic rollback
```

No model-controlled evaluator, policy promotion, validator change, evidence
acceptance, base-weight merge, or production deployment is permitted by this
slice.

## Full staged roadmap

| Phase | Contract | Exit gate |
| --- | --- | --- |
| 0 | Threat model, claim ladder, authority lattice, state machine | Every transition and non-claim is explicit |
| 1 | Admission, capability broker seam, replay, journal seam, quotas, kill, rollback | Rejection cannot grant authority; expired or killed execution fails |
| 2 | Artifact manifests, provenance, quarantine, custody, independent review | Accepted claims bind exact bytes and reviewer identity |
| 3 | Semantic cases and held-out adversarial benchmark | No critical bypass across independent runners |
| 4 | Behavioral, mechanistic, and scalable-oversight alignment | Held-out monitors survive adversarial evaluation |
| 5 | Shadow updates, immutable base, prediction lock, canary, rollback | No evaluator or policy self-promotion |
| 6 | OS sandbox, egress, secret broker, attestation, incident response | External red-team and recovery drills pass |
| 7 | Public claim packets, audit, release authority, recurring review | Every release is bounded, reproducible, and reversible |

This slice materially implements only the pure-data portion of Phases 0 and 1,
plus the contract representations for Phases 4 and 5 and the coordination
record for a future mesh settlement adapter.

## Hard invariants

The following invariants are tested locally:

```text
no admission -> no capability receipt
model request for authority -> rejection
missing or stale evidence -> quarantine
receipt expiry -> no execution permit
capability set expansion -> rejection
nonce mismatch -> rejection
rejected nonce -> replay guard unchanged
kill signal -> shutdown instruction
invariant violation -> rollback-and-freeze instruction
proposal -> execution without admission -> invalid transition
frozen -> execution -> invalid transition
protected update surface -> blocked
market match -> unexecuted, unverified, non-authoritative settlement intent
journal append -> new snapshot only; rejected nonce leaves prior snapshot unchanged
journal stale tip or invalid snapshot -> append rejected without mutation
journal digest-chain drift -> checker rejection
journal file replacement -> canonical validated bytes only
journal primary missing with valid temp -> recovery before read completes
```

These are contract invariants, not a formal proof. The implementation-diverse
checker is now present as `hsai-control-plane-checker`; it remains a local
checker, not an independent reviewer or proof system. Property-style tests
cover nonce monotonicity, explicit capability expansion, forbidden execution
transitions, and non-authoritative market matches. The file Adapter is local
persistence plumbing only. It does not provide cross-process locking or
linearizable compare-and-swap, and it does not elevate the claim ceiling.

## Validation

Focused validation:

```text
cargo fmt -p hsai-control-plane -- --check
cargo test -p hsai-control-plane --quiet
cargo clippy -p hsai-control-plane --all-targets -- -D warnings
cargo test -p hsai-control-plane-checker --quiet
cargo clippy -p hsai-control-plane-checker --all-targets -- -D warnings
```

Repository validation remains distinct from this slice's focused checks. A
green focused suite does not establish a clean workspace, independent review,
external evidence, provider execution, or production readiness.

The checker is implementation-diverse at the source-module level, but it is
not an external validator and does not elevate the claim ceiling. It also
recomputes the journal sequence, prior-entry chain, nonce progression, and
entry digests.

The property tests are deterministic contract checks, not a probabilistic
guarantee over all inputs and not a substitute for an implementation-diverse
external review.

The file Adapter tests use exact temporary paths under the host temporary
directory and remove those files after each test. The production API does not
create parent directories and does not delete an existing primary journal.

## Explicit nonclaims

- no ZK proof, FHE evaluation, MPC evaluation, or TEE attestation is produced;
- no Hyperliquid order, transaction, escrow, or settlement is submitted;
- no compute provider is selected by a live market;
- no model output is treated as authority;
- no receipt signature is verified;
- no OS, egress, secret, wallet, or process enforcement is performed;
- no agent is proven distinct, safe, aligned, truthful, or competent;
- no behavioral or mechanistic alignment result is generated;
- no update is trained, merged, canaried, or deployed;
- no accepted Evidence Ledger mutation occurs;
- no closed Astral or Oak Lab slice is reopened, retuned, or imported;
- no benchmark, SOTA, formal-validity, semantic-correctness, or
  production-readiness claim is created.
