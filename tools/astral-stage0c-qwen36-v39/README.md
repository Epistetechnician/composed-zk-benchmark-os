# Astral V39 Qwen3.6 layer-effect protocol

State slice: `astral-stage0c-qwen36-layer-effect-v39`.

This directory contains the qualification-only runner and independent
aggregate-result validator for the fresh V38-derived Stage 0C protocol. The
runner uses the externally cached Qwen3.6 MLX checkpoint only to recheck the
instrument seam. It does not read the future scientific corpus, train a model,
open an assessment, or retain prompts, tokens, activations, logits, or traces.

## External Project Gutenberg intake

State slice: `astral-stage0c-qwen36-layer-effect-v39`.

`fetch_gutenberg_corpus_v39.py` acquires a new repository-external source
bundle from explicit Project Gutenberg ebook IDs. It downloads the canonical
plain UTF-8 text and per-ebook RDF metadata, verifies the ebook identity,
English language, public-domain rights marker, Project Gutenberg boundaries,
and four-document fit/tune/assessment assignments, then publishes atomically
into a previously nonexistent output root. It does not select books, invent
concept families, or open assessment.

Prepare an external selection manifest with exactly twelve unique IDs and four
documents per split:

```json
{
  "protocol": "astral-stage0c-qwen36-layer-effect-v39",
  "state_slice": "astral-stage0c-qwen36-layer-effect-v39",
  "documents": [
    {"gutenberg_id": 100001, "split": "fit"},
    {"gutenberg_id": 100002, "split": "fit"},
    {"gutenberg_id": 100003, "split": "fit"},
    {"gutenberg_id": 100004, "split": "fit"},
    {"gutenberg_id": 100005, "split": "tune"},
    {"gutenberg_id": 100006, "split": "tune"},
    {"gutenberg_id": 100007, "split": "tune"},
    {"gutenberg_id": 100008, "split": "tune"},
    {"gutenberg_id": 100009, "split": "assessment"},
    {"gutenberg_id": 100010, "split": "assessment"},
    {"gutenberg_id": 100011, "split": "assessment"},
    {"gutenberg_id": 100012, "split": "assessment"}
  ]
}
```

The IDs above are placeholders and must not be used without a separate
freshness and rights review. Acquire into a new path outside the repository:

```text
python3 -B tools/astral-stage0c-qwen36-v39/fetch_gutenberg_corpus_v39.py \
  --selection-manifest /path/to/external/selection-v39.json \
  --output-root /Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v39-corpus-2026-08-26
```

Validate without contacting Project Gutenberg:

```text
python3 -B tools/astral-stage0c-qwen36-v39/validate_gutenberg_corpus_v39.py \
  /Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v39-corpus-2026-08-26 \
  --write-receipt
```

The bundle contains raw documents only in the external custody root,
`corpus-manifest.json`, its sidecar SHA-256, the copied selection manifest,
and the validator receipt. The downloader leaves
`concept_registry_sha256` unset and `assessment_ready` false. A separately
reviewed concept registry and prediction-lock workflow are still required by
the V39 protocol.

Run hermetic tests:

```text
python3 -B -m unittest discover -s tools/astral-stage0c-qwen36-v39/tests -p 'test_*.py'
```

Run qualification into a new repository-external output root:

```text
python3 -B tools/astral-stage0c-qwen36-v39/qualify_v39.py \
  --model /Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit \
  --output-root /path/to/external/astral-stage0c-qwen36-v39-qualification
```

Validate the aggregate result against the same external model root and write a
non-secret validator receipt:

```text
python3 -B tools/astral-stage0c-qwen36-v39/validator_v39.py \
  /path/to/external/astral-stage0c-qwen36-v39-qualification/qualification-result.json \
  --model /Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit \
  --write-receipt
```

The qualification ceiling is
`LocalDevelopmentInstrumentFeasibilityOnly`. A passing qualification does not
open assessment or authorize Stage 0C. The future assessment requires the
protocol record, fresh external concepts and document-disjoint splits, a
sealed configuration, independent review, prediction locking, directly
measured held-out effects, all preregistered controls, and a separate
assessment authorization.

## Fit/tune preassessment and independent review

State slice: `astral-stage0c-qwen36-layer-effect-v39`.

After the corpus and panel validator receipts pass, run the fit/tune-only
preassessment into a new external root:

