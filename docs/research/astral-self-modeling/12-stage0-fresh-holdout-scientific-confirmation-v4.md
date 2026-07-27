# Stage 0 Fresh-Holdout Scientific Confirmation V4

## Boundary

State slice: `astral-stage0-fresh-holdout-scientific-confirmation-v4`.

Status before execution: `PreregisteredFreshHoldoutConfirmation`.
Evidence ceiling: `LocalLearnedModelMeasurementCandidate`.

V4 is a fresh-holdout confirmation after exploratory training adaptation. It is
not a pristine independent replication: V1 evaluation outcomes were inspected
before the program continued. V4 results will not be pooled with V1, and its
bootstrap intervals are V4-local rather than program-wide error-controlled.

Repository inspection supports that actor seeds `109, 113, 127` and families
`384..447` have not been used by an Astral experiment. This cannot rule out an
unrecorded external computation.

## Frozen Actor Qualification

The actor is the V3-selected `a-width32-block1` configuration: one post-norm
attention block, width 32, four heads, head width 8, feed-forward width 64,
GELU, no dropout, CLS classifier, and 9,890 trainable parameters. V4 adds an
override-capable forward path without changing clean computation. Bitwise clean
logit, head, and attention equality against the V3 actor is required on
development-only test data before holdout access.

Training uses train families `0..159`, development families `160..191`, AdamW
learning rate `0.003`, weight decay `0.01`, batch 128, clipping `1.0`, exactly
2,000 updates, development loss every 25 updates, and lowest finite development
loss checkpoint selection with earliest exact tie. Each scientific seed is
trained twice. Both reproductions must reach train and development accuracy
`>=0.95` and have identical selected step, checkpoint digest, and trajectory
digest. Any failure is `Inconclusive` and leaves the holdout unopened.

Only after all actor pairs and the protocol/review lock validate may V4
materialize exactly 1,024 examples per seed from families `384..447`.

## Frozen Measurement and Order

Candidate components are the four attention-head outputs at CLS before output
projection. The candidate score is
`-<d(correct-minus-incorrect margin)/dh, h>`. Competitive baselines are
activation L2 norm, gradient L2 norm, and attention mass on causal tokens.
Controls are deterministic candidate permutation and zero.

All 3,072 score/capture records are serialized and hashed before any
intervention. The intervention phase then measures zero ablation and matched
same-family patching that flips only bit A. Top-one selection uses absolute
score with lowest-index tie breaking. Normalized regret, dead zone `1e-4`,
equal prompt-to-family-to-seed aggregation, 2,000-draw hierarchical paired
bootstrap seed `20260727`, practical margin `0.05`, and every V1 method remain
unchanged.

## Verdict Gate

`Pass` requires:

1. every actor pair qualifies reproducibly before holdout access;
2. informative coverage is at least `0.80` for every seed;
3. against every competitive baseline, mean paired regret advantage is above
   `0.05`, the V4-local 95% interval lower bound is above `0.05`, and every
   seed advantage is positive;
4. candidate advantage over the permuted control has positive mean and interval
   lower bound;
5. candidate-selected absolute patch effect exceeds every competitive
   baseline for every seed;
6. evaluation accuracy is at least `0.95` for every seed;
7. exact no-op, deterministic-repeat, clean-forward parity, split isolation,
   census, digest, semantic-validation, 30-minute, and 256 MiB gates pass.

A valid complete miss is `Null`. Pre-holdout actor failure is `Inconclusive`.
Contamination, ordering breach, unplanned retry, nonfinite computation,
malformed artifacts, control failure, provenance failure, or cap failure is
`Invalid`. Once families `384..447` are opened they are permanently retired,
including after interruption or invalidation.

## Claim Ceiling

A pass would show only that gradient-times-activation ranked the named CLS-head
interventions better than every frozen named baseline for this actor, training
procedure, task, candidate census, seeds, and holdout. It would not establish
independent replication, complete circuit recovery, general causal fidelity,
introspection, self-modeling, correction, observer value, safety, benchmark
evidence, or accepted evidence.

Independent pre-execution reviews completed on 2026-07-26 for protocol,
implementation structure, freshness, multiplicity, verdict mapping, and claim
boundary. No scientific seed or holdout family was executed before this
document was frozen.

## Execution Record — 2026-07-26

Classification: `InvalidAutogradCaptureBoundary`.

All actor pairs qualified before holdout access:

| Seed | Train / development | Step | Checkpoint SHA-256 | Trajectory SHA-256 |
|---:|---|---:|---|---|
| `109` | `1.0 / 1.0` | `2000` | `f8639d0a976375154094f18e0b549b574e7945d67c01b5e7f95eb740b6834f9c` | `a42848772a9a21aa2db72b50f5e1368594185a512ca9290efb5948149a51c4bf` |
| `113` | `1.0 / 1.0` | `2000` | `4847cd1c5bd67aa69ed9f43a169f9159a64cfe50f50be9b38c7c248e096060e0` | `27e38f6aa3f1f93d3cae0975f4f84ab290138e86c3858377095a9582e9dff005` |
| `127` | `1.0 / 1.0` | `2000` | `56615e8877d62272c27d4a9ce3deea72d74ee15fdec92342e391dcc2642e6bb2` | `91cbbbb3996a4103fddf9badfeeefa411060a8e4936ffb7d262c71754600923d` |

After the qualification lock, families `384..447` were materialized. The first
candidate score then failed before serialization because the returned CLS-head
view was not the autograd tensor used by the classifier computation. PyTorch
reported that the differentiated tensor had not been used in the graph.

No score lock, intervention, record set, comparison, or scientific verdict was
produced. The eight-file failure bundle had canonical inventory SHA-256
`9ab07c9a36ef593599e3fea0cce7382526b89b8d0187778dad395f81f07ec315`.
The protocol requires families `384..447` and seeds `109, 113, 127` to be
retired without retry. No directional conclusion is permitted.
