import pytest

from experiments.continual_learning.independent_replication import (
    CLAIM_CEILING,
    campaign_cases,
    summarize,
)


def test_campaign_uses_disjoint_fixed_cases_and_independent_tools():
    cases = campaign_cases()
    assert len(cases) == 2
    assert len({seed for seed, _ in cases}) == 2
    assert len({order for _, order in cases}) == 2
    summary = summarize(
        [
            {"seed": seed, "order": list(order), "retention_delta": 0.125}
            for seed, order in cases
        ],
        iters=40,
    )
    assert summary["claim_ceiling"] == CLAIM_CEILING
    assert summary["campaign_gate_passed"] is True
    assert summary["network_access"] is False
    assert summary["production_claim_eligible"] is False
    assert summary["executor"].endswith("subprocess")
    assert summary["validator"].endswith("subprocess")


def test_campaign_gate_rejects_nonpositive_effect():
    cases = campaign_cases()
    summary = summarize(
        [
            {"seed": seed, "order": list(order), "retention_delta": 0.0}
            for seed, order in cases
        ],
        iters=40,
    )
    assert summary["all_retention_deltas_positive"] is False
    assert summary["campaign_gate_passed"] is False


def test_empty_campaign_has_no_pass_result():
    summary = summarize([], iters=40)
    assert summary["campaign_gate_passed"] is False
    assert summary["mean_retention_delta"] is None
