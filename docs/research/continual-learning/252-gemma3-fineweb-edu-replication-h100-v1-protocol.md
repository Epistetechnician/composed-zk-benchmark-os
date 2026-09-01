# Gemma3 FineWeb-Edu replication H100 V1 protocol

State slice: `continual-learning-gemma3-fineweb-edu-replication-h100-v1`.

This is a new protocol identity. It does not mutate, accelerate, reinterpret,
or reuse the V31 result. The current local V31 process remains governed by its
own frozen protocol. This H100 slice is a separate CUDA/PyTorch replication
attempt using a fresh cohort and a separately re-custodied model bundle.

The slice is proposed and implementation-gated. A paid GiveMeANode job is
forbidden until an independent reviewer accepts this protocol, its review
packet, the implementation manifest, the launch-manifest schema, and the
current `AGENTS.md` bytes. The exact launch manifest is created only after
that acceptance and after the user supplies its hard USD ceiling. The user
authorization for this state slice is not a provider spend ceiling and does
not authorize a job submission by itself.

## Purpose and claim ceiling

The purpose is to test whether the one-additional-iteration recurrence from
[Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981) can be
executed reproducibly on one H100 using the original PyTorch Gemma3 1B PT
checkpoint. The reported Gemma3 pair `(source=11, destination=4)` remains an
expected replication target, never a forced selection.

The maximum claim is
`LocalDevelopmentGemma3FineWebEduReplicationH100V1`. A positive result is not
a breakthrough claim, a benchmark result, production evidence, a claim about
H100 superiority, or evidence for general recirculation. A failed parity,
custody, qualification, or statistical gate is `NoCandidate` or an execution
failure under this slice; no tuning around that outcome is allowed.

## Provider and spend boundary

The provider is GiveMeANode. The only permitted job shape is one `h100-1`
batch job. Interactive nodes, multi-GPU nodes, sweeps, spot fallback, or an
unbounded shell are prohibited. The job must be submitted with a sealed
context and an explicit maximum runtime.

The launch manifest must contain all of the following before the no-spend
preflight and any provider submission:

- `hard_usd_ceiling`, a positive finite number supplied by the user;
- `quoted_gpu_usd_per_minute`, `max_runtime_minutes`, and
  `estimated_max_total_usd`;
- `estimated_max_total_usd <= hard_usd_ceiling`;
- provider account/project identity without credentials or tokens;
- exact node type `h100-1`, container image digest, command digest, exact CUDA
  driver version, `container_network_mode: none`, and external storage
  namespace;
- a stop rule that terminates the node/job at the first failed gate or budget
  boundary.

No default dollar amount is implied. If a quote changes, the launch manifest
is stale and must be reviewed again. Credentials remain outside the repository
and outside retained receipts.

## Fixed local custody and fresh cohort

The local source model is the already-downloaded original PyTorch checkpoint:

```text
/Users/shaanp/.lmstudio/models/google/gemma-3-1b-pt
```

The stable file manifest currently observed for that directory is
`54b406ace506bfadcddf6391663de9c82a95636251f62df8aa8a699fc8f3bd8d`.
The manifest covers exactly these non-cache files:

```text
.gitattributes
README.md
added_tokens.json
config.json
generation_config.json
model.safetensors
special_tokens_map.json
tokenizer.json
tokenizer.model
tokenizer_config.json
```

The model bundle must be copied to a new external custody root and verified by
the same manifest before upload. The provider container may load only the
digest-identified bundle from its sealed working directory; it may not fetch a
model at runtime.

FineWeb-Edu identity remains the pinned dataset
`HuggingFaceFW/fineweb-edu`, revision
`87f09149ef4734204d70ed1d046ddc9ca3f2b8f9`, config
`fineweb-edu-crawl-shards`, split `train`. The two raw Parquet objects retain
the V31 byte pins, but this slice must re-custody them under a new H100 root.
The fresh row interval is `[34816,51200)` in each shard. The fit split uses
the first pinned shard and the assessment split uses the second pinned shard,
with the first 64 eligible 1024-token windows in each split. Every source
document ID, source row, raw byte digest, normalized record, and window digest
is rederived by the H100 packer and independently rechecked from the raw
Parquet objects before execution. The exclusion ranges are `[0,2048)` for the
prior pilot, `[2048,18432)` for the prior V31 fresh cohort, and `[18432,34816)`
for the discarded range, in each pinned shard. Their source IDs are rederived
from the raw objects and bound by digest; their text, activations, metrics, and
results are not scientific inputs. A corpus containing only window JSONL files
without these raw-object and row-lineage checks is invalid.

The exact external custody roots are:

```text
/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/
  gemma3-fineweb-edu-replication-h100-v1-raw/
/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/
  gemma3-fineweb-edu-replication-h100-v1-source/
/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/
  gemma3-fineweb-edu-replication-h100-v1-corpus/
/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/
  gemma3-fineweb-edu-replication-h100-v1-result/
```

