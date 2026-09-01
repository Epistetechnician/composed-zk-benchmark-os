from __future__ import annotations

import gzip
import json
from pathlib import Path

from experiments.continual_learning import gemma3_local_pilot_v1 as pilot_v1
from experiments.continual_learning import gemma3_local_pilot_v2 as pilot_v2


class CharacterTokenizer:
    def encode(self, text, add_special_tokens=False):
        return [ord(character) for character in text]

    def decode(self, token_ids):
        return "".join(chr(token_id) for token_id in token_ids)


def test_v2_selects_the_next_disjoint_eligible_cohort(tmp_path: Path):
    source = tmp_path / "test.jsonl.gz"
    with gzip.open(source, "wt", encoding="utf-8") as handle:
        for index in range(9):
            handle.write(
                json.dumps(
                    {
                        "url": f"https://example.test/{index}",
                        "text": chr(97 + index) * 300,
                    }
                )
                + "\n"
            )
    selected = pilot_v1._select_documents(
        source,
        CharacterTokenizer(),
        selection_offset=pilot_v2.SPEC.selection_offset,
    )
    assert [item["line_number"] for item in selected] == [5, 6, 7, 8]


def test_v2_identity_and_policy_are_frozen():
    assert pilot_v2.SPEC.state_slice == pilot_v2.STATE_SLICE
    assert pilot_v2.SPEC.corpus_schema == pilot_v2.CORPUS_SCHEMA
    assert pilot_v2.SPEC.source_schema == pilot_v2.SOURCE_SCHEMA
    assert pilot_v2.SPEC.selection_offset == 4
    assert pilot_v2.SPEC.selection_policy == pilot_v2.SELECTION_POLICY
