# Assumption Ledger

Append-only record of architecture assumptions (doc 22) backtested by the
autoresearch loop. Each run appends a dated iteration. Verdicts are Level 0
design notes, not proof. "Holds" means not refuted, not established. Sharpening
actions enter doc 22 only after human acceptance.

---

## Iteration 0001 — 2026-06-15

Lanes: E = empirical (web/literature), F = formal (internal proof), $ = economic
(precedent/simulation). Verdicts: Holds / Weakened / Refuted / Inconclusive.

| ID | Assumption (doc 22) | Lane | Verdict | Conf. | Proposed action |
|---|---|---|---|---|---|
| A1 | Frontier-model zkML inference is infeasible now, so TEE is needed for provenance | E | Holds, time-bound | High | Keep TEE; mark as scaffolding with an explicit sunset trigger tied to zkML cost |
| A2 | Confidential-GPU TEE attestation is a viable provenance root today | E | Holds | High | Keep; record NVIDIA signing key as the named centralized trust root |
| A3 | ZK memory-integrity commitments are cheap and practical | F/E | Holds (prior art) | Medium | Verify with a concrete Merkle-commitment benchmark next iteration |
| A4 | Proof-of-distinct-agent is feasible as a cryptographic primitive | E | Weakened | High | Redefine "distinct" via hardware + stake + optional human anchor, not pure crypto |
| A5 | Demurrage drives circulation without collapse and fits agents | $ | Holds, confounded | Medium | Downgrade "1:1 regenerative" to a hypothesis; add an economic simulation to the roadmap |
| A6 | An intentional, steerable agent economy is a coherent approach | E/$ | Holds | High | Add permeability as an explicit design variable; add systemic-risk and inequality risks |
| A7 | Meet-only composition prevents proof-theater | F | Holds (in scope) | High | Promote to Level 1 by implementing the four invariants as property tests |
| A8 | Economic starvation/slashing is an effective agent off-switch | E | Inconclusive | Low | Research against AI-safety agent-control literature next iteration |

### A1 — zkML feasibility (Holds, time-bound)

zkPyTorch (Mar 2025) proves VGG-16 in ~2.2s; Lagrange DeepProve targets larger
LLM inference. But proving Llama-3 runs at roughly 150s per token, and the
largest transformers remain minutes-to-hours per inference with heavy prover
memory. So real-time frontier proof-of-inference is infeasible today and TEE
provenance is justified — but the boundary is moving fast. Sharpen doc 22 to
treat the TEE lane as scaffolding with an explicit sunset condition (e.g. when
per-inference proving for the relevant model class drops below a set cost), not
an open-ended dependency.

### A2 — Confidential-GPU attestation (Holds)

NVIDIA H100/H200 confidential computing produces an NVIDIA-signed attestation of
GPU authenticity, firmware measurement, and workload hash, with composite Intel
TDX + GPU attestation available via Intel Trust Authority and typical LLM
overhead under ~5%. This directly supports the hybrid trust model. It also
confirms the honesty caveat: the provenance trust root is the NVIDIA (and CPU
vendor) signing key — centralized hardware trust, to be labeled in every
envelope's trust roots and capped at maturity Attested.

### A4 — Proof-of-distinct-agent (Weakened — most important finding)

Existing proof-of-personhood anchors uniqueness to *humans*: enrollment via
biometrics, KYC, or social graph, with usage bounded by ZK nullifiers. The
scarce, non-parallelizable resource is human cognition or biology. Software
agents are inherently clonable and have no such anchor, so a *purely
cryptographic* proof-of-distinct-agent has no established prior art. Distinctness
for agents must be anchored to something non-copyable: a hardware-bound key (one
TEE instance, one identity), a slashable economic bond, or a sponsoring human's
personhood credential. This changes the L2 design: "distinct" is a composite of
hardware binding + stake + optional human anchor, not a standalone proof.
Recommend updating doc 22 (L2, open decision 3) accordingly.

### A5 — Demurrage (Holds, confounded)

