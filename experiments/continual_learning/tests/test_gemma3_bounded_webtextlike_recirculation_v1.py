from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.continual_learning import (
    gemma3_bounded_webtextlike_recirculation_v1 as runner,
    validate_gemma3_bounded_webtextlike_recirculation_v1 as validator,
)


def test_runtime_window_contract_is_256_tokens():
    assert runner.WINDOW_TOKENS == 256
    assert runner.FIT_ALPHA == 0.10
    assert runner.EVALUATION_ALPHA == 0.15
    assert runner.EVALUATION_BETA == 0.85


def test_pilot_pairs_are_frozen():
    assert runner.PILOT_PAIRS == ((7, 2), (9, 3), (11, 4), (12, 5))
    assert validator.PILOT_PAIRS == runner.PILOT_PAIRS


def test_digest_is_canonical():
    assert runner.digest({"b": 2, "a": 1}) == runner.digest({"a": 1, "b": 2})


def test_self_digest_rejects_tampering():
    value = {"value": 1}
    value["value_sha256"] = validator.digest({"value": 1})
    validator._check_self_digest(value, "value_sha256", "value")
    value["value"] = 2
    with pytest.raises(ValueError, match="digest mismatch"):
        validator._check_self_digest(value, "value_sha256", "value")


def test_external_path_rejects_repository(tmp_path: Path):
    with pytest.raises(ValueError, match="outside the repository"):
        runner._external(runner.REPO_ROOT / "result", "result")


def test_read_jsonl_rejects_blank_line(tmp_path: Path):
    path = tmp_path / "rows.jsonl"
    path.write_text(json.dumps({"document_id": "one"}) + "\n\n", encoding="utf-8")
    with pytest.raises(ValueError, match="blank line"):
        runner._read_jsonl(path, "rows")


def test_short_records_are_excluded_from_fixed_window_panel(tmp_path: Path):
    class CharacterTokenizer:
        def encode(self, text, add_special_tokens=False):
            return [ord(character) for character in text]

        def decode(self, token_ids):
            return "".join(chr(token_id) for token_id in token_ids)

    data = tmp_path / "data"
    data.mkdir()
    fit_rows = [
        {"document_id": "fit-short", "text": "x" * 10},
        *(
            {"document_id": f"fit-{index}", "text": chr(97 + index) * 1024}
            for index in range(4)
        ),
    ]
    assessment_rows = [
        {"document_id": "assessment-short", "text": "y" * 10},
        *(
            {"document_id": f"assessment-{index}", "text": chr(101 + index) * 1024}
            for index in range(4)
        ),
    ]
    for split, rows in (("fit", fit_rows), ("assessment", assessment_rows)):
        (data / f"{split}.jsonl").write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
        )
    manifest = {
        "manifest_sha256": "source-manifest",
        "datasets": {
            split: {
                "relative_path": f"data/{split}.jsonl",
                "record_count": len(rows),
                "byte_len": (data / f"{split}.jsonl").stat().st_size,
                "sha256": runner.sha256_file(data / f"{split}.jsonl"),
            }
            for split, rows in (("fit", fit_rows), ("assessment", assessment_rows))
        },
    }

    fit, assessment, corpus = runner._runtime_windows(
        tmp_path, manifest, CharacterTokenizer()
    )

    assert len(fit) == 4
    assert len(assessment) == 4
    assert [item["document_id"] for item in corpus["manifest"]["excluded_short_records"]["fit"]] == [
        "fit-short"
    ]
    assert [
        item["document_id"]
        for item in corpus["manifest"]["excluded_short_records"]["assessment"]
    ] == ["assessment-short"]
