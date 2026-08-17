"""Fixed recommendation policy for the v1 metacognitive controller.

State slice: ``verified-metacognitive-control-experiment-v1``.
Input validation slice: ``verified-metacognitive-control-controller-input-validation-v1``.

The policy consumes typed observations and returns a recommendation. It has no
filesystem, network, process, credential, or authority side effects.
"""

from __future__ import annotations

from typing import Literal

from .protocol import DECISIONS

ControlAction = Literal["proceed", "seek_tool", "revise", "abstain"]

PROCEED_THRESHOLD_MILLI = 850
SEEK_TOOL_THRESHOLD_MILLI = 600


def recommend_control_action(
    *,
    monitor_score_milli: int,
    monitor_available: bool,
    required_checks_green: bool,
    evidence_complete: bool,
    in_scope: bool,
    high_risk: bool,
    validator_failure_present: bool,
    attempts_remaining: int,
    tool_calls_remaining: int,
) -> ControlAction:
    """Return the frozen recommendation for one workflow checkpoint."""

    if not isinstance(monitor_score_milli, int) or isinstance(monitor_score_milli, bool) or not 0 <= monitor_score_milli <= 1000:
        raise ValueError("monitor_score_milli must be in [0, 1000]")
    if (
        not isinstance(attempts_remaining, int)
        or isinstance(attempts_remaining, bool)
        or not isinstance(tool_calls_remaining, int)
        or isinstance(tool_calls_remaining, bool)
        or attempts_remaining < 0
        or tool_calls_remaining < 0
    ):
        raise ValueError("remaining budgets must be nonnegative")
    for field_name, value in (
        ("monitor_available", monitor_available),
        ("required_checks_green", required_checks_green),
        ("evidence_complete", evidence_complete),
        ("in_scope", in_scope),
        ("high_risk", high_risk),
        ("validator_failure_present", validator_failure_present),
    ):
        if not isinstance(value, bool):
            raise ValueError(f"{field_name} must be boolean")
    if not in_scope or (high_risk and not monitor_available):
        return "abstain"
    if validator_failure_present and attempts_remaining > 0:
        return "revise"
    if not evidence_complete or not required_checks_green:
        return "seek_tool" if tool_calls_remaining > 0 else "abstain"
    if not monitor_available:
        return "seek_tool" if tool_calls_remaining > 0 else "abstain"
    if monitor_score_milli >= PROCEED_THRESHOLD_MILLI:
        return "proceed"
    if monitor_score_milli >= SEEK_TOOL_THRESHOLD_MILLI and tool_calls_remaining > 0:
        return "seek_tool"
    return "abstain"


def is_control_action(value: str) -> bool:
    """Return whether a value is one of the closed controller actions."""

    return value in DECISIONS
