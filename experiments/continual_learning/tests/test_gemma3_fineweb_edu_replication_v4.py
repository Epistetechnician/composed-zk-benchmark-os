"""Hermetic tests for state slice continual-learning-gemma3-fineweb-edu-replication-v4."""

from __future__ import annotations

import json
import socket
import subprocess

import pytest

from experiments.continual_learning import (
    gemma3_fineweb_edu_replication_v4_contract as contract,
    stage_and_run_gemma3_fineweb_edu_replication_v4 as runner,
    validate_gemma3_fineweb_edu_replication_v4 as validator,
)


class CharacterTokenizer:
    def encode(self, text, add_special_tokens=False):
        return [ord(character) for character in text]

    def decode(self, token_ids):
        return "".join(chr(token_id) for token_id in token_ids)


def test_v4_protocol_is_frozen_and_distinct_from_rejected_revisions():
    assert contract.STATE_SLICE == "continual-learning-gemma3-fineweb-edu-replication-v4"
    assert contract.PROTOCOL_SHA256 == contract.sha256_file(contract.PROTOCOL_PATH)
    assert contract.PROTOCOL_SHA256 != "5c9c8e0b6ede43bde9fa66a98fb515b597fafa2f3ebcd811c1925ca5a457b8f7"
    assert contract.FRESH_ROW_START == 2048
    assert contract.FRESH_ROW_END == 18432
    assert contract.CANDIDATE_PAIRS == ((7, 2), (9, 3), (11, 4), (12, 5))
    assert contract.FIT_ALPHA + contract.FIT_BETA == 1.0
    assert contract.EVALUATION_ALPHA + contract.EVALUATION_BETA == 1.0


def test_bootstrap_is_exact_counter_hash_nearest_rank_and_strict():
    result = contract.bootstrap_mean_ci([1.0, 3.0])
    assert result["mean_delta"] == 2.0
    assert result["lower"] == 1.0
    assert result["upper"] == 3.0
    assert result["resamples"] == 10_000
    assert result == contract.bootstrap_mean_ci([1.0, 3.0])
    assert contract.decide_replication({"mean_delta": -0.1, "upper": -0.01}) == "ReplicationCandidate"
    assert contract.decide_replication({"mean_delta": -0.1, "upper": 0.0}) == "NoCandidate"
    with pytest.raises(ValueError, match="finite"):
        contract.bootstrap_mean_ci([True])


def test_exact_root_and_model_tree_symlink_guards(tmp_path):
    with pytest.raises(ValueError, match="exact path"):
        contract.exact_path(tmp_path, contract.CORPUS_ROOT, "V4 corpus root")
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        contract._reject_symlink_components(link, "test path")


def test_window_parser_retokenizes_and_rejects_wrong_shape(tmp_path):
    tokenizer = CharacterTokenizer()
    path = tmp_path / "fit/fineweb_edu/window-000000.txt"
    path.parent.mkdir(parents=True)
    path.write_text("x" * 1024, encoding="utf-8")
    entry = {"dataset": "fineweb_edu", "document_id": "doc-1", "path": "fit/fineweb_edu/window-000000.txt", "window_ordinal": 0, "byte_len": 1024, "source_sha256": "a" * 64, "text_sha256": contract.sha256_file(path), "token_count": 1024}
    window = validator.parse_window(tmp_path, entry, tokenizer, "fit")
    assert window.token_count == 1024
    assert window.token_ids == tuple(ord("x") for _ in range(1024))
    entry["token_count"] = 1023
    with pytest.raises(ValueError, match="digest/shape"):
        validator.parse_window(tmp_path, entry, tokenizer, "fit")


def test_explicit_beta_contract_is_enforced():
    config = runner.RecirculationConfig(11, 4, contract.EVALUATION_ALPHA, contract.EVALUATION_BETA)
    config.validate(26)
    with pytest.raises(ValueError, match="alpha/beta"):
        runner.RecirculationConfig(11, 4, contract.EVALUATION_ALPHA, 0.9).validate(26)


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


def test_metric_validator_recomputes_aggregate_and_rejects_bool_count():
    ids = {"doc-1"}
    text_sha = {"doc-1": "a" * 64}
    metrics = {"temperature": 1.0, "evaluation_config": None, "mean_nll": 1.0, "perplexity": round(2.718281828459045, 9), "target_tokens": 1023, "rows": [{"dataset": "fineweb_edu", "document_id": "doc-1", "window_ordinal": 0, "text_sha256": text_sha["doc-1"], "token_count": 1024, "target_count": 1023, "nll": 1023.0}]}
    assert validator._validate_metrics(metrics, ids, text_sha, "metrics", 1.0, None) == metrics
    metrics["mean_nll"] = 1.1
    with pytest.raises(ValueError, match="aggregate"):
        validator._validate_metrics(metrics, ids, text_sha, "metrics", 1.0, None)
    metrics["mean_nll"] = 1.0
    metrics["target_tokens"] = True
    with pytest.raises(ValueError, match="target token"):
        validator._validate_metrics(metrics, ids, text_sha, "metrics", 1.0, None)


def test_review_receipt_requires_identity_and_all_v4_bindings(tmp_path):
    receipt = {"schema": contract.REVIEW_SCHEMA, "state_slice": contract.STATE_SLICE, "claim_ceiling": contract.CLAIM_CEILING, "review_status": "ACCEPT", "effects_run": False, "protocol_sha256": contract.PROTOCOL_SHA256, "review_packet_sha256": contract.sha256_file(contract.REVIEW_PACKET_PATH), "implementation_manifest_sha256": validator.implementation_manifest()["manifest_sha256"], "reviewed_files": [path.relative_to(contract.REPO_ROOT).as_posix() for path in contract.IMPLEMENTATION_FILES], "findings": {key: True for key in contract.REVIEW_FINDINGS}}
    receipt["receipt_digest_sha256"] = contract.digest(receipt)
    path = tmp_path / "review.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    with pytest.raises(ValueError, match="identity"):
        validator.validate_review_receipt(path)


def test_validator_cli_has_explicit_mode_contract():
    assert "--mode" in validator.main.__code__.co_consts


def test_implementation_manifest_is_digest_bound():
    manifest = validator.implementation_manifest()
    assert manifest["manifest"]["state_slice"] == contract.STATE_SLICE
    assert len(manifest["manifest"]["files"]) == 7
    assert manifest["manifest_sha256"] == contract.digest(manifest["manifest"])
