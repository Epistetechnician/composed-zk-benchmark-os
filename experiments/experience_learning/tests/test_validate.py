from experiments.experience_learning.benchmark import run_benchmark
from experiments.experience_learning.validate import validate_result


def test_validator_rejects_digest_tampering_and_batch_violation():
    result = run_benchmark(["sparse_noisy"], steps=12, algorithms=("sgd_b1",))
    result["streams"]["sparse_noisy"]["algorithms"]["sgd_b1"]["accounting"]["explicit_replay"] = True
    assert any("digest" in finding for finding in validate_result(result))
    result = run_benchmark(["sparse_noisy"], steps=12, algorithms=("sgd_b1",))
    result["streams"]["sparse_noisy"]["algorithms"]["sgd_b1"]["accounting"]["max_experience_items_per_observe"] = 2
    assert any("batch-one" in finding for finding in validate_result(result))
