"""Hermetic V8 contract tests.

State slice: continual-learning-gemma3-fineweb-edu-replication-v8.
These tests do not load a model, acquire data, or run scientific effects.
"""

from __future__ import annotations

import ast
import inspect
import json
import os
import socket
from pathlib import Path

import pytest

from experiments.continual_learning import (
    gemma3_fineweb_edu_replication_v8_contract as c,
)
from experiments.continual_learning import (
    validate_gemma3_fineweb_edu_replication_v8 as v,
)


class CharacterTokenizer:
    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        assert add_special_tokens is False
        return [ord(character) for character in text]

    def decode(self, token_ids: list[int] | tuple[int, ...]) -> str:
        return "".join(chr(token_id) for token_id in token_ids)


def window(tmp_path: Path) -> v.Window:
    text = "a" * c.WINDOW_TOKENS
    path = tmp_path / "window.txt"
    path.write_text(text, encoding="utf-8")
    import hashlib

    encoded = text.encode()
    entry = {
        "dataset": "fineweb_edu",
        "document_id": "doc-1",
        "path": "window.txt",
        "window_ordinal": 0,
        "byte_len": len(encoded),
        "source_sha256": "b" * 64,
        "text_sha256": hashlib.sha256(encoded).hexdigest(),
        "token_count": c.WINDOW_TOKENS,
    }
    return v.parse_window(tmp_path, entry, CharacterTokenizer(), "fit")


def test_locked_constants_and_exact_bootstrap() -> None:
    assert c.STATE_SLICE.endswith("v8")
    assert c.CANDIDATE_PAIRS == ((7, 2), (9, 3), (11, 4), (12, 5))
    assert (c.FIT_ALPHA, c.FIT_BETA, c.EVALUATION_ALPHA, c.EVALUATION_BETA) == (
        0.10,
        0.90,
        0.15,
        0.85,
    )
    result = c.bootstrap_mean_ci([-0.1, 0.2, -0.3])
    assert result["resamples"] == 10_000 and result["seed"] == 20_260_829
    assert result == c.bootstrap_mean_ci([-0.1, 0.2, -0.3])
    with pytest.raises(ValueError):
        c.bootstrap_mean_ci([True])


def test_exact_file_set_and_parent_symlink_rejection(tmp_path: Path) -> None:
    (tmp_path / "required.txt").write_text("ok", encoding="utf-8")
    c.exact_file_set(tmp_path, {"required.txt"}, "test root")
    (tmp_path / "extra.txt").write_text("no", encoding="utf-8")
    with pytest.raises(ValueError):
        c.exact_file_set(tmp_path, {"required.txt"}, "test root")
    (tmp_path / "extra.txt").unlink()
    (tmp_path / "link.txt").symlink_to(tmp_path / "required.txt")
    with pytest.raises(ValueError):
        c.exact_file_set(tmp_path, {"required.txt"}, "test root")
    real = tmp_path / "real"
    real.mkdir()
    target = real / "file"
    target.write_text("x", encoding="utf-8")
    parent = tmp_path / "parent"
    parent.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError):
        c.regular(parent / "file", "symlinked parent")


def test_parse_window_recomputes_bytes_and_token_shape(tmp_path: Path) -> None:
    parsed = window(tmp_path)
    assert parsed.token_count == c.WINDOW_TOKENS
    (tmp_path / "window.txt").write_text("b" * (c.WINDOW_TOKENS - 1), encoding="utf-8")
    entry = {
        "dataset": "fineweb_edu",
        "document_id": "doc-1",
        "path": "window.txt",
        "window_ordinal": 0,
        "byte_len": parsed.byte_len,
        "source_sha256": parsed.source_sha256,
        "text_sha256": parsed.text_sha256,
        "token_count": c.WINDOW_TOKENS,
    }
    with pytest.raises(ValueError):
        v.parse_window(tmp_path, entry, CharacterTokenizer(), "fit")


