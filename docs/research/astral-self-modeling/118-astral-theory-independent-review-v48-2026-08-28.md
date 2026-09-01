# Astral theory independent review receipt — V48 post-stop audit

state_slice: astral-literature-coverage-theory-audit-independent-review-v48-2026-08-28

reviewed_memo_path: docs/research/astral-self-modeling/116-astral-literature-coverage-and-theory-audit-v48.md

reviewed_memo_sha256: c3dfbea483efc6d8e46cd38dfb59da14be4e9a5f94a38562a6054eed5690a412

reviewer_role: independent scientific review worker

verdict: REJECT

execution_authorized: false

review_date: 2026-08-28

final_authorization_status: Astral experimentation terminated after V48

## Scope and input boundary

This receipt is an independent review of the frozen theory packet. The local
scientific inputs were exactly:

1. `docs/research/astral-self-modeling/116-astral-literature-coverage-and-theory-audit-v48.md`
2. `docs/research/astral-self-modeling/06-literature-index.md`
3. `docs/research/astral-self-modeling/112-astral-cumulative-evidence-synthesis-stop-v48.md`
4. `docs/research/astral-self-modeling/astral-theory-docket-v48-closed.md`

The file
`docs/research/astral-self-modeling/117-astral-theory-review-packet-v48.md`
was used only as an administrative digest reference and was not treated as a
scientific input. No V48 raw output, model file, implementation file,
measurement output, experiment, or unrelated repository artifact was used.
The primary-source URLs cited by the audit were consulted only for literature
claim verification.

## Packet digest verification

The four SHA-256 values were independently recomputed and all matched the
administrative packet manifest:

| File | Manifest SHA-256 | Recomputed SHA-256 | Result |
|---|---|---|---|
| `116-astral-literature-coverage-and-theory-audit-v48.md` | `c3dfbea483efc6d8e46cd38dfb59da14be4e9a5f94a38562a6054eed5690a412` | `c3dfbea483efc6d8e46cd38dfb59da14be4e9a5f94a38562a6054eed5690a412` | `PASS` |
| `06-literature-index.md` | `8aee6cb1e1bb49bbc4002533fa7bf6da8e6083d7a1ff71224820b2018fb86cf8` | `8aee6cb1e1bb49bbc4002533fa7bf6da8e6083d7a1ff71224820b2018fb86cf8` | `PASS` |
| `112-astral-cumulative-evidence-synthesis-stop-v48.md` | `26b191ba424eac4201e3260cdb9081648f1889dad69185df2442ff19a72febd7` | `26b191ba424eac4201e3260cdb9081648f1889dad69185df2442ff19a72febd7` | `PASS` |
| `astral-theory-docket-v48-closed.md` | `18816aab4f6727a2535e9905b3135bc85db88ca961a60404c31efdd59fd37d34` | `18816aab4f6727a2535e9905b3135bc85db88ca961a60404c31efdd59fd37d34` | `PASS` |

Packet custody therefore passes. Custody success does not imply theory
acceptance.

## Findings

### 1. Six coverage classifications

The six classifications are internally coherent and supported by the packet:

- causal abstraction/interchange: partial analogue;
- J-space/global workspace: untested;
- circuit tracing/cross-layer transcoders: untested as accepted Astral
  evidence;
- dynamical systems/observability: untested in the Astral causal lane;
- identifiable causal representation learning: untested, with V48 only a
  related diagnostic; and
- introspection falsification: partial analogue without complete replication.

This finding passes. The classifications are appropriately narrower than
scientific confirmation.

### 2. Source accuracy and literature limitations

The cited source summaries are materially accurate at the abstract/method
level. The causal-abstraction source formalizes graded faithfulness and
unifies intervention-based interpretability methods. The circuit-tracing
source describes an interpretable replacement model and perturbational
validation while acknowledging approximation and coverage limitations. The
J-space, dynamics, identifiable-representation, and introspection sources are
correctly presented as model- or assumption-specific and not as Astral
evidence.

This finding is only partial. The literature index explicitly identifies itself
as a seed index rather than a systematic review, and it does not record the
databases, queries, inclusion criteria, exclusion criteria, and feature-level
prior-work matrix required by its own novelty-review rule. Because the packet
claims a reopening rationale rather than merely a bibliography, this omission
prevents a complete novelty and source audit.

### 3. Causal novelty relative to V46 and V48

