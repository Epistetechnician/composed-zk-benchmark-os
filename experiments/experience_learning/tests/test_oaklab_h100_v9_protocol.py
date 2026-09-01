"""Hermetic V9 protocol compiler tests.

State slice: ``oaklab-experience-learning-h100-replication-v9``.
"""

from experiments.experience_learning.compile_oaklab_h100_v9_protocol import (
    ROOT,
    SOURCE_PATH,
    compile_protocol,
)
from experiments.experience_learning.validate_oaklab_h100_v9_protocol import validate_compiled
import json


def test_v9_compiler_reproduces_compiled_artifact():
    source = json.loads((ROOT / SOURCE_PATH).read_bytes())
    compiled = compile_protocol(source)
    assert compiled["state_slice"] == "oaklab-experience-learning-h100-replication-v9"
    assert compiled["execution_gate"]["assessment_absent"] is True
    assert compiled["sections"]["estimand"]["treatment"] == "segment_budgeted_update_policy"
    assert compiled["sections"]["resource_accounting"]["controller_state_bytes"] == 43


def test_v9_compiled_digest_and_nested_contracts_are_current():
    result = validate_compiled()
    assert result["source_sha256"]
    assert result["compiled_sha256"]
    assert result["compiled_self_digest"]


def test_v9_requires_segment_boundary_and_null_controls():
    source = json.loads((ROOT / SOURCE_PATH).read_bytes())
    assert source["estimand"]["segment_rows"] == 32
    assert source["estimand"]["assessment_absent_until_lock"] is True
    assert "null" in source["statistics"]["families"]
    assert "noise_floor" in source["controls"]["arms"]
