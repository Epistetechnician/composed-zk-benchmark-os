# Astral V41 directional-block target protocol

State slice: `astral-stage0c-qwen36-directional-block-target-v41`.

V41 is an authorized fresh design-only successor to V40. It tests whether a
fixed non-overlapping signed block projection preserves predictive directional
geometry that may be lost by V40's hash-and-bucket sketch. The target, utility
thresholds, controls, review ordering, prediction lock, aggregate-only
retention, and claim boundary remain fixed.

Current implementation boundary:

- `protocol_v41.py` defines the pure-data custody and feature-map contract;
- `features_v41.py` implements the fixed 128-by-16 signed block projection;
- `acquire_gutenberg_corpus_v41.py` acquires only the sealed Project Gutenberg
  text/RDF inputs into an external root;
- `validate_gutenberg_corpus_v41.py` independently validates custody, freshness,
  split identity, and the corpus output census;
- `qualify_v41.py` and `validate_qualification_v41.py` implement the
  qualification-first Qwen3.6 instrument gate;
- `panel_v41.py` and `validate_panel_v41.py` implement the fresh-panel custody
  boundary;
- `run_preassessment_v41.py` and `validate_preassessment_v41.py` implement
  fit/tune effects, fit-only estimator selection, and the prediction lock;
- `prepare_independent_review_packet_v41.py` and
  `record_independent_review_v41.py` implement the explicit review gate;
- `run_assessment_v41.py` and `validate_assessment_v41.py` implement the
  post-review direct-effect assessment and aggregate-only validation;
- `finalize_v41.py` and `validate_final_v41.py` implement narrow final
  classification without Stage 0C or Stage 1 promotion;
- V41 qualification passed independently; no V41 corpus, panel, effect,
  prediction, review, or assessment result artifact exists.

The qualification command is offline and uses only the cached model:

```text
PYTHONDONTWRITEBYTECODE=1 python -B \
  tools/astral-stage0c-qwen36-v41/qualify_v41.py \
  --model /Users/shaanp/.lmstudio/models/lmstudio-community/Qwen3.6-35B-A3B-MLX-4bit \
  --output-root /Users/shaanp/Documents/astral-artifacts/astral-stage0c-qwen36-v41-qualification-r1-2026-08-27
```

The result must be independently validated before any future panel or
preassessment work. A failed qualification stops V41. No assessment may open
without fresh external corpus custody, a sealed prediction lock, and an
independent review receipt created before assessment effects.

The authorized execution order is:

```text
acquire corpus -> validate corpus -> qualify -> validate qualification
-> build panel -> validate panel -> run preassessment -> validate preassessment
-> prepare review packet -> record independent review -> run assessment
-> validate assessment -> finalize -> validate final result
```

The acquisition step is the only network-capable step. Qualification and all
model execution steps are offline and must use already-custodied inputs.
