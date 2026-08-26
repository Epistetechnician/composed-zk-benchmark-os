from __future__ import annotations

import json

from experiments.continual_learning.qwen_inference_recirculation_v3 import ALPHAS
from experiments.continual_learning.qwen_inference_recirculation_v4 import (
    ASSESSMENT_FILES,
    FIT_FILES,
    corpus_texts_and_manifest,
)


def test_fresh_corpus_is_source_disjoint_and_balanced():
    fit_texts, assessment_texts, corpus = corpus_texts_and_manifest()
    assert len(fit_texts) == 16
    assert len(assessment_texts) == 16
    assert not set(FIT_FILES) & set(ASSESSMENT_FILES)
    assert [item["path"] for item in corpus["manifest"]["fit_sources"]] == list(FIT_FILES)
    assert [item["path"] for item in corpus["manifest"]["assessment_sources"]] == list(
        ASSESSMENT_FILES
    )


def test_fresh_corpus_manifest_contains_digests_not_raw_text():
    fit_texts, assessment_texts, corpus = corpus_texts_and_manifest()
    serialized = json.dumps(corpus, sort_keys=True)
    assert all(text not in serialized for text in (*fit_texts, *assessment_texts))
    assert corpus["manifest"]["fit_sequence_count"] == 16
    assert corpus["manifest"]["assessment_sequence_count"] == 16


def test_v4_corpus_uses_the_v3_alpha_grid_without_redefinition():
    assert tuple(ALPHAS) == (0.04, 0.07, 0.10, 0.16)
