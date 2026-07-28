# Holistic Continual-Learning Benchmark V2

State slice: `astral-rgs-nested-recoverable-update-v27`.

Status: `ScientificValidatorImplemented / ImmutableReplayPending / ModelBackedAssessmentNotRun`.

## Evidence matrix

| Lane | Function | May update parameters? | Maximum direct evidence |
|---|---|---:|---|
| Fresh RGS stream | Architecture training and continual-update comparison | Yes, under the frozen local protocol | Bounded local model-backed comparison |
| Fresh sealed RGS assessment | Acquisition, retention, forgetting, calibration, recovery, regret | No fitting from assessment | Local development candidate or negative result |
| Tencent CL-bench | Frozen-system inference-time context learning | No | Frozen external context-learning observation |
| Independent implementation | Fresh corpus, code, checkpoint, and preregistration | Yes, independently | Replication result after review |

## Required dimensions

The benchmark reports performance, retention, recovery, calibration, resource
cost, and governance as separate dimensions. A method is feasible only if all
mandatory gates pass. Future-unseen score is the claim-bearing endpoint; no
weighted utility may compensate for a failed dimension.

The benchmark requires exact model and tokenizer hashes, source commits and
trees, dirty-state records, data and license hashes, split manifests, arm and
selector configurations, prediction locks, raw trajectories, update artifacts,
fault injections, PCSM journals, rollback/replay digests, resource identities,
failure records, and a sorted content manifest.

## External benchmark interpretation

Tencent CL-bench contains 1,899 professional and domain-specific context tasks
and uses binary all-rubrics grading. Its official scripts target an
OpenAI-compatible endpoint. It measures learning from current inference
context, not persistent parameter learning or recoverable continual updates.

V27 permits a deterministic category-stratified diagnostic subset chosen by a
sealed task-ID hash after context-length filtering. This subset is explicitly
not a full benchmark, canonical score, leaderboard result, or dominance claim.
Canonical grading additionally requires the official GPT-5.1 low-reasoning
judge configuration.

## Holistic dispositions

The V27 validator emits three separate dispositions:

- local RGS model-backed execution;
- Tencent frozen external context-learning execution;
- thesis and downstream research gates.

One lane cannot promote another. A valid Tencent run cannot fill missing
model-backed arms. A valid local RGS run cannot become independent replication.
The thesis remains `NotValidated` while Stage 0C confirmation, model-backed
correction gain, prospective failure prediction, independent human review, or
independent implementation replication is absent.

## Authoritative V27 command

```text
python tools/astral-rgs-continual-v27/validate_all_v2.py \
  --historical-report <digest-bound-V25-holistic-report> \
  --tencent-packet <digest-bound-Tencent-result-packet> \
  --tencent-subset-manifest <digest-bound-subset-manifest> \
  [--rgs-report <digest-bound-model-backed-RGS-report>] \
  --output <new-repository-external-V27-report.json>
```

The command rehashes the referenced Tencent bytes, checks the exact C001-C048
ledger census, independently recomputes candidate gates, oracle regret,
architecture and selector contrasts, the paired family/seed bootstrap, Holm
corrections, and specificity, preserves every required false claim, and emits a
SHA-256 sidecar. Omitting the RGS report is explicit `NotRun`. Supplying a
malformed RGS report is `Invalid` and returns nonzero.

The immutable release is built with `build_release.py` and replayed with
`replay_release.py`. It contains both Git bundles and exact source inventories,
runtime identity, historical evidence, every retained Tencent byte, a sorted
manifest, and the optional locked RGS input/report pair. A Tencent V2 packet is
rebound and replayed. The earlier V1 diagnostic is retained with its model,
dataset, licenses, outputs, and grades but remains nonreplayable because its
exact inference and grading commands were not recorded; no command may be
reconstructed or fabricated after the fact. Replay uses detached clean
checkouts and must not mutate the release.
