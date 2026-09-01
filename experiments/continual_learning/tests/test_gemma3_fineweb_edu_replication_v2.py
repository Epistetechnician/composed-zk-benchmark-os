"""Pure contract tests for state slice continual-learning-gemma3-fineweb-edu-replication-v2."""

from __future__ import annotations

import json
import socket

import pytest

from experiments.continual_learning import (
    stage_and_run_gemma3_fineweb_edu_replication_v2 as runner,
    validate_gemma3_fineweb_edu_replication_v2 as validator,
)


class CharacterTokenizer:
    def encode(self, text, add_special_tokens=False):
        return [ord(character) for character in text]

    def decode(self, token_ids):
        return "".join(chr(token_id) for token_id in token_ids)


def test_v2_is_distinct_and_protocol_hash_is_frozen():
    assert validator.STATE_SLICE == runner.STATE_SLICE
    assert validator.STATE_SLICE != "continual-learning-gemma3-fineweb-edu-replication-v1"
    assert validator.PROTOCOL_SHA256 == "580d3890668303e870184e910e0c0cd2098ddb6064b89da565385489e7e71564"
    assert validator.FRESH_ROW_START == 2048
    assert validator.FRESH_ROW_END == 18432
    assert validator.FIT_WINDOW_COUNT == validator.ASSESSMENT_WINDOW_COUNT == 64


def test_bootstrap_is_counter_hash_deterministic_with_nearest_rank():
    result = validator.bootstrap_mean_ci([1.0, 3.0], resamples=4, seed=1)
    assert result == {
        "mean_delta": 2.0,
        "lower": 1.0,
        "upper": 2.0,
        "resamples": 4,
        "seed": 1,
        "confidence": 0.95,
        "prng": "sha256-counter-v1",
        "statistic": "mean paired per-document NLL delta selected_minus_baseline",
        "percentile": "nearest-rank-1-indexed",
        "nonfinite": "reject",
    }
    assert result == validator.bootstrap_mean_ci([1.0, 3.0], resamples=4, seed=1)
    assert validator.decide_replication({"mean_delta": -0.2, "upper": -0.01}) == "ReplicationCandidate"
    assert validator.decide_replication({"mean_delta": -0.2, "upper": 0.0}) == "NoCandidate"


def test_bootstrap_rejects_nonfinite_values():
    with pytest.raises(ValueError, match="finite"):
        validator.bootstrap_mean_ci([float("nan")], resamples=2)


def test_external_paths_reject_repository():
    with pytest.raises(ValueError, match="outside the repository"):
        runner._external(runner.REPO_ROOT / "v2-result", "result root")


def test_window_selection_is_exactly_1024_tokens():
    tokenizer = CharacterTokenizer()
    assert runner._window_from_row(tokenizer, {"document_id": "short", "text": "x" * 100}, runner.Path("fit/window.txt")) is None
    window = runner._window_from_row(tokenizer, {"document_id": "long", "text": "y" * 1200}, runner.Path("fit/window.txt"))
    assert window is not None
    assert window.token_count == 1024
    assert len(tokenizer.encode(window.text, add_special_tokens=False)) == 1024


def test_network_block_denies_resolution_and_restores_process_state():
    original_socket = socket.socket
    original_create_connection = socket.create_connection
    with pytest.raises(RuntimeError, match="network access is disabled"):
        with runner.network_block():
            socket.create_connection(("example.invalid", 443))
    assert socket.socket is original_socket
    assert socket.create_connection is original_create_connection


def test_normalized_parquet_contract_is_explicit():
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


def test_review_receipt_requires_accept_and_all_findings(tmp_path):
    receipt = {
        "schema": validator.REVIEW_SCHEMA,
        "state_slice": validator.STATE_SLICE,
        "claim_ceiling": validator.CLAIM_CEILING,
        "protocol_sha256": validator.PROTOCOL_SHA256,
        "review_status": "REJECT",
        "effects_run": False,
        "findings": {key: True for key in validator.REVIEW_FINDINGS},
    }
    path = tmp_path / "review.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="ACCEPT"):
        validator.validate_review_receipt(path)


def test_per_document_delta_is_paired_and_normalized():
    rows = [
        {
            "document_id": f"doc-{index}",
            "target_count": 1023,
            "baseline_nll": 1023.0,
            "selected_nll": 1022.0,
            "delta_selected_minus_baseline": -1.0 / 1023.0,
        }
        for index in range(64)
    ]
    results = {"assessment_per_document": rows}
    assert validator._validate_result_rows(results, {f"doc-{index}" for index in range(64)}, set()) == [-1.0 / 1023.0] * 64
    rows[0]["delta_selected_minus_baseline"] = -1.0
    with pytest.raises(ValueError, match="paired delta"):
        validator._validate_result_rows(results, {f"doc-{index}" for index in range(64)}, set())


def test_implementation_manifest_is_digest_bound():
    manifest = validator.implementation_manifest()
    assert manifest["manifest"]["state_slice"] == validator.STATE_SLICE
    assert len(manifest["manifest"]["files"]) == 6
    assert manifest["manifest_sha256"] == validator.digest(manifest["manifest"])