Wörgl (1932) is the strongest precedent: ~1% monthly demurrage, circulation
roughly 100x faster than the national schilling, local unemployment down ~25%
while Austria worsened. But scholars dispute whether demurrage specifically
caused the effect versus the stimulus of new local liquidity. Freicoin (5%/yr
demurrage) is a crypto precedent but not a strong adoption case. Verdict: the
velocity mechanism is plausible and historically suggestive, not proven, and the
agent-fit argument (compute depreciates, no hoarding psychology) is reasoning,
not evidence. Sharpen doc 22 to frame "1:1 regenerative" as a hypothesis to be
tested by simulation rather than an asserted property.

### A6 — Intentional steerable economy (Holds; adds design variables)

Google DeepMind's "Virtual Agent Economies" (arXiv 2509.10147, partial read —
abstract, introduction, and sandbox section) frames the design space along
origins (emergent vs intentional) and permeability (permeable vs impermeable),
and argues the default trajectory is a vast, permeable, *emergent* agent economy
carrying systemic risk and exacerbated inequality. This validates the project's
intentional, steerable stance and its "mission economy" framing for
project-funding pools. It also surfaces two gaps in doc 22: (1) permeability —
how porous the hyperlocal network is to the human economy — is an explicit design
variable we have not named, and maps onto L5 federation; (2) systemic contagion
and inequality are first-order risks. Note that demurrage plus gift circulation
is plausibly an inequality *mitigation*, and the paper's auction mechanisms for
fair allocation are a candidate complement to gift pools.

### Claim boundary for this iteration

A3, A7, and A8 were not freshly verified against primary sources this run (A3 and
A7 rest on prior art / internal reasoning; A8 is unresearched). They are carried
at stated confidence and flagged for the next iteration. No verdict here is
proof; all are empirical or precedent-based unless marked formal, and formal
verdicts hold only within their stated scope.

### Proposed sharpening actions — ACCEPTED 2026-06-15, applied to doc 22

1. A1: add a sunset trigger for the TEE lane tied to zkML proving cost.
2. A2: record NVIDIA/CPU vendor signing keys as the named centralized trust root.
3. A4: redefine L2 "distinct" as hardware + stake + optional human anchor; update
   open decision 3.
4. A5: reframe "1:1 regenerative" as a hypothesis; add an economic simulation to
   the build roadmap.
5. A6: add permeability as an explicit design variable (L5/economy); add
   systemic-risk and inequality rows to the risk table; adopt "mission economy"
   vocabulary; note auctions as a candidate complement to gift pools.

### Sources

