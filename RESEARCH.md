# Research report and findings

This is the consolidated report for the whole repository. Longer treatments:
the paper *Evidence-Bounded AI* (`docs/research/evidence-bounded-ai/`, PDF in
`output/pdf/`), the Statebook whitepaper and PRD (`docs/statebook-*.md`), and
per-phase records under `docs/` and `docs/research/`. Every result below is
reported at its recorded **claim ceiling**; terminal negative results are kept
and published, not retuned.

## Thesis and method

Progress is measured in *claims*, and each claim is bound to an exact state
slice, a protocol, a custody identity, an independent validation path, and a
ceiling (Level 0 design note up to Level 6 independently reproduced). Models
may propose evidence; they cannot approve it, widen their own capabilities,
modify the evaluator, or promote an update. A benchmark pass is not a proof, a
local replay is not official benchmark evidence, and a recursion proof is not
semantic proof.

## Findings

### 1. Semantic benchmark OS (Level 1, local)
Semantic IR, oracle, deterministic generation across nine families, mutation
engine (all 14 mutation classes), local replay, evidence ledgers, pack readiness,
report bundles, audit indexes, soak runner with telemetry, and fail-closed
promotion and append mechanics. All of it is local deterministic infrastructure:
no official external benchmark, backend performance claim, or Level 2+ evidence
has been produced. A distinguishability matrix and an oracle-completeness audit
show which generated constructs the shipped oracle can and cannot evaluate.

### 2. HSAI gateway and formal-evidence ladder
- Gateway: a fourteen-case local demo gave one benign acceptance, thirteen unsafe
  rejections, zero false rejections, and fourteen recomputation agreements.
- Evidence ladder: candidate, review, handoff, policy, feasibility and
  eligibility metadata chains were built so that accepted formal evidence stays
  structurally blocked in the accepted-append path. This is a deliberate result:
  the system refuses to over-claim.
- One real local Z3 `unsat` path exists (a tiny digest-binding obligation) and a
  two-obligation mixed campaign. A production-preimage witness, an
  implementation-diverse checker (agreement on a golden vector, 18 mutations,
  opposite set orders, 256 generated cases), and a Lean kernel-checked theorem
  over a handwritten model of the checker exist, each at
  `Level1LocalReplayOrLower`. None proves the Rust source, SHA-256, or arbitrary
  input equivalence.
- Rust-to-Lean extraction with Aeneas was attempted across roughly 80 phases.
  Extraction itself ran, but no complete retained, kernel-checked extracted
  witness exists; the attempts ended in tooling, environment, or execution-
  protocol stops, each recorded and cleaned up. The lasting product was an
  execution state machine and a 102-command source ledger that make such
  attempts fail-closed and auditable. Finding: protocol discipline dominated
  cost; the formal result remained at the handwritten-model level.

### 3. Statebook (financial semantics, hermetic)
Exact P1 identity, bounded P2 payoff/residual engine, P3 seven completeness
reports, a P4 settlement simulator (hard gates, conservative valuation, budgets,
queue, circuit breakers, hysteresis, recovery), P5-P7 evidence adapters, source
import and authority preflight, and P8-P22 falsification corpora. All fixtures
are synthetic; there is no value movement, clearing, or live authority.

### 4. Mechanistic interpretability (Astral, Gemma 3)
- **Positive, narrow:** Gemma 3 V4 trace qualification passed (pooled NMSE
  0.0457 against a 0.05 gate; parity, repeat, no-op, intervention reach, event
  replay and feature stability passed). It is a model/runtime/asset-specific
  measurement qualification, not a causal-graph or introspection result.
- **Negative, terminal:** Gemma causal-feature-effects V2 (tune sign agreement
  0.75 < 0.80; one Holm gate failed; held-out never opened); Astral V42-V46 and
  V48 (target reliability, localization, measurement invariance,
  response-anchored and answer-aligned targets, cross-view transport) all ended
  `NoCandidate`; the
  program stopped rather than search more layers, wrappers or corpora.

### 5. Continual learning
- **BillSum LoRA curriculum (V2-V9):** V2/V3 stopped before model load
  (duplicate sources; tokenizer trailer), V4 hit its wall-clock limit, V5 ran out
  of MPS memory, V6 failed on an unexpected PEFT file, and **V7 completed**: local
  assurance `INTERNAL_PASS`, scientific disposition `NoCandidate` (the selected
  curriculum missed the selected-versus-random ROUGE-L gate).
- **Plasticity recovery (V1, V2):** `NoCandidate`; the mechanism family is closed.
- **Recursive update policy:** V1 rejected in review; V2 ran a 64-case synthetic
  campaign and ended `NoCandidate` (recursive selection lost to random).
- **Oak Lab V2:** four real panels, powered assessment (target power 0.8074),
  measured CPU energy, independent validation; no algorithm passed the strict
  gate. Oak Lab V3-V6 protocols were each rejected at independent review before
  any execution.
- **Gemma 3 recirculation / FineWeb H100:** earlier H100 identities were
  rejected at review; later work is gated on independent signed review.
- **Aligned holistic monitor (separate repo):** synthetic qualification only.

## Cross-cutting lessons

1. Terminal negative results are the main output; they were kept, not retuned.
2. Process and tooling failures (setup, identity binding, runtime pins) cost
   more phases than science failures; recording them as stops, not results,
   kept claims honest.
3. Fail-closed refusal to promote evidence is a feature: the accepted-evidence
   path is intentionally still blocked for formal and Level 2+ claims.
4. Narrow positive claims (Gemma V4 qualification, Lean-checked model theorem)
   are the right kind of claim; none was promoted beyond its ceiling.

## What this does not establish

No general alignment, introspection, causal self-modelling, benchmark
superiority, formal semantic correctness, security, or production readiness; no
independent replication; no live financial or settlement activity.

## Reproduce

```sh
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

Note: `repo_preserves_level1_hygiene_boundary` currently flags the presence of
`apps/desktop/package.json` (see Known issues). Several research lanes need
external custody (models, corpora, owner-only roots) and are not reproducible
from the repository alone.

## Known issues

- The hygiene test `repo_preserves_level1_hygiene_boundary` previously failed because `apps/desktop/package.json` is present. The test now allows that tracked desktop-shell manifest and skips the git-ignored `.weco` folder, and it passes.
- This repository's `AGENTS.md` forbids CI files and package scripts outside authorized slices, so no CI workflow is provided; run the commands above locally.
- The README is a very long implementation log; this report and the paper are the intended entry points.
