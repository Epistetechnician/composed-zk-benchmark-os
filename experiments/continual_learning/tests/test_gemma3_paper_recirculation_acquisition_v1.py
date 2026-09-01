from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning import acquire_gemma3_paper_recirculation_v1 as acquisition
from experiments.continual_learning import validate_gemma3_paper_recirculation_acquisition_v1 as validator


def test_normalized_jsonl_is_exact_two_field_contract(tmp_path: Path):
    destination = tmp_path / "source.jsonl"
    count = acquisition._write_jsonl(destination, [("doc-1", "alpha\nβeta")])
    assert count == 1
    assert destination.read_text(encoding="utf-8") == '{"document_id":"doc-1","text":"alpha\\nβeta"}\n'


def test_normalization_rejects_duplicate_ids(tmp_path: Path):
    with pytest.raises(ValueError, match="duplicate normalized document id"):
        acquisition._write_jsonl(tmp_path / "source.jsonl", [("doc-1", "a"), ("doc-1", "b")])


def test_manual_inputs_are_required_before_network_acquisition(tmp_path: Path):
    with pytest.raises(RuntimeError, match="both documented manual inputs"):
        acquisition.acquire(tmp_path / "raw", tmp_path / "source", None, None)


def test_missing_manual_file_fails_before_raw_root_creation(tmp_path: Path):
    c4 = tmp_path / "c4"
    newsroom = tmp_path / "newsroom"
    c4.mkdir()
    newsroom.mkdir()
    with pytest.raises(FileNotFoundError, match="C4 manual root"):
        acquisition.acquire(tmp_path / "raw", tmp_path / "source", c4, newsroom)
    assert not (tmp_path / "raw").exists()


def test_gov_report_sections_are_flattened_in_order():
    value = {
        "section_title": "Root",
        "paragraphs": ["first"],
        "subsections": [
            {"section_title": "Child", "paragraphs": ["second"], "subsections": []}
        ],
    }
    assert acquisition._gov_report_text(value) == "Root\nfirst\nChild\nsecond"


def test_validator_rejects_manifest_digest_tampering(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    manifest = {
        "schema": validator.MANIFEST_SCHEMA,
        "source_record_schema": validator.SOURCE_RECORD_SCHEMA,
        "state_slice": validator.CONSUMER_STATE_SLICE,
        "acquisition_state_slice": validator.ACQUISITION_STATE_SLICE,
        "selection_policy": "fixed-upstream-order-v1",
        "network_access": True,
        "training": False,
        "scientific_execution": False,
        "evidence_ledger_mutation": False,
        "datasets": {},
        "raw_artifacts": [],
        "paper": "https://arxiv.org/html/2608.17981v1",
    }
    manifest["manifest_sha256"] = acquisition.digest(manifest)
    manifest["paper"] = "https://example.invalid/tampered"
    (root / "acquisition-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest digest mismatch"):
        validator.validate(root)


def test_external_path_rejects_repository_targets():
    with pytest.raises(ValueError, match="outside the repository"):
        acquisition._external_path(acquisition.REPO_ROOT / "generated", "source root")
