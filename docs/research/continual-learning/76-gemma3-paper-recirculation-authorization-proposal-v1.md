# Gemma3 paper-aligned recirculation authorization proposal V1

Date: 2026-08-26

State slice: `continual-learning-gemma3-paper-recirculation-v1`.

Status: `Activated / ExecutionNotStarted`.

Candidate claim ceiling after all gates pass:
`LocalDevelopmentGemma3PaperAlignedRecirculationReplication`.

This document records activation of the named state slice for the bounded
offline execution described below. It does not authorize network access,
model or corpus downloads, create accepted scientific evidence, mutate the
Evidence Ledger, or authorize an Astral self-modeling claim.

## Source and purpose

The proposed study is a bounded local replication of the pretrained Gemma3 1B
perplexity arm in [Recirculation, arXiv:2608.17981](https://arxiv.org/html/2608.17981v1).
It measures inference-time representation recirculation. It does not test
consciousness, introspection, agency, privileged telemetry, or causal
self-modeling.

The prior Qwen V1-V5 studies remain separate local feasibility studies. Their
model, layer pair, corpus, and result must not be transferred into this slice.

## Candidate inputs and custody

The candidate checkpoint is the pretrained, non-instruction-tuned
`google/gemma-3-1b-pt` model, executed through the locally available BF16 MLX
conversion. The observed candidate directories are outside the repository:

- `/Users/shaanp/.lmstudio/models/google/gemma-3-1b-pt`
- `/Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16`

The observed weight-file SHA-256 values are recorded here only as preparation
observations, not as accepted execution-manifest values:

- Google checkpoint: `ee5250f6eb1aa7cfb729dfd4dc8d9964fd772324776c6d00bf2bc674c069cb27`
- MLX BF16 conversion: `37d4ce2e05be1febb1b390ce18923fadd18469f8b1544a3b47627906e5e5ba28`

Before execution, an immutable external artifact root must bind the complete
model file sets, source repository identifiers, conversion metadata, tokenizer
files, configuration files, runtime versions, per-file lengths, and SHA-256
digests. The native and converted weight hashes are expected to differ; the
conversion must instead pass declared runtime-output parity checks.

The external artifact root must also contain independently digest-bound copies
of the arXiv, C4, PG19, and evaluation panels. The repository Markdown corpus
used by Qwen V5 is ineligible as a substitute for the paper corpus.

The operator-facing
`experiments/continual_learning/stage_and_run_gemma3_paper_recirculation_v1.py`
utility stages those panels from an operator-acquired normalized source root.
The source root contains `acquisition-manifest.json` and one JSONL file per
protocol dataset; each JSONL record has a stable `document_id` and raw UTF-8
`text`. The acquisition manifest records the source, revision, and split for
each exact fit and assessment dataset. The utility tokenizes with the cached
Gemma tokenizer, materializes the external corpus atomically, requires the
paper's fit counts, rejects existing roots, runs the offline campaign, and
invokes the independent validator as a separate process. It never downloads
data or writes experiment artifacts inside the repository. `--pack-only`
performs the source and corpus custody checks without loading model weights.

## Frozen mechanism

For token position `t`, source layer `s`, and destination layer `d`, the
candidate implementation must perform one additional recurrence using the
paper's convex form:

`z[t+1,t,d] = alpha * f(z[t,t,s] | d,t) + (1 - alpha) * z[t,t,d]`.

The source contribution must use the paper's source-to-destination norm
adjustment. The baseline is the same model and token sequence with no
recirculation. The implementation must not train weights, update adapters,
loop transformer blocks, or perform more than the specified additional
iteration.

## Execution phases

### 1. Custody and runtime qualification

The runner must verify the external manifest, model/config/tokenizer identity,
safe paths, complete file census, and runtime versions before loading weights.
It must then establish:

- native-versus-MLX output parity on fixed token windows within a preregistered
  tolerance;
- exact zero-alpha identity within the same runtime;
- deterministic repeated execution;
- teacher-forced tokenization and target alignment;
- no training and no network access after acquisition.

Any failed qualification stops the phase without opening assessment.

### 2. Fit-only hyperparameter sweep

The fit panel must follow the paper's 1024-token procedure: at most two full
windows per document, no filler tokens, and separate document custody. The
fit sweep must evaluate source/destination pairs no more than twelve layers
apart over `alpha` in `{0.04, 0.07, 0.10, 0.16}`, with `beta = 1 - alpha` and
the declared convex norm-ratio adjustment.

The paper reports Gemma3 1B PT source layer `11` and destination layer `4` as
the selected pair. That pair is an expected replication target, not a forced
label: if the sealed fit sweep does not recover it, the discrepancy must be
reported rather than repaired by post-hoc selection.

The fit result must be sealed before any evaluation-panel metrics are computed.

### 3. Locked assessment

The assessment must use a distinct evaluation split and the paper's fixed
evaluation coefficient `alpha = 0.15`, `beta = 0.85`, after the source and
destination pair has been selected from fit data. Evaluation must use the
paper's full ten-dataset shape where the external panels are available, with
1024-token chunks and partial-window handling bound by the dataset policy.

The primary endpoint is the paired held-out mean next-token NLL difference:

`recirculation_mean_nll - baseline_mean_nll`.

Perplexity, document-level uncertainty intervals, token-count accounting,
per-window direction counts, and dataset-stratified results are secondary
outputs. Assessment thresholds, dataset inclusion, and uncertainty procedures
must not be tuned after assessment is opened.

### 4. Required controls

The locked report must keep these conditions separate:

- native baseline;
- zero-alpha recirculation identity control;
- paper recirculation;
- temperature-only and temperature-plus-recirculation controls;
- looped-transformer control, if the required runtime surface is independently
  qualified;
- deterministic repeat of the locked assessment.

The looping condition is not a substitute implementation. It must use its own
declared block-copy semantics and must not be described as recirculation.

## Independent validation and artifacts

The runner and validator must be separate source surfaces. The validator must
recompute, without trusting runner-produced summaries:

1. model and tokenizer manifests;
2. corpus file census, document split, token windows, and target alignment;
3. source/destination/alpha configuration and recurrence formula;
4. zero-alpha and native parity observations;
5. locked assessment NLL and perplexity from retained aggregate inputs;
6. deterministic-repeat equality and all stop conditions.

The external result root must retain the configuration, manifests, fit sweep,
prediction-lock receipt, aggregate assessment results, validator receipt, and
a final stop code. Secrets, credentials, and unnecessary raw model outputs do
not enter the repository.

## Claim boundary and Astral separation

Even a positive result would establish only a local, paper-aligned Gemma3
recirculation replication under the frozen inputs and runtime. It would not
prove that recirculation universally improves language modeling, establish a
general Qwen result, or establish Astral self-modeling.

The Astral project has a separate intervention-effect prediction question and
remains at its existing local measurement/attribution ceiling. No recirculation
result may be written into the Astral claim ledger, used to unlock Stage 0C or
Stage 1, or presented as privileged telemetry evidence without a separate
Astral authorization and endpoint.

## Activation record and execution prerequisites

The state slice is activated in the repository authorization records. Execution
still requires the runner to accept all of the following as present and
immutable:

- the runner and independent validator paths and source digests;
- the external model and corpus artifact root;
- the exact runtime and command-line contract;
- fit, tune, and assessment split digests;
- the prediction-lock ordering rule;
- the artifact retention and redaction policy;
- the claim ceiling and explicit non-promotion rules.

Activation does not imply that these prerequisites are present, that a model
has been loaded, or that an experiment result exists.
