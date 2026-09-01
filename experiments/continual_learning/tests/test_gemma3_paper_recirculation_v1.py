from __future__ import annotations

import json

import pytest

from experiments.continual_learning.gemma3_paper_recirculation_v1 import (
    ALPHAS,
    ASSESSMENT_DATASETS,
    CORPUS_SCHEMA,
    FIT_DATASETS,
    PAIR_SELECTION_ALPHA,
    RecirculationConfig,
    candidate_configs,
    candidate_pairs,
    digest,
    _check_corpus_root_manifest,
    load_corpus,
    model_manifest,
)


def _write_corpus(root):
    fit = []
    for index, dataset in enumerate(FIT_DATASETS):
        relative = f"sources/fit/{index}.txt"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"fit text {dataset}", encoding="utf-8")
        fit.append(
            {
                "dataset": dataset,
                "document_id": f"fit-{index}",
                "path": relative,
                "window_ordinal": 0,
            }
        )
    assessment = []
    for index, dataset in enumerate(ASSESSMENT_DATASETS):
        relative = f"sources/assessment/{index}.txt"
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"assessment text {dataset}", encoding="utf-8")
        assessment.append(
            {
                "dataset": dataset,
                "document_id": f"assessment-{index}",
                "path": relative,
                "window_ordinal": 0,
            }
        )
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "schema": CORPUS_SCHEMA,
                "window_token_count": 1024,
                "fit": fit,
                "assessment": assessment,
            }
        ),
        encoding="utf-8",
    )


def test_paper_pair_grid_is_complete_and_bounded():
    pairs = candidate_pairs(26)
    assert len(pairs) == 234
    assert (11, 4) in pairs
    assert all(0 < source - destination <= 12 for source, destination in pairs)
    configs = candidate_configs(26, PAIR_SELECTION_ALPHA)
    assert len(configs) == 234
    assert all(config.alpha == PAIR_SELECTION_ALPHA for config in configs)


def test_candidate_configuration_rejects_out_of_bound_distance():
    with pytest.raises(ValueError, match="distance exceeds paper bound"):
        RecirculationConfig(13, 0, ALPHAS[0]).validate(26)
    with pytest.raises(ValueError, match="destination < source"):
        RecirculationConfig(4, 11, ALPHAS[0]).validate(26)


def test_external_corpus_manifest_is_digest_bound_and_raw_text_free(tmp_path):
    _write_corpus(tmp_path)
    fit, assessment, manifest = load_corpus(tmp_path, None, strict_shape=True)
    assert len(fit) == 3
    assert len(assessment) == 10
    serialized = json.dumps(manifest, sort_keys=True)
    assert "fit text arxiv" not in serialized
    assert manifest["manifest_sha256"] == digest(manifest["manifest"])
    assert manifest["manifest"]["fit_window_count"] == 3


def test_external_corpus_rejects_fit_assessment_document_reuse(tmp_path):
    _write_corpus(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    value = json.loads(manifest_path.read_text())
    value["assessment"][0]["document_id"] = value["fit"][0]["document_id"]
    manifest_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="document identity"):
        load_corpus(tmp_path, None, strict_shape=True)


def test_external_corpus_rejects_path_traversal(tmp_path):
    _write_corpus(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    value = json.loads(manifest_path.read_text())
    value["fit"][0]["path"] = "../outside.txt"
    manifest_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid external corpus path"):
        load_corpus(tmp_path, None, strict_shape=True)


def test_external_corpus_root_is_checked_before_runtime_load(tmp_path):
    with pytest.raises(FileNotFoundError, match="manifest.json"):
        _check_corpus_root_manifest(tmp_path / "missing-corpus")


def test_model_manifest_excludes_ephemeral_download_cache(tmp_path):
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / ".cache").mkdir()
    (tmp_path / ".cache" / "incomplete").write_text("volatile", encoding="utf-8")
    manifest = model_manifest(tmp_path)
    assert [item["path"] for item in manifest["manifest"]["files"]] == ["config.json"]
