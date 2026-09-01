"""Hermetic V6 protocol compiler tests.

State slice: ``oaklab-experience-learning-constrained-update-policy-v6``.
No learner, generator, backend, provider, H100, or energy code is imported.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from experiments.experience_learning.compile_v6_protocol import (
    SECTIONS,
    compile_source,
    validate_compiled,
)
from experiments.experience_learning.validate_v6_protocol_compilation import validate


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "experiments/experience_learning/v6_protocol_spec.json"


def test_compiler_is_deterministic_and_emits_exact_seven_sections():
    first = compile_source(SOURCE)
    second = compile_source(SOURCE)
    assert first == second
    assert first["sections"] == list(SECTIONS)
    assert first["assessment_materialization_state"] == "absent"
    validate_compiled(first)


def test_independent_validator_accepts_compiled_artifact(tmp_path):
    artifact_path = tmp_path / "v6_compiled.json"
    artifact_path.write_text(json.dumps(compile_source(SOURCE), sort_keys=True), encoding="utf-8")
    result = validate(SOURCE, artifact_path)
    assert result["status"] == "valid"
    assert result["decision"] == "pending_independent_review"


def test_compiler_rejects_unknown_source_field(tmp_path):
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    source["unexpected"] = True
    path = tmp_path / "source.json"
    path.write_text(json.dumps(source) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing or extra"):
        compile_source(path)


def test_validator_rejects_compiled_digest_tamper(tmp_path):
    artifact = compile_source(SOURCE)
    artifact["compiled_protocol_sha256"] = "0" * 64
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    with pytest.raises(ValueError, match="compiled digest"):
        validate(SOURCE, path)


def test_validator_rejects_section_tamper(tmp_path):
    artifact = compile_source(SOURCE)
    artifact["compiled"]["adaptation_metrics"] = copy.deepcopy(artifact["compiled"]["adaptation_metrics"])
    artifact["compiled"]["adaptation_metrics"]["threshold"] = "1.20*baseline"
    path = tmp_path / "artifact.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    with pytest.raises(ValueError, match="compiled sections differ"):
        validate(SOURCE, path)