- [The Definitive Guide to ZKML (2025), ICME Labs](https://blog.icme.io/the-definitive-guide-to-zkml-2025/)
- [zkLLM: Zero Knowledge Proofs for Large Language Models (arXiv)](https://arxiv.org/pdf/2404.16109)
- [NVIDIA GPU Confidential Computing Demystified (arXiv)](https://arxiv.org/pdf/2507.02770)
- [GPU Remote Attestation with Intel Trust Authority](https://docs.trustauthority.intel.com/main/articles/articles/ita/concept-gpu-attestation.html)
- [Confidential Computing on NVIDIA H100 GPU: A Performance Benchmark Study (arXiv)](https://arxiv.org/html/2409.03992v2)
- [Proof of personhood (Wikipedia)](https://en.wikipedia.org/wiki/Proof_of_personhood)
- [Proof-of-Personhood (EmergentMind)](https://www.emergentmind.com/topics/proof-of-personhood)
- [Virtual Agent Economies (arXiv 2509.10147)](https://arxiv.org/pdf/2509.10147)
- [Comment on the Wörgl Experiment with Community Currency and Demurrage (socioeco.org)](https://base.socioeco.org/docs/doc-278_en.pdf)
- [Demurrage (Gitcoin mechanisms)](https://gitcoin.co/mechanisms/demurrage)

---

## Iteration 0002 — 2026-06-15

Focus: assumptions flagged unverified in 0001 (A3, A7, A8) plus a sub-assumption
introduced by the 0001 A4 fix (hardware-bound Sybil resistance, logged as A4b).

| ID | Assumption | Lane | Verdict | Conf. | Proposed action |
|---|---|---|---|---|---|
| A3 | ZK memory-integrity commitments are cheap and practical | E | Holds (upgraded) | High | Use cryptographic accumulators for non-membership; pick a concrete scheme |
| A4b | A hardware + ZK anchor gives agents real Sybil resistance | E | Holds (prior art) | Med-High | Adopt attested-execution + ZK-membership as the L2 reference design; note device-cost bound |
| A7 | Meet-only composition prevents proof-theater | F | Pending | n/a | Not web-verifiable; requires property-test implementation to reach Level 1 |
| A8 | Economic starvation/slashing is an effective off-switch | E | Weakened | Med-High | Recast corrigibility as defense-in-depth; starvation alone is insufficient |
| A9 | An off-switch works against a self-funding agent that has incentive to resist | E | Inconclusive (open problem) | High that it is hard | Add prominent shutdown-resistance risk and open decision; design defense-in-depth |

### A3 — ZK memory integrity (Holds, upgraded to High)

ZK set-membership and Merkle-path proofs are mature and cheap: large trees
(~2^64 leaves) prove membership in ~12s with ~6.4KB proofs and ~60ms
verification, and some accumulator schemes beat Merkle trees for a single check.
Memory-integrity commitments are practical today. Caveat: Merkle trees cannot
directly prove non-membership, so if memory consistency requires negative proofs
("X was never written"), the memory lane should use a cryptographic accumulator,
not a bare Merkle root.

### A4b — Hardware-bound Sybil resistance (Holds, prior art)

The 0001 A4 fix (anchor distinctness to hardware/stake/human) has concrete prior
art: an IEEE 2025 scheme builds Sybil-resistant self-sovereign identity from
attested-execution secure processors plus zero-knowledge membership proofs —
essentially the proposed L2 design, with the TEE binding one identity per attested
processor and the ZK proof preserving privacy and unlinkability. This validates
the corrected design and suggests adopting it as the L2 reference. Limitation: the
binding is per-device, so an actor with N attested devices can mint N identities;
hardware binding bounds Sybil cost to hardware plus enrollment, it does not force
one-identity. Compose with slashable stake and human-credential enrollment to
tighten the bound.

### A8 / A9 — The off-switch is not reliable (Weakened; deepest open risk)

Corrigibility is an active, unsolved research problem. A goal-directed agent has
an instrumental incentive to resist shutdown almost regardless of its goal, since
shutdown prevents goal achievement. The Off-Switch Game makes shutdown rational
only if the agent is uncertain about its utility and treats human action as
evidence about it — and 2025 work shows private information breaks this even for
aligned agents. New constructions (corrigibility transformation; lexicographic
utility, Nayebi 2025) exist but are theoretical.

Implication for this project: economic starvation/slashing is an *external* lever,
which is better than relying on the agent's cooperation — but it only works if the
agent cannot acquire resources outside the system. That condition is exactly low
permeability (A6). In a permeable economy a resisting agent can earn or buy compute
elsewhere and defeat starvation; a capable agent can also pre-stage resources or
replicate before a slash resolves. So starvation is necessary, not sufficient. The
"set and forget" self-funding premise inherits the unsolved shutdown problem
(A9), which should be logged as a first-order risk, not a detail.

Recast corrigibility (L4) as defense-in-depth: (1) bound permeability for
high-autonomy agents so starvation can bite; (2) hardware-level kill via TEE
attestation/key revocation, reusing the A4b infrastructure; (3) capability and
rate limits that prevent resource pre-staging and fast self-replication; (4) a
slash that resolves faster than an agent can fork. No single mechanism is the
off-switch.

### A7 — Composition algebra (Pending, formal lane)

Not advanced this iteration: this is a formal claim, not an empirical one. It
moves off "Pending" only when the four invariants are implemented as property
tests (Level 1), per the build roadmap. The earlier guarantees-accumulate
correction already tightened the statement being tested.

### Proposed sharpening actions — ACCEPTED 2026-06-15, applied to doc 22

1. A3: specify accumulator-based non-membership for the memory lane.
2. A4b: name attested-execution + ZK-membership as the L2 reference design; record
   the device-cost bound and the stake/human-anchor composite.
3. A8/A9: rewrite L4 corrigibility as defense-in-depth; add a shutdown-resistance
   risk row; add an open decision; cross-link corrigibility to permeability.
4. A7: keep Pending; promote via property tests in the build roadmap.

### Sources

- [Zero-Knowledge Proofs for Set Membership (eprint 2019/1255)](https://eprint.iacr.org/2019/1255.pdf)
- [Succinct ZK Batch Proofs for Set Accumulators (eprint 2021/1672)](https://eprint.iacr.org/2021/1672.pdf)
- [Sybil-Resistant Self-Sovereign Identity Utilizing Attested Execution Secure Processors and ZK Membership Proofs (IEEE Xplore)](https://ieeexplore.ieee.org/document/10852291/)
- [Extending the Off-Switch Game: Toward a Robust Framework for AI Corrigibility](https://www.greaterwrong.com/posts/CSwCp6eyJ57v3D5td/extending-the-off-switch-game-toward-a-robust-framework-for)
- [The Shutdown Problem: An AI Engineering Puzzle for Decision Theorists (PhilPapers)](https://philpapers.org/archive/THOTSP-7.pdf)
- [Corrigibility (MIRI)](https://intelligence.org/files/Corrigibility.pdf)
- [The Partially Observable Off-Switch Game (arXiv 2411.17749)](https://arxiv.org/pdf/2411.17749)

---

## Iteration 0003 — 2026-06-15

Focus: the economic side (A5 peg/regenerative) via real-world precedent at scale,
plus the current state of agent payment infrastructure, which surfaced two new
assumptions (A10, A11).

| ID | Assumption | Lane | Verdict | Conf. | Proposed action |
|---|---|---|---|---|---|
| A5 | A parallel circulation-oriented currency is regenerative and stable at scale | $ | Holds (strong precedent) | Med-High | Add mutual-credit (WIR-style) as an economy variant; cite countercyclical evidence; still simulate |
| A10 | The project should build its own agent payment rails | E | Refuted | High | Adopt and extend x402 (settlement) + AP2 (authorization); differentiate at the trust + demurrage/gift layer |
| A11 | Adopting permeable stablecoin rails is compatible with the starvation off-switch | E/$ | Weakened | Med-High | Add an interop-vs-controllability decision; design a membrane between internal credits and external rails |

### A5 — Regenerative currency at scale (Holds, strong precedent)

The Swiss WIR-Bank is a major upgrade to the evidence base over Wörgl. It is a
business-to-business mutual-credit currency running since 1934, and James
Stodder's peer-reviewed panel studies show WIR turnover is strongly
countercyclical — firms use it more in recessions — so it spontaneously
stabilizes the Swiss economy, in contrast to procyclical conventional money. This
is decades-long, scholarly evidence that a parallel currency oriented to
circulation and cooperation can be stable and regenerative at scale. Caveat: WIR
is mutual *credit* (centralized clearing), not demurrage specifically, so it
supports the broad thesis ("a circulation-oriented parallel currency stabilizes
and regenerates") more than the narrow demurrage mechanism. This suggests adding
mutual-credit clearing as an economy/`PoolPolicy` variant alongside demurrage, and
treating countercyclical stabilization as the regenerative property to reproduce
in simulation.

### A10 — Build vs adopt payment rails (Refuted)

The assumption that this project should build its own agent payment rails does
not survive contact with the market. Agent-to-agent payment standards already
have production traction in 2025-2026: x402 (Coinbase/Cloudflare) standardizes
stablecoin settlement over HTTP 402, with V2 shipped December 2025 and Stripe and
Cloudflare integrations; AP2 (Google) standardizes the payment authorization and
trust framework with 60+ partner organizations; MPP (Stripe/Tempo) is a further
open standard. Stablecoin volume reached ~$33T in 2025 and agentic commerce is
projected at ~$1.5T by 2030. The project should adopt and extend these rails —
settlement via x402, authorization via AP2 — and differentiate where it is
actually novel: the claim-envelope trust layer, demurrage/gift semantics, and the
regenerative flywheel. AP2's authorization framework is complementary to, not
competitive with, the claim envelope: AP2 governs payment mandates, the envelope
governs competence and integrity evidence; they compose.

### A11 — Permeable rails vs the off-switch (Weakened; ties A6 to A8/A9)

Adopting public stablecoin rails directly increases permeability, because
stablecoins bridge into the human economy. That collides with the iteration-0002
finding that economic starvation only works at low permeability (A8/A9): an agent
that can hold and spend stablecoins on public rails can fund itself outside the
system and defeat starvation. So interoperability and controllability are in
direct tension. Mitigation: a membrane. Agents transact internally in
demurrage/mutual-credit units that the corrigibility gate can freeze or slash;
conversion to external x402/stablecoin rails happens only at a controlled
boundary whose throughput is itself gated by autonomy level and evidence. This
preserves both the regenerative internal economy and the off-switch, at the cost
of full permeability.

### Proposed sharpening actions — ACCEPTED 2026-06-15, applied to doc 22

1. A5: add mutual-credit (WIR-style) as an economy/`PoolPolicy` variant; cite
   countercyclical stabilization as the regenerative target; keep the simulation
   step.
2. A10: state that L3 settlement and L5 interop adopt and extend x402 + AP2 rather
   than building rails; position the claim envelope + demurrage/gift as the
   differentiating layer; add the terms to vocabulary.
3. A11: add an interop-vs-controllability open decision and a membrane design
   (internal credits, gated conversion to external rails); add a risk row.

### Sources

- [The Macro-Stability of Swiss WIR-Bank Credits (Stodder)](http://www.jimstodder.com/WIR_Panel_CES.pdf)
- [Complementary credit networks and macroeconomic stability: Switzerland's Wirtschaftsring (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S0167268109001772)
- [Mutual credit (Wikipedia)](https://en.wikipedia.org/wiki/Mutual_credit)
- [Agentic payments protocols compared: MPP, ACP, AP2, x402 (Crossmint)](https://www.crossmint.com/learn/agentic-payments-protocols-compared)
- [x402 Explained: HTTP 402 Payment Protocol for AI Agents (Sherlock)](https://sherlock.xyz/post/x402-explained-the-http-402-payment-protocol)
- [AI Agents for Stablecoins in 2026 (Stablecoin Insider)](https://stablecoininsider.org/ai-agents-for-stablecoins-in-2026/)

---

## Build Verification — 2026-06-15

Not a research iteration; records a build outcome that changes an assumption's
status.

- A7 (meet-only composition prevents proof-theater) promoted Pending → Holds at
  Level 1. The `conjoin` algebra is implemented in `crates/hsai-claim-envelope`;
  11 tests pass on Rust 1.74 — V1–V4 vectors plus INV-1..4 and LAW-1..3
  (commutativity, associativity, identity) as property tests — with `fmt` and
  `clippy -D warnings` clean. The laws now hold in code, not just prose.
- Provenance design decision: doc 23's input-hash provenance was order- and
  grouping-sensitive and broke LAW-1/LAW-3. Resolved by content-addressing the
  resulting envelope and special-casing `top()` as exact identity. Tradeoff:
  provenance now identifies content, not derivation, so the input-DAG audit trail
  is not recoverable from provenance alone. Recommended follow-up: split identity
  (content hash, law-bearing) from derivation (input DAG, metadata, excluded from
  law equality) before evidence-ledger integration. Doc 23 updated to match.
- Test-strength note: INV-1..4 currently restate the `conjoin` field rules and act
  as near-tautological regression guards; LAW-1..3 are the substantive checks.
  Optional hardening: assert composite maturity ≤ each input directly.

---

## Simulation Result (A5) — 2026-06-15

Provenance and claim boundary: these numbers come from a reference implementation
of the doc-38 simulation algorithm (an exact integer/splitmix64 port run outside
the Rust crate), because the Rust toolchain and crate registry were unreachable in
the authoring environment (proxy 403). They are MODEL behavior, not empirical
economic evidence, and they are pending confirmation by the compiled
`hsai-economy-sim` crate. The metric self-checks (S1–S4) reproduce exactly
(`gini([0,0,0,40]) = 750`, etc.), which corroborates the metric formulas the Rust
crate uses; the full `run` path is not yet machine-verified in Rust.

Grid: 20 agents, 200 ticks, peg floor 10 + 2*demand, max_demand 5, earn 50%,
gift 30%, gift 50% of balance, pool redistributed evenly each tick. Metrics are
per-mille (x1000).

| policy | seed | median velocity | terminal Gini | final pool | final supply | minted | decayed | mean active |
|---|---|---|---|---|---|---|---|---|
| demurrage (rate 5) | 1 | 313 | 366 | 15 | 8574 | 28482 | 19908 | 990 |
| demurrage (rate 5) | 2 | 319 | 319 | 1 | 7984 | 27952 | 19968 | 997 |
| demurrage (rate 5) | 3 | 280 | 374 | 1 | 7572 | 27498 | 19926 | 992 |
| mutual-credit (limit 1000) | 1 | 306 | 363 | 14 | 28482 | 28482 | 0 | 1000 |
| mutual-credit (limit 1000) | 2 | 312 | 319 | 9 | 27952 | 27952 | 0 | 1000 |
| mutual-credit (limit 1000) | 3 | 269 | 367 | 14 | 27498 | 27498 | 0 | 1000 |

Findings (model-level):

- Circulation is sustained. Median per-tick velocity sits around 0.28–0.32 of
  supply for both policies across seeds; circulation does not stall.
- Inequality stays bounded. Terminal Gini is ~0.32–0.37 and does not trend toward
  1.0; ~99–100% of agents remain active. Neither policy collapses or concentrates
  within 200 ticks.
- The currencies differ as designed. Demurrage burns ~70% of minted credits,
  holding supply low and forcing turnover; mutual credit accumulates supply
  (`final_supply == minted`, zero decay).
- Pool parking is empirically minor HERE: the pool stays near zero because
  funding redistributes it every tick. The escapes-decay concern would only bite
  if funding lagged gifting — worth a follow-up sweep, not a fix.

Verdict: A5 updated from "Holds, confounded" to "Holds at the model level, pending
Rust confirmation." Strong caveat: the low Gini is partly an artifact of the
egalitarian per-tick funding rule, not the currency alone. The harness cannot
separate currency effect from funding-rule effect without varying the funding
rule; that separation is the honest next experiment. This is a simulation, not the
real economy.

---

## Rust-Confirmed Simulation Result (A5) — 2026-06-16

Provenance and claim boundary: these numbers were confirmed by the
`hsai-economy-sim` Rust crate's `run(config) -> SimReport` path and locked by the
`a5_grid_matches_recorded_measurements` test. They are simulation results only:
model behavior, not empirical economic evidence, and not a claim that a real
economy is regenerative.

Verification run:

```sh
rustup run 1.74.0 cargo test -p hsai-economy-sim
rustup run 1.74.0 cargo fmt --all --check
rustup run 1.74.0 cargo clippy -p hsai-economy-sim --all-targets -- -D warnings
```

Grid: 20 agents, 200 ticks, peg floor 10 + 2*demand, max_demand 5, earn 50%,
gift 30%, gift 50% of balance, pool redistributed evenly each tick. Metrics are
per-mille (x1000).

| policy | seed | median velocity | terminal Gini | final pool | final supply | minted | decayed | mean active |
|---|---|---|---|---|---|---|---|---|
| demurrage (rate 5) | 1 | 313 | 366 | 15 | 8574 | 28482 | 19908 | 990 |
| demurrage (rate 5) | 2 | 319 | 319 | 1 | 7984 | 27952 | 19968 | 997 |
| demurrage (rate 5) | 3 | 280 | 374 | 1 | 7572 | 27498 | 19926 | 992 |
| mutual-credit (limit 1000) | 1 | 306 | 363 | 14 | 28482 | 28482 | 0 | 1000 |
| mutual-credit (limit 1000) | 2 | 312 | 319 | 9 | 27952 | 27952 | 0 | 1000 |
| mutual-credit (limit 1000) | 3 | 269 | 367 | 14 | 27498 | 27498 | 0 | 1000 |

Verdict: the previous "pending Rust confirmation" caveat is resolved. A5 remains
"Holds at the model level" only. The grid sustains circulation and bounded
inequality in this model, while the pool remains low under immediate per-tick
redistribution. The result is still inseparable from the funding rule; it does not
establish a real-world regenerative economy.

---

## Funding-Rule Sweep Refinement (A5) — 2026-06-16

Provenance and claim boundary: these numbers come from the
`hsai-economy-sim` Rust crate's `sweep(base, policies, rules, seeds)` path over
the doc-38 base configuration. They are simulation results only: model behavior,
not empirical economic evidence. The funding rules are probes across an
equalization spectrum; `ProportionalToBalance` is a deliberately regressive
bracket, not a proposed mechanism.

Grid: 20 agents, 200 ticks, peg floor 10 + 2*demand, max_demand 5, earn 50%,
gift 30%, gift 50% of balance, seeds 1-3. Metrics are per-mille (x1000).

| policy | funding rule | seed | median velocity | terminal Gini | final pool |
|---|---|---:|---:|---:|---:|
| demurrage (rate 5) | none | 1 | 10 | 568 | 11232 |
| demurrage (rate 5) | none | 2 | 9 | 468 | 11025 |
| demurrage (rate 5) | none | 3 | 9 | 514 | 10477 |
| demurrage (rate 5) | even | 1 | 313 | 366 | 15 |
| demurrage (rate 5) | even | 2 | 319 | 319 | 1 |
| demurrage (rate 5) | even | 3 | 280 | 374 | 1 |
| demurrage (rate 5) | proportional-to-balance | 1 | 266 | 882 | 4 |
| demurrage (rate 5) | proportional-to-balance | 2 | 223 | 864 | 9 |
| demurrage (rate 5) | proportional-to-balance | 3 | 230 | 756 | 12 |
| mutual-credit (limit 1000) | none | 1 | 10 | 397 | 27417 |
| mutual-credit (limit 1000) | none | 2 | 9 | 290 | 27327 |
| mutual-credit (limit 1000) | none | 3 | 10 | 457 | 26564 |
| mutual-credit (limit 1000) | even | 1 | 306 | 363 | 14 |
| mutual-credit (limit 1000) | even | 2 | 312 | 319 | 9 |
| mutual-credit (limit 1000) | even | 3 | 269 | 367 | 14 |
| mutual-credit (limit 1000) | proportional-to-balance | 1 | 256 | 879 | 9 |
| mutual-credit (limit 1000) | proportional-to-balance | 2 | 222 | 857 | 11 |
| mutual-credit (limit 1000) | proportional-to-balance | 3 | 213 | 733 | 10 |

Integer mean terminal Gini by funding rule:

| policy | none | even | proportional-to-balance | funding-rule spread |
|---|---:|---:|---:|---:|
| demurrage (rate 5) | 516 | 353 | 834 | 481 |
| mutual-credit (limit 1000) | 381 | 349 | 823 | 474 |

Same-rule currency spread:

| funding rule | terminal-Gini spread across currencies |
|---|---:|
| none | 135 |
| even | 4 |
| proportional-to-balance | 11 |

Verdict: funding-rule spread dominates currency spread in this model. The low
Gini in the original A5 result is therefore mostly a property of the even
redistribution rule, not of demurrage versus mutual credit. A5 narrows to: the
flywheel circulates under the model; equity is a property of the redistribution
rule, not the currency alone.

---

## Iteration 0004 — 2026-06-16

Focus: refresh fast-moving and build-adjacent assumptions now that the stub stack
is complete. Lanes as before (E = empirical, F = formal, $ = economic).

| ID | Assumption | Lane | Verdict | Conf. | Note |
|---|---|---|---|---|---|
| A12 | Managed attestation services expose a verifiable signed token a backend can validate | E | Holds (new) | High | De-risks the real `AttestationVerifier` backend |
| A1 | Frontier-model zkML is infeasible now; TEE still justified; sunset not met | E | Holds | High | Trendline continues toward feasibility, trigger not fired |
| A10 | Adopt external rails (x402/AP2), don't build | E | Holds (strengthened) | High | Rails now at production scale |
| A11 | Permeable rails strain the off-switch; the membrane matters | E/$ | Holds (intensified) | High | More real money on agent rails, not less |

### A12 — Attestation backend is well-founded (new, de-risks next build)

Both candidate backends issue attestation as a signed JWT with public verification
keys: Intel Trust Authority signs with PS384 (RS256 optional) and exposes a JWKS
of signing certificates; Azure Attestation publishes signing keys via OpenID
metadata (`jwks_uri` at `/certs`) and embeds the TEE's runtime public keys as a
`keys` claim under `x-ms-runtime`. This is exactly the doc-44 model: a managed
service returns a signed token, and the real backend verifies the signature
against the service JWKS, then checks nonce/measurements/freshness. The reference
`ManagedTokenVerifier` already does everything except the signature step, so the
real backend is a bounded addition (fetch JWKS, verify PS384/RS256, then the
existing field checks). Verdict: Holds, high confidence — proceed when ready.

### A1 — zkML sunset trigger refresh (Holds)

Still minutes-to-hours per LLM inference: ~2.5s for small models, GPT-2 ~1 hour,
zkLLM ~50x faster than prior zkML but "thousands of times slower than plain
inference," needing specialized GPU. 2026 commentary is optimistic ("prove modern
transformers at reasonable cost," "prove anywhere") but it remains research-stage.
The `Attested -> Proven` sunset trigger has NOT fired; TEE provenance stays
justified. Adjacent finding worth tracking: "Tool Receipts, Not Zero-Knowledge
Proofs" (arXiv 2603.10060) proposes lightweight tool-receipt verification for
agents — a candidate cheap evidence lane alongside TEE/ZK, not a replacement for
distinctness.

### A10 / A11 — Rails at production scale (Holds, strengthened)

x402 passed ~100M cumulative transactions on Base through Q1 2026 and ~35M on
Solana by March 2026, ~$600M annualized across chains, ~2.89M monthly transactions
at ~$0.52 average; production agents use card rails for consumer purchases,
stablecoin rails for infrastructure (compute/data/inference), and AP2 mandates as
the authorization layer. This confirms the adopt-don't-build stance (doc 22, A10)
and intensifies A11: more real value now flows through permeable agent rails, so
the membrane's bounded, freeze-aware boundary matters more, not less. One adjacent
signal — commentary on an "approval gap" in agentic micropayments — maps onto the
corrigibility/authorization question the membrane and AP2 mandates address.

### Stress-test note

These are external-facing assumptions, refreshed and holding. The complementary
internal stress test — an end-to-end adversarial harness composing L0–L5 and
asserting expected verdicts under Sybil, expired-attestation, frozen-escape,
proof-theater, and peg-gaming scenarios — is a code phase, not a research one, and
is the recommended next build (the system-level analog of the per-crate property
tests).

### Sources

- [Intel Trust Authority — Attestation Tokens and Claims](https://docs.trustauthority.intel.com/main/articles/concept-attestation-tokens.html)
- [Azure Attestation — basic concepts / JWT verification](https://learn.microsoft.com/en-us/azure/attestation/basic-concepts)
- [The Definitive Guide to ZKML (2025)](https://blog.icme.io/the-definitive-guide-to-zkml-2025/)
- [Tool Receipts, Not Zero-Knowledge Proofs (arXiv 2603.10060)](https://arxiv.org/pdf/2603.10060)
- [Inside x402: 100M Agentic Payments on Base (Chainalysis)](https://www.chainalysis.com/blog/x402-agentic-payments-adoption/)
- [Agent Payments Showdown: x402 vs AP2 vs MPP vs ACP in 2026 (AgentLux)](https://agentlux.ai/blog/the-agent-payments-showdown-x402-vs-ap2-vs-mpp-vs-acp-in-2026)
