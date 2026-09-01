"""Auditable experience-stream learning baselines and backend protocols.

State slices: ``oaklab-experience-learning-baselines-v1`` and
``oaklab-experience-learning-benchmark-v2``. The core learner remains
dependency-light; real-data acquisition and optional GPU execution declare
their external dependencies explicitly.
"""

from .types import Experience, StepStats
from .equations import idbd_reference_step, tidbd_reference_step
from .streams import (
    DelayedRewardStream,
    DriftingTargetStream,
    EventCameraLikeStream,
    LongHorizonStream,
    NoisyMNISTArrayStream,
    NoisyMNISTLikeStream,
    NonstationaryFeatureStream,
    SparseNoisyStream,
)
from .learners import (
    AdamLearner,
    EWCLearner,
    EventDrivenLearner,
    IDBDLearner,
    NetworkIDBDLearner,
    PlasticityGuardLearner,
    ReplayLearner,
    SGDLearner,
    TIDBDLearner,
)
from .backends import BackendLinearLearner, BackendStatus, backend_statuses, run_backend_parity

__all__ = [
    "Experience", "StepStats", "idbd_reference_step", "tidbd_reference_step",
    "SparseNoisyStream", "NoisyMNISTLikeStream", "NoisyMNISTArrayStream",
    "NonstationaryFeatureStream", "DriftingTargetStream", "DelayedRewardStream",
    "EventCameraLikeStream", "LongHorizonStream", "SGDLearner", "AdamLearner",
    "IDBDLearner", "NetworkIDBDLearner", "TIDBDLearner", "ReplayLearner",
    "EWCLearner", "PlasticityGuardLearner", "EventDrivenLearner",
    "BackendLinearLearner", "BackendStatus", "backend_statuses", "run_backend_parity",
]
