"""Read-only adapters for caller-custodied real experience datasets.

State slice: ``oaklab-experience-learning-benchmark-v2``.  These functions
verify a supplied JSONL artifact; they never download, reorder, normalize, or
otherwise alter a dataset.  A validated adapter is not evidence that the
corresponding public dataset has been acquired or that it is representative.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from dataclasses import dataclass
from typing import Any

from .types import Experience


SUPPORTED_KINDS = {"noisy_mnist", "event_camera", "sensor", "long_horizon"}


@dataclass(frozen=True)
class CustodyRecord:
    kind: str
    filename: str
    sha256: str
    bytes: int
    rows: int
    status: str = "validated"


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{field} must be a finite number")
    return float(value)


def _experience(row: Any, line_number: int) -> Experience:
    if not isinstance(row, dict):
        raise ValueError(f"row {line_number} must be an object")
    features = row.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError(f"row {line_number} features must be a non-empty list")
    feature_values = tuple(_number(value, "features") for value in features)
    next_features = row.get("next_features")
    if next_features is not None:
        if not isinstance(next_features, list) or len(next_features) != len(feature_values):
            raise ValueError(f"row {line_number} next_features shape mismatch")
        next_features = tuple(_number(value, "next_features") for value in next_features)
    step = row.get("step")
    if isinstance(step, bool) or not isinstance(step, int) or step < 0:
        raise ValueError(f"row {line_number} step must be a non-negative integer")
    events = row.get("event_indices", [])
    if not isinstance(events, list) or any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in events):
        raise ValueError(f"row {line_number} event_indices invalid")
    task_id = row.get("task_id", 0)
    if isinstance(task_id, bool) or not isinstance(task_id, int):
        raise ValueError(f"row {line_number} task_id must be an integer")
    done = row.get("done", True)
    if not isinstance(done, bool):
        raise ValueError(f"row {line_number} done must be boolean")
    return Experience(
        step=step, features=feature_values, target=_number(row.get("target"), "target"),
        reward=_number(row.get("reward", 0.0), "reward"), next_features=next_features,
        done=done, task_id=task_id, event_indices=tuple(events),
        source_id=str(row.get("source_id", "")),
    )


def load_custodied_jsonl(path: str, kind: str, expected_sha256: str | None = None) -> tuple[tuple[Experience, ...], CustodyRecord]:
    """Validate and load an immutable, caller-supplied JSONL experience file."""
    if kind not in SUPPORTED_KINDS:
        raise ValueError(f"unsupported custody kind: {kind}")
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    digest = sha256_file(path)
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("custody digest mismatch")
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            rows.append(_experience(json.loads(line), line_number))
    if not rows:
        raise ValueError("custody artifact contains no experience rows")
    if any(item.step != index for index, item in enumerate(rows)):
        raise ValueError("custody rows must preserve contiguous source order")
    return tuple(rows), CustodyRecord(kind, os.path.basename(path), digest,
                                      os.path.getsize(path), len(rows))
