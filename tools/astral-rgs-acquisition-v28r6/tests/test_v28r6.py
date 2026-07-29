from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v28r6", ROOT / "v28r6.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def test_protocol_freezes_endurance_and_non_scientific_ceiling() -> None:
    assert module.PROTOCOL["superblock_count"] == 8
    assert module.PROTOCOL["query_count"] == 9_216
    assert module.PROTOCOL["batch_size"] == 8
    assert module.PROTOCOL["max_peak_rss_growth_bytes"] == 512 * 1024**2
    assert not module.PROTOCOL["scientific_campaign_authorized"]


def test_comparison_is_exactly_tolerance_bounded() -> None:
    row = {
        "query_id": "q", "family_id": "f", "retrieved_family_id": "f",
        "fact_kind": "nonce_fact", "query_class": "paraphrase",
        "prompt_sha256": "p", "token_ids": [1], "tokenized_input_sha256": "t",
        "predicted_label": "A", "expected_label": "A", "correct": True,
        "external_source_sha256": "s", "external_support_sha256": "u",
        "label_scores": [1.0, 0.0, -1.0, -2.0],
    }
    close = {**row, "label_scores": [1.0 + 1e-6, 0.0, -1.0, -2.0]}
    far = {**row, "label_scores": [1.0 + 1e-3, 0.0, -1.0, -2.0]}
    assert module.compare({"observations": [row]}, {"observations": [close]})["passes"]
    assert not module.compare({"observations": [row]}, {"observations": [far]})["passes"]


def test_missing_artifact_fails_closed(tmp_path: Path) -> None:
    report = module.validate(tmp_path)
    assert not report["valid"]
    assert not report["qualified"]