The proposed direction is conceptually distinct: V46 and V48 predicted or
transported model-internal effects, whereas the proposed score compares
held-out original-model intervention effects with corresponding
abstract/replacement-model interchange effects. This is a plausible new
estimand family and is not merely a layer or wrapper variation.

The distinction is not yet operationally sealed. The memo does not define the
high-level causal variables, the abstraction mapping, the allowed interchange
assignments, or the relationship between graph construction and the original
model's mechanisms. The novelty claim is therefore rationale-level only.

### 4. Estimand identifiability and measurability

The proposed `GCF` quantity is measurable in principle, but it is not an
identified, executable estimand in the packet. It is introduced as a “possible”
summary, uses an unspecified `epsilon`, and leaves the original-model and
abstract-model interchange operators undefined. Assignment, timing,
consistency, positivity, and no-interference assumptions are not operationally
specified for the proposed graph/replacement construction.

This is a blocking failure under the review rule.

### 5. Exact faithfulness threshold

Blocking failure. The memo expressly defers the final score and threshold to a
future reviewed protocol. No exact primary threshold, raw-scale companion
threshold, or minimum control separation is fixed before review.

### 6. Uncertainty, missingness, and multiplicity

Blocking failure. The memo requires uncertainty intervals, missingness rules,
and multiplicity correction but does not specify the interval procedure,
cluster unit, missingness treatment, familywise or false-discovery rule, or the
number and identity of prespecified graph/component comparisons.

### 7. Power and reliability

Blocking failure. The memo says to power the study on an independent unit and
to measure reconstruction and intervention reliability, but provides no
effect-size target, sample-size calculation, ICC/repeatability assumptions,
repeat count, attrition rule, or simulation contract. These are deferred to a
future protocol rather than fixed for acceptance.

### 8. Controls and falsifiers

The control and falsifier families are directionally appropriate: no-op/zero,
shuffled graph, constant, matched-energy, input-only, text-only, reconstruction
error, attention/QK coverage, and held-out intervention agreement are relevant.

They are not yet a sealed implementation contract. No exact construction,
threshold, uncertainty rule, or multiplicity treatment is fixed for those
controls. The memo's list is therefore useful design guidance but insufficient
for acceptance under the strict packet rule.

### 9. Fresh data and custody

The memo correctly requires fresh document- and concept-disjoint splits and
sealed custody, and it explicitly prohibits reuse of V48 evidence. However, it
does not define a fresh corpus identity, model/runtime identity, source
digests, operator identity, runner, validator, or custody root. Those are
appropriately implementation-level details, but the requested review rule
requires a complete sealed rationale before protocol drafting. This item is
therefore deferred and blocking.

### 10. Prediction locking, retention, and claim ceiling

The packet correctly requires predictions before assessment effects, aggregate-
only retention, independent recomputation, and a bounded
causal-abstraction/localization claim ceiling. It also correctly preserves the
separation of V48, V82, and the dynamic-learning control-plane branch.

These items pass as governance boundaries. They cannot compensate for the
missing causal and statistical specification.

## Verdict basis

The mandatory strict rule is triggered by multiple independent omissions:

1. the exact faithfulness threshold is deferred;
2. uncertainty, missingness, and multiplicity rules are deferred;
3. power and reliability analysis is qualitative rather than quantitative;
4. the proposed `GCF` is a possible summary rather than an identified,
   fully specified estimand; and
5. the literature review is explicitly a seed index, not the required
   systematic novelty review.

The packet is therefore rejected as a reopening rationale. This is not a claim
that causal abstraction or circuit tracing cannot be useful. It is a finding
that the current memo is not sufficiently specified to authorize protocol
drafting under the stated gate.

## Final authorization status

```yaml
verdict: REJECT
execution_authorized: false
protocol_drafting: CLOSED
implementation_authorization: CLOSED
qualification: CLOSED
assessment: CLOSED
astral_status: TERMINATED_AFTER_V48
stage_0c: BLOCKED
stage_1: BLOCKED
v82: ISOLATED_AND_BLOCKED
```

No model, corpus, circuit-tracing implementation, protocol variation, or
assessment may proceed from this packet. V48 remains the terminal Astral
result. Any future reconsideration requires a new, separately authorized
theory packet with the omitted specifications fixed before review; this
rejected receipt cannot authorize a revision or adaptive repair.
