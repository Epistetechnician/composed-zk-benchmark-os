# Gemma3 bounded WebText-like acquisition V1

State slice: `continual-learning-gemma3-paper-recirculation-c4-bounded-v1`.

This record defines a bounded local acquisition utility for the Gemma3
recirculation work. It is not the full TFDS `c4/webtextlike` dataset and does
not support a full C4 replication claim.

## Scope

`experiments/continual_learning/acquire_gemma3_bounded_webtextlike_wet_v1.py`
reads the already staged OpenWebText URL archive and the pinned Common Crawl
WET path manifests on PrimaryED, downloads a fixed number of deterministic WET
objects from each of the 12 collections, and filters those local WET records by exact
OpenWebText target URL. It then writes two-field JSONL files:

```text
/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/
  gemma3-c4-webtextlike-bounded-wet-v1/
    acquisition-manifest.json
    raw/wet/*.warc.wet.gz
    record-inventory.jsonl
    data/fit.jsonl
    data/assessment.jsonl
```

The default guard is 2,000 records, eight WET objects per collection, and 4 GiB
of retrieved WET bytes. The hard guards are 10,000 records, 16 objects per
collection, and 40 GiB. A 20 GiB free-space reserve is required
in addition to the configured byte ceiling. Existing roots and partial files
are never overwritten. `--resume` continues an incomplete external root using
already downloaded WET objects.

The source archive and all generated artifacts remain outside the repository.
The script records source paths, collection identities, raw digests, normalized
output digests, safety flags, and a manifest digest. The independent validator
is:

```text
experiments/continual_learning/validate_gemma3_bounded_webtextlike_wet_v1.py
```

## Usage

The staged archive already exists at the default path. A conservative first
run is:

```text
PYTHONDONTWRITEBYTECODE=1 python -B \
  experiments/continual_learning/acquire_gemma3_bounded_webtextlike_wet_v1.py \
  --objects-per-collection 16 \
  --max-records 100 \
  --max-bytes 34359738368 \
  --min-records 25
```

Then perform the independent readback:

```text
PYTHONDONTWRITEBYTECODE=1 python -B \
  experiments/continual_learning/validate_gemma3_bounded_webtextlike_wet_v1.py \
  /Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/gemma3-c4-webtextlike-bounded-wet-v1
```

## Executed bounded bundle

The resumed execution used the pinned first 16 WET objects from each of the 12
collections, a 32 GiB invocation ceiling, and an explicit `min_records=20`
override after the fixed raw custody set yielded 23 records. The external
bundle passed independent validation with:

- 192 WET objects and 28,079,347,831 downloaded bytes;
- 23 unique records, split into 15 fit and 8 assessment records;
- manifest SHA-256
  `449b5cbf7ea508cba9caa1d5a0c380bf547eb6a45472829c5aaf0c47d807d1fb`; and
- no partial files.

This is a bounded local mechanics panel only. The explicit threshold override
does not change the claim ceiling or make the panel equivalent to C4.

## Bounded mechanics execution

After acquisition validation, the bounded panel can be passed to
`experiments/continual_learning/gemma3_bounded_webtextlike_recirculation_v1.py`.
That adapter uses only the cached Gemma3 1B BF16 MLX checkpoint and performs no
network access or training. It selects the first four eligible 256-token
windows per split among the fixed pilot pairs
`(7,2)`, `(9,3)`, `(11,4)`, and `(12,5)` on fit records at `alpha=0.10`, then
locks the selected pair for assessment at `alpha=0.15` and `beta=0.85` with
source-to-destination norm adjustment. It checks native/zero-alpha parity and
a deterministic assessment repeat, and writes its result bundle only to an
external PrimaryED root. The independent result validator is
`experiments/continual_learning/validate_gemma3_bounded_webtextlike_recirculation_v1.py`.

The bounded runner is a mechanics adapter, not the paper-shaped runner. Its
short fixed windows are an execution-budget decision, not a claim of paper
protocol equivalence. It
does not assert exact C4 identity, paper replication, general recirculation,
benchmark superiority, production readiness, or accepted scientific evidence.

## Executed bounded mechanics result

The clean end-to-end run completed at:

```text
/Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/
  gemma3-c4-bounded-wet-recirculation-v1-r2/
```

The published bundle passed the independent result validator and the full
repository `pnpm run lint` gate. It contains four fit windows and four locked
assessment windows, each 256 tokens, with frozen cached Gemma3 1B BF16 MLX
weights and network access disabled. The selected fit pair was source layer 7
to destination layer 2 at `alpha=0.10`; the paper's Gemma3 1B expected pair
source 11 to destination 4 was not recovered by this bounded fit grid.

On the locked assessment panel, selected-minus-baseline mean NLL was
`-0.241517892` and perplexity delta was `-16.091500352`. Native/MLX parity,
zero-alpha identity, and the deterministic assessment repeat passed; the
repeat's maximum metric delta was `0.0`. These are local bounded mechanics
measurements over four assessment windows, not evidence for the paper's full
result.

The result chain is bound by these digests:

- source acquisition manifest:
  `449b5cbf7ea508cba9caa1d5a0c380bf547eb6a45472829c5aaf0c47d807d1fb`;
- runtime corpus manifest:
  `77dc1bbca18907390c03e793dadcc75beaa43a794fa363035bd72f650a305da9`;
- model manifest:
  `69f078b42d4521d3e53f0c388a20fa6cf32b4df7ea6535b0eb9da6ccef75c256`; and
- results:
  `018801229dbbf5721d216c26c6de395bc78308cfcb7b5c2cdf0474339365c5dd`.

The first completed run remains preserved as an audit artifact at
`gemma3-c4-bounded-wet-recirculation-v1`; r2 is the clean receipt-bound
publication because its stored validator receipt names the final output root.

The Common Crawl WET objects and path manifests are documented by
[Common Crawl](https://commoncrawl.org/latest-crawl). The CDX range-retrieval
utility remains available for smaller targeted probes, but the WET sample is
the bounded execution path because it avoids repeated rate-limited index
requests. The TFDS C4 builder is retained as the full-dataset reference, not
as an identity for this bounded bundle:
[TFDS C4 builder](https://raw.githubusercontent.com/tensorflow/datasets/v3.1.0/tensorflow_datasets/text/c4.py).

## Claim boundary

This slice permits only:

- custody and checksum validation of the bounded external bundle;
- local Gemma3 mechanics testing against its explicitly named fit and
  assessment files; and
- the claim ceiling
  `LocalDevelopmentGemma3BoundedWebTextLikeRecirculationPilot`.

It does not permit relabelling the bundle as `c4/webtextlike`, full-paper
replication, general recirculation, benchmark evidence, production claims,
training, model updates, Evidence Ledger mutation, or Astral claims.
