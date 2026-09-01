"""Hermetic contract tests for state slice continual-learning-gemma3-fineweb-edu-replication-v3."""

from __future__ import annotations

import json
import socket
import subprocess

import pytest

from experiments.continual_learning import (
    gemma3_fineweb_edu_replication_v3_contract as contract,
    stage_and_run_gemma3_fineweb_edu_replication_v3 as runner,
    validate_gemma3_fineweb_edu_replication_v3 as validator,
)


class CharacterTokenizer:
    def encode(self, text, add_special_tokens=False):
        return [ord(character) for character in text]

    def decode(self, token_ids):
        return "".join(chr(token_id) for token_id in token_ids)


def test_v3_protocol_is_distinct_and_hash_is_frozen():
    assert contract.STATE_SLICE == "continual-learning-gemma3-fineweb-edu-replication-v3"
    assert contract.PROTOCOL_SHA256 == contract.sha256_file(contract.PROTOCOL_PATH)
    assert contract.PROTOCOL_SHA256 != "580d3890668303e870184e910e0c0cd2098ddb6064b89da565385489e7e71564"
    assert contract.FRESH_ROW_START == 2048
    assert contract.FRESH_ROW_END == 18432
    assert contract.FIT_WINDOW_COUNT == contract.ASSESSMENT_WINDOW_COUNT == 64
    assert contract.CANDIDATE_PAIRS == ((7, 2), (9, 3), (11, 4), (12, 5))


def test_bootstrap_is_exact_counter_hash_and_nearest_rank():
    result = contract.bootstrap_mean_ci([1.0, 3.0])
    assert result["mean_delta"] == 2.0
    assert result["lower"] == 1.0
    assert result["upper"] == 3.0
    assert result["resamples"] == 10_000
    assert result["seed"] == 20260829
    assert result["percentile"] == "nearest-rank-1-indexed"
    assert result == contract.bootstrap_mean_ci([1.0, 3.0])
    assert contract.decide_replication({"mean_delta": -0.2, "upper": -0.01}) == "ReplicationCandidate"
    assert contract.decide_replication({"mean_delta": -0.2, "upper": 0.0}) == "NoCandidate"


def test_bootstrap_rejects_nonfinite_and_bool_inputs():
    with pytest.raises(ValueError, match="finite"):
        contract.bootstrap_mean_ci([float("nan")])
    with pytest.raises(ValueError, match="finite"):
        contract.bootstrap_mean_ci([True])


def test_external_and_model_paths_are_fail_closed(tmp_path):
    with pytest.raises(ValueError, match="outside the repository"):
        contract.external(contract.REPO_ROOT / "v3-result", "result root")
    wrong_model = tmp_path / "model"
    wrong_model.mkdir()
    with pytest.raises(ValueError, match="model path mismatch"):
        contract.model_manifest(wrong_model)
    symlink = tmp_path / "model-link"
    symlink.symlink_to(wrong_model, target_is_directory=True)
    with pytest.raises(ValueError, match="must not be a symlink"):
        contract.model_manifest(symlink)


def test_window_selection_requires_roundtrip_and_exact_shape(tmp_path):
    tokenizer = CharacterTokenizer()
    rows = [{
        "document_id": "doc-1",
        "text": "x" * 1024,
        "source_row_index": 2048,
        "source_path": "data/file.parquet",
    }]
    entries = runner._stage_windows(tmp_path, "fit", rows, tokenizer, 1)
    assert entries[0]["token_count"] == 1024
    assert (tmp_path / entries[0]["path"]).read_text(encoding="utf-8") == "x" * 1024
    with pytest.raises(ValueError, match="produced 0 windows"):
        runner._stage_windows(tmp_path / "short", "fit", [{**rows[0], "text": "x" * 100}], tokenizer, 1)


def test_network_block_denies_python_network_and_subprocess_and_restores():
    original_socket = socket.socket
    original_create_connection = socket.create_connection
    original_popen = subprocess.Popen
    with pytest.raises(RuntimeError, match="network access is disabled"):
        with contract.network_block():
            socket.create_connection(("example.invalid", 443))
    assert socket.socket is original_socket
    assert socket.create_connection is original_create_connection
    assert subprocess.Popen is original_popen


def test_normalized_record_contract_is_explicit():
    values = {"text": ["hello"], "id": ["doc-1"], "score": [1.5]}
    row = validator._normalized_from_values(values, {"crawl": "crawl", "path": "data/file.parquet"}, 2048, 0)
    assert row == {
        "document_id": "fineweb-edu:crawl:doc-1",
        "text": "hello",
        "metadata": {"id": "doc-1", "score": 1.5},
        "source_crawl": "crawl",
        "source_path": "data/file.parquet",
        "source_row_index": 2048,
    }


def test_result_metric_validation_rejects_bool_counts():
    ids = {"doc-1"}
    text_sha = {"doc-1": "a" * 64}
    metrics = {
        "mean_nll": 1.0,
        "perplexity": 2.718281828,
        "target_tokens": True,
        "rows": [{
            "dataset": "fineweb_edu",
            "document_id": "doc-1",
            "window_ordinal": 0,
            "text_sha256": text_sha["doc-1"],
            "token_count": 1024,
            "target_count": 1023,
            "nll": 1023.0,
        }],
    }
    with pytest.raises(ValueError, match="target token count"):
        validator._validate_metrics(metrics, ids, text_sha, "metrics")


def test_review_receipt_requires_identity_and_acceptance(tmp_path):
    receipt = {
        "schema": contract.REVIEW_SCHEMA,
        "state_slice": contract.STATE_SLICE,
        "claim_ceiling": contract.CLAIM_CEILING,
        "protocol_sha256": contract.PROTOCOL_SHA256,
        "review_packet_sha256": contract.sha256_file(contract.REVIEW_PACKET_PATH),
        "implementation_manifest_sha256": validator.implementation_manifest()["manifest_sha256"],
        "review_status": "ACCEPT",
        "effects_run": False,
        "findings": {key: True for key in contract.REVIEW_FINDINGS},
    }
    receipt["receipt_digest_sha256"] = contract.digest(receipt)
    path = tmp_path / "review.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="identity"):
        validator.validate_review_receipt(path)


def test_implementation_manifest_is_digest_bound_and_complete():
    manifest = validator.implementation_manifest()
    assert manifest["manifest"]["state_slice"] == contract.STATE_SLICE
    assert len(manifest["manifest"]["files"]) == 7
    assert manifest["manifest_sha256"] == contract.digest(manifest["manifest"])