def test_metrics_reject_boolean_and_recompute_provenance(tmp_path: Path) -> None:
    parsed = window(tmp_path)
    import math

    metrics = {
        "temperature": 1.0,
        "evaluation_config": None,
        "mean_nll": round(2.0 / 1023, 9),
        "perplexity": round(math.exp(round(2.0 / 1023, 9)), 9),
        "target_tokens": 1023,
        "rows": [
            {
                "dataset": "fineweb_edu",
                "document_id": "doc-1",
                "relative_path": "window.txt",
                "window_ordinal": 0,
                "source_sha256": "b" * 64,
                "text_sha256": parsed.text_sha256,
                "token_count": 1024,
                "target_count": 1023,
                "nll": 2.0,
            }
        ],
    }
    assert v.metrics(metrics, [parsed], "test metrics", 1.0, None) == metrics
    with pytest.raises(ValueError):
        v.metrics({**metrics, "mean_nll": True}, [parsed], "test metrics", 1.0, None)
    with pytest.raises(ValueError):
        v.metrics(
            {**metrics, "rows": [{**metrics["rows"][0], "source_sha256": "c" * 64}]},
            [parsed],
            "test metrics",
            1.0,
            None,
        )


def test_review_is_mandatory_and_loaders_guard_before_import() -> None:
    assert (
        inspect.signature(v.validate_source).parameters["receipt"].default
        is inspect.Parameter.empty
    )
    source = Path(
        "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v8.py"
    ).read_text(encoding="utf-8")
    for function_name, import_text, guard_text in (
        (
            "load_tokenizer",
            "from mlx_lm.utils import load_tokenizer",
            "V8 tokenizer custody/runtime mismatch",
        ),
        (
            "load_runtime",
            "from mlx_lm import load",
            "V8 model custody/runtime mismatch",
        ),
    ):
        start = source.index(f"def {function_name}")
        end = source.find("\ndef ", start + 5)
        block = source[start:] if end < 0 else source[start:end]
        assert block.index(guard_text) < block.index(import_text)


def test_network_block_covers_dns_socket_and_process_escape() -> None:
    with c.network_block():
        for operation in (
            lambda: socket.create_connection(("example.invalid", 443)),
            lambda: socket.getaddrinfo("example.invalid", 443),
            lambda: socket.gethostbyname("example.invalid"),
            lambda: socket.socket().sendall(b"blocked"),
            lambda: socket.socket().sendfile(None),
            lambda: os.fork(),
        ):
            with pytest.raises(RuntimeError):
                operation()
    assert socket.create_connection is not None


def test_native_network_guard_fails_closed_off_macos(monkeypatch) -> None:
    monkeypatch.setattr(c.os.sys, "platform", "linux")
    assert c.native_network_denied() is False


def test_v8_contract_references_are_defined() -> None:
    for relative in (
        "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v8.py",
        "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v8.py",
    ):
        tree = ast.parse(Path(relative).read_text(encoding="utf-8"))
        referenced = {
            node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "c"
        }
        assert not (referenced - set(dir(c)))


def test_manifest_pin_uses_recorded_self_digest(tmp_path: Path) -> None:
    body = {"schema": "test"}
    manifest = {**body, "manifest_sha256": c.digest(body)}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    assert v.pinned_manifest(path, manifest["manifest_sha256"], "test") == manifest
    with pytest.raises(ValueError):
        v.pinned_manifest(path, "0" * 64, "test")


def test_public_result_validator_requires_invocation_snapshot() -> None:
    parameters = inspect.signature(v.validate_result).parameters
    assert parameters["receipt"].default is inspect.Parameter.empty
    assert parameters["corpus_sha"].default is inspect.Parameter.empty
    assert parameters["invocation_snapshot_sha"].default is inspect.Parameter.empty


def test_publication_rechecks_exact_contents(tmp_path: Path) -> None:
    staging, final = tmp_path / "staging", tmp_path / "final"
    staging.mkdir()
    (staging / "required.txt").write_text("stable", encoding="utf-8")
    c.publish_no_replace(staging, final, {"required.txt"}, "test publication")
    assert (final / "required.txt").read_text(encoding="utf-8") == "stable"
    second = tmp_path / "second"
    second.mkdir()
    (second / "required.txt").write_text("stable", encoding="utf-8")
    with pytest.raises(FileExistsError):
        c.publish_no_replace(second, final, {"required.txt"}, "test publication")


def test_prior_rejection_history_is_pinned() -> None:
    observed = c.validate_prior_history()
    assert len(observed) == 14
    assert observed[0]["path"].endswith(
        "v1-independent-review-rejection-2026-08-30.json"
    )
