from __future__ import annotations

import json

from experiments.continual_learning.qwen_inference_recirculation_v2 import (
    ASSESSMENT_FILES as V2_ASSESSMENT_FILES,
    FIT_FILES as V2_FIT_FILES,
)
from experiments.continual_learning.qwen_inference_recirculation_v4 import (
    ASSESSMENT_FILES as V4_ASSESSMENT_FILES,
    FIT_FILES as V4_FIT_FILES,
)
from experiments.continual_learning.qwen_inference_recirculation_v5 import (
    ASSESSMENT_FILES,
    FIT_FILES,
    TRANSFER_SOURCE,
    TRANSFERRED_CONFIG,
    corpus_texts_and_manifest,
)


def test_transfer_corpus_is_fresh_and_balanced():
    fit_texts, assessment_texts, corpus = corpus_texts_and_manifest()
    prior = set(V2_FIT_FILES) | set(V2_ASSESSMENT_FILES) | set(V4_FIT_FILES) | set(
        V4_ASSESSMENT_FILES
    )
    current = set(FIT_FILES) | set(ASSESSMENT_FILES)
    assert len(fit_texts) == 16
    assert len(assessment_texts) == 16
    assert not current & prior
    assert not set(FIT_FILES) & set(ASSESSMENT_FILES)
    assert corpus["manifest"]["fit_sequence_count"] == 16
    assert corpus["manifest"]["assessment_sequence_count"] == 16


def test_transfer_corpus_manifest_contains_no_raw_text():
    fit_texts, assessment_texts, corpus = corpus_texts_and_manifest()
    serialized = json.dumps(corpus, sort_keys=True)
    assert all(text not in serialized for text in (*fit_texts, *assessment_texts))


def test_transfer_configuration_is_locked_to_v4_receipt():
    assert TRANSFER_SOURCE == {
        "state_slice": "continual-learning-qwen-inference-recirculation-v4",
        "config_sha256": "5ebd7e72ddf6bff5fff19103172e80f6ac73f3bc7c7da158d1b469c5c2017029",
        "receipt_sha256": "aeec8b111d67e38b25e68b17fda03aae84a37067e4bb3eec1016b272dc4820a9",
    }
    assert TRANSFERRED_CONFIG.source_layer == 12
    assert TRANSFERRED_CONFIG.destination_layer == 5
    assert TRANSFERRED_CONFIG.alpha == 0.07
