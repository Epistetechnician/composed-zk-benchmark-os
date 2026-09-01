# Astral V40 tooling

State slice: `astral-stage0c-qwen36-intervention-conditioned-target-v40`.

This directory implements the V40 protocol in
`docs/research/astral-self-modeling/90-stage0c-intervention-conditioned-target-protocol-v40.md`.
It is additive and claim-bounded. Model execution uses only the already-cached
Qwen3.6 MLX checkpoint; Gutenberg network access is limited to corpus
acquisition.

The custody sequence is:

1. `fetch_gutenberg_corpus_v40.py` publishes a fresh external corpus.
2. `validate_gutenberg_corpus_v40.py` independently validates its bytes and metadata.
3. `panel_v40.py` publishes the 144-family, fixed-320-token panel.
4. `validate_panel_v40.py` independently recomputes the panel and tokenizer length.
5. `qualify_v40.py` publishes instrument qualification only.
6. `validate_qualification_v40.py` independently validates qualification.
7. `run_preassessment_v40.py` measures fit/tune effects and seals estimator-only predictions.
8. `validate_preassessment_v40.py` independently validates the preassessment lock.
9. `prepare_independent_review_packet_v40.py` publishes a pending review packet.
10. `record_independent_review_v40.py` requires explicit reviewer identity and attestation.
11. If tune utility fails, `finalize_early_stop_v40.py` seals a no-candidate result and assessment is not run.
12. Only an accepted receipt permits `run_assessment_v40.py` when tune gates pass.
13. `validate_assessment_v40.py` and `finalize_v40.py` retain only aggregate results.

All scientific roots must remain outside the repository and must not be
overwritten. Assessment, Stage 0C, Stage 1, accepted-evidence, benchmark, and
production claims remain closed unless their separate existing gates pass.
