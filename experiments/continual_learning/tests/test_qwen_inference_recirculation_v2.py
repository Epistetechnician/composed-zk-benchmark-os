from __future__ import annotations

import json

import pytest

from experiments.continual_learning.qwen_inference_recirculation_v1 import digest
from experiments.continual_learning.qwen_inference_recirculation_v2 import (
    ASSESSMENT_FILES,
    EXTRACTOR,
    FIT_FILES,
    STATE_SLICE,
    corpus_texts_and_manifest,
)
from experiments.continual_learning.validate_qwen_inference_recirculation_v2 import (
    validate,
)


def _valid_artifact(root):
    _, _, corpus = corpus_texts_and_manifest()
    model_body = {"model_name": "synthetic-qwen", "files": []}
    manifest = {"manifest": model_body, "manifest_sha256": digest(model_body)}
    config = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": "LocalDevelopmentQwenInferenceRecirculationBroaderFeasibility",
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "fit_sequence_count": 12,
        "assessment_sequence_count": 12,
        "model_manifest_sha256": manifest["manifest_sha256"],
        "corpus_manifest_sha256": corpus["manifest_sha256"],
    }
    config["config_sha256"] = digest(config)
    results = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": config["claim_ceiling"],
        "corpus_manifest_sha256": corpus["manifest_sha256"],
        "parity": {"all_passed": True, "max_abs_logit_delta": 0.0},
    }
    results["results_sha256"] = digest(results)
    receipt = {
        "state_slice": STATE_SLICE,
        "claim_ceiling": config["claim_ceiling"],
        "config_sha256": config["config_sha256"],
        "results_sha256": results["results_sha256"],
        "model_manifest_sha256": manifest["manifest_sha256"],
        "corpus_manifest_sha256": corpus["manifest_sha256"],
        "zero_alpha_parity_passed": True,
        "network_access": False,
        "training": False,
        "weights_frozen": True,
        "deterministic_repeat_passed": True,
        "performance_improved_on_assessment": False,
    }
    receipt["receipt_sha256"] = digest(receipt)
    (root / "config.json").write_text(json.dumps(config), encoding="utf-8")
    (root / "corpus-manifest.json").write_text(json.dumps(corpus), encoding="utf-8")
    (root / "results.json").write_text(json.dumps(results), encoding="utf-8")
    (root / "model-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (root / "receipt.json").write_text(json.dumps(receipt), encoding="utf-8")


def test_corpus_is_document_disjoint_and_exactly_sized():
    fit, assessment, manifest = corpus_texts_and_manifest()
    assert len(fit) == 12
    assert len(assessment) == 12
    assert set(FIT_FILES).isdisjoint(ASSESSMENT_FILES)
    assert manifest["manifest"]["extractor"] == EXTRACTOR
    assert manifest["manifest"]["fit_sequence_count"] == 12
    assert manifest["manifest"]["assessment_sequence_count"] == 12


def test_corpus_manifest_has_no_raw_text():
    _, _, manifest = corpus_texts_and_manifest()
    serialized = json.dumps(manifest)
    assert "A state tracker updates" not in serialized
    assert all("text_sha256" in unit for source in manifest["manifest"]["fit_sources"] for unit in source["units"])


def test_validator_accepts_current_source_bound_synthetic_artifact(tmp_path):
    _valid_artifact(tmp_path)
    assert validate(tmp_path)["valid"] is True


def test_validator_rejects_corpus_manifest_drift(tmp_path):
    _valid_artifact(tmp_path)
    path = tmp_path / "corpus-manifest.json"
    corpus = json.loads(path.read_text())
    corpus["manifest"]["extractor"] = "tampered"
    path.write_text(json.dumps(corpus))
    with pytest.raises(ValueError, match="corpus manifest digest mismatch"):
        validate(tmp_path)
