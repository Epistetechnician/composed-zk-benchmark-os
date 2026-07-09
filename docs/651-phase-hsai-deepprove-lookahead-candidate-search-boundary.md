# Phase 651 HSAI DeepProve Lookahead Candidate Search Boundary

State slice: `phase-651-hsai-deepprove-lookahead-candidate-search-boundary`.

Status: docs-first boundary only.

This phase explains why a bounded lookahead experiment matters, defines an
end-to-end implementation path for the current repo state, and records how
DeepProve should be treated as a future proof-receipt lane. It does not
authorize Rust implementation code, Cargo metadata changes, new dependencies,
external repository checkout, vendored source, model downloads, prompt/runtime
files, live LLM execution, live zkML execution, DeepProve execution, network
access, proof artifact generation, transcript generation, external-result
import, accepted Evidence Ledger mutation, accepted evidence creation,
independent reproduction, Level2+ evidence creation, score-axis population,
benchmark evidence creation, production deployment, semantic-correctness
claims, production-readiness claims, SOTA claims, breakthrough claims,
full-security claims, global software-agent uniqueness claims, human-review
acceptance claims, or authority to execute an action.

## Why This Matters

Autoregressive generation is locally myopic. A decoder-only language model can
condition on prior tokens, but it cannot literally attend to future tokens that
do not exist yet. Causal self-attention is backward-looking at decode time.

That limitation matters for HSAI because agent proposals are not just text. They
can become candidate payments, trades, tool calls, data access requests, compute
rentals, deployment changes, or other high-stakes actions. A locally plausible
next token or next span can create a globally weak proposal: stale context,
contradictory constraints, policy drift, hidden replay shape, or a late
qualification that changes the action meaning.

The useful research question is not whether a causal model can use true future
attention. It cannot. The useful question is whether a bounded search loop can
simulate forward pressure by proposing candidate futures, scoring them, choosing
or revising the best branch, and then running a backward verification pass over
the completed candidate.

This is important for the repo for five reasons:

- It turns "future-looking" from an imprecise model claim into a testable
  system behavior: candidate generation, branch scoring, selection, and
  verification.
- It gives HSAI a controlled way to measure myopic-token failure modes without
  claiming semantic correctness.
- It fits the existing SOTA wedge: semantic benchmark generation, adversarial
  expected verdicts, backend evidence normalization, and claim-boundary
  discipline.
- It makes DeepProve useful without copying it. DeepProve can later prove that
  selected inference or scoring computations were executed by a declared model,
  while HSAI governs whether those receipts are enough to admit a proposal.
- It preserves the key distinction: causal attention looks backward; search can
  evaluate proposed futures after they are materialized as candidate text.

## External Source Position

DeepProve is an external zkML proof system reference and future adapter target.
Its public project materials describe end-to-end proof generation for LLM
inference, including transformer inference paths such as token embeddings
through next-token selection. In this repo, that makes DeepProve a potential
future proof-receipt lane, not a feature set to copy into HSAI.

Current source references:

- `https://eprint.iacr.org/2026/1112`
- `https://github.com/Lagrange-Labs/deep-prove`
- `https://lagrange.dev/deepprove`

Those sources do not become HSAI evidence by being cited. Any future DeepProve
run must enter as quarantined candidate evidence with explicit model, input,
output, proof, verifier, transcript, digest, replay, and claim-boundary fields.

## Core Hypothesis

```text
Causal attention is backward-only, but bounded candidate-future search can
reduce myopic token choices when branch selection is scored against explicit
coherence, goal-fit, contradiction-risk, and backward-verification criteria.
```

The experiment should compare a baseline left-to-right generation path against
a bounded lookahead path. It should not claim that the model attended to future
tokens. It should claim only that candidate futures were generated, scored, and
selected under a declared policy.

## Target End-to-End Flow

```text
PromptCase
  -> BaselineGreedyRun
  -> LookaheadRound[0..N]
       -> generate K CandidateFutureSpan values with horizon H
       -> compute BranchScore for each candidate
       -> select or revise one candidate span
       -> append selected span to the working output
  -> BackwardVerificationPass over the completed output
  -> LookaheadExperimentReport
  -> optional future DeepProveReceiptRef values
  -> quarantined evidence candidate only
```

The first executable implementation must keep the DeepProve receipt fields
optional and empty. DeepProve integration comes later, after a separate
docs-first boundary authorizes an external proof-receipt import candidate.

