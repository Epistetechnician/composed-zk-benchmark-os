import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import protocol_v48 as protocol


def test_fresh_catalog_matches_sealed_panel_size():
    assert len(protocol.CORPUS_DOCUMENTS) == protocol.TOTAL_DOCUMENTS == 48
    assert protocol.CORPUS_DOCUMENTS == protocol.CANDIDATE_GUTENBERG_IDS
    assert len(set(protocol.CORPUS_DOCUMENTS)) == 48
    assert not set(protocol.CORPUS_DOCUMENTS).intersection(protocol.FRESHNESS_EXCLUSION_INVENTORY)
    assert protocol.TOTAL_FAMILIES == 192


def test_operator_and_prediction_contract_are_fixed():
    manifest = protocol.protocol_manifest()
    assert manifest["model"]["source_layer"] == 26
    assert manifest["model"]["destination_layer"] == 12
    assert manifest["operator"]["alpha"] == 0.10
    assert manifest["operator"]["additional_passes"] == 1
    assert manifest["task"]["corpus_document_ids"] == list(protocol.CORPUS_DOCUMENTS)
    assert manifest["ridge_alphas"] == [0.1, 1.0, 10.0, 100.0]
    assert manifest["prediction_gates"]["minimum_correlation"] == 0.25


def test_digest_is_order_sensitive_for_sealed_selection():
    first = [{"gutenberg_id": 201, "split": "fit"}, {"gutenberg_id": 202, "split": "fit"}]
    second = list(reversed(first))
    assert protocol.selection_digest(first) != protocol.selection_digest(second)
