from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning import stage_and_run_gemma3_paper_recirculation_v1 as orchestrator


class CharacterTokenizer:
    def encode(self, text, add_special_tokens=False):
        return [ord(character) for character in text]

    def decode(self, token_ids):
        return "".join(chr(token_id) for token_id in token_ids)


def _source_manifest():
    keys = {f"fit/{name}" for name in orchestrator.FIT_DATASETS} | {
        f"assessment/{name}" for name in orchestrator.ASSESSMENT_DATASETS
    }
    return {
        "schema": orchestrator.SOURCE_SCHEMA,
        "state_slice": orchestrator.STATE_SLICE,
        "selection_policy": "fixed-source-order-v1",
        "datasets": {
            key: {"source": f"source:{key}", "revision": "rev-1", "split": "train"}
            for key in sorted(keys)
        },
    }


def _write_source(root: Path, fit_count=2):
    (root / "fit").mkdir(parents=True)
    (root / "assessment").mkdir(parents=True)
    (root / "acquisition-manifest.json").write_text(
        json.dumps(_source_manifest()), encoding="utf-8"
    )
    for dataset in orchestrator.FIT_DATASETS:
        count = fit_count if dataset == "arxiv" else 1
        (root / "fit" / f"{dataset}.jsonl").write_text(
            "".join(
                json.dumps(
                    {
                        "document_id": f"{dataset}-{index}",
                        "text": "a" * (orchestrator.WINDOW_TOKENS * 2),
                    }
                )
                + "\n"
                for index in range(count)
            ),
            encoding="utf-8",
        )
    for dataset in orchestrator.ASSESSMENT_DATASETS:
        path = orchestrator.SOURCE_FILES[("assessment", dataset)]
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(
            json.dumps(
                {
                    "document_id": f"assessment-{dataset}",
                    "text": "b" * (orchestrator.WINDOW_TOKENS + 5),
                }
            )
            + "\n",
            encoding="utf-8",
        )


def test_token_windows_roundtrip_and_partial_policy():
    tokenizer = CharacterTokenizer()
    full = list(
        orchestrator._token_windows(
            tokenizer,
            "a" * (orchestrator.WINDOW_TOKENS + 5),
            partial_allowed=False,
            maximum_windows=None,
        )
    )
    partial = list(
        orchestrator._token_windows(
            tokenizer,
            "a" * (orchestrator.WINDOW_TOKENS + 5),
            partial_allowed=True,
            maximum_windows=None,
        )
    )
    assert [item[2] for item in full] == [orchestrator.WINDOW_TOKENS]
    assert [item[2] for item in partial] == [orchestrator.WINDOW_TOKENS, 5]


def test_pack_file_limits_fit_to_two_windows_per_document(tmp_path):
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    (source / "fit").mkdir(parents=True)
    path = source / "fit" / "arxiv.jsonl"
    path.write_text(
        json.dumps(
            {
                "document_id": "doc-1",
                "text": "a" * (orchestrator.WINDOW_TOKENS * 3),
            }
        )
        + "\n",
        encoding="utf-8",
    )
    entries = orchestrator._pack_file(
        source,
        destination,
        CharacterTokenizer(),
        "fit",
        "arxiv",
        Path("fit/arxiv.jsonl"),
        target_windows=2,
    )
    assert len(entries) == 2
    assert [entry["window_ordinal"] for entry in entries] == [0, 1]


def test_stage_corpus_requires_paper_fit_counts(tmp_path, monkeypatch):
    source = tmp_path / "source"
    _write_source(source)
    model = tmp_path / "model"
    model.mkdir()
    monkeypatch.setattr(orchestrator, "_load_tokenizer", lambda path: CharacterTokenizer())
    with pytest.raises(ValueError, match="fixed to the paper fit window counts"):
        orchestrator.stage_corpus(
            source,
            tmp_path / "corpus",
            model,
            fit_target_counts={"arxiv": 2, "c4": 1, "pg19": 1},
        )


def test_stage_corpus_materializes_and_validates_external_root(tmp_path, monkeypatch):
    source = tmp_path / "source"
    _write_source(source)
    model = tmp_path / "model"
    model.mkdir()
    corpus = tmp_path / "corpus"
    monkeypatch.setattr(
        orchestrator,
        "PAPER_FIT_WINDOW_COUNTS",
        {"arxiv": 2, "c4": 1, "pg19": 1},
    )
    monkeypatch.setattr(orchestrator, "_load_tokenizer", lambda path: CharacterTokenizer())
    receipt = orchestrator.stage_corpus(source, corpus, model)
    manifest = json.loads((corpus / "manifest.json").read_text(encoding="utf-8"))
    assert receipt["fit_window_counts"] == {"arxiv": 2, "c4": 1, "pg19": 1}
    assert manifest["schema"] == orchestrator.CORPUS_SCHEMA
    assert len(manifest["fit"]) == 4
    assert len(manifest["assessment"]) == 13
    assert (corpus / "acquisition-manifest.json").is_file()
    assert (corpus / "staging-receipt.json").is_file()


def test_external_targets_cannot_be_inside_repository(tmp_path):
    with pytest.raises(ValueError, match="outside the repository"):
        orchestrator._external_path(orchestrator.REPO_ROOT / "nested", "target")


def test_existing_corpus_is_never_overwritten(tmp_path, monkeypatch):
    source = tmp_path / "source"
    _write_source(source)
    model = tmp_path / "model"
    model.mkdir()
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    monkeypatch.setattr(orchestrator, "_load_tokenizer", lambda path: CharacterTokenizer())
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        orchestrator.stage_corpus(source, corpus, model)


def test_pack_only_does_not_validate_unused_output_root(tmp_path, monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "stage_corpus",
        lambda source, corpus, model: {"staged": True},
    )
    result = orchestrator.run_end_to_end(
        tmp_path / "source",
        tmp_path / "corpus",
        orchestrator.REPO_ROOT / "unused-pack-only-result",
        tmp_path / "model",
        pack_only=True,
    )
    assert result == {"staging_receipt": {"staged": True}, "pack_only": True}
