from experiments.experience_learning.benchmark import ALGORITHM_IDS
from experiments.experience_learning.real_benchmark_v1 import (
    ASSESSMENT_COHORTS, CONTROL_NAMES, REQUIRED_ROWS, run_dataset,
)
from experiments.experience_learning.streams import DriftingTargetStream


def test_real_matrix_contract_runs_all_supervised_baselines_and_controls():
    experiences = tuple(DriftingTargetStream(steps=REQUIRED_ROWS, seed=91))
    result = run_dataset(experiences, "fixture")
    assert result["algorithm_names"] == list(ALGORITHM_IDS)
    assert result["control_names"] == list(CONTROL_NAMES)
    assert result["assessment_cohort_count"] == ASSESSMENT_COHORTS
    assert result["algorithms"]["tidbd"]["status"] == "not_applicable"
    assert result["controls"]["noise_floor"]["status"] == "executed"
    assert result["controls"]["fit_only_topk_feature_sgd_b1"]["status"] == "executed"
    assert result["controls"]["oracle_feature_sgd_b1"]["status"] == "not_available"
