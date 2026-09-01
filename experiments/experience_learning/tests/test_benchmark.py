from experiments.experience_learning.benchmark import ALGORITHM_IDS, run_benchmark
from experiments.experience_learning.validate import validate_result
from experiments.experience_learning.replay import replay


def test_benchmark_matrix_is_digest_bound_and_accountable():
    result = run_benchmark(["sparse_noisy", "delayed_reward"], steps=24)
    assert result["state_slice"] == "oaklab-experience-learning-baselines-v1"
    assert set(result["algorithm_names"]) == set(ALGORITHM_IDS)
    assert validate_result(result) == []
    for stream in result["streams"].values():
        for name in ALGORITHM_IDS:
            record = stream["algorithms"][name]
            if record["status"] == "not_applicable":
                assert name == "tidbd"
                continue
            assert record["accounting"]["learner_observe_calls"] == stream["n_experiences"]
            assert record["accounting"]["max_experience_items_per_observe"] == 1


def test_result_replays_deterministically(tmp_path):
    from experiments.experience_learning.benchmark import write_result
    result = run_benchmark(["sparse_noisy"], steps=16, algorithms=("sgd_b1", "idbd"))
    path = tmp_path / "result.json"
    write_result(result, str(path))
    assert replay(str(path))
