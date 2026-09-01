from experiments.experience_learning.plasticity_guard_assessment_v2 import (
    PLAN, PLAN_DIGEST, assess, paired_normal_power,
)
from experiments.experience_learning.types import Experience


def test_powered_plan_reaches_declared_target():
    assert len(PLAN["assessment_cohort_indices"]) == 32
    power = paired_normal_power(32, PLAN["target_standardized_effect"])
    assert power >= PLAN["target_power"]
    experiences = tuple(
        Experience(step, (1.0, 0.0), 0.25 if step % 2 else 0.0, event_indices=(0,))
        for step in range(40 * PLAN["cohort_size"])
    )
    result = assess(experiences, "fixture")
    assert result["plan_digest"] == PLAN_DIGEST
    assert result["assessment_cohort_count"] == 32
    assert result["paired_test"]["n"] == 32
    assert result["power"]["target_met"] is True
