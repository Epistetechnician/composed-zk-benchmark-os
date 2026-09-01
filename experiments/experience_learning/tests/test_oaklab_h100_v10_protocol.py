"""Hermetic V10 protocol tests.

State slice: oaklab-experience-learning-h100-replication-v10.
"""
import json

from experiments.experience_learning.compile_oaklab_h100_v10_protocol import ROOT, SOURCE_PATH, compile_protocol
from experiments.experience_learning.validate_oaklab_h100_v10_protocol import validate, validate_compiled


def test_v10_compiler_identity_and_new_mechanism():
    source = json.loads((ROOT / SOURCE_PATH).read_bytes())
    compiled = compile_protocol(source)
    assert compiled["protocol_id"] == "oaklab.h100.v10"
    assert compiled["sections"]["estimand"]["treatment"] == "dual_budgeted_credit"
    assert compiled["sections"]["controller"]["state_bytes"] == 62
    assert compiled["execution_gate"]["effects_run"] is False


def test_v10_compiled_artifact_is_current():
    result = validate_compiled(json.loads((ROOT / SOURCE_PATH).read_bytes()))
    assert result["source_sha256"] and result["compiled_sha256"] and result["compiled_self_digest"]


def test_v10_contract_has_all_real_and_null_families():
    source = json.loads((ROOT / SOURCE_PATH).read_bytes())
    assert source["generator_roster"]["stream_order"] == [
        "sparse_signal_v10", "drifting_relevance_v10", "delayed_reward_v10",
        "event_sensor_v10", "long_horizon_v10", "pure_noise_v10"
    ]
    assert source["statistics"]["raw_rows_required"] is True
    assert source["statistics"]["caller_supplied_booleans_forbidden"] is True
    assert source["locks"]["assessment_absence"]["entry_count"] == 0


def test_v10_manifest_and_packet_are_current():
    result = validate()
    assert result["valid"] is True
    assert result["real_execution"] == "prohibited"
    assert result["provider"] == "prohibited"
