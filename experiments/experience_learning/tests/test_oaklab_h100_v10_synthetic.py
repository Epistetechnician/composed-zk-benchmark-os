"""V10 synthetic qualification tests.

State slice: oaklab-experience-learning-h100-replication-v10.
"""
from experiments.experience_learning.validate_oaklab_h100_v10_synthetic import validate


def test_v10_synthetic_result_is_valid_and_closed():
    result = validate()
    assert result["valid"] is True
    assert result["qualification_status"] == "no_candidate"
    assert result["assessment_materialization_state"] == "absent"
    assert result["real_execution"] == "prohibited"
    assert result["hardware_energy"] == "not_run"
