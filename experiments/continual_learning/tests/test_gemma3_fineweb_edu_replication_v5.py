"""Hermetic V5 contract tests.

State slice: continual-learning-gemma3-fineweb-edu-replication-v5.
These tests do not load a model, acquire data, or run scientific effects.
"""

from __future__ import annotations

import inspect
import socket
from pathlib import Path

import pytest

from experiments.continual_learning import gemma3_fineweb_edu_replication_v5_contract as c
from experiments.continual_learning import validate_gemma3_fineweb_edu_replication_v5 as validator


class CharacterTokenizer:
    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        assert add_special_tokens is False
        return [ord(character) for character in text]

    def decode(self, token_ids: list[int] | tuple[int, ...]) -> str:
        return "".join(chr(token_id) for token_id in token_ids)


def test_locked_constants_and_bootstrap_algorithm() -> None:
    assert c.CANDIDATE_PAIRS == ((7, 2), (9, 3), (11, 4), (12, 5))
    assert c.FIT_ALPHA == 0.10
    assert c.FIT_BETA == 0.90
    assert c.EVALUATION_ALPHA == 0.15
    assert c.EVALUATION_BETA == 0.85
    result = c.bootstrap_mean_ci([-0.1, 0.2, -0.3])
    assert result["resamples"] == 10_000
    assert result["seed"] == 20_260_829
    assert result == c.bootstrap_mean_ci([-0.1, 0.2, -0.3])
    with pytest.raises(ValueError):
        c.bootstrap_mean_ci([True])


def test_exact_file_set_rejects_extra_files_and_symlinks(tmp_path: Path) -> None:
    (tmp_path / "required.txt").write_text("ok", encoding="utf-8")
    c.exact_file_set(tmp_path, {"required.txt"}, "test root")
    (tmp_path / "extra.txt").write_text("no", encoding="utf-8")
    with pytest.raises(ValueError):
        c.exact_file_set(tmp_path, {"required.txt"}, "test root")
    (tmp_path / "extra.txt").unlink()
    (tmp_path / "link.txt").symlink_to(tmp_path / "required.txt")
    with pytest.raises(ValueError):
        c.exact_file_set(tmp_path, {"required.txt"}, "test root")


def test_parse_window_recomputes_actual_text_shape(tmp_path: Path) -> None:
    text = "a" * c.WINDOW_TOKENS
    path = tmp_path / "window.txt"
    path.write_text(text, encoding="utf-8")
    raw = {"dataset": "fineweb_edu", "document_id": "doc-1", "path": "window.txt", "window_ordinal": 0, "byte_len": len(text), "source_sha256": "a" * 64, "text_sha256": __import__("hashlib").sha256(text.encode()).hexdigest(), "token_count": c.WINDOW_TOKENS}
    window = validator.parse_window(tmp_path, raw, CharacterTokenizer(), "fit")
    assert window.token_count == c.WINDOW_TOKENS
    path.write_text("b" * (c.WINDOW_TOKENS - 1), encoding="utf-8")
    with pytest.raises(ValueError):
        validator.parse_window(tmp_path, raw, CharacterTokenizer(), "fit")


def test_metrics_reject_boolean_and_recompute_aggregates(tmp_path: Path) -> None:
    text = "a" * c.WINDOW_TOKENS
    path = tmp_path / "window.txt"
    path.write_text(text, encoding="utf-8")
    import hashlib
    digest = hashlib.sha256(text.encode()).hexdigest()
    raw = {"dataset": "fineweb_edu", "document_id": "doc-1", "path": "window.txt", "window_ordinal": 0, "byte_len": len(text), "source_sha256": "b" * 64, "text_sha256": digest, "token_count": c.WINDOW_TOKENS}
    window = validator.parse_window(tmp_path, raw, CharacterTokenizer(), "fit")
    metrics = {"temperature": 1.0, "evaluation_config": None, "mean_nll": round(2.0 / 1023, 9), "perplexity": round(__import__("math").exp(round(2.0 / 1023, 9)), 9), "target_tokens": 1023, "rows": [{"dataset": "fineweb_edu", "document_id": "doc-1", "relative_path": "window.txt", "window_ordinal": 0, "source_sha256": "b" * 64, "text_sha256": digest, "token_count": 1024, "target_count": 1023, "nll": 2.0}]}
    assert validator._validate_metrics(metrics, [window], "test metrics", 1.0, None) == metrics
    invalid = {**metrics, "mean_nll": True}
    with pytest.raises(ValueError):
        validator._validate_metrics(invalid, [window], "test metrics", 1.0, None)


def test_review_is_mandatory_and_public_loaders_guard_before_import() -> None:
    source_parameters = inspect.signature(validator.validate_source).parameters
    assert source_parameters["review_receipt"].default is inspect.Parameter.empty
    loader_source = Path("experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v5.py").read_text(encoding="utf-8")
    for function_name, import_text, guard_text in (("_load_tokenizer", "from mlx_lm.utils import load_tokenizer", "model manifest mismatch before tokenizer load"), ("load_runtime", "from mlx_lm import load", "model manifest mismatch before model load")):
        start = loader_source.index(f"def {function_name}")
        end = loader_source.find("\ndef ", start + 5)
        block = loader_source[start:] if end < 0 else loader_source[start:end]
        assert block.index(guard_text) < block.index(import_text)


def test_network_block_covers_python_outbound_surface() -> None:
    with c.network_block():
        with pytest.raises(RuntimeError):
            socket.create_connection(("example.invalid", 443))
        with pytest.raises(RuntimeError):
            socket.getaddrinfo("example.invalid", 443)
        with pytest.raises(RuntimeError):
            socket.socket().sendall(b"blocked")
    assert socket.create_connection is not None


def test_public_result_validator_requires_all_bindings() -> None:
    parameters = inspect.signature(validator.validate_result).parameters
    assert parameters["review_receipt"].default is inspect.Parameter.empty
    assert parameters["corpus_manifest_sha256"].default is inspect.Parameter.empty


def test_publication_rechecks_exact_contents(tmp_path: Path) -> None:
    staging = tmp_path / "staging"
    final = tmp_path / "final"
    staging.mkdir()
    (staging / "required.txt").write_text("stable", encoding="utf-8")
    c.publish_no_replace(staging, final, "test publication", {"required.txt"})
    assert (final / "required.txt").read_text(encoding="utf-8") == "stable"
    second_staging = tmp_path / "second-staging"
    second_staging.mkdir()
    (second_staging / "required.txt").write_text("stable", encoding="utf-8")
    with pytest.raises(FileExistsError):
        c.publish_no_replace(second_staging, final, "test publication", {"required.txt"})
