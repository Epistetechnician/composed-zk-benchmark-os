"""State slice: astral-trace-completeness-native-instrument-v1."""

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import protocol
import review_packet_v1


def test_packet_binds_all_new_source_digests_and_stays_fail_closed(tmp_path):
    packet = review_packet_v1.build_packet(ROOT.parent.parent, model_root=tmp_path / protocol.MODEL_ID, custody_root=tmp_path / "custody")
    assert set(packet["source_digests"]) == set(review_packet_v1.SOURCE_FILES)
    assert packet["state_slice"] == protocol.STATE_SLICE
    assert packet["claim_ceiling"] == protocol.CLAIM_CEILING
    assert packet["execution_authorized"] is False
    assert packet["assessment_opened"] is False
    assert packet["status"] == "BLOCKED_PENDING_SIGNED_ACCEPT"
    assert "signed_ACCEPT_receipt" in packet["missing_required_fields"]
    assert len(packet["fresh_corpus"]["manifest_sha256"]) == 64
    assert len(packet["prediction_lock"]["digest"]) == 64


def test_packet_contains_explicit_estimand_assumptions_and_fixed_gates(tmp_path):
    packet = review_packet_v1.build_packet(ROOT.parent.parent, model_root=tmp_path / protocol.MODEL_ID, custody_root=tmp_path / "custody")
    estimand = packet["estimand"]
    assert set(estimand) == {"primary", "assignment", "timing", "consistency", "positivity", "interference"}
    assert packet["uncertainty_missingness_multiplicity_power"]["repeats"] == 2
    assert packet["uncertainty_missingness_multiplicity_power"]["attrition"] == 0.05
    assert packet["thresholds"]["event_missingness_max"] == 0.0