GiveMeANode object storage receives only the digest-bound model, source,
corpus, code context, launch manifest, and aggregate result bundle. Raw text,
token IDs, logits, hidden states, and per-token arrays may exist only in the
ephemeral provider workspace and must be removed before the final receipt is
sealed. The retained result is aggregate-only plus per-document scalar NLL
rows and their document/text digests.

## Runtime and job contract

The H100 container must pin all runtime identities by image digest and a
machine-readable lock. The minimum runtime fields are CUDA driver/runtime,
Python, PyTorch, Transformers, Safetensors, Tokenizers, and the exact NVIDIA
GPU identity. The H100 implementation must use `torch.inference_mode()`, BF16
weights, deterministic evaluation settings, and frozen parameters. No
training, optimizer, gradient, adapter, quantization, or weight update is
allowed.

The provider image build must verify the locked Python, PyTorch, Transformers,
Safetensors, Tokenizers, and CUDA versions from `requirements.lock` and
`runtime-lock.json`; runtime installation is forbidden. The runner must read
the same lock, compare every installed identity, and fail before model load on
any mismatch.

The implementation manifest is
docs/research/continual-learning/254-gemma3-fineweb-edu-replication-h100-v1-implementation-manifest.json.
It lists every reviewed implementation file and its SHA-256 digest. The launch
manifest, review receipt, and provider code bundle must all bind this
implementation-manifest digest.

The H100 runner must be independent of the MLX runner. It may share only the
documented JSONL/window schema and the mathematical recurrence. It must not
import the V31 runner, V31 validator, or V31 result files. The runner must
record the complete command, environment lock, container digest, GPU identity,
model manifest, source/corpus manifests, and result digest.

Network is allowed only for provider control-plane operations and pre-staged
bundle transfer. The container must be launched with a network-none namespace;
the runner independently proves that only `lo` exists and that IPv4/IPv6
route tables contain no non-loopback route. Python socket/DNS, child-process,
shell, fork, exec, and spawn paths are blocked around all effects. Any
download, DNS lookup, package installation, or external API call during
execution is a hard failure.

## Qualification gates

Before fit effects or assessment effects, the runner must pass all gates:

1. launch-manifest schema, review receipt, budget arithmetic, and exact
   provider/job shape;
2. complete model, code, source, corpus, and container digest custody;
3. tokenizer round-trip and exactly 1024 tokens per window;
4. native PyTorch deterministic repeat on the fixed probe set;
5. zero-alpha identity for every candidate pair;
6. nonzero intervention reach from each candidate source to destination layer;
7. frozen parameter manifest before and after qualification;
8. no network and no package/runtime drift inside the job;
9. exact fit/assessment disjointness and exclusion of all prior IDs;
10. independent validator readback of the pre-effect bundle.

The local MLX V31 output is not a parity oracle. Cross-runtime parity is
reported as a diagnostic only; it cannot silently convert the H100 result into
V31 evidence. A future cross-runtime equivalence claim would require its own
protocol.

## Locked recurrence and statistical decision

Fit candidates are exactly `((7,2),(9,3),(11,4),(12,5))`, with `alpha=0.10`
and `beta=0.90`. The lowest fit mean NLL wins, with listed order as the
tie-break. Assessment uses only the selected pair, `alpha=0.15`, `beta=0.85`,
source-to-destination L2 norm adjustment, and frozen weights.

Controls are native baseline, zero-alpha identity for every candidate pair, all
fixed candidates, temperature `1.20` baseline/intervention, deterministic
repeat, and frozen parameter digest. The primary estimand is paired per-document selected-minus-
baseline NLL over the 64 assessment windows. Uncertainty is the fixed 10,000-
resample SHA-256-counter nearest-rank 95% bootstrap. Only mean `<0` and upper
bootstrap bound `<0` yields `ReplicationCandidate`; otherwise the result is
`NoCandidate`.

The primary mechanical runtime metric is completed assessment windows per
H100 minute, subject to every scientific and custody gate passing. It is not
permitted to trade away controls, repeats, custody, or uncertainty for speed.

## Review, execution, and publication ordering

The independent reviewer must read exactly the files named in the review
packet, recompute all source digests, and return a signed canonical `ACCEPT`.
The receipt must bind the exact protocol, packet, implementation manifest,
launch-manifest schema, and current `AGENTS.md` bytes. The packet reviews the
launch-manifest schema; it does not invent a missing hard USD ceiling. A
changed reviewed byte invalidates the receipt.

After review acceptance, the operator may fill an exact launch manifest and
run the local no-spend preflight. The preflight must reject absent or stale
review, missing hard USD ceiling, budget overflow, unknown launch commands,
mutable bundle paths, missing digests, and any assessment flag before custody
and qualification pass. Only then may the operator use the GiveMeANode CLI or
API to submit one bounded `h100-1` batch job.

The provider receipt must be independently validated before the aggregate
result is classified. The result is published only through a no-overwrite
external root. Any provider, custody, qualification, validator, budget, or
publication failure closes this H100 slice without adaptive retry.

Every mutation in this phase names state slice
`continual-learning-gemma3-fineweb-edu-replication-h100-v1`.
