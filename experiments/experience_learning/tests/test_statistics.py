from experiments.experience_learning.statistics import estimate, paired_test, pareto_frontier, publish_gate


def test_estimate_reports_sample_ci():
    result = estimate([1.0, 2.0, 3.0])
    assert result.n == 3
    assert result.mean == 2.0
    assert result.std == 1.0
    assert result.ci95_low < 2.0 < result.ci95_high


def test_paired_test_is_finite_for_degenerate_samples():
    result = paired_test([1.0, 1.0, 1.0], [2.0, 2.0, 2.0])
    assert result["degenerate"] is True
    assert result["statistic"] == -1.0
    assert result["p_value"] == 0.0


def test_pareto_and_publish_gate_keep_resource_tradeoffs_visible():
    records = {
        "a": {"mean_loss": 1.0, "updates": 4, "active_synaptic_ops": 4, "state_bytes": 4},
        "b": {"mean_loss": 0.5, "updates": 8, "active_synaptic_ops": 8, "state_bytes": 8},
    }
    assert set(pareto_frontier(records)) == {"a", "b"}
    streams = {"one": {"sgd_b1": records["b"], "candidate": records["a"]}}
    assert publish_gate(streams)["status"] == "no_candidate"
