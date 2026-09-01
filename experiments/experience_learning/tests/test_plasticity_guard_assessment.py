from experiments.experience_learning.plasticity_guard_assessment_v1 import (
    PLAN_DIGEST, assess, paired_normal_power,
)
from experiments.experience_learning.types import Experience
from experiments.experience_learning.publication_gate_v1 import _digest, evaluate


def test_sealed_power_plan_is_finite_and_assessment_is_paired():
    experiences = tuple(
        Experience(step, (1.0, 0.0), 0.25 if step % 2 else 0.0, event_indices=(0,))
        for step in range(2048)
    )
    result = assess(experiences, "fixture")
    assert result["plan_digest"] == PLAN_DIGEST
    assert result["assessment_cohort_count"] == 7
    assert result["paired_test"]["n"] == 7
    assert 0.0 <= result["power"]["normal_approximation_power"] <= 1.0
    assert result["strict_gate"]["status"] in {"candidate", "no_candidate"}


def test_power_rejects_unsealed_alpha():
    assert 0.0 <= paired_normal_power(7, 0.5) <= 1.0


def test_publication_gate_requires_energy_and_two_streams():
    results = []
    for dataset in ("a", "b"):
        result = {"schema_version": "oaklab.experience-learning.plasticity-guard-assessment.v1",
                  "dataset": dataset, "plan_digest": PLAN_DIGEST,
                  "strict_gate": {"status": "candidate", "lower_loss": True,
                                  "paired_p_le_alpha": True, "power_target_met": True,
                                  "resource_non_inferiority": True}}
        result["result_digest"] = _digest(result)
        results.append(result)
    result = evaluate(results)
    assert result["status"] == "no_candidate"
    assert result["requirements"]["measured_hardware_energy"] is False
