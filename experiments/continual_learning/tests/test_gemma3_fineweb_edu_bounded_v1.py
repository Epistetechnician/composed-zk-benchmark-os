from __future__ import annotations

import pytest

from experiments.continual_learning import (
    acquire_gemma3_fineweb_edu_bounded_v1 as acquisition,
    stage_and_run_gemma3_fineweb_edu_bounded_v1 as runner,
    validate_gemma3_fineweb_edu_bounded_v1 as validator,
)


class CharacterTokenizer:
    def encode(self, text, add_special_tokens=False):
        return [ord(character) for character in text]

    def decode(self, token_ids):
        return "".join(chr(token_id) for token_id in token_ids)


def test_fineweb_edu_pin_and_state_slice_are_frozen():
    assert acquisition.STATE_SLICE == runner.STATE_SLICE == validator.STATE_SLICE
    assert acquisition.DATASET_REPO == "HuggingFaceFW/fineweb-edu"
    assert acquisition.DATASET_REVISION == "87f09149ef4734204d70ed1d046ddc9ca3f2b8f9"
    assert len(acquisition.DATASET_FILES) == 2
    assert acquisition.DATASET_BYTE_COUNT == 4_280_985_422
    assert acquisition.ROWS_PER_PANEL == 2048
    assert runner.WINDOW_TOKENS == 1024
    assert runner.FIT_WINDOW_COUNT == runner.ASSESSMENT_WINDOW_COUNT == 16
    assert runner.PILOT_PAIRS == ((7, 2), (9, 3), (11, 4), (12, 5))


def test_digest_is_canonical_and_self_digest_is_checked():
    assert acquisition.digest({"b": 2, "a": 1}) == acquisition.digest({"a": 1, "b": 2})
    value = {"value": 1}
    value["manifest_sha256"] = validator.digest({"value": 1})
    validator._check_self_digest(value, "manifest_sha256", "manifest")
    value["value"] = 2
    with pytest.raises(ValueError, match="mismatch"):
        validator._check_self_digest(value, "manifest_sha256", "manifest")


def test_external_paths_reject_repository():
    with pytest.raises(ValueError, match="outside the repository"):
        runner._external(runner.REPO_ROOT / "result", "result")


def test_window_selection_requires_a_full_1024_token_window(tmp_path):
    tokenizer = CharacterTokenizer()
    short, reason = runner._window_from_row(
        tokenizer,
        "fit",
        0,
        {"document_id": "short", "text": "x" * 100},
        tmp_path / "fit/fineweb_edu/window-000000.txt",
    )
    assert short is None
    assert reason["reason"] == "shorter_than_fixed_1024_token_window"
    window, skipped = runner._window_from_row(
        tokenizer,
        "fit",
        1,
        {"document_id": "long", "text": "y" * 1200},
        tmp_path / "fit/fineweb_edu/window-000000.txt",
    )
    assert skipped == {}
    assert window is not None
    assert window.dataset == "fineweb_edu"
    assert window.token_count == 1024
    assert len(tokenizer.encode(window.text, add_special_tokens=False)) == 1024


def test_corpus_validator_rejects_overlap(tmp_path, monkeypatch):
    monkeypatch.setattr(validator, "PRIMARY_VOLUME", tmp_path)
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    entries = []
    for index in range(16):
        relative = f"fit/window-{index:02d}.txt"
        path = corpus / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        data = ("x" * 1024).encode("utf-8")
        path.write_bytes(data)
        entries.append(
            {
                "dataset": "fineweb_edu",
                "document_id": f"fineweb-edu:CC-MAIN-2013-20:{index}",
                "path": relative,
                "window_ordinal": 0,
                "byte_len": len(data),
                "source_sha256": "source",
                "text_sha256": validator.sha256_file(path),
                "token_count": 1024,
            }
        )
    body = {
        "schema": validator.CORPUS_SCHEMA,
        "state_slice": validator.STATE_SLICE,
        "claim_ceiling": validator.CLAIM_CEILING,
        "window_token_count": 1024,
        "source_manifest_sha256": "source-manifest",
        "selection_policy": "first-sixteen-full-1024-token-windows-per-two-crawl-v1",
        "fit": entries,
        "assessment": entries,
        "fit_window_count": 16,
        "assessment_window_count": 16,
        "excluded_short_records": {"fit": [], "assessment": []},
        "deferred_record_count": {"fit": 0, "assessment": 0},
        "network_access": False,
        "training": False,
    }
    manifest = {**body, "manifest_sha256": validator.digest(body)}
    (corpus / "manifest.json").write_text(
        __import__("json").dumps(manifest), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="overlap"):
        validator.validate_corpus(corpus, "source-manifest")
