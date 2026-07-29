from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astral_v28_gate1", ROOT / "gate1.py")
assert SPEC and SPEC.loader
gate1 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate1
SPEC.loader.exec_module(gate1)


def _rows(correct: bool) -> list[dict]:
    rows = []
    for family_index in range(96):
        fact_kind = gate1.FACT_KINDS[family_index // 24]
        for query_index in range(12):
            scores = [1.0, 0.0, -1.0, -2.0]
            expected = "A" if correct else "B"
            tokens = [family_index, query_index]
            rows.append(
                {
                    "query_id": f"query-{family_index}-{query_index}",
                    "family_id": f"family-{family_index}",
                    "fact_kind": fact_kind,
                    "query_class": gate1.QUERY_CLASSES[query_index // 4],
                    "prompt_sha256": "sha256:" + "a" * 64,
                    "token_ids": tokens,
                    "tokenized_input_sha256": gate1.stable_hash(tokens),
                    "label_scores": scores,
                    "predicted_label": "A",
                    "expected_label": expected,
                    "correct": correct,
                }
            )
    return rows


def test_checked_in_protocol_matches_frozen_constants() -> None:
    protocol = gate1.load_protocol(ROOT / "protocol.json")
    protocol["astral_protocol_sha256"] = gate1.sha256_file(ROOT / "protocol.json")
    protocol["protocol_sha256"] = gate1.stable_hash(protocol)
    errors = []
    gate1.validate_protocol(protocol, errors)
    assert errors == []


def test_futility_recomputation_is_exact_and_strict() -> None:
    negative = gate1.recompute_futility(_rows(False))
    assert not negative["futile"]
    repeated = _rows(False) * 26
    for block, row in enumerate(repeated):
        row["query_id"] += f"-{block}"
    result = gate1.recompute_futility(repeated)
    assert result["futile"]
    assert result["calculations"]["overall"]["maximum_final_accuracy"] < 0.70


def test_cluster_metrics_reject_chance_and_accept_perfect() -> None:
    assert not gate1.recompute_metrics(_rows(False))["passes_cell_gate"]
    assert gate1.recompute_metrics(_rows(True))["passes_cell_gate"]


def test_observation_validator_recomputes_ties_and_token_hashes() -> None:
    rows = _rows(True)
    rows[0]["predicted_label"] = "B"
    rows[1]["tokenized_input_sha256"] = "sha256:" + "0" * 64
    errors = []
    gate1.validate_observations(rows, errors=errors, prefix="test", allow_prefix=True)
    assert "test:argmax" in errors
    assert "test:token_hash" in errors


def test_null_packet_fails_closed() -> None:
    result = gate1.validate_packet(None)
    assert not result["valid"]
    assert result["claim_ceiling"] == "NoGate1Claim"
