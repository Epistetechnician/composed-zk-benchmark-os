from experiments.experience_learning.benchmark import ALGORITHM_IDS
from experiments.experience_learning.energy import campaign_binding_digest
from experiments.experience_learning.measure_energy_v1 import write_receipt
from experiments.experience_learning.backends import _digest as backend_digest
from experiments.experience_learning.publication_gate_v2 import _digest, evaluate


def _matrix():
    algorithms = {}
    for algorithm in ALGORITHM_IDS:
        if algorithm == "tidbd":
            algorithms[algorithm] = {"status": "not_applicable", "reason": "fixture"}
        else:
            algorithms[algorithm] = {"status": "executed", "assessment_cohorts": [{"mean_loss": 1.0}] * 32}
    publish = {"sgd_b1": {"mean_loss": 1.0, "adaptation_lag": 1, "updates": 100,
                          "active_synaptic_ops": 100, "state_bytes": 100, "replay_storage_bytes": 100,
                          "paired_p_value": None}}
    publish["networkidbd"] = {"mean_loss": 0.5, "adaptation_lag": 0, "updates": 90,
                               "active_synaptic_ops": 90, "state_bytes": 90, "replay_storage_bytes": 90,
                               "paired_p_value": 0.01}
    matrix = {"schema_version": "oaklab.experience-learning.real-matrix.v1",
              "state_slice": "oaklab-experience-learning-benchmark-v2",
              "datasets": {"a": {"algorithms": algorithms, "assessment_cohort_count": 32,
                                   "publish_records": publish,
                                   "controls": {"noise_floor": {"status": "executed"},
                                                 "fit_only_topk_feature_sgd_b1": {"status": "executed"}}}}}
    matrix["result_digest"] = _digest(matrix)
    return matrix


def test_full_publication_gate_requires_measured_energy():
    matrix_a = _matrix()
    matrix_b = _matrix()
    matrix_b["datasets"] = {"b": matrix_b["datasets"]["a"]}
    matrix_b["result_digest"] = _digest({key: value for key, value in matrix_b.items() if key != "result_digest"})
    guard = {"state_slice": "oaklab-experience-learning-benchmark-v2", "strict_gate": {"status": "no_candidate"},
             "dataset": "a", "assessment_cohort_count": 32, "power": {"target_met": True}}
    guard["result_digest"] = _digest(guard)
    result = evaluate([matrix_a, matrix_b], [guard])
    assert result["status"] == "no_candidate"
    assert result["requirements"]["candidate_beats_fixed_sgd_on_quality_adaptation_resources"] is True
    assert result["requirements"]["measured_hardware_energy"] is False


def test_campaign_bound_energy_is_checked_against_gate_inputs(tmp_path):
    matrix_a = _matrix()
    matrix_b = _matrix()
    matrix_b["datasets"] = {"b": matrix_b["datasets"]["a"]}
    matrix_b["result_digest"] = _digest({key: value for key, value in matrix_b.items() if key != "result_digest"})
    guard = {"state_slice": "oaklab-experience-learning-benchmark-v2", "strict_gate": {"status": "no_candidate"},
             "dataset": "a", "assessment_cohort_count": 32, "power": {"target_met": True}}
    guard["result_digest"] = _digest(guard)
    backend = {
        "schema_version": "oaklab.experience-learning.backend-parity.v1",
        "state_slice": "oaklab-experience-learning-benchmark-v2",
        "dimensions": 1,
        "steps": 1,
        "backends": {"dense_cpu": {"status": "executed", "steps": 1, "updates": 1,
                                     "mean_loss": 1.0, "active_synaptic_ops": 2,
                                     "parameter_digest": "a" * 64}},
    }
    backend["result_digest"] = backend_digest(backend)
    matrix_digests = (matrix_a["result_digest"], matrix_b["result_digest"])
    guard_digests = (guard["result_digest"],)
    backend_digests = (backend["result_digest"],)
    manifest = campaign_binding_digest(matrix_digests, guard_digests, backend_digests)
    trace = tmp_path / "trace.csv"
    trace.write_text("timestamp_s,power_w\n0,2\n1,2\n", encoding="utf-8")
    energy = tmp_path / "energy.csv"
    write_receipt(energy, "campaign", "cpu:test", 1, trace, [(0.0, 2.0), (1.0, 2.0)],
                  manifest, matrix_digests, guard_digests, backend_digests)
    result = evaluate([matrix_a, matrix_b], [guard], energy, [backend])
    assert result["requirements"]["measured_hardware_energy"] is True
    assert result["energy"]["campaign_manifest_sha256"] == manifest
