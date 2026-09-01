from experiments.experience_learning.benchmark_v2 import run_multiseed
from experiments.experience_learning.replay_v2 import replay
from experiments.experience_learning.validate_v2 import validate_result


def test_v2_multiseed_is_frozen_and_validated(tmp_path):
    result = run_multiseed(
        ["sparse_noisy", "delayed_reward"], steps=24, seed_offsets=(0, 1, 2),
        algorithms=("sgd_b1", "idbd", "tidbd", "event_driven"),
    )
    assert result["frozen_hyperparameters"]["status"] == "sealed"
    assert result["seed_offsets"] == [0, 1, 2]
    assert validate_result(result) == []
    path = tmp_path / "v2.json"
    path.write_text(__import__("json").dumps(result), encoding="utf-8")
    assert replay(str(path))
