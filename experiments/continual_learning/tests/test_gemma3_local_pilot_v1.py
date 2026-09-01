from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from experiments.continual_learning import gemma3_local_pilot_v1 as pilot


class CharacterTokenizer:
    def encode(self, text, add_special_tokens=False):
        return [ord(character) for character in text]

    def decode(self, token_ids):
        return "".join(chr(token_id) for token_id in token_ids)


def _write_newsroom(path: Path) -> None:
    rows = [
        {"url": f"https://example.test/{index}", "text": chr(97 + index) * 300}
        for index in range(5)
    ]
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_selection_is_first_source_order_eligible_records(tmp_path):
    source = tmp_path / "test.jsonl.gz"
    _write_newsroom(source)
    selected = pilot._select_documents(source, CharacterTokenizer())
    assert [item["line_number"] for item in selected] == [1, 2, 3, 4]
    assert all(item["token_count"] == 300 for item in selected)
    assert all(len(item["token_ids"]) == pilot.WINDOW_TOKENS for item in selected)


def test_selection_rejects_duplicate_urls(tmp_path):
    source = tmp_path / "test.jsonl.gz"
    with gzip.open(source, "wt", encoding="utf-8") as handle:
        for _ in range(4):
            handle.write(json.dumps({"url": "https://example.test/same", "text": "a" * 300}) + "\n")
    with pytest.raises(ValueError, match="duplicate NEWSROOM url"):
        pilot._select_documents(source, CharacterTokenizer())


def test_volume_path_rejects_non_volume_and_repository(tmp_path):
    with pytest.raises(ValueError, match="under"):
        pilot._volume_path(tmp_path / "artifact", pilot.PRIMARY_VOLUME, "artifact")
    with pytest.raises(ValueError, match="outside the repository"):
        pilot._volume_path(pilot.REPO_ROOT / "artifact", pilot.PRIMARY_VOLUME, "artifact")


def test_pilot_configs_are_frozen_and_valid_for_gemma3():
    configs = pilot._pilot_configs(26)
    assert [(item.source_layer, item.destination_layer) for item in configs] == list(
        pilot.PILOT_PAIRS
    )
    assert all(item.alpha == pilot.FIT_ALPHA for item in configs)