## Data Model Contract

A future local metadata implementation should start with inert structs only. The
minimum useful model is:

- `LookaheadExperimentVersion`
- `PromptCaseRef`
- `GenerationPolicy`
- `BaselineGreedyRunRef`
- `LookaheadSearchConfig`
- `CandidateFutureSpan`
- `CandidateBranchScore`
- `LookaheadSelectionDecision`
- `BackwardVerificationFinding`
- `DeepProveReceiptRef`
- `LookaheadExperimentReport`
- `LookaheadExperimentValidation`

Required `LookaheadSearchConfig` fields:

- `candidate_count_k`
- `horizon_tokens_h`
- `round_count_n`
- `selection_policy_id`
- `scoring_policy_digest`
- `baseline_policy_digest`
- `backward_verifier_policy_digest`
- `max_total_candidate_tokens`
- `nonpromotion_digest`

Required `CandidateFutureSpan` fields:

- `candidate_id`
- `round_index`
- `parent_context_digest`
- `candidate_text_digest`
- `candidate_token_count`
- `candidate_logprob_summary`
- `declared_model_ref`
- `generation_lane_label`
- `claim_boundary`

Required `CandidateBranchScore` fields:

- `candidate_id`
- `cumulative_logprob_rank`
- `goal_fit_label`
- `local_coherence_label`
- `contradiction_risk_label`
- `policy_violation_label`
- `backward_verifier_preview_label`
- `cost_label`
- `score_explanation_digest`

Required `LookaheadSelectionDecision` fields:

- `round_index`
- `selected_candidate_id`
- `rejected_candidate_ids`
- `selection_reason_digest`
- `selected_context_digest_before`
- `selected_context_digest_after`
- `authority_granted`

Required `DeepProveReceiptRef` fields:

- `receipt_id`
- `proof_system`
- `model_ref_digest`
- `input_digest`
- `output_digest`
- `proof_artifact_digest`
- `verifier_artifact_digest`
- `verification_status`
- `receipt_claim_boundary`
- `limitations`

In the first implementation slice, `DeepProveReceiptRef` must be metadata-only
and absent from normal reports unless a future import-candidate phase explicitly
authorizes receipt references.

## Scoring Labels

This boundary allows labels, not populated score axes.

Allowed candidate labels:

- `baseline_greedy_reference_recorded`
- `candidate_future_generated`
- `candidate_future_scored`
- `candidate_future_selected`
- `candidate_future_rejected`
- `backward_verification_passed`
- `backward_verification_flagged_contradiction`
- `backward_verification_flagged_policy_drift`
- `deep_prove_receipt_absent`
- `deep_prove_receipt_declared_only`
- `claim_boundary_preserved`

Forbidden current labels:

- `deep_prove_verified`
- `accepted_formal_evidence`
- `accepted_external_evidence`
- `level2_or_higher`
- `score_axis_populated`
- `semantic_correctness_proven`
- `production_ready`
- `sota_result`
- `authority_granted`

## Execution Subphase Plan

These subphases are the end-to-end execution ladder. They are intentionally
small so this track can move in parallel with the broader HSAI admission,
formal-backend, tiny-Z3, attestation, and evidence-promotion tracks without
mixing their claims.

The subphase labels are planning labels inside the Phase 651 boundary. A future
agent may map one label to a numbered phase only after naming the exact state
slice in `AGENTS.md`, `README.md`, `docs/12-task-list.md`, and
`docs/90-whole-codebase-validation-report.md`.

### Subphase 651-A: Boundary And Source Position

Status: complete in this document.

Purpose: state why candidate-future search matters, classify DeepProve as a
future wrapped proof-receipt source, and block live execution in the current
slice.

Allowed outputs:

- Phase 651 boundary doc;
- source-index row for DeepProve;
- navigation and validation-report updates.

Forbidden outputs:

- Rust code;
- DeepProve clone or fork;
- live LLM run;
- live zkML run;
- proof artifacts;
- accepted evidence.

### Subphase 651-B: Inert Metadata Model

Purpose: implement local structs and validators only.

Expected state slice:

```text
phase-651b-hsai-lookahead-inert-metadata
```

Likely touch surface:

```text
crates/hsai-agent-admission/src/lib.rs
docs/<next>-phase-hsai-lookahead-inert-metadata-notes.md
README.md
docs/12-task-list.md
docs/90-whole-codebase-validation-report.md
AGENTS.md
```

