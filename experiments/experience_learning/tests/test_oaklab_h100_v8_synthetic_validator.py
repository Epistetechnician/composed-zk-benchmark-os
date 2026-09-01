"""Independent synthetic-result validation tests for Oak Lab V8.

State slice: ``oaklab-experience-learning-h100-replication-v8``.
"""

from experiments.experience_learning.validate_oaklab_h100_v8_synthetic import validate


def test_materialized_synthetic_result_is_valid_and_stays_closed():
    result = validate()
    assert result["status"] == "valid"
    assert result["qualification_status"] == "no_candidate"
    assert result["assessment_materialization_state"] == "absent"
    assert result["hardware_energy"] == "not_run"
