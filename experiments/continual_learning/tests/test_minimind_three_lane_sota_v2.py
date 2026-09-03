"""Hermetic tests for state slice continual-learning-minimind-three-lane-sota-v2."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning import minimind_three_lane_sota_v2 as harness


def test_synthetic_campaign_is_deterministic_and_assesses_every_arm() -> None:
    first = harness.run_synthetic_campaign()
    second = harness.run_synthetic_campaign()
    assert first == second
    assert len(first["aggregate_trials"]) == 540
    assert first["phase_order"] == ["fit", "tune", "prediction_lock", "assessment"]
    for lane in harness.LANES:
        arms = harness._expected_arms(lane)
        assert set(first["prediction_locks"][lane]) == set(arms)
        for arm in arms:
            rows = [row for row in first["aggregate_trials"] if row["lane"] == lane and row["arm"] == arm]
            assert {row["split"] for row in rows} == set(harness.SPLITS)
            assert len(rows) == 18


def test_ordering_is_seeded_and_reverse_is_exact_reversal() -> None:
    forward = harness._ordered_items("task", 7301, "forward")
    reverse = harness._ordered_items("task", 7301, "reverse")
    assert list(forward) == list(reversed(reverse))
    assert forward != harness.TASKS


def test_fixture_corpus_has_disjoint_record_and_author_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    corpus_root = tmp_path / "corpus"
    source_manifest = tmp_path / "source.json"
    monkeypatch.setattr(harness, "CORPUS_ROOT", corpus_root)
    monkeypatch.setattr(harness, "CORPUS_MANIFEST_PATH", corpus_root / "corpus-manifest.json")
    monkeypatch.setattr(harness, "SOURCE_MANIFEST_PATH", source_manifest)
    manifest = harness._prepare_corpus()
    assert manifest["fixture_only"] is True
    assert len({entry["path"] for entry in manifest["files"]}) == 9
    record_ids = []
    author_ids = []
    for entry in manifest["files"]:
        for line in Path(entry["path"]).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            record_ids.append(row["record_id"])
            author_ids.append(row["author_id"])
    assert len(record_ids) == len(set(record_ids))
    assert len(author_ids) == len(set(author_ids))


def test_receipt_is_required_before_model_import(tmp_path: Path) -> None:
    with pytest.raises(harness.ProtocolError, match="execution receipt custody mismatch"):
        harness._validate_receipt(tmp_path / "missing.json", "source", "corpus")


def test_synthetic_contract_does_not_claim_published_benchmark() -> None:
    result = harness.run_synthetic_campaign()
    assert result["published_benchmark_reproduced"] is False
    assert result["real_local_corpus"] is False
    assert result["training_executed"] is False
    assert result["model_loaded"] is False


def test_experience_state_channels_are_explicit_and_accounted() -> None:
    texts = {"fit": ["software fit", "forecasting fit", "database fit"]}
    for arm in harness.EXPERIENCE_ARMS:
        context, reads, writes = harness._experience_context(arm, texts, harness.EXPERIENCE_TASKS, harness.EXPERIENCE_TASKS)
        assert isinstance(context, str)
        assert reads >= 0 and writes >= 0
    assert harness._experience_context("stateless", texts, harness.EXPERIENCE_TASKS, harness.EXPERIENCE_TASKS) == ("", 0, 0)
    assert harness._experience_context("naive_icl", texts, harness.EXPERIENCE_TASKS, harness.EXPERIENCE_TASKS)[1] == 3