```text
python3 -B tools/astral-stage0c-qwen36-v39/run_preassessment_v39.py \
  --panel-root /path/to/external/astral-stage0c-qwen36-v39-panel \
  --corpus-root /path/to/external/astral-stage0c-qwen36-v39-corpus \
  --qualification-root /path/to/external/astral-stage0c-qwen36-v39-qualification \
  --model /Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit \
  --output-root /path/to/external/astral-stage0c-qwen36-v39-preassessment
```

Independently validate the aggregate-only output:

```text
python3 -B tools/astral-stage0c-qwen36-v39/validate_preassessment_v39.py \
  /path/to/external/astral-stage0c-qwen36-v39-preassessment \
  --panel-root /path/to/external/astral-stage0c-qwen36-v39-panel \
  --corpus-root /path/to/external/astral-stage0c-qwen36-v39-corpus \
  --qualification-root /path/to/external/astral-stage0c-qwen36-v39-qualification \
  --model /Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit \
  --write-receipt
```

Prepare the review packet only after that receipt is valid:

```text
python3 -B tools/astral-stage0c-qwen36-v39/prepare_independent_review_packet_v39.py \
  --preassessment-root /path/to/external/astral-stage0c-qwen36-v39-preassessment \
  --panel-root /path/to/external/astral-stage0c-qwen36-v39-panel \
  --corpus-root /path/to/external/astral-stage0c-qwen36-v39-corpus \
  --qualification-root /path/to/external/astral-stage0c-qwen36-v39-qualification \
  --model /Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit \
  --review-root /path/to/external/astral-stage0c-qwen36-v39-independent-review
```

The preassessment classification is
`PreassessmentPredictionLocked` at
`LocalDevelopmentV39PreassessmentPredictionLocked`. It measures direct
effects only on fit and tune, creates clean assessment predictions, and does
not measure assessment replacements. The accepted review receipt must be
created before assessment effects and must bind the unchanged prediction lock.

## Assessment and final disposition

State slice: `astral-stage0c-qwen36-layer-effect-v39`.

After the accepted review receipt exists, run the locked assessment into a new
external root:

```text
python3 -B tools/astral-stage0c-qwen36-v39/run_assessment_v39.py \
  --panel-root /path/to/external/astral-stage0c-qwen36-v39-panel \
  --corpus-root /path/to/external/astral-stage0c-qwen36-v39-corpus \
  --qualification-root /path/to/external/astral-stage0c-qwen36-v39-qualification \
  --preassessment-root /path/to/external/astral-stage0c-qwen36-v39-preassessment \
  --review-root /path/to/external/astral-stage0c-qwen36-v39-independent-review \
  --model /Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit \
  --output-root /path/to/external/astral-stage0c-qwen36-v39-assessment
```

Validate the aggregate assessment, finalize the narrow disposition, and
validate that final result:

```text
python3 -B tools/astral-stage0c-qwen36-v39/validate_assessment_v39.py \
  /path/to/external/astral-stage0c-qwen36-v39-assessment \
  --panel-root /path/to/external/astral-stage0c-qwen36-v39-panel \
  --corpus-root /path/to/external/astral-stage0c-qwen36-v39-corpus \
  --qualification-root /path/to/external/astral-stage0c-qwen36-v39-qualification \
  --preassessment-root /path/to/external/astral-stage0c-qwen36-v39-preassessment \
  --review-root /path/to/external/astral-stage0c-qwen36-v39-independent-review \
  --model /Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit \
  --write-receipt
python3 -B tools/astral-stage0c-qwen36-v39/finalize_v39.py \
  --assessment-root /path/to/external/astral-stage0c-qwen36-v39-assessment \
  --output-root /path/to/external/astral-stage0c-qwen36-v39-assessment
python3 -B tools/astral-stage0c-qwen36-v39/validate_final_v39.py \
  /path/to/external/astral-stage0c-qwen36-v39-assessment \
  --panel-root /path/to/external/astral-stage0c-qwen36-v39-panel \
  --corpus-root /path/to/external/astral-stage0c-qwen36-v39-corpus \
  --qualification-root /path/to/external/astral-stage0c-qwen36-v39-qualification \
  --preassessment-root /path/to/external/astral-stage0c-qwen36-v39-preassessment \
  --review-root /path/to/external/astral-stage0c-qwen36-v39-independent-review \
  --model /Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit
```

The final V39 utility gate is development-only: activation-only RMSE must be
strictly lower than the constant baseline on both tune and assessment. A
failure records `DevelopmentNoCandidate`; it does not establish target
validity, Stage 0C, Stage 1, benchmark evidence, or production readiness.
