from experiments.experience_learning.equation_parity_v1 import run_parity
from experiments.experience_learning.validate_equation_parity_v1 import validate_result


def test_multistep_idbd_tidbd_parity_receipt():
    result = run_parity()
    assert result["status"] == "PASSED"
    assert validate_result(result) == []
