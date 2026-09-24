"""Proof-engine behavior for the proof-carrying nano interpretability V1 slice."""

from tools.proof_carrying_nano_interp_v1.proof import LeanProofEngine
from tools.proof_carrying_nano_interp_v1.tests.test_store import _action


def test_lean_engine_returns_kernel_checked_attempt():
    action = _action(activation=(3, 1), timestamp="2026-09-16T12:00:00Z")
    attempt = LeanProofEngine().attempt(action)

    assert attempt.status == "checked", attempt.diagnostics
    assert attempt.action_digest == action.action_digest
    assert action.action_digest in attempt.source
    assert attempt.statement == "featureActivation [3, 1] 0 = 3"


def test_lean_engine_records_unavailable_checker_as_failed_attempt():
    action = _action(activation=(3, 1), timestamp="2026-09-16T12:00:00Z")
    attempt = LeanProofEngine(command=("executable-that-does-not-exist",)).attempt(action)

    assert attempt.status == "failed"
    assert attempt.diagnostics == ("executable not found: executable-that-does-not-exist",)
