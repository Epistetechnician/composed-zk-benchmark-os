# Autoresearch Loop

## Purpose

A repeatable loop that continuously backtests the Hyper Sacred AI architecture
(doc 22) against current evidence, scores each assumption, and proposes
sharpening actions. The loop treats architecture assumptions the way the parent
project treats benchmark cases: each assumption is a falsifiable claim with an
expected verdict, routed to an evidence lane, scored, and bounded by an explicit
claim boundary.

## Claim Boundary

This loop produces Level 0 design notes only. A research verdict is not proof. A
"Holds" verdict means current evidence did not refute the assumption, not that it
is established. The loop only ever *proposes*; sharpening actions enter doc 22
only through the human acceptance step, mirroring the evidence-append proposal
(doc 19) and reviewed-proposal acceptance (doc 20) workflows. No loop output may
raise the maturity of any claim in doc 22 on its own.

## Loop Stages

1. Extract. Enumerate the falsifiable assumptions in doc 22. Each gets a stable
   ID (A1, A2, ...), a one-line claim, and the architecture decision it supports.
2. Formulate. Restate each assumption as a falsifiable claim plus the observation
   that would refute it.
3. Route. Assign each claim to a verification lane (below). Empirical claims go to
   web/literature; formal claims go to internal proof or property tests; economic
   claims go to historical precedent and simulation.
4. Gather. Collect current evidence with sources. Prefer primary sources (papers,
   benchmarks, specs) over commentary.
5. Score. Assign a verdict and a confidence, with the supporting evidence and its
   claim boundary.
6. Propose. For any Weakened or Refuted claim, draft a concrete sharpening action
   against doc 22 (edit, new open decision, build-order change, new risk row).
7. Accept. A human reviews proposals and accepts or rejects. Only accepted
   proposals edit doc 22. The ledger records both proposed and accepted state.

## Verification Lanes

Assumptions, like evidence, come in capability-scoped lanes. The lane determines
what a verdict can mean.

- Empirical lane: web and literature evidence on the state of the art. Can show
  feasibility trends and counterexamples; cannot prove a general claim.
- Formal lane: internal proofs and property tests (e.g. the composition algebra
  invariants). Can establish a claim within its stated scope; says nothing about
  empirical adoption.
- Economic lane: historical precedent, mechanism analysis, and simulation. Can
  show plausibility and failure modes; precedent is suggestive, often confounded.

## Verdict Vocabulary

Mirrors the oracle model (accept / reject / inconclusive):

- Holds: current evidence is consistent with the assumption.
- Weakened: evidence narrows the assumption's scope or raises a caveat.
- Refuted: evidence contradicts the assumption as stated.
- Inconclusive: evidence is missing or a capability gap prevents classification.

Each verdict carries a confidence (low / medium / high) and the lane that
produced it. A high-confidence Holds in the empirical lane is still not proof.

## Cadence

Run the loop on a schedule (proposed: weekly) and on demand after any major
edit to doc 22. Each run appends a dated iteration to the assumption ledger,
never overwriting prior iterations, so the trajectory of each assumption is
auditable over time.

## Outputs

- `assumption-ledger.md`: the living, append-only ledger of assumptions, verdicts,
  and proposed/accepted actions, one dated iteration per run.
- Proposed edits to doc 22, surfaced for human acceptance.
