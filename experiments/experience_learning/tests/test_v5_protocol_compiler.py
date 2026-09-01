"""Hermetic V5 compiler and independent-validator tests.

State slice: ``oaklab-experience-learning-constrained-update-policy-v5``.
These tests validate only the protocol compiler; they never import or execute
learners, generators, backends, or energy capture.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from experiments.experience_learning.compile_v5_protocol import (
    SECTION_NAMES,
    compile_source,
    validate_compiled,
)
from experiments.experience_learning.validate_v5_protocol_compilation import validate


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "experiments/experience_learning/v5_protocol_spec.json"


def test_compiler_is_deterministic_and_has_exact_seven_sections():
    first = compile_source(SOURCE)
    second = compile_source(SOURCE)
    assert first == second
    assert first["sections"] == list(SECTION_NAMES)
    assert first["assessment_materialization_state"] == "absent"
    validate_compiled(first)


def test_independent_validator_accepts_generated_artifact(tmp_path):
    artifact = tmp_path / "compiled.json"
    artifact.write_text(json.dumps(compile_source(SOURCE), sort_keys=True), encoding="utf-8")
    result = validate(SOURCE, artifact, ROOT)
    assert result["status"] == "valid"
    assert result["decision"] == "pending_independent_review"


def test_compiler_rejects_unknown_source_field(tmp_path):
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    source["unexpected"] = True
    path = tmp_path / "source.json"
    path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ValueError, match="missing or extra"):
        compile_source(path)


def test_validator_rejects_digest_tamper(tmp_path):
    artifact = compile_source(SOURCE)
    artifact["compiled_protocol_sha256"] = "0" * 64
    path = tmp_path / "compiled.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    with pytest.raises(ValueError, match="compiled digest"):
        validate(SOURCE, path, ROOT)


def test_validator_rejects_section_tamper(tmp_path):
    artifact = compile_source(SOURCE)
    artifact["compiled"]["adaptation_metrics"] = copy.deepcopy(artifact["compiled"]["adaptation_metrics"])
    artifact["compiled"]["adaptation_metrics"]["threshold"] = "1.20*baseline"
    path = tmp_path / "compiled.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    with pytest.raises(ValueError, match="compiled section bytes"):
        validate(SOURCE, path, ROOT)