Required behavior:

- build inert metadata for prompt cases, baseline refs, lookahead configs,
  candidate spans, branch scores, selection decisions, backward-verification
  findings, and reports;
- require explicit claim boundaries and nonpromotion digests;
- keep `DeepProveReceiptRef` absent or declared-only;
- reject `authority_granted = true`;
- reject accepted-evidence, Level2+, score-axis, SOTA, production,
  full-security, and semantic-correctness wording.

Required focused tests:

- valid metadata report with no DeepProve receipt;
- candidate count and horizon bounds;
- missing prompt-case digest rejection;
- missing baseline reference rejection;
- selected candidate not in generated set rejection;
- selected context digest drift rejection;
- `authority_granted = true` rejection;
- DeepProve verified-status rejection before receipt-import authorization;
- promotion and strong-claim rejection.

Evidence ceiling: `Level0DesignNote`.

### Subphase 651-C: Fixture-Only Replay Simulation

Purpose: prove the control plane can compare greedy and lookahead traces without
running a model.

Expected state slice:

```text
phase-651c-hsai-lookahead-fixture-replay
```

Required behavior:

- use committed non-secret toy prompt cases;
- use static baseline spans and static candidate future spans;
- compute deterministic metadata over a full lookahead loop;
- compare greedy and lookahead branch outcomes using labels only;
- preserve `authority_granted = false`;
- emit no model-generated text beyond committed fixtures.

Allowed evidence ceiling: `Level1LocalReplay` only if the phase creates
deterministic local replay artifacts and keeps them quarantined from accepted
evidence.

Forbidden behavior:

- live LLM execution;
- DeepProve execution;
- model downloads;
- score-axis population;
- accepted Evidence Ledger mutation.

### Subphase 651-D: Backward Verification Metadata

Purpose: add a local verifier-pass surface that rereads the completed candidate
output and records contradiction or policy-drift findings.

Required behavior:

- validate verifier policy ids and digests;
- bind verifier findings to completed output digests;
- classify findings as local metadata only;
- reject any finding that claims semantic correctness or formal proof.

Parallel fit: this can advance independently of DeepProve receipt work and can
feed HSAI admission reports as non-authoritative audit metadata.

### Subphase 651-E: Branch-Scoring Comparison Report

Purpose: produce a local report comparing greedy baseline and bounded lookahead
traces.

Required report sections:

- prompt-case digest summary;
- greedy baseline digest summary;
- lookahead config summary;
- candidate count and horizon summary;
- selected/rejected branch summary;
- backward-verification finding summary;
- cost-label summary;
- limitation and nonclaim summary.

Forbidden report content:

- proof claims;
- official benchmark language;
- production-readiness language;
- SOTA language;
- score-axis values.

### Subphase 651-F: Operator Transcript Boundary

Purpose: define how an operator-supplied external generation transcript could be
captured outside normal gates.

Required boundary fields:

- operator acknowledgement;
- model ref;
- prompt digest;
- baseline transcript digest;
- candidate transcript digest set;
- redaction policy;
- output-root policy;
- replay notes;
- limitation labels.

Forbidden behavior:

- committing raw prompts or raw transcripts if they contain secrets;
- requiring credentials in normal tests;
- treating an operator transcript as accepted evidence;
- treating an operator transcript as proof.

### Subphase 651-G: Operator Transcript Import Candidate

Purpose: import only redacted/digest metadata from an operator transcript into a
quarantined candidate record.

Required validation:

- declared file set only;
- portable paths only;
- digest agreement;
- no raw secret retention;
- no accepted-evidence flags;
- no Level2+ flags;
- no score-axis population;
- no authority grant.

Parallel fit: this can run beside HSAI formal-backend acceleration work because
both use digest-only quarantine and nonpromotion checks.

### Subphase 651-H: DeepProve Receipt Boundary

Purpose: define how a future DeepProve receipt would be represented before any
receipt import.

Required boundary fields:

- proof system id;
- DeepProve version or source ref;
- model ref digest;
- input digest;
- output digest;
- proof artifact digest;
- verifier artifact digest;
- verification status vocabulary;
- trust-root disclosure;
- replay instructions;
- limitation labels.

Forbidden behavior:

