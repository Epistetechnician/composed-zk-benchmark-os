"""State slice: astral-trace-completeness-gemma3-causal-feature-effects-v1."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

import run_v1


def test_final_artifacts_are_append_only_per_execution() -> None:
    aggregate, expiry = run_v1._artifact_names("execution-123")
    assert aggregate == "v1-causal-feature-effects-aggregate-execution-123.json"
    assert expiry == "raw-deletion-completion-execution-123.json"
    assert aggregate != "v1-causal-feature-effects-aggregate.json"
    assert expiry != "raw-deletion-completion-v1.json"
