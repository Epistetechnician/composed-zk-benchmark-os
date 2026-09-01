"""Hermetic V29 contract tests.

State slice: continual-learning-gemma3-fineweb-edu-replication-v29.
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
    gemma3_fineweb_edu_replication_v29_contract as c,
)
from experiments.continual_learning import (
    validate_gemma3_fineweb_edu_replication_v29 as v,
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
    assert c.STATE_SLICE.endswith("v29")
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


def test_parse_window_rejects_non_prefix_of_claimed_source_row(tmp_path: Path) -> None:
    import hashlib

    source_text = "a" * c.WINDOW_TOKENS
    window_text = "b" * c.WINDOW_TOKENS
    path = tmp_path / "window.txt"
    path.write_text(window_text, encoding="utf-8")
    encoded = window_text.encode()
    entry = {
        "dataset": "fineweb_edu",
        "document_id": "doc-1",
        "path": "window.txt",
        "window_ordinal": 0,
        "byte_len": len(encoded),
        "source_sha256": hashlib.sha256(source_text.encode()).hexdigest(),
        "text_sha256": hashlib.sha256(encoded).hexdigest(),
        "token_count": c.WINDOW_TOKENS,
    }
    with pytest.raises(ValueError, match="source-row prefix"):
        v.parse_window(
            tmp_path,
            entry,
            CharacterTokenizer(),
            "fit",
            expected_source_row={"text": source_text},
        )


def test_metrics_rejects_reordered_rows(tmp_path: Path) -> None:
    from dataclasses import replace

    first = window(tmp_path)
    second = replace(first, document_id="doc-2", relative_path="second.txt")

    def row(item: v.Window, nll: float) -> dict[str, object]:
        return {
            "dataset": item.dataset,
            "document_id": item.document_id,
            "relative_path": item.relative_path,
            "window_ordinal": 0,
            "source_sha256": item.source_sha256,
            "text_sha256": item.text_sha256,
            "token_count": c.WINDOW_TOKENS,
            "target_count": c.WINDOW_TOKENS - 1,
            "nll": nll,
        }

    value = {
        "temperature": 1.0,
        "evaluation_config": None,
        "mean_nll": 0.0,
        "perplexity": 1.0,
        "target_tokens": 2 * (c.WINDOW_TOKENS - 1),
        "rows": [row(second, 2.0), row(first, 1.0)],
    }
    with pytest.raises(ValueError, match="row order"):
        v.metrics(value, [first, second], "ordered metrics", 1.0, None)


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
        "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    for function_name, import_text, guard_text in (
        (
            "load_tokenizer",
            "from mlx_lm.utils import load_tokenizer",
            "V29 tokenizer custody/runtime mismatch",
        ),
        (
            "load_runtime",
            "from mlx_lm import load",
            "V29 model custody/runtime mismatch",
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


def test_network_block_covers_all_process_launch_variants() -> None:
    names = tuple(
        name
        for name in dir(os)
        if (
            name.startswith("exec")
            or name.startswith("spawn")
            or name in ("posix_spawn", "posix_spawnp", "fork", "forkpty", "startfile")
        )
        and callable(getattr(os, name, None))
    )
    with c.network_block():
        for name in names:
            with pytest.raises(RuntimeError):
                getattr(os, name)()


def test_native_network_guard_fails_closed_off_macos(monkeypatch) -> None:
    monkeypatch.setattr(c.os.sys, "platform", "linux")
    assert c.native_network_denied() is False


def test_v29_contract_references_are_defined() -> None:
    for relative in (
        "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v29.py",
        "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v29.py",
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


def test_enriched_review_snapshot_projects_canonical_fields(monkeypatch) -> None:
    from experiments.continual_learning import (
        stage_and_run_gemma3_fineweb_edu_replication_v29 as runner,
    )

    observed = {}
    monkeypatch.setattr(runner.c, "assert_code_snapshot", observed.update)
    enriched = {
        "protocol": object(),
        "packet": object(),
        "receipt": object(),
        "implementation": object(),
        "history": object(),
        "review_sha256": "x" * 64,
        "review": {"review_decision": "ACCEPT"},
    }
    runner._assert_review(enriched)
    assert set(observed) == {"protocol", "packet", "receipt", "implementation", "history"}


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
    assert len(observed) == 82
    paths = {item["path"] for item in observed}
    assert {
        "docs/research/continual-learning/143-gemma3-fineweb-edu-replication-v1-protocol.md",
        "docs/research/continual-learning/144-gemma3-fineweb-edu-replication-v1-review-packet.md",
        "docs/research/continual-learning/176-gemma3-fineweb-edu-replication-v12-protocol.md",
        "docs/research/continual-learning/177-gemma3-fineweb-edu-replication-v12-review-packet.md",
        "docs/research/continual-learning/178-gemma3-fineweb-edu-replication-v12-independent-review-rejection-2026-08-30.json",
        "docs/research/continual-learning/179-gemma3-fineweb-edu-replication-v13-protocol.md",
        "docs/research/continual-learning/180-gemma3-fineweb-edu-replication-v13-review-packet.md",
        "docs/research/continual-learning/181-gemma3-fineweb-edu-replication-v13-independent-review-2026-08-30.json",
        "docs/research/continual-learning/182-gemma3-fineweb-edu-replication-v13-execution-failure-2026-08-30.json",
        "docs/research/continual-learning/183-gemma3-fineweb-edu-replication-v14-protocol.md",
        "docs/research/continual-learning/184-gemma3-fineweb-edu-replication-v14-review-packet.md",
        "docs/research/continual-learning/185-gemma3-fineweb-edu-replication-v14-independent-review-2026-08-30.json",
        "docs/research/continual-learning/186-gemma3-fineweb-edu-replication-v14-execution-failure-2026-08-30.json",
        "docs/research/continual-learning/187-gemma3-fineweb-edu-replication-v15-protocol.md",
        "docs/research/continual-learning/188-gemma3-fineweb-edu-replication-v15-review-packet.md",
        "docs/research/continual-learning/189-gemma3-fineweb-edu-replication-v15-independent-review-rejection-2026-08-31.json",
        "docs/research/continual-learning/190-gemma3-fineweb-edu-replication-v16-protocol.md",
        "docs/research/continual-learning/191-gemma3-fineweb-edu-replication-v16-review-packet.md",
        "docs/research/continual-learning/192-gemma3-fineweb-edu-replication-v16-independent-review-rejection-2026-08-31.json",
        "docs/research/continual-learning/193-gemma3-fineweb-edu-replication-v17-protocol.md",
        "docs/research/continual-learning/194-gemma3-fineweb-edu-replication-v17-review-packet.md",
        "docs/research/continual-learning/196-gemma3-fineweb-edu-replication-v17-independent-review-rejection-2026-08-31.json",
        "docs/research/continual-learning/197-gemma3-fineweb-edu-replication-v18-protocol.md",
        "docs/research/continual-learning/198-gemma3-fineweb-edu-replication-v18-review-packet.md",
        "docs/research/continual-learning/200-gemma3-fineweb-edu-replication-v18-independent-review-rejection-2026-08-31.json",
        "docs/research/continual-learning/201-gemma3-fineweb-edu-replication-v19-protocol.md",
        "docs/research/continual-learning/202-gemma3-fineweb-edu-replication-v19-review-packet.md",
        "docs/research/continual-learning/204-gemma3-fineweb-edu-replication-v19-independent-review-rejection-2026-08-31.json",
        "docs/research/continual-learning/205-gemma3-fineweb-edu-replication-v20-protocol.md",
        "docs/research/continual-learning/206-gemma3-fineweb-edu-replication-v20-review-packet.md",
        "docs/research/continual-learning/208-gemma3-fineweb-edu-replication-v20-independent-review-rejection-2026-08-31.json",
        "docs/research/continual-learning/209-gemma3-fineweb-edu-replication-v21-protocol.md",
        "docs/research/continual-learning/210-gemma3-fineweb-edu-replication-v21-review-packet.md",
        "docs/research/continual-learning/212-gemma3-fineweb-edu-replication-v21-independent-review-rejection-2026-08-31.json",
        "docs/research/continual-learning/213-gemma3-fineweb-edu-replication-v22-protocol.md",
        "docs/research/continual-learning/214-gemma3-fineweb-edu-replication-v22-review-packet.md",
        "docs/research/continual-learning/216-gemma3-fineweb-edu-replication-v22-independent-review-rejection-2026-08-31.json",
        "docs/research/continual-learning/217-gemma3-fineweb-edu-replication-v23-protocol.md",
        "docs/research/continual-learning/218-gemma3-fineweb-edu-replication-v23-review-packet.md",
        "docs/research/continual-learning/220-gemma3-fineweb-edu-replication-v23-independent-review-rejection-2026-08-31.json",
    } <= paths
    assert (
        "docs/research/continual-learning/145-gemma3-fineweb-edu-replication-v1-independent-review-rejection-2026-08-30.json"
        in paths
    )



def test_undocumented_v2_to_v6_receipts_are_absent() -> None:
    assert c.validate_history_absences() == []



def test_discarded_prior_document_ids_are_rederived() -> None:
    source = Path(
        "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    assert "def audit_discarded_prior_ids" in source
    assert "2_048, c.FRESH_ROW_START" in source
    assert "row[\"document_id\"] in forbidden_ids" in source


def test_accept_receipt_requires_empty_material_findings() -> None:
    source = Path(
        "experiments/continual_learning/gemma3_fineweb_edu_replication_v29_contract.py"
    ).read_text(encoding="utf-8")
    assert 'if value.get("material_findings") != []:' in source
    assert "empty material_findings list" in source
    assert "expected_keys = {" in source
    assert "type(findings[name]) is not bool" in source


def test_publication_rejects_changed_expected_snapshot(tmp_path: Path) -> None:
    staging, final = tmp_path / "staging", tmp_path / "final"
    staging.mkdir()
    (staging / "required.txt").write_text("stable", encoding="utf-8")
    expected = c.snapshot_files(staging, {"required.txt"}, "test publication")
    (staging / "required.txt").write_text("changed", encoding="utf-8")
    with pytest.raises(RuntimeError, match="snapshot mismatch"):
        c.publish_no_replace(
            staging,
            final,
            {"required.txt"},
            "test publication",
            expected_snapshot=expected,
        )
    assert not final.exists()


def test_result_and_nested_schemas_are_closed_world() -> None:
    source = Path(
        "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    for name in (
        "CONFIG_RESULT_KEYS",
        "RESULT_KEYS",
        "RECEIPT_KEYS",
        "VALIDATOR_RECEIPT_KEYS",
        "METRIC_ROW_KEYS",
        "PARITY_CHECK_KEYS",
    ):
        assert f"{name} =" in source
    assert 'exact_keys(config, CONFIG_RESULT_KEYS, "V29 config")' in source
    assert 'exact_keys(results, RESULT_KEYS, "V29 results")' in source
    assert 'exact_keys(result_receipt, RECEIPT_KEYS, "V29 result receipt")' in source
    assert 'exact_keys(row, METRIC_ROW_KEYS' in source
    assert 'exact_keys(row,' in source and "V29 assessment_per_document row" in source





def test_v29_all_parsed_artifacts_use_stable_reads() -> None:
    validator = Path(
        "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    assert "c.stable_read_bytes(path, label)" in validator
    assert 'c.stable_read_bytes(path, "V29 window")' in validator
    assert 'c.stable_read_bytes(staged, "V29 staged receipt")' in validator
    assert 'c.stable_read_bytes(review_path, "V29 review receipt")' in validator
    assert '"V29 result corpus manifest"' in validator
    assert '"V29 corpus manifest"' in validator
    assert ".read_text(encoding=" not in validator
    assert ".read_bytes()" not in validator
    assert ".open(encoding=" not in validator


def test_v29_descriptor_custody_covers_hashes_parquet_and_model_loads(
    tmp_path: Path,
) -> None:
    path = tmp_path / "stable.bin"
    path.write_bytes(b"stable")
    with c.stable_binary_file(path, "test binary") as handle:
        assert handle.read() == b"stable"
    assert c.sha256_file(path) == "f379ccb92b9116442dc65bdc35648a85d3786b34779db7f704a901fa07b00cb6"
    validator = Path(
        "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    runner = Path(
        "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    contract = Path(
        "experiments/continual_learning/gemma3_fineweb_edu_replication_v29_contract.py"
    ).read_text(encoding="utf-8")
    assert "def stable_binary_file" in contract
    assert 'with pinned_parquet(path, item, "V29 Parquet")' in validator
    assert '(config, "evidence_ledger_mutation", False)' in validator
    assert "MODEL_SNAPSHOT_ROOT" in contract
    assert "_require_read_only_snapshot" in contract
    assert "def _remove_tree" in contract
    assert "_remove_tree(snapshot" in contract
    assert "_remove_tree(staging" in contract
    assert "require_read_only=True" in contract
    assert "c.materialize_model_snapshot" in validator
    assert "c.materialize_model_snapshot" in runner
    assert "require_read_only=True" in validator
    assert "require_read_only=True" in runner


def test_v29_parquet_hash_and_parse_share_one_descriptor() -> None:
    validator = Path(
        "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    assert "def pinned_parquet(" in validator
    assert 'with c.stable_binary_file(path, label) as handle:' in validator
    assert 'hasher = hashlib.sha256()' in validator
    assert 'handle.seek(0)' in validator
    assert 'V29 Parquet pin mismatch on parse descriptor' in validator


def test_v29_all_loader_helpers_require_review_receipt() -> None:
    validator = Path(
        "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    runner = Path(
        "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    assert "def independent_load_runtime(\n    model_path: Path, receipt: Path" in validator
    assert "def load_tokenizer(model_path: Path, receipt: Path)" in validator
    assert "def load_runtime(\n    model_path: Path, receipt: Path" in validator
    assert "def load_tokenizer(model_path: Path, receipt: Path)" in runner
    assert "def load_runtime(\n    model_path: Path, receipt: Path" in runner
    assert validator.count("c.validate_review_receipt(receipt)") >= 4
    assert runner.count("c.validate_review_receipt(receipt)") >= 2


def test_v29_corpus_validator_checks_review_before_tokenizer_load() -> None:
    validator = Path(
        "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    assert "def _tokenizer_for_validation(model_path: Path, receipt: Path)" in validator
    assert "c.validate_review_receipt(receipt)" in validator
    assert "_tokenizer_for_validation(args.model, args.review_receipt)" in validator

def test_v29_source_metadata_and_configuration_are_closed_and_value_locked() -> None:
    validator = Path(
        "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    assert 'DATASET_KEYS = {"fit/fineweb_edu", "assessment/fineweb_edu"}' in validator
    assert 'exact_keys(datasets, DATASET_KEYS, "V29 source datasets")' in validator
    assert 'exact_keys(metadata, DATASET_METADATA_KEYS, "V29 source dataset metadata")' in validator
    for value in (
        '"model_name": c.MODEL_PATH.name',
        '"protocol": "paper-aligned-one-additional-iteration-v1"',
        '"mechanism_source": "arxiv:2608.17981"',
        '"window_token_count": c.WINDOW_TOKENS',
        '"fit_window_count": c.FIT_WINDOW_COUNT',
        '"assessment_window_count": c.ASSESSMENT_WINDOW_COUNT',
        '"normalization": "source_l2_norm_to_destination_l2_norm"',
        '"selection_policy": "first-64-eligible-1024-token-windows-per-disjoint-v29-source-split"',
    ):
        assert value in validator
    assert 'raise ValueError("V29 declared configuration value mismatch")' in validator


def test_v29_validation_binding_excludes_only_derived_snapshot() -> None:
    validation = {"valid": True, "decision": "NoCandidate", "result_snapshot": []}
    assert c.validation_binding(validation) == {
        "valid": True,
        "decision": "NoCandidate",
    }


def test_v29_publication_rejects_post_publish_mutation(tmp_path: Path) -> None:
    staging, final = tmp_path / "staging", tmp_path / "final"
    staging.mkdir()
    (staging / "required.txt").write_text("stable", encoding="utf-8")

    def mutate_published_root() -> None:
        (final / "extra.txt").write_text("unexpected", encoding="utf-8")

    with pytest.raises(RuntimeError, match="post-publication bytes"):
        c.publish_no_replace(
            staging,
            final,
            {"required.txt"},
            "test publication",
            mutate_published_root,
        )
    assert not final.exists()
    assert (staging / "required.txt").read_text(encoding="utf-8") == "stable"


def test_bfloat16_digest_uses_qualified_dtype_and_copy_conversion() -> None:
    source = Path(
        "experiments/continual_learning/gemma3_fineweb_edu_replication_v29_contract.py"
    ).read_text(encoding="utf-8")
    assert 'source_dtype.endswith("bfloat16")' in source
    assert "array = np.array(canonical)" in source


def test_publication_rolls_back_after_post_move_custody_failure(tmp_path: Path) -> None:
    staging, final = tmp_path / "staging", tmp_path / "final"
    staging.mkdir()
    (staging / "required.txt").write_text("stable", encoding="utf-8")
    with pytest.raises(RuntimeError, match="post-move"):
        c.publish_no_replace(
            staging,
            final,
            {"required.txt"},
            "test publication",
            lambda: (_ for _ in ()).throw(RuntimeError("post-move")),
        )
    assert not final.exists()
    assert (staging / "required.txt").read_text(encoding="utf-8") == "stable"


def test_independent_validator_does_not_import_runner_measurement_functions() -> None:
    source = Path(
        "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    assert "stage_and_run_gemma3_fineweb_edu_replication_v29" not in source
    assert "runner." not in source
    assert "def independent_evaluate_windows" in source
    assert "def independent_parity" in source




def test_v29_reach_and_post_validation_gates_are_hard() -> None:
    runner = Path(
        "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    validator = Path(
        "experiments/continual_learning/validate_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    assert 'raise RuntimeError("V29 nonzero intervention reach failed")' in runner
    assert 'raise ValueError("V29 nonzero intervention reach was not proven")' in validator
    assert 'v.validate_validator_receipt(staging / "validator-receipt.json", validation)' in runner
    assert "allow-missing-validator-receipt" in runner



def test_v29_runs_full_validator_after_receipt_binding() -> None:
    source = Path(
        "experiments/continual_learning/stage_and_run_gemma3_fineweb_edu_replication_v29.py"
    ).read_text(encoding="utf-8")
    assert 'argument for argument in command if argument != "--allow-missing-validator-receipt"' in source
    assert 'raise RuntimeError("V29 final validator result mismatch")' in source
    assert 'v.validate_validator_receipt(staging / "validator-receipt.json", validation)' in source