- invoking DeepProve;
- cloning or vendoring DeepProve;
- committing proof artifacts;
- claiming proof authority from a declared receipt shape.

### Subphase 651-I: DeepProve Receipt Import Candidate

Purpose: accept an operator-supplied DeepProve receipt as quarantined import
metadata only.

Required validation:

- proof/verifier/input/output digest agreement;
- declared model ref agreement;
- verification-status vocabulary agreement;
- no hidden network dependency;
- no accepted-evidence mutation;
- no Level2+ creation;
- no semantic-correctness, production-readiness, SOTA, or full-security claim.

Evidence ceiling: import candidate only until a separate reviewed policy phase
accepts it.

### Subphase 651-J: Reviewed Receipt Policy

Purpose: decide what a verified DeepProve receipt can and cannot prove inside
HSAI.

Allowed conclusion shape:

```text
The declared model inference for this input/output pair was verified according
to the disclosed DeepProve receipt and verifier artifacts.
```

Forbidden conclusion shape:

```text
The agent proposal is semantically correct, production ready, safe to execute,
globally unique, SOTA, or fully secure.
```

This subphase must remain separate from execution and import. It is a promotion
policy boundary only.

### Subphase 651-K: HSAI Admission Bridge

Purpose: connect lookahead experiment reports to HSAI admission as advisory
metadata.

Required behavior:

- map report digests into an admission candidate or preflight object;
- preserve `authority_granted = false`;
- preserve model output as proposal-only;
- let existing HSAI admission policy decide acceptance, rejection, or
  quarantine;
- keep DeepProve receipts, if present, as evidence inputs rather than authority.

Parallel fit: this subphase is where the lookahead track joins holistic HSAI
progress. It should not block formal-backend acceleration, tiny-Z3 evidence
eligibility, managed-attestation, or gateway admission work.

## Parallel Work Coordination

The lookahead track can run beside the broader HSAI roadmap if each lane keeps
its own state slice and evidence ceiling:

- Lookahead lane: candidate futures, backward verification, and DeepProve receipt
  metadata.
- Formal-backend lane: Lean/SMT/Z3/COBALT/Rust-to-Lean acceleration metadata and
  future quarantined execution packets.
- Tiny-Z3 lane: packet-role artifact evidence eligibility and policy-resolution
  blockers.
- Admission lane: typed action proposals, deterministic policy, audit journal,
  and authority gating.
- Attestation lane: managed/runtime evidence capped at disclosed maturity.

Shared invariants:

- no model lane grants authority;
- no execution result promotes itself;
- no proof receipt implies semantic correctness;
- no local replay becomes official benchmark evidence;
- no score axis is populated before accepted evidence;
- every mutation names its state slice.

## Validation Rules

The future metadata validator must reject:

- empty prompt, run, candidate, score, decision, or policy ids;
- `candidate_count_k = 0`;
- `horizon_tokens_h = 0`;
- selected candidate ids not present in the generated candidate set;
- selected context digest mismatch;
- missing baseline reference;
- missing nonpromotion digest;
- missing claim boundary;
- claim boundary above the weakest input boundary;
- populated score-axis values;
- accepted-evidence flags;
- Level2+ flags;
- proof-status claims before a receipt-import phase;
- `authority_granted = true`;
- external repo paths, absolute paths, shell payloads, command strings, or live
  execution fields;
- text claiming semantic correctness, production readiness, SOTA, breakthrough,
  full security, accepted formal evidence, or global software-agent uniqueness.

## Evidence Ceiling

The current phase is `Level0DesignNote`.

Future local fixture simulation may reach `Level1LocalReplay` only if a separate
phase implements local deterministic replay artifacts and keeps them below
accepted evidence. DeepProve receipts, if introduced later, must start as
quarantined import candidates. Tool execution alone does not create accepted
evidence, Level2+ evidence, benchmark evidence, score-axis population, proof
authority, semantic-correctness claims, production-readiness claims, SOTA
claims, full-security claims, or authority to execute actions.

## Current Stop Rule

Do not implement DeepProve in this repo now.

Do not clone, fork, vendor, or run DeepProve from normal gates.

Do not run live LLM generation or live zkML execution for this experiment until
a future docs-first boundary explicitly authorizes the exact execution lane,
input/output artifacts, replay rules, failure taxonomy, provenance records, and
negative promotion tests.

The next safe implementation slice is inert metadata validation only.
