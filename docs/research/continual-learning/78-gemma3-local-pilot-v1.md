# Gemma3 local recirculation mechanics pilot V1

Date: 2026-08-27

State slice: `continual-learning-gemma3-local-pilot-v1`.

Claim ceiling: `LocalDevelopmentGemma3NewsroomRecirculationMechanicsPilot`.

## Boundary

This is a scaled local mechanics pilot for the inference-time recurrence in
[Recirculation, arXiv:2608.17981](https://arxiv.org/abs/2608.17981). It is not a
replication of the paper's Gemma3 evaluation because it uses only four
NEWSROOM test documents, 256-token windows, and two fit plus two assessment
windows. It does not use the paper's C4 WebText-like export or its full
ten-dataset assessment panel.

The cached pretrained `google/gemma-3-1b-pt` BF16 MLX conversion is loaded
offline. Weights remain frozen; no model or corpus download, training, adapter
update, provider call, production traffic, Evidence Ledger mutation, or
benchmark claim is allowed.

## Frozen protocol

- Input: operator-supplied NEWSROOM registered `test.jsonl.gz`, retained under
  the active PrimaryED artifact root with a SHA-256 digest.
- Selection: first four source-order records with at least 256 Gemma tokens;
  first two are fit and last two are held-out assessment records.
- Window: exactly the first 256 tokens of each selected document, with no
  filler tokens and no document reuse across fit and assessment.
- Fit grid: `(source, destination)` pairs `(7,2)`, `(9,3)`, `(11,4)`, and
  `(12,5)` at `alpha=0.10`.
- Locked evaluation: the fit-selected pair at `alpha=0.15`, `beta=0.85`, with
  source-to-destination L2 norm adjustment.
- Controls: native baseline, zero-alpha parity, temperature-only,
  temperature-plus-recirculation, and a deterministic repeat.
- Storage: PrimaryED is the active immutable artifact; DAed receives an
  immutable mirror. Existing roots are rejected.

The paper's `(11,4)` pair is reported as an expected target only. The pilot
does not force that selection.

## Commands

The end-to-end command is:

```text
PYTHONDONTWRITEBYTECODE=1 python -B \
  /Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/gemma3_local_pilot_v1.py \
  --input /Users/shaanp/.codex/research-artifacts/composed-zk-benchmark-os/gemma3-manual-inputs-v1/newsroom/release/test.jsonl.gz \
  --model /Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16 \
  --primary-root /Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-gemma3-local-pilot-v1-20260827-r1 \
  --daed-root /Volumes/DAed/Archives/composed-zk-benchmark-os/continual-learning-gemma3-local-pilot-v1-20260827-r1
```

The runner invokes the independent validator before publishing the PrimaryED
root, mirrors it to DAed, and validates both published roots read-only. The
validator is:

```text
PYTHONDONTWRITEBYTECODE=1 python -B \
  /Users/shaanp/Documents/GitHub/composed-zk-benchmark-os/experiments/continual_learning/validate_gemma3_local_pilot_v1.py \
  --artifact-root /Volumes/PrimaryED/ResearchArtifacts/composed-zk-benchmark-os/continual-learning-gemma3-local-pilot-v1-20260827-r1 \
  --model /Users/shaanp/.lmstudio/models/mlx-community/gemma-3-1b-pt-bf16
```

## Claim ceiling

A valid artifact establishes only that this local Gemma3 runtime executed the
declared recurrence and passed the pilot's custody, parity, aggregate-metric,
and repeat gates. Any observed assessment delta is a fixture-local mechanics
signal. It does not prove recirculation generally improves language modeling,
replicate the paper, establish an Astral result, or authorize accepted
scientific, benchmark, provider, or production claims.
